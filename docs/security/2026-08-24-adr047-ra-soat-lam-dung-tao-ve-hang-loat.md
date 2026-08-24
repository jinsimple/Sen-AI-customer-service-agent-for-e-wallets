# ① Rà soát bảo mật ADR-047 (tiếp nhận trước, bổ sung sau) — 1 finding thật: không có trần số vé/phiên

> PO-agent giao 24/08, ưu tiên hơn ②. Ba câu hỏi cụ thể: (a) người không phải chủ ví có tạo vé rác
> được không, (b) có trần số vé/phiên không — nếu không, đây là đường DoS rẻ, (c) `description_raw`
> có thành đường nhét nội dung độc khi CSKH đọc không. Trả lời: **(a) không — vẫn cần OTP-fresh,
> ADR-047 không đổi AI, (b) CÓ — đây là finding thật, ADR-047 làm nó RẺ HƠN, (c) sạch, đã kiểm hai
> đường (UI CSKH và LLM context tương lai), không tìm được vector nào.**

## (a) Người không phải chủ ví — KHÔNG có đường mới, ADR-047 không đổi lớp xác thực

[ĐO] `create_ticket` (`customer_tools.py:918-921`) vẫn kiểm `otp_verified_at`/`_otp_fresh(...,
OTP_STEPUP_FRESH_MINUTES)` TRƯỚC MỌI THỨ, kể cả nhánh mới của ADR-047 — không có đường tắt nào bỏ
qua bước này. ADR-047 chỉ đổi ĐIỀU KIỆN NGHIỆP VỤ (không cần tra cứu thành công trước khi tạo),
không đụng lớp XÁC THỰC (vẫn cần OTP phiên tươi ≤15 phút). Muốn tạo vé mà không phải chủ ví, kẻ tấn
công vẫn phải có được một phiên OTP-fresh — đây là **kịch bản chiếm phiên đã tồn tại từ trước**
(không phải lỗ mới do ADR-047 mở), đã có cơ chế riêng chặn (JWT ngắn hạn 15 phút, revocation list,
OTP step-up riêng cho hành động có hậu quả — AUTH-008). **Không kết luận ADR-047 mở đường chiếm
danh tính** — nó chỉ làm một phiên ĐÃ BỊ CHIẾM có khả năng gây hại NHANH HƠN (xem mục b).

## (b) 🔴 FINDING THẬT — không có trần số vé được tạo trên một phiên/user, và ADR-047 vừa gỡ nốt
## rào chắn tự nhiên cuối cùng

**[ĐO] Toàn bộ cơ chế throttle hiện có, đọc hết `create_ticket` + đường gọi nó:**

| Cơ chế | Chặn gì | KHÔNG chặn gì |
|---|---|---|
| `require_otp_verified`/`_otp_fresh` (step-up 15 phút) | Danh tính phiên — phải OTP-fresh mới gọi được | Số LẦN gọi khi đã fresh — fresh một lần, gọi bao nhiêu lần tuỳ ý trong 15 phút |
| `@limiter.limit("20/minute")` trên `/agent/chat` (`main.py:610`) | Tần suất TIN NHẮN — khoá theo **địa chỉ IP** (`get_remote_address`) | Không khoá theo user — nhiều tài khoản cùng IP chia sẻ hạn mức; MỘT tài khoản đổi IP thì thoát hẳn hạn mức. Và đây là trần TIN NHẮN, không phải trần VÉ — không có gì đếm riêng số `create_ticket` thành công |
| `_agent_turn_limiter` (20 slot đồng thời, `main.py:378`) | Tổng THÔNG LƯỢNG toàn hệ thống tại một thời điểm | Không phải trần theo user, không ngăn MỘT user gửi liên tục (chỉ chặn khi hệ thống đã đầy) |
| `_locked`/bất biến chống livelock (`customer_tools.py:751`) | Gọi lại `create_ticket` với **cùng tham số** sau khi ĐÃ THẤT BẠI | Chỉ áp cho lỗi — gọi liên tiếp với tham số **khác nhau** (complaint_type/mô tả khác mỗi lần) và **THÀNH CÔNG** mỗi lần thì không chạm bất biến này (`_dau_loi` trả `None` khi thành công, không ghi sổ) |
| `_otp_request_user_limiter` (10 lần xin OTP/phút/user) | Tốc độ XIN OTP mới | Không phải trần vé — và với step-up 15 phút, không cần xin lại OTP giữa chừng để spam trong một cửa sổ |
| Câu prompt *"Không gọi lại create_ticket cho khiếu nại đã tạo ticket trong hội thoại này, trừ khi khách rõ ràng đang báo một vấn đề MỚI"* | — | Đây là hướng dẫn **CẤP PROMPT** (xác suất, model tuân theo mức độ nào tuỳ ngữ cảnh), **không phải cổng tất định** — và kể từ ADR-047, khách chỉ cần nói "vấn đề khác" là hợp lệ mở lại, không cần chứng minh gì (không cần trans_id, không cần mô tả khác biệt thật) |

