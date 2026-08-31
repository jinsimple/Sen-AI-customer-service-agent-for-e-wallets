# Soát trước khi quay video demo — ĐƯỢC LÊN HÌNH / CẤM LÊN HÌNH

> Vai: `security`. Giao trực tiếp từ PO qua Lead, 31/08/2026. **CHỈ VIẾT TÀI LIỆU** — không tự tắt
> cờ, không sửa cấu hình ngăn nào (vùng `devops`, chờ PO thật quyết). Ngăn xét: `fin05-qa-stripe`.
>
> **Vì sao chặt hơn demo trực tiếp:** video bị lộ thì KHÔNG đóng lại được — ghi lại, gửi đi, xem lại,
> tua chậm, chụp màn hình. Một khung hình 2 giây tồn tại vĩnh viễn.
>
> Đi theo đúng thứ tự người quay sẽ bấm: **đăng nhập (khách) → chat/khiếu nại → CSKH điều tra →
> tạo hồ sơ → supervisor duyệt.** Mỗi mục: THẤY GÌ · LÊN HÌNH ĐƯỢC KHÔNG · XỬ THẾ NÀO.
>
> **Nguồn:** phần lớn dòng dưới đây [ĐO 31/08, đọc thẳng mã nguồn + config chạy thật] — không suy
> đoán "chắc là vậy". Chỗ nào tôi chưa tự mắt thấy trên trình duyệt (không có công cụ chụp màn hình)
> được đánh dấu ⚠️ CẦN QA/QC XÁC NHẬN BẰNG ẢNH THẬT trước khi coi là đã kiểm đủ.
>
> 🟡 **CẬP NHẬT — TÀI LIỆU CHƯA CHỐT BẢN CUỐI.** PO quyết SỬA THẲNG (không chỉ né bằng cắt cảnh):
> Coder đang tắt banner môi trường + `OTP_DEMO_MODE` trên `fin05-qa-stripe`. QA/QC sẽ chạy lại đường
> quay + chụp ảnh xác nhận sau khi Coder xong. Hai mục 🔴-1/🔴-2 dưới đây sẽ chuyển từ "CẤM lên hình,
> phải xử lý" sang "đã xử lý, chờ xác nhận ảnh trước khi quay thật" — **giữ nguyên nội dung điều tra
> nguồn** (vẫn đúng, dùng làm bằng chứng TRƯỚC khi vá), thêm dòng trạng thái mới khi có ảnh.

## 🔴 Hai điều CẤM TUYỆT ĐỐI, xuất hiện ở NHIỀU màn hình, không phải một chỗ

### 1. Nhãn môi trường (`EnvBadge`) — xuất hiện Ở MỌI TRANG, không chỉ dashboard

**[ĐO]** `frontend/src/components/EnvBadge.tsx` — nhãn này render ở **topbar VÀ màn hình đăng nhập**
(đọc code, dòng 6: *"Nhãn này... hiện ở topbar VÀ ở màn hình đăng nhập"*), tức xuất hiện xuyên suốt
mọi bước của hành trình quay, không phải một khung hình lẻ.

- **THẤY GÌ:** chấm màu + chữ `DEVELOPMENT · postgresql/fin05` (hoặc tương tự tuỳ `env`/`db_kind`/
  `db_name` trả về từ `/api/env-info`).
- **CẤM LÊN HÌNH.**
- 🔴 **Nặng hơn cái thấy bằng mắt:** nhãn có `title` (tooltip khi hover) hiện thêm **`backend` URL
  nội bộ** (vd `http://backend:8010`) **VÀ `build_commit`/`build_at`** (băm commit + thời điểm build
  đang chạy) — đọc thẳng `frontend/src/app/api/env-info/route.ts`. Route này **KHÔNG cần đăng nhập**
  (public, tự khai trong code). Nếu người quay vô tình rê chuột qua badge, tooltip bung ra giữa
  video — lộ kiến trúc nội bộ + mã nguồn đang chạy, không chỉ lộ "đây là môi trường dev".
