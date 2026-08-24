# Soát ADR-049 (đề xuất, chưa duyệt) — đổi đòn bẩy nhận diện "khách yêu cầu tạo vé" sang tất định

> ADR-049 hiện mới ở mức **chẩn đoán + đề xuất chiến lược** (`docs/DECISIONS.md:2904-2953`), CHƯA
> có thiết kế cụ thể (Lead đang viết nháp). Hồ sơ này soát Ở MỨC CHIẾN LƯỢC — nói rõ chỗ nào SUY TỪ
> MÔ TẢ (chưa có mã để đo) và chỗ nào ĐO ĐƯỢC từ hạ tầng hiện có (`phan_luong.py`, đã đọc toàn văn).
> Sẽ soát lại ở mức THIẾT KẾ CỤ THỂ khi Lead chuyển nháp.

## ① Đòn bẩy tất định có đổi con số ~300 vé/phiên (`8b83518`) không — CÓ, nhưng KHÔNG theo cách "phá trần"

**[ĐO] đọc toàn văn `src/agents/phan_luong.py`** — hạ tầng ADR-049 tự nhận là "đúng cơ chế cổng
`thu_slot` (1B)": lớp này **CHỈ TRẢ VỀ MỘT TUYẾN ĐỊNH TUYẾN** (`(route, reason)`), tự khai ranh giới
cứng ngay đầu file: *"Lớp này KHÔNG quyết định nghiệp vụ... Đường nhẹ KHÔNG tạo bản ghi nghiệp vụ
nào. Bất biến đo được: đường nhẹ ⟹ Δcomplaints = Δtickets = 0."* Nó KHÔNG tự gọi `create_ticket` —
nó chỉ đổi ngữ cảnh/hướng dẫn cho LƯỢT MODEL kế tiếp.

**Suy ra (chưa có thiết kế ADR-049 để đo trực tiếp, đây là suy luận từ đúng khuôn tiền lệ):** nếu
ADR-049 đi đúng khuôn `phan_luong.py` hiện có — tức là một bộ NHẬN DIỆN tất định (regex/danh sách
cho phép, không LLM) đổi ĐƯỜNG ĐI của lượt (ép prompt/context mạnh hơn cho lượt đó), **LLM vẫn là
bên thực sự gọi `create_ticket`** — thì toàn bộ hàng rào tôi liệt kê ở `8b83518` (OTP-freshness,
`20/minute` theo IP, concurrency limiter, anti-livelock) **KHÔNG đổi**, vì các hàng rào đó nằm ở
tầng SAU quyết định gọi tool, không phải tầng phân loại ý định. **Trần LÝ THUYẾT ~300 vé/cửa sổ
OTP-fresh không đổi.**

**Nhưng đây đúng là điểm PO-agent thấy đúng — KHÔNG phải trần đổi, mà là TỈ LỆ ĐẠT TRẦN đổi:**
`8b83518` tính trần LÝ THUYẾT giả định "mỗi tin nhắn đều thuyết phục được model" — một giả định
CHƯA ĐO, vì hôm nay việc "thuyết phục model" là xác suất (đúng lý do ADR-049 tồn tại: sáu luật
MẠNH đang thắng một tín hiệu YẾU, tức pha thuyết phục KHÔNG ổn định). Một bộ nhận diện tất định,
theo đúng mục đích nó được đề xuất để làm (thắng được sáu luật cạnh tranh), sẽ đẩy **tỉ lệ thực
đạt được trần đó tiến gần 100%** — đúng câu PO-agent hỏi: kẻ lạm dụng không cần "thuyết phục" nữa,
chỉ cần lặp đúng một khuôn câu đã học được (và khuôn đó, theo đúng nguyên tắc `phan_luong.py` đang
dùng, là **danh sách CHO PHÉP đóng** — về LÝ THUYẾT liệt kê được hết, khác hẳn không gian câu tự
nhiên vô hạn mà một LLM phải "bị thuyết phục").

**Kết luận ①:** trần lý thuyết không đổi, nhưng đây không phải điều PO thật cần nghe — điều cần
nghe là: **hôm nay ~300 là số trần chưa ai đo được có đạt tới hay không (phụ thuộc hành vi model,
không kiểm soát được); sau ADR-049, ~300 trở thành số MỤC TIÊU MỘT KẺ TẤN CÔNG CÓ THỂ NHẮM TỚI VÀ
GẦN NHƯ CHẮC CHẮN ĐẠT ĐƯỢC, vì cơ chế kích hoạt không còn phụ thuộc hành vi model.** Đây đúng
nguyên tắc chung: *cơ chế tất định luôn đáng tin hơn cho bên PHÒNG THỦ (LLM03 hay nói), nhưng khi
cơ chế đó lộ RA NGOÀI thành một điều kiện đoán trước được (khách gõ đúng cụm là kích), nó cũng
đáng tin y hệt cho bên TẤN CÔNG.**

## ② Đồng ý với khung PO-agent đặt: trần vé là ĐIỀU KIỆN TIÊN QUYẾT của ADR-049, không phải khuyến nghị song song

