# Rà bảo mật — Phase 0 + Phase 1 ĐÃ ÁP THẬT (learning loop)

> Vai: **security** · 2026-08-14 · nhánh `dev/learning-loop`
> Phạm vi rà: `8fe3bed` (contract v2.1.0 + ADR-016→019) · `02d2b2a` (migration
> + route + QA-02 + M-02) · `5493080` (SEC-B + tiêu thụ OTP + `created_by`).
> Đối chiếu: mục 7 `threat-model-learning-loop.md` (rà sơ bộ) và phiếu duyệt
> `docs/giao-viec/2026-08-14-po-review-goi-phase0.md`.
>
> **Mọi kết luận dưới đây có bằng chứng chạy thật trên stack đang chạy**
> (backend rebuild 14/08, Postgres thật) hoặc trích diff. Không kết luận nào
> dựa trên mô tả của coder hay PO. Đánh số phát hiện tiếp nối
> `review-2026-08-13.md` (F-01…F-10) — đợt này là **F-11…F-16**.
>
> Dữ liệu sau khi rà: hàng chờ duyệt **3 pending_approval · 3 rejected ·
> 6 approved** — đúng như trước khi rà, probe không làm đổi trạng thái
> resolution nào (2 challenge OTP do probe tạo đã xoá).

---

## Kết luận

| Phần | Kết luận | Điều kiện |
|---|---|---|
| **Phase 0** (contract v2.1.0 + ADR-016→019) | **ĐẠT CÓ ĐIỀU KIỆN** | ADR-019 §6 ghi "backfill 1 dòng" — thực tế **3 dòng**; ADR-019 §5 mô tả field ghi chú như đã chốt trong khi code chưa có. Sửa 2 dòng chú thích, không chạm thiết kế. |
| **Phase 1** (migration + route + SEC-B + OTP + `created_by`) | **ĐẠT CÓ ĐIỀU KIỆN** | Lõi đạt và mục quan trọng nhất (không rò trường mới) **đạt tuyệt đối**. Ba điều kiện: F-11 (backfill bịa người + thời điểm), F-13 (hitl_status chưa backfill), F-15 (CHECK một chiều). Cả ba đều rẻ. |
| **TM-03** (field ghi chú tự do) | **ĐẠT — SIGN-OFF, coder được mở khoá** | Kèm 13 test đối kháng bắt buộc (mục Nhiệm vụ 2) + fail-closed khi scrub lỗi. |

**Không có phát hiện nào ở mức CHẶN.** Hai phát hiện mức CAO (F-11, F-12) đều
không chặn demo nhưng **phải đóng trước khi có người dùng thật** — F-12 là
phát hiện nặng nhất đợt này và nằm ngoài phạm vi coder được giao.

---

## Nhiệm vụ 1 — Rà bản áp thật

