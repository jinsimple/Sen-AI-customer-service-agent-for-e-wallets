# DỰ BÁO — cổng nghiệm thu backfill (ADR-032 việc ②)

> Vai: **tester** · 18/08, sau lần dựng ảnh · **0 token** · viết **TRƯỚC** khi
> đo. Mốc vật: **`bam_ma_nguon = d5b73a04d6ef`**.
> 🔴 **KHÔNG dùng `BUILD_COMMIT`** — PO-agent [ĐO] nhãn `bf1bd5a` **khác** mã
> đang chạy (ảnh dựng từ **cây làm việc**, không từ HEAD). Đúng vế thi hành
> Luật P: *đừng thay một con số chết bằng một con số dễ đọc nhầm.*

## ① Dữ kiện: script backfill CHƯA TỒN TẠI

`migrations/` không có file nào mới; `git log --all --grep=backfill` không có
commit nào của đợt này. ⟹ Cổng này viết **trước** vật nó nghiệm thu — nó **định
nghĩa điều backfill phải thoả**, không mô tả điều backfill đã làm.

🔴 **Và điều đó làm một việc thành KHẨN:** mẫu số **"sau"** đo lúc nào cũng
được; mẫu số **"trước"** chỉ đo được **trong cửa sổ từ giờ tới lúc backfill
chạy**. Bỏ lỡ cửa sổ này thì ADR-032 việc ② **vĩnh viễn không nghiệm thu được**
theo đúng yêu cầu *"đếm phân bố trước/sau"* của chính nó.

## ② 🔴 VÌ SAO "0 dòng plaintext" MỘT MÌNH LÀ CỔNG HỎNG

Cổng `test_cot_nhom_a_khong_nam_plaintext` (`b2825db`) đã khẳng định *"không
dòng nào nằm trần"*. **Một backfill chạy `DELETE FROM complaints` sẽ làm nó
XANH.** Đây là Luật 1 ở dạng nguy hiểm nhất: **bản cài đặt tầm thường nhất thoả
mãn assertion**.

Bốn kiểu hỏng mà "0 plaintext" **không** bắt được:

| # | kiểu hỏng | vì sao lọt |
|---|---|---|
| 1 | **mất dòng** (xoá/bỏ qua) | ít dòng hơn ⟹ vẫn 0 trần |
| 2 | **mất nội dung** (mã hoá một chuỗi rỗng) | đúng hình dạng `gAAAAA`, ruột rỗng |
| 3 | **mã hoá HAI LẦN** (dòng đã mã hoá bị mã hoá lại) | 🔴 hình dạng **không phân biệt được** — token bọc trong token |
| 4 | **mã hoá bằng khoá KHÁC** | hình dạng đúng, **không ai đọc được nữa** |

⟹ Cổng nghiệm thu phải bám **BỐN** mốc, không phải một: **số dòng · giải mã
được · không bọc hai lần · nội dung không đổi.**

## ③ Cách đo — hộp đen, KHÔNG đọc `src/`, KHÔNG in nội dung

Dùng `cryptography.fernet` **thẳng** trong container với `FIELD_ENCRYPTION_KEY`
của chính container. Đây là **thư viện công khai + biến môi trường**, không phải
đọc mã sản phẩm. Ba trạng thái tự rơi ra:

```
decrypt OK                        → giải mã được
InvalidToken  + mở đầu gAAAAA     → KHOÁ KHÁC
InvalidToken  + không mở đầu      → chưa mã hoá (plaintext)
decrypt OK NHƯNG ruột mở đầu gAAAAA → 🔴 BỌC HAI LẦN
```

**Nội dung không đổi — đo bằng VÂN TAY GỘP, không lưu vân tay từng dòng:**
`md5` mỗi bản rõ → sắp xếp → `md5` của chuỗi nối. Một con số cho cả cột.
🔴 **Cố ý KHÔNG lưu băm theo dòng:** băm của một câu ngắn là thứ **dò ngược
được**, và một tệp trong git chứa 761 băm lời khai khách là một tài sản PII mới
do chính bộ đo tạo ra — đúng Luật 10 (*bộ đo tự tạo ra hiện tượng nó đang đo*),
ở trục rủi ro thay vì trục kết quả. Vân tay gộp trả lời đúng câu cần hỏi
(*"tập nội dung có đổi không"*) và **không trả lời được** câu không nên hỏi.

## ④ Đối chiếu mẫu số ĐẦU của tech-lead — kiểm thành phần, không nhận số

