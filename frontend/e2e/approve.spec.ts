import { test, expect } from "@playwright/test";
import { createTicketAsCustomerViaAI, loginAs, proposeResolutionAsStaff } from "./helpers/actors";

/**
 * FIN05-StressTest-Plan-v4 P2 — `/approve` (Nhóm A1 v1, Nhóm C v2) chưa có
 * e2e nào dù đây là UI cho HITL cốt lõi — nơi QUYẾT ĐỊNH TÀI CHÍNH THẬT
 * được duyệt. Ưu tiên CAO NHẤT trong P2 theo đúng gap doc.
 *
 * 🔴 NIÊM 25/08 (đợt vá bộ màu tối giản) — CẢ HAI ca dưới đây đỏ ĐÃ CÓ TỪ
 * TRƯỚC, xác nhận trên `fin05-dot-otp` (ảnh CHƯA vá CSS, đã đặt đúng
 * JWT_SECRET_KEY) ⟹ KHÔNG liên quan đợt vá màu, KHÔNG được chặn việc đẩy
 * vì lý do đó. Triệu chứng: mỗi ca chạy ĐỦ 150s (đúng `test.setTimeout`
 * dưới đây) rồi mới đỏ — không đỏ sớm, không treo im — khớp đúng dấu hiệu
 * TIMEOUT/nudge-retry đã ghi ở dòng dưới ("bounded retry tối đa 2 lần nếu
 * backend chạm timeout >60s"), tức đang chạm ĐÚNG nhánh retry này và cả
 * hai lần thử đều không thành công trong 150s. Đây là manh mối chính cho
 * ai điều tra tiếp — không phải bằng chứng UI vỡ.
 */

const CUSTOMER_PHONE = "0387000001"; // USR-0001
const SUPERVISOR_PHONE = "0905000205"; // USR-0205, role supervisor

