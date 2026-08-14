# Checklist sẵn sàng DEMO PITCHING — 2026-08-14

> Mục tiêu: demo cho khách hàng xem PHẢI mượt. Mọi việc khác (lộ trình EU/US,
> load test 150, cắt token) LÙI SAU demo — xem `docs/PO-TONG-KET-2026-08-13.md`.
> Nguyên tắc: **tối nay chốt trạng thái code, sáng mai KHÔNG sửa gì ngoài blocker.**

---

## ⚡ CẬP NHẬT SÁNG 14/08 — PO đã kiểm chứng lại bằng repo + container thật

**Mục A tối qua đã xong toàn bộ:**
- R1 ✅ latency: coder tìm ra gốc (scrub PII trên span attribute trước khi cắt
  — commit `b598096`). Đường demo thật đo 3,6–23,2s/lượt. Con số p50 37,7s cũ
  là artifact của eval harness, KHÔNG phải trải nghiệm demo.
- R3 ✅ code sạch: 4 commit (`2d9a709`→`f2d4785`), working tree sạch, không
  stash treo. Đã verify bản vá QA-13 CÓ MẶT trong container đang chạy.
- R4 ✅ realtime: sau vá QA-13 đo 60/60 tin, 0 mất, 0 lặp, 6/6 phiên.
- R6 ✅ 4 case demo chốt trong `eval/demo_cases_20260814.md` (D1–D4, mỗi case
  ≥2 lượt đạt). LangSmith đã tắt trong container (verify `printenv` = false).

**Còn lại sáng nay:** mục B (smoke Playwright + diễn tập tay) + mục C diễn tập
trọn kịch bản + kiểm quota OpenAI.

## ✅ KẾT LUẬN CUỐI (sau smoke sáng 14/08): GO

Diễn tập tay trọn luồng trên stack Docker thật: đăng nhập → D2 (3,3s, 0 bịa)
→ D4 tạo ticket lượt 1 (8,2s) → CSKH thấy ticket → trình sếp → chặn duyệt
thiếu OTP (âm bản đạt) → sếp duyệt (<1s, `approved_by` đúng trong DB) → F5
giữ hội thoại. Không xuất hiện `[PERSON]`, không lộ múi giờ UTC.

**4 điều kiện cho người demo (cách nói/thao tác, không sửa code):**
1. **KHÔNG bật stack dev dưới mọi hình thức** — kể cả chạy Playwright B1/B2/
   B3/B5/B6 (config mặc định tự spawn `npm run dev` = stack thứ hai, ADR-009).
   Trước demo chỉ có stack Docker sống.
2. **Câu hỏi lại phải có chữ "khiếu nại"/"ticket"** (M-01 — bộ lọc phạm vi
   nhạy từ khoá). Câu an toàn đã kiểm: "hồ sơ khiếu nại của mình đang thế nào
   rồi?". TRÁNH hỏi "cho mình xem lại mã ticket vừa rồi" (M-05 — agent không
   đọc lại mã cụ thể).
3. **Hai điều KHÔNG hứa trên màn hình**: ticket đổi sang "đã duyệt" (M-03/
   QA-02 — hitl_status còn kẹt `pending`) và "xem được ai duyệt lúc nào" trên
   UI (M-02 — DB có đủ, API chưa trả). Câu thay thế mạnh hơn và vẫn đúng:
   *"ràng buộc chỉ sếp mới duyệt được nằm ở tầng database — viết SQL tay cũng
   không lách được"*.
4. **Dữ liệu demo đã phình** (M-04): hàng chờ CSKH ~730 ticket, USR-0145 có
   8 khiếu nại → agent sẽ nói "bạn có 8 khiếu nại". QUYẾT ĐỊNH PO: KHÔNG dọn
   DB sáng demo (rủi ro mới > lợi ích). Lời thoại nếu khách hỏi: "hệ thống
   đang mang dữ liệu của các đợt kiểm thử tự động — mỗi ticket này là một lần
   chạy test thật".

Ngân sách còn dư cho pitch: CSKH ~2/60 tin trong giờ, khách ~7 lượt chat.

