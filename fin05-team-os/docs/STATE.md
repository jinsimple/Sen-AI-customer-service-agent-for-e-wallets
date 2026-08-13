# Trạng thái hiện tại

Cập nhật: 2026-08-13 · Phiên vừa rồi làm bởi: (khởi tạo Team-OS)

> File này được ghi đè mỗi cuối phiên bằng `/wrapup`. Giữ **dưới 60 dòng** — cắt phần cũ
> không còn liên quan. Nếu nó phình lên, agent sẽ bắt đầu lơ nó, và bạn mất lớp chống mất
> ngữ cảnh quan trọng nhất.
>
> Lịch sử quyết định không nằm ở đây — nằm ở `docs/DECISIONS.md`.

## Vừa xong
- Khởi tạo Team-OS: 6 agent, 5 slash command, lớp contract, script phát hiện lệch, test bất biến

## Đang dở — chi tiết đủ để phiên sau tiếp được ngay
- *(chưa có)*

## Chặn / chờ
- 7 câu hỏi mở cho chuyên gia ví điện tử (PRD §8) — chờ buổi trao đổi với ZaloPay.
  Ưu tiên cao nhất: ngưỡng thật của FS-01…FS-12, và số tầng thẩm quyền thật.

## Cảnh báo còn tồn
- Contract stale: không có
- Test bất biến: 13 pass / 4 skip (skip vì `src/` chưa tồn tại — sẽ tự bật khi có code)
- `contracts/fraud-signals.yaml` và `contracts/api.openapi.yaml` **chưa được tạo** —
  cần tech-lead sinh từ PRD §5 và từ API hiện có

## Việc kế tiếp đề xuất
1. Ghi ADR hồi tố cho các quyết định trong PRD §4, điền ngày thật — agent: `po`
   *(làm sớm: đây là thứ chặn agent tương lai "tối ưu" ngược lại các quyết định đã cân nhắc kỹ)*
2. Sinh `contracts/fraud-signals.yaml` từ PRD §5 (12 tín hiệu, tầng A/B, ngưỡng + mục
   `open_questions` cho ngưỡng chưa xác nhận) — agent: `tech-lead`
3. Sinh `contracts/api.openapi.yaml` từ code API sprint 2 hiện có — agent: `tech-lead`
4. Viết testcase cho US chạm tiền, từ contract, mù code — agent: `tester`

## Sau demo (không làm bây giờ)
- `contracts/tone-of-voice.yaml` — contract hoá giọng văn xoa dịu (là một trong ba trụ định vị
  cạnh tranh, nhưng hiện chưa có cơ chế kiểm nào)
- Mô phỏng ngân hàng đối tác trả lời sai/mâu thuẫn (PRD §8.7)
