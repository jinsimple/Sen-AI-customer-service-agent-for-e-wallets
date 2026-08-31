# Kịch bản quay từng cảnh — phần ĐÃ CHẠY ĐƯỢC

> Vai: `security`. Bổ sung cho `docs/security/2026-08-31-soat-quay-video-demo-duoc-cam-len-hinh.md`
> (bản đó trả lời KHÔNG ĐƯỢC làm gì; tài liệu này trả lời NÊN làm gì, để người cầm máy quay MỘT LƯỢT,
> không phải vừa quay vừa nghĩ — mỗi lần quay lại là một lần nữa có nguy cơ lọt thứ không nên lọt).
>
> **Đọc file kia TRƯỚC khi quay** — mọi mục "🔴 CẤM" ở đó vẫn áp dụng nguyên vẹn ở đây, không lặp lại
> chi tiết, chỉ trỏ tới bằng số cảnh tương ứng.
>
> Luồng đã xác nhận chạy trọn (QA/QC 31/08): đăng nhập → OTP → xem giao dịch → mô tả khiếu nại →
> agent điều tra → tạo hồ sơ → CSKH xem → trình sếp. **Cảnh sếp duyệt để PLACEHOLDER**, chờ Coder vá
> xong bug OTP-duyệt (P0, đang khảo sát).

## Chuẩn bị TRƯỚC KHI bấm quay — làm một lần, không phải mỗi cảnh

