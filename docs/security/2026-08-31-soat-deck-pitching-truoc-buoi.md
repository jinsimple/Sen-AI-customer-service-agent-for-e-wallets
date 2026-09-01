# Soát `presentation/FIN05_Slide_Prompt_Context.md` — 31/08/2026, trước buổi

> Vai: `security`. Giao trực tiếp từ PO (qua Lead), ưu tiên TRÊN việc đọc nốt ADR vì "sửa được ngay
> trong vài giờ tới, ADR thì không". Duyệt MỌI câu chạm bảo mật/xác thực/quyền riêng tư/pháp lý,
> xếp vào ✅ CHỨNG MINH ĐƯỢC / ⚠️ CẦN KHAI PHẠM VI / 🔴 PHẢI CẮT.

## 🔴 PHẢI CẮT hoặc SỬA NGAY — 3 mục, xếp theo mức nghiêm trọng

### 1. 🔴🔴 Dòng 33 + Slide 7 (dòng 138) — "Dữ liệu cá nhân được che trước khi đưa vào mô hình" / "Data nằm gọn trong hạ tầng. An toàn dữ liệu tuyệt đối"

**Đây là câu SAI RÕ RÀNG nhất trong toàn bộ deck, và nó nằm ở đúng slide sẽ bị soi kỹ nhất
(bảo mật dữ liệu).** Đối chiếu với chính hồ sơ dự án đã có:

- `docs/security/2026-08-17-kiem-ke-du-lieu-roi-bien-gioi-cho-ho-so-D25.md §2`: **"Văn bản khách gõ
  (mô tả khiếu nại · tin chat) — RỜI NGUYÊN VĂN, không che được"** — che sẽ phá nghĩa câu (đã đo:
  S-01 chặn nhầm 40% văn bản nghiệp vụ tiếng Việt). Đây là **quyết định thiết kế có chủ đích**, ghi
  rõ trong hồ sơ, KHÔNG phải điều có thể lờ đi khi lên slide.
- Hệ quả: nếu khách gõ *"em chuyển nhầm cho anh X, sđt 09…"*, chuỗi đó **rời nguyên văn sang Alibaba
  DashScope (Singapore, xử lý tại node toàn cầu ngoài TQ đại lục)**, kể cả khi chứa dữ liệu của
  NGƯỜI THỨ BA chưa từng đồng ý. Đây là khoảng trống pháp lý nặng nhất dự án đang biết, tự khai rõ
  trong hồ sơ D25/C4.
- Câu **"Data nằm gọn trong hạ tầng"** (Slide 7) mâu thuẫn TRỰC TIẾP với sự thật trên — dữ liệu
  chat KHÔNG nằm gọn trong hạ tầng, nó rời sang hai nhà cung cấp LLM ở hai tài phán khác nhau.
- Cụm **"An toàn dữ liệu tuyệt đối"** là tuyên bố TUYỆT ĐỐI — cùng loại rủi ro với "0% Hallucination"
  mà chính deck đã tự nhận diện và cấm ở nơi khác (dòng 30-32). Không nhất quán khi cấm kiểu câu này
  ở một chỗ mà vẫn dùng ở chỗ khác.

**Đề xuất sửa (giữ đúng phần ĐÚNG của câu gốc, cắt phần sai):**
> *"Dữ liệu có cấu trúc (SĐT, tên, số tài khoản) được che trước khi vào mô hình — che ở đúng tầng dữ
> liệu, không phải tầng hiển thị, nên không có đường vòng nào qua UI để lộ. Văn bản tự do khách gõ
> đi qua mã hoá tại chỗ lưu và không đưa tên khách vào system prompt; đây là ranh giới thật, không
> phải giới hạn kỹ thuật tạm thời — nói rõ nếu bị hỏi sâu."*

Nếu không có thời gian viết lại kỹ, **ít nhất phải bỏ hai cụm "che TRƯỚC KHI đưa vào mô hình" (dùng
cho toàn bộ dữ liệu cá nhân) và "An toàn dữ liệu tuyệt đối"/"nằm gọn trong hạ tầng"** — đây là loại
câu một kỹ sư bảo mật của ZaloPay/VNPT Money sẽ hỏi thẳng, và câu trả lời hiện có trong chính hồ sơ
dự án lại **mâu thuẫn** với slide.

### 2. 🔴 Dòng 238-239 (Slide 11) — Đ.38.2: khẳng định CHẮC CHẮN "KHÔNG áp dụng cho ví điện tử"

**Đây chính là điểm PO yêu cầu tôi soi kỹ (mục 3 trong 4 chỗ được chỉ định) — và đúng là có vượt quá
bằng chứng, nhưng đi NGƯỢC hướng tôi lo ban đầu.**

