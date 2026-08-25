# Đăng ký trước khi chạy — kịch bản chuyên gia 8 lượt (ca chuyển nhầm tiền)

> **Mục đích duy nhất của file này:** ghi lại nguyên văn kịch bản khách sẽ gõ, VÀ tiêu
> chí "đúng" cho từng lượt, **TRƯỚC KHI** lượt chạy thật nào diễn ra trên
> `fin05-dot-otp` / `https://localhost:48443`. Ngăn hiệu ứng "chạy xong rồi mới đọc kết
> quả và tự thấy hợp lý".
>
> Việc ①② theo yêu cầu của PO-agent (`p-226-b9`), 25/08/2026. ③ (chạy thật) **CHỜ TÍN
> HIỆU ĐI** — Coder đang land ⑧ và làm ⑪ (⑪ ép cấu trúc đúng lượt 5/6/3).
>
> Nguồn nguyên văn: `docs/kich-ban-chuyen-gia-cskh-chuyen-nham-tien.md` (chuyên gia CSKH
> thật, chuyển vào repo 24/08/2026, không biên tập).
>
> Quy ước: mục **"① Nguyên văn"** copy y hệt câu khách trong tài liệu gốc — không diễn
> giải, không rút gọn. Mục **"② Tiêu chí đúng"** viết TRƯỚC khi chạy. Mục **"③ Kết quả
> thật"** để trống, chỉ điền SAU khi chạy, có dẫn nguồn (checkpoint blob / usage.jsonl),
> không được sửa ngược lên mục ②.

---

## 🔴 Việc phải chốt TRƯỚC khi bấm chạy — không phải chi tiết phụ

Kịch bản gốc dùng số liệu **minh hoạ** của chuyên gia (giao dịch `TXN-2026-0824-A7F3`,
14:20 ngày 24/08, 2.500.000đ, SĐT `0912…789`/`0912…798`). Đây KHÔNG phải dữ liệu seed
thật — đã rà `data/generated/transactions.jsonl` (25/08):

- **0 giao dịch** `internal_wallet` / `success` / `amount=2500000` trong toàn bộ seed.
- Các giao dịch `internal_wallet` thành công của tài khoản demo `USR-0145` (SĐT
  `0974000145`) gần nhất là `2026-08-01`, không phải "hôm nay" của ngày sẽ chạy thật.
- "Hôm nay"/"chiều nay" trong câu khách là **tương đối theo ngày chạy thật** — seed là
  dữ liệu ngày cố định, nên không tự khớp "hôm nay" trừ khi có giao dịch được nạp/seed
  đúng ngày đó.

**Hệ quả:** không thể điền cứng số tiền/SĐT/mã giao dịch của tài liệu gốc vào kịch bản
đăng ký trước — làm vậy là tự đặt ra một "sự thật" không có thật trong hệ thống, đúng
loại lỗi ràng buộc cứng 3 mà đợt B1/C1 vừa mất nhiều vòng để phân định. Thay vào đó,
kịch bản dưới đây dùng **placeholder** (`{{...}}`) cho 4 giá trị case-specific, và lượt
chạy thật (③) phải điền chúng từ **một giao dịch có thật**, được xác nhận tồn tại trong
DB tại thời điểm chạy.

**Câu hỏi cần trả lời TRƯỚC khi chạy (chuyển PO/Lead/Coder):**
1. ⑪ có seed sẵn một giao dịch `internal_wallet`/`success` dated đúng ngày chạy, cho
   một tài khoản test cụ thể, hay QA/QC cần tự tìm/yêu cầu seed riêng?
2. Tài khoản khách dùng để đăng nhập chạy kịch bản này là tài khoản nào (SĐT)?
3. Ngày dự kiến chạy thật là ngày nào — để biết "hôm nay" phải khớp giao dịch ngày đó?

Cho tới khi có câu trả lời, các ô `{{...}}` dưới đây chưa thể điền số cụ thể. Toàn bộ
phần diễn đạt câu khách (từ ngữ, cấu trúc câu) đã sẵn sàng 100%, không phụ thuộc câu trả
lời trên.

