import jwt from "jsonwebtoken";
import type { BrowserContext } from "@playwright/test";
import { SESSION_COOKIE, type Session } from "@/lib/session";

/**
 * AUTH-007/008 — kiểm ngưỡng "OTP còn tươi" (12h xem / 15 phút step-up,
 * src/auth.py::CurrentUser.otp_fresh_within) mà không chờ 12 giờ/15 phút
 * thật trôi qua. Backend ký JWT bằng HS256 (src/config.py:
 * JWT_ALGORITHM = "HS256", hardcode không qua env) với claim
 * {sub, role, otp_verified_at, iat, exp} (src/auth.py::create_access_token).
 *
 * `forgeOtpVerifiedAt` KHÔNG tự bịa lại payload — decode token THẬT vừa lấy
 * từ login/OTP-verify trong chính test (jwt.decode, không cần verify vì
 * token này do backend cấp thật, chỉ đọc lại claim), giữ nguyên
 * sub/role/iat/exp, CHỈ đổi otp_verified_at rồi ký lại bằng CÙNG secret —
 * đây là kỹ thuật time-travel cho test, không phải cách bypass auth (secret
 * dùng chung với backend trong cùng môi trường test, không phải secret production).
 *
 * `JWT_SECRET_KEY` PHẢI có trong env của tiến trình chạy `playwright test`
 * (playwright.config.ts không tự load .env) — CI đã set qua `env:` cấp
 * workflow trong ci.yml (dùng chung với backend). Chạy tay cục bộ: export
 * JWT_SECRET_KEY trước khi gọi `npx playwright test` (xem docs/TESTING.md).
 *
 * PHÁT HIỆN THẬT lúc verify (2026-08-11, KHÔNG sửa ở đây — ngoài phạm vi kế
 * hoạch hiện tại, chỉ né bằng cách viết test đúng): `secondsAgo` KHÔNG được
 * trừ từ đồng hồ máy chạy Playwright (`Date.now()`) — verify bằng
 * `python3 -c "print(dt.datetime.utcnow().timestamp() - time.time())"` trên
 * máy chạy backend ra đúng -25200s (-7h, khớp múi giờ UTC+7 máy dev). Lý do:
 * `src/auth.py::otp_fresh_within` và mọi nơi tính "now" khác trong
 * src/agents/graph.py, src/agents/tools/customer_tools.py đều dùng
 * `dt.datetime.utcnow().timestamp()` — gọi `.timestamp()` trên datetime NAIVE
 * đã là UTC khiến Python trừ NHẦM offset múi giờ local LẦN NỮA. Bug này VÔ
 * HẠI trong vận hành thật (verify lẫn check đều tự trừ lệch NHƯ NHAU trên
 * cùng 1 server, sai số tự triệt tiêu) — CHỈ lộ ra khi ngoại lai đưa 1 mốc
 * thời gian tính "đúng" (`Date.now()` của tiến trình Playwright, không lệch
 * múi giờ) vào so sánh với đồng hồ NỘI BỘ (lệch) của server. Né bằng cách
 * neo `secondsAgo` vào ĐÚNG mốc `otp_verified_at` THẬT mà server vừa tự cấp
 * (đọc lại từ token thật ở `session.access_token`, không phải đồng hồ máy
 * Playwright) — nằm gọn trong "khung giờ" của server, so sánh nội bộ vẫn tự
 * triệt tiêu sai số như vận hành thật.
 */
