# 🔴 Đường FALLBACK khi hết giờ ghi `scope` BỊA vào bảng bằng chứng

> Vai: **tester** · 17/08 · ngăn xếp đo dùng riêng `fin05do`, tài khoản hạt
> giống `USR-0001`. Phát hiện **ngoài ý muốn** trong lúc dựng phép đo quan
> sát ⑤ — không phải thứ tôi đi tìm.

## Điều đã xảy ra, theo bản ghi của chính hệ thống

```
log     agent_turn_timeout        correlation_id req-682ed13ef9004f0b · USR-0001
trả về  HTTP 200 · 50,6s
        tool_calls = []           ← RỖNG
        usage      = tất cả 0
        reply      "Mình chưa tra được yêu cầu này, để mình chuyển cho chuyên
                    viên hỗ trợ trực tiếp nhé — mã ticket của bạn là
                    TCK-54e4ba996e7c"
```

Nhưng trong CSDL, hiệu số **trước → sau** của đúng lượt đó:

```
tool_results          0 → 1      chỉ MỘT dòng, và là create_ticket
investigation_logs    0 → 0      🔴 RỖNG
complaints          600 → 601
tickets             600 → 601
```

Nội dung bản ghi được tạo:

```
ticket_id        TCK-54e4ba996e7c
type             other
scope            internal_wallet     🔴
status           investigating
trans_id         (rỗng)
description_raw  (đã mã hoá trường — lớp mã hoá HOẠT ĐỘNG ✓)
```

## Vì sao đây là finding, không phải một lượt lỗi

**① `scope = internal_wallet` là một giá trị BỊA.** Mô tả tool `create_ticket`
— nguyên văn từ `build_customer_tools()`, tôi đã băm và đối chiếu từng byte:

> *"scope … lấy từ dữ liệu transaction đã tra được (trường "scope"), KHÔNG hỏi
> khách đoán… Không tra ra giao dịch VÀ khách cũng không xác định được phạm vi
> (dù đã hỏi) → dùng **"unknown"**, KHÔNG tự đoán bừa 1 trong 3 giá trị thật."*

`tool_results` có **đúng một dòng** và nó là `create_ticket`. **Không có
`lookup_transaction`. Không có `get_customer_history`.** Không giao dịch nào
được tra. Contract nói phải là `"unknown"`; hệ thống ghi `internal_wallet` —
**một trong ba giá trị thật, không có căn cứ nào**.

**② Chuỗi truy vết đứt ở mắt xích đầu.** Hiến pháp §2 ràng buộc cứng 3:

    tool_results → investigation_logs.tool_result_id → resolutions.cited_tool_result_ids

`investigation_logs` **rỗng**. Vé này **không truy vết được** tới bất cứ kết
quả tool nào, kể cả dòng `create_ticket` vừa sinh ra nó.

**③ Đây là ĐƯỜNG CODE, không phải hành vi model.** `tool_calls=[]` và
`usage` toàn 0 ⟹ model **không hề quyết định** giá trị này. Nó do đường xử lý
hết-giờ điền vào. Nghĩa là:

> **Nó KHÔNG ngẫu nhiên.** Một hành vi model thì k=10 mới nói được gì; một
> nhánh code thì tái lập bằng cách ép lại đúng điều kiện. Bằng chứng ở đây là
> **mạnh hơn** một quan sát k=1 thông thường.

Và nó **vô hình với trục 2 của bộ đo tool-calling**: trục đó chấm tham số do
**model** điền. Ở đây model không điền gì. `0 bịa / ~500 lượt` vẫn đúng, và
vẫn hoàn toàn không nói gì về đường này.

**④ Hậu quả nghiệp vụ.** `scope` là trục phân loại quyết định hồ sơ đi đường
nào. Một vé mang `scope=internal_wallet` sai sẽ được điều tra như tranh chấp
nội bộ ví trong khi sự việc có thể là `to_bank`. Và khách **đã được báo** mã
vé, nên vé này vào hàng chờ CSKH như một vé thật.

## Vì sao lượt đó hết giờ — tách bạch với finding

    INFO: Child process [16] died
    → uvicorn khởi động lại worker
    → lượt đang chạy hết giờ → rơi vào fallback

Worker chết ngay sau khi Presidio nạp model NER (`Using device of type: cpu`).
Container **không đặt giới hạn bộ nhớ**, `OOMKilled=false`, nhưng `fin05do`
đang ở **1,1 GB** so với 744 MB của hai ngăn xếp kia, trên một máy Docker tổng
**7,75 GB** đang chạy **ba** ngăn xếp.

⚠️ **Nguyên nhân chết là chuyện của hạ tầng và tôi KHÔNG kết luận** — đó là
vùng của coder. Nhưng nó **không làm nhẹ** finding: hết giờ là chuyện sẽ xảy ra
trên production vì bất kỳ lý do nào (mạng, nhà cung cấp chậm, tải cao), và câu
hỏi *"khi hết giờ thì hệ ghi gì vào bảng bằng chứng"* độc lập với *"vì sao hết
giờ"*.

## Việc cần làm

1. **coder** — truy đường fallback hết-giờ: `scope` lấy từ đâu? Nếu là hằng số
   mặc định thì đổi sang `"unknown"` theo đúng contract. Nếu nó suy từ đâu đó,
   nói rõ từ đâu.
2. **security** — vé bịa `scope` nằm trong `complaints`, đúng bảng nhóm A của
   ADR-025 (lời khai = bằng chứng). Đây là **máy ghi vào bảng bằng chứng một
   giá trị nghiệp vụ không có nguồn** — cùng lớp tổn hại anh nêu sáng nay, lần
   này do chính sản phẩm gây ra chứ không do phép đo.
3. **tester (tôi)** — viết test canh: hết giờ ⟹ `scope` phải là `"unknown"`,
   và `investigation_logs` không được rỗng khi có vé. Chưa viết, vì cần biết
   cách ép hết-giờ một cách xác định.

## Dấu vết phép đo này để lại — khai đủ, điều kiện ④

Trên `fin05do` (dùng riêng, không ai khác ghi vào ⟹ hiệu số **quy được trách
nhiệm**):

    complaints +1 · tickets +1 · tool_results +1
    checkpoints +14 · checkpoint_blobs +20 · checkpoint_writes +21
    redis +5 khoá

**Tôi KHÔNG dọn.** Kế hoạch dọn khai trước là *"xoá volume và seed lại nếu có
bản ghi lạ"* — nhưng bản ghi lạ ở đây **chính là bằng chứng của finding**. Dọn
nó là xoá vật chứng. Giữ nguyên tới khi coder và security đọc xong.

## Phép đo quan sát ⑤ — CHƯA đo được

Đây là thứ tôi định làm. Lượt đầu worker chết, lượt sau hết giờ ⟹ chưa lượt nào
đi tới chỗ cửa OTP chặn `get_customer_history`. **Quan sát ⑤ vẫn ở k=1**, chưa
tái lập, chưa bác. Nhãn `43fb345f3e62` giữ nguyên, luật chấm bất động.
