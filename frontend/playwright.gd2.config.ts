import { defineConfig, devices } from "@playwright/test";

// GĐ2 (2026-08-19) — CHUẨN MỚI PO thật: QA/QC test THỰC TẾ trên giao diện
// localhost sau mọi bản vá, ≥3 good case/tính năng trước khi trình PO.
//
// 🚫 BẪY ADR-009 (đã ghi trong docs/giao-viec/2026-08-19-gd2-envelope-null-va-e2e-ui.md
// mục 2-QA/QC): `playwright.config.ts` mặc định trỏ baseURL
// `http://localhost:3000` và có `webServer: { command: "npm run dev" }` —
// [ĐO] `curl http://localhost:3000/login` → connection refused (frontend
// container KHÔNG publish 3000 ra host), trong khi `curl -k
// https://localhost/login` → 200 qua Caddy. Dùng config mặc định sẽ khiến
// Playwright TỰ SPAWN một `next dev` mới đè lên, không phải test đúng ảnh
// Docker đang chạy — chính con bug GĐ2 (tool_calls:null vỡ UI) chỉ hiện qua
// ĐÚNG topology thật (trình duyệt → Caddy → BFF → backend), y hệt lý do
// playwright.livechat.config.ts tồn tại. File này dùng lại đúng khuôn đó
// cho phần còn lại của e2e/ (mọi spec TRỪ live-chat.spec.ts, đã có config
// riêng).
//
// KHÔNG có `webServer` — cố ý, cùng lý do livechat config: yêu cầu
// `docker compose -p fin05 up -d` chạy sẵn trước khi gọi
// `npx playwright test --config=playwright.gd2.config.ts`.
export default defineConfig({
  testDir: "./e2e",
  testIgnore: /live-chat\.spec\.ts/,
  fullyParallel: false,
  workers: 1, // cùng lý do playwright.config.ts: nhiều spec dùng chung 1 CUSTOMER_PHONE hardcode
  timeout: 45_000,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["html", { open: "never", outputFolder: "playwright-report-gd2" }]] : "list",
  use: {
    // Portfolio edition: the UI follows Accept-Language when no `lang` cookie is set. The suites
    // assert Vietnamese copy, so pin the browser locale.
    locale: "vi-VN",
    baseURL: "https://localhost",
    ignoreHTTPSErrors: true, // Caddy tự cấp chứng chỉ NỘI BỘ khi SITE_DOMAIN=localhost
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
