# Định hạng bản vá A (O3 mở kênh nguồn sang ToolMessage lịch sử) — MỘT TRANG

> Vai: Bảo Mật · 18/08/2026 tối · theo brief `docs/giao-viec/2026-08-18-team-o3-demo-len-main.md` mục 2-Bảo Mật.
> Câu duy nhất phải trả lời: *mở kênh nguồn O3 sang `ToolMessage` lịch sử có mở kênh rò MỚI không?*
> Mọi số dòng dưới đây đo trên cây làm việc `dev/learning-loop`, băm src chưa đổi so với §2 STATE (không ai land gì từ lúc nhận chuông tới lúc đo).

## KẾT LUẬN: CHO PHÉP KÈM ĐIỀU KIỆN (một điều kiện bắt buộc, đánh số Đ1)

## 1. Kiểm lại độc lập tiền đề của PO-agent — KHÔNG đúng nguyên văn, nhưng đúng về bản chất PII

PO-agent viết: *"mọi `ToolMessage` đã qua `_scrub_pii_cho_llm`"*. **[ĐO] liệt kê ĐỦ 5/5 đường trả về** trong `build_customer_tools()` (`customer_tools.py`):

| tool | đường trả về | qua scrub? | payload chứa gì |
|---|---|---|---|
| `lookup_transaction` | `:838` `boc_ten_sau_scrub(_scrub_pii_cho_llm(_sanitize_lookup_result(…)))` | ✅ | dữ liệu tài khoản — ĐÃ che tên/SĐT/số TK |
| `get_customer_history` | `:867` `_scrub_pii_cho_llm(…)` | ✅ | như trên |
| `create_ticket` | `:909` `create_ticket_with_fraud_check(…)` | ❌ | **không PII theo cấu trúc**: `complaint_id`/`ticket_id`/`priority`/`sla_due_at`/`should_escalate`/`escalation_target`/`tool_result_id` — toàn ID server sinh + trạng thái (`src/tools/create_ticket.py:106-115`). KHÔNG echo `description_raw` |
| `request_human_handoff` | `:945` `flag_human_handoff(…)` | ❌ | không PII: `ticket_id`/`human_handoff_requested`/`created_new_ticket` (+ payload create_ticket ở nhánh tạo mới) (`complaint_intake.py:164,195`) |
| `search_policy` | `:993` `_sanitize_policy_results(…)` | ❌ | trích đoạn tài liệu chính sách công khai, đã sanitize chống injection |

⟹ Phát biểu đúng là: **hai tool trả dữ liệu tài khoản đều scrub; ba tool còn lại không scrub nhưng payload không chứa PII theo cấu trúc.** Trên trục PII, mở lịch sử làm nguồn O3 **không mở kênh rò mới**.

## 2. Trục ① — RÒ ra khách: KHÔNG có kênh mới (ba vế đã cân)

- **Đường ra hạ tầng:** bản vá A chỉ đổi **kênh nguồn của bộ lọc ĐẦU RA** — chạy cục bộ. `ToolMessage` lịch sử vốn đã nằm trong `all_messages` gửi model mỗi lời gọi; không byte nào đi thêm đâu cả. Kho checkpoint (§5.J STATE) không bị đọc/ghi khác đi.
- **Nhiễm chéo người dùng:** lịch sử lấy theo `thread_id = f"{user_id}:{iat}"` — server tự dựng từ claim JWT (`main.py:645`, ô sạch §5.R STATE), client không chạm được ⟹ nguồn lịch sử luôn là hội thoại CỦA CHÍNH khách đó.

## 3. LỖ THẬT TÌM THẤY — kênh rửa số bịa qua NHÁNH ERROR, và nó là lý do của Đ1

