# FIN-05 "Sen" — Báo cáo QA đã đối chiếu lại với code thật (2026-08-11)

**Đối chiếu bởi:** Claude (phiên làm việc trực tiếp trên repo `P-121-new`, có quyền đọc/sửa toàn bộ code)
**Tài liệu gốc:** [`FIN05-QA-Test-Report.md`](FIN05-QA-Test-Report.md) — viết bởi 1 phiên Claude khác đóng vai khách hàng test tay qua trình duyệt, KHÔNG có quyền truy cập trực tiếp code
**Phương pháp:** Không suy luận từ đọc báo cáo cũ — mọi kết luận dưới đây đều verify lại bằng 1 trong 3 cách: (a) đọc trực tiếp code hiện tại, (b) chạy Playwright thật (repro có kiểm soát), (c) chạy curl trực tiếp vào backend thật đang sống ở `:8010`/`:3000`.

---

## 0. Tóm tắt

| Hạng mục | Kết luận |
|---|---|
| BUG-01 (login treo vô hạn) | **KHÔNG tái hiện được** trên môi trường hiện tại, nhưng code review lộ ra gap thật (không có timeout) — đã sửa + có test tự động |
| BUG-02 (submit rỗng im lặng) | **False positive** — HTML5 `required` đã chặn đúng, chỉ là tool test trước không "thấy" được popup validation native của trình duyệt |
| §3.1–3.7 checklist (~50 case) | Đại đa số đã có test tự động sẵn (golden_set/adversarial_set/test_authz_matrix/AUTH-* Playwright) — báo cáo gốc viết TRƯỚC KHI biết các hạ tầng này tồn tại. 1 mảng thật sự thiếu: **§3.6 UX/Accessibility** — đã bổ sung toàn bộ. |
| Thuật ngữ lạc hậu | "8 quyết định thiết kế" → thật ra là 6 ràng buộc; "Tầng A/B gian lận" → thật ra chỉ còn 1 tín hiệu `FS-06` duy nhất (đã sửa ở nhiều đợt trước, báo cáo gốc dùng thuật ngữ từ PRD bản cũ) |
| Phát hiện MỚI thật trong đợt này | 2 lỗi tương phản màu (WCAG AA) + 1 nút không có `aria-label` — cả 3 đã sửa, có test `axe-core` chặn tái phát |
| Test tự động thêm | 12 test Playwright mới (`login.spec.ts` ×2, `accessibility.spec.ts` ×10) |

---

## 1. BUG-01 — Điều tra lại chi tiết

**Repro sạch (không tái hiện được):**
```
login("0851000021", "customer") → curl trực tiếp /auth/login: 200, 9ms
login qua BFF /api/session: 200, 16ms
login qua Playwright (browser thật): vào /chat trong 5.5s, 0 console error
```
`0851000021` (USR-0021, "Huỳnh Thị Chi") **có thật** trong dataset — không phải do SĐT không tồn tại như báo cáo gốc phỏng đoán.

**Nhưng review code lộ ra gap thật:** `frontend/src/app/login/page.tsx`'s `handleSubmit()` gọi `fetch()` **không có timeout nào** — nếu request thật sự treo (mạng, backend đơ), `finally { setLoading(false) }` không bao giờ chạy vì `fetch()` promise không bao giờ settle. Đây chính xác là kịch bản báo cáo mô tả, dù không tái hiện được TẠI THỜI ĐIỂM SỬA (môi trường ổn định lúc đó).

Đào sâu hơn: gap này **không chỉ ở login** — hàm `request<T>()` dùng chung cho MỌI API call phía client (`frontend/src/lib/api.ts`, dùng bởi `agentChat`, `approveResolution`, `getCustomerHistory`...) và `backendFetch()` (`frontend/src/lib/server-api.ts`, tầng BFF→FastAPI) **đều cùng gap**.

