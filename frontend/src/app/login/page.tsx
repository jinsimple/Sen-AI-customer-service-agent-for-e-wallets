"use client";

import { useLoginForm } from "@/lib/useLoginForm";
import EnvBadge from "@/components/EnvBadge";

// Đăng nhập bằng mật khẩu thật (quyết định 2026-08-12, thay luồng phone+role
// chọn tay trước đó) — vai trò giờ lấy từ RESPONSE của server (user tìm
// được qua phone trong DB), không còn do người dùng tự chọn trước khi gửi.
//
// 26/08 — tách trang: đây là cổng CÔNG KHAI cho khách hàng (nối từ trang
// quảng cáo). Cổng nội bộ (CSKH/sếp/đối tác ví) ở /dang-nhap-noi-bo, KHÔNG
// nối từ đây — xem lib/useLoginForm.ts để biết cơ chế xác thực dùng chung.
const DEMO_PASSWORD = "Demo@123";
// Demo 15/08: trỏ USR-0145 (0974000145) chứ không phải USR-0001 — đây là
// user có dữ liệu khớp kịch bản demo.
const CUSTOMER_PHONE = "0974000145";

export default function LoginPage() {
  const { phone, setPhone, password, setPassword, error, loading, doLogin, handleSubmit } = useLoginForm();

  return (
    <main style={{ maxWidth: 1000, margin: "48px auto", padding: "0 20px" }}>
      <div className="login-shell">
        <div className="login-brand">
          <div>
            <div className="mark">S</div>
            <h2>Sen — Trợ lý CSKH ví điện tử</h2>
            <p>Điều tra khiếu nại giao dịch bằng AI, quyết định cuối cùng luôn thuộc về con người.</p>
          </div>
          <div className="trustlist">
            <div>
              <svg className="icon" viewBox="0 0 24 24">
                <path d="M12 2l8 4v6c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-4z" />
              </svg>
              <span>Dữ liệu giao dịch không rời khỏi hạ tầng ví — không qua bên thứ ba lưu trữ.</span>
            </div>
            <div>
              <svg className="icon" viewBox="0 0 24 24">
                <rect x="4" y="11" width="16" height="9" rx="2" />
                <path d="M8 11V7a4 4 0 018 0v4" />
              </svg>
              <span>Không màn hình nào hỏi mật khẩu hoặc OTP giao dịch thật của bạn.</span>
            </div>
            <div>
              <svg className="icon" viewBox="0 0 24 24">
                <path d="M4 6h16M4 12h16M4 18h10" />
              </svg>
              <span>Mọi phê duyệt hoàn tiền được ghi log — truy vết được ai, khi nào, căn cứ gì.</span>
            </div>
          </div>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          {/* Nhãn môi trường ngay tại màn đăng nhập — đúng thời điểm cần biết
              mình sắp đăng nhập vào hệ thống/database nào. Xem ADR-009. */}
          <div style={{ marginBottom: 14 }}>
            <EnvBadge />
          </div>
          <h3>Chào bạn 👋</h3>
          <p className="sub">Đăng nhập để tiếp tục với trợ lý AI của ví — vài giây thôi.</p>

          <div className={`field${error ? " field-error" : ""}`} style={{ marginTop: 0 }}>
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
            <svg className="icon" viewBox="0 0 24 24">
              <path d="M5 12h14M13 6l6 6-6 6" />
            </svg>
          </button>

          <div className="note" style={{ marginTop: 16 }}>
            <svg className="icon" viewBox="0 0 24 24">
              <path d="M12 2l8 4v6c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-4z" />
            </svg>
            <div>
              <b>Demo:</b> tài khoản khách hàng bên dưới dùng mật khẩu{" "}
              <span className="mono">{DEMO_PASSWORD}</span>. Là nhân viên CSKH, sếp phê duyệt hay đối tác ví?
              Đăng nhập tại <span className="mono">/dang-nhap-noi-bo</span>.
            </div>
          </div>

          <div className="field" style={{ marginTop: 20 }}>
            <label>Đăng nhập nhanh (demo)</label>
            <div className="flex gap-sm wrap" style={{ marginTop: 7 }}>
              <button
                type="button"
                className="btn btn-outline btn-sm"
                disabled={loading}
                onClick={() => void doLogin(CUSTOMER_PHONE, DEMO_PASSWORD)}
              >
                Khách hàng — {CUSTOMER_PHONE}
              </button>
            </div>
          </div>
        </form>
      </div>
    </main>
  );
}
