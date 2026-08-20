# Xác minh thi hành ADR-044 khớp đặc tả Bảo Mật — trục THẨM QUYỀN (khác trục KIẾN TRÚC Review đã soi)

> 20/08/2026. [ĐO] đọc trọn diff `e1db3af` + `7b1c90d` + code hiện tại (`graph.py:450-552`,
> `main.py:806-870`, `TicketDetailClient.tsx:263-310`) trước khi trả lời — không nhận tóm tắt.

## Câu 1 — guard giữ đúng MỨC, không chỉ đúng CHỮ. Tự tìm "đường thứ ba", không tìm thấy.

**[ĐO] guard chính đúng như đặc tả:** route (`main.py`) chỉ nhận `ticket_id` qua path, KHÔNG tham số
`thread_id` dưới bất kỳ hình thức nào trong chữ ký hàm. `thread_id` suy DUY NHẤT từ
`session.get(Complaint, ticket.complaint_id).thread_id`.

**Tự truy NGƯỢC toàn bộ đường GHI `Complaint.thread_id` (không chỉ đường ĐỌC Review đã soi) — ba
điểm kiểm, cả ba đóng:**

1. **Tool `create_ticket` model gọi được** (`customer_tools.py:883-889`) — chữ ký CHỈ có
   `complaint_type, scope, description_raw, trans_id, otp_disclosed`. **KHÔNG có `thread_id`.**
   Model KHÔNG có cách nào đặt giá trị này qua injection dù bị dụ thế nào — nó không tồn tại trong
   không gian tham số model nhìn thấy. `thread_id` chỉ xuất hiện ở tham số CLOSURE của
   `build_customer_tools()` (server tự bind từ session đã xác thực), luồn xuống qua lời gọi hàm nội
   bộ, không qua đường model.
2. **Route REST `/tools/create_ticket`** dùng `CreateTicketRequest` — [ĐO] không có field
   `thread_id`. **Sửa lại một điểm Review mô tả chưa chính xác (không đổi kết luận):** đây KHÔNG phải
   "Pydantic chặn field lạ" theo nghĩa từ chối request (`CreateTicketRequest` không có
   `model_config(extra="forbid")` — chỉ MỘT class khác trong file, cho `k` truy vấn RAG, có cấu hình
   đó). Cơ chế thật là **Pydantic v2 mặc định `extra="ignore"`: field lạ bị BỎ QUA khi dựng object,
   không xuất hiện trong `req.model_dump()`** — route handler không bao giờ THẤY nó, dù request không
   bị 422. Kết luận an toàn GIỮ NGUYÊN, chỉ cơ chế mô tả khác — client gửi `thread_id` trong body vẫn
   KHÔNG chạm được cột này, chỉ là bằng cách "rơi mất lặng lẽ" chứ không phải "bị từ chối ồn ào".
3. **[ĐO] `grep -rn "Complaint(\|\.thread_id\s*=" src/`** → ĐÚNG MỘT chỗ trong toàn bộ `src/` dựng
   `Complaint(...)` (`create_ticket.py:80`). Không route UPDATE/PATCH nào chạm `Complaint` sau khi
   tạo. Không có đường ghi thứ hai để kiểm.

**KẾT LUẬN CÂU 1: giữ đúng MỨC bảo vệ đặc tả yêu cầu. Không tìm ra đường thứ ba.** Ba lớp (tool
schema, HTTP schema, đường ghi DB duy nhất) đều độc lập đóng cùng một cửa — không phải một lớp phòng
thủ đơn lẻ tình cờ đứng vững.

## Câu 2 — "user_id khớp" hạ xuống 404-phụ: bản thi hành làm ĐÚNG HƠN đặc tả yêu cầu, không lặng lẽ nâng lại

