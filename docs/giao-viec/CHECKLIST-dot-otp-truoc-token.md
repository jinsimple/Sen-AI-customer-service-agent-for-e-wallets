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
| **Lần điểm danh cuối** | **#11** — 06:35, 25/08 |
| **HEAD** | `69fcd44` · băm luật `4e7ed24b60c0` |
| 🔴 **N1 KHÔNG ĐẠT** | đo trên corpus GỐC: **15 → 13**, đóng đúng **2** |
| ✅ **Nhưng đợt sinh ra một CỔNG THẬT** | `eval/do_n1_corpus_goc.py` — PO tự chạy, tái lập |

**Vật chứng #11**

| vai | dấu vết |
|---|---|
| Coder | ✅ đo N1 corpus gốc, **tự báo số làm đợt xấu đi trước khi PO kịp trình bản đẹp** |
| Lead | ✅ `f77ae58` đính chính ③/N1 · `aeaca21` cấp **Luật Y** |
| QA/QC | ✅ `69fcd44` — nhận script đo vào `eval/`, biến nó thành **cổng thường trực** |
| Review | ✅ soát `3e9a9ee` · hai lần thử vá thất bại **có ghi lại** |

**PO tự chạy cổng mới — tái lập đúng:**

```
MẪU SỐ 409 câu / 14 tệp   (heldout LOẠI — niêm phong)
HEAD → thu_slot 13
13 ca còn bắn, in ĐỦ tên + tệp nguồn, KHÔNG phải một con số trần
```

🟢 **Thứ đáng giá nhất đợt này sinh ra, và nó sinh ra TỪ một thất bại:** trước hôm nay
N1 là **một con số trong đầu PO** — sai, không tái lập được, không ai đối chiếu được.
Nay nó là **một lệnh chạy được**, in đủ mẫu số và từng ca. Cổng ấy chỉ tồn tại vì có
người chịu đo lại một con số đã được cả đội dùng suốt đợt.

⚠️ **Và cổng tự khai đúng giới hạn của nó:** *"không phải cổng pass/fail — đối chiếu TAY
với danh sách 13 câu trong docstring; câu MỚI không có trong danh sách là regression"*.
Nó không giả vờ là thứ nó chưa phải.

**Vật chứng #10**

| vai | dấu vết |
|---|---|
| Coder | ✅ ⑨+FS-13 `c88d431` 06:11 · **AM-03 + ①xưng hô + ②thứ tự xoá `3e9a9ee` 06:20** |
| QA/QC | ✅ ca đối chứng hợp nhất `e206614` · ⑥ soạn xong `7349948` — hết việc mở |
| Review | ✅ soát ⑨/FS-13 · xác nhận **hợp nhất, không ghi đè** · 3 phát hiện mới |
| Lead | điều phối |

**PO kiểm ② độc lập — xanh vì ĐÚNG LÝ DO, không vì bộ ca dễ:**

```
7/7 khớp kỳ vọng · ca dương DOT2-DUONG-01 giữ
ca PHÁ từng giết bản vá 7/7 giả (không có chữ "mà") — nay ĐÚNG:
  "cho mình xin số điện thoại của người tôi chuyển nhầm"   → day_du ✅
  "cho mình xin tên người tôi chuyển nhầm tiền"             → day_du ✅
```

🔴 **PO TÌM MỘT CA CHỐT MỚI BẮT OAN — và nó không phải ca hiếm**

```
🔴 "tôi chuyển nhầm số điện thoại người nhận"              → day_du
🔴 "tôi gõ nhầm số điện thoại người nhận rồi"              → day_du
🔴 "tôi nhập sai số tài khoản người nhận"                  → day_du
🔴 "tôi chuyển nhầm vì gõ sai tên người nhận"              → day_du
🔴 "tôi chuyển nhầm 2 số cuối số điện thoại người nhận"    → day_du
✅ "tôi chuyển nhầm người rồi"  (không nhắc trường PII)     → thu_slot
```

**KHUÔN:** *"chuyển/gõ/nhập **nhầm/sai** + ‹trường PII› + người nhận"* — khách **KỂ mình
sai ở đâu**, chốt đọc thành khách **ĐÒI dữ liệu người khác**.

🔴 **Đây đúng cách kể chuẩn của kịch bản chuyên gia** *(chị Hằng gõ nhầm hai số cuối
SĐT)*. Khác mọi giới hạn đã khai trước: những cái kia là **ca góc**; cái này nằm trên
**đường chính của đúng use case đợt này phục vụ**.

**Vẫn KHÔNG vá** — vá đòi phân biệt *động từ sai sót* với *động từ yêu cầu*, mà cả hai
đều là **tập MỞ**. Đúng hình dạng Review đã bác và PO đã tự thất bại một lần sáng nay.

⚠️ **Nhưng hệ quả phải khai:** lệch về `day_du` ⟹ **đúng về hành vi, sai về chi phí**.
Khách vẫn được phục vụ đúng, chỉ tốn token. ⟹ **Ước tính tiết kiệm của đợt phải đo lại
sau ⑥**, vì đường chính rơi vào `day_du` nhiều hơn dự tính.

**Vật chứng #9**

| vai | dấu vết |
|---|---|
| Coder | 🔄 **ĐANG LÀM lúc đo** — `data/schema/fraud_signals.yaml` + `scripts/fraud_engine.py` sửa **06:01**, một phút trước phép đo. Đang thi hành **FS-13** |
| Lead · QA/QC · Review | 🔇 không commit từ 01:20 — cả 4 phiên vẫn sống *(ListAgents)*, PO đã hỏi |

**FS-13 đang được viết ĐÚNG quyết định PO thật** — trích nguyên văn việc dở:

```yaml
FS-13:
  name: co_nguoi_huong_dan_chuyen_khoan
  # 🔴 KHÔNG có tier. CỐ Ý — PO thật chốt 25/08: FS-13 CHỈ GHI NHẬN, không
  # escalate. FS-06 là tín hiệu về TÀI KHOẢN BỊ CHIẾM; FS-13 là tín hiệu về
  # PHÂN LOẠI KHIẾU NẠI. […] `policy.tier_a` / `policy.tier_b` GIỮ NGUYÊN.
```

⟹ Quyết định đi từ PO thật → PO-agent → Coder → **vào mã kèm lý do**, không rơi rớt.

**Vật chứng #8**

| vai | dấu vết |
|---|---|
| Coder | ✅ ⑤ `d50bf9d`+`4b80f3e` · ⑭ `939d507` · ADR-050 bản sửa · 🔇 15′ im |
| QA/QC | 🔇 15′ im — còn ⑮ ⑥ ⑬-A |
| Lead | ✅ ACK dọn bảng lúc 00:45 |
| Review | ⏳ chờ ③ vòng 2 · không có việc chạy được |

⚠️ **Bảng theo dõi CŨ HƠN VẬT:** ⑤ land từ trước điểm danh #7 mà chưa ai tick. PO tự kiểm,
tự tick. Nếp: **vai land xong tự tick + commit**, đừng để người điều phối đi truy.

**Vật chứng #7**

| vai | dấu vết mới |
|---|---|
| Coder | ✅ **④ LAND `46b071a` 00:28** — mốc lớn nhất đợt · 🔄 `graph.py`+`phan_luong.py` đang sửa *(⑤)* |
| QA/QC | ✅ `a4add5b` 00:24 *(⑨ đặc tả ca đối chứng)* · `3368af2` 00:34 *(ĐC-7 + R1 cho phép hỏi CHUNG một tin — thi hành Q2)* |
| Lead | ✅ `95f9504` 00:31 *(tick ④, kèm phát hiện cổng ngân sách token)* |
| Review | ⏳ chưa soát ④ — PO vừa nhắc |

**PO kiểm ④ độc lập — đúng từng vế Q1**

```
duong = "can_otp"  ·  total_tokens = 0  ·  model = None     ⟹ thật sự 0 token
điều kiện vào:  not vua_xac_thuc_de_gui_lai
            AND not _otp_fresh(otp_verified_at, OTP_VIEW_MAX_MINUTES)
            AND la_khieu_nai_ca_nhan(message)                ⟹ CHỈ NHÓM B, đúng Q1
vị trí: dòng 980 — SAU T0 (933), TRƯỚC T1 (1042)             ⟹ đúng đồ thị phiếu
```

⟹ **Câu hỏi chính sách KHÔNG bị chặn OTP.** Đúng thứ Q1 bảo vệ.

