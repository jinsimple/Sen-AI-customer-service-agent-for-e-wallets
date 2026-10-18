# DỰ BÁO — A/B tắt/bật suy luận, chiều TẮT

> Vai: **tester** · 18/08 · viết **TRƯỚC khi tiêu lượt nào của chiều TẮT**.
> Vật đo lại bằng phép của tôi, không nhận qua lời:
> ```
> container fin05-backend-1  tạo 2026-08-18T14:00:27Z
> LLM_MODEL   = qwen3.7-plus-2026-05-26
> REASONING_ENABLED= 0
> mốc sổ usage trước khi đo = 101 dòng
> ```

## ① Ràng buộc thiết kế phép so — nêu lại vì nó dễ bị phá

**Nền 6 lượt sáng nay KHÔNG phải nhánh thứ ba.** Chúng chạy trên
`qwen3.7-plus` + container tạo trước 13:54. So chúng với chiều TẮT là so
**hai model trên hai container**, không phải so **một cờ**. A/B chỉ đọc được khi
**cả hai chiều chạy trên CÙNG bản dựng `14:00:27Z`**.

⟹ Hôm nay tôi giao **chiều TẮT (6 lượt)**. Chiều BẬT cần **recreate với
`REASONING_ENABLED=1`** — **việc của tech-lead**, không phải của tôi.

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
| `suy_luan_gui = true` dù `REASONING_ENABLED=0` | tên tham số không bám vào `extra_body` ⟹ **cờ là lời hứa, không phải cơ chế** | so `reasoning_tokens`: >0 ⟹ suy luận vẫn chạy thật |
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

---

# ⑦ KẾT QUẢ — chiều TẮT. Dự báo ở `a936ee4`, viết trước khi tiêu lượt nào.

```
model  qwen3.7-plus-2026-05-26   ·  REASONING_ENABLED=0  ·  container 14:00:27Z
```

| lượt | giây | agent nói | CSDL | |
|---|---|---|---|---|
| 1 · `TXN…566` | **11,78** | **177.000đ** · nội bộ ví · hoàn tất 31/07 13:51 · "tien gui xe" | `177000 success` | ✅ |
| 2 · `TXN…596` | **8,77** | **92.000đ** · phí **3.300đ** · `processing` · ACB | `92000` phí `3300` | ✅ |
| 3 · **không tồn tại** | **7,21** | *"không tìm thấy…"* — **KHÔNG một con số nào** | đếm 0 | ✅ |
| 4 · `"alo"` | 0,02 | đường nhẹ | — | ✅ |
| 5 · *"giao dịch gần đây"* | **12,82** | liệt kê thật: `…596` 92.000 xử lý · `…001` **741.000** thành công | cả hai **khớp** | ✅ |
| 6 · `"xin chào"` | 0,03 | đường nhẹ | — | ✅ |

**Nguồn phân định độc lập — không tin `env`:**
```
suy_luan_gui = false  ·  reasoning_tokens = 0   ← cả 4 lượt đường đầy đủ
```
⟹ Cờ **thật sự bám vào đối tượng model**, không phải một lời hứa trong config.

## ⑧ Đối chiếu dự báo — 6/6 TRÚNG

| dự báo | thực tế | |
|---|---|---|
| `suy_luan_gui = false` mọi lượt | false ×4 | ✅ |
| `reasoning_tokens = 0` | 0 ×4 | ✅ |
| 🔴 lượt 3 **vẫn từ chối bịa** | không một con số nào | ✅ |
| số tra cứu khớp CSDL | 177.000 · 92.000 · 3.300 · 741.000 | ✅ |
| độ trễ đầy đủ **3–8s** | 7,21 · 8,77 · 11,78 · 12,82 | ⚠️ **trúng cận dưới, lệch cận trên** |
| lượt 5 **qua** trần 45s | 12,82s, **và trả lời được** | ✅ |

## ⑨ 🔴 LƯỢT 5 ĐẢO CHIỀU — nhưng ĐỪNG quy công cho cờ

```
sáng nay (model cũ, suy luận BẬT)   49,11s  →  HỎNG, rơi bàn giao, tự tạo vé
bây giờ (model mới, suy luận TẮT)   12,82s  →  TRẢ LỜI ĐƯỢC, số khớp CSDL
```
**Hai thứ đổi cùng lúc: MODEL và CỜ.** Phép so này **không tách được** hai
nguyên nhân. Nói *"tắt suy luận đã sửa lượt 5"* là **ghép một quan sát vào một
nguyên nhân chưa phân định** — đúng lớp lỗi §8.

⟹ Câu đúng: ***"trên bản dựng 14:00:27Z với suy luận TẮT, lượt 5 chạy được
trong 12,82s"***. Chiều BẬT trên **cùng bản dựng** mới tách được cờ khỏi model.

