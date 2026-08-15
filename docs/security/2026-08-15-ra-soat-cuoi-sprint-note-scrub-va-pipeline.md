# Rà soát cuối sprint — `note` PII masking + pipeline scrub trước log/trace

- **Ngày:** 2026-08-15 · **Vai:** security · **Vùng ghi:** `docs/security/`
- **Dấu đo (đóng dấu mọi phép đo — Luật 6):** `he_thong=fd16681d8088` ·
  `cham_diem=c0b79835e16c` · commit `2e8c888` · cây làm việc SẠCH (xác nhận
  độc lập với coder `p-226-8f` và PO-agent `p-226-7f` cùng lúc).
- **Môi trường:** venv có đủ `presidio-analyzer` + `underthesea` + model
  `xx_ent_wiki_sm` + `argon2` + `fakeredis`. Mọi phép đo dưới đây **0 TPM,
  tất định**, chạy TRONG PHIÊN (Luật 9 — không dẫn lại số của phiên khác).
- **Cửa sổ đóng băng:** đã báo coder + PO-agent giữ `src/` bất động trong lúc
  đo; `docs/`, `tests/`, `contracts/`, `scripts/` KHÔNG nằm trong dấu.

---

## 0. KẾT LUẬN CHO CÂU HỎI ĐANG CHẶN — có bật CI security-gate cho `note` không?

> **CHƯA BẬT.** Không phải vì scrub hỏng — scrub **che PII ĐẠT**. Mà vì cùng
> cơ chế đó đang **làm hỏng nghĩa của bản ghi kiểm toán trong im lặng**, và
> bật gate bây giờ là đóng dấu xanh lên hành vi đó.

Việc treo của tôi ghi là "verify PII masking (che-lúc-ghi, giữ-4-số, không lộ
transcript) đủ trước khi bật CI security-gate". Đo xong, ba vế trả lời như sau:

| Vế | Kết quả đo | Ghi chú |
|---|---|---|
| che-lúc-ghi | **ĐẠT** | 12/12 ca có PII bị che trước khi chạm DB (§2) |
| "giữ-4-số" | **KHÔNG áp dụng — và không NÊN áp dụng** | vế này tôi ghi sai trong sổ việc treo (§2.3) |
| không lộ transcript | **ĐẠT** | staff-gated, không vào tool LLM, không vào log (§2.2) |
| *(vế thứ tư, không ai đặt ra)* | **TRƯỢT** | toàn vẹn bản ghi kiểm toán (§3) |

Điều chặn gate là vế thứ tư — vế **không có trong đặc tả của chính tôi**. Đó là
lý do nó sống sót qua ADR-024, qua 13 test đối kháng của tester, và qua cả
sign-off TM-03 của tôi.

---

## 1. Phương pháp (vì sao tin được, và tin tới đâu)

Bộ test `tests/test_api/test_reject_note_doi_khang.py` của tester hỏi:
*"chuỗi PII X có VẮNG MẶT trong DB không?"* — trả lời được câu bảo mật.

Probe của tôi hỏi câu khác hẳn: *"cái CÒN LẠI trong DB là cái gì?"* — gọi thẳng
`scrub_pii` và **in ra nội dung**. Đây là hai **phương pháp khác nhau** trên
cùng một vật, đúng Luật 16 (giá trị không nằm ở "hai người cùng kiểm" mà ở
"hai bên sót khác chỗ nhau"). Bộ test của tester **không thể** bắt được §3 vì
assert dạng `not in` luôn XANH khi nội dung bị xoá nhiều hơn cần thiết —
xoá càng mạnh, test càng xanh.

Với `agent_note` (§4) tôi KHÔNG grep tên (bài học C4: grep-tên sai cả hai
chiều) — tôi gọi đúng route thật rồi đọc thẳng DB.

---

## 2. XANH — những gì thực sự đã đo và ĐẠT

### 2.1 Bộ test đối kháng chạy lại trong phiên

```
pytest tests/test_api/test_reject_note_doi_khang.py
→ 15 passed, 1 skipped, 0 failed
```

