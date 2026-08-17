# Phụ lục phán quyết ca 4/6 — đối chiếu với prompt SẢN PHẨM

> Vai: **security** · 2026-08-17 · phụ lục cho `90b6008`, mở sau khi PO-agent
> đưa bằng chứng mới: lượt v4 (`0aeb350`, 4 model, ~500 lượt) cho thấy
> `gpt-4o-mini` — **model sản phẩm đang chạy thật** — làm **ngược** phán quyết
> của tôi ở ca 4 và ca 6, **10/10, không do dự**.
>
> Câu hỏi PO đặt: *"sản phẩm đang SAI hôm nay — hay phán quyết bỏ sót gì?"*

## §1. Giả thuyết ② của PO — **BỊ BÁC bằng đo, và bác theo hướng ngược lại**

PO nghi: *quy tắc dẫn xuất `scope` chỉ nằm trong docstring, có thể chưa bao giờ
vào prompt sản phẩm ⟹ model không có cách nào biết ⟹ lỗi ở prompt, không ở
model.* Giả thuyết đúng cách đặt. Nhưng đo ra thì **ngược**.

Quy tắc đó tới model **hai lần**, và lần thứ hai **mạnh hơn cả phán quyết của
tôi**:

**① Mô tả tool `create_ticket`** (chính là docstring — LangChain gửi nguyên văn
làm `description`, tôi introspect app đang chạy để xác nhận):
> *`scope` … lấy từ dữ liệu transaction **đã tra được**, **KHÔNG hỏi khách
> đoán** …*

**② System prompt sản phẩm** — `build_system_prompt()`, **15.094 ký tự, gửi vô
điều kiện ở MỌI lượt** (`graph.py:273-274`). Mục `## Quy trình điều tra`:

> **bước 1, đúng ca 4:** *"**double_charge**: khách mô tả 2 giao dịch bị trừ
> trùng cho CÙNG 1 thao tác — **PHẢI tra ra CẢ HAI giao dịch** (2 lần gọi
> `lookup_transaction`/`get_customer_history` nếu cần) rồi gọi `create_ticket`
> ĐÚNG 1 LẦN DUY NHẤT."*
>
> *"**Xác định được complaint_type KHÔNG đồng nghĩa với đã đủ điều kiện gọi
> `create_ticket` ngay** — vẫn **BẮT BUỘC** thực hiện bước 2/3 bên dưới (gọi
> tool tra cứu giao dịch thật) trước, kể cả khi khách đã tự nêu đủ số tiền/thời
> gian … **KHÔNG được bỏ qua bước tra cứu chỉ vì đã phân loại được.**"*
>
> **và đúng ca 6:** *"… bạn PHẢI hướng dẫn từng bước kiên nhẫn hoặc **chủ động
> tra giúp (gọi `get_customer_history`)**, TUYỆT ĐỐI không được trả lời kiểu
> 'ngoài phạm vi của mình'."*

⟹ **Prompt sản phẩm nói ĐÚNG điều tôi phán, cho CẢ ca 4 lẫn ca 6, và nói dứt
khoát hơn tôi.** Không có chuyện "model không được dặn".

## §2. 🔴 Đây là Luật 16 thoả — và nó là kết quả mạnh nhất trong ngày

- Tôi dẫn nhãn **chỉ từ `contracts/` + `global_rules`**, và lúc dẫn **chưa đọc
  `prompt.py`** — hồ sơ `90b6008` không trích một dòng nào của nó.
- Prompt sản phẩm được viết từ **PRD/Brief §7**, bởi người khác, **không đọc
  nhãn của tôi**.

**Hai dẫn xuất, hai phương pháp độc lập, cùng một kết luận.** Để nhãn của tôi
sai, nó phải sai **cùng chiều** với prompt sản phẩm được viết độc lập — xác
suất thấp. Nhãn ca 4/6 **đứng**.

## §3. ⟹ Câu hỏi đổi hoàn toàn. Nó không còn là "nhãn hay sản phẩm"

Cả **nhãn** lẫn **đặc tả sản phẩm** đều nói *tra*. Model sản phẩm **không tra**
trong bộ đo. Chỉ còn **một** biến chưa ai nêu:

> 🔴 **Bộ đo có gửi system prompt 15.094 ký tự của sản phẩm không?**

