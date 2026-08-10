# FIN-05 — Quy tắc nghiệp vụ (business rules)

> **Trạng thái kiểm chứng — đọc trước khi dùng bất kỳ rule nào.**
> Mọi rule dưới đây do team soạn từ trí nhớ/thông lệ để **mở khoá việc build**.
> `verified: false` nghĩa là **chưa ai đối chiếu bản gốc văn bản pháp quy** —
> không được trích dẫn số điều/khoản cụ thể trong sản phẩm, slide hay khi pitch
> cho tới khi cột "Cách kiểm chứng" được thực hiện và cột trạng thái chuyển
> thành `verified: true` kèm link/bản chụp văn bản gốc.
> Đây là hiện thực hoá yêu cầu Data Brief §2.1 và nguyên tắc "không trích xuất
> từ nguồn chưa được kiểm chứng".

**Quy ước:** mỗi rule có mã `BR-xx`, dùng mã này trong code/comment thay vì
chép lại nội dung, để khi rule đổi chỉ sửa một chỗ.

---

## Nhóm 1 — SLA & thời hạn

| Mã | Rule (giá trị đang dùng) | Nguồn dự kiến | verified | Cách kiểm chứng |
|---|---|---|---|---|
| BR-01 | Tra soát giao dịch chạm ngân hàng: `sla_due_at = created_at + 4 ngày làm việc` | Thông tư 39/2014/TT-NHNN và văn bản sửa đổi (như Brief §7 đã dẫn) | **false** | Tải bản hợp nhất từ vanban.chinhphu.vn / sbv.gov.vn, đối chiếu đúng điều khoản về thời hạn tra soát |
| BR-02 | Khiếu nại nói chung: trần `30 ngày` | Cùng nguồn BR-01 | **false** | Như BR-01 |
| BR-03 | Cam kết dịch vụ nội bộ: phản hồi bước đầu `48h` | **Team tự đặt** (Data Brief §6.6) — không phải mốc pháp lý | n/a (nội bộ) | Chỉ cần PO duyệt; luôn nói rõ với khách đây là mốc dự kiến |
| BR-04 | `sla_due_at` luôn tính theo mốc **pháp lý** (BR-01/BR-02), không bao giờ theo BR-03 | Data Brief §6.6 | n/a (thiết kế) | — |
| BR-05 | Ngày làm việc = thứ 2–6, bỏ qua ngày lễ VN. **Bản demo bỏ qua ngày lễ** (chỉ tính T2–T6) | Đơn giản hoá có chủ đích | n/a (thiết kế) | Ghi rõ trong demo nếu bị hỏi |

## Nhóm 2 — Bảo vệ dữ liệu cá nhân (masking)

| Mã | Rule | Nguồn dự kiến | verified | Cách kiểm chứng |
|---|---|---|---|---|
| BR-06 | Không hiển thị đầy đủ SĐT/tên/STK của bên thứ ba; che SĐT dạng `090***1234`, tên chỉ hiện chữ cái đầu mỗi từ, STK hiện 4 số cuối | Nguyên tắc theo Nghị định 13/2023/NĐ-CP (như Brief §6.3); **định dạng che cụ thể do team đặt** | **false** (nguyên tắc) / n/a (định dạng) | Đối chiếu nghĩa vụ của bên kiểm soát dữ liệu trong bản gốc NĐ 13; định dạng che chỉ cần nhất quán |
| BR-07 | Masking thực hiện ở tầng API/tool, DB lưu bản đầy đủ (Data Brief §4.2 `bank_accounts`) | Thiết kế | n/a | Test T2 mục (d) |
| BR-08 | Không một byte PII thật nào trong repo; mọi định danh sinh từ dải test do generator kiểm soát (Data Brief §3.4) | Thiết kế | n/a | Bất biến I9 |

## Nhóm 3 — Thẩm quyền & HITL

