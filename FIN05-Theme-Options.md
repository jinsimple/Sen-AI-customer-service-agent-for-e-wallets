# FIN-05 — Bộ 9 phương án màu sắc & typography

Mục đích: đưa file này cho AI coding agent để dựng thành nhiều theme song song trên wireframe hiện tại, phục vụ so sánh trực quan trước khi chốt 1 phương án.

Mỗi phương án có 2 bảng con vì sản phẩm có 2 nhóm người dùng khác nhau:
- **Customer** — giao diện khách hàng (app/chatbot), ưu tiên thân thiện, đa độ tuổi.
- **Agent** — giao diện nội bộ CSKH, dùng liên tục 8 tiếng/ngày, ưu tiên chống mỏi mắt, quét thông tin nhanh.

**Quy ước bắt buộc giữa mọi phương án**: 3 màu trạng thái (`status-warning`, `status-danger`, `status-success`) giữ nguyên ý nghĩa xuyên suốt mọi theme — chỉ đổi sắc thái nền/màu thương hiệu, không đổi ngữ nghĩa màu trạng thái, để CSKH không phải học lại tín hiệu khi đổi theme.

> **Cập nhật 2026-08-13 — đã dựng UI thử nghiệm thật:** `FIN05-Wireframe-UXUI.html` (file wireframe UX/UI đang dùng thật của dự án, khác với `FIN05-Wireframe.html` tài liệu này gốc tham chiếu — file đó không tồn tại trong repo) giờ có **1 bộ chọn màu ở góc trên-phải header**, cạnh nút sáng/tối có sẵn — bấm vào để so sánh trực tiếp cả 9 phương án (5 gốc + 3 mới + màu mặc định đang dùng thật trong file) ngay trên toàn bộ các màn hình wireframe, không cần dựng 5 file HTML tách rời như gợi ý cũ ở mục "Ghi chú cho coding agent" bên dưới.
>
> **Phát hiện khi đối chiếu**: dòng "Option 1 (mặc định hiện tại)" bên dưới đã **lỗi thời** — bản thân `FIN05-Wireframe-UXUI.html` tự ghi rõ trong trang "Tổng quan" rằng đội đã chốt đổi sang tông **"Mận Sen"** (tím-mận, `#4C1D95`/`#C026D3`) thay cho "Trust Navy + Gold" ban đầu, không phải Xanh Ngọc. Bộ chọn màu mới liệt kê tông tím-mận này là lựa chọn đầu tiên, ghi rõ "(mặc định file)" để không gây nhầm lẫn với Option 1 của tài liệu này.

Cách triển khai đã áp dụng trong `FIN05-Wireframe-UXUI.html`: mỗi phương án là 1 object JS (biến `PALETTES`) map vào cùng bộ `--navy/--navy-2/--navy-soft/--gold/--gold-bg/--gold-ink/--bg/--surface/--surface-2/--border/--border-strong/--text/--text-dim/--text-faint` đã dùng trong wireframe (đặt qua `element.style.setProperty` khi chọn, không cần rebuild CSS), cộng thêm 7 token `--chrome-*` riêng cho thanh topbar/tabnav (cố ý luôn tối, tách biệt light/dark mode, giữ bản sắc thương hiệu). `--status-*` (+ `-bg`) giữ nguyên giá trị ở MỌI phương án — đúng quy ước bắt buộc ở trên.

---

## Option 1 — Sen Xanh Ngọc

Định hướng: an tâm, chuyên nghiệp, khớp brand "Sen" đã dựng trong mockup hi-fi.

### Customer

| Token | Hex | Dùng cho |
|---|---|---|
| `--customer-primary` | `#0F6E56` | Nút CTA chính, header |
| `--customer-accent` | `#5DCAA5` | Icon, highlight, progress |
| `--customer-surface` | `#E1F5EE` | Card, badge nền nhạt |
| `--customer-bg` | `#FAF9F6` | Nền trang (trắng ngà, không chói) |
| `--customer-text` | `#04342C` | Chữ chính trên nền sáng |

### Agent (CSKH)

| Token | Hex | Dùng cho |
|---|---|---|
| `--agent-text-primary` | `#2C2C2A` | Chữ chính |
| `--agent-text-secondary` | `#5F5E5A` | Nhãn phụ, timestamp |
| `--agent-surface-card` | `#EDEBE4` | Card, khung case |
| `--agent-bg` | `#F5F4EF` | Nền trang (off-white) |
| `--agent-action` | `#185FA5` | Nút thao tác, link |

