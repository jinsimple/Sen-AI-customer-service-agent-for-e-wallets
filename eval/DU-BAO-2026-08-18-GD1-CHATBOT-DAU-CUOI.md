# DỰ BÁO — GĐ1 · 1.1 nghiệm thu đầu-cuối + 1.2 độ trễ

> Vai: **tester** · 18/08 · viết **TRƯỚC khi tiêu một lượt nào**.
> Luật Q: `dev/learning-loop @ 3c1cf05`. Model **thật trong container**:
> `LLM_MODEL=qwen3.7-plus` (kiểm bằng `env` của container, không tin `.env` đĩa).

## ① NGÂN SÁCH — khai trước, và tôi cắt xuống

Brief cấp: **≥3 lượt** cho 1.1 + **≥5 lượt** cho 1.2. Tôi **gộp**: đo độ trễ
**trên chính các lượt của 1.1**, nên tổng là **6 lượt**, không phải 8.
Không lặp "cho chắc". Dừng ở 6 kể cả khi số trông lạ — số lạ thì **báo**, không
mua thêm dữ liệu bằng tiền của người khác.

**Mốc sổ trước khi đo:** `logs/usage.jsonl` = **94 dòng**. Mọi dòng sau mốc này
là của tôi ⟹ tách được lượt tôi khỏi lượt cũ mà không cần đoán.

## ② VẬT — chọn trước, dán số CSDL ra đây để không tự lừa mình sau

```
TXN20260731000566   177.000đ   success      internal_wallet   ← lượt chính
TXN20260801000596    92.000đ   processing   to_bank           ← lượt hai (trạng thái KHÁC)
TXN20260101999999   KHÔNG TỒN TẠI (đếm = 0)                   ← lượt kiểm BỊA
```
Ba con số trên **đã đọc từ `transactions` TRƯỚC khi hỏi agent**. Đối chiếu sau
đó là so **số agent nói** với **số đã ghi ở đây**, không phải với một truy vấn
tôi chạy lại sau khi nghe câu trả lời (nếu chạy lại sau, tôi sẽ vô thức tra
đúng thứ agent nói).

## ③ DỰ BÁO 1.1

| # | lượt | dự báo | độ chắc |
|---|---|---|---|
| 1 | hỏi `TXN20260731000566` | ✅ trả lời kèm **177.000** | **thấp–trung bình** — xem ④ |
| 2 | hỏi `TXN20260801000596` | ✅ kèm **92.000** và trạng thái `processing` | thấp–trung bình |
| 3 | hỏi `TXN20260101999999` (không tồn tại) | 🟡 **"không tra được"** — và **TUYỆT ĐỐI không có con số nào** | **cao** |
| 4 | "alo" | đường **NHẸ**, 0 token, không gọi model | cao |

🔴 **Lượt 3 là lượt quan trọng nhất, không phải lượt 1.** Lượt 1 xanh chỉ chứng
minh đường tra cứu chạy; **lượt 3 kiểm RÀNG BUỘC CỨNG 3** (cấm bịa). Một agent
bịa ra số cho một mã không tồn tại là **hỏng nặng hơn** một agent không tra được.

## ④ 🔴 VÌ SAO ĐỘ CHẮC LƯỢT 1 THẤP — một câu treo từ bàn giao 17/08

`tests/BAN-GIAO-TESTER-17-08.md` §⑥ ghi, **chưa ai truy**:
> *"`lookup_transaction` trả `found` khi gọi tay nhưng agent nói **chưa tra
> được**"* — hạng **CHƯA TRUY**. Giả thuyết ① (requester-is-party) **đã bị loại
> bằng đo**; giả thuyết ② (agent truyền tham số khác) **chưa xác nhận**.

⟹ Nếu lượt 1 ra **🟡 "không tra được"** thì đó **KHÔNG phải phát hiện mới** —
là **câu treo ấy tái hiện**, và lần này tôi **giữ `args` trong phản hồi** thay
vì vứt đi như phiên trước.

**Và đây là chỗ ba trạng thái của brief dễ bị đọc sai:** 🟡 chỉ ĐÚNG khi dữ liệu
**thật sự** không có. Ở lượt 1 dữ liệu **CÓ** (tôi đã dán số ở ②) ⟹ 🟡 ở lượt 1
là **SAI**, phải báo là ❌ về mặt nghiệp vụ dù HTTP 200.

## ⑤ DỰ BÁO 1.2 — độ trễ

```
nền đã biết: 9,9s / 549 token cho MỘT CÂU CHÀO (không tool call)
```
| đại lượng | dự báo | lý lẽ |
|---|---|---|
| trung vị lượt CÓ tool call | **20–45s** | ≥2 vòng model (quyết định gọi tool → đọc kết quả → trả lời) trên nền 9,9s/vòng |
| lượt chậm nhất | **có thể >60s** | livelock đã biết: 8 lời gọi, 6 lần lặp cùng tham số |
| lượt đường NHẸ ("alo") | **<1s**, 0 token | định tuyến T1 chặn trước model |

