import { test, expect, type Page, type BrowserContext } from "@playwright/test";
import { forgeOtpVerifiedAt, setForgedSessionCookie } from "./helpers/otp-forge";
import { SESSION_COOKIE, parseSessionCookie, type Session } from "@/lib/session";

/**
 * Nhóm identity/AUTH-* (FIN05_QA_TestCases.jsonl) — 8 case OTP + câu hỏi bảo
 * mật. Trước bản vá backend (src/auth.py::require_otp_verified), OTP chỉ là
 * gate UI mô phỏng — test này chạy qua UI THẬT + backend THẬT, không mock gì,
 * để xác nhận toàn bộ chuỗi browser → BFF → FastAPI hoạt động đúng.
 *
 * User demo: USR-0145 (data/generated/users.jsonl), SĐT 0974000145. Câu trả
 * lời bảo mật demo = `ans-{DATASET_SEED}-{user_id}` (xem docs/TESTING.md và
 * src/api/main.py::verify_otp) — CHỈ áp dụng ở seed cố định 20260802.
 */
const PHONE = "0974000145";
const DEMO_SECURITY_ANSWER = "ans-20260802-USR-0145";

async function login(page: Page) {
  await page.goto("/login");
  // "Khách hàng" đã active mặc định — chỉ cần điền SĐT.
  await page.getByPlaceholder("09xx xxx xxx").fill(PHONE);
  await page.getByRole("button", { name: "Đăng nhập" }).click();
  await page.waitForURL("**/chat");
}

async function sendChatMessage(page: Page, text: string) {
  const input = page.getByPlaceholder("Nhập tin nhắn...");
  await input.fill(text);
  await input.press("Enter");
}

// Kích hoạt luồng nhạy cảm qua nút "Báo lỗi giao dịch này" + chip loại khiếu
// nại — startComplaint() (ChatClient.tsx) LUÔN gọi beginOtpFlow() TRƯỚC khi
// liên hệ agent, không phụ thuộc agent có gọi tool hay không. Dùng đường này
// thay vì gõ tự do: phát hiện thật qua chạy test lần đầu — LLM không phải
// lúc nào cũng gọi tool ngay ở lượt đầu dù prompt đã dặn (agent đôi khi chỉ
// nói "để mình tra cứu" rồi hỏi lại luôn mà không hề gọi get_customer_history
// — cùng 1 bug đã ghi nhận trong quá trình audit golden_set trước đó), khiến
// test dựa vào hội thoại tự do không ổn định. Đường rail là gate UI xác định,
// không phụ thuộc hành vi LLM.
async function triggerSensitiveAction(page: Page) {
  await page.getByRole("button", { name: "Báo lỗi giao dịch này" }).first().click();
  await page.getByText("Tiền chưa về", { exact: true }).click();
}

// Đi hết 1 lượt xác thực OTP THẬT qua UI — dùng làm bước chuẩn bị cho
// AUTH-007 (cần 1 otp_verified_at thật trước khi forge lùi thời gian), tái
// dùng cho cả case "OTP đúng" đã có ở dưới.
async function completeOtpVerification(page: Page) {
  await expect(page.locator(".otp-row")).toBeVisible({ timeout: 20_000 });
  const demoCodeText = await page.locator(".otp-meta").first().locator("strong").textContent();
  const otpCode = (demoCodeText ?? "").trim();
  const boxes = page.locator(".otp-box");
  for (let i = 0; i < 6; i++) {
    await boxes.nth(i).fill(otpCode[i]);
  }
  await page.locator(".otp-answer").fill(DEMO_SECURITY_ANSWER);
  await page.getByRole("button", { name: "Xác nhận" }).click();
  await expect(page.getByText("Xác thực thành công")).toBeVisible({ timeout: 10_000 });
}

// Đọc lại session THẬT (kể cả httpOnly, Playwright context.cookies() đọc
// được — khác browser JS) — dùng làm nguồn payload thật cho forgeOtpVerifiedAt,
// không tự bịa claim.
async function readSessionCookie(context: BrowserContext): Promise<Session> {
  const cookies = await context.cookies();
  const raw = cookies.find((c) => c.name === SESSION_COOKIE)?.value;
  // Next.js cookies().set() tự URL-encode giá trị (xác nhận thật qua debug:
  // context.cookies() trả nguyên văn "%7B%22user_id..." chưa decode) —
  // parseSessionCookie() chỉ JSON.parse thẳng, phải decode trước.
  const session = parseSessionCookie(raw ? decodeURIComponent(raw) : raw);
  if (!session) throw new Error(`Không đọc được cookie ${SESSION_COOKIE} — chưa đăng nhập?`);
  return session;
}

