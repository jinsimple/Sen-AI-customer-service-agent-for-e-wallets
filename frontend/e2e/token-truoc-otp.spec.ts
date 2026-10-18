import { test, expect, type BrowserContext } from "@playwright/test";
import { loginAs, completeOtpIfPrompted } from "./helpers/actors";
import { forgeOtpVerifiedAt, setForgedSessionCookie } from "./helpers/otp-forge";
import { SESSION_COOKIE, parseSessionCookie, type Session } from "@/lib/session";

/**
 * ⑥ (đợt "OTP trước token", `docs/giao-viec/2026-08-24-dot-otp-truoc-token.md`)
 * — bất biến CỐT LÕI của cả đợt: KHÔNG lượt nào được tốn token trước khi OTP
 * xác thực xong. 18 mục khác của checklist đều là phép chạy CỤC BỘ (hàm
 * thuần, AST, unit test) — đây là ô CHỨNG MINH SẢN PHẨM đúng qua browser
 * thật + backend thật + model thật, không chỉ "code đúng".
 *
 * 🔴 SOẠN 25/08 — CHƯA CHẠY. Có tốn token/LLM thật (case B/C gọi model
 * thật) — cần khai trước với Lead/PO theo lớp giữ hoá đơn A3
 * (`FIN05_ALLOW_PAID_CALLS`), gộp vào cùng buổi trả phí với ⑬-B1/C1 theo
 * quyết định Lead 25/08. KHÔNG tự chạy file này khi chưa có xác nhận buổi
 * đã mở.
 *
 * ## Ba điều PO nhắc lại — đọc trước khi sửa/chạy file này
 *
 * 1. Envelope `/api/agent-chat` mang `duong` và `usage.total_tokens` ra tới
 *    trình duyệt — đo TRỰC TIẾP trên response THẬT (chặn `page.on("response")`,
 *    cùng khuôn `chat-otp-token-cu-sau-xac-thuc.spec.ts`), KHÔNG suy từ nội
 *    dung DOM.
 * 2. BA trạng thái, không phải hai: `0` ≠ `null` ≠ `>0`. Gộp `null` vào `0`
 *    (`ép ?? 0`) làm một envelope HỎNG (thiếu khoá `usage`/`total_tokens`)
 *    trông y hệt một lượt 0 token thật — ca sẽ xanh vì đúng lý do sai. Mọi
 *    assertion dưới đây kiểm KIỂU (`typeof ... === "number"`) TRƯỚC giá trị.
 * 3. 🔴 Cạm bẫy đắt nhất: cổng ④ (OTP cho NHÓM B) chỉ bắn theo trạng thái
 *    XÁC THỰC của phiên, không phải theo "lần đầu của hội thoại" — nhưng để
 *    tránh MỌI nghi ngờ trạng thái rò rỉ giữa các ca (session/thread cũ còn
 *    sống), mỗi test dưới đây tự làm MỘT lượt `loginAs` MỚI (thread mới,
 *    theo `user_id:iat` — xem `chat-otp-token-cu-sau-xac-thuc.spec.ts`),
 *    không tái dùng `page`/`context` giữa các `test()`.
 */

interface PhanHoiAgentChat {
  reply?: string;
  tool_calls?: { tool_name?: string }[];
  duong?: string;
  usage?: { total_tokens?: number };
  [key: string]: unknown;
}

const CUSTOMER_PHONE = "0974000145"; // USR-0145, cùng tài khoản các spec khác dùng

async function readSessionCookie(context: BrowserContext): Promise<Session> {
  const cookies = await context.cookies();
  const raw = cookies.find((c) => c.name === SESSION_COOKIE)?.value;
  const session = parseSessionCookie(raw ? decodeURIComponent(raw) : raw);
  if (!session) throw new Error(`Không đọc được cookie ${SESSION_COOKIE} — chưa đăng nhập?`);
  return session;
}

