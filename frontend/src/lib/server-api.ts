import "server-only";
import { cookies } from "next/headers";
import { NextResponse } from "next/server";
import { parseSessionCookie, SESSION_COOKIE, sessionCookieMaxAgeSeconds, type Session } from "@/lib/session";

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

// ---------------------------------------------------------------------------
// GIA HẠN PHIÊN — ĐẶT Ở ĐÂY, KHÔNG Ở `proxy.ts`
//
// `proxy.ts` VẪN gọi được `/auth/refresh` (đo được ở backend) nhưng cookie nó
// đặt bằng `NextResponse.cookies.set()` KHÔNG BAO GIỜ rời server — đo thật,
// 0 header `set-cookie` trên CẢ đường trang lẫn `/api`, trong khi ca đối
// chứng `/api/session` (dùng `cookies()` của `next/headers`) cho đúng 1
// header. Cùng mã nguồn ở ba image, cùng Node v20.20.2 + Next 16.3.0, và code
// khớp từng điểm với tài liệu chính thức của bản Next đang cài — nên đây
// KHÔNG phải lỗi cấu hình sửa được, mà là vùng không có đáp án viết sẵn.
//
// Hậu quả của việc token mới không tới browser: request kế tiếp cầm lại
// refresh token CŨ ĐÃ ROTATE -> AUTH5-03 coi là bị đánh cắp -> `revoke_family`
// -> CHẾT CẢ PHIÊN, kể cả cặp token vừa cấp. Hệ tự bắn vào chân mình.
//
// Nên: dùng ĐƯỜNG ĐÃ CHỨNG MINH HOẠT ĐỘNG — `cookies()` của `next/headers`
// trong route handler. Và đặt ở `backendFetch()` vì đây là ĐIỂM CHẶN DUY NHẤT
// mọi call BFF đi qua: "dễ sót route" được hoá giải bằng CẤU TRÚC, không bằng
// sự cẩn thận của người sửa sau.
const _dangRefresh = new Map<string, Promise<Session | null>>();

/**
 * Single-flight theo refresh token.
 *
 * BẮT BUỘC, không phải tối ưu: refresh token là DÙNG-MỘT-LẦN và lượt thứ hai
 * dùng lại chính nó sẽ kích `revoke_family` (auth.py:146-155) — tức hai lời
 * gọi song song không chỉ lãng phí mà GIẾT PHIÊN. Một trang render gọi nhiều
 * `backendFetch` song song là chuyện bình thường, nên không có khoá thì ta
 * tái tạo đúng con bug vừa sửa, chỉ ở tầng mới.
 *
 * ⚠️ GIỚI HẠN ĐÃ BIẾT: Map ở phạm vi MODULE nên chỉ phủ trong MỘT tiến trình
 * Node. Nhiều replica frontend, hoặc nhiều tab trình duyệt (hai ngữ cảnh JS
 * không thấy nhau), vẫn có thể refresh song song. Muốn phủ trọn phải khoá
 * dùng chung (Redis). Ghi ra để lần scale sau không tưởng vấn đề đã đóng.
 */
