# Cải thiện luồng hỏi chatbot — Đợt 1A + 1B

> **PO thật duyệt 24/08:** *"ok triển khai luôn"*. Nguồn nghiệp vụ: chuyên gia CSKH ngân hàng/ví
> (văn bản PO chuyển 24/08, đặc tả rút gọn ở cuối file). Đợt 2 (FS-13) và Đợt 3 (slot × loại
> vào contract) **chưa duyệt** — không làm.
>
> **Checklist trạng thái sống ở file này.** PO-agent là người duy nhất tick.

---

## CHECKLIST

### Đợt 1A — Luật hỏi trong prompt *(không đụng contract)*

- [x] **1A.1** ✅ `d70763e` — 6 ca R1–R5, viết trước từ đặc tả, R2/R3 tự khai skip-có-lý-do
- [x] **1A.2** ✅ `f6f70df` — R1–R5 vào prompt, 3 điểm chạm, land sau 1A.1 đúng trình tự
- [x] **1A.3** ✅ render thật 4.587 → 4.790 = **+203 token (+4,4%)**, dưới trần 600 · băm mẫu 75a57a47705a → d3ff8c526895, khớp trong cây
- [ ] **1A.4** Cổng: ca mới xanh + không hồi quy A2
- [ ] **1A.5** PO-agent kiểm độc lập → tick

### Đợt 1B — Cổng thu thập tất định *(nối dài `phan_luong`, 0 token khi chạy)*

- [x] **1B.1** ✅ duyệt kèm điều chỉnh: NHÓM B = (i) sở-hữu+động-từ ∨ (ii) mất-mát + số tiền ĐỨNG SAU ≤2 từ (MỘT CHIỀU — sửa lỗi số học ca S2b) · sổ ghi `duong=thu_slot`
- [ ] **1B.2** Coder: thi hành theo thiết kế 1B.1
- [ ] **1B.3** Tester: mở rộng cổng `cong_phan_luong` — ca dương + ca âm bắt-oan
      (câu chính sách có chữ "chuyển tiền" KHÔNG được kích cổng)
- [ ] **1B.4** Ca eval đường-cho-qua trên flash (~60–90K token)
- [ ] **1B.5** Đo lại token/hội thoại, đối chiếu **dự báo đã công bố**

### Chờ PO thật (không thuộc 1A/1B)

- [ ] Đợt 2 — ADR-047 tín hiệu FS-13 "có người hướng dẫn chuyển khoản"
- [ ] Nguồn tài liệu SLA tra soát cho kho RAG (chuyên gia CSKH hoặc soạn từ NĐ 52/2024 + TT 40/2024)

---

## 🔴 DỰ BÁO CÔNG BỐ TRƯỚC — niêm tại đây trước khi code

```
token/hội thoại (trung vị, deepseek, n=11):  18.597  [ĐO 20/08]
dự báo sau 1B:                               12.000–14.000  (giảm 25–35%)
```
Đo lại sau khi 1B chạy. **Không giảm ⟹ cổng không hoạt động như thiết kế — báo nguyên trạng,
không giữ, không chọn lần đo đẹp.**

---

## Đặc tả rút gọn cho 1A (đủ để Tester viết ca, không cần đọc src)

Năm luật phải vào prompt, mỗi luật một hành vi ĐO ĐƯỢC:

| # | luật | hành vi đo được |
|---|---|---|
| R1 | **Một câu hỏi một lượt.** Khi còn thiếu nhiều thông tin, mỗi lượt chỉ hỏi MỘT thứ | reply khi thiếu ≥2 slot chỉ chứa MỘT yêu cầu thông tin |
| R2 | **Hỏi mã giao dịch phải kèm đường đi.** Không nói trống "cho em xin mã" — kèm hướng dẫn dạng "vào Lịch sử, bấm vào giao dịch là thấy" | reply hỏi mã PHẢI chứa hướng dẫn tìm |
| R3 | **Lần hỏi lại thứ hai phải ĐỔI TRỤC.** Tra theo số tiền không ra → hỏi theo trục khác (thời gian, tên người nhận), không lặp nguyên câu | reply hỏi-lại không trùng trục với lần hỏi trước |
| R4 | **Tóm tắt slot trước create_ticket.** Trước khi tạo vé, đọc lại: loại + số tiền + thời gian + đích, để khách tự sửa. (Nâng A2: A2 là "chờ đồng ý", R4 là "đọc lại để khách sửa") | reply ngay trước create_ticket chứa đủ số tiền + thời gian + loại |
| R5 | **Hỏi thời gian bằng mốc neo.** Không hỏi "mấy giờ" — hỏi "hôm nay hay hôm trước, sáng hay chiều" | câu hỏi thời gian không đòi giờ chính xác |

Nguyên tắc gốc (chuyên gia): *mỗi câu hỏi phải mở được một nhánh quyết định · không hỏi thứ
tra được — hỏi để THU HẸP tìm kiếm, không hỏi để lấy dữ liệu*.

## Đặc tả 1B (cho Lead thiết kế)

```
① KHÔNG chặn lời kể — tin nhắn đầu của khách là tự do (= L1 tự nhiên).
   Cổng chỉ xét SAU khi nhận diện ý định tra-giao-dịch.
② BÓC TRƯỚC, HỎI SAU — bóc slot có sẵn trong lời kể (regex: số tiền, mốc ngày,
   mã TXN/TCK — khuôn đã có trong pii.py). CHỈ hỏi phần thiếu, MỘT tin gọn:
   khoảng thời gian + số tiền; mã giao dịch ghi "nếu có" kèm đường đi 3 bước.
③ CỔNG LÀ ĐƯỜNG TĂNG TỐC, KHÔNG PHẢI TƯỜNG — khách không nhớ / kể chuyện khác
   → cho qua LLM như cũ. Nhận diện thà BỎ SÓT còn hơn BẮT OAN: câu chính sách
   ("phí chuyển tiền là bao nhiêu?") tuyệt đối không kích cổng.
```
Điểm nối: `src/agents/phan_luong.py` (đường `nhe`/`day_du` sẵn có, fallback an toàn đã đúng nếp).
Cổng đối chứng: `eval/cong_phan_luong.py` — mở rộng corpus, không thay.

## Những thứ ĐÃ CÓ — cấm làm lại

- Xoa dịu tách khai thác (`prompt.py:21` — "Mình hiểu…" bắt buộc trước kết quả tra)
- Chờ đồng ý tường minh trước create_ticket (test A2)
- `multiple_matches` → PHẢI hỏi lại, cấm tự chọn (contract)
- Danh sách cấm hỏi: OTP/mật khẩu/thẻ (ràng buộc cứng 4) + `otp_disclosed` + che bên thứ ba
- Chống lặp `lap_lai_vo_ich` (R3 NỐI vào đây, không thay)
