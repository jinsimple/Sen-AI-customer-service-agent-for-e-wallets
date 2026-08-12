import type { Page } from "@playwright/test";
import { expect } from "@playwright/test";
import { SESSION_COOKIE, parseSessionCookie } from "@/lib/session";

/**
 * FIN05-StressTest-Plan-v4 P2 — helper dùng chung cho e2e mới (approve,
 * ticket-detail, dashboard, knowledge, policy-lookup) — login theo role +
 * tạo 1 ticket THẬT qua đúng luồng AI + OTP (không có route BFF tắt để tạo
 * ticket trực tiếp — `create_ticket` CHỈ gọi được qua `/agent/chat`, xem
 * `frontend/src/app/api/tools/` không có route `create-ticket`), rồi CSKH
 * đề xuất resolution qua BFF thật (`/api/tools/propose-resolution` CÓ tồn
 * tại) — dùng làm dữ liệu setup cho các test cần 1 ticket/resolution có
 * thật thay vì mock.
 */

export async function loginAs(page: Page, phone: string, roleLabel: string, expectedPathPrefix: string, attempt = 1): Promise<void> {
  await page.goto("/login");
  await page.locator(".filter-chip", { hasText: roleLabel }).click();
  await page.getByPlaceholder("09xx xxx xxx").fill(phone);
  const [response] = await Promise.all([
    page.waitForResponse((r) => r.url().includes("/api/session"), { timeout: 15_000 }).catch(() => null),
    page.getByRole("button", { name: "Đăng nhập" }).click(),
  ]);
  if (response && response.status() === 429) {
    if (attempt >= 3) throw new Error(`Vẫn 429 sau ${attempt} lần thử đăng nhập ${phone}.`);
    await page.waitForTimeout(15_000);
    return loginAs(page, phone, roleLabel, expectedPathPrefix, attempt + 1);
  }
  await page.waitForURL(`**${expectedPathPrefix}**`, { timeout: 15_000 });
}

/** Khách tạo 1 ticket THẬT qua đúng luồng rail "Giao dịch gần đây" → chip
 * loại khiếu nại (GIỐNG HỆT auth.spec.ts::triggerSensitiveAction đã verify
 * ổn định) — KHÔNG gõ tự do kèm trans_id tự bịa (phát hiện thật lúc viết
 * bản đầu của helper này: gõ tay 1 mã giao dịch không có thật cho user hiện
 * tại khiến agent trả lời "không tìm thấy giao dịch", không tạo ticket nào
 * — lỗi ở TEST, không phải sản phẩm). Dùng đúng transaction có thật đầu
 * tiên trong rail, và dựa vào `startComplaint()` (ChatClient.tsx) tự set
 * `pendingStarterRef` — TỰ ĐỘNG gửi lại câu hỏi sau khi xác thực OTP xong,
 * không cần logic gửi lại tay. Trả về ticket_id đọc từ rail "Trạng thái". */
/** Hoàn tất OTP NẾU bị chặn giữa chừng (chạm dữ liệu giao dịch/tài khoản) —
 * dùng chung cho MỌI luồng có thể trigger OTP (chip-based lẫn gõ tự do).
 * Trả `true` nếu thực sự có OTP xuất hiện và đã xác thực xong.
 *
 * LƯU Ý QUAN TRỌNG (khác nhau giữa 2 luồng): chip-based (startComplaint())
 * tự set `pendingStarterRef` — submitOtp() (ChatClient.tsx) tự động gửi lại
 * câu hỏi gốc SAU KHI xác thực xong, không cần gọi tay. Gõ TỰ DO trigger
 * OTP giữa chừng thì KHÔNG có pendingStarterRef nào được set (chỉ
 * startComplaint() set) — câu hỏi gốc KHÔNG tự động gửi lại, caller phải tự
 * gửi lại nếu cần. Đây là bất đối xứng thật trong sản phẩm, không phải lỗi
 * helper — ghi rõ ở đây để chỗ gọi biết mà xử lý đúng. */
