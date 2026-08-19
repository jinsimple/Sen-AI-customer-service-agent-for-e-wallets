# Kênh transcript phiên làm lộ khoá — định hạng (A) + chính sách key production (B)

> 19/08/2026. Bảo Mật trả lời Lead. **QUY TẮC CỦA CHÍNH TÀI LIỆU NÀY: không in bất kỳ giá trị bí mật
> nào — chỉ đếm, chỉ hash rút gọn.** Đã tự kiểm độc lập bằng phương pháp AN TOÀN trước khi định hạng,
> không nhận số của Lead làm bằng chứng.

## Kiểm lại độc lập — [ĐO], phương pháp an toàn (đếm/hash, không in giá trị)

```
[ĐO] thư mục ~/.claude/projects/-Users-soidoc-Code-Projects-P-226/    114 MB (khớp Lead)
[ĐO] grep -rlE "JWT_SECRET_KEY=.{32,}"  → 13 tệp                      (Lead: 11 — chênh do khác pattern,
[ĐO] tổng số khớp                       → 414                         không đổi kết luận)
[ĐO] số GIÁ TRỊ KHÁC NHAU (hash SHA-256 rút gọn 10 ký tự, KHÔNG in giá trị) → 7   (KHỚP CHÍNH XÁC Lead)
```

⚠️ **Khai một nguồn nhiễu tôi tự phát hiện, để không ai đọc nhầm số 414 thành mức độ nghiêm trọng:**
số LẦN XUẤT HIỆN bị THỔI PHỒNG bởi chính cuộc trao đổi ĐANG DIỄN RA giữa tôi và Lead về vụ này — mỗi
tin nhắn nhắc tới `JWT_SECRET_KEY=` (kể cả dưới dạng mô tả pattern) đều tự thêm dòng vào transcript
đang ghi. **Số GIÁ TRỊ KHÁC NHAU (7, xác nhận bằng hash) mới là con số đáng tin, không phải số lần
xuất hiện.** Đã kiểm: hash 7 giá trị hôm nay TRÙNG với lúc Lead đo — nghĩa là bản thân việc chúng tôi
đang bàn về vụ này KHÔNG tạo thêm giá trị thật nào mới vào sổ (không ai gõ nguyên văn khoá vào tin
nhắn). Điểm này tự nó là một bằng chứng nhỏ cho thấy kỷ luật "không trích lại giá trị" đang được giữ
đúng trong chính quá trình xử lý sự cố.

## (A) Định hạng kênh — MỨC TRUNG BÌNH cho phạm vi HÔM NAY, có điều kiện đứng vững

**Ba yếu tố kéo XUỐNG:**
1. Khoá đã lộ là `JWT_SECRET_KEY` của **ngăn xếp dev `fin05`** — đang trong quy trình xoay (tôi đã
   xác nhận với Coder, không chặn). Sau xoay, hai giá trị cũ trong sổ **mất khả năng ký token hợp
   lệ** — vẫn là dữ liệu nhạy cảm nằm sai chỗ, nhưng không còn là "chìa khoá đang mở được cửa".
2. **Không phát tán sang phiên khác** (Coder xác nhận, đúng thiết kế transcript per-session của công
   cụ) — thu hẹp về đúng MỘT máy, MỘT người dùng cục bộ.
3. Dữ liệu phía sau JWT là **dữ liệu demo/hạt giống**, không phải dữ liệu khách hàng thật đang phục
   vụ production (theo mọi hồ sơ trước đó của dự án — `app.adaptivealgo.uk` production KHÔNG bị đụng
   tới bởi bất kỳ phiên Claude nào).

