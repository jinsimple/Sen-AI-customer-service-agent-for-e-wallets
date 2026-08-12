import { test, expect } from "@playwright/test";
import { completeOtpIfPrompted, createTicketAsCustomerViaAI, loginAs } from "./helpers/actors";

/**
 * FIN05-StressTest-Plan-v4 GAP-FE-007 — `/chat` nhánh AI (chip chọn loại
 * khiếu nại, rail "Giao dịch gần đây"/"Lịch sử khiếu nại", luồng tạo ticket
 * đầy đủ) CHƯA có e2e nào coi ChatClient LÀ CHỦ THỂ CHÍNH — `createTicketAsCustomerViaAI`
 * (helpers/actors.ts) đã exercise gần hết luồng này, nhưng LUÔN LÀ BƯỚC SETUP
 * cho test khác (approve.spec.ts, ticket-detail.spec.ts), chưa từng tự nó
 * assert trên hành vi RIÊNG của ChatClient — cụ thể: rail "Lịch sử khiếu
 * nại của bạn" có thực sự TỰ LÀM MỚI (client-side, không cần F5) ngay sau
 * khi tạo ticket hay không (code comment ChatClient.tsx dòng ~381 khẳng
 * định có, nhưng chưa có test nào xác nhận).
 */
const CUSTOMER_PHONE = "0387000001"; // USR-0001

test.describe("CHAT-* — chatbot AI khách hàng, rail & luồng tạo ticket", () => {
  test("rail 'Giao dịch gần đây' hiện dữ liệu thật khi vào trang", async ({ page }) => {
    await loginAs(page, CUSTOMER_PHONE, "Khách hàng", "/chat");

    const txnItems = page.locator(".txn-item");
    await expect(txnItems.first()).toBeVisible({ timeout: 15_000 });
    const count = await txnItems.count();
    expect(count).toBeGreaterThan(0);

    // Mỗi giao dịch phải có số tiền định dạng "...đ" và nút báo lỗi riêng —
    // không phải placeholder/mock tĩnh.
    await expect(txnItems.first().locator(".txn-amount")).toHaveText(/đ$/);
    await expect(txnItems.first().getByRole("button", { name: "Báo lỗi giao dịch này" })).toBeVisible();
  });

  test("rail 'Lịch sử khiếu nại' TỰ LÀM MỚI ngay sau khi tạo ticket qua chip — không cần F5", async ({ page }) => {
    test.setTimeout(150_000);
    await loginAs(page, CUSTOMER_PHONE, "Khách hàng", "/chat");

    const histCard = page.locator(".card", { hasText: "Lịch sử khiếu nại của bạn" });
    await expect(histCard).toBeVisible({ timeout: 15_000 });
    // Chờ rail load xong (dim placeholder HOẶC có sẵn item) trước khi đếm
    // baseline — cùng phát hiện thật đã ghi nhận ở knowledge.spec.ts: đếm
    // quá sớm lúc bảng còn rỗng vì CHƯA load xong sẽ ra baseline sai.
    await Promise.race([
      histCard.locator(".hist-item").first().waitFor({ state: "visible", timeout: 10_000 }),
      histCard.getByText("Chưa có khiếu nại nào.").waitFor({ state: "visible", timeout: 10_000 }),
    ]);
    const before = await histCard.locator(".hist-item").count();

    const ticketId = await createTicketAsCustomerViaAI(page, "Tiền chưa về");

    // KHÔNG reload trang — nếu rail chỉ cập nhật sau F5 (không phải
    // client-side tự làm mới như code comment khẳng định), assert này sẽ
    // timeout vì count không đổi cho tới khi ai đó chủ động điều hướng lại.
    await expect(histCard.locator(".hist-item")).toHaveCount(before + 1, { timeout: 15_000 });

    // Item mới nhất phải có label đúng loại khiếu nại vừa chọn.
    const newestItem = histCard.locator(".hist-item").first();
    await expect(newestItem).toContainText("Tiền chưa về");
    // ticketId (TCK-...) không hiện trực tiếp trong rail này (rail hiện
    // complaint_id, không phải ticket_id) — chỉ xác nhận rail có 1 mục mới,
    // không assert nhầm nội dung không có trong UI.
    expect(ticketId).toMatch(/^TCK-/);
  });

  test("gõ tự do tham chiếu đúng mã giao dịch thật -> agent trả lời đúng thông tin giao dịch đó", async ({ page }) => {
    test.setTimeout(90_000);
    await loginAs(page, CUSTOMER_PHONE, "Khách hàng", "/chat");

    const txnItems = page.locator(".txn-item");
    await expect(txnItems.first()).toBeVisible({ timeout: 15_000 });
    const firstTransId = (await txnItems.first().locator(".txn-meta").textContent())?.split("·").pop()?.trim();
    expect(firstTransId).toMatch(/^TXN/);

    const question = `Giao dịch ${firstTransId} của tôi trạng thái thế nào rồi bạn?`;
    const input = page.getByPlaceholder("Nhập tin nhắn...");
    await input.fill(question);
    await input.press("Enter");

    // Gõ tự do trigger OTP giữa chừng KHÔNG tự động gửi lại câu hỏi gốc sau
    // khi xác thực xong (khác luồng chip — xem docstring completeOtpIfPrompted
    // trong helpers/actors.ts) — phải tự gửi lại nếu có OTP xảy ra.
    const otpHappened = await completeOtpIfPrompted(page);
    if (otpHappened) {
      await input.fill(question);
      await input.press("Enter");
    }

    const lastBotBubble = page.locator(".bubble-bot").last();
    await expect(lastBotBubble).toContainText(firstTransId!, { timeout: 30_000 });
  });
});
