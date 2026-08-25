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

## Cập nhật code trên production (đổi UI, đổi backend, mọi thay đổi) — đường THẬT

```powershell
cd <thư mục repo trên máy Windows>
.\scripts\deploy_home.ps1
```

Đó là toàn bộ lệnh. Script **tự** `git pull --ff-only`, tự build lại image nào có code đổi
(so khớp qua `docker-compose.yml`, không cần biết trước là frontend hay backend), tự chờ
`/health` xanh, tự kiểm kho RAG, tự xác nhận Cloudflare Tunnel đã nối. **Đọc `[LOI]` màu đỏ nếu
có** — script dừng và nói rõ bước nào hỏng, không tự đoán tiếp.

⚠️ **Luật Đ′ — cây làm việc phải ĐỨNG YÊN suốt lúc script chạy.** Đừng bấm script trong lúc
Coder đang commit dở trên `main` — `git pull --ff-only` giữa chừng một đợt land nhiều commit có
thể kéo về một trạng thái nửa vời. Hỏi trước "code đã land xong hết chưa" rồi mới chạy.

### Lùi lại một bản deploy (rollback)

🔴 **Không có "rollback ảnh"** — dự án build thẳng trên máy, không đẩy lên container registry
nào (xem `deploy.yml`, cố ý để đơn giản cho quy mô pilot). Cách lùi DUY NHẤT là lùi **mã nguồn**
trên `main` rồi build lại, không phải chuyển sang một image cũ đã lưu sẵn.

🔴 **ĐỪNG `git checkout <sha cũ>` trực tiếp trên máy production.** `deploy_home.ps1` luôn
`git pull --ff-only origin main` ở đầu — chạy lại script sau khi checkout thủ công sẽ kéo `main`
mới nhất về, xoá mất chỗ lùi vừa làm (hoặc lệnh `pull` tự chối chạy vì không còn là fast-forward
từ trạng thái detached HEAD). Rollback đúng cách đi qua git trước, máy production chỉ chạy lại
đúng một lệnh quen thuộc:

```powershell
# 1. TRÊN MÁY DEV (không phải máy production) — lùi main bằng một commit MỚI,
#    không sửa lịch sử cũ. Thay <sha-gay-loi> bằng commit thật của bản đổi UI.
git revert <sha-gay-loi>
git push origin main

# 2. TRÊN MÁY PRODUCTION (Windows) — chạy lại ĐÚNG lệnh deploy bình thường,
#    không có lệnh "rollback" riêng biệt nào khác:
cd <thư mục repo>
.\scripts\deploy_home.ps1
```

`git revert` tạo một commit MỚI đảo ngược thay đổi (không xoá lịch sử, không force-push) — đúng
Luật P của dự án, và an toàn khi nhiều phiên đang cùng đọc/ghi nhánh `dev/learning-loop`/`main`.
Nếu bản lùi lại vẫn xấu hơn bản trước nữa, `git revert` chính commit revert đó — không giới hạn
số lần, mỗi lần đều là một commit mới, không phải viết đè.

**Xác nhận rollback thật sự có hiệu lực** — đừng tin "script chạy xong không lỗi" là đủ:
```powershell
# build_commit trong /health PHẢI khớp commit vừa revert-và-push, không phải
# commit gây lỗi — so ĐÚNG loại với ĐÚNG loại, đừng lấy build_commit so với
# build_src_hash (hai nhãn khác nhau, xem src/dau_ma_nguon.py)
git rev-parse --short HEAD
curl.exe -s https://app.adaptivealgo.uk/health | ConvertFrom-Json | Select-Object build_commit, build_src_hash
# Mở https://app.adaptivealgo.uk TỪ MỘT MÁY KHÁC (không phải máy vừa deploy), xác nhận
# giao diện đã về đúng trạng thái cũ — đúng bước nghiệm thu cuối script tự nhắc
```

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
  nữa, không có cách khôi phục). **Xem mục "Khôi phục — diễn tập" ngay dưới
  trước khi tin file `.sql` này cứu được bạn.**

### 🔴 Khôi phục từ backup — diễn tập, không phải suy luận

