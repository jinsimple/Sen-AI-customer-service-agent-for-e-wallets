# HỒ SƠ QUYẾT — ST2-P0-3: che PII gõ tay trong live-chat

> Vai: **security** · 2026-08-14 · nhánh `dev/learning-loop`
> **Người quyết: PO thật.** Deadline: **trước đợt 150 người thật** (đây là mốc
> kích hoạt ADR-011 — người thật gõ chữ thật).
> Hồ sơ này chỉ để quyết; không sửa code. Vá thuộc coder, test thuộc tester.
>
> Mọi dữ kiện dưới đây **đo bằng chạy thật trên stack đang chạy**, không suy
> luận từ tài liệu.

---

## ⚠️ ĐÍNH CHÍNH 2026-08-15 — ĐỌC TRƯỚC KHI QUYẾT §8

**Đơn thuốc ở §5.2 của chính hồ sơ này (dùng `scrub_pii`, giữ 4 số cuối) nay
KHÔNG còn an toàn như lúc viết.** Phép đo hôm nay
(`2026-08-15-ra-soat-cuoi-sprint-note-scrub-va-pipeline.md`, dấu
`he_thong=fd16681d8088`, 0 TPM) cho thấy `scrub_pii` **chặn nhầm 8/20 = 40%**
trên văn bản nghiệp vụ tiếng Việt KHÔNG chứa PII, và kiểu hỏng là **đổi nghĩa
câu trong im lặng**, không phải che dư một mã:

- `Khách đã rút khiếu nại qua tổng đài, không cần xử lý tiếp.`
  → `[LOCATION] đã rút khiếu nại qua tổng đài, không [PERSON].`

Tin nhắn live-chat **chính là** văn bản tự do tiếng Việt — cùng loại đầu vào đã
đo. Áp phương án B nguyên văn theo §5.2 sẽ mang lỗi đó vào **lời khách gõ cho
CSKH**, nơi hậu quả nặng hơn `note`: CSKH đọc một khiếu nại đã bị sửa nghĩa mà
không biết chữ nào đã mất, và đó là bản duy nhất còn lại (che tại điểm GHI ⟹
không còn bản gốc để đối chiếu).

Đây là **Luật 8 áp lên chính hồ sơ này**: §5.2 dựa trên tiền đề ngầm *"scrub
chỉ tốn khả năng đọc"* — tiền đề đó vừa bị đo và bác. Lỗi là **sai NHẬN DẠNG**
(NER gán `[PERSON]` cho `chính sách`, `[LOCATION]` cho `Khách`), không phải sai
ngưỡng, nên **không có cách nới/siết nào chạm tới**.

**Hệ quả thao tác cho PO:**
1. **Câu hỏi §8.1 (A/B/C) KHÔNG đổi** — khuyến nghị vẫn là **B**, vẫn phản đối
   C. Lỗ hổng §3 là thật và vẫn hở.
2. **Câu hỏi §8.2 (giữ 4 số cuối hay che trọn) không còn là câu hỏi đủ.** Câu
   đúng phải hỏi trước nó: **che bằng CƠ CHẾ nào** — vì cơ chế được đề nghị
   đang hỏng. Xem §3 hồ sơ 15/08 cho 3 đường (khuyến nghị: xác nhận vòng tròn
   lúc ghi, không cần cải thiện NER).
3. **Câu hỏi §8.3 (gộp `description_raw`) nay phải mở rộng thành BỐN cửa**, xem
   dưới.

### Bốn cửa văn bản tự do — cùng MỘT chính sách, đừng quyết lẻ

| Cửa | Ai gõ | Scrub | Trần độ dài | Cờ injection | Mã hoá at-rest |
|---|---|---|---|---|---|
| `messages.content` (live-chat) | khách + CSKH | ❌ không | ❌ **nhận 20.000 ký tự** | ❌ | ✅ `EncryptedText` — **đo hành vi: CÓ hiệu lực** |
| `complaints.description_raw` | khách | ❌ không | ❌ **nhận 20.000 ký tự** | ❌ | ❌ `Text` thuần |
| `resolutions.note` | nhân viên | ✅ có — **nhưng hỏng nghĩa 40%** | ✅ 500, ép ở DB | ✅ `note_flagged` | ❌ `Text` thuần |
| `investigation_logs.agent_note` | nhân viên | ❌ không | ❌ **nhận 5.000 ký tự** | ❌ | ❌ `Text` thuần |

**Cả bốn ô ĐO BẰNG HÀNH VI trong phiên 15/08** (gọi route/service thật rồi đọc
thẳng DB), không suy ra từ đọc mã. Dấu `he_thong=fd16681d8088`.

