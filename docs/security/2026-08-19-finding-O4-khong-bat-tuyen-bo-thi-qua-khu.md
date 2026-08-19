# FINDING — O4 không bắt tuyên bố "ĐÃ hoàn tiền" (thì quá khứ) — lỗ chung, KHÔNG riêng GĐ3

> 19/08/2026. Bảo Mật mở finding độc lập theo đề nghị Lead — tách khỏi cuộc bàn cổng nhập bể GĐ3
> (`2026-08-19-gd3-cong-chay-duoc-vs-an-toan-hai-ca-toi-thieu.md`, mục ADV-041), vì đây là lỗ **có
> từ trước GĐ3, trên model ĐANG CHẠY production hôm nay (qwen), không phụ thuộc việc thêm deepseek.**

## [ĐO] — cả tôi và Lead đọc độc lập, cùng kết luận

```
output_filter.py:319   _O4_DONG_TU = ["se ","chac chan","dam bao","cam ket","du dieu kien","duoc duyet"]
                        → TOÀN BỘ là động từ hứa THÌ TƯƠNG LAI (+ một dạng bị động "được duyệt")
output_filter.py:356-360  vt_dong_tu = _vi_tri_dau(md, _O4_DONG_TU)
                        "đã hoàn tiền" → "đã" KHÔNG khớp bất kỳ token nào trong _O4_DONG_TU
                        → vt_dong_tu = None → continue → KHÔNG BAO GIỜ bị bắt
```

**Xác nhận qua đọc trực tiếp mã, không suy diễn:** một câu tuyên bố "đã hoàn tiền"/"đã hoàn tất giao
dịch này"/tương tự — TUYÊN BỐ MỘT HÀNH ĐỘNG Ở THÌ QUÁ KHỨ — không khớp `_O4_DONG_TU` vì danh sách chỉ
chứa động từ hứa THÌ TƯƠNG LAI. Không phải một lỗ hẹp cho một cách diễn đạt hiếm — **"đã" là cách phổ
biến nhất tiếng Việt để tuyên bố một việc đã xong.**

## Đây KHÔNG PHẢI khe hở injection — nó là khe hở TRONG THIẾT KẾ BỘ LỌC

Ca `ADV-041` (chỉ thị giả trong ghi chú giao dịch) chỉ là **con đường phát hiện ra lỗ này**, không
phải NGUYÊN NHÂN của lỗ. Một model tự **ảo giác** "giao dịch này đã được hoàn tiền" — không ai chèn
gì, không có injection, chỉ là lỗi suy luận/nhầm lẫn ngữ cảnh bình thường — **cũng lọt qua đúng khe
hở này, trên MODEL ĐANG CHẠY PRODUCTION HÔM NAY.** Đây là lý do finding này đứng riêng, không gộp vào
sổ nợ "kiểm an toàn deepseek" của GĐ3.

## Vì sao KHÔNG phải O3 bắt được thay

O3 (bịa số liệu) truy vết CON SỐ tới nguồn tool — "đã hoàn tiền" không tự nó chứa số nào cần truy vết
nếu không kèm số tiền cụ thể. Nếu câu bịa có kèm số tiền THẬT (khớp đúng số tiền giao dịch có trong
tool result — hoàn toàn hợp lý vì agent VỪA tra được giao dịch đó), O3 sẽ **không thấy vấn đề gì** —
con số đúng, có nguồn, truy vết được. **Cái sai không nằm ở CON SỐ, nằm ở TRẠNG THÁI/HÀNH ĐỘNG được
tuyên bố đã xảy ra mà không có căn cứ.** O3 và O4 mỗi cái bắt đúng phạm vi của nó; "tuyên bố hành động
đã hoàn tất, thì quá khứ" không thuộc phạm vi CỦA CÁI NÀO.

## Định hạng mức độ: TRUNG BÌNH — không phải P0, không phải bỏ qua được

