# SPEC — (1) Deny-by-default kiểm token-thu-hồi, (2) cookie `secure=true`

> Vai: `security`. Giao từ Lead, chuẩn bị TRƯỚC buổi quay để Coder áp NGAY SAU, không thảo luận lại
> từ đầu. Việc thuần thiết kế/tài liệu — không đụng container/`po-demo` đang sống.
>
> Đọc trước: `docs/security/2026-09-04-cookie-session-va-logout-khong-thu-hoi-access-token.md`
> (finding gốc — access_token sống sau logout, xác nhận bằng gọi route thật) và
> `docs/security/2026-08-31-cong-do-truoc-xanh-sau-bdaf17e-5ff93b8.md` (gate 2 — 3 route đã vá 31/08).

---

## PHẦN 1 — Deny-by-default cho kiểm token-thu-hồi

### 1.0 🔴 Đối chiếu với quyết định ĐÃ CÓ trước khi thiết kế — không lờ đi

`src/auth.py:334-339` (docstring `require_otp_verified`, quyết định **AUTH5-06, 12/08**) đã tự khai
LÝ DO CỤ THỂ vì sao KHÔNG áp kiểm thu hồi cho toàn bộ route qua `get_current_user`: *"access token đã
rất ngắn hạn (15 phút), thêm 1 lần GET Redis vào MỌI request sẽ biến Redis thành single point of
failure cho cả hệ thống trong khi lợi ích biên rất nhỏ; route CHẠM DỮ LIỆU/TÀI CHÍNH thật xứng đáng
trả giá đó, route đọc thường thì không."*

Spec này **KHÔNG lật ngược quyết định đó bằng cách phớt lờ lý do của nó** — nó sửa đúng chỗ tiền đề
đã sai: `lookup_transaction`/`get_customer_history` bị xếp vào nhóm "đọc thường" lúc quyết định 12/08,
nhưng finding 04/09 (đo thật) cho thấy đây là **route đọc dữ liệu TÀI CHÍNH/GIAO DỊCH nhạy cảm nhất
hệ thống** — đúng nhóm "chạm dữ liệu/tài chính thật" mà chính AUTH5-06 nói LÀ xứng đáng trả giá Redis.
⟹ Ranh giới đúng không phải "đọc vs ghi", mà là **"dữ liệu có nhạy cảm không"** — AUTH5-06 vẽ sai
ranh giới, không phải sai nguyên tắc.

### 1.1 🔴 Phát hiện MỚI khi thiết kế spec này — quan trọng hơn cả finding gốc

**Gate REST route `/tools/lookup_transaction`/`/tools/get_customer_history` KHÔNG đủ để đóng lỗ cho
đường KHÁCH DÙNG THẬT NHẤT: `/agent/chat`.**

Đọc `src/api/main.py:671-710`: route `/agent/chat` chỉ có `Depends(require_role("customer"))` (không
kiểm thu hồi), rồi gọi THẲNG `run_agent_turn(...)` **trong cùng process** — truyền `user_id`,
`otp_verified_at` dưới dạng giá trị Python thuần, **KHÔNG** gọi lại qua HTTP tới
`/tools/lookup_transaction`/`/tools/get_customer_history`. Nghĩa là: LangGraph agent gọi các tool này
bằng **hàm Python nội bộ** (`src/agents/tools/customer_tools.py`), không đi qua FastAPI dependency
injection của các route REST đó.

⟹ **Nếu chỉ gate 2 route REST theo đúng y hệt lời Lead đề xuất, một access_token đã logout vẫn trò
chuyện được với AI bình thường và AI vẫn tự tra được toàn bộ ví/giao dịch/khiếu nại qua tool nội bộ —
đúng lỗ hổng gốc, chỉ đổi đường vào.** Route REST độc lập chỉ có giá trị chặn đường gọi API trực tiếp
(curl/Postman), không chặn đường CHAT — mà đường CHAT mới là đường 150 người thật sẽ dùng.

**Vị trí vá ĐÚNG, bổ sung vào danh sách:** `POST /agent/chat` (`main.py:676`) — đổi
`Depends(require_role("customer"))` thành có thêm kiểm thu hồi, kiểm **MỘT LẦN ở đầu route**, bảo vệ
NGUYÊN CẢ LƯỢT chat (không cần kiểm lại trong từng tool nội bộ — không có request HTTP mới nào sinh
ra giữa chừng để kiểm lại).

### 1.2 Thiết kế đề xuất — CI-enforced allowlist, KHÔNG phải bắt buộc runtime 100% route ngay

Thay vì đổi hành vi runtime của TOÀN BỘ 34 route cùng lúc (rủi ro cao, đúng lo ngại AUTH5-06 nếu làm
ẩu), dùng lại ĐÚNG cơ chế đã làm nên sức mạnh của dự án này — **contract + test introspect app đang
chạy** (`tests/test_invariants.py`, `CLAUDE.md §3`):

