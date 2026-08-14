# Case demo chốt cho pitching 14/08/2026

> Người viết: phiên tester (hộp đen, không đọc `src/`) · tối 13/08
> Cách kiểm: chạy THẬT qua đúng đường người demo sẽ đi —
> trình duyệt → BFF `https://localhost` → backend Docker (4 worker, Postgres).
> **KHÔNG** dùng eval harness in-process (harness chạy trên DB tạm SQLite,
> không phải đường demo — số liệu latency của nó không đại diện).
> Mỗi case chạy **2 lượt**, mỗi lượt đăng nhập lại (thread hội thoại mới).

## RÀNG BUỘC QUAN TRỌNG NHẤT — chỉ 4 tài khoản đăng nhập được

`scripts/gen_dataset.py` chỉ gán mật khẩu demo `Demo@123` cho **4 user**;
200+ user còn lại có mật khẩu ngẫu nhiên 28 ký tự **không ai biết**:

| Vai | user_id | Số điện thoại | Mật khẩu |
|---|---|---|---|
| Khách hàng | USR-0145 | `0974000145` | `Demo@123` |
| Khách hàng | USR-0001 | `0387000001` | `Demo@123` |
| CSKH | USR-0201 | `0353000201` | `Demo@123` |
| Sếp (supervisor) | USR-0205 | `0905000205` | `Demo@123` |

⇒ **Mọi case demo phải nằm trên dữ liệu của USR-0145** (hoặc USR-0001).
Case trong `eval/golden_set.jsonl` gắn với user khác (USR-0141/0142/0143/0153…)
**không demo được** — hỏng ngay ở màn đăng nhập. Đây là lý do bộ case dưới
đây dựng lại trên USR-0145 thay vì bê nguyên case golden_set.

## Bộ case chốt

Tất cả đăng nhập bằng **`0974000145` / `Demo@123`**, xác thực OTP khi được hỏi.

### D1 — Tra cứu TÌM THẤY (happy path) ✅ 2/2 lượt đạt

- **Gõ vào:** `minh chuyen 171k cho ban hom 1/8 luc 12:47 ma ban bao chua nhan duoc`
- **Kỳ vọng:** agent gọi tool, tìm đúng `TXN20260801000466` (171.000đ,
  01/08/2026 12:47, thành công, nội bộ ví) giữa **9 giao dịch cùng số tiền**.
- **Đo được:** 22,3s · 16,4s · mở đầu có đồng cảm · số liệu khớp DB ·
  không lộ tên/SĐT.
- **Điểm kể cho khách:** khách chỉ nói "171k hôm 1/8", hệ thống có 9 giao dịch
  trùng số tiền — agent dùng thêm mốc thời gian để chọn đúng một, không đoán bừa.

### D2 — KHÔNG TÌM THẤY (điểm pitch mạnh nhất) ✅ 2/2 lượt đạt

- **Gõ vào:** `kiem tra giup gd TXN20260623999901, toi chuyen ma khong thay trong lich su`
- **Kỳ vọng:** agent nói rõ **không tìm thấy**, hỏi lại thông tin thu hẹp,
  **không bịa** số tiền/trạng thái/mã nào.
- **Đo được:** 9,3s · 3,6s (nhanh nhất bộ) · đồng cảm · 0 số bịa.
- **Điểm kể:** "Đây là chỗ chatbot thường bịa. Mã này không tồn tại trong
  60.000 giao dịch — agent nói thẳng là không tra được, và mọi con số nó nói
  đều truy được về một kết quả tool có thật."

### D3 — Trừ tiền 2 lần (case cảm xúc mạnh) ✅ 2/2 lượt đạt

- **Gõ vào:** `Trừ một lần đã xót, đây trừ tận hai lần 852k, quá đáng thật.`
- **Kỳ vọng:** agent xoa dịu trước, rồi liệt kê đúng 2 giao dịch 852.000đ
  ngày 30/06 (`TXN20260630000001` 11:31:02 và `TXN20260630000002` 11:31:39 —
  cách nhau 37 giây, trùng lặp thật trong dữ liệu).
- **Đo được:** 8,6s · 7,2s · đồng cảm · khớp cả 2 mã · không lộ PII.
- **Ghi chú:** agent liệt kê **3** giao dịch (có thêm 853.000đ lúc 16:12) —
  đúng dữ liệu, không phải lỗi; người demo nên nói trước để không bối rối.