### Trạng thái (dùng chung mọi theme)

| Token | Hex nền | Hex chữ/nhấn | Ý nghĩa |
|---|---|---|---|
| `--status-warning` | `#FAEEDA` | `#854F0B` | Chờ xử lý |
| `--status-danger` | `#FCEBEB` | `#791F1F` | Nghi gian lận / lỗi |
| `--status-success` | `#EAF3DE` | `#27500A` | Đã duyệt / hoàn tất |

### Typography

| Cấp | Font | Size / Weight | Line-height |
|---|---|---|---|
| Tiêu đề màn hình | Space Grotesk | 24px / 500 | 1.3 |
| Nội dung, chat | Inter | 16px / 400 | 1.6 |
| Nhãn phụ | Inter | 14px / 400 | 1.5 |
| Số tiền, mã GD | JetBrains Mono | 15px / 500 | 1.4 |

---

## Option 2 — Đại Dương Tín Nhiệm

Định hướng: quy ước màu xanh dương của ngành ngân hàng, tạo cảm giác an toàn/tin cậy tức thì, phù hợp khi pitch với đối tác ví điện tử.

### Customer

| Token | Hex | Dùng cho |
|---|---|---|
| `--customer-primary` | `#0C447C` | Nút CTA chính, header |
| `--customer-accent` | `#378ADD` | Icon, highlight |
| `--customer-surface` | `#E6F1FB` | Card, badge nền nhạt |
| `--customer-bg` | `#F7FAFD` | Nền trang |
| `--customer-text` | `#042C53` | Chữ chính |

### Agent (CSKH)

| Token | Hex | Dùng cho |
|---|---|---|
| `--agent-text-primary` | `#26313D` | Chữ chính |
| `--agent-text-secondary` | `#5C6B7A` | Nhãn phụ |
| `--agent-surface-card` | `#E8EDF2` | Card |
| `--agent-bg` | `#F4F6F8` | Nền trang |
| `--agent-action` | `#0F6E56` | Nút thao tác (màu lệch khỏi xanh dương để phân biệt với trạng thái thông tin) |

Trạng thái: dùng chung bảng ở Option 1.

### Typography

| Cấp | Font | Size / Weight | Line-height |
|---|---|---|---|
| Tiêu đề màn hình | Manrope | 24px / 500 | 1.3 |
| Nội dung, chat | Source Sans 3 | 16px / 400 | 1.6 |
| Nhãn phụ | Source Sans 3 | 14px / 400 | 1.5 |
| Số tiền, mã GD | IBM Plex Mono | 15px / 500 | 1.4 |

---

## Option 3 — Đất Ấm

Định hướng: tông ấm (terracotta/cam đất), giảm cảm giác lạnh lẽo của app tài chính, thân thiện hơn với người lớn tuổi, ánh sáng ấm cũng đỡ mỏi mắt hơn vào buổi tối.

### Customer

| Token | Hex | Dùng cho |
|---|---|---|
| `--customer-primary` | `#993C1D` | Nút CTA chính, header |
| `--customer-accent` | `#F0997B` | Icon, highlight |
| `--customer-surface` | `#FAECE7` | Card, badge nền nhạt |
| `--customer-bg` | `#FDF8F4` | Nền trang |
| `--customer-text` | `#4A1B0C` | Chữ chính |

### Agent (CSKH)

| Token | Hex | Dùng cho |
|---|---|---|
| `--agent-text-primary` | `#33291F` | Chữ chính |
| `--agent-text-secondary` | `#6B5D4F` | Nhãn phụ |
| `--agent-surface-card` | `#F0E9E0` | Card |
| `--agent-bg` | `#F8F4EE` | Nền trang |
| `--agent-action` | `#185FA5` | Nút thao tác |

Trạng thái: dùng chung bảng ở Option 1.

### Typography

| Cấp | Font | Size / Weight | Line-height |
|---|---|---|---|
| Tiêu đề màn hình | Lexend | 24px / 500 | 1.3 |
| Nội dung, chat | Noto Sans | 16px / 400 | 1.65 (hỗ trợ dấu tiếng Việt tốt) |
| Nhãn phụ | Noto Sans | 14px / 400 | 1.5 |
| Số tiền, mã GD | Roboto Mono | 15px / 500 | 1.4 |

---

## Option 4 — Ca Đêm Tối Màu

