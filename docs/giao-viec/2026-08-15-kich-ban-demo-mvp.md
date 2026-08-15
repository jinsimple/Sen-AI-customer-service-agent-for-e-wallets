# KỊCH BẢN DEMO MVP — FIN-05 (bản cho người thuyết trình)

> PO-agent soạn 15/08 từ bộ case ĐÃ DIỄN TẬP THẬT (`eval/demo_cases_20260814.md`, mỗi case
> đo 2-3 lượt) + checklist GO (`docs/DEMO-READINESS-2026-08-14.md`). Không case nào bịa.
> Thời lượng: ~10-12 phút cho đủ 6 màn; bản rút 6-7 phút bỏ Màn 5b + Màn 6.

## 0. Link sản phẩm & khởi động

| Môi trường | Link | Ghi chú |
|---|---|---|
| **Production (khuyên dùng demo)** | `https://app.adaptivealgo.uk` | VPS Oracle, tự deploy từ nhánh `main`. Kiểm trước giờ G: mở được màn login là sống. |
| Local Docker (dự phòng) | `https://localhost` | `docker compose up -d` ở gốc repo → chờ ~1 phút → kiểm `docker ps` thấy backend **healthy** (KHÔNG dùng `curl localhost/health` — Caddy đưa về app). |

⚠️ **Demo trên stack ĐÃ DIỄN TẬP (main/Docker), KHÔNG bật stack dev** (`next dev` + uvicorn) —
hai stack cùng sống là bẫy đã mất nhiều giờ (ADR-009). Công việc mới hôm nay nằm ở nhánh
`dev/learning-loop`, CHƯA deploy — đừng kỳ vọng tính năng mới (UI timeline đẹp) có mặt trên demo.

**5 tài khoản demo (mật khẩu chung `Demo@123`):**

| Vai | SĐT đăng nhập | Dùng cho màn |
|---|---|---|
| Khách hàng (chính) | **`0974000145`** — GÕ TAY | Màn 1-5 (mọi case D1-D4 dựng trên user này) |
| Khách hàng (phụ) | `0387000001` | không dùng |
| CSKH | `0353000201` | Màn 6 |
| Sếp | `0905000205` | Màn 7 |
| Đối tác ví | `0900000001` | Màn 8 |

🔴 **KHÔNG bấm nút "Đăng nhập nhanh — Khách hàng"** — nút đó trỏ user khác, D1-D4 trật hết dữ liệu.

---

## Màn 1 — Đăng nhập + OTP (1 phút) — kể về XÁC THỰC

Gõ tay `0974000145` / `Demo@123` → hệ thống đòi OTP → **mã hiện ngay trên màn hình** (môi
trường demo trả mã để tiện kiểm).

**Lời kể:** *"OTP này là OTP phiên làm việc — hệ thống KHÔNG BAO GIỜ hỏi mật khẩu ví hay OTP
giao dịch của khách. Và lát nữa sẽ thấy: hành động càng nguy hiểm càng đòi xác thực lại — đúng
chuẩn PSD2 dynamic linking của châu Âu."*

⚠️ Sau khi OTP xong **ĐỪNG F5 màn chat** (rail giao dịch ẩn lại — lỡ F5 thì bấm "Xác thực ngay", ~10s).

## Màn 2 — Trợ lý AI: tra cứu TÌM THẤY (D1, ~2 phút) — kể về GROUNDING

**Gõ:** `minh chuyen 171k cho ban hom 1/8 luc 12:47 ma ban bao chua nhan duoc`

Agent gọi tool thật, tìm đúng `TXN20260801000466` (171.000đ · 01/08 12:47) **giữa 9 giao dịch
cùng số tiền** — chọn bằng mốc thời gian, không đoán.

**Lời kể:** *"Khách chỉ nói '171k hôm 1/8'. Ví này có 9 giao dịch trùng số tiền — agent dùng
thêm mốc giờ để khoá đúng MỘT, và mọi con số trên màn đều truy ngược được về một kết quả tool
trong database. Không truy được thì nó không nói."*

⚠️ Nếu hiện `[PERSON]`: **chủ động** nói *"tên người nhận được che tự động — thông tin bên thứ
ba không rời hệ thống, đúng nghị định bảo vệ dữ liệu cá nhân 13/2023"* — biến thành điểm cộng.
⚠️ Chờ 10-20 giây là bình thường — lấp bằng lời kể: *"agent đang tra thật vào 60.000 giao dịch."*

