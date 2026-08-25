# Finding P0 · live-chat lưu PII thô — BA MỨC CHE, PO chọn một

> **Người chuẩn bị:** Coder (`p-226-63`), 25/08. **Người quyết:** PO thật.
> **Trạng thái:** ⛔ **CHƯA VÁ MỘT DÒNG NÀO** — chờ chữ ký. Cổng CI `security-findings-gate`
> đang đỏ **đúng chức năng**.
> Tài liệu ràng buộc: *"không được che tới mức CSKH mất khả năng gọi lại khách"*
> ⟹ **quyết định của PO, không phải việc kỹ thuật.**

## 1. Lỗ là gì — đo, không khái quát

```
src/services/live_chat.py:102 record_message(...)
  content: str  →  Message(content=content)  →  session.add()
  KHÔNG có bước scrub/mask nào giữa hai đầu.
```
`Message.content` **có** mã hoá at-rest (`EncryptedText`, cùng khoá `PolicyChunk.text`).
⟹ File CSDL trên đĩa **không** chứa số thô. Lỗ nằm ở **đường ĐỌC**: audit log, export, DSAR
PDPA, và bất cứ ai có quyền đọc bản ghi đã giải mã.

⟹ 🔴 **Đây là lỗ PHƠI RA (exposure), không phải lỗ LƯU TRỮ (at-rest).** Phân biệt này quyết
định mức nào vá đúng chỗ.

## 2. 🔴 DỮ KIỆN LÀM TAN MỘT NỬA NỖI LO — CSKH KHÔNG LẤY SỐ TỪ KHUNG CHAT

```
[ĐO] src/db/models.py:52   users.phone   nullable=False, unique=True   ⟹ MỌI khách đều có
[ĐO] src/services/live_chat.py:183  get_handoff_context() trả cho CSKH:
       "customer": {user_id, full_name, phone}      ← SỐ THẬT, KHÔNG CHE, ngay lúc nhận ca
```
⟹ **Khả năng gọi lại khách KHÔNG phụ thuộc khung chat.** Nó đi qua một đường riêng đã tồn tại.
Che số trong chat **không** làm CSKH mất khả năng gọi lại **khách hàng** — chỉ mất trong hai ca:

| ca | mất gì | có đáng giữ không |
|---|---|---|
| khách cho **số KHÁC** số tài khoản (*"gọi mình số này"*) | mất số liên hệ thay thế | ⚠️ **có** — đây là mất mát THẬT |
| khách gõ số **NGƯỜI THỨ BA** (người nhận nhầm) | mất số bên thứ ba | 🔴 **KHÔNG** — BR-06 nói phải che; giữ nguyên văn mới là sai |

## 3. Ba mức — số liệu **đo thật**, không phải ví dụ nghĩ ra

```
[ĐO] pwd=/Users/soidoc/Code/Projects/P-226 · chạy scrub_regex()/mask_phone() trên câu thật
```

### M1 — scrub toàn phần (`src/observability/pii.py::scrub_regex`, đã có sẵn)
```
"…qua số 0987654321 nhé"          →  "…qua số [PHONE] nhé"
"Số tài khoản của mình là 88000000000001"  →  "…là [ID_NUMBER]"
```
🔴 **Giá phải trả, ĐO ĐƯỢC, không suy đoán** — khuôn `\d{9,19}` ăn cả thứ không phải PII:
```
"Mình chuyển 1500000000 đồng mà chưa thấy vào."  →  "…chuyển [ID_NUMBER] đồng…"   ← MẤT SỐ TIỀN
"Mã đơn hàng 202608251234 chưa hoàn tiền."       →  "…đơn hàng [ID_NUMBER]…"      ← MẤT MÃ ĐƠN
"Mình chuyển 393000 đồng"                         →  giữ nguyên (6 chữ số, dưới ngưỡng)
```
⟹ Khách gõ số tiền **không dấu phân cách** từ 9 chữ số trở lên *(≥ 100 triệu)* thì **chính số
tiền khiếu nại bị xoá** — thứ CSKH cần nhất.

### M2 — che một phần, giữ 4 số cuối (`src/tools/masking.py::mask_phone`, đã có sẵn)
```
"…qua số 0987654321 nhé"   →  "…qua số 098***4321 nhé"
"…tài khoản 88000000000001" →  KHÔNG ĐỔI     ← 🔴 M2 chỉ chạm SĐT
```
⟹ CSKH **không bấm gọi được** `098***4321`, chỉ **đối chiếu** được với số lấy từ nơi khác.
🔴 **M2 KHÔNG đóng được finding**: test P0 nói *"số tài khoản"*, mà M2 không chạm số tài khoản.

### M3 — che ở tầng ĐỌC, lưu đủ *(đúng nguyên tắc BR-07 đang có trong repo)*
```
src/tools/masking.py:3  "masking chỉ xảy ra ở TẦNG NÀY (tool/API). DB … luôn lưu bản đầy đủ.
                         Không bao giờ lưu sẵn bản đã che vào DB."
```
Lưu nguyên văn (đã mã hoá at-rest), che khi **hiển thị / export / audit log**.

## 4. 🔴 XUNG ĐỘT PO PHẢI BIẾT TRƯỚC KHI CHỌN

**Test P0 đòi che TRƯỚC KHI LƯU. BR-07 trong repo cấm đúng điều đó.** Hai văn bản của cùng
dự án đang nói ngược nhau, và **không ai phát hiện vì chưa ai vá.**

Và một tính chất **không đảo lại được**:
> BR-07 che ở tầng đọc **được phép** vì bản đầy đủ vẫn nằm trong `users`/`bank_accounts`.
> **Khung chat KHÔNG có bản đầy đủ ở đâu khác.** Che lúc ghi ⟹ **mất vĩnh viễn**, không ai
> khôi phục được — kể cả khi sau này cần chính câu ấy để phân xử một khiếu nại.

## 5. Khuyến nghị của tôi — và ranh giới của nó

**Tôi khuyến nghị M3**, ba lý do:
1. Lỗ là lỗ **phơi ra** (§1) — mọi đường phơi ra đều là đường **ĐỌC**. M3 vá đúng chỗ lỗ nằm.
2. Nó **không mâu thuẫn** BR-07 đã có; M1/M2 thì có.
3. M1 **ăn mất số tiền khiếu nại** (§3, đo được) — hỏng theo hướng khó thấy: transcript vẫn
   trông bình thường, chỉ thiếu đúng con số quan trọng nhất.

🔴 **Nhưng M3 KHÔNG làm test P0 hiện tại xanh** — test đó chấm **giá trị đã lưu**. Nên nếu PO
chọn M3 thì **bắt buộc kèm**: sửa test P0 sang chấm **đường đọc**, và thêm test khẳng định
bản lưu vẫn đủ. Không có vế sau thì việc sửa test **không phân biệt được** với đi vòng qua cổng.

> **Phép thử để phân biệt, dùng luôn khi nghiệm thu:** *sau khi vá, có còn một test nào FAIL
> nếu ai đó gỡ bước che đi không?* Có ⟹ cổng còn sống. Không ⟹ ta vừa gỡ cổng, không vừa vá lỗ.

⛔ **Tôi không tự chọn, và không vá dòng nào trước khi có chữ ký.** Mức che là quyết định của
PO — che quá tay thì CSKH **không giúp được khách đang cần giúp**, và đó là hỏng theo hướng
khó nhìn thấy hơn hẳn.
