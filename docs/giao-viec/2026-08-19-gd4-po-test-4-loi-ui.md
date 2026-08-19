# GĐ4 — 19/08: BỐN LỖI PO THẬT TỰ BẮT KHI TEST KỊCH BẢN A TRÊN UI

> PO thật chạy kịch bản A trên `https://localhost/chat` và tìm ra 4 lỗi mà **cả bốn ô nghiệm thu
> GĐ3 đều không bắt được** — kể cả ô ④ smoke UI vừa xanh. Đọc kèm: brief GĐ3.

## 0. VÌ SAO CỔNG KHÔNG BẮT — ghi trước, để không ai tự trách nhầm chỗ

Ô ④ smoke UI chạy **3 bước tối thiểu** (login · chào · MỘT câu nặng). Cả 4 lỗi dưới chỉ hiện ra ở
**lượt thứ 2 trở đi của một hành trình nhiều lượt** — nơi có OTP xen giữa, có nhiều mã trong một
câu, có ngữ cảnh tích luỹ. **Smoke một-lượt không thể thấy lỗi nhiều-lượt.** Đây là giới hạn đã
biết của một smoke rút gọn, không phải ai làm ẩu — nhưng nó là dữ kiện cho lần sau:
🔴 **hành trình nhiều lượt phải có ít nhất MỘT ca trong mọi bộ smoke, kể cả bộ rút gọn.**

## 1. 🔴 LỖI 2 + LỖI 3 CÙNG MỘT GỐC — scrubber PII phá mã giao dịch của khách

**[ĐO PO-agent — chạy thật `scrub_pii()` trong container]:**
```
'TXN20260731000352'                                → '[LOCATION]'
'Mã giao dịch là TXN20260731000352 và TXN20260731000341'
                                                   → '[PERSON_VN] giao dịch là [PERSON] và TXN20260731000341'
'TXN20260731000341'                                → 'TXN20260731000341'   (nguyên vẹn)
```
`graph.py:787`: `HumanMessage(content=scrub_pii(message) or message)` — **tin nhắn khách bị scrub
TRƯỚC KHI gửi cho model.** ⟹ agent **không bao giờ nhìn thấy** mã `...352`; nó thấy `[PERSON]`.

**Giải thích trọn vẹn hai lỗi PO thật báo:**
- *"đưa 2 mã chỉ tra 1 rồi hỏi lại mã thứ 2"* — vì mã thứ 2 đã bị thay bằng `[PERSON]`.
- *"trả lời có [LOCATION]"* — agent lặp lại đúng thứ nó nhận được.
Và `Mã` → `[PERSON_VN]`: một **từ tiếng Việt thông thường** bị nhận là tên người.

**Gốc kỹ thuật:** `pii.py` ĐÃ có `_plausible_person_span()` loại span chứa chữ số / toàn hoa —
nhưng bộ lọc ấy **chỉ áp cho nhánh `underthesea`**, KHÔNG áp cho `SpacyRecognizer` của Presidio.
Chính docstring `pii.py:44-50` khai Spacy hay gán nhãn sai loại (LOCATION/ORGANIZATION) và đội
**cố ý chấp nhận over-redact**.
🔴 **Quyết định "chấp nhận over-redact" ĐÚNG cho LOG/TRACE, SAI khi áp lên đầu vào gửi model.**
Che nhầm trong log = mất một dòng debug. Che nhầm trong prompt = **agent mù trước dữ liệu khách
vừa đưa** — hỏng chức năng lõi. Cùng một chính sách, hai bối cảnh, chỉ đúng ở một.

**HƯỚNG VÁ (Coder, Bảo Mật định hạng trước):**
- Áp **cùng quy tắc `_plausible_person_span`** (có chữ số ⟹ không phải tên người) cho **MỌI**
  recognizer, không riêng underthesea — quy tắc đã được đội duyệt, chỉ chưa áp đủ chỗ.
