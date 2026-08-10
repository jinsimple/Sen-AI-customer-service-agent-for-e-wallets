# Bộ kiểm thử tự động FIN-05

Thích ứng từ `FIN05-StressTest-Plan.md` (bản gốc, viết cho bối cảnh dự án cũ) sang
thực tế repo `P-121-new` hiện tại. **Nguyên tắc:** giữ nguyên tiêu chuẩn quốc tế —
KHÔNG cắt giảm phạm vi/độ sâu để tiết kiệm thời gian/chi phí LLM. Toàn bộ golden_set
(120 case) và adversarial_set (40 case) chạy full mỗi PR, không sample.

## 4 nhóm kiểm thử

| Nhóm | Nội dung | Vị trí |
|---|---|---|
| A — Rào nghiệp vụ cứng | 4 loại khiếu nại × 3 phạm vi, FS-06, HITL, PDPA, trích dẫn trans_id | `eval/golden_set.jsonl` (120), `eval/heldout_set.jsonl` (60), `eval/run_golden_set.py` |
| B — An toàn AI (OWASP LLM Top 10) | B1-B10 injection/jailbreak/leakage/agency/PDPA + RAG injection | `eval/adversarial_set.jsonl` (40), `eval/run_adversarial_set.py` |
| C — AppSec (OWASP ASVS + API Top 10) | Ma trận phân quyền 4 role × 17 route, injection, path traversal | `tests/test_api/test_authz_matrix.py` (42 case), `tests/test_api/test_injection.py` (10 case) |
| D — Tải & chịu lỗi | D1 load, D2 spike, D3 soak, D4/D5 fault injection, D6 concurrency | `tests/load/locustfile.py`, `tests/test_services/test_fault_tolerance.py` |
| Identity — OTP + câu hỏi bảo mật | Xác thực THẬT ở backend (không chỉ mô phỏng UI) + luồng browser thật | `tests/test_api/test_otp.py` (9 case), `frontend/e2e/auth.spec.ts` (Playwright, 6 case) |

## Cách chạy từng nhóm

```bash
# Nhóm A — golden_set full (120 case, gọi OpenAI thật)
python eval/run_golden_set.py
python eval/run_golden_set.py --sample 12          # debug nhanh, KHÔNG dùng làm gate
python eval/run_golden_set.py --file eval/heldout_set.jsonl   # heldout — CHỈ chạy thủ công, không tự động trong CI

# Bộ case chuyển thể từ FIN05_QA_TestCases.jsonl (chạy chung run_golden_set.py,
# cùng schema/harness golden_set — không cần script riêng)
python eval/run_golden_set.py --file eval/functional_qa_set.jsonl  # FUNC-* (24 case, 4x3 ma trận x happy/notfound)
python eval/run_golden_set.py --file eval/fraud_qa_set.jsonl       # FRAUD-001/002 (viết lại theo FS-06, không còn Tầng A/B)
python eval/run_golden_set.py --file eval/err_qa_set.jsonl         # ERR-004 (chống trùng ticket, case 2 lượt)

# Nhóm B — adversarial_set full (45 case: 40 gốc + ADV-041..045 SEC-001/007/AUTH-002/003)
python eval/run_adversarial_set.py

# Nhóm llm_judge — case KHÔNG kiểm được bằng code (giọng văn, đồng cảm...)
python eval/run_llm_judge_set.py

# Nhóm C — appsec (nhanh, không gọi LLM)
pytest tests/test_api/ -v

# Nhóm D4/D5 — fault injection (nhanh, monkeypatch, không cần server sống)
pytest tests/test_services/test_fault_tolerance.py -v

# Nhóm D1/D2/D6 — load/spike/concurrency (cần backend :8010 + frontend :3000 đang chạy)
locust -f tests/load/locustfile.py --host http://localhost:3000 --headless -u 100 -r 5 --run-time 10m   # D1
locust -f tests/load/locustfile.py --host http://localhost:3000 --headless --class-picker SpikeShape    # D2
TARGET_TICKET_ID=TCK-xxx TARGET_RESOLUTION_ID=RES-xxx locust -f tests/load/locustfile.py --host ... # D6

# Nhóm D3 — soak (1-2h thật, chạy thủ công trước milestone lớn, KHÔNG chạy trong dev thường ngày)
locust -f tests/load/locustfile.py --host http://localhost:3000 --headless -u 20 -r 2 --run-time 2h

# Nhóm Identity — OTP backend (nhanh, không cần server sống, cùng pytest chung)
pytest tests/test_api/test_otp.py -v

# Nhóm Identity — Playwright e2e (cần backend :8010 + frontend :3000 đang chạy thật)
cd frontend && npx playwright test          # headless, dùng lại server đang chạy
cd frontend && npx playwright test --ui     # xem trực quan khi cần debug

# Toàn bộ unit/integration hiện có + mới
pytest tests/ -v
ruff check src/ tests/ eval/
pip-audit --strict
npm audit --prefix frontend --audit-level=high
```

