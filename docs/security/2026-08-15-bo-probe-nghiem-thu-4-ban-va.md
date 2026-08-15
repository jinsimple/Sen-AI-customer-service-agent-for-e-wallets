# Bộ probe nghiệm thu — S-03 · F-28 · A1 · A2

> Vai: **security** · 2026-08-15 · vùng ghi `docs/security/`
> **Soạn TRƯỚC khi coder land**, để land xong là chạy được ngay.
>
> Căn cứ điều kiện đóng PO-agent đã ghi vào lệnh giao việc của coder:
> **bốn bản vá này KHÔNG được coi là đóng nếu chỉ có coder tự nghiệm thu** —
> luật F-23: *coder tự nghiệm thu là CẦN, KHÔNG BAO GIỜ ĐỦ cho lớp phòng vệ*,
> vì mọi phép kiểm coder tự thiết kế thừa hưởng điểm mù của coder.

## Quy tắc chung cho cả bốn

1. **Probe HÀNH VI, không grep tên.** Bài học C4: grep-tên sai **cả hai
   chiều** (tưởng-chưa-vá vì không thấy tên · tưởng-đã-vá vì thấy tên).
2. **Đóng dấu `he_thong` hai đầu** (trước và sau lượt probe, phải bằng nhau).
   Coder đang mutate `src/` trong đợt này ⟹ **bắt buộc**, không phải tuỳ chọn.
3. **Mỗi ràng buộc mới phải có ≥1 ca đối chứng** chứng minh nó KHÔNG chặn nhầm
   (Luật 2) — thiếu vế này thì bản vá chặt tay nhất luôn thắng theo số đo.
4. Chạy **0 TPM**, tất định. Không cái nào trong bốn cần gọi LLM.

---

## A1 — mã hoá at-rest cho `complaints.description_raw`

**Đây là chỗ *hiện-diện ≠ hiệu-lực* dễ tái diễn nhất trong bốn.** Dòng khai
`EncryptedText` trên cột **không** chứng minh ciphertext nằm trong DB.

**Bắt buộc: probe BẰNG BYTE** — dùng lại đúng khuôn đã dùng cho
`messages.content` (`eb444eb`): ghi qua service thật, rồi đọc **SQL thô vòng
qua type decorator**.

```python
tho = session.execute(
    text("SELECT description_raw FROM complaints WHERE complaint_id = :id"), {...}
).scalar()
assert "0912345678" not in str(tho)      # không lộ plaintext
assert str(tho).startswith("gAAAAA")     # là ciphertext Fernet thật
```

| # | Ca | Kỳ vọng |
|---|---|---|
| A1-01 | ghi mô tả có PII → đọc **byte thô** | 0 mẩu PII plaintext · chuỗi Fernet |
| A1-02 | đọc lại **qua ORM** | ra **đúng nguyên văn** đã ghi (giải mã đúng, không mất chữ) |
| A1-03 | **đối chứng round-trip** tiếng Việt có dấu + emoji + 500+ ký tự | khớp byte-for-byte |
| A1-04 | dữ liệu CŨ ghi trước migration | đọc được (migration có backfill đúng) hoặc **fail rõ ràng**, KHÔNG trả chuỗi rác |

⚠️ **A1-04 là ca dễ bị bỏ nhất.** `messages.content` khi chuyển sang
`EncryptedText` là bảng **0 dòng dữ liệu** nên không có bài toán backfill.
`complaints` **đã có dữ liệu**. Nếu migration không xử lý hàng cũ, triệu chứng
là đọc ra rác hoặc exception ở đúng ticket cũ — và sẽ không lộ ra trong test
dùng DB sạch.

---

## A2 — trần độ dài cho các cửa văn bản tự do

Số đo hiện tại: `description_raw` nhận **20.000**, `agent_note` nhận **5.000**,
`messages.content` nhận **20.000**. `note` đã có trần 500 ép ở DB.

