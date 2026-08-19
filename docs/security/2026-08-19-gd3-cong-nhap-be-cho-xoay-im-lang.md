# GĐ3 — cổng nhập bể có đủ cho xoay IM LẶNG không (PO-agent hỏi, đã bỏ UI chọn model)

> 19/08/2026. Đọc `src/agents/llm_pool.py` (Coder đang viết dở, chưa commit) + diff `src/config.py`
> trước khi trả lời — không đoán trên mô tả brief. Chỉ ĐỌC, không sửa (vùng ghi Coder).

## Trả lời thẳng: HƯỚNG ĐÚNG (nâng lên chặn), NHƯNG 6 CA CHƯA ĐỦ CHO STAKES MỚI. Ba điều kiện cụ thể.

**Vì sao stakes đổi hạng, không chỉ đổi mức độ:** cổng 3-good+3-đối-kháng được thiết kế cho tiền đề
*"khách TỰ NGUYỆN chọn thử model"* — một smoke test là hợp lý khi người dùng biết và đồng ý là một
phần thử nghiệm. Bỏ UI chọn model đổi tiền đề thành *"khách THẬT, KHÔNG BIẾT, KHÔNG ĐỒNG Ý, KHÔNG TỪ
CHỐI ĐƯỢC"* — đây không còn là câu hỏi UX, là câu hỏi **ai được phép đại diện nói với khách hàng thật
mà chưa ai đo đủ kỹ**. Đúng lý do PO-agent nâng lên mức chặn — tôi đồng ý hướng, nhưng cỡ mẫu không
theo kịp lý do đã đổi.

## ① Cỡ mẫu — 6 ca là smoke test, không phải hiệu chuẩn

Dự án **đã có** bộ hiệu chuẩn thật: **"bộ an toàn 30/30"** (STATE.md §4, hiệu chuẩn trên
`gpt-4o-mini`, CHƯA chạy trên Qwen — tự khai là "tài sản lớn nhất dự án và đang chưa được xác nhận
trên model đang chạy"). Đây chính là cỡ mẫu dự án tự coi là đủ để nói "model này an toàn", không phải
6 ca.

**[ĐO] toán đơn giản, không cần mô hình phức tạp:** nếu một model có xác suất lỗi ẩn ~1/13 mỗi lượt
(đúng tỉ lệ livelock dự án ĐÃ ĐO được ở model đang dùng, §6.⓶ STATE.md — không phải con số giả định),
xác suất **6 ca ngẫu nhiên KHÔNG bắt được lỗi đó dù nó tồn tại** là khoảng **(12/13)^6 ≈ 62%**. Tức
cổng 6-ca có hơn MỘT NỬA khả năng cho một model mang đúng loại lỗi đã từng đánh sập một buổi demo đi
qua trót lọt.

**Đề nghị:** model MỚI vào bể phải qua **bộ 30 ca an toàn đã có sẵn** (không soạn ca mới — dùng lại),
không phải một bộ 6 ca riêng cho GĐ3. Đắt hơn về token, nhưng đây đúng chỗ đáng trả — model này sẽ
nói chuyện với khách thật không biết mình đang bị thử.

## ② Truy vết theo LƯỢT — [ĐO] Ý ĐỊNH ĐÚNG, cần xác nhận DÂY NỐI đủ trước khi merge

`llm_pool.py:1-7` tự khai: *"usage.jsonl vẫn ghi model PER-LƯỢT (không đổi) — đó là thứ cứu ta khi
đọc số sau này."* Đúng nguyên tắc cần — nhưng đây là Ý ĐỊNH viết trong docstring, tôi **chưa thấy**
dây nối thật (chỗ `run_agent_turn`/`_ghi_so` đổi từ đọc `LLM_MODEL` — hằng số module-level tĩnh —
sang đọc model THẬT SỰ được chọn cho lượt đó qua `model_dau_luot()`). **Điều kiện trước khi merge:**
QA/QC hoặc Review xác nhận bằng phép đo thật (không đọc code suông) — ép hai lượt liên tiếp xoay sang
hai model khác nhau (giả lập 403), rồi đọc `usage.jsonl` xác nhận trường `model` của hai dòng đó
**khác nhau, đúng model thật đã trả lời, không phải cùng một giá trị tĩnh**. Thiếu phép này thì khi
một model gây sự cố, sổ sẽ nói dối về AI nào đã nói câu đó — đúng loại "cổng chưa từng thật sự chạy"
đã gặp nhiều lần trong dự án (Luật J).

## ③ Cầu dao rút NHANH — không có UI khách để dựa vào nữa, ops phải nhanh hơn thay thế

Không còn tín hiệu "khách bực, khách báo" nào cả — **cổng GET-bể/log `model_rotated` là con mắt DUY
NHẤT** phát hiện một model đang có vấn đề. [ĐO] `llm_pool.py:52-61` (`danh_dau_can`) đã có sẵn cơ chế
Redis + TTL để đánh dấu MỘT model cạn — nhưng đó là do HỆ THỐNG tự phát hiện (lỗi hết ngạch), KHÔNG
phải nơi con người CHỦ ĐỘNG rút một model ra sau khi phát hiện vấn đề qua log/khiếu nại.

**Đề nghị rẻ, tái dùng CHÍNH cơ chế đã có, không xây gì mới:** thêm một cách gọi `danh_dau_can(model)`
thủ công (script vận hành, hoặc route nội bộ role cao) — dùng ĐÚNG khoá Redis `fin05:model_can:*` đã
tồn tại, TTL 15 phút hoặc dài hơn tuỳ ý khi gọi tay. Không cần sửa `.env` + recreate container (chậm,
đúng bẫy §9 STATE.md "sửa .env xong phải RECREATE mới có tác dụng") — một thao tác Redis trực tiếp là
đường rút NHANH duy nhất phù hợp với "không ai còn nhìn thấy khách đang gặp vấn đề gì".

## Điểm giữ nguyên, không đổi — để không phóng đại

Ràng buộc cứng (forbidden_tools, CHECK constraint DB cho HITL) **không phụ thuộc model đang xoay** —
model tệ nhất có thể làm là NÓI sai, không THỰC THI sai. Bề mặt rủi ro giới hạn ở tầng nội dung, đúng
như tôi đã ghi nhận lúc chuẩn bị GĐ3 (`2026-08-19-gd3-chuan-bi-truoc...md §1`). Đây là lý do tôi đề
nghị siết CỔNG VÀO BỂ + tốc độ rút ra, chứ không đề nghị chặn cả tính năng — rủi ro có trần, không
phải không đáy.

## KHÔNG kết luận

❌ tính năng xoay nên dừng lại — hướng và hạ tầng (Redis TTL, log sạch, fail-open có lý lẽ) đều đúng.
❌ 30 ca là đủ mãi mãi — đó là cỡ mẫu TỐT HƠN 6, không phải một con số thiêng; nếu sau này có ngân
sách/thời gian, một model phục vụ SUỐT NHIỀU NGÀY xứng đáng giám sát liên tục (③ đã gợi ý hướng đó
qua theo dõi tỉ lệ khớp O1-O4 theo từng model sau khi lên live), không chỉ một cổng một lần lúc vào.
