# Chạy FIN-05 thật tại nhà — máy bàn Windows + Cloudflare Tunnel

> **Người soạn: tech-lead (phiên coder P-226), 2026-08-15.** PO-agent chép nguyên văn vào
> `docs/` theo ranh giới vùng ghi (như F-MIG). Gói code tương ứng: commit `7ce57bd` trên `main`.
> Thay thế `docs/DEPLOY.md` cho đường triển khai tại nhà — **`DEPLOY.md` là tài liệu đợt P-121
> CHƯA AI THỰC THI**, mô tả một VPS chưa từng tồn tại và còn trỏ repo `P-121-new`. Đừng làm theo nó.

## Vì sao Cloudflare Tunnel chứ không mở port router

Mạng gia đình ở VN gần như luôn nằm sau **CGNAT** — nhà bạn không có IP công khai riêng, nên "mở
port 443 trên router" **không đủ**: gói tin từ Internet không biết đường về máy bạn. Tunnel làm
ngược lại: máy bạn **mở kết nối ĐI RA** tới Cloudflare rồi giữ nó, Cloudflare đẩy khách vào qua
đường đó.

Hệ quả phụ đáng giá: **không mở một cổng vào nào**. Bề mặt tấn công nhỏ hơn hẳn so với chĩa 443
thẳng vào máy trong nhà.

---

# PHẦN A — Việc làm MỘT LẦN trên máy Windows

### A1. Bật ảo hoá trong BIOS (nếu Docker báo lỗi)
Đa số máy đã bật sẵn. Chỉ làm nếu Docker Desktop báo thiếu: khởi động lại → vào BIOS (thường
`Del` hoặc `F2`) → tìm **Intel VT-x** / **AMD-V** / **SVM Mode** → **Enabled** → lưu và thoát.

### A2. Cài WSL2 + Docker Desktop
1. Mở **PowerShell với quyền Administrator**, chạy: `wsl --install`
2. Khởi động lại máy.
3. Tải **Docker Desktop for Windows** từ trang chủ Docker, cài, chọn dùng **WSL2 backend** khi được hỏi.
4. Mở Docker Desktop → **Settings → General** → bật **Start Docker Desktop when you log in**.
   Không bật thì mất điện xong dịch vụ không tự lên.

### A3. Máy KHÔNG được ngủ
**Settings → System → Power & battery → Screen and sleep** → đặt **Sleep = Never** (cả hai mục
nếu là laptop). Màn hình tắt thì không sao; **máy ngủ là dịch vụ chết**.

### A4. Lấy Cloudflare Tunnel token — BƯỚC TAY, không tự động hoá được
Bước này cần đăng nhập tài khoản cá nhân của bạn nên không script hoá.

1. Vào `dash.cloudflare.com` → **Zero Trust** → **Networks** → **Tunnels**
2. **Create a tunnel** → chọn **Cloudflared** → đặt tên (vd `fin05-home`)
3. Màn hình **Install connector** hiện một lệnh dài có chứa token — **chỉ copy phần token**
   (chuỗi rất dài sau `--token`). Không cần chạy lệnh đó.
4. Sang tab **Public Hostname** → **Add a public hostname**:

   | Ô | Điền chính xác |
   |---|---|
   | Subdomain | `app` |
   | Domain | `adaptivealgo.uk` |
   | Type | `HTTP` |
   | **URL** | **`caddy:80`** |

   ⚠️ Ô **URL** phải là **`caddy:80`** — đó là tên service trong `docker-compose.yml`, không phải
   `localhost`. Tunnel chạy trong cùng mạng Docker nên nó gọi hàng xóm bằng tên service. Điền
   `localhost` là tunnel tự gọi chính nó và không có gì trả lời. Type để **HTTP** (không phải
   HTTPS): TLS do Cloudflare lo ở phía ngoài.

5. **Save**.

---

# PHẦN B — Chuyển dữ liệu từ máy Mac sang

## ⚠️ BẪY CHẾT DỮ LIỆU SỐ 1 — đọc trước khi làm bất cứ gì

> ### `.env` phải mang sang với **`FIELD_ENCRYPTION_KEY` Y NGUYÊN**
>
> Các cột `EncryptedText` — nội dung chat, số tài khoản ngân hàng, đoạn chính sách, và mô tả
> khiếu nại — được mã hoá bằng **đúng khoá đó**. Sinh khoá mới trên máy Windows thì dữ liệu cũ
> **không giải mã lại được, vĩnh viễn**. Không có đường khôi phục, không có bản sao khoá ở đâu khác.
>
> **`JWT_SECRET_KEY`** cũng giữ nguyên (đổi thì mọi phiên đăng nhập hiện có vỡ — nhẹ hơn nhiều,
> nhưng không có lý do gì để đổi).

## ⚠️ BẪY CHẾT DỊCH VỤ SỐ 1 — cùng nằm trong `.env`, ngược hướng

