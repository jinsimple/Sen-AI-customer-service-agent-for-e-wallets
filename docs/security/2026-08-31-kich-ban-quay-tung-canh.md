# Kịch bản quay từng cảnh — 🟢 CHỐT BẢN CUỐI 31/08

> Vai: `security`. Bổ sung cho `docs/security/2026-08-31-soat-quay-video-demo-duoc-cam-len-hinh.md`
> (bản đó trả lời KHÔNG ĐƯỢC làm gì; tài liệu này trả lời NÊN làm gì, để người cầm máy quay MỘT LƯỢT,
> không phải vừa quay vừa nghĩ — mỗi lần quay lại là một lần nữa có nguy cơ lọt thứ không nên lọt).
>
> **Đọc file kia TRƯỚC khi quay** — mọi mục "🔴 CẤM" ở đó vẫn áp dụng nguyên vẹn ở đây, không lặp lại
> chi tiết, chỉ trỏ tới bằng số cảnh tương ứng.
>
> Luồng đã xác nhận chạy trọn (QA/QC 31/08, tự đi lại kịch bản này như người cầm máy thật — làm đúng
> chữ, không tự suy thêm): đăng nhập → OTP → xem giao dịch → mô tả khiếu nại → **agent tra cứu VÀ xin
> xác nhận tạo hồ sơ trong CÙNG một bong bóng** (Cảnh 5, gộp lại 31/08 — xem cảnh đó) → CSKH xem →
> trình sếp → **sếp duyệt CŨNG đã xác nhận chạy được** (P0 vá xong, xem Cảnh 8).
>
> 🟡 **CẬP NHẬT 31/08 — 6 chỗ QA/QC vướng khi đi đúng chữ, đã sửa vào bản này:** lệnh tra OTP còn
> chung chung (mục Chuẩn bị + Cảnh 2 + Cảnh 8), rủi ro 6 ô OTP hiện số khi gõ (Cảnh 2 + Cảnh 8),
> Cảnh 4 mô tả sai đường (phải bấm nút "Báo lỗi giao dịch này" trên rail, không gõ tự do), Cảnh 6
> chưa có câu xác nhận đã kiểm, Cảnh 7 thiếu cách tìm ticket giữa hàng trăm dòng, Cảnh 8 sai luồng
> màn hình (`/approve` chỉ là hàng chờ, nút Duyệt thật nằm ở `/tickets/[id]`).
>
> 🔴 **VÒNG 2, CÙNG NGÀY — PO xác nhận đúng cả 6 điểm QA/QC nêu thêm, sửa hết, không cần phân xử:**
> lệnh Chuẩn bị thiếu tên 3 tài khoản + cách lấy `user_id`; Cảnh 2 có HAI đoạn nói về "dừng quay"
> tách rời nhau, đọc gộp lại có thể hiểu nhầm thành "bật máy quay rồi mới gõ" — SỬA thành MỘT câu
> duy nhất; Cảnh 8 trước đó chỉ nhắc chung "qua terminal riêng", không có câu dừng-quay đầy đủ như
> Cảnh 2 — chép nguyên câu sang, đúng luật "điều kiện phải nằm TRONG câu", người đọc riêng một cảnh
> không thấy được câu ở cảnh khác; Cảnh 5 thiếu câu trả lời mẫu khi agent hỏi lại; mục "Sau khi quay"
> còn câu cũ nhắc "khi đã điền" trong khi Cảnh 8 đã điền xong từ vòng 1.
>
> 🟢 **QUYẾT ĐỊNH LỊCH — PO chốt: QUAY TRÊN BẢN HIỆN TẠI, TRƯỚC KHI cổng ép-tra-trước land.** Lý do:
> đường quay đã xác nhận chạy trọn trên bản này (băm mã `9c17c5684c9a`), 246 ca đo + báo cáo benchmark
> PO đã gửi đều mô tả ĐÚNG bản này — video và báo cáo phải nói về CÙNG một sản phẩm. Cổng mới chưa
> qua kiểm nào, không nên buộc buổi quay (có hạn chót) chờ nó (chưa chứng minh). **Đây LÀ bản dùng để
> quay thật, sau khi sửa xong 6 điểm dưới đây.**
>
> 🔴 **TỒN ĐỌNG, ghi ngay kẻo quên lý do:** sau khi cổng ép-tra-trước land và đo xong, **kịch bản này
> PHẢI soát lại** — Cảnh 5 gần như chắc chắn đổi (cổng khiến agent TRA NGAY thay vì có thể hỏi lại
> khách như hành vi Cảnh 5 mô tả hiện tại).

## Chuẩn bị TRƯỚC KHI bấm quay — làm một lần, không phải mỗi cảnh

### ⚡ THẺ HÀNH ĐỘNG — 10 việc, theo THỨ TỰ LÀM. Chi tiết & lý do nằm ngay dưới.

*(Thêm 01/09: mục Chuẩn bị đã phình từ ~50 lên 129 dòng trong một ngày. Lý do thì đáng giữ, nhưng
người cầm máy lúc 20h **không đọc 129 dòng** — họ cần biết PHẢI LÀM GÌ. Thẻ này là thứ đọc lúc đó;
phần dưới là thứ đọc khi có gì bất thường.)*

```
LÀM SỚM, thong thả — không cần sát giờ quay
  1 □ Mở https://localhost:59443/ trong ĐÚNG trình duyệt sẽ quay → bấm qua CẢNH BÁO ĐỎ một
      lần → đóng tab.  🔴 Bỏ bước này = khung hình đầu tiên nói "không an toàn".
  2 □ Terminal RIÊNG, trên màn hình KHÁC màn hình quay (để tra OTP).
  3 □ Caption CHỮ "dữ liệu sinh tổng hợp" đã chuẩn bị — BẮT BUỘC, lời thoại không thay được.
  4 □ Tắt DevTools, đóng tab/cửa sổ dễ Alt-Tab nhầm.
  5 □ Ba danh khoản trong tay:
        khách  0974000145 / Demo@123   (USR-0145 — ĐỪNG dùng USR-0001, xem Cảnh 2)
        CSKH   0353000201 / Demo@123
        sếp    0905000205 / TestP0Otp!2026   (KHÔNG phải Demo@123)

SÁT GIỜ QUAY — bốn phép đo, ~1 phút, chạy theo thứ tự này
  6 □ docker exec fin05-qa-stripe-backend-1 cat /app/.bam_ma_nguon
      → PHẢI là 9c17c5684c9a. Khác ⟹ DỪNG, KHÔNG BẤM MÁY.
  7 □ Hạn mức model (lệnh ở mục bên dưới) → BA nhánh, đừng bỏ nhánh giữa:
        200 = quay được
        403 = VẪN QUAY ĐƯỢC nhưng BÁO NGAY — model đầu bể cạn, còn 6 model, xoay tự tụt
        401 = DỪNG, KHÔNG BẤM MÁY (khoá sai)
  8 □ Cert còn hạn (lệnh openssl bên dưới) → notAfter phải cách giờ quay vài tiếng.
      🟢 Đo 01/09 14:41: hạn tới 02:40 sáng mai — gần như chắc chắn xanh.
  9 □ Phiên OTP của khách CHƯA "tươi" (lệnh psql ở Cảnh 2) → rỗng = Cảnh 2 quay được.
 10 □ ĐĂNG NHẬP rồi QUAY NGAY — token sống 15 phút. Nghỉ lâu hơn thì đăng nhập lại.
```

