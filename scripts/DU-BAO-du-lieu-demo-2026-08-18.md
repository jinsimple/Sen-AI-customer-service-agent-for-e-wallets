# DỰ BÁO — script sinh 4 hành trình demo (GĐ2)

> Công bố **trước** khi ghi dòng nào. Nền: `HEAD=ee6c952`. tech-lead · 18/08/2026.

## 0. Vì sao KHÔNG phải một alembic revision

Cùng lý lẽ đã áp cho `backfill_ma_hoa_description_raw.py`: `docker-entrypoint.sh` chạy
`alembic upgrade head` **mỗi lần container khởi động**, trên **cả ba ngăn xếp** và trên
**production**. Một revision sinh dữ liệu demo nghĩa là **demo tự mọc trên production**.

⟹ Script chạy tay, **mặc định KHÔNG GHI GÌ** (`--ghi` mới ghi).

## 1. Idempotent bằng ID TIỀN ĐỊNH, không bằng "đoán xem đã có chưa"

Mọi bản ghi mang ID cố định (`USR-DEMO-01`, `CMP-DEMO-01`…). Chạy lần hai: khoá chính đã tồn
tại ⟹ **bỏ qua, đếm vào rổ `da_co`**. Không `ON CONFLICT DO UPDATE` — cập nhật im lặng sẽ
che mất việc dữ liệu demo đã bị ai đó sửa tay.

🔴 **Ghi qua ORM, KHÔNG qua SQL thô.** Bốn cột mã hoá at-rest (`complaints.description_raw`,
`messages.content`, `bank_accounts.account_no`, `policy_chunks.text`). SQL thô sẽ nhét
**plaintext** vào đúng cột vừa mất một buổi để backfill.

## 2. Hai ràng buộc hiến pháp, và cách script CHỨNG MINH chứ không hứa

**maker ≠ checker** (`ck_resolutions_maker_checker_br12`): ca ① `created_by=USR-0201`,
`approved_by=USR-0205`; ca ③ `created_by=USR-0202`, `rejected_by=USR-0205`. Script có một
phép tự kiểm cố tình dựng bản ghi `created_by == approved_by` trong **savepoint** rồi
**kỳ vọng CSDL TỪ CHỐI** — nếu CSDL nhận, script **dừng**: constraint đã biến mất.

**Cờ gian lận ≠ khoá ví** (RÀNG BUỘC CỨNG 5): ca ④ bật `otp_disclosed`, `fraud_signals`,
`escalations`, `human_handoff_requested` — và **ví giữ nguyên `active`**. Script khẳng định
điều đó ở cuối. Theo dặn của security, hai việc ấy **không đứng cạnh nhau trong cùng bước**.

## 3. DỰ BÁO — điền TRƯỚC

| # | vật | DỰ BÁO | THẬT |
|---|---|---|---|
| 1 | chạy lần 1 (`--ghi`) tạo | 4 user · 4 ví · 2 tài khoản NH · 5 giao dịch · 4 khiếu nại · 4 vé | 4·4·2·5·4·4 | ✅ |
| 2 | · resolutions · investigation_logs · tool_results | 4 · 13 · 13 | **7** · 13 · 13 | ⚠️ đổi phạm vi, xem §6 |
| 3 | · chat_sessions · messages · escalations | 4 · 26 · 2 | 4 · **28** · 2 | ❌ trượt #messages |
| 4 | chạy lần 2 (`--ghi`) tạo thêm | **0 dòng ở MỌI bảng** | **0 mới · 90 đã có** · mọi mẫu số y hệt | ✅ |
| 5 | 200 khách + 60.001 giao dịch cũ | **KHÔNG đổi một dòng** | khách nền vẫn **200** · script chỉ INSERT | ✅ |
| 6 | phép tự kiểm maker=checker | CSDL **TỪ CHỐI** | TỪ CHỐI — br12 còn sống | ✅ |
| 7 | ví của ca ④ | `status='active'` | `active` | ✅ |
| 8 | `description_raw` của 4 khiếu nại demo | **hình dạng Fernet** | 4/4 Fernet | ✅ |
| 9 | `cited_tool_result_ids` | mọi id **tra được** | 7/7 resolution, 0 id treo | ✅ |
| 10 | `otp_disclosed=true` | **đúng 1** | 1 | ✅ |

## 4. Nếu khác thì nghi gì

