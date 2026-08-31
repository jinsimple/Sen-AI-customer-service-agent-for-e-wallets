# Bàn giao Lead — xác nhận & bổ sung benchmark EU/US, 30/08/2026

> Vai: `security`. Đây KHÔNG phải một rà soát mới từ đầu — bản NỀN đã có, đầy đủ và chất lượng cao:
> `docs/security/review-2026-08-27-benchmark-eu-us.md` (27/08, chưa commit — `git status` báo `??`).
> Tài liệu này chỉ làm ba việc: (1) xác nhận lại 3 phát hiện CAO trên **HEAD hiện tại** (30/08, sau
> 24 commit kể từ 27/08), (2) bổ sung MỘT phát hiện bị bỏ sót lúc đọc lần trước, (3) đóng gói thành
> một punch-list DUY NHẤT để Lead giao việc, khỏi phải tự gộp hai tài liệu.
>
> Đọc trước: `CLAUDE.md` §2, báo cáo nền 27/08 (đủ ngữ cảnh, không lặp lại ở đây), ADR-055.

## 1. Đối chiếu lại 3 phát hiện CAO của bản nền, trên HEAD 30/08

`git log --since=2026-08-27` cho 24 commit. Trong đó có đúng 2 commit chạm vùng đang xét
(`b8cb642`, `3cc7e2e`). Kết quả đối chiếu tay từng dòng:

| # | Phát hiện (27/08) | Trạng thái 30/08 | Bằng chứng |
|---|---|---|---|
| 1 | `require_token_chua_thu_hoi` chưa gắn vào `propose_resolution`/`escalate_ticket`/`request-approval-otp` | 🟡 **CƠ CHẾ xong, PHẠM VI vẫn treo — đúng như ADR-055 dự đoán, không đổi** | `b8cb642` đúng là commit "chỉ thêm, không rút" mà ADR-055 mô tả. `grep require_token_chua_thu_hoi src/api/main.py` → 0 kết quả ở 3 route trên. Vẫn chờ PO. |
| 2 | OTP trả thẳng trong response body (`/auth/otp/request`) | 🔴 **VẪN Y NGUYÊN — CHƯA VÁ** | `main.py:443` còn `"otp_code": otp_code`. Không commit nào trong 24 commit gần nhất chạm dòng này. |
| 3 | `verify_otp` so sánh OTP bằng `==` thay vì constant-time | 🔴 **VẪN Y NGUYÊN — CHƯA VÁ** | `main.py:480` còn `otp_ok = req.otp_code == auth_session.otp_code`. Đối chứng: `approve_resolution` (`main.py:1048`) đã dùng `secrets.compare_digest` từ trước — bất nhất vẫn tồn tại y như 27/08 mô tả. |

**Kết luận:** không có hồi quy, nhưng cũng không có tiến triển trên 2/3 phát hiện CAO. 24 commit vừa
qua đều thuộc vùng landing/marketing/e2e/docs — không ai chạm `src/api/main.py` phần OTP trong 3 ngày
qua. Điều này khớp với `docs/STATE.md §0` (bàn giao 27/08, toàn đội tắt) — không phải dấu hiệu việc bị
từ chối, chỉ là chưa ai cầm.

## 2. 🔴 Phát hiện bổ sung — bản 27/08 đọc chưa hết, cùng một lỗ, RỘNG hơn đã báo cáo

Bản nền viết Phát hiện #2 chỉ trích dẫn `/auth/otp/request` (`main.py:417-448`, OTP phiên đăng nhập).
**Đọc lại route `/resolutions/{id}/request-approval-otp` (`main.py:940-978`) — route sinh OTP
dynamic-linked cho hành động DUYỆT HOÀN TIỀN, tức route được chính bản 27/08 khen là "chính xác đúng
yêu cầu Điều 5 RTS" — cũng trả `"otp_code": otp_code` thẳng trong response** (`main.py:970`), kèm
chú thích tự khai y hệt: *"Môi trường demo — mã OTP trả trực tiếp ở đây để tiện test... sản phẩm thật
sẽ gửi qua SMS/app riêng cho sếp."*

