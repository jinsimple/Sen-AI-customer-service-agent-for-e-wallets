# Cookie session (client-trust UI) + xác nhận thật: logout KHÔNG thu hồi access_token trên đa số route

> Vai: `security`. Giao từ PO qua Lead — xếp hạng 2 khiếm khuyết tester tìm thấy (client-trust cookie,
> `secure` cookie) + xác minh CÂU HỎI MỞ ("refresh_token có bị thu hồi khi logout") **qua đúng route
> thật, không suy đoán**. Cả ba mục dưới đây đều [ĐO 04/09] bằng gọi API sống trên `po-demo`, không
> phải đọc code rồi suy luận.

## 1. Khiếm khuyết (a) — client tin field không có chữ ký để hiện UI (menu Phê duyệt)

**Xếp hạng: THẤP / GHI NHẬN — xác nhận đúng hướng P3 PO đã đề.**

Đọc `frontend/src/app/api/session/route.ts` xác nhận cookie session **`httpOnly: true`** — trình
duyệt/JS phía client không đọc/sửa được qua `document.cookie`/XSS. Cách tester sửa `role` (theo mô tả
PO) chỉ khả thi qua devtools/chỉnh tay giá trị cookie trên CHÍNH máy của người đã đăng nhập hợp lệ —
không phải một vector tấn công từ xa. Backend từ chối đúng (403, 0 byte dữ liệu — tester đã xác nhận,
không lặp lại đo). Rủi ro thực tế: **một người tự sửa cookie của chính mình chỉ tự làm mình thấy UI
sai, không đoạt được quyền gì** — đây đúng nghĩa "thiếu defense-in-depth ở tầng hiển thị", không phải
lỗ hổng cấp quyền. Vá rẻ nếu muốn (client không hiện menu dựa theo field cookie mà nên tin response
của route xác thực vai gần nhất), nhưng không cấp bách — đúng P3, không cần nâng.

## 2. Khiếm khuyết (b) — cookie thiếu `secure` — XÁC NHẬN, nhưng bối cảnh QUAN TRỌNG HƠN PO mô tả

**Xếp hạng: TRUNG BÌNH — cao hơn P3 PO đề xuất, thấp hơn CAO vì có 2 lớp giảm nhẹ đã tồn tại sẵn.**

Đọc `frontend/src/app/api/session/route.ts:62-71` xác nhận: `httpOnly: true`, `sameSite: "lax"`,
**KHÔNG có `secure`**. Đúng như PO báo.

