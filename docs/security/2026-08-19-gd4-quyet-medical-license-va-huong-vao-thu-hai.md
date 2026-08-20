# GĐ4 — quyết MEDICAL_LICENSE (b: loại bỏ) + hoãn quyết hướng Spacy, đòi đo lại sau khi vá lớp thứ hai

> 19/08/2026. [ĐO] tự kiểm `pii.py` hiện tại (sau `dec5335`) trước khi quyết — xác nhận
> `_NHAN_NER_TU_DO` không chứa `MEDICAL_LICENSE`, xác nhận danh mục predefined recognizer đầy đủ.

## Quyết (1): MEDICAL_LICENSE — **(b) LOẠI BỎ HẲN**, không chọn (a)

**(a) sai về cấu trúc, không chỉ kém hơn:** MEDICAL_LICENSE là entity ĐỊNH NGHĨA BẰNG chữ số — áp
"có chữ số ⟹ loại" vào chính nó là tự triệt tiêu, không còn gì để nhận diện. Không phải một lựa chọn
tồi, là một lựa chọn KHÔNG TỒN TẠI về mặt logic.

**(b) đúng, lý do domain rõ ràng:** hệ thống là CSKH ví điện tử tiếng Việt — xác suất một khách thật
nhắc số giấy phép hành nghề y tế Mỹ (định dạng recognizer này nhắm tới) trong tin nhắn xấp xỉ 0.
Recognizer này với dữ liệu của dự án **chỉ có thể sinh dương tính giả**, không có giá trị dương tính
thật nào để đánh đổi.

**[ĐO] khả thi kỹ thuật:** Presidio `RecognizerRegistry.remove_recognizer(recognizer)` nhận OBJECT,
không nhận tên chuỗi — cần lấy object trước (lọc theo `supported_entities` chứa `"MEDICAL_LICENSE"`
trong `registry.recognizers` sau khi `load_predefined_recognizers`, rồi gọi `remove_recognizer` với
object đó). Nguồn: thảo luận chính thức Microsoft Presidio repo.

**Áp DỮ NHẤT cho log/trace lẫn model-input — KHÔNG tách chính sách ở việc này.** Khác câu Spacy
PERSON/LOCATION (nơi tôi có lý do phân biệt bối cảnh vì đó là NHẦM LOẠI trên một PII THẬT), loại bỏ
MEDICAL_LICENSE không đánh đổi gì — không có PII thật nào phía sau nó ở domain này. Cùng lớp lý luận
đã dùng cho digit-filter: xoá nhiễu chưa từng là tín hiệu, không phải nới lỏng bảo vệ.

## 🔴 Phát hiện thêm — ĐỪNG dừng ở MEDICAL_LICENSE, đây là MỘT LỚP, không phải một ca

**[ĐO] `pii.py:275-279`:** danh mục predefined recognizer nạp cho "vi" gồm **Email · Phone · Iban ·
Crypto · Ip · Url · Date · MedicalLicense · MacAddress**. MEDICAL_LICENSE bị lộ ra vì nó TÌNH CỜ khớp
đúng dạng chuỗi số trong `TXN20260708000006`. Cùng cơ chế "khớp theo ĐỊNH DẠNG chuỗi, không theo ngữ
cảnh domain" áp cho các recognizer khác **có khả năng cao tương tự**:

- **`DateRecognizer`** — 🔴 rủi ro cao nhất: mã giao dịch dự án thường NHÚNG NGÀY THÁNG dạng
  `YYYYMMDD` ngay trong ID (`TXN20260708...`) — đây gần như chắc chắn TRÙNG khuôn một recognizer
  ngày tháng.
- **`PhoneRecognizer`**/`CryptoRecognizer` — chuỗi số/chữ-số dài trong mã nội bộ có thể trùng hình
  dạng số điện thoại quốc tế hoặc địa chỉ ví crypto tuỳ độ dài.
- Iban/Url/Mac/Email: khả năng thấp hơn (cần ký tự đặc trưng `@`/`http`/dấu `:` MAC mà mã nội bộ
  không có), không ưu tiên kiểm trước.

