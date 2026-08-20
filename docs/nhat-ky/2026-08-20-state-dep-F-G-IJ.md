# Lưu trữ — §5.F, §5.G, §5.I+J chuyển từ `docs/STATE.md`

> Dọn theo §7b (Lead thực hiện 20/08, PO-agent phân xử/đo lại từng mục trước khi cho đóng — không
> nhận claim cũ, đo hết). Ba mục đã ĐÓNG hoặc đã CHUYỂN THÀNH ADR — chuyển nguyên văn, để lại một
> dòng trỏ trong `STATE.md`.

## Trạng thái đóng, [ĐO] PO-agent 20/08

- **F (chốt chặn chi phí sai tầng) — ĐÃ VÁ**, đúng cả hai việc mục F đề xuất: `src/cong_ra_ngoai.py:22`
  tự giải thích "VÌ SAO Ở TẦNG TRANSPORT, KHÔNG Ở `_khoa_cho_nha_cung_cap()`" · `src/cong_ra_ngoai.py:355`
  có `so_luot_da_phat()` — bộ đếm ba rổ. Coder còn ghi lại vì sao đề xuất đầu của chính họ sai. Đóng
  đẹp hơn đề xuất gốc.
- **G (miễn trừ OTP `search_policy` chưa khai) — phần docstring ĐÃ CÓ**, dài hơn một dòng:
  `src/agents/tools/customer_tools.py:968` — *"⚠️ MIỄN TRỪ OTP CHO `search_policy` — CÓ CHỦ ĐÍCH,
  không phải chỗ bỏ sót."* Phần "thêm trường vào `contracts/agent-tools.yaml`" (đề xuất mở rộng
  contract, không phải nợ) CHƯA làm — nếu còn đáng, mở mục riêng, không giữ G "sống" vì nó.
- **I+J (kho checkpoint 0% mã hoá) — ĐÃ THÀNH ADR-045** (`b37218f`, 🟡 chờ PO thật duyệt). Bốn ràng
  buộc I+J đã nêu (bảo vệ tầng serde không đổi cột · đừng che `HumanMessage` · giải quyết retention
  cùng lúc · nghiệm thu dò trên byte) vào ADR nguyên vẹn. Review tìm ra bảng thứ hai chưa ai đếm
  (`checkpoint_writes`, 7.015 dòng, 2 channel `branch:to:model`/`__error__`) — tổng đúng **13.857
  blob, 0% mã hoá**, gấp đôi con số I+J giữ. Xem `docs/DECISIONS.md` ADR-045 cho bản đầy đủ + số mới.

---

## 🔴🔴 F. HAI PHIÊN ĐỘC LẬP HỘI TỤ — chốt chặn chi phí đặt SAI TẦNG

*(tech-lead và tester tìm ra **cùng một lỗ từ hai hướng khác nhau**, không ai biết việc của ai.
Hai NGUỒN độc lập — Luật D ở dạng mạnh nhất: không phải một biến viết hai lần.)*

**Hướng 1 — tech-lead**, khi dựng ca nghiệm thu, tự khai một suýt-sai:
~~`search_policy` là tool DUY NHẤT trong 5 tool không có cổng OTP~~ → **SAI, xem đính chính §5.G.**
Phát biểu đúng: `search_policy` là **một trong HAI** tool không kiểm OTP (tool kia:
`request_human_handoff`), và **cả năm tool đều mang `@_locked`**. Vế còn nguyên hiệu lực: một script
gọi thẳng tool chạy tới `embed_query()` → **gọi thật ra OpenAI**.
Lần này chặn bởi `OPENAI_API_KEY=gia` ⟹ 401, **0 đồng**. Khoá thật thì đó là lượt nhúng tính tiền.

**Hướng 2 — tester**, phép dò *vô hiệu hoá hậu quả TRƯỚC* (khoá giả + base_url `127.0.0.1:9`), chạy
**toàn bộ** `tests/`:

