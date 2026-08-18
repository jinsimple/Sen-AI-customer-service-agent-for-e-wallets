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
| 1 | chạy lần 1 (`--ghi`) tạo | 4 user · 4 ví · 2 tài khoản NH · 5 giao dịch · 4 khiếu nại · 4 vé | |
| 2 | · resolutions · investigation_logs · tool_results | 4 · 13 · 13 | |
| 3 | · chat_sessions · messages · escalations | 4 · 26 · 2 | |
| 4 | chạy lần 2 (`--ghi`) tạo thêm | **0 dòng ở MỌI bảng** · `da_co` = đủ số trên | |
| 5 | 200 khách + 60.001 giao dịch cũ | **KHÔNG đổi một dòng** | |
| 6 | phép tự kiểm maker=checker | CSDL **TỪ CHỐI** (IntegrityError) | |
| 7 | ví của ca ④ | `status='active'` — cờ gian lận KHÔNG nối sang khoá | |
| 8 | `description_raw` của 4 khiếu nại demo | **có hình dạng Fernet** (không plaintext) | |
| 9 | `cited_tool_result_ids` | mọi id **tra được** trong `tool_results` | |
| 10 | `otp_disclosed=true` | 761 dòng cũ = 0 ⟹ sau khi chạy **đúng 1** | |

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
