# Rà bảo mật — ADR-020 / BR-12 maker–checker (đã áp thật)

> Vai: **security** · 2026-08-15 · nhánh `dev/learning-loop`
> Rà theo yêu cầu PO trước khi PO thật ký ADR-020. Nối tiếp
> `review-phase01-ap-that.md` (F-01…F-16) — đợt này là **F-17…F-20**.
> Mọi kết luận có bằng chứng chạy thật; phép thử ghi DB đều
> transaction + rollback, không đổi dữ liệu.

---

## Kết luận: **ĐẠT CÓ ĐIỀU KIỆN**

Biểu thức CHECK **đúng**, ngữ nghĩa NULL **đúng như ADR khẳng định**, hai tầng
**khớp nhau**. Nhưng ở trạng thái hôm nay ràng buộc này **chưa ràng buộc dòng
nào**, và cửa thoát `created_by IS NULL` **đang được một script trong repo
tiếp tục nuôi** — nên nếu ký ADR-020 mà không kèm 2 điều kiện dưới đây thì
maker–checker là ràng buộc **trên giấy**.

Ba điều kiện trước khi coi BR-12 là đã có hiệu lực:
1. **F-17** — bịt cửa `created_by` NULL ở tầng sinh dữ liệu (bắt buộc).
2. **INV-15 phải có test thật** (đang thiếu — QA bắt đúng).
3. **F-19** — rebuild stack trước khi nghiệm thu; bản đang chạy chưa có BR-12.

---

## 1. Lõi BR-12 — ĐẠT

Ghi thẳng Postgres (rollback):

| Phép thử | Kết quả | Kỳ vọng |
|---|---|---|
| `created_by = approved_by` (tự đề xuất tự duyệt) | **BỊ CHẶN** — `CheckViolation` | chặn ✅ |
| `created_by ≠ approved_by` (đúng maker–checker) | GHI ĐƯỢC | cho phép ✅ |

## 2. Ngữ nghĩa NULL — ADR khẳng định ĐÚNG, đã verify

| Phép thử | Kết quả |
|---|---|
| `created_by` có, `approved_by` NULL (hàng chưa duyệt) | GHI ĐƯỢC ✅ — đúng, hàng chưa duyệt không được vướng |
| `created_by` NULL, `approved_by` có | **GHI ĐƯỢC** ← đây là **cửa thoát**, xem F-17 |

`approved_by IS NULL` ⟹ `approved_by != created_by` cho **NULL** ⟹ SQL coi
CHECK là **thoả**. Đúng như ADR mô tả, và đúng như thiết kế cần — kết hợp với
BR-10 (`approved` ⟹ `approved_by NOT NULL`) thì **mọi hàng đã duyệt đều có
`approved_by`**, nên vế NULL này không tạo lỗ ở nhánh approve.

Lỗ nằm ở **vế bên kia**: `created_by IS NULL`.

## 3. Chốt hai tầng — KHỚP, kể cả khớp ở chỗ hở

- Route: `main.py:918` — `if resolution.created_by is not None and
  resolution.created_by == current_user.user_id:` → **403** kèm thông báo
  đọc được. Comment giải thích đúng lý do tồn tại (không để người dùng nhận
  HTTP 500 từ `IntegrityError`).
- DB: `ck_resolutions_maker_checker_br12` — chốt cuối, chặn cả đường ghi
  thẳng/script/migration ẩu.
- **Hai tầng dùng cùng phép so sánh và cùng bỏ qua khi `created_by` NULL** —
  nhất quán, nhưng nghĩa là **cửa thoát cũng có ở cả hai tầng**, không tầng
  nào bù cho tầng kia.
- Không route nào khác ghi `approved_by` (chỉ `/resolutions/{id}/approve`),
  nên không có đường lách route mà chỉ CHECK bắt — **ngoài** các đường
  ngoài-ứng-dụng vốn là lý do CHECK tồn tại.
- *Ghi chú nhỏ, không phải lỗ hổng:* guard 403 nằm **sau** toàn bộ kiểm OTP
  (dòng 918, sau `amount_snapshot` ~905). Sếp phải đi xin OTP rồi mới bị từ
  chối. Không ảnh hưởng an toàn; nếu muốn thân thiện hơn thì đẩy lên trước
  khối OTP.

## 4. Phát hiện