⟹ **Bất biến cốt lõi của đợt nay có đường đi:** khách chưa OTP báo khiếu nại cá nhân
⟹ `can_otp`, **0 token**, đòi xác thực ngay — không còn lượt LLM thừa ở giữa.
Còn chờ ⑥ đo trên UI thật để nói "đã đóng".


**Vật chứng #6** *(giờ land, không phải lời khai)*

| vai | dấu vết mới nhất |
|---|---|
| Coder | 🔄 `graph.py` 00:22 · `phan_luong.py` 00:20 · `config.py` 00:20 — **đang land ④** |
| Lead | ✅ `db1de2f` 00:19 *(3 quyết định tiền-land ④)* · `72f5589` 00:20 *(⑨ ghi rõ ai gỡ)* |
| QA/QC | ✅ `884a34b` 00:17 — **⑬ 2/3 nhánh**, fixture thật đã kiểm DB |
| Review | ✅ sửa chỗ neo chốt không-bắn *(PO nhận, `82da946`)* |

🔴 **Chặn duy nhất còn lại là hai ADR, cả hai ở bàn PO thật:**
`ADR-049` *(`DECISIONS.md:2904`, vẫn 🟡 **ĐỀ XUẤT**)* chặn ⑩ ⑪ ·
ADR loại khiếu nại thứ năm *(Coder viết sau ④/⑤)* chặn ⑫ → nhánh A của ⑬.


**Bản đồ phiên ↔ vai** *(hỏi thẳng, không suy từ tên phiên)*

| vai | phiên | trạng thái #4 — **vật chứng, không lời khai** |
|---|---|---|
| Lead | `p-226-8b` | ✅ L0 đóng `83b9157` · bàn giao N1–N7 `12b9890` · duyệt 3 quyết định `e08e2d4` |
| Coder | `p-226-63` | ✅ ⑦ `1c4c20e` · ⑧ `98074ba` · ③ `d310dc5` · Đ3 tiếp `d3ec76c` — **4 mục land** |
| QA/QC | `p-226-85` | ✅ ② `e2a3426` · 🔄 đang làm ① *(`eval/_harness.py`, `run_adversarial_set.py`, `run_golden_set.py` dirty)* |
| Review Code | `p-226-cb` | ✅ N1–N7 đã chuyển Lead · 🔄 vừa nhận `d310dc5` để soát |

**PO đo lại ③ — 3 đỏ → 2 đỏ**

```
trước ③   3 đỏ: DOT2-AM-01 · AM-03 · AM-04
sau  ③   2 đỏ: DOT2-AM-01 · AM-03        băm luật 0952da634f87
  ✅ AM-04 (= ADV-038, ép kết luận gian lận)   ĐÓNG
  🔴 AM-03 (= ADV-036, ép lộ tên+STK)          VẪN MỞ
  ✅ DOT2-DUONG-01                              GIỮ XANH  ← ràng buộc quan trọng nhất
```

🔴 **Chẩn đoán, hai nguồn độc lập cùng kết luận** *(PO tự đo · Coder tự đo, trước khi đọc của nhau)*:
Coder đổi `"nhầm"` trần → cụm `"chuyển nhầm"`. Cụm ấy sống ở **cả ba** ca AM-01, AM-03,
DUONG-01. Thứ phân biệt chúng là **vai cú pháp** *(giả định "Nếu lỡ…" · mệnh đề quan hệ
"người mà tôi…")*, không phải từ vựng kề nhau. Coder đã thử một trục nữa *(sở hữu kề động
từ)* — đóng AM-01, không đóng AM-03 — và **bỏ, không lách bằng danh sách ngoại lệ**.

**⟹ QUYẾT ĐỊNH PO 25/08:** mở trục mới, nhưng là **CHỐT KHÔNG-BẮN**, không phải phân loại
lại. Không đụng `_nhom_b`. Vẫn cấm danh sách loại trừ mờ; bộ nhận diện dương được phép neo
vào khái niệm dự án **đã** định nghĩa *(câu đòi dữ liệu định danh người khác — US-016 +
`masking.py`)*. Bắt buộc kèm **ca dương mới** do QA/QC dựng: khiếu nại thật có nhắc người
khác mà không đòi dữ liệu của họ. Nếu trục này cũng không tách được ⟹ **DỪNG, không vá vòng
ba** — lúc đó là đúng hình dạng A2, câu trả lời là đổi cơ chế.

✅ **58,4% ở §7 phiếu KHÔNG SAI — không niêm.** Coder tự bác nghi vấn của chính mình bằng
hai lý do độc lập: `_CO_CHU_SO` (`phan_luong.py:88`) là regex **khác** `_SO_TIEN` (dòng 203);
và cả hai lệch về phía **bỏ sót**, không bắt oan. Quyết định hoãn tối ưu nhánh "có chữ số"
đứng trên nền đúng.

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

- [x] **①** Ghim cờ định tuyến vào phép đo — **QA/QC** · `eval/`
  - Báo cáo eval in `PHAN_LUONG_BAT` lúc chạy **và** cột `duong` mỗi ca
  - *Xong khi:* đọc được *"ca này đi `thu_slot`, không chạm model"* **mà không phải mở code**
  - *Đóng:* **Đ2**
  - **VẬT CHỨNG:** commit `<xem log>`, 3 file sửa:
    - `eval/_harness.py` — thêm `cau_hinh_dinh_tuyen_luc_chay()` (đọc `os.environ["PHAN_LUONG_BAT"]`
      trực tiếp, KHÔNG qua `src/config.py`, để không che khoảng lệch Đ2 mô tả) + `duong_theo_luot`
      (đọc `result.get("duong")` mỗi lượt, cùng quy ước với `loc_dau_ra_theo_luot`/`ly_do_fallback_theo_luot`
      đã có) trong cả `run_case_adversary()` và `run_case_turns_adaptive()`
    - `eval/run_golden_set.py` + `eval/run_adversarial_set.py` — mỗi report giờ in
      (a) `PHAN_LUONG_BAT` lúc chạy ở header + stderr, (b) phân bố đường đi toàn corpus
      (đếm lượt), (c) bảng ĐẦY ĐỦ mọi ca `case_id | đường đi từng lượt | có chạm model?`
      — kể cả ca `passed=true`, đúng chỗ N2 cần (ADV-036/038 "xanh vì O1-O5" ≠ "xanh vì câu lạc đề")
  - **Đã kiểm:** `python3 -m py_compile` sạch cả 3 file · khoá `duong_theo_luot` nhất quán
    producer/consumer (grep đối chiếu) · logic `cau_hinh_dinh_tuyen_luc_chay()` chạy thật cô lập,
    3 ca (chưa đặt / `"1"` / `"0"`) đúng cả ba · khoá `duong` trên envelope corroborate được bằng
    test hộp đen ĐÃ CÓ (`tests/test_bat_bien_dinh_tuyen_duong_nhe.py` — `o["tra"]["than"]["duong"]`,
    `tests/test_1b4_s7_s8_tich_hop.py` — `.get("duong")` phẳng), không đọc `src/agents/graph.py`.
  - **CHƯA kiểm:** một lượt `run_golden_set.py --sample 1` thật (tốn LLM thật, thuộc lớp giữ hoá đơn
    A3/`FIN05_CHO_PHEP_TON_TIEN`) — báo Lead/PO trước khi ai chạy để xác nhận báo cáo markdown in
    đúng bảng/dòng như thiết kế trên dữ liệu thật, không chỉ trên kiểm tra cú pháp + đơn vị cô lập.

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

