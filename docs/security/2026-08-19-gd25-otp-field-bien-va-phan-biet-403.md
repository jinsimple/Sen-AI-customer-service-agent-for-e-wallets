# GĐ2.5 — Bảo Mật: field OTP lộ ra client + phân biệt 403-OTP/403-role

> 19/08/2026. Theo `docs/giao-viec/2026-08-19-gd25-va-finding-ab-otp.md` mục 3-Bảo Mật.
> `frontend/src/` gỡ băng, `src/` backend ĐÓNG BĂNG — chỉ đọc backend để xác nhận, không đề xuất sửa.

## Câu ① — field phiên lộ ra client: BOOLEAN ĐÚNG, timestamp SAI. Xác nhận hướng Lead nghiêng.

**[ĐO]** `src/auth.py:72,118`: JWT payload mang `otp_verified_at` là **Unix timestamp trần**. Đây
chính là claim brief muốn giữ lại phía server.

**Boolean rò ít thông tin hơn timestamp, và mức chênh lệch LỚN hơn trực giác ban đầu** — không chỉ
"tiện hơn", mà **khác hẳn về mặt suy ngược được**:
- Ngưỡng `OTP_VIEW_MAX_MINUTES`/`OTP_STEPUP_FRESH_MINUTES` **không phải bí mật** — nằm trong ADR-005
  công khai trong repo. Nếu client nhận **mốc hết hạn** (timestamp), một người quan sát (hoặc chính
  khách tò mò mở devtools) suy ngược được **gần đúng thời điểm khách xác thực OTP** bằng phép trừ
  đơn giản (`hết_hạn - ngưỡng = lúc_xác_thực`) — tái tạo lại đúng claim mà brief cấm bê ra client,
  chỉ qua một bước số học.
- Boolean (`otp_xem_con_han`/`otp_stepup_con_han`) chỉ mang **một bit tại một thời điểm** — không có
  phép biến đổi ngược nào từ "true/false lúc render" ra "chính xác lúc nào đã xác thực". Mức rò tối
  thiểu đúng nghĩa.

⟹ **Đồng ý với Lead: boolean, không phải mốc hết hạn.** Không cần đắn đo thêm — chênh lệch rủi ro
giữa hai lựa chọn đủ lớn để không phải là một sự đánh đổi UX-vs-bảo mật cân bằng, mà là boolean thắng
ở cả hai trục (ít lộ hơn VÀ đúng nguyên tắc "logic hạn tính MỘT nơi" của brief — timestamp mời gọi
client tự làm phép trừ ngược, tức tự tính lại hạn theo cách khác).

**Một điều kiện đi kèm, không đổi kết luận:** boolean là ảnh chụp **lúc server render trang** — nó
KHÔNG tự cập nhật nếu khách mở tab lâu hơn ngưỡng. Đây **không phải lỗ hổng bảo mật**, chỉ cần nói rõ
để không ai coi nó là "nguồn xác thực real-time": theo câu ② dưới, backend (403 ở hành động thật) vẫn
là chốt cuối — boolean cũ chỉ làm sai UI (hỏi lại OTP không cần thiết, hoặc không mời xác thực sớm
như mong đợi), KHÔNG làm sai QUYẾT ĐỊNH cấp quyền. Nếu boolean này lại là nguồn duy nhất gác một hành
động (không qua chốt 403 nào), tính an toàn của phần đó sẽ SỤP hoàn toàn theo tuổi thọ trang mở — nên
phát biểu chính xác: **boolean an toàn CHÍNH VÌ câu ② đúng, hai câu không độc lập.**

## Câu ② — chiều fail-closed: XÁC NHẬN backend không đổi. Về "dấu hiệu BỀN" — có MỘT khoảng trống thiết kế Coder cần đóng trước khi viết catch.

**[ĐO] `src/auth.py:340-344`** (đọc, KHÔNG sửa — đúng phạm vi đóng băng): `require_otp_verified`
raise `HTTPException(403, "Cần xác thực OTP phiên làm việc trước khi thao tác này...")` khi
`otp_fresh_within(OTP_STEPUP_FRESH_MINUTES)` sai. Dependency này **chỉ gắn ở `/tools/create_ticket`**
(`main.py:566,570`) — không đụng gì tới `/agent/chat`. **Xác nhận: 403 vẫn là chốt DUY NHẤT, client
không có đường nào bỏ qua nó — mọi thứ Coder viết chỉ là PHẢN ỨNG với 403, không phải điều kiện thay
thế nó.** Đúng khung "client làm đẹp mà không làm yếu".

🔴 **Nhưng [ĐO] hiện trạng cho thấy một khoảng trống PHẢI ĐÓNG TRƯỚC khi viết nhánh catch, không chỉ
sau đó soi chuỗi:** `frontend/src/lib/api.ts` **KHÔNG có hàm gọi `/tools/create_ticket`**, và
`ChatClient.tsx` **không gọi route đó ở đâu cả** — toàn bộ luồng khách hàng hiện tại tạo ticket qua
**agent nội bộ** (LangGraph gọi thẳng hàm Python trong `customer_tools.py`, KHÔNG qua HTTP), và tool
đó khi OTP hết tươi trả về **`{"status": "error", ...}` bên TRONG lượt `/agent/chat` (HTTP 200)**,
không phải một exception 403 ở tầng route. ⟹ **Với luồng đang chạy hôm nay, `/agent/chat` không bao
giờ tự sinh ra đúng cái 403-OTP-cũ mà Finding B định bắt.**

