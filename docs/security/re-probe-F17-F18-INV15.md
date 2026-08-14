# Re-probe — F-17 · F-18 · INV-15 (sau bản vá của coder)

> Vai: **security** · 2026-08-15 · nhánh `dev/learning-loop`
> Đo lại đúng các điều kiện đã đặt ở `review-ADR-020-BR-12-maker-checker.md` §4 và §6.
> Phép thử ghi DB đều transaction + rollback; **không dòng dữ liệu nào bị đổi**.

---

## Kết luận: **ĐẠT 3/3** — kèm **một phát hiện mới (F-21)** sinh ra từ chính bản mở rộng

| Mục | Kết quả | Bằng chứng |
|---|---|---|
| **F-17** — bịt cửa thoát `created_by` NULL | **ĐẠT** | `created_by` nay là `KEYWORD_ONLY`, **không có default**. Gọi thiếu → `TypeError: propose_resolution() missing 1 required keyword-only argument: 'created_by'` — bỏ quên thành lỗi bắt được lúc test, đúng đặc tả. `seed_demo_scenarios.py` có 6 chỗ truyền `created_by=`. |
| **F-18** — BR-12 mở rộng sang `rejected_by` | **ĐẠT 6/6** | Xem bảng dưới. Biểu thức áp đúng **dạng C** đã khuyến nghị (đọc từ `pg_constraint`): `((created_by IS NULL) OR (((approved_by IS NULL) OR (approved_by <> created_by)) AND ((rejected_by IS NULL) OR (rejected_by <> created_by))))` — hai trị, không phụ thuộc `IS DISTINCT FROM`, chạy giống nhau trên Postgres/SQLite. |
| **INV-15** — test hiện diện + khớp biểu thức | **ĐẠT** | `test_inv15_check_constraint_br12_ton_tai_va_khop_bieu_thuc_contract` tồn tại và khẳng định **cả biểu thức contract**, không chỉ tên. Chạy trên cây làm việc host: **23 passed** — đúng con số tôi đã nêu trước sẽ kiểm. |

### Bảng 6 ca (chạy trên constraint ĐÃ ÁP trong Postgres thật)

| # | Tình huống | Kết quả | Kỳ vọng |
|---|---|---|---|
| 1 | `c=X`, chưa duyệt/từ chối | ghi được | cho phép ✅ |
| 2 | **`c=X, a=X` tự duyệt** | **chặn** | chặn ✅ |
| 3 | `c=X, a=Y` duyệt đúng | ghi được | cho phép ✅ |
| 4 | **`c=X, r=X` tự từ chối** ← F-18 mới | **chặn** | chặn ✅ |
| 5 | `c=X, r=Y` từ chối đúng | ghi được | cho phép ✅ |
| 6 | `c=NULL` (dòng cũ) | ghi được | cho phép ✅ |

Dữ liệu hiện tại vẫn 10/10 `created_by` NULL — đúng như đã chốt: **không backfill**,
cửa thoát tự cạn theo thời gian khi mọi resolution mới đều có người đề xuất.

---

## F-21 (MỚI, mức TRUNG BÌNH) — nhánh từ chối thiếu chốt tầng route

**Sự việc:** `reject_resolution` (`src/api/main.py`) **không có** guard maker-checker.
Nhánh duyệt có (`main.py:918` → **403** kèm câu giải thích cho người dùng); nhánh từ
chối chỉ còn **CHECK ở tầng DB**.

**Hệ quả:** sau khi F-18 mở rộng constraint, một supervisor **tự từ chối đề xuất của
chính mình** sẽ làm `UPDATE` vi phạm CHECK ⟹ `IntegrityError` ⟹ **HTTP 500**, thay vì
403 đọc được. Đây **đúng thứ mà chính coder viết ra guard route để tránh** — comment
tại `main.py:908-917` nói rõ: *"nếu chỉ dựa vào CHECK thì … sẽ nhận HTTP 500 kèm
IntegrityError — người dùng không hiểu chuyện gì, log thì trông như hệ thống hỏng chứ
không như một quy tắc nghiệp vụ đang làm đúng việc."* Lập luận đó áp nguyên văn cho
nhánh từ chối kể từ khi F-18 được duyệt.

**Có thật sự chạm tới được không — CÓ.** Route `POST /tools/propose_resolution` mở cho
**cả `cskh` lẫn `supervisor`** (`contracts/authority-matrix.yaml`), nên một supervisor
đi trọn được cả hai đầu — đúng cửa mà chính comment của coder đã nêu cho nhánh duyệt.
Chưa xảy ra hôm nay **chỉ vì** 10/10 dòng cũ có `created_by` NULL; mọi resolution tạo
qua API kể từ F-17 đều có `created_by`, nên cửa này mở ra ngay khi một supervisor tự
đề xuất rồi tự từ chối.

**Đây là hệ quả trực tiếp của bản mở rộng tôi khuyến nghị** — nêu ra vì trách nhiệm,
không phải để bắt lỗi coder: F-18 đúng, chỉ là nó thêm một trạng thái lỗi mới ở nhánh
chưa có lớp dịch lỗi cho người dùng.

**Mức độ:** không phải lỗ hổng — DB vẫn chặn, không ai tự từ chối được. Là lỗi **vận
hành + trải nghiệm**: 500 làm nhiễu log, trông như hệ thống hỏng, và che mất một quy
tắc nghiệp vụ đang chạy đúng.

**Đề nghị (coder, rẻ):** sao đúng khối guard của nhánh duyệt sang `reject_resolution`,
đặt cùng chỗ (sau khi lấy `resolution`, trước khi ghi), trả **403** với câu giải thích
tương ứng. **Tester:** thêm 1 ca "supervisor tự từ chối đề xuất của chính mình → 403,
không phải 500".

**Cách tôi xác minh:** chặn ở tầng DB đã chứng minh bằng ca số 4 ở trên (rollback);
việc route thiếu guard đọc trực tiếp từ mã. Tôi **cố ý không** dựng một resolution
thật để bắn 500 qua HTTP — sẽ để lại rác trong hàng chờ demo; nếu PO muốn bằng chứng
HTTP thật thì làm cùng lượt nghiệm thu sau rebuild (luật F-19).

---

## Nhắc lại một điều kiện chưa đóng

**Luật F-19 vẫn phải áp cho lượt nghiệm thu:** các phép đo trên chạy ở **tầng DB**
(dữ liệu dùng chung nên đúng) và **cây làm việc host** (test), **không** phải trong
container đang chạy. Trước khi tuyên bố BR-12/F-17/F-18 có hiệu lực trên hệ thống
đang phục vụ, phải `docker compose build` **rồi grep lại trong container** để xác
nhận bản mới thật sự nằm trong đó — đúng cách F-19 bị bắt lần đầu.
