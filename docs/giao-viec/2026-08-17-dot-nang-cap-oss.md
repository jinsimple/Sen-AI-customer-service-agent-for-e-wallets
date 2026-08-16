# Đợt nâng cấp Open-Source — kế hoạch & điều kiện nghiệm thu

> PO thật duyệt triển 16/08 tối (sau đối chiếu workshop RAG + khảo sát OSS — nguồn: STATE
> `a843f98`, mục "HƯỚNG NGHIÊN CỨU SAU GATE"). Bối cảnh chốt: đích thiết kế 100 CSKH + khách
> không giới hạn; API LLM xịn sẽ có ở giai đoạn khách thật (TPM = việc-đã-có-chủ); vector DB
> CHỐT Qdrant.
>
> **Nguyên tắc xuyên suốt (không nhân nhượng):** ① mọi công cụ phải TỰ HOST — không dữ liệu nào
> rời hạ tầng (bài F-30/LangSmith) ② mọi đòn đo trước-sau trên bộ 47 ca thước-đã-rà, nghiệm thu
> hai chiều (ca trượt lên + không ca đang-đạt nào rơi) ③ số-không-lợi-ích = revert ④ framework là
> nguồn CÔNG THỨC, thước đã hiệu chuẩn của tester là nguồn SỰ THẬT ⑤ không push code khi PR #11
> chưa merged.

## SÓNG 1 — chạy được NGAY (không đụng pool gpt-4o-mini, sống chung với đóng băng)

### N1 · Thí điểm RERANKER tại chỗ — coder · ưu tiên cao nhất về chất lượng
- Tải 2 ứng viên: **BAAI/bge-reranker-v2-m3** (Apache 2.0, ~278M, CPU được) và **ViRanker**
  (chuyên tiếng Việt, nền BGE-M3 — kiểm giấy phép trước khi cân nhắc production).
- Đo KHÔ kiểu ②-thí-điểm (không đụng kho phục vụ): baseline top-4 hiện tại vs đường
  **top-20 → rerank → top-4**, trên trọn bộ 47 ca, cả hai model, A/B.
- **Nghiệm thu:** (a) Recall@4 tăng có nghĩa (vượt nhiễu nền đo được — tự công bố ngưỡng TRƯỚC
  khi chạy, đúng Luật khai-luật-dừng-trước) (b) TRỌN 47 ca: 0 ca đang-đạt rơi (c) latency rerank
  ≤ ~300ms CPU/lượt trên máy dev (d) đóng dấu THƯỚC+VẬT + model-hash. Đặc biệt soi 6 ca ToS
  văn-phong-lệch (RAG-37/39/40/41/43/47) — reranker cross-encoder sinh ra để xử đúng lớp này.
- Chỉ land vào sản phẩm SAU khi có số + PO-agent GO; land = thêm bước trong search_policy_text,
  bật/tắt bằng config, mặc định TẮT cho tới khi nghiệm thu trên staging.

### N2 · MRR + NDCG vào benchmark — tester · gần miễn phí
- Mượn công thức từ RAGAS (Apache 2.0) — KHÔNG thay harness; script tự tính từ hạng đã ghi.
- In cạnh Recall@k mỗi lượt chấm; chạy lại trên số liệu ĐÃ CÓ (0 LLM) để có mốc nền trước-reranker.
- Giá trị: phân biệt "trượt sát top-4" với "chìm >100" — độ phân giải mà pass/fail không có.

### N3 · Thẩm định data-flow 3 công cụ hạ tầng — security · trước khi bất kỳ cái nào vào compose
- **LiteLLM proxy**: config nào tắt log prompt/response? key management? budget-per-key?
- **Langfuse self-host**: dữ liệu nằm đâu (Postgres riêng?), có gọi về nhà không (telemetry)?
- **Semantic cache** (chỉ thiết kế, chưa làm): ranh giới CỨNG câu-chính-sách-chung vs câu-cá-nhân
  — cache lẫn của người khác = thảm hoạ; đề xuất tiêu chí máy-kiểm-được.
- Sản phẩm: 1 trang ý kiến / công cụ, mẫu như F-LOG-3 (trường nào được ghi, retention, cờ đỏ).

## ⭐ N7 · ĐỔI API SANG QWEN — PO thật quyết 16/08, ƯU TIÊN CAO, làm ngay sau gate

