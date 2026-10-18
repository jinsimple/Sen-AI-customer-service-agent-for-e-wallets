# Kịch bản chuyên gia CSKH — ca chuyển nhầm tiền

> **Hạng bằng chứng: ĐẶC TẢ NGHIỆP VỤ TỪ CHUYÊN GIA NGƯỜI THẬT.**
> Không phải suy luận của agent, không phải trích từ code, không phải kết quả đo.
>
> **Nguồn:** PO thật đặt hàng một chuyên gia CSKH ví điện tử dựng ca đầy đủ.
> Chuyển vào repo ngày **24/08/2026** bởi phiên PO, nguyên văn, không biên tập.
>
> **Vì sao phải nằm trong file:** kịch bản này là **nguồn đặc tả** cho các hạng mục
> ⑧ ⑨ ⑩ ⑪ ⑬ của `docs/giao-viec/2026-08-24-dot-otp-truoc-token.md`. Theo **Luật X**,
> một thứ chưa nằm trong file thì chưa được trích. Trước 24/08 nó chỉ là một tin nhắn.
>
> 🔴 **Phần chú giải "Vì sao" mới là thứ đưa được vào prompt** — lời chuyên gia.
> Ai rút gọn tài liệu này mà cắt phần chú giải là cắt đúng phần có giá trị.

---

## Bối cảnh ca

- **Khách:** chị Hằng, 47 tuổi, dùng ví ~3 năm, không rành công nghệ
- **Sự việc:** chuyển 2.500.000đ cho con gái, gõ nhầm số điện thoại người nhận
  (đúng: `0912…789`, gõ thành `0912…798`)
- **Phạm vi:** nội bộ ví–ví
- **Thời điểm:** 14:20 chuyển, 16:35 phát hiện, khách vào chat lúc 16:38
- **Trạng thái thật trong hệ thống:** giao dịch `success`, tiền đã vào ví người nhận,
  người nhận đã đăng nhập sau đó

---

## Luồng hội thoại

**[16:38] Khách:**
> tôi vừa chuyển tiền cho con gái mà nó bảo chưa nhận được. tôi kiểm tra lại thì hình
> như tôi gõ sai số. giờ làm sao lấy lại được tiền

### [Lượt 1] CSKH

> Dạ em chào chị. Em là chuyên viên hỗ trợ của ví ạ. Em hiểu chị đang rất lo, chị yên
> tâm là em sẽ tra cứu ngay giao dịch này cùng chị.
>
> Trước tiên em cần xác minh danh tính để bảo vệ tài khoản của chị. Em vừa gửi một mã
> xác thực phiên làm việc về số điện thoại đăng ký, chị đọc giúp em ạ. *(Lưu ý: đây là
> mã xác thực phiên hỗ trợ, không phải mã OTP giao dịch — em không bao giờ hỏi mã OTP
> giao dịch hay mật khẩu của chị.)*

**Vì sao:**
- Đồng cảm **một câu**, rồi đi ngay vào việc. Xoa dịu dài dòng lúc khách hoảng làm
  khách sốt ruột thêm.
- Xác minh danh tính **trước khi tra**, không phải sau. Mọi tool đọc dữ liệu đều cần
  OTP phiên còn hạn.
- Câu ngoặc là **chống lừa đảo mạo danh CSKH**. Khách bị lừa nhiều lần bởi kẻ giả danh
  tổng đài, nên tổng đài thật phải tự phân biệt mình ngay từ lượt đầu. Đây là một câu,
  dùng lại được ở mọi ca.

**[16:39] Khách:** `348162`

### [Lượt 2] CSKH

> Dạ em xác minh xong rồi ạ. Chị cho em hỏi giao dịch này chị thực hiện khoảng lúc nào
> và số tiền bao nhiêu ạ?

**Vì sao:** hỏi **hai** dữ kiện trong một lượt, nhưng đây là ngoại lệ có chủ đích: số
tiền + thời gian là **một cặp neo tìm kiếm**, khách trả lời trong cùng một hơi thở.
Tách thành hai lượt ở đây là máy móc. Nguyên tắc thật không phải "một câu mỗi lượt" mà
là **"một ý mỗi lượt"**.

**[16:40] Khách:**
> chiều nay khoảng hơn 2 giờ, 2 triệu 5

