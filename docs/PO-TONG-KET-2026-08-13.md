# Tổng kết phân tích PO — 2026-08-13

> Người viết: phiên Claude vai PO (làm việc trực tiếp trên repo, không qua snapshot).
> Trạng thái repo lúc phân tích: HEAD `955264f` + 6 file sửa dở chưa commit.
> **LƯU Ý ƯU TIÊN: toàn bộ lộ trình trong tài liệu này LÙI SAU demo pitching 14/08.**
> Checklist demo: xem `docs/DEMO-READINESS-2026-08-14.md`.

---

## 1. Hiện trạng (TL;DR)

- MVP đã trưởng thành: 320 test xanh, 19 test bất biến introspect app thật,
  multi-worker 4 + Redis pub/sub + PostgresSaver đã verify trong container.
- 3 việc chặn đường găng 150 người: load test chưa chạy · trần TPM Tier 1
  OpenAI (việc của PO thật, có lead time) · cắt token chưa làm.
- `project-knowledge/` lỗi thời: snapshot `3d62a4c` < HEAD `955264f` + 6 file
  chưa commit (`eval/measure_quality.py` +128 dòng, `src/agents/graph.py`,
  `src/api/live_chat_ws.py`, `frontend/src/lib/server-api.ts`, 2 file test).
  Mọi phiên Claude khác đang làm việc trên ảnh chụp cũ.

## 2. Phát hiện MỚI từ eval rescored (chưa commit, chạy 13/08)

So sánh `eval/results/baseline_TRUOC_khi_cat_token_raw_rescored.md` (trước PII
scrub) vs `quality_run_20260813_150352_raw_rescored.md` (sau PII scrub):

| Chỉ số | Trước scrub | Sau scrub | Nhận định |
|---|---|---|---|
| p50 latency | 24,3s | **37,7s (+55%)** | Regression thật |
| p95 / max | 119,5s / 136,5s | 144,9s / **204,1s** | Xấu đi rõ |
| Bịa số tiền | 0/40 | 0/40 | Scorer mới đã tách false-positive ID |
| Vi phạm checks/forbidden | **21/40** | **29/40** | Chưa phân loại nguyên nhân |

- Con số "bịa 10% (4/40)" trong STATE.md là của scorer CŨ — bản rescore tách
  được false positive (số nằm trong mã `TCK-xxx` bị đếm nhầm). Baseline thật
  để so sánh sau này là bản rescored.
- **29/40 vi phạm checks chưa ai phân loại**: lỗi scorer (PII scrub che nhầm
  nội dung mà `expected` pattern cần) hay regression chất lượng thật. Chưa
  phân loại xong thì KHÔNG cắt token, KHÔNG load test — mọi so ghép cặp sau
  này dựa trên bộ chấm này.

## 3. Điểm mạnh đạt/vượt chuẩn — CẤM "tối ưu" lại

(Đồng thuận độc lập giữa phân tích PO và báo cáo bảo mật 13/08)

1. HITL ép ở tầng DB (`ck_resolutions_approved_requires_approver_br10`, ADR-003).
2. PSD2 dynamic linking đúng chuẩn RTS (EU) 2018/389 Điều 5: OTP duyệt gắn
   `resolution_id` + `amount_snapshot` (AUTH5-05/05B).
3. Refresh token rotation + thu hồi cả family (ADR-008); giữ `iat` gốc (ADR-007).
4. Bỏ KBA theo NIST 800-63B-4 (ADR-006).
5. PII masking hai đầu trước khi lên LLM (ADR-010), OWASP LLM02:2025.
6. AI không có role riêng — chặn customer là chặn AI (ADR-001).
7. Contract-as-code + test introspect chống drift = automated control testing
   (ngôn ngữ SOC 2 / DORA: kiểm soát liên tục).
8. Truy vết chống bịa số: `tool_results` → `investigation_logs` →
   `resolutions.cited_tool_result_ids`.

## 4. Gap so với chuẩn ví điện tử EU/US

