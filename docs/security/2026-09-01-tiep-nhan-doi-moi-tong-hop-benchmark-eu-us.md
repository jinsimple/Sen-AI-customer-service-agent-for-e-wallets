# Tiếp nhận đội mới 01/09 — Tổng hợp hiện trạng bảo mật + benchmark EU/US, sẵn sàng bàn giao Lead

> Vai: `security`. PO thật vừa mở lại đội (5 phiên khác khởi động cùng lúc — `p-226-56/77/92/29/0c`
> quan sát qua `ListAgents`, chưa xác định ai là Lead). Đây KHÔNG phải một rà soát bốn-bước từ đầu —
> bản nền đã rất đầy đủ (`docs/security/review-2026-08-27-benchmark-eu-us.md`,
> `2026-08-30-ban-giao-lead-xac-nhan-benchmark-eu-us.md`). Việc của phiên này: (1) đối chiếu kho
> kiến thức `project-knowledge/` với HEAD thật — **đã LỆCH, nói ra ngay theo đúng luật của chính
> kho đó**, (2) đo lại trên `HEAD` hôm nay xem 3 phát hiện CAO cũ còn mở hay đã vá, (3) gộp thêm 2
> phát hiện vận hành mới nhất (01/09) vào một bức tranh DUY NHẤT, (4) đóng gói punch-list KHÔNG
> LẶP LẠI việc đã xong, sẵn sàng cho Lead phân vai coder/QA-QC/review.

## 0. 🔴 Kho kiến thức Project (`project-knowledge/`) đã CŨ 407 commit — nói ra theo đúng luật của nó

`project-knowledge/00-SYNC-VERSION.md` tự khai chụp tại `961fc24` (24/08 23:51). `git rev-list
--count 961fc24..HEAD` = **407**. Riêng `contracts/agent-tools.yaml`, `CLAUDE.md`, `docs/DECISIONS.md`
(+415 dòng), `docs/STATE.md` (+1400 dòng) đã đổi kể từ mốc đó. Theo đúng quy tắc chính kho này in ra:
*"Lệch nhau ⟹ kho kiến thức đã cũ"* — nếu Lead hoặc bất kỳ ai dùng Claude Desktop Project để làm
việc, **đừng tin số liệu/ADR trong `project-knowledge/` cho bất cứ thứ gì sau 24/08**. Cần chạy lại
`python scripts/export_project_knowledge.py` và up lại. Không thuộc vùng ghi của tôi, nêu ra để Lead
giao đúng người (có thể là `po` hoặc `devops`).

Phần còn lại của báo cáo này đọc trực tiếp `HEAD` = `b60c6a5` (01/09), không dựa vào bản export cũ.

## 1. Dự án là gì — một câu

AI Agent hỗ trợ CSKH ví điện tử xử lý khiếu nại giao dịch: agent **điều tra** bằng 5 tool thật, đề
xuất hướng xử lý **có căn cứ truy vết**, nhưng **không bao giờ tự quyết** — mọi hành động chạm tiền
qua `supervisor` duyệt, ép ở cả tầng route lẫn tầng `CHECK constraint` DB. 5 ràng buộc cứng
(`CLAUDE.md §2`) đã mã hoá thành 23 test introspect app đang chạy — đây vẫn là điểm mạnh cấu trúc lớn
nhất của dự án, tôi xác nhận lại cơ chế này còn nguyên vẹn trên `HEAD` hôm nay (`grep -c "def test_"
tests/test_invariants.py` không đổi so với báo cáo 27/08).

## 2. 🟢 Tin tốt trước — 3 phát hiện CAO/TRUNG BÌNH của báo cáo 27/08 đã VÁ, đo lại tận nơi trên HEAD

