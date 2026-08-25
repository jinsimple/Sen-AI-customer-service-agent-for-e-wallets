# DỰ THẢO ADR-051 — `create_ticket` hai thì · CHỜ PO THẬT DUYỆT

> 🔴 **CHƯA DUYỆT, CHƯA THI HÀNH.** Đặt ở `docs/nhat-ky/` chứ không ở `docs/DECISIONS.md` là có
> chủ đích: `DECISIONS.md` chỉ ghi thứ **đã quyết**. Ai đọc tệp này mà thi hành theo là sai.
>
> Đổi **chữ ký tool** ⟹ chạm `contracts/agent-tools.yaml` ⟹ phải đi **đủ vòng `CLAUDE.md §3`**:
> sửa contract → ADR → **PO duyệt** → `check_contracts --update` → commit kèm baseline → rồi code.

---

## Vấn đề

Hạng mục ⑩ *(phiếu K4)*: khách phải **thấy và đồng ý** bản tóm tắt 6 trường **trước khi** vé được
tạo. Hôm nay vé được tạo **rồi mới** báo lại — khách không có cơ hội sửa trước khi hồ sơ thành
hình.

**Hai cách đọc phiếu, cả hai đều hỏng — và đó là dấu hiệu đề bài bị đóng khung sai:**

| | | |
|---|---|---|
| **Đọc A** | sửa prompt: thay 4 trường bằng 6, vẫn để model viết | 🔴 **BÁC.** Đây đúng là **vòng vá prompt thứ 7**, mà `ADR-049` kết luận đòn bẩy ấy **sai** sau khi A2 đỏ **6 vòng liên tiếp**. Land nó trong cùng repo chứa ADR-049 thì **hoặc ADR-049 sai, hoặc bản vá sai** |
| **Đọc B** | dựng trong mã | 🔴 Coder đo: **bất khả** — *"trước lời gọi `create_ticket`, tầng code không có trường nào"* |

**Đọc B sai ở kết luận, không sai ở tiền đề.** Sáu trường ấy **chính là tham số** model buộc phải
truyền vào `create_ticket`. Vấn đề không phải *thiếu dữ liệu* mà là **ranh giới đặt sai chỗ**.

---

## Quyết định đề xuất — Đọc C

```
thì 1   create_ticket(..., xac_nhan=False)
        → KHÔNG tạo hồ sơ nghiệp vụ nào
        → trả bản tóm tắt 6 trường DỰNG TRONG MÃ từ chính tham số vừa nhận
        → return_direct ⟹ THOÁT NGAY, không vòng gọi model thứ hai

thì 2   create_ticket(..., xac_nhan=True)   ← chỉ sau khi khách gật
        → tạo thật
```

Bản tóm tắt do **mã** dựng ⟹ tất định, không bịa được, không trôi theo prompt. Và nó **siết ràng
buộc cứng 1 (HITL) chặt hơn hiện tại**: không gì thành hình trước khi khách gật.

---

## Sáu ràng buộc kỹ thuật — thiếu bất kỳ cái nào là hỏng

| # | ràng buộc | nếu thiếu |
|---|---|---|
| 1–4 | bốn ràng buộc Coder ghi tại `655a112` | — |
| **5** | `xac_nhan=True` **chỉ nhận** khi có tín hiệu *"đã gửi tóm tắt khớp đúng 6 trường này"* ở lượt trước — khuôn `thread_signals` *(⑨/T0)*, **băm 6 trường** làm giá trị, **tự xoá sau khi dùng** | 🔴 model gọi thẳng `xac_nhan=True` ngay lượt đầu ⟹ **đi vòng qua toàn bộ giá trị HITL**. `TurnGuard` **KHÔNG cứu được**: [ĐO] nó tạo mới **mỗi lượt**, mà hai thì là **hai lượt chat** — nó không có khái niệm *"lượt trước"*. Cùng sửa này đóng luôn nhánh **"khách gật hai lần"** |
| **6** | `create_ticket` đổi return type **`dict` → CHUỖI ĐÃ ĐỊNH DẠNG**, cho **cả hai thì** | 🔴 `return_direct` phát **thẳng** giá trị trả về làm câu trả lời ⟹ **khách nhận JSON thô**. Hỏng **ở phía khách hàng**, không ở test — đây là thứ người thi hành sau đâm vào đầu tiên |

✅ **Không vỡ gì khác** — [ĐO] `tool_calls_out` · `ticket_id` · ⑧ · ⑨ · `investigation_logs` đều đọc
từ **state** do `agent.invoke()` trả về. `exit_node` chỉ tắt **vòng gọi model thứ hai**, **không
xoá `ToolMessage`** đã sinh. Vòng quét ở `graph.py:1789` vẫn thấy đủ lời gọi + kết quả.

---

## Chi phí — số THẬT, và chỗ còn là ước lượng

**Giá một lời gọi tool, đo từ sổ sống:**
```
0 tool → 10.381 token (n=8)   ·   1 tool → 20.811 (n=4)   ·   3 tool → 41.444 (n=1)
     ⟹ mỗi lời gọi tool ≈ +10.400 token, tuyến tính khít
     (bất biến: so_luot_goi_model = so_tool_call + 1, khít 100% trên hai ngăn độc lập)
```
Tiền **không** nằm ở lược đồ tool — nằm ở **vòng gửi lại toàn bộ ngữ cảnh**.

