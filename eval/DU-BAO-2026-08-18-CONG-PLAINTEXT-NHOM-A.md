# DỰ BÁO — cổng "không dòng nào trong cột Nhóm A nằm plaintext" (ADR-032 việc ③)

> Vai: **tester** · 18/08 · **0 token** · viết **TRƯỚC** khi truy vấn CSDL.
> Nguồn đặc tả: `docs/DECISIONS.md` ADR-032 + phần BỔ SUNG. **Không đọc `src/`.**

## ① 🔴 CỔNG NÀY ĐO CÁI GÌ — khai TRƯỚC, vì đây là chỗ nó dễ bị trích quá nhất

```
ĐO ĐƯỢC        HÌNH DẠNG TRÊN ĐĨA của giá trị trong CSDL
KHÔNG ĐO ĐƯỢC  giá trị ấy có giải mã được bằng khoá HIỆN TẠI hay không
KHÔNG ĐO ĐƯỢC  hành vi ORM (`process_result_value`) — bản vá ADR-032 việc ① đã
               vào cây nhưng CONTAINER VẪN CHẠY MÃ CŨ (PO-agent xác nhận 18/08)
```
Dấu hiệu dùng để phân biệt, lấy từ ADR-032 BỔ SUNG ③: **Fernet token luôn mở
đầu `gAAAAA`** (byte phiên bản `0x80` → base64url mở đầu `gA`).

⚠️ **`gAAAAA` chứng minh HÌNH DẠNG, không chứng minh QUYỀN ĐỌC.** Một dòng mã
hoá bằng **khoá khác** cũng mở đầu `gAAAAA` và cổng này sẽ đọc là "đã mã hoá".
Đó là **đúng phạm vi** — cổng này canh *dữ liệu nằm trần trên đĩa*, không canh
*ta còn đọc được không*. Việc sau thuộc bản vá ORM và **chỉ đo được sau khi
dựng ảnh**. Không gộp hai câu.

## ② HÌNH DẠNG CỔNG — chốt trước khi nhìn số

Hai nửa, cố ý không gộp:

**(a) NEO ĐẶC TẢ** — bốn cột ADR-032 BỔ SUNG ① khai là Nhóm A/`Encrypted*`
(`complaints.description_raw` · `messages.content` · `policy_chunks.text` ·
`bank_accounts.account_no`) phải **100%** mang hình dạng mã hoá.

**(b) TỰ DÒ CẢ HỌ** — quét **mọi** cột văn bản trong CSDL, tìm cột **PHA TRỘN**
(vừa có dòng `gAAAAA…` vừa có dòng không). Một cột pha trộn **theo định nghĩa**
là cột đáng lẽ được mã hoá mà có dòng nằm trần.

> **Vì sao bắt buộc có (b):** cổng chỉ kiểm 4 cột trong danh sách là cổng gõ
> cứng — nó **không biết gì về cột thứ năm**. Đó đúng lớp lỗi tôi đã vá hai lần
> hôm nay (đầu dò kho RAG gõ cứng tên collection; rồi gõ cứng path). *Vá một họ
> lỗi thì đi tìm HỌ, đừng vá cái đang cầm.*
> **Vì sao (b) KHÔNG thay được (a):** một cột **100% plaintext** mà lẽ ra phải
> mã hoá thì (b) **không thấy** — không pha trộn thì không có gì lạ để dò. Chỉ
> đặc tả mới biết cột ấy phải được mã hoá. Hai nửa canh hai lỗ khác nhau.

**Ba trạng thái:** sạch · có dòng trần · **KHÔNG ĐO ĐƯỢC** (không nối được CSDL ·
bảng/cột không tồn tại · bảng rỗng — bảng rỗng **KHÔNG** được đếm là "sạch").

## ③ DỰ BÁO

