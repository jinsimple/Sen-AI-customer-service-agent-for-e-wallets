import { defineConfig } from "vitest/config";
import react from "@vitejs/plugin-react";
import path from "node:path";

// FIN05-StressTest-Plan-v4 F4-01 — TÁCH HẲN khỏi Playwright (e2e/*.spec.ts,
// playwright.config.ts/playwright.livechat.config.ts): logic React thuần
// (helper functions, state reducer, custom hook) không cần dựng cả trình
// duyệt thật — trước đây dự án CHỈ có Playwright cho MỌI thứ (gap doc
// FIN05-QA-Coverage-Gaps.md §5 đã chỉ ra: "toàn Playwright hoặc không gì
// cả"), Vitest rẻ/nhanh hơn nhiều lần cho lớp test này.
export default defineConfig({
  plugins: [react()],
  test: {
    environment: "jsdom",
    globals: true,
    setupFiles: ["./vitest.setup.ts"],
    include: ["src/**/*.test.{ts,tsx}"],
    exclude: ["e2e/**", "node_modules/**"],
  },
  resolve: {
    alias: {
      "@": path.resolve(__dirname, "./src"),
    },
  },
});
