import { test, expect } from "@playwright/test";
import { DEMO_PASSWORD } from "./helpers/actors";

/**
 * DISC-002 (FIN05_QA_TestCases.jsonl, EU AI Act Article 50) — phải có tín
 * hiệu nhận biết AI ngay từ đầu phiên chat, không chỉ khi bị hỏi (DISC-001,
 * xem eval/llm_judge_set.jsonl UXQA-003). Deterministic string assert —
 * không cần LLM, câu chào là literal string cố định trong ChatClient.tsx.
 */
const PHONE = "0974000145";

test("DISC-002: câu chào đầu phiên nêu rõ đây là trợ lý AI", async ({ page }) => {
  await page.goto("/login");
  await page.getByPlaceholder("09xx xxx xxx").fill(PHONE);
  await page.getByPlaceholder("••••••••").fill(DEMO_PASSWORD);
  await page.getByRole("button", { name: "Đăng nhập" }).click();
  await page.waitForURL("**/chat");

  // Tin nhắn chào đầu tiên (bot) — không phải chỉ tiêu đề trang/nhãn cố định
  // bên ngoài khung chat (2 chỗ đó vốn đã có sẵn "AI" nhưng không đủ theo
  // đúng nghĩa "banner/câu mở đầu ngay trong hội thoại" mà EU AI Act Art.50
  // yêu cầu — phát hiện thật lúc đối chiếu, xem FIN05-QA-Test-Report-corrected.md).
  const firstBotBubble = page.locator(".bubble-bot").first();
  await expect(firstBotBubble).toContainText("AI");
});