Ca skip DUY NHẤT là `test_14` — exporter Phase 2 (`eval/candidates/`) chưa có
mã. Skip **hợp lệ và có ích**: nó là cọc mốc cắm sẵn cho một ranh giới chưa
tồn tại, không phải lỗ đang hở. (Ranh giới đó là điểm EXPORT, không phải điểm
hiển thị — vẫn đúng như sign-off TM-03.)

### 2.2 Che PII tại điểm ghi — 12 ca, che sạch

`scrub_pii` trên ghi chú nhân viên gõ tay, tiếng Việt có dấu:

| Ca | Thô | Sau scrub |
|---|---|---|
| SĐT thường | `…gọi số 0912345678 xác nhận…` | `…gọi số [VN_PHONE_NUMBER/VN_ID_NUMBER] xác nhận…` |
| SĐT định dạng lạ | `091.234.5678` và `0912-345-678` | cả hai → `[PHONE_NUMBER]` |
| CCCD 12 số | `CCCD 001234567890` | `CCCD [VN_ID_NUMBER]` |
| Tên người | `Anh Trần Văn Bách bên kỹ thuật…` | `Anh [PERSON_VN] bên kỹ thuật…` |
| STK + số thẻ | `88000000000194`, `9704123456789012` | cả hai → `[VN_ID_NUMBER]` |
| Email | `hoa.nguyen@example.com` | `[EMAIL_ADDRESS/URL]` |
| SĐT `+84` | `+84912345678` | `[VN_PHONE_NUMBER/VN_ID_NUMBER]` |

Fail-closed cũng đúng thiết kế: scrub ném exception → route trả 500, **không
có đường nào ghi bản thô rồi hẹn che sau** (`main.py:1033-1041`).

### 2.3 "giữ-4-số" — vế này tôi ghi SAI trong sổ, hành vi thật MẠNH HƠN

`note` **không** giữ 4 số cuối, nó thay trọn bằng `[NHÃN]`. Đúng như vậy mới
đúng, và tôi ghi nhầm khi mang quy ước của lớp khác sang:

- `mask_phone`/`mask_account_no` (`src/tools/masking.py`, BR-06/BR-07) giữ 4 số
  cuối vì đó là lớp **HIỂN THỊ** — DB vẫn giữ bản đầy đủ, che chỉ xảy ra lúc
  trả ra ngoài.
- `note` thì ngược hẳn: **DB chỉ còn bản đã che**, không có bản gốc ở đâu cả.
  Giữ 4 số cuối ở đây nghĩa là **ghi vĩnh viễn 4 chữ số thật của khách vào bản
  ghi kiểm toán** — 4 số cuối SĐT/thẻ là dữ liệu định danh có giá trị tái nhận
  dạng thật, và nó sẽ nằm trong mọi bản sao lưu.

⟹ Vế "giữ-4-số" **rút khỏi tiêu chí nghiệm thu của `note`**. Hành vi hiện tại
(thay trọn) là lựa chọn đúng, không phải thiếu sót.

### 2.4 Không lộ transcript

Đo lại các đường: `note` chỉ hiện ở route đã gated `cskh,supervisor`; không
xuất hiện ở route khách; không vào `build_customer_tools()`; không ra log
(`test_12` xanh). Ranh giới đọc **không** bị nới — đúng Quyết định 4 của
ADR-024.

---

## 3. 🔴 FINDING S-01 (CAO) — scrub xoá mất CĂN CỨ TỪ CHỐI: chặn nhầm 8/20 = 40%

### Số đo

Corpus đối chứng: **20 ghi chú CSKH dạng thật, KHÔNG chứa một mẩu PII nào**.
Bất kỳ thay đổi nào ở đây đều là chặn nhầm.

```
KẾT QUẢ CHẶN-NHẦM: 8/20 = 40%
```

### Ca nặng — không phải "che dư một chữ", mà là **mất căn cứ pháp lý của quyết định**