- Thêm chặn từ-tiếng-Việt-thông-thường (`Mã`, …) khỏi bị nhận là tên.
- 🔴 **Bảo Mật quyết:** đường `graph.py:787` (scrub đầu vào gửi nhà cung cấp) có nên giữ mức
  over-redact không, hay đường này cần chính sách RIÊNG chặt về loại thực thể nhưng không phá ID.
  KHÔNG tự nới scrub cho log/trace — hai đường phải tách chính sách.

## 2. LỖI 1 — OTP xen giữa làm MẤT câu hỏi của khách
Khách hỏi → hệ thống đòi OTP → xác thực xong → agent **không trả lời câu đã hỏi**, bắt hỏi lại.
Khuôn `pendingStarterRef` đã có sẵn trong `ChatClient.tsx` (dùng cho Finding B GĐ2.5) — **dùng
lại, đừng chế mới**: giữ câu khách đang hỏi, gửi tiếp tự động sau khi OTP xanh.
**Đây là lỗi UX nặng nhất trong bốn** — nó bắt khách gõ lại giữa lúc họ đang bực.

## 3. LỖI 4 — mọi thứ khách thấy phải là TIẾNG VIỆT (lệnh PO thật)
Nhãn scrub (`[LOCATION]`, `[PERSON]`, `[PERSON_VN]`) là tiếng Anh. PO thật yêu cầu **toàn bộ nội
dung trả về khi chat, VÀ nội dung gửi lên LLM, phải là tiếng Việt.**
- Sau khi vá mục 1, nhãn sẽ hiếm khi lọt ra — nhưng **hiếm ≠ không**.
- Đổi nhãn sang tiếng Việt (`[ĐỊA_ĐIỂM]`, `[TÊN_NGƯỜI]`…) ⟹ **đụng test đang ghim chuỗi nhãn**;
  QA/QC rà trước, đổi cùng lượt, không để cổng đỏ im lặng.

## 4. ĐỊNH NGHĨA XONG
- [ ] `scrub_pii` KHÔNG phá mã `TXN…`/`TCK…` ở mọi nhánh recognizer — ca chứng minh chạy thật
- [ ] Ca ĐỐI CHỨNG: PII thật (tên người, SĐT, CCCD) VẪN bị che — không nới nhầm chiều
- [ ] Hành trình: 2 mã trong 1 câu ⟹ tra ĐỦ CẢ HAI, không hỏi lại
- [ ] OTP xen giữa ⟹ trả lời tiếp câu cũ, khách không phải gõ lại
- [ ] Không nhãn tiếng Anh nào lọt ra bong bóng chat
- [ ] Smoke từ nay có ≥1 hành trình NHIỀU LƯỢT

---

## 5. 🔴 LỖI THỨ NĂM (PO thật bổ sung) — CSKH nhận vé mà KHÔNG có hội thoại bot↔khách

**Nguyên văn PO thật:** *"khi khách yêu cầu gặp người thật — thì bên khung chat của CSKH cũng phải
có lịch sử chat giữa bot và khách hàng — như thế họ mới có đủ thông tin để hỗ trợ khách."*

**[ĐO PO-agent — xác nhận đúng là đang thiếu, không phải đã có mà chưa hiện]:**
```
request_human_handoff() → flag_human_handoff()  (complaint_intake.py:131)
   lưu: human_handoff_requested=True · reason (MỘT CHUỖI) · ticket_id
   KHÔNG lưu: hội thoại
màn CSKH `tickets/[id]/TicketDetailClient.tsx` hiển thị:
   investigation_logs · resolutions · tool_result     ← KHÔNG có khối hội thoại nào
grep transcript|lich_su_chat|hoi_thoai|conversation trong frontend/src/  →  0 KẾT QUẢ
```
⟹ CSKH mở vé chỉ thấy **một câu `reason` do AI tóm tắt** + log điều tra. Toàn bộ lời khách tự nói —
ngữ cảnh, cảm xúc, thứ họ đã kể — **không tới được người sắp hỗ trợ họ.** Khách phải kể lại từ đầu,
đúng thứ họ vừa mất công kể cho bot.

