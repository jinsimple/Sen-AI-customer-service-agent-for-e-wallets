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
