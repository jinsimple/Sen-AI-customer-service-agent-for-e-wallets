# Checklist deploy P-226 lần đầu lên VPS — 2026-08-20

> Viết cho **lần deploy P-226 ĐẦU TIÊN lên site thật** (P-226 CHƯA TỪNG lên
> production — xem cảnh báo đầu `docs/DEPLOY.md`). Khác `docs/DEPLOY.md` ở
> một điểm: **mọi bước dưới đây, trừ khi ghi rõ khác, đã được LÀM THẬT** bằng
> clone sạch + `docker compose up --build` trên DB hoàn toàn rỗng, trong ngăn
> xếp cô lập, KHÔNG đụng ba ngăn xếp `fin05`/`fin05ttl`/`fin05do` đang chạy.
> Không phải chép lại tài liệu cũ rồi đoán là đúng.

## 🔴 ĐỌC MỤC NÀY TRƯỚC KHI GÕ LỆNH ĐẦU TIÊN

Sáu chỗ đứt thật, tìm được bằng cách **chạy hết chuỗi trên clone sạch**
(20/08) — không chỗ nào đọc lại tài liệu mà thấy ra được, vì người viết tài
liệu luôn đứng trên một máy đã có sẵn thứ đang thiếu. Ba trong sáu nằm ở
bước cuối/bước xác nhận — đúng chỗ người deploy tin nhất là đã xong. Và
⑥ khác hẳn năm chỗ kia: nó **không kêu** — mọi thứ chạy đúng, chỉ là hở.

| # | triệu chứng bạn sẽ thấy | nguyên nhân thật | việc cần làm |
|---|---|---|---|
| ① | `git clone` xong, thiếu `.env.example`, `docker-entrypoint.sh` không có bản vá mới nào | nhánh vừa clone **chưa được push đủ** lên GitHub — kiểm `git log -1` khớp commit kỳ vọng chưa | Xác nhận với DevOps/PO-agent commit HEAD đúng trước khi làm gì tiếp. Đừng tự đoán thiếu biến gì rồi tự chế `.env` |
| ② | `kho_rag.py nhan`/`kiem` báo `[SAI CHỖ]` dù bạn ĐANG chạy trong container | thông báo cũ dùng chung cho hai nguyên nhân khác nhau (chạy nhầm trên host / kho thật sự chưa từng nạp) — đã vá, giờ có dòng phân biệt | Đọc hết cả 2 nhánh trong thông báo. Nếu bạn đã ở trong container: kho chưa từng nạp, chạy `kho_rag.py nap-lai` (tốn tiền embedding thật) |
| ③ | `seed_db.py` báo `FileNotFoundError: Thiếu .../transactions.jsonl` | file 60K dòng CỐ Ý không nằm trong git (quá lớn để commit) — không phải thiếu sót, không tự ý commit nó | Chạy `scripts/gen_dataset.py --seed 20260802 --out data/generated/ --eval-out /tmp/eval_out/` TRƯỚC `seed_db.py` — xem bước 5 |
| ④ | `seed_demo_scenarios.py` dừng giữa chừng với `CheckViolation: ck_resolutions_rejected_requires_reason_br11` | **ĐÃ VÁ** (`0f5bd34`) — nếu vẫn thấy lỗi này, bạn đang chạy trên ảnh/commit CŨ hơn, không phải lỗi mới | Xác nhận `BUILD_COMMIT` trong container ≥ `0f5bd34` trước khi báo bug |
| ⑤ | `curl -f https://<domain>/health` trả về "thành công" (307) | 🔴 **BÁO ĐỘNG GIẢ TUYỆT ĐỐI — đã chứng minh bằng cách tắt hẳn backend rồi curl lại, VẪN ra cùng 307.** Mọi route qua Caddy (trừ `/ws/live-chat*`) vào `frontend` trước; `frontend/src/proxy.ts` chặn TẠI EDGE cho path chưa đăng nhập, redirect không bao giờ chạm backend | **Nếu bạn dùng `curl /health` qua domain và thấy xanh — BẠN CHƯA CHỨNG MINH ĐƯỢC GÌ về backend.** Kiểm backend thật qua SSH+docker (bước 6, lớp 1), không qua domain công khai |
| ⑥ | 🔴 **KHÔNG CÓ TRIỆU CHỨNG NÀO CẢ** — mọi thứ chạy bình thường, đăng nhập được, chat được. Chỉ là `/docs`, `/openapi.json`, `/redoc` (34 route + schema API) mở công khai ra Internet | [ĐO Bảo Mật + DevOps 20/08] `.env.example` bản cũ KHÔNG có dòng `APP_ENV` ⟹ mặc định code `"development"` (`src/config.py:71`) ⟹ `main.py:151` không bật chặn docs. Nguy hiểm hơn cả 5 chỗ trên CỘNG LẠI vì 5 chỗ kia đều KÊU khi hỏng, chỗ này IM — **kể cả người viết checklist (tôi) suýt tự đọc nhầm `curl /openapi.json` qua domain ra 307 thành "đã chặn", đúng cùng bẫy ở ⑤, chỉ thoát vì nhớ phải hỏi thẳng backend** | **ĐÃ VÁ trong `.env.example`** — giờ có dòng `APP_ENV=development` kèm cảnh báo tường minh phải đổi `production` trên VPS. Kiểm sau deploy: `curl -k https://<domain đã login>/openapi.json` qua domain KHÔNG đủ (cùng bẫy proxy 307) — phải hỏi thẳng `docker compose exec backend curl localhost:8010/openapi.json`, kỳ vọng KHÔNG PHẢI 200 |