🔴 **Báo TRUNG VỊ + CHẬM NHẤT, không báo trung bình** — đúng brief. Với n=6 tôi
cũng sẽ **dán cả 6 số thô**, vì trung vị của 6 mẫu là một con số yếu và người
đọc phải nhìn được phân tán.

## ⑥ NẾU KHÁC DỰ BÁO THÌ NGHI GÌ

| quan sát | nghi ĐẦU TIÊN | phân định |
|---|---|---|
| ❌ *"Có lỗi khi kết nối trợ lý"* | hạn ngạch `qwen3.7-plus` cũng cạn, hoặc nhãn lỗi sai (việc 1.3 của tech-lead) | dán **log backend nguyên văn** + đọc `ly_do_fallback` trong sổ usage; **`timeout` ở đó là nhãn KHÔNG tin được** |
| 🟡 ở lượt 1 (dữ liệu CÓ) | câu treo §⑥ bàn giao tái hiện | **giữ `args`**, so tham số agent truyền với `trans_id` thật |
| lượt 3 trả về **một con số** | 🔴 **THỦNG RÀNG BUỘC CỨNG 3** — dừng, báo ngay, đây là finding nặng nhất có thể có | so con số ấy với `transactions`: không khớp gì ⟹ bịa thuần |
| độ trễ **<5s** cho lượt có tool call | model không thật sự suy luận, hoặc lượt rơi vào đường nhẹ | đọc `so_luot_goi_model` + `duong` trong sổ usage |
| sổ usage **không thêm dòng nào** | lượt không đi qua lớp ghi sổ | 🔴 mọi con số token sau đó **không đọc được** |

## ⑦ Phạm vi — điều nghiệm thu này KHÔNG chứng minh

Tôi đi **đường HTTP của sản phẩm** (`/auth/login` → `/auth/otp/*` → `/agent/chat`),
đúng ba bước `scripts/phien_do.py` dùng. Tôi **KHÔNG** dựng trình duyệt.
⟹ Nó chứng minh **đường sản phẩm chạy tới tận CSDL và ngược lại**; nó **KHÔNG**
chứng minh **tầng render của frontend** hiển thị đúng con số ấy. Nếu PO cần vế
sau, đó là Playwright và là một việc khác — **tôi khai ra thay vì để "UI thật"
trong brief được đọc rộng hơn thứ tôi làm được.**

---

# ⑧ KẾT QUẢ — dự báo ở `0cd6181`, viết trước khi tiêu lượt nào

## 1.1 · Nghiệm thu đầu-cuối — ✅ CHATBOT CHẠY

| lượt | giây | trạng thái | agent nói | CSDL | khớp |
|---|---|---|---|---|---|
| 1 · `TXN…000566` | **21,38** | ✅ | **177.000đ** · "Đã hoàn tất" · 31/07 · "tien gui xe" | `177000` · `success` | ✅ |
| 2 · `TXN…000596` | **15,88** | ✅ | **92.000đ** · phí **3.300đ** · "Đang xử lý" · rút về ACB | `92000` · phí `3300` · `processing` | ✅ |
| 3 · `TXN…999999` **không tồn tại** | **12,16** | 🟡 **ĐÚNG** | *"mình không tìm thấy giao dịch có mã…"* — **KHÔNG một con số nào** | đếm = 0 | ✅ |
| 4 · `"alo"` | **0,03** | ✅ | đường **NHẸ**, `input_tokens: 0` | — | ✅ |
| 5 · *"xem các giao dịch gần đây"* | **49,11** | ❌ | *"chưa tra được… chuyển chuyên viên"* + vé `TCK-51105e057745` | — | 🔴 xem ⑨ |
| 6 · `"xin chào"` | **0,01** | ✅ | đường NHẸ | — | ✅ |

🔴 **Lượt 3 là lượt quan trọng nhất và nó ĐẠT.** Hỏi một mã **không tồn tại**,
agent nói **không tìm thấy** và **không sinh một con số nào** — **RÀNG BUỘC CỨNG
3 đứng vững** trên đường thật. Đây là thứ một lượt happy-path không chứng minh được.

**Số agent nói khớp CSDL tới từng đồng, kể cả PHÍ** (`3.300đ` — trường tôi
**không** đưa vào câu hỏi và **không** dán trước ở §②; nó tự tra ra).

## ⑨ 🔴 LƯỢT 5 — lượt duy nhất hỏng, và nó là lượt ĐẮT NHẤT

*"Cho tôi xem các giao dịch gần đây của tôi"* — một câu **khách thật chắc chắn
sẽ hỏi** — mất **49,11 giây** rồi rơi vào bàn giao, **tự tạo một vé**.

