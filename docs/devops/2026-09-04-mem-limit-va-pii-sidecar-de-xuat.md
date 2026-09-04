# Đề xuất — `mem_limit` mọi service + sidecar PII/NER — 04/09

> Việc backlog từ `docs/STATE.md §0-QUINQUIES` (mục 1-3), giao `devops`. Thuần thiết kế/tài liệu,
> KHÔNG đụng ngăn `po-demo` đang sống. Mọi số RAM dưới đây [TỰ CHẠY] lúc viết file (`docker stats
> --no-stream`, `docker top`), không suy đoán — trừ mục đánh dấu [ƯỚC TÍNH].

## 0. Sửa một tiền đề trong §0-QUINQUIES trước khi Coder mất công thử

Mục 1 của backlog ghi *"Thử trước, rẻ nhất: cờ `--preload` của uvicorn"* — **đã tự kiểm lại hôm nay,
xác nhận lần nữa: `python3 -m uvicorn --help` trong chính container `po-demo` KHÔNG có cờ này.**
`--preload` là khái niệm của **Gunicorn** (`gunicorn --preload -k uvicorn.workers.UvicornWorker`),
không phải uvicorn CLI trần đang dùng ở `docker-entrypoint.sh:32`. Hai đường thật sự khả thi:

- **Đường A — đổi process manager sang Gunicorn+UvicornWorker, dùng `--preload`.** Ăn ngay hiệu ứng
  copy-on-write (tải model 1 lần ở master, fork share bộ nhớ) mà không cần tách sidecar. Đánh đổi:
  thêm dependency (`gunicorn`), đổi hẳn `CMD` trong `docker-entrypoint.sh`, cần kiểm lại toàn bộ hành
  vi graceful-shutdown/healthcheck có đổi không (gunicorn quản worker khác uvicorn quản worker) —
  **rủi ro hồi quy KHÔNG nhỏ cho một thay đổi hạ tầng lõi**, không phải việc làm vội trước quay.
- **Đường B — sidecar PII/NER, đúng khuôn `rerank_service/` đã có tiền lệ CHẠY THẬT.** Chi tiết mục 2.

Đề xuất: **Đường B trước** (rủi ro thấp hơn, có mẫu đã chứng minh chạy được đêm nay), Đường A để dành
nếu sau này cần thêm — không làm cả hai cùng lúc.

## 1. `mem_limit` — giá trị cụ thể từng service, kèm căn cứ

**Số nền [TỰ CHẠY, `docker stats --no-stream`, 04/09 ~07:50 UTC — po-demo đang phục vụ traffic QA E2E
thật, KHÔNG phải máy rảnh]:**

| Service (po-demo) | RSS hiện tại | Đỉnh đã đo được (lịch sử) | `mem_limit` đề xuất | `mem_reservation` |
|---|---|---|---|---|
| `backend` (2 worker) | 1,87GiB | **3,54GiB** (4 worker, trước hạ xuống 2) · lý thuyết đỉnh 2 worker nếu CẢ HAI cùng lúc chạm PII lần đầu: 2×2,3GB+~400MB nền ≈ **5GB** | **4GiB** | 2GiB |
| `rerank` | 1,19GiB | ổn định (model cố định, không nhân theo worker — sidecar 1 tiến trình) | **1,5GiB** | 1GiB |
| `frontend` | 66MiB | — | **512MiB** | 128MiB |
| `caddy` | 39MiB | — | **256MiB** | 64MiB |
| `postgres` | 91MiB | tăng theo dữ liệu, chưa đo đỉnh thật | **1GiB** | 256MiB |
| `redis` | 4,5MiB | AOF nhỏ, không lưu blob lớn | **256MiB** | 64MiB |
| `jaeger` | 228MiB | **all-in-one giữ trace TRONG RAM**, KHÔNG có TTL/rotation cấu hình — có thể tăng KHÔNG GIỚI HẠN theo thời gian chạy (xem cảnh báo mục 1b) | **1GiB** | 256MiB |
| **Tổng trần (nếu mọi service cùng chạm đỉnh)** | | | **~8,5GiB** | |