| Mã | Rule | Nguồn | verified | Cách kiểm chứng |
|---|---|---|---|---|
| BR-09 | Thẩm quyền = f(role, scope); không có ngoại lệ theo hạn mức tiền | PRD §3, Brief §6.5 | n/a (đặc tả sản phẩm) | — |
| BR-10 | AI chỉ đề xuất; `resolutions` do agent tạo luôn ở `draft`/`pending_approval`; DB có ràng buộc `approved ⟹ approved_by NOT NULL` | Brief §6.1, Data Brief §4.2 | n/a | Test T5 + CHECK constraint trong models.py |
| BR-11 | Case chạm ngân hàng (`from_bank`/`to_bank`): CSKH chỉ tạo yêu cầu tra soát, không tự quyết | PRD §3 | n/a | Test T5 |
| BR-12 | Cấu trúc 3 tầng escalate (`supervisor`/`partner_bank`/`authority`) là **giả định thiết kế** | Brief §7, `assumption: true` | **false** | Tham vấn chuyên gia CSKH (Data Brief §2.1) |
| BR-13 | Ngưỡng N=2 lần hỏi lại trước khi tạo ticket tra thủ công | Data Brief §10 đề xuất, **chưa chốt với team** | **false** (nội bộ) | PO chốt trong buổi review tuần 2 |

> **BR-14 … BR-17 (nhóm dấu hiệu gian lận) đã được gỡ** cùng với tầng phát hiện
> dấu hiệu lừa đảo (PRD §5). Bốn mã này **không tái sử dụng cho rule mới** — giữ
> khoảng trống để mọi trích dẫn BR-xx trong code và tài liệu cũ vẫn trỏ đúng nghĩa.

## Nhóm 5 — Tiền tệ & định danh

| Mã | Rule | Nguồn | verified | Cách kiểm chứng |
|---|---|---|---|---|
| BR-18 | Tiền luôn là INTEGER đơn vị đồng; cấm float | Brief §6.2, Data Brief §5.1 | n/a | Bất biến I7 |
| BR-19 | Phí ra ngân hàng: **miễn phí 10 giao dịch đầu mỗi tháng dương lịch, tối đa 50tr/tháng**; vượt ngưỡng → `3.300đ + 0,65% × giá trị`. Ví→ví và nạp thẻ 0đ | Mô hình theo FAQ MoMo — **chốt lấy bên MoMo** ở vòng duyệt 2 khi phát hiện lệch với ZaloPay (§8.1 hồ sơ nguồn) | **false** | Check `FEE` tính lại độc lập với generator; `scenarios.yaml > fee_to_bank`, cờ `assumption: true` |
| BR-20 | Dải định danh test: SĐT 10 số `0[3|5|7|8|9]xx00xxxx` (6 số cuối 000000–009999); ví 12 số bắt đầu `9000`; STK 14 số bắt đầu `8800`; mã GD `TXNYYYYMMDD######` | Data Brief §3.4 | n/a (thiết kế) | Bất biến I9, regex trong validator |

## Nhóm 6 — Kết cục của một khiếu nại "tiền chưa về" (BR-21…BR-23)

> Nguồn: đối chiếu FAQ công khai của ví điện tử, hồ sơ ở
> `data/raw/scenario-candidates-momo-faq.md`. **Mốc thời gian là cam kết dịch vụ
> nội bộ do team đặt** (cùng hạng BR-03), KHÔNG chép mốc của ví nào — quyết định
> của PO ở vòng duyệt 1. `sla_due_at` vẫn luôn tính theo mốc pháp lý (BR-04).

| Mã | Rule | Nguồn | verified | Cách kiểm chứng |
|---|---|---|---|---|
| BR-21 | Giao dịch `processing` = ví ↔ ngân hàng chưa đối soát xong. Trong hạn đối soát nội bộ → agent **nêu mốc, KHÔNG tạo tra soát**, không đề xuất hoàn | Hình dạng quy tắc từ FAQ; mốc **do team đặt** | n/a (nội bộ) | Case `money_not_received × clear k=0` |
| BR-22 | Giao dịch `success` mà khách vẫn báo chưa nhận: trong hạn cam kết → **giải thích bằng timeline, KHÔNG tra soát**; quá hạn → **được** tạo tra soát | Như BR-21 | n/a (nội bộ) | Cặp case `trap` (trong hạn) vs `clear k=1` (quá hạn) — dữ liệu giống hệt, chỉ khác mốc |
| BR-23 | Giao dịch `failed` → tiền **chưa hề rời ví**, phí (nếu có) hoàn đủ. Agent chứng minh bằng số dư + timeline, không đề xuất hoàn | Khớp cả MoMo lẫn ZaloPay (§8.1) | n/a | Case `money_not_received × clear k=2` |

## Nhóm 7 — Giao dịch bị từ chối (BR-24…BR-29)

