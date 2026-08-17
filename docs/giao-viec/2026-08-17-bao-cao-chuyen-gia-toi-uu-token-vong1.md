# FIN-05 — Báo cáo đề xuất: Tối ưu token như bài toán THÔNG LƯỢNG

- **Người gửi:** Bách (PO thật)
- **Người nhận:** PO-agent
- **Ngày:** 17/08/2026
- **Nguồn số liệu:** `06-TRANG-THAI-HIEN-TAI.md`, `04-contract-agent-tools.yaml`, ADR-027 — mọi con số dưới đây trích từ số đội đã tự đo, không có số mới. Nếu con số nào đã đổi sau 17/08, số trong repo thắng báo cáo này.
- **Tính chất:** ĐỀ XUẤT để phân xử, chưa phải quyết định. Mọi mục đều tuân quy trình §3 (ADR trước, code sau) và không nới bất kỳ ngưỡng nghiệm thu nào đã chốt.

---

## 0. Định lại bài toán (khung cho toàn bộ báo cáo)

Đội đã tự kết luận: **tiền chưa bao giờ là vấn đề (~$10/tuần), trần TPM mới là thứ chặn đích 100 CSKH.** Vậy "tối ưu token" cho FIN-05 KHÔNG phải bài toán tiết kiệm chi phí — nó là bài toán **thông lượng**: mỗi token đầu vào cắt được quy đổi trực tiếp thành lượt/phút dưới cùng một trần TPM.

Quy đổi bằng chính số đã đo:

| Kịch bản | Token/lượt | Lượt/phút @ 1M TPM (qwen3.8-max) |
|---|---|---|
| Hiện tại (hội thoại mới) | 15,4k | ~65 |
| Sau tối ưu (mục tiêu) | ~10k | ~100 |
| Đích cần cho 150 người | — | 75 |

Nghĩa là: cắt ~35% token/lượt thì **vượt đích 75 lượt/phút mà không cần mua thêm hạn mức**. Đây là thước để xếp ưu tiên mọi việc bên dưới, và cũng là lý do các đề xuất này KHÔNG mâu thuẫn với thứ tự đầu tư PO thật đã chốt (nâng TPM → LiteLLM → reranker → Qdrant) — chúng lồng vào, không thay thế.

---

## 1. Câu hỏi ưu tiên số 1 — quyết định cả chiến lược, chi phí một email

> **Token cache-hit có được TRỪ khỏi TPM không, hay chỉ giảm tiền?**

Đội đã đo cache 85% (trên gpt-4o-mini) và biết giá cached của qwen3.7-plus rẻ 5×. Nhưng nếu Alibaba vẫn đếm cached token vào TPM thì prompt caching **không giải quyết bài toán thật** của đội (thông lượng), chỉ giải bài toán không tồn tại (tiền). Ngược lại nếu cached token được miễn/giảm khi đếm TPM thì caching nhảy lên đầu danh sách, trên mọi việc khác.

- **Đề xuất:** tester tra tài liệu chính thức Alibaba Model Studio (vùng Singapore, bản STABLE — tránh bẫy snapshot đã ghi) + xác minh bằng **một lượt gọi thật** đọc header/usage, đúng nếp "GỌI THẬT một lượt rẻ nhất, không liệt kê /models".
- **Đầu ra:** một dòng kết luận có nguồn, ghi vào `06-TRANG-THAI-HIEN-TAI.md`.

---

## 2. Tầng system prompt & schema tool (~13,1k token, nhân với 2,39 lời gọi/lượt)

### 2.1. Tái cấu trúc prompt theo thứ tự tĩnh-trước-động-sau (ăn cache)

Phần tĩnh tuyệt đối (hiến pháp agent, 5 ràng buộc cứng, schema 5 tool) đặt ở ĐẦU prompt; phần động (lịch sử hội thoại, kết quả tool, ngữ cảnh phiên) đặt ở CUỐI. Bất kỳ byte động nào chen giữa phần tĩnh sẽ phá cache từ điểm đó trở đi.

- **Rủi ro:** đổi thứ tự prompt là đổi kích thích ⟹ phải chạy lại bộ nghiệm thu (47 ca + ca chuỗi nhiều bước), ngưỡng giữ nguyên, An toàn không tụt một điểm.
- **Điều kiện tiên quyết:** mục 1 trả lời xong. Nếu cache không trừ TPM, việc này tụt hạng (vẫn đáng làm vì tiền, nhưng không còn khẩn).

### 2.2. Nén mô tả tool — có đo, không cắt mù

Schema 5 tool = 6.773 ký tự, trả lại mỗi lời gọi. ADR-027 vừa dạy bài học chiều ngược (mô tả nghèo 31 ký tự làm 3 model độc lập từ chối `create_ticket`) — nên đây KHÔNG phải đề xuất cắt tối đa, mà là tìm điểm giữa:

