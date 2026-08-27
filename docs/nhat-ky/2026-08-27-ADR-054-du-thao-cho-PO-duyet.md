# ADR-054 (DỰ THẢO — CHỜ PO THẬT QUYẾT) — Mã OTP trả thẳng qua API: đặt tên cho một đánh đổi đang vô danh

**Ngày:** 2026-08-27 · **Trạng thái:** 🟡 **DỰ THẢO — CHƯA THI HÀNH.** Không ai vá gì trước khi PO trả lời.
**Gấp vì:** đợt thử **150 người dùng thật** sắp chạy trên tên miền công khai.

---

## 1. Đo được — hai phiên đo độc lập, khớp nhau

| | |
|---|---|
| `src/api/main.py:440-448` | `/auth/otp/request` *(vai `customer`)* — trả `otp_code` trong thân JSON, **vô điều kiện** |
| `src/api/main.py:952-963` | OTP duyệt resolution *(vai `supervisor`)* — trả `otp_code` trong thân JSON, **vô điều kiện** |
| `src/api/main.py:168` | `_LA_PROD = APP_ENV == "production"` — **cờ đã tồn tại** |
| `src/api/main.py:172-174` | …và **chỉ** được dùng ở `docs_url`/`redoc_url`/`openapi_url` |

🔴 **Ta đang bảo vệ TÀI LIỆU API kỹ hơn bảo vệ MÃ DUYỆT HOÀN TIỀN.**

Bình luận trong mã tự khai: *"sản phẩm thật sẽ gửi qua SMS, KHÔNG BAO GIỜ trả OTP qua API response."*
📌 **Đó là một lời hứa trong BÌNH LUẬN, không phải một nhánh trong MÃ.** Không dòng nào phân biệt được
"sản phẩm thật" với "demo".

**Lead đo thêm, độc lập:** `grep` toàn `src/` cho `twilio|nexmo|vonage|zalo-otp|gui_sms` → **0 kết quả**.
**Không tồn tại đường gửi SMS nào.**

**Lead cũng xác nhận phần KHÔNG hỏng:** `verify_otp` (`:481`) so khớp đúng, có khoá sau N lần sai, có
`commit()` trước khi raise. ⟹ **Lỗ nằm ở PHÁT HÀNH, không nằm ở XÁC MINH.**

---

## 2. Hệ quả — nói cho chính xác, không thổi phồng

· ✅ **Người lạ KHÔNG lấy được mã.** Cả hai đường đòi phiên hợp lệ + đúng vai trước. **Không** phải lỗ
  cho người ngoài.
· ✅ **KHÔNG vi phạm Ràng buộc cứng #4** — vẫn là OTP **phiên**, không hỏi OTP giao dịch ngân hàng,
  không hỏi mật khẩu ví.
· 🔴 **Nhưng làm RỖNG ý định của ADR-005.** Bản chất: **hai yếu tố bị gộp thành một.**

```
ADR-005 định:  yếu tố 1 = ĐỊNH DANH (giữ được access_token)
               yếu tố 2 = SỞ HỮU KÊNH NGOÀI BĂNG TẦN (nhận được mã ở nơi khác)

thực tế nay:   yếu tố 1 TỰ ĐỦ để lấy luôn yếu tố 2
```
⟹ Một `access_token` của sếp bị lộ *(XSS · phiên bỏ quên chưa khoá máy · token lẫn vào log)* là **đủ để
duyệt hoàn tiền TRỌN VẸN**, không cần chạm gì khác. **Đúng nguy cơ ADR-005 sinh ra để chặn.**

**Hai đường KHÁC HẠNG RỦI RO — đây là lý do phải tách:**

| | hậu quả tối đa nếu bị lợi dụng |
|---|---|
| `:445` khách | khách **tự xác thực phiên của chính mình**. Không sinh hành động tài chính nào. |
| `:957` duyệt | 🔴 **cửa DUY NHẤT tới `approved`** *(ADR-002)*. Tiền ra khỏi ví. |

---

## 3. Vì sao HÔM NAY khác hôm qua

Đây là **một đánh đổi demo được khai báo tử tế** — không ai giấu gì, ghi chú nằm ngay trong phản hồi.
Cái đổi là **môi trường đã đổi dưới chân nó**:

```
· chạy trên tên miền công khai app.adaptivealgo.uk
· sắp có đợt thử 150 NGƯỜI DÙNG THẬT
· Marketing đang dựng /cho-khach-hang — trang CHỐNG LỪA ĐẢO, thông điệp lõi là về OTP
```
⟹ **"Môi trường demo" sắp hết đúng, và không dòng mã nào nhận ra sự khác biệt.**

---

## 4. Cách vá HIỂN NHIÊN — và vì sao **đã bị bác**

❌ **Không gate bằng `_LA_PROD` / `APP_ENV=production`.**

