# Soát phơi nhiễm lần đầu P-226 ra Internet — 4 đường (PO-agent giao 20/08)

> Bối cảnh giao việc: P-226 CHƯA từng deploy — `app.adaptivealgo.uk` hiện chạy repo khác
> (`P-121-new`). Mọi `docker-compose*.yml`/`Dockerfile` ở đây mới chỉ chạy sau `localhost`,
> chưa từng chạm Internet thật. **KHÔNG đụng `app.adaptivealgo.uk`** trong khi làm việc này —
> toàn bộ phép đo dưới đây chạy trên repo tĩnh + `docker exec` vào stack `fin05` cục bộ.
>
> **Kết luận đầu, đọc trước:** không có phát hiện nào ở mức "không được deploy trước khi vá".
> Cả 4 đường đều đã có kiểm soát đúng hình dạng cần có trong DEV config hiện tại. Việc còn lại
> là xác nhận cấu hình VPS thật khớp với thiết kế trong repo (chưa ai xác nhận được — xem mục
> "Phụ thuộc chưa trả lời" cuối file) và một quyết định hiệu chỉnh nhỏ (mục ②).

## ① Cổng nào mở ra ngoài — [ĐO] đọc toàn văn `docker-compose.yml` (244 dòng) + grep 2 file override

**Nguyên tắc thiết kế tự khai ở đầu file (đã đọc, không suy diễn):** *"CHỈ service `caddy`
publish port ra host (80/443). backend/frontend/postgres không có `ports:` nào — không container
nào trong 3 service đó chạm được từ bên ngoài Docker."* Đối chiếu từng service:

| service | ports trong `docker-compose.yml` (base) | đọc được gì |
|---|---|---|
| `postgres` | `127.0.0.1:5432:5432` | chỉ loopback host — không phải 0.0.0.0 |
| `redis` | **không có khoá `ports:`** | chỉ mạng Docker nội bộ, gọi được bằng tên service từ container khác, không có cổng nào trên host |
| `backend` | **không có khoá `ports:`** | như trên — mọi traffic phải qua `caddy` |
| `frontend` | **không có khoá `ports:`** | như trên |
| `jaeger` | `127.0.0.1:16686:16686` | UI trace chỉ loopback |
| `caddy` | `80:80`, `443:443` | **DUY NHẤT** publish ra `0.0.0.0` — đúng thiết kế, đây là cửa vào có chủ đích của một reverse proxy công khai |
| `cloudflared` | `profiles: [...]`, không `ports:` nào | outbound-tunnel-only, mặc định TẮT (profile-gated), không dùng cho VPS |

**[ĐO] `docker-compose.do.yml`** (stack "đo", không phải stack live) — override CÒN CHẶT HƠN:
`ports: !override []` cho backend/redis/chroma/caddy/frontend — tức trong stack `do` không
service nào publish port nào ra host, kể cả `caddy`. Đây rõ ràng là một stack đo nội bộ, không
phải ứng viên cho VPS.

**[ĐO] `docker-compose.ttl-test.yml`** — remap `postgres` sang `127.0.0.1:55432`, `jaeger` sang
`127.0.0.1:56686`, `caddy` sang `8443:443` (giữ loopback-style cho hai cái đầu, đổi cổng caddy
để tránh đụng cổng 443 của stack thật đang chạy song song trên cùng máy — có chú thích tự giải
thích lý do bỏ hẳn cổng 80 trong file). Đây là stack TEST TTL, cũng không phải VPS.

**Chroma (vector store RAG) — trả lời câu PO-agent hỏi cụ thể:** không có service `chroma` riêng
nào trong `docker-compose.yml`. [ĐO] `grep -n "chroma" docker-compose.yml` → chỉ xuất hiện dưới
dạng **volume** (`chroma_data:/app/data/rag_index`) mount vào container `backend`. Nghĩa là
Chroma ở đây chạy **nhúng trong tiến trình backend** (thư viện, không phải service mạng riêng) —
không có cổng nào của Chroma tồn tại để mở hay đóng. Không suy diễn thêm — đã đọc trực tiếp
file, không có dòng `services: chroma:` nào trong cả 3 file compose.

