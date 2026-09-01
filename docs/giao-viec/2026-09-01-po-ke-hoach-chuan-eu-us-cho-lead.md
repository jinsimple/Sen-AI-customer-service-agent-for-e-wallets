# KẾ HOẠCH — ĐỢT "CHỊU ĐƯỢC DUE-DILIGENCE"

> **Từ:** phiên PO (vai PO fintech/ví điện tử) · **Cho:** Lead · **Ngày:** 01/09/2026
> **Người quyết cuối:** PO thật (Đào Ngọc Bích). Tôi chốt **phạm vi và thứ tự**, không chốt
> tiền · khoá bí mật · push production · đổi contract.
>
> Thay thế phần thứ tự ưu tiên của `2026-08-30-po-ke-hoach-tong-quan-doi-moi.md`.
> Làn A/B/C/D của bản 30/08 **đã đóng phần lớn** — xem §1. Bản này mở đợt kế tiếp.

---

## 0. Một đoạn — kết luận của tôi sau khi đo

Dự án này có **kiến trúc bằng chứng tốt hơn hẳn mặt bằng MVP fintech** — contract introspect
app đang chạy, maker–checker ép ở tầng CHECK constraint, truy vết cấp dòng dữ liệu,
dynamic-linking OTP đúng RTS Điều 5. Đó là thứ **không được phá** trong bất kỳ đợt nào sau đây.

Nhưng nếu ngồi trước đội due-diligence của một ví điện tử EU/US **hôm nay**, ta thua ở ba chỗ,
và **không chỗ nào là lỗi thiết kế**:

1. **Không ai chứng minh được thứ đang chạy là thứ trong repo.** Nhánh `dev/learning-loop`
   đi trước `main` **213 commit**, trước `origin/main` **145 commit**. Production đang LIVE
   trên máy Windows của PO. Câu *"cho xem quy trình quản lý thay đổi"* (SOC 2 CC8.1, DORA
   Điều 8-9) hiện **không có câu trả lời**.
2. **Các cổng đo — thứ toàn bộ lập luận của dự án dựa vào — hiện KHÔNG MANG THÔNG TIN.**
   E2E 19 test / 11 đỏ, đỏ toàn vì môi trường. Golden **0/120 và 0/60** không phủ tool nào,
   tức bộ đề không đo đúng thứ sản phẩm là. Một cổng (`must_create_manual_ticket`) **chưa
   dòng nào từng đọc field của chính nó**. Dự án đã tự đặt tên cho lỗi này ngày 01/09:
   *cổng hằng XANH sống được nhiều tháng*.
3. **🔴 Đồng hồ pháp lý của chính sản phẩm chưa từng được benchmark.** Xem §3 — đây là phát
   hiện nặng nhất của tôi, và nó **không nằm trong bản rà soát 27/08**.

---

## 1. Tôi đã đo gì — lệnh + kết quả, 01/09/2026

| đo | kết quả |
|---|---|
| `python3 scripts/check_contracts.py` | 3/3 contract **khớp baseline**, không artifact lỗi thời |
| `grep '"otp_code"' src/api/main.py` | `:452` `:999` — **đã vào trong `if OTP_DEMO_MODE`**, `config.py:199` fail-fast khi `APP_ENV=production` ⟹ **A1 ĐÃ VÁ** |
| `grep compare_digest src/api/main.py` | `:492` `:1077` ⟹ **A2 ĐÃ VÁ** |
| `grep -E 'HSTS\|CSP\|X-Frame-Options' Caddyfile` | **0** ⟹ ⑤ header bảo mật **VẪN CHƯA LAND** (treo từ 27/08) |
| `git rev-list --count main..HEAD` | **213** · `origin/main..HEAD` = **145** |
| `grep -rl '91/2025' docs/` | 10 tệp ⟹ **C1/C2 đã làm**; nhưng `13/2023` còn ở **42 tệp** (phần lớn là lịch sử đã niêm — cần Bảo mật phân loại, không xoá) |
| `ls docs/security/*C3* *C4*` | IR runbook + DPIA **có bản DRAFT**, chưa phê duyệt |
| `grep -E 'sla\|due_at\|provisional' src/db/models.py` | **đúng 1 trường**: `Ticket.sla_due_at` — xem §3 |
| đếm | 56 file `src/*.py` · 102 file test · 38 file e2e · 56 ADR · 1.525 commit |

