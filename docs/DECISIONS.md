# Nhật ký quyết định kiến trúc (ADR)

> **CHỈ GHI THÊM. KHÔNG SỬA, KHÔNG XOÁ ADR cũ.**
>
> Vì sao: cần biết *tại sao* đã từng quyết định ngược lại. Nếu chỉ ghi kết quả cuối, vài
> tuần nữa sẽ có phiên Claude "tối ưu" nó trở lại — vì phương án cũ thường trông hợp lý
> hơn khi thiếu ngữ cảnh. **Lý do bác bỏ chính là thứ chặn vòng lặp đó.**
>
> Quyết định sai → ghi ADR MỚI thay thế (`Thay thế: ADR-00x`), giữ nguyên ADR cũ.
>
> Ghi ADR mới bằng `/adr`. Quy tắc vàng: **nếu một quyết định chưa nằm trong file này thì
> nó chưa tồn tại** — nói "ừ chốt vậy đi" trong chat không tính, phiên sau nó biến mất.

**Ghi chú về ADR-001…008:** đây là các ADR **hồi tố**, viết ngày 2026-08-13 dựa trên code
thật, commit history và các phiên làm việc trước. Ngày ghi trong mỗi ADR là ngày *quyết
định thực sự được đưa ra* (suy từ commit/migration), không phải ngày viết ADR.

---

## ADR-001 — AI gọi tool dưới danh nghĩa `customer`, không có role riêng

- **Ngày:** 2026-07 (từ thiết kế ban đầu) · **Trạng thái:** Đang hiệu lực
- **Bối cảnh:** Cần quyết định AI agent có role riêng trong hệ thống phân quyền không.
- **Quyết định:** Không. AI chạy trong phiên của khách, gọi tool với chính `user_id` của
  khách, chịu đúng mọi giới hạn của role `customer`.
- **Lý do:** Một role `ai_agent` riêng tạo ra bề mặt tấn công mới và một bảng phân quyền
  thứ hai phải giữ đồng bộ. Cách này khiến **chặn được `customer` là chặn được AI** — một
  lớp phòng thủ thay vì hai.
- **Hệ quả:** `contracts/authority-matrix.yaml` không có cột `ai_agent`. Test INV-02 kiểm
  "không route chạm tiền nào mở cho `customer`" chính là kiểm AI.

## ADR-002 — Sếp duyệt MỌI phạm vi, kể cả nội bộ ví–ví

- **Ngày:** 2026-07 · **Trạng thái:** Đang hiệu lực · **Thay thế:** thiết kế gốc
- **Bối cảnh:** Thiết kế ban đầu cho CSKH tự duyệt case nội bộ ví–ví (số tiền nhỏ, rủi ro
  thấp, giảm tải cho sếp).
- **Quyết định:** Bỏ. Chỉ `supervisor` duyệt, cho mọi phạm vi, không phân biệt số tiền.
- **Lý do bác bỏ phương án cũ (QUAN TRỌNG — đây là thứ chặn "tối ưu" ngược):** để CSKH tự
  duyệt trông hợp lý hơn về UX và vận hành, nên **sẽ có agent đề xuất quay lại**. Nhưng:
  (a) "ngoài thẩm quyền" định nghĩa theo **role**, không theo hạn mức — hạn mức tạo ra
  đường lách (chia nhỏ giao dịch); (b) một luồng duyệt duy nhất dễ audit hơn hai; (c) đây
  là sản phẩm tài chính đem pitch trước doanh nghiệp ví, HITL không có ngoại lệ mới là
  điểm mạnh kể được.
- **Hệ quả:** INV-01/03/04. `cskh` = `deny` ở mọi route chạm tiền.

## ADR-003 — HITL ép ở tầng DATABASE, không chỉ tầng application (BR-10)

- **Ngày:** 2026-07 · **Trạng thái:** Đang hiệu lực
- **Quyết định:** Thêm CHECK constraint
  `ck_resolutions_approved_requires_approver_br10`:
  `(status != 'approved') OR (approved_by IS NOT NULL AND approved_at IS NOT NULL)`
- **Lý do:** Ràng buộc nằm trong `if` của route chỉ bảo vệ được đường đi qua route đó. Một
  câu `UPDATE` viết tay, một script migration, một endpoint mới quên kiểm — đều lách được.
  CHECK constraint thì **không đường nào lách**.
- **Hệ quả:** INV-07 kiểm constraint này còn tồn tại. Đây là lớp phòng thủ cuối cùng của
  ràng buộc cứng số 1.

## ADR-004 — Ba trục trạng thái TRỰC GIAO, không phải một FSM tuyến tính

- **Ngày:** 2026-07 · **Trạng thái:** Đang hiệu lực
- **Bối cảnh:** Cách mô hình hoá tự nhiên là một máy trạng thái ticket nối tiếp
  (`draft → cskh_received → pending_bank → pending_supervisor → approved → executed`).
- **Quyết định:** Không dùng. Tách thành 3 trục độc lập:
  `Resolution.status` (HITL) · `Ticket.hitl_status` (góc nhìn CSKH) ·
  `Ticket.partner_wait_status` (chờ ngân hàng).
- **Lý do:** Chờ ngân hàng và chờ sếp duyệt **chạy song song**, không nối tiếp. Một ticket
  có thể vừa `waiting` ngân hàng vừa `pending` sếp. Ép vào một FSM tuyến tính buộc phải
  bịa ra thứ tự không có thật, rồi phát sinh state tổ hợp khi thực tế lộ ra.
