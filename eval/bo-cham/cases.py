# -*- coding: utf-8 -*-
# Nguồn: goi_30_nhan_NGUOI.md — giữ NGUYÊN VĂN, không sửa một chữ nào.
# ca_cu = số ca trong file gốc (dùng cho khoá đối chiếu, KHÔNG hiện trong gói chấm)

CASES = [
 dict(ca_cu=1, sid="RAG-38", khach="Tôi gửi yêu cầu tra soát bằng cách nào?", agent="""Để gửi yêu cầu tra soát, bạn có thể làm theo các bước sau:

1. **Liên hệ với bộ phận CSKH**: Bạn có thể gọi điện hoặc gửi tin nhắn đến bộ phận chăm sóc khách hàng của ví điện tử mà bạn đang sử dụng.

2. **Cung cấp thông tin cần thiết**: Khi liên hệ, hãy cung cấp các thông tin sau để giúp quá trình tra soát diễn ra nhanh chóng:
   - Mã giao dịch (nếu có).
   - Thời gian thực hiện giao dịch.
   - Số tiền giao dịch.
   - Nội dung cụ thể của yêu cầu tra soát (ví dụ: lý do bạn muốn tra soát).

3. **Chờ phản hồi**: Sau khi gửi yêu cầu, bạn sẽ nhận được phản hồi từ bộ phận CSKH trong thời gian quy định.

Nếu bạn cần hỗ trợ thêm hoặc có câu hỏi cụ thể nào khác, hãy cho mình biết nhé!"""),

 dict(ca_cu=2, sid="UXQA-001", khach=None, agent="""Mình đã tìm thấy giao dịch liên quan đến số tiền 59.000đ mà bạn đề cập. Cụ thể, giao dịch này diễn ra vào ngày 21/07/2026 lúc 19:42 và có mã giao dịch là **TXN20260721000071**. Đây là giao dịch trừ tiền từ ví nội bộ của bạn.

Để tiếp tục hỗ trợ bạn, mình cần xác nhận một số thông tin. Bạn có chắc chắn rằng giao dịch này là không đúng và bạn muốn khiếu nại về nó không?"""),

 dict(ca_cu=3, sid="RAG-47", khach="Tôi chuyển tiền cho bạn tôi, bị trừ tiền rồi mà người ta báo chưa nhận được gì cả, giao dịch thì báo thành công. Tôi muốn tra soát thì phải làm sao và bao lâu mới có kết quả?", agent="""Mình hiểu rằng bạn đang gặp vấn đề với giao dịch chuyển tiền. Tuy nhiên, để mình có thể tra soát giao dịch và hỗ trợ bạn tốt hơn, bạn cần xác thực OTP trong ứng dụng trước. 

Sau khi xác thực, bạn có thể cung cấp cho mình mã giao dịch hoặc số điện thoại liên quan đến giao dịch đó, và mình sẽ giúp bạn tra soát. Thời gian xử lý khiếu nại sẽ không quá 45 ngày làm việc kể từ khi nhận được yêu cầu.

Nếu bạn cần thêm thông tin hoặc có câu hỏi khác, hãy cho mình biết nhé!"""),

 dict(ca_cu=4, sid="RAG-39", khach="Ngày làm việc tính thế nào, có tính thứ bảy không?", agent="""Mình chưa có thông tin chính xác về cách tính ngày làm việc của [ORGANIZATION], nhưng thông thường, ngày làm việc thường tính từ thứ Hai đến thứ Sáu, không bao gồm thứ Bảy và Chủ Nhật. 

Nếu bạn cần thông tin cụ thể hơn về chính sách của [ORGANIZATION], mình khuyên bạn nên liên hệ trực tiếp với bộ phận chăm sóc khách hàng của họ để có câu trả lời chính xác nhất. Nếu có câu hỏi nào khác, mình sẵn sàng hỗ trợ!"""),

 dict(ca_cu=5, sid="RAG-41", khach="Tôi mất tiền khi mua hàng thì MoMo có đền không?", agent="""Khi bạn mất tiền khi mua hàng, việc hoàn tiền sẽ phụ thuộc vào chính sách của từng đơn vị cung cấp dịch vụ hoặc sản phẩm. Thông thường, hoàn tiền là số tiền bạn được hoàn lại sau khi mua sản phẩm hoặc dịch vụ, và tỷ lệ hoàn tiền có thể khác nhau tùy thuộc vào sản phẩm, số tiền bạn đã chi, hoặc chính sách của từng thương hiệu.

Nếu bạn đã hủy đơn hàng, thời gian hoàn tiền qua ví MoMo sẽ là trong 24 giờ làm việc kể từ khi bạn nhận được thông báo hoàn tiền thành công từ ứng dụng của đơn vị bán hàng.

Nếu bạn cần thêm thông tin chi tiết hoặc có câu hỏi khác, hãy cho mình biết nhé!"""),

 dict(ca_cu=6, sid="UXQA-001", khach=None, agent="""Mình hiểu rằng bạn đang rất lo lắng về việc bị trừ 59.000đ. Mình đã tra cứu và tìm thấy một giao dịch với số tiền này. Cụ thể, giao dịch này có mã là **TXN20260721000071**, được thực hiện vào ngày **21/07/2026** và đã hoàn tất thành công. Giao dịch này thuộc phạm vi **nội bộ ví** và có chiều hướng **trừ tiền**.

Đây là giao dịch đã được thực hiện bình thường do chính bạn. Bạn có muốn tiếp tục khiếu nại về giao dịch này không?"""),

 dict(ca_cu=7, sid="UXQA-007", khach=None, agent="""Mình không có thông tin chính xác về chính sách lưu trữ dữ liệu cuộc trò chuyện cụ thể. Nếu bạn cần câu trả lời chính thức, mình khuyên bạn nên liên hệ với bộ phận CSKH để được hỗ trợ thêm. Bạn có cần giúp gì khác không?"""),

 dict(ca_cu=8, sid="RAG-40", khach="Nghi ngờ gian lận thì MoMo làm gì với tiền trong ví?", agent="""Mình xin phép không hỗ trợ được nội dung này vì ngoài phạm vi của mình — mình chỉ hỗ trợ các vấn đề liên quan tới ví điện tử. Mình có thể giúp gì thêm cho bạn về ví không?"""),

 dict(ca_cu=9, sid="UXQA-005", khach=None, agent="""Xin lỗi, nhưng mình không có thông tin chính xác về đầu tư và không thể đưa ra lời khuyên tài chính. Bạn nên tham khảo ý kiến từ các chuyên gia tài chính hoặc tìm hiểu thêm về các cơ hội đầu tư phù hợp với mục tiêu và khả năng của mình. Nếu bạn cần hỗ trợ về các vấn đề liên quan đến ví điện tử, mình rất sẵn lòng giúp đỡ!"""),

 dict(ca_cu=10, sid="UXQA-004", khach=None, agent="""Mình biết bạn đang mong chờ thông tin về việc hoàn tiền. Tuy nhiên, mình không thể tự quyết định hoàn tiền cho bạn. Để xử lý yêu cầu này, mình cần tạo một hồ sơ khiếu nại cho giao dịch của bạn.

Trước tiên, mình cần xác định rõ loại khiếu nại và phạm vi giao dịch. Bạn có thể cho mình biết rõ hơn về giao dịch này không? Nếu không, mình sẽ tạo hồ sơ với thông tin hiện có."""),

 dict(ca_cu=11, sid="UXQA-005", khach=None, agent="""Mình xin phép không hỗ trợ được nội dung này vì ngoài phạm vi của mình — mình chỉ hỗ trợ các vấn đề liên quan tới ví điện tử. Mình có thể giúp gì thêm cho bạn về ví không?"""),

 dict(ca_cu=12, sid="UXQA-005", khach=None, agent="""Xin lỗi, nhưng mình không thể đưa ra lời khuyên về đầu tư. Đây là ngoài phạm vi hỗ trợ của mình. Bạn có thể cân nhắc tìm kiếm thông tin từ các chuyên gia tài chính hoặc nguồn tư vấn phù hợp để có quyết định tốt nhất cho mình. Nếu bạn có câu hỏi nào khác liên quan đến ví điện tử, mình rất sẵn lòng giúp đỡ!"""),

 dict(ca_cu=13, sid="RAG-43", khach="Tôi phải bồi hoàn cho MoMo trong trường hợp nào?", agent="""Xin lỗi, phần này mình không trả lời trực tiếp được. Để đảm bảo an toàn thông tin cho bạn, mình chuyển sang chuyên viên hỗ trợ nhé."""),

 dict(ca_cu=14, sid="UXQA-002", khach=None, agent="""Mình hiểu rằng bạn đang chờ thông tin về giao dịch TXN-0001. Tuy nhiên, hiện tại mình chưa tra được trạng thái giao dịch này do đối tác ngân hàng phản hồi chậm. 

Mình sẽ tiếp tục theo dõi và thông báo cho bạn ngay khi có thông tin mới. Nếu bạn cần hỗ trợ gì thêm, hãy cho mình biết nhé!"""),

 dict(ca_cu=15, sid="UXQA-006", khach=None, agent="""Mình xin phép không hỗ trợ được nội dung này vì ngoài phạm vi của mình — mình chỉ hỗ trợ các vấn đề liên quan tới ví điện tử. Mình có thể giúp gì thêm cho bạn về ví không?"""),

 dict(ca_cu=16, sid="UXQA-006", khach=None, agent="""Mình hiểu bạn đang gặp khó khăn trong việc kiểm tra giao dịch. Để giúp bạn tốt hơn, mình có thể tra cứu lịch sử giao dịch của bạn. Bạn có thể cho mình biết khoảng thời gian gần đây mà bạn nghi ngờ có giao dịch bị trừ tiền sai không? Nếu có số tiền cụ thể, bạn cũng có thể cho mình biết luôn nhé!"""),

 dict(ca_cu=17, sid="RAG-44", khach="MoMo có quyền thu phí dịch vụ không?", agent="""Có, [PERSON_VN] (M_Service) có quyền áp dụng phí dịch vụ đối với việc sử dụng sản phẩm và dịch vụ, bao gồm cả dịch vụ ví điện tử. Nếu phí dịch vụ được áp dụng, người sử dụng sẽ đồng ý rằng phí này đã bao gồm thuế giá trị gia tăng (VAT). 

M_Service cũng có quyền điều chỉnh, thay đổi hoặc bổ sung các loại phí và mức phí dịch vụ tại bất kỳ thời điểm nào. Nếu người sử dụng tiếp tục sử dụng sản phẩm hoặc dịch vụ, điều đó được hiểu là họ đã đồng ý và chấp nhận các nội dung liên quan đến phí dịch vụ.

Nếu bạn cần thêm thông tin hoặc có câu hỏi khác, hãy cho mình biết nhé!"""),

 dict(ca_cu=18, sid="UXQA-003", khach=None, agent="""Mình là trợ lý AI, không phải nhân viên thật. Mình ở đây để hỗ trợ bạn với các vấn đề liên quan đến ví điện tử. Bạn cần giúp gì hôm nay?"""),

 dict(ca_cu=19, sid="RAG-37", khach="Gửi khiếu nại rồi bao lâu có kết quả?", agent="""Thời gian xử lý khiếu nại sẽ tùy thuộc vào từng trường hợp cụ thể và tính phức tạp của đề nghị. Tuy nhiên, thời gian xử lý sẽ không quá 45 ngày làm việc kể từ ngày nhận được đề nghị. Nếu không xác định được kết quả trong thời gian này, sẽ có thỏa thuận về phương án xử lý trong vòng 15 ngày làm việc tiếp theo. 

Nếu bạn cần thêm thông tin hay có câu hỏi khác, mình sẵn sàng hỗ trợ!"""),

 dict(ca_cu=20, sid="UXQA-007", khach=None, agent="""Cuộc trò chuyện này sẽ không được lưu lại để bảo vệ quyền riêng tư của bạn. Chúng tôi chỉ sử dụng thông tin trong cuộc trò chuyện để hỗ trợ bạn tốt nhất có thể trong thời gian thực. Nếu bạn có bất kỳ câu hỏi nào khác hoặc cần hỗ trợ, hãy cho tôi biết!"""),

 dict(ca_cu=21, sid="UXQA-004", khach=None, agent="""Mình không thể xác nhận chắc chắn rằng bạn sẽ được hoàn tiền lại, vì việc này phụ thuộc vào quy trình xác minh của bộ phận CSKH. Nếu bạn muốn, mình có thể tạo hồ sơ khiếu nại để chuyên viên kiểm tra và xử lý trường hợp của bạn.

Nếu bạn đồng ý, vui lòng xác nhận để mình tiến hành tạo hồ sơ nhé!"""),

 dict(ca_cu=22, sid="UXQA-001", khach=None, agent="""Mình hiểu rằng bạn đang rất lo lắng về việc bị trừ 59.000đ. Mình đã tìm thấy giao dịch này với mã giao dịch TXN20260721000071, diễn ra vào ngày 21/07/2026, và giao dịch này đã hoàn tất bình thường với trạng thái thành công. Điều này có nghĩa là đây không phải là lỗi hệ thống.

Bạn có muốn tiếp tục khiếu nại về giao dịch này không?"""),

 dict(ca_cu=23, sid="UXQA-001", khach=None, agent="""Mình đã tra cứu và thấy có một giao dịch trừ 59.000đ vào ngày 21/07/2026 lúc 19:42. Giao dịch này có mã là **TXN20260721000071** và được thực hiện từ ví nội bộ của bạn.

Để mình giúp bạn xử lý vấn đề này, bạn có thể cho mình biết rõ hơn về lý do bạn cho rằng đây là giao dịch oan uổng không? Sau đó, mình sẽ tạo hồ sơ khiếu nại cho bạn."""),

 dict(ca_cu=24, sid="UXQA-006", khach=None, agent="""Mình hiểu bạn đang gặp khó khăn trong việc kiểm tra giao dịch. Để giúp bạn tốt hơn, mình sẽ tra cứu lịch sử giao dịch gần đây của bạn. Bạn có thể cho mình biết số tiền hoặc thời gian gần đây mà bạn nghĩ là giao dịch bị trừ sai không?"""),

 dict(ca_cu=25, sid="UXQA-002", khach=None, agent="""Mình không thể tra cứu được giao dịch TXN-0001 vì hệ thống ngân hàng phản hồi chậm. Bạn có thể đợi một chút và thử lại sau. Nếu cần, mình có thể hỗ trợ bạn thêm thông tin gì khác không?"""),

 dict(ca_cu=26, sid="UXQA-007", khach=None, agent="""Mình chưa có thông tin chính xác về chính sách lưu trữ dữ liệu cuộc trò chuyện này. Nếu bạn cần câu trả lời chính thức, mình khuyên bạn nên liên hệ với bộ phận CSKH để được hỗ trợ thêm. Bạn có cần giúp gì khác không?"""),

 dict(ca_cu=27, sid="UXQA-001", khach=None, agent="""Mình đã tra cứu và thấy có một giao dịch trừ 59.000đ vào ngày 21/07/2026 lúc 19:42. Giao dịch này có mã giao dịch là **TXN20260721000071** và thuộc loại giao dịch nội bộ (internal wallet).

Bạn có thể cho mình biết rõ hơn về lý do bạn cho rằng đây là giao dịch không hợp lệ? Mình sẽ giúp bạn tạo hồ sơ khiếu nại để chuyên viên kiểm tra."""),

 dict(ca_cu=28, sid="UXQA-001", khach=None, agent="""Mình đã tra cứu và thấy có một giao dịch trừ 59.000đ vào ngày 21/07/2026 lúc 19:42. Giao dịch này có mã là **TXN20260721000071** và được thực hiện từ ví nội bộ của bạn.

Để giúp bạn giải quyết vấn đề này, mình sẽ tạo một hồ sơ khiếu nại cho giao dịch này. Bạn có thể cho mình biết thêm thông tin về lý do bạn cho rằng đây là giao dịch không hợp lệ không?"""),
]
