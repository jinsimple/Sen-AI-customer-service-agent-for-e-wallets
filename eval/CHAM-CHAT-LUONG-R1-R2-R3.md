# Chấm chất lượng R1 · R2 · R3 — kịch bản PO thật

> Vai: **tester** · 17/08 · **0 lượt LLM** (đọc lại bản ghi đã có).
> Nguồn: `/app/logs/R{1,2,3}_po.json` trên volume `fin05`.
> Băm mã nguồn cả ba lượt: `1df2e1c3a5e6` (`sha256-noi-dung-src-py-da-sap-xep-12`)
> — **giống nhau cả ba** ⟹ ba lượt đo trên **cùng một vật**, điều kiện tôi gắn
> trước R1 được thoả.
>
> ⚠️ **Phạm vi, giữ nguyên từ coder, không làm nhẹ:** chạy qua `run_agent_turn`
> ⟹ **cổng OTP bị bỏ qua** · `lookup_transaction` **không tìm thấy giao dịch**
> nào ⟹ mọi số là **cận dưới**.

## 🔴 ① Hình dạng luồng — 1/5 khớp, GIỐNG HỆT ở cả ba lượt

| # | kỳ vọng (PO viết) | R1 | R2 | R3 | |
|---|---|---|---|---|---|
| 1 | — (hỏi lại) | `get_customer_history` | nt | nt | ✗ |
| 2 | — (yêu cầu OTP phiên) | `lookup_transaction` | nt | nt | ✗ |
| 3 | `lookup_transaction` | `lookup_transaction` | nt | nt | ✅ |
| 4 | **— (từ chối, giải thích)** | `create_ticket` ×2 | ×2 | ×1 | 🔴 |
| 5 | `create_ticket` + `request_human_handoff` | chỉ `request_human_handoff` | nt | nt | ✗ |

**Lượt 4 là finding, không phải lệch nhãn.** Lượt 4 khách hỏi *"huỷ giao dịch
được không?"* — khách **chưa đồng ý** tạo yêu cầu; đồng ý xảy ra ở lượt 5
(*"Ừ tạo đi"*). Agent **tạo vé trước khi khách đồng ý**, và vé đó là vé THẬT
(`TCK-6c3f32707b0c` · `TCK-fe9ff34f8279` · `TCK-2e7f40ebe9cb`, `Ticket +1` mỗi
lượt).

Cộng thêm: mô tả tool `create_ticket` — nguyên văn — nói *"bước **CUỐI CÙNG**
của quy trình, gọi **ĐÚNG MỘT LẦN** cho mỗi khiếu nại"*. Ở R1 và R2 nó được gọi
**hai lần trong một lượt**. Cả hai vế của câu đó đều bị vi phạm cùng lúc.

> **Hệ quả nghiệp vụ:** một khách hỏi *"huỷ được không?"* rồi **đổi ý và thoát**
> vẫn để lại một hồ sơ khiếu nại trong hàng chờ CSKH. Hỏi ≠ khiếu nại.

Lượt 5 lệch là **hệ quả** của lượt 4, không phải lỗi riêng: vé đã tồn tại nên
agent chỉ còn `request_human_handoff`.

Lượt 1–2 lệch nhưng tôi **không tính là finding**: cổng OTP bị harness bỏ qua
nên lượt 2 không có cơ hội yêu cầu OTP, và lượt 1 gọi `get_customer_history`
là chủ động tra — sai bảng, không sai nghiệp vụ.

## ③ R1 ↔ R3 — câu hỏi "tắt suy luận có kém đi không"

**Trả lời: KHÔNG kém. Và `InvestigationLog +4` KHÔNG có nghĩa là điều tra kỹ hơn.**

    R1  6 lời gọi tool · 11 lời gọi model · 81s · ToolResult +4 · InvLog +1
    R2  6                11               · 74s · ToolResult +4 · InvLog +1
    R3  5                10               · 37s · ToolResult +4 · InvLog +4

