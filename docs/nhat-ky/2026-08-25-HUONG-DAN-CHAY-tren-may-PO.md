# Cập nhật bản đang chạy — máy Windows của PO

> Cho người ngồi trước máy lúc 11 giờ đêm. **Gõ cái này, thấy cái kia.** Phần *vì sao* ở cuối,
> không cần đọc để chạy được.
> **Đây là CẬP NHẬT một bản đang chạy, không phải cài mới** — `.env` trên máy đã có sẵn, **đừng
> đụng vào nó**.

---

## 0. Trước khi gõ gì — ghi lại đường lùi (10 giây)

```bash
cd <thư-mục-P-226>
git rev-parse --short HEAD
```
**Chép con số hiện ra ra giấy/notepad.** Sai thì mục 5 dùng tới nó.
*(Bản đang chạy trước lần này: `38d5cd2`.)*

---

## 0b. 🔴 MỘT DÒNG THÊM VÀO `.env` — làm MỘT LẦN, trước khi gõ lệnh nào

Mở tệp `.env` trong thư mục dự án, **thêm đúng một dòng vào cuối**:
```
BAO_VE_CSDL=true
```
Lưu lại. **Không sửa dòng nào khác trong tệp ấy.**

**Dòng này làm gì:** khoá CSDL lại để lệnh `docker compose down -v` **không xoá được nó nữa**.

🔴 **Quên dòng này thì mất gì:** không mất gì **ngay** — hệ thống chạy y hệt. Nhưng
**`down -v` vẫn xoá sạch CSDL như trước**, tức mọi ticket, khiếu nại và transcript chat của khách.
**Thêm một lần, xong mãi mãi.**

---

## 1. Lấy mã mới

```bash
git pull origin main
```

## 2. Dựng và chạy

```bash
docker compose up -d --build
```
⏳ Lần đầu sau nhiều thay đổi: **5–15 phút**. Màn hình chạy chữ liên tục là bình thường.

### 🔴 Nếu nó ĐỎ giữa chừng với một lỗi lạ bên trong `pip`

Ví dụ `JSONDecodeError`, `IncompleteRead`, `Connection broken`, hoặc bất cứ thứ gì trông như lỗi
Python sâu bên trong `pip`:

> **GÕ LẠI ĐÚNG LỆNH Ở MỤC 2 MỘT LẦN. Đừng đi tìm bug.**

**[ĐO 25/08]** một lần dựng sạch đỏ đúng như vậy; chạy lại **xanh ngay**, không sửa một dòng nào.
Lỗi tải gói chập chờn **không hiện ra như lỗi mạng** — nó hiện ra như lỗi trong mã.

Chạy lại **hai lần vẫn đỏ** ⟹ lúc đó mới là lỗi thật, chụp màn hình gửi đội.

## 3. Biết là xong chưa

```bash
docker compose ps
```
**Đợi tới khi thấy ĐÚNG như thế này** *(chép từ một lần chạy thật, 25/08)*:
```
backend     Up 33 seconds (healthy)
caddy       Up 3 seconds
frontend    Up 3 seconds
jaeger      Up 44 seconds
postgres    Up 44 seconds (healthy)
redis       Up 44 seconds (healthy)
```
🔴 **`caddy` và `frontend` KHÔNG có chữ `healthy` — ĐÚNG như vậy**, chúng không khai healthcheck.
Chỉ cần **`backend` · `postgres` · `redis`** ghi `healthy`.
⏱ **backend chậm nhất** — nó chạy `alembic upgrade head` xong mới mở cổng. Trong lần đo:
postgres/redis healthy ở giây **44**, backend healthy ở giây **33 kể từ lúc nó khởi động**.
Chưa thấy `healthy` sau **~3 phút** thì mới đáng lo.

**Rồi mở trình duyệt vào site.** Thấy **trang đăng nhập** = xong.

*(Muốn chắc mà không mở trình duyệt — chạy đúng dòng này, thấy `200` là được:)*
```bash
curl -sk -o nul -w "%{http_code}\n" https://localhost/login
```

**Muốn xem nó đang làm gì:**
```bash
docker compose logs -f backend
```
*(Ctrl+C để thoát xem log — container **vẫn chạy**, không bị tắt.)*

---

## 3b. 🔴 BA THỨ TRÔNG NHƯ LỖI NHƯNG LÀ ĐÚNG — đừng sửa, đừng báo hỏng

Bản này đổi hành vi **nhìn thấy được ngay**. Ba thứ dưới đây **cố ý**:

