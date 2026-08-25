import { test, expect, type BrowserContext } from "@playwright/test";
import { loginAs, completeOtpIfPrompted } from "./helpers/actors";
import { forgeOtpVerifiedAt, setForgedSessionCookie } from "./helpers/otp-forge";
import { SESSION_COOKIE, parseSessionCookie, type Session } from "@/lib/session";

/**
 * Bug PO thật tự tìm ra (24/08) — frontend gọi `await verifyOtp(...)` rồi
 * VỨT kết quả, không lưu `access_token` MỚI mà OTP verify trả về. Mọi tin
 * nhắn GỬI SAU đó vẫn mang token CŨ (chưa xác thực) → agent nói "phiên chưa
 * hoàn tất xác thực" NGAY SAU KHI giao diện vừa báo "Xác thực thành công" —
 * một mâu thuẫn ngay trước mắt người dùng.
 *
 * 🔴 Vì sao suite trước đó không thấy: `_login()` (tests/ Python) và
 * `completeOtpIfPrompted` (helper e2e cũ) đều LẤY LẠI token mới sau verify —
 * đúng cách backend thiết kế, nhưng đó là "đường TEST đi", không phải "đường
 * UI THẬT đi" (ChatClient.tsx tự gọi verifyOtp() bên trong, người dùng không
 * có cơ hội can thiệp). Nguyên tắc PO-agent đặt ra: đường test đi qua và
 * đường người dùng đi qua phải là MỘT — khác nhau ở đâu, đo hỏng ở đó.
 *
 * `chat.spec.ts::"gõ tự do tham chiếu đúng mã giao dịch thật"` ĐÃ đi đúng
 * luồng free-text OTP-giữa-chừng này, nhưng KHÔNG ép otp_verified_at về
 * null trước — nếu phiên còn OTP tươi sót lại từ lượt chạy trước (đúng bẫy
 * đã ghi nhận nhiều lần trong repo này, xem unlockTxnRail/rail-cong-otp-loi-6),
 * OTP thật KHÔNG xảy ra trong lượt chạy đó và bug không có cơ hội lộ ra. Test
 * này ép otp_verified_at=null qua forgeOtpVerifiedAt (kỹ thuật time-travel
 * JWT đã có tiền lệ, KHÔNG phải bypass auth) để BẢO ĐẢM một lượt OTP THẬT
 * xảy ra trong chính lượt chạy, không phụ thuộc trạng thái sót lại.
 *
 * 🔴 [ĐO 24/08, RED-verify trên ngăn CHƯA vá — df65149] Bản đầu của ca này
 * CHỈ assert "reply không chứa TEXT_MOI_OTP" + "reply không rỗng" — chạy
 * trên ngăn CHƯA vá vẫn XANH (false green). Đọc `usage.jsonl` thật lúc đo:
 * lượt gửi lại sau OTP có `so_tool_call: 0` — agent KHÔNG gọi lại tool nào,
 * chỉ trả lời từ trí nhớ hội thoại cũ (một câu nghe hợp lý nhưng không tra
 * lại) — đúng root cause Coder khai (`5e8deb6`, KHÁC giả thuyết token/cookie
 * ban đầu). Hai assertion cũ không bắt được kiểu lỗi này vì câu trả lời từ
 * trí nhớ vẫn không rỗng và không nói "cần xác thực lại". Vá bằng cách chặn
 * response `/api/agent-chat` THẬT (đúng khuôn gd4-nghiem-thu-chinh.spec.ts)
 * và assert trực tiếp `tool_calls` của lượt cuối — bằng chứng THẬT agent có
 * tra lại hay không, không suy từ nội dung DOM.
 *
 * 🔴 [ĐO 24/08, Coder báo TRƯỚC khi tôi kịp chạy lại] `a663583` land THÊM một
 * cơ chế mới, khác `5e8deb6`: field `vua_xac_thuc_de_gui_lai` (frontend tự
 * đặt `true` ở đúng lượt gửi-lại-sau-OTP) → NẾU câu KHÔNG kèm mã giao dịch/
 * mốc thời gian, agent trả lời TẤT ĐỊNH (`duong=otp_resend_thu_slot`, 0
 * token, `tool_calls=[]`) hỏi lại mã/ngày.
 *
 * PO-agent chỉ ra: bug cũ và hành vi đúng MỚI **CÙNG HÌNH DẠNG NHÌN TỪ
 * NGOÀI** (cả hai đều `tool_calls=[]`) — nhưng vì HAI LÝ DO NGƯỢC NHAU:
 *
 *     bug cũ (nhớ lượt trước)   tool_calls=[]   model CÓ chạy (usage>0)   duong=day_du
 *     đúng mới (cổng bắn)       tool_calls=[]   model KHÔNG chạy (usage=0) duong=otp_resend_thu_slot
 *
 * ⟹ Khoá vào `duong`/`usage.total_tokens`, KHÔNG khoá vào riêng `tool_calls`
 * — chấp nhận HAI đường đúng (cổng bắn tất định HOẶC model chịu gọi lại
 * tool), chỉ chặn ĐÚNG một chữ ký hỏng: model đã chạy MÀ không gọi tool nào.
 */