| Thô (nhân viên gõ) | Lưu vào DB |
|---|---|
| `Thời hạn khiếu nại đã quá quy định, từ chối theo chính sách.` | `…từ chối [PERSON].` |
| `Khách đã rút khiếu nại qua tổng đài, không cần xử lý tiếp.` | `[LOCATION] đã rút khiếu nại qua tổng đài, không [PERSON].` |
| `Giao dịch nằm ngoài phạm vi hoàn tiền theo chính sách hiện hành.` | `…ngoài phạm vi hoàn tiền [PERSON] hiện hành.` |
| `Số tiền tranh chấp nhỏ hơn ngưỡng, xử lý theo luồng rút gọn.` | `…nhỏ hơn ngưỡng, [PERSON] luồng [PERSON].` |
| `Cần xác minh thêm trước khi trình duyệt, chuyển lại điều tra.` | `Cần xác minh thêm [PERSON] duyệt, chuyển lại điều tra.` |
| `Gọi lại giúp khách vào đầu giờ chiều mai.` | `…vào đầu [ORGANIZATION] mai.` |

`note` tồn tại để supervisor đọc và hiểu **vì sao** một đề xuất bị từ chối
(ADR-019 → ADR-024: `reject_reason='khac'` BẮT BUỘC kèm ghi chú). Một bản ghi
đọc ra `"…từ chối [PERSON]"` thì **không còn là bản ghi kiểm toán** — nó
không tái dựng được căn cứ, và tệ hơn: **không ai biết chữ nào đã mất**.

### Vì sao đây KHÔNG phải "đánh đổi đã chốt"

ADR-024 Quyết định 3 có chấp nhận che nhầm, nhưng tiền đề đo được của nó là
**mã 12 số trùng pattern CCCD** (`test_03`) — tức che nhầm một **chuỗi định
danh**. Lớp chặn nhầm tôi vừa đo là **cụm nghiệp vụ tiếng Việt thuần bị NER
gán nhãn thực thể**, chưa từng được đo, và hậu quả khác hẳn về chất: một bên
che dư một mã, một bên **đổi nghĩa một câu**.

**Ràng buộc DB vẫn XANH trong khi mục đích nghiệp vụ đã hỏng** (điểm của
tech-lead, ghi lại vì nó là phần dễ bỏ sót nhất): `"…từ chối [PERSON]"` thoả
đầy đủ CHECK `ck_resolutions_note_bat_buoc_khi_khac`
(`length(trim(note)) > 0`) — cột có nội dung, constraint hài lòng, test xanh,
**và bản ghi rỗng nghĩa**. Lớp phòng vệ ép-ở-tầng-DB mà ADR-024 dựng lên
(đúng đắn) không thể phát hiện lớp hỏng này, vì nó đếm ký tự chứ không đọc
nghĩa.

**Đây là sai NHẬN DẠNG, không phải sai NGƯỠNG** — ghi rõ để hồ sơ không bị
đọc thành "PO chọn một con số". NER gán `[PERSON]` cho `chính sách`,
`[LOCATION]` cho `Khách`, `[ORGANIZATION]` cho `giờ`. Không có ngưỡng nào
nới hay siết chạm được lớp lỗi đó; đường vá phải nằm ở chỗ khác (§ đề xuất).

Đây đúng hình dạng **Luật 8** (đo lại giao của các quyết định): quyết định
"tái dùng `scrub_pii`" dựa trên tiền đề "che nhầm là chấp nhận được", tiền đề
đó được đo ở **log/trace**, rồi bị mang sang **bản ghi có giá trị pháp lý** mà
không đo lại. Và họ hàng gần với **F-25** (mẫu tier-1 mở rộng xoá trắng chính
sách thật) — cùng một hình dạng: lớp phòng vệ tự tin xoá nội dung thật.

### Gốc kỹ thuật (đã khoanh, chưa kê đơn)

- `scrub_pii` docstring tự khai phạm vi: *"DÙNG HÀM NÀY cho mọi **log/span
  attribute**"*. Mất một chữ trong log = không sao. Mất một chữ trong bản ghi
  kiểm toán = chuyện khác. ADR-024 **đổi hạng mục sử dụng** của hàm này.
