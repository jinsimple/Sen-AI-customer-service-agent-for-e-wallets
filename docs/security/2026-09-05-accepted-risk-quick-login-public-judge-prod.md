# ACCEPTED RISK — `NEXT_PUBLIC_QUICK_LOGIN=true` công khai trên judge-prod

> Vai: `security`. PO thật đã duyệt CHẤP NHẬN RỦI RO (05/09), sau khi nghe đầy đủ cảnh báo dưới đây —
> **ghi để không bị re-flag như phát hiện MỚI ở lượt soát sau.**

**Rủi ro đã cảnh báo, PO xác nhận đã hiểu:** `docker-compose.home-judge.yml` bật
`NEXT_PUBLIC_QUICK_LOGIN=true` cho build deploy `app.adaptivealgo.uk` (domain PUBLIC, judge xem
thật) — bake 3 tài khoản (CSKH/Sếp/Đối tác ví, mật khẩu chung `Demo@123`) vào bundle JS công khai,
hiện nút một-click đăng nhập ngay thành `supervisor` (vai duyệt hoàn tiền theo Ràng buộc cứng #1)
trên `/dang-nhap-noi-bo` — không cần mật khẩu thật, không OTP. Cờ vốn thiết kế cho đúng một lần quay
video nội bộ (26/08 quyết định gốc), nay tái dùng cho production public thường trực.

**Quyết định PO (05/09):** GIỮ nguyên, chấp nhận rủi ro có chủ đích. **KHÔNG rotate mật khẩu
`Demo@123`.** Lý do PO nêu: dữ liệu trên `judge-prod` là dữ liệu giả/seed (không phải khách hàng
thật, không phải tiền thật), bối cảnh phục vụ giám khảo demo — đánh đổi tiện lợi lấy một rủi ro mà
hậu quả tối đa là thao túng dữ liệu giả.

**Điều kiện để mức chấp nhận này còn hiệu lực — nếu điều kiện đổi, phải soát lại, không mặc định giữ
nguyên vĩnh viễn:**
- Domain `app.adaptivealgo.uk` (hoặc bất kỳ build nào dùng lại `docker-compose.home-judge.yml`)
  **chỉ chứa dữ liệu seed/giả**, không có khách hàng thật/giao dịch thật.
- Nếu dự án tiến tới có dữ liệu thật (dù một phần) trên bất kỳ ngăn nào dùng cờ này ⟹ chấp nhận rủi
  ro này HẾT HIỆU LỰC NGAY, không cần chờ ai phát hiện lại.

**Không phải finding bỏ ngỏ.** Cảnh báo gốc (đầy đủ ngữ cảnh, trích dẫn `frontend/src/app/
dang-nhap-noi-bo/page.tsx:24-39`) đã đưa qua tin nhắn tối 04-05/09 khi soát commit `cf69591`
(`docker-compose.home-judge.yml`) trước khi PO PR lên `main` — không có file riêng ghi lại cảnh báo
đó (chỉ sống trong log điều phối), file NÀY là bản neo chính thức duy nhất. PO đã đọc đầy đủ cảnh
báo trước khi quyết, không phải tự tôi bịa lại sau.