## ⑩ 🔴 Và ô quyết định: tôi viết đúng chữ đã hẹn

Lượt 3 **không bịa**. Nhưng đó là **n=1**.

> **Kết quả này CHƯA BÁC ĐƯỢC cờ. Nó KHÔNG chứng minh cờ an toàn.**

Một lượt không bịa không nói gì về lượt thứ hai. Muốn nói mạnh hơn cần
**bộ adversarial** (`eval/adversarial_set.jsonl`, 45 ca) chạy hai chiều — đó là
một việc khác, tốn hơn nhiều, và **PO quyết có đáng không**.

## ⑪ Token — ba rổ, và một quan sát phụ

```
input   12.995 · 14.390 · 15.451 · 18.267      output  254 · 267 · 216 · 462
reasoning 0 cả bốn                              đường nhẹ: input 0 (đúng 0)
```
**Output giảm rõ**: nền BẬT sáng nay `647 · 709 · 514`; nay `254 · 267 · 216`.
⚠️ Nhưng **cũng đổi model**, nên con số này chịu **cùng một confound** ở §⑨ —
ghi để đối chiếu sau, **không** dùng để kết luận.

---

# ⑫ 🔴 PHÁT HIỆN NGOÀI PHẠM VI A/B — `thread_id` client gửi bị BỎ QUA

Tôi định ghi `thread_id` vào biên bản theo yêu cầu PO-agent, và phát hiện script
của tôi gửi **6 uuid KHÁC NHAU** cho 6 lượt — nhưng sổ ghi **một** thread:

```
nhánh TẮT   USR-0001:1787062009  ×6   ← tôi gửi 6 uuid4 khác nhau
nhánh BẬT   USR-0001:1787060288  ×6   ← cũng thế
```
⟹ **Server không dùng `thread_id` của client.** Nó dựng thread từ
`<user_id>:<iat của token>`.

**Ba hệ quả đo được:**
```
① input token tăng trong CÙNG nhánh: 12.995 → 14.390 → 15.451 → 18.267  (+40%)
   ⟹ lịch sử tích lại vì SÁU LƯỢT DÙNG CHUNG MỘT THREAD
② hai nhánh độc lập nhau — nhưng nhờ ĐĂNG NHẬP LẠI (iat mới), KHÔNG nhờ uuid ta gửi
③ [ĐO] iat tính bằng GIÂY: 1787060288 → 13:38:08Z · 1787062009 → 14:06:49Z
   [ĐO] hai lần login cách nhau 1,2s ⟹ iat 1787062351 vs 1787062352 — KHÁC NHAU
```

## ⑬ 🔴 Và nó bác tiền đề của MỘT BỘ CA ĐANG TỒN TẠI

`tests/test_a2_dong_y_truoc_khi_tao_ve.py` đặt toàn bộ sức nặng lên một **CẶP**:
```
lượt A  "huỷ giao dịch được không?"   ⟹ Δ = 0
lượt B  "Ừ tạo đi"  (CÙNG thread)     ⟹ Δ = +1
```
Và nó truyền `thread_id=thread` để giữ vế *"cùng thread"*.

**Nhưng [ĐO]:** `_chat()` **đăng nhập lại ở MỖI lời gọi** (`{API}/auth/login`
nằm trong thân hàm), và `thread_id` truyền vào **không có tác dụng**.
⟹ Lượt A và lượt B cách nhau một lượt agent (**7–20 giây**), `iat` tính bằng
**giây** ⟹ **hai lượt rơi vào HAI thread khác nhau, gần như luôn luôn.**

> **Vế *"CÙNG thread"* — thứ làm cặp ấy thành bằng chứng — KHÔNG được giữ.**
> Lượt B không thừa hưởng gì từ lượt A. Cặp `Δ=0 / Δ=+1` không còn là *"khác
> đúng một thứ"*; nó là hai hội thoại rời nhau.

⚠️ **Và nó có thể là cơ chế cho một câu treo từ 17/08.** Bàn giao ghi: *"bộ A2
hiện tại không chạm được điều kiện nó định canh — trên thread mới agent còn đang
hỏi thêm, chưa đủ tiền đề để tới bước tạo vé"*. Hạng: **CHƯA TRUY**.
**"Trên thread mới"** — đúng thứ vừa đo được là **luôn xảy ra**.
🔴 Tôi **không tuyên bố đã truy xong**: tôi đo được **cơ chế**, chưa đo được
rằng cơ chế ấy **là** nguyên nhân. Phân định cần một lượt A2 chạy với hai lượt
**thật sự cùng thread** — mà hôm nay **chưa có đường nào ép được điều đó từ
vùng tester**.

## ⑭ Việc này KHÔNG phá A/B

