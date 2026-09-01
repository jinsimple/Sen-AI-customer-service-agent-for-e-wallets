# Hai phát hiện PO đo — LAN expose 3 ngăn Caddy + khoá QWEN_API_KEY bị bỏ quên

> Vai: `security`. Tự xác minh cả hai trước khi viết (không chép nguyên số PO đưa).

## ① 3/4 ngăn Caddy mở ra LAN — SÓT, không phải chủ ý

**[ĐO 01/09, `docker ps` trực tiếp]** xác nhận đúng khớp claim của PO:

```
fin05-ctc1-check-caddy-1   0.0.0.0:61080->80, 0.0.0.0:61443->443   ← LAN
fin05-po-demo-caddy-1      0.0.0.0:60080->80, 0.0.0.0:60443->443   ← LAN
fin05-qa-stripe-caddy-1    0.0.0.0:59080->80, 0.0.0.0:59443->443   ← LAN
fin05-dot-otp-caddy-1      127.0.0.1:48080->80, 127.0.0.1:48443->443  ← ĐÚNG, chỉ localhost
```

**Gốc rễ [ĐO]:** `docker-compose.yml:277-279` (base) khai `"80:80"` / `"443:443"` — cú pháp KHÔNG có
tiền tố IP, Docker mặc định bind `0.0.0.0` (mọi giao diện mạng). Ba override
(`docker-compose.qa-stripe.override.yml` và tương đương cho `ctc1-check`/`po-demo`) chỉ **đổi số
cổng**, không đổi địa chỉ bind, nên kế thừa nguyên mặc định LAN-mở. `dot-otp` đúng vì dùng một
override RIÊNG (`.../scratchpad/dot-otp.override.yml`, không nằm trong repo chính — của một phiên
khác tự dựng) có ghim `127.0.0.1` tường minh. **Cùng file `qa-stripe`, `postgres`/`jaeger` ĐÃ ghim
`127.0.0.1` đúng, chỉ `caddy` bị sót** — đúng nhận định của PO: đây là SÓT một dòng, không phải chủ ý
mở LAN, vì tác giả rõ ràng BIẾT cách ghim (đã làm đúng cho 2/3 service khác trong cùng file).

**Ai trong LAN chạm được gì:** máy này ở địa chỉ `192.168.1.10` (mạng riêng/nhà) — bất kỳ thiết bị
nào cùng đoạn mạng (cùng WiFi, kể cả khách/hàng xóm nếu chia sẻ mạng) gõ thẳng
`https://192.168.1.10:59443` (hoặc `:60443`/`:61443`) sẽ vào được **đúng giao diện FIN-05 đầy đủ**
của ngăn tương ứng — không cần VPN, không cần ở trong Docker network. Cụ thể với `qa-stripe`: kịch
bản nghiêm trọng nhất là `OTP_DEMO_MODE=true` đang bật cho ngăn này (xem
`docs/security/2026-08-31-soat-quay-video-demo-duoc-cam-len-hinh.md`) — ai trong LAN cũng gọi được
`/auth/otp/request` và nhận thẳng mã OTP trong response, y hệt rủi ro đã ghi cho buổi quay, nhưng giờ
là **bất kỳ ai trong LAN**, không chỉ người ngồi trước máy này. Toàn bộ dữ liệu 3 ngăn là dữ liệu sinh
tổng hợp (seed), không phải khách hàng thật — mức độ nghiêm trọng THẤP HƠN một rò rỉ dữ liệu thật,
nhưng vẫn là bề mặt tấn công không cố ý, và với `ctc1-check`/`po-demo` chưa xác nhận có đang chứa gì
nhạy hơn seed hay không (ngoài phạm vi tôi tự kiểm đêm nay).

**Khuôn ghim đúng, đề xuất — DÙNG LẠI đúng mẫu đã có sẵn trong CHÍNH các file này** (không cần bịa
mẫu mới): đổi `"<cổng>:80"` / `"<cổng>:443"` thành `"127.0.0.1:<cổng>:80"` /
`"127.0.0.1:<cổng>:443"` cho khối `caddy:` — đúng cú pháp `postgres`/`jaeger` trong cùng file đã dùng.
Việc code/cấu hình, thuộc `devops`/`tech-lead`, không phải tôi tự sửa.

## ② `QWEN_API_KEY` — khoá sống, không ai dùng, không ai xoay

**[ĐO 01/09]** Xác nhận đủ 3 vế, không in giá trị khoá thật ra bất cứ đâu:

1. **App không đọc `QWEN_API_KEY` ở đâu cả:** `grep -rn "QWEN_API_KEY" src/ scripts/ eval/` → **0 kết
   quả**. `src/config.py:359` xác nhận app CHỈ dùng `LLM_API_KEY` (`_khoa_cho_nha_cung_cap`).
2. **Chưa từng vào git, không phải rò rỉ qua lịch sử:** `git log --all -p -- .env .env.example
   .env.production.example | grep QWEN_API_KEY` → **0 kết quả**. `.env.example`/
   `.env.production.example` (hai file THẬT SỰ có track trong git) **không chứa** `QWEN_API_KEY` —
   sạch, không phải khoá thật bị dán nhầm vào file mẫu.
3. **Vẫn đang "sống" trong `.env` thật** (không track, đúng `.gitignore`), đi theo **mọi container**
   nạp `.env` này — đúng như PO mô tả, một khoá không dùng nhưng vẫn nằm trong mọi ảnh đang chạy,
   nhân đôi bề mặt cần bảo vệ (nếu `.env`/container nào đó bị đọc trộm, kẻ tấn công có thêm MỘT khoá
   API hợp lệ không ai đang theo dõi/xoay, ngoài khoá chính đang dùng) mà không đổi lấy lợi ích gì.

**Còn hiệu lực không:** **KHÔNG tự kiểm được** — kiểm tính hiệu lực của một khoá API thật (gọi thử
tới nhà cung cấp) là hành động TỐN TIỀN/chạm dịch vụ ngoài, ngoài phạm vi "chỉ đọc, phân tích" của
tôi đêm nay, và đúng nguyên tắc dự án đã niêm nhiều lần (không tự ý gọi LLM thật ngoài phạm vi giao).

**Đề xuất:** rút `QWEN_API_KEY` khỏi `.env` (việc `devops`, không phải tôi tự sửa file `.env` — ngoài
vùng ghi `security`). Trước khi rút, người có quyền nên xác nhận khoá còn hiệu lực hay đã hết hạn tự
nhiên — nếu còn hiệu lực và có khả năng đây là khoá TRẢ PHÍ đang bị tính tiền dù không dùng, đây còn
là vấn đề CHI PHÍ, không chỉ bảo mật, đáng báo riêng cho người quản lý tài khoản nhà cung cấp.

## Việc thuộc vai khác, không phải tôi tự làm

- Sửa `docker-compose.*.override.yml` (mục ①) — `devops`/`tech-lead`.
- Rút `QWEN_API_KEY` khỏi `.env` (mục ②) — `devops`, sau khi xác nhận hiệu lực khoá.
- Xác nhận `ctc1-check`/`po-demo` có dữ liệu nhạy hơn seed hay không — tôi chưa tự kiểm đêm nay,
  ngoài phạm vi việc được giao (chỉ soát 2 phát hiện PO đưa).
