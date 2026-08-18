# DỰ BÁO — backfill 738 dòng `complaints.description_raw` (ADR-032 ②)

> Công bố **trước** khi viết script, và **rất trước** khi chạy nó.
> Nền: `HEAD=bb20f6f`, băm `src/` = `d5b73a04d6ef` (khớp cả ba ảnh, lệch× 0·0·0).
> tech-lead · 18/08/2026.

---

## 0. 🔴 VIỆC NÀY KHÁC MỌI VIỆC TÔI LÀM HÔM NAY — nó GHI VÀO DỮ LIỆU THẬT

Bốn bản vá trước đều hoàn nguyên được bằng `git checkout`. Cái này **không**. Nó viết đè lên
**738 dòng lời khai của khách**. Một lỗi ở đây không phải một cổng đỏ — nó là **738 khiếu nại
không đọc lại được**, và `FIELD_ENCRYPTION_KEY` thì *"xoay là mất vĩnh viễn"* (STATE §1).

⟹ Ba thứ dưới đây **không phải thủ tục cho đẹp**, chúng là điều kiện để việc này được phép chạy:
**sao lưu trước · đếm hai đầu · dừng hỏi trước khi ghi**.

## 1. 🔴 QUYẾT ĐỊNH THIẾT KẾ: script ĐỘC LẬP, **KHÔNG** phải một revision alembic

PO-agent giao *"script nạp lại 738 dòng trong `migrations/`"*. Tôi để nó trong `migrations/` nhưng
**KHÔNG** làm nó thành alembic revision, và lý do là một phép đo:

```
[ĐO] docker-entrypoint.sh:17
     exec su appuser -c "alembic upgrade head && uvicorn …"
     ⟹ chạy MỖI LẦN container khởi động, trên CẢ BA ngăn xếp
     ⟹ và trên production app.adaptivealgo.uk
```
Làm nó thành revision nghĩa là: lần tới ai đó `docker compose up`, **738 dòng dữ liệu khách bị
viết đè tự động** — không sao lưu, không ai bấm nút, không ai đọc số trước/sau. Trên **production**,
nơi mọi phiên chỉ được **CHỈ ĐỌC** (STATE §1).

**Di trú LƯỢC ĐỒ nên tự động; di trú NỘI DUNG thì không.** Cái đầu hoàn nguyên được bằng
`downgrade`; cái sau thì bản gốc **không còn ở đâu** để lấy lại nếu ta không tự cất.

## 2. Bất biến của script — ba cái, cái ① là cái sống còn

**① IDEMPOTENT, và không phải theo nghĩa "chạy lại thì bỏ qua".**
Chạy hai lần mà không chặn ⟹ `encrypt(encrypt(text))`. Giải mã một lần cho ra **chuỗi bản mã**,
đúng kiểu `str`, đúng chỗ — tức **chính xác cái lỗi `crypto_types` vừa vá**, nhưng lần này ta **tự
tay tạo ra nó** và **bản gốc đã bị ghi đè**. Chặn bằng **cùng một phép** `_co_hinh_dang_fernet()`
đã dùng ở `crypto_types` — **không viết phép thứ hai**: hai định nghĩa của cùng một vật sẽ lệch
trong im lặng.

**② Đọc RAW, không qua ORM.** Đọc qua ORM là đã giải mã rồi — ta sẽ mã hoá lại một thứ đã giải mã
và **không nhìn thấy dòng nào đang ở trạng thái nào**. Phải `SELECT` thô, tự phân loại, tự ghi.

**③ Dùng lại `_fernet` của `crypto_types`**, không dựng `Fernet()` mới. Cùng lý do ①.

## 3. DỰ BÁO — điền TRƯỚC

