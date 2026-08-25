# Sổ khoảng trống — soát xét theo chuẩn ví điện tử EU/US

> **Vì sao tệp này tồn tại:** bản soát xét này được làm ngày 24–25/08 và **chỉ nằm trong
> scratchpad của một phiên**. Thư mục scratchpad **theo phiên, tự mất khi phiên đóng, và không
> ai được báo**. Land vào `docs/` là để nó không phải được phát hiện lại từ đầu.
>
> 🔴 **Đây KHÔNG phải một kế hoạch được duyệt.** Nó là **danh sách khoảng trống + khuyến nghị**.
> Ba mục đánh dấu **CHẶN Ở PO THẬT** là câu nghiệp vụ, đội **không được tự chọn**.
>
> Phạm vi đã chốt với PO: **"đúng biên giới hệ thống"** — soát phần FIN-05 thật sự kiểm soát,
> không soát cả ngăn xếp ví. Người soát: phiên PO đóng vai reviewer fintech độc lập.

---

## Cách đọc mức

| mức | nghĩa |
|---|---|
| **P1** | thiếu một **kiểm soát nền** mà mọi khung quản trị đều đòi · hoặc một câu **sai** đang lưu hành ra ngoài |
| **P2** | khoảng trống thật, có đường vòng, **không xấu đi theo ngày** |
| **P3** | nên có, rẻ, chưa chặn ai |

⚠️ **Mức nói về KHOẢNG TRỐNG, không nói về chất lượng đội.** Nhiều mục P1 dưới đây là thứ một
đội 1 người **chưa tới lượt làm**, không phải thứ làm sai.

---

## Nhóm A — Dữ liệu & quyền riêng tư

| mức | khoảng trống | bằng chứng |
|---|---|---|
| **P1** | **Không có lịch lưu trữ, không có cơ chế xoá.** Transcript · checkpoint · `investigation_logs` tích luỹ **vĩnh viễn** | `[ĐO]` `grep -riE "retention\|erasure\|purge\|thoi_han_luu" src/` → chỉ trúng TTL của refresh-token và rate-limit. **Không có gì** cho dữ liệu khiếu nại. GDPR §5(1)(e) + §17 · NĐ 13 §16 |
| **P1** | **Chuỗi audit không có bằng chứng chống sửa.** `US-017` hứa *"log không sửa/xoá được bởi người dùng thường"* — hứa ở **tầng ứng dụng** | `[ĐO]` không trigger, không append-only, không hash-chain trên `InvestigationLog`/`Resolution` *(`src/db/models.py:336,351`)*. 🔴 Trong tranh chấp, đây là **mắt xích yếu của toàn bộ hồ sơ** |
| **P2** | **Số thẻ không có bộ nhận diện riêng.** Khách gõ số thẻ vào chat là kịch bản có thật | `[ĐO]` `src/observability/pii.py` nạp catalog Presidio `"vi"` — **không có `CreditCardRecognizer`**. Số thẻ chỉ được che **tình cờ** bởi luật `\d{9,19}` score 0.6. ⚠️ Cần **một ca đối chứng** trước khi kết luận là lỗ |
| **P2** | `investigation_logs.tool_input_json` **plaintext** chứa mã GD · SĐT · số tiền; live-chat `record_message` lưu **nguyên văn** | **Đội đã tự biết**, đã phân xử `ADR-034`, chưa vá. **Món nợ đã ghi sổ, không phải phát hiện mới** |

---

## Nhóm B — Xử lý khiếu nại *(khiếm khuyết nghiệp vụ nặng nhất)*

🔴 **CHẶN Ở PO THẬT — đây là câu nghiệp vụ, đội không được tự chọn ngưỡng.**

Vé được cấp một hạn xử lý **tại lúc tiếp nhận**, rồi **giữ nguyên hạn ấy** kể cả sau khi phạm vi
thật đã rõ *(nội bộ ví ↔ liên ngân hàng ↔ đối tác)* — trong khi khung pháp lý cho **mỗi phạm vi
một đồng hồ khác nhau** *(Reg E 10 ngày làm việc · PSD2/EBA 15 ngày)*.

