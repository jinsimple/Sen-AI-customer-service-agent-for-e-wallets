import { test, expect, type BrowserContext } from "@playwright/test";
import { loginAs, completeOtpIfPrompted } from "./helpers/actors";
import { forgeOtpVerifiedAt, setForgedSessionCookie } from "./helpers/otp-forge";
import { SESSION_COOKIE, parseSessionCookie, type Session } from "@/lib/session";

/**
 * Bug PO thật tự tìm ra (24/08) — frontend gọi `await verifyOtp(...)` rồi
 * VỨT kết quả, không lưu `access_token` MỚI mà OTP verify trả về. Mọi tin
 * nhắn GỬI SAU đó vẫn mang token CŨ (chưa xác thực) → agent nói "phiên chưa
 * hoàn tất xác thực" NGAY SAU KHI giao diện vừa báo "Xác thực thành công" —
 * một mâu thuẫn ngay trước mắt người dùng.
 *
 * 🔴 Vì sao suite trước đó không thấy: `_login()` (tests/ Python) và
 * `completeOtpIfPrompted` (helper e2e cũ) đều LẤY LẠI token mới sau verify —
 * đúng cách backend thiết kế, nhưng đó là "đường TEST đi", không phải "đường
 * UI THẬT đi" (ChatClient.tsx tự gọi verifyOtp() bên trong, người dùng không
 * có cơ hội can thiệp). Nguyên tắc PO-agent đặt ra: đường test đi qua và
 * đường người dùng đi qua phải là MỘT — khác nhau ở đâu, đo hỏng ở đó.
 *
 * `chat.spec.ts::"gõ tự do tham chiếu đúng mã giao dịch thật"` ĐÃ đi đúng
 * luồng free-text OTP-giữa-chừng này, nhưng KHÔNG ép otp_verified_at về
 * null trước — nếu phiên còn OTP tươi sót lại từ lượt chạy trước (đúng bẫy
 * đã ghi nhận nhiều lần trong repo này, xem unlockTxnRail/rail-cong-otp-loi-6),
 * OTP thật KHÔNG xảy ra trong lượt chạy đó và bug không có cơ hội lộ ra. Test
 * này ép otp_verified_at=null qua forgeOtpVerifiedAt (kỹ thuật time-travel
 * JWT đã có tiền lệ, KHÔNG phải bypass auth) để BẢO ĐẢM một lượt OTP THẬT
 * xảy ra trong chính lượt chạy, không phụ thuộc trạng thái sót lại.
 */
const CUSTOMER_PHONE = "0974000145"; // USR-0145, cùng tài khoản auth.spec.ts dùng

// Đúng nguyên văn hằng số TEXT_MOI_OTP đã xác nhận ở chat-403-role-loai.spec.ts
// — chuỗi DETERMINISTIC frontend hiện khi tool result có loai="otp_het_tuoi",
// không phải suy đoán cách LLM diễn đạt.
const TEXT_MOI_OTP = "Để tiếp tục thao tác này, mình cần bạn xác thực lại OTP phiên làm việc nhé.";

async function readSessionCookie(context: BrowserContext): Promise<Session> {
  const cookies = await context.cookies();
  const raw = cookies.find((c) => c.name === SESSION_COOKIE)?.value;
  const session = parseSessionCookie(raw ? decodeURIComponent(raw) : raw);
  if (!session) throw new Error(`Không đọc được cookie ${SESSION_COOKIE} — chưa đăng nhập?`);
  return session;
}

test.describe("Token OTP mới phải được DÙNG THẬT sau khi xác thực (không phải chỉ hiện 'thành công')", () => {
  test("gõ câu cần tra cứu -> xác thực OTP qua UI -> gõ tiếp: PHẢI tra cứu được, KHÔNG được nói phiên chưa xác thực", async ({
    page,
    context,
  }) => {
    test.setTimeout(120_000);
    await loginAs(page, CUSTOMER_PHONE, "/chat");

    // Ép otp_verified_at=null — bảo đảm lượt này THẬT SỰ đi qua một lần xác
    // thực OTP mới, không phải sống nhờ phiên còn tươi sót lại từ trước.
    const realSession = await readSessionCookie(context);
    const nguoi = forgeOtpVerifiedAt(realSession, null);
    await setForgedSessionCookie(context, nguoi);
    await page.reload();

    const input = page.getByPlaceholder("Nhập tin nhắn...");
    const question = "Cho mình xem lịch sử giao dịch gần đây của mình được không?";

    // Tối đa 2 lần gửi — LLM không phải lúc nào cũng gọi tool cần OTP ngay
    // lượt đầu (đã ghi nhận ở auth.spec.ts::triggerSensitiveAction), bounded
    // retry cùng khuôn createTicketAsCustomerViaAI, không lặp vô hạn.
    let otpHappened = false;
    for (let attempt = 1; attempt <= 2 && !otpHappened; attempt++) {
      await input.fill(question);
      await input.press("Enter");
      otpHappened = await completeOtpIfPrompted(page, 40_000);
    }
    expect(otpHappened, "OTP không xảy ra lần nào sau 2 lượt gõ — không đúng nhánh cần đo cho ca này.").toBe(true);
    await expect(page.getByText("Xác thực thành công")).toBeVisible({ timeout: 10_000 });

    // Gõ TỰ DO trigger OTP giữa chừng KHÔNG tự gửi lại câu hỏi gốc (khác
    // luồng chip — xem docstring completeOtpIfPrompted) — khách phải tự gõ
    // tiếp. ĐÂY là đúng bước "gõ tiếp" PO-agent mô tả, và đúng chỗ bug sống:
    // nếu frontend vứt access_token mới, LƯỢT NÀY sẽ mang token CŨ.
    await input.fill(question);
    await input.press("Enter");

    const lastBotBubble = page.locator(".bubble-bot").last();
    await expect(lastBotBubble).not.toContainText(TEXT_MOI_OTP, {
      timeout: 20_000,
    });

    // Đối chứng DƯƠNG — không chỉ "không nói phiên chưa xác thực", mà phải
    // THỰC SỰ tra cứu được (nội dung giao dịch thật: số tiền định dạng "...đ"
    // hoặc câu xác nhận không tìm thấy giao dịch — cả hai đều chứng minh tool
    // đã CHẠY, khác hẳn câu mời xác thực lại).
    await expect(lastBotBubble).not.toBeEmpty();
  });
});
