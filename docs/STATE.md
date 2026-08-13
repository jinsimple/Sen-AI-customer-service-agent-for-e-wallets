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
  Công cụ đồng bộ sang Claude Desktop: `scripts/export_project_knowledge.py`,
  `scripts/brief.py`, `scripts/harvest_prompt.md`.
- **Sửa BUGREPRO-001/002**: chip "Khách yêu cầu người thật (N)" và bảng ticket không cập
  nhật khi có khách mới — `tickets` chỉ fetch 1 lần lúc mount, WS `queue_update` và poll
  60s đều không chạm tới. 4 test vitest bảo vệ, đã chứng minh bắt được bug.
- **Dọn dẹp**: ghim `ruff==0.16.2` + sửa 113 lỗi lint; gỡ `langchain-chroma` (không dùng);
  xoá `fin05-team-os/` (test xanh giả, đã archive ở commit `933ecf7` để khôi phục được).
- **Đợt AUTH5** (2026-08-12, 11 commit): mật khẩu argon2id, JWT 15 phút + refresh
  rotation/reuse-detection trên Redis, bỏ KBA, OTP step-up duyệt resolution. Xem ADR-006/007/008.
- **Sửa `/agent/chat` treo 70s** → timeout 2 lớp, đo lại còn ~36s.

## Đang dở — chi tiết đủ để phiên sau tiếp được ngay

- *(chưa có)*

## Chặn / chờ

- 7 câu hỏi mở cho chuyên gia ví điện tử (PRD §8) + mục `open_questions` cuối cả 3 file
  `contracts/` — chờ buổi trao đổi với ZaloPay. Ưu tiên: số tầng thẩm quyền thật.

## Cảnh báo còn tồn

- Test bất biến: **19/19 xanh**, 0 skip. Đã chứng minh bắt được vi phạm thật qua 5 kịch
  bản phá có chủ đích (mở `/approve` cho cskh · thêm route lạ · đổi tên tool · gỡ CHECK
  BR-10 · sửa contract) — cả 5 đều ĐỎ đúng chỗ.
- `contracts/` baseline hash đã chốt. `check_contracts.py` sạch (exit 0).
- Full suite: **294 backend + 34 frontend** xanh. `ruff` sạch.
- **BUGREPRO-001 phần "kể cả sau F5" CHƯA XÁC NHẬN.** Đã sửa nguyên nhân chính (WS
  `queue_update` không nạp lại `tickets`), nhưng phần F5-cũng-fail không tái hiện được
  từ code — cache BFF đã `no-store`. **Cần QA/QC test tay lại trên bản mới để chốt.**
- Chưa có `contracts/fraud-signals.yaml` và `contracts/api.openapi.yaml` — chưa cần gấp,
  fraud policy MVP chỉ dùng FS-06 (đã ghi trong `resolution-state-machine.yaml`).
- QUEUEARCH-001..008 (tách hàng đợi live-chat khỏi hàng chờ ticket) — **chưa làm**, đang
  chờ quyết định của PO. Đây là thay đổi kiến trúc UI, không phải bug.

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
