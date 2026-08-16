# Đo NHỊP GÕ trước buổi test 150 người — giao thức

> Vai: **tester** · 17/08. PO nâng thành **điều kiện tiên quyết** của buổi test.
> Trạng thái: **phương pháp đã sẵn sàng, chưa có dữ liệu người thật.**

## Vì sao đây là điều kiện tiên quyết, không phải việc làm thêm

Mọi con số trần đội tranh luận cả ngày — `179` · `71,6` · `74` · `0,95×` — đều
**chia cho một mẫu số chưa ai đo**: giả định *"mỗi người 1 câu / 2 phút"*
(= 0,50 lượt/phút/người).

Giả định đó **không sai một cách hiển nhiên**, nên nó trôi qua mọi vòng phản
biện. Nhưng nếu người thật gõ nhanh gấp đôi ở 10 phút đầu — **hành vi rất tự
nhiên khi mới vào thử đồ mới** — thì mọi trần chia đôi và kết luận *"đổi model
là đủ"* **sập**.

## Nguồn dữ liệu: bảng `messages` — KHÔNG cần thêm dụng cụ

    SELECT chat_session_id, created_at FROM messages WHERE role='customer'

Nhóm theo phiên, lấy khoảng cách giữa hai tin liên tiếp. Đã kiểm: bảng có đủ
`chat_session_id · role · created_at`, 467 bản ghi từ 11/08.

⚠️ Log **không** dùng được: nó chỉ ghi **lời gọi model**, không ghi **lượt
khách**. Chia số lời gọi cho 2,39 là ước lượng chồng ước lượng.

## 🔴 Đã chạy thử trên dữ liệu hiện có — và kết quả là một bài học, không phải một số

    81 phiên · 230 tin khách · 149 khoảng cách
    khoảng giữa hai tin: p10 = 3s · trung vị = 3s · p90 = 12s
    ⟹ 19,8 lượt/phút/người

**Con số này VÔ NGHĨA cho mục đích của ta** — 230 tin đó do **script test** sinh
ra, không phải người. Máy gõ tin tiếp theo ngay khi nhận xong phản hồi.

> **Nguồn dữ liệu đúng, dân số SAI.** Phương pháp chạy được, đường ống thông,
> con số ra đẹp đẽ — và nó nói về một quần thể không phải quần thể ta cần.

Cùng họ với **Luật 7**: *corpus phải cùng phạm vi với thứ được đo*. Nếu ai đó
chạy truy vấn trên rồi báo *"đo được 19,8 lượt/phút, gấp 40 lần giả định"*, cả
đội sẽ hoảng và đi tối ưu một vấn đề không tồn tại.

**Vì thế phép đo này chỉ có giá trị khi chạy trên phiên của NGƯỜI THẬT**, và
truy vấn phải lọc đúng các phiên đó.

## Giao thức

1. **Nhóm nhỏ trước** — 5–10 người, 15 phút. Đừng đo trực tiếp trên 150 người:
   nếu nhịp cao hơn dự kiến thì buổi test lớn hỏng ngay trong 10 phút đầu, và
   ta mất cả buổi của 150 người để học một điều 10 người đã dạy được.
2. **Ghi mốc thời gian bắt đầu** để lọc đúng phiên người thật khỏi phiên test.
3. **Đo theo cửa sổ**, không đo trung bình cả buổi:
   - **0–10 phút**: nhịp cao nhất, dùng cái này làm mẫu số cho trần
   - **10 phút sau**: nhịp ổn định, dùng để ước tính chi phí
   Trung bình cả buổi **giấu mất** đỉnh, mà đỉnh mới là thứ làm sập.
4. **Đo cả số người GÕ ĐỒNG THỜI**, không chỉ nhịp mỗi người. `150 người có tài
   khoản` ≠ `150 người đang gõ`. Trần chịu tải phụ thuộc **tích** của hai số này.
5. **Báo cả phân bố**, không chỉ trung vị — p90 của nhịp là thứ quyết định.

## Đổi ra trần chịu tải

    lượt/phút cần = (số người gõ đồng thời) × (nhịp p90, lượt/phút/người)

So với bảng trần trong `eval/uoc_tinh_chi_phi.py` (đọc **hàng phân vị 95**, vì
lượt điều tra nhiều bước mới là thứ làm sập).

## Việc còn lại

Chạy được ngay khi có phiên người thật đầu tiên — không chờ gì, không tốn lượt
LLM nào. Tôi giữ sẵn truy vấn; nói một tiếng là có số trong vài phút.
