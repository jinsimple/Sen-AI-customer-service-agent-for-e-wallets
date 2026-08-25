# DỰ THẢO — PO thu hẹp phạm vi 25/08, chưa thi hành

> **Bối cảnh landing:** PO thật quyết 25/08 (qua PO agent) rằng đợt "OTP trước token"
> KHÔNG làm loại khiếu nại thứ năm đầy đủ (không đổi `contracts/`, không migration,
> không 7 bước) — chỉ cần nối FS-13 với `request_human_handoff` đã có sẵn (xem
> `docs/giao-viec/CHECKLIST-dot-otp-truoc-token.md` mục ⑫b). Bản dự thảo ADR-050 dưới
> đây (Coder soạn, dừng đúng bước 3, có phân tích tốt về đường tư vấn khác nhau/chuyển
> loại một chiều/SLA không tính lại/audit trail) **KHÔNG thi hành trong đợt này** —
> giữ lại nguyên văn cho đợt sau, theo CLAUDE.md §7b (chuyển chỗ, không xoá).
>
> **Lead land theo yêu cầu Coder** (file gốc nằm trong scratchpad phiên của họ, sẽ mất
> khi phiên đóng) — không sửa nội dung, chỉ thêm khối giới thiệu này.

---

## ADR-050 — Loại khiếu nại thứ năm: `authorized_scam` (khách BỊ DỤ tự chuyển tiền)

**Ngày:** 2026-08-25 · **Trạng thái:** 🟡 **DỰ THẢO — CHỜ PO THẬT DUYỆT. Chưa chạm
`contracts/`, chưa chạm mã, chưa migration.**
*(Coder `p-226-63` soạn theo §3 bước 3, dừng đúng bước 4. Nguồn: Q4=A do PO thật chốt
24/08 · `docs/kich-ban-chuyen-gia-cskh-chuyen-nham-tien.md` Nhánh A · ADR-048 FS-13.)*

### Bối cảnh — [ĐO] `src/db/models.py:199`

```
ck_complaints_type: type IN ('wrong_recipient','money_not_received',
                             'double_charge','refund','other')
```

Không có ô cho ca **bị lừa**. Chuyên gia CSKH xếp đây là **rủi ro nghiệp vụ lớn nhất
hiện tại**: bot ép ca lừa đảo vào `wrong_recipient` rồi khuyên *"chờ bộ phận nghiệp vụ
liên hệ người nhận"* — vô nghĩa khi người nhận **là đối tượng lừa**, và tiêu mất **giờ
vàng trình báo**.

`other` KHÔNG dùng thay được: nó nghĩa là *"chưa khớp loại nào"* (CTRL-001), tức
**thiếu thông tin**. Ca lừa đảo là ca **ĐÃ BIẾT RÕ**, và biết rõ theo một hướng đòi
đường xử lý **ngược hẳn** `wrong_recipient`. Gộp hai thứ ấy vào một ô là làm CSKH
không phân biệt được "chưa biết" với "biết là nguy".

### QĐ1 — Tên loại: `authorized_scam`

Tiếng Việt trong giao diện: **"bị lừa chuyển tiền (khách tự thao tác)"**.

> 🔴 **NIÊM TẠI CHỖ ĐỊNH NGHĨA — hai vế, phải đọc cùng nhau.**
> **Vế 1:** chọn tên khớp thuật ngữ chuẩn ngành (APP fraud) **KHÔNG** kéo theo chế
> độ hoàn tiền của quy định Anh/EU. Chế độ ấy chưa áp cho VN; ADR này không tạo ra
> quyền hoàn tiền nào.
> **Vế 2 (PO thêm 25/08):** nhưng vì nó LÀ thuật ngữ chuẩn, người đọc sau — đối tác
> ví, người soát tuân thủ, kiểm toán — **SẼ mang theo kỳ vọng của chuẩn ấy**. Ai
> trích giá trị `authorized_scam` ra khỏi hệ này phải trích kèm câu vế 1. Một cái
> tên mượn uy tín của chuẩn thì cũng mượn cả kỳ vọng của chuẩn.

