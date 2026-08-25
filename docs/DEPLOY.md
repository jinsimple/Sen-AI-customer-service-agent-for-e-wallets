# Deploy live — Oracle Cloud Always Free + Docker Compose

> 🔴 **[ĐO DevOps 20/08] `app.adaptivealgo.uk` hiện chạy repo `jinsimple/P-121-new`,
> KHÔNG PHẢI repo này (P-226). P-226 CHƯA TỪNG lên site thật** — file này mô tả
> quy trình cho lần deploy ĐẦU TIÊN của P-226, nhưng bản thân nó được viết lúc
> repo tiền nhiệm còn dùng chung domain đó, nên vài chi tiết bên dưới **CHƯA
> XÁC MINH lại trên P-226**:
> - Production trả header `server: cloudflare` và `docker-compose.yml` của
>   P-226 có sẵn service `cloudflared` — nghi đường thật là **Cloudflare
>   Tunnel**, không phải "expose thẳng port 80/443 của Oracle VPS" như mục 1-2
>   dưới đây mô tả. **CHƯA XÁC MINH** — đừng làm theo mục 1-2 như sự thật tuyệt
>   đối, kiểm lại cấu hình DNS/tunnel thật trước.
> - Muốn checklist đã được **CHỨNG MINH bằng lần dựng-từ-clone-sạch thật**
>   (không phải chép lại tài liệu cũ), xem
>   [`docs/devops/2026-08-20-checklist-deploy-lan-dau.md`](devops/2026-08-20-checklist-deploy-lan-dau.md).
>
> Phần dưới đây giữ nguyên làm tham khảo kỹ thuật (Docker/Caddy/CI) — đã verify
> đúng cho luồng "VPS lộ thẳng port", chỉ chưa chắc đó là luồng THẬT của
> `app.adaptivealgo.uk` hôm nay.

Hướng dẫn đưa FIN-05 lên chạy thật, tester từ xa vào được qua
`https://app.adaptivealgo.uk`, tự deploy lại mỗi khi push code lên `main`.

Tất cả file cấu hình (Dockerfile, docker-compose.yml, Caddyfile,
.github/workflows/deploy.yml) đã có sẵn trong repo và đã verify chạy được cục
bộ (build cả 2 image, `docker compose up` đủ 4 service, login/chat/upload RAG
qua HTTPS, mã hoá at-rest xác nhận đúng trên Postgres). Phần còn lại dưới đây
là những việc **chỉ bạn tự làm được** — tôi không có quyền tạo tài khoản
cloud/DNS/GitHub secret hộ bạn.

## 1. Tạo tài khoản + máy chủ Oracle Cloud

1. Đăng ký tại [cloud.oracle.com](https://cloud.oracle.com) (cần thẻ để xác
   minh danh tính, **không bị trừ tiền** nếu chỉ dùng tài nguyên Always Free).
   Quy trình này hay báo lỗi xác minh thẻ hoặc "Out of host capacity" ở một số
   region — nếu gặp, thử lại sau vài giờ hoặc đổi region lúc tạo tài khoản
   (region Asia Pacific thường ít bị nghẽn hơn US).
2. Vào **Compute > Instances > Create Instance**:
   - Image: **Ubuntu 22.04** (hoặc mới hơn còn trong danh sách Always Free)
   - Shape: đổi sang **Ampere (ARM)**, chọn `VM.Standard.A1.Flex`, cấu hình
     **2 OCPU / 12 GB RAM** (nằm trong hạn mức Always Free tối đa 4 OCPU/24GB)
   - Thêm SSH key: chọn "Generate a key pair" và **tải private key về máy
     ngay lúc đó** (chỉ hiện 1 lần) — hoặc paste public key của bạn nếu đã có
   - Tạo instance, đợi vài phút tới khi trạng thái "Running", ghi lại **Public
     IP**.

## 2. Mở port 80/443 — 2 lớp firewall

Oracle chặn traffic ở CẢ 2 lớp, thiếu 1 trong 2 là không vào được site dù
container chạy khoẻ:

**Lớp 1 — Security List (web console):**
Instance detail → tab "Subnet" → vào Subnet đó → "Security Lists" → security
list mặc định → "Add Ingress Rules" → thêm 2 rule:
- Source `0.0.0.0/0`, IP Protocol TCP, Destination Port `80`
- Source `0.0.0.0/0`, IP Protocol TCP, Destination Port `443`

**Lớp 2 — firewall ngay trên VPS (SSH vào máy trước):**
```bash
ssh -i <đường-dẫn-private-key> ubuntu@<PUBLIC_IP>
sudo iptables -I INPUT -p tcp --dport 80 -j ACCEPT
sudo iptables -I INPUT -p tcp --dport 443 -j ACCEPT
sudo netfilter-persistent save   # lưu lại qua reboot, nếu lệnh không có: sudo apt install iptables-persistent -y rồi chạy lại
```

## 3. Cài Docker trên VPS