Câu gốc: *"Đ.38.2 (miễn 5 năm cho DN nhỏ, **trừ** bên trực tiếp xử lý dữ liệu nhạy cảm — tức
**KHÔNG áp dụng** cho ví điện tử)."*

Đối chiếu với chính báo cáo PO đã gửi qua Lead trước đó (30/08, tôi ghi lại nguyên văn vào
`docs/security/2026-08-30-C4-dpia-dieu25-khung-draft.md §0/§3`):
> *"Đ.38.2 — miễn trừ 5 năm... CÓ THẬT nhưng KHÔNG áp dụng chắc chắn cho FIN-05 — mệnh đề loại trừ:
> không áp dụng nếu 'trực tiếp xử lý dữ liệu nhạy cảm HOẶC xử lý dữ liệu của số lượng lớn chủ thể'.
> FIN-05 xử lý khiếu nại tài chính — **CÓ THỂ** thuộc diện loại trừ (**tuỳ Đ.2.3 xác nhận 'nhạy cảm'
> hay không**) — KHÔNG dùng miễn trừ Đ.38.2 như một lối thoát CHẮC CHẮN."*

**Đ.2.3 giao việc định nghĩa "dữ liệu nhạy cảm" cho một DANH MỤC DO CHÍNH PHỦ BAN HÀNH (nghị định
riêng) — và chính deck (Slide 11) cũng tự nói NĐ 356/2025 mới đọc phần luật (91/2025/QH15, 23
trang), CHƯA nói đã đọc toàn văn nghị định 356/2025 (42 điều, nơi danh mục nhạy cảm thực sự nằm).**
⟹ Câu "KHÔNG áp dụng cho ví điện tử" là kết luận đã CHỐT một câu hỏi mà chính hồ sơ nội bộ (viết
CÙNG NGÀY, dựa CÙNG một lần đọc luật của PO) ghi rõ là CHƯA XÁC NHẬN ĐƯỢC.

⚠️ Lưu ý hướng rủi ro: đây KHÔNG phải hướng "claim miễn trừ để né nghĩa vụ" (hướng nguy hiểm hơn) —
đây là hướng "tự nhận mình thuộc diện nặng hơn luật đòi hỏi", vốn an toàn hơn về mặt tuân thủ. Nhưng
vẫn là một khẳng định KHÔNG CÓ CĂN CỨ ĐỦ MẠNH, và một chuyên gia thẩm định có thể hỏi ngược: *"Sao
biết chắc là 'dữ liệu nhạy cảm' — danh mục ở đâu?"* — câu hỏi hiện KHÔNG trả lời được, làm lộ ra
đúng chỗ hồ sơ chưa xong, phản tác dụng nếu bị hỏi dồn.

**Đề xuất sửa:**
> *"Đ.38.2 (miễn 5 năm cho DN nhỏ) có mệnh đề loại trừ cho bên xử lý dữ liệu nhạy cảm — dữ liệu tài
> chính CÓ KHẢ NĂNG thuộc diện đó, đang chờ xác nhận qua danh mục của Nghị định 356/2025 (42 điều,
> chưa đọc hết). Chúng tôi chủ động không dựa vào miễn trừ này cho tới khi xác nhận xong."*

### 3. ⚠️→🔴 Dòng 213 (Phần 3, bảng nguồn) — URL PDF "chạy lại được" nhưng số trang không khớp

Bảng nguồn tự khai *"Mỗi dòng đều chạy lại được"* (dòng 201) và cho URL cụ thể:
`datafiles.chinhphu.vn/cpp/files/vbpq/2025/7/91qh.signed.pdf`.

