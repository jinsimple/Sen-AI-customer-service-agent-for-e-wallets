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

---

## §8. Lượt đã bắn — "0 dòng" ĐÚNG nhưng **KHÔNG ĐỦ**: phép đếm bỏ sót một kho trạng thái

Tester bắn trước khi điều kiện tới, rồi đo hậu quả và báo **0 dòng mới ở CẢ HAI
Postgres**, mọi bảng. **Tôi kiểm và không bác con số đó.** Họ cũng tự viết vào
hồ sơ đúng cách đọc ngược — *"số 0 nói **lượt bị chặn không ghi**, không nói
**đường thật an toàn**"* — đó là câu quan trọng nhất trong báo cáo của họ, và
nó giữ nguyên cảnh báo ADR-025 ở §2.

**Nhưng phép đếm chỉ phủ Postgres.** [ĐO] ngay bây giờ:

```
fin05-redis-1  — TOÀN BỘ kho, đúng MỘT khoá:
   refresh:3eee797a…                       TTL còn 604.311 s
   JWT_REFRESH_EXPIRE_DAYS_CUSTOMER = 7d  = 604.800 s
   ⟹ khoá được tạo cách đây ≈ 489 s  ≈ 8 phút 9 giây
```

⟹ **Lượt đo ĐÃ ghi trạng thái** — một phiên đăng nhập vai `customer`, còn sống
7 ngày. Không có khoá `ratelimit:` nào còn lại (cửa sổ trượt đã hết hạn), nhưng
hạn ngạch **đã bị tiêu** lúc chạy.

**Mức độ: THẤP** — một vé phiên, tự hết hạn, **không chạm bảng bằng chứng nào**.
Kết luận đầu của tester đứng. Cái sai không nằm ở con số, **nằm ở phạm vi của
phép đếm**.

### ⟹ Điều kiện ④ phải mở rộng, và đây là dạng tổng quát

> **Một phép đo chạy qua hệ thật để lại dấu ở MỌI kho trạng thái nó chạm, không
> chỉ ở kho ta nghĩ tới.** Phải **liệt kê kho TRƯỚC**, rồi đếm **từng kho** —
> không đếm *"chỗ tôi nghĩ nó sẽ ghi"*.

Danh mục tối thiểu cho `/agent/chat`: **Postgres** (bảng nghiệp vụ) ·
**Redis** (phiên · refresh · rate-limit · concurrency) · **Chroma** (nếu chạm
nạp kho) · **log/trace** (tệp, Jaeger) · **phía nhà cung cấp** (token đã tiêu,
và bản ghi phía họ — §2 hồ sơ Qwen).

*(Đây là **khuôn mặt thứ ba trong một ngày** của cùng một luật: đo **trọn vẹn**
thứ mình đang nói tới, không đo **phần mình đang chú ý**. Sáng nay là kích thích
gửi cho model; trưa là runtime sinh ra nó; giờ là kho trạng thái nó chạm.)*

### Và ghi nhận đúng chỗ đáng ghi nhận

Tester tự chỉ ra Luật 10 của họ canh chiều *"bộ đo làm méo phép đo"*, còn chiều
*"bộ đo để lại dấu trong hệ đang chạy"* thì **không luật nào trong mười bốn luật
canh**. Họ nêu khoảng trống đó **trước khi** có ai đo ra khoá Redis trên. Phép
đo ở §8 này **không bác họ — nó xác nhận khoảng trống họ vừa tự tìm ra**, bằng
một ca cụ thể.

## §9. Đính chính "cặp lệch thứ sáu" — **không phải lệch**

Tester đo `SITE_DOMAIN` **rỗng**, tôi đo **`localhost`**. [ĐO]: biến
`SITE_DOMAIN` **không tồn tại** trong môi trường của `fin05-backend-1` (đếm =
**0**); giá trị `localhost` tôi đọc là của **`fin05-caddy-1`** — nơi biến đó
**thực sự được dùng** để dựng site block.

⟹ **Hai phép đo đều đúng, về hai đối tượng khác nhau.** Đây là **lần thứ sáu**
đúng một khuôn: *hai người đo "cùng một thứ" mà thực ra đo hai vật*. Cách chữa
vẫn y hệt bốn lần trước — **nói rõ VẬT trước khi so SỐ**. Kết luận không đổi:
**không ngăn xếp nào tự khai được nó phục vụ tên miền nào.**