- `create_ticket` mô tả 1.266 ký tự, `request_human_handoff` 1.176 ký tự cho tool chỉ 2 tham số — có khoảng nén.
- **Cách làm đúng quy trình:** (a) sửa `contracts/agent-tools.yaml` TRƯỚC (contract đi trước, lần này không có ngoại lệ kiểu ADR-027); (b) A/B bản nén vs bản hiện tại trên đúng bộ nghiệm thu, **bắt buộc có ca chuỗi nhiều bước** (bài học flash 84% bước đơn / 0-15 chuỗi); (c) hỏng định dạng = 0, không gọi tool = trượt, không nới.
- **Lưu ý ràng buộc INV-09:** mọi thay đổi mô tả phải giữ contract khớp app; test so lược đồ (hệ quả ADR-027) phải xanh.

### 2.3. Nạp schema tool theo trạng thái (tool routing) — đề xuất cần phân xử

Không phải lượt nào cũng cần cả 5 schema. Khách đang hỏi chính sách chung chưa cần `create_ticket` đầy đủ. State machine của resolution đã tồn tại làm trục routing.

- **Ước lượng:** cắt 30–50% phần schema ở các lượt sớm của hội thoại.
- **Phản biện cần cân trước khi làm:** (a) routing sai = tool "biến mất" đúng lúc cần ⟹ họ lỗi im lặng mới; (b) mỗi tổ hợp schema là một prefix cache khác nhau ⟹ có thể LÀM GIẢM tỉ lệ cache-hit của mục 2.1 — hai đề xuất này giằng nhau, chỉ nên chọn một làm trước và đo. **Đề nghị PO-agent phân xử thứ tự.**

---

## 3. Tầng lịch sử hội thoại & kết quả tool (thứ phình theo độ sâu: 15,4k → 25,7k ở lượt 4)

### 3.1. Nén kết quả tool trong context, dựa trên kiến trúc truy vết SẴN CÓ

Đây là chỗ kiến trúc chống-bịa-số của đội và tối ưu token **cộng hưởng thay vì mâu thuẫn**: bản đầy đủ (`raw_json` + `content_hash`) đã nằm trong bảng `tool_results`, mọi kết luận trích qua `tool_result_id`. Nghĩa là thứ đưa vào context model chỉ cần **bản rút gọn kèm tool_result_id** — audit đối chiếu bằng DB, không bằng context.

- Ví dụ: `get_customer_history` trả 20 giao dịch JSON thô → context chỉ cần bảng tối giản (mã · ngày · số tiền · trạng thái · tool_result_id).
- **Ràng buộc cứng 3 giữ nguyên vẹn:** con số model phát biểu vẫn đến từ kết quả tool trong chính lượt đó — chỉ là bản trình bày gọn hơn của cùng kết quả, cùng hash gốc.
- **Việc cho coder (sau khi có ADR):** thêm tầng "trình bày cho model" ở đầu ra tool, tách khỏi tầng "lưu sổ". Che PII vẫn ở tầng tool (masking.py) TRƯỚC tầng trình bày — thứ tự này không được đảo.

### 3.2. Tóm tắt cuốn chiếu (rolling summary) cho hội thoại dài

Sau N lượt, thay lịch sử cũ bằng tóm tắt có cấu trúc: loại khiếu nại đã phân loại · scope · tool đã gọi + tool_result_id · điều khách đã xác nhận.

- **Ràng buộc thiết kế bắt buộc:** bản tóm tắt KHÔNG được chứa con số nào không kèm tool_result_id — nếu không, chính bản tóm tắt thành nguồn bịa số ở lượt sau (đúng chỗ "bị chặn, không có dữ liệu, vẫn phải trả lời khách" mà tester đã đánh dấu là điểm dễ đẻ bịa-số nhất).
- **Chi phí ẩn phải khai:** tóm tắt tự nó tốn một lời gọi LLM. Chỉ lãi khi hội thoại đủ dài — cần đo điểm hòa vốn (gợi ý: chỉ kích hoạt từ lượt 4–5 trở đi, đúng chỗ số đo cho thấy phình).

---

## 4. Tầng token đầu ra — 77% output của qwen3.8-max là suy nghĩ thầm

Đội đã biết hai bẫy (trả lời rỗng im lặng · reasoning_tokens tính vào output làm mọi ước tính chi phí ước THẤP). Hướng xử lý KHÔNG phải siết `max_tokens` (sẽ gặp `TraLoiRongError` thường xuyên hơn — đã ghi trong hệ quả chọn max):

- Nếu API cho tham số thinking theo lời gọi: siết/tắt thinking ở các bước **đơn giản đã biết trước** (vd. bước soạn câu trả lời cuối khi kết quả tool đã đủ), giữ nguyên ở bước quyết định gọi tool.
- Ép output có cấu trúc ngắn ở các bước trung gian ReAct thay vì văn xuôi.
- **Điều kiện:** mọi thay đổi ở đây chạy lại nghiệm thu đầy đủ — flash đã chứng minh "rẻ 5,7×" có thể đổi bằng "0/15 chuỗi hai bước".

