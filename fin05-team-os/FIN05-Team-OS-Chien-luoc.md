# Team-OS: Vận hành Claude như một đội nhóm hoàn chỉnh
### Góc nhìn chuyên gia cho FIN-05 — 1 PO + Claude, deadline 2 tuần

---

## 0. Tóm tắt cho người bận

Vấn đề bạn gặp — *"Claude tech lead đổi cấu trúc, Claude tester và Claude bảo mật không biết, tôi phải bảo tech lead viết file md tóm tắt"* — không phải lỗi prompt. Nó là **lỗi kiến trúc thông tin**. Bạn đang mô phỏng *cuộc trò chuyện giữa hai người*, thứ dễ vỡ nhất trong mọi đội.

Cách sửa gói trong một câu:

> **Đừng để agent kể cho nhau nghe. Hãy để agent cùng đọc một nguồn sự thật, và để máy phát hiện khi ai đó lệch khỏi nó.**

Cụ thể: cấu trúc hệ thống không sống trong đầu tech lead, nó sống trong `contracts/`. Tech lead muốn đổi cấu trúc → sửa `contracts/` trước, code sau. Tester sinh test **từ `contracts/`**, không từ code. Security audit **đối chiếu `contracts/`**. Một script băm hash các file contract; artifact nào được sinh từ hash cũ sẽ bị đánh dấu *stale* và CI đỏ.

Không ai phải nhớ báo cho ai nữa. Đó là toàn bộ ý tưởng.

---

## 1. Chẩn đoán: vì sao mô hình "đội Claude" thường thất bại

Hầu hết mọi người dựng đội agent bằng cách **copy sơ đồ tổ chức**: một PO, một BA, một Dev, một QA. Rồi thất vọng vì kết quả rời rạc.

Lý do: sơ đồ tổ chức không phải là thứ làm một đội hoạt động. Trong đội người thật, thông tin **không** truyền qua việc người này kể cho người kia — cách đó thất bại liên tục, đó là lý do có Jira. Thông tin truyền qua ba thứ:

| Cơ chế | Trong đội người | Tương đương trong đội agent |
|---|---|---|
| **Artifact chuẩn hoá** | PRD, API spec, DB schema, ticket | `contracts/`, `docs/DECISIONS.md`, `docs/STATE.md` |
| **Cổng kiểm** | Code review, Definition of Done, CI đỏ | Gate checklist trong prompt + `tests/test_invariants.py` |
| **Vòng phản hồi** | Test fail, bug report, retro | `check_contracts.py`, golden_set scoring, critic agent |

Khi bạn bảo tech lead "viết file tóm tắt cho tester đọc", bạn đang thay thế cả ba cơ chế trên bằng **trí nhớ và thiện chí của một agent**. Trong đội người thật cách này vỡ vì người ta quên. Trong đội agent nó vỡ nặng hơn: agent không có động cơ nào để nhớ, và cửa sổ ngữ cảnh reset sạch mỗi phiên.

Có một nghịch lý cần nhìn thẳng: **agent càng giỏi, drift càng nguy hiểm.** Một tech lead kém sẽ code sai rõ ràng và bạn phát hiện ngay. Một tech lead giỏi sẽ tự ý "cải tiến" cấu trúc theo hướng hợp lý hơn, code chạy được, và bạn chỉ phát hiện ba ngày sau khi tester viết 40 testcase cho một API không còn tồn tại.

---

## 2. Bảy nguyên lý

### NL1 — Hợp đồng thay vì bản tin *(contract over broadcast)*

**Đây là nguyên lý trả lời trực tiếp điểm đau của bạn.**

Quy tắc: **agent không được phép thay đổi cấu trúc; agent chỉ được phép thay đổi hợp đồng.**

- Tech lead phát hiện thiết kế cần đổi (ví dụ: ticket cần thêm trạng thái `pending_bank`) → **không sửa code trước**. Sửa `contracts/ticket-state-machine.yaml`, ghi 1 dòng ADR, rồi mới code.
- Tester **không bao giờ đọc code implementation**. Sinh testcase từ `contracts/` + PRD.
- Security **không bao giờ đọc code trước**. Đối chiếu `contracts/authority-matrix.yaml` với PRD §4, rồi mới xuống code kiểm chứng.