> **Một bản sao lưu chưa từng khôi phục thử KHÔNG PHẢI là bản sao lưu — nó là một tệp và một
> niềm tin.** Niềm tin đó chỉ bị kiểm chứng đúng vào lúc tệ nhất: sau khi đã mất dữ liệu thật,
> khi không còn đường lui nào khác.

**🔒 NIÊM — cập nhật MỖI LẦN diễn tập lại, để con số tự già đi cho người sau thấy:**
```
Diễn tập QUY TRÌNH (lệnh có chạy được không, dump có phục hồi sạch không)
  [ĐO 25/08, DevOps] ĐÃ LÀM — trên dump THẬT của ngăn `fin05do` (không phải
  backup của PO thật, xem lý do bên dưới), khôi phục vào container vứt đi,
  0 dòng lỗi trong log restore, 5/5 bảng cốt lõi khớp CHÍNH XÁC số dòng
  (users 206 · tickets 607 · complaints 607 · resolutions 0 · tool_results
  29), alembic_version khớp, 7 CHECK constraint trên `resolutions` (gồm
  BR-10/BR-11/BR-12 maker-checker) còn nguyên sau restore, extension
  `plpgsql` khớp. Container/dump xoá sạch ngay sau khi đo, KHÔNG để lại gì.

Diễn tập TỆP THẬT của PO (`backup-truoc-25-08.sql`, 307MB, trên máy Windows
  production) — 🔴 CHƯA BAO GIỜ. File này KHÔNG tồn tại trên máy DevOps
  đang thao tác — không đo được, và diễn tập bằng một dump khác rồi báo
  "đã diễn tập" là ĐO SAI VẬT, nguy hơn không đo vì tạo niềm tin sai. Việc
  còn treo, thuộc về PO thật (quy trình dưới đây, tự chạy trên máy họ).
```

**Vì sao đủ để tin quy trình đúng dù chưa chạm tệp thật:** `pg_dump`/`psql`/lược đồ/constraint
là cùng một cơ chế cho MỌI dump từ cùng schema — chạy sạch với dump `fin05do` (206 user, 607
ticket, 7 CHECK constraint) là bằng chứng cơ chế **không hỏng theo cách hệ thống**. Ba cách hỏng
điều phối (`p-226-f0`) nêu (`pg_dump` cắt giữa chừng · lệch phiên bản Postgres · thiếu
extension/role) là hỏng theo **VẬT CỤ THỂ** (file dump nào, máy nào) — thứ diễn tập trên
`fin05do` không loại trừ được cho đúng tệp `backup-truoc-25-08.sql`. Hai lớp bằng chứng khác
nhau, không thay thế nhau.

🟢 **[SỬA — điều phối (`p-226-f0`) chỉ ra] Hai trong ba cách hỏng KHÔNG cần restore để loại trừ.**
Dump cắt giữa chừng và lệch phiên bản Postgres đều đọc được **thẳng từ chính tệp**, trong vài
giây — xem BƯỚC 0
ngay dưới, đặt TRƯỚC 6 bước dựng container vì đúng thứ tự phải là RẺ TRƯỚC, ĐẮT SAU: nếu tệp bị
cắt, sáu bước sau là công toi. Chỉ **thiếu extension/role** là thật sự PHẢI restore mới lộ ra —
không đọc được từ nội dung tệp mà không chạy nó.

**Quy trình cho PO thật tự chạy trên máy Windows, với ĐÚNG tệp đó — RẺ TRƯỚC, ĐẮT SAU:**

