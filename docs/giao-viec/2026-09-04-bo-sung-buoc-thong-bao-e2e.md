# Bổ sung: bước kiểm THÔNG BÁO vào luồng E2E 1-vé liền mạch

> Nguồn: PO · 04/09 · Nền: chèn vào kịch bản gốc
> `2026-09-04-kich-ban-e2e-cong-cuoi-truoc-review.md` (17 bước, 1 vé xuyên suốt).
> Soạn từ Ý ĐỊNH của ADR-063 (không từ code) để test kiểm cái tính năng PHẢI làm,
> không phản chiếu cái code tình cờ làm.
> Chạy XEN vào cùng 1 vé, KHÔNG tách lượt riêng. 3 lần, UI thật, ảnh thật mỗi bước.

## Điều kiện đầu (cần Lead/Coder xác nhận trước khi QA chạy)
- **2 tài khoản CSKH**: `CSKH-A` (điều tra + đề xuất vé) và `CSKH-B` (chỉ online để nhận
  fan-out "vé mới"). Nếu CHỈ có 1 CSKH → vẫn chạy được nhưng KHÔNG kiểm được fan-out
  nhiều người nhận trên UI; ghi rõ giới hạn đó, đừng làm tròn.
- 1 tài khoản `supervisor`. Cả CSKH-A/B và Sếp đăng nhập sẵn (đang online) trước khi khách tạo vé.

## Các bước THÔNG BÁO chèn vào (mã N, gắn vào mốc B của kịch bản gốc)

**N1 — sau khi khách tạo vé (≈B4).** Trên màn CSKH-A và CSKH-B (đang online):
- Chuông báo badge **+1**; mở ra có thông báo "Vé mới #TCK-…".
- ✅ Kiểm NỘI DUNG: chỉ mã vé + nhãn loại. **KHÔNG số tiền, KHÔNG PII, KHÔNG SĐT** (Ràng buộc #3 + PDPA).
- ✅ Cả A và B đều nhận (fan-out tới mọi CSKH). Nếu chỉ 1 tài khoản: ghi rõ không kiểm được vế này.

**N2 — CSKH-A mở thông báo.** Bấm item → nhảy đúng màn vé #TCK-… → badge của **A giảm 1**.
- ✅ Badge của **B vẫn còn** (đã-đọc là RIÊNG từng người, không lẫn).

**N3 — sau khi CSKH-A đề xuất hướng xử lý (`propose_resolution`, ≈B9).** Trên màn Sếp:
- Chuông Sếp badge **+1**; thông báo "Vé #TCK-… chờ duyệt".
- ✅ CSKH-B **KHÔNG** nhận thông báo "chờ duyệt" này (chỉ Sếp).

**N4 — Sếp mở bảng "CSKH đang online".**
- ✅ Thấy CSKH-A và CSKH-B là **online**; đóng tab CSKH-B ~45s → B chuyển **offline** (presence TTL).
- ✅ Cột "số vé đang xử lý" của CSKH-A phản ánh đúng (phiên live-chat đang nhận + đề xuất chờ duyệt).

**N5 — sau khi Sếp duyệt (≈B11).** Trên màn CSKH-A (người đã đề xuất):
- Chuông A badge **+1**; thông báo "Sếp đã duyệt #TCK-…".
- ✅ **Báo ngược đúng người**: CSKH-B **KHÔNG** nhận thông báo duyệt này (chỉ người đề xuất).

**N6 — kiểm cô lập (BOLA, ở mức UI).**
- ✅ Không có đường nào trên UI để CSKH-B thấy/mở thông báo riêng của A.
- (Ca BOLA tự động đầy đủ — mark-read noti người khác trả 404 — thuộc tester, chờ phiên tester;
  bước N6 này chỉ là kiểm mắt trên UI, không thay test tự động.)

## Tiêu chí ĐẠT của phần thông báo
1. Đúng vai nhận đúng thông báo đúng thời điểm (N1 mọi CSKH · N3 chỉ Sếp · N5 chỉ người đề xuất).
2. Nội dung thông báo KHÔNG rò tiền/PII.
3. Badge tăng/giảm đúng, đã-đọc riêng từng người.
4. Bảng presence đúng online/offline + cột số vé.
5. Toàn bộ nằm trong CÙNG 1 vé của luồng gốc, liền mạch.

## Ghi chú vận hành
- Vẫn giữ ràng buộc quay: người đóng CSKH nhận handoff trong 60-90s (hàng chờ hết hạn ~193s).
- Ảnh thật mỗi bước N; Lead tự soi ≥5 ảnh (gồm ít nhất 1 ảnh nội-dung-thông-báo để xác minh không rò PII) trước khi báo PO.
- Chạy 3 lần → tổng hợp → PO review để quay.

## 🎬 CHOREOGRAPHY QUAY — 2 lưu ý bắt buộc, không phải bug (04/09, từ lượt full seamless)

Đo trực tiếp trong lúc verify — người đóng vai/dàn cảnh PHẢI biết trước, nếu không sẽ tưởng sản phẩm
lỗi giữa take:

1. **Presence (bảng "CSKH đang online" của Sếp):** cần **>20 giây** sau khi CSKH đăng nhập mới cập
   nhật đúng — cơ chế heartbeat định kỳ (~20s/lượt), KHÔNG cập nhật tức thời lúc kết nối. Đo được:
   vẫn "Offline" tới giây 15, chuyển đúng "Đang online" ở giây 20. Nếu quay cảnh Sếp mở bảng presence
   ngay sau khi CSKH vừa đăng nhập — ĐỢI ít nhất 20 giây trước khi bấm quay/chụp, không cắt cảnh sớm.
2. **Hàng chờ live-chat:** người đóng vai CSKH phải bấm "Mở & nhận" trong khung **60-90 giây** sau khi
   khách bấm "nói chuyện trực tiếp" — hàng chờ tự hết hạn ở mốc ~193 giây (đo cận trên). CSKH trực sẵn,
   phản ứng nhanh khi khách bấm nút.