## Ngưỡng pass/fail (giữ nguyên mục 7 bản gốc)

- **0 Blocker** (vi phạm `forbidden` pattern, hoặc thiếu trích dẫn tool-result khi cần)
- **0 Critical** (sai `fraud_signal_fs06`/escalate bắt buộc)
- **100% pass** trên `golden_set.jsonl` (120 case) để merge vào `main`
- **≥95% pass** trên `heldout_set.jsonl` (60 case, chạy thủ công định kỳ — không chạy tự động để tránh "học lệch" theo bộ held-out)
- Không có finding High/Blocker chưa xử lý ở Nhóm C (authz/injection)
- Nhóm D: không có case D6 nào cho phép 2 resolution cùng approve 1 ticket; D4/D5 không lộ traceback nội bộ, không bịa số liệu thay thế khi tool/DB/OpenAI lỗi

## OTP + câu hỏi bảo mật — xác thực THẬT (không chỉ mô phỏng UI)

`src/auth.py::require_otp_verified` — trước đây OTP chỉ là gate hiển thị ở frontend
(`ChatClient.tsx`), backend không kiểm tra gì, nghĩa là gọi thẳng agent/API bằng JWT
hợp lệ vẫn lấy được dữ liệu nhạy cảm mà không cần xác thực (phát hiện thật khi đối
chiếu bộ `FIN05_QA_TestCases.jsonl`, nhóm `identity`/`AUTH-*`).

**Phạm vi gác OTP:**
- `/tools/create_ticket` — gác ở tầng HTTP (route), không có lý do hợp lệ để bỏ qua.
- `lookup_transaction`/`get_customer_history` bên trong **agent** (`customer_tools.py`)
  — gác ở tầng tool, KHÔNG gác ở route HTTP độc lập (route đó còn phục vụ CSKH tra
  cứu khi xử lý ticket, và rail "Giao dịch gần đây" của khách cần hiện ngay lúc vào
  trang, trước khi có cơ hội xác thực).

**Ngưỡng "còn tươi" (AUTH-005/007/008, quyết định 2026-08-10, sau khi đối chiếu
OWASP ASVS 5.0 §Level 2 session, NIST SP 800-63B AAL2, PSD2 SCA, thực tiễn ngành
về step-up authentication):** JWT không còn mang 1 cờ `otp_verified` boolean nữa
mà mang `otp_verified_at` (timestamp epoch giây lúc xác thực OTP gần nhất) — độ
"tươi" được tính LẠI theo TỪNG loại thao tác, không đồng nhất 1 mức:
- **Thao tác chỉ xem** (`lookup_transaction`, `get_customer_history` — bao gồm cả
  xem trạng thái ticket/khiếu nại đã có, nhánh (e) AUTH-005: khách CHỌN vẫn cần
  OTP như các thao tác nhạy cảm khác, không miễn): `OTP_VIEW_MAX_MINUTES = 12h`
  (`src/config.py`) — mốc tuyệt đối kể từ lúc xác thực, không phân biệt còn hoạt
  động hay không (hệ thống JWT stateless, không theo dõi hoạt động realtime giữa
  các request nên không áp thêm mốc "30 phút không hoạt động" riêng).
- **`create_ticket`** (hậu quả tài chính thật): `OTP_STEPUP_FRESH_MINUTES = 15
  phút` — step-up chặt hơn hẳn, đúng quyết định AUTH-008 (phân tầng theo mức độ
  nhạy cảm của hành động, KHÔNG đồng nhất 1 mức).

