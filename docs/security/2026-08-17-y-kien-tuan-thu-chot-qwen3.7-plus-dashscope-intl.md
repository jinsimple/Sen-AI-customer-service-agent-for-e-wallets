# Ý kiến tuân thủ — CHỐT `qwen3.7-plus` trên `dashscope-intl` (17/08)

> Vai: **security/tuân thủ** · 2026-08-17 · PO-agent báo PO thật đã chốt, coder
> đang land. Đây là bản **có ghim endpoint**, thay cho bản sơ bộ `c7a8217` (viết
> khi vùng còn chưa ghim). ⚠️ **Không phải tư vấn pháp lý** — nó khoanh vùng câu
> hỏi để người có thẩm quyền pháp lý trả lời.
> Nhãn: **[ĐO]** = kiểm được, có nguồn · **[PHẢI KIỂM]** · **[PHÁN ĐOÁN]**.

## Phán quyết trước, lý do sau: **KHÔNG chặn land.** Ba điều kiện trước demo.

Land là thay cấu hình, hôm nay chạy dữ liệu hạt giống. Khoảng trống tuân thủ
lớn nhất (§4) **có sẵn với OpenAI** và **không đóng lại nếu ta chặn Qwen** —
chặn land mua được số 0. Ba điều kiện ở §5, tất cả rẻ.

---

## §1. Câu ① — vùng. Câu trả lời KHÔNG phải "Singapore"

**[ĐO]** từ tài liệu chính thức Alibaba Cloud Model Studio:

| Đo được | Nguyên văn |
|---|---|
| `dashscope-intl.aliyuncs.com` ↔ vùng | **Singapore** (`ap-southeast-1`) |
| phạm vi triển khai dịch vụ | *"International (**global nodes excluding the Chinese mainland**)"* |
| nơi **lưu** | *"Your static data always remains in the selected region"* |
| nơi **xử lý** | *"The region forwards the request to an **inference node within the service deployment scope**"* |

🔴 **Hai dòng cuối không nói cùng một điều, và khác biệt đó phải vào hồ sơ.**
Dữ liệu **tĩnh** ở lại Singapore. Nhưng **lượt suy luận** — tức chính nội dung
hội thoại khách — được chuyển tới **một node không ghim**, chỉ biết là **ngoài
Trung Quốc đại lục**.

⟹ **Câu nói trước mentor phải là:** *"lưu trữ tại Singapore; xử lý suy luận tại
các node toàn cầu ngoài Trung Quốc đại lục."*
**KHÔNG được nói:** *"dữ liệu ở Singapore."* Đó là một nửa đúng, và nửa bị bỏ
lại chính là nửa mà Điều 25 hỏi.

**[PHẢI KIỂM] — một đường có thể ghim chặt hơn:** tồn tại endpoint riêng theo
workspace `{WorkspaceId}.ap-southeast-1.maas.aliyuncs.com`. Tôi **không** khẳng
định nó ghim luôn node **suy luận** hay chỉ ghim **cổng vào** — tài liệu không
nói rõ, và đây đúng loại câu phải hỏi nhà cung cấp chứ không suy ra.

**Nghĩa vụ Đ.25 — [ĐO] từ văn bản, khoanh vùng chứ không kết luận:** bên chuyển
phải **lập hồ sơ đánh giá tác động chuyển dữ liệu ra nước ngoài**, hồ sơ nêu đủ
**bên chuyển · bên nhận · mục đích · loại dữ liệu · biện pháp bảo vệ · đánh giá
rủi ro**; gửi **01 bản chính** tới **A05 (Cục An ninh mạng & PCTP công nghệ
cao)** trong **60 ngày kể từ ngày bắt đầu xử lý**; và **luôn có sẵn** để kiểm
tra. ⟹ Hồ sơ phải **liệt kê được trường dữ liệu nào thực sự đi** (bảng §4) —
một hồ sơ không làm được điều đó thì không dùng được.

## §2. Câu ② — train-on-data: **cờ đỏ PO lo KHÔNG được xác nhận**

**[ĐO]:** *"Alibaba Cloud strictly protects your data privacy and **will never
use your data for model training**."* — trang `privacy-notice` và
`what-is-model-studio`. Kèm: mã hoá **AES-256**, và **SOC 2** *unqualified
opinion* (Security · Availability · Confidentiality).

**[ĐO] — trả lời thẳng câu PO hỏi:** trang điều khoản hạn mức miễn phí nói về
**hiệu lực 30–90 ngày · chỉ vùng Singapore · phạm vi International · hết thì tự
trừ số dư** — và **không có một dòng nào** về dữ liệu bậc free được xử lý khác
bậc trả phí. ⟹ **Không tìm thấy khác biệt theo bậc.** Giả thuyết "free thì bị
dùng huấn luyện" **không được xác nhận**.