**Hai yếu tố kéo LÊN, và đây là phần khiến tôi KHÔNG hạ xuống THẤP:**
1. 🔴 **[PHẢI KIỂM, KHÔNG PHẢI [ĐO] — câu hỏi tôi không tự trả lời được và KHÔNG suy đoán:** transcript
   cục bộ này có bao giờ RỜI KHỎI máy này không (đồng bộ phiên cloud, backup hệ điều hành, telemetry
   công cụ)? Đây LÀ câu hỏi thật, không phải hình thức — hạ tầng harness này CÓ hỗ trợ phiên cloud
   (`ListAgents` liệt kê "Claude sessions running in the cloud"), nên khả năng đồng bộ **không thể
   loại trừ bằng suy luận, phải hỏi/kiểm cấu hình tài khoản**. Chưa trả lời được câu này thì "chỉ nằm
   trên một máy" là một GIẢ ĐỊNH, không phải một sự thật đã đo — đúng Luật R của dự án (*"một phép thử
   phải hỏi thứ ta quan tâm, không hỏi thứ đại diện cho nó"*: "phát tán sang PHIÊN khác" mà Coder đo
   không trả lời được câu "phát tán RA KHỎI MÁY".
2. 🔴 **Đúng như Lead chỉ ra — CƠ CHẾ, không phải một lần cố ý.** Đây là điều làm nó khác các ca Luật S
   trước: **nó tái diễn được VÔ HẠN LẦN, không phụ thuộc ai cẩn thận đến đâu.** Một rủi ro cấu trúc dù
   hạn hẹp hôm nay vẫn phải hạng đủ cao để bắt buộc có chính sách — đây chính là lý do (B) dưới đây
   không được để thành "khuyến nghị", phải thành "quy tắc".

**Kết luận (A): TRUNG BÌNH — không phải P0 khẩn cấp (không kẻ tấn công mới, không dữ liệu khách hàng
thật, khoá đang được xoay), nhưng đủ nghiêm trọng để bắt buộc một chính sách đứng vững, không phải
một ghi chú.** Nếu câu [PHẢI KIỂM] ở trên trả lời "CÓ đồng bộ ra ngoài máy", định hạng này phải nâng
lên CAO ngay lập tức, không cần đo gì thêm.

## (B) CHÍNH SÁCH — bí mật cấp PRODUCTION không bao giờ vào ngữ cảnh của một phiên Claude

*(Lead yêu cầu tôi viết điều khoản, không tự viết. Đây là bản viết — Lead thi hành, PO thật duyệt.)*

### Nguyên tắc

**Giá trị bí mật cấp PRODUCTION — API key nhà cung cấp trả phí (LLM/DashScope/OpenAI), mọi biến
`*_SECRET_KEY`/`*_API_KEY`/mật khẩu DB của môi trường production — KHÔNG BAO GIỜ được một phiên
Claude ĐỌC, GÕ, hay để GIÁ TRỊ THẬT xuất hiện trong bất kỳ lệnh/tệp nào phiên đó chạm tới, dưới BẤT KỲ
hình thức nào — kể cả gián tiếp (sed/echo/cat trên một tệp chứa nó, hay để công cụ TỰ ĐỘNG đọc tệp
đó vào ngữ cảnh, đúng cơ chế vừa gây ra sự cố này).**

### Vì sao PHẢI RỘNG hơn "đừng để nó lên transcript"

Sự cố hôm nay lộ ra một sự thật quan trọng hơn bản thân nó: **thời điểm một giá trị bí mật ĐI VÀO
NGỮ CẢNH của một phiên Claude, nó đã đồng thời đi qua HAI kênh phơi nhiễm, không phải một** —

1. **Lưu trên đĩa** (thứ Lead vừa đo) — transcript cục bộ, có thể mở rộng ra ngoài máy nếu (A)'s câu
   [PHẢI KIỂM] trả lời "có".
2. 🔴 **TRUYỀN QUA MẠNG TỚI NHÀ CUNG CẤP MÔ HÌNH — xảy ra NGAY LẬP TỨC, không phụ thuộc transcript có
   được lưu hay không.** Ngữ cảnh của một phiên (mọi thứ agent "đọc được") chính là nội dung được gửi
   trong MỌI lời gọi API tiếp theo tới nhà cung cấp LLM đang chạy phiên đó — đây không phải một lỗi có
   thể vá, nó là ĐỊNH NGHĨA của cách một agent hoạt động. Tắt/xoá transcript hoàn hảo cũng không đóng
   được kênh này, vì nó đã xảy ra xong tại thời điểm giá trị được ĐỌC, không phải tại thời điểm nó
   được GHI ra đĩa.

⟹ **Kênh (2) nghiêm trọng hơn kênh (1) cho một key production**, vì nó là chuyển giao cho MỘT BÊN THỨ
BA (nhà cung cấp mô hình) **ngay khi đọc**, không cần một lỗi vận hành nào thêm. Đây chính xác là câu
đã dùng cho `app` với dữ liệu khách hàng (Đ.25, hồ sơ chuyển dữ liệu ra nước ngoài) — áp NGUYÊN VĂN
cho bí mật vận hành của chính ta.

### Vế thi hành — ENFORCEMENT bằng SỰ VẮNG MẶT, không phải bằng kỷ luật

Đúng bài học hôm nay: **Coder đã làm đúng mọi thứ theo kỷ luật (một lệnh sed, không echo, không trích
lại) và giá trị vẫn lọt.** ⟹ **quy tắc dựa trên "cẩn thận hơn" KHÔNG đủ cho hạng bí mật này.** Cơ chế
đứng vững duy nhất là bí mật **KHÔNG BAO GIỜ CÓ MẶT** ở nơi một phiên Claude với tới được:

1. **`.env.production` (giá trị thật) KHÔNG BAO GIỜ tồn tại trên bất kỳ máy/thư mục nào một phiên
   Claude Code có quyền đọc.** Repo chỉ chứa `.env.production.example` — TÊN BIẾN + chú thích, ZERO
   giá trị thật, không ngoại lệ.
2. **PO thật (hoặc người có thẩm quyền) điền giá trị TRỰC TIẾP trên máy đích** (SSH vào VPS, hoặc qua
   giao diện quản lý secret của platform — dashboard trình duyệt) — đúng mục *"việc luôn cần xác nhận
   người dùng, không tự động hoá"* đã có sẵn trong playbook đóng gói của dự án (tạo token/secret cấp
   cao). Không có ngoại lệ "chỉ lần này, có giám sát".
