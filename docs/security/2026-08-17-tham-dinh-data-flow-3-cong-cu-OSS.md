# N3 — Thẩm định data-flow 3 công cụ hạ tầng (trước khi vào compose)

> Vai: **security** · 2026-08-17 · theo mẫu F-LOG-3 (trường được ghi ·
> retention · cờ đỏ · điều kiện land). Brief: `2026-08-17-dot-nang-cap-oss.md`.

## ⚠️ Đọc trước: ranh giới hiểu biết của tôi trong tài liệu này

Tôi phân biệt rõ ba loại phát biểu, vì trộn chúng là cách tài liệu bảo mật trở
nên vô dụng:

| | |
|---|---|
| **[KIẾN TRÚC]** | hình dạng luồng dữ liệu — ổn định qua các phiên bản, tôi tự tin |
| **[PHẢI KIỂM]** | tên cờ config, giá trị mặc định — **phụ thuộc phiên bản**, tôi **không** khẳng định từ trí nhớ |
| **[PHÁN ĐOÁN]** | đánh giá rủi ro của tôi |

Mọi mục **[PHẢI KIỂM]** phải xác nhận **trên đúng phiên bản sẽ deploy**, và
xác nhận **bằng quan sát** (đọc DB, bắt gói mạng), **không phải bằng đọc tài
liệu** — đây đúng bài học `hiện-diện ≠ hiệu-lực`: một cờ có tên đúng trong
config không chứng minh nó có hiệu lực.

---

# ① LiteLLM proxy

## [KIẾN TRÚC] Nó nằm ở đâu trong luồng — và đây là điểm quan trọng nhất

LiteLLM **chen vào giữa app và nhà cung cấp LLM**. ⟹ **toàn bộ prompt và
response đi qua nó**, gồm cả tin khách gõ và câu trả lời agent.

🔴 **Hệ quả mà tôi cho là nặng nhất, và chưa ai nêu:** nếu nó bật lưu payload,
ta vừa tạo ra **CỬA THỨ NĂM** của văn bản tự do khách hàng — **nằm ngoài bảng
bốn cửa của ADR-025**, ngoài pipeline scrub, với **retention riêng** và
**quyền đọc riêng**.

ADR-025 vừa được ký để **thống nhất** cách xử lý bốn cửa đó. Một cửa thứ năm
mọc lên **hai ngày sau** mà không qua cùng khung quyết định là đúng cách một
ADR trở thành giấy lộn.

## Trường được ghi

| Nhóm | Nội dung | Đánh giá |
|---|---|---|
| **spend/usage log** | model · token vào-ra · chi phí · virtual key · thời điểm | ✅ **an toàn** — không nội dung, đúng thứ ta cần cho budget |
| **request/response log** | **prompt đầy đủ + câu trả lời đầy đủ** | 🔴 **cửa thứ năm** — xem trên |

## [PHẢI KIỂM] Bốn câu, xác nhận bằng quan sát

1. **Tắt lưu nội dung**: LiteLLM có cơ chế che nội dung tin nhắn trong log
   (*tên cờ khác nhau theo phiên bản — tra tài liệu bản sẽ deploy*).
   **Nghiệm thu = đọc thẳng DB của proxy sau vài lượt gọi thật, grep một chuỗi
   mốc đã gửi. Không thấy = đạt.** Đúng khuôn tôi đã dùng cho F-LOG-3.
2. **Callback ra ngoài**: LiteLLM có hệ thống `success_callback`/
   `failure_callback` gửi được sang **Langfuse · Helicone · S3 · Datadog…**
   ⟹ **danh sách callback phải RỖNG**, hoặc chỉ chứa đích **nội bộ**. Bất kỳ
   mục nào trỏ ra ngoài = **đường xuất dữ liệu**, đúng lớp F-30.
3. **Telemetry mặc định** (câu PO hỏi riêng): LiteLLM **có** telemetry ẩn danh
   trong lịch sử phiên bản. Phải **tắt minh thị** và **xác nhận bằng quan sát
   mạng**, không bằng cờ config. → xem "điều kiện land" §L2.