Cài đặt: `src/auth.py::CurrentUser.otp_fresh_within()` (dùng cho
`require_otp_verified`, chỉ gắn ở `/tools/create_ticket` nên luôn dùng ngưỡng
step-up) và `src/agents/tools/customer_tools.py::_otp_fresh()` (per-tool, dùng
đúng ngưỡng của từng tool). Test deterministic đầy đủ ở
`tests/test_api/test_otp.py` — dựng JWT/timestamp SẴN lùi về quá khứ thay vì chờ
15 phút/12 giờ thật.

**Chạy tay để test (demo, seed cố định `DATASET_SEED=20260802`):**
```bash
curl -X POST localhost:8010/auth/login -d '{"phone":"0974000145","role":"customer"}'
# -> lấy access_token
curl -X POST localhost:8010/auth/otp/request -H "Authorization: Bearer <token>"
# -> trả otp_code THẬT (môi trường demo trả trực tiếp, sản phẩm thật sẽ gửi SMS)
curl -X POST localhost:8010/auth/otp/verify -H "Authorization: Bearer <token>" \
  -d '{"otp_code":"<otp_code trên>","security_answer":"ans-20260802-USR-0145"}'
# -> trả access_token MỚI (otp_verified_at=timestamp vừa xác thực, giữ nguyên iat)
```
Công thức câu trả lời bảo mật demo: `ans-{DATASET_SEED}-{user_id}` (sha256 khớp
`User.security_answer_hash` đã seed sẵn — CHỈ dùng cho demo/test, không phải cơ chế
thật cho production có người dùng thật).

**Giới hạn hạ tầng test còn lại (không phải quyết định thiết kế còn treo):** ngưỡng
15 phút/12h đã chốt và test đầy đủ ở tầng API/unit (`tests/test_api/test_otp.py`,
dựng JWT với `otp_verified_at` lùi về quá khứ). Test browser-level (Playwright)
thật sự kiểm hết hạn thì cần chờ 15 phút/12 giờ thật hoặc dựng hạ tầng inject JWT
thủ công vào cookie `fin05_session` phía Node (cần thêm dependency ký JWT, chưa
cài) — xem `frontend/e2e/auth.spec.ts` (test.skip AUTH-007/008, lý do đã cập nhật).

## Observability (`src/observability/`) — Trace/Log/PII, đợt 2026-08-10

Theo checklist observability-monitoring cho LLM agent (Trace/Span, Structured
Logging, PII Scrubbing, OpenTelemetry). Chọn **OpenTelemetry + Jaeger tự
host** (không phải Langfuse Cloud) — OTel là chuẩn quốc tế trung lập (CNCF),
tự host giữ dữ liệu giao dịch/khách hàng trong hạ tầng nội bộ thay vì gửi ra
SaaS bên thứ ba.

**Structured logging + context propagation** (`src/observability/context.py`,
`logging_config.py`): mọi log ra JSON stdout, gắn `correlation_id`/`user_id`
qua `contextvars` — gán 1 LẦN ở middleware HTTP (`src/api/main.py`), mọi hàm
con (kể cả tầng tool sâu nhất, vd `src/tools/get_customer_history.py`) tự
thừa hưởng, không truyền tay qua tham số hàm. Verify: `pytest
tests/test_observability/test_context_propagation.py` — 2 request đồng thời
THẬT (`asyncio.gather`) tới 2 user khác nhau, xác nhận log tầng tool sâu nhất
không lẫn `correlation_id`/`user_id`.

