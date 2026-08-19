# QUYẾT ĐỊNH BIÊN DỮ LIỆU — Phương án B (regex-only cho đường gửi model) — CHẤP THUẬN CÓ ĐIỀU KIỆN

> 19/08/2026. Bảo Mật trả lời PO-agent, có quyền phủ quyết theo khung NĐ 13/2023 đã dùng nhất quán
> cả đợt. [ĐO] tự kiểm `scrub_regex` trước khi quyết — không nhận số đo của PO-agent làm bằng chứng
> duy nhất.

## QUYẾT: CHẤP THUẬN Phương án B, kèm BA điều kiện bắt buộc — không phải một chữ ký trắng

## Vì sao chấp thuận — cân đúng hai giá trị đang xung đột, không chỉ nhìn một phía

**Phân tích phạm vi rủi ro tồn dư của PO-agent ĐÚNG, đã tự kiểm lại:**
- `scrub_regex` (`pii.py:77-84`) chỉ dùng `_FALLBACK_EMAIL_RE`/`_FALLBACK_PHONE_RE`/`_FALLBACK_ID_RE`
  — ba loại PII CÓ CẤU TRÚC RÕ, tất định, gần như không dương tính giả. [ĐO] kiểm riêng
  `_FALLBACK_ID_RE = r"(?<![\w-])\d{9,19}(?!\d)"`: đòi biên KHÔNG PHẢI ký tự chữ/gạch ngang ngay
  trước dãy số — `TXN20260731000352` có "N" (chữ) đứng ngay trước dãy số, biên đó KHÔNG thoả, nên mã
  giao dịch dạng chữ+số dính liền **không bị regex này chạm tới**, khớp đúng con số 4,8% PO-agent đo.
- `_scrub_pii_cho_llm` (che theo TRƯỜNG trong kết quả tool, `customer_tools.py`) và regex trên đều
  ĐỘC LẬP với NER — hai lớp bảo vệ MẠNH NHẤT (dữ liệu giao dịch có cấu trúc, định danh cứng) không
  phụ thuộc quyết định hôm nay.
- Rủi ro tồn dư THẬT SỰ hẹp đúng như PO-agent thu hẹp: **tên bên thứ ba do CHÍNH KHÁCH tự gõ trong
  câu tự do**, không tra cứu được, không xác minh được là tên thật hay chỉ trùng tên.

**Cân đối hai giá trị, không chỉ nhìn về phía PDPA:** 49,2% câu bị bóp méo không chỉ là một con số
kỹ thuật xấu — với một dịch vụ xử lý KHIẾU NẠI TÀI CHÍNH, agent hiểu sai gần một nửa số câu là một
rủi ro **bảo vệ người tiêu dùng** thật (hiểu sai dẫn tới xử lý sai/chậm một khiếu nại tài chính thật).
Đây không phải "đổi bảo mật lấy tiện lợi" — là cân hai loại rủi ro cho khách hàng, và ở quy mô 49%,
rủi ro từ status quo (A) không còn nhỏ hơn rủi ro tồn dư của (B).

**Một điểm neo quan trọng, không phải suy luận tuỳ tiện:** dự án đã có TIỀN LỆ chấp nhận dữ liệu tự
do của khách RỜI hạ tầng KHÔNG che (`complaints.description_raw`, ADR-025 QĐ1, vì lý do toàn vẹn bằng
chứng). Quyết định hôm nay CÙNG HỌ RỦI RO đó — chấp nhận một phần dữ liệu tự do đi qua chưa được lọc
sạch 100%, để giữ đúng giá trị nghiệp vụ của nó — không phải một tiền lệ mới, là áp cùng logic đã
duyệt cho một kênh khác.

## BA ĐIỀU KIỆN bắt buộc đi kèm chấp thuận