**Vì sao tên này, không phải `scam`/`fraud`/`bi_lua`:**
- `fraud` ĐÃ CÓ NGHĨA KHÁC trong hệ này — `complaints.fraud_signals`, `fraud_policy.py`,
  FS-xx là **tín hiệu định tuyến về TÀI KHOẢN**, không phải phân loại khiếu nại. Dùng lại
  chữ `fraud` cho một trục khác là mời người sau đọc nhầm hai thứ thành một, đúng thứ
  contract đã phải tách bạch giữa `fraud` và `tin_hieu_cam_xuc`.
- `authorized_` mang đúng dữ kiện phân biệt: **khách TỰ bấm chuyển**, giao dịch hợp lệ về
  kỹ thuật. Đây là chỗ nó khác `wrong_recipient` (bấm nhầm) và khác gian lận tài khoản
  (kẻ khác bấm).
- Đây là thuật ngữ chuẩn ngành quốc tế: **APP fraud — Authorized Push Payment**. Anh/EU
  đã có chế độ hoàn tiền riêng cho đúng nhóm này. Chọn tên khớp thuật ngữ chuẩn để sau
  này đối chiếu quy định không phải dịch lại. 🔴 **NIÊM: chọn TÊN, KHÔNG kéo theo nghĩa
  vụ hoàn tiền của quy định Anh/EU** — chế độ ấy chưa áp cho VN và ADR này KHÔNG tạo ra
  bất kỳ quyền hoàn tiền nào.

### QĐ2 — Vòng đời: KHÔNG có trạng thái mới. Khác `wrong_recipient` ở TƯ VẤN, không ở máy trạng thái.

Đường đi HITL giữ nguyên tuyệt đối: `draft|pending_approval → approved|rejected`, cửa
duy nhất vẫn là `POST /resolutions/{id}/approve`, vẫn chỉ `supervisor`, vẫn OTP step-up
+ `amount_snapshot`. **ADR này KHÔNG thêm một đường nào chạm tiền** (ràng buộc cứng 1).

Bốn khác biệt, đều ở tầng TƯ VẤN và ĐỊNH TUYẾN:

| | `wrong_recipient` | `authorized_scam` |
|---|---|---|
| liên hệ người nhận | có — bộ phận nghiệp vụ chủ động liên hệ | 🔴 **CẤM tư vấn**, và **cảnh báo khách không tự liên hệ lại** |
| trình báo công an | không nêu | **hướng dẫn NGAY**, nhấn mạnh yếu tố thời gian |
| `priority` | theo luật hiện hành | nâng, **trần `high`** — `critical` vẫn dành riêng FS-06 |
| chuyển người thật | theo hàng đợi | **sớm**, ưu tiên |

🔴 **Ràng buộc cứng 5 giữ nguyên:** loại này **KHÔNG** nối tới khoá ví. Tính năng khoá ví
không tồn tại, và ADR này không tạo ra nó.
🔴 **ADR-022 giữ nguyên:** model **không bao giờ** thấy mã tín hiệu. Câu cảnh báo
*"đừng liên hệ lại đối tượng"* phải là **dòng TẤT ĐỊNH** chèn sau khi tool trả về —
cùng cơ chế ⑧ đã dựng (`_them_canh_bao_mao_danh`), không giao model tự diễn đạt.

### QĐ3 — Thẩm quyền

| ai | được làm gì |
|---|---|
| AI | **được** truyền `complaint_type="authorized_scam"` khi tạo vé — **CHỈ** khi khách trả lời RÕ RÀNG câu sàng lọc ⑨. Không suy đoán. |
| tầng service | **được NÂNG** `wrong_recipient → authorized_scam` khi FS-13 bật (`complaint_intake.py`) — cùng chỗ mọi tín hiệu khác đã sống. **KHÔNG do AI gọi** (ràng buộc cứng 2). |
| `cskh` | **được đổi loại** sau khi điều tra. Điều tra là việc của họ; đây không phải hành động chạm tiền. |
| `supervisor` | kế thừa quyền `cskh`. Thẩm quyền duyệt tiền **KHÔNG đổi một chữ**. |
| `partner_admin` | không chạm. |

