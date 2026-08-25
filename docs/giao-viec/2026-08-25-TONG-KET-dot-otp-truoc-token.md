# Tổng kết đợt "OTP trước token" — đọc trong 3 phút

> Nguồn đầy đủ (1400+ dòng, mọi vật chứng/commit): `CHECKLIST-dot-otp-truoc-token.md`.
> File này KHÔNG lặp lại chi tiết — chỉ trả lời ba câu: xong gì, treo gì và vì sao,
> nợ gì sang đợt sau.

🟢 **[CHỐT 25/08] ĐỢT ĐÓNG — NGHIỆM THU ĐẠT.** Tiêu chí PO thật: *"chạy được thật theo
case study từ nhân viên CSKH thật"* — không phải "ô đã tick", không phải "cổng xanh".
**Kết quả: ĐẠT, ba nguồn độc lập cùng xác nhận, thread sạch** (checkpoint có ToolMessage
thật · sổ `so_tool_call=1`/`co_ticket=True` · DB: đúng khách, đúng giao dịch, đúng thread,
1 vé trỏ đúng). Chi phí: nghiệm thu cuối 9 lượt/165.200 token, cả đợt 46 lượt/660.170
token. Hạ tầng: đỉnh 2,86 GB, không sập. Sổ usage đứng yên sau buổi ⟹ không ai tiêu thêm.

**Hai thứ CỐ Ý để lại, không phải bỏ sót:** lượt 7 (cần code ADR-051 — đã qua §3, PO
duyệt, **chưa thi hành có chủ đích** để giữ mốc "trước khi có ⑩") · lượt 4 (⑨ phủ ~53%,
ghi nợ, xem "Nợ chuyển đợt sau").

## Mục tiêu gốc, đo được

**Bất biến:** không lượt nào tốn token trước khi khách xác thực OTP. **Đo trên UI thật,
đạt** — ⑥ 3/3 PASS trên `fin05-dot-otp` (`duong=can_otp`/`total_tokens=0` cho khiếu nại
cá nhân và câu hỏi chính sách chưa OTP; model chạy thật sau OTP).

## Đã đóng (vật chứng trong checklist)

| # | việc | ghi chú |
|---|---|---|
| ③ | Siết 3 từ bắn oan cổng `thu_slot` | 3 vòng vá, đóng 2/2 ca adversarial (ADV-036/038). **N1 KHÔNG đạt trên corpus gốc** — xem "Treo" |
| ④ | Cổng OTP tất định NHÓM B | Backend+FE 1 commit, hợp đồng envelope đúng |
| ⑤ | Cổng sau OTP hỏi thời gian+số tiền 1 tin | |
| ⑥ | Bất biến 0-token trên UI thật | 3/3 PASS — đóng N3 |
| ⑦ | Kill-switch T0 độc lập `PHAN_LUONG_BAT` | Tiêu chí sửa lại vì ④ ra đời sau: "day_du HOẶC can_otp" |
| ⑧ | 2 câu chống mạo danh CSKH | Hằng số, 0 token |
| ⑨ | Câu sàng lọc lừa đảo | 5/5 trục, tất định phần (a), phụ thuộc ADR-050 phần (b) |
| ⑫b | Nối FS-13 với `request_human_handoff` có sẵn | **KHÔNG phải** loại khiếu nại thứ 5 đầy đủ — xem "Thu hẹp" |
| ⑭⑮ | Cờ client cần bằng chứng server + 3 test rẻ | Finding Review, vá bởi Coder |

## Thu hẹp phạm vi (quyết định PO thật, không phải cắt giảm âm thầm)

- **⑫ (loại khiếu nại lừa đảo đầy đủ) → KHÔNG làm.** PO thật: "chỉ cần báo sẽ có chuyên
  gia liên hệ là đủ". Dự thảo ADR-050 đầy đủ (161 dòng, có giá trị cho đợt sau) lưu tại
  `docs/nhat-ky/2026-08-25-ADR-050-du-thao-chua-thi-hanh.md`.
- **⑩ (bản tóm tắt 6 trường tất định) → TREO, không phải huỷ.** Thiết kế đúng đã tìm ra
  (`create_ticket` hai thì — xem mục ⑩ trong checklist), nhưng đổi chữ ký tool ⟹ phải đi
  đủ quy trình đổi contract (§3), không nhét vừa một đợt.

## Treo, cần quyết định tiếp

- **N1 (số lần bắn oan `thu_slot`) KHÔNG đạt trên corpus gốc:** nền 15 → còn 13 (chỉ đóng
  2). Bộ ca độc lập QA/QC 7/7 xanh, nhưng **không đại diện corpus thật** — bài học đo
  lường lớn nhất đợt. PO thật quyết: để lại làm giới hạn đã khai, không mở vòng vá 4.
