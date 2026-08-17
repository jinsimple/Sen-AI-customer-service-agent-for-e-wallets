# Định nghĩa cổng ĐC-1..5 cho lớp phân luồng — nguồn chuẩn

> PO-agent viết 17/08/2026 theo yêu cầu của tester: ba trong năm điều kiện cổng
> (ĐC-1/3/4) chỉ tồn tại trong tin nhắn — *"một cổng có mục do người viết cổng
> tự nghĩ ra là cổng đo Ý KIẾN của người đó"*. File này là nguồn chuẩn; tin
> nhắn không phải nguồn.
>
> Gốc thiết kế: coder đề xuất ĐC-1..5 trong phiên 17/08, PO-agent duyệt từng
> mục. Đây là bản chép lại có ràng buộc, không phải thiết kế mới.

## Năm điều kiện — cổng `eval/cong_phan_luong.py` phải kiểm đủ

| # | điều kiện | đo mệnh đề gì |
|---|---|---|
| **ĐC-1** | Một câu xã giao thuần (kiểu `"alo"`) **phải đi ĐƯỜNG NHẸ** | cổng **có hoạt động không** — vế "kêu thật lúc bất thường" của Luật A. Không có ĐC-1, một router trả `day_du` cho mọi thứ vẫn qua hết các cổng còn lại |
| **ĐC-2** | Phân loại theo **TỪNG LƯỢT**, không theo phiên: `"alo"` rồi câu SAU kể mất tiền ⟹ câu sau **phải đi ĐẦY ĐỦ** | router không được nhớ *"phiên này đơn giản"* — ca do PO thật nêu |
| **ĐC-3** | Lớp phân loại **NÉM LỖI / timeout / bất kỳ ngoại lệ nào** ⟹ lượt đó đi **ĐẦY ĐỦ**, không chặn khách | hướng-sai-an-toàn: fail-open **về phía đắt tiền**. Lỗi hạ tầng của lớp tiết kiệm không bao giờ được thành lỗi của khách |
| **ĐC-4** | Câu **lạ / không rõ / ngưỡng không phân định được** ⟹ **ĐẦY ĐỦ** | đường nhẹ chỉ mở khi **KHẲNG ĐỊNH** được là đơn — mọi trạng thái không-khẳng-định-được đều là `day_du`. Cùng khuôn `DIALABLE` |
| **ĐC-5** | **Mọi câu** của bộ âm (`golden_set`, đếm theo **CÂU** — 124, không phải 120 ca) đi **ĐẦY ĐỦ** | chiều bỏ-sót: một khiếu nại thật bị gán "đơn" = một khách bị bỏ rơi |

## Ràng buộc đọc kết quả

1. **ĐC-1 và ĐC-5 chỉ có nghĩa khi đứng CÙNG NHAU** — ĐC-5 một mình thì router
   không-làm-gì đạt tuyệt đối; ĐC-1 một mình thì router cho-tất-qua đạt tuyệt đối.
2. Mỗi lần **đổi ngưỡng / đổi luật** ⟹ chạy lại **cả năm**, trên băm mới, công
   bố băm (kèm **tên thuật toán**) trước khi đọc số.
3. Kết quả kèm **phân bố lý do** (Luật E) — nhánh chưa khai hoả phải được in
   cảnh báo, kể cả khi tỉ lệ 100%.
4. Đường nhẹ trong mọi ĐC: **không gọi LLM, không trả lời nghiệp vụ, không tạo
   bản ghi** (`Δcomplaints = Δtickets = 0`) — bất biến do tester giữ.

## Thứ tự lượt thử R1/R2/R3 (chốt theo đề nghị tester 17/08)

**Khoá băm luật TRƯỚC khi hô lượt thử.** R1 (cờ OFF) chạy **trước** R2/R3 và
**trên cùng một băm luật** — nếu luật đổi giữa chừng (vd xoá `DAI_TOI_DA`)
thì R1↔R2 khác **hai** biến và toàn bộ so sánh mất nghĩa.
⟹ trình tự bắt buộc: T1 xong (gồm xoá `DAI_TOI_DA`) → băm luật chốt + công bố
→ cả ba bộ cổng xanh trên băm đó → **rồi mới** R1 → R2 → R3, không đổi luật
xen giữa.