- **XỬ THẾ NÀO:**
  1. Cách bền nhất (việc code, `devops`, KHÔNG phải tôi tự làm): set biến môi trường sao cho
     `env === "production"` trên ngăn dùng để quay — nhãn tự ẩn theo đúng thiết kế sẵn có (dòng 20
     component: "Nhãn TỰ ẨN khi `env === "production"`"). Đây là cách ĐÚNG Ý ĐỒ thiết kế của chính
     component, không phải patch tạm.
  2. Nếu không kịp đổi cấu hình trước buổi quay: **dựng riêng ngăn xếp SẠCH cho quay hình** (không
     dùng `fin05-qa-stripe` — ngăn đó đang phục vụ mục đích khác, đo axe-core Stripe, đổi cờ có thể
     ảnh hưởng việc khác đang chạy), set `env=production`-tương-đương chỉ cho ngăn quay.
  3. Nếu bắt buộc dùng ngăn hiện có, không kịp đổi gì: **crop/che vùng topbar bằng hậu kỳ**, và
     **tuyệt đối không để chuột đi qua vùng badge** trong lúc quay (tránh bật tooltip).

### 2. Mã OTP hiện thẳng trên màn hình — HAI chỗ khác nhau, cả hai đều nằm trên đường quay dự kiến

**[ĐO]** `OTP_DEMO_MODE=true` được set riêng cho `fin05-qa-stripe`
(`docker-compose.qa-stripe.override.yml`, có chủ đích — giữ ~8 file test QA-QC đọc thẳng `otp_code`
từ response tiếp tục chạy được trên ngăn này). Cờ này khiến backend trả `otp_code` thẳng trong JSON
(đây chính là Phát hiện #2, benchmark EU/US 27/08 — đã vá mặc định production ở `bdaf17e`, nhưng ngăn
demo cố ý bật lại để test cũ chạy được).

- **Chỗ 1 — màn hình chat của khách, bước xác thực OTP phiên:**
  `frontend/src/app/(app)/chat/ChatClient.tsx:815` — render thẳng:
  *"Mã OTP phiên làm việc (mô phỏng — gửi tới {phone}): **{mã 6 số}**"*, chữ đậm, trong bong bóng
  chat của bot. **Nằm ĐÚNG bước đầu hành trình quay (đăng nhập/xác thực khách).**
  🟢 **[XÁC NHẬN BẰNG ẢNH THẬT, QA/QC 31/08, `10_khach_rail.png`]:** đúng như đọc mã — dòng
  *"Mã OTP phiên làm việc (mô phỏng — gửi tới 0974000145): 440452"* hiện trực tiếp dạng văn bản
  trong bong bóng chat, KHÔNG phải giấu trong DevTools/Network — chắc chắn lọt khung hình nếu quay
  đúng luồng đăng nhập. Badge môi trường cũng xác nhận có thật, góc trên-phải, "nổi bật, dễ vào
  khung hình" (nguyên văn QA/QC).
- **Chỗ 2 — màn hình supervisor duyệt hoàn tiền, bước xin OTP duyệt:**
  `frontend/src/components/ResolutionApprovalActions.tsx:90` — render thẳng:
  *"Mã OTP xác nhận duyệt: **{mã 6 số}**"*, chữ đậm. **Nằm ĐÚNG bước cuối hành trình quay
  (supervisor duyệt) — đây là route CHẠM TIỀN NHẤT hệ thống, lộ OTP ở đây nặng hơn lộ ở chỗ 1.**
- **CẤM LÊN HÌNH cả hai.**
- **XỬ THẾ NÀO:**
  1. Cách bền: tắt `OTP_DEMO_MODE` trên ngăn dùng để quay (kéo theo phải có đường nhập OTP tay —
     người quay cần biết trước mã OTP thật từ đâu ra, vd xem log backend ngoài khung hình, hoặc quay
     riêng một ngăn có kênh gửi SMS giả lập không hiện trên UI). **Việc `devops`, chờ PO quyết.**
  2. Nếu không kịp: **cắt cảnh đúng khung hình hiện mã** (biết trước code hiện mã ở đâu — hai vị trí
     trên — nên cắt được chính xác, không phải đoán).
  3. Có thể diễn lại y hệt bằng ngăn khác đã tắt `OTP_DEMO_MODE` (any ngăn KHÔNG override cờ này —
     hành vi mặc định từ `bdaf17e` là không trả OTP) nếu chỉ cần đúng 2 cảnh đó, quay ngoài
     `qa-stripe`.

