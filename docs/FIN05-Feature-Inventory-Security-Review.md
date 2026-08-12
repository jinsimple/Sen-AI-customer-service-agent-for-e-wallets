# FIN-05 — Kiểm kê tính năng phục vụ đánh giá bảo mật

> Mục đích tài liệu: liệt kê đầy đủ, chính xác mọi tính năng/route/luồng dữ
> liệu hiện có của ứng dụng FIN-05 (AI agent xử lý khiếu nại ví điện tử, hợp
> tác ZaloPay), để một reviewer/agent chuyên bảo mật đưa ra tiêu chuẩn bảo
> mật cho từng phần. Rút trực tiếp từ code hiện tại (`src/`, `frontend/`,
> `docker-compose.yml`, `Caddyfile`) tại thời điểm viết — không suy diễn.
>
> Ngày tạo: 2026-08-11. Nếu code thay đổi, tài liệu này cần đối chiếu lại.

---

## 1. Bức tranh tổng quan

FIN-05 là hệ thống xử lý khiếu nại giao dịch cho một ví điện tử, gồm 1 AI
agent (LangGraph + OpenAI) trò chuyện trực tiếp với khách hàng, xác minh giao
dịch, tạo ticket, và một webapp CSKH/supervisor để duyệt/xử lý ticket, cộng
1 tính năng live chat (WebSocket) escalate từ AI sang người thật.

**Kiến trúc triển khai** (`docker-compose.yml`, `Caddyfile`):
- `caddy` — cổng duy nhất ra internet (80/443), reverse-proxy vào `frontend`
  cho mọi path, NGOẠI TRỪ 1 route `/ws/live-chat*` được forward thẳng tới
  `backend` (ngoại lệ có chủ đích, xem §6).
- `frontend` (Next.js) — không publish port ra host, chỉ Caddy gọi được.
  Đóng vai trò BFF (Backend-For-Frontend): mọi gọi tới backend đều qua route
  handler Next.js (`frontend/src/app/api/*/route.ts`), browser không bao giờ
  biết địa chỉ backend thật.
- `backend` (FastAPI, `src/api/main.py`) — không publish port ra host, chỉ
  gọi được qua Docker DNS nội bộ (`backend:8010`). Chạy **đúng 1 uvicorn
  worker** (quyết định có chủ đích — xem `Dockerfile`) vì state hội thoại AI
  (`MemorySaver`, LangGraph) và state live-chat (`ConnectionManager`) đều giữ
  trong RAM 1 process.
- `postgres` — không publish port ra host.
- `jaeger` — UI 16686 chỉ bind `127.0.0.1` (không lộ ra ngoài máy chủ), nhận
  trace từ backend qua OTLP gRPC nội bộ.

**Không có CORS** — cố ý (browser chỉ gọi Next.js cùng-origin, backend không
bao giờ nhận request trực tiếp từ browser trừ WebSocket).

---

## 2. Xác thực & phân quyền

### 2.1 Cơ chế đăng nhập
- `POST /auth/login` (`src/api/main.py:195`, rate-limit `10/minute`) — nhận
  phone + password (hoặc security question tuỳ luồng), trả JWT.
- JWT ký bằng `JWT_SECRET_KEY` (bắt buộc từ env, không có default —
  `src/config.py:85`), thuật toán HS256, hết hạn 8 giờ
  (`JWT_EXPIRE_MINUTES`).
- Frontend lưu JWT trong 1 cookie **httpOnly** (JS trình duyệt không đọc
  được) — `frontend/src/lib/session.ts`. Route `/api/session` phía Next.js
  đọc cookie, gọi backend kèm `Authorization: Bearer`.
- 4 role cố định (CHECK constraint DB, `src/db/models.py:38`):
  `customer`, `cskh`, `supervisor`, `partner_admin`.

