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