4. **Master key**: khoá cấp quyền **đúc key khác**. Phải **khác mọi secret ứng
   dụng**, không nằm trong git, xoay được — và **không được chép từ máy dev**
   (đúng bài học `JWT_SECRET_KEY` trùng dev/prod vừa rồi).

## [PHÁN ĐOÁN] Budget-per-key là control BẢO MẬT, không chỉ control chi phí

Brief xếp nó vào mục chi phí. Tôi đề nghị đọc nó thêm một tầng: nó là
**ngăn thiệt hại** khi một key bị lộ hoặc một vòng lặp hỏng — **giới hạn nổ**.
Điều đó đổi cách đặt hạn mức: đặt theo **mức đủ dùng bình thường**, không theo
**mức trần chịu được**.

## Cờ đỏ

- callback list **không rỗng** với đích ngoài hạ tầng
- proxy DB chứa prompt/response nguyên văn
- master key trùng bất kỳ secret nào của app hoặc chép từ `.env` dev
- không có hạn mức mặc định cho key mới (key mới = ngân sách vô hạn)

## Điều kiện land

- **L1** — grep chuỗi mốc trong DB proxy sau lượt gọi thật: **0 lần xuất hiện**
- **L2** — quan sát kết nối ra của container proxy trong một lượt chạy: **chỉ**
  tới nhà cung cấp LLM. Không có đích lạ nào.
- **L3** — key mới mặc định **có** hạn mức; kiểm bằng cách đúc một key rồi đọc
  lại thuộc tính
- **L4** — master key khai trong `.env` production **riêng**, không chép từ dev

---

# ② Langfuse (self-host)

## [KIẾN TRÚC] Bản chất: nó là **bản sao thứ hai của mọi hội thoại**

Mục đích tồn tại của Langfuse **là** lưu trace = prompt + response. Self-host
giải quyết đúng **một** vấn đề — dữ liệu không rời hạ tầng (đóng F-30). Nó
**không** giải quyết:

- một **bản sao thứ hai** của dữ liệu hội thoại, trong **DB khác**, với
  **retention khác** và **quyền đọc khác**;
- 🔴 **một đường ĐỌC không qua audit-log.** ADR-025 QĐ 2 Pha-1 vừa bắt
  **audit-log mọi lượt đọc nhóm A**. Ai có tài khoản Langfuse **đọc được toàn
  bộ hội thoại khách mà không để lại vết trong hệ thống của ta** — tức
  **đi vòng qua một quyết định vừa ký hai ngày trước**.

## [PHÁN ĐOÁN] Giải: **tách theo MỤC ĐÍCH**, đừng tách theo mức scrub

PO nêu đúng bài học 40%: scrub nội dung rồi lưu sẽ cho ra thứ **vừa có thể rò,
vừa hỏng nghĩa** — vô dụng cho việc gán nhãn, mà vẫn là bản sao.

Nhưng hai mục đích của Langfuse có **nhu cầu dữ liệu khác hẳn**:

| Mục đích | Cần gì | Đề nghị |
|---|---|---|
| **cost/trace theo lượt** (số 2) | model · token · chi phí · latency · **id** | **metadata, KHÔNG nội dung** — đúng nguyên tắc F-LOG-3 |
| **màn gán nhãn 30 ca** (số 1) | **nội dung thật** | **chỉ nạp một tập ĐƯỢC CHỌN** — 30 ca, không phải mọi trace |

⟹ **Langfuse KHÔNG nhận nội dung của traffic sản xuất.** Nó nhận metadata cho
mọi lượt, và **nội dung chỉ cho tập eval được curate**. Như vậy "bản sao thứ
hai của mọi hội thoại" **không tồn tại ngay từ đầu** — rẻ hơn nhiều so với
dựng retention/quyền-đọc/audit riêng cho nó rồi canh mãi.

## Trường được ghi (theo đề nghị trên)

- **mọi trace**: `trace_id` · model · token · chi phí · latency · trạng thái ·
  **id** (`chunk_ids`/`doc_ids`/`ticket_id`) — **không** prompt, **không**
  response
