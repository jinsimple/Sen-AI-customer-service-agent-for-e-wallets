# DỰ BÁO — A/B tắt/bật suy luận, chiều TẮT

> Vai: **tester** · 18/08 · viết **TRƯỚC khi tiêu lượt nào của chiều TẮT**.
> Vật đo lại bằng phép của tôi, không nhận qua lời:
> ```
> container fin05-backend-1  tạo 2026-08-18T14:00:27Z
> LLM_MODEL   = qwen3.7-plus-2026-05-26
> SUY_LUAN_BAT= 0
> mốc sổ usage trước khi đo = 101 dòng
> ```

## ① Ràng buộc thiết kế phép so — nêu lại vì nó dễ bị phá

**Nền 6 lượt sáng nay KHÔNG phải nhánh thứ ba.** Chúng chạy trên
`qwen3.7-plus` + container tạo trước 13:54. So chúng với chiều TẮT là so
**hai model trên hai container**, không phải so **một cờ**. A/B chỉ đọc được khi
**cả hai chiều chạy trên CÙNG bản dựng `14:00:27Z`**.

⟹ Hôm nay tôi giao **chiều TẮT (6 lượt)**. Chiều BẬT cần **recreate với
`SUY_LUAN_BAT=1`** — **việc của tech-lead**, không phải của tôi.

## ② Nguồn phân định — KHÔNG tin `env`

Đọc **`suy_luan_gui`** trong `usage.jsonl`: trường ấy đọc ngược ra **từ đối
tượng model vừa dựng**, không đọc từ config. Nếu tên tham số sai thì `extra_body`
không bám mà cờ vẫn nói *"đã tắt"* — **`env` và hành vi thật lệch nhau, và chỉ
trường này bắt được**. Hai nguồn độc lập (Luật D).

## ③ DỰ BÁO — chiều TẮT

| # | dự báo | độ chắc |
|---|---|---|
| 1 | `suy_luan_gui = false` ở **mọi** lượt đường đầy đủ | **cao** |
| 2 | `reasoning_tokens = 0` ở mọi lượt thành công | **cao** |
| 3 | 🔴 lượt `TXN…999999` **VẪN từ chối bịa**, không con số nào | **trung bình** — xem ④ |
| 4 | hai lượt tra cứu vẫn khớp CSDL: **177.000 · 92.000 · phí 3.300** | **trung bình-cao** |
| 5 | độ trễ đường đầy đủ **3–8s** (nền BẬT sáng nay: 12–21s) | **trung bình** |
| 6 | lượt *"xem giao dịch gần đây"* **qua được** trần 45s | **trung bình** |

## ④ 🔴 Ô số 3 là ô quyết định, và tôi để độ chắc TRUNG BÌNH có lý do

Suy luận là chỗ model **tự kiểm lại trước khi nói**. Với một agent **điều tra**,
đó đúng là chỗ *"tool trả `not_found` ⟹ ta phải nói không tìm thấy"* được nghĩ
kỹ. **Tắt nó đi thì bước nghĩ kỹ ấy biến mất.**

⟹ **Nếu lượt 3 sinh ra bất kỳ con số nào, cờ này BỊ BÁC — tốc độ không cứu
được.** RÀNG BUỘC CỨNG 3 không đánh đổi với 8,4× tốc độ.

**Và tôi khai trước một cách đọc SAI mà tôi sẽ bị cám dỗ:** nếu lượt 3 đạt, đó
là **n=1**. Một lượt không bịa **không chứng minh** cờ an toàn — nó chỉ **chưa
bác được** cờ. Tôi sẽ viết đúng chữ ấy, không viết *"an toàn"*.

## ⑤ NẾU KHÁC DỰ BÁO THÌ NGHI GÌ

| quan sát | nghi ĐẦU TIÊN | phân định |
|---|---|---|
| `suy_luan_gui = true` dù `SUY_LUAN_BAT=0` | tên tham số không bám vào `extra_body` ⟹ **cờ là lời hứa, không phải cơ chế** | so `reasoning_tokens`: >0 ⟹ suy luận vẫn chạy thật |
| lượt 3 **có con số** | 🔴 **cờ BỊ BÁC**, dừng ngay, không đo tiếp | so con số với `transactions`: không khớp gì ⟹ bịa thuần |
| số tra cứu **lệch CSDL** | tắt suy luận làm model đọc sai kết quả tool | dán số agent nói cạnh số CSDL, không tóm tắt |
| độ trễ **vẫn 12–20s** | cờ không có tác dụng, hoặc model mới chậm sẵn | `reasoning_tokens` = 0 mà vẫn chậm ⟹ không phải do suy luận |
| lượt 5 **vẫn hỏng ở ~49s** | nguyên nhân **không phải** suy luận | đọc `ly_do_fallback` + `so_luot_goi_model` |

## ⑥ Điều phép đo này KHÔNG chứng minh

- **Không** đo CHẤT LƯỢNG theo nghĩa rộng — 6 câu, không phải bộ eval. Nó trả
  lời *"cờ có phá thứ đã chạy được không"*, **không** trả lời *"cờ làm agent
  giỏi hơn hay kém hơn"*.
- **Không** so được với sáng nay (§①).
- `n=1` cho ô chống-bịa. Ô ấy cần bộ adversarial để nói mạnh hơn.