| # | vật | DỰ BÁO | THẬT | |
|---|---|---|---|---|
| 1 | phân bố TRƯỚC (`fin05`) | `giải mã 23 · plaintext 738 · khoá khác 0` | `23 · 738 · 0` | ✅ |
| 2 | số dòng script ĐỘNG VÀO | **738** — đúng bằng rổ plaintext | 738 | ✅ |
| 3 | phân bố SAU | `giải mã 761 · plaintext 0 · khoá khác 0` | `761 · 0 · 0` | ✅ |
| 4 | tổng số dòng `complaints` | **761 trước = 761 sau** | 761 = 761 | ✅ |
| 5 | chạy LẦN HAI | **0 dòng động vào** (idempotent) | *"không còn dòng plaintext nào"* | ✅ |
| 6 | đọc lại và so với bản sao lưu | nội dung **y hệt** | **761/761 khớp, lệch 0** | ✅ |
| 7 | cổng `test_cot_nhom_a…` | **ĐỎ → XANH** | 2 failed → **6 passed** | ✅ |
| 8 | suite `not security_finding` | **569 passed, 0 failed** | **570 passed, 0 failed** | ⚠️ |
| 9 | `src/` | **0 file đổi** | 0 | ✅ |
| 10 | token tiêu | **0** | 0 | ✅ |

**9/10 trúng.** Dòng #8 lệch **+1 ca** (569 → 570, và `deselected` 6 → 7): **không phải do backfill**
— `src/` đổi 0 file, và backfill không đụng `tests/`. Tester đang land song song, tổng số ca thu
thập tăng từ **628** lên **630**. Ghi ra thay vì làm ngơ vì con số lệch **về phía dễ chịu**, và
theo Luật K đó đúng là loại lệch không ai đi truy. **Nguyên nhân đã xác định, không phải suy đoán.**

`security_finding`: **3 failed → 1 failed.** Hai ca biến mất là **đúng hai ca cổng plaintext**; ca
còn lại là P0 live-chat PII đã có từ trước (12/08, `553b9e8`) — khớp đúng phân định tôi đưa ra
trước khi chạy.

## 4. Nếu khác thì nghi gì

| lệch | nghi |
|---|---|
| #1 khác `23/738/0` | 🔴 **DỪNG, KHÔNG CHẠY.** Có người đã đụng dữ liệu giữa chừng. Mẫu số đầu trong git là của lúc 18/08 sáng; nếu nó đã đổi thì tôi đang đọc một quần thể khác |
| #1 cột `khoá khác` > 0 | 🔴 **DỪNG.** Khoá đã bị xoay. Việc phải làm là **khôi phục**, không phải backfill — và backfill lúc này sẽ **ghi đè bản mã cũ bằng bản mã mới**, xoá vĩnh viễn cơ hội khôi phục |
| #2 ≠ 738 | phép phân loại của script khác phép của `crypto_types` ⟹ chúng đã lệch, đúng thứ ① sinh ra để chống |
| #4 khác nhau | script đang **XOÁ hoặc THÊM** dòng — không được phép, revert từ sao lưu |
| #5 ≠ 0 | 🔴 **KHÔNG idempotent** ⟹ đã có mã hoá hai lần ⟹ revert từ sao lưu **ngay**, đừng chạy tiếp |
| #7 ĐỎ → XANH nhưng #6 lệch | 🔴 **Luật J ở dạng tệ nhất**: cổng xanh vì cột hết plaintext, trong khi **nội dung đã hỏng**. Cổng ấy kiểm *hình dạng*, không kiểm *nội dung* — chỉ #6 mới trả lời được |

## 5. Khai trước — điều gì KHÔNG được tính là xác nhận

**Cổng `test_cot_nhom_a…` chuyển XANH KHÔNG chứng minh backfill đúng.** Nó kiểm *"còn dòng nào
trông như plaintext không"* — một script ghi **rác đã mã hoá** vào cả 738 dòng cũng làm nó xanh.
Thứ duy nhất chứng minh là **#6**: đọc lại qua ORM và so **từng dòng** với bản sao lưu.
⟹ Vì thế bản sao lưu **không phải lưới an toàn, nó là DỤNG CỤ ĐO**. Không có nó thì không có phép
kiểm nào phân biệt được *"đã mã hoá đúng"* với *"đã mã hoá một thứ khác"*.

**Và việc này KHÔNG đóng §5.E toàn phần:** nó chỉ chạy trên `fin05`. `fin05ttl`/`fin05do` và
**production** là quần thể riêng, mỗi nơi một quyết định, mỗi nơi một lần sao lưu.

