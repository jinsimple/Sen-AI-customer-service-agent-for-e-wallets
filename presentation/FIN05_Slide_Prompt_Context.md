# TÀI LIỆU CONTEXT DỰ ÁN FIN-05 & KỊCH BẢN SLIDE
(Tài liệu này được tối ưu để nạp vào LLM / Gemini Web nhằm mục đích tạo Slide và Generate Hình ảnh AI)

## PHẦN 1: THÔNG TIN TỔNG QUAN DỰ ÁN (PROJECT CONTEXT)
Dự án FIN-05 (Sen AI Agent) là AI trợ lý CSKH chuyên biệt cho Ví điện tử, tập trung xử lý các khiếu nại giao dịch (chuyển nhầm, tiền chưa về, trừ đúp).

1. Bài toán kinh tế & Pháp lý:
- Khung pháp lý hiện hành: **NĐ 52/2024/NĐ-CP** (trung gian thanh toán) và **TT 40/2024/TT-NHNN**.
  Thời hạn xử lý tra soát/khiếu nại theo quy định ngành là **30 ngày làm việc kể từ ngày tiếp nhận**.
  ⚠️ NẾU BỊ HỎI ĐIỀU/KHOẢN CỤ THỂ: nói "để tôi gửi lại trích dẫn chính xác sau buổi làm việc".
  Dự án **chưa đối chiếu bản gốc tới cấp điều/khoản** — đừng đọc số điều trên sân khấu.
  🔴 KHÔNG dùng "TT 15/2024" ở bất kỳ slide nào. Bộ slide cũ trộn TT 15/2024 (slide 2) với
  TT 40/2024 (slide 4) cho cùng một chủ đề — người trong ngành sẽ bắt ngay. CHỐT MỘT: TT 40/2024.
- Sự cố khách hàng thường xuyên xảy ra vào giờ mua sắm (đêm, ngoài giờ hành chính).
- Vận hành CSKH ngoài giờ tốn kém hơn giờ hành chính (ca đêm, cuối tuần).
  ⚠️ BỎ con số "gấp 5 lần" — không có nguồn nào trong hồ sơ dự án. Nói định tính, đừng nói bội số.

2. Giải pháp (Phễu 4 tầng):
- L0: Khách tự phục vụ
- L1: Sen AI tra cứu & trả lời
- L2: Sen AI điều tra, thu thập bằng chứng -> CSKH duyệt
- L3: Sếp phê duyệt. 
-> Giá trị: Giảm AHT (Average Handle Time) và đưa số bước tra cứu thủ công về 0.

3. Kỷ luật thép (Deterministic Guardrails) - Tính năng "ăn tiền" nhất:
- Không được làm: AI KHÔNG BAO GIỜ có quyền tự duyệt hoàn tiền. Ép bằng luật vật lý ở Database (CheckConstraint: người tạo khác người duyệt).
- Không được bịa: Origin-rule quy định mọi số liệu AI nói phải truy vết được về một kết quả tool
  có thật (`tool_results` → `investigation_logs` → `resolutions.cited_tool_result_ids`).
  Tra không được thì agent phải nói rõ "không tra được".
  🔴 BỎ HẲN cụm "0% Hallucination". Đó là tuyên bố TUYỆT ĐỐI — trước mặt người làm ví điện tử,
  nó là lời mời họ đi tìm một ca ngược lại, và chỉ cần một ca là mất toàn bộ uy tín phần còn lại.
  Nói CƠ CHẾ (truy vết được về nguồn), đừng nói TỈ LỆ TUYỆT ĐỐI.
