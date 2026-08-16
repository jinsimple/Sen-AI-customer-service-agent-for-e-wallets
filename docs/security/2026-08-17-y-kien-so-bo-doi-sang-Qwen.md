# Ý kiến SƠ BỘ — cân nhắc đổi sang API Qwen (Alibaba Cloud)

> Vai: **security/tuân thủ** · 2026-08-17 · PO hỏi ý kiến sơ bộ, **chưa quyết**.
> Đánh dấu theo nếp N3: **[KIẾN TRÚC]** · **[PHẢI KIỂM]** · **[PHÁN ĐOÁN]**.
> ⚠️ Đây **không** phải tư vấn pháp lý. Nó chỉ khoanh vùng câu hỏi để người có
> thẩm quyền pháp lý trả lời.

## 0. Khung câu hỏi đang bị đặt sai — sửa trước khi bàn tiếp

Câu đang được hỏi nghe như *"có nên bắt đầu gửi dữ liệu ra nước ngoài không?"*

**Nhưng ta ĐÃ gửi rồi.** Hệ thống hiện gọi `gpt-4o-mini` (OpenAI, Hoa Kỳ), và
[KIẾN TRÚC] **tin khách gõ đi nguyên văn** lên đó — agent buộc phải đọc được
khách viết gì.

⟹ **Nghĩa vụ theo NĐ 13/2023 Điều 25 (chuyển dữ liệu cá nhân ra nước ngoài)
KHÔNG do Qwen tạo ra. Nó đã tồn tại từ trước.**

🔴 **Câu hỏi thật sự cần trả lời TRƯỚC câu Qwen:** *hồ sơ đánh giá tác động
chuyển dữ liệu ra nước ngoài đã có chưa?* Nếu **chưa**, đó là **khoảng trống
đang tồn tại**, không phải rủi ro mới — và nó không tự biến mất nếu quyết định
là "giữ OpenAI".

## 1. [KIẾN TRÚC] Cái gì thực sự rời biên giới hôm nay — đã kiểm mã

| Loại | Có rời không | Cơ chế |
|---|---|---|
| **tin khách gõ** (mô tả khiếu nại, tin chat) | 🔴 **RỜI, nguyên văn** | không lớp scrub nào — agent cần đọc hiểu |
| **họ tên · SĐT trong kết quả tool** | ✅ đã che | `_scrub_pii_cho_llm` (ADR-010), che theo **tên khoá** |
| **số tiền · mã GD · thời gian · trạng thái** | rời, **có chủ đích** | agent cần để suy luận + trích dẫn (ràng buộc 3) |

Docstring `_scrub_pii_cho_llm` nói thẳng: *"kết quả agent thì RỜI HỆ THỐNG lên
OpenAI"* — đội **đã ý thức** điều này và đã che phần che được.

⚠️ **Phần không che được mới là phần nặng:** tin khách gõ. Theo chính khảo sát
bốn cửa của tôi, nó chứa **PII của bên thứ ba** ngay ở ca dùng điển hình nhất —
*"em chuyển nhầm cho anh X, sđt 09…"* — tức dữ liệu của **người chưa từng vào
quan hệ với ví**, đang rời biên giới.

## 2. [PHÁN ĐOÁN] Bốn khác biệt giữa hai lựa chọn — cái nào THỰC SỰ đổi rủi ro

**Không** đổi: nghĩa vụ Điều 25 áp cho **mọi** chuyển ra nước ngoài, bất kể đi
đâu. Đổi OpenAI→Qwen **không** làm nghĩa vụ đó nặng hay nhẹ hơn.

**Có** đổi, bốn thứ:

| # | Yếu tố | Ghi chú |
|---|---|---|
| 1 | **Vùng phục vụ** | Alibaba phục vụ Qwen từ **nhiều vùng**. "Dùng Qwen" **chưa phải một quyết định** cho tới khi ghim **endpoint/vùng cụ thể** — hai vùng khác nhau là hai hồ sơ pháp lý khác nhau. **[PHẢI KIỂM]** |
| 2 | **Điều khoản train-on-data** | Phải **đọc điều khoản doanh nghiệp của đúng sản phẩm + đúng vùng**. **[PHẢI KIỂM] — tôi KHÔNG khẳng định từ trí nhớ.** Câu cần trả lời: dữ liệu API có được dùng huấn luyện không · có tuỳ chọn tắt không · cam kết đó nằm trong **hợp đồng** hay chỉ trong **trang tài liệu** |
| 3 | **Chế độ pháp lý của nơi nhận** | Khác biệt **thực chất** về khả năng cơ quan nhà nước sở tại yêu cầu truy cập. Đây là yếu tố **phải đánh giá**, không phải yếu tố tôi phán quyết — nó thuộc hồ sơ Điều 25 và cần người có thẩm quyền pháp lý |
| 4 | **Đối tác thiết kế** | ZaloPay là đối tác phản hồi. Câu *"văn bản khiếu nại của khách ví đi tới nhà cung cấp đám mây nào"* là câu bộ phận tuân thủ của một ví điện tử **gần như chắc chắn sẽ hỏi**. Rủi ro **quan hệ đối tác**, không phải rủi ro kỹ thuật — nhưng có thật |

