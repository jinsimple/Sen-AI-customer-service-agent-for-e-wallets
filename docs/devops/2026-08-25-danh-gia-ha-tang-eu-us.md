# Đánh giá hạ tầng FIN-05 dưới ống kính ví điện tử EU–US — 2026-08-25

> Đọc toàn bộ `project-knowledge/` (hiến pháp, 51 ADR, trạng thái 24/08) rồi đối chiếu trực
> tiếp với repo và 6 ngăn Docker đang chạy — không suy từ tài liệu tĩnh. Bản dài hơn (14
> phát hiện + 5 điểm đã đạt chuẩn, trình bày cho người đọc ngoài đội) là một artifact đã
> gửi PO thật xem trực tiếp; file này là **bản landed vào repo**, có hạng bằng chứng cho
> từng mục — đúng Luật X, đừng để phát hiện chỉ sống trong một kênh.
>
> **Ranh giới, đọc trước khi phản đối bất kỳ mục nào:** nền tảng pháp lý CHÍNH THỨC của
> FIN-05 là luật Việt Nam (NĐ 52/2024, TT 40/2024, NĐ 13/2023) — `CLAUDE.md` đã ghi, PO đã
> chốt, không mở lại ở đây. "Chuẩn EU–US" trong file này là một **thước đo trưởng thành kỹ
> thuật vận hành** (thông lệ kiểu OWASP ASVS, SOC 2 Trust Services Criteria, tư duy phục
> hồi vận hành PSD2) dùng để soi hạ tầng — KHÔNG phải đề xuất đổi cơ sở pháp lý sản phẩm.

## Hạng bằng chứng

- **[TỰ CHẠY]** — đo trực tiếp trên container/ngăn đang chạy lúc viết (`docker exec`,
  `curl`, `docker inspect`, `docker stats`), người viết file này tự gõ lệnh.
- **[ĐỌC MÃ]** — đọc mã nguồn/cấu hình trong repo, suy ra hệ quả, không chạy lại.
- **[CHƯA KIỂM]** — nêu ra vì đáng chú ý nhưng chưa có phép đo hoặc phép đo chưa dứt khoát.

---

## P0 — chặn phát hành (4)

### P0-1 · Đường deploy được tài liệu hoá tự mở toang bề mặt API — **[TỰ CHẠY]**

`.env.example:25` mặc định `APP_ENV=development`; `docs/DEPLOY.md §5` (bản trước 25/08)
dặn `cp .env.example .env` ngay trên VPS, danh sách "điền vào .env" không nhắc `APP_ENV`.

```
GET /docs           → HTTP 200, 1031 byte
GET /openapi.json   → HTTP 200, 32 route kèm đầy đủ schema
```

**Đã vá 25/08** (`cdb3161`) — thêm `APP_ENV=production` vào danh sách biến bắt buộc §5 +
dòng xác nhận `curl .../health | grep '"env":"production"'`.

### P0-2 · Sổ thu hồi refresh-token + bộ đếm chi tiêu LLM sống trong RAM Redis — **[ĐỌC MÃ]**

`src/auth.py:151` ghi bản thu hồi family bằng `setex revoked_family:*`. Trước 25/08, Redis
trong `docker-compose.yml` không có `volumes:` — mọi recreate xoá sạch sổ thu hồi, một
refresh token đã bị đánh cắp-và-thu-hồi **sống lại** tới hạn tự nhiên, không lỗi, không log.

**Đã vá 25/08** (`02892bd`, Coder) — volume `redis_data` + `appendonly yes`. Đính chính
quan trọng của Coder khi vá: mất `refresh:*` là **fail-closed, phiền chứ không phải lỗ**;
thứ đáng vá thật là `fin05:chi_tieu_llm_token:*` (trần chi tiêu LLM/ngày) — mất là **trần
quên phần đã tiêu, quên im lặng**, cổng chi phí tự mở lại sau mỗi lần khởi động lại. Cảnh
báo `docker compose down -v` đổi nghĩa đã ghi vào `docs/DEPLOY.md` (`4677369`).

**Còn treo, chưa vá:** Redis không `requirepass`/ACL — xem
[`2026-08-25-treo-redis-khong-mat-khau.md`](2026-08-25-treo-redis-khong-mat-khau.md).

### P0-3 · Không có backup tự động, không RPO/RTO, chưa từng diễn tập phục hồi — **[ĐỌC MÃ]**

`docs/DEPLOY.md` chỉ có một dòng `pg_dump` thủ công, không lịch, không script, không nơi
lưu ngoài VPS, không phép thử khôi phục.

**≡ P3 của PO thật** (*"Sao lưu chưa từng được diễn tập phục hồi"* — PO land riêng, xem sổ
quyết định của PO). Không lặp lại nội dung ở đây, chỉ đối chiếu số hiệu.