**Khuyến nghị:** **hạn tính lại tại thời điểm phạm vi được xác định**, lấy mốc theo phạm vi thật.
**Ngưỡng cụ thể là quyết định của PO**, không phải của đội.

---

## Nhóm C — Sức bền vận hành

| mức | khoảng trống | bằng chứng |
|---|---|---|
| **P1** | **`FIELD_ENCRYPTION_KEY` không xoay được.** `STATE.md §1` ghi thẳng: xoay = **mất vĩnh viễn** dữ liệu đã mã hoá | `[ĐO]` không có script mã hoá lại trong `scripts/`. Xoay khoá là kiểm soát nền ở mọi khung *(ISO 27001 A.10 · PCI 3.6.4)*. 🔴 **Hệ quả thật: khoá lộ ⟹ không có đường phục hồi nào** — chỉ còn chọn giữa mất dữ liệu và chạy tiếp với khoá đã lộ |
| **P1** | **Sao lưu chưa từng được diễn tập phục hồi** | `[ĐO]` `docs/DEPLOY.md:192` có **đúng một dòng** `pg_dump` thủ công kèm chữ *"nên chạy định kỳ"*. Không tự động, không RTO/RPO, **không lần khôi phục nào**. 🔴 **Một bản sao lưu chưa phục hồi thử là một GIẢ THUYẾT, không phải một bản sao lưu** |
| **P2** | **Không có sổ đăng ký nhà cung cấp ICT bên thứ ba.** DashScope *(Alibaba, Singapore)* + OpenAI *(embedding)* đang đỡ một chức năng nghiệp vụ | Hình dạng **DORA §28**: sổ đăng ký + đánh giá tập trung rủi ro + kế hoạch thoát. ✅ **Điểm sáng:** bể 4 model tự xoay **đã là** cơ chế thoát trên thực tế — thiếu mỗi việc **khai nó ra thành văn bản**. Rẻ |
| **P2** | **Redis là điểm chết đơn** — tắt Redis ⟹ `/agent/chat` sập hẳn | Đội tự phát hiện, vá ở `1a33239`, **chưa live-fire xác nhận**. Theo **Luật A** của chính dự án: chưa có ca đối chứng thì **chưa biết cổng có kêu** |
| **P2** | **Không có sổ tay ứng cứu sự cố**, không thang mức độ, không đường báo cáo | Đội xử lý sự cố **rất tốt trên thực tế** *(xem sổ luật)* — nhưng tri thức nằm trong **nhật ký**, không nằm trong **một quy trình người trực đọc lúc 2 giờ sáng** |

---

## Nhóm D — Quản trị AI & phát ngôn ra ngoài

| mức | khoảng trống | bằng chứng |
|---|---|---|
| **P1** | 🔴 **`PRD §15.1` khẳng định một điều mà kiến trúc đang phản bác.** Nguyên văn: *"Dữ liệu giao dịch không rời khỏi hạ tầng do ví kiểm soát"* | `[ĐO]` chat đi **DashScope Singapore**, embedding đi **OpenAI**. Câu này đang là **định vị cạnh tranh trong PRD** — thứ sẽ được **đọc to trong phòng có đối tác**. ⚠️ **KHÔNG phải đề nghị mở lại quyết định Đ.25** *(đã chốt)* — đây là **một câu sai trong tài liệu bán hàng**. **Sửa câu, giữ quyết định** |
| **P2** | **Điểm 87,7% đã chết mà vẫn lưu hành** | Chính đội đã niêm: đo 16/08, **trước** khi đổi model và **trước** 4 vùng thay đổi; loại trục Trải nghiệm 15 điểm khỏi mẫu số; trọng số chưa hiệu chuẩn. **Hai đường ra, chọn một:** đo lại trên bản đang chạy, **hoặc** rút khỏi mọi tài liệu đối ngoại. 🔴 Đường thứ ba — *để nguyên kèm caveat* — là đường đội **đang đi**, và **Luật B** nói rõ nó thua: **người đọc giữ con số, không giữ lời dặn** |
| **P2** | **Không có model card / system card** | ✅ Nguyên liệu **đã có sẵn và tốt bất thường** — mục *"Điều chưa chứng minh được"* chính là phần giới hạn mà một system card đòi. Việc còn lại là **đóng gói cho người ngoài đọc được** |
| **P3** | Nghĩa vụ minh bạch *"bạn đang nói chuyện với AI"* — **EU AI Act §50** | Chưa kiểm giao diện. Rẻ, **bắt buộc ở EU**. Giao QA/QC đo trên UI thật |
| **P3** | Trục **Trải nghiệm** bị loại khỏi điểm ⟹ **không có số nào** nói khách có dễ chịu không | **CFPB (US)** nêu **đích danh** chatbot làm người tiêu dùng bế tắc là một dạng **tổn hại**. Với ví điện tử, *"an toàn tuyệt đối nhưng cộc lốc"* là một **sản phẩm hỏng** — chỉ hỏng ở **trục không ai đo** |

