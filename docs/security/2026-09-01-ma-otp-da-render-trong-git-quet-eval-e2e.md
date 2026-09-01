# Mã OTP đã render nằm trong `eval/`/`frontend/e2e/` — quét theo yêu cầu PO (01/09)

> Vai: `security`. Chỉ đọc (`git grep`, `git show HEAD:...`, xem lại ảnh bằng Read tool) — **KHÔNG sửa
> gì trong `eval/`**, kể cả 4 tệp đang tranh chấp (§0b.19e). Việc vá xếp SAU buổi quay, theo đúng lệnh.

## Vì sao quét: lớp rủi ro cả đội đang canh nhầm một nửa

Cả ngày lo "đừng để 6 số OTP lên hình quay video" — có quy trình 3 lượt soát, có người xem lại. Nhưng
hiện vật kiểm thử (`eval/results/*.json`, `*.png` từ Playwright) cũng ghi lại đúng loại dữ liệu đó, và
khác video ở một điểm quyết định: **hiện vật này VÀO GIT, Ở LẠI VĨNH VIỄN trong lịch sử, ai `git clone`
cũng đọc được** — không ai từng soát nó bằng quy trình nào cả.

## Kết quả quét

**Phạm vi:** `git grep` toàn bộ `eval/**` + `frontend/e2e/**` (working tree hiện tại, tức bao gồm cả
nội dung đã commit) tìm mẫu `OTP[^0-9]{0,40}[0-9]{6}` (số 6 chữ số gần chữ OTP) và `"Mã OTP...: NNNNNN"`
+ xem lại trực tiếp các ảnh `.png` liên quan bằng Read tool (không chỉ tin tên file).

**4 hiện vật CÓ mã OTP đã render thật, cả 4 đều ĐÃ COMMIT (không phải chỉ nằm ở working tree):**

| # | Tệp | Commit | Mã OTP lộ ra | Dạng |
|---|---|---|---|---|
| 1 | `eval/results/render_that_mobile_25aug.png` | `db7a488` | **556569** | Ảnh — nhìn thấy trực tiếp 6 ô số trên khung hình (đã xem lại bằng Read tool, không suy luận từ tên file) |
| 2 | `eval/results/render_that_mobile_25aug_SAU_VA.png` | `1a6eff1` | **198852** | Ảnh — cùng cách kiểm, cùng kết quả nhìn thấy trực tiếp |
| 3 | `eval/results/render_that_so_sanh_25aug.json` | `db7a488` | **923350** | Text — dòng `"Mã OTP phiên làm việc (mô phỏng — gửi tới 0974000145): 923350"` |
| 4 | `eval/results/render_that_so_sanh_25aug_SAU_VA.json` | `1a6eff1` | **574256** | Text — cùng dạng dòng. **Lưu ý:** bản working-tree hiện tại (chưa commit, thuộc §0b.19e đang tranh chấp) đã đổi thành `831051` — một mã THỨ NĂM, xác nhận đây là hiện tượng LẶP LẠI mỗi lần chạy lại spec, không phải sự cố một lần |

4 mã đều KHÁC NHAU → xác nhận đây là OTP thật được sinh ra tại thời điểm chạy test (không phải placeholder cố định), bị Playwright chụp/dump lại nguyên văn rồi commit thẳng vào git.

**1 nghi vấn kiểm tra, kết luận KHÔNG phải OTP (false positive, ghi lại để khỏi ai đo lại):**
`eval/results/golden_run_20260810_032309_raw.json:562` — chuỗi `"...chưa từng đưa OTP cho ai, giao dịch
này là TXN20260609000001..."` — số 6 chữ số khớp mẫu regex là MÃ GIAO DỊCH (TXN), không phải OTP. Đọc
nguyên câu xác nhận: khách đang nói KHÔNG đưa OTP cho ai, không phải một mã đang bị lộ.

**Không tìm thấy:** token/JWT (`eyJ...`), `access_token`/`refresh_token` có giá trị thật nào trong
`eval/**`/`frontend/e2e/**`. Playwright trace/report (`playwright-report/`, `test-results/`, `*.zip`)
không nằm trong git (`git ls-files` → 0 kết quả) — không phải nguồn rò rỉ.

