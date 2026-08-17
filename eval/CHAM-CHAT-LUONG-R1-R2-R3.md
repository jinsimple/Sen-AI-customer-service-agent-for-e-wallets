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

## 🔴 ĐÍNH CHÍNH BẮT BUỘC — reply lượt 4 KHÔNG phải lời model

> Thêm 17/08 sau điều tra của coder. Đọc dòng này **trước** mọi nhận xét về nội
> dung lượt 4 ở trên.

Câu trả lời lượt 4 trong bản ghi R là **mẫu thay thế của `output_filter`**,
không phải câu model nói. Harness lưu bản **SAU lọc**; nó không lưu nhóm-lọc-
nào-khớp, và không lưu bản gốc (cờ giữ-bản-gốc fail-closed, cố ý).

Coder kiểm chiều ngược trước khi kết luận: **bốn câu từ-chối ĐÚNG chạy qua bộ
lọc — cả bốn giữ nguyên** ⟹ bộ lọc **không chặn oan chủ đề này** ⟹ câu model
thật sự nói **đã khớp một nhóm lọc**, và **ta không biết nó nói gì**.

⟹ Mọi nhận xét về **NỘI DUNG** lượt 4 — lượt từ chối, "ca khó" theo PO — trong
**cả ba vòng R** đọc trên một bản đã bị thay. Cùng hạng `khong_do_duoc` với
tiêu chí ②, **khác nguyên nhân**: ② thiếu dữ liệu vì bị cắt, đây là **có dữ
liệu nhưng dữ liệu nói về một vật khác**.

> **Một phép đo ghi lại đúng bản ĐÃ BỊ SỬA, rồi ta đi hỏi vì sao nó bị sửa.**

⚠️ Phần **TOOL** của lượt 4 **không bị ảnh hưởng** — `create_ticket` chạy thật,
vé thật, `Ticket +1` trong CSDL. Finding ① đứng nguyên; chỉ nhận xét về **lời
văn** là không đọc được.

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

1. **coder** — ĐÃ TRẢ LỜI, và finding tách làm **HAI, khác loại**:
   · **tạo vé trước đồng ý = model TUÂN prompt.** Tiền đề bước 4 toàn về ĐỘ
     ĐẦY ĐỦ DỮ LIỆU, **không tiền đề nào là SỰ ĐỒNG Ý**. Thuộc F-31/32, nay có
     ca tái hiện **3/3**. Câu UX (chờ đồng ý hay không) PO cầm.
   · **gọi hai lần = model VI PHẠM chỉ dẫn tường minh** (*"ĐÚNG MỘT LẦN"* —
     rõ, không mâu thuẫn với gì). Thêm chữ không chữa được cái đã nói rõ.
   ⟹ **Hai loại, hai bản vá. Gộp chúng là sửa prompt rồi tưởng xong cả hai.**
2. **coder** — bỏ cắt 100 ký tự trong bộ ghi log R, hoặc ghi thêm trường
   `reply_day_du`. Không có nó, tiêu chí ② **không chấm được ở bất kỳ lượt R
   nào**, kể cả lượt sau.
3. **PO** — `2 lời gọi tool không sinh ToolResult` thuộc cùng hồ sơ ADR-029
   mục 2 (`investigation_logs`) đang chờ PO thật.
4. **tôi** — chưa chấm ② . Không báo "đạt", không báo "trượt". `khong_do_duoc`.

---

## 🔴 BỔ SUNG 17/08 — GIẢ ĐỊNH "CHỐNG-TRÙNG TẦNG CODE GÁNH" LÀ **SAI**

Đội đang dựa vào một giảm nhẹ: *"model gọi `create_ticket` hai lần, nhưng
chống-trùng tầng code gánh — 2 gọi → 1 ghi, cả ba vòng R"*. Tôi đi dựng cổng
canh cơ chế đó, và **cơ chế đó không tồn tại**.

Phép thử, **0 lượt LLM**, gọi thẳng tool trên `fin05do`:

    CÙNG guard, cùng tham số, gọi 2 lần   →  Δcomplaints = 2 · Δtickets = 2
                                             TCK-59807a7a80e1 · TCK-e694e8dba004
    KHÁC guard, cùng tham số, gọi 2 lần   →  Δcomplaints = 2 · Δtickets = 2
                                             TCK-6e24656773b9 · TCK-6d34e9dc1c0e