### P0-4 · Không header bảo mật nào ở tầng biên (Caddy) — **[ĐỌC MÃ]**

`Caddyfile` chỉ có `reverse_proxy`, không dòng nào set `Strict-Transport-Security`,
`Content-Security-Policy`, `X-Frame-Options`, `Referrer-Policy`. Hàng rào tối thiểu mọi
audit OWASP/PCI kiểm đầu tiên trên một mặt tiền công khai xử lý xác thực OTP. **Chưa vá.**

---

## P1 — trước khi mở rộng quy mô (6)

### P1-1 · Không quét CVE tầng ẢNH, chỉ quét tầng gói phụ thuộc — **[ĐỌC MÃ]**

CI có `pip-audit`, `npm audit`, `gitleaks` — tốt. Không job nào quét chính ảnh Docker đã
build (Trivy/Grype) — lỗ hổng trong base image hoặc gói hệ điều hành nằm ngoài phạm vi
`pip-audit`. Chưa vá.

### P1-2 · Sáu ngăn Docker cùng chạy, drift đã xác nhận, không nguồn sự thật — **[TỰ CHẠY]**

```
fin05-dot-otp    691dd9c40578   ✅ khớp cây làm việc lúc đo
fin05            6722ab874767   ❌ lệch  ← ngăn DEMO
fin05-final      6722ab874767   ❌ lệch
fin05do          26b1bd3b1ff5   ❌ lệch
fin05ttl         22ad74bdfa81   ❌ lệch
fin05-po-test    7636400be9c4   ❌ lệch + BUILD_COMMIT=khong-ro (dựng ngoài quy trình)
```

Cơ chế tự chứng thực đã hoạt động đúng — vấn đề là tần suất đọc, và không có quy ước "ngăn
nào là ngăn thật" khi sáu ngăn cùng tồn tại. Script kiểm-tươi đang được đội tự thiết kế
(trao đổi 25/08 với PO, chưa land).

### P1-3 · Cổng phát hiện lệch mã MÙ với đúng loại lệch từng gây hại nhất — **[ĐỌC MÃ, đã xác nhận qua trao đổi trực tiếp cùng ngày]**

`_khai_ma_nguon_lech_anh()` (`main.py:1624`) so `nhan_luc_dung()` (nhãn đóng vào ảnh lúc
build) với `bam_ma_nguon()` (băm `/app/src` lúc chạy). Cơ chế này bắt được *"ai sửa file
TRONG container đang chạy"* (đã từng bắt thật, 17/08, `docker cp`). Nó **không thể** bắt
được *"ảnh này build từ mã CŨ hơn repo hiện tại"* — nếu ảnh không bị tamper sau khi build,
hai vế luôn bằng nhau bất kể ảnh cũ bao lâu. Đây chính xác là hình dạng sự cố sáu ngăn ở
P1-2: cả sáu container `ma_nguon_lech_anh` đều **im lặng đúng cách**, vì mã trong mỗi ảnh
khớp với chính nhãn của ảnh đó — chỉ khớp sai với cây làm việc, thứ cơ chế này không so.

🔴 Một đề xuất "chuyển phép băm sang lúc khởi động container" đã được thảo luận cùng ngày
và **bị bác** — nó biến phép so thành `x == x` (hằng đúng), xoá cơ chế hiện có thay vì bổ
sung. Xem trao đổi PO/DevOps 25/08 (không land thành ADR, chỉ là quyết định điều phối).

### P1-4 · `FIELD_ENCRYPTION_KEY` không xoay được — **[ĐỌC MÃ]**

**≡ P2 của PO thật.** Không đối chiếu lại nội dung ở đây.

### P1-5 · Không có tầng cảnh báo ngưỡng — chỉ có trace, không có chuông — **[ĐỌC MÃ]**

Jaeger có mặt, PII scrub trước khi vào trace — đúng thứ tự `llm-observability-checklist.md`.
Không có Prometheus/Grafana/tương đương, không ngưỡng tự động báo khi lỗi 5xx tăng, độ trễ
vượt 45s, hay chi tiêu token vượt hạn mức. Phát hiện sự cố trong nhật ký dự án đều đến từ
con người tự đọc — hiệu quả với một đội nhỏ, không scale khi không ai đang nhìn màn hình.

### P1-6 · Container không đặt trần bộ nhớ, đã gây mất lượt trả tiền thật — **[TỰ CHẠY, một phần — xem ghi chú đối chiếu]**

```
docker inspect --format '{{.State.OOMKilled}} {{.HostConfig.Memory}}' <mọi backend>
  fin05-dot-otp-backend-1   OOMKilled=true   Memory=0
  fin05-po-test-backend-1   OOMKilled=true   Memory=0
  fin05do-backend-1         OOMKilled=false  Memory=0
  fin05-backend-1           OOMKilled=false  Memory=0
  fin05-final-backend-1     OOMKilled=false  Memory=0
  fin05ttl-backend-1        OOMKilled=false  Memory=0

docker info: Total Memory 7.75 GiB   ·   sysctl hw.memsize (host thật): 16.00 GB
```

