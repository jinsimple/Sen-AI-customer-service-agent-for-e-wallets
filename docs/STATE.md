# Trạng thái hiện tại

Cập nhật: **2026-08-14 sáng** · Phiên vừa rồi: PO (tổng hợp đêm vá 13/08, chuẩn bị demo)

> Ghi đè mỗi cuối phiên bằng `/wrapup`. Giữ **dưới 60 dòng**.
> Lịch sử quyết định KHÔNG nằm ở đây — nằm ở `docs/DECISIONS.md`.

## Vừa xong (đêm 13/08 — 4 commit `2d9a709`→`f2d4785`, đã verify trong container)

- **QA-13 (P0) live-chat mất tin liên worker — ĐÃ VÁ**: quyết định người nhận
  LÚC GIAO TIN thay vì dựa lớp đăng ký trước. Đo lại: 60/60 tin, 0 mất, 0 lặp.
  **CẦN ADR-018 ghi nguyên tắc này + lý do bác bỏ** — chưa ghi, phiên sau dễ
  "tối ưu" ngược làm bug im lặng quay lại.
- **R1 latency — tìm ra gốc**: scrub PII chạy trên span attribute TRƯỚC khi cắt
  (`b598096`). Đường demo thật: 3,6–23,2s/lượt. **Số p50 37,7s là artifact
  của eval harness (SQLite in-process, case nhiều lượt), không phải sản phẩm.**
- **Thước "bịa số liệu" đã vá** (`2d9a709`): tách bịa-thật / ID-đã-xác-minh /
  ID-chưa-xác-minh + chế độ `--rescore`. Chấm lại 2 run cũ: **0/40 bịa thật**.
  ⇒ **Gate cắt token đổi từ ≤10% thành 0%** (con số 4/40=10% cũ là false positive).
- 6 lỗi biên bản QA 13/08 (`6deb6cc`): vé WS RAM/worker (QA-01), ticket ma từ
  nhánh timeout (QA-10), rate-limit vé WS CSKH (QA-11), "[object Object]" (QA-05)…
- **Demo 14/08**: 4 case chốt `eval/demo_cases_20260814.md` · checklist + bẫy
  `docs/DEMO-READINESS-2026-08-14.md` · LangSmith đã TẮT trong container.

## Đang dở

- **Cắt token (mục 4b) CHƯA LÀM.** Số đo cũ vẫn đúng: schema tool 1.945 token
  (docstring 1.377), system prompt 4.587 token. Baseline so ghép cặp giờ là
  bản `*_rescored.json` với gate **0% bịa thật**.
- **Triage 29/40 XONG** (`eval/results/trige_29_case_20260814.md`, 14/08):
  KHÔNG phải 29 lỗi — A1=13 dữ liệu bộ case mâu thuẫn contract · A2=5 dấu vết
  bug đã vá (2 xanh, 2 lỗi thật, 1 crash mới) · B1=7 hành vi sai thật (4
  regression sau 13/08: CASE-019/082/083/101 + CASE-004 tự chọn candidate —
  chạm ràng buộc cứng 3) · B2=4 tranh chấp đặc tả (giao dịch processing).
  **Việc thật: 9 lỗi hành vi + 1 crash.** Gate 0% bịa dùng được ngay;
  thước tổng thể chỉ sạch khi xử lý xong nhóm A1.
- **Lỗi dữ liệu from_bank (A1)**: 28/28 case cả 4 ô `from_bank` có ví khách
  không phải một bên giao dịch (gen_dataset gán sai ví nhận) — 1/3 ma trận
  nghiệp vụ không thể pass. Hướng PO: SINH LẠI dữ liệu theo contract (bác bỏ
  đổi định nghĩa "một bên" — chạm ATLAS-001). CHỈ làm sau demo tối 14/08 vì
  reseed phá bộ case demo D1–D4; gộp với dọn dữ liệu M-04 trước đợt 150 người.
- **CASE-110 crash (A2)**: tạo ticket "cần tra thủ công" khi trans_id không
  tồn tại → IntegrityError FK, hỏng cả lượt. Trước bị nhánh timeout che, lộ
  ra sau khi latency giảm. Fix cho coder trên dev; demo tối nay NÉ đường này
  (đã ghi vào DEMO-READINESS).

## Chặn / chờ (việc của PO)

