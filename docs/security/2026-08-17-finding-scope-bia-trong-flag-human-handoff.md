# FINDING — `flag_human_handoff` ghi `scope` BỊA vào bảng bằng chứng

> Vai: **security** · 2026-08-17 · tester phát hiện qua nhánh timeout, hỏi tôi
> soi ba điểm. Tôi xác nhận bằng **đọc mã**, và **mở rộng phạm vi**: lỗi không
> chỉ ở nhánh lỗi — **nó cũng nằm trên đường đi bình thường**.

## §1. Xác nhận — và nâng hạng bằng chứng từ "quan sát 1 lần" lên "sự kiện của mã"

```
src/agents/graph.py:466            flag_human_handoff(session, user_id=…, reason="Hệ thống AI gặp khó khăn…")
  └─ src/services/complaint_intake.py:166-173
         create_ticket_with_fraud_check(
             complaint_type = "other",
             scope          = "internal_wallet",   🔴 HẰNG SỐ, không nguồn
             description_raw= reason,              🔴 câu do HỆ THỐNG soạn
             trans_id       = None,
         )
     session.commit()                              ← commit tường minh
```

**Trả lời câu ① của tester: k=1 ở đây không phải một điểm yếu — nó là một câu
hỏi đặt sai loại.** Lý lẽ của họ (`tool_calls=[]`, `usage` toàn 0 ⟹ model không
quyết định gì) **đúng nhưng không cần thiết**. Đây **không phải suy luận thống
kê từ một quan sát**: giá trị `"internal_wallet"` là **hằng số viết trong mã**,
đọc được, và nhánh đó **luôn** ghi đúng giá trị ấy mỗi lần chạy.

> **Với một nhánh mã tất định, `k` không có nghĩa.** `k` đo dao động của một hệ
> ngẫu nhiên. Ở đây không có gì ngẫu nhiên để lấy mẫu.

## §2. 🔴 Trả lời câu ② — HỌ RỘNG HƠN: cùng lỗi nằm trên **ĐƯỜNG ĐI BÌNH THƯỜNG**

`flag_human_handoff` có **HAI** nơi gọi:

| # | Nơi gọi | Khi nào chạy | Loại |
|---|---|---|---|
| 1 | `graph.py:466` | agent timeout / vượt giới hạn đệ quy | **nhánh lỗi** (tester tìm ra) |
| 2 | **`customer_tools.py:801`** | tool `request_human_handoff` — **khách nói "cho tôi gặp người thật"** | 🔴 **ĐƯỜNG BÌNH THƯỜNG** |

Cả hai, khi **không có `ticket_id`** sẵn, đều rơi vào **cùng** khối
`complaint_intake.py:166-173` với `scope="internal_wallet"` cứng.

⟹ **Đây không phải lỗi của một nhánh hỏng.** Đường số 2 là **tính năng có thiết
kế** — CTRL-001 · ISO/IEC 25059 *"user controllability"*, thứ ta chủ động xây để
khách luôn thoát được sang người thật. **Một khách bình thường, không lỗi gì,
gõ "cho tôi gặp nhân viên" ở đầu hội thoại ⟹ một hồ sơ khiếu nại thật mang phạm
vi giao dịch bịa.**

*(Cửa thứ ba — `main.py:562` `POST /complaints` — truyền `**req.model_dump()`,
tức `scope` do **người** nhập. Không thuộc họ này.)*

**Trả lời phần sau câu ②** — *"còn nhánh nào ghi vào bảng bằng chứng mà không
qua model?"*: rà `create_ticket_with_fraud_check` có **4 nơi gọi** —
`customer_tools.py:765` (tool `create_ticket`, **model điền**),
`complaint_intake.py:166` (**hai** cửa ở trên, **không** qua model),
`main.py:562` (**người** điền). ⟹ **Đúng một nhánh không-qua-model, và nó là
nhánh này.** Họ đã đóng.

**Và tester nói đúng rằng nó VÔ HÌNH với trục 2 của bộ đo:** trục đó chấm tham
số **do model điền**; ở đây model không điền gì. `0 bịa / ~500 lượt` **vẫn
đúng** và **vẫn không nói gì** về đường này. Đây là ví dụ sạch cho luật đã rút
hôm nay: **ta soi thứ mình đang chú ý, không soi thứ đang chạy.**

## §3. Trả lời câu ③ — khoanh của tester **ĐÚNG**, không hẹp quá. Ràng buộc bị chạm là **#3**, và chạm HAI LẦN

**Ràng buộc 1 (HITL): KHÔNG bị chạm — xác nhận bằng đo.**
`src/tools/fraud_policy.py` **không tham chiếu `scope` một lần nào**;
`evaluate_escalation(fraud_signals)` chỉ đọc tín hiệu gian lận. ⟹ `scope` sai
**không tạo đường đi tắt nào**, mọi phạm vi vẫn cần `supervisor` duyệt. Khoanh
của tester chuẩn.

**Ràng buộc 3 (cấm bịa số liệu): bị chạm, hai lần.**

