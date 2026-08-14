# GIAO VIỆC — tester (QA/QC) — Learning loop, nhánh `dev/learning-loop`

> PO giao 14/08. Dán nguyên văn vào phiên Claude tester.
> Kế hoạch tổng (đọc TRƯỚC): `docs/giao-viec/2026-08-14-ke-hoach-learning-loop.md`

---

Bạn là **tester** của FIN-05, làm trên nhánh **`dev/learning-loop`**
(`git checkout dev/learning-loop`, KHÔNG commit lên main — main đóng băng cho
demo tối 14/08). **KHÔNG đọc `src/`** — làm từ contracts/, docs/, eval/.

**Xác nhận trước khi bắt đầu (trả lời ngắn cho PO):**
a. Vì sao trong vòng lặp học, NGƯỜI DUYỆT case ứng viên là phòng tuyến chống
   data poisoning? (kế hoạch §1 mục bổ sung)
b. Điều kiện nào mở khoá Phase 3, và vì sao việc số 1 của bạn quyết định nó?
c. Một điểm thiếu/mâu thuẫn (bắt buộc ≥1).

## NHIỆM VỤ 1 — Phân loại 29/40 vi phạm checks (LÀM NGAY — chặn Phase 3)

Nợ từ 13/08, giờ là đường găng của cả kế hoạch:
1. Đọc `eval/results/quality_run_20260813_150352_raw_rescored.json` — với
   TỪNG case trong 29 case vi phạm, phân loại: (a) lỗi scorer/expected-pattern
   (vd PII scrub che đúng nhưng pattern cũ đòi nguyên văn), (b) regression
   chất lượng thật, (c) không rõ — ghi lại để chạy lại tay.
2. Nhóm (a): sửa pattern trong bộ case (vùng eval/ của bạn), ghi lại từng sửa.
   Nhóm (b): mô tả hành vi sai cụ thể — KHÔNG sửa gì ngoài eval/, báo PO.
3. Đầu ra: `eval/results/trige_29_case_20260814.md` — bảng case × phân loại ×
   bằng chứng, và CON SỐ SẠCH cuối cùng (bao nhiêu regression thật/40).

## NHIỆM VỤ 2 — Phase 1: Test từ contract mới (sau khi PO duyệt ADR)

Đọc contract `resolution-state-machine.yaml` bản MỚI (sau khi coder cập nhật
theo ADR được duyệt) và viết test từ đặc tả:
- Reject ghi đủ `reject_reason/rejected_by/rejected_at`; thiếu lý do → bị chặn.
- `hitl_status` chuyển đúng cả nhánh approve lẫn reject (đây là QA-02 cũ của
  bạn — giờ thành test hồi quy thật).
- API ticket trả trường audit cho cskh/supervisor; customer KHÔNG thấy.

## NHIỆM VỤ 3 — Phase 2: Quy trình duyệt case ứng viên

Thiết kế và viết thành `eval/CANDIDATE-REVIEW.md`:
- Format case ứng viên (khớp schema golden_set: `expected` + `forbidden`).
- Tiêu chí NHẬN (lỗi tái hiện được, nhãn rõ, đã scrub PII) và LOẠI (hội thoại
  bất thường/nghi dàn dựng, trùng case có sẵn, CSAT thấp không rõ nguyên nhân).
- Tích hợp checklist chống poisoning mà vai security sẽ giao cho bạn.
- Nhật ký duyệt: ai nhận case nào, ngày, lý do — append-only.
Nguyên tắc: KHÔNG có case nào vào `golden_set.jsonl` mà không qua tay bạn.

## Ràng buộc
- Vùng ghi: `tests/`, `frontend/e2e/`, `eval/`. Kéo `git pull --rebase` đầu phiên.
- Báo cáo trung thực — nhóm (b) regression thật là finding cho PO, không phải
  việc của bạn phải "làm cho xanh".

## BÁO CÁO: nhiệm vụ 1 nộp ngay khi xong (mở khoá Phase 3);
nhiệm vụ 2–3 theo phase, kèm output chạy thật.