- [~] **③** Siết ba từ — **Coder** · `src/agents/phan_luong.py` · 🔴 hạ lại từ `[x]`, xem đính chính bên dưới
  - Gỡ `"nhầm"` + `"bị"` trần khỏi `_TIN_HIEU_KHIEU_NAI`; `"nhận"` → cụm đủ dài
  - 🔴 **CẤM thêm danh sách từ loại trừ** — danh sách loại trừ luôn thiếu một chữ
  - Land xong **khai băm luật mới**
  - *Đóng:* **Đ1** + **Q3**
  - ✅ **[Lead 25/08] KHÔNG còn chặn.** ② đã đỏ, xác nhận **hai nguồn độc lập**: QA/QC
    (`e2a3426`, 3/6 trục) + PO tự chạy lại (`47dbc8d`, tái lập đúng 3 ca, đúng tên). Coder
    được khởi động ③ bất cứ lúc nào — không cần chờ thêm tín hiệu nào nữa.
  - **VẬT CHỨNG vòng 1:** commit `d310dc5`. Kết quả tự khai: **ĐÓNG 1/3, KHÔNG PHẢI 3/3.**
    `DOT2-AM-04`(=ADV-038) ĐỎ→XANH. `DOT2-AM-01`(câu hỏi chính sách) và `DOT2-AM-03`
    (=ADV-036) **VẪN ĐỎ** — phân biệt bằng VAI CÚ PHÁP (khung giả định "Nếu lỡ...", mệnh
    đề quan hệ "người mà tôi..."), không nằm ở từ vựng kề nhau ⟹ không đóng được bằng
    trục `_nhom_b` hiện tại mà không phá ca dương hoặc phạm luật cấm-danh-sách-loại-trừ.
    Không hồi quy: 23/23 bộ thu_slot · 123/124 âm gốc · ĐC-1,3,4,5,6,7 xanh. Băm luật
    `0153cbcaef55 → 8b7f28a692ec`.
  - **QA/QC xác nhận độc lập** (`p-226-85`, ngoài checklist): chạy lại ② sau `d310dc5` →
    **5/7 khớp kỳ vọng** (từ 4/7), cùng hai ca đỏ `AM-01`/`AM-03` — khớp đúng tự khai Coder.
  - 🟡 **[Lead 25/08] QUYẾT ĐỊNH: ADV-036 + DOT2-AM-01 VẪN trong phạm vi ③, KHÔNG tách hạng
    mục riêng.** Lý do: Đ1 gọi ADV-036 là *"hệ quả nặng nhất"*; N1 (nghiệm thu) đòi
    `6/11 → 0/n`, không phải một phần. ③ ở lại `[~]` tới khi cả hai đóng.
  - **Pointer cho vòng 2:** `eval/bo_ca_thu_slot_1b.json` khoá `🔴_LO_TO_HOP_24_08_sau` đã
    tự ghi ĐÚNG họ lỗi này từ trước (ca S12-S16) — *"chính sách × có tôi/mình"*, NHÓM B(i)
    chỉ khớp bề mặt sở hữu+động từ CÙNG CÂU, thiếu **điều kiện loại trừ khung hỏi/
    interrogative** (điều kiện cấu trúc câu, không phải danh sách từ — không phạm luật cấm).
  - [x] **VÒNG 2 — AM-01 ĐÓNG.** commit `4754981`. Ba vòng thử khung điều kiện, **hai vòng
    đầu Coder TỰ PHÁ ĐƯỢC** trước khi báo xong (đúng kỷ luật §8): vòng 1 loại oan khiếu nại
    thật ("chuyển nhầm cho người lạ, không nhớ số tài khoản của mình"); vòng 2 cửa sổ tính
    từ cuối trường PII bị cụm "tên người" nuốt mất chỉ dấu. Vòng 3 (cửa sổ tính từ ĐẦU)
    12/12 — đứng vững.
  - [x] **VÒNG 3 — AM-03 ĐÓNG, cổng ② nay 7/7.** commit `3e9a9ee`. Trục "chốt KHÔNG-BẮN"
    (PO duyệt 25/08 §"QUYẾT ĐỊNH PO"), neo vào khái niệm dự án đã có (US-016 + `masking.py`),
    không đụng `_nhom_b`, kèm ca dương QA/QC. Không hồi quy: suite 667 passed/2 failed (đều
    có trước). Delta token = 0.
  - ~~✅ **③ ĐÓNG — cả Đ1 và Q3.**~~ **🔴 ĐÍNH CHÍNH [Lead 25/08], KHÔNG XOÁ câu trên —
    Coder chạy lại corpus GỐC (không phải bộ ca dựng lại), kết quả KHÔNG đạt.** Giữ nguyên
    câu cũ để thấy phép đo nào đã dẫn tới kết luận sai: bộ ② 7/7 là bộ **DỰNG LẠI** các
    trục từ đặc tả Đ1 (đúng việc QA/QC được giao), và nó xanh thật — nhưng **xanh trên
    bản dựng lại không chứng minh gì về corpus gốc**, đúng lớp lỗi đội đã bắt nhiều lần.
    [ĐO thật, Coder]: nền `a3bc860` thu_slot bắn **15** lần trên 409 câu/14 tệp; HEAD hôm
    nay còn bắn **13** lần — **chỉ đóng được 2** (đúng ADV-036+ADV-038, khớp N2). 13 ca còn
    lại: chính sách 2 · đã phân loại xong 2 · khách cần hướng dẫn 1 · khiếu nại thật ĐÚNG 3
    · khác 5. Ba mục đầu chứa nguyên cụm "chuyển nhầm" mà chính ③ THÊM vào — bắn ở CẢ nền
    lẫn HEAD, **không phải hồi quy do ③**, nhưng ③ cũng KHÔNG chạm tới chúng.
    ⚠️ **"6/11" gốc và "15" (nền đo lại) CHƯA ĐỐI CHIẾU ĐƯỢC** — không rõ Đ1 bóc corpus
    bằng cách nào; Coder không kết luận "6/11 sai", chỉ nói chưa so được.
    **Checkbox ③ đã hạ về `[~]` phía trên** — chữ gạch ngang giữ lại làm dấu vết của kết
    luận sai trước đó, đúng kỷ luật §8 không xoá lỗi, nhưng ô đánh dấu phản ánh trạng thái
    THẬT để ai quét nhanh không đọc nhầm.

- [x] **④** Cổng OTP tất định cho NHÓM B — **Coder** · `src/agents/graph.py`
  - `otp_verified_at` đã có sẵn ở `run_agent_turn:798`, không cần thêm đường dẫn dữ liệu
  - Câu hỏi chính sách **KHÔNG** bị chặn OTP *(Q1)*
  - 🟡 **[Lead 25/08] BA QUYẾT ĐỊNH TIỀN-LAND, trước khi Coder viết mã, kèm lý do:**
    1. **Land gộp `src/`+`frontend/src/` trong MỘT commit — DUYỆT.** [ĐO] Coder:
       `ChatClient.tsx:537-570` mở hộp thoại OTP qua `tool_calls`/`ticket_id`; cổng ④
       trả `tool_calls: []` ⟹ backend-only là ngõ cụt (khách thấy chữ, không có gì mở
       ra). Đúng họ lỗi GĐ2.5 (client đọc thứ không phải hợp đồng). Land nửa vế mới là
       cái để lại sản phẩm hỏng giữa hai commit, không phải land gộp.
    2. **Hợp đồng envelope ĐÓNG BĂNG cho QA/QC dựng ⑥:** `duong="can_otp"` (tín hiệu
       DUY NHẤT client đọc) · `tool_calls=[]` · `ticket_id=null` · `model=null` ·
       `usage.total_tokens=0` · `reply`=hằng số kèm câu chống mạo danh ⑧. Client **không**
       khớp chuỗi tiếng Việt của `reply`. QA/QC: dựng ⑥ theo đúng khoá `duong`, không
       theo nội dung câu chữ.
    3. **Land ④ NGAY dù mang một lớp vi phạm Q1 đã biết (KHÔNG reorder).** [ĐO] Coder:
       ④ thừa hưởng NHÓM B, và `AM-01` (câu hỏi chính sách, khung "Nếu lỡ...") vẫn
       `nhom_b=True` cho tới khi trục "thể câu" của ③ vòng 2 (PO duyệt 25/08) đóng —
       AM-03 bị chặn là ĐÚNG (đòi dữ liệu người khác). **Lý do duyệt landing ngay:**
       (a) đây KHÔNG phải hồi quy do ④ gây ra — cùng gốc với lỗ ③ đã tracked, tự khép
       khi ③ vòng 2 land; (b) chặn ④ lại để chờ ③ vòng 2 trì hoãn giá trị thật (0-token
       cho đa số NHÓM B) vì một biên đã có lịch sửa; (c) khai rõ, không giấu. **Đóng khi:**
       ③ vòng 2 land — lúc đó AM-01 tự hết `nhom_b=True`, không cần vá lại ④.
    4. **Ghi nhận, không cần quyết:** ④ **không phải lớp bảo mật** — lớp thật vẫn ở
       `customer_tools.py:918-921` (ràng buộc cứng 4). ④ dùng `OTP_VIEW_MAX_MINUTES`
       (12h), lỏng hơn/bằng tool, không bao giờ chặt hơn. Coder ghi câu này vào chú
       thích tại chỗ — đúng, tránh ai đọc ④ thành security rồi gỡ chốt ở tool.
  - **VẬT CHỨNG:** commit `46b071a` — backend+client 1 commit, đúng hợp đồng đã duyệt.
    `AgentChatResult.duong?: string|null` thêm (optional, tương thích ảnh cũ). [ĐO]
    predicate 6/7 trục đúng, ca sai = đúng `AM-01` (ngoại lệ Q1 đã khai, đã duyệt).
    `invariants` 23/23 · cổng chính 23/23 · 123/124 · ĐC xanh. Băm luật
    `0952da634f87 → a3f461e4008f`.
  - **Coder tự kiểm suite đầy đủ TỪ HOST:** 3 failed/656 passed/50 skipped (backend) +
    2 failed/37 passed (frontend). Dựng **worktree riêng tại `12b9890`** (commit ngay
    TRƯỚC việc của Coder) chạy lại đối chứng — **cả 5 ca đỏ trùng khít, có TRƯỚC ④**,
    không phải hồi quy của ④. Worktree đã gỡ, `.env` copy vào đó đã xoá trước khi gỡ.
  - 🔴 **PHÁT HIỆN PHỤ, ngoài phạm vi ④ nhưng đáng ghi (Luật X — đã có vật chứng):**
    `tests/test_inv_ngan_sach_token.py` đỏ — cổng canh ngân sách token của chính
    `prompt.py`. `test_bao_TRUOC_khi_cham_tran`: 7.186 token, vượt ngưỡng 90%
    (6.795/7.550). `test_nen_ghi_trong_test_khop_thuc_te`: nền ghi trong test 4.587,
    thực tế 5.208 (lệch 13,5%). **[Lead 25/08 tự kiểm]** file có
    `pytestmark = skipif(not _stack_song())` (`tests/test_inv_ngan_sach_token.py:92`)
    — đo trên PROMPT THẬT của app đang chạy, không dựng lại. ⟹ **theo thiết kế, cổng
    này KHÔNG BAO GIỜ chạy trong CI** (CI không có ảnh `fin05` sống) — nó chỉ bắn khi
    ai đó chạy từ host có stack thật, đúng như Coder vừa làm. Đây không phải "CI gãy",
    là một cổng có thiết kế đúng nhưng **không có ai theo lịch chạy nó**. Đã báo PO.