**Đã sửa (3 điểm, dùng `AbortController`):**
1. `login/page.tsx` — timeout 10s, thông báo "Máy chủ phản hồi quá lâu (>10s) — thử lại giúp mình nhé."
2. `lib/api.ts::request()`/`uploadFile()` — timeout mặc định **60s** (không phải 10s như login — `agentChat` gọi LLM thật, đã đo thực tế có lượt cần 15-20s+ khi tải cao, timeout ngắn sẽ huỷ nhầm request đang chạy đúng).
3. `lib/server-api.ts::backendFetch()` — timeout 65s (hơi rộng hơn phía trình duyệt, chỉ là lưới an toàn tài nguyên phía server).

**Test tự động:** `frontend/e2e/login.spec.ts::"BUG-01"` — chặn `/api/session` bằng `page.route()` không bao giờ fulfill (mô phỏng treo thật), assert lỗi rõ ràng xuất hiện trong 13s và nút không còn kẹt "Đang đăng nhập…".

## 2. BUG-02 — Kết luận: không phải bug thật

Repro qua Playwright: submit form rỗng → `checkValidity()` = `false`, `validationMessage` = `"Please fill out this field."`, **0 network request** tới `/api/session`. Input có `required` (HTML5) — browser chặn submit NGAY TRƯỚC KHI `handleSubmit()` chạy, đúng hành vi mong muốn.

Tool test tay trước đó nhiều khả năng không "nhìn thấy" popup validation native của trình duyệt (hạn chế phổ biến của công cụ chụp màn hình/scrape DOM tự động, không phải giả lập tương tác người dùng thật qua bàn phím/chuột). **Không sửa code** (đã đúng) — chỉ thêm test `frontend/e2e/login.spec.ts::"BUG-02"` để khẳng định hành vi đúng và chặn regression nếu sau này ai đó lỡ bỏ `required`.

## 3. Đối chiếu §3.1–3.7 — bảng trạng thái từng ID

Chú thích: ✅ Đã có test tự động (trích dẫn vị trí) · 🔧 Đúng ý nhưng thuật ngữ/số liệu lạc hậu, đã sửa mô tả · ➕ Phát hiện thiếu thật, đã bổ sung · ⚪ Ngoài phạm vi/quyết định đã chốt, không phải gap

### §3.1 Đăng nhập & Xác thực

| ID | Trạng thái | Ghi chú |
|---|---|---|
| AUTH-01 | ✅ | `frontend/e2e/auth.spec.ts` (AUTH-004/001/006), `tests/test_api/test_otp.py` |
| AUTH-02 | ✅ | Verify lại: SĐT/role sai → 401 "Số điện thoại hoặc vai trò không khớp" (`src/api/main.py::login`), rate-limit 10/phút |
| AUTH-03 | 🔧 | Không phải "nút disable" mà là chặn native HTML5 — đã sửa mô tả, xem BUG-02. Test: `login.spec.ts` |
| AUTH-04 | ⚪ | Không có validate định dạng SĐT (client lẫn backend) — nhưng an toàn: input sai định dạng chỉ ra 401 chung chung giống SĐT không tồn tại (không phân biệt, đúng thực hành bảo mật — không tiết lộ SĐT có tồn tại hay không). Không sửa: validate định dạng SĐT VN đa dạng dễ tự tạo lỗi UX khác |
| AUTH-05 | ✅ | **Đây chính là bug khoá OTP sau 3 lần sai đã tìm và sửa ở đợt trước** (`src/api/main.py::verify_otp`, `tests/test_api/test_otp.py`) |
| AUTH-06 | ✅ | `auth.spec.ts::AUTH-002`, `eval/adversarial_set.jsonl` ADV-002/003 |
| AUTH-07 | ✅ | Cùng code path AUTH-02 (`user.role != req.role` → 401) — verify lại bằng đọc code, chưa có test case Playwright riêng biệt (độ ưu tiên thấp vì logic dùng chung, đã test qua AUTH-02) |
| AUTH-08 | ⚪ | Đã là quyết định thiết kế đã chốt (không phải gap): JWT stateless không track hoạt động realtime nên không có "idle timeout" riêng — thay vào đó có 2 ngưỡng freshness theo loại thao tác (12h xem / 15 phút step-up), xem `docs/TESTING.md` mục OTP. Test: `AUTH-007`/`AUTH-008` trong `auth.spec.ts` |
| AUTH-09 | ✅ (repro lại, đúng) | Logout rồi Back → về `/login`, không có nội dung cache cũ nào hiện ra (`(app)/layout.tsx` check session server-side mọi navigation, kể cả back) |