Tester khai bộ đo *"gọi **thẳng API nhà cung cấp, không qua sản phẩm**"*. Nếu
"không qua sản phẩm" nghĩa là **không có system prompt**, thì mọi thứ khớp lại
ngay lập tức: **hệ được đo không chứa câu "PHẢI tra ra cả hai giao dịch"**, và
bốn model — hai nhà cung cấp — hành xử **hợp lý với thông tin chúng có**. Bốn
model đồng thuận không phải bí ẩn; nó là **điều đáng kỳ vọng** khi kích thích
thiếu đúng câu quyết định.

**Đây cũng đúng cảnh báo tôi đã gửi tester ở phán quyết trước:** *"điều này chỉ
đúng chừng nào bộ đo đưa cho model ĐÚNG mô tả tool của sản phẩm; nếu bạn viết
lại cho gọn thì bạn đang đo một kích thích khác, và khoảng cách đó phải được
khai."* Khoảng cách ấy giờ có thể đang **rộng hơn** mức tôi cảnh báo — thiếu cả
system prompt, không chỉ mô tả tool.

## §4. Luật dừng — khai TRƯỚC khi biết đáp án

PO đã tự khai động cơ. **Tôi cũng có động cơ**, khai luôn: kết luận *"lỗi
thước"* **bảo vệ phán quyết của chính tôi**. Nên ghi trước, để không đọc số
theo ý mình:

| Bộ đo gửi gì | Đọc BẮT BUỘC |
|---|---|
| **KHÔNG** có system prompt sản phẩm | Bộ đo đo **năng lực gọi tool trần của model**, KHÔNG đo hành vi sản phẩm. Kết luận *"sản phẩm đang sai hôm nay"* **không được thiết lập**. Ca 4/6/7 nói về **kích thích của bộ đo**. Nhãn giữ nguyên. |
| **CÓ** system prompt sản phẩm | 🔴 **Đây LÀ finding sản phẩm, hạng nghiêm trọng** — agent đẩy việc điều tra sang khách ở ca nó tự tra được, **trên chính hệ đang cho mentor xem**. Và **tôi sai một phần**: §2 chỉ chứng minh *đặc tả đồng ý với nhãn*, **không** chứng minh *sản phẩm làm đúng đặc tả* — tôi phải mở hồ sơ, không được co về "nhãn của tôi vẫn đúng". |

⚠️ **Hai điều cấm đọc sai:**

1. **"Bộ đo thiếu prompt" ≠ "bộ đo vô giá trị".** Một bộ đo model-thuần đo được
   thứ thật: **năng lực gọi tool trần**, độc lập với 15k ký tự chỉ dẫn. Đó là
   số dùng được để **chọn model** — chỉ **không** được đọc thành hành vi sản
   phẩm.
2. **Nếu hoá ra CÓ prompt: đừng dừng ở "model kém".** Hình dạng *"tool không
   được gọi dù chỉ dẫn nói phải gọi"* **trùng khít** với F-31/F-32 (RAG-38/40:
   gọi search 0/8). Lúc đó giả thuyết **"tư thế từ-chối bị PHÂN TÁN khắp
   prompt"** — tôi nêu ở §B bản rà `6e44750` — vừa có **bằng chứng thứ hai ở
   một họ ca hoàn toàn khác**, và phép phân đôi đang chờ nên gộp cả hai họ.

## §5. Việc cần làm — một câu hỏi, rẻ, chặn mọi thứ còn lại

**Hỏi tester: bộ đo v4 gửi chính xác payload gì** — có `system` message không,
nội dung có phải `build_system_prompt()` không, mô tả tool là nguyên văn từ
`build_customer_tools()` hay do tester soạn lại. **Không diễn giải lại — xin
đúng payload.**

Chừng nào chưa có câu đó, **không kết luận nào về sản phẩm được rút ra từ v4**,
theo cả hai chiều.

---

# ĐÃ TRẢ LỜI — nhánh MỘT. Cập nhật 2026-08-17, sau `1de72a1` của tester

Tester đo và trả lời (không nhớ lại):