⚠️ **Hạng bằng chứng — chỗ này đừng nói quá:** cam kết đó nằm ở **trang tài
liệu**, không phải điều khoản hợp đồng; chính trang đó trỏ sang *"Alibaba Cloud
International Website Product Terms of Service"* cho chi tiết, và **tôi chưa
đọc văn bản hợp đồng đó**. Câu được phép nói: *"nhà cung cấp cam kết công khai
không dùng dữ liệu để huấn luyện; ta đã kiểm ở mức tài liệu, chưa ở mức hợp
đồng."* **Không** nói *"hợp đồng cam kết"*.

### 🔴 Thứ tôi tìm thấy mà không ai hỏi — **cửa thứ năm nằm ở phía Alibaba**

Tính năng **Model monitoring** ghi *"the input, output, and latency for **each**
model call"*, giữ **30 ngày**; với model được hỗ trợ thì *"the Request and
Response fields show the input and output for each call"*. **Basic monitoring
tự bật**; advanced phải bật tay. Quyền đọc: *"Members of the default workspace
can view model calls **across all workspaces**."*

⟹ Đúng **hình dạng cửa thứ năm** tôi đã cảnh báo cho LiteLLM/Langfuse
(`520d544`): một kho giữ **prompt + response đầy đủ**, retention riêng, quyền
đọc **nằm ngoài `contracts/authority-matrix.yaml`**. Khác một điểm quan trọng:
cửa này **không nằm trong repo** — nó bật bằng **một nút trên console Alibaba**,
bởi bất kỳ ai có tài khoản, và không diff nào của ta nhìn thấy.

**[ĐO] điều kiện giảm nhẹ:** tài liệu nói phần ghi **nội dung** Request/Response
hiện *"limited to some models in the **China (Beijing)** region"* ⟹ **hôm nay
Singapore chưa có bề mặt đó**. Đây là lý do nó là **việc cần canh**, không phải
việc chặn land — nhưng nó là thứ **đổi được bằng một bản cập nhật của nhà cung
cấp**, không phải bằng quyết định của ta.

## §3. Câu ③ — cửa nào trong ADR-025? **KHÔNG cửa nào. Và đó là lỗ của KHUNG.**

Bốn cửa ADR-025 phân loại **nơi văn bản tự do được LƯU** trong hệ thống ta. Nhà
cung cấp LLM **không lưu ở ta** — nó **NHẬN và XỬ LÝ** nhóm A (lời khai). Khung
chưa có ô đó, nên Qwen không "thuộc cửa nào" **không phải vì nó vô hại**, mà vì
khung phân loại sai trục cho nó.

**Khai đúng:** *Qwen = **bên nhận xử lý (processor) của nhóm A**, đứng đúng chỗ
OpenAI đang đứng, không tạo cửa mới bên trong hệ thống ta.*
**Đề nghị vào ADR khi land:** thêm hạng **"bên nhận xử lý"** vào bảng ADR-025,
để lần đổi nhà cung cấp sau **tự động** đi qua câu hỏi này thay vì phải có người
nhớ ra.

### 🔴 Và nó **không phải phép THAY, nó là phép THÊM** — [ĐO] trên mã `b2d9f4f`

```
chat                LLM_BASE_URL          → Alibaba (SG + node toàn cầu)   graph.py:258-261
embedding           EMBEDDING_BASE_URL=None → OpenAI                        store.py:44-49
trọng tài (judge)   JUDGE_MODEL ghim literal, api_key=OPENAI_API_KEY → OpenAI  _llm_judge.py:59
kẻ tấn công giả lập EVAL_SIM_MODEL         → OpenAI                        _harness.py:108,160
```

⟹ **Sau khi land, hệ thống có HAI bên nhận ở HAI tài phán**, không phải một.
Hồ sơ Đ.25 phải liệt kê **cả hai**.

Và embedding **không** chỉ nhận văn bản chính sách: `search_policy_text` gọi
`store.search(query, …)` — **chuỗi truy vấn do agent soạn từ lời khách** cũng
được đem đi nhúng ⟹ **văn bản dẫn xuất từ khách vẫn đi OpenAI** sau khi chat đã
sang Alibaba.

Việc **ghim thước vào literal `"gpt-4o-mini"`** là quyết định **đúng về đo
lường** và tôi ủng hộ (không ghim thì Qwen tự chấm Qwen). Nhưng nó có **giá
tuân thủ** — hai nhà cung cấp thay vì một — và giá đó phải được **khai**, không
được để lẫn vào chữ "đổi sang Qwen".

## §4. Câu ④ — "y hệt cũ" là **KẾT LUẬN ĐÃ KIỂM**, đúng như PO yêu cầu

**[ĐO]:** `_scrub_pii_cho_llm` (`customer_tools.py:477`) che **theo TÊN KHOÁ** —
`full_name` · `phone` · `account_no` · `user_id` (xoá hẳn) · `wallet_id` (giữ 4
số) — áp ở **lớp bọc tool phía khách**, và **không có nhánh nào rẽ theo nhà cung
cấp**. ⟹ đổi `base_url` **không đổi một dòng nào** ở lớp che. *"Y hệt cũ"* —
**và đã kiểm, không phải mặc định.**

