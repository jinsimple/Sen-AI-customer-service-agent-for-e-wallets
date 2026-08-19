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
