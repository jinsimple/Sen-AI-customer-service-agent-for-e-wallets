import { defineConfig, devices } from "@playwright/test";

// TẠM THỜI, KHÔNG COMMIT — trỏ vào ngăn fin05-qa-stripe (đo axe-core
// before/after đợt vá bảng màu Stripe + tách login 26/08, port riêng qua
// docker-compose.qa-stripe.override.yml để không đụng fin05-sach/fin05-dot-otp).
export default defineConfig({
  testDir: "./e2e",
  testIgnore: /live-chat\.spec\.ts/,
  fullyParallel: false,
  workers: 1,
  timeout: 45_000,
  retries: 0,
  reporter: "list",
  use: {
    baseURL: "https://localhost:59443",
    ignoreHTTPSErrors: true,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
