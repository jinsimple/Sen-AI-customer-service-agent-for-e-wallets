# Tường thuật đợt "OTP trước token" — các khối đã ĐÓNG, chuyển khỏi bảng theo dõi

> Chuyển từ `docs/giao-viec/CHECKLIST-dot-otp-truoc-token.md` theo `CLAUDE.md §7b`.
> **Không xoá gì** — bảng theo dõi để lại đường dẫn tới đây.

> Lý do dọn: bảng đã **1.470 dòng**, phần lớn do PO chèn tường thuật sau mỗi vòng điểm danh.
> PO vừa dặn Lead *"bản nghiệm thu phải đọc hết trong ba phút"* — không dọn thì lời dặn ấy rỗng.

<a id="su-co-ha-tang"></a>

## 🔴 SỰ CỐ HẠ TẦNG — PO gây ra, Coder tình cờ cứu

**Cả NĂM ngăn Docker đang chạy đều mang mã CŨ.** 12 commit chạm `src/` hôm nay chưa vào
bất kỳ ảnh nào.

```
fin05-backend-1        6722ab874767   ← ngăn DEMO
fin05do-backend-1      26b1bd3b1ff5   ← ngăn ĐO
fin05ttl-backend-1     22ad74bdfa81   ← ngăn ĐO
fin05-final-backend-1  6722ab874767
fin05-po-test-backend-1 7636400be9c4  ← build từ scratchpad PHIÊN KHÁC
cây làm việc THẬT      691dd9c40578
```

🔴 **Và PO đã dặn QA/QC gõ buổi test ở `fin05-po-test`** — nhiều lần, trong checklist, phiếu,
và ba tin nhắn. Ngăn ấy **không chứa một dòng nào** của đợt. Nếu buổi chạy ở đó, **mọi kết
quả xanh sẽ vô nghĩa mà không ai biết**, và A3 chỉ gỡ một lần.

**Đây là lỗi nặng nhất của PO trong đợt — nặng hơn con số `11` sai.** Một con số sai thì có
người bác. Một **lời dặn hạ tầng** thì không ai kiểm: QA/QC không có lý do gì nghi ngờ địa
chỉ do PO đưa, và họ đã soạn trọn bộ ca cho đúng ngăn ấy.

**Thứ cứu được KHÔNG phải PO:** Coder đi kiểm ảnh vì **lý do khác hẳn** *(thiếu hai cờ mới)*
rồi tình cờ đụng vào nguồn build.

**PO tự soát mọi lệnh của mình:** toàn bộ phép đo *(cổng ②, N1, ⑤, ⑨, ⑭, ⑮, ba đột biến)*
đọc mã **trên đĩa**, không qua ngăn nào. Đúng **một** lệnh chạm container
*(`printenv`, phát hiện Đ2)* — và Đ2 vẫn đứng vì hai ngăn kia build từ repo thật.
⟹ **Phép đo sạch. Lời dặn sai.**

---

---

<a id="su-co-ngan-xep"></a>

## 🔴 `fin05-po-test` KHÔNG mang mã đợt này — phát hiện chặn buổi tốn phí

**[ĐO Coder 25/08]** `docker inspect fin05-po-test-backend-1` → compose config file nằm
trong **scratchpad của một phiên KHÁC** (`17d3f149-…`), `build: context: .` trỏ vào
chính bản sao đó — **đông cứng lúc 24/08 22:04**, không phải `dev/learning-loop`. Băm
src/ bản đó `7636400be9c4` — **0 dòng nào của đợt "OTP trước token"** (④⑤⑦⑨⑫b, mọi cờ
`CONG_T0_BAT`/`CONG_OTP_NHOM_B_BAT`/`da_bi_otp_chan` đều KHÔNG có).

- 🔴 **BUỔI TỐN PHÍ DỪNG** — QA/QC đã báo dừng hẳn, không chạm ngăn này dưới bất kỳ
  hình thức nào cho tới khi có ngăn mới.