**✅ HOTFIX CHIỀU 14/08 ĐÃ NGHIỆM THU (commit a7c06f2/fc38ee6, QA/QC xác nhận
trong container):** V1 link Phê duyệt · V3 validation 3 lớp + dọn 6đ + prefill
· V6 rail gate OTP (frontend). V5+V4 bỏ có chủ đích. Hàng chờ duyệt đúng 3
item thật (323k · 178k · 107k). `/approve` hiện đủ danh sách — lần PO thấy
trống là do phiên/cache trình duyệt, đăng nhập lại sếp là thấy.

**Điều kiện thứ 6 (M-10):** sau khi OTP xong, **ĐỪNG F5 màn chat** — rail
giao dịch sẽ ẩn trở lại (cổng chặn theo state client, chưa đọc lại phiên
backend). Lỡ F5 → bấm "Xác thực ngay", ~10 giây. Fix gốc sau demo.

**Ghi chú người demo (từ nghiệm thu):** D4 có 2/5 lần mở đầu thẳng "Mình đã
tạo hồ sơ…" thiếu câu đồng cảm — không sai dữ liệu, không cần phản ứng;
USR-0145 hiện có 9 khiếu nại nên agent sẽ đọc số đó nếu hỏi tình trạng.

**⚠️ BỔ SUNG TRƯA 14/08 (từ triage của QA/QC) — điều kiện thứ 5:**
Trong case D2 (không tìm thấy giao dịch), **TUYỆT ĐỐI KHÔNG yêu cầu agent tạo
hồ sơ "cần tra thủ công"** sau khi tra không ra — đường tạo ticket với
trans_id không tồn tại có crash FK đã biết (CASE-110, IntegrityError — hỏng
cả lượt chat trên màn hình). D2 dừng ở "không tìm thấy + hỏi thu hẹp" như
kịch bản gốc là an toàn. D4 (tạo ticket từ giao dịch TÌM THẤY) không bị ảnh
hưởng — đã kiểm 3/3 + smoke sáng nay. Fix nằm ở nhánh dev, KHÔNG vá main
trước demo.

**BẪY MỚI PHÁT HIỆN — người demo BẮT BUỘC thuộc:**
1. **KHÔNG bấm nút "Đăng nhập nhanh — Khách hàng"** trên màn login: nút đó
   trỏ `0387000001` (USR-0001), còn TOÀN BỘ case demo dựng trên dữ liệu
   **USR-0145 — gõ tay `0974000145` / `Demo@123`**. Bấm nút nhanh là D1–D4
   trật hết dữ liệu.
2. Chỉ 4 tài khoản đăng nhập được (`Demo@123`); mọi user khác mật khẩu ngẫu
   nhiên — không bốc case golden_set của user khác.
3. D1 sẽ hiện chuỗi `[PERSON]` (PII đã che đúng) — chủ động giải thích, đừng
   để khách tự thắc mắc. D3 agent liệt kê 3 giao dịch (có thêm 853k) — đúng
   dữ liệu, nói trước để không bối rối.
4. Live-chat: gõ xong nhìn ô nhập trống rồi mới gõ tiếp (lỗi L4-04 cũ);
   trần 60 tin/giờ/người — diễn tập nhiều có thể chạm trần, đó không phải hỏng.
5. Kiểm health đúng cách: `docker ps` (backend healthy) — KHÔNG dùng
   `curl localhost/health` (Caddy đưa về app, không ra JSON backend).

---

## A. RỦI RO DEMO xếp theo mức nguy hiểm — xử lý TỐI NAY

### R1 — Latency agent: p50 37,7s/lượt sau PII scrub (nguy hiểm nhất)
40 giây im lặng giữa buổi pitch là chết demo. Hai đường xử lý, chọn 1 tối nay:
- [ ] **Coder điều tra nhanh** (nghi phạm số 1: Presidio/NER chạy đồng bộ trên
      đường nóng mỗi tin nhắn — đo bằng trace Jaeger đang có sẵn). Nếu sửa
      được an toàn trong tối nay → sửa, chạy lại smoke test.
