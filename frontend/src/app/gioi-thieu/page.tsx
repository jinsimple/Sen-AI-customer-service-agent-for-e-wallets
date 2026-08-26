import Link from "next/link";

// Trang quảng cáo công khai. Route CỐ Ý đặt ở /gioi-thieu, KHÔNG phải `/` —
// `/` hiện là logic xác thực (proxy.ts + app/page.tsx redirect theo phiên),
// đổi nó cần thiết kế riêng của Lead + Review, không làm ở đây.
//
// 🔴 NỘI DUNG trang này KHÔNG do ux-ui viết — dựng nguyên văn theo
// docs/2026-08-26-noi-dung-landing-page.md (PO-agent viết, chờ PO thật
// duyệt). Muốn đổi câu nào → hỏi p-226-f0, không tự sửa chữ ở đây. Lý do nêu
// trong tài liệu đó: trang quảng cáo là tuyên bố sản phẩm, và ba ràng buộc
// cứng (agent không quyết định · cấm bịa số liệu · không hỏi OTP giao dịch)
// đều phá được bằng một câu marketing mà không chạm dòng code nào.
//
// [ĐO 26/08/2026] 4 số liệu mục "SỐ LIỆU" đếm từ contracts/ hiện hành. SỐ
// NÀY SẼ CŨ ĐI khi contract đổi — đổi authority-matrix/agent-tools thì đếm
// lại, đừng để hoá thạch trên trang công khai.
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
          <h1>Khiếu nại giao dịch, điều tra trong vài phút — quyết định vẫn thuộc về con người</h1>
          <p className="lead">
            FIN-05 là trợ lý AI cho đội chăm sóc khách hàng ví điện tử. Nó tra cứu giao dịch, đối chiếu
            chính sách và chuẩn bị hồ sơ có dẫn chứng. <strong>Người duyệt vẫn là người.</strong>
          </p>
          <div className="lp-hero-actions">
            <a href="#cach-hoat-dong" className="btn btn-primary">
              Xem sản phẩm hoạt động
            </a>
            <Link href="/login" className="btn btn-outline">
              Đăng nhập
            </Link>
          </div>
        </div>
      </section>

      {/* Thay cho dải logo đối tác — chưa có khách hàng nào, không dựng logo/chứng thực. */}
      <section className="lp-section">
        <div style={{ display: "grid", gap: 28, maxWidth: 720, margin: "0 auto" }}>
          <p style={{ fontSize: "var(--fs-16)", color: "var(--text-dim)", textAlign: "center" }}>
            <b style={{ color: "var(--text)" }}>Không bịa số.</b> Mỗi con số agent nói ra đều truy ngược
            được tới một lần tra cứu có thật. Không tra được, nó nói thẳng là không tra được.
          </p>
          <p style={{ fontSize: "var(--fs-16)", color: "var(--text-dim)", textAlign: "center" }}>
            <b style={{ color: "var(--text)" }}>Không vượt quyền.</b> Agent gọi công cụ dưới danh nghĩa
            khách hàng, không hơn. Không có đường nào để AI tự hoàn tiền.
          </p>
          <p style={{ fontSize: "var(--fs-16)", color: "var(--text-dim)", textAlign: "center" }}>
            <b style={{ color: "var(--text)" }}>Không hỏi thứ không được hỏi.</b> FIN-05 không bao giờ
            hỏi mật khẩu ví hay mã OTP giao dịch của bạn.
          </p>
        </div>
      </section>

      <section className="lp-section" id="cach-hoat-dong">
        <h2>Bốn bước xử lý một khiếu nại</h2>
        <div className="lp-flow">
          <div className="step">
            <b>① Khách gửi khiếu nại</b>
            <span>Nhắn như nói chuyện bình thường</span>
          </div>
          <span className="arrow">→</span>
          <div className="step">
            <b>② AI điều tra</b>
            <span>Tra giao dịch, đối chiếu chính sách, dựng hồ sơ có dẫn chứng</span>
          </div>
          <span className="arrow">→</span>
          <div className="step">
            <b>③ CSKH kiểm tra và trình</b>
            <span>Người thật đọc hồ sơ, xác minh, rồi trình lên</span>
          </div>
          <span className="arrow">→</span>
          <div className="step" style={{ borderColor: "var(--navy)", borderWidth: 2, background: "var(--navy-soft)" }}>
            <b>④ Sếp duyệt</b>
            <span>Chỉ cấp duyệt mới ra được quyết định cuối</span>
          </div>
        </div>
      </section>

      <section className="lp-section" style={{ background: "var(--surface-2)", maxWidth: "none" }}>
        <div style={{ maxWidth: 1120, margin: "0 auto" }}>
          <h2>Không phải lời hứa — là con số đếm được</h2>
          <div className="lp-stat-strip" style={{ marginTop: 40 }}>
            <div className="lp-stat">
              <div className="num">34</div>
              <div className="label">route có kiểm quyền theo vai</div>
            </div>
            <div className="lp-stat">
              <div className="num">5</div>
              <div className="label">công cụ AI được phép gọi — và 5 công cụ bị cấm tuyệt đối</div>
            </div>
            <div className="lp-stat">
              <div className="num">23</div>
              <div className="label">phép kiểm tự động canh các ràng buộc không thoả hiệp</div>
            </div>
            <div className="lp-stat">
              <div className="num" style={{ color: "var(--navy)" }}>0</div>
              <div className="label">quyết định hoàn tiền AI được phép tự ra</div>
            </div>
          </div>
          <p style={{ textAlign: "center", marginTop: 20, fontSize: "var(--fs-12)", color: "var(--text-faint)" }}>
            Đếm ngày 26/08/2026 — đổi contract thì đếm lại.
          </p>
        </div>
      </section>

      <section className="lp-section">
        <p style={{ maxWidth: 720, margin: "0 auto", textAlign: "center", color: "var(--text-dim)", fontSize: "var(--fs-14)" }}>
          Thiết kế theo khung pháp lý hiện hành cho trung gian thanh toán tại Việt Nam —{" "}
          <b style={{ color: "var(--text)" }}>NĐ 52/2024</b> và <b style={{ color: "var(--text)" }}>TT 40/2024</b>.
          Dữ liệu cá nhân xử lý theo <b style={{ color: "var(--text)" }}>NĐ 13/2023</b>. Thông tin bên
          thứ ba trong giao dịch được che trước khi hiển thị.
        </p>
      </section>

      {/* CHỈ nối /login — KHÔNG nối /dang-nhap-noi-bo từ trang công khai. */}
      <footer className="lp-footer" style={{ textAlign: "center" }}>
        <div style={{ color: "var(--text)", fontWeight: 700 }}>FIN-05 · Trợ lý CSKH ví điện tử</div>
        <div style={{ color: "var(--text-dim)", fontSize: "var(--fs-14)", marginTop: 4 }}>
          AI 20K Build Phase Cohort 3 — Vingroup × VinUni
        </div>
        <Link href="/login" className="btn btn-outline btn-sm" style={{ marginTop: 20, display: "inline-flex" }}>
          Đăng nhập
        </Link>
      </footer>
    </>
  );
}
