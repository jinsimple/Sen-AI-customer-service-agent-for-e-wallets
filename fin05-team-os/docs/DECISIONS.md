# Nhật ký quyết định (ADR)

> **CHỈ GHI THÊM.** Không sửa, không xoá mục cũ. Quyết định mới đảo ngược quyết định cũ thì ghi
> ADR mới và điền mục "Thay thế" — bản cũ vẫn nằm nguyên đó.
>
> Vì sao: bạn cần biết *tại sao đã từng quyết định ngược lại*. Nếu chỉ giữ kết luận cuối,
> vài tuần nữa sẽ có agent "tối ưu" nó quay về cái sai cũ, vì cái sai đó trông hợp lý hơn.
>
> Ghi bằng `/adr <nội dung>`. Ghi **ngay khi chốt**, đừng để cuối ngày.

---

## ADR-001 — Áp dụng Team-OS: contract làm nguồn sự thật
- **Ngày:** 2026-08-13
- **Bối cảnh:** Làm một mình với nhiều vai Claude. Tech lead đổi cấu trúc, tester và security
  không biết, phải bắt tech lead viết file tóm tắt thủ công — dễ quên, dễ cũ, không kiểm được.
- **Quyết định:** Cấu trúc hệ thống sống trong `contracts/`. Agent bàn giao cho contract, không
  bàn giao cho nhau. `scripts/check_contracts.py` băm contract và đánh dấu artifact lỗi thời.
- **Phương án đã cân nhắc và bác bỏ:**
  - *File tóm tắt thủ công do tech-lead viết* — bác bỏ vì phụ thuộc trí nhớ agent, không có cách
    nào biết tóm tắt đã cũ, và không kiểm được tính đầy đủ.
  - *Một agent duy nhất biết mọi thứ* — bác bỏ vì tỉ lệ tín hiệu/nhiễu trong cửa sổ ngữ cảnh
    giảm mạnh, và mất luôn tính độc lập đối kháng khi kiểm thử.
- **Hệ quả:** Mọi thay đổi cấu trúc phải qua quy trình 6 bước (`CLAUDE.md §3`). Chậm hơn lúc đầu,
  hoà vốn khoảng ngày 3–4.
- **Thay thế:** không
- **Người duyệt:** Bách

## ADR-002 — Sếp duyệt mọi phạm vi, kể cả giao dịch nội bộ ví
- **Ngày:** (điền ngày quyết định gốc)
- **Bối cảnh:** Thiết kế ban đầu cho CSKH tự duyệt case nội bộ ví–ví, vì ví có toàn quyền
  ledger nội bộ và không cần ngân hàng.
- **Quyết định:** Chỉ role `supervisor` được duyệt, cho **mọi** phạm vi giao dịch, không ngoại lệ.
  "Ngoài thẩm quyền" định nghĩa theo role, không theo hạn mức tiền.
- **Phương án đã cân nhắc và bác bỏ:** *CSKH tự duyệt case nội bộ giá trị nhỏ* — bác bỏ vì tạo ra
  một đường đi tài chính không có HITL, và vì ngưỡng tiền là ranh giới trôi được (chia nhỏ giao
  dịch), còn ranh giới role thì không.
  **Lưu ý cho agent tương lai: đề xuất này trông rất hợp lý về UX. Nó đã bị bác bỏ có ý thức.**
- **Hệ quả:** `contracts/authority-matrix.yaml` INV-01…INV-04; `tests/test_invariants.py`
- **Thay thế:** quyết định thiết kế ban đầu (không có ADR)
- **Người duyệt:** Bách

## ADR-003 — AI không vượt cấp: mọi case qua CSKH tiếp nhận trước
- **Ngày:** (điền)
- **Bối cảnh:** Case nghi gian lận khẩn cấp có vẻ nên được đẩy thẳng lên sếp cho nhanh.
- **Quyết định:** Mọi kết quả điều tra của AI, kể cả khẩn cấp, phải qua state `cskh_received`.
  Không tồn tại tool `escalate_len_supervisor`.
- **Phương án đã cân nhắc và bác bỏ:** *Đường ưu tiên cho case tầng A* — bác bỏ vì tạo ra một
  đường đi mà con người đầu tiên nhìn thấy case lại là người có quyền quyết định, xoá mất lớp
  kiểm tra độc lập. Tốc độ giải quyết bằng cách ưu tiên hàng đợi của CSKH, không bằng cách bỏ qua CSKH.
- **Hệ quả:** `contracts/ticket-state-machine.yaml` INV-05, INV-06
- **Thay thế:** không
- **Người duyệt:** Bách

## ADR-004 — Cấm bịa số liệu: thực thi ở tầng hạ tầng, không ở tầng prompt
- **Ngày:** (điền)
- **Bối cảnh:** Prompt "không được bịa số" tuân thủ khoảng 95–99%. Với sản phẩm tài chính,
  con số đó không đủ.
- **Quyết định:** Mọi tool trả về `tool_call_id`. Agent không được render con số không kèm
  `tool_call_id` nguồn. Tool không tìm thấy dữ liệu trả `status='not_found'`, tuyệt đối không
  trả giá trị mặc định 0.
- **Phương án đã cân nhắc và bác bỏ:** *Chỉ dặn trong system prompt* — bác bỏ vì không kiểm chứng
  được và không có cách nào phát hiện khi nó hỏng.
- **Hệ quả:** `contracts/agent-tools.yaml` INV-09, INV-10
- **Thay thế:** không
- **Người duyệt:** Bách

## ADR-005 — Gắn cờ nghi gian lận tách bạch hoàn toàn khỏi khoá ví
- **Ngày:** (điền)
- **Bối cảnh:** Nối cờ gian lận sang khoá ví là cách bảo vệ hệ thống nhanh nhất.
- **Quyết định:** Hai hành động độc lập. Module chấm tín hiệu không được import module khoá ví.
  Khoá ví chỉ `supervisor` được thực hiện.
- **Phương án đã cân nhắc và bác bỏ:** *Tự động khoá khi trúng tín hiệu tầng A* — bác bỏ vì
  dương tính giả làm khách hàng lương thiện mất quyền dùng tiền của chính họ. Chi phí của một
  dương tính giả ở đây cao hơn nhiều so với chi phí chậm vài giờ.
- **Hệ quả:** `contracts/authority-matrix.yaml` INV-07; `tests/test_invariants.py`
- **Thay thế:** không
- **Người duyệt:** Bách

---

> **Còn thiếu:** ADR-002 đến ADR-005 là ghi hồi tố cho các quyết định đã có trong PRD 2.1 §4.
> Hãy điền ngày thật và rà lại phần "phương án đã bác bỏ" — đó là phần có giá trị nhất và cũng
> là phần dễ ghi qua loa nhất. Ngoài ra PRD §4 còn 3 quyết định chưa có ADR
> (xác thực OTP phiên, PDPA che thông tin bên thứ ba, định vị cạnh tranh) — nên bổ sung trong ngày 1.