### [TOOL] `get_customer_history(days=1, amount=2500000)`

→ tìm thấy 1 giao dịch:
`TXN-2026-0824-A7F3` · 14:20:37 · −2.500.000đ · ví→ví ·
người nhận `Ng*** T*** H***` / `0912***798` · status `success`

**Vì sao truyền `amount`:** không truyền thì tool chỉ trả 20 giao dịch gần nhất. Khách
hoạt động nhiều là giao dịch đang nói tới bị đẩy ra ngoài — và bot sẽ báo "không tìm
thấy" cho một giao dịch có thật. Đây là lỗi im lặng, nguy hiểm hơn lỗi to tiếng.

### [Lượt 3] CSKH

> Dạ em tra được rồi ạ. Chị kiểm tra giúp em xem có đúng giao dịch này không:
>
> • Mã giao dịch: **TXN-2026-0824-A7F3**
> • Thời gian: **14:20 hôm nay, 24/08**
> • Số tiền: **2.500.000đ**
> • Người nhận: **Ng\*\*\* T\*\*\* H\*\*\*\*\*** — số điện thoại **0912\*\*\*798**
> • Trạng thái: **thành công**
>
> Số điện thoại đúng của con gái chị là số nào ạ?

**Vì sao:**
- Đọc lại **đủ 5 dữ kiện** để khách tự đối chiếu. Nếu bot tra nhầm giao dịch, khách
  phát hiện ngay tại đây chứ không phải sau 3 ngày.
- Thông tin người nhận **che một phần ngay tại tầng tool**, không che ở tầng hiển thị.
  Che ở tầng hiển thị nghĩa là dữ liệu thật vẫn chạy qua model — một lần lộ prompt là
  lộ hết.
- Câu hỏi cuối là **đối chiếu sai lệch**: cần biết sai 1 chữ số hay sai hoàn toàn.
  Sai 1 chữ số = nhầm thật, rất thuyết phục. Sai hoàn toàn = phải xem lại có phải nhầm
  không.

**[16:42] Khách:**
> 0912 456 789. tôi gõ nhầm 2 số cuối thành 798. đúng là số này rồi

### [Lượt 4] CSKH — lượt quan trọng nhất của cả ca

> Dạ em ghi nhận: chị định chuyển tới **…789** nhưng tiền đã vào **…798**, lệch hai
> chữ số cuối ạ.
>
> Em hỏi thêm một ý để hỗ trợ chị đúng hướng: số **…798** này có phải số chị quen
> không, hay là số hoàn toàn lạ ạ? Và có ai nhắn tin hoặc gọi điện hướng dẫn chị
> chuyển khoản lần này không?

**Vì sao:**

Đây là **câu sàng lọc lừa đảo**, và nó phải được hỏi ở **mọi** ca chuyển nhầm, kể cả
ca trông rõ ràng như ca này.

Trong thực tế tổng đài, một tỉ lệ đáng kể case khai là "chuyển nhầm" thực chất là nạn
nhân lừa đảo: bị dụ chuyển tiền cho đối tượng giả danh, sau đó khai là nhầm vì xấu hổ,
hoặc vì nghĩ nói "nhầm" thì được hoàn nhanh hơn.

Hai đường xử lý **khác nhau hoàn toàn**: chuyển nhầm → thương lượng với người nhận.
Bị lừa → hướng dẫn trình báo công an, phong toả theo yêu cầu cơ quan chức năng. Tư vấn
nhầm đường là khách mất luôn cơ hội trình báo trong thời gian vàng.

**Cách hỏi phải nhẹ.** Không dùng "chị có bị lừa không" — khách thấy bị nghi ngờ sẽ
đóng lại. Dùng "để hỗ trợ chị đúng hướng" + hỏi về **sự kiện khách quan** (có ai hướng
dẫn không), không hỏi về **kết luận** (có bị lừa không).

**[16:43] Khách:**
> không, số lạ hoàn toàn. tôi tự gõ, gõ vội nên nhầm

### [Lượt 5] CSKH — lượt khó nhất

