# Khối "GIỚI HẠN PHẠM VI" — dán sẵn cho hồ sơ phát bắn heldout

> Vai: **security** · soạn 2026-08-17, **trước** khi phát bắn xảy ra.
> Lý do soạn trước: *con số sống lâu hơn ngữ cảnh sinh ra nó, và nó không tự
> mang theo phạm vi.* Để sẵn thì **lúc bắn không ai phải nhớ**.
>
> **Cách dùng:** chép nguyên khối trong khung dưới vào **chính file kết quả**
> phát bắn (không phải chỉ vào slide). Ba chỗ `⟨…⟩` điền lúc bắn.

---

## KHỐI DÁN — chép từ đây

```markdown
## ⚠️ GIỚI HẠN PHẠM VI CỦA CON SỐ NÀY — đọc trước khi trích dẫn

Con số dưới đây đo **năng lực của agent trên 60 kịch bản khiếu nại niêm phong**.
Nó **KHÔNG** phải điểm an toàn tổng thể, và **không** thay thế các bộ đo khác.

**Bốn điều con số này KHÔNG nói:**

1. **Không nói gì về ràng buộc cứng 4 (OTP).** Cả 60 ca đều `otp_disclosed=false`
   — heldout không chứa ca nào chạm đường lộ OTP. (Golden-set giữ 2 ca; đây là
   **chia có chủ đích giữa hai bộ**, không phải thiếu sót.)

2. **Không phủ hết bộ tín hiệu gian lận.** heldout gài **FS-03 · FS-06 · FS-09 ·
   FS-12**; golden-set gài **FS-01 · FS-02 · FS-04 · FS-05 · FS-07** — **không
   trùng một mã nào**. Con số này nói về 4 tín hiệu, không phải toàn bộ.

3. **Tương ứng giữa NHÃN và KỊCH BẢN chưa được kiểm.** Nhãn đã được rà đối chiếu
   `contracts/` + 5 ràng buộc cứng (security, `6170eca`) và **tự nhất quán**.
   Nhưng **không ai trong đội đọc trường `utterances`** — cố ý, để giữ tính độc
   lập của phát bắn. ⟹ một ca **nhãn đúng mà kịch bản viết lệch** sẽ **không**
   bị rà này bắt. Đây là **giới hạn đã biết, chấp nhận có ý thức**.

4. **⟨Trạng thái hiệu chuẩn trọng tài⟩** — điền lúc bắn:
   - kappa của `_llm_judge` so với nhãn người: **⟨…⟩**
   - tỉ lệ rộng-tay / chặt-tay đo riêng: **⟨…⟩**

   ⚠️ Nếu hai ô trên **chưa có số**: con số kết quả **chưa có khoảng tin cậy**,
   và **không được công bố ra ngoài đội** ở dạng một con số đơn. Sai số của
   thước chưa đo thì phép đo chưa hoàn chỉnh — đây là vấn đề **cách công bố**,
   không chỉ vấn đề đo lường.

**Ai đã soi bộ này:**
- **tester** — rà cơ học (khoá · kiểu · số đếm), **không đọc nội dung**
- **security** — rà nhãn đối chiếu `contracts/` + 5 ràng buộc cứng, **không đọc
  `utterances`** (`6170eca`)
- **⟨PO thật, nếu có⟩** — **một lần đọc thêm của người ngoài vai đo**.
  ⚠️ **KHÔNG** ghi là *"vai thứ tư kiểm độc lập"*: PO thật độc lập về **đo**
  (ngoài mọi vai đo lường) nhưng **không** độc lập về **động cơ** — họ là người
  trình con số này.

**Câu được phép nói:** *"agent đạt ⟨X⟩% trên bộ niêm phong 60 ca, đo ngày ⟨…⟩,
trong phạm vi nêu trên."*
**Câu KHÔNG được nói:** *"đã kiểm cả 5 ràng buộc cứng"* · *"agent an toàn ⟨X⟩%"*
· bất kỳ câu nào bỏ phần phạm vi.
```

## HẾT KHỐI DÁN

---

## Một câu cho tester (đúng thứ họ xin — không kèm nội dung ca)

> *"Con số này không nói gì về ràng buộc 4 (OTP) và chỉ phủ 4 trong bộ tín hiệu
> gian lận (FS-03/06/09/12); phần còn lại nằm ở golden-set."*

Dùng được ngay khi công bố, **không** lộ ca nào.

## Vì sao khối này nằm trong BẢN GHI, không phải slide

Slide có **người làm slide** đứng cạnh để giải thích. Bản ghi thì **người đọc
lại sáu tháng sau** mới là người cần — và lúc đó không ai đứng cạnh.

Tiền lệ trong chính dự án này: **`0/1814`**. Đó là một con số **đúng**, đo
**đúng quy trình**, và nó đã chống lưng cho một phán quyết **sai** suốt nhiều
vòng — chỉ vì phạm vi của nó (*corpus tiếng Việt, mẫu tiếng Anh*) **không được
ghi cạnh nó**. Con số không tự mang theo phạm vi; **người ghi phải gắn vào**.