Mật khẩu `Demo@123` xuất hiện nhiều trong `eval/*.py`/`*.md`/`frontend/e2e/helpers/actors.ts` — nhưng
đây là **credential cố định của tài khoản demo dùng để script tự đăng nhập** (đã biết, đã tài liệu hoá
công khai ngay trên UI đăng nhập — xem ảnh `eval/results/2026-08-28-p4-cskh-401-quicklogin.png`, có
dòng "4 tài khoản test dùng chung mật khẩu Demo@123"), khác về BẢN CHẤT với OTP: mật khẩu demo là hằng
số biết trước, công khai có chủ đích; OTP là bí mật *sinh ra tại thời điểm chạy*, đúng ra không nên bị
ghi lại vĩnh viễn. Không xếp cùng loại rủi ro với 4 hiện vật OTP ở trên.

## Đánh giá mức độ — THẤP, đúng khung PO đã dùng cho commit `48a562f`

Cùng lý do PO đã niêm cho phát hiện trước: cả 4 hiện vật đều dùng số điện thoại `0974000145` (tài
khoản demo `USR-0145`, dữ liệu sinh tổng hợp), sinh ra dưới `OTP_DEMO_MODE` phục vụ test render, đã hết
hạn từ lâu (OTP phiên có `OTP_VIEW_MAX_MINUTES` hữu hạn — xem `src/config.py:215` — các mã này sinh
ngày 25/08, giờ đã 01/09, chắc chắn hết hạn), không phải OTP của giao dịch thật hay khách hàng thật.

**Khác video ở một điểm — đây KHÔNG phải sự cố một lần, mà là MẪU HÌNH sẽ LẶP LẠI:** cả 4 hiện vật đều
đến từ cùng một spec (`frontend/e2e/kich-ban-chuyen-gia-render-that.spec.ts`, theo xác nhận của PO ở
STATE.md §0b.19e) chạy nhiều lần (25/08 gốc, 25/08 SAU VÁ, và lại một lần nữa 31/08 23:33 — mỗi lần một
mã OTP mới). **Nếu spec này còn tồn tại và còn được chạy + commit kết quả**, lần chạy TIẾP THEO chắc
chắn sẽ tạo thêm một hiện vật OTP mới trong git — kể cả sau khi dọn 4 tệp hiện tại. Đây là lỗ CẤU TRÚC,
không phải lỗ ở 4 tệp cụ thể.

## Cập nhật 01/09 (sau khi Lead relay PO đo tiếp) — spec chạy MẶC ĐỊNH, tự kiểm lại từng vế trước khi ghi

**Tự đo lại, không chép nguyên claim của peer:**

- `frontend/playwright.config.ts:30` — `testIgnore: /live-chat\.spec\.ts/` — **XÁC NHẬN ĐÚNG**, chỉ
  loại `live-chat.spec.ts`. `kich-ban-chuyen-gia-render-that.spec.ts` KHÔNG bị loại → chạy mỗi khi ai
  gõ `npx playwright test` không tham số, không cần cố ý nhắm đúng spec này.
- `.github/workflows/ci.yml` job `e2e-playwright-nightly` (dòng ~724) — **XÁC NHẬN ĐÚNG**: điều kiện
  `if: github.event_name == 'schedule' || 'workflow_dispatch'`, bước cuối chạy đúng
  `npx --prefix frontend playwright test` (dùng config mặc định, không lọc riêng nhóm AUTH-* dù comment
  cạnh đó ghi vậy) → spec render-that CHẠY THẬT mỗi đêm trên máy chủ CI.
- `frontend/e2e/kich-ban-chuyen-gia-render-that.spec.ts` — đọc trực tiếp: dòng 108-109/160/209 ghi
  CỨNG đường dẫn `../../eval/results/render_that_*_SAU_VA.{json,png}` bằng `fs.writeFileSync`/
  `page.screenshot`, không có bất kỳ điều kiện `OTP_DEMO_MODE`/seed-account nào bọc quanh (grep
  `OTP_DEMO_MODE|seed|USR-0145` trong file → chỉ có `CUSTOMER_PHONE = "0974000145"` hardcode, không có
  guard).

