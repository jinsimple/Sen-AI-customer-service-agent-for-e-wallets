import { test, expect } from "@playwright/test";
import { createTicketAsCustomerViaAI, loginAs, proposeResolutionAsStaff } from "./helpers/actors";

/**
 * FIN05-StressTest-Plan-v4 P2 — `/approve` (Nhóm A1 v1, Nhóm C v2) chưa có
 * e2e nào dù đây là UI cho HITL cốt lõi — nơi QUYẾT ĐỊNH TÀI CHÍNH THẬT
 * được duyệt. Ưu tiên CAO NHẤT trong P2 theo đúng gap doc.
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
      await loginAs(customerPage, CUSTOMER_PHONE, "Khách hàng", "/chat");
      ticketId = await createTicketAsCustomerViaAI(customerPage, "Tiền chưa về");
    } finally {
      await customerContext.close();
    }

    const staffContext = await browser.newContext();
    const staffPage = await staffContext.newPage();
    try {
      await loginAs(staffPage, "0353000201", "Nhân viên CSKH", "/dashboard");
      await proposeResolutionAsStaff(staffPage, ticketId, "Đối chiếu log giao dịch xác nhận đã trừ tiền, đề xuất hoàn ví.");
    } finally {
      await staffContext.close();
    }

    const supervisorContext = await browser.newContext();
    const supervisorPage = await supervisorContext.newPage();
    try {
      await loginAs(supervisorPage, SUPERVISOR_PHONE, "Sếp phê duyệt", "/approve");
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

      await card.getByRole("button", { name: "Duyệt" }).click();
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
      await loginAs(customerPage, CUSTOMER_PHONE, "Khách hàng", "/chat");
      ticketId = await createTicketAsCustomerViaAI(customerPage, "Trừ tiền 2 lần");
    } finally {
      await customerContext.close();
    }

    const staffContext = await browser.newContext();
    const staffPage = await staffContext.newPage();
    try {
      await loginAs(staffPage, "0353000201", "Nhân viên CSKH", "/dashboard");
      await proposeResolutionAsStaff(staffPage, ticketId, "Chưa đủ căn cứ xác nhận trừ tiền 2 lần, đề xuất từ chối.");
    } finally {
      await staffContext.close();
    }

    const supervisorContext = await browser.newContext();
    const supervisorPage = await supervisorContext.newPage();
    try {
      await loginAs(supervisorPage, SUPERVISOR_PHONE, "Sếp phê duyệt", "/approve");
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