Vì sao đáng tách ra thành mục riêng thay vì gộp chung Phát hiện #2:

- Đây không phải một route phụ — đây là **route rủi ro tài chính cao nhất toàn hệ thống**
  (`supervisor` duyệt hoàn tiền). Bản 27/08 đã khen đúng thiết kế dynamic-linking (gắn `resolution_id`
  + `amount_snapshot`) là "chuẩn RTS Điều 5", nhưng **không nêu rõ** rằng chính route đó, ở runtime,
  có CÙNG lỗ hổng "sở hữu = 0" như OTP phiên đăng nhập bình thường.
- Hệ quả cho benchmark: mục PSD2/NIST AAL2/FFIEC out-of-band trong bản 27/08 đã đúng kết luận
  ("hệ thống thực tế đang ở 1 yếu tố hiệu quả") nhưng **bằng chứng trích dẫn chưa đủ mạnh** — người
  đọc báo cáo có thể hiểu nhầm chỉ luồng đăng nhập bị ảnh hưởng, còn luồng duyệt tài chính (nơi rủi ro
  thật sự nằm) thì ổn nhờ dynamic-linking. **Không đúng — cả hai luồng cùng hở, và luồng duyệt tài
  chính hở thì hậu quả tài chính trực tiếp hơn nhiều.**
- **Tin tốt duy nhất:** vì cả hai route dùng một pattern giống hệt nhau và cùng note tự khai
  "môi trường demo", bản vá sẽ là MỘT cơ chế dùng chung cho cả hai (một cờ `OTP_DEMO_MODE` mặc định
  `False`/fail-closed, chặn `otp_code` khỏi response ở cả hai route), không phải hai bản vá riêng.

**Ưu tiên: CAO — nâng cấp mức khẩn so với bản 27/08**, vì phạm vi ảnh hưởng thực ra bao trùm cả
route duyệt tài chính, không chỉ route đăng nhập.

## 3. Đã xác nhận thêm — không phải phát hiện, xác nhận GAP đã biết

- **Security headers Caddyfile:** `grep -E 'X-Frame-Options|Strict-Transport-Security|Content-Security-Policy|X-Content-Type-Options' Caddyfile` → **0 kết quả**. Đề xuất `db8d460` (27/08, DevOps) vẫn
  CHƯA merge vào `Caddyfile` thật. Khớp đúng mục ⑥ trong `docs/STATE.md §0.7` (10 việc chờ PO) —
  không phải phát hiện mới, xác nhận vẫn còn treo ở đúng chỗ.
- **GDPR route xoá/xuất dữ liệu (Điều 15/17):** rà `docs/DECISIONS.md` cho `GDPR`/`Điều 17`/`Điều 15`
  chỉ ra 3 ADR nhắc GDPR làm CĂN CỨ cho quyết định khác (Art 25/32 least-privilege, Art 5(1)(d)
  accuracy) — **không có ADR nào quyết định HOÃN route xoá/xuất dữ liệu**. Xác nhận đây đúng là GAP
  chưa có quyết định, không phải quyết định có khai mà bản 27/08 chưa tìm thấy. An toàn để đưa vào
  backlog PO như một câu hỏi cần trả lời, không phải một việc code cần làm ngay.

## 4. Punch-list hợp nhất cho Lead — đã dedup với `docs/STATE.md §0.7` (10 việc chờ PO)

**Việc CODE, có thể làm ngay (coder), không chờ PO:**
1. `src/api/main.py:480` — `otp_ok = req.otp_code == auth_session.otp_code` → `secrets.compare_digest(req.otp_code or "", auth_session.otp_code or "")`. Rẻ, 1 dòng, không đổi hành vi ngoài timing.

