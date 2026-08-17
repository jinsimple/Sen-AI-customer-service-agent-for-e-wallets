# Điều kiện trước khi đo "đường thật" qua `/agent/chat`

> Vai: **security** · 2026-08-17 · viết **trước** khi lượt đo xảy ra, sau khi
> tester đề xuất **hoãn v5, chạy đường thật trước** (đề xuất đi xa hơn khuyến
> nghị của tôi — tôi ủng hộ hướng, nhưng nó mở một mặt rủi ro chưa ai nêu).

## §1. Trước hết, nói rõ phép đánh đổi — v5 và đường thật **KHÔNG thay thế nhau**

Tester đọc đề nghị của tôi (*"đừng dựng lại payload nữa"*) và đẩy tới **hoãn
v5**. Hướng ưu tiên **đúng**: trước một buổi test 150 người thật, câu cần trả
lời là **hành vi sản phẩm**, không phải **so model với model**.

Nhưng phải khai cái đang bị đổi đi, đừng để nó trôi qua như một nâng cấp:

| | v5 (so cặp) | đường thật (`/agent/chat`) |
|---|---|---|
| số biến đổi so với v4 | **một** (prompt) | **nhiều** (prompt · lược đồ · cả đường ống · RAG · DB · OTP) |
| trả lời được | *chỉ dẫn có hiệu lực không* | **hành vi sản phẩm** |
| dùng làm **phân đôi** | ✅ tốt nhất ta có | ❌ quá nhiều biến |
| dùng làm **sự thật nền** | ❌ | ✅ **duy nhất** |

⟹ Hoãn v5 **không nâng cấp phép đo**; nó **đổi** một phép so sạch lấy một sự
thật nền nhiều biến. Đổi đúng lúc này — nhưng nếu đường thật trả về *"agent
không tra"*, câu **tiếp theo** sẽ là *"vì sao"*, và đó **đúng là câu v5 trả
lời**. Đừng huỷ v5; **hoãn** nó, và giữ nhãn `dd134bfddd09` để chạy lại được.

## §2. 🔴 Mặt rủi ro chưa ai nêu: **đường thật GHI DỮ LIỆU THẬT**

Bộ đo dựng-payload gọi API nhà cung cấp — **không chạm hệ ta**. `/agent/chat`
thì **chạy đủ vòng ReAct trên hệ thật**, nên một lượt đo *thành công* ở ca 4/6
**kết thúc bằng `create_ticket`** — tức **ghi vào DB**:

```
complaints            ← description_raw (LỜI KHAI), complaint_type, scope, fraud_signals
tickets               ← vào hàng chờ CSKH
investigation_logs    ← từng bước tool
tool_results          ← raw_json mỗi lượt gọi
messages              ← nội dung hội thoại (EncryptedText)
```

**Ba hệ quả, theo thứ tự nặng dần:**

### ① Vé giả vào hàng chờ CSKH — ngay trước test 150 người và demo mentor

`k=10 × 2 ca` ⟹ tới **20 khiếu nại giả** nằm trong hàng chờ mà người thật sẽ
nhìn. Nếu không phân biệt được vé đo với vé thật, buổi test 150 người **bắt đầu
với một hàng chờ đã bẩn**, và không ai biết con số nào của buổi đó là thật.

### ② 🔴 Ghi lời khai TỔNG HỢP vào bảng BẰNG CHỨNG — chạm thẳng ADR-025

`complaints.description_raw` là **nhóm A của ADR-025 — "lời khai, bằng chứng"**.
Cả thiết kế của nhóm A dựng trên **một** mệnh đề: *bản ghi này là lời khách nói,
không ai sửa* — đó là lý do ADR-025 **bác che-lúc-ghi** cho nhóm A (*"hệ thống
tự sửa chữ trong lời khai thì bản ghi mất giá trị chứng cứ"*).

**Bơm lời khai do máy sinh vào chính bảng đó là cùng một tổn hại, đi từ cửa
khác.** Không phải sửa lời khai có sẵn — mà **thêm lời khai chưa từng có người
nào khai**. Với một bảng mà giá trị duy nhất của nó là *"mọi dòng ở đây đều do
một người thật gõ"*, đây là quyết định **phải cố ý**, không được là **tác dụng
phụ của một phép đo**.

### ③ Cần phiên OTP thật ⟹ cần tài khoản thật

`create_ticket` đòi OTP step-up 15 phút, hai tool đọc đòi OTP 12 giờ. ⟹ lượt đo
phải chạy **dưới danh nghĩa một tài khoản**. **Bắt buộc là tài khoản hạt
giống** — không bao giờ là tài khoản của người thật, kể cả tài khoản của PO.

## §3. Bốn điều kiện — xin thoả TRƯỚC lượt đo, kể cả lượt thăm dò 2%

Áp cho **cả lượt ~24K để biến ước thành đo** — lượt đó cũng ghi DB y như lượt đầy đủ.

1. **Chạy trên ngăn xếp KHÔNG được lộ ra ngoài.** [ĐO] có **hai** ngăn xếp song
   song, mỗi cái một Postgres riêng: `fin05-*` (Caddy giữ cổng **80/443** của
   máy) và `fin05ttl-*` (Caddy **8443**, và Caddyfile nói rõ có **"đường
   tunnel"**). Cả hai đều `SITE_DOMAIN=localhost` ⟹ **tôi KHÔNG kết luận được
   cái nào đang phục vụ `app.adaptivealgo.uk`.** ⟹ **người chạy phải xác định
   chắc, bằng đo, trước khi bắn** — và bắn vào cái **không** được tunnel ra
   ngoài.
2. **Tài khoản hạt giống, khai trong hồ sơ đo.** Không tài khoản người thật.
3. **Vé đo phải phân biệt được** — quy ước rõ trong `description_raw` (vd tiền
   tố `[DO-LUONG v6]`) **và** một mốc thời gian, để người dọn sau này lọc được
   mà không phải đoán. Chốt **cách dọn trước khi bắn**, không phải sau.
4. **Ghi số dòng đã sinh vào kết quả** — `complaints`/`tickets`/
   `investigation_logs`/`tool_results` trước và sau lượt đo. Không đếm được thì
   không dọn được, và không chứng minh được là đã dọn.

⚠️ **Nếu điều kiện 1 không xác định được chắc chắn:** dừng, hỏi PO thật. Đây
đúng loại việc *"cần xác nhận người dùng trước khi làm"* — nó ghi vào một cơ sở
dữ liệu có thể đang phục vụ người thật, và **không hoàn tác được bằng cách chạy
lại**.

## §4. Điều tôi KHÔNG kết luận

- **Không** biết ngăn xếp nào ra Internet — nêu bằng chứng ở §3.1, để người có
  quyền xác nhận trả lời.
- **Không** phản đối lượt đo. Đường thật là **phép đo đúng** cho câu hỏi ②, và
  đề xuất biến **ước thành đo** bằng một lượt 2% là kỷ luật đúng — tôi chỉ đòi
  nó **không ghi bừa vào bảng bằng chứng** trên đường đi.