- **Coder trình 3 đường, không tự chọn:** (1) dựng ngăn MỚI từ repo thật, project
  name mới · (2) sửa `context:` của ngăn cũ trỏ về repo — **bị bác**, đó là file
  trong scratchpad phiên khác, sẽ tự mất, không phải vật của ta để sửa · (3) đo riêng
  ⑦ qua host (0 token) — chỉ đóng được ⑦, không đóng ⑥/⑬/⑨/⑫b.
  **[Lead 25/08] QUYẾT ĐỊNH: đường (1).** Buổi tốn phí cần UI thật cho 4 hạng mục,
  không chỉ ⑦.
- 🔴 **Cần soát lại:** mọi lần "PO tự kiểm độc lập" trong đợt này (④, ②…) nếu có lần
  nào gọi qua HTTP/UI sống của `fin05-po-test` (không phải git log/grep/script host)
  — kết quả lần đó không phản ánh mã đợt này. Đã hỏi PO tự soát.
- `fin05-final` cũng build từ cùng scratchpad phiên đó — **chưa kiểm, đừng dùng cho
  tới khi có xác nhận**.
- 🔴🔴 **[ĐO Coder 25/08, mở rộng hơn cả câu hỏi ban đầu] KHÔNG MỘT NGĂN NÀO ĐANG CHẠY
  MANG MÃ ĐỢT NÀY** — kể cả BA ngăn CHÍNH THỨC của dự án:
  ```
  fin05-final-backend-1      6722ab874767
  fin05-po-test-backend-1    7636400be9c4
  fin05-backend-1            6722ab874767   ← ngăn DEMO
  fin05do-backend-1          26b1bd3b1ff5   ← ngăn ĐO
  fin05ttl-backend-1         22ad74bdfa81
  cây làm việc THẬT          691dd9c40578
  ```
  Năm ngăn, bốn băm khác nhau, không cái nào khớp cây làm việc. **17 commit của đợt
  "OTP trước token" chỉ tồn tại trong git + cây làm việc, không hệ thống chạy nào có.**
  Vượt phạm vi buổi tốn phí — **đã báo PO riêng**, không phải việc Lead tự xử lý; có
  thể ảnh hưởng demo/đo lường ngoài đợt này. Xem tin Lead→PO.
- **Ngăn tạm cho buổi đo:** `fin05-dot-otp` (project mới, cổng 48443/48080/45432/46686,
  override trong scratchpad Coder, `context: .` build từ repo thật) — **[Lead 25/08]
  DUYỆT**, không cần compose thường trực trong repo cho một ngăn dùng một lần. Coder
  tự verify băm ảnh = `691dd9c40578` trước khi báo Lead mở buổi.
- ✅ **SẴN SÀNG, xác nhận bằng backend tự khai** (`GET /health` trong ngăn, không phải
  lời khai): `build_src_hash=691dd9c40578` = cây làm việc, `build_commit=a74059c` xuất
  thật (không rơi về "khong-ro"). 5/5 mã đợt này có mặt (`CONG_T0_BAT` ·
  `CONG_OTP_NHOM_B_BAT` · `HOI_SANG_LOC_LUA_DAO` · `_FS13_BAN_GIAO` · `da_bi_otp_chan`).
  6/6 container Up/healthy. Không ngăn nào khác bị khởi động lại (`StartedAt` kiểm).
  **Đường vào:** `https://localhost:48443` (UI/API) — 🔴 **PHẢI dùng `localhost`, KHÔNG
  `127.0.0.1`** (chứng chỉ Caddy cấp cho tên, IP làm TLS gãy, trông như ngăn chết) ·
  backend nghe cổng **8010**, không phải 8000. Jaeger `46686` · Postgres `127.0.0.1:45432`.
  ⚠️ **Giới hạn:** override sống trong scratchpad Coder — ngăn chạy được cả sau khi
  Coder đóng phiên, nhưng KHÔNG ai dựng lại được nó. Chấp nhận vì dùng một lần cho
  buổi hôm nay; đừng để nó sống quá buổi rồi ai đó tưởng dựng lại được.
  **Chờ PO tự verify băm lần hai (đã tuyên bố không nhận qua relay nữa) trước khi báo
  QA/QC chính thức mở.**
