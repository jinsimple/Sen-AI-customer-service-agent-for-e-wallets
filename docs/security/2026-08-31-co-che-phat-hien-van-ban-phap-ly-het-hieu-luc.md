# Cơ chế phát hiện văn bản pháp lý hết hiệu lực

> Vai: `security`. Viết sau một đêm phát hiện: NĐ 13/2023 hết hiệu lực từ 01/01/2026, nhưng cả đội
> (kể cả tôi) không biết cho tới 30/08 — **8 tháng sau**, và chỉ phát hiện vì một chuỗi giao diện
> tình cờ lọt vào một tấm ảnh chụp màn hình chuẩn bị quay video. Không có cơ chế nào bắt được sớm
> hơn — kể cả chính tài liệu tôi viết để niêm phát hiện đó cũng chứa một lỗi lý luận (xem
> `docs/security/2026-08-30-niem-luat-91-2025-thay-nd-13-2023.md`, mục "TỰ SỬA 31/08").
>
> Mục tiêu tài liệu này: lần sau, phát hiện KHÔNG phụ thuộc may rủi của một tấm ảnh.

## ① Dự án đang dựa trên NHỮNG văn bản nào — một chỗ duy nhất

| Văn bản | Phạm vi | Trạng thái xác minh |
|---|---|---|
| **NĐ 52/2024/NĐ-CP** | Trung gian thanh toán | Hiện hành theo `CLAUDE.md §8`. **Chưa đối chiếu ngày hiệu lực chính xác / tới cấp điều khoản** — dự án tự khai giới hạn này (`presentation/FIN05_Slide_Prompt_Context.md:11`). |
| **TT 40/2024/TT-NHNN** | Cùng chủ đề, thay TT 39/2014 (đã hết hiệu lực) | Hiện hành theo `CLAUDE.md §8`. Cùng giới hạn "chưa đối chiếu điều khoản" như trên. |
| **Luật 91/2025/QH15 + NĐ 356/2025/NĐ-CP** | Bảo vệ dữ liệu cá nhân (PDPA) | Hiệu lực **01/01/2026**, thay TOÀN BỘ NĐ 13/2023. **Đã đọc toàn văn Luật** (PO, 31/08, PDF ký số VPCP) — NĐ 356/2025 (42 điều, danh mục "dữ liệu nhạy cảm") **CHƯA đọc toàn văn**, một số kết luận trong `docs/security/2026-08-30-C4-*.md` còn treo vì thiếu bước này. |
| **QĐ 2345/QĐ-NHNN** | Ngưỡng xác thực sinh trắc (10tr/lần, 20tr/ngày) — **KHÔNG** phải ngưỡng gian lận, dễ nhầm | Hiện hành theo `CLAUDE.md §8`. Chưa xác minh ngày hiệu lực chính xác. |

⚠️ **Bảng này TỰ NÓ có thể lạc hậu** — xem mục ② để biết cách giữ nó cập nhật, đừng coi bảng trên là
vĩnh viễn đúng chỉ vì vừa viết hôm nay.

## ② Ai kiểm lại, bao lâu một lần, bằng cách nào

**Hiện KHÔNG có cơ chế nào** — đây chính là lỗ hổng vừa trả giá 8 tháng phát hiện muộn. Đề xuất, rẻ,
gắn vào nghi thức đã có sẵn thay vì bày thêm việc mới:

- **Ai:** vai `security` (đúng vùng ghi `docs/security/` theo `CLAUDE.md §4`).
- **Bao lâu:** mỗi lần chạy `/wrapup` cuối phiên có chạm tới bất kỳ văn bản nào ở bảng ①, **VÀ** tối
  thiểu một lần mỗi tháng bất kể có việc gì hay không (luật có thể đổi mà không ai chủ động chạm tới
  chủ đề đó — đúng kiểu sự cố vừa xảy ra, 8 tháng liền không ai có lý do để nhìn lại).
- **Bằng cách nào — 1 câu hỏi, không cần điều tra sâu:** với MỖI văn bản ở bảng ①, tra
  "`<số hiệu văn bản> còn hiệu lực không`" trên `thuvienphapluat.vn` hoặc `luatvietnam.vn` (đã dùng
  tối nay, tin cậy được), đọc đúng MỘT dòng: còn hiệu lực / đã thay thế bởi văn bản nào. **Không cần
  đọc toàn văn định kỳ** — chỉ cần biết "còn sống hay đã chết", đọc toàn văn chỉ khi có việc THẬT cần
  trích điều khoản cụ thể (như C4/DPIA đang cần).