```powershell
# BƯỚC 0 — đọc TỆP, KHÔNG dựng gì cả. Vài giây, loại được 2/3 cách hỏng
# TRƯỚC KHI tốn công dựng container ở bước 1. Nếu bước 0 đỏ, DỪNG — bước 1-6
# phía dưới là công toi cho tới khi có một tệp backup khác.

# 0a. Dump có CẮT GIỮA CHỪNG không — pg_dump kết ở dòng "... complete", nhưng
#     bản psql 16.x còn ghi thêm 1-2 dòng \unrestrict SAU dòng đó, nên tìm
#     TRONG vài dòng cuối, đừng đòi đúng dòng cuối cùng tuyệt đối.
Get-Content "C:\đường\dẫn\backup-truoc-25-08.sql" -Tail 5
#     KHÔNG thấy dòng "-- PostgreSQL database dump complete" ⟹ TỆP BỊ CẮT.
#     DỪNG Ở ĐÂY — bước 1-6 vô nghĩa với tệp này, cần dump lại từ đầu.

# 0b. Dump có LỆCH PHIÊN BẢN Postgres không — hai dòng này nằm sẵn gần đầu
#     tệp (khoảng 10 dòng đầu, sau khối \restrict):
Get-Content "C:\đường\dẫn\backup-truoc-25-08.sql" -TotalCount 10 | Select-String "Dumped from database version|Dumped by pg_dump version"
#     So với phiên bản ĐANG CHẠY thật — đọc động, đừng chép một số cố định ở
#     đây: tag ảnh `postgres:16-alpine` là tag DI ĐỘNG, bản đang chạy hôm nay
#     và hôm PO tạo backup có thể không cùng patch version dù cùng "16-alpine":
docker compose --profile home exec postgres postgres --version
#     Lệch bản VÁ (16.13 vs 16.14) thường vô hại. Lệch bản LỚN (15 vs 16) là
#     dấu hiệu backup này KHÔNG dump từ đúng stack — hỏi lại trước khi restore.

# 1. Container Postgres RỖNG, tên riêng, KHÔNG publish port ra host (không
#    cần — mọi lệnh chạy qua `docker exec`, tránh luôn rủi ro đụng cổng)
docker run -d --name fin05-restore-diendap `
  -e POSTGRES_USER=fin05 -e POSTGRES_PASSWORD=diendap-tam-thoi -e POSTGRES_DB=fin05 `
  postgres:16-alpine

# 2. Đợi sẵn sàng (vài giây)
docker exec fin05-restore-diendap pg_isready -U fin05 -d fin05

# 3. Nạp ĐÚNG tệp backup-truoc-25-08.sql — sửa đường dẫn cho khớp máy bạn
Get-Content "C:\đường\dẫn\backup-truoc-25-08.sql" -Raw | docker exec -i fin05-restore-diendap psql -U fin05 -d fin05
#    Đọc kỹ output — 0 dòng "ERROR" là điều kiện ĐẦU, không phải điều kiện đủ

# 4. Đếm 5 bảng cốt lõi trong container VỪA PHỤC HỒI
docker exec fin05-restore-diendap psql -U fin05 -d fin05 -t -c "select 'users',count(*) from users union all select 'tickets',count(*) from tickets union all select 'complaints',count(*) from complaints union all select 'resolutions',count(*) from resolutions union all select 'tool_results',count(*) from tool_results;"

# 5. Đếm CÙNG 5 bảng đó trên ngăn ĐANG SỐNG thật (production), SO SÁNH BẰNG MẮT
docker compose --profile home exec postgres psql -U fin05 -d fin05 -t -c "select 'users',count(*) from users union all select 'tickets',count(*) from tickets union all select 'complaints',count(*) from complaints union all select 'resolutions',count(*) from resolutions union all select 'tool_results',count(*) from tool_results;"

# 6. DỌN SẠCH — đây là container vứt đi, không phải một stack cần giữ
docker rm -f fin05-restore-diendap
```

🔴 **Số ở bước 4 KHÔNG khớp số ở bước 5 là điều BÌNH THƯỜNG nếu backup cũ hơn hiện tại** —
backup chụp tại một MỐC, production sống tiếp sau mốc đó. Điều cần đúng là: **số ở bước 4 phải
là số THỰC TẾ có ý nghĩa** (không phải toàn 0, không phải lỗi), và **chênh lệch với bước 5 giải
thích được bằng thời gian** (vd backup 3 ngày trước ít ticket hơn hôm nay là hợp lý; backup ít
hơn một nửa số user hiện có mà chỉ cách 1 giờ thì đáng nghi).