| # | dự báo | độ chắc | |
|---|---|---|---|
| 1 | `complaints.description_raw` **PHA TRỘN** ⟹ cổng **ĐỎ** | **rất cao** | ADR-032 [ĐO] 738 trần / 23 mã hoá cùng ngày |
| 2 | số dòng trần **≥ 738** | **cao** | sổ chỉ tăng; lượt hôm nay có thể thêm |
| 3 | ba cột kia **100%** mã hoá, không pha trộn | **cao** | ADR-032 BỔ SUNG ① đo cả bốn: 467/0 · 378/0 · 245/0 |
| 4 | phép dò (b) tìm thấy **đúng 1** cột pha trộn | **trung bình** | (a) chỉ phủ 4 cột; (b) quét cả CSDL nên **có thể lộ cột thứ năm chưa ai khai** |

🔴 **Cổng này SINH RA ĐỂ ĐỎ.** Nó là bằng chứng cho một khoản nợ đã có ADR và
đã giao người (script backfill, `migrations/`). ⟹ gắn `@pytest.mark.security_finding`
— đúng quy ước `pytest.ini` (*"finding P0 CHƯA VÁ, cố ý fail làm bằng chứng,
chạy riêng ở CI job `security-findings-gate`"*). `lint-and-test` vẫn xanh.

🔴 **Khai trước:** nếu cổng **XANH ngay lần đầu**, đó **KHÔNG** phải tin tốt —
nghi theo thứ tự ở ④, đừng mừng.

## ④ NẾU KHÁC DỰ BÁO THÌ NGHI GÌ

| quan sát | nghi ĐẦU TIÊN | cách phân định |
|---|---|---|
| cổng **XANH** ở `description_raw` | 🔴 **tôi soi nhầm ngăn xếp** (`fin05do` kho rỗng, `fin05ttl` gần rỗng) — đúng lỗi kho RAG sáng nay, một tầng khác | in TÊN CONTAINER + tổng số dòng cùng dòng kết quả |
| cổng xanh **và** container đúng | ai đó đã chạy backfill mà chưa báo | hỏi trước khi kết luận — **đừng** ghi "đã vá" |
| (b) tìm thấy **>1** cột pha trộn | **finding MỚI**, ngoài phạm vi ADR-032 | báo PO-agent, **không tự mở rộng ADR** |
| (b) tìm thấy **0** cột dù (a) đỏ | 🔴 **phép dò (b) HỎNG** — nó phải bắt được ca đã biết | tiêu chí ④ của `4ac2162`: bộ dò không bắt được ca đã biết thì "0 kết quả" vô nghĩa |
| số dòng trần **< 738** | có người xoá dòng, hoặc tôi đếm khác mẫu số ADR | so mẫu số: ADR đếm **toàn bảng**, không `LIMIT` |
| cột nào đó báo "bảng rỗng" | KHÔNG ĐO ĐƯỢC | **không** được gộp vào "sạch" |

## ⑤ Đối chứng dương — bắt buộc, và làm được 0 rủi ro

Logic phân loại tách thành hàm **thuần** (`chuỗi → trần | mã_hoá`), kiểm bằng
dữ liệu bịa: `gAAAAABm...` ⟹ mã hoá · `"Toi bi tru tien"` ⟹ trần · `""` ⟹
**KHÔNG ĐO ĐƯỢC**, không phải "trần". Không ghi một byte nào vào CSDL đang phục
vụ (Luật I).

---

# ⑥ KẾT QUẢ THẬT — ghi SAU khi đo

Dự báo nằm trong `d88b5f0`, **trước** truy vấn đầu tiên. Container `fin05-postgres-1`.

| # | dự báo | thực tế | |
|---|---|---|---|
| 1 | `description_raw` pha trộn ⟹ ĐỎ | `{'tran': 738, 'ma_hoa': 23}` | ✅ TRÚNG |
| 2 | số dòng trần ≥ 738 | **đúng 738** | ✅ TRÚNG |
| 3 | ba cột kia 100% mã hoá | cả ba xanh | ✅ TRÚNG |
| 4 | phép dò (b) tìm đúng 1 cột pha trộn | đúng 1 | ✅ TRÚNG |

**4/4 trúng, tới từng chữ số.** Hai chế độ CI đều đúng: `-m security_finding`
→ **2 failed** (bằng chứng) · `-m "not security_finding"` → **1 passed, 5
deselected** (`lint-and-test` xanh).

## ⑦ 🔴 VÀ ĐÚNG VÌ 4/4 TRÚNG NÊN TÔI SOI TIẾP — Luật M

> *"Xác nhận không phải bằng chứng. Dấu hiệu khó thấy là kết quả KHỚP với thứ
> tài liệu đã hứa — lúc ấy không gì kích hoạt phản xạ soi lại."*

Trúng tới từng chữ số là **đúng lúc nguy hiểm nhất**. Câu tôi hỏi tiếp: *phép dò
(b) quét cột kiểu gì?* Trả lời: **chỉ kiểu văn bản.**

[ĐO] `information_schema.columns` trên `public`:
```
character varying  83 │ text  30 │ character  0   ← 113 cột, phép dò QUÉT
json 6 │ jsonb 2 │ bytea 2                        ← 10 cột, phép dò MÙ HOÀN TOÀN
```

Đo tiếp, **chỉ đếm, không in một byte nội dung nào**:
```
investigation_logs.tool_input_json      0 / 93     mang hình dạng mã hoá
checkpoint_blobs.blob                   0 / 6.213  mang hình dạng mã hoá
checkpoint_blobs.blob               2.179 / 6.213  CHỨA mã giao dịch "TXN2026…"
checkpoint_blobs.blob                   0 / 6.213  chứa SĐT tài khoản hạt giống
```

⟹ **Kho checkpoint giữ 2.179 dòng có mã giao dịch nằm trần**, ngoài cả sơ đồ mã
hoá lẫn cổng này. **738 không phải toàn cảnh.**

**Nhưng phải công bằng:** ADR-032 BỔ SUNG ① **đã khai đúng mẫu số của nó** —
*"[ĐO] cả bốn cột khai `Encrypted*`"*. Kết luận *"hệ thống mã hoá KHÔNG hỏng"*
đúng **bên trong mẫu số ấy**. Đây là **MỞ RỘNG PHẠM VI, KHÔNG phải đính chính**.

**Ranh giới tôi giữ:** `2.179/6.213` là số đếm dòng chứa mã giao dịch —
**KHÔNG** phải khẳng định "2.179 dòng chứa PII khách hàng". SĐT không xuất hiện
(`0/6.213`). Phân biệt hai câu đó là việc của security, không phải của tester.

**Cổng cố ý KHÔNG assert trên 10 cột đó.** Quyết định cột nào phải mã hoá là
việc của ADR. Tự mở rộng assertion là tester tự viết chính sách — đúng thứ quy
trình đổi contract sinh ra để chặn. **Đã báo PO-agent.**

## ⑧ Một lỗi trong CHÍNH THÔNG ĐIỆP của cổng, bắt được ở cùng vòng soi

Dòng báo lỗi của (b) viết cứng *"Cột ngoài 4 cột Nhóm A đã khai ⟹ FINDING
MỚI"* — nhưng cột nó bắt được **nằm TRONG** 4 cột ấy. Cổng đỏ đúng, **và câu nó
nói sai**: người đọc sẽ tưởng có finding thứ hai.

> Luật 7 — **biến dùng để TÍNH không được tái dùng để IN** (7d). Ở đây còn tệ
> hơn: câu in ra **không dựa trên biến nào cả**, nó là một hằng số văn bản giả
> định trước kết quả. Đã sửa: phân nhánh theo `set(pha_tron) - da_khai`.

Đây là lần thứ **ba** trong ngày lỗi nằm ở **công cụ đo / lớp báo cáo**, không
ở sản phẩm (① `doc_id` mồ côi · ② path gõ cứng · ③ dòng này). Cả ba đều lộ ra
vì hỏi tiếp **sau khi kết quả đã khớp**.
