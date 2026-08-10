import { test, expect, type Page } from "@playwright/test";

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
// OTP_VIEW_MAX_MINUTES=12h cho thao tác chỉ xem (bao gồm cả xem trạng thái
// ticket/khiếu nại đã có, nhánh (e) AUTH-005 — khách CHỌN vẫn cần OTP như
// thao tác nhạy cảm khác thay vì miễn), OTP_STEPUP_FRESH_MINUTES=15 phút cho
// create_ticket (step-up chặt hơn vì có hậu quả tài chính thật). Toàn bộ
// logic freshness đã cài đặt (src/auth.py::CurrentUser.otp_fresh_within,
// src/agents/tools/customer_tools.py::_otp_fresh) và có bộ test deterministic
// đầy đủ ở tests/test_api/test_otp.py — dùng JWT dựng SẴN với otp_verified_at
// lùi về quá khứ (test_view_tools_allowed_within_12h_but_stepup_action_needs_fresher_otp,
// test_view_tools_blocked_after_12h_absolute_max,
// test_stepup_action_allowed_when_within_fresh_window,
// test_http_create_ticket_gate_rejects_stale_otp_beyond_stepup_window) — cách
// DUY NHẤT khả thi để kiểm ngưỡng 15 phút/12 giờ mà không phải chờ thời gian
// thật trôi qua trong CI.
test.describe("AUTH-005/007/008 — đã chốt thiết kế, giới hạn còn lại là hạ tầng test browser", () => {
  test.skip(
    true,
    "AUTH-005 (ma trận đầy đủ mọi nhóm hành động, kể cả nhánh (e) xem trạng " +
      "thái ticket) đã phủ rải rác qua các test AUTH-001/004/006 ở trên " +
      "(get_customer_history dùng CHUNG 1 gate OTP với lookup_transaction) " +
      "— không cần 1 test ma trận riêng."
  );

  test.skip(
    true,
    "AUTH-007 (ngưỡng timeout OTP: 12h tuyệt đối cho thao tác xem) — NGƯỠNG ĐÃ " +
      "CHỐT VÀ CÀI ĐẶT XONG (OTP_VIEW_MAX_MINUTES, src/config.py), có test " +
      "deterministic đầy đủ ở tests/test_api/test_otp.py (JWT dựng sẵn với " +
      "otp_verified_at lùi 12h+1 phút). Còn lại CHỈ là hạ tầng: test qua " +
      "browser thật đòi chờ 12 giờ thật hoặc dựng JWT thủ công + inject " +
      "cookie fin05_session (cần thêm dependency ký JWT ở phía Node, chưa " +
      "cài) — không phải quyết định thiết kế còn treo."
  );

  test.skip(
    true,
    "AUTH-008 (phân tầng xác thực theo mức độ nhạy cảm) — đã CHỌN phân tầng: " +
      "create_ticket cần OTP TƯƠI HƠN (OTP_STEPUP_FRESH_MINUTES=15 phút) so " +
      "với lookup_transaction/get_customer_history (OTP_VIEW_MAX_MINUTES=12h) " +
      "— NGƯỢC với ghi chú cũ ở đây (bản trước ghi nhầm là 'đồng nhất 1 mức', " +
      "đã lạc hậu). Đã cài đặt + test đầy đủ ở tests/test_api/test_otp.py; " +
      "còn thiếu cùng 1 hạ tầng browser-level time-travel như AUTH-007."
  );
});