⚠️ Sau khi diễn tập xong — **cập nhật lại khối NIÊM ở trên** với ngày thật + kết quả thật. Đừng
để nó đứng yên ở "CHƯA BAO GIỜ" nếu đã làm — và đừng xoá dòng cũ, ghi đè bằng ngày mới (Luật P).
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

### 🔴 Trần chi tiêu LLM hằng ngày — chưa đặt, cần trước khi chia sẻ công khai

**[ĐO 25/08, đọc mã, không suy từ trí nhớ]** `TRAN_TOKEN_LLM_MOI_NGAY` (`src/config.py:368`) —
rỗng/thiếu ⟹ **không giới hạn**. Đơn vị: **token model CHAT nguyên**, KHÔNG gồm embedding
(khác nhà cung cấp — `src/config.py` giải thích tại chỗ vì sao cộng chung vô nghĩa). Đọc lúc
**IMPORT** ⟹ đổi giá trị bắt buộc **RECREATE container**, `docker exec -e` không đủ (cùng bẫy
đã ghi ở `PHAN_LUONG_BAT`).

**Điều gì xảy ra khi chạm trần — đã đọc hết đường đi, không đoán:** `cong_ra_ngoai.py` chặn ở
tầng transport (`GoiRaNgoaiBiChanError`), SDK nhà cung cấp bọc thành `openai.APIConnectionError`
(kế thừa `APIError`), `graph.py` bắt ở nhánh `except APIError` — khách **KHÔNG BAO GIỜ nhận
500**, nhận câu mềm *"hệ thống đang bận nên mình chưa xử lý kịp, bạn nhắn lại giúp mình sau ít
phút nhé"*. Ở tầng vận hành, log mức `warning` (không phải `error`), không tạo cảnh báo giả
"nhà cung cấp cần can thiệp" — `APIConnectionError` không nằm trong `_LOI_CAN_CAN_THIEP`.

🔴 **Một khoảng trống hành vi, khai ra chứ không giấu — thuộc `src/`, không tự sửa (vùng
tech-lead):** câu trả lời mềm ở trên hứa *"sau ít phút"* — đúng cho lỗi nhà cung cấp thoáng
qua, **SAI** cho ca chạm trần chi tiêu: trần reset lúc **00:00 UTC**, có thể còn hàng giờ, không
phải "vài phút". Hàm `la_bi_chan()` (`cong_ra_ngoai.py:96`) được viết sẵn CHÍNH ĐỂ phân biệt ca
này ("PHẢI DÙNG HÀM NÀY" — trích docstring) nhưng **0 lời gọi trong `src/`** — chưa được nối vào
`graph.py`. Không chặn việc đặt trần (khách vẫn được trả lời mềm, không 500), nhưng đề xuất
tech-lead nối `la_bi_chan()` vào nhánh `except APIError` để câu trả lời đúng lý do, tránh khách
nhắn lại liên tục trong ngày mà lần nào cũng bị chặn.

**Cách tính đề xuất — trình PO thật, PO quyết số cuối, KHÔNG tự đặt lên production:**

