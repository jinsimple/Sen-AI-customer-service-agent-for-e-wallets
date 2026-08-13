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

## ADR-009 — Môi trường phải TỰ KHAI BÁO, không suy từ số cổng

- **Ngày:** 2026-08-13 · **Trạng thái:** Đang hiệu lực
- **Bối cảnh — sự cố thật, mất nhiều giờ điều tra:** Docker stack (Caddy `:80` →
  Postgres) và stack dev cục bộ (`next dev :3000` → `uvicorn :8010` → SQLite) chạy song
  song. PO mở cửa sổ khách ở `localhost` và cửa sổ CSKH ở `localhost:3000`. Hai giao diện
  **giống hệt nhau** nhưng là hai hệ thống với hai database khác nhau: khách tạo ticket
  `TCK-6657099ba1b6` vào Postgres, CSKH đọc từ SQLite nên vĩnh viễn thấy 0 ticket, F5 bao
  nhiêu lần cũng vô ích. Đã báo cáo thành bug P0 (BUGREPRO-001) trong khi **mọi tầng code
  đều đúng**.
- **Quyết định:** hệ thống phải tự khai báo danh tính môi trường ở nơi người dùng nhìn
  thấy, không bắt suy luận từ số cổng trên thanh địa chỉ.
  1. `GET /health` trả thêm `env` / `db_kind` / `db_name`.
  2. Nhãn môi trường (`EnvBadge`) hiện ở topbar **mọi trang** và ở **màn đăng nhập** —
     tự ẩn khi `env === "production"`.
  3. `scripts/preflight.sh` cảnh báo khi phát hiện 2 stack; nối vào `npm run dev`.
- **Lý do:** ba lớp phòng thủ ở ba thời điểm khác nhau — *trước khi chạy* (preflight),
  *lúc đăng nhập* (badge ở /login), *trong lúc dùng* (badge ở topbar). Một lớp hỏng vẫn
  còn hai lớp. Riêng badge là lớp quan trọng nhất vì nó bắt được **mọi biến thể** của lỗi
  này: gõ nhầm cổng, tab cũ còn mở từ stack trước, hai người test trên hai máy khác nhau.
- **Lý do BÁC BỎ phương án khác:**
  - *Chặn cứng không cho chạy 2 stack:* đôi khi chạy song song là chủ đích (so sánh hành
    vi, test migration). Chặn cứng sẽ bị vô hiệu hoá bằng cách khác, và ta mất luôn cảnh
    báo. Cảnh báo + bắt xác nhận giữ được tính có-ý-thức mà không cản trở.
  - *Đổi cổng dev sang số khác cho đỡ nhầm:* không giải quyết gốc — vẫn là hai stack vô
    hình, chỉ đổi con số dễ nhầm này lấy con số dễ nhầm khác.
  - *Chỉ ghi vào README:* tài liệu không xuất hiện đúng lúc mắc lỗi. Nhãn thì có.
- **Bảo mật:** `db_kind`/`db_name` chỉ là scheme + tên database, **không** có host/user/
  mật khẩu — `/health` là endpoint công khai. Đã kiểm bằng test với URL Postgres có
  credential thật.
- **Hệ quả:** `src/config.py::_db_identity`, `src/api/main.py::health`,
  `frontend/src/components/EnvBadge.tsx`, `frontend/src/app/api/env-info/route.ts`,
  `scripts/preflight.sh`, `frontend/package.json` (`dev` chạy preflight trước;
  `dev:force` để bỏ qua khi cố ý).

## ADR-010 — Không dữ liệu định danh nào của khách rời hệ thống lên LLM

- **Ngày:** 2026-08-13 · **Trạng thái:** Đang hiệu lực
- **Bối cảnh:** Rà soát phát hiện họ tên thật + số điện thoại của khách đi thẳng vào
  payload gửi OpenAI, không qua bước che nào. `src/observability/pii.py` (regex +
  Presidio + underthesea) đã có sẵn nhưng **chỉ chạy cho log**, không chạm prompt.
  Chạm OWASP **LLM02:2025 Sensitive Information Disclosure** (nhảy từ #6 lên #2 bảng
  2025) và **NĐ 13/2023 Điều 25** — gọi OpenAI API chính là chuyển dữ liệu cá nhân
  công dân VN ra nước ngoài.
