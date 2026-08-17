# Sự cố — khoá OpenAI được gửi tới máy chủ Alibaba (17/08)

> Vai: **security** · 2026-08-17 · PO-agent hỏi ba câu, ưu tiên trên việc
> data-residency. Nhãn: **[ĐO]** = tôi chạy thật, có kết quả dán kèm ·
> **[PHẢI KIỂM]** · **[PHÁN ĐOÁN]**.

## Tóm tắt phán quyết

| Câu | Trả lời |
|---|---|
| ① `401` có tính là **lộ** không | **CÓ. Xoay khoá.** Nhưng hạ mức: **xác suất khai thác thấp, nguyên tắc thì dứt khoát** — làm theo lịch trong ngày, không phải báo động cháy |
| ② nghĩa vụ thông báo NĐ 13 | **KHÔNG** — khoá là bí mật hạ tầng, không phải dữ liệu cá nhân. Có **một điều kiện** phải kiểm mới khoá được kết luận (§2) |
| ③ có phải một HỌ lỗi không | **PHẢI — và họ CHƯA đóng.** Tôi tìm được **một thành viên thứ ba chưa ai vá**, đo thật ở §3 |

**Bạn không phản ứng thái quá ở câu ①.** Cách đọc của bạn (`401` = *họ từ chối
dùng*, không phải *họ không nhận được*) là **đúng về mặt kỹ thuật**, và nó là
cách đọc đúng.

---

## §1. Câu ① — `401` **chứng minh đã nhận**, không chứng minh chưa lộ

**Lập luận, không phải cảm nhận:**

1. **Để trả về `401`, máy chủ bên kia phải ĐỌC header `Authorization`.** `401`
   là một quyết định **sau khi phân tích thông tin xác thực**. Một mã trạng thái
   nói *"tôi đã xem khoá của anh và không chấp nhận"* thì không thể đồng thời là
   bằng chứng *"tôi chưa từng thấy khoá của anh"*.
2. **TLS kết thúc ở biên của họ.** Từ đó trở vào, header nằm ở dạng rõ trong hạ
   tầng của họ: gateway, WAF, log truy cập, log lỗi, dấu vết yêu cầu. Và **sự
   kiện xác thực THẤT BẠI thường được ghi kỹ hơn** sự kiện thành công — đó là
   dữ liệu chống lạm dụng, không ai vứt đi.
3. **Ta không kiểm toán được retention của họ.** Phơi nhiễm **không kiểm toán
   được** thì xử lý như **đã phơi nhiễm**. Quyết định xoay khoá không được phép
   phụ thuộc vào một giả định về cấu hình log của người khác mà ta không có
   quyền xem.
4. **Chuẩn xử lý sự cố dùng ngưỡng "nghi ngờ", không phải ngưỡng "chứng minh".**
   NIST SP 800-57 định nghĩa khoá bị tổn hại gồm cả **nghi ngờ tiết lộ**. Chờ
   bằng chứng khai thác rồi mới xoay là đảo ngược gánh nặng chứng minh về đúng
   phía không thể chứng minh được.
5. **Tính bất đối xứng của hai lựa chọn.** Xoay khoá: tốn công, **hoàn tác
   được**, thất bại thì thấy ngay (dịch vụ lỗi 401 của chính ta). Không xoay:
   miễn phí hôm nay, **không hoàn tác được**, và thất bại thì **không có triệu
   chứng** — nó xuất hiện dưới dạng hoá đơn.

### [PHÁN ĐOÁN] Nhưng hãy hiệu chuẩn mức, đừng thổi lên

Bên nhận là **một nhà cung cấp đám mây lớn có chứng nhận SOC 2**, không phải kẻ
tấn công. Khoá này **không mở được dữ liệu của ta** — nó tiêu được hạn mức
OpenAI của ta, thế thôi. Không có dấu hiệu lạm dụng nào.

⟹ **Xoay theo lịch trong ngày, ở cửa sổ bảo trì bình thường.** Đây **không**
phải sự cố cần đánh thức ai. Ghi là **sự cố hạng thấp về xác suất, hạng dứt
khoát về nguyên tắc**. Nói đúng mức cũng là một phần của việc nói đúng.

### 🔴 Cái làm việc này ĐÁNG hơn bản thân nó: một khoá cho cả hai môi trường

Điểm nặng nhất không phải Alibaba nhận được khoá. Nó là **khoá bị gọi là
"production" lại đang nằm trên máy dev và được một lượt thử nghiệm cầm đi**.
Bán kính vụ nổ của **mọi** sự cố sau này — nháp, benchmark, dán nhầm, log lỡ
tay — đều bằng "production" chừng nào một khoá còn phục vụ cả hai.