Cơ chế phát hiện lệch — phần khiến nó chạy được thật:

```
scripts/check_contracts.py
  → băm SHA256 từng file trong contracts/
  → so với .claude/state/contract-hashes.json (hash mà mỗi artifact hạ nguồn đã dùng)
  → in ra: "authority-matrix.yaml ĐÃ ĐỔI. Artifact stale: tests/test_authority.py, docs/security-review.md"
  → exit code 1 → CI đỏ
```

Bạn không còn phải nhắc ai cả. Máy nhắc.

> **Cách nghĩ đúng:** contract là *ranh giới*, không phải *tài liệu*. Tài liệu mô tả cái đã có. Contract quy định cái được phép có. Sửa contract là một hành động có nghi thức (cần ADR + bạn duyệt); sửa tài liệu thì không.

---

### NL2 — Ngữ cảnh nằm trong repo, không nằm trong trí nhớ

Chia ngữ cảnh dài hạn thành **ba tầng theo tần suất thay đổi**. Trộn chung là sai lầm phổ biến nhất — file phình lên rồi agent bắt đầu bỏ qua nó.

| Tầng | File | Tần suất đổi | Trần độ dài | Ai được ghi |
|---|---|---|---|---|
| **Hiến pháp** | `CLAUDE.md` | Gần như không | **≤ 200 dòng** | Chỉ bạn |
| **Quyết định** | `docs/DECISIONS.md` | Vài lần/tuần, **chỉ ghi thêm** | Không giới hạn | Agent đề xuất, bạn duyệt |
| **Trạng thái** | `docs/STATE.md` | Cuối mỗi phiên, **ghi đè** | ≤ 60 dòng | Agent cuối cùng làm việc |

**Quy tắc vàng:**

> Nếu một quyết định chưa nằm trong repo thì nó **chưa tồn tại**.

Bạn nói với Claude "ừ chốt vậy đi" trong chat — không tính. Phiên sau nó biến mất. Mọi lần bạn chốt điều gì, phản xạ phải là gõ `/adr`. Mất 30 giây, tiết kiệm nửa ngày kể lại.

Vì sao ADR **chỉ ghi thêm, không sửa**: bạn cần biết *tại sao* đã từng quyết định ngược lại. Chính dự án của bạn có ví dụ hoàn hảo — ban đầu thiết kế cho CSKH tự duyệt case nội bộ ví, sau sửa thành sếp duyệt mọi phạm vi. Nếu chỉ ghi kết quả cuối, ba tuần nữa sẽ có agent "tối ưu" nó trở lại, vì để CSKH tự duyệt trông hợp lý hơn về UX. ADR ghi rõ *lý do bác bỏ* là thứ chặn vòng lặp đó.

---

### NL3 — Ràng buộc cứng phải là **test**, không phải là **lời dặn**

Một dòng prompt "AI không bao giờ được tự duyệt hoàn tiền" là một lời đề nghị rất mạnh. Mô hình sẽ tuân khoảng 95–99% số lần. Với một sản phẩm tài chính đem đi pitch trước doanh nghiệp ví điện tử, con số đó là **hỏng**.

Một test là 100%:

```python
def test_no_approval_path_bypasses_supervisor():
    """PRD §4.1 — HITL tuyệt đối."""
    for route in app.routes:
        if route.effects_balance:
            assert route.required_role == "supervisor"
```

Quy đổi thẳng ba ràng buộc của bạn (card S2-03) sang test — file `tests/test_invariants.py` trong gói này đã dựng sẵn khung:

| Ràng buộc PRD | Test |
|---|---|
| HITL tuyệt đối — chỉ sếp duyệt, mọi phạm vi | Quét mọi route đổi số dư → bắt buộc role `supervisor` |
| AI không vượt cấp CSKH | Quét mọi transition escalate → phải qua state `cskh_received` |
| Cấm bịa số liệu | Mọi con số trong phản hồi agent phải truy vết được tới `tool_call_id` |

