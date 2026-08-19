# scrub_pii có BA đường, không phải hai — định hạng `main.py:1086` + kiến trúc tham số

> 19/08/2026 khuya. [ĐO] đọc trọn context `main.py:1065-1099` trước khi định hạng.

## Xác nhận "Tuần" KHÔNG tự đóng theo D' — đã tự kết luận giống Lead trước khi thấy tin nhắn

[ĐO] `pii.py:229` (`_underthesea_person_spans`) gọi `_plausible_person_span` — CÙNG hàm, CÙNG
`_TU_THUONG_BI_NHAN_NHAM_LA_TEN` mà Spacy dùng. D' bỏ Spacy, GIỮ underthesea ⟹ lỗ "Tuần" sống nguyên
dưới D'. Quyết định đã ra trước khi thấy tin nhắn Lead (niêm `299215a`): **GIỮ "tuần" trong stoplist,
khai rõ, thêm rào tự-hỏi cho từ mới** — xem toàn văn ở
`2026-08-19-gd4-dinh-hang-scrub-pii-model-input.md`. Không đổi.

## `main.py:1086` — định hạng: thuộc nhóm LOG/TRACE (giữ nguyên `scrub_pii` đầy đủ), KHÔNG áp D'

**[ĐO] đọc trọn `main.py:1077-1096`, ADR-024:** đây là `resolution.note` — lý do TỪ CHỐI một đề xuất,
do **NHÂN VIÊN** (cskh/supervisor) gõ, ghi vào DATABASE cùng dữ liệu kiểm toán, **KHÔNG BAO GIỜ gửi
cho bất kỳ LLM/nhà cung cấp bên ngoài nào**. Ba khác biệt quyết định phân loại:

1. **Đường ra khác hẳn model-input.** Toàn bộ lý do D' tồn tại (agent cần hiểu ĐÚNG để tra cứu, gọi
   tool, trả lời khách) không áp dụng ở đây — không có model nào đọc trường này để RA QUYẾT ĐỊNH gì,
   chỉ có SUPERVISOR KHÁC đọc lại để hồi cứu. Con người dung nạp một `[PERSON_VN]` lạc chỗ tốt hơn
   nhiều so với một agent cần tra đúng mã giao dịch.
2. **Ai viết khác hẳn.** Model-input là lời KHÁCH gõ; đây là lời NHÂN VIÊN gõ — rủi ro không phải
   "khách nhắc tên bên thứ ba" mà là "nhân viên vô tình chép tên/SĐT khách vào lý do từ chối" — đúng
   loại PII cần bảo vệ TỐI ĐA, không phải tối ưu độ chính xác.
3. **Chính code đã tự khai mức độ cẩn trọng mong muốn** — `:1087-1092`, scrub LỖI thì **FAIL-CLOSED,
   chặn cả việc ghi** thay vì lưu bản thô. Đây là tín hiệu THIẾT KẾ GỐC (ADR-024) đã chọn hướng cẩn
   trọng tối đa cho trường này — khớp đúng bản chất "log/audit", không khớp bản chất "model-input cần
   độ chính xác cao".

**KẾT LUẬN: `main.py:1086` giữ nguyên `scrub_pii()` đầy đủ (regex+Spacy+underthesea+MEDICAL_LICENSE-
đã-loại+Phone-generic-đã-loại — tức bản LOG/TRACE sau khi dọn hai recognizer nhiễu, KHÔNG áp riêng D'
scope-hẹp).** Không phải "biến trang trí ăn theo mặc định" — có lý do phân loại rõ, đã viết ra.

## Kiến trúc tham số của PO-agent — ĐỒNG Ý HƯỚNG, đề nghị một điều chỉnh AN TOÀN HƠN cho cách triển khai

**Đồng ý:** một nguồn cấu hình, không chép hai bảng recognizer thành hai bản riêng để rồi trôi theo
thời gian (đúng đề nghị PO-agent, đúng tinh thần đã áp cho lock-file/base-image cả ngày hôm nay).

**🔴 Đề nghị điều chỉnh — XÂY HAI REGISTRY TƯỜNG MINH, không phải MỘT registry + lọc theo `muc_dich`
sau khi phân tích xong:**

Lý do cụ thể, không phải sở thích kiến trúc: **cả HAI lỗ đã vá hôm nay đều CÙNG MỘT HÌNH DẠNG LỖI —
"quên áp một bước lọc cho MỘT nhánh"** (`_plausible_person_span` ban đầu chỉ áp underthesea, quên
Spacy — vá lúc `df186c0`; và chính khả năng quên loại MEDICAL_LICENSE/PhoneRecognizer cho một đường
mà áp cho đường kia). Một hàm DÙNG CHUNG registry đầy đủ rồi LỌC KẾT QUẢ theo `muc_dich` **tái tạo
đúng cấu trúc rủi ro đó** — dễ quên lọc đúng cho một nhánh, lỗi chỉ lộ ra khi có ai đó test đúng case.

**Đề xuất cụ thể:** MỘT hàm dùng chung dựng RECOGNIZER (ví dụ `_dung_recognizer_vn_phone()`,
`_dung_recognizer_vn_id()`, `_dung_vietnamese_name_recognizer()` — logic tạo từng recognizer chỉ viết
MỘT LẦN), nhưng HAI HÀM DỰNG REGISTRY riêng biệt gọi các mảnh dùng chung đó theo danh sách KHÁC NHAU
tường minh:
```python
def _registry_model_input() -> RecognizerRegistry:   # D': KHÔNG nạp Spacy/Date/Phone-generic/MedicalLicense
def _registry_log_trace() -> RecognizerRegistry:       # đầy đủ, trừ MedicalLicense/Phone-generic (đã loại vĩnh viễn)
```
Mỗi registry **KHÔNG NẠP** recognizer bị loại trừ ngay từ đầu — không có bước "chạy rồi lọc bỏ kết
quả", nên không có gì để QUÊN lọc. `scrub_pii(text, muc_dich=...)` chọn registry tương ứng (cache
riêng từng cái qua `@lru_cache`), không dùng chung MỘT registry rồi rẽ nhánh sau khi có kết quả.

**Đắt hơn một chút** (nạp hai registry thay vì một, dù registry nhẹ nhất — model-input — bỏ hẳn
Spacy nên khởi tạo còn NHANH HƠN registry đầy đủ) — **đổi lại loại bỏ hẳn một lớp lỗi đã cắn dự án
hai lần trong một ngày.** Đáng.

## Ba đường, ba chính sách — chốt bảng cho Coder

| đường | `muc_dich` | registry |
|---|---|---|
| `graph.py:787` (tin khách → model) | `"model_input"` | D': regex + underthesea + VN_PHONE/VN_ID, KHÔNG Spacy/Date/Phone-generic/MedicalLicense |
| `langchain_callback.py:65` (trace/observability) | `"log"` | đầy đủ, trừ MedicalLicense + Phone-generic (loại vĩnh viễn, cả hai đường) |
| `main.py:1086` (ghi chú nhân viên → DB) | `"log"` | như trên — cùng nhóm log/trace, KHÔNG áp D' |

Không kết luận: ❌ có đường thứ tư nào khác chưa lộ ra — chỉ xác nhận đủ ba đường đã biết hôm nay.
