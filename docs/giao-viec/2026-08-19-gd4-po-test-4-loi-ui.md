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
