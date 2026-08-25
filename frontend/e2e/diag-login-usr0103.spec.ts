import { test, expect } from "@playwright/test";
import { loginAs } from "./helpers/actors";

// TẠM THỜI, GIỮ LÀM BẰNG CHỨNG — kiểm login-only cho ứng viên fixture kịch
// bản chuyên gia 8 lượt (buổi tốn phí 25/08, không tốn LLM). PO đề nghị
// USR-0103/0526000103 (TXN20260801000096) nhưng tự nhận CHƯA kiểm đăng
// nhập được. Kiểm thật: FAIL — trang login xác nhận "Số điện thoại hoặc mật
// khẩu không đúng"; chỉ 4 tài khoản demo (0974000145/0353000201/0905000205/
// partner_admin) dùng chung Demo@123, mọi user khác trong dataset có mật
// khẩu ngẫu nhiên riêng — không dùng để test tay (xem chính trang /login).
// ⟹ đổi sang fixture trên tài khoản khách hàng demo đã verify (0974000145,
// TXN20260728000108, 339.000đ, đã dùng xuyên suốt các e2e khác trong đợt).
test("USR-0103 (0526000103) KHÔNG login được — mật khẩu ngẫu nhiên, không phải demo", async ({ page }) => {
  test.setTimeout(20_000);
  await page.goto("/login");
  await page.getByPlaceholder("09xx xxx xxx").fill("0526000103");
  await page.getByPlaceholder("••••••••").fill("Demo@123");
  await page.getByRole("button", { name: "Đăng nhập" }).click();
  await expect(page.getByText("Số điện thoại hoặc mật khẩu không đúng")).toBeVisible({ timeout: 10_000 });
});

test("USR-0145 (0974000145, tài khoản khách hàng demo) login OK — fixture thay thế", async ({ page }) => {
  test.setTimeout(20_000);
  await loginAs(page, "0974000145", "/chat");
  await expect(page).toHaveURL(/\/chat/);
});
