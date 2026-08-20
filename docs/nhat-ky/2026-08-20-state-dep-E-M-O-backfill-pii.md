# Lưu trữ — §5.E, §5.M, §5.O (saga backfill `complaints.description_raw`) chuyển từ `docs/STATE.md`

> Dọn theo §7b (Lead thực hiện 20/08, PO-agent đo lại độc lập trước khi cho đóng). Chuỗi ba mục
> (phát hiện → vá → đính chính phạm vi) ĐÃ ĐÓNG bằng một quyết định của PO-agent 20/08: `fin05ttl`
> là ngăn xếp dùng-một-lần, dữ liệu tổng hợp (`gen_dataset.py --seed 20260802`), không có khách
> thật ⟹ không phát sinh nghĩa vụ PDPA, cố ý không mã hoá. Dòng khai thay thế còn lại trong
> `STATE.md`. Toàn văn ba mục gốc giữ dưới đây.

## Vì sao đóng — [ĐO] PO-agent 20/08, sau khi tự chạy lại cả ba ngăn xếp

```
fin05      0/786   sạch  ✅
fin05do    0/607   sạch  ✅
fin05ttl   738/742 THÔ   ❌   ← đúng y con số §5.O giữ, xác nhận claim CÒN ĐÚNG
```

Câu hỏi treo cuối §5.O (*"`fin05ttl`/`fin05do` dùng-một-lần hay cần bảo vệ như `fin05`?"*) trả lời
được: **KHÔNG cần bảo vệ như `fin05`** — dữ liệu cả ba ngăn đều sinh từ `gen_dataset.py --seed
20260802`, không có khách thật, nghĩa vụ PDPA không phát sinh. Đây không phải nợ bảo mật.

**Rủi ro còn sống, khác hẳn dạng cũ:** một ngăn mang dữ liệu **hình dạng giống production** ở trạng
thái thô, cạnh hai ngăn đã mã hoá — ai đo nhầm ngăn sẽ kết luận sai "backfill hỏng". Đây là lý do
giữ một dòng khai trong `STATE.md` thay vì xoá trắng: *"`fin05ttl` là ngăn dùng-một-lần, dữ liệu
tổng hợp, cố ý không mã hoá"* — chuyển từ "nợ chưa xử" sang "trạng thái đã khai".

