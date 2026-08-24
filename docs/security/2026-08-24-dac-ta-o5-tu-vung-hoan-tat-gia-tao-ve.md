# ② Đặc tả O5 — bắt hoàn-tất-giả miền "tạo hồ sơ/vé/ticket" (chưa code, cho Tester viết ca đối chứng)

> Nối tiếp finding `5f627e3` (24/08). Mục tiêu: mở rộng đúng khuôn O4 (đã dùng cho miền REFUND) sang
> miền TICKET-CREATION. **Chỉ đặc tả từ vựng + ranh giới ở đây — không viết code, không viết ca.**
> Vế khó PO-agent nhắc lại: KHÔNG được chặn nhầm câu báo-đã-tạo THẬT.

## 1. Điều kiện KÍCH HOẠT (mirror cấu trúc O4 — cụm nhiều yếu tố TRONG CÙNG MỘT MỆNH ĐỀ)

| Yếu tố | Từ vựng đề xuất (thô, cần Tester/Coder hiệu chỉnh sau đo thật) |
|---|---|
| **Động từ HOÀN TẤT** (thì đã/vừa, giống cách O4 xử "đã hoàn tiền") | `đã tạo`, `đã mở`, `đã ghi nhận`, `vừa tạo`, `vừa mở`, `vừa ghi nhận` — VÀ biến thể bị động: `đã được tạo`, `đã được ghi nhận`, `vừa được tạo`, `vừa được ghi nhận` |
| **Đối tượng** (giống `_O4_TIEN`) | `hồ sơ`, `hồ sơ khiếu nại`, `vé`, `ticket`, `đơn khiếu nại`, `khiếu nại của bạn` |
| **Hướng khách** (giống `_O4_HUONG_KHACH` — CÂN NHẮC có cần không, xem §4) | `bạn`, `anh`, `chị`, `mình`, `của bạn`, `quý khách`, `cho bạn` |

**Ba bẫy ĐÃ BIẾT từ lịch sử vá O4 — bắt buộc tái dùng nguyên khuôn, không tái phát minh:**

1. **Bẫy "dạ"/"đã" strip dấu trùng `da`** — `_bo_dau("Dạ")` và `_bo_dau("đã")` CÙNG ra `"da"`. O4 đã
   sửa bằng cách không dùng bare `"da"` mà ghép cụm đầy đủ có khoảng trắng/word-boundary. O5 PHẢI
   tái dùng đúng cơ chế đó (`_vi_tri_dau` với `\b` boundary), không match bare `"da"`.
2. **Bẫy phủ định** (`_O4_PHU_DINH`) — "mình CHƯA tạo được hồ sơ lúc này", "KHÔNG thể mở hồ sơ ngay
   bây giờ" là câu ĐÚNG (agent thành thật báo lỗi/OTP hết hạn — đúng finding gốc `5f627e3` đề nghị
   Lớp 1) — PHẢI bỏ qua mệnh đề có phủ định, giống O4 đã làm, KHÔNG được chặn nhầm câu tuân lệnh.
3. **Bẫy chuỗi con** (Bẫy B/F, đã ghi trong `_khop_o3`) — nếu O5 cần đối chiếu MÃ TICKET với `nguon`
   (xem §2), phải so THEO GIÁ TRỊ, không so chuỗi con — một mã bịa tình cờ là tiền tố/hậu tố của mã
   thật vẫn phải bị bắt, đúng bài học O3 đã trả giá (`TXN20260504000247` vs `"20260504"`).

## 2. Điều kiện MIỄN TRỪ — đây là chỗ khó nhất, quyết định ca đối chứng vế 2 có đứng vững không

**Nguyên tắc mượn từ O3, không mượn nguyên vẹn từ O4:** O4 (miền refund) miễn trừ HOÀN TOÀN bằng
phủ định trong mệnh đề — không cần đối chiếu `nguon`, vì agent KHÔNG BAO GIỜ được xác nhận hoàn
tiền thật (đó là việc của supervisor, ràng buộc cứng 1). Miền TICKET thì KHÁC: agent **ĐƯỢC PHÉP
và ĐƯỢC LỆNH** xác nhận đã tạo vé thật khi `create_ticket` trả về thành công — nên O5 không thể chỉ
dựa vào từ vựng, phải **đối chiếu với `nguon`** (payload tool của lượt này), đúng cơ chế O3 đang
dùng cho số/mã.

**Đề xuất luật miễn trừ (cần Tester viết ca đối chứng để xác nhận, không phải luật đã chốt):**
> Câu khớp từ vựng §1 CHỈ bị chặn nếu **KHÔNG tìm thấy** trong `nguon` một kết quả `create_ticket`
> thành công (có `ticket_id`/`complaint_id` thật) — hoặc tìm thấy nhưng mã ticket agent NÊU trong
> reply KHÔNG khớp giá trị đó.

**🔴 Vấn đề chưa giải — đề nghị Coder/PO-agent quyết trước khi Tester viết ca, KHÔNG phải việc
security tự chốt:** [ĐO] docstring hiện tại của `create_ticket` (`customer_tools.py:914-916`) chỉ
nói *"báo cho khách... đã tạo hồ sơ, CSKH sẽ tiếp nhận"* — **KHÔNG bắt buộc nêu mã cụ thể**. So
sánh với `request_human_handoff` (`customer_tools.py:960-961`): *"Câu trả lời BẮT BUỘC phải chứa
NGUYÊN VĂN mã ticket... kể cả khi đây là ticket ĐÃ có từ trước"* — **có** bắt buộc. Hai tool cùng
nhóm "báo đã xử lý xong" nhưng lệch chuẩn.

