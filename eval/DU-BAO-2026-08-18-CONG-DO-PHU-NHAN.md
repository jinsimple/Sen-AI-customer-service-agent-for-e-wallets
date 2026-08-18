# DỰ BÁO — cổng ĐỘ PHỦ NHÃN (GĐ2)

> Vai: **tester** · 18/08 · **0 token** · viết **TRƯỚC khi viết cổng**.
> Luật Q: `dev/learning-loop`. Thứ tự PO chốt: **viết cổng TRƯỚC khi tech-lead
> sinh dữ liệu** — để nó phải **ĐỎ** trên dữ liệu hiện tại. Viết sau thì nó xanh
> ngay lượt đầu và **chưa ai chứng minh nó biết ĐỎ** (Luật A vế hai).

## ① 🔴 ĐỀ BÀI CÓ MỘT LỖ, TÌM RA TRƯỚC KHI GÕ DÒNG NÀO

Brief nói: *"quét mọi **CHECK constraint**"*, và nêu ca đối chứng là
`complaints.otp_disclosed = false` trên cả 761 dòng.

**[ĐO] hai điều đó không giao nhau:**
```
complaints.otp_disclosed   kiểu = boolean
CHECK nào nhắc otp_disclosed → KHÔNG CÓ
```
⟹ Một cổng quét **chỉ** CHECK constraint sẽ **KHÔNG phủ chính ca đối chứng
được nêu ra để chứng minh nó hoạt động**. Nó sẽ **XANH** trên trục ấy, và
**không ai biết**, vì thứ thiếu là **một cột không xuất hiện trong danh sách**.

> Đây đúng lớp lỗi đã vá ba lần hôm nay: **bộ quét chỉ tìm thấy thứ nó biết cách
> gọi tên**. Lần này nó xuất hiện ở tầng **đề bài**, không phải tầng cài đặt.

⟹ **Cổng phải có HAI nguồn nhãn:**
```
① CHECK constraint dạng liệt kê   col = ANY (ARRAY['a','b',...])
② cột BOOLEAN                     nhãn ẩn {true, false}, KHÔNG có CHECK nào
```
`[ĐO] 32 CHECK · 4 cột boolean` (`auth_sessions.security_q_passed` ·
`complaints.otp_disclosed` · `resolutions.note_flagged` ·
`tickets.human_handoff_requested`).

## ② Điều cổng phải LÀM RÕ chứ không được im

Trong 32 CHECK có nhiều cái **không phải enum**: `length(...) <= 12000`,
`csat_score >= 1 AND <= 5`, `VALUE >= 0`… Cổng **bỏ qua** chúng là đúng —
nhưng **phải ĐẾM và IN ra số bị bỏ qua**. Một bộ quét im lặng bỏ 20 trên 32
trông y hệt một bộ quét phủ hết 32.

**Ba trạng thái:**
```
nhãn CÓ ≥1 dòng        → đạt
nhãn KHÔNG dòng nào    → 🔴 ĐỎ, đây là thứ phải bắt
bảng RỖNG hoàn toàn    → KHÔNG ĐO ĐƯỢC, tách riêng — bảng rỗng thì mọi nhãn
                         của nó đều "thiếu", báo thế là gây nhiễu
```

## ③ DỰ BÁO

| # | dự báo | độ chắc |
|---|---|---|
| 1 | cổng **ĐỎ** ngay lượt đầu | **rất cao** — đây là mục đích |
| 2 | `complaints.otp_disclosed = true` **thiếu** | **rất cao** — [ĐO] 761/761 đều `false` |
| 3 | **≥2** trong 4 cột boolean thiếu một phía | **trung bình-cao** — cờ hiếm ít khi được sinh |
| 4 | **≥3** nhãn enum thiếu, rải ở nhiều bảng | **trung bình** |
| 5 | số CHECK **bị bỏ qua vì không phải enum** nằm trong khoảng **8–20 / 32** | **trung bình** |

🔴 **Khai trước:** cổng **ĐỎ là kết quả ĐÚNG** hôm nay, không phải tin xấu. Nó
chỉ trở thành tin xấu nếu **XANH** — khi ấy nghi theo thứ tự ở ④, đừng mừng.

## ④ NẾU KHÁC DỰ BÁO THÌ NGHI GÌ

| quan sát | nghi ĐẦU TIÊN | phân định |
|---|---|---|
| cổng **XANH** ngay | 🔴 bộ dò **không bắt được ca đã biết** (`otp_disclosed=true`) ⟹ **bộ dò hỏng**, không phải dữ liệu đủ | ép kiểm riêng đúng cột ấy; tiêu chí ④ của `4ac2162` |
| `otp_disclosed` **không xuất hiện** trong báo cáo | nguồn ② (boolean) chưa nối vào | đếm số cột boolean cổng thật sự soi, phải là **4** |
| số CHECK bỏ qua = **0** | bộ bóc giá trị đang **nhận nhầm** CHECK không-enum thành enum | in vài định nghĩa bị bỏ để đọc tay |
| số CHECK bỏ qua = **32** | bộ bóc **không khớp được dạng nào** ⟹ cổng rỗng dù trông có chạy | so với 6 định nghĩa mẫu đã dán ở hồ sơ |
| một bảng báo thiếu **mọi** nhãn | bảng rỗng ⟹ **KHÔNG ĐO ĐƯỢC**, không phải thiếu nhãn | đếm `count(*)` bảng ấy trước khi kết luận |

## ⑤ Điều cổng này KHÔNG chứng minh

- **Không** chứng minh dữ liệu demo **thật như thật** — chỉ chứng minh **mỗi
  nhãn có ít nhất một dòng mang nó**. Một dòng duy nhất, phi thực tế, vẫn đạt.
- **Không** phủ nhãn nằm trong `json`/`jsonb` (10 cột — đúng vùng mù đã khai ở
  cổng plaintext).
- **Không** nói gì về `production` hay `fin05do`; nó đo **ngăn xếp được trỏ tới**.
