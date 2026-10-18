import { defineConfig, devices } from "@playwright/test";

// TẠM THỜI, KHÔNG COMMIT — bản livechat.config.ts trỏ vào fin05-qa-stripe
// (https://localhost:59443) thay vì https://localhost mặc định (đang bị
// stack khác giữ cổng 443/80). Dùng để chạy live-chat.spec.ts (1/9 tệp e2e
// vừa retrofit loginPath, chưa ai chạy thử) đúng ngăn qa-stripe cùng 8 tệp
// còn lại — server đã chạy sẵn trong Docker, không để Playwright tự spawn.
export default defineConfig({
  testDir: "./e2e",
  testMatch: /live-chat\.spec\.ts/,
  fullyParallel: false,
  timeout: 90_000,
  retries: 0,
  reporter: "list",
  use: {
    // Portfolio edition: the UI follows Accept-Language when no `lang` cookie is set. The suites
    // assert Vietnamese copy, so pin the browser locale.
    locale: "vi-VN",
    baseURL: "https://localhost:59443",
    ignoreHTTPSErrors: true,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