🟢 **CẬP NHẬT — Coder đang tắt `OTP_DEMO_MODE` trên `qa-stripe` theo phương án 1. Hệ quả bắt buộc,
đây là THAO TÁC TAY của người cầm máy, không phải tự động:**

**[ĐO, xác minh trước khi ghi]** `src/api/main.py:441-446` tự khai rõ: `OTP_DEMO_MODE=false` là
**"gate chặn RÒ RỈ, không phải triển khai kênh gửi thật"** — tắt cờ này **không** tự nhiên có kênh
SMS thật thay thế. Khi tắt, response KHÔNG còn `otp_code` — người quay **phải có cách khác lấy mã**
để nhập tay lên UI, nếu không sẽ đứng hình giữa buổi quay.

**Cách lấy mã, đúng thứ tự:**
1. Mở **một cửa sổ terminal RIÊNG, tuyệt đối KHÔNG lọt khung hình quay** (khác màn hình/khác máy ảo
   càng tốt — không chỉ "thu nhỏ", vì thu nhỏ vẫn có thể vô tình Alt-Tab qua giữa lúc quay).
2. Truy vấn cột `otp_code` của bảng `auth_sessions` (`src/db/models.py:486` — cột `String`, không
   mã hoá, xem đánh giá riêng ở mục "Ghi nhận thêm" bên dưới) đúng `session_id` vừa xin.
3. Nhập tay mã đó vào UI (đang ở màn hình quay, KHÔNG đọc mã ra khung hình terminal).

⚠️ Đây là bước **BẮT BUỘC**, không phải tuỳ chọn — thiếu nó thì luồng quay xác thực OTP không đi
tiếp được. Ghi nguyên vào tóm tắt cuối tài liệu.

## Đi theo từng bước hành trình quay

### Bước 1 — Đăng nhập (khách)

| | |
|---|---|
| Thấy gì | Form đăng nhập (SĐT + mật khẩu), badge môi trường (mục 🔴-1) |
| Lên hình được không | Form: ĐƯỢC. Badge: KHÔNG — xem xử lý ở trên |
| ⚠️ Cần QA/QC xác nhận | Thanh địa chỉ lúc này hiện gì — cổng `59080`/`59443` remap riêng cho
  `qa-stripe` (khác cổng chuẩn 80/443) có lộ trên URL không, có nên crop thanh địa chỉ trình duyệt
  suốt buổi quay không (an toàn nhất: LUÔN crop thanh địa chỉ, không phụ thuộc ngăn nào) |

### Bước 2 — Chat/mô tả khiếu nại (khách)

| | |
|---|---|
| Thấy gì | Khung chat, có thể có bước xin OTP phiên (mục 🔴-2 chỗ 1) |
| Lên hình được không | Nội dung chat: ĐƯỢC (dữ liệu seed, không phải khách thật — nhưng xem cảnh
  báo "giống thật" bên dưới). Bước OTP: KHÔNG |
| 🟢 **[XÁC NHẬN BẰNG ẢNH THẬT, QA/QC 31/08]** | "Rail giao dịch" (giao dịch gần đây): chỉ hiện số
  tiền/ngày/mã TXN, **KHÔNG hiện tên/SĐT người liên quan — sạch**, đúng thiết kế che bên thứ ba. |