**[ĐO]** route KHÔNG còn một dòng kiểm tra `complaint.user_id` nào cả — không phải hạ xuống thành
handler phụ, mà **loại bỏ hoàn toàn**, kèm comment tại chỗ giải thích lý do (mọi cskh/supervisor vốn
đã đọc được mọi ticket qua `GET /tickets/{ticket_id}`, một kiểm tra luôn-đúng-với-mọi-ticket-hợp-lệ
không chặn được gì). **Đây là bản thi hành SẠCH HƠN đề xuất gốc của tôi** ("hạ xuống 404-phụ" ngụ ý
vẫn giữ một kiểm tra vô hại) — không giữ code chết, không tạo cảm giác an toàn giả từ một dòng kiểm
tra không có tác dụng. Đạt.

## Câu 3 — `20/minute` tái dùng từ `/agent/chat`: SỐ SAI ĐƠN VỊ, cần nói rõ dù không chặn merge hôm nay

**Đồng ý với khung PO-agent đặt câu hỏi — số này được HIỆU CHUẨN cho một bài toán khác.**
`20/minute` ở `/agent/chat` trả lời câu *"một khách gõ tin nhắn nhanh cỡ nào"* (giới hạn TỐC ĐỘ GÕ
của con người). Route transcript trả lời câu khác hẳn: *"một CSKH ĐỌC VÀ XỬ LÝ một hội thoại đầy đủ
nhanh cỡ nào trước khi hợp lý để mở hội thoại tiếp theo".* Hai câu khác nhau, tái dùng cùng con số là
đúng cơ chế "tên giống nhau, vật khác nhau" đã gặp nhiều lần hôm nay (base image tag, `langsmith`,
alias model trôi) — chỉ khác lần này là MỘT NGƯỠNG SỐ, không phải một chuỗi.

**[ĐO ước lượng, không phải số đo thật — cần khai rõ đây là NHẬN ĐỊNH, không phải phép đo]:** CSKH
đọc + xử lý một transcript đầy đủ (nhiều lượt) một cách nghiêm túc hợp lý mất VÀI PHÚT, không phải
vài giây — 20 lần/phút cho phép một tài khoản bị lộ kéo **1.200 transcript/giờ**, đủ nhanh cho một
chiến dịch trích xuất hàng loạt có ý nghĩa, không phải một ngưỡng mang tính bảo vệ thật cho đúng mục
đích đã khai (chống exfiltration tốc độ cao).

**Đề nghị: SIẾT riêng cho route này — không tái dùng số của `/agent/chat`.** Tôi KHÔNG tự chốt một
con số cụ thể (đó cần dữ kiện vận hành tôi không có: CSKH có kịch bản hợp lệ nào cần lướt NHANH nhiều
transcript liên tiếp không — vd đầu ca trực rà backlog?). **Đây là câu cần Lead/PO thật trả lời trước
khi tôi đề xuất số** — nhưng hướng SIẾT (không giữ nguyên 20/minute) là khuyến nghị bảo mật rõ ràng
của tôi. Không chặn merge hôm nay — route đã có MỘT lớp giới hạn (hơn không có), chỉ chưa đúng ngưỡng
cho đúng mục đích đã khai. Ghi vào sổ nợ, ưu tiên cao (rẻ để sửa: đổi một con số trong decorator).

## Câu 4 — đoạn khai UI: [ĐO] đọc nguyên văn `TicketDetailClient.tsx:277-283` — ĐỦ về nội dung

```
"Bản ghi tự động từ hệ thống lọc thông tin cá nhân — một số câu khách gõ có thể hiện thành nhãn
dạng [TÊN_NGƯỜI]/[ĐỊA_ĐIỂM] thay vì nguyên văn nếu bộ lọc nhận nhầm, kể cả với các câu nói chuyện
thông thường (không riêng dữ liệu nhạy cảm). Đây là giới hạn đã biết của bộ lọc tại thời điểm ghi,
không phải khách thực sự gõ như vậy."
```

Ba tiêu chí tôi kiểm cho một CSKH đọc (không phải cho một kỹ sư đọc code):
1. **Luôn hiện, không điều kiện theo "bản ghi này có thật sự lỗi hay không"** — đúng, tránh rủi ro
   một phép nhận diện "đây là bản ghi cũ" bị sai lại làm ẩn mất cảnh báo đúng lúc cần nhất.