**Số CŨ cần niêm lại:** kho `project-knowledge/` đang chụp tại commit `961fc24` (24/08) —
**cũ 407 commit**. Băm `agent-tools.yaml` trong kho ghi `00239f9f0bfc`, thực tế nay là
`df6e7c9353d3`. **Mọi phiên Claude đọc kho đó đang cầm bản đồ chết.** Việc đầu tiên của đợt này.

---

## 2. Thứ KHÔNG được đụng — tài sản thật của dự án

Bất kỳ đề xuất nào làm suy yếu một trong các mục dưới đây, **Lead trả lại ngay**, không cần hỏi tôi:

- `tests/test_invariants.py` introspect app đang chạy (23 test / 5 ràng buộc cứng).
- Maker–checker ở tầng `CheckConstraint`, **không** hạ xuống tầng ứng dụng.
- `tool_results → investigation_logs → resolutions.cited_tool_result_ids`.
- Dynamic-linking OTP duyệt (`resolution_id` + `amount_snapshot`) — đây là thứ **đúng chuẩn
  RTS Điều 5** và hiếm gặp ở MVP.
- Việc đã gỡ KBA khỏi vai trò authenticator (đi trước NIST 800-63B-4).
- Tester **không đọc `src/`**. Kiến trúc đối kháng, không phải phân công cho gọn.

---

## 3. 🔴 PHÁT HIỆN NẶNG NHẤT — đồng hồ pháp lý của sản phẩm chưa từng được benchmark

Bản rà soát 27/08 benchmark **các chuẩn BẢO MẬT** (PSD2-SCA · GDPR · PCI · NIST · FFIEC ·
ISO/SOC2 · AML). Nó làm tốt việc đó. Nhưng nó **không benchmark quy chế của chính nghiệp vụ
sản phẩm này đang làm** — và FIN-05 không phải một hệ thống bảo mật, nó là một **máy xử lý
khiếu nại giao dịch**. Quy chế của nghề đó là thứ đội due-diligence sẽ hỏi trước tiên.

**Trạng thái đo được:**

```
src/tools/sla.py   compute_sla_due_at(created_at, scope)
                   from_bank/to_bank → 4 NGÀY LÀM VIỆC
                   còn lại           → 30 NGÀY
src/config.py:166  "# BR-01/BR-02: trần pháp lý ... verified: false"
src/tools/sla.py   "ngày làm việc = T2-T6, bỏ qua ngày lễ VN (bản demo bỏ qua lễ)"
```

Bốn vấn đề, xếp theo độ nặng:

**① Toàn bộ đồng hồ pháp lý là MỘT cặp số Việt Nam, tự khai `verified: false`.**
Chưa ai đối chiếu với văn bản gốc — chính chú thích trong code nói thế. Một con số
`verified: false` nằm trên đường chạy thật, được agent **đọc ra cho khách** (`prompt.py:49`),
là thứ tệ hơn không có số: nó là **lời hứa pháp lý chưa ai kiểm**.

**② Không có chiều TÀI PHÁN (jurisdiction) trong mô hình dữ liệu.**
Một ví điện tử EU/US không dùng cặp số đó. Các mốc cần Bảo mật **xác minh nguyên văn** trước
khi ai trích:
- **US — Regulation E, 12 CFR §1005.11 (EFTA error resolution).** Đây là quy định **đúng
  nghiệp vụ FIN-05** — khách báo lỗi giao dịch điện tử. Nó áp mốc điều tra, và cơ chế
  **provisional credit** khi tổ chức cần kéo dài. Bản 27/08 **không nhắc một chữ nào**.
- **EU — PSD2 Điều 101 + EBA Guidelines on complaints handling (JC 2014 43).** Mốc trả lời
  khiếu nại, khái niệm *holding reply*, và **sổ đăng ký khiếu nại + phân tích nguyên nhân
  gốc** ở cấp tổ chức.
- **EU — PSD2 Điều 73**, giao dịch không được uỷ quyền: nghĩa vụ hoàn tiền **rất gấp**
  (mốc tính theo ngày làm việc kế tiếp). 🔴 **Thiết kế HITL hiện tại không có đồng hồ nào
  cho nhánh này** — vé chờ supervisor duyệt không có mốc riêng cho ca "unauthorised".
  Đây là chỗ **ràng buộc cứng #1 (HITL) và nghĩa vụ pháp lý EU va nhau**, và ta chưa có
  câu trả lời. Tôi coi đây là câu hỏi kiến trúc, không phải câu hỏi cấu hình.