**Phần tôi CHỨNG MINH được vs phần PHỤ THUỘC câu trả lời của PO thật (tách rõ theo yêu cầu):**
- ✅ Chứng minh được từ repo: THIẾT KẾ trong `docker-compose.yml` đúng nguyên tắc "chỉ caddy ra
  ngoài" — không có exception nào lọt qua khi đọc hết cả 3 file.
- ❌ KHÔNG chứng minh được từ repo: file compose nào THỰC SỰ chạy trên VPS thật, cách VPS mở
  firewall (có `ufw`/security-group nào chặn thêm không, hay để trần theo đúng docker-compose),
  và liệu người vận hành có tự thêm `-p 5432:5432` tay ngoài file khi debug rồi quên gỡ hay
  không — **không có dấu vết nào của việc này trong repo vì theo định nghĩa nó không nằm trong
  repo.** Đây là câu hỏi cho PO thật, đã từng nêu ở đánh giá checkpoint (`2026-08-20-danh-gia-
  kho-checkpoint-truoc-deploy-vps.md`) và vẫn CHƯA có câu trả lời — lặp lại ở đây theo đúng yêu
  cầu PO-agent.

## ② Thông báo lỗi có rò nội bộ không

**500 lỗi chưa bắt (mặc định FastAPI/Starlette khi `debug` không bật):** [ĐO]
`grep -n "debug=True\|uvicorn.run"` trên toàn `src/` và mọi file compose/Dockerfile → **0 kết
quả**. `app = FastAPI(...)` (`main.py:151-158`) không truyền `debug=` — mặc định `False`. Hành vi
mặc định của Starlette khi `debug=False`: lỗi chưa bắt trả JSON `{"detail":"Internal Server
Error"}`, không traceback, không tên file/module/thư viện.

**500 lỗi có bắt tay (duy nhất trong `src/api/main.py`) — `main.py:1169-1174`:** khối `except
Exception as exc` bọc quanh `scrub_pii(...)` (ADR-024, fail-closed khi scrub note duyệt/từ chối
hỏng) trả đúng `detail="Không xử lý được ghi chú — vui lòng thử lại"` — không có `str(exc)`, không
traceback, log chi tiết đi vào `_logger.error(...)` (nội bộ, không trả về client) chỉ kèm
`resolution_id`. Sạch.

**`require_role()` (`src/auth.py:298-310`) — 🟡 CÓ rò, nhưng rò gì cần định hạng đúng, không phải
"database/traceback":**
```
detail=f"Cần role thuộc {sorted(allowed_roles)}, tài khoản hiện tại là {current_user.role}"
```
Đây KHÔNG phải lỗi cùng loại với traceback/tên bảng/version thư viện — nó là **rò cấu trúc phân
quyền cho một người ĐÃ xác thực (JWT hợp lệ) nhưng sai role**, không phải cho người ngoài chưa
đăng nhập (route nào cũng qua `get_current_user` trước, 401 chặn ở lớp đó nếu không có JWT hợp
lệ — xem ③). Kịch bản khai thác thật: một tài khoản `cskh` gọi thẳng route `supervisor`-only
(vd `/resolutions/{id}/approve`) bằng Postman thay vì qua UI, nhận lại chính xác **role nào được
phép** + **role hiện tại của chính nó** — xác nhận cấu trúc phân quyền (route X cần role Y) mà
không cần đọc `contracts/authority-matrix.yaml`. Không rò thông tin của NGƯỜI KHÁC, không rò dữ
liệu giao dịch, chỉ rò "hình dạng của cánh cửa" cho người đã cầm một chìa (dù sai) đứng trước nó.

