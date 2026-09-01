# Cổng nghiệm thu đỏ-trước/xanh-sau — `bdaf17e` + `5ff93b8`, 31/08/2026

> Vai: `security`. Giao từ Lead (`p-226-61`) — `docs/STATE.md:51-52` ghi nợ cổng này, đang chặn mọi
> câu "đạt SCA/PSD2/AAL2" trong tài liệu đối ngoại. Cơ khí (dựng worktree/build/chạy) một phần tự
> làm, một phần đối chiếu với kết quả độc lập của Coder (`p-226-1c`) — tôi tự thẩm định trước khi
> đưa vào kết luận dưới đây, không nhận nguyên số thô của họ (đúng phân vai PO chốt).
>
> 🔴 **Kết luận ở đây đứng ĐỘC LẬP với điểm số golden benchmark** — theo đúng cảnh báo của Lead:
> `run_golden_set.py` tự khai không đo được tầng xác thực/OTP/JWT/rate-limit (dùng sentinel
> `_ALWAYS_FRESH`, bỏ qua các tầng đó). Hai luồng bằng chứng không được ghép.
>
> 🟢 **NIÊM 31/08, cuối đêm:** đội phát hiện bộ mô phỏng nhiều lượt của golden hồi quy hạ tầng
> (chết im lặng ~14-25/08), chỉ ~8/120 ca đo được thật — golden đêm nay KHÔNG chạy. **Hai gate ở
> file này không liên quan gì tới lỗi mô phỏng golden**: cả hai đo bằng `pytest`/`TestClient` trực
> tiếp trên worktree biệt lập, không đi qua `run_golden_set.py` hay bất kỳ mô phỏng nhiều lượt nào.
> Đọc file này KHÔNG được suy ra "cả đêm nay hỏng hết" — hai gate + phiếu dữ liệu
> (`2026-08-31-du-lieu-khach-hang-di-dau.md`) là phần việc đứng vững, tách biệt hoàn toàn.

## Phương pháp — ngoài cây làm việc chính, không chạm state dùng chung

```
git worktree add <scratch>/wt-red-bdaf17e    2a915db     # NGAY TRƯỚC bdaf17e
git worktree add <scratch>/wt-green-bdaf17e  bdaf17e
git worktree add <scratch>/wt-green-5ff93b8  5ff93b8      # = HEAD hiện tại lúc đo
```
Build `docker build --target builder` từng worktree (stage có đủ pytest + deps, không cần chạy full
compose vì test dùng `TestClient` + `sample_db` fixture, không cần Postgres/Redis thật —
`REDIS_URL=fake://ci`). Chạy bằng mount `-v <worktree>:/app` lên image đã build (tránh build lại khi
chỉnh sửa test giữa chừng). Không `git checkout`/`stash`/`clean` trên cây chính ở bất kỳ bước nào.

## Gate 1 — `bdaf17e` (gỡ `otp_code` khỏi response + `verify_otp` constant-time)

**Test dùng:** `tests/test_api/test_otp_demo_mode_khong_lo_otp_code.py` — đã tồn tại trong cây làm
việc (viết bởi tester, **chưa commit**), copy sang cả hai worktree để chạy được.

```
[ĐO 31/08, security, tự chạy]
RED   (2a915db, TRƯỚC vá):  2 ERROR
      AttributeError: <module 'src.api.main'> has no attribute 'OTP_DEMO_MODE'
      (cả 2 ca: test_auth_otp_request_khong_co_otp_code_khi_demo_tat,
       test_resolution_approval_otp_khong_co_otp_code_khi_demo_tat)
GREEN (bdaf17e, SAU vá):    2 passed, 24 warnings (toàn DeprecationWarning datetime.utcnow(),
                             không liên quan tới gate này)
```

**Đối chiếu độc lập:** Coder (`p-226-1c`) tự dựng và chạy riêng, báo **cùng kết quả từng chữ**
(2 ERROR → 2 passed, cùng thông điệp lỗi). Hai nguồn độc lập khớp nhau — đúng Luật ② của dự án.

**Đọc kết quả:** ERROR (không phải FAIL thường) là tín hiệu ĐỎ *mạnh hơn* một assertion fail — code
cũ không có khái niệm `OTP_DEMO_MODE`, nên không có cách nào để test này "tình cờ" pass trên code cũ.
Đây là bằng chứng đỏ-đúng-chỗ: nếu ai revert `bdaf17e`, gate này báo lỗi ngay, không im lặng.

## Gate 2 — `5ff93b8` (ADR-055 Bậc 1 — `require_token_chua_thu_hoi` trên 3 route)

**Test dùng:** 🔴 **KHÔNG có test chính thức nào tồn tại** cho hành vi này — tôi và Coder độc lập tìm
khắp `tests/` (`grep -rl "require_token_chua_thu_hoi"`) đều ra rỗng. Đây là gap tester đã được nêu
trong phân tích tác động gửi Lead trước đó, **vẫn chưa ai viết tính tới giờ đo**.