**Thiết kế: TÁCH CHAT KHỎI EMBEDDING.** `LLM_*` (chat → Qwen) và `EMBEDDING_*` (GIỮ OpenAI) là
hai bộ biến riêng, đều fallback về `OPENAI_*` ⟹ không đổi hành vi mặc định khi land. Lý do tách:
đổi embedding = **đổi VẬT** → nạp lại kho + mọi số truy hồi cắt chuỗi; chat mới là chỗ đốt tiền
(prompt ~5.400 token × tới 20 bước). Kèm: `RAG_EMBEDDING_MODEL` đang hardcode (`config.py:223`)
đưa ra env; thêm `JUDGE_MODEL` riêng — giám khảo phải khác model bị chấm (nếu không: Qwen tự
chấm Qwen). 4 chỗ sửa: `config.py` · `graph.py:239` · `store.py:41` · `eval/_llm_judge.py:51`.

**Thứ tự — ĐỔI MODEL TRƯỚC F-31/32 (PO-agent tự đính chính quyết định cũ):** F-31/32 là bản vá
PROMPT, phụ thuộc chặt vào cách model diễn giải MISINFO-002. Vá trên gpt-4o-mini rồi đổi model =
bản vá có thể không chuyển giao, làm lại từ chẩn đoán. ⟹ đổi model → đo lại mốc nền trên Qwen →
rồi vá F-31/32 trên chính model sẽ chạy thật. Sửa một lần thay vì hai.

**HOÁ ĐƠN ĐO LẠI (khai minh thị, không được giả định chuyển giao):** An toàn 30/30 (cổng-96 ·
adversarial 45 ca · over-block 0/96) hiệu chuẩn trên gpt-4o-mini → chạy lại TOÀN BỘ trên Qwen —
đây là tài sản lớn nhất dự án. Kèm 4 chỗ nhỏ: F-33 parse chuỗi lỗi 429 kiểu OpenAI (Qwen khác →
vá thoái hoá im lặng; test hardcode chuỗi) · `cached_input_tokens` đọc `input_token_details` kiểu
OpenAI (có thể báo 0 im lặng) · bảng giá `eval/measure_quality.py:67` · `test_genai_spans.py`
assert `"gpt-4o-mini"`. Ràng buộc security (chờ ý kiến): dữ liệu hội thoại đi tới hạ tầng Alibaba
Cloud — data residency NĐ 13/2023 Điều 25 + điều khoản train-on-data.

## NGUYÊN TẮC CẢ ĐỢT (security, N3 — nâng thành bắt buộc)
> **Mỗi công cụ mới phải khai nó thuộc CỬA NÀO trong khung ADR-025 trước khi vào compose.**
> Thêm một nơi dữ liệu tồn tại ngoài khung là cách một ADR thành giấy lộn.

## SÓNG 2 — sau #11 merged + N7 (thứ tự coder: đính-chính graph.py → dấu-build → cổng APP_ENV →
## N7 Qwen → đo lại An toàn/benchmark trên Qwen → F-31/32 → rồi mới sóng 2)

### N4 · Migrate Chroma → QDRANT — coder
4 điều kiện đã chốt (STATE `1f12244`): kỷ luật hai-kho vĩnh viễn (tem + canary + một-đường-nạp) ·
bộ lọc ADR-026 giữ ở bước SQL · nghiệm thu 47 ca recall-không-tụt với `exact=true` cho benchmark
(HNSW cho production) · vào compose cả hai profile. Kèm: gỡ Chroma khỏi requirements khi xong —
không nuôi hai đường.

### N5 · LiteLLM proxy — coder, sau ý kiến security
Hàng đợi chống burst-429 (cần ở MỌI hạn mức) + budget theo ngày + cache Redis (Redis có sẵn
trong stack). Nghiệm thu: ép burst → không request nào của khách nhận lỗi trần trụi; F-33/33b
chạy lại trên đường mới.

### N6 · Langfuse self-host — coder dựng, tester + PO thật dùng
Mục tiêu số 1: màn gán nhãn cho gói 30-nhãn hiệu chuẩn judge (thay bảng tay). Số 2: cost/trace
theo lượt. Điều kiện: telemetry-về-nhà tắt, chạy cạnh stack local trước, production tính sau.

## SÓNG 3 — pilot (đúng hẹn cũ, không sớm hơn)
Semantic cache cho câu chính-sách-chung — chỉ sau khi có ranh giới máy-kiểm-được từ N3 và có
traffic thật để đo hit-rate. Không land trước pilot.

## Việc KHÔNG nằm trong đợt này (đã bác bằng số hoặc chưa tới lúc)
HyDE · BM25/RRF thuần · LLM-chunking chèn câu hỏi (② xổ số) · PageIndex cho ToS (đáng nghiên
cứu, đợi API xịn vì tốn lượt LLM mỗi truy vấn — ghi sổ, chưa lịch) · thay harness đo bằng
framework ngoài.