1. **Phải thành một ADR có khai, không phải một commit âm thầm.** Đúng như PO-agent tự nhận: đây là
   "chính sách BIÊN DỮ LIỆU" thật, không phải một bản vá lỗi hình dạng. Ghi rõ: lý do chọn B thay A/C,
   phạm vi rủi ro tồn dư (tên bên thứ ba khách tự gõ), và **mốc xem lại** (không phải quyết định vĩnh
   viễn — xem điều kiện 3).
2. **KHÔNG đụng chính sách log/trace** — đã nói rõ, nhắc lại để không ai tự ý mở rộng: log/trace giữ
   nguyên regex+NER hiện có (kể cả sau khi loại `MEDICAL_LICENSE`, quyết định đó vẫn đứng riêng, độc
   lập với B — xem mục dưới).
3. 🔴 **Đo lại và cân nhắc PHƯƠNG ÁN D trước khi coi B là chốt cuối cùng — KHÔNG chặn quyết định hôm
   nay, nhưng phải làm trong tuần này:** PO-agent + Lead đã nhảy từ "regex+NER (Spacy+underthesea)"
   thẳng sang "regex-only", bỏ qua một điểm giữa CHƯA ĐO: **regex + `_VietnameseNameRecognizer`
   (underthesea) ĐƠN LẺ, KHÔNG có Spacy.** Underthesea là model CHUYÊN tiếng Việt (khác Spacy đa ngôn
   ngữ — nguồn chính của noise 12%+ trên từ thường đã tìm thấy trước đó). Nếu D đạt tỉ lệ sạch gần
   bằng B mà VẪN che được một phần tên bên thứ ba khách tự gõ — D tốt hơn B THUẦN TUỲ, không đánh đổi
   gì thêm. Đây là phép đo RẺ (đọc lại corpus 124 câu đã có, đổi registry, không cần lượt LLM mới).
   **Nếu D đo ra tệ hơn kỳ vọng (underthesea một mình cũng noise cao) — giữ B, đóng câu hỏi.** Nếu D
   tốt — thay B bằng D trong ADR trước khi trình PO thật duyệt bản cuối.

## MEDICAL_LICENSE — câu hỏi TỰ HẾT ĐỐI TƯỢNG cho model-input, NHƯNG quyết định trước đó VẪN ĐỨNG cho log/trace

Nếu B (hoặc D) được chọn cho đường model-input, không NER nào chạy trên đường đó nữa —
`MEDICAL_LICENSE` không còn cơ hội chạm dữ liệu ở đây, đúng như PO-agent nói. **Nhưng quyết định loại
bỏ hẳn recognizer `MEDICAL_LICENSE` khỏi registry (đã ra hôm nay, gửi Lead) KHÔNG vì thế mà thành thừa
— log/trace vẫn dùng registry đầy đủ, `MEDICAL_LICENSE` vẫn gây nhiễu Ở ĐÓ.** Hai quyết định độc lập,
cả hai đều làm, không cái nào thay được cái nào.

## Một khoản nợ kỹ thuật nhỏ, khai để không ai vấp

`pii.py:78-80` — docstring `scrub_regex()` hiện viết: *"KHÔNG dùng trực tiếp cho log thật (dùng
scrub_pii)."* Nếu B được chọn, câu này **sai với thực tế mới** (hàm này SẼ được dùng trực tiếp, chỉ
là cho đường model-input chứ không phải log). Coder cần sửa docstring cùng lúc land B, đừng để một
chú thích nói ngược lại điều code đang làm — đúng nguyên tắc "cơ chế/tài liệu phải khớp hành vi thật"
dự án đã áp nhiều lần trong đợt này.

## Ranh giới quyết định — đọc trước khi trích

Quyết định này CHỈ áp cho đường `graph.py:787` (tin nhắn khách gửi trực tiếp cho model). KHÔNG áp
cho: log/trace (giữ nguyên), kết quả tool (đã có cơ chế riêng, không đổi), transcript CSKH đọc lại
(ADR-044, đọc bản đã ghi tại thời điểm gửi — kế thừa quyết định này một cách tự nhiên, không cần
quyết lại). Không kết luận thay cho D — D là khuyến nghị đo, chưa phải quyết định.