- **tập eval curate**: nội dung đầy đủ, **đánh dấu rõ là dữ liệu eval**, tách
  project/dataset riêng

## Retention

Metadata: theo nhu cầu vận hành, **ngắn**, **tách khỏi 5 năm của ADR-025 QĐ 3**
(đây là dữ liệu vận hành, không phải hồ sơ khiếu nại).
Tập eval: theo vòng đời bộ eval, xoá khi bộ hết dùng.

## Cờ đỏ

- traffic sản xuất chảy vào Langfuse **kèm nội dung**
- telemetry-về-nhà chưa tắt (**[PHẢI KIỂM]** — có biến môi trường tắt, tên tuỳ
  phiên bản)
- tài khoản Langfuse **dùng chung**, không map về người thật ⟹ mất luôn khả
  năng truy "ai đã đọc"
- Langfuse mở ra ngoài internet (nó là UI có auth riêng, **không** nằm sau
  authority-matrix của ta)

## Điều kiện land

- **M1** — chạy vài lượt thật, mở Langfuse UI: **không thấy nội dung tin
  khách/câu trả lời** ở trace sản xuất
- **M2** — quan sát kết nối ra của container Langfuse: **không có đích ngoài**
- **M3** — chỉ nghe trên mạng nội bộ / sau reverse proxy có auth; **không**
  publish
- **M4** — tài khoản **theo người**, không dùng chung

---

# ③ Semantic cache (chỉ thiết kế — sóng 3)

## 🔴 [PHÁN ĐOÁN] Ranh giới NAIVE là ranh giới ta VỪA ĐO LÀ HỎNG

Cách đặt vấn đề tự nhiên — *"câu chính sách chung thì cache, câu cá nhân thì
không"* — đòi **phân loại ngữ nghĩa câu hỏi**. Đó **đúng cơ chế** vừa đo được
là **không tất định** ở F-31: cùng một câu, **6/8 lượt** phân loại một kiểu,
2/8 kiểu khác.

**Không được dựng ranh giới an toàn dữ liệu trên một bộ phân loại đã đo là
không tất định.** Một lần phân loại sai ở đây = **trả câu trả lời chứa dữ liệu
của khách A cho khách B**.

## Ranh giới đề nghị: quyết theo **XUẤT XỨ của câu trả lời**, không theo **hình dạng câu hỏi**

Đây **đúng hình dạng origin-rule** đã được đo và ký cho O3 — *"hình dạng giả
được, xuất xứ không"*:

> **Một câu trả lời chỉ được cache khi CHỨNG MINH ĐƯỢC nó độc lập với người
> dùng.** Mặc định: **KHÔNG cache**. Tính cache-được phải được **chứng minh**,
> không phải **giả định**.

**Bốn điều kiện, tất cả máy kiểm được, phải thoả ĐỦ:**

| # | Điều kiện | Kiểm bằng |
|---|---|---|
| **C1** | lượt đó **không gọi tool phạm vi người dùng** (`lookup_transaction` · `get_customer_history` · bất kỳ tool nhận `user_id`/`trans_id`) — chỉ `search_policy` | `tool_calls` |
| **C2** | **câu hỏi** không chứa định danh phạm vi người dùng (mã GD · SĐT · STK · số tiền cụ thể) | bộ dò đã có |
| **C3** | câu trả lời **đã qua lọc đầu ra O1-O4 và sạch** | cờ có sẵn |
| **C4** | khoá cache gắn **phiên bản kho RAG** | tem kho |

**C1 là điều kiện chính** — nó trả lời *"câu trả lời này được dựng từ dữ liệu
của ai"*, thay vì đoán *"câu hỏi này trông có cá nhân không"*.

**C3 chống một chế độ hỏng riêng của cache:** không có nó, một câu trả lời rò
rỉ được cache **một lần** rồi phục vụ **N lần** — cache **nhân bản** một lỗi
đơn lẻ thành lỗi hệ thống.