```
bộ đo v4 gửi system :    123 ký tự · băm 9d6dbff3bc7f · TESTER TỰ SOẠN
sản phẩm     gửi system: 15.094 ký tự · vô điều kiện mọi lượt
                          "PHẢI tra ra CẢ HAI" ×1 · "chủ động tra giúp" ×1
                          · "create_ticket" ×7
mô tả tool          : NGUYÊN VĂN từ build_customer_tools() (băm 4129d298555c)
lược đồ tham số     : introspect app, KHÔNG viết tay
```

⟹ **Nhánh MỘT của bảng §4, và ở dạng tệ hơn mức tôi phòng:** không chỉ thiếu
system prompt — hai câu **thiếu** lại **chính là hai câu quyết định hành vi
đúng của ca 4 và ca 6**, đúng hai ca lỗi.

**Theo tiền cam kết §4, chốt:**
- v4 đo **năng lực gọi tool trần của model**. **Không** đo hành vi sản phẩm.
- *"Sản phẩm đang sai"* **không được thiết lập** — và tester bổ sung đúng chiều
  còn lại mà tôi chưa ghi: ***"sản phẩm ổn"* cũng không.** v4 **câm về sản phẩm
  theo cả hai chiều.** Ghi nhận bổ sung này, nó chặt hơn bản của tôi.
- Bốn model đồng thuận ở ca 4/6 **không còn là bí ẩn cần giải**.
- **Nhãn ca 4/6 đứng.** Sai nằm ở **kích thích của bộ đo**, không ở nhãn.

## §5b. 🔴 Tôi BÁC một câu của tester — và bác theo chiều bất lợi cho con số

Tester nêu, kèm lời mời bác nếu sai:
> *"0 lần bịa xảy ra **KHI THIẾU** 15k ký tự dặn dò … nên kết quả này không phụ
> thuộc phần bị thiếu."*

**Vế sau đúng. Vế trước — "khi thiếu dặn dò" — SAI, và tôi đã viết y hệt ở bản
đầu §6 nên đây là tự đính chính.**

Đọc chính 123 ký tự đó: *"**LUÔN gọi tool để tra dữ liệu trước khi nói bất kỳ
con số hay trạng thái nào. Không bịa.**"*

⟹ Bộ đo **không hề bị tước** chỉ dẫn chống bịa. Ngược lại: **lệnh cấm bịa chiếm
khoảng một phần ba toàn bộ system prompt** mà model nhận. Trong sản phẩm, chính
lệnh đó là **một chỉ dẫn giữa 15.094 ký tự** cạnh tranh với mọi chỉ dẫn khác.

**⟹ Đối với TRỤC 2, bộ đo là điều kiện DỄ HƠN sản phẩm, không phải khắc nghiệt
hơn.** Con số 0 **không mạnh lên**; nó được đo dưới một kích thích có tỉ lệ
tín-hiệu/nhiễu cho đúng trục đó **cao hơn** sản phẩm.

**Cách công bố sửa lại:** *"0 lần bịa tham số bắt buộc trong ~500 lượt, **trong
điều kiện bộ đo — nơi lệnh cấm bịa chiếm ~1/3 system prompt**."*
**KHÔNG** nói *"kể cả khi thiếu 15k ký tự dặn dò"* — câu đó nghe như một phép
thử khắc nghiệt hơn, và nó không phải.

Câu hỏi thật — *"lệnh 'không bịa' có SỐNG SÓT qua pha loãng trong 15.094 ký tự
không?"* — **chưa ai đo**, và nó là câu quan trọng hơn cho sản phẩm.

## §5c. v5 là phép phân đôi rẻ nhất cho giả thuyết PHÂN TÁN — đừng bỏ lỡ

v4 và v5 sẽ khác nhau **đúng một yếu tố**: prompt của bộ đo ↔ prompt của sản
phẩm. Mô tả tool đã nguyên văn, lược đồ đã introspect, ca và `k` giữ nguyên.
**Một cặp so sánh chỉ-khác-một-biến** — thứ dự án này hiếm khi có được miễn phí.

⚠️ *Biến đó là **"prompt nào"**, không phải **"prompt dài bao nhiêu"*** — nó gộp
độ dài, nội dung, và cả tên thương hiệu (bộ đo ghi *"MoMo"*, sản phẩm ghi
*"Sen" của "một ví điện tử"*). Nên nó **không cô lập riêng pha loãng**. Vẫn
đáng chạy, và phải đọc đúng mức:

