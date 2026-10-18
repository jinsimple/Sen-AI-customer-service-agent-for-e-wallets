# Đợt "OTP trước token" — phiếu giao việc

> **Người giao:** phiên PO · **Người nhận:** Lead · **Ngày:** 24/08/2026
> **Nền đo:** HEAD `a3bc860` · băm luật `triage.py` = `abec4358a501` (md5-toan-file-12)
> **Đặc tả nghiệp vụ:** `docs/kich-ban-chuyen-gia-cskh-chuyen-nham-tien.md`
>
> **PO thật đã duyệt toàn bộ bản này ngày 24/08.** Bốn câu Q1–Q4 đã chốt, không hỏi lại.

---

## 0. Đọc trước khi làm gì

Ba tài liệu, theo thứ tự: `CLAUDE.md` → file này → `docs/kich-ban-chuyen-gia-cskh-chuyen-nham-tien.md`.

🔴 **`docs/STATE.md` đã cũ.** Nó tự niêm là cũ 6 ngày tính từ 24/08. Mục nào ghi "chờ PO"
mà không có dấu 24/08 thì đối chiếu `docs/DECISIONS.md` trước khi tin.

🔴 **`project-knowledge/` cũ 130 commit** (chụp tại `2a787bb`, HEAD nay `a3bc860`); hash
`agent-tools.yaml` đã đổi. Việc L0 dưới đây xử lý.

---

## 1. Bài toán, một đoạn

Một hội thoại khiếu nại đang tiêu **một lượt LLM thừa**: lượt nằm giữa lúc khách kể vấn
đề và lúc xác thực OTP. Lượt đó không mang thông tin nào cho vé CSKH — nó chỉ để model
tự khám phá ra rằng khách chưa OTP, một sự thật mà tầng tất định **đã biết trước**
(`otp_verified_at` truyền vào `run_agent_turn`, `src/agents/graph.py:798`).

`src/agents/tools/customer_tools.py:620-629` tự khai lượt này là chế độ livelock:
**8 tool call · 46 giây · 49.700–71.600 token · sổ ghi `total_tokens = 0`.**

**Bất biến của đợt:** *không lượt nào được tốn token trước khi OTP xác thực xong.*

Đo được vì envelope `/agent/chat` trả nguyên `duong` và `usage.total_tokens` ra tới trình
duyệt (`src/api/main.py` trả thẳng dict của `run_agent_turn`).

---

## 2. Bốn quyết định PO đã chốt — KHÔNG hỏi lại

| | quyết định |
|---|---|
| **Q1** | Đòi OTP ở tầng tất định **chỉ áp cho khiếu nại cá nhân (NHÓM B)**. Câu hỏi chính sách KHÔNG bị chặn OTP — `search_policy` vốn đã được miễn OTP. |
| **Q2** | Cổng sau OTP hỏi **thời gian + số tiền trong MỘT tin**. **Bỏ mã giao dịch khỏi câu hỏi** (vẫn nhận diện nếu khách tự nêu). |
| **Q3** | Hai ca adversarial xanh giả ⟹ **vá cổng**, không sửa ca test. |
| **Q4** | **Thêm loại khiếu nại thứ năm cho ca lừa đảo**, có đường xử lý riêng. Đi đủ 7 bước đổi contract. |

🟢 **Dữ kiện PO xác nhận, dùng được ngay:** quy trình *"bộ phận nghiệp vụ chủ động liên hệ
người nhận"* là **CÓ THẬT**. Bot được phép hứa điều này — không phải lời hứa bịa. Không
phiên nào cần hỏi lại.

### 2b. Q2 không lật ADR chốt 24/08 — đọc kỹ chỗ này

ADR ấy nói *"slot bắt buộc duy nhất là số tiền; thời gian **không bao giờ một mình** là lý
do hỏi."* Chuyên gia hỏi thời gian **đi kèm** số tiền, không thay thế. Hai điều tương
thích — **ADR đứng nguyên, không cần ADR thay thế.**

Thứ cần sửa là **cách R1 đang được thi hành**: đội đọc R1 thành *"một YÊU CẦU mỗi tin"* và
đã xoá `HOI_THIEU_CA_HAI`. Chuyên gia nói R1 thật là **"một Ý mỗi tin"**. Chặt hơn một
nấc — và chính nấc đó tạo ra cổng hỏi-số-tiền đứng cô lập mà Đ1 cho thấy bắn oan 6/11 lần.

---

## 3. Bốn khiếm khuyết đo được (Đ) + bốn phát hiện từ kịch bản (K)

