# Tiếp nhận đội mới 01/09 — DevOps: đối chiếu hạ tầng EU/US, sẵn sàng bàn giao Lead

> Vai: `devops`. Đọc `CLAUDE.md`, `docs/STATE.md §0-TER` (bàn giao 01/09, SÁU LỆNH CẤM), `docs/
> devops/2026-08-25-danh-gia-ha-tang-eu-us.md` (đánh giá gốc, 14 phát hiện + 5 điểm đạt chuẩn) và
> `docs/security/2026-09-01-tiep-nhan-doi-moi-tong-hop-benchmark-eu-us.md` (bảo mật vừa land cùng
> ngày). File này **không lặp lại phần bảo mật ứng dụng** (OTP, token revocation, PSD2/AAL2) — đã có
> báo cáo riêng, đủ tốt, tôi chỉ xác nhận lại các mục có giao cắt hạ tầng. Trọng tâm ở đây: **container/
> deploy/CI/backup/observability** — đúng lằn ranh CLAUDE.md §4 của vai `devops`.

## 0. Ranh giới đo — không suy diễn

- **[TỰ CHẠY]** = gõ lệnh thật trên máy này lúc viết file (`git`, `grep`, `docker` khi an toàn).
- **[ĐỌC MÃ]** = đọc cấu hình/repo, không chạy lại.
- Tuân thủ **SÁU LỆNH CẤM ở `docs/STATE.md §0-TER`** trong suốt phiên này: không `docker compose
  down/-v`, không rebuild bất kỳ ảnh nào, không sửa `src/`/`migrations/`, không dựng lại `caddy` của
  `fin05-qa-stripe`, không tắt `fin05-dot-otp`, không `git add .`/`checkout` thiếu pathspec. Mọi số
  liệu Docker dưới đây lấy từ `docker-compose.yml` tại `HEAD`, không từ `docker inspect` các ngăn đang
  chạy (tránh chạm vào cây quay video còn neo).

## 1. `project-knowledge/` đã cũ **417 commit** — [TỰ CHẠY]

```
git rev-list --count 961fc24..HEAD   → 417   (mốc chụp 24/08 23:51)
```

Bảo mật đã tự khai 407 hôm nay lúc viết báo cáo của họ; 10 commit trôi thêm chỉ trong vài giờ. Xác
nhận lại kết luận của họ: **đừng dùng `project-knowledge/` cho bất cứ số liệu nào sau 24/08.** Việc
chạy lại `python scripts/export_project_knowledge.py` không thuộc vùng ghi `devops` lẫn `security` —
đề xuất Lead giao `po` hoặc `tech-lead`.

## 2. Đối chiếu 14 phát hiện của báo cáo gốc 25/08 — cái nào còn mở hôm nay

### Đã vá, xác nhận lại [TỰ CHẠY / ĐỌC MÃ 01/09]

| # | Phát hiện | Trạng thái | Bằng chứng đo lại hôm nay |
|---|---|---|---|
| P0-1 | `APP_ENV` mặc định `development` mở toang `/docs` | ✅ | Không đổi so với 25/08, không hồi quy. |
| P0-2a | Redis mất persistence khi recreate | ✅ | `docker-compose.yml` service `redis` giữ `volumes:` + `appendonly yes` (không đổi từ `02892bd`). |
| P0-4 | 0/5 header bảo mật ở Caddy | ✅ **VÁ HÔM NAY** | `grep -cE "Strict-Transport-Security|X-Frame-Options|X-Content-Type-Options|Referrer-Policy|Permissions-Policy" Caddyfile` → **5**. Commit `8823ccf`. CSP **cố ý chưa thêm** — comment trong Caddyfile tự khai lý do: cần đo Report-Only trên traffic thật trước khi chốt policy, không đoán. Đúng nguyên tắc, không phải thiếu sót. |
| P0-3 (một phần) | Backup không tự động | 🟡 **NỬA VÁ** | `scripts/backup_home.ps1` **đã land** (đề xuất 27/08 → tech-lead đã đưa vào `scripts/`). Còn thiếu: (a) xác nhận đã `Register-ScheduledTask` trên máy production thật — việc tay PO, không đọc được từ repo; (b) diễn tập khôi phục **bằng chính file do script này sinh ra** — lần diễn tập trước dùng dump thủ công (`backup-truoc-25-08.sql`), chưa chứng minh được đường tự động hoạt động đầu-cuối. |
| Mục 01/09 mới | LAN expose do publish port trần | 🟡 **VÁ MỘT PHẦN** | `docker-compose.yml:292-293` base file giờ mặc định `${CADDY_BIND_HOST:-127.0.0.1}` — **mọi ngăn dựng MỚI từ nay đúng loopback theo mặc định**. Ngăn `po-demo` đang chạy (dựng từ trước bản vá) **vẫn LAN-mở tới lần rebuild kế tiếp** — không sửa được bây giờ vì đụng lệnh cấm §0-TER "không rebuild ảnh nào" trước buổi quay. |

