# FIN-05 — Hiến pháp dự án

> File này được nạp vào MỌI phiên của MỌI con Claude (code · QA/QC · UX/UI · tester).
> Trần cứng: **200 dòng**. Chỉ chứa thứ gần như không bao giờ đổi.
>
> Trạng thái hiện tại → `docs/STATE.md` · Lịch sử quyết định → `docs/DECISIONS.md`

## 1. Dự án là gì

AI Agent hỗ trợ CSKH ví điện tử xử lý khiếu nại giao dịch. Agent **điều tra** qua tool,
phân loại, đề xuất hướng xử lý có căn cứ. Agent **không bao giờ quyết định**.

- 4 role: `customer` · `cskh` (điều tra, KHÔNG duyệt) · `supervisor` (quyết định cuối,
  mọi phạm vi) · `partner_admin` (CHỈ quản lý kho chính sách RAG)
- Taxonomy: 4 loại khiếu nại × 3 phạm vi giao dịch
- Đội: 1 PO + nhiều phiên Claude chuyên trách. Cohort 3 (Vingroup × VinUni).

## 2. NĂM RÀNG BUỘC CỨNG — không thoả hiệp, không "tối ưu", không ngoại lệ

Nếu một đề xuất vi phạm bất kỳ mục nào: **từ chối và nêu rõ mục bị vi phạm.**
Kể cả khi PO yêu cầu — hỏi lại rằng có đang muốn sửa hiến pháp không.

1. **HITL tuyệt đối.** Không tồn tại đường đi nào cho AI hoặc CSKH tự thực thi hoàn tiền /
   điều chỉnh số dư. Chỉ `supervisor` duyệt được, cho **mọi** phạm vi — kể cả nội bộ
   ví–ví. *(Đã từng thiết kế sai và sửa lại — xem ADR-002.)*
2. **AI không vượt cấp.** AI không có role riêng: nó gọi tool **dưới danh nghĩa
   `customer`**. Escalate chỉ xảy ra qua tầng service (`fraud_policy.py`, tín hiệu FS-06)
   hoặc route của `cskh` — không bao giờ do AI tự gọi.
3. **Cấm bịa số liệu.** Mọi số tiền / trạng thái / thời điểm agent nhắc tới phải truy vết
   được tới một kết quả tool có thật (`tool_results` → `investigation_logs.tool_result_id`
   → `resolutions.cited_tool_result_ids`). Không tra được → nói rõ "không tra được".
4. **Xác thực.** OTP **phiên làm việc** (KHÔNG phải OTP giao dịch). **Không bao giờ hỏi
   mật khẩu ví, không bao giờ hỏi OTP giao dịch.** Hành động có hậu quả cần OTP step-up
   ngặt hơn (xem ADR-005).
5. **Gắn cờ nghi gian lận ≠ khoá ví.** Hai hành động độc lập hoàn toàn. Không code nào
   được nối trực tiếp cờ gian lận sang hành động khoá.

Cả 5 ràng buộc đã được mã hoá thành test tại `tests/test_invariants.py` (23 test).
**Test đỏ = build hỏng.** Chạy trong CI job `invariants` ở mọi push/PR.

## 3. Nguồn sự thật: `contracts/`

**Cấu trúc hệ thống sống trong `contracts/`, không sống trong code, không sống trong đầu
agent nào.**

| File | Quy định |
|---|---|
| `contracts/authority-matrix.yaml` | 33 route × role nào được gọi |
| `contracts/resolution-state-machine.yaml` | Vòng đời HITL + 3 trục trạng thái trực giao |
| `contracts/agent-tools.yaml` | 5 tool AI được gọi + tool bị cấm + cơ chế truy vết |

**Điều làm cơ chế này khác một tập tài liệu thường:** `tests/test_invariants.py`
**introspect app đang chạy thật** (đọc `app.routes`, moi `allowed_roles` từ closure của
`require_role()`, đọc `CheckConstraint` qua AST, gọi thẳng `build_customer_tools()`) rồi
so khớp với `contracts/`. Thêm 1 route · đổi 1 guard · đổi tên 1 tool · gỡ 1 CHECK
constraint mà quên cập nhật contract → **ĐỎ NGAY**. Không ai phải nhớ nhắc ai.

**Quy trình đổi contract — bắt buộc, không có đường tắt:**

```
1. Dừng lại. KHÔNG sửa code trước.
2. Sửa file trong contracts/
3. Ghi ADR mới vào docs/DECISIONS.md (dùng /adr)
4. Hỏi PO duyệt. CHỜ trả lời.
5. Chạy: python scripts/check_contracts.py --update
6. Cập nhật CONTRACT_VERSION ở đầu tests/test_invariants.py
7. Bây giờ mới code.
```

