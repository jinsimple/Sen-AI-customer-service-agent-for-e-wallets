# Đo drift chất lượng agent (thực tế, OpenAI thật) — 20260813_153645

Model: `gpt-4o-mini` — 40 case.

## 1. Latency

- p50: 24.32s | p95: 119.50s | max: 136.46s
- Trung bình: 33.28s/case

## 2. Cost (ước lượng, KHÔNG phải billing thật)

- Tổng: $0.1778 cho 40 case | Trung bình: $0.00445/case
- Giá dùng để ước lượng: input $0.15/1M token, output $0.6/1M token (gpt-4o-mini)

## 3. Bịa số liệu (ứng viên, cần người xem lại — không phải oracle)

- 0/40 case có ít nhất 1 số tiền trong reply KHÔNG khớp dữ liệu tool/lời khách (0.0%)
- 4/40 case có số nằm trong ID hệ thống CHƯA đối chiếu được DB (xem chi tiết — không tính vào tỉ lệ bịa, không âm thầm bỏ)

## 4. Lỗi hệ thống / vi phạm chất lượng khác

- Case lỗi khi chạy: 0/40
- Case sai lệch checks/forbidden pattern (không tính bịa số liệu riêng ở mục 3): 21/40

## Số trong ID hệ thống CHƯA đối chiếu DB (minh bạch, không tính vào mục 3)

- CASE-092: 2120 (trong TCK-2120ea25f00d)
- CASE-011: 060242 (trong TCK-eab060242ec4)
- CASE-094: 149629 (trong TCK-bd10da149629)
- CASE-068: 83330 (trong TCK-9d83330a0e83)
