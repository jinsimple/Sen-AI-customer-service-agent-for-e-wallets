# Evaluation Report

> Báo cáo đánh giá chất lượng sản phẩm theo tiêu chí BTC.
> Chỉ số và cách đo bám theo `FIN05-Data-Brief.md` §6. Số liệu được test runner điền tự động, không nhập tay.

---

## 1. Metrics

### 1.1 Tiêu chí BTC

| Metric | Target | Đo bằng | Actual | Status |
|--------|--------|---------|--------|--------|
| Response accuracy | >80% | T3 — độ chính xác phân loại khiếu nại & phạm vi giao dịch (ngưỡng nội bộ chặt hơn: ≥95%, xem §1.2) | — | ⏳ |
| Response latency | **<90s (p50)** | T3 — đo trên 180 case golden set (120 dev / 60 held-out) | — | ⏳ |
| User satisfaction | >4/5 | Khảo sát người test, tổng hợp ở §3 | — | ⏳ |
| Test coverage | >60% | `pytest --cov=src` | — | ⏳ |

> **Về mốc latency.** Template gốc đặt `<3s`. FIN-05 là agent **điều tra đa bước** — mỗi lượt trả lời gồm nhiều tool call nối tiếp (`lookup_transaction` → đọc timeline → đối chiếu → `create_ticket`/`propose_resolution`), nên `<3s` không đạt được với bất kỳ mô hình nào và cũng không phải thứ đáng tối ưu. Mốc dùng cho dự án này là **`<90s` ở p50**, theo PRD §8 ("đủ nhanh để demo mượt", không có SLA production). Đo ở p50 chứ không phải trung bình vì phân bố latency của agent lệch phải mạnh — một case `trap` nhiều bước có thể kéo dài gấp vài lần median mà không phản ánh trải nghiệm thường gặp.

### 1.2 Chỉ số riêng của FIN-05 (Data Brief §6.8)

Cột **Dev / Held-out** chỉ áp cho chỉ số chạy qua agent (T3–T5); chênh lệch giữa hai cột chính là thước đo chống overfit prompt.

| # | Chỉ số | Tầng | Ngưỡng | Dev (120) | Held-out (60) | Status |
|---|--------|------|--------|-----------|---------------|--------|
| 1 | Groundedness violation rate | T4 | **0%** | — | — | ⏳ |
| 2 | PDPA masking violation | T2 | **0%** | — | n/a | ⏳ |
| 3 | Số lần agent tự thực thi thay đổi số dư | T5 | **0** | — | — | ⏳ |
| 4 | Độ chính xác phân loại khiếu nại (4 nhóm) | T3 | ≥ 95% | — | — | ⏳ |
| 5 | Độ chính xác xác định phạm vi giao dịch | T3 | ≥ 95% | — | — | ⏳ |
| 6 | Độ chính xác chọn đích escalate | T3 | 100% | — | — | ⏳ |
| 7 | Tỉ lệ hỏi lại đúng lúc trên case `ambiguous` | T3 | ≥ 85% | — | — | ⏳ |
| 8 | Phủ ma trận 12 ô + phủ độ khó | T1 (I8) | 100% | — | n/a | ⏳ |
| 9 | Chênh lệch dev vs. held-out | T3 | ≤ 10 điểm | — | — | ⏳ |
| 10 | Độ trễ phản hồi (p50) | T3 | **< 90s** | — | — | ⏳ |

**Ba chỉ số không có "gần đạt"** — chỉ số 1, 2, 3 phải bằng 0 tuyệt đối. Đây là hiện thực hoá ràng buộc Brief §6.1–6.3; một vi phạm duy nhất là fail, không làm tròn.

---

## 2. Test Results

### T1 — Chất lượng dữ liệu (không cần LLM, chạy trong CI)
```
pytest tests/test_data/ -v
# Paste output here
```

### T2 — Tool (không cần LLM, chạy trong CI)
```
pytest tests/test_tools/ -v
# Paste output here
```

### T3–T4 — Phân loại, định tuyến & chống bịa số liệu (cần API key)
```
pytest tests/test_agent_eval/ -v
# Paste output here
```

### T5 — Guardrail HITL & phân quyền (cần API key)
```
pytest tests/test_guardrails/ -v
# Paste output here
```

### Coverage
```
pytest --cov=src --cov-report=term-missing
# Paste output here
```

> Dataset dùng khi chạy: `dataset-v1.0-demo` · seed `20260802` · checksum lấy từ `data/generated/manifest.json`.
> Ghi lại ba giá trị này mỗi lần chạy — không có chúng thì kết quả không tái lập được và không so sánh được giữa các lần.

---

## 3. User Feedback

| User | Feedback | Rating |
|------|----------|--------|
| [User 1] | [feedback] | [1-5] |
| [User 2] | [feedback] | [1-5] |

## 4. Demo Results

- Ngày demo: [YYYY-MM-DD]
- Người tham gia: [số người]
- Feedback chung: [tóm tắt]
- Issues phát hiện: [danh sách]

## 5. Action Items

- [ ] [Cần cải thiện 1]
- [ ] [Cần cải thiện 2]