| # | Mục | Kết quả | Bằng chứng chạy thật |
|---|---|---|---|
| 1 | **Trường mới không rò qua customer/LLM** (mục quan trọng nhất) | **ĐẠT — sạch trên mọi đường đo** | Probe với JWT khách USR-0119 (chủ `TCK-518527ab869f`, ticket có 2 resolution `rejected`, `reject_reason='khac'`, `rejected_by='USR-0205'`), qua trọn luồng OTP thật. Dò 7 dấu hiệu (`reject_reason`·`rejected_by`·`rejected_at`·`created_by`·`"khac"`·`USR-0205`·`Phan Hữu Châu`): `POST /tools/get_customer_history` (9.378 ký tự) **sạch** · `POST /tools/lookup_transaction` (505) **sạch** · `build_customer_tools().invoke()` — **đúng chuỗi đi vào prompt LLM** — 10.120 và 541 ký tự, **sạch cả hai**. Route nhân viên khi khách gọi: `/tickets/{id}` `/tickets` `/resolutions` `/reports/summary` → **403 cả bốn**. Kiểm kê tĩnh khớp: 2 nơi duy nhất đọc trường mới là `main.py:713-715` (ticket detail, gated `cskh,supervisor`) và `main.py:932-933` (response route reject, `supervisor`). |
| 2 | **Reject vẫn không-OTP** | **ĐẠT — không ai thêm bước thừa** | Gọi reject **không gửi OTP** (không mutate): resolution không tồn tại → **404** (không phải 403 ⟹ không có cổng OTP đứng trước); resolution đã `rejected` → **400** "đang ở trạng thái rejected, không từ chối được" (guard trạng thái chạm được, vẫn không cần OTP). Thiếu `reason` → **422**; `reason` ngoài enum → **422** (chặn ở `Literal`); CSKH gọi → **403** (INV-03 còn nguyên). |
| 3 | **BR-11 hiệu lực + kẽ hở NULL** | **ĐẠT chiều thuận · CÓ KẼ HỞ chiều nghịch (F-15)** | Ghi thẳng Postgres, transaction + rollback. Chiều thuận **chặn đủ 5/5**: rejected thiếu cả ba · thiếu từng trường (reason / by / at) · reason ngoài enum → `CheckViolation`; hàng hợp lệ ghi được. BR-10 kiểm lại: approved thiếu `approved_by` → chặn. **Chiều nghịch KHÔNG được canh**: hàng `pending_approval` **và** hàng `approved` vẫn **ghi được** kèm `reject_reason`/`rejected_by`/`rejected_at` → F-15. *(Ghi chú trung thực: bản probe đầu của tôi "ĐẠT" toàn bộ vì mọi INSERT chết ở `NOT NULL created_at` trước khi chạm CHECK — đúng loại bẫy "xanh vì lý do sai" mà QA vừa rút kinh nghiệm ở SEC-B. Kết quả trên là bản đã sửa, chạy lại.)* |
| 4 | **Backfill 3 dòng cũ** | **KHÔNG ĐẠT — F-11** | Cờ học: `khac` → `la_tin_hieu_hoc: false` ⟹ 3 dòng **không lọt phễu Phase 2** — phần này **đạt**. Nhưng dữ liệu kiểm toán **mập mờ**: cả 3 dòng có `rejected_by='USR-0205'` (Phan Hữu Châu) trong khi DB có **2 supervisor** (USR-0205, USR-0206) — người này bị migration gán vào bằng `ORDER BY user_id LIMIT 1`; và `rejected_at = created_at` **chính xác tới micro-giây ở cả 3 dòng** (SQL `COALESCE(rejected_at, approved_at, created_at)`), tức sổ ghi "từ chối xảy ra đúng lúc đề xuất được tạo". Ghi chú trong `rationale` chỉ nói *lý do* không được ghi lại, **không** tiết lộ rằng người và thời điểm là suy ra. |
| 5 | **ADR-016→019 dưới lăng kính bảo mật** | **ĐẠT có 3 ghi chú** | (a) ADR-019 §6 ghi "backfill **1 dòng**", thực tế **3 dòng** — ADR là bản ghi kiểm toán của chính thao tác chạm dữ liệu kiểm toán, phải khớp. (b) ADR-019 §5 mô tả field ghi chú như **đã chốt** trong khi code **chưa có** (đúng lệnh chờ sign-off — nay đã mở, xem Nhiệm vụ 2). (c) **ADR-018 tự khai 2 nợ PHẢI cứng hoá, chưa làm** → F-14. Ngược lại, không ADR nào mô tả thiếu so với code. ADR-016/017/018 đều có mục "Lý do BÁC BỎ" đúng chuẩn. |

**Nền tảng contract**: 22/22 test bất biến xanh (`pytest tests/test_invariants.py`),
`check_contracts.py` → "Không có artifact lỗi thời", 3 hash contract khớp
baseline (`resolution-state-machine.yaml` = `35001b6ecb04`).

**Ba việc gộp theo đề nghị của tôi ở mục 7 threat model — đã làm đủ**:
`created_by` (nullable vĩnh viễn, ghi từ JWT không nhận từ body: `main.py:537`);
SEC-B (approve chỉ nhận `pending_approval`: `main.py:816`); tiêu thụ OTP
(`otp_status='consumed'` + `otp_code=None`: `main.py:857-862`).

### Phát hiện mới