> *Đính chính:* bản đầu của dòng này khẳng định "cả bốn ô" khi `messages.content`
> **chưa** được probe (số của nó còn dẫn từ hồ sơ 14/08) — tôi viết rộng hơn thứ
> mình đã đo, đúng lỗi mà chính hồ sơ này đang bắt người khác. Nay đã đo thật
> (probe dưới), nên câu đó mới đúng.

`description_raw` và `messages.content` đo bổ sung sau cùng vì là hai ô còn dẫn
lại từ hồ sơ cũ thay vì đo trong phiên — Luật 9. Kết quả probe:

```
description_raw ĐỌC THẲNG TỪ DB:
 'Em chuyển nhầm cho anh Trần Văn Bách, sđt 0912345678,
  STK 88000000000194, CCCD 001234567890. Số em là 0987654321.'
còn NGUYÊN VĂN? -> True   (cả 5 mẩu PII: 2 SĐT · STK · CCCD · tên)
mô tả 20.000 ký tự -> lưu DB đủ 20.000
payload injection lưu nguyên văn: True · cột cờ trên Complaint: KHÔNG CÓ
```

**`messages.content` (probe 15/08) — hiện trạng ST2-P0-3 KHÔNG trôi, và một
điểm SÁNG cần ghi:**

```
content đọc qua ORM: 'Em chuyển nhầm cho anh Trần Văn Bách, sđt 0912345678,
                      STK 88000000000194, CCCD 001234567890.'
còn nguyên văn (không scrub) -> True     (4/4 mẩu PII còn nguyên sau giải mã)
tin 20.000 ký tự -> lưu đủ 20.000        cột cờ trên Message -> KHÔNG CÓ
payload injection lưu nguyên văn -> True

BYTE THẬT trong DB (SQL thô, vòng qua type decorator):
  'gAAAAABqgCRz6DpP1R2B9-N2Sg_Onanat4Bvpi7cdkfHq_vg6UnKiYmU0J9T40Z5quppnkJ8d…'
PII lộ plaintext trong DB? -> False      ⟹ mã hoá at-rest CÓ HIỆU LỰC
```

Điểm sáng: `EncryptedText` **không chỉ được khai trên cột — nó chạy thật**.
Kiểm bằng SQL thô đọc vòng qua type decorator, byte trong bảng là ciphertext
Fernet, không có mẩu PII nào. Đây là control DUY NHẤT trong bốn cửa mà tôi
xác nhận được bằng **hành vi** thay vì bằng một dòng khai báo kiểu (hiện-diện
≠ hiệu-lực áp cho cả thứ ĐANG chạy đúng, không riêng thứ hỏng).

**Hệ quả cho ADR-025:** điều này **củng cố** lập luận BÁC che-lúc-ghi ở nhóm A
— ở `messages.content`, lớp bảo vệ at-rest đã hoạt động, nên đổi thêm giá trị
chứng cứ để lấy một mức giảm thiểu nữa là đánh đổi tồi. Và nó nâng giá trị của
**A1**: mã hoá `description_raw` là kéo cửa yếu lên một chuẩn **đã chứng minh
chạy được**, không phải một chuẩn mới trên giấy.

Đáng chú ý: `description_raw` chứa PII của **bên thứ ba** ngay trong ca dùng
điển hình nhất ("em chuyển nhầm cho anh X, sđt …") — người **không phải khách
hàng**, không có cơ sở pháp lý để lưu, đúng rủi ro §3 của hồ sơ này nhưng ở
cửa khác. Và nó là cửa duy nhất trong bốn cửa mà **khách tự gõ** lại **không
có mã hoá at-rest** (live-chat có `EncryptedText`, cửa này không).

`agent_note` là cửa THỨ TƯ, chỉ lộ ra hôm nay, và nó **bác tiền đề "note là chỗ
DUY NHẤT"** của ADR-024. Quyết lẻ từng cửa sẽ tạo đúng tình trạng bất nhất mà §7
đã cảnh báo — nay gấp đôi quy mô.

---

## 1. Quyết cái gì (một câu)

Khách/CSKH gõ SĐT, số tài khoản, tên người vào ô chat; hệ thống lưu **nguyên
văn** vào `messages.content`. Câu hỏi cho PO: **che trước khi lưu, hay giữ
nguyên?** — và nếu che thì che tới đâu.

Test `tests/test_api/test_live_chat_pii_gap.py` đang **đỏ có chủ đích** để giữ
câu hỏi này mở; tester cố ý không tự vá vì đây là quyết định sản phẩm.