**[ĐO] cả 5 tool đều có nhánh** `return {"status": "error", "message": str(e)}` (`:840·:873·:919·:947·:997`), và nhiều `ToolError`/`ValueError` **echo nguyên văn tham số do MODEL tự đặt**:
```
create_ticket.py:42   "complaint_type không hợp lệ: {complaint_type}"
create_ticket.py:44   "scope không hợp lệ: {scope}"
complaint_intake.py:158-161  "ticket_id không tồn tại/không thuộc user: {ticket_id}"
```
Kịch bản rửa: lượt 1 model **bịa** một mã/dãy số, truyền làm tham số tool → tool lỗi, echo mã bịa vào `ToolMessage` → với bản vá A, lượt sau model nhắc lại mã bịa đó **không cần gọi tool** và O3 coi nó là "có trong kết quả tool lịch sử" ⟹ **đúng loại số O3 sinh ra để chặn được cấp giấy thông hành vĩnh viễn trong hội thoại**. (Hiện trạng cũng đã có lỗ này nhưng chỉ sống TRONG MỘT LƯỢT — qua `args` trong `tool_calls_out`, `graph.py:992` — bản vá A kéo dài nó ra cả hội thoại nếu không chặn.)

**Đ1 (BẮT BUỘC):** khi gom `ToolMessage` lịch sử vào kênh nguồn, **loại bỏ payload có `status == "error"`** (hoặc tối thiểu: bỏ trường `message` của chúng). Tất định, một điều kiện lọc, không đổi hành vi ca hợp lệ nào — ba ca chặn-oan trong brief đều dựa trên kết quả tool **thành công**.

## 4. Hai ghi chú KHÔNG chặn (khai để người sau khỏi tưởng chưa ai cân)

- **`search_policy` lịch sử thành nguồn O3:** số trong tài liệu chính sách được nhắc lại xuyên lượt — đúng chủ đích. Rủi ro tài liệu NỘI BỘ lọt kho (ADR-026 chưa thi hành, §5.N STATE) là rủi ro **có sẵn từ trước** ở chính kênh nguồn lượt-này; bản vá A không đổi hạng nó. Không thêm điều kiện.
- **QA/QC:** đặc tả mục 2-QA đã có ca "SĐT bị scrub → PHẢI CHẶN" (chiều KÊU, Luật A). Đề nghị thêm MỘT ca đối chứng cho Đ1: *số bịa nằm trong THAM SỐ/nhánh error của tool lượt trước → PHẢI CHẶN*. Đề nghị, không phải điều kiện chặn — Đ1 đứng độc lập.

## 5. Ranh giới phát biểu

Định hạng này chỉ nói về **bản vá A**. Không phát biểu gì về bản vá B (regex — thuộc Review soi chiều bắt-bịa) và C (log hình dạng — đúng nguyên tắc cấm log nội dung, hoan nghênh). Không đo lại kho checkpoint, không chạm container, 0 token LLM tiêu.

---

## PHỤ LỤC 19/08 (ghi thêm SAU khi PO-agent chấp nhận toàn văn — thân trên giữ nguyên)

Trả lời tường minh hai trục Lead nêu tối 18/08, bằng số đo đã có lúc định hạng nhưng chưa viết đủ vào trang:

**Trục ① (rò ra khách — PII bên thứ ba trong 3 tool chưa scrub): ÂM TÍNH theo cấu trúc.**
[ĐO] payload thành công của cả 3: `create_ticket` = 6 trường ID/trạng thái server sinh (`src/tools/create_ticket.py:106-115`); `request_human_handoff` = 3 trường tương tự (`complaint_intake.py:164,195`); `search_policy` = trích đoạn tài liệu công khai. **Không trường nào mang tên/SĐT/số TK của bất kỳ ai** — nên không có PII bên thứ ba để "câu trước bị chặn nay đi ra". (PII bên thứ ba của ca chuyển nhầm nằm trong `lookup_transaction` — tool ĐÃ che ở tầng tool + scrub.)

**Trục ② (toàn vẹn — ứng viên số một của Lead là `trans_id` trong `create_ticket`): ÂM TÍNH trên đường THÀNH CÔNG, DƯƠNG TÍNH trên đường LỖI.**
[ĐO] result thành công của `create_ticket` **không echo `trans_id`** (liệt kê đủ 6 trường ở trên — không có nó); `flag_human_handoff` chỉ echo `ticket_id` **sau khi đã xác minh tồn tại + thuộc đúng user** (`complaint_intake.py:156-161`) — tức chỉ echo giá trị THẬT. Kênh dương tính duy nhất là **nhánh error echo tham số** (§3) ⟹ Đ1 phủ đúng và đủ.