| mã | nội dung | bằng chứng |
|---|---|---|
| **Đ1** | Cổng `thu_slot` bắn oan **6/11** lần: 2 câu chính sách · 2 ca adversarial · 1 lượt sau khi đã phân loại · 1 ca khách cần hướng dẫn. Nguyên nhân: `"nhầm"`, `"bị"` trần trong `_TIN_HIEU_KHIEU_NAI`; `"nhận"` khớp trong "xác nhận" | chạy `phan_luong()` trên `eval/*.jsonl` |
| | 🔴 **Hệ quả nặng nhất:** `ADV-036` (ép lộ tên+STK người nhận) và `ADV-038` (ép kết luận gian lận) đang **XANH** vì cổng trả câu lạc đề — request không chạm LLM, không qua O1–O5. Khuôn cấm không khớp câu "cho mình xin số tiền" ⟹ đạt. **Hai lớp phòng thủ chưa từng được chạy** | `eval/_harness.py:555` gọi `run_agent_turn` |
| **Đ2** | Eval và sản phẩm chạy **hai cấu hình cờ khác nhau**: 3/3 container có `TRIAGE_ENABLED=1`; host — nơi eval bắt buộc chạy — **không đặt**; không tệp eval nào khai cờ | `printenv` từng container · `env` host |
| **Đ3** | Cổng T0 hỏi lại thứ khách vừa nói **2/8**: `"tuần trước"`, `"khoảng 3 giờ chiều"` không được khuôn thời gian nhận diện — dù chính câu hỏi của T0 dạy khách trả lời "sáng/chiều/tối" | `co_ma_giao_dich_hoac_thoi_gian()` |
| **Đ4** | T0 chạy trước T1 và **độc lập** `TRIAGE_ENABLED`. Tắt cờ chữa cháy thì T0 vẫn chạy, không tín hiệu nào báo | `graph.py:839` · Review nêu 24/08 |
| **K1** | 🔴 **Taxonomy không có ô cho lừa đảo.** `CHECK` chỉ có `wrong_recipient/money_not_received/double_charge/refund/other`. Bot ép ca lừa đảo vào `wrong_recipient` rồi khuyên "chờ liên hệ người nhận" — vô nghĩa khi người nhận là kẻ lừa, và tiêu mất giờ vàng trình báo | `src/db/models.py:199` |
| **K2** | Không chỗ nào **bắt bot HỎI** câu sàng lọc lừa đảo. FS-13 cho chỗ *ghi nhận* tín hiệu; thiếu chỗ bắt bot *đi lấy* | ADR-048 |
| **K3** | Hai câu chống mạo danh CSKH **chưa có câu nào**. Dự án ép rất chặt việc bot *không hỏi* OTP giao dịch; chưa ai nghĩ tới việc bot **nói cho khách biết** nó sẽ không bao giờ hỏi | grep toàn `src/` |
| **K4** | Lượt 7 kịch bản cho A2 một đặc tả lần đầu: **6 trường cố định**. Danh sách cố định ⟹ **dựng tất định được** — khác hẳn dặn model "hãy xác nhận", thứ đã đỏ 6 vòng | `docs/STATE.md` §5 24/08 |

---

## 4. Mười ba hạng mục — thứ tự và ràng buộc

```
L0  ──► ①  ──► ②  ──► ③        (ca đối chứng ĐỎ trước, rồi mới vá)
                  ──► ④ ──► ⑤ ──► ⑥
    ──► ⑦  ⑧  ⑨  ⑬             (song song, không chặn ai)
    ──► ⑩  ──► ⑪
    ──► ⑫  (ADR trước, PO duyệt, rồi mới mã)
```

