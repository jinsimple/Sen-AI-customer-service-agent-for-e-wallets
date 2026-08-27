// Trang "chống lừa đảo" — nội dung do Marketing (p-226-17) viết, ship
// NGUYÊN VĂN, không tự diễn giải lại. Route CỐ Ý luôn công khai (xem
// proxy.ts::ALWAYS_PUBLIC_PATHS) — không redirect theo bất kỳ chiều nào, kể
// cả với người ĐÃ đăng nhập, vì đây là trang khách mở ĐÚNG LÚC đang nghi
// mình bị lừa, thường là lúc đang đăng nhập dở.
//
// 🔴 KHÔNG dùng bộ chữ/hiệu ứng của trang "/" — Marketing dẫn "ADR-053"
// (Playfair Display + particles + magnetic CTA) làm lý do; [ĐO] ADR đó
// KHÔNG tồn tại trong docs/DECISIONS.md (mới nhất là ADR-052), và "/" thật
// sự đang dùng Inter + hero tĩnh, không phải Playfair/particles/magnetic
// CTA — đã báo lại Marketing. NHƯNG nguyên tắc đứng độc lập với ADR có thật
// hay không: trang trấn an người đang hoảng thì nên tối giản, không hiệu
// ứng — áp dụng bằng ĐÚNG bộ token sẵn có (Inter, --text/--bg/--danger...),
// không phải bằng bộ font/màu ấm của bản nháp Marketing (bản đó tự dùng
// serif "Source Serif 4" cho phần thân — cùng rủi ro dấu tiếng Việt họ vừa
// cảnh báo tôi tránh).
//
// KHÔNG liên kết về "/" ở bất cứ đâu trên trang này (chỉ định rõ từ
// Marketing) — người đang lo mất tiền mà bị mời "xem giải pháp doanh
// nghiệp" là phi lý.
export default function ChoKhachHangPage() {
  return (
    <main className="ck-page">
      <div className="ck-wrap">
        <p className="ck-eyebrow">Sen · Ví điện tử</p>
        <h1 className="ck-h1">
          Sen là trợ lý AI của tổng đài ví. Sen không bao giờ hỏi mật khẩu hay mã OTP giao dịch của bạn.
        </h1>
        <p className="ck-lead">
          Khi bạn gặp sự cố — bị trừ tiền hai lần, tiền chưa tới nơi, chuyển nhầm người — Sen tra cứu
          giao dịch và chuẩn bị hồ sơ để nhân viên xử lý.
        </p>
        <p className="ck-lead-strong">Sen không tự quyết định bất cứ điều gì về tiền của bạn.</p>

        <section className="ck-core">
          <h2 className="ck-h2">Ba điều Sen không bao giờ hỏi bạn</h2>
          <ul className="ck-never">
            <li>
              <span className="ck-x" aria-hidden="true">✕</span>
              <span><b>Mật khẩu ví của bạn.</b> Không bao giờ, không vì lý do gì.</span>
            </li>
            <li>
              <span className="ck-x" aria-hidden="true">✕</span>
              <span>
                <b>Mã OTP giao dịch.</b> Sen có thể xin mã xác thực <i>phiên hỗ trợ</i> để mở tra cứu —
                đó là mã khác, và Sen sẽ nói rõ. Mã OTP để <i>duyệt một giao dịch</i> thì không bao giờ.
              </span>
            </li>
            <li>
              <span className="ck-x" aria-hidden="true">✕</span>
              <span>
                <b>Chuyển tiền đi đâu đó.</b> Sen không bao giờ yêu cầu bạn chuyển tiền để &ldquo;xác
                minh&rdquo;, &ldquo;mở khoá&rdquo; hay &ldquo;nhận lại tiền&rdquo;.
              </span>
            </li>
          </ul>
          <p className="ck-core-warn">
            <b>Nếu ai đó tự xưng là Sen mà hỏi một trong ba điều trên — đó là lừa đảo.</b> Dừng lại.
            Đừng đưa. Gọi tổng đài của ví bạn đang dùng.
          </p>
        </section>

        <section className="ck-section">
          <h2 className="ck-h2">Sau khi bạn nhắn, chuyện gì xảy ra</h2>
          <p>
            <b>1 · Sen tra cứu.</b> Nó tìm giao dịch bạn nói tới và đối chiếu với quy định. Nếu không
            tìm ra, nó nói thẳng là không tìm ra — nó không đoán.
          </p>
          <p>
            <b>2 · Một nhân viên thật đọc hồ sơ.</b> Không phải máy đọc. Người đọc, và người đó thấy
            được từng bước Sen đã tra.
          </p>
          <p>
            <b>3 · Người có thẩm quyền quyết định.</b> Mọi việc liên quan tới tiền — hoàn tiền, điều
            chỉnh số dư — chỉ người này quyết được. Sen không quyết. Nhân viên tiếp nhận cũng không
            quyết.
          </p>
          <p>Bạn theo dõi được hồ sơ của mình đang ở bước nào.</p>
        </section>

        <section className="ck-section ck-grid-2">
          <div>
            <h3 className="ck-h3">Sen giúp được gì</h3>
            <ul className="ck-plain">
              <li>Tra cứu giao dịch của bạn và cho biết trạng thái thật của nó</li>
              <li>Giải thích quy định áp dụng cho trường hợp của bạn</li>
              <li>Mở hồ sơ khiếu nại và chuyển tới nhân viên</li>
              <li>Gọi một nhân viên thật vào cuộc trò chuyện khi bạn cần</li>
            </ul>
          </div>
          <div>
            <h3 className="ck-h3">Sen không làm gì</h3>
            <ul className="ck-plain">
              <li>Không hoàn tiền, không điều chỉnh số dư — Sen không có quyền đó</li>
              <li>Không kết luận ai đúng ai sai, không kết luận có gian lận hay không</li>
              <li>Không khoá ví của bạn</li>
              <li>Không trả lời khi không tra được — trường hợp đó Sen nói thẳng, thay vì đoán một câu nghe cho xuôi</li>
            </ul>
          </div>
        </section>

        <section className="ck-section">
          <h2 className="ck-h2">Nếu bạn thấy có gì đó không ổn</h2>
          <p>Bạn có thể yêu cầu nói chuyện với nhân viên thật bất cứ lúc nào — chỉ cần nhắn.</p>
          <p>
            Nếu ai đó liên hệ bạn, tự xưng là Sen hoặc là tổng đài, và hỏi mật khẩu, mã OTP giao dịch,
            hoặc bảo bạn chuyển tiền: <b>đó không phải chúng tôi.</b> Dừng lại và gọi tổng đài của ví
            bạn đang dùng.
          </p>
        </section>

        <footer className="ck-footer">
          <p>
            <b>Sen · Trợ lý CSKH ví điện tử</b>
            <br />
            AI 20K Build Phase Cohort 3 — Vingroup × VinUni
          </p>
          <p className="ck-footer-dim">
            Sen hiện là sản phẩm mẫu, chạy trên dữ liệu mô phỏng và chưa phục vụ khách hàng thật của ví
            nào.
          </p>
        </footer>
      </div>
    </main>
  );
}
