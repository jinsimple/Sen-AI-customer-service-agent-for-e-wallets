# Checklist deploy P-226 lần đầu lên VPS — 2026-08-20

> Viết cho **lần deploy P-226 ĐẦU TIÊN lên site thật** (P-226 CHƯA TỪNG lên
> production — xem cảnh báo đầu `docs/DEPLOY.md`). Khác `docs/DEPLOY.md` ở
> một điểm: **mọi bước dưới đây, trừ khi ghi rõ khác, đã được LÀM THẬT** bằng
> clone sạch + `docker compose up --build` trên DB hoàn toàn rỗng, trong ngăn
> xếp cô lập, KHÔNG đụng ba ngăn xếp `fin05`/`fin05ttl`/`fin05do` đang chạy.
> Không phải chép lại tài liệu cũ rồi đoán là đúng.

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

### 5. Seed dữ liệu demo (tuỳ chọn, theo `docs/DEPLOY.md` mục 6)

```bash
docker compose exec backend su appuser -c "python3 scripts/seed_db.py"
docker compose exec backend su appuser -c "python3 scripts/seed_demo_scenarios.py"
```

### 6. Smoke test — bổ sung, ĐÃ ĐO Ở LOCAL (chưa đo qua domain thật)

```bash
curl -f https://<domain-hoặc-IP>/health || echo "LỖI — dừng, đừng báo deploy xong"
```
Đăng nhập thử ít nhất 1 vai (khách hoặc CSKH), gửi 1 câu hỏi chính sách thật
để xác nhận kho RAG bước 4 đã nạp đúng — không chỉ tin log "nạp thành công".

## Ghi chú cho lần sau

Vòng kiểm này dùng `docker-compose.override.yml` riêng trong bản clone tạm
(đổi port publish của `postgres`/`caddy` bằng cú pháp `!override`, tránh
cộng dồn danh sách port — bẫy đã gặp thật lúc làm vòng đầu) để không đụng
ba ngăn xếp thật đang chạy trên máy đội. Không sửa file tracked trong repo.
Muốn lặp lại phép kiểm này (vd trước lần deploy tiếp theo), xem lịch sử
trao đổi DevOps ↔ PO-agent 20/08 hoặc hỏi DevOps.
