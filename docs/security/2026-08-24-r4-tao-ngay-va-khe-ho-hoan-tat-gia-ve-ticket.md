# ① Soát an ninh luật hỏi mới (R1-R5 + finding-1 "tạo ngay") — 1 khe hở thật, cùng hình ADV-041, khác miền

🔴 **NIÊM 24/08 — CA "HIẾM" TRONG FINDING GỐC THỰC RA LÀ CA THƯỜNG XUYÊN NHẤT.** Kịch bản §2 dưới
đây mô tả "OTP hết hạn GIỮA hội thoại" như một ca biên. Dữ kiện mới: bug frontend khiến
`otp_verified_at` **luôn null qua UI thật** (chưa từng tươi, không phải hết hạn giữa chừng) —
nghĩa là **MỌI lượt `create_ticket` qua UI thật, từ trước tới nay, đều rơi đúng vào nhánh lỗi này**,
không phải một ca hiếm. Đề nghị nâng ưu tiên Lớp 1 (đã giao Coder) + O5 (đang xếp hàng sau 1A/1B)
lên TRƯỚC hoặc ĐI CÙNG bản vá token — nếu bản vá token land trước mà hai lớp phòng vệ này chưa
xong, sẽ có cửa sổ nơi tạo vé lần đầu THẬT SỰ thành công qua UI đúng lúc phòng vệ hoàn-tất-giả chưa
sẵn sàng. Toàn văn: `2026-08-24-goc-bao-mat-bug-token-otp-va-tam-quan-trong-doi-cua-hai-finding.md`.
Nội dung gốc dưới đây GIỮ NGUYÊN — kết luận kỹ thuật không đổi, chỉ đổi MỨC ƯU TIÊN.

> Việc PO-agent giao 24/08: có luật nào trong prompt mới đẩy agent VƯỢT/LÁCH rào xác thực không.
> Trọng tâm nêu sẵn: luật "khách đồng ý ⟹ tạo vé NGAY" đứng cạnh cổng OTP step-up của
> `create_ticket`. Kết luận: **cổng OTP không bị lách — nó vẫn tất định, agent không có đường vượt
> qua bằng lời**. Nhưng có **một khe hở diễn đạt sai thật, đã kiểm bằng đọc mã, chưa từng đo bằng
> LLM thật** — nằm đúng hình dạng một finding đã đóng 5 ngày trước (ADV-041) nhưng ở MIỀN KHÁC.

## 1. Cổng OTP — [ĐO] tất định thật, hai lớp, không có đường LLM lách

`src/agents/tools/customer_tools.py:918-921` — `create_ticket` kiểm `otp_verified_at`/
`_otp_fresh(..., OTP_STEPUP_FRESH_MINUTES)` **TRƯỚC KHI** gọi `create_ticket_with_fraud_check`,
return thẳng `_OTP_REQUIRED_ERROR`/`_OTP_EXPIRED_ERROR` (dict `{"status":"error",...}`, KHÔNG
raise) nếu thiếu/hết hạn. `otp_verified_at` **đóng cứng trong closure lúc dựng tool cho lượt chat
này** (truyền thật từ `current_user.otp_verified_at`, `graph.py`) — model không có tham số nào để
tự khai "tôi đã xác thực rồi", không có tool nào để tự xin OTP. Đây đúng nguyên tắc ràng buộc cứng
2 (AI không vượt cấp): gate sống ở Python, không sống ở lời agent nói.

Route HTTP `/tools/create_ticket` **cũng** có `Depends(require_otp_verified)` cùng ngưỡng
(`src/auth.py:298-339`) — nhưng AI KHÔNG đi qua route đó, nó gọi thẳng hàm tool trong tiến trình
(`customer_tools.py` import trực tiếp `create_ticket_with_fraud_check`). Hai lớp trùng đúng giá
trị (`OTP_STEPUP_FRESH_MINUTES`), không lệch nhau — không có đường nào một trong hai lớp thiếu mà
lớp kia không bắt. **Không phải finding — xác nhận đúng thiết kế.**

## 2. Luật mới KHÔNG tạo áp lực "vượt cổng" — nhưng tạo áp lực "diễn đạt sai khi cổng chặn"