| # | Ca | Kỳ vọng |
|---|---|---|
| A2-01 | đúng **N** ký tự (mép dưới) | **NHẬN** |
| A2-02 | **N+1** ký tự (mép trên) | **TỪ CHỐI**, mã lỗi rõ (4xx), KHÔNG phải 500 |
| A2-03 | **đối chứng**: mô tả hợp lệ dài vừa phải (~N/2), tiếng Việt thật | **NHẬN**, không bị cắt, không mất chữ |
| **A2-05** | 🔴 **đối chứng BẮT BUỘC**: đúng **N ký tự tiếng Việt ĐỦ DẤU** (không phải ASCII) | **NHẬN** — xem cảnh báo dưới |
| A2-04 | ép ở **tầng DB** hay chỉ ở route? ghi thẳng qua ORM vượt trần | theo `note`: CHECK constraint chặn |
| **A2-06** | 🔴 **CẢ HAI đường ghi**: (i) REST (`ComplaintCreateRequest`) **và** (ii) đường **agent tool** (`customer_tools` → `create_ticket_with_fraud_check`) | cả hai đều **từ chối sạch** ở N+1, KHÔNG đường nào rơi xuống CHECK |

**Kiểm cả hai mép là bắt buộc** (đúng khuôn `test_06` của `note`: 500 nhận /
501 từ chối). Chỉ kiểm một mép thì không phân biệt được "trần đúng N" với
"trần bất kỳ đâu quanh N".

🔴 **A2-06 — vì sao phải kiểm CẢ HAI đường ghi.** Trần ký tự sống ở **Pydantic**
(`max_length`), mà Pydantic chỉ nằm trên đường **REST**. `description_raw` còn
một đường ghi thứ hai: **AI gọi tool dưới danh nghĩa customer** (ràng buộc cứng
2) → `customer_tools` → `create_ticket_with_fraud_check` → `create_ticket`.
Đường đó **không đi qua `ComplaintCreateRequest`**.

Nếu đường agent không có trần riêng, một mô tả quá dài (LLM tự sinh, hoặc khách
dán một khối văn bản) sẽ **đi thẳng xuống CHECK ở DB** → `IntegrityError` →
**500 cho khách**, đúng hình dạng **F-21** — trong khi đường REST trông hoàn
toàn ổn. CHECK phải là **lưới CUỐI**, không được là lưới **duy nhất** của bất kỳ
đường nào.

⚠️ Tôi **chưa xác nhận** đường agent có trần hay không (`src/` đang trôi lúc tôi
viết — 7 file sửa dở, chưa commit). Đây là **ca phải kiểm**, không phải một
finding đã đo.

---

🔴 **A2-05 — ca này bắt một lỗi ĐÃ ĐO ĐƯỢC trong dự thảo ADR-025 QĐ 5.** Bound
CHECK trên ciphertext `<= 4000` được dẫn từ số đo `2.000 ký tự → 3.556`, nhưng
số đó đo trên văn bản gần-ASCII. Fernet nở theo **byte UTF-8**, tiếng Việt có
dấu **3 byte/ký tự**:

```
ASCII thuần        2000 ký tự →  2000 byte →  2764 ciphertext   OK
Tiếng Việt CÓ DẤU  2000 ký tự →  6000 byte →  8100 ciphertext   VƯỢT BOUND
=> với ký tự 3-byte, CHECK<=4000 chỉ cho ~975 ký tự (trần nghiệp vụ là 2000)
```

⟹ khiếu nại 2.000 ký tự viết tiếng Việt đủ dấu **vượt CHECK ở tầng DB** →
`IntegrityError` → **500 cho khách** (hình dạng F-21), mà nhìn ngoài như
chống-flood chạy đúng. **A2-05 phải ĐẠT trước khi A2 được ký đóng.** Chi tiết +
hai phương án sửa: `2026-08-15-phan-bien-du-thao-ADR-025.md` §QĐ 5.

⚠️ **A2-03 là vế chống-siết-quá.** Trần đặt quá thấp sẽ cắt lời khiếu nại thật
— cùng họ tổn hại với S-01 (phá nội dung thật), chỉ khác cơ chế. Nếu coder
chọn N, xin nêu **căn cứ** cho N, không lấy số tròn cho đẹp.