## 6. KẾT QUẢ THẬT — ĐÃ CHẠY, và bốn phép hậu kiểm

```
MẪU SỐ ĐẦU   tổng 761 · đã mã hoá  23 · plaintext 738
SẼ ĐỘNG VÀO  738 dòng
MẪU SỐ SAU   tổng 761 · đã mã hoá 761 · plaintext   0
```
Khoá dùng để ghi: lấy **từ container ngay trong chính lệnh**, sha256 `c3071a75e5fb765ba5a283b3` —
in ra và đối chiếu **trước** khi chạy, vì host không có biến nào để dựa.

### ① Phép kết luận duy nhất — giải mã lại, so TỪNG DÒNG với bản sao lưu

```
bản SAO LƯU (đã phục hồi)  761 dòng
bản THẬT sau backfill      761 dòng
tập complaint_id           GIỐNG NHAU
NỘI DUNG khớp              761 / 761
NỘI DUNG lệch              0
```
So bằng cách giải mã **cả hai bên qua CÙNG hàm `_giai_ma()` của sản phẩm** — không so chuỗi thô,
vì bản gốc là 738 plaintext + 23 đã mã hoá, hai trạng thái khác nhau.

### ② Đọc qua ORM TRONG CONTAINER — đường thật của sản phẩm (PO-agent thêm)

Vòng tròn đo trước đó là **Fernet trần**. Đường sản phẩm là `EncryptedText` → nhánh **ba trạng
thái** mới, chạy bằng **py3.12 trong container**. Đây là chỗ duy nhất còn lại một khác biệt có thể
nấp, và là chỗ **khách hàng thật sự đọc**.

```
đọc TOÀN BỘ 761 dòng qua ORM      761/761 đọc được · 0 rỗng
cảnh báo `doc_gia_tri_chua_ma_hoa`   0        ← trước backfill sẽ là 738
lỗi   `giai_ma_that_bai_nghi_xoay_khoa`  0
⟹ cả 761 dòng đi nhánh "GIẢI MÃ ĐƯỢC"
```
Con số `0` ở dòng cảnh báo là **số duy nhất chứng minh 738 dòng kia đã thật sự đổi trạng thái theo
cách sản phẩm nhìn thấy** — trước backfill nó phải là 738.

### ③ Ca THUẬN LỢI, khai trước và giữ lời (Luật M)

`761 mã hoá / 0 plaintext` **là con số ta muốn nghe**, nên nó **không tự kích hoạt phản xạ soi
lại**. Nó một mình **không phân biệt được** *"mã hoá đúng"* với *"mã hoá một thứ khác"* — chỉ ① và
② phân biệt được, và đó là lý do cả hai được khai **trước** khi chạy chứ không nghĩ ra sau.

### ④ Luật I

```
sửa-tay ba container   0 · 0 · 0
băm cây d5b73a04d6ef == băm ảnh d5b73a04d6ef      ⟹ lệch× 0·0·0
src/ đổi trong lượt này   0 file
```

---

## 7. ĐIỀU KIỆN PO-agent THÊM — sao lưu phải được KIỂM PHỤC HỒI, không chỉ được TẠO

> *"Một bản sao lưu chưa từng được phục hồi thử **không phải một bản sao lưu** — nó là một tệp mà
> ta TIN là bản sao lưu."*

Đây là **KHAI ≠ CHẠY ở chỗ đắt nhất có thể**: một `pg_dump` rỗng/cụt trông y hệt một `pg_dump` tốt
cho tới **đúng lúc ta cần nó**, và lúc đó thì bản gốc đã bị ghi đè. Ba bước, không rút gọn:

```
① dump ra file            → ghi ĐƯỜNG DẪN + KÍCH THƯỚC + SỐ DÒNG vào mục 8
② PHỤC HỒI THỬ vào một CSDL VỨT ĐI     ← KHÔNG phục hồi đè lên bản thật
③ đếm TRÊN BẢN PHỤC HỒI: 761 dòng · 738 plaintext · 23 mã hoá
   khớp mẫu số ĐẦU  ⟹  sao lưu mới được tính là CÓ
```
Nếu ② không làm được: **DỪNG và NÓI**, không đổi ② thành *"tôi tin là được"*.

