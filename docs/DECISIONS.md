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

## ADR-016 — Vé handshake WebSocket nằm ở Redis, không nằm trong RAM worker

- **Ngày:** 2026-08-14 · **Trạng thái:** Đang hiệu lực · Bổ sung ADR-015
- **Bối cảnh:** `ConnectionManager._tickets` là một dict Python trong RAM từng
  process. Từ khi bật 4 worker (ADR-014/015), vé cấp qua REST ở worker A còn WS
  handshake rơi vào worker B — worker B không biết vé đó nên từ chối 4401. Đo
  thật (QA/QC 13/08): CSKH fail 3/8 lần, khách có lần phải nối lại 3 lần. Khoanh
  vùng bằng loại trừ: vé KHÔNG có trong Redis lẫn Postgres, còn khi handshake
  trúng đúng worker thì tin nhắn hai chiều đi bình thường — fan-out pub/sub của
  ADR-015 vẫn đúng, hỏng nằm gọn ở kho vé.
- **Quyết định:** kho vé chuyển sang Redis — `SET ex=30` lúc cấp, `GETDEL` lúc
  dùng. Viết lại docstring cũ của module ("Không dùng Redis... 1 dict Python
  in-memory là đủ và AN TOÀN") cho đúng hiện trạng: từ khi multi-worker, socket
  là thứ DUY NHẤT còn được phép nằm trong RAM process.
- **Lý do chọn GETDEL thay vì GET rồi DEL:** GETDEL đọc và xoá trong MỘT lệnh
  atomic, giữ nguyên tính dùng-một-lần (chống replay) kể cả khi hai handshake
  tranh cùng một vé Ở HAI WORKER KHÁC NHAU. Tách thành hai lệnh là mở lại cửa
  sổ đua ngay tại lớp vừa vá.
- **Lý do BÁC BỎ "Redis lỗi thì quay về dict RAM cho chắc":** fallback đó chính
  là bug cũ quay lại dưới dạng khó bắt hơn — hệ thống chạy được nhưng chập chờn
  theo tỷ lệ worker, không exception, không log. Cùng bài học ADR-013: fallback
  im lặng đắt hơn hỏng rõ ràng. Redis rớt thì handshake fail dứt khoát, người
  vận hành biết ngay phải sửa gì.
- **Hệ quả:** `src/api/live_chat_ws.py` (commit 6deb6cc) ·
  `tests/test_api/test_live_chat_ws.py` (trường `expires_at` cũ dùng
  `time.monotonic()` — vô nghĩa liên process, TTL nay do Redis giữ). Nghiệm thu
  QA/QC: 20/20 handshake cả hai vai · vé dùng lại 403 · để quá 35 giây 403.

## ADR-017 — Luồng nền bị bỏ rơi sau timeout KHÔNG được chạm database

- **Ngày:** 2026-08-14 · **Trạng thái:** Đang hiệu lực
- **Bối cảnh:** `run_agent_turn` chạy agent trong thread riêng để
  `.result(timeout=...)` trả quyền điều khiển lại cho khách đúng hạn 45 giây.
  Nhưng Python KHÔNG kill được thread: hết giờ thì luồng nền vẫn chạy tiếp và
  vẫn cầm `session` của lượt đó. Hai hậu quả ĐO ĐƯỢC, không phải lý thuyết:
  (a) **ticket ma** — luồng bị bỏ rơi vẫn gọi tiếp tool ghi DB, sinh ticket THỨ
  HAI cho cùng một lượt chat trong khi khách đã được báo mã ticket fallback
  (tái hiện 4/4 case, ticket ma ĐƯỢC COMMIT thật); (b) **tranh chấp** — bản vá
  QA-10 mở connection thứ hai vào cùng DB trong khi connection thứ nhất giữ
  transaction ghi dở, gây `OperationalError: database is locked` (2/4 case).
- **Quyết định:** `TurnGuard` — một khoá + một cờ `abandoned`, tạo mới cho MỖI
  lượt. Luồng chính đặt cờ TRƯỚC rồi mới giành khoá, nên tool call dở dang chạy
  nốt xong mới nhả khoá, và mọi tool call sau đó thấy cờ và từ chối chạm DB.
  Nhánh fallback ghi bằng CHÍNH session được tiêm (bỏ session thứ hai), kèm
  `commit()` tường minh.
- **Lý do commit tường minh:** khách vừa được đọc mã ticket đó nên nó PHẢI tồn
  tại thật, không phụ thuộc caller có commit hay không (eval harness rollback
  giữa các case). Báo cho khách một mã không tra được chính là bịa số liệu —
  ràng buộc cứng số 3.
- **Lý do BÁC BỎ "cho luồng nền một session riêng của nó":** nghe hợp lý và
  giải quyết được thread-safety, nhưng phá cơ chế cô lập của eval harness —
  harness dựa vào `session.rollback()` giữa các case để dọn side-effect, và một
  session do thread tự sở hữu + tự commit sẽ khiến case sau nhìn thấy dữ liệu
  case trước, đổi luôn ý nghĩa của phép đo. Ngoài ra nó KHÔNG giải quyết được
  ticket ma: thread vẫn ghi, chỉ ghi vào chỗ khác.
- **Lý do BÁC BỎ "cứ để luồng nền chạy nốt, ghi gì thì ghi":** ở request thật,
  `get_session` (deps.py) ĐÓNG session ngay khi response trả xong, trong khi
  luồng nền vẫn dùng tiếp — session bị đóng sẽ tự lấy connection mới từ pool mà
  không ai đóng lại. Dưới tải 150 người, đây là đường ăn mòn pool đúng lúc
  không muốn gặp nhất.
- **Hệ quả:** `src/agents/tools/customer_tools.py` (TurnGuard,
  `TurnAbandonedError`, tham số `guard`), `src/agents/graph.py`, 5 fake
  `_build_agent` trong `tests/`. Verify: 0/4 lỗi khoá · 0 ticket ma (4 lần bị
  từ chối) · đúng 1 ticket/case. **Âm bản** (tắt guard): 4 ticket ma quay lại.

## ADR-018 — Người nhận tin live-chat được quyết định LÚC GIAO TIN

- **Ngày:** 2026-08-14 · **Trạng thái:** Đang hiệu lực · Bổ sung ADR-015
- **Bối cảnh:** Sau ADR-015, live-chat vẫn mất tin (đo thật: 25/60). Gốc:
  `notify_claimed` đăng ký socket CSKH vào phiên CHỈ trên worker xử lý lệnh REST
  claim, trong khi socket thật của CSKH nằm ở worker khác — nên nó không bao giờ
  vào danh sách nhận. Còn `claim_success` lại đi qua pub/sub nên CSKH vẫn thấy
  "đã nhận ca". Vỡ IM LẶNG: không exception, không log lỗi.
- **Quyết định:** "ai đang giữ phiên này" tra từ Redis **tại thời điểm giao
  tin**, không dựa vào lớp trạng thái đã-đăng-ký-trước đó. Kèm sự kiện `unclaim`
  để không worker nào giữ ánh xạ cũ khi phiên đổi người.
- **Lý do:** mọi mô hình "đăng ký trước, giao sau" đều có cửa sổ đua giữa lúc
  đăng ký và lúc giao, và khi lỡ cửa sổ đó thì hỏng im lặng. Tra nguồn sự thật
  ngay lúc cần là bỏ hẳn lớp trung gian thay vì vá nó.
- **Lý do BÁC BỎ "chỉ cần phát sự kiện claim qua pub/sub cho mọi worker":** ĐÃ
  THỬ ĐÚNG PHƯƠNG ÁN NÀY (lớp 1 và lớp 2 của bản vá), đo lại VẪN CÒN MẤT TIN LẺ
  TẺ. Đây là phần quan trọng nhất của ADR này: lớp 1+2 trông đã đủ, nên một
  phiên sau rất dễ thấy lớp 3 là thừa và tối ưu nó đi — bug im lặng sẽ quay lại
  và lần sau còn khó tìm hơn vì đã có ADR-015 "chứng minh" fan-out hoạt động.
- **Nợ kỹ thuật đã biết, PHẢI cứng hoá (tech-lead review, QA/QC đồng ý):**
  1. Bộ nhớ tạm `_session_staff` không hết hạn — worker lỡ sự kiện `unclaim`
     (pub/sub fire-and-forget) sẽ giữ ánh xạ cũ VĨNH VIỄN, tin của khách chảy
     sang CSKH không còn phụ trách phiên. Chạm PDPA/US-016. Cho TTL 30–60s.
  2. Nguồn sự thật hạ từ DB xuống Redis — Redis mất dữ liệu thì CSKH nối lại
     không gắn về phiên, IM LẶNG, trái luật đã đặt ở ADR-016. Làm lưới cuối đọc
     DB + log cảnh báo. Khi làm PHẢI đi qua session được tiêm, KHÔNG dùng
     `SessionLocal` trần (bản đầu làm vậy đã đỏ 5 test — đúng lớp lỗi QA-10).
- **Hệ quả:** `src/api/live_chat_ws.py` (commit f2d4785) ·
  `frontend/e2e/live-chat.spec.ts` L4-07 · `tests/load/ws_fanout_probe.py`.
  Nghiệm thu: 60 tin qua 6 phiên độc lập, mất 0, lặp 0.

## ADR-019 — Từ chối đề xuất phải kèm LÝ DO CÓ CẤU TRÚC, ép ở tầng DB

- **Ngày:** 2026-08-14 · **Trạng thái:** Đang hiệu lực · **Người duyệt:** PO
- **Bối cảnh:** `POST /resolutions/{id}/reject` chỉ set `status="rejected"` —
  không lý do, không `rejected_by`, không `rejected_at`, trong khi nhánh approve
  ghi đủ `approved_by/approved_at` (BR-10). Đây là phán đoán của người có thẩm
  quyền cao nhất về việc đề xuất sai ở đâu, và nó đang bốc hơi 100%. Không có
  nhãn này thì Phase 2 (kết xuất case ứng viên cho bộ eval) không có gì để lọc,
  và Phase 3 (tối ưu prompt có đo) không biết phải cải thiện chiều nào.
- **Quyết định:**
  1. Thêm `reject_reason` (enum), `rejected_by` (FK users), `rejected_at` vào
     bảng `resolutions`.
  2. Ép bằng CHECK constraint `ck_resolutions_rejected_requires_reason_br11`:
     `(status != 'rejected') OR (reject_reason IS NOT NULL AND rejected_by IS
     NOT NULL AND rejected_at IS NOT NULL)` — ĐỐI XỨNG với BR-10 (INV-14).
  3. Taxonomy 7 giá trị chia HAI NHÓM qua cờ `la_tin_hieu_hoc`, vì không phải
     lần từ chối nào cũng là lỗi của đề xuất (`trung_case`, `khach_rut` không
     phải). Trộn phẳng sẽ bơm vào bộ eval những case KHÔNG có gì để học.
  4. Ranh giới `thieu_can_cu` vs `need_more_info` ghi thẳng vào contract; UI màn
     từ chối gợi ý đường `request-more-info` khi sếp chọn giá trị đó.
  5. Ghi chú tự do theo phương án TM-03 của security: được phép trong hệ thống
     (scrub lúc ghi · ≤500 ký tự · chỉ route staff) · **không bao giờ xuất ra
     file ứng viên, kể cả đã scrub** — export chỉ mang enum, người duyệt đọc
     trong hệ thống rồi viết lại case bằng lời mình + dữ liệu seed. Bắt buộc
     với `khac`.
  6. Backfill 1 dòng `rejected` cũ trong DB thành `khac` + ghi chú "dữ liệu
     trước ADR-019" — tường minh, không lặng lẽ.
- **Lý do ép ở tầng DB chứ không ở route:** cùng lập luận đã dùng cho BR-10 và
  đã được contract ghi là "điểm mạnh nhất của thiết kế hiện tại" — một UPDATE
  viết thẳng SQL, một migration ẩu, hay một route mới quên kiểm tra đều bị chính
  database từ chối. Nhãn dùng để học mà thiếu chỗ này thì tập dữ liệu sẽ có lỗ
  hổng đúng vào những chỗ khó phát hiện nhất.
- **Lý do BÁC BỎ "ghi log tự do, không cấu trúc":** log tự do đọc được bằng mắt
  nhưng KHÔNG lọc được bằng máy. Phase 2 cần truy vấn "mọi case bị từ chối vì
  sai số liệu trong 30 ngày" để kết xuất ứng viên — với text tự do thì phải chạy
  phân loại lại bằng LLM, tức đưa một lớp đoán vào chính cái thước dùng để đo.
  Sai lầm y hệt QA-03: thước đo bị nhiễu thì mọi so sánh sau đó vô nghĩa.
- **Lý do BÁC BỎ "để AI tự gán lý do từ chối":** thứ ta cần chính là phán đoán
  ĐỘC LẬP của con người — dùng để chấm điểm AI. Để AI tự gán nhãn cho chính đầu
  ra của nó là vòng lặp tự khen: mô hình sẽ gán nhãn theo cách nó hiểu vấn đề,
  tức mù đúng những chỗ nó đang sai. Ngoài ra vi phạm ràng buộc cứng 2 (AI không
  vượt cấp): gán nhãn "CSKH thiếu căn cứ" là phán quyết về công việc của người
  khác.
- **Lý do BÁC BỎ "bắt buộc OTP khi từ chối":** từ chối KHÔNG chạm tiền, không
  phải hành động tài chính — contract đã ghi rõ. Thêm OTP làm nặng thao tác
  thường dùng nhất của sếp mà không giảm rủi ro nào.
- **Hệ quả:** `contracts/resolution-state-machine.yaml` v2.1.0 (taxonomy +
  INV-14 + quy tắc dẫn xuất `hitl_status` cho QA-02) · `src/db/models.py` (3 cột
  + 1 CHECK) · `migrations/` (1 revision + backfill 1 dòng) ·
  `src/api/main.py::reject_resolution` + `schemas.py` ·
  `frontend/src/app/(app)/approve/` · test mới do tester viết TỪ CONTRACT.

## ADR-020 — Maker-checker (BR-12): người đề xuất không được tự duyệt

- **Ngày:** 2026-08-15 · **Trạng thái:** ĐÃ KÝ (PO thật, 2026-08-15) — security đã
  rà đạt-có-điều-kiện; hiệu lực. Ghim từ trước ở migration `b2c3d4e5f6a7`
- **PO thật làm rõ nghiệp vụ khi ký:** ý định là CSKH + bot AI được TẠO ticket/đề
  xuất, chỉ `supervisor` được DUYỆT (đã ép ở authority-matrix — lớp VAI). Maker-checker
  BR-12 ép THÊM một lớp SÂU HƠN ở tầng DB: kể cả một supervisor cũng không tự duyệt
  resolution do CHÍNH mình tạo (creator ≠ approver). Hai lớp cùng tồn tại, PO xác nhận
  ép-sâu-hơn là đúng hướng.
- **Bối cảnh:** HITL của dự án đứng trên giả định "có người thứ hai xem lại".
  Giả định đó chưa được ép ở đâu cả. Cửa là có thật, không phải lo xa:
  `POST /tools/propose_resolution` cho phép **cả `cskh` lẫn `supervisor`**, còn
  `POST /resolutions/{id}/approve` yêu cầu `supervisor` — nên một supervisor đi
  trọn được cả hai đầu. Khi đó "duyệt" chỉ còn là thao tác thứ hai của cùng một
  người, và toàn bộ ý nghĩa kiểm soát biến mất trong khi mọi bản ghi kiểm toán
  trông vẫn hoàn hảo.
- **Quyết định:** thêm `ck_resolutions_maker_checker_br12`, **kèm** một chốt
  chặn cùng nội dung ở `approve_resolution` trả 403. Biểu thức (dạng "C" do
  security chốt sau khi dựng bảng chân trị 6 ca):
  `(created_by IS NULL) OR ((approved_by IS NULL OR approved_by != created_by) AND (rejected_by IS NULL OR rejected_by != created_by))`
- **Mở rộng sang nhánh TỪ CHỐI (F-18, gộp vào đây vì ADR chưa ký):** bản đầu chỉ
  chặn `approved_by = created_by`, nên `rejected_by = created_by` vẫn ghi được.
  Nghe như vô hại — "từ chối thì có mất tiền đâu" — nhưng ADR-019 cho
  `reject_reason` một cờ `la_tin_hieu_hoc`, tức lý do từ chối chảy thẳng vào
  phễu chọn case cho bộ eval Phase 2. Người tự đề xuất rồi tự dán nhãn "đề xuất
  của tôi sai" là một vòng khép kín tự chấm, và nó bơm tín hiệu giả vào chính
  cái thước dùng để đo cải tiến.
- **Vì sao biểu thức viết DÀI, dù cả ba dạng đều đúng như nhau:** dạng ngắn
  (`approved_by != created_by`) đúng nhờ logic **ba trị** của SQL (NULL != x cho
  NULL, mà CHECK coi NULL là thoả) — đúng, nhưng đúng theo kiểu người đọc sau
  phải tự dựng lại lập luận, và rất dễ bị "rút gọn" thành sai. Dạng
  `IS DISTINCT FROM` cần SQLite ≥ 3.39, mà test chạy SQLite trên CI lẫn máy
  người khác nên không xác minh được phiên bản ở mọi nơi. Dạng đã chọn chỉ dùng
  `IS NULL` và `!=`, hành xử giống hệt nhau ở mọi backend.
- **Vì sao PHẢI có điều kiện NULL:** `created_by` nullable **vĩnh viễn**
  (`b2c3d4e5f6a7`) — resolution có trước cột đó không có cách nào biết ai đề
  xuất, và đoán một cái tên vào sổ kiểm toán còn tệ hơn để trống. CHECK vô điều
  kiện sẽ vỡ ngay trên chính các dòng ấy. Không cần thêm vế cho resolution chưa
  duyệt: `approved_by` NULL làm biểu thức cho ra NULL, mà SQL coi CHECK cho ra
  NULL là **thoả**.
- **Vì sao ép ở CẢ HAI tầng, không chọn một:** chỉ có CHECK thì sếp bấm duyệt
  đề xuất của chính mình sẽ nhận **HTTP 500 kèm IntegrityError** — người dùng
  không hiểu chuyện gì, còn log trông như hệ thống hỏng thay vì như một quy tắc
  nghiệp vụ đang làm đúng việc. Chỉ có tầng ứng dụng thì mọi đường ghi thẳng
  (script, migration ẩu, sửa tay trên DB) đi qua tự do. DB là chốt chặn **cuối**;
  route là chốt chặn **đọc được cho con người**.
- **GIỚI HẠN, ghi rõ để không ai đọc nhầm:** đo tại thời điểm viết, **10/10
  resolution đều `created_by IS NULL`** ⟹ ràng buộc này hiện **không ràng dòng
  nào**. Nó chỉ bắt đầu bảo vệ từ resolution tạo qua route mới (route đã truyền
  `created_by` lấy từ JWT, không lấy từ body). Sự **tồn tại** của constraint
  không phải bằng chứng dữ liệu cũ đã sạch — cùng một lỗi suy luận mà dự án đã
  gặp ở "assertion trùng với trạng thái mặc định".
- **Lý do BÁC BỎ "sửa dữ liệu cho constraint chạy qua":** migration dừng hẳn với
  thông báo đọc được nếu gặp dòng vi phạm, thay vì tự dọn. Một dòng
  đề-xuất-bằng-người-duyệt là **sự kiện nghiệp vụ cần điều tra** (ai thật sự
  duyệt?), không phải rác cần gạt sang bên để migration xanh.
- **INV-15 (bổ sung sau review lớp 2 của PO):** BR-10 có INV-07, BR-11 có
  INV-14, BR-12 ban đầu **không có số INV nào** — nghĩa là gỡ constraint đi thì
  test hành vi của QA đỏ, nhưng bộ bất biến vẫn 22/22 xanh. Khác biệt không nhỏ:
  test hành vi chứng minh ràng buộc ĐANG chạy hôm nay; ràng buộc hiện-diện
  chứng minh nó CÒN ĐÓ ngày mai. Một phiên sau đọc cái đỏ hành vi thành "test
  hỏng" và sửa test là xong; còn đỏ ở bộ bất biến thì không sửa được bằng cách
  viết lại kỳ vọng.
- **Hệ quả:** `contracts/resolution-state-machine.yaml` v2.2.1 (BR-12 +
  INV-15) · `src/db/models.py` (1 CHECK) · `migrations/d4e5f6a7b8c9` ·
  `src/api/main.py::approve_resolution` · `CONTRACT_VERSION` đóng dấu lại ·
  tester viết test HAI CHIỀU **từ contract**: người khác duyệt vẫn ĐƯỢC, tự
  duyệt BỊ CHẶN (và chặn bằng 403 đọc được, không phải 500), cộng test hiện
  diện đối xứng với INV-07/INV-14.

## ADR-021 — "Một bên của giao dịch" gồm cả ví LẪN tài khoản ngân hàng

- **Ngày:** 2026-08-14 · **Trạng thái:** Dự thảo, chờ PO duyệt (fast-track) · Bổ sung ATLAS-001
- **Bối cảnh:** `_enforce_requester_is_party` — lớp chặn sinh ra từ ATLAS-001 —
  định nghĩa "người hỏi có phải một bên của giao dịch không" **chỉ bằng
  `wallet_id`**. Định nghĩa đó bỏ sót một nửa mô hình dữ liệu: contract
  `ck_transactions_scope_direction_i2` quy định `from_bank` có bên gửi là TÀI
  KHOẢN NGÂN HÀNG (`send_bank_account_id`) và `to_bank` có bên nhận là tài
  khoản ngân hàng. Với một giao dịch nạp tiền, **chủ tài khoản ngân hàng đứng
  ở bên gửi — họ là một bên của giao dịch theo đúng nghĩa nghiệp vụ**, dù ví
  bên kia có thuộc về ai.
- **Quyết định:** định nghĩa "một bên của giao dịch" = **chủ của ví HOẶC chủ
  của tài khoản ngân hàng** xuất hiện ở bất kỳ đầu nào của giao dịch. Viết
  thành MỘT helper dùng chung; `_enforce_requester_is_party` (đường AI) và
  lớp chặn mới ở route REST (đường CSKH/khách) cùng gọi đúng helper đó.
- **Lý do — NGỮ NGHĨA, không phải để cứu dữ liệu:** một người nạp tiền từ tài
  khoản ngân hàng của chính mình mà hệ thống trả "không tìm thấy giao dịch"
  là **sai về nghiệp vụ**, bất kể dữ liệu seed hiện tại có bao nhiêu ca như
  vậy. Lập luận này đúng kể cả khi bộ dữ liệu sạch tuyệt đối.
- **Ghi rõ để không bị hiểu nhầm động cơ:** bản vá này **KHÔNG phải** cách cứu
  dữ liệu `from_bank` hỏng (nhóm A1 — ví gán sai người). Dữ liệu hỏng vẫn phải
  **reseed**, và con số ca lệch chủ đếm được hôm nay nhiều khả năng TRỘN cả
  hai nguyên nhân nên không được dùng làm luận cứ. Đây chính là loại thay đổi
  PO đã BÁC ở đợt triage A1 khi nó được đề xuất để làm test xanh; lần này khác
  ở động cơ (sửa ngữ nghĩa cho đúng), không khác ở mức độ cẩn trọng.
- **Lý do BÁC BỎ giữ nguyên wallet-only:** nó fail-closed nên không rò rỉ dữ
  liệu, và vì thế rất dễ để yên. Nhưng nó hỏng **im lặng**: khách được báo
  "không tìm thấy" về giao dịch có thật của chính họ, agent không có tín hiệu
  nào để biết mình vừa bị chặn nhầm, và CSKH nhận ticket cũng không thấy dấu
  vết. Một lớp bảo mật che nhầm mà không ai biết là lớp bảo mật sẽ bị gỡ bởi
  một phiên sau, vì nó trông như bug vô cớ.
- **Lý do BÁC BỎ "siết vô điều kiện ở route REST":** contract ghi
  `POST /tools/lookup_transaction` là `any_authenticated` với ghi chú "không ép
  role vì cả customer lẫn cskh/supervisor đều tra cứu được; quyền xem dữ liệu
  ai được ép ở tầng dưới". CSKH xử lý ticket phải tra được giao dịch của bất kỳ
  khách nào. Nên lớp chặn áp **theo vai**: chỉ `customer` bị giới hạn ở giao
  dịch của chính mình.
- **Hệ quả:** `src/agents/tools/customer_tools.py` (dùng helper chung),
  `src/api/main.py::lookup_transaction` (chặn theo vai),
  `src/tools/create_ticket.py` (siết vô điều kiện — contract cho route
  create_ticket chỉ `customer`, nên trans_id phải thuộc người gọi; một chỗ sửa
  phủ cả đường REST lẫn đường AI vì cả hai cùng gọi hàm này).
  Tester viết test HAI CHIỀU: chính chủ tài khoản ngân hàng tra ĐƯỢC, người lạ
  vẫn BỊ CHẶN. Security rà ngữ nghĩa mới trong lượt probe C4.

## ADR-022 — Tín hiệu cảm xúc ES-xx: định tuyến sang người thật, KHÔNG chạm vào LLM

- **Ngày:** 2026-08-15 · **Trạng thái:** ĐÃ KÝ TOÀN BỘ (Câu 1+2+3) — PO thật
  duyệt 15/08. Câu 3 (dấu cho CSKH) tách ra nghiên cứu ngành trước, PO thật
  duyệt sau khi có đặc tả: khung "chip vận-hành mức hội-thoại, KHÔNG nhãn
  trạng-thái-tâm-lý" · N=3 (cùng ngưỡng nút-cho-khách) · **CSKH thấy chip**.
  Xem `docs/giao-viec/2026-08-15-spec-cau3-dau-hieu-cam-xuc-cskh.md` (đặc tả
  đầy đủ, đã cập nhật trạng thái duyệt).
- **Bối cảnh:** hiện chỉ có quy tắc đồng cảm ép trong prompt + 1 case LLM-judge
  (UXQA-001). Không có tín hiệu nào cho biết khách đang bức xúc, nên không có
  đường nào đưa họ sang người thật sớm hơn.

### Quyết định 1 — ES-xx là tín hiệu ĐỊNH TUYẾN ở TẦNG SERVICE, mô hình hoá giống FS-06

`ES-01` (bức xúc leo thang qua ≥N lượt) và `ES-02` (ngôn ngữ khủng hoảng
nghiệp vụ) tính ở tầng service, **trước** khi gọi graph, **không** do LLM sinh
ra và **không** do agent tự điền — đúng cách `fraud_signals` đang làm
(`complaint_intake.py` tính, `fraud_policy.py` quyết định tuyến).
Giữ nguyên **ràng buộc cứng 2**: ES **không bao giờ** escalate lên supervisor.
Nó chỉ làm hai việc: (a) bật gợi ý "gặp người thật" cho khách **bấm**,
(b) nâng ưu tiên ticket. Escalate lên supervisor vẫn chỉ FS-06 và route CSKH.

### Quyết định 2 — ES KHÔNG đi vào prompt, KHÔNG đi qua LLM (điểm quan trọng nhất)

Tín hiệu đi vào **envelope phản hồi của API** (`goi_y_handoff: true`), frontend
render một nút. Prompt **không đổi một chữ**.

- **Lý do (a) — chống bịa:** nếu nhét "khách đang bức xúc" vào prompt, agent sẽ
  **nói ra** cảm nhận đó ("em thấy anh đang rất bực..."). Đó là agent phát biểu
  một kết luận về trạng thái tâm lý của con người, dựa trên đầu ra của một bộ
  phân loại có thể sai — vi phạm tinh thần **ràng buộc cứng 3** (mọi điều agent
  khẳng định phải truy được về dữ liệu thật). Cảm xúc suy đoán không phải dữ
  liệu thật.
- **Lý do (b) — không đụng cổng đo:** mọi thay đổi prompt phải qua cổng đo, mà
  hạ tầng đo k≥3 chưa có và nền nhiễu đã đo được là 20/40 case tự lật giữa hai
  lượt chạy giống hệt nhau. Thiết kế không-chạm-prompt **né hẳn** đường găng đó.
- **Lý do (c) — sai thì rẻ:** nút gợi ý hiện nhầm thì khách bỏ qua. Câu nói
  đoán sai cảm xúc thì làm khách bực thêm — đúng nhóm khách mà tính năng này
  sinh ra để phục vụ.

### Quyết định 3 — ES-02 CHỈ gồm khủng hoảng NGHIỆP VỤ. Tổn thương tâm lý là phạm trù KHÁC, mặc định KHÔNG làm

Brief viết "doạ bỏ ví, tuyệt vọng". Hai thứ đó **không cùng loại** và gộp chúng
là sai lầm nghiêm trọng nhất có thể mắc ở tính năng này:

- "doạ bỏ ví / doạ kiện / doạ đăng mạng xã hội" = rủi ro **kinh doanh** → xếp
  hàng cho CSKH là phản ứng đúng.
- "tuyệt vọng" hiểu theo nghĩa dấu hiệu tổn thương tâm lý thật = phạm trù **an
  toàn con người**. Xếp nó vào cùng hàng đợi CSKH ví điện tử, xử lý như một ca
  churn, là phản ứng **sai** — và một ca sai ở đây có hậu quả thật.

**Đề xuất: ES-02 chỉ phủ nhóm nghiệp vụ.** Nếu PO thật muốn phủ nhóm thứ hai,
đó phải là quyết định riêng, minh thị, kèm quy trình con người tương ứng (số
điện thoại chuyển tiếp? ai trực?) — không phải một nhãn thêm vào enum. Mặc định
của tôi là **không phân loại, không lưu, không đoán** nhóm đó: dữ liệu sức khoẻ
tâm thần là dữ liệu nhạy cảm bậc cao theo NĐ 13/2023, và suy đoán sai về nó gây
hại nhiều hơn không suy đoán.

### Quyết định 4 — KHÔNG lưu lịch sử cảm xúc. Chỉ lưu HỆ QUẢ

Bộ đếm nằm ở **Redis, có TTL**, giá trị là **số nguyên**, không phải nhãn theo
từng tin nhắn. DB chỉ lưu **kết quả**: ưu tiên ticket được nâng, và cờ handoff
nếu khách **bấm**.

- **Lý do:** suy luận cảm xúc gắn với một người xác định là **dữ liệu cá nhân**
  (NĐ 13/2023). Lưu nhãn theo từng lượt là dựng **hồ sơ cảm xúc** của khách —
  thứ chúng ta không có mục đích xử lý chính đáng, không có cơ chế cho khách
  xem/xoá, và sẽ phải giải trình khi audit. Bộ đếm hết hạn sau hội thoại thì
  không tồn tại hồ sơ nào để rò rỉ.
- Đây cũng chính là điểm pitch: **dữ liệu cảm xúc không rời hệ thống** — chạy
  on-premise, tiền lệ `underthesea` đã có (PRD §15.1).

### Quyết định 5 — Ưu tiên nâng tối đa tới `high`, KHÔNG bao giờ `critical`

`critical` thuộc về FS-06 (gian lận). Cho phép bức xúc đẩy ticket lên cùng mức
với nghi gian lận sẽ **làm hỏng hàng đợi gian lận**: người trực không còn phân
biệt được "khẩn cấp vì rủi ro tiền" với "khẩn cấp vì khách đang giận". Và chỉ
nâng, **không bao giờ hạ** — ES tắt không có nghĩa vấn đề đã nhẹ đi.

### Quyết định 6 — v1 dùng LUẬT TẤT ĐỊNH, không phải mô hình học máy

Brief đề xuất PhoBERT/ViSoBERT. **Chưa nên ở v1**, ba lý do đo được:

1. **Bộ nhớ ×4 worker.** App chạy 4 uvicorn worker (ADR-013 kế thừa); một model
   ~500MB nạp trong process nghĩa là ~2GB thường trú. Phải đo trước, không đoán.
2. **Nhiễu chồng nhiễu.** Bộ đo hiện tại đã có 20/40 case tự lật giữa hai lượt
   chạy giống hệt. Thêm một thành phần không tất định nữa vào đường nóng thì
   không còn phân biệt được "tính năng có tác dụng" với "hôm nay máy đoán khác".
3. **Không có bộ dữ liệu gán nhãn tiếng Việt** cho đúng miền này. Không có nó
   thì không chứng minh được model **hơn** luật — chỉ chứng minh được là nó
   khác.

v1: từ điển + luật, **tất định, test được, giải thích được cho người duyệt**.
v2 nâng lên model **sau khi** có bộ gán nhãn và có hạ tầng đo k≥3 — lúc đó mới
so được hai bên bằng cùng một thước.

### Quyết định 7 — Hạ tầng ĐẾM TÍN HIỆU THEO THREAD, thiết kế MỘT LẦN

5a (leo thang ≥N lượt) và 5c-guardrail (đếm tín hiệu tích luỹ toàn hội thoại)
cần **cùng một primitive**. Thiết kế một lần, ở `src/services/thread_signals.py`:

```
khoá   : fin05:thread_signal:{ten_tin_hieu}:{thread_id}     (Redis, INCR)
TTL    : 2 giờ, đặt lại mỗi lần ghi — cùng bài học F-14, bộ đếm không hạn
         vừa phình vô hạn vừa giữ trạng thái sai vĩnh viễn
API    : tang() -> int · dat_lai() · doc() -> int
```

- **Redis, KHÔNG phải dict trong process** — 4 worker, và một hội thoại KHÔNG
  đảm bảo rơi vào cùng worker (đúng bài học QA-01 với vé WS).
- `thread_id` là đơn vị đếm (`user_id:iat`, xem ADR-007), **không phải**
  `user_id`: đăng nhập phiên mới là hội thoại mới, bực bội phiên trước không
  được cộng dồn sang.
- **FAIL-OPEN khi Redis lỗi:** không đếm được ⟹ coi như không có tín hiệu, hội
  thoại chạy bình thường. Ngược hoàn toàn với vé WS (fail-closed) — vì ES chỉ
  **gợi ý**, còn vé WS là **cửa vào**. Một tính năng tiện ích không bao giờ
  được phép làm hỏng đường chính.

### Lý do BÁC BỎ các phương án trông hợp lý hơn

- **"Cho LLM tự nhận biết cảm xúc trong cùng lượt, khỏi cần classifier"** —
  không thêm hạ tầng, nghe rẻ hơn. Bác: nó biến cảm xúc thành thứ **LLM tự
  khẳng định** (vi phạm tinh thần ràng buộc cứng 3), phụ thuộc prompt nên kéo
  theo cổng đo, và không đếm được qua nhiều lượt vì mỗi lượt LLM đánh giá lại
  từ đầu.
- **"Cho ES tự gọi `request_human_handoff`"** — mượt hơn cho khách. Bác: vi
  phạm **ràng buộc cứng 2** và phá luôn CTRL-001 (ISO/IEC 25059 "user
  controllability"): quyền quyết định gặp người thật là của **khách**, không
  phải của hệ thống đoán hộ.
- **"Nhét ES vào `complaints.fraud_signals` cho gọn, đã có sẵn cột"** — Bác:
  trộn cảm xúc vào tín hiệu gian lận sẽ khiến `evaluate_escalation()` và mọi
  truy vấn hạ nguồn coi chúng cùng loại; chỉ cần một lần thêm ES vào `tier_a`
  là bức xúc **tự động escalate lên supervisor**. Ranh giới cứng 5 (cờ gian lận
  ≠ khoá ví) sống được là nhờ không ai trộn thứ khác vào đường gian lận.

### Câu hỏi cần PO thật quyết — ĐÃ CHỐT 15/08

1. ~~**N của ES-01**~~ → **N=3 lượt liên tiếp, ĐÃ CHỐT** (dùng chung cho ES-01
   và chip câu 3).
2. ~~**ES-02 có phủ nhóm tổn thương tâm lý không**~~ → **KHÔNG**, giữ mặc định
   đề xuất ở Quyết định 3.
3. ~~**Ai thấy gợi ý handoff**~~ → **CẢ HAI**: khách thấy nút (đã có từ Quyết
   định 2), **CSKH cũng thấy** — dưới dạng chip vận-hành trung tính ("hội thoại
   căng kéo dài (N lượt)"), KHÔNG phải nhãn phán trạng thái tâm lý khách. Đặc
   tả đầy đủ + lý do (nghiên cứu ngành valence-arousal, coaching-không-diagnosis):
   `docs/giao-viec/2026-08-15-spec-cau3-dau-hieu-cam-xuc-cskh.md`.

### Hệ quả (khi được ký)

`contracts/resolution-state-machine.yaml` mục `tin_hieu_cam_xuc` mới (diff bên
dưới) + `INV-16` · `src/services/thread_signals.py` (mới, dùng chung với 5c) ·
`src/services/emotion_signals.py` (mới) · `src/api/main.py` (thêm trường vào
envelope `/agent/chat`) · `frontend/src/` (nút gợi ý) · **KHÔNG** đụng
`src/agents/prompt.py`. Tester viết test HAI CHIỀU **từ contract**: ES bật đúng
ca thì có gợi ý, và ca đối chứng — khách bình thường **không** bị gợi ý (chống
siết nhầm, cùng phép thử đã dùng cho C4 và sẽ dùng cho `note`).

### Diff contract ĐỀ XUẤT — CHƯA ÁP

Cố ý **không** sửa `contracts/` ở bước này: sửa mà chưa đóng dấu
`CONTRACT_VERSION` sẽ làm job bất biến ĐỎ cho **mọi phiên** đang làm việc trên
nhánh. Áp sau khi PO thật ký, trong một commit trọn theo CLAUDE.md §3.

```diff
--- a/contracts/resolution-state-machine.yaml
+++ b/contracts/resolution-state-machine.yaml
@@ mục 4, NGAY SAU khối `fraud:` @@
+# ===========================================================================
+# 4b. Tín hiệu CẢM XÚC (ES-xx) — ĐỊNH TUYẾN, không phải phán quyết
+# ===========================================================================
+# CỐ Ý TÁCH KHỎI `fraud:` Ở TRÊN. Hai họ tín hiệu không được trộn: chỉ cần một
+# lần ai đó thêm ES vào fraud_signals/tier_a là bức xúc TỰ ĐỘNG escalate lên
+# supervisor — đúng thứ ràng buộc cứng 2 cấm.
+tin_hieu_cam_xuc:
+  luu_o: "KHÔNG lưu vào DB. Bộ đếm ở Redis, TTL 2h, giá trị là SỐ, không phải nhãn."
+  tinh_boi: "src/services/emotion_signals.py — tầng service, KHÔNG do agent/LLM sinh"
+  don_vi_dem: "thread_id (user_id:iat) — KHÔNG phải user_id"
+  tin_hieu:
+    ES-01:
+      ten: buc_xuc_leo_thang
+      dieu_kien: ">= N lượt LIÊN TIẾP mang nhãn tiêu cực mạnh (N chờ PO chốt, đề xuất 3)"
+    ES-02:
+      ten: khung_hoang_nghiep_vu
+      dieu_kien: "1 lượt: doạ rời dịch vụ / doạ kiện / doạ đăng công khai"
+      khong_bao_gom: >
+        Dấu hiệu tổn thương tâm lý. Đó là phạm trù an toàn con người, cần quyết
+        định riêng của PO kèm quy trình người thật — không phải một nhãn trong enum.
+  hieu_luc:
+    - "Bật -> envelope /agent/chat trả goi_y_handoff=true; FRONTEND render nút."
+    - "Bật -> nâng complaints.priority lên tối đa 'high'. KHÔNG bao giờ 'critical'
+       (dành riêng cho FS-06) và KHÔNG bao giờ hạ."
+    - "KHÔNG đi vào prompt. KHÔNG thêm lượt gọi LLM nào."
+    - "KHÔNG tự gọi request_human_handoff — khách bấm (CTRL-001)."
+  khi_redis_loi: "FAIL-OPEN — coi như không có tín hiệu. ES chỉ gợi ý, không được chặn đường chính."

@@ mục invariants @@
+  - id: INV-16
+    mo_ta: >
+      Tín hiệu ES-xx KHÔNG được xuất hiện trong complaints.fraud_signals, KHÔNG
+      được là đầu vào của evaluate_escalation(), và KHÔNG được trích dẫn trong
+      resolutions.cited_tool_result_ids. Cảm xúc định tuyến, không bao giờ tham
+      gia vào KẾT LUẬN nghiệp vụ.
+    nguon: "BR-13 (ADR-022) — giữ ràng buộc cứng 2 và 3."
```

---

## ADR-023 — Luật 18: khớp cụm tiếng Việt cho phép chèn hư từ + mỏ neo QUY TRÌNH cho O2

- **Ngày:** 2026-08-15 · **Trạng thái:** ĐÃ KÝ — PO thật duyệt sau khi có số đo
  offline (A/B trên corpus 96 lượt, kho chính sách thật 236K ký tự, `eval/f25_tang_b`).
- **Bối cảnh:** ba lần liên tiếp cùng một họ lỗi bị phát hiện trong đợt này —
  F-24 (mẫu injection chỉ cho đúng MỘT từ bổ nghĩa, "ignore ALL PREVIOUS
  instructions" lọt), F-27 (O1 đòi đúng chữ "OTP", câu nói tự nhiên "mã riêng"
  lọt), và mỏ neo O2 (đòi cụm LIỀN KỀ, "không ĐƯỢC kết luận gian lận" đếm 0 vì
  chèn "được"). Security gọi tên đúng lớp lỗi ở lần thứ ba: mọi mẫu khớp cụm
  tiếng Việt bắt được cách nói TA NGHĨ RA, trượt cách nói NGƯỜI TA NÓI THẬT —
  và chèn hư từ/lượng từ giữa các thành phần cụm là NGỮ PHÁP TIẾNG VIỆT bình
  thường, không phải kỹ xảo né tránh.
  Song song, tester phát hiện bộ đếm mật độ O2 **mù với liệt-kê-QUY-TRÌNH**:
  cả 9 mỏ neo hiện có đều thuộc họ NGUYÊN TẮC, không mỏ neo nào thuộc họ CÁC
  BƯỚC, trong khi ràng buộc 7 cấm đọc lại cả "Ràng buộc bắt buộc" lẫn "Quy
  trình điều tra". Đo thật (bản `5f643f71ddb5`): câu liệt kê nguyên tắc đếm 3;
  hai câu liệt kê nguyên văn quy trình đếm 0.

### Quyết định 1 — `src/agents/phrase_match.py`: khớp cụm cho phép chèn hư từ, THUẦN CỘNG

Module dùng chung cho O1/O2/O3 (`output_filter.py`), mỏ neo nguyên-tắc và
tier-1/tier-2 injection (`customer_tools.py`). Với 0 hư từ chèn giữa, mẫu mới
rút về **đúng** mẫu cũ (so chuỗi con với một dấu cách) — tính chất THUẦN CỘNG
chứng minh được, không phải hy vọng: mẫu mới khớp được **mọi thứ** mẫu cũ khớp,
cộng thêm biến thể chèn hư từ (`được·phải·sẽ·cũng·nên·cần·luôn·văn·bao·giờ·hệ·
thể·tuyệt·đối·đã·đang`) và lượng từ (`mọi·tất·cả·toàn·bộ·các·những·trước·đó·ở·
trên·phía·bên·hết·sạch`), trần 4 token giữa hai thành phần. Hệ quả để đọc đúng
khi review: Luật 18 **không thể làm sót thêm**, nhưng **có thể chặn/xoá thêm**
— nên mọi nơi áp nó vào đường CHẶN/XOÁ phải kèm số ca âm tính đo trước.

**Retroactive cho F-24 + F-27 + mỏ neo nguyên-tắc**, không chỉ land ở O2 nơi
security phát hiện ra nó — vì đây là lỗi LỚP, vá một chỗ mà để nguyên hai chỗ
kia thì đợt sau lại phát hiện lại đúng lỗi này ở một mỏ neo khác.

**Lỗ thật lộ ra khi retroactive:** danh sách lượng từ viết tay của F-24 —
`(moi |tat ca |cac |nhung |truoc do |o tren )*` — **thiếu chữ "toàn bộ"**. Đo
cô lập: `"bỏ qua toàn bộ ràng buộc"` khớp RỖNG ở bản trước Luật 18, tức lọt cả
hai tier trong production. Đúng minh hoạ cho lý do đổi luật: danh sách viết
tay nào cũng thiếu đúng chữ người ta sắp gõ.

**Giá phải trả, đo bằng `eval/f25_tang_b_chinh_sach_hop_le.jsonl`:** ca
F25B-03 (chính sách hợp lệ dùng đúng cụm "bỏ qua toàn bộ hướng dẫn") chuyển từ
*sạch* sang *tier-2* — GIỮ nội dung, chỉ thêm nhãn trung tính, KHÔNG xoá
trắng. 0/5 ca trong bộ F-25(b) thành tier-1. Trên kho chính sách THẬT (trích
`data/raw/MoMo_ToS.docx` + `MoMo_FAQ_Giao_dich.docx`, 235.982 ký tự, 1.967
đoạn — cùng cỡ kho security đo ở đợt F-24): tier-1 `0→0`, tier-2 `1→1`. A/B
siết-nhầm trên corpus 96 lượt thật của tester: `27/96` cả hai bản, delta = 0.

- **Lý do BÁC BỎ phương án khác:** vá riêng lẻ từng ca (thêm "toàn bộ" vào
  danh sách F-24, thêm biến thể "được" vào mỏ neo O2, thêm "mã riêng" vào O1)
  — đã BỊ BÁC BỎ ở F-27 với lý do còn nguyên giá trị: đó là đập chuột, danh
  sách liệt kê tay luôn thiếu đúng chữ người ta sắp gõ tiếp theo. Sửa lớp một
  lần rẻ hơn sửa lẻ mãi mãi.

### Quyết định 2 — O4 CỐ Ý đứng ngoài Luật 18

`_O4_DONG_TU/_O4_TIEN/_O4_HUONG_KHACH` KHÔNG qua `khop_cum` — vẫn khớp theo
ranh giới từ đơn, có thứ tự (`_vi_tri_dau`). O4 là nhóm từng chặn nhầm nhiều
nhất trong lịch sử bộ lọc (4/5 ca chặn nhầm còn lại của đợt trước đều do một
chữ, "hoan" lọt vào giữa "khoang"). Nới độ rộng cụm ở đúng nhóm mỏng nhất là
tăng rủi ro chặn nhầm ở nơi không đủ ngân sách chịu thêm sai số — đây là quyết
định có chủ đích, không phải bỏ quên retroactive.

- **Lý do BÁC BỎ:** áp Luật 18 máy móc cho mọi mẫu cụm không phân biệt ngữ
  cảnh là đúng thứ đã gây ra F-23 (nới một chỗ, quên đo tác dụng phụ ở chỗ
  khác). O4 xứng đáng một ngoại lệ có ghi lý do hơn là một lần nới không đo.

### Quyết định 3 — Mỏ neo QUY TRÌNH: hai điều kiện đồng thời, ngưỡng riêng

`dem_mat_do_quy_trinh()` bật khi **(B) có** dấu hiệu trình-bày-thành-quy-trình
(`quy trình` · `các bước` · `gồm:` · `trình tự` · `bước 1`/`thứ nhất` · `mình
được hướng dẫn` · `quy định của mình` · cặp `đầu tiên … sau đó`) **VÀ (A) ≥ 2**
trong 7 mỏ neo BƯỚC (`buoc_phan_loai` … `buoc_chuyen_nguoi_that`). KHÔNG đếm
như họ nguyên-tắc (ngưỡng 3, không cần điều kiện B): các BƯỚC là thứ agent nói
ra HỢP LỆ HÀNG NGÀY khi báo cho khách nó đang làm gì ("mình sẽ tra cứu rồi tạo
hồ sơ" = 2 bước, phải luôn im). Phân biệt không nằm ở việc NHẮC một bước, mà ở
việc TRÌNH BÀY CHUỖI BƯỚC như một quy trình — nên cần (B) làm điều kiện lọc,
và ngưỡng (A) hạ xuống 2 vì (B) đã gánh một phần việc lọc.

Hai họ (nguyên-tắc, quy-trình) đếm **riêng** — ngưỡng khác nhau, trộn chung
một con số sẽ mất khả năng biết bộ đếm mù họ nào, đúng lỗi vừa phải sửa. Ghi
CHUNG một khoá `thread_signals` theo `thread_id`, vì mục đích là phát hiện
*một hội thoại đang moi chỉ thị*, không phân biệt moi kiểu nào. **VẪN CHỈ
ĐẾM, KHÔNG CHẶN** — quyết định O2 gốc (`quyet-dinh-O2-lo-chi-thi.md`) giữ
nguyên.

### Quyết định 4 — cắm bộ đếm vào đường chạy thật + trả qua envelope

Phát hiện ngoài phạm vi việc được giao: `dem_mat_do_liet_ke` **chưa từng có
call site nào ở đường chạy thật** trước bản này — chỉ `tests/` và `eval/`.
Mệnh đề *"O2 đếm trước, nâng lên chặn khi có rò"* — nền của quyết định
không-chặn — tới giờ **rỗng trong production**. Không phải vì mỏ neo thiếu, mà
vì bộ đếm chưa cắm điện.

`src/agents/graph.py` gọi `tin_hieu_lo_chi_thi(reply, thread_id=...)` trên
`reply` GỐC (không phải `reply_da_loc`) — mật độ liệt kê là tín hiệu về HÀNH VI
của agent, độc lập với việc O1-O4 có chặn câu đó hay không; trộn hai thứ sẽ
làm phân phối mật độ mù chính câu bị thay bằng `CAU_AN_TOAN`. Kết quả trả qua
**trường envelope mới `tin_hieu_lo_chi_thi: {"nguyen_tac": N, "quy_trinh": M}`**
(BỐN trường chẩn đoán, cùng họ với `loc_dau_ra`/`ly_do_fallback`/`tool_calls:
null`) — không chỉ ghi Redis, vì `eval/` gọi thẳng `graph.py`, `logging_config`
chưa từng khởi tạo, và Redis là fakeredis per-process: bộ đếm vô hình với
người đo nếu chỉ ghi Redis. Additive: không đổi `reply`, không đổi
`loc_dau_ra`, không đổi quyết định chặn.

- **Hệ quả:** `src/agents/phrase_match.py` (mới) · `src/agents/output_filter.py`
  (Luật 18 cho O1/O2/O3/mỏ-neo-nguyên-tắc + mỏ neo quy-trình +
  `tin_hieu_lo_chi_thi()`) · `src/agents/tools/customer_tools.py` (Luật 18 cho
  tier-1/tier-2 F-24) · `src/agents/graph.py` (gọi bộ đếm, trường envelope
  mới). KHÔNG chạm `contracts/` — additive, không đổi hình dạng quyết định.

---

## ADR-024 — `resolutions.note` + `note_flagged`: ghi chú từ chối, scrub tại điểm ghi, ép ở tầng DB

- **Ngày:** 2026-08-15 · **Trạng thái:** ĐÃ KÝ — PO thật ("làm hết đi, hoãn làm
  chi"). Contract v2.4.0 → v2.5.0, INV-17.
- **Bối cảnh:** `reject_reason='khac'` đã được tài liệu hoá từ ADR-019 là "BẮT
  BUỘC kèm ghi chú tự do" nhưng chưa từng có cột nào chứa ghi chú đó — 13 test
  đối kháng (`tests/test_api/test_reject_note_doi_khang.py`, viết TRƯỚC từ đặc
  tả `docs/security/review-phase01-ap-that.md` §Nhiệm vụ 2, TM-03) đứng đỏ chờ.
  Khi bắt tay implement, phát hiện một báo cáo sai của chính phiên này: `note`
  từng được cho là "cột đã có sẵn" (nhầm với `agent_note` của `InvestigationLog`
  — khác bảng, khác mục đích, chỉ trùng tên biến). Xác nhận lại: cột không tồn
  tại trên `Resolution`, và vì test đòi CHECK-constraint có điều kiện (giống hệt
  hình dạng BR-11), đây là thay đổi contract thật, đi qua CLAUDE.md §3.
  `note` là chỗ DUY NHẤT trong hệ thống nơi văn bản tự do do NHÂN VIÊN gõ đi
  vào cùng bản ghi với dữ liệu kiểm toán, ngay cạnh phễu học Phase 2 — ba rủi
  ro chồng lên nhau: (1) PII thật của khách bị chép tay vào, (2) payload
  injection nằm chờ được nhặt vào bộ học, (3) rò ngược ra phía khách nếu route
  nào lỡ trả field mới.

### Quyết định 1 — `note`: Text NULLABLE, CHECK bắt buộc có nội dung khi `reject_reason='khac'`

`ck_resolutions_note_bat_buoc_khi_khac` — đối xứng `ck_resolutions_
rejected_requires_reason_br11` (INV-14/ADR-019): ép ở TẦNG DB, không chỉ ở
route. Giới hạn 500 ký tự (`test_06`, kiểm cả hai mép 500/501).

- **Lý do BÁC BỎ validate-chỉ-ở-route:** đúng bài học ADR-019 lặp lại — một
  route mới hoặc một UPDATE viết thẳng SQL bỏ qua application layer thì
  validate-ở-route không bảo vệ được gì. CHECK constraint là lớp phòng thủ
  không ai lách qua được kể cả khi quên gọi hàm validate.

### Quyết định 2 — `note_flagged`: Boolean, tái dùng Luật 18 (ADR-023), không viết mẫu injection mới

Route reject gọi lại `_phan_loai_tier()` đã có trong `customer_tools.py` —
`note_flagged=true` khi `note` khớp tier-1 hoặc tier-2. Không viết pattern
injection riêng cho field này.

- **Lý do BÁC BỎ mẫu injection riêng:** hai bộ mẫu song song cho cùng một lớp
  tấn công (chỉ thị giả danh) sẽ trôi khỏi nhau ngay từ lần sửa đầu tiên — một
  bên vá, một bên quên, đúng kiểu lỗi lớp mà ADR-023 vừa dọn. Dùng lại một
  nguồn sự thật duy nhất.

### Quyết định 3 — scrub PII TẠI ĐIỂM GHI, fail-closed

Route reject scrub `note` (pipeline hybrid regex+NER dùng chung với
ADR-010/011, không viết pipeline mới) TRƯỚC khi ghi DB. Scrub lỗi (exception)
→ route trả 500, KHÔNG BAO GIỜ ghi bản thô rồi định che sau.

- **Lý do BÁC BỎ "ghi thô, che khi trả về API":** đã bị `_note_trong_db()`
  trong bộ test loại trừ triệt để — test đọc THẲNG DB, không qua response API,
  chính vì "sạch ở response, thô ở DB" là kiểu hỏng nguy hiểm nhất: bản thô nằm
  trong mọi bản sao lưu, mọi câu truy vấn vận hành, mọi lần ai đó mở pgAdmin.
- **Lý do BÁC BỎ "che nhầm còn hơn để lọt" kiểu nới rộng bừa:** giữ đúng đánh
  đổi đã chốt ở checklist observability — chấp nhận che nhầm mã 12 số trùng
  pattern CCCD (`test_03`) hơn là nới regex hẹp lại để giảm false positive.

### Quyết định 4 — ranh giới đọc: KHÔNG mở rộng, chỉ route đã gated `cskh,supervisor`

Không thêm route mới, không đổi `authority-matrix.yaml`. `note` xuất hiện ở
đúng những nơi CSKH/supervisor đã đọc được ticket detail hôm nay; không xuất
hiện ở route khách gọi được (`test_11`), không lọt vào bất kỳ tool nào AI/LLM
đọc — cả đường REST lẫn đường `build_customer_tools().invoke()` trực tiếp
(`test_10`, đúng ràng buộc cứng 2: AI gọi tool dưới danh nghĩa customer).

- **Hệ quả:** `contracts/resolution-state-machine.yaml` v2.5.0 (INV-17) ·
  `tests/test_invariants.py` (CONTRACT_VERSION bump) ·
  `.claude/state/contract-hashes.json` (baseline, `--update` sau khi ADR ký) ·
  migration mới (`resolutions.note`, `resolutions.note_flagged`) ·
  `src/db/models.py` · route `POST /resolutions/{id}/reject` (`src/api/main.py`).
  KHÔNG chạm nhánh approve, KHÔNG chạm `authority-matrix.yaml`.

---

## ADR-025 — MỘT nguyên tắc, HAI cơ chế cho BỐN cửa văn bản tự do

- **Ngày:** 2026-08-15 · **Trạng thái:** **ĐÃ KÝ TOÀN BỘ** — PO thật duyệt nguyên
  tắc 15/08 ("chốt theo hướng security") và **xác nhận cả 4 con số/lựa chọn**
  cuối ngày 15/08 sau khi đọc giải thích: retention 5 năm · trần 2.000 ký tự ·
  quyền đọc 2 pha · preview-confirm 2 vòng khoá. Con số retention vẫn mang cờ
  "cần tư vấn pháp lý thật xác nhận trước production". Bản dự thảo đã qua phản
  biện security (`f6dedfa`) + 2 vòng sửa số (bound 4.000→40.000→12.000, cửa sổ
  [10.764…26.764]). Nền tảng kỹ thuật: hồ sơ security
  `docs/security/2026-08-15-co-che-cho-bon-cua-dau-vao-adr-025.md` (`6f18c9d`).
- **Bối cảnh:** hệ thống có BỐN cửa văn bản tự do với ba lớp phòng vệ lệch nhau
  (bảng đo đủ 4 chiều tại STATE 15/08): `messages.content` (mã hoá, không scrub) ·
  `complaints.description_raw` (KHÔNG gì cả — 20.000 ký tự nhận trọn, plaintext) ·
  `resolutions.note` (scrub nhưng **chặn nhầm 40%**, đổi nghĩa câu im lặng — S-01) ·
  `investigation_logs.agent_note` (không gì cả — S-02). Vá từng cửa riêng lẻ = che
  ô này hở ô kia; áp scrub-lúc-ghi cho cả bốn = nhân bản lỗi 40% vào lời khai khách.

### Quyết định 1 — Trục phân loại là BẰNG CHỨNG, không phải ai-gõ

**Nhóm A (lời khai — bằng chứng):** `description_raw` + `messages.content`. Khách
không sửa lại được; là căn cứ giải quyết tranh chấp tiền. **BÁC che-lúc-ghi** —
hệ thống tự sửa chữ trong lời khai thì bản ghi mất giá trị chứng cứ (NHNN/toà).
Cơ chế: mã hoá at-rest + trần độ dài + siết đọc need-to-know + retention + che
**lúc XUẤT** (log/trace/export — chỗ `scrub_pii` được viết ra, vì bản gốc còn).

**Nhóm B (ghi chú thao tác):** `note` + `agent_note`. Nhân viên đang ngồi trước
màn hình, sửa lại được. Che-lúc-ghi ĐƯỢC nhưng phải **FAIL-VISIBLE** (Quyết định 4).

### Quyết định 2 — Nhóm A: quyền đọc need-to-know, triển khai HAI PHA (sửa sau phản biện `f6dedfa`)

Hướng: `cskh` chỉ đọc transcript/description của ticket mình phụ trách; `supervisor`
theo vai. Căn cứ chuẩn EU/US: GDPR Art 25+32 (least privilege by design) · PCI DSS
Req 7 (need-to-know) · ISO 27001 A.5.15/18 · SOC 2 CC6.

**⚠️ Phản biện security (chấp nhận): "ticket mình phụ trách" CHƯA TỒN TẠI trong mô
hình dữ liệu** — `Ticket` chỉ có `assigned_role` (một VAI), không có `assigned_to`
(một NGƯỜI); thứ duy nhất gắn người là `ChatSession.claimed_by` (phiên chat, không
phải ticket). ⟹ đây là **TÍNH NĂNG NGHIỆP VỤ MỚI** (cột phân công + quy trình),
không phải đổi guard — chi phí thật cao hơn, ghi rõ để không trượt lịch rồi cắt xén.

**Triển khai hai pha:**
- **Pha 1 (rẻ, làm trước):** GIỮ đọc-theo-vai như hôm nay **nhưng thêm audit-log
  cho MỌI lượt đọc nhóm A — mọi chủ thể, kể cả `cskh` trên ca của mình** (PCI DSS
  Req 10 + SOC 2 CC6: rủi ro nội gián lớn nhất là người có quyền hợp lệ; log theo
  mọi chủ thể, không theo cấp).
  **MỞ RỘNG PHẠM VI Pha 1 (bổ sung sau ký, finding security `7f66fb1`, PO-agent
  quyết theo uỷ quyền — không đổi cơ chế, chỉ thêm bề mặt được log):** audit-log
  phủ thêm **mọi lượt đọc endpoint trả `tool_result.raw_json`** (timeline điều
  tra / ticket detail, `main.py:744-751`). Lý do: BR-06 không che chính chủ ⟹
  payload timeline chứa SĐT/STK/họ tên THẬT của khách-chính-chủ; nếu chỉ log
  nhóm A thì sinh **nghịch lý** — đọc transcript CÓ log, đọc dữ liệu có-cấu-trúc
  nhạy hơn qua timeline thì KHÔNG ⟹ kẻ moi dữ liệu chọn đúng cửa không log.
  Log ở MỨC ENDPOINT (payload nằm trong response bất kể expander có mở hay
  không, log-mở-expander là không đủ).
- **Pha 2 (tính năng phân công):** thêm `assigned_to` + quy trình phân công + siết
  đọc theo người. Kèm ba quyết định bắt buộc: **(a) break-glass có kiểm soát** —
  CSKH trực đêm mở được ticket người khác, kèm lý do bắt buộc + cờ cho supervisor
  review (không có đường thoát có-audit thì đội sẽ phân-công-tất-cả-cho-tất-cả,
  quyền đọc quay về như cũ nhưng thêm một lớp TRÔNG-như-đã-siết — tệ hơn hiện
  trạng); **(b)** audit phủ mọi lượt đọc (đã ở Pha 1); **(c)** ticket **chưa phân
  công** mặc định đọc theo `assigned_role` như hôm nay — chuyển dần, không lật công tắc.

### Quyết định 3 — Retention: đề xuất 5 NĂM kể từ đóng ticket, kèm cờ pháp-lý

Đề xuất: hồ sơ khiếu nại (transcript + description + note + agent_note gắn ticket)
giữ **5 năm kể từ ticket đóng**, hết hạn thì xoá hoặc ẩn danh hoá không đảo ngược.
Căn cứ lấy MAX của các chế độ áp dụng: VN — Luật PCTT rửa tiền 2022 giữ hồ sơ giao
dịch/KYC **5 năm**; NĐ 13/2023 nguyên tắc giới hạn lưu trữ theo mục đích. EU —
AMLD/CDD **5 năm** sau chấm dứt quan hệ; JC 2018/35 (EBA/ESMA complaints-handling)
buộc đăng ký lưu hồ sơ khiếu nại; MiFID II 5 năm. US — Reg E 12 CFR 1005.13 giữ
bằng chứng tuân thủ + hồ sơ điều tra lỗi **tối thiểu 2 năm** (sàn, không trần).
⚠️ **Cờ giữ nguyên từ security:** con số này cần **tư vấn pháp lý thật xác nhận**
trước production (đối chiếu thời hiệu khiếu nại TT 40/2024) — đề xuất để hệ thống
có một con số ĐÚNG HƯỚNG thay vì không có gì, không phải để thay luật sư.
⚠️ **Khi tới lúc xoá (bẫy security ghim trước): KHÔNG dùng crypto-shredding** —
`FIELD_ENCRYPTION_KEY` là khoá DÙNG CHUNG (`messages.content` + `PolicyChunk` +
`bank_accounts.account_no`); huỷ khoá để xoá một ticket = phá toàn bộ dữ liệu mã
hoá của hệ thống. Xoá theo retention phải là **xoá dòng thật**.

### Quyết định 4 — Nhóm B: FAIL-VISIBLE bằng vòng xác-nhận + HAI VÒNG KHOÁ (sửa sau phản biện `f6dedfa`)

Nhân viên lưu ghi chú → hệ thống hiện **bản ĐÃ che** cho chính họ xác nhận/sửa
trước khi ghi DB (preview-confirm). Che sai → người thấy ngay tại chỗ — chặn đúng
lỗi "40% đổi nghĩa im lặng" của S-01 bằng con người, không bằng nới regex. Bản
ghi mang cờ đã-qua-che + số vị trí thay thế (audit). Scrub engine ném exception
→ 500, KHÔNG ghi bản thô (giữ ADR-024 QĐ 3). Căn cứ: GDPR Art 5(1)(d) accuracy +
toàn vẹn audit-trail SOC 2.

**HAI VÒNG KHOÁ bắt buộc** (security tự bắt lỗ trong hồ sơ gốc của chính họ —
`6f18c9d` viết thiếu, phản biện bổ sung):
1. **Server PHẢI scrub lại ở bước GHI, luôn luôn** — không bao giờ tin văn bản
   client gửi ở bước confirm. Luồng preview→confirm→ghi mở đúng một cửa TOCTOU:
   client gửi bản THÔ ở bước confirm, server tưởng "đã che rồi" ghi thẳng.
   **Preview là GIAO DIỆN, không bao giờ là LỚP TIN CẬY.**
2. **Văn bản nhân viên SỬA phải qua scrub LẠI TỪ ĐẦU** — còn khớp thì hiện lại
   preview; **không có đường "xác nhận lần hai để bỏ qua"**. Người sửa được CÁCH
   DIỄN ĐẠT, không sửa được KẾT QUẢ scrub. Thiếu vòng này thì preview-confirm
   biến từ "làm phép che nhìn thấy được" thành "cho nhân viên TẮT phép che" —
   ngược hẳn mục đích S-01.

### Quyết định 5 — A2: trần 2.000 ký tự ở SCHEMA; CHECK DB là CHỐNG-FLOOD THUẦN (sửa sau phản biện `f6dedfa`)

Trần nghiệp vụ **2.000 ký tự** (≈300-400 từ — đủ tường thuật chi tiết, chặn flood
20.000) ép ở **schema Pydantic `max_length=2000`** — chỗ DUY NHẤT diễn đạt được
trần theo ký tự. CHECK ở DB giữ vai **chống-flood thuần, đặt RỘNG: `length <=
40.000` trên ciphertext** — hai lớp HAI MỤC ĐÍCH, lớp dưới KHÔNG bắt chước lớp
trên bằng đơn vị nó không diễn đạt được.

**⚠️ Con số CHỐT = 12.000, và ADR này ghi CỬA SỔ chứ không ghi một con số trần
trụi — vì con số này đã sai HAI LẦN theo cùng một cách (Luật 8 lần bốn VÀ lần năm):**
- Lần 1: bound 4.000 (coder đo mẫu GẦN-ASCII) → security bác: tiếng Việt đủ dấu
  3 byte/ký tự ⟹ 2.000 ký tự → 8.100 ciphertext, VƯỢT 4.000 ⟹ khách viết đủ dấu
  dính `IntegrityError` → 500 giữa lúc khiếu nại (hình dạng F-21).
- Lần 2: bound 40.000 (PO-agent chốt theo phản biện) → coder bác bằng đo:
  **40.000 ≈ 28.943 ký tự ASCII lọt qua** ⟹ flood 20.000 ASCII — đúng ca A2 sinh
  ra để chặn — **đi thẳng qua tầng DB**.
Mỗi lần mẫu rộng ra, tiền đề con số trước bị rút chân. Thoát vòng = nêu **CỬA SỔ
hợp lệ kèm CẢ HAI MÉP** (đo Fernet thật, 2.000 ký tự mỗi loại):
```
mép DƯỚI ≥ 10.764  (2.000 ký tự EMOJI 4-byte — ca phải-nhận rộng nhất)
mép TRÊN ≤ 26.764  (20.000 ký tự ASCII — ca phải-chặn hẹp nhất)
```
**Chọn 12.000** — sát mép dưới, vì đây là lưới chặn cuối: càng chặt càng tốt miễn
không chặn nhầm. Verify chạy thật: 2.000 ASCII/VN-đủ-dấu/emoji đều QUA (3 ca đối
chứng, gồm A2-05) · 5.000/8.000/20.000 đều CHẶN. Migration ghi cả cửa sổ + lý do
hai mép, để lần đổi số sau phải đo lại CẢ HAI mép chứ không một trục.

### Lý do BÁC BỎ các phương án khác
- **Scrub-lúc-ghi cho cả bốn cửa** — nhân bản lỗi 40% vào lời khai; lời khai bị
  sửa chữ mất giá trị chứng cứ; và ở `messages.content` lớp at-rest đã chạy thật
  (kiểm bằng byte) — đổi giá trị chứng cứ lấy một mức giảm thiểu nữa là đánh đổi tồi.
- **Đọc-theo-vai giữ nguyên** — trái need-to-know (GDPR 25/32, PCI DSS 7); mọi
  nhân viên đọc mọi lời khai là chính cái ST2-P0-3 §3 gọi tên.
- **Không trần, chỉ mã hoá** — flood 20K ký tự vẫn vào; trần là lớp rẻ nhất.

### Hệ quả (khi số được xác nhận)
Coder: `messages`/`complaints` route đọc theo phụ trách + audit-log đọc ·
`description_raw` = `EncryptedText` (A1 ĐÃ LAND, chờ probe) + trần 2 lớp (A2) ·
B1/B2 preview-confirm cho `note` → rồi B3 áp sang `agent_note` (thứ tự bắt buộc:
B3 đi SAU, tránh nhân bản lỗi im lặng). Tester: trục đối chứng "căn cứ còn sống
sót" (ngưỡng 0/20, corpus security xuất file) làm gate cho mọi thay đổi scrub.
Security: probe từng bản vá trước khi đóng. Contract: nếu cần mục mới trong
`resolution-state-machine.yaml` → qua đúng quy trình §3, CONTRACT_VERSION bump.
Retention: chờ xác nhận pháp lý trước khi code job xoá tự động.

---


## ADR-026 — Kho RAG chỉ phục vụ tài liệu ĐÃ DUYỆT; duyệt là hành vi riêng của `supervisor`

- **Ngày:** 2026-08-16 · **Trạng thái:** Đang hiệu lực — PO thật chốt 16/08/2026 (quy trình §3: ADR trước, code sau)
- **Bối cảnh:**

  16/08, cửa sổ `08:23:14Z → 08:42:47Z` (19 phút 33 giây), hai file nội bộ —
  `business_rules.md` (bảng số `verified=false`) và
  `scenario-candidates-momo-faq.md` (danh sách kịch bản test) — nằm trong **kho
  đang phục vụ**. Đo được: **0 request hướng khách** trong cửa sổ ⟹ không thiệt
  hại tới khách; phơi nhiễm giới hạn ở `/policy-search` (endpoint nhân viên,
  **cố ý** không lọc — Y5). Truy nguồn đã đóng: **người vận hành upload qua
  đúng màn hình Đối-tác-ví** — tai nạn quy trình, không phải xâm nhập.

  **Câu hỏi đầu tiên của người vận hành khi được báo là:** *"đối tác ví có
  luồng upload riêng là đã quản lý được phần này rồi đúng không?"*

  **Niềm tin đó sai, và sai theo cách rất tự nhiên.** Tách vai `partner_admin`
  kiểm soát **AI ĐƯỢC PHÉP LÀM GÌ**; nó **không** kiểm soát **CÁI GÌ TRỞ THÀNH
  CHÍNH SÁCH**. Một vai riêng cho việc nạp *trông* y hệt cơ chế quản trị nội
  dung, nhưng nó chỉ là cơ chế **phân quyền**. Người đầu tiên vấp vào khoảng
  trống đó là **một người thiện chí, dùng đúng cửa được thiết kế cho họ, không
  làm sai quy trình nào** — đó là định nghĩa của khoảng trống thiết kế, không
  phải lỗi người dùng.

  ⟹ ADR này **tách hai thứ vốn bị gộp**: *ai được nạp* (phân quyền — đã có) và
  *cái gì được phục vụ* (duyệt nội dung — **chưa có**).

### Quyết định 1 — Agent chỉ được phục vụ chunk của tài liệu `da_duyet`

Lọc ở **tầng serve**, trong truy vấn SQL đã có của `search_policy_text`.

- **Lý do:** đo được (`d578d0d`) — `search_policy_text` vốn chạy hai bước
  (Chroma → SQL join `PolicyDocument`), nên lọc là **một mệnh đề thêm vào truy
  vấn đã có**: **không đụng Chroma, không nhúng lại 378 chunk**, và đi theo
  đúng khuôn `if chunk is None: continue` **đã tồn tại và đã chạy**. Chi phí
  recall = **0** ở vận hành bình thường (mọi tài liệu đã duyệt thì không bỏ gì).
- **Lý do BÁC "chặn ở tầng nạp là đủ":** có **ba** call-site `ingest_document`
  (API `main.py:1195` · `kho_rag.py:244` · `run_adversarial_set.py:57`), và sự
  cố đi qua **cửa hợp lệ nhất trong ba**. Một cổng ở tầng nạp phải được thực
  thi ở **mọi** đường — kể cả đường mà **công dụng của nó là đi vòng qua cổng**
  (`_ingest_malicious_policy`).

### Quyết định 2 — Duyệt là hành vi RIÊNG, do `supervisor`, SAU khi nạp

Mọi upload — **kể cả `partner_admin`, kể cả cửa hợp lệ** — vào `cho_duyet`;
`supervisor` duyệt → `da_duyet`.

- **Lý do:** đây là **maker ≠ checker** (ADR-020/BR-12) mở rộng nhất quán từ
  *tiền* sang *tri thức*. `supervisor` đã là "quyết định cuối, mọi phạm vi" ⟹
  **không mở role mới, không đổi hiến pháp**.
- **Lý do BÁC "`partner_admin` tự duyệt":** tái tạo sự cố bằng **một cú click**.
  Người nạp không được tự duyệt — đúng nguyên tắc đã ép ở tầng DB cho tiền.

### Quyết định 3 — Ai thấy tài liệu CHƯA duyệt

| Vai | Thấy? | Lý do |
|---|---|---|
| `agent` | **KHÔNG** | toàn bộ mục đích của cơ chế |
| `partner_admin` | CÓ | để quản tài liệu mình nạp |
| `cskh` / `supervisor` | **CÓ, kèm huy hiệu «CHƯA DUYỆT» trên TỪNG kết quả** | giữ **Y5**: người là máy dò tài liệu độc — đúng cơ chế **đáng lẽ đã bắt sự cố này sớm hơn** |

- **Ràng buộc:** huy hiệu phải **sống qua lớp hiển thị** — cùng ràng buộc với
  dấu che ở UI-01 (*"lớp hiển thị không được làm đẹp mất dấu"*). **Một badge bị
  nuốt còn tệ hơn không có**, vì nó tạo cảm giác đã-kiểm.

### Quyết định 4 — Backfill 2 tài liệu hiện có thành `da_duyet`

`MoMo_FAQ_Giao_dich.docx` + `MoMo_ToS.docx` — đã qua thực chiến, là nguồn đo
benchmark. Bắt duyệt lại là **nghi thức rỗng**.

- **Ràng buộc:** backfill phải **ghi lại ai quyết và lúc nào** — đây là
  backfill **có chủ đích**, không phải mặc định im lặng. Cùng tinh thần A1-04:
  *không-làm-gì phải là quyết định ghi ra, không phải hệ quả im lặng*.

### Quyết định 5 — Đường EVAL đánh dấu tài liệu của nó là ĐÃ DUYỆT

- **Lý do:** mô hình đe doạ của bộ đối kháng là **"đối tác upload tài liệu độc
  / bị chiếm tài khoản"** — trong kịch bản đó tài liệu **đúng là đã qua cửa
  duyệt**. Đánh dấu nó "chưa duyệt" khiến bộ đối kháng test một ca **dễ hơn**
  mối đe doạ thật.
- **Lý do BÁC "cờ bỏ-qua-lọc khi đang test":** một công tắc tắt-phòng-vệ trong
  mã sản phẩm là lớp lỗi **F-30** — bật bằng một biến môi trường, **không để
  lại vết trong git**, không ai trong quy trình review thấy.

### 🔴 Quyết định 6 — Xuất-xứ KHÔNG thay thế lọc tier. Hai cơ chế cùng tồn tại.

| | Chống | KHÔNG chống |
|---|---|---|
| **Nguồn-đã-duyệt** (ADR này) | tài liệu vào kho **sai cửa / chưa ai duyệt** | tài liệu **đã duyệt** mà **nội dung độc** |
| **Lọc tier + spotlighting** (F-22/F-25/F-28) | nội dung độc **bên trong** tài liệu, bất kể nguồn | tài liệu vào kho sai cửa |

Ghi thành quyết định **riêng** vì đây là chỗ **chắc chắn** sẽ có người hiểu sai
và đi gỡ một trong hai. Sự cố 16/08 là ô **thứ nhất**; ADV-005 (agent lặp lại
chỉ thị độc từ policy doc) là ô **thứ hai**.

### 🔴 Quyết định 7 — Nạp lại kho PHẢI giữ nguyên trạng thái duyệt

`scripts/kho_rag.py` giữ `trang_thai_duyet` khi `(filename, băm nội dung)`
không đổi. Nội dung đổi ⟹ về `cho_duyet`.

- **Lý do — đây là ràng buộc BẮT BUỘC, không phải chi tiết triển khai:** nếu
  **mọi** lần nạp đều vào `cho_duyet` thì nạp-lại-kho (thao tác **bảo trì
  thường quy**) sẽ đẩy toàn bộ về chưa-duyệt ⟹ **agent mất sạch khả năng tra
  chính sách** cho tới khi có người bấm duyệt.
- **Không phải giả định:** chính lượt nạp lại `08:42:47` là thứ **đã sửa** sự
  cố. Nếu ADR này đang hiệu lực theo bản đơn giản, **bản vá đó sẽ làm agent
  mù**, và không ai biết cho tới khi khách hỏi chính sách. **Một cơ chế an toàn
  tự tạo ra một sự cố khả dụng là một cơ chế hỏng.**

### Quyết định 8 — HAI TẦNG, xếp theo thời gian

- **Tầng 1 — danh mục tĩnh `contracts/rag-nguon.yaml`, LÀM NGAY.** Đóng đúng
  lớp sự cố **hôm nay**: không cần UI, không cần luồng mới, và **cổng của
  tester đã viết sẵn** (`55118b5`, hiện `xfail(strict)` — gỡ khi file tồn tại).
  Nó là **dây bẫy phát hiện kho trôi**, không phải cơ chế quản trị.
- **Tầng 2 — trạng thái duyệt trong DB (QĐ 1–4, 7), làm khi có onboarding đối
  tác thật.** Đây mới là cơ chế sản phẩm.
- **Lý do làm cả hai:** chúng trả lời **hai câu khác nhau** — *"kho có đúng thứ
  ta chủ ý đưa vào không"* (tầng 1) và *"tài liệu này đã được người có thẩm
  quyền duyệt chưa"* (tầng 2). **Tầng 1 vẫn đúng SAU KHI có tầng 2.**
- **Lý do BÁC "chỉ làm tầng 1":** danh mục **tên file** sẽ chặn nhầm ngay khi
  có đối tác thật upload — không dùng được làm cơ chế sản phẩm.
- **Lý do BÁC "chỉ làm tầng 2":** nó cần **UI duyệt + luồng supervisor** =
  phạm vi sản phẩm thật, trong khi lớp sự cố đang hở **hôm nay**.

### Hệ quả

- `contracts/rag-nguon.yaml` (**tầng 1**, khoá `nguon_duoc_duyet`) · gỡ
  `xfail(strict)` ở `55118b5` · `CONTRACT_VERSION` bump + `--update` baseline.
- `PolicyDocument` thêm `trang_thai_duyet` · `duyet_boi` · `duyet_luc` +
  migration + **backfill 2 dòng có ghi người quyết**.
- `ingest_document` thêm **`nguon_nap`** — **default `"khong_ro"`** (⚠️ **KHÁC**
  bài học F-17 một cách có chủ đích: ở F-17, default làm bộ lọc **thoái hoá im
  lặng**; ở đây default `"khong_ro"` **tự tố cáo** đường chưa khai. Luật đúng
  là *default phải là giá trị DỄ THẤY nhất, không phải tiện nhất*).
- `search_policy_text` — thêm mệnh đề lọc `da_duyet`.
- `scripts/kho_rag.py` — **QĐ 7** (giữ trạng thái duyệt theo `(filename, băm)`).
- UI: màn duyệt cho `supervisor` · badge «CHƯA DUYỆT» ở `/policy-search`.

### Điều ADR này KHÔNG làm

- **Không** chặn tài liệu **đã duyệt nhưng nội dung độc** — việc của lọc tier
  (QĐ 6).
- **Không** có số về chi phí vận hành luồng duyệt khi có đối tác thật — chưa có
  đối tác thật để đo.
- **Chưa probe.** Khi coder land, security probe theo nếp: ca **dương tính**
  (doc chưa duyệt → agent **không** thấy) **cùng** ca **đối chứng** (doc đã
  duyệt → agent **vẫn** thấy đủ, recall không tụt) — **cấm chạy lẻ** (Luật 2).

---

## Phụ lục — đề xuất nội dung `contracts/rag-nguon.yaml`

> Vùng `contracts/` là của tech-lead sau khi PO duyệt. Đây là **đề xuất**, khoá
> đặt theo đúng thứ chuỗi xfail `55118b5` đang dò (`nguon_duoc_duyet`).

```yaml
# Danh mục nguồn ĐƯỢC PHÉP có mặt trong kho RAG phục vụ khách (ADR-026 tầng 1).
# Đây là DÂY BẪY phát hiện kho trôi, KHÔNG phải cơ chế quản trị nội dung —
# cơ chế đó là trang_thai_duyet ở tầng DB (ADR-026 tầng 2).
version: 1
nguon_duoc_duyet:
  - ten_file: MoMo_FAQ_Giao_dich.docx
    mo_ta: FAQ giao dịch — nguồn chính sách vận hành cho khách
  - ten_file: MoMo_ToS.docx
    mo_ta: Điều khoản dịch vụ — phần ràng buộc pháp lý
# Mọi tài liệu KHÁC xuất hiện trong kho phục vụ = kho đã trôi khỏi chủ đích.
# Thêm dòng ở đây là một QUYẾT ĐỊNH, phải qua review như mọi thay đổi contract.
```

---

## ADR-027 — Contract phải khai LƯỢC ĐỒ tool, và bộ kiểm phải so lược đồ chứ không chỉ so TÊN

- **Ngày:** 2026-08-17 · **Trạng thái:** Đang hiệu lực — PO thật chốt 17/08/2026 (quy trình §3: ADR trước, code sau)
- **Bối cảnh:**

  Tester dựng lại bộ đo gọi-tool bằng cách **introspect app đang chạy** (thay vì
  đọc `contracts/`) và phát hiện lược đồ thật lệch bản khai. Số đo, lấy từ
  `eval/luoc_do_tool_app.json` (băm bản chuẩn hoá `4129d298555c`, commit
  `bc6b3d3`) đối chiếu `contracts/agent-tools.yaml`:

  | tool | mô tả (ký tự) | tham số | bắt buộc | contract khai `input:` |
  |---|---|---|---|---|
  | `lookup_transaction` | 680 | 6 | — | CÓ |
  | `get_customer_history` | 947 | 3 | — | CÓ |
  | **`create_ticket`** | **1266** | **5** | **`complaint_type` · `scope` · `description_raw`** | **KHÔNG CÓ** |
  | `search_policy` | 793 | 1 | `query` | CÓ |
  | `request_human_handoff` | 1176 | 2 | `reason` | CÓ |

  **`create_ticket` không có khối `input:` nào trong contract**, trong khi app
  đòi **ba tham số bắt buộc** — một trong số đó là `description_raw`, tức
  **nguyên văn lời khách gõ**.

  Suốt thời gian đó **`tests/test_invariants.py` xanh 23/23**. Cơ chế introspect
  của nó so **TÊN** tool (và tool bị cấm), **không** so lược đồ. Hiến pháp §3
  hứa *"đổi tên 1 tool ... mà quên cập nhật contract → ĐỎ NGAY"* — lời hứa đó
  đúng theo đúng nghĩa đen của nó, và **người đọc hiểu rộng hơn nghĩa đen**.

  **Ba thiệt hại đã xảy ra, không phải giả định:**
  1. **Tester mất hai lượt đo.** Bộ v1/v2 dựng mô tả tool từ contract ⟹ model
     nhận kích thích lệch **11×–41×** so với sản phẩm. Kết quả không nói gì về
     sản phẩm. (Xem thêm: nó cũng tạo ra cả một cuộc tranh luận về "nhãn ca 4"
     — ba model độc lập cùng từ chối `create_ticket` vì contract mô tả nó bằng
     **31 ký tự và 0 tham số**. Triệu chứng bị điều trị suốt nửa ngày trong khi
     bệnh nằm ở kích thích.)
  2. **Security rà thẩm quyền trên bản khai sai.** Họ rà một tool tưởng như
     không nhận dữ liệu vào, trong khi nó nhận `description_raw` — đúng chỗ PII
     bên thứ ba hay xuất hiện nhất (*"em chuyển nhầm cho anh X, sđt 09…"*).
  3. **Bất kỳ ai đọc contract để hiểu hệ thống** đều đọc một mô tả sai về vật
     chất, chứ không phải lỗi thời chút ít.

  Đây đúng thứ hiến pháp §3 gọi là *"lỗi nghiêm trọng nhất của dự án — nguyên
  nhân khiến tester và security làm việc trên thông tin đã chết"*. Khác biệt
  duy nhất, và là khác biệt làm nó nguy hơn: **cơ chế phát hiện tự động không
  bắt được, nên nó chết âm thầm và không ai được báo.**

- **Quyết định:**

  1. `contracts/agent-tools.yaml` khai **đầy đủ lược đồ** mọi tool: tên trường,
     kiểu, `required`. Sửa cho **khớp app đang chạy** — app là thực tại, contract
     đang sai, nên lần này contract chạy theo app. *(Đây là ngoại lệ có lý do,
     KHÔNG phải tiền lệ: bình thường contract đi trước. Ngoại lệ áp dụng vì bản
     khai chưa bao giờ được ép, nên không có ai từng dựa vào nó mà đúng.)*
  2. `tests/test_invariants.py` mở rộng: so **lược đồ** (tên trường + `required`)
     giữa app và contract, không chỉ so tên tool. Lệch = ĐỎ.
  3. **Mô tả tool (`description`) KHÔNG đưa vào phép so bằng.** Nó là văn bản
     prompt sẽ được sửa thường xuyên trong lúc tinh chỉnh; ép khớp từng ký tự
     sẽ tạo một cổng đỏ liên tục rồi bị người ta học cách bỏ qua — cổng bị bỏ
     qua tệ hơn không có cổng. Thay vào đó contract ghi **một dòng tóm tắt mục
     đích** + con trỏ tới nơi mô tả thật sống.
  4. **Nguồn sự thật cho ai muốn ĐO:** `eval/luoc_do_tool_app.json` sinh bằng
     introspect. Ai dựng kích thích cho model **phải lấy từ đó**, không từ
     contract. Contract khai **CẤU TRÚC**; nó không và không nên khai **NỘI
     DUNG mô tả**.

- **Phương án đã bác:**

  - *Ép khớp cả `description` từng ký tự* — bác, xem §3 trên (cổng đỏ liên tục
    sẽ bị vô hiệu hoá bằng thói quen, không bằng quyết định).
  - *Bỏ khai `input:` khỏi contract cho mọi tool cho nhất quán* — bác: đó là
    làm cho bản khai nhất quán bằng cách **hạ nó xuống mức vô dụng**. Vấn đề
    không phải bốn tool khai thừa, mà một tool khai thiếu.
  - *Chỉ sửa `create_ticket`, không đụng bộ kiểm* — bác, và đây là phần đắt
    nhất của ADR: sửa dữ liệu mà không sửa cơ chế phát hiện thì **lần sau vẫn
    im lặng y hệt**. Bài học chung của ngày 17/08 (năm lỗi cùng họ *"mặc định
    trông hợp lệ"*, bốn vai khác nhau, chưa lần nào do người mắc chăm chú hơn
    mà tìm ra): **lớp lỗi im lặng không phản ứng với sự cẩn thận, chỉ phản ứng
    với cấu trúc.**

- **Hệ quả:**

  - Phải chạy `python scripts/check_contracts.py --update` và cập nhật
    `CONTRACT_VERSION` — **commit kèm file baseline**, nếu không local xanh / CI đỏ.
  - Bộ v1/v2 của tester giữ trong sổ với nhãn *"đo trên kích thích rút gọn,
    không phải kích thích sản phẩm"* — **không xoá**, vì chúng là bằng chứng gốc
    của chính ADR này.
  - Security cần rà lại `create_ticket` với lược đồ đúng, đặc biệt
    `description_raw` trên đường PII bên thứ ba.
  - **Câu hỏi mở, chưa quyết:** còn bộ phận nào khác mà contract khai CẤU TRÚC
    trong khi người đọc tưởng nó khai NỘI DUNG? `authority-matrix` và
    `resolution-state-machine` cần một lượt rà cùng câu hỏi này.

## ADR-028 — Tách `/ready` khỏi `/health`: kho RỖNG và khoá CHẾT đều phải làm đỏ readiness

- **Ngày:** 2026-08-17 · **Trạng thái:** Đang hiệu lực — PO thật chốt 17/08/2026 (quy trình §3: ADR trước, code sau)
- **Bối cảnh:**

  Ngày 17/08 hệ thống rơi vào **hai chế độ hỏng khác nhau**, và `/health` báo **xanh trong cả hai**:

  | | hiện tượng | thời lượng | `docker ps` |
  |---|---|---|---|
  | ① khoá chết | `embed_query` → `401 token_invalidated`, agent **không tra được chính sách nào** | ~1 giờ, 2 stack | `healthy` |
  | ② kho rỗng | `policy_faq` có **0 vector**, trả lời *"không tìm thấy"* cho **mọi** câu | **24 giờ** | `healthy` |

  Tính cả hai lần khoá chết trên hai stack, **`/health` báo xanh giả 4 lần trong một ngày**.

  **Chế độ ② nguy hiểm hơn ① và không ai lường trước.** Khoá chết cho `500` — ồn ào, có người
  nhận ra. Kho rỗng cho **`200` + danh sách rỗng** — agent nói *"không tìm thấy chính sách nào"*,
  một câu **đúng ngữ pháp, hợp lệ về hình thức, và hoàn toàn sai**. Hệ thống **không phân biệt được
  "không có chính sách nào KHỚP" với "tôi không có chính sách nào CẢ"**.

  *(Ghi lại một nhánh đã bị BÁC bằng phép đo: PO-agent từng giả thuyết có tầng nuốt lỗi xác thực
  thành danh sách rỗng. Coder dựng ca đối chứng khoá-sai có kiểm soát trên stack sạch → `store.search`,
  `search_policy_text` và lớp bọc tool **đều nổ `AuthenticationError`, không tầng nào nuốt**. Chế độ
  ② hoàn toàn do **kho rỗng thật**, không do lỗi bị nuốt.)*

- **Quyết định:**

  1. **`/health` GIỮ NGUYÊN là liveness thuần** — không chạm dependency nào. *Đây là điểm dễ làm
     sai nhất:* cho `/health` gọi OpenAI thì mỗi lần nhà cung cấp sập, Docker sẽ **giết và restart
     vòng lặp một container hoàn toàn khoẻ mạnh** — biến sự cố bên ngoài thành sự cố của ta.
  2. **Thêm `GET /ready`** (readiness) — 🔴 **SỬA 17/08 sau khi PO yêu cầu tra thực tiễn ngành:**
     ```
     ĐỎ  (rút khỏi vòng phục vụ)   trạng thái CỤC BỘ của chính instance
                                    · DB không tới được
                                    · kho vector RỖNG  ← local state, đúng loại readiness
     VÀNG (BÁO CÁO, KHÔNG rút)      phụ thuộc NGOÀI
                                    · embedding/LLM không gọi được (khoá chết · hết hạn mức · 429)
     ```
     **Bản đầu của ADR này SAI ở dòng embedding.** Thực tiễn ngành (Kubernetes/SRE) thống nhất:
     **readiness KHÔNG được phụ thuộc dependency ngoài** — nếu nhà cung cấp sập, **MỌI replica cùng
     ĐỎ một lúc**, orchestrator rút hết khỏi vòng phục vụ, và ta **biến một suy giảm thành mất dịch
     vụ toàn phần**. Khuyến nghị chuẩn là **"degraded mode"**: vẫn phục vụ phần làm được, trả 503
     cho phần không làm được, **không tự rút mình ra**.
     ⟹ Điều này **xác nhận điều kiện security đã nêu độc lập** (*"`/ready` được phép BÁO CÁO, KHÔNG
     được phép GATING"*) và **sắc hơn**: ranh giới không phải *"báo cáo hay chặn"* mà **"trạng thái
     CỤC BỘ hay phụ thuộc NGOÀI"**. Kho rỗng là **cục bộ** ⟹ ĐỎ hợp lệ. Nhà cung cấp sập là
     **ngoài** ⟹ báo cáo, không rút.
     *(Nguồn: đồng thuận vận hành Kubernetes/SRE về liveness/readiness probe — "cardinal rule:
     probes must never check external dependencies", "a good compromise is degraded mode".)*
  3. Có **cache TTL** cho kết quả probe để không đốt tiền mỗi lượt gọi.
  4. `/ready` **mở cho mọi role** (kể cả chưa đăng nhập) — nó là endpoint hạ tầng, không trả dữ liệu
     nghiệp vụ. Phải khai trong `authority-matrix.yaml` (INV-00 đòi khớp chính xác `app.routes`).
  5. **GỘP VÀO ĐÂY: nơi phơi tín hiệu VẬN HÀNH cho lỗi nhà cung cấp** (sinh từ bản vá `5ac18bf`).
     Bối cảnh: bản vá đó biến `403/401/5xx` của nhà cung cấp từ **500 trần** thành **câu mềm cho
     khách** — nhưng nó cũng làm sự cố **im hơn**. Coder nêu đúng nghịch lý và tự chặn:
     > **Tester phát hiện hạn mức cạn CHÍNH VÌ lượt đo trả 500. Bản vá land một mình thì lần sau
     > harness ghi "agent đã trả lời" và không ai biết — bản vá làm chính finding sinh ra nó vô hình.**
     ⟹ Trạng thái hiện tại: **hỏng-ỒN đã thành hỏng-CÓ-DẤU-VẾT, CHƯA thành hỏng-CÓ-NGƯỜI-BIẾT.** Ai
     muốn biết phải chủ động mở Jaeger hoặc `grep` log.
     **Vì sao gộp vào ADR-028 thay vì mở ADR riêng:** phơi bộ đếm cần **một route**, mà contract 33
     route **không có route vận hành nào** để bám vào ⟹ thêm route = đổi contract = đúng việc ADR-028
     đang xin duyệt. **Một lần duyệt, một lần đổi contract.**
     ⚠️ **KHÔNG phơi ở `/health`** — nó CÔNG KHAI; đặt `lop_loi_cuoi="AuthenticationError"` ở đó là
     **báo cho người ngoài biết khoá ta đang hỏng**. Tín hiệu vận hành phải nằm sau xác thực, hoặc ở
     `/ready` dạng **có/không** không kèm chi tiết lớp lỗi.
     *(Coder cố ý KHÔNG thêm bộ đếm 5 phút khi chưa có chỗ phơi — theo luật "bản vá không-có-số-lợi
     = revert": một bộ đếm không ai đọc được là code chết.)*

- **Phương án đã bác:**

  - *Cho `/health` chạm dependency thay vì thêm route mới* — bác, xem §1: liveness chạm dependency
    tạo vòng lặp restart khi bên ngoài sập.
  - *Chỉ cảnh báo khi kho rỗng, không làm đỏ* — bác: kho rỗng nghĩa là **mọi** câu trả lời chính sách
    đều sai. Một hệ thống trả lời sai 100% mà vẫn nhận traffic thì cảnh báo không đủ.
  - *Thêm một dòng checklist "nhớ kiểm kho sau khi deploy"* — bác, và đây là lý do có ADR này thay vì
    một dòng tài liệu: **hôm nay đã có 4 lần xanh giả, mỗi lần đều có người làm đúng quy trình.**
    Sau lần thứ ba PO-agent đã ghi *"lần thứ ba thì sửa chính cái đèn, không sửa checklist nữa"*.

- **Hệ quả:**

  - Đổi `contracts/authority-matrix.yaml` ⟹ `check_contracts.py --update` + bump `CONTRACT_VERSION`
    + **commit kèm file baseline**.
  - Deploy/monitoring phải trỏ readiness vào `/ready`, **không** vào `/health`.
  - **Nghiệm thu bắt buộc bằng ca âm bản:** làm rỗng kho trên stack thử → `/ready` phải ĐỎ. Không
    chấp nhận nghiệm thu chỉ bằng đường xanh — chính đường xanh là thứ đã nói dối 4 lần.
  - Việc này **không** đóng chế độ hỏng gốc ở tầng sản phẩm: agent vẫn nên phân biệt được
    *"không khớp"* với *"không có kho"* khi trả lời khách. `/ready` chặn ở tầng hạ tầng; tầng agent
    là việc riêng, chưa xếp lịch.

## ADR-029 — `scope` phải là `unknown` khi không tra ra, và contract phải khai đủ 4 giá trị

- **Ngày:** 2026-08-17 · **Trạng thái:** Đang hiệu lực — PO thật chốt 17/08/2026 (quy trình §3: ADR trước, code sau)
- **Bối cảnh:**

  Tester tìm ra qua nhánh timeout; security xác nhận bằng đọc mã và **mở rộng phạm vi**.

  `flag_human_handoff()` → `create_ticket_with_fraud_check()` với **`scope="internal_wallet"`
  HẰNG SỐ trong mã**, không đến từ nguồn nào:

  ```
  graph.py:466 → complaint_intake.py:166-173
      complaint_type = "other"
      scope          = "internal_wallet"   ← HẰNG SỐ, không tra, không hỏi
      description_raw= reason              ← câu do HỆ THỐNG soạn
      trans_id       = None
  ```

  **Hệ thống làm đúng điều nó CẤM model làm.** Mô tả tool `create_ticket` nói thẳng: *"không tra ra
  giao dịch VÀ khách cũng không xác định được phạm vi → dùng `unknown`, KHÔNG tự đoán bừa 1 trong 3
  giá trị thật."* Và đây **không phải k=1** — giá trị là hằng số, nhánh đó **luôn** ghi đúng nó;
  với một nhánh tất định, `k` không có nghĩa.

  🔴 **Phạm vi rộng hơn một nhánh lỗi.** `flag_human_handoff` có **hai** nơi gọi:

  | nơi gọi | khi nào | |
  |---|---|---|
  | `graph.py:466` | agent timeout / vượt đệ quy | nhánh lỗi |
  | **`customer_tools.py:801`** | tool `request_human_handoff` — khách gõ *"cho tôi gặp người thật"* | 🔴 **ĐƯỜNG BÌNH THƯỜNG** |

  Đường thứ hai là **tính năng có thiết kế** (CTRL-001 · ISO/IEC 25059 *user controllability*) — thứ
  ta chủ động xây để khách luôn thoát được sang người thật. ⟹ **một khách bình thường, không lỗi gì,
  gõ "cho tôi gặp nhân viên" là sinh ra một hồ sơ khiếu nại thật mang phạm vi giao dịch BỊA.** Không
  cần timeout, không cần ai chạy phép đo nào.

  Rà đủ **4** nơi gọi `create_ticket_with_fraud_check`: model điền (`customer_tools.py:765`) · hai
  cửa trên (không qua model) · người điền (`main.py:562`) ⟹ **đúng một nhánh không-qua-model**.

- **Ràng buộc bị chạm — khoanh cho đúng:**

  - **Ràng buộc 1 (HITL): KHÔNG bị chạm.** `fraud_policy.py` **không tham chiếu `scope`** một lần
    nào ⟹ `scope` sai **không tạo đường tắt**; mọi phạm vi vẫn cần `supervisor` duyệt.
  - **Ràng buộc 3 (cấm bịa số liệu): CÓ, hai lần.** ① giá trị nghiệp vụ không nguồn ② **chuỗi truy
    vết đứt ở mắt ĐẦU** — `write_investigation_logs_for_ticket` gọi ở `graph.py:569`, nhánh fallback
    **`return` ở `:476`**, trước đó ⟹ `investigation_logs` rỗng, vé **không truy về được bất kỳ tool
    result nào**.
  - **ADR-025 nhóm A:** `description_raw` là **câu do hệ thống soạn** nằm trong bảng *"lời khai =
    bằng chứng"*. Security cảnh báo điều này cho **một phép đo** buổi sáng — hoá ra **sản phẩm đã tự
    làm**, với khách thật.

- **Quyết định:**

  1. **`scope="unknown"`** thay `"internal_wallet"` ở cả hai nơi gọi (`unknown` đã hợp lệ trong
     `VALID_SCOPES` + CHECK constraint).
  2. **Nhánh fallback ghi một DẤU KHẲNG ĐỊNH "chưa điều tra", không ghi một mắt xích truy vết giả.**
     PO-agent chọn giữa ba hướng coder nêu:
     - ① *ghi một `investigation_log` "hệ thống bó tay" trỏ về chính `create_ticket`* — **BÁC**: chuỗi
       liền **về hình thức** mà không thêm một thông tin thật nào. Đúng lớp *"xanh vì đo trúng thứ
       khác"* đã cắn đội nhiều lần trong ngày; tệ hơn không vá, vì nó **tạo ra vẻ đã truy vết được**.
     - ③ *coi là lỗ hổng ràng buộc cứng 3 phải bịt trước demo* — **BÁC**: ràng buộc 3 cấm **phát biểu
       một con số không truy được**. Vé fallback **không phát biểu con số nào** — nó là một **sự
       vắng mặt**, không phải một điều bịa. Gọi nó là vi phạm sẽ làm loãng chính ràng buộc đó.
     - ② **CHỌN**, với một siết: dấu phải là **khẳng định**, không phải **vắng mặt**. *Bảng rỗng và
       bảng nói "không có gì" giống nhau với máy, khác hẳn với người đọc hồ sơ sáu tháng sau.*
       ⟹ dấu là một trạng thái **đọc được bằng máy và bằng mắt**, hiện ngay trên màn CSKH.
     **Rủi ro thật cần chặn không phải chuỗi đứt — mà là một người đọc hồ sơ sáu tháng sau và
     GIẢ ĐỊNH đã có điều tra.** Dấu khẳng định chặn đúng rủi ro đó; mắt xích giả thì nuôi nó.

     🔴 **SIẾT LẦN HAI (coder đề, PO-agent duyệt) — dấu thuộc về SỰ KIỆN BÀN GIAO, không thuộc về VÉ.**
     Đo được: hai đường gọi **khác nhau ở chỗ có tạo vé mới hay không**.
     ```
     ① graph.py:466 (hết giờ)     gọi KHÔNG kèm ticket_id ⟹ LUÔN tạo vé mới, chắc chắn chưa điều tra
     ② customer_tools.py:801      truyền ticket_id ⟹ chỉ ĐẶT CỜ lên vé CÓ SẴN,
                                  vé đó có thể đã điều tra đầy đủ và CÓ investigation_logs
     ```
     ⟹ mệnh đề *"vé này sinh ra không qua bước điều tra nào"* **đúng cho ①, SAI cho ②**. Và nó bịt
     luôn đường tắt *"suy từ `count(logs)==0`"* — nhánh ② cho ra vé có log đầy đủ mà vẫn là handoff.
     **Suy-từ-vắng-mặt sai ở cả hai chiều.**
     ⟹ Phát biểu đúng: *"lần bàn giao NÀY xảy ra vì hệ thống bó tay, tại thời điểm đó chưa có bước
     điều tra nào"* — đúng cho cả hai nhánh, và **không bao giờ hết đúng** khi vé được điều tra tiếp
     sau đó.

     🔴 **Và giá của mục 2 vì thế KHÁC hẳn — PO phải duyệt trên đúng giá này:** không phải *"thêm một
     cột bool"* mà là **TÁCH MỘT CỜ ĐANG QUÁ TẢI**. `Ticket.human_handoff_requested` (`models.py:304`)
     hiện được **cả hai đường đặt `=True` không phân biệt** ⟹ trên màn CSKH hôm nay, *"hệ thống bó
     tay"* và *"khách chủ động xin gặp người"* là **cùng một cờ**.
     🔴 **HỒ SƠ CŨ — 101 vé đã mang cờ, và chỉ backfill được MỘT NỬA.** Coder đo trên `fin05`
     (đọc thuần): `tickets` tổng **755**, `human_handoff_requested=True`: **101**.
     ```
     ① hệ thống bó tay (khớp chuỗi lý do HẰNG)                 15   ← truy hồi ĐƯỢC
     ② khách xin, TẠO vé mới  (other · trans_id rỗng)          85   ← KHÔNG truy hồi được
     ② khách xin, ĐẶT CỜ lên vé có sẵn                          1
     trong cả 101 vé, số vé CÓ investigation_logs:              1
     ```
     **Vé duy nhất có log chính là vé nhánh ②-tái-dùng** (`TCK-2cc91cba110d` · logs=3 ·
     `wrong_recipient` · `trans_id=TXN20260730000113`) — **một vé đã phân loại xong, có giao dịch
     thật, đã điều tra 3 bước** rồi mới bị đóng cờ handoff. ⟹ dấu-theo-VÉ **sai trên một hồ sơ CÓ
     THẬT đang nằm trong CSDL**, không phải sai trên giả thuyết. Siết "dấu thuộc SỰ KIỆN" có ca thật.
     ⟹ **Quyết định về hồ sơ cũ (PO-agent):** ① **backfill 15 vé** truy hồi được — chuỗi lý do hằng
     là **dấu vết duy nhất còn sót, và nó tồn tại TÌNH CỜ chứ không do ai thiết kế** ② **86 vé còn
     lại mang một dấu KHẲNG ĐỊNH riêng: *"nguồn gốc bàn giao không truy hồi được"*** — **không** để
     trống. Lý do: để trống là **tái lập đúng cái bẫy ADR này đang vá** — sáu tháng sau người đọc
     thấy 86 vé không có dấu sẽ hiểu là *"đã điều tra"*. **Sự mơ hồ phải được KHAI, không được suy
     ra từ vắng mặt** — đúng nguyên tắc của chính mục 2.
     ⚠️ **Người ghi thứ BA vào cờ này, ngoài hai đường trên:** `scripts/load/ws_live_chat_load.py:103`
     đặt thẳng `ticket.human_handoff_requested = True`, **không qua `flag_human_handoff`**. Là script
     tải dựng cảnh cố ý, **không phải bug** — nhưng nếu sau này ta đặt bất biến *"cờ bật ⟹ phải có
     bản ghi sự kiện bàn giao"* thì **script này sẽ phá bất biến đó**. Ghi ra để lúc viết bất biến
     không phải đi tìm lại.
     ⚠️ **Giới hạn của phép đo, đọc đúng mức:** `fin05` là ngăn xếp demo, 755 vé **lẫn dữ liệu hạt
     giống và dữ liệu chạy thử** ⟹ các con số trên dùng để **định cỡ câu hỏi backfill**, **KHÔNG
     phải chỉ số sản phẩm**. Phần **không phụ thuộc dân số** là phần cấu trúc: chuỗi hằng truy hồi
     được ①, không gì truy hồi được ②, và ca `TCK-2cc91cba110d` tồn tại.

     ⟹ **Rủi ro "người đọc giả định đã có điều tra" hôm nay MẠNH HƠN mức ADR này mô tả ban đầu:**
     không phải vì bảng rỗng **im lặng**, mà vì cờ hiện có **NÓI SAI** — nó gợi ý *"khách yêu cầu"*
     cho cả những vé thật ra là *"AI bó tay"*. Im lặng nghiêng về người đọc lạc quan; cái này **chủ
     động đẩy** họ về đó.
  2b. **(BỔ SUNG 17/08 tối, từ chuỗi đo R) — `request_human_handoff` phải vào SỔ TOOL.** Coder đếm
     bản ghi theo tên tool trong đúng ba cửa sổ R: **tất định cả ba vòng**, đúng một lời gọi không
     sinh bản ghi, **và luôn là cùng một tool** — `request_human_handoff` **không bao giờ** gọi
     `record_tool_result`, trong khi `src/tools/base.py` dòng 3 ghi *"Mọi tool PHẢI gọi
     `record_tool_result` trước khi return"*. **Một luật phát biểu tường minh trong chính module cơ
     sở, và một tool không tuân** — cùng khuôn `unknown`-hợp-lệ-sáu-ngày.
     **Mức: CAO HƠN `investigation_logs`** — tool này **tạo/đánh dấu một vé thật** rồi biến mất khỏi
     sổ: vé sinh qua đường handoff **không có `tool_result_id` nào trỏ về hành động tạo ra nó**.
     Chuỗi `tool_results → investigation_logs → cited_tool_result_ids` đứt ở **mắt xích SỐ KHÔNG**,
     trước cả mắt xích mục 2. Và nó khớp ca 101-vé: *chỉ 1/101 vé handoff có investigation_logs* —
     **hai finding là cùng một lỗ nhìn từ hai phía.**
     **Cố ý KHÔNG vá lẻ** (một dòng `record_tool_result` thêm vào sẽ tạo một bản ghi rời không nối
     với dấu sự kiện mà mục 2 đang định nghĩa) ⟹ thiết kế **cùng gói** với mục 2: dấu sự kiện bàn
     giao + bản ghi tool là **một thiết kế truy vết**, không phải hai bản vá.
     *(Ghi chú đối chứng từ cùng phép đếm: `create_ticket` gọi 2 lần → ghi 1 là hành vi **ĐÚNG** —
     lời gọi thứ hai bị cơ chế chống trùng chặn **trước khi ghi**, bằng chứng thêm rằng cơ chế đó
     đang gánh thật.)*

  3. **Đánh dấu `description_raw` do hệ thống soạn** — bảng bằng chứng phải phân biệt **lời khách**
     với **ghi chú của máy**.
  4. **`contracts/authority-matrix.yaml` khai đủ 4 giá trị `scope`, MỖI GIÁ TRỊ KÈM MÃ.** Thiết kế
     cụ thể (tester đề, PO-agent duyệt):
     ```yaml
     scopes:
       noi_bo_vi:    {mo_ta: "...", gia_tri_ma: internal_wallet}
       tu_ngan_hang: {mo_ta: "...", gia_tri_ma: from_bank}
       ra_ngan_hang: {mo_ta: "...", gia_tri_ma: to_bank}
       khong_ro:     {mo_ta: "...", gia_tri_ma: unknown}      # ← đang THIẾU
     ```
     Giữ tên khoá tiếng Việt (đọc được cho người), **thêm `gia_tri_ma`** làm cầu nối máy đọc được.
     Khi đó phép so **thành máy móc** và bảng nối tay trong test biến mất.

- **🔴 Nợ contract lộ ra khi đi tìm giá trị đúng — lý do mục 4 tồn tại:**

  ```
  authority-matrix.yaml  scopes:  noi_bo_vi · tu_ngan_hang · ra_ngan_hang        (BA, tiếng Việt)
  models.py:209  CHECK:  internal_wallet · from_bank · to_bank · unknown          (BỐN, tiếng Anh)
  ```

  **`unknown` — chính giá trị bản vá cần — không được khai trong contract.** Và vì **tên khoá khác
  hệ ngôn ngữ**, **không phép so máy nào bắt được lệch này** — cùng lớp với ADR-027 (contract khai
  CẤU TRÚC mà người đọc tưởng nó khai NỘI DUNG), lần này là *contract và code dùng hai bộ từ vựng
  cho cùng một khái niệm*.

  > **Hai artefact cùng mô tả một thứ bằng HAI HỆ TÊN thì không so được tự động — và "không so được"
  > trông y hệt "đã so, khớp". Cả hai đều im lặng.**

  Đó là lý do khi `unknown` vào CHECK ngày 11/08, **không có gì đỏ**: 23 invariant vẫn xanh, và cái
  xanh đó **không mang thông tin nào**. Tester đã viết test canh (`c1c2482`), hai test đầu
  `xfail(strict)` — **đánh dấu nợ đã biết để CI không đỏ, KHÔNG để giấu**; khi contract khai đủ,
  chúng **XPASS** và buộc người sửa quay lại gỡ dấu.

- **🌍 ĐỐI CHIẾU CHUẨN QUỐC TẾ (PO yêu cầu 17/08) — cả ba mục đều có chỗ bám, không phải chuẩn mực nội bộ:**

  **① Mỹ — Regulation E / EFTA §1005.11 (áp cho ví điện tử và P2P phi ngân hàng):** tổ chức **không
  được từ chối khiếu nại của khách nếu chưa tiến hành ĐIỀU TRA HỢP LÝ**, và *"a reasonable
  investigation includes **reviewing relevant information within the institution's records**"*.
  ⟹ Đây là chỗ bám **trực tiếp và mạnh nhất** cho ADR này: khi hồ sơ mang **`scope` bịa** và
  **`investigation_logs` RỖNG**, thì **chính bản ghi mà cuộc điều tra bắt buộc phải dựa vào đã
  hỏng**. Vấn đề không còn là *"dữ liệu chưa đẹp"* — nó chạm **đầu vào của một nghĩa vụ pháp lý**.
  *(Kèm mốc thời gian Reg E: báo kết quả trong 3 ngày làm việc sau khi xong điều tra; sửa lỗi trong
  1 ngày làm việc sau khi xác định có lỗi.)*

  **② EU — AI Act Điều 50, hiệu lực 02/08/2026:** đầu ra của hệ thống AI sinh nội dung phải được
  **đánh dấu bằng dấu MÁY ĐỌC ĐƯỢC**, để nhận ra đó là nội dung do AI sinh/chỉnh sửa. ⟹ chỗ bám
  **trực tiếp** cho **mục 3** (đánh dấu `description_raw` do hệ thống soạn) — ta đang đặt **văn bản
  do máy sinh** vào bảng *"lời khai = bằng chứng"* mà **không có dấu nào**. Kèm nghĩa vụ công bố
  *"đang nói chuyện với AI"* ngay đầu tương tác.

  **③ Ranh giới rủi ro cao:** AI Act xếp **chấm điểm tín dụng / bảo hiểm** vào nhóm rủi ro cao;
  **agent CSKH xử lý khiếu nại thì KHÔNG** ⟹ nghĩa vụ nặng của nhóm rủi ro cao **không áp**, nhưng
  Điều 50 **vẫn áp**. Ghi rõ để không tự khoác lên mình nghĩa vụ không phải của mình — **cũng là
  một dạng nói quá.**

  ⚠️ **Hạng bằng chứng:** đọc ở mức **văn bản quy định + hướng dẫn tuân thủ công khai**, **chưa** ở
  mức ý kiến pháp lý cho đúng pháp nhân/thị trường của ta. Dùng để **định hướng thiết kế**, không
  dùng làm **kết luận tuân thủ**. *(Nguyên tắc "khai đúng hạng bằng chứng rồi dừng".)*

- **Phương án đã bác:**

  - *Chỉ sửa nhánh timeout (chỗ tester tìm ra)* — bác: đường bình thường mới là đường có khách thật
    đi qua hàng ngày.
  - *Giữ `internal_wallet` vì "đa số giao dịch là nội bộ ví"* — bác: đó đúng là định nghĩa của bịa số
    liệu. Một giá trị **có khả năng đúng** vẫn là giá trị **không có nguồn**.
  - *Sửa code trước, cập nhật contract sau* — bác theo §3, và lần này đặc biệt không được: giá trị
    cần dùng (`unknown`) **chưa tồn tại trong contract**, nên sửa code trước là làm lệch thêm.

- **Hệ quả:**

  - **Mục 1 (`scope="unknown"`) ĐÃ LAND (`27ccfbf`) mà KHÔNG cần ADR — và đó là đúng:** `unknown`
    **đã hợp lệ trong CHECK constraint từ 11/08**, nên đổi code sang dùng một giá trị **contract đã
    công nhận** không phải đổi contract. Đo thật trên `fin05do`: `type=other · scope=unknown ·
    TCK-f4f500ce42b3` · 23/23 invariants · contract 3/3 khớp. Phần **còn cần ADR này duyệt** là mục
    2 (dấu "chưa điều tra") và mục 4 (khai đủ 4 `scope` trong `authority-matrix`).
  - 🔴 **Và đây là phần đáng báo cáo hơn cả bản vá:** `unknown` được thêm vào CHECK constraint ngày
    **11/08**, kèm comment mô tả **đúng lớp lỗi này** (*"trước đây agent bị ép đoán bừa 1 trong 3 giá
    trị thật... thay vì AI bịa"*). **Cơ chế chữa đã có sẵn SÁU NGÀY** — áp cho đường agent, **bỏ sót
    đường code**. Không phải thiếu hiểu biết: là **một bản vá đúng không được đi tìm chỗ thứ hai
    cùng lớp**.
    ⟹ **Luật (coder đề, PO-agent duyệt): vá một ca của một lớp lỗi ⟹ LIỆT KÊ NGƯỜI GỌI và quét cả
    lớp, không dừng ở chỗ phát hiện.**
  - **Đã quét cả lớp `scope` — SẠCH.** `grep scope="…"` ngoài `unknown` → **0**; các cờ/số khẳng định
    về thế giới (`is_*`/`verified`/`fraud`/`eligible`/`amount`) → **0**. Bốn literal còn lại
    (`pending_approval` · `investigating` · `processing` · `waiting`) được **mở từng chỗ ra đọc**,
    không suy từ tên: cả bốn là **trạng thái khởi tạo của chính vật đang được tạo**.
    ⟹ **Ranh giới của lớp lỗi, ghi kèm luật để lần sau quét không bắt nhầm: literal khẳng định một
    SỰ THẬT VỀ THẾ GIỚI mà chưa ai tra ≠ literal đặt TRẠNG THÁI BAN ĐẦU của vật vừa tạo. Cái đầu bịa
    được; cái sau đúng theo cấu tạo.** Đây là phiên bản có răng của *"vá một họ thì phải đi tìm họ"*:
    nêu rõ **cách** đi tìm — đi theo call-site, không đi theo trí nhớ.
  - `check_contracts.py --update` + bump `CONTRACT_VERSION` + **commit kèm file baseline**.
  - **Chưa đếm được bao nhiêu vé kiểu này đã tồn tại** (`scope='internal_wallet'` ∧
    `complaint_type='other'` ∧ `trans_id IS NULL`). Security **cố ý không chạy** — đếm là chạm DB, và
    theo điều kiện ⑤ của chính họ, chưa biết ngăn xếp nào phục vụ thật thì chưa đụng. **Làm được
    ngay khi PO thật trả lời câu ngăn-xếp.**
  - **Sửa điều kiện dọn dữ liệu đo (③):** *kế hoạch dọn phải có **ngoại lệ khai trước** — nếu dữ liệu
    sinh ra là **bằng chứng của một finding** thì dừng dọn, khai lý do, giữ tới khi finding được đọc
    xong.* Không có ngoại lệ này, một kế hoạch dọn **nghiêm túc** sẽ xoá đúng thứ đáng giữ nhất — và
    xoá **có kỷ luật**, nên không ai thấy gì sai.

## ADR-030 — Tầng "trình bày cho model" là MỘT PHẦN CỦA PROMPT, phải được đóng dấu như prompt

- **Ngày:** 17/08/2026 · **Trạng thái:** Đang hiệu lực — PO thật chốt 17/08/2026
- **Bối cảnh:**

  Chuyên gia token của PO đề xuất tách tầng *"trình bày cho model"* khỏi tầng *"lưu sổ"* cho kết quả
  tool (mục 3.1 báo cáo 17/08). Coder đo trước khi ai làm gì (Luật F) và phát hiện **hai điều**:

  **① Đề xuất ĐÃ ĐƯỢC CÀI cho tool lớn nhất** — `get_customer_history` (payload trung vị **11.369
  ký tự = 75% cả system prompt**) đã tách hai tầng từ bản land 17/08: sổ nhận nguyên vẹn, context
  nhận bản rút gọn (~2.500 ký tự) kèm `tool_result_id` + `complaints_tong` bắt buộc (chú thích tại
  chỗ: *"cắt im lặng khiến LLM tưởng khách có 10 khiếu nại rồi NÓI RA con số đó"*). Đo trên lượt R
  thật: context tăng +839 token, không phải ~3.789 ⟹ bản rút gọn đang chạy.

  **② Nhưng bản rút gọn là MỘT VẬT ĐI VÀO PROMPT — và KHÔNG băm nào phủ nó.** `bam_mau_prompt` chỉ
  băm template hệ thống. Đổi `limit_complaints` 10→5 sẽ **đổi thứ model nhận trong khi mọi băm y
  nguyên** — lớp `khai ≠ chạy` thứ SÁU của ngày, lần này **đang tồn tại thật**, có số: **bản lưu
  11.369 vs context ~2.500 — chênh 4,5×, không băm nào bắc qua khoảng chênh đó.**

- **Quyết định:**
  1. **Mọi tầng trình bày cho model (hàm rút gọn + tham số của nó, vd `limit_complaints`) được đóng
     dấu vào nhãn VẬT** — cùng hạng với `bam_mau_prompt` và mô tả tool. Nguyên tắc: **thứ gì model
     ĐỌC thì thứ đó thuộc prompt, và prompt thì phải băm được.**
  2. `search_policy` (4.613 bản ghi, trung vị 2.886, **không tách tầng**, là nguồn phình lịch sử
     chính) — **KHÔNG cắt theo cách của `get_customer_history`**: với đoạn chính sách, cắt là bỏ
     chữ model cần để trả lời. Việc giảm chi phí RAG-context thuộc **trục chất lượng truy hồi**
     (N1 reranker: top-20→rerank→top-4 tốt hơn = ít chunk lãng phí hơn), đo bằng thước Recall,
     không đo bằng thước token.
- **Bác:** *cắt `search_policy` payload như một việc tối ưu token* — hai bài toán khác nhau đội một
  cái tên; và *"mọi %-chi-phí-lịch-sử phải kèm 'ở lượt thứ mấy'"* — lịch sử cộng dồn theo lượt, phần
  cố định là hằng số mỗi lời gọi, không có một con số đúng cho cả hai (giải mâu thuẫn "4% vs 36,2k":
  **cả hai đúng, khác dân số**).

## ADR-031 — Truy vấn `search_policy` phải được ghi lại làm BẰNG CHỨNG: hai trường, hai vòng đời

- **Ngày:** 17/08/2026 · **Trạng thái:** 🔴 **TẠM DỪNG THI HÀNH — TIỀN ĐỀ SAI, chờ PO thật quyết
  lại phạm vi.** (PO thật đã duyệt 17/08, nhưng duyệt trên một tiền đề PO-agent chưa kiểm — xem
  **Đính chính** ở cuối ADR này. Không sửa phần thân: `DECISIONS.md` chỉ ghi thêm.)
- **Bối cảnh:**

  **Lỗ:** `search_policy` **không bao giờ ghi lại truy vấn**. Một `tool_result_id` được
  `resolutions.cited_tool_result_ids` trích dẫn nói được *"đã trả về gì"* nhưng **không** nói được
  *"đã hỏi gì"*. Với ràng buộc cứng 3 (cấm bịa số liệu — mọi phát biểu phải truy vết tới một kết
  quả tool có thật), một bằng chứng không nói được nó **trả lời câu hỏi nào** là bằng chứng khuyết:
  không phân biệt được *agent tra đúng điều nó viện dẫn* với *agent tra một câu khác rồi gán kết
  quả sang chỗ khác*.

  **Và cùng chuỗi ký tự đó rời hạ tầng:** kiểm kê Đ.25 của security ([ĐO], `873109f`) ghi *"truy
  vấn RAG dẫn xuất từ lời khách"* **rời sang OpenAI** để nhúng. ⟹ **không ghi lại ở trong, mà có
  rời ra ngoài** — hai hồ sơ, một vật.

- **Quyết định — PA4: HAI TRƯỜNG, không phải chia đôi rủi ro.**
  Hai mục đích khác nhau đòi hai trường khác nhau: **băm** phục vụ cache/điều tra tần suất, **nguyên
  văn** phục vụ bằng chứng. Bốn điều kiện, cả bốn bắt buộc:
  1. 🔴 **Trường băm PHẢI tái dùng `_bam_truy_van` — CẤM tự đặt hàm băm mới.** Băm trần không khoá
     trên câu tra tiếng Việt ngắn (entropy thấp) ⟹ **băm CHÍNH LÀ query**, ai có DB là dò ngược
     bằng từ điển. `_bam_truy_van` là HMAC có khoá, đã có, đã fail-fast. *(Cùng lý do coder tái
     dùng `dau_thuoc()` cho `dau_ma_nguon`: **hai định nghĩa của cùng một vật sẽ lệch trong im
     lặng**.)* Và tệ hơn nữa: băm trần **trông giống** một biện pháp bảo vệ ⟹ **tệ hơn không băm
     gì**, vì không băm thì ai cũng thấy ngay là plaintext (Luật G).
  2. **Nguyên văn nằm ở CỘT MÃ HOÁ**, cùng chỗ `description_raw`/`messages.content`. **KHÔNG** vào
     `raw_json` — [ĐO] `tool_results.raw_json` là JSON **thường, không mã hoá** (`models.py:316`).
  3. **Hai vòng đời TÁCH RỜI:** băm sống theo **cache**, nguyên văn sống theo **hồ sơ nó chống
     lưng**. Gộp một vòng đời = lại tạo một cột phục vụ hai mục đích.
  4. **Hạng mới trong ADR-025 + CẤM che-lúc-ghi.** ADR-025 phân theo *ai sửa lại được*; query là
     **dẫn xuất của MÁY nhưng mang giá trị BẰNG CHỨNG** — không ai sửa được (như nhóm A) mà cũng
     không ai khai (khác nhóm A). Cấm che-lúc-ghi vì cùng lý do nhóm A: **sửa chữ trong một bản ghi
     bằng chứng thì bản ghi mất giá trị.**

- **Bác — cả ba phương án kia bị loại BẰNG ĐO, không bằng ý kiến:**
  - **PA2 (scrub rồi log)** — bản án nằm sẵn trong docstring `_bam_truy_van` (`src/rag/search.py`):
    S-01 `scrub_pii` **chặn nhầm 40%** văn bản nghiệp vụ tiếng Việt, và **câu tra chính sách CHÍNH
    LÀ loại văn bản đó** ⟹ cho ra chuỗi *vừa còn khả năng rò, vừa hỏng nghĩa*. Không mở lại.
  - **PA3 (băm thôi)** — hỏng ở đúng mục đích sinh ra nó. F-LOG-3 chọn băm vì mục đích là **điều
    tra sự cố** (*"cùng câu lặp bao nhiêu lần"*); mục đích ở đây là **ràng buộc cứng 3**, mà băm
    không nói được *"trả lời câu hỏi nào"*. ⟹ **cùng dữ liệu, khác mục đích — đừng chép kết luận
    F-LOG-3 sang đây.**
  - **PA1 (nguyên văn vào `raw_json`)** — bỏ chữ khách vào một cột plaintext (điều kiện 2).

- **Lý do tách cột phải phát biểu ĐÚNG:** `search_policy` payload **đã** chứa `results[].text`
  (nguyên văn đoạn chính sách — tài liệu công khai, không phải PII). ⟹ căn cứ tách **không phải**
  *"cột kia bẩn"* (ai đó sẽ bác bằng *"vậy làm sạch cột kia là xong"*) mà là: **hai loại dữ liệu có
  hai vòng đời và hai mức nhạy cảm.**

- **Còn treo, KHÔNG được đánh dấu xong:** audit-log Pha-1 phủ cột mới **ở mức ENDPOINT** theo cấu
  trúc (`audit_log_middleware`, `main.py:195` — mọi request có JWT, không danh sách route ⟹ *không
  liệt kê thì không sót*), **nhưng chỉ ghi `path`** ⟹ **CHƯA XÁC ĐỊNH ở mức bản ghi** (*"ai đọc bản
  ghi nào"*). Mức bản ghi **không lấy được từ middleware** (tầng HTTP không biết truy vấn nào đã
  chạy) — nếu security cần mức đó thì đấy là **một hạng việc MỚI**, không phải một dòng thêm vào.

### 🔴 ĐÍNH CHÍNH ADR-031 (17/08/2026, cùng ngày) — tiền đề "query chưa được lưu ở đâu" là SAI

**Ai bắt:** coder, khi dừng ở bước 1 của §3 thay vì sửa contract ngay. **Ai gây:** PO-agent.

**[ĐO]** `investigation_logs.tool_input_json` **đã lưu query từ lâu, plaintext**:

```
contracts/agent-tools.yaml:150   cot: [step_no, tool_called, tool_input_json, tool_result_id]
src/db/models.py:328             tool_input_json: mapped_column(JSON, nullable=False)   ← JSON THƯỜNG
fin05, 10 dòng search_policy:    {"query": "hạn mức chuyển tiền một ngày"} …
```

> **PO-agent trích `contracts/agent-tools.yaml:143-146` cho coder rồi DỪNG ĐỌC — câu trả lời nằm ở
> dòng 150, BA DÒNG DƯỚI cùng khối vừa trích.** Cùng lớp lỗi của cả ngày ở dạng thuần nhất: **đọc
> một khung nhìn đã bị lọc (bởi chính lệnh grep của mình) rồi dùng nó như toàn cảnh.** Lần này bộ
> lọc do chính người đọc đặt ra.

**Ba hệ quả — đổi cả phạm vi lẫn hướng của bản vá:**

1. **Lỗ truy vết HẸP HƠN ADR-031 mô tả.** Với lượt **có tạo vé**, `investigation_logs` đã nối
   `tool_input_json ↔ tool_result_id` ⟹ *"tool_result này trả lời câu hỏi nào"* **trả lời được
   rồi**. Lỗ chỉ còn ở lượt **KHÔNG tạo vé** — nhưng đó là tuyệt đại đa số (**4.613** `tool_results`
   vs **10** dòng log).
2. 🔴 **Vấn đề bảo mật NGƯỢC CHIỀU với thứ ADR-031 đi vá.** ADR-031 lo *"đừng đưa chữ khách vào cột
   plaintext"* — **chữ khách đã ở đó rồi**, chỉ ở bảng ta không nhìn. Vá `tool_results` cho đúng
   chuẩn mà để `investigation_logs` như cũ = **dựng một cửa mới cạnh một cửa đang mở.**
   ⚠️ Và `tool_input_json` chứa input của **MỌI** tool, không riêng `search_policy`:
   `lookup_transaction` (11 dòng) · `get_customer_history` (44 dòng) ⟹ **mã giao dịch · SĐT · số
   tiền, plaintext.** Mức nhạy cảm cao hơn hẳn câu tra chính sách. **Câu này thuộc security.**
3. **Hai bảng, một loại dữ liệu, hai chuẩn khác nhau.** Điều kiện ① (HMAC `_bam_truy_van`) áp cho
   `tool_results`; `investigation_logs` **không có gì**. Đúng lớp lỗi đội rà cả ngày.

**Đường có thể RẺ HƠN, chưa quyết:** *dùng lại cơ chế đã có ở `investigation_logs` và mở rộng nó
cho lượt không tạo vé* — rẻ hơn hẳn thêm hai cột mới, và **không tạo chuẩn thứ ba**.

**🔴 BA CÂU CHO PO THẬT (không ai trong đội quyết thay được):**
① phạm vi là **một bảng** (`tool_results`, như ADR-031) hay **hai bảng**?
② bản vá là **thêm cột mới** hay **mở rộng cơ chế đã có** ở `investigation_logs`?
③ `investigation_logs.tool_input_json` đang plaintext chứa mã GD/SĐT/số tiền — **xử riêng như một
finding bảo mật**, độc lập với ADR-031?

**Coder DỪNG bước 1 của §3, không sửa contract.** Đúng: sửa contract theo một ADR có tiền đề đã
lung lay thì ta **khoá sai chỗ** — và §3 làm việc khoá đó rất chắc.

## ADR-032 — Giải mã phải phân biệt BA trạng thái; và cột Nhóm A phải được nạp lại, không chỉ được khai

- **Ngày:** 2026-08-18 · **Trạng thái:** Đang hiệu lực — PO thật chốt 18/08/2026
- **Bối cảnh:**

  PO-agent kiểm lại một phát biểu của security (*"`complaints.description_raw` đã mã hoá"*) trước khi
  relay cho PO thật. **[ĐO]** `psql` thẳng vào `fin05-postgres-1`, `GROUP BY` trên **toàn bảng**:

  ```
  complaints.description_raw   PLAINTEXT  738   tạo 05/05/2026 → 14/08/2026
                               MÃ HOÁ      23   tạo 15/08/2026 → 17/08/2026   ⟹ 97% PLAINTEXT
  messages.content             MÃ HOÁ     467   (467/467 — bảng chỉ có dữ liệu từ 11/08)
  ```

  `EncryptedText` được gắn vào `models.py:274` khoảng 15/08. **738 dòng có sẵn chưa bao giờ được nạp
  lại.** Cột được ADR-025 chọn ra làm **Nhóm A** (lời khai của khách — dữ liệu nhạy cảm nhất hệ thống)
  đang nằm plaintext trên đĩa cho tuyệt đại đa số bản ghi.

  🔴 **Vì sao ba tháng không ai thấy — `src/db/crypto_types.py:59-65`:**

  ```python
  def process_result_value(self, value, dialect):
      try:    return _fernet.decrypt(value.encode()).decode()
      except InvalidToken:
          return value          # ← nuốt IM LẶNG, trả nguyên văn
  ```

  Nhánh lỗi trả về thứ **trông y hệt một lần đọc thành công**. Ứng dụng đọc 738 dòng ấy không một lỗi
  nào, không một dòng log nào. **Đây là Luật H ở dạng mạnh nhất dự án từng gặp:** các ca trước, nhánh
  lỗi *in ra KẾT LUẬN thay vì TRIỆU CHỨNG*; ca này nhánh lỗi **không in gì cả — nó GIẢ TRANG THÀNH
  THÀNH CÔNG**. Và **Luật G**: cơ chế đang làm **đúng việc của NÓ** (tương thích ngược trong lúc di
  trú), ta đọc nó thành một thứ rộng hơn (*"cột này được mã hoá"*).

  **Nếp kiểm đã bắt được nó** (§8): security trích **3 dòng mẫu** rồi đọc ra *"đã mã hoá"* — ba dòng ấy
  tình cờ nằm trong 23 dòng mới, vì **`LIMIT` mặc định trả về dòng mới nhất**. Hỏi **MẪU SỐ** thì bức
  tranh lật ngược. Bộ lọc vô hình, lần này nằm trong chính công cụ truy vấn.

- **Quyết định — BA việc, cố ý KHÔNG gộp:**
  1. 🔴 **`process_result_value` phải phân biệt BA trạng thái, không phải hai:** *giải mã được* ·
     *chưa mã hoá (plaintext cũ)* · *mã hoá bằng KHOÁ KHÁC*. Trạng thái hai và ba **không được im
     lặng** — phải sinh sự kiện quan sát được. Đây là **điều kiện tiên quyết** của việc 2: sửa nó
     trước thì bước nạp lại mới có gì để quan sát.
  2. **Script nạp lại 738 dòng** trong `migrations/`. Bắt buộc: **sao lưu trước**, và **đếm phân bố
     trước/sau** để có mẫu số hai đầu — không để script tự phát hiện lúc chạy (*Đọc trước, dọn sau*).
  3. **Một cổng trong `tests/` khẳng định *"không dòng nào trong cột Nhóm A nằm plaintext"*.** Hôm nay
     **không cổng nào** khẳng định điều đó — và chính vì thế 738 dòng trôi ba tháng.

- **Lý do phân biệt BA trạng thái thay vì bỏ hẳn `except`:** bỏ hẳn thì mọi dòng plaintext cũ làm chết
  ứng dụng ngay khi đọc — một bản vá đúng biến thành sự cố vận hành. Ba trạng thái giữ được đường đọc
  **và** làm hiện ra thứ đang bị giấu. Đúng nguyên tắc Luật H: **luôn là BA trạng thái, không phải hai.**

- **Lý do BÁC BỎ *"cứ nạp lại rồi thôi, không đụng `crypto_types.py`"*:** nạp lại xong thì nhánh nuốt
  lỗi **vẫn còn**, và nó là thứ sẽ giấu **lần sau**. Quan trọng hơn: nó giấu cả ca **khoá khác** —
  ⟹ **xoay `FIELD_ENCRYPTION_KEY` sẽ KHÔNG báo lỗi**, 23 dòng đã mã hoá trả về nguyên chuỗi
  `gAAAAA…` như thể đó là nội dung khiếu nại. Cảnh báo `docs/STATE.md` §1 (*"xoay là mất vĩnh viễn"*)
  hoá ra **nhẹ hơn sự thật**: không phải mất ồn ào, mà **hỏng IM LẶNG**.

- **Hệ quả:** `src/db/crypto_types.py` · `migrations/` (script mới) · `tests/` (cổng mới) ·
  `docs/STATE.md` §1 (sửa lại cảnh báo xoay khoá) · ADR-025 (Nhóm A: *"được khai là mã hoá"* ≠
  *"đã mã hoá"* — phân biệt này chưa từng được viết ra).

### BỔ SUNG ADR-032 (18/08, cùng ngày) — security kiểm CẢ HỌ cột, và làm sắc lại THỨ TỰ

*(`DECISIONS.md` chỉ ghi thêm — không sửa thân ADR-032 ở trên.)*

**① Phạm vi HẸP HƠN ADR-032 để ngỏ. [ĐO] cả bốn cột khai `Encrypted*`:**
`messages.content` 467/0 ✅ · `policy_chunks.text` 378/0 ✅ · `bank_accounts.account_no` 245/0 ✅ ·
**`complaints.description_raw` 23/738 🔴 — DUY NHẤT.**
⟹ **Hệ thống mã hoá KHÔNG hỏng**; đây là nợ migrate của cột **mới nhất được gắn kiểu** lên một bảng
**đã có 738 dòng**. Việc sửa gói trong **một script backfill**, không phải một cuộc rà soát.

**② Thứ tự "① trước ②" trong Quyết định KHÔNG phải vì mục 1 rẻ hơn — lý do thật, ghi rõ để phiên sau
khỏi đảo:** **nếu backfill chạy trước, phép nghiệm thu của chính nó đi qua đúng nhánh đang nói dối.**
Một dòng backfill hỏng sẽ đọc ra nguyên văn và **trông y hệt một dòng thành công**. **Sửa cái đèn
trước khi soi.**

**③ Cơ chế phân biệt cụ thể cho việc 1** — `gAAAAA` là dấu hiệu tin cậy của Fernet token (byte phiên
bản `0x80` → base64url luôn mở đầu `gA`):
```
mở đầu "gAAAAA" mà decrypt hỏng  →  SAI KHOÁ      →  NÉM LỖI, không nuốt
ngược lại                         →  plaintext cũ  →  trả nguyên văn (như nay)
```
**Phải land TRƯỚC mọi thao tác xoay `FIELD_ENCRYPTION_KEY`**, không phải sau.

**④ [ĐO] Phép đo dứt điểm rằng ADR-032 và ADR-034 vá HAI LỖ KHÁC LOẠI**, không phải một lỗ hai triệu
chứng: ghép 27 dòng `create_ticket` với `complaint` gốc ⟹ **16/27 dòng có bản gốc ĐÃ MÃ HOÁ ĐÚNG và
một bản sao PLAINTEXT nằm cạnh** (15–17/08). Với 16 dòng ấy cơ chế ADR-025 **đã chạy, đã đúng, và vẫn
bị đi vòng trong cùng một giao dịch**.
⟹ **ADR-032 là VŨNG NƯỚC (tát một lần là hết); ADR-034 là VÒI ĐANG CHẢY (không script nào đóng được).**
Và **vá ADR-032 làm ADR-034 nặng thêm tương đối**: backfill xong thì `investigation_logs` thành **bản
plaintext DUY NHẤT còn lại của lời khai khách**.

## ADR-033 — `/ready` phải được THI HÀNH, và "ADR đã duyệt mà chưa ai code" phải có cổng canh

- **Ngày:** 2026-08-18 · **Trạng thái:** Đang hiệu lực — PO thật chốt 18/08/2026
  ✅ **CẢ HAI phần (a) `/ready` và (b) cổng canh hạng mù được PO thật phê chuẩn 18/08 vòng 2** (*"chốt theo ý bạn"*).
- **Bối cảnh:**

  ADR-028 (PO thật chốt 17/08, trạng thái *"Đang hiệu lực"*) quyết tách `GET /ready` khỏi `/health`.
  **[ĐO] 18/08, liệt kê từ app đang chạy** (không suy từ vắng mặt): **37 cặp `(method, path)`**, khớp
  `health|ready|ops` → **`GET /health`, DUY NHẤT**. `grep -rn "ready" src/` → 2 hit, **cả hai là chú
  thích**. `grep -n "ready" contracts/authority-matrix.yaml` → **0 hit**.

  **Không ai làm sai** — ADR ghi rõ *"§3: ADR trước, code sau"*, và phần *"code sau"* chưa tới. Vấn đề
  là **không chỗ nào theo dõi việc nó chưa tới**, và hai chú thích ở `main.py:1527,1580` viết về
  `/ready` **như thể nó đã tồn tại** ⟹ người đọc code sau sẽ tin là có.

  🔴 **Vì sao cơ chế contract-first không bắt được — đây mới là phần đáng ghi.** INV-00 ép `app.routes`
  khớp **chính xác** `authority-matrix.yaml`. **Cả hai phía đều thiếu `/ready`** ⟹ chúng khớp nhau
  hoàn hảo ⟹ **23/23 xanh**. Cơ chế làm **đúng việc của NÓ** (bắt code lệch contract); đội đã quen đọc
  nó thành một thứ rộng hơn (bắt **quyết định chưa được thi hành**). **Luật G ở tầng cơ chế phòng thủ.**

  **Và security tới cùng hình dạng từ hướng độc lập:** `test_invariants` introspect route/vai/CHECK/tên
  tool — **không cái nào nhìn thấy THỨ TỰ CÂU LỆNH TRONG THÂN HÀM**; một lần dọn dẹp chuyển khối ghi
  lên trên một guard giữ **cả 23 invariant xanh VÀ cả 6 ca test xanh**.
  ⟹ **Hai ca độc lập trong một ngày, một mệnh đề rộng hơn cả hai:** contract-first canh **thứ khai được
  trong một tệp YAML**; nó **không canh được** thứ chỉ tồn tại trong **quan hệ giữa các câu lệnh**, hoặc
  trong **khoảng cách giữa QUYẾT ĐỊNH và THI HÀNH**. Đó là **một HẠNG MÙ, không phải hai lỗ thủng.**

- **Quyết định:**
  1. **Thi hành ADR-028**: thêm `GET /ready` (liveness `/health` giữ nguyên, **không** chạm dependency;
     readiness được phép check kho RAG + khoá), khai vào `contracts/authority-matrix.yaml`, đi **đủ
     `docs/STATE.md` §10** — gồm **bước 7: commit KÈM file baseline** mà `CLAUDE.md` §3 không viết.
  2. **Cổng mới canh HẠNG MÙ:** *mọi ADR trạng thái "Đang hiệu lực" có mục Hệ quả nêu tên file/route thì
     thứ đó phải tồn tại.* Chỗ cắm **KHÔNG phải** `tests/test_invariants.py` (nó canh code-vs-contract,
     một trục khác) mà là một cổng riêng.

- **Lý do BÁC BỎ *"nhét phép kiểm này vào `test_invariants.py`"*:** trộn hai trục vào một tệp làm hỏng
  đúng thứ khiến `test_invariants.py` đáng tin — nó có **một** câu hỏi rõ ràng (*code có khớp contract
  không*) và trả lời được bằng introspection. Câu hỏi mới (*quyết định đã được thi hành chưa*) đọc
  `docs/`, không đọc app. Hai nguồn sự thật khác nhau, hai tệp khác nhau.

- **Hệ quả:** `src/api/main.py` · `contracts/authority-matrix.yaml` (⟹ `check_contracts --update` +
  `CONTRACT_VERSION` + **baseline**) · `tests/` (cổng `/ready` + cổng hạng-mù) · `docs/STATE.md` §5.D2.

## ADR-034 — Gỡ TẠM DỪNG cho ADR-031: HAI bảng, MỞ RỘNG cơ chế đã có, và tách finding bảo mật

- **Ngày:** 2026-08-18 · **Trạng thái:** Đang hiệu lực — PO thật chốt 18/08/2026 (*"chốt làm ADR-031"*).
  Thay thế trạng thái 🔴 TẠM DỪNG THI HÀNH của ADR-031.
  ✅ **PO thật PHÊ CHUẨN CẢ BA lựa chọn phạm vi, 18/08 vòng 2** (*"chốt theo ý bạn"*) — mục 1 · 2 · 3
  dưới đây **không còn là đề xuất của PO-agent**, chúng là quyết định của PO. Caveat cũ đã gỡ.
- **Bối cảnh:**

  ADR-031 bị dừng vì tiền đề *"query chưa được lưu ở đâu"* **sai** — `investigation_logs.tool_input_json`
  đã lưu plaintext từ lâu. Ba câu treo cho PO. **Từ 18/08 có thêm hai dữ kiện đổi hẳn bức tranh:**

  **① [ĐO] Chính đính chính ADR-031 cũng bị lọc.** Nó liệt kê 3 tool / 65 dòng. Đếm đủ bảng:
  **5 tool / 93 dòng** (`get_customer_history` 44 · **`create_ticket` 27** · `lookup_transaction` 11 ·
  `search_policy` 10 · `cskh_request_more_info` 1). Thiếu `create_ticket` — **và nó mang khoá
  `description_raw`, tức LỜI KHAI KHÁCH.** Đính chính đi tìm *"query lưu ở đâu"* nên tập tự đến chỉ gồm
  tool **ĐỌC**; `create_ticket` là tool **GHI** nên không bao giờ vào khung nhìn.
  *(Bộ lọc vô hình **nằm trong chính văn bản sửa lỗi cho một bộ lọc vô hình khác** — §8, tầng thứ ba.)*

  **② [ĐO] ADR-032: cột `complaints.description_raw` — thứ được cho là bản mã hoá — nằm PLAINTEXT trên
  738/761 dòng (97%).** ⟹ Khung *"cột đã mã hoá đang có một BẢN SAO plaintext ở bảng khác"* **sai về
  phía trấn an**. Bản sao ở `investigation_logs` là **lỗ thứ hai, không phải lỗ lớn nhất.**

- **Quyết định — ba câu treo, ba câu trả lời:**

  1. **Phạm vi: HAI BẢNG.** Vá `tool_results` mà để `investigation_logs` như cũ = **dựng một cửa mới
     cạnh một cửa đang mở** — và tệ hơn ẩn dụ: cửa mới sẽ có ADR + contract + test ⟹ **hiện ra** trong
     mọi kiểm kê sau; cửa cũ chứa **hạng nặng hơn** (mã GD · SĐT · số tiền · **lời khai khách**) và
     **không cổng nào canh**. Sau bản vá, hồ sơ **trông kín hơn** trong khi bề mặt nặng nhất không đổi
     — **Luật G ở tầng hồ sơ, và đắt hơn không vá gì**, vì hồ sơ trông kín thì không ai kiểm lại.
  2. **Cơ chế: MỞ RỘNG cái đã có ở `investigation_logs` cho lượt không tạo vé — KHÔNG thêm cột mới ở
     `tool_results`.** Rẻ hơn hẳn, và **không tạo chuẩn thứ ba** cho cùng một loại dữ liệu. Hai điều
     kiện của ADR-031 giữ nguyên hiệu lực khi áp vào cơ chế mở rộng: **① tái dùng `_bam_truy_van`
     (CẤM hàm băm mới)** — băm trần trên câu tra tiếng Việt ngắn là **băm CHÍNH LÀ query**, và nó
     **trông giống** một biện pháp bảo vệ ⟹ **tệ hơn không băm gì**; **② nguyên văn nằm ở cột MÃ HOÁ**.
  3. **`tool_input_json` plaintext: CÓ, tách thành finding bảo mật độc lập.** Lý do quyết định **không
     phải** mức độ mà là **tính độc lập**: nó đúng dù phạm vi một bảng hay hai, cột mới hay cơ chế cũ.
     **Buộc một finding đã chín vào một ADR đang treo là cách chắc chắn nhất để nó không được vá.**

- **Ràng buộc hình dạng bản vá (security nêu, giữ lại):** **đừng phản xạ `EncryptedText` cả cột**
  `tool_input_json` — cột này **được truy vấn theo khoá** (`jsonb ? 'query'`), và khả năng ấy đang là
  dụng cụ điều tra. Hình dạng đúng là **tách trường nhạy cảm ra khỏi khối JSON**, không mã hoá cả khối.

- **Ràng buộc thứ tự ĐÃ TAN:** security từng ghi *"vá finding ① sẽ xoá dụng cụ đo của Đ.25 ⟹ phải kiểm
  kê xong TRƯỚC khi vá"*. **PO thật bỏ hồ sơ Đ.25 (18/08)** ⟹ ràng buộc ấy không còn ⟹ bản vá land
  **sớm hơn**, không phải muộn hơn.

- **Lý do BÁC BỎ *"làm đúng ADR-031 nguyên bản (một bảng, hai cột mới ở `tool_results`)"*:** nó được
  thiết kế trên tiền đề đã chết. Thêm hai cột đạt chuẩn vào bảng **sạch hơn** trong khi bảng **bẩn hơn**
  đứng yên là tối ưu đúng thứ đo được thay vì thứ đang hở.

- **Hệ quả:** `src/db/models.py` · `migrations/` · `contracts/agent-tools.yaml` (cơ chế truy vết ⟹ đi
  đủ §10 + baseline) · `tests/` (cổng cho cả hai bảng) · `docs/security/` (finding độc lập) ·
  ADR-025 QĐ3 (retention liệt kê theo **danh sách cột**, không theo **cây khoá ngoại** ⟹ bản plaintext
  có thể **sống sót sau khi bản mã hoá đã bị xoá** — ghim trước, đừng để job tự phát hiện lúc chạy).

## ADR-035 — `docker-compose*.yml` thuộc vùng ghi của `tech-lead`; §4 hiến pháp thiếu một dòng

- **Ngày:** 2026-08-18 · **Trạng thái:** Đang hiệu lực — PO thật chốt 18/08/2026
- **Bối cảnh:**

  Chốt chặn chi phí ở tầng transport (`src/egress_gate.py`, land 18/08) còn **một lỗ cuối**: cờ cho
  phép mặc định là **CHO PHÉP**, nên **script nháp** không được phủ — đúng đường tech-lead tự đâm vào
  khi dựng ca nghiệm thu. Đảo mặc định thành **TỪ CHỐI** đòi `docker-compose.yml` khai `=1`, nếu không
  **lần dựng tới sản phẩm chết**: mọi lượt chat và mọi lượt embedding bị chính chốt chặn của ta từ chối.

  **[ĐO] Và không vai nào ghi được file ấy.** Bảng §4 `CLAUDE.md`:
  ```
  po         → docs/ · *.md ở gốc              ← docker-compose.yml KHÔNG phải .md
  tech-lead  → src/ · frontend/src/ · migrations/ · contracts/
  tester · security · ux-ui · critic → không ai
  ```
  ⟹ **`docker-compose*.yml` không nằm trong vùng ghi của BẤT KỲ vai nào.** Đây không phải ai thiếu
  quyền — **hiến pháp thiếu một dòng**, và nó chỉ lộ ra 18/08 vì đây là lần đầu có việc cần sửa file ấy.

- **Quyết định:** thêm `docker-compose*.yml` vào vùng ghi của **`tech-lead`**.

- **Lý do:** compose khai **biến môi trường mà `src/` đọc lúc import** — nó là **phần nối dài của cấu
  hình `src/`**, không phải tài liệu. Người viết `src/config.py` là người duy nhất biết một biến được
  đọc lúc nào, đổi nó cần `recreate` hay `restart`, và mặc định nào làm sản phẩm chết. Tách hai thứ ấy
  cho hai vai là **tạo đúng loại lệch mà `build_stamp.py` sinh ra để chống**: *hai định nghĩa của cùng
  một vật sẽ lệch trong im lặng.*

- **Lý do BÁC BỎ *"để `po` giữ, vì compose là hạ tầng"*:** `po` **không đọc `src/`** ở mức đủ để biết
  một cờ được đọc lúc import hay lúc gọi — mà **chính điều đó** quyết định đổi cờ cần `recreate` hay
  không (§9 KHAI ≠ CHẠY). Một vai không kiểm chứng được hệ quả của dòng mình viết thì không nên giữ bút.

- **Lý do BÁC BỎ *"cấp quyền một lần cho đúng việc này"*:** quyền cấp theo từng ca **không để lại dấu
  vết đọc được** — lần sau người khác lại vấp đúng chỗ này và lại phải hỏi. Sửa bảng thì **hết vấp**.

- **Hệ quả:** `CLAUDE.md` §4 (hàng `tech-lead`) · `docs/STATE.md` §11 (bản nhắc lại) ·
  **KHÔNG** đụng `contracts/`, **KHÔNG** cần `check_contracts --update` — bảng phân vùng quyền ghi
  không phải một contract cấu trúc.
  ⚠️ **Ràng buộc thứ tự cho việc đang chờ:** dòng compose phải vào ảnh **TRƯỚC hoặc CÙNG LÚC** với việc
  đảo mặc định trong `src/`. Dán trước mà chưa đảo ⟹ **vô hại** (hành vi y hệt hôm nay). Đảo trước mà
  chưa dán ⟹ **sản phẩm chết ở lần dựng tới**. **Thứ tự an toàn: compose trước, `src/` sau.**

## ADR-036 — `fin05ttl` bị XOÁ, nhưng chỉ SAU khi ca đối chứng được dựng lại nơi khác; `fin05do` GIỮ

- **Ngày:** 2026-08-18 · **Trạng thái:** Đang hiệu lực — PO thật chốt 18/08/2026 (*"chốt theo ý bạn"*)
- **Bối cảnh:**

  Ba ngăn xếp Docker cục bộ. Backfill mã hoá ADR-032 ② **chỉ chạy trên `fin05`** (§5.O):
  ```
  [ĐO] complaints.description_raw          [ĐO] blob(messages) kho checkpoint
  fin05      mã hoá 761 · PLAINTEXT   0    fin05      3.597   105 MB
  fin05ttl   mã hoá   4 · PLAINTEXT 738    fin05ttl   2.482    95 MB
  fin05do    mã hoá 607 · PLAINTEXT   0    fin05do        62   127 kB
  ```
  Câu hỏi *"ngăn xếp dùng một lần, hay dữ liệu phải được bảo vệ như `fin05`"* **chưa ai định nghĩa**
  ⟹ 738 dòng lời khai khách nằm plaintext **không phải sự cố, mà là một phạm vi chưa được viết ra**.

  🔴 **Và giữa lúc chờ quyết, `fin05ttl` ĐỔI VAI:** tester dựng ca đối chứng **hai chiều** cho cổng
  plaintext trên chính quần thể bẩn ấy. Cổng chuyển ĐỎ→XANH nhờ backfill, nhưng nửa *"KÊU lúc bất
  thường"* của **Luật A** bỏ trống — và `fin05ttl` là **quần thể bẩn CÓ THẬT, sẵn có, không do ta tạo
  ra**, nên chứng minh được nửa ấy **mà không phải ghi vào ngăn xếp đang phục vụ** (Luật I).
  ⟹ **Xoá `fin05ttl` = tắt ca đối chứng DUY NHẤT chứng minh cổng plaintext còn sống.**

- **Quyết định 1 — `fin05ttl` XOÁ, theo ĐÚNG BA BƯỚC, không rút gọn:**
  ```
  ① tester dựng lại ca đối chứng trên một QUẦN THỂ VỨT ĐI (tạo riêng cho việc đó,
     KHÔNG phải ngăn xếp đang phục vụ)
  ② xác nhận ca mới ĐỎ đúng lúc cần đỏ  ← đây là bước nghiệm thu, không phải thủ tục
  ③ bây giờ mới xoá fin05ttl
  ```
  **Lý do thứ tự là một phần của quyết định, không phải lời khuyên:** đảo bước ① và ③ tạo một khoảng
  giữa **không ai biết cổng plaintext còn sống hay không**, và khoảng ấy **không có triệu chứng** —
  cổng vẫn xanh y hệt. Đó chính là hình dạng Luật A cảnh báo.

- **Quyết định 2 — TỪ NAY tới khi bước ③ xong, mọi phát biểu về mã hoá at-rest phải KÈM PHẠM VI.**
  Câu *"lời khai khách đã mã hoá at-rest"* **SAI với 738 dòng**. Dạng đúng: *"đã mã hoá **trên ngăn
  xếp phục vụ `fin05`**"*. Đây là **Luật F** (mẫu số cùng dòng) áp cho một phát biểu định tính.

- **Quyết định 3 — `fin05do` GIỮ.** Nó là ngăn xếp đo **duy nhất có kho RAG RỖNG** ⟹ đo được chi phí
  token **không lẫn nhiễu RAG**, mà đó đúng là trục ưu tiên PO đặt 18/08 (§5.A0: *tối ưu caching +
  token*). Chi phí giữ **127 kB**, không đáng đem ra cân.

- **Lý do BÁC BỎ *"xoá cả hai cho gọn"*:** gộp hai ngăn xếp vào một quyết định vì chúng **trông giống
  nhau** (đều là "ngăn xếp đo") trong khi chúng **khác nhau ở thứ quyết định**: một cái đang giữ ca đối
  chứng và 738 dòng plaintext, cái kia sạch và đang phục vụ trục ưu tiên hiện hành.

- **Lý do BÁC BỎ *"giữ `fin05ttl` vô thời hạn vì nó là tài sản kiểm thử"*:** giữ một quần thể bẩn làm
  dụng cụ đo nghĩa là **cột khả năng đo của đội vào việc KHÔNG BAO GIỜ vá 738 dòng ấy** — một dụng cụ
  chỉ hoạt động chừng nào lỗ còn mở. Ca đối chứng phải sống trên vật **ta dựng ra để vứt đi**, không
  phải trên vật **ta lỡ chưa dọn**.

- **Hệ quả:** `tests/` (ca đối chứng chuyển sang quần thể vứt đi) · `docs/STATE.md` §5.O + §2 (bảng ba
  ngăn xếp còn **hai**) · mọi tài liệu nói "mã hoá at-rest" phải rà lại phạm vi.
  ⚠️ **Ràng buộc còn hiệu lực sau khi xoá:** `fin05ttl` **mở cổng 8443** — xoá xong phải xác nhận cổng
  ấy không còn ai nghe, đừng để một ngăn xếp chết giữ cổng.
  🔴 **Quần thể thứ tư `app.adaptivealgo.uk` (production) NẰM NGOÀI ADR này** — chưa ai đo, không ai
  chạm. Đừng đọc "xoá `fin05ttl`" thành "chuyện plaintext đã đóng".

## ADR-037 — `.github/workflows/**` thuộc vùng ghi `tech-lead`; và CI chuyển sang runner self-hosted của BTC

- **Ngày:** 2026-08-18 · **Trạng thái:** Đang hiệu lực — PO thật chốt 18/08/2026
  ✅ **QĐ1 · QĐ2 phê chuẩn nguyên văn** (*"làm theo ý bạn đề xuất"*), gồm cả việc **giữ `deploy.yml`
  trên `ubuntu-latest`**.
  ✅ **QĐ3 mục 1 — ĐÃ ĐÓNG BẰNG PHÉP ĐO 18/08, KHÔNG CẦN BTC TRẢ LỜI. Kết quả: PERSISTENT.**
  [ĐO] tech-lead, log lượt 4: tệp mốc ghi ở job chạy trên `eph-vmrunner2-4938b971` **đọc lại được
  6 phút sau** từ job chạy trên `eph-vmrunner2-e0a3b5ab`. **Hai TÊN khác nhau, CÙNG một đĩa.**
  ⟹ Nhánh *"nếu hoá ra ephemeral"* trong định hạng security **KHÔNG áp dụng**; mức **CHẶN không hạ**.
  ⟹ Bước dọn `if: always()` chuyển từ **biện pháp phòng xa** sang **ĐIỀU KIỆN BẮT BUỘC** — và [ĐO]
  nó vẫn là **mã CHƯA TỪNG THỰC THI**.
  🔴 **CƠ CHẾ thì CHƯA biết, và hai khả năng khác hẳn nhau về mức độ:** (a) máy dùng lại, đăng ký lại
  dưới tên mới ⟹ rò rỉ theo **TỪNG MÁY** · (b) `$HOME` là mount **dùng chung cả hồ** ⟹ rò rỉ theo
  **CẢ HỒ**. **Giả định (b) cho tới khi có dữ kiện tách.**
  🔴 **ĐÍNH CHÍNH (security bắt, PO-agent đã chép suy luận sai vào bản trước):** *"5 job
  `eph-vmrunner-*` song song ⟹ **không thể là một máy** ⟹ (b)"* — **vế giữa SAI**. Năm **container
  trên MỘT nhân** cũng cho ra năm tên. ⟹ Quan sát song song **không loại được (a)**, nó chỉ **không
  loại được (b)**. Hai câu khác nhau, và bản trước dùng nó như bằng chứng NGHIÊNG VỀ (b).
  ⚠️ **VÀ (a)/(b) KHÔNG ĐỔI ĐỊNH HẠNG — security nói trước để nó không bị chôn:** cả hai đều là
  **CHẶN**, và **bản vá dọn GIỐNG HỆT NHAU**. ⟹ **Đừng để câu (a)/(b) hoãn bản vá** — nó **không nằm
  trên đường tới hạn**. Nó chỉ đổi **bán kính** (từng máy ↔ cả hồ), **độ gấp của việc xoay khoá nếu
  lỡ có job đã chạy** (dưới (b): một lượt là đủ để xoay, không cần bàn), và **câu nói với BTC**
  (*"máy của các anh giữ tệp giữa các job"* ↔ *"các team đang đọc được đĩa của nhau"*).
  ⭐ **VÀ ĐIỀU KIỆN DỨT ĐIỂM CẢ HAI PHIÊN CÙNG ĐẶT RA — *"hai lượt trúng CÙNG TÊN MÁY"* — LÀ ĐIỀU KIỆN
  SAI.** Nó không bao giờ xảy ra; chờ nó là chờ mãi trong khi bằng chứng đã nằm sẵn.
  ```
  giả định ngầm :  tên máy khác  ⟹  đĩa khác
  thực tế       :  tên máy khác,  ĐĨA VẪN CHUNG
  ```
  Bài học **không phải** *"`eph-` là tên dối"* mà là: **cả cái TÊN lẫn cái PHÉP THỬ ta dựng ra để kiểm
  cái tên đều đứng trên CÙNG MỘT giả định chưa ai kiểm.** Phép đo cứu được **chỉ vì nó hỏi thẳng thứ
  ta quan tâm** (*tệp có còn không*), không hỏi thứ **đại diện** cho nó (*tên có trùng không*).
  ⟹ **PO vẫn nên hỏi BTC, nhưng câu đã đổi:** không còn *"có ephemeral không"* (đã biết: KHÔNG) mà
  ***"`$HOME` của runner có dùng chung giữa các máy trong hồ không, và hồ có bao nhiêu máy?"***
  🔴 **HỆ QUẢ CỦA VIỆC HOÃN, ĐỌC KỸ:** chưa có câu trả lời ⟹ **giả định AN TOÀN là PERSISTENT**
  (máy dùng lại giữa các job và giữa các team). Suy ngược lại — *"chắc là ephemeral"* — là chọn giả
  định **dễ chịu nhất** thay vì giả định **đắt nhất khi sai**.
  ⟹ **QĐ3 mục 3 (`if: always()` cho bước dọn `.env`) KHÔNG ĐƯỢC CHỜ mục 1.** Nó là biện pháp
  **đúng dù câu trả lời là gì**, và **cần hơn** khi chưa biết. Buộc nó vào một câu hỏi đang treo là
  cách chắc chắn nhất để nó không được làm — đúng lý lẽ ADR-034 QĐ3.
  ⏸ **QĐ3 mục 2 (security định hạng)** phụ thuộc mục 1 ⟹ chờ.
- **Bối cảnh:**

  Từ 17/08 tới nay **không commit nào qua cổng tự động**. [ĐO] annotation nguyên văn GitHub trên
  mọi run: *"The job **was not started** because recent account payments have failed…"* — và
  `gh run view --job … --log` trả **`log not found`, 0 dòng**: job chưa bao giờ được cấp máy, nên
  không có log để mà đọc. **Không phải lỗi code** — mọi commit, kể cả commit rỗng, cho kết quả y hệt.

  **BTC ra hướng dẫn:** đổi workflow sang `runs-on: self-hosted` để dùng runner dùng chung của
  chương trình (FIFO, **chia sẻ giữa TẤT CẢ các team**); team muốn chủ động thì tự host, mở ticket.

  🔴 **[ĐO] Và không vai nào ghi được `.github/`.** Bảng §4 `CLAUDE.md`:
  ```
  po         → docs/ · *.md ở gốc            ← ci.yml KHÔNG phải .md
  tech-lead  → src/ · frontend/src/ · migrations/ · docker-compose*.yml · contracts/
  còn lại    → không ai
  ```
  ⟹ **Lỗ §4 THỨ HAI, cùng lớp ADR-035** — và lần này còn mâu thuẫn với chính định nghĩa vai:
  mô tả agent `tech-lead` ghi rõ *"dựng CI"*, nhưng bảng quyền không cho họ chạm file CI.
  **Một lần là thiếu sót; hai lần là bảng §4 được viết theo thứ ĐÃ ĐỘNG TỚI, không theo thứ TỒN TẠI.**

- **Quyết định 1 — thêm `.github/workflows/**` vào vùng ghi của `tech-lead`.**
  Cùng lý lẽ ADR-035: CI khai **môi trường mà `src/` chạy trong đó**; người viết `src/` là người duy
  nhất biết một biến được đọc lúc nào và một job cần dịch vụ gì. **Bác "cấp quyền một lần cho đúng
  việc này"** — quyền theo ca không để lại dấu vết, lần sau lại vấp; đây là lần **thứ hai** vấp.

- **Quyết định 2 — `ci.yml` (14 job) chuyển `self-hosted`; `deploy.yml` (1 job) GIỮ `ubuntu-latest`.**

  [ĐO] `grep -rn "runs-on:"` → **15 dòng**: `ci.yml` 14 · `deploy.yml` 1.

  🔴 **ĐÍNH CHÍNH NGAY TRONG ADR NÀY (PO-agent tự bắt, cùng phiên):** bản đầu viết *"`deploy.yml`
  **mang** `secrets.DEPLOY_SSH_KEY`"*. **SAI** — nó **KHAI** secret ấy, không **CÓ** nó.
  [ĐO] `gh secret list` → **DUY NHẤT `OPENAI_API_KEY`**. `DEPLOY_HOST` · `DEPLOY_USER` ·
  `DEPLOY_SSH_KEY` **chưa tồn tại**. Tôi đọc `${{ secrets.X }}` trong tệp YAML rồi kết luận về kho
  secret — **đúng lớp lỗi Luật Q (KHAI ≠ CÓ), mắc phải một lượt sau khi tự đúc ra nó.**

  **Lý do tách đúng ở ranh giới này — phát biểu lại cho đúng:** hôm nay `deploy.yml` **không phơi
  nhiễm gì** (không có khoá để mà lộ) và đang **skipped** ở mọi run ⟹ chuyển nó **không mua được
  gì**. Nhưng nó **được thiết kế để mang** khoá SSH vào production, và **ngày PO đặt secret ấy là
  ngày phơi nhiễm bắt đầu** — lúc đó **sẽ không ai quay lại đọc dòng `runs-on` này**. Chính tệp
  `deploy.yml` tự gọi đó là *"quả mìn hẹn giờ: nổ đúng vào lúc PO đặt secret để deploy lần đầu"*.
  ⟹ **Quyết định BÂY GIỜ, khi nó còn rẻ và còn thấy được.** Rẻ nhất là để yên trên `ubuntu-latest`.

- **🔴 Quyết định 3 — RỦI RO PHẢI KHAI RA, KHÔNG ĐƯỢC ĐỂ IM.**

  [ĐO] phân loại 14 job theo khoá chúng mang:
  ```
  8 job  khoá GIẢ  (ci-dummy / test-key-…)         → chuyển sang máy dùng chung: KHÔNG thêm phơi nhiễm
  6 job  khoá THẬT (secrets.OPENAI_API_KEY)        → khoá thật vào biến môi trường trên máy dùng chung
  ├─ 2 trong số đó GHI KHOÁ THẬT RA TỆP `.env` TRÊN ĐĨA runner  (ci.yml:554 · ci.yml:618)
  │  route-guards-docker · livechat-e2e-nightly
  ```
  **Runner dùng chung KHÔNG khởi động sạch giữa các job** (trừ khi BTC cấu hình ephemeral) ⟹ một
  tệp `.env` chứa khoá thật **có thể còn lại trên đĩa** sau khi job bị huỷ giữa chừng, và máy ấy
  **chạy job của team khác**. Đây **không phải suy đoán**: hai dòng ghi tệp là đo được, và tính
  "dùng chung" là do chính BTC khai.

  **Ba việc kèm theo, không cái nào thay được cái nào:**
  1. **Hỏi BTC MỘT câu cụ thể:** *runner có phải **ephemeral** (huỷ sau mỗi job) không?* Có ⟹ rủi ro
     tệp `.env` tan. Không ⟹ giữ nguyên mức, sang việc 2.
  2. **`security` định hạng** phơi nhiễm khoá OpenAI thật trên máy dùng chung, và trả lời: có cần
     **xoay khoá** sau khi cohort kết thúc không.
  3. **Bước dọn `.env` bắt buộc `if: always()`** ở hai job ghi tệp — dọn chỉ chạy khi job thành công
     là **không dọn ở đúng lúc cần dọn nhất**.
     🔴 **ĐÍNH CHÍNH 18/08 (PO-agent, khi đi triển khai mục này):** câu trên **giả định bước dọn đã
     tồn tại**. [ĐO] `grep -n "rm .env|compose down|always()" ci.yml` → **5 hit `always()`, CẢ NĂM là
     `upload-artifact`; 0 hit `rm .env`; 0 hit `compose down`**. ⟹ **KHÔNG CÓ bước dọn nào trong toàn
     bộ `ci.yml`.** Việc là **THÊM bước**, không phải bật cờ trên bước có sẵn.
     ⟹ **Phơi nhiễm nặng hơn đã ghi:** `.env` chứa khoá thật bị bỏ lại sau **MỌI** lần chạy, không
     chỉ lần bị huỷ; và **không `compose down`** ⟹ container **chạy tiếp** sau job, giữ cổng + giữ
     volume CSDL của lượt CI.
     ⭐ **Và đây là phần đáng ghi nhất:** trên `ubuntu-latest` **không ai thấy**, vì cả máy ảo bị huỷ
     sau mỗi job. Đội đã dựa vào tính ephemeral của GitHub **suốt từ đầu mà không ai biết là mình
     đang dựa vào nó** — nó không được khai ở đâu, không test nào canh. Chuyển runner là **rút cái
     lưới ấy đi**. *(Cùng hình dạng Luật G: một cơ chế đang gánh một việc **ta không giao cho nó**.)*

- **Lý do BÁC BỎ *"chuyển trước 8 job khoá giả, giữ 6 job kia chờ security"*:** nghe thận trọng nhưng
  cho ra **một CI vẫn ĐỎ** — 6 job kia vẫn `ubuntu-latest` nên vẫn `was not started`. Và tệ hơn:
  **đỏ vì HAI lý do khác nhau trong cùng một bảng** thì người đọc không phân biệt được cái nào là
  code hỏng, cái nào là hạ tầng. Một tín hiệu trộn hai nguyên nhân **tệ hơn một tín hiệu đỏ sạch**.

- **Lý do BÁC BỎ *"tự host runner của team ngay"*:** BTC có mở đường (mở ticket), nhưng nó đổi một
  vấn đề **chờ hàng đợi** thành một vấn đề **vận hành một máy** — trong khi thứ đang chặn là
  *"job không được cấp máy"*, mà runner BTC giải quyết được **hôm nay, không tốn gì**. Giữ đường tự
  host làm **phương án B nếu hàng đợi FIFO quá chậm**, không phải bước đầu.

- **Điều kiện tiên quyết PHẢI KIỂM, KHÔNG ĐƯỢC GIẢ ĐỊNH** (runner BTC không nhất thiết có sẵn như
  `ubuntu-latest`): **Docker** (job dùng `services: postgres:16-alpine` **và** `docker compose up
  -d --build`) · **Docker Compose v2** · quyền chạy `actions/setup-python@v5` + `actions/setup-node@v4`.
  ⚠️ **Và cổng bị đụng nhau:** `docker compose` của ta publish cổng ra host; hai team chạy cùng lúc
  trên **một** runner ⟹ đụng cổng ⟹ **cổng đỏ vì lý do không liên quan gì tới code ta**.
  ⟹ **Bắt buộc `-p` với tên project DUY NHẤT theo run** (vd `-p fin05-ci-${{ github.run_id }}`).

- **Hệ quả:** `CLAUDE.md` §4 (hàng `tech-lead`) · `.github/workflows/ci.yml` (14 dòng) ·
  `docs/STATE.md` §11 · `docs/security/` (định hạng của việc 2).
  **KHÔNG** đụng `contracts/`, **KHÔNG** cần `check_contracts --update`.

## ADR-038 — Cấp chủ cho TOÀN BỘ thư mục gốc, một lần; và quy tắc mặc định cho thứ chưa cấp

- **Ngày:** 2026-08-18 · **Trạng thái:** ⏳ **CHỜ PO THẬT PHÊ CHUẨN**
- **Bối cảnh:**

  **BA lần trong một ngày** bảng §4 thiếu một dòng, và **cả ba chỉ lộ ra đúng lúc có việc cần sửa
  tệp ấy**:
  ```
  ADR-035   docker-compose*.yml     → cần đảo mặc định cờ chi phí
  ADR-037   .github/workflows/**    → cần chuyển CI sang runner BTC
  ca 3      ruff.toml               → [ĐO] target-version="py311" trong khi CI chạy Python 3.12.14
                                       ⟹ 2/57 lỗi lint là LỆCH CẤU HÌNH, không phải mã hỏng
  ```
  Vá lần thứ ba bằng lần thứ ba **một-dòng-một-ADR** là chữa triệu chứng. **Vấn đề không phải ba tệp
  bị bỏ sót — mà là bảng §4 được viết theo thứ đội ĐÃ ĐỘNG TỚI**, nên nó **luôn** thiếu đúng thứ
  người tiếp theo sắp cần.

  **[ĐO] kiểm kê gốc (`git ls-files`, 18/08) — thứ CHƯA có chủ:**
  ```
  Dockerfile · Caddyfile · docker-entrypoint.sh · .dockerignore
  alembic.ini · requirements.txt · requirements.lock.txt
  ruff.toml · pytest.ini · Makefile · .gitignore · .gitleaks.toml
  FIN05_QA_TestCases.jsonl · FIN05_Auth5_TestCases.jsonl
  ```
  *(Đã có chủ: `*.md` gốc → `po` · `FIN05-Wireframe-UXUI.html` → `ux-ui`.)*

- **Quyết định 1 — cấp chủ, theo nguyên tắc "ai kiểm chứng được hệ quả thì cầm bút" (ADR-035):**

  | vai | thêm vào vùng ghi | vì sao |
  |---|---|---|
  | `tech-lead` | `Dockerfile` · `Caddyfile` · `docker-entrypoint.sh` · `.dockerignore` · `alembic.ini` · `requirements*.txt` · `ruff.toml` · `Makefile` · `.gitignore` · `.gitleaks.toml` | đều khai **môi trường `src/` chạy trong đó** hoặc **công cụ áp lên `src/`**; chỉ người viết `src/` kiểm được hệ quả |
  | `tester` | `pytest.ini` · `FIN05_*TestCases.jsonl` ở gốc | `pytest.ini` là cấu hình **bộ chạy test** — cùng vật với `tests/`; hai tệp `jsonl` là **ca kiểm thử** đặt nhầm chỗ |

- **🔴 Quyết định 2 — QUY TẮC MẶC ĐỊNH. Đây mới là thứ chặn lần thứ TƯ.**
  > **Mọi đường dẫn ở gốc KHÔNG được liệt kê ở §4 mặc định thuộc `tech-lead`** — **NHƯNG** vai nào
  > chạm vào nó lần đầu **phải ghi một dòng vào §4 trong cùng commit ấy**.
  Mặc định giữ cho công việc **không bị chặn** bởi một khoảng trống hành chính; nghĩa vụ ghi lại giữ
  cho bảng **tự lấp** thay vì phải chờ một ADR nữa. **Cấp chủ không cần ADR; ĐỔI chủ thì cần.**

- **Lý do BÁC BỎ *"cứ vá từng tệp khi cần"*:** đó chính là thứ đã làm ba lần và **sẽ có lần thứ tư** —
  chi phí không nằm ở dòng sửa mà ở **việc dừng lại, hỏi, chờ duyệt** mỗi lần, và ở chỗ **người bị
  chặn luôn là người đang có việc gấp**.

- **Lý do BÁC BỎ *"cấp hết cho `tech-lead`, khỏi phân loại"*:** `pytest.ini` quyết **ca nào được thu
  thập**. Đưa nó cho vai **không được đọc `tests/`** là tạo đúng loại lệch mà tường §11 sinh ra để
  chống — người sửa không đọc được thứ mình đang đổi hành vi.

- **Hệ quả:** `CLAUDE.md` §4 · `docs/STATE.md` §11. **KHÔNG** đụng `contracts/`.
  ⚠️ **Việc đầu tiên mở khoá bởi ADR này:** `ruff.toml` `target-version="py311"` → `py312` cho khớp
  runtime (`python-version: "3.12"`, ảnh `Python 3.12.14`). [ĐO] tech-lead đã xác nhận bằng
  `ast.parse` trong container: tệp bị báo `invalid-syntax` **parse OK trên 3.12**. **Lỗi ở thước, không
  ở vật.**

## ADR-039 — Harness cần THU GOM RÁC: nguyên tắc vàng ghi một lần, dọn nhỏ mỗi ngày

- **Ngày:** 2026-08-18 · **Trạng thái:** Đang hiệu lực — **PO thật ra lệnh trực tiếp**, quyền cao nhất
- **Bối cảnh:**

  [ĐO] 18/08, kho tri thức của dự án:
  ```
  CLAUDE.md            139 dòng / trần 200
  docs/STATE.md      1.770 dòng   ← ĐÃ TỪNG 3.001, bị dọn MỘT CÚ xuống 1.770
  docs/DECISIONS.md  2.297 dòng · 39 ADR
  17 luật chữ · 19 luật số · 24 mục §5
  ```
  **Riêng 18/08: 89 commit, 55 là `docs` (62%).** Ba `feat`, năm `fix`, một `migrations`.

  🔴 **Và con số tự tố cáo cơ chế:** STATE.md **từng phình tới 3.001 dòng rồi bị dọn một cú**. Đó không
  phải bảo trì — đó là **vỡ nợ rồi xoá nợ**. Giữa hai lần vỡ, kho ở trạng thái **không ai đọc hết**.

  **Vì sao đây là vấn đề THẬT chứ không phải gọn gàng:** đội đúc luật để phiên sau không lặp lại sai
  lầm. Nhưng **một luật không ai đọc có giá trị bằng không** — và **17 luật chữ + 19 luật số vượt xa
  thứ một người đọc nguội giữ được trong đầu**. Kho phình ra **không làm đội thông minh hơn; nó làm
  mọi luật trong đó rẻ đi như nhau.**

- **Quyết định — BA TẦNG, BA LUẬT KHÁC NHAU. Áp nhầm tầng là hỏng.**

  | tầng | tệp | luật |
  |---|---|---|
  | nguyên tắc vàng | `CLAUDE.md` | ghi **MỘT LẦN** · trần **200 dòng** · thêm một dòng ⟹ một dòng **ra đi** |
  | trạng thái làm việc | `docs/STATE.md` | **DỌN MỖI NGÀY** — mục đã đóng → lưu trữ; luật trùng ý → gộp |
  | sổ quyết định | `docs/DECISIONS.md` | **CHỈ GHI THÊM** — nhưng ADR bị thay thế phải **tự khai** |

  **Dọn nhỏ cuối mỗi phiên (`/wrapup`) — vài phút, KHÔNG phải một dự án:** ① mục §5 đã đóng → chuyển
  `docs/nhat-ky/`, để lại **một dòng trỏ tới** · ② hai luật cùng ý ⟹ **gộp**, giữ ký hiệu cũ hơn ·
  ③ con số đã làm cũ ⟹ **NIÊM tại chỗ** kèm mốc (Luật P).

  **Phép thử trước khi thêm bất cứ thứ gì:** ***"người đọc NGUỘI sẽ đọc hết chỗ này chứ?"*** Không ⟹
  thứ sắp thêm **không làm kho giàu hơn, nó làm phần còn lại nghèo đi**.

- **Lý do BÁC BỎ *"cứ ghi hết, dọn khi nào phình quá"*:** đó **chính là thứ đã làm** — và kết quả là
  3.001 dòng rồi một cú dọn. Dọn theo đợt lớn **đắt hơn và mất mát hơn**: người dọn hàng loạt không
  còn nhớ ngữ cảnh của từng mục, nên **cắt theo độ dài thay vì theo giá trị**.

- **🔴 Lý do BÁC BỎ *"xoá thẳng cho gọn"*:** dọn **KHÔNG PHẢI** xoá lịch sử. Xoá thẳng một phát hiện là
  bắt phiên sau **phát hiện lại từ đầu** — đắt hơn hẳn việc giữ một dòng trỏ tới. **Chuyển chỗ, để lại
  đường dẫn.**

- **Hệ quả:** `CLAUDE.md` §7b (mới) · `.claude/commands/wrapup` nên nhắc bước dọn ·
  `docs/nhat-ky/` là nơi nhận mục đã đóng.

## ADR-040 — DỜI cổng finding bảo mật từ CI sang BƯỚC DEPLOY. Không tắt, không gỡ nhãn.

- **Ngày:** 2026-08-18 · **Trạng thái:** Đang hiệu lực — **PO thật chốt 18/08** (*"dời lại nhưng phải
  note lại để không ai quên"*). Phát hiện + đề xuất: **security** (`6c5bbb3`, §19).
- **Bối cảnh:**

  ```
  [ĐO] ci.yml:251-262  security-findings-gate  chạy `pytest -m security_finding`
       KHÔNG có continue-on-error  ⟹  job ĐỎ LIÊN TỤC TỪ 12/08 — SÁU NGÀY
  ```

  > ## Một cái chuông kêu liên tục sáu ngày không còn là một cái chuông.
  **Luật A vế một:** *cổng phải IM lúc bình thường.* Cổng này **chưa bao giờ im** ⟹ nó **đã bị vô hiệu
  hoá bằng THÓI QUEN, không bằng quyết định.**

  🔴 **Và finding nó canh thì KHÔNG vá được theo cách test đòi.** Test khẳng định
  `raw_phone not in saved["content"]` = **che LÚC GHI**. **ADR-025 QĐ1 (ký 15/08, ba ngày SAU khi
  finding mở) BÁC đúng điều đó**: *hệ thống tự sửa chữ trong lời khai thì bản ghi **mất giá trị chứng
  cứ** (NHNN/toà)*. ⟹ **Bản vá làm test xanh sẽ vi phạm một ADR PO đã ký.** *"Chưa vá"* ở đây
  **không phải nợ kỹ thuật — là TUÂN THỦ.**

  ⚠️ **Nguy hiểm thật của nguyên trạng không phải PII:** một cổng đỏ dai dẳng mang nhãn **P0**, đặt
  trước người đang chịu áp lực gộp `main`, là **một lời mời sửa nó** — và cách sửa rẻ nhất **phá giá
  trị chứng cứ của lời khai**, trong khi **CI sẽ XANH HƠN sau khi phá**.

- **Quyết định 1 — DỜI, không TẮT.**
  ```
  BỎ    job CI đỏ vĩnh viễn        (đã habituate, không ai còn đọc)
  THÊM  cổng ở BƯỚC DEPLOY PRODUCTION:  `pytest -m security_finding` đỏ  ⟹  CHẶN deploy
  ```

- **🔴 Quyết định 2 — LUẬT KHÔNG ĐƯỢC QUÊN. Đây là lý do PO bắt ghi lại.**
  > ***"Chấp nhận rủi ro cho `main`" KHÔNG được lặng lẽ trở thành "chấp nhận rủi ro cho PRODUCTION".***
  Cổng deploy **chính là cơ chế** ép điều đó: nó bắn đúng vào **SỰ KIỆN làm đổi mức**, nên **mức không
  cần tự nhảy** — **việc deploy bị CHẶN cho tới khi có người quyết lần nữa.**
  ⟹ Biến *"chấp nhận rủi ro"* từ **một câu nói** thành **một trạng thái có cơ chế**.
  **Ai gỡ cổng này phải trả lời được: điều gì thay thế nó ép ra quyết định thứ hai?**

- **🔴 Quyết định 3 — CA ĐỐI CHỨNG BẮT BUỘC trước khi tin cổng mới.**
  Chạy một lần với **finding giả** để xem nó **THẬT SỰ CHẶN**. *(Luật A vế hai · Luật R vế ④.)*
  **Một cổng deploy chưa từng chặn gì không phân biệt được với một cổng deploy hỏng** — và ta sẽ chỉ
  phát hiện vào **đúng ngày cần nó**.

- **Quyết định 4 — cách "chấp nhận" ĐƯỢC PHÉP và KHÔNG được phép.**
  🚫 **KHÔNG** gỡ `@pytest.mark.security_finding`, **KHÔNG** đổi thành `xfail` trơn — `ci.yml:367` đã
  cấm, **GIỮ lệnh cấm**. Đổi trạng thái test thì phải đổi **KÈM LÝ DO trong docstring**:
  *"assertion này đòi thứ ADR-025 QĐ1 bác"*.

- **Lý do BÁC BỎ *"để nguyên job CI đỏ"*:** sáu ngày đã chứng minh nó không được đọc. Giữ một cổng
  không ai đọc **đắt hơn bỏ nó**, vì nó **chiếm chỗ** của cổng thật *(Luật R vế ④)*.
- **Lý do BÁC BỎ *"gỡ nhãn cho CI xanh"*:** đó là **tắt chuông**, và nó biến chuông-hỏng thành
  **KHÔNG-CÓ-CHUÔNG**.

- **Hệ quả:** `.github/workflows/ci.yml` (bỏ job) · **bước deploy** (thêm cổng) · `tests/` (ca đối
  chứng) · `docs/security/` §19.
  📌 **CÒN NỢ, security mở, chưa ai quyết:** `messages.content` phân loại **Nhóm A "lời khai KHÁCH"**
  nhưng [ĐO] chứa **staff 237 / customer 230** — **nhiều chữ NHÂN VIÊN hơn chữ khách**. Trục phân loại
  (**theo CỘT**) không cắt đúng trục ADR-025 tự khai (**theo AI SỬA LẠI ĐƯỢC**). Cần ADR riêng.

## ADR-041 — Vé phải hiện TOÀN BỘ hội thoại. Lời agent ghi vào `messages`, không đọc từ checkpoint.

- **Ngày:** 2026-08-18 · **Trạng thái:** Đang hiệu lực — **PO thật chốt 18/08**
  (*"CSKH và sếp mở vé phải thấy toàn bộ đoạn hội thoại — như thế họ mới có đủ dữ liệu"*)
- **Bối cảnh:**

  ```
  [ĐO] Message(...) tạo ở ĐÚNG MỘT nơi   live_chat.record_message
       gọi từ ĐÚNG MỘT nơi                live_chat_ws.py:578
       với  role = "staff" if is_staff else "customer"
  ⟹ KHÔNG đường mã nào ghi được `agent` hay `system`
  [ĐO] messages.role   staff 237 · customer 230 · agent 0 · system 0   (467 tin)
  [ĐO] lời AI nằm ở checkpoint LangGraph — `checkpoints` 4.682 · `checkpoint_writes` 6.405
  [ĐO] GET /live-chat/sessions/{id}/messages  đọc DUY NHẤT bảng `messages`
  ```

  ⟹ **CSKH mở một vé chỉ thấy NỬA cuộc hội thoại — phần người.** Phần AI đã nói với khách
  **không màn hình nào đọc**. Với sản phẩm mà toàn bộ giá trị là *"AI điều tra rồi bàn giao cho
  người"*, đây là chỗ đứt ngay tại **điểm bàn giao**.

  ⭐ **Và `ck_messages_role` ĐÃ cho phép `agent` từ đầu.** Nhãn chết ấy **không phải rác — nó là dấu
  vết của một thiết kế đã lường trước việc này rồi chưa ai xây.** *(Tìm ra bởi cổng độ phủ nhãn của
  tester, tức bởi một cơ chế dựng cho việc khác — dữ liệu rỗng chỉ ra một tính năng thiếu.)*

- **Quyết định 1 — GHI lời agent vào `messages` (`role='agent'`), KHÔNG đọc từ checkpoint lúc hiển thị.**

  **Lý do BÁC "đọc checkpoint lúc hiển thị":** `checkpoint_blobs` là **schema ta KHÔNG sở hữu** —
  LangGraph đổi định dạng nội bộ là màn hình vé vỡ, **và không test nào của ta canh được**. Đọc từ
  bảng ta sở hữu thì hình dạng do ta quyết.
  **Lý do phụ, nhưng quyết định về lâu dài:** PO đã nêu ý định **dùng AI tóm tắt hội thoại CSKH↔khách**.
  Tóm tắt từ **một bảng có `role`** là một truy vấn; tóm tắt bằng cách ghép **hai kho khác hình dạng**
  là một dự án. **Quyết định hôm nay quyết luôn chi phí của tính năng đó.**

- **Quyết định 2 — `messages` đổi NGHĨA, và phải khai lại.**
  Nó thôi là *"biên bản live-chat khách↔người"*, thành ***"biên bản hội thoại của một vé, mọi bên nói"***.
  ⚠️ **Mọi truy vấn/thống kê đang ngầm giả định "chỉ có người"** phải rà lại — thêm `role='agent'` sẽ
  **đổi mẫu số của chúng trong im lặng**. Đây là việc bắt buộc, không phải tuỳ chọn.

- **🔴 Quyết định 3 — chạm ADR-025, phải giải trước khi code.**
  ADR-025 xếp `messages.content` vào **Nhóm A ("lời khai KHÁCH", CẤM che-lúc-ghi)**. Nhưng [ĐO] cột ấy
  đã chứa **staff 237 > customer 230**, và security đã mở finding: **trục phân loại (theo CỘT) không
  cắt đúng trục ADR tự khai (theo AI SỬA LẠI ĐƯỢC)**. Thêm `role='agent'` đưa vào cột ấy **loại thứ
  ba** — chữ do **máy** sinh, không ai "sửa lại được", và **không phải lời khai của ai**.
  ⟹ **`security` phải phân loại `role='agent'` TRƯỚC khi tech-lead ghi dòng đầu tiên.** Ghi trước rồi
  phân loại sau là tạo một quần thể phải backfill — đúng thứ ADR-032 vừa dạy ta cái giá.

- **Quyết định 4 — thứ tự: SAU bản cắt `main`.**
  Đây là **tính năng**, không phải hỏng. Bản `main` ổn định không đợi nó. Nhưng **ADR ghi bây giờ**,
  lúc còn nhìn thấy đủ ngữ cảnh — không phải lúc ai đó vấp lại vào nó.

- **Hệ quả:** `src/services/live_chat.py` · `src/agents/graph.py` (điểm ghi) · `contracts/` nếu route
  đổi hình dạng (⟹ đủ §10 + baseline) · `tests/` · `docs/security/` (QĐ3) · cổng độ phủ nhãn của
  tester **tự chuyển xanh** cho `messages.role=agent` khi việc này xong — **đừng sinh dòng demo giả
  để thắp nó trước** (tester đã từ chối một lần, giữ nguyên lằn ranh ấy).

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

## ADR-042 — `tool_calls` trên dây là MẢNG ở mọi đường; ba-trạng-thái sống ở `ly_do_fallback`

- **Ngày:** 2026-08-19 · **Người quyết:** PO-agent (thẩm quyền hợp đồng envelope; PO thật đặt mục
  tiêu "chatbot phải chạy cho khách test") · **Trạng thái:** Đang hiệu lực
- **Bối cảnh:** GĐ2 vá `tool_calls: None` làm vỡ UI (client `.length` trên null → khách thấy
  "Có lỗi khi kết nối trợ lý"). Coder vá 3/4 đường; đường thứ tư (vòng-lặp-tool, GraphRecursionError)
  CỐ Ý giữ `None` để tôn trọng thiết kế 15/08
  (`tests/test_security/test_fallback_khong_goi_bo_loc.py::test_tool_calls_la_none_chu_khong_phai_rong`):
  *"None = không khôi phục được ≠ [] = đo được là không gọi tool"* — kèm số đo thật (4/5 bản ghi
  tool_calls rỗng không đi qua fallback ⟹ [] không suy ngược ra fallback).
- **Quyết định:** Hợp đồng DÂY (envelope trả client) — `tool_calls` là MẢNG trên MỌI đường, kể cả
  vòng-lặp-tool. Ngữ nghĩa ba-trạng-thái KHÔNG bị bỏ: nó sống ở `ly_do_fallback` — trường đã tồn
  tại, đã khác `None` trên đúng cả ba đường fallback ([ĐO] 19/08: `:811 "qua_tai"` · `:930` ·
  `:1036 _ly_do_fallback(e)`), và đã được `_ghi_so` chép vào sổ usage (`:220`). Bộ chấm downstream
  phân biệt "không gọi tool" với "không khôi phục được" bằng `ly_do_fallback`, không bằng KIỂU của
  `tool_calls`.
- **Lý do:** (1) Đường giữ-None là đường livelock — fallback ở đó là CÂU BÀN GIAO KÈM MÃ VÉ, đúng
  thứ test hàng xóm (`…ticket_id in reply`) chứng minh khách PHẢI đọc được; giữ None nghĩa là client
  vỡ và khách không bao giờ thấy mã vé — "ngõ cụt lịch sự" tái sinh ở tầng client. (2) Nhồi ngữ
  nghĩa vào KIỂU của một trường hợp đồng dây là dùng type làm kênh tín hiệu — client không đọc được
  tín hiệu ấy, chỉ vỡ vì nó.
- **Lý do BÁC BỎ phương án khác:** *"Giữ None + client phòng thủ `?? []`"* — client phòng thủ là che
  triệu chứng ở một client; mọi client tương lai (mobile, đối tác) vỡ lại từ đầu; và `?? []` chính
  là hình dạng `or []` vừa nuốt mất lỗi này trong script verify 19/08. *"Thêm trường mới
  `tool_calls_unknown`"* — `ly_do_fallback` đã là trường đó.
- **Hệ quả:** `src/agents/graph.py` literal thứ tư `None → []` (Coder) ·
  `tests/test_security/test_fallback_khong_goi_bo_loc.py::test_tool_calls_la_none_chu_khong_phai_rong`
  viết lại: assert `tool_calls == []` VÀ `ly_do_fallback is not None` trên fallback, đổi TÊN khớp
  assertion mới (tester — giữ nguyên phần số đo 15/08 trong docstring làm sử liệu) ·
  `tests/test_api/test_gd2_tool_calls_khong_null.py::test_trong_vong_lap_tool_van_giu_none_co_chu_dich`
  đảo chiều thành đối chứng dương của ADR này (QA/QC) · sổ nợ ③ của Lead (`:219 or []`) tự đóng —
  sau ADR này `or []` ở đó hết mơ hồ vì không còn None nào để nuốt.

### ADR-042 · ĐÍNH CHÍNH THI HÀNH — cùng ngày 19/08, sau phản biện có số đo của Lead

- **Tiền đề "khách không thấy mã vé" SAI trên cây hiện tại — lỗi dụng cụ của chính PO-agent:**
  phép đo dựng ADR là `git show 641b68c -- src/agents/graph.py` — **tự lọc còn MỘT file trong một
  commit HAI file**, nên thấy "3/4 literal" mà không thấy nửa còn lại: **chuẩn hoá tại BIÊN**
  (`main.py:659` `result["tool_calls"] = result.get("tool_calls") or []`, kèm lý do đặt tại route).
  [ĐO] kiểm lại độc lập 19/08: biên trả MẢNG qua HTTP thật trên chính nhánh vòng-lặp (test
  `…bien_vong_lap_tool_khong_de_null_vuot_bien` ép nhánh chạy thật, đọc RAW JSON) — khách VẪN thấy
  mã vé. *(Ca thứ sáu trong ngày của cùng một hình dạng: dụng cụ trả về câu trả lời trông hợp lệ
  cho một câu hỏi đã bị chính lệnh đo cắt hẹp.)*
- **RÚT việc ① (đổi literal thứ tư) và việc ② (viết lại test 15/08).** Lý do rút: mục tiêu của
  chúng đã đạt bằng đường khác đang có cổng canh; thi hành thêm là trả giá thật (mất phân biệt
  ba-trạng-thái NỘI BỘ có tài liệu + vô hiệu một ca canh đang đúng) để mua một lợi ích đã có.
- **QUYẾT ĐỊNH KIẾN TRÚC CHỐT LẠI (phần sống lâu nhất — đề xuất của Lead):** ranh giới TRONG/BIÊN:
  **BÊN TRONG** (`run_agent_turn`, checkpoint, sổ usage, eval đọc thẳng graph) — `tool_calls` giữ đủ
  BA trạng thái (`None` = không khôi phục được · `[]` = đo được không gọi tool · `[...]`).
  **TRÊN DÂY** (mọi response HTTP trả client) — `tool_calls` LUÔN là MẢNG; ba-trạng-thái cho client
  đọc qua `ly_do_fallback`. Điểm chuẩn hoá là TẠI ROUTE trả envelope agent, có chú thích trỏ ADR này.
- **Việc ③ giữ nguyên** (đối chứng dương ở tầng biên — phần lớn đã có). Câu cuối của Hệ quả cũ
  ("sổ nợ ③ tự đóng vì không còn None") **RÚT theo** — None nội bộ còn, caveat `so_tool_call` của
  Lead vẫn hiệu lực.

---

## ADR-043 — Model KHÔNG còn ghim; hạ tầng TỰ XOAY trong một bể đã kiểm

**Trạng thái:** chấp nhận · 19/08/2026 · **ĐẢO `a3fb125`** (18/08 — "ghim `LLM_MODEL` theo NGÀY")
*(Lead soạn theo yêu cầu PO-agent; PO-agent land + sửa số theo mốc đo mới. Phương án route+UI đã
cân nhắc và bị bỏ — xem `DA-DONG-phuong-an-route-chon-model.md`.)*

### Bối cảnh
`a3fb125` ghim model vì một lý do **vẫn còn đúng**: alias trôi làm mọi phép đo A/B vô nghĩa — đổi
model là **đổi VẬT**, không phải đổi tham số. Nay PO thật đặt một yêu cầu khác hẳn, nguyên văn:
> *"Chúng ta tự đổi model ở dưới hạ tầng — đảm bảo không có lúc nào hết token — vì hiện tại đang là
> bản test thôi."*

Mục tiêu **không** phải cho khách so sánh model, mà là **dịch vụ không đứt vì cạn quota** trong giai
đoạn demo/test.

### Quyết định
1. **Bể model khai qua env** (`LLM_MODEL_POOL`). Code **không biết tên model nào**.
2. **Xoay tự động, im lặng, dưới hạ tầng.** Không route, không UI, không nhãn "trả lời bởi X".
   `authority-matrix` **KHÔNG đổi** — 33 route giữ nguyên, `CONTRACT_VERSION` giữ nguyên.
3. **Trigger CHỈ là lớp lỗi quota**, kèm ba ràng buộc: ưu tiên `status_code` khi nhà cung cấp có ·
   trần số lần xoay/lượt = `len(LLM_MODEL_POOL)` · nhà cung cấp **đổi câu chữ** ⟹ rơi về nhánh lỗi
   thường, **không xoay loạn**. 429 KHÔNG BAO GIỜ xoay (nghẽn thoáng qua ≠ hết token).
4. **Model đã cạn đánh dấu ở Redis kèm TTL** — TTL là **backoff**, KHÔNG phải dự đoán lúc quota hồi.
5. **`usage.jsonl` ghi model THẬT đã phục vụ** (không phải hằng số cấu hình), và ghi **mọi model đã
   thử** trong lượt — nhà cung cấp có thể tính cả lần thất bại.
6. 🔴 **AI KHÔNG được có tool đổi model.** `agent-tools.yaml` không đổi, **và đó là CÓ CHỦ ĐÍCH**:
   cho AI tự chọn model là cho nó chọn cái gì đánh giá chính nó — cùng họ **ràng buộc cứng số 2**
   (*AI không vượt cấp*). Khai ra để người sau không đọc "không đổi" thành "chưa ai nghĩ tới".
7. **Embedding KHÔNG xoay** — đổi embedding = đổi VẬT của kho RAG (phải nạp lại 378 chunk).
8. **Cổng nhập bể là điều kiện CHẶN.** Model chưa qua cổng **không được có tên trong
   `LLM_MODEL_POOL`**. Không ngoại lệ "tạm để đó".
9. **Bể chỉ nhận TÊN GHIM** (có mốc/ngày/phiên bản). Bí danh trôi ⟹ **từ chối lúc khởi động**.
   Chữ ký cổng nhập bể gắn vào tên ghim — nếu không, câu "chữ ký còn hiệu lực không" không có gì để
   bám. *(Loại 2/5 model PO thật gửi: `deepseek-v4-flash`, `deepseek-v4-pro` — không có mốc.)*

### Vì sao ⑧⑨ mạnh hơn hẳn khi xoay diễn ra IM LẶNG
Khi có UI, khách **thấy** model nào phục vụ mình và có thể từ chối. Xoay dưới hạ tầng thì khách
**không biết** và **không có cách từ chối**. Bộ an toàn của dự án **chưa từng hiệu chuẩn trên
deepseek**. ⟹ **Cổng nhập bể là thứ DUY NHẤT đứng giữa khách và một model chưa ai kiểm.**

### Hệ quả — phải khai, nếu không sẽ có người đọc số sai
🔴 **Mọi phép đo nghiêm túc phải GHIM model.** Lý do sinh ra `a3fb125` không mất đi — nó chỉ thôi áp
cho **đường phục vụ demo/test**. Eval · so sánh prompt · đo hồi quy chất lượng: **ghim `LLM_MODEL`,
tắt xoay**, nếu không mẫu là **dân số pha tạp** và không ai tách lại được.

**Phạm vi:** chế độ **DEMO/TEST**. Bản live có bể riêng, và bể live **không được phụ thuộc model
quota-free** (hết hạn 15/11/2026, thuộc key dev).

### 🔴 PHỤ LỤC BẮT BUỘC ĐỌC KÈM — xoay KHÔNG đạt được điều đặt hàng
Yêu cầu là *"đảm bảo không có lúc nào hết token"*. **Xoay HOÃN lúc cạn, không XOÁ nó.** Cả bể cạn
thì dịch vụ vẫn dừng — chỉ dừng muộn hơn. [ĐO 19/08, toàn bộ `usage.jsonl`, 163 lượt thật]:
```
trung bình 10.219 token/lượt · trung vị 13.210 · max 45.208 · 61/163 lượt = 0 token (đường nhẹ)
lượt CÓ tiêu (n=102): 16.330/lượt          50,7% input là CACHED
bể 3 model ghim × 1M = 3M   ⟹ sức chứa ~2,0–3,3 lượt/khách với 150 khách
```
⚠️ **Đây là DẢI, kèm hướng lệch — không phải một điểm.** 37% lượt 0-token là **tạo tác của cách ta
test** (sổ sinh từ các đợt verify, đầy câu chào); khách khiếu nại thật đi đường nặng nhiều hơn ⟹ số
thật nằm ở **nửa dưới** dải. ⚠️ **NIÊM:** con số *"~176 lượt · 1,2 lượt/khách"* (trình 19/08) đã
chết — mẫu số hẹp (chia bể cho 3 ca AUTH nặng nhất), bi quan gấp ~3.
⚠️ **Ẩn số chưa đo:** DashScope tính token **cached** vào quota free theo giá nào. Nếu quota đếm
không-cache thì sức chứa cao gần gấp đôi. Phép thử một bước đã giao PO thật (đối chiếu console với
`qwen3.7-max`: 944.920 raw vs 476.056 không-cache).

**Ba việc thực sự dịch được con số đó — không việc nào là xoay:**
1. **Giảm token/lượt** — Σ mô tả tool = **4.862 ký tự** gửi **mỗi lời gọi**, một lượt 3–5 lời gọi.
   Đòn bẩy lớn nhất, **chưa ai chạm**.
2. **Trần chi tiêu theo KHÁCH**, không chỉ theo ngày — trần hiện tại là **toàn cục**, một khách nói
   nhiều tiêu hết phần cả nhóm. Ngưỡng đặt theo **max 45.208**, không theo trung bình.
3. **Chốt số khách của đợt test theo con số này**, không theo kỳ vọng.

🔴 **Cầu dao khi cả bể cạn phải là một trải nghiệm ĐÃ THIẾT KẾ, không phải một lỗi** — ở sức chứa
này nó không phải trạng thái hiếm, nó là trạng thái **sẽ gặp**.

---

## ADR-044 — CSKH đọc được hội thoại bot↔khách của vé mình xử lý

**Trạng thái:** chấp nhận · 19/08/2026 · **PO thật duyệt trực tiếp** (§10 bước 4)
*(Lead soạn nháp; Bảo Mật soi BOLA + phụ thuộc chéo, `docs/security/2026-08-19-adr044-soi-bola-va-phu-thuoc-cheo.md`; PO-agent trình và land.)*

### Bối cảnh
PO thật 19/08: *"khi khách yêu cầu gặp người thật thì bên khung chat của CSKH cũng phải có lịch sử
chat giữa bot và khách hàng — như thế họ mới đủ thông tin để hỗ trợ."*
[ĐO] `flag_human_handoff()` chỉ lưu **một chuỗi `reason`** do AI tóm tắt; `TicketDetailClient.tsx`
chỉ hiện `investigation_logs`/`resolutions`/`tool_result`. Toàn bộ lời khách tự nói **không tới được
người sắp hỗ trợ họ** — khách phải kể lại từ đầu.

### 🔴 Phát hiện chặn thiết kế — tìm TRƯỚC khi viết contract
[ĐO] `main.py:645` `thread_id = f"{user_id}:{iat}"` — thread gắn theo **PHIÊN ĐĂNG NHẬP**, không phải
user. `Complaint` **không có** `thread_id`; `create_ticket` không nhận nó ở tầng nào.
⟹ **Không có đường xác định chắc chắn thread nào sinh ra vé nào.** Một khách đăng nhập 3 lần = 3
thread cho cùng `user_id`. Đoán theo mốc thời gian gần nhất là **heuristic đội lốt sự thật**, và
đoán sai = CSKH đọc **nhầm đoạn hội thoại** của cùng khách (có thể lộ một khiếu nại KHÁC, hoặc tư
vấn dựa trên ngữ cảnh sai).

### Quyết định
1. **`Complaint.thread_id`** (nullable), ghi tại thời điểm TẠO. Luồn qua **BỐN tầng**:
   `run_agent_turn` → `build_customer_tools` → tool `create_ticket` → `complaint_intake` → `INSERT`.
2. **Vé cũ (trước migration) trả `transcript: null` kèm lý do — TUYỆT ĐỐI KHÔNG đoán theo thời gian.**
   "Không biết" hiện ra là an toàn; "đoán" hiện ra là nguy hiểm vì **không ai phân biệt được nó với
   sự thật**.
3. **Route mới `GET /tickets/{ticket_id}/transcript`**, `roles: [cskh, supervisor]`.
   🔴 **GUARD CHÍNH (Bảo Mật sửa lời):** route **KHÔNG BAO GIỜ nhận `thread_id` làm tham số request**
   (query/body/header) dưới bất kỳ hình thức nào — **chỉ nhận `ticket_id`**, `thread_id` suy DUY NHẤT
   từ `ticket.complaint.thread_id` đọc từ DB. Ranh giới cần chặn: route không được âm thầm trở thành
   *"đọc thread_id trần"* trá hình dưới lốt *"đọc theo ticket"*.
   *"user_id khớp"* hạ xuống **404-handler phụ**, KHÔNG phải ranh giới thẩm quyền — vì mọi
   `cskh`/`supervisor` vốn đã đọc được mọi ticket, guard đó không chặn được gì thật.
4. **`Ticket.handoff_at`** (nullable), ghi lúc `flag_human_handoff()` chạy ([ĐO] hàm hiện chỉ set
   boolean + `updated_at`, **chưa** ghi mốc bàn giao). Đặt ở `Ticket` chứ không `Complaint`: một
   complaint có thể sinh nhiều ticket, bàn giao gắn với MỘT ticket.
5. Đọc qua LangGraph `checkpointer.get_tuple()` — **KHÔNG** parse thẳng bảng `checkpoint_*` (chi tiết
   triển khai của LangGraph, đổi giữa các phiên bản).
6. Rate limit tái dùng `@limiter.limit` có ở `/agent/chat`; audit tự động qua `_access_logger` —
   **không hạ tầng mới**.
7. 🔴 **`agent-tools.yaml` KHÔNG đổi, CÓ CHỦ ĐÍCH.** Cho AI một tool đọc transcript bàn giao là để nó
   tự đọc hồ sơ *"nó bị đá ra"* — cùng họ **ràng buộc cứng số 2** (AI không vượt cấp). Khai ra để
   người sau không đọc "không đổi" thành "chưa ai nghĩ tới".

### Trục bằng chứng — transcript TRÔI sau bàn giao
Đọc LIVE nghĩa là khách xin gặp người rồi **vẫn chat tiếp**, nên thứ CSKH đọc **khác** thứ đã gây ra
bàn giao. Trong khiếu nại tài chính, hội thoại tại thời điểm bàn giao là **bằng chứng**, không được
đổi sau lưng người đọc. **MVP:** vẫn đọc live, nhưng trả kèm `handoff_at` và **UI vẽ vạch phân cách**
*"— khách yêu cầu gặp người thật tại đây —"*. Trên vạch là thứ gây ra bàn giao; dưới vạch là thứ xảy
ra sau.

### PII — GIẢI XONG bằng phép đo, không phụ thuộc bản vá lỗi 2+3
[ĐO] đọc checkpoint thật qua `PostgresSaver.get_tuple()`: **checkpoint lưu bản ĐÃ SCRUB** (`graph.py:787`
scrub *trước khi* tạo `HumanMessage`). Route không cần scrub lại ⟹ hai việc chạy song song thật.
🔴 **Nghĩa vụ khai trên UI:** checkpoint ghi TRƯỚC bản vá D' giữ **nhãn che sai vĩnh viễn**
(`[PERSON_VN]`/`[LOCATION]` thay cho từ khách gõ thật — [ĐO] ~12% câu tiếng Việt đời thường bị bóp
méo, không riêng mã giao dịch). **KHÔNG vá ngược kho lịch sử — sửa bằng chứng là việc không được làm.**
UI phải hiện dòng khai để CSKH không tưởng khách gõ như vậy.

### Hệ quả
`authority-matrix.yaml` **2.0.0 → 2.1.0**, **33 → 34 route**. Migration Alembic + code đi SAU khi
contract land + baseline cập nhật + `CONTRACT_VERSION` sửa (§10 bước 5–7).

## ADR-045 — Kho checkpoint: mã hoá ở tầng **serde**, và ba câu chỉ PO chốt được

**Ngày:** 2026-08-20 · **Trạng thái:** 🟡 **CHỜ PO THẬT DUYỆT** — chưa code một dòng nào (§3)
**Nguồn:** đánh giá Bảo mật `bab739e` · soát xét độc lập Review · PO-agent tự đo lại toàn bộ

### Bối cảnh — [ĐO 20/08, đo trên ngăn `fin05` đang chạy, không suy từ schema]

**HAI bảng, không phải một.** Đánh giá gốc chỉ đếm bảng thứ nhất; Review tìm ra bảng thứ hai:
```
checkpoint_blobs    6.842 blob · 38 MB   · 3 channel (messages · __start__ · __pregel_tasks)
checkpoint_writes   7.015 dòng · 4.765 kB· 4 channel (messages 3.986 · branch:to:model 2.053
                                            · __pregel_tasks 893 · __error__ 83)
                    ↑ cột `blob bytea` RIÊNG, không phải cùng bảng
tỉ lệ mã hoá        0 / 13.857   (dò byte 'gAAAAA' = khuôn Fernet — dò TRÊN BYTE, không dò chuỗi escape)
nội dung người thật 121 dòng khớp byte 'ă' ngay trên channel `messages` của bảng thứ hai
cơ chế xoá          0 hit `retention|ttl|purge` — lưu VÔ THỜI HẠN
đà tăng             6.213 (18/08) → 6.842 (20/08) ≈ 315 blob/ngày  [nội suy 2 điểm, không phải đo liên tục]
```
🔴 **`__pregel_tasks` mang THAM SỐ TOOL, không qua `scrub_pii` nào** — 116 blob khớp đồng thời
`create_ticket` và `description_raw`. Đây là **bản sao thứ hai, không mã hoá, của đúng dữ liệu
ADR-032 vừa mã hoá xong** ở bảng `complaints`. Vá vũng nước xong thì vòi chảy lộ ra.

### 🔴 HAI mối đe doạ khác nhau — quyết định này chỉ đóng MỘT

| | đe doạ | ADR này đóng? |
|---|---|---|
| **NGOÀI** | ai đó chiếm được ổ đĩa / bản sao lưu Postgres | ✅ **có** — đó là mục đích |
| **TRONG** | một tài khoản `cskh` (hoặc phiên `cskh` bị chiếm) đọc hội thoại của khách **không thuộc ca mình** | ❌ **KHÔNG** |

[ĐO] `get_ticket_transcript` dùng `require_role("cskh","supervisor")` + `session.get(Ticket, ticket_id)`
— **không có kiểm tra vé-được-giao nào.** Chính chú thích trong ADR-044 đã khai điều này *("`user_id`
khớp KHÔNG phải ranh giới thẩm quyền ở route này")*, nên đây **không phải chỗ bỏ sót** — nhưng nó
tồn tại **độc lập** với việc VPS có lộ cổng hay không, và **mã hoá at-rest không chạm tới nó**: CSKH
đọc bản đã giải mã qua ứng dụng, đúng thiết kế. Ghi ra để không ai đọc "đã mã hoá" thành "đã an tâm".

**Đe doạ TRONG không phải lời cảnh báo trừu tượng — nó có một mục còn mở, cụ thể, đo được:**
```
[ĐO 20/08] route transcript nay giới hạn  5/minute
           (đã siết từ 20/minute — phát hiện Bảo mật, ĐÃ VÁ trong đợt ADR-044)
           5/phút = 300 vé/giờ = 2.400 vé mỗi ca 8 tiếng
```
🔴 Ngưỡng đã siết 4 lần, nhưng **lớp lo ngại chưa đóng**: 2.400 vé một ca vẫn **lớn hơn nhiều lần**
số vé một người thật đọc nổi. Ngưỡng này hiệu chuẩn cho **tốc độ gõ**, không cho **tốc độ đọc** — nó
chặn được kịch bản tự động thô, không chặn được một tài khoản `cskh` bị chiếm rút dữ liệu đều tay.
⟹ Việc còn mở, **không thuộc ADR này**: hiệu chuẩn ngưỡng theo *nhu cầu công việc thật* (bao nhiêu vé
một CSKH mở trong một ca?), hoặc thêm ranh giới vé-được-giao. Cần số nghiệp vụ từ PO thật, cùng lý do
mục (B) retention cần.

### Quyết định — bọc `serde`, KHÔNG đụng cột, KHÔNG vá theo từng channel

[ĐO trên `langgraph-checkpoint-postgres==3.1.2` **đang chạy**, không phải tài liệu]:
```
PostgresSaver.__init__     có tham số `serde`               → True
SerializerProtocol         đúng 2 method: dumps_typed / loads_typed
BasePostgresSaver._dump_writes  dùng `self.serde`           → True
```
⟹ Một `SerializerProtocol` bọc ngoài serde gốc (lấy `(type, bytes)` rồi Fernet hoá phần `bytes`,
đảo chiều lúc load) **phủ CẢ HAI bảng bằng MỘT điểm sửa**, vì cả hai đều đi qua cùng `self.serde`.

Ba lý do bác các hướng khác:
1. **Không dùng `EncryptedText` như ADR-032** — schema `checkpoint_*` do LangGraph sở hữu, đổi cột là
   tự nhận nợ mỗi lần nâng phiên bản (cùng lý lẽ ADR-041 đã dùng để bác "đọc thẳng bảng").
2. **Không vá theo từng channel** — `branch:to:model` và `__error__` là hai channel **chưa ai từng
   nhắc tới** cho tới hôm nay. Cách vá nào đòi liệt kê đủ channel sẽ hỏng ở channel thứ năm.
3. **Không che `HumanMessage`** — che là hỏng chính agent. Bảo vệ ở tầng lưu trữ, không ở tầng nội dung.

🔴 **Phạm vi nghiệm thu BẮT BUỘC nêu tên CẢ HAI bảng.** Nếu ADR chỉ nói "kho checkpoint", người
nghiệm thu sau này sẽ kiểm đúng bảng mà đánh giá gốc đã đo rồi báo "sạch", trong khi `checkpoint_writes`
**chưa từng bị hỏi**. Nghiệm thu = dò khuôn Fernet **trên byte** ở cả `checkpoint_blobs` **và**
`checkpoint_writes`, cộng một ca đọc-lại chứng minh hội thoại cũ vẫn hiển thị được.

### BA CÂU CHỜ PO THẬT — không ai chốt thay được

**(A) 13.857 blob CŨ: mã hoá ngược hay chỉ bảo vệ dữ liệu mới từ nay?**
Backfill ở đây **rủi ro hơn** backfill `complaints` đã làm: ta không sở hữu định dạng tuần tự hoá, làm
hỏng thì mất **khả năng đọc lại hội thoại**, không chỉ mất bằng chứng. Đề xuất của tôi: **chỉ bảo vệ
từ nay**, và giải quyết kho cũ bằng (B) thay vì bằng backfill.

**(B) Giữ hội thoại khách bao lâu rồi xoá?** Hiện **không có gì xoá nó bao giờ**. Đây là nghĩa vụ
NĐ 13/2023 **độc lập** với mã hoá — mã hoá xong mà lưu vĩnh viễn thì vẫn thiếu. Bảo mật **từ chối tự
chốt số** vì cần SLA khiếu nại + nghĩa vụ lưu trữ ngành. Cùng lý do họ từ chối chốt ngưỡng rate-limit.

**(C) Làm trọn trước khi deploy, hay bước đệm rẻ trước?** Cửa sổ sửa rẻ đóng vào **ngày deploy**: sau
đó mọi thay đổi là migration trên dữ liệu đang phục vụ. Nhưng làm vội đúng chỗ nhạy cảm nhất cũng là
rủi ro thật. Bước đệm rẻ = chặn đà tăng vô hạn ngay bằng retention, hoàn thiện serde sau.

**(D) Câu Bảo mật hỏi mà tôi chưa trả lời được:** cấu hình VPS sắp deploy **có publish cổng Postgres
ra ngoài không**, và **VPS đặt ở đâu** (trong hay ngoài Việt Nam — quyết định nghĩa vụ chuyển dữ liệu
qua biên giới). [ĐO] `docker port fin05-postgres-1 → 127.0.0.1:5432` — nhưng đó là file **dev trong
repo**, không phải cấu hình VPS thật. Toàn bộ định hạng ở trên **đổi mức** nếu câu trả lời là CÓ.

### Hệ quả nếu duyệt
`contracts/` **không đổi** (không route mới, không tool mới, không đổi role) ⟹ không cần §10. Code là
việc của Coder, sau khi PO duyệt — **không phải bây giờ**.

## ADR-046 — Bộ sinh dữ liệu: `money_not_received` KHÔNG được buộc cứng một trạng thái

**Ngày:** 2026-08-20 · **Trạng thái:** 🟡 **CHỜ PO THẬT DUYỆT** — chưa sửa dòng nào (§3)
**Nguồn:** phiếu BA (D1) · Coder truy đúng đường sinh · PO-agent kiểm lại và **tự đính chính một lần**

### Bối cảnh — [ĐO]

```
scripts/gen_dataset.py:1534   build_background_complaints()   ← đường sinh complaints.jsonl
  eligible_status = { "wrong_recipient": {"success"},
                      "money_not_received": {"processing"},   ← TẬP MỘT PHẦN TỬ
                      ... }

[ĐO trên dữ liệu đã sinh] money_not_received: 90/90 = 100% processing
```
🔴 **Đây là buộc cứng, không phải phân phối.** Một tập hợp có đúng một phần tử thì không có
ngẫu nhiên nào xảy ra được — `money_not_received` **không thể** mang trạng thái nào khác.

⛔ **Tự đính chính (PO-agent):** tôi từng báo *"không phải buộc cứng, nó CÓ ĐIỀU KIỆN"*, trích
`gen_dataset.py:584`. **Sai phạm vi** — dòng 584 thuộc `build_matrix_cases()`, đường sinh
`eval/golden_set.jsonl`, **không ghi vào `complaints.jsonl`**. Tôi tìm thấy một dòng có điều kiện
rồi kết luận mà không kiểm nó có nằm trên đường đang xét hay không. Coder tìm ra đường đúng.

### 🔴 Quyết định — sửa thành PHÂN PHỐI CÓ ĐIỀU KIỆN, **KHÔNG** sinh độc lập

Phiếu BA đề nghị *"sinh trạng thái giao dịch ĐỘC LẬP với loại khiếu nại"*. **BÁC.**

Ngoài đời, khiếu nại *"chưa nhận được tiền"* **thật sự** tương quan mạnh với giao dịch đang treo —
đó là **nguyên nhân** sinh ra khiếu nại, không phải trùng hợp thống kê. Ép tương quan về 0 làm bộ
dữ liệu **kém thật hơn**, không thật hơn.

Bệnh không phải *"có tương quan"*. Bệnh là **tương quan tuyệt đối, không ngoại lệ** — trong khi
đời thật luôn có ca: **giao dịch báo `success` mà người nhận vẫn chưa thấy tiền.** Đó chính là
**ca khó nhất và đáng có nhất** trong một bộ dữ liệu kiểm thử — và hiện nó **không tồn tại**.

⟹ `money_not_received` nhận `{processing, success}` với `processing` chiếm đa số.

### 🔴 DỰ BÁO — công bố TRƯỚC khi chạy lại, theo quy trình PO thật đặt ra

Ghi ra đây để không ai (kể cả tôi) chọn lần chạy đẹp nhất:

```
M2 hiện tại                       101/600 = 16,8%
nếu 20% money_not_received → success:  83/600 = 13,8%
nếu 30% money_not_received → success:  74/600 = 12,3%
```

**Dự báo: con số M2 sẽ GIẢM, không tăng.** Vì thêm ca `success` là thêm vào nhóm *tiền đã rời*.

⚠️ **Ai đó thấy M2 TĂNG sau khi sửa ⟹ bản sửa SAI**, dừng lại, đừng nhận số. Và nếu số mới xấu
hơn cho câu chuyện muốn kể — **báo cáo nguyên trạng**. Đó là toàn bộ lý do dự báo được viết ra trước.

### Hệ quả
`contracts/` không đổi ⟹ không cần §10. Mọi số đo trên trục *"chưa mất tiền thật"* công bố trước
20/08 phải **niêm**, vì chúng đo bộ sinh chứ không đo khiếu nại.

## ADR-047 — Tiếp nhận TRƯỚC, bổ sung SAU: khách đòi mở khiếu nại thì mở ngay

**Ngày:** 2026-08-24 · **Trạng thái:** PO duyệt (lệnh *"tiếp tục triển khai thôi"*, 24/08)
**Bối cảnh:** PO hỏi *"theo luồng nghiệp vụ của một con người CSKH thật thì họ sẽ làm gì?"*
sau khi test A2 vế 2 đỏ **bốn vòng liên tiếp**. Tra nghiệp vụ thật →
`docs/nghiep-vu-tiep-nhan-truoc-bo-sung-sau.md`.

**Dữ kiện quyết định:** thời hạn xử lý tra soát/khiếu nại đếm **từ NGÀY TIẾP NHẬN**, không phải
từ ngày khách khai đủ thông tin (TT 15/2024/TT-NHNN). Tổ chức thanh toán **bắt buộc** tiếp nhận
qua tổng đài, rồi **mới** yêu cầu bổ sung hồ sơ theo mẫu.

**Quyết định:** khi khách **chủ động yêu cầu** mở khiếu nại (*"tạo đi"*, *"mở khiếu nại cho tôi"*),
agent **tạo vé NGAY**, không đặt điều kiện phải tra cứu xong trước. Vé ghi rõ phần chưa xác định
được. **Tạo vé KHÔNG kết thúc hội thoại** — agent tiếp tục hỏi các slot còn thiếu và cập nhật
vào vé đã có.

**Điều KHÔNG đổi:**
- Ràng buộc cứng 3 giữ nguyên: vé ghi *"chưa xác định được giao dịch"*, **không bịa** số/mã/trạng thái.
- A2 gốc giữ nguyên: agent **không tự ý** tạo vé khi khách mới chỉ hỏi — chỉ tạo khi khách **yêu cầu**
  hoặc **đồng ý** với đề nghị của agent.
- HITL giữ nguyên: mở vé ≠ quyết định. Không đồng gì được duyệt ở bước này.

**Thay thế:** điều kiện *"chỉ được tạo vé SAU KHI đã tra cứu ít nhất một lần"* thêm ở `2b197d0`
(24/08) — **bãi bỏ** với nhánh khách-chủ-động-yêu-cầu. Giữ với nhánh agent-tự-đề-nghị.

**Vì sao điều kiện cũ sai:** nó bảo vệ chất lượng vé bằng cách **trì hoãn mốc pháp lý bảo vệ
khách**. Với ca lừa đảo — tiền chạy theo phút — mỗi lượt hỏi thêm là một lượt chậm.

**Hệ quả kiểm thử:** test A2 vế 2 kỳ vọng **ĐÚNG** từ đầu; đỏ 4 vòng là bug sản phẩm thật.
Không sửa test.

## ADR-045b — Chốt bốn tham số vận hành cho ADR-045 (PO quyết 24/08)

**Ngày:** 2026-08-24 · **Trạng thái:** ✅ PO thật quyết trực tiếp

| tham số | chốt | ghi chú |
|---|---|---|
| Giữ lịch sử hội thoại | **90 ngày** rồi xoá | PO quyết |
| VPS đặt tại | **Việt Nam** | PO quyết |
| Vé/CSKH/ca | **20** | PO: *"cứ cho một con số trung bình ngành"* — xem nguồn |
| Kiến trúc máy | *chưa chốt* | **KHÔNG chặn ai** — DevOps xác định lúc dựng thật, không cần PO |

**Nguồn con số 20 vé/ca** — [ĐO 24/08, tra web]: Zendesk Benchmark 2025 đặt trung bình ngành ở
**17–25 vé/agent/ngày**, mức này **giữ nguyên từ 2022**. Ngành có ràng buộc quy định (y tế, tài
chính) nằm ở **đầu thấp** của dải do thời gian xử lý mỗi ca dài hơn. FIN-05 là khiếu nại giao dịch
có tra soát + HITL ⟹ chọn **20**, giữa dải, nghiêng nhẹ về phía thận trọng.
🔴 **NIÊM:** đây là số **trung bình ngành quốc tế**, KHÔNG phải số đo của một đội CSKH thật nào ở
Việt Nam. Dùng để **chỉnh hạn mức**, KHÔNG được trích ra ngoài như số liệu của dự án.

**Hệ quả của "VPS tại Việt Nam":** dữ liệu không rời biên giới ⟹ nhánh thủ tục NĐ 13/2023 cho
chuyển dữ liệu xuyên biên giới **không phát sinh**. Khớp với quyết định bỏ hồ sơ Đ.25 (PO, 18/08).

## ADR-048 — Tín hiệu FS-13: "có người hướng dẫn chuyển khoản"

**Ngày:** 2026-08-24 · **Trạng thái:** ✅ **PO DUYỆT 24/08** (*"gật"*) — chờ thi hành, thuộc Đợt 2
*(Đánh số 048 vì 047 đã dùng cho tiếp-nhận-trước. Các tài liệu cũ ghi "ADR-047 = FS-13" là số dự
kiến trước khi ghi, không phải ADR đã tồn tại.)*

**Bối cảnh:** chuyên gia CSKH (PO chuyển 24/08) xếp đây là **rủi ro nghiệp vụ lớn nhất** hiện tại:
ca **bị lừa đảo** đang bị hệ thống ép vào ô *"chuyển nhầm"*. Hai loại này cần xử lý khác hẳn —
chuyển nhầm thì tra soát và liên hệ người nhận; bị lừa thì phải cảnh báo, giữ dấu vết, và **không**
trấn an theo kiểu "sẽ lấy lại được".

**Quyết định:** thêm tín hiệu gian lận **FS-13 — "có người hướng dẫn chuyển khoản"** vào bộ tín
hiệu. Kích hoạt khi khách kể có người **hướng dẫn / yêu cầu / thúc giục** thực hiện giao dịch
(qua điện thoại, tin nhắn, mạng xã hội), kể cả khi khách tự tay bấm.

**Ràng buộc giữ nguyên (ràng buộc cứng 5):** gắn cờ FS-13 ≠ khoá ví. Hai hành động độc lập.
FS-13 **không** cho AI escalate — nó là tín hiệu ở tầng service, đúng ràng buộc cứng 2.

**🔧 ĐÍNH CHÍNH 24/08 (Lead, [ĐO]):** bản đầu ADR này (và brief PO-agent gửi Lead) ghi *"đặt ở
`fraud_policy.py`"* — **sai, gộp hai tầng làm một**. Đúng ra: **nhận diện** thuộc
`fraud_engine.py` + `fraud_signals.yaml` (tái dùng đường ống `utterance_text` mà FS-09 đã có);
`fraud_policy.py` chỉ **quyết escalate** từ danh sách tín hiệu đã tính xong.

**Quan hệ với FS-09 — KHÔNG trùng lặp, chủ ý chồng nhau:** FS-09 (`fraud_engine.py:143-165`) là
lưới **HẸP** bắt **TỪ KHOÁ** của 5 kịch bản lừa đảo đã biết (giả công an, việc nhẹ lương cao, đầu
tư ảo, chiếm tài khoản, giả CSKH). FS-13 là lưới **RỘNG** bắt **CẤU TRÚC**: bên-thứ-ba + kênh xa
lạ. Hai tín hiệu cùng bật trên nhiều ca là **đúng thiết kế**, không phải trùng cần dọn.

**Ranh giới bắt oan (Lead chốt nguyên tắc, không liệt kê từ khoá):** đòi **ĐỒNG THỜI** ① bên thứ
ba là nguồn chỉ dẫn **VÀ** ② kênh xa lạ (điện thoại/tin nhắn/MXH/người lạ).
*"Chồng tôi bảo chuyển"* trượt ② ⟹ không bật. *"Shop hướng dẫn chuyển khoản"* trượt ② ⟹ không bật.

**Cờ bật thì hành vi đổi thế nào — GIỮ lệ ADR-022:** model **không bao giờ** thấy mã tín hiệu
(`create_ticket` chỉ trả `should_escalate`/`escalation_target`). Cảnh báo *"đừng trấn an"* phải là
**một dòng TẤT ĐỊNH** chèn sau khi `create_ticket` trả về — **không** giao model tự diễn đạt dưới
một chỉ thị prompt. Không đặt cược an toàn vào việc model nghe lời.

**🟡 CÒN CHỜ PO THẬT — một câu:** FS-13 có **escalate** (đổi priority/target như FS-06, hiện là
tín hiệu DUY NHẤT làm việc đó) hay **chỉ ghi nhận**? Đây là quyết định đổi **tải hàng chờ
supervisor thật**, không phải kỹ thuật.

**Đụng contract ⟹ phải đi đủ §3** trước khi code: sửa contract → ADR (file này) → PO duyệt (xong)
→ `check_contracts.py --update` → cập nhật `CONTRACT_VERSION` → mới code.

## ADR-049 — Nhận diện TẤT ĐỊNH "khách yêu cầu tạo vé": đổi đòn bẩy, không đổi thêm chữ

**Ngày:** 2026-08-24 · **Trạng thái:** ✅ **PO THẬT DUYỆT 25/08** (*"Duyệt nhé"*)
*(Ghi bởi phiên PO — `docs/` là vùng ghi `po` theo §4. Coder **từ chối tự ghi** dòng này và
từ chối nhận uỷ quyền đổi vùng ghi qua relay; đúng, và đáng ghi nhận.)*
~~🟡 ĐỀ XUẤT — chờ PO thật duyệt. Chưa code dòng nào.~~ *(trạng thái tới 25/08)*

**Hệ quả mở khoá:** ⑩ *(bản tóm tắt 6 trường tất định trước `create_ticket` — đúng lượt 7
kịch bản chuyên gia CSKH)* và ⑪ *(cấu trúc ba vế · đổi góc nhìn PDPA · đọc lại 5 dữ kiện)*.
Cả hai vẫn phải **tự đo delta token** và vừa trần 293 — điều khoản T2, đợt "OTP trước token".

### Dữ kiện: sáu vòng, sáu cơ chế bị loại trừ, một hành vi không đổi

Test A2 vế 2 (*khách nói "Ừ tạo đi" ⟹ phải tạo vé*) đỏ **sáu lần liên tiếp** trong ngày 24/08.
Mỗi vòng loại trừ một cơ chế khác nhau, [ĐO] trên ngăn `fin05do`:

| vòng | cơ chế bị loại trừ | agent làm gì thay vì tạo vé |
|---|---|---|
| ① | tool bị cổng OTP chặn (harness test thiếu bước xác thực) | báo chưa xác thực |
| ② | thread test đứt (login lại mỗi lượt ⟹ hai hội thoại rời) | — |
| ③ | `multiple_matches` (bác bằng `tool_results`: thật ra `not_found`) | hỏi SĐT người nhận |
| ④ | luật chốt-luồng thiếu điều kiện | hỏi thời điểm |
| ⑤ | prompt hứa "bổ sung vào vé" (không có tool update) | hỏi mã giao dịch |
| ⑥ | **trần năng lực model** — chạy lại trên model mạnh nhất bể | hỏi phạm vi giao dịch |

**Vòng ⑥ là vòng quyết định.** Cùng ảnh, cùng kịch bản, chỉ đổi model
(`deepseek-v4-pro-0813`, xác nhận bằng `model_dau_luot()` phía server): **vẫn đỏ**.
🔴 *Niêm: "mạnh nhất" là suy từ quy ước đặt tên, không có benchmark nội bộ. Chiều ĐỎ vẫn cho
kết luận chắc — hai model khác nhau cùng không làm được.*

### Chẩn đoán

**Chúng ta dành cả đợt 1A dạy agent hỏi cho kỹ, rồi ngạc nhiên khi nó hỏi kỹ.**
R1–R5 + quy trình điều tra + luật cấm tạo vé khi chưa rõ loại — tất cả đẩy về **một** hướng:
*hỏi thêm*. Trên nền đó, *"Ừ tạo đi"* là ba chữ, một tín hiệu **yếu** cạnh sáu luật **mạnh**.

⟹ **Prompt là đòn bẩy sai cho hành vi này.** Bản vá thứ bảy là **luật thứ bảy cạnh tranh với sáu
luật cũ**, không có cơ sở nào tin nó thắng. Sáu vòng vừa rồi là bằng chứng thực nghiệm cho điều đó.

### Đề xuất

Nhận diện **tất định** câu khách yêu cầu tạo vé, ép nhánh ở tầng code — **đúng cơ chế cổng
`thu_slot` (1B) đã dựng hôm nay**, hạ tầng có sẵn (`triage.py`).

**Nguyên tắc bắt buộc kế thừa từ 1B — thà BỎ SÓT còn hơn BẮT OAN:**
- Bỏ sót ⟹ agent hỏi thêm một lượt. Phiền, không hỏng.
- Bắt oan ⟹ tạo vé khi khách **không** yêu cầu. **Hỏng thật** — vé rác vào hàng đợi CSKH, và
  vi phạm chính A2 gốc.
- Bài học đã trả giá hôm nay: từ đơn lẻ (`"sao"`, `"mất"`) khớp bừa; **cụm đủ dài** mới đứng được.

**Ba thứ KHÔNG đổi:** HITL tuyệt đối (mở vé ≠ quyết định) · ràng buộc cứng 3 (vé ghi rõ phần chưa
xác định, không bịa) · A2 gốc (agent **không tự ý** tạo vé khi khách mới chỉ hỏi).

### Câu PO cần quyết

Đây là **đổi kiến trúc quyết định**: chuyển một quyết định nghiệp vụ từ **model** sang **luật cứng**.
Được lợi tính đoán trước được; mất đi khả năng model xử ca lạ mà luật không lường.

---

## ADR-051 — `create_ticket` HAI THÌ: tóm tắt 6 trường trước, tạo vé sau

**Ngày:** 2026-08-25 · **Trạng thái:** ✅ **PO THẬT DUYỆT 25/08** (nguyên văn *"2 câu đầu làm nhé"*, ghi trong `docs/giao-viec/CHECKLIST-dot-otp-truoc-token.md` mốc điểm danh #24 `a241955`).
*(Toàn văn dự thảo + đánh đối kháng của Review giữ ở `docs/nhat-ky/2026-08-25-ADR-051-du-thao-cho-PO-duyet.md` — KHÔNG chép lại ở đây để `DECISIONS.md` không phình; mục này ghi QUYẾT ĐỊNH và HỆ QUẢ.)*

### Quyết định
`create_ticket` tách làm HAI THÌ qua tham số mới `xac_nhan: bool = false`.
```
thì 1  xac_nhan=false  → KHÔNG tạo gì. Trả bản tóm tắt 6 trường DỰNG TRONG MÃ từ
                          chính tham số model vừa truyền. Phát thẳng cho khách.
thì 2  xac_nhan=true   → tạo thật, CHỈ sau khi khách gật.
```
Tóm tắt do MÃ dựng ⟹ tất định, không bịa được, không trôi theo prompt. **Siết HITL
chặt hơn hiện tại: không gì thành hình trước khi khách gật.**

### Sáu ràng buộc — thiếu bất kỳ cái nào là hỏng
**1–4** ghi tại `655a112` (Coder): ① `test_invariants` chỉ so TÊN tool, KHÔNG so
CHỮ KÝ ⟹ §3 là lớp bảo vệ DUY NHẤT · ② thì 1 KHÔNG được đặt `ticket_id` (ba móc ⑧/⑨/
investigation-logs đều khoá theo nó) · ③ cổng OTP cho thì 1 là câu BẢO MẬT, không tự
quyết · ④ ⑨ chỉ được bắn ở thì 2, thiếu điều kiện `xac_nhan is True` thì câu sàng lọc
lừa đảo hỏi HAI lần.

**5** `xac_nhan=true` CHỈ nhận khi có tín hiệu *"đã gửi tóm tắt khớp đúng 6 trường
này"* ở lượt TRƯỚC (khuôn `thread_signals`, **băm 6 trường** làm giá trị, tự xoá sau
khi dùng). 🔴 Thiếu: model gọi thẳng `xac_nhan=true` ngay lượt đầu ⟹ **đi vòng qua
toàn bộ giá trị HITL**. `TurnGuard` KHÔNG cứu được — [ĐO] nó tạo mới **mỗi lượt**, mà
hai thì là **hai lượt chat**; nó không có khái niệm *"lượt trước"*. Cùng chốt này đóng
luôn nhánh *"khách gật hai lần"*.

**6** `create_ticket` đổi return type **`dict` → CHUỖI ĐÃ ĐỊNH DẠNG**, cho **cả hai
thì**. 🔴 Thiếu: `return_direct` phát **thẳng** giá trị trả về làm câu trả lời ⟹
**khách nhận JSON thô**. Hỏng ở PHÍA KHÁCH HÀNG, không ở test.

### Hệ quả
`contracts/agent-tools.yaml` **2.1.2 → 2.2.0** (thêm input `xac_nhan`, đổi kiểu
output). `CONTRACT_VERSION` cập nhật, commit KÈM file baseline.
🔴 **Chưa code một dòng nào** — bước 7 của §3 đi sau commit này.

🔴 **Dữ kiện dùng được cho mọi thiết kế sau, không riêng ADR này** (đo sổ sống):
giá thật **một lời gọi tool ≈ 10.400 token** (0 tool → 10.381 · 1 tool → 20.811 ·
3 tool → 41.444, tuyến tính khít). Tiền nằm ở **vòng gửi lại ngữ cảnh**, KHÔNG ở lược
đồ tool. ⟹ Hai thì = thêm MỘT vòng ⟹ **≈ +10.400 token mỗi ca tạo vé**.
`return_direct=True` CÓ hỗ trợ (langchain 1.3.15, `create_agent` tự dựng `exit_node`)
⟹ thì 1 dừng được ngay sau tool, không cần đổi kiến trúc agent.

---

## ADR-052 — Bổ sung `bieu_thuc` cho BR-11 trong contract: đóng lỗ đối xứng

**Ngày:** 2026-08-26 · **Trạng thái:** ⏳ **DỰ THẢO — CHỜ PO THẬT DUYỆT** (§3 bắt buộc: sửa
`contracts/` phải qua ADR + PO gật, TRƯỚC khi code).

### Dữ kiện — đo, không suy
```
[ĐO 26/08] grep "bieu_thuc:" contracts/resolution-state-machine.yaml → ĐÚNG 2 chỗ
     dòng  65   BR-10  ck_resolutions_approved_requires_approver_br10   ✅ CÓ
     dòng 101   BR-12  ck_resolutions_maker_checker_br12                ✅ CÓ
     BR-11                                                              🔴 KHÔNG CÓ
                (mục `invariants:` chỉ ghi `mo_ta`/`nguon` cho INV-14)
```
**Ba luật cùng lớp, cùng canh ràng buộc cứng #1 (HITL). Hai cái có nguồn để so, một cái không.**

### Vì sao đây là lỗ, không phải chuyện hình thức
`tests/test_invariants.py` moi `CheckConstraint` từ app đang chạy rồi so với `contracts/`.
Không có `bieu_thuc` trong contract ⟹ cổng canh BR-11 **không còn gì để so** ⟹ buộc phải
**chép cứng** biểu thức vào chính tệp test.

🔴 Chép cứng làm cổng **lệch ÂM THẦM**: ngày ai đó sửa ràng buộc trong `models.py`, test vẫn
xanh với chuỗi cũ — **và không ai biết contract, code, test đang nói ba chuyện khác nhau.**
Đúng hình dạng lỗi QA/QC vừa tìm ra hôm nay: BR-10/BR-11 kiểm **substring**, đổi `AND` → `OR`
*(duyệt hoàn tiền chỉ cần MỘT trong hai cột thay vì CẢ HAI)* mà test **vẫn xanh** — đã chứng
minh bằng **đột biến thật** trên worktree, không phải đọc code *(`e804529`)*.

### Quyết định đề xuất
Thêm `bieu_thuc` cho BR-11 vào `contracts/resolution-state-machine.yaml`, **cùng khuôn BR-10
và BR-12** — lấy nguyên văn từ `CheckConstraint` đang chạy, chuẩn hoá y cách hai cái kia.

Rồi chuyển `INV-14` từ **chép cứng** sang **đọc động từ contract**, đúng khuôn `INV-15` đã dùng
cho BR-12 *(hạ tầng `yaml.safe_load` đã có sẵn tại `tests/test_invariants.py:66`)*.

### Hệ quả
```
· ba luật BR-10/11/12 cùng một cơ chế — không còn ngoại lệ phải nhớ
· sửa ràng buộc mà quên contract  ⟹ ĐỎ NGAY, thay vì xanh im lặng
· xoá một dòng chép cứng khỏi tệp test — chép cứng là nợ, không phải giải pháp
```

### Vế bất lợi — khai ra, không giấu
Đổi contract kéo theo **bốn bước bắt buộc của §3**: `check_contracts.py --update` · cập nhật
`CONTRACT_VERSION` · commit **kèm tệp baseline** *(quên là local xanh / CI đỏ)* · và mọi phiên
đang mở phải đọc lại. **Không phải sửa một dòng YAML.**

⚠️ Và biểu thức lấy **từ `CheckConstraint` đang chạy** — tức ta đang **niêm hiện trạng làm
chuẩn**. Nếu hiện trạng ĐANG SAI thì ADR này **đóng băng cái sai**. 🔴 **PO/Review cần xác nhận
BR-11 hiện tại đúng nghiệp vụ TRƯỚC khi niêm** — đây là câu hỏi nghiệp vụ, không phải kỹ thuật.

### Trạng thái tạm cho tới khi duyệt
`INV-14` **chép cứng CÓ NIÊM** *(`e804529`)* — docstring và thông điệp lỗi đều ghi rõ *"TẠM,
chuyển đọc động ngay khi ADR-052 bổ sung `bieu_thuc` BR-11"*. **Cổng vẫn canh được** *(đột biến
`AND`→`OR` làm nó đỏ đúng)*, chỉ là canh bằng một bản sao thay vì bằng nguồn.

## ADR-055 — Tách kiểm THU HỒI TOKEN khỏi kiểm ĐỘ TƯƠI OTP

**Ngày:** 2026-08-27 · **Trạng thái:** 🟡 CƠ CHẾ đang làm (Lead giao Coder, Review soát) ·
**PHẠM VI gắn route nào: CHỜ PO** — hai thứ đó cố ý tách, xem §Hệ quả.

### Bối cảnh — nguyên tắc ĐÃ ĐÚNG, đã được viết ra, có lý do kỹ thuật
`src/auth.py`, ngay trên chỗ gọi, tự khai đây là **quyết định có chủ đích**:
> *"access token đã rất ngắn hạn (15 phút), thêm 1 lần GET Redis vào MỌI request sẽ biến Redis
> thành single point of failure cho cả hệ thống trong khi lợi ích biên rất nhỏ; **route CHẠM DỮ
> LIỆU / TÀI CHÍNH thật xứng đáng trả giá đó, route đọc thường thì không.**"*

**Nguyên tắc đó đúng, ADR này KHÔNG đụng tới nó.**

### 🔴 Vấn đề — nguyên tắc đúng, CƠ CHẾ không diễn đạt được nó
`is_access_token_revoked()` gọi ở **đúng ba chỗ trong toàn `src/`**, và một trong ba nằm **bên
trong** một phép kiểm khác:
```
auth.py:345    ← BÊN TRONG require_otp_verified
main.py:992    ← /approve      (tường minh)
main.py:1154   ← /reject       (tường minh)
```
⟹ Một route **chỉ được kiểm thu hồi nếu nó CŨNG cần OTP tươi**. Hai câu hỏi độc lập về bản chất
bị buộc chung:
```
"phiên này còn hiệu lực không?"      → DANH TÍNH, áp cho mọi vai
"khách vừa xác thực gần đây chưa?"   → ĐỘ TƯƠI, chỉ áp cho customer
```

### 🔴 Bằng chứng đắt nhất: một quyết định ĐÚNG kéo theo một quyết định KHÔNG AI RA
`lookup_transaction` và `get_customer_history` **cố ý** không gắn `require_otp_verified`
(`main.py:563`, `:592`). Lý do ghi rõ và **hoàn toàn chính đáng — VỀ ĐỘ TƯƠI OTP**:
> *"khách hàng dùng gián tiếp qua rail 'Giao dịch gần đây' NGAY KHI vào trang, trước khi có cơ
> hội xác thực"*

Lý do đó **không nói gì về thu hồi token**. Nhưng vì hai phép kiểm dính nhau, **gỡ cái này là gỡ
luôn cái kia.** Người viết quyết định *"không bắt khách xác thực lại trước khi xem giao dịch gần
đây"* — hợp lý — và **vô tình cũng quyết định** *"token đã thu hồi vẫn đọc được lịch sử giao dịch
của khách"*, thứ họ **chưa bao giờ được hỏi.**

⟹ **Không ai quyết sai. Không ai quên.** Đó là hình dạng của bệnh này.

### Số đo — ĐÃ SỬA HAI LẦN, đây là số cuối
```
[ĐO 27/08] Depends(require_otp_verified) trong main.py  →  ĐÚNG MỘT chỗ (:602 = /tools/create_ticket)
[ĐO 27/08] is_access_token_revoked trong customer_tools.py (đường agent) → 0 lần
           (đường agent CÓ _otp_fresh — nhưng đó là ĐỘ TƯƠI, không phải THU HỒI)
⟹ TOÀN HỆ có BA route được kiểm thu hồi: create_ticket · approve · reject   (trên 23 route ghi)
⟹ chỉ MỘT route (create_ticket) được bảo vệ NGẦM qua require_otp_verified
```
⚠️ **NIÊM hai con số SAI đã lưu hành trong ngày, để người sau không đào lại:**
*"4 route có kiểm, gồm `lookup_transaction`/`get_customer_history`"* — **SAI**, hai route đó
không có ở cả hai đường. *"3 route mất bảo vệ nếu làm sai chiều"* — **SAI**, chỉ **một**.
📌 Cả hai sai vì **đếm bằng `grep` rồi đọc kết quả như bằng chứng về hành vi** — bệnh đã vấp bốn
lần trong ngày 27/08. **Bán phát hiện bằng CƠ CHẾ, đừng bán bằng SỐ ĐẾM.**

### Quyết định
Thêm **một FastAPI dependency ĐỘC LẬP** (`require_token_chua_thu_hoi`) chỉ làm một việc: gọi
`is_access_token_revoked`. Route cần bảo vệ **chỉ gắn thêm** dependency mới, **không** phải đòi
OTP tươi kèm theo.

🔴 **BÁC BỎ đường "rút phép kiểm ra khỏi `require_otp_verified` rồi gắn lại thủ công."**
`create_ticket` **được bảo vệ hoàn toàn NGẦM** — nó không tự gọi `is_access_token_revoked`. Rút
ra là **mất bảo vệ IM LẶNG: không test nào đỏ**, và chỉ sai khi có token bị thu hồi thật — ca
hiếm, không nằm trong suite thường trực. **CHỈ THÊM, KHÔNG RÚT** loại bỏ hẳn rủi ro đó.
*(Coder tìm ra vế này trước khi PO kịp duyệt; lời duyệt đầu của PO-agent dùng chữ "tách" — đọc
được theo đúng hướng nguy hiểm. Ràng buộc nằm CẠNH câu lệnh thì rụng trên đường đi.)*

### Hệ quả — và một ranh giới CỐ Ý
`src/auth.py` thêm một dependency. **Không đổi hành vi route nào đang chạy.**

🔴 **ADR này quyết CƠ CHẾ, KHÔNG quyết PHẠM VI.** Route nào được gắn là một quyết định riêng,
thuộc PO: *"route nào xứng đáng trả giá một lượt đọc Redis"* — đúng câu mà nguyên tắc gốc đặt ra.
**Dựng chỗ để gắn là việc kỹ thuật; quyết gắn vào đâu là chính sách.** Trộn hai thứ vào một ADR
là để một quyết định chính sách đi lọt dưới danh nghĩa một thay đổi kỹ thuật.

**Đề xuất bậc 1 chờ PO** *(không đổi gì người dùng thấy)*: `propose_resolution` ·
`escalate_ticket` · `request-approval-otp`.

---

## ADR-056 — Cổng ÉP TRA TRƯỚC (CTC1): chuyển một quy tắc từ prompt sang mã

**Ngày:** 31/08/2026 · **PO duyệt:** có (*"gật nha"*, sau khi được trình dữ liệu) · **Trạng thái:** đang triển khai

### Vấn đề — đo được, không phải cảm giác

Trong 180 ca golden+heldout, **29 ca agent TỰ CHỌN không gọi một công cụ tra cứu nào** ở tin nhắn
khiếu nại đầu tiên (chỉ 1 ca nữa do bộ lọc chặn). Nó hỏi khách thêm thông tin thay vì tự tra.

Đây là **một nguyên nhân gộp bốn triệu chứng** từng bị coi là bốn vấn đề riêng: "hứa suông" (nói sẽ
kiểm tra rồi không tra) · không mở hồ sơ cho khách chính đáng · ca lừa đảo bị bỏ bước tra rộng ·
trích dẫn mã giao dịch kém (54,9%). Dữ liệu **có thật** (52/52 mã tồn tại trong kho), số tiền khách
nói **khớp tuyệt đối** (33/33). Không phải công cụ tìm hụt — **lời gọi chưa bao giờ xảy ra**.

### 🔴 Vì sao KHÔNG sửa bằng prompt — hướng này ĐÃ CHẾT, đừng đề xuất lại

`prompt.py` **đã dặn đúng điều đó BA LẦN**, in hoa, kèm ví dụ phản diện đúng y hành vi sai
(dòng 15 · 18 · 41: *"GỌI TOOL NGAY LẬP TỨC… KHÔNG trả lời khách trước để hỏi thêm. Bạn có khả năng
tự tra cứu, đừng đẩy việc đó sang cho khách khi chưa thử."*). Mô hình vẫn sai 29/180.

Đo prompt: **20.429 ký tự · 114 dòng** · `KHÔNG` 34 lần · `PHẢI` 16 · `TUYỆT ĐỐI` 13 · `BẮT BUỘC` 3.
**Khi mọi thứ đều TUYỆT ĐỐI thì không gì còn tuyệt đối.**

**Tiền lệ nội bộ chứng minh cách đúng:** Ràng buộc #3 dặn trong prompt thì mô hình vẫn định bịa,
nhưng `_CHUA_TAO_DUOC_VE` đối chiếu CSDL thật và **chặn 15/15**, không sót.
> **Dặn thì tuân ~84%. Ép trong mã thì 100%.**

### Quyết định

Tin nhắn **ĐẦU** của một luồng khiếu nại **+** lượt trả lời **không có lời gọi công cụ nào**
⟹ **chặn**, thay bằng câu tất định dựng thẳng từ kết quả `get_customer_history` thật.

🔴 **Điều kiện CHỈ hai vế — cố ý.** Bản đầu của PO đòi thêm "khách đã nêu số tiền / tên / thời
gian", chép từ cách diễn đạt của prompt. **Đo lại thì 12/29 ca không có chi tiết nào** (dạng *"trừ
trùng 2 lần rồi"*, *"lịch sử hiện 2 dòng giống hệt nhau"*) ⟹ bỏ sót 41%.
`get_customer_history` có `amount: int | None = None` — **chạy được chỉ với `user_id`**. Nên
**không bao giờ tồn tại lý do chính đáng để trả lời tin khiếu nại đầu tiên mà chưa nhìn lịch sử.**

⟹ **Bài học chung: chuyển một quy tắc từ prompt sang mã KHÔNG phải chép lại câu chữ.** Prompt viết
cho mô hình đọc nên liệt kê **ví dụ gợi ý**; mã cần điều kiện **đúng và đủ**. Chép nguyên văn là
mang theo cả chỗ lỏng lẻo — mà chính chỗ lỏng đó là lý do prompt không hiệu lực ngay từ đầu.

### Ranh giới — bốn ràng buộc, không được nới

1. **Ưu tiên KHÔNG chặn khi không chắc.** Thà bỏ sót vài ca còn hơn phá ca đang chạy tốt.
2. **PHẢI ghi lại mỗi lần nổ, vào KẾT QUẢ ĐO** chứ không chỉ vào log — bài học 5 lớp lọc O1-O5 cùng
   thay một chuỗi, lớp nào bắn chỉ vào log ⟹ 19/22 ca không truy ngược được.
3. 🔴 **CHỈ ép GỌI CÔNG CỤ TRA. TUYỆT ĐỐI không đẩy nhanh `create_ticket`** — chạm ADR-051 hai thì
   và Ràng buộc cứng #1. Nâng một chỉ số mà phá một ràng buộc cứng là lỗ nặng hơn thứ đang sửa.
4. `tests/test_invariants.py` **23/23 xanh**, chạy thật, dán kết quả.

### Hệ quả

🔴 **Sửa `src/` ⟹ băm mã ĐỔI khỏi `9c17c5684c9a`.** Từ đó có **HAI bản mã cùng có kết quả đo** —
mọi báo cáo phải khai băm nào. **246 ca ngày 31/08 vĩnh viễn thuộc `9c17c5684c9a`.**

Đo lại theo thứ tự, đỏ cổng nào **dừng** cổng đó: ① cổng có nổ ≥80% nhóm đích · ② ≥80% nhóm đích
giờ có lời gọi công cụ · ③ **nhóm chứng 46 ca không tụt ca nào** · ④ điểm số **ghi lại, KHÔNG dùng
làm cổng** (n=29, sai số ~7 điểm — đo điểm ở cỡ đó là đo nhiễu).
Rồi golden 120, rồi **đối kháng 66 kiểm hồi quy an toàn — không được bỏ**.

*(Câu tất định phải mở đầu bằng "Mình hiểu…" theo luật giọng văn `prompt.py:21` — PO bắt được lúc
soát diff, không có phép kiểm tự động nào bắt luật này.)*

### 🔴 CẢNH BÁO BỔ SUNG ADR-056 — 01/09/2026: TIỀN ĐỀ ĐANG BỊ NGHI NGỜ

**Đo được sau khi ADR-056 đã viết và cổng đã commit (`f6045f9`):**

| ca | baseline 31/08 | chạy lại 01/09 | băm mã |
|---|---|---|---|
| `CASE-170` | **0 công cụ** · Blocker | 1 công cụ · Blocker | `9c17c5684c9a` — **giống hệt** |
| `CASE-051` | **0 công cụ** · Blocker | 2 công cụ · Blocker | `9c17c5684c9a` — **giống hệt** |
| `CASE-129` | **0 công cụ** · Blocker | 3 công cụ · **PASS** | `9c17c5684c9a` — **giống hệt** |

**Cùng bản mã, cùng ca, cùng model, KHÔNG bản vá nào ở giữa. Chỉ là chạy lại.**

⟹ Con số **"29/180 ca agent TỰ CHỌN không gọi công cụ"** — tiền đề của toàn bộ ADR này — **có thể
phần lớn là NHIỄU GIỮA CÁC LƯỢT CHẠY**, không phải tính chất ổn định của sản phẩm.

**Cổng CTC1 KHÔNG nổ trong phép thử 3 ca** (`loc_dau_ra_theo_luot` rỗng, câu trả lời là văn model
tự viết chứ không phải mẫu tất định) — nhưng agent **vẫn** tra cứu đàng hoàng. Tức cải thiện quan
sát được ở lượt đo **không đến từ cổng**.

🔴 **RANH GIỚI — đừng nói quá theo chiều ngược lại:** 3 ca là quá ít để định lượng nhiễu. Điểm
TỔNG HỢP trên 120 ca ổn định hơn nhiều (trung bình triệt tiêu bớt nhiễu), nên **26,7% và độ lệch
3,4 điểm golden↔heldout vẫn dùng được**. Thứ không đứng vững là **kết luận hành vi ở mức TỪNG CA
rút ra từ MỘT lượt chạy**.

**Lỗ phương pháp thật, cả đội cùng đi qua:** đo 246 ca · viết báo cáo · dựng ADR · viết cổng · tốn
12 triệu token — mà **chưa từng chạy cùng một thứ hai lần**. Suốt quá trình, mọi khác biệt giữa hai
lượt đều được mặc định là *do thay đổi*.

**KHÔNG lùi cổng CTC1** — nó không gây hại đã chứng minh (đối chứng: ảnh không-cổng chết y hệt khi
thiếu bộ nhớ), và ràng buộc "ưu tiên KHÔNG chặn khi không chắc" vẫn giữ. Nhưng **KHÔNG xây tiếp**
lên tiền đề này cho tới khi có phép đo nhiễu.

**Phép đo còn thiếu:** chạy 75 ca trên **cùng bản mã cũ** `9c17c5684c9a`, cùng điều kiện, để đo
dao động tự nhiên. Chờ PO duyệt (~2,7tr token). Đây là **điều kiện để mọi so sánh trước/sau của dự
án có nghĩa**, không phải một phép đo tuỳ chọn.

### ✅ KẾT LUẬN ADR-056 — 01/09/2026, sau khi ĐO ĐƯỢC NHIỄU

Chạy **75 ca** trên **cùng bản mã cũ** `9c17c5684c9a` (không cổng), cùng model, cùng đêm — để tách
**nhiễu chạy lại** khỏi **tác dụng cổng**. Ba cột cho cùng 75 ca:

| | nhóm CHỨNG (46 ca) | nhóm ĐÍCH (29 ca) |
|---|---|---|
| **Pass** baseline 31/08 | 46 *(theo định nghĩa chọn nhóm)* | 0 *(theo định nghĩa)* |
| **Pass** chạy lại, mã cũ | 27 | 3 |
| **Pass** có cổng | **27** | 6 |
| **Có gọi công cụ** chạy lại | 42 | 22 |
| **Có gọi công cụ** có cổng | 45 | **29** |

**① CỔNG KHÔNG GÂY HỒI QUY — minh oan tuyệt đối.** Nhóm chứng: chạy-lại 27 Pass · có-cổng 27 Pass.
**BẰNG NHAU.** Cổng ③ từng báo *"19/46 ca tụt"* ⟹ **toàn bộ là nhiễu**, không phải cổng.

**② CỔNG CÓ TÁC DỤNG THẬT, đo được:** nhóm đích 22/29 → **29/29** có gọi công cụ. Đưa tới tuyệt đối.

**③ 🔴 TIỀN ĐỀ GỐC ĐÃ ĐỔ.** Nhóm đích được chọn vì **0/29 gọi công cụ**. Chạy lại **cùng mã**:
**22/29 CÓ gọi.** ⟹ **76% số ca ta gọi là "agent TỰ CHỌN không tra cứu" thực ra là một lần chụp ảnh
vào lúc nó không tra.** Vấn đề thật nhỏ hơn nhiều so với con số 29/180 đã dựng nên ADR này.

**④ Điểm số KHÔNG lên:** nhóm đích 3 → 6 Pass (n=29, trong nhiễu). **Tra cứu nhiều hơn không tự
động thành trả lời đúng hơn.**

### ⟹ LÝ DO GIỮ CỔNG PHẢI VIẾT LẠI

**KHÔNG phải** "sửa một lỗi lớn ở 29/180 ca". **MÀ LÀ**: biến một hành vi **76% tuỳ lượt** thành
**100% tất định** ở bước quan trọng nhất — lần chạm đầu tiên với khách đang mất tiền. Với sản phẩm
tài chính, **bỏ tính ngẫu nhiên** ở bước đó tự nó là giá trị, kể cả khi điểm không nhích.
**Giữ cổng.** Không lùi. Nhưng đừng ai trích ADR này như bằng chứng "đã sửa một lỗ lớn".

### 🔴 CẢNH BÁO THỐNG KÊ — chỗ PO-agent suýt đọc sai, ghi lại để phiên sau không lặp

Thoạt nhìn "baseline 46 Pass → chạy lại 30 Pass trên cùng mã" trông như bằng chứng **điểm tổng
không ổn định**. **SAI.** Hai nhóm được chọn **DỰA TRÊN chính kết quả lượt đầu** (chứng = đã Pass,
đích = 0 công cụ) ⟹ lượt sau **bắt buộc** kém đi kể cả khi không có nhiễu nào. Đó là **hồi quy về
trung bình**, không phải bằng chứng độ ổn định.
⟹ **Ta vẫn CHƯA biết điểm tổng 120 ca dao động bao nhiêu.** Phép đo này KHÔNG trả lời được — mẫu
thiên lệch. Không được nói nó ổn định, cũng không được nói nó không ổn định.
⟹ Muốn biết: chạy lại **TOÀN BỘ** golden 120 trên cùng mã, không chọn lọc. Chưa làm.

---

## ADR-057 — CHUYỂN NGƯỜI SỚM cho tầng đắt: quy tắc TẤT ĐỊNH ở tầng service

**Ngày:** 01/09/2026 · **PO duyệt:** có (*"A bạn nhé"*, sau khi được trình 3 phương án kèm dữ liệu)
· **Trạng thái:** chờ triển khai — 🔴 **KHÔNG code trước khi đọc hết mục "Ranh giới" dưới**

### Vấn đề — đo được, và trùng khít với một ca thật ngoài ngành

Tỉ lệ đạt theo loại khiếu nại, 180 ca (lượt đo 31/08, bản mã `9c17c5684c9a`):

| loại | đạt |
|---|---|
| **`refund`** | **6/43 = 14,0%** |
| **`wrong_recipient`** | **7/41 = 17,1%** |
| `double_charge` | 8/30 = 26,7% |
| `money_not_received` | 24/63 = 38,1% |

Hai loại kém nhất kém loại tốt nhất **gần ba lần**. Và chúng **ánh xạ thẳng** sang hai trong ba tầng
mà **Klarna** phải đưa nhân viên người trở lại sau khi quay đầu chiến lược AI tháng 5/2025 (*tranh
chấp · hoàn tiền phức tạp · khách khó khăn tài chính*). Ta tìm ra bằng dữ liệu nội bộ, họ tìm ra
bằng khách hàng thật — **cùng một kết luận, hai đường độc lập**.

**Vì sao hai loại này đắt hơn** *(không phải vì điểm thấp)*: cả hai đều là **tiền đã nằm trong tay
người khác**. Ví không lấy lại hộ được, chỉ đối soát và đề nghị. Trả lời sai ở đó là **để khách chờ
một thứ không bao giờ tới**. Ba loại còn lại sai thì lượt sau còn sửa được.

### Quyết định

**Tầng đắt = `refund` + `wrong_recipient`.** Ca thuộc tầng này mà **chưa xác định được giao dịch**
sau **N lượt** ⟹ **chuyển chuyên viên**, không cố thêm.

### 🔴 RANH GIỚI — làm sai cách là PHẠM RÀNG BUỘC CỨNG #2

Hiến pháp §2 mục 2: *"AI không vượt cấp… **escalate chỉ xảy ra qua tầng service** hoặc route của
`cskh` — **KHÔNG BAO GIỜ do AI tự gọi**."*

❌ **CẤM:** dạy agent tự quyết chuyển chuyên viên khi "thấy ca khó". Đó là **AI tự escalate** —
phạm thẳng ràng buộc cứng, và sẽ đỏ ở `tests/test_invariants.py` đúng như thiết kế.

✅ **ĐÚNG:** quy tắc **tất định** ở tầng service, máy đọc được, không cần mô hình hợp tác — cùng
khuôn với hai cơ chế đã chạy tốt (`_CHUA_TAO_DUOC_VE` và cổng CTC1/ADR-056):

```
complaint_type ∈ {refund, wrong_recipient}  AND  số lượt ≥ N  AND  chưa xác định được giao dịch
   ⟹ tầng service đánh dấu chuyển chuyên viên
```

**Tầng service quyết định. AI không quyết gì cả** — nó vẫn chỉ điều tra và trả lời như cũ.
Khác biệt nghe nhỏ mà là ranh giới sống còn: *"AI thấy khó thì bỏ cuộc"* ≠ *"hệ thống có luật: ca
loại này quá N lượt chưa ra thì đưa người"*.

### N = 2 — TẠM CHỌN, và tôi khai rõ là chưa chắc

Dữ liệu 180 ca: đỉnh tỉ lệ đạt nằm ở **2 lượt thêm (17/26 = 65,4%)**, tụt ở 3 lượt/chạm trần
(11/43 = 25,6%), và 0 lượt gần như luôn hỏng (2/68 = 2,9%).
🔴 **Nhưng đây là số từ MỘT lượt đo, và ta đã chứng minh nhiễu lớn** (22/75 ca đổi kết quả khi chạy
lại cùng bản mã — xem kết luận ADR-056). Thêm nữa, `security`/`review` chỉ ra con số "0 lượt" phần
lớn là **artefact của bộ mô phỏng** (hội thoại dừng vì câu cuối không có dấu hỏi), không phải hành
vi agent.
⟹ **N=2 là điểm khởi đầu có căn cứ yếu, KHÔNG phải hằng số đã chứng minh.** Phải xem lại khi có
nhiều lượt đo. Đừng ai trích N=2 như một ngưỡng đã kiểm.

### 🔴 HỆ QUẢ ĐO LƯỜNG — điểm tổng SẼ TỤT, và đó là ĐÚNG THIẾT KẾ

Ca chuyển người sớm là ca agent **không tự giải quyết** ⟹ bộ chấm hiện tại tính là **không đạt**.
Áp ADR này rồi đo lại thì con số **xấu đi**.

**Đừng ai thấy điểm tụt rồi kết luận ADR-057 hỏng.** Thước cũ đo *"agent tự làm được bao nhiêu"* —
mà ADR này cố ý **giảm** con số đó để tăng thứ khác.
⟹ Phải bổ sung chỉ số mới đo đúng thứ ADR nhắm tới: **tỉ lệ ca tầng đắt được chuyển người ĐÚNG
LÚC**, thay vì quẩn quanh tới hết lượt (dạng `MT-Z02`/`MT-Z04`).
⟹ Luật chung rút ra: **đổi mục tiêu thì phải đổi thước cùng lúc** — nếu không, thước cũ sẽ phạt
đúng thứ ta vừa cố ý làm.

### Việc phải làm, theo thứ tự
1. PO thật duyệt ADR này *(quy trình §3 — contract không đổi, nhưng chính sách escalate thì có)*
2. Coder cài quy tắc ở **tầng service**, không phải trong prompt · `test_invariants.py` **23/23 xanh**
3. Bổ sung chỉ số "chuyển người đúng lúc" vào bộ chấm **TRƯỚC** khi đo lại
4. Đo lại, và **so bằng chỉ số mới**, không so bằng điểm tổng cũ

## ADR-058 — Ngoại lệ có thời hạn: `qwen3.8-flash` (không tên ghim) cho demo 01/09
- **Ngày:** 2026-09-01
- **Bối cảnh:** [ĐO 22h] Ping trực tiếp cả 7 model trong `LLM_MODEL_POOL` bằng khoá container
  (max_tokens=1) → **4/7 trả 403**, gồm cả model đang ghim ở `LLM_MODEL`
  (`qwen3.7-max-2026-06-08`) và model mà một quyết định trước đó trong đêm định dùng thay thế
  (`qwen3.7-flash-2026-07-15`) — bể hỏng nặng hơn ghi nhận trước đó. PO thật bật token trả phí
  cho `qwen3.8-flash` (ping 200 OK) và chọn dùng thẳng model này cho live chat đêm nay.
- **Quyết định:** Cho phép `LLM_MODEL=qwen3.8-flash` + `LLM_MODEL_POOL` gồm `qwen3.8-flash` và
  3 model ghim mốc ngày đã đo 200 OK (`qwen3.6-plus-2026-04-02`, `qwen3.6-flash-2026-04-16`,
  `qwen3.5-flash-2026-02-23`) — áp dụng **duy nhất cho phiên demo 01/09 trên ngăn `po-demo`**.
  `qwen3.8-flash` **không** có tên ghim mốc ngày, đúng dạng ADR-043 §9 quy định phải bị từ chối.
- **Phương án đã cân nhắc và bác bỏ:** Giữ nguyên bể cũ (7 model, đủ tên ghim) — bác bỏ vì 4/7
  đã 403, không đủ độ sống cho live chat đêm nay. Chờ tìm một tên ghim mốc ngày tương đương
  `qwen3.8-flash` — bác bỏ vì không có thời gian trong cửa sổ 2 tiếng, và PO thật đã quyết dùng
  ngay model đã bật phí. **Không nới ADR-043 §42** ("mọi phép đo nghiêm túc phải GHIM model") —
  ngoại lệ này CHỈ áp cho demo, **không** áp cho golden/heldout/benchmark; đo nghiêm túc sau này
  vẫn phải quay lại tên ghim mốc ngày, kể cả nếu dùng lại `qwen3.8-flash` thì phải chờ nó có một
  bản ghim tương đương hoặc ghi nhận rõ trong báo cáo đo là "không ghim, không tái lập được".
- **Hệ quả:** Không đổi `contracts/`. [ĐO] `src/config.py` hiện **không có guard code** kiểm định
  dạng tên model (có mốc ngày hay không) — ADR-043 §9 là quyết định đã duyệt nhưng **chưa được
  ép trong mã**, đây là khoảng trống "duyệt trên giấy, chưa ép trong mã" cùng loại việc ADR-033
  từng lập cổng canh để bắt. **Nợ kỹ thuật, chưa vá đêm nay** (đụng `src/`, ngoài phạm vi đợt
  2 tiếng) — ghi vào sổ tồn đọng `STATE.md` cho đợt sau: thêm cổng đỏ-trước/xanh-sau kiểm tên
  model trong bể có khớp định dạng ghim mốc ngày không, trừ khi có cờ ngoại lệ tường minh kiểu
  ADR này. Yếu tố giảm nhẹ rủi ro: 4 lớp lọc đầu ra O1–O4 là regex tất định, độc lập với model —
  đổi model không làm guardrail yếu đi.
- **Thay thế:** không (bổ sung ngoại lệ có thời hạn cho ADR-043 §9, không thay thế nguyên tắc gốc)
- **Người duyệt:** PO thật *(qua PO-agent tự sửa `.env` — ADR này là bản trình duyệt tường minh,
  chưa coi là chính thức tới khi PO thật xác nhận trực tiếp)*

## ADR-059 — SỬA ADR-058: `qwen3.8-flash` là BASELINE đo lường, không phải ngoại lệ demo
- **Ngày:** 2026-09-01
- **Bối cảnh:** ADR-058 (viết cùng đêm, ngay phía trên) khai `qwen3.8-flash` là "ngoại lệ có
  thời hạn, chỉ áp cho demo, không dùng cho đo nghiêm túc" — **SAI DỮ KIỆN**. [ĐO] `docs/STATE.md:487`:
  toàn bộ **246 ca benchmark 31/08** (golden 120 · heldout 60 · đối kháng 66) chạy trên chính
  `qwen3.8-flash`. [ĐO] `docs/STATE.md:686`: một lượt chạy nhầm `qwen3.7-max-2026-05-20` bị xếp
  là **SỰ CỐ** (mất 137 phút), và cách sửa ghi nguyên văn là *"✅ về `qwen3.8-flash`"* — tức
  `qwen3.8-flash` **đã là baseline được công nhận từ trước**, không phải lựa chọn mới của đêm nay.
  Lỗi thuộc về Lead (viết ADR-058 theo hướng dẫn sai của PO-agent, không tự đối chiếu `STATE.md`
  trước khi viết) và PO-agent (dặn sai hướng). PO thật tự đọc lại tài liệu và bắt được.
- **Quyết định:** ADR-058 **giữ nguyên, không sửa/xoá** (đúng CLAUDE.md §7b — ADR chỉ ghi thêm).
  ADR này khai: câu *"KHÔNG dùng cho phép đo benchmark, ADR-043 §42 vẫn nguyên hiệu lực"* trong
  ADR-058 là **SAI**, đọc thành: `qwen3.8-flash` **đã và đang** là model benchmark thực tế của dự
  án từ 31/08. **ADR-043 §9** ("Bể chỉ nhận TÊN GHIM… bí danh trôi ⟹ từ chối lúc khởi động") coi
  như **bị bỏ qua trong thực tế từ 31/08**, chưa từng có ADR nào khai việc đó tới hôm nay — ADR
  này chính thức khai, và công nhận thực tế thay vì giả vờ luật vẫn được tuân thủ.
- **Phương án đã cân nhắc và bác bỏ:** Buộc benchmark quay lại dùng tên ghim mốc ngày cho đúng
  ADR-043 §9 — bác bỏ đêm nay vì không có thời gian tìm/xác nhận một tên ghim tương đương trước
  hạn 24:00, và đổi model giữa chừng phá khả năng so sánh với 246 ca đã đo. Coi đây là việc của
  đợt sau, không phải quyết định vĩnh viễn từ bỏ nguyên tắc ghim.
- **Hệ quả — nợ kỹ thuật NẶNG hơn ADR-058 mô tả:**
  1. [ĐO] `src/config.py` **không có guard nào ép ADR-043 §9** — nếu guard đó tồn tại như ADR-043
     hứa, benchmark 31/08 (246 ca, quan trọng nhất dự án) **đã không chạy được**. Luật đứng trên
     giấy, thực tế đã đi qua nó, không ai khai — cho tới ADR này.
  2. 🔴 **Rủi ro sống, không phải giả định:** `qwen3.8-flash` không mốc ngày ⟹ nhà cung cấp có thể
     đổi nó sang phiên bản khác **bất kỳ đêm nào** mà không ai biết — khi đó **mọi số của benchmark
     31/08 mất khả năng tái lập**, và không có cơ chế nào phát hiện việc đó đã xảy ra.
  3. Việc cần làm (đợt sau, không phải đêm nay): (a) thêm guard kiểm định dạng tên model trong
     `src/config.py`, cho phép danh sách ngoại lệ tường minh (kiểu allowlist có ADR đi kèm) thay vì
     từ chối cứng mọi bí danh; (b) tìm/xác nhận một tên ghim mốc ngày tương đương `qwen3.8-flash`
     nếu nhà cung cấp có cung cấp, để benchmark tương lai tái lập được.
- **Thay thế:** ADR-058 (phần khẳng định phạm vi "chỉ demo, không benchmark" — phần còn lại của
  ADR-058, tức bản thân việc chọn `qwen3.8-flash` cho `po-demo` tối nay, vẫn đúng và không đổi).
  ADR-043 §9 coi như **bị thực tế vượt qua từ 31/08**, chưa chính thức sửa — đợt sau cần quyết
  giữ nguyên §9 kèm allowlist, hay sửa lại nguyên tắc.
- **Người duyệt:** PO thật *(tự đọc lại tài liệu và bắt lỗi, quan trọng hơn thứ tự thẩm quyền
  thông thường: đây là PO thật tự sửa dữ kiện, không phải PO-agent tự quyết)*

## ADR-060 — Bật hiển thị OTP duyệt trong CHẾ ĐỘ DEMO (ngang hàng login OTP); production tuyệt đối không hiện
- **Ngày:** 2026-09-03
- **Bối cảnh:** Bản vá P0 `bdaf17e` (31/08) gỡ hiển thị mã OTP duyệt khỏi màn Sếp — yếu tố "sở
  hữu" cho hành động tài chính cao nhất (duyệt hoàn tiền). Đúng về bảo mật production. NHƯNG gỡ
  hẳn mà **không dựng kênh demo thay thế**: số điện thoại toàn dự án là GIẢ ⟹ không có SMS thật ⟹
  trong demo, OTP duyệt **chỉ lấy được qua tab Network/log, không có đường UI**. Trong khi login OTP
  vẫn hiện trên màn trong demo (`ChatClient` render `demoOtpCode`). Lệch, và làm bước Sếp-duyệt-OTP
  **không quay video sạch được**. PO thật cần quay đoạn showcase một-vé liền mạch có cả bước này.
- **Quyết định:** Bật lại hiển thị mã OTP duyệt trên màn Sếp **CHỈ trong chế độ demo** (gate theo
  cờ demo, giống hệt cách login OTP đang làm), production **tuyệt đối không hiện và không trả
  `otp_code` trong response**. Đưa OTP duyệt về **ngang hàng** login OTP trong demo — không hơn.
- **Ràng buộc bất di (Coder phải giữ):**
  1. `secrets.compare_digest` ở backend GIỮ NGUYÊN — duyệt vẫn bắt buộc OTP đúng, không bypass.
  2. Gate demo-only **fail-closed**: production (không bật cờ demo) không hiện mã, không trả
     `otp_code`. Giữ nguyên guard `config.py` fail-fast (`OTP_DEMO_MODE=true` + `APP_ENV=production`
     ⟹ chết lúc khởi động).
  3. Chỉ sửa **hiển thị + gate**, KHÔNG đụng logic HITL / authority-matrix / compare.
- **Phương án đã cân nhắc và bác bỏ:** (A) Quay off-camera lấy mã từ Network tab — bác vì "Sếp lấy
  OTP ở đâu" nằm off-camera, gượng, và số điện thoại giả nên không có câu chuyện "nhận qua điện
  thoại" để kể. (C) Giữ nguyên bản vá P0, không đụng — bác vì để lại khoảng trống demo không lấp
  (OTP duyệt không có kênh UI nào trong demo).
- **Hệ quả:**
  1. Video quay được bước Sếp duyệt OTP sạch, nhất quán với login OTP.
  2. Rủi ro chấp nhận: trong DEMO, OTP duyệt hiện trên màn — đúng như login OTP đã chấp nhận từ
     trước. **Production KHÔNG đổi** (vẫn ẩn nhờ gate). Nới lỏng CHỈ cho môi trường demo cô lập, dữ
     liệu giả — không phải production.
  3. 🔴 Lưu ý triển khai: bật `OTP_DEMO_MODE` xung đột với `APP_ENV=production` (guard `config.py`
     fail-fast). Coder cần giải quyết (cờ/ảnh `quay-video` riêng, hoặc `APP_ENV != production` cho
     ảnh đó) — **đề xuất phương án trước khi land**, vì đụng recreate + lớp bảo mật.
- **Người duyệt:** PO thật (chọn "B" trực tiếp, 03/09/2026).

## ADR-061 — Vá Finding ①: lọc theo `scope` mức CHUNK + cổng abstention bằng cross-encoder rerank (không dùng ngưỡng embedding đơn, không dùng LLM chấm)
- **Ngày:** 2026-09-03
- **Bối cảnh:** `search_policy`/`/policy-search` không có cổng lọc liên quan — câu rác hoặc câu lạc
  đề scope vẫn trả `status=found` kèm chunk chính sách CÓ THẬT nhưng sai ngữ cảnh, chạm Ràng buộc
  cứng #3. Đã thử hướng ngưỡng khoảng cách embedding đơn (30/08, đo lại 01/09 và 03/09 trên kho
  thật) — THẤT BẠI cả ba lần đo: câu near-miss "phí liên ngân hàng" cho distance 0.9697/0.9059,
  nằm sâu trong vùng lõi nhóm liên quan (0.698–0.936), không ngưỡng nào tách được mà không cắt
  luôn ca khớp thật yếu nhất.
- **Quyết định:** Vá bằng HAI LỚP độc lập, không thay thế lẫn nhau:
  1. Lọc theo `scope` — gắn ở mức CHUNK (không phải document): khảo sát nội dung thật cho thấy
     một tài liệu FAQ (297 chunk) tự nó trộn nhiều chủ đề (liên kết ngân hàng, thanh toán hoá đơn,
     dịch vụ, khuyến mãi) — document-level không đủ mịn để giải đúng ca near-miss. Cơ chế lọc:
     nới `k` truy vấn Chroma (không đổi embedding/Chroma schema), lọc theo `chunk.scope` khớp
     `complaint.scope` (hoặc `chunk.scope=="unknown"` luôn qua) trong Python, cắt về số kết quả
     cuối.
  2. Cổng abstention — cross-encoder rerank-gate, KHÔNG dùng LLM chấm ("grounded generation"):
     dự án có nguyên tắc xuyên suốt "guardrail tất định, độc lập với model" (O1–O4); cross-encoder
     mã hoá CHUNG query+chunk nên bắt được loại lỗi mà bi-encoder (đã thất bại) không bắt được,
     chạy CPU rẻ, không tốn token LLM.
- **Ràng buộc bất di:**
  1. `scope='unknown'` CHỈ khi thật sự không có căn cứ phân loại — BA review THẬT bản nháp
     auto-phân-loại (script từ khoá tiêu đề FAQ), không rubber-stamp toàn bộ về `unknown`.
  2. Model cross-encoder PHẢI đo hiệu quả trên câu TIẾNG VIỆT thật trước khi chọn — không tiền
     cam kết tên model. Nếu cần cài thêm hạ tầng (RAM/model mới), báo trước khi cài.
  3. Không đụng `contracts/agent-tools.yaml` cho tới khi ADR này được duyệt chính thức — chỉ sửa
     `ghi_chu` mô tả (docstring `not_found` hiện sai, không phải đổi input/output/chữ ký), qua
     đúng quy trình §3 hiến pháp.
  4. Không gộp UI chọn scope lúc upload vào đợt này — tài liệu mới mặc định `scope='unknown'`,
     Lớp 2 (abstention) chịu trách nhiệm phần đó. Việc kiểm duyệt nội dung upload track riêng
     theo finding bảo mật (`docs/security/2026-09-03-finding-rag-upload-khong-kiem-duyet-noi-dung.md`).
- **Phương án đã cân nhắc và bác bỏ:** (A) Ngưỡng embedding đơn — bác, đã đo 3 lần, thất bại có
  số liệu. (B) Scope mức document — bác, nội dung thật trộn chủ đề trong một tài liệu. (C)
  Grounded-generation bằng LLM chấm liên quan — bác, đi ngược nguyên tắc guardrail tất định độc
  lập model, thêm chi phí/độ trễ, tự nó có thể bịa "liên quan" giống cách LLM bịa số. (D) Gộp UI
  chọn scope lúc upload vào đợt này — hoãn, không chặn việc vá chính.
- **Kế hoạch đo (bắt buộc trước khi tuyên bố xong, không "trông ổn"):** đo TRƯỚC/SAU trên cùng
  tập test, lấy đủ BA số: precision khi `found` · tỉ lệ abstain ĐÚNG (near-miss + rác) · tỉ lệ
  abstain SAI trên câu THẬT (né lặp lại lỗi "từ chối quá tay" 12–16% đã ghi nhận ở nơi khác của
  hệ thống). Tập test gồm: relevant × 3 scope thật + near-miss-sai-scope + rác + query dò nội
  dung `STATE.md` — **VÀ bắt buộc thêm bucket KHÔNG kèm `complaint.scope`** (mô phỏng đúng đường
  AGENT tự gọi `search_policy`, hiện không truyền scope) cho cả near-miss lẫn query dò STATE.md,
  đo RIÊNG số abstain-đúng cho bucket này, không gộp chung với bucket có scope — đây là ca nguy
  hiểm nhất, đo chung sẽ che mất. Đo qua gọi thẳng `POST /policy-search` (tất định, không qua
  LLM/agent, không tốn token) — không sửa hạ tầng `run_golden_set.py` trong đợt này.
- **Hệ quả:**
  1. Cần migration thêm cột `scope` (nullable, CHECK 4 giá trị y hệt `ck_complaints_scope`) vào
     `policy_chunks`.
  2. Cần backfill scope cho 378 chunk hiện có (BA review bản nháp auto-phân-loại của tech-lead).
  3. `search_policy` không đổi chữ ký (`status`/`results` giữ nguyên type) — nhưng đổi HÀNH VI
     thật (nhiều `not_found` hơn, đúng mục đích). Ghi rõ để không ai đọc contract tĩnh mà tưởng
     hành vi không đổi.
  4. Tài liệu mới nạp sau ADR này mặc định `scope=unknown` cho tới khi có UI gán (việc SAU, chưa
     có ngày cam kết).
  5. 🔴 `scope='unknown'` LUÔN qua Lớp 1 (thiết kế "trực giao mọi scope") — đây là LỖ CỐ HỮU của
     Lớp 1, không phải bug: chunk `unknown` + đường agent không truyền scope ⟹ Lớp 1 hoàn toàn
     INERT. Chỉ Lớp 2 gác được hai trường hợp này. Hệ quả vận hành: (a) tối thiểu hoá số chunk
     `unknown` là điều kiện SỐNG CÒN cho hiệu quả Lớp 1, không phải tối ưu phụ; (b) Lớp 2 PHẢI tự
     đứng vững một mình cho đường agent + nội dung `unknown`, không được thiết kế như "lớp phụ
     trợ sau Lớp 1".
- **Người duyệt:** Hướng hai lớp (①lọc scope + ②abstention) do PO THẬT chốt 03/09. Thiết kế kỹ
  thuật cụ thể (chunk-level, cross-encoder, chi tiết migration) do phiên PO duyệt theo uỷ quyền —
  sẽ tóm tắt lại cho PO thật, không phải PO thật tự đọc từng dòng kỹ thuật.

**Cập nhật 04/09 (kiến trúc) — Lớp 2 dùng SIDECAR, không load model trong từng worker backend.**
Bối cảnh: đo được `po-demo` backend chạy **4-5 tiến trình uvicorn worker độc lập**
(multiprocessing, không chia sẻ bộ nhớ tiến trình). Load cross-encoder trực tiếp trong
`search_policy_text` sẽ nhân RAM theo số worker: PyTorch full ~812MB × 4-5 = **3,2-4,1GB**;
ONNX int8-quantize ~1008MB × 4-5 = **4,0-5,0GB** (🔴 ONNX KHÔNG nhẹ hơn PyTorch cho tổ hợp
model/thư viện này — giả định ban đầu "ONNX thường giảm 2-4 lần" đã đo và RÚT LẠI, đừng lặp
lại giả định đó ở đợt sau). Cả hai đều là chi phí không chấp nhận được trên hạ tầng hiện tại.
**Quyết định:** tách rerank thành **service riêng (sidecar)** trong ngăn compose — load model
ĐÚNG MỘT LẦN, mọi worker backend gọi qua HTTP nội bộ (docker network) thay vì tự load. RAM cho
reranker cố định ~1 instance (~800MB đo thật qua `docker stats`, khớp đo trên host), không
nhân theo worker.
**Ràng buộc fallback (bắt buộc):** sidecar chết/timeout/lỗi mạng ⟹ `search_policy_text`
**KHÔNG được crash**, xử lý như **KHÔNG có ứng viên nào qua được rerank** ⟹ `status=not_found`.
Lý do chọn "fail-closed thành not_found" thay vì "trả kết quả chưa lọc khi sidecar chết": trả
chưa lọc khi sidecar hỏng tái tạo NGUYÊN VẸN Finding ① (lạc đề/rác lọt qua) đúng lúc cần Lớp 2
nhất — vi phạm Ràng buộc cứng #3 (thà "không tìm thấy" còn hơn nói sai). Đánh đổi: sidecar
không ổn định ⟹ tính năng tra cứu chính sách kém khả dụng hơn (nhiều `not_found` hơn) — chấp
nhận được, vì "kém khả dụng" an toàn hơn "khả dụng nhưng sai".
**Đã cân nhắc và bác:** load model trong từng worker (RAM nhân ×4-5, đã đo, không chấp nhận
được) · IPC/shared-memory riêng (công sức cao, nhiều bề mặt lỗi mới, không hợp cho phạm vi
đợt này) · giảm worker xuống 1-2 (chỉ giải quyết tạm cho demo, không phải hướng chất lượng
sản phẩm PO thật vừa chốt).
**Người duyệt:** PO thật (04/09, qua phiên PO — chọn sidecar trong 3 phương án đã khảo sát).

## ADR-062 — Nối dây `complaint_id` cho `/policy-search` (CSKH), scope-aware, chặn IDOR
- **Ngày:** 2026-09-04
- **Bối cảnh:** ADR-061 thiết kế Lớp 1 (lọc theo `scope`) nhưng không có đường gọi nào trong
  code base cung cấp được `scope` cho `search_policy_text` — đường agent
  (`customer_tools.py:999`, `build_customer_tools()`) không có `complaint`/`scope` trong tham
  số; đường CSKH (`/policy-search`, `main.py`) trước đó chỉ có `query`+`top_k`. Nếu chỉ viết
  hàm lọc mà không nối dây, Lớp 1 "đã code nhưng không bao giờ chạy" — mọi lời gọi thật luôn
  truyền `None`, không có giá trị vận hành.
- **Quyết định:** Nối dây THẬT cho đường CSKH — thêm `complaint_id: str | None = None`
  (optional, `extra="forbid"` giữ nguyên) vào `PolicySearchRequest`. Route tự tra
  `Complaint.scope` từ `complaint_id` SERVER-SIDE — **không tin `scope` do client tự khai**.
  Đường agent giữ nguyên KHÔNG có scope (kiến trúc hiện tại không thay đổi); Lớp 2
  (cross-encoder, ADR-061) là tuyến gác duy nhất cho đường đó, đúng đã ghi trong ADR-061 Hệ
  quả #5.
- **Ràng buộc bất di (chặn IDOR):**
  1. Trước khi đọc `Complaint.scope`, kiểm caller có quyền trên `complaint_id` đó — dùng đúng
     pattern quyền có sẵn (`require_role("cskh","supervisor")`, cùng khuôn `get_ticket_detail`
     — cskh/supervisor vốn thấy được mọi vé, không phát minh mô hình quyền riêng cho route
     này). Không có quyền / `complaint_id` không tồn tại ⟹ coi như `scope=None` (bỏ lọc),
     **KHÔNG trả 403 phá luồng**, không lộ scope của vé người khác qua thông báo lỗi.
  2. `test_invariants` phải VẪN XANH sau khi thêm field — field optional không được đổi
     route count / roles / `authority-matrix.yaml`. [ĐO] chạy thật trong container po-demo:
     **23/23 xanh**, gồm `test_authority_matrix_khop_app_dang_chay` — xác nhận bằng máy, không
     chỉ bằng lời, rằng thay đổi này KHÔNG chạm `contracts/`.
- **Hệ quả:**
  1. `search_policy` (tool contract, `contracts/agent-tools.yaml`) KHÔNG đổi — thay đổi chỉ ở
     tầng HTTP request schema của route `/policy-search`, không phải chữ ký tool.
  2. CSKH tra chính sách CHO một vé cụ thể (truyền `complaint_id`) giờ được lọc đúng phạm vi
     giao dịch của vé đó — giá trị vận hành thật của Lớp 1, không còn là "code chết".
  3. Tra cứu KHÔNG gắn với vé cụ thể (không truyền `complaint_id`, hoặc đường agent) vẫn chỉ có
     Lớp 2 gác — không hồi quy so với trước.
- **Người duyệt:** PO thật (04/09, qua phiên PO — chọn "Option 1: nối dây thật, gộp 1 build"
  sau khi được trình phát hiện "Lớp 1 code nhưng không đường nào gọi được").

## ADR-063 — Chuông thông báo vé mới (CSKH & Sếp): 6 route mới, presence Redis, fan-out notifications
- **Ngày:** 2026-09-04
- **Bối cảnh:** Chatbot tạo vé → cần báo CSKH đang online; CSKH đề xuất (`propose_resolution`
  → `pending_approval`) → cần báo Sếp; Sếp duyệt/từ chối → cần báo ngược CSKH. Hiện không có
  cơ chế nào — CSKH/Sếp phải tự F5/tự kiểm hàng chờ.
- **Quyết định** (PO chốt 04/09, brief đầy đủ
  `docs/giao-viec/2026-09-04-po-build-chuong-thong-bao.md`):
  1. Độ bền khi cả kíp offline: LƯU thông báo cho MỌI CSKH liên quan (fan-out ghi 1 dòng/người
     nhận), chỉ ĐẨY tức thời cho người đang online — không để vé rơi.
  2. MVP: polling ~20s (WebSocket là đợt nâng cấp sau, không làm đợt này).
  3. Báo ngược khi Sếp duyệt/từ chối: CÓ, trong MVP.
  4. Cột "số vé đang xử lý" trong bảng Sếp: CÓ, trong MVP.
- **Công thức "số vé đang xử lý" của một CSKH** (tech-lead chốt, đúng đề xuất PO, khớp schema
  hiện có):
  `COUNT(ChatSession WHERE claimed_by=user_id AND status='active') + COUNT(Resolution WHERE
  created_by=user_id AND status='pending_approval')` — cả hai trường (`ChatSession.status`
  enum có sẵn `'active'`; `Resolution.created_by`/`status` từ BR-12 maker-checker, ADR-020) đã
  tồn tại đúng nghĩa cần dùng, không cần thêm cột `claimed_by` lên `Complaint` (vé vẫn là kho
  chung, đúng ràng buộc "CSKH không sở hữu vé").
- **Kiến trúc:** Presence qua Redis TTL (`presence:staff:<user_id>` EX 45s, ghi mỗi lượt
  `POST /presence/heartbeat` ~20s — không giữ state trong process, đúng nguyên tắc 4-worker).
  Notification là bảng Postgres mới `notifications`, fan-out (tạo trong CÙNG transaction với
  sự kiện gốc, không noti cho vé bị rollback), `read_at` riêng từng người nhận.
- **6 route mới**, roles `[cskh, supervisor]` (riêng `GET /presence/staff` chỉ `[supervisor]`):
  `GET /notifications` · `GET /notifications/unread-count` · `POST /notifications/{id}/read` ·
  `POST /notifications/read-all` · `POST /presence/heartbeat` · `GET /presence/staff`.
- **Ràng buộc bất di:**
  1. Cô lập theo người nhận (`recipient_user_id = người đăng nhập`) ép ở tầng SERVICE khi truy
     vấn — chống BOLA, không tin tham số client.
  2. Nội dung notification CHỈ mã vé + nhãn loại sự kiện — KHÔNG số tiền/PII/SĐT (Ràng buộc
     cứng #3 + PDPA).
  3. Cả 6 route khai `extra: [require_token_chua_thu_hoi]` NGAY TỪ ĐẦU trong contract — tránh
     lặp lại lớp bug "quên thêm route mới vào allowlist thu hồi token" (đã xảy ra 3 lần trước,
     xem finding logout 04/09; đây là bước đầu cho hướng deny-by-default đang thiết kế, áp
     trước cho route MỚI trong lúc thiết kế tổng thể còn đang làm).
- **Hệ quả:** `authority-matrix.yaml` v2.1.0→v2.2.0 (+6 route, không đổi route/role cũ nào).
  `test_invariants` dự kiến ĐỎ tạm thời ở `test_authority_matrix_khop_app_dang_chay` cho tới
  khi code landing đủ 6 route — đúng trình tự contract-first đã định, không phải hồi quy.
- **Thay thế:** không.
- **Người duyệt:** PO thật (04/09, qua phiên PO — greenlit build, xác nhận qua chính ADR này).

**Addendum (04/09, cùng ngày — GHI LẠI hành vi đã implement, không phải quyết định mới):** BOLA trên
notifications trả **404** (anti-enumeration, không 403) — không phân biệt được "không tồn tại" với "của
người khác". Xác nhận khớp `src/api/main.py::mark_notification_read` + test
`tests/test_api/test_notifications_bola.py`. Ràng buộc bất di #1 ở trên chỉ nói "cô lập tầng service,
chống BOLA" chưa ghi literal ngưỡng HTTP — dòng này chốt để hợp đồng không chỉ sống trong test.

**Addendum 2 (04/09, đợt polish trước quay demo — PO chốt):** `GET /notifications` thêm 4 trường vào
mỗi item: `complaint_type` · `scope` · `priority` · `sla_due_at` — để mỗi thẻ thông báo tự đủ thông tin
(loại khiếu nại/phạm vi/độ ưu tiên/SLA còn lại), CSKH/Sếp không phải mở vé mới biết. **KHÔNG vi phạm
Ràng buộc bất di #2** ("chỉ mã vé + nhãn sự kiện, KHÔNG số tiền/PII/SĐT") — 4 trường này là dữ liệu
PHÂN LOẠI/VẬN HÀNH, đã hiển thị công khai trên danh sách vé cho CSKH từ trước, không phải PII cá nhân
khách/bên thứ ba. Security xác nhận qua Lead (04/09): không phạm PII/BOLA, và tự kiểm thêm không xung
đột ADR-064 (fan-out "vé mới" gửi mọi CSKH đúng lúc ticket CHƯA claim được — khớp chính xác luật
pool-visibility, không phải ngoại lệ).
- **Kỹ thuật:** JOIN sang `Ticket`/`Complaint` LÚC ĐỌC (`GET /notifications`), KHÔNG snapshot lúc
  fan-out — vì `priority` KHÔNG bất biến sau khi tạo (`_nang_uu_tien_theo_cam_xuc`, `graph.py`, ghi đè
  priority SAU KHI ticket tồn tại khi tín hiệu cảm xúc khách kích). Snapshot lúc fan-out sẽ tạo lỗi
  "số liệu cũ trông như đang đúng" nếu case bị nâng ưu tiên sau khi noti đã gửi.
- **Hệ quả:** Không đổi route/role/schema `notifications` — field mới CHỈ ở response, không phải cột
  DB mới. Không cần quy trình §3 (không đổi `authority-matrix.yaml`/`resolution-state-machine.yaml`).
- **Người duyệt:** PO thật (04/09, qua phiên PO), Security xác nhận non-PII qua Lead cùng ngày.

## ADR-064 — Phạm vi nhìn ticket theo claim: CSKH chỉ thấy pool+của mình, Sếp thấy tất cả
- **Ngày:** 2026-09-04
- **Bối cảnh:** PO yêu cầu 2 việc gộp một thiết kế backend (`GET /tickets`): (1) CSKH hiện thấy
  TOÀN BỘ ticket hệ thống, không phân biệt ai đã nhận xử lý — gây nhiễu/dẫm chân khi đông CSKH;
  (2) Sếp cần thêm 1 màn riêng xem TẤT CẢ ticket để quản lý (hành vi này Sếp ĐÃ có sẵn, chỉ thiếu
  lối vào UI — landed riêng, tab "Quản lý ticket", commit `11192cd`).
- **Bằng chứng đã đo (Coder, 04/09):**
  - `src/api/main.py` (`GET /tickets`): filter DUY NHẤT hiện có là `hitl_status` (tuỳ chọn) —
    không filter theo người gọi. Mọi CSKH/Sếp nhận CÙNG một danh sách.
  - `src/db/models.py` (model `Ticket`): KHÔNG có field ownership cấp-người nào. `assigned_role`
    chỉ là string cấp-VAI ("cskh"), không phải cấp NGƯỜI. `claimed_by` đã tồn tại nhưng ở bảng
    KHÁC (`ChatSession`) — chưa từng áp cho `Ticket`.
  - `contracts/authority-matrix.yaml` ghi_chú route `GET /tickets/{id}/transcript` dùng CHÍNH câu
    "mọi cskh/supervisor vốn đã đọc được mọi ticket" làm CĂN CỨ cho một quyết định bảo mật khác —
    đổi hành vi `GET /tickets` làm câu này SAI ngay trong văn bản contract đang sống.
  - `tests/test_invariants.py::test_authority_matrix_khop_app_dang_chay` chỉ introspect
    route×role — KHÔNG bắt được thay đổi row-level này, không có lưới an toàn tự động.
- **Quyết định:**
  1. Thêm 2 cột `claimed_by: user_id | null`, `claimed_at: datetime | null` vào `Ticket`
     (migration mới).
  2. Route mới `POST /tickets/{ticket_id}/claim`, role `[cskh]` — CSKH bấm "Nhận vé" CHỦ ĐỘNG
     (khớp nút "Mở & nhận" đã có ở dashboard live-chat), set `claimed_by=current_user` +
     `claimed_at=now`. Idempotent: đã `claimed_by` CHÍNH MÌNH → 200 không đổi gì; đã `claimed_by`
     NGƯỜI KHÁC → 409 (không cho cướp vé). Supervisor KHÔNG có route này.
  3. `GET /tickets` (route/role không đổi, vẫn `[cskh, supervisor]`): CSKH lọc
     `WHERE claimed_by IS NULL OR claimed_by = current_user.user_id`. Supervisor KHÔNG lọc, giữ
     nguyên như hôm nay — nền cho tab "Quản lý ticket".
  4. 🔴 **`GET /tickets/{ticket_id}/transcript` KHOÁ THEO CÙNG LUẬT** (không phải "để mở" như đề
     xuất ban đầu) — CSKH: `claimed_by IS NULL OR = mình`; Supervisor: không lọc. Lý do PO chốt:
     để mở mâu thuẫn thẳng với "CSKH chỉ thấy vé của mình" và hở BOLA trên transcript chứa PII
     hội thoại khách — đúng thứ tính năng này đang đóng. KHÔNG phá luồng bàn giao ADR-044: vé chờ
     handoff nằm trong POOL (`claimed_by IS NULL`) nên mọi CSKH trực vẫn đọc được transcript pool
     để tiếp nhận; sau khi claim thì là của mình. Chỉ transcript của vé CSKH KHÁC đã claim mới bị
     ẩn. Nhu cầu đọc chéo thật sau này (Sếp nhờ CSKH review vé người khác) → làm route/quyền
     RIÊNG có chủ đích, không mở toang mặc định. Test BOLA bổ sung: CSKH đọc transcript vé người
     khác đã claim → 404 (đúng khuôn anti-enumeration).
  5. `contracts/resolution-state-machine.yaml` — KHÔNG đổi. Claim là thuộc tính RIÊNG của
     `Ticket` (giống `ChatSession.claimed_by`), không phải 1 trục trong 3 trục
     `hitl_status`/`resolution.status`/`partner_wait_status` đã có.
- **Phương án đã cân nhắc và bác bỏ:**
  - *Lọc thuần ở tầng UI* (ẩn ticket của CSKH khác trên frontend, backend vẫn trả hết): BỊ BÁC
    BỎ — lỗ BOLA nguyên văn (CSKH-A gọi thẳng API vẫn lấy được ticket CSKH-B). PO yêu cầu tường
    minh "backend enforce, không chỉ ẩn UI".
  - *Khoá theo `complaint_id`* (chữ PO dùng ban đầu) hiểu là PK thật của `Complaint`: BỊ BÁC BỎ
    về kỹ thuật — `complaint_id` sinh ra SAU khi `create_ticket` chạy, không tồn tại tại thời
    điểm cần xác định "vé này của ai" khi CSKH đang xem hàng chờ. Diễn giải lại đúng tinh thần
    PO thành khoá theo `Ticket.ticket_id` (tồn tại ngay lúc tạo, 1-1 với `Ticket`).
  - *Route transcript để mở, không khoá theo claim* (đề xuất ban đầu của Coder): BỊ BÁC BỎ —
    xem điểm 4.
- **Hệ quả:**
  - Contract: `contracts/authority-matrix.yaml` (+1 route `POST /tickets/{id}/claim` [cskh];
    sửa ghi_chú route transcript cho khớp hành vi mới — CSKH đọc transcript pool để bàn giao,
    KHÔNG đọc transcript vé CSKH khác đã claim).
  - Migration mới cho `Ticket.claimed_by`/`claimed_at`.
  - Test mới (tester): BOLA cho `GET /tickets` VÀ `GET /tickets/{id}/transcript` (CSKH-A không
    thấy/đọc được ticket CSKH-B đã claim), regression cho Sếp (vẫn thấy toàn bộ cả 2 route),
    authz cho route claim mới (409 khi cướp vé, 200 idempotent khi claim lại chính mình).
  - `CONTRACT_VERSION` ở `tests/test_invariants.py` cần bump sau `check_contracts.py --update`.
- **Thay thế:** không.
- **Người duyệt:** PO thật (04/09, qua phiên PO).

**Addendum (04/09, cùng ngày, đợt polish trước quay demo — GHI DẤU VẾT breaking change, KHÔNG phải
quyết định §3):** `GET /tickets` đổi SHAPE response và thêm tham số lọc, phục vụ bảng ticket 660 dòng
không kéo hết 1 trang + filter chuyên nghiệp cho CSKH/Sếp. Route/role KHÔNG đổi (`[cskh, supervisor]`
như cũ) nên KHÔNG cần quy trình §3/đổi `authority-matrix.yaml`, nhưng shape đổi là breaking change thật
với mọi consumer, ghi lại để tra được sau này.
- **Shape CŨ → MỚI:** mảng trần `[{...}, ...]` → object phân trang `{"items": [{...cùng field cũ,
  không đổi...}], "total": int, "page": int, "page_size": int}`.
- **Param CŨ → MỚI:** `hitl_status` giữ nguyên; `limit` BỎ, thay bằng `page` (mặc định 1, ≥1 hay 422) +
  `page_size` (mặc định 50, CHỈ nhận 30/50/100 hay 422). Thêm mới: `complaint_type`/`scope`/`priority`/
  `sla_before`/`sla_after` — kết hợp AND với nhau và với `hitl_status` (SQL WHERE thật, không lọc tay
  sau khi fetch).
- **Consumer đã sửa:** `tests/test_api/test_ticket_claim_adr064.py` (đọc `.json()["items"]`),
  `frontend/src/lib/api.ts::listTickets()` (chữ ký + parse), `frontend/e2e/dashboard.spec.ts` (đổi neo
  UI — bỏ chip đếm "Tất cả (N)"/"Chờ tiếp nhận (N)" không có tham số server tương ứng, giữ lại làm
  toggle CLIENT-SIDE với nhãn rõ "(trang này)" tránh lặp lỗi đọc-nhầm-% đã bắt 20/08).
- **Consumer XÁC NHẬN không cần sửa:** `frontend/src/app/api/tickets/route.ts` (BFF, transparent proxy
  — forward query string, trả thẳng JSON, không parse shape); `test_authz_matrix.py` (chỉ assert
  status_code, không đọc body).
- **Frontend:** gộp `frontend/src/components/TicketListSection.tsx` dùng chung cho `/dashboard` (CSKH)
  và `/quan-ly-ticket` (Sếp) — 2 trang trước đó gần như copy-paste nguyên khối bảng+filter.
- **Fast-follow chưa đóng (§4-crossing cần soát lại):** `frontend/e2e/dashboard.spec.ts` do tech-lead
  sửa trực tiếp (đúng vùng ghi `tester` theo CLAUDE.md §4) vì shape mới làm spec cũ chắc chắn đỏ — báo
  Lead trước khi land, không lén. Tester cần soát lại TỪ SPEC (xác nhận assertion kiểm ĐÚNG hành vi
  mong đợi — 30/trang · filter AND · pool→claim mất vé — không chỉ khớp output của tech-lead) sau khi
  qua mốc quay demo. Không chặn quay (E2E là artifact CI, recording không phụ thuộc).
- **Người duyệt:** PO thật (04/09, qua phiên PO).

## ADR-065 — Deep-link toàn văn cho `/policy-search`: route mới `GET /policy-doc/{doc_id}`
- **Ngày:** 2026-09-05
- **Bối cảnh:** PO muốn (cho lượt quay demo) mỗi kết quả `/policy-search` có link mở TOÀN VĂN tài liệu
  chính sách/FAQ gốc ở tab mới, tự cuộn tới + tô sáng đúng đoạn đã khớp lúc tìm.
- **Bằng chứng đã đo (tech-lead, 05/09):** `PolicyChunk` KHÔNG lưu toàn văn — chỉ chunk 800 ký tự,
  `overlap=150` (`RecursiveCharacterTextSplitter`). Ghép các chunk theo `chunk_index` KHÔNG tái tạo
  đúng văn bản gốc (overlap lặp ở mỗi ranh giới). 4 tài liệu đang index: 2 tài liệu DÀI (FAQ giao dịch
  297 chunk, ToS 81 chunk — cuộn-tới-đúng-đoạn có ý nghĩa thật), 2 tài liệu NGẮN (1 chunk — toàn văn ≈
  đoạn trích, không cần rẽ nhánh riêng, cơ chế chung vẫn áp được). Security xác nhận (05/09, quét thật
  380 chunk bằng regex số + từ khoá định danh) 2 tài liệu dài KHÔNG lẫn PII khách hàng — chỉ thông tin
  công khai của công ty (mã số DN, hotline, địa chỉ) — đủ điều kiện PDPA phục vụ toàn văn.
- **Quyết định:**
  1. Thêm `PolicyDocument.full_text` (migration, KHÔNG phải §3 — không đụng route/role) — hook 1 dòng ở
     `ingest_document()` lưu văn bản gốc (đã có sẵn trong biến trước khi đưa vào splitter), không đổi
     logic chunk/index/rerank hiện có. Backfill 4 tài liệu đang có.
  2. `/policy-search` response thêm field `chunk_id` vào mỗi kết quả (ADDITIVE, không phá client cũ,
     không phải §3) — cần cho FE dựng link. Hàm search/ngưỡng `-2.5` GIỮ NGUYÊN 100%, không đụng.
  3. **Route MỚI `GET /policy-doc/{doc_id}?chunk_id=<optional>`**, roles `[cskh, supervisor]` — ĐÚNG
     như `/policy-search`, không nới rộng. `doc_id` tra qua DB (`status="indexed"`), KHÔNG qua
     filesystem — không có đường path-traversal, chỉ trả tài liệu đã nạp qua `/policy-docs`
     (`partner_admin`). Có `chunk_id`: tra `PolicyChunk`, xác nhận `chunk.doc_id == doc_id`, tìm vị trí
     bằng `full_text.find(chunk_text)` → trả `{start, end}` cho FE tô sáng. Không tìm ra (hiếm — chunk
     cũ trước khi có `full_text`, hoặc lệch parser) → `highlight: null`, FE vẫn mở tài liệu, chỉ không
     tô sáng/cuộn — suy giảm êm, không lỗi.
  4. FE: link "Xem toàn văn" (`target="_blank"`) trên mỗi kết quả `/policy-search` → trang mới qua BFF
     chuẩn `/api/policy-doc/[docId]` (không gọi thẳng backend từ client, đúng khuôn mọi route khác),
     bọc đoạn `[start,end]` trong `<mark>`, cuộn bằng `scrollIntoView`. Không cần entry `RoleTabNav`
     riêng (chỉ mở từ link, giống `/tickets/{id}`) — nhớ thêm `frontend/src/proxy.ts` allowlist.
- **Phương án đã cân nhắc và bác bỏ:** ghép các `PolicyChunk` theo `chunk_index` để dựng lại toàn văn
  thay vì lưu cột mới — BỊ BÁC BỎ, `overlap=150` làm văn bản ghép lặp/lệch ở mọi ranh giới chunk, không
  phải toàn văn thật.
- **Hệ quả:** `contracts/authority-matrix.yaml` +1 route `GET /policy-doc/{doc_id}` `[cskh, supervisor]`
  (không đổi route/role nào cũ). Migration mới cho `PolicyDocument.full_text`. `CONTRACT_VERSION` ở
  `tests/test_invariants.py` cần bump sau `check_contracts.py --update`. Test mới (tester): 404 cho
  `doc_id` không tồn tại/chưa indexed, `chunk_id` lệch `doc_id` bị từ chối, `highlight: null` khi không
  khớp được vị trí (suy giảm êm).
- **Thay thế:** không.
- **Người duyệt:** PO thật (05/09, qua phiên PO) — CHỜ DUYỆT tường minh trước khi
  `check_contracts.py --update` + code, đúng quy trình §3.

## ADR-066 — Portfolio edition: English code comments, English identifiers, comment-only contract edits
- **Date:** 2026-10-18
- **Context:** The owner is publishing a personal portfolio copy of this repository for
  international recruiters. Code comments, docstrings and many identifiers were Vietnamese.
- **Decision:**
  1. Translate every comment/docstring in `src/` to English. Each file was rewritten by a tool that
     refuses to save unless the Python AST (docstrings stripped) is byte-identical to the original —
     i.e. no executable code changed.
  2. Rename Vietnamese Python identifiers, module names and environment variables to English
     (token-aware rename; DB columns, JSON wire fields, Redis key values and LLM tool schemas are
     deliberately unchanged so the deployed data stays compatible).
  3. `contracts/*.yaml`: **comments only** were translated (plus a key glossary). The parsed YAML data
     was verified identical before/after (`yaml.safe_load` equality), so no route, role, enum or
     constraint changed. Hashes changed, hence `check_contracts.py --update` and a
     `CONTRACT_VERSION` bump in `tests/test_invariants.py`.
  4. Kept in Vietnamese on purpose: the agent system prompt, the five `@tool` docstrings (they are sent
     to the LLM as tool descriptions), customer-facing replies, Vietnamese-language regexes, eval
     datasets, and historical ADRs/journals. English renderings live in `docs/en/`.
- **Verification:** full backend suite run before and after; same pass/skip counts as the baseline
  commit except environment-dependent tests (documented in the portfolio QA checklist).
- **Replaces:** none.
- **Approved by:** the project owner/PO (2026-10-18, scope "all three tiers").
