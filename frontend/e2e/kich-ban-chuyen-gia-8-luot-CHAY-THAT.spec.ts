import { test } from "@playwright/test";
import * as fs from "node:fs";
import * as path from "node:path";
import { loginAs, completeOtpIfPrompted } from "./helpers/actors";

/**
 * ③ CHẠY THẬT — kịch bản chuyên gia 8 lượt (buổi tốn phí 25/08, tín hiệu đi
 * từ PO sau khi fin05-dot-otp dựng lại + cả hai phép kiểm băm/cờ xanh).
 *
 * KHÔNG assert pass/fail ở đây — mục đích là GHI LẠI nguyên văn + response
 * JSON của từng lượt để đối chiếu tay với
 * eval/kich-ban-chuyen-gia-8-luot-DANG-KY-TRUOC-CHAY.md (tiêu chí đã đăng ký
 * TRƯỚC khi chạy). Đúng/sai được chấm SAU, ở tài liệu đó — không chấm trong
 * chính file chạy.
 *
 * Ghi transcript JSON ra eval/results/ để làm bằng chứng, cộng với giải mã
 * checkpoint blob sau khi chạy (không tin riêng response JSON này).
 */

const CUSTOMER_PHONE = "0974000145"; // USR-0145, đã re-confirm login trên ảnh mới

interface PhanHoiAgentChat {
  reply?: string;
  tool_calls?: { tool_name?: string; args?: unknown }[];
  duong?: string;
  usage?: { total_tokens?: number; [k: string]: unknown };
  [key: string]: unknown;
}

const LUOT: { nhan: string; cau: string }[] = [
  {
    nhan: "Lượt 1 — mở ca (ĐÃ ĐỔI mốc thời gian, xem file đăng ký)",
    cau: "tôi có chuyển tiền cho con gái cuối tháng 7 mà giờ nó mới nói chưa nhận đủ. tôi kiểm tra lại thì hình như tôi gõ sai số. giờ làm sao lấy lại được tiền",
  },
  {
    nhan: "Lượt 2 — trả lời thời gian + số tiền (ĐÃ ĐỔI theo fixture thật)",
    cau: "cuối tháng 7, khoảng 7 rưỡi tối, 339 nghìn",
  },
  {
    nhan: "Lượt 4-khách — SĐT đúng + xác nhận nhầm (ĐÃ ĐỔI theo fixture thật)",
    cau: "0589 000 153. tôi gõ nhầm 2 số cuối thành 135. đúng là số này rồi",
  },
  {
    nhan: "Lượt 5-khách — không bị lừa, tự gõ nhầm",
    cau: "không, số lạ hoàn toàn. tôi tự gõ, gõ vội nên nhầm",
  },
  {
    nhan: "Lượt 6-khách — đòi biết danh tính người nhận",
    cau: "vậy tôi muốn biết người nhận là ai. tiền của tôi mà tôi không được biết ai cầm à???",
  },
  {
    nhan: "Lượt 7-khách — đồng ý ghi nhận",
    cau: "thôi được, chị ghi nhận giúp tôi đi",
  },
  {
    nhan: "Lượt 8-khách — xác nhận tóm tắt đúng",
    cau: "đúng rồi",
  },
];

test("Kịch bản chuyên gia 8 lượt — chạy thật trên fin05-dot-otp", async ({ page }) => {
  test.setTimeout(15 * 60_000);

  const responses: PhanHoiAgentChat[] = [];
  const transcript: { nhan: string; khach?: string; bot_bubble?: string; response_json?: PhanHoiAgentChat }[] = [];

  page.on("response", async (res) => {
    if (res.url().includes("/api/agent-chat") && res.status() === 200) {
      try {
        responses.push(await res.json());
      } catch {
        /* bỏ qua response không phải JSON */
      }
    }
  });

  await loginAs(page, CUSTOMER_PHONE, "/chat");
  const input = page.getByPlaceholder("Nhập tin nhắn...");

  async function guiVaCho(cau: string, nhan: string) {
    const soTruoc = responses.length;
    await input.fill(cau);
    await input.press("Enter");
    await test.step(`gửi: ${nhan}`, async () => {
      await page
        .waitForFunction((n) => n >= 0, soTruoc, { timeout: 1 })
        .catch(() => {});
    });
    // chờ response MỚI thật sự tới (LLM thật có thể mất 10-40s)
    const deadline = Date.now() + 90_000;
    while (responses.length <= soTruoc && Date.now() < deadline) {
      await page.waitForTimeout(500);
    }
    if (responses.length <= soTruoc) {
      throw new Error(`Không có response /api/agent-chat mới sau 90s cho: ${nhan}`);
    }
    return responses[responses.length - 1];
  }

  // Lượt 1
  let r = await guiVaCho(LUOT[0].cau, LUOT[0].nhan);
  transcript.push({ nhan: LUOT[0].nhan, khach: LUOT[0].cau, response_json: r });
  console.log(`[${LUOT[0].nhan}] duong=${r.duong} usage=${JSON.stringify(r.usage)} reply="${(r.reply ?? "").slice(0, 200)}"`);

  // OTP nếu bị chặn (rất có thể — đây là lượt đầu đụng dữ liệu khách hàng)
  const otpXay = await completeOtpIfPrompted(page, 40_000);
  if (otpXay) {
    console.log(">>> OTP đã xác thực. Gửi LẠI đúng câu Lượt 1 (free-typed KHÔNG tự resend).");
    const soTruoc = responses.length;
    r = await guiVaCho(LUOT[0].cau, `${LUOT[0].nhan} (gửi lại sau OTP)`);
    transcript.push({ nhan: `${LUOT[0].nhan} — SAU OTP (gửi lại)`, khach: LUOT[0].cau, response_json: r });
    console.log(`[sau OTP, gửi lại L1] duong=${r.duong} usage=${JSON.stringify(r.usage)} reply="${(r.reply ?? "").slice(0, 300)}"`);
    void soTruoc;
  } else {
    console.log(">>> KHÔNG có OTP xuất hiện ở lượt 1 — ghi lại để đối chiếu với tiêu chí đăng ký trước (BẮT BUỘC #4).");
  }

  // Các lượt còn lại — tuần tự
  for (let i = 1; i < LUOT.length; i++) {
    r = await guiVaCho(LUOT[i].cau, LUOT[i].nhan);
    transcript.push({ nhan: LUOT[i].nhan, khach: LUOT[i].cau, response_json: r });
    console.log(`[${LUOT[i].nhan}] duong=${r.duong} usage=${JSON.stringify(r.usage)} tool_calls=${JSON.stringify(r.tool_calls)} reply="${(r.reply ?? "").slice(0, 300)}"`);
  }

  const outDir = path.resolve(__dirname, "../../eval/results");
  const outPath = path.join(outDir, `kich_ban_chuyen_gia_8_luot_CHAY_THAT_${Date.now()}.json`);
  fs.writeFileSync(outPath, JSON.stringify({ transcript, all_responses: responses }, null, 2), "utf-8");
  console.log(`>>> Transcript đã ghi: ${outPath}`);
});
