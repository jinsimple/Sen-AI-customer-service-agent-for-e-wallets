# GIAO VIỆC — tester (QA/QC) — SÁNG 14/08, smoke cuối trước demo pitching

> PO giao. Dán nguyên văn file này vào phiên Claude tester.
> Deadline: xong TRƯỚC giờ demo ≥1 giờ. Báo cáo theo "ĐỊNH DẠNG BÁO CÁO CUỐI".

---

Bạn là **tester** của FIN-05. Đêm qua toàn bộ blocker đã đóng (QA-01/13, R1
latency) và đã commit đủ (`2d9a709`→`f2d4785`, verify trong container). Sáng
nay bạn chạy **smoke cuối cùng** trước demo — mục tiêu là XÁC NHẬN, không phải
đào bới: tìm blocker thật nếu có, không mở rộng phạm vi.

**NHẮC LẠI RÀNG BUỘC VAI: KHÔNG đọc `src/`.** Làm từ `contracts/`, `docs/`,
`eval/` và giao diện/API thật.

**Đọc trước:** `docs/DEMO-READINESS-2026-08-14.md` (đặc biệt khối "⚡ CẬP NHẬT
SÁNG 14/08" — có 5 bẫy demo) → `eval/demo_cases_20260814.md` → `docs/TESTING.md`.

**Xác nhận trước khi bắt đầu (trả lời ngắn):**
a. Sáng nay bạn ĐƯỢC sửa gì và KHÔNG được sửa gì? (gợi ý: sáng demo = chỉ báo
   cáo, KHÔNG vá — kể cả lỗi nhỏ; mọi thay đổi code sáng nay đều phải qua PO)
b. Vì sao không được diễn tập live-chat quá nhiều lần trước giờ pitch?
c. Một điểm thiếu/mâu thuẫn thông tin bạn thấy (bắt buộc ≥1).

## QUY TẮC SÁNG DEMO — khác mọi phiên trước

1. **CHỈ BÁO CÁO, KHÔNG SỬA.** Phát hiện gì → ghi lại + báo PO ngay, kể cả
   thấy fix "chỉ 1 dòng". Sáng demo mọi thay đổi đều là rủi ro mới.
2. **Không chạy gì làm bẩn dữ liệu demo**: không tạo hàng loạt ticket rác cho
   USR-0145 (hàng chờ CSKH sẽ đầy rác khi chiếu màn hình), không chạy
   `ws_fanout_probe` lặp nhiều lần bằng tài khoản demo — **trần 60 tin/giờ**
   sẽ khoá đúng lúc pitch.
3. Blocker (luồng demo không đi được) → báo PO NGAY, không đợi gộp báo cáo.

## NHIỆM VỤ — theo thứ tự, tick từng dòng

### 1. Hạ tầng (5 phút — làm ĐẦU TIÊN)
- [ ] `docker ps` → 6 container `fin05-*` Up, backend `(healthy)`.
      LƯU Ý: KHÔNG dùng `curl localhost/health` để kết luận — Caddy đưa route
      đó về app, không ra JSON backend (đã xác minh sáng nay, không phải bug).
- [ ] `pytest tests/test_invariants.py -v` → 19/19.
- [ ] `python scripts/check_contracts.py` → sạch.

### 2. Smoke tự động (chạy tuần tự, ~15–20 phút)
```
cd frontend
npx playwright test e2e/login.spec.ts e2e/auth.spec.ts e2e/auth-multirole.spec.ts   # B1 đăng nhập
npx playwright test e2e/chat.spec.ts                                                 # B2 chat
npx playwright test e2e/ticket-detail.spec.ts e2e/dashboard.spec.ts                  # B3 ticket
npx playwright test e2e/live-chat.spec.ts                                            # B4 realtime (CHẠY 1 LẦN, không lặp)
npx playwright test e2e/accessibility.spec.ts                                        # B5 UX/WCAG
npx playwright test e2e/approve.spec.ts                                              # B6 duyệt
```
- [ ] Ghi kết quả từng nhóm: pass/fail/số test. Fail do stack chưa sẵn sàng →
      chạy lại 1 lần trước khi kết luận; fail lặp lại → nghi blocker, báo ngay.

### 3. Diễn tập tay trọn luồng demo (1 LẦN DUY NHẤT, ~15 phút)
Đi đúng kịch bản mục C của `DEMO-READINESS` bằng trình duyệt thật:
- [ ] Đăng nhập khách: **GÕ TAY `0974000145` / `Demo@123`** — TUYỆT ĐỐI không
      bấm nút "Đăng nhập nhanh — Khách hàng" (nút đó là USR-0001, sai dữ liệu
      case demo).
- [ ] Chạy D2 (không tìm thấy — nhanh nhất, không tạo rác) và D4 (trọn luồng
      tạo ticket, dùng đúng lời thoại trong `eval/demo_cases_20260814.md`).
- [ ] Đăng nhập CSKH `0353000201` → thấy ticket D4 trong hàng chờ → trình sếp.
- [ ] Đăng nhập sếp `0905000205` → xin OTP duyệt → duyệt → xác nhận trạng thái
      đổi phía khách.
- [ ] Ghi latency từng lượt + mọi điểm "kém mượt" (câu thiếu đồng cảm, chuỗi
      `[PERSON]`, giờ UTC lệch múi — đã biết QA-06, chỉ cần xác nhận có/không
      xuất hiện trong luồng demo để người demo chuẩn bị lời giải thích).

### 4. Kiểm 1 vòng phòng thân
- [ ] Đăng nhập sai mật khẩu 1 lần → thông báo lỗi sạch (không "[object Object]").
- [ ] F5 giữa phiên chat → hội thoại còn nguyên (PostgresSaver).

## ĐỊNH DẠNG BÁO CÁO CUỐI (gửi PO)

```
## Kết luận: GO / NO-GO (+ điều kiện nếu có)
## Hạ tầng: (3 dòng kết quả)
## Smoke tự động: (bảng B1–B6: nhóm · pass/fail · ghi chú)
## Diễn tập tay: (D2, D4, duyệt — đạt/không · latency · điểm kém mượt)
## Phát hiện mới (nếu có): (mức độ · có chặn demo không · KHÔNG tự sửa)
## Lời dặn thêm cho người demo (nếu có)
```