- **Quyết định:** chặn ở **cả hai đầu**, đúng khuyến nghị chuẩn ngành fintech 2026
  (gate input lẫn output, không chỉ output):
  1. Bỏ hẳn `customer_name` khỏi system prompt — agent xưng "quý khách".
  2. `_scrub_pii_cho_llm()` che `full_name`/`phone`/`account_no` ở mọi kết quả tool.
  3. `scrub_pii()` áp lên tin nhắn khách **tự gõ** trước khi vào `HumanMessage`.
- **Lý do vá ở lớp wrapper agent, KHÔNG vá `src/tools/lookup_transaction.py`:**
  `_party_info` cố ý trả PII nguyên văn cho chính chủ — **đúng** cho đường CSKH gọi
  REST (nhân viên nội bộ, dữ liệu không rời hệ thống). Chỉ đường agent mới cần chặn.
  Cùng pattern đã dùng cho lỗ hổng ATLAS-001: chặn đúng đường cần chặn, không hạ cấp
  đường còn lại.
- **Lý do BÁC BỎ "che sạch cho an toàn":** che quá tay thì agent mất mã giao dịch/số
  tiền và hết tra cứu được — tệ hơn không che, vì khách không được giải quyết mà PII
  vẫn có thể lọt chỗ khác. Đo thật cho thấy phải cắt gọn span NER (`_cat_gon_dai_tu`):
  NER gán "tôi bị" → PERSON, che nguyên cụm làm câu mất chủ ngữ. Có test đối trọng
  canh chiều này.
- **Hệ quả:** `src/agents/prompt.py`, `src/agents/tools/customer_tools.py`,
  `src/agents/graph.py`, `src/observability/pii.py`,
  `tests/test_security/test_pii_khong_ro_ri_len_llm.py` (11 test).
- **Giới hạn — nói rõ để không hiểu nhầm:** đây là **masking** (che một chiều), KHÔNG
  phải **tokenization** (thay bằng token hoàn nguyên được qua vault). Với đường LLM thì
  masking đúng — agent không cần hoàn nguyên tên khách. Nghiệp vụ nào sau này cần hiển
  thị lại giá trị gốc thì phải nâng lên tokenization thật.
- **VẪN CÒN dữ liệu rời hệ thống:** số tiền, mã giao dịch, thời gian, nội dung khách
  gõ. Đó là thứ agent buộc phải có để làm việc. Bản vá thu hẹp phạm vi, **không** xoá
  bỏ nghĩa vụ hồ sơ pháp lý — xem ADR-011.

## ADR-011 — Hoãn hồ sơ pháp lý chuyển dữ liệu, KÈM MỐC KÍCH HOẠT