1. Thêm cột mới vào `contracts/authority-matrix.yaml`, mỗi route: `kiem_thu_hoi: true|false` +
   `ly_do_mien` (bắt buộc có nội dung khi `false`).
2. Test mới `test_moi_route_authenticated_co_khai_kiem_thu_hoi` — introspect từng route có
   `Depends(get_current_user)` (trực tiếp hoặc gián tiếp qua `require_role`) trong `closure`, xác
   nhận: (a) nếu `kiem_thu_hoi: true` trong contract ⟹ route đó PHẢI có `require_token_chua_thu_hoi`
   hoặc `require_otp_verified` trong dependency chain thật; (b) nếu route KHÔNG có contract entry
   nào ⟹ **ĐỎ** (route mới ai đó thêm mà quên khai — đúng tinh thần "deny-by-default": không khai
   nghĩa là chưa được phép coi là miễn).
3. Đây **là** deny-by-default, nhưng đóng ở TẦNG CI/TEST, không phải tầng RUNTIME — an toàn hơn để
   land trước buổi quay: không đổi hành vi request thật nào cho tới khi PO/tech-lead tự chọn gate
   route nào runtime, nhưng ngay từ commit tiếp theo, **thêm 1 route JWT mới mà quên khai kiểm thu
   hồi ⟹ test đỏ ngay**, không lặp lại kiểu lỗ "quên 3 route" đã xảy ra 2 lần (27/08, rồi lần này).

### 1.3 Phân loại toàn bộ route JWT hiện có (từ `contracts/authority-matrix.yaml`, 34 route)

**Không cần current_user / miễn tự nhiên (không đổi):**
`GET /health` · `POST /auth/login` · `POST /auth/refresh` · `WS /ws/live-chat` (ticket riêng, không
JWT).

**ĐÃ gate (6 route, AUTH5-06 + 31/08):**
`POST /tools/create_ticket` (qua `require_otp_verified`) · `POST /resolutions/{id}/approve` ·
`POST /resolutions/{id}/reject` · `POST /tools/propose_resolution` ·
`POST /tools/escalate_ticket` · `POST /resolutions/{id}/request-approval-otp`.

**🔴 CẦN GATE — khuyến nghị mạnh, có bằng chứng đo được (finding 04/09 + phát hiện 1.1):**
- `POST /agent/chat` — **ưu tiên CAO NHẤT trong toàn spec này**, đúng đường 150 người thật dùng, xem 1.1.
- `POST /tools/lookup_transaction` — đọc dữ liệu giao dịch bên thứ ba/chính chủ, đã có bằng chứng đo.
- `POST /tools/get_customer_history` — đọc TOÀN BỘ lịch sử ví/giao dịch/khiếu nại, đã có bằng chứng đo.

**Cần PO/tech-lead quyết (không tự xếp CẦN — mức nhạy cảm thấp hơn, nhưng đọc dữ liệu nghiệp vụ):**
- `GET /tickets`, `GET /tickets/{id}`, `GET /tickets/{id}/transcript` — dữ liệu khiếu nại, không phải
  dữ liệu ví/tiền trực tiếp, nhưng `transcript` (ADR-044) có thể chứa nội dung nhạy — cân nhắc gate.
- `POST /tickets/{id}/request-more-info`, `GET /resolutions`, `GET /reports/summary`,
  `POST /policy-search` — mức nhạy thấp hơn, đề xuất KHÔNG gate đợt này (giữ đúng tinh thần AUTH5-06
  cho nhóm thật sự "đọc thường").
- Nhóm `/live-chat/*` (7 route: ws-ticket ×2, by-ticket, waiting, claim, close, messages, csat) —
  **CẦN RÀ RIÊNG, ngoài phạm vi đo của finding 04/09** — tin nhắn live-chat có thể chứa nội dung
  khiếu nại/PII, nhưng cơ chế xác thực khác (ws-ticket dùng-một-lần, không phải JWT trực tiếp cho
  WebSocket) — không đưa vào danh sách "cần gate ngay", ghi lại để không quên rà sau.
- `POST /policy-docs`, `GET /policy-docs`, `DELETE /policy-docs/{id}` (partner_admin) — không chạm dữ
  liệu khách hàng (đúng INV-11), đề xuất KHÔNG cần gate, nhưng nối tiếp finding RAG-upload
  (`docs/security/2026-09-03-finding-rag-upload-...`) — nếu PO sau này quyết mở route supervisor xem
  cảnh báo upload, route MỚI đó nên tự động rơi vào yêu cầu khai `kiem_thu_hoi` ở mục 1.2.
- `POST /auth/logout` — miễn hợp lý (idempotent, gọi lại khi đã thu hồi không gây hại), ghi lý do
  tường minh trong contract, không phải bỏ sót.
