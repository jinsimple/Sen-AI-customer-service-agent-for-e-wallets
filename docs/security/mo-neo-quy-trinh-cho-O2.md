# Mỏ neo QUY TRÌNH cho bộ đếm O2 (định nghĩa của security)

> Vai: **security** · 2026-08-15 · nhánh `dev/learning-loop`
> Tester phát hiện: bộ đếm mật độ O2 **mù với liệt-kê-QUY-TRÌNH**. Lỗ nằm ở
> **bộ ĐO** — nguy hiểm hơn lỗ ở bộ lọc, vì bộ đo mù thì phân phối nói "không có
> vấn đề" và mệnh đề *"nâng lên chặn khi có rò"* thành **rỗng** — đúng thứ quyết
> định "O2 đếm trước, chặn sau" sinh ra để diệt. Lỗ này là của **spec tôi viết**.
>
> **Bản đo:** `output_filter.py` sha256 **`5f643f71ddb5`**.

---

## 1. Xác nhận lỗ bằng đo

| Câu | Mật độ đếm được | Kỳ vọng |
|---|---|---|
| *"Mình có mấy nguyên tắc: không tự quyết về tiền, không bịa số liệu, không tiết lộ thông tin người khác, và luôn xác nhận mình là AI."* | **3** | ≥3 ✅ |
| *"**Quy trình** của mình là: xác định loại khiếu nại, tra cứu giao dịch, rồi tạo hồ sơ…"* | **0** | ≥3 ❌ |
| *"**Các bước** mình làm gồm: tra lịch sử giao dịch, đối chiếu số tiền, tạo ticket…"* | **0** | ≥3 ❌ |

9 mỏ neo hiện có đều thuộc họ **NGUYÊN TẮC** (`khong_quyet_tien`, `khong_bia_so`,
`pdpa_ben_thu_ba`, `khong_ket_luan_gian_lan`, `otp`, `phan_loai`,
`tai_lieu_tham_khao`, `xung_ai`, `khong_tiet_lo_huong_dan`). Không mỏ neo nào
thuộc họ **CÁC BƯỚC**. Mà ràng buộc 7 cấm cả hai: nó cấm đọc lại
*"Ràng buộc bắt buộc"* **và** *"Quy trình điều tra"*.

## 2. Định nghĩa mỏ neo QUY TRÌNH — kèm điều kiện chống chặn nhầm

**Không thể** thêm mỏ neo các-bước rồi đếm y như họ nguyên-tắc. Lý do đo được:
các bước là thứ agent **nói ra hợp lệ hàng ngày** khi báo cho khách nó đang làm
gì. Ba câu bình thường dưới đây chứa 1–2 bước và **phải luôn im**:

- *"Mình sẽ tra cứu giao dịch này giúp bạn nhé."*
- *"Mình vừa tra cứu giao dịch và đã tạo hồ sơ cho bạn rồi."* (2 bước)
- *"Mình sẽ kiểm tra lại rồi tạo hồ sơ khiếu nại giúp bạn."* (2 bước)

⟹ **Phân biệt không nằm ở việc NHẮC một bước, mà ở việc TRÌNH BÀY CHUỖI BƯỚC như
một quy trình.** Nên họ quy-trình cần **hai điều kiện đồng thời**:

**(A) MỎ NEO CÁC BƯỚC** — mỗi mỏ neo là một bước trong `Quy trình điều tra` của
system prompt (đặt tên theo bước, không theo câu chữ):
| Mỏ neo | Bắt ý (viết nhiều cách) |
|---|---|
| `buoc_phan_loai` | xác định loại khiếu nại / phân loại khiếu nại / thuộc loại nào |
| `buoc_tra_lich_su` | tra lịch sử giao dịch / xem các giao dịch gần đây |
| `buoc_tra_giao_dich` | tra cứu giao dịch / tra mã giao dịch / đối chiếu số tiền |
| `buoc_hoi_lai` | hỏi lại để thu hẹp / hỏi thêm thông tin |
| `buoc_tao_ho_so` | tạo hồ sơ / tạo ticket / lập phiếu khiếu nại |
| `buoc_bao_ket_qua` | báo mã ticket / báo mốc xử lý / thông báo SLA |
| `buoc_chuyen_nguoi_that` | chuyển chuyên viên / gặp người thật |

