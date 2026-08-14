# Mốc nền C4 — đo TRƯỚC khi coder vá (BOLA `/tools/lookup_transaction`)

> Vai: **security** · 2026-08-14 · nhánh `dev/learning-loop`
> Mục đích: có **cặp đo** thật (trước/sau) cho lượt rà C4, thay vì chỉ xác
> nhận sau vá. Toàn bộ probe **chỉ đọc**, không đổi dữ liệu; 3 challenge OTP
> do probe tạo đã xoá.
>
> Giao dịch thử `TXN20260411000001` (`from_bank`): chủ **tài khoản ngân hàng**
> gửi = `USR-0156` · chủ **ví** nhận = `USR-0068` (hai người khác nhau — đây
> chính là lỗi dữ liệu A1 mà đợt reseed sẽ sinh lại). `USR-0002` là người lạ.

---

## 1. BOLA xác nhận độc lập — và rộng hơn mô tả ban đầu

| Người gọi | REST `POST /tools/lookup_transaction` | Đường TOOL (agent) |
|---|---|---|
| `USR-0002` — **người lạ hoàn toàn** | **HTTP 200 · `found`** · lộ `amount`, `fee`, `status`, `des`, `rec_code` | `not_found` ✅ |
| `USR-0156` — chủ TK ngân hàng gửi | HTTP 200 · `found` | **`not_found`** ← chặn nhầm chính chủ (động cơ của C4) |
| `USR-0068` — chủ ví nhận | HTTP 200 · `found` | `found` ✅ |

⟹ Xác nhận: lỗ nằm **đúng ở tầng REST**, đường tool đã áp
`_enforce_requester_is_party` đúng. Và xác nhận luôn hiện tượng "chặn nhầm
chính chủ TK ngân hàng" mà C4 sinh ra để sửa.

**Hai trường đáng lo hơn `amount`:** `des` (nội dung giao dịch — văn bản người
dùng tự gõ, cùng loại dữ liệu ST2-P0-3) và `rec_code` (mã biên lai — bản thân
nó **là một khoá tra cứu hợp lệ** của chính tool này).

## 2. PHÁT HIỆN NẶNG NHẤT — không cần biết mã giao dịch, chỉ cần SỐ ĐIỆN THOẠI

`LookupTransactionRequest` nhận `phone` + `amount` (`schemas.py:18-24`), và
contract cho phép tổ hợp đó. Chạy thật:

```
USR-0002 (người lạ) tra: {"phone": "<SĐT của USR-0068>", "amount": 167000}
-> HTTP 200 · status="multiple_matches"
   candidates: [{trans_id: TXN20260411000001, amount, created_at, scope, status},
                {trans_id: TXN20260712000501, ...}, ...]
```

Chuỗi tấn công **trọn vẹn chỉ từ một số điện thoại**:
`SĐT → danh sách giao dịch (kèm trans_id) → tra từng trans_id → amount/fee/
status/des/rec_code`. Không cần đoán mã, không cần quan hệ gì với nạn nhân.

**Hệ quả bắt buộc cho bản vá C4:** chặn phải áp cho **cả đường tìm kiếm**
(`phone`+`amount` → `multiple_matches`), không chỉ đường trả chi tiết một giao
dịch. Vá đúng một chỗ trả chi tiết mà bỏ đường liệt kê ứng viên là **vẫn còn
rò** — đủ để dựng lại hồ sơ giao dịch của một người từ số điện thoại của họ.

## 3. Kèm theo — `ValueError` thoát ra thành HTTP 500

```
{"phone": "<SĐT>"}  (thiếu amount)  ->  HTTP 500 Internal Server Error
src/tools/lookup_transaction.py:130  ValueError: lookup_transaction cần
trans_id, hoặc rec_code, hoặc (phone + amount)
```

`_handle_tool_error` (`main.py:210`) không bắt `ValueError`. Contract
`agent-tools.yaml` quy định thiếu tham số → `status='error'`, **không phải
crash**. Lệch contract–code, và là lỗi vận hành rẻ tiền để sửa cùng C4.

## 4. Đã trả lời trước một phần việc "quét cả họ REST tool route"

- `GetCustomerHistoryRequest` (`schemas.py:27-29`) chỉ có `days`,
  `limit_transactions` — **không nhận danh tính**, phạm vi lấy từ JWT ⟹
  **không cùng lỗi**. (Đã kiểm động ở `review-phase01-ap-that.md`: output sạch.)
- `CreateTicketRequest` không nhận `user_id`; `ProposeResolutionRequest`/
  `EscalateTicketRequest` là route nhân viên, `created_by` lấy từ JWT.
- Còn lại phải kiểm **sau khi có bản vá**: `lookup_transaction` là route duy
  nhất trong `authority-matrix.yaml` gắn `any_authenticated` — đúng chỗ đáng
  ngờ nhất, và đúng chỗ thủng.

## 5. Sẽ đo lại y hệt sau khi vá (điều kiện nghiệm thu C4)

1. Người lạ → `not_found`/403 ở **cả** đường `trans_id` **và** đường
   `phone+amount`.
2. Chủ **TK ngân hàng** → tra được giao dịch nạp của **chính mình** (mục (a)
   PO giao).
3. Union **không mở quá**: chủ TK ngân hàng **không** thấy dữ liệu thuộc về
   **ví của người khác** trong cùng giao dịch — masking bên thứ ba vẫn áp
   (mục (b); chồng với TM-R4 của `threat-model-dot-reseed.md`, chạy một lượt).
4. `phone` thiếu `amount` → `status='error'`, **không** 500.
5. Đối chiếu ADR-021 với ATLAS-001 (mục (c)).