```
Mốc đo — [ĐO, tra được] `docs/DECISIONS.md:3003-3005` · `docs/nhat-ky/2026-08-25-ADR-051-du-
thao-cho-PO-duyet.md` · `docs/giao-viec/CHECKLIST-dot-otp-truoc-token.md:1570` (đo THẬT từ sổ
sống usage.jsonl TRONG container — 25/08, không phải 17/08 như trao đổi trước đó ghi):
  0 tool → 10.381 token (n=8, chắc)  ·  1 tool → 20.811 (n=4, chắc)  ·  3 tool → 41.444 (n=1)
🔴 **`n=1` ở điểm "3 tool" — MỘT quan sát duy nhất, ở đầu mút xa nhất.** Khớp tuyến tính với
n=8/n=4 là tín hiệu tốt, nhưng một mẫu đơn ở đầu mút không đủ để KHẲNG ĐỊNH tuyến tính giữ đúng
ngoài phạm vi đã thấy — khai `n` ra thay vì trình bày như số cùng độ tin cậy với hai điểm kia.
⟹ mỗi lời gọi tool ≈ +10.400 token (từ (20.811−10.381)/1 và (41.444−10.381)/3, hai ước lượng
  khớp nhau ~1%, nhưng dựa trên đúng ba điểm trên).

🔴 **"141.000 token/hội thoại 8-lượt" — KHÔNG PHẢI SỐ ĐO.** [Điều phối p-226-f0 tự xác nhận,
`git grep` toàn repo không ra kết quả nào khác dòng này] Đây là **con số điều phối tự mang vào,
không kiểm gốc**. Bỏ khỏi vai trò "mốc", giữ lại làm ĐIỂM Ở GIỮA một khoảng suy ra minh bạch:

  8 lượt, giả định KHÔNG tool call nào     ⟹  8 × 10.381 =  83.048 token   (SÀN)
  8 lượt, giả định 1 lời gọi tool/lượt     ⟹  8 × 20.811 = 166.488 token   (TRẦN)
  141.000 tương ứng ~0,7 lời gọi tool/lượt trung bình — nằm giữa hai mốc, HỢP LÝ (agent gọi
  lookup_transaction/search_policy phần lớn lượt, không phải mọi lượt), nhưng vẫn là GIẢ ĐỊNH
  về hành vi, không phải số đo cho đúng kịch bản 8-lượt.

⚠️ **[ĐÍNH CHÍNH 25/08, `docs/STATE.md:24`]** số TUYỆT ĐỐI chỉ đúng khi đo TRONG container —
`langchain-core` 1.5.3 (host/venv) vs 1.5.4 (container) sinh lược đồ tool khác nhau, lệch ~12%
dù mã giống hệt. Ba điểm nguồn trên đo TRONG container (usage.jsonl thật) ⟹ đúng loại dùng được
cho quyết định tiền; đối chiếu lại bằng venv host thì đừng lấy số đó thay.

Giá qwen3.7-plus quốc tế [ĐO 17/08, CÓ THỂ ĐÃ ĐỔI — xác nhận lại trước khi dùng số tiền để
  quyết]: $0,40 / 1M token vào · $1,20 / 1M token ra (giả định 100% vào/100% ra làm hai đầu cận
  — chưa có tỉ lệ vào:ra thật để tính điểm chính xác hơn)
```

**Bảng dựng thẳng từ hai mốc SÀN/TRẦN — mọi ô tra ngược được, không qua một điểm-giữa che giấu
giả định:**

| Hội thoại 8-lượt/ngày | Token/ngày (SÀN: 0 tool/lượt) | Token/ngày (TRẦN: 1 tool/lượt) | USD/ngày (SÀN–TRẦN) |
|---|---|---|---|
| 50 | 4.152.400 | 8.324.400 | $1,66 – $9,99 |
| 100 | 8.304.800 | 16.648.800 | $3,32 – $19,98 |
| 150 | 12.457.200 | 24.973.200 | $4,98 – $29,97 |
| 300 | 24.914.400 | 49.946.400 | $9,97 – $59,94 |
| 500 | 41.524.000 | 83.244.000 | $16,61 – $99,89 |

🟢 **[PO THẬT CHỐT 26/08, nguyên văn "5 triệu thôi bạn ơi"] `TRAN_TOKEN_LLM_MOI_NGAY=5000000`.**
Thấp hơn cả năm mức đề xuất ở bảng trên (bảng để nguyên làm bối cảnh, không bôi đậm hàng nào —
PO không chọn một trong các mức, mà chọn thận trọng hơn toàn bộ dải) — quyết định đã chốt,
không hỏi lại (`CLAUDE.md §5`). Con số này rơi TRONG khoảng SÀN–TRẦN của đúng hàng **50**
(4.152.400–8.324.400), lệch về nửa dưới. Quy đổi ngược từ hai mốc SÀN/TRẦN:
`5.000.000 ÷ 166.488 (TRẦN) ≈ 30` và `5.000.000 ÷ 83.048 (SÀN) ≈ 60` hội thoại 8-lượt/ngày ⟹
**~30–60 hội thoại/ngày**, tệ nhất ~$2–6/ngày theo giá đã dẫn.

### 🔴 Dấu hiệu ĐÃ CHẠM TRẦN — người trực buổi demo phải biết TRƯỚC, không phải tra cứu lúc đang cuống

