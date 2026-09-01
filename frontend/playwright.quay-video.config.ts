import { defineConfig, devices } from "@playwright/test";

// ---------------------------------------------------------------------------
// CONFIG QUAY VIDEO TRÌNH SẢN PHẨM — 180 giây, 6 cảnh.
//
// 🔴 TỆP NÀY DO **PO** VIẾT, KHÔNG PHẢI tech-lead.
//    `frontend/` là vùng ghi của `tech-lead` theo CLAUDE.md §4. PO thật đã cấp
//    quyền mở rộng TẠM THỜI cho đúng việc quay này (28/08), vì Coder đang chờ
//    xác nhận ở tab của họ và QA/QC đã từ chối P5 (lệch vai đo/kiểm).
//    Khai ra để nó KHÔNG thành tiền lệ im lặng. Việc kế tiếp chạm `frontend/`
//    phải quay về đúng vai.
//
// KHÔNG COMMIT tệp này cùng mật khẩu. Mật khẩu đọc từ biến môi trường.
//
// Ngăn quay: fin05-dot-otp — https://localhost:48443
// 🔴 PHẢI là `localhost`, TUYỆT ĐỐI không `127.0.0.1`: chứng chỉ TLS cấp cho
//    TÊN; gọi bằng IP làm TLS gãy và trả lỗi trông y hệt "ngăn đã chết".
//    Lỗi này từng tốn của đội nhiều giờ (STATE §0 bàn giao 25/08).
// ---------------------------------------------------------------------------

export default defineConfig({
  testDir: "./e2e",
  testMatch: /quay-video-lien-mach\.spec\.ts/,
  fullyParallel: false,
  workers: 1,
  retries: 0,
  // Cảnh dài nhất 48 giây + thời gian dựng trang. Để rộng tay.
  timeout: 180_000,
  reporter: "list",
  outputDir: "./test-results/quay-video",
  use: {
    baseURL: "https://localhost:48443",
    ignoreHTTPSErrors: true,
    // Khung 720p: đủ nét cho đối tác xem, đủ nhẹ để ffmpeg ghép nhanh.
    viewport: { width: 1280, height: 720 },
    video: { mode: "on", size: { width: 1280, height: 720 } },
    // KHÔNG chụp ảnh/trace — chỉ cần video, đừng sinh rác vào outputDir.
    screenshot: "off",
    trace: "off",
    locale: "vi-VN",
    timezoneId: "Asia/Ho_Chi_Minh",
  },
  projects: [{ name: "chromium", use: { ...devices["Desktop Chrome"] } }],
});