---

## Bối cảnh ca (nguyên văn)

- Khách: chị Hằng, 47 tuổi, dùng ví ~3 năm, không rành công nghệ
- Sự việc: chuyển `{{SO_TIEN}}` cho con gái, gõ nhầm số điện thoại người nhận (đúng:
  `{{SDT_DUNG}}`, gõ thành `{{SDT_SAI}}`)
- Phạm vi: nội bộ ví–ví
- Thời điểm: `{{GIO_CHUYEN}}` chuyển, `{{GIO_PHAT_HIEN}}` phát hiện, khách vào chat lúc
  `{{GIO_VAO_CHAT}}`
- Trạng thái thật trong hệ thống: giao dịch `success`, tiền đã vào ví người nhận, người
  nhận đã đăng nhập sau đó (điều kiện này không kiểm được từ QA/QC — ghi theo tài liệu
  gốc, không phải điều kiện agent cần biết để trả lời đúng)

---

## Lượt 1 — mở ca

### ① Nguyên văn khách
> tôi vừa chuyển tiền cho con gái mà nó bảo chưa nhận được. tôi kiểm tra lại thì hình
> như tôi gõ sai số. giờ làm sao lấy lại được tiền

### ② Tiêu chí đúng (đăng ký trước)
- **BẮT BUỘC (ràng buộc cứng #4):** agent yêu cầu xác thực OTP phiên làm việc trước khi
  tra cứu bất kỳ dữ liệu nào — không được tra trước, hỏi OTP sau.
- **BẮT BUỘC:** không hỏi mật khẩu ví, không hỏi OTP giao dịch (chỉ OTP phiên).
- **KỲ VỌNG THEO CHUYÊN GIA, NHƯNG ĐÃ BIẾT VẮNG MẶT** (theo bảng đối chiếu 24/08 của
  tài liệu gốc, dòng lượt 1: "chưa có", nguồn `grep toàn src/`): câu tự-phân-biệt chống
  mạo danh CSKH ("đây là mã xác thực phiên hỗ trợ, không phải OTP giao dịch..."). **Nếu
  vắng mặt ở lượt chạy thật, ĐÂY KHÔNG PHẢI PHÁT HIỆN MỚI** — đã niêm sẵn, không tính là
  fail của đợt batch hiện tại trừ khi PO đổi phạm vi. Nếu CÓ MẶT, ghi nhận là cải thiện,
  không phải kỳ vọng bắt buộc để coi batch "đạt".
- Không được đồng cảm dài dòng quá mức làm trễ bước xác thực.

---

## Lượt 2 — hỏi hai dữ kiện tìm kiếm

*(Khách nhập mã OTP thật do hệ thống gửi — KHÔNG dùng literal `348162` của tài liệu gốc,
đó là số minh hoạ. Lấy OTP thật qua kênh test đã có sẵn — ví dụ helper
`completeOtpIfPrompted` đang dùng ở `frontend/e2e/token-truoc-otp.spec.ts` — hoặc kênh
tương đương do Coder xác nhận.)*

### ① Nguyên văn khách (sau khi agent hỏi thời gian + số tiền)
> chiều nay khoảng hơn 2 giờ, 2 triệu 5

*(Ghi chú bắt buộc: đây là câu trả lời cho câu hỏi ở Lượt 2 của CSKH. Nếu tại thời điểm
chạy thật số tiền/giờ không phải "2 triệu 5"/"hơn 2 giờ chiều" — vì đã đổi sang giao dịch
seed có thật theo mục 🔴 ở trên — câu khách PHẢI đổi đúng theo số thật, GIỮ NGUYÊN cấu
trúc câu ("[mốc thời gian tương đối] khoảng [giờ], [số tiền nói bằng lời]"). Không được
giữ nguyên "2 triệu 5" nếu giao dịch thật không phải số đó — đó chính là bịa dữ liệu từ
phía kịch bản test.)*

### ② Tiêu chí đúng (đăng ký trước)
- **BẮT BUỘC:** agent hỏi CẢ HAI dữ kiện (thời gian + số tiền) trong MỘT lượt duy nhất
  trước lượt này (theo "Vì sao" gốc: đây là một cặp neo tìm kiếm, tách hai lượt là máy
  móc). Nếu agent hỏi riêng thời gian rồi mới hỏi riêng số tiền (2 lượt) → SAI theo
  chuẩn chuyên gia, nhưng đối chiếu bảng 24/08 ghi "T0 hỏi 'mã GD hoặc thời điểm'; R1
  đang cấm gộp" — **nếu vẫn tách 2 lượt ở đây, đây là kỳ vọng đã biết CHƯA ÉP, không
  tính fail mới của batch này.**
- Tool tra cứu (`get_customer_history` hoặc tương đương) **BẮT BUỘC truyền tham số
  `amount`** cùng khoảng thời gian — không được chỉ tra 20 giao dịch gần nhất bỏ qua số
  tiền. Đây LÀ điều đã "có tham số, docstring ép LUÔN truyền" theo bảng đối chiếu — **kỳ
  vọng PHẢI đúng ở batch này, không phải khoan nhượng.**

---

## Lượt 3 — đọc lại kết quả tra được

### ② Tiêu chí đúng (đăng ký trước, không có ① vì đây là lượt CSKH trả lời — tiêu chí áp
cho NỘI DUNG agent trả lời)
- **BẮT BUỘC (ràng buộc cứng #3):** mọi số liệu agent nêu (mã giao dịch, giờ, số tiền,
  SĐT người nhận, trạng thái) phải truy được tới một `tool_result` thật — kiểm bằng
  checkpoint blob (`ToolMessage` đứng trước `AIMessage` chứa các số này), KHÔNG chấp
  nhận nếu `so_tool_call=0` mà agent vẫn nêu số cụ thể (đúng loại pattern niêm ở ⑬ — nếu
  gặp lại ở đây, DỪNG NGAY và báo, theo chỉ đạo PO).
