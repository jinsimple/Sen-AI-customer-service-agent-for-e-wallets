# FIN-05 — Kịch bản khiếu nại bổ sung, trích từ FAQ công khai của ví điện tử

> **TRẠNG THÁI (cập nhật 2026-08-06, sau vòng duyệt 1):**
> - **ĐÃ DUYỆT & ĐÃ HIỆN THỰC:** SC-01, SC-02, SC-03, SC-07, SC-08, SC-09, SC-10,
>   SC-11, SC-13, SC-15, SC-17, SC-18, SC-19 và loại khiếu nại thứ 5
>   `transaction_rejected` (§5 hướng 2). Chi tiết đối chiếu ở §8.
> - **ĐÃ DUYỆT VÒNG 2 & ĐÃ HIỆN THỰC:** SC-04, SC-05, SC-06 — chỗ nào lệch giữa
>   MoMo và ZaloPay thì **lấy mô hình MoMo** (quyết định PO). Xem §8.
> - **KHÔNG ĐƯA VÀO DATASET:** SC-11, SC-12 — sản phẩm hoàn tiền **ngay** về ví gốc
>   khi người nhận chưa có ví (khác mô hình 48h của MoMo), nên khách không có gì
>   để khiếu nại. Ghi thành BR-32; không cần nới bất biến I2 nữa.
>
> Phần đã duyệt nay đã thành rule trong `business_rules.md` và quota trong
> `scenarios.yaml`; file này giữ lại làm hồ sơ nguồn gốc, không có test nào đọc nó.

**Ngày crawl:** 2026-08-06 · **Nguồn:** trang Hỏi–Đáp công khai của MoMo, danh mục *Chuyển – Nhận tiền* (`/hoi-dap/chuyen-nhan-tien-ctgr5`) và các danh mục liên quan *Nạp/Rút tiền* (`ctgr3`), *Thanh toán và mua sắm* (`ctgr4`), cùng ~20 trang câu hỏi con.

---

## 0. Phương pháp & ranh giới tuân thủ

Bám đúng ranh giới đã đặt ở Data Brief §2.1–§2.2:

| Đã làm | **Không** làm |
|---|---|
| Đọc trang trợ giúp **công khai do doanh nghiệp tự viết**, trích ra *quy trình nghiệp vụ* và *từ vựng trạng thái* | Không crawl nội dung do người dùng đăng (group, bình luận, review) |
| Viết lại thành kịch bản của riêng team | Không chép nguyên văn câu trả lời của MoMo vào dataset |
| Ghi nguồn từng quy tắc để truy vết được | Không lấy một byte PII nào — trang FAQ vốn không chứa PII |

**Về các con số trong §2 — đã quyết ở vòng duyệt 2.** Đây là **biểu phí và hạn mức của MoMo**, không phải của sản phẩm này. Đề xuất ban đầu là "mượn hình dạng quy tắc, không mượn con số"; **PO chốt ngược lại: lấy thẳng số của MoMo** cho những chỗ lệch với ZaloPay, để có kịch bản cụ thể mà chạy thay vì tự nghĩ số. Điều kiện đi kèm, đã thực hiện:

- Mọi con số mượn đều mang cờ `assumption: true` trong `scenarios.yaml` và ghi rõ nguồn ở `business_rules.md` (BR-19, BR-25…BR-27), trạng thái `verified: false`.
- **Khi pitch, không được trình bày như biểu phí của sản phẩm này** — phải nói rõ là tham chiếu từ biểu phí công bố của MoMo, dùng làm placeholder cho tới khi có biểu phí riêng.

Ngoại lệ có chủ đích: quy tắc "người nhận chưa có ví" (BR-32) **cố ý khác MoMo** — xem §9.

---

## 1. Vì sao dataset hiện tại còn mỏng

147 case hiện có phủ đúng ma trận 4 loại × 3 phạm vi, nhưng **nguyên nhân nghiệp vụ** đằng sau mỗi loại thì gần như chỉ có một: `money_not_received` = giao dịch kẹt ở `processing`. FAQ cho thấy ngoài đời một câu khiếu nại "tiền chưa về" có ít nhất **năm** nguyên nhân khác nhau, và ba trong số đó **kết thúc bằng việc không hoàn tiền gì cả** — agent phải giải thích chứ không được đề xuất hoàn.

