# Kịch bản quay từng cảnh — 🟢 CHỐT BẢN CUỐI 31/08

> Vai: `security`. Bổ sung cho `docs/security/2026-08-31-soat-quay-video-demo-duoc-cam-len-hinh.md`
> (bản đó trả lời KHÔNG ĐƯỢC làm gì; tài liệu này trả lời NÊN làm gì, để người cầm máy quay MỘT LƯỢT,
> không phải vừa quay vừa nghĩ — mỗi lần quay lại là một lần nữa có nguy cơ lọt thứ không nên lọt).
>
> **Đọc file kia TRƯỚC khi quay** — mọi mục "🔴 CẤM" ở đó vẫn áp dụng nguyên vẹn ở đây, không lặp lại
> chi tiết, chỉ trỏ tới bằng số cảnh tương ứng.
>
> Luồng đã xác nhận chạy trọn (QA/QC 31/08, tự đi lại kịch bản này như người cầm máy thật — làm đúng
> chữ, không tự suy thêm): đăng nhập → OTP → xem giao dịch → mô tả khiếu nại → agent điều tra → tạo
> hồ sơ → CSKH xem → trình sếp → **sếp duyệt CŨNG đã xác nhận chạy được** (P0 vá xong, xem Cảnh 8).
>
> 🟡 **CẬP NHẬT 31/08 — 6 chỗ QA/QC vướng khi đi đúng chữ, đã sửa vào bản này:** lệnh tra OTP còn
> chung chung (mục Chuẩn bị + Cảnh 2 + Cảnh 8), rủi ro 6 ô OTP hiện số khi gõ (Cảnh 2 + Cảnh 8),
> Cảnh 4 mô tả sai đường (phải bấm nút "Báo lỗi giao dịch này" trên rail, không gõ tự do), Cảnh 6
> chưa có câu xác nhận đã kiểm, Cảnh 7 thiếu cách tìm ticket giữa hàng trăm dòng, Cảnh 8 sai luồng
> màn hình (`/approve` chỉ là hàng chờ, nút Duyệt thật nằm ở `/tickets/[id]`).

## Chuẩn bị TRƯỚC KHI bấm quay — làm một lần, không phải mỗi cảnh