## Đã CHỨNG MINH bằng đo thật (20/08, DevOps)

| bước | lệnh | kết quả đo |
|---|---|---|
| Build sạch, không cache/`.env` sẵn | `docker compose build backend` | Ảnh dựng xong, băm nguồn trong ảnh khớp host |
| Dựng từ DB **hoàn toàn rỗng** | `docker compose up -d postgres redis backend` | `alembic` chạy đủ chuỗi migration từ đầu → `a8b9c0d1e2f3 (head)` |
| Container tự dậy lại | `docker exec … alembic current` | Ra head sạch, không lỗi |
| Backend healthy | `docker inspect … .State.Health.Status` | `healthy` sau ~30s |
| `/health` trả đúng nhãn | `GET /health` từ trong container | `{"status":"ok","build_src_hash":...,"build_commit":...}` |
| Race checkpointer đa-worker (TRƯỚC vá) | dựng DB rỗng, đọc log | 3/4 worker crash `UniqueViolation`, tự respawn |
| Race checkpointer đa-worker (SAU vá, `docker-entrypoint.sh` commit `8890cd9`) | dựng lại DB rỗng, đọc log | 4/4 worker lên NGAY LẦN ĐẦU, 0 lỗi |
| Frontend build + serve | `docker compose up -d frontend` | Next.js `✓ Ready`, không lỗi build |
| Caddy tự xin TLS + route | `curl -k https://localhost:<port>/` | `307 → /login`, follow redirect ra `200` |

**Chưa đo trong vòng này** (không phải vì nghi có lỗi, mà vì chưa tới lượt —
đừng đọc "chưa đo" thành "đã ổn"):
- `jaeger` — đã biết backend graceful-degrade khi thiếu (comment sẵn trong
  `docker-compose.yml`, quan sát log OTLP warning không chặn health), nhưng
  KHÔNG tự đo full trace pipeline
- `cloudflared` — cần `CLOUDFLARE_TUNNEL_TOKEN` thật, không có token giả an
  toàn để test; `profiles: ["home"]` nên KHÔNG start trừ khi gọi
  `--profile home`
- `scripts/kho_rag.py nap-lai` — gọi API embedding THẬT, tốn tiền, KHÔNG tự
  chạy trong vòng kiểm này (xem cảnh báo trong `docs/DEPLOY.md`)
- `scripts/seed_db.py` / `seed_demo_scenarios.py` — chưa tự chạy trong ngăn
  xếp cô lập; theo `docs/DEPLOY.md` đã verify trước (giữ nguyên tin cậy)
- Domain/DNS/Cloudflare Tunnel thật — chỉ test được bằng `localhost` +
  chứng chỉ tự ký cục bộ của Caddy, không phải chứng chỉ Let's Encrypt qua
  domain thật

## Trình tự đề nghị cho lần deploy đầu

### 0. Xác định lại đường mạng THẬT trước khi làm theo mục 1-4 của `docs/DEPLOY.md`

🔴 `docs/DEPLOY.md` mô tả "Oracle VPS lộ thẳng port 80/443". Nhưng
`docker-compose.yml` có sẵn service `cloudflared` (`profiles: ["home"]`) và
production hiện tại (`app.adaptivealgo.uk`, repo khác) trả header
`server: cloudflare` — dấu hiệu đường thật có thể là **Cloudflare Tunnel**,
không phải expose thẳng port. **CHƯA XÁC MINH cho P-226.** Trước khi làm
theo mục 1-2 của DEPLOY.md (mở port 80/443, security list Oracle), xác nhận
với PO thật: site mới có dùng lại tunnel/domain cũ không, hay tách hẳn.
Nếu dùng tunnel: bỏ qua mục 1-2 (mở port) của DEPLOY.md, dùng profile `home`
(`docker compose --profile home up -d`) và điền `CLOUDFLARE_TUNNEL_TOKEN`.

