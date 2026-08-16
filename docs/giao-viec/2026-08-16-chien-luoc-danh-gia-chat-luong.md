# Chiến lược đánh giá chất lượng chatbot — phân tích 3 nguồn + số đo neo

> PO-agent research theo yêu cầu PO thật 16/08. Nguồn: LangSmith evaluation-concepts ·
> OpenAI Evals/Graders API · RAG chunking/retrieval. Mọi khuyến nghị đều neo vào SỐ ĐO THẬT
> của chính dự án (đo trong phiên, nhãn vật đầy đủ) — không khuyến nghị nào đứng trên lý thuyết suông.

## 0. SỐ ĐO NEO — chạy hôm nay trên kho RAG thật (backend stack demo, kho 419 chunk)

Mini golden-set 8 câu hỏi chính sách tự nhiên, chấm Recall@3 bằng từ-khoá-đáp-án
(k=3 = đúng cấu hình sản phẩm):

| Chế độ gõ | Recall@3 | Ghi chú |
|---|---|---|
| **Không dấu** (cách khách demo D1-D4 vẫn gõ) | **0/8** | Top-1 lạc đề hoàn toàn (hỏi phí → ra mã QR) |
| **Có dấu** (cùng 8 câu, chỉ thêm dấu) | **3/8** | Thí nghiệm MỘT-BIẾN: dấu là biến duy nhất đổi |

**Kiểm dụng cụ trước khi tin số** (nghi-mình-trước): đáp án CÓ TỒN TẠI trong kho —
`hoàn tiền` xuất hiện trong 44 chunk, `hạn mức` 40, `khiếu nại` 23, `mật khẩu` 14
⟹ lỗi nằm ở TẦNG TRUY HỒI, không phải kho thiếu nội dung.

**NGUYÊN VĂN 8 CA PROBE (thước của cặp trước/sau — GIỮ NGUYÊN VĂN, cấm sửa; mở rộng = thêm ca
mới):** chấm bằng `search_policy_text(session, query=..., k=3)`; chuẩn hoá NFD-bỏ-dấu-thường-hoá
cả hai vế; ĐẠT khi tồn tại MỘT chunk trong top-3 chứa ĐỦ mọi từ-khoá của ca.

| # | Không dấu | Có dấu | Từ-khoá-đáp-án |
|---|---|---|---|
| 1 | phi chuyen tien lien ngan hang la bao nhieu | phí chuyển tiền liên ngân hàng là bao nhiêu | `phi` |
| 2 | quy trinh hoan tien khi chuyen nham the nao | quy trình hoàn tiền khi chuyển nhầm thế nào | `hoan tien` |
| 3 | han muc chuyen tien toi da mot ngay | hạn mức chuyển tiền tối đa một ngày | `han muc` |
| 4 | lam sao de kich hoat vi lan dau | làm sao để kích hoạt ví lần đầu | `kich hoat` |
| 5 | thoi han khieu nai giao dich la bao lau | thời hạn khiếu nại giao dịch là bao lâu | `khieu nai` |
| 6 | chuyen tien bi tru tien nhung nguoi nhan chua nhan duoc thi lam gi | chuyển tiền bị trừ tiền nhưng người nhận chưa nhận được thì làm gì | `chua nhan` |
| 7 | toi quen mat khau thi lay lai kieu gi | tôi quên mật khẩu thì lấy lại kiểu gì | `mat khau` |
| 8 | giao dich cho xu ly trong bao lau thi xong | giao dịch chờ xử lý trong bao lâu thì xong | `cho xu ly` |

Lưu ý đọc thước: ca 1 từ-khoá `phi` rộng (có thể khớp "phí" bất kỳ); kiểm-kho cho thấy cụm
`phi chuyen` = 0 chunk ⟹ ca 1 có thể KHÔNG trả lời được từ kho hiện tại — nếu sau mọi đòn nó vẫn
0, cân nhắc loại khỏi mẫu số với lý do "kho không chứa đáp án" (khai, không lấp). Nhãn kho lúc đo
mốc: 419 chunk · băm Chroma `b630414088f8`.

**Ba phát hiện từ một phép đo 0đ LLM (chỉ tốn embedding ~vài trăm token):**
1. **Tiếng Việt không dấu giết embedding**: 0/8 vs 3/8 — mà khách thật (và chính bộ demo case
   của dự án) gõ không dấu. Chế độ người-dùng-thật đang ở vùng 0/8.
