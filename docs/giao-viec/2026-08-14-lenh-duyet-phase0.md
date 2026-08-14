# LỆNH DUYỆT PHASE 0 + PHÂN VIỆC TIẾP — PO, 14/08/2026

> Dán file này vào cả 3 tab (coder · tester · security). Mỗi vai đọc mục chung
> + mục của mình. Căn cứ: `docs/giao-viec/2026-08-14-po-review-goi-phase0.md`
> (đã tick DUYỆT).

## Chung — PO thật đã DUYỆT gói Phase 0, với 2 điều chỉnh

1. Bất biến mới đánh số **INV-14** (INV-13 đã bị `agent-tools.yaml` chiếm).
2. Ghi chú tự do theo **phương án TM-03 của security** (thay điều kiện (a)
   phiếu gốc): được phép trong hệ thống (scrub lúc ghi · ≤500 ký tự · chỉ
   route staff) · **không bao giờ xuất ra file ứng viên, kể cả đã scrub** —
   export chỉ mang enum · người duyệt đọc trong hệ thống rồi viết lại case
   bằng lời mình + dữ liệu seed ("cấm nguyên văn") · bắt buộc với `khac`.

Các phán quyết khác giữ nguyên như phiếu: taxonomy 7 giá trị + `la_tin_hieu_hoc`
· ranh giới thieu_can_cu/need_more_info ghi vào contract + UI gợi ý · backfill
1 dòng cũ → `khac` · ADR-016/017/018/019 commit cùng đợt.

**Kỷ luật nhánh:** mọi commit đợt này vào `dev/learning-loop`. Checkout đang ở
`main` cho demo tối 14/08 — vai nào cần chuyển nhánh phải báo PO trước, chuyển
xong việc TRẢ VỀ main cho tới khi demo xong. Sau demo, checkout chuyển hẳn
sang dev.

## Coder (tech-lead)

1. **Ngay, không đụng contract:** fix CASE-110 (IntegrityError FK khi tạo
   ticket "cần tra thủ công" với trans_id không tồn tại — chi tiết ở
   `eval/results/trige_29_case_20260814.md`) · CASE-004 (agent tự chọn 1/2
   candidate — vi phạm ràng buộc cứng 3) · regression CASE-019/082/083/101.
2. **Phase 0 thực thi:** sửa INV-14 trong diff → áp
   `contracts/resolution-state-machine.yaml` → ghi ADR-016/017/018/019 vào
   `docs/DECISIONS.md` → `check_contracts.py --update` → bump
   `CONTRACT_VERSION` → báo tester.
3. **Phase 1 code** theo brief cũ (`2026-08-14-learning-loop-tech-lead.md`),
   phần ghi chú tự do làm theo điều chỉnh TM-03 ở trên.
4. **Sau demo tối nay:** sửa `gen_dataset.py` cho 4 ô `from_bank` (ví khách
   phải là một bên giao dịch) + reseed gộp với dọn dữ liệu M-04. PHỐI HỢP
   tester dựng lại bộ case demo sau reseed.

## Tester (QA/QC)

1. Tiếp tục nhiệm vụ 3 (`eval/CANDIDATE-REVIEW.md`) — tích hợp checklist
   chống poisoning security đã nộp (`docs/security/threat-model-learning-loop.md`),
   gồm luật "cấm nguyên văn" + "export chỉ mang enum".
2. Khi coder báo contract mới đã chốt → nhiệm vụ 2 (test từ đặc tả: INV-14,
   CHECK br11, ranh giới thieu_can_cu, authz trường audit).
3. **Nhóm B2 (4 case processing) — nhãn mới theo phán quyết PO:** hành vi đúng
   là *thông báo trạng thái + mốc thời gian dự kiến từ dữ liệu + ĐỀ NGHỊ tạo
   hồ sơ, khách quyết*. Forbidden: từ chối thẳng ("chưa cần hồ sơ") VÀ tạo
   ticket vô điều kiện. Sửa nhãn 4 case theo đó.
4. Commit 2 file eval đang untracked (`trige_29_case_20260814.md`,
   `quality_run_20260814_041244_raw.json`) lên `dev/learning-loop` ở phiên tới.

## Security

1. Threat model + review EU/US đã nhận, chất lượng tốt — TM-03 được PO chọn
   làm phương án chính thức cho ghi chú tự do.
2. Việc tiếp: nhiệm vụ 3 trong brief cũ — rà bản contract + ADR coder áp
   THẬT (sau bước 2 của coder) so với dự thảo đã trình: trường mới không lộ
   route customer · reject không thêm OTP · nhắc coder gộp fix "OTP duyệt
   không bị consume" nếu tiện trong cùng migration.
3. Nhắc lịch: xoay `LANGCHAIN_API_KEY` ngay sau demo tối nay (đã lộ trong log
   phiên QA 13/08) — soạn 3 dòng hướng dẫn cho PO thật làm.
