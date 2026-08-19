# GĐ2.5 — Chữ ký Bảo Mật cho Finding A + Finding B

> 19/08/2026. Ký trên DIFF THẬT đã đọc (`git show 6441319`, `git show 1b916f1`), không dựa mô tả
> commit. Phạm vi ký nêu rõ ở cuối — đọc trước khi trích dẫn "Bảo Mật đã ký" ở chỗ khác.

## KÝ: CÓ, cho cả Finding A và Finding B, theo đúng phạm vi câu 44 brief GĐ2.5.

### Finding A (`6441319`) — [ĐO] khớp đúng ràng buộc đã đặt ra

- `getOtpXemConHan(): boolean` (`session-server.ts`) — trả **boolean thuần**, docstring tự khai
  *"KHÔNG BAO GIỜ trả nguyên claim JWT ra ngoài hàm này"*. Đọc code xác nhận đúng: hàm decode JWT
  **nội bộ**, chỉ `return` một so sánh (`ageMinutes <= OTP_VIEW_MAX_MINUTES`).
- `page.tsx` truyền đúng MỘT prop dẫn xuất (`otpXemConHanLucTai`) — không có `access_token`/claim
  nào lọt ra props.
- Tên biến `...LucTai` tự khai đây là ảnh chụp lúc render, không phải trạng thái sống — đúng điều
  kiện tôi nêu ("không coi là nguồn xác thực real-time").
- Ngưỡng `OTP_VIEW_MAX_MINUTES` là bản sao **có khai nguồn** (`src/config.py`) — có cổng ghim
  (`ChatClient.pin.test.ts` cổng ①) so giá trị hai bên, không so text.

### Finding B (`1b916f1`) — [ĐO] đúng hướng (b) tôi cảnh báo phải xác nhận trước khi viết catch

Xác nhận Coder đã tự phát hiện đúng thứ tôi nêu trong hồ sơ `2026-08-19-gd25-otp-field-bien-va-phan-biet-403.md`
(không cần tôi nhắc lại) — commit message ghi rõ: *"catch(e).status===403 viết theo brief gốc sẽ
không bao giờ bắn... đã dừng lại báo Lead trước khi viết"*. Bản vá đi đúng hướng (b): đọc
`result.tool_calls[].result.status === "error"` trong response 200, KHÔNG bịa ra một đường 403
không tồn tại.

- **Discriminator dùng `===` tuyệt đối** trên hằng số backend thật (`OTP_EXPIRED_MESSAGE`), KHÔNG
  regex/substring — đúng yêu cầu "dấu hiệu bền" tôi đặt ra, siết hơn cả đề xuất `startsWith()` ban
  đầu của tôi.
- **Ba trạng thái được tôn trọng:** khớp sai/không khớp rơi qua nhánh `touchedSensitiveData` cũ —
  KHÔNG bị gộp ngầm vào "OTP". Đúng điều khoản tôi đặt ra ở câu ②.
- **Cổng ghim `ChatClient.pin.test.ts` cổng ②** so `_OTP_EXPIRED_ERROR.message` hai phía bằng đọc
  VĂN BẢN THUẦN (không `import` từ `src/`) — đây CHÍNH LÀ đề xuất "một dòng comment liên kết coupling"
  tôi đưa ra hôm qua, nhưng làm MẠNH HƠN: một bài test THẬT SỰ CHẠY và ĐỎ khi lệch, không chỉ một dòng
  chữ hy vọng có người đọc. Không còn gì để yêu cầu thêm ở điểm này — nợ (i) đã "có hạn kèm chuyến"
  đúng nghĩa, không phải một lời hứa suông.

## 🔴 VỀ DỮ KIỆN MỚI — ảnh backend cũ (`38e65466e3ce`) bị xoá, không diff được 168 gói + OS

**Không chặn chữ ký này**, và tôi nói rõ VÌ SAO, không chỉ nói "không chặn":

1. **Nằm NGOÀI phạm vi Finding A/B.** Hai chữ ký trên xác nhận một TÍNH CHẤT LOGIC ỨNG DỤNG (biên
   dữ liệu qua BFF, chiều fail-closed OTP) — đọc từ **mã nguồn** (`git diff 06132a9..HEAD -- src/`
   rỗng, xác nhận độc lập bởi cả Lead lẫn tôi), không phụ thuộc gì vào việc image nào đang chạy hay
   gói OS nào bên dưới. Tính đúng đắn của hai finding này không suy giảm dù không diff được ảnh cũ.
2. **[ĐO] tự kiểm — vật thay thế cho việc diff ảnh, mạnh hơn diff ảnh ở điểm quan trọng nhất:**
   `git diff 06132a9..HEAD -- requirements.lock.txt requirements.txt Dockerfile` → **RỖNG**. Lock
   file là nguồn xác định phiên bản 168 gói Python — không đổi thì **không có lý do để phiên bản gói
   đổi**, bất kể build ở lần nào. Diff-ảnh-cũ nếu còn cũng chỉ xác nhận lại đúng điều này, không hơn.
3. **Khoảng trống THẬT còn lại, không phải giả:** `Dockerfile:5,33` ghim base image bằng **TAG**
   (`FROM python:3.12-slim`), không phải **digest**. Tag này TRÔI theo thời gian (Docker Hub cập
   nhật bản vá OS/Python patch dưới cùng một tên) — hai lần build cùng Dockerfile, cách nhau vài
   ngày, có thể kéo hai layer OS khác nhau dù mọi file trong repo giống hệt. Đây là khoảng trống
   **CÓ THẬT, TỒN TẠI TỪ TRƯỚC GĐ2.5**, không phải điều GĐ2.5 gây ra, và **không có gì trong đợt vá
   Finding A/B chạm tới lớp này**.

**Kết luận:** không xin PO thật DỪNG merge vì lý do này. Việc bảo mật của tôi đúng phạm vi được giao
là ĐẠT. Ghi một mục sổ nợ RIÊNG (không phải điều kiện của chữ ký GĐ2.5): *ghim `FROM python:3.12-slim`
bằng digest thay vì tag* — cùng nguyên tắc "ghim phiên bản, chống trôi chuỗi cung ứng" dự án đã áp cho
GitHub Actions (`@v4` không `@main`, ADR liên quan CI). Việc RẺ, KHÔNG GẤP — làm lúc nào backend gỡ
băng lần tới, không phải hôm nay.

## QĐ-C (PO bác publish cổng backend ra host) — ghi nhận, không việc gì thêm

Không mở bề mặt mạng mới — khớp mọi phân tích trước đó của tôi (mọi kết luận về biên dữ liệu/JWT dựa
trên kiến trúc BFF hiện có, cookie httpOnly, không route mới). Không cần xem lại gì.

## PHẠM VI CHỮ KÝ — đọc trước khi trích dẫn

Ký cho: (1) Finding A — field boundary qua BFF đủ hẹp, không lộ claim JWT thô. (2) Finding B — chiều
fail-closed phía server không đổi, discriminator client dùng dấu hiệu bền (so tuyệt đối, có cổng
ghim), ba trạng thái được tôn trọng.
**KHÔNG ký cho:** toàn vẹn mặt phẳng phụ thuộc ảnh (168 gói/OS) — ngoài phạm vi được giao, và đã nêu
lý do kỹ thuật vì sao không cần chặn vì lý do đó (mục trên). Không ký thay Review (diff B/regex vá
GĐ3 thuộc vai khác) — chỉ ký phần tôi được giao.
