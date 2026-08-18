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
| 1 | băm `src/` | ĐỔI khỏi `78154194edff` | `5bc33a9b254c` | ✅ |
| 2 | file `src/` đổi | **1** — chỉ `crypto_types.py` | 1 file | ✅ |
| 3 | `contracts/` · `check_contracts` | 0 đổi · sạch | 0 · sạch, ba băm không đổi | ✅ |
| 4 | `test_invariants.py` | **23 passed** | 23 passed | ✅ |
| 5 | hồi quy 7 file tầng tool | **50 passed** | 50 passed | ✅ |
| 6 | bộ test chạm cột mã hoá | **xanh** — vì cột `KHOÁ KHÁC` = 0 ⟹ nhánh mới không bắn | xanh | ✅ |
| 7 | `docker diff` | 0 · 0 · 0 | 0 · 0 · 0 | ✅ |
| 8 | token tiêu | **0** | 0 | ✅ |

**8/8 trúng.** (Quy trình dự báo-trước: 6/6 · 2/2 · 10/10 · 8/8.)

## 6. KẾT QUẢ THẬT

**Nghiệm thu ba trạng thái** (nháp ngoài repo, in băm vật; chạy lại sau khi siết `validate=True`):

```
① giải mã ĐƯỢC      trả nội dung, KHÔNG log            ✅ đường nóng không được ồn
② CHƯA mã hoá       nguyên văn + WARNING đếm được       ✅ `doc_gia_tri_chua_ma_hoa`
③ KHOÁ KHÁC         NÉM `KhongGiaiMaDuocError`          ✅ ca đối chứng, Luật A vế "KÊU"
   └ thông điệp lỗi KHÔNG chứa bản mã, KHÔNG chứa nội dung khách   ✅
   └ log ERROR cũng KHÔNG mang bản mã                              ✅
④ hình dạng         8/8 chuỗi thường không bị nhận nhầm ✅ gồm cả `"gAAAAA"` cụt và emoji
⑤ `None`            đi qua nguyên vẹn                   ✅ không lẫn với "không đọc được"
```

🔴 **Phép kiểm mạnh nhất — chạy HÀM ĐÃ SHIP trên 1.851 DÒNG THẬT** (không phải bản chép, không
phải mẫu tự nghĩ; qua cổng `127.0.0.1:5432` đã publish, chỉ đọc):

```
cột                          (1) giải mã   (2) chưa MH   (3) KHOÁ KHÁC
complaints.description_raw            23           738              0
messages.content                     467             0              0
bank_accounts.account_no             245             0              0
policy_chunks.text                   378             0              0
TỔNG                                1113           738              0
```
**Tái hiện CHÍNH XÁC bảng đo trước khi vá.** Đây là thứ đóng được vế *"fail-safe có HƯỚNG"*: 738
dòng tiếng Việt thật đi qua nhánh phân loại mới mà **không dòng nào** bị đẩy nhầm sang nhánh ném.

⚠️ **Tính chất đã biết, không phải bug — nhưng phải nói ra:** WARNING phát **theo từng dòng**, nên
quét cả bảng `complaints` in ra **738 dòng log**. Ở lưu lượng thật con số này rải ra theo request
nên nhỏ, và nó **tự tắt về 0** sau khi script nạp lại chạy. Ai thấy log ồn thì đó là **đúng số dòng
chưa mã hoá còn lại** — nó là **thước đo tiến độ**, không phải rác. Đừng hạ mức log để cho êm:
làm thế là dựng lại đúng sự im lặng vừa gỡ bỏ.

## 7. Việc này KHÔNG đóng ADR-032 — mới là 1/3

- ✅ ① `crypto_types` ba trạng thái — **xong** (bản này)
- ⬜ ② script nạp lại 738 dòng, `migrations/` — **chưa tồn tại**. PO-agent dặn: **sao lưu trước**,
  **đếm phân bố hai đầu**. Bảng 1.851 dòng ở trên là **mẫu số ĐẦU** — đã có, đã ghi vào git.
- ⬜ ③ cổng trong `tests/` — vùng tester, PO-agent giao.

**Ca đối chứng ③ ở trên là nháp NGOÀI repo.** Nó chứng minh cơ chế bắn, **không** thay thế cổng
trong `tests/` — nháp không chạy trong CI, và một cơ chế không có cổng là cơ chế sẽ bị gỡ mà không
ai biết.

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

## 8. SIẾT SAU KHI CÔNG BỐ — `validate=True`, và vì sao nó KHÔNG phải chuyện nhỏ

PO-agent đề xuất phân biệt bằng `startswith("gAAAAA")` (lý lẽ: byte phiên bản `0x80` → base64url
luôn mở đầu `gA`). **Cùng một hiểu biết**, và bản tôi đã land mã hoá nó theo **cấu trúc** thay vì
theo tiền tố chuỗi — mạnh hơn, lý do ghi trong docstring `_co_hinh_dang_fernet`.

Nhưng lời nhắc ấy làm tôi soi lại phép giải base64 và **tìm ra một kẽ hở thật của bản đầu**:

```
base64.urlsafe_b64decode(v)                      ← mặc định validate=FALSE
   ⟹ ÂM THẦM BỎ QUA mọi ký tự ngoài bảng chữ cái base64 rồi giải phần còn lại
   ⟹ một chuỗi tiếng Việt có dấu/khoảng trắng VẪN có thể giải ra byte
   ⟹ và nếu byte đầu tình cờ là 0x80 + đủ 57 byte thì nó bị NÉM OAN
```
Bản đầu **đúng trên 738 dòng thật**, nhưng đúng nhờ **may mắn về padding**, không nhờ phép kiểm.
Một phép kiểm đúng vì trùng hợp là phép kiểm sẽ hỏng trong im lặng — đúng lớp lỗi cả ngày đang vá.

⟹ Siết sang `base64.b64decode(..., altchars=b"-_", validate=True)`. Ký tự lạ ⟹ ném ⟹ rơi đúng
nhánh *"chưa mã hoá"*. Đo lại **trên cùng 1.851 dòng thật**: `1113 / 738 / 0` — **y hệt**, và ca
đối chứng khoá-khác **vẫn ném**. Tức siết chặt hơn mà **không đổi một phân loại nào** trên dữ liệu
thật; nó chỉ đóng một cửa chưa ai đi qua.

🔴 **Và đây là chỗ đáng ghi nhất:** nếu tôi chỉ chạy lại nghiệm thu mà **không đo lại 1.851 dòng**,
tôi đã không có bằng chứng nào rằng việc siết không đẩy dòng thật sang nhánh ném. Cổng xanh sẽ
"xác nhận" một điều nó không kiểm. Băm vật sau khi siết: `5bc33a9b254c`.