**Đây còn là vũ khí pitch.** Ở tuần 6, khi chuyên gia ví điện tử hỏi "làm sao đảm bảo AI không tự ý hoàn tiền?", câu trả lời mạnh nhất không phải một slide. Là mở terminal, chạy `pytest tests/test_invariants.py`, 3 dòng xanh. Rất ít đội sinh viên làm được điều đó.

---

### NL4 — Luồng một chiều + cổng vào

```
   BẠN (PO thật)
      │  duyệt ADR · duyệt contract · duyệt phạm vi
      ▼
  ┌────────┐   ┌────────┐   ┌───────────┐   ┌────────────────┐   ┌────────┐
  │   PO   │──▶│   BA   │──▶│ TECH LEAD │──▶│ TESTER·SECURITY│──▶│ CRITIC │
  └────────┘   └────────┘   └───────────┘   └────────────────┘   └────────┘
   brief/PRD    US + AC       contracts       test + audit        bác bỏ
                              rồi mới code    (mù code)
      ▲                                                              │
      └──────────────────── trả về nếu cổng vào không đạt ◀──────────┘
```

Mỗi agent có **cổng vào**: danh sách điều kiện input phải thoả trước khi được bắt đầu. Không thoả → **trả về thượng nguồn, không tự đoán**.

Ví dụ cổng vào của Tech Lead:
- [ ] US có mã (US-0xx) và đầy đủ AC dạng Given/When/Then
- [ ] AC nào chạm tiền phải nêu rõ ai duyệt
- [ ] Contract liên quan đã tồn tại hoặc US ghi rõ cần thêm contract mới

Đây chính là thứ biến *một người + AI* thành *một đội*: **AI bắt lỗi AI**. Nếu agent nào cũng "cố gắng hữu ích" và tự lấp chỗ trống, bạn không có đội — bạn có bốn agent cùng bịa theo bốn hướng khác nhau, và bạn là người duy nhất phải hoà giải.

Câu lệnh nên có trong **mọi** agent:

> *Thiếu thông tin thì DỪNG và hỏi. Tuyệt đối không suy đoán để lấp chỗ trống. Trả về thượng nguồn kèm câu hỏi cụ thể.*

Để ý sự trùng khớp: đây đúng là ràng buộc "cấm bịa số liệu" trong sản phẩm của bạn, áp cho quy trình làm ra sản phẩm. Quy trình và sản phẩm cùng một triết lý — điều này không chỉ đẹp, nó khiến bạn kể câu chuyện pitch mạch lạc hơn nhiều.

---

### NL5 — Người kiểm không được là người làm

**Tester không đọc code implementation.** Chỉ đọc PRD + `contracts/` + `eval/golden_set.jsonl`.

Lý do không phải hình thức. LLM bám cực chặt vào văn bản nó vừa đọc. Cho tester đọc code, test nó viết sẽ **phản chiếu** logic đang có — kể cả logic sai. Bạn sẽ nhận một suite 60 test xanh mướt chứng minh rằng bug hoạt động đúng như bug.

Thực thi bằng cách giới hạn `tools:` trong frontmatter của sub-agent, không phải bằng cách dặn dò. Tester chỉ được `Read` trong `docs/`, `contracts/`, `eval/`, `tests/`.

**Critic agent** là vai thứ hai của nguyên lý này. Nhiệm vụ duy nhất: **bác bỏ**. Prompt phải hướng phủ định — *"tìm ba lý do thiết kế này SAI"* — vì câu hỏi *"cái này ổn chứ?"* gần như luôn nhận lại "ổn, rất tốt!". Đây là thiên lệch mạnh nhất và nguy hiểm nhất khi làm việc một mình với AI: bạn mất đi người đồng nghiệp cau mày.

---

### NL6 — Cửa sổ ngữ cảnh là **ngân sách**, không phải kho chứa

Một agent to biết mọi thứ luôn thua năm agent hẹp. Không phải vì "chuyên môn hoá" — dưới nắp capo vẫn là cùng một mô hình. Mà vì **tỉ lệ tín hiệu trên nhiễu**: khi 80% ngữ cảnh không liên quan tới việc đang làm, chất lượng suy giảm rõ rệt và mô hình bắt đầu lôi chi tiết từ phần không liên quan vào.

