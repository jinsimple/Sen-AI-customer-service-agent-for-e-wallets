# FINDING NÓNG — tuyên bố kết quả điều tra KHÔNG kèm tool call (deepseek-v4-pro-0813, ca D1, 2/2)

🔴 **NIÊM 20/08 (lần hai) — dòng "3/3 ca đạt" ở niêm CŨ NGAY DƯỚI ĐÂY KHÔNG TRUY ĐƯỢC VỀ VẬT CHỨNG
NÀO. Đọc mục MỚI NHẤT bên dưới trước, đừng dừng ở niêm cũ.**

> **CÒN MỞ tính tới 20/08.** [ĐO] QA/QC rà hết `eval/results/` + `docs/security/`: khẳng định "3/3
> đạt" **không nằm trong bất kỳ file nào** — không trong kết quả eval, không trong chính file này
> (đọc trọn tới cuối, dừng ở "QA/QC đang sửa script và chạy lại cả 6 ca", không có dòng ghi kết quả).
> Nó tồn tại CHỈ DƯỚI DẠNG TIN NHẮN. Ba ca còn lại CHƯA CHẠY. **Không chạy lại lúc này** — hạn ngạch
> đang khan, ưu tiên phục vụ khách. [ĐO] thêm: `mtime` trong `eval/results/` KHÔNG dùng làm mốc thời
> gian được — cả thư mục mang chung dấu do một lần rebuild reset, ai lấy mtime ở đó sẽ đọc ra một
> dòng thời gian không có thật.

🔴 **BÀI HỌC, ghi tại đây vì nó lớn hơn finding này:** một kết quả chỉ sống trong tin nhắn KHÔNG PHẢI
một kết quả — không mẫu số, không thời điểm, không ai chạy lại được, nhưng LAN ĐI y hệt một kết quả
thật (chính niêm 20/08 lần một ngay dưới đây đã chuyển tiếp con số "3/3" như thể nó là dữ kiện).
**Luật: kết quả đo phải rơi vào một FILE trước khi được phép đi vào một CÂU.** Khác sáu lần trôi-hạn
trong ngày (trạng thái từng đúng rồi hết hạn) — lần này là trạng thái CHƯA TỪNG tồn tại ở dạng tra
được, không chữa được bằng thu dọn sổ, chỉ chữa được bằng luật trên.

---

🟡 **NIÊM 20/08 (lần một, ĐÃ BỊ VƯỢT QUA bởi mục trên — giữ lại làm bằng chứng cho chính bài học vừa
ghi, đừng đọc như hiện trạng):** Trạng thái cuối là "TẠM ĐÓNG, chờ đo lại sạch" (niêm dưới đây). QA/QC
báo 3/3 ca đạt với script sửa (mỗi lượt `user_id` riêng), đang chờ ngân sách cho 3 ca còn lại — kết
quả 6/6 cuối cùng CHƯA XÁC NHẬN được ở đây. PO-agent đang hỏi QA/QC trực tiếp (vùng của họ, không
đoán). Khi có câu trả lời, niêm ĐÓNG THẬT sẽ vào đúng chỗ này.

> 19/08/2026, giữa lúc cổng nhập bể GĐ3 đang chạy. QA/QC đã dừng, Lead chuyển định hạng. Trả lời
> nhanh nhưng có kiểm — không suy đoán trên mô tả, đã kiểm 2 điểm được ngay từ trong repo trước khi
> trả lời (không chạm phép đo QA/QC đang giữ).

## 🔴 NIÊM 19/08 (ngay sau) — TIỀN ĐỀ "2/2" SAI. TẠM ĐÓNG, chờ đo lại sạch. KHÔNG xoá thân dưới — đọc kèm phần này trước khi trích bất cứ câu nào ở dưới.

**[ĐO] Lead + QA/QC báo, tôi tự kiểm lại cơ chế (không nhận suông):** `grep -n "thread_id or
user_id" src/agents/graph.py` → khớp tại `:222,685,732,744,766` — xác nhận đúng: thiếu `thread_id`
truyền vào thì **mặc định = `user_id`**. Script chẩn đoán của QA/QC dùng `user_id="USR-A"` HARDCODE ở
MỌI lượt, không truyền `thread_id` riêng ⟹ **cả 4 lượt (nhẹ · nặng deepseek ×2 · qwen chẩn đoán) rơi
vào CÙNG MỘT thread LangGraph**, checkpointer Postgres sống ngoài process. Lượt ĐẦU TIÊN **THẬT SỰ có
gọi tool** (`so_tool_call=1`) và nhận kết quả thật "chưa thấy giao dịch nào" — mọi lượt sau **NHỚ
ĐÚNG** kết quả đó từ lịch sử hội thoại, đúng hành vi của một hệ thống CÓ TRẠNG THÁI, không phải bịa.