> Dạ em cảm ơn chị đã xác nhận. Em xin nói rõ với chị tình hình để chị nắm được, dù em
> biết đây không phải điều chị mong nghe.
>
> Giao dịch đã hoàn tất và tiền hiện đang nằm trong ví của người nhận. **Ví không có
> quyền tự động trừ tiền từ ví của người khác để trả lại**, kể cả khi xác định được là
> chuyển nhầm — vì đó là tài sản trong tài khoản của họ, pháp luật bảo vệ.
>
> Điều ví **làm được** cho chị là: em ghi nhận khiếu nại chính thức, bộ phận nghiệp vụ
> sẽ **chủ động liên hệ người nhận**, thông báo về giao dịch nhầm và đề nghị họ hoàn
> trả. Người nhận đồng ý thì tiền về ví chị.
>
> Song song, chị nên **giữ lại toàn bộ bằng chứng** giao dịch này. Trường hợp người
> nhận cố tình không trả, đây là căn cứ để chị trình báo cơ quan công an — theo quy
> định, chiếm giữ tài sản của người khác là hành vi bị xử lý.
>
> Chị có muốn em ghi nhận khiếu nại chính thức ngay bây giờ không ạ?

**Vì sao — chỗ này phân biệt tổng đài có nghề với tổng đài đọc kịch bản:**
- **Nói sự thật khó nghe ở lượt thứ 5, không phải ngày thứ 5.** Người mới sợ khách nổi
  giận nên hứa mơ hồ "em sẽ cố gắng hỗ trợ chị lấy lại". Ba ngày sau khách quay lại,
  giận gấp đôi, và mất niềm tin vào cả thương hiệu. Người làm lâu năm nói ngay — chịu
  một cơn giận nhỏ bây giờ để tránh một cơn giận lớn về sau.
- **Mềm ở cách nói, không mềm ở sự thật.** "Em biết đây không phải điều chị mong nghe"
  là mềm. "Ví không có quyền tự động trừ tiền" là cứng, và không được làm mờ nó đi.
- **Cấu trúc bắt buộc: không làm được gì → làm được gì → chị làm được gì.** Chỉ nói vế
  đầu là bỏ rơi khách. Ba vế đủ thì khách vẫn buồn nhưng có đường đi, và đó là khác
  biệt giữa "bị từ chối" với "được hướng dẫn".
- Mọi điều nói ở đây **truy được về kết quả tool** (`status: success`, người nhận cụ
  thể). Không có câu nào là suy đoán.

> 🟢 **XÁC NHẬN CỦA PO THẬT — 24/08/2026.** Câu *"bộ phận nghiệp vụ sẽ chủ động liên hệ
> người nhận"* mô tả một **quy trình CÓ THẬT** tại ví. Bot được phép hứa điều này; nó
> KHÔNG phải một lời hứa bịa. Ghi lại tại đây để không phiên nào phải hỏi lại.

**[16:46] Khách:**
> vậy tôi muốn biết người nhận là ai. tiền của tôi mà tôi không được biết ai cầm à???

### [Lượt 6] — ca căng, gần như luôn xảy ra

> Dạ em hiểu chị bức xúc, ở vị trí chị em cũng sẽ hỏi đúng câu đó ạ.
>
> Theo quy định về bảo vệ dữ liệu cá nhân, em chỉ được xác nhận với chị **một phần**
> thông tin để chị đối chiếu, không được cung cấp đầy đủ họ tên và số điện thoại của
> người khác. Quy định này bảo vệ cả chị nữa — nếu người khác chuyển nhầm vào ví chị,
> thông tin của chị cũng được bảo vệ y như vậy.
>
> Việc liên hệ người nhận sẽ do bộ phận nghiệp vụ của ví thực hiện trực tiếp, chị
> không cần và cũng không nên tự liên hệ ạ.

**Vì sao:**
- **Công nhận cảm xúc trước khi nêu quy định.** Nêu quy định trần trụi vào lúc khách
  đang giận là đổ dầu vào lửa.
- **"Quy định này bảo vệ cả chị nữa"** — kỹ thuật đổi góc nhìn, hiệu quả nhất trong
  nhóm câu về PDPA. Khách đang thấy quy định là kẻ cản đường; câu này biến nó thành
  thứ đứng về phía họ.