## Màn 3 — KHÔNG TÌM THẤY (D2, ~1,5 phút) — ĐIỂM PITCH MẠNH NHẤT

**Gõ:** `kiem tra giup gd TXN20260623999901, toi chuyen ma khong thay trong lich su`

Agent trả lời **không tìm thấy** + hỏi thông tin thu hẹp. Không một con số bịa.

**Lời kể:** *"Đây là chỗ chatbot thường chết: bịa. Mã này không tồn tại — agent nói thẳng
'không tra được' thay vì sáng tác một trạng thái nghe hợp lý. Với tiền của khách, 'không biết'
trung thực đáng giá hơn 'biết' bịa."*

🔴 **CẤM diễn tiếp ở màn này:** KHÔNG yêu cầu "tạo hồ sơ cần tra thủ công" sau khi không tìm
thấy — có lỗi đã biết (CASE-110) làm hỏng lượt chat. Dừng ở "không tìm thấy + hỏi lại" rồi sang màn 4.

## Màn 4 — Cảm xúc + TẠO TICKET trọn luồng (D3+D4, ~2,5 phút) — kể về HITL

**Gõ:** `Trừ một lần đã xót, đây trừ tận hai lần 852k, quá đáng thật.`
→ Agent **xoa dịu trước**, rồi liệt kê đúng 2 giao dịch 852.000đ cách nhau 37 giây (trùng lặp
thật trong dữ liệu). *(Nó có thể liệt kê thêm giao dịch 853k — đúng dữ liệu, không phải lỗi.)*

**Gõ tiếp:** `dung roi, 2 giao dich 852.000d luc 11:31 ngay 30/06 do, tao ho so giup minh`
→ Ticket được tạo, có mã TCK-xxx.

**Nếu agent hỏi lại thay vì tạo ngay — ĐÓ LÀ ĐIỂM KỂ, không phải lỗi:** *"Ví có 3 giao dịch
quanh 852k, tool báo 'nhiều kết quả khớp' nên agent BẮT BUỘC hỏi lại thay vì tự chọn — sửa cho
nó 'quyết đoán hơn' chính là mở đường cho nó bịa, nên chúng tôi cố ý không sửa."*

**Câu chốt màn:** *"Lưu ý: agent chỉ TẠO HỒ SƠ và ĐỀ XUẤT. Nó không có đường nào tự hoàn tiền —
không phải vì chưa làm, mà vì kiến trúc không tồn tại đường đó. Tiền chỉ đi khi người thật duyệt."*

## Màn 5 — Hỏi CHÍNH SÁCH (RAG) + gặp NGƯỜI THẬT (~1,5 phút)

**5a.** Hỏi một câu chính sách (vd: `phi chuyen tien lien ngan hang la bao nhieu?`) → agent trả
lời kèm **trích nguồn**. **ĐỌC TO** dòng trên màn: *"Kết quả là đoạn trích nguyên văn, không qua
tổng hợp AI"* — tự nó là điểm kể chống bịa.

**5b (tuỳ thời gian).** Bấm **gặp nhân viên thật** → mở tab ẩn danh đăng nhập CSKH `0353000201`
→ nhận ca → nhắn qua lại 2-3 câu → đóng phiên.
**Lời kể:** *"Quyền quyết định gặp người thật là của KHÁCH — một nút bấm, không phải xin xỏ."*
⚠️ Gõ xong một tin, **nhìn ô nhập trống rồi mới gõ tiếp** (lỗi giao diện đã biết khi gõ quá nhanh).

## Màn 6 — Góc nhìn CSKH (~1,5 phút) — kể về ĐIỀU TRA CÓ VẾT

Đăng nhập `0353000201` → **Dashboard** hàng chờ (ticket vừa tạo ở Màn 4 nằm đó — bằng chứng
luồng chạy xuyên suốt) → mở **chi tiết ticket** → chỉ vào **timeline điều tra**: từng bước tool
đã gọi, input, kết quả, thời gian.