- 🔴 **SỬA 31/08 — câu cũ *"Dữ liệu cá nhân được che trước khi đưa vào mô hình"* là SAI, đã bỏ.**
  Nó hứa một sự bảo đảm không có thật: **văn bản tự do khách tự gõ vẫn rời hạ tầng sang nhà cung
  cấp mô hình.** Che triệt để phần đó sẽ phá nghĩa câu — đã đo, bộ chặn S-01 chặn nhầm **40%**.
  Câu **được phép** nói, đúng phạm vi:
  > *"Trường dữ liệu có cấu trúc được mã hoá ở mức trường trong CSDL. Với văn bản tự do, chúng
  > tôi chạy bộ che PII trước khi ghi log và trace — đo được 4,8% câu trong bộ kiểm bị chèn nhãn
  > che, dưới ngưỡng 6% mà chúng tôi tự đặt. Nhưng chúng tôi **không** tuyên bố che được sạch
  > văn bản tự do: che quá tay thì phá nghĩa, và đó là đánh đổi chúng tôi đang cân, chưa đóng."*
  Căn cứ pháp lý: **Luật Bảo vệ dữ liệu cá nhân số 91/2025/QH15** + **NĐ 356/2025/NĐ-CP**,
  hiệu lực 01/01/2026. 🔴 KHÔNG dùng "NĐ 13/2023" — đã bị THAY THẾ từ 01/01/2026.
  (Đây là điểm ăn điểm: phần lớn hồ sơ cùng loại vẫn đang trích văn bản đã hết hiệu lực.)

4. Kiến trúc:
- 3 lớp: Next.js (BFF - không giữ JWT ở frontend) -> FastAPI -> LangGraph Agent (5 tools).
- Bể 4 model tự xoay (Deepseek, Qwen) để giảm chi phí, tăng tính khả dụng. RAG ChromaDB để tra chính sách.

5. Đo lường — MỌI SỐ DƯỚI ĐÂY ĐO LẠI NGÀY 30/08/2026, tra được nguồn:
- **526** test tự động toàn bộ backend, trong đó **23** test bất biến canh 5 ràng buộc cứng bằng cách
  **soi thẳng vào app đang chạy** (đọc `app.routes`, moi `allowed_roles` từ closure, đọc CHECK
  constraint qua AST) — không phải đọc tài liệu tĩnh. Đỏ là build hỏng. **16** job CI.
- **246 ca đánh giá**: 120 Golden · 60 Held-out (**niêm phong từ đầu**, để bộ đo không bị tối ưu
  ngược) · 66 Đối kháng. Toàn bộ kho đánh giá: **386 dòng / 15 bộ riêng biệt**.
- **Tái lập được**: cùng một câu hỏi, chạy 3 lần qua 2 ngày trên 2 bản build khác nhau → ra đúng
  cùng một giao dịch `TXN20260801000466` (`eval/EVAL-EVIDENCE.md`).
- **Che dữ liệu cá nhân**: tỉ lệ làm méo câu tiếng Việt **4,8%** (6/124 câu), dưới ngưỡng nội bộ 6%
  — và cả 6 ca đều là che số điện thoại ĐÚNG chức năng (`eval/do_bop_meo_pii.py`, chạy 30/08).

🔴 BA SỐ ĐÃ GỠ KHỎI BỘ SLIDE — nếu thấy ở đâu còn sót, XOÁ:
- "786 vé mô phỏng · xử lý TB 17,7h" → **KHÔNG tra được nguồn nào trong repo**. Số 786 thực chất
  là số bản ghi dữ liệu cá nhân đã vá mã hoá, hoàn toàn không liên quan tới vé.
- "60% đề xuất AI được duyệt" → đo trên **người duyệt mô phỏng**, và người nghe đọc ngược thành
  "4/10 bị bác". Đã có lệnh gỡ nội bộ từ 27/08.
- "593 Test Pass" → đếm thật ngày 30/08 là **526**.

### Hai bản vá xác thực 30/08 — nói được gì, cấm gì *(cập nhật 31/08)*