### CAO — chạm bản chất sản phẩm
- **G1. Không có đồng hồ SLA pháp định.** US Reg E (12 CFR 1005.11): điều tra
  10 ngày làm việc / provisional credit + 45 ngày. EU PSD2 Điều 101 + EBA GL:
  15 ngày làm việc (35 ngoại lệ); giao dịch không ủy quyền hoàn D+1 (Điều 73).
  State machine không có trục thời gian; vòng đời dừng ở `approved` — thiếu
  `executed` + đối soát (2 câu hỏi mở trong contract chính là mảnh này).
- **G2. Maker–checker chưa trọn.** `supervisor` gọi được cả
  `propose_resolution` lẫn `approve` → tự soạn tự duyệt.
  **[SỬA 14/08 — phát hiện của security, PO đã kiểm lại]**: bản đầu của tài
  liệu này viết "created_by có sẵn ở models.py:331, sửa rẻ" — SAI, dòng đó là
  cột của `Escalation`. `Resolution` KHÔNG có cột ghi ai đề xuất và
  `propose_resolution()` không ghi. Maker–checker cần: thêm cột `created_by`
  + migration + CHECK `approved_by != created_by` — gộp vào migration Phase 1
  learning-loop (cột) và ADR riêng (CHECK).
- **G3. Chưa có audit log bất biến** cho hành vi con người (ai đăng nhập, ai
  xem hồ sơ ai, ai duyệt) — GLBA / DORA / SOC 2 đều đòi, dạng append-only
  tamper-evident.

### TRUNG BÌNH — bắt buộc trước dữ liệu thật / thị trường EU-US
- **G4.** Quyền chủ thể dữ liệu (GDPR 15–20, retention). Lưu ý: PostgresSaver
  lưu hội thoại GỐC chưa scrub (scrub chỉ áp đường lên LLM) — cần chính sách
  retention + access control thành văn.
- **G5.** DORA: sổ ICT (đã nhận diện ADR-011) + runbook sự cố + chiến lược
  thoát — hiện phụ thuộc 100% OpenAI, trần TPM là biểu hiện của rủi ro tập trung.
- **G6.** EU AI Act Điều 50: chatbot tự khai báo là AI — nâng "thông báo demo"
  thành yêu cầu vĩnh viễn. HITL tuyệt đối là luận cứ phân loại limited-risk.
- **G7.** Ngưỡng chất lượng model chính thức (SR 11-7 / EBA): "không vượt 10%"
  là ngưỡng không-tụt-lùi, chưa phải ngưỡng đạt chuẩn. Đề xuất ≤2% trên golden
  set — chốt số SAU khi làm sạch bộ chấm (mục 2).

### Đã kiểm chứng từ báo cáo bảo mật 13/08
- Replay approve 2 lần trên cùng resolution: **KHÔNG tạo bút toán kép** (guard
  `status not in (draft, pending_approval)` chặn lần 2 — đã đọc main.py:788).
- **Tồn dư thật:** OTP duyệt KHÔNG bị consume sau khi dùng — vô hại hôm nay
  (không có đường quay lại `pending_approval`) nhưng là bẫy khi thêm luồng
  thu hồi duyệt. Sửa 2 dòng, gộp vào đợt G2.
- `docs/security/` chưa tồn tại — vai security chưa xuất báo cáo nào vào vùng
  ghi của mình; 5 kịch bản tấn công trong template chưa có bằng chứng đã chạy.

## 5. Nghiên cứu 3 chủ đề nâng cấp (13/08, có nguồn trong transcript)

### 5a. Phân loại cảm xúc văn bản
- Hiện có: quy tắc đồng cảm ép trong prompt + 1 case LLM-judge (UXQA-001).
  Chưa có classifier thật, chưa có định tuyến theo cảm xúc.
- Chuẩn ngành: classifier nhỏ (PhoBERT/ViSoBERT/E2v-PhoBERT cho tiếng Việt,
  CPU, ~ms) chạy song song làm TÍN HIỆU ĐỊNH TUYẾN, không phải LLM đoán trên
  đường nóng. Giảm ~20–40% escalation theo báo cáo ngành.
- Thiết kế đề xuất: tín hiệu `ES-xx` tính ở TẦNG SERVICE giống `FS-06`
  (giữ ràng buộc cứng 2 — AI không tự kết luận): ES-01 bức xúc leo thang ≥N
  lượt, ES-02 ngôn ngữ khủng hoảng. Bật → agent ĐỀ NGHỊ `request_human_handoff`
  (khách bấm) + ticket gắn ưu tiên (US-011). Không thêm lượt gọi LLM nào.