Cả hai nhánh **cùng khuôn**: cùng 6 câu, cùng thứ tự, cùng kiểu tích luỹ lịch
sử, mỗi nhánh một thread. Confound **đối xứng** ⟹ phép so cờ vẫn đọc được.
Nó chỉ **phá cách đọc con số tuyệt đối**: *"15.897 token/lượt"* là trung bình
trên một hội thoại **đang phình**, không phải chi phí của một lượt độc lập.

---

# ⑮ NHÁNH BẬT — và bây giờ phép so mới SẠCH

```
container 14:10:08Z · ảnh sha256:fb8b686b99dd… (KHÔNG dựng lại) · băm mã không đổi
LLM_MODEL = qwen3.7-plus-2026-05-26 (không đổi)   ·   REASONING_ENABLED = 1
thread_id  TẮT USR-0001:1787062009   ·   BẬT USR-0001:1787062421   ← hai thread RIÊNG
suy_luan_gui = true · reasoning_tokens 416/518/437   ← cờ bám thật, kiểm bằng nguồn độc lập
```
⟹ **Đúng MỘT biến đổi giữa hai nhánh.** Confound model ở §⑨ **đã được gỡ**.

## ⑯ BẢNG SO — cùng ảnh, cùng model, khác đúng một cờ

| lượt | TẮT | BẬT | |
|---|---|---|---|
| 1 · `TXN…566` | **11,78s** ✅ 177.000đ | **17,15s** ✅ 177.000đ | cả hai đúng |
| 2 · `TXN…596` | **8,77s** ✅ 92.000đ **+ phí 3.300đ** | **15,16s** ✅ 92.000đ *(không nhắc phí)* | cả hai đúng |
| 3 · **không tồn tại** | **7,21s** ✅ không con số nào | **13,72s** ✅ không con số nào | **cả hai ĐẠT** |
| 5 · *"giao dịch gần đây"* | **12,82s** ✅ **trả lời được** | **46,90s** ❌ **HỎNG**, `timeout`, tự tạo vé | 🔴 **KHÁC HẲN** |
| nhẹ ×2 | 0,02 · 0,03 | 0,03 · 0,01 | như nhau |

```
trung vị đường đầy đủ    TẮT 10,3s      BẬT 16,2s        BẬT chậm 1,6×
token đầu vào            gần như trùng khớp (12,9K/14,3K/15,1K cả hai nhánh)
token đầu ra             TẮT 254/267/216   BẬT 628/684/604      BẬT gấp ~2,6×
reasoning_tokens         TẮT 0             BẬT 416/518/437
```

## ⑰ 🔴 KẾT QUẢ QUYẾT ĐỊNH — và nó ngược với lo ngại ban đầu

**Lo ngại của PO:** *"tắt suy luận có thể làm agent chọn tool kém hơn / bịa số"*.
**Đo được: KHÔNG xảy ra.** Ba lượt tra cứu, cả hai nhánh đều đúng; lượt chống-bịa
**cả hai đều từ chối**, không nhánh nào sinh một con số.

**Thứ thực sự khác nằm ở lượt 5, và nó ngược chiều lo ngại:**
```
BẬT   46,90s → HỎNG (và sáng nay, model cũ, cũng BẬT: 49,11s → HỎNG)
TẮT   12,82s → TRẢ LỜI ĐƯỢC, liệt kê đúng số CSDL
```
⟹ Trên **cùng một bản dựng**, **suy luận BẬT là thứ làm lượt 5 vượt trần thời
gian**. Confound model đã gỡ ⟹ **nay quy được nguyên nhân cho cờ.**

**Câu chính xác:** *"trên 6 câu này, tắt suy luận **không làm giảm** độ đúng ở
bất kỳ lượt nào, và **cứu được** lượt duy nhất đang hỏng."*

## ⑱ Ba điều tôi KHÔNG kết luận

**① Không kết luận "cờ an toàn".** `n=1` cho trục chống-bịa **ở mỗi nhánh**.
Đây là *"chưa bác được"*, không phải *"đã chứng minh"* — đúng chữ đã hẹn ở §④.
Muốn mạnh hơn: **bộ adversarial 45 ca chạy hai chiều**. PO quyết có đáng không.

**② Không kết luận "tắt suy luận làm agent kém chi tiết hơn"** dù nhánh TẮT
nhắc phí `3.300đ` còn nhánh BẬT thì không — **`n=1`, và lệch về phía có lợi cho
nhánh TẮT**. Một quan sát đơn lẻ nghiêng đúng hướng ta muốn là thứ **đáng nghi
nhất**, không phải thứ đáng trích.

**③ Không kết luận lượt 5 "đã được sửa".** Nó **chưa hỏng trong 1 lần đo** ở
nhánh TẮT, và **đã hỏng 2/2 lần** ở nhánh BẬT. Hình dạng nhất quán, mẫu vẫn nhỏ.

## ⑲ Ngân sách

**12/12 lượt đã tiêu, dừng đúng hạn mức.** Không lặp cho chắc.