**Lý do ghép hai quyết định, nói thẳng không vòng:** ADR-049 mô tả đúng đây là đánh đổi *"được lợi
tính đoán trước được; mất đi khả năng model xử ca lạ mà luật không lường"* — nhưng bản ADR hiện tại
CHỈ cân nhắc mất-được ở phía TRẢI NGHIỆM KHÁCH THẬT (bỏ sót vs bắt oan, đúng nguyên tắc 1B kế thừa).
Nó **chưa cân nhắc** mất-được ở phía KHAI THÁC: "tính đoán trước được" là lợi ích cho vận hành ĐÚNG
LÚC NÀY (thắng sáu luật cạnh tranh), nhưng đúng nó cũng là chi phí AN NINH (thắng luôn khả năng "khó
đoán = khó tự động hoá tấn công" mà một model, dù không hoàn hảo, vẫn vô tình cung cấp).

**Đề nghị nguyên văn để chuyển PO thật:** *"ADR-049 và quyết định trần số vé/phiên (`8b83518`) là
MỘT quyết định, không phải hai. Duyệt ADR-049 mà chưa có trần vé là mở một cơ chế kích hoạt đáng tin
cậy hơn cho một lỗ đã biết còn hở. Không đề nghị hoãn ADR-049 — đề nghị PO thật đọc CẢ HAI hồ sơ
cùng lúc, và nếu duyệt ADR-049 trước khi có trần vé, ghi rõ đó là chấp nhận rủi ro CÓ THỜI HẠN (khuôn
ADR-040), không phải một khoảng trống bị quên."*

## ③ Ràng buộc cứng 2 (AI không vượt cấp) — không thấy vi phạm Ở MỨC MÔ TẢ HIỆN TẠI, nhưng có MỘT câu hỏi thiết kế cần Lead trả lời tường minh, chưa tự suy đoán được

Ràng buộc cứng 2 nói về **vượt CẤP/VAI** (customer→cskh/supervisor qua tầng service), không phải về
"ai bấm nút gọi tool". `create_ticket` không đổi vai, không đổi thẩm quyền — mở vé vẫn ≠ quyết định
(HITL nguyên vẹn, ADR-047/049 đều tự khai giữ nguyên). **Không thấy đường nào ADR-049 tạo ra escalation
role trá hình.**

**Nhưng có một câu hỏi kiến trúc CHƯA trả lời được vì thiết kế cụ thể chưa tồn tại — đúng chỗ cần
nói rõ "đây là suy luận, không phải đo":** ADR-049 có định (a) chỉ đổi NGỮ CẢNH/HƯỚNG DẪN cho lượt
model kế tiếp — LLM vẫn tự quyết định gọi `create_ticket` (đúng khuôn `phan_luong.py` hiện có), hay
(b) khi khớp mẫu tất định thì HỆ THỐNG tự gọi thẳng `create_ticket` từ code, bỏ qua bước LLM ra
quyết định tool-call? Bản ADR hiện tại không nói rõ — và hai lựa chọn này khác nhau NHIỀU hơn một
chi tiết cài đặt:

- Nếu **(a)**: mọi phân tích ở ①②, và cả finding sạch về `description_raw` (`8b83518` mục c — không
  có đường injection vì LLM vẫn là bên soạn nội dung/gọi tool) **giữ nguyên hiệu lực**.
- Nếu **(b)**: cần soát LẠI TỪ ĐẦU câu hỏi `description_raw` — nếu nội dung vé được điền THẲNG từ
  văn bản khách gõ (không qua LLM tóm tắt/phân loại), CSKH đọc nguyên văn một chuỗi khách tự chọn,
  không có lớp phán đoán nào chặn giữa — rủi ro khác hẳn, cần đánh giá riêng khi biết chọn (b).

**Khuyến nghị: hỏi Lead xác nhận tường minh (a) hay (b) ngay trong bản thiết kế**, đừng để đây là
một chi tiết cài đặt tự nhiên trôi theo — đúng loại câu hỏi mà nếu không hỏi trước sẽ thành phát
hiện muộn sau khi code đã landed (đúng hình dạng nhiều bài học đội đã trả giá trong ngày).

## Tổng kết ngắn cho PO-agent chuyển tiếp

- ① Trần lý thuyết ~300 không đổi; tỉ lệ THỰC ĐẠT trần đó tăng mạnh — đồng ý với trực giác của bạn,
  đã giải thích cơ chế cụ thể (kích hoạt tất định = danh sách cho phép đóng = học thuộc/tự động hoá
  được, khác không gian câu tự nhiên phải "thuyết phục" model).
- ② Đồng ý ghép ADR-049 với quyết định trần vé thành MỘT gói trình PO thật, câu đề nghị nguyên văn
  ở trên sẵn để dùng.
- ③ Không thấy vi phạm ràng buộc cứng 2 ở mức mô tả hiện tại — nhưng cần Lead xác nhận tường minh
  kiến trúc (a)/(b), vì (b) sẽ mở lại câu hỏi `description_raw` đã đóng hôm nay.

Sẽ soát lại đầy đủ khi có nháp thiết kế cụ thể từ Lead, theo đúng lời hẹn.