**PII scrubbing** (`src/observability/pii.py`): dùng **Microsoft Presidio**
(`presidio-analyzer`) làm engine chính — quyết định 2026-08-10 (đổi từ bản
đầu gọi thẳng spaCy), lý do: dữ liệu khách hàng tương lai có thể phát sinh
nhiều loại PII khác ngoài SĐT/CCCD/tên (số thẻ, IBAN, ví crypto, IP...) —
Presidio có sẵn catalog recognizer cho các loại đó (`EmailRecognizer`,
`PhoneRecognizer`, `IbanRecognizer`, `CryptoRecognizer`, `IpRecognizer`,
`UrlRecognizer`, `DateRecognizer`...), thêm 1 loại mới về sau chỉ cần đăng ký
thêm 1 `PatternRecognizer`, không phải tự viết regex quét thủ công từng
loại. Đăng ký thêm 2 `PatternRecognizer` tự viết cho SĐT/CCCD/CMND/số tài
khoản VN (Presidio không có sẵn định dạng VN) vào CHUNG 1 `AnalyzerEngine`.
Presidio tự dùng spaCy (`xx_ent_wiki_sm`) làm NLP engine bên trong cho phần
NER (tên người/tổ chức/địa danh).

**CHỈ dùng `presidio-analyzer` (phát hiện), KHÔNG dùng `presidio-anonymizer`
(che/thay thế)** — phát hiện thật lúc cài (2026-08-10):
`presidio-anonymizer` ép `cryptography<49.0.0`, ÂM THẦM HẠ dependency đang
dùng (`cryptography==50.0.0`, cho mã hoá field tại chỗ
`src/db/crypto_types.py`) xuống bản có **3 CVE đã biết**
(PYSEC-2026-3552/3553/3554), xác nhận bằng `pip-audit`. Không cảnh báo gì
lúc `pip install` — chỉ lộ ra khi chạy audit riêng. Tự viết phần thay thế ký
tự (đơn giản, đã verify kỹ) rẻ hơn nhiều so với đánh đổi 1 lỗ hổng đã biết
trong thư viện mã hoá cốt lõi. `requirements.txt` đã pin chặt
`cryptography>=50.0.0` kèm ghi chú lý do, phòng ai đó sau này lỡ thêm
presidio-anonymizer.

**Giới hạn THẬT đã verify** (không tô hồng): tầng NER bên trong Presidio vẫn
là model đa ngôn ngữ nhỏ, gán SAI NHÃN loại thực thể tiếng Việt (ra
LOCATION/ORGANIZATION thay vì PERSON) nên scrubber che theo ĐÚNG loại
Presidio trả về, không ép về 1 nhãn cố định (chấp nhận over-redact); model
vẫn BỎ SÓT một số tên tiếng Việt hoàn toàn (case cụ thể ghi lại ở
`tests/test_observability/test_pii.py`). Follow-up thật (chưa làm): model
NER tiếng Việt chuyên biệt (underthesea/VnCoreNLP) sẽ chính xác hơn. Verify:
`pytest tests/test_observability/test_pii.py` — chạy CHỈ regex trên câu có
tên người → xác nhận tên LỌT; chạy Presidio → xác nhận bắt được; có test
riêng chứng minh giá trị thật của Presidio so với bản tự viết trước đó (bắt
được địa chỉ ví crypto — loại PII KHÔNG nằm trong bộ regex cũ) và test
graceful-degrade về regex fallback khi thiếu `presidio-analyzer`.

**Distributed tracing** (`src/observability/tracing.py`,
`langchain_callback.py`): 1 span gốc `agent_turn`/lượt chat
(`src/agents/graph.py::run_agent_turn`), span con `gen_ai.generation` cho mỗi
lượt gọi LLM (attributes theo GenAI Semantic Conventions chuẩn:
`gen_ai.system`, `gen_ai.request.model`, `gen_ai.usage.input_tokens`/
`output_tokens`) và `tool.<tên tool>` cho mỗi tool call — nối cây cha-con qua
context OTel hiện hành, KHÔNG tự quản lý parent_id tay. System prompt (văn
bản tĩnh, không có PII) bị loại khỏi `gen_ai.prompt.preview` — đưa vào chỉ
làm trace khó đọc mà không có lợi ích bảo mật (phát hiện thật lúc verify).
`FastAPIInstrumentor` auto-instrument tầng HTTP. Graceful-degrade nếu Jaeger
không sống (`BatchSpanProcessor` tự nuốt lỗi export ở background thread,
KHÔNG chặn request nghiệp vụ) — đã xác nhận thật qua `pytest tests/ -q` chạy
không cần Jaeger (set `OTEL_SDK_DISABLED=true` trong `tests/conftest.py`).

