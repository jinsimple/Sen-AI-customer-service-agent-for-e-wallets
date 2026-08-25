import { test } from "@playwright/test";
import AxeBuilder from "@axe-core/playwright";
import { DEMO_PASSWORD } from "./helpers/actors";

// TẠM THỜI, chẩn đoán — số axe-core color-contrast TRƯỚC khi Coder vá bộ
// màu (PO/Lead 25/08 yêu cầu, tách khỏi cổng chính thức accessibility.spec.ts
// vì cổng đó CHỈ lọc serious/critical, ở đây in ĐỦ mọi impact + chi tiết
// selector để đối chiếu trước/sau).
const PHONE = "0974000145";

async function login(page: import("@playwright/test").Page) {
  await page.goto("/login");
  await page.getByPlaceholder("09xx xxx xxx").fill(PHONE);
  await page.getByPlaceholder("••••••••").fill(DEMO_PASSWORD);
  await page.getByRole("button", { name: "Đăng nhập" }).click();
  await page.waitForURL("**/chat");
}

test("chẩn đoán: TOÀN BỘ vi phạm color-contrast, mọi impact, /login (chế độ sáng)", async ({ page }) => {
  await page.goto("/login");
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  const contrast = results.violations.filter((v) => v.id === "color-contrast");
  console.log(`>>> /login color-contrast: ${contrast.length} rule-violation(s)`);
  for (const v of contrast) {
    console.log(`    impact=${v.impact} nodes=${v.nodes.length}`);
    for (const n of v.nodes) console.log(`      - ${n.target.join(" ")} :: ${n.failureSummary?.slice(0, 200)}`);
  }
  console.log(`>>> /login TẤT CẢ rule vi phạm (mọi impact): ${results.violations.map((v) => `${v.id}[${v.impact}]x${v.nodes.length}`).join(", ") || "(không có)"}`);
});

test("chẩn đoán: TOÀN BỘ vi phạm color-contrast, mọi impact, /chat (chế độ sáng)", async ({ page }) => {
  await login(page);
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  const contrast = results.violations.filter((v) => v.id === "color-contrast");
  console.log(`>>> /chat color-contrast: ${contrast.length} rule-violation(s)`);
  for (const v of contrast) {
    console.log(`    impact=${v.impact} nodes=${v.nodes.length}`);
    for (const n of v.nodes) console.log(`      - ${n.target.join(" ")} :: ${n.failureSummary?.slice(0, 200)}`);
  }
  console.log(`>>> /chat TẤT CẢ rule vi phạm (mọi impact): ${results.violations.map((v) => `${v.id}[${v.impact}]x${v.nodes.length}`).join(", ") || "(không có)"}`);
});

test("chẩn đoán: color-contrast ở CHẾ ĐỘ TỐI /chat (emulateMedia dark) — lớp CHƯA từng được quét", async ({ page }) => {
  await page.emulateMedia({ colorScheme: "dark" });
  await login(page);
  const results = await new AxeBuilder({ page }).withTags(["wcag2a", "wcag2aa"]).analyze();
  const contrast = results.violations.filter((v) => v.id === "color-contrast");
  console.log(`>>> /chat (DARK) color-contrast: ${contrast.length} rule-violation(s)`);
  for (const v of contrast) {
    console.log(`    impact=${v.impact} nodes=${v.nodes.length}`);
    for (const n of v.nodes) console.log(`      - ${n.target.join(" ")} :: ${n.failureSummary?.slice(0, 200)}`);
  }
  console.log(`>>> /chat (DARK) TẤT CẢ rule vi phạm (mọi impact): ${results.violations.map((v) => `${v.id}[${v.impact}]x${v.nodes.length}`).join(", ") || "(không có)"}`);
});