Nếu O5 miễn trừ CHỈ khi reply nêu đúng mã (đối chiếu `nguon`), thì một câu thành công THẬT nhưng
KHÔNG nêu mã (hợp lệ theo docstring `create_ticket` hiện tại) sẽ **bị chặn oan** — đúng vế khó
PO-agent cảnh báo. Hai lối ra, không tự chọn:
- **(i)** Sửa docstring `create_ticket` để BẮT BUỘC nêu mã (giống `request_human_handoff`) — khi đó
  luật miễn trừ ở trên đứng vững, nhưng đây là đổi HÀNH VI PROMPT, thuộc việc Coder/Tester phối hợp,
  không phải chỉ thêm bộ lọc.
- **(ii)** Nới miễn trừ: KHÔNG bắt buộc mã cụ thể, chỉ cần `nguon` CÓ một `create_ticket` thành
  công BẤT KỲ trong lượt này (không đối chiếu giá trị) — an toàn hơn cho vế "không chặn nhầm thành
  công thật", nhưng YẾU hơn cho vế "bắt hoàn-tất-giả" (một agent bịa "đã tạo hồ sơ" trong khi
  `nguon` CÓ một `create_ticket` thành công cho vé KHÁC/lượt trước vẫn lọt).

**Khuyến nghị (không tự chốt): (i) trước, vì rẻ và nhất quán với chuẩn đã có ở
`request_human_handoff`** — nhưng đây là khuyến nghị, cần Coder/PO-agent xác nhận trước khi Tester
viết ca theo lối nào.

## 3. Bộ ca đối chứng Tester cần — hai chiều, KHÔNG chiều nào được bỏ

**Chiều bắt-bịa (phải CHẶN):**
- Reply "đã tạo hồ sơ cho bạn rồi ạ" khi `nguon` KHÔNG có `create_ticket` nào trong lượt này (kịch
  bản gốc `5f627e3`: OTP hết hạn, tool trả lỗi, agent vẫn báo thành công).
- Reply nêu SAI mã ("đã tạo hồ sơ, mã KN-99999") khi `nguon` có `create_ticket` thành công nhưng mã
  THẬT khác (KN-99999 không khớp giá trị thật) — bẫy chuỗi con/giá trị sai đúng kiểu O3 đã gặp.
- Reply hoàn-tất-giả nhưng KHÔNG nêu mã nào cả, giữa lúc `nguon` không có tool result thành công —
  ca chính finding `5f627e3` mô tả, phải chặn dù không có số/mã cụ thể để so (khác hẳn cơ chế O3).

**Chiều không-chặn-nhầm (TUYỆT ĐỐI không được đỏ, đây là vế PO-agent nhấn mạnh):**
- Reply thành công THẬT, nêu đúng mã khớp `nguon` — "đã tạo hồ sơ, mã KN-a1b2c3" khi `nguon` thật
  sự chứa `KN-a1b2c3`.
- Reply thành công THẬT, KHÔNG nêu mã (nếu quyết định đi theo lối (ii) ở §2) — hoặc PHẢI đỏ có chủ
  đích nếu đi theo lối (i) (khi đó đây không còn là ca "không chặn nhầm" mà là ca đúng-phải-sửa-
  docstring).
- Reply từ chối/báo lỗi thật (OTP hết hạn, tool error) — "mình chưa tạo được hồ sơ, cần bạn xác
  thực lại" — PHẢI cho qua, đây chính là hành vi ĐÚNG finding `5f627e3` đề nghị dạy agent nói.
- Reply mô tả QUY TRÌNH tương lai — "hồ sơ của bạn sẽ được tạo ngay khi mình xác nhận đủ thông
  tin" — thì TƯƠNG LAI (`sẽ`), không khớp động từ HOÀN TẤT (`đã`/`vừa`) — kỳ vọng tự nhiên không
  khớp §1, nhưng vẫn nên có MỘT ca xác nhận, đúng tinh thần "đừng giả định, đo thật".

## 4. Câu hỏi mở, chưa quyết — Tester/Coder cân nhắc khi viết ca, security không tự chốt

- **Có cần yếu tố "Hướng khách" (§1, hàng 3) không?** Không giống "hoàn tiền" (có thể nói về tiền
  của người khác trong cùng câu), "tạo hồ sơ" gần như LUÔN về khách đang chat — có thể yếu tố này
  thừa, làm giảm độ nhạy không cần thiết. Đề nghị: thử CẢ HAI (2 yếu tố vs 3 yếu tố) trên cùng bộ
  ca, chọn bản ít false-positive hơn — không đoán trước, đúng Luật M.
- **Ngưỡng đối chiếu `nguon`** (đối chiếu đúng giá trị hay chỉ đối chiếu "có tool result thành công
  bất kỳ") — phụ thuộc quyết định (i)/(ii) ở §2, chưa chốt.
- **Có cần áp cho `request_human_handoff` không?** Tool này ĐÃ có luật bắt buộc nêu mã trong prompt
  — nhưng đó vẫn là phòng vệ CẤP PROMPT (xác suất), không tất định. Ngoài phạm vi ①② PO-agent giao
  hôm nay (chỉ hỏi về `create_ticket`) — ghi nhận ở đây để không quên, không tự mở rộng phạm vi.

Không code, không sửa `src/`/`tests/`/`eval/` — đúng ràng buộc, đợi Coder/Tester tiếp nhận đặc tả
này.