**Tin tốt: DỮ LIỆU ĐÃ CÓ, chỉ chưa ai nối.** [ĐO] Postgres có `checkpoints` · `checkpoint_blobs` ·
`checkpoint_writes` · `messages` — LangGraph checkpointer đã lưu toàn bộ hội thoại theo `thread_id`,
sống ngoài tiến trình. **Không phải xây kho mới, là nối một đường đọc.**

**RÀNG BUỘC — đọc kỹ trước khi thiết kế, đây là chỗ dễ vi phạm nhất:**
1. 🔴 **Thẩm quyền: route mới ⟹ `authority-matrix.yaml` ⟹ §10 ĐỦ 7 BƯỚC.** Lần này KHÔNG có đường
   tắt như GĐ3 (GĐ3 bỏ route nên không đụng contract; việc này thì đụng thật). Lead soạn contract +
   ADR, PO-agent trình PO thật duyệt MỘT LẦN.
2. 🔴 **CSKH chỉ được đọc hội thoại của ĐÚNG vé họ đang xử lý** — không phải mọi hội thoại của mọi
   khách. Đây là bề mặt BOLA điển hình (dự án đã có một finding BOLA treo). Bảo Mật soi trước khi code.
3. **Che PII bên thứ ba giữ nguyên** — hội thoại có thể nhắc tên/SĐT người nhận. CSKH thấy hội
   thoại **không** đồng nghĩa thấy dữ liệu người ngoài cuộc. Dùng lại `mask_full_name`/scrub theo
   trường đã có, **KHÔNG** dùng `scrub_pii` NER (chính thứ đang phá mã giao dịch — mục 1).
4. **Chỉ đọc, không sửa.** CSKH không được sửa/xoá lời khách — hội thoại là bằng chứng.
5. **Ghi rõ ai là ai** trong khung hiển thị (khách / bot), và **đánh dấu lượt nào có gọi tool** —
   CSKH cần biết câu nào của bot dựa trên dữ liệu thật, câu nào chỉ là lời thoại.

**Phạm vi đề xuất (Lead chốt sau khi Bảo Mật soi):** GET một route đọc hội thoại theo `ticket_id`
(không theo `thread_id` trần — buộc đi qua vé để có chỗ kiểm thẩm quyền), trả về danh sách lượt đã
che PII; UI thêm một khối "Hội thoại với trợ lý" trong `TicketDetailClient.tsx`.

⚠️ **Đây KHÔNG phải live-chat real-time** (thiết kế WebSocket đã hoãn có ghi sổ). Đây là **bàn giao
ngữ cảnh MỘT CHIỀU**, đúng mức MVP: CSKH đọc được những gì đã xảy ra trước khi họ vào.

---

## 6. 🔴 SỐ ĐO ĐỔI KHUNG QUYẾT ĐỊNH — NER mua gì, với giá bao nhiêu

Bản vá `dec5335` kéo tỉ lệ bóp méo **62,1% → 49,2%** (QA/QC đo trên `golden_set.jsonl`). Cải thiện
thật, **vẫn hỏng**: gần một nửa câu khách gõ bị chèn nhãn sai. Lead + Bảo Mật đang bàn trong khung
*"làm NER chính xác hơn"* (vá `MEDICAL_LICENSE`, loại Spacy…). **PO-agent bước ra khỏi khung đó và đo
câu gốc hơn: NER có nên nằm trên đường này không.**

**[ĐO PO-agent — 124 câu khách THẬT từ `golden_set.jsonl`, hai hàm đã có sẵn trong `pii.py`]:**
```
scrub_pii   (regex + NER — ĐANG DÙNG ở graph.py:787): 63/124 câu bị chèn nhãn = 50,8%
scrub_regex (CHỈ regex, đã có sẵn, pii.py:77)       :  6/124 câu bị chèn nhãn =  4,8%

ĐỐI CHỨNG regex-only vẫn che được gì:
  'SĐT tôi 0912345678'            → 'SĐT tôi [PHONE]'        ✅
  'email toi la nam.le@gmail.com' → 'email toi la [EMAIL]'   ✅
  'CCCD 001199012345'             → 'CCCD [ID_NUMBER]'       ✅
  'Tôi tên Lê Hoàng Nam'          → KHÔNG che                ❌ (tên người lọt)
```

