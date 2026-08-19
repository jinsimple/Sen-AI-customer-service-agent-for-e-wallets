# GĐ4 — định hạng scrub PII cho đầu vào gửi model (chặn Coder, trả lời nhanh)

> 19/08/2026. Đọc trọn `src/observability/pii.py` trước khi trả lời — xác nhận từng dòng Lead trích,
> không nhận nguyên văn. Coder đang chờ, trả lời ngay khi có kết luận, không giữ lại để viết dài.

## Xác nhận [ĐO] của Lead — ĐÚNG 100%, đã đọc tận mã

```
pii.py:190   _underthesea_person_spans() → CÓ gọi _plausible_person_span(token)
pii.py:294-298  scrub_pii(): kết quả Spacy (results = analyzer.analyze(...)) đi THẲNG vào raw_spans
                → KHÔNG qua _plausible_person_span ở đâu cả
pii.py:44-50 docstring: "chấp nhận over-redact, không nới lỏng để giảm false positive" — nguyên văn
```

## KHÔNG đồng ý với khung "tách hai chính sách" của brief — đề nghị NGƯỢC LẠI: áp lọc THỐNG NHẤT cho cả hai đường, không tách

Đây là điểm tôi lệch với brief, nói rõ ngay để Coder không viết nhầm hướng. Lý do:

**`_plausible_person_span` không phải một sự NỚI RỦI RO — nó là một CHỈNH SỬA MÔ TẢ ĐÚNG BẢN CHẤT.**
Quy tắc "có chữ số ⟹ không phải tên người" không làm giảm khả năng phát hiện PII THẬT — nó chỉ dừng
việc gán nhãn PERSON/LOCATION/ORGANIZATION cho những chuỗi CHƯA TỪNG LÀ PII (mã giao dịch, viết tắt
toàn hoa). Khác hẳn tình huống "chấp nhận over-redact" gốc — tình huống đó nói về Spacy **gán SAI
LOẠI cho một PII THẬT** (tên người bị gọi nhầm là LOCATION, nhưng vẫn LÀ PII, vẫn ĐÁNG che). Hai
tình huống khác bản chất:

| | Spacy gán sai LOẠI cho PII thật ("Nguyễn Văn A" → LOCATION) | Spacy/underthesea gán nhãn PERSON cho KHÔNG-PHẢI-PII ("TXN...352", "Mã") |
|---|---|---|
| Có nên che? | CÓ — vẫn là PII, chỉ sai tên loại | KHÔNG — chưa từng là PII |
| Rủi ro nếu sửa sai hướng | Bỏ lọt PII thật | Phá dữ liệu nghiệp vụ (đúng lỗi PO thật vừa bắt) |
| `_plausible_person_span` đụng vào cái nào? | KHÔNG đụng (không lọc theo LOẠI nhãn) | ĐÚNG cái này (lọc theo HÌNH DẠNG span: có số/toàn hoa) |

`_plausible_person_span` chỉ hoạt động ở dòng thứ hai của bảng — nó KHÔNG đá vào quyết định "over-
redact khi sai loại" ở dòng thứ nhất, hai cơ chế độc lập với nhau trong cùng file. **Không có gì
trong bản vá đề xuất làm YẾU đi khả năng che PII thật — chỉ dừng việc che nhầm thứ chưa từng là PII.**
⟹ **Không cần tách chính sách theo bối cảnh (log vs model-input) cho ĐÚNG hai bản vá này** — cả hai
nên áp UNIFORM cho `scrub_pii()`, một chỗ sửa, cả log/trace lẫn model-input cùng đúng hơn, không
đường nào mất gì.

## Xác nhận an toàn — bảo vệ PII THẬT không phụ thuộc cơ chế đang sửa

**[ĐO] `pii.py:241-254`:** SĐT/CCCD/số tài khoản VN được che bởi HAI `PatternRecognizer` RIÊNG
(`VN_PHONE_NUMBER`/`VN_ID_NUMBER`, regex chuyên biệt) — **độc lập hoàn toàn** với logic
PERSON/LOCATION/ORGANIZATION đang sửa. Nới lọc cho nhóm PERSON/LOCATION/ORGANIZATION **không đụng**
tới hai recognizer này. Một số điện thoại thật trong tin nhắn khách vẫn bị che dù bản vá này chạy —
đã kiểm bằng đọc code, không suy đoán.

**Vì sao filter không thể vô tình bỏ lọt TÊN NGƯỜI thật:** `_plausible_person_span` chỉ loại một span
khi nó **có chữ số HOẶC toàn chữ hoa HOẶC khớp đúng một đại từ trong danh sách đóng**. Tên người tiếng
Việt tự nhiên trong tin nhắn khách hàng thoả CẢ BA điều kiện loại trừ đó gần như KHÔNG BAO GIỜ (không
chữ số, không viết hoa toàn bộ, không phải một đại từ). Áp thêm cho Spacy không đổi kết quả trên MỘT
tên người thật nào — chỉ đổi kết quả trên các chuỗi vốn dĩ không phải tên.