> ### `SSL_CERT_FILE` phải **XOÁ** khi sang Windows
>
> Dòng đó trỏ `/Library/Frameworks/Python.framework/...` — đường dẫn **của máy Mac**. Nó cần cho
> một công cụ chạy trên Mac, nhưng khi `.env` đi sang máy khác thì đường dẫn đó không tồn tại.
>
> Đã cắn thật một lần: **mọi lượt chat của khách trả lỗi 500 trong 0,06 giây**, trong khi
> `docker ps` vẫn xanh hết vì trang kiểm tra sức khoẻ không đụng tới đường đó. Nhìn mọi dấu hiệu
> đều thấy "máy chủ khoẻ".
>
> Nghịch lý cần nhớ: **`.env` càng được mang sang trung thành thì lỗi càng chắc chắn tái hiện.**
> `docker-compose.yml` đã ghi đè giúp cho container, nên nó không còn chặn dịch vụ — nhưng xoá
> dòng đó đi vẫn sạch hơn.

**Nguyên tắc chung rút ra:** trong `.env` có hai loại biến — **bí mật** (mang sang y nguyên) và
**phụ thuộc máy** (phải sửa/xoá). Hiện tại loại thứ hai chỉ có `SSL_CERT_FILE`. Khi thêm biến mới
là đường dẫn tuyệt đối, ghi vào danh sách này ngay, đừng để lần chuyển máy sau dò tay.

## B1. Xuất dữ liệu trên máy Mac

```bash
cd ~/Code/Projects/P-226
docker exec fin05-postgres-1 pg_dump -U fin05 -d fin05 --clean --if-exists \
  > ~/Desktop/fin05-backup.sql
wc -l ~/Desktop/fin05-backup.sql          # phải hàng chục nghìn dòng, không phải 0
cp .env ~/Desktop/fin05.env
```

Chép **cả hai** file sang máy Windows (USB / Drive / OneDrive).

## B2. Nạp trên máy Windows

```powershell
cd C:\...\P-226            # thư mục repo sau khi git clone
copy ...\fin05.env .env    # rồi MỞ RA XOÁ dòng SSL_CERT_FILE, thêm CLOUDFLARE_TUNNEL_TOKEN

docker compose up -d postgres          # chỉ postgres, để nạp dữ liệu
docker exec -i fin05-postgres-1 psql -U fin05 -d fin05 < fin05-backup.sql
```

Kiểm nạp đúng chưa (số phải khớp máy Mac):

```powershell
docker exec fin05-postgres-1 psql -U fin05 -d fin05 -tAc `
  "SELECT (SELECT count(*) FROM users)||' user, '||(SELECT count(*) FROM transactions)||' giao dich'"
```

> Mẹo: mỗi câu đếm phải có `FROM` riêng. `SELECT count(*)` không có `FROM` trả về **1** và trông
> y hệt "mất sạch dữ liệu" — đã hoảng nhầm một lần vì đúng chỗ này.

---

# PHẦN C — Chạy

```powershell
.\scripts\deploy_home.ps1
```

Script tự làm: kiểm `.env` đủ 3 biến sống-chết → cảnh báo biến phụ-thuộc-máy → `git pull` → build
→ khởi động kèm tunnel → **kiểm tra thật** (`/health`, trang đăng nhập, 6 service, log tunnel đã
nối Cloudflare chưa).

Chạy lại bao nhiêu lần cũng vô hại. **Không đụng dữ liệu.** Mỗi lần có bản mới: chạy lại đúng lệnh đó.

> Nếu `.ps1` báo lỗi cú pháp: dùng `bash scripts/deploy_home.sh` trong WSL. Bản `.sh` đã được
> chạy thử thật; bản `.ps1` chưa (máy soạn không có PowerShell). Đó là đường lui có sẵn, không
> phải dấu hiệu hỏng.

---

# PHẦN D — Nghiệm thu: chỉ MỘT phép thử được tính

> ## Mở `https://app.adaptivealgo.uk` từ **máy khác**, hoặc điện thoại đã **TẮT WiFi** (dùng 4G)
> ## — và thấy màn hình đăng nhập.

Không tính: `docker compose up` không báo lỗi · script in toàn xanh · mở được từ chính máy đó.
Cả ba đều có thể xanh trong khi người ngoài không vào được.

Cả ngày hôm nay dự án đã trả giá nhiều lần cho đúng một lớp lỗi này — **mọi dấu hiệu nói khoẻ,
còn đường thật thì hỏng**. Phép thử từ máy khác là thứ duy nhất không tự lừa được.

---

# Khi có trục trặc

| Triệu chứng | Nhiều khả năng là |
|---|---|
| Script dừng ở `CLOUDFLARE_TUNNEL_TOKEN chua co gia tri` | Chưa dán token vào `.env` (Phần A4) |
| Tunnel không nối được | Token sai/hết hạn, hoặc máy mất mạng. Xem `docker compose --profile home logs cloudflared` |
| Máy khác báo lỗi 502 | Tunnel nối được nhưng ô **URL** trên dashboard sai — phải là `caddy:80` |
| Tên miền không phân giải | Chưa thêm **Public Hostname** ở Phần A4 bước 4 |
| Vào được nhưng chat trả lỗi | Xem có còn dòng `SSL_CERT_FILE` kiểu Mac trong `.env` không |
| Sáng ra dịch vụ chết | Máy đã ngủ (Phần A3) hoặc Docker không tự khởi động (Phần A2 mục 4) |

**Xem log:** `docker compose --profile home logs -f backend`
**Khởi động lại:** `docker compose --profile home restart`