🔴 **Tổng trần 8,5GiB VƯỢT NGAY VM 7,75GiB** — đây KHÔNG phải lỗi tính toán, là đúng bản chất của
`mem_limit`: nó là **TRẦN CỨNG PHÒNG THỦ cho từng container** (chặn MỘT container ăn hết máy, kéo chết
container khác — đúng mục tiêu P1-6), **không phải ngân sách được cấp phát chắc chắn**. Docker không
đòi hỏi tổng `mem_limit` ≤ RAM vật lý; overcommit là bình thường MIỄN LÀ không phải mọi container cùng
chạm trần CÙNG LÚC. Với `backend` (2 worker cold-load đồng thời) là nơi DUY NHẤT từng thật sự chạm gần
trần trong lịch sử đo — các service còn lại có biên độ rộng so với mức dùng thật.

**Nếu muốn siết chặt hơn (khuyến nghị SAU khi có sidecar PII ở mục 2, không phải bây giờ):** `backend`
mem_limit có thể hạ về **2,5GiB** một khi PII không còn tải trong tiến trình backend (chỉ còn base
uvicorn + buffer request, không còn +2,3GB/worker) — lúc đó tổng trần cả stack po-demo mới thực sự nằm
dưới VM mà không cần overcommit.

**1b — Cảnh báo phụ, đáng ghi riêng: Jaeger all-in-one không có cơ chế xoá trace cũ.** 228MiB sau vài
giờ chạy — chưa đủ dữ kiện để nói tốc độ tăng, nhưng KHÔNG thấy cấu hình `SPAN_STORAGE_TYPE`/TTL/
`--memory.max-traces` trong `docker-compose.yml` (mặc định memory storage của jaeger CÓ trần
`--memory.max-traces=100000` theo tài liệu upstream, nhưng ta chưa GHIM tường minh — đang ăn may theo
default). Đề xuất kèm `mem_limit` phòng thủ ở trên; xem xét ghim `--memory.max-traces` tường minh nếu
đợt 150 người tạo nhiều trace hơn pilot hiện tại — KHÔNG làm đêm nay, chỉ ghi để không quên.

## 2. Sidecar PII/NER — kiến trúc, đúng khuôn `rerank_service/`

**Vì sao đúng bài toán y hệt rerank (ADR-061 tự khai lý do, áp lại nguyên văn cho PII):** backend chạy
N tiến trình uvicorn worker ĐỘC LẬP (multiprocessing, không `--preload`) — mọi thứ tải TRONG tiến trình
backend bị nhân theo N. `src/observability/pii.py` hiện tải **HAI** `AnalyzerEngine` riêng
(`_load_analyzer_model_input` · `_load_analyzer_log`, cả hai `@lru_cache(maxsize=1)` — cache CHỈ trong
PHẠM VI MỘT TIẾN TRÌNH, không chia sẻ giữa worker) — đây CHÍNH XÁC là nguồn +2,3GB/worker đã đo.

### Interface đề xuất — `POST /scrub`

```python
# rag_pii_service/app.py — cùng khuôn rerank_service/app.py

MODEL_NAME = os.environ.get("PII_NER_MODEL", "xx_ent_wiki_sm")
app = FastAPI(title="fin05-pii-sidecar")

_analyzer_model_input = None   # lru_cache thay bằng biến module — CHỈ 1 tiến trình chạy sidecar
_analyzer_log = None           # (không multi-worker cho service này — không cần, tải 1 lần là đủ mục đích)

class ScrubRequest(BaseModel):
    text: str | None
    muc_dich: str   # "model_input" | "log" — khớp MucDichScrub hiện có trong pii.py

class ScrubResponse(BaseModel):
    text: str | None

@app.get("/health")
def health() -> dict:
    return {"status": "ok", "model": MODEL_NAME}   # liveness thuần, không đợi model tải xong

@app.post("/scrub", response_model=ScrubResponse)
def scrub(req: ScrubRequest) -> ScrubResponse:
    # Chuyển NGUYÊN VẸN thân hàm scrub_pii() hiện có (scrub_regex + phần Presidio/
    # AnalyzerEngine + _VietnameseNameRecognizer) từ src/observability/pii.py sang đây —
    # KHÔNG viết lại logic, chỉ đổi CHỖ CHẠY.
    ...
```

### Phía backend — đổi `scrub_pii()` thành HTTP client mỏng

