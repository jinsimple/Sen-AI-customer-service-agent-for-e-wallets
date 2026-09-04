# Làm câu khách THỰC TẾ hơn — khách nhỏ giọt, AI/CSKH phải DÒ từng lượt

> **Từ:** phiên PO-coord · **Cho:** Lead → QA/QC (chạy thật po-demo) + tester (nếu dựng test tự động)
> **Ngày:** 04/09/2026
> **Vì sao có brief này:** PO thật nhận xét câu mẫu hiện tại (B2 storyboard 1-vé) KHÔNG thực tế —
> khách khai đủ mã GD + số tiền + ngày + giờ + "nội bộ" trong MỘT câu. Khách thật không làm vậy.
> **Nguồn chuẩn:** `docs/kich-ban-chuyen-gia-cskh-chuyen-nham-tien.md` (chuyên gia CSKH người thật,
> 8 lượt, chuyển vào repo 24/08, KHÔNG biên tập). Đã từng dựng thành test chạy trên `fin05-dot-otp`
> (`eval/kich-ban-chuyen-gia-8-luot-DANG-KY-TRUOC-CHAY.md`) và **bắt bug thật** — nhưng ngăn đó nay
> đã tắt cho cửa sổ quay; brief này neo lại vào giao dịch seed THẬT của `po-demo`.

---

## 1. Nguyên tắc rút từ chuyên gia (thứ phải giữ)

1. **"Một Ý mỗi lượt", không "một câu mỗi lượt".** Khách mở đầu mơ hồ; AI/CSKH dò từng bước. Ngoại lệ
   có chủ đích: **số tiền + thời gian** là MỘT cặp neo tìm kiếm, hỏi chung một lượt là tự nhiên.