test.describe("AUTH-* — OTP phiên làm việc + câu hỏi bảo mật", () => {
  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("AUTH-004: câu hỏi chính sách chung KHÔNG bị chặn OTP", async ({ page }) => {
    await sendChatMessage(page, "Phí rút tiền về ngân hàng là bao nhiêu vậy bạn?");
    // Agent phải trả lời trực tiếp — form OTP KHÔNG được xuất hiện.
    await expect(page.locator(".otp-row")).toHaveCount(0, { timeout: 15_000 });
  });

  test("AUTH-001: thao tác nhạy cảm bị chặn, phải nhập OTP + câu hỏi bảo mật", async ({ page }) => {
    await triggerSensitiveAction(page);
    await expect(page.locator(".otp-row")).toBeVisible({ timeout: 20_000 });
    await expect(page.getByText("Câu hỏi bảo mật:")).toBeVisible();
  });

  test("AUTH-001 tiếp: nhập đúng OTP + câu trả lời -> xác thực thành công, agent tra tiếp", async ({ page }) => {
    await triggerSensitiveAction(page);
    await expect(page.locator(".otp-row")).toBeVisible({ timeout: 20_000 });

    const demoCodeText = await page.locator(".otp-meta").first().locator("strong").textContent();
    const otpCode = (demoCodeText ?? "").trim();
    expect(otpCode).toMatch(/^\d{6}$/);

    const boxes = page.locator(".otp-box");
    for (let i = 0; i < 6; i++) {
      await boxes.nth(i).fill(otpCode[i]);
    }
    await page.locator(".otp-answer").fill(DEMO_SECURITY_ANSWER);
    await page.getByRole("button", { name: "Xác nhận" }).click();

    await expect(page.getByText("Xác thực thành công")).toBeVisible({ timeout: 10_000 });
  });

  test("AUTH-006: đã xác thực 1 lần trong phiên -> không hỏi lại OTP cho thao tác nhạy cảm tiếp theo", async ({
    page,
  }) => {
    // Lượt 1 — xác thực.
    await triggerSensitiveAction(page);
    await expect(page.locator(".otp-row")).toBeVisible({ timeout: 20_000 });
    const otpCode = ((await page.locator(".otp-meta").first().locator("strong").textContent()) ?? "").trim();
    const boxes = page.locator(".otp-box");
    for (let i = 0; i < 6; i++) await boxes.nth(i).fill(otpCode[i]);
    await page.locator(".otp-answer").fill(DEMO_SECURITY_ANSWER);
    await page.getByRole("button", { name: "Xác nhận" }).click();
    await expect(page.getByText("Xác thực thành công")).toBeVisible({ timeout: 10_000 });

    // Lượt 2 — thao tác nhạy cảm KHÁC trong CÙNG phiên — không được hỏi lại OTP.
    await sendChatMessage(page, "Tôi bị trừ tiền 2 lần cho cùng 1 giao dịch, giúp tôi với.");
    await page.waitForTimeout(3_000);
    // Chỉ 1 form OTP duy nhất (từ lượt 1) tồn tại trong toàn bộ thread.
    await expect(page.locator(".otp-row")).toHaveCount(1);
  });

  test("AUTH-002: không bao giờ hiện chữ 'mật khẩu' hoặc yêu cầu OTP giao dịch thật", async ({ page }) => {
    await triggerSensitiveAction(page);
    await expect(page.locator(".otp-row")).toBeVisible({ timeout: 20_000 });
    const threadText = await page.locator(".chat-thread").textContent();
    expect(threadText).not.toMatch(/mật khẩu/i);
    // Disclaimer cố định trong UI cũng khẳng định lại đúng chính sách này (COMP-003).
    await expect(page.getByText("Sen không bao giờ hỏi mật khẩu")).toBeVisible();
  });

  test("AUTH-003: sai OTP/câu trả lời -> báo lỗi rõ ràng, KHÔNG cho qua", async ({ page }) => {
    await triggerSensitiveAction(page);
    await expect(page.locator(".otp-row")).toBeVisible({ timeout: 20_000 });

    const boxes = page.locator(".otp-box");
    for (let i = 0; i < 6; i++) await boxes.nth(i).fill("0");
    await page.locator(".otp-answer").fill("sai câu trả lời");
    await page.getByRole("button", { name: "Xác nhận" }).click();

    // Không được xác thực thành công — form vẫn còn, có báo lỗi.
    await expect(page.getByText("Xác thực thành công")).toHaveCount(0);
    await expect(page.locator(".otp-row")).toBeVisible();
  });
});

