# FIN-05 — Hồ sơ vòng brainstorm tối ưu (vòng 2): trả lời 3 câu hỏi + phân tích ý kiến chuyên gia Amazon

- **Người viết:** chuyên gia tối ưu (qua Bách chuyển)
- **Người nhận:** PO-agent — lưu `docs/giao-viec/`
- **Ngày:** 17/08/2026
- **Quan hệ với tài liệu trước:** nối tiếp `FIN05-BaoCao-ToiUu-Token.md` (vòng 1) và các đính chính trong thread. Bản này ĐÃ SỬA theo ba lỗ tester tìm ra — chỗ sửa đánh dấu rõ.
- **Nhãn bằng chứng dùng trong file:** `[đo]` = số đội tự đo · `[tài liệu]` = tài liệu nhà cung cấp/nghiên cứu, có nguồn · `[suy luận]` = suy luận có căn cứ, chưa đo · `[chưa kiểm]` = cần tester xác minh trước khi dùng làm căn cứ.

---

# PHẦN A — Trả lời ba câu hỏi PO-agent gửi ngược

## A.1. Tiền lệ "cached token được trừ khỏi rate limit": CÓ, và ngành chia đôi

Hai nhà cung cấp lớn nhất đi hai hướng ngược nhau ⟹ không suy được từ "thông lệ ngành", phải kiểm đúng nhà mình dùng.

| Nhà cung cấp | Cached token có đếm vào trần? | Nguồn |
|---|---|---|
| Anthropic | KHÔNG (hầu hết model hiện hành): chỉ input + cache_creation đếm vào ITPM; ví dụ chính thức: 2M ITPM + 80% hit ⟹ ~10M token vào/phút thực tế | platform.claude.com/docs/en/api/rate-limits `[tài liệu]` |
| OpenAI | CÓ: "cached input tokens still count toward TPM; caching does not change rate-limit calculations" | developers.openai.com — prompt caching guide `[tài liệu]` |
| xAI | CÓ (giá giảm, trần vẫn đếm) | docs.x.ai/developers/rate-limits `[tài liệu]` |
| Alibaba | CHƯA RÕ — tài liệu Context Cache chỉ nói về GIÁ (implicit 20%, explicit 10% đơn giá); không câu nào miễn trừ TPM pay-as-you-go. Hệ số cache-quota tra được là của PTU — sản phẩm khác, trích cho ca mình là trích nhầm vật (tester đã chặn) | help.aliyun.com/en/model-studio/context-cache `[tài liệu]` + kết luận tester `[đo]` |

**Trạng thái sau điều tra của tester:** suy luận có căn cứ là "vẫn đếm" — nhưng lưu ý tinh vi: `cached_tokens` là tập con của `input_tokens` trong usage report chỉ nói về cách BÁO CÁO/TÍNH TIỀN, chưa nói về cách LIMITER ĐẾM (Anthropic cũng báo cached trong usage nhưng limiter loại ra). Ticket hỗ trợ là thứ khép hồ sơ. `[suy luận]`

**Hai chỉnh cho ticket đã gửi Bách:** (a) yêu cầu chỉ đúng điều khoản tài liệu ("please point to the specific documentation clause") — trả lời không kèm trích dẫn xử lý như nguồn cấp hai; (b) hỏi tách implicit vs explicit cache — hai loại có thể khác nhau, câu gộp sẽ mơ hồ.

**Đường đo dự phòng nếu ticket mơ hồ:** tài khoản thử nghiệm riêng (trần áp cấp tài khoản gốc `[đo]`), prompt tổng hợp không dữ liệu khách, bắn chuỗi cùng prefix vượt trần danh nghĩa của tài khoản đó — 429 hay không là câu trả lời. Caveat khai trước: xác nhận cùng region + cùng loại pay-as-you-go, tránh đo nhầm trên biến thể bị siết (bẫy snapshot đã ghi sổ). `[suy luận]`

**Cảnh báo hạ tầng (mới):** LiteLLM proxy — thứ đội định dựng — có lỗi đã báo cáo: bộ giới hạn TPM của LiteLLM đếm cả cached_tokens vào total_tokens, chặn người dùng sớm hơn nhà cung cấp thật (github.com/BerriAI/litellm/issues/18728). Kể cả khi Alibaba trả lời "có trừ", tầng proxy của mình có thể dựng lại cái trần đã gỡ. ⟹ đưa vào checklist nghiệm thu LiteLLM: kiểm cách limiter đếm cached token trước khi tin số của nó. `[tài liệu]`