### §3.2 RBAC

| ID | Trạng thái | Ghi chú |
|---|---|---|
| RBAC-01, 02 | ✅ | `tests/test_api/test_resolution_approval.py`, `test_authz_matrix.py` — CSKH không có quyền approve, Sếp cần duyệt mọi phạm vi kể cả `internal_wallet` |
| RBAC-03 | 🔧 | Đúng Ý nhưng "Tầng A/B" đã lạc hậu — thực tế chỉ 1 tín hiệu `FS-06`. `Ticket.assigned_role` default luôn `"cskh"` (`src/db/models.py`), verify lại đúng như báo cáo mô tả |
| RBAC-04, 05, 06 | ✅ | `tests/test_api/test_authz_matrix.py` (42 case), có `approved_by`/`approved_at` ghi log |

### §3.3 Luồng khiếu nại

| ID | Trạng thái | Ghi chú |
|---|---|---|
| CLAIM-01..05 | ✅ | `eval/golden_set.jsonl`, `eval/functional_qa_set.jsonl` (ma trận 4×3 đầy đủ, đã build ở đợt thích ứng `FIN05_QA_TestCases.jsonl`) |
| CLAIM-06 | ✅ | `src/agents/prompt.py` có `CLARIFY_QUESTION_MAX_ROUNDS` — hỏi lại tối đa N lần rồi tạo ticket `trans_id=None`, cùng tinh thần với `eval/golden_set.jsonl` các case `not_found` |
| CLAIM-07, 08 | 🔧 | "Tầng A/B" lạc hậu — đã viết lại thành `FRAUD-001`/`FRAUD-002` theo đúng FS-06 duy nhất ở đợt thích ứng `FIN05_QA_TestCases.jsonl` trước đó (`eval/fraud_qa_set.jsonl`) |

### §3.4 AI grounding, §3.5 Bảo mật, §3.7 Pháp lý

| ID | Trạng thái | Ghi chú |
|---|---|---|
| AI-01..06 | ✅ | Đúng như AI-06 tự nhận định — `eval/golden_set.jsonl`/`adversarial_set.jsonl` đã build đầy đủ (120 + 45 case), gồm cả prompt injection (AI-02/03), chống lộ OTP/mật khẩu (AI-04) |
| SEC-01 | ✅ | `require_role`/`get_current_user`, `tests/test_api/test_authz_matrix.py` |
| SEC-02 | ✅ | Verify lại bằng curl: `/auth/login` có `@limiter.limit("10/minute")`, request #11 trở đi → 429 |
| SEC-03 | ✅ | Toàn bộ route auth/tools dùng POST body, không route GET nào chứa SĐT/số dư trong query string |
| SEC-04 | ⚪ | N/A cho demo local — thuộc phạm vi `production-packaging-checklist.md` khi lên deploy thật |
| SEC-05 | ✅ | Chính là mục tiêu của đợt observability trước đó — `src/observability/pii.py` (Presidio + underthesea), scrub trước khi log/trace |
| SEC-06 | ✅ | `scripts/verify_security.sh` check #2 — không có `CORSMiddleware`, xác nhận browser không gọi thẳng backend được |
| LEGAL-01 | ⚪ | Đã xác nhận ngoài phạm vi sản phẩm ở đợt trước — không có xác thực sinh trắc học, giữ `xfail` có ghi chú (`tests/test_services/test_not_applicable_qa_cases.py`, case `COMP-002`) |
| LEGAL-02 | ✅ | `must_not_reveal_full_receiver_phone` trong `FORBIDDEN_PATTERNS` |
| LEGAL-03 | ✅ | Đã xác nhận trích đúng Nghị định 52/2024 + Thông tư 40/2024, không dùng TT 39/2014 hết hiệu lực |