**Hai lựa chọn, không tự chọn thay — trình PO thật/Lead:**
- **(a) Giữ nguyên.** Lý do giữ: message này hiện là toàn bộ cơ chế debug cho CSKH/QA khi test
  phân quyền — đổi thành `"Không đủ quyền"` chung chung sẽ làm mọi ca lỗi 403 trong QA/log nhìn
  giống hệt nhau, khó soi khi có bug phân quyền thật. Rủi ro chấp nhận: một nhân viên `cskh` tò
  mò dò được bản đồ vai trò — nhưng `contracts/authority-matrix.yaml` vốn đã public trong repo
  (không phải bí mật), nên cái message này rò thêm chủ yếu là XÁC NHẬN xem role hiện tại của
  CHÍNH họ là gì, không phải thông tin mới với kẻ tấn công đã đọc contract.
- **(b) Làm nghèo message cho response ra CLIENT, giữ nguyên chi tiết ở log.** Trả
  `"Không đủ quyền cho thao tác này"` ra HTTP response, còn `_logger.warning(...)` với đầy đủ
  `allowed_roles`/`current_user.role` để debug nội bộ vẫn soi được qua log tập trung. Chi phí:
  một chỗ sửa (`src/auth.py:304-307`), không đụng test nào theo tôi thấy — `test_invariants.py`
  chỉ đọc `allowed_roles` qua introspect closure (không qua HTTP response), nên đổi message
  KHÔNG làm contract-test đỏ [chưa tự chạy pytest để xác nhận, nói đúng mức độ tôi kiểm — chỉ đọc
  code, chưa `pytest tests/test_invariants.py` sau khi sửa thử].

Không đạt mức "phải vá trước deploy" — cả (a) và (b) đều là lựa chọn an toàn để deploy, khác nhau
ở mức độ thận trọng.

## ③ Route không cần đăng nhập — bảng đầy đủ [ĐO] quét CHƯƠNG TRÌNH, không suy diễn từ tên route

**Phương pháp:** viết script Python đọc `src/api/main.py`, tìm mọi decorator
`@app.get/post/put/delete/websocket`, cắt thân hàm tới decorator kế tiếp, kiểm từng khối có chứa
`Depends(get_current_user|require_role|require_otp_verified)` hay không — quét TOÀN VĂN thân hàm,
không chỉ dòng `def`, vì signature nhiều route trải nhiều dòng.

**Kết quả — 31 route, đúng 3 route KHÔNG có Depends xác thực:**

| route | vì sao đúng là public |
|---|---|
| `POST /auth/login` | phát hành token — theo định nghĩa phải gọi được trước khi có token. Có `_login_ip_limiter` (rate-limit theo IP) chặn brute-force. |
| `POST /auth/refresh` | tự xác thực bằng CHÍNH refresh token trong body (`rotate_refresh_token(req.refresh_token)`), 401 nếu "không hợp lệ, đã hết hạn, hoặc đã bị thu hồi" — không phải "không kiểm gì", chỉ là cơ chế xác thực khác `get_current_user`. Có `@limiter.limit("30/minute")`. |
| `GET /health` | liveness, tự khai CỐ Ý không chạm DB/Redis (đúng chuẩn 12-factor: liveness ≠ readiness — khớp `production-packaging-checklist.md` giai đoạn 1). Trả `env`, `db_kind`, `db_name`, `build_src_hash`, `build_commit` — **không host/user/mật khẩu**, tự khai rõ trong docstring lý do an toàn để public. |

**28 route còn lại — toàn bộ đều có ít nhất một trong ba Depends xác thực**, bao gồm mọi route
`/tools/*`, `/tickets/*`, `/resolutions/*`, `/policy-*`, `/live-chat/*`, `/agent/chat`,
`/reports/summary`. Không tìm thấy route nào lọt lưới.

