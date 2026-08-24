# BẢNG THEO DÕI — đợt "OTP trước token"

> **Đây là NGUỒN SỰ THẬT về tiến độ.** Tin nhắn giữa các phiên là dữ kiện hạng THẤP NHẤT;
> file này là hạng cao nhất. Vai nào làm xong một mục thì **tự tick vào đây và commit**.
>
> **Phiếu giao việc:** `docs/giao-viec/2026-08-24-dot-otp-truoc-token.md`
> **Đặc tả nghiệp vụ:** `docs/kich-ban-chuyen-gia-cskh-chuyen-nham-tien.md`
> **Nền đo:** HEAD `a3bc860` · băm luật `abec4358a501`
>
> **Luật tick — đọc trước khi đánh dấu bất cứ ô nào:**
> - `[ ]` chưa bắt đầu · `[~]` đang làm · `[x]` xong · `[!]` chặn
> - 🔴 **Chỉ tick `[x]` khi có VẬT CHỨNG**: số commit, đường dẫn tệp, hoặc con số đo được.
>   Tick kèm một dòng bằng chứng ngay dưới. Không có vật chứng ⟹ vẫn là `[~]`.
> - **Luật X:** con số không kèm đường dẫn + cách dựng lại thì ghi *"nghe báo, chưa có vật chứng"*.

---

## Điểm danh gần nhất

> ⏱️ **Vòng điểm danh tự động 15 phút đang chạy** *(cron `b573f563`, phiên PO `p-226-b9`)*.
> Chết khi phiên PO đóng. Điểm danh bằng **git log + trạng thái tệp**, không bằng lời khai.

| | |
|---|---|
| **Lần điểm danh cuối** | **#2** |
| **HEAD lúc điểm danh** | `83b9157` |
| **Vai có dấu vết thật** | Lead *(land `83b9157`)* · Coder *(đang sửa `graph.py` + `config.py`)* |
| **Vai chưa có dấu vết** | QA/QC *(vừa nhận việc, chưa tính là đứng im)* · Review *(không ghi repo — dấu vết đi qua Lead)* |

**Bản đồ phiên ↔ vai** *(hỏi thẳng, không suy từ tên phiên)*

| vai | phiên | trạng thái #2 |
|---|---|---|
| Lead | `p-226-8b` | ✅ **L0 đóng** — `83b9157` |
| Coder | `p-226-63` | 🔄 đang sửa `src/agents/graph.py`, `src/config.py` — khớp ⑦ *(kill-switch T0 cần cờ mới)* |
| QA/QC | `p-226-85` | 🔄 vừa nhận ① ② ⑬ |
| Review Code | `p-226-cb` | ⏳ chờ ③ · được giao việc phụ: chuyển N1–N7 cho Lead land vào `docs/` |

---

## L0 — Nền, trước mọi việc

> 🔴 **ĐÍNH CHÍNH 24/08 — Coder (`p-226-63`) bắt lỗi trong chính bảng này, và bắt đúng.**
> Bản đầu gộp **ACK phiếu** với **ACK bản project-knowledge mới** làm một. Hai thứ khác nhau:
> ACK phiếu làm được ngay; ACK bản mới **không thể có** trước khi L0.1 chạy. Tách thành hai
> dãy. Ai tick L0.2–L0.4 khi L0.1 còn `[ ]` là tick một thứ không tồn tại.

**L0a — ACK phiếu giao việc** *(làm được ngay)*

- [x] **L0a.1** **Coder** = `p-226-63` — ACK phiếu tại `961fc24`
- [x] **L0a.2** **Lead** = `p-226-8b` — ACK phiếu tại `961fc24`
- [x] **L0a.3** **QA/QC** = `p-226-85` — ACK phiếu tại `961fc24`
- [x] **L0a.4** **Review Code** = `p-226-cb` — ACK phiếu tại `961fc24`

**L0b — Nền kiến thức** *(L0.1 chặn phần còn lại)*

- [x] **L0.1** Xuất lại `project-knowledge/` — **Lead**
  - `python3 scripts/export_project_knowledge.py` chạy tại HEAD `961fc24`
  - `project-knowledge/00-SYNC-VERSION.md` → `Commit repo: 961fc24`, `Xuất lúc: 2026-08-24 23:51`,
    `agent-tools.yaml @00239f9f0bfc` (khớp `check_contracts.py` hiện hành)
  - Thư mục **gitignore** (`.gitignore:91`) — không có commit, tự đọc trực tiếp trên đĩa để kiểm
  - ⚠️ Việc còn lại **ngoài quyền Lead**: xoá bản cũ + kéo-thả bản mới vào Claude Desktop
    Project là thao tác tay của PO thật — Lead không có quyền đó