```
620/620 ca ĐÃ CHẠY qua phép dò        ← MẪU SỐ THẬT của cả suite, không phải "3 bộ đã khai"
  1 lời gọi rời khỏi máy: POST api.openai.com/v1/embeddings → nguồn tests/test_api/test_injection.py
[ĐO] PO-agent kiểm lại: test_injection.py có 0 hit `_ton_tien|dang_dong_bang|skipif` — KHÔNG cổng nào
```
**Đối chứng dương của chính phép dò** (thiếu nó thì "chỉ 1 kết quả" = chưa nhìn kỹ): 5 file ứng viên
khác vẫn xanh với khoá giả ⟹ chúng thật sự không gọi.
⚠️ **TRẠNG THÁI THỨ BA:** phép dò chỉ bắt lời gọi phía **HOST**. `test_thanh_phan_tai_lieu_kho.py`
chạy `docker exec` vào container mang khoá RIÊNG ⟹ **NGOÀI tầm đo: KHÔNG ĐO ĐƯỢC**, không được đọc
thành "đã sạch".

🔴 **MỘT GỐC CHO CẢ HAI: chốt chặn chi phí đang nằm ở TẦNG `tests/`, còn cửa ra Internet nằm ở TẦNG
CLIENT NHÀ CUNG CẤP.** Lớp ① là `skipif` **bên trong file test** ⟹ không phủ script nháp, không phủ
file test quên khai, không phủ lượt chat. Lớp ② đã tắt vĩnh viễn. ⟹ **Đường đi tiền hiện không có
lớp nào phủ, và sẽ không có lớp nào phủ cho người sau.**
Và `CLAUDE.md §7` **in sẵn câu lệnh `pytest tests/`** ⟹ người mới **sẽ** gõ nó.

**Bản vá đúng — MỘT CHỖ, BA VIỆC:** chốt chặn phải cắm ở `_khoa_cho_nha_cung_cap()` — **nơi MỌI
đường ra ngoài đi qua**. Một cờ ở đó phủ **test + script nháp + lượt chat**. Và đó **đúng là chỗ**
`so_luot_da_phat` (sổ nợ §5.B, *"nguồn ĐỘC LẬP thật duy nhất với envelope"*) cần cắm ⟹ vừa **chặn
chi tiêu**, vừa **đo chi tiêu** — đúng trục ưu tiên PO đặt 18/08 (§5.A0).

**Điều phối (PO-agent chốt 18/08) — HAI việc, KHÔNG phải chọn một:**
1. **NGAY, tester:** cổng riêng cho **đúng 2 ca `/policy-docs`**, **KHÔNG** gắn `_ton_tien` cả file —
   gắn cả file sẽ **skip luôn 10 ca appsec** (SQLi/XSS) không tốn tiền. Luật J: đừng làm im một cổng
   đang canh đúng để bịt một cổng khác.
2. **TIẾP THEO, tech-lead:** chốt chặn + `so_luot_da_phat` ở tầng client. Đây là việc **thay nửa (b)**
   của bất biến — (b) đã có sẵn 12 ca mẫu và không chảy máu; cái này thì đang chảy.

---

## 🔴 G. ĐÍNH CHÍNH — PO-AGENT ĐỌC MỘT OUTPUT BỊ CHÍNH MÌNH CẮT, LẦN THỨ HAI TRONG NGÀY

*(Bắt bởi **security**. PO-agent phát biểu sai, đã kiểm lại và xác nhận security đúng cả hai điểm.)*

**PO-agent viết** (§5.F, bản đầu): *"4 tool mang `@_locked` + kiểm `otp_verified_at`; `search_policy`
dòng 949 mang `@tool` trần."* **Sai hai chỗ:**