```
□ Terminal RIÊNG đã mở sẵn, đặt ở màn hình/máy KHÁC màn hình đang quay, kết nối được DB ngăn
  fin05-qa-stripe — dùng để tra otp_code trong auth_sessions khi cần (xem cảnh 2 và cảnh 8).
  Lệnh THẬT, copy-paste được (xác nhận QA/QC 31/08):

  Cảnh 2 (OTP đăng nhập, theo user_id khách demo):
    docker exec fin05-qa-stripe-postgres-1 psql -U fin05 -d fin05 -tAc \
      "select otp_code from auth_sessions where user_id='<user_id khách demo>' \
       and otp_status='pending' order by created_at desc limit 1"

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
□ Danh khoản đăng nhập demo đã biết trước (không gõ sai, không phải thử lại nhiều lần).
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
- **Ngoài khung hình (nếu OTP_DEMO_MODE ĐÃ tắt):** cắt sang terminal riêng đã chuẩn bị, chạy đúng lệnh
  Cảnh 2 ở mục "Chuẩn bị" (điền `user_id` khách demo thật vào chỗ trống), đọc mã, quay lại khung hình
  chính, nhập tay. **Việc này diễn ra HOÀN TOÀN ngoài khung quay — dừng quay hoặc chuyển camera trước
  khi mở terminal, không chỉ thu nhỏ cửa sổ.**
- **Nếu OTP_DEMO_MODE CHƯA tắt lúc quay:** mã hiện thẳng trên UI (xem file gốc mục 🔴-2 chỗ 1) —
  BẮT BUỘC cắt cảnh đúng khung hình đó ở khâu dựng phim, không phát trực tiếp đoạn này.
- 🔴 **XỬ LÝ, dù đã tắt `OTP_DEMO_MODE` — PHƯƠNG ÁN PO CHỐT 31/08:** ô nhập OTP (component
  `.otp-box`) là `type="text"`, hiện RÕ chữ số khi gõ và sau khi gõ xong — KHÔNG phải chấm che (xác
  nhận bằng ảnh thật, xem file gốc mục 🔴-2 "RỦI RO CÒN LẠI SAU KHI VÁ"). **DỪNG GHI HÌNH đúng lúc
  chuẩn bị gõ 6 ô, gõ xong mới ghi tiếp** — không phải cắt ở khâu dựng phim, không phải quay riêng
  rồi ghép. Khán giả thấy panel OTP hiện ra, rồi thấy kết quả — thiếu đúng vài giây gõ số, không ai
  nhận ra thiếu. **Rẻ hơn cắt/dựng: không cần hậu kỳ, không sợ quên cắt.** *(Che ô nhập bằng chấm đã
  được PO CÂN NHẮC rồi RÚT LẠI — giá trị bảo mật thấp so với việc phá phép xác nhận độc lập QA/QC vừa
  làm; đưa vào tồn đọng, không làm gấp — xem file gốc.)*

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

## Cảnh 5 — Agent điều tra

- **Màn hình:** `/chat`, các bước agent gọi tool (hiện trạng thái "đang tra cứu"/kết quả).
- **Thao tác:** để agent tự chạy, không cần bấm gì thêm — có thể cần trả lời 1 câu hỏi làm rõ nếu
  agent hỏi lại (vd xác nhận đúng giao dịch).
- **Điểm nhấn — QUAN TRỌNG NHẤT của cả video:** đây là chỗ chứng minh "AI điều tra bằng tool thật,
  không bịa số liệu" — mọi số agent nhắc tới (số tiền, mã giao dịch, thời điểm) phải khớp đúng dữ
  liệu vừa thấy ở Cảnh 3. Nếu có thể, để camera đứng lâu hơn ở cảnh này so với các cảnh khác.
- **Ngoài khung hình:** không có.

## Cảnh 6 — Xác nhận & tạo hồ sơ

- **Màn hình:** `/chat`.
- **Thao tác:** agent tóm tắt 6 trường (loại khiếu nại, phạm vi, số tiền, mã GD, mô tả, đề xuất) TRƯỚC
  khi tạo — người quay gõ đúng nguyên văn câu ĐÃ XÁC NHẬN chạy (QA/QC 31/08): **"Có, tôi đồng ý để
  bạn tạo hồ sơ khiếu nại giúp tôi."** — agent mới thật sự tạo vé (`TCK-...`). Muốn chắc 100% khi
  quay, dùng đúng câu này, đừng tự diễn đạt lại.
- **Điểm nhấn:** hai lượt tách biệt (tóm tắt → xác nhận → tạo) — không tạo vé chỉ từ một câu mơ hồ.
  Đây chính là cơ chế ADR-051, đáng nói thành lời nếu kịch bản có thoại giải thích.
- **Ngoài khung hình:** không có.

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
- **Ngoài khung hình:** nếu `OTP_DEMO_MODE` vẫn bật, hoặc đã tắt — đều cần chạy lệnh Cảnh 8 ở mục
  "Chuẩn bị" (điền `resolution_id` thật vào chỗ trống, lấy từ trail đang xem), qua terminal riêng.
- 🔴 **XỬ LÝ, dù đã tắt `OTP_DEMO_MODE` (xem file gốc mục 🔴-2, chỗ 2 — NẶNG NHẤT toàn hành trình,
  PHƯƠNG ÁN PO CHỐT 31/08):** cùng component `.otp-box` như Cảnh 2 — 6 ô hiện rõ chữ số sau khi gõ,
  **xác nhận trực tiếp bằng ảnh `64_sau_dien_otp_duyet.png` (983252 hiện rõ)**. **DỪNG GHI HÌNH đúng
  lúc chuẩn bị gõ 6 ô, gõ xong mới ghi tiếp** (cùng cách xử lý Cảnh 2, không phải cắt/dựng phim) —
  đây là ưu tiên xử lý cao nhất nếu chỉ chọn được MỘT cảnh để làm đúng. *(Che ô nhập bằng chấm đã bị
  PO rút lại — xem Cảnh 2.)*
- ~~Nhắc riêng: khối "Thông tin giao dịch" từng trích "Nghị định 13/2023/NĐ-CP" đã hết hiệu lực~~
  **ĐÃ SỬA 31/08 (commit `9d46a3c`, tự đọc diff xác nhận)** — dòng giờ đọc đúng "Luật 91/2025/QH15,
  NĐ 356/2025/NĐ-CP". Hết áp dụng, khối này lên hình bình thường.

## Sau khi quay — trước khi coi là "xong"

```
□ Xem lại TOÀN BỘ bản ghi thô một lượt, đối chiếu với 2 mục 🔴 (banner, OTP) — kể cả khi đã vá,
  kiểm tra KHÔNG có khung hình nào sót lại từ lượt quay thử trước khi vá.
□ Nếu có cắt cảnh — xác nhận điểm cắt không để lộ nửa giây khung hình cấm (tua chậm qua điểm cắt).
□ Đối chiếu Cảnh 8 (khi đã điền) với bản checklist gốc trước khi ghép vào video cuối.
```
