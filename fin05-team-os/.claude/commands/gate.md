---
description: Kiểm tra cổng vào trước khi giao việc cho một agent — chặn rác đi vào từ đầu
argument-hint: <tên agent: po|ba|tech-lead|tester|security> [mô tả việc]
allowed-tools: Read, Bash, Grep, Glob
---

Kiểm tra cổng vào cho agent: **$1**
Việc dự định giao: $2

Đọc file `.claude/agents/$1.md`, lấy phần "Cổng vào" của agent đó, rồi kiểm tra từng mục
với tình trạng repo hiện tại. Với mỗi mục, trả lời ĐẠT / KHÔNG ĐẠT / KHÔNG XÁC ĐỊNH kèm bằng chứng
(tên file, dòng, hoặc kết quả lệnh).

Ngoài ra luôn kiểm thêm ba mục chung:
- Contract liên quan có stale không (`python scripts/check_contracts.py`)?
- Việc này có chạm ràng buộc cứng nào trong `CLAUDE.md §2` không?
- Việc này có nằm trong vùng quyền ghi của agent đó không (`CLAUDE.md §4`)?

Kết luận:

```
## Kết quả cổng vào: ĐẠT / KHÔNG ĐẠT
## Thiếu gì (nếu không đạt)
- <mục> → cần làm gì trước, giao cho agent nào
## Nếu đạt: câu lệnh nên dùng để giao việc
```

**Không tự chạy agent đó.** Chỉ kiểm và báo cáo.
