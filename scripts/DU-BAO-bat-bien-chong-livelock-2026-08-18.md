# DỰ BÁO — bất biến chống livelock, nửa (a). Công bố TRƯỚC khi chạm vật.

> Kỷ luật STATE §8: *công bố dự báo vào git TRƯỚC khi chạm vật*. Đã chạy 2 lần, trúng 6/6 và 2/2.
> File này viết **trước** khi sửa một dòng `src/` nào. Ai đọc sau: so cột **DỰ BÁO** với cột **THẬT**
> ở cuối file. Lệch ⟹ đọc bảng *"nếu khác thì nghi gì"*, **đừng** giải thích cho qua.

Người viết: tech-lead · 18/08/2026 · nền `HEAD=addec5e`, băm `src/` = `b8e7c5397457`

---

## 0. Khai trước — điều gì sẽ KHÔNG được tính là xác nhận

**Một kết quả thuận lợi ở đây KHÔNG xác nhận rằng livelock đã bị đóng trên lưu lượng thật.**
Nửa (a) là bất biến **tất định** ở tầng gọi tool; nó chỉ chứng minh được bằng test tất định.
Tần suất thật (`1/13`, mẫu nhỏ, STATE §6.⓶) **không đổi** vì bản vá này, và **không đo lại được**
khi chưa có hạn mức (A3). Cổng xanh ⟹ *"cơ chế bắn đúng trong ca dựng"*, **không** ⟹ *"đã hết
livelock"*.

---

## 1. Bất biến sẽ cài

> *"Cùng tool + cùng tham số + cùng lỗi ⟹ lần thứ hai là DỪNG."*

**Điểm chèn:** decorator `_locked` trong `build_customer_tools()`
(`src/agents/tools/customer_tools.py`). Chọn chỗ này vì nó là nơi **duy nhất** nhìn thấy đủ **ba**
thứ bất biến cần, trong **một** chỗ, cho **cả năm** tool:

| cần | `_locked` có? | vì sao |
|---|---|---|
| tên tool | ✅ | `functools.wraps` giữ `fn.__name__` |
| tham số | ✅ | `*args, **kwargs` của chính lời gọi |
| **lỗi** | ✅ | nó bọc **dưới** `@tool` ⟹ thấy **giá trị TRẢ VỀ** |

🔴 Vế thứ ba là vế quyết định chỗ chèn: cổng OTP **`return` một dict** `{"status":"error"}`,
**không `raise`** (`customer_tools.py:578-585`). Bất biến nào chỉ bắt exception sẽ **không thấy gì**
và livelock chạy y nguyên.

**Phạm vi đếm:** một `TurnGuard` — tức **một lượt chat**, đúng phạm vi livelock đã đo
(8 tool call **trong một lượt**). Không xuyên lượt, không xuyên thread.

## 2. Ranh giới CỐ Ý — nêu ra để người sau không tưởng là bỏ sót

- **Chỉ đếm `status == "error"`.** `not_found` / `multiple_matches` là **kết quả hợp lệ**, không
  phải lỗi. Lặp lại chúng cũng vô ích, nhưng nới bất biến sang đó là đổi hành vi ở nhánh mà
  **chưa ai đo**, và bất biến sẽ thôi tất định.
- **Chỉ nửa (a).** Không chạm câu nói với khách (nửa (b), đã có 12 ca mẫu, việc riêng).
- **Không đụng `_AGENT_RECURSION_LIMIT`.** Trần đó chặn cả vòng lặp **hợp lệ** (đã đo một lượt
  5 bước tra cứu bình thường). Đây là hai cơ chế khác trục, không thay nhau.
- **Không đụng contract.** Không thêm/bớt/đổi tên tool, không đổi lược đồ, không thêm route.
- **Không gộp 3 chú thích TPM.** Lý do gom chúng vào đợt này đã chết cùng đính chính §5.C1.

## 3. DỰ BÁO — điền TRƯỚC, không sửa sau