**Với `return_direct` áp tĩnh cho cả hai thì:**
```
đường cơ sở (tạo vé HÔM NAY, đang chạy)  ≈ 20.811
Đọc C  lượt 1 ≈ 10,4k  ·  lượt 2 ≈ 10,4k + Δlịch sử
                                    TỔNG ≈ 20,8k + Δlịch sử
```
⟹ **≈ NGANG GIÁ.** ⚠️ **`Δlịch sử` là ƯỚC LƯỢNG (~300–500 token, tức ~1–2%), CHƯA ĐO.** Coder đo
được rẻ bằng cách so `input_chars` giữa lượt đầu và lượt hai cùng nội dung.

🔴 **Hai chữ "delta" KHÁC LOẠI, đừng lẫn:** trần **261** của điều khoản **T2** canh **phình
prompt** = chi phí **CỐ ĐỊNH mọi lượt**. Con số ở đây là chi phí **BIÊN theo sự kiện** — chỉ trả
khi thật sự tạo vé. **261 không liên quan tới nó.**

---

## 🔴 Giới hạn ĐÃ BIẾT — khai ra, không giấu

`return_direct` đặt trên **định nghĩa tool** ⟹ áp cho **MỌI** lời gọi `create_ticket`, **vĩnh
viễn**. Nghĩa là model **mất khả năng** ghép thêm câu trả lời cho một **câu hỏi phụ** khách hỏi
**cùng lượt** với việc tạo vé *(vd vừa đủ 6 trường vừa hỏi "vậy tôi có mất phí không")*. Model
phải chọn **một**: gọi tool *(không trả lời được câu phụ)* hoặc trả lời câu phụ trước *(trễ vé)*.

**Đường tránh đã thử và ĐÃ CHẾT** — tách thì 1 thành tool riêng mang cờ, để `create_ticket` sạch:
```
[ĐO] docstring 4 tool đang chạy:  search_policy 793 · get_customer_history 947
                                  request_human_handoff 1.176 · create_ticket 1.368  (ký tự)
[ĐO] tỉ lệ THẬT của hệ thống:  input_chars / input_tokens ≈ 1,7–1,8
     (KHÁC quy ước "4 ký tự/token" tiếng Anh — tiếng Việt có dấu + JSON overhead tốn hơn)
⟹ trần 261 token ≈ ~457 ký tự ngân sách
⟹ ngay cả tool NGẮN NHẤT đang chạy (793 ký tự) đã VƯỢT ~1,7 LẦN, một mình nó
```
Và tool mới cần liệt kê **đúng enum hợp lệ** *(chính lý do khiến `create_ticket` dài 1.368)*. Ép
viết cực ngắn để lọt = **bỏ phần enum** ⟹ model tự đoán giá trị sai ⟹ **đổi rủi ro ngân sách lấy
rủi ro chất lượng dữ liệu — đúng loại lỗi ⑩ sinh ra để chữa.**

⚠️ Và tách tool chỉ né được **nửa** đánh đổi, **đúng nửa ít quan trọng hơn**: thì 1 *(khách vừa kể
xong sự việc)* **hay có câu hỏi phụ**; thì 2 *(“ừ tạo đi”)* **hiếm khi có**.

---

## 🔴 Dữ kiện còn VẮNG — PO cần biết trước khi quyết

Mục tiêu gốc của ⑩ là **giảm tạo vé sai**, **không** phải giảm token. Vậy phép so đúng **không**
phải `20,8k vs 20,8k`, mà là:

> **`20,8k + Δ` đảm bảo** ⟶ **vs** ⟵ **`20,8k` + (X% × chi phí sửa sai)**

**Không ai có `X`.** Chi phí sửa sai *(CSKH sửa tay · khách khiếu nại lần hai)* **có thật nhưng
không nằm trong `usage.jsonl`.**

⚠️ **PO không cần chờ `X` để quyết** — vì chi phí đã **ngang giá**, câu hỏi rút gọn thành:

> **Đổi một GIỚI HẠN HÀNH VI đã biết *(không trả lời được câu hỏi phụ cùng lượt tạo vé)* lấy một
> ràng buộc HITL chặt hơn *(khách thấy và duyệt trước khi hồ sơ thành hình)* — có đáng không?**

Đó là câu **nghiệp vụ**, và đội **không được tự trả lời thay**.

---

## Truy vết — và ba lần PO bị bác

| | |
|---|---|
| Đề xuất Đọc C | PO `p-226-b9` |
| Bác Đọc A | PO — mâu thuẫn `ADR-049` |
| Đánh đối kháng | Review `p-226-cb`, **trước** khi trình PO thật |
| Ràng buộc kỹ thuật 1–4 | Coder `p-226-63`, `655a112` |
| Ràng buộc 5, 6 · giới hạn hành vi · giết đường thứ ba | Review |

🔴 **PO sai ba lần trong chính hạng mục này, cả ba do Review bắt:**
1. tuyên bố `delta ≈ 0` — **không đo**. Thật ra một lời gọi tool **= 10.400 token**.
2. ví thì 1 với khuôn ⑫b *(`model=None`)* — **SAI KHUÔN**: ⑫b dừng **trước khi** gọi model, thì 1
   **buộc** phải chạy một vòng.
3. đề xuất đổi đường cơ sở sang một thiết kế **không ai đang đề xuất** — **đúng cái lỗi "so sai
   đường cơ sở" mà chính PO vừa cảnh báo Review một tin nhắn trước đó.**

*Ghi ra vì bản ADR này chỉ đáng tin ở mức nó đã bị đánh — và nó bị đánh ba lần rồi mới tới đây.*