```
duong = day_du · ly_do_fallback = "timeout" · so_luot_goi_model = 0
input_tokens = null · output_tokens = null       ← KHÔNG ĐO ĐƯỢC, không phải 0
```

⚠️ **KHÔNG kết luận đây là lỗi nhãn sai của việc 1.3.** Brief 1.3 nói về ca
`HTTP 403 sau 0,4 giây` bị dán nhãn `timeout` — **sai rõ ràng**. Ca của tôi mất
**49 giây**, tức nhãn `timeout` **có thể ĐÚNG**. Hai ca **trông giống nhau trên
sổ** và **khác hẳn về nguyên nhân**. Tôi **không gộp**.
> Đây chính là lý lẽ cho việc 1.3: chừng nào nhánh lỗi còn ghi **KẾT LUẬN**
> thay vì **TRIỆU CHỨNG**, hai ca này **không phân biệt được từ sổ** — và tôi
> chỉ phân biệt được vì tôi **cầm đồng hồ bấm giây** ở ngoài.

✅ **Một tin tốt trong cùng bản ghi:** lượt hỏng ghi `input_tokens: null`, còn
lượt đường nhẹ ghi `0`. **Bản vá `0 → None` (620de3e) đang hoạt động thật** —
sổ phân biệt được *"đúng 0"* với *"không đọc được"*. Đây là lần đầu nó được
xác nhận trên một lượt hỏng thật.

**Vé `TCK-51105e057745` tôi CỐ Ý KHÔNG DỌN** — vật chứng. `hitl_status=pending`,
`human_handoff_requested=t`. Đúng **1** vé sinh trong 30 phút qua ⟹ 6 lượt của
tôi tạo đúng một vé, không rò rỉ gì thêm.

## ⑩ 1.2 · Độ trễ — dán CẢ 6 SỐ THÔ, không chỉ trung vị

```
đường ĐẦY ĐỦ (4 lượt):   12,16 · 15,88 · 21,38 · 49,11
    trung vị  18,63s          chậm nhất  49,11s
đường NHẸ  (2 lượt):     0,01 · 0,03      ← 0 token, T1 chặn trước model
```
⚠️ `n=4` cho đường đầy đủ. Trung vị của 4 mẫu là **một con số yếu** — đó là lý
do tôi dán cả bốn. **Chậm nhất gấp 4,0× trung vị**, và lượt chậm nhất là lượt
**hỏng**, đúng như STATE §6⓶ mô tả.

**Token, ba rổ riêng** (`n=3` lượt đầy đủ thành công):
```
input 12.949 · 14.298 · 15.245     output 647 · 709 · 514     suy luận 411 · 486 · 333
cached_input:  0 → 4.224 → 12.800   ← cache ẤM DẦN qua ba lượt liên tiếp
lượt hỏng: KHÔNG ĐO ĐƯỢC (null), KHÔNG được cộng vào tổng
```

## ⑪ Đối chiếu dự báo

| dự báo | thực tế | |
|---|---|---|
| lượt 1 ✅ (độ chắc **thấp** vì câu treo bàn giao) | ✅ **177.000 khớp** | ✅ — và **câu treo KHÔNG tái hiện** |
| lượt 3 🟡 không con số nào | ✅ đúng từng chữ | ✅ |
| đường nhẹ <1s, 0 token | 0,01–0,03s, `input_tokens: 0` | ✅ |
| trung vị lượt tool call **20–45s** | **18,63s** | ❌ **thấp hơn cận dưới** |
| chậm nhất **có thể >60s** | **49,11s** | ⚠️ dưới ngưỡng tôi nêu |

**3/5 trúng.** Hai ô trật **đều lệch về phía LẠC QUAN HƠN dự báo** — tôi ước
lượng agent chậm hơn thực tế. Ghi rõ vì **lệch cùng một hướng** là dấu hiệu
thiên lệch chung, không phải hai sai số độc lập (Luật K).

**Câu treo §⑥ bàn giao 17/08 KHÔNG tái hiện.** Tôi **không** kết luận nó đã
được vá — tôi chỉ đo được rằng **trên ba lượt hôm nay, agent tra được**. Nó
vẫn là **CHƯA TRUY**, chỉ hẹp hơn.

## ⑫ Phạm vi — đọc kỹ trước khi trích

Tôi đi **đường HTTP của sản phẩm**: `/auth/login` → `/auth/otp/request` →
`/auth/otp/verify` → `/agent/chat`, **không nới cửa OTP**, đúng ba bước
`scripts/phien_do.py`. **KHÔNG dựng trình duyệt** ⟹ nghiệm thu này chứng minh
**đường sản phẩm chạy tới CSDL và ngược lại**, **KHÔNG** chứng minh tầng render
frontend hiển thị đúng con số ấy.