```
□ Terminal RIÊNG đã mở sẵn, đặt ở màn hình/máy KHÁC màn hình đang quay, kết nối được DB ngăn
  fin05-qa-stripe — dùng để tra otp_code trong auth_sessions khi cần (xem cảnh 2 và cảnh 8).
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
- **Ngoài khung hình (nếu OTP_DEMO_MODE ĐÃ tắt):** cắt sang terminal riêng đã chuẩn bị, truy vấn
  `otp_code` mới nhất theo `user_id` khách trong bảng `auth_sessions`, đọc mã, quay lại khung hình
  chính, nhập tay. **Việc này diễn ra HOÀN TOÀN ngoài khung quay — dừng quay hoặc chuyển camera trước
  khi mở terminal, không chỉ thu nhỏ cửa sổ.**
- **Nếu OTP_DEMO_MODE CHƯA tắt lúc quay:** mã hiện thẳng trên UI (xem file gốc mục 🔴-2 chỗ 1) —
  BẮT BUỘC cắt cảnh đúng khung hình đó ở khâu dựng phim, không phát trực tiếp đoạn này.

## Cảnh 3 — Xem giao dịch gần đây

- **Màn hình:** `/chat`, rail "Giao dịch gần đây" hiện sau khi xác thực.
- **Thao tác:** lướt qua danh sách, dừng ở giao dịch sẽ dùng làm ví dụ khiếu nại.
- **Điểm nhấn:** rail chỉ hiện số tiền/ngày/mã giao dịch — **đã xác nhận bằng ảnh thật (QA/QC
  31/08)** không hiện tên/SĐT người liên quan, an toàn để lên hình nguyên trạng.
- **Nhắc:** đây là dữ liệu sinh tổng hợp trông giống thật (tên/SĐT seed đúng định dạng VN thật) —
  đúng lý do cần caption/lời mở đầu đã chuẩn bị.

## Cảnh 4 — Mô tả khiếu nại (chat)

- **Màn hình:** `/chat`.
- **Thao tác:** gõ mô tả khiếu nại tự nhiên (vd "tôi bị trừ tiền hai lần cho giao dịch X"), gửi.
- **Điểm nhấn:** ngôn ngữ tự nhiên, không cần chọn form/danh mục — agent tự phân loại.
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
  khi tạo — người quay xác nhận (gõ "đồng ý"/tương tự), agent mới thật sự tạo vé (`TCK-...`).
- **Điểm nhấn:** hai lượt tách biệt (tóm tắt → xác nhận → tạo) — không tạo vé chỉ từ một câu mơ hồ.
  Đây chính là cơ chế ADR-051, đáng nói thành lời nếu kịch bản có thoại giải thích.
- **Ngoài khung hình:** không có.

## Cảnh 7 — CSKH xem hồ sơ

- **Màn hình:** đăng xuất khách → `/dang-nhap-noi-bo` (đăng nhập nhân viên) → `/dashboard` (vai
  CSKH) → `/tickets/[id]` (chi tiết đúng ticket vừa tạo).
- **Thao tác:** đăng nhập bằng tài khoản CSKH demo, tìm đúng ticket, mở xem trail điều tra.
- **Điểm nhấn:** CSKH thấy đầy đủ căn cứ (kết quả tool đã trích dẫn) nhưng **màn hình CSKH không có
  nút duyệt** — nếu kịch bản có thoại, đây là câu đắt giá nhất theo đúng tinh thần dự án ("đó không
  phải thiếu tính năng, đó là ràng buộc cứng số 1").
- **Nhắc:** dashboard cột KHÁCH HÀNG hiện đầy đủ họ tên seed trông giống thật (đã xác nhận ảnh thật)
  — cùng lý do cần caption dữ liệu sinh tổng hợp, nói lại nếu cảnh này xa Cảnh 3 về thời lượng.
- **⚠️ Rủi ro riêng, chưa loại trừ được:** lỗi dashboard hiện "NaN" đã tái lập 3 lần ở điều kiện sạch
  trước đây, root cause chưa rõ. Nếu xuất hiện giữa cảnh này — DỪNG, không quay tiếp qua màn hình
  tổng quan, thử lại hoặc quay lướt nhanh qua khỏi vùng số liệu nghi vấn.

## Cảnh 8 — [PLACEHOLDER, CHỜ CODER VÁ XONG] Trình sếp duyệt

**CHƯA quay được** — bug P0 đang khảo sát (nút duyệt thiếu ô nhập OTP ở frontend, backend từ chối
đúng 422, không phải lỗ hổng bảo mật — xem cập nhật Lead 31/08). Điền cảnh này SAU khi có ảnh QA/QC
xác nhận luồng duyệt chạy trọn trên bản đã vá.

**Khung sẵn, điền số liệu thật sau:**
- **Màn hình:** `/approve` (vai supervisor) — cần xác nhận URL chính xác khi vá xong.
- **Thao tác dự kiến:** xem trail đầy đủ (kể cả phần CSKH đã xem ở Cảnh 7) → bấm xin OTP duyệt →
  nhập OTP → duyệt/từ chối kèm lý do có cấu trúc.
- **Điểm nhấn dự kiến:** OTP RIÊNG cho đúng resolution này (không dùng lại OTP cũ), số tiền bị khoá
  tại thời điểm xin OTP (đổi số tiền sau đó phải xin lại) — đây là "route chạm tiền nhất hệ thống",
  đáng dừng camera lâu nhất trong toàn bộ video.
- **Ngoài khung hình (nếu OTP_DEMO_MODE vẫn bật ở ngăn dùng quay):** lặp lại quy trình terminal
  riêng như Cảnh 2, lần này tra theo `resolution_id` thay vì phiên đăng nhập.
- **Nhắc CẤM (xem file gốc mục 🔴-2 chỗ 2):** đây là chỗ NẶNG NHẤT nếu lộ mã OTP — ưu tiên xử lý cao
  nhất nếu chỉ chọn được một cảnh để kiểm kỹ trước khi phát hành video.

## Sau khi quay — trước khi coi là "xong"

```
□ Xem lại TOÀN BỘ bản ghi thô một lượt, đối chiếu với 2 mục 🔴 (banner, OTP) — kể cả khi đã vá,
  kiểm tra KHÔNG có khung hình nào sót lại từ lượt quay thử trước khi vá.
□ Nếu có cắt cảnh — xác nhận điểm cắt không để lộ nửa giây khung hình cấm (tua chậm qua điểm cắt).
□ Đối chiếu Cảnh 8 (khi đã điền) với bản checklist gốc trước khi ghép vào video cuối.
```
