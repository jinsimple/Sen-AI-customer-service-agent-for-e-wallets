# Góc bảo mật bug "token cũ sống sau khi verify OTP" — ③ đổi mức độ hai finding đang chờ

> Ba câu PO-agent hỏi, kèm niêm hai finding cũ theo dữ kiện mới (không viết lại, chỉ nối thêm).

## ① Vòng đời token CŨ — không phải "hai vé hợp lệ", là MỘT phiên với hai mức chứng minh, đúng thiết kế

**[ĐO] Đọc `/auth/otp/verify` (`main.py:449-527`) + toàn bộ vòng đời refresh token (`src/auth.py`):**

- **Access token:** token MỚI giữ **NGUYÊN `iat`** của token cũ (bắt buộc, giữ `thread_id` hội
  thoại AI) — chỉ thêm claim `otp_verified_at=now`. `is_access_token_revoked()` so `iat <
  revoked_before`; vì hai token CÙNG `iat`, không có cách nào thu hồi token cũ mà không thu hồi
  luôn token vừa cấp — comment tại chỗ đã tự giải thích đúng, không phải sơ suất. **Hệ quả: token
  cũ vẫn hợp lệ tới khi hết hạn tự nhiên (15 phút từ `iat`, CÙNG mốc hết hạn với token mới vì cùng
  `iat`) — nhưng năng lực của nó bị giới hạn ĐÚNG BẰNG thiếu claim `otp_verified_at` tươi.**
- **Refresh token:** verify mint **family MỚI** (không rotate family cũ) — [ĐO] `mint_refresh_token`
  không có cơ chế nào thu hồi family cũ tại đây. Family cũ **sống độc lập**, nhưng rotate nó chỉ
  mint được access token mang **claim `otp_verified_at` CŨ** (gốc từ lúc mint family đó) — không có
  đường nào qua family cũ để có được token OTP-fresh.

**Kết luận: đây KHÔNG phải "hai vé hợp lệ cùng lúc cho một phiên" theo nghĩa đáng lo** — cả ở tầng
access token lẫn tầng refresh-family, năng lực của nhánh "cũ" bị chặn cứng đúng và chỉ đúng ba route
OTP-gated (`lookup_transaction`/`get_customer_history`/`create_ticket`), không có đường nào rộng
hơn. Đây là ngữ nghĩa STEP-UP đúng thiết kế: một credential không tự "nâng cấp" chính nó, việc có
thêm một credential khác (token mới) chứng minh mức cao hơn không cần vô hiệu hoá credential cũ nếu
năng lực của nó vẫn bị chặn đúng chỗ. **Không có finding mới ở câu ①** — đã kiểm cả hai tầng
(access + refresh), không chỉ tầng access PO-agent hỏi.

## ② Bản vá có mở đường nào không — kiến trúc HIỆN TẠI đã đúng (httpOnly-only), rủi ro nằm ở CHỖ SỬA chứ không phải Ở ĐÂU LƯU

**[ĐO]** `frontend/src/app/api/otp/verify/route.ts` — route handler ĐÃ đúng khuôn: cập nhật
`access_token`/`refresh_token` vào cookie **httpOnly** (`store.set(SESSION_COOKIE, ..., {httpOnly:
true, sameSite: "lax", ...})`), comment tự khai rõ nguyên tắc *"Client KHÔNG BAO GIỜ thấy
access_token mới"*. Kiến trúc BFF hiện có **đã** đúng hình dạng an toàn nhất (token không bao giờ
vào vùng JS đọc được, không `localStorage`/`sessionStorage` nào chứa nó) — không phải chỗ cần vá.

**[ĐO] Bug LIÊN QUAN đã có tiền lệ trong CHÍNH file `proxy.ts`, đáng để Coder đọc trước khi vá (nếu
chưa đọc):** một bug **cùng họ** (refresh token xoay ở server nhưng cookie không rời được server)
đã từng bị bắt và **fix đã có sẵn, đã chứng minh chạy được**: chuyển logic đặt cookie từ
**middleware** (`NextResponse.cookies.set()` — [ĐO] đã xác nhận 0 header `set-cookie` thoát ra
trong ngữ cảnh middleware) sang **Route Handler** dùng `cookies()` của `next/headers` (đã chứng
minh emit đúng 1 header). Nếu bug PO-agent mô tả có họ hàng với đây (client không thấy token mới),
**khuyến nghị đầu tiên: kiểm xem đường lỗi có phải middleware đang cố đặt cookie theo cách đã biết
là hỏng, thay vì phát minh hướng vá mới.**

**Checklist cụ thể để soát diff KHI NÓ TỒN TẠI (chưa có diff để đọc lúc viết hồ sơ này — đây là tiêu
chí, không phải xác nhận đã kiểm):**
1. Không thêm `localStorage`/`sessionStorage`/biến JS client-side nào giữ giá trị token.
2. Không `console.log`/log giá trị token ở bất kỳ tầng nào (client lẫn route handler).
3. Không token nào đi qua query-string/URL (dễ lộ qua log truy cập/lịch sử trình duyệt/Referer).
4. Nếu chạm `proxy.ts` (middleware) — dùng lại đúng mẫu Route-Handler-`cookies()` đã chứng minh,
   không thử lại `NextResponse.cookies.set()` trong middleware (đã biết hỏng, ghi rõ trong chính
   file).
