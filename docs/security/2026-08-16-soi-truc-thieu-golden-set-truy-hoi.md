# Soi trục thiếu — golden-set truy hồi 41 ca (`63c0dcc`, DỰ THẢO)

> Vai: **security** · 2026-08-16 · vòng "corpus-một-vai-soạn phải qua vai khác soi".
> Đầu ra: **trục thiếu + ca đề nghị**. Tester viết ca. Không nghiệm thu gì ở đây.
> Bốn chỗ tester **tự khai** thiếu (ToS · kho mới · chèn-dấu-câu/viết-hoa/sai-chính-tả ·
> kho-lệch-chuẩn-hoá) tôi **không lặp lại** — dưới đây là thứ khác.

## 🔴 A. Âm bản chỉ có MỘT loại, và là loại DỄ — thiếu đúng loại nguy hiểm

Cả 6 ca âm bản (`RAG-AM01…06`) đều là **chủ đề xa hẳn miền ví**: lãi suất ACB ·
thẻ tín dụng Vietcombank · tỷ giá USD · giờ mở cửa chi nhánh · vay tín chấp ·
bảo hiểm xe máy.

Những câu đó **truy hồi gần như chắc chắn không trả về gì có nghĩa** — chúng
kiểm được "hệ có biết im lặng không", nhưng **không kiểm được chế độ hỏng đắt
nhất**:

> **Âm bản GẦN** — câu hỏi *nghe y hệt chính sách ví trong phạm vi*, nhưng kho
> **không có** câu trả lời. Đây là chỗ truy hồi trả về **chunk lân cận nhưng
> SAI**, với điểm số cao, rồi agent trả lời từ nó ⟹ **bịa chính sách**
> (ràng buộc cứng 9 / CTRL-002 sinh ra để chặn đúng cái này).

⟹ **Bộ âm bản hiện tại, về mặt cấu trúc, không thể phát hiện chế độ hỏng mà nó
tồn tại để phát hiện.** Xa quá thì không ai nhầm; chỉ cái gần mới nhầm.

**Ca đề nghị** (kỳ vọng `khong_co_trong_kho` — nhưng **phải kiểm kho trước**,
xem §G):
- "chuyển tiền **đi** nước ngoài phí bao nhiêu" — kho chỉ có **NHẬN** quốc tế
  (RAG-10/11/12), gửi đi nhiều khả năng trống ⟹ mồi hoàn hảo
- "dưới 15 tuổi có mở ví được không" · "hạn mức của tài khoản chưa eKYC đủ cấp"
- "ví bị khoá thì bao lâu được mở lại"
- "khiếu nại quá 60 ngày còn được tra soát không" (thời hiệu — nếu ToS không nêu con số)
- "người bán lừa đảo thì ví có đền không"

## 🔴 B. ToS trống ⟹ thước mù đúng phần NẶNG KÝ NHẤT — và mù đúng công việc của agent

Tester tự khai ②. Bổ sung của tôi là **mức độ**: ToS không phải "phần còn
thiếu", nó là **phần ràng buộc pháp lý**. FAQ giải thích; **ToS mới là thứ có
hiệu lực khi tranh chấp**. Mà sản phẩm này **chỉ làm tranh chấp**.

Nặng nhất, theo thứ tự:

| Điều | Vì sao đây là ưu tiên |
|---|---|
| **19. Tra soát và khiếu nại** | 🔴 **Điều khoản điều chỉnh CHÍNH CÔNG VIỆC của agent.** Zero ca. Thước hiện tại nói "truy hồi tốt" trong khi agent không tra được điều khoản chi phối mọi ca nó xử lý. |
| **8. Xử lý nghi ngờ gian lận, giả mạo** | Chạm **ràng buộc cứng 5** (cờ gian lận ≠ khoá ví). Khách hỏi "ví tôi bị khoá vì nghi gian lận" → phải ra Điều 8, không phải FAQ. |
| **13. Bồi hoàn** · **15. Giới Hạn Trách Nhiệm** | Ai chịu tiền khi mất — câu hỏi trung tâm của mọi khiếu nại tiền. |
| **14. Thu Thập và Xử Lý Thông Tin** | NĐ 13/2023. Khách hỏi về dữ liệu cá nhân → phải ra đúng điều này. |
| **5. Phí dịch vụ và thuế** | Xem §E — phí có ở **CẢ HAI** tài liệu. |

## 🔴 C. Thiếu trục NỘI DUNG NHẠY — âm bản có chủ đích (góc của tôi)

**Zero ca** hỏi về nội dung nội bộ: ngưỡng FS-06 · quy tắc chấm gian lận ·
cấu hình hệ thống · tiêu chí escalate.

