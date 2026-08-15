# Rà nốt HAI đường scrub còn lại — đường log EVAL + đường LangSmith/Langfuse

> Vai: **security** · 2026-08-15 (đợt giao việc thứ hai) · vùng ghi `docs/security/`
> Đóng khoảng trống tôi tự khai trong kết sổ (`80b217a` §4).
> Dấu: `he_thong=fd16681d8088` · HEAD `ed1746f` · `git status src/` **sạch lúc đo**.
> ⚠️ Coder đang mutate `src/` trong đợt này. Phép đo dưới đây **không cần cửa sổ
> đóng băng** (đọc mã tĩnh + đọc file kết quả đã lưu, không có cặp before/after).

---

## 0. Tóm tắt

| Đường | Kết luận | Mức |
|---|---|---|
| **Log JSON của eval** | **KHÔNG TỒN TẠI** — `configure_logging()` chưa từng được gọi ở đường eval. Không có gì để rò, cũng không có gì để điều tra khi lỗi. | — |
| **File kết quả eval** *(thứ tôi KHÔNG được giao nhưng tìm thấy khi rà)* | 🔴 **F-29 (CAO cho pilot)** — transcript đầy đủ + payload tool ghi vào **138 file đang track trong git**, không scrub, không retention | CAO |
| **LangSmith/Langfuse** | 🟡 **F-30 (TRUNG BÌNH, tiềm ẩn)** — không có tích hợp trong `src/`, nhưng gói `langsmith` **đã cài** và bật được **chỉ bằng biến môi trường**, đi vòng qua toàn bộ lớp scrub | TB |

---

## 1. Đường log của eval — xác nhận: KHÔNG CÓ LOG

`configure_logging()` chỉ được gọi **đúng một chỗ**: `src/api/main.py:115`
(module import time của app FastAPI). Đường eval gọi thẳng `graph.py`, không
qua app ⟹ **0 dòng log JSON**, đúng như sổ Đợt 2 đã ghi (F-LOG).

**Kết luận cho câu hỏi được giao** (*"log đường eval có scrub không"*): câu hỏi
**không áp dụng** — không có log nào được sinh ra. Không có rò rỉ qua đường này.

**Nhưng hệ quả ngược cần nói rõ:** đây không phải tin tốt. Nó nghĩa là khi một
ca eval hỏng (MT-E02, timeout, 429), **không có log nào để điều tra** — đúng
thứ đã làm tôi và tester mất công ở MT-E02. Vá F-LOG cải thiện khả năng điều
tra; và **khi vá xong thì câu hỏi scrub mới phát sinh** — lúc đó log sẽ chứa
tin khách + reply agent, và `configure_logging` phải được kiểm là có đi qua
`scrub_pii` trước khi ghi. Xin ghim điều kiện này vào lệnh vá F-LOG:

> **F-LOG không được coi là đóng nếu chỉ "có log".** Phải kèm: log đường eval
> đi qua cùng lớp scrub với đường app, verify bằng một ca có PII thật.

---

## 2. 🔴 F-29 (CAO cho pilot) — transcript eval nằm trong GIT, không scrub, không xoá được

### Phát hiện

`eval/results/` có **138 file đang được git track**, và `.gitignore` **không có
mục nào** loại chúng. File `*_raw.json` chứa các trường:

```
all_customer_texts     ← TOÀN BỘ tin khách gõ, nguyên văn, mọi lượt
all_agent_replies      ← toàn bộ câu trả lời agent
tool_calls_day_du      ← payload ĐẦY ĐỦ của mọi tool call (kết quả tra DB)
traceback              ← stacktrace khi lỗi
```

### Hôm nay: phơi nhiễm THẤP — nói rõ để không thổi

Đo trên file mới nhất (`adversarial_run_20260815_053214_raw.json`, 25 bản ghi):
1 SĐT (`0901234567`, dữ liệu seed tổng hợp) · **0** số tài khoản · **0** user_id
thật. Và payload tool **đã được che**: `wallet_id: "********0001"`,
`phone: "038***0001"`, `full_name: "P. Đ. Long"` ⟹ **lớp masking BR-06 chạy
đúng** ở đường này.

### Nhưng CƠ CHẾ mới là rủi ro, và nó nhắm thẳng vào pilot

**BR-06 KHÔNG che dữ liệu của chính chủ** — đúng thiết kế
(`lookup_transaction.py:41,53`):

```python
"phone":      user.phone      if is_owner else mask_phone(user.phone),
"full_name":  user.full_name  if is_owner else mask_full_name(user.full_name),
"account_no": acct.account_no if is_owner else mask_account_no(acct.account_no),
```

Trong eval hôm nay, các ca chạy dưới danh nghĩa người **không phải chủ** của
bên kia nên mọi thứ hiện ra đã che. **Trong một lượt chạy thật, khách hỏi về
giao dịch CỦA CHÍNH HỌ** ⟹ `is_owner=True` ⟹ **SĐT thật, số tài khoản thật,
họ tên thật, KHÔNG che**, đi thẳng vào `tool_calls_day_du`.

Cộng với `all_customer_texts` vốn **chưa bao giờ qua scrub** — đó là lời khách
gõ, đúng loại dữ liệu tôi vừa đo ở cửa `description_raw` (chứa cả PII **bên
thứ ba**: *"em chuyển nhầm cho anh X, sđt…"*).

### Vì sao điều này chạm thẳng điều kiện tôi đặt cho pilot

