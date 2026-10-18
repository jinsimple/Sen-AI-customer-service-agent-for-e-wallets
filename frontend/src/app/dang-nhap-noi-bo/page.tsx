"use client";

import { useLoginForm } from "@/lib/useLoginForm";
import EnvBadge from "@/components/EnvBadge";
import LanguageToggle from "@/components/LanguageToggle";
import { useI18n } from "@/lib/i18n/client";
import type { DictKey } from "@/lib/i18n/dict";

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
// 🔴 NGOẠI LỆ có chủ đích, hẹp, cho quyết định CẤM ở comment trên (26/08) —
// KHÔNG đảo quyết định đó. Cờ build-time `NEXT_PUBLIC_QUICK_LOGIN`, mặc định
// TẮT, cùng khuôn `OTP_DEMO_MODE`: Next.js thay `NEXT_PUBLIC_*` LÚC BUILD nên
// không đặt cờ = ba tài khoản dưới KHÔNG tồn tại trong bundle gửi trình
// duyệt, không phải chỉ ẩn UI. Dùng cho ĐÚNG một lần quay video demo 01/09,
// build riêng tag `quay-video`, KHÔNG đè `latest`. PO thật chốt qua Lead.
// PO thật đã đồng bộ CSDL `po-demo` 01/09 tối: cả ba tài khoản dưới dùng
// CHUNG một mật khẩu (của CSKH, có backup hash cũ, đảo ngược được) — chỉ
// khác số điện thoại. Không phải mặc định của toàn hệ thống, chỉ áp cho
// ngăn `po-demo` đêm quay video 01/09.
const MAT_KHAU_QUAY_VIDEO = "Demo@123";
const QUICK_LOGIN_ACCOUNTS: { label: DictKey; phone: string; password: string }[] = [
  { label: "role.cskh", phone: "0353000201", password: MAT_KHAU_QUAY_VIDEO },
  { label: "role.supervisor", phone: "0905000205", password: MAT_KHAU_QUAY_VIDEO },
  { label: "role.partner_admin", phone: "0900000001", password: MAT_KHAU_QUAY_VIDEO },
];

export default function LoginNoiBoPage() {
  const { phone, setPhone, password, setPassword, error, loading, doLogin, handleSubmit } = useLoginForm("internal");
  const { t } = useI18n();

  return (
    <main style={{ maxWidth: 420, margin: "80px auto", padding: "0 20px" }}>
      <div className="card" style={{ padding: 36 }}>
        <div style={{ marginBottom: 14, display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8 }}>
          <EnvBadge />
          <LanguageToggle />
        </div>
        <h3>{t("slogin.title")}</h3>
        <p className="sub">{t("slogin.sub")}</p>

        {process.env.NEXT_PUBLIC_QUICK_LOGIN === "true" && (
          <div style={{ display: "flex", gap: 8, marginBottom: 16, flexWrap: "wrap" }}>
            {QUICK_LOGIN_ACCOUNTS.map((acc) => (
              <button
                key={acc.phone}
                type="button"
                className="btn btn-primary"
                style={{ flex: "1 1 auto" }}
                disabled={loading}
                onClick={() => doLogin(acc.phone, acc.password)}
              >
                {t(acc.label)}
              </button>
            ))}
          </div>
        )}

        <form onSubmit={handleSubmit}>
          <div className={`field${error ? " field-error" : ""}`}>
            <label>{t("login.phone")}</label>
            <input
              type="tel"
              placeholder="09xx xxx xxx"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
              required
            />
          </div>

          <div className={`field${error ? " field-error" : ""}`}>
            <label>{t("login.password")}</label>
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
            {loading ? t("login.submitting") : t("login.submit")}
          </button>
        </form>
      </div>
    </main>
  );
}