Hai cách đọc PO nêu — *"R3 điều tra kỹ hơn"* vs *"R3 lan man hơn"* — **cả hai
đều sai**, và phân biệt được mà **không cần đọc transcript**:

> **`ToolResult` tăng đúng `+4` ở CẢ BA lượt.** Lượng hoạt động tra cứu **y hệt
> nhau**. R3 không tra nhiều hơn, cũng không lan man hơn — nó tra **giống hệt**,
> chỉ **ghi log nhiều hơn** về cùng một việc.

⟹ `+4` là chênh lệch **ở tầng GHI LOG**, không ở tầng HÀNH VI. Nếu đọc nó thành
"điều tra kỹ hơn" thì ta vừa gán một kết luận hành vi cho một hiện tượng ghi
chép — đúng lớp lỗi đã bắt nhiều lần hôm nay.

**Và R3 hơn ở chỗ ít ai ngờ:** ở lượt 4, R1/R2 gọi `create_ticket` **hai lần**,
R3 gọi **một lần**. Tắt suy luận làm agent **bớt** hành vi thừa, không thêm.
Cộng với 37s vs 81s (**nhanh gấp 2,2 lần**).

⚠️ **k=1 mỗi cấu hình**, và sàn nhiễu đo được là **≥3 lời gọi model/lần chạy**
(11 vs 14 cùng kịch bản). Chênh `11 → 10` **nằm trong nhiễu**, không đọc được.
Chênh **6 → 5 lời gọi tool** và **81s → 37s** thì lớn hơn nhiễu đó — nhưng vẫn
là một điểm, cần lặp lại trước khi công bố.

## 🔴 ② Truy vết (ràng buộc cứng 3) — CHƯA CHẤM ĐƯỢC, và có một lỗ đo được

**Chưa chấm được** vì bản ghi cắt `reply` ở **đúng 100 ký tự** mọi lượt:

    'Mình hiểu bạn đang rất lo lắng vì số tiền lớn. Mình đã thử tra với mã
     482913 nhưng vẫn chưa tìm thấy'

Không đọc được câu trả lời đầy đủ ⟹ **không kiểm được** số tiền/trạng thái agent
nêu có truy về `tool_results` không. Đây là tiêu chí trung tâm của cả chuỗi R,
và dữ liệu **không đủ** để chấm nó.

**Nhưng lỗ này thì đo được từ chính con số:**

    R1  6 lời gọi tool → ToolResult +4   ⟹ 2 lời gọi KHÔNG sinh bản ghi
    R2  6                            +4   ⟹ 2
    R3  5                            +4   ⟹ 1

> Chuỗi truy vết của ràng buộc cứng 3 là
> `tool_results → investigation_logs → resolutions`. Nếu **một phần lời gọi tool
> không sinh `ToolResult`** thì mắt xích đầu **thủng theo thiết kế**, không phải
> theo sự cố.

Cùng họ với `investigation_logs = 0` tôi báo sáng nay — đó là mắt xích **thứ
hai**; đây là mắt xích **thứ nhất**.

## Việc cần làm

1. **coder** — vì sao `create_ticket` chạy ở lượt 4 khi khách chưa đồng ý, và
   vì sao gọi hai lần trong một lượt. Đây là finding sản phẩm, không phải lệch
   nhãn.
2. **coder** — bỏ cắt 100 ký tự trong bộ ghi log R, hoặc ghi thêm trường
   `reply_day_du`. Không có nó, tiêu chí ② **không chấm được ở bất kỳ lượt R
   nào**, kể cả lượt sau.
3. **PO** — `2 lời gọi tool không sinh ToolResult` thuộc cùng hồ sơ ADR-029
   mục 2 (`investigation_logs`) đang chờ PO thật.
4. **tôi** — chưa chấm ② . Không báo "đạt", không báo "trượt". `khong_do_duoc`.
