import { NextRequest, NextResponse } from "next/server";
import {
  LAST_GATE_COOKIE,
  loginPathForGate,
  parseSessionCookie,
  roleHome,
  sessionCookieMaxAgeSeconds,
  SESSION_COOKIE,
  type Role,
  type Session,
} from "@/lib/session";

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
  // /policy-doc: deep-link "Xem toàn văn" từ /policy-lookup (ADR-065, 05/09)
  // — mở qua link, KHÔNG có tab nav riêng, cùng khuôn /tickets/{id}. CA THỨ
  // SÁU cùng lớp lỗi "route mới quên khai ở đây" nếu bỏ sót (5 lần trước:
  // /policy-lookup, /dashboard, /report, /cskh-online, /quan-ly-ticket) —
  // khai NGAY lúc thêm route, không đợi ai bấm hỏng mới phát hiện.
  cskh: ["/dashboard", "/tickets", "/policy-lookup", "/policy-doc", "/report"],
  // /policy-lookup: sếp cũng cần tra chính sách khi quyết định duyệt. Thiếu
  // tiền tố này thì proxy đá thẳng về roleHome() = /approve, nên bấm vào tab
  // trông như tab hỏng (QA đo được 14/08). Backend đã cho phép sẵn —
  // authority-matrix: POST /policy-search roles [cskh, supervisor].
  // /dashboard: sếp xem được hàng chờ CSKH theo contract hiện hành
  // (GET /tickets: cskh, supervisor). Đây là ca thứ BA cùng lớp lỗi
  // "guard frontend hẹp hơn contract" — bộ quét ma trận role×route của
  // tester là thứ chặn ca thứ tư.
  // /cskh-online: tab mới tách khỏi /approve (04/09) — thiếu tiền tố này ở
  // đây là CA THỨ TƯ cùng lớp lỗi "route mới không có mặt trong allowlist
  // riêng của proxy" (khác nhánh contract-backend, đã xảy ra 3 lần trước:
  // /policy-lookup, /dashboard, /report). Route không gọi API nào ngoài
  // /presence/staff (đã cho phép supervisor sẵn trong authority-matrix).
  // /quan-ly-ticket (ADR-064 b): tab MỚI tách từ /approve theo cùng khuôn
  // /cskh-online — CA THỨ NĂM nhắc lại đúng lớp lỗi "route mới quên khai ở
  // đây" nếu bỏ sót (4 lần trước: /policy-lookup, /dashboard, /report,
  // /cskh-online). Route không mở API mới — /quan-ly-ticket chỉ gọi lại
  // GET /tickets đã cho phép supervisor sẵn trong authority-matrix.
  supervisor: [
    "/approve", "/cskh-online", "/quan-ly-ticket", "/report", "/tickets",
    "/policy-lookup", "/policy-doc", "/dashboard",
  ],
  partner_admin: ["/knowledge"],
};

// 26/08 — landing đã dọn từ /gioi-thieu VỀ "/" (thiết kế Lead, soát bởi
// Review). "/" KHÔNG nằm trong mảng này — nó có nhánh khớp CHÍNH XÁC riêng
// ở dưới (`pathname === "/"`), CỐ Ý tách khỏi PUBLIC_PATHS vì matcher ở đây
// là `khopTienTo` (tiền tố + ranh giới "/"), và "/" + ranh giới sẽ khớp MỌI
// path — gộp vào đây là mở toang /dashboard, /approve... /dang-nhap-noi-bo
// vẫn ở đây: route công khai thật (trang đăng nhập nội bộ), không phải
// landing.
const PUBLIC_PATHS = ["/login", "/dang-nhap-noi-bo"];

// Review (p-226-8b, 26/08): `startsWith` thô khớp theo TIỀN TỐ KÝ TỰ, không
// theo ranh giới segment — "/dashboard".startsWith cũng đúng với
// "/dashboard-admin". Hai chỗ dùng nó (PUBLIC_PATHS bên dưới VÀ
// ROLE_PREFIXES) đều dính cùng lỗi hình dạng: ai đặt tên route mới trùng
// tiền tố một route đã cho phép là vô tình mở/leo thang quyền, không cần sửa
// gì khác. Một hàm khớp có ranh giới (chính xác HOẶC tiền tố + "/") đóng cả
// hai chỗ cùng lúc, không phải nhớ mà tránh.
function khopTienTo(pathname: string, prefix: string) {
  return pathname === prefix || pathname.startsWith(prefix + "/");
}

// 27/08 — Marketing dựng /cho-khach-hang: trang "chống lừa đảo" (kiểm chứng
// "Sen có bao giờ hỏi mã OTP không?"). Đây là NHÓM THỨ BA, khác bản chất với
// PUBLIC_PATHS — PUBLIC_PATHS đá người ĐÃ đăng nhập về roleHome (đúng cho
// /login), còn trang này phải đọc được ngay cả khi khách ĐANG đăng nhập và
// đang hoảng, không được redirect theo BẤT KỲ chiều nào. Không nhét vào
// PUBLIC_PATHS như một ngoại lệ — hành vi khác bản chất thì phải là nhóm
// khác, không phải một cờ rẽ nhánh trong nhóm cũ.
const ALWAYS_PUBLIC_PATHS = ["/cho-khach-hang"];

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

