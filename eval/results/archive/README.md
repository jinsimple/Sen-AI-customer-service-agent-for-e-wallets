# Lượt đo đã bỏ đi

Nơi cất các lượt đo **không dùng làm bằng chứng cho bất kỳ kết luận nào**: chạy
thử công cụ, lượt bị huỷ giữa chừng, lượt chạy sai tham số.

**Vì sao cất chứ không xoá:** một lượt đo là bằng chứng đã tốn tiền thật để
tạo ra. Xoá đi thì lần sau có ai hỏi "hôm đó đo được gì" là không trả lời
được. Nhưng để lẫn với lượt đo thật thì nguy hiểm hơn — người sau dễ nhặt
nhầm một lượt chạy thử làm mốc nền.

**Luật:** file nào đang được TRÍCH DẪN trong `docs/` hoặc `eval/results/*.md`
thì **KHÔNG được chuyển vào đây** — chuyển là làm chết đường dẫn trong biên
bản. Kiểm bằng `grep -rn "<tên file>" docs/ eval/` trước khi chuyển.

| File | Vì sao bỏ |
|---|---|
| `quality_run_20260814_164323_raw.json` | Lượt 1 case chạy thử công cụ D1 (xác nhận raw có transcript đủ lượt + dấu thước), không phải phép đo chất lượng. |