Ý kiến pilot của tôi có hai ràng buộc, một trong đó là **"có đường xoá sau
đợt"**. Một file đã commit vào git **không có đường xoá** theo nghĩa thực
hành: xoá file ở commit sau **không** xoá nó khỏi lịch sử; muốn xoá thật phải
rewrite history (`filter-repo`) và force-push — thao tác mà hiến pháp dự án
xếp vào loại **luôn phải hỏi PO trước**, và không làm được nếu repo đã được
BTC/người khác clone.

⟹ **Nếu harness được chạy với người thật ở đợt 150 người mà không sửa gì, điều
kiện "có đường xoá" của tôi TRƯỢT.** Đây là lần đầu tôi tìm thấy một thứ làm
hỏng chính điều kiện mình đặt ra.

### Đề nghị (mức thấp nhất đủ dùng, không đòi hơn)

1. **Trước pilot:** `.gitignore` loại `eval/results/*_raw.json` (giữ `.md` tóm
   tắt nếu nó không chứa transcript — cần kiểm riêng), HOẶC bắt buộc scrub
   trước khi ghi file raw.
2. **Không đòi xoá 138 file đang có** — chúng là dữ liệu tổng hợp, phơi nhiễm
   thấp (đo ở trên). Xoá lịch sử là thao tác đắt và rủi ro hơn lợi ích ở đây.
   **Đây là chỗ tôi chủ động KHÔNG leo thang.**
3. Quyết định thuộc PO vì nó đụng deliverable (file kết quả là bằng chứng nộp
   bài) — tôi không tự chốt đánh đổi đó.

---

## 3. 🟡 F-30 (TB, tiềm ẩn) — LangSmith bật được bằng MỘT biến môi trường, đi vòng qua scrub

### Hiện trạng

- **Không có tích hợp Langfuse/LangSmith nào trong `src/`** — grep toàn bộ
  `src/` chỉ ra **một dòng docstring** ở `tracing.py:2` giải thích vì sao chọn
  OpenTelemetry thay vì Langfuse. Không có code gửi, không có key trong
  `config.py`. **Đây là tin tốt và tôi xác nhận nó.**
- Nhưng: gói **`langsmith` ĐÃ ĐƯỢC CÀI** (v0.11.0 — đi kèm `langchain`).

### Rủi ro

Tracer gốc của LangChain bật **hoàn toàn bằng biến môi trường**
(`LANGCHAIN_TRACING_V2=true` + `LANGSMITH_API_KEY`), **không cần sửa một dòng
code nào**. Khi bật, nó gửi prompt thô + kết quả tool thô lên LangSmith cloud
(dịch vụ Mỹ) — **đi vòng qua toàn bộ lớp scrub của dự án**, vì
`_scrub_and_truncate` nằm trong `OTelTracingCallbackHandler` **tự viết**, còn
tracer native của LangChain là **cơ chế song song không gọi callback đó**.

Hai điều làm nó đáng ghi thay vì bỏ qua:

1. **Không qua review.** Bật bằng env var trên dashboard Render/Railway ⟹
   không có diff, không ai trong quy trình review thấy. Đây là lớp thay đổi
   duy nhất trong dự án có thể mở một kênh xuất dữ liệu mà **không để lại vết
   trong git**.
2. **Giáo trình khoá học hướng dẫn bật nó ở production.**
   `docs/guide/chapter-07.md:489,498-499,656` bảo đặt `LANGSMITH_API_KEY` +
   `LANGCHAIN_TRACING_V2="true"`, `LANGSMITH_PROJECT=ai20k-agent-production`.
   ⚠️ **Hiệu chuẩn cho đúng:** đây là **tài liệu giảng dạy của AI20K**, KHÔNG
   phải runbook triển khai của FIN-05 — tôi không kết luận đội đã hoặc sẽ làm
   theo. Nhưng nó là tài liệu đội đang học, nên xác suất ai đó bật theo hướng
   dẫn là **không nhỏ**, và đó đúng là kịch bản cần chặn trước.

### Pháp lý

Nếu bật với dữ liệu khách thật: đây là **chuyển dữ liệu cá nhân ra nước
ngoài** — NĐ 13/2023 đòi **hồ sơ đánh giá tác động chuyển dữ liệu ra nước
ngoài** (Điều 25). Không phải thứ bật bằng một env var rồi tính sau.

### Đề nghị

- Ghi vào tài liệu vận hành: **`LANGCHAIN_TRACING_V2` phải giữ `false` ở mọi
  môi trường có dữ liệu thật**, và việc bật nó là quyết định cần PO + hồ sơ
  pháp lý, không phải thao tác cấu hình.
- Rẻ hơn nữa nếu coder muốn làm cứng: đặt `LANGCHAIN_TRACING_V2=false` **minh
  thị** trong `config.py`/Dockerfile để env bên ngoài không tự bật được âm
  thầm — biến một cấu hình-ngầm thành một quyết định-hiện.
- **KHÔNG cần bật thử để đo** (đúng như PO-agent giao) — cơ chế đã rõ từ đọc
  mã + xác nhận gói đã cài.

---

## 4. Việc này KHÔNG đóng cái gì

- **Chưa đọc hết 138 file** — tôi đo mẫu file mới nhất. Kết luận "phơi nhiễm
  hôm nay thấp" đúng cho **file đó**; nếu PO cần chắc cho cả 138 file thì đó là
  một phép quét riêng, nói một tiếng tôi chạy.
- **Chưa kiểm các file `.md`** trong `eval/results/` có chứa transcript không
  (mới chỉ kiểm `_raw.json`).
- F-29/F-30 **chưa có probe hành vi** như bốn cửa — chúng là phát hiện từ đọc
  mã + đọc dữ liệu đã lưu. Với F-29 thì dữ liệu đã lưu **là** bằng chứng trực
  tiếp; với F-30 thì tôi cố ý không bật để đo.