⚠️ **Nhưng "y hệt cũ" cũng có nghĩa: cái hở vẫn hở y như cũ.**

| Loại | Có rời không | Cơ chế |
|---|---|---|
| **tin khách gõ** (mô tả khiếu nại · tin chat) | 🔴 **RỜI, nguyên văn** | không lớp scrub nào |
| họ tên · SĐT trong kết quả tool | ✅ đã che | `_scrub_pii_cho_llm` (ADR-010) |
| số tiền · mã GD · thời gian · trạng thái | rời, **có chủ đích** | agent cần để suy luận + trích dẫn (ràng buộc 3) |
| truy vấn RAG dẫn xuất từ lời khách | 🔴 rời — **sang OpenAI** | `store.search(query)` |

Không scrub được tin khách gõ vì **agent cần chính cái nghĩa** mà scrub phá —
**S-01 đã đo `scrub_pii` chặn nhầm 40%** trên văn bản nghiệp vụ tiếng Việt.
Và theo khảo sát bốn cửa, tin khách chứa **PII của bên thứ ba** ngay ở ca dùng
điển hình nhất — *"em chuyển nhầm cho anh X, sđt 09…"* — tức dữ liệu của **người
chưa từng vào quan hệ với ví và chưa ký đồng ý nào**.

⟹ Đây là câu Đ.25 **nặng nhất**, nó **không đổi theo nhà cung cấp**, và **không
được** dùng việc chọn xong nhà cung cấp để nói rằng phần "dữ liệu ra nước ngoài"
đã được xử lý.

### Một điểm CỘNG phải ghi nhận — coder tự bắt trước khi land

`_khoa_cho_nha_cung_cap` (`config.py:173`): fallback về `OPENAI_API_KEY` **chỉ
được phép khi đích đến vẫn là OpenAI**. Không có nó, quên `LLM_API_KEY` =
**khoá production OpenAI đi thẳng sang máy chủ Alibaba**, và bằng chứng duy nhất
là một dòng `401` mà người vận hành sẽ đọc thành "sai khoá". Đúng hạng *"một
fallback chỉ an toàn khi ĐÍCH ĐẾN không đổi"*. Bắt trước khi land, tự đo thật.

## §5. Ba điều kiện trước buổi demo tiếp theo — tất cả rẻ

1. **Nói đúng câu §1.** *"Lưu trữ Singapore; suy luận tại node toàn cầu ngoài
   TQ đại lục."* Không nói trống không *"Singapore"*.
2. **Kiểm công tắc inference-log trên console Alibaba, ghi lại ngày kiểm** (§2).
   Một dòng trong hồ sơ. Cửa thứ năm này không có trong repo nên **không ai
   nhìn thấy nó bằng cách đọc code**.
3. **Demo dùng TÀI KHOẢN HẠT GIỐNG, và nói to điều đó trước khi bắt đầu.** Một
   số điện thoại thật gõ vào ô chat trong lúc demo **chính là "dữ liệu thật đầu
   tiên"** — và lúc nhận ra thì cổng đã đóng sau lưng. Đây là biện pháp duy
   nhất trong ba cái này **thực sự ngăn** được sự kiện đó.

## §6. Điều tôi KHÔNG kết luận

- **Không** phán quyết Alibaba an toàn hơn hay kém hơn OpenAI. Cả hai đều là
  chuyển ra nước ngoài; Đ.25 áp **như nhau**. Chế độ pháp lý của nơi nhận là
  yếu tố **phải đánh giá trong hồ sơ**, không phải yếu tố tôi phán quyết.
- **Chưa đọc** *Product Terms of Service* (mức hợp đồng) — mới ở mức tài liệu.
- 🔴 **Vẫn chưa ai trả lời tôi:** *hồ sơ đánh giá tác động chuyển dữ liệu ra
  nước ngoài đã có chưa?* Tôi hỏi lần này là **lần thứ hai** (`c7a8217` §5). Nó
  **đang thiếu với OpenAI** ngay lúc này, độc lập hoàn toàn với Qwen — và nó
  quan trọng hơn việc chọn nhà cung cấp nào.

## Nguồn

- [Region, deployment scope & access domains](https://www.alibabacloud.com/help/en/model-studio/regions/)
- [What is Model Studio](https://www.alibabacloud.com/help/en/model-studio/what-is-model-studio)
- [Security certifications and privacy notice](https://www.alibabacloud.com/help/en/model-studio/privacy-notice)
- [Model monitoring](https://www.alibabacloud.com/help/en/model-studio/model-telemetry)
- [Free quota for new users](https://www.alibabacloud.com/help/en/model-studio/new-free-quota)
- [Đ.25 NĐ 13/2023 — hồ sơ ĐGTĐ, A05, 60 ngày](https://luatvietnam.vn/doanh-nghiep/chuyen-du-lieu-ca-nhan-ra-nuoc-ngoai-561-95414-article.html)