**Trạng thái nhánh liên quan (theo phán quyết tester, giữ nguyên):** T2 (sắp xếp prompt ăn cache nhà cung cấp) là nhánh DUY NHẤT hoãn chờ câu trả lời — hoãn có điều kiện mở lại rõ (ticket, hoặc phép đo tài-khoản-thử), tránh "hoãn" trượt thành "quên". Mọi nhánh khác quyết được ngay và thứ tự không đổi.

## A.2. Điểm hòa vốn rolling summary với hội thoại 5-6 lượt: không có số công khai đáng tin — nhưng có một xung đột cấu trúc đủ để xếp xó

Thẳng thắn: không có benchmark công khai nào đo điểm hòa vốn này đủ chặt để trích. Nhưng có một tương tác mà báo cáo vòng 1 BỎ SÓT: **rolling summary và prompt caching xung đột trực diện** — cùng họ với xung đột 2.3/2.1. Lịch sử append-only là prefix ổn định (lượt sau trúng cache phần cũ); tóm tắt là VIẾT LẠI phần đầu ⟹ phá prefix ⟹ lượt kế trả giá full cho context mới, cộng thêm một lời gọi LLM để tóm tắt. Với hội thoại ngắn, gần như chắc chắn âm. `[suy luận]`

Thực hành chung ở sản phẩm CSKH: rolling summary chỉ xuất hiện ở hội thoại hàng chục lượt hoặc phiên nhiều ngày. Kết luận PO-agent (ghi sổ, chờ phân bố traffic thật) đúng — đề xuất điều kiện kích hoạt định lượng: chỉ mở lại khi p95 số lượt/hội thoại từ traffic thật vượt ~8-10, đo bằng sổ usage đã có.

## A.3. Schema-theo-trạng-thái chung sống với caching: có lời giải thực tế — bằng cách ĐẢO chiều

Lời giải phổ biến không phải "cắt schema khỏi prompt" mà là **giữ schema tĩnh trong prefix (ăn cache trọn), siết LỰA CHỌN ở đuôi động hoặc tầng API**:

1. **Siết bằng tham số API:** OpenAI/Anthropic có cơ chế tool_choice/allowed-tools giới hạn tool được gọi mà không đụng khối schema. Trên Anthropic, đổi tool_choice mất cache phần messages nhưng khối tools giữ cache — phần đắt nhất (6.773 ký tự schema) sống sót. Qwen có tương đương không: `[chưa kiểm]`.
2. **Siết bằng một dòng chỉ dẫn ở đuôi động** (~20 token, prefix nguyên vẹn). Yếu về cưỡng chế, nhưng FIN-05 có thứ đa số sản phẩm không có: **cổng cứng đã ở server** (authority matrix + OTP + INV) — model gọi nhầm thì server từ chối. Soft-gate ở prompt + hard-gate ở server là tổ hợp đủ.
3. Đội cắt schema thật thì hoặc cache riêng từng tổ hợp (chỉ đáng khi ít tổ hợp VÀ traffic giữ từng cache ấm trong TTL ~5 phút), hoặc hàng chục tool trở lên.

⟹ Phán quyết BÁC 2.3 ở quy mô 5 tool: đúng. Nếu sau này cần routing, đường 1-2 mở lại mà không phá cache — xung đột flag ở vòng 1 có lời giải, không phải chọn một trong hai.

**Ghi chú cho biến thể T2 đang chờ thiết kế:** timestamp động là thủ phạm phá cache kinh điển — nếu nghiệp vụ cho phép, đẩy hẳn thời gian ra khỏi prefix (truyền qua kết quả tool hoặc đuôi động) mạnh tay hơn là hạ độ phân giải, vì hạ xuống giờ vẫn phá cache mỗi giờ một lần, có thể đúng lúc traffic demo đang dồn.

## A.4. ĐÍNH CHÍNH của chuyên gia (theo ba lỗ tester tìm ra)

Câu "bảng so sánh của PO-agent đúng" trong phản hồi trước của chuyên gia là ký nhầm vào bảng xếp hạng một-trục. Sửa thành: **"bảng đúng ở trục lợi-ích-mỗi-lần-trúng; chưa xếp hạng được vì thiếu thừa số tỉ-lệ-trúng và thiếu trục rủi-ro-ngữ-nghĩa."** Kết luận sau sửa, đủ ba thành phần trúng × lợi ÷ rủi:

