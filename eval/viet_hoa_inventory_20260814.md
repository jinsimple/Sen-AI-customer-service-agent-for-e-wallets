# INVENTORY chuỗi tiếng Anh / kỹ thuật trên UI — 14/08

> Phiên tester · **read-only**, đi hết các màn bằng trình duyệt thật trên stack
> Docker (frontend build 08:53), theo 4 vai: khách `0387000001` · CSKH
> `0353000201` · sếp `0905000205` · đối tác ví `0900000001`.
> Nhãn đề xuất lấy từ `contracts/resolution-state-machine.yaml` (`mo_ta`) khi
> contract có; nhóm **ngoài contract** đánh dấu ⚠ để PO duyệt.
> ID hệ thống (`TXN-`, `TCK-`, `RES-`, `CMP-`, `FS-`) **không tính** — giữ nguyên là đúng.

## Tóm tắt

| Ưu tiên | Số mục | Nhận xét |
|---|---:|---|
| **P1 — khách nhìn thấy** | 4 | Không phải enum, mà là **mã user story + tên công nghệ nội bộ** lộ trên màn khách |
| **P2 — staff nhìn thấy** | 9 | Enum `action_type`/`status`, tiêu đề "Investigation trail", + **1 câu copy SAI SỰ THẬT** |
| **P3 — phụ** | 2 | Định dạng SLA khó đọc |

**Phần lớn UI đã Việt hoá tốt** (dashboard, /approve, /report, /knowledge,
/policy-lookup gần như sạch). Chỗ còn sót tập trung ở **ticket detail** và
**thẻ đề xuất trên /approve**.

---

## P1 — khách hàng nhìn thấy (ưu tiên cao nhất cho pitch)

| # | Màn | Chuỗi đang hiện | Nhãn đề xuất | Ghi chú |
|---|---|---|---|---|
| P1-1 | `/chat` | `CHATBOT KHÁCH HÀNG · US-002, 003, 006, 007, 008, 009, 010` | **bỏ hẳn phần mã US** với vai khách | ⚠ ngoài contract. Mã user story nội bộ không có nghĩa gì với khách, lộ ra trông như bản nháp |
| P1-2 | `/chat` | `AI agent thật (LangGraph + OpenAI) đang chạy — tự tra cứu, phân loại…` | "Trợ lý ảo tra cứu trực tiếp trên dữ liệu giao dịch của bạn — mọi con số đều trích từ kết quả tra cứu thật." | ⚠ ngoài contract. Tên công nghệ (LangGraph/OpenAI) là thông tin nội bộ; PRD §15.2 cấm thuật ngữ kỹ thuật với khách |
| P1-3 | `/chat` (nav) | `Chatbot AI` | "Trò chuyện" hoặc "Hỗ trợ" | ⚠ ngoài contract |
| P1-4 | mọi màn | `DEVELOPMENT · postgresql/fin05` | *giữ nguyên* | **KHÔNG sửa** — đây là EnvBadge có chủ đích (ADR-009), tự ẩn khi `env=production`. Người demo nên biết trước để không bối rối khi nó hiện trên màn chiếu |

## P2 — nhân viên nhìn thấy

| # | Màn | Chuỗi đang hiện | Nhãn đề xuất | Nguồn nhãn |
|---|---|---|---|---|
| P2-1 | ticket detail · /approve | `refund_to_wallet` | **Hoàn tiền về ví** | contract `mo_ta` |
| P2-2 | /approve | `refund_to_bank` | **Hoàn tiền về tài khoản ngân hàng** | contract `mo_ta` |
| P2-3 | (chưa gặp trên UI, cần phủ) | `ledger_adjustment` | **Điều chỉnh sổ cái** | contract `mo_ta` |
| P2-4 | (nt) | `no_action` | **Không hành động (khiếu nại không có cơ sở)** | contract `mo_ta` |
| P2-5 | (nt) | `manual_review` | **Cần người xem xét thủ công thêm** | contract `mo_ta` |
| P2-6 | ticket detail | `approved` (trạng thái đề xuất) | **Sếp đã duyệt** | contract `mo_ta` |
| P2-7 | ticket detail | `success` (trạng thái giao dịch) | **Thành công** | ⚠ ngoài contract — `refunded` → "Đã hoàn tiền", `processing` → "Đang xử lý", `failed` → "Thất bại" |
| P2-8 | ticket detail | `Investigation trail` | **Nhật ký điều tra** | ⚠ ngoài contract. Phụ đề bên dưới đã tiếng Việt sẵn |
| P2-9 | /approve · /report · /chat | `WEBAPP SẾP · US-005, US-017` (và bản CSKH/khách tương ứng) | bỏ phần mã US, giữ nhãn vai | ⚠ ngoài contract |