- **Ngày:** 2026-08-13 · **Trạng thái:** Đang hiệu lực · **Người quyết:** PO
- **Bối cảnh:** ADR-010 thu hẹp nhưng không xoá việc dữ liệu rời hệ thống. Chuẩn ngành
  yêu cầu: DPA + Zero Data Retention với nhà cung cấp (tài liệu ngành gọi ZDR là "tiêu
  chuẩn vàng"), sổ đăng ký nhà cung cấp ICT (DORA Điều 28), và Hồ sơ đánh giá tác động
  chuyển dữ liệu ra nước ngoài (NĐ 13/2023 Mẫu 06, gửi A05 Bộ Công an trong 60 ngày).
- **Quyết định:** HOÃN hồ sơ Mẫu 06, ZDR và sổ đăng ký ICT. Vẫn LÀM ngay: ký DPA với
  OpenAI (5 phút, và đang gửi dữ liệu thật qua API rồi), scrub PII hai đầu (ADR-010),
  thông báo demo ở màn hình chat.
- **Lý do:** dự án chạy trên dữ liệu seed tổng hợp (`data/generated/users.jsonl`), chưa
  xử lý dữ liệu cá nhân của khách hàng thật → đồng hồ 60 ngày chưa chạy. ZDR cần thoả
  thuận doanh nghiệp, không hợp giai đoạn demo (tài khoản hiện là Personal, hạn mức $20).
- **Rủi ro tồn dư đã nhận diện:** 150 người test là **người thật gõ chữ thật**. Dù tài
  khoản là seed giả, một bạn gõ "mình là Bách, sđt 09..." thì đó là PII thật của chính
  bạn đó. Vì hoãn hồ sơ nên scrub đầu vào (ADR-010) trở thành **lớp bảo vệ duy nhất**
  — quan trọng hơn, không phải bớt đi.
- **MỐC KÍCH HOẠT — hoãn hết hiệu lực NGAY khi một trong các điều sau xảy ra:**
  1. Có người dùng thật với dữ liệu tài chính thật.
  2. Kết nối vào hệ thống ví thật, kể cả môi trường staging của đối tác.
  3. Đưa sản phẩm cho ZaloPay hoặc ví khác dùng thử với dữ liệu của họ.
  Khi đó Mẫu 06 + ZDR + sổ đăng ký ICT chuyển thành **bắt buộc trước khi chạy**.
- **Lý do BÁC BỎ "làm đầy đủ ngay từ bây giờ":** hồ sơ Mẫu 06 cần pháp nhân và người
  chịu trách nhiệm; ZDR cần thoả thuận doanh nghiệp. Làm sớm trên một demo chưa có dữ
  liệu thật là tốn công vào thứ sẽ phải làm lại khi pháp nhân/phạm vi thay đổi.
- **Lý do ADR này tồn tại:** "demo mà, không cần" là câu rất dễ nói lại ở phiên sau khi
  bối cảnh ĐÃ ĐỔI mà không ai để ý. Mốc kích hoạt ở trên là thứ chặn vòng lặp đó.

## ADR-012 — Chặn ĐỒNG THỜI cho /agent/chat, không xếp hàng chờ

- **Ngày:** 2026-08-13 · **Trạng thái:** Đang hiệu lực
- **Bối cảnh:** `@limiter.limit("20/minute")` không chặn được 150 người cùng bấm gửi
  trong 1 giây — mỗi người chỉ gọi đúng 1 lần, không ai vượt rate limit.
- **Quyết định:** `RedisConcurrencyLimiter` đếm tác vụ ĐANG CHẠY (khác rate limit đếm
  tần suất). Hết slot → `503` + `Retry-After` + thông báo tiếng Việt.
  `AGENT_MAX_CONCURRENT=20`.
- **Lý do dùng Redis, không dùng biến in-process:** hạn mức TPM của OpenAI là hạn mức
  TOÀN CỤC cho cả tài khoản. Đếm trong RAM từng worker sẽ nhân hạn mức lên theo số
  worker — 4 worker là vượt trần gấp 4 mà worker nào cũng tưởng mình đúng luật.
- **Lý do BÁC BỎ "xếp hàng chờ":** giữ request nằm chờ trong worker chính là thứ gây
  nghẽn dây chuyền. Trả lời "đang bận, thử lại" ngay tốt hơn cho cả người dùng lẫn
  hệ thống — hỏng có kiểm soát thay vì hỏng hỗn loạn.
- **Hệ quả:** TTL 90s (2× timeout 45s) làm lưới an toàn thu hồi slot của process chết
  giữa chừng; không có TTL thì hệ thống tự khoá vĩnh viễn với 0 request đang chạy.

## ADR-013 — DATABASE_URL bắt buộc, bỏ fallback SQLite im lặng

- **Ngày:** 2026-08-13 · **Trạng thái:** Đang hiệu lực
- **Bối cảnh:** `os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")` làm Docker
  chạy Postgres còn mọi thứ trên host âm thầm rơi về SQLite → hệ thống tách đôi
  database, mất nhiều giờ điều tra (xem ADR-009).
- **Quyết định:** thiếu biến thì chết ngay lúc khởi động. Postgres publish
  `127.0.0.1:5432` để script trên host nối được đúng DB app đang dùng.
- **Tinh chỉnh bất biến bảo mật, KHÔNG nới lỏng:** test cũ cấm postgres publish port.
  Ý định của nó là "chỉ Caddy là cửa ra internet" — bind loopback không phải cửa ra
  internet, và cùng file đã có tiền lệ Jaeger. Luật mới CHẶT HƠN: backend/frontend
  vẫn cấm tuyệt đối, postgres bắt buộc bind `127.0.0.1`, ra `0.0.0.0` là ĐỎ.
- **Phát hiện kèm theo:** test `test_authz_matrix[GET /live-chat/sessions/waiting]`
  trước đây PASS VÌ LÝ DO SAI — đang đọc `data/app.db` THẬT qua `SessionLocal`
  module-level. Bỏ fallback làm nó lộ ra.

## ADR-014 — MemorySaver → PostgresSaver: state ra khỏi RAM process

- **Ngày:** 2026-08-13 · **Trạng thái:** Đang hiệu lực
- **Bối cảnh:** `MemorySaver` giữ hội thoại trong RAM một process ⇒ backend bắt buộc
  1 worker (máy 10 vCPU dùng được 1), và restart = mọi khách mất sạch ngữ cảnh.
- **Quyết định:** `PostgresSaver` với pool RIÊNG (`CHECKPOINT_POOL_MAX=5`), tách khỏi
  pool SQLAlchemy vì hai thứ có nhịp truy cập khác nhau, gộp chung sẽ nghẽn lẫn nhau.
- **Đã verify thật:** ghi checkpoint ở process 1, mở process MỚI đọc lại → `get_tuple()`
  trả đúng `checkpoint_id`. Không suy luận từ code tĩnh.
- **Fallback CÓ CHỦ ĐÍCH nhưng KHÔNG im lặng:** DB không phải Postgres (test dùng
  SQLite) → MemorySaver kèm **log cảnh báo** nêu rõ hệ quả. Không lặp lại ADR-013.
- **Hệ quả:** `close_checkpointer()` + shutdown hook — pool psycopg chạy thread nền,
  không đóng tường minh thì ném `PythonFinalizationError` lúc thoát (đã gặp thật) và
  giữ kết nối tới khi TCP timeout, ăn vào `max_connections` khi deploy liên tục.

## ADR-015 — Fan-out live-chat liên worker qua Redis pub/sub

- **Ngày:** 2026-08-13 · **Trạng thái:** Đang hiệu lực
- **Bối cảnh:** `ConnectionManager` giữ WebSocket trong RAM từng process. Bật
  multi-worker mà thiếu lớp này thì live-chat **vỡ âm thầm**: khách ở worker 1, CSKH
  ở worker 2, tin nhắn mỗi bên chỉ tới socket cùng worker. Không exception, không log
  lỗi — tin nhắn chỉ biến mất. Test tay khó bắt vì một máy thường chỉ nối một worker.
- **Quyết định:** luôn giao local TRƯỚC rồi mới publish, kèm `_INSTANCE_ID` để worker
  gốc bỏ qua tiếng vọng của chính mình.
- **Lý do BÁC BỎ "publish rồi để subscriber giao tất":** cách đó làm 1 worker (test/
  dev/CI) phụ thuộc subscriber phải sống, sinh ra kịch bản "tin biến mất vì subscriber
  chưa kịp chạy". Cách đã chọn: Redis chết → suy giảm về phạm vi 1 worker thay vì
  chết hẳn. Đánh đổi: serialize thêm 1 lần mỗi tin, không đáng kể.
- **Ràng buộc vận hành:** subscriber PHẢI khởi động ở startup, TRƯỚC khi có traffic —
  Redis pub/sub fire-and-forget, không có hàng đợi giữ lại (lỗi thật mắc phải lúc
  viết test: subscribe sau publish thì không nhận được gì).

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
