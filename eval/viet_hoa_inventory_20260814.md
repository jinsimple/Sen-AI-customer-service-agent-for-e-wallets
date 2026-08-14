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

---

# NGHIỆM THU ĐỢT 2 — 14/08, đo trên bản build 16:47

> Điều kiện đo (ghi trước, vì lần đầu tôi suýt báo sai): container frontend
> khởi động **16:23**, commit vá `154b8f9` lúc **16:45** → bản đang chạy khi
> đó CŨ HƠN bản vá. Tôi đã `docker compose up -d --build frontend`, container
> mới khởi động **16:47**, rồi mới đo. Mọi kết quả dưới đây là của bản mới.

## Guard route (bộ quét 24 ô)

| | Trước | Sau |
|---|---|---|
| `cskh` × `/report` | 307 → `/dashboard` | ✅ **200 — đã vá thật** |
| `supervisor` × `/dashboard` | 307 → `/approve` | ❌ **307 → `/approve`, chưa vá** |

**23/24 xanh.** Ca 3 chưa nằm trong đợt này (phán quyết ra lúc 16:43, commit
coder lúc 16:45 — quá sát). Test giữ nguyên ánh xạ theo phương án A, sẽ tự
xanh khi vá.

## Việt hoá — đo bằng trình duyệt thật, 4 vai

| Mục | Kết quả | Chuỗi quan sát được |
|---|---|---|
| P1-1 mã US trên màn khách | ✅ | không còn `US-0xx` |
| P1-2 tên công nghệ | ✅ | không còn `LangGraph`/`OpenAI` |
| **P1-3 "Chatbot AI"** | ✅ **ĐÓNG 14/08** | nav + `<h1>` đã sửa ở `2a72245`. Chỗ thứ 3 tôi báo là **route announcer của Next.js** — `#__next-route-announcer__[role="alert"][aria-live="assertive"]`, do framework chèn nên KHÔNG có trong `frontend/src` (grep của coder đúng), và nó **đọc lại chính `h1`** nên tự khỏi. Kiểm DOM thật trên bản build 22:18: nội dung nay là **"Trợ lý AI"** |
| P2-1 `refund_to_wallet` | ✅ | **"Hoàn tiền về ví"** (khớp `mo_ta`) |
| P2-2 `refund_to_bank` | ✅ | **"Hoàn tiền về tài khoản ngân hàng"** (khớp `mo_ta`) |
| P2-6 `pending_approval` | ✅ | **"Chờ sếp duyệt"** — CÓ nguồn contract (xem đính chính dưới) |
| P2-8 `Investigation trail` | ✅ | **"Nhật ký điều tra"** |
| P2-9 mã US trên màn nhân viên | ✅ | còn `WEBAPP CSKH` / `WEBAPP SẾP` (đúng đề xuất: bỏ mã US, **giữ** nhãn vai), hết `US-005`/`US-017` |
| P3-1 SLA | ✅ | **"còn 29 ngày"** (trước: `còn 712h44p`) |
| **P2-10 câu SAI SỰ THẬT** | ✅ | nay là **"Chưa có bước điều tra nào được ghi cho hồ sơ này."** — hết câu bịa về agent, hết tên file nội bộ (đo trên `TCK-e5b1c615435d`, ticket có trail RỖNG — đúng điều kiện câu cũ xuất hiện) |
| P2-3/4/5 `ledger_adjustment`·`no_action`·`manual_review` | ⏳ **CHƯA ĐO ĐƯỢC** | không có dữ liệu nào trên UI dùng 3 giá trị này |
| P2-7 trạng thái giao dịch | ⏳ **CHƯA ĐO ĐƯỢC** | chỉ gặp trong JSON thô (xem "không phải lỗi") |

## ✅ `pending_approval` = "Chờ sếp duyệt" — ĐÃ DUYỆT, và tôi đã báo cáo SAI

**Đính chính (PO chỉ ra, `14d80fc`):** tôi ghi nhãn này là "coder tự đặt,
ngoài contract". **Sai.** `mo_ta` trong `contracts/resolution-state-machine.yaml`
mở đầu bằng đúng cụm đó:

> `pending_approval: "`**`Đã gửi, chờ sếp duyệt`**`. CỔNG BẮT BUỘC trước mọi hành động tiền."`

Nhãn ngắn là **mệnh đề đầu của `mo_ta`** — có nguồn hẳn hoi. Lỗi của tôi là
chỉ tìm nhãn ngắn dạng nguyên khối, thấy `mo_ta` là câu dài thì kết luận
"không có nguồn", thay vì đọc chính câu đó. Cùng loại sai với việc đo trên
container cũ: kết luận đúng quy trình nhưng dựa trên một phép tra thiếu.

**Mapping phải ghi nguồn như sau** (để đợt sau không ai lại tưởng là tự đặt):
`pending_approval` → "Chờ sếp duyệt" — *nguồn: `resolution-state-machine.yaml`,
mệnh đề đầu của `mo_ta`*.

## KHÔNG phải lỗi — 3 chuỗi tiếng Anh tôi CỐ Ý không báo