### 🔴 P2-10 — KHÔNG phải lỗi dịch, mà là câu SAI SỰ THẬT trên UI

Ticket detail, khi ticket chưa có bước điều tra nào, hiện nguyên văn:

> *"Chưa có bước điều tra nào được ghi nhận cho ticket này — **AI agent chưa
> xử lý case này (agent đang được xây, xem FIN05-Backend-Handoff.md §4.2)**."*

Hai vấn đề: (a) **agent đã chạy thật từ lâu** — câu này là copy từ thời chưa
có agent, nói sai về chính sản phẩm; (b) trỏ tên **file tài liệu nội bộ** ra
màn hình nhân viên. Đây là màn sếp sẽ mở trên sân khấu.

**Đề xuất:** *"Ticket này chưa có bước điều tra nào của trợ lý ảo — hồ sơ được
tạo trực tiếp, chưa qua luồng hội thoại."*
Mức: **P2 nhưng nên sửa cùng đợt 1** vì nó nằm ngay trong luồng demo.

## P3 — phụ

| # | Màn | Hiện | Đề xuất |
|---|---|---|---|
| P3-1 | dashboard | `còn 712h44p` (hạn SLA) | Đổi sang ngày khi > 48h: "còn 29 ngày" — 712 giờ bắt người đọc tự chia |
| P3-2 | /approve | Nhật ký HITL hiện căn cứ không dấu do QA nhập (`QA nghiem thu B3 — duyet`) | Không phải lỗi sản phẩm; ghi để PO biết vết QA còn trong log |

---

## 🔴 Phát hiện NGOÀI phạm vi Việt hoá — cùng lớp lỗi vừa vá cho sếp

**CSKH không vào được `/report` dù contract cho phép.**

- Nav của CSKH chỉ có **2 tab**: "Hàng chờ" · "Tra cứu chính sách" — **không có
  "Báo cáo vận hành"** (nav của sếp thì có đủ 3).
- Vào thẳng `https://localhost/report` bằng vai CSKH → **bị đá về `/dashboard`**.
- Trong khi `contracts/authority-matrix.yaml` ghi rõ:
  `GET /reports/summary` → `roles: [cskh, supervisor]`.

⇒ Đúng cùng lớp lỗi với vụ sếp không vào được `/policy-lookup` (đã vá ở
`d0baf35`): **guard route frontend chặt hơn contract**. Không chặn demo tối
nay (kịch bản demo không có bước CSKH xem báo cáo), nhưng nên vá cùng đợt.

---

## Cách nghiệm thu sau khi coder làm

1. Chạy lại đúng crawl này (4 vai × các màn) và đối chiếu từng dòng P1/P2 ở trên.
2. Đối chiếu nhãn với `mo_ta` trong contract — **không nhận nhãn tự sáng tác**
   cho nhóm đã có contract.
3. Xin coder bằng chứng **TypeScript compile sạch** với `Record<T, string>`
   exhaustive (thiếu một giá trị enum là lỗi compile — đó là điểm mạnh của
   cách làm này, phải thấy nó hoạt động).
