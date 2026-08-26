import { NextRequest, NextResponse } from "next/server";
import { parseSessionCookie, roleHome, sessionCookieMaxAgeSeconds, SESSION_COOKIE, type Role, type Session } from "@/lib/session";

// US-001 AC: "khách hàng không vào được dashboard CSKH kể cả sửa URL trực
// tiếp" — chặn ở proxy (Next.js 16 đổi tên từ middleware, chức năng như cũ),
// không chỉ ẩn UI. Đây là optimistic check (chỉ đọc cookie, không gọi DB) —
// đủ cho demo vì không có dữ liệu nhạy cảm nào trả trực tiếp từ proxy.
const ROLE_PREFIXES: Record<Role, string[]> = {
  customer: ["/chat"],
  // /report: contract cho phép (GET /reports/summary roles [cskh, supervisor])
  // nhưng frontend đang chặt hơn — CSKH bị đá về /dashboard. Đây là LẦN THỨ HAI
  // cùng lớp lỗi "guard frontend hẹp hơn contract" (lần một: sếp + /policy-lookup,
  // d0baf35). Tester đang viết test quét cả ma trận role×route để lần ba bị máy bắt.
  cskh: ["/dashboard", "/tickets", "/policy-lookup", "/report"],
  // /policy-lookup: sếp cũng cần tra chính sách khi quyết định duyệt. Thiếu
  // tiền tố này thì proxy đá thẳng về roleHome() = /approve, nên bấm vào tab
  // trông như tab hỏng (QA đo được 14/08). Backend đã cho phép sẵn —
  // authority-matrix: POST /policy-search roles [cskh, supervisor].
  // /dashboard: sếp xem được hàng chờ CSKH theo contract hiện hành
  // (GET /tickets: cskh, supervisor). Đây là ca thứ BA cùng lớp lỗi
  // "guard frontend hẹp hơn contract" — bộ quét ma trận role×route của
  // tester là thứ chặn ca thứ tư.
  supervisor: ["/approve", "/report", "/tickets", "/policy-lookup", "/dashboard"],
  partner_admin: ["/knowledge"],
};

// 26/08 — thêm 2 route công khai (duyệt bởi p-226-f0 sau khi tự đọc dòng
// 103-115, không qua lời kể). CHỈ thêm tiền tố CỤ THỂ vào mảng có sẵn —
// KHÔNG thêm "/" vào đây, vì matcher dưới là `startsWith` chứ không phải
// khớp chính xác; "/" sẽ khớp MỌI path và mở toang /dashboard, /approve...
// /gioi-thieu là landing TẠM — landing thật sẽ dọn về `/` theo thiết kế
// riêng của Lead (nhánh `pathname === "/"` ở dưới, giữ khớp CHÍNH XÁC).
// Hệ quả chấp nhận được: người ĐÃ đăng nhập lỡ mở /gioi-thieu hoặc
// /dang-nhap-noi-bo cũng bị đá về roleHome(role) — giống hệt cách /login xử
// lý hiện tại (dòng 104-106). Với /gioi-thieu điều này sẽ hết khi landing
// dọn về `/`; thêm nhánh riêng cho một route sắp biến mất là nợ, không phải
// tính năng.
const PUBLIC_PATHS = ["/login", "/dang-nhap-noi-bo", "/gioi-thieu"];

function homeFor(role: Role | undefined) {
  return role ? roleHome(role) : "/login";
}

// AUTH5-02 (đợt nâng cấp Auth Flow, 2026-08-12) — access_token giờ chỉ sống
// 15 phút (JWT_ACCESS_EXPIRE_MINUTES, src/config.py). Nếu không có gì chủ
// động làm mới, MỌI request sau 15 phút sẽ 401 và người dùng bị đăng xuất
// giữa chừng — không chấp nhận được cho 1 phiên demo/UAT thật. `proxy.ts` là
// file DUY NHẤT được phép theo quy ước Next.js 16 (không thể thêm
// middleware.ts riêng) nên logic làm mới token GỘP CHUNG vào đây, chạy
// TRƯỚC logic redirect theo role — áp dụng cho CẢ page lẫn route /api/* (BFF
// đọc access_token từ cookie), không loại trừ /api như nhánh redirect bên
// dưới. Docs Next.js cảnh báo proxy "không dùng cho slow data fetching/
// session management đầy đủ" — ở đây CHỈ gọi fetch khi token gần hết hạn
// (không phải mọi request), chấp nhận đánh đổi vì kiến trúc BFF của dự án
// không có chỗ nào khác chạy được trước ~30 route handler mà không sửa lại
// từng route.
const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8010";
const REFRESH_MARGIN_SECONDS = 120;

