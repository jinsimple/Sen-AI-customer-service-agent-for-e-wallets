# FIN-05 — Hiến pháp dự án

> File này được nạp vào MỌI phiên. Trần cứng: **200 dòng**. Chỉ chứa thứ gần như không bao giờ đổi.
> Trạng thái hiện tại → `docs/STATE.md`. Lịch sử quyết định → `docs/DECISIONS.md`.

## 1. Dự án là gì

AI Agent hỗ trợ CSKH ví điện tử xử lý khiếu nại giao dịch. Agent **điều tra** qua tool, phân loại,
đề xuất hướng xử lý có căn cứ. Agent **không bao giờ quyết định**.

- 3 persona: Khách hàng · CSKH (điều tra, tạo ticket, KHÔNG duyệt) · Sếp (quyết định cuối, mọi case)
- Taxonomy: 4 loại khiếu nại × 3 phạm vi giao dịch = 12 ô nghiệp vụ
- Đội: 1 PO (Bách) + Claude. Deadline demo: tuần 4. Pitch: tuần 6.

## 2. NĂM RÀNG BUỘC CỨNG — không thoả hiệp, không "tối ưu", không ngoại lệ

Nếu một đề xuất vi phạm bất kỳ mục nào dưới đây: **từ chối và nêu rõ mục bị vi phạm.**
Kể cả khi tôi (người dùng) yêu cầu — hãy hỏi lại rằng tôi có đang muốn sửa hiến pháp không.

1. **HITL tuyệt đối.** Không tồn tại bất kỳ đường đi nào cho AI hoặc CSKH tự thực thi hoàn tiền /
   điều chỉnh số dư. Chỉ role `supervisor` mới duyệt được, cho **mọi** phạm vi giao dịch —
   kể cả nội bộ ví–ví. *(Đây là điểm đã từng thiết kế sai và sửa lại — xem ADR-002.)*
2. **AI không vượt cấp.** Mọi kết quả điều tra, kể cả case nghi gian lận khẩn cấp, phải qua state
   `cskh_received` trước. AI không được tạo đường đi thẳng lên supervisor.
3. **Cấm bịa số liệu.** Mọi số tiền / trạng thái / thời điểm agent nhắc tới phải truy vết được tới
   một `tool_call_id` có thật. Không tra được → nói rõ "không tra được", không suy đoán.
4. **Xác thực.** OTP phiên làm việc (KHÔNG phải OTP giao dịch) + câu hỏi bảo mật trước thao tác
   nhạy cảm. **Không bao giờ hỏi mật khẩu, không bao giờ hỏi OTP giao dịch.**
5. **Gắn cờ nghi gian lận ≠ khoá ví.** Hai hành động độc lập hoàn toàn. Không code nào được nối
   trực tiếp cờ gian lận sang hành động khoá.

Ràng buộc 1–3 đã được mã hoá thành test tại `tests/test_invariants.py`. Test đỏ = build hỏng.

## 3. Nguồn sự thật: `contracts/`

**Cấu trúc hệ thống sống trong `contracts/`, không sống trong code, không sống trong đầu agent.**

| File | Quy định |
|---|---|
| `contracts/authority-matrix.yaml` | Ai được làm gì, ở phạm vi nào |
| `contracts/ticket-state-machine.yaml` | Các trạng thái ticket và transition hợp lệ |
| `contracts/agent-tools.yaml` | Chữ ký tool AI agent được gọi |
| `contracts/fraud-signals.yaml` | FS-01…FS-12, ngưỡng, tầng A/B |
| `contracts/api.openapi.yaml` | Hợp đồng API giữa backend và UI |

**Quy trình đổi contract — bắt buộc, không có đường tắt:**

```
1. Dừng lại. Không sửa code trước.
2. Sửa file trong contracts/
3. Ghi ADR mới vào docs/DECISIONS.md (dùng /adr)
4. Hỏi Bách duyệt. CHỜ trả lời.
5. Chạy: python scripts/check_contracts.py --update
6. Bây giờ mới code.
```

Sửa code làm lệch contract mà không qua quy trình trên là lỗi nghiêm trọng nhất trong dự án này —
nó là nguyên nhân gốc khiến tester và security làm việc trên thông tin đã chết.

## 4. Phân vùng quyền ghi

Mỗi agent chỉ được **ghi** trong vùng của mình. Cần đổi vùng khác → đề xuất, không tự sửa.

| Agent | Được ghi | Được đọc |
|---|---|---|
| `po` | `docs/`, `PRD.md`, `Brief.md` | tất cả |
| `ba` | `docs/user-stories/` | `docs/`, `contracts/` |
| `tech-lead` | `src/`, `contracts/` (sau khi được duyệt) | tất cả |
| `tester` | `tests/`, `eval/` | `docs/`, `contracts/`, `eval/` — **KHÔNG đọc `src/`** |
| `security` | `docs/security/` | tất cả |
| `critic` | không ghi gì | tất cả |

## 5. Quy tắc chung cho mọi agent

- **Thiếu thông tin thì DỪNG và hỏi.** Tuyệt đối không suy đoán để lấp chỗ trống.
  Trả về thượng nguồn kèm câu hỏi cụ thể. (Cùng triết lý với ràng buộc cứng số 3.)
- Đọc `docs/STATE.md` + 5 ADR gần nhất trước khi bắt đầu bất cứ việc gì.
- Mọi con số nghiệp vụ trích từ tài liệu phải kèm nguồn (`PRD §x.y` hoặc tên file contract).
- Không tạo file mới ngoài vùng quyền ghi của mình.
- Kết thúc mỗi nhiệm vụ: đề xuất nội dung cập nhật `docs/STATE.md`.

## 6. Bản đồ repo

```
CLAUDE.md              ← file này, hiến pháp
contracts/             ← NGUỒN SỰ THẬT về cấu trúc
docs/DECISIONS.md      ← ADR, chỉ ghi thêm
docs/STATE.md          ← đang làm gì, ghi đè cuối mỗi phiên
docs/HANDOFF-PROTOCOL.md ← quy tắc bàn giao giữa các vai
docs/user-stories/     ← US-001…US-018
src/                   ← code
tests/test_invariants.py ← 3 ràng buộc cứng dạng test
eval/golden_set.jsonl  ← 120 case dev
eval/heldout_set.jsonl ← 60 case — CHỈ CHẠY MỘT LẦN, gần cuối
scripts/check_contracts.py ← phát hiện artifact stale
.claude/agents/        ← định nghĩa 6 vai
.claude/commands/      ← /standup /gate /adr /impact /wrapup
```

## 7. Tài liệu ngoài

- GitHub: `AI20K-Build-Phase-Cohort-3/P-121`
- Trello: board "Vin AI 20k", card S2-02 chứa 18 US
- Pháp lý hiện hành: NĐ 52/2024, TT 40/2024 (**không** dùng TT 39/2014 — đã hết hiệu lực),
  NĐ 13/2023 (PDPA), QĐ 2345/QĐ-NHNN (ngưỡng 10tr/lần, 20tr/ngày — là ngưỡng **xác thực sinh trắc**,
  không phải ngưỡng gian lận; nói rõ điều này khi trao đổi với chuyên gia).