[ĐO] `git show 9418d1a` — Finding 1 (blocker A2 vế 2) thêm dòng vào `prompt.py:53`:
> *"Khách đã ĐỒNG Ý tạo vé rồi: KHÔNG hỏi thêm bất kỳ thông tin tuỳ chọn nào nữa... tóm tắt theo
> luật đọc-lại-trước-khi-tạo rồi gọi create_ticket **ngay**, đồng ý là mốc kết thúc thu thập."*

Câu này chỉ nói TỚI lúc gọi tool — không nói SAU khi tool trả lỗi. [ĐO] `grep -n "status.*error\|lỗi\|thất bại"
src/agents/prompt.py` → **0 kết quả liên quan tới nhánh lỗi của `create_ticket`** — toàn bộ
`prompt.py` không có một câu nào dạy agent phải nói gì khi tool trả `status=error` do OTP. Agent
CHỈ được dạy phải nói gì khi THÀNH CÔNG (`customer_tools.py:914-916`: *"Sau khi tạo xong... KHÔNG
tự hứa hoàn tiền hay mốc thời gian không có trong kết quả tool"*) — vế THẤT BẠI hoàn toàn phó mặc
cho khả năng suy luận chung của model.

**Kịch bản cụ thể, đọc mã xác nhận từng bước, chưa chạy LLM thật để đo tỉ lệ xảy ra:**
1. Khách đồng ý tạo vé → luật mới ép agent **không hỏi thêm gì, gọi ngay**.
2. OTP step-up (15 phút, `OTP_STEPUP_FRESH_MINUTES`) đã hết hạn từ lúc đầu hội thoại (hội thoại dài,
   hoặc khách quay lại sau khi rời tab) → `create_ticket` trả `_OTP_EXPIRED_ERROR`, KHÔNG raise,
   agent đọc được dict lỗi bình thường như một ToolMessage.
3. Agent **không có hướng dẫn nào** cho tình huống này, nhưng vừa bị luật mới đóng đúng NGAY LỰC —
   "đồng ý là mốc kết thúc thu thập" — hai lực này CÙNG CHIỀU đẩy về một câu trả lời kiểu kết thúc
   sớm: khả năng cao model sẽ tạo câu trả lời "đã hoàn tất" thay vì bảo khách xác thực lại, vì luật
   *duy nhất* nó vừa đọc nói "xong việc thì chốt", không nói "gặp lỗi thì dừng chốt".

**Đây có phải khoảng trống mới ADR-025/O1-O4 chưa từng thấy? KHÔNG — đúng HÌNH DẠNG một finding đã
biết (ADV-041, GĐ3, 19/08), nhưng khác MIỀN, và miền mới CHƯA được vá:**

- [ĐO] `output_filter.py:319-345` — `_O4_DONG_TU` **ĐÃ** được vá 19/08 (`030e4b2`) để bắt đúng lớp
  lỗi ADV-041 tả — thì HOÀN TẤT giả ("đã hoàn tiền", "đã được hoàn tiền", "vừa hoàn lại"...) — comment
  tại chỗ tự thuật lại đúng lý do: *"'đã được hoàn tiền' là khẳng định KẾT QUẢ, không phải lời hứa...
  hậu quả nặng hơn"*. **Đây là finding ADV-041 ĐÃ ĐÓNG, không mở lại.**
- Nhưng `_O4_TIEN` (danh sách bắt buộc phải khớp CÙNG mệnh đề với động từ) là **từ vựng THUẦN
  TIỀN**: `hoan tien, hoan lai, tra lai, boi hoan, nhan lai tien, nhan duoc tien, ve vi, vao vi,
  vao tai khoan`. **Không một từ nào thuộc miền "tạo hồ sơ/tạo vé/tạo ticket".** Một câu như *"Dạ
  mình đã tạo hồ sơ khiếu nại cho bạn rồi, CSKH sẽ liên hệ sớm ạ"* — nếu KHÔNG kèm mã ticket cụ thể
  — sẽ:
  - **Không khớp O3**: `_khop_o3` chỉ bắt khi có dãy số/mã (`_cac_day_so`/`_TOKEN_MA`, ≥7 ký tự)
    trong reply mà không truy vết được về `nguon`/lời khách — câu trên **không chứa mã nào để bắt**,
    `day_la` rỗng, O3 không bắn.
  - **Không khớp O4**: không có token nào trong `_O4_TIEN` xuất hiện trong câu — điều kiện
    `vt_tien is None` khiến `_khop_o4` `continue` ngay, không xét tiếp.
  - **Không khớp O1/O2**: hai bộ này nhắm rò FS-06/cụm nội bộ, không liên quan.
  ⟹ **Lọt hoàn toàn qua `loc_dau_ra`, không nhóm nào bắn, `khop=[]`, câu được trả nguyên văn cho
  khách.**

## 3. Vì sao đây là finding thật, không phải suy diễn quá xa

- **Không phải giả thuyết lý thuyết về prompt injection** — đây là **hai cơ chế có thật, đọc trực
  tiếp từ mã đang chạy**: (a) OTP step-up có thể hết hạn giữa hội thoại (15 phút là ngưỡng CHẶT,
  chủ đích siết hơn ngưỡng xem — hội thoại dài/khách rời tab hoàn toàn có thể chạm ngưỡng này),
  (b) luật "tạo ngay" vừa landed hôm nay tăng áp lực đúng vào thời điểm cổng có thể chặn.
- **Hậu quả nếu xảy ra đúng dạng ràng buộc cứng 3 cấm** (cấm bịa trạng thái không truy vết được tới
  tool result thật) — khách tưởng đã có hồ sơ, không theo dõi tiếp, không biết cần xác thực lại;
  đúng hậu quả comment 19/08 tự mô tả cho ADV-041 ("khách NGỪNG THEO DÕI một giao dịch chưa ai
  duyệt") — chỉ khác đối tượng (hồ sơ khiếu nại thay vì tiền hoàn).
- **Chưa đo bằng LLM thật** — đây là giới hạn thành thật của hồ sơ này: tôi xác nhận được KHE HỞ
  CƠ CHẾ (O1-O4 không có từ vựng để bắt), chưa xác nhận được TẦN SUẤT model thật đi vào khe đó khi
  gặp đúng tình huống (OTP hết hạn giữa hội thoại + luật "tạo ngay"). Cần một ca eval thật giả lập
  đúng kịch bản (đồng ý tạo vé → OTP hết hạn) để đo, không suy đoán xa hơn mức đã đọc mã.

## 4. Đề nghị — hai lớp, không tự chọn thay Coder/Tester

**Lớp 1 (rẻ, tất định — khuyến nghị làm trước):** thêm một câu trong `prompt.py`, cạnh câu đã có ở
dòng 53, dạy rõ nhánh LỖI: *"Nếu `create_ticket` trả `status=error` (kể cả do OTP hết hạn) — TUYỆT
ĐỐI không nói đã tạo hồ sơ/vé, nói rõ cần khách xác thực lại (nếu là lỗi OTP) hoặc chưa xử lý được
(lỗi khác), không tự ý coi là đã xong."* Đây vẫn là phòng vệ CẤP PROMPT (xác suất, không tất định)
— đúng giới hạn mọi phòng vệ prompt có, nhưng đóng đúng khoảng trống đang hở nhất: hiện KHÔNG có
CÂU NÀO cho nhánh này, thêm một câu rõ vẫn tốt hơn im lặng hoàn toàn.

**Lớp 2 (tất định, đắt hơn — khuyến nghị cân nhắc, không phải việc security tự quyết vá):** mở
rộng O4 hoặc thêm nhóm O5 THEO ĐÚNG khuôn đã có cho refund — cụm từ vựng "tạo hồ sơ/tạo vé/tạo
ticket/đã ghi nhận khiếu nại" ở thì HOÀN TẤT ("đã", "vừa") mà **không kèm mã ticket cụ thể trong
cùng lượt** (đối chiếu được với `nguon` giống hệt cách O3 đối chiếu số) → chặn, trả câu an toàn.
Đây là cách ĐÓNG DỨT ĐIỂM (không phụ thuộc model có đọc đúng câu prompt hay không), đúng nguyên
tắc dự án đã chọn cho ADV-041 (tất định thắng xác suất) — nhưng cần Tester viết ca đối chứng trước
(đúng nếp A2), không phải việc tôi tự thêm regex vào `src/`.

**Không kết luận:** ❌ cổng OTP bị lách (không — vẫn tất định, đã kiểm hai lớp). ❌ luật R1-R5 tự nó
sai (bốn luật còn lại — R1/R2/R3/R5 — không đứng cạnh bất kỳ cổng xác thực nào, không có áp lực
tương tự). Chỉ đúng MỘT câu trong finding-1 (dòng 53) đứng cạnh một cổng thật và đang thiếu hướng
dẫn nhánh lỗi.
