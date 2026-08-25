# MỤC TREO — Redis không có mật khẩu — 2026-08-25

> Ghi lại vì lần trước nó chỉ sống trong tin nhắn giữa các phiên và **rơi mất**.
> **KHÔNG vá trong đợt này** — đợt "OTP trước token" đang đóng, đây là mục
> cho đợt sau. Ghi vào repo để nó không rơi lần thứ hai.

## Hiện trạng [ĐO 25/08]

```
grep -rn "requirepass\|REDIS_PASSWORD" docker-compose*.yml src/config.py .env.example
  → 0 kết quả
```

Redis (`docker-compose.yml`, service `redis`) không đặt `requirepass`, không
đọc mật khẩu từ biến môi trường nào. Bất kỳ ai/tiến trình nào nối được vào
mạng nội bộ do Docker Compose dựng cho stack này đọc/ghi thẳng được vào Redis
— kể cả sổ thu hồi refresh-token (`revoked_family:*`, `src/auth.py:151`) và
từ 25/08 (`02892bd`) cả bộ đếm chi tiêu LLM theo ngày
(`fin05:chi_tieu_llm_token:*`).

## Vì sao CHƯA phải lỗ đang mở

`docker-compose.yml:35` — service `redis` **không publish `ports:`** ra host.
Chỉ container khác trong cùng mạng compose của stack đó với tới được; không
có đường nào từ ngoài Docker network vào thẳng Redis hôm nay.

## Vì sao vẫn phải ghi thành mục treo, không phải bỏ qua

Nó thành lỗ **ngay khi** có ai đó (kể cả chính đội, kể cả một ngăn đo/thử
nghiệm) thêm `ports:` cho service `redis` về sau — để debug tại chỗ, để một
script ngoài container đọc trực tiếp, hay bất kỳ lý do hợp lý nào khác.
Trường hợp ấy **không đòi ai làm sai** — chỉ cần một người không biết Redis
ở đây không có mật khẩu, đúng hình dạng "khoảng trống thiết kế" mà dự án đã
gặp nhiều lần ở nơi khác (ADR-026, `/ready`).

## Phạm vi khi vá (đợt sau, chưa làm)

- `requirepass` (hoặc ACL user riêng) cho service `redis`, `docker-compose.yml`
  — vùng ghi tech-lead (ADR-035).
- `REDIS_PASSWORD` vào `.env.example` + `.env.production.example`, ghép vào
  `REDIS_URL` (`redis://:${REDIS_PASSWORD}@redis:6379/0`) — vùng ghi DevOps.
- Đi kèm bản vá persistence `02892bd`: cả hai đổi cùng một service, nên phối
  hợp một lần, không phải hai lượt land tách rời.

## Liên quan

- `02892bd` — bền hoá Redis bằng volume + `appendonly yes` (đã land, đã ghi
  cảnh báo `down -v` vào `docs/DEPLOY.md`).
- Báo cáo `docs/devops/2026-08-25-danh-gia-ha-tang-eu-us.md` (đang chờ đóng
  buổi đo trước khi land) — mục tương ứng sẽ trỏ về file này thay vì lặp lại
  nội dung.