**Đề nghị: QA/QC chạy LẠI đúng corpus 124 câu, lần này liệt kê ĐỦ mọi `entity_type` xuất hiện trong
kết quả `analyzer.analyze()` (không chỉ đọc chuỗi kết quả cuối), rồi đối chiếu với danh mục 9
recognizer trên — biết CHÍNH XÁC recognizer nào đang góp vào 49,2%, thay vì đoán.** Đây rẻ (đọc lại
dữ liệu đã có, không cần lượt LLM mới) và đúng thứ tự phải làm TRƯỚC khi quyết định hướng thứ hai.

## 🔴 NIÊM 20/08 — bước 3 dưới đây ĐÃ LỖI THỜI, KHÔNG PHẢI vì sai mà vì SỰ KIỆN đi nhanh hơn kế hoạch. HOÃN đã được GIẢI, không phải bằng đo tiếp bước 3, mà bằng quyết định D' (file khác, sau đó cùng ngày).

**Bước 3 ("đo lại 62,1%→?,?% trên CHÍNH corpus 124 câu, sau bước 1+2") giả định kiến trúc VẪN LÀ "một
registry đầy đủ rồi lọc" — kiến trúc đó không còn tồn tại.** Cùng ngày 19/08, quyết định chuyển hẳn
sang HAI REGISTRY TÁCH BIỆT (ghi trong
`2026-08-19-scrub-ba-duong-va-kien-truc-tham-so.md`), rồi PO-agent đo trực tiếp bốn phương án A/D/B/D'
trên chính sự tách biệt đó (`2026-08-19-quyet-dinh-bien-du-lieu-regex-only-model-input.md`) — **KHÔNG
đi qua "bước 3" như tôi vạch ở đây.** Con đường thật đi TẮT qua đúng câu hỏi "giữ hay loại Spacy" mà
không cần đo riêng phần dư sau khi trừ Date/Phone/MedicalLicense — vì D (bỏ hẳn Spacy) và D' (bỏ Spacy
+ Date + Phone-chung) được đo TRỰC TIẾP, không cần suy ra từ phép trừ.

**HOÃN đã đóng — quyết định là D'.** File này KHÔNG có dòng nào tự khai điều đó (đúng Review chỉ ra)
— niêm tại đây để người đọc SAU không dừng lại ở "đang chờ đo bước 3" mà đi tìm quyết định thật ở
file kế tiếp. Không xoá kế hoạch cũ bên dưới — nó là dấu vết LẬP LUẬN đúng đắn tại THỜI ĐIỂM viết, chỉ
là thực tế diễn ra nhanh hơn, đi đường khác tới cùng đích.

---

## Quyết (2): HOÃN quyết "giữ/loại Spacy" — chưa đủ căn cứ để quyết BÂY GIỜ, không phải từ chối quyết

**Không né tránh câu hỏi — hoãn có lý do cụ thể, có điều kiện để hết hoãn:** 49,2% là con số ĐO
TRƯỚC KHI loại MEDICAL_LICENSE (và trước khi biết Date/Phone/Crypto có góp phần hay không). Nếu lớp
recognizer định dạng (không phải Spacy) đang gánh một phần đáng kể của 49,2% — như chính ca
MEDICAL_LICENSE vừa chứng minh nó CÓ góp phần — thì **con số 49,2% không phải là "phần Spacy gây
ra"**, nó là gộp của ÍT NHẤT HAI cơ chế khác nhau. Quyết "loại Spacy" trên một con số chưa tách được
nguồn là lặp đúng lỗi Luật F/N của dự án: **mẫu số/nguồn gốc không tách trước khi kết luận.**

**Trình tự đề nghị, không đổi so với lần trước, chỉ cụ thể hoá:**
1. Loại `MEDICAL_LICENSE` (quyết xong, làm ngay — mục 1).
2. Kiểm nhanh Date/Phone/Crypto trên corpus (mục "phát hiện thêm") — loại tiếp nếu xác nhận cùng lớp.
3. **Đo lại 62,1%→?,?% trên CHÍNH corpus 124 câu, sau bước 1+2** — đây mới là con số phản ánh ĐÚNG
   phần còn lại do Spacy PERSON/LOCATION/ORGANIZATION gây ra.
