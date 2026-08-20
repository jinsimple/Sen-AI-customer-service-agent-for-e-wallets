# ST2-P0-3/E-09 — trước khi soạn phương án mới: cơ chế đã được PO thật QUYẾT 5 ngày trước, trong ADR-025

> PO-agent giao: soạn 3-4 phương án A/B/C(/D) cho PO thật chọn cơ chế che PII live-chat, kèm một
> hướng gợi ý là "che lúc GHI". **Trước khi soạn — [ĐO] một dữ kiện làm đổi hình dạng cả bài toán:
> PO thật đã ký ADR-025 (15/08) trả lời đúng câu hỏi cơ chế này, và ĐÃ BÁC "che lúc GHI" cho đúng
> hai cửa đang bàn (`messages.content` + `description_raw`).** Theo §5 CLAUDE.md — "PO đã chốt thì
> không bao giờ hỏi lại" — trình DỮ KIỆN này trước, không soạn lại A/B/C như thể chưa có quyết định.
> Không chạm `src/` (đúng ràng buộc 3 PO-agent nêu).

## 1. [ĐO] ADR-025 đã quyết đúng câu hỏi này — trích nguyên văn, không diễn giải lại

`docs/DECISIONS.md:938-965` — **ADR-025, Trạng thái: ĐÃ KÝ TOÀN BỘ, PO thật duyệt 15/08**:

> **Quyết định 1 — Trục phân loại là BẰNG CHỨNG, không phải ai-gõ.**
> **Nhóm A (lời khai — bằng chứng):** `description_raw` + `messages.content`. Khách không sửa lại
> được; là căn cứ giải quyết tranh chấp tiền. **BÁC che-lúc-ghi** — hệ thống tự sửa chữ trong lời
> khai thì bản ghi mất giá trị chứng cứ (NHNN/toà). Cơ chế: mã hoá at-rest + trần độ dài + siết đọc
> need-to-know + retention + che **lúc XUẤT** (log/trace/export — chỗ `scrub_pii` được viết ra, vì
> bản gốc còn).

Hai cửa PO-agent hỏi (`messages.content`, và `description_raw` ở §7 hồ sơ cũ) là **CHÍNH XÁC** hai
cửa ADR-025 gọi tên trong "Nhóm A". Không phải suy diễn tương tự — đúng hai tên biến, đúng dòng.

**Vì sao "che lúc ghi" (một trong ba hướng PO-agent gợi ý, và là khuyến nghị B của hồ sơ 14/08 cũ
`ho-so-quyet-ST2-P0-3-pii-live-chat.md`) không còn là một lựa chọn hợp lệ để đưa ra:** nó chính là
cơ chế ADR-025 QĐ1 bác bằng tên, bằng lý do pháp lý cụ thể (giá trị chứng cứ trước NHNN/toà) —
không phải một trong nhiều lựa chọn ngang nhau, mà là lựa chọn **đã bị loại bằng văn bản đã ký**.

**Đối chiếu ngược — test đang đỏ hỏi đúng cơ chế đã bị bác:** [ĐO]
`tests/test_api/test_live_chat_pii_gap.py:37` — `assert raw_phone not in saved["content"]` = khẳng
định nội dung ĐÃ CHE **trong DB lúc ghi**. Đây đúng là hình dạng ADR-025 bác. **ADR-040
(`docs/DECISIONS.md:2348-2352`, ký 18/08) đã tự phát hiện đúng xung đột này** — nhưng chọn hướng xử
lý là DỜI cổng CI sang deploy-gate, không phải sửa test. Hồ sơ này không lặp lại phát hiện đó
(ADR-040 đã ghi), chỉ nối tiếp: **nếu cơ chế đã quyết, việc còn lại không phải "PO chọn A hay B" —
là "sửa test cho khớp quyết định đã ký, và đóng nốt phần ADR-025 nói cần làm mà CHƯA làm".**

## 2. [ĐO] Đối chiếu ADR-025 Nhóm A với hiện trạng `messages.content` — 5 vế, đo từng vế