| 🟢 **Phát hiện TỐT, đã có sẵn, không cần thêm việc** | Trang `/chat` **đã có** dòng chú thích ở
  chân trang: *"Bản demo dùng dữ liệu mô phỏng — vui lòng không nhập thông tin cá nhân thật. Nội
  dung chat được xử lý bởi AI của nhà cung cấp nước ngoài."* — đúng loại cảnh báo tôi định đề xuất
  thêm ở Bước 3, hoá ra ĐÃ CÓ trên trang chat. ⚠️ Chưa xác nhận dòng này có xuất hiện ở các trang
  KHÁC (dashboard, ticket-detail) hay chỉ riêng `/chat` — nếu chỉ một trang, video đi qua nhiều màn
  hình thì người xem không phải lúc nào cũng thấy được cảnh báo này. |

### Bước 3 — CSKH điều tra

| | |
|---|---|
| Thấy gì | Lịch sử giao dịch của khách, có thể có timeline điều tra |
| Lên hình được không | Dữ liệu CHÍNH CHỦ khách (tên/SĐT/số TK của khách đang được điều tra): kỹ
  thuật ĐƯỢC (không phải PII thật — toàn bộ 208 user là dữ liệu sinh tổng hợp, `data/generated/`) |
| 🔴 Cảnh báo riêng, không phải bug — vấn đề NHẬN THỨC | **[ĐO]** Tên seed là tên người Việt thật-nghe
  (vd "Phan Đức Long", "Trần Hữu Trang"), SĐT đúng định dạng nhà mạng VN thật (đầu số 0387/0761/0812…
  đều là đầu số THẬT đang cấp cho thuê bao thật ở Việt Nam, chỉ 7 số cuối là random). Số tài khoản
  ngân hàng (`bank_accounts.jsonl`) dùng mã ngân hàng thật (ACB/MB…) nhưng số tài khoản có dạng
  tuần tự lộ liễu nếu nhìn ≥2 dòng (`8800000000000X`) — nhìn MỘT dòng trên video thì KHÔNG lộ liễu.
  ⟹ **Trước hội đồng ví điện tử, một khung hình dừng lại đúng lúc hiện "Trần Hữu Trang · 0761000002"
  trông giống hệt dữ liệu khách thật** — đúng đúng lo ngại PO nêu. Không phải lỗi kỹ thuật, là rủi ro
  NGỘ NHẬN. **Xử lý đề xuất:** mở đầu video (hoặc caption cố định suốt video) ghi rõ "Toàn bộ dữ liệu
  trong demo là dữ liệu SINH TỔNG HỢP, không phải khách hàng thật" — rẻ, không cần đổi gì trong sản
  phẩm. Dòng chú thích tương tự **đã có sẵn ở `/chat`** (xem Bước 2) — cân nhắc lặp lại/làm nổi bật
  hơn ở đầu video thay vì chỉ dựa vào dòng chữ nhỏ chân trang một màn hình. |
| 🟢 **[XÁC NHẬN BẰNG ẢNH THẬT, QA/QC 31/08, `05_dashboard_cskh_full.png`]** | Trang `/dashboard`
  (vai CSKH): **không thấy chữ "NaN"** ở các tab đếm (Tất cả/Chờ tiếp nhận/...) trong lượt diễn tập
  này — 🔴 **không suy ra là đã hết**, lỗi đã tái lập 3 lần ở điều kiện sạch trước đó, "không thấy
  một lượt" ≠ "đã sửa" (xem mục riêng bên dưới). Cột "KHÁCH HÀNG" hiện **đầy đủ họ tên thật-trông-như-
  thật** (vd "Ngô Ngọc Huy", "Mai Thanh Tuấn", hàng chục dòng) — QA/QC tự nhận xét đúng ý: "nhìn
  giống danh sách khách hàng thật nếu ai xem video không biết đó là demo" — xác nhận trực tiếp mối
  lo NGỘ NHẬN ở trên, không chỉ ở màn hình điều tra một khách mà cả DANH SÁCH TỔNG trên dashboard. |

### Bước 4 — Tạo hồ sơ khiếu nại

| | |
|---|---|
| Thấy gì | Xác nhận 6 trường (ADR-051, HAI THÌ) rồi tạo ticket, mã `TCK-...` |
| Lên hình được không | ĐƯỢC — không có gì nhạy cảm riêng ở bước này ngoài dữ liệu đã xét ở Bước 3 |

