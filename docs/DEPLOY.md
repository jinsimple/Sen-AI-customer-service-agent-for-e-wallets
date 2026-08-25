# Deploy live — Oracle Cloud Always Free + Docker Compose

> 🔴🔴 **[PO THẬT, 25/08] SAI NỀN TẢNG TỪ TIÊU ĐỀ — production KHÔNG PHẢI Oracle Cloud.**
> Nguyên văn: *"Đây là máy cá nhân **Windows** của tôi và tôi bật nó **24/7** để làm server."*
>
> **Đường THẬT — dùng file này, không phải các mục 1–7 bên dưới:**
> [`docs/giao-viec/2026-08-15-chay-that-tai-nha-windows-tunnel.md`](giao-viec/2026-08-15-chay-that-tai-nha-windows-tunnel.md)
> (viết ngày 15/08, tự khai ngay dòng 4: *"Thay thế `docs/DEPLOY.md` cho đường triển khai tại
> nhà — `DEPLOY.md` là tài liệu đợt P-121 CHƯA AI THỰC THI"*). Deploy/cập nhật bằng script đã
> có sẵn, đã idempotent: `scripts/deploy_home.ps1` (Windows) / `.sh` (Linux/Mac tham khảo) —
> KHÔNG SSH tay, KHÔNG mục 1–4 bên dưới. Nghi ngờ "Cloudflare Tunnel" ở khối đính chính 20/08
> ngay dưới đây nay **được xác nhận đúng bằng đúng cơ chế này**, không còn là nghi vấn.
>
> **Vì sao 10 ngày không ai sửa `DEPLOY.md`:** file thay thế đã tồn tại từ 15/08 nhưng chỉ
> "thay thế" bằng lời tự khai trong chính nó — không có dòng nào ở ĐÂY trỏ ngược lại. Một tài
> liệu tự nhận đã lỗi thời mà không ai đọc nó không khác gì tài liệu không tự nhận gì cả.
>
> **Hai dữ kiện đo được trên máy production thật, 25/08 — dùng làm nền cho mọi quyết định sau:**
> ```
> [PO thật, docker volume ls]
>   fin05_postgres_data · fin05_chroma_data · fin05_logs_data
>   · fin05_caddy_data · fin05_caddy_config
>   🔴 fin05_redis_data KHÔNG CÓ ⟹ bản vá bền hoá Redis 25/08 (02892bd) CHƯA lên production —
>      trần chi tiêu LLM/ngày và sổ thu hồi phiên trên máy đó vẫn mất khi container Redis bị
>      gỡ, đúng cảnh báo ở mục "down -v" bên dưới.
> [deploy.yml] CHƯA BAO GIỜ chạy thành công thật: 320 lượt — 319 skipped, 1 failure, 0 success.
>   Deploy production tới nay là THỦ CÔNG: `git pull` + `docker compose` trên chính máy đó,
>   qua `scripts/deploy_home.ps1`, không qua GitHub Actions. Mục 7 bên dưới ("Bật auto-deploy")
>   mô tả một cơ chế chưa từng chạy thật cho ngăn production hiện có.
> ```
>
> **Việc CHƯA làm, ghi lại để không rơi mất (đúng Luật X):** viết lại toàn bộ file này lấy
> `scripts/deploy_home.ps1` làm trung tâm, chuyển mục 1–7 hiện tại xuống thành "đường thay thế
> — Oracle Cloud VPS, chưa từng dùng cho production thật" thay vì xoá (Luật P — SSH/Docker/
> Caddyfile/CI dưới đây vẫn đúng kỹ thuật, chỉ sai vai trò "đây là đường chính"). Việc lớn hơn
> phạm vi một bản vá, cần một phiên riêng.