### 2.2 OTP (xác thực 2 lớp cho hành động nhạy cảm)
- `POST /auth/otp/request`, `POST /auth/otp/verify` (`src/api/main.py:222,254`,
  cả 2 rate-limit `10/minute`).
- 2 ngưỡng "OTP còn tươi" tách biệt theo mức độ nhạy cảm của hành động
  (`src/config.py:63,69`):
  - `OTP_VIEW_MAX_MINUTES = 12h` — cho hành động XEM/GIAO TIẾP (vd mở live
    chat).
  - `OTP_STEPUP_FRESH_MINUTES = 15 phút` — cho hành động ghi dữ liệu tài
    chính (vd `create_ticket`) — `require_otp_verified`
    (`src/auth.py:144`).
- `OTP_MAX_FAILED_ATTEMPTS = 3` — khoá sau 3 lần sai.

### 2.3 Phân quyền theo route
- `require_role(role)` (`src/auth.py`) — dependency FastAPI gate từng route
  theo đúng 1 hoặc nhiều role.
- `tests/test_api/test_authz_matrix.py` — cơ chế tự đối chiếu **MỌI** route
  đã đăng ký trong `app.routes` với 1 bảng kỳ vọng role — CI tự fail nếu có
  route mới không được khai báo quyền tương ứng. Đây là control quan trọng
  nhất chống "quên gate 1 route mới".
- Đặc biệt: `partner_admin` (đối tác ví điện tử, KHÁC `supervisor` nội bộ)
  là role DUY NHẤT được upload/xoá tài liệu chính sách/FAQ nạp vào RAG —
  đây là actor duy nhất có thể đưa nội dung mới vào thứ agent/CSKH sẽ tin
  tưởng, nên phân quyền chặt hơn các route khác.

---

## 3. AI Agent (trò chuyện với khách hàng)

- `POST /agent/chat` (`src/api/main.py:397`, rate-limit `20/minute`,
  `require_role("customer")`) — điểm vào duy nhất cho khách chat với AI.
- Engine: LangGraph (`src/agents/graph.py`) + OpenAI (`OPENAI_MODEL`,
  mặc định `gpt-4o-mini`, key từ `OPENAI_API_KEY`). State hội thoại giữ
  trong RAM qua `MemorySaver` (per-process, mất khi restart — giới hạn đã
  biết, không phải bug).
- **Function-calling tools** agent được gọi (`src/agents/tools/customer_tools.py`,
  builder `build_customer_tools`, luôn scoped theo đúng `user_id` của khách
  đang chat — không có tool nào nhận `user_id` tự do từ input):
  - `lookup_transaction` — tra cứu giao dịch, ép buộc người hỏi PHẢI là 1
    bên trong giao dịch (`_enforce_requester_is_party`), chặn injection
    trong nội dung trả về từ dữ liệu ngoài (`_contains_injection_signal`),
    khoá theo OTP-fresh qua decorator `_locked`.
  - `get_customer_history` — lịch sử khiếu nại của CHÍNH khách đó.
  - `create_ticket` — tạo ticket khiếu nại, yêu cầu OTP step-up 15 phút
    (hành động ghi dữ liệu).
  - `request_human_handoff` — gắn cờ `human_handoff_requested`, mở luồng
    live-chat (KHÔNG yêu cầu OTP — coi là "định tuyến", không phải hành
    động dữ liệu, xem §6).
  - `search_policy` — tìm trong RAG chính sách/FAQ, kết quả được lọc qua
    `_sanitize_policy_results` trước khi đưa vào ngữ cảnh model.
- Mỗi lượt gọi tool được ghi `ToolResult` + `InvestigationLog`
  (`src/db/models.py:251,263`) — audit trail đầy đủ AI đã tra gì, quyết
  định gì, để CSKH/supervisor xem lại.
- Giới hạn số vòng hỏi làm rõ: `CLARIFY_QUESTION_MAX_ROUNDS = 2` — chống
  agent lặp vô hạn.