### QĐ4 🔴 — Ca đang là `wrong_recipient` mà hoá ra lừa đảo thì chuyển thế nào

Đây là câu Lead nêu là bắt buộc, và là câu duy nhất có bẫy thật.

1. **CHỈ MỘT CHIỀU:** `wrong_recipient → authorized_scam`. Chiều ngược **không tự động
   bao giờ**. Lý do bất đối xứng: đọc nhầm lừa-đảo thành nhầm-lẫn làm khách **mất giờ
   vàng trình báo**; đọc nhầm chiều kia chỉ làm khách nhận một cảnh báo thừa.
2. **`other → authorized_scam` được.** Mọi chiều khác phải do người quyết, ghi tay.
3. 🔴 **SLA KHÔNG TÍNH LẠI.** Mốc vẫn là **ngày TIẾP NHẬN đầu tiên** — thi hành đúng
   ADR-047 (thời hạn tra soát đếm từ ngày tiếp nhận, TT 15/2024/TT-NHNN). Đổi loại mà
   reset đồng hồ là dùng một bản vá nghiệp vụ để **rút ngắn quyền của khách**.
4. **Đổi loại phải để lại dấu.** `complaints.type` là một cột — UPDATE xong thì giá trị
   cũ biến mất, và hồ sơ khiếu nại tài chính không được phép mất lịch sử phân loại.
   🔴 **Đây là chỗ ADR này CHẠM VÀO MỘT LỖ ĐÃ BIẾT:** hệ thống **không có bảng audit
   log bất biến** (đo 24/08: 16 bảng, không bảng nào là audit; vết đi qua
   `logging.getLogger("fin05.access")` ra stdout). Ba đường, PO chọn:
   - **(a′)** MỘT cột JSON **chỉ-ghi-thêm** trên `complaints` (`lich_su_doi_loai`),
     mỗi mục: loại cũ · loại mới · lúc nào · ai · căn cứ. Cùng một migration, cùng
     một bảng với phương án 3-cột — nhưng KHÔNG mang giới hạn *"chỉ đủ một lần
     đổi"*. Mà QĐ3 cho `cskh` đổi loại sau điều tra, tức **>1 lần là có thật**,
     nên 3 cột cố định sai ngay từ ngày đầu. *(PO sửa 25/08 — bản đầu của tôi đề
     nghị 3 cột và tự khai giới hạn ấy như một đánh đổi chấp nhận được; nó không
     phải đánh đổi, nó là một lỗi thiết kế mà cùng chi phí có thể tránh.)*
   - **(b)** ghi vào `investigation_logs` — tái dùng cơ chế có sẵn, nhưng bảng đó đang
     mang `tool_input_json` **plaintext** (finding bảo mật ADR-034 ③ chưa vá).
   - **(c)** dựng bảng audit thật — đúng nhất, **vượt phạm vi đợt này**, và là một
     trong bốn P0 Coder đã trình ở bản soát xét 24/08.
   ⟹ **Đề nghị (a′) cho MVP**, ghi (c) vào sổ nợ. KHÔNG đề nghị (b): đưa thêm dữ liệu
   vào một bảng đang có finding chưa vá là làm lỗ rộng ra, và **tệ hơn — nó sẽ TRÔNG
   như đã có audit**.

   🔴 **PHẢI ĐỌC KÈM (a′), nếu không câu này sẽ bị đọc thành thứ nó không phải:**
   (a′) cho **LỊCH SỬ**, **KHÔNG** cho **TOÀN VẸN**. Không hash-chain, không chống
   sửa, không tách quyền ghi. Bất kỳ ai ghi được DB vẫn sửa được chính cột lịch sử
   ấy — kể cả xoá sạch. Đây là *"biết đã từng đổi"*, không phải *"chứng minh được
   trước bên thứ ba rằng không ai sửa"*. Nghĩa vụ audit thật của một ví điện tử vẫn
   nằm ở (c), và (c) **chưa tồn tại**.