### D4 — Trọn luồng tạo ticket → hàng chờ CSKH ✅ 3/3 lần đạt (kịch bản 2 lượt)

- **Gõ vào (lượt 1):** `ngay 30/06 minh bi tru 2 lan 852.000d, tao ho so khieu nai giup minh`
- **Nếu agent chỉ liệt kê giao dịch rồi hỏi lại → gõ tiếp (chuẩn bị sẵn câu này):**
  `dung roi, 2 giao dich 852.000d luc 11:31 ngay 30/06 do, tao ho so giup minh`
- **Đo được (3 lần chạy):** 3/3 tạo ticket THÀNH CÔNG và **ticket vào đúng hàng
  chờ CSKH** (kiểm bằng đăng nhập `0353000201` xem danh sách ticket).
  Số lượt cần: **2 · 1 · 1** — nghĩa là đôi khi xong ngay lượt 1.
  Latency: 10,9+5,9s · 8,8s · 13,4s.
- **Vì sao đôi khi cần 2 lượt (nói được với khách hàng, là điểm MẠNH):** ví có
  **3** giao dịch quanh 852k (hai giao dịch 852.000đ + một giao dịch 853.000đ),
  tool trả về `multiple_matches` nên agent **bắt buộc hỏi lại thay vì tự chọn**
  — đúng ràng buộc chống bịa số liệu. Sửa cho agent "quyết đoán hơn" chính là
  nới đúng cái rào đó, nên **cố ý không sửa**.
- **Ghi chú:** một lần trong 3 lần, câu trả lời mở đầu thẳng bằng "Mình đã tạo
  hồ sơ…" thay vì câu đồng cảm — không sai dữ liệu, chỉ kém mượt.

## Ghi chú chung cho người demo

1. **OTP:** hệ thống hỏi OTP trước khi tra cứu; môi trường demo trả mã ngay
   trên màn hình. Mã tạo ticket phải tươi ≤15 phút, mã duyệt của sếp ≤10 phút
   — demo kéo dài thì xin lại mã, đây là **tính năng** (PSD2 dynamic linking),
   kể được chứ không phải sự cố.
2. **Latency thật thấp hơn nhiều con số trong `docs/STATE.md`:** đo trên đường
   demo là **3,6–23,2s/lượt** (n=8), không phải p50 37,7s. Con số 37,7s đến từ
   eval harness chạy máy cục bộ với case nhiều lượt — không đại diện cho demo.
3. **Chuỗi `[PERSON]` hiện ra với khách:** ở D1 agent nói "chuyển 171k cho bạn
   **[PERSON]**" — đây là dấu hiệu PII đã được che đúng (tên người nhận không
   rời hệ thống), nhưng nhìn trên màn chiếu hơi lộ kỹ thuật. Người demo nên
   chủ động giải thích, hoặc tránh dừng lâu ở màn đó.
4. **Live-chat CSKH: ĐÃ VÁ, demo được** (blocker QA-13 tối 13/08 nay đã đóng).
   - Đo lại sau khi vá: **60/60 tin tới đủ, 0 mất, 0 lặp, 6/6 phiên độc lập**
     (`python tests/load/ws_fanout_probe.py 6`), và nhắn dồn dập 5 tin liên
     tiếp cũng tới đủ 5/5.
   - Kịch bản demo (khách xin gặp người thật → CSKH nhận ca → nhắn qua lại →
     đóng phiên) chạy qua trình duyệt thật **3/3 lần đạt**, ~7 giây/lần.
   - **Giới hạn còn lại — người demo cần biết:** gõ và Enter **quá nhanh liên
     tiếp** thì ô nhập đôi khi giữ lại chữ và tin đó KHÔNG được gửi đi (lỗi
     giao diện đã biết từ trước, mã L4-04, chưa tìm ra gốc — không liên quan
     tới bản vá tối nay). **Cách né: gõ xong nhìn ô nhập trống rồi mới gõ tin
     tiếp theo.** Nhịp người thật bình thường không gặp.
   - **Trần chống lạm dụng:** mỗi người 60 tin/giờ trong live-chat. Diễn tập
     nhiều lần trước giờ pitch có thể chạm trần — nếu tin đột nhiên không gửi
     được, kiểm tra điều này trước khi nghĩ là hỏng.