---

## §10. Rà chính đề nghị của tôi (BFF xuyên `GET /health`) — mặt trái + hai thứ PO chưa biết khi duyệt

PO duyệt kèm bốn điều kiện. Tôi là người đề xuất nên tôi nợ **mặt trái**, và có
**hai dữ kiện đo được** đổi mức quan trọng của điều kiện ②.

### ① 🔴 `/openapi.json` · `/docs` · `/redoc` ĐANG BẬT trên backend — [ĐO]

```
docker exec fin05-backend-1 → http://127.0.0.1:8010
   /openapi.json   HTTP 200 · 28.470 byte · 31 path
   /docs           HTTP 200
   /redoc          HTTP 200
```

`main.py:131` dựng `FastAPI(title=…, version=…)` — **không** `docs_url=None`,
**không** `openapi_url=None`.

**Hôm nay KHÔNG rò:** Caddy chỉ proxy frontend (`handle { reverse_proxy
frontend:3000 }`) cộng đúng một path WebSocket ⟹ backend không với tới được từ
ngoài. Đây là **rủi ro tiềm ẩn**, không phải rò đang xảy ra.

**Nhưng nó đổi hạng điều kiện ② của PO từ "nên có" thành "chặn land".** Nếu bản
xuyên của coder khớp theo **tiền tố** thay vì **khớp chính xác**, thứ rò ra
không phải một endpoint sức khoẻ — mà là **toàn bộ bề mặt API 31 path kèm lược
đồ và mô hình xác thực**, cho bất kỳ ai. Đó là món quà giá trị nhất một kẻ dò
tìm có thể nhận.

**Sửa danh sách ca âm bản của PO cho đúng thứ tồn tại:** `GET /health/../ready`
**không** kiểm được gì — **`/ready` KHÔNG TỒN TẠI** trong `main.py` (chỉ có
`/health`; `/ready` mới nằm ở playbook, chưa hiện thực). Ca âm bản phải bắn vào
thứ **có thật**:

```
/openapi.json · /docs · /redoc          ← giá trị cao nhất, PHẢI 404
/tickets · /resolutions · /policy-docs · /policy-search   ← dữ liệu thật
/health/ · /healthz · /health/x · POST /health            ← biến thể khớp
```

### ② Mặt trái của chính đề nghị tôi — nói ra thay vì bỏ qua

Mở `/health` công khai là **đánh đổi**: ta trả một ít **dấu vân tay** để mua khả
năng trả lời *"tôi đang nói chuyện với ngăn xếp nào"* **bằng máy thay vì bằng
người**. Cái trả ra: `build_commit` (SHA ngắn của repo **riêng tư** — không tra
ngược ra mã), `build_at` (thời điểm deploy), `env`, và `db_kind`/`db_name`.

**Tôi vẫn đề nghị làm** — nhưng nếu PO muốn siết: **`db_kind`/`db_name` là hai
trường có giá trị NGOÀI thấp nhất và giá trị dò-tìm cao nhất.** Câu hỏi cần trả
lời chỉ cần `env` + `build_commit` + `build_at`. ⟹ **Tuỳ chọn rẻ:** bản công
khai trả **ba trường**, giữ `db_*` cho đường nội bộ. Chi phí gần bằng 0, và nó
gỡ đúng phần tôi thấy khó biện minh nhất.

### ③ Tôi nhận điều kiện ③ và nói rõ sẽ kiểm gì sau khi coder land

Không kiểm chung chung *"không chứa bí mật"* mà kiểm bốn thứ, trên **hệ đã
land**, không trên diff:

1. `curl` từ **ngoài** → so **từng khoá** trả về với danh sách được duyệt;
2. bắn **đủ** danh sách ca âm bản ở §10.① → mọi ca **404/405**;
3. xác nhận `/health` **vẫn không chạm DB/Redis** (đo bằng đếm truy vấn hoặc
   đơn giản là dừng Postgres rồi gọi lại — nó phải vẫn `200`);
4. đối chiếu `authority-matrix.yaml` đã có dòng route công khai mới (điều kiện
   ④ của PO) **và** `check_contracts.py` xanh.

### ④ Một hạng mục độc lập, không dính quyết định `/health`

