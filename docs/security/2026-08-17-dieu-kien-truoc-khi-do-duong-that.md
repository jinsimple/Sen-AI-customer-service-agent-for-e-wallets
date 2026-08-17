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

---

## §5. Tôi thử biến "bằng chứng vắng mặt" thành bằng chứng dương — **và THẤT BẠI. Ca đối chứng cứu.**

PO-agent đo bốn lần, tất cả là **vắng mặt** (không container tunnel · không
tiến trình `cloudflared` · không launchd/`~/.cloudflared` · IP tên miền là dải
Cloudflare ≠ IP công cộng của máy). Họ tự khai đó là vắng mặt và vẫn hỏi PO
thật. Tôi thử tìm một phép **dương tính**.

### Phép thử — và ca đối chứng bác chính nó

```
① gửi một dấu duy nhất tới tên miền công khai
   curl "https://app.adaptivealgo.uk/?probe-sec-…"          -> http 307
   grep dấu đó trong log 4 container (caddy ×2, frontend ×2) -> 0 / 0 / 0 / 0
   → nhìn như "KHẲNG ĐỊNH: không phải máy này"

② CA ĐỐI CHỨNG — gửi dấu tương tự tới CHÍNH ngăn xếp cục bộ
   curl -k "https://localhost/?ctrl-sec-…"                   -> http 307 (y hệt)
   grep dấu đó trong log                                     -> 0 / 0
```

⟹ **Một yêu cầu tôi BIẾT CHẮC đã tới ngăn xếp cục bộ cũng không để lại dấu
nào.** Các container **không ghi log truy cập**. ⟹ **Phép thử ① không có khả
năng phát hiện điều nó định phát hiện; kết quả âm tính của nó KHÔNG mang thông
tin.**

Không có ca đối chứng, tôi đã báo *"xác nhận không phải máy này"* — một **khẳng
định sai** trên đúng câu hỏi mà khẳng định sai đắt nhất. Đây là Luật 2 (*ca đối
chứng bắt buộc*) tự chứng minh giá trị của nó trong vòng ba phút.

### Các đường đọc-thuần khác đều đóng — [ĐO]

- Caddy **chỉ lộ frontend** (`handle { reverse_proxy frontend:3000 }`, cộng
  đúng một path WebSocket) ⟹ `/health` của backend — nơi có `env` ·
  `build_commit` · `build_at` — **không với tới được từ ngoài**.
- `/api/health` · `/api/ready` → **404** · `/bff/health` → **307 `/login`**.
  Không có đường xuyên tới health của backend.
- Băm module font trùng nhau ở cả ba nguồn — **nhưng không phân biệt được gì**:
  chúng cũng trùng giữa **hai** build cục bộ khác commit, nên chúng không phải
  dấu vân tay của build.

⟹ **Tôi KHÔNG kết luận được bằng đo từ máy này.** Quyết định hỏi PO thật của
PO-agent là **đúng**, và giờ nó có thêm một lý do: **các phép đo rẻ ở đây hoặc
là vắng mặt, hoặc là mù.**

## §6. Câu hỏi đóng nên gửi kèm — biến câu trả lời của PO thật thành phép đo

Thay vì hỏi *"production nằm ở đâu"* (trả lời bằng trí nhớ), đưa họ **một lệnh**
và xin **dán nguyên văn kết quả**:

```
curl -s http://<máy chạy production>:8010/health
```

`/health` **cố ý công khai, không xác thực, không chạm DB**, và **cố ý không
chứa host/user/mật khẩu** (`main.py:1479-1481`) ⟹ dán ra ngoài an toàn.

Đối chiếu với hai ngăn xếp trên máy này — [ĐO] vừa xong:

```
fin05-backend-1    env=development · build_commit=61631ad · build_at=2026-08-17T05:07:39Z
fin05ttl-backend-1 env=development · build_commit=526dce7 · build_at=2026-08-17T04:01:18Z
```

**Khác `build_commit`/`build_at` ⟹ khác máy, dứt điểm.** Và lưu ý sẵn: **cả hai
ngăn xếp ở đây đều `env=development`** — nếu bản phục vụ Internet cũng trả
`development` thì đó là **một finding riêng**, độc lập với câu đang hỏi.

## §7. Đề nghị nhỏ, trả nợ đúng tình huống này (vùng tech-lead, cần PO duyệt)

Câu *"tôi đang nói chuyện với ngăn xếp nào"* hôm nay **chỉ trả lời được bằng
cách hỏi người**. Chính docstring của `/health` nói nó sinh ra sau một sự cố y
hệt (hai stack song song, hai trình duyệt giống nhau, khác database) — nhưng
tác dụng đó **dừng ở trong mạng nội bộ** vì BFF không xuyên tới nó.

**Đề nghị:** cho BFF xuyên **đúng `/health`** ra ngoài (chỉ GET, đã tự lược bỏ
thông tin nhạy cảm theo thiết kế). Đây là **mở một bề mặt công khai**, nên phải
là quyết định cố ý của PO — nhưng nó biến một câu hỏi-người thành một câu
hỏi-máy, đúng loại nợ vừa làm cả đội đứng chờ.
