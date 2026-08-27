import Link from "next/link";

// Trang "chống lừa đảo" — Marketing (p-226-17) đang dựng nội dung. Route CỐ
// Ý luôn công khai (xem proxy.ts::ALWAYS_PUBLIC_PATHS) — không redirect theo
// bất kỳ chiều nào, kể cả với người ĐÃ đăng nhập, vì mục đích của trang là
// cho khách kiểm chứng NGAY LÚC họ đang nghi ngờ bị lừa (thường là lúc đang
// đăng nhập/đang dùng sản phẩm, không phải lúc rảnh rỗi đọc trang giới thiệu).
//
// 🔴 KHUNG SƯỜN TẠM — nội dung thật (thông điệp lõi, câu chữ) là việc của
// Marketing, không phải ux-ui tự viết. Đừng lấy placeholder này làm nội
// dung chính thức.
export default function ChoKhachHangPage() {
  return (
    <main style={{ maxWidth: 720, margin: "64px auto", padding: "0 20px" }}>
      <div className="card" style={{ padding: 36 }}>
        <h1 style={{ fontSize: "var(--fs-24)" }}>Dành cho khách hàng</h1>
        <p className="sub" style={{ marginTop: 8 }}>
          Nội dung trang này đang được đội Marketing hoàn thiện.
        </p>
        <p style={{ marginTop: 16, color: "var(--text-dim)" }}>
          Sen không bao giờ hỏi mật khẩu ví hay mã OTP giao dịch của bạn trong khi trò chuyện.
        </p>
        <Link href="/" className="btn btn-outline" style={{ marginTop: 24, display: "inline-flex" }}>
          Về trang chủ
        </Link>
      </div>
    </main>
  );
}