| # | hạng mục | vai | ràng buộc |
|---|---|---|---|
| **L0** | Xuất lại `project-knowledge/`; thu ACK cả 4 vai đã đọc bản mới | Lead | **trước mọi việc** |
| ① | Ghim cờ định tuyến vào phép đo — in `TRIAGE_ENABLED` + cột `duong` vào báo cáo eval | QA/QC | trước mọi phép đo khác |
| ② | Bộ ca đối chứng **ÂM** cho cổng `thu_slot` | QA/QC | **phải ĐỎ trên `a3bc860`** trước ③ |
| ③ | Siết ba từ — đóng Đ1 + Q3 | Coder | sau ② |
| ④ | Cổng OTP tất định cho NHÓM B — Q1 | Coder | — |
| ⑤ | Cổng sau OTP hỏi **thời gian + số tiền một tin**; sửa cách thi hành R1 thành "một Ý mỗi tin" — Q2 | Coder | sau ④ |
| ⑥ | Ca E2E trên UI cho bất biến "0 token trước OTP" | QA/QC | sau ④⑤ |
| ⑦ | Khuôn thời gian (Đ3) + kill-switch riêng T0 (Đ4) | Coder | song song |
| ⑧ | **K3 — hai câu chống mạo danh**, hằng số, 0 token | Coder | song song · **rẻ nhất, giá trị cao nhất** |
| ⑨ | **K2 — bắt buộc hỏi câu sàng lọc lừa đảo** ở mọi ca chuyển nhầm | Coder | ca đối chứng QA/QC dựng trước |
| ⑩ | **K4 — bản tóm tắt 6 trường tất định** trước `create_ticket` | Coder | gắn ADR-049 |
| ⑪ | Ép cấu trúc lượt 5 (ba vế) + đổi góc nhìn lượt 6 + đọc lại 5 dữ kiện lượt 3 | Coder | sau ⑨⑩ |
| ⑫ | **K1 — loại khiếu nại lừa đảo** (Q4=A) | Coder | 🔒 **ADR trước, PO duyệt, rồi mới mã** |
| ⑬ | Bộ ca đánh giá dựng từ kịch bản chuyên gia — 8 lượt + 3 nhánh | QA/QC | song song |

---

## 5. Phiếu từng vai

### 5.1 Lead — điều phối, **không viết mã**

**Vùng ghi:** `docs/giao-viec/`, `docs/STATE.md`

- **L0 trước mọi việc.** `python3 scripts/export_project_knowledge.py`, thay thư mục, rồi
  **thu ACK bằng chữ** của cả bốn vai. Theo **Luật U**, chưa có ACK thì việc chưa tồn tại.
- Giữ **thứ tự cứng** ở §4. Đặc biệt: ② phải ĐỎ trước khi ③ khởi động.
- **Cổng chặn duy nhất còn lại:** ⑫ — Coder chỉ được đi tới bước 3 (ghi ADR) rồi **DỪNG**,
  trình PO. Không ai được chạm `contracts/` hay migration trước khi ADR được duyệt.
- **Luật X:** con số nào vai khác báo mà không kèm đường dẫn + cách dựng lại ⟹ ghi
  *"nghe báo, chưa có vật chứng"*. Không relay con số trần lên PO.
- **Luật I + pathspec:** mọi lệnh `git` phải có pathspec — cây làm việc dùng chung, đã có
  3 sự cố. Cân nhắc worktree riêng cho từng vai.
- **Không tự vá `src/` hay `tests/` cho nhanh.** Lead viết mã là Lead mất vai kiểm.

### 5.2 QA/QC — đối kháng, **KHÔNG đọc `src/`**

**Vùng ghi:** `tests/`, `frontend/e2e/`, `eval/`

> 🔴 **Bạn nhận ĐẶC TẢ và LÝ LẼ, không nhận nội dung test.** Phiên PO đã viết sẵn một file
> test cho ⑥ rồi **gỡ bỏ** — đó đúng cơ chế `STATE.md §5.D1` ghi PO-agent từng từ chối:
> test soạn hộ sẽ *phản chiếu* code, kể cả code sai. Bạn tự dựng, từ đặc tả và từ quan sát
> hộp đen (gọi API thật, liệt kê collection từ container đang chạy, đọc contract, gõ UI).

**① Ghim cờ.** Báo cáo eval in `TRIAGE_ENABLED` lúc chạy + một cột `duong` cho mỗi ca.
*Xong khi:* đọc được câu *"ca này đi `thu_slot`, không chạm model"* **mà không phải mở code**.

**② Ca âm cho cổng `thu_slot`.** Mỗi trục ≥1 ca, kỳ vọng **không** đi `thu_slot`:
câu hỏi chính sách · câu ép lộ thông tin bên thứ ba · câu ép kết luận gian lận · lượt sau
khi agent đã phân loại · câu khách cần hướng dẫn (người lớn tuổi, không rành công nghệ).
Kèm ca **dương** giữ nguyên: khiếu nại thật thiếu số tiền.
*Xong khi:* bộ ca **ĐỎ trên HEAD `a3bc860`**, báo số ca đỏ và tên từng ca. Luật A đòi cả
hai vế — cổng phải IM lúc bình thường **và** KÊU lúc bất thường.

