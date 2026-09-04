# Finding — Lưới an toàn chuyển người: chưa bắt được bức xúc mạnh ở LƯỢT ĐẦU tiên

> Vai: `security`. Nguồn: QA đo T1-T5 (test escalation-safety-net), báo qua Lead. PO đã đánh giá:
> **KHÔNG chặn quay đêm nay, xếp BACKLOG trước đợt 150 người thật, cố ý CHƯA tuning ngưỡng ngay
> (rủi ro over-escalate, giữ T5 làm đối chứng âm).** Việc của tôi: ghi hồ sơ + thêm khung ràng buộc
> kiến trúc cho lần vá sau, không tự vá/tự đo lại (QA đã đo, có bằng chứng ticket thật).

## Bằng chứng QA (relay, chưa tự đo lại — QA đã có ticket_id thật, không cần đo trùng)

| Ca | Kịch bản | Kết quả |
|---|---|---|
| T2 | Bức xúc RÕ RÀNG ở **một lượt đơn** ("các bạn làm ăn kiểu gì... tôi không tin cái máy này nữa!") | 🔴 KHÔNG tự chuyển — AI chỉ xin lỗi bằng lời, tiếp tục tra cứu |
| T3 | Bức xúc leo thang **≥3 lượt** | ✅ Tự chuyển ở lượt 3 — `TCK-1b08a60e075c` |
| T4 | Khách nói thẳng "muốn gặp nhân viên" | ✅ Chuyển đúng ngay |
| T5 | (đối chứng âm — không nêu chi tiết ở đây, QA giữ làm mốc chống over-escalate) | Không tự chuyển — ĐÚNG kỳ vọng |

**Khoảng trống:** hệ chỉ chắc chắn chuyển người khi bức xúc TÍCH LŨY ≥3 lượt hoặc khách nói thẳng —
chưa có đường bắt tín hiệu bức xúc **mạnh, tức thời, ngay lượt đầu**.

## Phân loại — đây là gap trải nghiệm/an toàn khách hàng, không phải lỗ hổng bảo mật cổ điển

Đúng như PO đã nêu khung: không có dữ liệu bị lộ, không có route bị bypass, không vi phạm 1-trong-5
ràng buộc cứng theo nghĩa đen. Nhưng chạm tinh thần **CTRL-001 (ISO/IEC 25059 "user controllability")**
— nguyên tắc đứng sau `request_human_handoff` — và ảnh hưởng trực tiếp trải nghiệm nhóm khách dễ tổn
thương nhất (đang bức xúc, có thể đang gặp khó khăn tài chính thật, đúng nhóm rủi ro ADR-057 vừa định
danh bằng dữ liệu 31/08).

## 🔴 Ràng buộc kiến trúc BẮT BUỘC cho lần vá sau — nêu ra TRƯỚC khi ai bắt tay code, tránh thiết kế sai hướng

**Đây là điểm giá trị nhất tôi thêm vào finding này, không chỉ chép lại số của QA.**

`CLAUDE.md §2` mục 2 — **Ràng buộc cứng #2: AI KHÔNG VƯỢT CẤP** — và `docs/DECISIONS.md` ADR-057
(01/09, PO duyệt) đã viết THẲNG, chữ in hoa, cho ĐÚNG loại quyết định này:

> ❌ **CẤM:** dạy agent tự quyết chuyển chuyên viên khi "thấy ca khó". Đó là **AI tự escalate** —
> phạm thẳng ràng buộc cứng, và sẽ đỏ ở `tests/test_invariants.py` đúng như thiết kế.
>
> ✅ **ĐÚNG:** quy tắc **tất định** ở tầng SERVICE, máy đọc được, không cần mô hình hợp tác.

