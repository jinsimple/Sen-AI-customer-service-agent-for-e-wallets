# Phân xử hai câu treo (ADR-031) + ranh giới ĐO ĐƯỢC của hồ sơ Đ.25

> Vai: **security** · 2026-08-18 · **0 lượt LLM.** Ghi trong `docs/security/`, không chạm vùng khác.
>
> **Dấu vết của vật đã đo** — mọi số dưới đây đo trên đúng ba ảnh này:
> ```
> băm src/ trong container   b8e7c5397457      (tính lại tại chỗ, không đọc nhãn)
> BUILD_COMMIT               bec7235 · bec7235 · bec7235
> sửa-tay (docker diff, trừ __pycache__)   0 · 0 · 0
> HEAD                       addec5e
> ```
> Khớp §2 `docs/STATE.md`. **Không `recreate`, không `restart`, không ghi gì vào container**
> trong cả phiên đo này — *đọc trước, dọn sau*, và lần này không có gì phải dọn.

---

## §0. Hạng bằng chứng — khai trước, vì nửa tài liệu này nằm NGOÀI vùng có vật đo

| Mục | Hạng bằng chứng | Ai kết luận được |
|---|---|---|
| ② `tool_input_json` plaintext | **[ĐO]** trên CSDL sống + `models.py` | tôi |
| ① mức audit-log | **[ĐO]** trên `access.log` thật, 22.389 dòng | tôi |
| 6 ca test TÊN≠ASSERTION | **[ĐO]** trên thứ tự câu lệnh trong `src/` | tôi |
| Đ.25 — *"15/08 có gõ dữ liệu THẬT không"* | **[ĐO] một phần**, phần còn lại **không đo được từ đây** | **PO thật**, sau khi tôi thu hẹp câu hỏi |
| A6 — hai công tắc logging nhà cung cấp | **CHƯA KIỂM · chỉ kiểm được bằng đăng nhập console** | **PO thật** |
| ToS mức hợp đồng, chế độ pháp lý nơi nhận | **ngoài vùng có vật đo** (Luật C) | người có thẩm quyền pháp lý |

---

## §1. Câu ② — CÓ, finding riêng. **Nhưng KHUNG ban đầu của tôi SAI — xem §1.0 trước.**

### 🔴 1.0 ĐÍNH CHÍNH (cùng ngày, sau khi PO-agent kiểm lại) — tôi đọc một MẪU thành một DÂN SỐ

**Tôi đã viết:** *"`complaints.description_raw` → `gAAAAABqgx…` ✅ ciphertext"*, rồi dựng cả finding
① trên khung **"cột ĐÃ mã hoá đang có bản sao plaintext ở bảng khác"**.

**Bắt bởi:** PO-agent. **Kiểm lại độc lập, [ĐO] trên dân số đầy đủ — số của tôi khớp số của họ:**

```
complaints.description_raw   PLAINTEXT  738   tạo 05/05 → 14/08     ← 97%
                             MÃ HOÁ      23   tạo 15/08 → 17/08
```

**Khung SAI.** Không phải *"lớp mã hoá bị đi vòng"* — **cột chính ĐANG 97% PLAINTEXT TRÊN ĐĨA.**
`EncryptedText` gắn vào khoảng 15/08 và **738 dòng cũ chưa bao giờ nạp lại**.

**Tôi sai thế nào, nói thẳng vì tôi sẽ dùng lại nếp này:** tôi chạy
`ORDER BY created_at DESC LIMIT 3`. Ba dòng ấy **là ba dòng mới nhất**, và ba dòng mới nhất nằm gọn
trong 23 dòng đã mã hoá. **Bộ lọc do chính tôi gõ ra, rồi tôi đọc khung nhìn đã lọc ấy như toàn cảnh**
— đúng §8, và **đúng lớp lỗi tôi vừa tự bắt được ở ca `447` trong cùng tài liệu này**.

> ⚠️ **Điểm đáng ghi nhất, và nó KHÔNG có trong bài học §8 cũ:** ở ca `447` tôi bắt được vì **tôi đang
> đi tìm** — con số trông quá lớn nên tôi soi bộ dò. Ở ca này tôi trượt vì **con số trông đúng như
> tôi mong đợi**. §8 dạy *"dữ liệu trông QUÁ GỌN thì hỏi cái gì đã không sinh ra dòng nào"*. Ca này
> bổ sung vế thiếu: **dấu hiệu nguy hiểm hơn không phải "quá gọn" mà là "ĐÚNG NHƯ TA ĐOÁN"** — vì
> lúc ấy không có gì kích hoạt phản xạ soi lại. Tôi đã soi bộ dò khi nó cho câu trả lời tôi không
> muốn, và không soi khi nó cho câu trả lời tôi muốn. **Cùng một người, cùng một tài liệu, cách nhau
> vài đoạn.**

### 1.0b Vì sao KHÔNG AI thấy 738 dòng ấy — và vì sao nó nguy hiểm hơn một cột quên mã hoá

[ĐO] `src/db/crypto_types.py` — **cả hai** lớp (`EncryptedString` ~dòng 40, `EncryptedText` ~dòng 73)
kết thúc bằng:

```python
except InvalidToken:
    return value          # ← trả NGUYÊN VĂN, không log, không đếm, không cờ
```

Ứng dụng đọc 738 dòng plaintext ấy **không một lỗi nào, không một dòng log nào**.

> 🔴 **Đây là Luật H ở dạng mạnh nhất dự án từng gặp.** Các ca trước: nhánh lỗi **in ra một KẾT LUẬN**
> (*"kho rỗng"*, *"KHÔNG KÊU — phép kiểm vô dụng"*) — sai, nhưng **có phát ra tín hiệu** nên bác được.
> Ca này nhánh lỗi **không phát ra gì cả — nó giả trang thành THÀNH CÔNG.** Không có dòng nào để bác.
> **Ba trạng thái (`giải mã được` · `plaintext cũ` · `sai khoá`) bị gộp thành một đường trả về duy nhất.**

**Và nó gộp đúng hai trạng thái KHÔNG ĐƯỢC PHÉP gộp** — PO-agent nêu vế thứ hai, tôi xác nhận bằng
đọc mã: nếu `FIELD_ENCRYPTION_KEY` bị xoay, 23 dòng đã mã hoá **không báo lỗi**; chúng trả về nguyên
chuỗi `gAAAAA…` **như thể đó là nội dung lời khai**. Cảnh báo STATE §1 *"không xoay khoá"* vì thế
nặng hơn mức đang ghi: **không phải "mất dữ liệu" mà là "hỏng dữ liệu IM LẶNG, và bản ghi hỏng trông
vẫn hợp lệ".**

⟹ **Bản vá rẻ, khôi phục được trạng thái thứ ba, đề nghị cho tech-lead:** tiền tố `gAAAAA` là dấu
hiệu **tin cậy** của một Fernet token (byte phiên bản `0x80` → base64url luôn mở đầu `gA`). Nên nhánh
`except` phân biệt được hai ca mà không cần thêm cột nào:

```
value BẮT ĐẦU bằng "gAAAAA" mà decrypt hỏng  →  SAI KHOÁ    →  ném lỗi / cảnh báo, KHÔNG nuốt
ngược lại                                     →  plaintext cũ →  trả nguyên văn (như hiện nay)
```

**Đây là bản vá phải land TRƯỚC mọi thao tác xoay khoá**, không phải sau.

### 1.1 Phạm vi của nợ mã hoá — [ĐO] **toàn bộ** lớp, không chỉ cột PO-agent tìm thấy

> 📌 **NIÊM 18/08 ~09:30 (Luật P) — bảng dưới đây là ẢNH CHỤP lúc 08:xx, nay đã CŨ. Thân giữ nguyên.**
> Backfill ADR-032 ② **đã chạy thật**. Kiểm độc lập bằng `psql` của tôi:
> **`complaints.description_raw` = 761 MÃ HOÁ · 0 PLAINTEXT.** Dòng `23 / 738` dưới đây **không còn
> đúng với hiện tại**.
> **Không sửa số trong thân** — `23/738` là số **đúng của thời điểm nó được đo**, và cả §1.4/§1.5
> dựng lập luận **trên** con số ấy. Sửa nó đi thì mất luôn lập luận, và mất luôn bằng chứng cho
> Luật M (§6). Ba cột còn lại **không đổi**: `messages.content` 467/0 · `policy_chunks.text` 378/0 ·
> `bank_accounts.account_no` 245/0.

Đây là phần tôi thêm vào sau đính chính: một cột hỏng thì phải hỏi **cả họ có hỏng không**.

| Cột dùng `Encrypted*` | MÃ HOÁ | PLAINTEXT | |
|---|---|---|---|
| `messages.content` | 467 | 0 | ✅ sạch |
| `policy_chunks.text` | 378 | 0 | ✅ sạch |
| `bank_accounts.account_no` | 245 | 0 | ✅ sạch |
| **`complaints.description_raw`** | 23 | **738** | 🔴 **nợ migrate** |

⟹ **Nợ khu trú ở ĐÚNG MỘT cột — không phải hỏng hệ thống mã hoá.** Ba cột kia có `EncryptedText` từ
đầu hoặc đã được nạp lại; `description_raw` là cột **mới nhất** được gắn kiểu (A1 của ADR-025, land
~15/08) và nó được gắn lên một bảng **đã có 738 dòng**. Kết quả này **thu hẹp việc sửa xuống một
script backfill**, và đó là tin tốt duy nhất trong mục này.

### 1.2 Xác nhận tiền đề của finding ①, [ĐO]

```
src/db/models.py:328   tool_input_json: mapped_column(JSON, nullable=False)   ← JSON THƯỜNG
src/db/models.py:316   raw_json:         mapped_column(JSON, nullable=False)   ← JSON THƯỜNG
```

`investigation_logs.tool_input_json → description_raw` = chữ Việt có dấu, **plaintext, 27/27 dòng.**

### 1.3 🔴 Đính chính ADR-031 **cũng bị lọc** — nó liệt kê 3 tool, thực tế có 5

Đính chính ghi `search_policy` (10) · `lookup_transaction` (11) · `get_customer_history` (44) = 65
dòng. Đếm đủ bảng:

| `tool_called` | dòng | khoá trong `tool_input_json` | mức nhạy cảm |
|---|---|---|---|
| `get_customer_history` | 44 | `days`, `amount` | thấp |
| 🔴 **`create_ticket`** | **27** | **`description_raw`**, `complaint_type`, `scope`, `trans_id`, `otp_disclosed` | **cao nhất — LỜI KHAI KHÁCH** |
| `lookup_transaction` | 11 | `trans_id`, `phone`, `amount`, `rec_code`, `date_from/to` | trung bình |
| `search_policy` | 10 | `query` | trung bình |
| `cskh_request_more_info` | 1 | `requested_by` | thấp |
| | **93** | | |

**`create_ticket` — 27 dòng, cột nặng nhất — không có trong đính chính.** Cùng lớp lỗi §8 STATE ở
dạng thuần nhất: đính chính đi tìm *"query được lưu ở đâu"*, nên tập tự đến chỉ gồm **tool ĐỌC**;
`create_ticket` là tool **GHI** nên nó không bao giờ xuất hiện trong khung nhìn ấy. **Bộ lọc vô hình,
và lần này nó nằm trong chính văn bản sửa lỗi cho một bộ lọc vô hình khác.**

### 1.4 Xếp lại hạng: HAI lỗ, khác NHAU VỀ LOẠI — và lỗ nhỏ hơn là lỗ KHÔNG tự khỏi

PO-agent nói *"`investigation_logs` là lỗ thứ hai, không phải lỗ lớn nhất"*. **Đúng theo số dòng
hôm nay.** Nhưng số dòng không phải trục duy nhất, và trục còn lại đảo thứ tự:

| | **E — `complaints.description_raw`** | **① — `investigation_logs.tool_input_json`** |
|---|---|---|
| dòng plaintext | **738** | 27 (lời khai) + 21 (mã GD·SĐT·query) |
| **loại lỗi** | **nợ MIGRATE** — cơ chế có, đúng, đang chạy cho ghi mới | **thiếu CƠ CHẾ** — chưa từng có gì |
| ghi mới hôm nay | ✅ được mã hoá | 🔴 **vẫn sinh plaintext, mỗi lượt** |
| sửa bằng | một script backfill, chạy một lần | một **quyết định thiết kế** (§1.6) |
| sau khi sửa xong lỗ kia | — | **vẫn nguyên vẹn** |

⟹ **E lớn hơn về tồn kho; ① lớn hơn về dòng chảy.** E là một **vũng nước** — đếm được, tát được,
tát xong là hết. ① là một **vòi đang chảy** — mỗi vé mới tạo thêm một dòng, và không script nào
đóng được vòi.

### 1.5 🔴 Và đây là phép đo chứng minh ① KHÔNG phải "một cột nữa cũng quên migrate"

Nếu ① chỉ là cùng một nợ migrate ở bảng khác, thì các dòng của nó sẽ **song hành** với các dòng
plaintext của E. [ĐO] — ghép 27 dòng `create_ticket` với chính `complaint` của chúng:

```
ngày log     trạng thái complaints.description_raw     số dòng
2026-08-13   complaint PLAINTEXT                          6
2026-08-14   complaint PLAINTEXT                          5
2026-08-15   complaint MÃ HOÁ                             3   🔴
2026-08-16   complaint MÃ HOÁ                             8   🔴
2026-08-17   complaint MÃ HOÁ                             5   🔴
```

> **16 trong 27 dòng có bản gốc ĐÃ MÃ HOÁ ĐÚNG và một bản sao PLAINTEXT nằm cạnh.**

Với 16 dòng ấy, cơ chế của ADR-025 **đã chạy, đã đúng, và vẫn bị đi vòng trong cùng một giao dịch.**
Đó là bằng chứng trực tiếp — không phải suy luận — rằng ① là **một lỗ thiết kế độc lập**, không phải
một triệu chứng khác của E. Và nó cho biết chuyện gì xảy ra sau khi E được vá:

🔴 **Vá E làm ① NẶNG THÊM về mặt tương đối, không nhẹ đi.** Backfill xong, `complaints` sạch 100% ⟹
`investigation_logs` trở thành **bản plaintext DUY NHẤT còn lại của lời khai khách**. Khung *"dựng
một cửa mới cạnh một cửa đang mở"* mà tôi viết ở §1.6 vẫn đúng — **chỉ là hai cánh cửa đổi vai cho
nhau so với bản tôi viết sáng nay.**

### 1.6 Ba biện pháp của ADR-025, và `investigation_logs` không có biện pháp nào

`description_raw` **chính là Nhóm A của ADR-025** — hạng "lời khai / bằng chứng", hạng mà ADR-025
Quyết định 1 dành riêng ba biện pháp: mã hoá at-rest, trần độ dài, che **lúc XUẤT** chứ không lúc ghi.

| Biện pháp ADR-025 cho Nhóm A | `complaints.description_raw` | bản sao trong `investigation_logs` |
|---|---|---|
| mã hoá at-rest | ⚠️ có cơ chế, **23/761 dòng** (§1.0) | 🔴 **không cơ chế** |
| trần chống flood ở DB | ✅ `CHECK length <= 12000` (QĐ 5) | 🔴 **không CHECK nào** — [ĐO] chỉ có PK/FK/not-null |
| retention "xoá dòng thật" 5 năm (QĐ 3) | nằm trong phạm vi | 🔴 **không được nêu tên** trong QĐ 3 |

Mục retention là mục dễ trượt nhất và nó có một cơ chế cụ thể, [ĐO]:

```
investigation_logs_ticket_id_fkey  →  delete_rule = NO ACTION
```

`NO ACTION` ⟹ xoá `tickets` sẽ **báo lỗi** chừng nào `investigation_logs` còn dòng. Người viết job
retention sẽ gặp lỗi đó, và cách sửa nhanh nhất là **xoá `investigation_logs` trước**. Nghĩa là mục
này *có thể* tự khỏi. Nhưng ADR-025 QĐ 3 liệt kê phạm vi là *"transcript + description + note +
agent_note gắn ticket"* — **`tool_input_json` không có trong danh sách** ⟹ nếu job xoá theo **danh
sách cột** thay vì theo **cây khoá ngoại**, bản plaintext sống sót sau khi bản mã hoá đã bị xoá.
**Đây là thứ phải ghim trước, không phải thứ để job tự phát hiện lúc chạy.**

### 1.7 Trả lời thẳng hai câu của đính chính

> **① Đây có phải một finding bảo mật riêng, độc lập ADR-031 không?**

