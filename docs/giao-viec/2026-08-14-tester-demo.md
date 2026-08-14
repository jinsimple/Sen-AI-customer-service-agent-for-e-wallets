# GIAO VIỆC — tester (QA/QC) — tối 13/08, chuẩn bị demo pitching 14/08

> PO giao. Dán nguyên văn file này vào phiên Claude tester.
> Kết quả báo cáo lại cho PO theo đúng "ĐỊNH DẠNG BÁO CÁO CUỐI" ở dưới.

---

Bạn là **tester** của FIN-05. NGÀY MAI (14/08) PO demo pitching cho khách
hàng — tối nay bạn có 2 nhiệm vụ (R6 và R4 trong
`docs/DEMO-READINESS-2026-08-14.md`, mục A).

**NHẮC LẠI RÀNG BUỘC VAI: bạn KHÔNG được đọc `src/`** — làm việc từ
`contracts/`, `docs/`, `eval/` và giao diện/API thật.

**Đọc trước khi làm:** `CLAUDE.md` → `docs/STATE.md` → `docs/TESTING.md` →
`docs/DEMO-READINESS-2026-08-14.md`.

**Xác nhận trước khi bắt đầu (trả lời ngắn cho PO):**
a. Vùng bạn ĐƯỢC ghi, và vì sao bạn KHÔNG được đọc src/?
b. Ràng buộc cứng nào liên quan nhất tới việc chọn case demo?
c. Một điểm bạn thấy thiếu/mâu thuẫn thông tin (bắt buộc nêu ít nhất 1).

## Bối cảnh & phối hợp

- Stack Docker chạy tại `localhost` (Caddy :80), backend healthy.
- **Phối hợp:** phiên tech-lead đang chốt code + rebuild container trong ~1
  giờ đầu tối nay. Vì vậy: làm PHẦN OFFLINE trước (bước 1 nhiệm vụ 1); trước
  MỌI lượt chạy live phải `curl localhost/health` xác nhận stack sống; bị đứt
  giữa chừng do rebuild → đợi rồi chạy lại, KHÔNG tính là bug.
- Bối cảnh chất lượng: bản đo mới nhất có **29/40 case vi phạm
  checks/forbidden** trên bộ chấm → KHÔNG được demo case ngẫu nhiên.

## NHIỆM VỤ 1 — R6: Chọn và kiểm chứng case demo (quan trọng nhất)

1. **(Offline)** Đọc `eval/results/quality_run_20260813_150352_raw_rescored.json`
   và `eval/results/baseline_TRUOC_khi_cat_token_raw_rescored.json` — lọc case
   PASS SẠCH ở CẢ HAI lần chạy: không vi phạm checks/forbidden, không nằm
   trong danh sách "ID chưa đối chiếu", latency thấp (ưu tiên case ít lượt).
2. Từ danh sách đó + `eval/golden_set.jsonl`, chọn **3–5 case demo** phủ đủ:
   - (a) 1 case tra cứu TÌM THẤY giao dịch (happy path)
   - (b) 1 case KHÔNG TÌM THẤY — chứng minh agent không bịa (điểm pitch mạnh nhất)
   - (c) 1 case trọn luồng: chat → tạo ticket (OTP step-up) → ticket vào hàng
     chờ CSKH
3. **(Live — sau khi health xanh)** Chạy thật từng case ≥2 lần qua stack
   Docker (harness sẵn trong `eval/`, cách chạy xem `docs/TESTING.md`).
   Ghi mỗi lượt: mở đầu có đồng cảm không ("Mình hiểu/biết…"), số liệu khớp
   không, có lộ tên thật/SĐT khách không (PII), latency.
4. Case chạy 2 lần đều đạt → vào danh sách chốt. Ghi kết quả vào
   **`eval/demo_cases_20260814.md`**: mỗi case gồm SĐT đăng nhập, lời thoại
   gõ vào, kết quả mong đợi, latency đo được, ghi chú cho người demo.

## NHIỆM VỤ 2 — R4: Kiểm chứng realtime live-chat đa worker

Bối cảnh: live-chat vừa đổi kiến trúc fan-out Redis pub/sub cho 4 worker
(ADR-015). Lỗi vỡ fan-out là lỗi IM LẶNG — tin biến mất, không exception —
và 1 kết nối đơn thường không bắt được vì hay rơi cùng worker.

1. Chạy `cd frontend && npx playwright test e2e/live-chat.spec.ts` (5 test).
2. Kiểm chứng 2 phía: 2 browser context Playwright riêng (khách + CSKH), gửi
   **≥5 tin MỖI CHIỀU xen kẽ**, assert từng tin xuất hiện phía bên kia trong
   thời gian hợp lý. Mở/đóng kết nối lặp lại để tăng xác suất rơi khác worker.
   Nếu `e2e/live-chat.spec.ts` hoặc `e2e/helpers` đã có kịch bản tương đương
   → dùng lại, đừng viết trùng.
3. Tin nào biến mất → **BLOCKER demo**, ghi rõ cách tái hiện.

## Ràng buộc

- Chỉ ghi trong `tests/`, `frontend/e2e/`, `eval/`.
- Báo cáo trung thực MỌI phát hiện — kể cả tin xấu ngay trước demo. PO cần
  sự thật để quyết kịch bản. Không tự ý "sửa cho qua".
- Test không chạy được → nói rõ chưa chạy được, không suy luận thay.

## ĐỊNH DẠNG BÁO CÁO CUỐI (gửi PO)

```
## R6 — Case demo chốt
(danh sách case + link eval/demo_cases_20260814.md · kết quả từng lượt chạy:
đạt/không, latency)
## R4 — Realtime 2 chiều
(kết quả playwright · kết quả 2 context ≥5 tin/chiều · có tin nào mất không)
## Blocker cho demo sáng mai
(nếu có — kèm cách tái hiện; không có thì ghi "không có")
## Điều PO cần quyết
```
