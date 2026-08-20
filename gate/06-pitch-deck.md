# Pitch Deck — FIN-05 · Nội dung slide

> **Cách dùng:** mỗi mục `## Slide N` là một slide. Phần **nói** là lời bạn nói, không chiếu lên màn hình.
> Mọi con số đều truy được về một phép đo có file — nguồn ghi ngay dưới mỗi số.
>
> Ước lượng: **14 slide · 8–10 phút**. Cắt slide 11–12 nếu chỉ có 5 phút.

---

## Slide 1 — Bìa

**FIN-05 — AI Agent hỗ trợ CSKH ví điện tử xử lý khiếu nại giao dịch**

Đội T226 · AI 20K Build Phase, Cohort 3 (Vingroup × VinUni)
PO & thực hiện: Đào Ngọc Bích · Mentor: Đặng Hải Lộc · Đối tác nghiệp vụ: ZaloPay

> **Nói:** Một câu định vị sản phẩm — *"Agent điều tra khiếu nại. Agent không bao giờ quyết định."*
> Dừng một nhịp. Câu đó là toàn bộ thiết kế.

---

## Slide 2 — Bài toán

Khách khiếu nại một giao dịch. CSKH phải: tra đúng giao dịch giữa nhiều giao dịch **cùng số tiền,
cùng ngày** · đối chiếu chính sách · phân loại · đề xuất hướng xử lý.

**Mỗi khiếu nại là một cuộc điều tra thủ công, và mỗi phút chờ là một khách hàng đang mất tiền chưa biết vì sao.**

> **Nói:** Đây là nghiệp vụ có tiền thật. Sai một con số không phải là "câu trả lời kém" — là một
> khách được hứa hoàn tiền mà không ai duyệt.

---

## Slide 3 — Vì sao không phải "gắn thêm một con chatbot"

Ba thứ một chatbot thông thường làm được, và **không được phép** ở đây:

| chatbot thường | ví điện tử |
|---|---|
| đoán khi thiếu dữ liệu | **cấm tuyệt đối** — sai một con số tiền là sự cố |
| tự động hoá cho nhanh | **tiền chỉ đi khi người duyệt** |
| trả lời cho êm tai | **thà nói "không tra được"** còn hơn đoán |

> **Nói:** Ràng buộc quyết định kiến trúc, không phải ngược lại.

---

## Slide 4 — Năm ràng buộc cứng

```
1. HITL tuyệt đối     — không đường đi nào cho AI hoặc CSKH tự hoàn tiền
2. AI không vượt cấp  — AI gọi tool DƯỚI DANH NGHĨA customer, không có role riêng
3. Cấm bịa số liệu    — mọi con số phải truy về một tool_result có thật
4. OTP phiên làm việc — không bao giờ hỏi mật khẩu ví hay OTP giao dịch
5. Gắn cờ gian lận ≠ khoá ví — hai hành động độc lập hoàn toàn
```

**Cả năm được mã hoá thành 23 test** *(`tests/test_invariants.py`)*. **Đỏ = build hỏng.**

> **Nói:** Đây là slide quan trọng nhất. Điều khác biệt không phải chúng tôi *viết ra* năm ràng buộc —
> ai cũng viết được. Là chúng tôi **không thể vi phạm chúng mà build vẫn xanh**.

---

## Slide 5 — Cách chúng tôi làm ràng buộc không thể trôi

**Cấu trúc hệ thống sống trong `contracts/`, không sống trong code, không sống trong đầu ai.**

```
contracts/authority-matrix.yaml        34 route × role nào được gọi
contracts/agent-tools.yaml             5 tool được phép · 5 tool BỊ CẤM
contracts/resolution-state-machine.yaml vòng đời HITL
```

Test **introspect app đang chạy thật** — đọc `app.routes`, moi `allowed_roles` từ closure của
`require_role()`, đọc `CheckConstraint` qua AST, gọi thẳng `build_customer_tools()` — rồi so với contract.

**Thêm một route · đổi một guard · đổi tên một tool mà quên cập nhật contract ⟹ đỏ ngay.**

> **Nói:** Khác biệt với một tập tài liệu thường: tài liệu không tự biết mình đã cũ. Cái này biết.

---

## Slide 6 — Kiến trúc

*(chiếu sơ đồ trong `gate/02-kien-truc/so-do-kien-truc.md`, mục 1 và 2)*

```
khách → Cloudflare Tunnel → Caddy → Next.js BFF (JWT không rời server) → FastAPI
     → che PII → LLM (bể 4 model tự xoay) → 5 tool → lọc O1–O4 → khách
     search_policy → spotlighting: hạ tài liệu ĐỐI TÁC xuống hạng DỮ LIỆU (nhánh riêng)
     tiền chỉ đi khi Supervisor duyệt — ràng buộc người-tạo ≠ người-duyệt ở tầng DATABASE
```

> **Nói:** Chỉ ra **lưới cuối O1–O4** — regex tất định, **độc lập với model**. Đổi model không làm
> lưới yếu đi. Đó là lý do chúng tôi dám xoay model tự động.