## Hai bản vá riêng biệt — Coder cần biết là HAI cơ chế, không phải một

1. **`_plausible_person_span` (đã có, mở rộng phạm vi áp dụng):** lọc theo HÌNH DẠNG (số/hoa toàn
   phần) — sửa case `TXN...352 → [PERSON]`. Áp cho `raw_spans` TRƯỚC khi merge, không phân biệt
   nguồn recognizer (Spacy hay underthesea).
2. **Stoplist từ thông thường (mới, cùng khuôn `_DAI_TU_KHONG_PHAI_TEN`):** sửa case `Mã →
   [PERSON_VN]` — đây là **underthesea, ĐÃ qua `_plausible_person_span`, VẪN lọt** vì "Mã" không có
   số/không viết hoa/không phải đại từ đã liệt kê. Cơ chế đúng: một danh sách từ thường bị NER gán
   nhầm nhãn người — **nhưng khác `_DAI_TU_KHONG_PHAI_TEN` ở một điểm quan trọng: danh sách này KHÔNG
   ĐÓNG.** Đại từ tiếng Việt là tập hữu hạn liệt kê hết được; "từ thông thường có thể bị NER nhận
   nhầm" thì không — sẽ còn phát sinh case mới sau "Mã". Đề nghị Coder ghi rõ trong code đây là danh
   sách MỞ, cần cập nhật khi phát hiện case mới (đúng cam kết chính docstring `pii.py:54-55` đã viết
   cho underthesea: *"nếu phát sinh, cập nhật ghi chú này, không âm thầm giữ nguyên"*).

## Trả lời thẳng câu brief hỏi

> *"đường graph.py:787 có nên giữ over-redact, hay cần chính sách RIÊNG"*

**Không cần chính sách riêng cho hai bản vá NÀY.** Cả hai là sửa lỗi hình dạng (digit/hoa/từ-thường-
gặp), áp đúng như nhau ở mọi nơi `scrub_pii()` được gọi. **Chính sách "chấp nhận over-redact khi Spacy
gán SAI LOẠI" (khác hẳn hai bản vá trên) giữ nguyên, không đụng, không tách** — nó chưa từng là vấn đề
brief đang mô tả.

Nếu sau này phát sinh một nhu cầu THẬT SỰ cần tách chính sách theo bối cảnh (ví dụ: muốn model-input
CHẤP NHẬN rủi ro lọt PII loại hiếm để đổi lấy độ chính xác cao hơn) — đó là một quyết định RỦI RO
THẬT, cần một trang riêng, không nên lẫn vào đợt vá lỗi hình dạng hôm nay.

## KHÔNG kết luận

❌ log/trace và model-input cần hai hàm scrub riêng — không cần cho hai bản vá này. ❌ nới lỏng làm
giảm bảo vệ PII thật — đã xác nhận độc lập bằng đọc code (regex SĐT/CCCD tách biệt) và bằng lý luận
hình dạng (tên người thật không thoả điều kiện loại trừ).

**Ca đối chứng bắt buộc trước khi land (đúng §4 brief đã có, xác nhận lại):** tên người thật, SĐT,
CCCD trong tin nhắn khách VẪN phải bị che sau bản vá — chạy cả hai chiều (dương: TXN/Mã không còn bị
che; âm: PII thật vẫn bị che) trước khi merge.

---

## 🔴 NIÊM 19/08 (sau) — dữ kiện MỚI làm bản vá đề xuất ở trên KHÔNG ĐỦ. Không rút phần đã đúng, thêm phần còn thiếu.

**[ĐO] PO-agent, tôi không tự kiểm lại được số (không chạm được `scrub_pii()` thật từ đây), nhưng
LOGIC của ca này tự nó đủ để đổi kết luận, không cần tôi verify lại con số:**
```
scrub_pii('Giao dịch bị treo mấy ngày rồi')  →  'Giao dịch bị treo mấy [LOCATION] rồi'
```
**"ngày" KHÔNG có chữ số, KHÔNG viết hoa toàn phần, KHÔNG phải đại từ trong danh sách đóng.** Ba
điều kiện của `_plausible_person_span` — thứ tôi vừa đề nghị mở rộng cho Spacy ở phần trên — **KHÔNG
LOẠI ĐƯỢC CASE NÀY.** Bản vá tôi đề nghị (mở rộng digit/hoa-toàn-phần filter) vẫn ĐÚNG cho đúng phạm
vi nó giải quyết (mã giao dịch, viết tắt toàn hoa) — **nhưng phạm vi đó hẹp hơn thứ đang thật sự xảy
ra.** Đây không phải lỗi hiếm gặp ở dữ liệu có cấu trúc (mã/số) — đây là `SpacyRecognizer`
(`xx_ent_wiki_sm`, mô hình ĐA NGÔN NGỮ, KHÔNG chuyên tiếng Việt — chính docstring `pii.py:30-32` đã
tự khai điều này) gán nhãn sai trên TỪ TIẾNG VIỆT THÔNG THƯỜNG, tần suất cao (~12% mẫu nhỏ ban đầu,
chờ corpus lớn hơn).