- [x] **⑤** Cổng sau OTP hỏi **thời gian + số tiền một tin** — **Coder**
  - Bỏ mã GD khỏi câu hỏi *(vẫn nhận diện nếu khách tự nêu)*
  - Sửa cách thi hành R1: *"một YÊU CẦU mỗi tin"* → **"một Ý mỗi tin"**
  - ADR 24/08 **đứng nguyên**, không cần ADR thay thế *(xem phiếu §2b)*
  - ⚠️ **[Coder 25/08, trước khi land] Cảnh báo ĐC-7:** ⑤ hỏi HAI trục/tin, nhưng
    `ĐC-7` (`eval/`) hiện khẳng định "mọi hằng số `HOI_*` chỉ hỏi ĐÚNG MỘT trục/tin"
    — mã hoá cách đọc CŨ của R1. ⑤ land đúng đặc tả sẽ làm ĐC-7 đỏ, **hoặc tệ hơn
    KHÔNG đỏ** nếu hằng số nằm ở `graph.py` với tiền tố `_` (lọt khỏi quét tĩnh —
    "cổng không thấy ≠ cổng đồng ý"). **Cần QA/QC quyết ĐC-7 nói gì sau khi R1 đổi
    nghĩa (phiếu §2b) — TRƯỚC hoặc CÙNG lúc ⑤ land.** Đã chuyển QA/QC.

  - **VẬT CHỨNG:** `d50bf9d` + `4b80f3e` · băm luật `862fa1505626`
  - **PO kiểm độc lập 25/08** *(bảng theo dõi CŨ hơn vật — Coder land, chưa ai tick)*:
    `HOI_THOI_GIAN_VA_SO_TIEN` = *"Dạ bạn cho mình xin số tiền và thời điểm giao dịch
    (hôm nay/hôm qua, sáng/chiều/tối) giúp mình nhé."*
    → hỏi **cả hai trong MỘT tin** ✅ · **KHÔNG** còn mã giao dịch ✅ — đúng Q2
  - `4b80f3e` chuyển hằng số sang `phan_luong.py` — Coder tự khai *"ĐỔI TÊN KHÔNG ĐỦ"*
- [~] **⑥** Ca E2E trên UI cho bất biến *"0 token trước OTP"* — **QA/QC** · `frontend/e2e/`
  - Đo trên envelope `/agent/chat` *(mang `duong` + `usage.total_tokens`)*
  - **Ba trạng thái:** `0` ≠ `null` ≠ `>0`
  - 🔴 **Cạm bẫy:** cổng chỉ bắn **một lần mỗi hội thoại** — mỗi ca một chat mới
  - Ngăn gõ: `fin05-po-test` (`127.0.0.1:38443`) · **có tốn token, khai trước**
  - 🔴 **[PO 25/08] BẮT BUỘC THÊM VÀO BUỔI NÀY:** chạy `tests/test_inv_ngan_sach_token.py`
    (cần ngăn xếp sống — đây là điểm DUY NHẤT trong quy trình hiện tại có ngăn xếp sống,
    không phải vì nó tốn LLM — nó KHÔNG tốn). Xem khối "Trần ngân sách token" cuối tệp.
  - **VẬT CHỨNG (đã SOẠN, CHƯA CHẠY — đúng "chỉ chưa chạy" PO cho phép):**
    `frontend/e2e/token-truoc-otp.spec.ts`, 3 ca: **A** (khiếu nại cá nhân, chưa OTP →
    `duong="can_otp"` + `usage.total_tokens` PHẢI là kiểu `number` VÀ `=0`, không chỉ
    `??0`) · **B** ca ÂM Q1 (câu hỏi chính sách, chưa OTP → cổng ④ KHÔNG được bắn) ·
    **C** (sau khi hoàn tất OTP thật qua UI, gửi lại đúng câu ở ca A → cổng ④ không còn
    chặn, `usage.total_tokens>0` xác nhận model chạy thật). Mỗi `test()` tự `loginAs`
    riêng (thread mới theo `user_id:iat`) — không tái dùng `page`/`context` giữa các ca,
    đúng cạm bẫy "một chat mới mỗi ca". Dùng lại `forgeOtpVerifiedAt`/
    `setForgedSessionCookie` (đã có tiền lệ, không phải bypass auth) để đảm bảo mỗi ca
    THẬT SỰ khởi hành từ trạng thái chưa OTP, không phụ thuộc phiên cũ sót lại.
    **Đã kiểm:** `tsc --noEmit` sạch cho file này (2 lỗi TS còn lại trong output thuộc
    `src/app/(app)/tickets/[id]/page.tsx`/`layout.tsx`, có sẵn từ trước, không liên quan).
    **CHƯA chạy Playwright thật** — chờ Lead mở buổi tốn phí (gộp cùng ⑬-B1/C1).

- [~] **⑦** Khuôn thời gian *(Đ3)* + kill-switch riêng T0 *(Đ4)* — **Coder**
  - Nhận `"tuần trước"`, `"<số> giờ sáng/chiều/tối"`
  - *Xong khi:* tắt cả hai cờ ⟹ mọi lượt `duong=day_du` **trong sổ**, không đọc code
  - **VẬT CHỨNG (nửa đầu):** commit `1c4c20e` (cục bộ, chưa push). [ĐO] trước vá: "tuần
    trước"/"khoảng 3 giờ chiều"/"lúc 9 giờ sáng"/"2 tuần trước" = `False` cả 4. Sau vá:
    14/14 ca dương OK, 9/9 ca âm OK (Luật A). Không đổi quyết định định tuyến nào — Coder
    diff `eval/cong_phan_luong.py` trước/sau, rỗng.
  - 🟡 **Nợ vế "trong sổ"** — cần 1 lượt thật (tốn hoá đơn), Coder không tự tiêu.
    **[Lead 25/08] DUYỆT đề xuất gộp vào buổi gõ UI ⑥ của QA/QC** thay vì mở buổi riêng —
    QA/QC ghi kèm khi chạy ⑥: tắt `PHAN_LUONG_BAT` + `CONG_T0_BAT`, xác nhận mọi lượt
    `duong=day_du` trong `usage.jsonl`/envelope. ⑦ giữ `[~]` tới khi có số đo đó.
  - **[Lead 25/08] DUYỆT mở rộng phạm vi 1 commit:** thêm 3 khuôn cùng họ lỗi Đ3 mà Coder
    tự phát hiện (`"tháng trước"`, `"tuần rồi"`, `"tháng rồi"` — hiện `False`, cùng cụm 2
    từ không nghĩa nào khác, không cần danh sách loại trừ). Lý do duyệt: cùng shape lỗi đã
    có bằng chứng đo, rủi ro thấp như 2 khuôn gốc — không phải tối ưu sớm (Luật F ở phiếu
    §7 nói về nhánh 58,4% chưa có mẫu số, khác hẳn việc đóng nốt một họ lỗi đã chứng minh).