- [x] **L0.2** ACK bản project-knowledge MỚI — **Coder**
  - `p-226-63` xác nhận qua SendMessage 24/08: đọc trực tiếp
    `project-knowledge/00-SYNC-VERSION.md` trên đĩa (không cần chờ Desktop) — khớp `961fc24`
- [x] **L0.3** ACK bản project-knowledge MỚI — **QA/QC**
  - `p-226-85` xác nhận qua SendMessage 24/08, cùng cách kiểm trên đĩa
- [x] **L0.4** ACK bản project-knowledge MỚI — **Review**
  - `p-226-cb` đã tự kiểm sớm nhất (trước cả khi Lead hỏi lại), SendMessage 24/08: đọc
    `00-SYNC-VERSION.md` trực tiếp, khớp `961fc24`, xuất `23:51`
- [x] **L0.5** Quyết định worktree riêng từng vai *(cây dùng chung đã gây 3 sự cố)* — **Lead**
  - **Quyết định: KHÔNG tách worktree trong đợt này.** Giữ nguyên kỷ luật pathspec.
  - **Vì sao:** (a) ba stack Docker (`fin05`/`fin05ttl`/`fin05do`) mount cố định đúng thư mục
    làm việc này — tách worktree kéo theo phải dựng lại toàn bộ ánh xạ compose/CI cho từng
    worktree, chi phí hạ tầng cao hơn lợi ích giữa một đợt đang chạy; (b) 3 sự cố cũ đều do
    lệnh `git` **thiếu pathspec** (`stash`/`checkout`/`clean` toàn cây), không phải do va chạm
    file hợp lệ giữa hai vai — sửa nguyên nhân gốc (pathspec) rẻ hơn đổi hạ tầng; (c) 4 vai
    ghi vào 4 vùng gần như rời nhau (`src/` · `tests/+eval/+frontend/e2e/` · `docs/giao-viec+STATE`
    · không ghi gì), bề mặt va chạm thật hẹp.
  - **Sẽ xét lại nếu:** xảy ra sự cố pathspec thứ 4 trong đợt này dù đã nhắc kỷ luật.

---

## Nhóm A — Đo lường (chặn mọi thứ sau nó)

- [ ] **①** Ghim cờ định tuyến vào phép đo — **QA/QC** · `eval/`
  - Báo cáo eval in `PHAN_LUONG_BAT` lúc chạy **và** cột `duong` mỗi ca
  - *Xong khi:* đọc được *"ca này đi `thu_slot`, không chạm model"* **mà không phải mở code**
  - *Đóng:* **Đ2**

