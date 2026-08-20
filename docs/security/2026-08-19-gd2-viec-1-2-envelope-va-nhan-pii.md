# GĐ2 — Việc ①② của Bảo Mật (envelope schema + finding nhãn PII lộ UI)

> 19/08/2026. Theo `docs/giao-viec/2026-08-19-gd2-envelope-null-va-e2e-ui.md` mục 3-Bảo Mật.
> 0 token LLM, không chạm container.

## Việc ① — `tool_calls: None → []` + siết schema: XÁC NHẬN không mở bề mặt mới

**[ĐO] `/agent/chat` (`main.py:609-647`) hiện KHÔNG có `response_model`** — trả thẳng dict của
`run_agent_turn()`, FastAPI serialize nguyên văn, 0 validate. `schemas.py` **0 hit** `tool_calls`.
Đúng như brief mô tả — đây chính là lý do server cứ 200 với `null`.

**Tiên nghiệm của Lead đúng: thu hẹp hợp đồng là chiều an toàn, đã kiểm hai điểm cụ thể:**
1. **500 không lộ thêm gì.** `app = FastAPI(...)` không đặt `debug=True`, không có
   `exception_handler` riêng cho lỗi validate response. Theo hành vi mặc định Starlette,
   `ResponseValidationError` (path chưa từng chạy vì chưa có schema) sẽ thành 500 chung chung —
   không kèm stack trace, không kèm giá trị field đã gửi. **Không có kênh rò dữ liệu mới.**
2. **Đường 500 mới KHÔNG đổi ai đọc được cái gì** — nó chỉ đổi mã trạng thái của đúng những lượt
   ĐANG vỡ (4 envelope `None`), và sau khi Coder vá 4 dòng thì không lượt nào còn rơi vào đó nữa
   trên đường hạnh phúc + fallback đã biết. Đường **chưa biết** (tool thứ 6, nhánh mới) sẽ **500 rõ
   ràng thay vì 200-rồi-vỡ-ở-client** — đúng hướng ADR-024 (fail-closed), và đây là hướng ta muốn.

**MỘT ĐIỀU KHAI (không chặn, nhưng Coder cần biết trước khi viết schema):** dict thật của
`run_agent_turn` mang **≥10 khoá** (`reply`, `tool_calls`, `ticket_id`, `should_escalate`, `usage`,
`loc_dau_ra`, `tin_hieu_lo_chi_thi`, `goi_y_handoff`, `duong`, `ly_do_fallback`, + trường eval).
Nếu `ChatResponse` khai **thiếu** một khoá frontend đang dùng, `response_model` sẽ **âm thầm cắt**
field đó khỏi response (hành vi lọc mặc định của FastAPI) — tái tạo **đúng lớp lỗi đang được vá**
(envelope hợp đồng lệch, phát hiện trễ) nhưng ở một trường khác. Đây là dữ kiện cho Coder/Review đối
chiếu diff, không phải điều kiện tôi đặt ra.

**KẾT LUẬN VIỆC ①: KHÔNG mở bề mặt mới. Xác nhận.**

## Việc ② — Định hạng finding nhãn PII lọt UI

### Phân định của Lead — ĐÚNG MỘT PHẦN. Sửa lại tầng gây lỗi (không đổi kết luận cuối)

Lead viết: *"lỗi nằm ở TẦNG HIỂN THỊ"*. **[ĐO] không đúng — không có tầng hiển thị nào để sửa theo
nghĩa thay chuỗi cố định.** Cơ chế thật:

```
[ĐO] graph.py:705   agent.invoke({"messages": [HumanMessage(content=scrub_pii(message) or message)]}, …)
```

`scrub_pii()` (`src/observability/pii.py`) chạy trên **CHÍNH LỜI KHÁCH GÕ**, TRƯỚC khi đưa vào
`HumanMessage` — tức chuỗi `"[PERSON_VN] chưa tới người nhận…"` **là nội dung THẬT model đọc được
làm lời khách**, không phải một chuỗi cố định nào đó bị in nhầm ra màn hình. Model trả lời tự nhiên
bằng cách diễn giải lại đúng thứ nó vừa đọc — nó **không biết** `[PERSON_VN]` là một placeholder kỹ
thuật, với nó đó chỉ là một phần của câu khách nói.

⟹ **Không có "chuỗi cố định" nào để hoán đổi ở tầng render.** Sửa đúng chỗ phải là MỘT trong hai:
- dạy model (system prompt) *"gặp mã dạng `[XXX]` trong lời khách thì diễn đạt lại tự nhiên, đừng lặp
  nguyên văn"* — rẻ, nhưng phụ thuộc hành vi model (không tất định);
- hoặc một lượt lọc/thay thế TRÊN OUTPUT của model (giống O1-O4) bắt mẫu `\[[A-Z_]+\]` rồi paraphrase
  — tất định hơn, cùng họ với `output_filter.py` nhưng **chưa có cổng nào ở đó biết mẫu này tồn tại**:
  [ĐO] `grep -n "PERSON_VN\|ORGANIZATION\|\[PERSON\]" src/agents/output_filter.py` → **0 hit**.