5. Cookie mới vẫn giữ nguyên `httpOnly`/`sameSite`/`path`/`maxAge` — không nới bất kỳ cờ nào "cho
   dễ debug" rồi quên xiết lại.

**Đề nghị: gửi diff khi Coder xong, tôi soát lại theo đúng checklist trên — không tự tin tưởng dựa
trên mô tả, đúng nguyên tắc "chạy thật, không suy luận" của dự án.**

## ③ 🔴 CÓ — đổi mức độ CẢ HAI finding đang chờ, và đổi theo hướng NGHIêM TRỌNG HƠN

**Câu hỏi PO-agent đúng là câu cần nhất.** Trả lời thẳng: **có**, và cơ chế cụ thể là phân biệt
**"lỗ tồn tại ở tầng API" vs "lỗ ĐI TỚI ĐƯỢC qua UI thật"** — hai điều khác nhau về XÁC SUẤT KHAI
THÁC THẬT dù không khác nhau về việc lỗ có tồn tại hay không.

**`8b83518` (ADR-047, ~300 vé/cửa sổ OTP-fresh):** Toán trong finding đó giả định "một phiên
OTP-fresh" tồn tại. **Backend luôn đúng** (`/auth/otp/verify` mint token đúng claim, xác nhận lại
ở câu ① trên) — lỗ **luôn có thật ở tầng API**, cho bất kỳ ai gọi thẳng API (đã biết cấu trúc
request, vd qua Postman/script). Nhưng **qua UI THẬT, trước bản vá này, không một khách hàng thật
nào từng có được access token mang `otp_verified_at` tươi** (đúng mô tả PO-agent: "otp_verified_at
= null" sau khi verify) — nghĩa là **quần thể có thể khai thác lỗ này trên thực tế bị giới hạn
CHỈ còn người đủ hiểu biết kỹ thuật để tự gọi API trực tiếp**, không phải người dùng thường. **Sau
bản vá: MỌI khách hàng thật, đi đúng luồng sản phẩm, sẽ có token OTP-fresh** — quần thể có thể khai
thác mở rộng thành TOÀN BỘ người dùng sản phẩm (chỉ cần mở tab Network trong devtools, thấy đúng
request `create_ticket` cần gửi, lặp lại — không cần hiểu biết API sâu). **Đây là tăng mức độ THẬT,
không phải suy diễn** — đề nghị nâng ưu tiên xử lý `8b83518` lên NGANG với bản vá token này, không
để tụt lại phía sau trong hàng đợi.

**`5f627e3` (O5, hoàn-tất-giả khi OTP hết hạn):** Đây là chỗ câu hỏi ③ lật một giả định của chính
tôi — **finding gốc mô tả kịch bản OTP hết hạn GIỮA hội thoại là một CA HIẾM** ("hội thoại dài,
hoặc khách quay lại sau khi rời tab"). Nhưng nếu qua UI, `otp_verified_at` **LUÔN LÀ NULL** (không
phải "hết hạn giữa chừng" — chưa từng tươi TỪ ĐẦU) thì **MỌI lượt `create_ticket` qua UI thật, từ
trước tới nay, đều đi vào đúng nhánh lỗi OTP mà finding `5f627e3` mô tả** — đây không phải một ca
biên, đó là **CA THƯỜNG XUYÊN NHẤT** của toàn bộ luồng tạo vé qua UI cho tới khi bản vá token này
land. **Đề nghị nâng ưu tiên Lớp 1 (câu prompt cho nhánh lỗi, PO-agent xác nhận đã giao Coder) và
O5 (đang xếp hàng sau 1A/1B) lên TRƯỚC hoặc ĐI CÙNG bản vá token** — nếu bản vá token land trước mà
hai lớp phòng vệ đó chưa xong, sẽ có một cửa sổ nơi tạo vé LẦN ĐẦU THỰC SỰ THÀNH CÔNG qua UI, và
đúng lúc đó là lúc CẦN NHẤT các lớp phòng vệ hoàn-tất-giả đã sẵn sàng — không phải lúc để chúng vẫn
xếp hàng chờ.

**Không đổi:** phân tích `(c)` trong `8b83518` (`description_raw` sạch, không injection) — không
phụ thuộc việc OTP có fresh hay không, kết luận đó giữ nguyên.

## Niêm — không viết lại hai file cũ, chỉ trỏ

Đề nghị PO-agent (hoặc tôi, nếu được giao) thêm một dòng niêm ngắn vào đầu `8b83518` và `5f627e3`
trỏ tới hồ sơ này, theo đúng quy ước dự án — giữ nguyên nội dung gốc làm bằng chứng đã suy luận
đúng ở thời điểm viết, chỉ bổ sung bối cảnh mới làm đổi mức ưu tiên xử lý.