**Lời kể:** *"Mỗi kết luận của AI đều có vết: tool nào, hỏi gì, dữ liệu trả về gì, lúc nào.
CSKH và kiểm toán đọc lại được toàn bộ. Đây là audit trail, không phải hộp đen."*
*(Nếu bị hỏi về định dạng kỹ thuật JSON: "bản đang chạy hiển thị dữ liệu thô cho kiểm toán —
bản kế tiếp đã có lớp hiển thị thân thiện cho CSKH, đang trong nhánh phát triển." — đúng sự thật, UI-01 đang làm.)*

**Chỉ thêm:** CSKH **không có nút duyệt nào** trên màn này. *"CSKH điều tra, không quyết."*

## Màn 7 — Góc nhìn SẾP: phê duyệt HITL (~2 phút) — ĐIỂM KẾT MẠNH

Đăng nhập `0905000205` → tab **Phê duyệt** → hàng chờ tóm tắt (KHÔNG có nút duyệt trên card)
→ **"Mở chi tiết →"** → đọc investigation trail + căn cứ → khối **"Quyết định phê duyệt"** →
Duyệt → **OTP step-up gắn đúng đề xuất** → xác nhận.

**Lời kể (3 câu ăn tiền):**
1. *"Muốn duyệt phải MỞ HỒ SƠ đọc đủ căn cứ — HITL không có đường tắt."*
2. *"OTP này gắn với ĐÚNG đề xuất đang duyệt — duyệt 2 hồ sơ là 2 mã khác nhau (dynamic linking)."*
3. *"Ràng buộc 'chỉ sếp duyệt được' và 'người đề xuất không được tự duyệt' nằm ở TẦNG DATABASE —
   viết SQL tay cũng không lách được."*

⚠️ OTP duyệt hết hạn sau 10 phút — demo kéo dài thì xin mã lại, **kể như tính năng** chứ không
phải sự cố. ⚠️ KHÔNG hứa màn hình đổi trạng thái "đã duyệt" ngay hay "xem ai duyệt lúc nào" trên UI.

## Màn 8 (tuỳ chọn, ~1 phút) — Đối tác ví tự quản tri thức

Đăng nhập `0900000001` → tab **Chính sách & FAQ** → cho xem kho tài liệu (2 tài liệu · 338
chunk) / upload.
**Lời kể:** *"Đối tác tự nạp chính sách — agent trả lời theo tài liệu MỚI ngay, không cần đội
kỹ thuật can thiệp. Và vai này CHỈ đụng được kho tri thức, không đụng được tiền hay dữ liệu khách."*

## Câu kết demo

*"Toàn bộ những gì vừa xem chạy trên một nguyên tắc: **AI điều tra — con người quyết định —
mọi con số có vết.** Agent không có quyền chạm tiền, mọi khẳng định truy được về dữ liệu thật,
và các ràng buộc đó không nằm trong lời hứa của chúng tôi — chúng nằm trong database và trong
19 bài test bất biến chạy trên mọi commit."*

---

## PHỤ LỤC — 8 bẫy người demo PHẢI thuộc (từ diễn tập thật)

1. Gõ tay `0974000145` — **không** bấm nút đăng-nhập-nhanh Khách hàng.
2. Chỉ 5 tài khoản trên đăng nhập được; đừng bốc user khác.
3. Câu hỏi-lại về hồ sơ phải chứa chữ **"khiếu nại"/"ticket"** (bộ lọc phạm vi nhạy từ khoá).
   Câu an toàn: *"hồ sơ khiếu nại của mình đang thế nào rồi?"*
4. D2: dừng ở "không tìm thấy", **không** yêu cầu tạo hồ sơ tra thủ công.
5. `[PERSON]` trên màn = che PII đúng — chủ động kể, đừng để khách tự thắc mắc.
6. Sau OTP: **đừng F5**. Live-chat: gõ xong chờ ô trống mới gõ tiếp.
7. Hàng chờ CSKH có nhiều ticket (dữ liệu các đợt kiểm thử tự động) — lời thoại: *"mỗi ticket
   là một lần chạy test thật."* USR-0145 có ~9 khiếu nại — agent đọc số đó là đúng.
8. Một lần lẻ agent mở đầu thẳng "Mình đã tạo hồ sơ…" thiếu câu đồng cảm — dữ liệu vẫn đúng,
   diễn tiếp, đừng dừng chờ.