- Nguồn FP là lớp spaCy `xx_ent_wiki_sm` — model đa ngữ nhỏ, chính docstring
  `pii.py:32` đã ghi *"KHÔNG chuyên tiếng Việt"*. Nhãn FP đều là
  `[PERSON]/[LOCATION]/[ORGANIZATION]` (spaCy), KHÔNG phải `[PERSON_VN]`
  (underthesea, lớp tự viết).

### ⚠️ Cạm bẫy cho bản vá — đừng chỉ tắt lớp spaCy

Cách sửa "hiển nhiên" là bỏ nhãn generic của spaCy, giữ `PERSON_VN`. **Đo cho
thấy làm vậy sẽ mở một lỗ rò thật**: ca `Nguyễn Thị Hoa` bị bắt bởi ĐÚNG lớp
spaCy (`[PERSON]`), underthesea **bỏ sót** (nhãn gộp chỉ có `PERSON`, không có
`/PERSON_VN` — trong khi ca `Lê Thu Hà` ở N-08 có gộp `[LOCATION/PERSON_VN]`,
chứng minh cơ chế gộp nhãn có hoạt động). Tắt spaCy = đổi lỗ toàn-vẹn lấy lỗ
bảo-mật. **Không nhận đánh đổi đó.**

### Đề xuất (PO quyết — đụng tiền đề ADR-024, không phải việc tôi tự chốt)

Nguyên tắc tôi đề nghị chốt trước, độc lập với cách implement:

> **Một phép che trong trường kiểm toán phải NHÌN THẤY ĐƯỢC là một phép che,
> và không được phép đổi nghĩa phần câu còn lại.**

Ba đường, tôi xếp hạng:

1. **KHUYẾN NGHỊ — xác nhận vòng tròn lúc ghi (fail-visible, không cần cải
   thiện NER).** Nhân viên gõ note → API trả về **bản đã che** → nhân viên xác
   nhận hoặc viết lại. Sửa được gốc vấn đề (im lặng) mà **không đụng vào chất
   lượng NER**, vốn là bài toán đắt và không có bộ gán nhãn tiếng Việt (cùng lý
   do ADR-022 hoãn PhoBERT). Đây là thay đổi UX + 1 route, không phải thay đổi
   lớp bảo mật.
2. Ghi kèm **số lượng vùng bị che** + hiển thị cho người đọc (`note_redactions`)
   — rẻ hơn (1), nhưng chỉ làm phép che *nhìn thấy được*, không cho người gõ
   cơ hội diễn đạt lại.
3. Tinh chỉnh entity-set theo trường — **KHÔNG khuyến nghị làm một mình** vì
   cạm bẫy ở trên; chỉ có nghĩa khi đã có corpus tiếng Việt gán nhãn để đo cả
   hai chiều.

Dù chọn đường nào: **cần một corpus đối chứng "ghi chú sạch" đứng thường trực**
(Luật 2 — ca đối chứng bắt buộc), nếu không bản vá chặt tay nhất luôn thắng
theo số đo. Corpus 20 ca của tôi ở §7 giao lại cho tester làm hạt giống.

---

## 4. 🔴 FINDING S-02 (CAO) — `InvestigationLog.agent_note`: cửa văn bản tự do THỨ HAI, KHÔNG scrub

### Tiền đề bị bác

ADR-024 (và docstring bộ test của tester) đứng trên câu này:

> *"`note` là chỗ **DUY NHẤT** trong toàn hệ thống nơi văn bản tự do do nhân
> viên gõ đi vào cùng bản ghi với dữ liệu kiểm toán"*

**Câu này SAI.** Route `POST /tickets/{ticket_id}/request-more-info` (US-012,
gated `cskh,supervisor`) nhận `RequestMoreInfoRequest.note: str | None` và ghi
thẳng vào `InvestigationLog.agent_note` (`main.py:1154`).

### Probe hành vi (gọi route thật, đọc thẳng DB — không grep tên)

