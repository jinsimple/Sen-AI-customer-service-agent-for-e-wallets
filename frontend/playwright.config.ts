import { defineConfig, devices } from "@playwright/test";

// Nhóm identity/AUTH-* (FIN05_QA_TestCases.jsonl) — cần OTP THẬT ở backend
// (src/auth.py::require_otp_verified) để test có ý nghĩa, không chỉ mô phỏng
// UI. `reuseExistingServer: true` LUÔN LUÔN (không chỉ dev cục bộ) — CI
// (.github/workflows/ci.yml, job e2e-playwright-nightly) tự dựng backend +
// build/start frontend production TRƯỚC khi gọi playwright test, đúng
// khuyến nghị Next.js "test against production code" — nếu để mặc định
// `!process.env.CI`, Playwright sẽ tự spawn thêm `npm run dev` đè lên cổng
// 3000 đã có sẵn server production, xung đột cổng. `command` bên dưới chỉ là
// fallback tiện lợi khi chạy tay mà quên bật server trước.
export default defineConfig({
  testDir: "./e2e",
  fullyParallel: false, // dùng chung 1 user/OTP state giữa các case trong 1 file — tránh đụng độ AuthSession
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["html", { open: "never" }]] : "list",
  use: {
    baseURL: "http://localhost:3000",
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
  webServer: {
    command: "npm run dev",
    url: "http://localhost:3000",
    reuseExistingServer: true,
    timeout: 60_000,
  },
});