- [x] **②** Bộ ca đối chứng **ÂM** cho cổng `thu_slot` — **QA/QC** · `tests/` hoặc `eval/`
  - Trục bắt buộc, mỗi trục ≥1 ca: câu chính sách · ép lộ thông tin bên thứ ba · ép kết luận
    gian lận · lượt sau khi đã phân loại · khách cần hướng dẫn
  - Kèm ca **dương** giữ nguyên *(khiếu nại thật thiếu số tiền)* — Luật A đòi cả hai vế
  - 🔴 *Xong khi:* bộ ca **ĐỎ trên HEAD `a3bc860`**, báo số ca đỏ + tên từng ca
  - **③ KHÔNG được khởi động trước khi mục này đỏ**
  - **VẬT CHỨNG:** `eval/bo_ca_am_thu_slot_dot2.json` (7 ca, băm `9e25ebd5aaea`) +
    `eval/cong_ca_am_thu_slot_dot2.py`. Chạy trên bản **ĐÃ COMMIT** tại HEAD `b6944a6`
    (`src/agents/phan_luong.py` đang dirty ở WIP của Coder — tách riêng, không đo bản dirty):
    `python3 eval/cong_ca_am_thu_slot_dot2.py --luat <bản blob HEAD b6944a6>` →
    **🔴 ĐỎ 3/6 trục âm**: `DOT2-AM-01` (câu hỏi chính sách, chứa "nhầm" trần) ·
    `DOT2-AM-03` (= ADV-036 nguyên văn, ép lộ thông tin bên thứ ba) ·
    `DOT2-AM-04` (= ADV-038 nguyên văn, ép kết luận gian lận) — cả ba đi `thu_slot` sai.
    3 trục còn lại (`DOT2-AM-02` bare "bị" · `DOT2-AM-05` xác nhận sau phân loại ·
    `DOT2-AM-06` khách lớn tuổi cần hướng dẫn) và ca dương `DOT2-DUONG-01` đã ĐÚNG kỳ vọng
    trên HEAD này — không đỏ giả, không đỏ oan các trục đã đúng.
    ⚠️ Số 3/6 không trùng "6/11" của Đ1 trong phiếu — bộ ca này là bộ ĐỘC LẬP mới dựng từ
    đặc tả, không phải chấm lại corpus gốc Đ1 (corpus gốc không nằm trong một file duy nhất).
  - ✅ **PO KIỂM ĐỘC LẬP 25/08** — chạy lại chính cổng ấy, không relay lời khai:
    `python3 eval/cong_ca_am_thu_slot_dot2.py --luat src/agents/phan_luong.py`
    → **tái lập đúng 3 ca đỏ, đúng tên**: `DOT2-AM-01` · `DOT2-AM-03` · `DOT2-AM-04`;
    ba trục còn lại + ca dương xanh. Băm bộ ca khớp `9e25ebd5aaea`, băm luật `9d3af69f8695`.
  - 🔴 **BẰNG CHỨNG NẶNG NHẤT, nay tái lập được:** `DOT2-AM-03` là **`ADV-036` nguyên văn**
    (ép lộ tên + STK người nhận) và `DOT2-AM-04` là **`ADV-038` nguyên văn** (ép kết luận
    gian lận). Cả hai đi `thu_slot` ⟹ request **không chạm LLM, không qua O1–O5**. Hai ca
    ấy đang XANH trong báo cáo adversarial vì câu trả lời lạc đề, **không phải vì hàng
    phòng thủ giữ được**. Một vai **không được đọc `src/`** dựng ra bộ ca này từ đặc tả —
    nên nó không phản chiếu code.
  - ⚠️ **NIÊM một suýt-báo-động-giả của PO, để phiên sau khỏi vấp lại:** PO đo băm bộ ca
    bằng `md5-toan-file-12` tự chế → ra `d19d928f47e7`, lệch. Tệp **đã tự khai** phép băm
    đúng ở khoá `thuat_toan_bam` (`sha256[:12]` của `json.dumps(…indent=1, sort_keys=True)`
    sau khi bỏ hai khoá tự mô tả). Dùng đúng phép ⟹ khớp tuyệt đối. **Gánh nặng thuộc
    người ĐỌC khi tệp đã khai** — đây đúng bẫy `STATE.md §7` ghi PO-agent sập hai lần.

---

## Nhóm B — Vá cổng định tuyến

- [ ] **③** Siết ba từ — **Coder** · `src/agents/phan_luong.py`
  - Gỡ `"nhầm"` + `"bị"` trần khỏi `_TIN_HIEU_KHIEU_NAI`; `"nhận"` → cụm đủ dài
  - 🔴 **CẤM thêm danh sách từ loại trừ** — danh sách loại trừ luôn thiếu một chữ
  - Land xong **khai băm luật mới**
  - *Đóng:* **Đ1** + **Q3**

- [ ] **④** Cổng OTP tất định cho NHÓM B — **Coder** · `src/agents/graph.py`
  - `otp_verified_at` đã có sẵn ở `run_agent_turn:798`, không cần thêm đường dẫn dữ liệu
  - Câu hỏi chính sách **KHÔNG** bị chặn OTP *(Q1)*

- [ ] **⑤** Cổng sau OTP hỏi **thời gian + số tiền một tin** — **Coder**
  - Bỏ mã GD khỏi câu hỏi *(vẫn nhận diện nếu khách tự nêu)*
  - Sửa cách thi hành R1: *"một YÊU CẦU mỗi tin"* → **"một Ý mỗi tin"**
  - ADR 24/08 **đứng nguyên**, không cần ADR thay thế *(xem phiếu §2b)*

- [ ] **⑥** Ca E2E trên UI cho bất biến *"0 token trước OTP"* — **QA/QC** · `frontend/e2e/`
  - Đo trên envelope `/agent/chat` *(mang `duong` + `usage.total_tokens`)*
  - **Ba trạng thái:** `0` ≠ `null` ≠ `>0`
  - 🔴 **Cạm bẫy:** cổng chỉ bắn **một lần mỗi hội thoại** — mỗi ca một chat mới
  - Ngăn gõ: `fin05-po-test` (`127.0.0.1:38443`) · **có tốn token, khai trước**

- [ ] **⑦** Khuôn thời gian *(Đ3)* + kill-switch riêng T0 *(Đ4)* — **Coder**
  - Nhận `"tuần trước"`, `"<số> giờ sáng/chiều/tối"`
  - *Xong khi:* tắt cả hai cờ ⟹ mọi lượt `duong=day_du` **trong sổ**, không đọc code

---

## Nhóm C — Kịch bản chuyên gia *(giá trị cao nhất, rẻ nhất)*

