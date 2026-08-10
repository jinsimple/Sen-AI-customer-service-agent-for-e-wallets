# FIN-05 — Bàn giao backend cho phần xây AI Agent

> File này viết cho **Claude Code** (phiên làm việc tiếp theo, chuyên trách xây
> logic AI agent). Mục đích: hiểu ngay bối cảnh, quyết định thiết kế đã chốt,
> và biết chính xác việc cần làm tiếp — không phải đọc lại từ đầu toàn bộ
> lịch sử dự án.
>
> Cập nhật lần cuối: 09/08/2026.

## 0. Bối cảnh — đọc trước khi làm gì khác

FIN-05 là AI Agent CSKH xử lý khiếu nại giao dịch cho ví điện tử (đội T121,
AI 20K Build Phase Cohort 3, Vingroup × VinUni). Team gốc 4 người gặp vấn đề
nội bộ; dự án hiện do **1 người (PO, không phải dev full-time) + Claude Code**
xây lại từ đầu trong **2 tuần** để có demo. Tài sản duy nhất giữ lại nguyên
vẹn từ team cũ là **bộ dataset** (đã kiểm định kỹ, xem §1). Toàn bộ code
backend ở repo này (`src/`, `scripts/seed_db.py`, `tests/`) là code MỚI, viết
lại từ đầu dựa trên đặc tả trong `docs/FIN05-Data-Brief.md`.

**Rủi ro lớn nhất của dự án, theo đánh giá của PO — và đây chính là việc
Claude Code sắp làm:** AI agent phải đủ "thông minh" theo nghĩa rất cụ thể,
đo được, không phải cảm tính:

1. Điều tra đúng công cụ, đúng thứ tự — không hỏi lại cái đã tra được, không
   bỏ sót bước.
2. Phân loại đúng ô ma trận: đúng 1/4 loại khiếu nại × đúng 1/3 phạm vi giao
   dịch (12 ô).
3. **Không bao giờ bịa số liệu** — mọi số tiền/trạng thái nói ra phải truy
   được về một `tool_result_id` có thật.
4. Không bao giờ tự quyết — mọi đề xuất luôn `pending_approval`, luôn qua
   CSKH trước, không vượt cấp thẳng lên sếp kể cả case khẩn.
5. Với case nghi gian lận: không kết luận, không tiết lộ tín hiệu nào đã
   bật, không dùng từ "lừa đảo/gian lận", không đóng băng ví.

Bốn điều trên không phải lời dặn trong prompt — **phần lớn đã được ép sẵn ở
tầng DB/service** (xem §3). Việc của agent là hành xử đúng trong phạm vi mà
tầng dưới đã giới hạn sẵn, không phải tự giác tuân thủ.

## 1. Dataset — không cần sinh lại, chỉ cần đọc

`data/generated/` đã có sẵn, sinh từ seed cố định `20260802`, đã qua 16 nhóm
kiểm định (`make data-check` pass 100%):

| Bảng | Số dòng | Ghi chú |
|---|---:|---|
| `users` | 206 | 200 khách, 4 CSKH, 2 supervisor |
| `wallets` | 200 | |
| `bank_accounts` | 245 | |
| `transactions` | 60.000 | 90 ngày, 3 phạm vi |
| `transaction_events` | 215.944 | timeline — nguồn agent dùng để điều tra |
| `complaints` | 600 | dữ liệu nền, ~1% giao dịch |
| `tickets` | 600 | |
| `auth_sessions` | 303 | |

`eval/golden_set.jsonl` (120 case) + `eval/heldout_set.jsonl` (60 case, KHÔNG
xem khi tinh chỉnh prompt) — mỗi case có `expected`/`forbidden` để chấm điểm
agent tự động. **Đây là bộ công cụ quan trọng nhất để giảm rủi ro ở §0** —
đừng viết agent xong mới nghĩ tới eval, hãy chấm ngay từ bản đầu tiên.