interface PhanHoiAgentChat {
  reply?: string;
  tool_calls?: { tool_name?: string; args?: Record<string, unknown>; result?: unknown }[];
  ticket_id?: string | null;
  duong?: string;
  usage?: { total_tokens?: number };
  [key: string]: unknown;
}
const CUSTOMER_PHONE = "0974000145"; // USR-0145, cùng tài khoản auth.spec.ts dùng

// Đúng nguyên văn hằng số TEXT_MOI_OTP đã xác nhận ở chat-403-role-loai.spec.ts
// — chuỗi DETERMINISTIC frontend hiện khi tool result có loai="otp_het_tuoi",
// không phải suy đoán cách LLM diễn đạt.
const TEXT_MOI_OTP = "Để tiếp tục thao tác này, mình cần bạn xác thực lại OTP phiên làm việc nhé.";

async function readSessionCookie(context: BrowserContext): Promise<Session> {
  const cookies = await context.cookies();
  const raw = cookies.find((c) => c.name === SESSION_COOKIE)?.value;
  const session = parseSessionCookie(raw ? decodeURIComponent(raw) : raw);
  if (!session) throw new Error(`Không đọc được cookie ${SESSION_COOKIE} — chưa đăng nhập?`);
  return session;
}

test.describe("Token OTP mới phải được DÙNG THẬT sau khi xác thực (không phải chỉ hiện 'thành công')", () => {
  test("gõ câu cần tra cứu -> xác thực OTP qua UI -> gõ tiếp: PHẢI tra cứu được, KHÔNG được nói phiên chưa xác thực", async ({
    page,
    context,
  }) => {
    test.setTimeout(120_000);
    await loginAs(page, CUSTOMER_PHONE, "/chat");

    // Ép otp_verified_at=null — bảo đảm lượt này THẬT SỰ đi qua một lần xác
    // thực OTP mới, không phải sống nhờ phiên còn tươi sót lại từ trước.
    const realSession = await readSessionCookie(context);
    const nguoi = forgeOtpVerifiedAt(realSession, null);
    await setForgedSessionCookie(context, nguoi);
    await page.reload();

    // Trục khẳng định chính cho tool_calls — response /api/agent-chat THẬT,
    // theo đúng thứ tự tới (cùng khuôn gd4-nghiem-thu-chinh.spec.ts). DOM chỉ
    // dùng để điều khiển (gõ/bấm/OTP) + kiểm câu chữ "không nói phiên chưa
    // xác thực" — bằng chứng "có tra lại hay không" đọc từ ĐÂY, không đoán.
    const responsesThat: PhanHoiAgentChat[] = [];
    page.on("response", async (res) => {
      if (res.url().includes("/api/agent-chat") && res.status() === 200) {
        try {
          responsesThat.push(await res.json());
        } catch {
          /* bỏ qua response không phải JSON */
        }
      }
    });

    const input = page.getByPlaceholder("Nhập tin nhắn...");
    const question = "Cho mình xem lịch sử giao dịch gần đây của mình được không?";

    // Tối đa 2 lần gửi — LLM không phải lúc nào cũng gọi tool cần OTP ngay
    // lượt đầu (đã ghi nhận ở auth.spec.ts::triggerSensitiveAction), bounded
    // retry cùng khuôn createTicketAsCustomerViaAI, không lặp vô hạn.
    let otpHappened = false;
    for (let attempt = 1; attempt <= 2 && !otpHappened; attempt++) {
      await input.fill(question);
      await input.press("Enter");
      otpHappened = await completeOtpIfPrompted(page, 40_000);
    }
    expect(otpHappened, "OTP không xảy ra lần nào sau 2 lượt gõ — không đúng nhánh cần đo cho ca này.").toBe(true);
    await expect(page.getByText("Xác thực thành công")).toBeVisible({ timeout: 10_000 });

    // Gõ TỰ DO trigger OTP giữa chừng KHÔNG tự gửi lại câu hỏi gốc (khác
    // luồng chip — xem docstring completeOtpIfPrompted) — khách phải tự gõ
    // tiếp. ĐÂY là đúng bước "gõ tiếp" PO-agent mô tả, và đúng chỗ bug sống:
    // nếu frontend vứt access_token mới HOẶC agent chỉ trả lời từ trí nhớ cũ
    // (root cause thật, Coder), LƯỢT NÀY lộ ra ở đây.
    const soResponseTruocGuiLai = responsesThat.length;
    await input.fill(question);
    await input.press("Enter");

    const lastBotBubble = page.locator(".bubble-bot").last();
    await expect(lastBotBubble).not.toContainText(TEXT_MOI_OTP, {
      timeout: 20_000,
    });

    // Bằng chứng THẬT — chờ response /api/agent-chat MỚI của đúng lượt gõ
    // lại này, rồi đọc duong/usage/tool_calls TRỰC TIẾP từ nó. KHÔNG suy từ
    // nội dung DOM (một câu trả lời từ trí nhớ cũ vẫn đọc "hợp lý" và không
    // rỗng — đúng false green đã đo được trên ngăn chưa vá, xem ghi chú đầu
    // file). KHÔNG khoá riêng `tool_calls` (PO-agent chỉ ra bug cũ và cổng
    // tất định mới CÙNG cho tool_calls=[]) — chấp nhận CẢ HAI đường đúng,
    // chỉ chặn đúng chữ ký hỏng: model đã chạy mà không gọi tool nào.
    await expect
      .poll(() => responsesThat.length, {
        message: "Không có response /api/agent-chat MỚI nào tự tới sau khi gõ lại câu hỏi.",
        timeout: 20_000,
      })
      .toBeGreaterThan(soResponseTruocGuiLai);
    const phanHoiLuotGoiLai = responsesThat[responsesThat.length - 1];
    const laCongTatDinh = phanHoiLuotGoiLai.duong === "otp_resend_thu_slot";
    const coToolTraCuu = (phanHoiLuotGoiLai.tool_calls?.length ?? 0) > 0;
    const modelDaChay = (phanHoiLuotGoiLai.usage?.total_tokens ?? 0) > 0;
    expect(
      laCongTatDinh || coToolTraCuu,
      `Không khớp đường ĐÚNG nào (cổng tất định otp_resend_thu_slot HOẶC model chịu gọi lại tool).\n` +
        `  duong=${phanHoiLuotGoiLai.duong ?? "?"} tool_calls=${JSON.stringify(phanHoiLuotGoiLai.tool_calls)} ` +
        `model_da_chay=${modelDaChay}\n` +
        `  reply: ${(phanHoiLuotGoiLai.reply ?? "").slice(0, 300)}\n` +
        (modelDaChay && !coToolTraCuu
          ? "  ĐÚNG CHỮ KÝ BUG: model đã chạy (usage.total_tokens>0) mà KHÔNG gọi tool nào — " +
            "agent trả lời từ trí nhớ cũ thay vì tra lại (5e8deb6 phải vá đúng chỗ này)."
          : "")
    ).toBe(true);
  });
});
