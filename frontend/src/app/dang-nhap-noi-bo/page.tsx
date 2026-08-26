"use client";

import { useLoginForm } from "@/lib/useLoginForm";
import EnvBadge from "@/components/EnvBadge";

// Cổng NỘI BỘ — CSKH · sếp phê duyệt · đối tác ví. Quyết định 26/08: tách
// TRANG khỏi /login (khách hàng), KHÔNG tách CƠ CHẾ — dùng chung
// lib/useLoginForm.ts, vai trò vẫn lấy từ RESPONSE server qua phone, không
// có ô chọn vai nào ở đây. Trang này CỐ Ý không nối từ landing page/`/login`
// — không phải bảo mật thật (đoán được URL vẫn vào), chỉ bớt một lời mời cho
// người lạ. Giọng: công cụ, gọn — khác hẳn tông "mời gọi" của /login.
//
// 🔴 [ĐO 26/08] KHÔNG đăng nhập nhanh, KHÔNG in mật khẩu demo, KHÔNG danh
// sách số điện thoại nhân viên — dù chỉ ở /login (khách) việc này an toàn
// (tài khoản khách sinh ra để phát cho người lạ), ở ĐÂY nó là rò rỉ thật:
// route này CÔNG KHAI (PUBLIC_PATHS) + số điện thoại sếp phê duyệt hiện sẵn
// + mật khẩu chung in thẳng ⟹ bất kỳ ai mở trang là đăng nhập được vai
// supervisor, duyệt được hoàn tiền. Ba quyết định RIÊNG LẺ đều hợp lý (trang
// đăng nhập phải công khai · nút nhanh tiện demo · mật khẩu chung tiện test)
// — cộng lại thành một cửa mở. Trang nội bộ phải trông như một ô đăng nhập
// trống, không kể gì về chính nó (không cả gợi ý "liên hệ quản trị" — gợi ý
// đó đã xác nhận "đây là cổng có tài khoản thật phía sau"). Nhân viên tự gõ
// số và mật khẩu của mình — họ biết, không cần trang nhắc.
export default function LoginNoiBoPage() {
  const { phone, setPhone, password, setPassword, error, loading, handleSubmit } = useLoginForm("internal");

  return (
    <main style={{ maxWidth: 420, margin: "80px auto", padding: "0 20px" }}>
      <div className="card" style={{ padding: 36 }}>
        <div style={{ marginBottom: 14 }}>
          <EnvBadge />
        </div>
        <h3>Đăng nhập nội bộ</h3>
        <p className="sub">Dành cho nhân viên CSKH, sếp phê duyệt và đối tác ví.</p>

        <form onSubmit={handleSubmit}>
          <div className={`field${error ? " field-error" : ""}`}>
            <label>Số điện thoại</label>
            <input
              type="tel"
              placeholder="09xx xxx xxx"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              required
            />
          </div>

          <div className={`field${error ? " field-error" : ""}`}>
            <label>Mật khẩu</label>
            <input
              type="password"
              placeholder="••••••••"
              value={password}
              onChange={(e) => setPassword(e.target.value)}
              required
            />
            {error && (
              <div className="error-text">
                <svg className="icon icon-sm" viewBox="0 0 24 24">
                  <circle cx="12" cy="12" r="10" />
                  <path d="M12 8v5M12 16h.01" />
                </svg>
                {error}
              </div>
            )}
          </div>

          <button className="btn btn-primary" style={{ width: "100%", justifyContent: "center", marginTop: 20 }} disabled={loading}>
            {loading ? "Đang đăng nhập…" : "Đăng nhập"}
          </button>
        </form>
      </div>
    </main>
  );
}