**Tắt `docs_url`/`redoc_url`/`openapi_url` khi `APP_ENV=production`.** Không ai
cần chúng ở production; chúng là thứ **đắt nhất khi rò** và **rẻ nhất khi tắt**.
Đề nghị này **đứng độc lập** — nên làm kể cả khi `/health` **không** được mở.

---

## §11. 🔴 Ngăn xếp `fin05-*` **KHÔNG phải môi trường đo có kiểm soát** — hai bằng chứng độc lập

Tester đo lại Redis lúc **05:26** và ra bức tranh khác tôi (05:18):

```
05:18 (tôi)    1 khoá
05:26 (tester) 14 khoá — 8 vé refresh sinh 05:24:10→05:25:18, cộng
               ratelimit:login_phone:0387000001 (ttl 15s)
               ratelimit:otp_request:USR-0001   (ttl 13s)   ← có người ĐANG đăng nhập
```

### Bằng chứng ① — phiên khác đang dùng ngăn xếp này

Tám vé trong hai phút, **sau** phép đo của tôi, không ai trong ba phiên Claude
nhận. *(Định danh `USR-0001` + SĐT `0387000001` có dạng **tài khoản hạt giống**,
nên nhiều khả năng là người trong đội hoặc một kịch bản tự động — **không** có
dấu hiệu người dùng thật. Nhưng "nhiều khả năng" không phải "đã quy được".)*

### Bằng chứng ② — và cái này nặng hơn: **trạng thái BỊ XOÁ bởi bên không ai kê được**

Tester tuyên bố rõ **không xoá** vé của họ và sẽ chỉ xoá **sau khi có xác
nhận**. Tôi đo lúc **05:29**:

```
EXISTS refresh:3eee797a…   → 0        ← vé của tester BIẾN MẤT
DBSIZE fin05-redis-1       → 0        ← TOÀN BỘ kho trống
DBSIZE fin05ttl-redis-1    → 22       ← ngăn xếp kia vẫn còn nguyên trạng thái
```

**Không phải hết hạn, không phải khởi động lại, không phải đuổi bộ nhớ** —
[ĐO]: `RestartCount=0`, `uptime 145.525s` (≈40h), `run_id` không đổi,
`maxmemory-policy=noeviction`, và vé refresh có vòng đời **7 ngày**. Trong mã
cũng **không có** `FLUSHDB`/`FLUSHALL` nào (`revoke_family` chỉ thu hồi **một
họ**, `auth.py:183`). ⟹ **Có ai đó xoá tay, giữa 05:26 và 05:29.**

*(Tôi khai: mọi lệnh Redis của tôi là chỉ-đọc — `--scan`, `TTL`, `EXISTS`,
`DBSIZE`, `INFO`, `CONFIG GET`. Không phải tôi.)*

### ⟹ Hệ quả: Luật 15 §4b của tester **đúng nhưng chưa đủ**

Họ vá *"quy trách nhiệm bằng **DẤU**, không bằng **HIỆU SỐ**"* — đúng, và nó
chữa được chiều **thừa** (hiệu số gộp việc người khác vào việc mình).

**Nhưng §11② chỉ ra chiều còn lại: trên hệ dùng chung, dấu cũng bị người khác
XOÁ.** Tester quyết định giữ vé lại làm bằng chứng, và bằng chứng **biến mất**
trong ba phút. ⟹ trên hệ dùng chung ta **không chứng minh được sự CÓ MẶT của
dấu mình** (người khác xoá), cũng **không chứng minh được sự VẮNG MẶT** (người
khác ghi). Kế toán tốt hơn **không** cứu được.

> **Kết luận vận hành: phép đo có-ghi phải chạy trên một ngăn xếp DÙNG RIÊNG.**
> Không phải vì sạch số, mà vì trên hệ dùng chung **không mệnh đề nào về dấu vết
> chứng minh được**, theo cả hai chiều. Đây là điều kiện thứ **năm**, và nó thay
> thế phần lớn công dụng của điều kiện ④.

### Một mẩu bằng chứng YẾU cho câu hỏi ngăn xếp — đừng dùng thay câu trả lời của PO thật

