# PHÁC THẢO (chưa code, chờ BA/PO duyệt) — tự nối vé mở gần nhất khi handoff thiếu `ticket_id`

> **Nguồn:** phát hiện giữa cổng E2E cuối 04/09 — B5 (`request_human_handoff`) tạo vé MỚI thay vì
> tiếp vé đang mở ở B4, vì model không truyền `ticket_id` (tham số đã CÓ SẴN, đúng ý đồ thiết kế nối
> 1 vé xuyên suốt — xem `docs/STATE.md §0-QUINQUIES`). Đây là bản PHÁC của tech-lead, KHÔNG PHẢI User
> Story chốt, KHÔNG code đêm nay — BA duyệt/tinh khi phiên BA được mở lại.

## Cơ chế đề xuất

Khi `request_human_handoff` được gọi mà model KHÔNG truyền `ticket_id` (bỏ trống, không phải cố ý
tạo vé mới cho vấn đề khác), service tự tìm ứng viên "vé mở gần nhất cùng phiên" TRƯỚC KHI rơi vào
nhánh tạo vé mới. Giữ nguyên nhánh cũ (model tự truyền `ticket_id` đúng) làm ƯU TIÊN CAO HƠN —
auto-attach chỉ là lưới đỡ khi model quên, không thay thế cơ chế hiện có.

## Điều kiện an toàn để auto-attach — ĐỦ CẢ 4, không thương lượng

1. **Cùng `thread_id`** (`Ticket.complaint_id → Complaint.thread_id`, cột đã có từ ADR-044) — điều
   kiện cứng nhất, khác thread coi như khác phiên hoàn toàn.
2. **Vé còn MỞ** — `hitl_status IN ('pending', 'need_more_info')`. Vé đã `approved`/`rejected` là đã
   có người quyết, gắn cờ "khách xin gặp người thật" lên vé đã đóng vô nghĩa với CSKH đọc dashboard.
3. **Đúng `user_id`** — giữ nguyên kiểm đã có sẵn trong `flag_human_handoff`, không đổi.
4. **Trong khung thời gian hợp lý** — đề xuất DÙNG CHUNG ngưỡng ân hạn hàng chờ live-chat (QA đang đo
   số giây thật, xem manifest E2E 04/09) thay vì bịa số riêng — cả hai cùng trả lời câu "bao lâu thì
   còn coi là cùng một phiên trò chuyện", tách hai ngưỡng dễ lệch nhau âm thầm về sau.

## Chủ động BỎ khỏi điều kiện tự động

**"Chưa đổi chủ đề rõ rệt"** — đây là phán đoán NGỮ NGHĨA, không có tín hiệu CỨNG nào trong dữ liệu
hiện có để đo tất định (không có trường "chủ đề" gắn theo lượt chat). Ép máy đoán chủ đề = quay lại
đúng loại rủi ro "model tự quyết không kiểm chứng được" mà thiết kế này định tránh. Chọn hướng "thà
bỏ sót" (không tự nối, để model tự tạo vé mới) thay vì thêm heuristic mềm đánh đổi tính tất định.

## Việc BA/PO cần quyết khi mở phiên lại

1. Con số ngưỡng thời gian cụ thể ở điều kiện 4 (chờ số đo thật từ QA).
2. Xác nhận nhánh cũ (`ticket_id` model tự truyền) vẫn ưu tiên cao hơn auto-attach — đề xuất: CÓ.
