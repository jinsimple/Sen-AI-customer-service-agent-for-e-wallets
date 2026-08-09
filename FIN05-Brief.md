# FIN-05 — Project Brief
## AI Agent CSKH Ví điện tử & Xử lý Khiếu nại Giao dịch

**Phiên bản:** 2.1 · **Đội:** T121 (Nhóm 121, AI 20K Build Phase, Cohort 3) · **PO:** Đào Ngọc Bích · **Đội thực hiện:** Lê Quang Huy, Đậu Quốc Duy, Đặng Thái Nam Sơn · **Mentor:** Lê Anh Tiến · **Đối tác đồng hành:** ZaloPay (cung cấp góc nhìn nghiệp vụ thực tế, phản hồi demo — PO đã gặp 2 lần)   

---

## 1. Bối cảnh

Tổng đài CSKH của ví điện tử đang quá tải bởi khiếu nại giao dịch lặp đi lặp lại thuộc 4 nhóm: chuyển nhầm, tiền chưa về, trừ tiền hai lần, hoàn tiền. Phần lớn các case này không đòi hỏi sáng tạo hay phán đoán phức tạp — chúng đòi hỏi **tra cứu chính xác nhiều hệ thống và đối chiếu theo quy trình rõ ràng**. Nhân viên CSKH hiện phải tự tay làm việc này, dẫn đến thời gian chờ dài và trải nghiệm khách hàng kém.

## 2. Vấn đề cần giải quyết

Xây dựng một AI Agent CSKH có khả năng:
- Tra cứu trạng thái giao dịch qua tool (không tự bịa)
- Tự điều tra đa bước để xác định nguyên nhân
- Phân loại khiếu nại và xác định **phạm vi giao dịch** (nội bộ ví, từ ngân hàng, hay ra ngân hàng) — yếu tố quyết định ai có thẩm quyền xử lý
- Đề xuất hướng xử lý/hoàn tiền kèm căn cứ, nhưng **không bao giờ tự quyết định**
- Luôn chuyển kết quả điều tra cho **nhân viên CSKH tiếp nhận trước** (kể cả case khẩn/nghi gian lận), CSKH mới trình lên **sếp phê duyệt** — không có đường tắt nào bỏ qua con người

## 3. Định vị cạnh tranh