Định hướng: CSKH có ca trực đêm — bảng agent mặc định dark mode để giảm chói khi phòng tối, giao diện khách hàng vẫn giữ sáng nhưng tông tím-xanh trầm hơn để hai bên có nhận diện thương hiệu nhất quán.

### Customer (light)

| Token | Hex | Dùng cho |
|---|---|---|
| `--customer-primary` | `#3C3489` | Nút CTA chính, header |
| `--customer-accent` | `#7F77DD` | Icon, highlight |
| `--customer-surface` | `#EEEDFE` | Card, badge nền nhạt |
| `--customer-bg` | `#FAFAFA` | Nền trang |
| `--customer-text` | `#26215C` | Chữ chính |

### Agent (dark mode mặc định)

| Token | Hex | Dùng cho |
|---|---|---|
| `--agent-bg` | `#1C1C1E` | Nền trang |
| `--agent-surface-card` | `#26262A` | Card |
| `--agent-border` | `#38383C` | Viền, phân cách |
| `--agent-text-primary` | `#EDEDED` | Chữ chính |
| `--agent-text-secondary` | `#A8A8AC` | Nhãn phụ |
| `--agent-action` | `#85B7EB` | Nút thao tác, link (đủ tương phản trên nền tối) |

### Trạng thái trên nền tối (thay bằng stop sáng hơn để đủ tương phản)

| Token | Hex | Ý nghĩa |
|---|---|---|
| `--status-warning-dark` | `#FAC775` | Chờ xử lý |
| `--status-danger-dark` | `#F09595` | Nghi gian lận / lỗi |
| `--status-success-dark` | `#97C459` | Đã duyệt / hoàn tất |

### Typography

| Cấp | Font | Size / Weight | Line-height |
|---|---|---|---|
| Tiêu đề màn hình | Work Sans | 24px / 500 | 1.3 |
| Nội dung, chat | IBM Plex Sans | 16px / 400 | 1.6 |
| Nhãn phụ | IBM Plex Sans | 14px / 400 | 1.5 |
| Số tiền, mã GD | JetBrains Mono | 15px / 500 | 1.4 |

---

## Option 5 — Tối Giản Đơn Sắc

Định hướng: xám hóa toàn bộ UI, chỉ giữ đúng 1 màu nhấn — kiểu Stripe/Linear. Ít nhiễu thị giác nhất, phù hợp nếu ưu tiên tốc độ xử lý case của CSKH hơn là cảm xúc thương hiệu.

### Customer

| Token | Hex | Dùng cho |
|---|---|---|
| `--customer-primary` | `#1F1F1F` | Chữ tiêu đề, nút chính |
| `--customer-accent` | `#0F6E56` | CTA, link — màu nhấn DUY NHẤT |
| `--customer-surface` | `#F7F7F5` | Card |
| `--customer-bg` | `#FFFFFF` | Nền trang |
| `--customer-text` | `#1F1F1F` | Chữ chính |

### Agent (CSKH)

| Token | Hex | Dùng cho |
|---|---|---|
| `--agent-text-primary` | `#262626` | Chữ chính |
| `--agent-text-secondary` | `#6B6B68` | Nhãn phụ |
| `--agent-surface-card` | `#FFFFFF` (viền `#E2E1DC`) | Card |
| `--agent-bg` | `#FAFAF8` | Nền trang |
| `--agent-action` | `#0F6E56` | Nút thao tác — cùng màu nhấn với customer |

Trạng thái: dùng chung bảng ở Option 1, nhưng chỉ hiển thị dưới dạng **chấm màu nhỏ (dot) hoặc badge viền**, không tô nền toàn khối — giữ đúng tinh thần tối giản.

### Typography

| Cấp | Font | Size / Weight | Line-height |
|---|---|---|---|
| Tiêu đề màn hình | Inter | 22px / 500 | 1.3 |
| Nội dung, chat | Inter | 16px / 400 | 1.6 |
| Nhãn phụ | Inter | 14px / 400 | 1.5 |
| Số tiền, mã GD | JetBrains Mono | 15px / 500 | 1.4 |

---

## Option 6 — Ngọc Bích San Hô *(mới)*

Định hướng: teal-cyan đậm hơn hẳn Option 1 (bão hòa cao, không dịu) ghép với accent coral ấm — cặp bổ túc lạnh/nóng, tạo cảm giác fintech hiện đại kiểu app đầu tư/thanh toán trẻ trung, khác biệt rõ với sắc "an toàn ngân hàng" của Option 1/2.