### 1. Chuẩn bị VPS + DNS — theo `docs/DEPLOY.md` mục 1-4

Chưa tự đo (không có VPS thật để test) — làm theo tài liệu, báo lại DevOps
nếu có bước nào không khớp thực tế để cập nhật.

### 2. Clone + `.env` — ĐÃ ĐO

```bash
git clone https://github.com/AI20K-Build-Phase-Cohort-3/P-226.git /opt/fin05
cd /opt/fin05
cp .env.example .env
```
Điền `.env` theo đúng khối "BẮT BUỘC" trong file (POSTGRES_USER/PASSWORD/DB,
JWT_SECRET_KEY, FIELD_ENCRYPTION_KEY, OPENAI_API_KEY hoặc LLM_BASE_URL+
LLM_API_KEY) — sinh key MỚI cho production, **không copy giá trị dev**.
Nếu dùng Cloudflare Tunnel (mục 0): thêm `CLOUDFLARE_TUNNEL_TOKEN` +
`SITE_DOMAIN=app.adaptivealgo.uk`.

### 3. Dựng — ĐÃ ĐO (trên DB rỗng, đúng tình huống lần đầu)

```bash
export BUILD_COMMIT=$(git rev-parse --short HEAD)
export BUILD_AT=$(date -u +%Y-%m-%dT%H:%M:%SZ)
docker compose up -d --build
docker compose logs -f backend
```
Kỳ vọng thấy: chuỗi `alembic upgrade` chạy hết tới `a8b9c0d1e2f3 (head)`,
MỘT dòng chạy ngầm hâm nóng checkpointer (không log gì ra ngoài, chạy im),
rồi `Uvicorn running` + 4 lần `Started server process` KHÔNG kèm dòng
`UniqueViolation`/`Child process died` nào. Có nếu thấy — đó LÀ bug, báo
ngay, không phải điều đã biết.

**Xác minh bằng đo, không bằng cảm giác "log chạy qua là xong":**
```bash
docker exec fin05-backend-1 python3 -m alembic current   # phải ra "... (head)"
docker inspect fin05-backend-1 --format '{{.State.Health.Status}}'   # phải "healthy"
```

### 4. Dựng kho RAG — DỄ QUÊN NHẤT, ĐÃ XÁC NHẬN TÊN LỆNH (chưa tự chạy vì tốn tiền)

```bash
docker compose exec backend su appuser -c "python3 scripts/kho_rag.py nhan"     # đọc, miễn phí — xem trạng thái hiện có
docker compose exec backend su appuser -c "python3 scripts/kho_rag.py nap-lai"  # gọi embedding THẬT, tốn tiền
docker compose exec backend su appuser -c "python3 scripts/kho_rag.py kiem"     # xác nhận không lệch chuẩn-hoá, exit 0
```
Thiếu bước này: agent vẫn trả lời (tool `search_policy` không lỗi), nhưng
trả lời **chung chung, không trích được chính sách thật** — không có log
lỗi nào báo, tự kiểm bằng cách hỏi thử một câu chính sách cụ thể sau khi
seed xong.

### 5. Seed dữ liệu demo (tuỳ chọn — nhưng ĐỌC CẢNH BÁO Ở BƯỚC 6 TRƯỚC KHI BỎ QUA)

🔴 **[ĐO 20/08, diễn tập clone sạch] `seed_db.py` KHÔNG chạy được ngay — thiếu
dữ liệu nguồn.** `data/generated/transactions.jsonl` (60K dòng) không nằm
trong git (7 file còn lại có, riêng file này không — quá lớn để commit).
Phải sinh trước:
```bash
docker compose exec backend su appuser -c "python3 scripts/gen_dataset.py --seed 20260802 --out data/generated/ --eval-out /tmp/eval_out/"
docker compose exec backend su appuser -c "python3 scripts/seed_db.py"
docker compose exec backend su appuser -c "python3 scripts/seed_demo_scenarios.py"
```
⚠️ **`seed_demo_scenarios.py` [ĐO 20/08] dừng giữa chừng với lỗi CHECK
constraint `ck_resolutions_rejected_requires_reason_br11`** (dòng 216 set
`status="rejected"` nhưng không set `reject_reason`/`rejected_by`/
`rejected_at` — script viết trước migration BR-11, chưa cập nhật theo).
Các ca TRƯỚC dòng lỗi đã `commit()` thành công (không mất), nhưng các ca
SAU (gồm cả kịch bản dashboard "Chờ đối tác NH") **chưa chạy được trên
schema hiện tại** — bug tái lập được, đã báo Coder, KHÔNG phải lỗi riêng
của lần dựng nào. Kiểm bằng `docker compose logs backend` hoặc output lệnh
trên; nếu vẫn thấy lỗi này lúc bạn deploy, đó là bug đã biết, không phải
bạn làm sai — báo Coder, đừng tự sửa script trên VPS.

