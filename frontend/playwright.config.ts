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
  // live-chat.spec.ts CẦN mạng Docker thật (Caddy → backend, xem
  // playwright.livechat.config.ts) — cổng 3000 trần (next dev/start) ở đây
  // KHÔNG proxy được /ws/live-chat, chạy nhầm ở config này sẽ luôn fail.
  // Loại trừ tường minh thay vì để 2 config vô tình đụng cùng 1 file test.
  testIgnore: /live-chat\.spec\.ts/,
  fullyParallel: false, // dùng chung 1 user/OTP state giữa các case trong 1 file — tránh đụng độ AuthSession
  // ĐÍNH CHÍNH ghi chú cũ ở đây (từng nói "chưa xác định chắc rễ, không phải
  // nghẽn khoá SQLite, đã verify bằng concurrent-load test") — SAI, xác nhận
  // lại 2026-08-12 bằng cách đọc TRỰC TIẾP traceback backend thật:
  // `sqlite3.OperationalError: database is locked` xảy ra 20 lần thật khi
  // chạy nhiều file spec CÙNG LÚC. Gốc rễ ĐÚNG: `fullyParallel: false` CHỈ
  // serialize test TRONG 1 file — Playwright vẫn tự chạy NHIỀU FILE spec
  // khác nhau ở NHIỀU WORKER SONG SONG theo mặc định (không có `workers: 1`
  // tường minh). approve.spec.ts/ticket-detail.spec.ts (và các file khác)
  // dùng CHUNG 1 CUSTOMER_PHONE hardcode — 2 worker cùng gọi
  // get_customer_history cho CÙNG user gần như đồng thời (đo được lệch
  // nhau ~4ms), tranh chấp ghi cùng lúc vào 1 file SQLite. Đã vá 2 lớp:
  // (1) `PRAGMA journal_mode=WAL` + `busy_timeout` (src/db/session.py) —
  // giảm lỗi khoá ~90% (20 -> 2 lần trong 1 lần chạy thử), (2) `workers: 1`
  // dưới đây — loại hẳn nguyên nhân gốc (chạy file spec song song), quan
  // trọng hơn cả lớp (1) vì (1) chỉ giảm nhẹ tần suất, không loại bỏ hẳn.
  workers: 1,
  // 45s (mặc định Playwright là 30s) — phát hiện thật lúc chạy full suite AUTH-*
  // nhiều lần liên tiếp: rail "Giao dịch gần đây" (getCustomerHistory lúc
  // mount) thi thoảng lâu hẳn dưới tải tuần tự nhiều test dù gọi trực tiếp
  // luôn nhanh (~30-60ms, đã verify bằng curl) — nới timeout mặc định thay
  // vì để mỗi test tự chỉnh riêng lẻ.
  timeout: 45_000,
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
