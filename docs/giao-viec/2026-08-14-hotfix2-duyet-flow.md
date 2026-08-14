# HOTFIX 2 — Đảo luồng duyệt + tab FAQ cho sếp — trước demo tối 14/08

> PO thật yêu cầu trực tiếp sau khi xem UI. Dán MỤC A cho tab coder,
> MỤC B cho tab QA/QC. Cả hai frontend-only — KHÔNG đụng backend/contracts
> (backend /policy-search đã mở cho supervisor sẵn trong authority-matrix).

## Bối cảnh & quyết định PO

1. **Luồng duyệt hiện tại ngược với US-005** ("sếp xem đầy đủ căn cứ điều tra
   trước khi quyết định"): nút Duyệt/Từ chối nằm ngay trên card danh sách
   /approve — mời duyệt mù không cần đọc trail. Luồng đúng: /approve chỉ là
   HÀNG CHỜ tóm tắt → bấm vào chi tiết ticket (trail + giao dịch + đề xuất)
   → nút duyệt/từ chối nằm Ở ĐÓ.
2. Điều này ĐẢO quyết định V1 sáng nay ("không đưa nút duyệt vào ticket
   detail") — đó là lựa chọn phạm vi hotfix của PO-agent, không phải ADR;
   PO thật override, hợp lệ. OTP dynamic linking không đổi (vẫn per-resolution).
3. Sếp cần tab "Tra cứu chính sách" (FAQ) — chỉ thiếu ở nav frontend.

## MỤC A — CODER (timebox 90 phút, thứ tự BẮT BUỘC để luôn demo-được)

1. **[SỬA THEO BÁO CÁO KHẨN QA/QC] Guard route /policy-lookup (~10 phút, làm
   trước):** QA đo trên build đang chạy: tab của sếp ĐÃ hiển thị nhưng bấm
   vào bị đá ngược về /approve; vào thẳng URL cũng bị redirect — trong khi
   backend /policy-search trả 200 cho token sếp (đúng matrix). Việc cần làm:
   sửa GUARD của route /policy-lookup (server layout/page) cho phép
   supervisor. ĐỪNG thêm tab mới khi chưa đối chiếu — kiểm `RoleTabNav.tsx`
   nguồn vs build thật trước, tránh tab trùng. KHÔNG đụng backend.
2. **Khối duyệt trong ticket detail (vai sếp):** thay banner + nút "Mở trang
   Phê duyệt →" (vừa thêm sáng nay) bằng khối duyệt đầy đủ cho (các) đề xuất
   `pending_approval` của ticket — tái sử dụng logic `ApproveClient.tsx`
   (handleRequestApprovalOtp → nhập OTP → handleConfirmApprove · handleReject),
   tách thành component dùng chung, đừng copy-paste 2 bản.
   **Role gate nghiêm ngặt: khối này CHỈ render cho supervisor** — CSKH/khách
   mở cùng trang không được thấy nút (UI phản chiếu đúng authority-matrix).
3. **CHỈ SAU KHI test tay bước 2 chạy trọn (OTP → duyệt 200):** sửa /approve —
   card bỏ nút Duyệt/Từ chối, thành tóm tắt + nút "Mở chi tiết →" (tới trang
   ticket của đề xuất đó). /approve giữ nguyên vai trò hàng chờ.
4. tsc sạch · rebuild · verify chuỗi đặc trưng trong container (mỗi bước một
   chuỗi) · test tay trọn luồng MỚI: /approve → chi tiết → đọc trail → OTP →
   duyệt · nhánh từ chối · đăng nhập CSKH mở cùng ticket → KHÔNG thấy nút.
- **Fallback:** hết giờ sau bước 2 → giữ nút ở CẢ HAI nơi tối nay (không lý
  tưởng nhưng không sai), bước 3 chuyển sau demo. Báo rõ trong báo cáo.
- Ràng buộc như hotfix 1: diff tối thiểu, không refactor ngoài phạm vi,
  commit main, không merge dev.

## MỤC B — QA/QC (nghiệm thu khi coder báo xong)

1. Sếp `0905000205`: bấm tab "Tra cứu chính sách" VÀO ĐƯỢC trang (không bị
   đá về /approve). Tiêu chí "ra kết quả" phụ thuộc PO đã nạp tài liệu chưa
   (xem mục PO dưới): ĐÃ nạp → tra "hoàn tiền" phải ra kết quả; CHƯA nạp →
   chấp nhận `not_found` sạch, và ghi rõ trong báo cáo để kịch bản demo né
   câu hỏi chính sách.

## Việc của PO THẬT (5 phút — quyết định B1 trọn vẹn hay thu hẹp)

Kho chính sách đang RỖNG (0 documents — QA xác nhận). Repo có sẵn nguyên liệu:
`data/sample-policy-for-testing.md` và `data/raw/MoMo_FAQ_Giao_dich.pdf`.
Đăng nhập **partner_admin `0900000001` / Demo@123** → tab "Chính sách & FAQ"
→ upload 1–2 file trên. Được vậy thì: B1 nghiệm thu trọn vẹn + demo có thêm
nhịp "khách hỏi chính sách → agent trích nguồn thật" (US-002) + tab FAQ của
sếp có cái để cho khách xem. KHÔNG kịp nạp → demo tuyệt đối né câu hỏi chính
sách, không hứa "đã có knowledge base".
2. /approve: card KHÔNG còn nút duyệt trực tiếp; "Mở chi tiết →" tới đúng
   ticket.
3. Ticket detail vai sếp: thấy trail + giao dịch + đề xuất; xin OTP → duyệt
   200, `approved_by=USR-0205` trong DB; nhánh từ chối 200; duyệt thiếu OTP
   → 403 sạch.
4. **Authz UI:** đăng nhập CSKH `0353000201` và khách mở cùng ticket → KHÔNG
   thấy khối duyệt; gọi thẳng API approve bằng token CSKH vẫn 403 (backend
   không đổi — xác nhận lại 1 phát).
5. Hồi quy: hàng chờ vẫn 3 item thật · D4 chạy 1 lần (luồng tạo ticket không
   liên quan nhưng rẻ) · 19/19 bất biến.
6. Báo GO/NO-GO. Nếu GO: PO sẽ cập nhật kịch bản demo bước sếp duyệt thành
   "/approve → mở chi tiết → đọc căn cứ → OTP → duyệt" — điểm kể chuyện MẠNH
   HƠN bản cũ (sếp đọc đủ căn cứ mới quyết được, đúng tinh thần HITL).

## Nợ ghi nhận (sau demo)

- Nếu fallback xảy ra: hoàn tất bước 3.
- Cân nhắc trang /approve/[id] chuyên biệt cho duyệt (thay vì mượn ticket
  detail) khi làm đợt maker–checker ADR-020 — quyết sau, không làm bây giờ.
