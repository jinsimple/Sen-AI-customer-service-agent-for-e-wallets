import { test, expect } from "@playwright/test";
import { completeOtpIfPrompted, loginAs, unlockTxnRail } from "./helpers/actors";

/**
 * GĐ2 (docs/giao-viec/2026-08-19-gd2-envelope-null-va-e2e-ui.md) — đúng ca
 * PO thật vấp: gõ "chào bạn" trên UI thật → "Có lỗi khi kết nối trợ lý".
 * Backend trả 200 OK, reply đầy đủ, nhưng `tool_calls: null` (không phải
 * `[]`) khiến `ChatClient.tsx:346` gọi `.length` trên `null` → TypeError →
 * rơi vào nhánh lỗi chung, không bubble reply nào được vẽ.
 *
 * TRỤC "3 case khác thật" — Lead 19/08 chọn TRỤC B (khác TRẠNG THÁI PHIÊN,
 * không phải khác câu chữ — ba câu chào khác chữ nhưng cùng khớp allow-list
 * đường nhẹ, cùng dựng envelope tại MỘT dòng, là một case chạy ba lần):
 *   (a) chào ở phiên MỚI — lịch sử hội thoại RỖNG
 *   (b) chào SAU một lượt nặng đã chạy — lịch sử có ToolMessage thật (ca
 *       giao thoa với vá A của GĐ1: rap_nguon_o3 gom lịch sử cho đường nhẹ)
 *   (c) chào NGAY SAU một lượt fallback lỗi — CHỈ giữ nếu ép được BẰNG
 *       ĐƯỜNG SẢN PHẨM THẬT qua UI; không ép được thì KHÔNG BỊA, ghi rõ
 *       "không dựng được ở tầng E2E" và để tầng TRONG
 *       (test_trong_fallback_nha_cung_cap_tool_calls_la_mang trong
 *       tests/test_api/test_gd2_tool_calls_khong_null.py) phủ thay.
 *
 * NGHIỆM THU THEO NỘI DUNG, không chỉ theo HTTP (Lead: "HTTP 200 là chính
 * xác thứ đã nói dối trong ca này") — assert bubble bot có chữ THẬT, và
 * KHÔNG có câu lỗi chung ("Có lỗi khi kết nối trợ lý...", đã dùng làm ca âm
 * ở accessibility.spec.ts::UX-05 cho một kịch bản KHÁC — network abort, còn
 * ca này là lỗi tầng envelope trên một response 200 THẬT).
 */
const CUSTOMER_PHONE = "0974000145"; // USR-0145 — đúng account PO thật gõ tay khi vấp bug

const CAU_LOI_CHUNG = "Có lỗi khi kết nối trợ lý, thử lại giúp mình nhé.";

async function guiCauChaoVaKiemTraBubble(page: import("@playwright/test").Page, cau: string, boLenh?: () => Promise<void>) {
  const input = page.getByPlaceholder("Nhập tin nhắn...");
  const soBotBubbleTruoc = await page.locator(".bubble-bot").count();
  await input.fill(cau);
  await input.press("Enter");

  // KHÔNG chỉ chờ HTTP 200 — chờ MỘT TRONG HAI: bubble bot mới xuất hiện,
  // hoặc câu lỗi chung hiện ra. Race hai khả năng để phân biệt được XANH
  // thật (bubble có chữ) với ĐỎ (không bubble nào, chỉ có câu lỗi chung).
  const botBubbleMoi = page.locator(".bubble-bot").nth(soBotBubbleTruoc);
  const banhLoi = page.getByText(CAU_LOI_CHUNG);
  await Promise.race([
    botBubbleMoi.waitFor({ state: "visible", timeout: 20_000 }).catch(() => null),
    banhLoi.waitFor({ state: "visible", timeout: 20_000 }).catch(() => null),
  ]);

  const coLoi = await banhLoi.isVisible().catch(() => false);
  if (coLoi) {
    throw new Error(
      `[ĐỎ ĐÚNG DỰ BÁO trên ảnh chưa vá / ĐỎ SAI DỰ BÁO trên ảnh đã vá] Câu "${cau}" nhận câu lỗi chung ` +
        `"${CAU_LOI_CHUNG}" thay vì bubble reply — đúng hình dạng TypeError trên tool_calls=null.`
    );
  }

  await expect(botBubbleMoi).toBeVisible({ timeout: 5_000 });
  const text = (await botBubbleMoi.textContent())?.trim() ?? "";
  expect(text.length, `Bubble bot mới xuất hiện nhưng RỖNG cho câu ${cau}`).toBeGreaterThan(0);
  return text;
}