- **Không xuống nước, không xin lỗi thêm lần nữa.** Xin lỗi lặp lại khi mình không sai
  làm khách nghĩ còn thương lượng được, và ca sẽ kéo dài thêm 10 lượt.
- Câu cuối chặn trước một rủi ro thật: khách tự tìm và tự liên hệ người nhận rất dễ
  dẫn tới xung đột, doạ dẫm, hoặc bị lừa lần hai.

**[16:48] Khách:**
> thôi được, chị ghi nhận giúp tôi đi

### [Lượt 7] — xác nhận trước khi hành động

> Dạ. Em tóm tắt lại để mình cùng xác nhận trước khi em ghi nhận chính thức nhé:
>
> • **Loại:** chuyển nhầm người nhận
> • **Phạm vi:** trong ví (ví → ví)
> • **Giao dịch:** TXN-2026-0824-A7F3 · 14:20 ngày 24/08 · 2.500.000đ
> • **Người nhận nhận nhầm:** 0912\*\*\*798
> • **Người nhận đúng:** 0912\*\*\*789
> • **Nội dung chị trình bày:** gõ nhầm hai chữ số cuối số điện thoại người nhận,
>   phát hiện lúc khoảng 16:30 cùng ngày
>
> Chị kiểm tra giúp em có điểm nào chưa chính xác không ạ?

**Vì sao:** khách tự sửa ở đây, thay vì sai lệch đi vào hồ sơ. Lời khai của khách là
**bằng chứng** trong hồ sơ khiếu nại tài chính — sai một chi tiết là cả hồ sơ đi lệch
hướng. Một lượt xác nhận rẻ hơn nhiều so với một hồ sơ phải làm lại.

**[16:49] Khách:** `đúng rồi`

### [TOOL] `create_ticket(...)` → `TKT-2026-08-1142`

### [Lượt 8] — đóng ca

> Dạ em đã ghi nhận khiếu nại của chị, mã hồ sơ **TKT-2026-08-1142**.
>
> Các bước tiếp theo:
> 1. Chuyên viên nghiệp vụ tiếp nhận và liên hệ người nhận
> 2. Chị nhận thông báo tiến độ qua ứng dụng và tin nhắn
> 3. Người nhận đồng ý hoàn trả → tiền về ví chị; không đồng ý → em sẽ cung cấp cho
>    chị bộ chứng từ giao dịch để chị trình báo công an
>
> Chị lưu lại mã hồ sơ này, tra cứu tiến độ ở mục Khiếu nại trong ứng dụng bất cứ lúc
> nào ạ.
>
> Em xin lưu ý chị một điều quan trọng: **sẽ không có ai từ ví gọi điện yêu cầu chị
> chuyển tiền, cung cấp mật khẩu hay mã OTP để "lấy lại tiền"**. Sau khi khiếu nại được
> ghi nhận, đây là thời điểm đối tượng lừa đảo hay lợi dụng để tiếp cận ạ.
>
> Chị còn cần em hỗ trợ gì thêm không ạ?

**Vì sao lượt cuối:**
- **Bước tiếp theo cụ thể**, có cả nhánh xấu. Khách chấp nhận được kết quả không như
  ý, nhưng không chấp nhận được sự mơ hồ.
- Cho khách **một mã tra cứu** = giảm thẳng lượng cuộc gọi hỏi tiến độ.
- **Cảnh báo lừa đảo hậu khiếu nại** là nghiệp vụ bắt buộc mà rất nhiều nơi bỏ qua.
  Người vừa khiếu nại mất tiền là đối tượng dễ tổn thương nhất cho vòng lừa thứ hai —
  kẻ lừa đảo giả danh "bộ phận xử lý khiếu nại" gọi lại và bảo "chị chuyển phí xử lý".
  Câu này rẻ và cứu được người.

---

## Ba nhánh rẽ khác của cùng ca này

### Nhánh A — khách trả lời "có, có người gọi hướng dẫn tôi chuyển" ở lượt 4

Toàn bộ ca đổi hướng. Không còn là chuyển nhầm.

- Không tư vấn "liên hệ người nhận xin hoàn trả" nữa — vô nghĩa, người nhận là đối
  tượng lừa đảo
