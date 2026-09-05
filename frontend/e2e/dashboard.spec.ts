import { test, expect } from "@playwright/test";
import { loginAs } from "./helpers/actors";

/**
 * FIN05-StressTest-Plan-v4 P2 — `/dashboard` (Webapp CSKH, US-011/US-014)
 * chưa có e2e nào. Dùng dữ liệu ticket THẬT đã có sẵn trong DB (seed demo +
 * ticket sinh ra từ các test khác chạy trước đó trong ngày — dashboard
 * không cần dữ liệu "sạch", chỉ cần CÓ ít nhất 1 ticket để verify bảng/lọc
 * hoạt động đúng, không assert số lượng tuyệt đối).
 *
 * [polish trước quay 04/09] `GET /tickets` đổi sang phân trang thật
 * (page/page_size 30/50/100) + bộ lọc server (complaint_type/scope/priority/
 * status/SLA) thay cho chip đếm-toàn-cửa-sổ cũ — test này cập nhật theo UI
 * mới (select "Trạng thái" + chân trang "Trang X/Y — tổng N vé khớp bộ lọc"),
 * không còn dùng chip "Tất cả (N)"/"Chờ tiếp nhận (N)" (đã bỏ).
 */
const CSKH_PHONE = "0353000201";

test.describe("DASHBOARD-* — hàng chờ ticket CSKH", () => {
  test("hiện bảng ticket có phân trang, lọc theo trạng thái, click hàng điều hướng sang ticket detail", async ({
    page,
  }) => {
    await loginAs(page, CSKH_PHONE, "/dashboard", 1, "/dang-nhap-noi-bo");

    const rows = page.locator("tbody tr");
    await expect(rows.first()).toBeVisible({ timeout: 15_000 });
    const totalRows = await rows.count();
    expect(totalRows).toBeGreaterThan(0);
    expect(totalRows).toBeLessThanOrEqual(50); // page_size mặc định

    // Chân trang phải khai đúng tổng số vé khớp bộ lọc hiện tại (>= số dòng
    // đang hiện — bằng nhau chỉ khi tổng hệ thống <= page_size).
    const footerText = (await page.getByText(/Trang \d+\/\d+ — tổng \d+ vé khớp bộ lọc/).textContent()) ?? "";
    const footerTotal = Number(footerText.match(/tổng (\d+) vé/)?.[1]);
    expect(footerTotal).toBeGreaterThanOrEqual(totalRows);

    // Lọc "Trạng thái" = Chờ CSKH tiếp nhận — mọi dòng còn lại phải đúng trạng
    // thái đó (không đoán số lượng, đọc trực tiếp từ bảng sau khi lọc).
    await page.locator("#tls-hitl-status").selectOption("pending");
    await page.waitForTimeout(300); // debounce refetch qua useEffect
    const rowsAfterFilter = page.locator("tbody tr");
    const rowCountAfterFilter = await rowsAfterFilter.count();
    if (rowCountAfterFilter > 0 && !(await page.getByText("Không có ticket nào khớp bộ lọc.").isVisible())) {
      const statusCells = page.locator('tbody tr td[data-label="Trạng thái"]');
      const n = await statusCells.count();
      for (let i = 0; i < n; i++) {
        await expect(statusCells.nth(i)).toContainText("Chờ CSKH tiếp nhận");
      }
    }

    // "Xoá bộ lọc" xuất hiện khi có bộ lọc đang bật, bấm để quay về trạng
    // thái không lọc.
    await page.getByText("Xoá bộ lọc").click();
    await expect(page.locator("#tls-hitl-status")).toHaveValue("");

    // Click 1 hàng, xác nhận điều hướng đúng sang /tickets/<id>
    const firstRow = page.locator("tbody tr").first();
    const ticketId = (await firstRow.locator("td").first().textContent())?.trim();
    expect(ticketId).toMatch(/^TCK-/);
    await firstRow.click();
    await page.waitForURL(`**/tickets/${ticketId}`, { timeout: 10_000 });
  });

  test("ô tìm kiếm lọc theo mã ticket (trong trang hiện tại)", async ({ page }) => {
    await loginAs(page, CSKH_PHONE, "/dashboard", 1, "/dang-nhap-noi-bo");

    const rows = page.locator("tbody tr");
    await expect(rows.first()).toBeVisible({ timeout: 15_000 });
    const ticketId = (await rows.first().locator("td").first().textContent())?.trim();
    expect(ticketId).toMatch(/^TCK-/);

    await page.getByPlaceholder(/Tìm theo mã ticket, mã khiếu nại, tên khách/).fill(ticketId!);
    await expect(rows).toHaveCount(1);
    await expect(rows.first()).toContainText(ticketId!);
  });

  test("đổi số dòng/trang cập nhật lại bảng và chân trang", async ({ page }) => {
    await loginAs(page, CSKH_PHONE, "/dashboard", 1, "/dang-nhap-noi-bo");

    const rows = page.locator("tbody tr");
    await expect(rows.first()).toBeVisible({ timeout: 15_000 });

    await page.locator("#tls-page-size").selectOption("30");
    await page.waitForTimeout(300);
    const rowsAfter = await page.locator("tbody tr").count();
    expect(rowsAfter).toBeLessThanOrEqual(30);
    await expect(page.getByText(/Số dòng\/trang/)).toBeVisible();
  });
});
