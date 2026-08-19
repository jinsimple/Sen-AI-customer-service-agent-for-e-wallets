import { test, expect, type BrowserContext } from "@playwright/test";
import { loginAs, unlockTxnRail } from "./helpers/actors";
import { forgeOtpVerifiedAt, setForgedSessionCookie } from "./helpers/otp-forge";
import { SESSION_COOKIE, parseSessionCookie, type Session } from "@/lib/session";

/**
 * Lỗi 6 (19/08, GĐ4 tiếp) — thẻ "Lịch sử khiếu nại của bạn" trong rail chat
 * KHÔNG có cổng OTP như thẻ "Giao dịch gần đây" đã có, lộ mã/loại/trạng thái
 * khiếu nại (tiền tố "CMP-") trước khi khách xác thực. Coder vá bằng component
 * dùng chung `RailCardGatedByOtp` cho cả hai thẻ.
 *
 * DANH SÁCH TÊN thẻ cần cổng OTP — liệt kê ĐỦ, không đếm số lượng (PO-agon,
 * lỗi "chính sách áp thiếu một nhánh" lặp lại 4 lần trong ngày 19/08). Ai
 * thêm thẻ rail mới mà quên cổng phải làm DANH SÁCH này đỏ, không phải một
 * con số "≥N thẻ bị che" mù trước thẻ thứ N+1.
 */
const CAC_THE_CAN_CONG_OTP = [
  { railTitle: "Giao dịch gần đây", vanBanKhoa: "Xác thực OTP để xem giao dịch gần đây" },
  { railTitle: "Lịch sử khiếu nại của bạn", vanBanKhoa: "Xác thực OTP để xem lịch sử khiếu nại" },
];

const CUSTOMER_PHONE = "0974000145";
// Quá 12h (ngưỡng XEM, AUTH-005/007) — chắc chắn rơi vào trạng thái khoá,
// không phụ thuộc OTP còn tươi sót lại từ lượt test trước đó trên cùng
// tài khoản demo (phát hiện thật lúc viết ca này: OTP thật vừa xác thực ở
// GĐ4 mấy phút trước còn tươi, rail hiện luôn ở trạng thái mở nếu không ép).
const QUA_12H_GIAY = 12 * 60 * 60 + 60;

async function readSessionCookie(context: BrowserContext): Promise<Session> {
  const cookies = await context.cookies();
  const raw = cookies.find((c) => c.name === SESSION_COOKIE)?.value;
  const session = parseSessionCookie(raw ? decodeURIComponent(raw) : raw);
  if (!session) throw new Error(`Không đọc được cookie ${SESSION_COOKIE} — chưa đăng nhập?`);
  return session;
}

test.describe("Lỗi 6 — cổng OTP cho rail phải áp ĐỦ mọi thẻ nhạy cảm", () => {
  test("TRƯỚC OTP (phiên nguội >12h): cả hai thẻ đều khoá, không lộ CMP-/txn-item nào", async ({ page, context }) => {
    // forgeOtpVerifiedAt() cần một session ĐÃ có otp_verified_at thật để
    // neo mốc trừ lùi — xác thực OTP thật MỘT lần trước (qua unlockTxnRail,
    // đường sản phẩm thật), rồi mới đọc session đó ra mà làm nguội đi.
    await loginAs(page, CUSTOMER_PHONE, "/chat");
    await unlockTxnRail(page);
    const realSession = await readSessionCookie(context);
    const nguoi = forgeOtpVerifiedAt(realSession, QUA_12H_GIAY);
    await setForgedSessionCookie(context, nguoi);
    await page.reload();

    for (const the of CAC_THE_CAN_CONG_OTP) {
      await expect(
        page.getByText(the.vanBanKhoa),
        `Thẻ "${the.railTitle}" KHÔNG hiện văn bản khoá "${the.vanBanKhoa}" khi phiên OTP đã nguội (>12h) — thẻ này có thể đang lộ dữ liệu trước xác thực.`
      ).toBeVisible({ timeout: 15_000 });
    }

    // Đối chứng ÂM — không dòng "CMP-" hay .txn-item nào lọt ra trước OTP.
    const noiDungRail = (await page.locator(".chat-rail").first().textContent()) ?? "";
    expect(noiDungRail, "Lộ 'CMP-' (tiền tố complaint_id) TRƯỚC khi xác thực OTP").not.toMatch(/CMP-/);
    expect(await page.locator(".txn-item").count(), "Lộ .txn-item TRƯỚC khi xác thực OTP").toBe(0);
  });

  test("SAU một lượt OTP: CẢ HAI thẻ cùng mở — xác nhận dùng chung một cơ chế, không phải hai cổng độc lập", async ({
    page,
    context,
  }) => {
    // forgeOtpVerifiedAt() cần một session ĐÃ có otp_verified_at thật để
    // neo mốc trừ lùi — xác thực OTP thật MỘT lần trước (qua unlockTxnRail,
    // đường sản phẩm thật), rồi mới đọc session đó ra mà làm nguội đi.
    await loginAs(page, CUSTOMER_PHONE, "/chat");
    await unlockTxnRail(page);
    const realSession = await readSessionCookie(context);
    const nguoi = forgeOtpVerifiedAt(realSession, QUA_12H_GIAY);
    await setForgedSessionCookie(context, nguoi);
    await page.reload();

    // Xác nhận cả hai ĐANG khoá trước khi mở — nếu không, bước "cùng mở
    // sau MỘT lần xác thực" bên dưới không chứng minh được gì (có thể một
    // thẻ vốn đã mở sẵn từ trước).
    for (const the of CAC_THE_CAN_CONG_OTP) {
      await expect(page.getByText(the.vanBanKhoa)).toBeVisible({ timeout: 15_000 });
    }

    // Chỉ bấm ĐÚNG MỘT nút "Xác thực ngay" (nếu có nhiều nút, mỗi thẻ một
    // nút riêng — bấm nút ĐẦU TIÊN, không bấm nút thứ hai).
    const nutXacThuc = page.getByRole("button", { name: "Xác thực ngay" });
    await nutXacThuc.first().click();
    const demoCode = (await page.locator(".otp-meta").first().locator("strong").textContent())?.trim() ?? "";
    const boxes = page.locator(".otp-box");
    for (let i = 0; i < 6; i++) await boxes.nth(i).fill(demoCode[i]);
    await expect(page.getByRole("button", { name: "Xác nhận" })).toBeEnabled({ timeout: 5_000 });
    await page.getByRole("button", { name: "Xác nhận" }).click();
    await expect(page.getByText("Xác thực thành công")).toBeVisible({ timeout: 10_000 });

    // CẢ HAI thẻ phải hết khoá — nếu chỉ thẻ vừa bấm mở còn thẻ kia vẫn
    // khoá, đó là HAI cổng độc lập (không phải cùng RailCardGatedByOtp như
    // Coder khai), và ca "MỘT nút, cả hai mở" của test này sẽ tự lộ điều đó.
    for (const the of CAC_THE_CAN_CONG_OTP) {
      await expect(
        page.getByText(the.vanBanKhoa),
        `Thẻ "${the.railTitle}" VẪN còn khoá sau khi đã xác thực OTP qua thẻ khác — hai thẻ đang dùng HAI cổng độc lập, không phải cùng một cơ chế.`
      ).toHaveCount(0);
    }
    await expect(page.locator(".txn-item").first()).toBeVisible({ timeout: 15_000 });
    await expect(page.getByText(/CMP-/).first()).toBeVisible({ timeout: 15_000 });
  });
});