🟢 **`bdaf17e` (gỡ mã OTP khỏi response + so sánh theo thời gian hằng) — ĐÃ CÓ cổng đỏ-trước/
xanh-sau.** `test_otp_demo_mode_khong_lo_otp_code.py`: **ĐỎ (2 ERROR)** trên commit trước
`2a915db` → **XANH (2 passed)** trên `bdaf17e`. Câu **được phép** nói, đúng nguyên văn này:

> *"Chúng tôi tìm ra mã OTP bị trả về trong thân phản hồi API, đã vá, và có test chạy đỏ trên
> commit trước bản vá — xanh trên commit sau. Đó là bằng chứng bản vá sửa đúng thứ nó nói."*

🟢 **`5ff93b8` (ADR-055 — token đã thu hồi phải bị chặn ở 3 route) — ĐÃ CÓ vế đỏ HÀNH VI
*(31/08)*.** Kịch bản đo: đăng nhập → đăng xuất → gọi lại route bằng token cũ.

| | trước vá | sau vá |
|---|---|---|
| `propose_resolution` | **200 OK** — tạo thật `RES-752998bd0673` | 401/403 |
| `escalate_ticket` | **200 OK** — tạo thật `ESC-f75e21f026d8` | 401/403 |
| `request_approval_otp` | **200 OK** — tạo thật `SES-80bb2de5ff9e` | 401/403 |

Câu **được phép** nói:

> *"Chúng tôi phát hiện token đã thu hồi vẫn gọi được ba route có hậu quả — và không chỉ trả về
> 200, nó tạo ra bản ghi thật. Chúng tôi vá, rồi chứng minh bằng cách chạy lại đúng kịch bản đó
> trên commit trước bản vá: ba lỗi. Trên commit sau: ba lượt bị chặn đúng."*

⚠️ **Giới hạn phải nói kèm nếu bị hỏi sâu:** bằng chứng này là **phép đo hành vi**, chưa phải
**cổng thường trực** — script kiểm nằm ngoài `tests/` (vùng ghi của `tester`, đợt này không có
phiên tester). Nghĩa là hôm nay nó đúng, nhưng nếu mai ai gỡ guard khỏi một route thì **chưa có
gì tự báo đỏ**. Việc đưa test vào `tests/` đã xếp hàng, chưa làm.
📎 Bằng chứng đầy đủ: `docs/security/2026-08-31-cong-do-truoc-xanh-sau-bdaf17e-5ff93b8.md`

🟢 **Kiểm chứng BA nguồn, BA phương pháp khác nhau — dùng được khi bị hỏi "ai kiểm lại?"**

| nguồn | phương pháp | tự khai không nhìn thấy được gì |
|---|---|---|
| Bảo mật | tự viết script rồi tự chạy | *"vừa viết vừa chạy — đây không phải kiểm chéo"* |
| Coder | công cụ khác hẳn — `TestClient` tự viết, CSDL riêng, đăng nhập/đăng xuất thật qua HTTP; **không** đụng script của Bảo mật. Đo được: 3 route **200 → 401** | chỉ đo 3 route trong phạm vi ADR-055 |
| Review | đọc tĩnh diff, không chạy | *"không xác minh được con số đỏ/xanh, vì đó là kết quả CHẠY"* |

Cả ba khớp nhau. Điểm đáng nói không phải "ba người cùng đồng ý" — mà là **ba phương pháp khác
nhau**, và **mỗi người tự khai ra giới hạn của phương pháp mình**. Ba người cùng chạy một script
thì vẫn chỉ là **một** phép kiểm lặp ba lần.

💡 **Cách trình hai bản vá này — đừng trình như lời thú tội.** Đây là **quy trình bảo mật đang
chạy đúng**: đội tự tìm ra lỗ của mình, chứng minh nó khai thác được, vá, rồi chứng minh bản vá
có tác dụng. Người thẩm định fintech tin một đội tìm ra bug của chính mình hơn một đội chưa
từng báo bug nào. Chuẩn bị sẵn cho câu hỏi tiếp theo — *"làm sao biết không còn chỗ nào như
vậy?"* — trả lời thật: 23 test bất biến soi cấu trúc thẩm quyền ở mọi lần chạy, **và** đây
chính là lý do đưa test hành vi vào `tests/` đang là việc kế tiếp, chứ không phải việc đã xong.