⟹ **Bản vá bền không phải xoay khoá. Nó là tách khoá theo môi trường.** Xoay
lần này rồi cấp **khoá dev riêng, hạn mức riêng**; lần sau sự cố cùng loại chỉ
tốn một khoá dev. Đây là đề nghị **quan trọng hơn** câu hỏi bạn hỏi.

## §2. Câu ② — **không** phát sinh nghĩa vụ thông báo, kèm một điều kiện phải kiểm

Nghĩa vụ thông báo của NĐ 13/2023 gắn với **vi phạm quy định bảo vệ dữ liệu cá
nhân**. Một khoá API là **bí mật hạ tầng của ta**, không phải dữ liệu cá nhân
của một chủ thể dữ liệu nào. ⟹ **Bản thân việc lộ khoá không kích hoạt nghĩa vụ
thông báo.**

⚠️ **[PHẢI KIỂM] — điều kiện duy nhất có thể lật kết luận trên:** nghĩa vụ sẽ
phát sinh **nếu khoá đó với tới được dữ liệu cá nhân**. Câu cần trả lời: *tài
khoản OpenAI có bật lưu nội dung yêu cầu (stored completions / logging ở mức tổ
chức) mà khoá này đọc lại được không?* Nếu **có bật**, thì khoá không chỉ tiêu
được tiền — nó **đọc lại được hội thoại khách**, và lúc đó đây là sự cố dữ liệu
cá nhân với hạng hoàn toàn khác. **Tôi không khẳng định theo chiều nào; đây là
một ô cần bấm vào bảng điều khiển để xem.** Kiểm ô này **trước** khi đóng hồ sơ.

**Bất kể kết quả:** ghi bản ghi sự cố có ngày tháng (file này). Không có nghĩa
vụ báo ra ngoài không có nghĩa là không có nghĩa vụ ghi lại bên trong.

## §3. Câu ③ — **PHẢI là một họ, và họ CHƯA đóng**

### Hình dạng đúng của họ — rộng hơn "fallback khoá"

> **ĐÍCH ĐẾN của một lượt gọi ra ngoài được quyết định bởi BIẾN MÔI TRƯỜNG,
> trong khi CÁI ĐI KÈM lượt gọi đó (khoá, nội dung) được quyết định bởi MÃ.**
> Người review mã không nhìn thấy đích đến. Người sửa `.env` không nhìn thấy
> cái đi kèm. Sự cố sinh ra ở đúng khe giữa hai tầm nhìn đó.

### Rà `src/` — [ĐO], chạy thật

**Chỉ có hai chỗ trong `src/` dựng client với `base_url` cấu hình được:**
`graph.py:256-261` (chat) và `store.py:44-49` (embedding). **Cả hai đã đi qua
`_khoa_cho_nha_cung_cap`** (`config.py:201` và `:215`).
⟹ **Đường embedding mà bạn nghi — đã được phủ.** Bản vá của coder đúng là một
bản vá HỌ, không phải vá một ca. Ghi nhận đúng công.

### 🔴 Nhưng có thành viên THỨ BA, và bản vá không với tới nó — [ĐO]

SDK OpenAI tự đọc **`OPENAI_BASE_URL` / `OPENAI_API_BASE` từ môi trường**. Tôi
chạy thật:

```
OPENAI_BASE_URL = https://dashscope-intl.aliyuncs.com/compatible-mode/v1

ChatOpenAI(api_key='sk-proj-GIA-LAP')                  -> dashscope-intl…/v1/
ChatOpenAI(api_key='sk-proj-GIA-LAP', base_url=None)   -> dashscope-intl…/v1/   ← truyền None KHÔNG cứu
OpenAIEmbeddings(api_key='sk-proj-GIA-LAP', base_url=None) -> dashscope-intl…/v1/
khoá client sẽ gửi: sk-proj-GIA-LAP…
```

**Ba hệ quả:**

1. **`_khoa_cho_nha_cung_cap` không bắn.** Nó hỏi *"CHÚNG TA có đổi đích đến
   không?"* (`LLM_BASE_URL` có được đặt không). Câu đúng phải hỏi là *"ĐÍCH ĐẾN
   có đổi không?"* — và đích đến là **hợp** của biến của ta **và** biến của SDK.
   Đặt `OPENAI_BASE_URL` mà để trống `LLM_API_KEY` ⟹ **tái lập chính xác sự cố
   hôm nay, im lặng, không lỗi khởi động.**
2. **Ba chỗ trong `eval/` phơi nhất:** `_llm_judge.py:59` và `_harness.py:108,160`
   truyền `api_key=OPENAI_API_KEY` và **không bao giờ truyền `base_url`** ⟹ chúng
   đi theo biến môi trường một cách vô điều kiện. Đây cũng là đường **không ai
   theo dõi** — và là đường mà thước đo chạy trên đó.