### Sửa định hạng mức độ — nâng lên, đúng như Lead cảnh báo

Không phải "phá mã giao dịch" (ca hiếm, đã có bản vá đúng) mà là **"agent nhận đầu vào bị bóp méo
trên một phần đáng kể MỌI cuộc hội thoại"** — đây là mức ảnh hưởng THÔNG LƯỢNG (chạm phần lớn tương
tác), không phải mức TẦN SUẤT THẤP-HẬU QUẢ CAO như finding O4 trước đó. Đúng loại severity khác, cần
xử lý khác — vá cục bộ (thêm từng từ vào stoplist) sẽ không đuổi kịp một tỉ lệ nền cao thế này.

### Đề nghị sửa hướng — từ "mở rộng bộ lọc" sang "cân nhắc GIỚI HẠN VAI TRÒ của Spacy cho đường model-input"

**Đây LÀ một trường hợp đáng tách chính sách theo bối cảnh** — đúng điều tôi viết ở trên là "nếu có
nhu cầu THẬT SỰ... cần một trang riêng." Dữ kiện mới chính là nhu cầu thật đó.

- **Log/trace:** giữ nguyên Spacy + toàn bộ pipeline như cũ — over-redaction chấp nhận được, đúng
  chính sách gốc.
- **Model-input (`graph.py:787`):** cân nhắc KHÔNG dùng nhãn PERSON/LOCATION/ORGANIZATION từ
  `SpacyRecognizer` cho đường này — dựa vào `_VietnameseNameRecognizer` (underthesea, chuyên tiếng
  Việt) + hai `PatternRecognizer` định dạng (SĐT/CCCD, không phụ thuộc NER nên không có noise này) là
  đủ cho đường model-input, tránh đúng nguồn nhiễu (mô hình đa ngôn ngữ không chuyên Việt).

**Đánh đổi phải nói thẳng, không giấu:** docstring `pii.py:51-53` tự ghi nhận MỘT case cụ thể
("Trần Thị Bích") mà Spacy bắt được còn underthesea bỏ sót. Loại Spacy khỏi đường model-input ⟹ case
dạng đó (nếu tái diễn) sẽ KHÔNG bị che khi vào model — mất một lớp bảo vệ hiếm nhưng có thật, để đổi
lấy việc không bóp méo ~12% hội thoại thường ngày. **Tôi cho rằng đánh đổi này ĐÁNG làm** (một lớp
bảo vệ hiếm, có lớp regex SĐT/CCCD định dạng đứng độc lập phía sau nó, đổi lấy việc không phá hỏng
một phần lớn tương tác hằng ngày) — nhưng đây là NHẬN ĐỊNH, cần corpus lớn hơn của QA/QC xác nhận quy
mô thật trước khi chốt, không phải quyết định dựa trên 8 câu mẫu.

**Một hướng thứ ba đáng thử trước khi loại hẳn Spacy (rẻ hơn, chưa xác nhận được):** Presidio trả
`score` cho mỗi kết quả nhận diện — nếu các lần Spacy gán nhầm ("ngày"→LOCATION) có điểm tin cậy THẤP
hơn rõ rệt so với lần nhận diện đúng, đặt một ngưỡng `score` tối thiểu cho riêng đường model-input có
thể giữ được phần lớn giá trị của Spacy mà lọc bớt nhiễu — **tôi KHÔNG xác nhận được điều này từ đọc
code, cần Coder đo thật trên chính corpus QA/QC đang dựng trước khi chọn hướng.**

### Trả lời câu hỏi của Lead — thêm gì vào tiêu chí đối chứng

**Bắt buộc thêm MỘT ca cụ thể, không phải chung chung "PII vẫn bị che":** một câu chứa đúng dạng tên
người mà **CHỈ Spacy bắt được, underthesea bỏ sót** (mẫu gần nhất với case "Trần Thị Bích" đã ghi
trong docstring — nếu corpus không có case y hệt, QA/QC cần một câu tương tự cấu trúc). Đây là ca
**hồi quy** — bất kỳ hướng vá nào chọn (giới hạn Spacy / thêm ngưỡng score / mở rộng stoplist) đều
PHẢI chạy qua ca này và biết rõ nó ĐẠT hay TRƯỢT, không được bỏ qua vì "hiếm gặp". Nếu hướng vá cuối
cùng làm ca này TRƯỢT — đó là đánh đổi có Ý THỨC cần ghi vào hồ sơ, không phải một hồi quy im lặng.