```
[1] POST /tickets/{id}/request-more-info -> HTTP 200
[2] agent_note ĐỌC THẲNG TỪ DB:
    'Khách Trần Văn Bách, sđt 0912345678, CCCD 001234567890, thẻ 9704123456789012'
[3] PII còn NGUYÊN VĂN trong bản ghi kiểm toán? -> True
      '0912345678'        còn trong DB: True
      '001234567890'      còn trong DB: True
      '9704123456789012'  còn trong DB: True
      'Trần Văn Bách'     còn trong DB: True

[4] note 5000 ký tự -> HTTP 200; độ dài lưu DB = 5000   (note của reject chặn ở 500)
[5] payload injection  -> HTTP 200; lưu DB nguyên văn: True
    trường cờ nào cho InvestigationLog? -> KHÔNG CÓ
```

### Đối chiếu hai cửa — cùng một loại dữ liệu, ba lớp phòng vệ lệch nhau

| | `resolutions.note` | `InvestigationLog.agent_note` |
|---|---|---|
| scrub PII lúc ghi | ✅ fail-closed | ❌ **không có** |
| trần độ dài | ✅ 500, ép ở DB | ❌ **không có** (nhận 5.000) |
| cờ injection | ✅ `note_flagged` (Luật 18) | ❌ **không có cột nào** |
| mã hoá at-rest | ❌ `Text` thuần | ❌ `Text` thuần |
| ranh giới đọc | staff-gated | staff-gated ✅ |

### Mức độ — CAO, nhưng nói cho đúng phạm vi

- **KHÔNG phải lỗ rò ra khách.** Tôi đã kiểm mọi đường đọc `agent_note`:
  `main.py:750` (`GET /tickets/{id}`) và `live_chat.py:191`
  (`get_handoff_context`, gọi từ `main.py:1328/1396`) — **cả ba đều gated
  `cskh,supervisor`**. Không có đường khách, và node agent ghi
  `agent_note=None` (`investigation_log.py:82`) nên **không vào ngữ cảnh LLM**
  hôm nay.
- **Là rủi ro tuân thủ + rủi ro tương lai:**
  1. **Số thẻ (PAN) 16 số nằm plaintext trong DB.** Trong khi dự án ĐÃ có sẵn
     `EncryptedString`/`EncryptedText` và đã áp cho `bank_accounts.account_no`
     (`models.py:92`), nội dung chat (`:475`) và văn bản RAG (`:513`) — tức
     `agent_note` chỉ đơn giản **bị bỏ sót**, không phải một quyết định.
     NĐ 13/2023 (tối thiểu hoá + bảo vệ dữ liệu cá nhân) áp thẳng vào đây.
  2. **Phễu học Phase 2.** `test_14` của ADR-024 cắm cọc cấm `note` ra file ứng
     viên — **không có cọc nào cho `agent_note`**, trong khi
     `investigation_logs` mới chính là thứ tự nhiên nhất để xuất làm dữ liệu
     học (nó là vết điều tra). Payload injection lưu nguyên văn (probe [5]) sẽ
     đi thẳng vào bộ học nếu exporter viết ra mà không ai nhớ trường này.
  3. **Không trần độ dài** = một trường text tự do không giới hạn trong bảng
     kiểm toán, ghi được bởi mọi tài khoản CSKH.

### Đề xuất

Áp **đúng ba lớp đã có sẵn** cho `note`, không phát minh gì mới (và đúng tinh
thần Quyết định 2 của ADR-024: một nguồn sự thật, không dựng bộ mẫu song song):
scrub tại điểm ghi fail-closed · trần 500 ký tự · cờ tier qua
`_phan_loai_tier()`. Cộng thêm: cân nhắc `EncryptedText` cho `agent_note`.

⚠️ **Nhưng phải chờ S-01 chốt trước** — nếu bê nguyên `scrub_pii` sang thì bê
luôn lỗi 40% chặn nhầm sang một trường thứ hai. **Hai finding này phải sửa
CÙNG một quyết định, không sửa lẻ.** (Luật 8 áp cho chính bản vá của tôi.)

---

