# Đợt đo 31/08/2026 — 246 ca, một bản mã, một ngày

**Vì sao thư mục này tồn tại:** toàn bộ kết quả đợt đo từng nằm **ngoài git**, một bản
duy nhất, trên một máy **không có Time Machine hoạt động**. PO thật ra lệnh đưa vào git
31/08. Bộ `heldout` **đã cháy** sau đợt này — chạy lại không cho ra phép đo học tủ nữa,
nên những tệp ở đây **không dựng lại được**.

## Danh tính lượt đo — khai trước mọi con số

| | |
|---|---|
| mô hình | `qwen3.8-flash` |
| băm mã nguồn | `9c17c5684c9a` (khớp HEAD lúc đo) |
| ngày | 31/08/2026 |
| ca chạy | 246 · **0 ca chết vì hạ tầng** |
| chi phí | 12.104.482 token · 1.467 lượt gọi (cả ngày, gồm cả lượt hỏng) |

🔴 **Thước đã dời:** `qwen3.8-flash` KHÁC model ghim `qwen3.7-plus-2026-05-26`. Các số ở
đây **không** đặt cạnh mốc đo cũ được. Chỉ `golden` ↔ `heldout` so được với nhau.

## Tệp

| tệp | nội dung |
|---|---|
| `golden38_tung_ca.jsonl` | 120 ca golden, mỗi dòng một ca — `checks` · `tool_calls` · `reply` · `all_agent_replies` · `all_customer_texts` |
| `heldout38_tung_ca.jsonl` | 60 ca heldout, cùng cấu trúc |
| `adversarial_run_*_140317_raw.json` | 46 ca đối kháng một lượt |
| `adversarial_run_*_141532_raw.json` | 20 ca đối kháng nhiều lượt |
| `adversarial_run_*.md` | báo cáo tương ứng |
| `usage_*.jsonl` | sổ chi phí từng lượt gọi mô hình — token, model, băm mã |

## Kết quả gọn

| | đạt trọn ca | đúng từng phép kiểm |
|---|---|---|
| golden 120 | 32 · 26,7% | 319/462 · 69,0% |
| heldout 60 | 14 · 23,3% | 158/236 · 66,9% |
| **lệch** | **−3,4 điểm** | **−2,1 điểm** |

Lệch nằm trong sai số cỡ mẫu 60 ca ⟹ **không có dấu hiệu học tủ**.
Đối kháng: 60/66 đạt — nhưng **4/6 ca trượt là thước bắt nhầm**, chỉ 2 là lỗi thật.

## Đọc rồi hãy trích — ba chỗ dễ trích sai

1. **`khong_tao_ticket_hop_le` là tỉ lệ ĐÚNG, không phải tỉ lệ hỏng.** 46,3% golden nghĩa
   là hỏng 53,7%. Đã có người trong đội trích ngược cực một lần.
2. **Không được nói "an toàn trên 66 ca đối kháng".** Thước khớp chuỗi, mù phủ định.
   Câu được phép: *không tìm thấy vi phạm trong những ca bị gắn cờ, sau khi đọc tay*.
   60 ca thước cho qua thì mới đọc tay được 20.
3. **Ca nhiều lượt: đọc `reply` KHÔNG đủ.** Phải đọc `all_agent_replies` +
   `all_customer_texts`. Lỗi nghiêm trọng nhất tìm được hôm nay — agent không nhận ra
   khách đã bỏ cuộc — chỉ lộ khi đối chiếu lượt N với lượt N−1.

Chi tiết đầy đủ: `docs/STATE.md §0b.15`.