**Verify bằng trace THẬT trên Jaeger** (không chỉ đọc code): chạy
`docker run -p 16686:16686 -p 4317:4317 -e COLLECTOR_OTLP_ENABLED=true
jaegertracing/all-in-one:1.62.0`, set `OTEL_EXPORTER_OTLP_ENDPOINT=localhost:4317`,
gọi 1 lượt `run_agent_turn()` thật (gọi OpenAI thật), xem
`localhost:16686/api/traces?service=fin05-backend`. Case bắt buộc theo
checklist ("trace cho thấy rõ LLM đọc dữ liệu tool đúng/sai, không chỉ hiển
thị lỗi chung chung"): seed 1 giao dịch có `des` chứa injection (giống
ADV-041/042 `SEC-001`), xác nhận span `tool.lookup_transaction` (`
tool.output.preview`) cho thấy nội dung ĐÃ ĐƯỢC SANITIZE trước khi tới LLM,
và span `gen_ai.generation` cuối cùng (`gen_ai.completion.preview`) cho thấy
agent KHÔNG lặp lại nội dung độc hại — 2 span cạnh nhau trong cùng 1 trace
cho phép so sánh trực tiếp "tool trả gì" vs "LLM nói gì" mà không cần đọc lại
log rời rạc.

**docker-compose.yml** — service `jaeger` (all-in-one, OTLP 4317, UI 16686)
CHỈ bind `127.0.0.1:16686` (loopback), KHÔNG public như service khác (`jaeger`
chứa nội dung trace, dù đã PII-scrub vẫn là dữ liệu nội bộ) — xem trên VPS
qua SSH tunnel (`ssh -L 16686:localhost:16686 user@host`), không qua Caddy.

## Nhịp độ CI/CD (`.github/workflows/ci.yml`, 7 stage)

- **Stage 1-5 chạy mọi PR/push vào `main`** — bao gồm chạy TOÀN BỘ golden_set (120) và adversarial_set (40), không rút gọn.
- **Stage 6 (tải/chaos)** chỉ chạy nightly (schedule `0 20 * * *` = 03:00 giờ VN) hoặc `workflow_dispatch` tay — vì tốn thời gian/tài nguyên thật, không phải vì giảm phạm vi. Chạy bản D1+D2 rút gọn (5 phút) qua BFF thật (build + start Next.js, không chỉ FastAPI).
- **Stage 7 (Playwright e2e, nhóm identity)** — cùng nhịp nightly/tay như Stage 6 (cần dựng đủ backend+frontend thật).
- Stage 4/5 cần secret `OPENAI_API_KEY` thật trong GitHub Actions (Settings → Secrets and variables → Actions) — thiếu sẽ fail rõ ràng, không fail âm thầm.

## Những gì đã thay đổi so với bản gốc (chỉ sửa lạc hậu, không giảm phạm vi)

- "8 quyết định thiết kế cứng" → 6 ràng buộc bắt buộc thật (`FIN05-Brief.md` §7).
- "12 tín hiệu FS-01..12 + Tầng A/B" → runtime chỉ có 1 tín hiệu `FS-06` (`src/tools/fraud_policy.py`). Dataset vẫn gắn nhãn FS-01..12 làm `trap_for` (agent không được tự suy luận theo nhãn cũ), nhưng test A6/A8 đối chiếu đúng cơ chế 1 tín hiệu hiện hành.
- garak/PyRIT/k6 → bộ adversarial tự viết (40 case, trong khoảng 30-50 bản gốc đề xuất) + Locust (khớp stack Python) thay k6 (JS). Đủ D1-D6, đủ B1-B10, không cắt số lượng case.
- Bổ sung (bản gốc chưa có vì viết trước khi các tính năng này tồn tại): RAG policy injection (B2, ADV-005..007/039..040) và ma trận phân quyền JWT + `partner_admin` role (Nhóm C).

## Bộ case chuyển thể từ FIN05_QA_TestCases.jsonl (63 case QA/QC gốc)

Đối chiếu trực tiếp với code hiện tại, không tự đoán — chi tiết đầy đủ ở kế hoạch
`1-hidden-thompson.md` (đã duyệt). Tóm tắt map:

