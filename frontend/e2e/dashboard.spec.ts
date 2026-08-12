import { test, expect } from "@playwright/test";
import { loginAs } from "./helpers/actors";

/**
 * FIN05-StressTest-Plan-v4 P2 — `/dashboard` (Webapp CSKH, US-011/US-014)
 * chưa có e2e nào. Dùng dữ liệu ticket THẬT đã có sẵn trong DB (seed demo +
 * ticket sinh ra từ các test khác chạy trước đó trong ngày — dashboard
 * không cần dữ liệu "sạch", chỉ cần CÓ ít nhất 1 ticket để verify bảng/lọc
 * hoạt động đúng, không assert số lượng tuyệt đối).
 */
const CSKH_PHONE = "0353000201";

test.describe("DASHBOARD-* — hàng chờ ticket CSKH", () => {
  test("hiện bảng ticket, filter chip đổi đúng số lượng, click hàng điều hướng sang ticket detail", async ({ page }) => {
    await loginAs(page, CSKH_PHONE, "Nhân viên CSKH", "/dashboard");

    const rows = page.locator("tbody tr");
    await expect(rows.first()).toBeVisible({ timeout: 15_000 });
    const totalRows = await rows.count();
    expect(totalRows).toBeGreaterThan(0);

    // Chip "Tất cả (N)" phải khớp đúng N ticket đang hiện trong bảng — nguồn
    // sự thật duy nhất là chính bảng, không hard-code số.
    const allChipText = (await page.locator(".filter-chip", { hasText: "Tất cả" }).textContent()) ?? "";
    const allCount = Number(allChipText.match(/\((\d+)\)/)?.[1]);
    expect(allCount).toBe(totalRows);

    // Bấm filter "Chờ tiếp nhận" — bảng phải thu hẹp lại đúng số ghi trong chip
    const pendingChip = page.locator(".filter-chip", { hasText: "Chờ tiếp nhận" });
    const pendingChipText = (await pendingChip.textContent()) ?? "";
    const pendingCount = Number(pendingChipText.match(/\((\d+)\)/)?.[1]);
    await pendingChip.click();
    await expect(pendingChip).toHaveClass(/active/);
    if (pendingCount > 0) {
      await expect(rows).toHaveCount(pendingCount);
    } else {
      await expect(page.getByText("Không có ticket nào khớp bộ lọc.")).toBeVisible();
    }

    // Quay về "Tất cả", click 1 hàng, xác nhận điều hướng đúng sang /tickets/<id>
    await page.locator(".filter-chip", { hasText: "Tất cả" }).click();
    const firstRow = page.locator("tbody tr").first();
    const ticketId = (await firstRow.locator("td").first().textContent())?.trim();
    expect(ticketId).toMatch(/^TCK-/);
    await firstRow.click();
    await page.waitForURL(`**/tickets/${ticketId}`, { timeout: 10_000 });
  });

  test("ô tìm kiếm lọc theo mã ticket", async ({ page }) => {
    await loginAs(page, CSKH_PHONE, "Nhân viên CSKH", "/dashboard");

    const rows = page.locator("tbody tr");
    await expect(rows.first()).toBeVisible({ timeout: 15_000 });
    const ticketId = (await rows.first().locator("td").first().textContent())?.trim();
    expect(ticketId).toMatch(/^TCK-/);

    await page.getByPlaceholder("Tìm theo mã ticket, mã khiếu nại, tên khách...").fill(ticketId!);
    await expect(rows).toHaveCount(1);
    await expect(rows.first()).toContainText(ticketId!);
  });
});