```bash
curl -fsSL https://get.docker.com | sudo sh
sudo usermod -aG docker $USER
# thoát SSH rồi đăng nhập lại để nhóm "docker" có hiệu lực
exit
ssh -i <private-key> ubuntu@<PUBLIC_IP>
docker --version && docker compose version
```

## 4. Trỏ domain

Vào trang quản lý DNS của `adaptivealgo.uk` (nơi bạn mua domain), thêm 1 bản
ghi:
- Type: `A`
- Name/Host: `app`
- Value: `<PUBLIC_IP>` của instance Oracle

Đợi vài phút tới vài giờ để DNS lan truyền — kiểm bằng `dig app.adaptivealgo.uk`
hoặc `ping app.adaptivealgo.uk` từ máy bạn, thấy đúng IP là được.

## 5. Clone repo + tạo `.env` thật trên VPS

```bash
sudo mkdir -p /opt/fin05 && sudo chown $USER:$USER /opt/fin05
cd /opt/fin05
git clone https://github.com/AI20K-Build-Phase-Cohort-3/P-226.git .
# 🔴 [SỬA 20/08] dòng trên TRƯỚC ghi `jinsimple/P-121-new.git` — SAI REPO
# (repo tiền nhiệm, không phải P-226). Nếu bạn thấy tài liệu/script nào khác
# còn ghi P-121-new, đó cũng là lỗi thời cùng nguồn, báo DevOps sửa.
cp .env.example .env   # mẫu compose cần — KHÔNG dùng .env.production.example
                        # cho DATABASE_URL (sai định dạng, bị compose ghi đè,
                        # xem chú thích trong .env.example)
nano .env   # điền các biến bên dưới
```

Điền vào `.env` (mỗi dòng 1 biến, xem `.env` trên máy dev để biết đủ danh
sách — **KHÔNG copy nguyên giá trị dev sang**, sinh key mới cho production):

```bash
OPENAI_API_KEY=sk-...                    # key thật, có thể dùng chung key dev nếu muốn
JWT_SECRET_KEY=...                       # sinh MỚI, xem lệnh dưới
FIELD_ENCRYPTION_KEY=...                 # sinh MỚI, xem lệnh dưới
POSTGRES_USER=fin05
POSTGRES_PASSWORD=...                    # mật khẩu MẠNH, không dùng giá trị dev
POSTGRES_DB=fin05
SITE_DOMAIN=app.adaptivealgo.uk          # để Caddy tự xin HTTPS đúng domain
```

Sinh 2 key bảo mật (chạy trên chính VPS, cần đã cài Docker ở bước 3 — dùng
tạm image python có sẵn, không cần cài Python lên VPS):
```bash
docker run --rm python:3.12-slim python3 -c "import secrets; print(secrets.token_urlsafe(48))"
docker run --rm python:3.12-slim pip install -q cryptography && python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

## 6. Deploy lần đầu (bằng tay)

```bash
cd /opt/fin05
docker compose up -d --build
docker compose logs -f backend   # xem alembic migrate + uvicorn khởi động, Ctrl+C để thoát log (container vẫn chạy)
```

🔴 **[ĐO DevOps 20/08] Trên DB HOÀN TOÀN RỖNG (đúng trường hợp lần đầu này),
log sẽ có một dòng lệnh Python chạy TUẦN TỰ giữa `alembic upgrade head` và
lúc `Uvicorn running` xuất hiện — đây là BÌNH THƯỜNG, ĐỪNG Ctrl+C giữa
chừng.** `docker-entrypoint.sh` cố ý hâm nóng lược đồ checkpointer một lần
trước khi mở 4 worker song song (né race `UniqueViolation` khi nhiều worker
cùng tạo bảng lần đầu — xem chú thích trong `docker-entrypoint.sh` và
`src/agents/graph.py::_build_checkpointer`). Nếu bạn thấy dòng
`UniqueViolation` / `Child process ... died` trong log dù đã có bước hâm
nóng này, đó LÀ bug thật, báo ngay — không phải điều đã biết.

**Dựng kho RAG chính sách — DỄ QUÊN, thiếu thì agent trả lời chung chung mà
KHÔNG báo lỗi nào** (kho vector `chroma_data` là volume, KHÔNG nằm trong git,
không tự có sau `docker compose up`):
```bash
docker compose exec backend su appuser -c "python3 scripts/kho_rag.py nap-lai"
docker compose exec backend su appuser -c "python3 scripts/kho_rag.py kiem"   # xác nhận không lệch chuẩn-hoá
```
⚠️ **`nap-lai` gọi API embedding THẬT (tốn tiền/hạn mức)** — [ĐO DevOps 20/08,
đọc source, KHÔNG tự chạy] `scripts/kho_rag.py` docstring. Không chạy lặp
nhiều lần, và không chạy song song với việc khác đang đo chi phí. Xem
`python scripts/kho_rag.py nhan` (chỉ ĐỌC, miễn phí) để kiểm nhãn kho hiện có
trước khi quyết có cần nạp lại không.

Nạp dữ liệu mẫu lần đầu (danh sách khách hàng/giao dịch demo cho tester dùng
thử — bỏ qua nếu bạn muốn DB trống hoàn toàn):
```bash
docker compose exec backend su appuser -c "python3 scripts/seed_db.py"
docker compose exec backend su appuser -c "python3 scripts/seed_demo_scenarios.py"
```

Mở `https://app.adaptivealgo.uk` — lần đầu Caddy tự xin chứng chỉ Let's
Encrypt (vài giây), sau đó vào được ngay. Đăng nhập thử cả 4 vai trò (số điện
thoại mẫu xem trong `data/generated/users.jsonl` sau khi seed, hoặc dùng
`0900000001` cho vai trò "Đối tác ví" nếu đã chạy `seed_demo_scenarios.py`).