// AUTH-005/007/008 — quyết định thiết kế đã CHỐT (2026-08-10, xem
// docs/TESTING.md): 2 ngưỡng "còn tươi" theo rủi ro thao tác —
// OTP_VIEW_MAX_MINUTES=12h cho thao tác chỉ xem, OTP_STEPUP_FRESH_MINUTES=15
// phút cho create_ticket (step-up chặt hơn vì có hậu quả tài chính thật).
// Ngưỡng đã cài đặt + test deterministic đầy đủ ở tests/test_api/test_otp.py
// — 2026-08-11: hạ tầng browser-level time-travel đã dựng xong
// (helpers/otp-forge.ts, ký lại JWT thật bằng jsonwebtoken cùng
// JWT_SECRET_KEY backend đang dùng), un-skip AUTH-007/008 bên dưới.
test.describe("AUTH-005 — ma trận hành động đã phủ qua các test khác", () => {
  test.skip(
    true,
    "Ma trận đầy đủ mọi nhóm hành động, kể cả nhánh (e) xem trạng thái " +
      "ticket, đã phủ rải rác qua AUTH-001/004/006/007/008 (get_customer_history " +
      "dùng CHUNG 1 gate OTP với lookup_transaction) — không cần 1 test ma trận riêng."
  );
});

test.describe("AUTH-007 — ngưỡng 12h tuyệt đối cho thao tác chỉ xem", () => {
  // PHÁT HIỆN THẬT lúc verify (không theo đúng kế hoạch ban đầu — kế hoạch
  // định test qua UI/.otp-row, nhưng thực nghiệm cho thấy cách đó KHÔNG thể
  // phân biệt fresh/stale):
  //   1. Gate OTP 12h CHỈ nằm trong customer_tools.py (lớp bọc tool khi AGENT
  //      gọi) — 2 route HTTP trực tiếp /tools/lookup_transaction và
  //      /tools/get_customer_history KHÔNG gắn require_otp_verified (route đó
  //      còn phục vụ CSKH tra cứu không qua OTP khách hàng, xem comment ở
  //      src/api/main.py ngay phía trên 2 route đó) — không có BFF route nào
  //      gọi thẳng được gate này ngoài đường agent.
  //   2. ChatClient.tsx dùng `otpVerifiedRef` — cờ CLIENT-SIDE "đã hỏi 1
  //      lần/phiên", chỉ reset khi RELOAD trang, hoàn toàn tách biệt với
  //      otp_verified_at THẬT ở backend. Test qua `.otp-row` + reload() vì
  //      vậy LUÔN hỏi lại OTP sau reload bất kể forge fresh hay stale (reset
  //      cờ client), còn KHÔNG reload thì LUÔN không hỏi lại (cờ vẫn true) —
  //      cả 2 hướng đều không phản ánh đúng otp_verified_at thật.
  // Cách đáng tin cậy duy nhất: gọi thẳng /api/agent-chat (BFF thật, vẫn qua
  // browser context + cookie forge, không mock) với câu hỏi ĐỊNH HƯỚNG mạnh
  // (đã verify thật bằng curl 2 chiều fresh/stale, agent gọi tool ổn định,
  // không như câu hỏi tự do chung chung) — đọc trực tiếp
  // tool_calls[].result.status thay vì suy luận qua UI, vì graph.py trả
  // nguyên văn kết quả tool (kể cả lỗi OTP) trong response, không cần đợi
  // LLM diễn đạt lại đúng ý.
  const SENSITIVE_MESSAGE = "Cho tôi xem lịch sử giao dịch gần đây của tôi.";

  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("OTP xác thực 12h-1 phút trước -> vẫn còn hiệu lực, trả dữ liệu thật", async ({ page, context }) => {
    await triggerSensitiveAction(page);
    await completeOtpVerification(page);

    const realSession = await readSessionCookie(context);
    const forged = forgeOtpVerifiedAt(realSession, 12 * 60 * 60 - 60); // 12h - 1 phút
    await setForgedSessionCookie(context, forged);

    const response = await page.request.post("/api/agent-chat", { data: { message: SENSITIVE_MESSAGE } });
    const body = await response.json();
    const call = body.tool_calls.find((c: { tool_name: string }) => c.tool_name === "get_customer_history");
    expect(call).toBeTruthy();
    expect(call.result.status).not.toBe("error");
  });

  test("OTP xác thực 12h+1 phút trước -> hết hiệu lực, tool trả lỗi cần xác thực lại", async ({ page, context }) => {
    await triggerSensitiveAction(page);
    await completeOtpVerification(page);

    const realSession = await readSessionCookie(context);
    const forged = forgeOtpVerifiedAt(realSession, 12 * 60 * 60 + 60); // 12h + 1 phút
    await setForgedSessionCookie(context, forged);

    const response = await page.request.post("/api/agent-chat", { data: { message: SENSITIVE_MESSAGE } });
    const body = await response.json();
    const call = body.tool_calls.find((c: { tool_name: string }) => c.tool_name === "get_customer_history");
    expect(call).toBeTruthy();
    expect(call.result.status).toBe("error");
    expect(call.result.message).toContain("OTP");
  });
});