Sửa code làm lệch contract mà không qua quy trình trên là lỗi nghiêm trọng nhất của dự án
— nó chính là nguyên nhân khiến tester và security làm việc trên thông tin đã chết.

## 4. Phân vùng quyền ghi

Mỗi phiên Claude chỉ được **ghi** trong vùng của mình. Cần đổi vùng khác → đề xuất, không tự sửa.

| Vai | Được ghi | Được đọc |
|---|---|---|
| `po` | `docs/`, `*.md` ở gốc | tất cả |
| `tech-lead` | `src/`, `frontend/src/`, `migrations/`, `docker-compose*.yml`, `.github/workflows/**`, `contracts/` (sau khi PO duyệt) | tất cả |
| `tester` | `tests/`, `frontend/e2e/`, `eval/` | `docs/`, `contracts/`, `eval/` — **KHÔNG đọc `src/`** |
| `security` | `docs/security/` | tất cả |
| `ux-ui` | `frontend/src/`, `*.html` wireframe | `docs/`, `contracts/` |
| `critic` | không ghi gì | tất cả |

**Vì sao tester không được đọc `src/`:** LLM bám rất chặt vào văn bản vừa đọc. Cho tester
đọc code, test nó viết sẽ *phản chiếu* logic đang có — kể cả logic sai. Kết quả là một
suite xanh mướt chứng minh rằng bug hoạt động đúng như bug.

## 5. Quy tắc chung cho mọi phiên Claude

- **Thiếu thông tin thì DỪNG và hỏi.** Tuyệt đối không suy đoán để lấp chỗ trống.
  (Cùng triết lý với ràng buộc cứng số 3 — quy trình và sản phẩm cùng một nguyên tắc.)
- Đọc `docs/STATE.md` + 5 ADR gần nhất **trước khi** bắt đầu bất cứ việc gì.
- Mọi con số nghiệp vụ trích từ tài liệu phải kèm nguồn (`PRD §x.y` hoặc tên file contract).
- Không tạo file mới ngoài vùng quyền ghi của mình.
- Kết thúc mỗi nhiệm vụ: đề xuất nội dung cập nhật `docs/STATE.md` (dùng `/wrapup`).
- **Không báo cáo hoàn thành dựa trên suy luận từ code tĩnh** — chạy thật, đọc log thật,
  dán kết quả thật. Test không chạy được thì nói là chưa chạy được.

## 6. Bản đồ repo

```
CLAUDE.md                    ← file này, hiến pháp
contracts/                   ← NGUỒN SỰ THẬT về cấu trúc
docs/DECISIONS.md            ← ADR, CHỈ GHI THÊM, không sửa
docs/STATE.md                ← đang làm gì, ghi đè cuối mỗi phiên
docs/TESTING.md              ← cách chạy từng nhóm test
scripts/check_contracts.py   ← phát hiện artifact lỗi thời
tests/test_invariants.py     ← 5 ràng buộc cứng, 23 test, introspect app thật
tests/                       ← 42 file test backend
frontend/e2e/                ← 13 file Playwright
eval/golden_set.jsonl        ← case dev · eval/heldout_set.jsonl CHỈ CHẠY MỘT LẦN, gần cuối
.claude/agents/              ← định nghĩa vai
.claude/commands/            ← /standup /gate /adr /impact /wrapup
```

## 7. Lệnh hay dùng

```bash
# Ràng buộc cứng (phải luôn 19/19 xanh)
pytest tests/test_invariants.py -v

# Phát hiện artifact lỗi thời so với contracts/
python scripts/check_contracts.py

# Toàn bộ backend, trừ finding P0 chưa vá
pytest tests/ -m "not security_finding"
```

Biến môi trường bắt buộc (fail-fast nếu thiếu): `JWT_SECRET_KEY`, `FIELD_ENCRYPTION_KEY`,
`REDIS_URL` (dùng `fake://ci` cho test/CI — fakeredis, không cần Redis thật).

## 8. Tài liệu ngoài

- GitHub: `AI20K-Build-Phase-Cohort-3/P-226` *(đo 18/08 từ `git remote -v` — dòng cũ ghi `P-121`, SAI)*
- Pháp lý hiện hành: NĐ 52/2024, TT 40/2024 (**không** dùng TT 39/2014 — đã hết hiệu lực),
  NĐ 13/2023 (PDPA), QĐ 2345/QĐ-NHNN (ngưỡng 10tr/lần, 20tr/ngày — là ngưỡng **xác thực
  sinh trắc**, KHÔNG phải ngưỡng gian lận; nói rõ điều này khi trao đổi với chuyên gia).