## 7. Bật auto-deploy khi push code (GitHub Actions)

1. Tạo 1 SSH key **riêng cho việc deploy** (không dùng key cá nhân của bạn):
   ```bash
   ssh-keygen -t ed25519 -f ~/deploy_key -N ""
   cat ~/deploy_key.pub >> ~/.ssh/authorized_keys   # chạy trên VPS
   cat ~/deploy_key   # copy private key này — sẽ dán vào GitHub Secret
   ```
2. Vào repo trên GitHub → **Settings → Secrets and variables → Actions → New
   repository secret**, tạo 3 secret:
   - `DEPLOY_HOST` = IP public của VPS
   - `DEPLOY_USER` = `ubuntu`
   - `DEPLOY_SSH_KEY` = nội dung file `deploy_key` (private key) vừa tạo — dán
     nguyên văn kể cả dòng `-----BEGIN...`/`-----END...`
3. Push 1 thay đổi bất kỳ lên `main` — vào tab **Actions** trên GitHub xem
   workflow "Deploy" chạy, kiểm tra site cập nhật đúng.

Từ giờ, mỗi lần bạn sửa code + push lên `main`, site tự động build lại và lên
live sau khoảng 1-2 phút — không cần SSH tay nữa.

## Việc vặt cần biết thêm

### ⚠️ `docker compose down -v` ĐỔI NGHĨA từ 25/08

Redis nay có volume `redis_data` + `appendonly yes` (bền hoá chi phí/phiên,
`02892bd`) — trước bản đó Redis không có volume, mất sạch mỗi lần gỡ
container. **`down -v` nay XOÁ LUÔN:**

- **bộ đếm chi tiêu LLM theo ngày** (`fin05:chi_tieu_llm_token:*`) ⟹ trần
  ngày về 0, **quên phần đã tiêu, và quên IM LẶNG** — không có gì báo. Với
  dự án mà ràng buộc vận hành số một là ngân sách token, đây là cổng chi phí
  tự mở lại sau mỗi lần khởi động lại.
- **phiên đăng nhập** (`refresh:*`) ⟹ mọi người phải đăng nhập lại. Phiền,
  **không phải lỗ bảo mật** — đây là hành vi fail-closed đúng thiết kế
  (`auth.py:172-174`), không phải tác dụng phụ ngoài ý muốn.

Muốn hạ ngăn xếp mà **giữ** hai thứ trên: dùng `docker compose down` **KHÔNG
có `-v`**. Chỉ dùng `-v` khi **CỐ Ý** muốn về trạng thái trắng.

- **Xem log backend khi có lỗi**: `docker compose logs -f backend` (hoặc
  `frontend`/`caddy`/`postgres`).
- **Audit log bảo mật** (`logs/access.log`) nằm trong volume `logs_data`, xem
  bằng: `docker compose exec backend cat /app/logs/access.log`.
- **Backup DB**: `docker compose exec postgres pg_dump -U fin05 fin05 >
  backup-$(date +%F).sql` — nên chạy định kỳ, đặc biệt trước khi đổi
  `FIELD_ENCRYPTION_KEY` (đổi key sẽ làm dữ liệu cũ đã mã hoá không đọc được
  nữa, không có cách khôi phục).
- **Xoá sạch làm lại từ đầu**: `docker compose down -v` (xoá cả volume — MẤT
  HẾT dữ liệu, **kể cả bộ đếm chi tiêu và mọi phiên đăng nhập từ 25/08**, chỉ
  dùng khi chắc chắn muốn reset — xem cảnh báo phía trên).
- **Deploy lại thủ công** (không đợi push code): `cd /opt/fin05 && git pull
  && docker compose up -d --build`, hoặc vào tab Actions trên GitHub bấm "Run
  workflow" (đã bật `workflow_dispatch`).
- **Xem trace agent (Jaeger UI)** — chỉ bind loopback trên VPS (không public,
  xem docs/TESTING.md phần Observability), truy cập qua SSH tunnel:
  `ssh -L 16686:localhost:16686 <user>@<vps-ip>` rồi mở
  `http://localhost:16686` trên máy mình, chọn service `fin05-backend`.