**Hai điều kiện nữa:**
- **Mẫu số hai đầu đo bằng CÙNG MỘT câu lệnh.** Hai câu lệnh khác nhau cho hai đầu là **hai phép
  đo**, không phải một hiệu số. ⟹ tôi dùng đúng một hàm `dem()`, gọi hai lần.
- 🔴 **Khai trước cả ca THUẬN LỢI (Luật M).** Nếu sau backfill ra `761 mã hoá / 0 plaintext` thì đó
  **đúng thứ ta muốn nghe** — và đó chính là lúc **không gì kích hoạt phản xạ soi lại**. Khai
  trước, ngay đây: **con số đó CHƯA ĐỦ.** Một dòng mã hoá bằng **khoá sai** cũng cho `gAAAAA` và
  cũng làm cổng xanh. Thứ duy nhất kết luận được là **#6**: giải mã lại và so **từng dòng** với bản
  sao lưu.

## 8. SAO LƯU — ĐÃ TẠO **VÀ ĐÃ KIỂM PHỤC HỒI**

### ① Bản sao lưu

```
đường dẫn   <scratchpad>/saoluu/complaints-truoc-backfill-DAY-DU.sql
kích thước  260.828 byte
INSERT      761          (khớp đúng 761 dòng của bảng)
CREATE TABLE 1           ⟹ TỰ ĐỨNG ĐƯỢC, không cần bảng có sẵn
sha256      496087c69ba54626…
```
⚠️ Bản `--data-only` đầu tiên tôi tạo **không tự phục hồi được** (cần bảng tồn tại sẵn). Đã làm
lại bản đầy đủ. Ghi ra vì đó đúng loại "sao lưu mà ta TIN là sao lưu": nó có kích thước, có 761
INSERT, trông hoàn hảo — và **không dùng được một mình**.

### ② PHỤC HỒI THỬ vào CSDL **VỨT ĐI** (`vutdi_kiem_saoluu`, KHÔNG đè lên `fin05`)

```
⚠️ 2 ERROR khoá ngoại: relation "public.transactions" / "public.users" does not exist
   ⟹ ĐÚNG và VÔ HẠI: CSDL vứt đi không có hai bảng kia nên FK không dựng được.
     Bảng + DỮ LIỆU vào đủ. KHÔNG báo cáo đây là "phục hồi sạch" — nó là
     "phục hồi ĐỦ PHẦN TA CẦN", hai câu khác nhau.
```

### ③ ĐẾM TRÊN BẢN PHỤC HỒI — và so **nội dung**, không chỉ so **số đếm**

```
                    bản THẬT      bản PHỤC HỒI
tổng dòng              761            761
plaintext              738            738
đã mã hoá               23             23

so md5(description_raw) TỪNG DÒNG, sắp theo complaint_id:
  761 dòng / 761 dòng  ·  số dòng KHÁC nhau = 0  ⟹ ✅ GIỐNG NHAU TỪNG DÒNG
```
🔴 Bước so md5 từng dòng là bước biến bản sao lưu từ *"một tệp trông đúng"* thành **dụng cụ đo**.
Ba con số đếm ở trên **giống nhau** vẫn có thể che một bản sao lưu chứa 761 dòng **nội dung khác**.

⟹ **SAO LƯU ĐƯỢC TÍNH LÀ CÓ.**

### ④ Xem thử script (`--ghi` KHÔNG bật) — khớp dự báo #1 và #2

```
MẪU SỐ ĐẦU   tổng 761 · đã mã hoá 23 · plaintext 738     ← dự báo #1 ✅
SẼ ĐỘNG VÀO  738 dòng                                    ← dự báo #2 ✅
```
Script mặc định **không ghi một byte nào**; phải có `--ghi` mới chạy thật.