**⑥ Ca E2E trên UI.** Bất biến: *không lượt nào tốn token trước mốc OTP*.
- Đo trên envelope `/agent/chat` — nó mang `duong` và `usage.total_tokens` ra tới trình duyệt
- **Ba trạng thái, không phải hai:** `0` ≠ `null` ≠ `>0`. Gộp `null` vào `0` làm một envelope
  hỏng trông y hệt một lượt 0 token ⟹ ca xanh vì đúng lý do sai
- 🔴 **Cạm bẫy đắt nhất:** cổng chỉ bắn **một lần mỗi hội thoại**. Ca thứ hai trong cùng cửa
  sổ chat cho kết quả sai và **trông như đã vá**. Mỗi ca một hội thoại mới
- Ngăn để gõ: `fin05-po-test` (`127.0.0.1:38443`)

**⑬ Bộ ca từ kịch bản chuyên gia.** Nguồn: `docs/kich-ban-chuyen-gia-cskh-chuyen-nham-tien.md`.
Trục bắt buộc:
- **Nhánh A** — khách trả lời *"có người gọi hướng dẫn tôi chuyển"* ⟹ kỳ vọng bot **không**
  tư vấn liên hệ người nhận, và **có** hướng dẫn trình báo
- **Nhánh B** — nhiều GD khớp ⟹ bot **không tự chọn**, và câu hỏi lại phải **đổi trục**
- **Nhánh C** — hai lần hỏi hai trục vẫn không ra ⟹ phải có chữ *"chưa tra được"*, **không**
  có giao dịch "có vẻ giống"
- 🔴 **Trục dễ trượt nhất:** ca chuyển nhầm **trông rõ ràng** — kiểm bot **có hỏi** câu sàng
  lọc lừa đảo không. Chuyên gia nói phải hỏi ở *mọi* ca, nên chính ca rõ ràng mới là ca bot
  hay bỏ qua

**Hoá đơn:** ⑥ và một phần ⑬ gọi model thật. Khai trước, đừng để lẫn vào cổng thường trực.

### 5.3 Coder — **vai duy nhất chạm `src/`**

**Vùng ghi:** `src/`, `frontend/src/`, `migrations/`, `contracts/` *(chỉ sau khi PO duyệt ADR)*

**③ Siết ba từ.** Gỡ `"nhầm"` và `"bị"` trần khỏi `_TIN_HIEU_KHIEU_NAI`; đổi `"nhận"` trong
`_DONG_TU_GD` thành cụm đủ dài (`"chưa nhận"`/`"không nhận"` đã có sẵn). Giữ nguyên mọi thứ khác.
> 🔴 **CẤM thêm danh sách từ loại trừ** ("chính sách", "quy định", "thủ tục"…). Chú thích
> trong chính tệp đã ghi lý do: *danh sách loại trừ luôn thiếu một chữ*. Siết điều kiện **vào**.
> **Đánh đổi phải khai khi land:** *"tôi chuyển nhầm cho người lạ"* không còn kích cổng ⟹ đi
> LLM ⟹ tốn token, nhưng khách được xoa dịu đúng luật prompt. Đúng hướng module tự khai.

**④⑤ Cổng OTP + cổng sau OTP.** `otp_verified_at` đã có sẵn ở `run_agent_turn` — không cần
thêm đường dẫn dữ liệu nào. Cổng sau OTP hỏi **thời gian + số tiền một tin**, bỏ mã GD khỏi
câu hỏi.

**⑦** Bổ sung khuôn thời gian cho `"tuần trước"` và `"<số> giờ sáng/chiều/tối"`. Cờ riêng cho
T0. *Xong khi:* tắt cả hai cờ ⟹ mọi lượt `duong=day_du` trong sổ — đo bằng sổ, không đọc code.

**⑧ Hai câu hằng số K3.** Không gọi model.
- Câu lượt 1, gắn vào cổng OTP: *"đây là mã xác thực phiên hỗ trợ, không phải mã OTP giao
  dịch — em không bao giờ hỏi mã OTP giao dịch hay mật khẩu của chị"*
- Câu lượt 8, gắn vào lượt báo mã hồ sơ: *"sẽ không có ai từ ví gọi điện yêu cầu chị chuyển
  tiền, cung cấp mật khẩu hay mã OTP để lấy lại tiền"*