🔴 **CẤM cụm "đạt SCA / PSD2-compliant / AAL2"** ở mọi slide và mọi lời nói — **kể cả sau khi
trả xong cả hai vế đỏ.** Lý do đã đổi: không còn là thiếu bằng chứng, mà là **một cổng đỏ-xanh
trên hai bản vá không phải một cuộc đánh giá tuân thủ.** Những nhãn đó do bên đánh giá độc lập
kết luận theo bộ tiêu chí đầy đủ, không suy ra được từ hai test.

---

## PHẦN 2: KỊCH BẢN SLIDE PITCHING (11 SLIDE)
Kịch bản này thiết kế theo phong cách trực quan, ít chữ (chỉ key words) và dùng hình ảnh.

### Slide 1: Bức tranh tương phản
- **Chữ:** 15 tỷ GD không tiền mặt. 4.6 triệu cảnh báo gian lận. "Sự cố không có giờ hành chính".
- **Chữ:** 15 tỷ GD không tiền mặt. "Sự cố không có giờ hành chính". *Nỗi đau được xác nhận qua phản hồi không chính thức từ các chuyên gia trong ngành ví điện tử và một GĐ Chi nhánh Ngân hàng — không phải hợp tác chính thức.*
- **Prompt tạo ảnh AI:** A highly cinematic, photorealistic image of a frustrated young person looking at their glowing smartphone screen in a completely dark bedroom at 2:00 AM. In the background, subtly out of focus, glowing digital financial charts and data streams float in the air, representing massive digital transaction volumes. Neon blue and orange color palette, dramatic lighting.
### Slide 2: Đồng hồ pháp lý vs Quỹ lương
- **Chữ:** Đồng hồ pháp lý chạy 24/7. Đội ngũ thì không.
- **Căn cứ nếu bị hỏi:** NĐ 52/2024/NĐ-CP · TT 40/2024/TT-NHNN. **KHÔNG nhắc TT 15/2024.**
- 🔴 BỎ "Gấp 5 lần" — không có nguồn. Thay bằng ý định tính: *"Đêm và cuối tuần là lúc sự cố
  nhiều nhất, cũng là lúc đắt nhất để có người trực."*
- **Prompt tạo ảnh AI:** A dramatic visual of a heavy, glowing clock ticking down. Next to it, an elegant conceptual illustration of an oversized math equation balancing a 24/7 clock with a heavy stack of glowing golden coins, representing a 5x labor cost multiplier.

### Slide 3: Phân luồng 4 tầng chi phí
- **Chữ:** Cắt giảm chi phí bằng phễu lọc 4 tầng (L0 đến L3). Sen xử lý L1 & L2.
- **Prompt tạo ảnh AI:** A sleek, modern 3D glowing funnel diagram with 4 levels. The top levels (L0, L1) are wide and illuminated in blue, representing AI automation. The bottom level (L3) is narrow, illuminated in orange, showing human executive approval.

### Slide 4: Tự động hóa KHÔNG ĐƯỢC PHÉP SAI
- **Chữ:** AI Điều tra -> CSKH Trình bày -> Sếp Duyệt. Kỷ luật 3 KHÔNG: Không tự làm, Không tự bịa, Không để lộ.
- **Prompt tạo ảnh AI:** An abstract futuristic cybersecurity visual showing an AI glowing core interacting with a human silhouette, with a massive glowing digital padlock in the middle representing strict deterministic guardrails.