🔴 **BỐN thứ TUYỆT ĐỐI không làm trong lúc quay:** dựng lại bất kỳ container nào (đặc biệt `caddy` —
mất chuỗi gia hạn cert) · sửa CSDL ngăn quay · bấm link **"Tra cứu chính sách"** trên nav CSKH ·
**đăng nhập thử bằng `0974000145`** (xem ngay dưới).

### 🟢 CẢNH 2 AN TOÀN HƠN TA TƯỞNG — và phép kiểm cũ đo NHẦM CHỖ *(đính chính 01/09 15:50)*

**Bản 15:41 của mục này SAI CƠ CHẾ, đã gỡ.** Nó viết rằng đăng nhập thử bằng `0974000145` sẽ tạo
"phiên OTP tươi 12 tiếng" trong CSDL và giết Cảnh 2. Đọc mã thì không phải vậy:

- `otp_verified_at` **không nằm trong CSDL**. Nó là một trường **trong token** (`src/auth.py:46`).
- Đăng nhập cấp token với `otp_verified_at=None` — **đóng cứng**, `src/api/main.py:339`.
- `/agent/chat` đọc `current_user.otp_verified_at`, tức **từ token** (`main.py:697`), không tra bảng.

⟹ **Mỗi lần đăng nhập mới là một lần OTP được đòi lại.** Lịch sử trong `auth_sessions` không ảnh
hưởng. Cảnh 2 kích hoạt vì **trình duyệt vừa đăng nhập**, không vì tài khoản "chưa dùng gần đây".

🔴 **Hệ quả cho thẻ hành động:** phép kiểm số **9** (truy `auth_sessions` xem có phiên tươi không)
**không phải là cổng của Cảnh 2** — nó đo một bảng liên quan, không đo thứ quyết định. Giữ lại thì
được, nhưng đừng dựa vào nó, và **đừng DỪNG quay chỉ vì nó ra khác kỳ vọng**.

**Điều kiện thật của Cảnh 2, thay cho mục 9:** vào bằng **cửa sổ ẩn danh / đã đăng xuất sạch**, rồi
đăng nhập tại chỗ. Còn đăng nhập sẵn từ trước là rủi ro thật — nhưng vì **token cũ còn hiệu lực**,
không vì CSDL.

*Vẫn nên tránh diễn tập bằng `0974000145`* — lý do còn lại là `failed_attempts`/`locked_at`
(gõ sai OTP 3 lần có thể khoá). Đo 01/09 15:50: **0 phiên bị khoá**, tài khoản sạch.

> **Vì sao giữ nguyên cả đoạn sai ở đây thay vì xoá:** kết luận *"đừng đụng tài khoản đó"* đúng ở cả
> hai bản, nên nếu chỉ sửa lặng lẽ thì không ai biết **lý do** đã đổi. Một kết luận đúng dựng trên cơ
> chế sai sẽ **gãy im lặng** ngay lần đầu hoàn cảnh đổi.

---


```
□ Terminal RIÊNG đã mở sẵn, đặt ở màn hình/máy KHÁC màn hình đang quay, kết nối được DB ngăn
  fin05-qa-stripe — dùng để tra otp_code trong auth_sessions khi cần (xem cảnh 2 và cảnh 8).
  Lệnh THẬT, copy-paste được (xác nhận QA/QC 31/08):

  Cảnh 2 (OTP đăng nhập, theo user_id khách demo):
    docker exec fin05-qa-stripe-postgres-1 psql -U fin05 -d fin05 -tAc \
      "select otp_code from auth_sessions where user_id='<user_id khách demo>' \
       and otp_status='pending' order by created_at desc limit 1"

    Cách lấy `user_id` để điền vào lệnh trên: tra theo SĐT tài khoản khách demo đã dùng ở Cảnh 1 —
    docker exec fin05-qa-stripe-postgres-1 psql -U fin05 -d fin05 -tAc \
      "select user_id from users where phone='<SĐT khách demo>'"

  Cảnh 8 (OTP duyệt, theo resolution_id):
    docker exec fin05-qa-stripe-postgres-1 psql -U fin05 -d fin05 -tAc \
      "select otp_code from auth_sessions where resolution_id='<resolution_id>' \
       and otp_status='pending' order by created_at desc limit 1"

  ⚠️ Nếu phải quay LẠI một đoạn: bấm xin OTP lại TRÊN UI TRƯỚC, rồi mới chạy lệnh tra DB — không thì
  lệnh trả về mã CŨ đã hết hạn/không khớp phiên hiện tại.
□ Xác nhận trạng thái banner môi trường + OTP_DEMO_MODE lúc quay THẬT (đã tắt hay chưa) —
  đối chiếu docs/security/2026-08-31-soat-quay-video-demo-duoc-cam-len-hinh.md, đầu file, mục
  "CẬP NHẬT — TÀI LIỆU CHƯA CHỐT BẢN CUỐI" để biết đang ở nhánh nào (đã vá / chưa vá).
□ Caption hoặc lời mở đầu đã chuẩn bị: "Dữ liệu trong demo là dữ liệu sinh tổng hợp, không phải
  khách hàng thật."
□ Không mở DevTools, không có tab/cửa sổ nào khác dễ vô tình Alt-Tab vào khung quay.
□ Danh khoản đăng nhập demo đã biết trước, ĐỦ CẢ BA vai (không gõ sai, không phải thử lại nhiều lần).
  **[Điền 01/09 — QA/QC ĐĂNG NHẬP THẬT cả ba vai trên `https://localhost:59443`, không đọc CSDL rồi
  suy; không gửi lượt chat nào.]**
  - Khách (Cảnh 1-6): 🟢 **DÙNG `0974000145` / `Demo@123`** → vào `/chat`. `user_id` = **`USR-0145`**
    (điền vào lệnh `psql` Cảnh 2 ở trên).
    🔴 **ĐỪNG dùng `0387000001` (`USR-0001`)** — bản trước của mục này ghi tài khoản đó, **SAI cho
    buổi quay**: `USR-0001` đã xác thực OTP hôm nay nên **còn "tươi" tới 23:37 giờ VN** ⟹ Cảnh 2
    sẽ KHÔNG hiện ô OTP. Xem khối 🔴🔴 đầu Cảnh 2. Chỉ 2/200 tài khoản khách dùng `Demo@123`
    (`USR-0001` và `USR-0145`) — **không có lựa chọn thứ ba**, đừng thử tài khoản khác.
  - CSKH (Cảnh 7): **`0353000201` / `Demo@123`** → vào `/dashboard`.
    *(QA/QC đăng nhập THẬT thành công nhiều lần 01/09 — ghi ra để dòng này tin được ngang hai
    dòng kia, đúng đề nghị QA/QC: mỗi dòng phải tự đủ nghĩa khi đọc một mình.)*
  - Sếp/supervisor (Cảnh 8): tài khoản đăng nhập qua `/dang-nhap-noi-bo`, vai khác CSKH. **SĐT
    `0905000205`, mật khẩu `TestP0Otp!2026`.** 🔴 **KHÁC với `Demo@123` ghi trong `docs/STATE.md:758`
    — ĐỪNG dùng giá trị đó.** Tự xác minh 01/09 bằng cách so trực tiếp với `password_hash` thật trong
    CSDL ngăn `qa-stripe` (không đoán): Coder đã đổi mật khẩu này ngay trong CSDL ngăn `qa-stripe` khi
    test tay bản vá P0 tối 31/08 (có báo qua tin nhắn lúc đó, nhưng chìm giữa luồng chat) — **CHỈ
    riêng ngăn `qa-stripe`**, không phải thay đổi toàn cục, các ngăn khác vẫn dùng `Demo@123` bình
    thường. Không đổi lại giá trị trong CSDL (đụng CSDL ngăn dùng để quay có rủi ro không cần thiết)
    — sửa tài liệu thay vì sửa CSDL.