4. **CHỈ SAU KHI có con số bước 3, quay lại quyết định giữ/loại Spacy** — nếu con số đã tụt xuống một
   mức chấp nhận được (cần Lead/PO thật định nghĩa ngưỡng "chấp nhận được" là bao nhiêu, không phải
   quyết định của tôi), có thể không cần phẫu thuật lớn (loại hẳn Spacy, mất case "Trần Thị Bích").
   Nếu vẫn cao, quay lại phương án loại Spacy hoặc ngưỡng `score` như đã đề xuất.

**Không phải trì hoãn vô thời hạn** — bước 1+2 rẻ và làm được ngay hôm nay, không chặn tiến độ đáng
kể. Tôi tin bước 3 sẽ cho một con số rõ ràng để quyết dứt điểm, thay vì quyết bây giờ trên một mẫu số
đã biết là trộn nhiều nguồn.

## Ghi nhận ca hồi quy "Trần Thị Bích" ĐẠT cả hai bản — đúng vai trò của nó

Xác nhận đây là mốc nền đúng cách QA/QC đã dựng — không cần thêm gì, giữ nguyên trong bộ ca chạy lại
ở bước 3 để biết ngay nếu hướng vá cuối cùng (dù chọn gì) vô tình làm nó trượt.

---

## NIÊM 19/08 (sau) — breakdown thật đã về. Dự đoán "Phone/Date đáng nghi" ĐÚNG MỘT NỬA, SAI MỘT NỬA — khai cả hai, không chỉ khai phần đúng.

**[ĐO] Lead, breakdown entity_type trên corpus sau `dec5335+45618f3`:**
```
PERSON 43 câu · LOCATION 27 · ORGANIZATION 12 · PHONE_NUMBER 8 · VN_ID_NUMBER 6
DATE_TIME 6 (Lead ghi rõ: "ngày thật, hợp lý") · VN_PHONE_NUMBER 5 · PERSON_VN 1
```

**Dự đoán của tôi về `DateRecognizer` SAI — khai thẳng, không giấu phần trật.** 6 lần `DATE_TIME`
đều là ngày THẬT, không phải dương tính giả — tôi đoán sai vì suy luận tĩnh (mã giao dịch nhúng
YYYYMMDD) mà chưa đo, đúng lớp lỗi Luật M của dự án: *suy luận không thay được số đo.* Không cần vá
gì cho DateRecognizer.

**Dự đoán về `PhoneRecognizer` ĐÚNG, và tệ hơn hình dung ban đầu — [ĐO] Lead xác nhận, tôi không tự
đo lại được (không có quyền chạm phép đo QA/QC), nhưng LOGIC của ca này đủ để quyết ngay:**
```
scrub_pii('chuyen ra VPB 393.000 ma sai stk nguoi nhan, nho kiem tra')
  → '[PERSON] VPB [PHONE_NUMBER] ma sai stk nguoi nhan, nho kiem tra'
```
**SỐ TIỀN bị nhận nhầm thành SĐT.** Đây là dữ liệu TRUNG TÂM của mọi khiếu nại giao dịch — nặng hơn
hẳn `MEDICAL_LICENSE` (gần như 0 xác suất xuất hiện thật ở domain này).

### QUYẾT: loại bỏ `PhoneRecognizer` (built-in, generic) khỏi registry — CÙNG LÝ LUẬN đã áp cho `MEDICAL_LICENSE`, không phải một quyết định mới

**[ĐO] `_FALLBACK_PHONE_RE` (`pii.py:73`) và `_VN_PHONE_REGEX` (`pii.py:97`) LÀ CÙNG MỘT PATTERN**
(`(?<![\w-])(?:\+84|0)\d{9}(?!\d)`) — dự án ĐÃ CÓ recognizer chuyên SĐT Việt Nam, tách biệt hoàn toàn
khỏi `PhoneRecognizer` (built-in, đa quốc gia, dùng thư viện định dạng quốc tế) đang gây lỗi. Loại bỏ
`PhoneRecognizer` KHÔNG mất khả năng phát hiện SĐT Việt Nam thật — `VN_PHONE_NUMBER` vẫn đứng nguyên,
độc lập, không đổi.

