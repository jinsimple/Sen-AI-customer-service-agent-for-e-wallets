# ADR-044 nháp — soi BOLA route transcript + quyết định phụ thuộc chéo lỗi 2+3

> 19/08/2026. Đọc trọn nháp `nhap-adr-044-CSKH-doc-hoi-thoai.md` + đối chiếu `authority-matrix.yaml`
> + `main.py` trước khi trả lời.

## Câu 1 — BOLA guard: hướng ĐÚNG, nhưng mô tả "user_id khớp" CHƯA phải guard thật sự. Sửa lại mô tả trước khi Coder code.

**[ĐO] `contracts/authority-matrix.yaml`:** `GET /tickets` và `GET /tickets/{ticket_id}` đều
`roles: [cskh, supervisor]`, **không có giới hạn theo `assigned_to`/phân công** — bất kỳ cskh/
supervisor nào cũng đọc được BẤT KỲ ticket nào hôm nay. Đây là mô hình thẩm quyền ĐÃ CÓ TỪ TRƯỚC,
route transcript không đổi nó.

⟹ **Guard "ticket.complaint.user_id khớp đúng khách của vé" gần như LUÔN ĐÚNG với mọi `ticket_id`
hợp lệ** (đó chỉ là quan hệ khoá ngoại — một ticket luôn thuộc về một complaint, một complaint luôn
thuộc về một user). Viết guard như vậy không chặn được gì — nó chỉ tương đương xử lý 404 cho
`ticket_id` sai/không tồn tại, KHÔNG PHẢI một ranh giới thẩm quyền.

**🔴 Ranh giới thật sự cần chặn — khác hẳn điều nháp đang mô tả:** nguy cơ không phải "CSKH đọc vé
của khách khác" (điều đó ĐÃ được phép, đúng mô hình call-center hiện có) — nguy cơ là **route
transcript âm thầm trở thành một "đọc THREAD_ID TRẦN" trá hình dưới lốt "đọc theo ticket".** Nếu cách
triển khai chấp nhận `thread_id` như tham số client truyền vào (dù chỉ là optional override, hay suy
ra từ `user_id` thay vì đúng `complaint.thread_id` của CHÍNH complaint đó), CSKH có thể đọc một cuộc
hội thoại KHÔNG liên quan gì tới vé đang mở — kể cả hội thoại của một PHIÊN ĐĂNG NHẬP KHÁC của cùng
khách (đúng finding chính nháp đã tự tìm ra ở đầu tài liệu, về `thread_id` gắn theo phiên, không phải
user_id đơn thuần).

**Đề nghị sửa câu guard thành:** *"`thread_id` PHẢI được suy ra DUY NHẤT từ
`ticket.complaint.thread_id` (đọc từ DB), KHÔNG BAO GIỜ nhận `thread_id` như tham số request dưới bất
kỳ hình thức nào (query/body/header) — route chỉ nhận `ticket_id`."* Đây mới là guard có ý nghĩa
thẩm quyền thật, và đúng khớp thiết kế mục 3 nháp đã viết đúng (*"đọc theo `thread_id` đã lưu"*) —
tôi chỉ đề nghị NÊU RÕ đây là guard CHÍNH, còn "user_id khớp" hạ xuống thành một 404-handler phụ, để
Coder không lầm tưởng check thứ hai là ranh giới bảo mật.

### Câu hỏi phụ của Lead — rate limit riêng cho route đọc transcript?

**Đề nghị: CÓ, nhưng lý do KHÁC "dò `ticket_id` tuần tự"** — `new_id()` sinh hex ngẫu nhiên 12 ký tự
(`src/tools/base.py:31`), không phải số nguyên tăng dần, nên dò tuần tự KHÔNG khả thi thực tế. Lý do
thật đáng rate-limit: **transcript mang TOÀN VĂN lời khách** (nặng hơn nhiều so với ticket metadata
có cấu trúc) — một tài khoản CSKH bị lộ/dùng sai có thể LOOP qua danh sách `ticket_id` đã có từ
`GET /tickets` để **kéo hàng loạt transcript trong thời gian ngắn** — đây là nguy cơ **exfiltration
tốc độ cao bởi một credential nội bộ**, không phải BOLA cổ điển. Đề nghị tái dùng CHÍNH cơ chế
`@limiter.limit(...)` đã có ở `/agent/chat` (`main.py:610`) — không cần hạ tầng mới, một dòng decorator.

**Về audit/hồi cứu — [ĐO] KHÔNG CẦN xây thêm, đã có sẵn:** `main.py:177-238`, middleware
`_access_logger` ghi **MỌI request** (method/path/status/identity/ip/thời điểm) vào `access.log`,
tự động áp dụng cho route mới mà không cần code gì thêm. Route transcript tự động được audit đủ để
trả lời "CSKH nào đọc transcript vé nào lúc nào" — không cần thiết kế cơ chế ghi log riêng.

## Câu 2 — Chặn cứng hay song song có gate? Đề nghị SONG SONG + GATE CƠ CHẾ HOÁ, không phải chặn cứng thuần tuý — nhưng đây một phần là quyết định điều phối, không thuần bảo mật, Lead cân nhắc cuối cùng.

