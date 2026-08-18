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