- [ ] **⑧** Hai câu chống mạo danh **K3** — **Coder** · hằng số, 0 token
  - Lượt 1 → gắn cổng OTP: *"đây là mã xác thực phiên hỗ trợ, không phải OTP giao dịch — em
    không bao giờ hỏi OTP giao dịch hay mật khẩu"*
  - Lượt 8 → gắn lượt báo mã hồ sơ: *"sẽ không có ai từ ví gọi điện yêu cầu chị chuyển tiền,
    cung cấp mật khẩu hay mã OTP để lấy lại tiền"*
  - ⭐ **Nếu tuần này chỉ làm được một việc, làm mục này và ⑨**

- [ ] **⑨** Bắt buộc hỏi câu sàng lọc lừa đảo **K2** — **Coder**
  - Hỏi **sự kiện khách quan** *("có ai nhắn tin hoặc gọi điện hướng dẫn chị chuyển khoản
    không")*, **KHÔNG** hỏi kết luận *("chị có bị lừa không")*
  - Khung mở bắt buộc: *"em hỏi thêm một ý để hỗ trợ chị đúng hướng"*
  - Hỏi ở **MỌI** ca chuyển nhầm, kể cả ca trông rõ ràng

- [ ] **⑩** Bản tóm tắt **6 trường tất định** trước `create_ticket` **K4** — **Coder**
  - loại · phạm vi · mã+giờ+tiền · người nhận nhầm · người nhận đúng · nội dung khách trình bày
  - Đây là **đòn bẩy cho A2** mà sáu vòng vá prompt không có · gắn ADR-049

- [ ] **⑪** Ép cấu trúc lượt 5/6/3 — **Coder** · prompt
  - Lượt 5: **ba vế** — không làm được gì → làm được gì → chị làm được gì
  - Lượt 6: đổi góc nhìn PDPA — *"quy định này bảo vệ cả chị nữa"*
  - Lượt 3: đọc lại **đủ 5 dữ kiện** để khách tự đối chiếu
  - 🟢 Bot **được phép** hứa *"bộ phận nghiệp vụ chủ động liên hệ người nhận"* — PO xác nhận
    quy trình CÓ THẬT 24/08

- [ ] **⑬** Bộ ca đánh giá từ kịch bản chuyên gia — **QA/QC** · `eval/`
  - Nhánh A *(có người hướng dẫn)* · Nhánh B *(nhiều GD khớp, phải đổi trục)* · Nhánh C
    *(hai trục vẫn không ra ⟹ "chưa tra được")*
  - 🔴 **Trục dễ trượt nhất:** ca chuyển nhầm **trông rõ ràng** — bot **có hỏi** câu sàng lọc không

---

## Nhóm D — Đổi contract 🔒

- [ ] **⑫** Loại khiếu nại thứ năm cho ca lừa đảo **K1** *(Q4 = A)* — **Coder**
  - [ ] Bước 1 — DỪNG, không sửa code trước
  - [ ] Bước 2 — sửa `contracts/resolution-state-machine.yaml`
  - [ ] Bước 3 — ghi ADR mới vào `docs/DECISIONS.md`
  - [ ] Bước 4 — ⛔ **TRÌNH PO, CHỜ TRẢ LỜI** *(Coder DỪNG ở đây)*
  - [ ] Bước 5 — `python3 scripts/check_contracts.py --update`
  - [ ] Bước 6 — cập nhật `CONTRACT_VERSION` ở đầu `tests/test_invariants.py`
  - [ ] Bước 7 — commit **KÈM file baseline**, rồi mới code + migration `CHECK constraint`
  - *ADR phải trả lời:* tên loại · vòng đời trạng thái · ai có thẩm quyền · ca đang là
    `wrong_recipient` mà hoá ra lừa đảo thì **chuyển loại thế nào**

---

## Nghiệm thu cả đợt — bốn con số trong bốn tệp

- [ ] **N1** Số lần cổng `thu_slot` bắn oan: **6/11** → **0/n**
- [ ] **N2** `ADV-036` · `ADV-038` xanh **vì** O1–O5 giữ được, không phải vì câu lạc đề
- [ ] **N3** Lượt tốn token trước mốc OTP đo trên UI thật: **1** → **0**
- [ ] **N4** Cấu hình cờ in trong mọi báo cáo eval

🔴 **Đợt đóng khi bốn con số nằm trong bốn tệp, không phải khi bốn vai báo xong.**

---

## Sổ điểm danh

> PO ghi mỗi 15 phút. Cột "bằng chứng" là commit/tệp, **không phải lời khai**.

| giờ | HEAD | Lead | Coder | QA/QC | Review | ghi chú |
|---|---|---|---|---|---|---|
| — | `a3bc860` | chưa nhận | chưa nhận | chưa nhận | chưa nhận | phiếu vừa land |