### Slide 5: KIẾN TRÚC - Hai đường đi, tách bạch có chủ đích
*(Làm theo layout ngang, chia 2 đường song song dựa trên ảnh tham khảo)*
- **Khối Client & API:** Next.js 14 (BFF - không giữ JWT ở Frontend) & FastAPI (Backend xác thực OTP, JWT rotation).
- **Đường 1 (Trên) - Vòng đời HITL (Người duyệt):** TẤT ĐỊNH - 0 LLM CALL. Con người đọc vết điều tra (Trail) -> Phê duyệt kèm OTP step-up. Ràng buộc Maker-Checker ép chết bằng CHECK constraint tại Database.
- **Đường 2 (Dưới) - Luồng AI điều tra:** MULTI-TURN. LangGraph Agent gọi 5 tools tra cứu. Bọc lớp Guardrails cứng: Che PII (Presidio) và Origin-rule (chặn bịa số liệu).
- **Khối Infra (Bên phải):** Postgres (Mã hóa data) | Bể 4 model tự xoay (Deepseek, Qwen) | ChromaDB RAG.
- **Gợi ý thiết kế:** Vẽ dạng sơ đồ Block Diagram nền dark mode, chia rõ 2 luồng: Luồng con người (**TẤT ĐỊNH — 0 lượt gọi LLM**) và Luồng AI (Chỉ tra cứu & đề xuất).
  🔴 **SỬA 31/08 — đã bỏ *"An toàn tuyệt đối"* khỏi nhãn này.** Chỗ này **nguy hơn** một câu nói
  miệng: nó là gợi ý cho người dựng ảnh, nên chữ "tuyệt đối" có thể **in thẳng lên slide** — mà
  chữ đã nằm trên hình thì giữa buổi không rút lại được. Dùng "TẤT ĐỊNH" cho khớp với chính
  dòng mô tả kiến trúc phía trên, và vì đó mới là điều ta chứng minh được: luồng người duyệt
  **không gọi LLM lần nào**, ràng buộc maker-checker ép bằng `CHECK constraint` ở CSDL.

### Slide 6: Xóa bỏ 100% thời gian tra cứu thủ công
- **Chữ:** 0 bước tra cứu thủ công. Ra quyết định trong tích tắc.
- **Prompt tạo ảnh AI:** A futuristic, clean, and minimalist digital workspace. A glowing AI hologram is automatically organizing chaotic floating financial data and documents into one single, neat, glowing green summary folder. Bright, optimistic lighting, representing speed, clarity, and instant AI problem-solving in customer service. No text in the image.

- **Chữ:** Dữ liệu nghiệp vụ nằm trong hạ tầng của mình. Giọng văn thấu cảm.
  🔴 **SỬA 31/08 — đã bỏ cụm *"An toàn dữ liệu tuyệt đối"*.** Đó là tuyên bố TUYỆT ĐỐI, **cùng
  loại** với *"0% Hallucination"* mà chính deck này đã tự cấm ở PHẦN 1. Và nó sai thật: văn bản
  tự do vẫn đi ra nhà cung cấp mô hình. Trước người làm ví điện tử, một chữ "tuyệt đối" là lời
  mời họ đi tìm ca ngược lại — chỉ cần một ca là mất uy tín toàn bộ phần còn lại.
- **Prompt tạo ảnh AI:** A high-tech, futuristic illustration of a glowing, transparent digital vault placed safely inside a modern corporate server room. Inside the vault, golden digital coins and private data streams are swirling peacefully. The vault acts as an impenetrable shield, representing on-premise data security for e-wallets. Professional, secure, deep blue and gold tones.

### Slide 8: Bằng chứng minh bạch - Traceability
- **Gợi ý hình ảnh:** Dùng chính Screenshot màn hình terminal và log của dự án. AI không tự suy diễn mà luôn truy vấn ra bằng chứng.

### Slide 9: ĐO LƯỜNG — Ba nguồn số, ba mức độ chắc chắn
*(Layout 3 khối. MỌI SỐ ĐO LẠI 30/08/2026 — bảng nguồn ở cuối tài liệu này.)*