- [ ] **Không sửa kịp → xử lý bằng KỊCH BẢN**: chọn case demo NGẮN (1 lượt tra
      cứu, tránh case multi-turn dài), người demo chủ động nói trong lúc chờ
      ("agent đang gọi tool tra cứu thật vào database 60.000 giao dịch —
      không bịa số"), biến điểm yếu thành điểm kể chuyện grounding.

### R2 — Bẫy hai stack (ADR-009, đã từng mất nhiều giờ vì chính nó)
- [ ] Trước demo: TẮT stack dev cục bộ (`next dev :3000` + uvicorn), chỉ chạy
      stack Docker. Chạy `scripts/preflight.sh` xác nhận chỉ 1 stack sống.
- [ ] Nhìn thấy `EnvBadge` trên topbar + màn login đúng môi trường mong đợi.
- [ ] `curl localhost/health` → xem `env` / `db_kind=postgresql` / `db_name`.

### R3 — 6 file sửa dở chưa commit (graph.py, live_chat_ws.py, server-api.ts…)
- [ ] Coder chốt TỐI NAY: hoàn tất + commit, hoặc stash để demo trên HEAD sạch.
      KHÔNG demo trên working tree lửng lơ — container đang chạy có thể lệch
      với code trên đĩa (bài học `feedback_docker_verify_rebuild`: rebuild +
      verify fix có mặt TRONG container trước khi tin).
- [ ] Sau khi chốt: `docker compose build && docker compose up -d` lại, verify
      `/health` xanh.

### R4 — Realtime live-chat vừa đổi kiến trúc (ADR-015 multi-worker + file đang sửa dở)
Đây đúng luồng "tạo ticket phải hiển thị đúng chat realtime" bạn yêu cầu.
Lỗi vỡ fan-out là lỗi IM LẶNG (tin biến mất, không exception) — test tay 1
trình duyệt KHÔNG bắt được vì thường nối cùng 1 worker.
- [ ] Test thật 2 trình duyệt khác nhau (Chrome + Safari/incognito): khách gửi
      tin ↔ CSKH thấy NGAY, và ngược lại. Lặp lại ≥5 tin để đi qua nhiều worker.
- [ ] Chạy `npx playwright test e2e/live-chat.spec.ts` (5 test).

### R5 — OTP hết hạn giữa demo
- [ ] OTP step-up tạo ticket tươi ≤15 phút, OTP duyệt của sếp ≤10 phút: nếu
      demo kéo dài, phải xin OTP lại — người demo cần THUỘC đường xin lại để
      không lúng túng (đây là feature bảo mật, kể được: "PSD2 dynamic linking").
- [ ] Diễn tập trước: cố tình để OTP hết hạn 1 lần, xem thông báo lỗi có sạch không.

### R6 — Chất lượng trả lời (29/40 case đang vi phạm checks trên bộ chấm)
- [ ] KHÔNG demo case ngẫu nhiên. Chọn trước 3–5 case từ `eval/golden_set.jsonl`
      đã pass ổn định, chạy thử tối nay ≥2 lần mỗi case trên đúng stack demo.
- [ ] Case demo nên phủ: 1 tra cứu tìm thấy (happy) · 1 không tìm thấy (chứng
      minh không bịa — điểm mạnh nhất để pitch) · 1 luồng đầy đủ tạo ticket →
      duyệt.

## B. CHECKLIST 6 LUỒNG — chạy sáng mai trước demo (QA/QC)

Chạy tự động trước (nhanh, ~vài phút), rồi diễn tập tay đúng kịch bản demo.

### B1. Đăng nhập & phân quyền
- [ ] `npx playwright test e2e/login.spec.ts e2e/auth.spec.ts e2e/auth-multirole.spec.ts` (13 test)
- [ ] Tay: login khách → vào /chat · login CSKH → dashboard · login supervisor
      → màn duyệt · khách sửa URL sang trang CSKH → bị chặn.

### B2. Chat khách hàng + OTP (đủ tiêu chuẩn test case chat)
- [ ] `npx playwright test e2e/chat.spec.ts` (3 test)
- [ ] Tay theo case đã chọn ở R6: câu mở đầu có đồng cảm ("Mình hiểu…"),
      số liệu khớp DB, không lộ tên thật khách (PII scrub), OTP flow mượt.

### B3. Tạo ticket
- [ ] Chat → agent đề nghị tạo ticket → OTP step-up → ticket xuất hiện ĐÚNG
      trong hàng chờ CSKH (mở dashboard CSKH xác nhận — chính là kịch bản
      BUGREPRO-001 ngày xưa, giờ phải xanh).
- [ ] `npx playwright test e2e/ticket-detail.spec.ts e2e/dashboard.spec.ts` (4 test)

### B4. Realtime live-chat
- [ ] Xem R4 ở trên (2 trình duyệt + `live-chat.spec.ts`).

### B5. UX/UI các luồng
- [ ] `npx playwright test e2e/accessibility.spec.ts` (8 test — axe-core WCAG,
      mobile viewport, bàn phím, mất mạng).
- [ ] Tay: soát nhanh dark/light mode màn hình sẽ chiếu · font/tương phản trên
      máy chiếu thật nếu có · timeline trạng thái ticket (US-007) hiển thị
      đúng bước.

### B6. Phê duyệt supervisor
- [ ] `npx playwright test e2e/approve.spec.ts` (2 test)
- [ ] Tay: CSKH trình đề xuất → sếp thấy đủ căn cứ (trích tool result) → xin
      OTP duyệt → duyệt → trạng thái đổi realtime phía khách · thử cả nút
      TỪ CHỐI và YÊU CẦU BỔ SUNG (need_more_info) — khách hàng xem demo hay
      bấm thử nút phụ.

### B7. Chốt hạ tầng (chạy cuối cùng, ngay trước demo)
- [ ] `pytest tests/test_invariants.py -v` → 19/19 xanh.
- [ ] `python scripts/check_contracts.py` → sạch.
- [ ] `docker ps` → 6 container healthy · Redis/Postgres không restart gần đây.
- [ ] Còn quota OpenAI (tài khoản Personal $20 — kiểm số dư TRƯỚC demo, hết
      tiền giữa demo là lỗi không đỡ được).
- [ ] Mạng nơi demo: nếu demo qua internet, thử trước trên đúng mạng đó.

## C. KỊCH BẢN DEMO GỢI Ý (kể chuyện theo điểm mạnh)

1. **Mở màn**: khách mô tả "chuyển tiền mà bạn chưa nhận được" → agent đồng
   cảm rồi tra cứu THẬT → số liệu có nguồn (kể: mọi con số trace được về tool
   result trong DB — cấm bịa số liệu là ràng buộc cứng).
2. **Không tìm thấy**: cố tình đưa mã sai → agent nói "không tra được", không
   bịa (điểm khác biệt lớn nhất so với chatbot thường).
3. **Tạo ticket + OTP step-up**: kể chuyện 2 mức OTP (12h xem / 15 phút hành động).
4. **CSKH nhận realtime** → investigation trail đầy đủ → trình sếp.
5. **Sếp duyệt với OTP gắn đúng resolution + số tiền** (PSD2 dynamic linking
   — "đổi số tiền là OTP cũ vô hiệu") → khách thấy trạng thái đổi ngay.
6. **Chốt**: AI không có nút chuyển tiền — kể cả bị hack prompt cũng không
   chuyển được tiền, vì quyền chặn ở database, không ở lời dặn.

Diễn tập trọn kịch bản ≥2 lần tối nay hoặc sáng sớm, bấm giờ tổng thời lượng.

## D. PHÂN VIỆC TỐI NAY

| Ai | Việc | Deadline |
|---|---|---|
| Coder | R1 (điều tra latency — timebox 2h, không xong thì dừng) · R3 (chốt 6 file, rebuild container) | tối nay |
| QA/QC | R6 (chọn + chạy thử case demo) · R4 (test 2 trình duyệt) | tối nay |
| QA/QC | Toàn bộ mục B theo thứ tự | sáng mai, xong trước demo ≥1h |
| PO thật | Kiểm quota OpenAI · quyết R1 đi đường nào nếu coder không sửa kịp · diễn tập kịch bản C | tối nay |

**Go/No-Go sáng mai**: B7 xanh + B1–B6 không có blocker + đã diễn tập C trọn
vẹn ít nhất 1 lần trên đúng stack demo → GO.