### Vẫn mở, chưa có bằng chứng vá [TỰ CHẠY / ĐỌC MÃ 01/09 — grep trực tiếp `HEAD`]

| # | Phát hiện | Vì sao vẫn xác nhận mở |
|---|---|---|
| P0-2b | Redis không `requirepass`/ACL | `grep -n "requirepass\|REDIS_PASSWORD" docker-compose.yml .env.example` → **0 kết quả thật** (chỉ có 1 dòng comment tự trích dẫn chính câu lệnh grep này, không phải cấu hình thật). Rủi ro vẫn ở mức "chưa phải lỗ đang mở" y hệt 25/08 — service `redis` không publish `ports:` ra host — nhưng **là lỗ tiềm tàng đầu tiên bật lên nếu ai thêm `ports:` để debug**, đúng cảnh báo cũ. |
| P1-1 | Không quét CVE tầng ảnh Docker | `grep -n "trivy\|grype" .github/workflows/*.yml` → **0 kết quả**. CI vẫn chỉ có `pip-audit` + `npm audit` + `gitleaks` (đều xác nhận có mặt, tốt) — không job nào soi base image/gói OS. |
| P1-2 | Sáu (nay là bốn+) ngăn Docker chạy song song, không nguồn sự thật | Vẫn đúng hình dạng cũ, hiện đang **cố ý đóng băng** vì buổi quay video (`§0-TER`) — không phải bug mới, nhưng Lead cần biết: **không stack nào trong số đang chạy được rebuild cho tới khi có xác nhận buổi quay đã xong.** |
| P1-3 | Cơ chế phát hiện lệch mã băm lúc BUILD, mù với "ảnh cũ hơn repo" | Không đổi. Đề xuất chuyển băm sang lúc khởi động **đã bị bác có chủ đích** (25/08, không land ADR) vì biến phép so thành hằng đúng — Lead đừng để ai đề xuất lại mà không đọc quyết định cũ này trước. |
| P1-4 | `FIELD_ENCRYPTION_KEY` không xoay được | Không đổi, ≡ P2 của PO thật. |
| P1-5 | Có trace (Jaeger), không có ngưỡng cảnh báo tự động | Không đổi — vẫn không thấy Prometheus/Grafana/tương đương trong `docker-compose.yml`. Phát hiện sự cố vẫn phụ thuộc người tự đọc log — đúng mẫu hình đã gây sự cố P1-6 dưới đây (không ai canh RAM tới khi mất lượt trả tiền thật). |
| P1-6 | Không service backend nào đặt `mem_limit`/`mem_reservation` | `grep -n "mem_limit\|mem_reservation" docker-compose.yml` → **0 kết quả**. **Vẫn treo y hệt 25/08**, dù đã từng gây mất 4 lượt agent trả tiền thật do OOM-kill không kiểm soát. Đây là mục P1 rẻ nhất/rủi ro thật nhất còn tồn đọng lâu nhất trong toàn bộ danh sách — khuyến nghị Lead ưu tiên ngay sau buổi quay. |
| P2-1 → P2-5 | Runner CI dùng chung FIFO · TLS không ghim version/cipher · 72 volume mồ côi/27GB cache · không lịch lưu trữ/xoá dữ liệu · audit log không chống sửa | Không có dữ kiện mới trong 10 commit gần nhất thay đổi bất kỳ mục nào — giữ nguyên trạng 25/08. P2-4 nay có thêm bằng chứng chéo từ báo cáo bảo mật hôm nay: `contracts/authority-matrix.yaml` vẫn 0 route export/xoá dữ liệu (Điều 15/17 Luật 91/2025) — cùng một khoảng trống nhìn từ hai góc (hạ tầng lưu trữ vs. route ứng dụng). |
| P3-1 | `PHAN_LUONG_BAT` mặc định khác nhau giữa `make run` và Docker compose | Không đổi. |