| Vế ADR-025 QĐ1 | Hiện trạng `messages.content` | Bằng chứng [ĐO] |
|---|---|---|
| Mã hoá at-rest | ✅ **CÓ, đã xác nhận bằng hành vi** | `2026-08-15`: đọc byte thật qua SQL thô, ciphertext Fernet, không mẩu PII nào (`ho-so-quyet-ST2-P0-3...md` dòng 85-94) |
| Trần độ dài | ❌ **KHÔNG có** | `grep -n "max_length" src/api/schemas.py` → có ở `description_raw=2000`, `note=500`, `message=4000` (agent chat) — **không có trường nào ứng với nội dung tin nhắn live-chat**; `grep -n "record_message\|max_length" src/api/live_chat_ws.py` → không có kiểm tra độ dài trước khi gọi `record_message` |
| Quyền đọc need-to-know Pha 1 (audit mọi lượt đọc) | 🟡 **CÓ cơ chế, nhưng có một khoảng trống ĐÃ được đội tự khai, chưa đóng** | `main.py:177-223` — `audit_log_middleware` ghi `logs/access.log` thật, đang chạy. Nhưng `docs/STATE.md` (mục "R", #3, mở 18/08 bởi PO-agent + security + tech-lead, BA nguồn độc lập) tự khai: *"`access.log` sống sót `recreate` — cơ chế bù DUY NHẤT của Pha 1 ADR-025... chỉ 1 dòng `docker-compose.yml`; `tests/`·`contracts/`·ADR → 0 hit"* — nghĩa là: có ghi log, nhưng **liệu file này có SỐNG SÓT qua lần container recreate hay không thì chưa ai đo/kiểm/khai ở đâu cả**. Đây là gap đã biết, không phải phát hiện mới của hồ sơ này. |
| Retention 5 năm | ❌ chưa cài đặt | ADR-025 QĐ3 **tự khai** cờ "cần tư vấn pháp lý thật xác nhận trước production" — đây là gap **CHẤP NHẬN có chủ đích**, không phải nợ bị bỏ quên |
| Che lúc XUẤT (log/trace/export) | ❌ **KHÔNG áp dụng cho `messages.content` ở BẤT KỲ đâu** | `grep -rn "scrub_pii(" src/` → 4 lần gọi thật trong toàn bộ `src/`: `note` (resolution reject, `main.py:1168`), `LLM callback text` (`langchain_callback.py:67`), `model_input` cho graph (`graph.py:901`), và tham chiếu trong docstring — **không lần nào tham số là `messages.content`, không route đọc transcript nào (`get_handoff_context`, `/live-chat/sessions/{id}/messages`) gọi `scrub_pii`.** Đây là vế duy nhất trong 5 vế ADR-025 đòi hỏi cho Nhóm A mà **hoàn toàn chưa có dòng code nào**, không phải "có nhưng chưa đủ" như vế audit. |

**Tóm một câu:** ADR-025 đã QUYẾT cơ chế (không che-lúc-ghi, che-lúc-xuất). Việc **THI HÀNH** cơ chế
đó cho `messages.content` mới làm được **1/5 vế** (mã hoá). Ba vế còn thiếu hẳn, một vế cố ý hoãn.
**Đây mới là thứ PO cần biết hôm nay — không phải một câu hỏi chính sách mới.**

## 3. `description_raw` (§7 hồ sơ 14/08 hỏi "có gộp không") — ĐÃ GỘP, cùng ngày với ADR-025, không phải câu hỏi mở

Hồ sơ `ho-so-quyet-ST2-P0-3...md` §7/§8.3 (viết 14/08, TRƯỚC ADR-025) hỏi PO "có gộp
`description_raw` vào cùng chính sách live-chat không". **ADR-025 (15/08, một ngày sau) đã tự
trả lời — `description_raw` đứng NGANG HÀNG `messages.content` trong chính định nghĩa "Nhóm A"**,
trích nguyên văn ở §1. Không cần hỏi lại câu §8.3 của hồ sơ cũ — nó đã có câu trả lời, chỉ chưa ai
cập nhật lại hồ sơ 14/08 để nói vậy (hồ sơ đó dừng ở "đính chính 15/08" về vấn đề scrub-hỏng-nghĩa,
chưa nối với ADR-025 ký cùng ngay sau).

## 4. Phương án — KHÔNG phải "chọn cơ chế" (đã chọn), mà "tốc độ đóng 3 khoảng trống thi hành"

Ba lựa chọn dưới đủ 4 vế PO-agent yêu cầu (①che gì/tầng nào ②CSKH gọi lại được không ③NĐ 13/2023
③④chi phí/rủi ro) — nhưng khung câu hỏi đổi từ "cơ chế nào" sang "đóng khoảng trống thi hành với
tốc độ nào", vì cơ chế đã cố định bởi ADR-025.

### Lựa chọn 1 — Đóng đủ 3 khoảng trống trước đợt 150 người thật

① Thêm `max_length` cho nội dung tin nhắn live-chat (ở tầng nhận WS, giá trị cụ thể cần Coder+PO
thống nhất — không đoán số ở đây, chỉ nêu thiếu); gọi `scrub_pii(muc_dich="log")` tại các điểm
ĐỌC/XUẤT (transcript route, `get_handoff_context`, mọi export/DSAR tương lai) — **không sửa
`record_message`**; xác nhận `access.log` sống sót `recreate` bằng một phép đo thật (đóng gap #3
STATE.md).
② CSKH KHÔNG mất khả năng gọi lại — số điện thoại gọi được lấy từ hồ sơ tài khoản qua
`get_handoff_context()`, không từ chuỗi khách gõ tay (đã xác nhận bằng probe thật 14/08, xem hồ sơ
cũ §2 — dữ kiện này KHÔNG đổi, ADR-025 không đụng tới nó).
③ Đạt được: tối thiểu hoá lúc XUẤT (không phải lúc lưu — đúng NĐ 13/2023 nguyên tắc giới hạn mục
đích áp cho việc AI/log truy cập, không áp cho hồ sơ điều tra gốc cần giữ nguyên vẹn làm bằng
chứng). Vẫn hở: retention 5 năm chưa cài (ADR-025 đã tự khai, chờ pháp lý — không phải gap mới).
④ Chi phí: 3 việc độc lập, không đụng schema DB (mã hoá giữ nguyên), rủi ro chính là **rủi ro ĐÃ
biết từ 15/08**: registry `scrub_pii(muc_dich="log")` là registry ĐẦY ĐỦ (giữ Phone/Date, không bị
thu hẹp như `model_input`) — **CHƯA có phép đo tỉ lệ chặn-nhầm của chính registry "log" trên văn
bản live-chat thật**, chỉ có phép đo cũ cho `model_input` (D', 1.61%) và cho `note` (40%, đã sửa
một phần bằng bộ lọc `_plausible_person_span` áp chung cho mọi NER, nhưng CHƯA đo lại con số sau
sửa). 🔴 **Không lặp lại lỗi Aug-15**: đo tỉ lệ chặn-nhầm của registry "log" trên mẫu văn bản
live-chat/nghiệp vụ THẬT trước khi bật cho `messages.content`, đúng Luật M (xác nhận không phải
bằng chứng).

### Lựa chọn 2 — Đóng 2 khoảng trống rẻ ngay, hoãn export-scrub tới khi đo xong registry "log"

Làm `max_length` + xác nhận `access.log` sống sót `recreate` ngay (chi phí thấp, không phụ thuộc
đo lường PII). **Hoãn** gọi `scrub_pii` tại điểm xuất cho tới khi có phép đo tỉ lệ chặn-nhầm của
registry "log" trên văn bản live-chat — tránh lặp kịch bản 15/08 (mang lỗi biến-nghĩa-câu vào một
kênh CSKH đọc trực tiếp để phục vụ khách, hậu quả nặng hơn `note` vì đây là kênh THỜI GIAN THỰC,
không có bước duyệt trước khi CSKH đọc). ③ Đạt tối thiểu hoá muộn hơn Lựa chọn 1 nhưng không đưa
một cơ chế chưa đo vào một kênh trực tiếp-tới-khách. ④ Rẻ hơn, rủi ro thấp hơn, nhưng gap "che lúc
xuất" (vế ADR-025 chưa có dòng code nào) tồn tại lâu hơn.

### Lựa chọn 3 (khuôn ADR-040) — Chấp nhận rủi ro CÓ KHAI cho phần còn thiếu, không vá trước 150 người

Ghi nhận CHÍNH XÁC phần rủi ro còn lại (không phải "chưa che PII" — đã che 1/5 vế bằng mã hoá, và
cơ chế đã quyết) là: thiếu trần độ dài + thiếu che-lúc-xuất + độ bền `access.log` chưa xác nhận.
Khai rủi ro cụ thể, ai ký, thời hạn hết hiệu lực (vd "trước đợt 150 người thật phải đóng, không
được trôi tiếp" — đúng tinh thần ADR-011 đã áp cho rủi ro tồn dư khác). ④ Rẻ nhất trước mắt, nhưng
ADR-040 QĐ2 đã ghim luật: *"chấp nhận rủi ro cho main KHÔNG được lặng lẽ trở thành chấp nhận rủi ro
cho PRODUCTION"* — chọn lựa chọn này cho `main` được, **không được** cho gate deploy khi 150 người
thật chạm hệ thống, trừ khi PO thật ký lại rõ ràng ở đúng cổng đó.

**Khuyến nghị (không tự chốt): Lựa chọn 2.** Lý do có thể đổi ý: nếu Coder/tester đo được registry
"log" trên mẫu live-chat thật và tỉ lệ chặn-nhầm thấp (gần mức D' 1.61%, không phải mức note 40%
cũ) TRƯỚC đợt 150 người, thì không có lý do hoãn — chuyển thẳng sang Lựa chọn 1. Khuyến nghị hoãn
chỉ đứng vững chừng nào con số đó CHƯA ĐƯỢC ĐO.

## 5. Câu hỏi gộp ADR-045 (checkpoint) — PO-agent gợi ý gộp, câu trả lời: gộp PHÂN LOẠI, không gộp CƠ CHẾ

Không thể gộp CƠ CHẾ vá — hai cửa hỏng theo hai cách khác nhau:
- `messages.content`: **CÓ** mã hoá at-rest, thiếu che-lúc-xuất → vá còn lại là thêm `scrub_pii` ở
  điểm đọc.
- Checkpoint (`checkpoint_blobs`, ADR-045 seed, `2026-08-20-danh-gia-kho-checkpoint...md`):
  **KHÔNG có mã hoá at-rest nào**, PII (kể cả `description_raw` y hệt tool call) nằm plaintext
  trong Postgres — vá là ở tầng `serde` khác hẳn, không liên quan `scrub_pii`.

**Nhưng PHÂN LOẠI thì gộp được, và nên gộp — đây là chỗ đề xuất của PO-agent đúng:** nội dung
khách gõ cho AI (đi vào checkpoint qua `HumanMessage`) và nội dung khách gõ cho CSKH người thật
(đi vào `messages.content`) là **CÙNG MỘT LOẠI DỮ LIỆU** theo đúng tiêu chí ADR-025 QĐ1 dùng để
định nghĩa "Nhóm A" — "lời khai, khách không sửa lại được, là căn cứ giải quyết tranh chấp". Không
có lý do phân loại hai kênh này khác nhau chỉ vì bên nhận là người hay là model.

**Đề nghị cụ thể:** một quyết định ĐÍNH KÈM (không phải ADR-045 độc lập tranh luận lại từ đầu) —
**mở rộng định nghĩa "Nhóm A" của ADR-025 QĐ1 để tự động phủ nội dung khách gõ được lưu trong
checkpoint LangGraph**, cùng 5 vế cơ chế (ở đây: mã hoá at-rest CHƯA có — là khoảng trống cần vá
đầu tiên, khác thứ tự ưu tiên với `messages.content` nơi mã hoá đã xong). PO thật quyết **một câu
phân loại**, hai đội (live-chat + checkpoint serde) tự suy ra cơ chế theo đúng ADR-025 đã có sẵn —
đúng mục tiêu "quyết một lần" PO-agent nêu, chỉ khác ở **cấp độ nào được gộp** (phân loại, không
phải lịch vá).

## Tổng kết cho PO thật (qua PO-agent)

**Không cần chọn lại cơ chế cho `messages.content`/`description_raw` — đã chọn, ADR-025, 15/08,
đã ký.** Việc cần quyết hôm nay hẹp hơn nhiều:
1. Tốc độ đóng 3 khoảng trống thi hành (Lựa chọn 1/2/3 ở §4) — khuyến nghị **2**, đổi ý nếu có số
   đo registry "log" sớm.
2. Có mở rộng phân loại "Nhóm A" của ADR-025 sang dữ liệu checkpoint không (§5) — khuyến nghị
   **có**, dạng một quyết định đính kèm ngắn, không phải ADR-045 tranh luận lại nguyên tắc.
3. Việc ĐÃ mở và KHÔNG cần quyết lại: retention 5 năm (đã tự khai chờ pháp lý), gộp
   `description_raw` vào Nhóm A (đã gộp từ 15/08).

Không có tay ai của security chạm `src/` trong hồ sơ này — toàn bộ là đối chiếu tài liệu + đo bằng
`grep`/đọc mã, không sửa gì.