export async function completeOtpIfPrompted(page: Page): Promise<boolean> {
  // Có thể bị chặn OTP giữa chừng (chạm dữ liệu giao dịch/tạo ticket).
  // Phát hiện thật (lúc viết bản đầu của helper này): agent đôi khi gọi 2
  // tool (lookup_transaction + get_customer_history) trước khi trả lời cần
  // OTP — tổng thời gian round-trip LLM thật > 15s, timeout ngắn khiến
  // isVisible() hết hạn TRƯỚC KHI OTP thật xuất hiện, trả false lặng lẽ.
  // Dùng waitFor thay vì isVisible ngắn hạn, timeout dài hơn hẳn.
  const otpRow = page.locator(".otp-row");
  const otpVisible = await otpRow
    .waitFor({ state: "visible", timeout: 40_000 })
    .then(() => true)
    .catch(() => false);
  if (!otpVisible) return false;

  const demoCode = (await page.locator(".otp-meta").first().locator("strong").textContent())?.trim() ?? "";
  const boxes = page.locator(".otp-box");
  for (let i = 0; i < 6; i++) await boxes.nth(i).fill(demoCode[i]);
  // fin05_session là cookie httpOnly — document.cookie (JS trình duyệt)
  // KHÔNG đọc được (đúng thiết kế bảo mật, xem lib/session.ts) — phát
  // hiện thật lúc viết test này: page.evaluate đọc document.cookie luôn
  // ra null, làm câu trả lời bảo mật sai (ans-...-null), OTP verify fail
  // âm thầm (form đứng yên, không báo lỗi rõ). Phải đọc qua
  // context.cookies() (API Playwright, đọc được cả httpOnly) — đúng cách
  // otp-forge.ts::readSessionCookie đã làm.
  const cookies = await page.context().cookies();
  const raw = cookies.find((c) => c.name === SESSION_COOKIE)?.value;
  const session = parseSessionCookie(raw ? decodeURIComponent(raw) : raw);
  if (!session) throw new Error("Không đọc được session cookie thật để lấy user_id cho câu trả lời bảo mật demo.");
  await page.locator(".otp-answer").fill(`ans-20260802-${session.user_id}`);
  // Nút "Xác nhận" chỉ enable sau khi React xử lý xong TOÀN BỘ onChange
  // của 7 ô nhập (6 OTP + 1 câu trả lời) — chờ enable thật trước khi
  // click thay vì click ngay (phát hiện thật: click quá sớm vào nút vẫn
  // đang disabled do React chưa kịp re-render).
  await expect(page.getByRole("button", { name: "Xác nhận" })).toBeEnabled({ timeout: 5_000 });
  await page.getByRole("button", { name: "Xác nhận" }).click();
  await expect(page.getByText("Xác thực thành công")).toBeVisible({ timeout: 10_000 });
  return true;
}