**Một điểm cần Coder kiểm nhanh trước khi loại hẳn (không phải điều kiện chặn, chỉ một câu hỏi rẻ):**
`VN_PHONE_NUMBER` đòi khớp CHÍNH XÁC `\d{9}` liền mạch, không dấu cách/gạch ngang. Nếu khách gõ SĐT
có định dạng rời (`091 234 5678` / `091-234-5678`) — liệu `PhoneRecognizer` built-in có đang bắt được
những ca ĐÓ mà `VN_PHONE_NUMBER` bỏ lỡ? Nếu QA/QC xác nhận KHÔNG có ca nào trong corpus thuộc dạng
này, loại bỏ ngay, không cần chờ. Nếu CÓ, cân nhắc nới `_VN_PHONE_REGEX` chấp nhận dấu cách/gạch
ngang tuỳ chọn, THAY VÌ giữ lại `PhoneRecognizer` đa quốc gia để đổi lấy noise trên số tiền.

### 🔴 ĐIỂM CẦN LÀM RÕ NGAY — "Phương án B" của tôi và "phương án đang có PhoneRecognizer" của Lead CÓ THỂ là HAI THỨ KHÁC NHAU

**[ĐO]** `scrub_regex()` (`pii.py:77-84`) — hàm tôi đã duyệt cho Phương án B trong quyết định biên dữ
liệu — chỉ gọi BA regex tự viết (`_FALLBACK_EMAIL_RE/_FALLBACK_PHONE_RE/_FALLBACK_ID_RE`), **KHÔNG hề
chạm registry Presidio, KHÔNG hề gọi `PhoneRecognizer`/`MEDICAL_LICENSE`/bất kỳ recognizer built-in
nào.** Nếu B được triển khai ĐÚNG BẰNG hàm này (như PO-agent đã đo và tôi đã duyệt), lỗi
`PhoneRecognizer`-nhận-nhầm-số-tiền **KHÔNG chạm đường model-input** — nó chỉ tồn tại ở đường log/
trace (nơi vẫn dùng `scrub_pii()` đầy đủ).

Lead viết *"ngay cả phương án B vẫn dùng PhoneRecognizer"* — nếu điều này đúng, nghĩa là bản triển
khai THẬT của B đang đi qua một đường KHÁC với `scrub_regex()` tôi đã duyệt (có thể là lọc registry
Presidio chỉ bỏ nhãn NER, giữ lại mọi pattern recognizer built-in). **Đề nghị Lead xác nhận: B đang
triển khai bằng `scrub_regex()` thuần, hay bằng một đường khác?** Nếu là đường khác — đó là một
QUYẾT ĐỊNH TRIỂN KHAI chưa được tôi duyệt, cần xác nhận lại (không nhất thiết sai, nhưng cần khai rõ
nó khác gì với B tôi đã ký).

**Dù câu trả lời là gì, quyết định loại `PhoneRecognizer` ở trên VẪN ĐÚNG và VẪN CẦN LÀM** — nó luôn
đúng cho log/trace, và nếu B triển khai qua đường Presidio-registry thì nó cũng cần cho model-input.

## ORGANIZATION (VTB/VPB) — KHÔNG cần quyết riêng, đã có chỗ đứng: gộp vào câu hỏi Spacy đang chờ (Phương án D)

Đúng như Lead nói, đây không phải PII cá nhân — nhưng tôi KHÔNG tách nó ra quyết riêng, vì gốc của nó
là CÙNG một nguồn với PERSON/LOCATION (Spacy gán nhãn sai trên văn bản tiếng Việt, đa ngôn ngữ không
chuyên) — tách lẻ từng nhãn của Spacy ra quyết từng cái là vá triệu chứng, không phải vá gốc. Câu này
đã có chỗ đứng: nằm trong phạm vi đo của Phương án D (regex+underthesea, không Spacy) đã yêu cầu ở
quyết định trước — nếu D được chọn, ORGANIZATION-sai của Spacy tự động biến mất cùng PERSON/LOCATION.
Nếu B (loại hẳn NER) được giữ, câu hỏi này cũng tự động đóng theo cách khác — không NER nào chạy nên
không có ORGANIZATION nào để bàn. Không cần một quyết định thứ ba song song.
