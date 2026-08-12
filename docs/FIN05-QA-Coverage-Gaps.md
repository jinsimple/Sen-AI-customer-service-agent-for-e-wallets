# FIN-05 — Bản đồ khoảng trống kiểm thử (để bàn giao QA/QC)

> Mục đích: liệt kê MỌI tính năng hiện có mà **chưa có test tự động**, hoặc
> có test nhưng **chưa đủ sâu/chưa đủ tin cậy** — để Claude QA/QC bổ sung.
> Rút trực tiếp từ khảo sát code + test suite thật tại thời điểm viết
> (2026-08-12), không suy đoán. Đi kèm 3 tài liệu đã có, đọc trước khi bổ
> sung test để không làm trùng:
> - `docs/TESTING.md` — mô tả ĐẦY ĐỦ những gì ĐÃ có (đừng viết lại).
> - `docs/FIN05-Feature-Inventory-Security-Review.md` — kiểm kê toàn bộ
>   tính năng (không chỉ bảo mật).
> - `docs/FIN05-StressTest-Plan-v2.md` + mục "v2 bổ sung" trong
>   `docs/TESTING.md` — gap-analysis riêng cho khía cạnh BẢO MẬT (đã xử lý
>   xong đợt trước, tóm tắt lại ở §1 dưới đây, không lặp lại chi tiết).

---

## 0. Quy ước đọc bảng dưới

- **Trạng thái:**
  - 🔴 **KHÔNG CÓ TEST** — chưa có bất kỳ test tự động nào chạm tới.
  - 🟡 **CÓ TEST NÔNG** — có test nhưng chỉ kiểm bề mặt (vd. "route trả 200"),
    không kiểm đúng logic/số liệu/edge case.
  - 🟠 **THIẾU TẦNG** — có test ở 1 tầng (vd unit) nhưng thiếu tầng khác
    (vd integration/e2e) cho CÙNG tính năng.
  - ✅ **ĐÃ ĐỦ** — liệt kê để QA biết KHÔNG cần làm lại, tránh trùng công sức.
- Mỗi dòng có file/route cụ thể — không viết test cho thứ chưa xác nhận tồn tại.

---

## 1. Bảo mật — đã xử lý riêng, chỉ tóm tắt (KHÔNG làm lại ở đây)

Đợt trước (2026-08-11/12) đã làm gap-analysis + bổ sung test bảo mật đầy đủ.
Xem chi tiết ở `docs/TESTING.md` mục "v2 bổ sung". Tóm tắt phần **còn tồn
đọng, QA có thể tiếp tục**:

| Việc còn mở | Trạng thái | Việc cần làm |
|---|---|---|
| `security_answer_hash` SHA-256 không salt | 🔴 test đỏ có chủ đích, chờ quyết định vá | Không phải việc QA — chờ PO quyết định thuật toán, QA chỉ giữ nguyên test đỏ |
| PII thô trong live-chat không bị che | 🔴 test đỏ có chủ đích | nt |
| Rate-limit `/auth/login` theo IP dùng chung | 🔴 test đỏ có chủ đích | nt |
| JWT không có revocation | 🔴 test đỏ có chủ đích | nt |
| IDOR ở `POST /tools/lookup_transaction` (khách lạ tra được giao dịch người khác qua route REST, không qua AI) | 🟠 có test `xfail`, CHƯA xin duyệt chặn CI | QA có thể đề xuất PO nâng thành `security_finding` (chặn CI) nếu đồng ý mức rủi ro |
| `InvestigationLog` — chỉ tầng `ToolResult` được test, tầng `InvestigationLog` (node LangGraph riêng) CHƯA có test nào chạm tới | 🔴 KHÔNG CÓ TEST | Cần 1 eval case thật (gọi LLM) hoặc mock LangGraph state đủ trung thực — xem `tests/test_agents/test_audit_trail_completeness.py` docstring, đã ghi rõ giới hạn này |
| B-09 anti-hallucination (số liệu agent nói ra phải truy về đúng `ToolResult`) | 🟡 chỉ kiểm gián tiếp qua golden_set "thiếu trích dẫn = Blocker" | Chưa có test đối chiếu TRỰC TIẾP số liệu trong câu trả lời text với DB |
| B-07 clarify-loop (agent dừng hỏi đúng sau `CLARIFY_QUESTION_MAX_ROUNDS`) | 🟡 chỉ test WIRING (prompt chứa đúng số), KHÔNG test hành vi LLM thật | Cần 1 eval case multi-turn gọi OpenAI thật |
| B-14 REST-vs-AI parity cho các tool còn lại (`propose_resolution`, `escalate_ticket`, `create_ticket`) | 🔴 mới verify `lookup_transaction`/`get_customer_history`, 3 tool còn lại CHƯA đối chiếu | Lặp lại cách làm ở `tests/test_api/test_tools_rest_parity.py` cho 3 route còn lại |

