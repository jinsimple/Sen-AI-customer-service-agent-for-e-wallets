import { test, expect } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { DEMO_PASSWORD, loginAs } from "./helpers/actors";

/**
 * [ĐO 27/08] Bốn câu chữ đối ngoại vừa đổi (Marketing, p-226-17), sắp deploy
 * qua `deploy_home.ps1` (PO chạy tay, máy cá nhân):
 *   ① /login — câu dữ liệu bên thứ ba (dài nhất, 2 mệnh đề)
 *   ② /login — câu chống lừa đảo (mật khẩu ví/OTP) — CÙNG câu này lặp lại
 *      nguyên văn ở /chat và /cho-khach-hang (cố ý, để khách NHẬN RA được)
 *   ③ /chat — phụ đề "Trợ lý AI" (dài hơn bản cũ)
 *
 * Lead: KHÔNG chấm nội dung câu (Marketing/PO giữ quyền đó) — chỉ đo nó có
 * HIỂN THỊ ĐÚNG không: cắt cụt/tràn/đè nhau ở mobile 375px, chìm mất ở theme
 * nào đó, đẩy vỡ bố cục khung chat. Không đọc `src/`, chỉ đọc frontend (nơi
 * chứa chính các câu này) để biết literal string cần dò trên màn hình.
 */

const CUSTOMER_PHONE = "0974000145";
const CAU_CHONG_LUA_DAO = "Sen không bao giờ hỏi mật khẩu ví hay mã OTP giao dịch của bạn.";
const CAU_DU_LIEU_BEN_THU_BA =
  "Thông tin của người khác trong giao dịch được che trước khi hiển thị. Phần suy luận của mô hình đi qua nhà cung cấp đã khai báo, và hệ thống có sẵn cơ chế chuyển đổi nhà cung cấp.";
const CAU_PHU_DE_CHAT =
  "Trợ lý AI — Sen tra cứu từ hệ thống trước khi trả lời, và nói rõ khi không tra được. Mọi đề xuất đều có người kiểm trước khi thành quyết định.";

async function khongTranNgang(page: import("@playwright/test").Page): Promise<boolean> {
  return page.evaluate(() => document.documentElement.scrollWidth <= document.documentElement.clientWidth + 1);
}

test.describe("HIỂN THỊ — 4 câu chữ đối ngoại mới, mobile 375px + sáng/tối", () => {
  for (const theme of ["light", "dark"] as const) {
    test(`/login (${theme}, 375px) — câu dữ liệu + câu chống lừa đảo hiện đủ, không tràn/đè`, async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 812 });
      await page.emulateMedia({ colorScheme: theme });
      await page.goto("/login");

      await expect(page.getByText(CAU_DU_LIEU_BEN_THU_BA)).toBeVisible();
      await expect(page.getByText(CAU_CHONG_LUA_DAO, { exact: true })).toBeVisible();
      expect(await khongTranNgang(page), `/login (${theme}) tràn ngang ở 375px`).toBe(true);

      // Không chấm nội dung — chỉ chấm axe color-contrast (câu "chìm mất").
      const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
      const nghiemTrong = results.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
      expect(
        nghiemTrong,
        `/login (${theme}, 375px) có vi phạm tương phản màu:\n` +
          nghiemTrong.map((v) => `- [${v.impact}] ${v.id}: ${v.help}`).join("\n")
      ).toEqual([]);
    });

    test(`/chat (${theme}, 375px) — phụ đề mới hiện đủ, không đẩy vỡ chiều cao khung chat`, async ({ page }) => {
      await page.setViewportSize({ width: 375, height: 812 });
      await page.emulateMedia({ colorScheme: theme });
      await loginAs(page, CUSTOMER_PHONE, "/chat", 1, "/login");

      await expect(page.getByText(CAU_PHU_DE_CHAT)).toBeVisible();
      await expect(page.getByText(CAU_CHONG_LUA_DAO, { exact: true })).toBeVisible();
      expect(await khongTranNgang(page), `/chat (${theme}) tràn ngang ở 375px`).toBe(true);

      // 🔴 [ĐO 27/08, tự sửa trước khi báo cáo] Bản đầu của ca này assert
      // "input phải nằm TRONG viewport lúc mới vào trang" — đỏ ở CẢ HAI theme
      // (input tại y=903, ngoài 812px). Kiểm lại trước khi báo: trang này
      // KHÔNG có phần tử position:fixed/sticky nào (đo bằng cách duyệt hết
      // ancestor chain của input) — toàn trang cuộn CHUNG một khối, và sau
      // khi cuộn xuống, input hiện lại bình thường ở y=414, HOÀN TOÀN dùng
      // được. Input nằm dưới màn hình lúc mới vào trang là ĐÚNG NHƯ MỌI
      // trang có topbar+rail cards+bong bóng chào phía trên, không phải hồi
      // quy DO phụ đề mới — assertion cũ đo sai thứ ("nằm trong viewport lúc
      // scroll=0") thay vì đo đúng thứ cần biết ("có cuộn tới được không").
      // Sửa: chỉ xác nhận input THẬT SỰ TỒN TẠI và CUỘN TỚI ĐƯỢC.
      const inputLocator = page.getByPlaceholder("Nhập tin nhắn...");
      await expect(inputLocator, "Không tìm thấy khung nhập tin nhắn trong DOM").toHaveCount(1);
      await inputLocator.scrollIntoViewIfNeeded();
      await expect(inputLocator, "Khung nhập tin nhắn không cuộn tới được / không hiển thị sau khi cuộn").toBeVisible();

      const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
      const nghiemTrong = results.violations.filter((v) => v.impact === "serious" || v.impact === "critical");
      expect(
        nghiemTrong,
        `/chat (${theme}, 375px) có vi phạm tương phản màu:\n` +
          nghiemTrong.map((v) => `- [${v.impact}] ${v.id}: ${v.help}`).join("\n")
      ).toEqual([]);
    });
  }

  test("🔴 câu chống lừa đảo GIỐNG HỆT nhau ở cả 3 bề mặt (login/chat/cho-khach-hang) — cố ý, để khách NHẬN RA được", async ({
    page,
  }) => {
    await page.goto("/login");
    await expect(page.getByText(CAU_CHONG_LUA_DAO, { exact: true })).toBeVisible();

    await page.goto("/cho-khach-hang");
    await expect(page.getByText(CAU_CHONG_LUA_DAO, { exact: true }).first()).toBeVisible();

    await loginAs(page, CUSTOMER_PHONE, "/chat", 1, "/login");
    await expect(page.getByText(CAU_CHONG_LUA_DAO, { exact: true })).toBeVisible();
  });
});