```python
# src/observability/pii.py — SAU khi tách, hàm này chỉ còn gọi HTTP, không tải model nữa
PII_SIDECAR_URL = os.environ.get("PII_SIDECAR_URL")  # http://pii-sidecar:8021

def scrub_pii(text: str | None, *, muc_dich: MucDichScrub) -> str | None:
    if not PII_SIDECAR_URL:
        raise RuntimeError("PII_SIDECAR_URL chưa đặt — không có đường fallback tự tải model tại "
                            "backend, đúng chủ đích (một nguồn tải model DUY NHẤT).")
    r = httpx.post(f"{PII_SIDECAR_URL}/scrub", json={"text": text, "muc_dich": muc_dich}, timeout=10)
    r.raise_for_status()
    return r.json()["text"]
```

⚠️ **Điểm khác rerank cần lưu ý — PII scrub nằm trên đường NÓNG hơn rerank nhiều** (mọi input/output
qua LLM đều scrub, không chỉ RAG). Thêm 1 HTTP round-trip nội bộ (~1-5ms cùng docker network) cho MỖI
lượt scrub — cần đo latency thật trước/sau khi land, không giả định "rẻ vì nội bộ". Nếu tần suất gọi
quá cao làm chậm rõ rệt, cân nhắc batch nhiều đoạn text trong 1 request thay vì gọi lẻ từng đoạn.

### `docker-compose.yml` — thêm service (mẫu, phỏng `rerank`)

```yaml
pii-sidecar:
  build:
    context: ./rag_pii_service
    dockerfile: Dockerfile
  restart: unless-stopped
  mem_limit: 3g          # ~2,3GB model + buffer — ĐO LẠI THẬT sau khi build, đừng tin số suy từ backend
  healthcheck:
    test: ["CMD", "python", "-c", "import urllib.request; urllib.request.urlopen('http://localhost:8021/health')"]
    interval: 30s
    timeout: 10s
    start_period: 60s
    retries: 3
  # KHÔNG publish port ra host — đúng nguyên tắc rerank, chỉ mạng nội bộ compose.
```

### Kết quả kỳ vọng sau khi land (chưa đo, [ƯỚC TÍNH] — phải đo lại thật, không tin số này)

```
TRƯỚC:  backend (N worker) = N × (base + 2,3GB PII)         → nhân theo worker
SAU:    backend (N worker) = N × base  +  1 × pii-sidecar (~2,3GB cố định)  → KHÔNG nhân theo worker
```
Với `backend` 2 worker: từ ước ~5GB đỉnh lý thuyết (mục 1) xuống còn **~2,7GB** (2×~200MB base +
2,3GB sidecar, sidecar tách container riêng nên còn tính vào tổng chung nhưng KHÔNG BAO GIỜ nhân đôi).
Đây là fix TẬN GỐC, không phải giảm concurrency đổi lấy an toàn như band-aid 4→2 đêm nay.

## 3. Thứ tự đề xuất cho Coder (không làm đêm nay — sau buổi quay)

1. Land `mem_limit`/`mem_reservation` mục 1 cho **cả hai** ngăn `po-demo` và `dot-otp` (và bất kỳ ngăn
   nào dựng lại sau này) — rẻ nhất, không đổi code, chặn ngay kịch bản một ngăn OOM-kill ngăn khác.
2. Tách `rag_pii_service/` (Đường B, mục 2) — dựng + đo RAM/latency thật trên một ngăn thử nghiệm
   TRƯỚC khi áp cho `po-demo`, đúng quy trình đã dùng cho `rerank`.
3. Sau khi (2) ổn định, đo lại RAM `backend` thật, cân nhắc siết `mem_limit` xuống 2,5GiB (mục 1, ghi
   sẵn) và tăng `UVICORN_WORKERS` trở lại nếu concurrency cần hơn 2 (band-aid 4→2 đêm nay không còn
   cần thiết một khi PII không nhân theo worker nữa).

## Liên quan

```
docs/devops/2026-09-01-tiep-nhan-danh-gia-ha-tang-eu-us.md   ← P1-6 gốc, đề xuất từ 01/09
docs/STATE.md §0-QUINQUIES                                    ← sự cố thật 04/09, số đo gốc
rerank_service/                                                ← khuôn mẫu đã chạy thật (ADR-061)
src/observability/pii.py                                       ← nơi cần tách (scrub_pii, AnalyzerEngine ×2)
```
