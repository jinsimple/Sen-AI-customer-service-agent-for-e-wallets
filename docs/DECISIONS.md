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

### Quyết định 1 — `src/agents/khop_cum.py`: khớp cụm cho phép chèn hư từ, THUẦN CỘNG

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

- **Hệ quả:** `src/agents/khop_cum.py` (mới) · `src/agents/output_filter.py`
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

- **Ngày:** 2026-08-15 · **Trạng thái:** NGUYÊN TẮC ĐÃ ĐƯỢC PO THẬT DUYỆT 15/08
  ("chốt theo hướng security"); các CON SỐ đề xuất bên dưới do PO-agent nghiên cứu
  chuẩn EU/US theo uỷ quyền — chờ PO thật xác nhận nhanh trước khi coder chạm
  contract/code. Nền tảng kỹ thuật: hồ sơ security
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

**⚠️ Vì sao KHÔNG dùng bound 4.000 như bản đầu (security đo, chặn):** số 2.000→
3.556 của lượt đo đầu là trên văn bản GẦN-ASCII. Fernet nở theo **byte UTF-8**,
tiếng Việt ĐỦ DẤU là 3 byte/ký tự: 2.000 ký tự → 6.000 byte → **8.100 ciphertext
= VƯỢT bound 4.000** ⟹ khách viết khiếu nại 2.000 ký tự đủ dấu — cách viết bình
thường — dính `IntegrityError` → **500 giữa lúc khiếu nại** (hình dạng F-21),
trong khi nhìn ngoài trông như chống-flood chạy đúng. Đây là S-01 lặp ở cơ chế
khác: số biện minh đo trên mẫu hẹp áp cho mẫu rộng (Luật 8, lần bốn). Ca probe
bắt buộc trước khi ký A2: **A2-05 — 2.000 ký tự tiếng Việt đủ dấu → NHẬN.**

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