### PHÁN QUYẾT DẠNG THI HÀNH Đ1 (Lead hỏi 19/08 — allow-list hay deny-list)

**HƯỚNG fail-closed / allow-list: KÝ.** Lead đúng và tôi ký cả phần **vượt** mức Đ1 tôi viết: Đ1 bản gốc là deny-list (`bỏ status=="error"`), và ba đường payload **không mang khoá `status`** (exception thoát ra, parse hỏng, không phải dict) **lọt qua nó** — trong đó nhánh `{"raw": tm.content}` **đã tồn tại sẵn** trong mã (`graph.py:989-991`). Đó là fail-open thật. Đúng lớp ADR-024 đã chốt fail-closed.

🔴 **VỊ NGỮ CỤ THỂ Lead đề nghị — `status ∈ {found, not_found, multiple_matches}` — TÔI BÁC. Nó im lặng loại 2/5 tool.**

```
[ĐO] đếm khoá "status" trong payload THÀNH CÔNG, cả 5 tool, đếm từng tệp:
  lookup_transaction     lookup_transaction.py:175·178·181     CÓ
  get_customer_history   get_customer_history.py:78·89·98      CÓ
  search_policy          rag/search.py:95                      CÓ
  create_ticket          grep '"status"' create_ticket.py  →  0 hit    🔴 KHÔNG CÓ
  request_human_handoff  grep '"status"' complaint_intake.py → 0 hit   🔴 KHÔNG CÓ
                         (:164 và :195 — hai nhánh, cả hai không có)
```

⟹ Allow-list ấy loại đúng **hai payload mang `ticket_id`/`complaint_id`** khỏi nguồn ⟹ ca *"mã hồ sơ của tôi là gì?"* **vẫn bị chặn oan**. Đây **chính là phương án thu hẹp Lead vừa rút**, đi vào bằng một cửa khác — và lần này **không ai thấy**, vì nó không phải một dòng "chỉ gom 2 tool đọc" mà là **hệ quả của một vị ngữ trông trung lập**.

**Và căn cứ ③ của Lead không đỡ được ca này:** *"allow-list hỏng ⟹ chặn oan, thấy ngay"* — chặn oan của O3 biểu hiện bằng `CAU_AN_TOAN`, **đúng triệu chứng cả chiến dịch đang chữa**, và nó chập chờn theo hành vi model. Nó **không** thấy ngay; nó trông y hệt *"bản vá chưa chữa hết"*.

🔴 **Căn cứ ① là chỗ đắt nhất, và nó là một finding riêng: CONTRACT ĐANG MÔ TẢ MỘT THỨ CODE KHÔNG LÀM.**
`contracts/agent-tools.yaml:94` (create_ticket) và `:106` (request_human_handoff) **khai `output.status` enum** — code **không phát khoá đó**. Neo allow-list vào contract nghe chắc chắn **hơn thực tế**. Không cổng nào bắt: INV-09 so **TÊN** tool; [ĐO] `grep "output" tests/test_invariants.py` → **0 hit** ⟹ **lược đồ OUTPUT chưa từng được so.** Cùng hạng mù §5.D2/§5.N của STATE (contract-first canh thứ khai được, không canh khoảng cách khai↔chạy). **Khai ở đây, KHÔNG tự mở rộng làm hôm nay** — mục tiêu ngày là demo lên `main`.

**RÀNG BUỘC TÔI KÝ (định hạng, không thiết kế thay Coder):**
> Vị ngữ phải phân biệt ***payload đến từ ĐƯỜNG THÀNH CÔNG của tool*** khỏi *nhánh lỗi · parse hỏng · không phải dict*, và phải được **đối chiếu với CẢ NĂM hình dạng payload THẬT**, **không đối chiếu với contract** (contract sai ở đúng hai tool này).

