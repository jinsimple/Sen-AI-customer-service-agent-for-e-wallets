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

---

# ⑥ KẾT QUẢ THẬT — dự báo ở `42ccca7`, viết trước khi dựng

| # | dự báo | thực tế | |
|---|---|---|---|
| 1 | ảnh có sẵn cục bộ, không kéo mạng | `postgres:16-alpine` có sẵn, không kéo | ✅ |
| 2 | ca "có plaintext" → ĐỎ | **PASSED** (đếm đúng `tran=3`) | ✅ |
| 3 | ca "sạch" → XANH | **PASSED** | ✅ |
| 4 | ca "không đọc được" → báo riêng | **PASSED** — nhưng xem ⑧ | ⚠️ |
| 5 | `docker diff` ba ngăn xếp Δ=0 | **Δ=0 · 0 · 0** | ✅ |
| 6 | ca `fin05ttl` cũ vẫn PASSED | **7 passed** | ✅ |

## ⑦ NGHIỆM THU — ba dòng brief yêu cầu, output thật

**① Quần thể vứt đi — dựng bằng gì:**
```
docker run -d --rm --name fin05-doi-chung-vut-di \
  -e POSTGRES_USER=vutdi -e POSTGRES_DB=vutdi -e POSTGRES_PASSWORD=<ngẫu nhiên> \
  postgres:16-alpine
```
`vutdi` **có chủ đích**: ai lỡ trỏ ca này vào container thật thì `psql -U vutdi`
**trượt ngay** thay vì lặng lẽ đọc CSDL sản phẩm. Lời khai nạp vào là **GIẢ**,
không lấy từ dữ liệu thật — bộ đo không được sinh thêm một bản sao PII.

**② Ca đối chứng ĐỎ — và đây là bằng chứng mạnh nhất:** không phải một ca mới
tự khẳng định, mà là **chính cổng sản phẩm, không sửa một dòng**, chĩa vào quần
thể vứt đi:
```
phân bố quần thể vứt đi : {'tran': 2, 'ma_hoa': 1}
E  AssertionError: 🔴 CỘT NHÓM A CÓ DÒNG NẰM TRẦN TRÊN ĐĨA: complaints.description_raw
E      trần          2
```

**③ Ca chiều xuôi XANH trên quần thể sạch (`fin05` thật):**
```
tests/test_security/test_doi_chung_quan_the_vut_di.py            3 passed
tests/test_security/test_cot_nhom_a_khong_nam_plaintext.py  +
tests/test_security/test_nghiem_thu_backfill_nhom_a.py           9 passed
```

## ⑧ 🔴 HAI LỖI TRONG PHÉP THỬ CỦA TÔI, cả hai bắt được nhờ ĐỌC chứ không nhờ màu

**(a) Ca thứ ba đỏ vì test-của-test sai, KHÔNG phải vì cổng sai.**
`pytest.fail()` ném `Failed` — kế thừa **`BaseException`**, không phải
`Exception` ⟹ `pytest.raises(Exception)` **không bắt được**. Thông điệp cổng in
ra **đã đúng ngay lượt đầu**. Nếu tôi đọc màu, tôi đã đi sửa cổng.
> *"Phép thử của tôi hỏng" ≠ "thứ tôi đo hỏng"* — cùng câu đã dùng cho
> `Exit code 143` sáng nay, lần này ở tầng assertion.

**(b) Ca ① CHẬP CHỜN: xanh lượt đầu, đỏ lượt sau, cùng một mã.**
Nguyên nhân thật, in ra trong output chứ không phải suy đoán:
```
FATAL: the database system is starting up
```
`pg_isready` **trả 0 trong khi CSDL còn đang khởi động** — ảnh postgres chạy một
server **TẠM** lúc `initdb`, và `pg_isready` bắt tay được với server tạm ấy.

🔴 **Cách chữa KHÔNG phải chạy lại tới khi xanh** — đó là biến một ca chập chờn
thành một ca **không đọc được theo cả hai chiều**. Cách chữa là đổi **mốc sẵn
sàng** sang thứ ta **thật sự cần**: một câu SQL chạy trót lọt.
Xác nhận bằng **ba lượt liên tiếp**: `3 passed · 3 passed · 3 passed`.

> Đây đúng **Luật 4c** — *đừng suy cơ chế từ một cái TÊN*. `pg_isready` tên là
> "sẵn sàng chưa", nhưng nó trả lời *"có ai nhận kết nối không"*, **không** trả
> lời *"CSDL của tôi dùng được chưa"*. Cùng họ với `Luật G`: một cơ chế đang làm
> **đúng việc của NÓ** không có nghĩa nó đang làm việc **ta giả định**.

## ⑨ Bước ③ — điều tôi KHÔNG làm, và vì sao

Xoá `fin05ttl` **ngoài vùng ghi của tester**, và ADR-036 ghi rõ bước ③ là **báo
lại**, không phải xoá. Tôi giao ①②, PO quyết ③.

**Và tôi ĐỀ NGHỊ CHƯA xoá ngay**, theo tinh chỉnh PO-agent đã duyệt: giữ song
song tới khi ca mới **ĐỎ THẬT ít nhất MỘT lần trong một lượt chạy BÌNH THƯỜNG**
— không phải lượt tôi cố ý ép như hôm nay. Mốc ấy phân biệt *"ca chạy được khi
tôi ép"* với *"ca sống trong nếp chạy hằng ngày"*, và hôm nay tôi mới chứng minh
được vế đầu.
