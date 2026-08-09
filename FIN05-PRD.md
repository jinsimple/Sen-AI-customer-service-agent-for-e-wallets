# FIN-05 — Product Requirements Document
## AI Agent CSKH Ví điện tử & Xử lý Khiếu nại Giao dịch

**Phiên bản:** 2.1 · Đi kèm với `FIN05-Brief.md`, `FIN05-Wireframe.html`, `FIN05-Data-Brief.md`

---

## 1. Personas

| Persona | Bối cảnh & nhu cầu |
|---|---|
| **Khách hàng** | Gặp sự cố giao dịch, không rành thuật ngữ, thường không nhớ mã giao dịch. Cần câu trả lời rõ ràng và mốc thời gian cụ thể. |
| **Nhân viên CSKH** | Tiếp nhận và điều tra **mọi** ticket, kể cả case khẩn — không có quyền tự duyệt. Cần thấy toàn bộ investigation trail để trình sếp nhanh và đúng. |
| **Sếp / Người phê duyệt** | Cấp duyệt duy nhất, cho mọi phạm vi giao dịch. Cần đủ căn cứ hiển thị ngay để quyết trong vài giây. |

---

## 2. User Stories (US-001 → US-018)

Định dạng: *Với vai trò [X], tôi muốn [Y], để đạt được [Z]* + tiêu chí chấp nhận. Đồng bộ với Trello card S2-02.

### Nhóm 1 — Nền tảng

**US-001 — Đăng nhập & phân quyền**
Với vai trò khách hàng/nhân viên CSKH, tôi muốn đăng nhập và được phân đúng vai trò, để tôi chỉ thấy và dùng đúng chức năng mình được phép.
- Đăng nhập đúng → chuyển đúng giao diện theo vai trò
- Đăng nhập sai → báo lỗi rõ, không cho vào hệ thống
- CSKH không thấy/thao tác được chức năng của "sếp"
- Khách hàng không vào được dashboard CSKH kể cả sửa URL trực tiếp

**US-006 — Xác thực danh tính trước thao tác nhạy cảm**
Với vai trò khách hàng, tôi muốn xác thực bằng OTP phiên làm việc và câu hỏi bảo mật trước khi thao tác liên quan đến tiền, để tài khoản được bảo vệ mà không bị hỏi mật khẩu/OTP giao dịch qua chat.
- Trước thao tác về tiền → yêu cầu OTP phiên làm việc + 1 câu hỏi bảo mật khớp giao dịch gần nhất
- Sai OTP quá số lần cho phép → khoá phiên, hướng dẫn kênh khác
- Không màn hình nào hỏi trực tiếp mật khẩu hoặc OTP giao dịch chuyển tiền
- Nhiều lần thất bại OTP rồi rút gần hết số dư ngay sau đó → hệ thống tự ghi nhận tín hiệu bất thường (không tự kết luận, chỉ gắn cờ — liên hệ FS-06 ở §5)

### Nhóm 2 — Tiếp nhận & điều tra (lõi AI)

**US-002 — AI trả lời theo knowledge base**
Với vai trò khách hàng, tôi muốn AI trả lời câu hỏi chính sách dựa trên tài liệu thật của ví, để tôi nhận thông tin chính xác thay vì bị suy đoán.
- Hỏi về chính sách 1 trong 4 loại khiếu nại → trả lời có trích nguồn từ knowledge base
- Ngoài phạm vi tài liệu → nói rõ "không có thông tin", không suy đoán
- Không tự sinh thêm số liệu/cam kết không có trong tài liệu gốc

**US-003 — Luồng khiếu nại lõi**
Với vai trò khách hàng, tôi muốn mô tả sự cố giao dịch và được AI tra cứu + phân loại đúng 1 trong 4 loại khiếu nại, để tôi biết vấn đề của mình đang ở đâu mà không cần gọi tổng đài.
- Agent gọi tool tra cứu giao dịch thật, không tự bịa trạng thái/số tiền
- Phân loại đúng 1 trong 4 loại, hiển thị trên UI
- Giao dịch không tồn tại → báo "không tìm thấy", không suy diễn
- Mọi số liệu trên UI trace được về đúng 1 tool call cụ thể