2. **Có dấu vẫn chỉ 3/8** — khớp độc lập với quan sát security từ trước ("kết quả đầu cho
   'quy trình hoàn tiền' là danh sách tên dịch vụ") và với số end-to-end (3/5 câu chính sách fail).
3. **Chunk mang lỗi trích xuất PDF**: mẫu top-1 hiện `"Giao D ịch"`, `"liên k ết"` — khoảng
   trắng chèn giữa từ do extraction, tự nó phá cả embedding lẫn khớp từ khoá.

## 1. Đọc 3 nguồn — cái gì áp được, cái gì dự án ĐÃ có, cái gì KHÔNG nên bê nguyên

### 1a. LangSmith evaluation-concepts

Khung của họ: 4 loại evaluator (code / LLM-judge / human / pairwise) · offline vs online ·
dataset→experiment→regression/backtesting · bắt đầu 10-20 ca tay rồi nở.

**Dự án ĐÃ có (và có phần MẠNH hơn chuẩn họ mô tả):**
- Offline eval + regression + backtesting: golden 120 · adversarial 45+ · heldout 60 (chạy-một-lần)
  · cơ chế so-cặp trước/sau **đóng dấu cả THƯỚC lẫn VẬT** (Luật 6) — LangSmith không đề cập tới
  mức kỷ luật này.
- Code evaluators là xương sống: origin-rule, xep_trang_thai, cổng-96, cổng 0/20, number-grounding.
- Human eval: PO duyệt demo case, biên bản nghiệm thu.

**Dự án THIẾU (đây là chỗ 3 nguồn thật sự giúp):**
1. **Đánh giá TỪNG BƯỚC trung gian (component-level)** — end-to-end thấy "3/5 câu chính sách fail"
   nhưng không tách được lỗi tại retrieval / bộ lọc / generation. Phép đo §0 chứng minh: một
   retrieval-eval cô lập tầng truy hồi trong VÀI GIÂY, 0đ LLM. Đúng Luật 13 của chính dự án
   ("ném vật vào lưới, không chờ diễn viên ngã") — giờ áp cho RAG.
2. **LLM-judge chưa được HIỆU CHUẨN**: `run_llm_judge_set.py` tồn tại nhưng chưa ai đo
   judge-vs-người đồng thuận bao nhiêu %. Một thước chưa hiệu chuẩn + nhiễu nền 20/40 case tự lật
   = số judge đơn lượt gần như vô nghĩa.
3. **Pairwise**: chưa có — hữu ích khi so hai bản prompt mà điểm tuyệt đối khó tin.
4. Online/production eval: chưa cần (pilot hoãn) — ghi nhận, không làm.

### 1b. OpenAI Evals + Graders API

Taxonomy grader: `string_check` (eq/ne/like) · `text_similarity` (cosine/rouge/fuzzy) ·
`score_model` / `label_model` (LLM chấm) · `python` (tự viết) · multi.

**Nhận định: LẤY TAXONOMY, KHÔNG lấy HOSTED SERVICE.** Ba lý do đo được:
1. **Dữ liệu**: đẩy eval lên dịch vụ hosted = transcript/tool-payload rời hạ tầng — dự án VỪA
   tắt LangSmith tracing có chủ đích vì đúng lý do này (F-30, NĐ 13/2023 Đ25). Bê eval lên cloud
   là mở lại cùng cánh cửa bằng tên khác.
2. **Grader của ta cần chạm DB**: origin-rule phải truy `tool_results` payload để biết số có
   nguồn không — grader hosted không với tới DB nội bộ. `python` grader của họ chạy sandbox
   phía OpenAI, không phải máy mình.
3. **Kỷ luật thước-vật**: harness nội bộ đã bắt được over-block 27/96=28% ở 0 TPM TRƯỚC khi tốn
   tiền end-to-end — bằng chứng local-first hoạt động. Hosted eval không cho đóng dấu he_thong/
   image-ID theo nếp của đội.

**Việc đáng làm từ nguồn này**: chuẩn hoá mỗi ca eval TỰ KHAI loại grader
(`string_check`/`python`/`score_model`) thay vì logic chấm trộn trong runner — cấu trúc lại,
không viết lại; mở đường sau này nếu muốn export sang format chuẩn.

### 1c. RAG chunking & retrieval

Số §0 chỉ thẳng 3 đòn bẩy, mỗi đòn có cơ chế dự đoán được:
1. **Chuẩn hoá dấu ở tầng QUERY** (hoặc index kép có-dấu/không-dấu): kỳ vọng kéo chế độ
   không-dấu ≈ có-dấu (0/8 → ~3/8 ngay, chưa sửa gì khác).
2. **Chunking theo CẤU TRÚC tài liệu**: kho FAQ có đơn vị tự nhiên ("217. Tài khoản bị trừ
   tiền...") — chunk theo từng câu-hỏi-FAQ và theo Điều/Khoản của ToS, thay vì cắt theo cỡ.
   Top-1 hiện tại dính chunk "danh sách tên dịch vụ" = triệu chứng kinh điển của cắt-theo-cỡ.
3. **Hybrid BM25 + embedding**: "hạn mức" nằm NGUYÊN VĂN trong 40 chunk mà embedding vẫn trượt —
   keyword-match sẽ bắt được; hybrid là chuẩn ngành cho corpus thuật-ngữ-cố-định.
   (+ đòn 0: làm sạch extraction PDF — "Giao D ịch" phá mọi thứ phía sau.)

**Nguyên tắc thí nghiệm (nếp sẵn của đội)**: một-biến-một-lần, đo trên cùng golden-set,
nhãn vật (image + he_thong + bản kho). KHÔNG nới ràng buộc 9 — sửa truy hồi, không nới prompt.

## 2. PHƯƠNG ÁN TỰ CHẤM ĐIỂM — "Kim tự tháp 3 tầng + scorecard một trang"

### Tầng 1 — Grader tất định (GATE, chạy mọi PR, 0đ LLM) — ĐÃ CÓ, THÊM 1 MẢNH
Giữ nguyên: invariants 23 · origin-rule · cổng-96 · cổng 0/20 · number-grounding.
**THÊM: Retrieval Gate** — golden-set truy hồi 30-50 câu (mỗi câu: query có-dấu + không-dấu,
nhãn đoạn-tài-liệu chứa đáp án), chấm Recall@3 + MRR. Chi phí/lượt: ~50 embedding call ≈ 0đ.
Mốc nền hôm nay: **0/8 · 3/8**. Ngưỡng đề xuất sau khi sửa: **Recall@3 ≥ 80% cả hai chế độ gõ.**

### Tầng 2 — LLM-judge CÓ HIỆU CHUẨN (chỉ cho tiêu chí chủ quan: đồng cảm, giọng)
Ba điều kiện bắt buộc trước khi số judge được tính vào bất kỳ gate nào:
1. **Hiệu chuẩn judge**: 30 ca PO gán nhãn tay một lần → đo % đồng thuận judge-vs-người.
   **≥85% mới được dùng**; dưới ngưỡng thì sửa prompt judge (few-shot từ chính ca lệch), đo lại.
   (Đây là "align your judge" của LangSmith — dự án chưa từng làm.)
2. **temp=0 + k=3 majority vote**: nhiễu nền đã đo 20/40 case tự lật giữa hai lượt giống hệt —
   không k-lặp thì mọi delta nhỏ là ảo. k=3 đưa xác suất đọc-nhầm-một-ca từ ~p xuống ~3p²(1-p)+p³
   (p=0.2 → ~10%; p=0.1 → ~2.8%).
3. **Luật đọc delta**: chỉ tin khác biệt giữa hai bản khi nó LỚN HƠN nhiễu nền đo được của chính
   metric đó (đo nhiễu = chạy k lần cùng một bản).
Chi phí: 20 ca chủ quan × k=3 × ~800 token ≈ **48k token gpt-4o-mini/lượt** — trong trần TPM,
rẻ hơn một lượt golden-set end-to-end nhiều lần.

### Tầng 3 — Human spot-check có cấu trúc (PO, 15 phút/tuần)
5 hội thoại thật (demo/rehearsal) mỗi tuần, 3 câu hỏi cố định (đúng dữ liệu? giọng ổn? có gì
lạ?) — nguồn ca mới cho golden-set + nguồn nhãn cho hiệu chuẩn judge. Đúng "human feedback là
đánh giá giá trị nhất" (LangSmith) nhưng đóng khung 15 phút để bền.

### Scorecard MỘT TRANG (chạy mỗi PR đáng kể)
```
Invariants        23/23        [gate]     0đ
Contract drift    3/3          [gate]     0đ
Retrieval@3       x% dấu/khôngdấu [gate mới] ~0đ
Over-block        0/96 · 0/20  [gate]     0đ
Grounding số      x/y          [gate]     0đ
Judge (đồng cảm)  x% (k=3, đã hiệu chuẩn 85%+)  ~48k tok
E2E golden 120    CHỈ trước release / đổi model  [đắt, nhiễu — không chạy mỗi PR]
```

## 3. Trình tự thực thi đề xuất (mỗi bước một PR, đo trước-sau)

1. **Tester**: dựng retrieval golden-set 30-50 câu (cặp có-dấu/không-dấu, nhãn đoạn đáp án)
   + script Recall@3/MRR → chạy MỐC NỀN đầy đủ. (Nở từ 8 câu hôm nay — đã chứng minh cách làm.)
2. **Coder**: đòn rẻ nhất trước — (a) làm sạch extraction PDF, (b) chuẩn hoá dấu tầng query.
   Đo lại sau MỖI đòn riêng.
3. **Coder**: chunking theo cấu trúc (FAQ-question / Điều-Khoản) → đo. Nếu chưa đạt 80%:
   hybrid BM25. (Từng đòn một, không gộp — Luật 8.)
4. **Tester + PO**: hiệu chuẩn judge (30 nhãn tay, đo đồng thuận) → bật tầng 2.
5. **PO-agent**: scorecard tổng hợp vào CI (khi billing thông) + báo cáo một-trang mỗi tuần.

## 4. Điều KHÔNG làm, ghi rõ để khỏi bàn lại

- KHÔNG đẩy transcript/eval lên LangSmith/hosted evals với dữ liệu thật (F-30, NĐ 13 Đ25).
- KHÔNG lấy điểm judge đơn-lượt làm gate (nhiễu 20/40).
- KHÔNG nới ràng buộc 9 (cấm bịa) để "cải thiện điểm trả lời chính sách" — sửa truy hồi.
- KHÔNG chạy golden 120 end-to-end mỗi PR (đắt, nhiễu, không thêm thông tin so với scorecard).