export async function createTicketAsCustomerViaAI(page: Page, complaintChipLabel = "Tiền chưa về"): Promise<string> {
  await page.locator(".txn-item").first().waitFor({ state: "visible", timeout: 20_000 });
  await page.getByRole("button", { name: "Báo lỗi giao dịch này" }).first().click();
  await page.getByText(complaintChipLabel, { exact: true }).click();

  // KHÔNG cần gửi lại câu hỏi tay nếu có OTP — startComplaint() đã set
  // pendingStarterRef, submitOtp() (ChatClient.tsx) tự động sendToAgent(starter)
  // sau khi xác thực xong (xem completeOtpIfPrompted docstring).
  await completeOtpIfPrompted(page);

  const ticketIdLocator = page.locator(".step-note.mono").first();
  const ticketCreated = await ticketIdLocator
    .waitFor({ state: "visible", timeout: 30_000 })
    .then(() => true)
    .catch(() => false);

  if (!ticketCreated) {
    // Phát hiện thật: nếu giao dịch của khách hàng liên kết tới có trạng
    // thái "success" bình thường (không thật sự lỗi), agent (đúng hành vi
    // hợp lý, không phải bug) hỏi lại xác nhận trước khi tạo hồ sơ thay vì
    // tự tạo ngay — mô phỏng khách trả lời "có" để đẩy tiếp, giống người
    // dùng thật sẽ làm.
    const input = page.getByPlaceholder("Nhập tin nhắn...");
    let gotStepper = false;
    // Tối đa 2 lần gửi nudge — phát hiện thật: chính lượt nudge cũng có thể
    // vượt >60s (cùng nhóm timeout đã biết, xem UX-01/BUG-01), không phải
    // logic sai. Bounded retry, không lặp vô hạn — giống mẫu retry 429 đã
    // dùng ở loginAs().
    for (let attempt = 1; attempt <= 2 && !gotStepper; attempt++) {
      await input.fill("Vâng, hãy tạo hồ sơ khiếu nại giúp tôi để chuyên viên CSKH kiểm tra thêm.");
      await input.press("Enter");
      gotStepper = await ticketIdLocator
        .waitFor({ state: "visible", timeout: 30_000 })
        .then(() => true)
        .catch(() => false);
    }
    if (!gotStepper) {
      // Phát hiện thật (KHÔNG phải bug ở helper): nếu lượt trước đó thật sự
      // đã vượt >60s (xem BACKEND_FETCH_TIMEOUT_MS/lib/api.ts) và client bỏ
      // cuộc, backend/LangGraph vẫn chạy tiếp tới khi xong (tool
      // create_ticket vẫn được gọi thật, ticket vẫn được tạo thật trong DB
      // — đã verify trực tiếp qua SQL). Nhưng graph.py::run_agent_turn chỉ
      // soi `ticket_id` trong CÁC TOOL CALL CỦA ĐÚNG LƯỢT NÀY
      // (`all_messages[prev_len:]`) — lượt nudge kế tiếp chỉ THUẬT LẠI
      // bằng lời ("Mình đã tạo hồ sơ... TCK-...") mà không gọi lại
      // create_ticket, nên `result.ticket_id` rỗng, panel "Trạng thái"
      // (ChatClient.tsx dòng ~617) không bao giờ sáng — dù ticket có thật
      // và CSKH vẫn thấy đúng. Đây là gap thật ở sản phẩm (đã báo cáo lại
      // cho người dùng), KHÔNG sửa kiến trúc ở đây — chỉ làm helper bền
      // vững hơn bằng cách đọc thẳng mã ticket từ NỘI DUNG tin nhắn bot cuối
      // cùng (agent luôn nói rõ mã ticket dạng TCK-xxxxxxxxxxxx khi tạo).
      const lastBotBubble = page.locator(".bubble-bot").last();
      const text = (await lastBotBubble.textContent()) ?? "";
      const match = text.match(/TCK-[a-f0-9]{12}/);
      if (match) return match[0];
      throw new Error(
        `Không thấy panel "Trạng thái" VÀ không tìm được mã ticket TCK- trong tin nhắn bot cuối cùng: "${text}"`
      );
    }
  }

  const ticketId = (await ticketIdLocator.textContent())?.trim();
  if (!ticketId) throw new Error("Không đọc được ticket_id từ UI sau khi tạo khiếu nại qua AI.");
  return ticketId;
}

/** CSKH đề xuất resolution qua BFF thật cho 1 ticket đã có — dùng làm setup
 * nhanh, KHÔNG phải test chính (test chính là /approve dùng resolution này). */
export async function proposeResolutionAsStaff(page: Page, ticketId: string, rationale: string): Promise<void> {
  const resp = await page.request.post("/api/tools/propose-resolution", {
    data: { ticket_id: ticketId, action_type: "refund_to_wallet", rationale, amount: 92_000 },
  });
  if (!resp.ok()) {
    throw new Error(`propose_resolution thất bại (${resp.status()}): ${await resp.text()}`);
  }
}
