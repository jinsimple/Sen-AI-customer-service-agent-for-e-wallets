import { test, expect } from "@playwright/test";
import * as fs from "node:fs";
import * as path from "node:path";
import { loginAs, completeOtpIfPrompted } from "./helpers/actors";

/**
 * PO 25/08 — "backend trả gì" đã đo (transcript JSON). Việc CÒN THIẾU:
 * "khách NHÌN THẤY gì" — chữ có hiện đủ trên UI thật không, có vỡ khung
 * không, câu chống mạo danh/sàng lọc lừa đảo có đọc được không.
 *
 * 0 TOKEN — KHÔNG gọi LLM. Mock `/api/agent-chat` để trả lại ĐÚNG 8 response
 * JSON đã capture thật ở lần chạy 25/08 (kich_ban_chuyen_gia_8_luot_CHAY_
 * THAT_1787651644702.json), theo ĐÚNG thứ tự — nhưng để component React
 * thật render bong bóng từ dữ liệu đó. OTP verify vẫn gọi THẬT (auth thuần,
 * không LLM, không tốn gì) để đúng luồng thật của app, không giả lập tắt.
 */

const CUSTOMER_PHONE = "0974000145";
const TRANSCRIPT_PATH = path.resolve(
  __dirname,
  "../../eval/results/kich_ban_chuyen_gia_8_luot_CHAY_THAT_1787651644702.json"
);

interface PhanHoiAgentChat {
  reply: string;
  tool_calls: { tool_name?: string }[];
  duong?: string;
  [key: string]: unknown;
}