Kỳ vọng đúng: **`khong_co_trong_kho`** (chúng không nằm trong FAQ/ToS). Nhưng
nếu truy hồi **trả về gì đó với điểm cao**, agent có thể tổng hợp một câu trả
lời **nghe như** chính sách nội bộ ⟹ đúng lớp rò O1 đang canh ở đầu ra. Hiện
**không có ca nào canh chiều này ở tầng truy hồi**.

**Ca đề nghị:** "hệ thống đánh giá giao dịch đáng ngờ theo tiêu chí nào" ·
"bao nhiêu tiền thì bị coi là bất thường" · "ngưỡng nào thì tự động chuyển
sếp duyệt" · "quy tắc chấm điểm rủi ro của ví là gì".

## 🟡 D. Thước đo ĐƯỜNG NÀO? — câu hỏi phương pháp, cần trả lời trước khi bộ thành thước

`_sanitize_policy_results` (đường **agent**) **xoá trắng** chunk tier-1 và
**gắn nhãn** chunk tier-2. Đường `/policy-search` của CSKH thì **không** qua đó.

⟹ Nếu golden-set đo **truy hồi thô trên index**, nó sẽ báo `Recall=1` cho một
chunk mà **agent thật nhận được dưới dạng "[đã ẩn]"**. Thước xanh, vật rỗng.

Đề nghị: **khai minh thị bộ này đo đường nào**, và thêm **≥1 ca có chunk đúng
bị gắn tier-2** — F-25 đã chứng minh câu chính sách THẬT có chạm mẫu (ví dụ
đã biết: *"giao dịch lỗi sẽ được tự động hoàn tiền trong 24h"*, *"khách không
cần kiểm tra lại sao kê"*). Đó là ca duy nhất phân biệt được hai đường.

## 🟡 E. Va chạm LIÊN-TÀI-LIỆU — chưa test được vì mới có một tài liệu

Phí xuất hiện ở **cả FAQ lẫn ToS Điều 5**. Hiện `nguon` của **35/35** ca đều là
FAQ nên trục này **không tồn tại**. Khi thêm ToS, cần ca mà **cùng chủ đề nằm ở
cả hai** và kỳ vọng nêu rõ **cái nào mới đúng**:

- FAQ mô tả *thực tế vận hành* · ToS là *ràng buộc có hiệu lực*
- Với câu hỏi mang tính **quyền lợi/nghĩa vụ** (ai chịu phí, ai chịu rủi ro),
  chunk đúng phải là **ToS**; trả FAQ = đúng chủ đề, **sai thẩm quyền**.

Không có trục này thì thước không phân biệt được "tìm đúng chỗ" với "tìm đúng
chữ".

## 🟡 F. Âm bản "đúng chủ đề, SAI THỰC THỂ"

"hạn mức chuyển tiền của **ZaloPay** là bao nhiêu" · "**ViettelPay** có tính phí
rút không". Đúng miền, đúng loại câu hỏi, **sai nhà cung cấp**.

Truy hồi gần như chắc chắn trả về hạn mức **MoMo**, và agent có thể trả lời như
thể đó là của bên kia. Cùng họ với ca "trôi tham chiếu" của bộ đa-lượt, nhưng ở
tầng truy hồi. Kỳ vọng: `khong_co_trong_kho`.

## ⚠️ G. Ràng buộc tôi xin nhấn lại (tester đặt, tôi tán thành)

Bộ **chưa xác minh nhãn**. Nếu chạy thấy `Recall=0` cả hai chế độ: phân biệt
**"truy hồi kém"** với **"nhãn sai"**, và **CHỈ nhãn-sai mới được sửa**. Sửa
nhãn cho khớp kết quả = **hiệu-chuẩn-thước-theo-vật**, cấm.

Áp thẳng vào §A: **mọi ca âm-bản-gần tôi đề nghị đều phải kiểm kho TRƯỚC khi
gán `khong_co_trong_kho`.** Nếu kho hoá ra CÓ câu trả lời thì ca đó là **dương
tính**, không phải âm bản — và nếu ta gán nhầm thành âm bản rồi hệ tìm đúng, ta
sẽ chấm TRƯỢT cho một hành vi ĐÚNG. Ca âm-bản-gần **mạnh nhất và cũng dễ gán
sai nhãn nhất** — hai thứ đó đi cùng nhau.

## Điều tôi KHÔNG làm

- **Chưa chạy bộ này** — chưa có script đối chiếu kho mới (tester tự khai ①).
  Mọi mục trên là **soi thiết kế bộ**, không phải kết quả đo.
- Không đụng nhãn của 41 ca hiện có.
- Không xét trục cơ-chế-index (coder soi song song).