export function forgeOtpVerifiedAt(session: Session, secondsAgo: number | null): Session {
  const secret = process.env.JWT_SECRET_KEY;
  if (!secret) {
    throw new Error(
      "Thiếu JWT_SECRET_KEY trong env của tiến trình Playwright — " +
        "export JWT_SECRET_KEY=<cùng giá trị backend đang dùng> trước khi chạy test này."
    );
  }
  const decoded = jwt.decode(session.access_token) as {
    sub: string;
    role: string;
    iat: number;
    exp: number;
    otp_verified_at: number | null;
  };
  if (secondsAgo !== null && decoded.otp_verified_at == null) {
    throw new Error("forgeOtpVerifiedAt cần session đã qua OTP verify thật ít nhất 1 lần (thiếu otp_verified_at gốc để neo mốc).");
  }
  const otp_verified_at = secondsAgo === null ? null : decoded.otp_verified_at! - secondsAgo;
  // KHÔNG dùng option `noTimestamp: true` — tên gây hiểu lầm, hành vi thật
  // (verify bằng node -e trực tiếp) là XOÁ hẳn `iat` khỏi payload thay vì
  // giữ nguyên giá trị đã truyền vào, làm backend từ chối token với "Token
  // không hợp lệ" (src/auth.py::_decode kiểm `iat is None`). Không truyền
  // option này — jsonwebtoken tự dùng `payload.iat || now()`, giữ đúng `iat`
  // đã set sẵn trong payload vì nó truthy.
  const forgedToken = jwt.sign(
    { sub: decoded.sub, role: decoded.role, iat: decoded.iat, exp: decoded.exp, otp_verified_at },
    secret,
    { algorithm: "HS256" }
  );
  return { ...session, access_token: forgedToken };
}

/** Ghi đè cookie `fin05_session` trong browser context — khớp đúng cookie
 * options ở frontend/src/app/api/session/route.ts (httpOnly/sameSite=lax/
 * path=/) để hành vi giống hệt cookie thật do server set. Next.js
 * `cookies().set()` tự URL-encode giá trị (xác nhận thật qua debug — cookie
 * đọc lại từ context.cookies() luôn ở dạng `%7B%22user_id...`) — encode ở
 * đây để route handler phía server (đọc qua `cookies().get()`, tự decode)
 * parse lại đúng, khớp hành vi cookie thật do server set. */
/**
 * AUTH5-HARD-01 (đợt nâng cấp Auth Flow 2026-08-12) — kiểm proxy.ts tự làm
 * mới access_token giữa phiên (REFRESH_MARGIN_SECONDS=120) mà KHÔNG phải
 * chờ 15 phút thật trôi qua (JWT_ACCESS_EXPIRE_MINUTES). Cùng kỹ thuật
 * time-travel với forgeOtpVerifiedAt — decode token THẬT, CHỈ đổi `exp`, ký
 * lại bằng cùng secret. `refresh_token` KHÔNG đổi (vẫn là refresh_token THẬT
 * do backend cấp, còn hiệu lực trong Redis) — điểm mấu chốt: access_token
 * "hết hạn" nhưng refresh_token vẫn sống, đúng kịch bản proxy.ts cần xử lý
 * (khác forgeOtpVerifiedAt vốn không đổi exp).
 */
export function forgeAccessTokenExpiry(session: Session, expiresInSeconds: number): Session {
  const secret = process.env.JWT_SECRET_KEY;
  if (!secret) {
    throw new Error(
      "Thiếu JWT_SECRET_KEY trong env của tiến trình Playwright — " +
        "export JWT_SECRET_KEY=<cùng giá trị backend đang dùng> trước khi chạy test này."
    );
  }
  const decoded = jwt.decode(session.access_token) as {
    sub: string;
    role: string;
    iat: number;
    otp_verified_at: number | null;
  };
  const nowSeconds = Math.floor(Date.now() / 1000);
  const forgedToken = jwt.sign(
    {
      sub: decoded.sub,
      role: decoded.role,
      iat: decoded.iat,
      otp_verified_at: decoded.otp_verified_at,
      exp: nowSeconds + expiresInSeconds,
    },
    secret,
    { algorithm: "HS256" }
  );
  return { ...session, access_token: forgedToken };
}

export async function setForgedSessionCookie(context: BrowserContext, session: Session): Promise<void> {
  await context.addCookies([
    {
      name: SESSION_COOKIE,
      value: encodeURIComponent(JSON.stringify(session)),
      url: "http://localhost:3000",
      httpOnly: true,
      sameSite: "Lax",
    },
  ]);
}