**Bằng chứng, không phải cảm tính:** hộp production **chính là** hộp demo, và **không có SMS** *(đo ở §1)*.
Gate theo `APP_ENV` sẽ **khoá cứng đăng nhập + duyệt** trong đợt 150 người, **không còn lối thoát nào ngoài
gỡ gate ra**.

📌 Và khi ai đó gỡ nó ra cho chạy được, **ta mất cả gate lẫn sự chú ý** — tệ hơn hẳn hiện trạng, vì lúc đó
hồ sơ ghi là "đã có gate".

---

## 5. Đề xuất — hai cờ RIÊNG, mặc định ĐÓNG

```
CHO_PHEP_TRA_OTP_QUA_API_KHACH   (:445)   mặc định false
CHO_PHEP_TRA_OTP_QUA_API_DUYET   (:957)   mặc định false
```

**Vì sao cờ riêng, không dùng `APP_ENV`:** đây là **một quyết định về RỦI RO**, không phải một thuộc tính
của môi trường. Cờ riêng buộc người bật **gõ đúng tên nó ra** — cái tên tự khai đang đánh đổi gì.

**Vì sao mặc định ĐÓNG:** mọi ảnh · mọi máy mới · mọi CI **fail-closed tự động**, không ai phải nhớ tắt.
📌 Đúng nguyên tắc 12-factor PO đã chốt: *secret không có default an toàn giả*.

**Vì sao TÁCH LÀM HAI:** không phải để cho gọn. Gộp một cờ **ép PO chọn "cả hai cùng bật" hoặc "cả hai
cùng tắt"**, trong khi câu trả lời hợp lý nhất có thể là **lệch nhau**.

📌 Khuôn này **không phải phát minh mới** — dự án đã dùng đúng khuôn ở `PHAN_LUONG_BAT` · `CONG_T0_BAT` ·
`CONG_OTP_NHOM_B_BAT`.

---

## 6. 🔴 HAI CÂU CHỜ PO — không ai trong đội trả lời thay được

### Câu 1 — đợt thử 150 người thật, bước **duyệt tiền** có được phép **một yếu tố** không?

```
A. MỞ CẢ HAI   giữ nguyên hành vi hôm nay, nhưng nay CÓ TÊN và mặc định đóng ở mọi nơi khác.
               giá: bước duyệt tiền vẫn là một yếu tố suốt đợt thử.

B. MỞ KHÁCH ·  150 người đăng nhập bình thường. Duyệt tiền giữ được hai yếu tố.
   ĐÓNG DUYỆT  giá: người duyệt thật cần một đường lấy mã khác → xem Câu 2.

C. ĐÓNG CẢ HAI 150 người KHÔNG đăng nhập được. ❌ Không khả thi, liệt ra cho đủ.
```

### Câu 2 *(Lead nêu — và nó là câu quyết định B có thật hay không)*

🔴 **Nếu chọn B, cơ chế THAY THẾ để supervisor thật vẫn duyệt được là gì?**

📌 **Không có câu trả lời cho câu này thì "đóng" chỉ là một quyết định trên giấy.** Đúng bài học dự án đã
trả giá nhiều lần: **quyết định không kèm cơ chế thi hành thì không tồn tại.**

Ứng viên *(liệt để PO chọn, KHÔNG phải đề xuất của đội)*:
- DevOps đọc OTP từ **log server** rồi báo tay qua kênh riêng *(gọi điện/Slack)* cho người duyệt.
  ✅ Giữ được tính **ngoài băng tần** dù không qua SMS thật.

⚠️ **Một dữ kiện làm B rẻ hơn vẻ ngoài — PO xác nhận giúp:** trong đợt 150 người, **150 người đó là
KHÁCH**. Bước `approve` là việc của **supervisor**, tức là **người trong đội**. Nếu đúng vậy thì đóng
`:957` chỉ phiền **vài người nội bộ có sẵn quyền đọc log**, không phiền 150 người ngoài.
**Nếu kịch bản thử có cho người ngoài đóng vai sếp thì kết luận này SAI** — nên cần PO xác nhận.

---

## 7. Trạng thái thi hành

```
[ ] PO trả lời Câu 1 + Câu 2
[ ] Lead vá theo hướng đã chốt (src/ — vùng của Lead)
[ ] Đối chứng: gọi thật cả hai endpoint ở cả hai trạng thái cờ, dán phản hồi thật
[ ] Marketing: KHÔNG được hứa "OTP gửi qua SMS" trên /cho-khach-hang chừng nào chưa đổi (đã chuyển)
[ ] UX/UI: ảnh mkt-2 không đăng ở dạng hiện mã (đã chuyển)
```

**Không đụng `contracts/`** — không route nào thêm/bớt, không vai nào đổi. Đây là thay đổi **hành vi phản
hồi**, không phải thay đổi **cấu trúc**.