### Bước 5 — Supervisor duyệt

| | |
|---|---|
| Thấy gì | Trail điều tra, nút xin OTP duyệt, ô nhập OTP, nút Duyệt/Từ chối |
| Lên hình được không | Luồng thao tác: ĐƯỢC. **Mã OTP hiện trên màn hình: CẤM** (mục 🔴-2 chỗ 2 —
  route chạm tiền nhất hệ thống, ưu tiên xử lý cao nhất nếu chỉ chọn được MỘT cảnh để cắt) |

## Hai điều PO đã biết trước, xác nhận lại + bổ sung phạm vi

- **Dashboard NaN:** **[ĐO]** `docs/STATE.md:291` — lỗi `"Expected 100, Received NaN"` đã **tái lập
  3 lần Ở ĐIỀU KIỆN SẠCH** (không phải nhiễu ngẫu nhiên, chưa root-cause). QA/QC "không thấy" trong
  một lượt diễn tập **không đồng nghĩa đã hết** — đúng như Lead cảnh báo. **Xử lý nếu hiện ra giữa
  lúc quay:** KHÔNG quay tiếp qua nó — dừng, tránh màn hình tổng quan (dashboard) trong lần quay này
  cho tới khi có ai xác nhận đã root-cause, hoặc chấp nhận cắt cảnh nếu lỡ dính.
- **Banner + OTP demo:** xác nhận đầy đủ ở mục 🔴 trên, kèm vị trí mã nguồn chính xác.

## Ghi nhận thêm — không gấp trước buổi quay, nhưng cần đứng trong hồ sơ bảo mật

### `otp_code` lưu dạng chuỗi thường trong `auth_sessions` — đánh giá của tôi, không phải kết luận sẵn

PO nêu quan sát, yêu cầu tôi tự đánh giá thay vì tự kết luận hộ. **[ĐO]** xác nhận: `AuthSession.otp_code`
(`src/db/models.py:486`) là cột `String` thường, không qua hàm băm nào trước khi lưu; `verify_otp` so
sánh trực tiếp `secrets.compare_digest(req.otp_code, auth_session.otp_code)` (constant-time, nhưng
constant-time compare KHÔNG đồng nghĩa với "đã băm" — hai việc khác nhau, chống hai loại tấn công
khác nhau: compare-thời-gian chống dò từng ký tự qua độ trễ phản hồi, băm chống lộ khi đọc được DB).

**Đánh giá — KHÔNG ổn, nhưng mức độ THẤP, không phải khẩn cấp:**
- Lý do KHÔNG coi là khẩn: OTP 6 số có không gian nhỏ (10⁶), khác hẳn mật khẩu — băm bằng thuật toán
  chậm kiểu Argon2 (như đang dùng cho mật khẩu) gần như vô nghĩa cho không gian nhỏ này nếu kẻ tấn
  công đã đọc được DB (dò ngược 10⁶ khả năng rất rẻ dù có băm). Đây là lý do hợp lý để KHÔNG áp cùng
  chuẩn với mật khẩu, không phải lý do để bỏ qua hoàn toàn.
- Lý do VẪN đáng sửa: OTP có **thời hạn ngắn (session TTL)**, nhưng trong ĐÚNG cửa sổ còn hiệu lực,
  một lượt đọc DB (backup lộ, dump sự cố, SQL injection giả định, hoặc — đúng bối cảnh tài liệu này —
  một người có quyền truy vấn DB trực tiếp như bước "lấy mã để quay video" ở trên) cho ngay mã DÙNG
  ĐƯỢC, không cần thêm bước nào. Băm bằng SHA-256 (rẻ, không cần salt phức tạp do TTL ngắn + đã có
  `failed_attempts`/khoá chống dò) loại bỏ hẳn rủi ro này với chi phí gần như bằng không — so sánh
  vẫn O(1): `sha256(input) == stored_hash`.