## 5. 🟡 FINDING S-03 (TRUNG BÌNH) — exception gửi lên trace KHÔNG qua scrub

`src/observability/langchain_callback.py:96-98`:

```python
if error is not None:
    span.set_status(StatusCode.ERROR, str(error))
    span.record_exception(error)
```

Mọi text khác đi vào span đều qua `_scrub_and_truncate` — và khối đó được viết
rất kỹ (cắt-trước-scrub-sau, có biên `_SCRUB_WINDOW` chống tên nằm vắt ngang
mốc cắt). Nhưng **hai dòng này đi thẳng ra backend trace không qua lớp nào**:
`str(error)` và `record_exception` (ghi cả message lẫn stacktrace thành span
event).

Vi phạm đúng điều khoản Giai đoạn 3 của checklist observability: *"Scrub PII
phải chạy TRƯỚC khi dữ liệu được gửi lên backend trace — nếu trace đã lên cloud
rồi mới scrub thì dữ liệu gốc đã rời khỏi vùng kiểm soát."*

**Nói cho đúng mức độ — chưa đo được rò thật:** traceback MT-E02/MT-F01 tôi đọc
được (§6) **không chứa PII** (SQLite chỉ trả `FOREIGN KEY constraint failed`,
không echo tham số). Rủi ro là **có cấu trúc, chưa có ca dương tính**: exception
loại khác thì có echo dữ liệu vào message — `ValidationError` của Pydantic in
lại giá trị đầu vào, `IntegrityError` của Postgres in lại `DETAIL: Key
(phone)=(0912345678) already exists`. **Postgres hành xử khác SQLite ở đúng
điểm này**, mà production là Postgres còn test là SQLite ⟹ đây là lớp lỗi chỉ
lộ ra sau khi deploy thật.

**Đề xuất:** cho `str(error)` và exception message đi qua `scrub_pii` trước khi
vào span. Rẻ, không đụng luồng nghiệp vụ. Không chặn gate nào.

---

## 6. MT-E02 — thu hẹp được đáng kể, CHƯA đóng

Việc treo của tôi là "MT-E02 traceback". Đã đọc traceback đã lưu trong
`eval/results/adversarial_run_*_raw.json`. Thu được:

- **Chỗ nổ xác định chính xác:** `graph.py:429 (run_agent_turn)` →
  `write_investigation_logs_for_ticket` → `investigation_log.py:89
  session.flush()` → `sqlite3.IntegrityError: FOREIGN KEY constraint failed`
  (FK `investigation_logs.ticket_id → tickets.ticket_id`).
- **MT-E02 và MT-F01 có traceback TRÙNG HÌNH DẠNG** — cùng chỗ nổ, cùng FK.
  STATE ghi "cùng IntegrityError/FK" như một quan sát; nay khẳng định được là
  **cùng một chỗ nổ**, không chỉ cùng loại lỗi. ⟹ hai nhãn nhiều khả năng là
  **một defect**, và việc coder gọi "MT-F01" / tester gọi "MT-E02" (STATE ghi
  nhận đối chiếu label) là hai tên cho cùng một thứ.
- **Lớp defect nhìn ra được từ code** (`graph.py:412-428`): `ticket_id` được
  moi ra từ **payload trong lịch sử tin nhắn của LLM**, rồi dùng thẳng làm FK
  để insert — **không có bước xác nhận hàng đó còn tồn tại trong DB**. Bất kể
  cơ chế nào sinh ra `ticket_id` cũ/không hợp lệ (rollback giữa chừng, lịch sử
  được phát lại sau một lượt trượt, v.v.), lớp lỗi vẫn là *tin vào id do
  history cung cấp mà không kiểm tồn tại*.

**KHÔNG kết luận** cơ chế sinh ra id cũ — tôi chưa đo được, và theo Luật 5
(lượt LLM sinh để KHÁM PHÁ, lượt viết cứng để ĐIỀU TRA) thì không được quy
nhân quả từ một lượt adversary không tái lập. **Vẫn giữ nguyên: ĐỪNG đốt TPM
tái hiện chủ động.**

