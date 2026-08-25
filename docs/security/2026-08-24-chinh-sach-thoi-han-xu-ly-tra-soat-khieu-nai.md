# Chính sách thời hạn xử lý tra soát/khiếu nại — soạn cho kho RAG

> Giao việc từ PO-agent 24/08, chặn thật (ADR-047 vừa mở cửa "tạo vé ngay" — câu tiếp theo khách
> hỏi gần chắc chắn là "bao lâu thì xong", kho RAG hiện không có gì trả lời). Ba con số PO-agent
> đưa (30 ngày / +15 ngày / 5 ngày) đã **xác minh độc lập** bằng tra cứu web thật (không suy luận,
> không nhận nguyên văn con số PO-agent đưa mà không kiểm) — xem §3 Nguồn & mức tin cậy trước khi
> dùng số nào ở đây cho việc khác ngoài phạm vi tài liệu này.
>
> Vùng ghi: `docs/security/` (đây). Đưa vào kho RAG (`data/`) là việc của PO-agent, KHÔNG đụng ở
> đây.

## 1. Khối nội dung cho kho RAG (viết cho khách đọc, không phải cho luật sư)

> **Bao lâu thì xử lý xong khiếu nại của tôi?**
>
> Theo quy định của Ngân hàng Nhà nước, thời hạn xử lý tối đa là **30 ngày làm việc kể từ ngày
> chúng tôi tiếp nhận yêu cầu** (không phải từ lúc bạn khai đủ thông tin — hồ sơ được tính giờ
> ngay khi bạn báo, kể cả khi thông tin còn thiếu và cần bổ sung sau).
>
> Nếu sau 30 ngày làm việc mà vẫn **chưa xác định được lỗi thuộc về bên nào**, chúng tôi có thêm
> tối đa **15 ngày làm việc** để cùng bạn thống nhất phương án xử lý.
>
> Sau khi có kết quả và thông báo cho bạn, nếu có bồi hoàn, việc hoàn tất được thực hiện trong tối
> đa **05 ngày làm việc** kể từ ngày thông báo kết quả.
>
> Các mốc trên là **thời hạn tối đa theo quy định pháp luật** — nhiều trường hợp được xử lý nhanh
> hơn, tuỳ mức độ phức tạp. Chúng tôi **không phân biệt thời hạn xử lý theo phạm vi giao dịch**
> (chuyển nội bộ trong ví, qua ngân hàng, hay giao dịch quốc tế) — cùng một mốc 30 ngày làm việc
> áp dụng chung.
>
> *(Nếu khách hỏi "tôi còn được khiếu nại giao dịch cũ không": bạn có quyền yêu cầu tra soát/khiếu
> nại trong vòng tối thiểu 60 ngày kể từ ngày phát sinh giao dịch — mốc cụ thể do từng tổ chức
> công bố, không được ngắn hơn mức này.)*

## 2. Vì sao KHÔNG phân biệt theo phạm vi giao dịch — không phải thiếu sót, đã kiểm

Taxonomy dự án có 3 phạm vi (`internal_wallet`/`from_bank`/`to_bank`). [ĐO — tra độc lập, không
suy luận] Điều 6 Thông tư 15/2024/TT-NHNN **áp dụng CHUNG một mốc 30 ngày làm việc cho mọi loại
giao dịch thanh toán**, không có khoản/điểm nào tách riêng theo phạm vi nội bộ/liên ngân
hàng/quốc tế. Đây KHÔNG phải chỗ thiếu dữ liệu cần ghi "chưa có căn cứ" — đã tra và xác nhận luật
**không phân biệt**, nên câu trả lời đúng là nói rõ "áp dụng chung", không phải im lặng bỏ qua
phạm vi.

**Cái duy nhất tôi KHÔNG tìm được căn cứ cụ thể** là mốc xử lý có rút ngắn cho giao dịch **quốc
tế** hay không (tra cứu web không ra kết quả riêng cho trục này, có thể do thông tư này chủ yếu
điều chỉnh thanh toán nội địa) — nếu có khách hỏi thẳng "giao dịch quốc tế có nhanh hơn/chậm hơn
không", RAG nên trả **"áp dụng cùng mốc 30 ngày làm việc như giao dịch trong nước, không có quy
định rút ngắn/kéo dài riêng cho giao dịch quốc tế theo thông tin hiện có"** — không bịa thêm.