```
[ĐO] customer_tools.py, liệt kê ĐỦ, không cắt cửa sổ:
  791 @tool  792 @_locked   lookup_transaction       813 kiểm otp   OTP_VIEW_MAX_MINUTES
  842 @tool  843 @_locked   get_customer_history     862 kiểm otp   OTP_VIEW_MAX_MINUTES
  875 @tool  876 @_locked   create_ticket            904 kiểm otp   OTP_STEPUP_FRESH_MINUTES
  921 @tool  922 @_locked   request_human_handoff     —  KHÔNG kiểm
  949 @tool  950 @_locked   search_policy             —  KHÔNG kiểm
[ĐO] thân _locked (735-790): `otp_verified_at` chỉ xuất hiện trong CHÚ THÍCH, 0 lần làm điều kiện
```

**Sai ①** — `search_policy` **KHÔNG** mang `@tool` trần: dòng 950 là `@_locked`. **Cả NĂM tool đều có.**
**Sai ②** — **`@_locked` KHÔNG PHẢI cổng OTP.** Nó làm hai việc khác: chặn lượt đã bị bỏ
(`TurnAbandonedError`) và **bất biến chống livelock**. Câu *"4 tool mang `@_locked` + kiểm OTP"*
**gộp hai cơ chế không liên quan**, rồi đọc sự vắng mặt của cơ chế thứ hai như sự vắng mặt của cả hai.

🔴 **CƠ CHẾ SINH LỖI — cùng lớp với đính chính ADR-031, lần thứ HAI trong ngày, cùng một người:**
PO-agent chạy `grep … | head -40`. Output **bị cắt đúng ở dòng 949**. Dòng 950 tồn tại, nằm **ngay
dòng sau chỗ bị cắt**. ⟹ **đọc một khung nhìn đã bị chính lệnh của mình lọc, rồi dùng như toàn cảnh.**
Ca ADR-031: `grep` trúng dòng 143, câu trả lời ở dòng 150. Ca này: `head` cắt ở 949, câu trả lời ở 950.
> ⚠️ **Và dấu hiệu đã nằm SẴN trong chính câu sai, bắt được MIỄN PHÍ lúc đọc, không cần chạy gì:**
> câu viết **"4 tool"** nhưng chỉ kèm **BA số dòng**. **Mẫu số và danh sách lệch nhau trong một câu —
> Luật F.** Không ai phải mở `psql` mới thấy.

**FINDING THẬT — và nó không nằm ở chỗ ai cũng nhìn:**

```
request_human_handoff   docstring: "KHÔNG cần OTP (đây là routing request…)"   ← MIỄN TRỪ CÓ KHAI
search_policy           docstring: không một chữ nào về OTP                     ← MIỄN TRỪ IM LẶNG
```

⟹ Vấn đề **không phải** *"thiếu một cổng"* mà **"một MIỄN TRỪ không phân biệt được với một CHỖ BỎ
SÓT"**. Trên mã hai thứ ấy **trông y hệt nhau** — cùng là sự vắng mặt của mấy dòng. Người đọc sáu
tháng sau biết ngay `request_human_handoff` là **quyết định**; với `search_policy` họ **không có cách
nào biết**. **Luật H ở tầng mã nguồn:** một bên báo triệu chứng kèm chẩn đoán, một bên để lại **im
lặng — và im lặng thì không bác được**.

**Thẩm quyền: KHÔNG vi phạm** (security rà, không nâng hạng). Ràng buộc cứng 2 ✅ · ràng buộc cứng 4 ✅
(OTP gác **truy cập dữ liệu KHÁCH**; `search_policy` đọc tài liệu công khai) · `authority-matrix` ✅ ·
ADR-005 ✅. Miễn trừ **nhiều khả năng cố ý và trên trục "truy cập dữ liệu" là ĐÚNG**.

**Nhưng có TRỤC THỨ HAI chưa ai cân:** `search_policy` là tool **duy nhất mà một khách CHƯA xác thực
OTP làm cho văn bản mình gõ RỜI HẠ TẦNG** (`/agent/chat` → `search_policy` → `search_policy_text()` →
`store.search()` → `embed_query()` → OpenAI/Hoa Kỳ). Bốn tool kia dừng ở cổng OTP trước khi chạm gì.
Miễn trừ được cân trên trục *"có đọc dữ liệu khách không"* (đáp án đúng: KHÔNG) — nhưng đó **không
phải trục có chi phí** của tool này. **Trục có chi phí là ĐƯỜNG RA, và chưa ai cân nó trên trục đó.**