async function _lamMoiPhien(cu: Session): Promise<Session | null> {
  const dangCo = _dangRefresh.get(cu.refresh_token);
  if (dangCo) return dangCo;

  const viec = (async (): Promise<Session | null> => {
    try {
      const res = await fetch(`${BACKEND_URL}/auth/refresh`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ refresh_token: cu.refresh_token }),
        cache: "no-store",
      });
      // 27/08 [ĐO] p-226-f0: khi refresh_token cũng đã hỏng (hết hạn/bị thu
      // hồi), hàm này trả null NHƯNG cookie phiên chết vẫn nằm nguyên trong
      // trình duyệt — proxy.ts chỉ kiểm HÌNH DẠNG cookie, không kiểm hiệu
      // lực, nên vẫn coi là "đã đăng nhập" và cho vào. Mọi lời gọi backend
      // sau đó lại 401 → lại thử refresh → lại hỏng, VÒNG LẶP không tự thoát
      // — chỉ bấm Đăng xuất (nơi DUY NHẤT khác gọi store.delete) mới ra
      // được. Xoá cookie NGAY tại đây để vòng lặp không có gì để lặp lại.
      //
      // 🔴 [ĐO 27/08] p-226-8b (Review): CHỈ xoá khi backend THẬT SỰ từ chối
      // refresh_token (401) — `!res.ok` rộng hơn ý định, còn bắt cả 429
      // (`/auth/refresh` có rate limit 30/phút, main.py — nhiều tab/request
      // BFF song song đều có thể trigger) và 5xx (exception chưa bắt trong
      // rotate_refresh_token khi Redis chập chờn thoáng qua). Cả hai đều là
      // "mạng/backend hỏng tạm thời", không phải "token bị từ chối" — xoá
      // cookie ở hai ca đó là HUỶ MỘT PHIÊN CÒN SỐNG, đúng loại hồi quy bản
      // vá này định tránh, chỉ khác hướng (trước: giữ cookie chết quá lâu;
      // giờ nếu không sửa: xoá cookie sống quá sớm).
      if (res.status === 401) {
        (await cookies()).delete(SESSION_COOKIE);
        return null;
      }
      if (!res.ok) {
        return null;
      }
      const moi = (await res.json()) as { access_token: string; refresh_token: string };
      const phien: Session = { ...cu, access_token: moi.access_token, refresh_token: moi.refresh_token };
      // ĐÂY là đường egress đã đo được — `cookies()` của next/headers, cùng
      // cách `/api/session` làm. KHÔNG dùng `NextResponse.cookies.set()`.
      const store = await cookies();
      store.set(SESSION_COOKIE, JSON.stringify(phien), {
        httpOnly: true,
        sameSite: "lax",
        path: "/",
        maxAge: sessionCookieMaxAgeSeconds(phien.role),
      });
      return phien;
    } catch {
      // Mạng/backend hỏng (KHÔNG PHẢI refresh_token bị từ chối — đó là
      // nhánh !res.ok phía trên) — không xoá cookie ở đây: session có thể
      // vẫn còn hợp lệ, chỉ là backend tạm không gọi được. Trả null để
      // caller ném đúng lỗi 401 gốc thay vì thử lại bằng một token không
      // chắc còn tồn tại.
      return null;
    } finally {
      _dangRefresh.delete(cu.refresh_token);
    }
  })();

  _dangRefresh.set(cu.refresh_token, viec);
  return viec;
}

type InitCoCo = RequestInit & { __daThuLai?: boolean };

export async function backendFetch<T>(
  path: string,
  token: string,
  init?: InitCoCo
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
      // Riêng lỗi 422 validation, FastAPI trả detail là MẢNG object
      // [{loc, msg, type}...] — đưa thẳng vào Error(message) sẽ bị ép chuỗi
      // thành "[object Object]" trên màn hình khách (QA-05, biên bản 13/08,
      // bắt được ở /api/otp/verify lẫn /api/resolutions/.../approve).
      if (Array.isArray(body.detail)) {
        detail = body.detail
          .map((d: { loc?: unknown[]; msg?: string }) => {
            const field = Array.isArray(d.loc) ? d.loc.slice(1).join(".") : "";
            return field ? `${field}: ${d.msg ?? "không hợp lệ"}` : d.msg ?? "không hợp lệ";
          })
          .join("; ");
        detail = `Dữ liệu gửi lên chưa hợp lệ — ${detail}`;
      } else {
        detail = body.detail ?? body.error ?? JSON.stringify(body);
      }
    } catch {
      // giữ statusText nếu body không phải JSON
    }
    // 401 -> thử gia hạn ĐÚNG MỘT LẦN rồi gọi lại. Chỉ 401 (token hết hạn),
    // KHÔNG áp cho 403 (sai vai — gia hạn không đổi được vai, thử lại là vô
    // nghĩa và làm loãng log).
    if (res.status === 401 && !init?.__daThuLai) {
      const cu = parseSessionCookie((await cookies()).get(SESSION_COOKIE)?.value);
      if (cu) {
        const moi = await _lamMoiPhien(cu);
        if (moi) {
          return backendFetch<T>(path, moi.access_token, { ...init, __daThuLai: true });
        }
      }
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