**[ĐO 31/08, tôi tự fetch]:** URL này **CÓ THẬT, tải được** (không phải link chết/bịa) — điểm cộng
thật. Nhưng: đây là **PDF ẢNH QUÉT** (CCITT Fax, khớp đúng lời Lead thuật lại "PO đọc bằng ảnh từng
trang" — không mâu thuẫn với "ký số", VPCP hay scan bản gốc đã ký rồi đóng dấu số xác thực), và công
cụ đọc của tôi báo **cấu trúc chỉ 3 "trang đối tượng" PDF**, không phải 23 trang như deck ghi ở dòng
234 (*"bản PDF ký số Văn phòng Chính phủ, 23 trang"*).

**Tôi KHÔNG kết luận số 23 trang sai** — đếm object PDF từ một tool tự động cho file ảnh quét có thể
không phản ánh đúng số trang thật (một trang scan có thể tách nhiều object, hoặc đây có thể là MỘT
phần của một bộ file nhiều mảnh trên cùng thư mục, không phải toàn văn). Đây là điều CẦN NGƯỜI THẬT
xác nhận bằng cách mở chính file này lên bằng trình đọc PDF thường, đếm trang tay — **rẻ, 1 phút**,
trước khi đứng trước ZaloPay/VNPT dùng con số "23 trang" mà không tự tay đếm lại lần cuối.

## ⚠️ CẦN KHAI PHẠM VI — không sai nhưng thiếu vế giới hạn

### 4. Dòng 131 — "Postgres (Mã hóa data)"

Không sai nhưng dễ đọc thành "toàn bộ DB được Postgres mã hoá ở tầng hạ tầng". Thực tế: mã hoá là
**tầng ứng dụng, theo TRƯỜNG cụ thể** (`EncryptedText` cho `messages.content`,
`complaints.description_raw`, `bank_accounts.account_no` — theo ADR-025/045), không phải mã hoá toàn
ổ đĩa/toàn Postgres. Nếu bị hỏi "encryption at rest kiểu gì — TDE hay field-level?", câu trả lời
đúng là **field-level**, khác với gợi ý của slide. Đề xuất đổi nhãn thành "Mã hoá trường dữ liệu nhạy
cảm" nếu còn kịp.

### 5. Dòng 242-243 (Slide 11) — "Cả ba đang trong kế hoạch có mốc thời gian"

Ba việc nêu: route tự phục vụ xuất/xoá dữ liệu · hồ sơ đánh giá tác động · quy trình thông báo vi
phạm. Đối chiếu tình trạng thật (tôi là người giữ hồ sơ cả ba):
- **Hồ sơ đánh giá tác động (DPIA):** CÓ mốc — 14/10/2026, nhưng đây là **mốc lập kế hoạch NỘI BỘ**
  (`docs/security/2026-08-30-C4-dpia-dieu25-khung-draft.md §0d`), không phải cam kết đã công bố.
- **Route tự phục vụ xuất/xoá + quy trình thông báo vi phạm (IR runbook):** hiện chỉ ở dạng
  **backlog có ưu tiên**, KHÔNG có ngày cụ thể nào được PO chốt — C3 (runbook) vẫn là DRAFT, route
  code thì "KHÔNG vào backlog đợt đo benchmark hiện tại" (đóng băng tính năng).

⟹ Nói "cả ba đang trong kế hoạch có mốc thời gian" hơi vượt quá — chỉ MỘT trong ba có mốc (và là
mốc nội bộ, không phải cam kết ngoài). Đề xuất sửa: *"Cả ba đã vào backlog có ưu tiên; hồ sơ đánh
giá tác động có mốc nội bộ 14/10/2026, hai việc còn lại đang chờ xếp lịch."* — trung thực hơn, vẫn
đủ mạnh để thể hiện đội KHÔNG lờ đi vấn đề.

## ✅ CHỨNG MINH ĐƯỢC — đối chiếu đúng, không cần sửa

- Dòng 34-36 (căn cứ Luật 91/2025 thay NĐ 13/2023): khớp đúng `docs/security/2026-08-30-niem-luat-91-2025-thay-nd-13-2023.md`, đã xác minh qua WebSearch + (theo báo cáo) PO đọc toàn văn.
- Dòng 26-28 (HITL/maker-checker/Origin-rule): khớp `review-2026-08-27-benchmark-eu-us.md` mục "Đã kiểm và đạt".
- Dòng 60-101 (hai gate đỏ-xanh): **tự tôi đo**, khớp `docs/security/2026-08-31-cong-do-truoc-xanh-sau-bdaf17e-5ff93b8.md` — câu chữ trong deck bám sát đúng phạm vi bằng chứng, không thấy chỗ vượt quá. Dòng 84-87 (giới hạn "chưa phải cổng thường trực") giữ đúng, không bị cắt bớt so với báo cáo gốc — đúng tinh thần "câu trung thực làm tăng uy tín" mà chính deck đề cao ở nơi khác.
- Dòng 97-100, 216-224 (cấm "đạt SCA/PSD2/AAL2", cấm ghép benchmark với bảo mật): khớp đúng lệnh PO đã ra, giữ nguyên trong toàn bộ hai gate — không thấy chỗ nào lách.
- Dòng 236-237 (Đ.4.1.d, Đ.21.1, Đ.23.1): khớp đúng nội dung Lead đã báo qua tôi (`C4 §0/§2b`), không thấy sai lệch khi đối chiếu.

## Việc CHƯA kiểm được trong khung giờ ưu tiên này

- Không kiểm lại số liệu ở PHẦN 3 dòng 205-212 (526 test, 23 bất biến, 246 ca, tái lập 3/3, 4,8% méo
  tiếng Việt) — đây là số liệu benchmark/test, ngoài chuyên môn trực tiếp `security`, và deck tự
  ghi "đo lại 30/08" kèm lệnh chạy cụ thể — nếu Lead muốn tôi đối chiếu thêm, báo riêng.
- Không xác nhận lại "23 trang" bằng cách khác (cần người có trình đọc PDF ảnh quét đàng hoàng,
  ngoài khả năng công cụ WebFetch của tôi).
