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
□ Danh khoản đăng nhập demo đã biết trước, ĐỦ CẢ BA vai (không gõ sai, không phải thử lại nhiều lần):
  - Khách (Cảnh 1-6): SĐT + mật khẩu.
  - CSKH (Cảnh 7): tài khoản đăng nhập qua `/dang-nhap-noi-bo`.
  - Sếp/supervisor (Cảnh 8): tài khoản đăng nhập qua `/dang-nhap-noi-bo`, vai khác CSKH.
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

## Cảnh 1 — Đăng nhập (khách)

- **Màn hình:** `/login`
- **Thao tác:** nhập SĐT + mật khẩu tài khoản khách demo, bấm đăng nhập.
- **Điểm nhấn muốn người xem thấy:** xác thực bằng mật khẩu thật (Argon2), không phải chọn vai trò
  tuỳ ý — hệ thống tự biết ai đang đăng nhập.
- **Ngoài khung hình:** không có thao tác tay nào cần chuẩn bị ở cảnh này.
- **Nhắc CẤM (xem file gốc mục 🔴-1):** badge môi trường ở topbar — nếu CHƯA vá, tránh khung hình
  góc trên-phải; nếu ĐÃ vá, không cần né nhưng vẫn không rê chuột qua vùng đó (thói quen an toàn).

## Cảnh 2 — Xác thực OTP phiên

- **Màn hình:** `/chat`, ngay sau đăng nhập, bong bóng chat đầu tiên xin OTP.
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

- **Màn hình:** `/chat`, rail "Giao dịch gần đây" hiện sau khi xác thực.
- **Thao tác:** lướt qua danh sách, dừng ở giao dịch sẽ dùng làm ví dụ khiếu nại.
- **Điểm nhấn:** rail chỉ hiện số tiền/ngày/mã giao dịch — **đã xác nhận bằng ảnh thật (QA/QC
  31/08)** không hiện tên/SĐT người liên quan, an toàn để lên hình nguyên trạng.
- **Nhắc:** đây là dữ liệu sinh tổng hợp trông giống thật (tên/SĐT seed đúng định dạng VN thật) —
  đúng lý do cần caption/lời mở đầu đã chuẩn bị.

## Cảnh 4 — Mô tả khiếu nại (chat)

🔴 **SỬA 31/08 — đường "gõ tự do" CHƯA được xác nhận tối nay, đừng quay đường đó chưa kiểm.**

- **Màn hình:** `/chat`, vẫn ở rail "Giao dịch gần đây" từ Cảnh 3.
- **Thao tác (đường ĐÃ xác nhận chạy, dùng đường này để quay):** bấm nút **"Báo lỗi giao dịch này"**
  ngay trên dòng giao dịch đã chọn ở Cảnh 3 → hệ thống hiện các **chip loại khiếu nại** → bấm đúng
  chip khớp tình huống (vd "Bị trừ tiền hai lần").
- **Điểm nhấn:** thao tác bấm, không phải gõ — nhanh, ít khả năng lỗi chính tả/gõ nhầm khi quay
  nhiều lượt. Nếu kịch bản MUỐN có đoạn gõ tự do (cho tự nhiên hơn), đó là một nhánh KHÁC, cần ai
  xác nhận riêng bằng thực tế trước khi đưa vào quay — không suy đoán nó cũng chạy được.
- **Ngoài khung hình:** không có.

## Cảnh 5 — Agent tra cứu & xác nhận tạo hồ sơ

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
- 🟡 **TỒN ĐỌNG:** cảnh này có thể phải soát lại sau khi cổng "ép-tra-trước" (đang làm, chưa land) đi
  vào bản chạy thật — cần xác nhận lại hành vi gộp-một-bong-bóng này có giữ nguyên không sau khi cổng
  đổi cách agent xử lý tra cứu. Soát lại khi cổng đó land và đo xong, đừng quay bản cũ nếu hành vi
  đã đổi.

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
- ~~⚠️ Rủi ro dashboard "NaN"~~ **GỠ 31/08 — PO root-cause xong: lỗi nằm ở bài test**
  (`frontend/e2e/dashboard.spec.ts:24`, regex đọc nhãn không khớp định dạng mới "N/100 vé mới nhất"),
  **sản phẩm render đúng** (`dashboard/page.tsx:165` dùng số thật). Không cần né chip/số nào ở cảnh
  này, không cần dọn ticket xuống dưới 100.

## Cảnh 8 — Trình sếp duyệt

🟢 **P0 đã vá (commit 554f6ad) — ĐÃ XÁC NHẬN CHẠY TRỌN bằng ảnh thật** (`64_sau_dien_otp_duyet.png`,
`70_ket_qua_duyet_that.png`; đối chiếu DB: `status=approved`, `approved_by=USR-0205`). Không còn
placeholder.

- **Màn hình, ĐÚNG LUỒNG (sửa 31/08 — bản trước ghi sai):** `/approve` **CHỈ là hàng chờ** (danh sách
  thẻ đề xuất, KHÔNG có nút Duyệt ở đây) → bấm **"Mở chi tiết →"** trên đúng thẻ → chuyển sang
  `/tickets/[id]` — **nút Duyệt/ô nhập OTP/nút Xác nhận nằm ở TRANG NÀY**, không phải ở `/approve`.
- **Thao tác đã xác nhận:** ở `/tickets/[id]`, xem trail đầy đủ (kể cả phần CSKH đã xem ở Cảnh 7,
  cùng trang) → bấm xin OTP duyệt → nhập OTP → bấm "Xác nhận duyệt" → trạng thái chuyển
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
  LẠI máy quay SAU KHI 6 ô đã điền xong**, TRƯỚC khi bấm "Xác nhận duyệt". Không tách thành hai việc
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