/** Ép otp_verified_at=null NGAY SAU login — bảo đảm ca THẬT SỰ khởi hành từ
 * trạng thái "chưa xác thực OTP phiên", không phụ thuộc phiên cũ còn tươi
 * sót lại (đúng bẫy đã ghi nhận nhiều lần trong repo này). */
async function batDauChuaXacThucOtp(page: import("@playwright/test").Page, context: BrowserContext) {
  await loginAs(page, CUSTOMER_PHONE, "/chat");
  const phienThat = await readSessionCookie(context);
  const phienChuaOtp = forgeOtpVerifiedAt(phienThat, null);
  await setForgedSessionCookie(context, phienChuaOtp);
  await page.reload();
}

function ganResponseHook(page: import("@playwright/test").Page): PhanHoiAgentChat[] {
  const responses: PhanHoiAgentChat[] = [];
  page.on("response", async (res) => {
    if (res.url().includes("/api/agent-chat") && res.status() === 200) {
      try {
        responses.push(await res.json());
      } catch {
        /* bỏ qua response không phải JSON */
      }
    }
  });
  return responses;
}

test.describe("⑥ Bất biến '0 token trước OTP' — cổng ④ (NHÓM B)", () => {
  test("A — khiếu nại cá nhân, CHƯA xác thực OTP: cổng bắn, usage.total_tokens PHẢI = 0 (số, không phải null)", async ({
    page,
    context,
  }) => {
    test.setTimeout(60_000);
    await batDauChuaXacThucOtp(page, context);
    const responses = ganResponseHook(page);

    const input = page.getByPlaceholder("Nhập tin nhắn...");
    // Câu khiếu nại cá nhân THẬT — cùng câu đã xác nhận đi thu_slot ở tầng
    // triage.py trong ② (eval/bo_ca_am_thu_slot_dot2.json, DOT2-DUONG-01)
    // — chọn lại để KHÔNG cần tái xác nhận thêm câu này có "là khiếu nại cá
    // nhân" hay không, giảm một biến chưa biết trong ca UI.
    await input.fill("tôi chuyển nhầm tiền cho người lạ rồi, không nhớ chuyển bao nhiêu");
    await input.press("Enter");

    await expect
      .poll(() => responses.length, {
        message: "Không có response /api/agent-chat nào tới sau khi gõ khiếu nại cá nhân.",
        timeout: 20_000,
      })
      .toBeGreaterThan(0);

    const luot = responses[0];
    expect(luot.duong, `duong thực nhận: ${luot.duong}`).toBe("can_otp");
    // KIỂU trước GIÁ TRỊ — envelope hỏng (thiếu usage/total_tokens) không
    // được đọc thành "đạt 0 token" (xem lưu ý #2 ở docstring đầu file).
    expect(typeof luot.usage?.total_tokens, `usage.total_tokens THỰC: ${JSON.stringify(luot.usage)}`).toBe("number");
    expect(luot.usage?.total_tokens).toBe(0);
  });

  test("B — câu hỏi CHÍNH SÁCH, CHƯA xác thực OTP: cổng ④ KHÔNG được bắn (Q1, ca âm — Luật A)", async ({
    page,
    context,
  }) => {
    test.setTimeout(90_000);
    await batDauChuaXacThucOtp(page, context);
    const responses = ganResponseHook(page);

    const input = page.getByPlaceholder("Nhập tin nhắn...");
    // Câu hỏi chính sách chung — cùng câu đã xác nhận KHÔNG kích slot ở
    // tầng phan_luong (tests/test_1a_luat_hoi_prompt.py::
    // test_r1_cau_hoi_chinh_sach_khong_bi_hoi_slot).
    await input.fill("Phí chuyển tiền trong ví là bao nhiêu vậy?");
    await input.press("Enter");

    await expect
      .poll(() => responses.length, {
        message: "Không có response /api/agent-chat nào tới sau khi gõ câu hỏi chính sách.",
        timeout: 30_000,
      })
      .toBeGreaterThan(0);

    const luot = responses[0];
    expect(
      luot.duong,
      `Cổng ④ BẮN OAN cho câu hỏi chính sách (duong=${luot.duong}) — vi phạm Q1: ` +
        `"câu hỏi chính sách KHÔNG bị chặn OTP".`
    ).not.toBe("can_otp");
    // Ca ÂM không đòi usage>0 tuyệt đối (câu hỏi có thể rơi vào nhánh nhẹ
    // khác, 0 token vì lý do KHÁC "chặn OTP") — chỉ đòi ĐÚNG một điều: không
    // phải cổng ④.
  });

  test("C — SAU khi OTP xác thực xong: gửi lại đúng khiếu nại đó, cổng ④ KHÔNG còn chặn, model chạy thật (usage > 0)", async ({
    page,
    context,
  }) => {
    test.setTimeout(120_000);
    await batDauChuaXacThucOtp(page, context);
    const responses = ganResponseHook(page);

    const input = page.getByPlaceholder("Nhập tin nhắn...");
    // 🔴 [ĐO 25/08, buổi tốn phí] Câu PHẢI có sẵn số tiền — khác Case A cố ý.
    // Lần đầu viết câu này GIỐNG Case A (thiếu số tiền): sau OTP, cổng ⑤/T0
    // (`otp_resend_thu_slot`, 0 token) đúng đắn bắn để hỏi số tiền còn thiếu
    // — ĐÚNG hành vi sản phẩm, nhưng làm Case C thất bại SAI LÝ DO (assert
    // cũ đòi usage>0 tuyệt đối, không chấp nhận nhánh tất định hợp lệ này,
    // cùng họ lỗi `chat-otp-token-cu-sau-xac-thuc.spec.ts` đã cảnh báo: "chấp
    // nhận CẢ HAI đường đúng"). Sửa: cho sẵn số tiền để sau OTP không còn
    // slot nào thiếu ⟹ đi thẳng day_du (model chạy thật), tách bạch với
    // hành vi của ⑤ (phạm vi ca khác, không phải ca này).
    const cauKhieuNai = "tôi chuyển nhầm 500 nghìn cho người lạ rồi, không biết làm sao lấy lại";

    await input.fill(cauKhieuNai);
    await input.press("Enter");
    await expect
      .poll(() => responses.length, { timeout: 20_000 })
      .toBeGreaterThan(0);
    expect(responses[0].duong, "Tiền đề ca C: lượt đầu PHẢI bị cổng ④ chặn trước đã").toBe("can_otp");

    const otpHappened = await completeOtpIfPrompted(page, 40_000);
    expect(otpHappened, "OTP không xảy ra sau khi cổng ④ chặn — không đúng nhánh cần đo.").toBe(true);
    await expect(page.getByText("Xác thực thành công")).toBeVisible({ timeout: 10_000 });

    const soResponseTruocGuiLai = responses.length;
    await input.fill(cauKhieuNai);
    await input.press("Enter");

    await expect
      .poll(() => responses.length, {
        message: "Không có response /api/agent-chat MỚI nào sau khi gõ lại khiếu nại, sau OTP.",
        timeout: 30_000,
      })
      .toBeGreaterThan(soResponseTruocGuiLai);

    const luotSauOtp = responses[responses.length - 1];
    expect(luotSauOtp.duong, `duong sau OTP: ${luotSauOtp.duong} — cổng ④ KHÔNG được còn chặn`).not.toBe("can_otp");
    expect(typeof luotSauOtp.usage?.total_tokens, `usage sau OTP: ${JSON.stringify(luotSauOtp.usage)}`).toBe(
      "number"
    );
    expect(
      (luotSauOtp.usage?.total_tokens ?? 0) > 0,
      `Sau OTP mà usage.total_tokens vẫn = 0 (${luotSauOtp.usage?.total_tokens}) — model không chạy thật, ` +
        `nghi cổng tất định khác (thu_slot/otp_resend) đang bắn thay vì đường model đầy đủ.`
    ).toBe(true);
  });
});
