# Đề xuất — header bảo mật ở tầng biên (Caddy) — 2026-08-27

> Chủ động đề xuất, chưa ai giao. Đúng mục P0-4 trong
> [`2026-08-25-danh-gia-ha-tang-eu-us.md`](2026-08-25-danh-gia-ha-tang-eu-us.md) ("Không header
> bảo mật nào ở tầng biên") — nâng đúng lúc vì PO thật sắp mở landing page công khai, đưa nhiều
> khách vãng lai hơn tới đúng domain chạm cả màn hình đăng nhập nhân viên.

## Hiện trạng [ĐO 27/08]

```
grep -n "header|Strict-Transport|X-Frame|Content-Security" Caddyfile → 0 kết quả
```

Không có header bảo mật nào được set ở tầng biên. Trình duyệt nhận response không có bất kỳ chỉ
dẫn nào về HSTS/clickjacking/MIME-sniffing.

## Đề xuất — CHỈ phần AN TOÀN, không kèm CSP

🔴 **Cố ý tách CSP (Content-Security-Policy) ra khỏi đề xuất này.** CSP là header có khả năng phá
vỡ trang cao nhất (chặn nhầm script/style hợp lệ của Next.js nếu cấu hình sai) — cần đo trên chính
ứng dụng đang chạy trước khi chốt policy, không đoán. Năm header dưới đây rủi ro rất thấp, không
cần điều chỉnh theo từng route.

```caddyfile
# Thêm vào snippet (dinh_tuyen_app), TRƯỚC hai khối handle — áp cho MỌI response.
(header_bao_mat) {
	header {
		# HSTS — buộc trình duyệt luôn dùng HTTPS cho domain này sau lần
		# truy cập đầu. KHÔNG set cho {$SITE_DOMAIN} khi chạy local (cert
		# tự ký) — chỉ áp ở đường Cloudflare Tunnel (production thật).
		Strict-Transport-Security "max-age=31536000; includeSubDomains"
		# Chặn nhúng trang này vào <iframe> trên domain khác — clickjacking,
		# đặc biệt quan trọng cho /login và /dang-nhap-noi-bo.
		X-Frame-Options "DENY"
		# Chặn trình duyệt tự đoán content-type khác Content-Type khai báo.
		X-Content-Type-Options "nosniff"
		# Không gửi URL đầy đủ (có thể chứa query nhạy cảm) sang site khác
		# khi khách bấm link ra ngoài.
		Referrer-Policy "strict-origin-when-cross-origin"
		# Tắt các quyền trình duyệt app này không cần — camera/mic/định vị.
		Permissions-Policy "camera=(), microphone=(), geolocation=()"
	}
}
```

Nối vào `dinh_tuyen_app` bằng `import header_bao_mat` — một dòng, cạnh `import dinh_tuyen_app` đã
có ở cả hai site block.

**[ĐO 27/08]** cú pháp trên đã xác nhận hợp lệ bằng chính binary Caddy đang dùng
(`docker run caddy:2-alpine caddy validate`) — không phải suy đoán, `"Valid configuration"`, mã
thoát 0.

## Vì sao AN TOÀN — không cần lo domino với `/ws/live-chat*`

Các header trên là **response header thường**, không chạm giao thức. WebSocket handshake
(`Upgrade: websocket`) không bị ảnh hưởng — Caddy vẫn tự nhận diện và forward đúng như hiện tại,
các header này chỉ đi kèm response HTTP thường của `/login`, `/dashboard`, v.v.

## CSP — việc riêng, sau, cần đo

Khi làm CSP thật: cần bật ở chế độ `Content-Security-Policy-Report-Only` trước, chạy vài ngày,
đọc report xem có script/style hợp lệ nào bị chặn nhầm không, rồi mới chuyển sang chặn thật. Việc
này cần môi trường test có traffic thật hoặc giả lập kỹ — không đề xuất làm vội cùng đợt này.

## Việc còn lại

- 🔴 **Chưa land** — `Caddyfile` đang không có vùng ghi rõ ràng trong `CLAUDE.md §4` (đã báo PO
  thật, đang chờ xác nhận thuộc devops hay tech-lead — xem trao đổi 27/08). Đừng đụng file cho
  tới khi có câu trả lời, kể cả cho năm header rủi ro thấp này.
- Sau khi có chủ file: land, rồi xác nhận thật bằng `curl -I https://app.adaptivealgo.uk` từ một
  máy khác, đọc đủ 5 header trong response.
