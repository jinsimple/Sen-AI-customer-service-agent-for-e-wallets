import "server-only";
import { cookies } from "next/headers";
import { parseSessionCookie, SESSION_COOKIE, type Session } from "@/lib/session";

export async function getServerSession(): Promise<Session | null> {
  const store = await cookies();
  return parseSessionCookie(store.get(SESSION_COOKIE)?.value);
}

// M-10 (ghi sổ 14/08) / Finding A GĐ2.5 — F5 sau khi đã xác thực OTP làm rail
// "Giao dịch gần đây" khoá lại dù OTP còn hiệu lực: ChatClient.tsx khởi tạo
// `otpVerified` bằng `useState(false)` KHÔNG PHỤ THUỘC phiên thật, nên MỌI lần
// mount (F5, mở tab mới) đều coi như chưa xác thực — kể cả khi `otp_verified_at`
// trong JWT còn cách hạn 12 tiếng.
//
// PHẢI khớp `OTP_VIEW_MAX_MINUTES` ở backend (src/config.py) — ĐÂY LÀ BẢN SAO
// CÓ Ý THỨC, cùng nếp `sessionCookieMaxAgeSeconds` ở session.ts đã dùng cho
// JWT_REFRESH_EXPIRE_DAYS_*. Backend GĐ2.5 đang ĐÓNG BĂNG nên không có đường
// nào đọc ngưỡng này từ một nguồn chung duy nhất — lệch giữa hai bên chỉ gây
// UI hiển thị sai TRONG VÀI GIÂY (rail mở/khoá nhầm), KHÔNG PHẢI lỗ bảo mật:
// mọi route đọc dữ liệu thật vẫn tự kiểm otp_verified_at ở server (INV-10),
// giá trị này CHỈ quyết định UI hiển thị gì, không quyết định ai đọc được gì.
const OTP_VIEW_MAX_MINUTES = 12 * 60;

function decodeJwtPayload(token: string): Record<string, unknown> | null {
  try {
    const segment = token.split(".")[1];
    if (!segment) return null;
    return JSON.parse(Buffer.from(segment, "base64url").toString("utf8"));
  } catch {
    // JWT hỏng/không đọc được -> coi như KHÔNG có otp_verified_at, không ném
    // lỗi làm hỏng cả trang chat vì một giá trị chỉ ảnh hưởng hiển thị.
    return null;
  }
}

// Trả boolean/mốc hết hạn, KHÔNG BAO GIỜ trả nguyên claim JWT ra ngoài hàm này
// — caller (page.tsx) chỉ được phép truyền tiếp giá trị ĐÃ DẪN XUẤT sang
// client, không truyền `access_token` hay object claim thô.
export function getOtpXemConHan(session: Session): boolean {
  const claims = decodeJwtPayload(session.access_token);
  const otpVerifiedAt = claims?.otp_verified_at;
  if (typeof otpVerifiedAt !== "number") return false;
  // `Date.now()` đúng vì backend VÀ frontend cùng chạy TZ=UTC trong Docker
  // ([ĐO] Lead 19/08). KHÔNG vô điều kiện: `otp-forge.ts` (11/08) đã ghi nhận
  // `utcnow().timestamp()` lệch múi giờ khi backend chạy TRỰC TIẾP trên host
  // (vd `make run`) — cửa sổ 12h sẽ co lại đúng bằng offset, IM LẶNG, không
  // lỗi nào bắn. Phép so này chỉ đúng khi cả hai phía cùng đứng trên UTC.
  const ageMinutes = (Date.now() / 1000 - otpVerifiedAt) / 60;
  return ageMinutes <= OTP_VIEW_MAX_MINUTES;
}