Ngoài `/agent/chat`, các tool trên còn có route REST riêng dùng nội bộ bởi
webapp CSKH (không phải do AI gọi):
`POST /tools/lookup_transaction`, `/tools/get_customer_history`,
`/tools/create_ticket`, `/tools/propose_resolution`, `/tools/escalate_ticket`
(`src/api/main.py:325-397`) — mỗi route gate theo role tương ứng qua
`require_role`, đã có trong authz matrix.

---

## 4. Nghiệp vụ ticket / khiếu nại (webapp CSKH + supervisor)

- `GET /tickets`, `GET /tickets/{id}` (`cskh`/`supervisor`) — danh sách +
  chi tiết ticket, kèm `Complaint`, `InvestigationLog`, `ToolResult`,
  `Escalation` liên kết.
- `POST /tickets/{id}/request-more-info` — CSKH yêu cầu khách bổ sung thông
  tin.
- `POST /resolutions/{id}/approve`, `POST /resolutions/{id}/reject`
  (`supervisor` — CHỈ supervisor được duyệt) — nguyên tắc **HITL tuyệt đối**:
  AI/CSKH chỉ được `propose_resolution` (đề xuất), không route nào cho phép
  tự động thực thi hoàn tiền/hành động tài chính mà không qua duyệt người.
  Không có ngoại lệ nào trong toàn bộ codebase (đã audit qua session trước).
- `GET /resolutions` — hàng chờ duyệt của supervisor.
- `GET /reports/summary` — số liệu tổng hợp SLA/loại khiếu nại
  (`src/services/reporting.py`), dùng cho trang `/report`.

**SLA** (`src/tools/sla.py`, `src/config.py:33-39`) — tính hạn xử lý theo
loại khiếu nại (giao dịch ngân hàng: 4 ngày làm việc; khiếu nại chung: 30
ngày; phản hồi đầu tiên: 48h; nghi gian lận: 7 ngày làm việc).

**Fraud policy** (`src/tools/fraud_policy.py`) — `evaluate_escalation`, xác
định tín hiệu gian lận nào cần escalate ngay (ưu tiên `critical`).

**Frontend pages tương ứng**: `/dashboard` (hàng chờ ticket + hàng chờ live
chat), `/tickets/[id]` (chi tiết + panel live chat khi có), `/approve`
(supervisor duyệt resolution), `/report` (số liệu tổng hợp), `/chat`
(khách hàng — AI + live chat gộp chung 1 luồng).

---

## 5. RAG chính sách/FAQ (`src/rag/`)

- `POST /policy-docs` (`partner_admin`, `20/hour`) — upload file (PDF/DOCX/...),
  `MAX_UPLOAD_SIZE_MB = 10`, parse (`src/rag/parsers.py`) → chunk
  (`RAG_CHUNK_SIZE=800`, `RAG_CHUNK_OVERLAP=150`) → embed
  (`text-embedding-3-small`) → lưu Chroma (`data/rag_index/`, không commit
  git) + `PolicyChunk.text` (bản gốc, **mã hoá at-rest** qua `EncryptedText`
  trong Postgres).
- `GET /policy-docs`, `DELETE /policy-docs/{id}` (`partner_admin`).
- `POST /policy-search` — tìm kiếm ngữ nghĩa, dùng bởi cả agent
  (`search_policy` tool) lẫn trang `/policy-lookup` (CSKH tra cứu thủ công).
- `RAG_SEARCH_TOP_K = 4` — số chunk trả về mỗi lần tìm.

---

## 6. Live chat trực tiếp CSKH ↔ khách hàng (WebSocket)

Escalation path từ AI (`request_human_handoff`) lên chat 2 chiều thời gian
thực với người thật — chi tiết đầy đủ nằm ở
`/Users/soidoc/.claude/plans/1-hidden-thompson.md` (đã triển khai, đã test
qua `docker compose` thật). Tóm tắt bề mặt tấn công:

