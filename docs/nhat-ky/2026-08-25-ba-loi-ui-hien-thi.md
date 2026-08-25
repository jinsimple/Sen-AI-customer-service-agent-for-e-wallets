# Ba lỗi hiển thị UI (25/08) — hồ sơ chẩn đoán & quyết định

> **Nguồn việc:** PO thật, sau khi tự chạy UI. **Người làm:** Coder (`p-226-63`).
> **Điều kiện nghiệm thu PO đặt:** *"đảm bảo kiểm thử trên UX/UI thật cho tôi chạy tốt
> mới được, tôi kiểm tra lại lần nữa nghiệm thu"* ⟹ ảnh chụp desktop + 375px, trước/sau.

| | lỗi | trạng thái |
|---|---|---|
| ① | bong bóng OTP hiện **hai lần, giống hệt từng chữ** | 🔎 **tìm ra gốc, bản vá CHỜ mở băng `frontend/src/`** |
| ② | markdown thô: khách đọc thấy `**Số tiền**` | ⛔ **KHÔNG VÁ — quyết định có cân** |
| ③ | xuống dòng bị nuốt, ba vế dồn thành một khối chữ | ✅ **đã land `3c70024`** |

---

## ① Bong bóng OTP lặp — GỐC ĐÃ TÌM RA, là lỗi VẼ

**Cách khoanh vùng (hai đầu, không đoán):**
```
[ĐO backend] 4 thread · đường `can_otp` phát ĐÚNG MỘT LẦN mỗi thread, 0 cặp liền kề
[ĐO frontend, PO] eval/results/render_that_so_sanh_25aug.json
                  backend gửi 8 câu → màn hình hiện 12 bong bóng
                  1 bong bóng LẶP 2 LẦN, GIỐNG HỆT TỪNG CHỮ
```
⟹ Backend đúng, **frontend vẽ hai lần**. Và vì hai bong bóng **trùng khít từng chữ**
(không phải "hai câu na ná"), nghi vấn *"hai nguồn khác nhau trông giống nhau"*
(`CANH_BAO_OTP_PHIEN` trong bong bóng vs dòng `chat-disclaimer` cố định dưới ô nhập)
**bị loại** — hai câu ấy khác chữ. **Không cần PO chọn bỏ câu nào.**

**Gốc — hai lệnh `push` cùng đẩy `result.reply`:**
```
frontend/src/app/(app)/chat/ChatClient.tsx

:501   push({ from:"bot", text: result.reply, cite: … })   ← VÔ ĐIỀU KIỆN, mọi đường
       …
:538   if (result.duong === "can_otp") {
:539     push({ from:"bot", text: result.reply });          ← ĐẨY LẠI CHÍNH NÓ
:541     void beginOtpFlow();
```
Câu bị lặp là `src/agents/graph.py:239` (`_CAN_XAC_THUC_OTP`) — trả về ở
`graph.py:1223` kèm `"duong": DUONG_CAN_OTP`.

🔴 **Vì sao lỗi này lọt qua người viết — đáng nhớ hơn chính lỗi:** chú thích ngay trên
`:538` viết *"`reply` vẫn được hiển thị: nó đã mang sẵn câu chống mạo danh K3"*. Người
viết **lo đúng thứ đáng lo** (đừng để mất câu K3), rồi **tự bảo đảm điều đó bằng một
`push` mới** — không biết `:501` cách đó 37 dòng đã đẩy rồi. Cả hai lệnh đều đúng khi
đọc riêng; chỉ sai khi đọc cùng nhau.
⟹ **Một nhánh sớm (`return` giữa hàm) là chỗ dễ nhân đôi tác dụng phụ nhất**: nó ở xa
đoạn dùng chung phía trên đủ để không lọt vào cùng một màn hình.

**Bản vá (một dòng, xoá `:539`)** — an toàn vì trên đường `can_otp` **không có tool nào
được gọi** ⟹ `tool_calls` rỗng ⟹ `cite` ở `:501` là `undefined`. Hai bong bóng vốn
**y hệt nhau**, giữ cái đầu là đủ và không mất chữ nào.