Chia vai, xét cho cùng, là **kỹ thuật quản lý ngữ cảnh** được nguỵ trang thành sơ đồ tổ chức.

Hệ quả thực hành:
- **Một phiên = một nhiệm vụ.** Xong thì `/wrapup` rồi mở phiên mới. Đừng kéo một phiên 4 tiếng qua nhiều việc — nửa sau chất lượng rơi thấy rõ.
- Sub-agent chạy trong cửa sổ riêng và chỉ trả về kết luận. Đây là lý do dùng sub-agent thay vì "đóng vai" trong cùng một phiên: đóng vai không tách được ngữ cảnh, chỉ đổi giọng văn.

---

### NL7 — Bạn là HITL. Hãy giữ đúng vai.

| Bạn **phải** duyệt | Bạn **không nên** duyệt |
|---|---|
| Thay đổi `contracts/` | Tên biến, cấu trúc thư mục con |
| ADR mới | Cách viết một testcase cụ thể |
| Thay đổi phạm vi sprint | Format log, comment |
| Bất cứ gì chạm ràng buộc cứng | Refactor nội bộ không đổi contract |

Duyệt mọi thứ → bạn thành cổ chai, tốc độ về 0. Không duyệt gì → drift, tuần sau phát hiện sản phẩm đã đi chệch.

Lại một trùng khớp đáng nói: bảng trên **chính là ma trận thẩm quyền** trong sản phẩm bạn đang xây. Bạn = sếp duyệt. Agent = CSKH điều tra, đề xuất, không quyết. Nếu bạn muốn một câu mở đầu cho buổi pitch tuần 6: *"Chúng tôi xây một sản phẩm HITL bằng một quy trình HITL."*

---

## 3. Nhịp vận hành

**Đầu ngày — `/standup` (~5 phút).** Đọc `STATE.md` + 5 ADR gần nhất + chạy `check_contracts.py`. Trả về: đang dở gì, có gì stale, đề xuất 3 việc hôm nay. Bạn chọn.

**Trong ngày — 1 đến 3 phiên nhiệm vụ.** Mỗi phiên gọi đúng một agent chính. Bắt đầu bằng `/gate <role>` để kiểm tra input đủ chưa.

**Cuối ngày — `/wrapup` (~5 phút).** Cập nhật `STATE.md`, ghi ADR phát sinh, cập nhật contract-hashes, commit. **Đừng bỏ bước này** — nó chính là thứ chống mất ngữ cảnh giữa các phiên.

**Cuối tuần — `/impact` + critic quét toàn bộ.** Critic đọc PRD + contracts + test và tìm mâu thuẫn. Mỗi lần chạy hãy kỳ vọng 2–5 phát hiện thật; nếu ra 0, prompt critic của bạn đang quá lễ phép.

---

## 4. Sai lầm thường gặp và cách chặn

| Triệu chứng | Nguyên nhân thật | Cách chặn |
|---|---|---|
| Agent đồng ý với mọi thứ bạn nói | Không có vai đối kháng | Thêm critic, prompt hướng phủ định |
| Tài liệu phình, agent bắt đầu lơ | Trộn 3 tầng ngữ cảnh vào một file | Trần 200 dòng cho `CLAUDE.md`, tách STATE/DECISIONS |
| Test xanh nhưng sản phẩm sai | Test viết sau code, bởi người viết code | Test viết trước, từ contract, bởi agent mù code |
| Hai agent sửa hỏng file của nhau | Không phân vùng quyền ghi | Mỗi agent sở hữu thư mục riêng (bảng ở `HANDOFF-PROTOCOL.md`) |
| Sửa hỏng, không quay lại được | Không có checkpoint | Mỗi phiên = 1 branch + commit `checkpoint:` ngay khi mở |
| Nhắc lại điều đã chốt nhiều lần | Quyết định chỉ tồn tại trong chat | `/adr` ngay khi chốt, không để sau |
| Tuần 5 mới phát hiện AI vi phạm HITL | Ràng buộc chỉ nằm trong prompt | `tests/test_invariants.py` chạy trong CI từ ngày 1 |

