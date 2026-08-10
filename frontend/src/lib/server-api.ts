import "server-only";
import { NextResponse } from "next/server";

/**
 * Lớp gọi FastAPI THẬT — chỉ được import từ Route Handler (`app/api/**\/route.ts`),
 * không bao giờ từ Client Component. Đây là điểm mấu chốt của kiến trúc BFF
 * (Backend for Frontend): trình duyệt không bao giờ gọi thẳng FastAPI hay
 * biết địa chỉ/token của nó — mọi request đi qua route handler server-side
 * của Next.js, nơi đọc token từ cookie httpOnly rồi gắn `Authorization:
 * Bearer` khi gọi backend thật.
 *
 * `BACKEND_URL` cố ý KHÔNG có tiền tố `NEXT_PUBLIC_` — biến không tiền tố
 * đó không được Next.js đóng gói vào bundle gửi cho trình duyệt, nghĩa là
 * JS chạy trên máy khách không thể biết địa chỉ backend thật, thu hẹp bề
 * mặt tấn công so với khi phải để `NEXT_PUBLIC_API_BASE` lộ ra trước đây.
 */
export const BACKEND_URL = process.env.BACKEND_URL ?? "http://localhost:8010";

export class ServerApiError extends Error {
  status: number;
  constructor(status: number, message: string) {
    super(message);
    this.status = status;
  }
}

export async function backendFetch<T>(
  path: string,
  token: string,
  init?: RequestInit
): Promise<T> {
  // FormData (upload file, xem app/api/policy-docs/route.ts) — KHÔNG tự set
  // Content-Type: application/json ở đây, để fetch/undici tự tính boundary
  // multipart đúng. Ép JSON lên body FormData sẽ làm FastAPI không parse được.
  const isFormData = init?.body instanceof FormData;
  const res = await fetch(`${BACKEND_URL}${path}`, {
    ...init,
    headers: {
      ...(isFormData ? {} : { "Content-Type": "application/json" }),
      Authorization: `Bearer ${token}`,
      ...(init?.headers ?? {}),
    },
  });
  if (!res.ok) {
    let detail = res.statusText;
    try {
      const body = await res.json();
      // FastAPI (HTTPException) trả {"detail": "..."}, nhưng slowapi (rate
      // limit 429, xem src/api/main.py) trả {"error": "..."} — thiếu nhánh
      // này khiến lỗi rơi xuống JSON.stringify(body) và hiện nguyên văn JSON
      // thô cho khách (phát hiện thật: bấm "Xác nhận" OTP liên tục chạm rate
      // limit, màn hình hiện {"error":"Rate limit exceeded: ..."} thay vì lời
      // Việt dễ hiểu).
      detail = body.detail ?? body.error ?? JSON.stringify(body);
    } catch {
      // giữ statusText nếu body không phải JSON
    }
    throw new ServerApiError(res.status, detail);
  }
  if (res.status === 204) return undefined as T;
  return res.json() as Promise<T>;
}

/** Dùng trong catch block của mọi route handler proxy — chuyển lỗi backend
 * (401/403/400/404...) thành đúng response tương ứng cho client, thay vì
 * để lộ traceback 500 chung chung. */
export function proxyErrorResponse(e: unknown): NextResponse {
  if (e instanceof ServerApiError) {
    return NextResponse.json({ detail: e.message }, { status: e.status });
  }
  throw e;
}

/** Hàm, không phải hằng số — mỗi lần gọi phải tạo Response mới. Response chỉ
 * đọc/gửi được 1 lần; nếu dùng chung 1 instance cho nhiều request đồng thời
 * sẽ lỗi khó dò. */
export function unauthorized(): NextResponse {
  return NextResponse.json({ detail: "Chưa đăng nhập" }, { status: 401 });
}