| Mã | Rule | Nguồn | verified | Cách kiểm chứng |
|---|---|---|---|---|
| BR-24 | Loại khiếu nại thứ 5 `transaction_rejected`: giao dịch bị từ chối, khách **không mất tiền** → không có gì để hoàn, không có gì để escalate đối tác | Quyết định sản phẩm sau đối chiếu FAQ | n/a (đặc tả) | Check `REJ` trong validator |
| BR-25 | Từ chối vì **vượt hạn mức ví** trong ngày | Hạn mức placeholder theo FAQ MoMo | **false** | `scenarios.yaml > limits`, cờ `assumption: true`; xem §8.2 hồ sơ nguồn |
| BR-26 | Từ chối vì **hạn mức riêng của ngân hàng liên kết** — lỗi phía đối tác, không phải lỗi ví | Như BR-25 | **false** | Như BR-25 |
| BR-27 | Từ chối vì **chưa xác thực / chưa liên kết ngân hàng** (`kyc_level = 0`) | Yêu cầu định danh theo NĐ 52/2024 (Brief §7) | **false** | Đối chiếu bản gốc NĐ 52/2024 |
| BR-28 | Từ chối vì **ví bên nhận đã đóng**, hoặc **không đủ số dư tối thiểu phải giữ ở ngân hàng** | FAQ công khai | n/a (thiết kế) | `wallets.status = closed`; `rejection_reason` |
| BR-29 | **Định tuyến theo lý do**: tra được `rejection_reason` → agent **giải thích ngay, không cần HITL** (không có tiền nào phải duyệt). `rejection_reason` NULL → **cấm suy đoán lý do**, đẩy người xử lý | Quyết định của PO vòng duyệt 1 | n/a (đặc tả) | Check `REJ`; case `trap` có reason NULL |

## Nhóm 9 — Người nhận chưa có ví (BR-32)

| Mã | Rule | Nguồn | verified | Cách kiểm chứng |
|---|---|---|---|---|
| BR-32 | Chuyển tới người **chưa có ví**: tiền **hoàn NGAY về ví gốc**, không giữ chờ người nhận đăng ký | **Quyết định của PO** (vòng duyệt 2) — cố ý **khác** mô hình FAQ MoMo (giữ 48h chờ người nhận đăng ký rồi mới hoàn) | n/a (thiết kế) | Chưa sinh case — xem ghi chú dưới |

> **Vì sao chưa có case trong dataset.** Vì tiền hoàn ngay về ví gốc nên khách gần
> như không có gì để khiếu nại: không mất tiền, không phải chờ. Đây cũng **không**
> phải `transaction_rejected` (giao dịch không bị từ chối, nó hoàn tất rồi tự đảo).
> PO chốt chưa đưa vào dataset ở vòng này. Nếu sau này cần, kịch bản đúng là khách
> *không để ý khoản hoàn* rồi báo mất tiền — thuộc `money_not_received`, không phải
> loại mới.

## Nhóm 8 — Giới hạn quyền của ví (BR-30…BR-31)

| Mã | Rule | Nguồn | verified | Cách kiểm chứng |
|---|---|---|---|---|
| BR-30 | Khách **chủ động yêu cầu khoá ví**: đúng chủ ví → khoá được (hành động về *tài khoản*, không phải về *tiền*, nên không cần sếp duyệt). Người khác yêu cầu → **không khoá**, đẩy người xử lý xác minh | FAQ công khai + quyết định PO | n/a (thiết kế) | Edge case `lock_on_request` ×3 |
| BR-31 | Chuyển nhầm tới ví **đang hoạt động**: ví **không tự thu hồi/huỷ/sửa** giao dịch, chỉ làm cầu nối hai bên | FAQ công khai — **xác nhận ràng buộc PRD US-004** | n/a (thiết kế) | Điều cấm `must_not_promise_recovery` trên mọi case `wrong_recipient` |

---

## Việc phải làm trước khi pitch (chặn trình bày, không chặn build)

- [ ] BR-01/BR-02: đối chiếu bản hợp nhất Thông tư 39/2014/TT-NHNN
- [ ] BR-06: đối chiếu Nghị định 13/2023/NĐ-CP bản gốc
- [ ] BR-12: tham vấn chuyên gia CSKH về số tầng thẩm quyền thật (Data Brief §2.1)
- [ ] Sau mỗi mục: cập nhật cột `verified`, đính link/bản chụp vào thư mục `docs/legal/`