**③ Thiếu các trường mà mọi chế độ trên đều bắt buộc.** `Complaint` hiện có
`created_at` và không gì khác về vòng đời pháp lý. Không có: mốc **tiếp nhận/xác nhận**
riêng với mốc tạo · **provisional credit** (số tiền, ngày cấp, ngày thu hồi) · **lý do gia hạn**
· **phân loại authorised/unauthorised** · mốc **thông báo kết quả cho khách**.
Không có trường ⟹ không có bằng chứng ⟹ **không audit được**, dù quy trình thực tế có đúng.

**④ `add_business_days` bỏ qua ngày lễ.** Ở VN là chấp nhận được cho demo. Dưới Reg E và
PSD2, **định nghĩa "ngày làm việc" là thứ mang tải pháp lý** — sai một ngày là sai nghĩa vụ.

🔴 **Vì sao tôi xếp mục này trên cả các lỗ bảo mật còn lại:** các lỗ bảo mật đều **vá được
trong một lượt code**. Mục này là **thiếu một chiều trong mô hình dữ liệu và trong contract**
— nó chạm `contracts/`, chạm `migrations/`, chạm prompt, chạm UI, chạm bộ đề đánh giá. Càng
để lâu càng đắt, theo cấp số.

---

## 3b. Ba khung pháp lý EU/US bản 27/08 bỏ sót hoàn toàn

Cần Bảo mật xác minh nguyên văn rồi mới đưa vào hồ sơ — **tôi nêu là hướng, không phải dữ kiện đã kiểm**:

| khung | vì sao chạm FIN-05 | ai đụng đầu tiên |
|---|---|---|
| **DORA — Regulation (EU) 2022/2554** | Áp cho tổ chức thanh toán/tiền điện tử. Quản trị rủi ro ICT, báo cáo sự cố ICT nghiêm trọng, **và sổ đăng ký nhà cung cấp ICT bên thứ ba**. 🔴 **Nhà cung cấp LLM của ta CHÍNH LÀ một ICT third-party provider** — bể 4 model qua DashScope + embedding qua OpenAI. Hiện **không có sổ đăng ký nào**. Sự cố mất CSDL 27/08 là đúng dạng sự cố DORA hỏi tới. | Bảo mật |
| **European Accessibility Act — Directive (EU) 2019/882** | Áp cho **dịch vụ ngân hàng tiêu dùng và thương mại điện tử** tại EU, đã tới hạn áp dụng **trước** thời điểm hiện tại. ⚠️ **ĐÍNH CHÍNH bản 30/08 §5.2**, vốn ghi *"sẽ thành thật khi bàn thị trường EU, không phải hôm nay"* — nếu mục tiêu đợt này là benchmark EU thì **là hôm nay**. Nó không cần vào MVP, nhưng **phải là một GAP có khai**, không phải một khoảng trống im lặng. | UX/UI + PO |
| **Reg E / EBA complaints GL** | Xem §3. | Bảo mật + BA |

---

## 4. SỔ RỦI RO — xếp theo cách một PO fintech xếp, không theo vị trí trong code

Nguyên tắc xếp hạng: **rủi ro = (thứ ta không nói được với đối tác) × (chi phí sửa muộn)**.

### P0 — chặn mọi phát ngôn đối ngoại và mọi kết luận đo

| # | việc | vì sao P0 | trạng thái |
|---|---|---|---|
| **R1** | **① RAG không lọc ngưỡng khoảng cách** | Chạm thẳng **Ràng buộc cứng #3**. `search` không bao giờ trả mảng rỗng ⟹ backend **luôn** đưa ra một chính sách, kể cả khi không có chính sách nào khớp. CSKH **nhìn thấy bằng mắt**: chính sách SAI được trình bày như chính sách ĐÚNG. Cảnh 7 buổi quay phải **cấm bấm nút** để né — lệnh cấm đó đang che một lỗi thật. | mở, có địa chỉ |
| **R2** | **Đồng bộ lại `project-knowledge/`** | Cũ 407 commit. Mọi vai đọc nó đang cầm bản đồ chết. Rẻ nhất trong sổ, và **nó là điều kiện để mọi việc khác không sinh ra sai lệch mới**. | mở |
| **R3** | **Phục hồi tín hiệu đo** (E2E 11 đỏ · golden 0 tool · `must_create_manual_ticket` không ai đọc · `_NEGATION_WORDS`) | Không có cổng đáng tin thì **không nghiệm thu được bất cứ bản vá nào ở dưới**. Đây là điều kiện, không phải một việc song song. | mở |
| **R4** | **Đường ra production không xác định** (213/145 commit lệch, production trên máy Windows) | SOC 2 CC8.1 · DORA Đ.8-9. Và nguy hiểm thật: **không ai biết bản vá OTP đã lên production chưa.** | mở |

