# Ý kiến tuân thủ — agent diễn giải điều khoản pháp lý vs "không tra được"

> Vai: **security/tuân thủ** · 2026-08-16 · trả lời câu ② của PO cho mặt trận ToS.
> Mệnh đề cần xác nhận/bác:
> *"Agent tự diễn giải điều khoản pháp lý SAI còn rủi ro hơn là trả lời
> 'không tra được' + escalate người thật."*

## XÁC NHẬN — và bất đối xứng còn mạnh hơn cách phát biểu

Hai nhánh **không cùng hạng rủi ro**:

| | Trả lời sai về điều khoản | "Không tra được" + escalate |
|---|---|---|
| Bản chất | **phát ngôn về nghĩa vụ hợp đồng** | **trì hoãn** một câu trả lời |
| Ai gánh | nhà cung cấp **và** khách | khách chờ thêm |
| Đảo ngược được? | **thường KHÔNG** — xem §2 | có, người thật trả lời tiếp |
| Nằm trong thiết kế? | **KHÔNG** | **CÓ** — đúng đường HITL đã dựng |

## 1. Vì sao "sai" ở đây nặng hơn "sai" thông thường

ToS là **hợp đồng theo mẫu** giữa nhà cung cấp và người dùng. Phát ngôn của
agent về nó **không phải thông tin tham khảo** — nó là nhà cung cấp **nói về
nghĩa vụ của chính mình**, qua một kênh chính thức, có lưu vết.

Ba điều khoản nặng nhất, đúng những chỗ khiếu nại chạm tới:

- **Điều 19 (tra soát và khiếu nại)** — nói sai **thời hạn** khiếu nại có thể
  khiến khách **mất quyền** khiếu nại. Đây là thiệt hại **không đảo ngược
  được**: khách tin, không nộp đúng hạn, hết thời hiệu.
- **Điều 15 (giới hạn trách nhiệm)** · **Điều 13 (bồi hoàn)** — nói sai **ai
  chịu tiền**. Sai theo hướng **có lợi cho khách** thì nhà cung cấp có thể bị
  ràng buộc bởi chính phát ngôn đó; sai theo hướng **bất lợi cho khách** là
  tước quyền của người tiêu dùng.
- **Điều 8 (nghi ngờ gian lận)** — chạm **ràng buộc cứng 5** (cờ gian lận ≠
  khoá ví). Nói sai ở đây làm khách hiểu nhầm về tình trạng ví của họ.

Thêm một vế **của chính hiến pháp dự án**: một diễn giải **không truy được về
đoạn văn bản đã trích** chính là **bịa** — vi phạm **ràng buộc cứng 3**, bất kể
nội dung diễn giải nghe hợp lý đến đâu.

## 2. Vì sao "không tra được" là nhánh AN TOÀN — nó nằm trong thiết kế

Hệ thống này được dựng trên nguyên tắc **agent điều tra, không quyết định**
(ràng buộc cứng 1) và **HITL tuyệt đối**. "Không tra được → chuyển người thật"
**không phải chế độ hỏng — nó là đường đi đã thiết kế**, và nó đã có người thật
đứng cuối.

⟹ Nhánh từ chối **tiêu hao thời gian**; nhánh diễn giải sai **tạo ra một phát
ngôn pháp lý** mà hệ thống **không có cơ chế nào thu hồi**.

## 3. ⚠️ NHƯNG — xác nhận mệnh đề KHÔNG có nghĩa là chấp nhận truy hồi ToS hỏng

Đây là chỗ mệnh đề dễ bị dùng sai, nên tôi ghi rõ ranh giới:

> Mệnh đề trên hợp lệ như một **thứ tự ưu tiên rủi ro**. Nó **KHÔNG** là lý do
> để **ToS 2/10 trở thành trạng thái chấp nhận được**.

Ba lý do:

1. **Từ chối quá tay có giá thật.** Đội đã điều tra over-refusal (H2/H3) và
   chốt "agent đúng" — nhưng đó là kết luận cho **một** ca, không phải giấy
   phép để từ chối rộng. Một agent CSKH trả lời "không tra được" cho phần lớn
   câu hỏi điều khoản là **một sản phẩm không dùng được**, và người dùng sẽ
   ngừng hỏi thay vì escalate.
2. **Escalate không miễn phí ở quy mô.** Đường an toàn chỉ an toàn khi **có
   người thật đủ để nhận**. 2/10 nghĩa là phần lớn câu hỏi điều khoản dồn sang
   người — đúng góc năng lực TPM/nhân sự đã ghi cho đợt 150 người.
3. **Nó hoãn được, nhưng không hoãn vô hạn.** ToS là **phần ràng buộc pháp lý**
   của kho tri thức, và sản phẩm này **chỉ làm tranh chấp**. Một thước truy hồi
   mù ở ToS là mù đúng phần nặng ký nhất (đã nêu ở
   `2026-08-16-soi-truc-thieu-golden-set-truy-hoi.md` §B).

## 4. Kết luận cho benchmark

**Ghi ToS 2/10 thành "giới hạn ĐÃ BIẾT, có đường an toàn" là ĐÚNG** — với ba
điều kiện, nếu không nó thành "giới hạn đã biết và đã quên":

1. **Đường an toàn phải ĐO ĐƯỢC, không phải giả định.** Cần bằng chứng rằng ở
   8/10 ca hỏng, agent **thật sự** trả "không tra được" + escalate — **chứ
   không** tự diễn giải từ chunk gần đúng. **Đây là ca tôi lo nhất**: truy hồi
   trả **chunk lân cận nhưng sai** với điểm cao thì agent **không biết** là nó
   đang thiếu dữ liệu — nó tưởng đã tìm thấy. Trùng đúng trục **âm-bản-GẦN**
   tôi đã nêu (§A cùng hồ sơ) và **hiện chưa có ca nào canh**.
2. **Ghi kèm ngày và mốc đóng** (trước pilot người thật) — giới hạn không có
   hạn là giới hạn vĩnh viễn.
3. **Ghi rõ nó là giới hạn của TRUY HỒI, không phải quyết định sản phẩm** rằng
   agent không trả lời điều khoản.

⟹ Một câu cho benchmark: *"ToS 2/10 — giới hạn đã biết của tầng truy hồi. An
toàn về tuân thủ **vì và chỉ vì** đường thoát 'không tra được → người thật' đã
được xác nhận hoạt động ở các ca này; **chưa** an toàn về khả dụng."*

**Vế "và chỉ vì" là phần tôi không nhân nhượng**: nếu điều kiện 1 chưa được đo,
thì mệnh đề an-toàn-tuân-thủ **chưa đứng** — nó mới chỉ là mong đợi.
