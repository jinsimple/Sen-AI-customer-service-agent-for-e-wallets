# Khi nào ĐÁNG dựng lại một ngăn đang chạy — 2026-08-20

> Mặc định của hầu hết mọi người là *"có bản vá mới thì dựng lại cho mới"*.
> Mặc định đó sai đủ thường xuyên để đáng viết ra một quy trình thay thế.
> Ca cụ thể dùng làm ví dụ: ngăn `fin05` đang chạy ảnh băm nguồn
> `6722ab874767` (commit `cbeb02c`), trong khi cây làm việc đã ở
> `29b0496a4946` — chênh 6+ commit, một số là bản vá bảo mật/reliability
> thật. Quyết định cuối: **không dựng lại**. Ba câu dưới đây là lý do, viết
> thành quy trình để dùng lại lần sau, không riêng ca này.

## Ba câu phải trả lời TRƯỚC khi quyết — không câu nào bỏ được

### 1. Bản vá có TÁC DỤNG trên đúng ngăn này không, hay chỉ tác dụng trên giấy?

Đừng suy tác dụng của một bản vá từ **nội dung nó sửa** — suy từ **trạng thái
nơi nó sẽ chạy**. Một bản vá đổi *mặc định* (vd đảo `APP_ENV` mặc định
`"development"` → `"production"` khi thiếu biến) chỉ có tác dụng ở nơi biến
đó **đang thiếu**. [ĐO ca này]: `.env` thật của `fin05` đã có
`APP_ENV=development` tường minh từ trước — bản vá mặc định **vô hình** ở
đây, dù đọc diff thấy rất thuyết phục.

Cách kiểm rẻ nhất: hỏi thẳng biến/cấu hình thật đang chạy (`docker exec …
printenv`, không phải đọc lại `.env.example` hay code), TRƯỚC khi tính bản
vá đó vào cột "được".

### 2. Bản vá "đúng" có cứu được gì BÂY GIỜ không, hay chỉ cứu LẦN SAU?

Một bản vá có thể hoàn toàn đúng và vẫn không cứu được gì ở ngăn đang chạy,
vì điều kiện nó chặn **đã đi qua**. [ĐO ca này]: bản vá race condition
checkpointer (`docker-entrypoint.sh`) chặn lỗi xảy ra khi **DB khởi tạo từ
rỗng**. `fin05` đã init từ lâu — điều kiện kích hoạt bug đã trôi qua, bản vá
chỉ có tác dụng **phòng ngừa cho lần dựng lại DB rỗng tiếp theo** (vd sau
`down -v`, hoặc lần đầu deploy VPS), không cứu gì cho phiên đang chạy.

Phân biệt **"vá này tốt"** (đúng, nên giữ, nên áp dụng cho lần dựng sau) với
**"vá này giúp được ta bây giờ"** (đủ lý do để chịu downtime dựng lại NGAY) —
hai câu khác nhau, dễ gộp làm một nếu chỉ đọc changelog.

### 3. Chi phí downtime tính ở ĐƠN VỊ NGƯỜI DÙNG CẢM THẤY, không phải số phút trừu tượng

"1-2 phút downtime" là con số đúng nhưng vô cảm — nó không nói ai bị ảnh
hưởng và ảnh hưởng như thế nào. [ĐO ca này]: hội thoại khách đang dở **sống
sót** qua recreate container (checkpointer lưu ngoài process, thiết kế có
chủ đích từ ADR-014) — nhưng **WebSocket live-chat bị ngắt** trong lúc
container khởi động lại. Nếu đang có ai trong phiên live-chat lúc dựng lại,
người đó thấy kết nối rớt thật, không phải một con số trên báo cáo.

Viết chi phí dưới dạng: *"ai bị ảnh hưởng, họ thấy gì"*, không chỉ *"bao
nhiêu giây"*.

## Khuôn quyết định

```
Với MỖI bản vá trong danh sách "chênh lệch":
  ① có tác dụng ở TRẠNG THÁI THẬT của ngăn này không?     → không thì bỏ khỏi cột "được"
  ② có cứu được gì BÂY GIỜ, hay chỉ phòng ngừa lần sau?    → chỉ phòng ngừa thì hạ trọng số
  ③ downtime ảnh hưởng AI, họ THẤY GÌ?                     → viết cụ thể, không chỉ số phút

So tổng "được" (sau khi lọc qua ①②) với "mất" (theo ③) — quyết theo đó,
không theo phản xạ "có bản vá mới thì dựng lại".
```

**Khi nào NÊN dựng lại dù chi phí y hệt:** có bản vá đang cứu một sự cố THẬT
đang diễn ra (không phải phòng ngừa), hoặc chi phí downtime rơi vào lúc
không ai dùng (đêm khuya, ngoài giờ demo) — hai điều kiện đó đổi hướng cân
nhắc, không phải quy tắc cố định "luôn chờ".
