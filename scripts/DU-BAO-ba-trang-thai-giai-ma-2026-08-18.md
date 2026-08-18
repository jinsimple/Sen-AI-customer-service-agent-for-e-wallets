# DỰ BÁO — `crypto_types`: BA trạng thái giải mã, không phải hai

> Công bố **trước** khi sửa `src/db/crypto_types.py`. Nền: `HEAD=bad3e1b`, băm `src/` = `78154194edff`.
> Người viết: tech-lead · 18/08/2026 · việc (1) trong bốn việc PO thật chốt (STATE §5.E).

---

## 0. Ba phát biểu của PO-agent — tôi KIỂM LẠI BẰNG VẬT, không nhận qua lời kể

| phát biểu | tôi đo | |
|---|---|---|
| `except InvalidToken: return value` nuốt im lặng | `crypto_types.py:40-43` và `:64-65`, **hai chỗ** | ✅ |
| phân bố 738 plaintext / 23 mã hoá | `psql`: **738** (05/05→14/08) · **23** (15/08→17/08) | ✅ |
| xoay khoá ⟹ hỏng dữ liệu IM LẶNG | dựng lại bằng hai khoá Fernet: khoá sai trả `'gAAAAABqg6vU…'` **không exception, không log**, và **không phân biệt được** với ca plaintext hợp lệ ở nơi gọi | ✅ |

**Cả ba đúng.** Phát biểu thứ ba là phát biểu nặng nhất và nó đúng theo nghĩa đen: giá trị trả về
cho nơi gọi là `str`, đúng kiểu, đúng chỗ, **nội dung là bản mã**. Ràng buộc cứng 3 của hiến pháp
(*"cấm bịa số liệu — không tra được thì nói rõ không tra được"*) bị vi phạm ở tầng thấp nhất: hệ
thống **không nói** là không đọc được, nó đưa ra một chuỗi trông như nội dung.

## 1. 🔴 BÁN KÍNH NỔ — đo TRƯỚC khi sửa, đây là số quyết định

```
cột                          giải mã ĐƯỢC   chưa mã hoá   KHOÁ KHÁC
complaints.description_raw            23           738           0
messages.content                     467             0           0
bank_accounts.account_no             245             0           0
policy_chunks.text                   378             0           0
```
⟹ **KHÔNG dòng nào đang mã hoá bằng khoá khác.** Bản vá fail-closed **không đổi một lượt đọc nào
hôm nay** — nó chỉ **lên đạn** cho lần xoay khoá. Đây là thời điểm rẻ nhất để land nó, và nếu con
số cột `KHOÁ KHÁC` khác 0 thì việc phải làm là một việc KHÁC (khôi phục), không phải việc này.

⚠️ Phép phân loại dùng **hình dạng token Fernet** (giải base64 → byte đầu `0x80`, ≥57 byte =
1 phiên bản + 8 timestamp + 16 IV + 32 HMAC), **không** dùng tiền tố chuỗi `'gAAAAA%'`. Bảng trên
là bằng chứng phép ấy chạy đúng: 738 dòng tiếng Việt vào đúng rổ *"chưa mã hoá"*, 0 dòng lạc.

## 2. Sẽ sửa gì

`process_result_value` phải trả **BA** kết cục thay vì hai:

```
giải mã ĐƯỢC        -> trả nội dung                          (không đổi)
CHƯA mã hoá         -> trả nguyên văn + LOG WARNING đếm được (đang: trả im lặng)
mã hoá KHOÁ KHÁC    -> 🔴 NÉM `KhongGiaiMaDuocError`          (đang: trả BẢN MÃ như nội dung)
```

**Vì sao ném chứ không trả cờ:** trả bản mã là **bịa nội dung** — ràng buộc cứng 3. Trả `None` thì
lẫn với `NULL` hợp lệ. Chỉ có ném mới không thể bị nơi gọi vô tình bỏ qua. Cùng nếp fail-closed
đã dùng cho `dau_ma_nguon` (`.bam_ma_nguon` rỗng ⟹ TỪ CHỐI khởi động).

**Vì sao vế "chưa mã hoá" phải ĐẾM ĐƯỢC:** nó là **điều kiện tiên quyết** của bước nạp lại 738
dòng (`migrations/`, chưa tồn tại). Không có số đếm thì script nạp lại chạy xong không ai biết nó
đã phủ hết chưa — và ta lại có một cơ chế "trông như xong".

## 3. DỰ BÁO — điền TRƯỚC

| # | vật | DỰ BÁO | THẬT | |
|---|---|---|---|---|
| 1 | băm `src/` | ĐỔI khỏi `78154194edff` | | |
| 2 | file `src/` đổi | **1** — chỉ `crypto_types.py` | | |
| 3 | `contracts/` · `check_contracts` | 0 đổi · sạch | | |
| 4 | `test_invariants.py` | **23 passed** | | |
| 5 | hồi quy 7 file tầng tool | **50 passed** | | |
| 6 | bộ test chạm cột mã hoá | **xanh** — vì cột `KHOÁ KHÁC` = 0 ⟹ nhánh mới không bắn | | |
| 7 | `docker diff` | 0 · 0 · 0 | | |
| 8 | token tiêu | **0** | | |

## 4. Nếu khác thì nghi gì

| lệch | nghi |
|---|---|
| #4/#5/#6 ĐỎ | 🔴 nghi **nặng nhất**: có dòng mã hoá bằng khoá khác mà phép đo bán-kính của tôi **bỏ sót** — vì đó là điều kiện DUY NHẤT làm nhánh mới bắn. Đọc dòng nào, đừng vá cho xanh |
| #6 đỏ ở **fixture test** chứ không phải dữ liệu thật | test tự sinh giá trị `gAAAAA…` giả làm bản mã ⟹ **nội dung của tester**, tôi không sửa, soạn kết luận chuyển qua PO-agent |
| #3 bẩn | tôi chạm `contracts/` ngoài ý định ⟹ DỪNG, đi đủ §10 |
| #7 ≠ 0 | Luật I — hoàn nguyên trước khi báo bất cứ số nào |

## 5. Khai trước — điều gì KHÔNG được tính là xác nhận

Cổng xanh ở đây ⟹ *"nhánh mới không làm hỏng đường đang chạy"*. Nó **KHÔNG** ⟹ *"đã bảo vệ được
việc xoay khoá"* — điều đó chỉ chứng minh được bằng **ca đối chứng** (Luật A): nạp một giá trị mã
hoá bằng khoá khác rồi xác nhận nó **NÉM**. Ca đó thuộc `tests/`, **vùng tester**. Tôi kiểm bằng
nháp ngoài repo và chuyển **kết luận + lý lẽ** qua PO-agent, **không** soạn nội dung test.

**Và việc này KHÔNG đóng được §5.E.** Nó là bước 1/3. Còn: script nạp lại 738 dòng (`migrations/`,
chưa tồn tại) và **sao lưu + đếm phân bố trước/sau** (PO-agent đã dặn: *đọc trước, dọn sau* —
đừng để script tự phát hiện lúc chạy).

## 6. KẾT QUẢ THẬT

*(để trống tới khi đo xong)*
