"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { roleHome, type Role } from "@/lib/session";

const ROLE_OPTIONS: { value: Role; label: string }[] = [
  { value: "customer", label: "Khách hàng" },
  { value: "cskh", label: "Nhân viên CSKH" },
  { value: "supervisor", label: "Sếp phê duyệt" },
  { value: "partner_admin", label: "Đối tác ví (Chính sách)" },
];

export default function LoginPage() {
  const router = useRouter();
  const [role, setRole] = useState<Role>("customer");
  const [phone, setPhone] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    setError(null);
    setLoading(true);
    try {
      const res = await fetch("/api/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone: phone.trim(), role }),
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.detail ?? "Số điện thoại hoặc vai trò không khớp.");
        return;
      }
      router.push(roleHome(role));
      router.refresh();
    } catch {
      setError("Không kết nối được máy chủ — kiểm tra backend đã chạy chưa (make run).");
    } finally {
      setLoading(false);
    }
  }

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
          <h3>Đăng nhập</h3>
          <p className="sub">Chọn vai trò và nhập số điện thoại tài khoản demo của bạn.</p>

          <div className="field" style={{ marginTop: 0 }}>
            <label>Bạn là</label>
            <div className="flex gap-sm" style={{ marginTop: 7 }}>
              {ROLE_OPTIONS.map((opt) => (
                <span
                  key={opt.value}
                  className={`filter-chip${role === opt.value ? " active" : ""}`}
                  style={{ flex: 1, justifyContent: "center" }}
                  onClick={() => setRole(opt.value)}
                >
                  {opt.label}
                </span>
              ))}
            </div>
          </div>

          <div className={`field${error ? " field-error" : ""}`}>
            <label>Số điện thoại</label>
            <input
              type="tel"
              placeholder="09xx xxx xxx"
              value={phone}
              onChange={(e) => setPhone(e.target.value)}
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
              <b>Demo:</b> không có mật khẩu thật — dataset chỉ định danh theo số điện thoại + vai trò.
              Xem <span className="mono">data/generated/users.jsonl</span> để lấy số điện thoại mẫu theo từng vai trò.
            </div>
          </div>
        </form>
      </div>
    </main>
  );
}