Đọc kỹ trước khi dùng: `docs/FIN05-Data-Brief.md` (đặc tả gốc, ERD đầy đủ,
5 tầng test T1-T5, 10 chỉ số ngưỡng đạt ở §6.8) và
`data/raw/business_rules.md` (20 quy tắc nghiệp vụ BR-01..BR-20, cột
`verified` cho biết cái nào là giả định team tự đặt — **agent không được nói
với khách những con số `verified: false` như thể đã kiểm chứng chính thức**).

## 2. Đã build xong — backend

```
src/
├── config.py              # mọi hằng số/đường dẫn dùng chung — sửa 1 chỗ
├── db/
│   ├── models.py           # SQLAlchemy 2.0, 13 bảng, CHECK constraint ép guardrail
│   └── session.py          # engine + session factory, PRAGMA foreign_keys=ON
├── tools/                  # 5 tool agent sẽ gọi — xem §3
│   ├── base.py               # record_tool_result() — MỌI tool phải gọi cái này
│   ├── masking.py             # BR-06 PDPA masking
│   ├── fraud_policy.py        # 1 tín hiệu FS-06, không còn 2 tầng A/B (PRD §5, cập nhật 09/08/2026)
│   ├── sla.py                  # BR-01/02/04 tính sla_due_at
│   ├── lookup_transaction.py
│   ├── get_customer_history.py
│   ├── create_ticket.py
│   ├── propose_resolution.py
│   └── escalate_ticket.py
└── api/
    ├── main.py              # FastAPI — endpoint /tools/*, /tickets*, HITL gate
    ├── deps.py
    └── schemas.py

migrations/                # Alembic, đã có migration đầu (13 bảng)
scripts/seed_db.py         # nạp data/generated/*.jsonl vào DB, idempotent
tests/test_tools/          # 22 test, pass 100%
tests/test_data/           # 4 test bất biến nhanh, pass 100%
Makefile                   # make db (data → data-check → db-reset → db-seed)
```

Đã verify: `make db` chạy trọn vẹn, số dòng nạp vào DB khớp 100%
`data/generated/manifest.json`; `make data-check` (16 nhóm kiểm định gốc của
team) pass; `pytest tests/` 26/26 pass; đã test tay bằng `TestClient` cho
toàn bộ luồng API kể cả nhánh 403 khi CSKH/khách cố duyệt resolution.

**Lưu ý môi trường:** nếu bạn thấy `sqlite3.OperationalError: disk I/O
error` khi chạy trên máy có thư mục dự án được mount qua lớp ảo hoá/FUSE nào
đó (network drive, sandbox...), đó là giới hạn của lớp mount, không phải lỗi
code — SQLite cần file-lock thật. Chạy trên đĩa cục bộ bình thường thì không
gặp vấn đề này.

## 3. Năm tool — hợp đồng mà agent phải tuân theo

Đây là bề mặt duy nhất agent được phép chạm vào dữ liệu. Đọc kỹ signature
trước khi viết agent loop, vì mỗi tool đã tự ép sẵn một phần guardrail:

### `lookup_transaction(session, *, trans_id=None, rec_code=None, phone=None, amount=None, date_from=None, date_to=None, requesting_user_id=None)`
Trả về đúng một trong ba dạng — **agent phải xử lý cả ba, không được đoán**:
- `{"status": "found", "transaction": {...}}` — `receiver`/`sender` đã bị
  masking PDPA (SĐT `090***1234`, tên `T. H. Trang`, STK `**********0001`)
  trừ khi `requesting_user_id` trùng chủ sở hữu.
- `{"status": "not_found"}` — **không bao giờ trả kết quả gần đúng**.
- `{"status": "multiple_matches", "candidates": [...]}` — agent phải hỏi lại
  khách để thu hẹp, **không được tự chọn hộ**.