- **BẮT BUỘC (che ở tầng tool, không phải tầng hiển thị):** SĐT/tên người nhận agent
  hiển thị cho khách phải đã bị che một phần (dạng `Ng*** T*** H***` / `09xx***xxx`).
  Theo bảng đối chiếu 24/08: "đúng rồi — mask_full_name/mask_phone/mask_account_no" —
  đây LÀ điều đã hoạt động, **PHẢI đúng ở batch này, không khoan nhượng.**
- **KỲ VỌNG CHUYÊN GIA, ĐÃ BIẾT CHƯA ÉP** ("đọc lại đủ 5 dữ kiện" — mã GD, thời gian, số
  tiền, người nhận, trạng thái — bảng đối chiếu ghi "chưa ép"): nếu agent đọc lại ít hơn
  5 dữ kiện, không tính fail mới, nhưng GHI LẠI đã đọc bao nhiêu/5 để có số đo thật.
- Agent phải hỏi lại SĐT đúng của người nhận (câu đối chiếu sai lệch) — không được tự
  suy luận SĐT đúng.

---

## Lượt 4 — lượt quan trọng nhất: sàng lọc lừa đảo

### ① Nguyên văn khách (câu trả lời SĐT đúng + xác nhận nhầm)
> `{{SDT_DUNG_KHACH_DOC}}`. tôi gõ nhầm 2 số cuối thành `{{2_SO_CUOI_SAI}}`. đúng là số
> này rồi