**Không phải "2/2 độc lập" — là MỘT phép đo, lặp lại ba lần trên cùng một câu trả lời đã cache trong
state hội thoại.** Câu hỏi gốc ("model có gọi tool đúng khi cần, trong một hội thoại SẠCH, cô lập
thread") **vẫn CHƯA có câu trả lời** — không phải đã trả lời NO, chỉ là chưa đo được vì lỗi thiết kế
script, không phải lỗi sản phẩm.

**PHẦN GIỮ NGUYÊN GIÁ TRỊ, không phụ thuộc vụ thread:** lập luận *"O3 không bắt được câu này"* và
*"cổng nhập bể là cơ chế duy nhất hiện có đủ khả năng bắt loại lỗi này (nếu nó có thật)"* — cả hai
đúng bất kể kết quả đo lại. Khung ③ (ngắn hạn: nếu tái diễn thì loại model / dài hạn: ghi sổ nợ O5)
**vẫn giá trị dưới dạng CHUẨN BỊ SẴN**, nhưng KHÔNG có căn cứ để thi hành "loại model" cho tới khi có
kết quả đo sạch — thân bài dưới đây viết trên tiền đề đã đổ, đọc như MỘT PHÂN TÍCH GIẢ ĐỊNH ("nếu
điều này là thật thì..."), không phải một kết luận đã xác nhận.

QA/QC đang sửa script (mỗi lượt `user_id` riêng, có cả một tài khoản CÓ giao dịch thật để phân biệt
"không gọi tool" khỏi "gọi tool nhưng đọc sai kết quả" ngay trong lần đo đầu) và chạy lại cả 6 ca.

## Xác nhận khung của Lead: ĐÚNG, đây là ràng buộc cứng, không phải "lỗi gate thông thường"

CLAUDE.md §2, ràng buộc cứng 3 dùng nguyên văn cả ba loại đại lượng: *"số tiền/TRẠNG THÁI/thời
điểm"*. "Chưa thấy giao dịch nào trong 90 ngày" là một khẳng định TRẠNG THÁI (kết quả điều tra), đúng
loại ràng buộc cứng 3 nêu tên tường minh — không cần suy diễn để xếp nó vào đây.

**[ĐO] xác nhận O3 không bắt được, đúng như Lead nói.** `output_filter.py:280` (`_khop_o3`) hoạt động
trên **dãy số** trích từ reply — câu "chưa thấy giao dịch nào" không chứa số nào để so khớp/truy vết.
Không phải O3 bỏ sót do lỗi, mà O3 **được thiết kế cho một hạng khác** (số, không phải mệnh đề trạng
thái).

**[ĐO] bổ sung — vì sao 23/23 test_invariants KHÔNG bắt được finding này, và sẽ KHÔNG BAO GIỜ bắt
được nếu không đổi bản chất:** đọc `tests/test_invariants.py:506-560` (mục "RÀNG BUỘC CỨNG 2+3") —
hai test ở đây (`INV-08`/`INV-09`) kiểm **danh sách/schema tool khớp contract**, hoàn toàn CẤU TRÚC
TĨNH. Không có gì trong 23 test này đọc một CUỘC HỘI THOẠI THẬT và hỏi "model có gọi tool trước khi
tuyên bố kết quả không". Đây đúng hạng mù đã gặp nhiều lần trong dự án (§5.D2/§5.N STATE.md, cùng
tên): **contract-first canh được KHAI BÁO, không canh được HÀNH VI THẬT của model trên một lượt cụ
thể.** Cổng nhập bể GĐ3 (chạy thật, có tool_calls thật) chính là cơ chế DUY NHẤT hiện có đủ khả năng
bắt loại lỗi này — và nó vừa làm đúng việc đó.

## Trả lời ba câu

### ① Mức độ — CAO cho finding, nhưng phân biệt HAI NGỮ CẢNH khác severity

**Với vai trò MỘT PHÁT HIỆN TRONG CỔNG (đang đúng vị trí của nó — gate testing, TRƯỚC khi vào bể phục
vụ khách):** đây là **cổng làm đúng việc nó sinh ra để làm.** Model chưa từng chạm một khách hàng
thật. Xếp mức "gate finding, CHẶN model này khỏi bể — không điều kiện, không thương lượng" là đủ, và
đó chính là bằng chứng ngân sách 46-ca/cổng-A đáng giá: nó vừa mua lại đúng một sự cố mà nếu bỏ qua
sẽ xảy ra trên khách thật.

**Với vai trò một CÂU HỎI VỀ HỆ THỐNG NÓI CHUNG (nếu tái diễn trên qwen):** đây sẽ là **P0 tức thì,
độc lập hoàn toàn với lịch GĐ3.** Không phải vì mức độ CÔNG NGHỆ khác đi, mà vì QUẦN THỂ bị ảnh hưởng
đổi — từ "0 khách hàng thật" sang "khách hàng thật đang dùng production hôm nay." **Đừng chờ tôi định
hạng lại nếu kết quả song song ra dương tính trên qwen — báo PO thật ngay lập tức, đúng như bạn đang
làm song song.** Đây đúng nguyên tắc dự án đã học (Luật B): cùng dữ kiện, quần thể khác thì hành động
khác, không phải mức độ khác.

### ② Model bug hay prompt/tool-binding bug — CHƯA KẾT LUẬN ĐƯỢC, và phép đo song song của bạn là ĐÚNG cách trả lời, không phải tôi đoán hộ

Tôi không tự trả lời câu này bằng suy luận — đây đúng loại câu Luật M của dự án dạy phải MỞ SỔ TRƯỚC
KHI LẬP LUẬN, và sổ ở đây là chính phép đo song song bạn đang chạy (D1 trên qwen). Hai kết quả có thể
xảy ra và hai hướng xử khác hẳn nhau — không đoán trước:

- **Qwen KHÔNG tái diễn** ⟹ bằng chứng nghiêng về đặc thù binding/tool-schema của deepseek (nhiều họ
  model có cách "quyết định có nên gọi tool hay tự trả lời" khác nhau tuỳ fine-tuning) ⟹ xử lý: loại
  `deepseek-v4-pro-0813` khỏi bể, không cần sửa prompt chung.
- **Qwen TÁI DIỄN** ⟹ đây là lỗ trong PROMPT/TOOL-BINDING DÙNG CHUNG, đang sống trên production ⟹ xử
  lý hoàn toàn khác: dừng lại, báo PO thật, ưu tiên trên MỌI việc GĐ3.

**Một gợi ý chẩn đoán bổ sung, không thay thế phép đo của bạn:** nếu có thời gian, đáng thử lại CHÍNH
câu D1 nhưng đổi `otp_verified_at`/ngữ cảnh sang một tài khoản có SẴN giao dịch trong 90 ngày (khác
tài khoản test hiện tại) — nếu model VẪN trả lời "chưa thấy giao dịch nào" bất kể sự thật, đó là bằng
chứng mạnh hơn cho "model không gọi tool, không phải model gọi tool nhưng đọc sai kết quả." Không bắt
buộc, chỉ là một lát cắt rẻ nếu ngân sách còn.

### ③ Có cần O5 không, hay chỉ cần loại model — CẢ HAI, không phải MỘT TRONG HAI

**Ngắn hạn (GĐ3, ngay bây giờ): loại model, KHÔNG CẦN chờ O5.** Loại `deepseek-v4-pro-0813` khỏi
`LLM_MODEL_POOL` là đủ để gỡ chặn GĐ3 — không cần thiết kế xong một bộ lọc mới trước khi tiếp tục.

**Dài hạn (sổ nợ riêng, không chặn GĐ3): CÓ, một O5 dạng này đáng xây — lý do dựa trên chính triết
lý guardrail tất định dự án đã theo (ARCHITECTURE.md, Lead từng trích khi đề xuất O5 cho nhãn PII):**
1. Ngay cả khi HÔM NAY chỉ deepseek tái diễn, một lần đổi phiên bản qwen tương lai/thêm model khác
   sau này có thể tái tạo đúng lỗi này — loại một model không đóng được LỚP RỦI RO, chỉ đóng một
   TRIỆU CHỨNG của nó.
2. Ràng buộc cứng 3 tự văn bản đã nêu TRẠNG THÁI ngang hàng với SỐ TIỀN — đã có O3 canh số, đáng có
   một cơ chế song song canh trạng thái, không phải để trống bên cạnh cái đã có.

**🔴 Nhưng ĐỪNG THIẾT KẾ VỘI, và đây là lý do không nên gộp vào cổng đang chạy hôm nay:** không như
O3 (khớp dãy số, tất định rõ ràng) hay O4 (khớp cụm động từ+tiền, đã có sẵn từ vựng), phát hiện "tuyên
bố điều tra không kèm tool" cần MỘT TỪ VỰNG MỚI cho "câu mang dáng dấp kết luận điều tra" (*"đã kiểm
tra"*, *"chưa thấy"*, *"không tìm thấy giao dịch nào"*...) — và đúng bẫy tôi vừa tự bắt ở finding O4
hôm nay: một câu CHÍNH SÁCH hợp lệ cũng có thể tình cờ chứa "chưa thấy" (*"nếu bạn CHƯA THẤY tiền về
sau 3 ngày, hãy liên hệ..."* — không phải kết luận điều tra, là mô tả quy trình chung). Cần bộ ca âm
tính riêng trước khi land, đúng nếp vừa áp dụng cho O4. **Không phải việc làm trong lúc gate đang chạy
dở** — ghi sổ nợ, thiết kế sau khi GĐ3 qua.

## Không kết luận

❌ đây là lỗi của cổng — cổng đang làm ĐÚNG việc, phát hiện y hệt lý do 46-ca tồn tại. ❌ deepseek nói
chung không an toàn — mới có MỘT model, MỘT ca, cần đủ dữ liệu trước khi phát biểu về cả họ model.
❌ đã biết đây là bug model hay bug chung — đang chờ phép đo song song, không đoán trước kết quả.