⛔ **CHƯA LAND**: PO đang dựng lại ảnh frontend, `frontend/src/` **đóng băng** (Luật Đ′).
Land ngay sau khi PO báo xong, rồi chụp lại ảnh.

---

## ② Markdown thô (`**Số tiền**`) — **KHÔNG VÁ, quyết định có cân**

🔴 **Đây là quyết định, KHÔNG phải bỏ sót.** Ghi lại để phiên sau không "sửa giúp".

**Vì sao không vá:** nội dung bong bóng **do model sinh**, mà model **đọc chữ khách gõ**.
Dựng markdown thành HTML là mở một đường **prompt injection → XSS**: khách gõ một chuỗi,
model nhắc lại, trình duyệt **thi hành**. Đổi lấy được gì? **Chữ in đậm.**

**Vế PO thêm vào (25/08), nặng hơn vế của Coder:** hai lỗ vừa đóng trong đợt này *(bịa
mã ticket · khai đã tạo vé khi chưa có)* **cùng một họ — hệ thống nói ra thứ nó không
nên nói**. Vá ② là mở đường **thứ ba** cho đúng họ ấy. **Không cân.**

**Và sau `3c70024` thì cái giá đã hạ:** xuống dòng đã đúng ⟹ **cấu trúc đã đọc được**.
Còn lại thuần thẩm mỹ.

**Nếu PO đổi ý — đường đi DUY NHẤT được chấp nhận:**
```
1. thoát HTML TOÀN BỘ chuỗi trước (escape), KHÔNG ngoại lệ
2. rồi dựng lại ĐÚNG một tập đóng, hẹp: xuống dòng · in đậm · gạch đầu dòng
3. TUYỆT ĐỐI KHÔNG: dangerouslySetInnerHTML với chuỗi chưa lọc · thư viện markdown đầy đủ
4. làm SAU khi đóng đợt, kèm test đối kháng: khách gõ <img onerror=…> → phải hiện NGUYÊN VĂN
```

📌 **Việc còn nợ:** chép **bốn dòng trên** thành chú thích cạnh `.bubble` trong
`frontend/src/app/globals.css`. Lý do: người sẽ mở lại ② là người sửa CSS bong bóng, và
**họ đọc tệp CSS, không đọc `docs/nhat-ky/`** — cùng bài học đã ghi ở mục ⑦ của
`2026-08-25-du-kien-ky-thuat-ngoai-hang-muc.md` (cảnh báo Redis đặt tại `docker-compose.yml`).
Chưa làm được vì `frontend/src/` đang đóng băng.

---

## ③ Xuống dòng bị nuốt — đã land `3c70024`

```css
.bubble, .bubble-system { white-space: pre-wrap; word-break: break-word; }
```
**Vì sao đây KHÔNG phải lỗi thẩm mỹ:** chuyên gia thiết kế lượt 5 thành **ba vế**, PO
thật **nới trần token 7.550 → 7.800** để giữ trọn vế thứ ba. Giao diện dồn cả ba thành
một khối chữ liền ⟹ **ta trả tiền để sinh ra cấu trúc, backend gửi đúng cấu trúc, giao
diện xoá cấu trúc trước khi khách kịp thấy.**

**Vì sao chọn CSS chứ không render:** `white-space: pre-wrap` **không diễn giải một ký
tự nào** ⟹ **0 bề mặt tấn công mới**. Cùng lý lẽ đã từ chối ② ở trên.

---

## 🔴 Điều kiện đã suýt làm cả đội kết luận nhầm lần thứ ba trong ngày

`globals.css` **nằm trong ảnh Docker frontend**. PO chỉ dựng lại **backend**.
⟹ Ảnh chụp trước khi dựng lại frontend sẽ cho thấy **lỗi cũ**, và ta sẽ tuyên `3c70024`
là hỏng — đúng khuôn "đo đúng cách, sai VẬT" (ca ③: đo trên một ngăn không mang mã của
đợt). PO xác nhận đã bỏ sót và đang dựng lại.

**Thứ tự bắt buộc:** land ① → dựng lại ảnh frontend → **rồi mới** chụp desktop + 375px.
Chụp trước bất kỳ bước nào trong ba bước ấy là chụp một hệ thống khác.
