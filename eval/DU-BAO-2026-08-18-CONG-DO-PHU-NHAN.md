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

---

# ⑥ KẾT QUẢ — dự báo ở `4103aa4`, viết trước khi gõ dòng nào. **5/5 TRÚNG.**

```
🔴 20 NHÃN KHÔNG CÓ DÒNG NÀO MANG NÓ
nguồn ①  20 cột enum bóc từ CHECK  ·  10 CHECK BỊ BỎ QUA vì không phải liệt kê
nguồn ②  4 cột boolean
bảng rỗng: —
```

| # | dự báo | thực tế | |
|---|---|---|---|
| 1 | cổng ĐỎ | ĐỎ, 20 nhãn | ✅ |
| 2 | `otp_disclosed = true` thiếu | **thiếu** | ✅ |
| 3 | ≥2/4 boolean thiếu một phía | **2** (`otp_disclosed` · `note_flagged`) | ✅ |
| 4 | ≥3 nhãn enum thiếu | **18** | ✅ |
| 5 | 8–20 / 32 CHECK bị bỏ qua | **10** | ✅ |

## ⑦ Luật J — cổng khẳng định CÁI GÌ. Đối chiếu thật, không tin cổng.

```
messages.role              staff 237 · customer 230        → agent 0 · system 0
resolutions.status         approved 8 · pending 3 · rejected 1   → draft 0
resolutions.reject_reason  (NULL) 11 · khac 1              → 6 giá trị taxonomy = 0
chat_sessions.status       closed 161                      → waiting 0 · active 0
```
Cổng nói đúng từng dòng.

## ⑧ 🔴 HAI PHÁT HIỆN LỚN HƠN `otp_disclosed`

**① Toàn bộ taxonomy lý do từ chối CHƯA TỪNG CÓ MỘT DÒNG NÀO.**
```
sai_so_lieu · sai_phan_loai · thieu_can_cu · sai_chinh_sach · trung_case · khach_rut
                                                                  ⟹ 0 dòng, cả sáu
đúng MỘT lần từ chối từng xảy ra, và nó dùng ô gộp `khac`
```
ADR-019 dựng taxonomy này **để nuôi vòng học Phase 2**. Vòng học ấy hôm nay
**không có tín hiệu nào** — không phải "ít dữ liệu", mà **rỗng**, và ca duy nhất
có thì rơi vào ô *"khác"*, tức ô **không dạy được gì**.
> Và ràng buộc `note` bắt buộc khi `reject_reason='khac'` (ADR-024/INV-17) —
> nhánh **duy nhất từng bắn** lại đúng là nhánh ngoại lệ.

**② `messages.role = agent` chưa từng có dòng nào**, trên 467 tin.
`staff 237 · customer 230` — **lời của chính agent không nằm trong bảng
`messages`**. Hoặc nó ghi ở nơi khác, hoặc giá trị `agent` trong constraint là
**nhãn chết**. Cần `src/` để trả lời ⟹ **không phải việc của tester**, chuyển
tech-lead. Nhưng nó chạm một thứ đo được: mọi thống kê đếm "tin của agent" từ
bảng này **đang trả về 0** và **không ai kêu**.

## ⑨ Vì sao đề bài suýt bỏ sót đúng ca đối chứng của chính nó

`complaints.otp_disclosed` là **boolean, không CHECK nào** ⟹ nguồn ① mù hoàn
toàn. Nếu tôi làm đúng chữ *"quét mọi CHECK constraint"*, cổng vẫn **ĐỎ 18 nhãn**
— trông rất thuyết phục — trong khi **im lặng ở đúng cột được nêu ra để chứng
minh nó hoạt động**. Và không ai kiểm lại, vì cổng đã đỏ rồi.

> **Một cổng đỏ vì 18 lý do đúng vẫn có thể mù ở lý do thứ 19** — và cái đỏ ấy
> làm người ta **thôi nghi ngờ**. Đây là mặt trái của Luật A: nửa "biết kêu"
> được chứng minh **không** kéo theo "kêu đủ chỗ".

---

# ⑩ VÒNG HAI — dữ liệu demo + DANH SÁCH MIỄN TRỪ

```
20 nhãn thiếu  →  sau khi tech-lead sinh dữ liệu (b0865e2)  →  11
               →  sau khi khai 4 miễn trừ                    →  7 ĐỎ · 4 📋
```

## Bốn khai, hai LOẠI — và loại không phải trang trí

```
nhan_chet      messages.role = agent · system
ngoai_pham_vi  resolutions.reject_reason = trung_case · khach_rut
```
Hai loại đòi **hai hành động khác hẳn**: `nhan_chet` ⟹ sửa **CONTRACT** (constraint
cho phép một giá trị **sản phẩm không tạo được**); `ngoai_pham_vi` ⟹ **sinh dữ
liệu**, khi PO mở rộng phạm vi. Gộp chúng vào một rổ *"đã khai"* là mất đúng
thông tin dùng để hành động.

**`messages.role` — [ĐO] của tech-lead khép câu hỏi:** `Message(...)` tạo ở
**đúng một nơi** (`live_chat.record_message` ← `live_chat_ws.py:578`) với
`role = "staff" if is_staff else "customer"`. **Không đường mã nào ghi được
`agent`.** ⟹ `messages` là **biên bản LIVE-CHAT khách↔người thật**, không phải
"lịch sử hội thoại" nói chung.
> ⭐ Bản đầu script demo của tech-lead có **12 dòng `role="agent"`** — họ tự gỡ.
> Nếu lằn ranh ấy không được giữ, **cổng đã XANH trên một điều không đúng**, và
> dữ liệu demo đã dạy sai hình dạng của bảng cho mọi người đọc sau.
> [ĐO] sau khi sinh: `staff 253 · customer 242`, **0 dòng `agent`**. Giữ được.

## ⑪ Phép bắt KHAI THỪA — thứ brief không đòi, và là thứ giữ cho danh sách không mục

Cổng còn kiểm chiều **ngược**: một nhãn **nay đã CÓ dòng** mà khai miễn trừ
**vẫn còn** ⟹ **ĐỎ**, đòi gỡ khai.

Không có nó thì danh sách miễn trừ **mục dần**: mỗi khai sống lâu hơn lý do của
nó, và người sau đọc một danh sách **toàn thứ không còn đúng** — rồi tin nó.
Đây là **Luật P ở dạng artefact tự làm cũ mà không ai niêm**, lần này **bịt bằng
cơ chế** thay vì bằng lời dặn.

**Đột biến xác nhận:** khai miễn trừ cho `messages.role = customer` (nhãn có
**242 dòng**) ⟹
```
🔴 MIỄN TRỪ KHAI THỪA — nhãn nay đã có dòng, khai không còn đúng:
    messages.role = customer  ← nay CÓ dòng, GỠ khai đi
hoàn nguyên: băm khớp lại ef8948aa3bd4
```

## ⑫ Bảy nhãn còn ĐỎ — KHÔNG khai, cố ý

```
chat_sessions.status = waiting          escalations.target = authority
policy_documents.status = processing    policy_documents.status = failed
resolutions.action_type = no_action     resolutions.note_flagged = true
wallets.status = closed
```
PO **chưa cấp miễn trừ** cho nhóm này ⟹ chúng ở lại màu đỏ. Đó **chính là thiết
kế**: miễn trừ là **hành vi có chủ đích**, không phải mặc định. Ai muốn tắt một
dòng đỏ ở đây phải **viết ra lý do** và ký tên vào đó.