2. **Nêu đúng HÌNH DẠNG lỗi** (câu thường ngày cũng bị, không riêng dữ liệu nhạy cảm) — khớp chính
   xác phát hiện thật (12% câu tiếng Việt đời thường), không mô tả sai thành "chỉ PII mới bị che".
3. **Có câu KẾT LUẬN tường minh cho hành động đọc** ("không phải khách thực sự gõ như vậy") — đây là
   câu quan trọng nhất, trực tiếp ngăn đúng kịch bản PO-agent lo (CSKH tưởng nhãn là lời khách thật).

**KẾT LUẬN CÂU 4: ĐỦ ở mức NỘI DUNG.** Một điểm ngoài thẩm quyền tôi (mức độ NỔI BẬT thị giác — font
11px, class "note"/dim) là quyết định UX-UI, không phải bảo mật — nội dung câu chữ đã đúng, cách
trình bày bắt mắt tới đâu là việc khác.

## Câu bổ sung — ca `chi_so_bang_giao=None` thứ hai (Review tìm): KHAI LÀ ĐỦ, không cần vá

**[ĐO] đọc trọn docstring `graph.py:496-519`** — hai ca `None` được phân biệt RÕ RÀNG trong code (a:
không có `ToolMessage` nào — nhánh timeout không qua tool; b: có `ToolMessage` thật nhưng lượt bị cắt
trước khi có `AIMessage` xác nhận). Route/UI xử lý GIỐNG NHAU (hiện note, không vạch) nhưng **nguyên
nhân được khai riêng trong code** — đúng kỷ luật "ba trạng thái, không phải hai" dự án đã dùng cả
ngày.

**[ĐO] disclosure UI (`TicketDetailClient.tsx:284-291`)** đã phủ đúng ca này, và câu cuối minh bạch:
*"toàn bộ hội thoại dưới đây vẫn ĐẦY ĐỦ"* — đây là điểm quyết định severity: cái MẤT chỉ là một dấu
mốc ĐIỀU HƯỚNG (biết chính xác đọc từ đâu là "lý do bàn giao"), KHÔNG PHẢI mất NỘI DUNG (toàn bộ lời
khách + bot vẫn hiện đủ, badge `co_goi_tool` từng lượt vẫn đúng). CSKH đọc hết transcript vẫn nắm
được toàn bộ vụ việc, chỉ thiếu một điểm nhấn tiện lợi.

**Vì sao KHÔNG nên vá bằng cách đoán vị trí — không chỉ vì docstring nói vậy, tự kiểm lý do:** nguyên
tắc "không đoán khi thiếu tín hiệu xác định" đã được ÁP DỤNG NHẤT QUÁN ở một ca khác NGAY TRONG CHÍNH
FEATURE NÀY (vé không có `thread_id` → trả `transcript:null` kèm lý do, KHÔNG đoán theo mốc thời
gian). Vá case (b) bằng cách đoán sẽ PHÁ VỠ tính nhất quán đó — hai ca cùng họ "thiếu tín hiệu chắc
chắn" mà xử lý khác nhau (một khai thật, một đoán) là điều khó giải thích cho người đọc sau.

**KẾT LUẬN: khai là đủ, không cần vá.**

## Tổng kết cho PO-agent

Bốn câu: ①③④ ĐẠT đặc tả (③ đạt về CƠ CHẾ, còn một khuyến nghị SIẾT NGƯỠNG cần Lead/PO thật quyết số,
không chặn merge). ② bản thi hành TỐT HƠN đặc tả gốc. Ca bổ sung của Review: khai đủ, không vá.
**Không có phát hiện nào chặn merge.** Một mục đưa vào sổ nợ ưu tiên cao: ngưỡng rate-limit route
transcript cần tách khỏi `/agent/chat`, chờ Lead/PO thật cho input vận hành trước khi tôi đề xuất số
cụ thể.