PO-agent chuyển: `1.113 giải mã được / 738 chưa mã hoá / 0 khoá khác`.
Tôi **không nhận con số**, tôi kiểm nó **cộng lại từ đâu**:
```
messages.content        467
policy_chunks.text      378
bank_accounts.account_no 245
complaints.description_raw 23
                     ─────
                      1.113  ✅ khớp
```
⟹ `1.113` là mẫu số của **cả bốn cột Nhóm A**, không phải của riêng
`complaints`. Số của tôi (`738 trần / 23 mã hoá` **trên `complaints`**) và số
của họ **cùng một sự thật, hai mẫu số khác nhau**. Ghi rõ để không ai trừ chéo.

## ⑤ DỰ BÁO

| # | dự báo | độ chắc | nếu khác thì nghi gì |
|---|---|---|---|
| 1 | `complaints.description_raw` vẫn **738 trần / 23 giải mã được** | **rất cao** | khác ⟹ **ai đó đã chạy backfill mà không báo** — DỪNG, hỏi, đừng ghi "đã vá" |
| 2 | **0** dòng khoá khác, cả bốn cột | **cao** | >0 ⟹ khoá đã bị xoay ⟹ finding nặng hơn ADR-032 |
| 3 | **0** dòng bọc hai lần, cả bốn cột | **cao** | >0 ⟹ đã có một lần backfill/di trú chạy hai lần trong quá khứ |
| 4 | tổng bốn cột: **1.113 giải mã được** | **cao** | lệch ⟹ số của tech-lead đo trên ngăn xếp khác, hoặc đã đổi |
| 5 | container **thật sự** chạy nhánh ba trạng thái | **trung bình** | 🔴 tôi **tự kiểm**, không nhận lời — đây đúng cạm bẫy tôi đã ghi vào sổ hôm 12/08 |

🔴 **Khai trước:** dự báo 1 TRÚNG nghĩa là **chưa có gì được vá** — đó là kết
quả **đúng** cho lúc này, không phải tin xấu. Cổng này sinh ra để **đỏ cho tới
khi backfill chạy**, giống cổng plaintext.

## ⑥ Điều cổng này KHÔNG chứng minh

- **Không** chứng minh nội dung *đúng nghiệp vụ* — chỉ chứng minh nó **không
  đổi** giữa hai lần đo. Backfill làm hỏng dữ liệu **trước** lần đo đầu thì
  cổng này im.
- **Không** phủ 10 cột `json`/`jsonb`/`bytea` (kho checkpoint) — phạm vi đó đã
  được PO chốt là **ADR riêng**.
- Vân tay gộp bảo *"tập có đổi"*, **không** bảo *"dòng nào đổi"*. Đó là đánh
  đổi **cố ý** đã nêu ở ③.

---

# ⑦ KẾT QUẢ THẬT — ghi SAU khi đo. Dự báo nằm ở `3cd0dbc`.

```
nền chốt lúc  2026-08-18 02:40:29 UTC   ·  bam_ma_nguon d5b73a04d6ef
tệp nền       eval/NEN-TRUOC-BACKFILL-2026-08-18.json
```

| # | dự báo | thực tế | |
|---|---|---|---|
| 1 | `complaints` vẫn 738 trần / 23 giải mã được | **738 / 23** | ✅ |
| 2 | 0 dòng khoá khác, cả bốn cột | **0 / 0 / 0 / 0** | ✅ |
| 3 | 0 dòng bọc hai lần, cả bốn cột | **0 / 0 / 0 / 0** | ✅ |
| 4 | tổng bốn cột 1.113 giải mã được | **245+467+378+23 = 1.113** | ✅ |
| 5 | container thật sự chạy nhánh ba trạng thái | **chỉ xác minh GIÁN TIẾP** | ⚠️ xem ⑨ |

**4/5 trúng · 1 ô chỉ xác minh được gián tiếp và tôi hạ nó xuống đúng hạng.**

## ⑧ 🔴 PHÉP ĐỐI CHỨNG BÁC CHÍNH TÔI — "chỉ đọc" vẫn GHI

Tôi định báo cáo số ngay sau khi đo. Vế thi hành Luật I bắt chạy `docker diff`
**trước khi báo bất cứ số nào** — nên tôi chạy, và nó **không rỗng**.

Giả định của tôi: *"lệnh `SELECT` qua `docker exec python -c` là chỉ đọc."*
Phép phân định: chạy **cùng lệnh** trên `fin05ttl-backend-1`, container tôi
**chưa hề chạm**, đo `docker diff` hai đầu:

