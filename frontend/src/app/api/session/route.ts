import { NextResponse } from "next/server";
import { cookies } from "next/headers";
import {
  LAST_GATE_COOKIE,
  SESSION_COOKIE,
  sessionCookieMaxAgeSeconds,
  type Gate,
  type Session,
} from "@/lib/session";
import { BACKEND_URL } from "@/lib/server-api";

// Gọi backend server-side (không CORS) rồi set cookie httpOnly — theo đúng
// khuyến nghị Next.js: "Cookies should be set on the server to prevent
// client-side tampering" (docs/01-app/02-guides/authentication.md). Token
// JWT backend phát ra cũng chỉ nằm trong cookie httpOnly này — trình duyệt
// không bao giờ đọc được, chỉ route handler server-side dùng lại (BFF).
// 26/08 — PO chốt: chặn nhân viên đăng nhập ở /login (cổng khách) và ngược
// lại. KHÔNG phải cổng bảo mật — vai vẫn 100% lấy từ RESPONSE backend, `gate`
// chỉ có thể làm ĐĂNG NHẬP THẤT BẠI THÊM, không bao giờ giúp thành công thêm
// (ai gửi sai `gate` chỉ tự làm mình bị từ chối, không đi vòng qua được gì).
// Chặn SAU khi xác thực mật khẩu đúng — sai mật khẩu không học được gì; đúng
// mật khẩu thì thêm một câu cũng không mất gì (PO). Cùng MỘT câu lỗi cho mọi
// lý do bị từ chối ở bước này — không khai vai ra màn hình.
const WRONG_GATE_MESSAGE = "Tài khoản này không đăng nhập tại đây. Vui lòng dùng cổng dành cho nhân viên.";

function gateRejects(gate: Gate, role: string) {
  if (gate === "customer") return role !== "customer";
  return role === "customer";
}

export async function POST(req: Request) {
  const { phone, password, gate } = (await req.json()) as { phone: string; password: string; gate: Gate };
  const res = await fetch(`${BACKEND_URL}/auth/login`, {
    method: "POST",
    headers: { "Content-Type": "application/json" },
    body: JSON.stringify({ phone, password }),
  });

  if (!res.ok) {
    const body = await res.json().catch(() => ({ detail: "Đăng nhập thất bại" }));
    return NextResponse.json({ detail: body.detail }, { status: res.status });
  }

  const user = (await res.json()) as {
    user_id: string;
    role: string;
    full_name: string;
    access_token: string;
    refresh_token: string;
  };

  // Mật khẩu đã đúng (backend vừa xác nhận) — nhưng sai cổng. KHÔNG lập
  // phiên (không set cookie, tokens backend vừa phát ra chết theo request
  // này). Trả 403 chung chung, không nói vai thật là gì.
  if (gateRejects(gate, user.role)) {
    return NextResponse.json({ detail: WRONG_GATE_MESSAGE }, { status: 403 });
  }

  const session: Session = { ...user, phone, role: user.role as Session["role"] };

  const store = await cookies();
  store.set(SESSION_COOKIE, JSON.stringify(session), {
    httpOnly: true,
    sameSite: "lax",
    path: "/",
    // AUTH5-02/02B — cookie sống theo TTL refresh_token (7 ngày khách hàng,
    // 1 ngày role nội bộ), KHÔNG còn khớp trực tiếp JWT_ACCESS_EXPIRE_MINUTES
    // (chỉ 15 phút) — middleware.ts tự làm mới access_token bên trong cookie
    // này trước khi hết hạn, khách không bị đăng xuất sau 15 phút.
    maxAge: sessionCookieMaxAgeSeconds(session.role),
  });

  // Cookie gợi ý cổng — xem chú thích tại khai báo LAST_GATE_COOKIE
  // (lib/session.ts) để biết vì sao KHÔNG httpOnly và KHÔNG xoá khi đăng
  // xuất. `gate` ở đây chính là tham số client đã gửi (đã qua gateRejects()
  // ở trên — tới được dòng này nghĩa là gate khớp role thật).
  //
  // 🔴 [ĐO 27/08] Review + p-226-f0: TTL ban đầu ghim CỐ ĐỊNH 30 ngày —
  // không bám vào vòng đời thật nào (refresh_token nhân viên chỉ 1 ngày,
  // khách 7 ngày). Sau 1 ngày, nhân viên BẮT BUỘC đăng nhập lại dù cookie
  // gợi ý còn hay không — nó chỉ CHỌN CỔNG, không thay được đăng nhập, nên
  // 29 ngày còn lại của hằng số cũ không phục vụ ca dùng hợp lệ nào, chỉ để
  // lại dấu vết thừa trên máy trạm. Dùng LẠI sessionCookieMaxAgeSeconds(role)
  // — đã tồn tại, đã đúng theo vai — để mai đổi vòng đời phiên thì cookie
  // gợi ý tự đi theo, không phải nhớ đồng bộ một hằng số riêng.
  const gateThat: Gate = gate === "internal" ? "internal" : "customer";
  store.set(LAST_GATE_COOKIE, gateThat, {
    httpOnly: false,
    sameSite: "lax",
    path: "/",
    maxAge: sessionCookieMaxAgeSeconds(session.role),
  });

  // Trả về client KHÔNG kèm access_token/refresh_token — client chỉ cần
  // biết đăng nhập xong và role gì để điều hướng, token ở lại phía server.
  const { access_token: _accessToken, refresh_token: _refreshToken, ...publicSession } = session;
  return NextResponse.json(publicSession);
}

export async function DELETE() {
  const store = await cookies();
  const raw = store.get(SESSION_COOKIE)?.value;
  const session = raw ? (() => {
    try {
      return JSON.parse(raw) as Session;
    } catch {
      return null;
    }
  })() : null;

  // AUTH5-06 (đợt nâng cấp Auth Flow 2026-08-12) — đăng xuất giờ THẬT SỰ thu
  // hồi JWT ở backend (POST /auth/logout), không còn CHỈ xoá cookie phía
  // frontend như trước (đúng phát hiện đã ghi trong
  // tests/test_security/test_jwt_revocation.py). Best-effort — lỗi mạng lúc
  // gọi backend không được chặn việc xoá cookie phía trình duyệt.
  if (session?.access_token && session?.refresh_token) {
    try {
      await fetch(`${BACKEND_URL}/auth/logout`, {
        method: "POST",
        headers: { "Content-Type": "application/json", Authorization: `Bearer ${session.access_token}` },
        body: JSON.stringify({ refresh_token: session.refresh_token }),
        cache: "no-store",
      });
    } catch {
      // best-effort — vẫn xoá cookie phía dưới dù backend không gọi được
    }
  }

  store.delete(SESSION_COOKIE);
  return NextResponse.json({ ok: true });
}