## 3. Trạng thái đóng băng hiện tại — điều Lead PHẢI biết trước khi giao việc

`docs/STATE.md §0-TER` đang có hiệu lực: **PO thật vừa tắt cả bốn phiên cũ để mở đội mới**, một buổi
quay video demo dự kiến tối 01/09 **có thể chưa xong tại thời điểm Lead đọc file này**. Sáu lệnh cấm
áp dụng cho MỌI vai, không riêng `devops`:

1. Không `docker compose down`/`-v`/`--volumes`/`rm`/`prune` — đã từng xoá sạch DB `fin05` (27/08).
   Tắt ngăn chỉ `stop`. Mọi lệnh compose bắt buộc `-p <project>`.
2. Không rebuild bất kỳ ảnh nào — ngăn quay đang neo vào băm `9c17c5684c9a`.
3. Không sửa `src/`/`migrations/`.
4. Không rebuild `caddy` của ngăn `fin05-qa-stripe` — phá chuỗi gia hạn cert.
5. Không tắt ngăn `fin05-dot-otp` — không dựng lại được, cấu hình sinh ra nó không nằm trong repo.
6. Không `git add .`/`commit -a`/`clean`/`checkout` thiếu pathspec — cây làm việc dùng chung.

**Khuyến nghị điều phối cho Lead:** trước khi giao bất kỳ việc nào chạm Docker/CI/deploy cho `devops`
hoặc `tech-lead`, xác nhận trước "buổi quay đã xong chưa" — nếu chưa, mọi việc ở mục 4 dưới đây liên
quan tới rebuild phải xếp hàng sau, chỉ việc thuần viết tài liệu/script (chưa chạy) làm được ngay.

## 4. Punch-list DevOps cho Lead — đã loại bỏ việc đã xong, phân theo vùng ghi

**`devops` tự làm được ngay (vùng ghi: `docker-compose.do.yml`, `docker-entrypoint.sh`,
`.env.example`, `docs/DEPLOY.md`, `docs/devops/**`), không chạm ảnh đang chạy:**
1. Thêm `REDIS_PASSWORD` vào `.env.example` + `.env.production.example`, ghép vào
   `REDIS_URL=redis://:${REDIS_PASSWORD}@redis:6379/0` — chỉ sửa tài liệu mẫu, không phải
   `docker-compose.yml` thật (đó là vùng `tech-lead`, xem mục dưới).
2. Viết hướng dẫn `Register-ScheduledTask` chi tiết + checklist xác nhận vào `docs/DEPLOY.md` cho
   `scripts/backup_home.ps1` đã land — hiện thiếu bước "đã đăng ký thật chưa" trong tài liệu vận hành.

**`tech-lead` làm sau khi buổi quay xong (đụng `docker-compose.yml`/`Caddyfile`/`scripts/`, cần rebuild):**
3. `requirepass`/ACL cho service `redis` trong `docker-compose.yml` (ADR-035 đã có, chỉ chưa land) —
   phối hợp CÙNG LÚC với việc thêm biến ở mục 1, một lượt land, không tách hai lần (đã ghi rõ trong
   `docs/devops/2026-08-25-treo-redis-khong-mat-khau.md`).
4. `mem_limit`/`mem_reservation` cho MỌI service backend — P1 rẻ nhất, rủi ro thật nhất còn tồn đọng.
   Trước khi đặt số, đo lại phân bổ RAM thật của Docker Desktop VM (7,75 GB lúc 25/08, có thể đổi) và
   tính lại bao nhiêu ngăn có thể chạy đồng thời.
5. Job Trivy/Grype quét ảnh Docker đã build vào `ci.yml`, cạnh `pip-audit`/`npm audit`/`gitleaks` hiện
   có — cùng vị trí logic, một PR.