Máy host 16 GB, Docker Desktop VM chỉ được cấp 7,75 GB — sáu ngăn xếp chia nhau một trần
chung, và **không container backend nào đặt `mem_limit`** (`HostConfig.Memory=0` ở cả sáu)
⟹ kernel/Docker tự chọn nạn nhân khi áp lực bộ nhớ tăng, không theo ưu tiên nghiệp vụ nào.

🔴 **Đối chiếu số liệu, không giấu:** phiên PO báo *"3/4 backend OOMKilled=true"*. [TỰ CHẠY]
đo lại độc lập ra **2/6** (`fin05-dot-otp-backend-1`, `fin05-po-test-backend-1`) — không
khớp tỉ lệ PO nêu, dù cùng chiều kết luận (một số container backend đã bị OOM-kill thật,
không phải giả thuyết). Chưa truy được PO đếm trên tập bốn ngăn nào. Snapshot bộ nhớ sống
tại thời điểm đo (`docker stats`) cho tổng ~4,2 GB trên 7,75 GB trần — dưới ngưỡng, nên áp
lực gây OOM nhiều khả năng là **đỉnh tức thời** (nhiều lượt agent/embedding chạy cùng lúc),
không phải một ngăn "ngồi không" chiếm sẵn 3,5 GB như một giả thuyết đã nêu — giả thuyết đó
**không tự xác nhận được bằng snapshot hiện tại**, để CHƯA KIỂM, không đưa vào làm kết luận.

**Khuyến nghị đứng vững bất kể con số nào đúng:** đặt `mem_limit`/`mem_reservation` cho mọi
service backend theo đo lường thật (không đoán), và tính lại số ngăn xếp có thể chạy đồng
thời trên 7,75 GB — bốn/năm ngăn cùng lúc trên một VM giới hạn là cấu hình đã chứng minh
gây mất lượt trả tiền thật, bất kể tỉ lệ chính xác là 2/6 hay 3/4.

---

## P2 — nợ kỹ thuật, không chặn ai (5)

### P2-1 · Runner CI tự quản là FIFO dùng chung với đội khác — **[ĐỌC MÃ]**

Đã tự khai trong `docs/STATE.md §5.R`. Một hệ thống xử lý PII khách hàng build/test trên hạ
tầng CI chia sẻ với đội khác là câu hỏi cách ly tenancy mà một audit SOC 2 sẽ hỏi thẳng.

### P2-2 · TLS không ghim phiên bản/cipher tối thiểu — **[ĐỌC MÃ]**

Caddy tự động xin chứng chỉ, mặc định khá an toàn, nhưng không dòng nào trong `Caddyfile`
khẳng định tường minh TLS tối thiểu — một mặc định ngầm, đúng loại rủi ro dự án đã nhiều
lần tự bắt được ở nơi khác ("khai ≠ chạy").

### P2-3 · 72 volume Docker mồ côi, 27 GB build cache — **[TỰ CHẠY]**

```
docker system df:  111 volume (72 không gắn container nào) · 612 lớp build cache, 27,07 GB
```

Không phải sự cố, nhưng volume mồ côi là đúng nơi một bản sao PII cũ có thể nằm quên — kiểm
kê backfill PII (`§5.E` trong `project-knowledge`) chỉ xử lý ba ngăn đang sống, chưa liệt kê
nhóm này.

### P2-4 · Không có lịch lưu trữ, không có cơ chế xoá dữ liệu — **[ĐỌC MÃ]**

**≡ P4 của PO thật** (*"Không có lịch lưu trữ, không có cơ chế xoá"*). Không đối chiếu lại
nội dung ở đây.

### P2-5 · Chuỗi audit không có bằng chứng chống sửa — **[ĐỌC MÃ]**

