# GIAO VIỆC — tech-lead — Learning loop, nhánh `dev/learning-loop`

> PO giao 14/08. Dán nguyên văn vào phiên Claude tech-lead.
> Kế hoạch tổng (đọc TRƯỚC): `docs/giao-viec/2026-08-14-ke-hoach-learning-loop.md`

---

Bạn là **tech-lead** của FIN-05. Đánh giá "có trí nhớ, chưa có học" của bạn đã
được PO duyệt thành kế hoạch 3 phase — bạn làm đúng thứ tự dưới đây trên nhánh
**`dev/learning-loop`** (đã tạo sẵn từ `f2d4785`).

**TUYỆT ĐỐI KHÔNG commit lên `main` — main đóng băng cho demo tối 14/08.**
`git checkout dev/learning-loop` trước khi làm bất cứ gì.

**Xác nhận trước khi bắt đầu (trả lời ngắn cho PO):**
a. Vì sao phải có ADR + PO duyệt TRƯỚC khi viết migration? Quy trình 7 bước ở đâu?
b. Hai lằn ranh không vượt của đợt này (kế hoạch §4) là gì?
c. Một điểm thiếu/mâu thuẫn thông tin (bắt buộc ≥1).

## NHIỆM VỤ 1 — Phase 0: Dự thảo ADR + diff contract (làm ngay, KHÔNG code)

1. Soạn dự thảo ADR "Thu nhãn phán đoán chuyên gia tại luồng reject" theo mẫu
   cuối `docs/DECISIONS.md` — bắt buộc có mục "Lý do BÁC BỎ phương án khác"
   (tối thiểu: vì sao không ghi log tự do không cấu trúc, vì sao không để AI
   tự gán lý do).
2. Soạn diff đề xuất cho `contracts/resolution-state-machine.yaml`: transition
   `pending_approval → rejected` thêm `yeu_cau_them` ghi lý do; taxonomy enum
   `sai_so_lieu · sai_phan_loai · thieu_can_cu · sai_chinh_sach · khac`.
3. Soạn luôn dự thảo **ADR-018** (nguyên tắc "quyết định người nhận LÚC GIAO
   TIN" của live-chat — nợ từ 13/08, kèm lý do bác bỏ mô hình đăng-ký-trước).
4. **DỪNG. Trình PO cả gói. Chỉ code sau khi PO duyệt** →
   `python scripts/check_contracts.py --update` + bump `CONTRACT_VERSION`.

## NHIỆM VỤ 2 — Phase 1: Code (sau khi ADR được duyệt)

1. Migration: `resolutions` thêm `reject_reason` (enum, NOT NULL khi
   status='rejected' — cân nhắc CHECK constraint cùng triết lý BR-10),
   `rejected_by` FK users, `rejected_at`.
2. `POST /resolutions/{id}/reject` nhận `reason` bắt buộc (+ `note` tự do nếu
   PO chốt cho phép — qua scrub trước khi lưu); ghi đủ 3 trường.
3. **Vá QA-02**: `ticket.hitl_status` chuyển `approved`/`rejected` đúng lúc
   resolution đổi trạng thái (transaction cùng commit, không job nền).
4. API chi tiết ticket trả `approved_by/approved_at/rejected_by/rejected_at/
   reject_reason` cho cskh/supervisor (KHÔNG cho customer — kiểm authz).
   Đóng luôn M-02. UI: dropdown lý do ở màn reject của sếp.
5. Chạy: 19/19 bất biến · full suite · check_contracts sạch · test mới của
   tester (phối hợp — tester viết từ contract, bạn không sửa test của họ).

## NHIỆM VỤ 3 — Phase 2 (chỉ sau khi Phase 1 xong và tester có quy trình duyệt)

Exporter: resolution rejected + phiên CSAT ≤2 → `eval/candidates/*.jsonl`,
**bắt buộc qua scrub PII tại điểm export** (dùng pipeline pii.py sẵn có);
nối CSAT vào `/reports/summary`. KHÔNG có đường nào tự động ghi vào
`eval/golden_set.jsonl` — người duyệt (tester) là cổng duy nhất.

## Ràng buộc
- Vùng ghi: `src/`, `frontend/src/`, `migrations/`; `contracts/` CHỈ sau khi
  PO duyệt ADR. Không chạm `eval/golden_set.jsonl` (vùng tester).
- KHÔNG fine-tuning, KHÔNG nới hành vi `multiple_matches`/hỏi-lại (kế hoạch §4).
- Kéo `git pull --rebase` đầu mỗi phiên — tester/security cùng commit nhánh này.

## BÁO CÁO: theo phase — Phase 0 nộp gói ADR+diff rồi DỪNG chờ duyệt;
Phase 1/2 nộp kết quả test thật + output lệnh.
