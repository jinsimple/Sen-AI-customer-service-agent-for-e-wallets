# Giao việc: Build tính năng Chuông thông báo vé mới (CSKH & Sếp)

> Nguồn: PO · 04/09 · Trạng thái: **GREENLIT build** · Ưu tiên: **sau khi vá RB3**
> Kế hoạch đầy đủ (bản PO đã duyệt): artifact `2c6704c4-2efd-472f-a1f9-aae1aa4d7fc4`
> File tham chiếu HTML: scratchpad `ke-hoach-chuong-noti.html`

## Bối cảnh 1 dòng
Chatbot tạo vé → báo CSKH **đang online**. CSKH đề xuất hướng xử lý
(`propose_resolution` → `pending_approval`) → báo **Sếp**. Sếp duyệt/từ chối →
báo ngược CSKH. Một icon chuông nhỏ **trên–trái cạnh tên nhân viên**, bấm ra danh sách.
Sếp có thêm **bảng "CSKH nào đang online"**.

> ⚠️ Ràng buộc #1: CSKH **KHÔNG duyệt**. "CSKH duyệt" = CSKH **đề xuất** (`propose_resolution`).

## 4 quyết định PO đã CHỐT (04/09)
1. **Độ bền khi cả kíp offline:** LƯU thông báo cho MỌI CSKH (thấy khi đăng nhập lại),
   chỉ ĐẨY tức thời cho người đang online. Không để vé rơi.
2. **Giao hàng MVP:** polling ~20s (WS là đợt nâng cấp sau).
3. **Báo ngược khi Sếp duyệt/từ chối:** CÓ, làm trong MVP.
4. **Cột "số vé đang xử lý" trong bảng Sếp:** CÓ, làm luôn trong MVP.

## Việc mở cần TECH-LEAD chốt định nghĩa (đừng tự đoán)
- **"Số vé đang xử lý" của một CSKH nghĩa là gì?** Vé là kho CHUNG (không có
  `claimed_by` trên Complaint — chỉ ChatSession có). Đề xuất: đếm
  (a) phiên live-chat `claimed_by = user_id` đang active + (b) resolution
  do CSKH đó đề xuất còn `pending_approval`. Tech-lead chốt công thức trước khi code cột này.

## Kiến trúc (tóm tắt — chi tiết ở artifact)
- **Presence:** Redis TTL. `POST /presence/heartbeat` mỗi ~20s → khoá
  `presence:staff:<user_id>` EX 45s. Online = còn khoá. Không giữ state trong process (4 worker).
- **Thông báo:** bảng Postgres `notifications` (fan-out khi ghi: 1 dòng/người nhận;
  read_at riêng từng người). Tạo trong cùng transaction sự kiện gốc (không noti cho vé rollback).
- **UI:** chuông + badge số chưa đọc; bấm → danh sách; bấm item → nhảy vé + mark read;
  poll unread-count gộp cùng vòng heartbeat. Bảng presence cho Sếp.

## 6 route mới — QUA QUY TRÌNH §3 (bắt buộc, không tắt)
`GET /notifications` · `GET /notifications/unread-count` ·
`POST /notifications/{id}/read` · `POST /notifications/read-all` ·
`POST /presence/heartbeat` · `GET /presence/staff`
→ Roles: `[cskh, supervisor]` (presence/staff chỉ `[supervisor]`).
**Trình tự §3:** sửa `authority-matrix.yaml` → ghi ADR → PO duyệt (PO đã greenlit build,
xác nhận qua ADR) → `check_contracts.py --update` → bump CONTRACT_VERSION → mới code.

## Bảo mật (bắt buộc)
- Cô lập theo người nhận: chỉ đụng dòng `recipient_user_id = người đăng nhập` (chống BOLA).
- Nội dung noti: CHỈ mã vé + nhãn loại — KHÔNG số tiền/PII/SĐT (ràng buộc #3 + PDPA).
- 6 route mới phải nằm trong cơ chế kiểm token-chưa-thu-hồi (gộp với vá deny-by-default
  của finding logout hôm nay để không lặp lớp bug "quên thêm route mới").

## Trình tự thực thi
1. **Vá RB3 xong + xác nhận trước** (P0 đang chạy). §3 ADR + authority-matrix có thể
   làm SONG SONG (file khác, không đụng graph.py).
2. Migration + backend (presence + fan-out + 6 route) → frontend (chuông + bảng).
3. **Bổ sung bước thông báo vào storyboard 1-vé** (chatbot tạo vé → chuông CSKH →
   đề xuất → chuông Sếp → bảng presence → Sếp duyệt → báo ngược CSKH).
4. **QA chạy 3 lần** luồng mở rộng trên UI thật → rồi mới trình PO review.

## Phân vùng ghi
- tech-lead: `src/`, `migrations/`, `contracts/` (sau ADR duyệt)
- ux-ui/coder: `frontend/src/`
- tester: `tests/`, `frontend/e2e/`

## Việc tồn — chưa có phiên tester nào đang chạy lúc giao (04/09)
🔴 PO nhắc (soát ADR-063 04/09): cô lập theo `recipient_user_id` ép ở tầng SERVICE — cần
tester viết ca **BOLA thật** (CSKH A không đọc/không mark-read được noti của CSKH B) khi có
phiên tester. Không có phiên nào đang hoạt động lúc ADR-063 land — ghi lại đây để không rơi
mất, đón khi tester được bật lại.