| v5 ở ca 4/6 | Đọc |
|---|---|
| **ĐÚNG** | 15k chỉ dẫn **có hiệu lực** ở họ ca này. Giả thuyết phân-tán **không** được củng cố ở đây. Sản phẩm ổn ở họ ca này (và chỉ họ này). |
| **SAI** | 🔴 **finding sản phẩm thật** — **và** đây là ca đối chứng đẹp nhất từ trước tới nay cho giả thuyết **PHÂN TÁN** (§B, `6e44750`): cùng model, cùng tool, cùng ca, chỉ đổi prompt; chỉ dẫn **có mặt** (`"PHẢI tra ra CẢ HAI"` ×1) mà **không có hiệu lực**. `hiện-diện ≠ hiệu-lực` **đo được trực tiếp**, không phải suy ra. |

**Quan sát khai TRƯỚC, để nếu v5 đỏ thì nó là dự đoán chứ không phải giải thích
hậu nghiệm:** chính số đếm tester đưa đã lệch sẵn — chỉ dẫn *tra trước* xuất
hiện **×1**, còn `create_ticket` — hành động mà nó có nhiệm vụ chặn — xuất hiện
**×7**. Nếu v5 đỏ, **độ chênh nổi bật giữa hành động và tiền đề của nó** là ứng
viên cơ chế đầu tiên cần soi, trước khi kết luận "model kém".

**Đề nghị vận hành:** đóng băng mọi thứ khác giữa v4↔v5, công bố **băm cả hai
prompt** cạnh kết quả (v4 đã có `9d6dbff3bc7f`), và **chạy trục 2 lại trong
v5** — vì đúng theo §5b, trục 2 dưới sản phẩm là phép thử **chưa từng chạy**.

## §5d. Tỉ lệ pha loãng: **~2×, không phải ~20×** — đo trên KÍCH THÍCH TRỌN VẸN

Tester đo mật độ *"bịa"* và ra **loãng ~20 lần** (`6/15.094` = 0,04%/ký tự so
với `1/123` = 0,81%/ký tự). Tôi kiểm phần họ đo — **khớp chính xác cả ba số**:
`len=15094` · băm `33d66da05520` · `"bịa"` **×6**. Phép đo của họ đúng.

**Nhưng nó so system-prompt với system-prompt, trong khi model không nhận riêng
system prompt.** Mô tả tool cũng là chỉ dẫn, cũng chứa lệnh cấm bịa, và **có
mặt ở CẢ HAI phiên bản**. Ở v4 chúng **áp đảo** kích thích:

```
mô tả tool (chung cho cả hai)     4.334 ký tự · "bịa" ×3
   get_customer_history ×1 · create_ticket ×1 · request_human_handoff ×1

KÍCH THÍCH TRỌN VẸN (system + mô tả tool)
   v4 (bộ đo)      4.457 ký tự · "bịa" ×4 · 0,0897 %/ký tự
   v5 (sản phẩm)  19.428 ký tự · "bịa" ×9 · 0,0463 %/ký tự
                                          ⟹ loãng ~1,94×
```

⟹ **Kết luận §5b không đổi** — v4 **vẫn** là điều kiện dễ hơn cho trục 2. Nhưng
**độ mạnh phải hạ theo**: chênh lệch là **~2 lần**, không phải 20. Tôi đã nới
lời văn một lần (bỏ *"khắc nghiệt hơn"*); giờ nới lần thứ hai theo hướng ngược
lại — *"loãng 20 lần"* cũng **không** công bố được.

🔴 **Và đây là điều chỉnh quan trọng hơn con số:** *"pha loãng"* là câu trả lời
cho **trục 2**, và nó **không nói gì về ca 4/6**. Với ca 4/6, chỉ dẫn quyết
định (*"PHẢI tra ra CẢ HAI"*, *"chủ động tra giúp"*) **VẮNG MẶT hoàn toàn**
trong v4 — đó là **hiện diện/vắng mặt**, không phải **đậm/loãng**. Hai trục
khác nhau, đừng gộp:

