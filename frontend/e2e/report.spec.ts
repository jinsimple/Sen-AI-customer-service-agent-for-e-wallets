import { test, expect } from "@playwright/test";
import { loginAs } from "./helpers/actors";

/**
 * FIN05-StressTest-Plan-v4 P2 — `/report` (Webapp Sếp, US-018) chưa có e2e
 * nào. Dùng dữ liệu ticket THẬT đã có sẵn (không cần tạo mới — báo cáo tính
 * trực tiếp từ toàn bộ dữ liệu ticket hiện có, US-018 "không phải ước
 * lượng"). Verify KPI hiển thị + bộ lọc ngày thực sự đổi số liệu.
 */
const SUPERVISOR_PHONE = "0905000205";

test.describe("REPORT-* — báo cáo vận hành (Sếp)", () => {
  test("hiện đủ 4 KPI + 2 biểu đồ phân bố với dữ liệu thật", async ({ page }) => {
    await loginAs(page, SUPERVISOR_PHONE, "Sếp phê duyệt", "/approve");
    await page.goto("/report");

    const kpiCards = page.locator(".kpi");
    await expect(kpiCards).toHaveCount(4, { timeout: 15_000 });

    const totalTicketsCard = kpiCards.filter({ hasText: "Tổng ticket trong kỳ" });
    const totalTicketsText = await totalTicketsCard.locator(".kpi-value").textContent();
    expect(Number(totalTicketsText)).toBeGreaterThan(0);

    // Barchart phân bố — phải hiện ít nhất 1 hàng (dữ liệu thật đã có nhiều
    // ticket đủ 4 loại khiếu nại từ seed_demo_scenarios.py + các test khác).
    const complaintTypeCard = page.locator(".card", { hasText: "Phân bố theo loại khiếu nại" });
    await expect(complaintTypeCard.locator(".barrow").first()).toBeVisible();

    const scopeCard = page.locator(".card", { hasText: "Phân bố theo phạm vi giao dịch" });
    await expect(scopeCard.locator(".barrow").first()).toBeVisible();
  });

  test("lọc theo khoảng ngày trong tương lai (chưa có ticket nào) -> tổng ticket = 0, không lỗi", async ({ page }) => {
    await loginAs(page, SUPERVISOR_PHONE, "Sếp phê duyệt", "/approve");
    await page.goto("/report");
    await expect(page.locator(".kpi")).toHaveCount(4, { timeout: 15_000 });

    // Khoảng ngày xa trong tương lai — chắc chắn không có ticket nào rơi vào,
    // xác nhận filter thật sự lọc (không phải luôn trả về toàn bộ dữ liệu).
    const dateInputs = page.locator('input[type="date"]');
    await dateInputs.nth(0).fill("2030-01-01");
    await dateInputs.nth(1).fill("2030-01-02");
    await page.getByRole("button", { name: "Áp dụng" }).click();

    const totalTicketsCard = page.locator(".kpi", { hasText: "Tổng ticket trong kỳ" });
    await expect(totalTicketsCard.locator(".kpi-value")).toHaveText("0", { timeout: 15_000 });
    await expect(page.locator(".note", { hasText: /không|lỗi/i })).not.toBeVisible();
  });
});