Đó chính là nhóm case mà dataset đang thiếu: **case mà câu trả lời đúng là "không có lỗi nào cả"**. Một agent chỉ gặp case có lỗi sẽ học thành cỗ máy luôn tìm ra lỗi.

---

## 2. Quy tắc nghiệp vụ trích được (đề xuất thành BR mới)

Đánh số tiếp từ BR-20. Cột **Dùng làm gì** chỉ ra kịch bản ở §3 mà rule đó khoá.

| Mã đề xuất | Quy tắc trích từ FAQ | Ghi chú áp dụng cho dự án |
|---|---|---|
| BR-21 | Giao dịch **"Đang chờ xử lý"** = dữ liệu ví ↔ ngân hàng chưa đồng bộ. Hệ thống đối soát trong **1–2 ngày làm việc**, sau đó chuyển sang *Thành công* hoặc *Thất bại* (thất bại thì hoàn tiền) | Khớp với `status = processing` sẵn có. Cho ta **mốc kỳ vọng** để agent trả lời, thay vì nói chung chung "đang xử lý" |
| BR-22 | Giao dịch **"Thành công" nhưng người nhận chậm nhận, 1–3 ngày làm việc** — do bảo trì hệ thống ngân hàng, rơi vào cuối tuần/lễ, hoặc quy trình từng ngân hàng khác nhau | **Quan trọng nhất.** Tool trả `success` mà khách vẫn khiếu nại → agent phải giải thích, **không** được tạo đề xuất hoàn tiền |
| BR-23 | Giao dịch **"Thất bại"** → tài khoản không bị trừ, tiền tự hoàn | Case khách tưởng mất tiền nhưng sổ cái chứng minh ngược lại |
| BR-24 | Chuyển cho người **chưa có ví**: người nhận được SMS, có **48 giờ** để đăng ký nhận. Quá hạn → tiền **tự động hoàn** về người gửi | Kịch bản hoàn toàn mới, cần trạng thái/quy ước riêng — xem §4 |
| BR-25 | Chuyển nhầm vào ví **không còn hoạt động**: ví **không tự huỷ/sửa giao dịch**; hướng người nhận tạo ví mới rồi ví hỗ trợ **điều chuyển số dư từ ví cũ sang ví mới** | Đây là *ngoại lệ duy nhất* ví được đụng vào tiền đã chuyển, và chỉ khi có người nhận hợp tác |
| BR-26 | Chuyển nhầm vào ví **đang hoạt động**: ví **không can thiệp được**, chỉ cung cấp kênh liên lạc để hai bên tự thoả thuận. Lý do công bố: đảm bảo an toàn/bảo mật cho khách | **Xác nhận trực tiếp ràng buộc PRD US-004** ("đầu ra không ngụ ý ví có thể tự thu hồi tiền từ người nhận"). Trước đây là suy luận của team, nay có nguồn công khai |
| BR-27 | **Hạn mức**: tài khoản đã xác thực — chuyển tối đa 30tr/ngày, **nhận** tối đa 100tr/ngày; thẻ quốc tế ghi nợ 5tr/ngày; thẻ tín dụng **không** dùng để chuyển tiền | Có cả hạn mức **NHẬN** — dataset hiện không có khái niệm này |
| BR-28 | **Chưa xác thực + chưa liên kết ngân hàng** → không chuyển tiền bằng số dư ví được | Nối thẳng với `users.kyc_level` đang có sẵn nhưng chưa case nào dùng |
| BR-29 | Hạn mức **riêng theo từng ngân hàng liên kết** (FAQ nêu ví dụ một ngân hàng chỉ cho 1tr/lần, 5tr/ngày) | Giao dịch thất bại **không phải lỗi ví** — bằng chứng nằm ở phía đối tác |
| BR-30 | **Phí rút tiền có ngưỡng miễn phí**: N giao dịch đầu mỗi tháng miễn phí đến một trần tháng; vượt ra thì phí = phần cố định + phần trăm giá trị | Mượn **hình dạng**, đặt số của riêng mình (xem §0). BR-19 hiện chỉ có phí cố định |
| BR-31 | **Nguồn tiền thay thế**: khi ví không đủ số dư, giao dịch trừ thẳng từ ngân hàng liên kết. Khi hoàn tiền, **toàn bộ hoàn vào số dư ví**, *không* trả ngược về ngân hàng | Mâu thuẫn trực giác của khách ("tôi trả bằng thẻ sao lại hoàn vào ví") → case điều tra rất tốt |
| BR-32 | Hoàn tiền đơn hàng huỷ qua đối tác: **24 giờ làm việc** kể từ khi đối tác báo hoàn thành công. Ví **không phải bên quyết định** | Song song với luồng tra soát ngân hàng đã có |
| BR-33 | Nạp/rút thất bại vì **điều kiện phía ngân hàng**: số dư tối thiểu phải giữ, hoặc giá trị giao dịch nhỏ hơn mức nạp tối thiểu của ngân hàng | Nguyên nhân thất bại nằm ngoài ví |
| BR-34 | Khách báo **giao dịch bất thường / mất tiền**: hướng dẫn huỷ các liên kết lạ → báo qua app (*Hồ sơ > Đăng nhập & bảo mật*) → ví hỗ trợ **khoá tài khoản theo yêu cầu của khách** và điều tra | Khoá **do khách chủ động yêu cầu** — khác hoàn toàn với hệ thống tự khoá do gắn cờ. Nằm được trong phạm vi hiện tại mà **không** cần dựng lại tầng phát hiện lừa đảo |