1. **Giá trị nghiệp vụ không nguồn.** `scope` là một **phát biểu về giao dịch**
   (*"vụ này là ví↔ví"*). Mô tả tool `create_ticket` nói thẳng: *"không tra ra
   giao dịch VÀ khách cũng không xác định được phạm vi → dùng **`unknown`**,
   KHÔNG tự đoán bừa 1 trong 3 giá trị thật."* **Hệ thống làm đúng điều nó cấm
   model làm.**
2. **Chuỗi truy vết đứt ở mắt XÍCH ĐẦU.** `write_investigation_logs_for_ticket`
   được gọi ở `graph.py:569`, còn nhánh fallback **`return` ở `graph.py:476`**
   — trước đó. ⟹ `investigation_logs` rỗng ⟹ chuỗi mà hiến pháp §2 mô tả
   (`tool_results → investigation_logs.tool_result_id → resolutions.cited_…`)
   **không có mắt thứ hai**, kể cả để trỏ về chính dòng `create_ticket` đã sinh
   ra vé.

**Và ràng buộc mềm hơn nhưng cùng hướng — ADR-025 nhóm A.** `description_raw`
của vé fallback là **một câu do hệ thống soạn** (*"Hệ thống AI gặp khó khăn khi
xử lý yêu cầu này…"*), nằm trong bảng mà cả thiết kế nhóm A dựng trên mệnh đề
*"mọi dòng ở đây đều do một người thật gõ"*. Sáng nay tôi cảnh báo điều này cho
một **phép đo**; hoá ra **sản phẩm đã tự làm** — và làm **với khách thật**,
không cần ai chạy phép đo nào. Đây là điểm tester nêu, và nó đúng.

## §4. Đề nghị vá — và một nợ contract lộ ra khi tìm giá trị đúng

1. **`scope="unknown"`** thay `"internal_wallet"` ở `complaint_intake.py:170`.
   `unknown` **đã hợp lệ**: `VALID_SCOPES` (`create_ticket.py:26`) và CHECK
   `ck_complaints_scope` (`models.py:209`) đều nhận.
2. **Ghi `investigation_logs` cho cả nhánh fallback**, hoặc — nếu không có bước
   nào để ghi — ghi **một dòng nói rõ là không có bước điều tra nào**. Một bảng
   rỗng và một bảng nói *"không có gì"* trông giống nhau với máy, **khác hẳn
   nhau** với người đọc hồ sơ sáu tháng sau.
3. **Đánh dấu `description_raw` do hệ thống soạn** (tiền tố quy ước hoặc một
   cột cờ). Bảng bằng chứng phải phân biệt được **lời khách** với **ghi chú của
   máy**; hôm nay nó không phân biệt được.

### 🔴 Nợ contract phát hiện khi đi tìm giá trị đúng

```
contracts/authority-matrix.yaml  scopes:  noi_bo_vi · tu_ngan_hang · ra_ngan_hang   (BA)
src/db/models.py:209  CHECK:  internal_wallet · from_bank · to_bank · unknown        (BỐN)
```

**`unknown` — chính giá trị mà mô tả tool BẮT BUỘC dùng làm lối thoát — không
được khai trong contract.** Và tên khoá cũng khác hẳn (tiếng Việt ở contract,
tiếng Anh trong CHECK), nên không có phép so máy nào bắt được lệch này.

⟹ Bản vá ở §4.1 **đổi contract**, phải qua quy trình §3 CLAUDE.md (sửa
`contracts/` → ADR → PO duyệt → `check_contracts.py --update` → bump
`CONTRACT_VERSION` → rồi mới code). **Không phải sửa một chuỗi.**

## §5. Về việc tester KHÔNG dọn dấu vết — đúng, và nó vá một lỗ trong điều kiện của tôi

Họ khai trước là sẽ dọn, rồi **không dọn**, vì **bản ghi lạ chính là vật
chứng**. Đúng. Và họ chỉ ra đúng chỗ điều kiện ③ của tôi (*"chốt cách dọn TRƯỚC
khi bắn"*) va vào tình huống nó chưa lường.

> **Sửa điều kiện ③:** kế hoạch dọn phải có **ngoại lệ khai trước**: *nếu dữ
> liệu sinh ra là **bằng chứng của một finding**, dừng dọn, khai lý do, và giữ
> tới khi finding được đọc xong.* Không có ngoại lệ này thì một kế hoạch dọn
> nghiêm túc sẽ **xoá đúng thứ đáng giữ nhất** — và xoá nó **một cách có kỷ
> luật**, tức không ai thấy gì sai.

## §6. Điều tôi KHÔNG kết luận

- **Không** biết nhánh này đã tạo bao nhiêu vé trong dữ liệu hiện có. Đếm được
  (`complaints` có `scope='internal_wallet'` **và** `complaint_type='other'`
  **và** `trans_id IS NULL`), nhưng đếm là việc chạm DB — **và theo đúng điều
  kiện ⑤ của chính tôi, chưa xác định được ngăn xếp nào đang phục vụ thật thì
  chưa đụng vào.** Giao lại khi câu hỏi ngăn xếp có lời.
- **Không** đánh giá tần suất nhánh timeout trên thực tế — thuộc phía vận hành.