- **Auth WebSocket handshake**: vé dùng-1-lần (ws-ticket), TTL 30s, sinh qua
  `POST /live-chat/ws-ticket` (customer) / `POST /live-chat/staff/ws-ticket`
  (cskh/supervisor) — browser không gắn được `Authorization` header vào
  `new WebSocket(url)`, và JWT thật không bao giờ đi qua query param.
- **Rate limit riêng, khoá theo `user_id`** (không theo IP như hầu hết route
  khác — vì mọi khách gọi qua chung 1 container `frontend`, khoá IP sẽ thành
  khoá chung cho TẤT CẢ khách): mint vé tối đa 5/phút/user, gửi tin nhắn tối
  đa 60/giờ/user (`InMemoryRateLimiter`, `src/api/live_chat_ws.py`).
  **Lưu ý cho reviewer bảo mật**: đặc điểm này (rate-limit theo IP =
  `get_remote_address` của container frontend) áp dụng cho **mọi route
  khác** trong app (kể cả `/auth/login`), không riêng live-chat — là hạn
  chế kiến trúc có sẵn, không phải phát sinh mới.
- **Định tuyến claim-based**: `UPDATE chat_sessions SET claimed_by=:uid
  WHERE claimed_by IS NULL` — atomic, chống 2 CSKH cùng nhận 1 ca (có test
  race-condition).
- **Ngoại lệ routing Caddy duy nhất**: `/ws/live-chat*` forward thẳng
  `backend:8010`, mọi path khác vẫn qua `frontend`. Đây là điểm DUY NHẤT
  browser chạm trực tiếp backend trong toàn bộ hệ thống.
- **Mã hoá at-rest**: `Message.content` qua `EncryptedText` (Fernet,
  `FIELD_ENCRYPTION_KEY` từ env, cùng khoá dùng cho `BankAccount.account_no`
  và `PolicyChunk.text`) — đã verify raw SQL query thấy ciphertext, không
  phải chỉ code claim suông.
- **Disclaimer cố định** gửi khách lúc vào phiên: không bao giờ hỏi mật
  khẩu/OTP giao dịch qua chat.
- **State in-memory, không Redis** — chủ đích, dựa trên constraint uvicorn
  1-worker sẵn có (xem §1). Nếu sau này scale nhiều worker, đây LÀ điểm cần
  đổi thiết kế (thêm Redis pub/sub) — flag rõ cho reviewer.
- **Đã cắt cho v1** (ghi rõ, không phải thiếu sót): typing indicator, read
  receipt, CSAT chỉ 1-5 sao không có bình luận tự do, ETA chờ là heuristic
  thô (đếm số ca chờ/CSKH online).
- **Giới hạn PDPA đã biết**: nếu CSKH/khách gõ tay SĐT/số tài khoản thô vào
  nội dung chat, KHÔNG có cơ chế tự động che (khác với AI, nơi
  `masking.py`/`scrub_pii` áp dụng) — đây là gap đã xác định, cần reviewer
  đánh giá mức rủi ro chấp nhận được.

---

## 7. Bảo vệ dữ liệu (PII / mã hoá / masking)

- **Masking cho bên thứ ba** (`src/tools/masking.py`, nguyên tắc BR-06/BR-07):
  chỉ áp dụng ở TẦNG TOOL/API lúc trả kết quả — DB luôn lưu bản đầy đủ,
  KHÔNG bao giờ lưu sẵn bản đã che (để còn test được logic masking). Che
  SĐT (`090***4567`), tên (`T. H. Trang`), số tài khoản (`**********0001`).
- **Mã hoá at-rest** (`src/db/crypto_types.py`, Fernet qua
  `FIELD_ENCRYPTION_KEY`): `BankAccount.account_no`, `Message.content`
  (live chat), `PolicyChunk.text`.
