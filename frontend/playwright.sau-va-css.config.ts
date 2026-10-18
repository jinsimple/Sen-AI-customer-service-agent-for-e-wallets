import { defineConfig, devices } from "@playwright/test";

// TẠM THỜI, KHÔNG COMMIT — trỏ vào ngăn fin05-sach (https://localhost, port
// mặc định 443) để đo axe-core SAU khi Coder vá bộ màu/phông (25/08). Song
// song với playwright.buoi-tot-phi.config.ts (fin05-dot-otp, giữ nguyên làm
// mốc TRƯỚC vá) — hai ngăn khác nhau, không đụng nhau.
export default defineConfig({
  testDir: "./e2e",
  testIgnore: /live-chat\.spec\.ts/,
  fullyParallel: false,
  workers: 1,
  timeout: 45_000,
  retries: 0,
  reporter: "list",
  use: {
    // Portfolio edition: the UI follows Accept-Language when no `lang` cookie is set. The suites
    // assert Vietnamese copy, so pin the browser locale.
    locale: "vi-VN",
    baseURL: "https://localhost",
    ignoreHTTPSErrors: true,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