**Lý do không chặn cứng toàn bộ:** phần lớn khối lượng việc của ADR-044 (migration cột `thread_id`/
`handoff_at`, luồn `thread_id` qua BỐN tầng như nháp đã tự đo, route skeleton, guard thẩm quyền, UI
khung "Hội thoại với trợ lý") **hoàn toàn độc lập** với việc `scrub_pii` đang được vá. Phụ thuộc thật
CHỈ nằm ở ĐÚNG MỘT ĐIỂM: bước cuối cùng route TRẢ NỘI DUNG transcript đã scrub cho client. Chặn cứng
toàn bộ ADR-044 để chờ một điểm phụ thuộc hẹp là trả giá thông lượng cho một rủi ro có thể khoanh hẹp
hơn nhiều.

**Đề nghị cụ thể — GATE CƠ CHẾ HOÁ, không phải một dòng nhắc trong hồ sơ:**
1. Toàn bộ phần schema/plumbing/guard/UI-khung: phát triển song song, không chờ.
2. Bước "trả nội dung transcript đã scrub": PHẢI có một test tự động (không phải review bằng mắt)
   khẳng định `scrub_pii` KHÔNG phá mã `TXN…`/`TCK…` trong transcript trả về — **test này viết TRƯỚC,
   sẽ ĐỎ cho tới khi lỗi 2+3 land**, đóng vai trò "cầu dao" tự động thay vì dựa vào ai đó nhớ đúng thứ
   tự. Đúng tinh thần "cơ chế thắng lời hứa" dự án đã dùng nhiều chỗ khác trong đợt này (cổng ghim
   `ChatClient.pin.test.ts`, cổng ngân sách token…) — không phải phát minh cơ chế mới, áp lại khuôn
   đã có.
3. Route KHÔNG được merge/deploy trong khi test cầu dao ở bước 2 còn đỏ — đây MỚI là điểm chặn cứng
   thật sự, hẹp đúng bằng phạm vi phụ thuộc, không rộng ra cả ADR.

**Đây là đề nghị của tôi, không phải mệnh lệnh** — nếu Lead thấy năng lực đội hiện tại (đang chạy
song song GĐ3 + GĐ4 lỗi 1-4 + ADR-044) không kham nổi thêm một luồng song song, chặn cứng đơn giản
vẫn AN TOÀN, chỉ chậm hơn. Đây là cân bằng thông lượng/đơn giản, không phải câu hỏi an toàn có/không
— cả hai phương án đều an toàn nếu làm đúng.

## Không kết luận

❌ mô hình thẩm quyền ticket hiện tại (mọi cskh đọc mọi vé) là vấn đề cần sửa trong ADR này — đó là
thiết kế đã có từ trước, ngoài phạm vi phát hiện hôm nay, không phải thứ ADR-044 gây ra hay cần vá.
❌ rate limit đề xuất là bắt buộc theo nghĩa BOLA — nó là phòng vệ sâu (defense-in-depth) cho một
class rủi ro khác (exfiltration tốc độ cao), gắn nhãn đúng để không ai đọc nhầm thành "vá BOLA".

---

## NIÊM 19/08 (sau) — câu 2 (gate) đã TỰ GIẢI, đóng đúng cách. Một nghĩa vụ khai mới, không phải bảo mật, cần ghi vào route.

**[ĐO] PO-agent xác nhận, đúng thiết kế:** checkpoint LangGraph lưu bản `HumanMessage` SAU khi
`graph.py:787` đã scrub — nghĩa là nội dung route lỗi 5 đọc ra **VỐN DĨ đã đi qua scrub tại THỜI ĐIỂM
GHI**, không phải scrub lúc ĐỌC. ⟹ route transcript **không phụ thuộc** trạng thái vá lỗi 2+3 hiện
tại — gate tôi đề nghị ở câu 2 KHÔNG CẦN, hai việc chạy song song thật, đóng đúng bằng thiết kế
(không phải bằng đo thêm) — cùng hình dạng cách đóng tôi đã dùng cho câu hỏi transcript-đồng-bộ hôm
trước: *bỏ được sự phụ thuộc, không phải xác minh nó vô hại.*

🔴 **Hệ quả PHẢI khai trong route, không phải việc của tôi tự quyết cách viết nhưng phải nêu ra:**
lịch sử ĐÃ GHI trước khi lỗi 2+3 được vá mang nhãn SAI VĨNH VIỄN (`[LOCATION]` thay vì "ngày", v.v.)
— **không vá ngược được, và không nên thử** (sửa dữ liệu lịch sử = sửa bằng chứng, đúng nguyên tắc
"đọc trước dọn sau" áp cho chính kho hội thoại). Route lỗi 5 phải hiển thị một dòng khai rõ:
*"hội thoại trước [ngày vá lỗi 2+3] có thể chứa nhãn che không chính xác"* — để CSKH đọc transcript
cũ không hiểu nhầm `[LOCATION]` là một địa điểm khách thật sự nhắc tới.
