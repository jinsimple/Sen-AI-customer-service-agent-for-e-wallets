---
description: Phân tích tác động — contract nào đã đổi, artifact nào giờ đã lỗi thời, ai phải làm lại gì
allowed-tools: Read, Bash, Grep, Glob
---

Phân tích tác động của các thay đổi contract gần đây.

1. Chạy `python scripts/check_contracts.py --verbose`.
2. Với mỗi contract bị đánh dấu ĐÃ ĐỔI, chạy `git diff` trên file đó (so với commit gần nhất mà
   hash được cập nhật) và tóm tắt **thay đổi ngữ nghĩa**, không phải thay đổi ký tự.
3. Với mỗi thay đổi ngữ nghĩa, lần theo hạ nguồn:
   - `docs/user-stories/` — US nào mô tả hành vi giờ đã sai?
   - `tests/` — file nào có `CONTRACT_VERSION` cũ?
   - `docs/security/` — báo cáo rà soát nào dựa trên contract cũ?
   - `src/` — có chỗ nào code vẫn theo contract cũ không?

Báo cáo:

```
## Contract đã đổi
| File | Thay đổi ngữ nghĩa | Hash cũ → mới |

## Artifact lỗi thời — cần làm lại
| Artifact | Vì sao lỗi thời | Giao cho agent | Ưu tiên |

## Không bị ảnh hưởng
(liệt kê ngắn, để khỏi kiểm lại)
```

Đây là công cụ thay thế cho việc bắt tech-lead viết file tóm tắt cho tester đọc.
Nếu báo cáo này ra kết quả rỗng trong khi contract vừa đổi, tức là hash đã bị cập nhật sớm —
báo cho Bách biết, đừng im lặng.