### P1 — cần trước khi dùng chữ "sẵn sàng tuân thủ EU/US"

| # | việc |
|---|---|
| **R5** | §3 — chiều tài phán + trường vòng đời pháp lý cho `Complaint`. **Phải qua ADR + PO duyệt trước khi code** (chạm `contracts/`). |
| **R6** | GDPR Điều 15/17 — **không có route xuất/xoá dữ liệu nào**. Cần **quyết định** trước, không phải code trước. |
| **R7** | Căn cứ pháp lý cho **dữ liệu người thứ ba** rời biên giới (*"tôi chuyển nhầm cho anh X"*). Che PII đã có nhưng registry `model_input` **hẹp có chủ đích**. Đây là lỗ GDPR sắc nhất và **không đóng được bằng DPIA đơn thuần**. |
| **R8** | Header bảo mật `Caddyfile` — **đã có bản đề xuất `db8d460` từ 27/08, chỉ cần merge**, đo lại vẫn 0. Rẻ nhất trong nhóm P1. |
| **R9** | ⑤ LAN expose còn sống + **thu hồi `QWEN_API_KEY`** (việc tay của PO thật). |
| **R10** | DPIA (C4) + IR runbook (C3): **có draft, chưa phê duyệt**. Draft không phải hồ sơ. |
| **R11** | ③ rò rỉ RAM — **chặn bài đo 150 người** ⟹ ta **không có bằng chứng năng lực tải nào**. Giữ đúng mức **"hướng điều tra"**, `tracemalloc` soi cả nhánh OTel. |
| **R12** | Sổ đăng ký nhà cung cấp ICT bên thứ ba (DORA) — giấy tờ, rẻ. |

### P2 — ghi nhận có khai, không làm đợt này

R13 chặn cứng PAN có Luhn-check trong `description_raw` · R14 SoD mở rộng (supervisor kế thừa
toàn quyền cskh; maker–checker chỉ chặn trùng **người đề xuất**, không chặn trùng **người điều
tra**) · R15 FIDO2/WebAuthn cho vai supervisor · R16 device fingerprinting (FFIEC) ·
R17 EAA/WCAG · R18 MT-Z01 nguyên nhân gốc · R19 registry mã tag `loc_dau_ra` ·
R20 contract chỉ so **TÊN** tool, không so **lược đồ** (`agent-tools.yaml` dòng 34-40 tự khai).

---

## 5. BỐN LÀN — và cổng nghiệm thu của từng làn

Luật cổng của dự án, áp không ngoại lệ: **cổng phải ăn CẢ HAI đầu vào** — chứng minh được nó
**ĐỎ khi lỗi còn đó**, không chỉ xanh khi lỗi đã hết. Thiếu vế đỏ ⟹ chưa nghiệm thu.

### Làn 0 — Lead, làm trước mọi thứ, trong ngày
- **L0.1** Chạy `scripts/export_project_knowledge.py`, thay toàn bộ kho, báo băm mới (R2).
- **L0.2** Trả lời **bằng phép đo**: ảnh Docker đang phục vụ production băm gì · nó chứa
  `bdaf17e`/`5ff93b8` không · nếu chưa thì phát ngôn "đã vá OTP" hiện **chỉ đúng cho repo**,
  không đúng cho production (R4). 🔴 Đây đúng cái bẫy Bảo mật đã ghi ở `proxy.ts:115-145`.
- **Cổng 0:** một bảng, mỗi dòng một băm, mỗi băm một lệnh tái lập được.

### Làn A — Coder (+ Review soát): R1, R11
- **A1** ① ngưỡng khoảng cách cho `search_policy`. **Đây là thay đổi hành vi có thể chạm
  contract** ⟹ Lead phải nói rõ **có** hay **không** chạm `contracts/agent-tools.yaml`
  **trước khi** gõ dòng đầu tiên. Chạm ⟹ dừng, đi đường ADR (`CLAUDE.md` §3).
- **A2** ② xoay model dừng ở lỗi non-quota.
- **A3** R11 `tracemalloc` **cả nhánh OTel**, lưu log **ra tệp** (lần trước mất bằng chứng vì không lưu).
- **Cổng A:** với A1, ca đỏ **bắt buộc** là: *truy vấn không khớp gì ⟹ backend trả mảng rỗng
  ⟹ UI hiện "Chưa tìm thấy"*. Chính là `policy-lookup.spec.ts`. Nó phải **đỏ trước, xanh sau**.