**Không đổi định tuyến của PO-agent** (sổ việc sau merge, UX/UI + tech-lead, không làm hôm nay) — chỉ
đổi MÔ TẢ tầng, để người nhận việc không đi tìm ở frontend/rendering (chỗ không có gì để sửa).

### Bộ scrub KHÔNG SAI — xác nhận đúng như Lead phân định

`Tien`/`minh` không dấu khớp cả tên riêng thật lẫn đại từ nhân xưng — nguyên tắc *"che nhầm còn hơn
để lọt PII thật"* (playbook PII giai đoạn 3, Luật L của dự án) áp đúng. **Không nới bộ scrub.**

### Trả lời câu hỏi OPSEC của Lead: rò rỉ nhãn có tiết lộ gì về bộ dò để giúp né tránh không?

**KHÔNG đáng kể — ba lý do, không phải một cảm giác:**

1. **Đây không phải một biên giới cấp quyền.** `scrub_pii()` ở `graph.py:705` tối thiểu hoá dữ liệu
   ĐẦU VÀO gửi cho LLM (ADR-010) — nó không gác một quyết định cấp quyền hay che PII của NGƯỜI KHÁC.
   Biết cơ chế này tồn tại không giúp ai đọc được dữ liệu người khác; tại đa "lợi ích" của việc né nó
   là chính lời khách tự gõ (tên của chính họ) đi thẳng vào LLM — không phải phần thưởng cho kẻ tấn công.
2. **Tên nhãn không phải bí mật.** `PERSON`/`ORGANIZATION` là taxonomy chuẩn công khai của Presidio
   (thư viện nguồn mở, tài liệu công khai); `PERSON_VN` chỉ thêm một chữ hậu tố lộ "có bộ nhận diện
   tên tiếng Việt riêng" — không lộ ngưỡng, không lộ danh sách từ khoá, không lộ cách phối hai lớp
   regex+NER (Luật L). Không đủ để dựng câu né.
3. **Cơ chế bảo vệ dữ liệu NGƯỜI THỨ BA (rủi ro thật) KHÔNG bị đụng.** [ĐO] `_scrub_pii_cho_llm`
   (che sender/receiver trong kết quả tool, `customer_tools.py:495`) dùng **định dạng che tự nhiên**
   (`mask_full_name` → `"T. H. Trang"`, `mask_phone` → `"090***4567"`, `masking.py:17-45`) — KHÔNG
   phải placeholder ngoặc vuông. Cơ chế đó **không cùng họ lỗi** với cái đang bàn: nếu nó bị model lặp
   lại nguyên văn, khách đọc ra một cái tên bị che tự nhiên, không đọc ra một token kỹ thuật vỡ giao
   diện — và quan trọng hơn: không lộ CÁCH bộ che đó hoạt động.

**KHÔNG kết luận:** ❌ đây là lỗ bảo mật cấp cao — nó là lỗi trải nghiệm/toàn vẹn hiển thị. ❌ cần vá
gấp trước demo — PO-agent định tuyến đúng, giữ nguyên (sổ nợ sau merge).

---

🔴 **NIÊM 20/08 — mức độ "sổ nợ, không gấp" ở trên ĐÃ LỖI THỜI, đọc kèm chuỗi sau trước khi tin nó.**
Đây là phát hiện ĐẦU TIÊN trong ngày về nhãn scrub lọt ra — lúc đó phạm vi quan sát được là MỘT case
UI (`[PERSON_VN]`), hợp lý để xếp mức thấp. Cùng ngày, phạm vi mở rộng gấp bội qua chuỗi phát hiện
sau, đọc theo đúng thứ tự:
1. `2026-08-19-gd4-dinh-hang-scrub-pii-model-input.md` — PO thật tự bắt lỗi UI, lộ ra đây không phải
   một case mà là **~50% MỌI câu khách gõ** bị chèn nhãn sai (không riêng PII, cả từ thường).
2. `2026-08-19-quyet-dinh-bien-du-lieu-regex-only-model-input.md` — quyết định biên dữ liệu, dựng lại
   toàn bộ cơ chế scrub cho đường model-input (phương án D').
3. `2026-08-19-scrub-ba-duong-va-kien-truc-tham-so.md` — kiến trúc hai-registry thay thế cơ chế cũ.

**File NÀY vẫn đúng ở phần KỸ THUẬT** (tên `[PERSON_VN]` không rò cách bộ dò hoạt động, cơ chế che
người thứ ba không bị đụng) — chỉ riêng CÂU MỨC ĐỘ ở trên là thứ đã bị vượt qua. Đừng dừng lại đọc
"sổ nợ, không gấp" mà không đọc tiếp ba file trên.