> ✅ **[PO THẬT ĐÍNH CHÍNH 25/08/2026] `app.adaptivealgo.uk` ĐANG CHẠY `main` CỦA P-226.**
> Nguyên văn PO thật: *"Domain này đang là P-226 nhánh main rồi bạn ơi — bạn đọc doc nào bảo là
> P-121 thì sửa ngay lại cái doc đấy luôn cho mình nhé."*
>
> 🔴 **Mọi phát biểu «domain chạy repo `jinsimple/P-121-new`» trong repo này ĐÃ LỖI THỜI.** Chúng
> đúng lúc DevOps đo *(20/08)*, và **sai từ lúc nào đó giữa 20/08 và 25/08** — không ai cập nhật.
> Giữ nguyên văn cũ **gạch ngang** theo Luật P, **không xoá**: một phép đo đúng-lúc-đo mà **không
> ai niêm hạn dùng** là cách một con số chết tiếp tục lái quyết định suốt năm ngày.
>
> ⚠️ **Hệ quả:** việc đưa P-226 lên production **KHÔNG phải "thay một dự án khác"** như tài liệu
> này từng mô tả. Nó là **cập nhật chính sản phẩm đang chạy** — rủi ro khác hẳn, và **cần đúng
> loại cẩn thận khác**.

> ~~**[ĐO DevOps 20/08 — LỖI THỜI, xem đính chính ngay trên]** `app.adaptivealgo.uk` hiện chạy repo `jinsimple/P-121-new`,~~
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

🔴 **[SỬA 25/08] Vì sao dùng `.env.example` (mẫu DEV) chứ không phải
`.env.production.example` (đã có sẵn `APP_ENV=production` đúng) làm nền cho
VPS thật — không rõ lý do gốc, không tìm thấy ghi chú nào giải thích lựa
chọn này. Giữ nguyên lời dặn cũ (đổi sang `.env.production.example` là một
thay đổi rộng hơn, cần soát lại toàn bộ khác biệt giữa hai mẫu, không phải
việc của bản vá một dòng này) — chỉ bổ sung dòng `APP_ENV` còn thiếu bên
dưới, vì thiếu đúng dòng đó từng làm `/docs`/`/redoc`/`/openapi.json` (32
route kèm schema) mở công khai trên một ngăn dựng đúng theo tài liệu này.

Điền vào `.env` (mỗi dòng 1 biến, xem `.env` trên máy dev để biết đủ danh
sách — **KHÔNG copy nguyên giá trị dev sang**, sinh key mới cho production):