⚠️ **Security tự bác một khung của chính họ trước khi gửi** — [ĐO] `main.py:610`: `@limiter.limit(
"20/minute")` **+** `RedisConcurrencyLimiter`. Có chặn, **hai lớp**. ⟹ tụt từ *"lỗ thủng ngân sách"*
xuống *"một cái đuôi chi phí nhỏ trên một miễn trừ chưa khai"* — **hạ hai bậc, KHÔNG phải việc gấp.**

**Đề nghị (security, PO-agent duyệt): HAI DÒNG CHỮ, KHÔNG phải một cổng.**
🔴 **KHÔNG thêm OTP cho `search_policy`** — nó chặn đúng ca dùng hợp lệ (*"phí rút tiền bao nhiêu"*)
để đổi lấy một rủi ro vừa bị hạ hai bậc. Đúng phản xạ *"thêm một cổng cho yên tâm"* mà **Luật A** gọi tên.
1. **Viết miễn trừ vào docstring `search_policy`**, đúng khuôn `request_human_handoff` đã dùng, nêu
   **CẢ HAI trục**. *Miễn trừ có khai thì lần sau sửa được; miễn trừ im lặng thì người ta xoá nhầm
   hoặc nới nhầm.* (tech-lead, một dòng) — **✅ ĐÃ LÀM, `customer_tools.py:968`, xem trên.**
2. **Đề xuất PO:** thêm vào `contracts/agent-tools.yaml` trường khai ***"tool này có ĐƯỜNG RA ngoài
   hạ tầng không"***. Hôm nay contract khai tên + lược đồ, **không khai đường ra**. Có trường đó thì
   `search_policy` là tool **duy nhất** bật cờ ⟹ **câu hỏi tự hiện ra** thay vì phải có người đi tìm.
   Đụng contract ⟹ đủ §10. — **⬜ CHƯA làm, đề xuất mở rộng contract, không phải nợ.**

---

## 🔴 I. MỞ RỘNG PHẠM VI (KHÔNG phải đính chính) — kho checkpoint nằm NGOÀI sơ đồ mã hoá

*(Bắt bởi **tester**, khi soi tiếp **sau khi** cổng plaintext trúng dự báo 4/4 tới từng chữ số.
PO-agent kiểm lại độc lập bằng `psql`, **chỉ đếm, không in một byte nội dung nào**.)*

```
[ĐO] phép dò của cổng quét KIỂU GÌ:
     character varying 83 · text 30   → 113 cột, QUÉT ĐƯỢC
     json 6 · jsonb 2 · bytea 2       →  10 cột, MÙ HOÀN TOÀN

[ĐO] checkpoint_blobs — chỉ ĐẾM:
     tổng                            6.213
     mang hình dạng Fernet (gAAAAA)      0     ⟹ 0% mã hoá
     CHỨA mã giao dịch "TXN2026…"    2.179
```

⟹ **`738` KHÔNG phải toàn cảnh.** Mẫu số của kho checkpoint (**6.213**) lớn gấp **8,4 lần** mẫu số
ADR-032 đang bàn (**761**).

✅ **KHÔNG AI SAI — đây là MỞ RỘNG PHẠM VI, không phải đính chính.** ADR-032 BỔ SUNG ① **đã khai đúng
mẫu số của nó**: *"[ĐO] cả bốn cột khai `Encrypted*`"*. Kết luận *"hệ thống mã hoá KHÔNG hỏng"* **đúng
BÊN TRONG mẫu số ấy**. Phân biệt này quan trọng: gọi nhầm nó là "đính chính" sẽ làm người đọc mất
niềm tin vào một phát biểu vốn trung thực.

