# DỰ BÁO — dời ca đối chứng sang QUẦN THỂ VỨT ĐI (ADR-036 bước ①②)

> Vai: **tester** · 18/08 · **0 token** · viết **TRƯỚC** khi dựng quần thể.
> Nhánh: `dev/learning-loop` @ `ff4f40b` (Luật Q — kiểm trước khi tin file nào).

## ① Vì sao không dùng lại cách cũ

Ca đối chứng hiện tại chĩa vào `fin05ttl` — **quần thể bẩn tồn tại vì chưa ai
dọn**. PO-agent chỉ ra và tôi nhận: *một cổng không nên phụ thuộc vào việc ai
đó QUÊN DỌN.* ADR-036 nói mạnh hơn: một dụng cụ chỉ hoạt động chừng nào lỗ còn
mở là dụng cụ **cột đội vào việc không bao giờ vá lỗ ấy**.

## ② Hình dạng — chốt TRƯỚC khi gõ

**Quần thể vứt đi = một container `postgres:16-alpine` RIÊNG**, dựng lúc chạy
test, xoá lúc xong. **Không** phải ngăn xếp đang phục vụ (Luật I), **không**
phải một CSDL mới trong postgres của `fin05` — tạo CSDL trong đó vẫn là **ghi
vào máy chủ đang phục vụ**.

🔴 **Vì sao PHẢI là postgres thật chứ không phải SQLite cho nhanh:** cổng đo
bằng `docker exec … psql` + `CASE … LIKE 'gAAAAA%'`. Đổi sang SQLite là **đổi
đúng đoạn đường đang cần chứng minh**. Ca đối chứng phải đi **cùng một dây**
với ca thật, nếu không nó chứng minh một cổng khác.

**Ba ca, ba trạng thái** (`§3` của brief):
```
quần thể CÓ plaintext      → cổng ĐỎ    ← thứ phải chứng minh
quần thể SẠCH (toàn gAAAAA) → cổng XANH  ← Luật 2, không chặn nhầm
quần thể KHÔNG ĐỌC ĐƯỢC     → BÁO RIÊNG, tuyệt đối không lặng lẽ xanh
```

## ③ DỰ BÁO

| # | dự báo | độ chắc | nếu khác thì nghi gì |
|---|---|---|---|
| 1 | container vứt đi lên được từ ảnh **có sẵn cục bộ**, không kéo mạng | **cao** | phải kéo ⟹ tôi ghi tên ảnh sai; dừng, đừng kéo bừa |
| 2 | ca "có plaintext" → **ĐỎ** | **rất cao** | XANH ⟹ 🔴 cổng **không** đọc container tôi trỏ tới — nghi tham số container bị bỏ qua |
| 3 | ca "sạch" → **XANH** | **cao** | ĐỎ ⟹ bộ phân loại bắt nhầm `gAAAAA…` thành trần |
| 4 | ca "không đọc được" → **báo riêng**, chữ `KHÔNG ĐO ĐƯỢC` | **cao** | xanh ⟹ đúng lỗ Luật 1, phải vá trước khi đi tiếp |
| 5 | `docker diff` ba ngăn xếp **Δ=0** | **cao** | ≠0 ⟹ tôi lỡ chạm ngăn xếp phục vụ; hoàn nguyên + khai |
| 6 | ca `fin05ttl` cũ **vẫn PASSED** | **cao** | nó còn sống tới bước ③ |

🔴 **Khai trước:** dự báo 2 TRÚNG **không** đủ để gỡ `fin05ttl`. ADR-036 bước ②
đòi ca mới **ĐỎ đúng lúc cần đỏ**; PO-agent tinh chỉnh thêm mốc đóng: nó phải
**đỏ thật ít nhất MỘT lần trong một lượt chạy bình thường**, không phải lượt tôi
cố ý ép. Hôm nay tôi chỉ giao được **①②**. **Bước ③ là báo cáo, không phải xoá.**

## ④ Vì sao GIỮ SONG SONG, và cửa sổ đóng lúc nào

```
quần thể vứt đi   chứng minh cổng kêu THEO THIẾT KẾ
fin05ttl          chứng minh cổng kêu TRÊN DỮ LIỆU THẬT CHƯA AI ĐỤNG
```
**Hai NGUỒN độc lập** (Luật D — *"dư thừa là hệ quả, không phải tiêu chí"*),
không phải một nguồn có bản sao lưu. Nhưng cửa sổ **có hạn**, đúng ADR-036:
giữ vô thời hạn là quay lại đúng cái bẫy vừa thoát.

## ⑤ Điều ca này KHÔNG chứng minh

- **Không** chứng minh dữ liệu trên `fin05` an toàn — nó chứng minh **cái cổng**
  còn biết kêu. Hai câu khác nhau.
- **Không** phủ `production`, nơi **chưa ai đo**.
- Và tới khi bước ③ xong: mọi phát biểu at-rest phải kèm phạm vi — *"đã mã hoá
  **trên ngăn xếp phục vụ `fin05`**"* (ADR-036 QĐ2, hiệu lực NGAY).