### QĐ5 — 🟡 CÂU MỞ, KHAI RA CHỨ KHÔNG ĐỂ TRỐNG: khách đã nghe lời khuyên CŨ

*(PO bắt 25/08. Bản đầu của tôi thiếu hẳn mục này.)*

Ca đang là `wrong_recipient` **đã được tư vấn** *"bộ phận nghiệp vụ sẽ chủ động liên
hệ người nhận"* — quy trình PO xác nhận CÓ THẬT 24/08. Rồi ca ấy đổi sang
`authorized_scam`, nơi lời khuyên đúng là **ngược lại**: tuyệt đối không liên hệ đối
tượng, đi trình báo ngay.

🔴 **Lời khuyên cũ đã ra khỏi miệng rồi.** Đổi một giá trị trong DB không thu hồi được
thứ khách đã đọc. Nếu không ai đính chính, khách cầm **hai lời khuyên ngược nhau** và
sẽ làm theo cái họ nghe trước — cái nguy hiểm hơn.

**Ba câu ADR này KHÔNG tự trả lời** (thuộc quy trình CSKH, không thuộc kỹ thuật):
1. Ai đính chính — hệ thống tự nhắn, hay CSKH gọi lại?
2. Trong bao lâu kể từ lúc đổi loại?
3. Nếu khách **đã** liên hệ đối tượng trước khi được đính chính thì ghi nhận thế nào
   (đó là dữ kiện điều tra, và có thể là thời điểm khách bị lừa lần hai)?

**Ràng buộc kỹ thuật tôi khẳng định được ngay, không cần chờ ba câu trên:** việc đổi
loại **PHẢI** ghi lại mốc thời gian (đã có trong (a′)), vì không có mốc thì không ai
trả lời được câu 2 và câu 3 sau này.

### Hệ quả nếu PO duyệt (bước 5–7, CHƯA làm)
- `contracts/resolution-state-machine.yaml` + `contracts/agent-tools.yaml` (`ghi_chu`
  `complaint_type` của `create_ticket` đang khai "1 trong 4")
- `check_contracts.py --update` · `CONTRACT_VERSION` · commit **KÈM baseline**
- migration: `ck_complaints_type` thêm giá trị + 3 cột QĐ4(a)
- **Đơn hàng token: QĐ2 = 0.** [PO sửa 25/08, và sửa đúng] Tôi viết *"QĐ2 thêm chữ
  vào prompt, có thể không vừa"* — **mâu thuẫn với chính QĐ2**, nơi tôi đã ràng buộc
  câu cảnh báo phải là **dòng TẤT ĐỊNH chèn sau khi tool trả về** (cơ chế ⑧, đo được
  delta = 0). Model không bao giờ thấy câu đó. Tôi tự đặt ra ràng buộc rồi lo về một
  chi phí mà chính ràng buộc ấy đã loại bỏ.
  ⟹ **293 token còn lại KHÔNG phải chia cho ADR này.** Nó thuộc về ⑨ (PO đã quyết:
  ⑨ được 293, ⑪ hoãn sang đợt cắt prompt).

### Câu ADR này CỐ Ý KHÔNG trả lời
Khách bị lừa **có được hoàn tiền không**, và ai chịu. Đó là **chính sách công ty +
pháp lý**, không phải kỹ thuật — và nó là đúng loại câu mà một ADR kỹ thuật trả lời hộ
thì sẽ thành tiền lệ không ai định ra. ADR này chỉ mở **ô phân loại** và **đường tư
vấn**. Quyền hoàn tiền vẫn đi qua đúng cửa HITL cũ, không hơn một chữ.
