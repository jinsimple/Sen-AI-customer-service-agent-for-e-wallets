# DỰ BÁO — ca đỏ `test_kho_khong_chua_tai_lieu_noi_bo_da_biet`

> Vai: **tester** · 18/08 · **0 token** · viết **TRƯỚC** khi liệt kê collection.
> Đèn xanh PO-agent. Đường: quan sát **hộp đen** qua `docker exec` chỉ-đọc.
> **Không đọc `src/`. Không nhận nội dung soạn sẵn từ tech-lead.**

## ① Điều đã biết, và nó KHÔNG phải "kho rỗng"

`docs/STATE.md` §2 (bản 17/08) ghi ca này đỏ vì *"kho rỗng, điều kiện hạ tầng"*.
Đó là **KẾT LUẬN mà chính cái đèn in ra**, không phải triệu chứng — Luật H:

```
tests/test_rag/test_thanh_phan_tai_lieu_kho.py:113
    pytest.fail("index KHÔNG có doc_id nào — kho rỗng, mọi khẳng định … vô nghĩa")
```
Câu đúng đáng lẽ phải là *"collection tên `policy_faq` trả 0 doc_id"*. Vì nó in
kết luận, cả đội chép lại và tin từ 17/08.

## ② SUY LUẬN — nó cho một dự báo KIỂM ĐƯỢC, không phải phỏng đoán

Đầu dò gõ cứng `c.get_collection('policy_faq')` (dòng 80).

- `get_collection` với tên **không tồn tại** ⟹ **ném ngoại lệ** ⟹ `returncode != 0`
  ⟹ ca sẽ chết ở nhánh `"không đọc được index"`, **không** ở nhánh `"kho rỗng"`.
- Ca đang chết ở nhánh **`"kho rỗng"`**.

⟹ **DỰ BÁO 1: collection `policy_faq` TỒN TẠI và RỖNG (0 metadata).**
Đây là suy luận từ **KIỂU thất bại**, không từ nội dung kho — nên nó kiểm được
và có thể sai một cách nhìn thấy được.

## ③ Dự báo, kèm độ chắc

| # | dự báo | độ chắc | nếu khác thì nghi gì |
|---|---|---|---|
| 1 | `policy_faq` tồn tại, **0** metadata | **cao** — suy từ kiểu thất bại (②) | nếu nó KHÔNG tồn tại ⟹ phiên bản chromadb đổi hành vi `get_collection`, và suy luận ② hỏng ⟹ đọc lại từ đầu |
| 2 | index có **≥2** collection | **trung bình-cao** | chỉ có 1 ⟹ dữ liệu nằm ở **path khác**, không phải tên khác ⟹ đổi hướng truy |
| 3 | đúng **1** collection giữ gần hết dữ liệu, cỡ **≈378 chunk** trên `fin05` | **trung bình** — 378 là số bàn giao 17/08, chưa tự đo | lệch nhiều ⟹ ai đó đã nạp lại kho; hỏi trước khi kết luận |
| 4 | `fin05ttl` cho số **khác** (`≈419`) | **trung bình** | giống hệt ⟹ hai ngăn xếp dùng chung volume — finding riêng, nặng hơn |

🔴 **Khai trước:** dự báo 1 TRÚNG **không** xác nhận rằng ta đã hiểu kho. Nó chỉ
loại một giả thuyết (*"kho rỗng thật"*). Tên collection đúng vẫn là thứ phải
**quan sát**, không được suy.

## ④ 🔴 CẤM VÁ NHANH — ca Luật J sách giáo khoa

Sửa `'policy_faq'` thành tên mới làm cổng ĐỎ→XANH trong một dòng. **Không được
làm thế.** Hỏi cổng ấy khẳng định **CÁI GÌ**: tên nó hứa canh **RÒ TÀI LIỆU NỘI
BỘ vào kho RAG** — trục **rò rỉ dữ liệu**. Vì đầu dò trỏ sai chỗ, phép kiểm ấy
**CHƯA TỪNG chạy trên kho thật**.

⟹ Đây **không** phải "cổng đỏ vì hạ tầng". Nó là **cổng chưa bao giờ khẳng định
được điều nó hứa**. Vá tên suông = đổi một cổng **đỏ trung thực** lấy một **cổng
xanh rỗng** — tệ hơn hẳn trạng thái hiện tại.

## ⑤ Hình dạng bản vá — chốt TRƯỚC khi nhìn số

1. **KHÔNG gõ cứng tên collection nào.** Gõ tên mới là chép từ code lần thứ
   hai, và chết y hệt lần sau khi đổi model nhúng. Test phải **tự liệt kê**.
2. **Kiểm MỌI collection**, không chỉ cái to nhất. *Cổng rò rỉ mà bỏ sót một
   collection là cổng rò rỉ hỏng.*
3. **Đối chứng dương bắt buộc** (Luật A — cổng phải KÊU lúc bất thường): nhét
   một `doc_id` nội bộ giả vào một kho THỬ rồi xác nhận nó **kêu**. Thiếu vế
   này thì "xanh" chỉ nghĩa là chưa ai nhìn kỹ.
4. **Ba trạng thái:** kho sạch · kho bẩn · **không đọc được index** — nhánh thứ
   ba KHÔNG được gộp vào "sạch" (đúng lỗi vừa xảy ra ở đây).
5. Đối chứng dương phải chạy trên **kho THỬ**, tuyệt đối không ghi vào kho đang
   phục vụ (Luật I — bước đo không ghi vào container đang chạy).
