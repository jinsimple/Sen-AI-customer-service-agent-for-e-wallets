import { NextResponse } from "next/server";

/**
 * Định danh môi trường (2026-08-13) — trả về stack này đang nói chuyện với
 * BACKEND nào và DATABASE nào.
 *
 * Sinh ra sau sự cố thật: Docker stack (Caddy :80 → Postgres) và stack dev cục
 * bộ (next dev :3000 → uvicorn :8010 → SQLite) chạy song song. Hai cửa sổ trình
 * duyệt GIỐNG HỆT NHAU nhưng khác database — khách tạo ticket vào Postgres,
 * CSKH đọc từ SQLite nên vĩnh viễn thấy 0. Xem ADR-009.
 *
 * KHÔNG cần đăng nhập: chỉ trả scheme + tên DB (không có host/user/mật khẩu),
 * và phải xem được ngay ở màn hình /login — đúng lúc người dùng cần biết mình
 * đang đăng nhập vào đâu.
 */
export async function GET() {
  const backendUrl = process.env.BACKEND_URL ?? "http://localhost:8010";
  try {
    const res = await fetch(`${backendUrl}/health`, {
      cache: "no-store",
      signal: AbortSignal.timeout(3000),
    });
    if (!res.ok) throw new Error(`backend trả ${res.status}`);
    const data = (await res.json()) as { env?: string; db_kind?: string; db_name?: string };
    return NextResponse.json({
      env: data.env ?? "unknown",
      db_kind: data.db_kind ?? "unknown",
      db_name: data.db_name ?? "unknown",
      backend: backendUrl,
    });
  } catch {
    // Không ném lỗi ra UI — nhãn môi trường là thông tin phụ trợ, hỏng nó
    // KHÔNG được làm hỏng trang. Trả trạng thái "không rõ" để badge hiện
    // cảnh báo thay vì biến mất im lặng (biến mất = quay lại đúng vấn đề
    // môi trường vô hình mà cơ chế này sinh ra để chặn).
    return NextResponse.json({
      env: "unreachable",
      db_kind: "unknown",
      db_name: "unknown",
      backend: backendUrl,
    });
  }
}