| | Delta v4→v5 | Loại |
|---|---|---|
| **ca 4/6** (tra trước khi tạo vé) | ×0 → ×1 | **vắng mặt → có mặt** |
| **trục 2** (cấm bịa) | 0,0897% → 0,0463% | **loãng ~2×** |

Suy luận của tester — *"nếu nhắc 'bịa' tận 6 lần mà lệnh vẫn không sống sót thì
pha loãng mạnh hơn ta tưởng"* — là một **điều kiện đúng cách đặt**, nhưng
**×6 trong một kích thích dài gấp 4,4 lần** không ấn tượng như con số trần gợi
ra. Giữ nó làm giả thuyết, đừng làm kết luận chờ sẵn.

⚠️ **Một lệch chưa giải thích, ghi lại thay vì làm phẳng:** tester báo độ dài
mô tả tool `680·947·1266·793·1176` (tổng 4.862); tôi đo `t.description` ra
`608·851·1114·713·1048` (tổng 4.334). Lệch đều ~70–150 mỗi tool — nhiều khả
năng họ tính cả tên tool/lược đồ tham số mà nhà cung cấp thực nhận. **Không đổi
tỉ lệ** (~2× hai đằng), nhưng phải khai: hai bên đang băm **hai đối tượng khác
nhau**, và nếu sau này ai đó đối chiếu hai file sẽ thấy lệch mà không rõ vì sao.

> 🔴 **ĐÃ GIẢI THÍCH — và tôi sai, xem §5f.** Không phải "hai cách đếm". **Cùng
> một trường `description`, cùng một file, và hai giá trị khác nhau vì HAI
> RUNTIME khác nhau.** Số **4.862 của tester là số đúng của sản phẩm**; **4.334
> là artefact của môi trường tôi đo**. Tỉ lệ ở bảng trên tính trên 4.334 nên
> **không dùng nữa** — dùng bảng §5f.

## §5e. Ratify phát hiện `current_time` của tester — và một hệ quả họ chưa nêu

`build_system_prompt(*, current_time)` là tham số **bắt buộc**, và ngày/giờ đi
thẳng vào prompt. ⟹ **prompt sản phẩm KHÔNG cố định — nó đổi theo thời điểm
gọi.** Tester ghim `2026-08-17 10:00:00` và khai băm `33d66da05520` là **băm
của mốc đó**, không phải của hàm. **Đúng, và đây là loại lỗi hỏng-lặng-lẽ điển
hình** — hai đợt cách nhau vài giờ nhận hai prompt khác nhau, cặp đối chứng
hỏng mà không có triệu chứng nào.

**Hệ quả họ chưa nêu:** điều đó áp **ngược về quá khứ**. Mọi mốc đã công bố đo
qua sản phẩm (An toàn 30/30, mốc nền đối kháng 18/20…) chạy dưới một prompt mà
**ta không băm lại được trừ khi biết mốc thời gian của lượt chạy**. Không phải
báo động — chưa có bằng chứng ngày/giờ đổi hành vi — nhưng nó có nghĩa là câu
*"cùng một prompt"* giữa hai ngày **là một giả định, không phải một sự kiện**.
**Đề nghị:** từ nay ghi **mốc thời gian truyền vào prompt** cạnh mọi con số đo
qua sản phẩm, cùng chỗ với băm THƯỚC và băm VẬT.

## §6. Hai kết quả v4 ĐỨNG VỮNG bất kể phán quyết trên — ghi vào hồ sơ an toàn

**🟢 Bịa tham số bắt buộc = 0 / ~500 lượt / 4 model / 2 nhà cung cấp.**

Nghi ngờ ban đầu của PO (*"nhãn thưởng model chịu bịa"*) nay bị bác **ở mức
mạnh nhất có thể**: không phải "nhãn không thưởng", mà **không model nào bịa,
dù có cơ hội rõ ràng** — ca 4 và ca 8 đều đặt sẵn cái bẫy đó.