Với `5.000.000` và PO dự kiến chia sẻ công khai ("chắc sẽ đông đấy"), **~20 người mỗi người 2
lượt chat là đủ chạm trần** — không phải kịch bản hiếm.

```
Dấu hiệu: khách nhận câu "Xin lỗi bạn, hệ thống đang gặp sự cố kỹ thuật nên tạm thời chưa xử lý
được yêu cầu này. Nếu việc của bạn cần xử lý ngay, bạn liên hệ <hotline> giúp mình nhé."
KHÔNG phải câu "hệ thống đang bận, bạn nhắn lại sau ít phút" — hai câu khác NGHĨA, không chỉ
khác chữ: câu sau hứa được, câu trên (đúng cho ca chạm trần) không hứa mốc thời gian.
[SỬA 26/08, `d749691`] Trước bản vá đó, chạm trần cho câu "sau ít phút" — SAI, vì trần chỉ reset
lúc 00:00 UTC (= 07:00 giờ VN), có thể còn hàng giờ, không phải "ít phút". Với trần 5 triệu —
thấp, dễ chạm — bản vá này đổi từ "hữu ích" thành "thiết yếu".

Mốc reset: 00:00 UTC = 07:00 giờ Việt Nam. Chạm trần lúc 20:00 VN thì phải chờ tới 07:00 sáng
hôm sau, không phải "vài giờ" — gần 11 tiếng nếu chạm sớm buổi tối.

Nâng gấp giữa buổi (PO tự quyết, không phải quy trình tự động): sửa `.env` + RECREATE — KHÔNG
phải restart, xem bước 2 dưới. Không có cách nâng "tạm thời" nhẹ hơn recreate.
```

**Cách đặt CẢ HAI biến trên máy Windows, cùng một lần gõ + xác nhận đã có hiệu lực** (gộp
`TRAN_TOKEN_LLM_MOI_NGAY` với `BAO_VE_CSDL` — cùng tệp `.env`, PO chỉ cần mở lên một lần):

```powershell
# 1. Thêm HAI dòng vào .env thật trên máy Windows (KHÔNG phải .env.example)
#    TRAN_TOKEN_LLM_MOI_NGAY=5000000
#    BAO_VE_CSDL=true

# 2. RECREATE backend — bắt buộc cho TRAN_TOKEN_LLM_MOI_NGAY (biến đọc lúc
#    import, restart KHÔNG đủ). BAO_VE_CSDL không cần recreate container nào
#    (chỉ đổi cách `docker compose` quản lý volume, có hiệu lực ngay ở lần
#    `up` kế tiếp — vd lần chạy deploy_home.ps1 sau) nhưng gộp vào MỘT lệnh
#    `up` cho gọn, không hại gì khi recreate cả hai cùng lúc:
docker compose up -d --force-recreate backend

# 3. Xác nhận TRAN_TOKEN_LLM_MOI_NGAY đã vào ĐÚNG container
docker compose exec backend printenv TRAN_TOKEN_LLM_MOI_NGAY
#   phải in ra 5000000 — rỗng nghĩa là chưa recreate đúng cách

# 4. Xác nhận BAO_VE_CSDL đã có hiệu lực — tìm dòng `external: true`, KHÔNG
#    so `true`/`false` (compose ẨN hẳn khoá `external` khi tắt, không in
#    `false` — xem .env.example)
docker compose config | Select-String -Context 0,2 "postgres_data:"

# 5. Xem chi tiêu HÔM NAY đang được đếm (không tốn tiền, chỉ đọc Redis) —
#    khoá theo NGÀY UTC, không phải giờ VN (UTC+7)
$ngay_utc = (Get-Date).ToUniversalTime().ToString("yyyyMMdd")
docker compose exec redis redis-cli get "fin05:chi_tieu_llm_token:$ngay_utc"
```

⚠️ **Đừng "test cho chắc" bằng cách cố tình chạm trần trên production** — đó là tự đốt đúng số
tiền đang muốn bảo vệ. Tin vào việc đọc mã (đã làm ở trên) thay vì gây sự cố thật để xem nó có
kêu không.