---

## 2. Backend — nghiệp vụ ngoài phạm vi bảo mật

| Tính năng | File | Trạng thái | Ghi chú |
|---|---|---|---|
| Tính SLA (`compute_sla_due_at`, `add_business_days`) | `src/tools/sla.py` | 🔴 KHÔNG CÓ TEST trực tiếp | Chỉ được chạm GIÁN TIẾP qua test tạo ticket (không kiểm tra số ngày/giờ tính RA có đúng không) — cần test riêng: 4 ngày làm việc bỏ qua cuối tuần đúng cách, 30 ngày/48h/7 ngày làm việc cho từng loại, case tạo ticket đúng NGAY trước/sau nửa đêm |
| Báo cáo tổng hợp (`build_summary`) | `src/services/reporting.py` | 🟡 CÓ TEST NÔNG | `test_authz_matrix.py` chỉ kiểm route trả 200 (`safe_success_check=True`), KHÔNG kiểm số liệu tính ra có đúng không (vd tổng số ticket theo trạng thái, SLA quá hạn) |
| `POST /tools/escalate_ticket` (qua HTTP, không phải gọi hàm trực tiếp) | `src/api/main.py` | 🟠 THIẾU TẦNG | `tests/test_tools/test_escalate_ticket.py` chỉ test hàm Python trực tiếp; chưa có test gọi qua HTTP thật (giống cách `test_resolution_approval.py` đã làm cho `/resolutions/{id}/approve`) |
| Alembic migration (`upgrade head` / `downgrade`) | `migrations/versions/*.py` | 🔴 KHÔNG CÓ TEST | Chỉ được verify TAY (chạy `alembic upgrade`/`downgrade` thủ công lúc build tính năng) — không có test tự động chạy trong CI xác nhận MỌI migration áp được sạch lên DB rỗng, và downgrade không mất dữ liệu/lỗi FK |
| `request-more-info` — state machine ticket | `src/api/main.py::request_more_info` | 🟡 CÓ TEST NÔNG | Chỉ có authz test (role gate), chưa test transition trạng thái hợp lệ/không hợp lệ (C-07 trong stress-test-v2, chưa làm) |
| Chuyển ca live-chat (`transfer_session`) qua nút bấm thủ công của CSKH | `src/services/live_chat.py` | 🔴 KHÔNG CÓ TEST | Hàm có sẵn, nhưng KHÔNG có route REST nào gọi nó (chỉ auto-trigger qua `release_staff_sessions` khi disconnect) — nếu có ý định thêm nút "Chuyển ca" thủ công ở UI, cần test cho cả route lẫn UI |

---

## 3. Live-chat — tính năng vừa xây dựng nhiều nhất, rủi ro cao nhất nếu thiếu test

Backend WS/REST đã có 20+ test (`tests/test_api/test_live_chat_ws.py`,
`tests/test_services/test_live_chat.py`) — khá vững. Nhưng toàn bộ phần
**frontend + trải nghiệm 2 người dùng thật cùng lúc** chưa có bất kỳ test
tự động nào — mọi bug tìm được trong quá trình xây tính năng này (tin nhắn
lặp, khung chat tách rời, session mồ côi, dashboard không cập nhật realtime...)
đều do **người dùng tự tay phát hiện qua test thủ công**, không phải CI bắt
được.

