import "@testing-library/jest-dom/vitest";

// format.ts::formatDateTime dùng toLocaleString(...) KHÔNG truyền timeZone
// — đúng ý (trình duyệt thật của người dùng VN tự có local timezone
// UTC+7, không cần ép cứng trong code sản phẩm). Nhưng test chạy trong
// Node (Vitest/CI) sẽ dùng timezone CỦA MÁY CHẠY TEST, không phải UTC+7 cố
// định — GitHub Actions runner mặc định UTC, khác máy dev (UTC+7), làm
// test format ngày giờ pass ở máy dev nhưng fail trên CI. Ghim TZ cố định
// ở đây để test xác định, không phụ thuộc máy chạy.
process.env.TZ = "Asia/Ho_Chi_Minh";

// jsdom KHÔNG implement Element.scrollTo (giới hạn đã biết của jsdom, không
// phải bug component) — nhiều component chat tự cuộn xuống cuối khi có tin
// nhắn mới (ChatClient.tsx, LiveChatPanel.tsx) sẽ throw "not a function"
// khi test render trong jsdom nếu không polyfill no-op này.
if (typeof Element !== "undefined" && !Element.prototype.scrollTo) {
  Element.prototype.scrollTo = () => {};
}