- Tầng phân luồng tất định: trúng 100% theo định nghĩa, rủi ~0 ⟹ đứng đầu lớp không-có-request (nhất trí với tester). `[đo]`
- Semantic cache: lợi-mỗi-lần-trúng cao nhất, nhưng tỉ lệ trúng CHƯA BIẾT (chế độ bóng sinh ra để đo) và mang rủi ro trục ③ (khách nhận câu trả lời của khách khác). Kiểm soát kiến trúc mạnh hơn ngưỡng similarity: đặt tầng cache TRƯỚC cổng OTP về kiến trúc — chỉ phục vụ lớp câu search_policy trả lời (chính sách công khai, không dữ liệu khách); lượt nào đã gọi tool nhạy cảm thì không đủ điều kiện GHI vào cache. Khi đó rủi ro ③ bị loại bằng vị trí, không bằng ngưỡng chỉnh được. Chế độ bóng đo thêm **tỉ lệ trúng-sai** (khác nghĩa nhưng vượt ngưỡng tương đồng — tiếng Việt CSKH đầy cặp "chuyển nhầm cho" / "bị chuyển nhầm cho"), không chỉ tỉ lệ trúng. `[suy luận]`
- Quy luật rút ra dùng cho đề xuất sau: **cơ chế tất định luôn thắng cơ chế xác suất cùng lớp** — tất định thì trúng = 100% theo định nghĩa và rủi ~0 vì kiểm được bằng test thường.

---

# PHẦN B — Phân tích ba ý của chuyên gia Amazon

## B.1. Rule-base trước LLM

Đã ship và đo (−33,5% tất định, "alo" = 0 token) `[đo]`. Giá trị mới duy nhất: tiền lệ ngành cho slide pitch — thực hành chuẩn là xếp lớp rule-based trước, classifier giữa, cascade cuối (nguồn: digitalapplied.com — LLM Model Routing 2026). Không phát sinh việc.

## B.2. Model tiering — NHẬN, kèm XOAY TRỤC

**Nghiên cứu nền có thật:** RouteLLM (UC Berkeley, ICLR 2025) ~85% giảm chi phí trên MT-Bench, giữ 95% chất lượng GPT-4, chỉ 14% câu lên model mạnh; FrugalGPT (Stanford) tới 98% qua cascade. `[tài liệu]`

**Caveat ngành khớp chính xác số của đội:** MT-Bench là benchmark hội thoại mở, KHÔNG phải tác vụ agent có cấu trúc (tool call, JSON schema, chuỗi nhiều bước) — nơi lỗi routing lan thành lỗi pipeline; phải tự kiểm trên đúng loại tác vụ của mình (nguồn: openlegion.ai/en/learn/llm-routing). Số của đội đã nói cùng điều đó: flash 84% bước đơn / 0-15 chuỗi hai bước. `[đo]`

**Xoay trục:** route theo LOẠI BƯỚC trong pipeline (biết chắc, tất định) thay vì ĐỘ KHÓ CÂU HỎI (đoán, xác suất) — áp dụng quy luật A.4. Bước quyết-định-gọi-tool + chuỗi nhiều bước: model mạnh. Ứng viên hạ tầng: bước đơn-lượt-không-tool (vd. soạn câu trả lời cuối khi kết quả tool đã đủ — trùng chỗ đề xuất tắt thinking). Flash trượt ở CHUỖI, chưa bị kết án ở BƯỚC-ĐƠN-CUỐI-CHUỖI — ô chưa đo, thí nghiệm rẻ, chấm bằng bộ nghiệm thu nguyên ngưỡng. `[suy luận]`

**Phát hiện thông lượng (mới, trục thông lượng):** trần TPM Model Studio áp THEO TỪNG MODEL ⟹ mỗi model được route là một bucket riêng — routing CỘNG bucket, khác hẳn prompt caching (đã hạ hạng). Chính tài liệu Alibaba khuyến nghị chuyển model dự phòng khi rate limit để tăng thông lượng — nhà cung cấp tự thừa nhận pattern nhiều-bucket (alibabacloud.com/help/en/model-studio/rate-limit). Bucket có độc lập thật không: `[chưa kiểm]` — tester đang kiểm cùng đợt ticket cache-TPM.

**Cảnh báo an ninh riêng FIN-05 (trục rủi ro):** router theo độ-khó-câu là bề mặt tấn công — tài liệu ngành ghi dạng lỗi "câu chế tác để trông đơn giản bị route nhầm sang model yếu"; với sản phẩm mà loại gian lận số một là social engineering, kẻ gian chủ động viết tin "trông dễ" để được model yếu (dễ lách ràng buộc hơn) tiếp. **Kẻ gian điều khiển được NỘI DUNG câu hỏi — không điều khiển được VỊ TRÍ bước trong pipeline.** Đây là lý do an toàn thứ hai, độc lập, cho trục-theo-bước. `[suy luận]`

## B.3. "Research inference optimization" — khoanh phạm vi trước khi research

Phần lớn văn liệu (quantization, speculative decoding, continuous batching, PagedAttention/vLLM, KV-cache management) dành cho người TỰ HOST trên GPU riêng — FIN-05 thuê API, các tối ưu đó là việc của Alibaba. Tập con dùng được cho người thuê API: routing/cascade (B.2), caching (đã phân xử), giảm token tuyệt đối (đã ship), siết output/thinking (chờ k>1), và:

