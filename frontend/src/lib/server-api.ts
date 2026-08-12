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

// 65s — hơi rộng hơn timeout phía trình duyệt (60s, xem lib/api.ts) để dưới
// điều kiện bình thường lỗi timeout thật luôn tới từ phía trình duyệt trước
// (thông báo có ý nghĩa hơn cho khách), timeout ở đây chỉ là lưới an toàn
// tài nguyên phía server (không giữ connection/handler treo vô hạn nếu
// backend thật sự đơ) — UX-01 (FIN05-QA-Test-Report.md), cùng gốc BUG-01.
const BACKEND_FETCH_TIMEOUT_MS = 65_000;

export async function backendFetch<T>(
  path: string,
  token: string,
  init?: RequestInit
): Promise<T> {
  // FormData (upload file, xem app/api/policy-docs/route.ts) — KHÔNG tự set
  // Content-Type: application/json ở đây, để fetch/undici tự tính boundary
  // multipart đúng. Ép JSON lên body FormData sẽ làm FastAPI không parse được.
  const isFormData = init?.body instanceof FormData;
  const controller = new AbortController();
  const timeoutId = setTimeout(() => controller.abort(), BACKEND_FETCH_TIMEOUT_MS);
  let res: Response;
  try {
    res = await fetch(`${BACKEND_URL}${path}`, {
      ...init,
      // Proxy cho dữ liệu tài chính/phiên đăng nhập theo user — không bao giờ
      // được cache. Next.js (kể cả Route Handler, kể cả method GET) mặc định
      // vẫn cache fetch qua "HMR cache" lúc `next dev` DÙ ĐÃ set no-store ở
      // mức route (xem node_modules/next/dist/docs/.../fetch.md mục
      // Troubleshooting) — phát hiện thật: sau khi supervisor duyệt xong
      // (POST thành công, backend đã đổi status), GET /api/resolutions ngay
      // sau đó vẫn trả bản ghi cũ, card không biến mất khỏi hàng chờ dù
      // backend đã đúng. Set no-store tường minh ở đây (điểm gọi fetch duy
      // nhất tới backend thật) để không phụ thuộc cấu hình mặc định.
      cache: "no-store",
      headers: {
        ...(isFormData ? {} : { "Content-Type": "application/json" }),
        Authorization: `Bearer ${token}`,
        ...(init?.headers ?? {}),
      },
      signal: controller.signal,
    });
  } catch (err) {
    if (err instanceof DOMException && err.name === "AbortError") {
      throw new ServerApiError(504, "Backend phản hồi quá lâu — thử lại giúp mình nhé.");
    }
    throw err;
  } finally {
    clearTimeout(timeoutId);
  }
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