3. **Vai trò của agent giới hạn ở ĐƯA HƯỚNG DẪN, không THAO TÁC.** Agent được phép: viết lệnh mẫu
   (`ssh ... 'echo "OPENAI_API_KEY=<dán giá trị của bạn>" >> .env.production'`), giải thích bước, xác
   nhận KẾT QUẢ qua tín hiệu GIÁN TIẾP không cần giá trị (health check trả 200, log không còn dòng lỗi
   xác thực) — KHÔNG được phép là bên chạy lệnh có tham số chứa giá trị thật, KHÔNG được phép đọc lại
   tệp đích để "xác nhận đã ghi đúng" (đọc lại = đưa giá trị vào ngữ cảnh, đúng lỗi hôm nay).
4. **Nếu một tính năng BẮT BUỘC agent phải xác minh giá trị đúng** (hiếm, nhưng có thể xảy ra) — xác
   minh bằng SO SÁNH BĂM do người vận hành tự chạy và dán KẾT QUẢ BĂM (không dán giá trị), đúng kỹ
   thuật `bam_ma_nguon`/băm mẫu prompt dự án đã dùng ở nhiều chỗ khác — không phát minh cơ chế mới.

### Không áp dụng cho (tránh nới quá tay, đúng Luật B "làm tròn một phát biểu lên đúng một nấc")

- Khoá **DEV/demo** (`fin05`/`fin05ttl`/`fin05do`) — vẫn theo kỷ luật hiện có (grep tên biến, không
  grep cả dòng) + xoay khi cần, KHÔNG cần nâng lên mức "không bao giờ chạm" — chi phí/lợi ích khác
  hẳn: khoá dev lộ chỉ mở dữ liệu hạt giống, xoay được ngay, không mất tiền thật.
- Chính sách này áp cho **GIÁ TRỊ**, không áp cho **TÊN BIẾN** — agent vẫn đọc/viết tên biến, cấu
  trúc `.env.production.example`, kiểm tra biến nào THIẾU (không kiểm tra biến đó CHỨA GÌ) như bình
  thường.

## Việc còn lại — không phải quyết định của tôi

- Trả lời câu [PHẢI KIỂM] ở mục (A) (đồng bộ cloud/backup có chạm transcript không) — thuộc PO
  thật/thiết lập tài khoản, không phải điều tôi kiểm được từ trong repo.