Việc `fin05-redis-1` **bị xoá trắng phiên** hợp với hành vi trên một ngăn xếp
**dev** hơn là trên ngăn xếp đang phục vụ người thật (xoá trắng Redis ở đó =
đăng xuất toàn bộ người dùng). **Cùng hướng** với suy đoán của PO-agent. **Nhưng
đây là bằng chứng yếu và gián tiếp** — không được dùng thay cho câu hỏi đóng ở
§6. Ghi lại vì nó là dữ kiện, không phải vì nó kết luận.

## §12. Bản ghi phía nhà cung cấp cho ~500 lượt v4 — đóng nhánh này, không để mở

Tester đưa lại điểm của tôi và ghi rằng nó **áp ngược** cho ~500 lượt v4 đã
chạy: dữ liệu **đã rời hạ tầng ta**, và đó là kho **duy nhất không đếm lại
được, không xoá được**.

**Đóng nhánh, mức THẤP, với lý do đo được:** kích thích của v4 là **8 câu kịch
bản tổng hợp** do tester soạn, chạy dưới **123 ký tự system prompt tự soạn**, và
**không có tool nào thực thi** (lượt chết ở cửa OTP ⟹ không kết quả tool nào
quay lại model). ⟹ thứ đã rời hạ tầng là **văn bản tổng hợp + mô tả tool của
ta**, **không có dữ liệu cá nhân của ai**.

Phần **không** đóng, và nó thuộc hồ sơ Qwen (`4a55e77` §2) chứ không thuộc vụ
này: mô tả tool của ta — tức **một phần thiết kế nội bộ** — nằm trong bản ghi
của hai nhà cung cấp, 30 ngày (Alibaba) và không rõ hạn (OpenAI). Không phải
PII, không phải sự cố; là **dữ kiện cho hồ sơ Điều 25**, ghi để không phải phát
hiện lại.

---

## §13. 🔴 ĐÍNH CHÍNH §11: **"có người xoá tay" là SAI.** Thủ phạm là `tests/conftest.py`

Tester truy tiếp bằng đường của họ và bác kết luận của tôi. **Tôi kiểm lại và
không cãi** — Redis tự khai:

```
cmdstat_flushdb: calls=437        ← khớp CHÍNH XÁC số tester đưa
tests/conftest.py — fixture autouse=True gọi get_default_client().flushdb()
                    TRƯỚC MỖI test
```

Chạy `docker exec fin05-backend-1 pytest` thì `REDIS_URL=redis://redis:6379/0`
— **Redis THẬT** — và fixture cuốn sạch nó trước mỗi test. Không ai xoá tay:
**bộ test của tester xoá vé của chính tester**, 437 lần tính tới giờ.

**Chỗ tôi sai, và nó có hình dạng rõ:** ở §11 tôi loại trừ hết hạn · restart ·
eviction · `FLUSHDB` trong `src/` — rồi kết luận *"có người xoá tay"* từ việc
**không còn nghi can nào TRONG PHẠM VI TÔI NHÌN**. Phạm vi đó dừng ở `src/`.
Nghi can nằm ở `tests/` — vùng tôi **không có lý do nào để nhìn vào**, và đúng
vì thế tôi đã coi như nó không tồn tại.

> **Vắng mặt bằng chứng trong phạm vi mình soi ≠ vắng mặt bằng chứng.** Sáng nay
> tôi cảnh báo PO-agent đúng câu này về `cloudflared`; buổi chiều tôi vi phạm
> nó. Cách chữa giống hệt cách chữa cả ngày: **khai PHẠM VI cùng lúc với khai
> KẾT LUẬN** — *"không nghi can nào trong `src/`"* đứng vững; *"có người xoá
> tay"* thì không.

## §14. Rà cả HỌ theo luật đội — và kết quả nói lên bản vá nào là đúng

Redis bị lộ vì fixture **mượn tài nguyên của tiến trình**. Hai anh em còn lại:

| Kho | Fixture làm gì | Kết luận |
|---|---|---|
| **Postgres** | `db_session` **TỰ DỰNG** engine SQLite riêng trong `tmp_path` (`conftest.py:110-112`); `DATABASE_URL` chỉ tồn tại vì `src/config.py` đọc lúc import | ✅ **an toàn theo kiến trúc** — không bao giờ chạm DB thật, kể cả khi env trỏ vào Postgres |
| **Chroma** | test RAG monkeypatch `store.search`; ca duy nhất chạm index thật chỉ **ĐỌC** (`test_thanh_phan_tai_lieu_kho.py`), không `reset()`/`delete_collection` | ✅ an toàn |
| **Redis** | `get_default_client()` — **MƯỢN client toàn cục của tiến trình** | 🔴 nguồn của 437 lần |