□ 🔴🔴 **CẢNH BÁO TLS — mở thử TRƯỚC KHI BẤM MÁY, đây là thứ lên hình ngay khung đầu tiên**
  *(phát hiện 01/09 13:15, chưa ai kiểm bao giờ vì QA/QC dùng Playwright — công cụ đó BỎ QUA lỗi
  TLS, nên chạy xanh cả ngày mà không ai thấy điều trình duyệt thật sẽ thấy.)*

  Đo thật: `curl https://localhost:59443/` **không** cờ `-k` → `curl: (60) SSL certificate problem:
  unable to get local issuer certificate`. Cấp bởi `CN=Caddy Local Authority - ECC Intermediate`,
  và CA gốc đó **KHÔNG có trong keychain nào** của máy (System = 0, login = 0).
  ⟹ **Trình duyệt sạch sẽ hiện TRANG CẢNH BÁO ĐỎ TOÀN MÀN HÌNH** *(“Kết nối của bạn không phải là
  kết nối riêng tư” / `NET::ERR_CERT_AUTHORITY_INVALID`)* trước khi tới `/login`.
  🔴 **Với một sản phẩm FINTECH, khung hình đầu tiên nói “không an toàn” là hỏng cả video.**

  **Cách xử — làm TRƯỚC khi bật máy quay, chọn một:**
  🟢 (a) **Mở `https://localhost:59443/` trong ĐÚNG trình duyệt sẽ quay, bấm qua cảnh báo MỘT LẦN,
     đóng tab.** Ngoại lệ được lưu theo trình duyệt ⟹ lúc quay vào thẳng, không cảnh báo.
     **Rẻ nhất, không đụng hệ thống, không cần quyền admin.**
  (b) Cài CA gốc của Caddy vào keychain (`docker cp` cert ra rồi thêm vào System keychain) — sạch
     hơn nhưng **đổi cấu hình tin cậy toàn máy**, cần cân nhắc, KHÔNG làm gấp trước giờ quay.
  ⚠️ **Đừng suy từ “hôm qua tôi mở được”** — ngoại lệ lưu theo **từng trình duyệt và từng hồ sơ**.
  Quay bằng cửa sổ ẩn danh / hồ sơ khác / trình duyệt khác là **cảnh báo quay lại**.

□ ⏱ **ĐĂNG NHẬP LẠI ngay trước khi bấm máy — đừng để phiên nguội** *(thêm 01/09)*
  `JWT_ACCESS_EXPIRE_MINUTES = 15` (`src/config.py`). Nếu đăng nhập sẵn rồi đi dựng đèn / tập lời
  thoại **quá 15 phút**, access token hết hạn **ngay giữa cảnh** — không ai gõ sai gì cả.
  Có cơ chế gia hạn ngầm (`frontend/src/proxy.ts`), và chú thích tại `proxy.ts:115-145` ghi lại một
  chuỗi bug ĐÃ TỪNG xảy ra đúng ở cơ chế đó *(“nhẹ khi bấm lại, CHẾT khi tầng UI chỉ thử đúng một
  lần”)*, khai là **ĐÃ VÁ** — nhưng **chưa ai xác nhận bản vá đó nằm trong ảnh đang chạy**
  (`9c17c5684c9a`), và đọc mã tĩnh **không** thay được điều đó.
  ⟹ **Đừng dựa vào gia hạn ngầm.** Cách rẻ nhất và chắc nhất: **đăng nhập là quay ngay.** Nghỉ giữa
  chừng quá 15 phút thì **đăng xuất, đăng nhập lại** trước khi quay tiếp.

□ ⏱ **Chứng chỉ TLS còn hạn tới khi nào** *(vòng đời chỉ 12 GIỜ — Caddy tự gia hạn, nhưng “tự động”
  không phải “chắc chắn”)*:
    echo | openssl s_client -connect localhost:59443 -servername localhost 2>/dev/null \
      | openssl x509 -noout -dates
  → `notAfter` phải cách giờ quay **ít nhất vài tiếng**. *(Đo 01/09 13:13: `notAfter = 01/09 11:40
  GMT = 18:40 giờ VN` — tức **có thể hết hạn NGAY GIỮA buổi quay chiều tối**. Caddy gia hạn theo chu
  kỳ 12h và đã gia hạn nhiều lần trong đêm, nên nhiều khả năng tự ổn — **nhưng phải ĐO LẠI, đừng suy
  từ “tối qua thấy nó gia hạn”**.)*
  🟢 **[CẬP NHẬT 01/09 14:41 — RỦI RO NÀY ĐÃ QUA]** Caddy **đã gia hạn đúng lúc 14:40 như dự đoán**;
  `notAfter` mới = **01/09 19:40 GMT = 02:40 VN sáng hôm sau** ⟹ **phủ trọn buổi quay chiều tối, dư
  ~8 tiếng.** Nhịp gia hạn đo được từ 15 lần trong log: **8,0 giờ đều tăm tắp** (vòng đời 12h ⟹ cert
  luôn còn ít nhất 4h dự trữ). Tiến trình `caddy` chạy liên tục **4 ngày**, chưa từng dựng lại — đó
  là ĐÚNG tiến trình đã gia hạn 15 lần. **Vẫn chạy lệnh trên trước khi quay** (30 giây), nhưng nay
  biết trước rằng nó gần như chắc chắn xanh.
  → Nếu `notAfter` sắp tới: đợi Caddy gia hạn (xem `docker logs fin05-qa-stripe-caddy-1 | grep renew`)
  🔴 **TUYỆT ĐỐI KHÔNG khởi động lại `caddy` để “ép gia hạn”** — dựng lại là mất cache, và ta đã mất
  một vòng sáng nay vì dựng lại làm rơi cấu hình.