test.describe("CHAO-* — GĐ2: câu chào đường nhẹ không được vỡ UI (trục: trạng thái phiên)", () => {
  test("(a) chào ở phiên MỚI, chưa có lượt hội thoại nào", async ({ page }) => {
    await loginAs(page, CUSTOMER_PHONE, "/chat");
    const text = await guiCauChaoVaKiemTraBubble(page, "chào bạn");
    expect(text).not.toBe("");
  });

  test("(b) chào SAU một lượt nặng đã chạy — lịch sử có kết quả tool thật", async ({ page }) => {
    test.setTimeout(90_000);
    await loginAs(page, CUSTOMER_PHONE, "/chat");

    // Lượt nặng thật trước: hỏi giao dịch gần đây (rail đã có sẵn dữ liệu
    // demo cho USR-0145) — bắt buộc TỐN TOKEN, đã khai + Lead duyệt phần ②.
    // Rail khoá theo mặc định (phiên không tự động "tươi") — phải xác thực
    // OTP trước khi .txn-item render, đúng docstring unlockTxnRail() ở
    // helpers/actors.ts. [ĐO] tự bắt lỗi: bản đầu quên bước này, .txn-item
    // timeout 15s vì rail còn khoá — lỗi Ở TEST, không phải sản phẩm.
    await unlockTxnRail(page);
    const txnItems = page.locator(".txn-item");
    await expect(txnItems.first()).toBeVisible({ timeout: 15_000 });
    const input = page.getByPlaceholder("Nhập tin nhắn...");
    await input.fill("Cho mình xem giao dịch gần đây nhất với.");
    await input.press("Enter");
    await completeOtpIfPrompted(page, 40_000);
    await expect(page.locator(".bubble-bot").last()).toBeVisible({ timeout: 30_000 });

    // Giờ mới gửi câu chào — lịch sử hội thoại đã có ToolMessage thật, đúng
    // ca giao thoa với vá A của GĐ1 (rap_nguon_o3 gom lịch sử cho đường nhẹ).
    const text = await guiCauChaoVaKiemTraBubble(page, "cảm ơn bạn nhé");
    expect(text).not.toBe("");
  });

  // (c) CỐ Ý KHÔNG VIẾT — không dựng được "ngay sau một lượt fallback lỗi"
  // bằng đường sản phẩm thật qua UI: không có cơ chế nào trong helpers/
  // actors.ts hay route nào của app cho phép ép provider trả lỗi từ phía
  // trình duyệt (route.abort() mô phỏng MẤT MẠNG phía client — một lớp
  // KHÁC hẳn RateLimitError/APIError phía server, đã dùng ở
  // accessibility.spec.ts::UX-05 cho đúng mục đích của nó, không tái dùng
  // nhầm ở đây). Ép lỗi provider thật đòi đốt gần hết TPM dùng chung —
  // đúng thứ CLAUDE.md/STATE.md cấm làm trên ngăn xếp demo. Ca (c) do vậy
  // ĐƯỢC PHỦ Ở TẦNG TRONG: xem
  // tests/test_api/test_gd2_tool_calls_khong_null.py::test_trong_fallback_nha_cung_cap_tool_calls_la_mang
  // và test_bien_fallback_nha_cung_cap_tool_calls_la_mang (monkeypatch
  // được, không cần đốt TPM thật). Ghi ở đây để không ai đọc nhầm thành bỏ
  // sót — đây là quyết định có khai, đúng Luật P.
});