- **Khối 1 — Bộ ca đánh giá:** **246 ca** — 120 Golden · **60 Held-out** · 66 Đối kháng.
  Điểm nhấn nên nói thành lời, vì người trong ngành hiểu ngay giá trị của nó:
  *"60 ca held-out được niêm phong từ ngày đầu, chưa từng dùng để chỉnh sản phẩm — để bộ đo
  không bị tối ưu ngược."* Toàn kho: **386 dòng / 15 bộ**.

- **Khối 2 — Độ phủ test:** **526** test tự động, gồm **23 test bất biến** canh 5 ràng buộc cứng
  bằng cách **soi thẳng vào ứng dụng đang chạy** — đọc bảng route thật, moi danh sách vai được
  phép từ trong hàm bảo vệ, đọc ràng buộc CHECK của cơ sở dữ liệu. Không phải đọc tài liệu mô tả.
  ⟹ Thêm một route · đổi một guard · đổi tên một tool mà quên cập nhật hợp đồng → **đỏ ngay**.
  **16 job CI** chạy mọi lần push/PR.

- **Khối 3 — Bằng chứng tái lập, thay cho "chỉ số vận hành":**
  Cùng một câu hỏi, chạy **3 lần qua 2 ngày trên 2 bản build khác nhau** → ra đúng cùng một giao
  dịch `TXN20260801000466`. Đo trên môi trường 208 người dùng · 60.001 giao dịch.
  Che dữ liệu cá nhân: làm méo **4,8%** câu tiếng Việt (6/124), dưới ngưỡng nội bộ 6%.

- **Gợi ý thiết kế:** tô đậm **60** (held-out), **23** (bất biến), **3/3** (tái lập).
  🔴 KHÔNG tô đậm "0%" hay bất kỳ tỉ lệ tuyệt đối nào.

🔴 **BA SỐ ĐÃ GỠ, đừng để lọt lại:** "0% Hallucination" (tuyên bố tuyệt đối — nói cơ chế truy vết
thay vì tỉ lệ) · "593 Test Pass" (thật là **526**) · "786 vé / 17,7h / 60% duyệt" (không tra được
nguồn; 786 thực chất là số bản ghi dữ liệu cá nhân đã vá mã hoá, không liên quan vé).

### Slide 10: Ưu điểm & Thách thức
- **Chữ:** Sức mạnh bảo mật vs. Giới hạn thực tế (chưa cắm trực tiếp Core Banking).
- **Chữ:** Sức mạnh: Luồng nghiệp vụ chuẩn được góp ý không chính thức bởi các chuyên gia trong ngành ví điện tử Việt Nam. Thách thức: Chưa cắm trực tiếp Core Banking thật.
- **Prompt tạo ảnh AI:** A visually striking glowing balance scale. On one side, a heavy, secure metallic lock (security). On the other, a digital bridge that is still under construction, representing the missing core banking integration.

### Slide 10b (THÊM MỚI — nên có): Đo cái gì, và chưa đo được cái gì

Slide này làm bộ hồ sơ đáng tin hơn hẳn việc chỉ khoe số. Người thẩm định chuyên nghiệp
tin một đội **biết rõ mình chưa đo được gì** hơn một đội chỉ trình toàn số đẹp.

- **Đã đo:** an toàn (ràng buộc cứng + đối kháng) · không bịa số (truy vết về nguồn) ·
  truy hồi chính sách · thời gian phản hồi.
- **Chưa đo được, và nói thẳng vì sao:** trục **trải nghiệm người dùng** cần bộ nhãn do người
  quyết định sản phẩm chấm tay để hiệu chuẩn máy chấm. Đội một người, chưa làm xong.
  ⟹ Con số tổng hiện đo trên **thang 85 điểm**, không phải 100.
