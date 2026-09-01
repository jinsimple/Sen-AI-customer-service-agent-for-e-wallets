import { test, expect } from "@playwright/test";
import { loginAs } from "./helpers/actors";

/**
 * FIN05-StressTest-Plan-v4 P2 — `/policy-lookup` (Webapp CSKH, tra cứu
 * chính sách/FAQ) chưa có e2e nào. Setup: đăng nhập partner_admin, tải lên 1
 * tài liệu chính sách với nội dung ĐẶC TRƯNG (chuỗi ngẫu nhiên duy nhất, để
 * chắc chắn kết quả tìm được LÀ đúng tài liệu vừa tải lên, không nhầm với
 * tài liệu có sẵn nào khác) — rồi CSKH tra cứu lại đúng nội dung đó qua UI.
 */
const PARTNER_ADMIN_PHONE = "0900000001";
const CSKH_PHONE = "0353000201";

test.describe("POLICY-LOOKUP-* — tra cứu chính sách/FAQ (CSKH)", () => {
  test("tra đúng nội dung tài liệu vừa tải lên; tra chuỗi không tồn tại -> báo không tìm thấy", async ({ browser }) => {
    const uniqueMarker = `MARKER${Date.now()}`;
    const filename = `e2e-policy-lookup-${Date.now()}.txt`;

    const adminContext = await browser.newContext();
    const adminPage = await adminContext.newPage();
    try {
      await loginAs(adminPage, PARTNER_ADMIN_PHONE, "/knowledge", 1, "/dang-nhap-noi-bo");
      await adminPage.setInputFiles('input[type="file"]', {
        name: filename,
        mimeType: "text/plain",
        buffer: Buffer.from(
          `Chính sách đặc biệt ${uniqueMarker}: phí rút tiền về ngân hàng đối tác là 0 đồng trong chương trình khuyến mãi thử nghiệm.`
        ),
      });
      await adminPage.getByRole("button", { name: "Tải lên" }).click();
      await expect(adminPage.locator("tbody tr", { hasText: filename }).locator(".badge-success")).toHaveText(
        "Đã lập chỉ mục",
        { timeout: 20_000 }
      );
    } finally {
      await adminContext.close();
    }

    const staffContext = await browser.newContext();
    const staffPage = await staffContext.newPage();
    try {
      await loginAs(staffPage, CSKH_PHONE, "/dashboard", 1, "/dang-nhap-noi-bo");
      await staffPage.goto("/policy-lookup");

      await staffPage.getByPlaceholder(/phí rút tiền, thời gian hoàn tiền/).fill(uniqueMarker);
      await staffPage.getByRole("button", { name: "Tìm kiếm" }).click();

      const resultCard = staffPage.locator(".card", { hasText: filename });
      await expect(resultCard).toBeVisible({ timeout: 15_000 });
      await expect(resultCard).toContainText(uniqueMarker);

      // Tra 1 chuỗi chắc chắn không khớp tài liệu nào — UI phải báo rõ,
      // KHÔNG bịa/hiện lại kết quả cũ.
      await staffPage.getByPlaceholder(/phí rút tiền, thời gian hoàn tiền/).fill(`khong-ton-tai-${Date.now()}-xyz`);
      await staffPage.getByRole("button", { name: "Tìm kiếm" }).click();
      await expect(
        staffPage.getByText("Chưa tìm thấy tài liệu chính sách nào khớp với câu hỏi này.")
      ).toBeVisible({ timeout: 15_000 });
    } finally {
      await staffContext.close();
    }
  });
});