| # | vật | DỰ BÁO | THẬT |
|---|---|---|---|
| 1 | băm `src/` | **ĐỔI** khỏi `b8e7c5397457` (sửa ≥1 file `.py`) | *(điền sau)* |
| 2 | số file `src/` đổi | **1** — chỉ `customer_tools.py` | |
| 3 | `contracts/` | **0 file đổi** | |
| 4 | `check_contracts.py` | **sạch** — băm 3 contract KHÔNG đổi | |
| 5 | `test_invariants.py` | **23 passed** — không đổi số ca | |
| 6 | `docker diff` ba container | **0 · 0 · 0** (không dựng ảnh, không `docker cp`) | |
| 7 | `BUILD_COMMIT` ba container | **`bec7235`, KHÔNG đổi** | |
| 8 | nhãn băm trong ảnh | **`b8e7c5397457`, KHÔNG đổi** ⟹ **lệch× = 1·1·1** so cây | |
| 9 | ca đỏ "kho rỗng" | **VẪN ĐỎ** — bản vá này không liên quan | |
| 10 | token tiêu | **0** — bất biến tất định, không lượt LLM nào | |

🔴 **Dòng 8 là dòng dễ đọc nhầm nhất.** Sau khi tôi land, cây làm việc **cố ý lệch** khỏi ảnh
đang chạy, vì PO-agent đã ra lệnh **không dựng ảnh** cho tới khi tester land xong (`tests/` nằm
trong ảnh, dựng hai lần là hai lần rủi ro). **`lệch× = 1·1·1` ở giai đoạn này là ĐÚNG, không phải
sự cố.** Nó chỉ thành sự cố nếu còn lệch **sau** lần dựng chung.

## 4. Nếu khác thì nghi gì

| lệch | nghi |
|---|---|
| #1 băm **không** đổi | file chưa ghi thật (harness nuốt lỗi ghi) — `git diff --stat` trước khi tin bất cứ gì |
| #2 >1 file đổi | tôi sửa lan sang chỗ khác ngoài ý định, hoặc đụng việc dở của phiên khác trên **cây dùng chung** |
| #4 `check_contracts` bẩn | tôi đã chạm `contracts/` mà không nhận ra ⟹ **DỪNG**, đi đủ §10, không tự chữa |
| #5 ≠ 23 passed | 🔴 nghi **nặng nhất**. INV gọi thẳng `build_customer_tools()`; đổi chữ ký/hành vi tool là đổi thứ INV soi. Đọc **ca nào** đổi, đừng đọc màu |
| #5 xanh nhưng **số ca < 23** | `skip` và `pass` cùng màu trên bảng tổng (STATE §9) — đọc bằng **số ca chạy** |
| #6 ≠ 0 | tôi đã ghi vào container đang chạy — **Luật I**, hoàn nguyên rồi mới báo bất cứ số nào |
| #9 chuyển **XANH** | 🔴 **Luật J**. Bản vá của tôi không có đường nào chạm kho RAG. Nó xanh ⟹ có người khác vừa đổi thứ khác, **không phải** ⟹ tôi vá được nó |
| #10 ≠ 0 | có lượt LLM thật chạy ⟹ tìm xem lớp giữ hoá đơn nào thủng (STATE §3 đang là **HAI** lớp, không phải ba — cờ `.DANG-DONG-BANG-LLM` đang mất) |

## 5. Cách nghiệm thu — và vì sao đường xanh KHÔNG đủ

Luật A: cổng phải **IM** lúc bình thường **VÀ KÊU** lúc bất thường; nửa sau **chỉ chứng minh được
bằng ca đối chứng**. Nên nghiệm thu cần **cả hai** chiều:

```
KÊU    hai lời gọi giống hệt + cùng lỗi  ⟹  lời thứ hai trả CHỈ THỊ DỪNG, khác lời thứ nhất
IM     cùng tool, THAM SỐ KHÁC           ⟹  không bắn (vòng lặp tra cứu hợp lệ, 5 bước, đã đo)
IM     cùng tool, cùng tham số, THÀNH CÔNG ⟹ không bắn (không phải lỗi thì không đếm)
IM     lượt KHÁC                          ⟹ không bắn (sổ đếm chết theo lượt, không rò sang lượt sau)
```

Ba dòng `IM` quan trọng ngang dòng `KÊU`: một bất biến bắn cả vào vòng lặp hợp lệ sẽ bị gỡ trong
vòng một tuần, và lúc đó ta mất luôn dòng `KÊU`.

`tests/` là vùng **tester**. Tôi **không viết test**. Tôi soạn nội dung bốn ca trên để họ dán.

---

## 6. KẾT QUẢ THẬT — điền sau khi chạy, KHÔNG sửa mục 3

*(để trống tới khi đo xong)*
