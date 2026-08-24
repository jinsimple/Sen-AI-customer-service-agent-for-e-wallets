# Bàn giao cho `security` — 7 phát hiện độc lập từ Review Code (N1–N7)

> **Nguồn:** Review Code (`p-226-cb`), gửi Lead qua SendMessage 24/08, đối chiếu PSD2/GDPR/EU AI
> Act/OWASP ASVS/SOC2. **Lý do đặt ở đây, không phải `docs/security/`:** vùng ghi `docs/security/`
> thuộc `security` (CLAUDE.md §4); Review không ghi repo; Lead trong đợt này chỉ được cấp
> `docs/giao-viec/` + `docs/STATE.md` (phiếu `2026-08-24-dot-otp-truoc-token.md`). Đặt tại đây để
> **Luật X** thoả (đo mà chưa vào file thì phiên sau tìm lại từ đầu) mà không vượt vùng ghi của ai.
> `security` land chính thức vào `docs/security/` khi rảnh tay — không phải việc của đợt "OTP
> trước token" (13 hạng mục ①–⑬ không có mục này), nên **không chặn đợt đang chạy**.

**Đã đối chiếu với 4 finding PO đã ghi trước đó** (FIELD_ENCRYPTION_KEY không xoay được · audit
log không tamper-evident · backup/DR chưa diễn tập phục hồi · lịch lưu trữ/xoá dữ liệu) — kết quả:
**N3 rút** (trùng hoàn toàn PO), **N2 gộp một phần** (N2a giữ riêng, N2b nhập vào finding audit-log
của PO). Còn lại **7 mục distinct nên land**: N1, N2a, N4, N5, N6, N7 + 2 mục PO đã có (backup/DR,
retention) — Review verify độc lập cả hai, xác nhận đúng.

---

## N1 [Trung bình] — Security headers

Không có HSTS/CSP/X-Content-Type-Options/X-Frame-Options/Referrer-Policy ở tầng Caddy lẫn FastAPI.
`CORSMiddleware` cố ý không có (đã giải thích tốt ở `main.py:180-188`) — nhưng đó là chuyện khác
với security response headers.

**Dựng lại:** `grep -n "CORSMiddleware\|Secure\|X-Frame\|Content-Security\|Strict-Transport" src/api/main.py`
→ 0 hit ngoài dòng giải thích CORS. `Caddyfile` không có khối `header`.
**Chuẩn:** OWASP ASVS v5 §14.

## N2a [Trung bình] — Audit trail tầng HTTP không tamper-evident

`logs/access.log` là file phẳng trên đĩa host/volume — không hash-chain, không WORM, không xuất
sang hệ thống tách quyền ghi.

**Dựng lại:** `src/api/main.py:191-254` (`audit_log_middleware` ghi qua `logging.FileHandler`
thường).
**Chuẩn:** SOC2 CC7.

*(N2b — tầng nghiệp vụ `InvestigationLog`/`Resolution` không có trigger chặn UPDATE/DELETE hay
hash-chain — **gộp vào finding audit-log của PO**, không land riêng.)*

## N4 [Thấp-Trung bình] — Thiếu runbook incident response

Có threat-model tốt (`docs/security/threat-model-*.md`) nhưng không có runbook dạng "xảy ra X →
ai làm gì trong bao lâu", đặc biệt để khớp GDPR Art. 33 (72h báo vi phạm) / PDPA VN tương đương.

**Dựng lại:** `find docs -iname "*incident*" -o -iname "*runbook*" -o -iname "*breach*"` → rỗng.

## N5 [Thấp-Trung bình] — Không có vendor/subprocessor risk register

Không có sổ đăng ký nhà thầu phụ (OpenAI, Alibaba DashScope Singapore, Cloudflare) dạng bảng tập
trung; thông tin rải trong nhiều file sự cố `docs/security/2026-08-17-*`.

**Chuẩn:** GDPR Art. 28, NĐ 13/2023.

## N6 [Thấp, không khẩn] — JWT thuật toán đối xứng

HS256 hợp lý ở quy mô 1 backend hiện tại; cân nhắc RS256/ES256 khi tách dịch vụ. Ghi lại để không
quên, **không phải việc cần làm bây giờ** — ưu tiên thấp nhất trong 7 mục.

## N7 [Thấp] — Fail-open chưa có alert chủ động

`RedisConcurrencyLimiter`/`RedisSlidingWindowLimiter` fail-open có trần khi Redis chết (thiết kế
đúng, đã lập luận kỹ trong code) nhưng chỉ `_logger.warning` — chưa xác nhận có hook alert
(pager/dashboard) để vận hành biết ngay thay vì đọc log sau.

**Dựng lại:** `src/rate_limit.py:79-89` — chỉ thấy `_logger.warning`, không thấy hook alert.

---

## Hai mục PO đã nêu, Review verify độc lập, xác nhận đúng — giữ số hiệu của PO

- **Backup/DR chưa từng diễn tập phục hồi** — `docs/DEPLOY.md:192` chỉ có một dòng `pg_dump` thủ
  công, không cron, không test restore.
- **Lịch lưu trữ/đường xoá dữ liệu** — không có trong N1–N7 của Review, giữ nguyên số hiệu PO.

---

## Việc của `security` khi nhận bàn giao này

1. Đọc, xác nhận hoặc bác từng mục (đây là báo cáo Review, chưa phải finding đã được `security`
   thẩm định).
2. Land chính thức vào `docs/security/` theo đúng vùng ghi của mình, gắn mức ưu tiên.
3. Nếu mục nào cần đổi `contracts/` hoặc chặn merge — đi đủ quy trình CLAUDE.md §3, không tự chèn.