---

## 5. Giảm SỐ lời gọi, không chỉ token/lời gọi (2,39 lời gọi/lượt đã đo)

Mỗi lời gọi bớt được = bớt nguyên một lần trả prompt ~13k.

1. **Semantic cache cho câu chính-sách-chung** — đã có trong lộ trình (mục ⑤ sau gate), báo cáo này chỉ đề nghị giữ đúng hẹn pilot, không đề xuất mới.
2. **Định tuyến tất định trước LLM:** những gì rule làm được thì làm trước khi chạm model — nhận diện mã TXN trong tin nhắn, chặn sớm khi thiếu OTP phiên. Đội đã có tiền lệ tốt (`_phan_loai_tier` cho injection). Tín hiệu tất định và rẻ, cùng họ với "rerank có chọn lọc" đã ghi sổ.
3. **Ngưỡng cảnh báo bước ReAct:** trần 20 bước là trần kỹ thuật; đề xuất ngưỡng mềm (vd. >6 bước → cân nhắc human handoff) vì lượt 36k token gần như chắc là lượt agent loay hoay. Con số 6 là đề xuất để phân xử, không phải số đo.

---

## 6. Dài hạn — biến tối ưu token thành kỷ luật vận hành (cho ví điện tử thật)

1. **Token budget thành BẤT BIẾN kiểm được** — đúng văn hóa invariant của đội: CI đo kích thước system prompt + schema, vượt ngưỡng đã chốt → ĐỎ. Prompt phình 500 token vì ai đó thêm một đoạn hướng dẫn là drift im lặng cùng họ ADR-027 — không ai thấy cho tới khi thông lượng tụt. Đề xuất mã: INV mới, tester đặt ngưỡng từ số đo hiện tại + biên độ.
2. **Đơn vị đo so được giữa nhà cung cấp:** giữ và mở rộng nếp `input_chars` / `$/1000 ký tự vào` — token hai nhà không cùng đơn vị (2,43 ký tự/token là số của gpt-4o-mini, sẽ khác trên Qwen với tiếng Việt; mệnh đề "Qwen tiếng Việt tốt hơn" vẫn CHƯA kiểm được, cấm trích). Mọi báo cáo tối ưu nên phát biểu bằng **ký tự + lượt/phút**, không phải token trần.
3. **Bảng giá có hạn dùng:** cơ chế "cảnh báo khi bảng giá quá N ngày" đã giao tester — đề nghị áp cùng cơ chế cho **bảng trần TPM/RPM** (trần cũng là một loại nhãn-vật, đổi mà không ai biết thì mọi ước tính thông lượng sai im lặng).

---

## 7. Ba việc đầu tiên đề xuất (xếp theo tỉ lệ lợi/công)

| # | Việc | Chi phí | Vì sao trước |
|---|---|---|---|
| 1 | Xác minh cache-hit có trừ TPM không (mục 1) | 1 tra cứu + 1 lượt gọi thật | Quyết định thứ hạng của mọi việc còn lại |
| 2 | Tái cấu trúc prompt tĩnh-trước-động-sau (mục 2.1) | 1 đợt nghiệm thu | Ăn cache tối đa, không đổi nội dung — chỉ đổi thứ tự |
| 3 | Nén kết quả tool trong context qua tool_result_id (mục 3.1) | ADR + việc coder vừa | Kiến trúc đã sẵn 90%, chỉ thiếu tầng trình bày; đánh đúng chỗ phình theo độ sâu |

**Không đề xuất làm ngay:** tool routing theo trạng thái (mục 2.3 — giằng với cache, chờ phân xử) · rolling summary (mục 3.2 — chờ đo điểm hòa vốn) · chỉnh thinking budget (mục 4 — chờ xác nhận API hỗ trợ).

---

## 8. Điều báo cáo này KHÔNG đề xuất

- Không đổi model, không lùi model, không nới bất kỳ ngưỡng nghiệm thu nào.
- Không đụng embedding (đổi embedding = đổi VẬT, nạp lại kho — đã chốt tách chat khỏi embedding).
- Không thay thế thứ tự đầu tư PO thật đã chốt — các việc trên lồng vào giữa các mốc đó.
- Không phát biểu con số đo mới nào: mọi số trong báo cáo là số đội đã đo hoặc quy đổi số học từ số đã đo; chỗ nào là ước lượng đã ghi rõ là ước lượng.

*Hết báo cáo. Đề nghị PO-agent phân xử mục 2.3 và ngưỡng ở mục 5.3, giao tester mục 1, và cho ý kiến có cần ADR riêng cho mục 3.1 hay gộp vào ADR truy vết đang mở.*