| # | Mức | Vị trí | Mô tả | Giao ai |
|---|---|---|---|---|
| **F-11** | **CAO** | `migrations/versions/a1b2c3d4e5f6_reject_reason_adr019.py` | **Backfill bịa dữ liệu vào sổ kiểm toán, và chú thích nói ngược với code.** Comment ngay trên câu SQL viết: *"thà để migration hỏng còn hơn gán bừa một cái tên người vào bản ghi kiểm toán"* — rồi câu SQL bên dưới làm đúng điều đó: `rejected_by = ... (SELECT user_id FROM users WHERE role='supervisor' ORDER BY user_id LIMIT 1)` → gán **Phan Hữu Châu (USR-0205)** cho cả 3 lần từ chối, dù có 2 supervisor và không có gì chứng minh là ông ấy. Kèm `rejected_at = created_at` (thời điểm bịa). Migration anh em `b2c3d4e5f6a7` (`created_by`) áp **đúng** nguyên tắc này ("NULLABLE VĨNH VIỄN, KHÔNG backfill") — cùng một đợt, hai chuẩn khác nhau. Hệ quả xa: mọi thống kê theo `rejected_by`, và mọi phép đo SLA thời-gian-ra-quyết-định (G1) tính từ `rejected_at`, đều sai âm thầm. | **coder** — đề xuất: trỏ `rejected_by` vào **user sentinel hệ thống** (không phải người thật) hoặc, vì 2/3 dòng là dữ liệu QA (`RES-663769e6d9dc`, `RES-b9b1f9344dc6`), PO cho phép xoá hẳn; và mở rộng ghi chú `rationale` để nói rõ **cả người lẫn thời điểm** là suy ra. Kèm sửa ADR-019 §6 (1→3 dòng). |
| **F-12** | **CAO** | `src/api/main.py:800-870` (`approve_resolution`) | **OTP duyệt tiền không có throttle lẫn lockout — brute-force được.** Đo thật: **60 lần gửi mã SAI liên tiếp, 275 req/s, 0 lần 429**, và sau đó challenge vẫn `failed_attempts=0`, `otp_status='pending'`, `otp_code` còn sống. Route `approve` **không có `@limiter.limit`** (route `request-approval-otp` ngay trên nó thì có) và **không tăng `failed_attempts`**. Đối chiếu: đường OTP của **khách** (`/auth/otp/verify`) có **cả hai** — `@limiter.limit("10/minute")` và khoá sau 3 lần sai (`main.py:424-438`). Tức đường **ít rủi ro hơn được bảo vệ, đường chạm tiền thì không**. Docstring `AuthSession` còn ghi rõ ý định *"tái dùng nguyên cơ chế failed_attempts/locked_at đã có"* — ý định có trong thiết kế, **không có trong code**. Đường tấn công: kẻ chiếm được phiên supervisor (đúng kịch bản mà step-up OTP sinh ra để chặn) dò 6 chữ số trong cửa sổ 10 phút; ở tốc độ đo được là ~15% mỗi cửa sổ, và xin challenge mới được 10 lần/phút. Vi phạm NIST 800-63B §5.2.2 (bắt buộc throttle) và làm rỗng nghĩa PSD2 dynamic linking. **Có trước đợt này**, không do Phase 1 gây ra — nhưng nằm đúng trong hàm đợt này vừa sửa. | **coder** — vá rẻ: thêm `@limiter.limit` cho `/approve` + tăng `failed_attempts` và chặn theo `OTP_MAX_FAILED_ATTEMPTS`/`locked_at`, sao đúng khuôn `main.py:424-438`. **tester**: test "N lần sai → khoá", viết từ đặc tả này. |
| **F-13** | TRUNG BÌNH | Dữ liệu `tickets` | **Vá QA-02 không backfill dữ liệu cũ**: `_dong_bo_hitl_status()` chỉ chạy khi có approve/reject MỚI, nên **8 ticket** vẫn có `hitl_status='pending'` trong khi resolution của chúng đã `approved`/`rejected` (6 approved + 2 rejected — đã liệt kê bằng truy vấn). Contract v2.1.0 `dan_xuat.quy_tac` nói hitl_status **theo resolution mới nhất** — 8 dòng này vi phạm chính quy tắc vừa ghi. Mục đích của QA-02 là để thống kê duyệt/từ chối tin được ("không có số sạch thì không đo được gì" — kế hoạch §1); chưa backfill thì số vẫn bẩn đúng ở phần lịch sử. | **coder** — 1 câu UPDATE trong cùng đợt, hoặc PO chấp nhận có chủ đích và ghi rõ vào STATE. **tester**: test bất biến dữ liệu "không tồn tại ticket có hitl_status='pending' mà resolution mới nhất đã approved/rejected". |
| **F-14** | TRUNG BÌNH | `src/api/live_chat_ws.py:105,305-306` | **Nợ ADR-018 tự khai "PHẢI cứng hoá" vẫn chưa làm**: `_session_staff` vẫn là dict RAM **không TTL** (dòng 105), và khi đã có entry thì trả thẳng (dòng 305-306) chứ không kiểm tươi. Đúng kịch bản ADR-018 mô tả: worker lỡ sự kiện `unclaim` (pub/sub fire-and-forget) giữ ánh xạ cũ vĩnh viễn → **tin của khách chảy sang CSKH không còn phụ trách phiên**. Chính ADR gọi đây là chạm PDPA/US-016. Lưới đọc lại nguồn khi *thiếu* entry (dòng 308-314) đã có; thiếu đúng phần **hết hạn entry cũ**. | **coder** — TTL 30–60s như ADR-018 đã chốt. Carry-over, không do đợt này gây ra. |
| **F-15** | TRUNG BÌNH | `models.py` CHECK br11 | **BR-11 chỉ canh một chiều.** `rejected ⟹ đủ 3 trường` được ép; chiều ngược `có nhãn từ chối ⟹ phải là rejected` **không** — đã ghi được thật hàng `pending_approval` và hàng `approved` mang `reject_reason='sai_so_lieu'` + `rejected_by` + `rejected_at`. Route hiện tại không tạo ra tình trạng này, nhưng BR-10/BR-11 tồn tại chính vì kịch bản "UPDATE viết tay / route mới quên kiểm" (ADR-003). **Rủi ro cụ thể cho Phase 2**: nếu exporter lọc theo `reject_reason IS NOT NULL` thay vì `status='rejected'`, một nhãn sót/bị chèn trên hàng chưa từ chối sẽ kéo case vào phễu học; và một hàng `approved` mang sẵn hồ sơ từ chối là dữ liệu kiểm toán tự mâu thuẫn. Đã kiểm: hiện **0 hàng** vi phạm ⟹ thêm CHECK đối xứng an toàn, không cần backfill. | **coder** — CHECK `(status = 'rejected') OR (reject_reason IS NULL AND rejected_by IS NULL AND rejected_at IS NULL)`. **Bắt buộc kèm**: đặc tả exporter Phase 2 lọc theo `status='rejected' AND la_tin_hieu_hoc(reject_reason)`, **không** lọc theo nhãn đơn thuần. |
| **F-16** | GHI NHẬN | `models.py` (br10 + br11) | `rejected_by`/`approved_by` chỉ có FK **kiểm tồn tại, không kiểm vai** — ghi thẳng DB đặt được `rejected_by` = khách hàng (USR-0119) hoặc CSKH (USR-0201), cả hai đều **ghi được**. CHECK chuẩn SQL không truy vấn bảng khác nên **không ép được bằng CHECK** — nói rõ để không ai đặt việc bất khả thi. Đường route đã chặn (`require_role("supervisor")`, verify 403 ở trên). Bù bằng F-05 (audit log append-only) hoặc trigger nếu sau này cần. | **ghi nhận**, không giao việc ngay. |