**US-004 — Investigation trail cho CSKH**
Với vai trò nhân viên CSKH, tôi muốn xem toàn bộ quá trình điều tra của AI (không chỉ kết luận), để tôi tin tưởng và xử lý ticket nhanh, không phải tra lại từ đầu.
- Mỗi bước hiển thị: tool đã gọi, kết quả tool, ghi chú của AI
- Mở ticket bất kỳ → thấy investigation trail đầy đủ kèm thời gian từng bước
- AI không tự kết luận gian lận cho case nghi vấn — chỉ trình bày dấu hiệu quan sát được
- Case chuyển nhầm: đầu ra không ngụ ý ví có thể tự thu hồi tiền từ người nhận

**US-008 — Xử lý khi không tìm thấy giao dịch**
Với vai trò khách hàng, tôi muốn được hỏi lại có kiểm soát khi hệ thống không tìm thấy giao dịch, để không bị bỏ mặc hay nhận câu trả lời bịa ra.
- Không tìm thấy → hỏi lại tối đa N lần, mỗi lần đúng 1 thông tin cụ thể
- Quá N lần → tạo ticket "cần tra thủ công", nói rõ giới hạn
- Không có trường hợp nào agent tự sinh mã giao dịch/số tiền/trạng thái khi chưa tra được

**US-009 — Xử lý mô tả mơ hồ**
Với vai trò khách hàng, tôi muốn agent hỏi lại làm rõ khi mô tả chưa đủ rõ, để không bị phân loại sai chỉ vì tôi tự đoán nhầm.
- Mô tả chưa đủ xác định 1/4 loại → hỏi làm rõ, không tự chọn đại
- Khách tự gọi tên sai loại → phân loại cuối dựa trên dữ liệu tool, không theo lời khách tự chẩn đoán
- Xử lý được mô tả viết tắt/không dấu/sai chính tả thông thường

### Nhóm 3 — Trải nghiệm khách hàng

**US-007 — Theo dõi trạng thái real-time**
Với vai trò khách hàng, tôi muốn xem trạng thái khiếu nại cập nhật theo thời gian thực, để biết vấn đề đang ở bước nào mà không cần hỏi lại tổng đài.
- Timeline tối thiểu: tiếp nhận & xác thực → tra cứu → điều tra → chờ duyệt → hoàn tất
- Cập nhật ngay khi CSKH/sếp thao tác
- "Chờ đối tác ngân hàng" hiển thị khác rõ với "chờ nội bộ duyệt"

**US-010 — Memory hội thoại & lịch sử khách**
Với vai trò khách hàng, tôi muốn agent nhớ những gì tôi vừa nói trong phiên và biết lịch sử khiếu nại trước của mình, để không phải lặp lại thông tin.
- Trong cùng phiên, không hỏi lại thông tin đã cung cấp
- Tra được lịch sử khiếu nại trước của đúng khách đang xác thực
- Không giữ ngữ cảnh xuyên phiên đăng nhập khác nhau trừ khi có cơ chế lưu trữ riêng được xác nhận

### Nhóm 4 — Xử lý & phê duyệt

**US-005 — Sếp phê duyệt (HITL)**
Với vai trò sếp/người có thẩm quyền phê duyệt, tôi muốn xem đầy đủ căn cứ điều tra và đề xuất trước khi quyết định, để tôi duyệt/từ chối nhanh mà vẫn kiểm soát rủi ro.
- Ticket CSKH trình lên → thấy loại khiếu nại, phạm vi, đề xuất, căn cứ (trích tool result)
- Đúng 3 hành động: Duyệt / Từ chối / Yêu cầu điều tra thêm — không có đường nào để AI/CSKH tự thực thi đổi số dư
- Case chạm ngân hàng → chỉ có nút "Tạo yêu cầu tra soát", không có nút duyệt hoàn tiền trực tiếp
- Mọi hành động ghi log: ai, khi nào, căn cứ gì

**US-011 — CSKH xem & lọc hàng chờ**
Với vai trò nhân viên CSKH, tôi muốn lọc/sắp xếp hàng chờ theo trạng thái và ưu tiên, để xử lý đúng case cấp bách trước.
- Lọc tối thiểu: chờ duyệt / chờ đối tác ngân hàng / vượt thẩm quyền / khẩn cấp
- Ticket nghi gian lận Tầng A nổi bật rõ hơn ticket thường
- Ticket đối tác quá hạn SLA có trạng thái/cảnh báo riêng