Ngân hàng và ví điện tử hiện có xu hướng dùng nền tảng CSKH chuyên nghiệp lâu năm (ví dụ [Zendesk](https://www.zendesk.com/)) — những nền tảng có dữ liệu, kinh nghiệm vận hành, và độ trưởng thành sản phẩm mà một dự án 6 tuần không thể cạnh tranh trực diện. Vì vậy sản phẩm không nhắm thay thế toàn bộ nền tảng CSKH tổng quát, mà nhắm vào 3 lợi thế mà nền tảng tổng quát khó làm tốt bằng một sản phẩm chuyên biệt cho ví điện tử:

1. **Bảo mật dữ liệu chuyên biệt cho ví điện tử** — dữ liệu giao dịch tài chính không rời khỏi hạ tầng do ví kiểm soát, không qua bên thứ ba lưu trữ/xử lý như các nền tảng CSKH tổng quát; kiểm soát chặt theo PDPA và đặc thù ngành thanh toán.
2. **Giọng văn & ứng xử phù hợp bối cảnh tài chính** — bot phải đủ mềm dẻo để xoa dịu khách hàng đang lo lắng vì mất tiền, không robotic, không rập khuôn kịch bản chung chung của nền tảng CSKH đa ngành.
3. **Chi phí vận hành mô hình AI thấp** — để ví điện tử có động lực kinh tế dùng thử, chi phí mỗi hội thoại phải rẻ hơn đáng kể so với chi phí CSKH truyền thống hoặc nền tảng SaaS tổng quát.

Ba yếu tố này là kim chỉ nam định vị sản phẩm — bổ sung góc nhìn cạnh tranh cho thiết kế, không thay thế 4 ràng buộc bắt buộc ở mục 7.

## 4. Mục tiêu & tiêu chí thành công

| Mục tiêu | Đo bằng |
|---|---|
| Giảm thời gian xử lý trung bình một khiếu nại | So sánh thời gian AI điều tra + đề xuất vs. quy trình thủ công mô phỏng |
| CSKH & sếp ra quyết định nhanh hơn, ít lỗi hơn | Số bước tự tra cứu thủ công giảm về 0 (mọi bằng chứng đã có sẵn trong ticket) |
| Độ tin cậy của agent | 0% trường hợp agent đưa ra số tiền/trạng thái không khớp với dữ liệu tool trả về |
| Chi phí vận hành mỗi hội thoại | Chi phí token trung bình/ticket, so sánh với ngưỡng khả thi kinh doanh cho ví điện tử |
| Chất lượng giao tiếp & xoa dịu khách hàng | Đánh giá định tính qua kịch bản demo: khách hàng bức xúc → agent có xoa dịu trước khi cung cấp thông tin không |
| Thành công demo day | ZaloPay và/hoặc một doanh nghiệp ví điện tử khác đồng ý xem/góp ý demo |

## 5. Đối tượng sử dụng

- **Khách hàng**: người dùng ví điện tử gặp sự cố giao dịch, tương tác qua chat.
- **Nhân viên CSKH**: tiếp nhận và điều tra mọi ticket (kể cả case khẩn), xem lại toàn bộ investigation trail của AI, trình lên sếp — **không có quyền tự duyệt** ở bất kỳ trường hợp nào.
- **Sếp / Người có thẩm quyền phê duyệt**: người duy nhất quyết định duyệt, từ chối, hoặc yêu cầu điều tra thêm cho mọi ticket, bất kể phạm vi giao dịch.

## 6. Phạm vi

**Trong phạm vi (build trong khóa):**
- Web app, đăng nhập, 3 vai trò (khách hàng / nhân viên CSKH / sếp phê duyệt)
- Dữ liệu giao dịch **mô phỏng** có kiểm định (xem `FIN05-Data-Brief.md`) — không kết nối core banking thật
- Agent chat xử lý đủ cả 4 loại khiếu nại
- Phân loại theo cả loại khiếu nại **và** phạm vi giao dịch (nội bộ ví / từ ngân hàng / ra ngân hàng)
- Điều tra đa bước có log/giải thích lập luận, gồm bộ 12 tín hiệu gian lận (2 tầng kích hoạt)
- HITL bắt buộc cho mọi đề xuất liên quan tiền — CSKH tiếp nhận, sếp phê duyệt
- Memory hội thoại + lịch sử khách trong phiên làm việc
- Xử lý lỗi khi không tìm thấy giao dịch, khi mô tả mơ hồ, khi đối tác ngân hàng quá hạn phản hồi
- Cảnh báo khi ngoài thẩm quyền của người đang thao tác

**Ngoài phạm vi (không làm ở bản demo này):**
- Kết nối hệ thống ngân hàng/NAPAS thật
- Xác thực sinh trắc học thật qua NFC/CCCD (chỉ mô phỏng OTP + câu hỏi bảo mật)
- Xử lý report cơ quan nhà nước cho case hình sự (chỉ dừng ở bước gắn cờ, tạo ticket đặc biệt)
- Đa ngôn ngữ, đa kênh (chỉ web, tiếng Việt)

## 7. Ràng buộc bắt buộc

1. **HITL bắt buộc** — không có nút nào cho AI hoặc CSKH tự thực thi hoàn tiền/điều chỉnh số dư; chỉ **sếp** mới có quyền quyết định, cho mọi phạm vi giao dịch.
2. **Cấm AI bịa trạng thái/số tiền giao dịch** — mọi số liệu phải có nguồn từ tool call, nếu không tra được phải nói rõ.
3. **Tuân thủ PDPA (Nghị định 13/2023/NĐ-CP)** — không lộ thông tin của người khác (che một phần thông tin người nhận trong case chuyển nhầm).
4. **Xác thực danh tính bắt buộc** — trước thao tác nhạy cảm: OTP phiên làm việc + câu hỏi bảo mật (không bao giờ hỏi mật khẩu/OTP giao dịch thật, đúng khuyến cáo chống lừa đảo của các ví thật).
5. **AI không bao giờ vượt cấp** — mọi kết quả điều tra của AI (kể cả case nghi gian lận) đều phải qua CSKH tiếp nhận trước; CSKH không có quyền tự duyệt bất kỳ case nào; sếp là cấp duyệt duy nhất.
6. **Gắn cờ nghi vấn ≠ khoá ví** — tín hiệu gian lận là điều kiện định tuyến (chuyển người xử lý), không phải kết luận; hai hành động luôn tách biệt.

## 8. Giả định quan trọng (đã cập nhật — một phần đã xác minh, một phần vẫn chờ chuyên gia)

**Đã xác minh với nguồn công khai:**
- Ngưỡng 10 triệu đồng/lần và 20 triệu đồng/ngày (dùng làm ngưỡng tham chiếu cho tín hiệu gian lận FS-05, FS-08) khớp với Quyết định 2345/QĐ-NHNN — nhưng cần lưu ý đây vốn là ngưỡng **bắt buộc xác thực sinh trắc học**, không phải ngưỡng NHNN định nghĩa riêng cho gian lận; đội chủ động mượn ngưỡng này làm mốc rủi ro.
- Khung pháp lý hiện hành cho trung gian thanh toán là **Nghị định 52/2024/NĐ-CP** (hiệu lực 1/7/2024) và **Thông tư 40/2024/TT-NHNN** (hiệu lực 17/7/2024, thay thế Thông tư 39/2014/TT-NHNN đã hết hiệu lực) — yêu cầu tổ chức trung gian thanh toán phải có quy trình giải quyết tra soát/khiếu nại riêng.

**Vẫn là giả định thiết kế, chưa được doanh nghiệp xác nhận:**
- Cấu trúc phân cấp CSKH (giả định 4 CSKH + 2 supervisor, 3 tầng escalate: supervisor / ngân hàng đối tác / cơ quan chức năng).
- 14 ngưỡng trong bộ 12 tín hiệu gian lận, ngoài 2 ngưỡng đã đối chiếu ở trên.
- Tỉ lệ khiếu nại thực tế trên tổng giao dịch (đang mô phỏng ~1,0%) và độ lệch khiếu nại nghiêng về nhóm chạm ngân hàng (~78%).
- SLA xử lý tra soát liên ngân hàng dùng mốc phổ biến theo quy định NHNN, không phải cam kết thật của một ngân hàng cụ thể.

Danh sách câu hỏi đầy đủ cho chuyên gia nghiệp vụ: xem `FIN05-Data-Brief.md` §7.

## 9. Rủi ro chính

| Rủi ro | Ảnh hưởng | Giảm thiểu |
|---|---|---|
| Cỡ mẫu held-out mỏng (≈1-2 case/ô ma trận) | Một lần trượt trông như tỉ lệ lỗi cao dù mẫu quá nhỏ để kết luận | Trình bày kết quả gộp theo nhóm độ khó thay vì theo từng ô riêng |
| AI vẫn có thể "diễn giải" số liệu sai dù có tool | Vi phạm ràng buộc cốt lõi, mất điểm | Test case riêng cho hallucination; ép agent trích dẫn tool result |
| Timeline gấp, không phải ai cũng mạnh code | Không kịp phần Nâng cao | Ưu tiên HITL + chống bịa số liệu trước; escalation multi-tier làm đơn giản trước, tinh chỉnh sau |

## 10. Liên kết

- **GitHub:** https://github.com/AI20K-Build-Phase-Cohort-3/P-121
- **Figma:** https://www.figma.com/design/qLqouOA7n1oL41Gm0CrBPM/VinUni-AI20k
- **Trello (quản lý việc hằng ngày):** https://trello.com/b/lO9aaQy6/vin-ai-20k
- **Tài liệu đi kèm:** `FIN05-PRD.md` · `FIN05-Wireframe.html` · `FIN05-Data-Brief.md`

## 11. Timeline

- **Tuần 1:** Phân tích bài toán, lên tính năng chung, liên kết với các bên thực tế để hiểu nghiệp vụ
- **Tuần 2–3:** Build sản phẩm mẫu
- **Tuần 4:** Demo cho các bạn trong lớp test
- **Tuần 5:** Fix lỗi, làm slide, làm video demo
- **Tuần 6:** Chấm điểm & pitching — mục tiêu có doanh nghiệp ví điện tử tham dự
