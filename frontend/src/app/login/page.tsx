"use client";

import { useState } from "react";
import { useRouter } from "next/navigation";
import { roleHome, type Role } from "@/lib/session";

// Đăng nhập bằng mật khẩu thật (quyết định 2026-08-12, thay luồng phone+role
// chọn tay trước đó) — vai trò giờ lấy từ RESPONSE của server (user tìm
// được qua phone trong DB), không còn do người dùng tự chọn trước khi gửi.
// 4 tài khoản demo dùng CHUNG 1 mật khẩu (scripts/gen_dataset.py::
// SHARED_TEST_PASSWORD) — hiện thẳng ở đây làm nút "đăng nhập nhanh" để
// tiện test tay, đúng tinh thần minh bạch demo đã có sẵn (OTP demo cũng
// hiện thẳng mã, không giấu).
const DEMO_PASSWORD = "Demo@123";
const QUICK_LOGIN_ACCOUNTS: { label: string; phone: string }[] = [
  { label: "Khách hàng", phone: "0387000001" },
  { label: "Nhân viên CSKH", phone: "0353000201" },
  { label: "Sếp phê duyệt", phone: "0905000205" },
  { label: "Đối tác ví (Chính sách)", phone: "0900000001" },
];

export default function LoginPage() {
  const router = useRouter();
  const [phone, setPhone] = useState("");
  const [password, setPassword] = useState("");
  const [error, setError] = useState<string | null>(null);
  const [loading, setLoading] = useState(false);

  async function doLogin(loginPhone: string, loginPassword: string) {
    setError(null);
    setLoading(true);
    // Timeout phía client (10s) — BUG-01 (FIN05-QA-Test-Report.md): nút "Đang
    // đăng nhập…" từng bị báo treo vô hạn không có lối thoát. fetch() không tự
    // có timeout — nếu request thật sự treo (mạng, backend đơ), trước đây
    // không có gì làm loading=false. AbortController đảm bảo LUÔN có phản hồi
    // rõ ràng trong 10s, đúng khuyến nghị "không bao giờ để loading treo vô
    // hạn" của báo cáo — dù thời điểm sửa không tái hiện lại được hang gốc.
    const controller = new AbortController();
    const timeoutId = setTimeout(() => controller.abort(), 10_000);
    try {
      const res = await fetch("/api/session", {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ phone: loginPhone.trim(), password: loginPassword }),
        signal: controller.signal,
      });
      const body = await res.json();
      if (!res.ok) {
        setError(body.detail ?? "Số điện thoại hoặc mật khẩu không đúng.");
        return;
      }
      // Vai trò lấy từ RESPONSE (server tra được qua phone), không phải lựa
      // chọn client tự khai trước khi gửi như luồng cũ.
      router.push(roleHome(body.role as Role));
      router.refresh();
    } catch (err) {
      if (err instanceof DOMException && err.name === "AbortError") {
        setError("Máy chủ phản hồi quá lâu (>10s) — thử lại giúp mình nhé.");
      } else {
        setError("Không kết nối được máy chủ — kiểm tra backend đã chạy chưa (make run).");
      }
    } finally {
      clearTimeout(timeoutId);
      setLoading(false);
    }
  }

  async function handleSubmit(e: React.FormEvent) {
    e.preventDefault();
    await doLogin(phone, password);
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
          <p className="sub">Nhập số điện thoại và mật khẩu tài khoản của bạn.</p>

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
              <b>Demo:</b> 4 tài khoản test bên dưới dùng chung mật khẩu{" "}
              <span className="mono">{DEMO_PASSWORD}</span>. Toàn bộ user khác trong dataset có mật khẩu ngẫu nhiên
              riêng (không dùng để test tay) — xem <span className="mono">data/generated/users.jsonl</span>.
            </div>
          </div>

          <div className="field" style={{ marginTop: 20 }}>
            <label>Đăng nhập nhanh (demo) — bấm để vào thẳng đúng vai trò</label>
            <div className="flex gap-sm wrap" style={{ marginTop: 7 }}>
              {QUICK_LOGIN_ACCOUNTS.map((acc) => (
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
