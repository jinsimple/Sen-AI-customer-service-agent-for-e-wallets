# GIAO VIỆC — security — Rà chính thức Phase 0 + Phase 1 đã áp thật

> PO giao tối 14/08. Dán nguyên văn vào phiên Claude security.
> Nhánh làm việc: `dev/learning-loop` (git pull --rebase trước khi bắt đầu).
> Vùng ghi của bạn: CHỈ `docs/security/`.

---

Bạn là vai **security** của FIN-05. Gói ADR + contract mà nhiệm vụ 3 của bạn
chờ ("khi coder trình gói, tôi rà chính thức") **đã áp thật vào repo**:

- **Phase 0 — commit `8fe3bed`:** contract `resolution-state-machine.yaml`
  v2.0.0 → v2.1.0 (taxonomy 7 giá trị + cờ `la_tin_hieu_hoc` · ranh giới
  thieu_can_cu ↔ need_more_info · `dan_xuat` cho hitl_status · INV-14) +
  ADR-016→019 ghi vào DECISIONS.md (+148/-0).
- **Phase 1 — commit `02d2b2a`:** migration 3 cột reject + CHECK
  `ck_resolutions_rejected_requires_reason_br11` + backfill 3 dòng cũ →
  `khac` · route reject nhận `reason` bắt buộc + guard chỉ nhận
  `pending_approval` · vá QA-02 (hitl_status cùng transaction) · API ticket
  trả trường audit cho staff (M-02).
- **Commit bổ sung đang làm (coder):** SEC-B (guard approve bỏ `draft`) +
  consume OTP sau duyệt + cột `resolutions.created_by` (nullable, propose
  luôn ghi) — đúng 3 điều bạn đề nghị "gộp vào cùng migration".

PO đã review lớp 2 cả hai commit (đối chiếu bản duyệt, chạy lại gate).
Việc của bạn là **lớp rà chuyên môn bảo mật** — góc nhìn PO không thay được.

**Xác nhận trước khi bắt đầu (trả lời ngắn):**
a. Sign-off của bạn đang chặn việc gì của coder?
b. Trường dữ liệu mới nào của đợt này có nguy cơ đi vào context LLM, và qua
   đường nào?
c. Một điểm thiếu/mâu thuẫn trong brief (bắt buộc ≥1).

## NHIỆM VỤ 1 — Rà bản áp thật (chính)

Đọc diff thật của `8fe3bed` và `02d2b2a` (+ commit bổ sung nếu đã vào lúc bạn
làm), đối chiếu với dự thảo bạn đã rà sơ bộ (mục 7 threat model) và phiếu
duyệt PO (`docs/giao-viec/2026-08-14-po-review-goi-phase0.md`). Trọng tâm:

1. **Trường mới không rò qua đường customer/LLM** — đây là mục QUAN TRỌNG
   NHẤT, đúng cảnh báo của chính bạn: kiểm bằng chạy thật (không chỉ đọc
   code) rằng `reject_reason`/`rejected_by`/`rejected_at`/`created_by` KHÔNG
   xuất hiện trong: (a) response route nào mở cho customer, (b) kết quả tool
   nào agent gọi được (`get_customer_history`, `lookup_transaction` —
   đường tool → context LLM → khách), (c) tin nhắn live-chat khách thấy.
2. **Reject vẫn không-OTP** (nguyên tắc "hành động an toàn phải rẻ hơn hành
   động nguy hiểm" — xác nhận không ai thêm bước thừa).
3. **BR-11 hiệu lực**: tester đã có test ghi-thẳng-DB đòi IntegrityError
   (`test_check_constraints_hitl.py`) — bạn đối chiếu biểu thức CHECK trong
   migration với contract, tìm kẽ hở logic (OR/AND, NULL semantics: cả 3
   trường có bị ép đủ khi status='rejected' không, và NULL ở cột nào lách
   được không).
4. **Backfill 3 dòng cũ** → `khac` kèm ghi chú nguồn gốc trong rationale —
   xác nhận dữ liệu kiểm toán không mập mờ và 3 dòng đó KHÔNG mang cờ
   `la_tin_hieu_hoc=true` (không được lọt vào phễu học Phase 2).
5. **ADR-016→019** đọc dưới lăng kính bảo mật: có ADR nào mô tả hành vi mà
   code thật chưa làm (nợ ẩn), hoặc ngược lại.

## NHIỆM VỤ 2 — Sign-off TM-03 cho field GHI CHÚ TỰ DO (đang chặn coder)

Coder chưa code field `note` — chờ đúng chữ ký của bạn. Ra phán quyết
ĐẠT/KHÔNG-ĐẠT cho thiết kế theo 5 điều kiện TM-03 đã được PO chốt:
scrub-trước-khi-ghi-DB · ≤500 ký tự · chỉ đọc qua route staff · KHÔNG BAO
GIỜ vào context agent · KHÔNG BAO GIỜ export (git chỉ thấy enum). Nếu ĐẠT
kèm điều kiện kiểm thử: đặc tả các test đối kháng bạn muốn có (tối thiểu:
note chứa SĐT/CCCD phải bị scrub trong DB; note không xuất hiện ở bất kỳ
tool result nào; note không có trong file export) — giao danh sách cho
tester viết, bạn không viết test.

## NHIỆM VỤ 3 — Kiểm chuỗi bàn giao checklist của chính bạn

`eval/CANDIDATE-REVIEW.md` (tester dựng): xác nhận checklist chống poisoning
mục 5 threat model của bạn đã được tích hợp ĐỦ — đặc biệt luật CẤM NGUYÊN
VĂN và trần ứng viên/người dùng. Thiếu → ghi rõ thiếu gì, tester bổ sung.
File chưa tồn tại → ghi nhận "chưa có, chờ tester" và nêu trong báo cáo.

## Ràng buộc

- Chỉ ghi `docs/security/` (báo cáo mới: `docs/security/review-phase01-ap-that.md`).
- Phát hiện gì KHÔNG tự sửa code/test — đặc tả cho vai đúng vùng làm.
- Kết luận nào cũng kèm bằng chứng chạy thật hoặc trích diff — không suy
  luận từ mô tả của coder/PO (cả hai đã từng sai trong ngày hôm nay).

## BÁO CÁO CUỐI (gửi PO)

```
## Kết luận: ĐẠT / ĐẠT CÓ ĐIỀU KIỆN / KHÔNG ĐẠT (từng phần: Phase 0 · Phase 1 · TM-03)
## Nhiệm vụ 1: bảng 5 mục × kết quả × bằng chứng
## Nhiệm vụ 2: sign-off TM-03 + danh sách test đối kháng giao tester
## Nhiệm vụ 3: trạng thái tích hợp checklist
## Phát hiện mới (nếu có): mã F-xx tiếp theo, mức độ, giao ai
```