**US-012 — CSKH tiếp nhận mọi case trước khi trình sếp**
Với vai trò nhân viên CSKH, tôi muốn tiếp nhận đầy đủ hồ sơ điều tra cho mọi loại case kể cả khẩn cấp, để luôn là điểm kiểm tra đầu tiên trước khi việc lên sếp.
- Không case nào (kể cả nghi gian lận Tầng A) đi thẳng từ AI lên sếp, bỏ qua CSKH
- CSKH thấy đủ: loại khiếu nại, phạm vi, mức ưu tiên, toàn bộ investigation trail trước khi trình
- CSKH không có nút "duyệt" cho bất kỳ case nào — chỉ có "trình sếp" / "yêu cầu điều tra thêm"

**US-013 — Tra soát ngân hàng & xử lý quá hạn**
Với vai trò nhân viên CSKH, tôi muốn tạo yêu cầu tra soát cho case chạm ngân hàng và được cảnh báo khi đối tác quá hạn, để chủ động cập nhật cho khách thay vì im lặng chờ.
- Case chạm ngân hàng → có nút tạo yêu cầu tra soát, không có nút duyệt hoàn tiền trực tiếp
- Yêu cầu ghi rõ ngân hàng đối tác, lý do, thời điểm gửi
- Quá hạn SLA chưa phản hồi → ticket chuyển "quá hạn chờ đối tác", CSKH nhận cảnh báo

**US-014 — Escalate nghi gian lận theo 2 tầng**
Với vai trò nhân viên CSKH, tôi muốn hệ thống phân loại mức khẩn cấp theo số lượng/loại tín hiệu gian lận bật, để ưu tiên đúng mức mà không ngập trong cảnh báo giả.
- 1 tín hiệu Tầng A → escalate ngay, ưu tiên khẩn
- Tầng B: 1 tín hiệu → chỉ ghi nhận cho CSKH thấy; ≥2 tín hiệu cùng bật mới escalate
- AI không bao giờ kết luận "gian lận" — chỉ trình bày tín hiệu quan sát được
- Gắn cờ không tự động khoá ví — 2 hành động độc lập
- Case có dấu hiệu giống đáng ngờ nhưng có căn cứ hợp pháp rõ ràng → không bị escalate nhầm

**US-015 — Chặn hành động ngoài thẩm quyền**
Với vai trò nhân viên CSKH, tôi muốn hệ thống tự chặn và giải thích khi tôi cố thao tác vượt quyền, để không lỡ duyệt nhầm case không thuộc quyền mình.
- Không có nút hành động nào cho phép CSKH tự duyệt hoàn tiền/điều chỉnh số dư
- Cố thao tác vượt quyền → hệ thống chặn, hiển thị lý do theo ma trận thẩm quyền
- Mọi lần bị chặn được ghi log

### Nhóm 5 — Tuân thủ

**US-016 — Bảo vệ thông tin bên thứ ba (PDPA)**
Với vai trò khách hàng, tôi muốn thông tin của người khác liên quan đến khiếu nại của tôi được ẩn bớt, để quyền riêng tư của mọi người được bảo vệ.
- Case chuyển nhầm: tên/SĐT người nhận hiển thị cho khách chỉ ở dạng che một phần
- Hỏi thông tin giao dịch của người khác → hệ thống từ chối, không tiết lộ
- CSKH thấy đủ thông tin cần xử lý nhưng không thừa ngoài phạm vi case

**US-017 — Ghi log hành động HITL**
Với vai trò sếp/người phê duyệt, tôi muốn mọi hành động duyệt/từ chối được ghi log đầy đủ, để truy vết trách nhiệm nếu có tranh chấp sau này.
- Mỗi hành động ghi: ai, khi nào, căn cứ nào (trích investigation trail)
- Log không sửa/xoá được bởi người dùng thường
- Tra cứu log được theo ticket_id

### Nhóm 6 — Giá trị vận hành

**US-018 — Báo cáo tổng quan vận hành**
Với vai trò sếp/quản lý, tôi muốn xem báo cáo thời gian xử lý và tỉ lệ khiếu nại theo loại, để đánh giá hiệu quả và báo cáo đối tác/mentor.
- Hiển thị tối thiểu: thời gian xử lý TB, tỉ lệ đề xuất AI được duyệt, tỉ lệ escalate, phân bố theo loại & phạm vi
- Số liệu khớp dữ liệu ticket thật, không phải ước lượng
- Lọc được theo khoảng thời gian