## 3. Nguồn & mức tin cậy — xác minh độc lập, không nhận nguyên văn số PO-agent đưa

**Văn bản gốc:** Thông tư 15/2024/TT-NHNN (Ngân hàng Nhà nước, hiệu lực 01/7/2024) — **Điều 6**,
"Quy trình xử lý sai sót và điều chỉnh sai sót, tra soát, khiếu nại trong giao dịch thanh toán,
dịch vụ trung gian thanh toán". Nghị định 52/2024/NĐ-CP là **nghị định gốc trao quyền** (khung
chung về thanh toán không dùng tiền mặt) — [ĐÃ TRA, KHÔNG THẤY] bản thân NĐ 52/2024/NĐ-CP không
tự quy định con số ngày cụ thể nào cho tra soát/khiếu nại; ba mốc 30/15/5 ngày sống ở **Thông tư
15/2024/TT-NHNN**, văn bản hướng dẫn thi hành — trích đúng nguồn, không gộp hai văn bản làm một.

**Ba con số — [ĐO] đối chiếu ĐỘC LẬP qua 3 nguồn thứ cấp khác nhau (luatvietnam.vn × 2 lượt fetch,
hethongphapluat.com), khớp nhau cả ba lần, không chỉ nhận PO-agent nói:**
- 30 ngày làm việc kể từ ngày tiếp nhận — Điều 6, **Khoản 3**.
- +15 ngày làm việc khi chưa xác định lỗi — Điều 6, **Khoản 4**.
- Tối đa 5 ngày làm việc bồi hoàn sau thông báo kết quả — Điều 6, **Khoản 4** (cùng khoản với vế
  trên, khác điểm).

🟡 **Mức tin cậy KHÔNG đều nhau, cần nói rõ trước khi PO-agent dùng để trích dẫn pháp lý chính
thức (khác với dùng cho RAG trả lời khách):** cấp ĐIỀU (6) và cấp KHOẢN (3, 4) được **2-3 nguồn
độc lập xác nhận khớp nhau**, tin cậy cao. Cấp **ĐIỂM** (a/b/c trong khoản 4 — nguồn nào ghi
"4a"/"4b" cho vế nào) chỉ đến từ **một** lượt fetch qua công cụ tóm tắt tự động (không phải đọc
trực tiếp văn bản gốc/Công báo) — **không đủ độc lập để khẳng định chắc**, có thể lệch. Vì lý do
đó, khối nội dung RAG ở §1 **cố tình không trích số điểm (a/b/c)**, chỉ dừng ở "Điều 6" — đủ chính
xác cho một câu trả lời khách hàng, và tránh rủi ro trích sai một chữ cái mà không ai kiểm lại.
**Nếu PO thật cần trích dẫn ở mức điểm cụ thể cho hồ sơ pháp lý/hợp đồng** (khác mục đích RAG trả
lời khách), cần đối chiếu thêm bản Công báo/Cổng thông tin Chính phủ (chinhphu.vn) hoặc bản PDF
chính thức trước khi dùng — hồ sơ này CHƯA làm bước đó, chỉ đủ cho mục đích trả lời khách.

**Mốc 60 ngày (khách có quyền yêu cầu tra soát trong bao lâu kể từ ngày giao dịch)** — chỉ xuất
hiện ở **một** nguồn tra cứu, diễn đạt "không ít hơn 60 ngày" (tức đây là SÀN tối thiểu tổ chức
phải cho phép, từng tổ chức có thể công bố dài hơn, không phải một con số cố định). Đưa vào §1 vì
hữu ích, nhưng gắn cờ mức tin cậy THẤP HƠN ba mốc chính — nếu PO-agent muốn dùng mốc này làm căn
cứ cho quyết định sản phẩm khác (không chỉ trả lời khách), nên xác minh thêm trước khi dựa vào.

**Không kết luận:** ❌ đã đọc bản Công báo/PDF gốc của Thông tư 15/2024/TT-NHNN — chưa, tài liệu
này dựa trên tra cứu web (WebSearch/WebFetch), đối chiếu chéo nhiều nguồn thứ cấp độc lập, KHÔNG
phải đọc trực tiếp văn bản gốc. Đủ tin cậy cho một câu trả lời khách hàng qua RAG (đúng mục đích
PO-agent giao), **không tự động đủ** cho một trích dẫn pháp lý chính thức nếu dùng vào việc khác.