**Vì sao con số này KHÔNG bị ảnh hưởng bởi câu hỏi §3:** các lệnh cấm bịa nằm
trong **mô tả tool** (*"KHÔNG bịa một mã giao dịch"*, *"KHÔNG tự đoán bừa 1
trong 3 giá trị thật"*), mà mô tả tool là **artefact sản phẩm** và phải có mặt
trong mọi bộ đo gọi được tool. ⟹ kết quả quy được cho **model + mô tả tool**,
cả hai đều là của ta, **bất kể system prompt có hay không**.

> ~~Nếu bộ đo **không** có system prompt thì đây còn là **phép thử KHẮC NGHIỆT
> HƠN** — 0 lần bịa khi thiếu 15k ký tự dặn dò, không phải nhờ chúng.~~
>
> 🔴 **ĐÍNH CHÍNH (xem §5b):** câu gạch trên **SAI**. Sau khi đọc chính 123 ký
> tự bộ đo gửi, hoá ra nó **chứa** lệnh *"Không bịa"* và chiếm ~1/3 prompt ⟹
> với **trục 2**, bộ đo là điều kiện **DỄ HƠN** sản phẩm, không khắc nghiệt
> hơn. Tôi suy ra "thiếu prompt = thiếu dặn dò" mà **chưa đọc prompt bộ đo** —
> đúng lớp lỗi tôi đang bắt ở người khác cả ngày hôm nay.

**🟢 Hỏng định dạng = 0 / ~500 lượt / 4 model.**

⚠️ **Cách công bố — trục "bịa tham số" trả 0 nghĩa là nó CHƯA phân biệt được
gì trong lượt này.** Giá trị của nó hôm nay là **dây bẫy giữ cho tương lai**,
không phải thước phân loại model. Nói *"không model nào bịa tham số bắt buộc
trong ~500 lượt"* — **không** nói *"trục này cho thấy model X an toàn hơn"*.
(Cùng nguyên tắc khối GIỚI HẠN PHẠM VI của heldout: con số không tự mang theo
phạm vi.)

## §5f. 🔴 Lệch 4.862 vs 4.334 — TRUY RA GỐC. Tôi sai, và gốc là một FINDING lớn hơn con số

Tester từ chối nhận §5d③ và làm đúng: họ đo lại **trên container đang chạy**,
ba lần, ra y hệt `4.862`. Tôi đi tìm gốc.

### Loại trừ từng khả năng — [ĐO]

```
① mã nguồn khác nhau?
   md5 src/agents/tools/customer_tools.py
       container fin05-backend-1 : bc02c7a59bb1b4116ad2b4bf997cac11 · 827 dòng
       cây làm việc (HEAD 9e42faa): bc02c7a59bb1b4116ad2b4bf997cac11 · 827 dòng
   ⟹ TRÙNG KHÍT. Không phải "bản mô tả tool thứ hai trong src/".

② mã hoá / chuẩn hoá?   NFC=4.334 · NFD=5.233 · utf-8=5.457 — không số nào ra 4.862.
   ⟹ KHÔNG phải.

③ RUNTIME?
   container           : langchain-core 1.5.4 · Python 3.12.14   ⟹ 4.862
   venv tôi mượn       : langchain-core 1.5.3 · Python 3.14.6    ⟹ 4.334
```

**⟹ Nguyên nhân: hai phiên bản `langchain-core` khác nhau ĐÚNG MỘT SỐ VÁ.**

### Lệch là gì, chính xác

Bản `1.5.4` **giữ nguyên thụt đầu dòng** của docstring khi dựng `description`;
bản `1.5.3` **gỡ thụt** (dedent). Dán từ container:

```
'Tra chính sách/phí/quy định chung của ví (KHÔNG phải tra 1 giao\n        dịch cụ thể — …'
                                                          ↑ 8 dấu cách còn nguyên
```

Kiểm chéo: mọi delta đều **chia hết cho 8** — `72·96·152·80·128` = `8×(9·12·19·10·16)`
= đúng **số dòng tiếp nối × 8 dấu cách**. Lệch là **khoảng trắng thuần**, không
phải nội dung.

### Chỗ tôi sai, nói thẳng

Tôi đo trên **một venv mượn của dự án khác** (`P-121-new/.venv`) thay vì trên
**hệ đang chạy**. Tôi vừa viết cho tester đúng một câu — *"luôn đo trên KÍCH
THÍCH TRỌN VẸN, không đo trên phần mình đang chú ý"* — rồi **đo kích thích đó
trên một runtime không phải runtime của sản phẩm**. Số của tester đúng; số của
tôi là artefact; **tỉ lệ 1,94× ở §5d phải bỏ**.

*(Có sẵn bài học trong sổ mà tôi không áp: **kiểm trong container trước khi tin
một phép đo**. Lần trước nó là chuyện xác nhận bản vá; lần này là chuyện đo
kích thích. Cùng một luật.)*

### 🔴 Nhưng gốc mới là phần đáng giá — tester đoán đúng rằng nó lớn hơn con số

> **Văn bản thực sự gửi cho model là hàm của PHIÊN BẢN MỘT THƯ VIỆN PHỤ THUỘC,
> không chỉ của mã ta viết.** Một bản vá của `langchain-core` đổi kích thích
> ~12% mà **không có commit nào của ta, không diff nào, không cảnh báo nào**.

Và bộ đóng dấu hiện tại **không bắt được**:

- `dau_thuoc()` → `he_thong` băm `src/**/*.py` + `commit`. **Cả hai TRÙNG KHÍT**
  giữa hai lần đo trên — mà prompt gửi đi vẫn khác nhau.
- `requirements.txt:14` ghi `langchain>=0.3.0` — **sàn, không ghim**, và
  **không có lockfile** (`ls` chỉ có `requirements.txt`). ⟹ **dựng lại image vào
  một ngày khác có thể đổi prompt gửi cho model**, im lặng.

**Hệ quả cho các mốc đang giữ:** hai lượt đo cùng `he_thong`, cùng commit, khác
ngày dựng image ⟹ **có thể là hai kích thích khác nhau**. Chưa có bằng chứng
khoảng trắng đổi hành vi (nhiều khả năng ảnh hưởng nhỏ, chủ yếu ở đếm token),
nên **không rút mốc nào** — nhưng đây là **lỗ thứ hai trong cùng một ngày** ở
mệnh đề *"cùng một prompt"*, sau lỗ `current_time` (§5e).

### Đề nghị — hai việc

1. **Băm CHÍNH PAYLOAD, đừng băm nguồn sinh ra payload.** Quy tắc *"băm thứ
   thực sự lên dây"* mà tester áp — định nghĩa kích thích là *"system message +
   JSON tool trọn vẹn như gửi đi"* rồi băm nó — **vá đúng lỗ này**, vì băm
   payload bắt được trôi do thư viện mà băm mã nguồn **không bao giờ bắt được**.
   *(Đính chính theo yêu cầu của chính tester: họ áp nó như một **quy tắc
   chung**, **không** vì lường trước trôi-do-thư-viện. Ghi đúng công: quy tắc
   tốt che được cả rủi ro người đặt ra nó chưa nhìn thấy — đó là lý do nên theo
   quy tắc, không phải bằng chứng ai đó tiên đoán được.)*
2. **Ghim phiên bản + lockfile** (vùng tech-lead). `langchain>=0.3.0` để ngỏ
   đúng thứ vừa chứng minh là có ảnh hưởng tới đầu vào model. Đây cũng là mục
   đã có sẵn trong playbook đóng gói (*ghim phiên bản, không dùng dải mở*), chỉ
   là chưa ai nghĩ nó chạm tới **nội dung prompt**.

### Một điểm ĐỨNG VỮNG qua cả vụ này

`build_system_prompt(current_time=2026-08-17 10:00:00)` đo **trong container**:
`len=15094` · băm `33d66da05520` — **trùng khít số tester ghim**. Prompt hệ
thống là chuỗi thuần, không qua `langchain`, nên nó **không** dính lớp lỗi trên.
Cặp v4↔v5 vẫn dựng được; chỉ phần mô tả tool phải lấy **từ container**.

## §5g. Lược đồ tool bộ đo thừa 399 ký tự — **KHÔNG bác quyết định của tester, nhưng gắn một nhãn**

Tester kiểm điều kiện *"băm trong container"* và bắt được lỗi của chính họ: băm
`0c08f10a8f55` **tái lập được**, nhưng so **từng trường** thì `parameters`
**lệch cả năm tool** — file lược đồ bộ đo mang **17 trường `"title"`** mà
`convert_to_openai_tool` của app không sinh, cộng `required: []` ở hai tool nơi
app bỏ hẳn khoá. **7.172 (bộ đo) vs 6.773 (app) — thừa 399 ký tự ≈ +100
token/lượt mà sản phẩm KHÔNG BAO GIỜ GỬI.**

Họ chọn **giữ nguyên lược đồ v4 cho v5** và khai lệch ra, thay vì sửa — vì sửa
làm **hai biến** khác nhau giữa v4↔v5 (system prompt **và** lược đồ), phá đúng
cặp chỉ-khác-một-biến mà v5 tồn tại để giữ.

**Tôi KHÔNG bác. Lập luận một-biến đúng, và đó là lựa chọn đúng — cho MỘT trong
hai mục đích.** Vấn đề là v5 đang được giao **hai** mục đích:

| Mục đích của v5 | Giữ lược đồ v4 |
|---|---|
| **① so cặp v4↔v5** (giả thuyết vắng-mặt / pha-loãng) | ✅ **ĐÚNG** — một biến, đọc được |
| **② đo hành vi SẢN PHẨM ở ca 4/6** | ❌ **KHÔNG đạt** — vẫn mang 399 ký tự sản phẩm không gửi |

⟹ **Ràng buộc tôi gắn:** v5 phải được gán nhãn là **“phép SO CẶP”**, **không**
được đọc thành *“đo hành vi sản phẩm”*. Nếu để hai mục đích dính vào nhau, câu
*"sản phẩm hành xử thế nào ở ca 4/6"* sẽ **được coi là đã trả lời** trong khi nó
**vẫn chưa có phép đo nào** — đúng lớp lỗi ta vừa mất cả ngày để gỡ ở v4.

### 🔴 Và câu hỏi ② đáng một phép đo KHÁC HẲN: đừng dựng lại payload nữa

Năm lỗi hôm nay **đều sinh từ việc DỰNG LẠI** thứ sản phẩm gửi: prompt tự soạn ·
mật độ đo trên phần đang chú ý · runtime sai · lược đồ phồng ·
`current_time` trôi. **Phép đo duy nhất không thể sai theo lớp đó là phép đo
không dựng lại gì** — gọi thẳng endpoint của sản phẩm.

**Đề nghị:** câu *"sản phẩm có tra trước khi tạo vé không"* đo qua **chính
`/agent/chat`**, không qua bộ đo dựng payload. Đắt hơn (vòng ReAct đủ, DB, phiên
OTP) và nó đo **cả đường ống** thay vì riêng phép chọn tool — nhưng *"cả đường
ống"* **chính là định nghĩa của "hành vi sản phẩm"**. Bộ đo dựng-payload giữ
đúng việc nó làm tốt: **so model với model**.

### Một chỗ tôi đồng ý nhưng hạ mức chắc chắn

Tester khai `required: []` **khớp nghĩa** với việc app bỏ hẳn khoá (rỗng ==
vắng mặt) nên trục 2 không bị ảnh hưởng. Theo JSON Schema thì **đúng**. Nhưng
*"hai nhà cung cấp xử lý hai dạng đó y hệt nhau"* là một **suy luận**, không
phải một phép đo — rủi ro thấp, không chặn gì, chỉ **đừng ghi nó vào hồ sơ như
một sự kiện đã kiểm**.

### §5h. Luật rút ra từ NĂM lần trong một ngày

Tester tổng kết, và tôi ratify vì nó khớp cả năm ca:

> **Lớp lỗi "đọc kích thích qua một đại diện thay vì đọc chính nó" KHÔNG chết vì
> bị đặt tên.** Hôm nay nó bắt tester ba lần và tôi ba lần — kể cả **ngay sau**
> khi mỗi người vừa viết ra luật cấm chính nó.
> **Không lần nào bị bắt bởi tự kiểm. Cả năm lần đều bị bắt bởi HAI NGƯỜI ĐO
> ĐỘC LẬP RỒI SO SỐ.**

**Vế thi hành — chỗ dễ trượt nhất, ghi rõ:** phải so **SỐ**, không so **KẾT
LUẬN**. Chính tôi đã suýt đóng vụ `4.862 vs 4.334` bằng cách hoà *"hai cách đếm
khác nhau"* — một câu ở tầng **kết luận**, nghe hợp lý, và nó **đã che mất** một
finding về phiên bản thư viện. Thứ cứu được là tester **từ chối cách hoà đó** và
đòi so tiếp ở tầng số.