2. **Xác minh danh tính TRƯỚC khi tra** (OTP phiên), kèm **một câu chống mạo danh CSKH** ("em không
   bao giờ hỏi mật khẩu ví / OTP giao dịch").
3. **Đọc lại đủ 5 dữ kiện** (mã GD · thời gian · số tiền · người nhận đã che · trạng thái) để khách
   tự đối chiếu — bắt lỗi tra nhầm giao dịch NGAY, không phải sau 3 ngày.
4. **Câu sàng lọc lừa đảo BẮT BUỘC ở mọi ca chuyển nhầm** — hỏi nhẹ về SỰ KIỆN KHÁCH QUAN ("số này
   quen hay lạ? có ai hướng dẫn chị chuyển không?"), KHÔNG hỏi KẾT LUẬN ("chị có bị lừa không").
5. **Tóm tắt → xác nhận TRƯỚC khi tạo vé.** Lời khai là bằng chứng; sai một chi tiết là hồ sơ đi lệch.
6. **Cảnh báo lừa đảo hậu khiếu nại** ở lượt đóng ca ("sẽ không có ai từ ví gọi yêu cầu chuyển tiền /
   OTP để lấy lại tiền").

## 2. Câu khách nhỏ giọt — NEO VÀO SEED THẬT po-demo (thay B2 dồn-một-cục)

> Giao dịch seed thật trong storyboard 1-vé: khách `0974000145` · `TXN20260728000108` · 339.000đ ·
> nội bộ ví · ~19:30 tối 28/07 · người nhận che `058***0135`. GIỮ đúng các số này (đã seed, tra ra
> thật). Chỉ đổi CÁCH khách nói: từ khai-đủ-một-cục → nhỏ giọt.

**K1 (mở đầu, mơ hồ — gõ nguyên văn):**
> `Tôi có chuyển tiền cho một người quen mấy hôm trước mà giờ họ bảo chưa nhận được, tôi lo quá không biết tiền đi đâu, bạn kiểm tra giúp tôi với.`
- KIỂM: AI đồng cảm MỘT câu → đề nghị xác thực phiên TRƯỚC khi tra + câu chống mạo danh. KHÔNG tra vội
  khi chưa có neo + chưa xác thực.

**K2 (sau khi AI xin xác thực):** khách bấm "Xác thực ngay" → nhập OTP phiên hiện trên màn.
- KIỂM: AI xác nhận xác thực xong, rồi HỎI neo tìm kiếm (thời gian + số tiền — một cặp, một lượt).

**K3 (khách trả lời neo — vẫn hơi mờ, gõ nguyên văn):**
> `Chắc khoảng 3-4 hôm trước, tối muộn ấy, hình như hơn ba trăm nghìn một chút.`
- KIỂM: AI tra bằng cửa sổ thời gian + số tiền (KHÔNG ép khách nhớ mã GD). Tra ra `TXN20260728000108`.

**K4 (AI đọc lại 5 dữ kiện để đối chiếu):**
- KIỂM: AI trình đủ **mã GD · thời gian · số tiền · người nhận đã che `058***0135` · trạng thái**.
  Mọi số khớp cột trái = không bịa (ràng buộc cứng #3). Hỏi khách xác nhận đúng giao dịch không.

**K5 (khách xác nhận — gõ nguyên văn):**
> `Đúng rồi, giao dịch đó đó. Giờ tôi phải làm sao để lấy lại tiền?`

**K6 (AI sàng lọc lừa đảo — BẮT BUỘC, gõ nguyên văn khách trả lời):**
- KIỂM: AI hỏi nhẹ "số người nhận này quen hay lạ? có ai nhắn/gọi hướng dẫn anh/chị chuyển lần này
  không?" → khách đáp `Người quen tôi thật, tôi tự chuyển, không ai xui cả.`
- 🔴 Nếu AI po-demo KHÔNG hỏi câu sàng lọc này → **ghi FINDING**, không bỏ qua (bảng đối chiếu 24/08
  ghi FS-13 có *tín hiệu* nhưng KHÔNG chỗ nào bắt AI HỎI — cần đo lại trên po-demo hiện tại).

**K7 (xin tạo khiếu nại + xin gặp người thật):** như B4/B5 storyboard cũ — tóm tắt → tạo vé `TCK-...`
→ handoff DÙNG LẠI đúng mã vé (không tạo vé mới).

## 3. 🔴 Việc phải làm THEO THỨ TỰ (đừng đảo)

1. **QA/QC chạy phiên bản nhỏ-giọt này THẬT trên po-demo TRƯỚC** — mục tiêu KHÔNG phải để quay ngay,
   mà để ĐO: AI có dò đúng từng lượt không · có tra ra bằng thời-gian+số-tiền khi khách KHÔNG đưa mã GD
   không · có đọc lại 5 dữ kiện không · **có hỏi câu sàng lọc lừa đảo không** · có bịa gì khi thông tin
   mờ không. Chụp ảnh + đối chiếu `tool_calls` với TEXT (đúng cách đã bắt bug RB3).
2. **Ghi thẳng Đạt/Lệch cho từng nguyên tắc §1.** Lệch = FINDING thật (đúng tinh thần: câu mẫu cũ dễ
   vì mình cho khách khai sẵn hết; câu thật khó hơn và mới lộ được năng lực/lỗ hổng thật của AI).
3. **CHỈ SAU KHI** QA xác nhận AI xử lý mượt luồng nhỏ-giọt trên po-demo → mới bàn đưa bản nhỏ-giọt vào
   storyboard quay (thay B2 dồn-một-cục). Nếu AI vấp → trình PO thật: hoặc vá trước, hoặc quay bản
   khách được dẫn nhẹ hơn. **Không script lên camera một luồng chưa verify chạy mượt.**
4. Bản 8-lượt đầy đủ (có nhánh lừa đảo A/B/C, hard-truth 3 vế, PDPA đổi góc nhìn) là chuẩn vàng CHO
   HUMAN CSKH — phần lớn thuộc lượt CSKH thật (B6-B9), không phải lượt AI. Tách đúng: §2 ở trên là
   luồng khách↔AI (B2-B5); các nguyên tắc 4/5/6 của chuyên gia thể hiện rõ nhất khi CSKH thật tiếp quản.

## 4. Ranh giới
- Đây là **đặc tả kịch bản** (docs/, vùng PO). Test tự động (`frontend/e2e/`, `eval/`) là vùng tester —
  nếu dựng lại bản 8-lượt cho po-demo, giao tester, đăng-ký-trước-khi-chạy như bản dot-otp cũ.
- KHÔNG đụng backend/contract từ brief này. Nếu QA thấy cần AI hỏi câu sàng lọc mà code chưa ép → đó là
  finding, đưa vào backlog theo §3, KHÔNG tự sửa trong cửa sổ quay.