## 3. 🔴 [PHÁN ĐOÁN] Đòn bẩy thật không nằm ở "chọn nhà cung cấp nào"

Hai cách giảm phơi nhiễm, và **một trong hai không dùng được**:

**❌ Scrub tin khách trước khi gửi LLM — KHÔNG DÙNG ĐƯỢC.**
Sẽ có người đề xuất cái này, nên nói trước: **S-01 đã đo** — `scrub_pii` **chặn
nhầm 40%** trên văn bản nghiệp vụ tiếng Việt, và ở đây **LLM cần chính cái
nghĩa** mà scrub phá. Scrub tin khách = agent đọc một khiếu nại đã bị sửa nghĩa.
**Đổi một rủi ro tuân thủ lấy một sản phẩm hỏng.**

**✅ Tự host mô hình — xoá hẳn câu hỏi, và đó là NGUYÊN TẮC ĐỘI VỪA TỰ ĐẶT.**
Brief đợt nâng cấp OSS, nguyên tắc ① không nhân nhượng:

> *"mọi công cụ phải TỰ HOST — không dữ liệu nào rời hạ tầng (bài F-30/LangSmith)"*

**Qwen có trọng số mở.** ⟹ tồn tại một lựa chọn **nhất quán với nguyên tắc đội
vừa ký**: **tự host Qwen** thay vì gọi API Alibaba. Khi đó **không có chuyển dữ
liệu ra nước ngoài nào** — Điều 25 không áp, khoản 4 (đối tác) biến mất, khoản
2 (train-on-data) biến mất.

⚠️ Tôi **không** kết luận tự-host là khả thi ở đây — nó đổi bài toán sang phần
cứng/độ trễ/chất lượng, và **đó không phải vùng tôi đo được**. Nhưng nếu
**gọi API Alibaba** được chọn, cần nói rõ rằng đó là **một ngoại lệ có ý thức
đối với nguyên tắc ①** — chứ không phải một quyết định nằm ngoài nguyên tắc đó.

**Đây là điểm tôi muốn nhấn nhất:** đội vừa dựng cả một đợt nâng cấp quanh
*"không dữ liệu nào rời hạ tầng"*, trong khi **thứ rời hạ tầng nhiều nhất — toàn
bộ hội thoại khách — thì không nằm trong phạm vi đợt đó**. Cả LiteLLM lẫn
Langfuse đều được soi kỹ vì chúng *có thể* giữ nội dung; còn nhà cung cấp LLM
thì **chắc chắn** nhận toàn bộ nội dung, mỗi lượt, và điều đó đang được coi là
mặc định.

## 4. Đề nghị thứ tự — không phải "chọn nhà cung cấp"

1. **Xác định hồ sơ Điều 25 đã có chưa.** Áp cho hiện trạng, **không chờ** quyết
   định Qwen. Nếu chưa có, đây là việc gấp hơn việc đổi nhà cung cấp.
2. **Nếu cân nhắc Qwen: ghim VÙNG trước**, rồi mới đọc điều khoản của **đúng
   vùng + đúng sản phẩm** đó. "Dùng Qwen" chưa đủ cụ thể để thẩm định.
3. **Đặt tự-host lên bàn như một lựa chọn ngang hàng**, vì nó là lựa chọn duy
   nhất **xoá** câu hỏi thay vì **chuyển** nó sang một pháp lý khác — và nó nhất
   quán với nguyên tắc ① đội vừa ký.
4. **Bất kể chọn gì**: ghi vào hồ sơ **cái gì rời hạ tầng** (bảng §1). Một hồ sơ
   Điều 25 không liệt kê được **trường dữ liệu nào thực sự đi** thì không dùng
   được.

## 5. Điều tôi KHÔNG kết luận

- **Không** phán quyết nhà cung cấp nào an toàn hơn — điều đó cần đọc điều
  khoản thật của đúng vùng, và cần người có thẩm quyền pháp lý.
- **Không** biết hồ sơ Điều 25 hiện có hay không — **cần hỏi PO thật**, và đó
  là câu quan trọng nhất trong tài liệu này.
- **Không** đánh giá được chất lượng/độ trễ/chi phí của Qwen so với hiện tại —
  ngoài vùng của tôi, và nó có thể là yếu tố quyết định thật sự.