**Có.** Ba lý do, và lý do thứ ba là lý do quyết định:

1. **Khác phạm vi dữ liệu.** ADR-031 nói về `search_policy.query` (10 dòng). Finding này nói về
   lời khai khách (27 dòng) + mã GD/SĐT (11 dòng) + query (10 dòng) = 48 dòng ở **ba hạng nhạy cảm
   khác nhau**, trong đó hạng nặng nhất **không phải** hạng ADR-031 đang bàn.
2. **Khác chiều tác động.** ADR-031 là *thêm bằng chứng để thoả ràng buộc cứng 3*. Finding này là
   *gỡ dữ liệu đã có ra khỏi chỗ nó không được nằm*. Một cái **thêm**, một cái **bớt**.
3. 🔴 **Khác vòng đời quyết định — và đây mới là lý do phải tách.** ADR-031 đang **TẠM DỪNG**, chờ
   PO thật quyết ba câu. Nếu finding này bị buộc vào ADR-031, thì **mọi ngày ADR-031 còn treo là một
   ngày finding này cũng treo** — mà nó **không phụ thuộc vào bất kỳ câu nào trong ba câu đó**. Nó
   đúng dù PO chọn một bảng hay hai bảng, cột mới hay cơ chế cũ.
   **Buộc một finding đã chín vào một ADR đang treo là cách chắc chắn nhất để nó không được vá.**

> **② Vá `tool_results` cho đúng chuẩn mà để bảng này như cũ — có phải "dựng một cửa mới cạnh một
> cửa đang mở" không?**

**Có, và hình dạng còn tệ hơn ẩn dụ đó.** Ẩn dụ "hai cửa" gợi ý hai lối vào ngang hàng. Thực tế:

- cửa mới (`tool_results.query`, HMAC `_bam_truy_van` + cột mã hoá) sẽ được **ghi vào ADR, vào
  contract, vào test** ⟹ nó **hiện ra** trong mọi bản kiểm kê sau này;
- cửa cũ (`investigation_logs.tool_input_json`) **không có trong contract như một cột nhạy cảm**,
  không có test nào canh, và [ĐO] nó chứa **hạng dữ liệu nặng hơn** cửa mới.

⟹ Sau bản vá, bảng kiểm kê sẽ **trông kín hơn trước** trong khi bề mặt nặng nhất không đổi. Đó là
**Luật G ở tầng hồ sơ**: cơ chế mới làm đúng việc của nó (`query` được bảo vệ), nhưng không làm việc
ta giả định (*"chữ khách không nằm plaintext"*). Và nó **đắt hơn không vá gì**, vì một hồ sơ trông
kín thì không ai đi kiểm lại.

### 1.8 Điều tôi **KHÔNG** kết luận ở finding này

- **Không** đề xuất mã hoá `tool_input_json` bằng `EncryptedText` như phản xạ đầu tiên. Cột này là
  `JSON` và **được truy vấn theo khoá** (`jsonb ? 'query'` — chính phép tôi vừa dùng). Mã hoá cả cột
  giết khả năng truy vấn đó, mà khả năng ấy đang là **dụng cụ điều tra duy nhất** (§3.2). Đúng hình
  dạng là **tách trường nhạy cảm ra khỏi khối JSON**, không phải mã hoá khối. **Nhưng đây là thiết
  kế, thuộc tech-lead — tôi nêu ràng buộc, không nêu bản vá.**
- **Không** quyết ba câu của ADR-031 thay PO. Finding này **độc lập** với cả ba.

---

## §2. Câu ① — mức bản ghi cho cột `query`: **KHÔNG phải hạng việc mới. Phần lớn ĐÃ CÓ.**

### 2.1 🔴 Tiền đề của câu hỏi bị làm tròn lên đúng một nấc (Luật B — luật của chính vai này)

Phát biểu đang lưu hành:

> *"`audit_log_middleware` chỉ ghi `path` ⟹ trả lời được «ai gọi endpoint nào», KHÔNG trả lời được
> «ai đọc BẢN GHI nào»."*

Vế đầu đúng. **Vế sau đúng cho MỘT LOẠI route và sai cho loại kia** — và cột `query` nằm ở loại nó
đúng… theo hướng thuận lợi. [ĐO] trên `access.log` thật, 22.389 dòng, 11/08 → 18/08:

```
$ grep '"path": "/tickets/TCK' access.log | (lọc status 200, gom theo identity+path)
cặp (danh tính, bản ghi) phân biệt được:  101

  USR-0205:supervisor   /tickets/TCK-ddd78e22867f   x9
  USR-0205:supervisor   /tickets/TCK-e5b1c615435d   x9
  USR-0201:cskh         /tickets/TCK-ddd78e22867f   x5
  USR-0201:cskh         /tickets/TCK-e5b1c615435d   x5
  USR-0201:cskh         /tickets/TCK-55a27eb7eea7   x4
```

**Đó chính là "ai đọc bản ghi nào", có sẵn, hôm nay, kèm vai.** Không phải suy luận từ code — tôi
dựng lại được bảng ấy từ nhật ký đang nằm trên đĩa.

### 2.2 Vì sao nó lại đúng — và vì sao điều đó KHÔNG phải may mắn

[ĐO] `src/api/main.py`: **toàn bộ** payload Nhóm A + `raw_json` được phục vụ bởi **đúng một route**:

```
main.py:708   @app.get("/tickets/{ticket_id}")
main.py:744       "description_raw": complaint.description_raw      ← Nhóm A, đã giải mã
main.py:785       "tool_result": …ToolResult….raw_json              ← đích mở rộng Pha-1 ADR-025
```

`grep description_raw|raw_json src/api/main.py` → **chỉ hai dòng này**. `GET /tickets` (bản danh
sách, 187 lượt) **không** trả `description_raw` — nó là siêu dữ liệu.

⟹ Route duy nhất đọc dữ liệu nặng là route **có định danh bản ghi trong đường dẫn**. Và cột `query`
mà ADR-031 định thêm vào `tool_results` sẽ được đọc **qua đúng dòng 785** ⟹ **thừa hưởng mức bản ghi
miễn phí, ngày nó land.**

### 2.3 Vậy khoảng trống THẬT nằm ở đâu — phân đôi bằng số

| Loại | Định danh nằm ở | Lượt trong log | Mức bản ghi |
|---|---|---|---|
| **Loại 1** `/tickets/TCK…` · `/resolutions/RES…` · `/live-chat/sessions/CHS…` | **đường dẫn** | ~530 | ✅ **đã có** |
| **Loại 2** `/policy-search` · `/tools/*` · `/agent/chat` | **thân request (POST body)** | ~5.265 | ❌ không lấy được từ middleware |
| **Loại 3** `GET /tickets` (danh sách) | trả về một **TẬP** | 187 | ⚠️ mức tập, không mức bản ghi |

**Và Loại 2 phần lớn nằm ngoài mục đích của Pha 1.** Pha 1 ADR-025 sinh ra để chống **rủi ro nội
gián đọc hồ sơ người khác**. `/policy-search` (4.576 lượt) là khách/agent **đặt câu hỏi**, không phải
nhân viên **đọc bản ghi của ai**. Log nó ở mức bản ghi là trả lời một câu không ai hỏi.

⟹ **Trả lời câu ①:** với cột `query`, **không cần hạng việc mới.** Việc còn lại là hai mục nhỏ, và
cả hai đều **không phải "thêm trường vào middleware"**:

1. **Loại 3** — `GET /tickets` trả một tập; nếu Pha 2 (`assigned_to`) tới, tập ấy chính là thứ cần
   audit. **Ghim lại, chưa làm.**
2. **`/agent/chat` + `/tools/*`** — cần nhật ký ở **phía GHI** (dòng đã sinh ra mang theo ai gây ra),
   không phải phía đọc. Đó lại đúng là `investigation_logs`, tức **§1**.

### 2.4 🔴 Nhưng cổng này có ba điểm yếu KHÁC, và không cái nào là "mức bản ghi"

Luật A vế hai: đừng khai một cổng xanh chỉ vì nó im. [ĐO]:

| | Đo được gì | Hệ quả |
|---|---|---|
| **Không xoay vòng** | không có `RotatingFileHandler` ở đâu trong `src/`; 4,5 MB / 22.389 dòng trong 7 ngày | tăng vô hạn; và **không bao giờ xoá** ⟹ bản thân nhật ký (chứa `ip` + `user_id`) vi phạm nguyên tắc **giới hạn lưu trữ** của NĐ 13/2023 — một cổng tuân thủ đang tạo ra một khoản nợ tuân thủ khác |
| **Không toàn vẹn** | tệp `-rw-rw-r--` do `appuser` sở hữu, **cùng user chạy tiến trình bị kiểm toán**; không append-only, không niêm phong | kẻ có shell trong container **viết lại được lịch sử của chính mình**. Nhật ký kiểm toán mà đối tượng bị kiểm toán ghi đè được là **bằng chứng hạng thấp** |
| **Không rời hộp** | mount `fin05_logs_data → /app/logs`; **không** chuyển ra ngoài | sống qua `recreate` ✅ nhưng **chết theo `down -v`**, và một sự cố phá container thì phá luôn dấu vết của sự cố ấy |

*(Tôi đã dự đoán sai điểm thứ ba theo hướng nguy hiểm hơn — tưởng `access.log` nằm trong lớp
writable nên `recreate` là mất. `docker inspect` cho thấy nó là **volume có tên**. Ghi lại vì nếu
ai đó dùng phán đoán sai đó để biện minh cho một quyết định, họ sẽ biện minh sai.)*

**Xếp hạng của tôi:** ba mục này **quan trọng hơn** mức bản ghi. Mức bản ghi là *"ta biết được gì"*;
ba mục này là *"thứ ta biết có đứng vững trước ai không"*. Nhưng cả ba **không chặn** ADR-031 —
chúng là nợ riêng của cổng audit, nên tôi ghi vào §7, không gói vào câu ①.

---

## §3. Hồ sơ Đ.25 — ⛔ **PO THẬT QUYẾT 18/08: BỎ, KHÔNG LÀM.** Giữ mục này làm hồ sơ lưu