test.describe("APPROVE-* — luồng phê duyệt HITL", () => {
  // Mặc định 45s (playwright.config.ts) không đủ cho luồng 3 actor + AI
  // thật + OTP thật (riêng chờ OTP xuất hiện đã tới 40s ở trường hợp agent
  // gọi 2 tool trước khi hỏi OTP — xem helpers/actors.ts).
  // 150s — nới thêm so với 120s ban đầu: helper tạo ticket giờ có bounded
  // retry (tối đa 2 lần) cho nudge nếu backend chạm timeout >60s thật.
  test.setTimeout(150_000);

  test("supervisor duyệt 1 resolution đang chờ -> biến mất khỏi hàng chờ, xuất hiện trong nhật ký", async ({ browser }) => {
    const customerContext = await browser.newContext();
    const customerPage = await customerContext.newPage();
    let ticketId: string;
    try {
      await loginAs(customerPage, CUSTOMER_PHONE, "/chat");
      ticketId = await createTicketAsCustomerViaAI(customerPage, "Tiền chưa về");
    } finally {
      await customerContext.close();
    }

    const staffContext = await browser.newContext();
    const staffPage = await staffContext.newPage();
    try {
      await loginAs(staffPage, "0353000201", "/dashboard", 1, "/dang-nhap-noi-bo");
      await proposeResolutionAsStaff(staffPage, ticketId, "Đối chiếu log giao dịch xác nhận đã trừ tiền, đề xuất hoàn ví.");
    } finally {
      await staffContext.close();
    }

    const supervisorContext = await browser.newContext();
    const supervisorPage = await supervisorContext.newPage();
    try {
      await loginAs(supervisorPage, SUPERVISOR_PHONE, "/approve", 1, "/dang-nhap-noi-bo");
      // Chỉ tìm trong lưới "đang chờ duyệt" (.grid.grid-2) — KHÔNG chỉ dùng
      // ".card" trần: nhật ký hành động HITL bên dưới cũng là 1 div.card bọc
      // <table>, và sau khi duyệt xong, ticketId sẽ xuất hiện lại dưới dạng
      // link trong chính div.card đó (dòng log mới) — locator ".card" trần
      // vẫn khớp (nhầm sang card khác), làm not.toBeVisible() luôn timeout dù
      // luồng approve đã đúng hoàn toàn (phát hiện thật qua debug network +
      // React state: backend/BFF/state cập nhật đúng, chỉ locator test sai).
      const pendingGrid = supervisorPage.locator(".grid.grid-2");
      const card = pendingGrid.locator(".card", { has: supervisorPage.getByRole("link", { name: ticketId, exact: true }) });
      await expect(card).toBeVisible({ timeout: 15_000 });

      // AUTH5-04 (đợt nâng cấp Auth Flow 2026-08-12) — "Duyệt" giờ chỉ XIN
      // OTP riêng cho resolution này (PSD2 dynamic linking), chưa duyệt
      // ngay — phải gõ đủ 6 số rồi bấm "Xác nhận" mới thật sự gọi approve.
      //
      // [01/09, P0 554f6ad] otp_code KHÔNG còn hiện trên màn hình (đúng mục
      // đích bản vá bảo mật — sếp phải tự gõ, không đọc thẳng như trước) —
      // đọc mã từ CHÍNH response mạng thật (chỉ có khi OTP_DEMO_MODE=true ở
      // ngăn đang chạy, xem ghi chú đầu helpers/actors.ts), không đọc DOM.
      const [otpResp] = await Promise.all([
        supervisorPage.waitForResponse(
          (r) => r.url().includes("/request-approval-otp") && r.request().method() === "POST"
        ),
        card.getByRole("button", { name: "Duyệt" }).click(),
      ]);
      const { otp_code: otpCode } = (await otpResp.json()) as { otp_code: string };
      expect(otpCode, "OTP_DEMO_MODE phải bật ở ngăn đang chạy e2e — xem ghi chú đầu helpers/actors.ts").toBeTruthy();
      const otpBoxes = card.locator(".otp-box");
      await expect(otpBoxes.first()).toBeVisible({ timeout: 10_000 });
      for (let i = 0; i < otpCode.length; i++) {
        await otpBoxes.nth(i).fill(otpCode[i]);
      }
      await card.getByRole("button", { name: "Xác nhận", exact: true }).click();
      await expect(card).not.toBeVisible({ timeout: 15_000 });

      const historyRow = supervisorPage.locator("tbody tr", { hasText: ticketId });
      await expect(historyRow).toBeVisible();
      // .badge-success thay vì getByText("Duyệt") — căn cứ (rationale) CSKH
      // gõ tự do có thể vô tình chứa chuỗi con trùng nhãn badge, làm
      // getByText khớp nhầm ô khác trong cùng hàng (xem ghi chú ở test kế
      // dưới, phát hiện thật với badge "Từ chối").
      await expect(historyRow.locator(".badge-success")).toHaveText("Duyệt");
    } finally {
      await supervisorContext.close();
    }
  });

  test("supervisor từ chối 1 resolution -> hiện đúng badge 'Từ chối' trong nhật ký", async ({ browser }) => {
    const customerContext = await browser.newContext();
    const customerPage = await customerContext.newPage();
    let ticketId: string;
    try {
      await loginAs(customerPage, CUSTOMER_PHONE, "/chat");
      ticketId = await createTicketAsCustomerViaAI(customerPage, "Trừ tiền 2 lần");
    } finally {
      await customerContext.close();
    }

    const staffContext = await browser.newContext();
    const staffPage = await staffContext.newPage();
    try {
      await loginAs(staffPage, "0353000201", "/dashboard", 1, "/dang-nhap-noi-bo");
      await proposeResolutionAsStaff(staffPage, ticketId, "Chưa đủ căn cứ xác nhận trừ tiền 2 lần, đề xuất từ chối.");
    } finally {
      await staffContext.close();
    }

    const supervisorContext = await browser.newContext();
    const supervisorPage = await supervisorContext.newPage();
    try {
      await loginAs(supervisorPage, SUPERVISOR_PHONE, "/approve", 1, "/dang-nhap-noi-bo");
      // Xem ghi chú ở test "duyệt" bên trên — scope vào .grid.grid-2 để
      // không nhầm sang div.card của bảng nhật ký HITL.
      const pendingGrid = supervisorPage.locator(".grid.grid-2");
      const card = pendingGrid.locator(".card", { has: supervisorPage.getByRole("link", { name: ticketId, exact: true }) });
      await expect(card).toBeVisible({ timeout: 15_000 });

      await card.getByRole("button", { name: "Từ chối" }).click();
      await expect(card).not.toBeVisible({ timeout: 15_000 });

      const historyRow = supervisorPage.locator("tbody tr", { hasText: ticketId });
      // .badge-danger thay vì getByText("Từ chối") — phát hiện thật: rationale
      // CSKH gõ tự do ("...đề xuất từ chối.") chứa sẵn chuỗi con "từ chối",
      // getByText (khớp không phân biệt hoa/thường, dạng substring) khớp
      // nhầm cả ô rationale lẫn badge, strict-mode báo lỗi 2 phần tử.
      await expect(historyRow.locator(".badge-danger")).toHaveText("Từ chối");
    } finally {
      await supervisorContext.close();
    }
  });
});