Không có route đăng ký tài khoản nào trong API (`/auth/login`,
`/auth/refresh`, `/auth/logout`, `/auth/otp/*` — không có `/auth/register`)
— **tài khoản CHỈ tồn tại qua bước seed này.** Bỏ qua là lựa chọn hợp lệ
(vd muốn DB trống hoàn toàn), nhưng có hệ quả trực tiếp ở bước 6.

### 6. Smoke test — SỬA 20/08: `curl /health` qua domain là BÁO ĐỘNG GIẢ, đừng dùng

🔴🔴 **[ĐO 20/08] `curl -f https://<domain>/health` KHÔNG kiểm được backend —
tự chứng minh bằng cách tắt hẳn backend rồi curl lại vẫn ra cùng kết quả
"thành công":**
```bash
docker stop fin05-backend-1 && curl -k -sS -o /dev/null -w "%{http_code}\n" https://localhost/health
# → 307   (KHÔNG lỗi — curl -f coi 307 là thành công)
```
Lý do: MỌI route qua Caddy — kể cả `/health` — đi vào `frontend` trước
(`Caddyfile`, chỉ `/ws/live-chat*` nối thẳng `backend`). `frontend/src/proxy.ts`
(Next.js 16 đổi tên từ `middleware.ts`) chặn TRƯỚC khi chạm route handler
nào: path không nằm trong `PUBLIC_PATHS=["/login"]` và chưa đăng nhập ⟹
redirect `307 → /login` **NGAY TẠI EDGE, KHÔNG BAO GIỜ gọi tới backend**.
Backend sống hay chết, kết quả `curl` giống hệt nhau. Trước đây tài liệu
(cả bản gốc DEPLOY.md lẫn checklist này) đều khuyên dùng lệnh này — **SAI**,
đã sửa.

**Cách kiểm THẬT — hai lớp, không lớp nào thay được lớp kia:**
```bash
# Lớp 1 — backend healthy (chạy TRÊN VPS qua SSH, không qua domain công khai
# vì backend cố ý không publish port ra ngoài — Caddyfile ghi rõ lý do):
docker compose exec backend python3 -c "import urllib.request; print(urllib.request.urlopen('http://localhost:8010/health').read())"
docker inspect fin05-backend-1 --format '{{.State.Health.Status}}'   # phải "healthy"

# Lớp 2 — đường khách THẬT hoạt động, từ ngoài, qua domain công khai:
curl -k -sS -o /dev/null -w "%{http_code}\n" https://<domain>/login   # phải 200
```
Lớp 2 chỉ xác nhận Caddy+frontend sống, KHÔNG xác nhận backend — hai lớp
BẮT BUỘC đi cùng nhau, đừng suy backend sống từ lớp 2.

🔴 **Phần đăng nhập bên dưới CHỈ làm được nếu đã chạy bước 5** (và là phép
kiểm MẠNH HƠN cả hai lớp trên — POST `/api/session` bắt buộc `frontend` gọi
`backend` thật qua `/auth/login`, không đi qua `proxy.ts` redirect như GET).
Bỏ qua bước 5 ⟹ dừng ở hai lớp phía trên — **đừng thử đăng nhập**, chưa có
tài khoản nào tồn tại. Gõ SĐT/mật khẩu đoán vào form lúc đó sẽ ra
"sai thông tin đăng nhập" — **trông y hệt một bug xác thực thật**, không có
tín hiệu nào phân biệt được với lỗi thật ngoài việc tự nhớ đã bỏ bước 5.

Đã chạy bước 5: đăng nhập thử ít nhất 1 vai (số điện thoại mẫu xem trong
`data/generated/users.jsonl` sau khi seed, hoặc dùng `0900000001` cho vai
"Đối tác ví" nếu đã chạy `seed_demo_scenarios.py` — xem `docs/DEPLOY.md`
mục 6 để biết đủ danh sách), gửi 1 câu hỏi chính sách thật để xác nhận kho
RAG bước 4 đã nạp đúng — không chỉ tin log "nạp thành công".

## Ghi chú cho lần sau

Vòng kiểm này dùng `docker-compose.override.yml` riêng trong bản clone tạm
(đổi port publish của `postgres`/`caddy` bằng cú pháp `!override`, tránh
cộng dồn danh sách port — bẫy đã gặp thật lúc làm vòng đầu) để không đụng
ba ngăn xếp thật đang chạy trên máy đội. Không sửa file tracked trong repo.
Muốn lặp lại phép kiểm này (vd trước lần deploy tiếp theo), xem lịch sử
trao đổi DevOps ↔ PO-agent 20/08 hoặc hỏi DevOps.