### Làn B — QA/QC: R3
- **B1** Sửa nguyên nhân **môi trường** của 11 đỏ (`OTP_DEMO_MODE` · mật khẩu `USR-0205` ·
  regex nhãn dashboard). 🔴 **Đây là nợ môi trường, KHÔNG phải hồi quy** — đừng ai báo cáo
  nó như bug mới.
- **B2** Golden phủ tool: hiện **0/120 và 0/60**. Đây là **mở rộng phạm vi**, cần PO thật gật.
- **B3** `check_expected` đọc `must_create_manual_ticket` (CASE-109/110 đang chấm như thể cờ
  không tồn tại) · vá `_NEGATION_WORDS`. 🔴 Matcher **mù đối tượng/phạm vi** thì **không vá
  được bằng cách thêm từ** — báo lại, đừng cố.
- **Cổng B:** mỗi cổng vừa sửa phải có **một ca cố ý sai** làm nó đỏ. Cổng chỉ biết xanh thì
  trả lại — chính là bài học 01/09.

### Làn C — Bảo mật (+PO): R5 §3, R6, R7, R8, R9, R10, R12
- **C1** Xác minh **nguyên văn** các mốc Reg E §1005.11 · PSD2 Đ.101 · PSD2 Đ.73 · EBA GL ·
  DORA · EAA. **Trích điều khoản, không trích trí nhớ.** Cái nào không xác minh được ⟹ ghi
  *"chưa xác minh"*, đúng như dự án đã làm với `13/2023`.
- **C2** Từ C1, soạn **đề xuất ADR** cho chiều tài phán + trường vòng đời pháp lý (R5).
  **Soạn đề xuất, KHÔNG code, KHÔNG sửa contract.**
- **C3** R8 merge header (rẻ nhất) · R9 · R12.
- **C4** R7 — trình **hai đường** (thu hẹp dữ liệu rời biên giới **hoặc** lập luận căn cứ
  pháp lý có văn bản), kèm chi phí mỗi đường. Đừng trình câu hỏi trống.
- **Cổng C:** mỗi khẳng định tuân thủ = **một điều khoản + một hiện vật trong repo + một
  lệnh tái lập**. Thiếu một trong ba ⟹ tôi trả lại.

### Làn D — Review: soát chéo + R20
- **D1** Soát làn A, canh đúng bẫy: **CHỈ THÊM** guard, **KHÔNG BAO GIỜ** rút
  `is_access_token_revoked` khỏi `require_otp_verified` (rút ⟹ `create_ticket` mất bảo vệ
  **im lặng, không test nào đỏ**).
- **D2** R20 — đề xuất cách bịt lỗ "chỉ so tên tool".
- 🔴 **D3 — LUẬT MỚI, tôi áp từ hôm nay:** vai Review **phải ghi kết luận ra tệp**
  (`docs/nhat-ky/` hoặc `docs/security/`). Ngày 01/09 kết luận của Review **chết theo phiên**,
  chỉ cứu được 3 mục. Kiến thức sống trong tin nhắn không phải kiến thức của dự án.

---

## 6. Việc CHỈ PO THẬT quyết — Lead không quyết, tôi không quyết

1. Đổi `contracts/` (gồm R5) — `CLAUDE.md` §3: ADR + PO duyệt **trước** khi code.
2. Đường ra `main` / push 145 commit / chạm production.
3. Khoá bí mật, **thu hồi `QWEN_API_KEY`**, billing, self-hosted runner.
4. Nộp hồ sơ DPIA/Đ.25 chính thức — nghĩa vụ đứng tên tổ chức. *(đã treo 2 lần — lần này
   trình kèm **chi phí của việc KHÔNG làm**, đừng hỏi lần ba.)*
5. **Mở rộng bộ đề golden sang chiều tool** (B2) — mở rộng phạm vi, không phải sửa lỗi.
6. **Có theo đuổi thị trường EU/US thật không** — vì R5 và §3b chỉ đáng làm nếu câu trả lời
   là có. Nếu chỉ là **bài tập benchmark để pitch**, thì R5 hạ xuống *"GAP có khai, có lộ
   trình"* và đợt này rẻ đi một nửa. 🔴 **Đây là câu hỏi đắt nhất trong tài liệu và tôi
   không tự trả lời được.**