```
① live-chat hiện `098***4321` thay vì số đầy đủ
     → ĐÚNG. Số đầy đủ VẪN tới CSKH qua MÀN HÌNH BÀN GIAO, và bản LƯU vẫn nguyên vẹn.
       (M3 — PO ký 25/08, commit d8e4ff9)
     🔴 Đây là TÍNH NĂNG BẢO MẬT trông y hệt một LỖI HIỂN THỊ. Ai "sửa lại cho hết lỗi"
       là đang gỡ đúng bản vá PO vừa ký.

② tin nhắn của trợ lý còn dấu sao, kiểu `**Số tiền**`
     → ĐÚNG, cố ý không vá. Dựng chữ đậm từ chuỗi do model sinh mở đường bơm mã qua
       lời khách gõ. Đổi một khiếm khuyết thẩm mỹ lấy một bề mặt tấn công: không cân.

③ bong bóng chat trông KHÁC hẳn bản cũ — xuống dòng đúng, tin nhắn dài tách vế
     → ĐÚNG (3c70024). Bản cũ dồn ba vế thành một khối chữ liền.
```

---

## 4. 🔴 LỆNH KHÔNG ĐƯỢC GÕ

```
docker compose down -v          ←  ĐỪNG.  Chữ  -v  là chữ nguy hiểm.
```
Muốn **dừng** thì gõ **không có `-v`**:
```bash
docker compose down
```

**Nếu lỡ gõ `down -v` rồi:** CSDL **vẫn còn — NẾU đã làm mục 0b**. Chưa làm mục 0b thì CSDL **mất**. Nhưng **chỉ mục RAG mất**. Dựng lại:
```bash
docker compose up -d
docker compose exec backend su appuser -c "python3 scripts/kho_rag.py nap-lai"
```

---

## 5. Sai thì lùi

```bash
git checkout 38d5cd2          # con số đã chép ở mục 0
docker compose up -d --build
```
**An toàn.** **[ĐO 25/08]** lần cập nhật này **KHÔNG có migration mới nào**
*(`git diff --name-only origin/main..HEAD -- migrations/` → 0 tệp)* ⟹ lùi mã **không để lại**
CSDL ở trạng thái mới hơn mã. Dữ liệu giữ nguyên.

Quay lại bản mới: `git checkout main` rồi dựng lại như mục 2.

---

## Phần *vì sao* — không cần đọc để chạy được

- **Vì sao `.env` không đụng tới:** máy đang chạy đã có đủ. Sinh khoá mới sẽ **mất vĩnh viễn** dữ
  liệu đã mã hoá (`FIELD_ENCRYPTION_KEY` không xoay được nếu không có script giải-mã-lại).
- **Vì sao `-v` nguy:** nó xoá các kho dữ liệu của ngăn. Từ 25/08 CSDL đã được khoá riêng ra nên
  `-v` không xoá được nữa, nhưng chỉ mục RAG và log thì vẫn mất.
- **Vì sao chạy lại là đúng khi build đỏ lạ:** lỗi tải gói chập chờn hiện ra như lỗi phân tích dữ
  liệu sâu trong `pip`; người đo hôm 25/08 suýt kết luận *"cây sạch không dựng được"* từ đúng một
  lần như thế.

---

## 🔴 Điều người viết ĐÃ đo và CHƯA đo — đọc trước khi tin

**ĐÃ đo thật, 25/08:**
```
· dựng từ cây SẠCH (clone thật, không .env)     → cả hai ảnh dựng được
· ảnh backend CHẠY được, không chỉ dựng được    → 339 gói, spacy/chromadb/fastapi import OK,
                                                   model NER nạp được
· thiếu 1 trong 4 biến bắt buộc                 → app CHẾT NGAY lúc khởi động, báo rõ thiếu gì
   (DATABASE_URL · JWT_SECRET_KEY · FIELD_ENCRYPTION_KEY · REDIS_URL)
· `down -v` với volume external                 → volume external SỐNG, volume thường bị xoá
· không có migration mới so với main            → 0 tệp
```

**ĐÃ chạy TRỌN NGĂN thật, 25/08** *(bản sao sạch của `dev/learning-loop`, `.env` sinh mới,
`docker compose up -d --build` từ đầu)*:
```
· 6/6 dịch vụ lên     backend · caddy · frontend · jaeger · postgres · redis
· backend /health     {"status":"ok","env":"production","db_kind":"postgresql","db_name":"fin05"}
· https://…/login     200 · text/html · 10.516 bytes   ← TRANG ĐĂNG NHẬP DỰNG RA THẬT
· http (cổng 80)      308 → chuyển sang https, đúng thiết kế
· volume external     `up` DÙNG ĐÚNG `fin05_postgres_data`, không tự tạo cái khác
```

**CHƯA đo — nói rõ thay vì để người đọc tưởng đã kiểm:**
```
🔴 Toàn bộ số đo trên chạy trên macOS. Máy PO là Windows + Docker Desktop.
   Cái này KHÔNG đóng được từ đây.
🔴 Chưa đăng nhập bằng tài khoản thật rồi bấm thử luồng chat — chỉ xác nhận trang
   đăng nhập DỰNG RA được, chưa xác nhận đăng nhập XONG được.
```
⟹ Hai vế trên là chỗ **nhiều khả năng sai nhất** — báo đội, đừng tự sửa.