**Dữ kiện cho Coder — KHÔNG phải đơn thuốc:** `tool_result_id` là mỏ neo có **nghĩa nghiệp vụ đúng** (có nó ⟹ đã ghi vào bảng `tool_results` thật ⟹ đúng ràng buộc cứng 3), và [ĐO] có mặt ở **4/5** đường: `lookup_transaction.py:195` · `get_customer_history.py:172` · `create_ticket.py:115` · `rag/search.py:97`. **Lỗ đã biết: `complaint_intake.py:164`** (nhánh handoff trên ticket ĐÃ tồn tại) **không có**. Chọn neo nào là việc của Coder; nhưng **neo nào cũng phải chạy qua đủ 5 hình dạng trước khi land**.

---

## CHỮ KÝ Đ1 — 19/08, kiểm trên diff THẬT (đã `git diff`, không nhận tóm tắt)

**Cả hai câu Lead hỏi: ĐẠT.**

1. **Dạng thi hành đúng ràng buộc đã ký.** [ĐO] `graph.py:496-503` (`rap_nguon_o3`): ba `continue` liên tiếp — `json.loads` lỗi → continue · `not isinstance(payload, dict)` → continue · **SHAPE fail-closed đúng, phủ cả ba đường không mang khoá `status`** đã cảnh báo ở §PHÁN QUYẾT. Dòng cuối `payload.get("status") == _TRANG_THAI_LOI_TOOL` → continue = **BRANCH đúng, không phải allow-list theo enum**. Đối chiếu với 8/8 điểm trả lỗi liệt kê trong comment (`customer_tools.py:596,600,818,840,873,919,947,997`) khớp với chính danh sách tôi lập lúc định hạng (§1, §3) — không thêm, không thiếu.
2. **Không có call-site thứ hai.** [ĐO] tự tìm, không dựa Review: `loc_dau_ra` gọi đúng **1 lần** trong toàn bộ production path (`graph.py:1203`), `nguon_tool` dựng đúng **1 lần** qua `rap_nguon_o3` (`:1199`). `run_agent_turn` là entrypoint AI-chat **duy nhất** (`main.py:641`, `grep -rln run_agent_turn src/api/ src/agents/` → chỉ graph.py + main.py gọi thật). Đường nhẹ `triage.py` (câu "alo") — `grep -n "O3\|nguon\|ToolMessage" triage.py` → **0 hit**, không có kênh nguồn song song. Bốn chỗ `"loc_dau_ra": []` khác (`:646·802·919·1020`) là **fallback tĩnh không qua LLM** — comment tại chỗ tự khai "câu do CHÍNH TA viết, không cần lọc", không phải đường vòng.

**Về ba dữ kiện Lead khai kèm:** ① đúng, khớp diff tôi vừa đọc. ② đồng ý xử lý ngoài-phạm-vi-hôm-nay. ③ **không đổi kết luận chữ ký** — đúng như Lead nói, tôi định hạng CƠ CHẾ (đã đọc trong mã, không phụ thuộc cổng nào chạy), độ phủ cổng là việc của QA/QC. Nhưng khai lại cho hồ sơ: *trước khi PO thật merge*, mục "ĐỊNH NGHĨA XONG" của brief cần ca ⑪⑫⑬ **xanh thật**, không chỉ được giao — nếu không, Đ1 đúng trên giấy mà chưa có cổng nào canh nó đúng mãi (đúng câu "nợ, không phải bảo đảm vĩnh viễn" trong chính comment của Coder).

**KÝ: Đ1 THI HÀNH ĐÚNG.** 0 token tiêu, không chạm container.

**Vì sao Đ1 tốt hơn phương án thu hẹp về 2 tool đọc (gợi ý dự phòng của Lead):** thu hẹp sẽ loại `create_ticket` lịch sử khỏi nguồn ⟹ agent nhắc lại `ticket_id`/`complaint_id` của vé vừa tạo ở lượt trước (ca rất phổ biến: *"mã hồ sơ của tôi là gì?"*) lại **bị chặn oan tiếp** — tái tạo đúng cơ chế #3 mà bản vá A sinh ra để chữa. Đ1 giữ được ca đó và vẫn đóng kênh rửa.