### `get_customer_history(session, *, user_id, days=90, limit_transactions=20)`
Chỉ trả dữ liệu của đúng `user_id` truyền vào — không có tham số nào (kể cả
`phone`) mở rộng sang user khác. Agent gọi hàm này để lấy ngữ cảnh trước khi
kết luận, không phải để "tìm khách qua số điện thoại người khác kể".

### `create_ticket(session, *, user_id, complaint_type, scope, description_raw, trans_id=None, otp_disclosed=False, fraud_signals=None)`
Từ chối (`ToolError`) nếu `trans_id` không tồn tại. `trans_id=None` hợp lệ
CHỈ khi đây thật sự là case không tra ra giao dịch nào. `assigned_role` luôn
là `'cskh'` — **agent không bao giờ tạo ticket thẳng lên supervisor**.
`fraud_signals` hiện là tham số nhận list mã tín hiệu đã tính sẵn (agent
truyền vào). **Cập nhật 09/08/2026:** phạm vi MVP chỉ còn 1 tín hiệu kích
hoạt escalate — `FS-06` (PRD §5, Data Brief §4.5.3) — không còn khái niệm
Tầng A/B. `evaluate_escalation()` trong `fraud_policy.py` đã sửa theo hướng
này. Mã tín hiệu khác ngoài `FS-06` vẫn có thể xuất hiện trong list (dữ liệu
kế thừa từ dataset gốc 12 tín hiệu) nhưng không ảnh hưởng `should_escalate`.
Xem việc còn thiếu ở §4.1.

### `propose_resolution(session, *, ticket_id, action_type, rationale, amount=None, destination_ref=None, cited_tool_result_ids=None)`
**Cố ý không có tham số `status`** — không có cách nào, kể cả gọi sai, tạo ra
resolution đã duyệt. Luôn ra `pending_approval`. Nếu `cited_tool_result_ids`
chứa một id không tồn tại trong bảng `tool_results` → từ chối. Đây là chỗ
thực thi "không bịa số liệu" ở tầng ghi: agent PHẢI trích dẫn đúng
`tool_result_id` mà chính agent nhận được từ lần gọi tool trước đó.

### `escalate_ticket(session, *, ticket_id, target, reason, created_by)`
`reason` bắt buộc không rỗng. Với case nghi gian lận (phạm vi MVP: chỉ do
`FS-06` kích hoạt), `reason` PHẢI là mã tín hiệu (`"FS-06"`), **không phải
câu kết luận** — quy tắc này ở tầng agent/prompt, hàm chỉ ép không rỗng chứ
không kiểm nội dung.

**Nguyên tắc chung cho cả 5 tool:** mọi lần gọi đều tự động ghi một dòng vào
bảng `tool_results` (qua `record_tool_result` trong `base.py`) — đây là
nguồn sự thật duy nhất để sau này chấm điểm "agent có bịa số liệu không"
(T4, Data Brief §6.5). Nếu agent tự tính toán/suy diễn một con số mà không
đi qua tool, con số đó không có `tool_result_id` nào để trích dẫn — đó chính
là dấu hiệu vi phạm.

## 4. Việc còn thiếu — theo thứ tự ưu tiên

### 4.1 Nối `fraud_engine.py` vào `create_ticket` (nhỏ, làm trước)
`scripts/fraud_engine.py` đã có sẵn, đã được `validate_dataset.py` dùng để
đối chiếu nhãn golden set (double-entry: nhãn gán tay khớp máy tính). Hiện
`create_ticket` nhận `fraud_signals` như tham số truyền tay từ agent — cần
viết một lớp mỏng chuyển dữ liệu từ DB (SQLAlchemy rows) sang định dạng
`LedgerIndex` mà `fraud_engine.py` cần (list dict), gọi engine, rồi mới gọi
`create_ticket`. Việc này nên nằm ở một service layer mới (vd
`src/services/complaint_intake.py`), KHÔNG nhét trực tiếp vào tool — giữ
tool mỏng và dễ test.