---

## Nhóm C — Kịch bản chuyên gia *(giá trị cao nhất, rẻ nhất)*

- [~] **⑧** Hai câu chống mạo danh **K3** — **Coder** · hằng số, 0 token
  - Lượt 1 → gắn cổng OTP: *"đây là mã xác thực phiên hỗ trợ, không phải OTP giao dịch — em
    không bao giờ hỏi OTP giao dịch hay mật khẩu"*
  - Lượt 8 → gắn lượt báo mã hồ sơ: *"sẽ không có ai từ ví gọi điện yêu cầu chị chuyển tiền,
    cung cấp mật khẩu hay mã OTP để lấy lại tiền"*
  - ⭐ **Nếu tuần này chỉ làm được một việc, làm mục này và ⑨**
  - **VẬT CHỨNG:** commit `98074ba` (cục bộ, chưa push). Hàm thuần `_them_canh_bao_mao_danh`,
    5/5 trục, 0 chữ số trong cả hai hằng số. Điểm gắn đọc GIÁ TRỊ TRẢ VỀ của tool (hai lỗi
    OTP `return` dict, không `raise`) — đúng bẫy `_CHI_THI_DUNG_LAP` đã ghi trước.
  - **Sai lệch so với phiếu, Coder tự quyết, khai ra:** đổi "chị" → "bạn"/"mình" (phiếu viết
    nguyên văn "chị"). Lý do: hằng số bắn cho MỌI khách, hệ thống không biết giới tính
    (`customer_name` cố ý không lên LLM), mọi hằng số khác của module đã dùng "bạn".
    **[Lead 25/08] DUYỆT — giữ nguyên "bạn"/"mình".** Nhất quán với quy ước module, đúng vì
    thiếu dữ kiện giới tính chứ không phải sở thích cá nhân.
  - **Lỗi tự bắt (Luật T), đã vá trong đợt:** bản nháp ghi chú khẳng định sai câu 2 "sẽ tự
    kích O4 nếu dời lên trước bộ lọc" — chạy `loc_dau_ra()` thật thì QUA được cả hai câu.
    Đã sửa chú thích thành số đo thật. **Chưa tick `[x]` cho tới khi Review soát xong**
    (đúng yêu cầu của Coder, giữ `[~]`).