- 🔴 **Kho RAG rỗng — PO QUYẾT: KHÔNG nạp (không tốn tiền ⟹ không cần trình PO thật).**
  PO tự đo: `grep -c search_policy` trên cả `bo_ca_kich_ban_chuyen_gia.jsonl` lẫn
  `token-truoc-otp.spec.ts` = 0. Chỉ ⑥ Ca B là câu hỏi chính sách, nhưng assertion của
  nó CHỈ kiểm `duong !== "can_otp"` (đường đi), không kiểm nội dung ⟹ **kho rỗng không
  làm hỏng ca nào của buổi này.**
  - **BẮT BUỘC QA/QC ghi ĐẦU báo cáo buổi, TRƯỚC khi chạy** (nguyên văn PO):
    *"Kho RAG của ngăn này RỖNG (0 mục) — CÓ CHỦ ĐÍCH, không nạp vì 0/5 ca của buổi
    cần `search_policy`. TRỤC KHÔNG ĐO: chất lượng trả lời chính sách. Ca ⑥-B kiểm
    ĐƯỜNG ĐI, không kiểm nội dung. Câu trả lời chính sách trong transcript KHÔNG phải
    bằng chứng về gì cả — đừng đọc nó thành phát hiện."*
  - ⚠️ **Nếu Ca B đỏ:** phân biệt hai nguyên nhân TRƯỚC khi báo — ① cổng ④ bắn oan cho
    câu chính sách (phát hiện thật) hay ② kho rỗng làm `search_policy` NÉM LỖI thay vì
    trả rỗng (hỏng vì hạ tầng, không phải bug định tuyến). Đọc `ly_do_fallback` +
    `tool_calls` trước khi kết luận cổng ④ bắn oan.
  - **Sau buổi, không phải bây giờ:** kho rỗng ở ngăn mới là dữ kiện cho thiết kế dựng
    ảnh — PO đang chuyển cho DevOps (`p-226-b8`, vừa nhận việc).

---

---

<a id="doc-c"></a>

### 🔴 ⑩ Đọc C — Review đánh sập, **KHÔNG trình PO thật**

PO tự đề xuất Đọc C, tự giao Review đánh đối kháng **trước** khi trình. Kết quả: **thiết kế chưa
đủ chín, và cả cách PO đề xuất cứu nó cũng sai.** Năm chỗ, không chỗ nào là chi tiết vặt:

1. 🔴 **PO ví thì 1 với khuôn ⑫b *(`model=None`)* — SAI KHUÔN.** ⑫b dừng **TRƯỚC KHI** gọi model
   *(cổng tất định chặn từ đầu)*. Thì 1 **buộc phải** chạy ít nhất **một vòng model** — model phải
   tự đọc câu khách và tự quyết gọi `create_ticket(xac_nhan=False, …)`. **Không thể `model=None`.**
2. 🔴 **Tổng KHÔNG rẻ hơn — đắt hơn:**
   ```
   baseline (tạo vé 1 lượt)        ≈ 20.811
   Đọc C: lượt 1 (thì 1)           ≈ 10.381   ← CỘNG THÊM, không thay thế vòng nào
          lượt 2 (thì 2, tạo thật) ≈ 20.811+
                              TỔNG ≈ 31.200+   ⟹ +10.400/vé so với baseline
   ```
   PO nghi *"chỉ dời tiền sang lượt kế"* — **còn tệ hơn thế**: không dời, mà **cộng thêm**.
