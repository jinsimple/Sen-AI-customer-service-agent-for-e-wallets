# Lượt đo đã bỏ đi

Nơi cất các lượt đo **không dùng làm bằng chứng cho bất kỳ kết luận nào**: chạy
thử công cụ, lượt bị huỷ giữa chừng, lượt chạy sai tham số.

**Vì sao cất chứ không xoá:** một lượt đo là bằng chứng đã tốn tiền thật để
tạo ra. Xoá đi thì lần sau có ai hỏi "hôm đó đo được gì" là không trả lời
được. Nhưng để lẫn với lượt đo thật thì nguy hiểm hơn — người sau dễ nhặt
nhầm một lượt chạy thử làm mốc nền.

**Luật:** file nào đang được TRÍCH DẪN trong `docs/` hoặc `eval/results/*.md`
thì **KHÔNG được chuyển vào đây** — chuyển là làm chết đường dẫn trong biên
bản. Kiểm bằng `grep -rn "<tên file>" docs/ eval/` trước khi chuyển.

| File | Vì sao bỏ |
|---|---|
| `quality_run_20260814_164323_raw.json` | Lượt 1 case chạy thử công cụ D1 (xác nhận raw có transcript đủ lượt + dấu thước), không phải phép đo chất lượng. |
| `quality_run_20260814_131834_raw.json` | **Cụm 4 lượt thước-trung-gian** — xem ghi chú bên dưới. Là NỀN của 3 lượt patch kế tiếp. |
| `quality_run_20260814_133738_raw.json` | nt (lượt patch 1) |
| `quality_run_20260814_135022_raw.json` | nt (lượt patch 2) |
| `quality_run_20260814_140419_raw.json` | nt (lượt patch 3) |

## Cụm 4 lượt 14/08 — chuyển NGUYÊN CỤM, có lý do

Chuyển cả bốn cùng lúc chứ không chỉ 3 lượt patch: `131834` là **mốc nền** mà
ba lượt kia ghép cặp với nó. Để nền ở lại `results/` trong khi các lượt patch
đi vào archive là dựng sẵn một cái bẫy — người sau rất dễ nhặt nền cũ này ghép
với một lượt đo mới, ra một cặp số vô nghĩa mà trông hoàn toàn hợp lệ.

### ⚠️ ĐÍNH CHÍNH mô tả ban đầu: KHÔNG phải "thước cũ, trước d72017a"

Đề xuất ban đầu ghi cụm này là *"thước cũ, trước `d72017a`"*. Đối chiếu giờ
thật thì **sai**:

| Mốc | Giờ địa phương |
|---|---|
| `d72017a` — dữ kiện thứ 3 cho khách ảo | 20:08 |
| **4 lượt trong cụm này** | **20:18 – 21:04** |
| `aa5d593` — check `de_nghi_truoc_khi_tao_ticket` | 22:17 |
| `394feef` — check `tao_ho_so_tra_thu_cong` | 23:05 |

⇒ Thước của cụm này là **SAU `d72017a`, TRƯỚC `aa5d593` và `394feef`**. Tức nó
ĐÃ có bản sửa khách-ảo, CHƯA có hai check mới.

*(Tên file là giờ **UTC**, giờ sửa file là giờ địa phương — lệch đúng 7 tiếng.
Đây chính là chỗ dễ đọc nhầm, ghi ra để người sau khỏi vấp lại.)*

**Vì sao đính chính này quan trọng:** ai đó đọc "trước `d72017a`" sẽ tưởng cụm
này thiếu bản sửa khách-ảo và có thể kết luận sai về nguyên nhân chênh lệch.
Một dòng mô tả sai trong archive nguy hiểm hơn không có mô tả — nó được tin.

**Cách kiểm lại bằng máy** (không cần tin dòng nào ở trên): file raw của cụm
này KHÔNG có `_thuoc`, và không case nào mang check `tao_ho_so_tra_thu_cong`
dù `CASE-109`/`CASE-110` đều có mặt — hai check mới chưa tồn tại lúc đó.

**Đã kiểm trước khi chuyển:** không file nào trong cụm được trích dẫn ở `docs/`
hay `eval/` (`grep -rl`). **KHÔNG chuyển:** `161529`, `163222`, `164859`,
`041244` — đang dùng làm bằng chứng/mốc so sánh hiện hành.