**⑨ Câu sàng lọc lừa đảo.** Hỏi **sự kiện khách quan** (*"có ai nhắn tin hoặc gọi điện hướng
dẫn chị chuyển khoản lần này không"*), **KHÔNG** hỏi kết luận (*"chị có bị lừa không"*).
Khung mở bắt buộc: *"em hỏi thêm một ý để hỗ trợ chị đúng hướng"* — khách thấy bị nghi ngờ
sẽ đóng lại.

**⑩ Bản tóm tắt 6 trường cố định** trước `create_ticket`: loại · phạm vi · mã+giờ+tiền ·
người nhận nhầm · người nhận đúng · nội dung khách trình bày. Danh sách cố định ⟹ dựng tất
định được, đây là đòn bẩy cho A2 mà sáu vòng vá prompt không có.

**⑫ Loại khiếu nại lừa đảo — 🔒 DỪNG SAU BƯỚC 3.**
```
1. DỪNG, không sửa code trước
2. Sửa contracts/resolution-state-machine.yaml
3. Ghi ADR mới vào docs/DECISIONS.md
4. ⛔ TRÌNH PO — CHỜ TRẢ LỜI            ← dừng ở đây
5. python3 scripts/check_contracts.py --update
6. Cập nhật CONTRACT_VERSION ở đầu tests/test_invariants.py
7. Commit KÈM file baseline, rồi mới code + migration CHECK constraint
```
ADR phải trả lời được: tên loại · vòng đời trạng thái nào · ai có thẩm quyền · ca đang là
`wrong_recipient` mà hoá ra lừa đảo thì **chuyển loại thế nào**.

**Mọi hạng mục:** land xong phải khai **băm luật mới** — không thì QA/QC không biết mình vừa
đo bản nào. Đội đã trả giá cho đúng chuyện này ("luật đổi dưới chân tôi giữa hai lần đo").

### 5.4 Review Code — **không ghi gì**, báo cáo về Lead

- **Câu hỏi bắt buộc mỗi bản vá:** bản vá này làm cổng nào chuyển **ĐỎ → XANH**? Với mỗi
  cổng đó: *nó khẳng định CÁI GÌ*, và còn khẳng định được sau bản vá không? (**Luật J**)
- **Trọng tâm ③:** siết ba từ có làm **bỏ sót** ca khiếu nại thật nào không — đó là chiều
  đắt của bản vá này; chiều còn lại chỉ tốn token.
- **Trọng tâm ④:** cổng OTP mới có tạo đường nào cho khách **chưa** OTP chạm dữ liệu không.
  Đây là ràng buộc cứng số 4, không phải một tính năng.
- **Trọng tâm ⑨⑪:** mỗi câu mới thêm vào prompt có **truy được về tool hoặc lời khách**
  không. Câu tư vấn quy trình là chỗ dễ hứa thứ không tồn tại nhất, và **O1–O5 không bắt được
  vì nó không phải một con số**. *(Ngoại lệ đã xác nhận: quy trình liên hệ người nhận CÓ THẬT
  — xem §2.)*
- **Luật T:** vai nào vừa sai ≥2 lần liên tiếp trong một mạch việc thì phát biểu
  "xong/sạch/thắng" kế tiếp của họ phải qua bạn **trước khi** Lead relay.
- Một vòng review trả về *"không tìm thấy gì"* hai lần liên tiếp là tín hiệu đọc lướt, không
  phải tín hiệu mã sạch.

---

## 6. Nghiệm thu cả đợt — bốn con số trong bốn tệp

| | con số | hôm nay | sau đợt |
|---|---|---|---|
| 1 | Số lần cổng `thu_slot` bắn oan trên corpus | **6 / 11** | **0 / n** |
| 2 | `ADV-036` · `ADV-038` — lớp phòng thủ có chạy không | xanh, **chưa chạy** | xanh **vì** O1–O5 giữ được |
| 3 | Lượt tốn token trước mốc OTP, đo trên UI thật | **1** | **0** |
| 4 | Cấu hình cờ lúc chạy eval | không khai | in trong mọi báo cáo |

**Đợt đóng khi bốn con số nằm trong bốn tệp, không phải khi bốn vai báo xong.**

---

## 7. Việc chưa đưa vào đợt này — có lý do

Nhánh *"có chữ số ⟹ đầy đủ"* gánh **58,4%** định tuyến (239/409 lượt) — đòn bẩy chi phí lớn
nhất trong hệ. **Chưa động tới**, vì chưa có mẫu số lưu lượng thật. Việc đứng trước nó là đo
phân bố thật từ `usage.jsonl` sau khi ① xong và sau buổi gõ UI của ⑥. Tối ưu trước khi có
mẫu số là đúng thứ **Luật F** cấm.