---

## 3. Complaint Taxonomy × Phạm vi giao dịch

Cập nhật theo schema dữ liệu thật (`FIN05-Data-Brief.md`): **3 phạm vi**, không phải 2.

| Loại khiếu nại | Nội bộ ví–ví | Từ ngân hàng (nạp) | Ra ngân hàng (rút) |
|---|---|---|---|
| **Chuyển nhầm** | Tra được cả 2 phía, mediate nội bộ | — (nạp không có "chuyển nhầm" người nhận) | Sai số tài khoản đích, tra soát riêng |
| **Tiền chưa về** | Lỗi hệ thống nội bộ, hiếm kéo dài | Delay đối soát liên ngân hàng/NAPAS | Delay xác nhận từ ngân hàng nhận |
| **Trừ tiền 2 lần** | Sửa trực tiếp trên ledger nội bộ | Đối chiếu với ngân hàng nạp | Đối chiếu với ngân hàng rút |
| **Hoàn tiền** | Ghi có thẳng vào ví | Hoàn về ví (thuộc quyền quản lý ví) | Hoàn về ngân hàng — cần ngân hàng xác nhận |

Quy tắc bắt buộc: agent phải xác định đúng ô trước khi đề xuất hướng xử lý. Chưa xác định được → tiếp tục điều tra hoặc báo "chưa đủ căn cứ", không đoán.

---

## 4. Ma trận thẩm quyền (Permission Matrix) — đã sửa

Thẩm quyền quyết định **luôn luôn** là sếp, không phụ thuộc phạm vi giao dịch. Phạm vi giao dịch chỉ quyết định sếp duyệt xong thì thực thi trực tiếp hay phải chờ ngân hàng xác nhận.

| Hành động | AI Agent | CSKH | Sếp |
|---|---|---|---|
| Xem trạng thái/lịch sử giao dịch | ✅ | ✅ | ✅ |
| Điều tra, trình bày bằng chứng | ✅ (không kết luận) | ✅ | ✅ |
| Đề xuất hướng xử lý kèm căn cứ | ✅ | ✅ | ✅ |
| Tạo yêu cầu tra soát sang ngân hàng đối tác | ✅ (soạn, không gửi) | ✅ gửi | ✅ |
| **Quyết định** hoàn tiền/điều chỉnh ví | ❌ luôn luôn | ❌ luôn luôn | ✅ luôn luôn |
| **Kết luận** có gian lận hay không | ❌ không bao giờ | ❌ không bao giờ | ✅ hoặc chuyển cơ quan chức năng |
| Nhận kết quả điều tra đầu tiên từ AI | — | ✅ luôn luôn, mọi case | ❌ không bao giờ nhận trực tiếp từ AI |

---

## 5. Bộ tín hiệu gian lận (12 tín hiệu, kích hoạt 2 tầng)

Tín hiệu là **điều kiện định tuyến** (chuyển người xử lý), không phải bằng chứng phạm tội — agent không bao giờ kết luận gian lận.

| Nhóm | Tín hiệu |
|---|---|
| Trên giao dịch bị khiếu nại | FS-01 hoàn về đích khác nguồn gốc · FS-02 nguồn lạ + đòi hoàn <24h · FS-03 chuỗi tăng dần ≥3 lần cùng người nhận · FS-04 lệch ≥10× p95 lịch sử · FS-05 người nhận mới + ≥10tr + ngoài giờ |
| Trên hành vi tài khoản | FS-06 rút ≥90% số dư sau bất thường xác thực · FS-07 nhận từ ≥5 nguồn rồi rút ngay · FS-08 KYC mức 0 + ≥20tr/ngày · FS-12 bên nhận đã bị gắn cờ/bị ≥3 khách tố |
| Trong lời kể của khách | FS-09 khớp 6 nhóm từ khoá kịch bản lừa đảo · FS-10 khách khai đã đưa OTP/mật khẩu |
| Chiều ngược lại | FS-11 trục lợi chính sách hoàn tiền (≥3 lần được duyệt trong 90 ngày) |