**Không phải lỗi của thiết kế Finding B — là một quyết định Coder phải làm TƯỜNG MINH trước khi viết
catch, và nó đổi CẢ CÂU HỎI ② lẫn CÂU HỎI của Review về vị trí diff:**
- Nếu hướng đi là **thêm một lệnh gọi `/tools/create_ticket` trực tiếp** (route ĐÃ CÓ, không đụng
  backend) cho đúng hai lối vào "biết chắc liên quan giao dịch" (chip/rail, `startComplaint()`) —
  đây là cách 403 thật sự xuất hiện, và closure hợp lý nhất với brief.
- Nếu hướng đi là **giữ nguyên qua agent**, thì "403-OTP-cũ" phải đổi nghĩa thành đọc `status:"error"`
  trong `tool_calls` (không phải `ApiError`/403 HTTP) — và toàn bộ đoạn brief mô tả bằng ngôn ngữ 403
  sẽ SAI CHỖ, Coder cần định tuyến lại (đây không còn là câu hỏi của tôi — thuộc thiết kế Coder/Lead).
**Đề nghị Lead xác nhận với Coder hướng nào TRƯỚC khi họ viết catch** — hai hướng cho ra hai loại
lỗi khác hẳn nhau để phân biệt, câu trả lời "dấu hiệu bền" dưới đây giả định hướng THỨ NHẤT (403 HTTP
thật, đúng chữ brief dùng).

### Dấu hiệu BỀN cho 403-OTP vs 403-role — [ĐO] hai chuỗi backend thật, đề xuất neo ĐỦ RỘNG PREFIX

```
role   :  f"Cần role thuộc {sorted(allowed_roles)}, tài khoản hiện tại là {current_user.role}"
otp    :  "Cần xác thực OTP phiên làm việc trước khi thao tác này (POST /auth/otp/request rồi /auth/otp/verify)"
```

Cả hai là **f-string cố định trong mã ĐÓNG BĂNG** — không đổi trong sprint này, nên "bền" ở đây có
nghĩa thực tế là ***"bền cho tới lần backend gỡ băng tiếp theo"***, không phải bền tuyệt đối (backend
không có trường mã lỗi có cấu trúc — không thể có gì bền hơn mà không sửa `src/`, việc bị cấm đợt
này). Trong giới hạn đó:

**🔴 Nhánh 403-role HIỆN TẠI (`ChatClient.tsx:431`, `/role/i.test(e.message)`) đã LỎNG HƠN mức cần
thiết — SỬA NHÂN TIỆN GĐ2.5, đừng chỉ thêm nhánh OTP bên cạnh một nhánh cũ còn lỏng.** Một regex một
từ (`role`) khớp bất kỳ 403 nào TÌNH CỜ chứa chữ đó — không phải kịch bản giả định, là rủi ro thật
khi thêm nhánh OTP cạnh nó: hai regex lỏng cùng tồn tại làm tăng khả năng chồng chéo.

**Đề nghị cụ thể — neo PREFIX riêng biệt, thứ tự CÓ Ý NGHĨA, mặc định AN TOÀN:**
```
1. e.message.startsWith("Cần role thuộc")               → 403-role (nhánh đã có, SIẾT lại)
2. e.message.startsWith("Cần xác thực OTP phiên làm việc") → 403-OTP (nhánh MỚI)
3. còn lại (bao gồm 403 KHÔNG khớp cả hai)               → nhánh chung hiện có ("Có lỗi: …")
                                                            — KHÔNG được coi ngầm định là OTP
```
**Điều khoản quan trọng nhất, đúng thứ Lead lo:** nhánh (3) — 403 không khớp — **PHẢI đi vào đường
lỗi chung trung tính, TUYỆT ĐỐI không rơi vào nhánh mời-xác-thực-lại theo mặc định.** Sai hướng nguy
hiểm duy nhất là "không nhận ra được ⟹ coi như OTP ⟹ mời xác thực lại" — đó mới là chỗ rò thẩm quyền
qua hành vi UI. Sai hướng ngược lại (không nhận ra ⟹ rơi về lỗi chung) chỉ mất một chút UX, không mất
gì về bảo mật — đây chính là "chọn chiều fail-closed" áp cho một discriminator ở tầng UI, cùng tinh
thần Luật H của dự án (ba trạng thái, không phải hai: role · OTP · không rõ — "không rõ" không được
gộp ngầm vào một trong hai loại có tên).

## Tóm tắt cho Review đối chiếu diff
- ① đạt nếu: field mới là boolean (không phải timestamp/claim thô), tên biến không gợi ý giá trị số.
- ② đạt nếu: (a) không route/dependency backend nào bị đổi (băm `src/` giữ nguyên) · (b) discriminator
  403 dùng `startsWith` trên PREFIX đã liệt kê ở trên (không phải regex một từ) · (c) nhánh "không
  khớp cả hai" rơi về lỗi chung, KHÔNG rơi về nhánh mời xác thực lại · (d) nhánh 403-role cũ cũng
  được siết lại trong cùng diff, không chỉ nhánh OTP mới.