```
TRƯỚC 80  →  SAU 181   Δ = +101      🔴 giả định SAI
124/125 mục mới nằm ở /usr/local/lib/python3.12/**/__pycache__
```
**Nhập một thư viện là biên dịch nó.** `import sqlalchemy` ghi bytecode cache.

**Bản vá, xác minh trên container THỨ BA (`fin05do`, cũng chưa chạm):**
```
docker exec -e PYTHONDONTWRITEBYTECODE=1 …   TRƯỚC 287 → SAU 287   Δ = 0  ✅
```

### Vì sao đây không phải chuyện nhỏ

101 tệp `.pyc` **không hỏng dữ liệu** và **không đổi hành vi**. Cái nó hỏng là
**CÁI BẪY**: `docker diff` là dây báo động của cả đội cho câu *"phép đo có chạm
vật không"*. Một phép đo tự thêm 101 dòng nhiễu khiến **lần dò tampering sau
phải bới qua nhiễu của chính mình** — và một thay đổi thật sẽ nấp trong đó.

> **Bộ đo làm MÙ chính dụng cụ dùng để canh bộ đo.** Luật 10 (*bộ đo tự tạo ra
> hiện tượng nó đang đo*), nhưng ở trục **dụng cụ giám sát** thay vì trục kết quả.

**Đã vá cả hai nơi dùng khuôn này** trong vùng tester: cổng nghiệm thu mới, và
`tests/test_rag/test_thanh_phan_tai_lieu_kho.py` (`docker exec … python -c`
tôi viết sáng nay — **nó đã rò suốt từ lúc đó**). Cả hai nay đo Δ=0.

⚠️ **Còn nơi khác tôi KHÔNG vá được:** `docker exec … pytest /app/tests` ghi
**121 tệp** vào `fin05-backend-1` (`.pytest_cache/` + `src/**/__pycache__`,
dấu thời gian `02:31`). Đó là **lượt nghiệm thu ảnh của PO-agent**, không phải
của tôi — nêu ra vì nó cùng một cơ chế và **`PYTHONDONTWRITEBYTECODE=1` không
chữa được `.pytest_cache`** (cần `-p no:cacheprovider`). Đây là lý lẽ định
lượng cho món *"container lint/test riêng"* đang nằm trong `STATE §5.B`.

## ⑨ Ô số 5 — hạ hạng, không tự nâng

Tôi **không xác minh trực tiếp được** rằng container chạy nhánh giải mã ba
trạng thái: làm thế cần đọc `src/db/crypto_types.py`, mà tester **không được
đọc `src/`**. Thứ tôi xác minh được, bằng **siêu dữ liệu**:
- `git merge-base --is-ancestor c079323 HEAD` → **đúng**, commit vá nằm trong cây
- `git show --stat` → nó chạm đúng **`src/db/crypto_types.py`** (đọc TÊN, không mở)
- PO-agent [ĐO] độc lập: `bam_ma_nguon` khớp cả bốn chỗ ⟹ ảnh mang đúng cây đó

⟹ Phát biểu đúng hạng: ***"ảnh mang cây có chứa commit tự khai là bản vá ba
trạng thái"*** — **KHÔNG** phải *"đã xác minh nhánh ba trạng thái hoạt động"*.
Khoảng cách giữa hai câu ấy chỉ đóng được bằng một phép thử **hành vi**, và
phép thử đó cần một lượt đọc qua ORM. **Ghi là CHƯA XÁC MINH.**

## ⑩ Cổng — hai nửa, và phép đột biến

```
🟢 test_backfill_khong_lam_mat_dong_hay_doi_noi_dung   ← cổng chính, XANH NGAY
🔴 test_cot_nhom_a_da_duoc_nap_lai_het                 ← security_finding, cố ý đỏ
```
Tách vì **Luật J**: nửa trên canh được **ngay hôm nay** (nó là nửa bắt một
backfill làm mất dữ liệu); gộp rồi gắn nhãn thì nó biến mất khỏi `lint-and-test`.

**Đột biến trên tệp nền — hai kiểu hỏng, hai câu khác nhau:**
```
"tong" 761→762        ⟹ "MẤT/THÊM DÒNG trong tập đã đóng băng — nền 762 → nay 761"
vân tay → 0000…       ⟹ "NỘI DUNG ĐỔI — vân tay 0000000000000000 → 2805e52d1a4d0bed"
hoàn nguyên: băm khớp lại 71204425330e
```
⟹ nửa xanh **biết đỏ**, và **phân biệt được hai kiểu hỏng** thay vì gộp thành
"khác nền". Đúng Luật 16: N mệnh đề cần N đột biến.