---

## Năm luồng khắc phục *(khuyến nghị, chưa duyệt)*

| # | luồng | ai | chặn ở đâu |
|---|---|---|---|
| **P1** | **1 — Đồng hồ khiếu nại chạy đúng.** Vé không còn giữ một hạn đã cấp qua thời điểm phạm vi đã rõ | — | 🔴 **PO THẬT.** Câu nghiệp vụ |
| **P1** | **2 — Bằng chứng chống sửa được.** Hash-chain trên `investigation_logs` + `resolutions` *(mỗi bản ghi mang băm bản trước)*, khai cách kiểm | Bảo mật đặc tả · Coder thi hành · QA/QC dựng **ca đối chứng** | ⚠️ Đụng `models.py` + migration, **không** đụng `contracts/`. Nếu hoá ra **có** đụng ⟹ **dừng, đi đủ §3**, chờ PO |
| **P1** | **3 — Dữ liệu có vòng đời, khoá có đường xoay.** Hai thứ mà **mọi ngày trôi qua đều làm đắt thêm** | Bảo mật đặc tả chính sách · Coder viết script · QA/QC đo | 🔴 **PO THẬT** cho phần *giữ bao lâu*; cơ chế là việc đội |
| **P2** | **4 — Phát ngôn ra ngoài phải đúng.** Sửa `PRD §15.1` · quyết định đo lại hay rút 87,7% · đóng gói system card | Reviewer quét · Lead trình PO duyệt **từng câu sửa** | ⚠️ Rỗng phải là **kết quả quét**, không phải **kết luận** |
| **P2** | **5 — Đóng các cổng đã biết.** `tool_input_json` plaintext · live-chat PII | Bảo mật dẫn · Coder vá · QA/QC gỡ nhãn | Xếp **sau** bốn luồng trên vì đã khai, đã phân xử, **không xấu đi theo ngày** |

---

## Ba câu chỉ PO thật trả lời được

1. **Đồng hồ khiếu nại** — hạn có tính lại khi phạm vi được xác định không, và mốc lấy theo đâu?
2. ~~**Lịch lưu trữ** — transcript / checkpoint / `investigation_logs` **giữ bao lâu**?~~
   ✅ **ĐÃ TRA LUẬT 25/08 — câu hỏi này ĐẶT SAI, xem §"Sàn 5 năm" ngay dưới.**
3. **Điểm 87,7%** — **đo lại** trên bản đang chạy, hay **rút** khỏi mọi tài liệu đối ngoại?
   *(Để nguyên kèm caveat là đường đang đi, và Luật B nói nó thua.)*

---

## 🔴 Sàn 5 năm — tra luật 25/08, PO thật yêu cầu

**Câu *"giữ bao lâu"* đặt SAI.** Nó nghe như một quyết định kinh doanh; thật ra **luật đã chốt sàn.**

### Sàn cứng — không thương lượng được