**`/docs`, `/redoc`, `/openapi.json` — câu hỏi cụ thể PO-agent nêu:** [ĐO] `main.py:151-158`:
```python
_LA_PROD = APP_ENV == "production"
app = FastAPI(
    ...
    docs_url=None if _LA_PROD else "/docs",
    redoc_url=None if _LA_PROD else "/redoc",
    openapi_url=None if _LA_PROD else "/openapi.json",
)
```
**Đã tắt khi `APP_ENV=production`** (biến này đặt `APP_ENV=production` sẵn trong
`.env.production.example:69`, tức đúng luồng deploy tay VPS sẽ đặt nó). Có chú thích ngay phía
trên [ĐO trước đó, đã từng đo trong container] ghi lại: `/openapi.json` khi mở trả **200, 28.470
byte, 31 path** — tức phơi TOÀN BỘ bản đồ API + schema tham số nếu quên tắt. Comment giải thích rõ
lý do KHÔNG tắt cứng mà gate theo môi trường (dev cần `/docs` để làm việc), và xác nhận
`test_invariants.py` (`INV-00`) đã cố ý bỏ qua 3 tiền tố này để việc route xuất hiện/biến mất
theo môi trường không làm cổng contract đỏ.

**🔴 Một điểm CẦN xác nhận, không phải lỗi nhưng là phụ thuộc chưa kiểm:** kiểm soát này chỉ có
hiệu lực NẾU biến môi trường `APP_ENV` thực sự được set thành `production` trên VPS thật.
`src/config.py:71`: `APP_ENV = os.environ.get("APP_ENV", "development")` — **mặc định là
`development`** nếu ai đó quên set biến này khi deploy. Nghĩa là: thiếu MỘT dòng `APP_ENV=production`
trong `.env` thật trên VPS ⟹ `/docs`+`/openapi.json`+`/redoc` TỰ ĐỘNG BẬT LẠI, im lặng, không có
cảnh báo nào từ ứng dụng (khác với `JWT_SECRET_KEY`/`FIELD_ENCRYPTION_KEY` vốn fail-fast khi
thiếu). `.env.production.example` đã có sẵn dòng này với giá trị đúng — rủi ro chỉ là người điền
tay bỏ sót đúng MỘT dòng không có gì nhắc.

## ④ Secret trong ảnh/log lúc khởi động, và độ thật của placeholder `.env.example`

**Log lúc khởi động — [ĐO] đọc cả 3 khối `@app.on_event("startup")`:**
1. `_khai_ma_nguon_lech_anh` — chỉ log HASH mã nguồn (`bam_luc_dung`, `bam_dang_chay`) khi lệch,
   không log giá trị bí mật nào.
2. `_khai_khoang_trong_kenh_ho_tro` — log `HOTLINE_CSKH` dạng raw (`gia_tri_tho`) khi thiếu/hỏng —
   **đây KHÔNG phải bí mật**, là số tổng đài công khai cho khách, tự khai rõ trong docstring vì
   sao route/field này khác `JWT_SECRET_KEY` (không cần fail-fast, không nhạy cảm).
3. `_khoi_dong_fanout_live_chat` — khởi động vòng lặp nền, không log giá trị cấu hình nào.

**[ĐO] `grep -rn "logger\.\(info\|warning\|error\)(.*\(config\|settings\|os\.environ\|vars(\)" src/`
→ 0 kết quả** — không có chỗ nào dump nguyên object config/settings/environ ra log.

**`api_key=` LLM client — đã đo trước đó (file `2026-08-19-gd3-tiep-tuc-key-trong-log-va-free-
quota.md`, còn đúng, không đổi):** đúng 2 chỗ chạm `LLM_API_KEY` trong `graph.py` — import và
MỘT lần dùng làm tham số constructor `ChatOpenAI(api_key=...)`, không đường thứ hai vào log/dict.
Không đo lại từ đầu ở đây — trỏ tới file gốc theo đúng quy ước "đừng lặp, chỉ tóm tắt + trỏ".

**`.env.example` (dev) — độ thật của placeholder:** [ĐO] đọc toàn văn. Không giá trị nào ở dạng
"trông như thật":
- `POSTGRES_PASSWORD=doi-gia-tri-nay-truoc-khi-dung-that` — chữ nghĩa TỰ NÓI "đổi giá trị này
  trước khi dùng thật", không thể nhầm là giá trị thật.
- `JWT_SECRET_KEY=`, `FIELD_ENCRYPTION_KEY=` — **rỗng**, kèm lệnh sinh giá trị ngay dòng trên —
  app fail-fast nếu deploy nguyên xi (đúng nguyên tắc "secret không có default" ở
  `production-packaging-checklist.md` GĐ1).
