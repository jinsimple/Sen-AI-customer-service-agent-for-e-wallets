# Tối ưu token — audit nội bộ + chuẩn ngành + kế hoạch (PO nêu: 63M token/7 ngày khi chưa có user)

## 1. TIỀN ĐANG CHẢY ĐI ĐÂU (audit đo trong phiên)

| Nguồn tiêu | Số đo | Hệ quả |
|---|---|---|
| System prompt | **~5.400 token**, gửi lại MỖI bước LLM | Nhân với mọi thứ bên dưới |
| Vòng ReAct | trần **20 bước/lượt**, mỗi bước GỬI LẠI TOÀN BỘ (prompt+tools+history+tool results) | Lượt 10 bước ≈ 100-150k input — khớp "1 user tuần tự bão hoà 200k TPM" |
| Tool result | **KHÔNG cắt bớt** trước khi đưa lại LLM (grep: không có truncate) | Payload lớn lặp qua các bước |
| History | MemorySaver replay đầy đủ, không window/summary | Lượt càng dài càng đắt luỹ tiến |
| Ca timeout | đốt trọn 20 bước × full context rồi vẫn fallback | Token chết — đã biết từ điều tra timeout |
| Eval | usage ĐÃ được ghi cộng dồn trong `_harness.py` | → tách được 63M theo nguồn, tester làm |

Quy đổi tiền (gpt-4o-mini $0.15/M in · $0.60/M out, ~85-90% là input do ReAct):
**63M/7 ngày ≈ 9M/ngày ≈ $1,5-2/ngày ≈ $10-14/tuần.** Chưa phải khủng hoảng TIỀN —
nhưng là khủng hoảng CẤU TRÚC: token/lượt cao chính là thứ (a) bão hoà TPM với MỘT user,
(b) nhân tuyến tính khi 150 user vào.

## 2. CHUẨN NGÀNH (nguồn kèm cuối file chiến lược)

- **OpenAI Prompt Caching**: TỰ ĐỘNG, prefix ≥1024 token lặp trong ~5-10 phút → **giảm 50% giá
  input phần cache**. gpt-4o-mini hỗ trợ. Không phải sửa code — chỉ phải đảm bảo PHẦN ĐẦU prompt
  ổn định (system+tools trước, phần động sau). Đọc được hit qua `usage.prompt_tokens_details.cached_tokens`.
- **Batch API**: −50% mọi model, CỘNG DỒN với prompt caching, không ăn TPM — chuẩn cho eval/Chấm-MỐC.
- **Semantic caching** (GPTCache/Redis-vector): ngành báo giảm 20-86% chi phí ở production support
  bot (case $47k→$12.7k/tháng; hit-rate 61-68%; bot 4k-system+6k-RAG giảm 76%). ĐỂ DÀNH cho pha
  có-người-dùng (test hiện tại câu hỏi ít lặp → hit thấp).
- Chuẩn chung: tool-result truncation · history window+summary · early-stop · model routing.

## 3. KẾ HOẠCH — 5 đòn, ước lượng tiết kiệm, thứ tự theo rẻ-trước

| # | Đòn | Ước tiết kiệm | Ai | Ghi chú |
|---|---|---|---|---|
| T1 | **Kích hoạt prompt-cache hit**: kiểm prefix ổn định (system+tools đứng đầu, mọi thứ động — ngày giờ, user info — đẩy xuống sau), log `cached_tokens` vào envelope/eval | **~40-50% input** trong-lượt (20 bước cùng prefix) | coder | Gần như free — chỉ sắp xếp lại + đo |
| T2 | **Batch API cho eval/Chấm-MỐC** | **−50%** chi phí eval + 0 áp lực TPM | coder (runner) | Stack với T1 |
| T3 | **Cắt tool-result + window history** (cap payload đưa LLM; giữ k=3 chunk như hiện tại; history N tin cuối + tóm tắt) | 20-40% input lượt dài | coder | MỘT ĐÒN MỘT PR, đo token/lượt trước-sau |
| T4 | **Early-stop ca lặp-vòng** (đường "trừ 2 lần không mã" đốt 20 bước) | token-chết về ~0 | coder | Đã có chẩn đoán từ điều tra timeout |
| T5 | **Semantic cache câu hỏi chính sách** | 20-60% khi CÓ user thật | hoãn tới pilot | Cần guardrail cache-đúng-vai |

**Thước đo mới (vào benchmark trục Hiệu-năng): token/lượt (input+output+cached) — tester thêm
cột từ usage đã ghi.** Mục tiêu sau T1-T3: **lượt chat điển hình < 30k input** (từ ~100-150k).

## 4. Việc giao
- **Tester**: bẻ 63M theo nguồn từ usage logs đã có (eval nào, probe nào, demo nào) + thêm cột
  token/lượt vào scorecard. 0 TPM.
- **Coder**: T1 (kiểm+log cached_tokens, sắp prefix) → T2 (batch cho runner) → T3 → T4. Mỗi đòn
  một PR, số token trước/sau trong message.
- **KHÔNG làm**: semantic cache lúc này · đổi model · nới trần bước.