🔴 **Đánh đổi hiện nguyên hình: NER mua ĐÚNG MỘT THỨ — che TÊN NGƯỜI khách tự gõ — với giá là bóp
méo thêm 46% số câu khách.** Mọi định danh gây hại thật (SĐT · email · CCCD/CMND · số tài khoản) đều
do **regex** bắt, tất định, gần như không dương tính giả.

**Thu hẹp phạm vi rủi ro tồn dư — đọc kỹ, nó nhỏ hơn vẻ ngoài:**
- Tên bên thứ ba trong **kết quả tool** đã được che bởi `_scrub_pii_cho_llm` (che theo TRƯỜNG, chính
  xác) — [ĐO ảnh chụp UI: người nhận hiện `C. H. Lan`). NER **không** đóng góp gì ở đó.
- Tên **của chính khách** thì nhà cung cấp nhận cũng không thêm rủi ro mới: ta đã gửi dữ liệu giao
  dịch gắn với khách đó rồi.
- Phần NER thật sự đóng: **tên bên thứ ba do KHÁCH TỰ GÕ** (vd *"tôi chuyển cho chị Nguyễn Thị Lan"*).
  Có thật, nhưng hẹp — và đang được mua bằng việc agent hiểu sai một nửa số câu.

**KHUNG QUYẾT ĐỊNH cho PO thật (PO-agent trình, không tự quyết — đây là chính sách BIÊN DỮ LIỆU):**
| | phương án | agent hiểu đúng | tên bên-thứ-ba khách gõ |
|---|---|---|---|
| A | giữ regex+NER (nay đã vá) | ~49% câu bị méo | được che |
| B | **regex-only trên ĐƯỜNG GỬI MODEL**, giữ regex+NER cho LOG/TRACE | ~95% câu sạch | lọt tới nhà cung cấp |
| C | bỏ scrub hẳn trên đường gửi model | 100% sạch | lọt, kèm SĐT/CCCD |

**PO-agent khuyến nghị B**, và nêu rõ vì sao B khác C: C bỏ luôn regex — mất phần che **có hiệu quả
thật và gần như không dương tính giả**. B chỉ gỡ đúng lớp đang gây hại. Và B **không đụng** chính
sách log/trace (checklist observability Giai đoạn 3 nói về log/trace — đường model-input là phần mở
rộng chưa từng được cân nhắc riêng).

⚠️ **Bảo Mật giữ quyền phủ quyết theo NĐ 13/2023** — nếu họ định hạng "tên bên thứ ba do khách gõ
rời hạ tầng" là không chấp nhận được, B bị loại và ta quay lại tối ưu NER. Trình PO thật kèm ý kiến
Bảo Mật, không trình trước.

---

## 7. 🟢 PHƯƠNG ÁN D' — THỐNG TRỊ CẢ A LẪN B, không phải đánh đổi

Bảo Mật chấp thuận B kèm điều kiện ③: **đo điểm giữa CHƯA AI ĐO** (regex + underthesea, bỏ Spacy)
trước khi chốt. Họ đúng — tôi và Lead đã nhảy thẳng từ A sang B. Phép đo rẻ nên tôi làm ngay.

**[ĐO PO-agent — cùng 124 câu khách thật, cùng corpus, chỉ đổi registry recognizer]:**
```
A  regex + Spacy + underthesea  (ĐANG DÙNG)      62/124 = 50,0% bóp méo
D  regex + underthesea (bỏ Spacy)                16/124 = 12,9%
B  regex-only                                      6/124 =  4,8%   ← mất che tên người
D' regex + underthesea, bỏ Spacy+Date+Phone-chung  7/124 =  5,6%   ← GIỮ TRỌN che tên người
```

