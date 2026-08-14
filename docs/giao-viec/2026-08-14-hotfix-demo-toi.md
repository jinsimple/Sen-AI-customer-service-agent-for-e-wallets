# HOTFIX TRƯỚC DEMO TỐI 14/08 — PO đã chẩn đoán, giao coder

> KHẨN — PO thật test tay bản main lúc ~07:00 thấy 3 vấn đề. PO-agent đã
> chẩn đoán bằng DB thật + đọc code. NGOẠI LỆ đóng băng main: được sửa main
> theo lệnh PO thật, diff tối thiểu, xong phải rebuild + verify container +
> 19/19 bất biến, rồi merge main → dev.

## Chẩn đoán (bằng chứng thật, không suy đoán)

### V1 — "Sếp không có nút duyệt": NÚT CÓ THẬT, thiếu ĐƯỜNG DẪN tới nó
- `ApproveClient.tsx:136-155` có đủ nút (Xin OTP duyệt → Duyệt, Từ chối);
  nav sếp có tab "Phê duyệt" (`RoleTabNav.tsx:15`).
- Màn ticket detail (nơi PO đứng khi chụp ảnh) chỉ có banner CHỮ "phê duyệt ở
  trang Phê duyệt" — không có link bấm được. Đây là gap UX thật.
- **Fix:** trên ticket detail, với role supervisor, biến banner thành có nút/
  link "Mở trang Phê duyệt →" (href `/approve`). KHÔNG đưa nút duyệt trực
  tiếp vào ticket detail — tách trang là thiết kế có chủ đích (OTP dynamic
  linking theo resolution), đừng phá.
- **Nếu PO thật báo đã vào tab Phê duyệt mà danh sách RỖNG** → đó là bug khác,
  điều tra `list_resolutions`/filter của ApproveClient (RES-b8d2c7798d53 đang
  `pending_approval` trong DB, phải hiện).

### V2 — "Chuyển nhầm mà status refunded": KHÔNG PHẢI BUG HIỂN THỊ
- DB thật: `TXN20260730000514` có `status='refunded'` trong seed — UI hiển thị
  đúng dữ liệu. Không sửa gì cho demo.
- **Lỗi sản phẩm thật (backlog, không phải tối nay):** agent tạo ticket
  "chuyển nhầm" cho giao dịch ĐÃ hoàn tiền mà không cảnh báo. Hành vi đúng:
  thấy `refunded` → nói rõ "giao dịch này đã được hoàn tiền lúc X" + hỏi còn
  muốn khiếu nại không. → tester thêm case eval (đánh mã M-08).
- Demo tối nay: bám D1–D4 đã kiểm, không ứng tác case lạ.

### V3 — "Đề xuất 6đ": DB LƯU THẬT amount=6 — lỗi ở đầu vào, không phải hiển thị
- `resolutions` có `RES-b8d2c7798d53 | refund_to_wallet | 6 | pending_approval`.
- Đường dữ liệu sạch: form gửi `amount ? Number(amount) : null`
  (TicketDetailClient.tsx:89), backend passthrough → khả năng cao nhất là
  nhập tay "6" khi test (input type=number còn dính scroll/typo).
- **Lỗi sản phẩm thật phải fix tối nay:** số tiền đề xuất hoàn đang là ô nhập
  TỰ DO không gắn với giao dịch nào — trái tinh thần ràng buộc cứng 3 (mọi
  con số truy vết được về tool result). Fix tối thiểu:
  1. Prefill số tiền từ giao dịch gắn với ticket (107.000đ ở case này).
  2. Validation backend: `refund_to_wallet/refund_to_bank` thì amount BẮT
     BUỘC > 0 và ≤ amount giao dịch được trích; lệch với giao dịch → warning
     ở UI, chặn giá trị vô nghĩa.
  3. Dọn dữ liệu test: sửa RES-b8d2c7798d53 về 107000 hoặc xoá — để màn demo
     không còn "6đ" (1 UPDATE, ghi rõ trong báo cáo).

### V4 — (PO phát hiện thêm khi soi trail) tool call đầu trả `null`
- Investigation trail hiện bước 1 `get_customer_history` kết quả `null` (06:58)
  rồi bước 2 mới có dữ liệu. Điều tra nhanh vì sao (OTP chưa verify? lỗi nuốt
  exception?) — nếu là hành vi hợp lệ thì hiển thị phải nói rõ lý do thay vì
  `null` trần. Không blocker, sửa nếu rẻ.

## Thứ tự làm (timebox tổng 2h, ưu tiên trên xuống)
1. V3.2 validation + V3.3 dọn dòng 6đ (chạm tiền — quan trọng nhất)
2. V1 link "Mở trang Phê duyệt"
3. V3.1 prefill
4. V4 nếu còn giờ
5. Rebuild container + verify (grep code mới TRONG container) + 19/19 bất biến
   + báo PO thật test lại đúng luồng: CSKH trình (số tiền tự điền) → sếp vào
   tab Phê duyệt → xin OTP → duyệt.