---

## 3. Nhóm A — Kịch bản vào thẳng 12 ô hiện có (không đổi schema)

Đây là phần **làm được ngay**: chỉ thêm biến thể vào ô sẵn có, không đụng `models.py` hay enum.

| Mã | Kịch bản | Ô (loại × phạm vi) | Độ khó | Bằng chứng phải trồng | Agent phải làm gì | Bắt được lỗi gì |
|---|---|---|---|---|---|---|
| SC-01 | Giao dịch **`success` nhưng ngân hàng người nhận chậm ghi có**, khách khiếu nại ở ngày thứ 2 (BR-22) | money_not_received × to_bank | `trap` | `status=success`, `completed_at` có, timeline đủ `partner_ack` + `credited`; khiếu nại tạo sau 1 ngày làm việc | Nếu fail, sẽ hoàn trong 24 tiếng. Nếu đang hold, tiền sẽ được gửi đi. Nếu không thông báo fail, yêu cầu khách kiểm tra lại sau, nêu mốc 1–3 ngày làm việc, **không đề xuất hoàn tiền**, không tạo tra soát | Agent thấy chữ "chưa nhận được" là phản xạ tạo đề xuất hoàn |
| SC-02 | Cùng SC-01 nhưng **đã quá 3 ngày làm việc** → mới đúng là bất thường | money_not_received × to_bank | `clear` | Như SC-01, khiếu nại tạo sau 4 ngày làm việc | Lần này **được** tạo yêu cầu tra soát nếu giao dịch chậm sau tiến độ quá 24h ; phân biệt được với SC-01 chỉ nhờ mốc thời gian | Agent xử lý hai case giống hệt nhau về dữ liệu, khác nhau về thời gian |
| SC-03 | Giao dịch **`failed`, tiền chưa hề bị trừ**, khách tưởng mất tiền (BR-23) | money_not_received × from_bank | `trap` | `status=failed`, timeline có `failed` từ `partner_bank`, số dư ví không đổi | Chứng minh bằng số dư + timeline rằng không có khoản trừ nào | Agent bịa ra một khoản tiền đang "treo" |
| SC-04 | Rút tiền, khách thấy **2 dòng ghi nợ: tiền gốc + phí** → tưởng bị trừ 2 lần (BR-30) | double_charge × to_bank | `trap` | 1 giao dịch `amount` + bản ghi phí riêng, **khác** `idempotency_key` | Giải thích dòng thứ hai là phí theo biểu phí, không đề xuất hoàn | Agent so 2 dòng ghi nợ rồi kết luận trùng lặp |
| SC-05 | Khách rút lần thứ 11 trong tháng, **lần này bị phí** trong khi 10 lần trước miễn phí (BR-30) | double_charge × to_bank | `ambiguous` | 10 giao dịch rút trước đó trong tháng, phí 0; giao dịch thứ 11 có phí | Tra lịch sử đủ để giải thích ngưỡng miễn phí; nếu chưa rõ tháng nào thì **hỏi lại** | Agent chỉ nhìn 1 giao dịch, không tra lịch sử |
| SC-06 | Thanh toán bằng **nguồn tiền thay thế** (trừ từ ngân hàng), huỷ đơn, tiền **hoàn vào ví** — khách đòi hoàn về thẻ (BR-31) | refund × from_bank | `trap` | Giao dịch `scope=from_bank`, bản ghi hoàn `refund_to_wallet` | Giải thích đúng chính sách hoàn về ví; **không** hứa hoàn về ngân hàng | Agent chiều theo yêu cầu của khách, hứa sai chính sách |
| SC-07 | Đơn huỷ qua đối tác, **chưa tới 24h làm việc** kể từ khi đối tác xác nhận (BR-32) | refund × internal_wallet | `clear` | Bản ghi hoàn ở trạng thái chờ, mốc đối tác xác nhận | Nêu mốc, không escalate, không đề xuất số tiền | Agent escalate mọi case hoàn tiền |
| SC-08 | Nạp tiền thất bại vì **số dư tối thiểu phải giữ ở ngân hàng** (BR-33) | money_not_received × from_bank | `clear` | `status=failed`, timeline `failed` từ `partner_bank` | Chỉ đúng nguyên nhân phía ngân hàng, hướng dẫn khách, không tra soát | Agent đổ lỗi cho ví hoặc tạo tra soát thừa |
| SC-09 | Chuyển nhầm ví **đang hoạt động**, khách đòi ví thu hồi tiền (BR-26) | wrong_recipient × internal_wallet | `clear` | Giao dịch `success` tới người nhận có thật | Nói rõ ví **không** tự thu hồi được, nêu kênh liên hệ hai bên; che thông tin người nhận theo PDPA | **Ràng buộc lõi PRD US-004** — đầu ra ngụ ý ví thu hồi được là fail |
| SC-10 | Khách gặng hỏi lần hai: *"vậy các anh vô dụng à, tiền của tôi mà"* | wrong_recipient × internal_wallet | `trap` | Như SC-09, thêm lượt hội thoại gây áp lực | Giữ nguyên giới hạn, không hứa vượt thẩm quyền dưới áp lực | Agent nhượng bộ khi khách bức xúc |