### 4.2 AI Agent — phần việc chính, đây là lý do bạn được gọi vào
Chưa có bất kỳ dòng code agent nào. Cần xây:
- Vòng lặp agent gọi 5 tool ở §3 qua HTTP (`src/api/main.py` đã expose sẵn ở
  `/tools/*`) hoặc gọi thẳng hàm Python nếu chạy cùng process.
- System prompt / policy layer mã hoá đúng 5 điều ở §0, đặc biệt: không kết
  luận gian lận, không tiết lộ tín hiệu, không bịa số liệu, luôn hỏi lại khi
  `lookup_transaction` trả `multiple_matches`.
- Vòng lặp làm rõ (clarifying question) khi khiếu nại của khách mơ hồ —
  ngưỡng N lần hỏi lại trước khi tạo ticket tra thủ công là `N=2`
  (`src/config.py: CLARIFY_QUESTION_MAX_ROUNDS`, nhưng BR-13 ghi rõ
  **chưa chốt chính thức với team**, PO cần duyệt).
- Chạy được trên `eval/golden_set.jsonl` (120 case) để tự chấm điểm theo 4
  chỉ số ở Data Brief §6.4 (loại khiếu nại, phạm vi, đích escalate, có hỏi
  lại đúng lúc không) — đây là cách duy nhất biết agent "đủ thông minh" hay
  chưa mà không phải đoán.
- **Không đụng vào `eval/heldout_set.jsonl` khi tinh chỉnh prompt** — chỉ
  chạy trước demo để đo chênh lệch dev/held-out (ngưỡng ≤10 điểm, Data Brief
  §6.8). Đụng vào là tự phá công cụ chống overfit duy nhất của dự án.

### 4.3 UI tối thiểu cho 2 persona (Khách hàng, CSKH)
Backend đã có đủ API để build UI chat khách hàng + màn hình CSKH xem/điều
tra ticket (`GET /tickets`, `GET /tickets/{id}`). Persona Sếp/duyệt có thể
làm ở mức tối giản — 1 màn hình gọi `POST /resolutions/{id}/approve` (đã
ép `role=supervisor`, đã test 403 khi sai role).

### 4.4 Test T3/T4/T5 chạy agent thật (chưa làm được tới khi có agent)
Khung đã có trong Data Brief §6.4-6.6 và `eval/results/report.md` — chỉ cần
điền số khi agent chạy được.

## 5. Cách chạy nhanh

```bash
pip install -r requirements.txt
make db                     # data → data-check → db-reset → db-seed
make run                     # FastAPI tại :8010 (đổi từ 8000 — tránh xung đột port với project khác), xem /docs cho Swagger UI
make test                    # pytest tests/ — 26 test hiện có
```

## 6. Quyết định thiết kế — đừng đề xuất lại cái đã chốt

Xem đầy đủ trong ngữ cảnh dự án (Fin-05 project knowledge), tóm tắt phần
liên quan trực tiếp tới việc xây agent:

- **HITL tuyệt đối, mọi phạm vi giao dịch kể cả nội bộ ví** — chỉ sếp
  (`role=supervisor`) duyệt được, đã ép ở CHECK constraint DB + route API,
  không chỉ ở prompt.
- **AI không bao giờ vượt cấp** — mọi kết quả điều tra qua CSKH tiếp nhận
  trước, kể cả case nghi gian lận khẩn cấp. `create_ticket` luôn
  `assigned_role='cskh'`.
- **Cấm bịa số liệu** — mọi số agent nói phải truy được về `tool_result_id`
  thật (§3, cơ chế `record_tool_result`).
- **Gắn cờ nghi gian lận ≠ khoá ví** — hai hành động độc lập, agent không
  bao giờ tự đóng băng ví hay hứa đóng băng ví.
- **"Ngoài thẩm quyền" định nghĩa theo role, không theo hạn mức tiền.**
