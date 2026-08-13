# Trạng thái hiện tại

Cập nhật: **2026-08-13** · Phiên vừa rồi: Claude Code (cài Team-OS lớp đồng bộ)

> Ghi đè mỗi cuối phiên bằng `/wrapup`. Giữ **dưới 60 dòng** — cắt phần cũ không còn liên
> quan. File phình lên = agent bắt đầu lơ nó = mất lớp chống mất ngữ cảnh quan trọng nhất.
>
> Lịch sử quyết định KHÔNG nằm ở đây — nằm ở `docs/DECISIONS.md`.

## Vừa xong

- **Cài lớp đồng bộ Team-OS** (phiên này): `CLAUDE.md` (hiến pháp), `docs/DECISIONS.md`
  (8 ADR hồi tố), file này, `contracts/` (3 file sinh NGƯỢC từ code thật),
  `tests/test_invariants.py` (19 test introspect app đang chạy), `scripts/check_contracts.py`.
- **Đợt AUTH5** (2026-08-12, 11 commit): đăng nhập mật khẩu argon2id, JWT access 15 phút +
  refresh rotation có reuse-detection trên Redis, bỏ hẳn KBA, OTP step-up riêng cho duyệt
  resolution (PSD2 dynamic linking), rate-limit chuyển sang Redis.
- **Sửa `/agent/chat` treo 70s** → timeout 2 lớp (20s mỗi lượt gọi OpenAI, 45s cả lượt
  chat), đo lại còn ~36s.
- **Sửa 3 file Playwright hỏng âm thầm** (accessibility/login/transparency) — helper
  `login()` cục bộ chưa điền mật khẩu sau đợt AUTH5. 13/13 xanh.

## Đang dở — chi tiết đủ để phiên sau tiếp được ngay

- *(chưa có)*

## Chặn / chờ

- 7 câu hỏi mở cho chuyên gia ví điện tử (PRD §8) — chờ buổi trao đổi với ZaloPay.
  Ưu tiên: số tầng thẩm quyền thật, có tồn tại vai "CSKH cấp 2" không.
- `open_questions` trong cả 3 file `contracts/` — mỗi file cuối có mục riêng, đọc trước
  khi trao đổi với chuyên gia.

## Cảnh báo còn tồn

- Test bất biến: **19/19 xanh**, 0 skip. Đã chứng minh bắt được vi phạm thật qua 4 kịch
  bản phá có chủ đích (mở `/approve` cho cskh · thêm route lạ · đổi tên tool · gỡ CHECK
  BR-10) — cả 4 đều ĐỎ đúng chỗ.
- `contracts/` mới tạo, baseline hash đã chốt. `check_contracts.py` sạch.
- **`fin05-team-os/` (thư mục gói gốc) vẫn còn trong repo** — contract/test trong đó mô tả
  một sản phẩm KHÁC (5 tool tên tiếng Việt không tồn tại, FSM 10 state không có thật).
  Giữ lại làm tham chiếu tài liệu chiến lược, nhưng **KHÔNG chạy test trong đó** — nó
  xanh giả. Cân nhắc xoá `fin05-team-os/{contracts,tests,scripts}` để tránh nhầm lẫn.
- Chưa có `contracts/fraud-signals.yaml` và `contracts/api.openapi.yaml` — chưa cần gấp,
  fraud policy MVP chỉ dùng FS-06 (đã ghi trong `resolution-state-machine.yaml`).

## Việc kế tiếp đề xuất

1. Chạy `/standup` đầu mỗi phiên của MỌI con Claude — đây là thứ giải quyết bài toán
   phân mảnh, không phải bản thân contract.
2. Cho 3 con Claude còn lại (QA/QC · UX/UI · Tester) đọc `CLAUDE.md` §4 để biết vùng
   quyền ghi của mình. Tester đặc biệt: **không đọc `src/`**.
3. Bổ sung ADR cho các quyết định UX/UI (theme màu, wireframe) — hiện `DECISIONS.md` mới
   chỉ có quyết định backend/auth.

## Sau demo (không làm bây giờ)

- `contracts/tone-of-voice.yaml` — contract hoá giọng văn xoa dịu (một trong ba trụ định
  vị cạnh tranh, hiện chưa có cơ chế kiểm nào).
- `eval/heldout_set.jsonl` — **CHỈ CHẠY MỘT LẦN, gần cuối**. Chạy lặp rồi sửa theo kết quả
  là tự làm rò rỉ tập kiểm định.