| # | Phát hiện (27/08) | Trạng thái hôm nay 01/09 | Bằng chứng [ĐO 01/09] |
|---|---|---|---|
| 1 | `require_token_chua_thu_hoi` chưa gắn vào `propose_resolution`/`escalate_ticket`/`request-approval-otp` | ✅ **ĐÃ VÁ** (`5ff93b8`, xem gate đỏ-trước/xanh-sau 31/08) | `grep -n require_token_chua_thu_hoi src/api/main.py` → có mặt ở dòng 632, 645, 969 — đúng 3 route đã nêu. Bằng chứng tái tạo được: RED 3 FAILED (token thu hồi vẫn 200 OK) → GREEN 3 passed. |
| 2 | OTP trả thẳng trong response body, cả 2 route (`/auth/otp/request` + `/resolutions/{id}/request-approval-otp`) | ✅ **ĐÃ VÁ** (`bdaf17e`) — cờ `OTP_DEMO_MODE` mặc định `False`, **fail-fast nếu bật cùng `APP_ENV=production`** | `src/config.py:198-203`: `OTP_DEMO_MODE=...False mặc định`, `if OTP_DEMO_MODE and APP_ENV=="production": raise` — đây là dạng vá ĐÚNG khuyến nghị 27/08 (fail-closed, không phải fail-open). `src/api/main.py:451`/`:998` bọc `otp_code` trong `if OTP_DEMO_MODE`. |
| 3 | `verify_otp` so sánh `==` thay vì constant-time | ✅ **ĐÃ VÁ** | `src/api/main.py:492` VÀ `:1077` đều `secrets.compare_digest(...)` — cả hai route OTP giờ nhất quán, không còn bất nhất với `approve_resolution`. |

**Đây KHÔNG phải tự tôi vá được kiểm ngay — đã có gate đỏ-trước/xanh-sau độc lập** (`docs/security/
2026-08-31-cong-do-truoc-xanh-sau-bdaf17e-5ff93b8.md`, worktree cô lập, đối chiếu độc lập với Coder,
kết quả khớp từng chữ). Tôi chỉ xác nhận lại code hiện có trên `HEAD` hôm nay còn đúng như gate đã đo
2 ngày trước — không có hồi quy.

**🟡 Một gap còn treo, không phải bug:** hành vi của `require_token_chua_thu_hoi` (mục 1) **chưa có
test chính thức trong `tests/`** — bằng chứng 31/08 là script audit tạm của `security`, không commit
được (ngoài vùng ghi). Đây là backlog thật cho `tester`.

## 3. Rủi ro VẬN HÀNH đang sống — không phải lỗi code, là cấu hình/hiện vật, đo tối nay

Hai phát hiện mới nhất (01/09), tôi xác nhận lại trạng thái tại thời điểm viết báo cáo này:

