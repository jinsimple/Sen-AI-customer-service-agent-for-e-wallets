# Gate G2 — Hồ sơ nộp MVP · Đội T226 (FIN-05)

> **Hạn:** 23:59 ngày 16/08/2026 · **Nộp bằng:** `/gate submit gate_key:G2 link:<link repo hoặc file này>`
> **PO & thực hiện:** Đào Ngọc Bích (MSV 2A202601745) · AI 20K Build Phase, Cohort 3 (Vingroup × VinUni)
> **Sản phẩm:** AI Agent CSKH ví điện tử — điều tra khiếu nại giao dịch qua tool, **không bao giờ tự quyết định**.
> **Live:** https://app.adaptivealgo.uk *(home-server + Cloudflare Tunnel — hiện mở cho đội & mentor)*

Thư mục này là **mục lục hồ sơ nộp**. Mỗi mục trỏ tới file gốc trong repo — cố ý **không sao chép nội dung**
để hồ sơ không bao giờ lệch với sản phẩm thật.

---

## 1. MVP Demo — video 3 phút, user flow end-to-end

- **Trạng thái:** ⏳ PO tự quay
- **Kịch bản quay sẵn (8 màn, có cả bẫy hay gặp):** [`docs/giao-viec/2026-08-15-kich-ban-demo-mvp.md`](../docs/giao-viec/2026-08-15-kich-ban-demo-mvp.md)
- **Bản đọc dễ (HTML):** https://claude.ai/code/artifact/53c01e06-6f9a-4f10-87ae-b642c6538ce1
- **Tài khoản demo** (mật khẩu chung `Demo@123`): khách `0974000145` · CSKH `0353000201` ·
  Sếp duyệt `0905000205` · Đối tác ví `0900000001`
  → Hai vai cùng máy: vai khách cửa sổ thường, vai nhân viên **cửa sổ ẩn danh**.

**Luồng end-to-end nên quay:** khách chat khiếu nại → agent gọi tool điều tra, tìm đúng giao dịch giữa
nhiều giao dịch cùng số tiền → tạo ticket → CSKH tiếp nhận, xem timeline điều tra (**không có nút duyệt**)
→ Sếp mở hồ sơ, đọc căn cứ, duyệt bằng OTP step-up → khách nhận kết quả.

## 2. Architecture diagram — components + data flow

- ✅ **Sơ đồ rút gọn (deliverable):** [`docs/architecture_diagram.md`](../docs/architecture_diagram.md)
- ✅ **Bản đầy đủ + data flow + bảng quyết định kiến trúc:** [`ARCHITECTURE.md`](../ARCHITECTURE.md)

Mermaid render thẳng trên GitHub. Một câu tóm tắt: khách gõ → che PII → agent (LangGraph + GPT-4o-mini,
5 tool, gọi **dưới danh nghĩa customer**) → guardrails tất định (spotlighting · O1-O4 · origin-rule) →
khách; **tiền chỉ đi khi Sếp duyệt** — ràng buộc người-tạo-≠-người-duyệt nằm ở tầng database.

## 3. Repo có ≥ 10 PR merged

- ✅ **7 PR đã merge** (#1–#7)
- 🔗 **3 PR đang mở, merge theo đúng thứ tự này:**
  1. [PR #8 — RAG đòn 4 + kho sạch + bản đồ phủ](https://github.com/AI20K-Build-Phase-Cohort-3/P-226/pull/8)
  2. [PR #9 — F-LOG-3 log có cấu trúc + T3 cắt 24% token](https://github.com/AI20K-Build-Phase-Cohort-3/P-226/pull/9)
  3. [PR #10 — ADR-026 + benchmark v0.4 + bộ lệnh đo](https://github.com/AI20K-Build-Phase-Cohort-3/P-226/pull/10)

→ Sau khi merge đủ: **10 PR merged**, và `main` (nhánh production đang deploy) ngang với nhánh phát triển.

## 4. README.md — setup, env vars, sample queries

- ✅ [`README.md`](../README.md) — gồm: chạy bằng Docker (đủ stack) hoặc dev hot-reload · bảng **biến môi
  trường** kèm cách sinh secret và cảnh báo mất `FIELD_ENCRYPTION_KEY` = mất dữ liệu vĩnh viễn · **câu hỏi
  mẫu đã kiểm bằng chạy thật** · tài khoản demo · lệnh kiểm thử · cấu trúc repo.

## 5. Eval evidences — ≥ 5 test case manual, output thực tế

- ✅ [`eval/EVAL-EVIDENCE.md`](../eval/EVAL-EVIDENCE.md) — **7 ca** (vượt yêu cầu 5), output **nguyên văn từ
  hệ thống chạy thật**, có dán nhãn môi trường đo (commit, hạ tầng, dữ liệu, tài khoản).
  Trong đó **2 ca âm bản** — cố tình hỏi thứ hệ thống *không* có, để chứng minh agent nói "không tìm thấy"
  chứ không bịa số.
- Bổ sung, không bắt buộc nhưng nên xem:
  [`docs/giao-viec/2026-08-16-benchmark-spec-va-v0.md`](../docs/giao-viec/2026-08-16-benchmark-spec-va-v0.md)
  — bộ benchmark tự dựng (5 trục, trọng số), **v0.4 = 87,7% điểm đo được**, ghi kèm 2 finding còn mở
  thay vì làm tròn thành điểm đẹp.

---

## Điểm nên nhấn khi trình bày

| | |
|---|---|
| **Ràng buộc cứng ép bằng test** | 5 ràng buộc (HITL tuyệt đối · AI không vượt cấp · cấm bịa số · OTP phiên · gắn cờ ≠ khoá ví) mã hoá thành `tests/test_invariants.py` — **23 test introspect app đang chạy thật** (đọc route, moi guard từ closure, đọc CHECK constraint qua AST). Đỏ = build hỏng. |
| **Contracts là nguồn sự thật** | Cấu trúc hệ thống sống trong `contracts/`, không sống trong code. Thêm route/đổi guard/đổi tên tool mà quên cập nhật contract → đỏ ngay. |
| **26 ADR có lý do bác phương án khác** | [`docs/DECISIONS.md`](../docs/DECISIONS.md) — mới nhất **ADR-026**: kho chính sách chỉ phục vụ tài liệu **đã duyệt**, sinh ra từ một sự cố thật trong ngày. |
| **Kỷ luật đo lường** | Mỗi con số kèm nhãn hệ thống; thước đo bị bắt lỗi 3 lần trong ngày và **cả 3 lần đều do chính người dùng thước phát hiện**; bản vá không có số lợi ích thì **revert dù vô hại**. |
