"use client";

import { useLoginForm } from "@/lib/useLoginForm";
import EnvBadge from "@/components/EnvBadge";
import LanguageToggle from "@/components/LanguageToggle";
import { useI18n } from "@/lib/i18n/client";

// Log in with a real password (decision 2026-08-12, replacing the earlier phone+manual-role-pick
// flow) — the role now comes from the server's RESPONSE (the user found by phone in the DB), no
// longer chosen by the user before submitting.
//
// Aug 26 — split the page: this is the PUBLIC gate for customers (linked from the marketing page).
// The internal gate (support/supervisor/wallet partner) is at /dang-nhap-noi-bo, NOT linked from
// here — see lib/useLoginForm.ts for the shared authentication mechanism.
const DEMO_PASSWORD = "Demo@123";
// Demo, Aug 15: points at USR-0145 (0974000145) rather than USR-0001 — this user has data matching
// the demo script.
const CUSTOMER_PHONE = "0974000145";

export default function LoginPage() {
  const { phone, setPhone, password, setPassword, error, loading, doLogin, handleSubmit } = useLoginForm("customer");
  const { t } = useI18n();

  return (
    <main style={{ maxWidth: 1000, margin: "48px auto", padding: "0 20px" }}>
      <div className="login-shell">
        <div className="login-brand">
          <div>
            <div className="mark">S</div>
            <h2>{t("app.brand")}</h2>
            <p>{t("clogin.tagline")}</p>
          </div>
          <div className="trustlist">
            <div>
              <svg className="icon" viewBox="0 0 24 24">
                <path d="M12 2l8 4v6c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-4z" />
              </svg>
              {/* 27/08 vòng 3 — Marketing (p-226-17) chỉ ra bản vòng 2 ("kết
                  quả tra cứu được che... trước khi đưa vào xử lý") ĐÚNG
                  NHƯNG dẫn người đọc TRÊN TRANG ĐĂNG NHẬP tới kết luận sai:
                  "dữ liệu CỦA TÔI được che" — trong khi thứ được che là dữ
                  liệu NGƯỜI KHÁC trong kết quả tra, và câu khách tự gõ vẫn đi
                  nguyên văn tới model (đúng như chân khung chat tự khai).
                  Câu mới nói đúng phạm vi thật (bên thứ ba, trước khi HIỂN
                  THỊ — kiểm được bằng mắt: "T. H. Ngân 058***0135" trên ảnh
                  sản phẩm), khớp nguyên văn câu đã duyệt trên landing. Copy
                  nguyên văn marketing, không tự viết lại. */}
              <span>{t("clogin.trustMasking")}</span>
            </div>
            <div>
              <svg className="icon" viewBox="0 0 24 24">
                <rect x="4" y="11" width="16" height="9" rx="2" />
                <path d="M8 11V7a4 4 0 018 0v4" />
              </svg>
              {/* 27/08 vòng 2 — Marketing: "không màn hình NÀO" tự mâu thuẫn
                  với ô "Mật khẩu" ngay bên dưới trên chính trang này, nên
                  từng thêm vế mở đầu "Trong khi trò chuyện,". 27/08 vòng 3 —
                  Marketing TỰ RÚT LẠI: câu chuẩn chống lừa đảo phải giống hệt
                  ở MỌI bề mặt (login/chat/cho-khach-hang) để khách NHẬN RA
                  được — thêm vế mở đầu phá mất tính nhận-ra-được đó. Mâu
                  thuẫn với ô "Mật khẩu" tự tan vì câu chuẩn nói "mật khẩu VÍ",
                  đã khác ô đăng nhập ứng dụng. Câu chuẩn trần, nguyên văn
                  marketing, giống hệt cả ba nơi. */}
              <span>{t("common.neverAsk")}</span>
            </div>
            <div>
              <svg className="icon" viewBox="0 0 24 24">
                <path d="M4 6h16M4 12h16M4 18h10" />
              </svg>
              <span>{t("clogin.trustAudit")}</span>
            </div>
          </div>
        </div>

        <form className="login-form" onSubmit={handleSubmit}>
          {/* Nhãn môi trường ngay tại màn đăng nhập — đúng thời điểm cần biết
              mình sắp đăng nhập vào hệ thống/database nào. Xem ADR-009. */}
          <div style={{ marginBottom: 14, display: "flex", justifyContent: "space-between", alignItems: "center", gap: 8 }}>
            <EnvBadge />
            <LanguageToggle />
          </div>
          <h3>{t("clogin.hello")}</h3>
          <p className="sub">{t("clogin.sub")}</p>

          <div className={`field${error ? " field-error" : ""}`} style={{ marginTop: 0 }}>
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
            <svg className="icon" viewBox="0 0 24 24">
              <path d="M5 12h14M13 6l6 6-6 6" />
            </svg>
          </button>

          <div className="note" style={{ marginTop: 16 }}>
            <svg className="icon" viewBox="0 0 24 24">
              <path d="M12 2l8 4v6c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-4z" />
            </svg>
            <div>
              <b>Demo:</b> {t("clogin.demoNote")}{" "}
              <span className="mono">{DEMO_PASSWORD}</span>.
            </div>
          </div>

          <div className="field" style={{ marginTop: 20 }}>
            <label>{t("clogin.quickLogin")}</label>
            <div className="flex gap-sm wrap" style={{ marginTop: 7 }}>
              <button
                type="button"
                className="btn btn-outline btn-sm"
                disabled={loading}
                onClick={() => void doLogin(CUSTOMER_PHONE, DEMO_PASSWORD)}
              >
                {t("clogin.quickCustomer", { phone: CUSTOMER_PHONE })}
              </button>
            </div>
          </div>
        </form>
      </div>
    </main>
  );
}