🔴 **RANH GIỚI PHÁT BIỂU — giữ nguyên, đừng nới (Luật B mở rộng: phát biểu này đẩy người nhận vào
CHẾ ĐỘ NÀO):**
`2.179/6.213` là **số dòng chứa MÃ GIAO DỊCH**. **KHÔNG** phải *"2.179 dòng chứa PII khách hàng"*.
SĐT tài khoản hạt giống: **0/6.213**. Khoảng cách giữa hai câu ấy là việc **định hạng của security**,
không phải của tester và không phải của PO-agent.

⚠️ **Nối thẳng vào cảnh báo xoay khoá ở §1, và nó ĐẢO DẤU tin tốt:** `checkpoint_blobs` và
`investigation_logs.tool_input_json` **0% mã hoá** ⟹ chúng **KHÔNG bị ảnh hưởng** khi xoay
`FIELD_ENCRYPTION_KEY`. Nghe như tin tốt. **Nó là tin xấu:** nghĩa là một phần dữ liệu hội thoại
**chưa bao giờ được bảo vệ bởi khoá nào.**

**PHẠM VI — PO-agent chốt: ADR RIÊNG, KHÔNG mở rộng ADR-032.** Ba lý do:
1. **Khác LOẠI, đúng phân biệt đã dùng cho 032 vs 034:** ADR-032 là **nợ MIGRATE** trên một cột **đã
   được khai là mã hoá**; `checkpoint_blobs` **chưa bao giờ nằm trong sơ đồ** — không có gì để migrate.
2. **Ta KHÔNG sở hữu lược đồ ấy** — nó là bảng của LangGraph `PostgresSaver`. Bảo vệ nó là việc ở
   **tầng serde**, không phải đổi kiểu cột ⟹ **cơ chế khác, chi phí khác, rủi ro khác**.
3. **Gộp vào là khoá ADR-032 lại.** 032 đang gần đóng (① xong, ② chờ dựng ảnh, ③ cổng đã land); buộc
   nó chờ một bài toán nặng hơn là **cách chắc chắn nhất để cả hai không xong** — cùng lý lẽ đã dùng
   khi tách finding `tool_input_json` khỏi ADR-031.
🔴 **Cổng CỐ Ý không assert trên 10 cột đó, và đó là quyết định ĐÚNG** — *quyết định cột nào phải mã
hoá là việc của ADR, không phải của tester tự viết chính sách bằng một assertion.* Đúng thứ quy trình
§10 sinh ra để chặn.

**Chờ:** security **định hạng** (mã GD trần có phải finding mức nào) → PO thật duyệt ADR mới.

---

## 🔴🔴🔴 J. KHO CHECKPOINT CHỨA TOÀN BỘ BẢN GHI HỘI THOẠI, KHÔNG MÃ HOÁ — mức CAO

*(Security định hạng sau khi hỏi *"cái gì đã KHÔNG sinh ra dòng nào ở đây"*. PO-agent kiểm lại độc
lập bằng **byte thật**, **chỉ đếm, 0 byte nội dung được in, không giải mã gì**.)*

```
[ĐO] checkpoint_blobs WHERE channel='messages'
     tổng                       3.597
     mang hình dạng Fernet          0      ⟹ 0% mã hoá
     chứa "HumanMessage"        3.597      ⟹ TIN NHẮN KHÁCH, MỌI DÒNG
     chứa "AIMessage"           3.220
     kích thước bảng             37 MB     (security báo 105 MB — MẪU SỐ khác,
                                            có thể là mọi channel / trước nén. Chưa truy,
                                            KHÔNG ĐỔI kết luận)
[ĐO] FK trên mọi bảng checkpoint*   0
```

⟹ **Kho checkpoint không chứa "một ít mã giao dịch". Nó chứa TOÀN BỘ BẢN GHI HỘI THOẠI — gồm văn bản
KHÁCH TỰ GÕ — chưa mã hoá.** §5.I (2.179 dòng mã GD) là **phần vô hại nhất** của bức tranh này.

