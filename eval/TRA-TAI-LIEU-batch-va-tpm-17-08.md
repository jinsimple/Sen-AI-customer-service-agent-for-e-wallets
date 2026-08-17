# Tra tài liệu: Batch API · bucket TPM theo model — 0 lượt LLM

> Vai: **tester** · 17/08. Đọc thẳng tài liệu chính thức Alibaba Cloud Model
> Studio. Hạng bằng chứng: **TÀI LIỆU NÓI**, chưa có phép đo nào của ta xác nhận.

## ④ Batch API — 🔴 KHÔNG DÙNG ĐƯỢC cho model của ta

    danh sách Bắc Kinh:  qwen3.7-max · qwen3-max · qwen-max · qwen-max-latest
                         qwen3.7-plus · … · deepseek-*  · text-embedding-v4
    danh sách SINGAPORE: qwen-max · qwen-plus · qwen-flash · qwen-turbo   ← CHỈ BỐN

Ta chạy `LLM_BASE_URL=https://dashscope-intl.aliyuncs.com` ⟹ **vùng Singapore**,
và `LLM_MODEL=qwen3.7-max`.

⟹ **`qwen3.7-max` KHÔNG có trong danh sách Batch của Singapore.** `qwen3.8-max`
cũng không. Chỉ `qwen-max` (bản gốc, không đánh số) có mặt.

> Chuyên gia khai họ **không phải nguồn** cho câu *"qwen3.8-max có trong danh
> sách batch chưa"*. Đáp án: **chưa**, ở vùng ta dùng — và câu hỏi đúng không
> phải *"model nào hỗ trợ batch"* mà **"model nào hỗ trợ batch Ở VÙNG NÀY"**.
> Danh sách Bắc Kinh dài gấp ba và **không áp dụng cho ta**.

**Giá**: batch = **50%** giá thời-gian-thực. **Hạn mức riêng**: tài liệu
**không nói** batch có bucket tách khỏi real-time hay không — cùng chỗ im lặng
với câu cached-token/TPM.

⚠️ Phạm vi PO đã khai và tôi giữ nguyên: eval qua **vòng lặp agent** là
real-time theo bản chất; batch chỉ hợp cho **lời gọi judge độc lập**. Đừng ai
ước tiết kiệm trên toàn bộ eval.

⟹ **Đường này đóng cho tới khi ta đổi model hoặc đổi vùng.** Không phải "chưa
làm", là "không dùng được".

## ⑤ Bucket TPM theo model — 🟢 ĐỘC LẬP THẬT (theo tài liệu)

> *"Each model has its own rate limit."*
> *"Rate limits are applied at the root account level. The usage of all RAM
> users, workspaces, and API keys under the account is combined."*

⟹ **Hai chiều, cả hai đều quan trọng:**

    theo MODEL     → bucket ĐỘC LẬP. Chia việc sang model khác CỘNG thông lượng.
    theo TÀI KHOẢN → gộp mọi RAM user · workspace · API key.
                     Tách khoá KHÔNG cộng thông lượng — nó chỉ tách trách nhiệm.

Điểm thứ hai là điểm dễ hiểu sai nhất, và nó **bác trước** một ý tưởng chưa ai
nêu nhưng chắc chắn sẽ có người nêu: *"tạo thêm API key để có thêm hạn mức"*.
Không. Cùng tài khoản = cùng bucket.

**Và vùng đổi con số rất mạnh:** `qwen3.8-max` có **600 RPM ở Singapore** nhưng
**30.000 RPM ở US (Virginia)** — gấp **50 lần**. Nếu trần RPM (không phải TPM)
là thứ chặn đích 100 CSKH thì **đổi vùng** là đòn bẩy lớn hơn mọi thứ ta đang
bàn. Chưa ai đo xem ta chạm trần nào trước.

⟹ Điều này **mở lại** hướng *route-theo-bước*: bước rẻ đi model rẻ, bước khó đi
model mạnh — **cộng** được hai bucket. Trước đây nó là một giả định; giờ tài
liệu nói có.

⚠️ **Hạng bằng chứng: TÀI LIỆU NÓI.** Ta chưa đo. Phép đo thực nghiệm cần đâm
vào trần hai model song song — đốt hạn mức và chặn phiên khác, tôi **không**
làm và **không** đề nghị làm. Nếu cần chắc, gộp vào cùng phiếu hỏi Alibaba.

## Ba câu cho MỘT phiếu hỏi Alibaba

1. Cached token có được trừ/chiết khấu khi đếm **TPM** không (tier thường, **không**
   phải PTU)?
2. Lời gọi bị **client huỷ giữa chừng** có tính vào TPM và vào tiền không?
3. Batch có **bucket hạn mức riêng** khỏi real-time không?

Ba câu, một vòng. Thao tác tài khoản ⟹ PO thật gửi.

---

## 🔴 BỔ SUNG — "50×" là con số SAI TRỤC. Trần thật chỉ ×5.

PO xếp việc đổi vùng vào ngăn *"đo được, quyết định thuộc người có thẩm quyền
pháp lý"* và đề nghị **đo cái rẻ để khỏi phải quyết cái đắt**. Tôi làm được
ngay bằng số học từ số đã đo — **không cần lưu lượng người thật**.

### Trần nào chạm trước

    trần TPM   1.000.000 / 14.198 token/lượt  =  70,4 lượt/phút
    trần RPM         600 /   2,39 gọi/lượt    = 251,0 lượt/phút

