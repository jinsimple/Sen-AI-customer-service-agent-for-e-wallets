# GIAO VIỆC — security — Learning loop, nhánh `dev/learning-loop`

> PO giao 14/08. Dán nguyên văn vào phiên Claude security.
> Kế hoạch tổng (đọc TRƯỚC): `docs/giao-viec/2026-08-14-ke-hoach-learning-loop.md`
> Báo cáo EU/US trước đó của bạn đã được PO kiểm chứng — 2 hiệu chỉnh ghi tại
> `docs/PO-TONG-KET-2026-08-13.md` §4 (replay approve KHÔNG tạo bút toán kép
> nhờ status guard, nhưng OTP không bị consume — tồn dư thật; và số liệu G7
> đã cũ, gate mới là 0% bịa thật theo thước `2d9a709`).

---

Bạn là vai **security** của FIN-05, làm trên nhánh **`dev/learning-loop`**
(`git checkout dev/learning-loop`; main đóng băng cho demo tối 14/08).
Vùng ghi của bạn: **`docs/security/`** (chưa tồn tại — phiên này bạn tạo,
và đây là báo cáo đầu tiên của vai security vào đúng vùng ghi của mình).

**Xác nhận trước khi bắt đầu (trả lời ngắn cho PO):**
a. Vì sao vòng lặp học là bề mặt tấn công MỚI, khác các bề mặt đã rà?
b. Mốc kích hoạt nào của ADR-011 mà Phase 2 (export case từ hội thoại thật)
   có nguy cơ chạm khi có 150 người dùng thật?
c. Một điểm thiếu/mâu thuẫn (bắt buộc ≥1).

## NHIỆM VỤ 1 — Lưu báo cáo đánh giá EU/US vào đúng vùng (nhanh)

Lưu báo cáo bạn đã viết (PO đang giữ bản text) thành
`docs/security/review-2026-08-13.md`, KÈM 2 hiệu chỉnh của PO nêu ở đầu brief
này — báo cáo lưu kho phải là bản đã đối chiếu code, không phải bản gốc.

## NHIỆM VỤ 2 — Threat model vòng lặp học (chính — trước khi Phase 2 chạy)

Viết `docs/security/threat-model-learning-loop.md`:
1. **Data poisoning qua hội thoại dàn dựng**: kẻ tấn công chat theo kịch bản
   để tạo case bị reject/CSAT thấp có nội dung do hắn kiểm soát → case đó
   thành ứng viên vào eval/few-shot → uốn hành vi agent về sau. Phân tích
   đường đi cụ thể trên thiết kế Phase 2 (exporter → candidates → duyệt tay).
2. **CSAT bombing**: chấm 1 sao hàng loạt để đẩy hội thoại chọn lọc vào phễu.
   Đề xuất ngưỡng/lọc (vd tối thiểu N tin nhắn, loại phiên quá ngắn).
3. **Nhãn từ chối làm kênh rò**: `reject_reason` + ghi chú tự do của sếp có
   thể chứa PII khách hoặc thông tin nội bộ → nếu case ứng viên mang theo nó
   vào git thì rò vĩnh viễn. Khuyến nghị cho PO chốt: enum thuần hay
   enum + ghi chú tự do có scrub? (PO đang chờ ý kiến bạn — kế hoạch §5.3)
4. **Đầu ra bắt buộc**: checklist chống poisoning cho người duyệt case (giao
   tester tích hợp vào `eval/CANDIDATE-REVIEW.md`) + danh sách kiểm scrub tại
   điểm export (giao coder làm test đối kháng).

## NHIỆM VỤ 3 — Rà thiết kế Phase 1 (khi coder trình gói ADR)

Rà dự thảo ADR + diff contract của coder trước khi PO duyệt:
- Trường mới không lộ qua route customer (least-privilege như INV-11).
- Reject vẫn không cần OTP (đúng contract hiện hành) — xác nhận không ai
  "tiện tay" thêm OTP làm sếp ngại từ chối (từ chối khó hơn duyệt là sai lệch
  khuyến khích nguy hiểm).
- Nhân tiện: nhắc lại tồn dư "OTP duyệt không bị consume" (PO đã xác minh) —
  đề xuất coder sửa 2 dòng trong cùng migration đợt này nếu tiện, kèm test.

## Ràng buộc
- Chỉ ghi `docs/security/`. Không sửa code/test/eval — phát hiện gì thì đặc
  tả cho vai khác làm.
- Kéo `git pull --rebase` đầu phiên.

## BÁO CÁO: nhiệm vụ 1 xác nhận đường dẫn file; nhiệm vụ 2 nộp threat model +
2 checklist bàn giao; nhiệm vụ 3 nộp ý kiến rà trước khi PO duyệt ADR.