🔴 **VÌ SAO CẢ SECURITY LẪN PO-AGENT ĐỀU MÙ Ở VÒNG TRƯỚC — bẫy này sẽ tái diễn, [ĐO] chứng minh:**

```
dò TIẾNG VIỆT bằng BYTE THẬT      position('\xe1babf'::bytea in blob)  →  2.738   (ế)
                                   position('\xe1bb8b'::bytea in blob)  →  2.833   (ị)
dò qua encode(blob,'escape') ~ '[àáảãạăâđ…]'                          →      0   🔴 MÙ HOÀN TOÀN
```

`encode(…,'escape')` biến **mọi byte ngoài ASCII** thành escape bát phân ⟹ **mọi ký tự tiếng Việt biến
mất khỏi phép so khớp**, trong khi `TXN2026` (thuần ASCII) hiện ra bình thường.
> **Một bộ dò PII chạy trên `bytea` mà so khớp bằng CHUỖI sẽ THẤY đúng phần ASCII và MÙ đúng phần
> tiếng Việt** — tức **mù đúng phần chứa lời khai khách, thấy đúng phần vô hại nhất**. Kết quả nó trả
> về **không phải *"ít PII"*** mà là ***"chỉ những PII viết bằng chữ không dấu"***.
> **Luật L ở một mặt phẳng mới:** không phải ngưỡng lỏng/chặt, mà **bộ dò MÙ VỚI CHÍNH BẢNG MÃ của
> dữ liệu nhạy cảm nhất**. **Sửa: dò trên BYTE THẬT** (`position(…::bytea in blob)`).

**MỘT MITIGATION CÓ THẬT, [ĐO] chứ không giả định:** `ToolMessage` **đã được che** —
`_scrub_pii_cho_llm` (`customer_tools.py:495`) che `full_name`/`phone`/`account_no` trước khi vào hội
thoại LLM. **Đó chính là lý do SĐT ra `0/6.213` ở §5.I.**
🔴 ⟹ **Con số `0` ấy là bằng chứng CƠ CHẾ CHE ĐANG CHẠY, KHÔNG phải bằng chứng KHO SẠCH. Đừng ai trích
`0/6.213` như một lời trấn an.**
Còn **`HumanMessage` KHÔNG được che, và đó là CỐ Ý, đúng thiết kế** — ADR-025 QĐ1 bác che-lúc-ghi cho
Nhóm A. **Quyết định ấy đúng** — nó chỉ giả định lời khai được bảo vệ bằng **MÃ HOÁ** thay vì bằng che.
**Ở kho checkpoint KHÔNG CÓ VẾ THỨ HAI.**

🔴 **HỆ QUẢ NẶNG NHẤT — nó làm dấu ✅ ở §5.E thành GÂY HIỂU NHẦM:**

| | cột được chỉ định | bản sao plaintext |
|---|---|---|
| lời khai | 23/761 — nợ migrate (ADR-032) | `investigation_logs` 27 |
| **hội thoại** | **`messages.content` 467/467 — HOÀN HẢO** | **`checkpoint_blobs` 3.597 · 37 MB** |

Con số `467/467` **vẫn đúng**. Nhưng kết luận người đọc rút ra — *"nội dung hội thoại được mã hoá
at-rest"* — **SAI**. ⟹ **Người đọc không hỏi *"cột khai `Encrypted*` có sạch không"*; họ hỏi *"lời khai
khách có được bảo vệ không"*.** Ta trả lời câu thứ nhất và **để họ tưởng đã có câu thứ hai.**

**HẠNG: finding RIÊNG · mức CAO · hạng "HỆ SỐ NHÂN BÁN KÍNH", KHÔNG phải "cửa mới".**
Security **cố ý không chọn hạng cao nhất**, và nói rõ cả hai vế:
- **KHÔNG phải P0 gấp:** không kẻ tấn công mới · không đường ra ngoài hạ tầng · không vi phạm ràng
  buộc cứng nào. Cùng CSDL, **cùng biên tin cậy** — ai đọc được cái này thì đã đọc được 738 dòng
  `complaints`. **Không phải cửa mới; cùng một cửa, mở ra căn phòng lớn hơn nhiều.**