---

## Nhiệm vụ 2 — SIGN-OFF TM-03: field ghi chú tự do

**Phán quyết: ĐẠT. Coder được mở khoá code field `note`.**

Thiết kế PO đã chốt thoả đủ 5 điều kiện TM-03 (scrub trước khi ghi DB · ≤500 ký
tự · chỉ đọc qua route staff · không bao giờ vào context agent · không bao giờ
xuất ra file ứng viên). Điểm mấu chốt tôi xác nhận lại: **ranh giới một chiều là
điểm export, không phải điểm hiển thị** — giá trị nhãn ở lại DB dưới quyền role,
git chỉ thấy enum. Hạ tầng đã sẵn: `scrub_pii(text: str | None) -> str | None`
(`src/observability/pii.py:277`).

**Ba điều kiện kỹ thuật kèm sign-off (bắt buộc, không thương lượng):**

1. **Scrub tại điểm GHI, không tại điểm đọc.** Giá trị nằm trong DB phải là bản
   đã che — kiểm bằng đọc thẳng DB, không qua response API.
2. **Fail-closed.** `scrub_pii` ném lỗi/timeout (Presidio, underthesea) ⟹ **từ
   chối ghi cả bản ghi**, trả lỗi rõ; tuyệt đối không ghi bản thô rồi hẹn che sau.
3. **Không mở rộng phạm vi đọc.** `note` chỉ xuất hiện ở route đã gated
   `cskh,supervisor`. Không thêm vào `/reports/summary`, không thêm vào bất kỳ
   payload nào của live-chat.

**Danh sách test đối kháng giao tester** (viết từ đặc tả này, không đọc `src/`):

