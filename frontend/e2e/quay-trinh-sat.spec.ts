import { test, type Page } from "@playwright/test";

// TRINH SÁT — không quay, chỉ in ra cấu trúc màn hình để dựng cảnh đúng.
// Xoá sau khi quay xong. PO viết, xem đầu playwright.quay-video.config.ts.

const MK = process.env.STAFF_PW!;
const CSKH = "0353000201";
const SEP = "0905000205";
const KHACH = "0974000145";

async function dangNhap(page: Page, phone: string, mk: string) {
  const r = await page.request.post("/api/session", { data: { phone, password: mk } });
  return r.status();
}

async function soi(page: Page, duong: string, nhan: string) {
  await page.goto(duong);
  await page.waitForLoadState("networkidle").catch(() => {});
  await page.waitForTimeout(1200);
  const url = page.url();
  const tieuDe = await page.locator("h1, h2, h3").allInnerTexts().catch(() => []);
  const nut = await page.getByRole("button").allInnerTexts().catch(() => []);
  const cao = await page.evaluate(() => document.body.scrollHeight);
  console.log(`\n### ${nhan}  →  ${url}`);
  console.log(`    cao=${cao}px`);
  console.log(`    tiêu đề: ${tieuDe.slice(0, 8).join(" | ").replace(/\n/g, " ")}`);
  console.log(`    nút: ${nut.slice(0, 10).join(" | ").replace(/\n/g, " ")}`);
}

test("trinh-sat", async ({ page }) => {
  console.log("=== CSKH ===", await dangNhap(page, CSKH, MK));
  await soi(page, "/tickets", "Hàng chờ (CSKH)");
  await soi(page, "/dashboard", "Dashboard");
  await soi(page, "/report", "Báo cáo vận hành");
  await soi(page, "/policy-lookup", "Tra cứu chính sách");

  console.log("\n=== SẾP ===", await dangNhap(page, SEP, MK));
  await soi(page, "/approve", "Hàng đợi duyệt (sếp)");

  console.log("\n=== KHÁCH ===", await dangNhap(page, KHACH, "Demo@123"));
  await soi(page, "/chat", "Chat khách");
});
