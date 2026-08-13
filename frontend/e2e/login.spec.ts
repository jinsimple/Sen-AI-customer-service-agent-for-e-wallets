import { test, expect } from "@playwright/test";
import { DEMO_PASSWORD } from "./helpers/actors";

/**
 * FIN05-QA-Test-Report.md (2026-08-11, phiên Claude khác đóng vai khách hàng
 * test tay) — BUG-01 (login treo vô hạn không timeout) và BUG-02 (nút Đăng
 * nhập không disable khi để trống SĐT, submit rỗng im lặng).
 *
 * Đối chiếu lại: BUG-01 KHÔNG tái hiện được qua repro sạch (login với
 * 0851000021 — USR-0021, có thật trong dataset — vào /chat trong <6s, 0 lỗi
 * console) — nhưng code review lộ ra gap thật: fetch() trong
 * frontend/src/app/login/page.tsx không có timeout, nếu request THẬT SỰ treo
 * (mạng, backend đơ) thì loading=true mãi mãi, không có lối thoát nào cho
 * người dùng. Đã sửa (AbortController 10s) dù không tái hiện được hang gốc —
 * đúng khuyến nghị "không bao giờ để loading treo vô hạn" của báo cáo.
 *
 * BUG-02 KHÔNG phải bug thật — input có `required` (HTML5), submit rỗng bị
 * browser chặn native TRƯỚC KHI handleSubmit() chạy (checkValidity()=false,
 * validationMessage="Please fill out this field.", 0 network request) — test
 * dò UI/screenshot của phiên trước không thấy được popup validation native
 * của trình duyệt nên báo nhầm "im lặng không phản hồi gì". Giữ test này lại
 * để xác nhận hành vi đúng, chống regression nếu sau này ai đó lỡ bỏ
 * `required`.
 */
test.describe("Login — BUG-01/BUG-02 (FIN05-QA-Test-Report.md)", () => {
  test("BUG-01: request login treo quá 10s -> hiện lỗi rõ ràng, KHÔNG treo vô hạn", async ({ page }) => {
    // Chặn /api/session, không bao giờ fulfill — mô phỏng đúng kịch bản báo
    // cáo tả: request treo, không network response nào trả về.
    await page.route("**/api/session", async () => {
      await new Promise(() => {}); // không bao giờ resolve — mô phỏng treo thật
    });

    await page.goto("/login");
    await page.getByPlaceholder("09xx xxx xxx").fill("0851000021");
    await page.getByPlaceholder("••••••••").fill(DEMO_PASSWORD);
    await page.getByRole("button", { name: /Đăng nhập/ }).click();

    await expect(page.getByRole("button", { name: "Đang đăng nhập…" })).toBeVisible();
    // Timeout client 10s (page.ts) — assert xong TRONG vòng 13s, không phải
    // "chờ mãi": nút phải quay lại trạng thái bình thường + có lỗi rõ ràng.
    await expect(page.getByText(/phản hồi quá lâu/i)).toBeVisible({ timeout: 13_000 });
    await expect(page.getByRole("button", { name: "Đăng nhập" })).toBeVisible();
    await expect(page.getByRole("button", { name: "Đang đăng nhập…" })).toHaveCount(0);
  });

  test("BUG-02: submit khi để trống SĐT -> browser chặn native, KHÔNG gọi API, KHÔNG im lặng", async ({ page }) => {
    const apiCalls: string[] = [];
    page.on("request", (r) => {
      if (r.url().includes("/api/session")) apiCalls.push(r.url());
    });

    await page.goto("/login");
    await page.getByRole("button", { name: /Đăng nhập/ }).click();
    await page.waitForTimeout(500);

    expect(apiCalls).toHaveLength(0);
    const phoneInput = page.getByPlaceholder("09xx xxx xxx");
    expect(await phoneInput.evaluate((el: HTMLInputElement) => el.checkValidity())).toBe(false);
    expect(await phoneInput.evaluate((el: HTMLInputElement) => el.validationMessage)).not.toBe("");
    // Vẫn ở /login — không crash, không chuyển trang nhầm.
    expect(page.url()).toContain("/login");
  });
});
