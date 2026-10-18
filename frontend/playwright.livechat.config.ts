import { defineConfig, devices } from "@playwright/test";

// FIN05-StressTest-Plan-v4 L4-01..L4-05 — live-chat cần MẠNG DOCKER THẬT
// (Caddy → backend, xem Caddyfile) để WebSocket `/ws/live-chat` route đúng
// — bug thật đã từng lọt tới người dùng (tin nhắn lặp, session mồ côi,
// dashboard không realtime) CHỈ lộ ra khi 2 kết nối WS thật cạnh tranh qua
// đúng topology này. `playwright.config.ts` (AUTH-*) chạy thẳng `next dev`/
// `next start` trên cổng 3000 KHÔNG qua Caddy — Next.js không tự proxy
// WebSocket upgrade sang backend, nên KHÔNG dùng chung config đó cho nhóm
// test này (đã verify: `/ws/live-chat` qua thẳng cổng 3000 không route được).
//
// KHÔNG có `webServer` tự động — đây LÀ điểm khác biệt cố ý: bug thật cần
// đúng 5 service (`docker compose up`), Playwright tự spawn `next dev` sẽ
// không tái hiện được. Yêu cầu `docker compose up -d` chạy sẵn trước khi
// gọi `npx playwright test --config=playwright.livechat.config.ts`.
export default defineConfig({
  testDir: "./e2e",
  testMatch: /live-chat\.spec\.ts/,
  fullyParallel: false,
  // 90s (khác 45s ở playwright.config.ts AUTH-*) — mỗi test ở đây có 2 actor
  // thật + ít nhất 1 lượt gọi OpenAI thật (agent phải tự quyết định gọi
  // request_human_handoff) + nhiều vòng WS round-trip tuần tự, tổng thời
  // gian thật cao hơn hẳn 1 luồng OTP đơn actor.
  timeout: 90_000,
  retries: process.env.CI ? 1 : 0,
  reporter: process.env.CI ? [["html", { open: "never", outputFolder: "playwright-report-livechat" }]] : "list",
  use: {
    // Portfolio edition: the UI follows Accept-Language when no `lang` cookie is set. The suites
    // assert Vietnamese copy, so pin the browser locale.
    locale: "vi-VN",
    baseURL: "https://localhost",
    // Caddy tự cấp chứng chỉ NỘI BỘ khi SITE_DOMAIN=localhost (mặc định
    // docker-compose.yml) — không phải Let's Encrypt thật, trình duyệt thật
    // sẽ cảnh báo, Playwright cần bỏ qua để test được trên máy dev/CI.
    ignoreHTTPSErrors: true,
    trace: "retain-on-failure",
    screenshot: "only-on-failure",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
