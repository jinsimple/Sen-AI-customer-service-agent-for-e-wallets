# BÀN GIAO LEAD — 30/08/2026 — phân tích tổng quan trước khi đội (bảo mật/QA-QC/review) vào việc

> Viết bởi phiên phân tích tổng quan (không gán vai cố định trong `.claude/agents/`), theo yêu cầu
> PO thật: đọc `project-keeper-knowledge/` + toàn dự án, đúc kết cho Lead trước khi Lead điều phối
> Coder/QA-QC/Review/Bảo mật đưa FIN-05 lên chuẩn ví điện tử EU/US.
> Đọc trước: `CLAUDE.md`, `docs/STATE.md` §0 (bàn giao 27/08 — TOÀN ĐỘI TẮT), `docs/security/review-2026-08-27-benchmark-eu-us.md` (đã commit `2a915db`).

## 0. Đừng làm lại việc đã xong

`docs/security/review-2026-08-27-benchmark-eu-us.md` **đã là bản benchmark EU/US đầy đủ**: PSD2/RTS-SCA,
GDPR, PCI-DSS, NIST 800-63B, FFIEC, ISO 27001/SOC2, biên giới AML/CFT — kèm bước 1-4 (5 phát hiện code
cụ thể, dòng số) và backlog đã chia sẵn theo `coder`/`QA-QC`/`review`. File này **là input chính** cho
đợt tới, không phải một tài liệu nền cần đọc rồi bỏ qua. Việc của Lead là **điều phối thực thi backlog
đó**, không phải giao lại một vòng rà soát mới từ đầu.

Tài liệu này bổ sung ba thứ báo cáo kia KHÔNG có: (1) góc nhìn kiến trúc tổng thể so với ngành, (2) rủi
ro vận hành đang treo có thể làm Lead đi sai hướng ngay từ lệnh đầu tiên, (3) thứ tự làm việc đề xuất.

## 1. Đánh giá kiến trúc — so với ngành ví điện tử EU/US

**Đúng hướng, nền tảng hiếm ở quy mô 1 người/vài tuần:**
- AI không có quyền tài chính: 5 tool chạm tiền không tồn tại trong hàm dựng tool AI (`INV-08`, kiểm
  bằng máy, không phải quy ước). Đây chính là mẫu "AI-assisted, human-executed" mà ví điện tử nghiêm
  túc dùng khi chưa đủ track record để tin AI tự quyết — đúng, đừng đổi hướng sang "AI tự động hơn"
  trước khi có dữ liệu vận hành thật.
- Maker-checker ép ở **tầng DB** (`CheckConstraint`), không chỉ tầng ứng dụng — sống sót qua cả truy
  cập SQL trực tiếp. Ít MVP làm tới mức này.
- `contracts/*.yaml` + test introspect app đang chạy (không đọc lại tài liệu) giải quyết đúng vấn đề
  "tài liệu nói dối" — đây là điểm khác biệt kỹ thuật thật sự, nên giữ nguyên triết lý này khi mở rộng
  contract, đừng để nó suy biến thành tài liệu thường.
- Audit trail cấp dòng dữ liệu (`tool_results → investigation_logs → resolutions.cited_tool_result_ids`)
  đáp ứng tinh thần SOC2 CC7.2 / ISO 27001 A.8.15 ở tầng ứng dụng — hiếm ở MVP.