**Cách trình đúng:** trình **DỮ KIỆN kèm hệ quả**, không trình lại **CÂU HỎI**.

---

## 7. Cách tôi giám sát Lead — nói trước để không ai mất thời gian

PO thật giao tôi một việc cụ thể: canh Lead **quá kỹ thuật · cứng nhắc · ảo giác**.
Ba chế độ hỏng, ba phép thử:

### ① Quá kỹ thuật — dấu hiệu: kế hoạch xếp theo vị trí trong code
**Phép thử:** mỗi việc Lead giao phải kèm đúng một câu:
> *"Không làm việc này thì câu ta KHÔNG nói được với đối tác là: ____"*

Không điền được ⟹ việc đó không thuộc đợt này. Đây là cách phân biệt *bug đáng sửa* với
*bug làm ta khó chịu*. R8 (merge header, 1 dòng) đứng trên R18 (MT-Z01, thú vị hơn nhiều)
chính vì phép thử này.

### ② Cứng nhắc — dấu hiệu: thi hành kế hoạch trong khi phép đo nói kế hoạch sai
**Phép thử — bắt buộc ở báo cáo ĐẦU TIÊN:** Lead phải nêu **ít nhất một mục trong tài liệu
này là sai** (sai thứ tự · sai giả định · đã lỗi thời so với phép đo), **hoặc** nói rõ *"đã
tìm, không thấy"* **kèm cách đã tìm**. QA/QC làm đúng điều này ngày 30/08 với con số 27/27
và nó đáng giá hơn một ngày làm đúng theo kế hoạch sai. Báo cáo đầu tiên không có mục này
⟹ tôi trả lại, không đọc phần còn lại.

### ③ Ảo giác — dấu hiệu: khẳng định sống lâu hơn sự thật của nó
Đây là chế độ hỏng **dự án đã trả giá 9 lần trong một ngày** (20/08). Bốn phép thử tôi chạy
trên **mọi** báo cáo:

| # | phép thử | dạng bị trả lại |
|---|---|---|
| **T1** | **ĐỌC hay CHẠY?** | *"sạch"* từ đọc diff bị trình như *"sạch"* từ chạy thật |
| **T2** | **Cổng ăn cả hai đầu vào?** | chỉ có vế xanh |
| **T3** | **Phạm vi phép đo = phạm vi kết luận?** | trình bằng **số đếm** thay vì bằng **cơ chế**; `grep` đúng rồi suy rộng |
| **T4** | **Mọi con số có mốc giờ?** | 🔴 con số ở dự án này **hỏng theo ngày**. Số không mốc = số đã chết |

Bốn phép trên là luật cũ của dự án. **Tôi thêm hai phép của vai PO fintech:**

| # | phép thử | dạng bị trả lại |
|---|---|---|
| **T5** | **Mọi khẳng định tuân thủ = điều khoản + hiện vật + lệnh tái lập** | *"đạt PSD2"* không kèm *"RTS Đ.5 · `main.py:940-978` · test X đỏ-trước/xanh-sau"* |
| **T6** | **Danh tính vật đang chạy ≠ danh tính mã nguồn** | *"đã vá"* trong khi ảnh production chưa ai kiểm. Dự án đã trượt bẫy này một đêm với ảnh lùi 55 commit |

### Nhịp
Lead báo cáo **theo mốc** — mỗi khi một cổng ở §5 đóng, hoặc gặp một mục ở §6.
**Không báo cáo tiến độ trống.** Một làn tắc **không** làm tắc làn khác — người ngồi không
trong lúc có việc đã gỡ chặn là lãng phí không ai báo cáo, vì nó trông giống *"đang chờ đúng quy trình"*.

---

## 8. Đính chính bản 30/08

| mục 30/08 | đính chính 01/09 |
|---|---|
| §5.2 *"EAA sẽ thành thật khi bàn thị trường EU, không phải hôm nay"* | Nếu mục tiêu là benchmark EU thì **là hôm nay**. Vẫn KHÔNG vào MVP — nhưng phải là **GAP có khai** (§3b). |
| Làn A/B/C/D | A1/A2 **đã land** (đo 01/09) · C1/C2 **đã làm** · B1 **chưa** (11 đỏ) · R8 **vẫn treo từ 27/08**. |
| Benchmark EU/US coi như đã phủ | **Chưa phủ** Reg E · PSD2 Đ.73/101 · EBA complaints GL · DORA · EAA. Xem §3 và §3b. |