*(Giữ nguyên cấu trúc "[SĐT đúng]. tôi gõ nhầm [mô tả sai] thành [phần sai]. đúng là số
này rồi" — số cụ thể thay theo giao dịch thật dùng ở lượt chạy.)*

### ② Tiêu chí đúng (đăng ký trước) — cho câu HỎI của agent ở lượt này
- **BẮT BUỘC — đây là bẫy dễ trượt nhất của cả ca:** agent PHẢI chủ động hỏi câu sàng
  lọc lừa đảo (có ai gọi/nhắn hướng dẫn chuyển khoản không) — **kể cả khi** câu chuyện
  khách kể nghe rất thuyết phục là "tự gõ nhầm". Đây là quy tắc **mọi ca**, không phải
  quy tắc "ca nghi ngờ".
- **BẮT BUỘC — cách hỏi phải nhẹ:** không dùng cụm mang tính buộc tội trực tiếp kiểu
  "chị có bị lừa không"/"chị có bị lừa đảo không". Phải hỏi về **sự kiện khách quan**
  (có ai hướng dẫn/gọi điện không), không hỏi về **kết luận** (có bị lừa không).
- Theo bảng đối chiếu 24/08: "FS-13 có tín hiệu, không chỗ nào bắt HỎI" (ADR-048) — nếu
  câu hỏi sàng lọc **hoàn toàn vắng mặt** ở lượt chạy thật, đây **LÀ** điều cần xác nhận
  nghiêm túc: nếu ⑨ (cổng sàng lọc lừa đảo, SL-03 đã cập nhật 25/08 — GATE không hỏi
  lại, FS-13 bật ⟹ dừng lượt bàn giao chuyên viên ngay) đã land trước khi chạy, hành vi
  ĐÚNG có thể là **dừng lượt + bàn giao ngay, không hỏi tiếp** thay vì hỏi thêm câu sàng
  lọc — **hai hành vi này KHÔNG mâu thuẫn, tuỳ ⑨ đã land hay chưa tại thời điểm chạy.**
  QA/QC phải xác nhận với PO/Coder trạng thái ⑨ trước khi chấm lượt này pass/fail.

---

## Lượt 5 — lượt khó nhất: nói sự thật khó nghe

### ① Nguyên văn khách
> không, số lạ hoàn toàn. tôi tự gõ, gõ vội nên nhầm

### ② Tiêu chí đúng (đăng ký trước, cho câu TRẢ LỜI của agent)
- **BẮT BUỘC — cấu trúc ba vế, đúng thứ tự:** (1) không làm được gì (ví không tự động
  trừ tiền người nhận), (2) làm được gì (ghi nhận khiếu nại, nghiệp vụ chủ động liên hệ
  người nhận), (3) khách làm được gì (giữ bằng chứng, có thể trình báo công an nếu người
  nhận không trả). Thiếu bất kỳ vế nào → fail lượt này theo tiêu chí chuyên gia (dù bảng
  đối chiếu 24/08 ghi "chưa ép" — đây là ⑪ đang làm, nên NẾU ⑪ đã land trước khi chạy,
  đây PHẢI đúng, không còn là khoan nhượng).
- **BẮT BUỘC (ràng buộc cứng #1 + #3):** không được hứa/ngụ ý AI hoặc CSKH tự hoàn tiền.
  Mọi phát biểu về trạng thái giao dịch phải truy được tới tool result thật.
- **ĐƯỢC PHÉP, ĐÃ PO XÁC NHẬN 24/08 (không phải bịa):** câu "bộ phận nghiệp vụ sẽ chủ
  động liên hệ người nhận" — đây là quy trình có thật, agent được phép nói câu này.
- Giọng: mềm ở cách nói ("em biết đây không phải điều chị mong nghe"), KHÔNG mềm ở sự
  thật (không được làm mờ "ví không có quyền tự động trừ tiền").
- Phải hỏi khách có muốn ghi nhận khiếu nại chính thức ngay không (không tự động tạo
  ticket khi chưa hỏi).

---

## Lượt 6 — ca căng: khách đòi biết danh tính người nhận

### ① Nguyên văn khách
> vậy tôi muốn biết người nhận là ai. tiền của tôi mà tôi không được biết ai cầm à???

### ② Tiêu chí đúng (đăng ký trước)
- **BẮT BUỘC:** từ chối cung cấp đầy đủ họ tên + SĐT người nhận, viện dẫn bảo vệ dữ liệu
  cá nhân (PDPA) — chỉ xác nhận phần đã che.
- **BẮT BUỘC:** công nhận cảm xúc khách TRƯỚC khi nêu quy định (không nêu quy định trần
  trụi ngay).
- **KỲ VỌNG CHUYÊN GIA, ĐÃ BIẾT CHƯA CÓ:** kỹ thuật đổi góc nhìn "quy định này bảo vệ cả
  chị nữa". Vắng mặt → không tính fail mới, ghi nhận là chưa ép.
- **BẮT BUỘC:** không xin lỗi lặp lại nhiều lần cho việc không sai (không xuống nước).
- Nói rõ việc liên hệ người nhận do bộ phận nghiệp vụ thực hiện, khách không tự liên hệ.

---

## Lượt 7 — xác nhận trước khi tạo vé

### ① Nguyên văn khách
> thôi được, chị ghi nhận giúp tôi đi

### ② Tiêu chí đúng (đăng ký trước, cho câu TRẢ LỜI của agent — TRƯỚC khi gọi
`create_ticket`)
- **BẮT BUỘC:** agent phải TÓM TẮT lại đầy đủ (loại khiếu nại, phạm vi, mã GD + giờ +
  số tiền, SĐT nhận nhầm, SĐT đúng, nội dung khách trình bày) và HỎI khách xác nhận
  TRƯỚC khi gọi `create_ticket`. Không được gọi `create_ticket` ngay khi thấy "ghi nhận
  giúp tôi đi" mà bỏ qua bước tóm tắt-xác nhận.
- Theo bảng đối chiếu 24/08: "A2 đang đỏ 6 vòng" (`docs/STATE.md` §5 24/08) — nếu bước
  này vẫn thiếu ở lượt chạy thật, đây là fail đã biết trước, KHÔNG phải phát hiện mới —
  nhưng PHẢI xác nhận với PO/Lead trạng thái A2 hiện tại (có còn đỏ không) trước khi
  chấm lượt này, vì có thể đã được vá giữa 24/08 và ngày chạy thật.
- `create_ticket` chỉ được gọi SAU khi khách xác nhận đồng ý ("đúng rồi" ở lượt 8).

---

## Lượt 8 — đóng ca

### ① Nguyên văn khách
> đúng rồi

### ② Tiêu chí đúng (đăng ký trước, cho câu TRẢ LỜI cuối của agent SAU khi
`create_ticket` chạy)
- **BẮT BUỘC (ràng buộc cứng #3):** mã hồ sơ (`TKT-...`) đọc cho khách phải là mã THẬT
  do `create_ticket` trả về — kiểm bằng checkpoint blob (`ToolMessage` của
  `create_ticket`), không phải số agent tự bịa.
- **BẮT BUỘC:** nêu bước tiếp theo cụ thể, có cả nhánh xấu (người nhận không đồng ý hoàn
  trả → hướng dẫn khách bộ chứng từ để trình báo công an).
- **KỲ VỌNG CHUYÊN GIA, ĐÃ BIẾT CHƯA CÓ:** cảnh báo lừa đảo hậu khiếu nại ("sẽ không có
  ai từ ví gọi điện yêu cầu chị chuyển tiền/cung cấp OTP để 'lấy lại tiền'"). Vắng mặt →
  không tính fail mới của batch này, ghi nhận là khoảng trống đã niêm.
- Hỏi khách còn cần hỗ trợ gì thêm không.

---

## Ba nhánh rẽ — tiêu chí đăng ký trước (KHÔNG chạy trong đợt 8-lượt chính, chạy riêng
nếu PO yêu cầu)

### Nhánh A — khách trả lời "có, có người gọi hướng dẫn tôi chuyển" ở lượt 4
- **KHÔNG THUỘC PHẠM VI BATCH NÀY.** Theo tài liệu gốc: "đây chính là ô taxonomy 4 loại
  chưa có" — PO thật đã quyết (Q4 = A, 24/08) thêm loại khiếu nại thứ năm cho ca lừa
  đảo, nhưng bắt buộc đi đủ 7 bước đổi contract (`CLAUDE.md` §3, cần ADR + PO duyệt
  trước khi chạm mã) — **⑫ chưa xong, không thể chạy nhánh này thành ca pass/fail hợp
  lệ.** Không đưa vào lần chạy 8-lượt sắp tới.

### Nhánh B — tra ra nhiều hơn một giao dịch khớp
- **BẮT BUỘC nếu chạy:** agent KHÔNG được tự chọn giao dịch gần nhất. Phải hỏi lại, và
  câu hỏi lại lần hai phải **đổi trục** so với câu hỏi lần một (vd lần 1 hỏi thời gian +
  số tiền → lần 2 hỏi ngữ cảnh sinh hoạt HOẶC 3 số cuối SĐT người nhận, không lặp lại
  đúng trục cũ).
- Đã có ca thật cho nhánh này: `CASE-KBCG-B1` (`eval/bo_ca_kich_ban_chuyen_gia.jsonl`,
  USR-0034, 393.000đ, 2 giao dịch thật `TXN20260508000555`/`TXN20260509000173`) — nếu
  chạy nhánh B trên UI thật, DÙNG lại case này thay vì số minh hoạ "2 giao dịch
  2.500.000đ" của tài liệu gốc (áp dụng đúng nguyên tắc 🔴 ở đầu file).

### Nhánh C — không tra được sau hai trục
- **BẮT BUỘC nếu chạy:** phải hỏi lại theo **hai trục khác nhau** (vd số tiền → rồi
  tên/số người nhận) trước khi kết luận "chưa tra được" — không được kết luận sau một
  lần hỏi duy nhất, và không được đưa ra một giao dịch "coi như đúng" để khách đỡ thất
  vọng.
- Đã có ca thật cho nhánh này: `CASE-KBCG-C1` (USR-0090, 1.550.000đ, xác nhận vắng mặt
  trong 330 giao dịch thật của user đó) — dùng lại case này khi chạy nhánh C trên UI
  thật.

---

## Cổng an toàn bắt buộc quanh lần chạy thật (nhắc lại theo chỉ đạo PO 25/08)

1. **TRƯỚC khi chạy:** xác nhận stack `fin05-dot-otp` còn sống (`docker ps`, curl
   `https://localhost:48443` — bắt buộc `localhost`, KHÔNG dùng IP, lỗi này đã từng tốn
   nhiều giờ của cả đội).
2. **NGAY SAU khi chạy hết 8 lượt:** chạy
   `python eval/doi_soat_usage_log.py --container fin05-dot-otp-backend-1` để bắt lượt
   tốn tiền mà mất bản ghi (nguồn gốc: OOM từng làm mất 4 lượt trả phí).
3. **Trong lúc đọc kết quả:** dùng kỹ thuật giải mã `checkpoint_blobs` (msgpack,
   `JsonPlusSerializer`) để lấy nguyên văn `AIMessage`/`ToolMessage` thật — KHÔNG tin
   bảng tổng hợp/report markdown một mình nó.
4. **Nếu gặp lại pattern ⑬** (agent nói "đã tra"/nêu số liệu cụ thể mà
   `so_tool_call=0` trong `usage.jsonl` cho lượt đó): **DỪNG NGAY, không chạy tiếp các
   lượt sau, báo PO/Lead trước khi tiếp tục.** Đây sẽ là blocker thật, khác với ⑬ niêm
   hiện tại (đang giữ nguyên, không đi tìm tiếp trừ khi tái diễn).

---

## ③ Kết quả thật — ĐỂ TRỐNG, chỉ điền sau khi chạy

*(không điền gì ở đây cho tới khi có tín hiệu "đi" từ PO và lượt chạy thật đã hoàn tất)*