3. 🔴 **`TurnGuard` KHÔNG cứu được lỗ "model gọi thẳng `xac_nhan=True`".** [ĐO] TurnGuard tạo mới
   **mỗi lượt**, mà Đọc C tách thì 1/thì 2 thành **hai lượt chat**. TurnGuard **không có khái niệm
   "lượt trước"**. ⟹ cần **ràng buộc thứ NĂM** *(chưa có trong 4 cái Coder ghi)*: `xac_nhan=True`
   chỉ nhận khi có tín hiệu **"đã gửi tóm tắt khớp đúng 6 trường này"** ở lượt trước — dùng lại
   khuôn `thread_signals` của ⑨/T0, **băm 6 trường** làm giá trị, tự xoá sau khi dùng. Cùng một
   sửa này đóng luôn nhánh **"khách gật hai lần"**.
4. ⚠️ **"Thì 1 không để lại dấu vết" là phát biểu SAI.** Checkpointer LangGraph **vẫn** ghi tham số
   6 trường vào lịch sử hội thoại *(không phải rò rỉ mới — mọi câu chat đều thế)*. Phải viết đúng:
   *"không tạo **hồ sơ nghiệp vụ chính thức**, vẫn nằm trong lịch sử hội thoại như bình thường"*.
5. ❓ **"Kết thúc lượt ngay" CHƯA KIỂM ĐƯỢC.** Phụ thuộc `create_agent` *(LangChain prebuilt)* có
   hỗ trợ dừng ngay sau một tool hay không. Đường khả dĩ: cờ **`return_direct=True`** trên tool.
   🔴 **Nếu KHÔNG hỗ trợ ⟹ phải viết lại bằng `StateGraph` tuỳ biến = ĐỔI KIẾN TRÚC AGENT**, một
   hạng mục **khác hẳn độ lớn** so với những gì ⑩ đang mô tả. **Coder phải xác nhận trước.**

🔴 **VÀ CHỖ THIẾU LỚN NHẤT — không phải lỗ thiết kế, là DỮ KIỆN VẮNG:** mục tiêu gốc của ⑩ là
**giảm sai số liệu/tạo vé sai**, KHÔNG phải giảm token. Vậy phép so đúng **không** phải
`31,2k vs 20,8k`, mà là `31,2k đảm bảo` **vs** `20,8k + (X% × chi phí sửa sai)`.
**Không ai có X.** Chi phí sửa sai *(CSKH sửa tay, khách khiếu nại lần hai)* **có thật nhưng không
nằm trong `usage.jsonl`.**

⚠️ **Hai chữ "delta" KHÁC LOẠI — đừng lẫn khi viết ADR:** T2 *(⑨/⑫b)* đo **phình prompt** = chi
phí **CỐ ĐỊNH mọi lượt**, trần **261**. Con số +10.4k ở đây là chi phí **BIÊN theo SỰ KIỆN** *(chỉ
trả khi thật sự tạo vé)*. Người đọc sau sẽ tưởng 261 liên quan tới nó — **nó không.**

**⟹ QUYẾT: ⑩ KHÔNG trình PO thật trong phiên này.** Chặn cứng: hỏi PO chọn giữa `31,2k` và
`20,8k + X%` khi **không ai biết X** là đẩy một quyết định **không thể quyết** về phía PO.
Thứ tự đúng: **Coder xác nhận `return_direct` (0 token)** → nếu khả thi thì **đo X** → rồi mới ADR.

**#16 — ba phát hiện, và PO sai hai lần**

🟢 **CÔNG CỤ MỚI, GIÁ TRỊ VƯỢT RA NGOÀI ĐỢT NÀY — QA/QC mở:** đọc được **nguyên văn mọi hội
thoại đã lưu, 0 token**, không cần chạy lại, không cần model:
```python
# bảng Postgres `checkpoint_blobs`, cột `blob` (msgpack), channel "messages"
from langgraph.checkpoint.serde.jsonplus import JsonPlusSerializer
msgs = JsonPlusSerializer().loads_typed(("msgpack", blob))   # → HumanMessage/AIMessage thật
```
🔴 **Vì sao đây là chuyện lớn:** trước hôm nay, muốn biết agent **nói gì** ta phải **chạy lại và
trả tiền** — nên mọi tranh luận về hành vi đều bị chặn bởi ngân sách. Từ giờ **mọi lượt đã xảy ra
đều đọc lại được miễn phí.** Ca ⑬ suýt chết vì thiếu đúng thứ này.