⚠️ **Không đảo quyết định giữ `fin05ttl` làm tài sản kiểm thử** (xem §5.O gốc, đoạn "VÀ `fin05ttl`
NAY LÀ TÀI SẢN KIỂM THỬ") — nạp lại nó sẽ TẮT ca đối chứng duy nhất chứng minh cổng plaintext còn
sống. Quyết định đó vẫn đứng, độc lập với việc đóng mục này.

---

## 🔴🔴 E. PHÁT HIỆN NẶNG NHẤT 18/08 — cột Nhóm A KHÔNG được mã hoá trên 97% số dòng

*(Bắt bởi **PO-agent**, trong lúc kiểm lại một phát biểu của **security** trước khi relay cho PO thật.
Security báo `complaints.description_raw` **đã mã hoá**; số không khớp, và lệch về hướng **nặng hơn**.)*

**Security phát biểu** (hồ sơ 18/08): *"`complaints.description_raw` → `gAAAAABq…` **MÃ HOÁ**"*, và
dựng finding ① trên khung *"cột đã mã hoá đang có một BẢN SAO plaintext ở bảng khác."*

**[ĐO] PO-agent, `psql` thẳng vào `fin05-postgres-1`, đếm ĐỦ dân số:**

```
complaints.description_raw     PLAINTEXT  738   tạo 05/05/2026 → 14/08/2026
                               MÃ HOÁ      23   tạo 15/08/2026 → 17/08/2026
                               ⟹ 738/761 = 97% NẰM PLAINTEXT TRÊN ĐĨA

messages.content               MÃ HOÁ     467   tạo 11/08 → 16/08   (467/467 = 100%)
```

⟹ **Khung của finding ① SAI, và sai về phía trấn an.** Không phải *"lớp mã hoá bị đi vòng"* —
**bản thân cột ấy chưa từng được mã hoá cho dữ liệu có sẵn.** `EncryptedText` được gắn vào
`models.py:274` khoảng **15/08** và **738 dòng cũ chưa bao giờ được nạp lại**. `messages` không
dính vì bảng ấy chỉ có dữ liệu từ 11/08 và mã hoá từ đầu.

🔴 **VÌ SAO KHÔNG AI THẤY — `src/db/crypto_types.py:59-65`:**

```python
def process_result_value(self, value, dialect):
    try:
        return _fernet.decrypt(value.encode()).decode()
    except InvalidToken:
        return value          # ← nuốt IM LẶNG, trả nguyên văn
```

Nhánh lỗi **trả về thứ trông y hệt một lần đọc thành công**. Ứng dụng đọc 738 dòng plaintext ấy
**không một lỗi nào**, không một dòng log nào. **Luật H ở dạng mạnh nhất từng gặp:** các ca trước
nhánh lỗi *in ra kết luận*; ca này nhánh lỗi **không in gì cả** — nó **giả trang thành thành công**.
Và **Luật G**: cơ chế đang làm **đúng việc của NÓ** (tương thích ngược lúc di trú), ta đọc nó thành
một thứ rộng hơn (*"cột này được mã hoá"*).

🔴 **HỆ QUẢ THỨ HAI, chưa ai nêu — nó làm cảnh báo §1 về `FIELD_ENCRYPTION_KEY` NGHIÊM TRỌNG HƠN.**
§1 ghi *"KHÔNG xoay khoá nếu chưa có script mã hoá lại — xoay là mất vĩnh viễn"*. Với nhánh nuốt
lỗi này, xoay khoá **không báo lỗi**: 23 dòng đã mã hoá sẽ `InvalidToken` → **trả về nguyên chuỗi
`gAAAAA…`** như thể đó là nội dung khiếu nại. **Không mất dữ liệu ồn ào — mà hỏng dữ liệu IM LẶNG.**

**[ĐO] 18/08 bổ sung — security kiểm CẢ HỌ cột, bước PO-agent đã bỏ sót. Tin TỐT:**

```
cột khai Encrypted*          MÃ HOÁ   PLAINTEXT
messages.content               467        0     ✅
policy_chunks.text             378        0     ✅
bank_accounts.account_no       245        0     ✅
complaints.description_raw      23      738     🔴  ← DUY NHẤT
```
⟹ **Nợ khu trú ở ĐÚNG MỘT cột. Hệ thống mã hoá KHÔNG hỏng.** `description_raw` là cột **mới nhất**
được gắn kiểu, gắn lên một bảng **đã có 738 dòng**. Việc sửa gói trong **một script backfill**, không
phải một cuộc rà soát toàn hệ thống.

🔴 **[ĐO] PHÉP ĐO DỨT ĐIỂM — §5.E và finding ① là HAI LỖ KHÁC LOẠI, không phải một lỗ hai triệu chứng.**
Ghép 27 dòng `create_ticket` với chính `complaint` của chúng:

```
13/08  gốc PLAINTEXT  6      15/08  gốc MÃ HOÁ  3
14/08  gốc PLAINTEXT  5      16/08  gốc MÃ HOÁ  8
                             17/08  gốc MÃ HOÁ  5
⟹ 16/27 dòng có BẢN GỐC ĐÃ MÃ HOÁ ĐÚNG và một BẢN SAO PLAINTEXT NẰM CẠNH
```
Với 16 dòng ấy, cơ chế ADR-025 **đã chạy, đã đúng, và vẫn bị đi vòng trong cùng một giao dịch**.

| | **§5.E** | **finding ① (`tool_input_json`)** |
|---|---|---|
| loại | **nợ MIGRATE** — cơ chế có, đúng, đang chạy | **thiếu CƠ CHẾ** — chưa từng có gì |
| ghi mới hôm nay | ✅ được mã hoá | 🔴 **vẫn sinh plaintext, mỗi lượt** |
| sửa bằng | script backfill, chạy MỘT LẦN | một **quyết định thiết kế** |
| sau khi sửa lỗ kia | — | **vẫn nguyên** |

> **§5.E là VŨNG NƯỚC — tát một lần là hết. Finding ① là VÒI ĐANG CHẢY — không script nào đóng được.**
> ⟹ **Vá §5.E làm ① nặng thêm về mặt TƯƠNG ĐỐI:** backfill xong, `complaints` sạch 100% ⟹
> `investigation_logs` thành **bản plaintext DUY NHẤT còn lại của lời khai khách**.

🔴 **THỨ TỰ BẮT BUỘC — mục 1 đứng trước mục 2 KHÔNG phải vì nó rẻ hơn:**
**nếu backfill chạy trước, phép nghiệm thu của chính nó đi qua đúng nhánh đang nói dối** — một dòng
backfill hỏng sẽ đọc ra nguyên văn và **trông y hệt một dòng thành công**. **Sửa cái đèn trước khi soi.**
Cơ chế phân biệt rẻ và tin được: `gAAAAA` là dấu hiệu của Fernet token (byte phiên bản `0x80` →
base64url luôn mở đầu `gA`) ⟹ *bắt đầu bằng `gAAAAA` mà decrypt hỏng* = **SAI KHOÁ, ném lỗi, KHÔNG
nuốt**; *ngược lại* = plaintext cũ, trả nguyên văn. **Phải land TRƯỚC mọi thao tác xoay khoá.**

**Ba việc, KHÔNG gộp làm một:**
1. `src/` — nhánh `except InvalidToken` phải **phân biệt ba trạng thái** (giải mã được · chưa mã hoá ·
   mã hoá bằng khoá khác), không phải hai. Đúng Luật H: *luôn là BA trạng thái.*
2. `migrations/` — script nạp lại 738 dòng. **Chưa tồn tại.**
3. `docs/security/` — security phải **đánh giá lại finding ①** trên dân số đúng: bản sao plaintext ở
   `investigation_logs` là **lỗ thứ hai**, không phải lỗ duy nhất, và **không phải lỗ lớn nhất**.

> ⚠️ **NẾP KIỂM, ghi lại vì nó vừa hiệu quả lần thứ hai trong ngày:** security trích **3 dòng mẫu**
> và đọc ra *"đã mã hoá"*. Ba dòng ấy tình cờ nằm trong **23 dòng mới**. PO-agent hỏi **MẪU SỐ**
> (`GROUP BY` trên toàn bảng) thì bức tranh **lật ngược**. Đúng §8: *tập tự đến đã bị lọc rồi* — lần
> này bộ lọc là **`LIMIT 3` mặc định trả về dòng mới nhất.**

---

## ✅ M. ADR-032 ② BACKFILL ĐÃ CHẠY — nghiệm thu độc lập ĐẠT. §5.E đóng MỘT PHẦN

**PO-agent kiểm bằng phép của mình, sau khi tech-lead làm đủ ①→④:**
```
[ĐO] psql thẳng, GROUP BY toàn bảng   complaints.description_raw: MÃ HOÁ 761 · PLAINTEXT 0
[ĐO] đọc qua ĐƯỜNG SẢN PHẨM (container py3.12, ORM, nhánh ba trạng thái):
       tổng đọc được        761
       rỗng                   0
       CÒN dạng gAAAAA        0   ← >0 nghĩa là giải mã HỎNG, trả nguyên bản mã
[ĐO] sửa-tay 0·0·0 · băm cây == băm ảnh d5b73a04d6ef · lệch× 0·0·0
```
**738 → 0.** Cột Nhóm A nặng nhất nay mã hoá 100% trên `fin05`.

🔴 **PHÉP QUYẾT ĐỊNH KHÔNG PHẢI CON SỐ `761/0`** — nó là con số **ta muốn nghe**, và theo **Luật M**
đó là lúc không gì kích hoạt phản xạ soi lại. Hai phép dưới mới phân định, và **cả hai được khai
TRƯỚC khi chạy**, không nghĩ ra sau:
- **① so TỪNG DÒNG với bản sao lưu:** `761/761 khớp · 0 lệch`. Chi tiết làm nó có nghĩa: **giải mã CẢ
  HAI bên qua cùng `_giai_ma()` của sản phẩm**, không so chuỗi thô — bản gốc là *738 plaintext + 23 đã
  mã hoá*, so thô sẽ cho 738 "lệch" và dẫn người ta đi chữa một thứ không hỏng.
- **② đọc qua ORM trong container** *(phép PO-agent thêm)*: cảnh báo `doc_gia_tri_chua_ma_hoa`
  **738 → 0**, lỗi `giai_ma_that_bai_nghi_xoay_khoa` **0**.
  🔴 **Đây là số duy nhất chứng minh 738 dòng đổi trạng thái THEO CÁCH SẢN PHẨM NHÌN THẤY** — mọi số
  khác đều đo bằng script của tech-lead, trên Python của tech-lead. Thiếu phép này thì toàn bộ báo cáo
  là *"dụng cụ của tôi nói dụng cụ của tôi đúng"*.
  ⭐ Và nó là **ca đối chứng TỰ NHIÊN** cho nhánh ba trạng thái land sáng nay: `738 → 0` là chuỗi thời
  gian ngắn nhất chứng minh **cả cơ chế lẫn bản vá** cùng hoạt động.

**Hai điều kiện PO-agent thêm đã bắt được HAI lỗi thật, trước khi ghi:**
1. *"Sao lưu phải được KIỂM PHỤC HỒI, không chỉ được tạo"* → bản `pg_dump --data-only` đầu tiên có đủ
   761 INSERT, kích thước đẹp, băm đẹp — **và không tự phục hồi được**.
2. *"So BYTE khoá host với khoá container"* → [ĐO] host **KHÔNG có `FIELD_ENCRYPTION_KEY`**; phản xạ
   mặc định cả buổi chiều là `Fernet.generate_key()`. Ở đây nó là **ghi đè 738 dòng bằng khoá không ai
   giải được**.
> 🔴 **Cả hai thuộc CÙNG MỘT LỚP, và tech-lead gọi đúng tên nó:**
> ***"thứ tôi đã làm đúng 20 lần hôm nay ở một ngữ cảnh mà nó vô hại"***. Hai điều kiện ấy **không bắt
> sự cẩu thả** — chúng bắt **một thói quen ĐÚNG bị mang sang chỗ nó SAI**. Đó là lý do chúng đáng tồn
> tại kể cả khi người thao tác đang rất cẩn thận.

**Quyết định thiết kế giữ lại — đừng ai đảo:** **KHÔNG làm alembic revision.** Entrypoint chạy
`alembic upgrade head` **mỗi lần container khởi động, trên cả ba ngăn xếp VÀ production** ⟹ revision
hoá nghĩa là **738 dòng lời khai khách bị viết đè tự động, không ai bấm nút**.
> ***Di trú LƯỢC ĐỒ nên tự động; di trú NỘI DUNG thì không.***
Và ba phép kiểm sau khi ghi nằm **trong cùng giao dịch, `raise` để rollback** — *một script ghi dữ
liệu mà chỉ CẢNH BÁO khi phát hiện sai là script đã ghi rồi mới nói.*

🔴 **CHƯA ĐÓNG — §5.E đóng ĐÚNG MỘT PHẦN:**
- Backfill **chỉ chạy trên `fin05`**. **`fin05ttl` · `fin05do` · PRODUCTION là BA QUẦN THỂ RIÊNG**,
  mỗi nơi **một quyết định, một lần sao lưu**. tech-lead **không tự mở rộng** — đúng.
- **ADR-032 ③** (cổng trong `tests/`) thuộc tester.
- **CSDL `vutdi_kiem_saoluu` GIỮ LẠI** — nó là bản phục hồi **đã kiểm**, và là **đường lùi duy nhất còn
  lại**. Xoá khi PO thấy đủ an toàn.
- **§5.J (kho checkpoint) KHÔNG bị đụng tới** — và nay nó thành **bản plaintext DUY NHẤT còn lại của
  lời khai khách**, đúng như security dự đoán: *vá vũng nước làm vòi chảy lộ ra rõ hơn.*

⚠️ **Dự báo 9/10 — dòng lệch tech-lead TRUY thay vì làm ngơ, và lệch về phía DỄ CHỊU:** `not
security_finding` dự báo 569, thật **570** (tổng ca thu thập 628→630 vì **tester land song song**).
`src/` đổi 0 file, backfill không đụng `tests/`. **Luật K:** lệch về phía nhiều-ca-xanh-hơn là loại
lệch **không ai đi truy** — họ truy vì *"nếu nó lệch xuống 568 thì tôi đã truy ngay"*.

---

## 🔴🔴 O. ĐÍNH CHÍNH §5.M — "738 → 0" ĐÚNG CHO MỘT NGĂN XẾP, KHÔNG ĐÚNG CHO HỆ THỐNG

*(Ô `O` chỉ bỏ trống ở **SỔ LUẬT §7**, không ở đây — hai không gian tên khác nhau.)*
*(Bắt ĐỘC LẬP bởi **security** và **tester**, cùng lúc, không ai biết việc của ai. PO-agent kiểm lại.)*

```
[ĐO] complaints.description_raw, cả ba ngăn xếp cục bộ:
     fin05      mã hoá 761  ·  PLAINTEXT   0   ✅ đã backfill
     fin05ttl   mã hoá   4  ·  PLAINTEXT 738   🔴 NGUYÊN VẸN
     fin05do    mã hoá 607  ·  PLAINTEXT   0
[ĐO] 738 dòng ở ttl: created_at 05/05/2026 → 14/08/2026  ⟹ ĐÚNG CÙNG TẬP đã có ở fin05
```
⟹ ***"738 → 0"* đúng cho `fin05`, và CHỈ cho `fin05`. Tính cả ba ngăn xếp cục bộ: VẪN 738.**

🔴 **SẮC THÁI TESTER THÊM — `fin05do` sạch KHÔNG phải bằng chứng backfill tốt: NÓ CHƯA BAO GIỜ BẨN**
(kho nạp **sau** khi `EncryptedText` đã có). Đọc *"hai ngăn xếp đã sạch"* là **dân số pha tạp** (§8):
**BỐN quần thể, mỗi cái sạch/bẩn vì một LÝ DO KHÁC NHAU.**

🔴 **CƠ CHẾ — VÀ NÓ NẰM Ở PHÉP NGHIỆM THU, KHÔNG Ở BẢN VÁ.**
Bản vá **đúng**. Phép nghiệm thu của PO-agent cũng **chặt** (đọc lại qua ORM trong container, 761 đọc
được, 0 dòng còn bản mã). **Không ai làm ẩu.**
> **PHÉP NGHIỆM THU THỪA HƯỞNG MẪU SỐ CỦA BẢN VÁ.** Bản vá chạy trên `fin05` ⟹ người kiểm mở `fin05`
> ⟹ kết luận mang tên *"backfill xong"* thay vì *"backfill xong TRÊN `fin05`"*.
> **Tập tự đến bị lọc bởi CHÍNH THAO TÁC đang được kiểm.**
Đây là §8 áp lên một **NGHIỆM THU** thay vì một **phép đo** — **hiểm hơn**, vì nghiệm thu là bước ta
dựng ra **ĐỂ BẮT** thiếu sót. Ba ngăn xếp nằm ở **dòng thứ tư của §1**; không ai phải đi tìm. Nó chỉ
**không có mặt trong CÂU HỎI**.
⚠️ **Và security mắc đúng lỗi ấy cùng ngày, độc lập:** §11 định hạng kho checkpoint **chỉ trên
`fin05`**. Họ **có tự khai** — nhưng **khai một khoảng trống không lấp nó**, y hệt ca §10.2.
**Hai người, hai artefact, một bộ lọc, một ngày** ⟹ tính chất của **quy trình**, không phải lỗi của ai.

**MẪU SỐ ĐẦY ĐỦ cho §5.J (kho checkpoint) — gấp 1,7× con số đã báo:**
```
             blob(messages)  HumanMessage  tiếng Việt   dung lượng
fin05            3.597          3.597        3.413       105 MB
fin05ttl         2.482          2.482        2.318        95 MB
fin05do             62             62           59       127 kB
TỔNG cục bộ      6.141          6.141        5.790      ~200 MB
```
**Hạng §5.J GIỮ NGUYÊN mức CAO — security KHÔNG nâng**, lý do họ nêu đúng: mẫu số lớn hơn **không đổi
bản chất** (cùng biên tin cậy, không kẻ tấn công mới), nó đổi **độ chính xác của hồ sơ**. *Nhưng một
định hạng đúng với mẫu số sai vẫn là một định hạng phải làm lại.*

⭐ **VÀ `fin05ttl` NAY LÀ TÀI SẢN KIỂM THỬ, KHÔNG PHẢI RÁC** *(tester)*: cổng plaintext chuyển ĐỎ→XANH
nhờ backfill, nhưng **không ai chứng minh nó CÒN BIẾT ĐỎ** — nửa *"KÊU lúc bất thường"* của **Luật A**
bỏ trống. Cách rẻ nhất trông có vẻ là nhét một dòng plaintext giả vào CSDL — **tester TỪ CHỐI** (ghi
vào ngăn xếp đang phục vụ, Luật I). **Không cần:** `fin05ttl` là **quần thể bẩn CÓ THẬT, sẵn có,
không do ta tạo ra**. Ca đối chứng hai chiều đã dựng, và **chiều thứ hai mới quan trọng**: ngày
`fin05ttl` được nạp lại, ca ấy **báo MẤT KHẢ NĂNG ĐỐI CHỨNG** thay vì lặng lẽ xanh.
🔴 ⟹ **Ai định dọn `fin05ttl` phải biết: nạp lại nó sẽ TẮT ca đối chứng duy nhất chứng minh cổng
plaintext còn sống.**

**QUẦN THỂ THỨ TƯ — `app.adaptivealgo.uk` (production): CHƯA AI ĐO, KHÔNG AI CHẠM.** Mọi số ở §5.J và
mục này là của **BA ngăn xếp CỤC BỘ**. Ai trích chúng như *"toàn hệ thống"* là **một mẫu số sai nữa**.
Nếu một ADR có phạm vi production thì **quần thể quyết định nhất là quần thể duy nhất chưa ai đo** —
đó là **câu xin phép PO thật**, chưa hỏi.

**KHÔNG kết luận:** ❌ `fin05ttl` là **sự cố** — nó là **bản vá chạy chưa hết phạm vi, mà phạm vi đúng
thì CHƯA AI ĐỊNH NGHĨA**. ❌ ai sai — **thiếu sót nằm ở CÂU HỎI, không ở THAO TÁC**.

*(Câu hỏi treo cuối mục này đã được PO-agent trả lời 20/08 — xem đầu file.)*