**Luật Phòng, chống rửa tiền 2022 · Điều 38.** Tổ chức trung gian thanh toán *(ví điện tử là một)*
là **"đối tượng báo cáo"**, buộc phải lưu:
- thông tin, hồ sơ **nhận biết khách hàng**
- kết quả **phân tích, đánh giá** khách hàng và giao dịch phải báo cáo
- hồ sơ, tài liệu **liên quan tới khách hàng và giao dịch phải báo cáo**

> **05 năm**, kể từ ngày **kết thúc giao dịch** · ngày **đóng tài khoản** · hoặc ngày **báo cáo**.

⟹ 🔴 **Hồ sơ khiếu nại của FIN-05 rơi thẳng vào nhóm thứ ba** ⟹ **KHÔNG được xoá trước 5 năm, kể
cả khi khách yêu cầu.**

### Và nó KHÔNG mâu thuẫn với NĐ 13/2023

**NĐ 13/2023 · Điều 16 khoản 2** liệt kê các trường hợp **không phải xoá** dù chủ thể yêu cầu —
mục **đầu tiên** là *"pháp luật quy định không cho phép xóa dữ liệu"*.

⟹ Nghĩa vụ 5 năm theo Luật PCRT **là căn cứ hợp pháp để từ chối yêu cầu xoá**. Hai luật **không
đánh nhau**: **PCRT đặt SÀN, PDPA đặt TRẦN.**

### Khung đúng để quyết

| | |
|---|---|
| **Sàn** | **5 năm** — luật định |
| **Trần** | *"chỉ giữ khi còn cần cho mục đích đã thông báo"* — quá 5 năm mà giữ tiếp thì **phải giải thích được vì sao** |
| 🔴 **Câu THẬT cần PO quyết** | **sau 5 năm thì làm gì** — xoá hẳn · ẩn danh hoá · hay giữ tiếp có lý do |

**Khuyến nghị:** giữ đúng **5 năm rồi xoá tự động**; riêng **nội dung chat** thì **ẩn danh hoá sớm
hơn** — luật đòi giữ **hồ sơ giao dịch và định danh**, **không** đòi giữ **nguyên văn hội thoại**.

### 🔴 Nhưng khoảng trống thật KHÔNG phải con số

Hệ thống hiện **không có cơ chế xoá nào cả** — transcript · checkpoint · `investigation_logs` tích
luỹ **vĩnh viễn**. ⟹ Vấn đề không phải *"5 năm hay 3 năm"* mà là:

> **Không có đường nào để xoá bất cứ thứ gì — kể cả khi luật CHO PHÉP, kể cả khi luật BẮT BUỘC.**

⚠️ **Giới hạn của phần tra cứu này:** đọc từ nguồn công khai, **người tra không có chuyên môn pháp
lý**. Con số **5 năm** và cơ chế miễn-trừ-xoá thì rõ ràng trong văn bản; nhưng **"hồ sơ khiếu nại
có thuộc Điều 38 hay không"** là **một bước DIỄN GIẢI**. 🔴 **Trước production phải có người có
chuyên môn pháp lý xác nhận** — đừng chỉ dựa vào tệp này.

**Nguồn:** Luật 14/2022/QH15 Điều 38 · NĐ 13/2023 Điều 16.2 · NĐ 52/2024.

---

## Truy vết

| | |
|---|---|
| Soát | 24–25/08/2026, phiên PO đóng vai reviewer fintech độc lập |
| Phạm vi | **"đúng biên giới hệ thống"** — PO chốt qua `AskUserQuestion` |
| Nguồn gốc | scratchpad phiên `49f23ea3` — **sẽ mất khi phiên đóng**, đó là lý do land |
| Trạng thái | **CHƯA DUYỆT.** Không giao việc cho ai từ tệp này mà chưa qua PO |
| Khung tham chiếu | GDPR · NĐ 13/2023 · Reg E · PSD2/EBA · DORA §28 · EU AI Act §50 · ISO 27001 A.10 · PCI 3.6.4 · CFPB |