test.describe("AUTH-008 — step-up 15 phút cho create_ticket (hậu quả tài chính thật)", () => {
  // /tools/create_ticket KHÔNG có route BFF riêng ở frontend (chỉ gọi được
  // qua tool-calling nội bộ của agent trong /agent/chat) — ép đi hết luồng
  // chat tới lúc LLM tự quyết định gọi create_ticket sẽ tái tạo đúng vấn đề
  // flaky đã ghi nhận ở triggerSensitiveAction() (LLM không phải lúc nào
  // cũng gọi tool ngay). Gọi thẳng backend thật bằng token đã forge (vẫn là
  // token THẬT lấy từ browser context, chỉ bỏ qua hop BFF — BFF chỉ là proxy
  // thêm header Authorization, đã test riêng qua AUTH-001/004/006) — vẫn xác
  // nhận đúng logic step-up 15 phút thật ở backend, không cần LLM tham gia.
  const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8010";
  // TXN20260429000001 — giao dịch thật của USR-0145 (scope internal_wallet,
  // status success), seed cố định (DATASET_SEED=20260802).
  const TICKET_PAYLOAD = {
    complaint_type: "money_not_received",
    scope: "internal_wallet",
    description_raw: "Tôi chuyển tiền nhưng người nhận báo chưa thấy tiền về.",
    trans_id: "TXN20260429000001",
  };

  test.beforeEach(async ({ page }) => {
    await login(page);
  });

  test("OTP xác thực 15 phút+1 giây trước -> KHÔNG đủ tươi cho create_ticket, 403", async ({ page, context }) => {
    await triggerSensitiveAction(page);
    await completeOtpVerification(page);

    const realSession = await readSessionCookie(context);
    const forged = forgeOtpVerifiedAt(realSession, 15 * 60 + 1);
    const response = await page.request.post(`${BACKEND_URL}/tools/create_ticket`, {
      data: TICKET_PAYLOAD,
      headers: { Authorization: `Bearer ${forged.access_token}` },
    });
    expect(response.status()).toBe(403);
    expect((await response.json()).detail).toContain("OTP");
  });

  test("OTP xác thực 5 phút trước -> đủ tươi cho create_ticket, không bị chặn OTP", async ({ page, context }) => {
    await triggerSensitiveAction(page);
    await completeOtpVerification(page);

    const realSession = await readSessionCookie(context);
    const forged = forgeOtpVerifiedAt(realSession, 5 * 60);
    const response = await page.request.post(`${BACKEND_URL}/tools/create_ticket`, {
      data: TICKET_PAYLOAD,
      headers: { Authorization: `Bearer ${forged.access_token}` },
    });
    // Không còn bị chặn bởi gate OTP (403) — response có thể vẫn khác 2xx vì
    // lý do nghiệp vụ khác (vd trùng ticket), nhưng KHÔNG phải lỗi OTP/token.
    // Assert cả 401 lẫn 403 (không chỉ 403) — 401 "Token không hợp lệ" từng
    // là false-pass thật ở đây lúc verify (bug ký JWT thiếu `iat`, xem
    // otp-forge.ts), `not.toBe(403)` một mình không bắt được vì 401 cũng
    // khớp điều kiện đó.
    expect(response.status()).not.toBe(401);
    expect(response.status()).not.toBe(403);
  });
});
