# Đo drift chất lượng agent (thực tế, OpenAI thật) — 20260813_153645

Model: `gpt-4o-mini` — 40 case.

## 1. Latency

- p50: 37.74s | p95: 144.94s | max: 204.08s
- Trung bình: 53.94s/case

## 2. Cost (ước lượng, KHÔNG phải billing thật)

- Tổng: $0.1782 cho 40 case | Trung bình: $0.00446/case
- Giá dùng để ước lượng: input $0.15/1M token, output $0.6/1M token (gpt-4o-mini)

## 3. Bịa số liệu (ứng viên, cần người xem lại — không phải oracle)

- 0/40 case có ít nhất 1 số tiền trong reply KHÔNG khớp dữ liệu tool/lời khách (0.0%)
- 3/40 case có số nằm trong ID hệ thống CHƯA đối chiếu được DB (xem chi tiết — không tính vào tỉ lệ bịa, không âm thầm bỏ)

## 4. Lỗi hệ thống / vi phạm chất lượng khác

- Case lỗi khi chạy: 0/40
- Case sai lệch checks/forbidden pattern (không tính bịa số liệu riêng ở mục 3): 29/40

## Số trong ID hệ thống CHƯA đối chiếu DB (minh bạch, không tính vào mục 3)

- CASE-091: 236406 (trong TCK-06a236406ad6)
- CASE-094: 43857 (trong TCK-bf43857f0de7)
- CASE-068: 38750618 (trong TCK-38750618ef4b)