| lệch | nghi |
|---|---|
| #4 > 0 | idempotent hỏng ⟹ chạy lần ba sẽ có 12 khách demo, và không ai phát hiện vì màn hình vẫn "có dữ liệu" |
| #5 đổi | script đang ĐỘNG VÀO quần thể nền — dừng, quần thể ấy là thứ làm việc tra cứu giống thật |
| #6 CSDL NHẬN | `ck_resolutions_maker_checker_br12` đã mất ⟹ đây là tin nặng hơn cả việc script hỏng |
| #8 plaintext | tôi đã ghi bằng SQL thô ⟹ tự tạo lại đúng lỗ vừa vá |
| #9 tra không được | demo đang **dạy sai** chính điều sản phẩm bán (ràng buộc cứng 3) |

## 5. Khai trước — KHÔNG được tính là xác nhận

Script chạy xong ⟹ *"4 hành trình có mặt trong CSDL"*. **KHÔNG** ⟹ *"8 màn hình hiển thị đúng"*.
Cổng độ phủ nhãn (tester, bước ②) và soát bằng mắt (PO-agent, bước ③) là hai phép **khác**, và
không phép nào trong số đó tôi tự làm thay được.

**Nhãn tôi biết là CHƯA thắp sau script này** (báo trước, không tự mở rộng phạm vi):
`escalations.target='authority'` · `action_type` `no_action`/`manual_review` ·
`wallets.status` `frozen`/`closed` · `messages.role='system'`.
🔴 `wallets.status='frozen'` **cố ý không thắp ở ca ④** — thắp nó cạnh cờ gian lận là dựng
đúng liên tưởng mà RÀNG BUỘC CỨNG 5 cấm. Muốn phủ, nó phải là một tài khoản **không liên
quan gì tới gian lận**, và đó là một quyết định phạm vi, không phải việc cơ học.

## 6. ĐỔI PHẠM VI GIỮA CHỪNG — khai, không giấu vào ô ✅

Sau khi dự báo đã công bố, PO-agent chuyển tin của tester: **cả 6 giá trị
`reject_reason` đều 0 dòng**, và ADR-019 dựng taxonomy ấy để nuôi vòng học
Phase 2 — vòng học đó hôm nay **rỗng tín hiệu**, không phải "ít".

⟹ Tôi thêm **3 bản ghi TỪ CHỐI** vào lịch sử của chính 4 vé (4 → 7 resolutions).
Đó là **đổi phạm vi**, không phải dự báo trúng. Ô #2 đánh ⚠️ chứ không đánh ✅.

**Vì sao gắn vào 4 vé cũ thay vì dựng hành trình thứ 5:** một vé HITL thật thường
có nhiều lượt đề xuất — bị trả lại, sửa, trình lại. Dựng chúng thành lịch sử của
vé có sẵn là **mô tả đúng quy trình**; dựng thêm khách chỉ để thắp nhãn là dựng
dữ liệu không có ai đứng sau.

**Kết quả đo:** `sai_so_lieu` · `sai_phan_loai` · `thieu_can_cu` · `sai_chinh_sach`
**đã thắp**. 🔴 `trung_case` · `khach_rut` **CÒN RỖNG** — hai lý do ấy mô tả tình
huống mà **không hành trình nào trong bốn cái này LÀ**. Thắp chúng đòi thêm hành
trình ⟹ **quyết định phạm vi của PO**, và bịa cho đủ nhãn chính là thứ tester vừa
TỪ CHỐI làm với `messages.role`.

## 7. Ô #3 TRƯỢT THẬT — 26 dự báo, 28 thật

Tôi ước số lượt hội thoại **trước khi viết** chúng, rồi viết 7 lượt/ca thay vì 6,5.
Trượt nhỏ và vô hại, nhưng nó là **ước lượng, không phải phép đo**, và tôi để nguyên
ô ❌ thay vì sửa dự báo cho khớp.

## 8. Hai lỗi trong lúc chạy, cả hai đã khai trong mã

**① `add_all` + một `flush` ⟹ `ForeignKeyViolation`** — `bank_accounts` bị chèn
trước `users`. Sửa bằng chèn theo nhóm bảng, flush sau mỗi nhóm.
🔴 **Tôi KHÔNG biết cơ chế.** Lời giải thích hiển nhiên — *"ORM không thấy ràng
buộc"* — **SAI**: `models.py:87` có khai `ForeignKey`. Chú thích trong mã ghi
**triệu chứng** và để ngỏ nguyên nhân, thay vì gắn một cơ chế nghe hợp lý mà chưa đo.
Lần chạy hỏng ấy **không ghi một dòng nào** (giao dịch rollback) — đã kiểm: `users=208`.

**② `docker cp` script vào `/tmp` container** — khai theo Luật I, đã xoá,
`docker diff /app/src` = **0**, và chuyển sang chạy **từ host** với `PYTHONPATH`.
