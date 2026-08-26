import { test, expect } from "@playwright/test";
import { DEMO_PASSWORD, loginAs } from "./helpers/actors";

/**
 * [ĐO 26/08] PO nghi (từ ghi chú cũ, CHƯA tự kiểm lại): phiên làm việc định
 * danh bằng mã người dùng ghép thời điểm đăng nhập TÍNH THEO GIÂY — nếu
 * đúng, hai người bấm đăng nhập trong CÙNG một giây sẽ trùng mã phiên.
 *
 * Bối cảnh: PO sắp share công khai, chỉ có vài tài khoản demo — kịch bản
 * ĐIỂN HÌNH (không hiếm): nhiều người lạ cùng bấm nút "Đăng nhập nhanh"
 * trên /login gần như CÙNG LÚC, tất cả vào CHUNG một tài khoản khách hàng
 * demo (0974000145). Nếu phiên bị trộn, người lạ A thấy được hội thoại của
 * người lạ B — SỰ CỐ RIÊNG TƯ trên sản phẩm tài chính, xảy ra TRƯỚC MẶT
 * người PO mời tới xem.
 *
 * Đo bằng 2 browser context TÁCH BIỆT (không chung cookie — mô phỏng đúng
 * "hai trình duyệt khác nhau"), đăng nhập CÙNG một tài khoản CÀNG GẦN NHAU
 * CÀNG TỐT (Promise.all, không tuần tự), mỗi bên gửi một câu hỏi có chuỗi
 * ĐẶC TRƯNG dễ nhận, rồi kiểm CHÉO xem màn bên này có lộ chuỗi của bên kia
 * không.
 *
 * 🔴 Gọi LLM THẬT — giữ ĐÚNG 1 cặp (2 lượt gọi), không lặp lại nhiều lần
 * (PO: hạn mức đã gỡ nhưng vẫn phải giữ số lượt tối thiểu).
 */

const DEMO_CUSTOMER_PHONE = "0974000145"; // USR-0145 — số trên nút "Đăng nhập nhanh" thật của /login

test.describe("PRIVACY — nhiều người cùng đăng nhập MỘT tài khoản demo gần như đồng thời", () => {
  test("hai phiên trình duyệt tách biệt, cùng tài khoản demo, đăng nhập + gửi tin gần như cùng lúc -> KHÔNG thấy tin của nhau", async ({
    browser,
  }) => {
    test.setTimeout(90_000);

    const contextA = await browser.newContext();
    const contextB = await browser.newContext();
    const pageA = await contextA.newPage();
    const pageB = await contextB.newPage();

    try {
      // Đăng nhập GẦN NHƯ ĐỒNG THỜI — Promise.all, không await tuần tự từng
      // cái, đúng kịch bản "nhiều người bấm link cùng lúc".
      await Promise.all([loginAs(pageA, DEMO_CUSTOMER_PHONE, "/chat"), loginAs(pageB, DEMO_CUSTOMER_PHONE, "/chat")]);

      // 🔴 [ĐO 26/08, tự bắt trước khi báo cáo] /chat hiện SẴN 1 bubble bot
      // chào hỏi ngay lúc vào trang (KHÔNG qua LLM) — `expect(.bubble-bot.last())
      // .toBeVisible()` trần trụi sẽ khớp NGAY bubble chào này, không chờ trả
      // lời thật, làm ca "không rò rỉ" xanh mà KHÔNG hề xác nhận request đã
      // chạm backend/LLM (đo được: lượt chạy đầu 2.4s, 0 dòng usage.jsonl).
      // Phải đếm SỐ LƯỢNG bubble bot TRƯỚC, chờ tăng thêm đúng 1 — mới chắc
      // là bubble MỚI, không phải bubble chào có sẵn.
      const soBubbleBanDauA = await pageA.locator(".bubble-bot").count();
      const soBubbleBanDauB = await pageB.locator(".bubble-bot").count();

      const markerA = `MA-DAC-TRUNG-PHIEN-ALPHA-${Date.now()}`;
      const markerB = `MA-DAC-TRUNG-PHIEN-BETA-${Date.now()}`;
      const questionA = `Câu hỏi riêng của phiên ALPHA, mã nhận diện ${markerA} — phí rút tiền về ngân hàng là bao nhiêu vậy bạn?`;
      const questionB = `Câu hỏi riêng của phiên BETA, mã nhận diện ${markerB} — phí chuyển tiền nội bộ ví là bao nhiêu vậy bạn?`;

      // Gửi gần như đồng thời — cùng lý do: rò rỉ do đụng độ thời điểm thường
      // KHÔNG lộ nếu làm tuần tự có khoảng cách.
      await Promise.all([
        (async () => {
          const input = pageA.getByPlaceholder("Nhập tin nhắn...");
          await input.fill(questionA);
          await input.press("Enter");
        })(),
        (async () => {
          const input = pageB.getByPlaceholder("Nhập tin nhắn...");
          await input.fill(questionB);
          await input.press("Enter");
        })(),
      ]);

      // Chờ SỐ LƯỢNG bubble bot mỗi bên TĂNG THÊM ĐÚNG 1 so với baseline —
      // xác nhận đây là bubble MỚI (request đã hoàn tất thật), không phải
      // bubble chào có sẵn từ lúc vào trang.
      await Promise.all([
        expect(pageA.locator(".bubble-bot")).toHaveCount(soBubbleBanDauA + 1, { timeout: 60_000 }),
        expect(pageB.locator(".bubble-bot")).toHaveCount(soBubbleBanDauB + 1, { timeout: 60_000 }),
      ]);

      const noiDungA = await pageA.locator("body").innerText();
      const noiDungB = await pageB.locator("body").innerText();

      // Sanity trước — mỗi bên PHẢI thấy câu hỏi CỦA CHÍNH MÌNH (nếu không,
      // ca dưới "không thấy của người kia" xanh vì lý do sai — cả hai màn
      // đều trống/hỏng, không phải vì cách ly đúng).
      expect(noiDungA, "Màn A không thấy câu hỏi CỦA CHÍNH MÌNH — bài đo hỏng, không phải cách ly đúng").toContain(
        markerA
      );
      expect(noiDungB, "Màn B không thấy câu hỏi CỦA CHÍNH MÌNH — bài đo hỏng, không phải cách ly đúng").toContain(
        markerB
      );

      // Phép đo THẬT — đây là điều PO cần biết.
      expect(
        noiDungA,
        `🔴 RÒ RỈ PHIÊN: màn hình A (đăng nhập ${DEMO_CUSTOMER_PHONE}) thấy được mã đặc trưng của phiên B ` +
          `(${markerB}) — hai người lạ cùng tài khoản demo NHÌN THẤY HỘI THOẠI CỦA NHAU. Sự cố riêng tư ` +
          `thật trên sản phẩm tài chính, phải chặn TRƯỚC khi share công khai.`
      ).not.toContain(markerB);
      expect(
        noiDungB,
        `🔴 RÒ RỈ PHIÊN: màn hình B thấy được mã đặc trưng của phiên A (${markerA}) — chiều ngược lại của ` +
          `lỗi trên.`
      ).not.toContain(markerA);
    } finally {
      await contextA.close();
      await contextB.close();
    }
  });
});
