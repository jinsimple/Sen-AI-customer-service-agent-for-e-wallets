---
description: Kết phiên — chốt ngữ cảnh vào repo để phiên sau không phải kể lại từ đầu
allowed-tools: Read, Write, Edit, Bash, Grep, Glob
---

Kết thúc phiên làm việc. Đây là bước chống mất ngữ cảnh — **không được bỏ qua**.

1. **Chạy kiểm tra**
   - `pytest tests/test_invariants.py -q`
   - `python scripts/check_contracts.py`
   - `git status`

2. **Ghi lại quyết định phát sinh.** Rà lại phiên này: có điều gì đã chốt mà chưa có ADR không?
   Nếu có, liệt kê ra và hỏi Bách có muốn ghi ADR ngay không. Đừng tự ghi ADR cho những thứ
   Bách chưa duyệt tường minh.

3. **Ghi đè `docs/STATE.md`** theo khuôn dưới. Giữ dưới 60 dòng — cắt phần cũ không còn liên quan.

```markdown
# Trạng thái hiện tại
Cập nhật: <YYYY-MM-DD HH:mm> · Phiên vừa rồi làm bởi agent: <tên>

## Vừa xong
- <việc> (<file bị chạm>)

## Đang dở — chi tiết đủ để phiên sau tiếp được ngay
- <việc>: đã làm tới đâu, vướng ở đâu, bước kế tiếp cụ thể là gì

## Chặn / chờ
- <việc> — chờ ai/cái gì

## Cảnh báo còn tồn
- Contract stale: <...>
- Test đỏ: <...>

## Việc kế tiếp đề xuất
1. <việc> — agent: <tên>

## Sau demo (không làm bây giờ)
- <ý tưởng bị hoãn — để khỏi quên và khỏi bị đề xuất lại>
```

4. **Cập nhật hash nếu contract đã đổi và đã được duyệt:** `python scripts/check_contracts.py --update`

5. **Commit.** Đề xuất câu commit theo dạng `<loại>(<vùng>): <việc>` kèm dòng
   `Contract đã đổi: <danh sách | không có>`. Hỏi Bách trước khi commit, không tự commit.