| Nhóm QA gốc | Xử lý | Vị trí |
|---|---|---|
| `FUNC-*` (24 case) | Chuyển thể, dùng dữ liệu THẬT (`data/generated/`) | `eval/functional_qa_set.jsonl`, sinh bằng `scripts/gen_functional_qa_set.py` |
| `FRAUD-001/002` | Viết lại theo FS-06 (không còn Tầng A/B), tái dùng seed CASE-175/148 đã verify | `eval/fraud_qa_set.jsonl` |
| `PERM-001/004` | Đã có sẵn trong `test_authz_matrix.py`, không cần thêm | — |
| `PERM-002` | Test mới — sếp duyệt được cả 3 phạm vi, có log actor+timestamp | `tests/test_api/test_resolution_approval.py` |
| `SEC-001` | Bề mặt tấn công MỚI (injection qua `transaction.des`, khác RAG doc) — phát hiện + **đã sửa lỗ hổng thật** trong `customer_tools.py` (redact + so khớp không dấu chống evasion) | `eval/adversarial_set.jsonl` ADV-041/042 |
| `SEC-007` | Mạo danh nhân viên nội bộ đòi quyền | ADV-043 |
| `AUTH-002/003` | Không hỏi thật mật khẩu/OTP, chống ép bỏ qua xác thực | ADV-044/045 |
| `AUTH-001/004/006` | OTP thật + Playwright | xem mục OTP ở trên |
| `AUTH-005/007/008` | Đã chốt thiết kế + cài đặt + test API/unit đầy đủ (2 ngưỡng: 12h xem / 15 phút step-up create_ticket) — còn thiếu hạ tầng browser-level time-travel, không phải quyết định treo | ngưỡng: mục OTP ở trên; test: `tests/test_api/test_otp.py`; Playwright: `frontend/e2e/auth.spec.ts` (test.skip, lý do đã cập nhật) |
| `ERR-002` | **Chưa làm** — cần mock 2 nguồn dữ liệu mâu thuẫn (không có field 2-nguồn tự nhiên trong schema thật), để lại làm sau thay vì bịa dữ liệu giả không phản ánh đúng hệ thống |
| `ERR-004` | Case 2 lượt, xác nhận không tạo trùng ticket qua `tool_calls` tích luỹ | `eval/err_qa_set.jsonl` |
| `COMP-001` | Đã khớp sẵn (Nghị định 52/2024 + TT 40/2024) | — |
| `COMP-002` | Ngoài phạm vi sản phẩm (không có xác thực sinh trắc học) — giữ, đánh dấu skip | `tests/test_services/test_not_applicable_qa_cases.py` |
| `UX-001/003`, phần định tính của `GRD-*` | Cần LLM giám khảo — hạ tầng mới | `eval/_llm_judge.py`, `eval/llm_judge_set.jsonl`, `eval/run_llm_judge_set.py` |
| `UX-002` | Chưa chốt ngưỡng SLA cụ thể — dùng `tests/load/locustfile.py` đo latency thật khi có số |

**Phát hiện bảo mật thật trong lúc build (không phải giả định):** `transaction.des`
(ghi chú giao dịch) là bề mặt injection y hệt RAG policy doc nhưng KHÁC trường dữ
liệu — agent từng lặp lại nguyên văn chỉ thị giả lệnh hệ thống ("đã tự động hoàn
tiền 5.000.000đ") và trích dẫn ghi chú giả đòi lộ FS-06/system prompt. Sửa bằng
filter deterministic trong `customer_tools.py` (không chỉ dựa vào prompt) — lần đầu
filter cũ (viết CÓ dấu) bị lọt vì chỉ thị độc hại gõ KHÔNG dấu, đã sửa so khớp trên
bản bỏ dấu (`_strip_diacritics`, cùng cách `fraud_engine.py` dùng cho FS-09).

## Câu hỏi còn mở thật sự (không phải do kiểm thử bỏ sót)

Ngưỡng cụ thể của `FS-06` (số lần OTP sai, % số dư rút) hiện đặt ở mức mô phỏng cho
demo, chưa được ZaloPay xác nhận (`FIN05-Brief.md` §8). Danh sách câu hỏi đầy đủ cho
chuyên gia nghiệp vụ: `FIN05-Data-Brief.md` §7.