Bộ lọc của tôi bắt `rejected` · `refunded` · `success` còn trên màn. Soi ngữ
cảnh thì cả ba đều **đúng khi để nguyên**:

- `rejected`/`refunded` nằm **bên trong JSON kết quả tool thô** ở Nhật ký điều
  tra — **Luật 4 của brief cấm dịch chỗ này**, vì đó là bằng chứng chống bịa
  số liệu (ràng buộc cứng 3). Dịch nó đi là phá chính cơ chế truy vết.
- `success` trên `/approve` nằm trong **căn cứ do CHÍNH TÔI gõ** khi nghiệm thu
  đợt trước (`"QA e2e: ... status success ..."`) — vết dữ liệu test, không phải
  copy sản phẩm. Cùng loại với P3-2.

Ghi lại đây để đợt sau không có ai "sửa" nhầm ba chỗ này.

## 🔴 Phát hiện mới — khuyết tật của chính bộ e2e (không phải lỗi sản phẩm)

`e2e/helpers/actors.ts::createTicketAsCustomerViaAI` chờ thẳng `.txn-item`
ngay sau `loginAs`. Nhưng rail "Giao dịch gần đây" **chỉ hiện danh sách khi
phiên còn OTP tươi** (ngưỡng XEM 12h, AUTH-005/007/008); phiên nguội thì rail
hiện *"Xác thực OTP để xem giao dịch gần đây"* + nút *"Xác thực ngay"*, và
`.txn-item` **không bao giờ render**.

Nghĩa là 2 test `ticket-detail.spec.ts` (và mọi test dùng helper này) **chỉ
xanh khi vô tình còn OTP hợp lệ sót lại từ lượt chạy trước** — chạy nguội trên
máy sạch hoặc trên CI là đỏ, mà **không phải lỗi sản phẩm**. Đây là loại test
tệ nhất: nó phụ thuộc trạng thái sót lại, nên vừa bỏ lọt lỗi thật vừa đỏ giả.

**Đã sửa trong vùng của tôi**: thêm `unlockTxnRail()` — thấy nút "Xác thực
ngay" thì bấm + hoàn tất OTP rồi mới chờ rail, không thấy thì đi tiếp. Cố ý
**không** nuốt lỗi: xác thực xong mà rail vẫn không hiện thì đỏ, vì lúc đó là
lỗi sản phẩm thật.

**Điều PO cần biết cho kịch bản demo:** khách đăng nhập lần đầu **không thấy
ngay danh sách giao dịch** — phải qua OTP. Người demo cần biết trước bước này.

## Kết quả chạy test — nói thẳng cái nào xanh, cái nào chưa

**Backend, sau toàn bộ thay đổi hôm nay:**
`pytest tests/ -m "not security_finding"` → **343 passed · 1 failed · 3 skipped
· 2 xfailed** (125s). Đúng một đỏ: ô `supervisor × /dashboard` — đỏ đúng, đang
chờ coder vá. **Không có hồi quy nào.**

**e2e `ticket-detail.spec.ts`: VẪN ĐỎ — và tôi KHÔNG nới test để nó xanh.**

Đã sửa được 2 lớp nguyên nhân thật (xem trên: phụ thuộc OTP sót lại; và lỗi
ngân sách thời gian do chính bản sửa của tôi gây ra). Lớp thứ 3 thì **không
sửa bằng cách vá test được**, vì nó là câu hỏi sản phẩm:

- Trần thời gian 150s nằm ở chính spec (`ticket-detail.spec.ts:15`), không
  phải config. **Tôi cố ý không nới nó**: nới trần để test xanh chính là việc
  tôi vừa dặn người khác đừng làm ở 2 ô guard.
- Thời gian bị đốt vào việc agent **không tạo ticket** cho giao dịch
  `processing` (ca B2), buộc helper phải nudge 2 lượt LLM nữa.
- Cách vá đúng — cho helper **chọn có chủ đích** một giao dịch phù hợp thay vì
  lấy bừa cái đầu rail — hiện **không làm được từ phía client**: rail chỉ hiện
  chiều tiền/số tiền/thời gian/mã giao dịch, **không hiện trạng thái**, và
  không có route API nào cho khách đọc danh sách giao dịch (đã thử 5 đường,
  đều 404).

⇒ **Chặn ở phán quyết B2.** Chi tiết + hai nhánh xử lý: xem
`eval/results/trige_29_case_20260814.md`, mục "BỔ SUNG 14/08 (chiều)".

**Về 2 assert nhãn tôi đã cập nhật:** chúng **chưa được chính lượt e2e xác
nhận** (test chết trước khi tới đó). Nhưng chuỗi nhãn thì **đã kiểm trực tiếp
bằng trình duyệt** trên `TCK-ddd78e22867f`, khối "Đề xuất đã trình" hiện đúng:
*"Hoàn tiền về ví — 107.000đ"* và *"Chờ sếp duyệt"*. Nói rõ mức độ bằng chứng
để không ai hiểu nhầm là đã chạy xanh.