| Tính năng | Trạng thái | Ghi chú |
|---|---|---|
| Toàn bộ `frontend/src/components/LiveChatPanel.tsx` | 🔴 KHÔNG CÓ TEST | Không unit test (không có Jest/Vitest/Testing Library trong dự án — xem §5), không e2e |
| Toàn bộ `frontend/src/lib/useLiveChatSocket.ts` (hook quản lý WebSocket) | 🔴 KHÔNG CÓ TEST | Logic reconnect, dedupe, status derive — chưa test |
| Luồng 2 người dùng thật: khách mở chat → CSKH nhận ca → nhắn qua lại → đóng phiên → CSAT | 🔴 KHÔNG CÓ TEST E2E | Đây LÀ tính năng cốt lõi nhất vừa xây — cần Playwright 2 `BrowserContext` (1 khách, 1 CSKH) chạy song song, xem `frontend/e2e/auth.spec.ts` làm mẫu cấu trúc |
| `beforeunload` cảnh báo khi đang chat | 🔴 KHÔNG CÓ TEST | Playwright hỗ trợ được (`page.on('dialog')`) — chưa viết |
| Input-reset-key (chữ sót lại sau khi gửi) | 🔴 KHÔNG CÓ TEST | Nguyên nhân gốc CHƯA xác định chính xác (chỉ vá triệu chứng bằng remount) — nếu muốn test, cần trước tiên xác định lại root cause |
| CSAT phía khách hàng | 🔴 **TÍNH NĂNG CHƯA TỒN TẠI**, không phải chỉ thiếu test | `ChatClient.tsx` (trang `/chat`) — grep `csat`/`CSAT` ra 0 kết quả. `LiveChatPanel.tsx` (dùng cho CSKH) CÓ UI đánh sao, nhưng phía khách hàng (đã merge vào ChatClient.tsx, không dùng LiveChatPanel nữa — xem lịch sử refactor 2026-08-11) chưa từng được nối lại UI đánh giá sau khi chat kết thúc. Cần QUYẾT ĐỊNH sản phẩm trước (có làm không), rồi mới viết test |
| Dashboard CSKH cập nhật real-time khi có khách mới vào hàng chờ | 🔴 KHÔNG CÓ TEST | `dashboard/page.tsx` có WS riêng lắng nghe `queue_update` — logic đã sửa 1 lần vì thiếu (phát hiện qua test tay), chưa có test tự động bảo vệ khỏi tái phát |
| Sweep phiên rác (`sweep_stale_waiting_sessions`) chạy đúng nhịp khi CSKH thật load trang nhiều lần/phút | 🟡 CÓ TEST NÔNG | Có test logic (đóng đúng phiên cũ, không đóng phiên đang kết nối) nhưng chưa có test tần suất gọi thực tế/hiệu năng khi hàng nghìn phiên tồn đọng |
| Restart backend giữa lúc có live-chat đang mở | 🔴 KHÔNG CÓ TEST | Chỉ verify được qua `docker compose` thật (đã ghi trong `docs/TESTING.md`), chưa có script tự động hoá bước restart + assert |

---

## 4. AI Agent — hành vi hội thoại (ngoài phần đã liệt kê ở §1)

| Tính năng | Trạng thái | Ghi chú |
|---|---|---|
| Giọng văn/đồng cảm (FAIR-002 và tương tự) | 🟡 CÓ TEST NÔNG | `eval/llm_judge_set.jsonl` mới 7 case — ít so với độ rộng của yêu cầu "giọng văn kiên nhẫn, không phân biệt đối xử" |
| Multi-turn quên ngữ cảnh (khách nhắc lại thông tin đã cho ở lượt trước, agent có nhớ không) | 🔴 KHÔNG CÓ TEST | Chưa có case nào kiểm tra agent KHÔNG hỏi lại thông tin đã có trong `MemorySaver` cùng thread |
| Giới hạn `_AGENT_RECURSION_LIMIT` — số cụ thể | 🟡 CÓ TEST NÔNG | Có test agent xử lý được `GraphRecursionError` (graceful), nhưng chưa test đúng NGƯỠNG cụ thể là bao nhiêu vòng thì kích hoạt |
| `search_policy` trả về 0 kết quả (RAG rỗng/câu hỏi ngoài phạm vi tài liệu đã upload) | 🔴 KHÔNG CÓ TEST | Chưa xác nhận agent phản hồi thế nào khi RAG không có gì liên quan — có bịa không |
| Đổi ngôn ngữ giữa chừng (khách hỏi bằng tiếng Anh) | 🔴 KHÔNG CÓ TEST | Ngoài phạm vi ban đầu nhưng đáng để QA xác nhận hành vi thực tế (từ chối lịch sự hay cố trả lời sai) |

---

## 5. Frontend — thiếu hẳn 1 tầng kiểm thử

**Phát hiện hạ tầng quan trọng nhất mục này:** `frontend/package.json`
KHÔNG có bất kỳ test runner nào (không Jest, không Vitest, không Testing
Library) — chỉ có `"lint": "eslint"`. Toàn bộ kiểm thử frontend hiện tại
CHỈ có **Playwright E2E** (4 file: `auth.spec.ts`, `login.spec.ts`,
`transparency.spec.ts`, `accessibility.spec.ts`) — nghĩa là **không có tầng
unit/component test nào cho logic React thuần** (parsing, state machine,
hàm helper) — mọi bug logic chỉ bắt được khi chạy được cả trình duyệt.

### 5.1. Trang/component hoàn toàn chưa có test tự động nào chạm tới

