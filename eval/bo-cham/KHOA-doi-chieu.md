# KHOÁ ĐỐI CHIẾU — KHÔNG MỞ TRƯỚC KHI CHẤM XONG

> Mở file này trước khi điền xong ô cuối cùng là làm hỏng tính mù của cả gói.

> Seed xáo: `20260830`


| L-id | ca trong file gốc | mã kịch bản |
|---|---|---|
| L01 | Ca 02 | `UXQA-001` |
| L02 | Ca 11 | `UXQA-005` |
| L03 | Ca 15 | `UXQA-006` |
| L04 | Ca 26 | `UXQA-007` |
| L05 | Ca 25 | `UXQA-002` |
| L06 | Ca 21 | `UXQA-004` |
| L07 | Ca 27 | `UXQA-001` |
| L08 | Ca 03 | `RAG-47` |
| L09 | Ca 08 | `RAG-40` |
| L10 | Ca 19 | `RAG-37` |
| L11 | Ca 13 | `RAG-43` |
| L12 | Ca 28 | `UXQA-001` |
| L13 | Ca 12 | `UXQA-005` |
| L14 | Ca 24 | `UXQA-006` |
| L15 | Ca 07 | `UXQA-007` |
| L16 | Ca 17 | `RAG-44` |
| L17 | Ca 06 | `UXQA-001` |
| L18 | Ca 04 | `RAG-39` |
| L19 | Ca 01 | `RAG-38` |
| L20 | Ca 18 | `UXQA-003` |
| L21 | Ca 05 | `RAG-41` |
| L22 | Ca 22 | `UXQA-001` |
| L23 | Ca 14 | `UXQA-002` |
| L24 | Ca 10 | `UXQA-004` |
| L25 | Ca 09 | `UXQA-005` |
| L26 | Ca 16 | `UXQA-006` |
| L27 | Ca 20 | `UXQA-007` |
| L28 | Ca 23 | `UXQA-001` |

## Cách tổng hợp — đọc trước khi tính bất kỳ tỉ lệ nào

**k lệch rất mạnh.** Một kịch bản chiếm 6/28 lượt, tám kịch bản khác chỉ 1 lượt.
Lấy trung bình phẳng trên 28 dòng là để **một kịch bản chiếm 21% trọng số** của
con số cuối.

**Quy tắc bắt buộc — tổng hợp HAI TẦNG:**

1. **Tầng kịch bản:** với mỗi mã kịch bản, tính tỉ lệ đạt trên k lượt của nó.
   Kịch bản có k ≥ 2 mà **các lượt không đồng nhất** → đánh dấu `KHÔNG ỔN ĐỊNH`
   và báo cáo riêng. Đây là phát hiện có giá trị nhất trong cả gói, đừng để nó
   tan vào một con số trung bình.
2. **Tầng gói:** trung bình **các tỉ lệ ở tầng 1**, mỗi kịch bản một phiếu —
   KHÔNG trung bình 28 dòng.

**`KHONG_CHAC` báo cáo riêng, KHÔNG nằm trong mẫu số** của tỉ lệ đạt. Gộp vào
`TRUOT` là biến "chưa biết" thành "đã biết là sai".

**Câu khai phạm vi — phải đi kèm mọi lần trích con số này, không có ngoại lệ:**

> *Tỉ lệ đo trên gói 28 lượt chấm, phủ 15 kịch bản (k không cân, từ 1 đến 6),
> một người chấm, chấm mù. Đây KHÔNG phải tỉ lệ đạt của agent trên tập khiếu nại
> thật.*