**🔴 Một chỗ cần ĐÍNH CHÍNH so với cách Lead thuật lại — đã tự kiểm bằng `grep "git commit\|git push"
.github/workflows/ci.yml` → 0 kết quả:** CI **KHÔNG tự commit** hiện vật vào git. Job
`e2e-playwright-nightly` chỉ `actions/upload-artifact` đúng thư mục `frontend/playwright-report/`
(báo cáo HTML riêng của Playwright) — khác hẳn `eval/results/`, và artifact CI là lưu trữ tạm gắn với
lần chạy (ephemeral), không phải commit vào lịch sử git. Nghĩa là: mỗi đêm CI CÓ sinh một mã OTP mới
ghi ra đĩa **trên máy chủ CI** (rủi ro thật nhưng ở phạm vi hẹp hơn — mất theo vòng đời runner, không
tự động vào git) — còn cơ chế biến nó thành VĨNH VIỄN trong git vẫn là bước NGƯỜI tự làm sau đó (`git
add`/commit trên máy cá nhân, đúng như 4 tệp gốc của §0b.19e). Không đổi kết luận severity hay hướng
sửa PO đề xuất — chỉ tách rõ HAI cơ chế khác nhau (sinh ra ↔️ đi vào git) để không sửa nhầm chỗ.

**Xác nhận đúng, không đổi:**

- ① Giải đúng bí ẩn §0b.19e — không ai "chạy phép đo render" có chủ đích; chạy bộ e2e bình thường
  (`npx playwright test`, không tham số) tạo ra 4 tệp này như TÁC DỤNG PHỤ không ai biết trước, khớp cả
  4 người phủ nhận thành thật.
- ② Severity THẤP là do **HOÀN CẢNH** (số điện thoại demo, `OTP_DEMO_MODE`, mã đã hết hạn), **KHÔNG
  PHẢI do THIẾT KẾ** — đã tự xác nhận spec không hề kiểm `OTP_DEMO_MODE` hay xác nhận tài khoản là seed
  trước khi ghi hiện vật. Chạy đúng đoạn mã này nhắm vào một cấu hình/tài khoản khác (không phải seed)
  sẽ commit một mã OTP THẬT, không có gì trong code chặn lại.
- ③ Che ô OTP khi chụp/dump (đề xuất ban đầu của tôi) chỉ chữa NỘI DUNG hiện tại, không chặn được chu
  kỳ lặp — mỗi lần chạy vẫn ghi đè `eval/results/render_that_*_SAU_VA.*`, ai đó `git add` là lại vào
  git. Sửa CƠ CHẾ đúng hơn: đổi đường dẫn ghi ra ngoài repo (thư mục tạm) hoặc thêm 3 tên tệp
  `render_that_*_SAU_VA.*` vào `.gitignore` — khi đó dù CI/local chạy bao nhiêu lần, hiện vật không còn
  ĐƯỜNG nào vào git nữa, không phụ thuộc người chạy có nhớ che ô hay không.

## Việc thuộc vai khác, không phải tôi tự sửa — ghi lại để không ai đo lại từ đầu

- Dọn/rotate 4 hiện vật đã commit — **KHÔNG LÀM TRƯỚC BUỔI QUAY**, đụng đúng 4 tệp trong §0b.19e đang
  tranh chấp. Sau buổi quay, thuộc `tester` (chủ `frontend/e2e/`, `eval/`).
- Sửa CƠ CHẾ (ưu tiên hơn che nội dung, xem mục cập nhật 01/09 ở trên): đổi đường ghi hiện vật của
  `kich-ban-chuyen-gia-render-that.spec.ts` ra thư mục NGOÀI repo, hoặc thêm
  `eval/results/render_that_*_SAU_VA.*` vào `.gitignore` — chặn ĐƯỜNG vào git thay vì trông chờ người
  chạy nhớ che ô OTP mỗi lần. Việc code, thuộc `tester`/`tech-lead`, không phải `security` tự sửa.
- Vì các mã đã hết hạn và dữ liệu là seed, KHÔNG cần hành động khẩn (không phải OTP thật, không có
  giao dịch thật đứng sau) — nhưng nên xếp vào backlog "trước khi chạy spec này trên dữ liệu THẬT" nếu
  tương lai project đổi sang môi trường có dữ liệu thật, để không lặp lại đúng lỗ này ở mức nghiêm
  trọng hơn hẳn.
