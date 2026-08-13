---
description: Mở đầu phiên làm việc — nạp lại ngữ cảnh, phát hiện artifact stale, đề xuất việc hôm nay
allowed-tools: Read, Bash, Grep, Glob
---

Thực hiện standup đầu phiên. Làm đúng 5 bước, không bỏ bước nào:

1. Đọc `docs/STATE.md`.
2. Đọc **5 mục cuối** của `docs/DECISIONS.md` (không đọc toàn bộ file).
3. Chạy `python scripts/check_contracts.py` và đọc kết quả.
4. Chạy `pytest tests/test_invariants.py -q` (nếu có). Ghi nhận đỏ/xanh.
5. Chạy `git log --oneline -10` để xem việc gần nhất.

Rồi báo cáo **ngắn gọn** theo đúng khuôn:

```
## Đang dở
(từ STATE.md — tối đa 4 dòng)

## Cảnh báo
- Contract stale: <danh sách, hoặc "không có">
- Test bất biến: <XANH / ĐỎ — nếu đỏ, liệt kê test nào>

## Quyết định gần đây cần nhớ
(tối đa 3 dòng, chỉ những ADR ảnh hưởng tới việc sắp làm)

## Đề xuất 3 việc hôm nay
1. <việc> — agent: <tên> — vì sao ưu tiên: <1 dòng>
2. ...
3. ...
```

Sau đó **dừng lại và đợi Bách chọn**. Không tự bắt đầu việc nào.