export async function proxy(req: NextRequest) {
  const { pathname } = req.nextUrl;
  if (pathname.startsWith("/_next") || pathname.startsWith("/favicon")) {
    return NextResponse.next();
  }

  // GIA HẠN PHIÊN ĐÃ CHUYỂN KHỎI ĐÂY -> `lib/server-api.ts::backendFetch`.
  //
  // Vì sao gỡ chứ không sửa: proxy VẪN gọi được `/auth/refresh` (đo được ở
  // backend, tầng-0 xác nhận rotate thành công) nhưng cookie nó đặt bằng
  // `NextResponse.cookies.set()` KHÔNG BAO GIỜ rời server — 0 header
  // `set-cookie` trên CẢ đường trang lẫn `/api`, trong khi ca đối chứng
  // `/api/session` (dùng `cookies()` của next/headers) cho đúng 1 header.
  //
  // Hậu quả khi còn để ở đây: token được xoay ở server, browser không biết,
  // request kế cầm lại refresh token CŨ ĐÃ ROTATE -> AUTH5-03 -> thu hồi cả
  // family -> chết phiên. Một cơ chế "gia hạn" mà mỗi lần chạy lại giết phiên.
  //
  // Đã loại trừ: hồi quy UI-01 · sai vị trí file · sai tên export · sai mẫu
  // code (cả ba khớp docs Next 16.3.0 từng điểm) · dependency drift (ba image
  // cùng Node v20.20.2 + Next 16.3.0 + manifest rỗng). Không phải lỗi cấu
  // hình sửa được — nên chuyển sang đường ĐÃ CHỨNG MINH EGRESS ĐƯỢC.
  const session = parseSessionCookie(req.cookies.get(SESSION_COOKIE)?.value);

  // Header request ĐÃ VÁ — để route handler chạy TRONG CHÍNH request này đọc
  // được access_token mới, chứ không phải chỉ browser nhận nó ở lượt sau.
  //
  // ĐÂY LÀ BUG, KHÔNG PHẢI TỐI ƯU. Bản trước ghi comment "Vẫn phải áp dụng
  // withRefreshedCookie() để route handler thấy access_token ĐÃ được làm mới"
  // — phát biểu đúng CÁI Ý ĐỊNH mà code không đạt được: `res.cookies.set()`
  // đặt cookie lên RESPONSE (đường về browser), còn route handler đọc cookie
  // từ REQUEST, nơi vẫn là token cũ. Người review đọc comment sẽ gật đầu.
  //
  // Hậu quả đo được: sau khi token hết hạn, request ĐẦU TIÊN vẫn 401 dù
  // refresh đã thành công ngay trong request đó; request thứ hai mới 200.
  // Nhẹ khi người dùng bấm lại — CHẾT khi tầng UI chỉ thử đúng một lần
  // (`liveChatConnectStartedRef`, ca demo của PO).

  // /api/* — route handler BFF tự đọc cookie + tự trả unauthorized(), không
  // cần logic redirect theo role ở đây (đó là cho page).
  //
  // HAI vế, thiếu vế nào cũng hỏng một nửa:
  //   `NextResponse.next()` -> route handler TRONG request
  //       này thấy token mới  (vế trước đây THIẾU)
  //   `withRefreshedCookie(...)`                 -> browser nhận token mới cho
  //       các request SAU
  if (pathname.startsWith("/api")) {
    return NextResponse.next();
  }

  if (pathname === "/") {
    return NextResponse.redirect(new URL(homeFor(session?.role), req.url));
  }

  const isPublic = PUBLIC_PATHS.some((p) => pathname.startsWith(p));
  if (isPublic) {
    if (session) return NextResponse.redirect(new URL(roleHome(session.role), req.url));
    return NextResponse.next();
  }

  if (!session) {
    return NextResponse.redirect(new URL("/login", req.url));
  }

  const allowedForRole = ROLE_PREFIXES[session.role];
  const isAllowed = allowedForRole.some((p) => pathname.startsWith(p));
  if (!isAllowed) {
    return NextResponse.redirect(new URL(roleHome(session.role), req.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
