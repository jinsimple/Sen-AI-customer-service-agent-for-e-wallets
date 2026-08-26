"use client";

import { useLoginForm } from "@/lib/useLoginForm";
import EnvBadge from "@/components/EnvBadge";

// Cổng NỘI BỘ — CSKH · sếp phê duyệt · đối tác ví. Quyết định 26/08: tách
// TRANG khỏi /login (khách hàng), KHÔNG tách CƠ CHẾ — dùng chung
// lib/useLoginForm.ts, vai trò vẫn lấy từ RESPONSE server qua phone, không
// có ô chọn vai nào ở đây. Trang này CỐ Ý không nối từ landing page/`/login`
// — không phải bảo mật thật (đoán được URL vẫn vào), chỉ bớt một lời mời cho
// người lạ. Giọng: công cụ, gọn — khác hẳn tông "mời gọi" của /login.
const DEMO_PASSWORD = "Demo@123";
const STAFF_ACCOUNTS: { label: string; phone: string }[] = [
  { label: "Nhân viên CSKH", phone: "0353000201" },
  { label: "Sếp phê duyệt", phone: "0905000205" },
  { label: "Đối tác ví (Chính sách)", phone: "0900000001" },
];

export default function LoginNoiBoPage() {
  const { phone, setPhone, password, setPassword, error, loading, doLogin, handleSubmit } = useLoginForm("internal");

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

          <div className="note" style={{ marginTop: 16 }}>
            <b>Demo:</b> 3 tài khoản bên dưới dùng chung mật khẩu <span className="mono">{DEMO_PASSWORD}</span>.
          </div>

          <div className="field" style={{ marginTop: 20 }}>
            <label>Đăng nhập nhanh (demo)</label>
            <div className="flex gap-sm wrap" style={{ marginTop: 7 }}>
              {STAFF_ACCOUNTS.map((acc) => (
                <button
                  key={acc.phone}
                  type="button"
                  className="btn btn-outline btn-sm"
                  disabled={loading}
                  onClick={() => void doLogin(acc.phone, DEMO_PASSWORD)}
                >
                  {acc.label} — {acc.phone}
                </button>
              ))}
            </div>
          </div>
        </form>
      </div>
    </main>
  );
}