| # | Mức | Mô tả | Bằng chứng | Giao ai |
|---|---|---|---|---|
| **F-17** | **CAO** (hiệu lực, không phải tính đúng) | **Cửa thoát `created_by IS NULL` đang được nuôi tiếp, không chỉ là dữ liệu cũ.** `src/tools/propose_resolution.py:87` khai `created_by: str | None = None` — **bỏ quên là im lặng**, không lỗi. `scripts/seed_demo_scenarios.py` gọi `propose_resolution()` **4 lần và KHÔNG lần nào truyền `created_by`** (dòng 149/164/179/197). Mọi hàng sinh ra từ đó **miễn nhiễm maker–checker ở CẢ HAI tầng** (route bỏ qua vì `is not None`; CHECK thoả rỗng) — và đó chính là các hàng dùng để diễn demo rồi được duyệt. | Truy vấn thật: **10/10 hàng hiện có `created_by` NULL** (6 approved · 3 pending_approval · 1 rejected) ⟹ BR-12 đang ràng **0 dòng**. Probe: `created_by NULL + approved_by` → ghi được. | **coder**: đổi `created_by` thành tham số **bắt buộc** (keyword-only, không default) ở `propose_resolution()` — bỏ quên thành `TypeError` bắt được lúc test, không thành NULL im lặng; + sửa 4 call site trong `seed_demo_scenarios.py` (truyền `user_id` của CSKH seed). **tester**: test "không đường nào tạo được resolution với `created_by` NULL". |
| **F-18** | TRUNG BÌNH | **BR-12 KHÔNG canh nhánh từ chối.** `created_by = rejected_by` (tự đề xuất, tự từ chối + tự dán nhãn) **ghi được**. Không phải rủi ro tiền, nhưng chạm thẳng mục tiêu đợt này: ADR-019 chọn nhãn `reject_reason` làm **phán đoán ĐỘC LẬP của con người để chấm điểm AI**, và bác bỏ "để AI tự gán nhãn" vì đó là vòng lặp tự khen. Người tự từ chối và tự dán nhãn đề xuất của chính mình là **đúng vòng lặp đó ở phiên bản con người** — nhãn vào phễu học Phase 2 mất tính độc lập mà không ai thấy. | Probe: `created_by='USR-0205'`, `rejected_by='USR-0205'` → **GHI ĐƯỢC** (kỳ vọng chặn). | **PO quyết**: mở rộng BR-12 sang `rejected_by`, hay giữ nguyên và **ghi rõ trong ADR-020 vì sao** (phải trả lời được lập luận độc lập của ADR-019). Security nghiêng về **mở rộng** — rẻ, cùng biểu thức. |
| **F-19** | TRUNG BÌNH | **Stack đang chạy CHƯA có BR-12, trong khi DB đã có.** Container không có guard route (`grep -c "maker-checker" = 0`) và model trong container không có `ck_resolutions_maker_checker_br12`. Hệ quả hôm nay: nếu một hàng có `created_by` bị chính người đó duyệt qua API, app sẽ đâm `IntegrityError` → **HTTP 500** — đúng thứ mà guard route được viết ra để tránh. Nguy hiểm kép: **mọi phép đo chạy trong container đều đang đo code cũ** — lần chạy đầu của tôi trong container cho "22 passed · hash khớp baseline `35001b6ecb04`" **không chứng minh gì về BR-12**. | `docker exec` kiểm trực tiếp: 0 lần khớp "maker-checker"; danh sách constraint của model thiếu br12. Chạy lại trên cây làm việc host: hash `60977cba503f` (v2.2.1). | **coder/PO**: rebuild trước khi nghiệm thu; và ghi thành luật — nghiệm thu BR-12 phải chạy trên bản đã rebuild, không chạy trong container cũ. |
| **F-20** | GHI NHẬN | **INV-15 khai trong contract nhưng CHƯA có test** — đúng như QA bắt. `tests/test_invariants.py` chỉ có `test_inv07_check_constraint_br10_ton_tai` và `test_inv14_check_constraint_br11_ton_tai`; **không có** `test_inv15_*`. Chạy thật trên host: **22 passed** — bằng đúng số trước ADR-020, tức không test nào được thêm. Nên hôm nay cơ chế chống-drift **không phủ** BR-12: ai gỡ CHECK đi thì không gì đỏ. | Host: `22 passed`; grep chỉ thấy br10/br11. | **coder** (đang làm): thêm test đọc `models.py` đúng khuôn `test_inv14`, khẳng định **cả tên** `ck_resolutions_maker_checker_br12` **lẫn biểu thức** `(created_by IS NULL) OR (approved_by != created_by)` — khai thiếu biểu thức thì đổi biểu thức mà vẫn xanh. Sau khi thêm phải là **23 passed**. |

## 5. Đã kiểm và đạt (không cần kiểm lại lần sau)

- Biểu thức CHECK không có kẽ hở logic ngoài vế `created_by IS NULL` **cố ý**
  (đã phân tích ở §2 — bắt buộc phải có, nếu không migration vỡ trên dữ liệu cũ,
  đúng lý do đã ghi ở `b2c3d4e5f6a7`).
- Route và CHECK dùng **cùng** ngữ nghĩa; không có đường ghi `approved_by` nào
  khác trong ứng dụng.
- Giới hạn PO nêu — *"10/10 `created_by` NULL ⟹ chưa ràng dòng nào"* —
  **ĐÚNG**, đã xác nhận bằng truy vấn. Và cần nói rõ với PO thật: đây **không**
  chỉ là giới hạn với dữ liệu cũ; **F-17 cho thấy dữ liệu MỚI vẫn đang sinh ra
  ở dạng NULL**. Bịt F-17 rồi thì giới hạn này tự hết theo thời gian, không cần
  backfill (và **không được** backfill — đoán tên người đề xuất vào sổ kiểm
  toán là đúng lỗi F-11 vừa dọn).
- `.claude/state/contract-hashes.json` đã bump sang `60977cba503f` nhưng **đang
  nằm chưa commit** trong cây làm việc (của coder). Không phải lỗi bảo mật —
  nhắc để bump không bị mất hoặc bị commit nhầm bởi vai khác.

## 6. Chưa kiểm được

- **Không chạy phép thử tự-duyệt qua HTTP thật**: sẽ phải tạo một resolution
  thật rồi duyệt/để lại rác trong hàng chờ demo, và stack đang chạy chưa có
  guard (F-19) nên phép đo cũng không đúng bản code cần đo. Sẽ đo sau khi
  rebuild, cùng lượt nghiệm thu C4.
- **Một người hai tài khoản** vẫn lách được cả hai tầng (so sánh `user_id`,
  không phải danh tính người) — cùng lớp giới hạn đã ghi ở F-16; bù bằng
  audit log (F-05), không bù được bằng CHECK.