---

## Slide 7 — Hạ tầng tự xoay model

Bể **4 model**, tên GHIM có mốc ngày:
`qwen3.7-plus-2026-05-26` · `deepseek-v4-pro-0813` · `deepseek-v4-flash-0731` · `deepseek-v3.2`

🔴 **Bí danh trôi bị TỪ CHỐI lúc khởi động.** ADR-043 loại 2/5 model PO gửi vì tên không mốc —
`deepseek-v4-pro` (không `-0813`) có thể trỏ sang PHIÊN BẢN MÔ HÌNH khác sau một đêm mà không ai biết.

Cạn hạn mức một model ⟹ **hạ tầng tự chuyển**, không ai phải sửa cấu hình lúc nửa đêm.

🔴 Xoay **chỉ** khi lỗi thuộc hạng hết-hạn-mức. **`429` không xoay** — nghẽn tạm thời không phải cạn hạn mức.

> **Nói:** Một chi tiết nhỏ nói lên cách đội làm việc: phân biệt được *"hết tiền"* với *"đang đông"*.
> Gộp hai cái đó lại thì hệ thống sẽ đốt sạch cả bể model chỉ vì một phút cao tải.

---

## Slide 8 — Chất lượng: đo bằng gì

| trục | ngưỡng | trạng thái |
|---|---|---|
| Bịa số liệu | **= 0** | có cổng, đỏ được |
| AI/CSKH tự hoàn tiền | **= 0** | 23 test invariant |
| Timeout một lượt | **≤ 45s** | ghim đúng số |
| Vòng ReAct | **≤ 20** | ghim đúng số |
| OTP xem / hành động | **≤ 12h / ≤ 15 phút** | test biên hai chiều |
| Bóp méo câu tiếng Việt | **≤ 6%** | **đo 1,6% (2/124)**, có cổng tự chấm lại |

**90 file test backend · 19 file E2E · 14 bộ dữ liệu đánh giá.**

> **Nói:** Chỉ vào dòng cuối. Bộ che PII từng bóp méo **50,8%** câu tiếng Việt đời thường — nuốt cả
> số tiền lẫn mã giao dịch. Tách hai đường xử lý theo mục đích, còn **1,6%**.

---

## Slide 9 — Điều chúng tôi CHƯA chứng minh được

**Chiếu nguyên slide này. Không lướt.**

- Điểm benchmark **87,7%** là mốc đo **16/08**, **không phải điểm của bản đang chạy**.
- Nó **loại trục Trải nghiệm (15đ)** khỏi mẫu số vì chưa hiệu chuẩn ⟹ **87,7% không nói gì về việc
  khách có dễ chịu khi nói chuyện với bot không.**
- Ngưỡng An toàn **chưa phủ** họ lỗi *"bịa có vỏ bọc sau một câu từ chối đúng"*.
- Trọng số 5 trục là **phán đoán chưa hiệu chuẩn**, không phải kết quả tính toán.

> **Nói:** Slide này để trong deck có chủ đích. Một đội đọc được giới hạn của chính con số mình đưa
> là một đội dùng được con số đó. Chúng tôi thà mất một slide đẹp còn hơn để ban giám khảo tự phát hiện.

---

## Slide 10 — Kỷ luật đo lường

**Trong một ngày, đội bắt được 9 khẳng định sống lâu hơn sự thật của nó.**

Không phải chín lời nói dối — chín câu **từng đúng**, rồi thực tế đi qua mà sổ sách không đi theo.

```
"Hai ca kiểm an toàn chưa chạy được"  → sai từ 5 ngày trước; chúng đã chạy và ĐẠT
"Bóp méo tiếng Việt 5,6%"             → đo trên một chữ ký hàm NAY KHÔNG CÒN TỒN TẠI
"Chín file mang nhãn chưa vá"          → thật ra MỘT; người đếm dùng sai công cụ
```

**Cả chín được niêm tại chỗ kèm bằng chứng, không xoá** — xoá đi thì phiên sau phát hiện lại từ đầu.

> **Nói:** Cái thứ ba là lỗi của chính tôi. Chúng tôi ghi tên người vấp vào luật, vì một luật rút từ
> lỗi của người điều phối mà giấu tên thì lần sau ai cũng tưởng nó chỉ áp cho cấp dưới.

---

## Slide 11 — Cách đội vận hành *(cắt được nếu thiếu giờ)*

**1 người thật + nhiều phiên AI chuyên trách**, mỗi vai một vùng ghi riêng:

```
tech-lead → src/, contracts/     tester → tests/, eval/  (CỐ Ý không được đọc src/)
security  → docs/security/       DevOps → Dockerfile, CI     critic → không ghi gì
```

🔴 **Vì sao tester không được đọc `src/`:** cho tester đọc code thì test nó viết sẽ **phản chiếu logic
đang có — kể cả logic sai**. Kết quả là một suite xanh mướt chứng minh rằng bug hoạt động đúng như bug.

