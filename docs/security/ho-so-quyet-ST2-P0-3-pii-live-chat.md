# HỒ SƠ QUYẾT — ST2-P0-3: che PII gõ tay trong live-chat

> Vai: **security** · 2026-08-14 · nhánh `dev/learning-loop`
> **Người quyết: PO thật.** Deadline: **trước đợt 150 người thật** (đây là mốc
> kích hoạt ADR-011 — người thật gõ chữ thật).
> Hồ sơ này chỉ để quyết; không sửa code. Vá thuộc coder, test thuộc tester.
>
> Mọi dữ kiện dưới đây **đo bằng chạy thật trên stack đang chạy**, không suy
> luận từ tài liệu.

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
2. **Giữ 4 số cuối** cho SĐT/STK; tên người che trọn theo NER
   (`scrub_pii` đã có sẵn, `src/observability/pii.py:277`).
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