```bash
APP_ENV=production                       # 🔴 BẮT BUỘC đổi — .env.example nền
                                          # để development, quên dòng này thì
                                          # /docs · /redoc · /openapi.json mở
                                          # công khai toàn bộ route + schema
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

⚠️ **Build chết giữa chừng với một lỗi lạ bên trong `pip`** (vd `JSONDecodeError`,
`IncompleteRead`, `Connection broken`) ⟹ **CHẠY LẠI ĐÚNG LỆNH ẤY MỘT LẦN trước khi đi tìm bug.**

**[ĐO 25/08]** một lần `docker compose build --no-cache` từ cây sạch đỏ tại bước
`pip install` với `json.decoder.JSONDecodeError: Expecting ',' … char 5980170`. Chạy lại
đúng bước ấy: **XANH, không sửa một dòng nào.**

🔴 Vì sao đáng viết ra: lỗi tải gói nhất thời không đọc ra là lỗi mạng — nó hiện ra như một
lỗi *phân tích dữ liệu* sâu trong `pip`, và người ta sẽ đi tìm lỗi trong mã. `Dockerfile` đã
có `--retries 5 --timeout 60` ở cả hai lệnh `pip install` (`d504c40`), nhưng đó là cờ tầng
*kết nối* — ca trên là phản hồi đã về đủ về mặt giao thức nhưng nội dung bị cắt, cờ retry
không hứa cứu được đúng ca đó. Chạy lại vẫn là cách chắc nhất, vì nó không cần biết lỗi tên
gì — phủ được cả kiểu hỏng chưa từng thấy.

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

### ⚠️ `docker compose down -v` ĐỔI NGHĨA từ 25/08 — và bản mô tả đầu tiên NÓI NHẸ ĐI

🔴 **[SỬA 25/08, tự đính chính]** Bản đầu của mục này (viết sáng 25/08, ngay sau `02892bd`)
chỉ nói `down -v` xoá "bộ đếm chi tiêu LLM và phiên đăng nhập" — **nói nhẹ đi**. [ĐO]
`docker compose config --volumes` liệt kê **SÁU kho**, gồm cả `postgres_data` — **TOÀN BỘ
CSDL** (ticket, khiếu nại, resolution, transcript chat) và `chroma_data` (chỉ mục RAG). Trên
máy production (máy Windows cá nhân của PO — xem đính chính đầu file), đó là **dữ liệu
khách hàng thật**. Lý do sai: người viết mục này cùng lúc đang thêm `redis_data`, nên mô tả
đúng thứ mình vừa thêm, và câu ấy bị đọc thành mô tả cho CẢ LỆNH.

✅ **Nay đã có bảo vệ thật cho phần nặng nhất** (`e5ee8cd`) — `postgres_data` khai
`external: true` trong `docker-compose.yml`, `down -v` **không xoá được nó nữa**: compose in
`"volume ... is external, skipping"` rồi bỏ qua. Muốn xoá thật phải gõ tường minh
`docker volume rm fin05_postgres_data` — một câu không ai gõ nhầm.

🔴 **Nhưng NĂM kho còn lại vẫn mất theo `down -v`:**

| kho | mất gì | phục hồi được không |
|---|---|---|
| `redis_data` | **bộ đếm chi tiêu LLM/ngày** (`fin05:chi_tieu_llm_token:*`) — trần ngày về 0, quên phần đã tiêu, **quên IM LẶNG**; **phiên đăng nhập** (`refresh:*`) — fail-closed đúng thiết kế (`auth.py:172-174`), phiền chứ không phải lỗ | không — mất vĩnh viễn phần đã tiêu |
| `chroma_data` | chỉ mục RAG chính sách | có — `scripts/kho_rag.py nap-lai` (tốn embedding thật) |
| `logs_data` | `access.log` (audit log) | không |
| `caddy_data`/`caddy_config` | chứng chỉ TLS | có — Caddy tự xin lại Let's Encrypt |

Muốn hạ ngăn xếp mà **giữ** cả sáu: dùng `docker compose down` **KHÔNG có `-v`**. Chỉ dùng
`-v` khi **CỐ Ý** muốn mất năm kho phụ ở trên — `postgres_data` giờ an toàn khỏi `-v`, nhưng
đừng đọc điều đó thành "an toàn khi gõ `-v`", vì `redis_data`/`logs_data` vẫn mất thật và
không phục hồi được.

- **Xem log backend khi có lỗi**: `docker compose logs -f backend` (hoặc
  `frontend`/`caddy`/`postgres`).
- **Audit log bảo mật** (`logs/access.log`) nằm trong volume `logs_data`, xem
  bằng: `docker compose exec backend cat /app/logs/access.log`.
- **Backup DB**: `docker compose exec postgres pg_dump -U fin05 fin05 >
  backup-$(date +%F).sql` — nên chạy định kỳ, đặc biệt trước khi đổi
  `FIELD_ENCRYPTION_KEY` (đổi key sẽ làm dữ liệu cũ đã mã hoá không đọc được
  nữa, không có cách khôi phục).
- **Xoá sạch làm lại từ đầu**: `docker compose down -v` (xoá **năm trong sáu**
  volume — `postgres_data` giờ an toàn khỏi lệnh này (`external: true`,
  `e5ee8cd`), nhưng bộ đếm chi tiêu/phiên đăng nhập/audit log/chỉ mục RAG/
  chứng chỉ TLS vẫn mất, chỉ dùng khi chắc chắn — xem bảng đầy đủ phía trên).
  Muốn xoá luôn CSDL: `docker volume rm fin05_postgres_data` tường minh, sau
  khi `down -v`.
- **Deploy lại thủ công** (không đợi push code): `cd /opt/fin05 && git pull
  && docker compose up -d --build`, hoặc vào tab Actions trên GitHub bấm "Run
  workflow" (đã bật `workflow_dispatch`).
- **Xem trace agent (Jaeger UI)** — chỉ bind loopback trên VPS (không public,
  xem docs/TESTING.md phần Observability), truy cập qua SSH tunnel:
  `ssh -L 16686:localhost:16686 <user>@<vps-ip>` rồi mở
  `http://localhost:16686` trên máy mình, chọn service `fin05-backend`.