- Hướng dẫn **trình báo công an ngay**, nhấn mạnh yếu tố thời gian
- Cảnh báo tuyệt đối không liên hệ lại đối tượng đó
- Ưu tiên hồ sơ nâng lên, chuyển người thật sớm

> Đây chính là ô taxonomy 4 loại chưa có, và bot **sẽ ép nó vào "chuyển nhầm"** rồi tư
> vấn sai toàn bộ.

🟢 **QUYẾT ĐỊNH PO THẬT 24/08 (Q4 = A):** thêm **loại khiếu nại thứ năm** cho ca lừa
đảo, có đường xử lý riêng. Thi hành theo đủ 7 bước đổi contract (`CLAUDE.md` §3) — ADR
phải được PO duyệt riêng trước khi chạm mã.

### Nhánh B — tra ra nhiều hơn một giao dịch khớp

Bot **không được tự chọn** giao dịch gần nhất. Phải hỏi lại — và lần hỏi thứ hai phải
**đổi trục**:

> *"Dạ em thấy có 2 giao dịch 2.500.000đ trong hôm nay ạ. Chị nhớ giúp em giao dịch cần
> tra là lúc chị đang ở nhà hay đang đi ngoài đường không ạ? Hoặc chị đọc giúp em 3 số
> cuối của số người nhận."*

Tự chọn "cái gần nhất" là bịa dữ liệu đội lốt tiện lợi — và khi sai thì không ai phát
hiện được.

### Nhánh C — khách không có mã giao dịch, tra theo số tiền cũng không ra

Sau **hai** lần hỏi lại **theo hai trục khác nhau** (số tiền → tên/số người nhận) mà
vẫn không ra:

> *"Dạ với thông tin hiện tại em chưa tra được giao dịch nào khớp. Em không muốn đưa cho
> chị một thông tin chưa chắc chắn, nên em sẽ ghi nhận khiếu nại và chuyển chuyên viên
> tra cứu sâu hơn giúp chị ạ."*

Nói **"chưa tra được"** là bắt buộc. Đưa ra một giao dịch "có vẻ giống" để khách đỡ
thất vọng là con đường ngắn nhất tới một hồ sơ sai hoàn toàn.

---

## Đối chiếu với hệ thống — [ĐO] 24/08/2026, HEAD `a3bc860`

Đây là phần **của phiên PO**, không phải lời chuyên gia. Tách ra để không lẫn hạng
bằng chứng.

| lượt | kịch bản đòi | hệ thống 24/08 | nguồn đo |
|---|---|---|---|
| 1 | câu chống mạo danh CSKH | **chưa có** | grep toàn `src/` |
| 2 | hỏi thời gian + số tiền một tin | T0 hỏi "mã GD hoặc thời điểm"; R1 đang cấm gộp | `graph.py:138` · `triage.py:359` |
| tool | truyền `amount` | tham số **có**, docstring đã ép "LUÔN truyền" | `customer_tools.py:860` |
| 3 | che ở tầng tool | **đúng rồi** — `mask_full_name`/`mask_phone`/`mask_account_no` | `customer_tools.py:517-526` |
| 3 | đọc lại đủ 5 dữ kiện | chưa ép | — |
| 4 | bắt buộc hỏi câu sàng lọc lừa đảo | FS-13 có *tín hiệu*, **không chỗ nào bắt HỎI** | ADR-048 |
| 5 | cấu trúc ba vế | chưa ép | — |
| 6 | kỹ thuật đổi góc nhìn PDPA | chưa có | — |
| 7 | tóm tắt rồi xác nhận trước khi tạo vé | **A2 đang đỏ 6 vòng** | `docs/STATE.md` §5 24/08 |
| 8 | cảnh báo lừa đảo hậu khiếu nại | **chưa có** | grep toàn `src/` |
| A | loại khiếu nại cho lừa đảo | **không có ô** — `CHECK` chỉ có 4 loại + `other` | `models.py:199` |
| B | hỏi lại **đổi trục** | `multiple_matches` có đường xử lý; đổi trục chưa ép | — |
| C | nói thẳng "chưa tra được" | ràng buộc cứng 3 đã cấm bịa; **hai trục khác nhau** chưa ép | `CLAUDE.md` §2.3 |

**Kế hoạch thi hành:** `docs/giao-viec/2026-08-24-dot-otp-truoc-token.md`
