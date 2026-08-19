import { test, expect } from "@playwright/test";
import { loginAs, unlockTxnRail } from "./helpers/actors";

/**
 * KHẨN — GĐ3, PO thật chuẩn bị tự vào test sau khi Coder bật trần chi tiêu.
 * Smoke tối giản theo lệnh Lead: chào nhẹ + 1 câu nặng có tool, KHÔNG phủ
 * rộng. Tránh bẫy đã gặp ở chao-hoi-duong-nhe.spec.ts::(b) — KHÔNG gọi
 * completeOtpIfPrompted() lần hai sau lượt nặng (khối OTP cũ còn trong
 * transcript, đã disabled, gọi lại sẽ treo tới timeout — lỗi ở helper,
 * không phải sản phẩm, xem báo cáo Lead trước đó cùng ngày).
 */
const CUSTOMER_PHONE = "0974000145";

test("KHẨN GĐ3 — chào nhẹ + 1 câu nặng có tool, UI thật", async ({ page }) => {
  test.setTimeout(90_000);
  await loginAs(page, CUSTOMER_PHONE, "/chat");

  // Bước 2 — chào nhẹ.
  const input = page.getByPlaceholder("Nhập tin nhắn...");
  const soBubbleTruoc = await page.locator(".bubble-bot").count();
  await input.fill("chào bạn");
  await input.press("Enter");
  const bubbleChao = page.locator(".bubble-bot").nth(soBubbleTruoc);
  await expect(bubbleChao).toBeVisible({ timeout: 20_000 });
  const textChao = (await bubbleChao.textContent())?.trim() ?? "";
  expect(textChao.length, "Bubble chào rỗng").toBeGreaterThan(0);

  // Bước 3 — một câu nặng có tool (mở rail trước để không bị OTP chặn giữa chừng).
  await unlockTxnRail(page);
  await page.locator(".txn-item").first().waitFor({ state: "visible", timeout: 20_000 });

  const soBubbleTruocNang = await page.locator(".bubble-bot").count();
  await input.fill("Cho mình xem giao dịch gần đây nhất với.");
  await input.press("Enter");
  const bubbleNang = page.locator(".bubble-bot").nth(soBubbleTruocNang);
  await expect(bubbleNang).toBeVisible({ timeout: 40_000 });
  const textNang = (await bubbleNang.textContent())?.trim() ?? "";
  expect(textNang.length, "Bubble lượt nặng rỗng").toBeGreaterThan(0);
  console.log("[KHẨN] reply lượt nặng:", textNang.slice(0, 200));
});