**① LAN expose 3/4 ngăn Caddy** (`docs/security/2026-09-01-lan-expose-caddy-va-khoa-qwen-bo-quen.md`)
— gốc: `docker-compose.yml:277-279` publish `"80:80"/"443:443"` không ghim IP ⟹ Docker mặc định
`0.0.0.0`. Cặp nguy hiểm nhất (`ctc1-check`: LAN mở + `OTP_DEMO_MODE=true` cộng dồn) **đã vá bằng
commit `dbdbc6e`** (ghim `${CADDY_BIND_HOST:-127.0.0.1}`), có hiệu lực từ lần dựng lại sau. `po-demo`
vẫn LAN-mở tới lần dựng lại tiếp theo (chưa rebuild, đúng lệnh cấm §0-TER "không dựng lại bất kỳ
ảnh nào" trước buổi quay). **Không phải phát hiện mới của tôi — xác nhận lại nguyên trạng đã ghi.**

**② `QWEN_API_KEY` sống thừa trong `.env`** — app không đọc key này ở đâu (`grep -rn QWEN_API_KEY
src/ scripts/ eval/` → 0), chưa từng vào git, nhưng vẫn nạp vào mọi container đang chạy. Không đổi
lấy lợi ích gì, chỉ nhân đôi bề mặt nếu `.env`/container bị đọc trộm. Việc tay PO: thu hồi key trong
console DashScope.

**③ Mã OTP đã render nằm VĨNH VIỄN trong git** (`docs/security/2026-09-01-ma-otp-da-render-trong-
git-quet-eval-e2e.md`) — 4 hiện vật đã commit (`db7a488`, `1a6eff1`) chứa OTP thật đã render (ảnh +
JSON), sinh từ `frontend/e2e/kich-ban-chuyen-gia-render-that.spec.ts` chạy **mặc định** (không có
guard `OTP_DEMO_MODE`/seed-account nào bọc quanh), và chạy lại **mỗi đêm qua CI** (`e2e-playwright-
nightly`). Mức hiện tại THẤP (seed data, số đã hết hạn) nhưng đây là **lỗ CẤU TRÚC sẽ tái diễn** —
lần chạy tiếp theo tạo OTP mới, và nếu ai đó chạy đúng spec này nhắm vào dữ liệu THẬT trong tương
lai, không có gì trong code chặn lại. Vá đúng: đổi đường ghi ra ngoài repo (không phải chỉ
`.gitignore` — 4 file đã tracked, cần `git rm --cached` trước). **Cố ý CHƯA vá** — đụng đúng 4 file
tranh chấp trước buổi quay demo tối 01/09, xếp sau buổi quay.

## 4. Benchmark chuẩn ngành EU/US — CẬP NHẬT so với bản 27/08 (không lặp lại phần không đổi)

| Chuẩn | 27/08 | **01/09 (sau vá)** |
|---|---|---|
| **PSD2 + RTS on SCA (EU)** | Đáp ứng MỘT PHẦN — thiết kế đúng, runtime demo lộ OTP xoá mất yếu tố "sở hữu" | 🟢 **Đáp ứng thiết kế đầy đủ, runtime PRODUCTION-mode đã fail-closed đúng chuẩn.** `OTP_DEMO_MODE` mặc định tắt, chặn cứng ở tầng `config.py` nếu ai bật nhầm cùng `production`. **Vẫn phải nói rõ**: dynamic linking + constant-time compare + token-revocation giờ đã đủ 3 lớp, nhưng "sở hữu" (SMS thật) mới dừng ở MÔ PHỎNG khi `OTP_DEMO_MODE=true` (dùng cho demo/CI) — câu dùng với đối tác vẫn phải là *"thiết kế đạt PSD2 RTS Điều 5; kênh SMS thật CHƯA tích hợp nhà cung cấp"*, không phải "đã tuân thủ PSD2" trần trụi. |
| **GDPR (EU)** | Đáp ứng MỘT PHẦN — DPIA chưa có hồ sơ chính thức, không route export/xoá | 🟡 **Không đổi về code.** Đã có **KHUNG DPIA** (`2026-08-30-C4-dpia-dieu25-khung-draft.md`, chưa ký — tự khai rõ chưa xác nhận số điều Luật 91/2025/NĐ 356/2025 tương đương Đ.25 cũ) và **IR runbook draft** (`C3`, chưa ký). Route xoá/xuất dữ liệu (Đ.15/17) **xác nhận lại hôm nay: vẫn 0 route** trong `contracts/authority-matrix.yaml` (grep không khớp `export`/`delete.*user`/`users/me`). Đây vẫn là GAP CHƯA CÓ QUYẾT ĐỊNH — không tìm thấy ADR nào hoãn nó có chủ đích. |
| **PCI-DSS** | Không áp dụng (có điều kiện) | Không đổi. |
| **NIST SP 800-63B (US)** | Thiết kế ~AAL2, runtime demo ~AAL1 | 🟢 **Thiết kế AAL2 + runtime PRODUCTION-mode giờ khớp thiết kế** (yếu tố "sở hữu" không còn bị xoá bởi response lộ OTP khi demo tắt đúng cách). AAL3/FIDO2 cho `supervisor` vẫn là khoảng cách dài hạn, không đổi so với 27/08. |
| **FFIEC (US banking)** | Layered security có, out-of-band verification chưa thật | 🟢 **Layered security 4 lớp không đổi + out-of-band giờ thật khi `OTP_DEMO_MODE=false`** (kênh gửi vẫn cần tích hợp nhà cung cấp SMS thật — chưa kiểm được, xem mục 6). |
| **ISO 27001/27701, SOC2 Type II** | Nền tảng tốt, thiếu IR runbook chính thức + security headers | 🟡 **IR runbook nay có DRAFT** (chưa ký — vẫn treo). **Security headers Caddyfile vẫn 0/4** (`grep -E 'X-Frame-Options\|Strict-Transport-Security\|Content-Security-Policy\|X-Content-Type-Options' Caddyfile` → xác nhận lại hôm nay, vẫn 0 kết quả — đề xuất `db8d460` từ 27/08 chưa merge). Segregation-of-duties mở rộng (supervisor tự điều tra rồi supervisor khác duyệt) — vẫn là câu hỏi mở, chưa có test định lượng nào được viết (backlog QA-QC 27/08 mục 4 chưa làm). |
| **AML/CFT (FATF)** | Ngoài phạm vi PRD, cần khai rõ ranh giới | Không đổi. |

## 5. Đã kiểm và đạt (bổ sung so với bản 27/08 — không lặp các mục đã liệt kê ở đó)

- 3/3 phát hiện CAO/TB của báo cáo 27/08 xác nhận ĐÃ VÁ trên `HEAD` hôm nay, có gate đỏ-trước/xanh-sau
  độc lập đứng sau (mục 2).
- Cặp nguy hiểm nhất của LAN-expose (`ctc1-check`: OTP demo bật + cổng mở) đã được vá tận gốc
  (`docker-compose.yml` mặc định loopback cho MỌI ngăn sau này, dùng biến `CADDY_BIND_HOST` thay vì
  hardcode).
- OTP demo mode dùng đúng mẫu **fail-closed** (raise lúc khởi động nếu cấu hình sai), không phải
  fail-open — đây là mẫu vá đúng tinh thần "Secret không có giá trị mặc định" của checklist đóng gói
  production.

## 6. Chưa kiểm được và vì sao (bổ sung)

- **Kênh SMS thật** — chưa xác nhận đã tích hợp nhà cung cấp nào khi `OTP_DEMO_MODE=false` ngoài môi
  trường demo/CI. Nếu chưa có, `OTP_DEMO_MODE=false` đúng ra chặn được lộ OTP nhưng **không tạo ra
  được luồng gửi OTP thật** — cần xác nhận với `tech-lead`/PO đây có phải trạng thái "sẵn sàng bật
  production nhưng thiếu nhà cung cấp SMS" hay còn thiếu code.
- **`OTP_DEMO_MODE` thật của `po-demo`/`qa-stripe`** tại đúng thời điểm đọc báo cáo này — số đo
  (`ctc1-check=true`, `qa-stripe=false`, `po-demo=không đặt`) là ảnh chụp lúc 01/09 đêm qua, có thể
  đã đổi nếu có ai dựng lại ngăn nào từ đó tới giờ; đọc `§0-TER` để biết ngăn nào còn "neo" không
  được rebuild.
- Mọi mục "Chưa kiểm được" của bản 27/08 vẫn giữ nguyên (hiệu quả bộ lọc injection trên case mới,
  trạng thái thật `.env` production, CI xanh/đỏ thật, nội dung DPA hợp đồng nhà cung cấp LLM) — không
  có dữ kiện mới nào trong các commit gần đây thay đổi các mục đó.

## 7. Punch-list cho Lead — CHỈ việc còn mở, đã loại bỏ mọi thứ đã xong ở mục 2/5

**coder — có thể làm ngay, không chờ PO:**
1. Merge đề xuất security headers vào `Caddyfile` (`db8d460`, 27/08) — vẫn 0/4 header, việc rẻ nhất
   còn tồn đọng lâu nhất trong toàn bộ danh sách này.
2. Ghim `po-demo` sang loopback ở lần dựng lại tiếp theo — dùng đúng khuôn `CADDY_BIND_HOST` đã có
   sẵn trong `docker-compose.yml`, KHÔNG dựng lại trước khi buổi quay 01/09 xong (lệnh cấm §0-TER).
3. Dọn `QWEN_API_KEY` khỏi `.env` sau khi PO xác nhận đã thu hồi trên console DashScope.

**tester — viết theo QUYẾT ĐỊNH, không đọc `src/`:**
4. Test chính thức cho `require_token_chua_thu_hoi` trên 3 route (`propose_resolution`,
   `escalate_ticket`, `request-approval-otp`) — hiện chỉ có script audit tạm của `security`, chưa
   được đưa vào `tests/`. Ưu tiên cao vì đây là gate đã đo XANH nhưng không có cổng tự động giữ nó
   xanh mãi.
5. Test segregation-of-duties định lượng (supervisor A điều tra, supervisor B duyệt) — backlog từ
   27/08 mục QA-QC-4, vẫn chưa làm.
6. Sau buổi quay demo: dọn 4 hiện vật OTP đã commit (`git rm --cached` + đổi đường ghi
   `kich-ban-chuyen-gia-render-that.spec.ts` ra ngoài repo) — **KHÔNG làm trước khi quay xong**, đụng
   đúng 4 file tranh chấp §0b.19e.

**review:**
7. Đọc toàn bộ ~56 ADR (chưa ai đọc hết tính tới báo cáo 30/08) xác nhận có/không có ADR quyết định
   hoãn route GDPR export/xoá dữ liệu — tránh backlog trùng.
8. Xác nhận `docs/STATE.md §0-TER` (bàn giao 01/09) đã được mọi vai đọc trước khi bắt việc — mục
   "SÁU LỆNH CẤM" ở đầu file đó chặn đúng những thao tác dễ phá mốc neo buổi quay & benchmark
   30-31/08 (không rebuild ảnh, không `docker compose down -v`, không sửa `src/`/`migrations/`).

**PO (việc tay, không ai tự động hoá được):**
9. Ký/quyết KHUNG DPIA (`C4`, đã đủ vật liệu kỹ thuật, chỉ thiếu bước ký + xác nhận số điều luật mới).
10. Quyết GDPR export/xoá dữ liệu có nằm trong phạm vi MVP hay hoãn có chủ đích (chưa có ADR nào ghi).
11. Quyết segregation-of-duties mở rộng (supervisor tự điều tra rồi tự thu xếp supervisor khác duyệt)
    — câu hỏi mở từ `contracts/authority-matrix.yaml`, cần chuyên gia ví điện tử/domain, không phải
    quyết định kỹ thuật thuần.
12. Xác nhận kênh SMS thật (mục 6) — thiếu nhà cung cấp hay đã có, chỉ tôi chưa đọc thấy.

## 8. Điều PO phải quyết trước khi dùng cụm từ "PSD2/SCA/AAL2-compliant" — CẬP NHẬT so với 30/08

**Đỡ ngặt hơn bản 30/08**: `OTP_DEMO_MODE` fail-closed đã đóng đúng lỗ khiến 30/08 phải cấm hoàn
toàn các cụm từ này. Câu dùng được TỪ HÔM NAY, có điều kiện: *"Thiết kế đạt PSD2 RTS Điều 5 (dynamic
linking) và NIST AAL2; runtime production-mode fail-closed đúng chuẩn; kênh gửi SMS out-of-band thật
[CẦN XÁC NHẬN mục 6 — đã tích hợp hay chưa] trước khi tuyên bố ĐANG VẬN HÀNH ở AAL2."* Không được rút
gọn thành "hệ thống đạt PSD2/AAL2" trần trụi cho tới khi mục 6 được xác nhận.