// 27/08 [ĐO] p-226-dc: thêm ảnh thật vào landing (`/landing/*.png`) rồi phát
// hiện file đó (VÀ mọi file có sẵn từ trước trong `public/` — đo được cả
// `/next.svg`, `/file.svg` mặc định của Next) bị đá về /login cho khách
// CHƯA đăng nhập — matcher chỉ loại trừ `_next/*`/`favicon`, không loại trừ
// phần còn lại của `public/`. Lỗi CÓ SẴN TỪ TRƯỚC, không phải do ảnh mới gây
// ra — ảnh mới chỉ là request đầu tiên chạm đúng lớp lỗi này.
//
// 🔴 [ĐO 27/08] Review (p-226-8b): bản vá ĐẦU dùng regex theo ĐUÔI FILE —
// SAI, vì nó test trên pathname mà không phân biệt "file tĩnh thật trong
// public/" với "route App Router có segment ĐỘNG mà giá trị tham số tình cờ
// khớp đuôi". Cụ thể: `/tickets/[id]` (chỉ cskh/supervisor được vào theo
// ROLE_PREFIXES) — khách gọi `/tickets/x.json` sẽ khớp regex đuôi `.json` ở
// NGAY DÒNG ĐẦU, bỏ qua hẳn khối kiểm vai bên dưới, RENDER được vỏ trang
// (dữ liệu thật vẫn an toàn vì backend tự kiểm role riêng — nhưng đây vẫn
// trái nguyên văn US-001 AC ở đầu file: chặn ở proxy, không chỉ ẩn UI).
// Đuôi file KHÔNG PHẢI bất biến an toàn khi hệ có route động — ALLOWLIST
// THEO ĐƯỜNG DẪN THẬT thì có, vì nó không suy luận từ HÌNH DẠNG chuỗi (có
// dấu chấm hay không) mà từ DANH SÁCH asset thật đang tồn tại. Đổi lại dùng
// `khopTienTo` (đã có sẵn, cùng cơ chế PUBLIC_PATHS/ALWAYS_PUBLIC_PATHS bên
// dưới) trên đúng các thư mục asset tĩnh thật — `public/` ở dự án này gần
// như không đổi, chi phí nhớ thêm 1 dòng khi thêm thư mục asset mới THẤP
// HƠN HẲN rủi ro một regex đuôi file mở lại khe US-001.
const STATIC_ASSET_PATHS = ["/landing", "/file.svg", "/vercel.svg", "/next.svg", "/globe.svg", "/window.svg"];

export async function proxy(req: NextRequest) {
  const { pathname } = req.nextUrl;
  if (
    pathname.startsWith("/_next") ||
    pathname.startsWith("/favicon") ||
    STATIC_ASSET_PATHS.some((p) => khopTienTo(pathname, p))
  ) {
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

  if (ALWAYS_PUBLIC_PATHS.some((p) => khopTienTo(pathname, p))) {
    return NextResponse.next();
  }

  // Nhánh khớp CHÍNH XÁC, CỐ Ý tách khỏi PUBLIC_PATHS (xem comment ở khai
  // báo mảng đó) — "/" giờ là landing công khai, không phải logic xác thực
  // thuần tuý nữa. Có phiên -> vẫn về màn theo vai, KHÔNG ĐỔI GÌ so với
  // trước (0 thay đổi bề mặt auth cho người đã đăng nhập). Không phiên ->
  // ĐỔI: cho render (trang quảng cáo tại app/page.tsx), không còn redirect
  // "/login" nữa.
  if (pathname === "/") {
    if (session) return NextResponse.redirect(new URL(roleHome(session.role), req.url));
    return NextResponse.next();
  }

  const isPublic = PUBLIC_PATHS.some((p) => khopTienTo(pathname, p));
  if (isPublic) {
    if (session) return NextResponse.redirect(new URL(roleHome(session.role), req.url));
    return NextResponse.next();
  }

  if (!session) {
    // 27/08 — PO báo: nhân viên hết phiên luôn bị đá về /login (cổng khách),
    // NGÕ CỤT vì gate ở đó từ chối vai nội bộ. Không có `session` ở đây nghĩa
    // là không còn vai nào để tra (cookie phiên đã mất/hỏng) — dùng cookie
    // gợi ý cổng (LAST_GATE_COOKIE, ghi lúc đăng nhập, sống dài hơn session
    // thật) làm dự phòng thay vì mặc định luôn /login. Xem lib/session.ts.
    const goiY = req.cookies.get(LAST_GATE_COOKIE)?.value;
    return NextResponse.redirect(new URL(loginPathForGate(goiY), req.url));
  }

  const allowedForRole = ROLE_PREFIXES[session.role];
  const isAllowed = allowedForRole.some((p) => khopTienTo(pathname, p));
  if (!isAllowed) {
    return NextResponse.redirect(new URL(roleHome(session.role), req.url));
  }

  return NextResponse.next();
}

export const config = {
  matcher: ["/((?!_next/static|_next/image|favicon.ico).*)"],
};