> **Quyết định của PO thật (18/08, qua PO-agent, ghi ở STATE §5.A0):** dừng toàn bộ nhánh hồ sơ Đ.25.
> **Ⓐ/Ⓑ/Ⓒ/Ⓓ ở §3.5 không cần trả lời nữa.** Ràng buộc thứ tự ở §3.2 (*"phải kiểm kê xong trước khi
> vá ①"*) **TAN** — dụng cụ đo không còn phải giữ, bản vá plaintext land được sớm hơn. Tôi không
> tranh luận lại; đây là phạm vi của PO.
>
> 🔴 **Ranh giới, PO-agent đã ghi và tôi xác nhận nó là ranh giới đúng:** PO bỏ **HỒ SƠ GIẤY**, không
> bỏ **LỖ KỸ THUẬT**. 738 dòng lời khai plaintext trên đĩa (§1.0) và 93 dòng ở `investigation_logs`
> **vẫn là việc thật**, và chúng **không phải nghĩa vụ giấy tờ** — chúng là dữ liệu đang nằm sai chỗ.
>
> ⚠️ **Một hệ quả của §1.0 mà mục này viết khi chưa biết:** tôi đo *"0 chuỗi dạng SĐT ngày 15/08"*
> **chỉ trên `tool_input_json`**, vì tôi tưởng `description_raw` đã mã hoá. Thực tế **738 dòng lời
> khai plaintext từ 05/05** là một bề mặt đọc được **rộng hơn nhiều** so với thứ tôi đã quét. Kết
> luận §3.4 vì thế đứng trên một **mẫu số hẹp hơn mức cần thiết**. Hồ sơ đã bỏ nên tôi **không quét
> lại** — nhưng nếu câu này quay lại, **quét trên `complaints` trước, không phải trên `investigation_logs`.**

<details>
<summary>Nội dung §3 nguyên trạng lúc trước quyết định (giữ để tra lại)</summary>

### 3.1 Ngày, nói đúng chế độ (Luật B mở rộng)

```
demo mentor 15/08  +  60 ngày  =  14/10/2026
hôm nay 18/08                  →  CÒN 57 NGÀY
```

**Đây là một việc CÓ LỊCH, không phải một vi phạm cần khắc phục** — và câu đó chỉ đúng **nếu** đồng
hồ đã chạy, điều chưa ai xác định. Người tiền nhiệm đã viết *"quá hạn"* rồi phải rút; tôi giữ nguyên
cảnh báo ấy ở đây để con số 57 không bị đọc rời khỏi điều kiện của nó.

### 3.2 🔴 Điều trớ trêu, và nó tạo ra một RÀNG BUỘC THỨ TỰ có thật

**Bề mặt duy nhất tôi đọc được để trả lời câu Đ.25 chính là finding §1.**

`messages.content` mã hoá ⟹ tôi không đọc. `complaints.description_raw` mã hoá ⟹ tôi không đọc.
Thứ duy nhất còn plaintext và tra được là `investigation_logs.tool_input_json` — **đúng cái cột phải
vá**.

> ⟹ **Vá §1 sẽ XOÁ dụng cụ đo của câu Đ.25.** Đây là *"đọc trước, dọn sau"* ở tầng dữ liệu, không
> tầng container. **Phải chạy xong phép kiểm kê ở §3.3 và LƯU KẾT QUẢ trước khi bản vá land** — sau
> đó bề mặt này biến mất và câu hỏi *"buổi demo có dữ liệu thật không"* mất luôn cách trả lời bằng đo.

### 3.3 Kết quả kiểm kê 15/08 — và **một con số tôi RÚT trước khi nó rời khỏi đội**

Phép thử **LỎNG LẺO** (`0[35789][0-9]{8}` ở bất cứ đâu) cho:

```
tool_results:        447 dòng "chứa SĐT"     ← get_customer_history 352 · lookup_transaction 60 …
investigation_logs:  5 dòng lời khai có SĐT, 4 giá trị khác nhau, 0/4 khớp bộ seed users
```

Đó là một con số **rất dễ báo cáo** và nó sai. Nguyên nhân, [ĐO]:

```
trans_id = "TXN20260801000596"    chứa chuỗi con  "0801000596"   → khớp 0[35789][0-9]{8}
```

**`TXN` + ngày + số thứ tự sinh ra chuỗi con y hệt một SĐT Việt Nam.** Dải "111 SĐT" tôi đếm được ở
`get_customer_history` chạy từ `0518…` tới `0801…` — **đó là ngày tháng**, không phải đầu số nhà mạng.

Phép thử **NGHIÊM** (10 chữ số, hai đầu không dính chữ/số):

| Bề mặt | lỏng lẻo | **nghiêm** | thứ còn sống sót |
|---|---|---|---|
| `tool_results.get_customer_history` | 352 | **0** | toàn bộ là mảnh `trans_id` |
| `tool_results.create_ticket` | 1 | **0** | — |
| `tool_results.lookup_transaction` | 60 | 29 | 4 giá trị, **cả 4 thuộc `users.phone` bộ seed** |
| `tool_results.search_policy` | 34 | 34 | **1 giá trị duy nhất**, nằm trong văn bản chính sách (dạng mã số doanh nghiệp 10 số) |
| `investigation_logs` lời khai | 5 dòng | **1 dòng, ngày 17/08** | 1 giá trị không giải thích được |
| **`investigation_logs` lời khai NGÀY 15/08** | 1 dòng | **0 dòng** | — |

> 🔴 **`447` là con số bị RÚT hôm nay, và nó bị rút TRƯỚC khi rời khỏi đội.** Ghi vào đây để không ai
> trích lại, và vì hình dạng của nó đáng ghi: cùng một regex PII, dùng cho **CHE** thì false positive
> là đánh đổi **đúng** (che nhầm hơn để lọt — playbook observability GĐ3); dùng cho **ĐẾM** thì cùng
> false positive ấy **thổi phồng một báo động** theo đúng hướng người đọc sẽ hành động.
> **Cùng công cụ, hai mục đích, hướng sai số ngược nhau.** (Đề xuất thành luật — §6.)

### 3.4 ⟹ Kết quả cho ngày 15/08, và **chính xác nó KHÔNG chứng minh điều gì**

Trong ngăn xếp `fin05`, ngày 15/08:

```
messages            6  (3 khách + 3 nhân viên, 13:24 → 13:28)   ← content = "gAAAAABq…", MÃ HOÁ
create_ticket       3  lời khai plaintext, dài 67 · 122 · 134 ký tự
                       → phép thử NGHIÊM: 0/3 có chuỗi dạng SĐT
investigation_logs  11 · tool_results 43
```

**Điều này CHỈ loại trừ, và chỉ loại trừ một thứ, ở một chỗ.** Ba giới hạn, cả ba phải đi kèm con số:

1. 🔴 **Sai ngăn xếp có thể.** *"Ngăn xếp nào phục vụ `app.adaptivealgo.uk`"* đang là câu **chưa ai
   trả lời** (§7 hồ sơ KHAI≠CHẠY, 🔴 PO thật). Nếu demo chạy trên bản đã triển khai, **những dòng
   tôi vừa đo không phải dòng của buổi demo** và toàn bộ mục này rỗng. **Câu đó phải trả lời TRƯỚC.**
2. 🔴 **Tôi chỉ đo được SĐT. Câu hỏi có BA vế: SĐT · TÊN · mã giao dịch.** **HỌ TÊN THẬT không bắt
   được bằng regex** — đó đúng là lý do playbook đòi lớp NER ở GĐ3, và **tôi chưa chạy lớp đó**. Nên:
   *"0 SĐT ngày 15/08"* **không** hàm ý *"0 dữ liệu thật ngày 15/08"*. Đừng để vế đo được che vế
   không đo được.
3. 🔴 **6 tin nhắn ngày 15/08 mã hoá — tôi không đọc, và tôi không tự ý giải mã.** Khách có thể gõ
   SĐT thật trong khung chat mà **không** tạo vé; đường đó không đi qua `create_ticket`.

### 3.5 Việc còn lại cho PO thật — đã thu hẹp thành một danh sách ĐẾM ĐƯỢC

Câu *"buổi demo 15/08 có ai gõ dữ liệu thật không"* trả lời bằng trí nhớ được, nên nó là câu sai
dạng. Sau phép đo, nó thành:

```
Ⓐ  Ngăn xếp nào phục vụ app.adaptivealgo.uk lúc 14h–15h ngày 15/08?     ← chặn cả mục
Ⓑ  6 tin nhắn ngày 15/08 (13:24–13:28) — 3 tin phía khách. Ai gõ, gõ gì?
Ⓒ  3 lời khai plaintext 15/08 (67 · 122 · 134 ký tự) — có TÊN người thật không?
     LOG-eca112966417 · LOG-452190dde2e3 · LOG-59b87146009a
Ⓓ  1 chuỗi dạng SĐT trong lời khai, ngày 17/08 (KHÔNG phải 15/08), không thuộc bộ seed:
     LOG-f8d02c57138f  ·  TCK-00e9f34c6301  ·  09:38:20  ·  đuôi …678
     → số thật hay số bịa? Một câu hỏi có/không, cho một dòng.
```

**Bốn mục. Không mục nào cần trí nhớ về buổi demo** — Ⓑ/Ⓒ/Ⓓ trả lời được bằng cách mở đúng bản ghi
đã nêu tên. Ⓐ là câu duy nhất thực sự cần người biết hạ tầng.

*(⛔ Cả bốn mục **đã đóng** theo quyết định 18/08 ở đầu §3. Giữ nguyên văn để nếu câu quay lại thì
không phải dựng lại từ đầu.)*

> Và **Ⓓ đứng độc lập với đồng hồ Đ.25**: nếu đuôi …678 là số thật thì **dữ liệu thật đã rời biên
> giới ngày 17/08**, bất kể buổi demo 15/08 có hay không. Đó là một mốc kích hoạt **thứ hai**, muộn
> hơn nhưng **chắc chắn hơn** vì nó có bản ghi. Nếu Ⓐ xác nhận đúng ngăn xếp, hạn 60 ngày tính từ
> mốc **SỚM NHẤT** được xác nhận.

---

</details>

---

## §4. A6 — hai công tắc logging: khai hạng bằng chứng rồi DỪNG

**Phía ta khai gì, [ĐO] trên mã:** `grep` toàn `src/` cho `store=True` · `"store"` · `metadata=` ·
`user=` gửi kèm lời gọi model → **không dòng nào**. `ChatOpenAI` (`graph.py:395`) và
`OpenAIEmbeddings` (`store.py:108`) chỉ truyền `extra_body={"enable_thinking": …}`.

⟹ **Phía client, ta không chủ động bật lưu trữ nào.** Đây là một dòng **ghi được vào hồ sơ §3**.

🔴 **Và nó KHÔNG phải bằng chứng về công tắc phía tài khoản.** Cả hai công tắc (`Model monitoring`
của Alibaba, `stored completions`/org logging của OpenAI) là **cấu hình phía máy chủ, bật bằng một
nút trên console**. Không mã nào của ta nhìn thấy chúng; `grep` sạch **không nói gì** về chúng.

Hạng bằng chứng, đúng như Luật C ngoài vùng có vật đo:

| | Trạng thái | Kiểm được bằng | Ai |
|---|---|---|---|
| Alibaba `Model monitoring` | **CHƯA KIỂM** | đăng nhập console Model Studio, đọc công tắc, **ghi ngày kiểm** | PO thật |
| OpenAI stored completions / org logging | **CHƯA KIỂM** | đăng nhập dashboard OpenAI, mục Data controls | PO thật |

**Tôi không thao tác tài khoản của PO và không đoán trạng thái công tắc.** Hai ô này ở nguyên trạng
thái *"chưa kiểm"* — và *"chưa kiểm"* là một phát biểu **đúng và dùng được**; *"không bật"* là một
phát biểu **không ai bác được, và vì thế không ai kiểm được**.

**Lý do giữ mục này ở mức 🔴 dù hồ sơ Đ.25 đã bỏ:** vế *"ô bắt buộc của hồ sơ"* **rụng theo quyết định
18/08**, nhưng vế còn lại **không**: hai công tắc ấy **định hạng sự cố lộ khoá 17/08**. Nếu OpenAI
đang lưu nội dung yêu cầu, phạm vi sự cố ấy rộng hơn hẳn thứ đã ghi. **Đó là một sự cố đã xảy ra,
không phải một nghĩa vụ giấy tờ** — nên nó sống sót qua việc bỏ hồ sơ.

---

## §5. Thẩm định 6 ca "TÊN hứa X, ASSERTION kiểm Y" — kết luận của tester ĐỨNG, và tôi thêm được một tầng

Việc vá thuộc tester. Việc của tôi là câu tester **không đọc được**: *phía sau cái cổng canh nhầm,
tính chất thật có đúng không?* Tôi đọc `src/` được; tester cố ý không. [ĐO] trên
`approve_resolution` (`main.py:857`):

**① Tính chất HITL hôm nay ĐÚNG.** Ghi phê duyệt (`resolution.status = "approved"`,
`approved_by = …`) nằm ở **sau toàn bộ** chuỗi guard — vai, phiên, trạng thái, OTP, hạn tươi,
dynamic-linking. Không có đường nào đi tới nó mà bỏ qua guard. **Không có sự cố. 6 ca này không phải
báo động đang cháy.**

**② Nhưng tiền đề của 5 ca test thì SAI ngay trên chính endpoint đó**, [ĐO] `main.py:932`:

```
        session.commit()            ← commit CÓ THẬT, TRƯỚC 5 lần raise 403 phía dưới
        if auth_session.locked_at is not None:
            raise HTTPException(status_code=403, …)
```

Và commit ấy **đúng** — nó ghi `failed_attempts` + `locked_at`; thiếu nó thì `get_session()` rollback
mọi exception và **khoá OTP không bao giờ xảy ra qua HTTP thật**. Chú thích tại chỗ nói rõ, có dẫn
ca đã sập một lần ở `/auth/otp/verify`.

⟹ Nhưng hệ quả cho bộ test là dứt khoát:

> **Trên đúng endpoint mà 5 ca HITL đang canh, `403` và "CSDL đã đổi" là hai điều ĐỒNG THỜI ĐÚNG —
> đo được, không phải giả thuyết.** Suy luận *"403 ⟹ không có gì xảy ra"* không chỉ thiếu chặt; nó
> **đã sai** ở đây. Sáu bản vá **không** phải bảo hiểm cho một rủi ro lý thuyết.

**③ Và không có cổng nào khác đỡ chỗ này.** `tests/test_invariants.py` introspect **route, vai,
CHECK constraint, tên tool** — không cái nào nhìn thấy **THỨ TỰ CÂU LỆNH TRONG THÂN HÀM**. Thứ giữ
cho tính chất ① đúng hôm nay là *dòng ghi nằm dưới dòng guard*, và **không cổng nào trong dự án canh
điều đó**. Một lần dọn dẹp chuyển khối ghi lên trên một guard sẽ giữ **cả 23 invariant xanh VÀ cả 6
ca test xanh**.

> ⭐ **HỘI TỤ ĐỘC LẬP với §5.D2 STATE (18/08, tech-lead + PO-agent).** D2 tìm ra: INV-00 ép
> `app.routes` khớp `authority-matrix.yaml`, **cả hai đều thiếu `/ready`** ⟹ khớp hoàn hảo ⟹ 23/23
> xanh, và **không cơ chế tự động nào bắt được "ADR đã duyệt mà chưa ai code"**. Tôi tới cùng hình
> dạng từ hướng khác: **không cơ chế tự động nào bắt được "guard đúng nhưng thứ tự câu lệnh sai"**.
>
> **Hai ca, một mệnh đề — và mệnh đề ấy rộng hơn cả hai:** cơ chế contract-first canh **thứ KHAI
> ĐƯỢC TRONG MỘT TỆP YAML** (route tồn tại, vai nào gọi, tên tool, CHECK). Nó **không canh được**
> thứ chỉ tồn tại trong **quan hệ giữa các câu lệnh** hoặc trong **khoảng cách giữa quyết định và
> thi hành**. Đây là **Luật G ở tầng cơ chế phòng thủ**, và hai ca độc lập trong một ngày đủ để nói
> đó là **một hạng mù, không phải hai lỗ thủng**. Hạng mù ấy chưa có chủ.

⟹ **Ủng hộ vá, ưu tiên 5 ca HITL trước, và lý do ưu tiên là ③ chứ không phải ②.** ② nói bộ test đang
đo sai; ③ nói **đây là cổng duy nhất có thể đo đúng**. Đề nghị tester ghi ③ vào ghi chú của bản vá,
để phiên sau không "tối ưu" 6 assertion ấy đi vì thấy chúng trùng với invariant.

*(Tôi không dán mã `src/` vào tài liệu này — tester đọc được `docs/`. Trên là hai trích dẫn tối thiểu
đủ neo kết luận vào vị trí kiểm lại được, không phải chuyển giao logic.)*

---

## §6. **LUẬT L và LUẬT M** — PO-agent cấp số hiệu 18/08

> **Một bộ dò dùng để CHE và dùng để ĐẾM cần hai ngưỡng ngược nhau. Dùng chung một bộ dò cho cả hai
> việc là nhập hai bài toán có hướng sai số trái dấu.**

- **CHE:** false positive rẻ (che nhầm mã đơn hàng), false negative đắt (lọt PII thật) ⟹ **nới rộng**.
  Playbook observability GĐ3 nói đúng điều này.
- **ĐẾM / BÁO CÁO:** false positive **đắt** — nó sinh ra một con số **đẩy người đọc vào chế độ khắc
  phục sự cố** cho một sự cố không có ⟹ **siết chặt**, và **báo cả hai số**.

**Bằng chứng hôm nay:** cùng một regex cho `447 dòng chứa SĐT` (lỏng) và `29 dòng, 4 giá trị, cả 4
thuộc bộ seed` (nghiêm). Con số thứ nhất **rời khỏi tay tôi thì thành một sự cố rò rỉ PII quy mô
lớn**; con số thứ hai là **hoạt động bình thường của hệ thống**.

Đây là **Luật B ở tầng dụng cụ** — cùng họ với ca `|| echo "vô dụng"` của tech-lead, nhưng đi theo
hướng ngược lại: chỗ kia công cụ **xoá** trạng thái thứ ba, chỗ này công cụ **bịa ra** trạng thái
đáng báo động nhất. Cả hai đều là một phép làm tròn được đóng cứng vào công cụ.

**Vế thi hành:** mọi con số đếm PII trong báo cáo phải kèm **định nghĩa bộ dò** và **cả hai phép đo**
khi chúng lệch nhau quá một bậc độ lớn.

### 🔴 LUẬT M — PO-agent cấp SỐ RIÊNG 18/08 (từ chối ghép làm vế hai của L, và họ đúng)

Tôi xin ghép cái này làm vế hai của L. **PO-agent từ chối, và lý do của họ đúng hơn đề nghị của tôi:**
**L nói về NGƯỠNG của bộ dò; M nói về KHI NÀO người ta chịu kiểm bộ dò.** Hai cơ chế khác nhau —
ghép lại thì loãng cả hai, và người sau trích một nửa sẽ mất nửa kia.

> **Tôi soi lại bộ dò khi nó cho câu trả lời tôi KHÔNG mong đợi (`447` — quá lớn), và không soi khi
> nó cho câu trả lời tôi MONG ĐỢI (`gAAAAA…` — đúng như ADR-025 hứa).**

§8 STATE dạy dấu hiệu là *"dữ liệu trông QUÁ GỌN"*. Ca này thêm một dấu hiệu **khó thấy hơn hẳn**:
***"kết quả KHỚP với thứ tài liệu nói"***. Khi phép đo xác nhận một điều đã được viết trong ADR, phản
xạ soi lại **không bật** — vì không có gì bất thường để giải thích. Đó chính là lúc một `LIMIT 3`
đi lọt.

> **LUẬT M — XÁC NHẬN KHÔNG PHẢI BẰNG CHỨNG. Xác nhận là lúc cảnh giác RẺ NHẤT, nên là lúc hay bị bỏ
> nhất.** §8 dạy dấu hiệu là *"dữ liệu trông QUÁ GỌN"*; M thêm dấu hiệu **khó thấy hơn**: *"kết quả
> KHỚP với thứ tài liệu đã hứa"* — lúc ấy **không có gì kích hoạt phản xạ soi lại**.

**Vế thi hành:** khi phép đo **xác nhận** điều tài liệu đã khẳng định, **đó là lúc bắt buộc hỏi mẫu
số** — không phải lúc nó mâu thuẫn.

**Bằng chứng đi kèm luật là CẶP ca của chính tôi, cùng ngày, hai kết cục ngược nhau:** `447` — soi vì
con số **không giống thứ tôi mong đợi** ⟹ **bắt được**; `LIMIT 3` — **không soi** vì kết quả **đúng
như ADR-025 đã hứa** ⟹ **trượt**. Khác nhau đúng ở chỗ kết quả **có làm người đọc ngạc nhiên hay không**.

*(§9.5 bổ sung ca thứ ba cùng ngày, và ba ca cùng lệch một hướng ⟹ Luật K.)*

---

## §7. Sổ nợ sau phiên này

**Xếp lại 18/08 sau hai quyết định của PO thật** (bỏ Đ.25 · trọng tâm chuyển sang **caching + token**).
Đóng 6 mục, mở 2 mục, đổi thứ tự phần còn lại.

### ⛔ ĐÃ ĐÓNG theo quyết định PO — không ai phải làm nữa

Ⓐ ngăn xếp `app.adaptivealgo.uk` · Ⓑ/Ⓒ/Ⓓ · hồ sơ Đ.25 · *"Ⓐ rơi khỏi bản đồ chặn"* ·
ràng buộc thứ tự §3.2 · cờ đóng băng (lớp ② tắt vĩnh viễn 18/08).

### 🔴 Còn sống — xếp theo thứ tự làm

| # | Việc | Ai | Vì sao thứ tự này |
|---|---|---|---|
| 1 | **Nhánh `except InvalidToken` phân biệt `gAAAAA` (§1.0b)** | tech-lead | **rẻ nhất, và là điều kiện tiên quyết của mọi mục dưới.** Chừng nào nó còn nuốt im lặng thì **không phép đo nào về mã hoá đáng tin**, kể cả phép đo nghiệm thu bản backfill |
| 2 | **Backfill 738 dòng `complaints.description_raw`** | tech-lead | vũng nước — tát một lần là hết. Nghiệm thu bằng mục 1, **không** bằng `LIMIT` |
| 3 | 🔴 **Vá `investigation_logs.tool_input_json`** — 5 tool / 93 dòng | PO quyết phạm vi → tech-lead | **vòi đang chảy.** Mục 2 không đóng được nó; vá xong mục 2 thì đây là bản plaintext **duy nhất còn lại** của lời khai (§1.5) |
| 4 | **A6** — 2 công tắc console, **ghi ngày kiểm** | PO thật | hồ sơ rụng nhưng **hạng sự cố lộ khoá 17/08 thì không** |
| 5 | Vá 6 ca TÊN≠ASSERTION, 5 ca HITL trước, kèm lý do §5③ | tester | đang chạy |
| 6 | ADR-025 QĐ 3 không nêu tên `tool_input_json` trong retention | PO/tech-lead | ghim trước khi ai viết job xoá |
| 7 | `access.log`: không xoay vòng · không toàn vẹn · không rời hộp (§2.4) | tech-lead | nợ chất lượng bằng chứng |
| 8 | Hạng mù *"contract-first không canh được quan hệ giữa câu lệnh / khoảng cách quyết định→thi hành"* (§5③ + STATE §5.D2) | chưa có chủ | hai ca độc lập trong một ngày |

> 🔴 **Mục 1 đứng trước mục 2 không phải vì rẻ hơn.** Nếu backfill chạy trước, phép nghiệm thu của
> nó (*"đọc lại thấy đúng nội dung"*) **đi qua đúng nhánh đang nói dối** — một dòng backfill hỏng sẽ
> đọc ra nguyên văn và **trông y hệt một dòng thành công**. **Sửa cái đèn trước khi soi.**

### 🆕 Việc MỚI theo trục caching/token — security nêu trước khi thiết kế bắt đầu

| | Việc | Vì sao nó là việc của security |
|---|---|---|
| 🔴 | **Khoá cache không được là hàm của chỉ văn bản khách** | Cache prompt/response keyed trên chữ khách ⟹ hai người gõ **cùng một câu** dùng chung một mục cache. Nếu câu trả lời đã được cá nhân hoá bằng kết quả tool (số dư, mã GD của người A) thì người B **nhận dữ liệu của người A** — rò rỉ chéo người dùng, **không có log nào tố cáo**. **Khoá phải gồm cả phạm vi chủ thể.** |
| 🟡 | `_bam_truy_van` (HMAC có khoá) là khuôn đúng cho **khoá cache**, đừng đúc hàm băm thứ hai | ADR-031 điều kiện ① đã lập luận rồi — băm trần trên câu tiếng Việt ngắn dò ngược được bằng từ điển |
| 🟡 | Cache **hit** phải vào được sổ token, không được biến mất | Nếu lượt hit ghi `0 token` **giống hệt** lượt lỗi ghi `0`, ta lặp lại đúng bẫy §8/⓶ trên một dụng cụ mới. **Ba rổ, không phải hai.** |

---

## §8. Điều tôi KHÔNG kết luận

- **Không** kết luận có rò rỉ dữ liệu cá nhân thật. Phép đo cho **1 chuỗi dạng SĐT không giải thích
  được** (17/08) và **0 chuỗi như vậy ngày 15/08** trong ngăn xếp `fin05` — **và mẫu số của phép đo
  ấy hẹp hơn mức cần thiết** (§3 đầu mục). *"Thật hay bịa"* thuộc người đã gõ.
- **Không** kết luận đồng hồ Đ.25 đã chạy hay chưa — **và không còn cần kết luận**, PO đã bỏ hồ sơ.
- **Không** coi *"PO bỏ hồ sơ Đ.25"* là *"738 dòng lời khai plaintext không còn là vấn đề"*. Hai
  việc khác nhau; ranh giới ấy do PO-agent vạch và tôi giữ nguyên.
- **Không** phán quyết nhà cung cấp nào an toàn hơn. Đ.25 áp **như nhau** cho mọi chuyển ra nước ngoài.
- **Không** đọc ToS mức hợp đồng, **không** đánh giá chế độ pháp lý nơi nhận — ngoài vùng có vật đo.
- **Không** giải mã bất kỳ cột nào, **không** in giá trị PII nào vào tài liệu này (SĐT ở §3.5 che 7/10
  chữ số; định danh dòng để tra lại là `log_id`, không phải nội dung).
- **Không** đề xuất bản vá kỹ thuật cho §1 — nêu ràng buộc (§1.5), thiết kế thuộc tech-lead.
- **Không** quyết ba câu ADR-031 thay PO thật.

---

## §9. Phân xử câu thẩm quyền `search_policy` (giao 18/08) — **KHÔNG phải lỗi thẩm quyền. Là một MIỄN TRỪ KHÔNG ĐƯỢC KHAI.**

### 9.1 🔴 Tiền đề của câu hỏi có hai chỗ sai — phải sửa trước khi trả lời

PO-agent chuyển câu hỏi kèm [ĐO]: *"4 tool mang `@_locked` + kiểm `otp_verified_at is None`
(813 · 862 · 904); `search_policy` (949) mang `@tool` trần."* Tôi đo lại
`src/agents/tools/customer_tools.py` — **hai vế đều không khớp:**

```
791 @tool 792 @_locked   lookup_transaction      813 kiểm otp   (OTP_VIEW_MAX_MINUTES)
842 @tool 843 @_locked   get_customer_history    862 kiểm otp   (OTP_VIEW_MAX_MINUTES)
875 @tool 876 @_locked   create_ticket           904 kiểm otp   (OTP_STEPUP_FRESH_MINUTES)
921 @tool 922 @_locked   request_human_handoff   —  KHÔNG kiểm
949 @tool 950 @_locked   search_policy           —  KHÔNG kiểm
```

**Sai ①: `search_policy` KHÔNG "mang `@tool` trần" — nó có `@_locked` như cả bốn tool kia. CẢ NĂM
đều có.**

**Sai ②: `@_locked` KHÔNG PHẢI CỔNG OTP.** [ĐO] thân hàm (dòng 735-790): nó làm đúng hai việc —
chặn lượt đã bị bỏ (`TurnAbandonedError`) và **bất biến chống livelock** mà tech-lead vừa land. Không
một dòng nào chạm `otp_verified_at`. Câu *"4 tool mang `@_locked` + kiểm OTP"* **gộp hai cơ chế không
liên quan** thành một, rồi đọc sự vắng mặt của cơ chế thứ hai như sự vắng mặt của cả hai.

*(Dấu hiệu đã nằm sẵn trong chính câu đó: "4 tool" nhưng chỉ kèm **BA** số dòng. Mẫu số và danh sách
lệch nhau ngay trong một câu — Luật F.)*

⟹ **Phát biểu đúng:** *"`search_policy` là một trong **HAI** tool không có cổng OTP."* Và tool kia là
`request_human_handoff`.

### 9.2 Sự bất đối xứng THẬT — và nó không nằm ở chỗ ai cũng nhìn

Hai tool cùng không có OTP, nhưng chỉ một trong hai **khai lý do**. [ĐO] docstring:

```
request_human_handoff  "KHÔNG cần OTP (đây là routing request, không …)"   ← MIỄN TRỪ CÓ KHAI
search_policy          (không một chữ nào về OTP)                          ← MIỄN TRỪ IM LẶNG
```

> **Đó mới là finding.** Không phải *"thiếu một cổng"* mà *"một miễn trừ không phân biệt được với một
> chỗ bỏ sót"*. Trên mã, hai thứ ấy **trông y hệt nhau** — cùng là sự vắng mặt của mấy dòng. Người
> đọc sáu tháng sau không có cách nào biết `search_policy` là **quyết định** hay **quên**, trong khi
> với `request_human_handoff` họ biết ngay.

Đây là **Luật H ở tầng mã nguồn**: `request_human_handoff` báo *triệu chứng có kèm chẩn đoán*;
`search_policy` để lại một khoảng trống **im lặng**, và im lặng thì không bác được.

### 9.3 Trả lời câu thẩm quyền: **KHÔNG vi phạm.** Tôi không nâng hạng.

Đối chiếu từng ràng buộc, không đối chiếu cảm giác:

| | |
|---|---|
| Ràng buộc cứng 2 (AI không vượt cấp) | ✅ tool gọi **dưới danh nghĩa `customer`**, không có đường escalate |
| Ràng buộc cứng 4 (OTP phiên) | ✅ OTP thiết kế để gác **truy cập dữ liệu KHÁCH**. `search_policy` đọc **tài liệu chính sách công khai** — không chạm dữ liệu khách nào |
| `contracts/authority-matrix.yaml` | ✅ không mục nào bị phá |
| ADR-005 (step-up cho hành động có hậu quả) | ✅ tra cứu tài liệu không phải hành động có hậu quả |

⟹ **Tôi xác nhận đánh giá của tech-lead: miễn trừ này nhiều khả năng CỐ Ý, và trên trục "truy cập dữ
liệu" nó ĐÚNG.** Tôi không kết luận là lỗi. Giữ nguyên hạng bằng chứng họ khai.

### 9.4 Nhưng có một TRỤC THỨ HAI không ai khai, và trên trục đó `search_policy` là tool duy nhất

Ràng buộc cứng 4 nói về **ai được đọc gì**. Nó không nói gì về **dữ liệu đi ra đâu**. [ĐO] đường đi
đầy đủ:

```
POST /agent/chat          require_role("customer")          ← KHÔNG kiểm OTP ở tầng route
  → model chọn tool
  → search_policy(query)                                    ← KHÔNG kiểm OTP ở tầng tool
  → search_policy_text(session, query)                      rag/search.py:48
  → store.search(query, k)                                  rag/store.py:248
  → _get_embeddings().embed_query(bo_dau(query))            rag/store.py:255  → OpenAI (Hoa Kỳ)
```

> 🔴 **`search_policy` là tool DUY NHẤT mà một khách CHƯA xác thực OTP làm cho văn bản mình gõ RỜI
> HẠ TẦNG.** Bốn tool kia đều dừng lại ở cổng OTP trước khi chạm bất cứ thứ gì. Chuỗi rời đi là
> `query` do agent soạn **từ lời khách** — đúng dòng §2 của hồ sơ kiểm kê Đ.25.

**Cách phát biểu đúng, và nó không phải một cáo buộc:** miễn trừ được cân trên trục *"tool này có đọc
dữ liệu khách không"* — **câu trả lời đúng là KHÔNG**. Nhưng `search_policy` là tool duy nhất mà trục
ấy **không phải trục có chi phí**. Trục có chi phí của nó là **đường ra**, và **chưa ai cân nó trên
trục đó**.

### 9.5 ⚠️ Một khung tôi ĐỊNH BÁO rồi tự bác bằng phép đo — ghi lại vì đây là lần thứ ba trong ngày

Phản xạ đầu của tôi: *"đường khuếch đại chi phí không cần OTP — mỗi tin nhắn một lời gọi embedding,
không giới hạn, và ngân sách chỉ còn ~32K token."* Nghe rất khớp với ưu tiên mới của PO. **Sai.** [ĐO]
`main.py:610`:

```
@limiter.limit("20/minute")          + RedisConcurrencyLimiter (_agent_turn_limiter)
```

⟹ **Có chặn, hai lớp.** Trần là **20 lượt/phút mỗi client**, không phải vô hạn. Con số đúng biến việc
này từ *"lỗ thủng ngân sách"* thành *"một cái đuôi chi phí nhỏ trên một miễn trừ chưa khai"* — **hạ
hai bậc**.

> **Ba lần trong một ngày, cùng một hình dạng, cùng một người:** `447` (bắt được vì con số quá lớn) ·
> `LIMIT 3` (**trượt** vì kết quả đúng như mong đợi) · lần này (bắt được vì tôi đi tìm sau khi đã
> trượt một lần). **Cả ba đều nghiêng về phía làm báo cáo NGHE MẠNH HƠN.** Thiên lệch cùng một hướng
> ở ba phép đo độc lập ⟹ **Luật K nói đây là thiên lệch CHUNG, đi tìm bộ lọc chung.**
> Bộ lọc chung, tôi khai thẳng: **tôi kiểm mẫu số kỹ hơn khi con số bất lợi cho hệ thống, và lỏng
> hơn khi nó có lợi cho báo cáo của tôi.** Đó là vế thứ hai của Luật L (§6) áp cho chính tôi.

### 9.6 Đề nghị — hai dòng chữ, không phải một cổng

**KHÔNG đề nghị thêm OTP cho `search_policy`.** Nó sẽ chặn đúng ca dùng hợp lệ (khách hỏi *"phí rút
tiền bao nhiêu"* trước khi đăng nhập sâu) để đổi lấy một rủi ro tôi vừa tự hạ hai bậc — **đánh đổi tồi**,
và nó là **phản xạ "thêm một cổng cho yên tâm"** mà Luật A gọi tên.

Đề nghị đúng, rẻ, và đúng vùng của tech-lead:

1. **Viết miễn trừ ra docstring `search_policy`, đúng khuôn `request_human_handoff` đã dùng** — nêu
   **cả hai trục**: *không chạm dữ liệu khách (nên miễn OTP)* **và** *có đường ra ngoài hạ tầng qua
   `embed_query` (nên đừng nới rate limit ở đây mà không nghĩ lại)*. Một miễn trừ có khai thì lần sau
   người ta **sửa được**; một miễn trừ im lặng thì người ta **xoá nhầm hoặc nới nhầm**.
2. **Ghi vào `contracts/agent-tools.yaml` trường khai *"tool này có đường ra ngoài hạ tầng không"*.**
   Hôm nay contract khai tên + lược đồ; **không khai đường ra.** Nếu có trường đó thì
   `search_policy` là tool **duy nhất** bật cờ, và câu hỏi hôm nay **đã tự hiện ra** thay vì phải có
   người đi tìm. *(Đụng contract ⟹ đủ §10, không đường tắt — nên đây là đề xuất cho PO, không phải
   việc làm ngay.)*

### 9.7 Việc ② (chốt chặn chi phí sai tầng, §5.F) — tôi không mở lại, chỉ thêm một dòng

Đã giao tech-lead cắm ở `_khoa_cho_nha_cung_cap()`. Đồng ý đó là **đúng tầng** — cùng chỗ
`so_luot_da_phat`, và là **cửa duy nhất** mọi đường ra tiền phải đi qua.

Một dòng cần thêm, và nó nối thẳng với §9.4: **đường `embed_query` phải đi qua đúng cái chốt ấy.**
Nó là đường ra tiền **không đi qua `graph.py`**, nên một bản vá chỉ cắm ở đường chat sẽ **để lọt đúng
đường mà §9.4 vừa chỉ ra là ít cổng nhất**. Nếu chốt cắm ở `_khoa_cho_nha_cung_cap()` thì nó phủ cả
hai (cùng hàm cấp khoá) — **nhưng phải kiểm bằng ca đối chứng trên đường embedding, không suy từ ca
đường chat.** Luật A vế hai.

---

## §10. Trục CACHING — rà soát bảo mật TRƯỚC khi thiết kế, vì sau khi land thì đắt

### 10.1 Hiện trạng, [ĐO] — **chưa có cache tầng ứng dụng nào**

`grep` toàn `src/` cho `cache|lru_cache|ttl`: mọi hit `lru_cache` đều là **`maxsize=1`** (nạp cấu
hình/model một lần), **không phải cache dữ liệu**. `_bam_truy_van` (`rag/search.py:33`) hiện **chỉ
dùng để ghi log** `query_hash` (dòng 116), chưa làm khoá cache của gì cả.

⟹ Ba điều kiện tôi gửi lần trước là **ràng buộc thiết kế phòng ngừa**, đúng thời điểm — chưa có gì
để vá, và vì thế chưa có gì phải tháo.

### 🔴 10.2 **RÚT TOÀN BỘ** — phát biểu của tôi sai 51 điểm phần trăm, và bản vá đã bị thử rồi

**Tôi đã viết:** *"tiền tố ~189 ký tự < 1024 token ⟹ **prompt cache hit 0%, mọi lượt, từ trước tới
nay**"*, rồi đề xuất dời `{current_time}` xuống cuối prompt như *"đòn bẩy lớn nhất, bản vá một dòng"*.

**Bắt bởi:** PO-agent. **Tôi kiểm lại độc lập cả hai nguồn của họ — cả hai đều đúng, số tôi trùng
khít số họ:**

```
[ĐO] /app/logs/usage.jsonl — trường `cached_input_tokens` NẰM SẴN Ở ĐÓ
  tổng dòng                        90
  đọc được CẢ input LẪN cached     54      (None: 9 · input=0: 27 — ba rổ, không gộp)
  tổng input_tokens           923.787
  tổng cached_input_tokens    468.864
  ⟹ TỈ LỆ CACHE THẬT            50,8%      ← không phải 0%
  dòng có cached > 0            50/54

[ĐO] scripts/BAN-GIAO-coder-2026-08-17.md:132-137, mục "Chỗ đã thử và THẤT BẠI — đừng thử lại"
  "Dời {current_time} xuống cuối prompt để cứu prefix cache — đo: cache 85,0% → 86,3%.
   ĐÃ REVERT. Lý lẽ tĩnh rất thuyết phục (current_time ở byte 208/15.094) nhưng phần lớn
   cache hit là TRONG CÙNG MỘT LƯỢT, không liên lượt."
```

⟹ **Bản vá tôi gọi là "đòn bẩy lớn nhất" đã được làm, đo được +1,3 điểm, và revert.** Nó nằm trong
một mục có tiêu đề đúng nghĩa đen là ***"đừng thử lại"***.

#### Cơ chế sinh lỗi — một SUY LUẬN đội lốt `[ĐO]`

Phép đo *"tiền tố 189 ký tự"* **là thật**. Bước ***"⟹ hit 0%"* thì không phải phép đo** — nó là suy
luận, và nó **thừa hưởng dấu `[ĐO]` của câu đứng trước**. Nó sai vì giả định **tiền tố cache-được chỉ
là system prompt**; thực tế trong một lượt ReAct nhiều lời gọi, **toàn bộ ngữ cảnh của lời gọi trước
trở thành tiền tố của lời gọi sau** — nên lời gọi 2..N có tiền tố khổng lồ. Đó chính xác là điều
người bàn giao đã đo và viết ra: *"phần lớn cache hit là TRONG CÙNG MỘT LƯỢT"*.

#### 🔴 Và chỗ nặng nhất: câu cấm làm đúng việc này nằm trong đoạn tôi đang TRÍCH

`graph.py:945-949` — đoạn tôi mở ra đọc và dẫn lại trong chính mục này — viết:

> *"`cached_tokens` là thứ **DUY NHẤT** nói prompt-cache có ăn hay không. Trước bản này không ai biết
> cache đang hit 0% hay 50%; **suy luận từ tài liệu không thay được số đo** — và suy luận đó **đã sai
> một lần**."*

**Tôi đọc câu đó, rồi làm đúng thứ nó cấm, trong cùng một mục.** Và trường số nó nói tới nằm trong
`usage.jsonl` — tệp tôi **đã liệt kê ra màn hình ở §2.4 của chính tài liệu này** khi đo `access.log`,
rồi không mở.

Cùng hình dạng với hai ca đã ghi hôm nay: đính chính ADR-031 (`grep` trúng 143, câu trả lời ở 150) ·
PO-agent (`head -40` cắt ở 949, câu trả lời ở 950). **Lần này khoảng cách không phải mấy dòng — câu
trả lời nằm trong cùng đoạn văn tôi đang trích dẫn.**

#### Ca thứ TƯ cùng một bộ lọc — và điều đáng ghi là bộ lọc VẪN CHẠY SAU KHI TÔI ĐẶT TÊN CHO NÓ

Ở §9.5, cách mục này **vài trăm dòng trong cùng một tệp**, tôi tự khai bộ lọc chung: *"tôi kiểm mẫu
số kỹ hơn khi con số bất lợi cho hệ thống, và lỏng hơn khi nó có lợi cho báo cáo của tôi."*
Rồi tôi viết §10.2 — *"đòn bẩy lớn nhất, bản vá một dòng"*, trên **đúng trục PO vừa ưu tiên** — và
**không kiểm gì cả.**

> 🔴 **Đây mới là bài học, không phải con số 50,8%: KHAI RA MỘT THIÊN LỆCH KHÔNG VÔ HIỆU HOÁ NÓ.**
> Tôi đã đặt tên nó, viết nó ra, gửi nó cho PO-agent — và nó vẫn chạy nguyên vẹn ở phép đo kế tiếp.
> Một thiên lệch được nêu tên vẫn là một thiên lệch; thứ duy nhất chặn được nó là **một phép kiểm
> MÁY MÓC bắn bất kể kết quả nghe thế nào**, không phải một quyết tâm cẩn thận hơn.

**Vế thi hành tôi đề nghị — một câu hỏi cơ học, không phải một đức tính:**

> **Trước khi phát biểu về một đại lượng, hỏi: *"sổ nào của ta có TRƯỜNG ĐO THẲNG đại lượng này?"* —
> và mở nó ra TRƯỚC khi lập luận.** Nếu có trường đó thì mọi lý lẽ tĩnh đều là **giả thuyết**, không
> phải kết quả.

Ở ca này câu hỏi ấy mất **một dòng lệnh** và trả về ngay `cached_input_tokens`. Nó không đòi tôi cẩn
thận hơn, không đòi tôi nghi ngờ động cơ của mình — nó chỉ đòi tôi **hỏi trước khi suy**. Xin PO-agent
xem đây là **vế thi hành của Luật M**, không phải một luật mới.

#### Ba số cho cùng một vật — khai, không hoà

```
graph.py:949                      233 / 16.082
BAN-GIAO-coder-2026-08-17.md:135  208 / 15.094
tôi đo 18/08 trong container      189 / 15.094
```

Mẫu số **15.094 khớp ở hai trong ba** ⟹ `16.082` của `graph.py:949` **nhiều khả năng đã cũ**. Tử số
lệch ba chiều (189/208/233) — có thể do đếm từ mốc khác nhau (`{current_date}` vs `{current_time}` vs
chuỗi năm). **Chưa truy nguyên, và không cần truy** — vì §10.2 đã rút, **không quyết định nào còn
treo trên ba con số này.** Ghi lại để người sau đừng trích một trong ba như thể nó là con số.

### 10.3 🔴 Phần bảo mật: **ranh giới tiền tố cache LÀ một ranh giới phân loại dữ liệu**

Đây là câu chưa ai phát biểu, và nó phải được phát biểu **trước** khi ai đó đi tăng tỉ lệ hit:

```
TRÊN ranh giới (tiền tố ổn định)   →  nhà cung cấp GIỮ LẠI và TÁI DÙNG qua nhiều request
DƯỚI ranh giới                     →  mỗi request một lần
```

**Tin tốt, và tôi cấp phép rõ ràng cho nó:** [ĐO] tiền tố hôm nay chứa **hằng số thuần** —
`build_system_prompt` đóng cứng `customer_name="quý khách"` (`prompt.py:79`, ADR-010 đã gỡ tên khách
từ 13/08). ⟹ **Bật prompt cache là TRUNG TÍNH về bảo mật.** Phần được cache đúng là phần **không
chứa dữ liệu khách nào**. Không cần hỏi thêm ai, không cần hồ sơ gì.

🔴 **Và cái bẫy nằm ở BƯỚC SAU — mục này KHÔNG rụng theo §10.2, nó còn quan trọng HƠN.** Cache thật
đang **50,8%** (§10.2) nghĩa là prompt cache **đang ăn thật**, không phải một cơ chế lý thuyết ⟹ áp
lực đẩy tỉ lệ ấy lên cao hơn là áp lực **có thật và đang diễn ra**. Khi ai đó muốn đẩy hit rate cao hơn, phản xạ tiếp theo là **đưa THÊM thứ lên tiền tố** — lịch sử hội thoại, hồ sơ khách,
kết quả tool của lượt trước. **Đúng khoảnh khắc ấy, tiền tố thôi là hằng số và bắt đầu là dữ liệu
khách được nhà cung cấp giữ lại.** Và:

- **không cổng nào canh** — `test_invariants` không nhìn thấy *thứ tự các đoạn trong một chuỗi prompt*;
- **không diff nào của ta thấy** — đây đúng hạng mù §5.D2 + §5③, lần thứ ba;
- **triệu chứng là một con số ĐI ĐÚNG HƯỚNG TA MUỐN** (hit rate tăng) ⟹ **không ai đi kiểm** — đúng
  Luật M.

**Ràng buộc đề nghị, một câu, ghim vào cạnh `build_system_prompt`:**

> **Mọi thứ nằm trên ranh giới cache phải là HẰNG SỐ BIÊN DỊCH. Đưa bất cứ giá trị nào phái sinh từ
> khách lên tiền tố là một quyết định phân loại dữ liệu, không phải một tinh chỉnh hiệu năng.**

### 10.4 🔴 Ràng buộc cứng 3 đảm bảo TRUY VẾT, **không** đảm bảo TƯƠI — cache khai thác đúng khoảng hở

Ràng buộc cứng 3: mọi số agent nhắc tới phải **truy vết được** tới một `tool_result` có thật. Đọc kỹ:
nó đòi **tồn tại**, không đòi **tươi**. Một kết quả cache **là** một `tool_result` có thật ⟹ nó **thoả
ràng buộc cứng 3 một cách hình thức** trong khi nói với khách một trạng thái đã cũ.

Ca cụ thể: `lookup_transaction` được cache 5 phút · giao dịch chuyển `pending → completed` · agent
trả lời `pending` · con số **truy vết được tới một dòng có thật** ⟹ **mọi cổng đều xanh.**

**Dự án đã có tiền lệ lý luận đúng chiều này** và tôi trích để đề nghị không đi ngược nó —
`services/complaint_intake.py:52`:

> *"nạp lại mỗi lần gọi là đủ nhanh — **không cần cache, tránh rủi ro đọc dữ liệu cũ** sau khi có
> ticket/complaint mới."*

⟹ **Đề nghị phân loại tool theo tính CACHE-ĐƯỢC, và nó không trùng phân loại theo OTP:**

| tool | cache được? | vì sao |
|---|---|---|
| `search_policy` | ✅ **có** | tài liệu chính sách, đổi theo tuần. **Đây là tool duy nhất caching có nghĩa** — và cũng là tool tốn embedding |
| `lookup_transaction` | 🔴 **không** | trạng thái giao dịch là thứ khách đang khiếu nại; cũ = sai |
| `get_customer_history` | 🔴 **không** | cùng lý do |
| `create_ticket` · `request_human_handoff` | — | tool GHI, không có nghĩa gì để cache |

**Và `search_policy` cache được thì phải vô hiệu hoá theo kho RAG**, không theo đồng hồ: ADR-026 buộc
kho chỉ phục vụ tài liệu **đã duyệt**, nên một tài liệu vừa được `supervisor` duyệt mà cache còn giữ
câu trả lời cũ thì **ADR-026 bị vô hiệu bởi một lớp cache** — cùng hình dạng với §1.5 (cơ chế chạy
đúng, vẫn bị đi vòng).

### 10.5 Tổng hợp — bốn ràng buộc cho tech-lead, xếp theo lúc cần

| khi nào | ràng buộc |
|---|---|
| ~~trước khi dời `current_time`~~ | ⛔ **RÚT — xem §10.2.** Bản vá đã thử, +1,3 điểm, đã revert. Cache thật đang **50,8%**, không phải 0% |
| **ngay khi** bản vá đó land | ghim câu §10.3 cạnh `build_system_prompt` — **trước** khi có người đi tăng hit rate |
| **trước** khi cache bất cứ kết quả tool nào | khoá cache **phải gồm phạm vi chủ thể**; chỉ `search_policy` được cache (§10.4) |
| **cùng lúc** cắm `so_luot_da_phat` | ba rổ `hit` · `miss` · `hỏng`, **ba mẫu số riêng** — `hit` ghi `0 token` mà lẫn với `hỏng` ghi `0` là lặp lại bẫy §8/⓶ trên dụng cụ mới |

### 10.6 Điều tôi KHÔNG kết luận ở mục này

- 🔴 **Không** kết luận prompt cache của DashScope có tính vào **TPM** hay không — đó là **câu ③ phiếu
  Alibaba (§5.A3)**, thuộc nhà cung cấp, **không đo được từ đây**. **Mục này SỐNG SÓT qua việc rút
  §10.2, và giờ nó nặng hơn:** ta vừa biết cache **đang ăn 50,8%** ⟹ câu *"50,8% ấy có được miễn khỏi
  TPM không"* là một câu **có tiền đề đã xác nhận**, không còn là giả thuyết. Nếu **có** miễn thì trần
  TPM hiệu dụng cao hơn ta tưởng; nếu **không** thì mọi tối ưu cache **không chạm được trần đang
  chặn buổi 150 người**. Hai thế giới rất khác nhau, và ta chưa biết đang ở cái nào.
- **Không** đề xuất kiến trúc cache. Tôi nêu ràng buộc; thiết kế thuộc tech-lead.
- **Không** đo bằng lượt LLM thật — ngân sách A3 còn hiệu lực, **0 lượt tốn tiền** cả phiên. Con số
  50,8% đọc từ **sổ đã có sẵn**, không phát sinh lời gọi nào.

---

## §11. ĐỊNH HẠNG kho checkpoint LangGraph (giao 18/08) — và câu hỏi được giao là câu hỏi về PHẦN NHỎ NHẤT

> **Áp vế thi hành Luật M ngay từ dòng đầu:** trước khi lập luận, tôi hỏi *"sổ nào đo thẳng thứ này?"*
> Câu trả lời: **chính bảng ấy** — `channel`, `type`, và nội dung `blob` đều tra được bằng `psql`.
> Toàn bộ §11 là số đọc ra, **0 lượt LLM, 0 byte nội dung được in**.

### 11.1 Trả lời thẳng câu được giao: **mã giao dịch trần = mức THẤP**

`2.179` (tôi đo `1.944` trên riêng `channel='messages'`) dòng chứa `TXN2026…`. Đối chiếu ADR-025 §2:
số tiền · mã GD · thời điểm · trạng thái đã được phân loại là **"rời, CÓ CHỦ ĐÍCH"** — agent cần chúng
để suy luận và trích dẫn, đó là **điều kiện của ràng buộc cứng 3**. Một mã GD nằm plaintext trong một
bảng nội bộ **không thêm rủi ro nào** so với thứ đã được quyết định cho rời hạ tầng mỗi lượt.

**Nếu chỉ có mã GD, tôi sẽ xếp 🟢 và đóng lại.**

### 11.2 🔴 Nhưng phép dò dừng ở mã GD và SĐT. Tôi hỏi *"cái gì đã KHÔNG sinh ra dòng nào ở đây"*

[ĐO] `checkpoint_blobs`, `channel='messages'` — **3.597 dòng, 105 MB, `bytea`, 0 mã hoá**:

```
chứa "HumanMessage"     3.597 / 3.597   ← TIN NHẮN KHÁCH, mọi dòng
chứa tiếng Việt UTF-8   3.413 / 3.597   (byte e1ba/e1bb — phép dò cũ MÙ với nó, xem 11.3)
chứa "AIMessage"        3.220
chứa "ToolMessage"      2.735
chứa "TXN2026"          1.944
SĐT (phép NGHIÊM)           9
```

> **Kho checkpoint không chứa "một ít mã giao dịch". Nó chứa TOÀN BỘ BẢN GHI HỘI THOẠI**, gồm **văn
> bản khách tự gõ**, chưa mã hoá, 105 MB.

### 11.3 Vì sao phép dò trước không thấy — và đây là một cái bẫy sẽ tái diễn

Phép dò của tôi lúc đầu cũng **mù y hệt**: tôi test `encode(blob,'escape') ~ '[àáảãạăâđêôơư]'` và được
**0/3.597** — rồi suýt đọc thành *"không có văn bản tiếng Việt"*. **Sai.** `encode(…,'escape')` biến
mọi byte ngoài ASCII thành escape bát phân `\303\251`, nên **mọi ký tự tiếng Việt biến mất khỏi phép
so khớp** trong khi `TXN2026` (thuần ASCII) thì hiện ra bình thường.

> 🔴 **Một bộ dò PII chạy trên `bytea` mà so khớp bằng chuỗi sẽ thấy ĐÚNG phần ASCII và MÙ ĐÚNG phần
> tiếng Việt** — tức mù đúng phần chứa lời khai khách, và thấy đúng phần vô hại nhất.
> Kết quả nó trả về **không phải "ít PII"**, mà là **"chỉ những PII viết bằng chữ không dấu"**.
> Đây là **Luật L ở một mặt phẳng mới**: không phải ngưỡng lỏng/chặt, mà **bộ dò mù với chính bảng mã
> của dữ liệu nhạy cảm nhất**. Phép sửa: dò trên **byte thật** (`position(…::bytea in blob)`), không
> dò trên biểu diễn đã escape.

### 11.4 Một MITIGATION có thật, tôi đo chứ không giả định

`ToolMessage` (2.735 dòng) **đã được che**: `_scrub_pii_cho_llm` (`customer_tools.py:495`) che
`full_name` · `phone` · `account_no` **trước khi** kết quả tool vào hội thoại LLM — nên thứ đọng lại
trong checkpoint là **bản đã che**. Đó chính là lý do SĐT tài khoản hạt giống ra **0/6.213** và phép
NGHIÊM chỉ ra **9**. **Con số thấp ấy là BẰNG CHỨNG CƠ CHẾ CHE ĐANG CHẠY, không phải bằng chứng kho
sạch.** Ghi rõ để không ai trích `0/6.213` như một lời trấn an.

🔴 **Nhưng `HumanMessage` KHÔNG được che — và đó là CỐ Ý, đúng thiết kế.** ADR-025 Quyết định 1 bác
che-lúc-ghi cho Nhóm A: *sửa chữ trong lời khai thì bản ghi mất giá trị chứng cứ*. Quyết định ấy đúng.
**Nó chỉ giả định lời khai được bảo vệ bằng MÃ HOÁ thay vì bằng che** — và ở kho checkpoint, **không
có vế thứ hai.**

### 11.5 🔴 Hệ quả nặng nhất: nó làm dấu ✅ CỦA CHÍNH TÔI thành gây hiểu nhầm

Bảng §1.1 của tôi ghi `messages.content` **467 / 0 · ✅ sạch**. **Con số vẫn đúng.** Nhưng kết luận
người đọc rút ra từ nó — *"nội dung hội thoại được mã hoá at-rest"* — **là sai**, vì cùng nội dung ấy
nằm ở `checkpoint_blobs`, 3.597 dòng, không mã hoá.

⟹ Đây **không phải** finding ① lặp lại ở bảng khác. Nó là finding ① **áp lên đúng cột duy nhất tôi đã
chứng nhận là sạch 100%**:

| | cột được chỉ định | bản sao plaintext |
|---|---|---|
| lời khai (`description_raw`) | 23/761 mã hoá — nợ migrate (ADR-032) | `investigation_logs` 27 dòng |
| **hội thoại (`messages.content`)** | **467/467 mã hoá — HOÀN HẢO** | **`checkpoint_blobs` 3.597 dòng · 105 MB** |

**Đúng như PO-agent phân biệt: đây là MỞ RỘNG PHẠM VI, không phải đính chính** — mẫu số của tôi
(*"bốn cột khai `Encrypted*`"*) được khai đúng, và trong mẫu số ấy kết luận *"hệ thống mã hoá không
hỏng"* vẫn đứng. **Nhưng bài học thì thuộc về tôi:** một bảng khai đúng mẫu số vẫn **dẫn sai** nếu
mẫu số ấy không phải mẫu số người đọc quan tâm. Người đọc không hỏi *"cột khai `Encrypted*` có sạch
không"* — họ hỏi ***"lời khai khách có được bảo vệ không"***. Tôi trả lời câu thứ nhất và **để họ
tưởng đã có câu thứ hai**.

### 11.6 Hai dữ kiện quyết định HẠNG — và chúng kéo ngược chiều nhau

> 📌 **NIÊM 18/08 ~09:30 (Luật P) — lập luận KÉO XUỐNG dưới đây vừa MẤT MỘT CHÂN. Thân giữ nguyên.**
> Nó dựa một phần vào *"(trước backfill) 738 dòng `complaints` plaintext"*. **Backfill đã chạy** ⟹
> `complaints` sạch 100% ⟹ `checkpoint_blobs` + `investigation_logs` nay là **bản plaintext DUY NHẤT
> còn lại của lời khai khách**.
> **Hạng GIỮ NGUYÊN mức CAO, nhưng LÝ DO đổi:** trước là *"một căn phòng lớn hơn sau cùng một cửa"*;
> nay là ***"căn phòng DUY NHẤT còn lại sau cửa ấy"***. Đây đúng là điều §1.5 dự đoán — nay **không
> còn là dự đoán**.

**Kéo XUỐNG — không tạo kẻ tấn công mới.** Cùng CSDL, cùng biên tin cậy. Ai đọc được
`checkpoint_blobs` thì cũng đọc được `investigation_logs` và (trước backfill) 738 dòng `complaints`
plaintext. **Đây KHÔNG phải một cửa mới** — nó là **cùng một cửa, mở ra một căn phòng lớn hơn nhiều.**

**Kéo LÊN — [ĐO], và đây là phần quyết định:**

```
khoá ngoại trên mọi bảng checkpoint*          0
cơ chế prune/TTL/delete trong src/            0   (grep delete|prune|clean|ttl → không hit nào)
thread_id                                     "USR-0145:1786630536"   ← CHỨA user_id
khoảng thời gian                              13/08 → 17/08  ·  370 thread  ·  ~21 MB/ngày
```

Ghép ba dòng ấy lại thành một câu, và nó là câu nặng nhất mục này:

> **Không khoá ngoại ⟹ một job retention đi theo CÂY KHOÁ NGOẠI sẽ KHÔNG BAO GIỜ chạm tới nó.
> Nhưng `thread_id` chứa `user_id` ⟹ nó LÀ dữ liệu cá nhân gắn được với một con người.**
> **Không tra ra được, nhưng quy trách nhiệm được** — kết hợp tệ nhất có thể có.

Và ADR-025 QĐ 3 (*xoá dòng thật sau 5 năm*) liệt kê phạm vi theo **danh sách cột** —
`checkpoint_blobs` **không có trong danh sách, cũng không có khoá ngoại để lộ ra khi job chạy**. Khác
`investigation_logs`: ở đó `NO ACTION` ít nhất làm job **báo lỗi**. Ở đây **job chạy xong, báo thành
công, và bản ghi hội thoại vẫn nguyên.** Không cổng nào kêu.

**Về ca "đảo dấu" PO-agent nêu — tôi xác nhận và làm nó sắc hơn:** đúng, `checkpoint_blobs` không bị
ảnh hưởng khi xoay `FIELD_ENCRYPTION_KEY`. Cách phát biểu đúng không phải *"xoay khoá an toàn hơn ta
tưởng"* mà: **xoay khoá không bảo vệ gì ở đây, vì ở đây chưa từng có gì được bảo vệ.** Cảnh báo
STATE §1 và §1.0b của tôi nói về **rủi ro HỎNG dữ liệu**; mục này nói về **vùng dữ liệu mà khoá chưa
bao giờ với tới**. Hai câu khác nhau, và câu thứ hai chưa ai viết.

### 11.7 ⟹ ĐỊNH HẠNG

> ## 🔴 Finding riêng · mức CAO · hạng **"HỆ SỐ NHÂN BÁN KÍNH"**, không phải **"cửa mới"**

**Cách đọc hạng này, và tôi cố ý chọn một hạng không phải hạng cao nhất:**

- **KHÔNG** phải P0 gấp: không có kẻ tấn công mới, không có đường ra ngoài hạ tầng, không vi phạm
  ràng buộc cứng nào. Tôi **không** nâng nó lên mức sự cố.
- **CÓ** là mức cao vì **ba tính chất cộng lại**, không vì kích thước: ① **8,4× mẫu số** ADR-032 và
  **39×** finding ① · ② **vô hình với job retention** (0 FK) trong khi **quy trách nhiệm được**
  (`user_id` trong `thread_id`) · ③ **không cơ chế dọn nào tồn tại**, ~21 MB/ngày, không trần.
- **Chi phí của việc KHÔNG làm, phát biểu chính xác:** ngày ADR-032 backfill xong, sẽ có người viết
  *"lời khai khách đã được mã hoá at-rest"*. **Câu đó sẽ SAI chừng nào kho checkpoint còn như hôm
  nay** — và nó sẽ sai theo kiểu **nghe rất đúng**, đi vào hồ sơ, rồi không ai kiểm lại. Đúng hình
  dạng Luật G ở tầng hồ sơ mà tôi đã mô tả ở §1.6, lần này với bán kính lớn nhất trong ngày.

**Xếp thứ tự so với việc đang có:** **SAU** bản vá nhánh giải mã và backfill ADR-032 (rẻ, đóng một
khoảng trống **đã được khai**), **TRƯỚC** phần còn lại. Không phải vì nó nhỏ hơn — vì nó **đắt hơn và
ta không sở hữu lược đồ**, nên nó cần một quyết định chứ không cần một script.

### 11.8 Ràng buộc cho ADR mới — nêu ràng buộc, KHÔNG thiết kế

Tôi đồng ý phạm vi PO-agent đã chốt (**ADR riêng, không mở rộng ADR-032**) và ba lý do của họ đều
đứng. Bốn ràng buộc từ phía bảo mật:

1. 🔴 **Bảo vệ ở tầng SERDE, không đổi kiểu cột.** `PostgresSaver` sở hữu lược đồ; đổi cột là đánh
   nhau với thư viện mỗi lần nâng phiên bản. Đây là ràng buộc **hình dạng**, giống ràng buộc tôi nêu
   cho `tool_input_json` (§1.8): **đừng phản xạ đổi kiểu cột.**
2. **Đừng che `HumanMessage`.** Cùng lý lẽ ADR-025 QĐ 1: đây là lời khai, che-lúc-ghi làm mất giá trị
   chứng cứ. **Mã hoá, không che.** Bản vá nào đi theo hướng scrub là đi ngược một quyết định đã ký.
3. 🔴 **Phải giải quyết RETENTION cùng lúc, không để lần sau.** 0 FK nghĩa là mục này **sẽ không tự
   lộ ra** khi ai đó viết job xoá. Nếu ADR chỉ nói *"mã hoá kho checkpoint"* mà không nói *"và xoá nó
   theo cùng lịch với hồ sơ khiếu nại"*, ta đổi **một kho plaintext vĩnh viễn** lấy **một kho đã mã
   hoá vĩnh viễn** — tốt hơn, nhưng vẫn phá nguyên tắc giới hạn lưu trữ.
4. **Nghiệm thu phải dò trên BYTE, không dò trên chuỗi đã escape** (§11.3) — nếu không, cổng nghiệm
   thu sẽ báo xanh đúng theo cách nó đã mù hôm nay.

### 11.9 Điều tôi KHÔNG kết luận

- **Không** in một byte nội dung nào. Mọi số ở trên là `count(*)` và `position()`; tôi **không** giải
  mã, **không** trích, **không** xem bất kỳ tin nhắn nào.
- **Không** kết luận có PII của **người thứ ba** trong kho checkpoint. Nó **rất có thể có** (cùng văn
  bản khách đã bàn ở §2 hồ sơ kiểm kê) nhưng tôi **chưa đo**, và đo được thì phải chạy NER — **chưa
  chạy**, đúng như đã khai ở §3.4.
- **Không** kết luận về ngăn xếp khác. Số này là của `fin05`; `fin05ttl`/`fin05do` chưa đo.
- **Không** thiết kế bản vá. Bốn ràng buộc ở 11.8 là ràng buộc, không phải giải pháp.

---

## §12. H3 — vô hiệu hoá cache theo kho RAG. **Câu trả lời: H3 CHƯA LÀM ĐƯỢC, và lý do lớn hơn H3.**

> **Áp vế thi hành Luật M từ dòng đầu**, đúng như đã hứa: trước khi lập luận, đi tìm **sổ nào đo thẳng
> *"kho RAG đổi lúc nào"***. Toàn mục là `psql` **chỉ-đọc** + đọc tệp repo — **0 `docker exec`**, vì
> cửa sổ dựng ảnh đang mở. *(Phép đo metadata collection Chroma cần vào container ⟹ **cố ý bỏ**, ghi
> ở §12.5 là khoảng trống đã biết, không phải khoảng trống bị quên.)*

### 12.1 Mở sổ trước: **không sổ nào đo thẳng "kho đổi lúc nào"**

| ứng viên | đo được gì | mù với |
|---|---|---|
| `policy_documents.uploaded_at` | lúc **nạp** | xoá · đổi trạng thái |
| `policy_chunks.created_at` | lúc **chunk sinh ra** | **xoá** (max không giảm) · đổi trạng thái |
| `count(policy_chunks)` | thêm **và** xoá | đổi trạng thái |
| metadata Chroma `chuan_hoa` | **phiên bản ĐỊNH DẠNG** (hằng số tay `= 2`, `store.py:138`) | **mọi** thay đổi nội dung |

🔴 **`CHUAN_HOA_VERSION` là cái bẫy đáng gọi tên**: nó *tên là version*, nó *nằm trên collection*, nó
*trông đúng như một khoá vô hiệu hoá cache*. Nó **không phải**. Nó theo dõi **cách biến text**
(bỏ dấu hay không) + **model nhúng** — hai thứ đổi khi **ta đổi mã**, không đổi khi **kho đổi nội
dung**. Dùng nó làm khoá cache là dựng *"hai định nghĩa của cùng một vật"* — đúng lớp lỗi ADR-031
điều kiện ① đã cấm.

⟹ **Không ứng viên nào phủ đủ bốn sự kiện** {thêm · xoá · duyệt · gỡ duyệt}. Ghép
`(count, max(created_at))` phủ được **thêm + xoá**. Hai sự kiện còn lại thì —

### 12.2 🔴 …hai sự kiện còn lại **KHÔNG TỒN TẠI**. ADR-026 chưa được thi hành.

[ĐO], bốn nguồn độc lập cùng chiều:

```
models.py:543   CheckConstraint("status IN ('processing','indexed','failed')")   ← KHÔNG có 'approved'
lược đồ         cột approved_at / approved_by  →  CHỈ có trên `resolutions`; tài liệu KHÔNG có
main.py:1223·1249·1273   cả BA route /policy-docs  →  require_role("partner_admin")
                         KHÔNG một route nào cho `supervisor`
dữ liệu         2 tài liệu, cả hai status='indexed'
```

**ADR-026 — "Đang hiệu lực", PO thật chốt 16/08 — quyết đúng một việc: tách *ai được nạp* (phân
quyền, đã có) khỏi *cái gì trở thành chính sách* (duyệt, mới). [ĐO] cho thấy vế thứ hai KHÔNG TỒN TẠI
Ở ĐÂU.** Tài liệu đi thẳng `processing → indexed` rồi được phục vụ.

⟹ **H3 như đặt ra là PREMATURE.** Không thể dựng *"vô hiệu hoá cache theo sự kiện duyệt"* khi **sự
kiện duyệt không có biểu diễn nào trong hệ thống**. Dựng nó sẽ cho ra một cơ chế **trông như đang thi
hành ADR-026 và thi hành số không** — đúng hình dạng §1.6, lần này ta sẽ **tự tay dựng** thay vì thừa
hưởng.

### 12.3 Ca thứ BA cùng lớp — và là ca nặng nhất trong ba

| ca | ADR | trạng thái | có KHAI là chưa code không? |
|---|---|---|---|
| `/ready` (STATE §5.D2) | ADR-028 | duyệt 17/08, chưa code | ❌ không |
| `assigned_to` | ADR-025 QĐ2 | duyệt 15/08, chưa code | ✅ **có** — ADR tự khai *"TÍNH NĂNG NGHIỆP VỤ MỚI"* |
| **duyệt tài liệu** | **ADR-026** | **duyệt 16/08, chưa code** | ❌ **không** |

**ADR-026 nặng nhất trong ba, và không phải vì kích thước:** hai ca kia là **tính năng chưa tới**.
ADR-026 được viết **ĐỂ ĐÓNG MỘT SỰ CỐ CÓ THẬT** — `08:23:14Z → 08:42:47Z` ngày 16/08, **19 phút 33
giây**, hai tệp nội bộ nằm trong kho **đang phục vụ**. **Khoảng trống sinh ra sự cố ấy vẫn đang mở**,
và cơ chế được chốt để đóng nó chưa tồn tại.

Và ADR-026 tự viết ra **chính xác vì sao khoảng trống này khó thấy** — câu của người vận hành:
*"đối tác ví có luồng upload riêng là đã quản lý được phần này rồi đúng không?"* ⟹ **một vai riêng cho
việc nạp TRÔNG y hệt một cơ chế quản trị nội dung.** Hôm nay `require_role("partner_admin")` trên cả
ba route vẫn đang tạo đúng ấn tượng đó.

### 12.4 🔴 Vì sao contract-first không bắt được — cùng cơ chế §5.D2, và lần này nó chạm CHECK constraint

`CheckConstraint` **là** một trong bốn thứ `tests/test_invariants.py` introspect (CLAUDE.md §3:
*"đọc `CheckConstraint` qua AST"*). Nó đọc `('processing','indexed','failed')`, so với `contracts/` —
**`contracts/` cũng không có `approved`** ⟹ **khớp hoàn hảo ⟹ 23/23 xanh.**

> Cơ chế đang làm **đúng việc của NÓ** (bắt code lệch contract). Nó **không** làm việc ta giả định
> (bắt **quyết định chưa được thi hành**). **Luật G ở tầng cơ chế phòng thủ — ca thứ ba trong ngày.**

⟹ **Cổng do §5.D2 đề xuất** (*"mọi ADR Đang-hiệu-lực có mục Hệ quả nêu file/cột thì thứ đó phải tồn
tại"*) **sẽ bắt được ca này.** Và tôi đề nghị dùng **ADR-026 làm ca biện minh cho việc xây cổng ấy**,
không phải `/ready`: `/ready` là một endpoint thiếu; **ADR-026 là một sự cố đã xảy ra mà bản vá được
ký rồi không được thi hành.** Cổng nào cũng cần một ca chứng minh nó đáng xây (Luật A vế hai) — đây
là ca đó.

### 12.5 Trả lời H3 cho ĐÚNG phần trả lời được

Bỏ vế "duyệt" (chưa tồn tại), phần còn lại của H3 **vẫn có câu trả lời** và tôi để lại ràng buộc:

1. **Khoá vô hiệu hoá phải là hàm của NỘI DUNG KHO, không của phiên bản MÃ.** Ứng viên đo được hôm
   nay: `(count(policy_chunks), max(policy_chunks.created_at), count(policy_documents))`. Phủ
   **thêm + xoá**. 🔴 **CẤM dùng `CHUAN_HOA_VERSION`** (§12.1).
2. **Khi cột `approved` tồn tại, khoá phải gồm nó** — nếu không, cache sẽ **giữ nguyên câu trả lời
   sinh từ tài liệu chưa duyệt** sau khi `supervisor` gỡ duyệt, và **ADR-026 bị vô hiệu bởi một lớp
   cache** đúng như tôi cảnh báo ở §10.4. **Ghi ràng buộc này vào ADR-026 NGAY BÂY GIỜ**, trước khi
   ai code phần duyệt — rẻ hơn nhiều so với phát hiện sau.
3. **Nghiệm thu phải có CA ĐỐI CHỨNG** (Luật A vế hai): nạp/xoá một tài liệu → **cùng một câu hỏi phải
   ra kết quả KHÁC**. Không có ca ấy thì ta chỉ chứng minh được cache **im**, không chứng minh được nó
   **kêu** đúng lúc.

**Khoảng trống đã biết, khai để không ai tưởng tôi đã phủ:** tôi **chưa đo** metadata thật của
collection Chroma (`chuan_hoa`/`model_embed` đang mang giá trị gì trên ảnh mới `d5b73a04d6ef`) — phép
ấy cần `docker exec`, và **cửa sổ dựng ảnh đang mở**. Việc còn lại, không chặn kết luận nào ở trên.

### 12.6 Điều tôi KHÔNG kết luận

- **Không** kết luận ADR-026 bị vi phạm hôm nay. Kho hiện có **2 tài liệu**, cả hai do
  `partner_admin` nạp qua đúng cửa. Phát biểu đúng là **"cơ chế duyệt chưa tồn tại"**, không phải
  **"có tài liệu chưa duyệt đang được phục vụ"** — hai câu khác nhau, và tôi chỉ đo được câu thứ nhất.
- **Không** kết luận ai sai. §3 hiến pháp ghi rõ *ADR trước, code sau*; phần "code sau" **chưa tới**.
  Vấn đề là **không chỗ nào theo dõi việc nó chưa tới** — y hệt lời §5.D2.
- **Không** thiết kế cơ chế duyệt. Đó là tính năng nghiệp vụ, thuộc PO + tech-lead.

---

## §13. Mẫu số đầy đủ cho §11 — ba ngăn xếp. **Và backfill ADR-032 ② mới chạy trên MỘT trong BA.**

> Cửa sổ dựng ảnh đã đóng (PO-agent nghiệm thu 09:30, ảnh `d5b73a04d6ef`). Toàn mục là `psql`
> **chỉ-đọc** trên ba ngăn xếp **cục bộ**. **Production `app.adaptivealgo.uk` KHÔNG chạm** — §1 quy
> định chỉ-đọc + thăm dò phải báo trước; nếu §11 cần số của nó thì đó là **việc xin phép PO thật**,
> không phải việc tôi tự đi. Xem §13.4.

### 13.1 🔴 Phát hiện ngoài kế hoạch: `fin05ttl` **CHƯA** được backfill

Tôi đi đo mẫu số cho §11 và đụng phải thứ này trước:

```
                       complaints   PLAINTEXT      trạng thái
fin05                     761            0        ✅ đã backfill
fin05ttl                  742          738        🔴 NGUYÊN VẸN, chưa chạm
fin05do                   607            0        ✅ sạch (nạp sau khi EncryptedText đã có)
```

[ĐO] thêm trên 738 dòng của `fin05ttl`: **105 dòng chứa chữ Việt có dấu**, mới nhất **14/08** —
**đúng cùng tập dữ liệu** đã nằm ở `fin05` trước khi backfill chạy.

⟹ **Phát biểu *"738 → 0"* đúng cho `fin05`, và chỉ cho `fin05`.** Tính trên cả ba ngăn xếp cục bộ,
số dòng lời khai còn plaintext là **738**, không phải **0**.

### 13.2 Cơ chế — và lần này nó nằm ở PHÉP NGHIỆM THU, không ở bản vá

Bản vá **đúng**. Phép nghiệm thu cũng **chặt** — PO-agent đọc lại qua ORM trong container, 761 đọc
được, 0 dòng còn ở dạng bản mã. Không ai làm ẩu.

> 🔴 **Phép nghiệm thu thừa hưởng MẪU SỐ của bản vá.** Bản vá chạy trên `fin05` ⟹ người kiểm mở
> `fin05` ⟹ kết quả sạch ⟹ **kết luận mang tên "backfill xong", không mang tên "backfill xong TRÊN
> `fin05`"**. Tập tự đến đã bị lọc bởi **chính thao tác đang được kiểm**.

Đây là **§8 áp lên một phép NGHIỆM THU** thay vì lên một phép đo — và nó là chỗ hiểm hơn, vì nghiệm
thu là bước ta **dựng ra để bắt** thiếu sót. **Ba ngăn xếp là một tính chất đã được ghi ở dòng thứ tư
của STATE §1**; không ai phải đi tìm nó. Nó chỉ **không có mặt trong câu hỏi**.

**Và tôi mắc đúng lỗi ấy cùng ngày, độc lập:** §11 định hạng kho checkpoint **chỉ trên `fin05`**, và
tôi đã tự khai điều đó ở §11.9 — nhưng **khai một khoảng trống không lấp nó**. Cùng hình dạng với ca
§10.2: nêu tên một thiếu sót rồi đi tiếp. **Hai người, hai artefact, một bộ lọc, một ngày.**

### 13.3 Mẫu số đầy đủ cho §11 — kho checkpoint, ba ngăn xếp

```
                    blob(messages)   chứa HumanMessage   chứa tiếng Việt   dung lượng
fin05                    3.597            3.597              3.413          105 MB
fin05ttl                 2.482            2.482              2.318           95 MB
fin05do                     62               62                 59          127 kB
─────────────────────────────────────────────────────────────────────────────────────
TỔNG cục bộ              6.141            6.141              5.790         ~200 MB
```

⟹ **Mẫu số thật là 6.141, không phải 3.597 — gấp 1,7×.** Và `fin05ttl` **mang cùng hình dạng nội
dung** (100% blob chứa `HumanMessage`, 93% chứa tiếng Việt), không phải một kho rỗng hay kho giả.

**Định hạng §11: GIỮ NGUYÊN mức CAO. Không nâng.** Lý do không nâng, nói rõ vì hôm nay tôi đã phải
tự hạ hai lần: mẫu số lớn hơn **không đổi bản chất** — vẫn cùng biên tin cậy, vẫn không có kẻ tấn
công mới, vẫn không có đường ra ngoài hạ tầng. Nó **đổi ĐỘ CHÍNH XÁC của hồ sơ**, và hồ sơ này sắp
được PO thật dùng để quyết một ADR. **Một định hạng đúng với mẫu số sai vẫn là một định hạng phải
làm lại.**

### 13.4 Câu cần một QUYẾT ĐỊNH, không cần thêm phép đo

Cả hai mục trên quy về **một câu chưa ai trả lời**:

> **`fin05ttl` và `fin05do` là ngăn xếp DÙNG MỘT LẦN, hay là dữ liệu phải được bảo vệ như `fin05`?**

Hai đường, cả hai chấp nhận được, **và sự im lặng thì không**:

- **Nếu DÙNG MỘT LẦN** ⟹ khai ra, và mọi phát biểu về mã hoá at-rest phải **kèm phạm vi** (*"trên
  ngăn xếp phục vụ"*). `fin05ttl` giữ 738 dòng plaintext là **chấp nhận được có ý thức**.
- **Nếu KHÔNG** ⟹ **backfill chưa xong**, và cả hai mục ADR-032 (nhánh giải mã ba trạng thái +
  script nạp lại) phải chạy trên `fin05ttl`.

**Tôi không quyết thay** — đây là phạm vi hạ tầng/sản phẩm. Nhưng tôi ghi hệ quả của việc **không
quyết**: hôm nay đội đang tin *"lời khai khách đã mã hoá at-rest"*, và **câu đó sai với 738 dòng**.
Nó là **đúng loại phát biểu Luật B cảnh báo** — nghe dứt khoát, đi vào hồ sơ, không ai kiểm lại.

### 13.5 Quần thể thứ TƯ — tôi KHÔNG chạm, và nêu để nó không bị quên

**Production `app.adaptivealgo.uk`.** §1 STATE: **CHỈ ĐỌC với mọi phiên, thăm dò phải báo trước.**
Tôi **không gửi một request nào**, không đo, không suy đoán.

**Nêu ra vì hai lẽ:** ① mọi số ở §11 và §13 là của **ba ngăn xếp cục bộ** — nếu ai trích chúng như
*"toàn hệ thống"* thì đó là một mẫu số sai nữa; ② nếu định hạng §11 dùng để quyết một ADR có phạm vi
production, thì **quần thể quyết định nhất là quần thể duy nhất chưa ai đo** — và đó là **câu xin
phép PO thật**, không phải câu đo.

### 13.6 Điều tôi KHÔNG kết luận

- **Không** kết luận `fin05ttl` là một sự cố. Nó là **một bản vá chạy chưa hết phạm vi**, và phạm vi
  đúng thì **chưa ai định nghĩa** (§13.4). Hai câu khác nhau.
- **Không** kết luận ai làm sai. Bản vá đúng, phép nghiệm thu chặt; thiếu sót nằm ở **câu hỏi**, không
  ở **thao tác**.
- **Không** đo production. Không đo metadata Chroma (§12.5) — H3 đã gác, đo bây giờ là đo cho một việc
  chưa chạy.

---

## §14. Ý kiến trước khi PO quyết "bản rẻ" cho ADR-026 — vấn đề KHÔNG phải rẻ, mà là **CÁI GÌ rẻ**

> PO-agent hỏi ý kiến thẩm quyền/dấu vết **trước** khi sếp quyết. Đây là ý kiến, không phải phán quyết
> — phạm vi thuộc PO thật. `psql` chỉ-đọc, **0 thao tác chạm container** (cửa sổ dựng ảnh đang mở).

### 14.1 Mở sổ trước: dự án ĐÃ trả lời đúng câu hỏi này một lần, và câu trả lời còn sống

Tôi không đi tìm nguyên tắc — tôi đi tìm **tiền lệ có thật**. [ĐO]:

```
models.py:352   CheckConstraint(
                  "(status != 'approved') OR (approved_by IS NOT NULL AND approved_at IS NOT NULL)",
                  name="ck_resolutions_approved_requires_approver_br10")

dữ liệu thật:   approved         8   ·  approved_by 8/8  ·  approved_at 8/8
                pending_approval 3   ·  approved_by 0    ·  approved_at 0
                rejected         1   ·  approved_by 0    ·  approved_at 0
```

⟹ Với `resolutions`, **"đã duyệt mà không có người duyệt" là một dòng KHÔNG TỒN TẠI ĐƯỢC.** CSDL từ
chối nó. Không nhờ ai nhớ, không nhờ một bộ lọc, không nhờ một quy trình — **nhờ một ràng buộc**.

**Đó chính xác là hình dạng ADR-026 đang xin cho tài liệu**, và dự án đã dựng nó một lần rồi, đặt tên
theo một luật nghiệp vụ (`BR-10`), và nó đang giữ **8/8**.

### 14.2 Vì sao bản-script-chạy-tay đắt về nghĩa — nói cho chính xác

Cảnh báo của tech-lead đúng, và tôi làm nó sắc hơn một nấc. Vấn đề **không phải** *"ít dấu vết hơn"*:

> **Một tài liệu được duyệt bởi một script là một hành vi duyệt KHÔNG CÓ CHỦ THỂ.**
> Không phải *"chủ thể khó tra"* — mà là **không có chỗ nào để chủ thể tồn tại.**

Đối chiếu `contracts/authority-matrix.yaml`: nó khai **route × vai nào được gọi**. Một script chạy tay
**không đi qua route nào** ⟹ nó **nằm ngoài toàn bộ ma trận thẩm quyền**. ADR-026 phát biểu *duyệt là
**hành vi riêng của `supervisor`***; bản script biến nó thành thao tác của **bất kỳ ai có quyền chạy
lệnh trên máy chủ** — tức `partner_admin`, tức chính vai mà ADR-026 được viết ra để **tách khỏi** việc
này. **Khoảng trống gốc quay lại nguyên hình, chỉ đổi cửa.**

⚠️ **Nhưng nói cho công bằng, và tôi không nâng hạng:** đây **KHÔNG** vi phạm ràng buộc cứng nào.
Ràng buộc 1 (HITL) nói về hoàn tiền/điều chỉnh số dư, không nói về duyệt tài liệu. Đây là một **bước
lùi về truy vết so với một khuôn dự án đã tự đặt ra**, không phải một vi phạm hiến pháp. PO chọn bản
rẻ là **hoàn toàn chính đáng**; ý kiến của tôi là về **rẻ ở CHỖ NÀO**.

### 14.3 🔴 Lập luận mạnh nhất: cột rẻ HÔM NAY và **không dựng lại được** ngày mai

Đây là lý do tôi viết mục này thay vì để im:

| | thêm muộn | phục hồi được không? |
|---|---|---|
| `description_raw` mã hoá (ADR-032) | 738 dòng | ✅ **được** — bản rõ còn đó, mã hoá lại là xong |
| **`approved_by` / `approved_at`** | n dòng đã duyệt | 🔴 **KHÔNG** — **ai đã duyệt** không suy ra được từ bất cứ đâu |

Cả đội vừa tiêu một ngày cho 738 dòng của một cột **thêm muộn nhưng backfill được**. Cột này **thêm
muộn và KHÔNG backfill được**: mọi tài liệu được duyệt trong giai đoạn "bản rẻ" sẽ **vĩnh viễn không
có người duyệt**, và cách duy nhất để hồ sơ sạch là **duyệt lại từ đầu bằng tay**.

**Chi phí của việc chờ không phải là chi phí của cột — nó là chi phí của mọi hàng duyệt trong khoảng
chờ.** Và nó tăng theo thời gian, im lặng.

### 14.4 Đề nghị: giữ "rẻ", chuyển chỗ rẻ

**Phần đắt thật của ADR-026 là MÀN HÌNH cho `supervisor`** (giao diện, luồng, phân công). Đề nghị hoãn
đúng phần đó. **Phần rẻ nên giữ lại là RÀNG BUỘC**, và tech-lead đã khai **cần 1 revision
`migrations/` dù sao đi nữa**:

```
① thêm cột  approved_by (FK users) · approved_at        ← trong revision đã tính
② CHECK: tài liệu chỉ được PHỤC VỤ khi approved_by IS NOT NULL
          — chép nguyên khuôn ck_resolutions_approved_requires_approver_br10
③ script (nếu vẫn cần) BẮT BUỘC nhận user_id của một supervisor làm tham số
          — CSDL TỪ CHỐI dòng thiếu nó, nên script KHÔNG THỂ bỏ qua
```

⟹ Hôm nay **script điền chỗ ấy** (rẻ), mai **màn hình điền chỗ ấy** (đắt) — **dấu vết tồn tại ở CẢ
HAI thế giới**, và bảo đảm cấu trúc **không phải chờ giao diện**.

✅ **Và tôi ủng hộ mạnh phần còn lại của đề xuất tech-lead:** *hoãn đưa vector vào kho cho tới khi có
người duyệt* — biến *"không được phục vụ"* thành **CẤU TRÚC** thay vì một bộ lọc ai đó quên gọi. Đó
đúng là bài học §5.D2 + §12.4 được áp đúng chỗ: **thứ chỉ sống trong một lời dặn thì không có cổng nào
canh được.**

### 14.5 Về khả năng BỎ HẲN `fin05ttl` — đường thứ ba, và nó tốt hơn cả hai đường tôi nêu

Tôi đặt câu hỏi nhị phân (*dùng một lần* / *phải bảo vệ*) và PO-agent tìm ra đường thứ ba: **bỏ thứ
không ai cần**. Đường đó **tốt hơn cả hai** — nó không đổi rủi ro lấy công sức, nó **xoá cả rủi ro
lẫn công sức**.

**Ghi nhận sai sót trong cách tôi đặt vấn đề:** câu hỏi nhị phân của tôi **giả định ngăn xếp phải tồn
tại**, và giả định ấy **không được kiểm** — tôi đã đo *dữ liệu trong đó*, không đo *có ai cần nó
không*. Cùng lớp với §10.2: **đo cái đang có, không hỏi cái đó có nên có không.**

**Hai điều kiện nếu bỏ**, nêu vì chúng dễ trượt:
1. **`down -v`** — xoá volume là thao tác **không đảo ngược được**, và ba ngăn xếp dùng chung một cây
   lệnh. Phải khai **đích danh `-p fin05ttl`**; một lần gõ thiếu `-p` là mất ngăn xếp khác. *(STATE §1
   đã cảnh báo, nhắc lại vì đây đúng là lúc nó bị vấp.)*
2. **Khai vào hồ sơ rằng 738 dòng ấy biến mất VÌ BỊ XOÁ, không vì được mã hoá** — hai câu cho ra cùng
   một con số `0` và **khác hẳn nhau** khi ai đó đọc lại sau sáu tháng. Ba trạng thái, không phải hai.

### 14.6 Điều tôi KHÔNG kết luận

- **Không** phản đối bản rẻ. Tôi phản đối **rẻ ở chỗ không phục hồi được**, và nêu một chỗ rẻ khác.
- **Không** kết luận bản script vi phạm ràng buộc cứng nào — nó không.
- **Không** quyết `fin05ttl`. Đó là quyết định hạ tầng của PO thật.
- **Không** thiết kế màn hình duyệt. Nêu ràng buộc, không nêu giải pháp.

---

## §15. ADR-037 — định hạng phơi nhiễm khoá OpenAI trên runner DÙNG CHUNG

### 15.1 Kiểm lại số đo trước, [ĐO] độc lập

| | PO-agent | tôi đo | |
|---|---|---|---|
| **job mang khoá THẬT** | **6** | **6** | ✅ **khớp — đây là con số quyết định** |
| tổng job | 14 | **17** | ⚠️ lệch, chưa truy nguyên |
| job khoá GIẢ | 8 | 6 (+5 job không dùng khoá) | ⚠️ lệch, **cùng cách chia khác nhau** |
| ghi `.env` ra đĩa | `554` · `618` | `548` · `612` | ✅ **cùng hai chỗ** (mốc heredoc vs dòng khoá) |
| `rm .env` | 0 | **0** | ✅ |
| `compose down` | 0 | **0** | ✅ |
| `always()` | 5, cả 5 là upload-artifact | **5** | ✅ |
| `gh secret list` | chỉ `OPENAI_API_KEY` | ✅ **chỉ một**, tạo 17/08 03:54Z | ✅ |

**Sáu job mang khoá thật — hai người đo độc lập, cùng số.** Hai chỗ lệch nằm ở **cách phân loại job**
(tôi tách thêm rổ *"không dùng khoá"* = 5), **không** ở kết luận nào. Khai theo Luật C, **không hoà**.

🔴 **Và một dữ kiện định khung toàn mục:** `runs-on: self-hosted` → **0 hit**. `ubuntu-latest` → **14**.
⟹ **CHƯA CÓ PHƠI NHIỄM NÀO XẢY RA.** Đây là **định hạng cho một thay đổi SẮP LAND**, không phải cho
một sự cố. Đó là thời điểm rẻ nhất có thể có, và nó đổi hạng của khuyến nghị (§15.7).

### 15.2 🔴 Khoá nằm ở HAI chỗ, không phải một — và chỗ thứ hai chưa ai nêu

`.env` được `cat` ra đĩa runner (dòng 548 · 612), chứa **`OPENAI_API_KEY` thật** cạnh các giá trị
CI-ephemeral. **Ngay sau đó là `docker compose up -d --build`.**

```
bản sao ①   .env trên ĐĨA runner            ← đã nêu
bản sao ②   Config.Env của CONTAINER đang chạy   ← CHƯA AI NÊU
```

Compose đọc `.env` rồi **ghim biến vào container lúc TẠO**. Không `compose down` ⟹ **container sống
tiếp sau khi job kết thúc** ⟹ bất kỳ ai trên máy đó `docker inspect` là đọc được khoá.

> 🔴 **Hệ quả thi hành, và nó là chỗ dễ trượt nhất của cả mục:** một bước dọn chỉ làm `rm .env`
> **trông như đã vá và KHÔNG vá** — bản sao ② còn nguyên, và giờ **không còn `.env` để ai nhìn thấy
> vấn đề**. Đúng luật 17/08: *bản vá đúng có thể làm IM một cổng đang hỏng vì lý do khác.*
> **Dọn phải là `compose down -v` RỒI `rm .env`, và phải chạy trong `always()`** — 5 `always()` hiện
> có đều là `upload-artifact`, **không cái nào dọn gì.**

### 15.3 Định hạng DƯỚI GIẢ ĐỊNH PERSISTENT — giả định đắt nhất khi sai

Bốn tính chất, [ĐO] hoặc suy trực tiếp từ [ĐO]:

| | |
|---|---|
| **Ai đọc được** | mọi job của **mọi team trong cohort** chạy trên cùng runner — theo **thiết kế** của BTC, không phải do lỗi cấu hình |
| **Đọc bằng gì** | `cat .env` · `docker inspect` · `docker exec`. **Không cần đặc quyền nào** ngoài việc chạy được một job |
| **Kéo dài bao lâu** | **vô hạn** — 0 bước dọn, không TTL, không `always()` nào chạm tới |
| **Có phát hiện được không** | **KHÔNG.** Không log nào ghi ai đọc `.env`; khoá dùng lại được **im lặng** ở bất cứ đâu |

> ## 🔴 Hạng: **CHẶN việc chuyển `runs-on`** — không phải sự cố P0
>
> **Không phải P0** vì [ĐO] cho thấy **chưa job nào chạy trên self-hosted** ⟹ **chưa có gì bị lộ**.
> **Là CHẶN** vì ba tính chất trên **có hiệu lực ngay lời-gọi-job đầu tiên** sau khi `runs-on` đổi,
> và **bản vá rẻ hơn nhiều so với việc xoay khoá + kiểm hoá đơn sau đó.**

**Điều làm nó nặng hơn một khoá CI thông thường:** đây là khoá của **một nhà cung cấp TRẢ TIỀN**, và
sổ chi tiêu của đội **không đối chiếu được với bảng điều khiển nhà cung cấp** (§5.A4 vẫn treo). ⟹ Một
người dùng lại khoá này để tiêu tiền sẽ **không hiện ra ở đâu trong dụng cụ đo của ta** cho tới khi
ai đó mở hoá đơn. **Ta không có cửa nào để thấy.**

### 15.4 Cái gì ĐỔI nếu hoá ra EPHEMERAL — đọc thẳng, không định hạng lại

| | persistent | ephemeral |
|---|---|---|
| `.env` còn lại | 🔴 vô hạn | ✅ chết theo máy |
| container mang khoá | 🔴 chạy tiếp | ✅ chết theo máy |
| volume CSDL CI | 🔴 tích luỹ | ✅ chết theo máy |
| đụng cổng giữa các team | 🔴 có | ✅ không |
| **khoá đi qua máy KHÔNG PHẢI của ta** | 🔴 có | 🔴 **VẪN CÓ** |

⟹ **Ephemeral hạ từ CHẶN xuống 🟡**, không xuống 🟢. **Một dòng sống sót qua cả hai thế giới:** khoá
thật vẫn **rót xuống đĩa một máy do BTC quản trị**, và BTC có quyền quản trị trên máy đó. Ephemeral
bảo vệ khỏi **team khác**, **không** bảo vệ khỏi **chủ máy**.

**Và bản vá §15.2 nên land BẤT KỂ câu trả lời là gì** — nó rẻ (hai dòng trong `always()`), nó đúng
trong cả hai thế giới, và **nó không phải chờ BTC**.

### 15.5 Xoay `OPENAI_API_KEY` — có, và mốc thì khai theo điều kiện

- **Bây giờ: KHÔNG cần** *vì lý do này*. [ĐO] chưa job self-hosted nào chạy ⟹ chưa phơi nhiễm.
- 🔴 **Xoay NGAY nếu** một job self-hosted chạy **trước khi** bản vá §15.2 land. Đó là điều kiện
  **quan sát được**, không phải một phán đoán — ai cũng kiểm được bằng `runs-on` + lịch sử Actions.
- **Xoay khi kết thúc cohort, bất kể chuyện gì xảy ra.** Lý do: khoá đã tồn tại trên hạ tầng của một
  bên thứ ba trong suốt kỳ, và *"không có bằng chứng bị đọc"* ≠ *"có bằng chứng không bị đọc"* — ta
  **không có cửa nào để phân biệt hai câu ấy** (§15.3).

⚠️ **Việc xoay này KHÁC hẳn `FIELD_ENCRYPTION_KEY`** — xoay `OPENAI_API_KEY` **không phá dữ liệu nào**,
không cần script nạp lại, không có 738 dòng nào phụ thuộc. **Rẻ. Đừng để nó bị lây tâm lý "không xoay
khoá" từ cảnh báo STATE §1** — cảnh báo ấy nói về một khoá khác, vì một lý do khác.

### 15.6 Container bỏ lại — định hạng riêng, và nó THẤP hơn khoá

CSDL trong container CI là **dữ liệu seed** (`fin05_ci`), không phải khách thật — cùng bộ sinh mà tôi
đã đo cả ngày (`0xxx0000NN`). ⟹ **Phơi nhiễm dữ liệu: 🟢 thấp.**

**Nhưng hai thứ khác thì không thấp:** ① container **giữ cổng** ⟹ team khác dựng service sẽ **đụng
cổng**, và triệu chứng sẽ là *"CI của họ hỏng"*, không phải *"máy còn rác của ta"* — **một lỗi rất tốn
thời gian của người khác**; ② container **mang bản sao ② của khoá** (§15.2) — **đó mới là lý do phải
dọn nó**, không phải vì CSDL.

### 15.7 Tóm tắt cho PO — ba dòng

```
① Bản vá dọn (compose down -v + rm .env, trong always())  →  LAND TRƯỚC khi đổi runs-on.
                                                              Đúng trong CẢ HAI thế giới, không chờ BTC.
② Câu ephemeral của BTC                                   →  quyết CHẶN hay 🟡, KHÔNG quyết ① .
③ Xoay OPENAI_API_KEY cuối cohort                          →  rẻ, không phá dữ liệu. Và xoay NGAY
                                                              nếu ① land sau một lượt self-hosted.
```

---

## §16. ⭐ Câu PO-agent hỏi: **còn chỗ nào dựa vào một bảo đảm KHÔNG KHAI?**

Chẩn đoán của họ đúng và tôi phát biểu lại cho gọn: `ubuntu-latest` **bị huỷ sau mỗi job** là một tính
chất **ta chưa từng khai, chưa test nào canh, chưa ADR nào nhắc** — và nó đang gánh **BỐN việc**:
dọn `.env` · dọn container · dọn volume · chống đụng cổng. **Một cơ chế gánh bốn việc ta không hề giao
cho nó**, và ta chỉ biết mình đứng trên nó vào đúng lúc sắp rút nó đi.

Đi tìm chỗ khác cùng hình dạng. Tiêu chí tôi khai trước: **① có một tính chất đang được DỰA VÀO ·
② không khai ở contract/ADR/test nào · ③ mất đi thì hỏng IM LẶNG.**

### 🔴 16.1 Độ bền của nhật ký kiểm toán — ứng viên MẠNH NHẤT, và tôi suýt phát biểu sai về nó

```
[ĐO] grep -rn "logs_data"  →  docker-compose.yml:127, :229.  HẾT.
     tests/ · contracts/ · docs/DECISIONS.md  →  0 hit
```

`access.log` là **cơ chế bù duy nhất của Pha 1 ADR-025** — thứ đứng thay cho `assigned_to` chưa tồn
tại. Nó sống sót qua `recreate` **chỉ vì đúng một dòng compose khai một volume có tên**. Đổi sang
bind-mount, sang volume ẩn danh, hay dọn tay một lần — **nhật ký thành theo-container**, và:

- **không test nào đỏ** · **không cổng nào kêu** · **triệu chứng là một tệp NGẮN HƠN**, thứ không ai
  nhìn cho tới khi cần điều tra một sự cố **đã xảy ra rồi**.

> **Tôi đã tự dự đoán sai về đúng cơ chế này ở §2.4** — tưởng nó nằm trong lớp writable và chết theo
> `recreate`. `docker inspect` cho thấy ngược lại. **Việc tôi phải đi ĐO mới biết chính là bằng chứng
> nó chưa được khai ở đâu cả.** Nếu có một dòng trong ADR-025 hoặc một test, tôi đã đọc ra thay vì
> đoán — và đoán sai.

### 16.2 "Không có dữ liệu khách THẬT" — một tư thế, không phải một cơ chế

Mọi kết luận PII của tôi hôm nay (§3.3, §3.4, §11) đứng một phần trên việc bộ dữ liệu là **tổng hợp**
(`users.phone` = dãy sinh `0xxx0000NN`). **Không cơ chế nào ngăn dữ liệu thật đi vào** — không cổng
nhập, không cờ môi trường, không CHECK. Nó đúng **vì chưa ai nạp**, không vì có gì chặn.

**Và nó ĐÃ rò một lần, đo được:** 4 chuỗi dạng SĐT trong lời khai **không thuộc bộ seed** (§3.3). Tức
tính chất này **đã bị vi phạm ở quy mô nhỏ**, và thứ phát hiện ra là **một phép đo tình cờ**, không
phải một cổng.

### 16.3 `heldout_set.jsonl` niêm phong · quy tắc `-p` cho ba ngăn xếp

Cả hai **có khai** (STATE §1) nhưng **chỉ khai bằng CHỮ**: không cơ chế nào chặn chạy heldout lần hai,
không cơ chế nào chặn `compose` thiếu `-p`. **Khai bằng chữ tốt hơn không khai** — nên tôi xếp chúng
**dưới** 16.1/16.2 — nhưng cả hai vẫn thoả tiêu chí ③: **hỏng im lặng**, và hỏng **không đảo ngược
được** (heldout đã nhìn thì không niêm lại được; `down -v` nhầm ngăn xếp thì không hoàn nguyên được).

### 16.4 Chỗ tôi KIỂM và thấy nó SẠCH — ghi để không ai đi tìm lại

Ứng viên mạnh nhất tôi nghĩ ra là **`thread_id` của kho checkpoint**: nếu client đặt được `thread_id`
thì đọc được trạng thái hội thoại của người khác — BOLA ở tầng LangGraph. **[ĐO] `main.py:645`:**

```
thread_id=f"{current_user.user_id}:{current_user.iat}"     ← dẫn từ CLAIM CỦA JWT, server tự dựng
```

**Client không chạm được.** Và nó **có khai** — ba chú thích (`main.py:315`, `:488`, `:498`) giải thích
vì sao `iat` phải giữ nguyên qua refresh **chính vì** `thread_id` phụ thuộc nó. ⟹ **Không phải bảo đảm
không khai. Đây là một quyết định có ý thức, được ghi lại, ở đúng ba chỗ người ta sẽ phá nó.**
Ghi ra vì §16 mà chỉ liệt kê chỗ hỏng thì thành một danh sách thiên lệch — **và một mục "đã kiểm,
sạch" là thứ giữ cho danh sách này đọc được.**

### 16.5 Nếp kiểm đề nghị, rút từ cả năm mục trên

> **Một tính chất được DỰA VÀO mà không nêu được nó khai ở ĐÂU, thì nó không phải một bảo đảm — nó là
> một THÓI QUEN của môi trường hiện tại.**
> Phép thử một câu: ***"nếu ngày mai thứ này biến mất, cái gì kêu?"*** — không trả lời được thì **thứ
> đang giữ ta an toàn là sự may mắn về cấu hình**, và may mắn thì không xuất hiện trong diff.