**Việc CODE, cần PO chốt chính sách TRƯỚC (đừng tự quyết phạm vi):**
2. Thêm cờ `OTP_DEMO_MODE` (mặc định `False`, fail-closed) chặn `otp_code` khỏi response ở **CẢ HAI**
   route: `/auth/otp/request` (`main.py:417-448`) VÀ `/resolutions/{id}/request-approval-otp`
   (`main.py:940-978`) — mục 2 ở trên. **Đây là việc CAO nhất trong toàn bộ punch-list**: chặn mọi
   tuyên bố "SCA"/"2FA"/"AAL2" trong tài liệu đối ngoại, và ảnh hưởng route duyệt tài chính, không chỉ
   đăng nhập.
3. Gắn `require_token_chua_thu_hoi` vào `propose_resolution`/`escalate_ticket`/`request-approval-otp`
   — cơ chế đã sẵn (`b8cb642`), **chỉ còn chờ PO chốt phạm vi** (ADR-055). Không đổi gì so với 27/08.

**Việc GIẤY TỜ, rẻ, PO/pháp lý làm song song không chặn code:**
4. Merge `db8d460` (header bảo mật Caddyfile) — đã có bản đề xuất, chỉ cần merge.
5. Hồ sơ DPIA/Điều 25 chính thức cho cross-border transfer — vật liệu kỹ thuật đã đủ
   (`docs/security/2026-08-17-kiem-ke-du-lieu-roi-bien-gioi-cho-ho-so-D25.md`), chỉ thiếu bước ký/phê
   duyệt.
6. IR (Incident Response) runbook chính thức — sự cố mất CSDL 27/08 (`docs/STATE.md §0.6b`) là bằng
   chứng SOC2 sẽ hỏi tới; hiện chỉ có ghi chép thủ công trong STATE.md.

**QA/QC — viết test theo QUYẾT ĐỊNH, không đọc `src/` (đúng luật phân vùng):**
7. Test xác nhận `OTP_DEMO_MODE=False` ⟹ response KHÔNG có field `otp_code`, ở CẢ HAI route (mục 2)
   — sau khi coder làm xong.
8. Test kịch bản FS-07 dương tính giả (ví thu hộ hợp pháp) — xem bản 27/08 Phát hiện #4, chưa đổi.
9. Test segregation-of-duties: supervisor A tự điều tra + đề xuất case X, supervisor B duyệt — xác
   nhận hành vi HIỆN TẠI (đang cho phép) để PO có số liệu quyết định, không phải bug report.

**Review — đối chiếu, tránh trùng việc:**
10. Đối chiếu punch-list này với `docs/STATE.md §0.7` (10 việc chờ PO) — mục ⑥/⑦ đã trùng, đã dedup ở
    trên. Xác nhận với PO thứ tự ưu tiên trước khi pitch đối tác EU/US thật.
11. Đọc nốt phần ADR chưa lướt (bản 27/08 mới đọc ADR-040→055) để xác nhận không có quyết định GDPR
    export/erasure nào bị bỏ sót — đã làm một phần ở mục 3 trên (grep từ khoá), nhưng review nên đọc
    tay các ADR liên quan xử lý dữ liệu khách để chắc chắn.

## 5. Điều PO phải quyết trước khi dùng bất kỳ cụm từ "PSD2/SCA/AAL2-compliant" nào với đối tác

Không đổi so với bản 27/08, chỉ nhấn mạnh lại vì mục 2 ở trên mở rộng phạm vi: **cho tới khi mục 2
được vá, không tài liệu đối ngoại nào (slide ZaloPay, hồ sơ pitch EU/US) được dùng các cụm từ này —
kể cả khi mô tả riêng luồng DUYỆT TÀI CHÍNH**, vì luồng đó cũng chưa có yếu tố "sở hữu" thật trong
runtime hiện tại.

## 6. Chưa kiểm được (kế thừa nguyên trạng từ bản 27/08, không đổi)

Giữ nguyên toàn bộ mục "Chưa kiểm được" của bản 27/08 — production readonly, CI chưa xanh trên nhánh
này, hiệu quả bộ lọc injection trên corpus mới, nội dung DPA thật của nhà cung cấp LLM. Không có dữ
kiện mới nào trong 24 commit vừa qua thay đổi các mục này.