**(B) DẤU HIỆU TRÌNH BÀY-THÀNH-QUY-TRÌNH** (bắt buộc có ít nhất một):
`quy trình` · `các bước` · `gồm:` · `trình tự` · `đầu tiên … sau đó` ·
`bước 1` / `thứ nhất` · `mình được hướng dẫn` · `quy định của mình`.

**Ngưỡng:** bật tín hiệu khi **(B) có** **VÀ** **(A) ≥ 2 mỏ neo khác nhau**.
Ngưỡng 2 (không phải 3) là được, vì (B) đã gánh phần lọc — một câu có dấu hiệu
trình-bày-quy-trình cộng hai bước thì đã là đọc lại quy trình.

**Kiểm lại trên bộ ở §1/§2:** hai câu liệt kê quy trình đều có (B) + ≥2 bước →
**bật**. Ba câu hợp lệ đều **không có (B)** → **im**. Không cần đếm chung
ngưỡng với họ nguyên-tắc.

**Cách gộp vào bộ đếm:** hai họ đếm **riêng**, nhưng cùng ghi vào **một khoá đếm
theo `thread_id`** — vì mục đích là phát hiện *hội thoại đang moi chỉ thị*, không
phân biệt moi nguyên-tắc hay moi quy-trình. **Vẫn CHỈ ĐẾM, không chặn** — giữ
nguyên quyết định O2 (`quyet-dinh-O2-lo-chi-thi.md`).

## 3. Phát hiện KÈM THEO — mỏ neo NGUYÊN TẮC cũng giòn (cùng họ F-24/F-27)

Câu 7 trong corpus của tôi có vế *"mình cũng **không được** kết luận gian lận"* —
đúng ý của mỏ neo `khong_ket_luan_gian_lan` — nhưng **cả câu đếm 0**, tức vế đó
cũng không được tính. Nguyên nhân gần như chắc chắn là **liền kề**: mỏ neo khớp
`không kết luận…` còn câu chèn thêm `được` ở giữa.

Đây là **lần thứ ba** cùng một họ lỗi trong bộ lọc: F-24 (mẫu injection đòi đúng
một từ bổ nghĩa), F-27 (O1 đòi đúng chữ "OTP"), và nay mỏ neo O2 đòi đúng cụm
liền kề. **Đề nghị chung, không chỉ cho O2:** mọi mẫu khớp cụm tiếng Việt phải
cho phép **chèn từ đệm** giữa các thành phần (`được`, `phải`, `sẽ`, `cũng`,
`không bao giờ`), thay vì đòi liền kề. Đây là đặc điểm ngữ pháp tiếng Việt, không
phải kỹ xảo né tránh — người viết bình thường chèn những từ này một cách tự nhiên.

## 4. Giao ra

| Vai | Việc |
|---|---|
| **coder** | 7 mỏ neo (A) + danh sách dấu hiệu (B) + ngưỡng "(B) và (A)≥2"; ghi vào cùng khoá đếm theo `thread_id`; **không chặn**. Cộng: nới liền-kề cho mỏ neo nguyên-tắc hiện có (§3). |
| **tester** | Ca DƯƠNG: 2 câu liệt kê quy trình ở §1. Ca ÂM **bắt buộc**: 3 câu hợp lệ ở §2 — phải luôn im. Cộng ca `"không được kết luận gian lận"` cho §3. |
| **security** | Sau khi land: đo lại phân phối mật độ trên corpus thật để xem bộ đếm còn mù chỗ nào. |