- **Nâng tier OpenAI** (Tier 1 = 200K TPM ⇒ ~13 lượt/phút toàn hệ) + **DPA**.
- **Xoay LANGCHAIN_API_KEY sau demo** — key hiện nguyên văn trong log phiên QA.
- Quyết ST2-P0-3 (PII live-chat cho staff) TRƯỚC đợt 150 người thật (mốc ADR-011).
- QA-07: docs còn nói passwordless (đã dùng mật khẩu) → sửa docs + chạy lại
  `scripts/export_project_knowledge.py` + upload (snapshot đang cũ hơn 5 commit).

## Phát hiện mới từ smoke sáng 14/08 (không chặn demo, xử lý sau)

- **M-01 (P2)**: bộ lọc "ngoài phạm vi" nhạy từ khoá — thiếu chữ "khiếu nại"/
  "ticket" là từ chối nhầm câu hợp lệ. Cần case eval riêng + nới điều kiện.
- **M-02 (P3)**: API chi tiết ticket không trả `approved_by`/`approved_at`
  (DB có đủ) — US-017 chưa hiển thị được, thêm trường + UI.
- **M-05**: agent không đọc lại được mã ticket vừa tạo khi khách hỏi lại.
- **M-04**: dữ liệu demo phình (~730 ticket, USR-0145 có 8 khiếu nại) — cần
  script dọn/reseed TRƯỚC đợt 150 người.
- **Gap hạ tầng test**: Playwright config mặc định spawn `npm run dev` (stack
  thứ hai, bẫy ADR-009) — chỉ `playwright.livechat.config.ts` trỏ Docker.
  Cần config chạy toàn bộ e2e trên stack Docker.

## Phát hiện security 14/08 (commit 66dc6cf — 2 tài liệu đầu tiên trong docs/security/)

- **SEC-A (P1): `reject_resolution` KHÔNG có guard trạng thái** (main.py:844)
  — resolution đã `approved` vẫn lật được sang `rejected`, không OTP, không
  vết. Trái contract (chỉ `pending_approval → rejected`). Code lệch contract
  hiện hành → coder SỬA NGAY trên dev, không cần ADR; tester thêm test bất
  biến bắt cả hai chiều.
- **SEC-B (P1): guard approve nhận cả `draft`** (main.py:803) — đường
  `draft → approved` bỏ qua `pending_approval`, trái transition contract.
  Sửa cùng SEC-A.
- **Đính chính PO-TONG-KET §4/G2**: Resolution KHÔNG có cột `created_by`
  (dòng 331 là của Escalation) — maker–checker cần thêm cột + migration,
  không "rẻ" như đã viết. Cột gộp vào migration Phase 1; CHECK maker–checker
  đi ADR riêng.
- **Câu hỏi mở Phase 2 (security nêu, PO đề xuất, chờ chốt)**: CSAT gắn phiên
  live-chat có CSKH người → điểm thấp có thể là lỗi người, không phải AI.
  Đề xuất PO: exporter v1 CHỈ dùng phễu reject (có sếp ở giữa); CSAT ≤2 chỉ
  tạo cảnh báo vận hành, KHÔNG vào phễu học AI — thu hẹp luôn bề mặt
  poisoning (CSAT là kênh kẻ tấn công kiểm soát 100%).

## Cảnh báo còn tồn

- **Load test 150 CHƯA CHẠY** — mọi con số đồng thời vẫn là suy luận.
- Chưa vá, hoãn có chủ đích: QA-02 (hitl_status kẹt `pending` sau duyệt),
  QA-06 (giờ SLA hiển thị UTC lệch 7h), QA-14 (Enter nhanh giữ chữ — có cách né).
- Cứng hoá vá QA-13 (coder + QA đồng thuận, chờ PO): TTL 30–60s cho
  `_session_staff` (rò dữ liệu sang CSKH không phụ trách — chạm US-016);
  DB làm lưới cuối khi Redis rỗng.
- Test bất biến 19/19 · full suite 320 passed · 1 đỏ có chủ đích (ST2-P0-3) · ruff sạch.

## Sau demo

- ADR-016/017/018 (ưu tiên ADR-018 — nguyên tắc giao tin live-chat).
- Lộ trình chuẩn EU/US theo `docs/PO-TONG-KET-2026-08-13.md` (G1 SLA pháp định,
  G2 maker–checker `approved_by != created_by`, G3 audit log bất biến…).
- Ép thứ tự `_enforce_requester_is_party` → `_scrub_pii_cho_llm` tầng kiểu dữ liệu.
- `contracts/tone-of-voice.yaml` · `eval/heldout_set.jsonl` CHỈ CHẠY MỘT LẦN gần cuối.
