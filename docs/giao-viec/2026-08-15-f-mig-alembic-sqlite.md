# F-MIG — `alembic upgrade head` KHÔNG chạy được trên SQLite từ DB trắng

> **Người tìm ra + soạn hồ sơ: tech-lead (phiên coder P-226).** PO-agent chép nguyên văn vào
> `docs/` theo yêu cầu của tech-lead (vùng `docs/` ngoài quyền ghi của họ) — nội dung là chữ của
> người tìm ra, không phải diễn đạt lại. Lý do không dán đường dẫn scratchpad: thư mục đó gắn với
> phiên coder, phiên đóng là link chết trông như bằng chứng sống (đúng bài học F-LOG).

- **Ngày:** 2026-08-15 · **Người tìm ra:** tech-lead (phiên coder P-226)
- **Mức:** TRUNG BÌNH — không phải lỗ hổng bảo mật, là **đường dựng schema chính thức của dự án
  không chạy được ở môi trường test mặc định**.
- **CÓ SẴN TỪ TRƯỚC**, không thuộc lô 15/08. Phát hiện tình cờ khi verify migration A2, không do
  đi tìm.
- **Trạng thái:** chưa vá. Security đã xem, **không** nghiệm thu (ngoài phạm vi 4 bản vá của họ),
  đề nghị tách finding riêng. Chờ PO thật xếp lịch thành lô riêng.

## Triệu chứng — đo thật

```
$ DATABASE_URL="sqlite:///<db trắng>" python -m alembic upgrade head
...
Running upgrade e702b39353b4 -> a1b2c3d4e5f6, ADR-019 — nhãn phán đoán chuyên gia tại luồng từ chối
NotImplementedError: No support for ALTER of constraints in SQLite dialect.
Please refer to the batch mode feature which allows for SQLite migrations
using a copy-and-move strategy.
```

Chết ở **`a1b2c3d4e5f6`** (ADR-019). Chuỗi dừng tại đó, mọi revision sau **không bao giờ chạy**.

## Vì sao chưa ai gặp

Test suite dựng schema bằng `Base.metadata.create_all()` (đọc thẳng `src/db/models.py`), không qua
alembic. Nên **540 test xanh không nói gì** về việc chuỗi migration có chạy được hay không — hai
đường dựng schema tách biệt, chỉ một được canh.

Đúng họ **Luật 14**: nhánh alembic tồn tại, được commit, được review, nhưng **không test nào chạm nó**.

## Ba hệ quả, xếp theo mức đau

**1. Migration `a7b8c9d0e1f2` (A2) là mã CHƯA ĐƯỢC CHẠY THẬT.** Nó nằm cuối chuỗi, tức sau chỗ gãy.
⚠️ **"A2 đã verify" KHÔNG đọc thành "migration A2 đã verify".** CHECK của A2 được verify bằng
`create_all()` + probe hành vi (2.000 ký tự QUA ở ASCII/VN/emoji · 5.000/8.000/20.000 CHẶN) — tức
**định nghĩa constraint trong `models.py` đúng**, nhưng **đường migration đưa nó vào một DB đã có
sẵn thì chưa ai chạy**. Với DB production đã tồn tại, chỉ thứ thứ hai mới có tác dụng.

**2. Không dựng lại được DB dev/test bằng đường chính thức.** Ai clone repo rồi làm theo alembic sẽ
thất bại. Đường đi được hiện nay là `create_all()`, nhưng nó **không áp lịch sử migration** — DB
dựng bằng hai cách có thể khác nhau mà không ai phát hiện.

**3. Không có gì bảo đảm `models.py` và chuỗi migration còn khớp.** Vì chuỗi chưa bao giờ chạy
trọn, không tồn tại phép kiểm nào xác nhận "schema sau khi chạy hết migration" == "schema
`create_all()` sinh ra". Độ lệch có thể đã tích luỹ và **chỉ lộ ở lần deploy Postgres thật đầu
tiên** — đúng lúc đắt nhất.

## Hướng vá (đề xuất, chưa làm)

`render_as_batch=True` trong `migrations/env.py` khi dialect là SQLite. Alembic tự dựng bảng mới →
chép dữ liệu → đổi tên cho mọi ALTER mà SQLite không hỗ trợ. Migration `a7b8c9d0e1f2` đã dùng
`batch_alter_table` thủ công nên không cần sửa; các migration cũ hơn thì `render_as_batch` xử lý
mà không phải viết lại từng file.

**Cần đo sau khi vá — KHÔNG coi là xong khi `upgrade head` hết đỏ:**
1. `alembic upgrade head` trên SQLite trắng → chạy trọn chuỗi.
2. `downgrade base` rồi `upgrade head` lại → chuỗi hai chiều.
3. **So schema hai đường**: `upgrade head` vs `create_all()` → phải TRÙNG. Đây là phép kiểm quan
   trọng nhất và là thứ duy nhất trả lời được hệ quả số 3. Lệch = finding riêng.
4. Cân nhắc test CI chạy phép so ở mục 3 — biến nhánh-không-ai-canh thành nhánh-có-canh.

## Ghi chú phạm vi

Không vá trong lô 15/08 vì nó ngoài việc được giao, và sửa `migrations/env.py` chạm mọi migration
cùng lúc — đáng một lô riêng có đo, không đáng một dòng "tiện tay".