> **Nói:** Đây là kiến trúc **đối kháng**, không phải phân công cho gọn. Hôm 20/08, tester bác một kết
> luận của tôi bằng bằng chứng — và họ đúng.

---

## Slide 12 — Sẵn sàng production *(cắt được nếu thiếu giờ)*

```
12-factor config · secret fail-fast · multi-stage Docker · non-root
graceful shutdown · state dùng chung (scale ngang được)
CI: ràng buộc cứng · contract drift · appsec · migration-chain
```

**Diễn tập deploy trên bản clone sạch tìm ra 6 chỗ đứt** — không chỗ nào phát hiện được bằng cách
đọc lại tài liệu. Hai chỗ nguy hiểm nhất **không có triệu chứng gì**: `/health` xanh cả khi backend
đã chết, và một biến môi trường thiếu làm mở toàn bộ tài liệu API ra Internet.

> **Nói:** Người viết tài liệu không thể tự thấy thứ máy mình đã có sẵn. Chỉ một bản clone sạch nói ra được.

---

## Slide 13 — Demo

*(chuyển sang video hoặc thao tác thật)*

**Luồng:** khách chat khiếu nại → agent gọi tool điều tra, tìm **đúng** giao dịch giữa nhiều giao dịch
cùng số tiền → tạo vé → CSKH tiếp nhận, xem dòng thời gian điều tra (**không có nút duyệt**) → Supervisor
mở hồ sơ, đọc căn cứ, duyệt bằng OTP step-up → khách nhận kết quả.

**Điểm cần chỉ ra khi demo:** màn hình CSKH **không có nút duyệt**. Đó không phải thiếu tính năng — đó là ràng buộc cứng số 1.

---

## Slide 14 — Chốt

**Agent điều tra. Người quyết định. Mọi con số truy được về nguồn.**

Ba thứ để lại: **contract tự bắt lệch** · **guardrail độc lập với model** · **kỷ luật niêm số sai
thay vì xoá**.

> **Nói:** Chúng tôi không xây một con bot trả lời hay. Chúng tôi xây một hệ thống mà **khi nó sai,
> ta biết ngay và biết vì sao**.

---

## Phụ lục — số liệu, nếu bị hỏi

```
982 commit · 3 tuần        46 ADR có ghi lý do BÁC phương án khác
34 route trong contract    5 tool được phép · 5 tool bị cấm tuyệt đối
90 file test backend       19 file E2E Playwright · 14 bộ dữ liệu eval
23 test ràng buộc cứng     introspect app đang chạy thật, không đọc code tĩnh
```

**Nếu bị hỏi *"đã deploy thật chưa"*:** trả lời thẳng theo trạng thái tại thời điểm trình bày.
Sổ tay deploy đã có, 6 bước đã có người đi hết trên bản clone sạch, 6 chỗ đứt đã vá.


---

## ⚠️ KIỂM TAY TRƯỚC KHI NỘP — file này nằm NGOÀI cơ chế tự canh

`gate/MANIFEST.md` ghi băm sha256 để phát hiện bản sao đã trôi. **File này không có bản gốc nơi
khác, nên nó KHÔNG nằm trong bảng băm đó** — không cơ chế nào báo khi nó nói sai.

Ba thứ đối chiếu tay, mất một phút:
```bash
grep LLM_MODEL_POOL .env                 # tên model — phải KHỚP, KỂ CẢ mốc ngày
grep -c '^## ADR-' docs/DECISIONS.md     # số ADR
git log --oneline | wc -l                # 🔴 TỔNG commit — so 1 số với 1 số
gh pr list --state merged --limit 50 | wc -l                     # số PR đã merge
find src -name '*.py' | wc -l ; find tests -name 'test_*.py' | wc -l   # số file
git log --format='%ad' --date=format:'%Y-W%V' | sort | uniq -c   # commit mỗi TUẦN
```

🔴 **Vì sao lệnh `wc -l` cho TỔNG là lệnh quan trọng nhất ở đây, không phải lệnh cuối:**
lệnh cuối cho ra **bảng theo tuần** — người kiểm phải **tự cộng ba dòng** rồi mới so được với con số
ở đầu file. **Đó chính xác là bước đã sai** (tiêu đề ghi `982`, bảng cộng ra `984`). Tái tạo đúng
phép đo mà không bỏ được bước cộng tay thì cổng kiểm vẫn hở ở đúng chỗ nó từng hở.
**So một số với một số, đừng bắt người kiểm làm phép tính.**
🔴 **Ca thật 20/08:** ba file trong `gate/` từng ghi bể model là `deepseek-v4-pro` / `deepseek-v4-flash`
— **đúng hai bí danh mà ADR-043, nằm chung hồ sơ, đã tường minh TỪ CHỐI vì không có mốc ngày.** Hồ sơ
tự mâu thuẫn ngay trên chủ đề nó dùng làm điểm nhấn. Review bắt được; không cơ chế nào bắt được.