- Điểm pitch: dữ liệu cảm xúc không rời hệ thống (on-premise NLP, đã có tiền
  lệ underthesea) — khớp định vị PRD §15.1. CẦN ADR + sửa contract.

### 5b. Prompt injection
- Hiện có: lọc từ khoá `_contains_injection_signal` (kèm không dấu) trên 2
  cửa (RAG + ghi chú giao dịch), 45 case adversarial. Lớp mạnh nhất là KIẾN
  TRÚC: AI-as-customer + forbidden_tools + HITL DB → injection không chuyển
  được tiền.
- Rủi ro tồn dư: (a) dụ agent HỨA/PHÁT BIỂU SAI (rủi ro pháp lý), (b) moi
  system prompt/ngưỡng nội bộ, (c) indirect injection qua tài liệu
  partner_admin upload.
- Nâng cấp rẻ: spotlighting/data-marking kết quả tool + RAG (lọc từ khoá làm
  lớp phụ) · lọc ĐẦU RA chặn lộ system prompt/tên ngưỡng nội bộ · kiểm kê cửa
  vào untrusted thành tài liệu sống trong `docs/security/`.
- Bối cảnh 2026: OWASP LLM01 vẫn #1; Unit 42 ghi nhận indirect injection quy
  mô lớn đầu tiên ngoài đời thật (03/2026).

### 5c. Prompt escalation đa lượt
- Kỹ thuật Crescendo/Echo Chamber/Tempest: leo thang dần qua 5–10 lượt, ASR
  56–83% trên model lớn. **45 case adversarial hiện tại toàn 1 lượt — lỗ hổng
  test lớn nhất.**
- Kịch bản thật cho FIN-05: dẫn dắt nhiều lượt để moi thông tin bên thứ ba
  hoặc ép hứa hoàn tiền; leo thang cảm xúc giả.
- Phòng thủ: guardrail nhìn CẢ HỘI THOẠI + đếm tín hiệu tích luỹ theo
  `thread_id` (Redis) — **dùng chung hạ tầng với ES-xx ở 5a, thiết kế 1 lần**.
- Việc cần: `eval/adversarial_multiturn_set.jsonl` (bảo mật đặc tả → tester
  viết, đúng nguyên tắc không đọc src/).

## 6. Lộ trình hợp nhất (SAU demo 14/08)

- **Đợt 0** (không đổi contract): refresh project-knowledge · lưu báo cáo bảo
  mật vào docs/security/ · phân loại 29/40 (QA) · truy latency +55% (coder) ·
  load test 150 · rate-limit request_human_handoff · chạy 5 kịch bản tấn công
  + replay/OTP-consume có bằng chứng · Tier OpenAI + DPA (PO thật).
- **Đợt 1** (mỗi mục 1 ADR, quy trình 7 bước): G2 maker–checker + consume OTP
  (nhỏ nhất, làm trước) → G1 trục SLA + executed/reconciled → G3 audit_logs
  append-only.
- **Đợt 2**: spotlighting + lọc đầu ra · bộ test đa lượt · tín hiệu ES-xx ·
  retention/GDPR · runbook DORA · tài liệu AI Act.
- **Đợt 3**: heldout set (MỘT lần) · evidence SOC 2 · ngưỡng chất lượng chính thức.

Lời giải cho 4 câu hỏi mở trong contracts (từ chuẩn EU/US, không cần chờ
chuyên gia ví): CSKH cấp 2 tự duyệt → KHÔNG (khớp ADR-002) · supervisor tách
khỏi điều tra → CÓ (G2) · state executed + đối soát → CẦN (G1) ·
search_policy không OTP → chấp nhận được.

## 7. Chờ PO thật quyết

1. Ngưỡng chất lượng mục tiêu (đề xuất ≤2% bịa trên golden set, chốt sau khi
   làm sạch bộ chấm).
2. Duyệt nguyên tắc ADR maker–checker (chuẩn ngành + bảo mật cùng khuyến nghị CÓ).
3. Lịch tín hiệu cảm xúc: đề xuất sau load test, trước demo lớn kế tiếp.
4. Nâng Tier OpenAI + ký DPA (không ai làm thay được).