- **Hệ quả:** `contracts/resolution-state-machine.yaml` (đổi tên từ `ticket-state-machine`
  — tên cũ mô tả sai bản chất). INV-12 kiểm giá trị contract khớp CHECK constraint thật.

## ADR-005 — Hai mức tươi OTP: 12 giờ để xem, 15 phút cho hành động

- **Ngày:** 2026-08-10 · **Trạng thái:** Đang hiệu lực
- **Quyết định:** `OTP_VIEW_MAX_MINUTES = 12h` cho tool chỉ đọc
  (`lookup_transaction`, `get_customer_history`); `OTP_STEPUP_FRESH_MINUTES = 15 phút` cho
  `create_ticket`; `RESOLUTION_APPROVAL_OTP_FRESH_MINUTES = 10 phút` cho sếp duyệt.
- **Lý do:** Một ngưỡng duy nhất buộc phải chọn giữa phiền khách (ngặt) và rủi ro (lỏng).
  Tách theo *hậu quả của hành động* giải được cả hai: xem thì thoáng, tạo/duyệt thì ngặt.
- **Hệ quả:** AUTH-005/007/008. INV-10 + `test_otp_step_up_cho_hanh_dong_co_hau_qua_van_con`.

## ADR-006 — Bỏ hẳn câu hỏi bảo mật (KBA) khỏi vai trò xác thực

- **Ngày:** 2026-08-12 · **Trạng thái:** Đang hiệu lực · **Thay thế:** một phần ADR-005
- **Bối cảnh:** Đối chiếu luồng auth với NIST 800-63B-4 / PSD2 / OWASP ASVS 5.0 (đợt AUTH5).
- **Quyết định:** KBA không còn gate bất kỳ route nào. `security_question` /
  `security_answer_hash` giữ lại trong model **chỉ để hỗ trợ nhận diện khi khách gọi
  hotline**, và nâng hash lên argon2id.
- **Lý do:** NIST 800-63B-4 loại KBA khỏi danh sách authenticator hợp lệ — câu trả lời
  thường đoán được hoặc tìm được trên mạng xã hội. Giữ nó tạo *ảo giác* hai lớp.
- **Hệ quả:** `verify_otp` bỏ `answer_ok`. Test `test_security_answer_hash.py` viết lại,
  gỡ marker `security_finding`.

## ADR-007 — Refresh token GIỮ NGUYÊN `iat` gốc lúc login

- **Ngày:** 2026-08-12 · **Trạng thái:** Đang hiệu lực
- **Bối cảnh:** Rút access token từ 8 giờ xuống 15 phút, thêm refresh token rotation.
- **Quyết định:** Mọi access token cấp qua `/auth/refresh` phải mang **`iat` GỐC của lần
  login đầu tiên**, không phải giờ hiện tại. Dùng `calendar.timegm()` để round-trip khớp
  chính xác cách PyJWT mã hoá.
- **Lý do:** LangGraph dùng `user_id:iat` làm `thread_id` của hội thoại. `iat` đổi ⟹
  `thread_id` đổi ⟹ **agent mất sạch trí nhớ hội thoại ngay sau lần refresh đầu tiên**.
  Phát hiện qua test lệch đúng 7 giờ = timezone máy (`datetime.timestamp()` trên datetime
  naive diễn giải theo giờ LOCAL, khác PyJWT luôn coi naive là UTC).
- **Hệ quả:** `test_refresh_preserves_original_iat_for_thread_continuity`. **Cảnh báo cho
  phiên sau:** đây là loại lỗi im lặng — không crash, không log, chỉ là agent bỗng "quên"
  khách vừa nói gì.

## ADR-008 — Reuse refresh token ⟹ thu hồi CẢ FAMILY

- **Ngày:** 2026-08-12 · **Trạng thái:** Đang hiệu lực
- **Quyết định:** Khi một refresh token đã rotate bị dùng lại, thu hồi toàn bộ chuỗi token
  cùng `family_id` — kể cả token mới nhất mà client hợp pháp đang giữ. Buộc đăng nhập lại.
- **Lý do:** Token đã rotate bị dùng lại chỉ có thể do bị sao chép — client hợp pháp không
  có lý do gì dùng lại token cũ. Chỉ chặn token bị reuse thì kẻ tấn công và nạn nhân **thay
  phiên dùng chung session mà không ai biết**. Đăng nhập lại là cái giá rẻ hơn nhiều.
- **Hệ quả:** `test_refresh_token_reuse_revokes_whole_family`. Đã kiểm thật qua curl
  4 bước (login → refresh → reuse token cũ → token mới cũng bị từ chối).

---

## Mẫu ADR mới

```markdown
## ADR-0xx — <tiêu đề ngắn, thể khẳng định>

- **Ngày:** YYYY-MM-DD · **Trạng thái:** Đang hiệu lực | Đã thay thế bởi ADR-0yy
- **Bối cảnh:** vấn đề gì buộc phải quyết
- **Quyết định:** chốt cái gì
- **Lý do:** vì sao chọn cái này
- **Lý do BÁC BỎ phương án khác:** (bắt buộc nếu phương án kia trông hợp lý — đây là thứ
  chặn phiên Claude sau "tối ưu" ngược lại)
- **Hệ quả:** file/test/contract nào bị ảnh hưởng
```