**Khoảng cách với chuẩn "production ví điện tử EU/US thật":**
- Runtime demo tụt xuống AAL1 hiệu quả vì OTP trả thẳng trong response (chi tiết ở báo cáo 27/08,
  Phát hiện #2) — đây là gap LỚN NHẤT, đứng trước mọi gap khác vì nó chặn mọi tuyên bố tuân thủ.
- Chưa có hồ sơ giấy tờ compliance chính thức (DPIA Đ.25 GDPR, Incident Response runbook) dù vật liệu
  kỹ thuật đã đủ — đây là khoảng cách "giấy tờ", rẻ hơn khoảng cách "code" nhiều, nên xếp song song.
- Segregation-of-duties mới ở mức "không tự duyệt đề xuất của chính mình", chưa tới mức "người duyệt
  phải độc lập với người điều tra" mà SOC2 CC6.3 thường đòi cho vai có quyền tài chính cao nhất — đây
  là quyết định NGHIỆP VỤ (PO/domain expert), không phải lỗi kỹ thuật, đừng tự ý khép lại.

## 2. 🔴 Rủi ro vận hành đang treo — đọc trước khi gõ lệnh đầu tiên

Từ `docs/STATE.md` §0 (bàn giao 27/08, toàn đội tắt để tránh tràn context):
- Nhánh `dev/learning-loop` **đi trước origin 47 commit, chưa push** — CI trên nhánh này chưa từng
  chạy xanh trên đợt gần nhất. Đừng lấy "đã land cục bộ" làm bằng chứng CI xanh.
- Ba ngăn Docker (`fin05`/`fin05ttl`/`fin05do`) — **mọi lệnh `docker compose` bắt buộc `-p <tên ngăn>`**,
  thiếu là hạ nhầm ngăn khác. Một sự cố thật đã xóa sạch DB ngăn `fin05` do gõ nhầm lệnh shell (dấu
  huyền ngược trong nháy kép bị thực thi) — ngăn đó **chưa seed lại**.
- `fin05-sach` đang ở trạng thái lai: container chạy đã bị `docker cp` tay 4 tệp, ảnh cũ hơn container.
  Dựng lại ảnh sẽ MẤT 4 tệp đó và trông giống hồi quy — đừng dựng lại mà không biết trước.
- Cây làm việc **dùng chung giữa nhiều phiên Claude** — mọi lệnh git (`stash`/`commit`/`checkout`/`clean`)
  phải có pathspec, kể cả `git commit` phải kèm `-- <path>` trong CÙNG một lệnh với `git add` (tách
  bước sẽ tạo cửa sổ index dùng chung, đã gây sự cố mất truy vết thật).
- `~50 lượt gọi loginAs() trong frontend/e2e/` sẽ đỏ hàng loạt vì cổng chặn-sai-cổng-đăng-nhập đã land
  nhưng phần lớn test chưa retrofit — **không phải hồi quy mới**, đừng báo động nhầm.

## 3. Thứ tự làm việc đề xuất cho Lead

1. **Xác nhận trạng thái vật lý trước** — không tin STATE.md/ADR là hiện tại tuyệt đối, đo lại: `git
   status`, `git rev-list --left-right --count origin/dev/learning-loop...HEAD`, `python
   scripts/check_contracts.py`, đếm `def test_` trong `tests/test_invariants.py` (phải = 23).
2. **Giao backlog benchmark 27/08 theo đúng phân vùng ghi** — mục "Backlog đề xuất cho Lead" trong báo
   cáo đã chia sẵn `coder`/`QA-QC`/`review`, không cần chia lại. Việc rẻ, không cần PO chốt trước, có
   thể giao ngay: đổi `==` sang `secrets.compare_digest` (verify_otp), banner nguồn-sự-thật cho
   `fraud_signals.yaml`. Việc cần PO chốt trước khi code: vá OTP-qua-SMS-thật, gắn
   `require_token_chua_thu_hoi` vào 3 route (ADR-055 đang chờ).
3. **Review đọc lại ~55 ADR** (báo cáo 27/08 chỉ lướt ADR-040→055) để xác nhận có ADR nào đã quyết
   định KHÔNG làm route xóa/xuất dữ liệu GDPR chưa, tránh backlog trùng.
4. **Đối chiếu 10 việc chờ PO** ở `docs/STATE.md` §0.7 với backlog benchmark — mục ⑥ (Caddyfile header
   bảo mật) và ⑦ (ADR-054 hai câu OTP) khả năng trùng một phần với Phát hiện #2/#3 của báo cáo 27/08.
5. **Ba việc CAO cần xác nhận với PO cùng lúc** (giấy tờ, không chặn lẫn nhau, có thể xếp lịch song
   song): OTP-qua-SMS-thật (code) · DPIA/hồ sơ Đ.25 chính thức (giấy tờ) · IR runbook chính thức
   (giấy tờ).

## 4. Việc chưa gán vai — cần Lead/PO xác nhận vùng ghi trước khi ai đó tự ý viết

Các file/thư mục sau đang untracked, không khớp rõ vùng ghi nào trong CLAUDE.md §4:
- `docker-compose.qa-stripe.override.yml` (gốc repo) — không phải `docker-compose.do.yml` (vùng
  devops được nêu đích danh); cần hỏi xem đây là vùng devops hay tester.
- `presentation/FIN05_Slide_Prompt_Context.md` — thư mục `presentation/` không nằm trong bản đồ repo
  §6 của CLAUDE.md.
- `frontend/e2e/quay-*.spec.ts`, `frontend/playwright.*.config.ts` — khớp vùng `tester`
  (`frontend/e2e/`), có vẻ ổn, chỉ nêu để Lead biết đang có việc dở chưa commit.

## 5. Câu hỏi cần PO quyết, không tự suy đoán

- Mức ưu tiên "trước khi pitch đối tác EU/US thật" cho 3 mục CAO ở mục 3.5 — deadline pitch đang tới
  gần hay còn thời gian?
- Có ADR nào đã quyết định KHÔNG làm route xóa/xuất dữ liệu GDPR (Đ.15/17) chưa, hay đây là thiếu sót
  thật cần thêm vào backlog?
- Segregation-of-duties mở rộng (người duyệt phải độc lập người điều tra) — có cần chặn ở MVP này
  không, hay để lại làm câu hỏi mở như hiện tại?