**C4 nối thẳng ADR-026:** trạng thái duyệt tài liệu **đổi được**. Một câu trả
lời cache từ tài liệu **sau đó bị thu hồi duyệt** vẫn tiếp tục được phục vụ ⟹
cache **vô hiệu hoá** cơ chế duyệt. Khoá cache phải đổi khi kho đổi.

## [PHÁN ĐOÁN] Bất đối xứng quyết định ngưỡng

Cache **trượt** = chậm thêm một chút. Cache **trúng sai** = **dữ liệu khách A
sang khách B** — sự cố phải báo cáo, không phải sự cố chất lượng.

⟹ Ngưỡng **không phải** *"thường thì an toàn"* mà là *"chứng minh được độc lập
người dùng"*. **Fail-closed**, và nghi ngờ thì không cache.

## Cờ đỏ

- cache key dựng từ **embedding câu hỏi đơn thuần** — hai câu khác nhau về
  chủ thể có thể **gần nhau trong không gian vector** ("số dư của tôi" ~ "số dư
  của anh ấy")
- cache dùng chung mà **không** có C1
- cache không invalidate khi kho đổi (C4)
- ngưỡng tương đồng đặt theo **hit-rate mong muốn** thay vì theo an toàn

## Điều kiện land (sóng 3, không sớm hơn)

- **S1** — ca đối kháng: hai user hỏi câu **gần giống nhau về ngữ nghĩa** nhưng
  **khác chủ thể**; chứng minh **không** dùng chung entry
- **S2** — ca C3: một câu trả lời bị O1-O4 chặn **không bao giờ** vào cache
- **S3** — ca C4: đổi trạng thái duyệt một tài liệu ⟹ câu trả lời cũ **không
  còn được phục vụ**
- **S4** — chạy **cùng lượt** với bộ đối chứng hit-rate, **cấm chạy lẻ**
  (Luật 2): một cache "an toàn tuyệt đối" bằng cách không bao giờ trúng cũng
  đạt S1–S3

---

# Phụ lục — N1 reranker: một góc chuỗi cung ứng đáng ghi vào sổ probe

PO nói N1 chạy local nên không cần ý kiến trước. Đồng ý về **luồng dữ liệu**
(không có gì rời máy). Nhưng có **một** góc đáng ghi:

🟡 **Định dạng file trọng số quyết định mức rủi ro.** Trọng số `.bin` của
PyTorch dùng **pickle** ⟹ **nạp file là chạy mã**. Định dạng `safetensors`
thì không.

⟹ Đề nghị (rẻ, làm một lần): **ưu tiên `safetensors`** · **ghim theo revision
hash**, không theo tag/branch (tag có thể bị đẩy lại) · ghi hash vào hồ sơ đo
cùng `he_thong` (brief đã đòi model-hash — đây là lý do bảo mật, không chỉ lý
do tái lập).

Rủi ro "model xếp hạng sai có chủ đích" thì **thấp và tự lộ**: bộ 47 ca sẽ
thấy. Rủi ro **mã chạy lúc nạp** thì **không tự lộ** — đó mới là cái đáng ghim.

---

# Tổng hợp cho PO

| | Chặn land không? | Việc phải làm trước |
|---|---|---|
| **LiteLLM** | không, nếu qua L1–L4 | chứng minh **không lưu nội dung** + **không gọi ra ngoài**, bằng **quan sát** |
| **Langfuse** | không, nếu qua M1–M4 | chốt **metadata-only cho traffic sản xuất**; nội dung chỉ cho tập eval curate |
| **Semantic cache** | **chưa thiết kế xong thì chưa bàn land** | chốt **C1–C4** như ranh giới, trước khi ai viết dòng code nào |

**Một câu tôi muốn đặt lên đầu báo cáo:** cả ba công cụ này đều **thêm một nơi
dữ liệu hội thoại tồn tại**. ADR-025 vừa mất nhiều công để **thống nhất** bốn
nơi như thế. Nếu đợt này thêm ba nơi nữa mà mỗi nơi có retention/quyền-đọc/
audit riêng, thì **cái ta vừa xây xong đã lạc hậu trước khi khô mực** — không
phải vì công cụ xấu, mà vì **chưa ai hỏi chúng thuộc cửa nào**.