### §3.6 UX/Accessibility — mảng THẬT SỰ THIẾU, đã bổ sung toàn bộ

Trước đợt này: **0 test tự động** cho toàn bộ mục này (khác các mục khác đã có sẵn hạ tầng). Đã cài `@axe-core/playwright` (chuẩn ngành, engine kiểm WCAG thật) + viết `frontend/e2e/accessibility.spec.ts` (10 test):

| ID | Cách test | Phát hiện thật trong lúc verify |
|---|---|---|
| UX-01 | Xem mục BUG-01 — đã fix hệ thống (timeout cho mọi async call) | — |
| UX-02 | Viewport 360×640 + 390×844 (resize) + profile mobile Chrome thật (Pixel 7 userAgent/touch) | Không phát hiện vỡ layout |
| UX-03 | Tab focus + Enter submit form login | Không phát hiện vấn đề |
| UX-04 | `axe-core` quét `/login` + `/chat` | **Phát hiện thật:** nút "Gửi" (icon-only) không có `aria-label` nào — vi phạm WCAG nghiêm trọng (`critical`, rule `button-name`). Đã sửa (`ChatClient.tsx`). Grep xác nhận đây là gap **hệ thống** (0 `aria-label` nào trong toàn bộ frontend trước khi sửa) — chỉ sửa đúng chỗ `axe-core` xác nhận, phần còn lại cần audit riêng rộng hơn (ghi ở mục 5) |
| UX-05 | `page.route().abort()` mô phỏng mất mạng khi gửi chat | Không phát hiện vấn đề — tin nhắn vẫn hiện trong luồng, có lỗi rõ ràng |
| UX-06 | `axe-core` rule `color-contrast` | **Phát hiện thật:** `--text-faint` (light 3.05:1, dark 3.70:1) và `.eyebrow` badge (4.16:1) đều dưới ngưỡng AA 4.5:1 — đã sửa cả 2 theme (`globals.css`), verify lại bằng công thức WCAG relative luminance trước khi chọn màu thay thế |
| UX-07 | `eval/llm_judge_set.jsonl` case `UXQA-001` | **Đã có sẵn** — đúng kịch bản báo tin xấu (giao dịch đã thành công đúng ý khách, không phải lỗi hệ thống), kiểm cả đồng cảm lẫn không hứa hoàn tiền sai căn cứ |

---

## 4. Test tự động đã bổ sung trong đợt này

| File | Số case | Mảng |
|---|---|---|
| `frontend/e2e/login.spec.ts` | 2 | BUG-01 (timeout), BUG-02 (native validation) |
| `frontend/e2e/accessibility.spec.ts` | 10 | UX-02 (mobile viewport ×5), UX-03 (bàn phím ×2), UX-04+UX-06 (axe-core WCAG ×2), UX-05 (mất mạng ×1) |

Chạy: `cd frontend && npx playwright test e2e/login.spec.ts e2e/accessibility.spec.ts`

## 5. Việc còn lại (khuyến nghị, không phải blocker)

- **Audit `aria-label` rộng hơn**: `axe-core` chỉ quét được `/login` và `/chat` (2 trang có test) — các trang khác (`/approve`, `/dashboard`, `/tickets/[id]`, `/knowledge`) dùng cùng pattern `icon-btn`/`icon` chưa được quét, nên nhiều khả năng có cùng gap. Đề xuất mở rộng `accessibility.spec.ts` sang các trang đó khi có thời gian.
- **AUTH-04** (validate định dạng SĐT): để nguyên có chủ đích (an toàn hơn khi không phân biệt lỗi định dạng vs không tồn tại), nhưng nếu muốn polish UX có thể thêm gợi ý định dạng khi blur.
- **Timezone bug đã ghi nhận ở đợt Playwright AUTH-007/008 trước** (`dt.datetime.utcnow().timestamp()`) vẫn chưa sửa — không liên quan trực tiếp tới báo cáo này nhưng cùng nhóm "nợ kỹ thuật đã biết", xem `docs/TESTING.md`.