### Customer

| Token | Hex | Dùng cho |
|---|---|---|
| `--customer-primary` | `#0E7C86` | Nút CTA chính, header |
| `--customer-accent` | `#FF6B5B` | Icon, highlight, nút gửi/hành động nổi bật |
| `--customer-surface` | `#DFF3F3` | Card, badge nền nhạt |
| `--customer-bg` | `#F5FBFB` | Nền trang |
| `--customer-text` | `#0A2E31` | Chữ chính |

### Agent (CSKH)

| Token | Hex | Dùng cho |
|---|---|---|
| `--agent-text-primary` | `#123034` | Chữ chính |
| `--agent-text-secondary` | `#4C7276` | Nhãn phụ |
| `--agent-surface-card` | `#E7F4F4` | Card |
| `--agent-bg` | `#F3F9F9` | Nền trang |
| `--agent-action` | `#0E7C86` | Nút thao tác — cùng họ với customer, giữ nhất quán thương hiệu |

Trạng thái: dùng chung bảng ở Option 1.

### Typography

| Cấp | Font | Size / Weight | Line-height |
|---|---|---|---|
| Tiêu đề màn hình | Sora | 24px / 500 | 1.3 |
| Nội dung, chat | Karla | 16px / 400 | 1.6 |
| Nhãn phụ | Karla | 14px / 400 | 1.5 |
| Số tiền, mã GD | Fira Code | 15px / 500 | 1.4 |

---

## Option 7 — Than Chì Chanh Cốm *(mới)*

Định hướng: primary gần như đen (charcoal) thay vì bất kỳ hue "an toàn" nào, ghép accent chanh-cốm rực — độ tương phản cao nhất trong mọi phương án, hướng thẩm mỹ kiểu app fintech thế hệ mới (Revolut/Robinhood). Rủi ro: charcoal-làm-màu-thương-hiệu-chính dễ bị đọc nhầm là "nghiêm trọng/cảnh báo" nếu dùng sai chỗ — luôn giữ 3 màu trạng thái tách biệt hoàn toàn khỏi `--customer-primary`.

### Customer

| Token | Hex | Dùng cho |
|---|---|---|
| `--customer-primary` | `#1C1F26` | Nút CTA chính, header |
| `--customer-accent` | `#A6D608` | CTA nổi bật, nút gửi, badge |
| `--customer-surface` | `#EEF0F3` | Card, badge nền nhạt |
| `--customer-bg` | `#FAFBFC` | Nền trang |
| `--customer-text` | `#14161B` | Chữ chính |

### Agent (CSKH)

| Token | Hex | Dùng cho |
|---|---|---|
| `--agent-text-primary` | `#181A20` | Chữ chính |
| `--agent-text-secondary` | `#565C68` | Nhãn phụ |
| `--agent-surface-card` | `#F1F2F5` | Card |
| `--agent-bg` | `#F8F9FA` | Nền trang |
| `--agent-action` | `#1C1F26` | Nút thao tác — cùng charcoal, accent chanh chỉ dành riêng cho CTA khách hàng |

Trạng thái: dùng chung bảng ở Option 1.

### Typography

| Cấp | Font | Size / Weight | Line-height |
|---|---|---|---|
| Tiêu đề màn hình | Archivo | 24px / 700 | 1.25 |
| Nội dung, chat | DM Sans | 16px / 400 | 1.6 |
| Nhãn phụ | DM Sans | 14px / 400 | 1.5 |
| Số tiền, mã GD | Space Mono | 15px / 500 | 1.4 |

---

## Option 8 — Hồng Đất Sa Mạc *(mới)*

Định hướng: dusty rose/mận đất ghép sand/ochre — ấm nhưng khác hẳn Option 3 (Option 3 nghiêng cam-nâu, option này nghiêng hồng-đỏ đất, "mềm" và có phần sang trọng hơn). Phù hợp nếu muốn một lựa chọn thân thiện nhưng không bị đọc nhầm thành cảnh báo/nguy hiểm (rose ở đây tối và trầm, khác hẳn đỏ status-danger).

### Customer

| Token | Hex | Dùng cho |
|---|---|---|
| `--customer-primary` | `#A64B5C` | Nút CTA chính, header |
| `--customer-accent` | `#C99A4A` | Icon, highlight, badge vàng đất |
| `--customer-surface` | `#F7E9E7` | Card, badge nền nhạt |
| `--customer-bg` | `#FDF7F5` | Nền trang |
| `--customer-text` | `#3D1620` | Chữ chính |