4. Regression — **có 2 assert sẽ VỠ khi đổi nhãn** (đã rà `frontend/e2e/`):

   | File · dòng | Câu lệnh | Xử lý |
   |---|---|---|
   | `e2e/ticket-detail.spec.ts:52` | `expect(proposedSection).toContainText("refund_to_wallet")` | Đổi sang assert nhãn mới **"Hoàn tiền về ví"** |
   | `e2e/ticket-detail.spec.ts:53` | `expect(proposedSection).toContainText("pending_approval")` | Đổi sang assert nhãn mới của `pending_approval` |

   **KHÔNG đụng** 2 chỗ sau — chúng dùng giá trị enum làm *dữ liệu*, không
   phải text hiển thị, đúng Luật 1 (giá trị giữ tiếng Anh):
   `e2e/ticket-detail.spec.ts:43` (`selectOption("refund_to_wallet")` — value
   của `<option>`) và `e2e/helpers/actors.ts:159` (payload API).

   Tôi sẽ cập nhật 2 assert đó **sau khi coder chốt nhãn** (assert đúng nhãn
   tiếng Việt cuối cùng mạnh hơn là nới lỏng assert bây giờ). Sau đó chạy lại
   D2/D4 + luồng duyệt.

---

# BỔ SUNG 14/08 — test quét ma trận vai × trang (lệnh PO)

Đã viết `tests/test_api/test_frontend_route_guards.py`: đọc thẳng
`contracts/authority-matrix.yaml`, quét **mọi cặp vai × trang** (4 vai × 6
trang = 24 ô), canh **cả hai chiều** — guard hẹp hơn contract (chức năng chết
âm thầm) lẫn guard rộng hơn contract (lỗ hổng phân quyền).

Đo bằng HTTP + cookie, không cần trình duyệt: guard là **redirect 307 phía
server** (đã xác minh). Không tới được stack Docker thì test tự `skip`, không
đỏ giả — CI không có Docker vẫn xanh.

**Ánh xạ trang → route để lộ thiên trong file test** (phần này là suy luận sản
phẩm, không tự suy ra được từ contract, nên đặt chỗ ai cũng thấy để duyệt).
Riêng `/approve` **cố ý** neo vào route DUYỆT (supervisor) chứ không neo vào
`GET /resolutions` (cskh cũng đọc được) — mục đích trang là ra quyết định
chạm tiền, mở cho cskh là mời duyệt vượt quyền (ràng buộc cứng 1).

## Kết quả lần chạy đầu: **22/24 ô xanh · 2 ô đỏ**

| Ô đỏ | Contract nói | Thực tế | Trạng thái |
|---|---|---|---|
| `cskh` × `/report` | `GET /reports/summary` → `[cskh, supervisor]` | 307 → `/dashboard` | Đã biết, PO đã giao coder vá đợt này |
| **`supervisor` × `/dashboard`** | `GET /tickets` → `[cskh, supervisor]` | **307 → `/approve`** | 🔴 **CA THỨ BA — mới, do chính test này bắt** |

Ca thứ ba khớp đúng dự đoán của PO ("hai lần là một pattern"). Nó còn mâu
thuẫn trực tiếp với mô tả vai trong chính contract: *"supervisor kế thừa toàn
bộ quyền của cskh (mọi route cskh đều mở cho supervisor)"*.

**Không chặn demo** — kịch bản demo mới đi `/approve` → "Mở chi tiết →" →
ticket detail, và `/tickets/{id}` với vai sếp vẫn **200** (đã kiểm riêng).

**Cần PO quyết** (test sẽ canh theo quyết định đó): sếp có được mở hàng chờ
CSKH không?
- *Nếu CÓ* (đúng chữ "kế thừa toàn bộ quyền" trong contract) → coder mở guard
  `/dashboard` cho supervisor, test tự xanh.
- *Nếu KHÔNG* (chủ đích: nhà của sếp là `/approve`, tách bạch vai để chống
  xung đột lợi ích — đúng `open_questions` cuối `authority-matrix.yaml`) →
  phải ghi ngoại lệ vào contract, và tôi sửa ánh xạ trong test kèm dẫn nguồn.
  **Không được để nguyên trạng im lặng** — đó chính là cách 2 ca trước lọt.

## Lưu ý vận hành

Cho tới khi 2 ô đỏ được xử lý, `pytest tests/` trên máy có Docker sẽ hiện
thêm 2 đỏ. Đây là **đỏ đúng** (đang tố cáo lỗi thật), cùng tinh thần các test
`security_finding` — không nên "làm cho xanh" bằng cách nới test.