- 🔴 **RANH GIỚI CỦA PHÉP ĐO — con số này KHÔNG nói gì về tầng xác thực.**
  Đường đo coi OTP phiên **luôn vừa xác thực xong**; **JWT · chặn tần suất · nhật ký kiểm toán
  KHÔNG nằm trên đường đo**. Chính báo cáo tự in cảnh báo này ở đầu mỗi lượt chạy
  (`eval/run_golden_set.py:158-165`): *"kết luận về các tầng đó từ kết quả eval là **kết luận
  SAI CHỖ ĐO**."* Con số đo **chất lượng suy luận + tuân thủ nội dung** của agent với giả định
  người dùng đã đăng nhập xong — không hơn.
  ⟹ Bằng chứng bảo mật và con số benchmark là **hai luồng riêng, không được chạm nhau.**
- 🔴 **Câu khai phạm vi — BẮT BUỘC nói kèm mỗi lần đọc con số tổng, không có ngoại lệ:**
  *"Đo trên `qwen3.7-max-2026-05-20` — checkpoint anh em của mô hình đang phục vụ thật.
  Thang 85 điểm, trục trải nghiệm chưa đo."*
  Bỏ vế này ⟹ người nghe tự hiểu thành thang 100, con số bị thổi lên khoảng 18%.

---

## PHẦN 3: BẢNG NGUỒN — mở ra khi bị hỏi "số này ở đâu ra?"

> Soát và đo lại toàn bộ ngày **30/08/2026**. Mỗi dòng đều chạy lại được.

| Con số | Nguồn tra được |
|---|---|
| 526 test tự động | đếm `def test_` trong `tests/` |
| 23 test bất biến | `tests/test_invariants.py` |
| 16 job CI | `.github/workflows/ci.yml` |
| 120 / 60 / 66 ca | `wc -l` trên `golden_set` · `heldout_set` · `adversarial_set` + `adversarial_multiturn_set` |
| 386 dòng / 15 bộ | `cat eval/*.jsonl \| wc -l` · `ls eval/*.jsonl \| wc -l` |
| Tái lập 3/3 lượt — **chọn đúng cùng một mã giao dịch**, trong đó **2/3 lượt chạy trên bản build code KHÁC nhau** | `eval/EVAL-EVIDENCE.md`, ca 1 (`TXN20260801000466`), đo 14–16/08. ⚠️ Phạm vi: tái lập **việc tra đúng giao dịch**, KHÔNG phải văn bản trả lời giống hệt (độ trễ 3 lượt: 12,5s · 22,3s · 16,4s). Hồ sơ **không ghi** nhiệt độ/tên model — khoảng trống đã biết. 🔴 Ca này KHÁC `CASE-001` của `golden_set` — trùng số thứ tự, khác hoàn toàn nội dung |
| 208 người · 60.001 giao dịch | môi trường seed `DATASET_SEED=20260802` |
| 4,8% làm méo tiếng Việt | `python3 eval/do_bop_meo_pii.py`, chạy 30/08 |
| Luật 91/2025 · NĐ 356/2025 | PDF ký số VPCP: `datafiles.chinhphu.vn/cpp/files/vbpq/2025/7/91qh.signed.pdf` |
| Góc nhìn nghiệp vụ từ chuyên gia ngành ví điện tử | `FIN05-Brief.md` — phản hồi không chính thức |

**Bốn câu KHÔNG được nói, kể cả khi bị dồn:**
1. *"0% ảo giác"* / bất kỳ tỉ lệ tuyệt đối nào — nói **cơ chế truy vết**, không nói tỉ lệ.
2. *"Đạt SCA / PSD2-compliant / AAL2"* — bản vá xác thực chưa có cổng nghiệm thu đỏ-trước.
3. Bất kỳ **số điều/khoản luật nào chưa mở bản gốc ra đọc** — với Luật 91/2025 thì đọc rồi,
   nói được; với TT 40/2024 thì **chưa**, nên chỉ nói tên văn bản, không nói số điều.