- **⑪ (cấu trúc lượt hội thoại, 3 vế + góc nhìn PDPA) — ĐÃ ĐÓNG.** Land `421396a`, vượt
  trần token 56 (PO quyết nới 7.550→7.800, không cắt vế). Xác nhận đúng trên kịch bản
  CSKH thật: lượt 5/6/3 đạt/vượt kỳ vọng. ~~Trước đó từng bị ghi nhầm HOÃN (PO hiểu sai
  lệnh gốc, đảo lại 25/08) — lý do hoãn cũ giữ gạch ngang phía trên làm vật chứng, Luật P.~~
- **BLOCKER #23 (bot bịa "đã tạo hồ sơ", mã đưa cho khách là hồ sơ khách khác) — ĐÃ VÁ,
  XÁC NHẬN LẠI TRÊN UI THẬT.** Vá B (cổng ràng buộc cứng 3: khai đã tạo vé phải có
  `ticket_id` thật) `466c59a`, đo 9/9 hai chiều. Nghiệm thu cuối chạy lại đúng kịch bản
  gây lỗi ban đầu — sạch, ba nguồn độc lập xác nhận (xem đầu tài liệu).
- **CI: chưa xanh commit nào của đợt.** PO thật quyết KHÔNG push, KHÔNG gỡ hạn mức
  billing — chấp nhận có khai, không phải sự cố bị bỏ sót.

## Nợ chuyển đợt sau

- ~~Model có tool nhưng không gọi, rồi báo khách như đã tra — vi phạm ràng buộc cứng 3~~
  — **ĐÍNH CHÍNH DỨT ĐIỂM (`4f79741`): agent KHÔNG bịa.** Ba lỗi thật xếp chồng ở tầng
  tra cứu: ① cửa sổ tìm giao dịch mặc định 90 ngày, giao dịch thật 108-109 ngày tuổi
  ⟹ tool chưa từng thấy · ② `get_customer_history` khớp số tiền kiểu MỜ (±2%, có chủ
  đích) lấp chỗ trống bằng kết quả gần giống thay vì trả `not_found` rõ ràng — **khớp
  mờ không gây lỗi, nó xoá dấu vết của lỗi** · ③ `thread_id` cố định theo case + eval
  không xoá checkpoint giữa các lần chạy ⟹ lần chạy sau đọc lại kết quả tool của lần
  trước. Cần vá cả 3, ghi nợ đợt sau.
- `NP-1`: cổng 0-token chỉ nhận diện xưng hô "tôi/mình", bỏ sót "em/cháu/con" — chênh
  lệch trải nghiệm theo tuổi khách, chưa vá vì phải chờ cổng hết bắn oan trước.
- **Cả 3 ngăn Docker chính thức của dự án** (`fin05`/`fin05do`/`fin05ttl`) từng lệch mã
  đợt này giữa chừng, nay `fin05`+`fin05do` đã bật lại — xác nhận lại trước khi tin.
- Backend OOM giữa buổi đo (máy chạy 6 ngăn xếp cùng lúc) — đã xử lý, nhưng trần bộ nhớ
  từng ngăn vẫn chưa đặt, có thể lặp lại.
- Cắt giảm prompt thật (nền token đã lên 96%+, trần nới 7.550→7.800 giữa đợt) — ghi nợ
  tường minh (T3), đo lại khi ổn định.
- **Cổng bất biến phải ĐỎ khi thiếu hạ tầng, không được SKIP** — phát hiện + vá trong
  đợt (`b9e89fa`), nhưng cần rà thêm các cổng khác có cùng lỗ không.

## Bài học quy trình đáng giữ (đã lên `docs/STATE.md`: Luật Z · AA · AB · AC · vế ba
của Luật A · mở rộng Luật D)

- Điểm danh bằng git chỉ đúng với vai CÓ vùng ghi — Review/critic im lặng trên git
  không phải bằng chứng của gì cả. *(Luật Z)*
- Một kết luận không kèm số thô — kể cả từ PO — người nghe được quyền đòi số trước khi
  làm theo. *(Luật AA)*
- Đếm thô trên quần thể pha tạp cho tỉ lệ trông hợp lý mà sai 2-6 lần; luôn hỏi mẫu số
  có đúng quần thể trước khi công bố. *(Luật AB)*
- Một phép đo sai VẬT (không sai quy trình) đi qua mọi cổng và cho số đúng định dạng
  mà sai — ba biến thể, ba cách bắt khác nhau (đo lại/in mẫu số/hỏi đơn vị). *(Luật AC)*
- Cổng canh ràng buộc cứng phải KÊU khi không chạy được, không được im lặng SKIP.
  *(Vế ba, Luật A)*
- Một bất biến kiểm quan hệ giữa hai số rút từ CÙNG một nguồn không phải bất biến — nó
  là phép lặp lại, chứng minh nội bộ nhất quán chứ không chứng minh đúng. *(Mở rộng
  Luật D)* — **món nợ lớn nhất còn lại: rà các bất biến khác của dự án có cùng lỗ này.**