□ 🔴 BẮT BUỘC, cùng lúc với phép kiểm băm bên dưới — **HẠN MỨC MODEL còn không**
  *(thêm 01/09: sáng nay agent CHẾT HẲN vì hết hạn mức free tier — `403` trên 3 model, rồi `400`
  ở model thứ tư làm cơ chế xoay DỪNG luôn. Khách chỉ thấy "hệ thống đang gặp sự cố kỹ thuật".
  Băm mã đúng KHÔNG bảo vệ được khỏi chuyện này: hạn mức nằm ngoài mã, và nó cạn dần theo giờ.)*

    docker exec fin05-qa-stripe-backend-1 python -c "
    import sys,json,urllib.request,urllib.error; sys.path.insert(0,'/app')
    from src.config import LLM_API_KEY, LLM_BASE_URL, LLM_MODEL_POOL
    m=LLM_MODEL_POOL[0]
    b=json.dumps({'model':m,'messages':[{'role':'user','content':'hi'}],'max_tokens':1}).encode()
    r=urllib.request.Request(LLM_BASE_URL.rstrip('/')+'/chat/completions',data=b,
        headers={'Authorization':'Bearer '+LLM_API_KEY,'Content-Type':'application/json'})
    try: urllib.request.urlopen(r,timeout=20); print(m,'-> 200 CON HAN MUC')
    except urllib.error.HTTPError as e: print(m,'->',e.code)"

  → **`200 CON HAN MUC`** ⟹ quay được. Sinh **1 token**, gần như không tốn gì.
  → **`403`** ⟹ model đầu bể đã cạn. **CHƯA phải dừng** — bể còn 6 model, xoay sẽ tự tụt xuống.
     Nhưng **báo ngay**, và biết trước rằng Cảnh 5 có thể chậm hơn hoặc trả lời khác lượt đã thử.
  → **`401`** ⟹ khoá sai. **DỪNG, KHÔNG BẤM MÁY.**
  *(Đo 01/09 13:10: `qwen3.6-plus-2026-04-02` → `200`. Con số này SẼ CŨ — chạy lại, đừng tin dòng này.)*
□ 🔴 BẮT BUỘC, làm CUỐI CÙNG — ngay TRƯỚC khi bấm quay Cảnh 1 (kiểm ở phút chót mới có nghĩa; kiểm
  đầu buổi rồi làm việc khác nửa tiếng thì thành lời khẳng định cũ). **[Tự chạy, xác nhận khớp trước
  khi ghi vào đây]:**
    docker exec fin05-qa-stripe-backend-1 cat /app/.bam_ma_nguon
  → phải in đúng: `9c17c5684c9a`
  → in ra thứ KHÁC ⟹ **DỪNG, KHÔNG BẤM MÁY, báo ngay** — nghĩa là ngăn đã bị dựng lại/đổi ảnh, mọi
  cảnh trong kịch bản này (đã kiểm trên đúng băm này) không còn đảm bảo đúng như mô tả.
  *(Lý do đây là PHÉP ĐO, không phải MỆNH LỆNH: lệnh cấm đụng `qa-stripe` phụ thuộc mọi người nhớ và
  tuân theo; một `docker compose up` vô hại nhắm nhầm ngăn không mệnh lệnh nào chặn được, nhưng phép
  đo 5 giây này thì luôn đúng bất kể ai quên gì.)*
```

## 🔴🔴 KHI NÀO Ô OTP HIỆN — đọc trước, đây là chỗ dễ khựng nhất (sửa 01/09, VÒNG 2)

🔴 **ĐÍNH CHÍNH BẢN 12:17 CỦA CHÍNH TÔI.** Bản đó viết *"Cảnh 2 xảy ra SAU Cảnh 4"* và
*"Cảnh 3 KHÔNG cần OTP"* — **SAI**. Rail giao dịch **CÓ** đòi OTP. Số cảnh **1→2→3→4→5 vốn đã
đúng**; tôi sửa một lỗi thật rồi tự thêm một lỗi mới. Bằng chứng:
`ChatClient.tsx:125-133` — `if (!otpVerified)` thì rail **không render**, chỉ hiện nút
**"Xác thực ngay"**; `customer_tools.py:829-831 / 878-880` — `get_customer_history` trả
`_OTP_REQUIRED_ERROR` khi chưa xác thực. QA/QC **nhìn thấy tận mắt** rail `USR-0145` đang khoá.

**Điều DUY NHẤT sai trong bản gốc:** câu *"ngay sau đăng nhập, bong bóng chat đầu tiên xin OTP"*.
**Ô OTP KHÔNG tự hiện.** Nó cần **một hành động của người dùng** — có hai đường:

```
Cảnh 1  đăng nhập → /chat
        → bong bóng đầu là LỜI CHÀO TĨNH của Sen (ChatClient.tsx:208-214)
        → rail "Giao dịch gần đây" hiện ở trạng thái KHOÁ + nút "Xác thực ngay"
Cảnh 2  ô OTP hiện — CHỈ SAU MỘT TRONG HAI:
        🟢 (a) BẤM NÚT "Xác thực ngay" trên rail        ← DÙNG ĐƯỜNG NÀY ĐỂ QUAY
           (b) gõ/bấm chip sinh ra một câu KHIẾU NẠI CÁ NHÂN
        → nhập 6 số → xác thực xong → rail MỞ KHOÁ