Vì gate không có sẵn nhưng Lead cần bằng chứng ngay, tôi viết một **script AUDIT tạm thời** (KHÔNG
commit vào `tests/` — vùng đó thuộc tester theo `CLAUDE.md §4`, tôi không có quyền ghi), theo đúng
mẫu đã có sẵn trong repo (`test_logout_revokes_current_access_token_for_sensitive_routes`,
`tests/test_api/test_auth_jwt_refresh.py`): login → logout (thu hồi access token cũ) → gọi route
bằng token CŨ → kỳ vọng 401/403.

```
[ĐO 31/08, security, tự viết + tự chạy — KHÔNG phải test chính thức của tester]
RED   (bdaf17e, TRƯỚC 5ff93b8):  3 FAILED — cả 3 route trả 200 OK với token đã thu hồi
      test_audit_propose_resolution:      200, tạo được resolution_id=RES-752998bd0673
      test_audit_escalate_ticket:         200, tạo được escalation_id=ESC-f75e21f026d8
      test_audit_request_approval_otp:    200, tạo được session_id=SES-80bb2de5ff9e
      ⟹ Token bị thu hồi (đăng xuất) VẪN dùng được cho cả 3 route — đúng lỗ hổng ADR-055 mô tả,
        chứng minh được bằng dữ liệu thật tạo ra, không phải suy luận từ đọc code.

GREEN (5ff93b8):                  3 passed — cả 3 route trả 401/403 đúng như kỳ vọng
```

**Đối chiếu độc lập (Coder):** Coder chạy `tests/test_invariants.py` (23 test ràng buộc cứng) trên
cả hai trạng thái — **23 passed cả hai phía, không đổi**. Đây LÀ đúng như kỳ vọng theo phân tích tác
động (Depends độc lập, không nằm trong closure `require_role()`, không đổi `allowed_roles` nào) —
**nhưng đây KHÔNG PHẢI bằng chứng cho hành vi ADR-055 hoạt động đúng**, chỉ là bằng chứng "không phá
gì khác". Hai loại bằng chứng khác nhau, không được gộp khi báo cáo.

## ⚠️ Giới hạn phải khai — đọc trước khi dùng cổng này để nói "đã nghiệm thu"

1. **Gate 1** dùng test CỦA TESTER (dù chưa commit) — đủ tư cách làm cổng nghiệm thu chính thức MỘT
   KHI được commit.
2. **Gate 2** dùng script AUDIT của TÔI (security), không phải test chính thức. Nó **chứng minh được
   hành vi đúng tại thời điểm đo (31/08)**, nhưng KHÔNG thay thế được việc tester viết test committed
   vào `tests/` — thiếu bước đó thì gate 2 không tự động chạy lại ở CI, không bảo vệ được về sau nếu
   ai vô tình gỡ `require_token_chua_thu_hoi` khỏi 1 trong 3 route. Đây đúng dạng "bảo vệ IM LẶNG"
   mà chính ADR-055 đã cảnh báo (rút phép kiểm ⟹ không test nào đỏ) — script tạm của tôi không đóng
   được lỗ đó, chỉ tester viết test thường trực mới đóng được.
3. Cả hai gate chỉ đo trên **code tĩnh trong worktree**, không phải trên bất kỳ ngăn Docker compose
   nào đang chạy — không nói được gì về production hay các ngăn demo hiện có.
4. Script audit của gate 2 hiện nằm ở `<scratch>/wt-*/tests/test_api/zz_audit_5ff93b8.py` (2 bản
   sao, cả hai worktree) và bản gốc tại
   `<scratch>/audit_5ff93b8_require_token_chua_thu_hoi.py` — KHÔNG nằm trong repo chính, sẽ mất khi
   dọn scratch. Nếu tester muốn dùng làm điểm khởi đầu viết test chính thức, nội dung available theo
   yêu cầu.

## Việc còn cần — chuyển tester (không phải chờ security, việc rẻ)

**Gate 2 cần một test CHÍNH THỨC, committed vào `tests/test_api/`**, cùng kịch bản đã chứng minh ở
trên (login → logout → gọi route bằng token cũ → 401/403), cho cả 3 route
`propose_resolution`/`escalate_ticket`/`request-approval-otp`. Tôi không tự viết vào `tests/` vì
ngoài vùng ghi của `security` (`CLAUDE.md §4`) — đây là bàn giao, không phải tôi từ chối làm.

## Kết luận cho Lead — dùng để mở khoá ngôn từ đối ngoại

- **Gate 1 (`bdaf17e`) — ĐẠT, có bằng chứng đỏ-trước/xanh-sau, đối chiếu độc lập khớp.**
- **Gate 2 (`5ff93b8`) — ĐẠT về mặt HÀNH VI (đo được thật, đối chiếu độc lập một phần), nhưng CHƯA
  ĐẠT về mặt CỔNG THƯỜNG TRỰC** (thiếu test committed) — dùng được để mở khoá câu tuân thủ CHO TỚI
  THỜI ĐIỂM ĐO (31/08), nhưng không tự bảo vệ về sau nếu không có test chính thức. Khuyến nghị: gắn
  điều kiện "committed test cho gate 2 xong trong vòng N ngày" nếu muốn dùng câu tuân thủ ở tài liệu
  sống lâu hơn một lần pitch.
