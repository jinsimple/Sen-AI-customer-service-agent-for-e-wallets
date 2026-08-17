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
