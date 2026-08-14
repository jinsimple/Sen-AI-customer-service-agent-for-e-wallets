# GIAO VIỆC — tech-lead — tối 13/08, chuẩn bị demo pitching 14/08

> PO giao. Dán nguyên văn file này vào phiên Claude tech-lead.
> Kết quả báo cáo lại cho PO theo đúng "ĐỊNH DẠNG BÁO CÁO CUỐI" ở dưới.

---

Bạn là **tech-lead** của FIN-05. NGÀY MAI (14/08) PO demo pitching cho khách
hàng — tối nay bạn có 2 nhiệm vụ, làm ĐÚNG THỨ TỰ, không làm gì ngoài phạm vi.

**Đọc trước khi làm:** `CLAUDE.md` → `docs/STATE.md` →
`docs/DEMO-READINESS-2026-08-14.md` (mục A: R1, R3 — brief gốc) →
5 ADR cuối trong `docs/DECISIONS.md` (đặc biệt ADR-010, ADR-014, ADR-015).

**Xác nhận trước khi bắt đầu (trả lời ngắn cho PO):**
a. Vùng bạn ĐƯỢC ghi và KHÔNG được ghi tối nay?
b. Ràng buộc cứng nào dễ chạm nhất trong 2 nhiệm vụ dưới? Vì sao?
c. Một điểm bạn thấy thiếu/mâu thuẫn thông tin (bắt buộc nêu ít nhất 1).

## Bối cảnh

- Repo ở HEAD `955264f`, có **6 file sửa dở chưa commit**:
  `eval/measure_quality.py` (+128 dòng — logic rescore, của phiên QA/QC),
  `src/agents/graph.py`, `src/api/live_chat_ws.py`,
  `frontend/src/lib/server-api.ts`, `tests/test_api/test_live_chat_ws.py`,
  `tests/test_services/test_fault_tolerance.py`.
- Stack Docker đang chạy 6 container `fin05-*` healthy.
- **Cảnh báo có sẵn:** LangSmith tracing ĐÃ HẾT QUOTA THÁNG — gây nhiễu khi
  chạy test. Tắt tracing (unset biến env LangSmith) khi chạy test/đo để nhìn
  kết quả sạch. Cân nhắc tắt luôn cho container demo ngày mai — hết quota
  giữa demo có thể thêm latency/log lỗi vô ích.

## NHIỆM VỤ 1 — R3: Chốt trạng thái code (~30–45 phút, làm TRƯỚC)

1. Đọc diff 6 file dở, đánh giá từng file: hoàn chỉnh hay dở dang, có test đi
   kèm không.
2. Chạy thật: `pytest tests/test_invariants.py -v` (phải 19/19) ·
   `pytest tests/ -m "not security_finding"` ·
   `python scripts/check_contracts.py` · và test liên quan trực tiếp
   (`test_live_chat_ws`, `test_fault_tolerance`).
3. Tất cả xanh → commit 1–2 commit message rõ ràng (tách phần `eval/` rescore
   khỏi phần `src/` nếu độc lập). File nào dở/đỏ → stash riêng, ghi rõ stash
   gì và vì sao. Demo chạy trên trạng thái sạch.
4. Rebuild: `docker compose build && docker compose up -d`. **BẮT BUỘC** verify
   thay đổi có mặt TRONG container (`docker exec ... grep` một dòng code đặc
   trưng) — bài học thật của dự án, đừng tin "build thành công".
   Xác nhận `curl localhost/health` trả `env`/`db_kind=postgresql` đúng.

## NHIỆM VỤ 2 — R1: Điều tra latency (TIMEBOX 2 GIỜ — hết giờ là DỪNG)

Bối cảnh: sau khi bật PII scrub (ADR-010), p50 của `/agent/chat` tăng
24,3s → 37,7s (+55%), max 204s (nguồn: `eval/results/*_rescored.md`).
Nghi phạm số 1: Presidio/NER (underthesea) trong `src/observability/pii.py`
chạy ĐỒNG BỘ trên đường nóng cho mọi tin nhắn khách + mọi kết quả tool
(`src/agents/graph.py`, `src/agents/tools/customer_tools.py`).

1. **Đo trước, không đoán**: dùng Jaeger sẵn có (`fin05-jaeger-1`) hoặc timing
   log tạm — xác định bước nào ăn thời gian (lazy-init model NER mỗi request?
   scrub từng tool result? hay LLM chậm hơn vì prompt dài ra?).
2. CHỈ sửa nếu có fix AN TOÀN, rủi ro thấp, **không đổi hành vi che PII**
   (ADR-010 là ràng buộc cứng — TUYỆT ĐỐI không thu hẹp phạm vi scrub, không
   bỏ lớp NER lấy tốc độ). Fix an toàn hợp lệ: preload model lúc startup,
   cache instance, bỏ scrub trùng lặp trên cùng chuỗi.
3. Sửa xong: `pytest tests/test_security/test_pii_khong_ro_ri_len_llm.py`
   (11 test phải xanh) + đo lại thật vài request qua stack Docker, dán số
   trước/sau.
4. Không có fix an toàn trong 2 giờ → DỪNG, báo cáo phát hiện + đề xuất.
   PO sẽ chuyển phương án kịch bản demo. Đây là kết quả CHẤP NHẬN ĐƯỢC —
   không sửa ẩu trước ngày demo.

## Ràng buộc

- Chỉ ghi trong vùng tech-lead: `src/`, `frontend/src/`, `migrations/`.
  **KHÔNG chạm `contracts/`** — không có ADR nào được duyệt tối nay.
- Không refactor ngoài phạm vi 2 nhiệm vụ. Sáng mai KHÔNG sửa gì ngoài blocker.
- Không báo cáo hoàn thành từ suy luận tĩnh — mọi kết luận kèm output lệnh thật.

## ĐỊNH DẠNG BÁO CÁO CUỐI (gửi PO)

```
## R3 — Trạng thái code
(từng file: commit <hash> / stash / lý do · kết quả test · verify container)
## R1 — Latency
(bước nào chậm, bằng chứng đo · đã sửa gì / vì sao không sửa · số trước/sau)
## Còn treo cho sáng mai
## Điều PO cần quyết
```