test.describe("Render thật — kịch bản chuyên gia 8 lượt (0 token, mock /api/agent-chat)", () => {
  test("chữ hiện đủ trên bong bóng, không vỡ khung, câu K3/sàng lọc đọc được — desktop", async ({ page }) => {
    test.setTimeout(90_000);
    const raw = JSON.parse(fs.readFileSync(TRANSCRIPT_PATH, "utf-8"));
    const queue: PhanHoiAgentChat[] = [...raw.all_responses];
    expect(queue.length, "transcript phải có đủ 8 response đã capture thật").toBe(8);

    let soLanGoi = 0;
    await page.route("**/api/agent-chat", async (route) => {
      soLanGoi++;
      const body = route.request().postData();
      const next = queue.shift();
      console.log(`>>> [MOCK #${soLanGoi}] request body: ${(body ?? "").slice(0, 150)}`);
      if (!next) {
        console.log(`>>> [MOCK #${soLanGoi}] HẾT HÀNG ĐỢI — trả response rỗng an toàn.`);
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ reply: "(MOCK RỖNG — hết hàng đợi)", tool_calls: [], duong: "day_du" }),
        });
        return;
      }
      console.log(`>>> [MOCK #${soLanGoi}] trả reply="${next.reply.slice(0, 60)}"`);
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(next) });
    });

    await loginAs(page, CUSTOMER_PHONE, "/chat");
    const input = page.getByPlaceholder("Nhập tin nhắn...");

    // Lượt 1 — mở ca (kích hoạt can_otp mock, response[0])
    await input.fill("tôi có chuyển tiền cho con gái cuối tháng 7 mà giờ nó mới nói chưa nhận đủ. tôi kiểm tra lại thì hình như tôi gõ sai số. giờ làm sao lấy lại được tiền");
    await input.press("Enter");
    await expect(page.locator(".bubble-bot").last()).toBeVisible({ timeout: 15_000 });

    // OTP — verify THẬT (0 token, thuần auth) rồi tự động resend (submitOtp
    // gọi sendToAgent nội bộ) → kích hoạt response[1] tự động, KHÔNG cần gõ lại.
    const otpXay = await completeOtpIfPrompted(page, 20_000);
    expect(otpXay, "Ca này PHẢI đi qua OTP để đúng thứ tự transcript").toBe(true);
    await expect(page.getByText("Xác thực thành công")).toBeVisible({ timeout: 10_000 });
    // Chờ auto-resend trả lời (response[1]) trước khi gõ tiếp.
    await page.waitForTimeout(1_500);

    const cauConLai = [
      "cuối tháng 7, khoảng 7 rưỡi tối, 339 nghìn",
      "0589 000 153. tôi gõ nhầm 2 số cuối thành 135. đúng là số này rồi",
      "không, số lạ hoàn toàn. tôi tự gõ, gõ vội nên nhầm",
      "vậy tôi muốn biết người nhận là ai. tiền của tôi mà tôi không được biết ai cầm à???",
      "thôi được, chị ghi nhận giúp tôi đi",
      "đúng rồi",
    ];
    for (const cau of cauConLai) {
      const soBongBongTruoc = await page.locator(".bubble-row.from-bot").count();
      await input.fill(cau);
      await input.press("Enter");
      await expect(page.locator(".bubble-row.from-bot")).toHaveCount(soBongBongTruoc + 1, { timeout: 15_000 });
    }

    expect(queue.length, "phải dùng hết đúng 8 response, không thừa không thiếu").toBe(0);

    // ===== ① So nội dung bong bóng với `reply` gốc — chữ hiện ĐỦ không =====
    // Dùng khớp KHÔNG-THEO-VỊ-TRÍ (mỗi reply gốc chỉ cần xuất hiện Ở ĐÂU ĐÓ
    // trong luồng, đủ nguyên văn) — vì đã quan sát bong bóng lượt 1 (can_otp)
    // xuất hiện HAI LẦN giống hệt nhau trong DOM (xem mục "phát hiện phụ" cuối
    // file), làm so khớp CHẶT theo vị trí báo sai "thiếu" trong khi thật ra
    // là THỪA. Khớp theo vị trí sẽ đo nhầm hai loại lỗi khác nhau thành một.
    const botBubbles = page.locator(".bubble-row.from-bot .bubble-bot");
    const soLuong = await botBubbles.count();
    const vanBanHienThi: string[] = [];
    for (let i = 0; i < soLuong; i++) {
      vanBanHienThi.push((await botBubbles.nth(i).innerText()).trim());
    }
    const gomKhoangTrang = (s: string) => s.replace(/\s+/g, " ").replace(/\*\*/g, "").trim();
    const boHienThi = vanBanHienThi.map(gomKhoangTrang);

    const repliesGoc = (raw.all_responses as PhanHoiAgentChat[]).map((r) => r.reply.trim());
    console.log(`>>> Tổng bong bóng bot trong DOM: ${soLuong} (kỳ vọng tối thiểu 1 lời chào + 1 "xác thực thành công" + 8 reply = 10)`);

    fs.writeFileSync(
      path.resolve(__dirname, "../../eval/results/render_that_so_sanh_25aug.json"),
      JSON.stringify({ repliesGoc, vanBanHienThi }, null, 2),
      "utf-8"
    );

    // `.bubble-bot` có thể chứa thêm dòng trích dẫn "nguồn: tool1 → tool2"
    // (`.bubble-cite`, khi lượt đó có gọi tool) NỐI THÊM sau `reply` — nên
    // kiểm CHỨA ĐỦ (startsWith sau chuẩn hoá), không đòi bằng tuyệt đối.
    const khongTimThay: number[] = [];
    for (let i = 0; i < repliesGoc.length; i++) {
      const gocGomKhoangTrang = gomKhoangTrang(repliesGoc[i]);
      const timThay = boHienThi.some((t) => t.startsWith(gocGomKhoangTrang));
      console.log(`--- reply[${i}] (${repliesGoc[i].length} ký tự gốc) — có bong bóng chứa ĐỦ nguyên văn trong DOM: ${timThay}`);
      if (!timThay) khongTimThay.push(i);
    }
    expect(
      khongTimThay,
      `${khongTimThay.length} reply KHÔNG tìm thấy bong bóng khớp nguyên văn trong DOM (chỉ số: ${khongTimThay.join(",")}) — xem eval/results/render_that_so_sanh_25aug.json để đối chiếu chi tiết.`
    ).toEqual([]);

    // ===== ② Câu chống mạo danh CSKH (K3) + câu sàng lọc lừa đảo — ưu tiên cao nhất =====
    const coK3O_dau = vanBanHienThi.some((t) => /mã xác thực phiên hỗ trợ|không phải.*OTP giao dịch|không bao giờ hỏi/i.test(t));
    console.log(`>>> Câu chống mạo danh K3 đọc được ở ĐÂU ĐÓ trong DOM: ${coK3O_dau}`);
    expect(coK3O_dau, "Câu chống mạo danh CSKH (K3) PHẢI đọc được trên UI thật.").toBe(true);

    // ===== ③ Định dạng — markdown thô (**) và newline có bị mất/sai không =====
    const coDauSaoThoTrenManHinh = vanBanHienThi.some((t) => t.includes("**"));
    console.log(`>>> Còn dấu ** THÔ trên màn hình (markdown không được render): ${coDauSaoThoTrenManHinh}`);

    // ===== 🔴 Phát hiện phụ — bong bóng lượt 1 (can_otp) có bị LẶP trong DOM
    // không (quan sát thật lần chạy đầu, KHÔNG phải giả định trước) =====
    const dem: Record<string, number> = {};
    for (const t of boHienThi) dem[t] = (dem[t] ?? 0) + 1;
    const bongBongLap = Object.entries(dem).filter(([, n]) => n > 1);
    if (bongBongLap.length > 0) {
      console.log(`🔴 PHÁT HIỆN PHỤ: ${bongBongLap.length} nội dung bong bóng LẶP trong DOM (số lần lặp): ${bongBongLap.map(([t, n]) => `${n}x "${t.slice(0, 40)}..."`).join("; ")}`);
    }

    // ===== ④ Không vỡ khung — bề rộng bong bóng không vượt khung chat =====
    const khungChat = page.locator(".chat-thread, .chat-panel").first();
    for (let i = 0; i < soLuong; i++) {
      const bubbleBox = await botBubbles.nth(i).boundingBox();
      const containerBox = await khungChat.boundingBox().catch(() => null);
      if (bubbleBox && containerBox) {
        expect(
          bubbleBox.x + bubbleBox.width,
          `Bong bóng ${i} TRÀN ra ngoài khung chat (desktop)`
        ).toBeLessThanOrEqual(containerBox.x + containerBox.width + 2);
      }
    }

    await page.screenshot({ path: path.resolve(__dirname, "../../eval/results/render_that_desktop_25aug.png"), fullPage: true });
  });

  test("mobile 375px — không vỡ khung, K3 vẫn đọc được", async ({ page }) => {
    test.setTimeout(90_000);
    await page.setViewportSize({ width: 375, height: 812 });

    const raw = JSON.parse(fs.readFileSync(TRANSCRIPT_PATH, "utf-8"));
    const queue: PhanHoiAgentChat[] = [...raw.all_responses];

    await page.route("**/api/agent-chat", async (route) => {
      const next = queue.shift();
      if (!next) {
        await route.fulfill({
          status: 200,
          contentType: "application/json",
          body: JSON.stringify({ reply: "(MOCK RỖNG)", tool_calls: [], duong: "day_du" }),
        });
        return;
      }
      await route.fulfill({ status: 200, contentType: "application/json", body: JSON.stringify(next) });
    });

    await loginAs(page, CUSTOMER_PHONE, "/chat");
    const input = page.getByPlaceholder("Nhập tin nhắn...");
    await input.fill("tôi có chuyển tiền cho con gái cuối tháng 7 mà giờ nó mới nói chưa nhận đủ. tôi kiểm tra lại thì hình như tôi gõ sai số. giờ làm sao lấy lại được tiền");
    await input.press("Enter");
    await expect(page.locator(".bubble-bot").last()).toBeVisible({ timeout: 15_000 });
    const otpXay = await completeOtpIfPrompted(page, 20_000);
    expect(otpXay).toBe(true);
    await expect(page.getByText("Xác thực thành công")).toBeVisible({ timeout: 10_000 });
    await page.waitForTimeout(1_500);

    // Chỉ cần tới lượt có câu K3 (đã hiện ở lượt 1) — đủ để kiểm mobile không vỡ khung.
    const viewport = page.viewportSize();
    const botBubbles = page.locator(".bubble-row.from-bot .bubble-bot");
    const soLuong = await botBubbles.count();
    for (let i = 0; i < soLuong; i++) {
      const box = await botBubbles.nth(i).boundingBox();
      if (box && viewport) {
        expect(box.x + box.width, `Bong bóng ${i} TRÀN ra ngoài viewport 375px (mobile)`).toBeLessThanOrEqual(viewport.width + 2);
      }
    }

    const tatCaBongBong: string[] = [];
    for (let i = 0; i < soLuong; i++) tatCaBongBong.push((await botBubbles.nth(i).innerText()).trim());
    const coK3 = tatCaBongBong.some((t) => /mã xác thực phiên hỗ trợ|không phải.*OTP giao dịch|không bao giờ hỏi/i.test(t));
    expect(coK3, "K3 phải đọc được trên mobile 375px").toBe(true);

    await page.screenshot({ path: path.resolve(__dirname, "../../eval/results/render_that_mobile_25aug.png"), fullPage: true });
  });
});