- Đây là loại phát hiện một kiểm toán viên chuẩn ngành (SOC2/ISO 27001, mục logging & credential
  storage) sẽ nêu theo phản xạ — "OTP/mã xác thực không nên nằm dạng đọc được trong CSDL", bất kể TTL
  ngắn hay không, vì nguyên tắc là KHÔNG BAO GIỜ giả định lớp phòng thủ khác (TTL) đủ một mình.

**Đề xuất:** thêm vào backlog `security`/`tech-lead` — băm `otp_code` trước khi lưu (SHA-256 đủ,
không cần Argon2), sửa `verify_otp`/route xin OTP duyệt để so khớp theo băm. Việc RẺ, KHÔNG đổi hành
vi quan sát được từ bên ngoài, không chặn buổi quay video (chính bước "lấy mã để quay" ở trên còn
cần đọc DB trực tiếp — sửa xong vẫn đọc DB được, chỉ đọc ra bản băm thay vì bản rõ, quy trình lấy mã
để quay phải đổi cách khác nếu vá xong TRƯỚC buổi quay — nêu ra để không ai ngạc nhiên nếu thứ tự vá
đổi chỗ lấy mã sau này).

## Việc CHƯA soát được — khai rõ, không giấu

- **DevTools/console lỗi nếu người quay lỡ mở** — tôi không có công cụ mở trình duyệt thật để kiểm
  console log có in ra thứ nhạy cảm nào không (token, stack trace, URL nội bộ khác ngoài badge đã
  biết). Đề xuất: **quy tắc vận hành đơn giản, không cần điều tra thêm** — không mở DevTools trong
  suốt buổi quay, không phải vì đã kiểm sạch mà vì đây là cách rẻ nhất loại trừ rủi ro chưa biết.
- **Bất cứ chỗ nào lộ đây là môi trường dựng cho thử Stripe** — chưa tìm thấy gì ngoài badge môi
  trường (đã xử ở mục 🔴-1); nếu có màn hình thanh toán/Stripe riêng trong hành trình quay (không có
  trong mô tả 5 bước ở đầu tài liệu), cần bổ sung soát riêng, báo tôi nếu hành trình có bước đó.
- Toàn bộ mục đánh dấu **⚠️ CẦN QA/QC XÁC NHẬN BẰNG ẢNH THẬT** ở trên — tôi suy luận đúng từ mã
  nguồn/dữ liệu, nhưng chưa tự mắt thấy trình duyệt thật hiện đúng như vậy. Đã nhắn p-226-10 xin ảnh,
  chưa nhận được lúc viết tài liệu này.

## Tóm tắt cho người cầm máy — đọc một lần, không cần hỏi ai

```
1. Crop/tránh vùng topbar (badge môi trường) suốt video, KHÔNG rê chuột qua nó — TRỪ KHI Coder xác
   nhận đã tắt banner trên qa-stripe VÀ có ảnh QA/QC xác nhận biến mất thật (đang chờ, xem đầu file).
2. 🔴 MỚI, BẮT BUỘC: nếu OTP_DEMO_MODE đã tắt — chuẩn bị SẴN một cửa sổ terminal RIÊNG (không lọt
   khung hình) để truy vấn cột otp_code trong bảng auth_sessions, nhập tay mã vào UI ở CẢ HAI bước
   (khách xác thực phiên + supervisor xin OTP duyệt). Thiếu chuẩn bị này = đứng hình giữa buổi quay.
   Nếu banner/OTP_DEMO_MODE CHƯA kịp tắt lúc quay: quay lại đúng mục 1 cũ (crop + cắt cảnh) thay thế.
3. KHÔNG mở DevTools trong lúc quay.
4. Nếu dashboard hiện NaN/lỗi lạ giữa chừng — dừng, không quay tiếp qua đó, báo lại.
5. Đầu video hoặc caption cố định: "Dữ liệu trong demo là dữ liệu sinh tổng hợp, không phải khách
   hàng thật." (đã có sẵn dạng chữ nhỏ ở chân trang /chat — cân nhắc làm nổi bật hơn, không chỉ dựa
   vào dòng đó).
6. Nếu có bước liên quan Stripe/thanh toán ngoài 5 bước đã soát — dừng, báo security trước khi quay.
```
