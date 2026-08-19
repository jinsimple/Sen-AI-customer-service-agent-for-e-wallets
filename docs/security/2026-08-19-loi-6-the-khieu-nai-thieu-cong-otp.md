# LỖI 6 — thẻ "Lịch sử khiếu nại" thiếu cổng OTP có "Giao dịch gần đây" đã có

> 19/08/2026 khuya. [ĐO] đọc `ChatClient.tsx:604-650` + `src/tools/get_customer_history.py:114-171`
> trước khi định hạng — xác nhận backend trả CẢ HAI trường không điều kiện, chỉ frontend chọn ẩn một.

## Xác nhận [ĐO] Lead — đúng, cả hai vế

1. `ChatClient.tsx:645` render `history?.complaints.map(...)` KHÔNG có điều kiện `!otpVerified`,
   trong khi thẻ `recent_transactions` ngay phía trên (`:615-641`) CÓ.
2. [ĐO] `get_customer_history.py:114-171`: backend trả CẢ `recent_transactions` LẪN `complaints`
   không điều kiện — không có gate OTP nào ở tầng backend cho TRƯỜNG NÀO trong hai trường, đúng
   comment `:604-608` đã tự khai ("route đọc phía backend giữ nguyên theo contract hiện hành").

## Câu 1 — mức độ lộ: THẤP HƠN thẻ giao dịch, nhưng KHÔNG tầm thường, cùng URGENCY xử lý

**So sánh trực tiếp:** thẻ giao dịch lộ SỐ TIỀN + CHIỀU + MÃ GIAO DỊCH — dữ liệu TÀI CHÍNH TRỰC TIẾP,
hạng nhạy cảm cao nhất cho một ví điện tử. Thẻ khiếu nại lộ LOẠI KHIẾU NẠI + TRẠNG THÁI + NGÀY —
không có số tiền, không phải dữ liệu tài chính trực tiếp. **Về DỮ LIỆU: thấp hơn.**

**Nhưng đúng như Lead nêu — đây là "chân dung rủi ro", một hạng dữ liệu cá nhân THẬT theo NĐ 13/2023
(dữ liệu hành vi/tranh chấp của một cá nhân), không phải phụ.** Ai chiếm được một phiên đăng nhập
(trước bước OTP) có thể suy luận: khách này khiếu nại thường xuyên loại gì, đang có tranh chấp mở
hay không — thông tin hữu ích để **hiệu chỉnh một cuộc tấn công social engineering tiếp theo** nhắm
đúng vào khách đó (vd giả danh CSKH gọi điện "về vụ hoàn tiền bạn đang khiếu nại").

**Kết luận mức độ: DỮ LIỆU nhạy cảm thấp hơn, nhưng CƠ CHẾ LỘ giống hệt (cùng lỗ truy cập, cùng phiên
chưa OTP) — xử lý với URGENCY NGANG thẻ giao dịch, không hạ thấp vì "chỉ là metadata".**

## Câu 2 — tầng chặn: giữ TẦNG HIỂN THỊ cho hôm nay ĐỦ, nhưng nâng khẩn cấp của nợ backend + thêm một cơ chế RẺ chống tái diễn

**Không cần ép backend NGAY cho ca này** — logic nhất quán: nếu tầng hiển thị được PO thật chấp
nhận cho dữ liệu NHẠY CẢM HƠN (giao dịch, có số tiền), thì áp cùng chuẩn cho dữ liệu ít nhạy cảm hơn
là hợp lý, không phải hạ chuẩn. Vá theo đúng khuôn Coder đang làm — đủ.

🔴 **Nhưng đây là LẦN THỨ TƯ cùng hình dạng trong một ngày — bản thân đó là tín hiệu cần xử lý ở
tầng KHÁC với "vá từng chỗ", không chỉ định hạng riêng ca này.** Nợ "ADR đợt sau demo" (ép backend)
nên được NÂNG MỨC ƯU TIÊN lên do tần suất tái diễn, không phải vì ca này riêng lẻ nặng hơn — bốn lần
một ngày là bằng chứng thống kê rằng "nhớ áp đúng chỗ" không phải cơ chế đứng vững.

**Đề nghị RẺ, làm được HÔM NAY, không cần đổi contract/backend:** khi Coder vá thẻ khiếu nại, đừng
lặp lại cấu trúc `!otpVerified ? ẩn : hiện` một lần nữa TÁCH BIỆT khỏi thẻ giao dịch — **gộp CẢ HAI
thẻ vào MỘT điều kiện dùng chung** (một wrapper/component/hằng số boolean tính MỘT LẦN, áp cho cả
hai render). Một thẻ thứ ba thêm vào rail này sau này (nếu có) THỪA HƯỞNG gate tự động thay vì cần ai
nhớ copy đúng pattern lần thứ ba — đúng đúng bài học "đặt cơ chế ở nơi không thể đi vòng" dự án đã
dùng nhiều lần hôm nay (cổng ghim, kiến trúc 2-registry vừa quyết cho `pii.py`).

## Không kết luận

❌ mức độ lộ ngang thẻ giao dịch — thấp hơn về dữ liệu, xử lý ngang về urgency vì cùng cơ chế lỗ.
❌ cần ép backend ngay hôm nay — chưa cần, nhất quán với chuẩn đã áp cho ca nặng hơn; NHƯNG nợ backend
cần nâng ưu tiên vì tần suất tái diễn, không phải vì ca này riêng lẻ.