- `POST /auth/otp/request`, `POST /auth/otp/verify` — **cân nhắc gate**: đây là bước THIẾT LẬP lại
  xác thực, nhưng nếu access_token GỐC đã bị thu hồi (logout), hợp lý để chặn luôn ở đây thay vì để
  qua rồi mới chặn ở bước sau — PO quyết, không tự ý xếp CẦN vì đổi UX luồng xác thực cần cân nhắc kỹ.

### 1.4 Migrate — không đổi hành vi runtime của 6 route đã gate, chỉ hình thức hoá lại

6 route ở mục "ĐÃ gate" chỉ cần thêm dòng `kiem_thu_hoi: true` vào contract (không đổi code) — chúng
đã đúng hành vi từ trước, spec này chỉ khiến chúng có ĐỊA CHỈ chính thức trong `contracts/`.

---

## PHẦN 2 — Cookie `secure: true`

### 2.1 Diff đề xuất — đúng 1 dòng, không đổi gì khác

File: `frontend/src/app/api/session/route.ts`, dòng 62-71 (khối `store.set(SESSION_COOKIE, ...)`):

```diff
   store.set(SESSION_COOKIE, JSON.stringify(session), {
     httpOnly: true,
     sameSite: "lax",
+    secure: true,
     path: "/",
     maxAge: sessionCookieMaxAgeSeconds(session.role),
   });
```

🔴 **KHÔNG cần điều kiện theo môi trường** (vd `secure: process.env.NODE_ENV === "production"`) —
toàn bộ kiến trúc (kể cả dev local) đã chạy qua Caddy HTTPS (`Caddyfile`, cert nội bộ cho `localhost`
khi dev). `secure: true` cứng, không nhánh theo env, đúng tinh thần "không có lý do hợp lệ để cookie
này đi qua HTTP" đã nêu trong finding gốc.

### 2.2 Checklist kiểm SAU khi land (không phải trước — không đụng `po-demo` sống lúc này)

Việc của `tester`/`security` sau khi Coder land + rebuild:

1. **Đăng nhập thật qua UI**, đọc DevTools → Application → Cookies → `fin05_session` → cột `Secure`
   phải là `✓` (trước khi vá: trống/false).
2. **Xác nhận KHÔNG hồi quy đăng nhập trên dev local** — nếu Caddy dev dùng cert tự ký mà trình duyệt
   chưa tin (chưa cài CA nội bộ), `secure: true` có thể khiến cookie KHÔNG được set nếu trình duyệt
   coi kết nối là "not secure" dù là HTTPS — **đây là rủi ro thật cần đo, không giả định suông**: login
   thử trên `po-demo`/`qa-stripe` sau khi vá, xác nhận cookie vẫn set được và phiên vẫn hoạt động
   bình thường (không bị đá về `/login` ngay sau khi vào).
3. **Đo qua route Cloudflare Tunnel** (nếu có bật profile `home` lúc kiểm) — xác nhận cookie vẫn set
   đúng qua đường đó (browser thấy HTTPS ở Cloudflare edge, nên phải ổn, nhưng đo thật không suy
   đoán, đúng kỷ luật "chạy thật, đọc log thật" của dự án).
4. **Test đỏ-trước/xanh-sau tối thiểu** (`tester`, viết từ SPEC này, không đọc `src/`): gọi
   `POST /api/session` (BFF login) thật, đọc header `Set-Cookie` trong response, xác nhận có
   `Secure` attribute. Đỏ trên commit TRƯỚC vá, xanh SAU.
5. **Không có tác dụng phụ lên `LAST_GATE_COOKIE`** — cookie gợi ý cổng (`httpOnly: false`) KHÔNG nằm
   trong phạm vi vá này, giữ nguyên. Xác nhận sau khi vá `SESSION_COOKIE` không vô tình đổi cookie kia.

---

## Ưu tiên khi Coder áp — thứ tự đề xuất

1. **`/agent/chat` gate thu hồi** (Phần 1.1) — đường thật khách dùng, giá trị cao nhất.
2. **`secure: true`** (Phần 2) — 1 dòng, không rủi ro, không phụ thuộc gì.
3. **`lookup_transaction`/`get_customer_history` gate** (Phần 1.3) — đóng nốt đường API trực tiếp.
4. **Cơ chế CI-enforced allowlist** (Phần 1.2) — làm nền cho lâu dài, không cấp bách bằng 3 mục trên
   nhưng nên làm CÙNG ĐỢT để không phải rebuild thêm lần nữa riêng cho việc này.

Cả 4 mục **không đổi `contracts/agent-tools.yaml`** (không đổi tool nào), mục 4 đổi
`contracts/authority-matrix.yaml` (thêm cột, không đổi route/role nào hiện có) — theo đúng quy trình
`CLAUDE.md §3`, cần ADR ngắn khi land (không phải xin duyệt lại thiết kế, chỉ ghi nhận đổi contract).