**Chính sách 2 tầng:**
- **Tầng A** (FS-01, 06, 07, 10, 12) — chỉ cần 1 tín hiệu là escalate ngay, ưu tiên tối cao.
- **Tầng B** (7 tín hiệu còn lại) — cần ≥2 tín hiệu cùng bật mới escalate; 1 tín hiệu đơn lẻ chỉ ghi lại cho CSKH thấy khi mở ticket.

Gắn cờ **không** tự động khoá ví — hai hành động độc lập, tách biệt hoàn toàn (một dương tính giả không được phép làm khách hàng lương thiện mất quyền dùng tiền của chính họ).

Ngưỡng cụ thể của từng tín hiệu là giả định thiết kế, chưa được doanh nghiệp xác nhận (trừ FS-05/FS-08 đã đối chiếu được với Quyết định 2345/QĐ-NHNN — xem Brief §7).

---

## 6. Luồng nghiệp vụ (Agent Workflow)

```
[1] Khách đăng nhập → chọn vai trò
[2] Mở phiên khiếu nại → Xác thực danh tính (OTP phiên làm việc + câu hỏi bảo mật)
[3] Khách mô tả vấn đề bằng ngôn ngữ tự nhiên
[4] Agent gọi tool: lookup_transaction()
      - Không tìm thấy → hỏi lại tối đa N lần → tạo ticket "cần tra thủ công"
[5] Agent điều tra đa bước:
      - Đối chiếu trạng thái, timeline, log liên quan
      - Xác định phạm vi giao dịch (nội bộ / từ ngân hàng / ra ngân hàng)
      - Xác định loại khiếu nại (1 trong 4 nhóm)
      - Chấm bộ 12 tín hiệu gian lận theo chính sách 2 tầng
[6] Agent trình bày kết luận + đề xuất (trích dẫn tool result cho mọi số liệu)
[7] CSKH tiếp nhận — LUÔN LUÔN, không có ngoại lệ kể cả case Tầng A khẩn cấp
      - Xem đầy đủ investigation trail
      - Không có quyền tự duyệt — chỉ "trình sếp" hoặc "yêu cầu điều tra thêm"
[8] Sếp phê duyệt — quyết định cuối cùng cho MỌI case
      - Nội bộ ví: duyệt xong → thực thi trực tiếp
      - Chạm ngân hàng: duyệt xong → CSKH gửi yêu cầu tra soát, chờ đối tác xác nhận
      - Nghi gian lận: duyệt hướng xử lý hoặc chuyển cơ quan chức năng
[9] Trả kết quả cho khách → đóng ticket hoặc chuyển trạng thái theo dõi
```

---

## 7. Yêu cầu chức năng — đối chiếu US

| # | Yêu cầu | US liên quan |
|---|---|---|
| F1 | Đăng nhập, phân quyền 3 vai trò | US-001 |
| F2 | Xác thực danh tính trước thao tác nhạy cảm | US-006 |
| F3 | Agent chat tiếp nhận mô tả khiếu nại | US-003, US-009 |
| F4 | Tool tra cứu giao dịch mô phỏng | US-003, US-008 |
| F5 | Phân loại khiếu nại + phạm vi giao dịch | US-003 |
| F6 | Tạo ticket khiếu nại | US-003, US-011 |
| F7 | Dashboard CSKH xem hàng chờ ticket | US-011 |
| F8 | Điều tra đa bước có log lập luận | US-004 |
| F9 | Đề xuất hoàn tiền + HITL phê duyệt | US-005, US-012 |
| F10 | Memory hội thoại & lịch sử khách | US-010 |
| F11 | Escalation thông minh 2 tầng | US-014 |
| F12 | Xử lý lỗi không tìm thấy giao dịch | US-008 |
| F13 | Cảnh báo ngoài thẩm quyền | US-015 |
| F14 | Tra soát ngân hàng & xử lý quá hạn SLA | US-013 |
| F15 | Bảo vệ PDPA | US-016 |
| F16 | Ghi log HITL | US-017 |
| F17 | Báo cáo vận hành | US-018 |

---

## 8. Tool Specifications (mô phỏng)

