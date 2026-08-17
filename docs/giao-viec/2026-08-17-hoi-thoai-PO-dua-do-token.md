# Hội thoại PO thật đưa 17/08 — dùng để đo token trên `qwen3.7-max`

> Nguồn: PO thật dán nguyên văn. **Không sửa một chữ.**
> Mục đích: đo `usage` THẬT của nhà cung cấp cho một kịch bản do PO chọn.
> Ngăn xếp: `fin05` (kho RAG 378 chunk) — **KHÔNG dùng `fin05do`** (kho rỗng).

## Hình dạng luồng (để dựng harness)

| # | vai | nội dung | tool kỳ vọng |
|---|---|---|---|
| 1 | KH | chuyển nhầm 2 triệu, sai số điện thoại, xin lấy lại | — (hỏi lại) |
| 2 | KH | ~9h sáng, nhập `0912xxx678` thay vì `0912xxx687` | — (yêu cầu OTP phiên) |
| 3 | KH | `482913` (mã OTP phiên) | xác thực → `lookup_transaction` |
| 4 | KH | xác nhận đúng giao dịch, hỏi **huỷ được không** | — (từ chối, giải thích) |
| 5 | KH | đồng ý tạo yêu cầu + **xin gặp người thật** | `create_ticket` + `request_human_handoff` |
| 6 | — | CSKH tiếp nhận | — (ngoài phạm vi agent) |

---

## Nguyên văn

**KH:** Mình vừa chuyển nhầm 2 triệu cho người lạ, sai số điện thoại. Giúp mình lấy lại với.

**AI:** Mình hiểu, chuyển nhầm tiền rất sốt ruột. Mình tra ngay giúp bạn. Giao dịch thực hiện lúc mấy giờ, và số điện thoại bạn đã nhập nhầm là số nào ạ?

**KH:** Khoảng 9h sáng nay, mình nhập 0912xxx678 mà đúng ra phải là 0912xxx687.

**AI:** Cảm ơn bạn. Trước khi xem chi tiết giao dịch, mình cần xác thực bạn là chủ ví. Mình vừa gửi một mã xác thực phiên làm việc về số điện thoại đăng ký — bạn đọc giúp mình 6 số đó nhé. Lưu ý: mình không bao giờ hỏi mật khẩu hay mã OTP giao dịch.

**KH:** 482913

**AI:** Xác thực thành công. Mình tra được giao dịch: 09:14 hôm nay, chuyển 2.000.000đ tới ví của Ngu* V** A** (số 0912***678), trạng thái Thành công, mã giao dịch MM2608130914. Đây có đúng là giao dịch bạn muốn khiếu nại không ạ?

**KH:** Đúng rồi. Vậy huỷ giao dịch được không, tiền vẫn trong ví người ta mà?

**AI:** Mình nói thẳng để bạn khỏi chờ đợi vô ích: giao dịch đã hoàn tất và tiền đã vào ví người nhận, nên hệ thống không tự thu hồi được. Cách xử lý là mình mở yêu cầu tra soát, ví sẽ liên hệ chủ ví nhận tiền để đề nghị hoàn trả — nhưng việc hoàn hay không phụ thuộc vào sự đồng ý của họ. Mình tạo yêu cầu ngay cho bạn nhé?

**KH:** Ừ tạo đi. Mà mình muốn nói chuyện với người thật, không muốn nói với bot.

**AI:** Được ạ, mình đã tạo yêu cầu KN-20826-4471 và đính kèm toàn bộ thông tin giao dịch mình vừa tra, để bạn không phải kể lại từ đầu. Mình chuyển sang nhân viên hỗ trợ ngay bây giờ. Trong lúc chờ, bạn giữ nguyên cửa sổ này giúp mình.

**AI:** Xin chào anh/chị, em là Trang — nhân viên hỗ trợ ví Sen. Em đã đọc yêu cầu KN-20826-4471 và thông tin giao dịch. Em xác nhận đang tiếp nhận và sẽ liên hệ chủ ví nhận tiền trong hôm nay, cập nhật lại cho anh/chị chậm nhất trong 3 ngày làm việc ạ.

---

## Ba điều đáng chú ý về chính kịch bản này (PO viết, không phải đội)

1. **Nó đi qua CẢ NĂM ràng buộc cứng** — OTP phiên (không hỏi mật khẩu/OTP giao dịch) · che PII bên thứ ba (`Ngu* V** A**`, `0912***678`) · không tự thu hồi tiền · trích số liệu từ tool có thật · bàn giao người thật.
2. **Lượt 4 là lượt từ chối** — agent nói *"không tự thu hồi được"* thay vì hứa. Đây là hành vi đúng và là ca khó.
3. **Lượt 5 gộp hai việc**: tạo ticket **và** handoff — đúng đường `request_human_handoff` mang `ticket_id` (nhánh ②, không tạo vé mới).