Cảnh 3  xem rail (nay đã mở)
Cảnh 4  bấm "Báo lỗi giao dịch này" → rồi mới hiện 4 chip con → chọn chip
Cảnh 5  agent tra cứu
```

**Hai đường này đi qua HAI CƠ CHẾ KHÁC HẲN NHAU — đo 01/09, đừng gộp:**
· **(a)** nút gọi `beginOtpFlow()` → `requestOtp()` **thẳng tới endpoint xác thực**
  (`ChatClient.tsx:324-326`, `:642`/`:679`). **KHÔNG gửi tin nhắn nào, KHÔNG qua agent, KHÔNG qua
  cổng nhận-diện-khiếu-nại của `graph.py`.** Vì thế nó chạy **ngay sau đăng nhập**, và **cái bẫy
  chip "Hoàn tiền" không liên quan gì tới đường này.**
· **(b)** gửi tin → server trả `duong === "can_otp"` → client **cũng gọi `beginOtpFlow()`**
  (`:472`). Đây mới là đường bị cổng `graph.py:1267-1276` chi phối (4 điều kiện, gồm
  `la_khieu_nai_ca_nhan`).

⟹ **Nói cho chính xác về câu gốc:** *"ngay sau đăng nhập… xin OTP"* sai ở chữ **"tự"** — phải **bấm
một nút**. Nhưng **VỊ TRÍ thì đúng**: OTP vẫn ở Cảnh 2, ngay sau Cảnh 1, trước Cảnh 3.

🟢 **Quay theo đường (a).** Ba lý do: nó là nút **hiện sẵn trên màn hình**, không phụ thuộc câu chữ;
nó tách bạch Cảnh 2 khỏi Cảnh 4 nên **thứ tự quay = thứ tự số cảnh**; và nó **miễn nhiễm với cái bẫy
chip "Hoàn tiền"** ở Cảnh 4 (xem cảnh đó) — vì OTP đã xong trước khi chạm chip.

⚠️ Nếu **cố ý** quay đường (b) cho tự nhiên hơn: **chip "Hoàn tiền" KHÔNG kích được OTP** — bắt buộc
đọc bảng ở Cảnh 4 trước.

## Cảnh 1 — Đăng nhập (khách)

- **Màn hình:** `/login`
- **Thao tác:** nhập SĐT + mật khẩu tài khoản khách demo, bấm đăng nhập.
- **Điểm nhấn muốn người xem thấy:** xác thực bằng mật khẩu thật (Argon2), không phải chọn vai trò
  tuỳ ý — hệ thống tự biết ai đang đăng nhập.
- **Ngoài khung hình:** không có thao tác tay nào cần chuẩn bị ở cảnh này.
- **Nhắc CẤM (xem file gốc mục 🔴-1):** badge môi trường ở topbar — nếu CHƯA vá, tránh khung hình
  góc trên-phải; nếu ĐÃ vá, không cần né nhưng vẫn không rê chuột qua vùng đó (thói quen an toàn).

## Cảnh 2 — Xác thực OTP phiên

🔴🔴 **CHẶN — ĐỌC TRƯỚC KHI BẤM MÁY (phát hiện 01/09, đo thật trên ngăn quay):**
**Nếu khách đã xác thực OTP trong vòng 12 giờ, cảnh này SẼ KHÔNG XẢY RA.** Đăng nhập xong là vào
thẳng `/chat`, **không có ô OTP nào để quay.** Không phải hỏng — đúng thiết kế
(`src/config.py:215` `OTP_VIEW_MAX_MINUTES = 12 * 60`).

Đo lúc 01/09 05:02 UTC trên `qa-stripe`: `USR-0001` có phiên `verified` lúc **04:37 UTC**
⟹ **còn "tươi" tới 16:37 UTC (23:37 giờ VN)** ⟹ **quay chiều tối nay bằng `USR-0001` thì Cảnh 2
KHÔNG hiện ô OTP.** Đây là hệ quả trực tiếp của việc QA/QC test tay cả ngày trên đúng tài khoản này.

**Cách xử — chọn MỘT, theo thứ tự ưu tiên:**
1. **Đổi tài khoản khách sang một `user_id` chưa xác thực hôm nay** (KHÔNG đụng CSDL, an toàn nhất).
   🟢 **DÙNG `USR-0145` / `0974000145` / `Demo@123`.** Đây là tài khoản **DUY NHẤT** thoả cả ba
   điều kiện — cả ba đều **đo thật**, không suy:

   | điều kiện | `USR-0001` | `USR-0145` ✅ | `USR-0097` |
   |---|---|---|---|
   | mật khẩu `Demo@123` còn đúng | ✅ | **✅** | ❌ **TỪ CHỐI** |
   | không có phiên OTP tươi <12h | ❌ tươi tới 23:37 | **✅ không có** | ✅ |
   | đủ giao dịch cho Cảnh 3-4 | 239 | **241 · to_bank 61** | 108 |

   🔴 **ĐÍNH CHÍNH — bản trước của mục này khuyến nghị `USR-0097`, SAI hai lần.** ① Mật khẩu không
   phải `Demo@123`, không đăng nhập nổi Cảnh 1. ② Cái "26/08" khiến tôi chọn nó là **ĐÚNG MỘT giao
   dịch lẻ**, gần như chắc chắn do ai đó test tay — không phải dữ liệu seed.

   **Đo toàn CSDL 01/09 — "kẹt ở 01/08" là tính chất của BỘ DỮ LIỆU, không phải của tài khoản:**
   ```
   2026-08-26  ->     1 GD     ← DUY NHẤT, của USR-0097
   2026-08-01  ->   663 GD     ← mọi thứ dừng ở đây
   2026-07-31  ->   676 GD
   ...        ~660 GD/ngày, liên tục từ 11/04
   ```
   **Chỉ 1/200 khách có giao dịch sau 01/08.** ⟹ Rail "Giao dịch gần đây" của **mọi** tài khoản đều
   hiện ngày 01/08 — không có lựa chọn nào "tươi hơn". Và rail của `USR-0097` sẽ hiện **một dòng
   26/08 rồi nhảy về 01/08**, trông LẠ HƠN một rail 01/08 đều đặn.
   ⟹ **Ngày dữ liệu KHÔNG phải tiêu chí chọn tài khoản.** Câu caption đã chuẩn bị — *"dữ liệu sinh
   tổng hợp, không phải khách hàng thật"* — đã trả lời đủ. **Đóng, đừng mở lại.**

   🔴🔴 **VÀ ĐÂY MỚI LÀ PHÁT HIỆN LỚN — quét toàn bộ 200 khách bằng chính hàm Argon2 của app:**
   > **CHỈ `USR-0001` và `USR-0145` nhận `Demo@123`. 198/200 tài khoản khách KHÔNG dùng mật khẩu này.**

   Không phải "một số tài khoản bị đổi tay" — mà **ngược lại**: hầu như **không** tài khoản nào từng
   có `Demo@123`. Ai đọc `Demo@123` thành "mật khẩu chung của khách demo" sẽ **đăng nhập hỏng 99%
   số lần thử**. Phép đối chứng xác nhận cách đo đúng: hai tài khoản QA/QC đăng nhập THẬT thành công
   đều `NHẬN`, còn `USR-0205` (đã đổi sang `TestP0Otp!2026`) đúng là `TỪ CHỐI`.

   ⚠️ Đổi tài khoản thì **rail giao dịch Cảnh 3 đổi theo** — chọn lại một giao dịch cho Cảnh 4
   (`USR-0145` có 61 giao dịch `to_bank`). **Cảnh 5 (agent điều tra) chưa ai đi thử trên tài khoản
   này — chưa kiểm ⟹ chưa hứa.**
2. ~~Quay Cảnh 2 sau 23:37 giờ VN, giữ nguyên `USR-0001`~~ — **không dùng được cho buổi quay
   chiều tối** (23:37 muộn hơn giờ quay dự kiến). Giữ lại làm phương án cuối nếu buổi quay dời
   sang khuya.
3. ~~Xoá bản ghi phiên trong CSDL~~ — **KHÔNG.** Kịch bản dòng 77 đã chốt: không đụng CSDL ngăn quay.

🔴 **Kiểm 30 giây ngay trước khi quay** (đừng tin dòng này, nó là số của 01/09):
```
docker exec fin05-qa-stripe-postgres-1 psql -U fin05 -d fin05 -tAc \
  "select otp_status, created_at from auth_sessions where user_id='<user_id khách>' \
   and otp_status='verified' and created_at > now() - interval '12 hours'"