**Không có chống-trùng ở tầng tool.** Hai lời gọi ⟹ hai hồ sơ khiếu nại, kể cả
khi dùng chung `TurnGuard` và tham số giống hệt từng chữ.

⟹ Việc R1/R2 chỉ sinh **một** vé dù gọi hai lần **KHÔNG phải do chống-trùng**.
Nguyên nhân thật **chưa biết** — lời gọi thứ hai có thể đã lỗi mà bản ghi chỉ
lưu lời gọi chứ không lưu kết quả. Đây là chỗ phải **điều tra**, không phải chỗ
để yên tâm.

> **Một giảm nhẹ chưa ai đo là một giảm nhẹ chưa tồn tại.** Nó nguy hơn không
> có giảm nhẹ nào, vì nó làm finding gốc bị hạ hạng.

**Hệ quả cho finding "gọi hai lần":** nó **không** phải chuyện chỉ-tốn-một-dòng-
log. Trên đường thật, một lượt model gọi hai lần sẽ đẩy **hai** hồ sơ khiếu nại
vào hàng chờ CSKH cho **một** sự việc — và khách chỉ được báo **một** mã vé.

**Dấu vết phép thử này để lại** (khai đủ, Luật 15 điều kiện ④): **4 vé** trên
`fin05do`, `description_raw` mang tiền tố `[DO-LUONG cong-chong-trung]`:
`TCK-59807a7a80e1` · `TCK-e694e8dba004` · `TCK-6e24656773b9` · `TCK-6d34e9dc1c0e`.
Tôi **không xoá** — chúng là vật chứng của chính finding này. Dọn được bất cứ
lúc nào bằng bốn mã trên, sau khi coder và PO đọc xong.


---

## 🔴 BỔ SUNG — `investigation_logs` RỖNG được TÁI LẬP TRÊN `fin05`, finding ĐỨNG

> 17/08, sau một vòng tôi suýt tự rút nhầm finding của mình.

Tôi từng định **rút** phần *"`investigation_logs` rỗng ⟹ chuỗi truy vết đứt ở
mắt xích đầu"*, vì thấy `fin05do` có `investigation_logs = 0` **toàn bảng** và
kết luận đó là **artefact ngăn xếp**. Coder chặn lại, và họ đúng:

    tôi thấy   fin05do  tool_results: CHỈ create_ticket · investigation_logs 0
    tôi suy    ⟹ ngăn xếp này không GHI ⟹ mọi phép đo truy vết ở đó vô giá trị
    coder đo   gọi thẳng tool trên fin05do → ToolResult Δ=+1, kể cả status=not_found
    ⟹ cơ chế GHI hoạt động. Cái tôi thấy là **VẮNG MẶT LƯU LƯỢNG**, không phải
      vắng mặt cơ chế.

**Tôi suy một cơ chế từ một con số đếm** — đúng lớp lỗi coder mắc sáng nay với
*"chống-trùng đang gánh"*, cùng khuôn, **ngược dấu**: họ suy *"đếm ra 1 ⟹ có cơ
chế"*, tôi suy *"đếm ra 0 ⟹ hỏng cơ chế"*.

### Và phép đo quyết định, trên `fin05` — ngăn xếp CÓ 93 dòng `investigation_logs`

Một lượt fallback thật, đo hiệu số từng bảng:

    Δcomplaints = +1 · Δtickets = +1 · ΔToolResult = +1 · **ΔInvestigationLog = +0**
    vé TCK-4c5165e91770 · type=other · scope=unknown
    log: `agent_turn_timeout` · total_tokens = 0 · không tool_calls nào

⟹ **Finding ĐỨNG, và giờ đã tái lập trên ngăn xếp có lưu lượng thật.** Nhánh
fallback ghi vé **mà không ghi một dòng điều tra nào** — không phải vì ngăn xếp
không ghi được (nó ghi 93 dòng cho các lượt đi hết đường bình thường), mà vì
`write_investigation_logs_for_ticket` nằm **sau** chỗ nhánh fallback `return`.

**Hai dân số khác nhau, không phải hai kết quả khác nhau cho cùng câu hỏi.**

### Điểm tốt đo được cùng lượt

`scope = unknown` ✅ — bản vá của coder giữ đúng trên đường fallback ở `fin05`,
không chỉ ở `fin05do`. Trước đây chỗ này ghi `internal_wallet` bịa.
