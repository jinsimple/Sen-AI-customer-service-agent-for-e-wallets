# Nội dung trang quảng cáo FIN-05 — bản duyệt để dựng

**Ngày:** 2026-08-26 · **Người viết:** điều phối (`p-226-f0`) · **Trạng thái:** chờ PO thật duyệt
**Người dựng:** `ux-ui` — dựng theo **đúng chữ** ở đây. Muốn đổi câu nào thì **hỏi**, đừng tự sửa.

---

## 🔴 Vì sao nội dung do PO-agent viết, không phải UX/UI

Trang quảng cáo là **tuyên bố của sản phẩm về chính nó**, không phải một màn hình. Với sản phẩm tài
chính, mỗi câu là một **cam kết** — và ba ràng buộc cứng của dự án đều **có thể bị phá bằng một câu
marketing** mà không cần chạm dòng code nào:

```
ràng buộc #1  AI KHÔNG BAO GIỜ quyết định
              🔴 phá bằng: "AI tự xử lý khiếu nại của bạn"
ràng buộc #3  cấm bịa số liệu
              🔴 phá bằng: bất kỳ con số hiệu quả nào ta không đo được
ràng buộc #4  không bao giờ hỏi mật khẩu ví / OTP giao dịch
              🔴 phá bằng: ảnh minh hoạ vẽ ô nhập OTP giao dịch
```

**Fin.ai quảng cáo *"AI resolves X% of tickets"*. Ta KHÔNG được chép câu đó** — nó mô tả một sản phẩm
khác, có mô hình trách nhiệm khác.

---

## Luật viết — áp cho mọi câu trên trang

| | |
|---|---|
| ✅ **ĐƯỢC nói** | *AI **điều tra** · **tra cứu** · **đề xuất có căn cứ** · **chuẩn bị hồ sơ*** |
| 🔴 **CẤM nói** | *AI **xử lý** · **giải quyết** · **quyết định** · **duyệt** · **hoàn tiền*** |
| ✅ **ĐƯỢC nói** | *con người quyết định — và đó là **thiết kế**, không phải hạn chế* |
| 🔴 **CẤM** | mọi con số hiệu quả không đếm được · logo đối tác · lời chứng thực · tên khách hàng |

**Phép thử một câu, chạy trước khi thêm bất cứ dòng chữ nào:**
> ***"Câu này có khiến người đọc tin rằng AI tự ra một quyết định nào đó không?"***
> Có ⟹ viết lại. **Không có ngoại lệ vì lý do marketing.**

---

## Nội dung

### 1 · HERO

> # Khiếu nại giao dịch, điều tra trong vài phút — quyết định vẫn thuộc về con người
>
> FIN-05 là trợ lý AI cho đội chăm sóc khách hàng ví điện tử. Nó tra cứu giao dịch, đối chiếu chính
> sách và chuẩn bị hồ sơ có dẫn chứng. **Người duyệt vẫn là người.**

`[ Xem sản phẩm hoạt động ]`  ·  `[ Đăng nhập ]`

📌 **Câu tiêu đề có hai vế và vế sau BẮT BUỘC.** Bỏ vế sau đi là vi phạm ràng buộc #1.

---

### 2 · BA CÂU GIẢI THÍCH — thay cho dải logo đối tác

🔴 **Ta chưa có khách hàng nào. Không dựng dải logo, không dựng lời chứng thực.**

> **Không bịa số.** Mỗi con số agent nói ra đều truy ngược được tới một lần tra cứu có thật. Không tra
> được, nó nói thẳng là không tra được.
>
> **Không vượt quyền.** Agent gọi công cụ dưới danh nghĩa khách hàng, không hơn. Không có đường nào để
> AI tự hoàn tiền.
>
> **Không hỏi thứ không được hỏi.** FIN-05 không bao giờ hỏi mật khẩu ví hay mã OTP giao dịch của bạn.

---

### 3 · LUỒNG BỐN BƯỚC — phần quan trọng nhất trang

Vẽ thành bốn ô ngang, **đánh số rõ**, mỗi ô một câu:

```
① KHÁCH gửi khiếu nại        nhắn như nói chuyện bình thường
② AI điều tra                tra giao dịch, đối chiếu chính sách, dựng hồ sơ CÓ DẪN CHỨNG
③ CSKH kiểm tra và trình     người thật đọc hồ sơ, xác minh, rồi trình lên
④ SẾP duyệt                  🔴 CHỈ cấp duyệt mới ra được quyết định cuối
```

🔴 **Bước ④ phải nổi bật nhất, không phải bước ②.** Đây là điểm bán, không phải điều phải giấu — thị
trường đang ngập sản phẩm hứa "AI tự động hoá hoàn toàn", và **trách nhiệm giải trình là thứ ngân hàng
với ví điện tử thật sự cần.**

---

### 4 · SỐ LIỆU — chỉ số ĐẾM ĐƯỢC

🔴 **Bốn số dưới đây đều đếm được từ mã và hồ sơ chuẩn. KHÔNG thêm số nào khác.**

| số | nghĩa |
|---|---|
| **34** | route có kiểm quyền theo vai |
| **5** | công cụ AI được phép gọi — **và 5 công cụ bị cấm tuyệt đối** |
| **23** | phép kiểm tự động canh các ràng buộc không thoả hiệp |
| **0** | số quyết định hoàn tiền AI được phép tự ra |

📌 **Số `0` là số mạnh nhất trang.** Đặt nó cuối cùng.

⚠️ **Bốn số này sẽ CŨ ĐI khi mã đổi.** Ghi rõ trong mã nguồn trang: *"đếm ngày 26/08/2026 — đổi contract
thì đếm lại"*. Đừng để một con số hoá thạch trên trang công khai.

---

### 5 · TUÂN THỦ

> Thiết kế theo khung pháp lý hiện hành cho trung gian thanh toán tại Việt Nam — **NĐ 52/2024** và
> **TT 40/2024**. Dữ liệu cá nhân xử lý theo **NĐ 13/2023**. Thông tin bên thứ ba trong giao dịch được
> che trước khi hiển thị.

🔴 **Nói "thiết kế theo", KHÔNG nói "đã được chứng nhận" hay "tuân thủ đầy đủ"** — ta chưa qua kiểm toán
độc lập nào. **Đó là khác biệt giữa mô tả và cam kết pháp lý.**

---

### 6 · CHÂN TRANG

```
FIN-05 · Trợ lý CSKH ví điện tử
AI 20K Build Phase Cohort 3 — Vingroup × VinUni
[ Đăng nhập ]                        ← CHỈ trang khách. KHÔNG nối trang nội bộ.
```

🔴 **KHÔNG nối tới `/dang-nhap-noi-bo` từ bất cứ đâu trên trang công khai.** Không phải bảo mật thật —
ai đoán được URL vẫn vào tới — nhưng **bớt một lời mời** cho người không có việc ở đó.

---

## Ba thứ KHÔNG dựng, dù mẫu Stripe có

```
🔴 dải logo khách hàng      — ta chưa có khách hàng nào
🔴 case study / lời chứng thực — ta chưa có ai để trích
🔴 số liệu quy mô kiểu "$1.9T đã xử lý" — ta không có con số nào thuộc loại đó
```

**Để trống còn hơn điền số đẹp.** Một con số bịa trên trang công khai của sản phẩm tài chính là thứ
**không rút lại được** — và nó phá đúng ràng buộc cứng #3 mà cả sản phẩm được xây để giữ.