🔴 **Một điểm PO chưa nêu, đáng nâng mức quan tâm:** cookie này (`fin05_session`) **không chỉ chứa
`role`** — theo đúng comment trong code (dòng 15: *"Token JWT backend phát ra cũng chỉ nằm trong
cookie httpOnly này"*) — nó mang **NGUYÊN VĂN `access_token` VÀ `refresh_token`**. Thiếu `secure`
không chỉ để lộ "vai hiển thị sai", nó là đường có thể để lộ **toàn bộ bearer credential thật** nếu
cookie từng bị gửi qua kênh không mã hoá.

**Hai lớp giảm nhẹ đã tồn tại, khiến rủi ro không phải "luôn khai thác được":**
1. `httpOnly: true` — chặn hoàn toàn đường XSS/JS đọc trộm cookie. Kẻ tấn công cần một VỊ TRÍ MẠNG
   (MITM), không chỉ một lỗ XSS.
2. **HSTS vừa land tối 01/09** (`Caddyfile`, `Strict-Transport-Security: max-age=31536000;
   includeSubDomains` — chính tôi đã thêm, xem `docs/security/2026-09-01-...`): sau lần truy cập
   ĐẦU TIÊN thành công qua HTTPS, trình duyệt tự chặn mọi yêu cầu HTTP tới domain này trong 1 năm —
   thu hẹp cửa sổ khai thác xuống còn **lần truy cập đầu tiên trước khi HSTS được trình duyệt ghi
   nhớ** (hoặc trình duyệt/thiết bị chưa từng ghé domain này, chưa có preload list).

**Kết luận xếp hạng:** không phải "luôn lộ token" (như khi thiếu cả `httpOnly` lẫn HSTS), nhưng cũng
không phải rủi ro trang trí — cửa sổ khai thác hẹp (lần đầu + MITM) vẫn là MẤT TOÀN BỘ SESSION nếu
trúng, không phải chỉ mất một field hiển thị. Vá RẺ (`secure: true`, một dòng, không có lý do hợp lệ
nào để cookie này đi qua HTTP — toàn bộ kiến trúc đã HTTPS-everywhere), không có lý do trì hoãn dù
không cấp bách. Đề xuất **TRUNG BÌNH**, làm cùng đợt với các việc rẻ khác, không cần ADR.

## 3. Câu hỏi mở PO — ĐÃ XÁC MINH THẬT qua route sống, kết quả ĐÁNG LO HƠN câu hỏi ban đầu

**Xếp hạng: CAO — phát hiện mới, không phải câu trả lời cho câu hỏi cũ.**

**Phương pháp** [ĐO 04/09, gọi thẳng backend qua docker network nội bộ `po-demo`, không qua UI/BFF để
loại nhiễu tầng trình bày]:
```
1. POST /auth/login (USR-0001, customer)                    → access_token A, refresh_token R
2. POST /tools/get_customer_history  (Bearer A)              → 200 OK, dữ liệu đầy đủ (kiểm trước)
3. POST /auth/logout {refresh_token: R} (Bearer A)           → {"ok": true}
4. POST /auth/refresh {refresh_token: R}                     → 401 Unauthorized  ✅ ĐÚNG — refresh_token bị thu hồi thật
5. POST /tools/get_customer_history  (Bearer A — TOKEN CŨ)   → 🔴 200 OK — TRẢ ĐẦY ĐỦ ví/giao dịch/khiếu nại
```

**Trả lời trực tiếp câu hỏi PO:** `refresh_token` ĐƯỢC thu hồi thật (Redis key bị xoá,
`rotate_refresh_token` tự kiểm tra và từ chối đúng — `src/auth.py:233-236`). **Nhưng đây không phải
câu trả lời đầy đủ** — `access_token` (JWT, TTL 15 phút) là token **tự ký, tự xác thực**, KHÔNG bị
tra cứu thu hồi trừ khi route gọi `require_token_chua_thu_hoi`/`is_access_token_revoked`
(`src/auth.py:239-250`, cơ chế `revoked_before:{user_id}`). Cơ chế đó **CHỈ được gắn vào một số route
hẹp** (`create_ticket`, `approve`, `reject`, và từ 31/08: `propose_resolution`, `escalate_ticket`,
`request-approval-otp` — xem `docs/security/2026-08-31-cong-do-truoc-xanh-sau-bdaf17e-5ff93b8.md`).
**`get_customer_history` và `lookup_transaction` — hai route đọc dữ liệu KHÁCH HÀNG nhạy cảm nhất —
KHÔNG nằm trong danh sách đó.**

**Ý nghĩa cho đợt 150 người thật:** "Đăng xuất" trên UI **không thật sự chấm dứt phiên** ở tầng dữ
liệu nhạy cảm nhất — một `access_token` đã lộ (thiết bị công cộng, XSS chụp được trước khi vá, log
vô tình) **vẫn đọc được toàn bộ lịch sử ví/giao dịch/khiếu nại của khách trong tối đa 15 phút sau khi
khách đã bấm "Đăng xuất" và tin rằng phiên đã kết thúc.** Đây KHÔNG phải lỗ hổng lý thuyết — vừa tái
tạo bằng dữ liệu thật (`USR-0001`, 20 giao dịch, 10 khiếu nại trả về nguyên văn).

**So sánh với các route ĐÃ được gate đúng:** `approve`/`reject`/`create_ticket` đã đóng đúng lỗ này —
tức đội đã BIẾT cơ chế và đã áp cho nhóm route "chạm tiền"/"hành động". Route "chỉ đọc" bị bỏ sót có
thể vì bị coi nhẹ hơn — nhưng dữ liệu đọc được ở đây (toàn bộ lịch sử tài chính) không hề "nhẹ" hơn.

## 4. Đề xuất — không tự chọn thay PO/tech-lead, chỉ nêu đánh đổi

**Việc rẻ, làm ngay, không cần ADR (thuộc `tech-lead`):**
1. Thêm `secure: true` vào cookie `fin05_session` (`frontend/src/app/api/session/route.ts:62-71`) —
   không có lý do hợp lệ để KHÔNG bật, kiến trúc đã HTTPS-everywhere.
2. Gắn `require_token_chua_thu_hoi` vào `lookup_transaction`/`get_customer_history` — đúng MẪU đã
   dùng cho `propose_resolution`/`escalate_ticket`/`request-approval-otp` 3 ngày trước, không phải kỹ
   thuật mới, chỉ là MỞ RỘNG PHẠM VI danh sách route đã gate. Rẻ, có tiền lệ, có gate đỏ-trước/xanh-
   sau mẫu sẵn để copy cách đo.

**Việc cần PO quyết phạm vi trước (không tự mở rộng ngoài 2 route trên):**
3. Có nên gắn `require_token_chua_thu_hoi` cho **TOÀN BỘ** route yêu cầu JWT (mặc định-bật thay vì
   danh sách trắng từng route), thay vì tiếp tục thêm từng route một mỗi lần phát hiện? Đây là câu
   hỏi kiến trúc — danh sách trắng hiện tại đã 2 lần cần vá bổ sung (31/08, và giờ là ca này) vì có
   route mới/bị bỏ sót — một thiết kế "mặc định BẬT, chỉ tắt cho route thật sự không cần" đảo ngược
   được gánh nặng "phải nhớ thêm mỗi route mới" — nhưng đây là quyết định kiến trúc rộng, không phải
   một vá điểm, cần PO/tech-lead cân nhắc chi phí kiểm tra Redis thêm mỗi request.

**Không đổi contract/schema** cho bất kỳ đề xuất nào trên — `require_token_chua_thu_hoi` là
`Depends()` bổ sung, không đổi input/output route, không chạm `authority-matrix.yaml`.

## Chưa kiểm được

- Chưa đo độ trễ thêm khi gắn `require_token_chua_thu_hoi` vào 2 route đọc dữ liệu tần suất cao (mỗi
  request thêm 1 lần đọc Redis) — nếu PO/tech-lead lo về hiệu năng ở quy mô 150 người, cần đo riêng.
- Chưa kiểm route `POST /policy-search` và các route `live-chat` có cùng lỗ hay không (ngoài phạm vi
  2 route PO hỏi cụ thể) — nêu ra như khả năng cần rà thêm, không phải kết luận đã có.