- **LÀ mức cao vì BA tính chất CỘNG LẠI, không vì kích thước:** ① **8,4×** mẫu số ADR-032, **39×**
  finding ① · ② **vô hình với job retention** ([ĐO] **0 FK**) trong khi `thread_id` = `"USR-0145:…"`
  **CHỨA `user_id`** ⟹ **không tra ra được nhưng QUY TRÁCH NHIỆM ĐƯỢC — kết hợp tệ nhất** · ③ **0 cơ
  chế prune/TTL/delete** trong `src/`, ~21 MB/ngày, **không trần**.
  *Khác `investigation_logs`: ở đó `NO ACTION` ít nhất làm job **báo lỗi**. Ở đây **job chạy xong, báo
  thành công, bản ghi hội thoại vẫn nguyên. Không cổng nào kêu.***
- 🔴 **CHI PHÍ CỦA VIỆC KHÔNG LÀM, phát biểu chính xác:** ngày ADR-032 backfill xong, **sẽ có người
  viết *"lời khai khách đã được mã hoá at-rest"*. Câu đó SAI chừng nào kho checkpoint còn như hôm nay**
  — và sai theo kiểu **nghe rất đúng**, đi vào hồ sơ, rồi không ai kiểm lại. **Luật G ở tầng hồ sơ,
  bán kính lớn nhất trong ngày.**

**Sắc lại ca "đảo dấu" §5.I:** cách nói đúng **không phải** *"xoay khoá an toàn hơn ta tưởng"* mà
**"xoay khoá KHÔNG BẢO VỆ GÌ ở đây, vì ở đây CHƯA TỪNG có gì được bảo vệ"** — hai câu khác nhau:
ADR-032 nói về rủi ro **HỎNG** dữ liệu; mục này nói về **vùng khoá chưa bao giờ với tới**.

**BỐN RÀNG BUỘC cho ADR mới** *(security nêu ràng buộc, KHÔNG thiết kế — thiết kế thuộc tech-lead)*:
1. 🔴 **Bảo vệ ở tầng SERDE, KHÔNG đổi kiểu cột** — `PostgresSaver` sở hữu lược đồ; đổi cột là đánh
   nhau với thư viện mỗi lần nâng phiên bản.
2. **ĐỪNG che `HumanMessage`** — cùng lý lẽ ADR-025 QĐ1. **Mã hoá, không che.** Bản vá đi hướng scrub
   là **đi ngược một quyết định đã ký**.
3. 🔴 **Giải quyết RETENTION CÙNG LÚC, không để lần sau.** 0 FK ⟹ mục này **sẽ không tự lộ ra** khi ai
   viết job xoá. ADR chỉ nói *"mã hoá kho checkpoint"* mà không nói *"và xoá theo cùng lịch với hồ sơ
   khiếu nại"* ⟹ ta đổi **kho plaintext vĩnh viễn** lấy **kho ĐÃ MÃ HOÁ vĩnh viễn**.
4. **Nghiệm thu phải dò trên BYTE, không dò trên chuỗi đã escape** — nếu không, cổng nghiệm thu **báo
   xanh đúng theo cách nó đã mù hôm nay**.

**THỨ TỰ:** **SAU** ADR-032 (rẻ, đóng khoảng trống **đã khai**), **TRƯỚC** phần còn lại. Không phải vì
nhỏ hơn — vì **đắt hơn và ta không sở hữu lược đồ**, nên nó cần một **QUYẾT ĐỊNH**, không cần một script.

**KHÔNG kết luận:** ❌ có PII **người thứ ba** trong kho (rất có thể có, **chưa đo** — cần NER, chưa
chạy) · ❌ về `fin05ttl`/`fin05do` (số này của `fin05`) · ❌ không giải mã, không trích, không xem tin
nhắn nào.