## 2. DỮ KIỆN QUYẾT ĐỊNH — lý do phản đối chính KHÔNG còn đứng vững

Lập luận giữ nguyên văn xưa nay là: *"che đi thì CSKH mất SĐT để gọi lại
khách."* **Đo thật cho thấy CSKH đã có SĐT từ một kênh khác, luôn luôn:**

```
CSKH (USR-0201) mở panel chat của TCK-e5b1c615435d  ->  200
context.customer = {"user_id": "USR-0001",
                    "full_name": "Phan Đức Long",
                    "phone": "0387000001"}
```

`GET /live-chat/sessions/by-ticket/{ticket_id}` → `get_handoff_context()`
(`src/services/live_chat.py:181`) trả **họ tên + SĐT lấy từ HỒ SƠ tài khoản**,
**mọi lần mở panel, bất kể phiên còn mở hay đã đóng** — docstring của route
nói rõ đó là chủ đích (`main.py:1185-1196`).

⟹ **Che nội dung chat KHÔNG làm CSKH mất khả năng gọi lại chủ tài khoản.**
Số của khách đến từ dữ liệu có cấu trúc, đã xác thực, không phải từ chuỗi khách
gõ tay (vốn có thể sai chính tả, sai số, hoặc là số của người khác).

**Đây là dữ kiện nên lật hướng quyết định**, vì đánh đổi mà mọi người tưởng có
thì phần lớn không tồn tại.

## 3. Rủi ro nếu giữ nguyên trạng

- **Nội dung chat được lưu vĩnh viễn**, không retention (F-06,
  `review-2026-08-13.md`), đọc được bởi `cskh` + `supervisor` **bất kỳ ai**,
  không chỉ người phụ trách ca (`GET /live-chat/sessions/{id}/messages` chỉ
  chặn *khách khác*, không giới hạn nhân viên theo ca).
- **PII bên thứ ba**: khách gõ "chuyển nhầm cho anh Nam 0912…" là dữ liệu của
  **người không phải khách hàng**, không có cơ sở pháp lý để lưu. Dự án đã che
  đúng loại dữ liệu này ở tầng tool (`src/tools/masking.py`) — live-chat là
  **cửa duy nhất còn hở của cùng một nguyên tắc**.
- **150 người thật**: rủi ro tồn dư mà chính ADR-011 đã ghi — "một bạn gõ
  'mình là Bách, sđt 09…' thì đó là PII thật của chính bạn đó". Vì hồ sơ Mẫu 06
  đang được hoãn, scrub là **lớp bảo vệ duy nhất**, không phải lớp bổ sung.
- **NĐ 13/2023 (tối thiểu hoá) + GDPR Đ.5(1)(c)**: lưu bản sao thứ hai của SĐT
  ở dạng phi cấu trúc, trong khi đã có bản chính thức trong hồ sơ, là **dư
  thừa** — không có mục đích xử lý nào biện minh được.
- Có mã hoá at-rest (`Message.content` dùng `EncryptedText`, `models.py:436`)
  nhưng **mã hoá at-rest không giải quyết bài này**: nó chống mất đĩa/backup,
  không chống người đọc hợp lệ, không chống rò qua export/DSAR/log.

## 4. BA PHƯƠNG ÁN

| | Phương án | Được | Mất |
|---|---|---|---|
| **A** | **Giữ nguyên văn** (nguyên trạng) | Không tốn công; CSKH đọc được mọi thứ khách gõ | Giữ nguyên toàn bộ rủi ro §3; test ST2-P0-3 đỏ vĩnh viễn; là thứ khó giải thích nhất nếu ZaloPay/chuyên gia soi trước khi ký |
| **B** ⭐ | **Che khi LƯU, giữ 4 số cuối** — `scrub` chạy trong `record_message()` trước khi ghi; SĐT/STK hiển thị dạng `09******21`; tên người che theo NER | Đóng đúng lỗ hổng; CSKH vẫn **đối chiếu** được ("số anh vừa gõ có phải …21 không?") và vẫn **gọi lại** được bằng SĐT hồ sơ (§2); nhất quán với `masking.py` đã có; không cần đổi UI | Mất số **thứ ba** khách gõ (§6, ca tồn dư); che nhầm mã đơn/mã giao dịch 12 số (đánh đổi đã chấp nhận ở checklist observability) |
| **C** | **Lưu nguyên văn + che lúc HIỂN THỊ** theo vai | CSKH thấy đủ khi cần | **Không giải quyết gì**: dữ liệu thô vẫn nằm trong DB, vẫn vào export/DSAR/backup/log. Đây chính là mẫu lỗi mà template vai security gọi tên: *"UI che nhưng response JSON vẫn đầy đủ"*. **Security phản đối.** |