- **Tín hiệu báo động sớm, rẻ hơn cả lịch định kỳ:** bất cứ khi nào một phiên `security` chuẩn bị
  TRÍCH một văn bản trong bảng ① vào tài liệu MỚI, tự hỏi một câu trước khi gõ: *"lần cuối tôi xác
  nhận văn bản này còn sống là khi nào?"* — nếu câu trả lời là "không nhớ"/"chưa từng", dừng lại tra
  trước khi trích, đừng trích rồi tính sau.

## ③ Khi một văn bản đổi, phải sửa NHỮNG ĐÂU — 5 nơi, đêm nay mới lộ hết

Trước 30/08, không ai biết danh sách này có 5 chỗ — mỗi chỗ lộ ra một cách khác nhau, rải trong 8
tháng, không cơ chế nào gom chúng lại. Ghi đủ một lần, để lần sau sửa 1 văn bản thì đi hết cả 5, không
phải chờ 5 người tình cờ vấp phải 5 chỗ như đêm nay.

| # | Nơi | Vì sao dễ bỏ sót | Ví dụ đêm 31/08 |
|---|---|---|---|
| 1 | **`CLAUDE.md §8`** | Tưởng chỉ là tài liệu tham khảo, không phải "nguồn" — nhưng nó nạp vào **MỌI phiên Claude**, nên trích sai ở đây lan ra khắp nơi | Gốc rễ thật của cả 5 chỗ — PO sửa `82c1791` |
| 2 | **`docs/security/*.md`** | Số lượng file lớn (~100), viết rải rác nhiều tháng, không ai đọc lại hết một lượt | 2 file security cần sửa/niêm đêm nay (C4, và chính file niêm luật) |
| 3 | **Chuỗi hiển thị UI (`frontend/src/`)** | KHÔNG NẰM TRONG "tài liệu" theo nghĩa thường — kỹ sư không nghĩ tới khi rà soát pháp lý, chỉ lộ khi nhìn MÀN HÌNH THẬT | 3 chỗ (`ChatClient.tsx`, `TicketDetailClient.tsx`, `page.tsx`) — chỉ phát hiện vì chuẩn bị quay video, đọc ảnh chụp màn hình |
| 4 | **Chú thích trong `src/` (code comment)** | Không hiện ra ngoài, không lên UI/video — dễ bị coi là "vô hại", nhưng đọc được bởi bất kỳ ai xem code (kể cả đối tác kiểm toán/audit code) | `config.py:547`, `agents/prompt.py:81` — cố ý hoãn sửa, không phải bỏ sót |
| 5 | **Prompt của agent (`src/agents/prompt.py`)** | Nặng nhất trong 5 chỗ, dễ bỏ sót nhất: đây không chỉ là "chữ", mà là **NHỮNG GÌ AGENT CÓ THỂ NÓI VỚI KHÁCH** nếu phần liên quan bị lộ ra qua injection hoặc bị hỏi trực tiếp — trích sai văn bản pháp lý ở đây có thể khiến agent tự tin nói SAI căn cứ pháp lý cho khách hàng thật | Cùng dòng với #4 (`prompt.py:81`), cố ý gộp sửa cùng đợt với cổng ép-tra-trước vì đổi prompt đổi băm mã nguồn |

**Thứ tự sửa khi phát hiện một văn bản đổi:** 1 → 2 → (3, 4, 5 làm song song, không phụ thuộc nhau) —
sửa gốc (`CLAUDE.md`) trước để mọi phiên sau đọc đúng ngay, rồi mới dọn các nhánh đã trót trích sai.

## Tiền lệ đêm nay — ví dụ dùng được, đừng để trôi

**Phát hiện muộn 8 tháng** (luật hiệu lực 01/01/2026, phát hiện 30/08/2026), **chỉ lộ do một chuỗi
giao diện tình cờ lọt vào ảnh chụp màn hình** chuẩn bị cho một việc hoàn toàn khác (quay video demo,
không phải rà soát pháp lý). Không ai chủ động đi tìm — nếu không có buổi quay video, khoảng trống
này có thể còn kéo dài vô thời hạn. Đây chính là lý do mục ② đề xuất một tần suất TỐI THIỂU không phụ
thuộc có việc gì đang làm hay không — may rủi không phải một chiến lược.