⟹ **TPM chạm trước, sớm hơn 3,6 lần.** Ở mọi mức tải thực tế, RPM **không bao
giờ** là trần chặn:

    150 người × 0,5 lượt/ph =  75 lượt/ph → TPM 106% 🔴 · RPM  30%
    100 người × 1,0 lượt/ph = 100 lượt/ph → TPM 142% 🔴 · RPM  40%

### Nên "50× RPM" mua được gì — tra tiếp, và câu trả lời là ×5

    Singapore     qwen3.7-max   600 RPM  ·  1.000.000 TPM
    US Virginia   qwen3.7-max  30.000 RPM  ·  5.000.000 TPM

    trần thật:  Singapore  70 lượt/phút  →  US  352 lượt/phút
                TPM vẫn là trần chặn ở CẢ HAI vùng

> **Đổi vùng mua `×5`, không phải `×50`.** Con số 50 là tỉ lệ của một trục
> **không chặn gì cả**. Ai trích `50×` vào một quyết định về thông lượng đang
> trích một đại lượng đúng để trả lời sai câu hỏi — **Luật 12b, xếp hạng trên
> một trục**, lần này trục đó còn không phải trục ràng buộc.

### Hệ quả cho hồ sơ pháp lý

`×5` **vẫn đáng kể** — nó là hiệu số giữa *"vỡ ở 150 người"* và *"chịu được
150 người"*. Nên nhánh vùng **không tự rụng** như PO hy vọng.

Nhưng nó đổi **hạng** của cuộc thảo luận: không phải *"một đòn bẩy 50× đang bị
pháp lý chặn"* mà *"một đòn bẩy 5× đòi đưa hội thoại khách Việt Nam ra hạ tầng
Mỹ (NĐ 13/2023 · cư trú dữ liệu)"*. Cùng một quyết định, hai mức giá rất khác
nhau để cân.

⚠️ Hạng: **TÀI LIỆU NÓI** cho các con số trần; **ĐO ĐƯỢC** cho `14.198
token/lượt` và `2,39 gọi/lượt`. Phép chia là số học, không phải phép đo.

---

## 🔴 BỔ SUNG 2 — tỉ lệ lượt-đơn KHÔNG ĐO ĐƯỢC, nhưng câu hỏi đảo được

PO hỏi: *"tỉ lệ lượt-đơn trong lưu lượng thật là bao nhiêu? trả lời được bằng
bộ ca sẵn có, không cần token."*

**Không trả lời được, và cả hai nguồn đều hỏng theo cùng một kiểu — DÂN SỐ SAI:**

- `messages` (230 tin khách, 85 phiên): **script sinh ra**, không phải người.
  Tôi đã chứng minh sáng nay bằng nhịp gõ — p10 = 3s · trung vị = 3s ⟹ **19,8
  lượt/phút/người**, tức máy gõ tiếp ngay khi nhận xong phản hồi. Và script
  không bao giờ gõ *"alo"*. ⟹ tỉ lệ tính từ đây là **sàn giả**, gần 0%.
  *(Nội dung còn mã hoá trường, nhưng kể cả giải mã được thì dân số vẫn sai.)*
- `eval/bo_ca_luot_don.json` (20 ca): **tôi soạn tay để dò RANH GIỚI**, cố ý
  làm giàu ca hiểm. Tỉ lệ 9/20 = 45% là **một lựa chọn thiết kế**, không phải
  một thống kê. Đọc 45% thành tỉ lệ lưu lượng là **dùng bộ ca dò biên làm mẫu
  đại diện** — đúng lỗi `golden_set không có lượt đơn` ta gặp sáng nay, chỉ
  ngược chiều.

> **Không corpus nào ta có là một mẫu của lưu lượng thật.** Con số này chỉ đo
> được ở buổi test người thật đầu tiên.

### Nhưng ĐẢO câu hỏi thì trả lời được ngay, và nó hữu ích hơn

    150 người × 0,50 lượt/ph →  75 lượt/ph → TPM 106%  →  cần ≥  6,1% lượt đơn
    150 người × 0,75 lượt/ph → 113 lượt/ph → TPM 160%  →  cần ≥ 37,4%
    150 người × 1,00 lượt/ph → 150 lượt/ph → TPM 213%  →  cần ≥ 53,0%
    100 người × 1,00 lượt/ph → 100 lượt/ph → TPM 142%  →  cần ≥ 29,6%

⟹ **Ở nhịp thận trọng chỉ cần 6,1%.** Con số `30%` tôi đưa lúc trước là ngưỡng
của **kịch bản xấu**, không phải ngưỡng chung — tôi trích nó không kèm kịch bản,
lại đúng lỗi *khai trục* (Luật 12b).

**Và đây là dạng câu miễn nhiễm với ẩn số:** thay vì chờ một con số không đo
được, ta phát biểu **điều kiện** — *"T1 đủ cứu buổi test nếu ≥6,1% lượt là lượt
đơn ở nhịp 0,5"*. Nó kiểm được ngay trong 10 phút đầu buổi test, bằng chính dấu
`duong` đã có.

### ⚠️ Thiên lệch sống sót — PO khai, tôi ghi kèm

`14.198 token/lượt` là **trung bình lượt THÀNH CÔNG**. Coder đo lượt **hỏng**
tốn **50–70K**. Nếu lưu lượng thật có lượt hỏng thì `70,4 lượt/phút` là **quá
lạc quan**, và mọi ngưỡng `% lượt đơn cần` ở trên là **cận dưới**.

Không sửa số — sửa là bịa. Khai kèm.
