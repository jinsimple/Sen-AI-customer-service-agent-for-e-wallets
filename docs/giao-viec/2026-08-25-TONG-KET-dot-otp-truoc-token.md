# Tổng kết đợt "OTP trước token" — đọc trong 3 phút

> Nguồn đầy đủ (1400+ dòng, mọi vật chứng/commit): `CHECKLIST-dot-otp-truoc-token.md`.
> File này KHÔNG lặp lại chi tiết — chỉ trả lời ba câu: xong gì, treo gì và vì sao,
> nợ gì sang đợt sau.

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
- **⑪ (cấu trúc lượt hội thoại, 3 vế + góc nhìn PDPA):** đang chạy lúc file này viết,
  phải cân trong ngân sách token còn lại (~261, đo trong container — số 293 ban đầu SAI
  vì đo bằng công cụ bị cấm dùng cho việc này, xem `STATE.md`).
- **CI: chưa xanh commit nào của đợt.** PO thật quyết KHÔNG push, KHÔNG gỡ hạn mức
  billing — chấp nhận có khai, không phải sự cố bị bỏ sót.

## Nợ chuyển đợt sau

- Model **có tool nhưng không gọi**, rồi báo khách như đã tra — vi phạm ràng buộc cứng 3,
  tái lập 2/2 + trên UI thật. Không phải hỏng diện rộng (đã loại trừ bằng `usage.jsonl`
  thật), nhưng là bug thật cần sửa hành vi model.
- `NP-1`: cổng 0-token chỉ nhận diện xưng hô "tôi/mình", bỏ sót "em/cháu/con" — chênh
  lệch trải nghiệm theo tuổi khách, chưa vá vì phải chờ cổng hết bắn oan trước.
- **Cả 3 ngăn Docker chính thức của dự án** (`fin05`/`fin05do`/`fin05ttl`) không mang mã
  đợt này — cần quyết định thời điểm dựng lại.
- Backend OOM giữa buổi đo (máy chạy 6 ngăn xếp cùng lúc, không ngăn nào đặt trần bộ
  nhớ) — đã trình PO thật riêng.
- Cắt giảm prompt thật (nền token đã lên 96%+) — ghi nợ tường minh (T3), đo lại sau khi
  Nhóm C ổn định.

## Bài học quy trình đáng giữ (đã lên `docs/STATE.md` Luật Z/AA/AB)

- Điểm danh bằng git chỉ đúng với vai CÓ vùng ghi — Review/critic im lặng trên git
  không phải bằng chứng của gì cả.
- Một kết luận không kèm số thô — kể cả từ PO — người nghe được quyền đòi số trước khi
  làm theo.
- Đếm thô trên quần thể pha tạp cho tỉ lệ trông hợp lý mà sai 2-6 lần; luôn hỏi mẫu số
  có đúng quần thể trước khi công bố.