**Áp trực tiếp vào ca T2:** cách vá SAI là "prompt cho LLM tự nhận biết giọng điệu bức xúc rồi tự
quyết gọi `request_human_handoff`" — nghe hợp lý, nhưng đó chính xác là **AI tự phán đoán mức độ khó
của tình huống rồi tự hành động** — cùng họ với "AI thấy khó thì bỏ cuộc" mà ADR-057 cấm tường minh.
Route hợp lệ DUY NHẤT: một **tín hiệu tất định** ở tầng service (vd một bộ nhận diện từ khoá/cường độ
cảm xúc CHẠY TRƯỚC khi vào LLM — cùng kiến trúc với `_sanitize_policy_results`/lọc O1-O4: **guardrail
tất định, độc lập với model**, không phải "hỏi LLM có nên chuyển không"), tầng service đọc tín hiệu
đó và QUYẾT ĐỊNH, AI chỉ thực thi khi tầng service đã bật cờ — **giống hệt khuôn `evaluate_escalation`
(`src/tools/fraud_policy.py`) đã dùng cho tín hiệu gian lận**, không phải phát minh cơ chế mới.

**Vì sao T4 (khách nói thẳng) KHÔNG vi phạm ràng buộc này dù có vẻ giống:** T4 là AI **thực thi yêu
cầu TƯỜNG MINH của khách** (đúng CTRL-001, user controllability — khách chủ động chọn) — khác về BẢN
CHẤT với AI tự phán đoán cảm xúc rồi tự quyết thay khách. T3 (≥3 lượt) hiện đang hoạt động — **cần
xác nhận LẠI cơ chế đứng sau T3 có phải quy tắc tất định (đếm số lượt/từ khoá ở service) hay đang
là LLM tự judge nhiều lượt** — nếu là cách thứ hai, T3 đang hoạt động ĐÚNG bằng MAY MẮN chứ không
phải bằng THIẾT KẾ đúng, và cùng cần xem lại khi vá T2 (không nằm trong phạm vi đo của QA lần này,
nêu ra như câu hỏi cần xác nhận, không phải kết luận).

## Liên hệ ADR-057 — hai trục khác nhau, cần PHỐI HỢP không PHẢI TRÙNG LẶP khi thiết kế

ADR-057 (chuyển người sớm) là quy tắc theo **LOẠI KHIẾU NẠI + SỐ LƯỢT CHƯA XÁC ĐỊNH ĐƯỢC GIAO DỊCH**
(`refund`/`wrong_recipient`, N lượt). Ca T2 là trục **CƯỜNG ĐỘ CẢM XÚC**, độc lập — một khách bức xúc
mạnh có thể đang khiếu nại LOẠI BẤT KỲ, kể cả loại "dễ" (`money_not_received` đạt 38,1%). Hai trục
này nên CÙNG đổ vào một cơ chế chuyển người dùng chung (không phải hai đường triển khai riêng biệt
chồng chéo) — khi PO/tech-lead thiết kế vá T2, nên đọc ADR-057 trước để tận dụng đúng hạ tầng "tầng
service quyết định" đã dựng cho trục kia, không xây một cơ chế song song.

## Không tự đề xuất ngưỡng/từ khoá cụ thể ở đây

Đúng quyết định PO ("cố ý CHƯA tuning ngay, rủi ro over-escalate") — tôi KHÔNG đề xuất một bộ từ khoá
hay ngưỡng cường độ cụ thể trong hồ sơ này, vì đó chính là việc PO đã nói rõ chưa muốn làm ngay, và
tôi không có dữ liệu đo (QA có dữ liệu T1-T5, tôi chỉ relay + đóng khung kiến trúc). Khi tới lúc làm,
áp dụng đúng phương pháp dự án đã dùng cho các ngưỡng khác (đo phân bố trên dữ liệu thật trước, không
đoán) — xem cách ADR-057 tự đo tỉ lệ đạt 180 ca trước khi chọn N làm mẫu.

## Backlog — không cấp bách, ghi để không mất

- Trước đợt 150 người thật: quyết cơ chế tất định cho tín hiệu bức xúc lượt-đơn (phối hợp với ADR-057).
- Xác nhận lại cơ chế T3 hiện tại có tất định hay đang là LLM tự judge (câu hỏi mở, chưa đo).
- Khi thiết kế: bắt buộc đọc `CLAUDE.md §2` mục 2 + ADR-057 trước, tránh lặp lại đúng anti-pattern đã
  bị cấm tường minh — đây là lý do chính tôi viết hồ sơ này thay vì chỉ note một dòng trong STATE.md.
