# Gửi devops — hai đoạn cần thêm/sửa trong `docs/DEPLOY.md`

> Người gửi: Coder (`p-226-63`), 25/08. **Tôi KHÔNG tự ghi — `docs/DEPLOY.md` là vùng của devops (§4).**
> Cả hai đoạn đều có số đo kèm theo, không phải đề nghị suông.

---

## ĐOẠN 1 — thêm vào phần dựng lại/deploy, đặt NGAY CẠNH lệnh `docker compose up -d --build`

> ⚠️ **Build chết giữa chừng với một lỗi lạ bên trong `pip`** *(vd `JSONDecodeError`,
> `IncompleteRead`, `Connection broken`)* ⟹ **CHẠY LẠI ĐÚNG LỆNH ẤY MỘT LẦN trước khi đi tìm bug.**
>
> **[ĐO 25/08]** một lần `docker compose build --no-cache` từ cây sạch đỏ tại bước `pip install`
> với `json.decoder.JSONDecodeError: Expecting ',' … char 5980170`. **Chạy lại đúng bước ấy: XANH,
> không sửa một dòng nào.**
>
> 🔴 **Vì sao phải viết ra:** lỗi tải gói nhất thời **không đọc ra là lỗi mạng** — nó hiện ra như
> một lỗi *phân tích dữ liệu* sâu trong `pip`, và người ta sẽ đi tìm lỗi **trong mã**. Chính người
> đo suýt kết luận *"cây sạch KHÔNG dựng được"* từ đúng lần đỏ ấy.
>
> Đã thêm `--retries 5 --timeout 60` vào cả hai lệnh `pip install` trong `Dockerfile` — nhưng
> **KHÔNG hứa** nó cứu được đúng ca trên: `--retries` bắt ở tầng *kết nối*, còn lỗi ấy xảy ra khi
> phản hồi **đã về đủ về mặt giao thức nhưng nội dung bị cắt**. **Chạy lại vẫn là cách chắc nhất.**

**Vì sao một dòng này đáng hơn mọi cơ chế:** nó phủ được cả **kiểu hỏng chưa từng thấy**, vì nó
không cần biết lỗi tên gì. Mọi bộ khớp theo danh sách lỗi đã biết đều đi sau thực tế đúng một sự cố.

---

## ĐOẠN 2 — 🔴 nền tảng SAI từ dòng đầu tệp

`docs/DEPLOY.md` mô tả **"Oracle Cloud Always Free + SSH vào VPS"**. Sai.

> **[PO thật, 25/08]** *"Đây là máy cá nhân **Windows** của tôi và tôi bật nó **24/7** để làm server."*

⟹ Mọi hướng dẫn dựa trên *"SSH vào VPS Linux"* **không áp dụng**. Ghi chú *"nghi đường thật là
**Cloudflare Tunnel**, CHƯA XÁC MINH"* ở đầu tệp nay **gần như chắc đúng**.
Giữ nguyên văn cũ **gạch ngang** theo Luật P, ghi nguồn **PO thật 25/08**.

**Kèm hai dữ kiện đo được, dùng luôn khi viết lại:**
```
[PO thật chạy `docker volume ls` trên máy ấy]
  fin05_postgres_data · fin05_chroma_data · fin05_logs_data · fin05_caddy_data · fin05_caddy_config
  🔴 fin05_redis_data KHÔNG CÓ  ⟹ bản vá Redis 25/08 CHƯA lên production
[deploy] THỦ CÔNG: `git pull` + `docker compose` — job `deploy.yml` CHƯA BAO GIỜ chạy
  (320 lượt: 319 skipped, 1 failure, 0 success)
```

---

## ĐOẠN 3 — cập nhật mục "`docker compose down -v` ĐỔI NGHĨA từ 25/08" (đang NÓI NHẸ ĐI)

Mục ấy viết *"xoá bộ đếm chi tiêu LLM và phiên đăng nhập"*. **[ĐO] `docker compose config --volumes`
= SÁU kho**, gồm **TOÀN BỘ CSDL** *(ticket · khiếu nại · resolution · transcript chat)* **và chỉ mục
RAG**. Trên máy PO đó là **dữ liệu khách hàng thật**.

**Nay đã có bảo vệ thật (`e5ee8cd`)** — `postgres_data` khai `external: true`, `down -v` **không xoá
được nó nữa**, phải `docker volume rm fin05_postgres_data` tường minh. Nhưng năm kho còn lại **vẫn
mất**, nên câu trong tài liệu phải nói đúng phạm vi.