**Không có hàng nào trong bảng trên đếm SỐ VÉ đã tạo cho một user/phiên.** Đây là khoảng trống có
thật, độc lập với ADR-047 — nhưng **ADR-047 làm chi phí khai thác giảm mạnh**, đúng câu hỏi PO-agent
đặt.

### [ĐO] ADR-047 gỡ đúng rào chắn TỰ NHIÊN cuối cùng (không phải chủ đích, nhưng là hệ quả thật)

Trước ADR-047: nhánh `not_found` (`prompt.py` gốc, trước `f6f70df`) buộc agent hỏi lại tối đa
`{max_rounds}` lần trước khi được tạo ticket với `trans_id=None` — nghĩa là **spam một vé cũ đòi
hỏi ÍT NHẤT vài lượt hội thoại thất bại** (dù không cần dữ liệu thật, vẫn tốn số lượt = tốn thời
gian + dễ chạm trần `20/minute`). Sau ADR-047: nhánh **khách chủ động yêu cầu** bỏ hẳn điều kiện
đó — **một tin nhắn** ("mở khiếu nại cho tôi, tôi bị mất tiền") đủ để agent gọi `create_ticket`
NGAY trong lượt đó, `scope="unknown"`, `trans_id=None`.

**Phép tính cụ thể, dùng đúng số vừa chốt CÙNG NGÀY (ADR-045b, `docs/DECISIONS.md:2839-2858`):**
`OTP_STEPUP_FRESH_MINUTES` = 15 phút (AUTH-008), `20/minute` là trần tin nhắn (không phải trần
vé) → **một phiên OTP-fresh, nếu mỗi tin nhắn đều thuyết phục được model tạo vé "vấn đề mới", có
thể tạo tới ~20 vé/phút × 15 phút = tới ~300 vé trong MỘT cửa sổ OTP-fresh, từ MỘT tài khoản** —
so với con số **PO thật vừa chốt CÙNG NGÀY (ADR-045b): 20 vé/CSKH/ca**. Một phiên duy nhất, một
cửa sổ 15 phút, đủ sức tạo lượng vé rác **vượt xa** hạn mức xử lý của MỘT CSKH cho MỘT CA làm
việc — nếu request thật xảy ra hàng loạt (không phải giả định lý thuyết xa vời, chỉ cần script gọi
`/agent/chat` lặp với các câu "vấn đề mới" khác nhau).

**Giới hạn thành thật của phép tính này:** đây là TRẦN LÝ THUYẾT dựa trên các cơ chế tất định đã
đọc — **chưa đo được tỉ lệ model THẬT SỰ tuân theo "vấn đề mới" bao nhiêu lần liên tiếp** trước khi
từ chối hoặc bị bất biến chống lặp khác chặn (vd. hai giao dịch giống hệt nhau về mô tả có thể bị
đối chiếu — nhưng không có cơ chế đối chiếu MÔ TẢ giữa các vé, chỉ có đối chiếu THAM SỐ trong CÙNG
MỘT lượt gọi lỗi). Không đo LLM thật ở đây, đúng giới hạn cần nói rõ.