```
→ **có dòng trả về ⟹ SẼ KHÔNG hiện OTP**, đổi tài khoản. **Rỗng ⟹ quay được.**

- **Màn hình:** `/chat`. 🔴 **[Sửa 01/09]** Ô OTP **KHÔNG** tự hiện sau đăng nhập — bản trước
  viết "bong bóng chat đầu tiên xin OTP", SAI. Nó hiện **sau khi bấm nút "Xác thực ngay"** trên
  rail giao dịch đang khoá (đường khuyến nghị), hoặc sau khi khách gửi một câu khiếu nại cá nhân.
  Xem khối "KHI NÀO Ô OTP HIỆN" ngay trước Cảnh 1.
- **Thao tác:** hệ thống hiện ô nhập OTP; người quay nhập mã.
- **Điểm nhấn:** đây là OTP PHIÊN LÀM VIỆC (xác thực danh tính), khác OTP giao dịch — nếu kịch bản
  lời thoại có nhắc, đây là chỗ hợp lý để nói "hệ thống không bao giờ hỏi OTP giao dịch hay mật khẩu
  ví qua chat".
- 🔴 **MỘT CÂU DUY NHẤT, ĐỌC ĐÚNG THEO ĐÚNG THỨ TỰ (sửa 31/08 vòng 2 — bản trước tách hai đoạn, đọc
  gộp có thể hiểu nhầm thành "bật máy quay rồi mới gõ" ⟹ 6 số OTP lên phim):**

  **Nếu OTP_DEMO_MODE ĐÃ tắt: DỪNG GHI HÌNH ngay trước khi mở terminal riêng — giữ máy quay TẮT
  xuyên suốt từ lúc mở terminal, chạy lệnh tra `otp_code` (điền `user_id` lấy theo hướng dẫn ở mục
  "Chuẩn bị"), đọc mã, quay lại cửa sổ chính, TỚI KHI gõ xong đủ 6 ô trên UI — chỉ BẬT LẠI máy quay
  SAU KHI 6 ô đã điền xong.** Không tách thành hai việc riêng (chỉ né terminal / chỉ né lúc gõ) —
  đây là MỘT khoảng dừng liên tục, không có điểm nào ở giữa được ghi hình.
  Rẻ hơn cắt/dựng phim: không cần hậu kỳ, không sợ quên cắt. Khán giả thấy panel OTP hiện ra, rồi
  thấy kết quả — thiếu đúng vài giây, không ai nhận ra thiếu.

  **Nếu OTP_DEMO_MODE CHƯA tắt lúc quay:** mã hiện thẳng trên UI ngay khi panel mở ra (xem file gốc
  mục 🔴-2 chỗ 1) — áp dụng CÙNG quy tắc dừng ghi hình như trên, từ trước khi panel hiện ra tới khi
  qua khỏi màn hình đó.

  *(Che ô nhập bằng chấm đã được PO CÂN NHẮC rồi RÚT LẠI — giá trị bảo mật thấp so với việc phá phép
  xác nhận độc lập QA/QC vừa làm; đưa vào tồn đọng, không làm gấp — xem file gốc.)*

## Cảnh 3 — Xem giao dịch gần đây

- **Màn hình:** `/chat`, rail "Giao dịch gần đây" hiện sau khi xác thực OTP.
  ✅ **[Xác nhận 01/09] Câu này ĐÚNG, giữ nguyên.** Ghi rõ vì bản 12:17 của tôi từng nói ngược
  ("Cảnh 3 KHÔNG cần OTP") và cả Review lẫn QA/QC đều đề xuất sửa dòng này theo bản sai đó —
  đừng ai sửa lại lần nữa. `ChatClient.tsx:125-133`: chưa xác thực thì rail **không render**,
  chỉ hiện nút "Xác thực ngay".
- **Thao tác:** lướt qua danh sách, dừng ở giao dịch sẽ dùng làm ví dụ khiếu nại.
- **Điểm nhấn:** rail chỉ hiện số tiền/ngày/mã giao dịch — **đã xác nhận bằng ảnh thật (QA/QC
  31/08)** không hiện tên/SĐT người liên quan, an toàn để lên hình nguyên trạng.
- **Nhắc:** đây là dữ liệu sinh tổng hợp trông giống thật (tên/SĐT seed đúng định dạng VN thật) —
  đúng lý do cần caption/lời mở đầu đã chuẩn bị.

## Cảnh 4 — Mô tả khiếu nại (chat)

🔴 **SỬA 31/08 — đường "gõ tự do" CHƯA được xác nhận tối nay, đừng quay đường đó chưa kiểm.**

- **Màn hình:** `/chat`, vẫn ở rail "Giao dịch gần đây" từ Cảnh 3.
- **Thao tác (đường ĐÃ xác nhận chạy, dùng đường này để quay):** bấm nút **"Báo lỗi giao dịch này"**
  ngay trên dòng giao dịch đã chọn ở Cảnh 3.
  🔴 **HAI TẦNG, không phải một** *(QA/QC đo thật 01/09 — bản trước gộp làm một, người quay sẽ tìm
  chip ngay mà không thấy)*: bấm **"Báo lỗi giao dịch này"** TRƯỚC → **RỒI** mới hiện 4 chip loại
  khiếu nại con → bấm chip khớp tình huống.
  **[Sửa 01/09 — bản trước ghi "Bị trừ tiền hai lần", KHÔNG có chip nào tên vậy.]** Bốn chip THẬT:

  | chip | câu tự sinh khi bấm | kích được ô OTP? |
  |---|---|---|
  | **"Chuyển nhầm"** | "Tôi bị chuyển nhầm tiền." | ✅ |
  | **"Tiền chưa về"** | "Tôi chuyển tiền mà bên kia chưa nhận được." | ✅ |
  | **"Trừ tiền 2 lần"** | "Tôi bị trừ tiền 2 lần cho cùng 1 giao dịch." | ✅ |
  | **"Hoàn tiền"** | "Tôi được duyệt hoàn tiền nhưng chưa thấy tiền về." | ❌ **KHÔNG** |

  🔴🔴 **ĐỪNG BẤM CHIP "Hoàn tiền" nếu còn cần quay Cảnh 2.** Đo thật 01/09 bằng chính hàm
  `la_khieu_nai_ca_nhan` (hàm thuần, 0 lời gọi model): câu tự sinh của chip này **không khớp** bộ
  nhận diện khiếu nại cá nhân ⟹ **cổng OTP không nổ** ⟹ Cảnh 2 biến mất, và trông y hệt "hệ thống
  hỏng". Ba chip kia đều kích được.
  **Câu gõ tay dự phòng** (đã đo, đều kích được) nếu muốn đường tự nhiên hơn:
  *"Tôi bị trừ tiền hai lần cho một giao dịch"* · *"Tôi bị mất 500.000đ trong tài khoản"* ·
  *"Tôi chuyển nhầm 500.000đ cho người khác tối qua"*.
  **Câu KHÔNG kích** (đã đo, đừng dùng làm câu mở đầu): *"xin chào"* · *"Phí chuyển tiền là bao
  nhiêu?"* · *"Chính sách hoàn tiền thế nào?"*.
- **Điểm nhấn:** thao tác bấm, không phải gõ — nhanh, ít khả năng lỗi chính tả/gõ nhầm khi quay
  nhiều lượt. Nếu kịch bản MUỐN có đoạn gõ tự do (cho tự nhiên hơn), đó là một nhánh KHÁC, cần ai
  xác nhận riêng bằng thực tế trước khi đưa vào quay — không suy đoán nó cũng chạy được.
- **Ngoài khung hình:** không có.

## Cảnh 5 — Agent tra cứu & xác nhận tạo hồ sơ

⚠️ **[Thêm 01/09 — QA/QC]** Nếu quay theo đường **(b)** (không bấm "Xác thực ngay" trước, mà để
chip/câu khiếu nại kích OTP), thì **Cảnh 2 xen vào GIỮA Cảnh 4 và cảnh này**: bấm chip → ô OTP
hiện → **dừng ghi hình, lấy mã, nhập** → rồi agent mới trả lời. Đọc lại đoạn dừng-ghi-hình ở
Cảnh 2 TRƯỚC. Quay theo đường **(a)** khuyến nghị thì không có bước xen này — OTP đã xong từ
trước Cảnh 3.

🔴 **CƠ CẤU LẠI 31/08 — gộp Cảnh 5 + Cảnh 6 cũ thành MỘT cảnh, theo đúng hành vi thật QA/QC quan sát
được, không phải theo suy đoán ban đầu về sản phẩm.** Bản trước viết hai cảnh tách rời: "Cảnh 5 —
agent điều tra, có thể hỏi lại làm rõ" rồi "Cảnh 6 — agent tóm tắt & xin xác nhận, một lượt riêng".
**Thực tế đo được (QA/QC, đường bấm nút → chip ở Cảnh 4):** agent trả về **MỘT bong bóng DUY NHẤT**
gộp sẵn kết quả tra cứu + câu hỏi xác nhận tạo hồ sơ — không tách thành hai lượt như kịch bản cũ giả
định. Người quay theo bản cũ sẽ đợi một bong bóng "chỉ hỏi làm rõ" không bao giờ tới rồi lúng túng
trước ống kính — đây đúng loại sai khác chỉ lộ ra khi có người đi thật qua sản phẩm, không lộ ra khi
viết kịch bản từ hiểu biết chung về luồng nghiệp vụ.
*(Số hiệu cảnh giữ nguyên "nhảy" 5 → 7, KHÔNG đánh số lại — nhiều tài liệu khác (checklist gốc,
`docs/security/2026-08-31-quy-trinh-soat-ban-ghi-tho.md`) đã tham chiếu "Cảnh 8" cụ thể, đổi số sẽ
làm lệch các tham chiếu đó. Không có Cảnh 6 riêng nữa — đã gộp vào đây.)*

- **Màn hình:** `/chat`, sau khi bấm chip ở Cảnh 4 — agent tự gọi tool tra cứu (hiện trạng thái "đang
  tra cứu" thoáng qua), rồi trả về MỘT bong bóng gộp: kết quả tra cứu + câu hỏi xác nhận tạo hồ sơ.
- **Thao tác:** không cần bấm gì thêm cho tới khi bong bóng đó xuất hiện — gõ câu xác nhận. **Hai câu
  ĐÃ XÁC NHẬN CHẠY ĐƯỢC (QA/QC 31/08, cả hai đều tạo vé thật)**, dùng câu nào cũng được:
  - *"Đúng, đúng giao dịch đó."* → tạo vé `TCK-0c9436641f04`.
  - *"Có, tôi đồng ý để bạn tạo hồ sơ khiếu nại giúp tôi."* → tạo vé (lượt xác nhận trước đó).
  Muốn chắc 100% khi quay, dùng nguyên một trong hai câu trên, đừng tự diễn đạt lại.
- **Điểm nhấn — QUAN TRỌNG NHẤT của cả video:** hai việc cùng lúc, cả hai đều đáng nói thành lời nếu
  kịch bản có thoại giải thích: (1) mọi số agent nhắc tới (số tiền, mã giao dịch, thời điểm) trong
  bong bóng phải khớp đúng dữ liệu vừa thấy ở Cảnh 3 — chứng minh "AI điều tra bằng tool thật, không
  bịa số liệu"; (2) dù gộp một bong bóng, agent vẫn CHỜ xác nhận rồi mới thật sự tạo vé — không tự ý
  tạo chỉ từ một câu mơ hồ, đây là cơ chế ADR-051 (hai LƯỢT GỌI TOOL tách biệt bên trong — đề xuất rồi
  mới tạo — dù hiển thị gộp một bong bóng cho khách). Nếu có thể, để camera đứng lâu hơn ở cảnh này so
  với các cảnh khác.
- **Ngoài khung hình:** không có.
- 🟡 **TỒN ĐỌNG, ĐIỀU KIỆN RÕ (cập nhật 01/09, đừng hiểu nhầm là phải sửa ngay):** cảnh này chỉ cần
  soát lại **NẾU sau này quay trên bản ĐÃ CÓ cổng "ép-tra-trước"**. Hiện tại (01/09): PO đã gỡ băng
  `src/`, Coder sắp dựng lại ảnh có cổng đó — **nhưng ngăn dùng để QUAY PHIM vẫn giữ bản KHÔNG có
  cổng**, nên mô tả Cảnh 5 ở trên **vẫn đúng cho buổi quay sắp tới**, không cần sửa gì bây giờ. Chỉ
  khi nào quyết định quay trên một bản build MỚI có cổng đó, mới cần xác nhận lại hành vi
  gộp-một-bong-bóng này còn giữ nguyên không.

## Cảnh 7 — CSKH xem hồ sơ

- **Màn hình:** đăng xuất khách → `/dang-nhap-noi-bo` (đăng nhập nhân viên) → `/dashboard` (vai
  CSKH) → `/tickets/[id]` (chi tiết đúng ticket vừa tạo).
- **Thao tác:** đăng nhập bằng tài khoản CSKH demo. **Cách tìm đúng ticket giữa hàng trăm dòng** (xác
  nhận QA/QC 31/08): gõ mã ticket (`TCK-...`) vào ô tìm kiếm đầu bảng (placeholder "Tìm theo mã
  ticket, mã khiếu nại, tên khách..."), Enter, bấm vào dòng duy nhất hiện ra. Mở xem trail điều tra.
- **Điểm nhấn:** CSKH thấy đầy đủ căn cứ (kết quả tool đã trích dẫn) nhưng **màn hình CSKH không có
  nút duyệt** — nếu kịch bản có thoại, đây là câu đắt giá nhất theo đúng tinh thần dự án ("đó không
  phải thiếu tính năng, đó là ràng buộc cứng số 1").
- **Nhắc:** dashboard cột KHÁCH HÀNG hiện đầy đủ họ tên seed trông giống thật (đã xác nhận ảnh thật)
  — cùng lý do cần caption dữ liệu sinh tổng hợp, nói lại nếu cảnh này xa Cảnh 3 về thời lượng.
- 🔴 **CẤM ngoài kịch bản (thêm 01/09):** **không bấm link "Tra cứu chính sách"** trên nav bar CSKH,
  dù nó luôn hiển thị sẵn cạnh "Hàng chờ" / "Báo cáo vận hành". Trang này có **hai lỗi thật chưa
  vá**: ① giao diện có khe hở để kết quả cũ hiện thoáng qua khi tìm lượt mới (đã vá phần `catch`,
  chưa phủ hết); ② **tìm kiếm vector không có ngưỡng tương đồng** — câu vô nghĩa vẫn trả
  `status=found` kèm một chính sách CÓ THẬT nhưng không liên quan (đo thật trên `qa-stripe` 01/09).
  Chỉ đi đúng đường Cảnh 7 đã định: `/dashboard` → `/tickets/[id]`.
  *(Không phải lỗi của kịch bản — kịch bản chưa bao giờ chỉ đạo mở trang này, QA/QC đã grep xác nhận
  0 kết quả. Đây là rào phòng ngừa cho trường hợp người cầm máy tò mò bấm thử.)*
- ~~⚠️ Rủi ro dashboard "NaN"~~ **GỠ 31/08 — PO root-cause xong: lỗi nằm ở bài test**
  (`frontend/e2e/dashboard.spec.ts:24`, regex đọc nhãn không khớp định dạng mới "N/100 vé mới nhất"),
  **sản phẩm render đúng** (`dashboard/page.tsx:165` dùng số thật). Không cần né chip/số nào ở cảnh
  này, không cần dọn ticket xuống dưới 100.

## Cảnh 8 — Trình sếp duyệt

🔴 **SỬA 01/09 — nút sau khi nhập OTP tên là "Xác nhận", KHÔNG phải "Xác nhận duyệt".**
Review grep `frontend/src/`: chuỗi "Xác nhận duyệt" **không tồn tại ở đâu cả**. Nút mở panel
đúng là **"Duyệt"**; nút bấm SAU KHI nhập OTP nằm trong `OtpInput.tsx:86` — dùng CHUNG với
Cảnh 2 — chỉ ghi **"Xác nhận"** (và "Đang xác thực..." lúc chờ). Người quay tìm chữ "duyệt"
trên nút đó sẽ không thấy, và khựng lại đúng ở route chạm tiền nhất hệ thống.

🟢 **P0 đã vá (commit 554f6ad) — ĐÃ XÁC NHẬN CHẠY TRỌN bằng ảnh thật** (`64_sau_dien_otp_duyet.png`,
`70_ket_qua_duyet_that.png`; đối chiếu DB: `status=approved`, `approved_by=USR-0205`). Không còn
placeholder.

- **Màn hình, ĐÚNG LUỒNG (sửa 31/08 — bản trước ghi sai):** `/approve` **CHỈ là hàng chờ** (danh sách
  thẻ đề xuất, KHÔNG có nút Duyệt ở đây) → bấm **"Mở chi tiết →"** trên đúng thẻ → chuyển sang
  `/tickets/[id]` — **nút Duyệt/ô nhập OTP/nút Xác nhận nằm ở TRANG NÀY**, không phải ở `/approve`.
- **Thao tác đã xác nhận:** ở `/tickets/[id]`, xem trail đầy đủ (kể cả phần CSKH đã xem ở Cảnh 7,
  cùng trang) → bấm xin OTP duyệt → nhập OTP → bấm **"Xác nhận"** → trạng thái chuyển
  "Đã duyệt", khối "Quyết định phê duyệt" đổi thành "Ticket này không có đề xuất nào đang chờ duyệt."
- **Điểm nhấn:** OTP RIÊNG cho đúng resolution này (còn hiệu lực 10 phút, chỉ dùng được cho đúng đề
  xuất này — dòng chữ này HIỆN THẲNG trên UI, có thể đọc thành lời), số tiền bị khoá tại thời điểm
  xin OTP. Đây là "route chạm tiền nhất hệ thống" — đáng dừng camera lâu nhất toàn video, ở đoạn
  TRƯỚC và SAU khi gõ OTP (không phải đúng lúc đã gõ, xem mục CẤM ngay dưới).
- 🔴 **MỘT CÂU DUY NHẤT, chép NGUYÊN VĂN từ Cảnh 2 (xem file gốc mục 🔴-2 chỗ 2 — NẶNG NHẤT toàn
  hành trình, đây là "route chạm tiền nhất hệ thống") — đọc riêng cảnh này vẫn phải đủ nghĩa, không
  được chỉ ghi "qua terminal riêng" chung chung:**

  **Nếu OTP_DEMO_MODE ĐÃ tắt: DỪNG GHI HÌNH ngay trước khi mở terminal riêng — giữ máy quay TẮT
  xuyên suốt từ lúc mở terminal, chạy lệnh tra `otp_code` theo `resolution_id` (điền từ trail đang
  xem, ở mục "Chuẩn bị"), đọc mã, quay lại cửa sổ chính, TỚI KHI gõ xong đủ 6 ô trên UI — chỉ BẬT
  LẠI máy quay SAU KHI 6 ô đã điền xong**, TRƯỚC khi bấm **"Xác nhận"**. Không tách thành hai việc
  riêng — đây là MỘT khoảng dừng liên tục.

  **Nếu OTP_DEMO_MODE CHƯA tắt lúc quay:** mã hiện thẳng trên UI ngay khi panel mở ra — cùng quy tắc
  dừng ghi hình như trên, từ trước khi panel hiện ra tới khi qua khỏi màn hình đó.

  Xác nhận trực tiếp bằng ảnh `64_sau_dien_otp_duyet.png` (983252 hiện rõ) — đây là ưu tiên xử lý
  cao nhất nếu chỉ chọn được MỘT cảnh để làm đúng trong toàn video. *(Che ô nhập bằng chấm đã bị PO
  rút lại — xem Cảnh 2.)*
- ~~Nhắc riêng: khối "Thông tin giao dịch" từng trích "Nghị định 13/2023/NĐ-CP" đã hết hiệu lực~~
  **ĐÃ SỬA 31/08 (commit `9d46a3c`, tự đọc diff xác nhận)** — dòng giờ đọc đúng "Luật 91/2025/QH15,
  NĐ 356/2025/NĐ-CP". Hết áp dụng, khối này lên hình bình thường.

## Sau khi quay — trước khi coi là "xong"

```
□ Xem lại TOÀN BỘ bản ghi thô một lượt, đối chiếu với 2 mục 🔴 (banner, OTP) — kể cả khi đã vá,
  kiểm tra KHÔNG có khung hình nào sót lại từ lượt quay thử trước khi vá.
□ Nếu có cắt cảnh — xác nhận điểm cắt không để lộ nửa giây khung hình cấm (tua chậm qua điểm cắt).
□ Đối chiếu toàn bộ 7 cảnh (1,2,3,4,5,7,8 — Cảnh 5+6 cũ đã gộp làm một, không có Cảnh 6 riêng; kể cả
  Cảnh 8, đã điền đầy đủ từ vòng sửa 31/08) với bản checklist gốc
  (`docs/security/2026-08-31-soat-quay-video-demo-duoc-cam-len-hinh.md`) trước khi ghép vào video
  cuối — đặc biệt xác nhận đoạn dừng ghi hình ở Cảnh 2 và Cảnh 8 đã làm ĐÚNG một khoảng liên tục,
  không có khung hình nào lọt vào giữa lúc mở terminal và lúc gõ xong OTP.
```
