import Link from "next/link";
import { redirect } from "next/navigation";
import { getServerSession } from "@/lib/session-server";
import { roleHome } from "@/lib/session";

// `/` dọn về từ `/gioi-thieu` (26/08) — thiết kế của Lead, soát bởi Review:
// GIỮ nhánh redirect có phiên NGUYÊN VẸN (0 thay đổi logic auth), chỉ đổi
// NHÁNH KHÔNG PHIÊN từ redirect("/login") sang render trang quảng cáo.
// proxy.ts xử lý y hệt (khớp CHÍNH XÁC pathname === "/", KHÔNG qua
// PUBLIC_PATHS — xem comment ở đó vì sao) — trang này là lớp phòng thủ thứ
// hai (docs Next.js khuyến nghị không chỉ dựa vào proxy cho auth), phòng khi
// có đường vào không qua proxy.
export default async function Home() {
  const session = await getServerSession();
  if (session) {
    redirect(roleHome(session.role));
  }

  // 🔴 NỘI DUNG dưới đây KHÔNG do ux-ui viết — dựng nguyên văn theo
  // docs/2026-08-26-noi-dung-landing-page.md (PO-agent viết, PO thật duyệt).
  // Muốn đổi câu nào → hỏi p-226-f0, không tự sửa chữ ở đây. Lý do: trang
  // quảng cáo là tuyên bố sản phẩm, và ba ràng buộc cứng (agent không quyết
  // định · cấm bịa số liệu · không hỏi OTP giao dịch) đều phá được bằng một
  // câu marketing mà không chạm dòng code nào.
  //
  // [ĐO 26/08/2026] 4 số liệu mục "SỐ LIỆU" đếm từ contracts/ hiện hành. SỐ
  // NÀY SẼ CŨ ĐI khi contract đổi — đổi authority-matrix/agent-tools thì đếm
  // lại, đừng để hoá thạch trên trang công khai.
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
            {/* 27/08 — Marketing: "Đăng nhập dùng thử" là cánh cửa khoá cho
                người chưa có tài khoản. Đổi sang dẫn thẳng vào phiên demo
                (tài khoản khách demo có sẵn ở /login, đăng nhập nhanh 1
                chạm), không còn dẫn tới ô nhập mật khẩu trống.
                Nút phụ "Đặt lịch trao đổi" CHƯA thêm — chưa có đích thật
                (không có email/lịch hẹn nào công bố trong dự án để trỏ tới,
                và trang không tự bịa URL/mailto). Đã hỏi p-226-17. */}
            <Link href="/login" className="btn btn-primary">
              Dùng thử ngay — tài khoản demo
            </Link>
          </div>
        </div>
      </section>

      {/* 27/08 — Marketing (khối 02, "Đặt vấn đề — 2 giờ sáng"): trang cũ
          nhảy thẳng từ hero sang cơ chế; người mua không thức dậy với "tôi
          cần một luồng bốn bước", họ thức dậy với một ca lúc 2 giờ sáng
          không ai trực. CỐ Ý không có mốc ngày cụ thể (30/05/15 ngày làm
          việc) — chưa chốt TT 15/2024 hay TT 40/2024, ship được ngay vì
          không có con số nào để sai. */}
      <section className="lp-section">
        <div style={{ maxWidth: 640, margin: "0 auto", textAlign: "center" }}>
          <h2 style={{ marginBottom: 12 }}>Sự cố tiền bạc không đợi giờ hành chính</h2>
          <p style={{ fontStyle: "italic", color: "var(--text-dim)", fontSize: "var(--fs-16)" }}>
            &ldquo;Khách chuyển nhầm lúc 2 giờ sáng, và không liên hệ được tổng đài.&rdquo;
          </p>
          <p style={{ color: "var(--text-dim)", fontSize: "var(--fs-16)", marginTop: 16 }}>
            Hạ tầng thanh toán chạy 24/7. Nhu cầu hỗ trợ cũng vậy — hai trong ba khung giờ cao điểm của
            người mua sắm nằm ngoài giờ hành chính. Nhưng đồng hồ pháp lý cho tra soát khiếu nại thì đếm
            từ <b style={{ color: "var(--text)" }}>ngày tiếp nhận</b>, không đếm từ ngày đội trực đi làm.
          </p>
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
          <div className="step emphasis">
            <b>④ Sếp duyệt</b>
            <span>Chỉ cấp duyệt mới ra được quyết định cuối</span>
          </div>
        </div>
      </section>

      {/* 27/08 — Marketing (khối 05, "Bài toán kinh tế"): Brief §3 đặt chi
          phí vận hành làm một trong ba trục định vị, trang cũ không có một
          dòng nào về kinh tế. CỐ Ý không có con số tiền (chưa có lương CSKH
          kèm nguồn) — nói HÌNH DẠNG đường chi phí, không nói giá trị. KHÔNG
          dùng -33,5% (chưa có mẫu số — đúng lỗi STATE §8 ghi là bài học đắt
          nhất dự án). Cặp số 0,06s/0 token vs 8,70s/6.216 token là CÙNG MỘT
          CÂU đo hai đường — không mẫu số nào để tranh cãi. */}
      <section className="lp-section">
        <div style={{ maxWidth: 720, margin: "0 auto" }}>
          <h2 style={{ textAlign: "center" }}>Chi phí người tăng theo giờ phủ. Chi phí máy thì không.</h2>
          <p style={{ color: "var(--text-dim)", fontSize: "var(--fs-16)", textAlign: "center", marginTop: 16 }}>
            Phủ hỗ trợ 24/7 cần <b style={{ color: "var(--text)" }}>168 giờ mỗi tuần</b>. Với ca 40 giờ,
            đó là hơn bốn người trước khi tính phép, ốm và đào tạo — và{" "}
            <b style={{ color: "var(--text)" }}>hơn một nửa số giờ ấy</b> rơi vào ban đêm hoặc cuối tuần,
            nơi lương phải cộng phụ trội theo luật.
          </p>
          <p style={{ color: "var(--text-dim)", fontSize: "var(--fs-16)", textAlign: "center", marginTop: 12 }}>
            Sen không có đường chi phí đó. Hai giờ sáng và hai giờ chiều tốn như nhau.
          </p>
          <h3 style={{ textAlign: "center", marginTop: 32, fontSize: "var(--fs-20)" }}>
            Và nó không tiêu tiền cho việc không cần tới mô hình
          </h3>
          <p style={{ color: "var(--text-dim)", fontSize: "var(--fs-16)", textAlign: "center", marginTop: 16 }}>
            Một câu chào hỏi không cần tới AI. Sen nhận ra bằng luật cứng và trả lời trong{" "}
            <b style={{ color: "var(--text)" }}>0,06 giây</b>, tốn <b style={{ color: "var(--text)" }}>0 token</b>.
            Cùng câu đó nếu đẩy qua mô hình đầy đủ:{" "}
            <b style={{ color: "var(--text)" }}>6.216 token</b> và{" "}
            <b style={{ color: "var(--text)" }}>8,70 giây</b>.
          </p>
          <p style={{ color: "var(--text-dim)", fontSize: "var(--fs-16)", textAlign: "center", marginTop: 12 }}>
            Đây không phải &ldquo;mô hình thông minh hơn nên rẻ hơn&rdquo;. Đây là{" "}
            <b style={{ color: "var(--text)" }}>không gọi mô hình</b>. Cơ chế tất định — nó không phụ
            thuộc hôm nay mô hình hành xử ra sao.
          </p>
        </div>
      </section>

      <section className="lp-section" style={{ background: "var(--surface-2)", maxWidth: "none" }}>
        <div style={{ maxWidth: 1120, margin: "0 auto" }}>
          <h2>Không phải lời hứa — là con số đếm được</h2>
          <div className="lp-stat-strip" style={{ marginTop: 40 }}>
            <div className="lp-stat">
              <div className="num">34</div>
              <div className="label">Mọi đường vào hệ thống đều kiểm quyền theo vai. Không có cửa sau.</div>
            </div>
            <div className="lp-stat">
              <div className="num">5/5</div>
              <div className="label">
                Năm công cụ AI được phép gọi. Năm công cụ bị cấm tuyệt đối — chúng không tồn tại trong
                hàm dựng công cụ.
              </div>
            </div>
            <div className="lp-stat">
              <div className="num">386</div>
              <div className="label">Ca đánh giá chất lượng, chia 15 bộ riêng biệt.</div>
            </div>
            <div className="lp-stat">
              <div className="num">60</div>
              <div className="label">
                Trong số đó, 60 ca được niêm phong từ đầu và chưa ai chạy lần nào — để bộ đo không bị
                tối ưu ngược. Chúng chỉ được mở một lần, gần cuối.
              </div>
            </div>
            <div className="lp-stat">
              <div className="num" style={{ color: "var(--navy)" }}>0</div>
              <div className="label">Quyết định hoàn tiền AI được phép tự ra.</div>
            </div>
          </div>
          <p style={{ textAlign: "center", marginTop: 20, fontSize: "var(--fs-12)", color: "var(--text-faint)" }}>
            Đếm ngày 27/08/2026 — đổi contract thì đếm lại.
          </p>
        </div>
      </section>

      {/* 27/08 — Marketing (khối 07, "Vì sao AI cộng người, không phải AI
          thay người"): KHÔNG nêu tên công ty cụ thể trên trang công khai —
          nói tên trong phòng pitch, không nói ở đây (rủi ro không cần
          thiết, không được lợi gì thêm). */}
      <section className="lp-section">
        <div style={{ maxWidth: 640, margin: "0 auto", textAlign: "center" }}>
          <h2 style={{ marginBottom: 16 }}>Ngành đã thử hướng kia rồi</h2>
          <p style={{ color: "var(--text-dim)", fontSize: "var(--fs-16)" }}>
            Năm 2024, một fintech lớn công bố trợ lý AI của họ làm việc của{" "}
            <b style={{ color: "var(--text)" }}>700 nhân viên</b>. Năm 2025, chính lãnh đạo công ty
            thừa nhận việc lấy chi phí làm tiêu chí đánh giá chủ đạo đã dẫn tới{" "}
            <b style={{ color: "var(--text)" }}>chất lượng thấp hơn</b> — và họ tuyển người thật trở lại.
          </p>
          <p style={{ color: "var(--text-dim)", fontSize: "var(--fs-16)", marginTop: 16 }}>
            Sen chọn &ldquo;AI cộng người&rdquo; từ đầu. Không phải vì chúng tôi khôn hơn — mà vì với
            tiền thật của khách hàng, không có lựa chọn nào khác.
          </p>
          <p style={{ color: "var(--text-dim)", fontSize: "var(--fs-16)", marginTop: 16 }}>
            <b style={{ color: "var(--text)" }}>Và chúng tôi ép nó bằng kiến trúc, không bằng chính
            sách.</b> Nguyên tắc người đề xuất không được là người duyệt nằm ở tầng ràng buộc của cơ sở
            dữ liệu. Một chính sách đảo được bằng một cuộc họp. Cái này thì không.
          </p>
        </div>
      </section>

      {/* 27/08 — Marketing (khối 08, "SỬA GẤP"): P0 đã đóng TỪ TRƯỚC (xem
          các đợt vá /login copy cùng ngày) — câu cũ ở đây ("Thông tin bên
          thứ ba... được che trước khi hiển thị") không sai, nhưng KHÔNG nói
          gì về việc suy luận mô hình đi qua nhà cung cấp ngoài, trong khi
          /login và ChatClient.tsx ĐÃ TỰ KHAI điều này. Câu 2 (bể mô hình tự
          xoay) KHÔNG phải lời bào chữa — đó là kế hoạch thoát nhà cung cấp
          có thật. Giữ "thiết kế theo", KHÔNG viết "đã được chứng nhận" (PO
          chốt 26/08) — chưa qua kiểm toán độc lập nào. */}
      <section className="lp-section">
        <div style={{ maxWidth: 720, margin: "0 auto", textAlign: "center" }}>
          <p style={{ color: "var(--text-dim)", fontSize: "var(--fs-14)" }}>
            Thiết kế theo khung pháp lý hiện hành cho trung gian thanh toán tại Việt Nam —{" "}
            <b style={{ color: "var(--text)" }}>NĐ 52/2024</b> và <b style={{ color: "var(--text)" }}>TT 40/2024</b>.
            Dữ liệu cá nhân xử lý theo <b style={{ color: "var(--text)" }}>NĐ 13/2023</b>. Thông tin bên
            thứ ba trong giao dịch được che trước khi hiển thị.
          </p>
          <p style={{ color: "var(--text-dim)", fontSize: "var(--fs-14)", marginTop: 12 }}>
            Hệ thống chạy trong vùng hạ tầng do ví kiểm soát. Phần suy luận của mô hình đi qua nhà cung
            cấp đã khai báo, và hệ thống có sẵn cơ chế chuyển đổi nhà cung cấp mà không phải dựng lại.
          </p>
        </div>
      </section>

      {/* CHỈ nối /login — KHÔNG nối /dang-nhap-noi-bo từ trang công khai.
          27/08 — Marketing (khối 09): thương hiệu "FIN-05" -> "Sen" (khớp
          xưng hô "Sen" dùng xuyên suốt các khối mới), nút "Đăng nhập" ->
          "Dùng thử tài khoản demo" (cùng lý do đổi CTA ở khối 01 — không
          mời khách bấm vào một ô mật khẩu trống). */}
      <footer className="lp-footer" style={{ textAlign: "center" }}>
        <div style={{ color: "var(--text)", fontWeight: 700 }}>Sen · Trợ lý CSKH ví điện tử</div>
        <div style={{ color: "var(--text-dim)", fontSize: "var(--fs-14)", marginTop: 4 }}>
          AI 20K Build Phase Cohort 3 — Vingroup × VinUni
        </div>
        <Link href="/login" className="btn btn-outline btn-sm" style={{ marginTop: 20, display: "inline-flex" }}>
          Dùng thử tài khoản demo
        </Link>
      </footer>
    </>
  );
}