### Agent (CSKH)

| Token | Hex | Dùng cho |
|---|---|---|
| `--agent-text-primary` | `#33161C` | Chữ chính |
| `--agent-text-secondary` | `#6E4048` | Nhãn phụ |
| `--agent-surface-card` | `#F4E4E1` | Card |
| `--agent-bg` | `#FAF1EF` | Nền trang |
| `--agent-action` | `#185FA5` | Nút thao tác (lệch sang xanh dương để phân biệt rõ với trạng thái, cùng nguyên tắc ở Option 1/3) |

Trạng thái: dùng chung bảng ở Option 1.

### Typography

| Cấp | Font | Size / Weight | Line-height |
|---|---|---|---|
| Tiêu đề màn hình | Fraunces | 24px / 500 | 1.3 |
| Nội dung, chat | Karla | 16px / 400 | 1.6 |
| Nhãn phụ | Karla | 14px / 400 | 1.5 |
| Số tiền, mã GD | JetBrains Mono | 15px / 500 | 1.4 |

*(Fraunces là serif — lựa chọn có chủ đích, khác hẳn 8 phương án còn lại đều dùng sans cho tiêu đề, tạo cảm giác ấm/biên tập phù hợp tông màu đất-hồng. Nếu team muốn giữ hệ thống chữ đồng nhất tuyệt đối xuyên suốt mọi theme, đổi lại thành Lexend hoặc Work Sans cũng ổn.)*

---

## Bảng so sánh nhanh

| # | Tên | Tông chủ đạo | Ưu tiên chính | Rủi ro cần lưu ý |
|---|---|---|---|---|
| 1 | Sen Xanh Ngọc | Xanh lá-ngọc | Cân bằng, an toàn | Không có gì nổi bật để phân biệt cạnh tranh |
| 2 | Đại Dương Tín Nhiệm | Xanh dương | Tín nhiệm kiểu ngân hàng | Dễ trộn lẫn với UI ngân hàng khác, kém khác biệt |
| 3 | Đất Ấm | Cam đất | Thân thiện, giảm mỏi mắt buổi tối | Cam/đỏ đất dễ liên tưởng nhầm sang màu cảnh báo nếu dùng sai chỗ |
| 4 | Ca Đêm Tối Màu | Tím trầm + dark mode | Chống chói cho ca trực đêm | Cần build thêm bộ token dark mode riêng, tốn công hơn |
| 5 | Tối Giản Đơn Sắc | Xám + 1 accent | Tốc độ quét case nhanh nhất | Có thể bị chê "nhạt", thiếu cảm xúc thương hiệu khi demo |
| 6 | Ngọc Bích San Hô | Teal đậm + coral | Hiện đại, trẻ trung, khác biệt hoá | Bão hòa cao — cần kiểm tương phản kỹ ở trạng thái hover/disabled |
| 7 | Than Chì Chanh Cốm | Charcoal + chanh cốm | Tương phản cao nhất, tốc độ đọc | Charcoal-làm-primary dễ lẫn cảm giác "nghiêm trọng" nếu dùng sai chỗ |
| 8 | Hồng Đất Sa Mạc | Hồng đất + sa mạc | Ấm áp, sang trọng, không lẫn màu cảnh báo | Kén thị hiếu hơn (hồng/mận có thể không hợp mọi đối tượng khách hàng) |

## Ghi chú cho coding agent

1. Toàn bộ theme dùng chung layout, spacing, icon set của wireframe — chỉ đổi biến màu và font, không đổi cấu trúc HTML.
2. Cỡ chữ nội dung tối thiểu 16px ở phía customer (đa độ tuổi); phía agent có thể 14–15px nhưng không thấp hơn.
3. Với mọi theme, chữ đặt trên nền màu (badge, pill) phải dùng đúng stop đậm cùng họ màu — không dùng đen thuần hay xám generic.
4. ~~Nên dựng 1 trang demo có dropdown chuyển theme để so sánh trực tiếp~~ — **đã có**, xem ghi chú "Cập nhật 2026-08-13" ở đầu file: bộ chọn màu ở góc trên-phải `FIN05-Wireframe-UXUI.html`.
5. `--status-*` (+ `-bg`) là NHÓM DUY NHẤT không đổi qua mọi phương án, kể cả 3 option mới — nếu bổ sung thêm phương án sau này, giữ nguyên tắc này.