| Trang/Component | Route | Việc chính chưa test |
|---|---|---|
| `dashboard/page.tsx` | `/dashboard` | Filter/search ticket, badge khẩn cấp, widget hàng chờ live-chat (xem §3) |
| `tickets/[id]/TicketDetailClient.tsx` | `/tickets/[id]` | Hiển thị đầy đủ investigation log, resolution, panel live-chat theo role |
| `approve/page.tsx` | `/approve` | Luồng duyệt/từ chối resolution của supervisor — tính năng HITL cốt lõi, hoàn toàn chưa có e2e |
| `report/page.tsx` | `/report` | Hiển thị số liệu tổng hợp |
| `policy-lookup/page.tsx` | `/policy-lookup` | Tra cứu chính sách thủ công của CSKH |
| `knowledge/page.tsx` | `/knowledge` | Upload/xoá tài liệu RAG qua UI (`partner_admin`) — route backend đã test kỹ, UI thao tác file chưa test |
| `ChatClient.tsx` — nhánh AI (ngoài phần OTP đã có ở `auth.spec.ts`) | `/chat` | Chip chọn loại khiếu nại, rail "Giao dịch gần đây"/"Lịch sử khiếu nại", luồng tạo ticket đầy đủ end-to-end |

### 5.2. Việc nên làm

- Cân nhắc thêm Vitest + React Testing Library cho logic thuần (helper
  functions trong `lib/`, state reducer trong các component phức tạp như
  `ChatClient.tsx`) — rẻ và nhanh hơn Playwright cho loại test này, Playwright
  chỉ nên dành cho luồng thật cần trình duyệt.
- `tsc --noEmit` hiện KHÔNG phải npm script chính thức (`package.json` chỉ
  có `lint`) — dễ quên chạy, nên thêm `"typecheck": "tsc --noEmit"` và gắn
  vào CI (kiểm tra `.github/workflows/ci.yml` xem đã có bước này chưa,
  nếu chỉ chạy tay thì cần thêm vào pipeline).

---

## 6. Kiểm thử tải/chaos — giới hạn đã biết, còn thiếu

| Việc | Trạng thái | Ghi chú |
|---|---|---|
| Load test có live-chat (WS) đồng thời với `/agent/chat` | 🔴 KHÔNG CÓ TEST | `tests/load/locustfile.py` hiện chỉ có HTTP scenario (Locust không hỗ trợ WS sẵn — đã ghi nhận trong `FIN05-StressTest-Plan-v2.md` §10, chưa viết script `websockets` riêng) |
| Soak test 1-2h theo dõi memory leak (`MemorySaver`/`ConnectionManager` giữ RAM) | 🔴 KHÔNG CÓ TEST TỰ ĐỘNG | Có lệnh chạy tay trong `docs/TESTING.md`, chưa có ai thực sự chạy + ghi lại kết quả |
| Chaos: OpenAI timeout | ✅ ĐÃ ĐỦ | `tests/test_services/test_fault_tolerance.py` |
| Chaos: Postgres mất kết nối giữa chừng | 🟡 CÓ TEST NÔNG | Có test lỗi DB mid-transaction (rollback sạch), nhưng chưa test App tự PHỤC HỒI khi DB online lại sau khi mất kết nối thật (connection pool retry) |

---

## 7. Đề xuất thứ tự ưu tiên cho QA/QC

1. **Live-chat e2e 2 người dùng** (§3) — rủi ro cao nhất vì đây là tính năng
   mới nhất, phức tạp nhất, đã có sẵn chuỗi bug thật (lặp tin nhắn, session
   mồ côi, dashboard không cập nhật) từng lọt qua tới tay người dùng thật.
2. **Hạ tầng unit/component test cho frontend** (§5.2) — nền tảng, càng để
   lâu càng khó bổ sung khi code đã lớn thêm.
3. **SLA + reporting** (§2) — logic tính toán số liệu, sai sẽ ảnh hưởng
   trực tiếp quyết định nghiệp vụ (CSKH thấy sai hạn xử lý).
4. **Migration test tự động** (§2) — rẻ để làm (spin DB tạm, chạy
   upgrade/downgrade toàn bộ chuỗi), rủi ro cao nếu bỏ qua (hỏng dữ liệu
   production khi deploy).
5. Phần còn lại theo §1/§4/§6 — đã có test nông, nâng cấp dần không gấp.

---

## 8. Quy ước khi bổ sung test (để nhất quán với suite hiện có)

- Verify mã hoá/masking bằng raw SQL, không tin ORM tự giải mã ngầm (đã là
  quy ước xuyên suốt `docs/TESTING.md`).
- Test P0/finding bảo mật viết ở trạng thái ĐỎ trước, không tự sửa code
  cùng lúc (xem `docs/TESTING.md` mục "v2 bổ sung").
- Playwright e2e mới nên theo cấu trúc `test.describe` gắn ID case
  (`AUTH-*`, `UX-*`...) giống các file hiện có, dễ truy vết ngược về nguồn
  yêu cầu.
- Chạy `pytest tests/ -v` + `ruff check src/ tests/` trước khi coi 1 test
  mới là "xong" — xác nhận không phá test cũ.