⚠️ **Một bước sai của tôi, khai:** tôi `docker cp` script vào `/tmp` của container để chạy thử
(import hỏng, không chạy được). **Đã chạy `docker diff` ngay: `/app/src` = 0 sửa-tay**, và đã xoá
`/tmp/bf.py`. Đường đúng là chạy từ host với `PYTHONPATH` — đã làm lại thế. Ghi ra theo Luật I:
*trạng thái "đã ghi vào container" phải HIỆN RA, không nằm trong trí nhớ.*

## 9. 🔴 DỪNG Ở ĐÂY — chờ PO-agent gật cho lệnh ghi

Mọi điều kiện đã đủ: dự báo trong git · sao lưu **đã kiểm phục hồi** · mẫu số hai đầu dùng **cùng
một hàm `dem()`** · script mặc định không ghi · ba phép kiểm nằm **trong cùng giao dịch** và
`raise` để rollback thay vì cảnh báo rồi commit.

**Lệnh sẽ chạy khi được gật:**
```
docker exec -w /app fin05-backend-1 python migrations/backfill_ma_hoa_description_raw.py --ghi
```
*(cần dựng lại ảnh để script có mặt ở `/app/migrations/` — hoặc chạy từ host với `PYTHONPATH`,
tôi sẽ hỏi bạn chọn đường nào.)*

## 10. HAI PHÉP KIỂM PO-agent ĐÒI TRƯỚC KHI GẬT — cả hai XANH

### ① KHOÁ — so BYTE, không so "chắc là giống"

```
FIELD_ENCRYPTION_KEY  từ Config.Env container   44 byte · sha256 c3071a75e5fb765ba5a283b3
FIELD_ENCRYPTION_KEY  do src.config đọc ra      44 byte · sha256 c3071a75e5fb765ba5a283b3
⟹ GIỐNG TỪNG BYTE ✅

FIELD_ENCRYPTION_KEY trên HOST                  <KHÔNG ĐẶT>
```
🔴 **Vế thứ hai mới là vế quan trọng, và nó xác nhận đúng rủi ro PO-agent nêu:** host **không có
sẵn khoá nào**. Nghĩa là mọi lệnh chạy từ host **bắt buộc** phải lấy khoá **từ container** — và nếu
ai đó theo phản xạ gõ `Fernet.generate_key()` (đúng thứ tôi làm suốt buổi cho **test**, nơi nó vô
hại) thì đó là **ghi đè 738 dòng bằng một khoá không ai giải được**.
⟹ Lệnh chạy thật **phải mang khoá lấy từ container ngay trong chính lệnh đó**, không dựa vào biến
môi trường có sẵn — vì **không có biến nào có sẵn**.

### ② VÒNG TRÒN py3.14 ↔ py3.12 — biến *"tôi không nghĩ có khác biệt"* thành phép đo

Mẫu: **chuỗi tiếng Việt có dấu**, 128 byte UTF-8, có `đ`/`—`/số tiền/SĐT/mã GD — **không** dùng
ASCII, vì hôm nay đã có một ca bộ dò mù đúng phần tiếng Việt (§5.J).

```
py host      3.14.6   cryptography 50.0.0
py container 3.12.14  cryptography 50.0.0      ← CÙNG phiên bản thư viện, khác bản Python

① host (3.14) mã hoá  →  container (3.12) giải  →  == gốc, SO BẰNG BYTE: True (128/128)
② container (3.12) mã hoá  →  host (3.14) giải  →  == gốc, SO BẰNG BYTE: True (128/128)
③ `_co_hinh_dang_fernet`  container: True/False  ·  host: True/False   ← HAI BÊN ĐỒNG Ý
```
🔴 **Chiều đúng của phép thử** (PO-agent nêu, tôi ghi lại vì nó dễ làm sai): thứ cần chứng minh
**không phải** *"hai bên sinh ra token giống nhau"* — không thể, IV ngẫu nhiên — mà **"bên kia ĐỌC
ĐƯỢC thứ bên này ghi"**. Đo cả hai chiều, vì backfill ghi từ host còn sản phẩm đọc từ container.

⟹ **Chạy từ HOST là an toàn.** Không dựng lại ảnh cho một script chạy một lần, và `docker cp` đã bị cấm.