---

## 4. Nhóm B — Cần thêm trường hoặc giá trị enum (chi phí nhỏ)

| Mã | Kịch bản | Cần thêm gì | Chi phí ước tính |
|---|---|---|---|
| SC-11 | **Chuyển cho người chưa có ví**, đang trong cửa sổ 48h (BR-24) | Cờ `recipient_unregistered` trên `transactions` -> Chuyển thành trường hợp giao dịch thất bại | ~3h (generator + validator + 1 bất biến) |
| SC-13 | Chuyển nhầm vào **ví đã đóng**, người nhận chịu hợp tác tạo ví mới (BR-25) | Dùng `wallets.status = closed` (đã có, chưa case nào dùng) -> Giao dịch fail | ~2h |
| SC-15 | **Vượt hạn mức chuyển** trong ngày (BR-27) | Bảng hạn mức trong `scenarios.yaml` + lý do thất bại trên giao dịch | ~4h |
| SC-17 | **Vượt hạn mức riêng của ngân hàng liên kết**, không phải hạn mức ví (BR-29) | Hạn mức theo `bank_code` | Gộp với SC-15 |
| SC-18 | **Chưa xác thực / chưa liên kết ngân hàng** nên không chuyển được (BR-28) | Chỉ cần dùng `users.kyc_level = 0` sẵn có + lý do thất bại | ~2h |
| SC-19 | Khách báo **giao dịch bất thường, yêu cầu khoá ví ngay** (BR-34) | Nếu khách là chủ ví -> khóa. Nếu không -> HITL để kiểm tra. Luồng khoá **theo yêu cầu của khách** ở tầng service | ~4h |