- `OPENAI_API_KEY=sk-...` — định dạng placeholder rõ ràng (`sk-...`), không phải một khoá thật bị
  che một phần, không parse được thành khoá hợp lệ.

**`.env.production.example` — cùng kiểm, nghiêm ngặt hơn vì đây là file dùng thật cho VPS:** [ĐO]
đọc toàn văn. Toàn bộ giá trị bắt buộc dùng cú pháp `<mo-ta-trong-dau-ngoac-nhon>` (vd
`DATABASE_URL=postgresql+psycopg2://<user>:<pass>@<host>:5432/<db>`,
`LLM_API_KEY=<key-production-that>`) — **không một dòng nào trông như giá trị thật**, và quan
trọng hơn: dạng `<...>` sẽ FAIL NGAY (DNS không resolve `<host>`, không phải "chạy sai âm thầm")
nếu ai đó quên điền rồi chạy nguyên xi — khác hẳn kịch bản nguy hiểm thật (placeholder ĐỦ GIỐNG
thật để chạy được nhưng sai, kiểu `localhost`/`changeme` hợp lệ cú pháp). File này còn có sẵn 3
dòng cảnh báo tự khai (KHÔNG copy `.env` dev sang đây; KHÔNG commit `.env` thật; key production
KHÔNG BAO GIỜ qua phiên Claude nào) — khớp đúng chính sách (B) đã chốt ở GĐ3
(`2026-08-19-gd3-tiep-tuc-key-trong-log-va-free-quota.md` mục 2).

**Kết luận ④:** sạch, không có phát hiện cần vá.

## Tổng kết — không phát hiện nào ở mức "không được deploy trước khi vá"

| # | đường | kết quả | hành động |
|---|---|---|---|
| ① | cổng | thiết kế đúng ("chỉ caddy ra ngoài"), Chroma là thư viện nhúng không phải service mạng | không cần vá; **chờ PO thật xác nhận VPS thật khớp thiết kế** |
| ② | lỗi rò | 500 sạch; `require_role()` rò cấu trúc phân quyền cho người ĐÃ xác thực sai role (không phải traceback/dữ liệu khách) | 2 lựa chọn (a)/(b) trình PO thật/Lead, không tự chọn |
| ③ | route public | đúng 3/31 route public, cả 3 đều hợp lý; `/docs` đã gate theo `APP_ENV` | 🟡 xác nhận `.env` VPS thật CÓ dòng `APP_ENV=production` — thiếu nó thì `/docs` tự bật lại im lặng |
| ④ | secret log/placeholder | sạch cả log khởi động lẫn 2 file `.env*.example` | không cần vá |

## Phụ thuộc chưa trả lời (nhắc lại theo yêu cầu PO-agent, không phải phát hiện mới)

Cả ①③ đều có một chân phụ thuộc cấu hình VPS thật mà tôi không có quyền/khả năng kiểm (đúng giới
hạn "không đụng `app.adaptivealgo.uk`"):
1. File compose nào thực sự chạy trên VPS, và VPS có mở firewall/security-group nào ngoài những
   gì `docker-compose.yml` khai không.
2. `.env` thật trên VPS có dòng `APP_ENV=production` hay bị bỏ sót (mặc định code là
   `development` nếu thiếu — im lặng bật lại `/docs`).

Đề nghị cụ thể, không phải câu hỏi mở: khi PO thật deploy, chạy đúng MỘT lệnh xác nhận sau khi
lên VPS thật (không phải đoán) —
```bash
curl -s https://<domain-that>/openapi.json -o /dev/null -w "%{http_code}\n"   # kỳ vọng: 404 hoặc tương tự "not found", KHÔNG phải 200
curl -s https://<domain-that>/health | grep -o '"env":"[^"]*"'               # kỳ vọng: "env":"production"
```
Hai lệnh trên là smoke-test đúng tinh thần GĐ6 checklist đóng gói (`production-packaging-
checklist.md`) — xác nhận bằng công cụ đo khách quan, không suy luận từ code tĩnh.