**Góc bảo mật khiến việc này không chỉ là phiền toái của eval:** khi flush này
chết, **`investigation_logs` của lượt đó KHÔNG được ghi**. Mà `investigation_logs`
chính là mắt xích giữa của chuỗi truy vết mà **ràng buộc cứng 3** dựng lên
(`tool_results` → `investigation_logs.tool_result_id` →
`resolutions.cited_tool_result_ids`). Đứt mắt xích giữa = mất khả năng truy vết
của cả lượt, im lặng. Đề nghị coder xử lý như lỗi **toàn vẹn truy vết**, không
phải flake của bộ đo.

---

## 7. Bàn giao cho vai khác

**Cho tester** — corpus đối chứng "ghi chú sạch" (hạt giống, 20 ca) nằm trong
probe của tôi ở scratchpad; 8 ca đang chặn nhầm là:
`Khách không cung cấp đủ bằng chứng…` · `Giao dịch nằm ngoài phạm vi hoàn tiền
theo chính sách hiện hành.` · `Gọi lại giúp khách vào đầu giờ chiều mai.` ·
`Khách đã rút khiếu nại qua tổng đài, không cần xử lý tiếp.` · `Số tiền tranh
chấp nhỏ hơn ngưỡng, xử lý theo luồng rút gọn.` · `Cần xác minh thêm trước khi
trình duyệt, chuyển lại điều tra.` · `Khách đồng ý phương án xử lý, chờ xác
nhận bằng văn bản.` · `Thời hạn khiếu nại đã quá quy định, từ chối theo chính
sách.`
Đề nghị dựng thành ca đối chứng thường trực cho MỌI lớp che/lọc chạm `note`.
Ngưỡng đề nghị: **0/20**, không phải "thấp hơn" (cùng kỷ luật đã dùng cho
over-block O1-O4 27/96 → 0/96).

**Cho coder** — 3 việc, **không sửa lẻ S-01/S-02** (§4). S-03 sửa được ngay,
độc lập. MT-E02 xem §6.

**Cho PO** — cần quyết: (1) nguyên tắc "phép che trong trường kiểm toán phải
nhìn thấy được" (§3); (2) chọn đường 1/2/3 cho S-01; (3) `agent_note` có phải
thay đổi contract không — tôi đọc là **KHÔNG** (không thêm route, không đổi
`authority-matrix.yaml`, chỉ thêm cột + scrub, đúng hình dạng ADR-024) nhưng
việc đó thuộc thẩm quyền PO + tech-lead, tôi không tự kết luận thay.

---

## 8. Còn treo của tôi (không đóng trong phiên này)

- **Mốc nền đối kháng 18/20** (`he_thong 6c5fff420bb9`): hôm nay cây làm việc
  đo ra `fd16681d8088`. Trôi là **đúng dự kiến** (O1-O4 + F-27 + `note` đã land
  từ lúc đó), nhưng hệ quả phải nói rõ: **mọi lượt đo mới KHÔNG ghép cặp
  hợp lệ với mốc nền cũ nữa** (Luật 6 — đổi `he_thong` + giữ `cham_diem` là
  cặp HỢP LỆ theo nghĩa so được, nhưng "trước/sau" thì vật đã khác). Đợt
  CỔNG-A cần **mốc nền mới** đóng băng ở một `he_thong` xác định trước khi tiêu
  TPM, nếu không sẽ lặp lại đúng sự cố `8e46f28→6c5fff`.
- **oracle-phủ-định "không phải 21"** (1 bit/lượt, có tài liệu) — vẫn chờ đợt
  CỔNG-A gộp 3 oracle. Không đổi trạng thái trong phiên này.
- **Rà pipeline scrub trước log/trace** — làm được phần OTel/callback (§5).
  **Chưa rà:** đường Langfuse (đang TẮT có chủ đích, `LANGCHAIN_TRACING_V2=false`)
  và đường log của eval (`logging_config` chưa từng init ở runner — 0 dòng JSON,
  đã ghi trong sổ Đợt 2). Nói rõ để không ai đọc §5 thành "đã rà hết".