- **PII scrubbing cho log/trace** (`src/observability/pii.py`) — pipeline
  hybrid 2 lớp: regex tiếng Việt (SĐT/CCCD/email) trước, Presidio+NER
  (`underthesea`) sau cho tên người/địa chỉ tự do; graceful-degrade về
  CHỈ regex nếu Presidio không load được model (không crash app). Chạy
  TRƯỚC khi log/trace rời khỏi hệ thống.
- **Injection defense**: `_contains_injection_signal` (customer_tools.py) —
  chặn nội dung độc hại chèn vào ngữ cảnh model qua dữ liệu tra cứu được
  (transaction, policy search).

---

## 8. Observability (đã triển khai, xem thêm playbook riêng)

- **Structured logging** (`src/observability/logging_config.py`) — JSON,
  ISO 8601 UTC.
- **Distributed tracing** — OpenTelemetry, auto-instrument FastAPI
  (`instrument_fastapi_app`), `BatchSpanProcessor` xuất qua OTLP gRPC tới
  Jaeger nội bộ (UI chỉ bind `127.0.0.1`, không lộ ra ngoài).
- **Context propagation** — `src/observability/context.py`
  (`contextvars`), gắn `correlation_id` 1 lần ở entry point.
- LLM generation span gắn attribute theo GenAI Semantic Conventions chuẩn
  (`gen_ai.system`, `gen_ai.request.model`, token usage) —
  `src/observability/langchain_callback.py`.

---

## 9. Dữ liệu (bảng chính, `src/db/models.py`)

`users`, `wallets`, `bank_accounts`, `transactions`, `transaction_events`,
`complaints`, `tickets`, `tool_results`, `investigation_logs`, `resolutions`,
`escalations`, `auth_sessions`, `chat_sessions`, `messages`,
`policy_documents`, `policy_chunks`.

Toàn bộ FK/CHECK constraint quan trọng (role hợp lệ, status hợp lệ,
csat_score 1-5...) enforce ở TẦNG DB, không chỉ tầng ứng dụng.

---

## 10. Secrets & cấu hình (12-factor)

Tất cả đọc từ biến môi trường, **không có default cho secret** (fail-fast
nếu thiếu — `JWT_SECRET_KEY`, `FIELD_ENCRYPTION_KEY`, `OPENAI_API_KEY`):
`DATABASE_URL`, `OPENAI_API_KEY`, `OPENAI_MODEL`, `JWT_SECRET_KEY`,
`FIELD_ENCRYPTION_KEY`.

---

## 11. Câu hỏi gợi ý cho reviewer bảo mật (không phải kết luận, chỉ để định hướng)

- Rate-limit theo IP container (`get_remote_address`) trên mọi route ngoại
  trừ live-chat — có chấp nhận được ở quy mô hiện tại, hay cần đổi sang
  khoá theo `user_id` toàn bộ?
- JWT 8 giờ, không có refresh token / revocation list — chấp nhận được ở
  mức rủi ro nào?
- `MemorySaver`/`ConnectionManager` in-memory (mất state khi restart, không
  scale >1 worker) — điểm nào cần thiết kế lại trước khi tăng tải?
- Gap PDPA ở live-chat (không tự động che PII gõ tay) — mức ưu tiên vá?
- `security_answer_hash` — xác nhận qua code (`src/api/main.py:277`): so
  khớp bằng SHA-256 **không salt**, không phải thuật toán chuyên cho mật
  khẩu (bcrypt/scrypt/argon2). SHA-256 trần dễ brute-force offline nếu DB
  lộ (câu trả lời bảo mật thường có entropy thấp — tên trường/ngày sinh...).
  Đây là finding cụ thể, không phải suy đoán — cần reviewer đánh giá mức ưu
  tiên vá.
- Toàn bộ upload file (`/policy-docs`) — đã có kiểm tra loại file/nội dung
  độc hại (không chỉ giới hạn dung lượng) chưa?