✅ **CA ĐỐI CHỨNG — đóng, không phải phát hiện.** Lượt UI thật `USR-0145`, `so_tool_call=0`:
```
Khách: "tôi bị trừ tiền"
Agent: "…Để mình tra giúp bạn ngay nhé.  Bạn cho mình biết số tiền bị trừ là bao nhiêu được không ạ?"
```
Agent **hỏi lại**, dùng **thì ý định** *("sẽ tra")* — **không** tuyên bố đã tra. `tool_call=0` ở
đây là **ĐÚNG đặc tả**.
⟹ Ca này làm **nổi bật** B1/C1 chứ không làm nhẹ đi: agent **biết** cách hỏi lại khi thiếu thông
tin. B1/C1 là **lệch khỏi hành vi chuẩn của chính nó**, không phải giới hạn chung của model.
🔴 **Và nó xác lập ranh giới của phát hiện:** thứ vi phạm **không phải `tool_call=0`** — mà là
**`tool_call=0` KÈM lời khẳng định ĐÃ tra**. Bỏ vế sau thì không còn phát hiện nào.

🔴 **PO SAI HAI LẦN LIÊN TIẾP TRONG MỘT GIỜ — niêm, vì cả hai đều nghe rất chặt:**
| # | PO lập luận | thứ bác nó | mất gì |
|---|---|---|---|
| 1 | *"bản ghi có `usage` rỗng ⟹ dụng cụ mù ⟹ `tool_calls: []` vô nghĩa"* | bản ghi **không hề có khoá `usage`** — thiếu khoá, không phải rỗng | bác nhầm một phát hiện **đúng**, bắt QA/QC sửa biên bản **2 lần** |
| 2 | *"14/08 ghi 40/40, 25/08 ghi 0/4 ⟹ hồi quy ⟹ P0"* | sổ server: `tool_call=1` **hai lần hôm nay** | gác việc cả đội ~20 phút |
⟹ **Luật Đ″: kết luận nào của PO không kèm SỐ THÔ thì đội được quyền đòi số trước khi làm theo.**
Áp cho **mọi** vai, **kể cả PO** — nhất là PO, vì lời PO không ai chặn.

🔴 **LUẬT Đ‴ — TUYỆT ĐỐI KHÔNG `git add`. LẦN THỨ HAI CÙNG MỘT CÁI BẪY.**
Luật cũ *"luôn `git commit -- <pathspec>`"* **chưa đủ**, và đây là chứng minh: PO chạy
`git add -- <checklist>`, **lệnh commit ngay sau đó HỎNG** *(sai thứ tự cờ: `-m` phải đứng
TRƯỚC `--`)*. Tệp nằm lại trong chỉ mục. Vài giây sau QA/QC commit ⟹ **83 dòng của PO bị cuốn
trọn vào `97ebe31`**, một commit có thông điệp chỉ nói về ⑦.

**Không mất nội dung — mất TRUY VẾT.** Ba luật Đ/Đ′/Đ″ ở trên nay nằm dưới một tiêu đề không hề
nhắc tới chúng. Ai tra `git log` tìm nguồn của Luật Đ′ sẽ **không thấy gì**.

⟹ **Luật đúng: `git commit -m "..." -- <pathspec>` là MỘT lệnh, KHÔNG bao giờ tách `git add` ra
trước.** `git commit -- <pathspec>` **không cần** chỉ mục — thêm `git add` chỉ tạo ra một **cửa
sổ sống** mà lệnh hỏng sẽ để mở vô thời hạn. 🔴 **Chỉ mục là TRẠNG THÁI DÙNG CHUNG của 5+ phiên:
mọi thứ bạn `add` đều thuộc về người commit kế tiếp, bất kể đó là ai.**

---

---