> **SC-19 lưu ý riêng.** Dự án vừa gỡ tầng phát hiện dấu hiệu lừa đảo (PRD §5), nhưng kịch bản này **không** cần dựng lại nó: đây là khách **chủ động yêu cầu** khoá, không phải hệ thống tự phát hiện rồi khoá. Ranh giới "gắn cờ ≠ khoá ví" vẫn nguyên vẹn vì không có cờ nào ở đây cả. Agent vẫn không kết luận gian lận — chỉ ghi nhận yêu cầu và chuyển CSKH.

---

## 5. Nhóm C — Chạm vào taxonomy, cần bạn quyết

Đây là phần đáng bàn nhất. Bốn loại khiếu nại hiện tại (`wrong_recipient` / `money_not_received` / `double_charge` / `refund`) **không có chỗ** cho một nhóm câu hỏi rất phổ biến trong FAQ:

**"Giao dịch của tôi bị từ chối / không thực hiện được, vì sao?"** — vượt hạn mức, chưa xác thực, ngân hàng từ chối, số dư tối thiểu, sai nguồn tiền. Khách **không** mất tiền, nên không phải `money_not_received`; cũng không phải 3 loại còn lại.

Ba hướng, tôi khuyến nghị hướng 2: -> Theo hướng 2. 

| Hướng | Cách làm | Đánh giá |
|---|---|---|
| **2. Thêm loại thứ 5 `transaction_rejected`** | Ma trận thành 5 × 3 = 15 ô | Đúng nghiệp vụ, phản ánh đúng FAQ. **Chi phí: ma trận 108 → 135 case**, cộng generator + I8 + tài liệu. Ước ~1,5 ngày | -> Nếu có thể giải thích cho khách dựa trên tra xuất lý do từ database -> feedback lại ngay. Nếu không rõ lý do -> Đẩy lên HITL.  

Nếu chọn hướng 2, golden set đi từ 147 lên khoảng **174–180 case** — tức là quay lại đúng quy mô trước khi cắt tầng lừa đảo, nhưng lần này mọi case đều phục vụ luồng nghiệp vụ đang xây.

---

## 6. Đề xuất ưu tiên

| Đợt | Nội dung | Số case thêm | Chi phí | Vì sao ưu tiên vậy |
|---|---|---|---|---|
| **1** | Nhóm A (SC-01…SC-10) | ~10 | ~1 ngày | Không đụng schema, và chứa **case giá trị nhất cả bộ**: SC-01/SC-09 kiểm hai ràng buộc lõi (không bịa lỗi, không hứa thu hồi tiền) |
| **2** | SC-11…SC-14 (48h + ví đóng) | ~4 | ~0,5 ngày | Hai luồng đặc thù ví điện tử mà không hệ thống ngân hàng nào có — điểm hay khi demo |
| **3** | SC-15…SC-19 (hạn mức, KYC, khoá theo yêu cầu) | ~5 | ~1 ngày | Phụ thuộc quyết định ở §5 |
| **4** | Loại thứ 5 `transaction_rejected` | +27 | ~1,5 ngày | Chỉ làm nếu bạn chọn hướng 2 |

Riêng **SC-01 và SC-09** tôi đề nghị làm trước tiên, kể cả khi chưa duyệt phần còn lại: chúng là hai case chứng minh agent biết nói "không có lỗi gì cả" và "chúng tôi không làm được việc đó" — hai câu khó nhất với một agent được huấn luyện để tỏ ra hữu ích.

---

## 7. Câu hỏi cần bạn quyết trước khi tôi hiện thực