**≡ P1 của PO thật** (*"US-017 hứa log không sửa/xoá được — hứa ở tầng ứng dụng, không có
trigger/append-only/hash-chain thật"*). Không đối chiếu lại nội dung ở đây.

---

## P3 — cạnh, đáng ghi nhưng hẹp phạm vi (1)

### P3-1 · `PHAN_LUONG_BAT` mặc định khác hai cờ cùng họ — **[ĐỌC MÃ, xác nhận từng dòng]**

```
config.py:86   PHAN_LUONG_BAT       = os.environ.get("PHAN_LUONG_BAT", "").…      → mặc định TẮT
config.py:103  CONG_T0_BAT          = os.environ.get("CONG_T0_BAT", "1").…        → mặc định BẬT
config.py:119  CONG_OTP_NHOM_B_BAT  = os.environ.get("CONG_OTP_NHOM_B_BAT", "1").…→ mặc định BẬT
```

`docker-compose.yml:120` ghi đè `PHAN_LUONG_BAT: ${PHAN_LUONG_BAT:-1}` — mọi ngăn dựng qua
compose đều nhận mặc định BẬT, đúng ý PO đã chốt 17/08. **Nhưng đây là MỘT CHỖ DUY NHẤT giữ
mặc định đó**: `Makefile:4` (`make run`) gọi thẳng `uvicorn`, không qua khối
`environment:` này — chạy `make run` ngoài Docker, `PHAN_LUONG_BAT` về mặc định TẮT trong
mã, trong khi hai cờ cùng họ vẫn BẬT. Phạm vi hẹp (chỉ đường chạy ngoài compose), nhưng là
đúng hình dạng "một chỗ là đủ cho cả ba ngăn xếp" mà chính comment tại `docker-compose.yml`
đã tự cảnh báo cho một biến khác — rủi ro có thật nếu có thêm một đường chạy mới (compose
file khác, script CI) quên chép dòng override.

---

## Đã đạt chuẩn — công bằng thì phải nói (5)

Một báo cáo chỉ liệt kê lỗ hổng là một báo cáo lệch. Năm điều dưới đây, phần lớn dự án ví
điện tử quy mô pilot không có.

1. **Contract-first có introspect app đang chạy** — `tests/test_invariants.py` đọc thẳng
   `app.routes`, moi role từ closure của guard, đọc `CheckConstraint` qua AST.
2. **Maker-checker ép ở tầng database** — `CheckConstraint` chặn người đề xuất tự duyệt
   hoàn tiền, đúng tinh thần phân tách nhiệm vụ PSD2/SOX đòi hỏi.
3. **Lưới lọc đầu ra tất định, độc lập với model** — O1–O4 chạy bằng regex, đổi model xoay
   vòng không làm yếu lưới cuối.
4. **Vệ sinh Docker trên trung bình** — multi-stage build, non-root user, healthcheck không
   giả định có `curl`, nhãn tự tố cáo khi thiếu build-arg, chỉ Caddy publish port ra ngoài.
5. **Văn hoá ADR + sổ "Luật"** — 51 ADR có ghi lý do bác phương án khác, sổ đăng ký "Luật"
   rút từ chính sai lầm của đội (kể cả lỗi người điều phối, có ghi tên) — văn hoá
   blameless-postmortem hiếm thấy ở quy mô một người + nhiều phiên AI.

---

## Đối chiếu số hiệu với PO thật

| Mục file này | Quan hệ | Mục PO thật |
|---|---|---|
| P0-3 | ≡ | P3 — sao lưu chưa diễn tập phục hồi |
| P1-4 | ≡ | P2 — `FIELD_ENCRYPTION_KEY` không xoay được |
| P2-4 | ≡ | P4 — không lịch lưu trữ/xoá dữ liệu |
| P2-5 | ≡ | P1 — audit log không chống sửa |

Bốn mục PO thật land ở kênh riêng của PO (chưa xác định đường dẫn lúc viết file này) —
không lặp nội dung, chỉ trỏ số hiệu để tránh hai bên mang hai ID cho cùng một phát hiện.

---

## Đề xuất thứ tự

| Khi nào | Việc | Vì sao trước |
|---|---|---|
| Đã xong | `APP_ENV=production` + xác nhận | P0, rủi ro thấp, hệ quả nặng |
| Đã xong | Volume + `appendonly` cho Redis | P0, chặn phát hành |
| Tuần này | `requirepass`/ACL cho Redis | Còn treo, xem mục P0-2 |
| Tuần này | Header bảo mật vào Caddyfile | P0, một tệp, rủi ro thấp |
| Tuần này | `mem_limit` cho mọi service backend | P1, đã gây mất lượt trả tiền thật |
| Trước khi nhận traffic thật đầu tiên | Backup tự động + một lần diễn tập khôi phục có số | ≡ P3 của PO, không thể lùi |
| Trước khi mở rộng > pilot | Quét CVE tầng ảnh (Trivy) + alerting ngưỡng cơ bản | P1, không chặn demo, chặn vận hành 24/7 |
| Khi rảnh, không khẩn | Script mã hoá lại + kế hoạch xoay `FIELD_ENCRYPTION_KEY` | ≡ P2 của PO, nợ đã tự khai từ trước |

---

## Liên quan

```
docs/DEPLOY.md                                        ← 2 bản vá P0 đã land (cdb3161, 4677369)
docs/devops/2026-08-25-treo-redis-khong-mat-khau.md   ← mục treo P0-2 phần còn lại
project-knowledge/06-TRANG-THAI-HIEN-TAI.md           ← bản chụp 24/08, nguồn phần lớn P1/P2
```