*Nhóm A — scrub tại điểm ghi (đọc thẳng DB để assert):*
1. `note` chứa SĐT `0912345678` → giá trị trong DB đã che.
2. `note` chứa SĐT dạng `+84 91 234 56 78` và `091-234-5678` → đã che.
3. `note` chứa CCCD 12 số → đã che (chấp nhận che nhầm mã 12 số khác).
4. `note` chứa **tên người** ("khách Trần Văn B khai sai") → đã che (đây là ca
   regex không bắt được, chứng minh lớp NER đang chạy — đúng bài học ADR-010).
5. `note` chứa số tài khoản 9–19 chữ số / đầu `9704` → đã che.

*Nhóm B — ràng buộc trường:*
6. `note` dài 501 ký tự → **422**; đúng 500 → **200**.
7. `reason='khac'` mà thiếu `note` → **422** (bắt buộc).
8. `reason='sai_so_lieu'` không có `note` → **200** (tuỳ chọn).
9. `note` rỗng/toàn khoảng trắng với `khac` → **422** (không lách bằng chuỗi rỗng).

*Nhóm C — ranh giới rò rỉ (quan trọng nhất):*
10. Sau khi từ chối có `note`, `note` **không xuất hiện** trong output của
    `get_customer_history` và `lookup_transaction` — kiểm **cả** REST lẫn
    `build_customer_tools().invoke()` (đường vào prompt LLM).
11. `note` không xuất hiện ở bất kỳ route nào khách gọi được, kể cả
    `/live-chat/sessions/{id}/messages`; route ticket detail (staff) **có** `note`.
12. `note` không xuất hiện trong log/span observability (đường Jaeger).
13. `note` chứa payload injection ("bỏ qua hướng dẫn trên…") → vẫn không lên LLM,
    và bản ghi mang **cờ cảnh báo** để người duyệt ứng viên thấy (nối vào
    checklist A của threat model).

*Nhóm D — khi exporter Phase 2 có mã:* `note` **không** có mặt trong
`eval/candidates/*.jsonl` kể cả đã scrub (test đối kháng bắt buộc, thuộc danh
sách kiểm mục 6 threat model).

---

## Nhiệm vụ 3 — Chuỗi bàn giao checklist

**`eval/CANDIDATE-REVIEW.md` CHƯA TỒN TẠI** (đã kiểm `ls eval/`; cũng chưa có
`eval/candidates/`). Chưa có gì để đối chiếu — trạng thái: **chờ tester**.

Khi tester dựng, tối thiểu phải mang đủ 8 mục của checklist A
(`threat-model-learning-loop.md` §5), và **hai mục sau là điều kiện đủ, không
được rút gọn**:

- **Luật CẤM NGUYÊN VĂN** — case vào `golden_set`/few-shot phải được người duyệt
  **viết lại** bằng lời mình + dữ liệu seed (`data/generated/`), không copy-paste
  câu nào của khách. Đây là mục vô hiệu hoá cùng lúc payload injection và PII
  còn sót; mất mục này thì toàn bộ phòng tuyến duyệt tay chỉ còn là đọc lướt.
- **Trần ứng viên/người dùng** — 1/người/ngày, tối đa 3/người toàn vòng đời,
  trần toàn cục 20/ngày, kèm loại phiên < 3 lượt khách hoặc không có tool call
  (chống CSAT bombing, `threat-model-learning-loop.md` §3).

Thiếu một trong hai → tôi sẽ ghi KHÔNG ĐẠT ở lần rà Phase 2.

---

## Việc giao ra từ đợt rà này

| Vai | Việc |
|---|---|
| **coder** | F-11 (sentinel/xoá + ghi chú đủ + sửa ADR-019 §6 "1→3 dòng") · **F-12 (nặng nhất: throttle + lockout cho `/approve`)** · F-13 (backfill hitl_status) · F-15 (CHECK đối xứng + đặc tả lọc exporter theo `status='rejected'`) · F-14 (TTL `_session_staff`, nợ ADR-018) · code field `note` theo sign-off trên |
| **tester** | 13 test đối kháng `note` · test "N lần sai OTP duyệt → khoá" (F-12) · test bất biến dữ liệu hitl_status (F-13) · dựng `eval/CANDIDATE-REVIEW.md` với 8 mục checklist A |
| **PO** | Quyết F-11 (sentinel hay xoá 2 dòng QA) · xếp lịch F-12 trước mốc người dùng thật · ghi nhận F-14 là nợ carry-over có chủ đích hay đóng luôn đợt này |