---

# ⑪ SAU BACKFILL — gỡ nhãn, và đọc lại CỔNG KHẲNG ĐỊNH CÁI GÌ (Luật J)

Backfill land `5939b6a`. **Tôi đo lại bằng phép của mình, không nhận số relay:**

```
fin05      ma_hoa=761              ← 738 trần → 0
fin05ttl   ma_hoa=4   tran=738     ← 🔴 CÒN NGUYÊN
fin05do    ma_hoa=607              ← sạch vì HẠT GIỐNG SINH SAU, không do backfill
production ——                      ← CHƯA AI ĐO
```
🔴 **BỐN quần thể, đừng gộp.** `fin05do` sạch **không phải bằng chứng backfill
tốt** — nó chưa bao giờ bẩn. Đọc nó thành "hai ngăn xếp đã sạch" là **dân số
pha tạp**, đúng lớp lỗi §8.

**Cổng nay khẳng định gì** — đọc, không chỉ ghi nhận màu:
```
tong        761  (không đổi)      ⟹ không mất dòng
vân tay gộp 2805e52d1a4d0bed (không đổi) ⟹ NỘI DUNG BẢO TOÀN, không bị thay
                                            bằng thứ khác cho đúng hình dạng
chua_ma_hoa 738 → 0 · khoa_khac 0 · boc_hai_lan 0
```
Vân tay không đổi là mốc **không ai đặt ra trước** khi tôi viết cổng: nó phân
biệt *"đã mã hoá"* với *"đã mã hoá ĐÚNG THỨ CŨ"*.

## ⑫ Ca đối chứng dương — thứ cổng này THIẾU cho tới hôm nay

Cổng chuyển ĐỎ → XANH nhờ backfill. **Nhưng không ai chứng minh nó CÒN BIẾT ĐỎ.**
Nửa *"im lúc bình thường"* có rồi; nửa *"KÊU lúc bất thường"* thì trống — và
Luật A nói nửa sau **chỉ chứng minh được bằng ca đối chứng**.

Cách rẻ nhất trông có vẻ là nhét một dòng plaintext giả vào CSDL. **Không làm** —
ghi vào ngăn xếp đang phục vụ (Luật I).

**Không cần.** `fin05ttl` **chưa được nạp lại** ⟹ đó là một **quần thể bẩn có
thật, sẵn có, không do ta tạo ra**. Chĩa đúng phép đo ấy sang đó thì cổng phải
kêu. Xác minh **hai chiều**:
```
chĩa vào fin05ttl (bẩn)  → PASSED       ← cổng KÊU đúng
chĩa vào fin05   (sạch)  → "KHÔNG ĐO ĐƯỢC … mất quần thể bẩn để chứng minh
                            cổng biết KÊU. Đừng bỏ ca này."
```
Chiều thứ hai là phần quan trọng: ngày `fin05ttl` cũng được nạp lại, ca này
**báo mất khả năng đối chứng** thay vì lặng lẽ xanh.

## ⑬ Trạng thái hai job CI, đo ở host

```
-m "not security_finding"   577 passed · 42 skipped · 1 deselected · 11 xfailed   ✅
-m "security_finding"       1 failed  ← P0 live-chat, file sửa lần cuối 12/08
docker diff quanh mọi lượt đo:  Δ = 0
```
Ca đỏ còn lại **không phải hồi quy** — nó đã đỏ từ trước và **phân định ấy được
đưa ra TRƯỚC khi backfill chạy**, không phải giải thích sau.

## ⑭ Một chỗ tôi suýt báo sai, ghi lại vì nó đúng lớp lỗi cả ngày

Lệnh chạy suite của tôi **vượt hạn hai lần** (2 phút, rồi 7 phút). Phản xạ đầu
là *"bộ ca treo sau bản vá của tôi"*. Chạy lại có mốc thời gian: **`exit 0`,
`577 passed` trong `106s`** — cái vượt hạn là **cửa sổ lệnh của tôi** (tôi nhét
**hai** lượt quét toàn suite vào một lệnh), không phải bộ ca.

> **"Lệnh của tôi hết giờ" ≠ "thứ tôi đo bị treo".** Suýt nữa tôi báo một kết
> luận thay vì một triệu chứng — đúng Luật H, lần thứ tư trong ngày, lần này
> là tôi.