3. **Đây là thao tác TỰ NHIÊN NHẤT của người vận hành.** Bảo một người *"trỏ hệ
   thống sang nhà cung cấp mới"*, thứ họ tìm đầu tiên là `OPENAI_BASE_URL`. Bản
   vá hiện tại chặn con đường **có tài liệu**; nó không chặn con đường **trực
   giác**.

**[ĐO] Trạng thái hôm nay: CHƯA kích hoạt.** `.env` **không** có
`OPENAI_BASE_URL` cũng không có `OPENAI_API_BASE` (kiểm bằng tên biến, không
đọc giá trị). Đây là lỗ **tiềm ẩn**, không phải đang rò.

**Đề nghị cho tech-lead** (vùng của họ, tôi không sửa): **cấm hẳn biến của SDK**
thay vì cố suy luận về nó — lúc import, nếu môi trường có `OPENAI_BASE_URL` hoặc
`OPENAI_API_BASE` thì **chết ngay kèm lý do**, vì dự án đã có biến riêng cho
từng vai (`LLM_*` / `EMBEDDING_*`) và cửa của SDK chỉ có thể **đi vòng** qua
chúng. Truyền `base_url=None` tường minh **không** phải bản vá — đã đo ở trên.

### Hai thành viên còn lại, mức thấp — ghi để không phải tìm lại

- **`LLM_MODEL = … or OPENAI_MODEL` (`config.py:200`)** — **cùng hình dạng**, tải
  trọng lành: quên đặt thì ta hỏi Alibaba một model tên `gpt-4o-mini` và nhận lỗi
  của nhà cung cấp. Không phải bí mật, nhưng có tiết lộ *ta đang dùng gì*. Không
  cần guard — **cần một dòng ghi vì sao nó KHÔNG cần**, nếu không người đọc sau
  không phân biệt được "đã cân nhắc" với "bỏ sót".
- **`LANGCHAIN_TRACING_V2` (`.env`)** — hôm nay **`false`**, `LANGCHAIN_API_KEY`
  **rỗng** ([ĐO], đọc tên + cờ, không đọc khoá). Lật một chữ là **toàn bộ prompt
  + câu trả lời** đi LangSmith (Hoa Kỳ) — **người nhận thứ ba**, đúng hình dạng
  *cửa thứ năm*, và cũng đúng họ này: **đích đến nằm trong `.env`, không nằm
  trong mã.** Không phải việc hôm nay; là việc phải nằm trong danh mục kiểm
  trước dữ liệu thật đầu tiên.

## §4. Ghi nhận về coder — và điều nó nói về quy trình

Lỗi là của họ. Nhưng ba điều đúng:
① họ tìm ra bằng **cách duy nhất tìm được** — chạy thật, không suy luận từ mã
tĩnh; ② họ chặn bằng **mã chết-lúc-khởi-động**, không bằng lời dặn; ③ họ vá
**cả đường embedding** chứ không chỉ đường gây ra sự cố — đó là phản xạ vá-họ,
đúng luật đội.

**Và nếu họ không chạy thật thì PO-agent đã điền đúng cấu hình rò đó vào `.env`
và đẩy lên production.** Đây là bằng chứng cụ thể cho luật *hiện-diện ≠
hiệu-lực*: bản thiết kế "tách chat khỏi embedding" **đúng** ở mọi dòng, và nó
vẫn sinh ra một đường rò khoá mà **chỉ một lượt chạy thật mới thấy**.

## §5. Việc cần làm — theo thứ tự

1. **Xoay `OPENAI_API_KEY`** (trong ngày, cửa sổ bình thường).
2. **[PHẢI KIỂM] §2** — tài khoản OpenAI có bật lưu nội dung không. Ô này quyết
   định hồ sơ này đóng ở hạng nào.
3. **Cấp khoá dev riêng**, tách khỏi production (§1) — bản vá bền thật sự.
4. **Giao tech-lead: chặn `OPENAI_BASE_URL`/`OPENAI_API_BASE`** (§3) — họ chưa
   đóng chừng nào còn cửa đó.
5. Ghi vào danh mục kiểm trước dữ liệu thật đầu tiên: `LANGCHAIN_TRACING_V2`.

## §6. Điều tôi KHÔNG kết luận

- **Không** biết Alibaba có thật sự ghi header đó hay không, và **không thể
  biết**. Khuyến nghị xoay khoá **không dựa** vào việc họ có ghi — nó dựa vào
  việc **ta không kiểm chứng được**.
- **Không** phán quyết ô "stored completions" (§2) — chưa xem bảng điều khiển.
- **Không** đọc giá trị bất kỳ biến nào trong `.env`; mọi kết luận ở §3 dựa trên
  **tên biến** và **cờ boolean**.