🔴 **Ba nhóm trong 12,9% của D — phân loại xong mới thấy hai nhóm là THIỆT HẠI THUẦN:**
| nhóm | ví dụ | phán |
|---|---|---|
| `DateRecognizer` | `"Ngày 07/07"` → `"Ngày [DATE_TIME]"` | **thiệt hại thuần** — ngày không phải PII ở đây, và agent CẦN nó để tra |
| `PhoneRecognizer` (chung) | `"chuyển 18.000.000"` → `"chuyển [PHONE_NUMBER]"` · `"1.647.000"` → `[PHONE_NUMBER]` | 🔴 **NẶNG NHẤT TRONG NGÀY** — recognizer SĐT nuốt **SỐ TIỀN** |
| `VN_PHONE_NUMBER` | `"cho so 0884000085"` → `[VN_PHONE_NUMBER]` | **ĐÚNG** — dương tính thật, giữ nguyên |

🔴 **Số tiền bị thay bằng `[PHONE_NUMBER]` tệ hơn mất mã giao dịch.** Trong một khiếu nại tài chính,
**số tiền là dữ kiện lõi**; mất nó thì agent không thể đối chiếu, không thể phân loại, và mọi con số
nó nói sau đó đều không có gốc. Định dạng tiền VN (`18.000.000`) trùng hình dạng SĐT quốc tế —
recognizer chung của Presidio không biết bối cảnh ví điện tử Việt.

**ĐỐI CHỨNG D' — giữ trọn MỌI thuộc tính bảo mật của A:**
```
'Tôi tên Lê Hoàng Nam'              → 'Tôi tên [PERSON_VN]'                    ✅ che
'tôi chuyển cho chị Nguyễn Thị Lan' → 'tôi chuyển cho chị [PERSON_VN]'         ✅ che BÊN THỨ BA
'toi chuyen cho so 0884000085'      → '[VN_PHONE_NUMBER/VN_ID_NUMBER]'         ✅ che
'email nam.le@gmail.com'            → '[EMAIL_ADDRESS/URL]'                    ✅ che
'CCCD 001199012345'                 → '[VN_ID_NUMBER]'                         ✅ che
'TXN20260731000352'                 → nguyên vẹn                               ✅ giữ
'chuyen 18.000.000'                 → nguyên vẹn                               ✅ giữ
'Ngày 07/07 rút 1.524.000đ'         → nguyên vẹn                               ✅ giữ
```

🟢 **D' sạch ngang B (5,6% vs 4,8%) và giữ TRỌN thuộc tính bảo mật của A** ⟹ **THỐNG TRỊ cả hai.**
**Rủi ro tồn dư của B — "tên bên thứ ba khách tự gõ rời hạ tầng" — TAN BIẾN.** Không còn đánh đổi
nào để PO thật phải quyết. Câu hỏi chính sách biên-dữ-liệu **tự đóng bằng một phép đo**.

**Vì sao câu hỏi ấy từng tồn tại:** cả tôi lẫn Lead đều đóng khung *"NER hay không NER"* — một lựa
chọn nhị phân giữa hai gói. Sự thật là **gói NER gồm nhiều recognizer độc lập**, và **hai trong số
đó (Date, Phone-chung) gây gần hết thiệt hại mà không che thêm PII nào**. Hỏi "bỏ NER không" là hỏi
sai đơn vị. Bảo Mật ép đo điểm giữa chính là thứ làm đơn vị đúng hiện ra.

**⟹ ĐỀ XUẤT CHỐT: D'**, và ba điều kiện của Bảo Mật giữ nguyên hiệu lực (ADR có khai · không đụng
log/trace · mốc xem lại). Nợ sửa docstring `pii.py:78-80` vẫn đứng. `MEDICAL_LICENSE` đã loại thống
nhất — không đổi.