- Có purge 7 giá trị cũ khỏi transcript hay không — SAU KHI xoay khoá, giá trị đó đã mất tác dụng ký
  token, mức ưu tiên THẤP, không gấp. Nếu làm, đó là quyết định vận hành của PO thật/Lead (đụng vào
  dữ liệu quản lý bởi chính công cụ Claude Code), không phải việc tôi tự làm.
- Đưa (B) vào brief GĐ3 trước khi Coder chạm bất cứ thứ gì có key product thật — theo đúng đề nghị
  Lead đã nêu, tôi đã viết xong điều khoản, Lead thi hành.

---

## NIÊM 19/08 (chiều) — Lead đo nốt câu [PHẢI KIỂM], quyết KHÔNG purge, chặn một near-miss của QA/QC

**Câu đồng bộ cục bộ: ĐÓNG được một nửa, đúng cách đóng.** [ĐO] Lead: `readlink -f` ra đường thật
(không symlink), `$HOME` không nằm dưới bất kỳ thư mục đồng bộ cloud nào (iCloud/Dropbox/GDrive/
OneDrive), `~/.claude/settings.json` không có khoá telemetry/sync/upload. iCloud Drive CÓ bật trên
máy nhưng phạm vi của nó (`~/Library/Mobile Documents` + Desktop/Documents nếu bật) **không phủ**
`~/.claude`. **Nửa còn lại — công cụ có tự tải transcript lên phía nhà cung cấp hay không — Lead
ĐÚNG khi từ chối trả lời**: đó là hành vi phía nhà cung cấp, không quan sát được từ hệ thống tệp,
mọi câu trả lời sẽ là suy đoán đội lốt phép đo — đúng thứ cả ngày hôm nay đã dạy phải tránh. Lead đã
chuyển câu này lên PO thật thay vì đoán. **Đúng cách xử lý một câu không đo được: khoanh vùng rồi
dừng, không lấp bằng suy luận** (cùng nguyên tắc tôi đã áp cho câu hợp đồng ToS Alibaba 17/08).

**Đồng ý KHÔNG purge 7 giá trị — ba lý do của Lead đủ, không cần thêm.** ① không đóng được gì đáng
kể (một giá trị đang sống) ② nhắm sai kênh (kênh (1) là kênh NHẸ hơn trong hai kênh tôi nêu — purge
không chạm được kênh (2)) ③ tự tạo rủi ro mới bằng cách sửa chính vật đang ghi lại lịch sử — đúng
tinh thần "đọc trước, dọn sau" và "niêm tại chỗ, đừng sửa thân" đã dùng nhiều lần trong dự án, áp
đúng cho một loại vật mới (transcript của chính harness, không phải file trong repo). **Một điều
kiện nhỏ, không đổi kết luận:** một khi kênh gốc đã đóng bằng (B) (agent hết đường chạm key
production, và kỷ luật dev-key cũ vẫn giữ), một đợt dọn RẤT LÂU về sau — khi không còn giá trị nào
trong 7 giá trị đó còn "sống" — sẽ là thao tác rủi ro THẤP hơn hẳn (không còn bí mật hoạt động nào
để lỡ tay làm hỏng theo hướng nguy hiểm). Không phải việc hôm nay.

**QA/QC near-miss — Lead bắt đúng, và đáng thành một nguyên tắc đứng, không chỉ một lần sửa.**
Dùng CHÍNH khoá thật làm vật thử "khoá không rời máy" là tự tạo ra đúng sự kiện đang được đo — kiểm
tra ăn chính đối tượng nó bảo vệ. Đổi sang sentinel không chỉ an toàn hơn, còn **mạnh hơn về mặt
kiểm được**: sentinel `grep` được thoải mái để xác nhận (có hay không), khoá thật thì không ai dám
chạy đúng lệnh cần chạy để xác nhận — nghịch lý tự trói tay chính phép kiểm. **Nguyên tắc chung cho
mọi ca tương lai cùng hình dạng:** muốn CHỨNG MINH một bí mật không rò, đừng bao giờ dùng CHÍNH bí
mật đó làm dữ liệu thử — dùng một giá trị vô hại nhưng ĐỘC NHẤT (sentinel) đóng vai trò của nó.