6. Ghim `po-demo` sang `CADDY_BIND_HOST=127.0.0.1` ở lần rebuild kế tiếp (mẫu đã có sẵn trong base
   `docker-compose.yml`, chỉ là ngăn này dựng trước khi có mẫu).

**`tester`, không đọc `src/`:**
7. Diễn tập khôi phục THẬT bằng file do `backup_home.ps1` sinh ra (không phải dump thủ công) — điều
   kiện: đã chạy tự động được vài ngày trên máy production thật.

**PO thật, việc tay không ai tự động hoá được:**
8. Xác nhận đã `Register-ScheduledTask` cho backup trên máy production.
9. Quyết định lịch lưu trữ/xoá dữ liệu (P2-4, ≡ P4 của PO) — khoá cả câu hỏi GDPR export/xoá route
   (0 route hôm nay, xác nhận chéo từ báo cáo bảo mật) lẫn câu hỏi hạ tầng (không có TTL/archive job).
10. Xác nhận buổi quay video 01/09 đã kết thúc — mở khoá cho mục 3-6 ở trên.

## 5. Bảng đối chiếu chuẩn ngành EU/US — chỉ phần hạ tầng (bổ sung bảng ứng dụng của `security`)

| Chuẩn | Khía cạnh hạ tầng | Trạng thái 01/09 |
|---|---|---|
| SOC 2 Type II | Change management / tenancy CI | 🔴 CI runner tự quản dùng chung FIFO với đội khác (P2-1) — câu hỏi cách ly đầu tiên một audit SOC2 sẽ hỏi. |
| SOC 2 / ISO 27001 | Backup & DR | 🟡 Script tự động đã land, chưa xác nhận đã đăng ký chạy thật + chưa diễn tập bằng chính file tự động (mục 2, 7 ở trên). RPO/RTO chưa định nghĩa bằng số. |
| SOC 2 / ISO 27001 | Vulnerability management | 🔴 Tầng gói phụ thuộc có (`pip-audit`/`npm audit`), tầng ảnh Docker **không** (P1-1) — nửa chuỗi. |
| SOC 2 / ISO 27001 | Monitoring & alerting | 🔴 Có trace (Jaeger), không có ngưỡng tự động (P1-5) — phát hiện sự cố phụ thuộc con người nhìn màn hình. |
| PCI-DSS-adjacent (dù không áp dụng trực tiếp) | Network segmentation | 🟡 Redis không auth (P0-2b), một số ngăn cũ LAN-expose tới khi rebuild (mục 2 ở trên) — mẫu mặc định đã sửa đúng hướng (loopback), nợ chỉ còn ở ngăn cũ. |
| Vận hành 24/7 nói chung | Resource isolation | 🔴 Không `mem_limit` — đã có sự cố thật (P1-6), không phải rủi ro lý thuyết. |
| Vận hành 24/7 nói chung | Header bảo mật biên | 🟢 **Đạt** — 5/5 header landed hôm nay, CSP hoãn có chủ đích đúng quy trình (Report-Only trước). |

## 6. Điểm đã đạt chuẩn — không đổi so với báo cáo gốc, xác nhận lại còn nguyên vẹn

Giữ nguyên 5 điểm của báo cáo 25/08 (contract-first introspect app thật, maker-checker ép ở CHECK
constraint DB, lưới lọc đầu ra tất định, vệ sinh Docker trên trung bình, văn hoá ADR/sổ Luật) — không
lặp lại nội dung, chỉ xác nhận không có dấu hiệu hồi quy trong 10 commit gần nhất.

## Liên quan

```
docs/devops/2026-08-25-danh-gia-ha-tang-eu-us.md                    ← báo cáo gốc, 14 phát hiện
docs/devops/2026-08-25-treo-redis-khong-mat-khau.md                 ← P0-2b, còn treo
docs/devops/2026-08-27-de-xuat-backup-tu-dong.md                    ← script đã land, mục 2/7/8
docs/devops/2026-08-27-de-xuat-header-bao-mat-caddy.md               ← đã land hôm nay (8823ccf)
docs/security/2026-09-01-tiep-nhan-doi-moi-tong-hop-benchmark-eu-us.md ← bản song song, góc ứng dụng
docs/STATE.md §0-TER                                                 ← sáu lệnh cấm, đọc trước mọi việc
```
