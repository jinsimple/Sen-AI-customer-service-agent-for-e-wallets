# 5 ca khó nhất RAG chính sách — khung ghi (điền sau khi qua mốc quay + vá ngưỡng land)

> Nguồn: `docs/giao-viec/2026-09-04-ke-hoach-test-rag-chinh-sach.md`. 5 ca do PO gợi ý, QA chốt đồng ý
> (xem log điều phối). Trigger chạy: (1) vá ngưỡng RAG đã land + Review soát, VÀ (2) qua mốc quay.
> Nhãn kỳ vọng lấy từ `eval/rag_policy_set.jsonl` (đã đăng ký trước — KHÔNG sửa nhãn sau khi thấy kết quả).

## Cách điền
- Chạy trên UI thật po-demo, ô "Tra cứu chính sách" trang CSKH.
- Ảnh: chụp full page, đặt tên `RAG5-<id>-<mo-ta-ngan>.png`, lưu cùng thư mục với file này.
- Đối chiếu **displayed text** (câu trả lời) VỚI **kết quả tool/API thật** (status found/not_found,
  chunk_id trả về) — đúng phương pháp đã dùng cho RB3/K1-K7, đừng chỉ tin câu chữ hiển thị.
- Đạt/Lệch: ghi thẳng, không tô. "Lệch" phải kèm ảnh + JSON response thật, không suy đoán.

## Bảng ghi

| # | id (rag_policy_set) | Câu hỏi | Nhãn kỳ vọng | Đạt/Lệch | Ảnh | Response thật (status/chunk_id) | Ghi chú |
|---|---|---|---|---|---|---|---|
| 1 | R1-02 | "phí rút" | found, chunk ∈ {CHK-2088a419f862, CHK-77260e1b5f5f} | _(điền)_ | _(điền)_ | _(điền)_ | Chính bug PO gặp — ưu tiên xác nhận vá thật |
| 2 | R3-01 | "phí rút" ↔ "phí rút tiền từ ví về ngân hàng là bao nhiêu" | found, CÙNG chunk cả 2 độ dài | _(điền)_ | _(điền)_ | _(điền)_ | Vá recall mà lệch chunk giữa 2 độ dài = vá chưa triệt để |
| 3 | P2-01 | "giá vàng hôm nay bao nhiêu" | not_found | _(điền)_ | _(điền)_ | _(điền)_ | Kiểm precision KHÔNG bị nới theo khi vá recall |
| 4 | F1-01 | "phí rút tiền từ ví về ngân hàng là bao nhiêu" (khi sidecar rerank tắt/chặn) | not_found tử tế, KHÔNG crash/off-topic | _(điền)_ | _(điền)_ | _(điền)_ | 🔴 Cần tech-lead/DevOps xác nhận cách ép sidecar chết AN TOÀN trước khi chạy — không tự đoán cách chặn |
| 5 | T1-01 | "phí rút tiền từ ví về ngân hàng là bao nhiêu" (ngay sau rebuild po-demo) | found, KHÔNG timeout→rỗng | _(điền)_ | _(điền)_ | _(điền)_ | 🔴 Cần phối hợp đúng thời điểm rebuild với Coder/DevOps — không tự rebuild po-demo |

## Trước khi chạy — điều kiện cần xác nhận riêng

- [ ] Vá ngưỡng RAG (re-tune rerank câu ngắn) đã **land** trên po-demo (hash/commit xác nhận qua Lead).
- [ ] Đã qua mốc quay (PO xác nhận).
- [ ] Ca #4 (F1-01): có phương án ép sidecar chết AN TOÀN, không ảnh hưởng dữ liệu/service khác — hỏi
      tech-lead/DevOps trước, không tự ý chặn network/kill process.
- [ ] Ca #5 (T1-01): có cửa sổ rebuild po-demo đã lên lịch, chạy câu hỏi NGAY sau khi container backend
      vừa healthy trở lại — phối hợp thời điểm với Coder/DevOps, không tự rebuild.

## Sau khi điền — báo cáo

Tổng hợp Đạt/Lệch 5 ca → gửi Lead → Lead chuyển PO review (PO tự xem cuối, không xem sớm theo lệnh đã
chốt). Nếu có ≥1 ca Lệch: mô tả CƠ CHẾ lệch (không chỉ số đếm), kèm ảnh + response JSON thật.
