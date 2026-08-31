# "Dữ liệu khách hàng của chúng tôi đi những đâu?" — một trang, để trả lời trước ZaloPay/VNPT

> Vai: `security`. Câu hỏi khó nhất, không phải điểm benchmark. Nguồn: `docs/security/2026-08-17-kiem-ke-du-lieu-roi-bien-gioi-cho-ho-so-D25.md`
> (kiểm kê kỹ thuật) + `docs/security/2026-08-30-C4-dpia-dieu25-khung-draft.md` + đọc toàn bộ
> `docs/DECISIONS.md` (31/08). Không có tuyên bố tuyệt đối, không dùng chữ viết tắt tuân thủ.

## 1. Cái gì RỜI hạ tầng, tới đâu

| Dữ liệu | Tới nhà cung cấp nào | Ghi chú |
|---|---|---|
| **Văn bản khách gõ** — mô tả khiếu nại, tin chat | Alibaba DashScope (Singapore lưu, xử lý tại node toàn cầu ngoài TQ đại lục) | **NGUYÊN VĂN, không che** — kể cả khi chứa SĐT/tên người khác khách tự gõ vào (vd "chuyển nhầm cho anh X, sđt 09…") |
| **Truy vấn RAG** dẫn từ lời khách | OpenAI (`text-embedding-3-small`) | Nhúng để tìm chính sách liên quan — cũng nguyên văn |
| **Nội dung tài liệu chính sách** (chunk) | Cả hai (Alibaba đọc, OpenAI nhúng) | Tài liệu của đối tác ví, không phải dữ liệu khách |
| **Số tiền · mã giao dịch · thời điểm · trạng thái** | Alibaba | Rời **có chủ đích** — agent cần dữ liệu thật để trích dẫn, không được bịa (ràng buộc cứng #3) |

## 2. Cái gì KHÔNG rời — hoặc rời đã được che

- **Họ tên / SĐT / số tài khoản trong KẾT QUẢ TRA CỨU** (khác với khách tự gõ) — bị che **trước khi**
  vào mô hình (`_scrub_pii_cho_llm`), che theo tên trường, không theo regex đoán nội dung.
- **Tên khách không bao giờ vào system prompt** (ADR-010, gỡ 13/08).
- Toàn bộ nội dung (kể cả phần rời sang mô hình) **cũng được lưu mã hoá tại chỗ** trong CSDL
  (`messages.content`, `complaints.description_raw` — `EncryptedText`). ⚠️ **Đây là hai lớp bảo vệ
  KHÁC NHAU, đừng gộp**: mã hoá tại chỗ bảo vệ dữ liệu NẰM Ở ĐÂU (ai đọc được ổ đĩa/CSDL), không bảo
  vệ được dữ liệu ĐÃ RỜI sang mô hình — một khi đã gửi, bản mã hoá trong DB không kéo lại được bản đã
  đi.

## 3. Chốt chặn ĐANG CÓ

- Mã hoá **mức trường** cho nội dung nhạy cảm (không phải mã hoá toàn ổ đĩa/toàn CSDL).
- Che PII theo tên trường ở kết quả tra cứu, trước khi vào mô hình.
- Cách ly khoá API theo từng nhà cung cấp — khoá của bên này không rơi sang bên kia dù đổi cấu hình
  (`_khoa_cho_nha_cung_cap`, vá sau một sự cố thật 17/08).
- Đo được, không suy đoán: che dữ liệu làm méo câu tiếng Việt **4,8%** (6/124 câu, `eval/do_bop_meo_pii.py`,
  chạy 30/08) — cái giá của việc che, và vì sao che RỘNG hơn không khả thi cho văn bản tự do (thử che
  rộng: méo tới 40%, phá cả nghĩa câu).
- Đọc dữ liệu điều tra theo nguyên tắc need-to-know + ghi log MỌI lượt đọc, kể cả người có quyền hợp
  lệ (ADR-025 Quyết định 2, ký 15/08).
- Cam kết không dùng dữ liệu để huấn luyện — **mức trang tài liệu công khai của nhà cung cấp, chưa
  phải mức điều khoản hợp đồng đã ký**.

## 4. Chốt chặn CHƯA CÓ — nói thẳng

- **Văn bản tự do của khách không che được** trước khi rời hạ tầng — đây là **quyết định thiết kế có
  ý thức** (che sẽ phá nghĩa câu), không phải thiếu sót kỹ thuật, nhưng vẫn là một khoảng trống thật.
- **Dữ liệu của NGƯỜI THỨ BA** (do khách tự gõ vào, chưa từng đồng ý) rời biên giới cùng văn bản trên
  — chưa có cơ chế nào tách/che riêng trường hợp này.
- **Chưa xác nhận công tắc phía nhà cung cấp**: cả Alibaba (tính năng "Model monitoring" ghi
  input/output, bật bằng một nút trên console, chưa ai kiểm có bật không) và OpenAI (stored
  completions/org logging) — đây là cấu hình phía họ, không có gì trong mã của chúng tôi nhìn thấy.
- **Chưa có hồ sơ đánh giá tác động chuyển dữ liệu chính thức** (DPIA) — vật liệu kỹ thuật đã đủ, còn
  thiếu bước ký của người có thẩm quyền pháp lý. Mốc "60 ngày kể từ lần xử lý dữ liệu thật đầu tiên"
  (Đ.21.1) **chưa xác định được đã chạy hay chưa** — bằng chứng hiện có (log máy dev, 15/08→30/08,
  không thấy IP/danh tính thật) nghiêng về "chưa", nhưng chỉ log production mới trả lời dứt điểm.
- **Chưa có bộ lọc chặn cứng cho số thẻ (PAN)** nếu khách vô tình gõ vào ô mô tả — chỉ có bộ nhận diện
  PII mềm (Presidio), không đảm bảo bắt hết.

## 5. Nếu khách yêu cầu XOÁ dữ liệu — làm được tới đâu HÔM NAY

**Câu trả lời trung thực: chưa có nút nào.** Không có route tự phục vụ (không có
`DELETE /users/me` hay `GET /users/me/data-export` trong 34 route hiện có — đã kiểm đủ, không phải
suy đoán).

Nhưng **không phải "chưa ai nghĩ tới"** — có hai quyết định đã ký, mô tả HỆ THỐNG sẽ tự xoá theo
lịch (khác với khách TỰ YÊU CẦU xoá bất cứ lúc nào):
- **ADR-025 Quyết định 3** (15/08, đã ký): hồ sơ khiếu nại giữ **5 năm** kể từ ticket đóng rồi xoá
  hoặc ẩn danh hoá không đảo ngược. Đã tự cảnh báo: **không được dùng crypto-shredding** để xoá (khoá
  mã hoá dùng chung cho nhiều bảng, huỷ khoá sẽ phá luôn dữ liệu khác) — phải xoá dòng thật.
- **ADR-045b** (24/08, PO quyết): lịch sử hội thoại giữ **90 ngày** rồi xoá.
- **Cả hai CHƯA được lập trình** — không có job xoá theo lịch nào chạy trong hệ thống hôm nay (đã
  kiểm bằng grep, không suy đoán).

⟹ **Câu trả lời đầy đủ, dùng được trước người thẩm định:** *"Hôm nay, nếu một khách hàng yêu cầu xoá
dữ liệu, chúng tôi không có quy trình tự phục vụ — sẽ cần can thiệp tay của kỹ sư, chưa phải một quy
trình được hỗ trợ. Chúng tôi đã quyết định chính sách giữ dữ liệu có thời hạn (5 năm cho hồ sơ khiếu
nại, 90 ngày cho lịch sử hội thoại), nhưng chưa lập trình cơ chế tự xoá theo lịch đó. Cả hai — route
tự phục vụ và cơ chế xoá tự động — đang trong backlog, chưa có ngày cam kết cụ thể."* Đây là câu làm
**tăng** uy tín trước một người thẩm định thật, không phải làm giảm.