---

## 5. Đo lường: bốn con số nên theo dõi

1. **% test bất biến pass** — phải luôn là 100%. Đây là chỉ số duy nhất không được phép thoả hiệp.
2. **Điểm golden_set / heldout_set** — bạn đã có sẵn 120/60 case có nhãn. Chạy tự động mỗi commit, vẽ đường theo thời gian. Đây là bằng chứng định lượng mạnh nhất khi pitch.
3. **Số lần contract stale bị `check_contracts.py` bắt** — chỉ số sức khoẻ quy trình. Con số > 0 là **tốt** (cơ chế đang hoạt động); con số 0 kéo dài nghĩa là bạn quên cập nhật hash, không phải mọi thứ hoàn hảo.
4. **Số lần bạn phải nhắc lại một điều đã chốt** — mục tiêu 0. Mỗi lần > 0 là một ADR còn thiếu. Đây là chỉ số trực tiếp cho điểm đau bạn nêu.

---

## 6. Áp vào FIN-05: đề xuất 10 ngày còn lại

| Ngày | Việc | Agent chính |
|---|---|---|
| 1 | Cài Team-OS, viết `contracts/` từ PRD 2.1 hiện có, viết 3 test bất biến | Tech Lead + bạn |
| 1 | Ghi ADR hồi tố cho 8 quyết định trong PRD §4 (quan trọng: chặn agent "tối ưu" ngược) | PO |
| 2–3 | Tech Lead code API theo contract; Tester song song viết testcase từ contract (mù code) | Tech Lead ∥ Tester |
| 4–5 | Tích hợp AI agent + tool; nối `eval/golden_set.jsonl` vào script chấm tự động | Tech Lead |
| 6 | Security audit đối chiếu authority-matrix; critic quét toàn bộ | Security + Critic |
| 7 | Sửa theo phát hiện; chạy heldout_set lần đầu (chỉ 1 lần — giữ tính "held-out") | Tech Lead |
| 8 | Demo lớp; ghi phản hồi thành ADR | Bạn |
| 9–10 | Slide + video; dựng phần "bằng chứng kỹ thuật": test bất biến xanh + biểu đồ điểm eval | PO + bạn |

Một lưu ý về heldout_set: đội bạn đã tách 60 case held-out rất bài bản. Hãy chỉ chạy nó **một lần duy nhất, gần cuối**. Chạy lặp lại rồi sửa theo kết quả là tự làm rò rỉ tập kiểm định, và mất đúng thứ giá trị nhất bạn có để trả lời câu hỏi *"làm sao biết nó thật sự đúng?"*.

---

## 7. Giới hạn của cách làm này — nói thẳng

- **Không thay được kiểm thử với người thật.** Testcase sinh từ contract bắt được lỗi logic, không bắt được "giọng văn này khiến khách hàng đang bực càng bực hơn". Với một sản phẩm mà lợi thế cạnh tranh là *giọng văn xoa dịu*, bạn cần vài người thật đọc thử — chi phí thấp, giá trị cao.
- **Contract chỉ đúng bằng PRD.** Nếu PRD sai nghiệp vụ thì cả bộ máy này sẽ thực thi cái sai một cách rất kỷ luật. Bảy câu hỏi mở dành cho chuyên gia (PRD §8) vẫn là ưu tiên số một; không cơ chế kỹ thuật nào trả lời thay được.
- **Chi phí cố định của quy trình.** Ngày đầu tiên gần như không ra tính năng nào. Với deadline 2 tuần điều đó nghe đáng sợ, nhưng điểm hoà vốn rơi vào khoảng ngày 3–4, và phần lớn thời gian tiết kiệm được đến từ đúng chỗ bạn đang đau: không phải kể lại ngữ cảnh, không phải tự làm liên lạc viên giữa các agent.
- **Đây là mô hình dựa trên kinh nghiệm vận hành, không phải kết quả nghiên cứu đã kiểm chứng.** Hãy sửa nó theo thực tế của bạn thay vì tuân thủ nguyên văn.

---

*Kèm theo tài liệu này là bộ file cấu hình chạy được ngay — xem `README.md` trong cùng gói.*