---

## S-03 — scrub cho exception đi vào span

**Ca dương tính CẦN Postgres.** SQLite **không** echo tham số trong thông báo
lỗi (`FOREIGN KEY constraint failed`, hết); Postgres **có**
(`DETAIL: Key (phone)=(0912345678) already exists`). Đây đúng lớp lỗi chỉ lộ
sau khi deploy thật.

| # | Ca | Kỳ vọng |
|---|---|---|
| S03-01 | Postgres: gây IntegrityError trên cột có PII → đọc span attribute | PII **không** xuất hiện trong `status.description` lẫn span event |
| S03-02 | `ValidationError` echo giá trị đầu vào | như trên |
| S03-03 | **đối chứng**: exception KHÔNG có PII (vd `ZeroDivisionError`) | thông báo lỗi **còn nguyên**, vẫn debug được |

⚠️ **Nếu không dựng được Postgres thật thì GHI RÕ "chưa đo được"** — không kết
luận từ SQLite, và **không** đánh dấu S-03 là đóng. Đây là chỗ tôi tự ràng
buộc mình: mặc định phải là **chưa đo được**, không phải "chắc là ổn".

S03-03 quan trọng ngang hai ca kia: scrub exception mà làm mất luôn thông tin
gỡ lỗi thì đổi một rủi ro rò lấy một rủi ro mù.

---

## F-28 — mở tier-1 EN sang họ động từ

Đặc tả đầy đủ ở `F-28-tier1-EN-neo-mot-dong-tu.md` §2/§6.

| # | Bộ ca | Kỳ vọng |
|---|---|---|
| F28-A | **8 câu tấn công** (`ignore`/`disregard`/`forget`/`override`/`bypass`/`skip`/`do not follow`/`must not obey`) | **tier1** cả 8 |
| F28-B | **7 câu đối chứng lành** (`Skip this step…`, `Do not follow links…`, `…follow the instructions on the screen`, `must follow the rules…`) | **`""`** cả 7 |
| F28-C | **FP kho thật** `data/raw/` 1.814 câu | **0/1814** (bằng mốc trước vá) |

**Chạy A và B CÙNG NHAU, cấm lẻ** (Luật 2) — mỗi bộ đẩy về một phía sai.

⚠️ **Khi ký nghiệm thu, ghi đúng chữ:** *"bắt thêm 7 ca ĐÃ BIẾT"*, **KHÔNG**
được ghi *"đã chặn lớp tấn công đổi-động-từ"*. Thêm 9 động từ vẫn là danh sách
viết tay; `refrain from following`, `pay no attention to`, gõ sai chính tả vẫn
qua. Bản vá đúng tầng là `KC.GAP` cho tiếng Anh (Luật 18/ADR-023 đã làm cho
tiếng Việt), thuộc **CỔNG-A**.

⚠️ **F-28 làm `MOC_TIER1` của tester TĂNG.** Mốc mới phải được nâng bằng một
quyết định **dẫn nguồn** (*"F-28 land ⟹ sàn 4→N, dẫn F-28 §2"*), **không** được
đặt bằng cách chạy suite rồi chép số ra — đó đúng là hiệu-chuẩn-thước-theo-vật
(luật 6b của tester). `MOC_TIER1` là **SÀN**: chỉ nâng, không bao giờ hạ; hạ
sàn cần một finding, không phải một lần sửa hằng số.

---

## Điều kiện đóng chung

Một bản vá được tôi ký đóng khi có **đủ ba**: (1) ca hiệu quả ĐẠT · (2) ca đối
chứng chứng minh không siết nhầm · (3) dấu `he_thong` hai đầu không lệch.

Thiếu (2) thì **không ký**, kể cả khi (1) đẹp — đó là bài học lặp lại nhiều
nhất của dự án này (F-22 → F-24 → F-25 → S-01, bốn lần cùng một hình dạng).