| Tool | Input | Output | Ràng buộc |
|---|---|---|---|
| `lookup_transaction` | SĐT / mã GD / thời gian / số tiền | Trạng thái, số tiền, thời gian, phạm vi (3 giá trị), 2 bên liên quan (che theo PDPA) | Không có kết quả → `not_found`, không tự suy diễn |
| `get_customer_history` | user_id | Danh sách khiếu nại trước đó | Chỉ trả về của chính khách đang xác thực |
| `score_fraud_signals` | transaction_id, customer_history | 12 tín hiệu FS-01…FS-12 (bật/tắt) + tầng kích hoạt | Không tự kết luận gian lận, chỉ trả tín hiệu |
| `create_ticket` | transaction_id, loại, phạm vi, ưu tiên, log | ticket_id | Bắt buộc có transaction_id hợp lệ, trừ case không tìm thấy GD |
| `propose_resolution` | ticket_id, phương án, căn cứ | resolution_draft (chờ duyệt) | Không có hiệu lực cho tới khi sếp duyệt |
| `escalate_ticket` | ticket_id, đích escalate, lý do | escalation_id | Bắt buộc kèm lý do; log ai/khi nào |

---

## 9. Data Model — theo dataset thật (`data/generated/`, seed 20260802)

| Bảng | Số bản ghi | Ghi chú |
|---|---|---|
| users | 206 | 200 khách · 4 CSKH · 2 supervisor |
| wallets / bank_accounts | 200 / 245 | Có trạng thái đóng băng/đã đóng |
| transactions | 60.000 | 104 ngày, phạm vi 3 giá trị |
| transaction_events | 215.944 | Timeline liên tục cho từng giao dịch |
| complaints / tickets | 600 / 600 | ~1,0% tổng giao dịch |
| auth_sessions | 303 | Gồm phiên khoá & thất bại OTP (US-006) |

**Bộ case có nhãn:** 180 case (120 dev / 60 held-out) — mỗi case mang khối `expected` (đáp án đúng) và `forbidden` (hành vi bị cấm), dùng làm assertion tự động khi test agent. Chi tiết đầy đủ về phương pháp, kiểm định, và hạn chế đã biết: xem `FIN05-Data-Brief.md`.

---

## 10. Yêu cầu phi chức năng

- **Chống bịa số liệu**: mọi câu trả lời có số tiền/trạng thái phải trích dẫn được tool result — test case riêng để verify.
- **PDPA**: không hiển thị thông tin định danh đầy đủ của bên thứ ba.
- **Audit trail**: mọi hành động HITL phải log ai, khi nào, dựa trên căn cứ gì (US-017).
- **Độ trễ**: phản hồi agent đủ nhanh để demo mượt (không yêu cầu SLA production thật).

---

## 11. Error Handling & Edge Cases

| Tình huống | Xử lý |
|---|---|
| Không tìm thấy giao dịch | Hỏi lại có kiểm soát (tối đa N lần) → ticket "cần tra thủ công" |
| Mô tả mơ hồ / khách tự chẩn đoán sai loại | Hỏi lại làm rõ, phân loại theo dữ liệu tool chứ không theo lời khách |
| Case có dấu hiệu gian lận | Không đề xuất số tiền, gắn cờ theo tầng, CSKH tiếp nhận trước khi escalate |
| Ngân hàng đối tác quá hạn SLA | Ticket "quá hạn chờ đối tác", cảnh báo CSKH |
| CSKH cố duyệt case | Hệ thống chặn — CSKH không có quyền duyệt bất kỳ case nào |

---

## 12. Tiêu chí nghiệm thu cho demo

- [ ] Chạy đủ 4 loại khiếu nại × 3 phạm vi giao dịch với case mẫu mỗi ô
- [ ] Có case "không tìm thấy giao dịch" chứng minh agent không bịa
- [ ] Có case HITL đầy đủ: AI đề xuất → CSKH tiếp nhận → sếp duyệt → cập nhật trạng thái
- [ ] Có case escalate "ngân hàng đối tác" và case escalate nghi gian lận (qua đúng CSKH trước)
- [ ] Toàn bộ investigation trail hiển thị được cho CSKH xem lại
- [ ] Không có trường hợp nào AI hoặc CSKH tự thực thi thay đổi số dư
- [ ] Chạy được tối thiểu các case trong `eval/golden_set.jsonl`, đối chiếu đúng `expected`/`forbidden`

---

## 13. Ngoài phạm vi