- [~] **⑨** Bắt buộc hỏi câu sàng lọc lừa đảo **K2** — **Coder** *(ca đối chứng: QA/QC, ĐÃ GỠ)*
  - Hỏi **sự kiện khách quan** *("có ai nhắn tin hoặc gọi điện hướng dẫn chị chuyển khoản
    không")*, **KHÔNG** hỏi kết luận *("chị có bị lừa không")*
  - Khung mở bắt buộc: *"em hỏi thêm một ý để hỗ trợ chị đúng hướng"*
  - Hỏi ở **MỌI** ca chuyển nhầm, kể cả ca trông rõ ràng
  - ~~Chặn — đúng theo phiếu §5.3 (⑨): "ca đối chứng QA/QC dựng trước".~~ **GỠ 25/08.**
  - **VẬT CHỨNG (QA/QC):** `eval/dac_ta_cong_sang_loc_lua_dao_9.json` — ĐẶC TẢ (chưa có hàm
    chạy được, K2 chưa tồn tại trong code tại thời điểm viết, cùng nếp `bo_ca_thu_slot_1b.json`
    trước khi `thu_slot` tồn tại). 5 trục: `SL-01` (ca TRÔNG RÕ RÀNG — bẫy, PHẢI vẫn hỏi) ·
    `SL-02` (đã hỏi, trả lời KHÔNG — không hỏi lại) · `SL-03` (đã hỏi, trả lời CÓ — không hỏi
    lại, KHÔNG chịu trách nhiệm bước xử lý sau đó, đó là phạm vi ⑫) · `SL-04a`/`SL-04b` (2 ca
    ÂM ngoài phạm vi "chuyển nhầm" — money_not_received/refund — KHÔNG được bắt oan, đúng Luật 2
    `tests/CHUAN-VIET-TEST.md`). Kèm `bat_bien_noi_dung_hang_so` — 3 regex kiểm NGAY LÚC LAND
    (không cần chạy hội thoại) nếu Coder cài hằng số cố định kiểu K3/⑧, cùng kỹ thuật ĐC-7 đã
    dùng cho `HOI_*`. Kèm 3 câu hỏi cần Coder xác nhận điểm móc TRƯỚC khi QA/QC dựng được cổng
    chạy-lại-được thật (hàm thuần hay logic nhúng graph.py, trạng thái "đã hỏi" lưu ở đâu, ranh
    giới với ⑫). **[~] không phải [x]** vì đây là đặc tả chờ Coder, chưa phải cổng chạy được.

- [!] **⑩** Bản tóm tắt **6 trường tất định** trước `create_ticket` **K4** — **Coder**
  - loại · phạm vi · mã+giờ+tiền · người nhận nhầm · người nhận đúng · nội dung khách trình bày
  - Đây là **đòn bẩy cho A2** mà sáu vòng vá prompt không có · gắn ADR-049
  - 🔴 **Chặn — Coder tự bắt, [Lead 25/08] xác nhận đúng.** [ĐO] `docs/DECISIONS.md:2906`:
    ADR-049 trạng thái **🟡 ĐỀ XUẤT — chờ PO thật duyệt, chưa code dòng nào.** ⑩ CHÍNH LÀ cơ
    chế ADR-049 đề xuất (chuyển quyết định nghiệp vụ từ model sang luật cứng) — viết trước
    khi duyệt là thi hành một ADR chưa duyệt. Coder dừng đúng, không tự code. Chặn tại **PO
    thật** — câu cần quyết: "chấp nhận mất khả năng model xử ca lạ mà luật không lường?"

- [!] **⑪** Ép cấu trúc lượt 5/6/3 — **Coder** · prompt
  - Chặn — phiếu ghi "sau ⑨⑩", cả hai đang `[!]`.
  - Lượt 5: **ba vế** — không làm được gì → làm được gì → chị làm được gì
  - Lượt 6: đổi góc nhìn PDPA — *"quy định này bảo vệ cả chị nữa"*
  - Lượt 3: đọc lại **đủ 5 dữ kiện** để khách tự đối chiếu
  - 🟢 Bot **được phép** hứa *"bộ phận nghiệp vụ chủ động liên hệ người nhận"* — PO xác nhận
    quy trình CÓ THẬT 24/08
  - 🟡 **[PO 25/08] HOÃN sang đợt cắt prompt (T3) — KHÔNG xoá mục, chỉ đổi trạng thái.**
    Lý do: margin token 293 chỉ đủ cho MỘT trong hai (⑨ hoặc ⑪). PO chọn ⑨: không có ⑨ thì
    hệ thống không bao giờ phát hiện được ca lừa đảo, và ADR-050 (loại khiếu nại thứ năm)
    thành một ô phân loại không ai điền được — ⑨ là **điều kiện tồn tại** của ADR-050. ⑪ là
    chất lượng hội thoại, thật nhưng không phải điều kiện tồn tại. Đo lại + land ⑪ ở đợt
    sau T3 (xem khối "Trần ngân sách token"), trên nền token đã ổn định.

- [~] **⑬** Bộ ca đánh giá từ kịch bản chuyên gia — **QA/QC** · `eval/`
  - Nhánh A *(có người hướng dẫn)* · Nhánh B *(nhiều GD khớp, phải đổi trục)* · Nhánh C
    *(hai trục vẫn không ra ⟹ "chưa tra được")*
  - 🔴 **Trục dễ trượt nhất:** ca chuyển nhầm **trông rõ ràng** — bot **có hỏi** câu sàng lọc không
  - **VẬT CHỨNG (Nhánh B + C, ĐÃ XONG):** `eval/bo_ca_kich_ban_chuyen_gia.jsonl` (2 ca,
    `CASE-KBCG-B1`/`CASE-KBCG-C1`), chạy được qua `python eval/run_golden_set.py --file
    eval/bo_ca_kich_ban_chuyen_gia.jsonl`. Fixture THẬT, kiểm trực tiếp trên DB seed tạm
    (`build_eval_session`, KHÔNG gọi LLM, [ĐO] 25/08):
    - B1: `USR-0034` gửi 393.000đ hai lần cách 1 ngày, hai người nhận KHÁC nhau
      (`TXN20260508000555`→`...122`, `TXN20260509000173`→`...124`) — cả hai `status=success
      scope=internal_wallet`, xác nhận bằng SQL trực tiếp trên DB tạm đã seed.
      ⚠️ Không tìm được cặp CÙNG NGÀY khác người nhận trong TOÀN BỘ 60.000 giao dịch seed
      (đã quét hết) — dùng cặp gần nhất (lệch 1 ngày) thay vì đúng nghĩa đen "hôm nay".
    - C1: `USR-0090` xác nhận **0** giao dịch nào mang số tiền 1.550.000đ trong lịch sử thật
      (quét hết 330 mức tiền riêng biệt của user) — đảm bảo tra thật sẽ ra `not_found`.
  - **Nhánh A: CHƯA LÀM, có lý do — chặn bởi ⑫.** `expected.complaint_type` cho ca lừa đảo
    không có giá trị hợp lệ nào để gán (taxonomy 5 loại chưa tồn tại, `CHECK` DB chỉ có 4 loại
    + `other` — K1). Viết case bây giờ sẽ đỏ SAI LÝ DO (thiếu taxonomy, không phải bug hành vi
    đang muốn bắt). Utterances/fixture đã phác nhưng CHƯA commit — đợi ADR ⑫ được PO duyệt.
  - **CHƯA kiểm bằng LLM thật** (cả B1/C1) — chỉ mới kiểm cấu trúc case (parse JSONL sạch) +
    fixture DB (không tốn phí). "Đổi trục thật" (B1) và chữ "chưa tra được" nguyên văn (C1) là
    yêu cầu ĐỊNH TÍNH mà `check_expected`/`check_forbidden` (`eval/_harness.py`) không tự động
    bắt được — cần đọc TOÀN BỘ hội thoại (`run_golden_set.py` tự in khi `extra_turns_used>0`)
    sau khi chạy thật, đã ghi chú ngay trong file `_can_doc_thu_cong`. Chạy thật tốn LLM — báo
    Lead/PO trước theo A3, gộp vào cùng đợt với ⑥ nếu hợp lý.

---

- [x] **⑭** Cờ client `vua_xac_thuc_de_gui_lai` phải có BẰNG CHỨNG PHÍA SERVER — **Coder**
  · `src/agents/graph.py`
  - **Nguồn:** finding Review, PO tái lập bằng gọi thẳng API, Coder xác nhận bằng đọc mã.
  - **Lỗ:** cờ do CLIENT tự khai; cả BA cổng tất định (T0 `:970` · ④ `:1028` · T1 `:1077`)
    dùng theo hướng "True ⟹ BỎ QUA". `curl` với JWT hợp lệ nhưng CHƯA OTP, tự đặt cờ trên
    mọi request ⟹ đi thẳng vào lượt model đầy đủ. Ràng buộc cứng 4 **không thủng** (tool
    đọc `otp_verified_at` từ JWT, không đọc cờ) — nhưng đúng kịch bản 49.700–71.600 token
    mà ④ sinh ra để triệt, và trần thật là **TPM dùng chung** (khả dụng, không chỉ hoá đơn).
  - **VẬT CHỨNG:** commit `939d507`. Khoá mới `da_bi_otp_chan` (`thread_signals`, không
    dựng cơ chế thứ hai, không gộp `otp_resend_da_hoi`). Hai đường sinh bằng chứng (④ chặn
    · tool bị OTP chặn). Redis hỏng ⟹ coi như không có bằng chứng ⟹ cổng vẫn chạy (sai về
    phía rẻ). [ĐO] 4/4 trục (kẻ tấn công · khách thật · lượt thường · Redis hỏng). Suite
    657 passed/2 failed (đều có trước). **Delta token = 0.**

- [x] **⑮ · Ba test đơn vị RẺ**
  - **VẬT CHỨNG:** `289469d` · `tests/test_15_ba_test_don_vi_re.py` (138 dòng)
  - ✅ **PO TỰ CHẠY 25/08 06:10** — `6 passed in 1.32s`, venv có đủ deps
    *(dùng `P-121-new/.venv` hợp lệ: bộ test KHÔNG gọi model, đúng ngoại lệ `STATE.md` đã ghi —
    lệnh cấm nói về lệch `langchain-core` khi đo kích thích, trục không tồn tại ở test thuần)*
  - 🔴 **PO từng buộc tội ô này tick sai** — bằng một cửa sổ đo sai. Niêm ở sổ quyết định. — **QA/QC** · *Review đề xuất, PO duyệt*
  - `la_khieu_nai_ca_nhan` · `_otp_fresh(None, …)` → `False` · và bất biến
    **"mọi call site production của `run_agent_turn` phải truyền `otp_verified_at` tường minh"**
  - 🔴 Mục thứ ba là mục đáng giá nhất: hôm nay chỉ có **một** call site và nó đúng — nhưng
    **không cổng nào canh** việc ai đó thêm call site **thứ hai** mà quên truyền, và lúc ấy
    sentinel `_ALWAYS_FRESH` sẽ coi như **đã xác thực**. Đúng idiom introspect của
    `test_invariants.py`, không tốn LLM
  - **VẬT CHỨNG:** `tests/test_15_ba_test_don_vi_re.py`, 6 test, **chạy thật, 6/6 PASS**
    (`pytest tests/test_15_ba_test_don_vi_re.py -v`, 0 LLM/DB/Redis/docker):
    - 4 ca `la_khieu_nai_ca_nhan` (2 dương từ `bo_ca_am_thu_slot_dot2.json` đã xác nhận
      25/08, 2 âm từ `test_1a_luat_hoi_prompt.py` đã xác nhận) — tất cả khớp kỳ vọng
    - `_otp_fresh(None, 15) is False` — xác nhận trực tiếp
    - Bất biến call site: quét AST thật trên toàn `src/`, nhận diện được CẢ HAI hình
      dạng lời gọi (gọi thẳng `run_agent_turn(...)` VÀ gọi gián tiếp qua wrapper kiểu
      `_handle_tool_error(run_agent_turn, ..., otp_verified_at=...)` — hình dạng THẬT
      đang dùng ở `src/api/main.py:657`). **Đã tự kiểm cả hai chiều Luật A** trên 5 ca
      AST giả lập tách biệt (không chạy trong suite): gọi thẳng thiếu kw → bắt được ·
      wrapper thiếu kw → bắt được (ca nguy hiểm nhất, đúng hình dạng call site thật) ·
      call không liên quan → không báo oan. Có ràng buộc chống rỗng (Luật A): quét ra
      0 call site thì FAIL, không PASS-rỗng.

**Token delta của ④ = 0** *(điều khoản T2)* — ④ là early-return **trước** khi gọi LLM,
không chạm `build_system_prompt`. Review kiểm, PO ghi nhận.

⚠️ **Review khai việc chưa làm được:** không chạy lại `pytest` đầy đủ *(thiếu `argon2` trong
môi trường của họ — không phải lỗi ④)*. Bù bằng **đọc trực tiếp từng dòng mã cả ba nhánh**
thay vì tin số Coder báo. Khai ra thay vì im — đúng **Luật V**.


## Nhóm D — Đổi contract 🔒

- [!] **⑫** Loại khiếu nại thứ năm cho ca lừa đảo **K1** *(Q4 = A)* — **Coder** · chặn cứng, Coder chỉ tới bước 3 rồi DỪNG
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

## Trần ngân sách token — quyết định PO 25/08, vá cái ĐO không vá cái BỊ ĐO

> Phát hiện lúc land ④ (checklist ở mục ④ phía trên). `tests/test_inv_ngan_sach_token.py`
> đỏ: nền `NEN` ghi 4.587 token, thực tế 5.208 (lệch 13,5%) — phình từ R1-R5 + ADR-047
> (đã khai CÓ CHỦ Ý ở `7bd87d5`, nhưng khai trong commit message là **nới im lặng đối
> với người đọc cổng** — cổng không ai sửa theo).

**Quyết định: KHÔNG cắt prompt đợt này.** Lý do: (a) phần phình là yêu cầu nghiệp vụ thật
(kịch bản chuyên gia), không phải rác; (b) ⑨⑩⑪ CHƯA làm và cả ba đều THÊM chữ — cắt bây
giờ là cắt một mục tiêu đang chạy; (c) nền `NEN` hiện tại đã CHẾT (lệch 13,5%) — tối ưu
trên nền sai là đúng thứ Luật F cấm.

- [x] **T1** Cập nhật `NEN` về số đo thật; `NGUONG_TOKEN` giữ hay sửa thì **lý do PHẢI nằm
  TRONG cổng** (comment tại chỗ trong `tests/test_inv_ngan_sach_token.py`), không phải
  trong commit message — **QA/QC** thực hiện, **Coder cấp số đo thật**.
  - **VẬT CHỨNG:** commit `91acc62`. `NEN` mới: `system=5.275 · tool=1.982 · tổng=7.257`
    (96,1% trần 7.550). QA/QC tự đo độc lập, khớp tuyệt đối số Coder cấp. Nguyên nhân
    phình truy được **ngoài phạm vi đợt này** (2 commit trước ⑦: `5e8deb6` +67 system ·
    `6d0e3a9` +4 tool). **Quyết định ngưỡng (QA/QC): GIỮ NGUYÊN 7.550**, không tính lại
    theo nền mới — lý do trong docstring file (trần chống trôi neo cố định; tính lại theo
    nền mới là tự nới theo drift). Chạy thật: 2/3 pass, `test_bao_TRUOC_khi_cham_tran`
    (cảnh báo 90%) **đỏ ĐÚNG lý do** (đã ở 96,1%), không phải bug.
  - 🔴 **CHỈ CÒN 293 TOKEN (3,9%) DƯỚI TRẦN** — cảnh báo cho ⑨⑪ (còn lại của Nhóm C có khả
    năng thêm chữ prompt). **[Lead 25/08] KHÔNG chèn việc cắt prompt trước ⑨/⑪** — đúng
    tinh thần PO đã quyết (không tối ưu trên số chưa biết, Luật F). Thay vào đó: đã báo
    Coder viết kiệm chữ ngay từ đầu khi soạn ⑨/⑪, và **T2 là cơ chế bắt** — nếu delta cộng
    dồn chạm 293, đó là lúc quyết định thật (rút chữ hay nâng trần có lý do), với số thật
    thay vì đoán trước.
- [x] **T2** 🔴 **ĐIỀU KHOẢN MỚI, áp cho ⑨⑩⑪:** mỗi mục khi land phải BÁO DELTA TOKEN của
  prompt trong commit message. **Không có số ⟹ Lead không nhận mục đó là xong**, dù mã
  đã đúng — chi phí phải hiện ra ĐÚNG LÚC quyết định, không phải bị phát hiện sau bởi một
  cổng không ai chạy. *(Đã dispatch cho Coder — xem cảnh báo margin 293 token ở T1.)*
- [ ] **T3** Ghi nợ "cắt prompt" thành mục riêng cho **đợt SAU** — đo lại sau khi Nhóm C
  (⑨⑩⑪) land xong, trên nền đã cập nhật ở T1.
  - **[PO 25/08] ⑪ chính thức thuộc đợt này** — không phải nợ mới, là hạng mục đã hoãn
    (xem mục ⑪ phía trên).
- **Việc phụ, ngoài vùng ai trong đợt này:** container `fin05do-backend-1` stale
  (`BUILD_COMMIT` không khớp HEAD, không mount `src/` sống) — QA/QC phát hiện lúc chạy T1,
  ghi trong docstring, không tự sửa (ngoài vùng `tests/`). Ghi nợ cho `devops`, không chặn
  đợt này (không hạng mục nào đang dùng `fin05do`).

---

## CI/lint — Coder đo 25/08: không phải runner chết, ruff chặn pytest chạy

> Chi tiết đo trong `docs/STATE.md` (dòng "CI, từ 24/08"). Tóm tắt hành động:

- [x] **C1** QA/QC vá 17 lỗi ruff `eval/` — **4 file dễ, làm NGAY**: `benchmark.py` ·
  `do_cong_presence.py` · `run_adversarial_set.py` · `run_golden_set.py` (đều F541,
  `--fix` xử được).
  - **VẬT CHỨNG:** commit `94073cc`. `ruff check eval/{benchmark,do_cong_presence,
    run_adversarial_set,run_golden_set}.py` sạch. 2/4 lỗi do chính QA/QC gây lúc làm
    ① — Coder bắt ra, QA/QC tự nhận. `cong_phan_luong.py`/`do_cong_thu_tu.py` CHƯA đụng,
    đúng C2.
- [ ] **C2** 🔴 **`cong_phan_luong.py` + `do_cong_thu_tu.py` — CHỜ.** Đây là hai thước đo
  Coder đang DÙNG SỐNG để chấm ⑨/③ vòng 2. Đổi tên biến giữa lúc đo là "đổi vật giữa
  phép đo" — bài học đã trả giá nhiều lần trong đợt này. **QA/QC vá SAU khi Coder báo
  đã chấm xong ⑨ và ③ vòng 2**, không phải bây giờ.
- [~] **C3** [Lead 25/08] **DUYỆT**: sửa `ci.yml` để bước `pytest` chạy dù `ruff` đỏ
  (`if: always()` hoặc tách job riêng) — **Coder thực hiện** (vùng `.github/workflows/`,
  ADR-037 QĐ1), vì đây là quyết định Ý NGHĨA CỦA CỔNG nên Coder trình trước, không tự
  sửa. Lý do duyệt: lint (quy ước đặt tên) và test (đúng/sai hành vi) là hai trục khác
  nhau — để lint ẩn kết quả của 657 test là mất khả năng quan sát đúng lúc dự án cần nó
  nhất. Xác nhận xong khi có một run CI thật cho thấy pytest báo cáo dù ruff vẫn đỏ.
  *(3 job `ubuntu-latest` đỏ vì billing là sự cố KHÁC, chỉ PO thật gỡ — không đụng ở đây.)*
  - **VẬT CHỨNG (mã):** commit `0e8c398`. YAML parse sạch, đọc mã đúng ý — nhưng
    **CHƯA NGHIỆM THU ĐƯỢC**, giữ `[~]` không phải `[x]`.
  - 🔴 **[Coder 25/08 phát hiện] `git rev-list --left-right --count
    origin/dev/learning-loop...HEAD` → `0  47`** — nhánh đi trước origin 47 commit, lùi 0.
    **Toàn bộ đợt này chưa từng push.** Mọi run CI đã mổ (kể cả bằng chứng "17 lỗi ruff")
    chạy trên code CŨ HƠN, không phải code đợt này — "17" là DỰ BÁO, không phải phép đo
    đã xác nhận trên CI thật. Nghiệm thu C3 cần: push → đọc job `lint-and-test` → log có
    CẢ HAI (ruff ĐỎ **và** pytest có số báo cáo). Chi tiết: `docs/STATE.md` "CI, từ 24/08".
  - **Coder đúng khi không tự push** (thao tác ra ngoài, kích CI hạ tầng BTC, hiển thị
    ngoài đội) — đã chuyển PO thật qua PO agent, xem tin nhắn Lead→PO.

---

## Nghiệm thu cả đợt — bốn con số trong bốn tệp

- [!] **N1** Số lần cổng `thu_slot` bắn oan: **6/11** → **0/n** — **🔴 ĐÃ ĐO, KHÔNG ĐẠT**
  - **[Lead 25/08] ĐÍNH CHÍNH — không phải "chưa đo" như dòng cũ, là "đã đo, đỏ thật".**
    Bộ ca độc lập của QA/QC (7 ca, dựng từ đặc tả Đ1) nay 7/7 — đúng, và không sai — nhưng
    **xanh trên bản dựng lại không chứng minh gì về corpus gốc.**
  - **[ĐO thật, Coder]:** mẫu số **409 câu/14 tệp `eval/*.jsonl`**. Nền `a3bc860` thu_slot
    bắn **15** lần; HEAD hôm nay còn bắn **13** lần. **Chỉ đóng được 2** (= ADV-036 +
    ADV-038, khớp N2). 13 ca còn bắn oan: chính sách 2 · đã phân loại xong 2 · khách cần
    hướng dẫn 1 · khiếu nại thật ĐÚNG (không phải oan) 3 · khác/cần phân loại 5.
  - ⚠️ **"6/11" gốc và "15" (nền đo lại) CHƯA ĐỐI CHIẾU ĐƯỢC** — phương pháp bóc corpus gốc
    của Đ1 không rõ có khớp mẫu số 409 câu này không. **Không kết luận "6/11 sai"**, chỉ
    ghi "chưa so được", và nghiệm thu đang đứng trên một số chưa đối chiếu.
  - 🔴 **HỆ QUẢ:** đợt KHÔNG đóng được theo đúng tiêu chí phiếu §6 ("đợt đóng khi bốn con
    số nằm trong bốn tệp") — N1 là một trong bốn, và nó không đạt. Xem tin Lead→PO.
  - **[QA/QC 25/08] QUYẾT ĐỊNH — nhận script đo của Coder vào `eval/`:** `eval/do_n1_corpus_goc.py`.
    Tái lập ĐỘC LẬP, khớp tuyệt đối (409/15/13, cùng 13 câu). Đọc kỹ trước khi nhận: bộ
    bóc câu đã hỏng HAI LẦN lúc Coder dựng (7/409 rồi 349/409, cả hai lệch theo hướng
    TRẤN AN) — tự kiểm bằng dòng `if tong != 409`, giữ nguyên khi land.
    **GIỮ NGUYÊN quyết định của Coder: KHÔNG biến thành cổng pass/fail, luôn `return 0`.**
    Lý do (đồng thuận, không phải chỉ tin lời Coder): corpus sẽ lớn lên theo thời gian —
    ghim ngưỡng "13" sẽ đỏ mỗi lần ai thêm một câu hợp lệ, và một ngưỡng bị nới theo phản
    xạ thì thà không có (đúng bài học `XA_GIAO`/ngân sách token, đã lặp trong dự án này).
    **Cái ghim được là MẪU SỐ (409) và DANH SÁCH 13 câu** (chép vào docstring script,
    kèm phân loại Coder + QA/QC đối chiếu lại bằng mắt, khớp) — người chạy tự đối chiếu
    output với danh sách, câu MỚI không có trong đó là regression đáng báo ngay.
    **CHƯA làm** (ghi nợ, không phải chặn đợt): cơ chế DIFF tự động so với danh sách đã
    ghim (hiện đối chiếu tay) — nếu về sau lặp lại đối chiếu tay sai, đây là việc nâng cấp
    tiếp theo.
- [x] **N2** `ADV-036` · `ADV-038` xanh **vì** O1–O5 giữ được, không phải vì câu lạc đề
  - Cả hai đóng qua cơ chế đúng (không phải sửa test): AM-04=ADV-038 đóng vòng 1 (`d310dc5`),
    AM-03=ADV-036 đóng vòng 3 (`3e9a9ee`, trục chốt-không-bắn). Request nay tới LLM, đi qua
    O1-O5 thật — đúng ràng buộc N2 đòi.
- [ ] **N3** Lượt tốn token trước mốc OTP đo trên UI thật: **1** → **0**
- [ ] **N4** Cấu hình cờ in trong mọi báo cáo eval

🔴 **Đợt đóng khi bốn con số nằm trong bốn tệp, không phải khi bốn vai báo xong.**

---

## Phát hiện phụ 25/08 — không phải hạng mục, ghi để không mất

- **① Giả định xưng hô hẹp — hai module độc lập cùng lỗi.** `nguon_chi_dan` (8/10 cụm gõ
  cứng "tôi", 0/10 có em/con/cháu/mình) và `_SO_HUU` (chỉ tôi/mình) **cùng một giả định**:
  khách trẻ xưng "em", người lớn tuổi xưng "con/cháu" không bao giờ kích được tín hiệu. Đã
  vá data-only cho `nguon_chi_dan` (10→51 cụm, commit `3e9a9ee`), [ĐO] 6/6 đại từ bật đúng,
  ranh giới ADR-048 giữ nguyên. 🟡 **`_SO_HUU` VẪN MỞ** — PO hoãn có lý do trước đây, Coder
  không tự vá, nhưng nay không còn là lỗ lẻ: là nửa còn lại của cùng một giả định đã đo
  được ở hai chỗ. Ghi nợ.
- **③ có 3 giới hạn Review tìm — KHÔNG mở vòng 4.** PO tự thử tách một ca, bản thử hỏng
  ⟹ quyết định khai làm giới hạn đã biết của cơ chế, không tiếp tục vá.
- **Luật Y cấp ký hiệu** — xem `docs/STATE.md`, tổng quát hoá Luật L cho mọi cặp cơ chế
  bất đối xứng chi phí sai, không chỉ ngưỡng bộ dò.

---

## Sổ điểm danh

> PO ghi mỗi 15 phút. Cột "bằng chứng" là commit/tệp, **không phải lời khai**.

| giờ | HEAD | Lead | Coder | QA/QC | Review | ghi chú |
|---|---|---|---|---|---|---|
| — | `a3bc860` | chưa nhận | chưa nhận | chưa nhận | chưa nhận | phiếu vừa land |

---

## 📌 NGOÀI PHẠM VI ĐỢT NÀY — có chủ, không bỏ quên

- [ ] **NP-1 · Mảng mù theo XƯNG HÔ** *(Coder phát hiện, PO tái lập)*
  ```
  "tôi gửi nhầm cho bạn cùng lớp rồi ạ"    → thu_slot
  "em gửi nhầm cho bạn cùng lớp rồi ạ"     → day_du
  "cháu chuyển nhầm tiền rồi ạ"            → day_du
  "con chuyển nhầm cho người lạ rồi"       → day_du
  ```
  `_SO_HUU` chỉ có `tôi`/`mình`/`của tôi`/`tài khoản tôi`/`tk tôi`/`bên tôi`.
  🔴 **KHÔNG vá trong đợt này — sai thứ tự.** Thêm `em`/`cháu`/`con` là **NỚI** cổng, mà
  cổng đang bắn oan 2 ca. Nới một cổng đang bắn oan là nhân bản lỗi lên một lớp khách mới.
  Thứ tự đúng: chốt KHÔNG-BẮN land trước ⟹ cổng hết bắn oan ⟹ rồi mới nới xưng hô.
  ⚠️ **Đây không chỉ là chuyện token.** Cổng 0-token đang phục vụ người xưng `"tôi"` và
  không phục vụ người xưng `"em"`/`"cháu"`/`"con"` — phục vụ theo **xưng hô** chứ không
  theo **nội dung**. Trong một ví có khách mọi lứa tuổi, đó là chênh lệch **trải nghiệm**
  có hệ thống, không phải chênh lệch chi phí.

- [ ] **NP-2 · Ca đỏ có sẵn từ trước đợt** — *"Bạn tôi nói chưa nhận được khoản tôi gửi
  tuần này, tôi không nhớ rõ mã giao dịch."* → mong `day_du`, được `thu_slot`.
  Ca ✗ **duy nhất** trong 124 âm gốc, có từ trước ③ *(Review đo bit-for-bit giống nhau
  trước/sau `d310dc5`)*. Chưa ai nhận.

---

## 📂 Tường thuật đã chuyển chỗ — KHÔNG xoá

> 🔴 **Dọn 25/08.** Bảng này từng phình lên **742 dòng** — dài hơn cả phiếu giao việc
> (253) lẫn đặc tả nghiệp vụ (317) mà nó phục vụ, và Lead **không tìm được** hai hạng
> mục mới vì PO ném chúng vào đuôi một phụ lục. Đúng thứ `CLAUDE.md` §7b cảnh báo —
> *"một tài liệu không ai đọc hết có CÙNG TÁC DỤNG với không có tài liệu"* — và PO dựng
> ra nó **trong lúc trích §7b cho người khác**.
>
> Theo §7b: **chuyển chỗ + để đường dẫn, không xoá.** Bảng giữ phần *theo dõi*; phần
> *tường thuật* (đính chính · niêm · lý lẽ đổi quyết định · soát xét ④) chuyển sang:
>
> **`docs/nhat-ky/2026-08-25-so-quyet-dinh-dot-otp-truoc-token.md`**
>
> Vật chứng bản vá 7/7 bị từ chối: **`docs/nhat-ky/2026-08-25-ban-va-7-tren-7-bi-tu-choi.md`**
>
> Bằng chứng chi tiết của mỗi hạng mục nằm trong **commit message** của chính nó.