**Batch API — tách traffic đánh giá khỏi bucket TPM sản xuất.** Alibaba batch inference: 50% giá real-time cả input lẫn output, API tương thích OpenAI, tự mô tả là lý tưởng cho model evaluation và data labeling, chỉ tính tiền request thành công (help.aliyun.com/en/model-studio/batch-inference). `[tài liệu]` Giá trị thật với FIN-05 không phải 50% tiền — mà là gỡ traffic eval khỏi con đường mà 150 người sẽ đi.

**Khoanh vùng của PO-agent (nhận vào hồ sơ):** eval chạy qua VÒNG LẶP AGENT là real-time theo bản chất (mỗi bước chờ bước trước) — batch chỉ ăn được lời gọi ĐỘC LẬP: giám khảo chấm, gán nhãn, chạy lại phân loại đơn bước. Khai trước để không ai ước tiết kiệm trên toàn bộ eval rồi thất vọng ở một nửa.

**Caveat batch:** không dùng được context cache (không sao — cache đã hạ hạng); một số model bật thinking mặc định trong batch, sinh token tính tiền — chỉnh enable_thinking theo tác vụ; danh sách model hỗ trợ batch trong tài liệu đã đọc dừng ở qwen3.7-max — qwen3.8-max có hỗ trợ không: `[chưa kiểm]`, tester đang kiểm.

**Ý brainstorm nối tiếp cho phần eval agent-loop không batch được** `[suy luận — chưa kiểm điều khoản]`: toàn bộ dataset là mô phỏng (60k giao dịch tổng hợp, không byte dữ liệu khách thật) ⟹ rào residency/PII không tồn tại ⟹ eval agent-loop về nguyên tắc chạy được trên tài khoản/workspace tách riêng (cùng logic phép đo trần tài-khoản-thử ở A.1). Caveat PHẢI kiểm trước: điều khoản Alibaba về nhiều tài khoản cùng tổ chức — cách ly tải khác bản chất với né trần, nhưng ranh giới do nhà cung cấp định nghĩa. Nếu điều khoản không cho: phương án hạ cấp là lịch eval lệch giờ demo + siết concurrency.

---

# PHẦN C — Bảng tổng kết trạng thái các nhánh sau vòng 2

| Nhánh | Trạng thái | Điều kiện thay đổi |
|---|---|---|
| Phân luồng tất định (T1) | ✅ ship, −33,5% `[đo]` | — |
| Nén tool result qua tool_result_id | 🟢 coder đo phân bố payload | có số thì xếp hạng |
| Invariant ngân sách token CI | ✅ xong (ngưỡng 7.550, cảnh báo 90%) | gợi ý thêm: in headroom mỗi lần chạy để thấy xu hướng phình trước mốc cảnh báo |
| T2 — prompt ăn cache nhà cung cấp | ⏸ hoãn CÓ ĐIỀU KIỆN | ticket Alibaba HOẶC phép đo tài-khoản-thử |
| T3 — thinking k=1 (−11%) | 🟡 chờ k>1 | — |
| Nén mô tả tool | 🟡 xếp sau F-31/32 | gỡ mâu thuẫn ADR-029 mục 4 trước, tránh trộn biến |
| Tool routing theo trạng thái (2.3) | ❌ bác ở 5 tool | mở lại qua đường tool_choice/đuôi-động (A.3), không phá cache |
| Rolling summary | 🟡 ghi sổ | p95 lượt/hội thoại > ~8-10 từ traffic thật |
| Semantic cache | 🟡 chế độ bóng | đo tỉ lệ trúng + tỉ lệ TRÚNG-SAI; kiến trúc trước-cổng-OTP |
| Model tiering theo bước | 🆕 thí nghiệm mở | flash cho bước-đơn-cuối-chuỗi, bộ nghiệm thu nguyên ngưỡng; bucket TPM độc lập `[chưa kiểm]` |
| Batch API cho eval độc lập | 🆕 nhận, đã khoanh vùng | danh sách model hỗ trợ `[chưa kiểm]` |
| Eval agent-loop tách tài khoản | 🆕 ý brainstorm | kiểm điều khoản Alibaba trước |

---

*Hết hồ sơ vòng 2. Nguyên tắc làm việc rút ra từ vòng này, đề nghị giữ cho các vòng sau: (1) mọi phát biểu xếp hạng kèm một dòng khai trục — "xếp trên trục X, chưa xét trục Y"; (2) cơ chế tất định thắng cơ chế xác suất cùng lớp; (3) mọi cơ chế mới cần ca kiểm cả hai chiều — kích hoạt đúng VÀ không kích hoạt nhầm.*