Xem Brief §5. Nhấn mạnh: không kết nối core banking/NAPAS thật, không xác thực sinh trắc học thật, không xử lý report cơ quan nhà nước.

---

## 14. Câu hỏi mở còn lại

Danh sách đầy đủ và ưu tiên: xem `FIN05-Data-Brief.md` §7. Tóm tắt các câu quan trọng nhất:
- Ngưỡng thật của từng tín hiệu gian lận FS-01…FS-12
- Số tầng thẩm quyền thật của một ví điện tử
- Tỉ lệ khiếu nại thật trên tổng giao dịch, và độ lệch theo phạm vi giao dịch
- Ngưỡng N lần hỏi lại trước khi coi là không tìm thấy giao dịch (đề xuất hiện tại N = 2)

---

## 15. Định vị cạnh tranh & Nguyên tắc thiết kế

Ngân hàng/ví điện tử hiện có xu hướng dùng nền tảng CSKH chuyên nghiệp lâu năm (ví dụ Zendesk) — nhiều dữ liệu và kinh nghiệm vận hành hơn một sản phẩm build trong 6 tuần có thể có. Sản phẩm này không cạnh tranh trực diện trên trục "nền tảng CSKH tổng quát", mà định vị theo 3 trục chuyên biệt cho ví điện tử (xem thêm Brief §3).

### 15.1 Bảo mật dữ liệu chuyên biệt cho ví điện tử
- Dữ liệu giao dịch không rời khỏi hạ tầng do ví kiểm soát — khác với mô hình SaaS CSKH tổng quát nơi dữ liệu khách hàng được xử lý trên hạ tầng bên thứ ba.
- US-016 (PDPA) và US-017 (audit log) là lợi thế cạnh tranh, không chỉ là yêu cầu tuân thủ tối thiểu — nên nhấn mạnh khi trình bày với đối tác/mentor.
- Cân nhắc cho v2 (ngoài phạm vi demo hiện tại): mã hoá at-rest cho dữ liệu giao dịch, cam kết không dùng dữ liệu khách hàng để huấn luyện lại mô hình.

### 15.2 Giọng văn & ứng xử — nguyên tắc giao tiếp của agent
Bot phải mềm dẻo, xoa dịu được khách hàng đang lo lắng vì mất tiền — không robotic, không rập khuôn kịch bản chung của nền tảng CSKH đa ngành.
- Luôn xác nhận cảm xúc/tình huống của khách trước khi đưa dữ kiện (ví dụ: "Mình hiểu bạn đang lo vì chưa thấy tiền về — để mình tra ngay giúp bạn" thay vì đi thẳng vào bảng trạng thái).
- Không dùng thuật ngữ nghiệp vụ khi nói với khách hàng (giữ các từ như "tra soát", "đối soát" cho phần hiển thị nội bộ CSKH).
- Không hứa hẹn mơ hồ ("sẽ xử lý sớm") — ưu tiên mốc thời gian cụ thể lấy từ dữ liệu thật.
- **Giới hạn cứng**: agent được phép mềm mại trong CÁCH nói, không được mềm mại trong SỰ THẬT nói ra — nguyên tắc chống bịa số liệu (§10) luôn ưu tiên cao hơn nguyên tắc xoa dịu.
- Đề xuất bổ sung tiêu chí nghiệm thu định tính (§12): chạy thử kịch bản khách hàng bức xúc, đánh giá agent có xoa dịu được trước khi cung cấp thông tin hay không.

### 15.3 Chi phí vận hành mô hình AI
- Chi phí trung bình mỗi hội thoại là yếu tố quyết định ví điện tử có động lực dùng thử hay không — cần thấp hơn đáng kể so với chi phí nhân sự CSKH truyền thống hoặc phí nền tảng SaaS tổng quát.
- Cân nhắc kiến trúc phân tầng mô hình: dùng mô hình rẻ/nhanh cho các bước tra cứu và phân loại đơn giản, chỉ dùng mô hình mạnh hơn cho bước điều tra phức tạp hoặc case mơ hồ.
- Bổ sung theo dõi: chi phí token trung bình/ticket như một chỉ số trong báo cáo vận hành (US-018).

Ba nguyên tắc trên không thay thế các ràng buộc bắt buộc ở Brief §7 — bổ sung tiêu chí định vị/cạnh tranh cho toàn bộ quá trình thiết kế và pitch.