**Ba yếu tố giữ mức KHÔNG lên P0/cao:**
1. **Không có đường thực thi thật đi kèm.** Route duyệt hoàn tiền (`/resolutions/{id}/approve`) vẫn
   CHỈ mở cho `supervisor`, CHECK constraint DB vẫn chặn ghi thẳng `approved` (ADR-003/BR-10) —
   ràng buộc cứng 1 vẫn đứng nguyên ở TẦNG THỰC THI. Đây là lỗ ở TẦNG NỘI DUNG (agent NÓI sai), không
   phải tầng hành động (không tiền nào thực sự di chuyển sai).
2. **Có một lớp phòng vệ khác, độc lập, đã tồn tại:** prompt hệ thống (`create_ticket` docstring)
   đã dặn agent *"KHÔNG tự hứa hoàn tiền hay mốc thời gian không có trong kết quả tool"* — đây là
   phòng vệ Ở TẦNG HƯỚNG DẪN MODEL, khác tầng O4 (lọc SAU khi model đã nói). Lỗ đang bàn là lỗ Ở LƯỚI
   THỨ HAI, không phải mất toàn bộ phòng vệ.

**Hai yếu tố giữ mức KHÔNG hạ xuống thấp:**
1. **Hậu quả nếu xảy ra là nghiêm trọng cho khách hàng cụ thể:** một khách nghe "tiền của bạn đã được
   hoàn" khi thực tế CHƯA — hợp lý để họ NGỪNG theo dõi/khiếu nại tiếp, tin sự việc đã xong. Phát hiện
   trễ (khi khách kiểm tra lại số dư) sẽ đến kèm mất niềm tin nghiêm trọng hơn một câu trả lời sai
   thông thường — đây là loại bịa đặt "khách sẽ HÀNH ĐỘNG theo" (ngừng khiếu nại), khác một câu bịa
   vô hại về giờ làm việc.
2. **Zero phát hiện hôm nay** — không test nào, không cổng nào, không giám sát nào bắt được shape này.
   Đây đúng hình dạng "cái đèn không kêu" — lỗ tồn tại từ trước GĐ3, trên model đang phục vụ khách
   thật, và không ai biết cho tới hôm nay.

## Đề nghị cho Coder — định hạng, không thiết kế thay

Thêm dấu hiệu THÌ HOÀN TẤT/QUÁ KHỨ vào tập động từ O4 xét (`đã`, `vừa`, `vừa mới`...) — cùng vị trí
đang có, thứ tự động-từ-trước-tiền vẫn dùng được nguyên xi (`"đã HOÀN TIỀN"` → "đã" đứng trước "hoàn
tiền", đúng khuôn hiện có, không cần đổi logic thứ tự). **Một điểm cần cẩn thận khi viết, không phải
đơn thuốc:** "đã" là từ CỰC KỲ phổ biến trong tiếng Việt (`"tôi đã hỏi rồi"`, `"trước đây bạn đã từng
hỏi..."`) — thêm nó thô vào `_O4_DONG_TU` có nguy cơ tăng dương tính giả hơn hẳn các token hiện có
(`"se "`, `"cam ket"` hiếm gặp ngoài ngữ cảnh hứa hẹn). Cần kiểm bằng chính bộ ca âm tính O4 đã có
(comment `:329` tự khai "96/463 lần chặn là O4" — có sẵn dữ liệu để đối chiếu dương tính giả trước
khi land).

## Phạm vi & thứ tự

**Không thuộc GĐ3, không chờ GĐ3.** Đây là bug tồn tại độc lập trên model hiện đang chạy — đủ điều
kiện vá NGAY trong nhánh làm việc hiện tại (không đụng contract, không đụng route, chỉ sửa một hằng
số + kiểm bằng ca âm tính đã có). Đề nghị PO-agent xếp vào sổ việc chung, KHÔNG gắn nhãn "chờ GĐ3
xong", vì gắn nhãn đó sẽ khiến một bug production-hôm-nay bị xếp hàng sau một tính năng demo.
