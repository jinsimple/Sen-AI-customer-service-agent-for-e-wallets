import { defineConfig, devices } from "@playwright/test";

// TẠM THỜI, KHÔNG COMMIT — chỉ dùng cho buổi tốn phí 25/08 (⑥/⑬-B1-C1) để
// trỏ vào ngăn fin05-dot-otp (https://localhost:48443) thay vì
// http://localhost:3000 mặc định. Server ĐÃ chạy sẵn trong Docker — không
// để Playwright tự spawn `npm run dev`.
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
    baseURL: "https://localhost:48443",
    ignoreHTTPSErrors: true,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
