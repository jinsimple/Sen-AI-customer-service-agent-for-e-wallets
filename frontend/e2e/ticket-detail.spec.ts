import { test, expect } from "@playwright/test";
import { createTicketAsCustomerViaAI, loginAs } from "./helpers/actors";

/**
 * FIN05-StressTest-Plan-v4 P2 — `/tickets/[id]` chưa có e2e. `approve.spec.ts`
 * đã dùng `proposeResolutionAsStaff` (POST BFF trực tiếp, KHÔNG qua form UI)
 * làm bước setup nhanh — spec này bổ sung phần approve.spec.ts CHƯA test:
 * chính FORM "Hành động của bạn (CSKH)" trên trang ticket detail (US-012,
 * US-015) và investigation trail hiển thị đúng dữ liệu thật.
 */
test.describe("TICKET-DETAIL-* — chi tiết ticket & hành động CSKH", () => {
  // 150s — cùng ngân sách approve.spec.ts dùng cho luồng 3 actor (ở đây chỉ
  // 2 actor, không cần OTP supervisor, nên thừa dư hơn). Xem cùng ghi chú
  // approve.spec.ts về độ trễ LLM thật + nudge retry.
  test.setTimeout(150_000);

  test("CSKH mở ticket thật, thấy investigation trail, trình đề xuất qua FORM UI -> hiện trong 'Đề xuất đã trình'", async ({ browser }) => {
    const customerContext = await browser.newContext();
    const customerPage = await customerContext.newPage();
    let ticketId: string;
    try {
      await loginAs(customerPage, "0387000001", "/chat");
      ticketId = await createTicketAsCustomerViaAI(customerPage, "Tiền chưa về");
    } finally {
      await customerContext.close();
    }

    const staffContext = await browser.newContext();
    const staffPage = await staffContext.newPage();
    try {
      await loginAs(staffPage, "0353000201", "/dashboard");
      await staffPage.goto(`/tickets/${ticketId}`);

      await expect(staffPage.locator("h2.mono")).toHaveText(ticketId);

      // Investigation trail — ticket tạo qua AI phải có ít nhất 1 bước ghi
      // nhận thật (lookup_transaction/create_ticket...), KHÔNG phải rỗng.
      const trailSteps = staffPage.locator(".trail-step");
      await expect(trailSteps.first()).toBeVisible({ timeout: 10_000 });

      // Form "Hành động của bạn (CSKH)" — trình đề xuất qua UI thật, KHÔNG
      // qua BFF trực tiếp (khác proposeResolutionAsStaff của approve.spec.ts).
      await staffPage.locator("select").selectOption("refund_to_wallet");
      await staffPage.locator('input[type="number"]').fill("92000");
      await staffPage.locator("textarea").fill("Đối chiếu log giao dịch qua form UI thật — e2e ticket-detail.spec.ts.");
      await staffPage.getByRole("button", { name: "Trình sếp" }).click();

      await expect(staffPage.getByText("Đã trình sếp — chờ phê duyệt.")).toBeVisible({ timeout: 10_000 });

      const proposedSection = staffPage.locator(".card", { hasText: "Đề xuất đã trình" });
      await expect(proposedSection).toBeVisible();
      // Việt hoá 14/08 (brief docs/giao-viec/2026-08-14-viet-hoa-ui.md): tầng
      // HIỂN THỊ dùng nhãn tiếng Việt, GIÁ TRỊ enum vẫn tiếng Anh (Luật 1) —
      // vì vậy `selectOption("refund_to_wallet")` ở trên KHÔNG đổi, chỉ 2
      // assert text này đổi. Nhãn đã quan sát trên bản build thật 14/08 16:47.
      //   refund_to_wallet -> "Hoàn tiền về ví"  (khớp `mo_ta` trong
      //     contracts/resolution-state-machine.yaml — nhãn có nguồn)
      //   pending_approval -> "Chờ sếp duyệt"    (nguồn: MỆNH ĐỀ ĐẦU của
      //     `mo_ta` — "Đã gửi, chờ sếp duyệt. CỔNG BẮT BUỘC trước mọi hành
      //     động tiền." Nhãn có nguồn contract, đã duyệt 14/08)
      await expect(proposedSection).toContainText("Hoàn tiền về ví");
      await expect(proposedSection).toContainText("Chờ sếp duyệt");
    } finally {
      await staffContext.close();
    }
  });

  test("CSKH bấm 'Yêu cầu điều tra thêm' -> ticket chuyển trạng thái need_more_info", async ({ browser }) => {
    const customerContext = await browser.newContext();
    const customerPage = await customerContext.newPage();
    let ticketId: string;
    try {
      await loginAs(customerPage, "0387000001", "/chat");
      // "Tiền chưa về" thay vì "Trừ tiền 2 lần" — phát hiện thật (lặp lại
      // đúng pattern đã thấy ở approve.spec.ts): chip "Trừ tiền 2 lần"
      // (double_charge) khiến agent cần nhiều vòng tool call hơn (khả năng
      // phải soát thêm giao dịch trùng), thường xuyên cần tới nhánh nudge-
      // retry của createTicketAsCustomerViaAI — cộng dồn dễ vượt ngân sách
      // 150s. Mục tiêu của TEST NÀY là nút "Yêu cầu điều tra thêm", không
      // phụ thuộc complaint_type nào — dùng chip resolve nhanh hơn để tránh
      // đụng ngân sách thời gian một cách không cần thiết.
      ticketId = await createTicketAsCustomerViaAI(customerPage, "Tiền chưa về");
    } finally {
      await customerContext.close();
    }

    const staffContext = await browser.newContext();
    const staffPage = await staffContext.newPage();
    try {
      await loginAs(staffPage, "0353000201", "/dashboard");
      await staffPage.goto(`/tickets/${ticketId}`);
      await expect(staffPage.locator("h2.mono")).toHaveText(ticketId);

      await staffPage.getByRole("button", { name: "Yêu cầu điều tra thêm" }).click();
      await expect(staffPage.getByText("Đã chuyển ticket sang trạng thái cần điều tra thêm.")).toBeVisible({
        timeout: 10_000,
      });
      // HITL_STATUS_LABEL.need_more_info === "Cần điều tra thêm" (lib/types.ts)
      await expect(staffPage.locator(".badge-warning", { hasText: "Cần điều tra thêm" })).toBeVisible();
    } finally {
      await staffContext.close();
    }
  });
});
