# Dự báo TRƯỚC khi dựng lại lần 2 — `daac112 → HEAD`

> Vai: **tester** · 17/08 · **ghi TRƯỚC khi dựng**. Lần trước cách này trúng cả
> hai cổng, cổng ngân sách trúng tới từng chữ số. Lần này ít commit hơn — nhưng
> **bỏ vì dễ thì lần khó cũng sẽ bỏ**.

## Trạng thái tôi: KHÔNG có phép đo nào đang dở

`ps` không có tiến trình `pytest` / `do_quan_sat` / `do_mot_luot` /
`cong_phan_luong` nào của tôi. **Dựng được cả ba ngăn xếp.**

Và tôi ủng hộ dựng vì lý do coder nêu: `fin05` đang chạy mã **không nằm trong
ảnh nào** (`docker cp`), tức trạng thái kém bền nhất — *"không dựng" không có
nghĩa "không đổi gì", nó có nghĩa "đổi vào một lúc ta không chọn"*.

## Căn cứ: `src/` đổi ĐÚNG MỘT file

    src/rag/ingest.py   +12 −1     (d0aabc0 — vá `extra={"filename"}`)

Không đụng `prompt.py` · `customer_tools.py` · `graph.py` · `main.py`.

## Dự báo

### ① Ba test đang ĐỎ vì `LogRecord` → 🟢 **XANH**

    test_injection.py::test_policy_doc_upload_path_traversal_filename_is_safe
    test_ingest.py::test_ingest_md_creates_indexed_document
    test_ingest.py::test_delete_document_removes_db_rows_and_calls_store

Cả ba đỏ vì cùng một `KeyError`. Bản vá quét cả lớp bằng AST + tập thuộc tính
`LogRecord` **dựng từ runtime**, coder đo trước 1 / sau 0.

**Nếu vẫn đỏ:** đọc thông điệp — nếu **không còn** `KeyError: LogRecord` thì đó
là **lỗi thứ hai bị lỗi thứ nhất che**, không phải bản vá hỏng. Ba test này
chưa từng chạy qua được chỗ đó, nên phần sau nó **chưa ai kiểm**.

### ② `7cd8343` ngân sách token → 🟢 **XANH**, in `6.565/7.550 · còn 985 (13%)`

`prompt.py` và `customer_tools.py` không đổi ⟹ `4.587 + 1.978` giữ nguyên.
Cùng dự báo lần trước, cùng lý do, và lần trước nó trúng từng chữ số.

### ③ `bc73cbe` một-lượt-một-hồ-sơ → 🟢 **1 pass · 1 XFAIL · 1 pass**

`customer_tools.py` không đổi ⟹ chống-trùng vẫn chưa có ⟹ XFAIL giữ nguyên.

### ④ Hai bộ TỐN TIỀN → ⏭️ **SKIP** (`5fbd01f` đã land)

    test_a2_dong_y_truoc_khi_tao_ve        skip · ~42K
    test_bat_bien_dinh_tuyen_duong_nhe     skip · ~14K

Đây là **thay đổi hành vi có chủ ý** so với lần dựng trước: cùng lệnh
`pytest tests/` giờ **không đốt token nào**. Nếu chúng **vẫn chạy** thì cờ
`FIN05_CHO_PHEP_TON_TIEN` đang bị đặt ở đâu đó ngoài ý muốn — **điều tra ngay**,
đừng để nó thành mặc định ngầm.

### ⑤ Tổng suite `-m "not security_finding"` → **7 đỏ → 4 đỏ**

Còn lại, và tôi **chưa truy** nên **không dự báo màu**, chỉ khoanh:

    test_thanh_phan_tai_lieu_kho::…noi_bo_da_biet   "kho rỗng" — điều kiện hạ tầng
    test_live_chat_pii_gap::…_is_not_masked…        tên test tự nói là GAP đã biết
    test_f31_f32 × 2                                 xfail(strict) trên đường agent thật

⚠️ `test_f31_f32` gọi LLM thật và **chưa có cổng chi phí** — hôm nay nó tốn 0
token (rơi vào đường nhẹ/fallback), nhưng đó là **may**, không phải thiết kế.
Tôi gắn cờ cho nó **sau** lần dựng này, không sửa giữa chừng.

## Bảng tóm

| | dự báo | nếu khác thì nghi gì |
|---|---|---|
| 3 test `LogRecord` | 🟢 xanh | còn đỏ mà **không** phải KeyError ⟹ lỗi thứ hai bị che |
| `7cd8343` | 🟢 `6.565/7.550` | prompt/lược đồ đổi — **là phát hiện** |
| `bc73cbe` | 🟢 1p·1x·1p | XPASS ⟹ có ai thêm chống-trùng, **tin tốt** |
| 2 bộ tốn tiền | ⏭️ skip | chạy ⟹ cờ bị đặt ngoài ý muốn, **điều tra** |