4. *"Benchmark chứng minh phần xác thực/bảo mật của chúng tôi chạy đúng"* — dưới **mọi** cách
   diễn đạt. Phép đo đó **không chạm** tầng xác thực (xem RANH GIỚI ở PHẦN 2). Muốn nói về
   bảo mật thì dẫn **bằng chứng bảo mật**; muốn nói về chất lượng agent thì dẫn **điểm
   benchmark**. Ghép hai thứ lại là dựng một kết luận chưa ai đo.

**Câu trả lời chuẩn khi bị hỏi một số ta chưa có:**
*"Cái đó chúng tôi chưa đo, nên tôi không đưa số. Tôi gửi lại sau khi đo."*
Đây là câu **làm tăng** uy tín trước người thẩm định, không phải làm giảm.

---

### Slide 11: Đón đầu sóng Pháp lý AI 2026-2027
- **Chữ:** Trích đúng luật đang có hiệu lực, không trích luật đã bị thay thế.
- **Căn cứ ĐÃ ĐỌC TOÀN VĂN** (bản PDF ký số Văn phòng Chính phủ, 23 trang):
  **Luật 91/2025/QH15** + **NĐ 356/2025/NĐ-CP**, hiệu lực **01/01/2026**, thay thế NĐ 13/2023.
  Nói được cụ thể nếu bị hỏi: Đ.4.1.d (quyền yêu cầu cung cấp/xoá dữ liệu) · Đ.21.1 (nộp hồ sơ
  đánh giá tác động trong **60 ngày** kể từ ngày xử lý đầu tiên) · Đ.23.1 (báo cơ quan chuyên
  trách chậm nhất **72 giờ**).
  🔴 **SỬA 31/08 — Đ.38.2 hạ giọng, câu cũ khẳng định chắc quá mức.** Câu cũ: *"miễn 5 năm cho
  DN nhỏ, trừ bên trực tiếp xử lý dữ liệu nhạy cảm — tức KHÔNG áp dụng cho ví điện tử"*. Vế
  *"tức KHÔNG áp dụng"* là **suy luận của ta**, không phải chữ trong luật — nó đứng trên giả
  định ví điện tử thuộc danh mục nhạy cảm Đ.2.3, mà danh mục đó **ta chưa đối chiếu từng mục**.
  Câu được phép nói:
  > *"Đ.38.2 có cơ chế miễn 5 năm cho doanh nghiệp nhỏ, kèm ngoại lệ cho bên xử lý dữ liệu nhạy
  > cảm. Chúng tôi **chưa** đối chiếu xong danh mục Đ.2.3 nên chưa khẳng định mình thuộc diện
  > nào — và chúng tôi không lập kế hoạch dựa trên việc được miễn."*

  Vì sao hạ giọng dù hướng suy luận có thể đúng: trước chuyên gia ngành, **khẳng định chắc một điều
  mình chưa tra là rủi ro lớn hơn hẳn việc nói thẳng là chưa tra.** Câu cũ còn tự mâu thuẫn với
  hồ sơ pháp lý của chính ta — vốn ghi *"CÓ THỂ thuộc diện loại trừ, KHÔNG dùng như lối thoát
  chắc chắn"*.
- 🔴 BỎ "NĐ 142/2026" — không tra được nguồn, đừng trích một văn bản chưa mở ra đọc.
- **Khung nói trung thực về khoảng trống** (mạnh hơn là giấu): *"Chúng tôi đã đối chiếu hệ thống
  với luật mới và biết rõ ba chỗ còn thiếu — route tự phục vụ xuất/xoá dữ liệu, hồ sơ đánh giá
  tác động, và quy trình thông báo vi phạm. Cả ba đang trong kế hoạch có mốc thời gian."*
- **Prompt tạo ảnh AI:** A glowing futuristic timeline road leading towards a bright horizon. Glowing signposts along the road read "2026" and "2027", representing AI legal compliance and forward-thinking roadmap.