### Đề nghị — không tự vá, ba lựa chọn có đánh đổi

1. **Trần số vé/user/khoảng thời gian, tất định, ở đúng tầng `create_ticket_with_fraud_check`**
   (nơi MỌI đường ghi vé hội tụ, kể cả REST) — vd N vé/giờ/user, trả lỗi rõ ràng khi vượt. Đắt nhất
   nhưng đóng dứt điểm, đúng khuôn "tất định thắng xác suất" dự án đã chọn nhiều lần.
2. **Khoá theo `user_id` thay vì chỉ IP** cho `/agent/chat` — không tự nó đủ (vẫn cho phép ~20
   vé/phút/user, gần bằng nguyên trần hiện tại), nhưng đóng lỗ "nhiều tài khoản chung IP" và "một
   tài khoản đổi IP thoát trần". Rẻ hơn #1, không đóng dứt điểm.
3. **Không vá ngay, khai rủi ro có kiểm soát** (khuôn ADR-040) — nếu hạ tầng có lớp giám sát khác
   (vd cảnh báo khi một user tạo >N vé/giờ, xem log/dashboard sau) đã đủ bù đắp trong ngắn hạn.
   Rẻ nhất, nhưng đúng nguyên tắc ADR-040 QĐ2: chấp nhận cho `main` không tự động là chấp nhận cho
   PRODUCTION — cần ai đó ký lại rõ ràng nếu chọn nhánh này.

**Không khuyến nghị một phương án cụ thể** — đây là quyết định vận hành (đánh đổi chi phí vá vs.
rủi ro DoS/hàng đợi rác), đúng loại quyết định cần PO thật/Lead, không phải security tự chọn.

## (c) `description_raw` khi CSKH đọc — sạch, đã kiểm 2 đường, không tìm được vector

**Đường 1 — hiển thị trực tiếp cho CSKH (XSS/HTML injection):** [ĐO]
`grep -rln "dangerouslySetInnerHTML" frontend/src/` → **0 kết quả** trong toàn bộ frontend. React
mặc định escape mọi nội dung text — `description_raw` (dù chứa `<script>`/HTML thô) render thành
chữ, không thực thi. `get_handoff_context()` (`live_chat.py:175`) trả `description_raw` nguyên văn
cho panel CSKH, nhưng nguyên văn ở đây là DỮ LIỆU HIỂN THỊ, không phải mã chạy.

**Đường 2 — quay lại NGỮ CẢNH LLM ở một lượt/agent tương lai (prompt injection gián tiếp):** [ĐO]
đọc toàn bộ `get_customer_history` (`src/tools/get_customer_history.py:140-147`) — trường trả về
cho mỗi complaint quá khứ CHỈ có `complaint_id`, `type`, `status`, `created_at`. **Không có
`description_raw`.** Lời khai gốc của khách KHÔNG BAO GIỜ quay lại ngữ cảnh model ở một lượt sau —
kể cả chính khách hỏi lại "tôi đã báo gì trước đó", agent chỉ thấy loại+trạng thái+thời gian, không
thấy lại nguyên văn. Đối chiếu với `des` (ghi chú GIAO DỊCH, khác trường, có `danh_dau_du_lieu`
spotlighting ở `customer_tools.py:450`) — hai trường tên gần giống dễ nhầm, đã phân biệt rõ ở đây
để không lẫn.

**Không kết luận:** ❌ cần thêm spotlighting cho `description_raw` — không cần, nó chưa từng vào
lại ngữ cảnh LLM ở bất kỳ đường nào tìm được. Nếu sau này có tool/route MỚI đưa `description_raw`
quay lại LLM (vd một tool "tóm tắt lịch sử khiếu nại" tương lai), phải áp `danh_dau_du_lieu` ngay
lúc đó — ghi lại đây làm điều kiện cần nhớ, không phải việc cần làm hôm nay.
