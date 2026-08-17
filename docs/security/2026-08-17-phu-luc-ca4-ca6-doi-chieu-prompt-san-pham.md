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