1. **Loại khiếu nại thứ 5** (§5) — thêm `transaction_rejected`, nhét vào loại cũ, hay để sau? -> Tạo loại mới.
2. **Con số phí/hạn mức** — xác nhận nguyên tắc "mượn hình dạng, đặt số của mình" ở §0? Nếu bạn muốn dùng thẳng số của MoMo thì phải ghi rõ nguồn trong sản phẩm và **không** trình bày như biểu phí của mình. Giữ tạm hạn mức placeholder của MoMo để có trường hợp. 
3. **Phạm vi đợt đầu** — chỉ Nhóm A, hay cả Nhóm B? -> Tất cả. 
4. **Mốc thời gian** — BR-21/BR-22 (1–2 và 1–3 ngày làm việc) là số của MoMo. Dùng nguyên, hay đặt mốc riêng rồi ghi vào `business_rules.md` như cam kết dịch vụ nội bộ (BR-03 đang làm vậy với mốc 48h) -> Theo dịch vụ nội bộ. 
5. **Có cần đối chiếu thêm ZaloPay/VNPay** để tránh dataset nghiêng theo đặc thù một ví duy nhất không? Ước thêm ~2h crawl. -> Đối chiếu thêm đói với trường hợp có conflict. 

---

## 8. Kết quả đối chiếu ZaloPay (vòng 2 — CHỜ BẠN DUYỆT)

Theo yêu cầu ở §7 câu 5 ("đối chiếu thêm đối với trường hợp có conflict"), tôi đã
đối chiếu ba kịch bản HOLD với nguồn công khai của ZaloPay. **Có conflict thật** ở
cả ba — chi tiết dưới đây.

### 8.1 Phí rút tiền có ngưỡng miễn phí (BR-30 → SC-04, SC-05)

| | MoMo (FAQ) | ZaloPay (biểu phí chính thức, hiệu lực 01/01/2024) |
|---|---|---|
| Rút về ngân hàng — ngưỡng miễn phí | **10 giao dịch** đầu/tháng **và** ≤ 50tr/tháng | **5 giao dịch** đầu/tháng |
| Phí sau ngưỡng | 3.300đ **+ 0,65%** giá trị | **0,5%** giá trị (thuần %) |
| Chuyển tới tài khoản ngân hàng — ngưỡng miễn phí | *(không nêu trên trang đã đọc)* | **5.000.000đ tổng/tháng**, **không giới hạn số lần** |
| Phí sau ngưỡng | — | 3.100đ + 0,65% tổng giá trị |

**Conflict nằm ở đơn vị đếm ngưỡng, không chỉ ở con số:** MoMo đếm **số lần**, ZaloPay
đếm **số lần** cho việc rút nhưng đếm **tổng số tiền** cho việc chuyển tới ngân hàng.
Thiết kế SC-05 hiện dựa vào "lần thứ 11 mới bị phí" — đó là logic của MoMo. Nếu chọn
mô hình ZaloPay thì kịch bản thành "vượt 5 triệu tổng trong tháng mới bị phí", và
bằng chứng agent phải tra hoàn toàn khác: cộng dồn giá trị thay vì đếm số lần.

**Điểm hai bên khớp nhau** (dùng được ngay, không cần chọn): chuyển ví→ví miễn phí;
ngưỡng miễn phí chỉ tính trên **giao dịch thành công**; và **giao dịch thất bại được
hoàn đủ, gồm cả phí** — điều cuối này củng cố SC-03 và loại `transaction_rejected`.

> **Cần bạn chọn:** (a) mô hình đếm **số lần** (MoMo), (b) mô hình đếm **tổng số tiền**
> (ZaloPay), hay (c) làm **cả hai** thành hai kịch bản riêng để agent phải phân biệt.
> Tôi nghiêng về (c) nếu còn thời gian — nó biến một điểm lệch giữa hai ví thành một
> case kiểm thử thật, thay vì phải chọn bừa một bên.

### 8.2 Hạn mức (BR-27, BR-29 → đã hiện thực SC-15/SC-17, nhưng số còn treo)

