# Quét cả lớp: test có TÊN hứa một tính chất, ASSERTION kiểm tính chất khác

> Vai: **tester** · 17/08 · **0 lượt LLM**. Quét 79 file `tests/`.
> Tiêu chí **khai TRƯỚC khi quét** — không có nó thì *"0 kết quả"* chỉ nghĩa là
> chưa nhìn kỹ.

## Vì sao quét cả lớp thay vì vá một ca

`test_policy_doc_upload_path_traversal_filename_is_safe` đỏ suốt vì một
`KeyError` trong **logging**, rồi xanh khi lỗi đó được vá — và trong cả hai
trạng thái nó **chưa từng kiểm path traversal**. Assertion duy nhất là
`status_code in (200, 400)`.

Coder vừa dạy cả đội bài ngược lại: họ **không** sửa `filename`, họ quét cả họ
bằng AST với tập thuộc tính `LogRecord` **dựng từ runtime**. Vá một ca của một
lớp, ngay sau bài học đó, là học nửa vời.

## Tiêu chí, khai trước

    ① tập quét: hàm `test_*` có TÊN chứa
       safe · an_toan · khong_ · chan · reject · deny · block · mask · che_
       injection · traversal · bola · authz · quyen · lo_
    ② đánh dấu khi: tên hứa một HIỆU QUẢ (hành động không xảy ra · vật không
       đổi · dữ liệu không lộ) NHƯNG mọi assertion chỉ chạm `status_code`
    ③ KHÔNG đánh dấu khi: status CHÍNH LÀ tính chất trong tên, hoặc có ít nhất
       một assertion chạm vật thật (CSDL · đường dẫn · nội dung)
    ④ "0 kết quả" chỉ có nghĩa NẾU bộ quét bắt được ca ĐÃ BIẾT.
       Không bắt được ⟹ bộ quét hỏng, không phải `tests/` sạch.

**④ thoả:** bộ quét bắt được ca đã biết. Nên con số dưới đây đọc được.

## 🔴 Kết quả: 6 ca, và CẢ SÁU chạm ràng buộc cứng 1 (HITL)

    test_policy_doc_upload_path_traversal_filename_is_safe      status in (200,400)
    test_otp_from_one_resolution_cannot_approve_a_different_…   403
    test_approve_without_requesting_otp_first_is_rejected       403
    test_stale_approval_otp_beyond_freshness_window_rejected    403
    test_wrong_otp_code_rejected                                403
    test_sec_a_cskh_khong_duoc_reject                           403

Năm trong sáu nằm trên **đường duyệt HITL** — cổng quan trọng nhất dự án.

> **`403` chứng minh REQUEST bị từ chối. Nó KHÔNG chứng minh HÀNH ĐỘNG không
> xảy ra.** Một endpoint trả 403 rồi vẫn duyệt là chuyện lạ — nhưng "lạ" chính
> là thứ cổng an toàn tồn tại để bắt.

## Dấu phân biệt: nó nằm TRONG CÙNG MỘT FILE

Đây là phần làm kết quả này chắc chắn, không phải một ý kiến về phong cách:

    test_resolution_reject.py
      ✅ test_sec_a_reject_tu_trang_thai_khac_pending_bi_tu_choi   ← kiểm CSDL
      ✅ test_sec_b_approve_tu_trang_thai_khac_pending_bi_tu_choi  ← kiểm CSDL
      🔴 test_sec_a_cskh_khong_duoc_reject                          ← chỉ 403

    test_injection.py
      ✅ test_create_ticket_description_injection_is_inert          ← kiểm vật
      🔴 test_policy_doc_upload_path_traversal_filename_is_safe     ← chỉ status

Cùng tác giả, cùng file, cùng khuôn — **hai cái kiểm vật, một cái không**.
⟹ Đây là **thiếu sót**, không phải một lựa chọn thiết kế. Nếu là lựa chọn thì
nó đã nhất quán trong cùng một file.

## Vì sao lớp lỗi này khó nghi hơn Luật 1 cổ điển

Luật 1 cổ điển: assertion trùng **trạng thái mặc định** ⟹ vô dụng.
Ở đây assertion **có nội dung thật** — *"không crash"* là tính chất thật, và nó
**đã bắt được bug `LogRecord` hôm nay**.

> **Một cổng vừa hữu ích vừa mang tên sai thì khó bị nghi ngờ hơn một cổng vô
> dụng** — vì nó có thành tích, và thành tích đó thuộc về một trục khác với
> trục tên nó hứa.

## Việc

Sáu ca cần thêm **một** assertion chạm vật: trạng thái CSDL sau lời gọi (năm ca
HITL) · không tệp nào ngoài thư mục kho (ca traversal). Mỗi ca một dòng, 0
token. Tôi làm, nhưng **báo trước** vì nó đổi sáu ô trong bảng an toàn từ
*"đã canh"* sang *"đang canh một nửa"*.