⟹ **Bất đối xứng nằm ngay trong một file, cách nhau chưa tới 50 dòng:** fixture
DB **tự dựng** tài nguyên; fixture Redis **mượn**. Cái tự dựng **cô lập theo
kiến trúc**; cái mượn cô lập **theo giả định về một biến môi trường**.

> **Luật rút ra: fixture phải TỰ DỰNG tài nguyên của nó, không mượn tài nguyên
> của tiến trình.** Cổng `RuntimeError` của tester là bản vá **đúng và cần**,
> nhưng nó là một **phép KIỂM**, không phải **sự CÔ LẬP**. Hình mẫu cô lập đã
> nằm sẵn trong cùng file — `tmp_path`.

**Và tester đúng khi nói điều kiện ⑤ của tôi KHÔNG đủ cho ca này:** ngăn xếp
dùng riêng cũng bị chính fixture đó xoá sạch ngay lần đầu ai chạy pytest vào nó.
**Cổng chặn tại NGUỒN, ⑤ chặn tại PHẠM VI** — cần cả hai, và cổng mạnh hơn.
*(Mệnh đề ở §11 — "trên hệ dùng chung không chứng minh được CÓ MẶT lẫn VẮNG MẶT
của dấu" — vẫn đứng; chỉ đổi ví dụ cho chiều "thiếu".)*

## §15. Bản vá mới ở MỘT container — [ĐO] ngăn xếp kia vẫn đang mở

```
fin05-backend-1     có cổng "TỪ CHỐI flushdb"        → 1 (tester docker cp)
fin05ttl-backend-1  có cổng                          → 0   🔴 VẪN BẢN CŨ
fin05ttl-redis-1    cmdstat_flushdb                  → chưa có lệnh nào
                    DBSIZE                           → 22 khoá đang sống
```

⟹ **Lỗi vẫn còn nạp đạn ở `fin05ttl-*`.** Chưa nổ vì chưa ai chạy pytest trong
container đó — 22 khoá còn nguyên là bằng chứng. Ai chạy `docker exec
fin05ttl-backend-1 pytest` **trước khi image được dựng lại** sẽ xoá sạch chúng.

**Hai việc:**
1. **Không chạy pytest trong bất kỳ container nào** cho tới khi bản vá vào git
   **và** cả hai image được dựng lại. `docker cp` sửa **một container**, và mất
   khi dựng lại.
2. Coder land bản vá + dựng lại **cả hai** ngăn xếp. Sau đó tôi kiểm lại đúng
   ô `grep -c` trên **từng** container, không suy từ một cái.

*(Tester tự khai đã `docker cp tests/conftest.py` vào `fin05-backend-1` — ghi
vào container người khác đang dùng, dù nội dung đúng hơn bản cũ. Khai là đúng.
§15 là hệ quả trực tiếp của việc đó và là lý do khai có giá trị.)*

## §16. Sửa một vế trong §12 — theo đính chính của tester

Tôi viết *"lượt chết ở cửa OTP ⟹ không kết quả tool nào quay lại model"*. **Đúng
cho lượt `/agent/chat` hôm nay, SAI cho ~500 lượt v4** — v4 dùng **tool giả
lập** (`GIA_LAP`) **có** trả kết quả về model.

**Kết luận mức THẤP không đổi** (dữ liệu vẫn tổng hợp do tester soạn, **không
PII**), nhưng **lý do phải sửa**: thứ rời hạ tầng gồm **cả kết quả tool giả
lập**, không chỉ câu hỏi. Ghi đúng vì hồ sơ Điều 25 cần **liệt kê trường dữ liệu
thực sự đi**, không phải một câu tóm tắt nghe hợp lý.

## §17. Rút một mẩu bằng chứng của chính tôi, và khoanh BÁN KÍNH VỤ NỔ

### ① Rút — mẩu "bằng chứng yếu" ở §11 không còn giá trị

Tôi viết: *"`fin05-redis-1` bị xoá trắng phiên hợp với hành vi trên ngăn xếp
**dev** hơn"*. **Rút.** Việc xoá trắng **không phải hành vi của người vận hành**
— nó là **tác dụng phụ của `pytest`**. Nó **không nói gì** về việc máy nào phục
vụ Internet. Câu hỏi ngăn xếp vẫn **hoàn toàn** chờ PO thật.

*(Đây là mẩu bằng chứng tôi đã tự dán nhãn "yếu và gián tiếp" khi đưa ra. Nhãn
đó đúng, và nó là lý do rút nó tốn đúng một dòng thay vì tốn một vòng tranh
luận. Ghi lại như một lý lẽ ủng hộ việc dán nhãn mức chắc chắn ngay lúc phát
biểu.)*

### ② Ratify chẩn đoán của PO-agent về VÌ SAO nó ẩn được 437 lần

> **Bán kính của fixture không trùng với vật đang đo.** Fixture xoá Redis mà
> tiến trình `pytest` trỏ tới; test lại nói chuyện HTTP với ngăn xếp **khác**.
> ⟹ **Người gây ra không thấy hậu quả. Người chịu hậu quả không thấy nguyên
> nhân.**

Đó cũng là lý do phép suy luận *"vé biến mất ⟹ có người xoá tay"* nghe rất chặt
mà vẫn sai: tôi đi tìm **một tác nhân có chủ đích**, trong khi thủ phạm là **một
tác dụng phụ không quan sát được từ phía người gây ra**.

### ③ 🔴 Bán kính vụ nổ — hướng nguy hiểm là **XANH GIẢ**, không phải đỏ

Một lượt `flushdb` xen giữa một phép đo đang chạy có **hai** hậu quả, và chúng
**không đối xứng**:

| Bị xoá | Hậu quả | Nhìn ra sao |
|---|---|---|
| phiên · vé refresh | phép đo **gãy** | **ĐỎ** — thấy ngay, đi tìm |
| **bộ đếm rate-limit · cửa sổ trượt · bộ đếm cost/OTP** | ngưỡng **được đặt lại về 0** | 🔴 **XANH GIẢ — không triệu chứng** |

⟹ Chiều nguy hiểm chạm đúng **các chốt an toàn ta quan tâm nhất**: giới hạn tần
suất · chặn chi phí · độ tươi OTP. Một test *"gửi quá hạn mức phải bị chặn"* mà
bộ đếm bị cuốn giữa chừng sẽ **PASS vì lý do sai**.

**Khoanh phạm vi cho đúng, đừng thổi:**
- Quy ước dự án là `REDIS_URL=fake://ci` cho test/CI ⟹ **lượt chạy bình thường
  không chạm Redis thật**.
- Rủi ro chỉ hiện khi **có ai chạy `pytest` TRONG container** **đồng thời** với
  một phép đo khác dùng **cùng** Redis. Cần **đồng thời**, nên nó hiếm.
- **[ĐO] AUTH5-03 an toàn** (PO-agent kiểm): đo qua ngăn xếp `ttl` (8443), và
  `fin05ttl-redis-1` có `cmdstat_flushdb` = **chưa có lệnh nào**, 22 khoá nguyên.

**Việc còn lại:** với **mọi phép đo phụ thuộc trạng thái Redis tích luỹ** từng
chạy qua `fin05-*` (rate-limit · 429/F-33 · cost guard · độ tươi OTP), hoặc
**chạy lại sau khi cổng đã land**, hoặc **ghi rõ là chưa xác minh**. Ta **không
định vị được 437 lần đó trong thời gian** — `INFO commandstats` chỉ có tổng,
không có mốc — nên **không thể loại trừ từng lượt bằng lập luận**, chỉ bằng chạy
lại.

### ④ Điều khó chịu phải nói ra: lời khuyên của chính tôi là thứ NẠP ĐẠN cho lỗi này

Suốt hôm nay tôi lặp lại — đúng — rằng **phải kiểm trong container, đừng tin một
phép đo chạy trên runtime mượn**. Và **`docker exec … pytest` chính là cách người
ta làm đúng lời khuyên đó** — cũng chính là cách duy nhất kích hoạt lỗi này.

⟹ Không rút lời khuyên; **thêm vế còn thiếu**: *chạy trong container để **ĐỌC**
trạng thái thật là đúng; chạy **BỘ TEST** trong container thì bộ test mang theo
đồ nghề dọn dẹp của nó.* **Quan sát và thực thi là hai việc — công cụ của việc
sau không được dùng cho việc trước.**