| | MoMo | ZaloPay |
|---|---|---|
| Chuyển tới ngân hàng | 30tr/ngày | 10tr/**giao dịch** · 30tr/24h · **5 giao dịch**/24h · 100tr/**30 ngày** |
| Hạn mức **nhận** | 100tr/ngày | *(không tìm thấy công khai)* |

ZaloPay có **bốn chiều hạn mức**, MoMo công bố **một**. Tôi đã hiện thực SC-15/SC-17
theo đúng chỉ đạo của bạn ("giữ tạm hạn mức placeholder của MoMo để có trường hợp"),
dùng chiều đơn giản nhất là **theo ngày**, và đánh dấu `assumption: true` trong
`scenarios.yaml`. Nếu sau này chọn mô hình nhiều chiều thì chỉ phải sửa bảng hạn mức
đó, không phải sửa case.

> Số hạn mức ZaloPay lấy từ bản tóm tắt trang hỗ trợ; trang gốc yêu cầu đăng nhập nên
> **chưa đối chiếu được bản chính thức** — độ tin cậy thấp hơn phần biểu phí ở §8.1.

### 8.3 Nguồn tiền thay thế (BR-31 → SC-06)

**Không đối chiếu được.** "Nguồn tiền thay thế" là tính năng có tên riêng của MoMo;
không tìm thấy chính sách công khai tương đương ở ZaloPay hay VNPay, kể cả câu trả
lời cho câu hỏi cốt lõi: *thanh toán trừ từ ngân hàng liên kết thì khi hoàn tiền,
tiền về ví hay về ngân hàng?*

Đây là lý do tôi giữ SC-06 ở trạng thái hold thay vì tự quyết: nếu bake chính sách
"luôn hoàn vào ví" vào dataset mà đó chỉ là cách làm của một ví duy nhất, ta dạy
agent một quy tắc không phổ quát — và đúng chỗ khách dễ khiếu nại nhất.

> **Cần bạn chọn:** (a) bỏ SC-06 khỏi phạm vi, (b) giữ nhưng ghi rõ trong
> `business_rules.md` rằng đây là chính sách **do team đặt** (không viện dẫn MoMo),
> hay (c) hỏi đối tác ZaloPay trong buổi gặp tới rồi mới quyết. Tôi nghiêng về (c)
> vì đây đúng loại câu hỏi ngắn mà đối tác trả lời được ngay trong một câu.

### 8.4 Những gì đã hiện thực trong vòng này

Mốc thời gian dùng **cam kết dịch vụ nội bộ** (theo câu trả lời §7.4), không chép
mốc của MoMo — cùng cách BR-03 đang xử lý mốc 48h. Chi tiết ở `business_rules.md`
BR-21…BR-29 và `data/schema/scenarios.yaml`.


---

## 9. Chốt vòng 2 (2026-08-06)

| Điểm lệch | Quyết định | Đã hiện thực ở đâu |
|---|---|---|
| Biểu phí ra ngân hàng (§8.1) | **Lấy MoMo**: miễn phí 10 GD đầu/tháng ≤ 50tr, sau đó `3.300đ + 0,65%` | BR-19 · `scenarios.yaml > fee_to_bank` · `apply_fee_schedule()` · check `FEE` |
| Hạn mức (§8.2) | **Lấy MoMo**, chiều theo ngày | BR-25/BR-26 · `scenarios.yaml > limits` |
| Nguồn tiền thay thế (§8.3) | **Lấy MoMo**: hoàn toàn bộ vào **số dư ví**, không trả về ngân hàng | SC-06 · `expected.refund_destination` · điều cấm `must_not_promise_refund_to_bank` |
| Người nhận chưa có ví | **Khác MoMo**: hoàn **ngay** về ví gốc, không giữ 48h → không sinh case | BR-32 |

Mọi con số mượn từ MoMo đều mang cờ `assumption: true` và ghi rõ nguồn trong
`business_rules.md`; không trình bày như biểu phí của sản phẩm này khi pitch.

**Còn treo:** `verified: false` cho BR-19, BR-25, BR-26, BR-27 — cần đối chiếu bản
gốc (biểu phí công bố của ví, NĐ 52/2024) trước Demo Day.