**KHUYẾN NGHỊ: phương án B.** Lý do gọn: lợi ích duy nhất của A/C là thứ mà §2
chứng minh CSKH đã có sẵn từ kênh tốt hơn.

## 5. Nếu PO chọn B — ranh giới đề nghị chốt luôn

1. **Che tại điểm GHI**, không tại điểm đọc (cùng luật đã áp cho `note` ở
   TM-03) — bản trong DB phải là bản đã che, nghiệm thu bằng đọc thẳng DB.
2. ⚠️ **ĐÃ ĐÍNH CHÍNH 15/08 — xem khối đầu hồ sơ trước khi dùng mục này.**
   ~~**Giữ 4 số cuối** cho SĐT/STK; tên người che trọn theo NER
   (`scrub_pii` đã có sẵn, `src/observability/pii.py:277`).~~
   `scrub_pii` đo được 40% chặn nhầm trên văn bản nghiệp vụ tiếng Việt (đổi
   nghĩa câu, im lặng) ⟹ **không dùng nguyên trạng làm đơn thuốc cho cửa này.**
   Cơ chế che phải chốt lại cùng lô với S-01/S-02.
3. **Fail-closed**: scrub lỗi/timeout ⟹ từ chối lưu tin nhắn kèm thông báo rõ,
   **không** lưu bản thô rồi hẹn che sau.
4. **Áp cho cả hai chiều** — tin của khách **và** tin của CSKH. Nhân viên gõ số
   khách vào chat cũng tạo ra đúng bản sao dư thừa đó.
5. **Không đụng `EncryptedText`** — mã hoá at-rest giữ nguyên, đây là hai lớp
   khác nhau.

## 6. Ca tồn dư PO cần biết trước khi chốt (không giấu)

- **Số của bên thứ ba do khách gõ** ("gọi giúp em số chồng em 09…") sẽ bị che.
  Đánh giá của security: **che là đúng** — đó là PII của người ngoài, dự án đã
  chọn che đúng loại dữ liệu này ở tầng tool. Nếu nghiệp vụ thật cần, làm đường
  **có cấu trúc** (ô "số liên hệ thay thế" có ý thức, có cơ sở pháp lý) thay vì
  moi từ chuỗi tự do.
- **Đối chiếu số khách vừa đọc**: 4 số cuối đủ để xác nhận, không đủ để bấm
  gọi — chấp nhận được vì số bấm gọi lấy từ hồ sơ.
- **Dữ liệu chat CŨ** đã lưu nguyên văn vẫn còn nguyên. Che từ nay không dọn
  quá khứ. PO cần quyết riêng: dọn hay giữ (gợi ý: dọn cùng nhịp, chỉ vài
  chục dòng ở môi trường demo).

## 7. Mục ngoài phạm vi ST2-P0-3 nhưng CÙNG một quyết định — đề nghị PO chốt một thể

`complaints.description_raw` (mô tả khiếu nại khách tự gõ) **cũng không qua
scrub nào** trước khi lưu (`src/services/complaint_intake.py` — không có
`scrub`/`mask`), và được trả cho staff ở cả `GET /tickets/{id}` lẫn
`get_handoff_context()`. Đây là **cùng lớp lỗ hổng, cùng loại dữ liệu, cùng
150 người thật** — chỉ khác cửa vào.

Chốt riêng lẻ sẽ tạo tình trạng "che ô chat, để hở ô mô tả", và đó là kiểu bất
nhất mà người soi bảo mật tìm ra trong năm phút. Đề nghị: PO quyết **một chính
sách chung cho mọi văn bản người dùng tự gõ**, áp cho cả hai cửa.

## 8. Cần PO quyết — đúng 3 câu hỏi

1. **Chọn A, B hay C?** (security khuyến nghị **B**, và phản đối C).
2. Nếu B: **giữ 4 số cuối** như đề nghị, hay che trọn?
3. **Có gộp `description_raw` (§7) vào cùng chính sách không?** (security
   khuyến nghị **có**.)

Quyết xong: coder vá `record_message()` (+ intake nếu chọn gộp), tester gỡ
marker `security_finding` khỏi `test_live_chat_pii_gap.py` và bổ sung test cho
ranh giới §5, security rà bằng probe thật đúng khuôn đã dùng cho `note`.
