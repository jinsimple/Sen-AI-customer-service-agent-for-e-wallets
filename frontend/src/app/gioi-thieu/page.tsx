import Link from "next/link";

// Trang quảng cáo công khai — quyết định 26/08. CỐ Ý đặt ở /gioi-thieu, KHÔNG
// phải ở `/` — route `/` hiện là logic xác thực (proxy.ts + app/page.tsx
// redirect theo phiên đăng nhập); đổi nó là chạm đường đăng nhập của sản
// phẩm đang chạy thật, cần Review soát riêng trước khi làm, không tự sửa ở đây.
//
// RÀNG BUỘC PHÁP LÝ RIÊNG CHO TRANG NÀY (chặt hơn app nội bộ, vì người NGOÀI
// đọc và tin): không một câu nào được nói AI tự xử lý/tự duyệt/tự hoàn tiền —
// vi phạm ràng buộc cứng số 1 (agent không bao giờ quyết định). Chỉ được nói
// AI điều tra và đề xuất CÓ CĂN CỨ, con người quyết định. Không bịa logo đối
// tác, không bịa lời chứng thực, không bịa số hiệu quả (%, tốc độ xử lý...).
// Mọi con số trên trang này là SỰ THẬT VỀ CẤU TRÚC hệ thống (đếm được trong
// contracts/), không phải số đo hiệu năng.
export default function GioiThieuPage() {
  return (
    <>
      <nav className="lp-nav">
        <span className="brand">Sen · FIN-05</span>
        <Link href="/login" className="btn btn-primary btn-sm">
          Đăng nhập
        </Link>
      </nav>

      <section className="lp-hero">
        <div className="lp-hero-inner">
          <h1>Agent điều tra. Người quyết định. Mọi con số truy được về nguồn.</h1>
          <p className="lead">
            Trợ lý AI cho đội chăm sóc khách hàng ví điện tử — tra cứu giao dịch bằng công cụ thật, đề
            xuất hướng xử lý có căn cứ. Quyết định cuối cùng liên quan tới tiền luôn thuộc về con người.
          </p>
          <div className="lp-hero-actions">
            <Link href="/login" className="btn btn-primary">
              Dùng thử với vai khách hàng
            </Link>
            <a href="#cach-hoat-dong" className="btn btn-outline">
              Xem cách hoạt động
            </a>
          </div>
        </div>
      </section>

      <section className="lp-section">
        <div className="lp-bento">
          <div className="card span-2">
            <svg className="icon icon-lg" viewBox="0 0 24 24"><circle cx="11" cy="11" r="7" /><path d="M21 21l-4-4" /></svg>
            <div className="card-title">AI điều tra bằng công cụ thật</div>
            <div className="card-sub">
              Mọi câu trả lời bắt nguồn từ 5 công cụ tra cứu có kiểm soát — giao dịch, lịch sử khách
              hàng, chính sách. Không tra được thì nói rõ &quot;không tra được&quot;, không đoán cho êm tai.
            </div>
          </div>
          <div className="card span-2">
            <svg className="icon icon-lg" viewBox="0 0 24 24"><rect x="4" y="11" width="16" height="9" rx="2" /><path d="M8 11V7a4 4 0 018 0v4" /></svg>
            <div className="card-title">Con người luôn quyết định</div>
            <div className="card-sub">
              AI không có đường nào để tự thực thi hoàn tiền hay điều chỉnh số dư. Nhân viên CSKH điều
              tra và trình đề xuất; chỉ người phê duyệt mới xác nhận hành động cuối cùng.
            </div>
          </div>
          <div className="card">
            <svg className="icon icon-lg" viewBox="0 0 24 24"><path d="M9 12l2 2 4-4" /><circle cx="12" cy="12" r="10" /></svg>
            <div className="card-title">Truy vết được về nguồn</div>
            <div className="card-sub">Mọi số tiền, trạng thái nhắc tới đều gắn với một kết quả tra cứu cụ thể.</div>
          </div>
          <div className="card">
            <svg className="icon icon-lg" viewBox="0 0 24 24"><rect x="4" y="11" width="16" height="9" rx="2" /><path d="M8 11V7a4 4 0 018 0v4" /></svg>
            <div className="card-title">Không chạm dữ liệu nhạy cảm</div>
            <div className="card-sub">Xác thực bằng mã phiên làm việc — không bao giờ hỏi mật khẩu ví hay mã OTP giao dịch.</div>
          </div>
          <div className="card">
            <svg className="icon icon-lg" viewBox="0 0 24 24"><path d="M12 2l8 4v6c0 5-3.5 8.5-8 10-4.5-1.5-8-5-8-10V6l8-4z" /></svg>
            <div className="card-title">Minh bạch với khách hàng</div>
            <div className="card-sub">Mọi phiên chat nói rõ ngay từ đầu đây là trợ lý AI, không giả làm người thật.</div>
          </div>
          <div className="card">
            <svg className="icon icon-lg" viewBox="0 0 24 24"><path d="M12 9v4M12 17h.01" /><circle cx="12" cy="12" r="10" /></svg>
            <div className="card-title">Gắn cờ khác với khoá ví</div>
            <div className="card-sub">Nghi ngờ gian lận và khoá tài khoản là hai việc tách biệt hoàn toàn — không tự động hoá thành một.</div>
          </div>
        </div>
      </section>

      <section className="lp-section" style={{ background: "var(--surface-2)", maxWidth: "none" }}>
        <div style={{ maxWidth: 1120, margin: "0 auto" }}>
          <h2>Không phải lời hứa — là con số đếm được</h2>
          <p className="lead">Đo trực tiếp trên cấu trúc hệ thống, không phải số đo hiệu năng.</p>
          <div className="lp-stat-strip" style={{ marginTop: 40 }}>
            <div className="lp-stat">
              <div className="num">4</div>
              <div className="label">loại khiếu nại được phân loại</div>
            </div>
            <div className="lp-stat">
              <div className="num">5</div>
              <div className="label">công cụ điều tra dữ liệu thật</div>
            </div>
            <div className="lp-stat">
              <div className="num">23</div>
              <div className="label">kiểm thử tự động canh 5 ràng buộc an toàn</div>
            </div>
            <div className="lp-stat">
              <div className="num">0</div>
              <div className="label">đường để AI tự duyệt hoàn tiền</div>
            </div>
          </div>
        </div>
      </section>

      <section className="lp-section" id="cach-hoat-dong">
        <h2>Cách một khiếu nại được xử lý</h2>
        <p className="lead">Bốn bước, mỗi bước một vai — không ai kiêm luôn vai người duyệt.</p>
        <div className="lp-flow">
          <div className="step">
            <b>Khách hàng</b>
            <span>Mô tả khiếu nại qua chat</span>
          </div>
          <span className="arrow">→</span>
          <div className="step">
            <b>AI điều tra</b>
            <span>Tra cứu, phân loại, đề xuất</span>
          </div>
          <span className="arrow">→</span>
          <div className="step">
            <b>CSKH</b>
            <span>Kiểm tra, trình đề xuất</span>
          </div>
          <span className="arrow">→</span>
          <div className="step">
            <b>Người phê duyệt</b>
            <span>Xác thực, quyết định cuối</span>
          </div>
        </div>
      </section>

      <footer className="lp-footer">
        <div className="lp-footer-grid">
          <div>
            <h4>Sen · FIN-05</h4>
            <p>AI Agent hỗ trợ CSKH ví điện tử xử lý khiếu nại giao dịch. AI điều tra và đề xuất có căn cứ — con người quyết định.</p>
          </div>
          <div>
            <h4>Sản phẩm</h4>
            <Link href="/login">Đăng nhập</Link>
            <a href="#cach-hoat-dong">Cách hoạt động</a>
          </div>
          <div>
            <h4>Về dự án</h4>
            <span style={{ display: "block", fontSize: "var(--fs-14)", color: "var(--text-dim)" }}>
              AI 20K Build Phase · Cohort 3
            </span>
          </div>
        </div>
      </footer>
    </>
  );
}
