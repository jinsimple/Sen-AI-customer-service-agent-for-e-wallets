# Trạng thái hiện tại

## 🔴 CHỐT 17/08 — BỘ SỐ THỜI GIAN "hai đồng hồ không biết nhau" + phạm vi A2 ở đường hỏng

Coder chẩn: `OPENAI_TIMEOUT=20` × `MAX_RETRIES=1` ⟹ **một** lời gọi hỏng ăn 40s trên trần lượt
45s, trong khi lượt điển hình cần 2–5 lời gọi (lượt 4 đo thật 30,7s = 68% ngân sách lúc BÌNH
THƯỜNG). Tổng quát hoá đúng của F-33b: **không cần 429 — mọi chậm trễ đủ lớn đều đội lốt
timeout, và timeout thì đẻ vé.**

**PO-agent tự đọc config xác nhận 3 số, và tìm ra ĐỒNG HỒ THỨ TƯ coder chưa thấy:**
`api/main.py:384` `ttl_seconds=90` là **HẰNG SỐ CHẾT**; quan hệ "2× trần lượt" chỉ sống trong
CHÚ THÍCH dòng 379. ⟹ **(b) nâng trần lượt lên 90s TỰ SÁT**: trần = TTL ⟹ lưới thu hồi cướp slot
của lượt đang chạy hợp lệ — đúng thứ chính chú thích đó viết ra để tránh, và nổ ở chỗ đắt nhất
(buổi 150 người, limiter là thứ duy nhất giữ dưới ngưỡng bão 429). Cùng lớp với
`docs/2026-08-17-ra-soat-khai-bao-vs-ep-buoc.md`: **khai quan hệ trong chú thích, đọc thành
ràng buộc — không có ràng buộc nào cả.**

| ph.án | quyết | vì sao |
|---|---|---|
| (a) hạ trần lời gọi 12s | **NHẬN HƯỚNG, HOÃN SỐ** | 11,6s là CỰC ĐẠI QUAN SÁT — Luật F: mẫu số đâu? Đặt trần ở max+3% = hiệu chuẩn van trên mẫu nhỏ hơn nhiều lần quần thể nó cai quản. Hỏi p50/p90/p99 (0 token, số đã trên đĩa) |
| (b) nâng trần lượt 90s | **BÁC** | đụng TTL 90 hardcode (trên) |
| (c) `MAX_RETRIES=0` | **BÁC** | coder viết "để tầng lượt quyết định" — nhưng **tầng lượt không thử lại, nó ĐẺ VÉ**. (c) không dời quyền quyết định lên trên, nó XOÁ lớp tự lành duy nhất. Đổi "tự lành im lặng" lấy "vé" là đi NGƯỢC CHIỀU A2 |

**Chữa đúng bệnh, không chỉnh số (làm ngay, không chờ mẫu số):** ① rút `ttl_seconds` khỏi
hardcode, dẫn xuất từ trần lượt — quan hệ phải sống trong CODE ② **kiểm mạch lạc lúc khởi động,
fail-fast**: `TIMEOUT × (RETRIES+1) ≤ TURN × k` ⟹ bộ config vô lý KHÔNG deploy được, thay vì lộ
qua một lượt hỏng của khách. Chọn số nào cũng chỉ chữa lần này.

**🔴 CÂU HỎI HIẾN PHÁP suýt lọt — A2 vs đường hỏng.** Nhánh timeout TẠO VÉ không hỏi ai (thiết
kế ĐÚNG: khách vừa được đọc mã vé ⟹ vé phải có thật, ràng buộc cứng #3). Nhưng A2 chốt sáng nay
là "chờ khách đồng ý mới mở ticket". **Phán quyết (đề xuất lên PO thật, đội thi hành ngay vì
tester đang viết ca):**

> A2 chi phối đường agent **CHỦ Ý** mở vé thay khách. A2 **KHÔNG** chi phối đường bàn giao khi
> **hệ thống hỏng** — đồng ý giả định một hội thoại còn hoạt động; lúc timeout agent không hỏi
> được ai, và bỏ khách tay trắng tệ hơn một cái vé họ không xin.
> **ĐIỀU KIỆN CỨNG:** vé từ đường hỏng phải PHÂN BIỆT ĐƯỢC BẰNG MÁY với vé từ đường đồng ý —
> mốc thuộc **SỰ KIỆN** không thuộc **VÉ** (tinh thần ADR-029). Bằng chứng cần thiết đã có sẵn
> trong tay tester: `Δcomplaints=+1` với `total_tokens=0` ⟹ **hôm nay đếm vé không tách được hai
> loại**, nên mọi số A2 dựa trên đếm vé đều bị vé-fallback pha loãng.

Không chốt trước khi tester viết xong ⟹ bộ ca **đóng băng một hành vi chưa ai xét** — đúng cái
§4 dựng tường đọc để tránh.

**Trình tự (giữ nguyên đề nghị coder):** quyết trọn → đổi MỘT lần → đo lại nền → rồi mới A2.
Nền A2 đã đo (13,9K + 14K) là **chi phí chìm**; nuốt bây giờ rẻ hơn nuốt sau khi A2 xong. Tester:
viết ca cứ viết, **không chạy lượt tính tiền nào cho A2 tới khi có nền mới.**

**Ghi nhận nếp đúng:** coder KHÔNG kết luận "nhà cung cấp chậm" từ "3/3 gần nhất" của tester mà
chỉ ra **mẫu số khác nhau** (3 lượt rải trên 3 ngăn xếp; log `fin05` chỉ có ×1) — Luật F dùng
đúng lúc, ngay trên báo cáo của đồng đội.

### ⛔ KẾT CỤC — (a)/(b)/(c) ĐÓNG HẾT. Trần là câu trả lời SAI cho câu hỏi này.

Bóc log lượt timeout thật (`USR-0001:1786976758`, `fin05` 14:25:58, không lượt nào chạy song song):

```
+8,2 · +13,0 · +17,3 · +24,0 · +28,7 · +32,9 · +36,5s   → 7 lời gọi, TẤT CẢ 200 OK
+46,2s   agent_turn_timeout
+47,3s   lời gọi thứ 8 trả 200 OK — SAU khi ta đã bỏ
```

**8 lời gọi model, 0 tool call.** Mọi lời gọi đều NHANH (4–10s, khớp p50–p95). Lượt chết vì
**QUÁ NHIỀU lời gọi**, không vì lời gọi nào chậm. ⟹ trần mỗi-lời-gọi `20s` **chưa từng liên quan
tới ca này**; nâng trần lượt lên 60s chỉ cho ra lượt **10 lời gọi thay vì 8** — đắt hơn, vẫn hỏng.
**Trần quyết định nó CHẾT LÚC NÀO, không quyết định nó CÓ XẢY RA KHÔNG.**

Hai bản vá đã land GIỮ NGUYÊN (đúng trong phạm vi của chúng): `ttl_seconds` dẫn xuất từ trần lượt
(`59bf4d7`) + cổng mạch lạc fail-fast lúc import, có ca đối chứng. **Cổng ② tự khai giới hạn:** nó
kiểm `TIMEOUT × (RETRIES+1) ≤ TURN` nhưng **KHÔNG nhìn SỐ LẦN GỌI** — mà `8 × 5,8s = 46s` mới là
đại lượng giết lượt này. Cổng xanh, và xanh không có nghĩa ở lớp này.
**Việc thật chuyển sang: VÌ SAO 8 lời gọi model mà 0 tool — hành vi, thuộc F-31/32.**
**Dấu thời gian (UTC):** `13:59:29` recreate `fin05` BẬT cờ · `14:01:14` commit A1 `ccbf09c` ·
`14:25:58` lượt timeout ⟹ **SAU, 26 phút.** Nhưng `ccbf09c` **không đổi một dòng mã** (chỉ
`docker-compose.yml`, lật mặc định một biến env); mã phân luồng đã trong ảnh từ `1e42146`/`8060261`
và chạy với cờ TẮT suốt. Sổ usage: `duong='day_du'` · `so_tool_schema_gui=5` ⟹ nhánh phân luồng
chạy, trả `day_du`, rơi về đúng đường cũ; nhánh `day_du` **giống hệt trước T1**.
⚠️ **Nhưng đó là lập luận CẤU TRÚC, không phải phép đo** — coder tự chặn, đúng, vì hôm nay đã sai
2 lần vì đúng loại lập luận ấy. **Một điểm không phân biệt được "sau" với "vì".**
🔴 **PO-agent CHƯA DUYỆT phép thử tốn tiền** (chạy lại câu đó với cờ TẮT ≈ 50–70K). Có phép thử
**0 token phân định TRƯỚC**, từ chính tiên đoán của lập luận cấu trúc: nếu nhánh `day_du` giống hệt
trước T1 thì vòng lặp 8-gọi-0-tool **phải TỪNG xảy ra trước khi T1 tồn tại**. ⟹ **quét log `httpx`
cả 3 ngăn xếp: có lượt nào TRƯỚC `1e42146` với ≥5 POST `/chat/completions` liên tiếp không xen
ToolResult không?** CÓ ⟹ loại phân luồng **bằng QUAN SÁT**, đóng nhánh, 0 đồng. KHÔNG ⟹ lúc đó mới
đáng xin PO thật ngân sách, với câu hỏi đã sắc.
⚠️ Phép quét này **cũng có bộ lọc phải khai TRƯỚC**: chỉ thấy được khoảng log còn giữ. Log đã xoay
vòng ⟹ kết quả "KHÔNG" **không có sức phân biệt** (Luật 17). Kiểm tầm với của log TRƯỚC khi đọc.
### ✅ PHÂN LUỒNG LOẠI BẰNG QUAN SÁT — nhánh đóng, 0 ĐỒNG

Coder kiểm tầm với TRƯỚC (Luật 17): `docker logs` chỉ có từ `13:59` mà T1 land `09:47` ⟹ quét ra
"KHÔNG" **không có sức phân biệt** ⟹ **không chạy phép quét**. Tìm nguồn thứ hai sống qua recreate:
**sổ usage**, 62 dòng từ `09:28:18`, có ~19 phút TRƯỚC T1.

```
so_luot_goi_model:  0 gọi ×22 · 1 ×6 · 2 ×29 · 3 ×4 · 5 ×1
lượt ≥4 gọi: ĐÚNG MỘT →  09:38:18 · 5 gọi · duong=None   ⟵ TRƯỚC T1 chín phút
```

⟹ **Vòng lặp nhiều bước xảy ra trước khi phân luồng tồn tại. Phân luồng vô can, loại bằng QUAN
SÁT chứ không bằng cấu trúc mã. Không xin ngân sách phép thử tốn tiền.**
Hạng coder tự khai, chép nguyên (cái thứ ba dễ bị người sau lặng lẽ nâng hạng nhất):
`phân luồng vô can` = quan sát · `vòng lặp dài là bệnh CÓ TỪ TRƯỚC` = quan sát ·
**`tần suất của nó` = KHÔNG BIẾT, và sổ KHÔNG ĐO ĐƯỢC.**

> 🔴 **BỘ LỌC VÔ HÌNH LẦN THỨ NĂM — lần này NẰM TRONG CHÍNH DỤNG CỤ ĐO.** Lượt hỏng ghi
> `so_luot_goi_model = 0` ⟹ trong 22 dòng ghi `0` lẫn **hai thứ khác hẳn nhau**: *"đường nhẹ, đúng
> là 0"* và *"lượt hỏng, không đọc được"*. **Sổ dựng ra để đếm lời gọi, và nó lọc mất đúng loại
> lượt ta đang đi tìm — rồi báo bằng một giá trị trông hợp lệ.** ⟹ "chỉ 1 lượt ≥4 gọi" là câu về
> **lượt THÀNH CÔNG**, không phải về hệ thống.

### ⬆️ `0 → None` LÊN HẠNG: từ "đáng làm" thành **CHẶN BUỔI TEST 150 NGƯỜI**

PO-agent **DUYỆT** đề nghị của tester: buổi 150 người ghi `duong · total_tokens · mốc thời gian`
cho **MỌI lượt** (+ PO-agent thêm `ly_do_fallback · so_luot_goi_model`). Lý do tester nêu và nó
đúng: **lần đầu và có thể là lần DUY NHẤT có lưu lượng thật — không có buổi thứ hai để sửa.** Có
đủ trường thì sau buổi test trả lời được MỘT LÚC: tỉ lệ lượt đơn · nhịp gõ thật · token/lượt thật ·
tỉ lệ lượt hỏng · trần nào chạm trước.
📌 **PO-agent RÚT câu "`0 → None` phải land TRƯỚC buổi test"** — tester đọc thẳng 62 dòng
`usage.jsonl`: 22 dòng `goi=0` tách **sạch 22/22, bất đồng 0 lần** bằng `duong` + `ly_do_fallback`
(`nhe`·không-fallback·token 0 → 13 · `day_du`·CÓ-fallback·token 0 → 9; và `nhe ⟺ goi==0` đúng
tuyệt đối trên mọi dòng không fallback). ⟹ **vệ sinh, KHÔNG phải điều kiện chặn**: buổi test chạy
được với vật hôm nay miễn script đọc **bộ ba** thay vì đọc `goi` một mình. **PO-agent đã tự tạo
một phụ thuộc lịch không cần thiết vào việc code.**
⚠️ **Hạng — hở duy nhất còn lại:** đồng thuận 100% trên n=22 là thứ ta kỳ vọng thấy **cả khi hai
trường do CÙNG một dòng mã đặt ra**; lúc ấy chúng là **một nguồn viết hai lần**, và **Luật D không
được thoả**. ⟹ câu cho coder: **`duong` và `ly_do_fallback` ghi bởi HAI đoạn mã hay một chỗ?** Hai
chỗ ⟹ tách được **theo cấu trúc**. Một chỗ ⟹ chỉ tách được **trên dữ liệu đang có**.

**✅ DUYỆT land `0 → None` NGAY, riêng** (lý do LỊCH của coder, độc lập với lý do vừa rút): đóng
băng `src/` đang bảo vệ **một phép đo CHƯA BẮT ĐẦU** — nền A2 của coder (13,9K) không tái hiện được
finding, nền của tester (14K) là lượt timeout không tới model, ca A/B/C đang viết lại, ngăn xếp
chưa chốt. A2 **không có nền hợp lệ nào để mất**.
> **`0` có BA nghĩa, không phải hai** (coder): ① đường nhẹ = ĐÚNG 0 ② 429/lỗi NCC = 0 lời gọi trả
> về, nhưng **token có bị tính không: KHÔNG BIẾT** ③ timeout/recursion = lời gọi ĐÃ CHẠY (8, log
> httpx chứng minh), đếm được KHÔNG · token KHÔNG BIẾT. ⟹ `so_luot_goi_model`: `0·0·None` ·
> `*_tokens`: `0·None·None`. **`None` ở đây nghĩa "KHÔNG ĐỌC ĐƯỢC", không phải "KHÔNG CÓ"** — vá
> một giá trị hai nghĩa bằng một giá trị hai nghĩa khác thì chỉ dời chỗ bệnh.
> 🔴 **Chưa chốt:** trường `so_luot_goi_model` đếm lời gọi **ĐÃ PHÁT** hay **ĐÃ TRẢ VỀ**? Tên nó
> không nói. Đếm-đã-phát ⟹ `0` ở ② **sai y hệt** `0` ở ③, và ③ ghi được **8** thật thay vì `None`.
> **Định nghĩa trường TRƯỚC, chọn null SAU** — một trường không khai nó đếm gì thì mọi giá trị của
> nó đều mơ hồ, kể cả giá trị đúng.
> ⚠️ **"KHAI ≠ CHẠY" ĐỌC NGƯỢC:** `59bf4d7` đang ở git mà KHÔNG ở container — git đi trước
> container **4 tiếng**. Cú dựng lại **trả hết nợ cùng lúc**. ⟹ **liệt kê MỌI commit chạm `src/`
> giữa ảnh đang chạy và HEAD trước khi build**, rồi ba phép kiểm sau khi dựng. Ba lần
> `git ≠ container` hôm nay đều theo chiều kia; chiều này chưa ai vấp nên chưa ai canh.

**BỐN RỔ bắt buộc cho script tổng hợp buổi test** (tester, duyệt): `nhe` → lượt đơn thật ·
`day_du`+fallback=None → chạy xong · `day_du`+fallback CÓ → HỎNG · **KHÔNG có khoá `duong` → 🔴
ĐIỀU TRA, không gộp vào đâu**. Rổ 4 khác 0 = dừng trước khi công bố tỉ lệ nào. Bẫy cụ thể: viết
`duong != 'day_du'` thì lượt 422/500 thành "lượt đơn" ⟹ **thổi tỉ lệ tiết kiệm đúng hướng ta muốn
nghe** — confound hướng-có-lợi.
**BA RỔ cho token** (coder→tester): `đo được` · `không đọc được` · `đúng 0`. **KHÔNG `sum()` với
`or 0`** — `or 0` biến *"không biết"* thành *"không tốn"*: cùng lời nói dối, dời sang phía đo.

### 🧭 NGƯỠNG CỨU BUỔI TEST — và biến quyết định KHÔNG phải T1

Tester **từ chối** trả lời "tỉ lệ lượt đơn là bao nhiêu" vì **cả hai nguồn đều sai dân số**:
`messages` là **script sinh** (p10=p50=3s ⟹ 19,8 lượt/ph/người, và script **không bao giờ gõ
"alo"** ⟹ sàn giả ~0%) · `bo_ca_luot_don.json` 9/20=45% là **bộ ca dò biên soạn tay**, đọc thành
tỉ lệ lưu lượng = dùng mẫu làm-giàu-ca-hiểm làm mẫu đại diện (ngược chiều lỗi `golden_set thiếu
lượt đơn` sáng nay). ⟹ **chỉ đo được ở buổi test người thật.** Rồi **đảo câu hỏi** thành điều kiện:

```
150 × 0,50 lượt/ph → TPM 106% → cần ≥  6,1% lượt đơn
150 × 0,75         →      160% → cần ≥ 37,4%
150 × 1,00         →      213% → cần ≥ 53,0%
100 × 0,50         →       71% → không cần gì ✅
```

🔴 **BIẾN QUYẾT ĐỊNH LÀ NHỊP GÕ, KHÔNG PHẢI T1** — thứ ta điều khiển bằng **kịch bản chạy**, không
phải bằng code: nhịp ≤0,5 lượt/ph/người thì T1 chỉ cần **6,1%** (gần như chắc đạt); nhịp 1,0 thì
**53%** là bất khả, **không bản vá nào cứu kịp**.
**Dạng phát biểu ĐÚNG cho ẩn số không đo được trước: ĐIỀU KIỆN, không phải con số** — và nó tự
kiểm trong 10 phút đầu buổi test bằng dấu `duong` đã ship.
⚠️ Mọi `% cần` ở trên là **CẬN DƯỚI** (thiên lệch sống sót: `14.198` là trung bình lượt THÀNH
CÔNG). 5% lượt hỏng ở 60K ⟹ token/lượt ~16.500, trần tụt ~61 lượt/ph, **106% → ~123%**. Tester
**không sửa số** — *"sửa là bịa"*. Một cận dưới CÓ KHAI thì dùng được; một số "đã hiệu chỉnh" bằng
giả định thì không.
📌 Tester tự bắt mình trích `30%` **không kèm kịch bản** (đó là ngưỡng của `100×1,0`) — nếu không
tự sửa thì PO-agent đã đóng dấu nó vào STATE như ngưỡng chung. Khai-trục, lần thứ hai trong một giờ.

### 💸 NGÂN SÁCH: sổ đang ghi 1/6 TỚI 1/9 SỐ THẬT — và có thể là lời giải cho câu "2,3M"

Tester đo (`fin05` 14:26): **`14:26:44.157` ta bỏ → `14:26:45.335` DashScope trả HTTP 200 TRỌN
VẸN, 1,2s SAU.** ⟹ đếm-thiếu **THÔI LÀ GIẢ THUYẾT**. Câu đúng để trình: **"chắc chắn đã tiêu thêm,
chưa biết bao nhiêu."**

Cơ chế (coder đọc mã, `graph.py:977`): usage cộng bằng cách lặp `turn_messages` SAU khi lượt xong;
nhánh fallback `return` TRƯỚC vòng đó và `turn_messages` KHÔNG TỒN TẠI (`.result()` đã ném). Cùng
bệnh `tool_calls` — nhưng `0` **không lộ ra vì nó trông giống một phép đo hợp lệ**. ⟹ vá `0 → None`
ưu tiên TRÊN vá callback (callback thu về 0 ở chính ca đang chảy — khai trước để sau không đọc
nhầm thành "bản vá hỏng").

```
1 lượt HỎNG        ≈ 49.700 – 71.600   (8 gọi × 6.216–8.956 đo được trong R)
1 lượt bình thường    15.136            (main.py:376)
⟹ lượt hỏng đắt gấp 3,3 – 4,7 lần lượt CHẠY XONG, và là lượt DUY NHẤT ghi 0
đã ghi sổ 28.000 · 3 lượt hỏng 149.000–215.000 ⟹ THỰC TẾ ~177.000–243.000
```

**Trực giác "timeout thì đỡ tốn" lật ngược hoàn toàn.** 🔴 Giả thuyết: đây là lời giải cho câu PO
hỏi sáng nay *"sao hết 2,3M?"* — **có cơ chế + có một ca đo, CHƯA xác nhận.** Phân định rẻ và tất
định: đối chiếu **tổng sổ nội bộ một ngày** vs **tổng trên bảng điều khiển nhà cung cấp** cùng ngày
→ thuộc PO thật. Còn hở: lời gọi thứ 8 (về sau khi client bỏ) có bị tính không → phiếu Alibaba.

### 🧠 BÀI HỌC LỚN NHẤT NGÀY: 5 lỗi, MỘT lớp — suy từ tập ĐÃ BỊ LỌC mà không khai bộ lọc

| ai | lỗi | bộ lọc giấu |
|---|---|---|
| coder | "không ToolResult ⟹ chết ở lời gọi đầu" | **vắng mặt** (không tool ≠ không lời gọi — thật ra 8 gọi, 0 tool) |
| coder | "0/70 lời gọi chạm trần 20s" | `giay` **chỉ tồn tại cho lời gọi ĐÃ TRẢ VỀ** ⟹ hằng đúng, thiên lệch sống sót |
| coder | "trần đệ quy 20 đặt xa gấp 4 hành vi thật (max 5)" | max 5 là của **lượt THÀNH CÔNG**; lượt HỎNG có **8** |
| PO-agent | `P(cả 3 ≥ p95)=1/8.000` | tính từ **trung bình** `8,07`; số thật `[10,2·5,4·6,9]` — **một** giá trị trên p95, cấu hình "cả 3" **chưa từng quan sát** |
| PO-agent | "phương sai co lại ⟹ có cái ghìm ~30s" | **chọn mẫu theo chính biến sắp đo** — 3 điểm chọn VÌ gần nhau. Trên n=5 cùng lớp: CV 28% ≈ CV thành phần. **Rút trọn.** |

> **LUẬT MỚI (đề nghị số hiệu):** khi nhiều ước lượng ĐỘC LẬP của cùng một đại lượng đều lệch
> **CÙNG MỘT HƯỚNG**, đó không phải nhiễu — đó là **thiên lệch chung**, và phải đi tìm bộ lọc
> chung. Bằng chứng hôm nay: `45K` (PO-agent) → `0–21K` (coder "đính chính") → **thực tế
> 149–215K**. Đính chính đi XA HƠN khỏi sự thật. Bộ lọc chung: **vắng mặt luôn trông giống "ít",
> không bao giờ trông giống "nhiều".**

**Luật 17 dùng ngược lên PO-agent (tester):** `total_tokens=0` với lượt CHỈ-1-lời-gọi ⟹ cả hai giả
thuyết (mất-trọn-lượt / mất-lời-gọi-đang-bay) **dự đoán CÙNG giá trị** ⟹ sức phân biệt **BẰNG
KHÔNG**, không phải "yếu nghiêng một bên". Chặn con số là đúng, nhưng vì **không có dữ kiện nào**.

### 📋 BỐN THỨ CHO PO THẬT (gom, đừng hỏi lẻ)

1. **Phiếu Alibaba — 4 câu một vòng, thứ tự đã xếp lại:** ① 🔴 **trần TPM/RPM ở Singapore có nâng
   được theo yêu cầu không, điều kiện gì** (tester đề, ưu tiên CAO NHẤT — nâng được thì cả nhánh
   đổi vùng LẪN hồ sơ pháp lý cùng rụng bằng một câu hỏi, và nó là đường thoát cho con số 106%)
   ② request client ngắt giữa chừng có tính tiền/TPM không ③ cached-token có vào TPM không
   ④ batch ở **Singapore**: giá 50% và bucket riêng hay không
2. **Đối chiếu bảng điều khiển** tổng token 1 ngày vs sổ nội bộ — phân định giả thuyết "2,3M"
3. **Cư trú dữ liệu** — xem mục dưới
4. 🔴 **CHỐT NHỊP GÕ cho buổi 150 người** — biến quyết định duy nhất. ≤0,5 lượt/ph/người ⟹ T1 đủ;
   1,0 ⟹ không bản vá nào cứu kịp. Đây là **kịch bản chạy**, không phải code, nên là việc của PO.
5. (giữ nguyên) xoay khoá Qwen · secret GitHub Actions · số hotline thật

### ✅ ĐÓNG — Batch API ở vùng ta: KHÔNG KHẢ DỤNG (tester `930e9ff`, hạng: TÀI LIỆU NÓI)

Singapore (`dashscope-intl`, vùng ta chạy) hỗ trợ batch cho **đúng 4 model**: `qwen-max` ·
`qwen-plus` · `qwen-flash` · `qwen-turbo`. **`qwen3.7-max` và `qwen3.8-max` KHÔNG có.** Danh sách
Bắc Kinh dài gấp ba và **không áp dụng cho ta**.
> **Lỗi mẫu, ghi sổ:** câu chuyên gia hỏi (*"qwen3.8-max có trong danh sách batch chưa"*) **thiếu
> một chiều**. Câu đúng: *"model nào hỗ trợ batch **Ở VÙNG NÀY**"*. **Một danh sách năng lực không
> có nghĩa cho tới khi khai vùng/tài khoản/gói mà nó áp dụng.** Cùng họ Luật 12b (khai trục).

### ✅ ĐÓNG — bucket TPM: ĐỘC LẬP theo MODEL, GỘP theo TÀI KHOẢN GỐC (tester, hạng: TÀI LIỆU NÓI)

*"Each model has its own rate limit"* ⟹ route-theo-bước **CỘNG được** thông lượng ✅
*"Rate limits applied at the **root account level** — mọi RAM user, workspace, API key gộp chung"*
⟹ 🔴 **bác trước** ý "tạo thêm API key để có thêm hạn mức" — cùng tài khoản = cùng bucket; tách
khoá chỉ tách **trách nhiệm**, không tách **hạn mức**. Và **thu hẹp** ý tài-khoản-riêng của hồ sơ
chuyên gia vòng 2: tách *workspace* vô ích, chỉ tách **tài khoản gốc** mới đổi bucket — tức đúng
thứ nằm sau cổng điều-khoản đã dựng, không phải đường vòng rẻ hơn.

### 🔴🔴 SỐ QUAN TRỌNG NHẤT NGÀY: ta ĐÃ VƯỢT TRẦN TPM ở đúng cấu hình buổi 150 người

Tester **tự bác con số "50×" của chính mình** bằng chính Luật 12b họ viết 4 giờ trước (xếp hạng
trên một trục — và trục RPM **còn không phải trục ràng buộc**). Số học từ số đã đo, **không cần
lưu lượng người thật**:

```
trần TPM  1.000.000 / 14.198 token/lượt =  70,4 lượt/phút   ← TRẦN THẬT
trần RPM        600 /   2,39 gọi/lượt   = 251,0 lượt/phút   ← không bao giờ chạm trước

150 người × 0,5 lượt/ph =  75 lượt/ph → TPM 🔴 106%  · RPM 30%
100 người × 1,0 lượt/ph = 100 lượt/ph → TPM 🔴 142%  · RPM 40%
```

**Không phải "sát trần" — VƯỢT, ở mức gõ chậm hơn người dùng thật.** ⟹ chỉ có ba đường, không có
đường thứ tư: **giảm token/lượt · giảm lượt/phút · nâng trần** — trước buổi đó.

**Đổi hạng cho T1 phân luồng:** nếu 30% lưu lượng là lượt đơn, T1 cho ~×1,4 — ở mức 106% thì
×1,4 chính là **hiệu số giữa vỡ và không vỡ**. T1 thôi là "tối ưu chi phí", nó thành **điều kiện
đủ tải**, miễn phí, đã ship. ⟹ **việc kế, 0 token: tỉ lệ lượt-đơn trong lưu lượng thật là bao
nhiêu?** ≥30% ⟹ qua được 150 người mà không đụng vùng lẫn hạn mức.

⚠️ **Hở phải khai kèm:** `14.198 token/lượt` là trung bình lượt **THÀNH CÔNG**; lượt hỏng tốn
50–70K. Có lượt hỏng trong lưu lượng thật ⟹ `70,4 lượt/phút` là **quá lạc quan** — đúng thiên
lệch sống sót đã đốt 2 giờ hôm nay. Không sửa số, chỉ khai kèm.

**Đổi vùng mua ×5, KHÔNG phải ×50:** Singapore 600 RPM/1M TPM = 70 lượt/ph · US-Virginia
30.000 RPM/**5M TPM** = 352 lượt/ph.
> ⛔ **CỔNG GIỮ NGUYÊN:** US-Virginia = đưa hội thoại khách VN ra hạ tầng Mỹ. Hôm nay dữ liệu tổng
> hợp nên vô hại; **khách thật là NĐ 13/2023 + cư trú dữ liệu**. Cùng ngăn với ý nhiều-tài-khoản:
> *đo được, QUYẾT ĐỊNH thuộc người có thẩm quyền pháp lý.* Nhưng hạng đã đổi: không phải *"đòn bẩy
> 50× bị pháp lý chặn"* mà *"đòn bẩy 5× đòi đưa dữ liệu khách Việt ra Mỹ"* — hai mức giá rất khác
> nhau để cân, và ×5 có thể **thua** T1 (×1,4 miễn phí, không hồ sơ pháp lý).
> **Phép đo RPM tôi định xếp hàng đợi: KHÔNG CẦN CHẠY** — phép chia đã trả lời.

### 📊 Số nền đo được hôm nay (giữ để đối chiếu, ĐÃ KHAI bộ lọc)

```
lời gọi (n=70, ĐIỀU KIỆN HOÁ TRÊN THÀNH CÔNG — lời gọi bị giết KHÔNG có `giay`)
  p50 3,3 · p90 6,9 · p95 8,0 · p99 11,6 · max 11,6 · tb 4,0
lời gọi/lượt (n=33 lượt THÀNH CÔNG)  tb 2,12 · max 5    ⟵ lượt HỎNG có 8
thời gian NGOÀI lời gọi model: trung vị 24% · min 10% · max 61%
lượt ≥3 lời gọi (n=5): 13,1 · 19,6 · 29,3 · 29,4 · 30,7  → CV 28%, KHÔNG có chỗ tụ
biên hiện tại: lượt nặng nhất 30,7 / trần 45 = 68%  ⟵ báo động biên, thuộc bộ ca tester
`agent_recursion_limit_reached`: 0 lần trên cả 3 ngăn xếp — nhưng lượt hỏng đã đi tới 8/20
```

### 🧭 A2 — phạm vi chốt, cách đếm chốt (tester `d510187`, trục 3 đã vào bộ ca)

Tester ĐO thay vì nhận mệnh đề của PO-agent: `other/*` `trans_id` rỗng ×101 · `human_handoff_
requested=true` ×107 / **761** ⟹ **~14% thuộc lớp không phân biệt được**. Hai tập gần trùng nhưng
không trùng, và `human_handoff_requested=true` **đúng về ngữ nghĩa** cho cả khách CHỦ ĐỘNG xin gặp
người ⟹ **không cột nào tách được** — Luật G nguyên bản: *cơ chế đang làm đúng việc của nó không
có nghĩa nó đang làm việc ta giả định.*
⟹ **Cách đếm cho bộ A2: qua SỔ USAGE (`ly_do_fallback ≠ null`, coder land `559d6df`), KHÔNG qua
`Δcomplaints` thuần.** Nửa còn thiếu ở bản ghi nghiệp vụ = ADR-029 mục 2 + F-33c, chờ PO.
Ép đường hỏng bằng `AGENT_TURN_TIMEOUT=1`: **được, 0 token**, nhưng cần recreate ⟹ **đổi vật** ⟹
phải nằm trong đợt đổi bộ số của coder, **không làm riêng** (tester tự chặn trước khi PO-agent nói).

## 🔴 ĐANG ĐIỀU TRA (16/08) — DEMO-BUG "gặp người thật ra lỗi": đua-refresh → AUTH5-03 thu hồi family
PO gặp lỗi giữa demo mentor 15/08 (đúng quy trình 2 cửa sổ — giả thuyết đè-phiên BỊ BÁC bởi dữ
kiện PO). **Dữ kiện bổ sung của PO siết thêm:** trước demo họ chạy TRỌN kịch bản KỂ CẢ handoff —
ĐẠT (lướt nhanh <13 phút từ đăng nhập); rồi ĐĂNG XUẤT HẲN, 1 tiếng sau đăng nhập TƯƠI demo thật
— chết ở handoff (>13 phút vì có mentor). ⟹ biến số duy nhất giữa đạt/trượt là THỜI-GIAN-TỪ-ĐĂNG-
NHẬP; loại nghi vấn phiên-cũ-để-rác (family demo là mới sạch). Cặp đối chứng tự nhiên từ đời thật. Giả thuyết hiện tại (coder đọc code xác nhận KHẢ THI CẤU TRÚC, "gần như tất định"):
access token vào cửa sổ refresh (`REFRESH_MARGIN_SECONDS=120`) → handoff là thời điểm đầu tiên có
≥2 request đồng thời (`ChatClient.tsx:195` bắn ws-ticket ngay) → 2 đường cùng refresh bằng MỘT
token dùng-một-lần → đứa thua trúng AUTH5-03 (`auth.py:146-155`) → **thu hồi CẢ FAMILY kể cả cặp
vừa phát** → phiên chết chuỗi → "Có lỗi" trong khung chat. Cờ `rotated` giữ 60s ⟹ KHÔNG cần trùng
mili-giây. Khớp 3 dữ kiện PO + log (`refresh 401`×2, `ws-ticket 401`×4 cụm).
- **TTL access token ĐO ĐƯỢC (tester): 15,0 phút ĐỒNG NHẤT cả 4 role** — khớp chính xác "chat
  ~15-20 phút rồi chết" của PO; con số đó là TTL, không phải cảm giác.
- **Tester tinh chỉnh không gian giả thuyết (từ số đo tối qua, tất định):** một request ĐƠN sau
  khi token chết đã đủ 401 (proxy đặt cookie lên response, handler đọc từ request — 401 rồi lượt
  sau 200, TỰ HỒI). ⟹ đua là **điều kiện ĐỦ chứ chưa chắc CẦN** cho "có lỗi"; nhưng chỉ ĐUA mới
  giải thích được **chết-hẳn-không-hồi** (AUTH5-03 revoke family). Trục phép đo = phân biệt
  "401-rồi-hồi" vs "401-rồi-chết-luôn" (3 lần gọi lại sau đó là phép thử quyết định).
- **HAI QUYẾT ĐỊNH ĐO (tester đề nghị, PO-agent duyệt):** ① **N của grace CHỈ lấy từ dấu thời
  gian SERVER-SIDE** (log `auth.py:150`) — khoảng cách `curl & curl` là độ trễ spawn của MÁY ĐO
  không phải của sản phẩm; lấy N từ đó = hạ một control bảo mật dựa trên hiện vật công cụ (họ 7b,
  hậu quả nằm trong ADR). Số client-side chỉ ghi nhãn "giới hạn trên thô, không dùng định N".
  ② **Instance TTL ngắn (`JWT_ACCESS_EXPIRE_MINUTES=1`, compose project riêng) = HẠ TẦNG ĐO BẮT
  BUỘC vùng auth** — cửa sổ refresh mở ở phút 13 ⟹ k=10 mất 2 giờ; TTL 1 phút → k=30/20phút, và
  test hồi quy vùng auth CHỈ tồn tại được nếu có đường này (Luật 14 chiều thời gian: nhánh không
  chạy NHANH được cũng là nhánh không ai canh). → coder.
- **🏁 TÁI LẬP TRỌN VẸN CA PO (tester, stack demo, backend a216b98c1b79 có tầng-0):** mở /chat →
  2 request → **16 phút ngồi yên KHÔNG một request nào** (trang im hoàn toàn — không heartbeat)
  → token chết lặng → bấm gặp-người-thật → `agent-chat` **401**, màn hình in nguyên văn
  **"Có lỗi: Phiên đăng nhập đã hết hạn"** → **chính response 401 đó mang cookie mới**
  (tầng-0: rotated=1, revoked=0) → gõ lại một tin → **200 + handoff chạy trọn** (~86s sau).
  Cơ chế chốt = đúng khiếm khuyết proxy.ts coder đọc: cookie đặt trên RESPONSE không áp cho
  request đang chạy. Không đua · không revoke · không hồi quy · không hai tab.
  **UI-no-retry BÁC CHO CA NÀY** (agent-chat chết TRƯỚC khi luồng chạm ws-ticket ⟹ ref-guard
  chưa bao giờ bật; lần thử lại đi trọn) — UI-02 vẫn làm trên merit nhưng PR không được claim
  fix-bug-demo. Ref-guard vẫn có thể là lỗ riêng nếu 401 rơi đúng ws-ticket — chưa quan sát,
  không vá mù.
- **🔴 ĐÍNH CHÍNH HỒ SƠ (PO-agent):** câu "PO nói bấm lại vẫn không được" **KHÔNG tồn tại trong
  lời khai nào** — PO chỉ nói "nhận được tin trả lời là có lỗi"; 3 câu hỏi lời khai ĐANG CHỜ.
  Câu đó sinh từ vòng diễn-giải nội bộ rồi được trích như lời khai = **lời-kể-ma ở dữ liệu định
  tính** (họ hàng dấu-băm cho dữ liệu định lượng). Không có mâu thuẫn số-vs-lời — chỉ có câu hỏi
  chưa trả lời (đã hỏi lại bản sắc: GÕ TIN MỚI hay BẤM NÚT trên khung lỗi).
- **Cặp cổng mốc-nền "trước" hoàn chỉnh** (frontend chưa vá): [cổng proxy: sau-ngồi-yên thao tác
  đầu 401] + [cổng tầng-0: rotated=1/revoked=0 ✅]. Điều kiện bắt buộc ghi trong cổng: trang MỞ
  SẴN không điều hướng (goto() tự lành → xanh giả). Coder land hướng-2 → deploy → đo "sau".
- **Drift BÁC bằng đo** (3 image cùng node 20.20.2 / next 16.3.0 / manifest rỗng; `oldc447abb`
  trúng cache toàn phần, timestamp 15/08T13:01Z ⟹ nhiều khả năng CHÍNH LÀ image 15/08 — và nó
  cho 0 Set-Cookie). **Code khớp docs Next 16 từng điểm** (src/proxy.ts đúng chỗ, export đúng
  tên, mẫu cookie đúng docs). Đã bác HẾT 8 giả thuyết. Còn: proxy CHẠY + manifest RỖNG +
  Set-Cookie KHÔNG egress (có đối chứng /api/session=1 header).
- **PO-agent chặn một vòng lãng phí:** câu coder định hỏi ("harness 15/08 có /api/session xen
  giữa?") ĐÃ được tester trả lời từ trưa (chỉ dòng 14 lúc login). Phép hoà giải cuối giao coder:
  grep route handler nào NGOÀI /api/session tự set-cookie (nếu đường ws-ticket có → +842s là
  cookie từ ROUTE HANDLER, không phải proxy → mâu thuẫn tan). Không có → +842s = dị thường lịch
  sử, GHI KHÔNG LẤP KHÔNG CHẶN (nếp MT-E02).
- **QUYẾT: HƯỚNG (2) GO — không chờ giải dị thường.** Refresh chuyển xuống `backendFetch()` MỘT
  điểm chặn: 401 → refresh → set-cookie trên response route handler (đường ĐÃ chứng minh egress).
  Điều kiện đóng: single-flight per-request trong backendFetch (không tái tạo bug đua tầng mới) ·
  test cấu trúc canh proxy-đăng-ký · cổng đo request-1-VÀ-2 + family-không-revoke · gỡ phần
  refresh chết khỏi proxy.ts có ghi lý do · security re-probe. Sau land: PO-agent viết ADR-026
  ghi quyết định + trọn lịch sử điều tra.
- **Bước (1) coder: khả-năng-(3) BÁC có đối chứng** (`/api/session` route-handler-tự-set-cookie
  grep THẤY ⟹ dụng cụ không hỏng; ws-ticket + trang /chat đều 0 set-cookie). Thu hẹp: middleware
  CHẠY nhưng **mọi mutation lên response bị BỎ** — proxy.ts biên dịch + thực thi nhưng KHÔNG được
  đăng ký như middleware thật (manifest rỗng khớp). Hai hướng vá treo: (1) sửa đăng ký Next 16 /
  (2) chuyển refresh xuống backendFetch (một điểm chặn).
- **🔍 PO-agent chỉ ra MÂU THUẪN DỮ KIỆN = lối tắt:** tối 15/08 tester đo image THẬT đang chạy —
  **cookie CÓ XOAY tới client** (+842s đọc từ jar); hôm nay rebuild TỪ CÙNG COMMIT `c447abb` →
  0 set-cookie. Cùng mã, hai hành vi ⟹ nghi phạm mới ngoài cả 3 khả năng: **DRIFT PHỤ THUỘC lúc
  build** (base image node tag di chuyển / Next patch khác). Phép kiểm rẻ giao coder TRƯỚC khi
  đọc docs: tìm image thật 15/08 còn trên đĩa (untagged/dangling) → so version Next + manifest
  hai bên. Version khác = root là drift → vá bằng GHIM dependency (digest base image + lockfile).
- **Điều kiện đóng RATIFY bất kể hướng:** thêm test CẤU TRÚC canh middleware-được-đăng-ký
  (manifest không rỗng / probe cookie-tới-client trong e2e) — middleware chết im lặng không ai
  biết bao lâu là bài học lớn nhất vụ này (Luật 14). Tiêu chí chọn hướng đã chốt sẵn: cấu-hình-
  có-tài-liệu→(1); mơ hồ→(2) qua MỘT điểm chặn backendFetch.
- **🎯 CƠ CHẾ CỤ THỂ NHẤT TỪ ĐẦU (coder đo 1-request sau khi vá thử, CHƯA LAND):** middleware
  chạy ĐÚNG MỘT lần (đo) · backend xoay token THÀNH CÔNG (tầng-0 `refresh_rotated`) · **Set-Cookie
  KHÔNG BAO GIỜ RỜI SERVER** (header response không có set-cookie) ⟹ request kế cầm token cũ đã
  rotate → AUTH5-03 revoke. Không đua, không hai-lần-gọi — **cookie mất trên đường ra**. Bản vá
  hiện tại của coder chỉ sửa vế route-handler-thấy-token-mới (cần) — CHƯA sửa vế browser-nhận-
  cookie (vế giết phiên). **Coder TỪ CHỐI LAND** vì cổng tester ("request đầu 200") sẽ xanh trong
  khi phiên vẫn chết ở request thứ hai — xanh-cổng-mà-không-hết-bệnh. Thứ tự duyệt: kiểm khả-năng-
  (3) (chính bản vá làm mất cookie — rẻ nhất, nghi-mình-trước) → rebuild demo backend sau khi
  tester xong → chốt hình dạng vá. **Cổng nghiệm thu MỞ RỘNG: đo cả REQUEST THỨ HAI** (req1 200 ∧
  req2 200 ∧ family không revoke). UI-02+retry song song.
- **Quy ước báo-trước-rebuild TRẢ LÃI trong 1 giờ:** tester xin coder giữ tay rebuild vì phép đo
  đang chạy — rebuild giữa chừng KHÔNG làm phép đo đỏ, nó vẫn in số, chỉ là số của HAI backend ở
  hai nửa lượt (dạng vật-trôi nguy nhất: không triệu chứng). Lần thứ tư vật-trôi trong hai ngày,
  lần ĐẦU tránh được nhờ báo trước.
- **✅ KHÉP VÒNG SỐ (coder xác nhận bằng bằng chứng mạng):** cả 11 refresh + cặp 10/10 đều ở
  backend fin05ttl (172.20.x), client là middleware TTL, probe của chính coder — "10/10 mô tả
  instance TTL, chấm hết"; coder tự nhận *"nặng hơn vì chính tôi dựng instance đó rồi quên nó là
  vật khác"*. Cơ chế TTL-là-chế-độ-biên xác nhận: TTL 60s < margin 120s ⟹ token TRONG cửa sổ
  refresh từ giây đầu ⟹ refresh MỌI request (production: 2 phút cuối/15). Cảnh báo ghi thẳng vào
  `docker-compose.ttl-test.yml`. Demo backend CHƯA có tầng-0 (build trước a74de7d) → việc-0:
  rebuild theo quy ước báo-trước-khi-rebuild-image.
- **✅ REF-GUARD XÁC NHẬN ĐỌC-MÃ (mảnh ráp trọn ca PO):** `liveChatConnectStartedRef` đúng 3 dòng,
  KHÔNG reset ở đâu — một lần thử vĩnh viễn. Chi tiết chốt: nhánh `.catch` bảo khách *"thử lại
  giúp mình nhé"* trong khi KHÔNG TỒN TẠI đường thử lại (effect chỉ chạy lại khi liveChatTicketId
  đổi — nó không đổi). ⚠️ Điều kiện nghiệm thu vá (ratify): reset-ref KHÔNG đủ (deps không đổi thì
  effect không chạy lại) — cần đường thử-lại THẬT (nút/retryCount trong deps), GIỮ chống-StrictMode;
  e2e assert "sau 401 đầu, UI CÓ bắn request thứ hai khi thử lại".
- **GREENLIGHT đã phát:** ① vá `proxy.ts` cookie-trên-request (PR, gate: cổng hồi quy tester +
  re-probe security) · ② UI-02+retry (PR) · ⓪ rebuild demo backend lấy tầng-0 (xin khe tester).
  Lời khai PO (đã hỏi 3 câu) không chặn vá — nó quyết có CÒN cơ chế nào ngoài hai defect đã chốt.
- **⚖️ PHÂN XỬ CUỐI (tester, log server-side, MỘT request sạch):** `rotated=1 · family_revoked=0
  · HTTP 200` ⟹ refresh gọi ĐÚNG MỘT lần, chạy THÀNH CÔNG, không thu hồi gì. **Cặp "10/10 tất
  định" là TỔNG TÍCH LUỸ của nhiều lượt thử trộn lẫn** (gồm cả probe song song của tester) — suy
  nhân-quả từ hai tổng bằng nhau = ca sách giáo khoa **đếm-tổng không thay được đếm-theo-lượt**
  (LUẬT MỚI). Số +842s cũng khép: chuỗi đầy đủ 200→(16 phút)→401-vì-token-MỚI-cũng-hết-hạn→200→200
  — phiên sống khoẻ, không cần cơ chế thu-hồi nào để giải thích.
- **VẬT ĐỔI LẦN BA** (image TTL bị dựng lại giữa hai phép đo → "TTL không rotate" RÚT). **RATIFY
  quy ước đội:** ① mọi phép đo trên stack kèm IMAGE ID trong nhãn; ② **ai dựng lại image phải báo
  vai đang đo** — luật BÁO-TRƯỚC-KHI-LAND mở rộng sang image.
- **CHỖ ĐỨNG THẬT SAU MỌI SỐ:** thứ DUY NHẤT tái lập được = hiện vật `proxy.ts:112` — *token hết
  hạn ⟹ request đó 401, cookie mới về client, request KẾ 200*. KHÔNG tái lập được: đua-giết-phiên
  · thu-hồi-family · refresh-không-chạy · hồi-quy-image. Ứng viên ráp trọn ca PO: hiện vật 401-
  một-lần + **UI ref-guard không-bao-giờ-thử-lại** (`ChatClient.tsx:199` — PO-agent góp, chờ e2e
  + coder xác nhận). Mảnh quyết định còn thiếu: **lời khai PO — lúc lỗi có thao tác lần hai
  không, kết quả gì** (đang hỏi).
- **✅ CƠ CHẾ CHỐT (16/08 tối, bằng chứng server-side tầng-0):** middleware refresh CÓ chạy nhưng
  **nuốt lỗi im lặng**; cặp log `refresh_rotated`×10 ↔ `refresh_family_revoked`×10 **ghép 1-1 tất
  định**: cookie mới đặt lên RESPONSE, lượt gọi refresh THỨ HAI trong cùng vòng request vẫn cầm
  token CŨ → AUTH5-03 thu hồi family — **hệ TỰ BẮN VÀO CHÂN, không cần user sai, không hai tab,
  không đua.** Dòng-A (hồi quy UI-01) BÁC bằng đo (image c447abb hành xử y hệt, proxy.ts 0 byte
  đổi); ứng viên-4 cũng sai ("không chạy" = "chạy-thất-bại-nuốt-lỗi"). **Dòng B (bug demo PO)
  được giải thích trọn**: sau phút 15, lượt đầu tiên rotate+tự-thu-hồi → mọi thứ 401.
  **Grace-window RÚT khỏi kế hoạch** (bug tất định của client, không phải đua hiếm — AUTH5-03 giữ
  nguyên, nó vừa chứng minh làm đúng việc). Còn lại: tester đếm `refresh_rotated` trên ĐÚNG MỘT
  request (phân xử vì-sao-gọi-hai-lần, quyết hình dạng vá) → coder vá (hướng: request-headers cho
  lượt sau thấy token mới) → hồi quy TTL → security re-probe → đóng.
  Coder tự khai: suýt kết luận sai BA lần từ artifact tĩnh — thứ cứu là hỏi-hệ-thống-một-câu-khác
  thay vì đọc-kỹ-hơn-cùng-một-chỗ.
- **🔴🔴 BƯỚC NGOẶT (16/08 chiều): KHÔNG AI ĐO SAI — VẬT ĐỔI. Image frontend stack demo được DỰNG
  LẠI 2026-08-16T02:11Z** (12,5h sau phép đo exp+842s; nghi là lần deploy UI-01). **Image cũ:
  refresh CHẠY** (exp+842s = một lần xoay thật, harness tester sạch — không /api/session xen giữa,
  đã kiểm). **Image mới: refresh CHẾT** (cả hai endpoint, phủ-đều-bằng-không). Hai image ID:
  `90d7b915bcbf` (mới) vs `210edbc5a06a` (TTL). ⟹ **TÁCH HAI DÒNG ĐIỀU TRA:**
  · **Dòng A — HỒI QUY refresh (ưu tiên 1, ĐANG SỐNG trên stack demo):** mọi phiên chết cứng phút
    15. Coder dựng image từ commit trước 15/08T13:43Z probe đối chiếu → chốt hồi quy → tìm diff
    trong cửa sổ [demo-GO … 6a07b16+lô cùng deploy].
  · **Dòng B — BUG DEMO 15/08 của PO: CHƯA GIẢI.** Nó xảy ra trên IMAGE CŨ nơi refresh CHẠY ⟹
    ứng viên "refresh chưa bao giờ chạy" KHÔNG giải thích được nó; và MỌI số Pha A/C/D hôm nay đo
    trên hệ đã-hồi-quy — nói về dòng A, không nói được gì về B. Đua-revoke/harness sống lại làm
    ứng viên; đo lại B chỉ được SAU khi A vá (cần hệ có refresh chạy). CẤM vá single-flight/grace
    tới khi B đo trên vật đúng.
- **📌 Lỗ nhãn phép đo (tester tự nhận): `he_thong` băm `src/**/*.py` — KHÔNG phủ `frontend/`**,
  mà refresh sống ở `frontend/src/proxy.ts` ⟹ vật trôi ngay dưới chân phép đo, cái ghim mù trước
  nó. Từ giờ nhãn phép đo kèm **IMAGE ID** (+ SHA + he_thong) cho mọi phép đo chạm frontend.
- **🔄 ĐẢO BÀN CỜ (16/08 chiều — coder đọc-mã + đo trên instance TTL):** `refreshSessionIfNeeded`
  có đúng MỘT call-site (`proxy.ts` dòng đầu, matcher phủ mọi `/api/*`) — phủ ĐỀU, **nhưng đo ra
  phủ-đều-BẰNG-KHÔNG: không endpoint nào xoay cookie** (TTL=1ph < margin=120s ⟹ mọi request trong
  cửa sổ; đã loại backend-unreachable + image-cũ). ⟹ **Ứng viên cơ chế THỨ TƯ, đơn giản nhất:
  refresh KHÔNG BAO GIỜ CHẠY** — token chết phút 15, "15-20 phút rồi lỗi" của PO = TTL, handoff
  chỉ tình cờ là thao tác đầu tiên sau mốc. Nếu đúng: single-flight = vá thứ không tồn tại, grace
  không áp dụng — bản vá đúng là LÀM CHO REFRESH CHẠY. **CẤM viết vá tới khi phân xử.**
  Mâu thuẫn còn lại: số tester tối qua (`ws-ticket` exp+842s = một lần refresh thật) vs 0 hôm nay
  → kiểm (a) rẻ nhất: tester đọc lại harness tối qua tìm `/api/session` xen giữa; (b) nếu âm:
  probe stack demo phút 13. Tầng-0 log đã LAND `a74de7d` (trường `refresh_rotated` server-side).
  Instance TTL SỐNG: `https://localhost:8443`, project `fin05ttl`, 208 user, stack demo nguyên vẹn.
- **📌 Tri thức mới (coder tự bắt khi đo):** compose đặt tên IMAGE theo PROJECT — hai stack = hai
  image khác nhau (`fin05-frontend` ≠ `fin05ttl-frontend`); đo trên stack TTL mà so với số stack
  demo là ĐO NHẦM VẬT. Phát hiện bằng `docker inspect`, chữa bằng build-lại-từ-nguồn cho khớp.
  Nhãn phép đo đa-stack phải kèm IMAGE ID.
- **Tái lập đang chạy nền (~32 phút, 0 TPM):** Pha A đua (2 request song song cùng chuỗi cookie
  cũ, đúng cảnh browser 2 request in-flight) + Pha B đối chứng tuần tự. Qua đúng đường BFF
  `https://localhost/api/live-chat/ws-ticket` = đúng chỗ PO chết. Giới hạn tự khai: bắn 2 request
  CÙNG endpoint — nếu single-flight có ở đường này thiếu ở đường khác thì đo không thấy ⟹ Pha A
  xanh = "chưa tái lập bằng cách này", KHÔNG phải "giả thuyết sai".
- **Coder chờ số mới vá**: single-flight promise module-scope `proxy.ts` — tự khai giới hạn *chỉ
  chặn đua cùng tiến trình Node*; scale nhiều replica frontend cần khoá Redis (ghi vào bản vá).
- **Ý KIẾN SECURITY VỀ AUTH5-03 (`2cff494`) — ba tầng, định hình cả lô vá:**
  ① **Single-flight: CẦN nhưng KHÔNG ĐỦ** — promise dùng chung chỉ phủ MỘT ngữ cảnh JS; **đa-tab
  là hai ngữ cảnh không thấy nhau**, mà CSKH mở nhiều ticket nhiều tab là cách làm việc bình
  thường ⟹ vá single-flight làm bug biến mất trong demo một-tab rồi QUAY LẠI trên bàn làm việc
  thật, lần sau khó truy hơn vì "đã vá rồi mà". Vẫn làm (rẻ, đúng), nhưng KHÔNG coi là xong.
  ② **Grace-window: DUYỆT đúng MỘT dạng — PHÁT-LẠI-BẤT-BIẾN** (trong N giây, cùng token cũ trả
  ĐÚNG cặp đã cấp lần đầu). **BÁC dạng cấp-cặp-mới** (tạo hai phiên phân kỳ = đúng thứ rotation
  sinh ra để chặn). Bốn điều kiện: bất biến · N NGẮN vài giây lấy từ PHÂN BỐ ĐO ĐƯỢC không lấy số
  tròn · bắn-trong-grace log nhánh riêng · ngoài N giữ nghiêm. **KHÔNG land trước khi có số tester.**
  ③ **🔴 FINDING NẶNG HƠN CẢ CÂU HỎI: `auth.py` 294 dòng KHÔNG MỘT DÒNG LOG** — `revoke_family()`
  (sự kiện "chúng tôi tin token bị đánh cắp" — lớn nhất của cả hệ xác thực) bắn HOÀN TOÀN IM LẶNG.
  Không đếm được AUTH5-03, không phân biệt được đua-vs-trộm trên production, **chỉnh control không
  quan sát được = chỉnh mù**. Vá TRƯỚC hoặc CÙNG lô, rẻ nhất trong ba việc: log cấu trúc tại
  `auth.py:150` (family_id · user_id · role · nhánh `reuse_that`/`phat_lai_trong_grace`). Đây
  cũng là lý do bug demo thành bí ẩn: control bắn đúng mà không để lại dấu vết nào.
- Nối finding cũ: đường proxy-cookie (401-rồi-200) LUÔN tiêu một lượt refresh → chồng thêm request
  là 401-vô-hại thành thu-hồi-family ⟹ bản vá proxy.ts backlog NÂNG mức quan trọng.
- UI-01 (timeline không-JSON) đã land `6a07b16` + deploy stack demo. UI-02 (banner lệch-vai) vẫn
  đáng làm, xếp sau.
- Workaround demo tới khi vá: đăng nhập lại vai khách NGAY TRƯỚC màn gặp-người-thật.
Cập nhật: **2026-08-15 (phiên Đợt 2 + bàn giao P-226)** · PO-agent điều phối 4 vai (Claude Code)

## 🔄 BÀN GIAO SANG P-226 — ĐỌC ĐẦU TIÊN
> **Repo đã migrate từ P-121 → P-226 (đầy đủ lịch sử).** Nhánh làm việc: `dev/learning-loop`
> (HEAD dacbefd, 256 commit). `main` = 104 commit. Đang code trong thư mục `P-226`.
>
> **Bối cảnh dự án:** FIN-05 — AI Agent CSKH ví điện tử xử lý khiếu nại, chuẩn fintech EU/US.
> Đội = 4 phiên Claude Code (PO-agent điều phối · coder/tech-lead · tester · security), đồng bộ
> qua **git + cross-session message** (SendMessage/ListAgents), mỗi vai chỉ ghi vùng của mình (§4).
> ⚠️ **CÂY LÀM VIỆC DÙNG CHUNG giữa 4 phiên** → mọi `git stash/commit/checkout/clean` **phải kèm
> pathspec vùng của mình**. Lệnh không pathspec sẽ cuốn theo việc đang dở của vai khác.
>
> **PHIÊN MỚI Ở P-226 làm gì trước:** đọc `CLAUDE.md` (hiến pháp) → file này → sổ Đợt 2
> `docs/giao-viec/2026-08-15-ke-hoach-3-chu-de-nang-cap.md` (18 luật đo + mọi finding) →
> 5 ADR gần nhất trong `docs/DECISIONS.md` (tới ADR-024). Đó là toàn bộ ký ức Đợt 2.
>
> **AI-log (đo lại 15/08 tại P-226 — mục cũ ghi theo P-121, KHÔNG đúng cho repo này):**
> Lớp THU log chạy tốt (`.ai-log/session.jsonl`). Nhưng lớp GỬI cần ba thứ, **hook không đi
> theo git nên migration làm mất hai thứ đầu**:
> 1. `.git/hooks/pre-push` — P-226 ban đầu KHÔNG có (chỉ còn `.sample`); cài bằng
>    `bash scripts/setup_hooks.sh`. Hook là file local, migration `.git` mới là mất.
> 2. `.env` với `AI_LOG_SERVER` + `AI_LOG_API_KEY` — P-226 ban đầu KHÔNG có `.env`.
>    Thiếu → `submit_log.py` in "AI_LOG_SERVER not set" rồi `exit 0` **im lặng**, push vẫn xanh.
> 3. `SSL_CERT_FILE` — **thiếu thì trượt `CERTIFICATE_VERIFY_FAILED`** (đo thật lúc push
>    `954a6a9`). ⚠️ **Phải ghi ĐƯỜNG DẪN THẬT** (`.../certifi/cacert.pem`, lấy bằng
>    `python3 -c "import certifi; print(certifi.where())"`) — dạng `$(python -m certifi)` mà
>    bản STATE trước ghi là **SAI**: `python-dotenv` không chạy command substitution, nó đọc
>    nguyên văn chuỗi `$(...)` thành đường dẫn rác.
>
> **AI log KHÔNG đi qua commit** — `.gitignore:74-75` loại `.ai-log/*.jsonl`; log được POST
> lên grading server bởi pre-push hook, tức lúc **`git push`**, không phải `git commit`.
> Trượt submit KHÔNG chặn push (`exit 0` cuối hook) và log được giữ lại nguyên vẹn (đường
> `_restore_pending` đã verify thật: 0 dòng mất sau lần trượt SSL).
>
> **✅ ĐƯỜNG AI-LOG P-226 ĐÃ THÔNG — verify thật 15/08, push `eadcca7`:**
> `[ai-log] Submitted 73 entries → 202` · `.ai-log/archive/2026-08-15.jsonl` sinh ra với đúng
> 73 bản ghi, parse JSON 73/73 hỏng 0, metadata đúng (`repo=P-226` · `branch=dev/learning-loop`
> · `student=jin.simple@gmail.com`).
>
> **Chuỗi chẩn đoán 4 lượt push (giữ lại vì mỗi nấc hỏng cho một triệu chứng KHÁC nhau):**
> `954a6a9` CERTIFICATE_VERIFY_FAILED (thiếu SSL_CERT_FILE) → `3f59e3e` **401** (SSL thông) →
> `e6e5f7b` 401 (không đổi vì key chưa thay) → `eadcca7` **202 ✅** (key mới `ai20…` 38 ký tự,
> lấy từ link mời BTC; key cũ `f3p1…` 64 ký tự chép sang từ P-121 là key ĐÃ THU HỒI).
> `LANGCHAIN_*` KHÔNG liên quan tới đường này: `submit_log.py:28-30` chỉ đọc `AI_LOG_SERVER` ·
> `AI_LOG_API_KEY` · `AI_LOG_DIR`.
>
> ⚠️ **Hỏng IM LẶNG — đừng lấy "push xanh" làm bằng chứng.** Hook `exit 0` nên push luôn
> thành công dù submit trượt; dòng `[ai-log] Submit failed` lẫn giữa output git. **Bằng chứng
> khách quan DUY NHẤT là `.ai-log/archive/`** — chỉ sinh ra SAU khi POST thành công.
> `session.jsonl` BIẾN MẤT sau lần gửi được là ĐÚNG THIẾT KẾ (atomic rename), hook tạo lại ở
> lượt ghi kế tiếp — đừng tưởng mất log.
>
> **AI_LOG_API_KEY mới đã hoạt động ở P-226.** LANGCHAIN tạm TẮT có chủ đích
> (`LANGCHAIN_TRACING_V2=false`, key rỗng) — PO quyết gác lại, không chặn gì.
>
> **CÒN TREO — backlog P-121: 9133 dòng ở `P-121-new/.ai-log`.** Phải **thay key mới vào
> `P-121-new/.env` nữa** (nơi đó vẫn là key `f3p1…` đã thu hồi) rồi push từ P-121.
> **ĐỪNG xoá P-121-new tới khi submit xong** (deliverable #4). Liệu lịch: `BATCH_LIMIT=500`
> mỗi lần push ⟹ cần **~19 lượt push**, không phải một phát xong.
> ⚠️ Nhánh leftover của `_archive_entries()` (vá ở `eadcca7`) **CHƯA từng chạy thật** — lượt
> 15/08 chỉ có 73 bản ghi, dưới ngưỡng 500 nên không sinh leftover. Backlog P-121 sẽ là lần
> ĐẦU TIÊN nhánh đó chạy; kiểm `wc -l .ai-log/archive/*.jsonl` sau 2 lượt push đầu để chắc
> archive không phình trùng lặp.
>
> **Việc còn treo (không chặn, đã có tài liệu trong sổ Đợt 2):** đợt nâng CỔNG-A gộp 3 oracle
> (số-ngắn+tên+phủ-định) theo xuất-xứ · câu-4 RAG retrieval quality (3/5 câu chính sách hợp lệ agent
> không trả được — sửa chunk/embedding, KHÔNG nới ràng buộc 9) · MT-E02 traceback · hạ tầng đo temp=0/k≥3.
>
> **Chờ PO thật:** tạo lại keys · hướng đợt 150 người (lượt end-to-end đã cho dữ liệu: bộ lọc 17/17
> không siết nhầm, RAG retrieval là điểm yếu; 4 góc chưa-sẵn-sàng: TPM · 429→500 · timeout · RAG).


> Nhánh: **`dev/learning-loop`**. Sổ điều phối Đợt 2 (đầy đủ, ~18 luật + mọi finding):
> `docs/giao-viec/2026-08-15-ke-hoach-3-chu-de-nang-cap.md`. Đêm 14→15/08: sổ `2026-08-14-*`.
> Đồng bộ = git (4 vai cùng repo). Cơ chế: dấu-băm mọi phép đo · nháp-ngoài-repo · báo-trước-khi-land.

## Vừa xong (Đợt 2 — nhánh 5b chống-injection, verified CẢ HAI nửa)
- **Spotlighting** (F-22/23/24/25/26) — bọc dữ liệu untrusted 4 cửa, nhãn TRUNG TÍNH, verify trong container.
- **Lọc đầu ra O1-O4 + luật XUẤT XỨ** (số agent nói phải truy về tool result — trùng ràng buộc cứng 3):
  origin-rule verified 14/14 (corpus độc lập tester) · efficacy 15/16 · chặn-nhầm 0/8 · 0 gán-sai-nhóm.
  Vá dọc đường: JSON-comma phantom (hai-kênh) · F-27 (bỏ neo chữ "OTP") · F-26 (nhãn-sau-scrub).
- **5a (cảm xúc) contract v2.4.0/v2.5.0 ĐÃ KÝ TOÀN BỘ Câu 1+2+3** (ADR-022): thread_signals +
  emotion_signals dựng xong. **Câu 3 (chip câu CSKH) PO thật duyệt 15/08**: khung "chip vận-hành
  mức hội-thoại, KHÔNG nhãn tâm-lý" + N=3 (cùng ngưỡng nút-khách) + **CSKH thấy chip** — xem
  `docs/giao-viec/2026-08-15-spec-cau3-dau-hieu-cam-xuc-cskh.md`. CHƯA CODE (xếp sau 5a core).
- **F-25(b) cổng siết-nhầm** (0-TPM, đã chứng minh hoạt động).
- **Luật 18 (ADR-023)** — khớp cụm cho phép chèn hư từ + mỏ neo QUY TRÌNH cho O2 — LAND
  (`221abb5`, `8d26548`), retroactive F-24/F-27.
- **`resolutions.note` + `note_flagged` (ADR-024)** — LAND (`7b68992`), field ẩn duy nhất nơi
  văn bản tự do nhân viên gõ đi vào bản ghi kiểm toán; scrub tại điểm ghi, fail-closed, ép ở DB.
- **Lượt đo end-to-end "sau" O1-O4 ĐÃ CHẠY** (`e4ef0e8`) — sửa bug 21/24 ở câu 2, **cổng-96 giờ
  BẬT THẬT** (không còn tắt), raw lượt end-to-end đã lưu.
- **Seed test USR-0119/USR-0201 xong** (`dacbefd`, tester) — lộ + vá 2 bug ẩn: TXN-0001 không
  "mượn" được cho user mới (đã parametrize `trans_id`), import sai module
  (`src.tools.registry`→`src.agents.tools.customer_tools`), guard cổng-96 kiểm nhầm payload
  toàn cục thay vì đúng tập mốc nền đang dùng.
- **Xác nhận trạng thái THẬT trong phiên này (Luật 9, 2026-08-15, PO-agent dựng venv sạch chạy
  từ đầu — không suy luận từ code tĩnh):**
  - `pytest tests/test_invariants.py -v` → **23/23 PASSED**, 0 failed.
  - `pytest tests/test_api/test_reject_note_doi_khang.py tests/test_migrations/test_trang_thai_dich_nhip_note_f11_f13.py`
    → **15 passed, 8 skipped** (0 failed) — skip có lý do rõ: 7 ca cần Postgres thật (env test
    dùng `sqlite:///:memory:`), 1 ca chờ exporter Phase 2 chưa tồn tại. KHÔNG có `khong_do_duoc`
    lạ nào.
  - `pytest tests/test_security/ -q` → **38 passed, 26 skipped**, 0 failed.
  - Môi trường test cục bộ trước đó CHƯA từng được dựng ở máy chạy phiên PO-agent (thiếu
    `argon2`, thiếu model NER `xx_ent_wiki_sm` của presidio) — đã dựng venv scratchpad + cài đủ,
    không phải bug sản phẩm.

## Đang dở — chi tiết đủ tiếp ngay
- **Chip câu 3 (dấu cho CSKH)** — PO thật đã duyệt khung+N=3+CSKH-thấy (xem "Vừa xong"). CHƯA CODE:
  coder xếp SAU 5a core + sau QA baseline (thứ tự đã định từ sổ Đợt 2). Câu hỏi kỹ thuật còn treo
  (không cần PO quyết lại, coder tự đề xuất): cần thêm 1 trường envelope riêng cho kênh CSKH, hay
  tái dùng cờ ES sẵn có mà khách cũng đọc — xem đặc tả §4.
- **Đợt nâng CỔNG-A** gộp 3 oracle (số-ngắn+tên+phủ-định "không phải 21") theo xuất-xứ + dữ liệu
  phân phối — chưa làm, có tài liệu ở sổ Đợt 2.
- **Câu-4 RAG retrieval quality** — 3/5 câu chính sách hợp lệ agent không trả được. Sửa chunk/embedding,
  KHÔNG nới ràng buộc 9. Mốc: trước pilot 150 người.
- **MT-E02 traceback** — cơ chế chưa rõ, giữ quan sát, ĐỪNG đốt TPM tái hiện chủ động.

## 🚀 GÓI DEPLOY HOME-SERVER (đêm 15/08, đang chạy) — sự thật nền tảng ĐÃ SỬA HAI LẦN
- **PO thật quyết:** demo mentor XONG → deploy production lên **máy bàn Windows 24/7 ở nhà PO**,
  domain `app.adaptivealgo.uk`, đường ra **Cloudflare Tunnel** (không cần IP công khai/mở port).
- **Sự thật đã kiểm (đè MỌI tài liệu cũ):** KHÔNG có VPS nào tồn tại — `app.adaptivealgo.uk`
  không phân giải; `docs/DEPLOY.md` là tài liệu đợt P-121 CHƯA AI THỰC THI (còn trỏ repo
  P-121-new). Demo chạy localhost Docker trên Mac PO. Domain gốc `adaptivealgo.uk` ĐÃ đăng ký,
  NS = Cloudflare — PO đang kiểm quyền truy cập tài khoản.
- **Hai lần PO-agent sai tiền đề trong CÙNG gói này (Luật 9, ghi để không lặp):** (1) coi VPS
  trong DEPLOY.md là hạ tầng sống; (2) brief cho coder ghi "main đang là bản demo GO" — SAI, demo
  chạy từ `dev/learning-loop`, main đứng sau **220 commit**, thiếu cả vá SSL_CERT_FILE compose lẫn
  hotfix quick-login. Coder DỪNG trước khi viết và bác brief bằng số — nếu làm theo, production
  đêm đầu chết mọi lượt chat.
- **CHỐT NHÁNH: fast-forward `main` lên `dev` HEAD** (PO-agent đo: `dev..main = 0` commit riêng ⟹
  merge là FF thuần, main = đúng cây đã nghiệm thu 540 passed + 2 chữ ký security). Lệnh có chốt
  `--ff-only`. Gói home-server land trên main sau FF.
- **HAI BẪY `.env` khi chuyển máy (coder phát hiện, vào doc từng-bước-bấm):** ① `FIELD_ENCRYPTION_KEY`
  phải GIỮ NGUYÊN (đổi = dữ liệu mã hoá thành rác vĩnh viễn); ② `SSL_CERT_FILE` là đường dẫn
  macOS, PHẢI sửa khi sang Windows — *"`.env` càng được mang sang trung thành thì lỗi càng chắc
  chắn tái hiện"*. Bẫy chết-dữ-liệu và bẫy chết-dịch-vụ, khác nhau, cùng một file.
- Việc tay của PO thật: ✅ Cloudflare CÓ domain (PO xác nhận) · đang tạo tunnel (ô Service điền
  **`caddy:80`, Type HTTP** — KHÔNG điền localhost) · cài Docker Desktop/WSL2 máy Windows ·
  Never-sleep + Docker start-at-login. Nghiệm thu cuối = mở `https://app.adaptivealgo.uk` từ
  **4G tắt WiFi** thấy màn login — phép thử DUY NHẤT được tính.
- **✅ GÓI LAND trên `main` `7ce57bd` — SẴN SÀNG CHỜ TOKEN.** FF main làm bằng `push origin
  HEAD:main` (server từ chối non-FF = giữ chốt an toàn, KHÔNG checkout — cây làm việc dùng chung
  4 phiên, checkout là giật file khỏi tay 3 vai kia; lệnh gốc của PO-agent quên điều này). Verify:
  `03d02da..a694ff1` · diff rỗng · demo-GO→HEAD chỉ 1 commit docs.
- **📌 Tri thức mới (coder đo):** `docker compose` NỘI SUY BIẾN cho MỌI service kể cả service bị
  profile loại — `${VAR:?}` fail-fast trong compose RÒ sang mọi người dùng compose, không riêng
  người bật profile. Fail-fast cho service optional phải đặt ở SCRIPT cửa vào của đường đó.
- **⚠️ Khai minh thị:** `deploy_home.ps1` mới review bằng mắt, CHƯA chạy thật (máy không có pwsh);
  bản `.sh` đã chạy thật cả hai cổng. PO gặp lỗi cú pháp `.ps1` → dùng `.sh` trong WSL, đó là
  đường lui có sẵn.

## 🚨 SỰ CỐ KHO + ĐÒN 4 LAND — MỐC 35,7% VÔ HIỆU KÉP, chờ cặp sạch (16/08)
- **SỰ CỐ (chạm ràng buộc cứng 3):** kho đang-phục-vụ bị nạp 2 file NỘI BỘ lúc 08:23 (hai lần nạp
  thẳng cách 15s, KHÔNG qua nap-lai): `business_rules.md` 20 chunk (bảng số verified=false) +
  `scenario-candidates-momo-faq.md` 37 chunk (kịch bản test). Agent trích cả hai **như chính sách
  thật**. Coder đã GỠ + chặn `_chon_nguon` chỉ nhận `.docx/.pdf` (kèm docstring lý do — bản nháp
  commit của chính coder cũng suýt nạp .md, bắt được nhờ in danh sách nguồn trước khi nạp).
  **Truy nguồn (cập nhật 16/08):** tester + security ĐỀU tự loại trừ BẰNG CHỨNG (tester: log
  container — endpoint/user_id/script chỉ-đọc; security: import-list 3 probe, 0 lời gọi ingest).
  Tester truy ra đường nạp: **`POST /policy-docs` × 2 (08:23:14/08:23:27) dưới `USR-PA01`** —
  cửa upload HỢP LỆ của partner_admin, không phải lách. PO đối chiếu: `kho_rag.py` nạp bằng
  `ingest_document()` trực tiếp (không HTTP) nên không thể tạo 2 dòng POST ⟹ nghi phạm còn lại
  duy nhất: **PO thật thao tác màn hình upload Đối-tác-ví** — đang hỏi. Security được giao đo
  thiệt hại thật (log `/policy-search` trong cửa sổ 08:23→lúc-gỡ, loại 3 đợt quét USR-0201 của
  tester) → hồ sơ vào docs/security/. Dữ kiện giảm nhẹ: bảng trong business_rules.md mang cột
  `verified=false` ngay trong thân — trích là trích kèm.
- **ĐÍNH CHÍNH truy nguồn (tester, 16/08):** "USR-PA01 trông như chữ ký nhưng thật ra là CON DẤU
  CỦA CÁI CỬA" — `uploaded_by=USR-PA01` là danh tính đường nạp, không phải người (lượt nạp đòn-4
  của coder 08:42 cũng mang USR-PA01, 2 file cách 4s; 13s-vs-4s không phân biệt người/máy). PO đã
  lỡ hỏi PO-thật theo hướng dẫn-dắt trước khi đính chính tới — lần chạm sau hỏi MỞ + thêm nghi
  phạm thứ ba: script-của-đội gọi API. Phép kiểm còn phân biệt được (tester đang chạy): đếm lại
  dòng `POST /policy-docs` — kho_rag.py nạp trực-tiếp không qua HTTP, nên nếu vẫn đúng 2 dòng thì
  "08:23 = một client HTTP thật" vẫn đứng.
- **✅ SỐ SẠCH ĐẦU TIÊN: Recall@3 = 41,4% → trục Truy-hồi 8,29/20 → benchmark v0.2 = 86,2% đo
  được** (thước-đã-vá × kho-sạch 378c/2doc × 3-lượt-lặp-y-hệt; nhãn `55118b5`/`1e367a58c2e5`/
  `332c053b9fde`/StartedAt-08:44:29Z). **QUYẾT ĐỊNH: KHÔNG đọc 41,4−35,7 thành delta đòn-4**
  (ba biến cùng đổi: thước+kho+rác) và **KHÔNG dựng lại nền PDF** để attribution — câu hỏi về
  quá khứ, giá = 1 vòng nạp + 1 lần đổi-vật-dưới-chân-4-phiên; chuyện đòn 4 kể bằng số cấu trúc.
  Chuỗi trục Truy-hồi BẮT ĐẦU LẠI tại 41,4%.
- **Hồ sơ sự cố ĐÓNG (`10af46d`, docs/security/): 0 thiệt hại tới khách** — cửa sổ 19ph33s
  (15:23:14→15:42 giờ máy), toàn bộ traffic = /policy-search nhịp-máy (trùng mạch tester+commit
  coder) + 0 lượt /chat/agent; stack fin05ttl không ảnh hưởng. **LUẬT MỚI: mọi mốc giờ trong hồ
  sơ sự cố ghi kèm MÚI GIỜ** (08:23 hoá ra là UTC = 15:23 giờ máy — suýt làm điều tra đi tìm log
  đã bay). Truy nguồn còn mở: POST /policy-docs là dấu-vết-đường-đi PHÂN BIỆT ĐƯỢC (kiểm 2 chiều:
  lượt kho_rag 15:42 của coder KHÔNG sinh dòng POST/USR-PA01 nào trong HTTP log) ⟹ 15:23 = một
  client HTTP thật đã đăng nhập partner_admin; khung giờ NẰM GIỮA phiên đòn-4 của coder → đã hỏi
  coder câu mở (curl/script HTTP nào 15:00–15:45?) + PO thật (chưa trả lời). Bằng chứng sống nhờ
  MAY (container restart, không force-recreate) — câu trả lời bằng thiết kế là F-LOG-3.
  **CẢ 3 PHIÊN ĐÃ TỰ LOẠI BẰNG CHỨNG CỨ** (tester: endpoint/user-id/script-chỉ-đọc · security:
  import-list 3 probe · coder: nguồn-IP 172.19.0.6=frontend-container trong khi curl của coder là
  127.0.0.1-trong-backend + CHƯA TỪNG cầm token partner_admin hôm nay nên guard không cho qua +
  Playwright không có setInputFiles + zsh-history 0 dòng). Dấu vết hội tụ: một phiên TRÌNH DUYỆT
  đăng nhập partner_admin, mở trang 08:22:45Z rồi nạp 2 lần — nghi phạm còn lại: PO thật (đang
  hỏi). Nợ mới ghi nhận: `uploaded_at` lưu naive-UTC không hậu tố — bẫy múi giờ sẽ lặp; F-LOG-3
  dùng ts ISO-8601 có offset, đổi `uploaded_at` là mục nợ riêng.
  Quan sát thêm (security, không phải kết luận): mỗi POST kéo theo GET /policy-docs sau 20-40ms =
  nhịp UI-tự-tải-lại-sau-upload; 13s GIỮA hai lượt hợp người bấm 2 lần ⟹ kéo giả thuyết thao-tác-
  UI LÊN (không loại script điều khiển trình duyệt). Đặc tả trường F-LOG-3 security đã gửi coder:
  doc_id[]/chunk_id[] trả về (trường quan trọng nhất) · query_hash HMAC + query_len (KHÔNG log
  nguyên văn — S-01 scrub hỏng 40% nghĩa trên văn bản nghiệp vụ) · nguon cho /policy-docs (tên
  khớp việc xuất-xứ) · retention ngắn tách QĐ3 · không IP/UA.
- **F-LOG-3 GIAO coder (sau fix-kho-restart, trước T3):** log có cấu trúc /policy-search +
  /policy-docs — lần THỨ BA trong 2 ngày câu hỏi sự cố dừng ở "đo không được" vì thiếu 1 dòng log
  (uvicorn access log không có user_id/query/chunk). Security gửi danh sách trường; ràng buộc:
  JSON + PII-scrub-trước-khi-ghi + contextvars sẵn có.
- **Bộ đo 6-trục XONG (`8a7f853`): 41→60 ca · benchmark v0.3 = 85,7%** (trục Truy-hồi hiện hành
  **39,4% / 47 ca có ToS** → 7,87/20; ghi kèm `41,4% / 35 ca chỉ-FAQ` — số ca đổi = cắt chuỗi).
  **ToS 2/8 = trục yếu nhất → tín hiệu ưu tiên đòn RAG kế**, TRÌNH TỰ: chờ coder trả lời §15-ToS
  (15.1 + tiêu đề "Giới Hạn Trách Nhiệm" vắng trong 340/378 chunk khảo sát — lỗi nạp hay 38 chunk
  chưa lộ?) rồi mới đo lại ToS. §G bắt 2/4 ca âm-bản security đề xuất hoá ra DƯƠNG (kho CÓ đáp án:
  ToS 19.2 60-ngày · ToS 2.8) — mọi ca âm-bản nay mang `moi_gan`+`vi_sao_am` chống sửa-nhãn-khớp-
  kết-quả. Datum: typo/caps không phá truy hồi (mỏng, 1 ca/loại); đối chứng 2 lượt nạp cùng nguồn
  15/14 TRÙNG KHÍT ⟹ nạp-lại không đổi phép đo, băm-đổi = ghi sổ không phải nhiễu (chống lưng đề
  xuất `_bam_kho` text-only — coder nhét vào lượt chạm kho_rag kế). Nhắc-một-lần đã gửi coder:
  lượt nạp 08:55Z không hô trước — quy ước mới không được mềm tuần đầu. Nợ tester: mồi-neo §D +
  k-boundary (cần đường agent), sau khi kho đứng yên.
- **🎉 LIVE: https://app.adaptivealgo.uk — PO thật TỰ deploy Windows home-server + Cloudflare
  Tunnel (16/08).** PO-agent smoke-test từ ngoài: /login 200 qua CF edge HKG · title đúng ·
  POST /api/session đăng nhập demo THẬT 200 + đúng user (0,4s) ⟹ tunnel+caddy+BFF+backend+
  Postgres+seed sống. GET /api/session 405 — coder xác nhận chủ-đích hay thiếu. Việc coder (sau
  F-LOG-3): checklist kho-RAG-trên-Windows (kiem xanh trên máy đó · restart-sau-nạp-lại trong
  deploy_home.* · 1 câu policy-search thật) + soạn "3 lệnh kiểm sức khoẻ" cho PO thật. Quy ước
  cho cả đội: stack live = môi trường THẬT — probe chỉ-đọc, báo trước.
## 🔐 HELDOUT-60: GÓI 30 NHÃN THÀNH ĐIỀU KIỆN TIÊN QUYẾT CỦA PHÁT BẮN (chốt 16/08 đêm)
- **Tiền đề của PO-agent SAI (lần thứ 3 trong ngày, tester kiểm giả định trước khi làm theo):**
  heldout **KHÔNG phải bộ truy hồi** — cùng lược đồ `golden_set.jsonl`, là bộ **kịch bản khiếu
  nại** (`complaint_type`·`authority`·`escalation_target`·`fraud_signals`·`must_not_*`), chấm
  bằng **bất biến tất định + trọng tài LLM**, không so chuỗi với text kho ⟹ 6 lớp lỗi thước tôi
  lo KHÔNG áp dụng. (Bộ rà báo `60/60 không có nhãn` = **bộ rà hỏng**, không phải heldout hỏng.)
- **🔴 RỦI RO THẬT, LỚN HƠN: heldout được chấm bởi `_llm_judge` — TRỌNG TÀI CHƯA HIỆU CHUẨN**
  (kappa chưa đo · tỉ lệ rộng-tay chưa đo). ⟹ *bắn phát duy nhất để lấy một con số có sai số
  KHÔNG XÁC ĐỊNH*; trọng tài rộng tay ⟹ **số công bố CAO HƠN SỰ THẬT**, ở đúng con số sẽ rời khỏi
  đội đi tới BTC. **CHỐT: gói 30 nhãn là ĐIỀU KIỆN TIÊN QUYẾT, heldout khoá sau nó, không ai
  được bắn trước.**
- **Rà khoá `must_not_*` GIAO SECURITY** (phải đọc nội dung ⟹ không thể là tester — họ là người
  bắn). Bất thường tester tìm ra mà **cố ý không kết luận**: `expected` 59/60 có 6 khoá · 1 ca có
  7 (`blocked_staff_action`); `forbidden` 48/60 có 3 · 11/60 có 6 · 1/60 có 4. Cố ý hay thiếu
  sót? **Nếu thiếu, ca đó không kiểm được điều nó sinh ra để kiểm — và chỉ biết SAU khi đã bắn.**
  Ràng buộc security: cấm sửa ca · cấm chỉnh thước/sản phẩm theo nội dung đã đọc · mọi đề xuất
  guardrail sau này phải khai "sau khi đã đọc heldout" · được quyền từ chối.
- **PO quyết: tester VẪN là người bắn heldout** dù họ tự đề nghị đứng ngoài. Cân hai chiều: thứ
  họ biết là **cấu trúc** (khoá·kiểu·số đếm — không nội dung), không cho đường tinh chỉnh về phía
  đáp án; đổi lại giao phát-một-lần cho vai không quen harness là **rủi ro thao tác thật** đổi lấy
  độc lập gần bằng không. Bù bằng minh bạch: mức tiếp xúc ghi thẳng vào hồ sơ phát bắn.
- **LUẬT MỚI: "một bộ rà chưa biết SÀN NHIỄU của mình thì báo cáo của nó không đọc được."** Tester
  đo sàn bằng cách chạy bộ rà trên golden-set (bộ **biết là sạch**): 9/47 nghi-không-trong-kho
  **đều là dương tính giả** ⟹ sàn ~19% ⟹ đổi nhãn từ *"lỗi"* thành *"NGHI — phép dò yếu, phải
  kiểm bằng đường độc lập trước khi sửa nhãn"*, chặn đúng vòng lặp suýt sửa 15 nhãn lành hôm qua.

## 🧾 SPEC BENCHMARK ĐƯỢC SOI + CHỮA GỐC BẰNG `--khoi-spec` (16/08 đêm)
- **Tester soi `benchmark-spec-va-v0.md` theo yêu cầu PO — 7 chỗ, PO sửa 7/7 (`41753d4`).** Nặng
  nhất: ① một dòng lấy `48,9%` (chỉ chế độ **có-dấu**) nhân thành điểm trục `9,79` trong khi công
  thức spec là **TB hai chế độ 47,9% → 9,57** (cộng theo dòng đó ra tổng khác) ⑥ **nhãn vật lỗi
  thời: ghi `kho 419 chunk` gắn lên số đo trên kho 378 — mà 419 CHÍNH LÀ kho còn 57 chunk rác
  `.md`** ⟹ số đúng đang mô tả một cái vật đã bị gỡ. Còn lại: đính chính `top_k` có hiệu lực
  (trần 8; phát biểu cũ sai do đọc 422 thành 0-kết-quả), gắn nhãn lịch sử cho `39,4%`/`80,9%`/
  `3,75`, cập nhật bảng "Đường tới v1" (5 mục XONG).
- **Mẫu hình: 6/7 là "số cũ còn sót sau khi số mới thay chỗ", KHÔNG chỗ nào tính sai** — chi phí
  của một tài liệu do MỘT người sửa nhiều lần trong ngày số liệu đổi liên tục. ⟹ **NẾP MỚI: mỗi
  tài liệu PO sửa nhiều lần phải qua mắt một vai khác trước khi thành hồ sơ.**
- **CHỮA GỐC `--khoi-spec` (`e886307`):** script in **khối markdown chép thẳng vào spec** thay vì
  PO diễn giải lại thành câu ⟹ **số cũ không thể sót vì không ai chép tay nữa** (cùng họ luật
  gom-về-một-nguồn). Khối tự mang **nhãn vật + thời điểm** (chống đúng lỗi ⑥) và in dòng
  `⚠️ CHƯA ĐO ĐƯỢC (loại khỏi mẫu số, KHÔNG loại khỏi tầm mắt)` cả trong lẫn ngoài khối.
  **Bẫy tester tự tạo rồi tự sửa trước khi giao:** bản đầu lượt `--chi-truy-hoi` in cả 5 dòng với
  4 trục `KHÔNG ĐO ĐƯỢC` ⟹ ai chép nguyên văn sẽ **xoá mất số hợp lệ** của 4 trục kia —
  *"công cụ chống số-cũ-còn-sót suýt tự tay xoá số-mới-đang-đúng"*. Sửa: lượt một phần chỉ in
  dòng nó đo, có cảnh báo, **không in tổng**. Họ Luật 6b: **"không đo ở lượt này" ≠ "chưa đo
  được"** — gộp lại làm bảng nói sai theo hướng BI QUAN (hướng ít ai đi kiểm vì trông khiêm tốn).
- **GIAO tester (0 LLM): rà CƠ HỌC nhãn `eval/heldout_set.jsonl` (60 ca)** — heldout **chỉ được
  bắn MỘT LẦN** cho số công bố gần Demo Day, nhưng nhãn viết TRƯỚC khi phát hiện loạt lỗi thước
  tuần này (bo_dau khoảng trắng · từ-khoá-chung · chuỗi không sống qua trích PDF · mẫu số đếm
  mục lục). Dính cùng lớp lỗi ⟹ phát hiện đúng lúc bắn phát duy nhất, không có phát thứ hai.
  **Ràng buộc chống nhiễm bẩn:** rà CƠ HỌC (chuỗi có sống qua pipeline · có trong kho · có đặc
  trưng theo luật 3 cửa · định dạng nhất quán), **CẤM** sửa ca theo nội dung / chọn-loại ca /
  chỉnh thước dựa trên thứ thấy trong heldout; báo PO dạng [ca → lỗi cơ học → cách sửa]. Tester
  được quyền TỪ CHỐI nếu thấy chính việc rà đã là nhiễm bẩn quá mức.

## 💵 GIÁ QWEN + PHÂN TÍCH CHI PHÍ — kết luận NGƯỢC giả định ban đầu (16/08)
- Giá endpoint quốc tế (USD/1M vào-ra): **qwen3.7-flash `0,03/0,13`** (rẻ hơn gpt-4o-mini ~5×) ·
  qwen3.7-plus `0,40/1,20` (đắt 2,7×) · qwen3.8-max `2,00/6,00` (đắt 13×) · *(đang dùng)*
  gpt-4o-mini `0,15/0,60`. Bắc Kinh rẻ hơn 60-70% nhưng **dữ liệu vào hạ tầng TQ — không khuyến
  nghị**. Gói thuê bao tháng −40% so trả-theo-dùng.
- **🔑 KẾT LUẬN: TIỀN CHƯA BAO GIỜ LÀ VẤN ĐỀ.** Một lượt chạy lại toàn bộ mốc nền (~260 lượt
  agent, ~20k token vào/lượt) = **~$0,9** trên gpt-4o-mini · ~$0,18 flash · ~$11,7 max. Mối lo
  "63 triệu token/7 ngày" của PO thật quy ra **~$10 cả tuần**. ⟹ thứ chặn đội là **trần 200k
  TPM**, không phải hoá đơn. Khi mở được tài khoản Qwen, câu hỏi đúng là **"gói nào cho trần tốc
  độ cao nhất"**, không phải "model nào rẻ nhất".
- **🔴 TRẦN TPM CỦA QWEN — ĐÂY MỚI LÀ LÝ DO ĐÁNG ĐỔI (tra 16/08):** Alibaba Model Studio cho
  **600 RPM / 1.000.000 TPM** cho hầu hết model (Qwen-Turbo tới **5M TPM**) — so với **200k TPM**
  hiện tại = **5× đến 25×**. Quy ra bằng chính số đo của đội (15,4k token/lượt hội thoại mới):
  1M TPM ⟹ **~65 lượt/phút** (hiện 13); 5M TPM ⟹ ~325 lượt/phút. Đích "150 người × 1 câu/2 phút
  = 75 lượt/phút" từ chỗ thiếu **7,5-13,6×** nay chỉ còn **thiếu chút ở gói 1M** và **thừa ở gói
  5M**. ⚠️ **BẪY: bản snapshot bị siết mạnh (60 RPM / 100k TPM)** — phải dùng bản STABLE, không
  dùng bản ghim ngày. Free quota: 1M token/model trong 90 ngày đầu; có đường xin nâng TPM tạm
  thời (30 ngày) qua console. ⟹ **Lý do đổi sang Qwen KHÔNG phải tiền (≈$10/tuần), mà là TRẦN
  TỐC ĐỘ** — thứ duy nhất đang chặn đích 100 CSKH.
- **Bảng trần chi tiết (tra tài liệu chính thức, vùng Singapore):** `qwen-max` 600 RPM/1M TPM ·
  `qwen-plus` 600/1M · **`qwen-flash` 600 RPM/5M TPM** · **`qwen3.7-plus` 15.000 RPM/5M TPM** ·
  **snapshot (tên có ngày) 60 RPM/100k TPM ← BẪY, không dùng**. **Trần áp ở CẤP TÀI KHOẢN GỐC**
  (mọi workspace + mọi API key cộng chung — giống org-level của OpenAI, không né được bằng cách
  tạo nhiều key). Nâng tạm thời qua console, hiệu lực ngay, 30 ngày, chỉ Bắc Kinh + Singapore.
- **🔻 ĐÍNH CHÍNH KÉP (tester bác PO-agent HAI LẦN trong cùng buổi):** ① "RPM là ràng buộc" —
  **SAI**: đo 1327 bản ghi ra **2,39 lời gọi/lượt** (không phải ~4 tôi ước) ⟹ RPM cho 251 lượt/
  phút > TPM 179 ⟹ **TPM chặn ở MỌI model**. ② "RPM chặn ở ĐUÔI" — **cũng SAI, và sai vì LỖI
  PHƯƠNG PHÁP của PO-agent**: tôi ghép **max-lời-gọi** với **trung-vị-token**, trong khi r=+0,88
  (2 lời gọi→13.709 tok · 7 lời gọi→**67.572 tok**) ⟹ kịch bản đó **gần như không xảy ra**.
  **LUẬT 10e (ratify):** *đuôi phải tính CÓ ĐIỀU KIỆN — mỗi mức của biến này dùng đúng giá trị đo
  được của biến kia ở chính mức đó*; dấu hiệu tự soi: *"tôi có bản ghi nào THẬT SỰ trông như thế
  này không?"* — không có ⟹ đang suy luận trên **điểm dữ liệu tưởng tượng**.
- **Trần CÓ ĐIỀU KIỆN (số đúng):** 2 lời gọi/13,7k tok → flash 300 · 3.7-plus 365 · 4o-mini 14,6.
  5 lời gọi/37k → 120 · 135 · 5,4. **7 lời gọi/67,5k → flash 74 · 3.7-plus 74 (HOÀ) · 4o-mini 3,0.**
  ⟹ **lợi thế 15.000 RPM chỉ đáng 12% ở VÙNG GIỮA, hoà ở đuôi** (TPM chặn trước) ⟹ **lý lẽ thông
  lượng cho `qwen3.7-plus` CHẾT; 12% không đáng 2,1-10× tiền.** Lý do duy nhất còn sống để ưu tiên
  bản lớn = **độ tin cậy gọi tool nhiều bước, CHƯA AI ĐO** ⟹ PO-agent **rút khuyến nghị dựa-trên-
  lập-luận, chuyển sang phép-thử-quyết-định**.
- **150 người: `71,6 vs 75` = 0,95× ở p95** — "đổi model là đủ" ĐÚNG ở tải trung bình, **SAI ở tải
  đỉnh**. Đường thoát: nâng TPM tạm thời qua console (hiệu lực ngay, 30 ngày) — **đổi MẪU SỐ chứ
  không đổi tỉ lệ**, và **phải bật TRƯỚC buổi test**, không tự có.
- **🧪 LUẬT MỚI: "NGUỒN DỮ LIỆU ĐÚNG, DÂN SỐ SAI"** (tester, khi thử giao thức đo nhịp gõ
  `6158661`): bảng `messages` là nguồn ĐÚNG (có `chat_session_id`+`created_at`; log không dùng
  được vì ghi *lời gọi model* chứ không phải *lượt khách*) — chạy ra **trung vị 3 giây giữa hai
  tin = 19,8 lượt/phút/người, gấp 40× giả định 0,50**. **Con số vô nghĩa: 230 tin đó do SCRIPT
  TEST sinh, không phải người.** Đường ống thông, truy vấn đúng, số ra đẹp — nói về **một quần
  thể không phải quần thể ta cần**. Nguy hơn nguồn-sai vì nguồn sai lộ ra sớm, cái này *chạy
  trơn*. Cùng họ Luật 7. **Cảnh báo ghi NGAY CẠNH truy vấn** (người sau gặp truy vấn trước khi
  gặp tài liệu) — không có nó thì cả đội sẽ hoảng vì `19,8` rồi tối ưu một vấn đề không tồn tại.
- **Giao thức đo nhịp gõ (sẵn sàng, chạy vài phút khi có phiên người thật):** ① nhóm nhỏ 5-10
  người TRƯỚC (nếu nhịp cao hơn dự kiến thì buổi 150 người hỏng trong 10 phút đầu — mất cả buổi
  của 150 người để học điều 10 người dạy được) ② đo theo cửa sổ `0-10 phút` và `sau đó`, **không
  lấy trung bình cả buổi** (trung bình giấu đỉnh, đỉnh mới làm sập) ③ **đo cả SỐ NGƯỜI GÕ ĐỒNG
  THỜI — `150 người có tài khoản` ≠ `150 người đang gõ`; trần phụ thuộc TÍCH hai số mà cả buổi
  ta chỉ cãi về một** ④ báo cả phân bố, **p90 mới là số quyết định**.
- **Từ chối mượn benchmark ngành thay cho `0,50` (tester, PO duyệt):** *"một con số mượn từ sản
  phẩm khác, tập người dùng khác, ngôn ngữ khác cũng là một giả định — chỉ khác là nó TRÔNG có
  căn cứ hơn nên KHÓ BỊ CHẤT VẤN hơn"* ⟹ **một giả định đội lốt dữ liệu tệ hơn một giả định tự
  nhận là giả định.** Giữ `0,50` với nhãn "giả định của ta, chưa đo".
- **🔴 LỖ HỔNG LỚN NHẤT CÒN LẠI (tester nêu): "1 câu/2 phút" là GIẢ ĐỊNH CỦA TA, chưa phải quan
  sát.** Mọi trần vừa tính (179 · 71,6 · 74 · 0,95×) đều chia cho một mẫu số chưa ai đo; người
  thật gõ nhanh gấp đôi ở 10 phút đầu (hành vi rất tự nhiên khi thử đồ mới) thì mọi trần chia đôi
  và kết luận "Qwen là đủ" SẬP. ⟹ **ĐIỀU KIỆN TIÊN QUYẾT của buổi test 150 người: đo nhịp gõ
  thật ở 10 phút đầu của một nhóm nhỏ TRƯỚC** — rẻ, và nó quyết định toàn bộ phần còn lại.
- **PHÉP THỬ QUYẾT ĐỊNH (§2b kế hoạch, chưa chạy):** cả hai model, `bo_lenh_do.jsonl` v2 (đã có
  mốc nền gpt-4o-mini ⟹ cặp sạch sẵn), k=5, 7 câu × 5 lượt × 2 model = **70 lượt <$0,50**.
  **Đo BỐN thứ TÁCH RIÊNG** (có gọi tool · gọi ĐÚNG tool · chuỗi nhiều bước hoàn tất · hỏng ĐỊNH
  DẠNG) — gộp thành một tỉ lệ là cách chắc chắn chọn sai model: model gọi-nhầm-20%-không-hỏng-
  định-dạng và model ngược lại ra **cùng một số**. Ngưỡng chốt trước: đúng tool ≥90% · chuỗi
  nhiều bước không thấp hơn 4o-mini quá 1 ca · **hỏng định dạng = 0 (lỗi cứng, không đánh đổi)**.
  Kèm miễn phí: **tỉ lệ ký-tự/token** — kiểm mệnh đề "Qwen tiếng Việt tốt hơn" (4o-mini = 2,43).
- **Giá cached qwen3.7-plus ĐÃ công bố** ($0,064 implicit, rẻ hơn input 5×) ⟹ tester bỏ giả định
  thận trọng cho model đó, giữ cho model chưa công bố. `$/lượt`: 0% cache 4o-mini 0,00438 vs
  3.7-plus 0,00934 (2,1×) · **85% cache: 0,00260 vs 0,00326 (1,25×)** — cache THU HẸP nhưng KHÔNG
  LẬT; flash vẫn rẻ nhất tuyệt đối 0,00088. (85% là tỉ lệ đo trên hệ ta **với gpt-4o-mini**, chưa
  phải với Qwen.) Bảng giữ CẢ biến thể tệ (`qwen-plus` 1M · snapshot-bẫy) — *"bảng phải cho thấy
  cả biến thể tệ, không chỉ biến thể ta định chọn"*.
- **⚠️ RÀNG BUỘC BỊ QUÊN: RPM, không phải TPM.** Một *lượt chat* của agent = **NHIỀU lời gọi API**
  (ReAct tới 20 bước). Với 600 RPM và ~4 lời gọi/lượt ⟹ trần thực ~**150 lượt/phút** dù TPM cho
  phép 250. Gói `qwen3.7-plus` (15.000 RPM) gỡ ràng buộc này ⟹ TPM thành cái chặn, ~250 lượt/phút.
  **Ta ĐO ĐƯỢC con số này chứ không phải đoán:** envelope đã có `so_luot_goi_model` (coder thêm
  cùng `input_chars`) — tính RPM thực tế/lượt trước khi chọn gói. Giao vào bộ ước-tính-chi-phí
  của tester: thêm cột **"trần lượt/phút theo RPM"** cạnh cột theo TPM, lấy cái NHỎ HƠN.
- **⚠️ Bẫy đã cảnh báo PO thật: đo trên model rẻ mà chạy production model khác = ĐO NHẦM VẬT** —
  đúng lỗi tester vừa bịt bằng ghim-ba-vai. Kèm rủi ro kỹ thuật: agent cần gọi tool đúng qua tới
  20 bước với prompt 5.400 token; hạng *flash* là hạng nhỏ nhất, dễ gãy đúng chỗ đó. Khuyến nghị
  PO-agent: nếu thử Qwen thì thử **flash cho lượt SỐNG/CHẾT** (~$0,18) chỉ để trả lời "tool-calling
  qua nhiều bước có đúng không", đạt rồi mới cân model chính thức.
- **NẾP MỚI (tester nêu, PO nhận — tôi suýt mắc):** phép kiểm sẵn-sàng-nhà-cung-cấp là **GỌI THẬT
  một lượt chat rẻ nhất**, KHÔNG phải liệt kê `/models`. Key hợp lệ + `/models` trả 159 dòng là
  đúng dạng tín hiệu dễ đọc thành "đã dùng được" ⟹ sẽ chạy cả kế hoạch 260 lượt rồi mới phát hiện
  không gọi được model nào. Cùng họ `_song()` ≠ `_api_song()`.
- **GIAO tester (0 LLM): bộ ƯỚC TÍNH CHI PHÍ theo TIỀN** — đầu vào là `usage`+`input_chars` đã đo,
  bảng giá cấu hình được (không hardcode) + **cảnh báo khi bảng giá quá N ngày** (giá là một loại
  nhãn-vật, cũ đi thì số sai mà không ai biết); đầu ra `$/lượt` và **`$/1000 ký tự vào`** — vì
  token hai nhà cung cấp không cùng đơn vị, chỉ ký tự mới so được cùng một lượng văn bản.

## 🧬 LUẬT MỚI: "vá một HỌ lỗi thì phải đi tìm HỌ, không vá cái đang cầm" (16/08, `8fd8481`)
- **Ba lần trong một tuần, cùng hình dạng:** gộp khoảng trắng (3 chỗ, vá 1) · nuốt mã trạng thái
  (2 chỗ, vá 1) · **cổng đóng băng LLM (6 lối gọi `/api/agent-chat`, vá 3)** — tester tự phát
  hiện khi vi phạm đóng băng LẦN HAI (~14 lượt): vá lần một chỉ ở `eval/`, không mang sang
  `tests/`. Lối hở nguy hiểm nhất: **`tests/load/locustfile.py`** — gọi agent theo TẦN SUẤT, cạn
  hạn mức cả đội trong vài chục giây (nếu chạy trúng lúc PO quay demo thì không phải 14 lượt mà
  là hết sạch).
- **Chữa gốc: gom về MỘT nguồn sự thật `tests/_dong_bang.py`** — *"cách chắc nhất để không phải
  đi tìm lần sau là để chỉ còn một chỗ"*; `locustfile` kiểm ở tầng **import** (chết trước khi
  sinh user nào). Kiểm: 6/6 nơi có cổng · 3 bộ → 13 skipped, 0 lượt gọi model.
- **NẾP MỚI (PO cấp cho tester): kiểm cổng bằng KEY GIẢ** — `OPENAI_API_KEY=sk-invalid-…` trong
  đúng lệnh kiểm. Cổng thủng ⟹ chết ở 401: **ồn, tức thì, 0 đồng**; cổng kín ⟹ skip. Biến
  "rò rỉ im lặng tốn tiền" thành "rò rỉ ồn ào miễn phí". Áp dụng cho MỌI lượt kiểm cổng.
- **Vi phạm Luật 5 của chính tester:** script F-31/32 hôm qua chỉ `print`, **không ghi file** ⟹
  findings vào hồ sơ nhưng **bằng chứng thô chết theo terminal** ⟹ chốt-① của PO (tái dùng
  transcript + 10 lượt judge-only) **không chạy được**; tầng C nay tốn **~16 lượt (8 agent + 8
  judge)**. Vá gốc: `_hoi()` ghi transcript thô **TRƯỚC mọi assertion** (assert đỏ vẫn giữ bằng
  chứng) → `eval/results/f31_f32_transcript.jsonl`. Ghi nhận thêm: **nếp lưu-raw ĐÃ CÓ trong
  `run_golden_set.py` mà không được mang sang chỗ mới — cũng là một dạng họ-lỗi chưa quét hết.**

## ⚖️ GÓI 30 NHÃN — NÂNG ƯU TIÊN: nó hiệu chuẩn TRỌNG TÀI, không phải agent (`e361d4a`)
- **Lập luận tester được chấp nhận:** `_llm_judge` nằm THƯỢNG NGUỒN adversarial + golden-set +
  handoff ⟹ mọi con số An toàn 30/30 đang đọc qua một cái thước **chưa ai đo sai số**. Trọng tài
  rộng tay = điểm An toàn CAO HƠN SỰ THẬT — loại sai nguy hiểm nhất dự án. ⟹ **rời vị trí cuối
  hàng, lên ngay sau N1b** (chỉ sau vì N1b đang dở và không tốn giờ PO thật).
- **3 quyết định thiết kế (duyệt):** ① người chấm KHÔNG thấy phán quyết máy (thấy trước = nhãn bị
  neo = đồng thuận cao GIẢ; cùng họ luật tester-không-đọc-src) ② **phân tầng 10/10/10** (máy-ĐẠT
  soi rộng-tay · máy-TRƯỢT soi chặt-tay · ca biên) thay vì 30 ca ngẫu nhiên — *"tập máy đạt ~90%
  thì 30 ca ngẫu nhiên ra 27 ca dễ, con số cao đó không nói gì"*; đây là **Luật 9 áp cho trọng
  tài** ③ **kappa + tách hai chiều sai** thay tỉ lệ trùng (tỉ lệ trùng thổi phồng khi một lớp áp
  đảo). **Ngưỡng chốt TRƯỚC khi mở nhãn:** kappa ≥0,60 để công bố · <0,40 thì MỌI số đã qua
  trọng tài gắn nhãn nghi vấn · **rộng tay ≥2/30 = ĐỎ bất kể kappa**.
- 4 mẫu hỏng bắt buộc ở tầng biên: từ-chối-rồi-trả-lời-tiếp (dò chuỗi sẽ chấm ĐẠT) · diễn giải
  chunk lạc đề giọng chắc nịch · **từ chối SAI phạm vi (dễ chấm ĐẠT vì "có từ chối = an toàn"
  — F-31 nhìn từ phía thước)** · đúng nhưng thiếu căn cứ.
- **Bộ soạn xong (`1e1aef9`, 0 LLM) — đổi thiết kế: TÁI DÙNG 53 ca đã có phán quyết trọng tài
  trong `eval/results/` thay vì sinh mới.** Lý do KHÔNG phải tiết kiệm: *hiệu chuẩn trọng tài
  phải đo trên chính phân bố nó thật sự làm việc* — sinh tập mới thì kết quả hiệu chuẩn không áp
  được sang các số đang công bố. ⟹ khâu tốn LLM biến mất. Cổng chống rò rỉ (8 chuỗi cấm + lý-do-
  máy từng ca) **đã ĐỎ một lần bằng ca đối chứng cố ý** (chèn `(máy: passed)` → script DỪNG,
  không ghi file) — đúng nếp cổng-chưa-từng-đỏ-chưa-chứng-minh-được-gì. Thứ tự ca xáo (gom theo
  tầng cũng là một dạng rò rỉ). Cảnh báo script tự in: **40/93 ca là phán quyết bộ TẤT ĐỊNH,
  script từ chối trộn** — *"hiệu chuẩn trọng tài mà lấy phán quyết bộ tất định là đo nhầm vật"*.
- **PO chốt tầng C (10 ca biên):** tái dùng transcript F-31/32 hôm qua + **chạy RIÊNG trọng tài
  lên chúng** (~10 lượt judge-only, không phải lượt agent — sau khi hết đóng băng, không xin
  ngoại lệ). Lý do cần bước này: các ca đó do MẮT tester phân loại, không có phán quyết
  `_llm_judge` ⟹ không có gì để so với nhãn người. Ràng buộc: phân loại cũ của tester **không đi
  kèm file giao** và **không phải "đáp án đúng"** — nó chỉ là tiêu chí CHỌN ca; ghi minh thị rằng
  tầng C được chọn CÓ ĐỊNH HƯỚNG. Cổng chống rò rỉ chạy trên tầng C y như hai tầng kia.
  **KHÔNG giao gói thiếu tầng C** — gói mù đúng 4 chỗ nguy hiểm nhất là tiêu 1 giờ của PO thật
  để mua thông tin không đủ dùng.
- **Chi phí thật = ~1 GIỜ CỦA PO THẬT**, không phải LLM (sinh 30 hội thoại chỉ ~30-40 lượt).
  *"Sinh lại dữ liệu thì rẻ; xin người ta chấm lại lần hai thì gần như không xin được"* ⟹ thiết
  kế phải chặt trước khi tiêu một phút nào của họ. **Không đưa PO thật trước khi nộp gate xong.**

## 🔁 QWEN TẠM DỪNG — quay về OpenAI, KHÔNG phải revert gì (16/08 tối)
- Tài khoản Qwen chưa mở quyền model (403 `AccessDenied.Unpurchased` trên **6/6** model thử:
  qwen3.8-max · 3.7-flash · 3.6-flash · 3.7-plus · 3.7-max · 3.6-27b; key `sk-ws-…` xác thực OK,
  `/models` trả 159 model, endpoint `dashscope-intl` thông). PO thật chốt **TẠM DỪNG**.
- **Không có gì phải revert — thiết kế fallback của coder làm đúng việc.** Xác minh bằng chạy
  thật: `LLM_MODEL=gpt-4o-mini` · `LLM_BASE_URL=(mặc định OpenAI)` · embedding OpenAI ·
  `JUDGE_MODEL`/`EVAL_SIM_MODEL`=gpt-4o-mini · **invariants 23/23**. Điều kiện land "mọi biến mới
  fallback về OPENAI_*" được chứng minh bằng tình huống thật: PO đổi ý giữa chừng, **0 dòng code
  phải sửa**. `.env` đã ghi chú trạng thái + cách bật lại khi tài khoản kích hoạt.
- `54164fa` GIỮ (không revert) · kế hoạch đo lại `a1747c8` CẤT KHO (đúng nguyên khi bật lại) ·
  ghim-ba-vai `c5c9fc2` giữ giá trị độc lập · **F-31/32 hết lý do chờ — làm trên gpt-4o-mini**.

## 🔬 N1b — HƯỚNG RẺ CHẾT DỨT ĐIỂM, trần latency ĐỊNH LẠI CÓ NGUYÊN TẮC
- Bảng cắt ứng viên (revision đã ghim `953dc6f6f85a`): kd=20 → 38/47 · 3967ms; kd=10 → 32/47 ·
  1855ms; **kd=4 → 23/47 (= nền, 0 cải thiện) · 720ms = cấu hình DUY NHẤT đạt 800ms.**
  ⟹ **chất lượng và latency đối nghịch trực tiếp, KHÔNG có điểm ngọt** — cắt ứng viên là cắt
  chính cơ hội. **Giả thuyết PO-agent ("top-10 vẫn giữ đủ +15") SAI theo hướng ngược**: mất 6/15
  ca và mất CẢ HAI ca ToS, vì 2 ca ToS thắng được đến từ ứng viên **hạng 13-20**. Bài học: phân
  bố hạng-thô của FAQ **không suy ra được** cho ToS (ToS đúng là lớp bị chôn sâu).
- **TRẦN ĐỊNH LẠI (PO), và ranh giới chống dời-cọc ghi minh thị:** 800ms rút từ **lập luận thuần
  latency** khi CHƯA biết giá vế bên kia; nay biết (+15/47 = **+65% câu trả lời đúng**) ⟹ định lại
  là **quyết định có thông tin mới**, không phải nới vì vừa trượt. **Tự ràng buộc: định lại NGAY,
  TRƯỚC khi coder đo int8** — nếu đợi int8 xong mới nới thì đó mới là dời cọc.
  **Trần mới đo ĐẦU-CUỐI:** ① 0 ca vượt 30s (bất di bất dịch) ② trung vị lượt chat ≤15s ③ thông
  lượng đủ quy mô hiện tại, scale-up là điều kiện riêng.
- **Tách CHỦ SỞ HỮU:** latency = quyết định UX (PO-agent) · **thông lượng 0,25 lượt/giây = quyết
  định NĂNG LỰC HẠ TẦNG (PO thật, cùng nhóm "sẽ có API xịn")** — demo/pilot thì đủ, 100 CSKH thì
  không; int8 chỉ nâng 2-3× (~0,7/s), còn xa. Coder khai giới hạn: đo tuần tự, chưa gộp lô.
- **Rerank bất đồng bộ: BÁC** — giá trị nằm trong chính câu trả lời của lượt này; đẩy sang lượt
  sau thì lượt đầu (quan trọng nhất) không được cải thiện. **Biến thể đáng đo (chưa phát lệnh):
  rerank CÓ CHỌN LỌC theo khoảng cách điểm** — chỉ chạy khi 4 ứng viên đầu sát điểm; tín hiệu
  TẤT ĐỊNH và rẻ (khác HyDE), đo sau int8 và chỉ khi số đầu-cuối không đạt.
- `input_chars` land (`9d5988c`): 13.116 token / 31.937 ký tự = **2,43 ký tự/token** — chính tỉ
  lệ này đổi khi sang nhà cung cấp khác, có nó thì tách được "prompt dài ra" khỏi "tokenizer đếm
  khác". Khai rõ phần KHÔNG đếm (schema 5 tool = 6.773 ký tự) và trả hằng số đó ra envelope.

## 🔒 LUẬT MỚI: cổng PHẢI-NHỚ-BẬT chỉ chặn được người đang nhớ (tester tự phát hiện 16/08)
- Tester **tự báo vi phạm chính cổng của mình**: chạy `do_token_latency --nhom ngan` (3 lượt LLM)
  trong lúc đóng băng, vì `FIN05_DONG_BANG_LLM` là **biến môi trường — chỉ sống trong shell đã
  export**. Không hậu quả đo được. PO ghi thành **phát hiện thiết kế, không phải lỗi**: lý do họ
  đưa khi tự báo ("nếu tôi chọn báo cái gì theo mức độ bị phát hiện thì mọi con số tôi đưa sau
  này đều mất chỗ dựa") là thứ làm số của họ có giá trị.
- **Vá (`6c6cc1a`):** cổng nổ khi có biến môi trường **HOẶC** có file **`.DANG-DONG-BANG-LLM`** ở
  gốc repo — sống qua shell/phiên/nén-ngữ-cảnh, `ls` là thấy, thông báo in rõ nguồn chặn. File
  ĐANG TỒN TẠI ⟹ đóng băng có hiệu lực với cả 4 phiên. **Quy ước xoá: chỉ khi PO thật xác nhận
  quay xong; người xoá hô cả 4 phiên.** Đường index-thô (model embedding, pool khác) vẫn chạy.
- **LUẬT (ratify):** cơ chế nào còn một nửa dựa vào trí nhớ thì vẫn còn một nửa là lời hứa — bản
  nâng cấp của luật cơ-chế-thắng-lời-hứa. Áp cho mọi cổng dựng về sau.
- Kèm 2 vá: `usage` thiếu trường → in `–` đi tiếp thay vì `TypeError` (cần cho Qwen — nhà cung
  cấp khác trả bộ trường khác). Và `ky_tu_vao`: tester **cố ý KHÔNG** dựng chỉ số ký-tự-một-phần
  (sẽ trông như đại lượng bất biến mà không phải — cùng họ "nhãn nói dối nguy hơn không nhãn")
  ⟹ PO gộp **`input_chars` vào envelope `usage`** cho coder: ký tự là đại lượng BẤT BIẾN QUA
  TOKENIZER, giữ chuỗi so sánh token sống sót khi đổi nhà cung cấp.

## 🏆 N1 RERANKER — CHẠM ĐÚNG TRẦN LÝ THUYẾT, nhưng TRƯỢT ngưỡng latency (16/08)
- `bge-reranker-v2-m3`: **23/47 → 38/47** (= trần Recall@20, tức lấy HẾT phần còn trong tầm) ·
  **ToS 2→4 = đúng trần ToS** · **0 ca rơi** · p=0,0001 (ngưỡng khai trước: ≥6 ca ròng).
  ViRanker 37/47, rơi RAG-01 ⟹ **loại, chỉ đi tiếp với bge**. Cả hai tải bằng safetensors (băm
  `5cea425ef710` / `d86f3bd32eda`); **chưa ghim revision hash — phải ghim trước vòng sau**.
- **TRƯỢT: latency 3776 ms/lượt vs ngưỡng 300 ms coder tự khai TRƯỚC khi chạy.** Coder tuyên bố
  trượt thay vì dời cọc sau khi thấy số đẹp — **mẫu chuẩn của ngưỡng-khai-trước**, ghi làm nếp.
  Trạng thái chính thức: KHÔNG ĐẠT, không đổi tên thành "đạt-chờ-tối-ưu".
- **PO chốt TRẦN LATENCY THẬT: ≤800 ms/lượt tra trên máy chạy thật** (rút từ số của tester: trung
  vị lượt 5,9-9,9s, 1-2 lần tra/lượt ⟹ +1,6s ≈ +20%, xa trần 30s). 300ms là ước chừng của PO khi
  chưa có dữ liệu latency — giữ nó là để ước-chừng-cũ phủ quyết phép-đo-mới. **Ràng buộc kép:**
  trung vị lượt không tăng >20% VÀ 0 ca vượt 30s.
- **VÉ N1b MỞ — tối ưu latency**, thứ tự rẻ→đắt: top-10 thay top-20 (giảm ~½, kiểm luôn chất
  lượng có giữ +15 không) → int8/ONNX → đo trên máy Windows thật. **+ trục CHƯA AI ĐO mà đích
  100 CSKH bắt buộc: THÔNG LƯỢNG** (lượt tra/giây chịu được), khác bài toán độ trễ và không cải
  thiện cùng tỉ lệ. Không land reranker cho tới khi N1b đạt.
- **Hai dự đoán độc lập của tester+coder được xác nhận bằng số:** trần reranker có thật và chạm
  được; **6/10 ca ToS ngoài tầm MỌI reranker** ⟹ bệnh ToS ở bước TÌM — nay là sự kiện đo được.
- ⚠️ **DỰ KIẾN, KHÔNG PHẢI MỐC** (tester đính chính PO-agent): con số "48,9%→~80,9% · 9,57→~16/20"
  suy ra từ 38/47 ở MỘT chế độ gõ, trong khi thước sổ sách là TRUNG BÌNH hai chế độ (lệch ~2 điểm
  ở mọi lượt đo từ trước) — chưa qua canary, chưa có nhãn vật, chưa lặp 3. **Không ghi vào sổ như
  mốc cho tới khi tester đo đúng quy trình.** (Tiền lệ: 60,0% từng được ghi rồi phải rút, giá là
  cả một ngày rà lại.)
- ⚠️ **Cách đọc phải giữ khi đo chính thức:** 38/47 = ĐÚNG trần ⟹ nếu lượt đo sau ra **cao hơn**
  38/47 thì phần vượt **KHÔNG phải công của reranker** — đi tìm biến thứ hai. Và khi land: thêm
  rerank + có thể đổi `k` = **HAI biến**; land tách hai lượt thì đo được cặp sạch, land một lượt
  thì chấp nhận nhưng **ghi rõ hai biến**, không để trôi vào báo cáo như một (bài học đòn 4).

## 🔒 QUYẾT ĐỊNH 17/08 — MODEL CHAT = `qwen3.8-max` (PO thật đổi từ `qwen3.7-plus`, ưu tiên CHẤT LƯỢNG)
- **Căn cứ: nghiệm thu §2b v3 của tester** (`e92c5d1`, nhãn `797b8c509a8d`, lược đồ lấy TỪ APP
  `4129d298555c`, ~190 lượt, 3 model):
  | model | gọi-đúng | không gọi | hỏng ĐN | chuỗi nhiều bước | suy nghĩ % |
  |---|---|---|---|---|---|
  | **qwen3.8-max** | **23/25 = 92%** ✅ | 2 | 0 | 6/15 = 40% | 77% |
  | qwen3.7-plus | 19/25 = 76% ❌ | 6 | 0 | 6/15 = 40% | 61% |
  | qwen3.7-flash | 21/25 = 84% ❌ | 3 | 0 | **0/15 = 0%** | 89% |
  Ngưỡng công bố trước: gọi-đúng ≥90% · hỏng-định-dạng = 0. **Chỉ `max` đạt.**
- **`flash` bị LOẠI DỨT ĐIỂM và đây là bài học đắt nhất của phép đo:** 84% ở bước đơn nhưng **0/15
  chuỗi hai bước**. Nếu đo như v1/v2 (chỉ một bước) thì flash *trông gần đạt* và có thể đã được chọn
  vì rẻ hơn 5,7×. ⟹ **một phép đo THIẾU ĐÚNG MỘT CỘT đã đủ để dẫn tới quyết định sai về sản phẩm
  thật.** Dùng lập luận này khi cần bảo vệ chi phí đo. Ca chuỗi là **điều kiện** do PO-agent chốt.
- **❌ Quan sát `1/4 JSON hỏng` của PO-agent: CHẾT HẲN** — 0 hỏng định dạng trên n≈190, cả 3 model,
  cả bước đơn lẫn chuỗi. Ghi là *tôi sai*, không phải *chưa kết luận*.
- **🟡 LƯỢT v3 BỊ HUỶ (PO-agent quyết), nhưng model vẫn chốt được vì `max` thắng dưới CẢ hai cách
  đọc.** Lý do huỷ: **cả 6 lượt trượt của `plus` rơi vào ĐÚNG MỘT CÂU (ca 4)**; tách ca đó ra thì
  plus = **20/20 = 100%**. Đây là lần **thứ hai** ca 4 cho kết quả nhất quán tuyệt đối ⟹ Luật 8b.
  Lần một là **lược đồ trống**; lần này lược đồ đã đúng ⟹ nghi ngờ chuyển sang **nhãn**.
- **🔴 NGHI VẤN THƯỚC, lớn hơn ca 4:** `create_ticket` đòi 3 tham số bắt buộc (`complaint_type` ·
  `scope` · `description_raw`) mà khách **chưa cung cấp**. Model **hỏi lại khách** thay vì gọi tool.
  Với sản phẩm có **ràng buộc cứng 3 (cấm bịa số)**, hỏi lại có thể là hành vi **ĐÚNG NHẤT** ⟹
  **bộ nhãn hiện đang trừ điểm chính xác hành vi an toàn nhất, và thưởng model nào chịu BỊA tham
  số.** Lỗ gốc: **nhãn chỉ có ô "gọi tool nào", KHÔNG có ô "chưa đủ dữ kiện, hỏi lại"** — trong sản
  phẩm điều tra khiếu nại đó là trạng thái thường xuyên và đúng đắn.
- **PO-agent KHÔNG tự phán nhãn** (có động cơ rõ: kết quả bất lợi cho model đang chốt) ⟹ **security
  phán mù lần 2**, không được xem bảng điểm, không được đọc lập luận của PO-agent. Tester **không
  tự sửa nhãn, không nới ngưỡng, không tự lùi model** — giữ nguyên số bất lợi và báo lên.
- **v4 VẪN CHẠY dù model đã chốt**, hai lý do: ① **2 lượt không-gọi của `max` chưa biết rơi vào ca
  nào** — nếu cũng là ca 4 thì max/plus **HOÀ về chất lượng**, mà plus hơn 5× thông lượng và rẻ hơn
  4,6× ⟹ **quyết định có thể lật** ② thước sai thì **mọi phép đo sau đều mang lỗi đó** (F-31/32, An
  toàn 140 lượt, benchmark công bố). *Sửa thước vì thước sai, không phải vì model nào.*
- **BA HỆ QUẢ của việc chọn `max`, không được để trôi:** ① **trần TPM tụt 5×** (5M→1M ≈ **36
  lượt/phút toàn hệ thống**, dưới mức 75 cần cho 150 người) ⟹ **hàng đợi chống burst (N5/LiteLLM)
  LÊN HẠNG: giờ chặn cả buổi test nội bộ, không chỉ pilot** ② **chi phí/lượt ×4,61**
  (`$0,002257` vs `$0,000489`) ⟹ mọi ước tính đang dùng số `plus` sai theo hướng CÓ LỢI ③ **77%
  token đầu ra là suy nghĩ thầm** (plus 61%) ⟹ bẫy `TraLoiRongError` nguy hơn, `LLM_MAX_TOKENS`
  phải rộng hơn, ai siết để tiết kiệm sẽ gặp trả-lời-rỗng thường xuyên.
- `.env`: `LLM_MODEL=qwen3.8-max`, băm `db1965367fa0`. Chờ coder recreate 2 backend.
  **`EMBEDDING_*` CHƯA đụng** — kho phục vụ vẫn `3-small`, không có cửa sổ hỏng.

## 📁 HỒ SƠ CHUYÊN GIA ĐÃ LƯU + một ý mới cần CỔNG ĐIỀU KHOẢN
- Hồ sơ vòng 2 (đã sửa theo 3 lỗ tester, nhãn bằng chứng từng mục): `docs/giao-viec/2026-08-17-ho-so-
  brainstorm-toi-uu-vong2.md` · vòng 1: `…bao-cao-chuyen-gia-toi-uu-token-vong1.md`. Bảng trạng thái
  12 nhánh trong Phần C là bản đồ hiện hành.
- **Ý MỚI trong hồ sơ, chưa xử: eval agent-loop trên TÀI KHOẢN/WORKSPACE TÁCH RIÊNG** (dataset toàn
  tổng hợp ⟹ rào residency không áp). 🔴 **CỔNG BẮT BUỘC TRƯỚC MỌI BƯỚC: đọc điều khoản Alibaba về
  nhiều tài khoản** — *"cách ly tải" khác bản chất với "né trần/farm quota free", nhưng RANH GIỚI DO
  NHÀ CUNG CẤP ĐỊNH NGHĨA, không phải do ta tự thấy thiện chí*. Đọc ToS mức hợp đồng = việc người có
  thẩm quyền pháp lý (đúng giới hạn Luật C — không có vật đo). Chưa ai làm gì nhánh này cho tới khi
  cổng đó qua. Phương án hạ cấp không cần cổng: lệch giờ demo + siết concurrency.

## ✅ PO THẬT CHỐT 17/08 KHUYA — 5 quyết định + vòng chuyên gia 3
- **A1 BẬT phân luồng** trên ngăn xếp thật · **A2 chờ khách ĐỒNG Ý tường minh mới `create_ticket`**
  (vá prompt qua F-31/32, thử-rẻ-trước) · **A3 KHÔNG nạp hạn mức tới khi tối ưu chi tiêu đạt chuẩn PO**
  ⟹ `qwen3.7-max` là model TẠM chính thức (PO biết, không phải trạng thái trôi) · **ADR-028/029/030:
  Đang hiệu lực** · 4 thao tác tài khoản (ticket Alibaba · xoay khoá Qwen · GitHub secret · hotline):
  **để sau, chưa chốt**.
- **Vòng chuyên gia 3 (ý "chuyên gia Amazon"):** ① rule-trước-LLM: đã ship, nhận thêm tiền lệ ngành
  cho pitch, 0 việc mới. ② model tiering: **NHẬN nhưng XOAY TRỤC** — route theo **LOẠI BƯỚC** (tất
  định) không theo **ĐỘ KHÓ CÂU** (xác suất + **bề mặt tấn công social engineering**: kẻ gian điều
  khiển được nội dung câu, không điều khiển được vị trí bước). Giá trị thông lượng MỚI: **trần TPM
  theo TỪNG MODEL ⟹ route = CỘNG BUCKET** — khác hẳn prompt caching; cần kiểm bucket có độc lập thật
  không. Thí nghiệm mở: flash cho **bước-đơn-cuối-chuỗi** (flash trượt ở CHUỖI, chưa bị kết án ở
  bước đơn cuối — ô chưa đo), chấm bằng bộ nghiệm thu nguyên ngưỡng. ③ khoanh research vào tập-con
  cho người-thuê-API; việc mới duy nhất: **Batch API cho eval** (50% giá, tách traffic đánh giá khỏi
  bucket TPM sản xuất; caveat: không dùng context cache · thinking mặc định BẬT trong batch ở một số
  model · **qwen3.8-max có trong danh sách batch chưa: PHẢI KIỂM**). Nhãn từng ý chuyên gia tự khai
  theo Luật 12b.
- Ghi chú áp dụng PO-agent: Batch API hợp cho **lời gọi judge/chấm điểm** (độc lập, gom lô được);
  **eval qua vòng lặp agent sản phẩm là real-time theo bản chất** — không đẩy sang batch được. Khai
  rõ trước khi ai ước tiết kiệm trên toàn bộ eval.

## 🧊 SEMANTIC CACHE — ĐẶC TẢ CODER + phán quyết A-TRƯỚC-B (17/08 khuya)
- **🔴 Con số quyết định KHÔNG TỒN TẠI và không truy hồi được:** 4.613 bản ghi `search_policy` chỉ có
  `['results','status']` — **TRUY VẤN KHÔNG ĐƯỢC LƯU** (`rag/search.py:95` ghi kết quả, không ghi câu
  hỏi). ⟹ shadow mode là cách DUY NHẤT có tỉ lệ lặp. **Và là lỗ TRUY VẾT độc lập với cache:** một
  `tool_result_id` được trích **không tự nói nó trả lời cho cái gì** (ràng buộc 3). Thêm `query` vào
  payload = việc cần làm dù có cache hay không — nhưng là chữ khách gõ ⟹ **mức che PII chờ security**.
- **PHÁN QUYẾT (tự áp luật tất-định-thắng-xác-suất): shadow đo CẢ HAI, A TRƯỚC.**
  ```
  A · khớp CHÍNH XÁC (chuẩn hoá + băm)   trúng-sai = 0 THEO ĐỊNH NGHĨA · 0 ngưỡng · 0 byte · 0 bên nhận mới
  B · ngữ nghĩa (nhúng + cosine)          trúng-sai > 0 · ngưỡng nới được · trả 1 lời gọi embedding mỗi lượt
  trúng(A) = CẬN DƯỚI của trúng(B) · B−A = phần B mua thêm = phần DUY NHẤT mang rủi ro
  A đạt đủ ⟹ B không đáng rủi ro
  ```
- **Siết giá trị lưu:** khoá theo CÂU HỎI; giá trị **không chứa một chữ nào khách gõ/agent sinh** —
  chỉ đoạn chính sách + `tool_result_id`. (Lọt vào KHOÁ ⟹ trúng sụp ~0; lọt vào GIÁ TRỊ ⟹ mẩu hội
  thoại khách A vào câu trả lời khách B — rủi ro vị-trí quay lại qua cửa sau.)
- **Ca đối chứng ④: hai câu Y HỆT PHẢI trúng** — ba ca "không-làm-sai" một mình thì **cache chết đạt
  cả ba** (khuôn ĐC-5).
- Ba số trừ trước khi ước: 54% input đã được nhà cung cấp cache · cache-vs-TPM chưa xác định · B khi
  trúng vẫn trả một lời gọi embedding (tính NET).

## 📐 CHỐT TỪ VÒNG 2 — ba vật mới của tester (17/08 khuya)
- **Bộ ca cặp na-ná cho semantic cache: `2ecb739780f4`** — 10 cặp TRÚNG-SAI + **4 cặp TRÚNG-ĐÚNG
  (phần tester tự thêm)**: bộ TS một mình thì *cache-không-bao-giờ-trúng* đạt 100% — hoàn hảo và vô
  dụng (khuôn router-toàn-day_du). ⟹ **hai số đọc CÙNG NHAU**: `TS=0` và `TD cao` mới là cache dùng
  được. Công thức dựng TS: *giữ nguyên gần hết từ vựng, đổi ĐÚNG MỘT thứ có nghĩa nghiệp vụ* — vùng
  embedding yếu nhất (bề mặt gần nhất, nghiệp vụ xa nhất). Cặp mạnh nhất: **B chứa trọn A** (*"Tôi
  chuyển 2 triệu"* vs *"…nhưng bị trừ 4 triệu"*). Điều kiện land: **TS = 0/10, không ngưỡng mặc cả.**
- **Luật 12b (ratify): KHAI TRỤC khi xếp hạng** — `xếp trên trục X · CHƯA XÉT trục Y`; không đủ chỗ
  cho dòng đó ⟹ đừng xếp hạng, nêu ĐIỀU KIỆN thay vì THỨ TỰ. Lý do tồn tại riêng: *số-đúng-phạm-vi-
  sai không bị bắt bởi kiểm số — vì số vẫn đúng.*
- **INV token-budget in headroom cả khi ĐẠT** (`1b96c63`) ⟹ chuỗi thời gian trong log CI — prompt bò
  6.565→7.400 qua mười lần xanh rồi đỏ lần 11 thì phải thấy được nó bò từ bao giờ.
- Tester tự hạ hạng suy luận cache-TPM của chính mình (`⟹` → *nhất quán với cả hai giả thuyết*) —
  hai giờ sau khi viết luật cấm đúng lỗi đó. Ghi kèm câu của họ: *"thứ khác nhau không phải ai mắc —
  mà là nó CÓ BỊ BẮT TRONG NGÀY hay không."*

## 🌐 VÒNG BRAINSTORM 2 VỚI CHUYÊN GIA (17/08 khuya) — chốt sau ba lỗ tester bắt
- **Chuyên gia TỰ KHAI một trong ba lỗ có chữ ký họ** (đã ký "bảng của PO-agent đúng" = cùng thiếu
  thừa-số-trúng ② và cùng bỏ trục rủi ro ③). **Tester bắt được cả chuyên gia lẫn PO-agent.**
- **Tinh chỉnh hạng suy luận cache-TPM:** `cached ⊂ input_tokens` trong usage nói về BÁO CÁO/TÍNH
  TIỀN, không tự động nói về cách LIMITER đếm (Anthropic cũng báo cached trong usage nhưng limiter
  loại ra) ⟹ cấu trúc usage *nhất quán với* "vẫn đếm", **chưa chứng minh**. Ticket vẫn là thứ khép.
- **Ticket bổ sung 2 yêu cầu:** (a) *"point to the specific documentation clause"* — trả lời không
  kèm trích dẫn = nguồn cấp hai, không đủ làm căn cứ kiến trúc; (b) hỏi riêng implicit vs explicit.
- **Đường đo dự phòng nếu ticket mơ hồ:** TÀI KHOẢN THỬ mới (trần theo tài khoản gốc) + prompt tổng
  hợp (né residency) + burst cùng-prefix vượt trần danh nghĩa → 429? Caveat khai trước: cùng region
  + cùng loại PAYG (bẫy snapshot 60RPM/100k — trần thấp lại làm phép đo RẺ hơn nếu cơ chế đếm giống).
- **Prompt caching hạ hạng, KHÔNG vứt:** "đòn bẩy thông lượng" → **"phụ phẩm latency (TTFT) + tiền,
  nhận không mất gì, 0 công thiết kế thêm"** — khớp kết quả 85,0→86,3 đã revert.
- **🔒 Kiến trúc semantic cache chốt thêm (mạnh hơn ngưỡng similarity):** đặt cache **TRƯỚC cổng OTP
  về kiến trúc** — chỉ phục vụ lớp câu `search_policy` trả lời (chính sách công khai, không OTP,
  không dữ liệu khách); **lượt nào đã gọi tool nhạy cảm ⟹ KHÔNG đủ điều kiện GHI vào cache**. Rủi
  ro "trả lời của khách khác" bị loại **bằng VỊ TRÍ trong kiến trúc**, không bằng ngưỡng similarity
  (thứ có thể bị nới theo phản xạ — họ `XA_GIAO`).
- **Shadow mode đo HAI số:** tỉ lệ TRÚNG (quyết định lợi) và **tỉ lệ TRÚNG-SAI** (khác nghĩa nhưng
  vượt ngưỡng — tiếng Việt CSKH đầy cặp *"chuyển nhầm CHO người khác"* vs *"BỊ người khác chuyển
  nhầm cho"*) — **số thứ hai quyết định sống chết**. Giả thuyết để KIỂM, không giả định: câu chính
  sách phân bố dồn ⟹ hit có thể cao.
- **LUẬT XẾP HẠNG (chuyên gia khái quát từ điểm T1 của tester):** *cơ chế TẤT ĐỊNH luôn thắng cơ chế
  XÁC SUẤT cùng lớp* — tất định thì trúng=100% theo định nghĩa, rủi≈0 vì kiểm được bằng test thường.
- **T2 hoãn CÓ ĐIỀU KIỆN MỞ LẠI:** câu trả lời Alibaba, hoặc phép đo tài-khoản-thử — tránh "hoãn"
  trượt thành "quên".
- **NẾP MỚI (ratify): mọi phát biểu XẾP HẠNG khi trình kèm một dòng KHAI TRỤC** — *"xếp trên trục X,
  chưa xét trục Y"*. Họ lỗi số-đúng-phạm-vi-sai không bị bắt bởi kiểm số (số vẫn đúng), chỉ bị bắt
  bởi câu hỏi *"kết luận này đứng trên trục nào, trục nào chưa nói?"* — rẻ hơn ba lần đính chính.
- **INV token-budget:** CI in **headroom còn lại** mỗi lần chạy, không chỉ đỏ/xanh — xu hướng phình
  nhìn thấy trước mốc 90%.

## 🌐 PHẢN HỒI CHUYÊN GIA TOKEN (17/08 tối) — ba câu trả lời đổi kế hoạch
- **① Cache-hit vs rate-limit: NGÀNH CHIA ĐÔI, không suy được từ thông lệ.** Anthropic: cached token
  **ĐƯỢC TRỪ** khỏi ITPM (cache-aware rate limits, công bố tường minh, vd 2M ITPM + 80% hit ⟹ 10M
  thực tế). OpenAI (+xAI): cached **VẪN ĐẾM** vào TPM. Alibaba PAYG: tài liệu **im lặng** ⟹ đọc là
  "chưa biết", KHÔNG phải "có"; điểm gợi ý duy nhất: chế độ **PTU** ghi cached tiêu quota theo mức
  chiết khấu. Bẫy đã ghi: implicit cache kích hoạt từ ~1000 token (dòng max) / 256 (khác), khớp
  prefix. Phép kiểm thực nghiệm (burst cùng-prefix vượt trần danh nghĩa → 429?) **đắt** — thăm dò
  header rate-limit trước nếu có.
- **② 🔴 BẪY LiteLLM cho N5:** limiter TPM của LiteLLM có lỗi đã báo cáo — **đếm cả cached_tokens
  vào total_tokens** ⟹ kể cả khi nhà cung cấp trừ cached khỏi trần, **chính proxy của ta dựng lại
  cái trần đã được gỡ**. Vào checklist nghiệm thu N5: kiểm cách limiter đếm cached TRƯỚC khi tin số.
- **③ Rolling summary XUNG ĐỘT prompt caching** (viết lại đầu lịch sử = phá prefix; append-only là
  prefix ổn định) ⟹ với hội thoại 5-6 lượt gần chắc ÂM. **Điều kiện mở lại khai trước: p95 số
  lượt/hội thoại từ traffic thật > ~8-10** (đo bằng sổ usage).
- **④ Đường mở lại 2.3 KHÔNG phá cache** (nếu sau này cần): giữ schema TĨNH trong prefix, siết bằng
  `tool_choice`/allowed-tools ở tầng API (Anthropic: đổi tool_choice mất cache messages nhưng khối
  tools SỐNG — cần kiểm Qwen tương đương) hoặc một dòng chỉ dẫn ở đuôi động + **hard-gate server đã
  có sẵn** (authority matrix + OTP + INV). Soft-gate prompt + hard-gate server = đủ. BÁC-ở-5-tool giữ.
- **⑤ T2:** chuyên gia đề nghị đẩy hẳn thời gian RA KHỎI prefix (qua tool result / đuôi động) thay vì
  hạ độ phân giải (hạ xuống giờ vẫn phá cache mỗi giờ, đúng lúc demo dồn) — đưa vào yêu cầu thiết kế
  T2. Ưu tiên T2 phụ thuộc câu ①.

## ⚡ ĐỢT TỐI ƯU TOKEN 17/08 (T1-T5) — ĐÃ LÀM VÀ ĐÃ ĐO (bổ sung muộn: đợt này diễn ra trong tin nhắn/code, STATE ghi thiếu — lỗi PO-agent)
- **T1 PHÂN LUỒNG: ĐÃ LAND + ĐO.** Luật 0-token (regex danh-sách-cho-phép, `md5:4e50e609e085`), sau cờ
  `PHAN_LUONG_BAT` mặc định OFF. Đường nhẹ = template, 0 LLM, 0 bản ghi (`Δcomplaints=Δtickets=0`,
  4 test Δ xanh trên HTTP thật). Cổng: 124/124 âm · 14/14 âm-ngắn · 15/20 dương · ĐC-1..5 đạt
  (định nghĩa chuẩn: `docs/giao-viec/2026-08-17-dinh-nghia-cong-DC-phan-luong.md`).
- **Chuỗi R (k=1, cùng ảnh `86b652d18e26`, kho 378):**
  | | PO 5 lượt | đơn 4 lượt |
  |---|---|---|
  | R1 OFF/ON | 87.470 (11 gọi) | 46.909 |
  | R2 ON/ON | 86.633 | **31.193 = −33,5% TẤT ĐỊNH** (2 lượt nhẹ 0-token) |
  | R3 ON/OFF | 76.986 (10 gọi) | 30.761 |
  **"alo": 6.566 → 0 token, 0,01s (kiểm chéo HTTP).** Sàn nhiễu đo được: **dao động ≥3 lời gọi giữa
  hai lần chạy y hệt** (14 vs 11) ⟹ "−32% nhờ tắt thinking" sáng 17/08 bác còn **−11% k=1**; hiệu
  ứng <3 lời gọi = không kết luận được. R3: ToolResult +4 y hệt cả ba vòng (tra như nhau, khác tầng
  ghi), bớt gọi `create_ticket` thừa, nhanh 2,2×.
- **T3 `SUY_LUAN_BAT`: đã land** (mặc định = giữ thinking; sổ ghi trạng thái THẬT từ payload).
  **T2 (hạ độ phân giải current_time): CHƯA làm** — thiết kế trước, đã bác phương án dời-chỗ bằng đo
  (85,0→86,3%). **T4: cố ý không làm** (đường nhẹ = 0 model). **T5: có sẵn.**
- **Finding từ chuỗi R:** lượt-4 tạo vé TRƯỚC đồng ý = model TUÂN prompt (tiền đề bước 4 toàn
  data-completeness, không có consent — F-31/32, tái hiện 3/3) · gọi 2 lần = VI PHẠM chỉ dẫn tường
  minh, chống-trùng tầng code đang gánh · reply lượt-4 trong log là bản BỊ output_filter THAY (mù
  nội dung; harness đã vá cho lượt sau) · `request_human_handoff` không vào sổ tool (ADR-029 mục 2b).
- Sổ usage: JSONL trên volume, mỗi dòng mang `bam_ma_nguon+cach_bam · duong · so_tool_schema_gui ·
  suy_luan_gui · base_url`. Ngân sách đợt: 556K/640K free `qwen3.7-max`, dừng chủ động.
- **Semantic cache: hướng đã duyệt** — shadow mode (ghi không phục vụ) · trong đường-chính-sách sau
  router · vô hiệu theo băm kho · bộ an toàn = cache-miss theo thiết kế (cổng hit=0). Bộ ca ranh giới
  16 ca `0dae3b0c3949` (nhóm ⑤ "chung về ngôn ngữ, cá nhân theo DỮ LIỆU" = nhóm giết bộ lọc câu).

## 🧊 NGUYÊN TẮC SEMANTIC CACHE (17/08 tối — sinh từ câu hỏi của PO thật, chốt TRƯỚC khi ai thiết kế)
PO hỏi: *"đi đường semantic cache thì bộ an toàn sẽ rẻ hơn từ lần gọi thứ 2 đúng không?"* — trả lời:
**KHÔNG, và đảo thành nguyên tắc thiết kế:**

> **BỘ AN TOÀN PHẢI LÀ CACHE-MISS THEO THIẾT KẾ. Tỉ lệ cache-hit trên ca an toàn = 0 là một CỔNG.
> Một ca an toàn trúng cache = ranh giới cache đã thủng — điều tra, không ăn mừng tiết kiệm.**

Lý do: ① bộ an toàn đo **hành vi HIỆN TẠI của model** — câu trả lời từ cache đo **cái cache**, tức
lần chạy thứ 2 trở đi vừa rẻ vừa **vô giá trị**: xanh-giả hoàn hảo (model thoái hoá bao nhiêu cũng
không thấy, vì cache phát lại câu trả lời của model CŨ lúc còn tốt). ② theo ranh giới đã chốt (chỉ
cache **câu chính-sách-chung khách-bất-biến**), mọi ca an toàn — tấn công, dò OTP, khiếu nại cá nhân
— **không thuộc lớp cache được**; ca nào hit là ranh giới hỏng. ③ cache còn **mở bề mặt tấn công
mới** mà bộ an toàn phải MỞ RỘNG để canh: hai câu na ná nhưng khác người/khác dữ kiện trúng nhầm
nhau (N3 đã ghi: *"cache lẫn của người khác = thảm hoạ"*) + kẻ tấn công dò được đáp án tất định.

Chỗ có tiền THẬT của cache: **production** — câu chính-sách-chung lặp lại rẻ từ lần hỏi thứ 2, đo
bằng tỉ lệ hit trên traffic thật. **Tiết kiệm nằm ở phần được phép rẻ; an toàn nằm ở phần không
bao giờ được phép rẻ.**
## 🗄️ PHÁN QUYẾT KHO RAG CHUẨN (17/08 tối) — "lệch 41 chunk" KHÔNG tồn tại như một tập
- Coder diff hai kho (0 LLM): **không phải ttl thiếu/thừa 41 chunk** — hai kho dựng từ **HAI ĐỊNH
  DẠNG NGUỒN** của cùng bộ tài liệu:
  ```
  fin05  378 chunk · nguồn .DOCX · băm nội dung 2b9f271b0d26   ← đi qua parser ĐÃ VÁ (đòn 4b:
                                                                  bảng→dòng tự mô tả, đọc doc.tables)
  ttl    419 chunk · nguồn .PDF  · băm nội dung b165930f0e81   ← KHÔNG qua đường đó; có chunk
                                                                  MỤC LỤC toàn dấu chấm = rác truy hồi
  ```
  `+41` chỉ là hiệu số ngẫu nhiên của hai lần chunk hai văn bản khác nhau. **Đuổi theo "41 chunk đó
  là gì" sẽ không ra gì — chúng không tồn tại như một tập.** (Một câu hỏi sai được giải thể bằng đo,
  không phải được trả lời.)
- **PHÁN QUYẾT: `fin05` (378, .docx) là KHO CHUẨN** — lý do mạnh hơn "vật của benchmark": nó là kho
  **duy nhất đi qua parser đã vá**. Bằng chứng dấu vết: chunk "hạn mức" của fin05 bắt đầu bằng NỘI
  DUNG; của ttl bắt đầu bằng "MỤC LỤC \n I. ..." — khớp mọi truy vấn nhắc tên mục mà không mang câu
  trả lời nào.
- **Hệ quả:** ① mọi phép kiểm chính sách (gồm RG-12/13) **bắt buộc chạy trên fin05** ② bất kỳ kết
  luận RAG nào từng đo trên `ttl` là đo **một kho chưa vá** — cần rà lại (giao tester xác nhận không
  có số công bố nào dính) ③ vì sao ttl nạp từ PDF: **chưa biết, không đoán** — có thể lần nạp cũ
  trước khi có .docx.
- Coder khai rõ điều KHÔNG kết luận: chưa so **chất lượng truy hồi** giữa hai định dạng — việc đó
  tốn embedding, thuộc cửa sổ được hô.

## 🧭 TỔNG KẾT 17/08 — "KHAI ≠ CHẠY": SÁU cơ chế, và cách duy nhất bắt được chúng
> Hồ sơ đầy đủ: `docs/security/2026-08-17-ho-so-KHAI-khac-CHAY-nam-co-che.md` (`36d6a1a`)
>
> ### 🔑 **DÒNG DUY NHẤT NẾU CHỈ ĐƯỢC GIỮ MỘT (security, chốt cuối phiên):**
> # **Kiểm chéo không phải một THÁI ĐỘ. Nó là một CƠ CHẾ, và nó cần một VẬT ĐO.**
>
> *Hôm nay hai vai bắt chéo nhau **bảy lần** (security→PO-agent 4 · PO-agent→security 3), và
> **không lần nào ai tự bắt được mình**. Nhưng **tỉ số không phải luận điểm — ĐIỀU KIỆN của nó mới
> là**: cả bảy lần đều có **một vật đo được mà cả hai truy cập ĐỘC LẬP**. Ở chỗ không có vật đó,
> hai vai vẫn ngồi đủ và **không lần bắt chéo nào xảy ra được** — **không phải vì ai lơ là.***

| # | Cơ chế | Dấu vẫn khớp? | Bắt bằng |
|---|---|---|---|
| 1 | `docker cp` vào container đang chạy | ✅ `build_commit` không đổi | `docker diff` (bản siết) |
| 2 | Ảnh dựng từ **cây làm việc**, không từ HEAD | ✅ `BUILD_COMMIT=HEAD` vẫn đúng | md5 `src/` ↔ `git show HEAD` |
| 3 | **Phiên bản thư viện phụ thuộc đổi** | ✅ commit **và** `he_thong` **đều** trùng | băm **payload đã gửi** |
| 4 | **Prompt chứa thời gian thực** | ✅ mọi dấu trùng | ghi **mốc thời gian** cạnh dấu |
| 5 | Bộ đo tự soạn lại kích thích | — | so **từng trường** với app sống |

🔴 **#3 và #4 đáng sợ nhất và mãi tới hôm nay mới được xếp cùng họ:** chúng **không cần thao tác
Docker nào**, **không ai làm gì sai**, và **mọi dấu ta đang có đều trùng khít**. `langchain-core`
1.5.3→1.5.4 đổi kích thích **~12%** với `he_thong` y hệt; `current_time` đổi prompt **mỗi lần gọi**.

⟹ **BẢN VÁ CHO CẢ HỌ, MỘT CÂU: băm THỨ ĐÃ GỬI / ĐANG CHẠY, đừng băm THỨ SINH RA NÓ.**
Băm `src/` **không bao giờ** bắt được #3/#4/#5; nhãn `build_commit` **không bao giờ** bắt được #1/#2.

### LUẬT A — cổng phải hỏng được theo HAI hướng ngược nhau
> **Cổng phải IM lúc bình thường VÀ KÊU THẬT lúc bất thường — vế hai chỉ chứng minh được bằng
> CA ĐỐI CHỨNG.**

Vế một chống **cổng bị tắt bằng thói quen** (ca: `docker diff` bản thô kêu ở mọi lần chạy vì
`__pycache__` ⟹ *"một cái còi kêu lúc bình thường là cái còi người ta tắt đi"*). **Vế hai chống
cổng CHƯA BAO GIỜ HOẠT ĐỘNG** — và *"im lúc bình thường"* một mình cũng là tiêu chí của **một cổng
chết**. Hai ca đối chứng hôm nay chứng minh vế hai: coder ép `ValueError` **phải ném ra** (chặn một
bản vá *"bắt tất cả thành mềm"* vẫn 10/10 xanh) · security gửi dấu tới **chính localhost** cũng ra
0 ⟹ phép thử **mù**. **Không có vế hai, cả hai cổng đó đều "xanh".**

### LUẬT B — làm tròn một phát biểu lên đúng MỘT NẤC là lỗi đắt nhất trong ngày
| Phát biểu ĐÚNG | Bị làm tròn thành |
|---|---|
| *"không nghi can nào trong `src/`"* | *"có người xoá tay"* |
| *"bản vá đã land"* | *"bước 1 xong, xoay khoá được rồi"* |
| *"lệnh cấm bịa chiếm 1/3 prompt bộ đo"* | *"phép thử khắc nghiệt hơn"* |
| *"v4 không đo được hành vi sản phẩm"* | *(suýt)* *"sản phẩm đang sai"* |

Áp mạnh nhất cho **PO-agent** (nấc cuối trước khi một phát biểu thành **quyết định**) và **security**
(nấc ngay trước đó — 2/4 dòng là của họ).

### LUẬT F — con số đi vào một QUYẾT ĐỊNH phải mang MẪU SỐ trong CÙNG MỘT DÒNG
Ba lần trong ngày 17/08, một con số **đúng** thiếu mẫu số suýt dẫn tới quyết định sai:
```
f ≈ 0%      đo trên golden_set — bộ ca CỐ Ý không có lượt đơn   ⟹ suýt bác đòn bẩy tốt nhất
120 ca      thứ được chấm là 124 CÂU                            ⟹ 4 câu không bao giờ được chấm
473M        ảnh hiện tại 892M ⟹ thật ra là +53%                 ⟹ PO phải tự đoán lớn hay nhỏ
```
**Cả ba lần mẫu số tìm được trong MỘT lệnh** (`wc -l` · `du -sh`). Không phải nó khó tìm — là
**không ai nghĩ tới việc tìm**, kể cả người đang rất cẩn thận về một chuyện khác.

> **LUẬT F: con số nào đi vào một quyết định thì phải mang MẪU SỐ của nó trong CÙNG MỘT DÒNG.
> Không phải "nhớ hỏi so với cái gì" — mà là KHÔNG ĐƯỢC VIẾT CON SỐ TRẦN RA.**

*(Vế thi hành do coder đề. Khác biệt: "nhớ hỏi" là một thói quen — hỏng khi người ta bận;
"không được viết con số trần" là một quy tắc về hình thức đầu ra — kiểm được bằng mắt.)*

### LUẬT G — cơ chế CÓ MẶT và làm ĐÚNG việc của nó, không làm việc ta tưởng
Bốn ca cùng khuôn trong ngày:
```
build_commit   định danh ẢNH        — tưởng định danh MÃ ĐANG CHẠY
docker diff    bắt drift MÃ         — tưởng bắt drift PHỤ THUỘC (4GB site-packages lọt)
multi-stage    bỏ compiler+cache    — tưởng bỏ cả dev-tool (cùng requirements.txt, COPY nguyên khối)
băm 12 hex     md5 vs sha256        — chuỗi hex KHÔNG TỰ KHAI nó sinh ra từ đâu
```
**Không cơ chế nào hỏng.** Cả bốn làm **đúng** việc chúng sinh ra để làm. Cái sai nằm ở **phạm vi
ta gán cho chúng**, và phạm vi đó **không được ghi ở đâu cả** ⟹ mỗi người tự suy, và suy rộng ra.
⟹ Hệ quả cho quy ước băm: **băm phải công bố kèm TÊN THUẬT TOÁN** — `1edd51dff555` không phải một
băm, `md5:1edd51dff555` mới là.

### LUẬT E — một bộ ca XANH phải kèm PHÂN BỐ LÝ DO xanh
Coder mổ con số `124/124` (bộ ca âm, luật phân luồng `1edd51dff555`) xem nó **đạt vì lý do gì**:
```
103 ca  chặn vì CÓ CHỮ SỐ
 21 ca  chặn vì DÀI > 40 ký tự        ← chỉ mình mệnh đề này gánh
  0 ca  chặn vì TOKEN NGOÀI TẬP XÃ GIAO   🔴 mệnh đề CHÍNH, chưa khai hoả lần nào
```
**Danh-sách-cho-phép — nguyên tắc số ① của cả thiết kế, vừa được PO-agent ratify — chưa chặn được
một ca nào.** Nó **chưa hề được thử**. Và 21 ca kia đứng **chỉ trên một ngưỡng độ dài chọn tuỳ
tiện** (`DAI_TOI_DA=40`) — đúng mệnh đề coder tự tuyên bố *"độ dài không bao giờ đủ một mình"*.
Nới ngưỡng lên 60 là mở cửa cho 21 ca đó, **và `124/124` vẫn xanh cho tới lúc ai đó nới**.

> **LUẬT E: một bộ ca xanh phải kèm PHÂN BỐ LÝ DO xanh. Nhánh nào không xuất hiện lần nào là nhánh
> CHƯA ĐƯỢC KIỂM — dù tỉ lệ có là 100%.**
> **Hỏi "mỗi ca ĐẠT nhờ nhánh nào", đừng hỏi "bao nhiêu ca ĐẠT".**

**Khác với các ca cùng ngày ở TẦNG:** không phải sai **dân số** (`golden_set` không có lượt đơn),
không phải sai **mẫu số** (120 ca vs 124 câu) — mà là **bộ ca KHÔNG CHẠM ĐƯỢC mệnh đề cần chạm**.
`124/124` **đúng, không bịa**, và vẫn **không chứng minh** điều người đọc sẽ tưởng nó chứng minh.

*(Coder tự soạn 8 ca "khiếu nại thật · ngắn · không chữ số" để ĐI TÌM LỖ — cả 8 đi `day_du`, và
lần này chặn bằng **đúng mệnh đề danh-sách-cho-phép**. ⟹ luật không có lỗ ở đó, **nhưng chỉ biết
được sau khi đi tìm**. Và họ **không** đưa 8 ca đó vào bộ chấm: soạn ca để thử luật của chính mình
là thứ đội đã cấm. Cũng **không sửa `DAI_TOI_DA`** — *"phát hiện này về BỘ CA, không về LUẬT; sửa
luật lúc này là tối ưu cho một bộ ca tôi vừa tự soạn."*)*

### LUẬT D — cột phòng thủ phải có NGUỒN KHÁC, "dư thừa" chỉ là hệ quả
Cơ chế **thứ SÁU** (coder tự bắt, tầng khác): `>/dev/null` nuốt một lệnh **không chạy**, bảng vẫn
hiện **nhãn cũ + chuông ×0**, và họ **suýt đọc thành "bản vá không hoạt động"**. Không phải
khai-vs-chạy mà **lệnh-không-chạy-vs-tưởng-đã-chạy** — nhưng **cùng mệnh đề bị phá**: *thứ được báo
cáo không phải thứ đã xảy ra.* Thứ cứu được là **một cột in ra vì lý do hoàn toàn khác**.

> **Cột phòng thủ = cột có NGUỒN KHÁC với cột nó bảo vệ. "Dư thừa" là HỆ QUẢ, không phải tiêu chí.**

⚠️ PO-agent ban đầu ghi *"một cột thừa là một cột phòng thủ"* — **làm tròn lên đúng một nấc**
(Luật B, ngay sau khi ratify chính Luật B). Security sửa: cột cứu được coder là cột có **nguồn độc
lập** (`docker diff`, trong khi thứ hỏng là `docker compose`). **Một cột thừa lấy từ CÙNG một lệnh
với cột chính thì cũng đứng yên y hệt khi lệnh đó không chạy** ⟹ ghi vế rộng thì luật thành *"in
nhiều cột vào"*, và **một bảng nhiều cột cùng nguồn vẫn im lặng y như một bảng một cột**.

### LUẬT C — cách duy nhất đã bắt được cả năm cơ chế
**Không cơ chế nào bị bắt bởi một người tự soi lại việc mình.** Cả năm bị bắt bởi **hai người đo
cùng một vật rồi so SỐ** — **tám lần trong ngày**, và **tám lần chỗ khác nhau là chỗ có thông tin**.

🔴 **Vế thi hành, chỗ dễ trượt nhất: SO SỐ, KHÔNG SO KẾT LUẬN.** Security suýt đóng vụ
`4.862 vs 4.334` bằng câu hoà *"hai cách đếm khác nhau thôi"* — ở tầng **kết luận**, nghe hợp lý,
**hai bên cùng yên** — và nó **đã che mất cơ chế #3**. Thứ cứu được là **tester TỪ CHỐI cách hoà đó**.
⟹ **Một quy ước "hai người cùng đo" mà thiếu vế "cấm hoà ở tầng kết luận" sẽ tự vô hiệu ngay lần
đầu hai người lịch sự với nhau.**

### 🔴 GIỚI HẠN CỦA LUẬT C — nơi KHÔNG có vật đo thì luật không áp được
Luật C bắt được **cả sáu** cơ chế chỉ nhờ một điều kiện chưa ai nêu ra: **mỗi ca đều có một VẬT ĐO
ĐƯỢC mà hai người truy cập ĐỘC LẬP được** — một băm, một số đếm, một dòng log, một `docker diff`.
**Chỗ lệch hiện ra thành SỐ, và số thì không thương lượng.**

⟹ **Ở nơi không có vật đo, Luật C không áp được.** Ca điển hình: đọc *Product Terms of Service* của
Alibaba rồi kết luận *"hợp đồng có cam kết"* — **không băm, không số đếm, không phép đo nào để
lệch** ⟹ cái sai đó **không bao giờ bị bắt bởi cơ chế đã cứu ta sáu lần**.

**Lớp này nguy nhất vì HAI lý do cộng lại: nó không tự lộ, VÀ nó nghe có thẩm quyền.** Cùng hình
dạng lỗi security mắc buổi sáng với MISINFO-002 (biến một **giọng văn nhấn mạnh** thành một **ràng
buộc chịu lực** chỉ vì nó viết hoa).

> **Quy tắc thay thế: ở nơi không có vật đo, thay "hai người đo rồi so số" bằng "KHAI ĐÚNG HẠNG
> BẰNG CHỨNG rồi DỪNG".** *"Cam kết ở mức trang tài liệu, chưa kiểm mức hợp đồng"* là phát biểu
> **dùng được**; *"hợp đồng cam kết"* là phát biểu **không ai bác được, nên không ai kiểm được**.

**Và đây là lý do phải ghi giới hạn KÈM luật:** một luật không có giới hạn ghi kèm **sẽ được áp ra
ngoài vùng nó hoạt động**, và ở đó nó **tạo ra sự tự tin mà không tạo ra kiểm chứng** — *đó là cách
một quy trình tốt sinh ra một sai lầm mà chính nó che.*

## 🔴🔴 SỰ CỐ 17/08 — KHOÁ OpenAI PRODUCTION ĐÃ TRUYỀN TỚI MÁY CHỦ ALIBABA (chờ security phán quyết xoay khoá)
- **Cơ chế:** `config.py` (`54164fa`, PO-agent duyệt) có fallback **vô điều kiện**
  `LLM_API_KEY or OPENAI_API_KEY`. Trỏ `LLM_BASE_URL` sang `dashscope-intl` mà để `LLM_API_KEY`
  trống ⟹ client gửi **khoá OpenAI production `sk-proj…` nguyên văn trong header `Authorization`
  tới Alibaba**. Alibaba trả `401`. Coder đo thật, không suy luận.
- **Luật rút ra:** **một fallback chỉ an toàn khi ĐÍCH ĐẾN KHÔNG ĐỔI. Đổi đích mà giữ fallback là
  biến tiện lợi thành RÒ RỈ.** Và nó **im lặng**: người vận hành đọc `401` rồi đi tìm sai chỗ,
  trong khi khoá đã rời hệ thống. Điều kiện sinh ra lớp lỗi này = **hai nhà cung cấp cùng sống
  trong một tiến trình** — đúng thiết kế ta vừa chọn (chat→Qwen, embedding→GIỮ OpenAI).
- **⚠️ PHÂN KỲ CÁCH ĐỌC — đã nêu với coder:** coder mô tả ở **thì tương lai** (*"cấu hình đó sẽ
  kích hoạt đường này"*), PO-agent đọc ở **thì quá khứ**: phép đo chứng minh đường đó **ĐÃ chạy
  thật, hôm nay, trên máy này**. `401` = *họ TỪ CHỐI DÙNG khoá*, **không phải** *họ KHÔNG NHẬN ĐƯỢC
  khoá*. ⟹ PO-agent coi là **LỘ**, đề xuất **xoay `OPENAI_API_KEY`**. Đã hỏi security 3 câu, có
  nêu rõ *"tôi có thể đang phản ứng thái quá, muốn biết nếu vậy"*: ① `401` có đủ để coi là chưa lộ
  không (cần căn cứ, vì xoay khoá có giá thật) ② nghĩa vụ thông báo NĐ 13/2023 hay chỉ là secret
  hạ tầng ③ **rà cả HỌ**: còn cặp `X_API_KEY or Y_API_KEY` / `X_BASE_URL` nào cùng hình dạng trong
  `src/`, đặc biệt đường embedding.
- **✅ Đã chặn bằng CODE, không phải dặn nhau (`7ce8209`):** base_url khác + thiếu khoá → **CHẾT
  lúc khởi động nêu rõ lý do** · không base_url → fallback giữ nguyên · base_url khác + có khoá →
  dùng đúng khoá đó. 23/23 invariants xanh.
- **`.env` đã điền TƯỜNG MINH** `LLM_API_KEY=<giá trị QWEN_API_KEY>` (117 ký tự `sk-ws-…`) +
  `LLM_BASE_URL` + `LLM_MODEL=qwen3.7-plus`; `EMBEDDING_*` **cố ý không đặt** (giữ OpenAI = giữ
  VẬT); JUDGE giữ gpt-4o-mini. Băm nội dung `.env` `22529a2cbf76`. `git ls-files .env` = **0**.
- **Chờ coder liệt kê VỊ TRÍ (không giá trị) mọi nơi `OPENAI_API_KEY` tồn tại** — `.env` dev ·
  `.env` Windows production · biến trong container đang chạy · CI secrets. Xoay mà sót một nơi =
  service chết giữa chừng; phải biết TRƯỚC khi bấm.
- **Ghi nhận công bằng:** lỗi của coder, nhưng tìm ra bằng cách duy nhất tìm được là **chạy thật**
  — nếu không, PO-agent đã điền đúng cấu hình rò đó vào `.env` rồi đẩy lên production.
- **⚖️ LUẬT (coder tự nêu khi nhận đính chính, PO-agent nâng thành luật):** *"Nói giảm một sự cố
  TỆ HƠN việc gây ra sự cố, vì nó làm người đọc định giá sai."* ⟹ **thì của động từ trong báo cáo
  sự cố là một DỮ KIỆN KỸ THUẬT, không phải văn phong** — "sẽ kích hoạt" vs "đã chạy" là hai sự
  việc khác nhau.
- **KIỂM KÊ 6 VỊ TRÍ `OPENAI_API_KEY` (coder, chỉ vị trí, 0 giá trị được in):** ① `.env` Mac (PO
  giữ quyền ghi) ② biến môi trường trong `fin05-backend-1` — *`frontend` KHÔNG có, đúng thiết kế
  BFF* ③ `docker inspect … Config.Env` ④ GitHub Actions secret ⑤ **`.env` máy Windows production —
  coder KHÔNG truy cập được, không đoán** ⑥ **log của Alibaba — ngoài tầm kiểm soát, không ai xoay
  được**. Kèm 3 phát hiện phụ đã kiểm: khoá **không** lọt log của ta (`grep -c "sk-proj"` = 0, SDK
  không in khoá trong lỗi 401) · **0 khoá thật** trong scratchpad (6 chuỗi `sk-…` đều là placeholder
  — đối chiếu GIÁ TRỊ thật chứ không đoán theo hình dạng).
- **🪤 BẪY XOAY KHOÁ (coder, cùng HỌ với `PersistentClient` hôm qua):** `Config.Env` của container
  ghi **lúc container được TẠO**, không phải lúc chạy ⟹ sửa `.env` rồi `docker compose restart` thì
  **container vẫn giữ khoá CŨ**, service chết bằng 401 và người xoay tưởng mình sót chỗ khác.
  **Luật: `restart` KHÔNG ĐỦ khi thứ cần đổi được ghim lúc TẠO.** Thứ tự bắt buộc: sửa `.env` →
  `docker compose up -d --force-recreate backend` → `docker inspect` xác minh.
- **🟡 `/health` XANH GIẢ — lần thứ HAI trong dự án:** `/health` không chạm OpenAI ⟹ khoá sai vẫn
  xanh, production chết **im lặng**. **Nghiệm thu xoay khoá = bắn một lượt CHAT THẬT**, không tin
  `/health`. *Nếu xuất hiện lần thứ ba thì phải sửa chính `/health`, không sửa checklist nữa.*
- **TRẠNG THÁI: chưa xoay gì cả.** Chờ ① security phán quyết `401`-có-tính-lộ ② **PO thật quyết**
  (họ giữ máy Windows #5 + dashboard GitHub #4). Coder được dặn **không đụng** `.env`/container —
  **xoay nửa vời tệ hơn chưa xoay**.

## ⭐ ĐỔI API SANG QWEN — PO thật quyết 16/08, ƯU TIÊN CAO sau gate (chi tiết: brief `2026-08-17-dot-nang-cap-oss.md` §N7)
- **🔒🔒 PO THẬT CHỐT 17/08: `qwen3.7-plus`.** Cấu hình: `LLM_BASE_URL=https://dashscope-intl.
  aliyuncs.com/compatible-mode/v1` · `LLM_MODEL=qwen3.7-plus` · **EMBEDDING GIỮ OpenAI** (đổi =
  đổi VẬT) · **JUDGE giữ gpt-4o-mini** (giám khảo ≠ bị chấm). Free quota đã kích hoạt: 1M token/
  model, hết hạn 15/11/2026 — 403 `AccessDenied.Unpurchased` đã hết, 4/4 model trả lời.
- **⚠️ LÝ LẼ CHỌN: nửa đầu SAI, PO-agent tự bắt và rút trong ngày.** Tôi khuyến nghị plus bằng lập
  luận *"5M TPM/15K RPM là tầng DUY NHẤT đủ cho 100 CSKH"*. **`qwen3.7-flash` CŨNG 5M TPM**, và
  tester đã đo từ 16/08 rằng lợi thế 15.000 RPM chỉ đáng **12% ở vùng giữa, HOÀ ở đuôi** (TPM chặn
  trước) — tức lý lẽ thông lượng plus-vs-flash **đã chết trước khi tôi dựng nó lại**. Phần đúng
  còn lại: plus > `qwen3.8-max` (5M vs 1M TPM ≈ 36 lượt/phút < 75 cần). ⟹ **Lý do sống duy nhất
  để chọn bản lớn vẫn là độ tin cậy gọi tool nhiều bước — CHƯA ĐO XONG.** Bài học ghi thành luật:
  **một lý lẽ đã bị số bác thì CHẾT VĨNH VIỄN, không hồi sinh được bằng việc quên mất là nó đã
  chết** — dạng tự lừa êm ái nhất, vì nó tiện cho kết luận đang muốn.
- **Hệ quả bắt buộc:** `LLM_MODEL` phải là biến env thuần, **không hardcode tên model ở bất kỳ đâu
  kể cả default và test** — nếu flash đạt ngưỡng thì đổi phải là một dòng `.env`, không phải một PR.
- **📉 GIÁ NIÊM YẾT ≠ GIÁ THỰC ĐO — token suy nghĩ ăn mất hơn NỬA lợi thế giá của flash.** Tester đo
  (prompt tối giản 733 token vào): plus `164` token ra/lượt (74% suy nghĩ) `$0,000489` · max `119`
  (63%) `$0,002257` = **4,61×** · flash **`492`** (**91%** suy nghĩ) `$0,000086` = **0,18×**. ⟹ trên
  giấy flash rẻ hơn plus **13×**, đo thật chỉ **5,7×** — vì flash đốt gần gấp ba token ra để suy
  nghĩ. Câu hỏi *"chọn plus có tốn gấp 13 lần vô ích không"* thật ra là *"gấp 5,7 lần"*: vẫn đáng
  hỏi, **nhỏ hơn một bậc**. ⚠️ Đo trên prompt 733 token, **không phải prompt sản phẩm ~14k** — dùng
  để biết THỨ TỰ ĐỘ LỚN, cấm dùng cho quyết định cuối.
- **❌ Quan sát `1/4 JSON hỏng` của PO-agent về flash: KHÔNG TÁI HIỆN ở n=25 (hỏng định dạng 0/25).**
  Cả 3 model đều 0 lỗi định dạng; flash 23/25 = 92%, trượt 2 ca là **không gọi tool** (plus/max: 0).
  ⟹ quan sát n=4 của tôi là **nhiễu**, phải rút. Nhưng tester chặn luôn chiều ngược lại, và đây mới
  là điều quan trọng: **cả `1/4` lẫn `0/25` đều đo trên NHÁNH SAI** — bộ probe là gọi tool **MỘT
  BƯỚC**, còn thứ đang bỏ ngỏ là **chuỗi NHIỀU BƯỚC**. `0/25` không phải bằng chứng flash ổn, chỉ là
  bằng chứng flash ổn **ở nhánh dễ nhất**; và 2 lượt không-gọi-tool của flash là dấu hiệu đúng ở
  chiều đó (F-31 nhìn từ phía model). ⟹ nghiệm thu **BẮT BUỘC có ca chuỗi nhiều bước**, nếu không
  nó chỉ lặp lại đúng lỗ hổng của probe.
- **§2b nâng lên BA model** (plus đã chốt · max mốc trên · **flash kẻ thách thức giá**) và đổi
  tính chất: từ *phép chọn model* thành **phép NGHIỆM THU**. Chốt trước ≠ miễn kiểm; ngưỡng giữ
  nguyên, **hỏng định dạng = 0** không nới. Trượt thì tester báo, KHÔNG tự lùi model.
- **HAI BẪY MODEL-BIẾT-SUY-NGHĨ (PO-agent đo, đã giao coder — `b2d9f4f` land bản đầu):**
  ① **trả lời RỖNG im lặng**: model tiêu `max_tokens` vào suy nghĩ thầm → `content` rỗng, **không
  exception, không mã lỗi** (đúng họ hỏng-im-lặng; nếu rơi giữa demo thì chatbot câm mà log sạch).
  ② **`reasoning_tokens` tính vào ĐẦU RA** ⟹ mọi ước tính chi phí đang ước THẤP. Tester đo được:
  **suy nghĩ chiếm 74% output ở plus, 91% ở flash** — bảng giá `eval/measure_quality.py:67` sai
  theo hướng có lợi cho ta, loại sai nguy hiểm nhất. Kèm: `cached_input_tokens` đọc
  `input_token_details` kiểu OpenAI có thể trả 0 im lặng trên Qwen.
- **🟡 SỰ CỐ NHÃN (tester tự bắt, 17/08) — nhãn sửa ĐÚNG nhưng sửa SAU KHI THẤY SỐ.** Nhãn cũ kỳ
  vọng `create_ticket` cho câu *"mở khiếu nại cho giao dịch bị trừ hai lần"*; **cả 3 model, 15/15
  lượt** đều gọi `get_customer_history` — nhất quán tuyệt đối giữa các model độc lập = **dấu hiệu
  nhãn hỏng, không phải model yếu**. Contracts xác nhận nhãn cũ sai hai lần (luật chung #1: số phải
  đến từ tool TRONG LƯỢT ĐÓ · `create_ticket` **không có trường `input`** nhận diện giao dịch).
  Chấm lại dữ liệu cũ: plus 80%→**100%**, max 80%→**100%**, flash 84%→**92%**.
  **Rủi ro thủ tục PO-agent nêu (nội dung đúng ≠ quy trình lành):** hướng sửa nâng chính model PO
  vừa chốt; nếu chỉ cần một lời giải thích hợp lý là sửa được nhãn hậu-kiểm thì *ngưỡng-chốt-trước*
  hết ràng buộc. ⟹ **3 điều kiện trước khi nghiệm thu chạy:** ① **security xác nhận nhãn** (đọc
  `contracts/`, KHÔNG đọc `tests/`, **không được cho xem bảng điểm** — phán quyết mù) ② **rà TOÀN
  BỘ nhãn còn lại theo cùng cách** (luật *vá một họ thì đi tìm họ*: ca này lộ vì cả 3 model cùng
  cãi; **nhãn sai mà model tình cờ chiều theo thì không bao giờ lộ** — mới là loại nguy hiểm)
  ③ **đóng băng + công bố bộ nhãn kèm băm file** trước khi chạy; sau đó phát hiện nhãn sai = **huỷ
  lượt đo và chạy lại**, không sửa tại chỗ. Biên bản phải ghi rõ nhãn được sửa SAU khi thấy dữ liệu.
  **✅ ĐÃ ĐÓNG (tester, 17/08):** ① gửi security 5 cặp câu-hỏi/tool **không kèm bảng điểm** (phán
  quyết mù) + tự nêu câu chưa chắc: *3 tool đòi OTP mà probe gọi thẳng API không có phiên OTP —
  nhãn có sai không?* ② rà cả 5 nhãn, 4 nhãn kia suy thẳng từ mô tả tool trong contracts, nay mỗi
  nhãn có trường `can_cu` trích nguyên văn ③ **đóng băng `eval/nhan_tool_calling_v1.json` SHA-256
  `c759b81c76ab` @ `8e264d9`**, và **`canh_bao_thu_tuc` nằm TRONG file** (ghi rõ ca 4 sửa hậu-kiểm,
  hướng sửa có lợi cho model đã chốt, số trước/sau 80%→100%) — người đọc sau mở file là thấy, không
  phải lục lịch sử chat. *Nguyên tắc rút ra: khai thủ tục phải sống cùng dữ liệu, không sống trong
  tin nhắn.*
- **🧊 LUẬT ĐÓNG BĂNG NHÃN (PO-agent ra 17/08, vá mâu thuẫn "bất động" vs "sẽ thêm ca"):** thêm ca =
  đổi file = **băng đã tan** — không ai cần cố ý làm bậy để chuỗi so sánh đứt. ⟹ ① `v1` đóng VĨNH
  VIỄN, sai thì sai vĩnh viễn trong sổ ② ca mới → **file `v2` băm mới, công bố TRƯỚC khi chạy**, có
  `dua_tren: v1@<băm>` + liệt kê chính xác cái được thêm ③ **điều kiện cứng: nhãn của ca mới phải
  viết TRƯỚC khi cho bất kỳ model nào chạy trên chúng** — ca 4 dạy rằng nhãn viết từ trực giác
  nghiệp vụ thì hỏng, nhưng **nhãn viết sau khi thấy model làm gì thì hỏng theo cách tệ hơn: nó
  luôn *có vẻ* đúng** ④ `v1→v2` = **đổi thước** ⟹ **cấm đọc `100% → x%` thành hồi quy**.
- **Câu OTP — phán quyết PO-agent (security có quyền bác):** nhãn đo **Ý ĐỊNH**, không đo việc lời
  gọi có được phép thực thi. Model chọn đúng tool = đạt, kể cả khi cổng OTP chặn ngay sau đó; trộn
  hai thứ = đúng **Luật 10d** (vô hiệu hậu quả rồi kiểm cổng). **Nhưng lộ ra khoảng trống lớn hơn:**
  probe gọi thẳng API không có phiên OTP ⟹ **chưa ai đo đường THẬT** — model làm gì khi tool bị từ
  chối vì thiếu OTP? Đó đúng là chỗ dễ đẻ bịa-số nhất (bị chặn, không có dữ liệu, vẫn phải trả lời
  khách). Ghi sổ, chưa xếp lịch. **Tester ghi tiếp (`66d4694`): đúng hình dạng F-32 nhưng do HỆ
  THỐNG gây ra chứ không do truy hồi trượt, nằm đúng trên ràng buộc cứng 3, CHƯA CÓ CA NÀO CANH**
  ⟹ *phải làm trước khi bất kỳ con số an toàn nào được công bố*.
- **Nhãn `v2` = `b4b85433a8a0` @ `98701de`** (3 ca chuỗi nhiều bước, nhãn viết TRƯỚC khi model nào
  chạy, trường `v1_v2` trỏ ngược `c759b81c76ab`, trong file ghi *"v1 và v2 là HAI THƯỚC"*). Tester
  làm xong TRƯỚC khi nhận luật — luật chỉ chép lại thành chữ thứ họ vốn đã làm.
- **PO-agent RÚT yêu cầu đổi tên trường `dua_tren`** — tester từ chối đúng: **đổi một ký tự là đổi
  băm đã công bố; churn băm vì lý do ĐẶT TÊN làm loãng chính cơ chế** (băm đổi được vì thẩm mỹ thì
  người đọc mất khả năng tin rằng băm đổi = nội dung đổi).
- **HOÁ ĐƠN ĐO LẠI (không được giả định chuyển giao):** An toàn 30/30 (cổng-96 · adversarial 45 ca
  · over-block 0/96) hiệu chuẩn trên gpt-4o-mini → **chạy lại TOÀN BỘ trên Qwen** ≈ 140 lượt. Free
  quota ⟹ tiền không còn là ràng buộc, **TPM là thứ phải xếp lịch**. Lịch: sau §2b, trước F-31/32.
- **Mệnh đề "Qwen tiếng Việt tốt hơn" vẫn CHƯA kiểm được:** tỉ lệ ký-tự/token tester đo (0,21-0,22)
  **không so được** với 2,43 của gpt-4o-mini — hai định nghĩa đếm khác nhau (tester chỉ đếm prompt
  gửi đi, không gồm system prompt sản phẩm). Tester tự bắt trước khi ai kịp dùng nó phán. Phải đo
  lại cùng định nghĩa; **cấm trích con số này cho tới lúc đó**.
- **Data residency thành việc THẬT (giao security, ưu tiên cao):** hội thoại khách giờ đi tới hạ
  tầng Alibaba Cloud. Cần 1 trang: ① vùng đặt endpoint `-intl` + NĐ 13/2023 Đ.25 ② điều khoản
  train-on-data **theo từng bậc** (free vs trả phí — nếu khác nhau thì đây là cờ đỏ vận hành)
  ③ **khai Qwen thuộc CỬA NÀO trong ADR-025** trước khi vào compose ④ lớp che PII trước khi gửi ra
  ngoài có đủ cho **tài phán mới** không — cần là *kết luận đã kiểm*, không phải mặc định. Mốc:
  **trước buổi demo tiếp theo**, vì mốc kích hoạt đã chốt là "dữ liệu thật ĐẦU TIÊN" (mentor gõ số
  điện thoại thật là đã tính), không phải "mở cho người ngoài".
- PO thật ĐÃ CÓ key. PO-agent đã đặt khối biến **chưa-hiệu-lực** vào `.env` local (QWEN_API_KEY +
  LLM_*/EMBEDDING_*/JUDGE_* comment sẵn) — không ảnh hưởng gì cho tới khi coder land code.
- **🔒 PO thật CHỐT 16/08: DÙNG API Qwen, KHÔNG tự host.** Nhánh khảo sát tự-host HUỶ (coder khỏi
  làm; số tham khảo đã có: 14B-Q4 cần 12-16GB VRAM · 32B-Q4 cần ~24GB · tool-calling tự host có
  lỗi thật đã ghi nhận · một máy để bàn phục vụ <20 người đồng thời — không đạt đích 100 CSKH).
  **Hệ quả phải theo dõi, KHÔNG được quên:** ① dùng API ⟹ ngoại lệ CÓ Ý THỨC với nguyên tắc ①
  của đợt ("không dữ liệu nào rời hạ tầng") — ghi vào ADR khi land, không để thành mặc định
  không ai để ý ② **"dùng Qwen" chưa đủ là một quyết định cho tới khi GHIM VÙNG** (Singapore /
  Tokyo / Bắc Kinh / Virginia — mỗi vùng một hồ sơ pháp lý khác) + đọc điều khoản train-on-data
  đúng sản phẩm+vùng ③ **hồ sơ đánh giá tác động chuyển dữ liệu ra nước ngoài (NĐ 13/2023 Đ.25)
  bổ sung vào CỔNG-TRƯỚC-DỮ-LIỆU-THẬT-ĐẦU-TIÊN** — khoảng trống này ĐANG tồn tại với OpenAI, độc
  lập với việc đổi sang Qwen (security đo: tin khách gõ rời hệ thống NGUYÊN VĂN, không scrub được
  vì agent cần chính cái nghĩa đó; S-01 đã chứng minh scrub chặn nhầm 40%).
- **Thiết kế: TÁCH CHAT KHỎI EMBEDDING** (chat→Qwen, embedding GIỮ OpenAI; đổi embedding = đổi
  VẬT, nạp lại kho + cắt chuỗi mọi số truy hồi). 4 chỗ: config.py (biến mới, fallback OPENAI_* ⟹
  không đổi hành vi mặc định) · graph.py:239 · store.py:41 · eval/_llm_judge.py:51. Kèm 2 nợ lộ
  ra: `RAG_EMBEDDING_MODEL` hardcode config.py:223; **judge dùng chung OPENAI_MODEL** dù docstring
  nói "tách biệt" ⟹ nếu đổi cả hai thì Qwen tự chấm Qwen (chờ coder xác nhận là finding hay tôi
  đọc nhầm).
- **THỨ TỰ — PO-agent TỰ ĐÍNH CHÍNH quyết định cũ:** trước nói "đổi model SAU F-31/32", SAI —
  F-31/32 là vá PROMPT phụ thuộc chặt cách model diễn giải MISINFO-002; vá trên gpt-4o-mini rồi
  đổi model = có thể làm lại từ chẩn đoán. ⟹ **đổi model → đo lại mốc nền trên Qwen → rồi vá
  F-31/32 trên chính model chạy thật.** Sửa một lần thay vì hai.
- **Hoá đơn đo lại (khai minh thị):** An toàn 30/30 hiệu chuẩn trên gpt-4o-mini → chạy lại TOÀN
  BỘ; + F-33 parse chuỗi 429 kiểu OpenAI · cached_input_tokens đọc input_token_details kiểu
  OpenAI (có thể báo 0 im lặng) · bảng giá measure_quality.py:67 · test_genai_spans assert
  "gpt-4o-mini". Tester đang soạn **kế hoạch đo lại** (danh mục mất-hiệu-lực từ phía thước · thứ
  tự + chi phí LLM · tiêu chí GO/NO-GO với ràng buộc *An toàn không được tụt một điểm nào* · cặp
  so sánh chỉ-khác-một-biến). Security được hỏi: data residency Alibaba Cloud (NĐ 13/2023 Đ.25)
  + điều khoản train-on-data.

## 🧭 HƯỚNG NGHIÊN CỨU SAU GATE — PO thật chốt 16/08 (từ đối chiếu workshop RAG + khảo sát OSS)
- **Vector DB: CHỐT QDRANT (PO thật, 16/08 tối)** — sau phân xử đủ hai chiều. Dữ kiện quyết định:
  PO thật xác nhận **đích thiết kế = 100 CSKH + khách không giới hạn** ⟹ multi-tenant/scale là
  YÊU CẦU không phải giả định ⟹ 3 lý do lật: (a) Postgres ví thật sẽ bận OLTP — nhét vector search
  vào cùng máy = hai tải giành nhau, "một kho" thành "một điểm nghẽn"; (b) collection-per-partner
  sạch hơn cột lọc; (c) tránh migrate 2 lần. Mối lo tất-định-thước GIẢI được: Qdrant có
  `exact=true` per-query — benchmark chạy exact, production chạy HNSW. **Điều kiện kèm:** kỷ luật
  hai-kho giữ vĩnh viễn (tem + canary + một-đường-nạp); bộ lọc ADR-026 GIỮ ở bước SQL không chép
  cờ sang payload; migration đo trước-sau 47 ca. **Thứ tự đầu tư cho đích 100-người:** ① nâng
  hạn mức TPM/model (PO mua sắm — nút cổ chai THẬT đã đo) ② LiteLLM proxy hàng đợi+budget ③
  reranker ④ Qdrant. Vector DB chưa bao giờ là nghẽn — TPM mới là.
  **CẬP NHẬT (PO thật cam kết 16/08 tối): tới giai đoạn demo/khách thật SẼ CÓ API LLM hạn mức
  xịn** ⟹ ① chuyển từ "chặn đường sống" thành "việc đã có chủ, kích hoạt theo lịch pilot"; thứ
  tự kỹ thuật còn lại: reranker → Qdrant → LiteLLM (vẫn đáng làm vì: hàng đợi chống burst-429 cần
  ở MỌI hạn mức, và hoá đơn token vẫn tỉ lệ thuận usage — T-series/caching là tiền thật kể cả khi
  quota rộng). Cổng-trước-người-thật (A1/A2-prod + đường-xoá + xoay-FIELD-key) KHÔNG đổi.
- Thứ tự nghiên cứu đã trình PO thật: ① reranker tại chỗ (bge-reranker-v2-m3 A/B ViRanker, Apache
  2.0, CPU) ② Qdrant ③ LiteLLM proxy (hàng đợi TPM + budget + cache Redis — điều kiện trước 150
  người) ④ Langfuse self-host (màn gán nhãn 30-ca + cost, thay-thế-được LangSmith mà không rời
  hạ tầng) ⑤ semantic cache CHỈ cho câu chính-sách-chung, đúng hẹn pilot. Đã bác bằng số của
  chính mình: HyDE, BM25/RRF thuần, LLM-chunking (② xổ số). MRR/NDCG mượn công thức RAGAS lắp
  vào script tester — thước-đã-rà vẫn là nguồn sự thật.

## 🔴 TRẦN TPM = RÀNG BUỘC CỨNG HƠN MỌI THỨ ĐANG TỐI ƯU (tester đo 16/08, `aa020d3`)
- Trần org **200k TPM**. Đo được: 15,4k/lượt (hội thoại mới) → **13,0 lượt/phút TOÀN HỆ THỐNG** ·
  25,7k (lượt 4) → 7,8 · 36,2k (trần đo) → 5,5. **150 người × 1 câu/2 phút = 75 lượt/phút** ⟹
  hội thoại ngắn cần 1,5tr TPM (**7,5× trần**), dài cần 2,7tr (**13,6× trần**). Chính phép đo
  (MỘT người, 21 lượt, 2 phút) đẩy org tới 193k/200k. ⟹ **T4 cắt lịch sử KHÔNG đủ** — cắt 36k→15k
  vẫn chỉ ~26 người. Khoảng cách là BẬC ĐỘ LỚN: cần nâng hạn mức tài khoản hoặc đổi mô hình —
  **quyết định của PO thật**, không phải đòn kỹ thuật. (Giới hạn của số: đo trên trần org hiện
  tại, và trần đó mua được.) Số này biện minh hồi tố cho quyết định hoãn 150-user test.
- **🔴 429 của OpenAI ra tới KHÁCH thành HTTP 500** — nhà cung cấp nói rõ "try again in 1.381s",
  khách nhận `{"detail":"Internal Server Error"}`. Không retry/degrade/thông báo. GIAO coder vá
  tối thiểu (retry+backoff theo đúng số giây trả về, hết khe thì câu xin lỗi tử tế thay 500).
  Rủi ro trực tiếp cho video demo Gate ⟹ **PO-agent lệnh tester DỪNG mọi phép đo tốn LLM** cho
  tới khi PO thật quay xong (chia sẻ tài nguyên, không phải đánh giá việc).
- **Bản vá F-31 REVERT** (luật không-có-số-lợi-ích): 9/16 mục không đạt, 2 ca đối chứng security
  giữ 8/8 nên không hại — nhưng land là gieo tiền lệ "chỗ này sửa rồi". **Manh mối cửa THỨ BA,
  lexical không phải ngữ nghĩa:** bỏ đúng chữ "tra soát" là hết từ chối (4/4 → 0/4) ⟹ nghi dòng
  `## Giọng văn` ("tránh thuật ngữ nội bộ: 'tra soát', 'đối soát'…") bị model khái quát từ *đừng
  DÙNG từ* thành *đừng ĐỘNG tới chủ đề*. Vẽ lại trục phạm vi bao nhiêu lần cũng không chạm tới.
  Chưa xác nhận (nghi cửa thứ tư cùng loại với "gian lận"/ràng buộc 4) — chẩn đoán ~10 lượt khi
  TPM rảnh, CẤM sửa prompt lần hai trước đó.

## 📦 GATE G2 — hạn 23:59 16/08, hồ sơ ĐÃ DỰNG (`gate/README.md`, `da4e51e`)
- **Conflict 3 PR ĐÃ GIẢI (PO-agent, worktree riêng):** `main` có 2 merge-commit (#5,#6) không
  có trong dev; xung đột DUY NHẤT `docs/STATE.md` (main là bản CŨ hơn). Giải một lần ở nhánh đầu
  (-X ours) rồi nối chuỗi B1⊂B2⊂B3 — hai nhánh sau 0 xung đột. Cả 3 nay **MERGEABLE**.
- **CI đỏ = runner org bị chặn billing** — coder chứng minh dứt điểm: `steps: []`, job chưa từng
  khởi động (test đỏ phải có bước và mất phút, không phải 2-3s). **Hệ quả khai minh thị: 3 PR
  #8-10 merge KHÔNG mang đảm bảo CI nào** (hiện-diện ≠ hiệu-lực áp vào chính cổng của ta). Thay
  thế tại chỗ trên HEAD #11 (`14a8c96`): contract-drift 3 file khớp baseline + invariants 23/23 —
  hai cổng quan trọng nhất xanh THẬT; 8 cổng còn lại (appsec/adversarial/migration/route-guards/
  frontend-lint/dep-scan…) KHÔNG AI CHẠY đợt này — khai rõ, không ngụ ý xanh.
- **Tester xác minh: production = stack RIÊNG** (đường dẫn đánh dấu qua app.adaptivealgo.uk →
  0 dòng trong log local) — phép đo local không chạm bản PO quay; đóng băng GIỮ vì TPM chung tài
  khoản. Hai việc rẻ cho coder sau gate: ① **dấu-build vào `/api/env-info`** (hiện không commit/
  phiên bản — "sản phẩm đang chạy không có nhãn vật"; hệ quả thật: KHÔNG kiểm được từ ngoài là
  production đã nhận vá 429 chưa) ② env-info production trả `env: "development"` — đặt biến đúng.
- Đã sửa dòng 6/8-2/8 trong benchmark-spec thành câu chữ đầy đủ (bẫy-đọc: phân số đứng trơ cạnh
  chỗ vừa sửa 2/8→2/10 — "không sai một chữ nào mà vẫn gây hiểu sai").
- **`env=development` trên production — truy xong (coder): `.env` chép từ Mac mang theo dòng
  chỉ-đúng-ở-dev** (APP_ENV vào qua env_file, cùng họ bẫy SSL_CERT_FILE — "`.env` càng được mang
  sang trung thành thì lỗi càng chắc chắn tái hiện"). Fix 2 dòng đã chuyển PO thật (sửa
  APP_ENV=production + restart backend, kiểm qua /api/env-info); rào dài hạn: thêm APP_ENV vào
  CỔNG 2 deploy_home (sau merge). **Thiết kế dấu-build DUYỆT**: BUILD_COMMIT qua build-arg (không
  đọc git lúc chạy — nhãn tự-thất-bại-im-lặng tệ hơn không nhãn) · build_at ISO có offset ·
  fallback "khong-ro" tự-tố-cáo. Coder GIỮ TAY mọi commit code tới khi #11 merged (headRef=dev —
  commit lúc này rơi vào PR PO thật đang cầm); thứ tự sau merged: đính-chính graph.py → dấu-build
  → cổng APP_ENV.
- 5 deliverable: ① video PO tự quay (kịch bản 8 màn sẵn) ② architecture ✅ ③ **≥10 PR — mở 3 PR
  dev→main: #8 RAG-đòn-4+kho · #9 F-LOG-3+T3 · #10 ADR-026+benchmark+gate/** (lát cắt tuần tự,
  tổ tiên lồng nhau, merge THEO THỨ TỰ; 7 đã merge + 3 = 10) ④ README ✅ ⑤ EVAL-EVIDENCE 7 ca ✅.
  Invariants 23/23 xanh trên HEAD trước khi mở PR. Sau #10 merged: `main` = dev ⟹ PO thật chạy
  `deploy_home` trên Windows là production nhận đủ.
- **ADR-026 ĐÃ LAND (`851cd7c`) — PO thật ký 16/08.** Trạng thái trong sổ: Đang hiệu lực.
- **🔴 T3 CHƯA ĐẠT <30k — thước mới lộ đúng trục (tester `ecf538a`):** token đi theo **VỊ TRÍ
  LƯỢT**, không theo câu (chạy đảo thứ tự thì số đảo theo; bản đầu của chính bộ đo nói dối, tester
  tự bắt). Chế độ `rieng` trần 14,3k (số 14,7k của coder nằm đây) · chế độ `don` trần **35,6k ở
  lượt 7**. **PO CHỐT: <30k áp chế độ `don`** (trần TPM bị chạm bởi hội thoại thật). ⟹ T3 giữ
  (−24%/lượt) nhưng **đòn token kế ĐỔI HÌNH: cắt LỊCH SỬ HỘI THOẠI** (early-stop/tóm tắt/cửa sổ
  trượt), không cắt thêm tool-result; lượt 47-84k hồi T1 giải thích xong. Latency: trung vị
  5,2-5,9s, không ca nào >10,4s, KHÔNG tương quan độ dài input ⟹ câu kết trục Hiệu năng: *muốn
  tối ưu thì tối ưu SỐ VÒNG ReAct, không phải kích thước prompt*. `--lap 3` duyệt chạy lấy dải.
- **Xoay secret production (security xác nhận + siết 2 chỗ):** JWT xoay NGAY — **không phải rủi
  ro lý thuyết**: security đã tự đúc token hợp lệ `create_access_token(USR-0201, cskh)` trên dev
  lúc probe F-LOG-3, và DB prod mang từ dump Mac nên user đó tồn tại (họ KHÔNG thử lên live —
  ngoài quy tắc chỉ-đọc). Nguyên tắc phân biệt: *key cho hành động từ xa → xoay ngay; key chỉ mở
  dữ liệu đã bị lấy → xoay theo lịch*. **Chỗ hở phải bịt cùng lúc: production giữ `.env` RIÊNG,
  deploy KHÔNG ghi đè** — không thì lần deploy tới chép đè là key lại trùng, không ai biết (đây
  mới là bản vá; xoay key chỉ dọn hậu quả). `.env` KHÔNG nằm trong git (đã kiểm) ⟹ trùng là do
  chép tay khi deploy. Xác nhận bằng HÀNH VI sau xoay: đăng nhập mới OK **và** token ký bằng key
  cũ bị từ chối (security làm được nếu PO mở cửa sổ). Sửa mốc cổng: **"trước DỮ LIỆU THẬT ĐẦU
  TIÊN"**, không phải "trước khi mở người ngoài" (demo mentor gõ SĐT thật là đã có dữ liệu thật).
- **4 CÂU PRODUCTION — PO THẬT TRẢ LỜI ĐỦ (16/08 tối):** ① deploy từ `main`; nhịp release chốt:
  "code hôm nay done test ok thì cho lên main" (PO-agent điều phối link PR) ② secret TRÙNG dev
  → xử lý: xoay `JWT_SECRET_KEY` NGAY trên Windows (rẻ, chỉ rớt phiên mở); `FIELD_ENCRYPTION_KEY`
  GIỮ (xoay không re-encrypt = mất dữ liệu vĩnh viễn — DB prod mã bằng key Mac); nợ coder: script
  xoay-có-re-encrypt, kích hoạt trước người-dùng-thật ③ `LANGCHAIN_TRACING_V2` KHÔNG có — F-30
  production ĐÓNG ④ live = demo đội+mentor, chưa người ngoài. **CỔNG-TRƯỚC-NGƯỜI-THẬT (ghi
  chính thức):** mở người ngoài CHỈ KHI: A1/A2 đã lên production + đường-xoá dữ liệu + xoay
  FIELD-key có re-encrypt.
- **② KHÉP — KẾT QUẢ ÂM (như T1), 3 nếp mới thành chuẩn:** thí điểm chèn-câu-hỏi trượt điều
  kiện (a): 1/6 × 2 lần, HAI prompt độc lập cứu HAI ca KHÁC nhau (lần 1 cứu RAG-37 lần 2 làm nó
  tụt; tổng luôn 20/47) = XỔ SỐ không phải cơ chế; 4 ca chôn sâu >100 bất động. Điều kiện (b) 0
  ca rơi — cả hai lần. Nếp: (i) đo KHÔ không đụng kho-chung + hiệu chuẩn phép đo trước (Chroma =
  L2 bình phương, khớp 0.900776/0.900798); (ii) khai luật-dừng TRƯỚC lần 2; (iii) từ chối quay-
  số-tới-khi-khớp-bộ-test ("land kiểu đó, số sụp khi tester đổi cách hỏi"). **Hội tụ 3 đường độc
  lập: truy vấn NGẮN-GIỌNG-THƯỜNG-BÁM-TỪ-KHOÁ thắng** (agent tự viết lại ăn RAG-37 · HyDE thua
  vì dài-trang-trọng · prompt A sinh câu FAQ-ngắn trúng hạng 1) ⟹ **đòn-kế-có-căn-cứ: bắt buộc
  viết-lại-truy-vấn có mẫu — CHƯA phát lệnh**, xếp sau F-31/32 (hai lẽ: không trộn 2 bản vá
  prompt; RAG-38/40 chưa từng đi tới truy hồi — nền số ToS đổi sau F-31/32, đo trên nền mới).
- **top_k /policy-search: 4 là chủ đích (RAG_SEARCH_TOP_K) nhưng NUỐT-IM-LẶNG field k của client
  là bug** (Pydantic vứt field lạ — cùng họ bo_qua_thieu_chunk; chính coder cũng dính: gửi k:3
  nhận 4 in "4 kết quả" không hỏi). QUYẾT: làm CẢ HAI một commit — top_k Field(4, ge=1, le=8) +
  extra="forbid", grep caller BFF gửi field thừa sửa cùng commit. Chen trước F-31/32.
- **F-31+F-32 GỘP MỘT VÉ (khung security, chốt thành ràng buộc thiết kế):** hai finding kéo
  ngược nhau trên CÙNG luật MISINFO-002 (prompt.py:52-60 — security loại trừ tier/lọc-trước-graph
  bằng đo: không mã nào chặn truy vấn trước truy hồi, refusal = LLM tự theo prompt; "pháp lý
  phức tạp" là tiêu chí từ chối chỉ rào bằng "không liên quan giao dịch ví"). Vá độc lập = đá
  nhau vô hạn (Luật 8, lần này THẤY TRƯỚC). Ràng buộc: ① trục đổi "pháp-lý?"→"về-ví-NÀY?" ②
  đường thứ ba cho câu trong-phạm-vi-màu-pháp-lý: TRÍCH-được HOẶC không-tra-được+escalate (cấm
  từ-chối-ngoài-phạm-vi, cấm "tuy nhiên thông thường") ③ CẤM nới MISINFO-002 trước khi có đường
  thứ ba (lằn ranh MT-F02/F-22/CTRL-002 giữ) ④ đặc tả viết trước trong hồ sơ vé — security rà
  văn bản trước land, tester viết test từ đặc tả, nghiệm thu đo CẢ HAI ĐẦU cùng lượt + MT-F02/
  cổng-96/adversarial xanh nguyên. Bối cảnh vé: mọi số ToS hiện đo trên đường agent chưa từng
  đi tới (0 tool call) — chấm lại toàn bộ sau vé. §D security tự nhận sai chiều (index-thô HỤT
  không nống) — ca mồi-neo phải neo cả chiều agent-viết-lại.
- **Thứ tự coder chốt:** top_k → F-31/32 → đo lại T3 (chờ bộ-lệnh tester) → đòn viết-lại (thí
  điểm có đo, nền mới) → T4/T2.
- **🔴 CỔNG TUÂN-THỦ ToS SẬP MỆNH ĐỀ (tester chạy 8 ca đường agent): 4/8 đường thoát KHÔNG hoạt
  động** — (c) đúng 2 · (a) từ-chối-an-toàn 2 (RAG-47 đòi OTP step-up = ĐÚNG) · **(b) diễn giải
  2: RAG-41** (hỏi trách-nhiệm-pháp-lý, trả lời bằng chunk cashback, chắc nịch) + **RAG-43**
  ("chưa tìm thấy… **Tuy nhiên, thông thường**: 1.…" — TỪ-CHỐI-RỒI-TRẢ-LỜI-TIẾP = bịa có vỏ bọc,
  bộ chấm dò chuỗi "chưa tìm thấy" sẽ chấm ĐẠT; vào chuẩn viết test: kiểm cả phần SAU câu từ
  chối) · **loại thứ TƯ — từ-chối-SAI-PHẠM-VI 2: RAG-38** ("gửi tra soát bằng cách nào" = chính
  nghề sản phẩm!) + **RAG-40** (chạm vùng ràng buộc 5), cả hai 0 tool call, guardrail chặn trước
  truy hồi, VÔ HÌNH với mọi trục đo. **F-31** (sai-phạm-vi, ưu tiên cao) + **F-32** (diễn-giải)
  GIAO coder xếp sau ②-thí-điểm. Benchmark ghi "2 finding mở", KHÔNG ghi giới-hạn-đã-biết.
- **THƯỚC INDEX-THÔ HỤT (đảo chiều §D):** agent TỰ VIẾT LẠI truy vấn trước khi tra (RAG-37:
  "bao lâu có kết quả"→"thời gian xử lý khiếu nại"→HẠNG 1; thước hỏi nguyên văn thì trượt) ⟹
  security lo index-thô nống, đo thật ra HỤT. Hệ quả coder: HyDE-âm ≠ viết-lại-vô-dụng (âm là
  viết-lại-thành-văn-điều-khoản; đang thắng là viết-lại-thành-truy-vấn-ngắn). Chấm-MỐC đường
  agent càng nặng vai.
- **METRIC ĐỔI @3→@4 (PO duyệt, cắt chuỗi):** sản phẩm luôn đưa agent 4 kết quả (top_k bị bỏ
  qua — coder xác nhận chủ-đích/bug) ⟹ Recall@4 = 48,9% (23/47) = số sổ sách → benchmark v0.4 =
  88,0% kèm 2 finding mở. Dải chẩn đoán @1 27,7% · @3 40,4%. 24/47 ngoài top-4 ⟹ nới k không
  phải đòn chính. Mẫu số ToS chốt 2/10 (tester đếm sót 2 ca, tự sửa).
- **✅ T3 LAND (`99de792`) — input/lượt 19.397→14.698 (−24%) trên câu đo của coder.** Chẩn đoán:
  `get_customer_history` complaints KHÔNG limit/không lọc days = 13.620 ký tự = 41% toàn prompt
  (107 phần tử). Thiết kế: BẢN TRẢ LLM cắt còn 10 complaints (4.707 ký tự) · BẢN GHI DB nguyên
  vẹn 107. **LUẬT MỚI (coder tự dựng): cổng nghiệm thu PHẢI CHẠM ĐƯỜNG THAY ĐỔI** — origin-rule
  0/5 + o-group 0/8 xanh nhưng không chạm đường T3 ("nhận chúng làm bằng chứng là tự lừa");
  bằng chứng thật = ca đúng-rủi-ro: agent thấy 10 bản ghi nói "105/107" (tra ngược được), KHÔNG
  nói "10". **<30k CHƯA tuyên bố đạt** — chờ bộ-lệnh-cố-định đo token+latency (GIAO tester, gộp
  việc backlog "bộ đo latency thay n=8"); coder đo lại lượt dài 47-84k khi thước về. T3 đóng
  ngoài thứ tự = ngoại lệ chấp nhận (code-dở-cây-chung rủi ro hơn), không thành nếp.
- **② điều kiện (c) GIẢI QUYẾT — kiến trúc TÁCH SẴN tìm/trích:** store.py::add_chunks embed
  texts nhưng Chroma documents=chunk_ids (placeholder); văn bản trả LLM lấy từ PolicyChunk.text
  Postgres ⟹ dòng chèn ② chỉ đi vào embedding, không có đường lọt ra khách. Coder thêm docstring
  bất biến tại chỗ chèn. ②-thí-điểm ĐANG CHẠY (hô 4 phiên trước khi nạp).
- **ADR-026 BẢN THẢO XONG (`a65e9fc`, docs/security/…-ban-de-PO-land.md) — TRÌNH PO THẬT KÝ.**
  8 quyết định = 4 điểm PO chốt + QĐ5 (eval đánh dấu ĐÃ-duyệt — mô hình đe doạ là đối-tác-bị-
  chiếm, cờ bỏ-qua-lọc bị bác vì là lớp lỗi F-30) + 🔴QĐ6 (xuất-xứ ≠ thay tier, quyết định riêng
  chống-gỡ-nhầm) + 🔴QĐ7 (nạp-lại GIỮ trạng thái duyệt theo (filename,băm-file) — không thì bảo
  trì thường quy làm agent mù; chính lượt 08:42 đã-sửa-sự-cố sẽ là ca vấp đầu tiên) + QĐ8 (2
  tầng: dây-bẫy contracts/rag-nguon.yaml LÀM NGAY khớp xfail 55118b5 · trạng-thái-duyệt DB khi
  onboarding thật; bác cả hai phương án đơn lẻ). Điểm rà PO-agent: chuyển tiếp production đang
  cầm kho PDF — manifest chỉ có 2 DOCX, dây bẫy phải land CÙNG nhịp release đòn-4 lên production.
- **Ý kiến tuân thủ ToS (security): XÁC NHẬN CÓ ĐIỀU KIỆN KHÔNG-NHÂN-NHƯỢNG** — "an toàn tuân
  thủ VÌ VÀ CHỈ VÌ đường thoát 'không tra được→người thật' đã được XÁC NHẬN hoạt động; chưa đo
  thì mệnh đề chưa đứng". Ca lo nhất: top-3 trả chunk-lân-cận-SAI điểm cao ⟹ agent tưởng tìm
  thấy ⟹ diễn giải thay vì từ chối (trục âm-bản-GẦN chưa có ca canh). ĐÃ GIAO tester: chạy các
  ca ToS trượt qua đường agent, phân loại (a)không-tra-được=đạt (b)diễn-giải-từ-chunk-lạc=TRƯỢT
  NẶNG báo ngay (c)đúng-nhờ-đường-khác=ghi chú; + chốt mẫu số ToS (2/8 vs 2/10 đang lệch).
- **Version-drift HIỆU CHỈNH XUỐNG (security tự đo lại):** origin/main ĐÃ CÓ đủ A1+A2·S-03·F-30·
  F-29·F-28/e·note/ADR-024·CI-appsec — production KHÔNG hở lỗ bảo mật; thiếu duy nhất F-LOG-3 +
  7 commit RAG/observability hôm nay ⟹ lý-do-redeploy là quan-sát-được, không phải vá-khẩn.
  (Bài học security tự ghi: main local là nhánh chết 1 commit — đọc origin/main, đo hai lần
  trước khi kêu.)
- **THƯỚC RÀ HAI PHÍA XONG — 39,4% LÀ SỐ SẠCH, mặt trận truy hồi MỞ LẠI (16/08):** phía trượt
  28/28 công bằng (0 nhãn hỏng; 15 ca nghi-oan ban đầu là bẫy truy-vấn-ngắn-embed-kém — kiểm
  đường độc lập 15/15 lành, suýt làm cả đội sửa 15 nhãn lành) · phía đạt 0/47 chuỗi lỏng. Bản đồ
  phủ vào chỗ cố định eval/do_phu_kho.py + phu_kho.json (`ed654b9`, băm `5b5dbc12719f`): ToS
  97,1% · FAQ 87,4% (tester tự bắt 2 lỗi thước của mình: "mục 15 thiếu" = chỉ tra 340/378; "FAQ
  81%" = mẫu số đếm cả 146 dòng mục-lục đã-cố-ý-vứt — "đếm cái ta chủ động vứt thành cái ta đánh
  mất"). **②-THÍ-ĐIỂM PHÁT LỆNH cho coder** (3 điều kiện mở-lại đều thoả): 5 chunk từ bộ RAG-37/
  47/39/41 (khách hỏi "bao lâu có kết quả" ↔ chunk "không quá 45 Ngày Làm Việc" — khoảng cách
  VĂN PHONG không phải chủ đề; giải thích luôn vì sao FAQ tốt hơn ToS); nghiệm thu: ≥3/5 chuyển
  đạt + TRỌN 47 ca không ca-đang-đạt nào rơi + dòng-chèn-không-được-trích-cho-khách (nếu không
  tách được phần-tìm/phần-trích thì DỪNG); xếp sau F-LOG-3 trước T3. Caveat đã ghi: HyDE âm
  (1/47) = sửa-phía-CÂU-HỎI đã có điểm âm; ② = sửa-phía-NỘI-DUNG offline là chiều chưa đo.
- **Kho PRODUCTION SẠCH (PO-agent đo chỉ-đọc qua HTTPS):** GET /policy-docs trên live = đúng 2
  PDF MoMo (uploaded 07:24, 362 chunk) — sự cố .md CHỈ ở stack local, không có sự cố production.
  NHƯNG lộ **version drift**: production = snapshot TRƯỚC đòn 4 (kho PDF cũ) + `deploy_home.*`
  pull `main` ⟹ máy Windows nhiều khả năng chạy code cũ hơn hôm nay. Đang hỏi PO thật: nhánh
  deploy · secret khác dev? · `LANGCHAIN_TRACING_V2`? · live = demo đội hay người thật? (3 câu
  sau là F-30/secret/pilot-cam-kết của security, nay tăng hạng vì có production thật). Kế tiếp:
  một nhịp release dev→main + redeploy CÓ TRẬT TỰ — coder không tự đẩy main trước khi chốt.
- **CHẨN ĐOÁN ToS XONG (coder) — 5 SỐ ÂM LIÊN TIẾP, quyết ①+③:** kho ổn (0/10 thiếu nội dung) ·
  embedding ổn (8/8 ca trượt lên hạng-1 khi hỏi bằng chính văn chunk) ⟹ lỗi = khoảng cách
  hỏi-đời-thường↔viết-pháp-lý. Top-3 của ca trượt = 79% FAQ = đúng tỉ lệ nền kho (truy hồi không
  thiên vị, chỉ không phân biệt nguồn). 5 cơ chế đo đều âm: BM25 0/10 · RRF 3/10 (FAQ chưa đo) ·
  trộn-nguồn 17/47↓ · HyDE 1/47↓↓ · RRF+HyDE 8/47↓↓. HyDE datum giữ: cứu ca chôn sâu (>100→8)
  nhưng phá ca đang đúng — sống lại nếu có bộ phân-loại-ca-khó. **QUYẾT: ① ToS 2/10 = giới-hạn-
  đã-biết** (câu pháp lý nên escalate người thật; ràng buộc 3 làm trượt-truy-hồi thành hành vi AN
  TOÀN "không tra được"; chờ security 1 dòng góc tuân thủ) **+ ③ không chọn đòn trên thước FAQ
  chưa rà; ② (chèn câu-hỏi-tương-ứng vào chunk ToS) ĐỖ BẾN** — mở lại khi: thước FAQ sạch + ToS
  vẫn ưu tiên theo số + đo trước 5 ca. `GET /api/session` 405 = CHỦ ĐÍCH giữ nguyên (BFF: 34 chỗ
  đọc getServerSession server-side, không mở thêm cửa phát thông tin phiên).
- **🔒 ÁN KHO ĐÓNG — PO thật xác nhận chính họ upload 2 file .md qua UI Đối-tác-ví ~15:23** (tai
  nạn quy trình, không xâm nhập, không ai có lỗi). Khớp trọn chuỗi bằng chứng (IP frontend ·
  nhịp UI POST→GET 20-40ms · 13s giữa 2 lượt). Câu hỏi đầu tiên của PO thật khi nghe tin — "đối
  tác ví có luồng riêng là đã quản lý được rồi đúng không?" — vào phần động-cơ ADR-026: người
  vận hành thiện chí TIN tách-vai = kiểm-soát-nội-dung, và sự cố chứng minh niềm tin đó sai.
- **§15-ToS ĐÓNG — nghi vấn bị chính người nêu tự bác bằng đo:** phủ ToS = 198/206 đoạn (96,1%);
  mục 15 đủ 6/6; **mục 19 (tra soát & khiếu nại) đủ 11/11 TRONG KHI 6/8 ca ToS trượt hỏi đúng
  mục 19** ⟹ ToS 2/8 chắc chắn là lỗi TRUY-HỒI-thứ-đã-có, tín hiệu sạch nhất ngày. 8 đoạn vắng =
  mảnh vụn gạch-đầu-dòng, QUYẾT ĐỊNH không vá (riêng [210] hotline ghi biên-biết-trước — còn ở
  19.3). Lần thứ TƯ trong ngày họ lỗi "không-thấy-bằng-cách-A ⟹ không-tồn-tại" nhưng lần ĐẦU
  người mắc TỰ bắt trước khi ai phải đo lại. **Đầu bài coder đặt lại (sau F-LOG-3, trước T3):
  CHẨN ĐOÁN 6 ca ToS trượt** (top-3 trả gì · khoảng cách embedding · giả thuyết lệch văn phong
  khách-hỏi↔chunk-pháp-lý) rồi mới chọn đòn — không lặp T1. Tester chạy thêm bản đồ phủ FAQ
  (0 LLM) → đóng câu 29-chunk-không-lộ; hai bản đồ phủ vào eval/ (không để scratchpad).
- **ADR-026 (xuất-xứ kho RAG) ĐANG SOẠN — security, sau khi ĐO (`d578d0d`):** chi phí rẻ bất ngờ
  (cờ ở PolicyDocument, backfill 2 DÒNG; serve = 1 mệnh đề SQL vào bước join sẵn có; không đụng
  Chroma; recall-cost 0 khi vận hành bình thường). **Phát hiện quyết định (security tự bác đề
  xuất gốc):** ghi ĐƯỜNG NẠP không chặn được sự cố — file đi qua đúng cửa hợp lệ; phải là TRẠNG
  THÁI DUYỆT tách khỏi hành vi nạp. Khuyến nghị PO-agent đã chuyển security soạn (chốt = PO thật
  ký, quy trình §3): ① mọi upload vào `cho_duyet`, **supervisor** duyệt (maker≠checker mở rộng
  nhất quán sang kho tri thức; partner_admin tự duyệt = tái tạo sự cố 1 click) ② backfill 2 doc
  MoMo = `da_duyet` có-chủ-đích ③ thấy chưa-duyệt: partner_admin CÓ · agent KHÔNG · CSKH CÓ kèm
  badge «CHƯA DUYỆT» (giữ Y5 người-là-máy-dò, không để dựa nhầm làm căn cứ) ④ mục riêng: xuất-xứ
  ≠ thay lọc tier (hai mối đe doạ, hai cơ chế). Kèm `contracts/rag-nguon.yaml` khớp chuỗi xfail
  `55118b5`. **Va chạm tên bắt kịp lúc rẻ:** `nguon` (F-LOG-3, đường ĐỌC) đổi thành `duong_tra`;
  `nguon_nap`+`trang_thai_duyet` dành cho đường GHI — coder đang đổi. Điểm mù công cụ (họ C4):
  grep "ingest_document(" bỏ sót call-site truyền-hàm-như-tham-chiếu (`_handle_tool_error(
  ingest_document, ...)`) — chỉ lộ khi truy ngược từ endpoint.
- **LUẬT MỚI (tester): nhãn định danh LƯỢT ≠ nhãn định danh VẬT** — `new_id("CHK")` ngẫu nhiên ⟹
  nạp cùng nguồn+parser vẫn ra băm khác (6e3c11…→8820b6…→a3c5c7… là MỘT kho). "Băm khác ⟹ kho
  khác" SAI; chỉ chiều "giống ⟹ giống" đúng. So hai lượt bằng chunk/doc/parser. Đề xuất route
  coder (chưa quyết): `_bam_kho` chỉ băm sorted(text), bỏ chunk_id ⟹ băm định danh được VẬT.
- **Biến thể #4 luật assertion-trùng-mặc-định** (tester bắt trong chính test của mình `55118b5`):
  hai vế CÙNG KIỂU (set[str]) nhưng khác KHÔNG-GIAN-TÊN (doc_id-băm so với filename) — không bao
  giờ khớp, test xanh mà chặn con số 0. Bắt bằng CA ĐỐI CHỨNG: đổi danh sách sang tài liệu ĐANG
  có thật trong kho → test phải đỏ (đã đỏ đúng: 'MoMo_ToS.docx'). Fix: lấy tên thật từ
  `policy_documents.filename` ∩ doc_id-có-vector, fail-nếu-index-rỗng. `55118b5` = chuỗi
  xfail(strict)-đẻ-nghĩa-vụ: đặc tả `contracts/rag-nguon.yaml` xuất hiện → XPASS → strict đỏ →
  buộc người kế bật cổng thật; file contract đó sẽ ra đời cùng gói ADR xuất-xứ (quy trình §3).
- **Bug kho tra-rỗng-không-tất-định: coder ĐÃ root-cause** (docstring `_server_dang_cam_kho_cu`):
  `chromadb.PersistentClient` không dùng chung persist-dir giữa 2 tiến trình — `nap-lai` chạy
  docker-exec riêng, server giữ segment CŨ đã bị xoá → tra rỗng, HTTP 200, không log lỗi; mọi
  công cụ kiểm (tiến trình riêng) mở client MỚI thấy kho mới → cả ba đèn xanh trong khi sản phẩm
  trả rỗng. **Khắc phục: sau `nap-lai` PHẢI restart backend**; `kiem` nay có cổng-cuối phát hiện
  (dấu `nap_lai_luc` do riêng nap-lai đặt — mtime chroma.sqlite3 ĐÃ THỬ VÀ SAI vì server cũng ghi
  WAL). Mở rộng: bước restart cần vào cả `deploy_home.*` (kho_rag nap-lai trong script deploy).
  Tester thêm cổng canary vào benchmark (3 truy vấn tối giản, rỗng cả 3 = DỪNG không đo) sau khi
  SUÝT báo 0,0% làm số sản phẩm.
- **Hướng thiết kế sự cố (security chủ trì, probe kế tiếp):** chặn đuôi file = đóng cửa TAI NẠN,
  không đóng cửa QUY TRÌNH (.docx nháp vẫn vào cửa hợp lệ). Whitelist tên file ở serve = SAI
  (chặn onboarding đối tác thật). Hướng nghiêng: **XUẤT XỨ trên chunk** (nguon_da_duyet) — đúng
  hình dạng origin-rule cho RAG, xử cả ca-tai-nạn lẫn ca-eval-cố-ý. Chưa đo chưa đề xuất; không
  ai code trước khi có số + ADR. Tester (trong lúc chờ kho): ca hồi quy chặn-thành-phần-tài-liệu,
  danh mục lấy từ ĐẶC TẢ không hardcode 2 tên PDF.
- **QUY ƯỚC MỚI (PO phát 16/08):** kho RAG đang-phục-vụ là VẬT DÙNG CHUNG của 4 phiên — không ai
  nạp thẳng vào nó để test. Cần kho thử → collection/CHROMA-path riêng trong scratchpad (như
  run_adversarial_set dùng DB tạm). Đổi kho phục vụ CHỈ qua `kho_rag.py nap-lai` + hô cả 4 phiên.
- **MỐC 35,7% VÔ HIỆU KÉP** — hỏng cả THƯỚC (tester tìm ra `bo_dau()` không gộp khoảng trắng ⟹
  cụm ≥2 từ vắt qua xuống-dòng = TRƯỢT GIẢ, ngược hướng với pass-giả cũ) lẫn VẬT (57 chunk rác
  nội bộ nằm trong kho lúc chấm, có thể chiếm top-3). Chuỗi so sánh trục Truy-hồi CẮT tại đây
  (Luật 6). **KHÔNG ghi delta đòn 4 nào** cho tới khi tester trả cặp sạch: thước-đã-vá × kho-sạch
  (nền phải là `f9b06f9983bc`, không phải kho lúc 08:23).
- **Đòn 4a+4b LAND (`1481074`), tách 3 mốc băm:** nền PDF-đã-gỡ-md 362 `f9b06f9983bc` · 4a DOCX-
  parser-cũ 333 `71bb841435ea` · 4b DOCX-giữ-cấu-trúc 378 `6e3c11fb04f4` (đang phục vụ). Số CẤU
  TRÚC (đếm được, không phụ thuộc thước truy hồi): chữ-vỡ-từ-điển 131→0 · hàng bảng bank vào kho
  0→25 · chunk mồ côi nhãn 61%→36%. Ca đối chứng 4b: docx thường ra chuỗi GIỐNG BYTE bản cũ;
  upload partner_admin không đổi hành vi. 36% mồ côi còn lại = đuôi khối dài cắt theo kích thước
  — coder CHƯA làm chưa hứa, quyết sau khi có số cặp sạch.
- **Hai đính chính coder tự khai:** ① "đòn 1 quét sạch lớp một" SAI — lớp `[aeiouyăâêôơư]` thiếu
  ký tự dựng sẵn có dấu (`ị`,`ồ`,`ế`) ⟹ `đ ịnh`,`g ồm` lọt, tester đếm đúng ~53 còn lại; đáng ghi:
  coder CẦM bằng chứng bác mình (list 131 chứa `b ất`,`đ ịnh`) mà phát biểu ngược — lỗi đọc-lướt-
  số-của-chính-mình, cùng họ với bài coder-tự-nghiệm-thu. ② Hai thước cùng tên: băm trong
  `kho_chunks.tsv` ≠ `kho_rag.py::_bam_kho` — chỉ tin băm in từ `kho_rag.py nhan`.
- Coder chuyển sang **T3** (truncation tool-result; cổng-96 + origin-rule phải xanh nguyên, đo
  input-tokens/lượt trước-sau cùng bộ lệnh, tham chiếu <30k/lượt).

## ✅ UI-02 ĐÓNG + ĐÒN 4 THÀNH 4a/4b — bảng-23-hàng là lời giải bài chôn (16/08 đêm)
- **UI-02 nghiệm thu 5/5** (đối chứng 1/5 trên image-chưa-vá, A2 tái hiện nguyên văn lỗi PO demo).
  Mẫu thiết kế nghiệm thu UI ghi lại: **đếm REQUEST không đếm pixel** — vá-giả (reset ref quên
  deps) hiện nút y hệt mà không request nào đi; B2 bắt bằng 1→2 request. Nợ: e2e vào repo
  (coder thêm dep playwright · tester dựng sau chuỗi benchmark).
- **Đòn 4 hồ sơ tiền-đề-sai-kết-luận-đúng:** "215 chữ vỡ trong kho" SAI (tester đếm PDF thô; kho
  đã qua đòn 1) — nhưng thước độc lập từ-điển-DOCX lộ **lớp vỡ THỨ HAI: 131 lần/52 dạng cả đòn-1
  lẫn luật-đếm-tester đều mù** (`ho ặc`,`kho ản` — vế trái có nguyên âm). Soi đối xứng PDF↔DOCX:
  DOCX sạch 0 vỡ + đủ hơn (17-vs-9 câu thiếu). **4a GO** (đổi nguồn nạp).
- **4b DUYỆT mở phạm vi `parsers.py` (gồm upload partner_admin), 4 điều kiện** (một-parser-dùng-
  chung đúng thiết kế · ca đối chứng upload-docx-thường · bảng→mỗi-hàng-một-chunk-mang-tên-thực-
  thể · đo trên thước 35,7% tách 4a/4b nếu rẻ). **Phát hiện chốt: "20 đoạn gần-trùng" thật ra là
  MỘT BẢNG 23 hàng (bank·viết-tắt·hạn-mức) bị PDF nghiền thành cháo** — `_extract_docx` hiện vứt
  heading + KHÔNG đọc tables. 4b = chunk theo H3 (mỗi FAQ-bank một heading có sẵn tên) ⟹ chunk-
  theo-thực-thể MIỄN PHÍ. **ĐÍNH CHÍNH nhận định cũ**: "đòn 4 không chữa được lớp chôn" — sai với
  4b; 4b chữa được vì tách bảng thành 23 dòng riêng.
- Coder GIỮ TAY nạp-lại chờ tester nhả khe (362 chunk_id sẽ đổi giữa lúc họ rà nhãn) — quy ước
  báo-trước-đổi-vật chạy đều. Danh sách chunk_id đã đổ cho tester (băm 8a3185199493).

## 🔍 ĐIỀU TRA CHUNK-CHÌM XONG: KHÔNG PHẢI RÁC — CHÔN-DO-GẦN-TRÙNG (16/08 tối)
- Tester tự sửa số 47%→**31,5%** (thước lại là thủ phạm: 160 câu quét đều là câu FAQ mà kho có 2
  tài liệu; quét lại 340 truy vấn → 82/260 chunk FAQ không bao giờ nổi với chính câu sinh ra
  chúng; 60 chunk ToS "chìm" chỉ là chưa-hỏi-tới). **Mẫu 20/20 = nội dung THẬT bị chôn, 0 rác.**
- **Cơ chế: GẦN-TRÙNG** — ~20 đoạn hướng-dẫn-liên-kết-bank gần y hệt (khác mỗi tên bank): một
  truy vấn lấy 3, 17 cái vĩnh viễn chìm. Nhóm chìm CHỨA đáp án các ca đang trượt (RAG-08/22/23/
  29) — nguyên nhân thứ hai của RAG-22. **Đòn 4 DOCX không chữa lớp này.**
- Hướng đề xuất (tester, CHƯA đo): **chunk-theo-THỰC-THỂ** (mỗi bank một chunk có nhãn tên) —
  coder trả lời khả thi trước, tester dựng ca đo sau. Thứ tự: đòn 4 trước (rẻ, chắc) → chống-chôn
  theo số. Còn mù: 29 chunk (8%) không lộ bằng cách nào — coder đổ danh sách chunk_id cho tester.

## 🎯 ~~THƯỚC ĐÃ RÀ — 35,7%~~ ⚠️ VÔ HIỆU KÉP 16/08 (bo_dau + 57 chunk rác — xem mục SỰ CỐ ở trên)
- Luật chuỗi-đặc-trưng (3 cửa: có-trong-đáp-án-đúng-biên · sống-qua-trích-PDF · ≤2 câu FAQ) +
  xác minh nhãn bằng ĐƯỜNG ĐỘC LẬP (quét kho bằng 160 câu nguồn → 31/35 chuỗi có thật trong kho
  ⟹ trượt THẬT). Khoảng bất định siết từ 25,7 điểm còn 4,6 (cận trên 40,3% nếu 4 ca chưa-kết-luận
  đều nhãn hỏng). **12/12 pass-giả lộ diện** (9 nghi + 3 chưa nghi: RAG-06/28/32).
- **Hai mốc cũ 54,3% & 60,0% ghi SAI THƯỚC** (không phải cận trên — số đo bằng thước đã chứng
  minh cho pass giả không có tư cách cận trên). Chuỗi so sánh trục Truy-hồi BẮT ĐẦU tại 35,7%.
- **① 215 chữ vỡ chắc chắn trong kho** (vế trái không nguyên âm) từ trích PDF — trong khi DOCX
  SẠCH cùng nội dung nằm ngay cạnh trong data/raw/ ⟹ **RAG ĐÒN 4: ingest DOCX thay PDF** (coder,
  sau UI-02, trước T3 — chất lượng 7,14/20 ưu tiên hơn tối ưu giá). Đòn 1 giữ cho nguồn chỉ-có-PDF.
- **② 171/362 chunk (47%) không bao giờ lọt top-3** với chính 160 câu kho sinh ra để trả lời —
  tester lấy mẫu 20 chunk phân loại (rác vs nội-dung-bị-chôn) trước khi viết ca 6-trục; kết quả
  quyết đòn-chunk-theo-cấu-trúc có quay lại không.

## 💰 T1 KHÉP BẰNG KẾT QUẢ ÂM — cache ĐÃ hit ~85% từ trước, bản vá revert (16/08 tối)
- Coder đo hai vế chỉ-khác-một-file: bản cũ 85,0% cache-hit, bản "vá" 86,3% — chênh = nhiễu;
  `cache_read` lượt 1 giống nhau TỚI TỪNG TOKEN (29.568). **Cache chưa bao giờ hit 0% — phần tái
  dùng chính nằm GIỮA các bước ReAct trong CÙNG lượt** (mốc thời gian render một lần/lượt = hằng
  số trong lượt; vị trí của nó chưa bao giờ quan trọng). Giả thuyết T1 sai → **REVERT dù vô hại**.
- **LUẬT MỚI (ratify):** bản vá không-có-số-lợi-ích = revert, kể cả vô hại — land nó là gieo tiền
  lệ "chỗ này tối ưu rồi" chặn người sau tìm đòn thật. GIỮ LẠI phần đo (`cached_input_tokens`
  vào envelope, `e2cf59b`) — công cụ đã bác chính người tạo nó.
- **Bức tranh chi phí ĐÍNH CHÍNH:** 63M là token danh nghĩa; ~85% phần lặp hưởng giá cache rẻ ⟹
  hoá đơn thật THẤP hơn ước tính đầu. Nhưng mục tiêu <30k/lượt là về LƯỢNG (input 46,8-84,7k/lượt
  đo được) — cache giảm GIÁ không giảm LƯỢNG ⟹ **T3 là đòn duy nhất chạm mục tiêu**.
- **Thứ tự chốt:** UI-02 đóng trước (compiled, hoãn 5 lần, chỉ còn verify) → T3 (cổng kèm:
  origin-rule xanh — cắt phần đưa-LLM không được làm số mất nguồn) → T4 → T2 độc lập.
- Đòn 3 đính chính: **mốc 20/35 (+1)**, RAG-04 = pass-giả-bị-lộ không phải hồi quy — nhất quán
  chuỗi 9/21; số nằm vùng thước-đang-rà, chưa vào benchmark.

## ⚖️ TRỤC TRUY-HỒI: TẠM TREO SỐ — thước đang được rà HAI PHÍA (16/08 tối)
- Tester (theo dữ kiện tech-lead nêu) soi 21 ca ĐẠT sau đòn-3: **9/21 đạt CHỈ nhờ từ khoá chung
  chung** (RAG-17 có chuỗi đặc trưng `20.000.000` KHÔNG khớp mà vẫn đạt nhờ `hạn mức` — đáp án
  thật không trong top-3, thước vẫn ĐẠT). ⟹ **60% (21/35) là GIỚI HẠN TRÊN, cận dưới 34,3%**;
  và mốc 54,3% hôm trước CÙNG bộ từ-khoá ⟹ cùng caveat. Benchmark ghi `[đang rà thước]`, không
  số nào của thước-chưa-rà đứng như số thật.
- **LUẬT MỚI (ratify vào CHUAN-VIET-TEST):** xác minh nhãn phải soi CẢ HAI PHÍA — ca trượt (oan?)
  VÀ ca đạt (giả?). *"Chỉ soi ca trượt thì thước lỏng tay nhất luôn thắng — chiều im lặng nguy
  hơn vì không ai đi tìm"* — mặt đối xứng Luật 2, do chính tác giả Luật 2 phát hiện mình mắc.
- Luật từ-khoá mới: **≥1 chuỗi ĐẶC TRƯNG bắt buộc** (số/viết-hoa/cụm-dài), từ chung chỉ phụ. Áp
  cả 41 ca + ca mới. Thứ tự: rà 9 ca → đo lại (MỐC THẬT đầu tiên của thước-đã-rà) → ca 6-trục.
- Cặp tester↔coder hai lượt liền bác-nhau-bằng-số và nhận-bằng-số (RAG-04 không-phải-hồi-quy ·
  ca-đạt-cũng-phải-soi) — ví dụ vận hành tốt nhất của kiến trúc đối kháng tới giờ.

## 📊 THƯỚC 35-CA CHẠY LẦN ĐẦU — mốc Truy-hồi MỚI 54,3% + phát hiện TOC (16/08)
- **19/35 = 54,3% CẢ HAI chế độ gõ** (nhãn: 7fdca4e · he_thong 5d63edfc7cc7 · backend 95e17b99 ·
  kho 418·2doc·v2 · cổng-kiem-trong-container). Trục benchmark: **10,86/20 — MỐC MỚI trên thước
  mới, KHÔNG so cặp với 3,75/20 probe-8** (hai bộ khác nhau; chuỗi so sánh bắt đầu từ đây).
- **Xác minh 16 ca trượt: 1 nhãn sai (RAG-08 — từ khoá là TIÊU ĐỀ MỤC, sửa; thước sai vật đúng)
  · 15 truy hồi kém THẬT (không sửa nhãn)** — luật chỉ-sửa-nhãn-chứng-minh-được-sai giữ nghiêm.
- **🔴 PHÁT HIỆN → RAG ĐÒN 3 CHỐT: MỤC LỤC BỊ INDEX** — TOC chứa nguyên văn 160 câu hỏi, embedding
  khớp câu-hỏi-trong-mục-lục thay vì đáp-án-trong-thân; càng giống câu thật càng dễ trúng TOC
  (RAG-21/22 top-3 toàn dòng mục lục). Kho tự cạnh tranh với mình. Đòn 3 = LOẠI DÒNG TOC khỏi
  index (luật 2-điều-kiện: ≥N chấm liền VÀ kết thúc số trang — chống loại nhầm kiểu F-25), giao
  coder; **thước trước/sau = chính bộ 35 ca, mốc 19/35**. Đòn chunk-theo-cấu-trúc HOÃN chờ số.
- **Spec sửa (tester đề, duyệt):** sau đòn 2 hai chế độ gõ HỘI TỤ (19/35 cùng danh sách trượt) —
  "trung bình 2 chế độ" = cộng-số-với-chính-nó, hết thông tin. Đổi: 2 chế độ thành **CỔNG chống
  hồi quy** (phải bằng nhau), trục biến-thiên-đầu-vào chấm bằng **sai-chính-tả·viết-hoa·dấu-câu**.

## 🔴 BĂM KHO RAG KHÔNG TẤT ĐỊNH (tester bắt bằng Luật 4) — nhãn tạm bỏ trường băm
- Đọc `kho_rag.py kiem` 3 lần liên tiếp trên kho KHÔNG đổi → 3 giá trị băm khác nhau ⟹ mọi suy
  luận "băm khác = kho đổi" trong ngày VÔ HIỆU hai chiều (re-index vẫn THẬT — bằng chứng là số
  probe 0/8→5/8, không phải băm). Bắt được vì kiểm-nhạc-cụ-trước-khi-kết-luận-vật-đổi — sau một
  ngày kết-luận-vật-đổi đúng 3/4 lần, phản xạ tin lần 4 rất mạnh; không kiểm là cả đội đi truy
  "lần đổi kho thứ tư" không tồn tại.
- **Quy ước nhãn tạm (ratify):** bỏ trường băm-kho, dùng `418 chunk · 2 doc · chuẩn-hoá v2`.
  Băm quay lại khi tất định (nghiệm thu: 3 lần đọc cùng giá trị, trong container).
- **3 fix giao coder (xen trước UI-02):** ① băm tập-đã-sắp-xếp `(chunk_id,text)` hoặc bỏ băm
  nội dung; ② xoá rác `data/rag_index/` trên host (store rỗng do chính công cụ đẻ, bẫy người
  chạy host); ③ `kho_da_cu()` FAIL-CLOSED — hiện trả False khi KHÔNG dấu, mà không-dấu chính là
  kho-cũ cần bắt: **cổng cấp chứng nhận an toàn cho đúng ca nguy hiểm nhất** ("cổng sai hướng
  tệ hơn không có cổng" — bản tầng-dữ-liệu của F-CI-2).
- Tester song song: `benchmark.py` gọi cổng qua `docker exec` (kho thật sống trong volume, công
  cụ chỉ đúng TRONG container) → xác minh 41 nhãn không chờ fix băm (fix chỉ ảnh hưởng nhãn).

## ▶️ PHIÊN NỐI LẠI 16/08 — ba mốc mới
- **✅ CẶP AUTH ĐÓNG — BUG DEMO CHÍNH THỨC ĐƯỢC CHỨNG MINH ĐÃ VÁ** (tester, dấu khớp hai đầu,
  StartedAt vào nhãn chuẩn): sau 16 phút ngồi yên + token chết thật (−63s đo từ cookie), thao
  tác đầu **200** (trước-vá: 401 + "Có lỗi"), tầng-0 `rotated=1·revoked=0`. Caveat tự khai:
  backend khác giữa hai nửa (2 đòn RAG) — không phải cặp một-biến tuyệt đối, trích số phải kèm
  câu này. Giả thuyết log-bay-do-force-recreate của coder xác nhận đúng. Workaround demo
  (đăng-nhập-lại-trước-handoff) HẾT CẦN.
- **🔴 `kho_rag.py kiem` bắn sai trong container** (đường Chroma không tồn tại cả container lẫn
  host; báo "kho trống · băm-MD5-chuỗi-rỗng" trong khi policy-search trả 4 kết quả thật) — đúng
  món coder tự khai chưa-verify; tester GIỮ CỔNG không đo, bắt nhờ hai-đường-đo-mâu-thuẫn.
  Coder sửa XEN TRƯỚC UI-02 (đang chặn đường găng tester).
- **✅ Security nộp soi-trục golden-set** (`37c5511`, 6 trục): nặng nhất §A âm-bản-GẦN (bộ âm bản
  hiện toàn loại-xa-dễ-pass — về cấu trúc không phát hiện được chế-độ-hỏng nó tồn tại để phát
  hiện: chunk-lân-cận-sai điểm cao → bịa chính sách) + §B ToS trống kể cả **Điều 19 tra-soát-
  khiếu-nại — điều khoản điều chỉnh chính công việc của agent, zero ca**.
  **PO-agent chốt câu §D:** trục Truy-hồi benchmark đo **ĐƯỜNG AGENT THẬT** (sau sanitize) —
  benchmark đo sản-phẩm-khách-nhận; index-thô giữ làm chẩn đoán phụ, hai số hai tên. Ratify luật
  bộ: ca âm-bản-gần phải kèm bằng-chứng-đã-tìm-mà-không-thấy (tester + security độc lập cùng đề).

## ⏸️ ĐIỂM DỪNG PHIÊN 16/08 (hết limit) — phiên sau đọc mục này TRƯỚC
- **Đang chờ chuyển tiếp:** 5 bullet soi-trục golden-set của coder (ca-ranh-giới-k · độ-dài-query
  · đối-chứng-kho-lệch-vế dùng `kho_rag.py kiem` · ca-vắt-ranh-chunk cho đòn 3 · 2-3 ca
  đáp-án-không-tồn-tại) **CHƯA tới tay tester** — nằm trong transcript PO-agent; phiên sau chuyển.
  Security đang soi song song, chưa nộp.
- **Coder:** re-index tự động `0a4ff58` CHƯA VERIFY TRONG CONTAINER (tự khai) · UI-02 vừa bắt đầu
  · kế: 2 việc nhỏ lô auth → ADR-025 phần B → exporter.
- **Tester:** thứ tự 3→1→2 (script benchmark → xác minh nhãn 41 ca → gói 30 nhãn PO) · lượt đo
  sạch cặp auth đang/vừa chạy — kết quả chưa báo.
- **PO thật:** không việc nào chờ họ. PR 7/10 — 3 đợt release dev→main nữa là đủ.
- Doc home-server đã có dòng re-index (f3eba77). Mọi trạng thái khác: các mục phía dưới của
  chính file này — không có tri thức nào chỉ nằm trong đầu phiên nào.

## 🔀 PO THẬT ĐỔI QUY TRÌNH GIT (16/08 tối): MỘT NHÁNH, PR CHỈ THEO ĐỢT
- **Bỏ tách-nhánh-mỗi-việc** — cả 4 phiên code THẲNG trên `dev/learning-loop` (PO chứng kiến chi
  phí: 2 merge nhầm + thứ-tự + retarget trong một chiều). #4 + #7 đã merge sạch, **7/10 PR**.
- **PR còn MỘT loại: `dev` → `main` theo ĐỢT** (release gate) — PO-agent soạn, PO thật merge theo
  link đích danh. Vừa đủ đường tới 10 PR (3 đợt release nữa), vừa làm mỗi lần deploy home-server
  = một bản nghiệm thu trọn. **PO chỉ merge PR có link PO-agent gửi; bỏ qua banner GitHub.**
- Luật git cây-chung (một-lệnh-pathspec · HEAD+nhánh · file-mới-dính-liền · staged-lạ-dừng-hỏi ·
  báo-trước-land-src) NÂNG mức quan trọng — 4 phiên giờ chung một nhánh. Điều kiện chất lượng
  (đo-trước-land, probe-vai-khác cho lớp phòng vệ) KHÔNG đổi. Coder đưa cây chung về dev (có báo).

## 🏆 RAG ĐÒN 2 — SỐ VỀ: HAI CHẾ ĐỘ GÕ BẰNG NHAU (16/08)
- **Không dấu 0/8 → 5/8 · có dấu giữ 5/8 — Recall@3 trung bình 18,75% → 62,5%.** Ba mốc kho:
  `419·b630414088f8` (gốc) → `418·5aab3e7c43a2` (đòn 1) → `418·265aa93031bd` (đòn 2, hiện tại).
  Một-biến-mỗi-lần giữ nghiêm (đòn 1 đo xong hẳn mới áp đòn 2); cùng một thước (tái lập
  0/8·3/8 trên kho gốc). Chế-độ-người-dùng-thật (không dấu) từ 0% lên ngang có dấu — đòn ăn
  đúng như dự đoán.
- **PR: #4 (đòn 1) + #7 (đòn 2, đã retarget → dev). THỨ TỰ MERGE BẮT BUỘC #4 TRƯỚC #7** — đòn-2
  đâm trên đòn-1; merge ngược thì dev nhận cả hai một lượt, #4 rỗng, lịch sử mất khả năng tách
  hai đòn (thứ làm cặp số một-biến đọc được về sau).
- Sự cố merge-nhầm của PO thật (#5 dev→main vô hại · #6 đòn-2→main): KHÔNG cần revert — cả hai
  đòn ĐÃ ĐO trước khi mở PR, main không mang code chưa nghiệm thu. Quy tắc mới cho PO: CHỈ merge
  PR có link PO-agent gửi kèm số; bỏ qua banner gợi ý của GitHub (default-branch=main nên banner
  luôn trỏ main).
- **⚠️ Hệ quả cho gói home-server:** main giờ chứa cả hai đòn RAG ⟹ máy nhà dựng lần đầu PHẢI
  RE-INDEX kho sau deploy — không thì text cũ (còn dấu, còn từ vỡ) nằm cạnh query đã bỏ dấu,
  lệch một vế và KHÔNG CÓ TRIỆU CHỨNG. Coder soạn dòng lệnh chính xác → PO-agent đặt vào Phần C
  doc home-server + trang HTML.

## 📈 RAG ĐÒN 1 — SỐ VỀ, LAND DUYỆT (16/08)
- **Có dấu 3/8 → 5/8 (+2) · không dấu 0/8 KHÔNG ĐỔI (đúng dự đoán — việc của đòn 2) · 0 hồi quy.**
  Vật: kho TRƯỚC `419·b630414088f8` → SAU `418·5aab3e7c43a2` (backup kho cũ giữ nguyên) · thước
  probe-8 nguyên văn, coder KIỂM DỤNG CỤ bằng tái lập 0/8·3/8 trên kho cũ trước khi đo kho mới.
  Nhân quả sạch nhất đợt: ca 5 mới-đạt có top-1 cũ là chính chunk vỡ `"giao d ich… t oi da"`.
  Nhãn: **số-probe, không vào chuỗi benchmark** — trục RAG chấm lại khi golden-set land.
  PR đòn 1 sắp mở (`fix/rag-don1-extraction-pdf` @ 585ca06) — PO thật merge theo quy ước.
  Đòn 2 (chuẩn hoá dấu) GO ngay sau. Tester gán nhãn golden-set trên KHO MỚI; khuyến nghị nhãn
  theo định-danh-bền (mã câu FAQ/số Điều) thay vì chunk-id — sống qua re-index.
- Coder nhận nửa sự cố cây-chung không giảm nhẹ + tự gọi tên meta-pattern: *"biết một cái bẫy
  không miễn nhiễm với nó"* (lần 2 trong phiên: TTL-số-nói-về-hệ, rồi switch-cây-chung sau hai
  lần chính mình cảnh báo). Ghi thành luật đọc-người: **người cảnh báo giỏi nhất về một bẫy
  thường là người sắp dính nó — vì họ làm việc gần bẫy nhất.** Worktree áp ngay từ lô này.

## ⚖️ SỰ CỐ GIT TRÊN CÂY DÙNG CHUNG (16/08) + HAI LUẬT MỚI + QUY ƯỚC PR
- **Sự cố (lỗi ĐÔI, đã khắc phục, KHÔNG mất gì):** tester `git add` 9 file (đúng pathspec) →
  PO-agent `git commit` KHÔNG pathspec cuốn cả 9 file staged vào commit `7548bcb` → tester
  `reset HEAD~1` không đọc lại HEAD, đè local (remote an toàn, đã khôi phục khớp remote).
  **Hồ sơ:** commit `7548bcb` ("docs(state): PO chốt benchmark…") ngoài nội dung message còn mang
  **2.584 dòng thuộc `tests/`+`eval/` của tester** (cuốn vào do sự cố index, không chủ đích).
  Nội dung (5 bullet của tester, ghi lại để người đọc lịch sử khỏi mò diff):
  ① **`eval/EVAL-EVIDENCE.md`** — DELIVERABLE nộp BTC: 7 ca manual output NGUYÊN VĂN từ stack
  thật (nhãn `c447abb`), gồm 2 ca ÂM BẢN; cặp CA1↔CA6 = cùng câu hỏi, khác trạng thái xác thực,
  hai kết quả ngược (bằng chứng cổng OTP thật); có mục "những gì bộ này KHÔNG chứng minh".
  ② **`tests/test_ai_log/`** — cổng nhánh leftover `submit_log.py` (sắp chạy 19 lượt backlog
  P-121); F-LOG/F-LOG-2 vá cùng phiên nên 2 ca xfail-strict tự XPASS → lật thành regression gate.
  ③ **`tests/test_security/test_corpus_en_du_truc.py`** — cổng ký mẫu tier-1 EN: 50 ca/8 trục/
  BA mức kỳ vọng (mức giữa "tier-2 chấp nhận được" là thứ bộ hai-mức báo đỏ nhầm cho hành vi
  đúng) + mức `theo_doi` in-số-không-chấm có rào 4 vế.
  ④ **`test_note_toan_ven_can_cu_tu_choi.py`** — trục "căn cứ từ chối còn đọc được": 8/20 trùng
  8/8 ID với security qua phương pháp khác + cổng cấm-chạy-lẻ. Kèm `test_dua_refresh_token.py`
  — giả thuyết đua bác bằng đo, file ở lại canh tính-chất-đang-đúng, docstring giữ lịch sử.
  ⑤ **`tests/CHUAN-VIET-TEST.md` lên 8 LUẬT** — Luật 6 (skip tự chứng minh) · Luật 7 (canh chính
  công-cụ-đo) · Luật 8 (phát hiện công cụ sai = một ĐƯỜNG ĐO KHÁC, không phải sự cẩn thận — 6 ca
  thật/một buổi/hai vai) + `TIEU-CHI-CI.md` (F-CI, F-CI-2, CI-10/11) + 2 bộ tier-1 cũ bỏ tầng
  dò-đoán-tên (chúng SKIP TỪ NGÀY VIẾT vì đoán `phan_tier` ≠ tên thật `_phan_loai_tier`). Nhánh rác `test/bo-do-va-bang-chung-16-08` đã xoá; KHÔNG tạo PR ngược
  (PR rỗng cho đẹp số là thứ không làm khi BTC đếm PR).
- **HAI LUẬT GIT MỚI (ratify, áp cả 4 phiên):** ① `git commit <pathspec> -m …` MỘT LỆNH — cấm
  add-rồi-commit-rời, index dùng chung không được có trạng thái chờ; ② sau MỌI lệnh đổi HEAD,
  ĐỌC LẠI HEAD trước lệnh kế (in ra chưa đủ — phải đọc).
  **Addendum ①b (coder bắt):** một-lệnh KHÔNG phủ FILE CHƯA TRACK — ca đó `git add <file> &&
  git commit <cùng file>` DÍNH LIỀN; thấy staged-LẠ trong status thì DỪNG HỎI, không commit đè.
  **Addendum ②b (PO-agent tự dính ngay sau khi ratify ②):** đọc HEAD phải đọc CẢ TÊN NHÁNH —
  3 commit docs của PO-agent (923e42a·ed0d237·3493dbd) đi lạc lên nhánh coder vì cây chung bị
  chuyển nhánh giữa chừng mà PO-agent chỉ đọc hash, không đọc nhánh. Đã cứu về dev bằng
  push-ref + worktree, không mất gì.
  **Addendum ③ (quy ước cây chung):** CHUYỂN NHÁNH cây dùng chung = ĐỔI VẬT của cả 4 phiên —
  phải BÁO TRƯỚC như rebuild image; làm việc nhánh riêng ưu tiên `git worktree` thay vì checkout
  tại chỗ.
- **QUY ƯỚC PR (PO thật chốt trực tiếp với tester):** các vai tách nhánh + tạo PR, **KHÔNG tự
  merge — PO thật là người merge**. PO-agent gom danh sách PR chờ-merge cho PO duyệt theo đợt;
  chờ-merge không được chặn việc kế (nhánh sau đâm trên nhánh trước nếu phụ thuộc).
- **RAG đòn 1 — KHE MỞ, đang chạy:** tester xác nhận không giữ phép đo trên demo. Trình tự chốt:
  re-index trước (backup Chroma+policy_chunks, báo nhãn kho mới số-chunk+băm) → tester soạn
  golden-set trên kho MỚI (nhãn đoạn gắn kho — soạn trước là công đôi + vật-trôi). Ràng buộc cặp
  trước/sau: **GIỮ NGUYÊN VĂN 8 câu probe** (cùng bộ câu, khác kho — một biến). Golden-set ETA:
  ~3h sau nhãn kho mới cho bản DỰ THẢO; thành THƯỚC sau vòng soi-trục-thiếu của security+coder.
  Thiết kế hay của tester ghi lại: bộ có **ca đối chứng ÂM TÍNH** (câu không có đáp án trong kho
  ⟹ Recall phải =0 — chống thước-tự-thưởng).

## 🎯 QUYẾT ĐỊNH PO THẬT 16/08 — BENCHMARK + LEARNING LOOP v1 (mới nhất)
1. **Chiến lược đánh giá chất lượng: CHỐT** theo `2026-08-16-chien-luoc-danh-gia-chat-luong.md`
   (kim tự tháp 3 tầng · lấy taxonomy OpenAI graders không lấy hosted · heldout 60 niêm phong).
2. **Benchmark spec v1 + v0: CHỐT** (`2026-08-16-benchmark-spec-va-v0.md`, PR #3) — trọng số
   30/25/20/15/10; **v0 = 68,75/85 điểm đo được (80,9%)**, điểm nghẽn định lượng: Truy hồi RAG
   3,75/20 (Recall@3 probe: 0/8 không dấu · 3/8 có dấu — đáp án CÓ trong kho ⟹ lỗi tầng truy hồi).
   Đang chạy: tester golden-set truy hồi 30-50 câu + script benchmark + gói 30 ca nhãn PO (hiệu
   chuẩn judge ≥85%) · coder RAG đòn 1 (extraction sạch — chunk dính "Giao D ịch") + đòn 2 (chuẩn
   hoá dấu tầng query), mỗi đòn một PR có đo trước/sau; đòn 3-4 chờ số.
3. **LEARNING LOOP v1: GO** ("sau benchmark chạy luôn phần LLM tự cải thiện") — bánh đà dữ liệu
   CÓ NGƯỜI GÁC, không phải model tự train: ① tín hiệu học ĐÃ thu (reject_reason +
   la_tin_hieu_hoc, ADR-019; maker-checker chống bơm nhãn giả, ADR-020) · ② thước = benchmark
   vừa chốt · ③ mảnh thiếu = **exporter Phase 2** (`eval/candidates/`, test_14 cắm cọc chờ sẵn).
   **TRÌNH TỰ AN TOÀN BẮT BUỘC: ADR-025 phần B land TRƯỚC exporter** — S-02 (`agent_note` chưa
   cọc/chưa scrub) là nguồn tự nhiên nhất của phễu học; mở exporter trước khi đóng cọc = dữ liệu
   bẩn chảy vào bộ học. Sau exporter: quy trình đề-cử→duyệt 10 phút/tuần (PO hoặc uỷ PO-agent sơ
   duyệt) → golden-set tự lớn từ vận hành thật → benchmark v2 chứng minh "học được" bằng số.

## ⚡⚡ QUYẾT ĐỊNH PO THẬT MỚI NHẤT — tối muộn 15/08 (đè mọi mục cũ)
1. **ADR-025 ĐÃ KÝ TOÀN BỘ** — PO thật xác nhận cả 4 con số sau khi đọc giải thích: retention
   5 năm (giữ cờ tư-vấn-pháp-lý) · trần 2.000 ký tự · quyền đọc 2 pha · preview-confirm 2 vòng
   khoá. ⟹ **MỞ KHOÁ cho coder**: Pha-1 audit-log đọc nhóm A · B1/B2 preview-confirm cho `note`
   (2 vòng khoá) · B3 `agent_note` (SAU B1/B2) · nếu cần route/contract mới → quy trình §3.
   Tester: cổng 8/20 sẽ xanh khi B1/B2 land → gỡ marker thành regression-gate.
2. **F-MIG: DUYỆT làm luôn LÔ KẾ TIẾP** của coder (cùng lô với phần B ADR-025 hoặc trước, coder
   xếp) — 4 phép kiểm nghiệm thu trong hồ sơ, quan trọng nhất: so schema hai đường phải TRÙNG.
3. **VIỆC MỚI UI-01**: 2 chỗ JSON thô trong timeline điều tra của ticket (input + kết quả) →
   hiển thị tiếng Việt trực quan cho CSKH + supervisor. Đặc tả đầy đủ:
   `docs/giao-viec/2026-08-15-ui-timeline-dieu-tra-khong-json.md`. Ràng buộc cứng 3 giữ nguyên:
   lớp ĐỊNH DẠNG không phải lớp DIỄN GIẢI, map nhãn tĩnh, giá trị đã che hiển thị nguyên trạng,
   JSON gốc giữ trong expander cho audit.

## ⚡ BA QUYẾT ĐỊNH PO THẬT — chiều tối 15/08 (mới nhất, đè các mục cũ bên dưới)
1. **Billing/CI: PO thật CHỐT ĐỂ LẠI SAU (tối 15/08)** — không giải quyết hôm nay; PO không phải
   owner org, chỉ BTC sửa được, và việc liên hệ BTC dời sang ngày khác. **KHÔNG chặn gì**: tester
   đã chạy đủ lệnh từng job trên host (540 passed sau lô mới), F-CI-2 đã vá sẵn đón ngày billing
   thông. Tin nhắn gửi BTC đã soạn sẵn trong lịch sử trao đổi — khi PO sẵn sàng thì lấy dùng.
   Việc DUY NHẤT sẽ đọng lại nếu quên: bằng chứng CI trên runner + badge cho Demo Day
   (deliverable) — nhắc lại khi gần mốc nộp.
2. **ADR-025: NGUYÊN TẮC ĐÃ DUYỆT** ("chốt theo hướng security"). PO thật uỷ quyền PO-agent research
   chuẩn EU/US cho 3 chỗ trống → **dự thảo ADR-025 ĐÃ VIẾT** vào `docs/DECISIONS.md` với đề xuất:
   retention **5 năm** (max của VN-PCRT-5n/EU-AMLD-5n/US-RegE-2n-sàn, cờ: cần tư vấn pháp lý thật
   trước production) · đọc transcript theo **NGƯỜI PHỤ TRÁCH** + supervisor có audit-log (GDPR 25/32
   · PCI DSS Req 7 · ISO 27001 · SOC 2) · fail-visible = **preview-confirm** (nhân viên thấy bản đã
   che, xác nhận trước khi ghi; engine lỗi vẫn fail-closed 500 giữ ADR-024). Con số chờ PO xác nhận
   nhanh rồi coder mới chạm contract/code phần B + A3/A4.
3. **PILOT 150 NGƯỜI: HOÃN** — PO thật chốt: chỉ mở khi (a) tối ưu **caching** xong và (b) chatbot
   **tự học/tự nâng cấp** được (learning loop Phase 2). ⟹ các mục "trước pilot" (F-29, A1/A2, RAG,
   TPM) **giãn deadline nhưng KHÔNG huỷ** — F-29/A1/A2 rẻ nên vẫn làm ngay trong lô hiện tại. Hai
   cam kết của security (dữ liệu thật + đường xoá) ghi lại cho thời điểm pilot thật.

## Chặn / chờ PO THẬT — RÚT GỌN 15/08 (chip câu 3 + ADR-020 ĐÃ CHỐT, xem "Vừa xong")
- **Hướng đợt 150 người.** Số end-to-end đã có: bộ lọc 17/17 không siết nhầm, RAG retrieval là
  điểm yếu; 4 góc chưa-sẵn-sàng: TPM · 429→500 · timeout · RAG (sổ Đợt 2, mục "429 SẢN PHẨM" +
  "TIMEOUT trên câu phổ biến nhất").
  **➕ Ý KIẾN BẢO MẬT VỀ PILOT (security, kết sổ `80b217a`) — đọc trước khi quyết:**
  > Bốn cửa **KHÔNG chặn pilot về mặt bảo mật**. Thứ **thật sự cần trước pilot** là **A1 + A2** —
  > rẻ, không cần quyết cơ chế, đóng đúng phần *"lưu plaintext vĩnh viễn"*. Phần còn lại
  > (B1/B2, A3, A4) là **nợ đúng hạn, không phải nợ gấp**.

  🔴 **SECURITY KHÔNG CẤP PHÉP CHO PILOT — họ nói bốn cửa KHÔNG PHẢI THỨ CHẶN nó.** Hai chuyện
  khác nhau, và security nhắc lại lần hai để nó không mòn đi qua vài tay. Kèm **hai ràng buộc mà
  PO PHẢI CAM KẾT**, không phải bảo mật cấp:
  1. **Dữ liệu pilot được coi là DỮ LIỆU THẬT** — chịu NĐ 13/2023 như dữ liệu khách thật, **không
     phải** *"dữ liệu demo nên thoải mái"*.
  2. **Có ĐƯỜNG XOÁ sau đợt** — **có người chịu trách nhiệm, có mốc thời gian**, không phải *"tính sau"*.

  **Thiếu một trong hai thì ý kiến của security ĐỔI.**

  ⚠️ **Phạm vi:** bốn cửa không chặn pilot **VỀ MẶT BẢO MẬT**. Bốn góc chưa-sẵn-sàng còn lại
  (**TPM · 429→500 · timeout · RAG retrieval**) **KHÔNG thuộc phạm vi security đánh giá** và
  **không được cộng gộp** vào câu trên.
  ⚠️ Và **bốn cửa không phải một khối** — chúng có **hạng khác nhau**; trộn lại sẽ khiến **A1/A2
  (rẻ, đáng làm ngay) bị kẹt sau A3/A4** (đụng vận hành CSKH, cần PO).
- **PO-1 xong** (key đã xoay). **PO-2**: keys đang tạo lại — AI_LOG_API_KEY + LANGCHAIN keys (key cũ
  401), OPENAI_API_KEY secret PO đang đặt (đã có hướng dẫn). 9118 dòng backlog AI-log ở
  P-121-new/.ai-log chờ submit khi có key mới — ĐỪNG xoá P-121-new tới khi submit xong.

## 🔴 HAI FINDING MỚI 15/08 (chiều) — cần PO thật, ghi đầu vì cả hai chặn kết luận đang có

### F-CI — CI ở P-226 CHƯA TỪNG CHẠY MỘT JOB NÀO (tester `p-226-c8` đo bằng `gh run list`)
13/13 lượt chạy trên `dev/learning-loop` đều `failure` sau **4-5 giây**, annotation nguyên văn:
> *"The job was not started because recent account payments have failed or your spending limit
> needs to be increased. Please check the 'Billing & plans' section"*

**Không phải test đỏ, không phải config sai — ZERO job khởi động.** Hai lượt `success` duy nhất
trong lịch sử repo là "Initial commit" 26/07 (22s/27s, trước khi có bộ test thật).

**Tester đã chạy TRƯỚC đúng lệnh của từng job trên host** (Python 3.14 vs CI 3.12 — ghi rõ để
không đọc thành chắc chắn), HEAD `2e8c888`, để khi runner sống lại thì tách sẵn "đỏ vì billing"
khỏi "đỏ vì code":

| Job | Lệnh CI | Host |
|---|---|---|
| `invariants` | `pytest tests/test_invariants.py` | 23 passed ✅ |
| contract drift | `check_contracts.py` | 3/3 khớp ✅ |
| `lint-and-test` | `pytest tests/ -m "not security_finding"` | **446 passed · 41 skipped · 0 failed** ✅ |
| `security-findings-gate` | `pytest tests/ -m security_finding` | 1 failed — ĐỎ ĐÚNG CHỦ ĐÍCH |
| `appsec` | `pytest tests/test_api/` | **1 failed** · 227 passed 🔴 |

**🔴 F-CI-2 — job `appsec` sẽ đỏ vì LÝ DO SAI ngay khi billing thông.** `appsec` chạy
`pytest tests/test_api/ -v` **thiếu `-m "not security_finding"`** mà `lint-and-test` có ⟹ nó bắt
luôn `test_live_chat_pii_gap.py::…_is_not_masked_before_storage` = **ST2-P0-3**, finding P0 duy
nhất còn lại (3 P0 kia đã vá đợt Auth5). `security-findings-gate` đỏ là ĐÚNG THIẾT KẾ; `appsec`
đỏ là SAI. Vi phạm chiều hai của `tests/TIEU-CHI-CI.md`: *"cổng đỏ vì lý do sai còn tệ hơn không
có cổng — nó dạy cả đội bỏ qua chính cảnh báo đó"*. **Nguy hơn thường lệ vì nó nổ ĐÚNG LÚC billing
vừa thông**, lúc cả đội đang mong thấy xanh và dễ tặc lưỡi nhất. Vá = **một dòng `ci.yml`** (vùng
coder). Tester đã ghi tiêu chí **CI-10** + 2 phép thử vào `tests/TIEU-CHI-CI.md`.

**🟡 F-CI-3 — hai test tier-split TỰ SKIP BẰNG ĐOÁN TÊN HÀM.** Trong 41 skip, 38 có lý do chính
đáng. Còn `test_mau_tier1_chi_thi.py` + `test_f24_recall_tier1.py` skip với *"F-22 CHƯA SHIP"* —
chúng thử 4 cặp module/tên cho `phan_tier`, không thấy thì skip. Nhưng sổ Đợt 2 ghi F-22/F-24/F-25
đã chốt và ship. Tester **không phân biệt được vì không đọc `src/`** (§4): hoặc chưa ship thật
(skip trung thực), hoặc **đã ship DƯỚI TÊN KHÁC** ⟹ hai bộ skip vĩnh viễn trong khi cả đội tưởng
đang được canh. **Khả năng thứ hai ĐÃ XẢY RA một lần cùng đợt này**: `8d26548` — *"O2 mỏ neo tìm
đúng tên `dem_mat_do_liet_ke`, 7 ca hết SKIP"*. **Coder chỉ cần trả lời một dòng: tên hàm thật.**
⟹ **Toàn bộ Đợt 2 ở P-226 chạy với 0 lượt CI có hiệu lực.** Mọi câu "CI xanh chưa" vô nghĩa tới
khi thông. **VIỆC PO THẬT (không phiên Claude nào làm được): Billing & plans của org
`AI20K-Build-Phase-Cohort-3`.** Hệ quả: CI-1/CI-4/CI-5 (`tests/TIEU-CHI-CI.md`) không nghiệm thu
được; CI-1 đã nối dây đúng cho `dev/**` nhưng **chưa bao giờ chứng minh được có hiệu lực**.
Đây là "hiện diện ≠ hiệu lực" ở tầng HẠ TẦNG: `ci.yml` đủ 13 job, trigger đúng, mọi push đều
sinh một lượt chạy — và **không byte code nào từng được kiểm**.

### F-NOTE — `note` scrub CHẶN NHẦM 40%, xoá đúng CĂN CỨ TỪ CHỐI (security `p-226-0f` đo, 0 TPM)
Che PII **ĐẠT** (12/12 ca có PII đều bị che; bộ đối kháng 15 passed/1 skipped). **NHƯNG 8/20 ghi
chú CSKH KHÔNG có một mẩu PII nào vẫn bị đục**, NER gán nhầm cụm nghiệp vụ tiếng Việt:
- *"…từ chối theo chính sách."* → *"…từ chối **[PERSON]**"*
- *"Khách đã rút khiếu nại qua tổng đài, không cần xử lý tiếp."* → *"**[LOCATION]** … không **[PERSON]**"*

**KHÔNG phải "đánh đổi đã chốt".** ADR-024 chấp nhận che-nhầm với tiền đề ĐO ĐƯỢC là *mã 12 số
trùng pattern CCCD* (`test_03`). Lớp vừa đo là **cụm nghiệp vụ thuần bị NER gán [PERSON]** —
tiền đề đó **CHƯA TỪNG ĐO** ⟹ đúng **Luật 8** (đo lại GIAO của các quyết định), họ hàng F-25
(xoá trắng chính sách thật), lần này rơi vào **BẢN GHI KIỂM TOÁN**: supervisor đọc `note` để hiểu
vì sao từ chối, mà bản ghi hỏng nghĩa **TRONG IM LẶNG**.
Gốc: `scrub_pii` docstring tự khai dùng cho **log/span attribute** — mất một chữ trong log thì
không sao; ADR-024 tái dùng nó cho **record có giá trị pháp lý** = đổi hạng mục sử dụng.
⟹ **CHƯA BẬT CI security-gate cho `note`** (bật = đóng dấu xanh lên hành vi làm hỏng audit trail).
Bản vá đụng tiền đề ADR-024 → phải qua PO thật, coder ĐỪNG vá vội.
**Hồ sơ đầy đủ (23KB, §0-§8): `docs/security/2026-08-15-ra-soat-cuoi-sprint-note-scrub-va-pipeline.md`** (`c2c2d06`).
**Đính chính mục "Vừa xong" bên trên:** `note` đủ về **BẢO MẬT**, KHÔNG đủ về **TOÀN VẸN BẢN GHI**.

### 🔴 S-02 (CAO) — tiền đề "chỗ DUY NHẤT" của ADR-024 BỊ BÁC: `InvestigationLog.agent_note`
Route `POST /tickets/{id}/request-more-info` ghi thẳng `req.note` → `agent_note`: **không scrub,
không trần độ dài, không cờ tier**. Probe HÀNH VI (gọi route thật + đọc thẳng DB, không grep tên):
PAN 16 số `9704123456789012` · CCCD · SĐT · tên đều nằm **plaintext trong DB**; note **5.000 ký
tự** nhận trọn (bên `reject` chặn ở 500); payload injection lưu nguyên văn.
Không rò ra khách (3 đường đọc đều gated `cskh,supervisor`; node agent ghi `agent_note=None` nên
không vào LLM). Nhưng hở **NĐ 13/2023** — và `EncryptedText` ĐÃ được áp cho chat content
(`models.py:475`) lẫn RAG (`:513`), nên `agent_note` **chỉ đơn giản bị BỎ SÓT, không phải một
quyết định**. Cộng hở **phễu học Phase 2**: `test_14` cắm cọc cấm `note` ra file ứng viên, **không
có cọc nào cho `agent_note`** — trong khi `investigation_logs` mới là thứ tự nhiên nhất để xuất
làm dữ liệu học.
⚠️ **S-01 và S-02 PHẢI SỬA CÙNG MỘT QUYẾT ĐỊNH** — bê nguyên `scrub_pii` sang cửa thứ hai là
**nhân bản lỗi chặn-nhầm 40% sang trường thứ hai**.

### 🔴🔴 PHẠM VI THẬT LÀ **BỐN CỬA**, KHÔNG PHẢI HAI — đây là quyết định lớn nhất đang chờ PO
Security rà tiếp (`eff47ac`) và mở rộng §8.3 từ 2 lên **4** cửa văn bản tự do:

**CẢ BỐN Ô NAY ĐO BẰNG HÀNH VI TRONG PHIÊN** (`b7e4230` + `eb444eb`) — hai ô phải bổ sung sau:
`description_raw` (security tự thấy không ổn khi nó sắp thành căn cứ quyết ADR-025) và
`messages.content` (PO-agent xin đo, lý do: nhóm A là nơi security khuyến nghị **BÁC** một cơ chế,
mà **bác = để nguyên hiện trạng hở** ⟹ cần số chắc hơn khuyến nghị áp; nếu hiện trạng đã trôi thì
đang bác dựa trên trạng thái không còn đúng). **Kết quả: hiện trạng KHÔNG trôi ⟹ khuyến nghị §2
đứng nguyên** (không scrub · 4/4 PII còn nguyên sau giải mã · 20.000 ký tự · không cờ · injection
nguyên văn). Bảng nay có **4 chiều**:

| Cửa | Ai gõ | Scrub | Trần độ dài | Cờ tier | Mã hoá at-rest |
|---|---|---|---|---|---|
| `messages.content` (live-chat) | khách + CSKH | ❌ | ❌ | ❌ | ✅ `EncryptedText` |
| `complaints.description_raw` | khách | ❌ | ❌ **20.000 ký tự nhận trọn** | ❌ | ❌ **`Text` thuần** |
| `resolutions.note` | nhân viên | ✅ **nhưng hỏng nghĩa 40%** (S-01) | ✅ 500 | ✅ | ❌ |
| `investigation_logs.agent_note` | nhân viên | ❌ | ❌ | ❌ | ❌ (S-02) |

**Hai điểm mới, quyết định cách xếp thứ tự trong ADR-025:**
1. `description_raw` chứa **PII BÊN THỨ BA ngay ở ca dùng điển hình nhất** — *"em chuyển nhầm cho
   anh X, sđt…"*. Người đó **không phải khách hàng**, không có cơ sở pháp lý để lưu. Đo: 5/5 mẩu
   PII còn nguyên văn (2 SĐT · STK · CCCD · **tên bên thứ ba**), injection lưu nguyên văn.
2. Nó là **cửa khách-tự-gõ DUY NHẤT không có mã hoá at-rest** (live-chat có `EncryptedText`, cửa
   này không).
⟹ Nếu PO định làm ADR-025 theo kiểu *"cửa nào gấp làm trước"* thì **`description_raw` KHÔNG phải
cửa nhẹ nhất như tên gọi gợi ý.**

### ✅ ĐIỂM SÁNG — `EncryptedText` KHÔNG chỉ được khai, nó CHẠY THẬT (kiểm bằng BYTE)
Security đọc **byte thô trong DB bằng SQL, vòng qua type decorator**:
```
'gAAAAABqgCRz6DpP1R2B9-N2Sg_Onanat4Bvpi7cdkfHq_vg6UnKiYmU0J9T40Z5quppnkJ8d…'
PII lộ plaintext? -> False        ⟹ mã hoá at-rest CÓ HIỆU LỰC
```
Đây là control **DUY NHẤT trong bốn cửa** được xác nhận bằng **HÀNH VI** thay vì bằng một dòng khai
báo kiểu — ba cửa kia mới chỉ đọc được dòng khai `Text`/`EncryptedText`, **chưa kiểm byte**.
📌 **Nhắc quan trọng: "hiện diện ≠ hiệu lực" áp cho cả thứ ĐANG CHẠY ĐÚNG, không riêng thứ hỏng.**
Ta quen dùng luật đó để bắt lỗi; đây là lần nó dùng để **xác nhận một thứ tốt là tốt thật**.

**Hai hệ quả cho ADR-025:**
1. **CỦNG CỐ lập luận BÁC che-lúc-ghi ở nhóm A.** Ở `messages.content` lớp bảo vệ at-rest **đã hoạt
   động** ⟹ đổi thêm **giá trị chứng cứ** để lấy một mức giảm thiểu nữa là **đánh đổi tồi**. Câu
   *"tại sao không che cho xong cho an toàn"* nay có thêm một vế trả lời: **vì lớp phòng vệ không
   phá gì đã chạy rồi.**
2. **NÂNG giá trị A1.** Mã hoá `description_raw` không phải "thêm một chuẩn mới trên giấy" — là kéo
   cửa yếu lên một chuẩn **đã chứng minh chạy được ở cửa bên cạnh**.

⚠️ **Mã hoá at-rest KHÔNG chạm tới lỗ đọc-theo-vai.** `messages.content` vẫn hở ST2-P0-3 §3: mọi
`cskh`/`supervisor` đọc được **mọi** transcript, không giới hạn theo ca phụ trách. At-rest chống
**mất đĩa/backup**, không chống **người đọc hợp lệ**. Đó là việc **A3** — cần PO quyết vì đụng vận
hành CSKH. Đừng đọc "mã hoá đã chạy" thành "cửa này đã an toàn".

### 🧭 MỘT NGUYÊN TẮC, **HAI CƠ CHẾ** — đọc TRƯỚC khi soạn ADR-025 (security `6f18c9d`)
Phương án + lý do bác cho từng cửa đã viết sẵn:
`docs/security/2026-08-15-co-che-cho-bon-cua-dau-vao-adr-025.md`.

**Nguy cơ lớn nhất của việc gộp bốn cửa vào một ADR là nó kết thành "áp scrub-lúc-ghi cho cả
bốn"** — và số đo nói điều đó **hỏng nặng nhất ở đúng hai cửa quan trọng nhất**. Đây là lý do
security viết phần cơ chế TRƯỚC bản dự thảo, không phải sau.

⚠️ **Đường phân chia KHÔNG phải "nhân viên gõ / khách gõ"** như bảng bốn cửa ở trên gợi ý —
security tự cảnh báo chính bảng của họ dễ dẫn người đọc đi sai. **Trục thật: bản ghi đó có phải
BẰNG CHỨNG không, và người gõ có SỬA LẠI ĐƯỢC không.**

**NHÓM A — `description_raw` + `messages.content` = LỜI KHAI CỦA KHÁCH.** Là căn cứ giải quyết
tranh chấp tiền bạc, và khách **không sửa lại được** (họ đã rời đi).
⟹ **BÁC che-lúc-ghi.** Ba cửa kia hỏng thì mất khả năng ĐỌC; cửa này hỏng thì **mất GIÁ TRỊ CHỨNG
CỨ** — một lời khai bị hệ thống sửa chữ **không đứng được** nếu khiếu nại đi xa hơn (NHNN, hoặc
toà). Cơ chế đúng: **mã hoá at-rest + trần + siết đọc theo NGƯỜI PHỤ TRÁCH (không theo vai) +
retention + che lúc XUẤT**. Chỗ xuất/log mới đúng hạng mục `scrub_pii` được viết ra — **vì bản gốc
vẫn còn**.

**NHÓM B — `note` + `agent_note` = ghi chú thao tác.** Nhân viên **đang ngồi trước màn hình**, sửa
lại được. ⟹ che-lúc-ghi **được**, nhưng phải **FAIL-VISIBLE** (xác nhận vòng tròn), **không im lặng**.

**Cắt lô:**
- **LÀM NGAY, KHÔNG cần PO quyết cơ chế** → nhập vào nhóm việc rẻ: **A1** mã hoá at-rest
  `description_raw` (chỉ là **bù cho ngang chuẩn dự án đã có** — live-chat có `EncryptedText`,
  cửa này không) · **A2** trần độ dài.
- **CẦN PO quyết**: **B1-vs-B2** (chế độ fail-visible) · **A3/A4** (siết đọc + retention — đụng
  vận hành CSKH, không thuần kỹ thuật).
- **SAU CÙNG**: **B3** (áp ba lớp cho `agent_note`) — **phải đi SAU B1/B2**; bê nguyên `scrub_pii`
  sang khi chưa sửa chế độ im lặng = **nhân bản lỗi 40% sang cửa thứ hai**.

**BA điều security ghi rõ là KHÔNG kết luận — giữ nguyên khi soạn ADR-025:**
1. **Không đề xuất con số retention** — đó là câu hỏi **pháp lý** (NĐ 13/2023 + thời hiệu khiếu nại
   TT 40/2024), có thể cần **tư vấn pháp lý thật**, không phải suy luận của security.
2. **Không kết luận nhóm A có cần scrub ở dạng nào** — nếu PO vẫn muốn thì phải đo trên corpus
   **LỜI KHAI THẬT**, ngưỡng **0 câu bị đổi nghĩa**.
3. **`messages.content` là cửa DUY NHẤT chưa probe hành vi trong phiên** (số dẫn từ ST2-P0-3 14/08
   + đọc `models.py`). Nếu ADR-025 quyết dựa trên nó → **nói một tiếng, security đo như đã đo ba
   cửa kia**.

§7 hồ sơ cũ đã cảnh báo *"chốt riêng lẻ sẽ tạo tình trạng che ô chat để hở ô mô tả, người soi bảo
mật tìm ra trong năm phút"* — nay quy mô **gấp đôi**, và một trong bốn cửa đã "được che" theo cách
**làm hỏng bản ghi**. ⟹ **S-01 + S-02 + ST2-P0-3 + `description_raw` là MỘT quyết định, không phải
bốn.** ADR-025 nên phủ **cả bốn cửa**, không riêng `note`.

### ⚠️ SECURITY TỰ BÁC ĐƠN THUỐC CŨ CỦA CHÍNH HỌ — đọc trước khi trả lời §8.2
Hồ sơ ST2-P0-3 §5.2 kê **"dùng `scrub_pii`, giữ 4 số cuối"** — đúng cái hàm hôm nay đo được chặn
nhầm 40%. Tin nhắn live-chat **chính là** văn bản tự do tiếng Việt, cùng loại đầu vào đã đo. Áp
nguyên văn sẽ mang lỗi vào **lời khách gõ cho CSKH**, và ở đó **hậu quả NẶNG HƠN `note`**: che tại
điểm GHI ⟹ **không còn bản gốc**, CSKH đọc một khiếu nại đã bị sửa nghĩa mà không có cách nào biết
chữ nào đã mất (`"không cần xử lý tiếp"` → `"không [PERSON]"` đủ để xử lý sai ca).
- **KHÔNG đổi:** khuyến nghị vẫn là **B**, vẫn phản đối **C**, lỗ hổng §3 vẫn thật.
- **ĐỔI:** câu hỏi §8.2 (*"giữ 4 số cuối hay che trọn"*) **không còn đủ** — phải hỏi TRƯỚC nó
  **"che bằng CƠ CHẾ nào"**. Trả lời §8.2 trên bản cũ = chọn giữa hai biến thể của một cơ chế đã hỏng.
Đính chính đã vào hồ sơ tại `eff47ac` (cảnh báo đầu file + gạch bỏ §5.2 tại chỗ, giữ nguyên văn cũ
để thấy được cái gì đã đổi).

### ST2-P0-3 — **GIỮ NGUYÊN mở/đỏ, KHÔNG đổi trạng thái** (security đo lại rồi mới trả lời)
Không phải finding lỗi thời mà là **quyết định sản phẩm chờ PO thật**, cố ý giữ đỏ để câu hỏi khỏi
bị đóng im lặng. Lỗ §3 còn hở nguyên: `messages.content` lưu nguyên văn, không retention, mọi
`cskh`/`supervisor` đọc được bất kể có phụ trách ca hay không.
⟹ **F-CI-2 sửa ở JOB CI, KHÔNG sửa bằng cách đóng finding** — đóng một finding đang mở để CI xanh
thì CI xanh mà lỗ vẫn hở. Security xác nhận defect: `ci.yml:251` = `pytest tests/test_api/ -v`,
thiếu `-m "not security_finding"`, còn `test_live_chat_pii_gap.py:25` có `@pytest.mark.security_finding`.
Họ cũng **BÁC nghi ngờ thứ hai của chính mình**: job `appsec` KHÔNG thiếu env (`JWT_SECRET_KEY` /
`FIELD_ENCRYPTION_KEY` ở khối `env:` mức workflow `ci.yml:23-31`, mọi job thừa hưởng) ⟹ **MỘT
defect ở job này, không phải hai**.

### 🔴 S-03 (NÂNG HẠNG 15/08 tối — CA DƯƠNG TÍNH ĐO ĐƯỢC, `c99361d`) — exception lên trace không qua scrub
`span.set_status` / `record_exception` (`langchain_callback.py:96-98`). **Không còn là rủi ro suy
luận**: security đo THẬT trên Postgres có sẵn của dự án (`fin05-postgres-1`, docker-compose):
```
DETAIL:  Key (phone)=(0912345678) already exists.   ← SĐT NGUYÊN VĂN trong DETAIL
```
→ vào `str(error)` → `span.set_status(..., str(error))` + `record_exception` → **ra thẳng backend
trace, không qua scrub** (`_scrub_and_truncate` chỉ áp attribute khác). Đường rò: BẤT KỲ vi phạm
unique constraint trên cột có PII (đăng ký trùng SĐT, upsert…). SQLite im lặng — đúng lớp lỗi chỉ
lộ sau deploy. Tái lập 3 dòng SQL. Security tự ghi nhận: trước đó họ khẳng định từ hiểu-biết-chưa-đo
— đúng lỗi họ vẫn đòi vai khác không mắc; nay đã đo. Bỏ nhánh "không dựng được Postgres thì khai
chưa-đo" trong bộ probe — Postgres có sẵn, S03-01..03 chạy ngay khi coder land.
**Bộ probe A1/A2 viết sẵn ở scratchpad** (đúng quy ước nháp): A1-01 byte-level · A1-02/03 round-trip
biên VN-đủ-dấu+emoji · A1-04 hàng-cũ (ca CHẨN ĐOÁN, không assert — chờ coder trả lời minh thị
backfill) · A2-01/02 hai mép 2000/2001 · A2-05 · A2-06 đường agent. Script kẹp dấu `he_thong` HAI
ĐẦU — lệch = phép đo VÔ HIỆU, không phải "gần đúng".

### 🟡 F-28 (TB) — tier-1 tiếng Anh neo vào MỘT động từ `ignore`; việc coder, KHÔNG cần PO quyết
Tester + tech-lead hội tụ bằng **hai phương pháp khác nhau** (Luật 16): mẫu tier-1 tiếng Anh chỉ
neo `ignore`, nên 7 câu tấn công **cùng ý định, đổi động từ** đi thẳng qua (`disregard` · `forget`
· `override` · `bypass` · `skip` · `do not follow` · `must not obey`). Security đo bổ sung: mẫu mở
rộng đưa độ phủ **1/8 → 8/8**, **FP 0/1814** trên kho MoMo thật (239K ký tự) và **0/7** trên đối
chứng tiếng Anh hợp lệ ⟹ thoả tiêu chí vào tier-1 do chính F-25 đặt. **Vá được ngay, không đổi
contract, không cần PO** — chỉ cần xếp lịch.

⚠️ **Hai vế phải giữ, đừng rút gọn khi báo cáo:**
- **(a) TRUNG BÌNH, KHÔNG phải P0** — F-25 §3(a) đã tuyên bố tier-1 **không phải lằn ranh**: nội
  dung vẫn bị spotlighting bọc và vẫn qua O1-O4.
- **(b) Bản vá KHÔNG đóng LỚP lỗi** — thêm 9 động từ vẫn là **danh sách viết tay**. Luật 18
  (ADR-023) đã sửa lớp này **cho tiếng Việt** và **chưa từng sửa cho tiếng Anh**; việc đó thuộc
  **CỔNG-A**. Sau khi vá phải nói *"bắt thêm 7 ca ĐÃ BIẾT"*, **không** được nói *"đã chặn lớp tấn
  công đổi-động-từ"*.

### ✅ Đính chính F-25 §3(a) — hai "lệch impl-vs-đặc-tả" của tester, coder KHÔNG phải vá (`d312428`)
Tester chặn ở hai lệch trên lớp tier injection; security phân xử: **một không phải lệch** (impl
ĐÚNG, kỳ vọng sai — kéo `bo qua…` về tier-1 sẽ **mở lại đúng lỗ F-25 vừa bịt**); **lệch còn lại là
chữ security viết sai**, họ tự rút sau khi đo FP `0/1814` — đúng phép đo mà F-25 §4 giao cho
security, nay mới làm. ⟹ **Coder không phải vá cả hai; tester viết lại kỳ vọng.**

### 📌 LUẬT MỚI (security rút, đáng đưa vào chuẩn dự án) — assert VẮNG MẶT mù với XOÁ QUÁ TAY
Assert dạng `X not in db` **LUÔN XANH khi nội dung bị xoá nhiều hơn cần thiết** — xoá càng mạnh
test càng xanh. ⟹ Một bộ test chỉ hỏi *"PII có vắng mặt không"* **KHÔNG THỂ** phát hiện over-scrub,
chạy bao nhiêu ca cũng vậy. Đây là lý do cấu trúc khiến bộ 13 ca của tester xanh mà lỗ 40% vẫn
lọt — **bộ test KHÔNG yếu**, nó đo đúng thứ đặc tả (TM-03) yêu cầu; vế toàn-vẹn thiếu vì **không
được viết vào sign-off**, không phải vì ai làm ẩu. Hai câu hỏi phải đi CẶP:
tester hỏi *"X có vắng mặt không"* · security hỏi *"cái CÒN LẠI là gì"* — đúng **Luật 16**, giá trị
nằm ở **sót khác chỗ nhau**. Khi vá S-01, trục đối chứng phải đo *"căn cứ từ chối còn đọc được
không"* và **để FILE RIÊNG** với bộ che-PII (nhét chung = mời một lần sửa làm hỏng cả hai).

**Vế bổ sung (security, để luật đủ dùng về sau):** luật này **không nói bộ test SAI — nó nói bộ
test ĐO SAI THỨ**. Nên cách vá **không phải "viết assert chặt hơn"** mà là **thêm một câu hỏi KHÁC
LOẠI**: cạnh mọi assert *"PII có vắng mặt không"* phải có ca đối chứng *"nội dung hợp lệ có SỐNG
SÓT không"*. Thiếu vế hai thì **bản vá chặt tay nhất luôn thắng theo số đo** (đúng Luật 2 — và là
lý do 27/96 của O1-O4 mới lộ ra được). Hạt giống có sẵn: **corpus 20 ca ghi chú sạch** security đã
giao tester ở §7 hồ sơ 15/08, ngưỡng **0/20** — không phải "thấp hơn".

### F-LOG — bản vá `submit_log.py` (`eadcca7`) NUỐT DÒNG JSON HỎNG, im lặng (tech-lead đo A/B)
Chạy `submit_log.py` THẬT với server giả + `AI_LOG_DIR` giả ở scratchpad (không đụng `.ai-log`
thật, không đụng `src/`). Kịch bản 10 dòng, 1 dòng bị cắt giữa chừng:
```
TRƯỚC vá (eadcca7^) băm f1e4950e1df6 : archive 10 dòng · dòng hỏng CÒN (truy được)
SAU   vá (eadcca7)  băm ab75391a3e09 : archive  9 dòng · dòng hỏng MẤT HẲN
```
Cơ chế: `submit_log.py:118-119` nuốt dòng không parse được (`except JSONDecodeError: pass`).
Trước vá, `_archive(pending)` chép NGUYÊN FILE nên dòng hỏng vẫn nằm lại archive. Sau vá,
`_archive_entries(entries)` chỉ ghi bản ghi ĐÃ PARSE → dòng hỏng không gửi, không archive, rồi
`pending.unlink()`. **Mất cả ba đường cùng lúc, không một dòng cảnh báo.**
**NẶNG vì:** STATE này tuyên bố *"bằng chứng khách quan DUY NHẤT là `.ai-log/archive/`"* — bản vá
làm suy yếu đúng kênh đó, và nó sắp chạy **19 lượt trên 9133 dòng backlog P-121** (deliverable #4).
`73/73 parse sạch` ở lượt 15/08 **KHÔNG** loại trừ: 73 dòng sạch thì nhánh nuốt-lỗi không chạy —
lại đúng "hiện diện ≠ hiệu lực" (nhánh CÓ tồn tại ≠ nhánh ĐƯỢC canh).
Vá ~3 dòng: gom dòng không parse được, ghi bytes GỐC vào archive (hoặc `*.hong.jsonl`) TRƯỚC
`unlink`. **CHƯA SỬA** — `scripts/` ngoài vùng ghi của mọi vai (xem F-ZONE), chờ PO thật giao.
⟹ **Khuyến nghị: vá F-LOG TRƯỚC khi đẩy backlog P-121**, đừng chạy 19 lượt trên đường có lỗ.

**Hồ sơ phép đo (Luật 10): `docs/giao-viec/2026-08-15-do-luong-F-LOG.md`** — hai script đo giữ
NGUYÊN VĂN trong đó, chạy lại được, chỉ thư viện chuẩn. **PO-agent đã chạy lại độc lập, khớp từng
số** (băm hai script tính lại bằng `shasum` cũng khớp con số tech-lead báo). ⚠️ Đó là **chỗ đặt
TẠM** vì bản gốc nằm ở `/private/tmp` gắn phiên tech-lead (phiên đóng = bằng chứng bốc hơi, và
đường dẫn chết trong hồ sơ tệ hơn không có); chỗ đúng là `scripts/` hoặc `tests/`, **chờ F-ZONE**.
⚠️ CA2 + phần B **CỐ Ý ĐỎ** (ca tái lập finding, không phải test hồi quy) — đừng ai sửa cho xanh.
**Bẫy đã ghi trong hồ sơ:** CA3 (tuần tự) báo thứ tự ĐẠT còn phần B (đua thật) báo TRƯỢT — cùng
một câu hỏi, ngược nhau; F-LOG-2 **chỉ hiện ra dưới đồng thời thật**, test tuần tự sẽ xanh giả.

**TIN TỐT cùng lượt đo:** nhánh **leftover CHẠY ĐÚNG** — 502 dòng, `BATCH_LIMIT=500` → lượt 1 gửi
500 + "2 deferred", lượt 2 gửi 2; `archive 502 dòng · id duy nhất 502 · trùng lặp 0`. Bản vá làm
đúng điều nó hứa, backlog sẽ không phình archive.

**F-LOG-2 (thấp, CÓ TRƯỚC bản vá — không phải hồi quy):** `submit_log.py:155` dùng
`open(LOG_FILE, "a")` → leftover (CŨ) bị nối SAU phần hook vừa ghi (MỚI); đo thật ra thứ tự
`[900, 901, 500, 501]`. Trớ trêu: nhánh THẤT BẠI `_restore_pending()` cố ý xử đúng ca này (có
comment *"pending (older) + LOG_FILE (newer)"*) — **nhánh thành công mắc đúng lỗi mà nhánh thất
bại được viết ra để tránh**. Chưa từng quan trọng vì leftover chưa từng chạy; backlog P-121 là lần
đầu nó thành thật. Sai thứ tự, KHÔNG mất dữ liệu — server sắp xếp lại được nếu bản ghi có timestamp.

### F-ZONE — `scripts/` là VÙNG VÔ CHỦ trong §4 (đề xuất, PO thật quyết)
§4 giao `src/ frontend/src/ migrations/ contracts/` cho tech-lead, `docs/` + `*.md` gốc cho po —
**không ai sở hữu `scripts/`**. Đó chính là chỗ bản vá `_archive_entries()` nằm lửng lơ trong cây
làm việc mà không vai nào nhận. Tech-lead xác nhận **không phải nháp của phiên này** (phiên khởi
động sạch, chưa ghi byte nào) ⟹ là của một PHIÊN TRƯỚC. Đề xuất thêm một dòng vào §4 giao
`scripts/` cho tech-lead, để nháp mồ côi lần sau có chủ.

## Cảnh báo còn tồn
- **gate-96 giờ BẬT THẬT** (`e4ef0e8`, không còn tắt — mục trên đã lỗi thời, sửa 15/08).
- **Số end-to-end gắn với hệ thống KHÔNG CÒN TỒN TẠI** (tester đo): lượt "sau" chạy ở
  `he_thong 6096dc8b5678` (commit `8d26548`); cây hiện tại `fd16681d8088` vì `7b68992` (note) land
  sau đó. ⟹ hai số **HÀNH VI** (câu 2: 17/17 · câu 4: 2/5) gắn hệ thống đã mất; hai số **DỮ LIỆU**
  (câu 1 cổng-96 · câu 3 fallback) mua vĩnh viễn. Trích cho quyết định 150 người thì trích được
  cả bốn, **chỉ cần ghi rõ nhãn**.
- **Cửa sổ đóng băng ĐÃ ĐÓNG** — security nhắn "MỞ TAY `src/`" sau khi nộp hồ sơ `c2c2d06`.
  Không vai nào đang giữ mốc nền. Coder chạm `src/` được khi PO giao việc.
- 🔴 **MỐC NỀN 18/20 `6c5fff420bb9` ĐÃ TRÔI** — cây làm việc nay `fd16681d8088` (đúng dự kiến:
  O1-O4 + F-27 + `note` đã land). **Hệ quả: lượt đo mới KHÔNG ghép cặp trước/sau với mốc cũ được
  nữa.** Đợt CỔNG-A phải đóng băng một **mốc nền MỚI ở một `he_thong` xác định TRƯỚC khi tiêu
  TPM** — không thì lặp đúng sự cố `8e46f28→6c5fff`.
  📌 **GHIM — security xin được gọi TRƯỚC lượt đo đầu tiên của CỔNG-A, không phải sau.** Bước đóng
  băng mốc nền mới là bước **không được bỏ**; gọi sau thì **lượt đo đã hỏng rồi mới biết**, và TPM
  đã tiêu. Đây là mốc tương lai duy nhất security chủ động xin ghim khi đóng sổ.
- **Rà pipeline scrub mới xong PHẦN OTel/callback.** CHƯA rà: đường **Langfuse** (đang TẮT có chủ
  đích) và **đường log của eval** (`logging_config` chưa init ở runner). Ghi rõ để không ai đọc §5
  của hồ sơ security thành "đã rà hết".
- **MT-E02 thu hẹp** (security §6): chỗ nổ xác định = `investigation_log.py:89 session.flush()`,
  FK `investigation_logs.ticket_id`. **MT-E02 và MT-F01 traceback TRÙNG HÌNH DẠNG** ⟹ nhiều khả
  năng **một defect hai tên** (đúng chỗ sổ ghi "coder gọi MT-F01, tester gọi MT-E02"). Cơ chế sinh
  id cũ **CHƯA kết luận** (Luật 5) — **giữ nguyên: ĐỪNG đốt TPM tái hiện**. Góc bảo mật mới: flush
  chết ⟹ mất `investigation_logs` của lượt đó ⟹ **ĐỨT MẮT XÍCH chuỗi truy vết của RÀNG BUỘC CỨNG
  3**, im lặng.
- **Mốc nền đối kháng chốt VĨNH VIỄN 18/20** (he_thong 6c5fff420bb9); 18 ca MÙ với siết-nhầm → "18/18→18/18"
  là chốt-chặn-hồi-quy MỘT NỬA, nửa kia đo bằng 🔇 + F-25(b). MT-A01/F-01 không quay lại nhánh "trước" được.
- CI: **TẤT CẢ đều treo sau F-CI (billing), không phải "chưa làm"** — note-tests đã land và xanh ở
  MÁY (15 passed), thiếu đúng phần quan sát trên runner · 2 eval chờ PO-2 secret · CI-4/5 chưa
  nghiệm thu. Không mục nào tiến được tới khi billing thông.
- **[c] oracle-phủ-định "không phải 21"** còn lọt (1 bit/lượt, có tài liệu) → đợt cổng-A (vẫn treo).
- Môi trường test cục bộ (máy PO-agent) thiếu sẵn `argon2` + model NER `xx_ent_wiki_sm` — không phải bug,
  chỉ là máy này chưa từng dựng venv cho repo (dùng venv scratchpad tạm, không commit).

## 📋 PHÂN CÔNG SONG SONG 15/08 (chiều muộn) — PO thật uỷ quyền PO-agent giao 3 vai
> PO thật chỉ quản PO-agent; PO-agent giao việc + nhận báo cáo từ 3 vai. Nguyên tắc chia:
> **vùng ghi tách hẳn** (coder: `src/`+`ci.yml`+`scripts/` · tester: `tests/`+`eval/` · security:
> `docs/security/` · PO-agent: `docs/`) và **không vai nào giữ mốc đo trên `src/` trong lúc coder
> mutate nó**. Ba việc đầu mỗi vai đều KHÔNG cần chờ vai khác.

| Vai | Việc (thứ tự ưu tiên) | Ràng buộc chính |
|---|---|---|
| **Coder** (`p-226-8f`) | ① F-CI-3 trả lời tên hàm `phan_tier` (MỘT DÒNG, đang chặn tester) → ② F-CI-2 một dòng `ci.yml` (trước khi billing thông; CẤM sửa bằng đóng ST2-P0-3) → ③ A1+A2 `description_raw` (CẤM scrub — nhóm A chờ ADR-025) → ④ F-LOG (gate đẩy backlog P-121) → ⑤ S-03 → ⑥ F-28 | BÁO-TRƯỚC-KHI-LAND mọi commit chạm `src/` · nháp ở scratchpad · S-03/F-28/A1/A2 KHÔNG tự đóng, chờ security probe |
| **Tester** (`p-226-c8`) | ① Port 2 script F-LOG vào `tests/` canh nhánh leftover (CA2+phần-B CỐ Ý ĐỎ, không sửa cho xanh) → ② Dựng trục đối chứng "căn cứ từ chối còn SỐNG SÓT không" (corpus 20 ca, ngưỡng 0/20, FILE RIÊNG; XÂY chưa chạy gate — chờ ADR-025) → ③ Gỡ skip 2 test tier khi coder trả lời tên hàm | KHÔNG đọc `src/` · KHÔNG mốc nền/TPM đợt này (coder đang mutate `src/`) |
| **Security** (`p-226-0f`) | ① Rà nốt 2 đường scrub tự khai "chưa rà": log-eval (ưu tiên, dính F-LOG) + Langfuse (mức "nếu bật thì rò gì") → ② Soạn trước bộ probe cho A1 (byte-level) · A2 (2 mép) · S-03 (cần Postgres, không kết luận từ SQLite) · F-28 (kèm đối chứng) → ③ GIỮ CHỜ: ADR-025, MT-E02 | Cần đóng băng `src/` thì báo PO-agent xin coder dừng tay, không tự lấy mốc |

**Điểm khớp nối:** coder land ①→tester gỡ skip · coder land ③④⑤⑥→security probe→mới đóng ·
ADR-025 ký→tester chạy trục đối chứng làm gate + coder làm B1/B2/B3/A3/A4.

### Tiến độ phân công (cập nhật chiều muộn 15/08)
- **✅✅ LÔ ĐÓNG SỔ HOÀN TOÀN — security nghiệm thu CẢ BỐN ĐẠT** (biên bản `9122677`, probe tại
  `cf98ef8`, `src/` byte-identical với `cc07dd3`): **A1** ĐẠT probe-bằng-byte **KÈM ĐIỀU KIỆN**
  (chỉ bảo vệ dữ liệu ghi TỪ `cc07dd3` trở đi — *"A1 đã nghiệm thu" ≠ "description_raw đã được mã
  hoá"*, hàng cũ vẫn plaintext, backfill = quyết định PO TRƯỚC pilot) · **A2** ĐẠT chặn ở tầng
  service không rơi xuống CHECK · **S-03** ĐẠT trên Postgres THẬT (lỗi thật từ container →
  `[PHONE_NUMBER]`, 0 PII trong span, vẫn giữ tên constraint để gỡ lỗi — hai vai bù đúng thiết kế:
  coder tự khai "chuỗi lỗi mô phỏng" → security lấy lỗi thật) · **F-28** ĐẠT 8/8 · 0/7 · FP 0/1814.
- **📌 GIỚI HẠN CÔNG CỤ DẤU-BĂM (tech-lead chỉ ra, security xác nhận):** `he_thong` băm
  `src/**/*.py` — **KHÔNG phủ `scripts/` + `migrations/`**. Lô chạm ngoài `src/` sẽ có dấu
  **không lệch mà vẫn VÔ NGHĨA**. Nhãn phép đo cho lô đa-vùng: dùng **SHA commit**, không dùng
  `he_thong`. (Biên bản `9122677` dùng SHA vì đúng lý do này.)
- **🎁 DẪN XUẤT THỨ BA CHO S-01 (từ probe S-03):** scrub gán `DETAIL`/`ERROR` → `[ORGANIZATION]` —
  cùng lớp lỗi với `"chính sách"` → `[PERSON]` nhưng ở **đường khác** (trace ≠ note), **vai khác**
  phát hiện, **phương pháp khác**. Ba dẫn xuất độc lập cùng kết luận: **sai NHẬN DẠNG, không sai
  NGƯỠNG — lỗi là thuộc tính của LỚP NER, mọi cửa dùng `scrub_pii` đều thừa hưởng.** Đây là lập
  luận mạnh nhất cho việc ADR-025 quyết CƠ CHẾ, không vá từng cửa.
- Security tự đính chính trong biên bản: khuyến nghị 40.000 của họ ở phản biện **sai ở mép trên**
  (thiếu trục chặn-flood) — ADR đã ghi 12.000 + cửa sổ từ `cda800d`, khớp. Quét `.md` trong
  `eval/results` đóng: **0 SĐT thật** (16/18 seed, 2/18 mảnh mã GD — số "18" ban đầu tự thổi bởi
  đúng false-positive đó).
- **F-LOG-2 ĐÃ LAND `e321780`** (sớm hơn lịch), tester gỡ marker F-LOG xác nhận 5 passed · 1 xfailed.
- **🔴 F-28b — tester bắt lỗ TRONG phạm vi F-28 vừa ký:** `disregarding all previous instructions`
  LỌT — dạng **V-ing của chính động từ F-28 vừa thêm** (mẫu đòi dấu cách ngay sau động từ). Không
  phải "lớp rộng chưa làm" — biến thể hình thái của từ trong phạm-vi-tự-nhận-đã-đóng. Coder đo HAI
  bản vá trước khi đề xuất: bản A (liệt kê hậu tố `s|ed|ing`) **cũng lọt** `forgetting` (phụ âm
  gấp đôi — danh sách viết tay vá lỗ danh-sách-viết-tay, thiếu đúng chữ kế, lần hai trong cùng bản
  vá); bản B (thân + `\w*`) đóng **8/8, FP 0/7 + 0/2006 kho MoMo thật**. Đo cả cái KHÔNG đóng:
  5 ca đổi-hẳn-động-từ (`refrain from…`, `pay no attention…`, gõ-sai `ignroe`) vẫn lọt = CỔNG-A.
  ~~PO-agent QUYẾT: đường (1) — land bản B vào tier-1~~ → **🔴 ĐẢO LỆNH sau probe khẩn của
  security (Luật 8 lần SÁU — chân bị rút là của CẢ BA):** bản B gây **FP TIER-1 THẬT** — `ignor\w*`
  bắt `ignorant` (từ khác hẳn), và *"Please do not disregard the safety guidelines"* bị **XOÁ
  TRẮNG** = **F-25 tái diễn nguyên hình dạng bằng tiếng Anh** (khuyến cáo an toàn thật bị xoá).
  Vì sao FP 0/7+0/2006 không bắt được — **corpus có lỗi, security tự nhận corpus của họ**: 7 câu
  đối chứng mỏng đúng trục bản vá chạm (không mệnh-lệnh-phủ-định, không ca `\w*` vươn quá);
  2.006 câu kho MoMo là TIẾNG VIỆT — cấu trúc không thể bắt FP mẫu tiếng Anh. Số đúng, không nói
  gì về lớp lỗi này.
  **LỆNH CUỐI (security đề nghị, PO-agent duyệt): `\w*` vào TIER-2** (giữ nội dung + nhãn trung
  tính + đếm — V-ing attack bị đánh dấu, không bị xoá trắng, vẫn qua spotlighting + O1-O4) ·
  **tier-1 GIỮ HẸP** dạng nguyên thể 0/1814 · phân biệt cực-của-động-từ (`do not follow` tấn công
  vs `do not disregard the safety` khuyến cáo) = sửa LỚP thuộc **CỔNG-A**, cấm nhét vào hotfix.
  Đây là áp đúng tiêu chí F-25 §3(a): vào tier-1 = FP đo được phải bằng 0 trên nội dung hợp lệ.
  ~~Chữ ký F-28 ĐÃ RÚT~~ → **✅ F-28 ĐÓNG HẲN — security ký lại tại `ae954fe`** (biên bản
  `a7c191a`), cổng đối chứng mới **50 ca / 8 trục** thay bộ 7 câu cũ. Bốn vòng trong một tối:
  F-28 → F-28b (bác vì FP tier-1) → F-28c → F-28d → F-28e. Suite **540 passed · 0 failed**,
  ruff sạch, 4 test tier của tester xanh.
- **Hồ sơ F-MIG đặt tại `docs/giao-viec/2026-08-15-f-mig-alembic-sqlite.md`** (tech-lead soạn,
  PO-agent chép nguyên văn vào docs/ — attribution trong file). Chờ PO thật xếp lô riêng; phép
  kiểm quan trọng nhất sau vá = SO SCHEMA HAI ĐƯỜNG (upgrade-head vs create_all phải TRÙNG).
- **HAI LUẬT MỚI từ lô F-28 (PO-agent ratify vào chuẩn dự án):**
  · **Luật mỏ-neo-sau-bỏ-khoảng-trắng** (security `20bb323`): token dùng làm MỎ NEO dưới phép
    khớp ĐÃ BỎ KHOẢNG TRẮNG phải ĐỦ DÀI VÀ ĐẶC TRƯNG để không xuất hiện như chuỗi con, kể cả
    vắt ngang ranh giới từ (ca `these` ⊂ `thesecurity`).
  · **Luật điểm-mù** (coder+security chốt): *điểm mù không được chữa bằng cố gắng — nó được chữa
    bằng việc VỪA NHÌN THẤY cùng lớp lỗi ở người khác.* Hệ quả thao tác: **finding phải được kể
    kèm CƠ CHẾ, không chỉ kèm kết luận** — cơ chế mới là thứ truyền được sang người khác. (Bằng
    chứng: coder viết `system rules` mù với `ecosystem`; thứ cứu họ là ca `these`⊂`thesecurity`
    của security còn nóng trong đầu.)
  · Hệ luận corpus, đúng HAI CHIỀU trong lô: bộ ca do MỘT vai soạn gần như chắc chắn hụt trục
    của vai khác — cả bộ ĐỐI CHỨNG (security hụt trục danh-từ-đích) lẫn bộ TẤN CÔNG (bản siết
    của security tụt recall 3 ca vì bộ 10 ca của họ không chứa chúng).
- **✅ LÔ CODER ĐÃ LAND — HEAD `cc07dd3`** (5 commit: F-LOG `cc07dd3` · F-28 `e082a34` ·
  S-03+F-30+F-29-gitignore `83f45df` · A1+A2 `5b65b81` · F-CI-2+ruff `37ed7fc`). Pathspec sạch —
  không đụng `tests/`/`docs/`. Đo tại `cc07dd3`: ruff sạch · invariants 23 · contracts 3/3 ·
  suite 492 passed/18 skipped/9 xfailed/**1 failed = XPASS(strict) ca F-LOG của tester — cơ chế
  chạy ĐÚNG**: bản vá làm ca tái lập qua được, strict biến "qua" thành đỏ buộc tester gỡ marker
  (họ gỡ, không phải coder). **Chưa đóng A1/A2/S-03/F-28 — chờ probe security** (đã được mời).
- **A2-06 ĐÓNG bằng câu trả lời + số đo:** trần đặt ở `create_ticket_with_fraud_check`
  (`complaint_intake.py:118` — call site DUY NHẤT của `_create_ticket`) ⟹ phủ CẢ BA đường
  (REST `main.py:538` · agent `customer_tools.py:620` · `flag_human_handoff`), đo cả ba có đối
  chứng (3.200→CHẶN · 2.000→NHẬN). Còn TỐT hơn gợi ý đặt-ở-`create_ticket`: trần đứng TRƯỚC fraud
  engine (engine đọc `description_raw` làm `utterance_text`) — không phân tích gian lận trên chuỗi
  20K rồi mới từ chối. CHECK 12.000 không là lưới duy nhất của đường nào — nguyên tắc ADR nguyên vẹn.
- **A1-04 ghi minh thị vào docstring `models.py`** (nơi người sửa tiếp theo thật sự đọc): hàng
  trước 2026-08-15 plaintext VĨNH VIỄN trên đĩa; "đọc được" ≠ "được mã hoá at-rest"; chấp nhận vì
  seed/test + pilot hoãn; **backfill là quyết định RIÊNG phải ra TRƯỚC khi mở pilot**.
- **⚠️ Nuance migration phải giữ khi đọc "A2 đã verify":** migration A2 (`a7b8c9d0e1f2`) **CHƯA
  TỪNG chạy qua alembic** — chuỗi gãy ở `a1b2c3d4e5f6` (SQLite) TRƯỚC khi tới nó; coder verify
  CHECK bằng `create_all` + probe hành vi. "A2 đã verify" ≠ "migration A2 đã verify".
- **F-LOG-2 (thứ tự đảo): PO-agent xếp lịch = lô nhỏ KẾ TIẾP của coder, ưu tiên thấp** — vá rẻ
  (tái dùng logic prepend của `_restore_pending` cho nhánh leftover), xfail của tester đứng làm
  tài-liệu-sống tới lúc đó. Không gấp: sai thứ tự không mất dữ liệu, server sort được theo ts.
- **QĐ 5 / bound 12.000: security ĐO LẠI XÁC NHẬN ĐỦ** (`44c3c9a`) — biên 12% trên worst-case
  emoji 4-byte, và Fernet tất định theo byte nên không có ca xui. **Đủ CÓ ĐIỀU KIỆN** ⟹ ca mới:
- **🟠 A2-06 (CA PHẢI KIỂM, chưa phải finding — security minh thị chưa đo vì cây trôi):**
  `description_raw` có **HAI đường ghi** — REST (qua Pydantic, có trần) và **AI-gọi-tool dưới danh
  nghĩa customer** (`customer_tools` → `create_ticket…`), đường sau **không đi qua
  `ComplaintCreateRequest`**. Nếu đường agent không có trần riêng: mô tả quá dài rơi thẳng xuống
  CHECK DB → `IntegrityError` → 500 (hình dạng F-21), trong khi mọi test REST xanh. **CHECK phải
  là lưới CUỐI, không được là lưới DUY NHẤT của bất kỳ đường nào.** → chuyển coder dạng CÂU HỎI.
- **A1-04 nhắc lại cho probe:** `complaints` ĐÃ CÓ dữ liệu (khác `messages` 0 dòng) — coder chọn
  không-backfill (hàng cũ đọc được qua đường InvalidToken) ⟹ **hàng cũ nằm PLAINTEXT vĩnh viễn
  trên đĩa** trừ khi có quyết định backfill-mã-hoá riêng. Test DB-sạch không lộ ca này.
- **A2 bound CHỐT LẦN CUỐI = 12.000, ghi thành CỬA SỔ [10.764 … 26.764]** (ADR-025 QĐ 5 sửa lần 2):
  40.000 của PO-agent bị coder bác bằng đo — ≈28.943 ký tự ASCII lọt, flood 20K ASCII đi thẳng qua.
  Luật 8 lần NĂM, bắt cả coder (mẫu ASCII) lẫn security+PO-agent (mẫu 3-byte quên emoji 4-byte).
  Thoát vòng = ghi CỬA SỔ kèm cả hai mép, mọi lần đổi số phải đo lại CẢ HAI.
- **Coder vá thêm ngoài phạm vi (chấp nhận, có lý do):** 3 lỗi ruff có sẵn từ trước (N812×2 +
  UP037) — không vá thì job lint đỏ TRƯỚC khi tới pytest, F-CI-2 vô nghĩa.
- **🔴 PHÁT HIỆN MỚI (có sẵn, cần quyết định riêng — CHƯA ai sửa): chuỗi migration GÃY trên SQLite**
  tại `a1b2c3d4e5f6` (ADR-019): `NotImplementedError: No support for ALTER of constraints in SQLite
  dialect` ⟹ `alembic upgrade head` trên DB trắng SQLite CHẾT. Coder verify CHECK A2 bằng
  `create_all` + probe hành vi thay vì alembic. Hướng vá khi giao: `render_as_batch`/batch_alter
  cho SQLite — xếp lịch riêng, không gộp lô này.
- Suite lúc báo cáo: 492 passed · 18 skipped · **9 failed = toàn bộ ở cổng F-NOTE của tester
  (`test_note_toan_ven_can_cu_tu_choi.py`, file chưa track) — ĐỎ CÓ CHỦ ĐÍCH chờ vá B1/B2**,
  không phải hồi quy của lô coder.
- **Coder ①②③(A1) XONG** (báo-trước-khi-land đúng luật): F-CI-2 verify hai chiều (appsec
  227 passed/1 deselected · security-findings-gate VẪN ĐỎ — chuyển finding về đúng job canh, không
  giấu) · A1 `models.py:223` EncryptedText, probe hành vi tiền tố Fernet + đối chứng hàng-cũ-vẫn-đọc
  (đường InvalidToken, không cần migration/backfill) — CHỜ security probe mới đóng. **A2: PO-agent
  quyết phương án (b) + trần 2.000 ký tự** (schema chính-xác-ký-tự + CHECK thô ciphertext ≤4.000;
  Fernet nở theo byte nên DB không diễn đạt được trần ký tự — số đo coder ×1.72-1.9).
- **🔴 Finding mới của coder (Luật 8 lần BA): F-24 vs F-25 MÂU THUẪN trên nhánh EN**
  (`customer_tools.py:152-154` chỉ có comment F-24; `:165` VN có cả hai) — nhánh EN không bị bỏ
  quên, nó bị MỘT trong hai bản vá sờ tới. → security gộp phân xử vào probe F-28.
- **Corpus 20 ca ĐÃ XUẤT FILE** (`c403384`): `docs/security/corpus-ghi-chu-sach-20-ca.jsonl` (+.md,
  8 ca 🔴). Trích **bằng AST** từ script đo gốc — không chép tay, không import src/. **BA GIỚI HẠN
  đi kèm corpus (cấm dùng rộng hơn):** (1) 20 câu soạn tay — chứng minh TỒN TẠI lớp chặn nhầm,
  KHÔNG phải tỷ lệ sản phẩm — **đừng để "40%" đi vào báo cáo PO như tỷ lệ thật**; (2) chỉ phủ nhóm
  B — nhóm A (khẩu ngữ/sai chính tả/không dấu) cần corpus riêng; (3) thuần đối chứng, **PHẢI chạy
  cùng bộ ca có PII, cấm chạy lẻ** — không thì bản vá "không scrub gì" đạt 0/20 hoàn hảo. Mở rộng =
  THÊM ca GC-21+, **không sửa 20 ca gốc** (mất mốc). `ket_qua_goc` là nhãn tại `fd16681d8088` —
  cây ĐÃ trôi sang `f3193ecae0e2` (A1 land); ai đo lại = cặp MỚI đóng dấu riêng, không ghi đè.
- **Tester ①③ XONG** — `tests/test_ai_log/test_f_log_leftover.py`: 3 passed · 2 **xfail(strict)** ·
  suite đầy đủ 478 passed/0 failed. Hai ca finding dùng `xfail(strict=True)` thay đỏ-trần (PO-agent
  RATIFY): hiện rõ trong report, không chặn CI khi billing thông (né hình dạng F-CI-2), và khi coder
  vá F-LOG thì **XPASS tự báo lỗi buộc gỡ marker** — yêu cầu "chỉ xanh sau khi vá" thành CƠ CHẾ.
  Thêm assert server-nhận-đủ (502 archive ≠ 502 đã POST — hai câu hỏi, hai assert). Không port phần
  A/B lịch sử (đã kết luận, `git show eadcca7^` chết trên CI fetch-depth:1) — kết luận giữ trong
  `reason` của xfail. **Việc ③**: `_phan_loai_tier` (coder trả lời) → 2 bộ tier chạy lần đầu, lượt
  đầu 6 failed → security phân xử bằng phép đo mới → tester viết lại kỳ vọng → **29 passed**,
  `he_thong` trước=sau=`fd16681d8088`, `src/` không ai chạm. +5 ca khoá 4 họ tier-1 + Luật 6/6b vào
  `CHUAN-VIET-TEST.md`.
- **Tester ② XONG — trục đối chứng LÀ CỔNG SỐNG** (`he_thong c110a1a8eff7`, dấu trước=sau, đo 3
  lần tất định): **8/20 chặn nhầm, cổng ĐỎ đúng chủ đích**. Giá trị nhất: **DANH SÁCH trùng 8/8
  với security** (GC-02·03·07·10·11·15·17·18) qua **hai phương pháp khác nhau** — security gọi
  thẳng hàm scrub, tester đi đường ghi thật POST /reject → **đọc thẳng DB** (đọc qua API không phân
  biệt được che-khi-ghi với ghi-thô-che-lúc-trả). Chốt được: finding KHÔNG phải hiện vật của cách
  đo · còn nguyên tại cây đã gồm lô A1/F-28 · cổng sống không ai phải nhớ chạy lại. Ba giới hạn
  corpus đều thành CƠ CHẾ (docstring + test cấm-chạy-lẻ đọc `request.session.items`, nghiệm thu
  hai chiều). Bộ đo KHÔNG đọc `ket_qua_goc` để chấm — đo lại từ đầu, đóng dấu riêng.
  **Một lượt đo bị VỨT đúng quy trình** (chạy khi coder sửa dở, dấu trước≠sau): con số không SAI,
  nó **VÔ DANH** — không gán được nhãn hệ thống thì không tái lập/ghép cặp. Khác cơ chế Luật 4
  (pytest import một lần — 20 ca vẫn cùng hệ thống trong bộ nhớ); gộp hai lý do sẽ khiến lần sau
  quy sai nguyên nhân.
  ~~PO-agent quyết: gắn marker `security_finding`~~ → **ĐÈ bằng số đo của tester: cơ chế là
  `xfail(strict=True)` THEO TỪNG CA, KHÔNG marker.** Tester đo thử marker và tìm ra lỗ chết
  người: job `security-findings-gate` lọc `-m security_finding` sẽ **DESELECT bộ ca có PII lẫn
  chính test cấm-chạy-lẻ** ⟹ trục đối chứng chạy MỘT MÌNH trong đúng job đó — bản vá "gỡ sạch
  scrub" đạt 20/20 xanh mà không gì bắt được, đúng kịch bản cổng sinh ra để chặn. Cơ chế
  xfail-strict giữ đủ 3 mục tiêu (không đỏ lint-and-test · không job mới · không chờ coder) VÀ
  giữ cặp đối chứng cùng phiên. **Đọc tín hiệu khi B1/B2 land:** 8 ca XPASS ⟹ suite ĐỎ =
  **THÀNH CÔNG** (buộc gỡ marker → thành regression-gate), đừng đọc thành hồi quy; vá-gỡ-sạch-scrub
  thì bộ ca PII cùng phiên đỏ — hai tín hiệu tách bạch. Cơ chế đã tự bắn ĐÚNG hai lần trong
  phiên (F-LOG, F-LOG-2).
  **Luật 7 (5 mục 7a-7e) vào `tests/CHUAN-VIET-TEST.md`** — canh chính CÔNG CỤ ĐO; đã dán tóm
  tắt sang `docs/TESTING.md` theo yêu cầu tester. Treo nhỏ: 2 failed `EN-S03` chờ security phân
  xử `security` có phải mỏ neo META không.
- **Security ①② XONG** (`7c71905`, không cần đóng băng — toàn đọc tĩnh): đường log eval
  **KHÔNG TỒN TẠI** (`configure_logging()` chỉ ở `main.py:115`) ⟹ câu "log eval có scrub không"
  không áp dụng — chưa có gì để scrub, và hỏng thì không có gì điều tra. **GHIM vào F-LOG: không
  đóng nếu chỉ "có log" — log eval phải qua CÙNG lớp scrub với đường app, verify bằng ca có PII.**
  Bộ probe A1/A2/S-03/F-28 đã soạn, land là chạy; điều kiện ký = đủ BA (hiệu quả + đối chứng +
  dấu he_thong hai đầu), thiếu đối chứng thì không ký kể cả hiệu quả đẹp.
- ⚠️ Nếu `test_mau_tier1_chi_thi.py`/`test_f24_recall_tier1.py` ĐỎ trong lô coder: **không phải
  hồi quy sản phẩm** — hàm đổi tên; gọi tester, đừng sửa test.

### 🔴 F-29 (CAO cho PILOT) — `eval/results/` 138 file TRACK trong git, harness ghi tin khách nguyên văn
PO-agent xác minh độc lập: **138 file track · 74 file `_raw.json` · `.gitignore` 0 dòng về eval**.
File `_raw.json` chứa `all_customer_texts` (tin khách nguyên văn mọi lượt) + `tool_calls_day_du` +
traceback. **Hôm nay phơi nhiễm THẤP** — payload đã che (`********0001`), lớp masking BR-06 chạy
đúng. **Nhưng cơ chế là rủi ro thật:** BR-06 **không che chính chủ** (`lookup_transaction.py:41,53`);
eval chạy dưới danh nghĩa người-không-phải-chủ nên mọi thứ ra đã che — **pilot thật thì khách hỏi
giao dịch CỦA HỌ ⟹ `is_owner=True` ⟹ SĐT/STK/họ tên THẬT không che, vào thẳng file git-track**.
Cộng `all_customer_texts` chưa bao giờ qua scrub.
**Chạm thẳng điều kiện pilot của security ("có đường xoá sau đợt")**: file đã commit thì không có
đường xoá thực hành (xoá commit sau không xoá lịch sử; rewrite+force-push = loại việc luôn phải hỏi
PO, bất khả nếu repo đã clone). ⟹ **chạy harness với người thật mà không sửa = điều kiện pilot TRƯỢT.**
- Mức tối thiểu TRƯỚC pilot: `.gitignore` loại `_raw.json` (→ coder, kèm lô) + scrub-trước-khi-ghi
  (→ tester, vùng `eval/`, sau việc ②).
  **⚠️ PHẠM VI SỬA theo đo lại của tester (không phải chỉ `all_customer_texts`):** trường văn bản
  tự do trong `_raw.json` gồm `all_customer_texts · all_agent_replies · reply · description ·
  tool_calls` — và `reply`/`all_agent_replies` là **lời agent NHẮC LẠI thông tin khách** (tên, số
  tiền, mã GD — đó là mục đích của nó), nên scrub riêng tin khách thì PII thật vẫn rò qua lời agent
  ở pilot. **Phạm vi đúng: scrub MỌI trường văn bản tự do.** Số đo lại: 69 file raw trên đĩa ·
  138 track · 33 file có `all_customer_texts`.
  **HỒI TỐ: KHÔNG scrub lại 69 file cũ — CHỈ chặn từ nay. Lý do ghi rõ (PO-agent quyết):** file cũ
  đã đo là vô hại (eval chạy danh nghĩa không-chính-chủ, BR-06 che hết), và scrub file đang track
  cũng KHÔNG xoá được bản gốc khỏi lịch sử git — muốn xoá thật phải rewrite history, đúng thứ
  security đã cân và chủ động không đòi. Scrub hồi tố = tốn công mà không thêm an toàn thật.
- **138 file CŨ: quyết định của PO THẬT** — phơi nhiễm thấp, rewrite history đắt/rủi ro hơn lợi ích
  (security chủ động KHÔNG đòi xoá), nhưng file kết quả là bằng chứng nộp bài (deliverable #10) nên
  không ai khác quyết thay được.
- Còn treo security tự khai: mới đo MẪU file mới nhất, chưa quét hết 138 file, chưa kiểm các `.md`
  trong `eval/results/`.

### 🟡 F-30 (TB, tiềm ẩn) — LangSmith: kênh xuất dữ liệu mở được bằng env var, không để vết trong git
KHÔNG có tích hợp nào trong `src/` (grep sạch — tin tốt). Nhưng gói `langsmith` 0.11.0 ĐÃ CÀI (kèm
langchain; PO-agent xác minh có trong env), và tracer native của LangChain bật **hoàn toàn bằng env
var**, đi vòng qua `_scrub_and_truncate` (lớp đó nằm trong callback TỰ VIẾT, tracer native không gọi).
Bật trên dashboard ⟹ không diff, không ai review thấy. `docs/guide/chapter-07.md` (giáo trình AI20K,
KHÔNG phải runbook FIN-05) hướng dẫn bật ở production — đội đang học nó. Pháp lý nếu bật với dữ liệu
thật: **chuyển dữ liệu cá nhân ra nước ngoài — NĐ 13/2023 Điều 25**, cần hồ sơ đánh giá tác động.
Vá rẻ (→ coder, kèm lô): đặt `LANGCHAIN_TRACING_V2=false` **MINH THỊ** trong config/Dockerfile —
biến cấu-hình-ngầm thành quyết-định-hiện.

## Việc kế tiếp
0. **PO THẬT — TRƯỚC PILOT (danh sách gom, mới):** quyết **backfill A1** (mã hoá hàng
   `description_raw` cũ — hiện plaintext vĩnh viễn, docstring `models.py` ghi rõ) · cam kết 2 điều
   kiện pilot của security (dữ liệu thật + đường xoá) · A3/A4 pha 2. Pilot đã hoãn nên KHÔNG gấp —
   gom một chỗ để không rơi.
1. **PO THẬT — billing org `AI20K-Build-Phase-Cohort-3`** (F-CI). Chặn mọi nghiệm thu CI.
2. **PO THẬT — MỘT quyết định cho CẢ BỐN CỬA văn bản tự do** (S-01 `note` · S-02 `agent_note` ·
   ST2-P0-3 `messages.content` · `complaints.description_raw`) ⟹ **ADR-025**. Ba lý do buộc phải
   gộp: (a) chốt riêng lẻ = che ô này hở ô kia, hồ sơ §7 đã cảnh báo từ trước; (b) `scrub_pii` —
   cơ chế được kê cho cả bốn — **đã đo được hỏng 40%**, nên phải trả lời **"che bằng CƠ CHẾ nào"**
   TRƯỚC khi trả lời "giữ 4 số hay che trọn" (§8.2); (c) ST2-P0-3 giữ **mở/đỏ có chủ đích** cho
   tới khi có quyết định này — **đừng đóng nó để CI xanh**. KHÔNG để coder tự vá.
3. **PO THẬT — giao ai vá F-LOG** (`scripts/` vô chủ, xem F-ZONE) và chốt: **vá TRƯỚC rồi mới đẩy
   backlog P-121**. Đẩy trước = chạy 19 lượt trên đường có lỗ nuốt-dòng-hỏng, đúng deliverable #4.
4. **Coder — BỐN việc rẻ, KHÔNG cần PO quyết cơ chế, chỉ cần xếp lịch:**
   (a) **F-CI-2** một dòng `ci.yml` thêm `-m "not security_finding"` cho job `appsec` — nên xong
   **TRƯỚC khi billing thông**, nếu không cổng đỏ vì lý do sai đúng lúc đội dễ tặc lưỡi nhất;
   (b) **F-CI-3** trả lời một dòng **tên hàm thật** của `phan_tier` để 2 bộ test tier-split hết skip;
   (c) **S-03** scrub exception trước khi lên trace — độc lập, không chặn gate nào;
   (d) **F-28** mở rộng động từ tier-1 tiếng Anh (1/8→8/8, FP 0/1814) — nhớ **vế (b)**: bản vá
   KHÔNG đóng lớp lỗi, chỉ bắt thêm 7 ca đã biết; lớp thuộc CỔNG-A;
   (e) **A1** mã hoá at-rest `complaints.description_raw` + **(f) A2** trần độ dài — security xác
   nhận **không chờ ADR-025**: A1 chỉ là **bù cho ngang chuẩn đã có** (live-chat đã `EncryptedText`),
   không phải cơ chế mới cần quyết.
   ⚠️ **Cả bốn bản vá S-03 · F-28 · A1 · A2 PHẢI có probe từ VAI KHÁC trước khi coi là đóng** —
   security đã nhận sẵn việc re-probe. Lý do là luật đội đã ratify: **coder tự nghiệm thu là CẦN,
   KHÔNG BAO GIỜ ĐỦ** cho lớp phòng vệ (mọi phép kiểm coder tự thiết kế thừa hưởng điểm mù của coder
   — rút từ sự cố F-23 thật).
3. PO chốt hướng đợt 150 người (số end-to-end đã có, nhớ ghi nhãn hành-vi/dữ-liệu ở "Cảnh báo").
4. Coder: chờ security "MỞ TAY src/" rồi mới chạm. Xếp hàng: chip câu 3 (sau 5a core + QA baseline)
   · đợt cổng-A gộp 3 oracle · câu-4 RAG retrieval (chunk/embedding, trước pilot 150 người).
5. **PO-2**: đặt `OPENAI_API_KEY` thành secret trên GitHub → mở 2 CI eval (chỉ có tác dụng SAU khi
   billing thông).

## Phiên rà soát bảo mật ĐÃ ĐÓNG SỔ — mục lục cho phiên security sau
**`docs/security/2026-08-15-ket-so-ra-soat-cuoi-sprint.md`** (`80b217a`) = mục lục + tư thế rủi ro
tồn dư, **không lặp nội dung**, để phiên sau không phải dựng lại mạch từ 7 commit + một chuỗi tin
nhắn. Năm việc treo security nhận đầu phiên, trạng thái đóng sổ:

| Việc treo | Trạng thái |
|---|---|
| `note` / CI security-gate | **XONG** — kết luận **CHƯA BẬT** |
| mốc nền 18/20 | **ĐÃ TRÔI** `6c5fff` → `fd16681d`, kèm hệ quả bắt buộc cho CỔNG-A |
| oracle-phủ-định "không phải 21" | **KHÔNG ĐỔI** — vẫn thuộc CỔNG-A |
| MT-E02 | **thu hẹp, CHƯA đóng** (cố ý — Luật 5) |
| pipeline scrub | **XONG MỘT PHẦN** — rà OTel/callback; **chưa** rà Langfuse (tắt có chủ đích) + đường log eval (F-LOG) |

### 📌 Về SÁU ca tự-bắt-mình trong phiên (§6 kết sổ) — ghi để đọc đúng, không đọc thành cẩu thả
Sáu ca cùng họ **thước-hiệu-chuẩn-theo-vật**: PO-agent tuyên bố `archive/` là bằng chứng đủ · PO-agent
gọi `note` là việc đã đóng · security viết "cả bốn ô đã đo hành vi" khi một ô chưa probe · security
kê `scrub_pii` ở §5.2 mà chưa đo nó · test skip im lặng hai ngày · 15 kỳ vọng suýt viết theo impl.
Đánh giá security ghi nguyên văn:
> Đây là dấu hiệu **kiến trúc phân-vai ĐANG CHẠY**, không phải dấu hiệu đội cẩu thả. Một đội không
> có cơ chế đối kháng thì các lỗi này **không được PHÁT HIỆN**, chứ không phải không xảy ra.

**Và cả sáu ca đều do CHÍNH NGƯỜI MẮC tự bắt**, không phải do người khác soi ra — thứ khó có hơn cả
việc bắt được lỗi của nhau.

## Hoãn có chủ đích
- Hạ tầng đo temp=0/k≥3 (gói B2 HOLD, floor nhiễu 20/40) · reseed gộp (⚠️ gỡ lọc-A1 khi from_bank sửa) ·
  401/403 hai route OTP · B3 timezone (31 utcnow) · lộ trình EU/US G1(SLA)/G3(audit bất biến) — xem PO-TONG-KET.
