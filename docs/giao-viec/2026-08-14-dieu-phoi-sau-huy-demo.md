# ĐIỀU PHỐI SAU KHI HUỶ DEMO — PO, chiều 14/08

> Demo tối 14/08 HUỶ (PO thật báo). Lệnh đóng băng main HẾT HIỆU LỰC.
> Dán file này vào cả 3 tab. Mỗi vai đọc mục chung + mục của mình.

## Chung

1. **DUYỆT bảng nhãn Việt hoá của coder — toàn bộ, không sửa gì:**
   6 trạng thái giao dịch (success→Thành công · processing→Đang xử lý ·
   failed→Thất bại · refunded→Đã hoàn tiền · pending→Chờ xử lý ·
   on_hold→Đang tạm giữ) + 7 nhãn tool (kể cả propose_resolution→Đề xuất
   hướng xử lý · escalate_ticket→Chuyển cấp xử lý). Lý do duyệt nguyên trạng:
   tách pending/processing tránh trùng nhãn là đúng; nhóm trong contract chép
   mo_ta không cần duyệt lại.
2. **Chuyển toàn bộ mũi làm việc sang nhánh `dev/learning-loop`.** Main giữ
   làm mốc ổn định (trạng thái đã nghiệm thu GO). Việc ĐẦU TIÊN của coder:
   trên dev chạy `git merge main` (main đi trước ~26 commit — merge, không
   rebase, giữ nguyên lịch sử đã nghiệm thu), xử lý conflict nếu có
   (docs/STATE.md dễ đụng), báo xong để 2 vai kia checkout theo.
3. Từ giờ mọi commit vào dev. Quy tắc cũ giữ nguyên: kéo rebase đầu phiên,
   ai vùng nấy.
4. DEMO-READINESS-2026-08-14.md giữ nguyên làm tài sản cho buổi demo kế tiếp
   (6 điều kiện + kịch bản vẫn đúng), không ai xoá.

## Coder — thứ tự

1. Merge main → dev (mục 2 ở trên).
2. **Nối lại `2026-08-14-lenh-duyet-phase0.md` mục Coder** (bị demo chen
   ngang): fix nhóm không cần ADR — CASE-110 (crash FK not_found) ·
   CASE-004 + 4 regression · SEC-A (guard reject) · SEC-B (guard approve) —
   giờ sửa thẳng trên dev, có tester viết test song hành.
3. Thực thi Phase 0: áp contract (INV-14) + ghi 4 ADR (016→019) +
   `check_contracts.py --update` + bump CONTRACT_VERSION → báo tester.
4. Phase 1 learning-loop theo brief cũ (migration reject_reason +
   created_by + consume OTP + vá QA-02 + M-02) + dự thảo ADR-020.
5. Việt hoá Đợt 2 khi inventory QA về (nhãn đã duyệt ở mục Chung) — trên dev.

## Tester (QA/QC) — thứ tự

1. Hoàn tất inventory Việt hoá (đang làm dở) → giao coder.
2. Sau khi coder xong bước 2: test hồi quy cho SEC-A/B (reject chỉ từ
   pending_approval, approve không nhận draft — test từ contract HIỆN HÀNH)
   + xác nhận CASE-110 hết crash (chạy lại case not_found tạo ticket).
3. Sau khi coder xong bước 3 (contract mới): nhiệm vụ 2 brief learning-loop
   (test INV-14, CHECK br11, ranh giới thieu_can_cu, authz trường audit).
4. Tiếp tục nhiệm vụ 3 (CANDIDATE-REVIEW) + sửa nhãn 4 case B2 theo phán
   quyết PO ("thông báo + đề nghị, khách quyết") + case eval M-08.

## Security — thứ tự

1. Rà bản contract + ADR coder áp THẬT ở bước 3 (so với dự thảo đã duyệt).
2. Soạn 3 dòng hướng dẫn xoay `LANGCHAIN_API_KEY` cho PO thật làm NGAY
   (không còn lý do chờ demo).
3. Threat model đã giao tester tích hợp — theo dõi CANDIDATE-REVIEW.md có
   phản ánh đúng checklist chống poisoning không, phản hồi trong vùng
   docs/security/.

## BỔ SUNG — phán quyết ca thứ ba của test quét ma trận (supervisor × /dashboard)

**QUYẾT: MỞ guard /dashboard cho supervisor (phương án A)** — coder thêm vào
ROLE_PREFIXES.supervisor + tab "Hàng chờ" trong nav sếp. Test của tester tự
xanh, KHÔNG sửa ánh xạ. Bốn lý do:

1. Contract là nguồn sự thật và đang ghi rõ "supervisor kế thừa toàn bộ quyền
   cskh". Muốn hạn chế sếp là ĐỔI CHÍNH SÁCH → thuộc về đợt ADR-020
   (maker–checker), quyết có đủ ngữ cảnh — không phải quyết ké trong một đợt
   Việt hoá UI.
2. Trạng thái hiện tại là TỆ NHẤT có thể: API mở (GET /tickets trả 200 cho
   sếp — QA đã kiểm) mà trang chặn — không thêm kiểm soát nào, chỉ thêm
   mâu thuẫn.
3. Kiểm soát xung đột lợi ích THẬT nằm ở maker–checker tầng DB
   (`approved_by != created_by`, ADR-020 sắp tới) — chặn một trang ĐỌC không
   thay thế được nó.
4. Câu hỏi mở cuối authority-matrix ("sếp có nên bị cấm tự điều tra?") VẪN
   MỞ — quyết định hôm nay chỉ là "frontend khớp contract hiện hành", không
   phải phán quyết cuối về tách bạch vai. ADR-020 được quyền lật lại, và khi
   đó sửa từ contract xuống, đúng quy trình.

Ghi chú kèm: 2 test đỏ của bộ quét là ĐỎ ĐÚNG cho tới khi coder vá — cấm
"làm xanh" bằng nới test (đồng ý nguyên văn cảnh báo của tester).

## PHÁN QUYẾT đợt nghiệm thu Đợt 2 (PO, tối 14/08)

1. **Nhãn `pending_approval` = "Chờ sếp duyệt" — DUYỆT.** Không phải nhãn tự
   đặt hoàn toàn: contract mô tả trạng thái này mở đầu bằng đúng cụm "Đã gửi,
   chờ sếp duyệt" — nhãn ngắn là mệnh đề đầu của mo_ta. Ghi nguồn vậy trong
   mapping.
2. **"Chatbot AI" (nav · h1 · alert screen-reader) → "Trợ lý AI"** — thống
   nhất với câu minh bạch đã duyệt ("Trợ lý AI — mọi con số đều được tra cứu
   từ hệ thống thật") và giọng thương hiệu "Sen — Trợ lý CSKH". Sửa cả 3 chỗ,
   kể cả alert cho screen-reader (khiếm thị cũng là người dùng).
3. **Ca B2 — phán quyết CŨ GIỮ NGUYÊN, giờ KÍCH HOẠT THI HÀNH** (đã ghi trong
   lệnh duyệt Phase 0, PO thật không phản đối trong thời hạn): hành vi đúng =
   thông báo trạng thái + mốc thời gian từ dữ liệu + ĐỀ NGHỊ tạo hồ sơ, khách
   quyết. Thi hành:
   - Coder: sửa prompt/hành vi agent cho ca giao dịch `processing`. Đây là
     THAY ĐỔI PROMPT → bắt buộc qua cổng đo: chạy paired eval 40 case trên bộ
     chấm đã làm sạch, gate 0% bịa thật, trước khi merge. Không ngoại lệ —
     đây chính là lằn ranh 2 của kế hoạch learning-loop.
   - Tester: sau khi hành vi mới lên, sửa nhãn 4 case B2 + e2e ticket-detail
     assert luồng 2 lượt (đề nghị → khách xác nhận → ticket). KHÔNG nới trần
     150s.
4. **3 giá trị action_type chưa đo được trên UI** (ledger_adjustment ·
   no_action · manual_review): CHẤP NHẬN bằng chứng exhaustive compile-time
   (Record<ActionType, string> — thiếu là không build được) cho đợt này;
   thêm dòng vào checklist nghiệm thu ĐỢT RESEED sắp tới: seed phải sinh ít
   nhất 1 resolution mỗi loại để 3 nhãn này được thấy bằng mắt một lần.
5. **Guard supervisor × /dashboard**: coder vá nốt (phán quyết đã ra trước
   commit fd20b12 hai phút — chỉ là lệch nhịp, không phải bất đồng). Mục
   tiêu: bộ quét 24/24 xanh.
6. **Xoay key LangSmith — NHẮC LẦN 3, việc của PO thật, 5 phút, không phụ
   thuộc gì cả:** vào smith.langchain.com → Settings → API Keys → Revoke key
   cũ → tạo key mới → cập nhật `.env` (`LANGCHAIN_API_KEY=`) →
   `docker compose up -d` lại backend. Tracing đang tắt nên key mới nằm im,
   nhưng key CŨ đã lộ 3 nơi và vẫn còn hiệu lực cho tới khi revoke.

## PHÁN QUYẾT B2 (PO, tối 14/08 — sau báo cáo coder về patch B2)

**Chọn đường (2) rồi (3), đúng đề xuất coder. KHÔNG nhận đánh đổi ở trạng
thái hiện tại.** Lý do: đổi 4 ca tạo-ticket lấy 7 ca phân-loại-sai là đổi lỗi
nhẹ lấy lỗi nặng — phân loại sai vi phạm quy tắc bắt buộc PRD §3 ("chưa xác
định đúng ô thì không đề xuất") và US-009 (phân loại theo dữ liệu tool).
*Đính chính nhỏ cho coder: đây không phải ràng buộc cứng số 5 (số 5 là cờ
gian lận ≠ khoá ví) — nhưng kết luận không đổi: không được nhận.*

Trình tự thi hành:
1. **Coder — đường (2), miễn phí:** đọc reply đầy đủ 7 ca hồi quy
   (065/092/094/085/022/068/047), phân định từng ca: "agent sai thật" vs
   "khách mô phỏng trả lời cụt quá nên agent thiếu dữ kiện". Đầu ra: bảng
   ca × phán định × trích dẫn.
2. **Tester — song song:** chuyển 4 case B2 sang đặc tả 2 lượt theo phán
   quyết đã có (thông báo + đề nghị → khách xác nhận → ticket).
3. **Sau khi CẢ HAI xong:** chạy đúng MỘT lần paired eval 40 case trên bộ đã
   cập nhật (~$0,22) → lúc đó mới quyết áp lại patch hay thiết kế lại.
   Trần chi phí đo cho B2 từ giờ: 1 lần chạy, hết.
4. **Ghi sổ bài học harness** (backlog tester, không làm ngay): trường
   `reply` trong raw chỉ là lượt cuối — mọi chỉ số đơn-lượt trên harness đa
   lượt đều dễ đo sai. Cân nhắc xuất transcript đủ lượt trong raw để lần sau
   không ai vấp lại (coder vấp hôm nay, người khác sẽ vấp ngày mai).

Chi phí $1,10 cho 5 lần chạy: CHẤP NHẬN, không truy — cổng đo vừa chặn một
đánh đổi tồi trước khi nó được ship, rẻ hơn mọi phương án khác.

## PHÁN QUYẾT sau việc (2) của B2 + khởi động Phase 0 (PO, tối 14/08)

1. **Uỷ quyền MỘT LẦN ghi `docs/DECISIONS.md`:** coder ĐƯỢC ghi ADR-016→019
   trong đợt Phase 0 này (file thuộc vùng PO — hỏi trước khi ghi là đúng kỷ
   luật, ghi nhận). Điều kiện kèm: (i) 018/019 đúng nguyên văn bản đã duyệt
   + sửa INV-14; (ii) 016/017 theo đủ mẫu ADR, bắt buộc có "Lý do BÁC BỎ";
   (iii) CHỈ GHI THÊM; (iv) hai lớp review sau commit: security rà (đã giao)
   + PO đọc diff. Sai sót nếu có sửa bằng ADR mới, không sửa ADR đã ghi.
2. **B2 — xác nhận phán định 7/7 agent-sai-thật + KHÔNG áp patch.** Bằng
   chứng "không giao dịch nào processing ⇒ luật chưa từng chạy mà vẫn hỏng ⇒
   tác hại từ SỰ HIỆN DIỆN của bullet trong mục Giọng văn" là loại bằng chứng
   quyết định. Chốt luôn nguyên tắc thiết kế prompt cho lần làm lại (và cho
   mọi luật hành vi sau này): **luật gắn với dữ liệu tra cứu đặt trong "Quy
   trình điều tra", mục Giọng văn chỉ chứa giọng văn.** Đưa nguyên tắc này
   vào ADR khi làm lại B2.
3. **CASE-110 — đồng ý không vá:** lớp chặn đã tồn tại (create_ticket.py:50
   ToolError), lỗi không tái hiện trên HEAD, viết thêm code là mã chết.
   QA chạy lại trên HEAD xác nhận đóng + cập nhật trạng thái trong
   `trige_29_case_20260814.md`.
4. **Gộp cổng đo — DUYỆT:** trần "1 lần chạy" áp cho CẢ GÓI (B2 làm lại +
   CASE-004 + CASE-083 + CASE-101), chạy sau khi tester xong bộ case 2 lượt.
   Đây đúng tinh thần trần cũ, không phải nới.

## REVIEW LỚP 2 CỦA PO CHO PHASE 0 (8fe3bed) — ĐẠT · LỆNH PHASE 1: GO

Đã kiểm độc lập bằng diff + chạy lại gate, không duyệt chay:
- Append-only đúng (148 thêm / 0 xoá) · 4 ADR đủ mục "Lý do BÁC BỎ"
  (016: 1 · 017: 2 · 018: 1 · 019: 4) · ADR-019 khớp nguyên văn bản duyệt.
- Contract v2.1.0 đủ: taxonomy 7 giá trị + `la_tin_hieu_hoc` · ranh giới
  thieu_can_cu trong enum · `dan_xuat` (đặc tả vá QA-02) · INV-14 kèm ghi
  chú lý do đánh số ("INV-13 đã thuộc agent-tools.yaml") ngay trong `nguon`.
- Gate chạy lại bằng tay PO: 19/19 bất biến · check_contracts sạch.
- Còn treo đúng 1 lớp: security rà bản áp thật (đặc biệt TM-03) — không chặn
  Phase 1 code, chỉ chặn phần GHI CHÚ TỰ DO (đã carve-out sẵn trong lệnh).

**PHASE 1: GO** theo đúng phạm vi coder liệt kê: migration 3 cột + CHECK br11
+ backfill 1 dòng → `khac` · route reject nhận reason bắt buộc · vá QA-02
theo `dan_xuat` (cùng transaction) · API ticket trả trường audit cho staff
(M-02) · dropdown lý do + gợi ý need_more_info. Ghi chú tự do LÀM SAU CÙNG,
chờ security sign-off. Tester nhiệm vụ 2 chạy song song từ contract v2.1.0.

Sổ nợ PO thật: key LangSmith ĐÃ XOAY (gạch nợ — coder xác nhận PO làm trong
phiên coder) · CÒN LẠI: export + upload project-knowledge — LÀM NGAY BÂY GIỜ
là đúng thời điểm (contract v2.1.0 vừa chốt).

## REVIEW LỚP 2 PHASE 1 (02d2b2a) — LÕI ĐẠT · CHƯA ĐÓNG, THIẾU 3 MỤC LỆNH GỘP

**Đã kiểm và ĐẠT (bằng chứng thật):** thứ tự migration cột→backfill→CHECK
đúng + backfill ghi nguồn gốc vào rationale (dữ liệu kiểm toán không mập mờ —
đúng) · br11 kiểm HIỆU LỰC bằng IntegrityError thật · QA-02 đóng (hitl_status
chuyển cả 2 nhánh) · M-02 an toàn (khách 403) · lỗi draft→reject tester bắt
đã sửa — PO chạy lại test_resolution_reject.py trên HEAD: 9/9 xanh · hai lớp
schema-Literal + CHECK đúng lập luận ADR-019.

**3 mục lệnh gộp (khối "BỔ SUNG chiều 14/08" của lệnh duyệt Phase 0) CHƯA
làm — coder bổ sung 1 commit trước khi Phase 1 được coi là đóng:**
1. **SEC-B**: guard approve VẪN nhận `draft` (PO grep HEAD:
   `status not in ("draft", "pending_approval")`) — trái transition contract
   (approved chỉ từ pending_approval) và tinh thần INV-05. Sửa như đã sửa reject.
2. **Consume OTP sau duyệt thành công**: chưa có (grep không thấy
   delete/consume trong approve_resolution).
3. **`resolutions.created_by`**: CHƯA vào — Resolution class 0 match, dòng
   352 vẫn là của Escalation. Cần migration nhỏ; điểm thiết kế coder tự đề
   xuất: cột nullable cho dữ liệu cũ (backfill trung thực = không bịa người
   đề xuất), route propose LUÔN ghi từ giờ; CHECK maker–checker để ADR-020.

**Tester — 1 khoảng trống đối xứng:** bộ SEC 9 test có draft→reject nhưng
KHÔNG có draft→approve (nếu có thì nó đã đỏ trên HEAD). Thêm case đó — chính
nó sẽ nghiệm thu mục 1 ở trên. Đồng thời chạy lại để đóng chính thức
draft→reject + CASE-110 trong biên bản triage.

**Ghi nhận:** vòng tester-bắt-lỗi-coder lần này là bằng chứng sống cơ chế
"tester không đọc src/" hoạt động đúng thiết kế. Phần test HIỆU LỰC constraint
(ghi thẳng DB đòi IntegrityError, kiểm cả mặt ngược) lấp đúng khoảng trống
INV chỉ đọc AST — chuẩn thuật ngữ audit: presence vs operating effectiveness.

**Mở đường gói đo B2:** bộ case 2 lượt + check `de_nghi_truoc_khi_tao_ticket`
đã sẵn (aa5d593 + d72017a) → coder làm lại patch B2 (luật đặt trong "Quy
trình điều tra" theo nguyên tắc đã chốt) + sửa CASE-004/083, rồi chạy ĐÚNG
MỘT lần paired eval cả gói theo trần đã duyệt.

## PHÁN QUYẾT sau báo cáo QA 87b9a32 (PO — kèm nhận đính chính)

1. **PO nhận đính chính:** review trước ghi "bộ SEC thiếu draft→approve" —
   SAI. Test đã có từ aa5d593 nhưng xanh vì lý do sai (OTP rác → chết ở cổng
   OTP, chưa từng chạm guard trạng thái). Bài học "muốn canh tầng N thì
   request phải sống qua tầng N-1" ghi vào docstring là đúng chỗ — nó là quy
   tắc chung cho MỌI test authz nhiều tầng của dự án từ giờ.
2. **SEC-B đã có bằng chứng sống** (200 khi approve từ draft với OTP hợp lệ,
   body approved_by=USR-SUP). Test đỏ này là ĐỎ ĐÚNG — nó chính là nghiệm
   thu cho commit bổ sung Phase 1 của coder (SEC-B + consume OTP +
   created_by). Coder ưu tiên commit này TRƯỚC mọi việc khác.
3. **Vá harness `must_create_manual_ticket` — DUYỆT, áp TRƯỚC lượt đo:**
   quyết định giữ-thước-cố-định-trước-cả-hai-nhánh là đúng nguyên tắc, áp
   ngay bản vá vài dòng. Quy tắc xử lý hệ quả: nếu CASE-109/110 chuyển ĐỎ
   trên baseline (agent không tạo hồ sơ tra thủ công — gap US-008 thật) thì
   GHI NHẬN là known-red, KHÔNG nhét thêm vào gói prompt B2+004+083 —
   gói đo đã chốt phạm vi, gate là "không tệ hơn baseline trên CÙNG thước
   mới", đỏ có sẵn ở cả hai nhánh không chặn gate. Gap US-008 xếp hàng đợi
   riêng sau gói này.
4. **CASE-110 đóng CÓ ĐIỀU KIỆN** như QA nêu — điều kiện chính là mục 3.

## PHASE 1 ĐÓNG (5493080 — PO review lớp 2 ĐẠT, kiểm code + chạy lại test)

- Verify thật: guard approve `!= pending_approval` ✓ · consume OTP
  (`otp_status='consumed'` + xoá `otp_code`, dòng 62-63) ✓ · `created_by`
  trong Resolution (models.py:338, nullable + comment tại chỗ) ✓ ·
  test SEC của QA 9/9 xanh — đỏ thành xanh BẰNG FIX, không bằng sửa test ✓.
- **DUYỆT "nullable vĩnh viễn, không backfill"** — đúng lệnh gốc, lý do ghi
  đúng: bịa tên vào sổ kiểm toán tệ hơn để trống.
- **GHIM cho ADR-020 (quan trọng):** CHECK maker–checker phải viết
  `created_by IS NULL OR approved_by != created_by` — thiếu vế NULL là vỡ
  trên dữ liệu cũ. Coder đã tự phát hiện, ghi vào đây để không rơi.
- **Mục "Chatbot AI" 3 chỗ:** coder grep toàn frontend không có alert/aria
  nào mang chuỗi đó — 3 chỗ thật là nav · h1 · eyebrow, đã sửa cả 3
  (2a72245). QA: hoặc đưa selector cụ thể của "vùng alert" đã thấy, hoặc
  đóng mục này — mô tả gốc nhiều khả năng là aria-live render lại text đã sửa.
- Ghi nhận: coder tự đính chính phép thử OTP đầu (chết ở guard N-1) — bài
  học "sống qua tầng N-1" của QA đã lan sang vai khác trong cùng ngày.
  Đúng nghĩa tổ chức học.

**Nhịp còn lại:** QA áp vá harness `must_create_manual_ticket` (ĐÃ duyệt từ
f23552a — áp ngay, đừng chờ thêm) → coder chạy gói đo B2+004+083 (một lần)
→ security nộp rà Phase 0+1 + sign-off TM-03 → coder làm field note (gộp
migration cùng nhịp nếu kịp) → ADR-020.

## PHÁN QUYẾT trần đo sau vá harness (PO)

**DUYỆT cách hiểu của coder.** Vá harness d72017a đổi chính cái thước ⇒
baseline cũ hết ghép cặp được ⇒ mốc nền mới trên thước mới là BẮT BUỘC về
phương pháp, không phải tiêu thêm lượt. Trần diễn đạt lại cho hết mơ hồ:
**một CẶP đo trên thước mới** (mốc nền prompt nguyên bản + mốc sau khi sửa)
— cấm vòng lặp sửa-đo-sửa-đo ở giữa. Nếu mốc nền cho thấy 5/6 ca tự xanh
nhờ khách ảo biết trả lời ý định mở hồ sơ → chỉ sửa phần còn hỏng thật
(nhiều khả năng mỗi CASE-004 — vẫn phải sửa, tự chọn candidate là chạm ràng
buộc cứng 3), rồi chạy mốc sau. Tổng ≤ 2 lượt (~$0,44).

Chuẩn ứng xử ghi lại cho các lần sau: trần/lệnh nào thấy mơ hồ thì NÊU RA
TRƯỚC KHI TIÊU TIỀN — coder lần này nêu ngay trong lúc chạy kèm lập luận
đầy đủ, chấp nhận được; nêu trước khi bấm nút thì hoàn hảo.

Ghi nhận QA lần nữa: từ chối sửa nhãn theo hướng nới lỏng và sửa CÔNG CỤ ĐO
thay vì sửa bài thi — đúng tinh thần "thước cố định, thước trung thực".

## GHI NHẬN sau vá harness 394feef (PO)

- **CASE-109/110 đỏ trên thước mới = quy tắc known-red KÍCH HOẠT ĐÚNG NHƯ
  ĐÃ ĐẶT TRƯỚC** (phán quyết f23552a mục 3): không phải hồi quy — thước hết
  mù, đo được gap US-008 thật (not-found phải mở hồ sơ tra thủ công, không
  chào tạm biệt). KHÔNG ai đi tìm commit gây lỗi. KHÔNG nhét vào gói B2 —
  gate vẫn hợp lệ vì đỏ ở cả hai nhánh. **Gap US-008 vào hàng đợi prompt
  KẾ TIẾP sau gói B2**, có thể tái dùng đúng pattern "đề nghị → khách xác
  nhận" + check `tao_ho_so_tra_thu_cong` làm bài nghiệm thu sẵn.
- **Mục "alert screen-reader" ĐÓNG — cả hai bên đều đúng:** chuỗi thứ ba là
  `__next-route-announcer__` của Next.js (ngoài frontend/src, dẫn xuất từ
  h1) — grep coder đúng, quan sát QA thật, sửa h1 tự khỏi (DOM build 22:18
  đọc "Trợ lý AI"). **Chuẩn mới cho báo cáo accessibility: phát hiện từ AX
  tree luôn kèm selector** — QA tự đề xuất, PO chuẩn hoá thành luật.
- Check mới đọc tool_calls TÍCH LUỸ thay vì chỉ lượt cuối — tránh đúng bẫy
  từng làm cite_ fail oan. Thiết kế thước có trí nhớ. Ghi nhận.

## PHÁN QUYẾT sau báo cáo security 5080165 + thiết lập kênh liên tab (PO, đêm 14/08)

**Kênh liên tab hoạt động:** coder · QA · security đều đã xưng vai, báo cáo
qua SendMessage. Vụ "SEC-B chưa vá" của QA = tin soạn trước 5493080 — PO
chạy lại test trên HEAD: 3/3 xanh. ĐÓNG.

**Luật đo mới (từ đề nghị của QA, PO chuẩn hoá):** MỌI báo cáo đo phải ghi
COMMIT CỦA THƯỚC (harness/bộ case) tại thời điểm chạy. Mốc nền hợp lệ phải
chạy trên HEAD ≥ {d72017a, aa5d593, 394feef}. Coder xác nhận đang chạy trên
tree đúng, prompt nguyên bản, git status sạch — hợp lệ.

**TM-03 SIGN-OFF ĐẠT → coder MỞ KHOÁ field `note`**, kèm 3 điều kiện security:
scrub tại điểm GHI · fail-closed khi scrub lỗi · không mở rộng phạm vi đọc.
13 test đối kháng đã đặc tả sẵn trong docs/security/review-phase01-ap-that.md
— tester viết.

**F-11 (backfill bịa danh tính — PO QUYẾT):**
- XOÁ 2 dòng residue QA (RES-663769e6d9dc, RES-b9b1f9344dc6) — dữ liệu thử
  nghiệm, xoá kèm FK là trung thực hơn giữ.
- Dòng genuine còn lại: trỏ `rejected_by` về SENTINEL gắn nhãn rõ ("không
  xác định — backfill ADR-019"), TUYỆT ĐỐI không gán ID người thật; cơ chế
  cụ thể coder đề xuất (user hệ thống không đăng nhập được, không lọt danh
  sách supervisor), security rà lại.
- KHÔNG nới CHECK br11 để cho NULL — constraint giữ nguyên.
- Đính chính tài liệu "1 dòng vs 3 dòng": chấp nhận — 2 dòng dôi là residue
  QA sinh SAU khi dự thảo viết; phiếu duyệt PO kế thừa số cũ, không ai bịa.

**F-12 (route /approve không rate-limit + không đếm OTP sai — High):** DUYỆT
vá theo khuôn main.py:424-438. LỊCH: ngay SAU khi cặp đo B2 xong (sửa
main.py giữa lúc đo không ảnh hưởng container đang chạy, nhưng KHÔNG rebuild
container cho tới khi mốc sau đo xong — tránh đổi hệ giữa hai nhánh đo).
Deadline cứng: trước mốc người dùng thật.

**F-13** (backfill hitl_status 8 ticket cũ — số lịch sử đang bẩn) + **F-14**
(TTL `_session_staff` — nợ ADR-018 tự khai, chạm PDPA): vào cùng nhịp
migration với field note. **F-15**: CHECK br11 một chiều là chấp nhận được
NHƯNG exporter Phase 2 BẮT BUỘC lọc theo `status='rejected'`, không lọc theo
nhãn — ghi thành điều kiện thiết kế exporter, tester thêm test canh.

**Tester — 2 việc từ báo cáo security:** (1) dựng `eval/CANDIDATE-REVIEW.md`
— security tuyên bố sẽ chấm KHÔNG ĐẠT ở lần rà Phase 2 nếu thiếu luật CẤM
NGUYÊN VĂN hoặc trần ứng viên/người dùng; (2) viết 13 test đối kháng field
note theo đặc tả trong báo cáo security.

## MỐC NỀN THƯỚC MỚI + GATE CHO MỐC SAU (PO, đêm 14/08)

- Mốc nền (thước 394feef · HEAD 1909c5a · prompt nguyên bản): 30/40 case lỗi
  · 55 check · 0/40 bịa · p50 13,91s · $0,2171. Giả thuyết "5/6 tự xanh" của
  coder SAI và coder tự đính chính — thước mới CHẶT HƠN (thêm check
  `de_nghi_truoc_khi_tao_ticket`), 25→30 là thước hết mù, không phải hồi quy.
- DUYỆT kế hoạch 3 luật riêng cho 3 nguyên nhân (B2-processing · siết
  multiple_matches CASE-004 · dấu hiệu refund CASE-083), tất cả trong
  "Quy trình điều tra", kiểm cấu trúc bằng máy trước khi đo.
- **GATE MỐC SAU (đặt trước khi đo, không đổi sau):** (1) bịa thật = 0/40 ·
  (2) 6 ca trong gói: cải thiện ≥ B2 4 ca + CASE-004; (3) KHÔNG ca nào ngoài
  gói xấu đi so với mốc nền trên cùng thước (109/110 giữ nguyên đỏ = đúng
  kỳ vọng). KHÔNG có lần đo thứ ba — kết quả lẫn lộn thì PO quyết ship/hold
  trên đúng cặp số liệu này.
- CHỈNH LỆNH F-12 theo phát hiện kỹ thuật của coder (eval chạy in-process
  trên host): điều bất biến giữa hai nhánh đo là **src/ trên host** (trừ
  prompt.py), không phải image container. F-12 code SAU mốc sau.

## LỆNH RÀNG BUỘC cho nhịp migration (từ pre-review security 23f57ef — PO phê chuẩn)

1. **Thứ tự BẮT BUỘC trong CÙNG một transaction:** xoá 2 residue QA →
   sentinel cho dòng genuine → backfill hitl_status (F-13). KHÔNG giao hoán:
   TCK-518527ab869f có đúng 2 resolution là 2 dòng sắp xoá — backfill trước
   là ticket khẳng định phán quyết HITL không còn bản ghi chống đỡ, trái
   `dan_xuat.quy_tac` contract v2.1.0.
2. Backfill bám "resolution MỚI NHẤT" tất định:
   `ORDER BY created_at DESC, resolution_id DESC LIMIT 1` — ticket nhiều
   resolution ĐÃ tồn tại (TCK-173cee0218a0), UPDATE...FROM join không xác
   định sẽ hỏng im lặng về sau.
3. **Trạng thái đích assert được** (coder dán truy vấn thật vào commit,
   tester viết test canh): 6 approved / 3 pending_approval / 1 rejected ·
   đúng 6 ticket đổi trạng thái (5 approved + TCK-0e7f530fbd4f rejected) ·
   TCK-518527ab869f còn 0 resolution và GIỮ pending · 3 ticket chỉ có
   pending_approval giữ pending.
4. **Sentinel — 5 điều kiện nghiệm thu** (security sẽ rà): không đăng nhập
   được (chứng minh bằng POST /auth/login thật → 401) · full_name là nhãn
   không phải tên người · KHÔNG khớp `WHERE role='supervisor' ORDER BY
   user_id LIMIT 1` (chính câu sinh ra F-11 — sentinel mang role supervisor
   là lần backfill sau lại vớ đúng nó) · không vào thống kê theo người ·
   rationale khai CẢ người LẪN thời điểm là suy ra.
5. FK đã kiểm hộ: auth_sessions là bảng duy nhất trỏ resolutions, 0 dòng
   trỏ 2 residue → xoá sạch không cần dọn FK.

## LUẬT CHUNG MỚI (đề xuất coder, PO phê chuẩn): SỬA PROMPT = KIỂM CẤU TRÚC TRƯỚC HÀNH VI

Mọi lần sửa prompt: kiểm cấu trúc bằng máy (đánh số liên tục, không trùng
bước, bullet đúng mục) TRƯỚC khi đo hành vi — ngang hàng với cổng đo. Lý do
bằng sự cố thật: lần này máy bắt được HAI bước cùng số "4" (prompt build
được, ruff sạch, không gì báo) — đúng lớp lỗi câm từng tốn 3 lượt đo +
1 giả thuyết gốc rễ sai. Cặp luật prompt hiện hành: (1) luật hành vi gắn
dữ liệu nằm trong "Quy trình điều tra", Giọng văn chỉ chứa giọng văn;
(2) kiểm cấu trúc trước, kiểm hành vi sau.

## GHI NHẬN gói QA 9278fc3 + 1dbc970 (PO)

- SEC-B ĐÓNG chính thức (QA chạy lại 9/9 trên HEAD).
- CANDIDATE-REVIEW.md đạt cả 2 điều kiện security (CẤM NGUYÊN VĂN + trần
  fail-closed 1/người/ngày · 3/vòng đời · 20/ngày toàn cục) + đặc tả lọc
  exporter đúng F-15. Khai trung thực: ngưỡng chưa thi hành bằng máy — khi
  exporter có mã phải kiểm bằng test đối kháng.
- 13 test note: 14 đỏ chủ ý chờ field. **QA tự bắt 6 test xanh-rỗng của
  chính mình và siết helper ĐÒI cột tồn tại + có nội dung** — nghĩa là route
  nhận note mà không lưu, hoặc scrub xoá sạch, test ĐỎ chứ không gật. Bài
  "hiện diện vs hiệu lực" giờ đã thành phản xạ ở cả 3 vai trong cùng một ngày.
- Test trạng thái đích migration: 7 test trên DB THẬT (5 đỏ · 2 xanh = đúng
  trạng thái trước migration, nền đo được). Hoà giải số "7 lệch vs 6 đổi":
  ticket TCK-518527ab869f rời khỏi mẫu số khi 2 resolution bị xoá — đặc tả
  nhất quán. Có test riêng bắt ca chạy SAI THỨ TỰ. ⚠️ pytest mặc định skip
  cả 7 (SQLite) — lệnh chạy đúng trong docstring, đừng đọc nhầm "7 skipped".
- QA làm tiếp: test F-12 (ưu tiên — thành bài nghiệm thu sẵn cho fix của
  coder) + test bất biến F-13 tầng logic. DUYỆT thứ tự này.

## LUẬT VIẾT TEST MỚI (đề xuất QA sau 3 lần xanh giả cùng ngày — PO phê chuẩn)

**"Assertion trùng với trạng thái MẶC ĐỊNH của hệ thống thì nó không kiểm gì
cả."** Ba biến thể đã gặp thật trong ngày 14/08: (a) `>= 400` khi request
chết sớm ở tầng trước (SEC-B bản đầu) · (b) `X not in Y` khi Y rỗng vì field
chưa tồn tại (nhóm A test note) · (c) `== 403` khi 403 cũng là mã của đường
thất bại thông thường (F-12 bản đầu). **Cách chữa chung: assert vào dữ kiện
CHỈ đúng khi hành vi cần đo thật sự xảy ra** (vd `locked_at` chuyển NULL →
có giá trị). Áp cho MỌI vai viết test, ngang hàng luật "sống qua tầng N-1".

## GHI NHẬN F-12/F-13 (1bc4f4b)

- F-12: 5 test (4 đỏ chờ fix — đúng), test then chốt:
  `test_f12_da_khoa_thi_ma_dung_cung_khong_duyet_duoc` — cơ chế khoá mà mã
  đúng vẫn qua thì failed_attempts/locked_at chỉ là trang trí.
- F-13: 5/5 xanh — phân vai đúng: file này canh LUẬT từ nay về sau, test
  trạng thái đích canh DỮ LIỆU LỊCH SỬ; thiếu một trong hai thì hoặc số sạch
  đúng một lần rồi trôi, hoặc backfill không ai kiểm.
- Toàn bộ việc security giao tester đợt rà này: XONG (13 note · F-12 · F-13
  · CANDIDATE-REVIEW · trạng thái đích).

## PHÁN QUYẾT GATE GÓI B2 (PO — cặp đo 161529/163222, thước 394feef)

**Kết quả cặp:** (a) bịa 0/40 cả hai ĐẠT · (b) B2 4/4 cải thiện + CASE-083
sạch, CASE-004 XẤU ĐI 1→3 · (c) HỎNG — 7 ca ngoài gói xấu đi, chữ ký đồng
nhất complaint_type/scope, TRÙNG chữ ký patch hỏng hôm trước dù luật lần này
nằm đúng mục ⇒ "đặt sai mục" có thể chưa từng là nguyên nhân thật. Tổng
30→24 đẹp lên nhưng thành phần đổi — đúng cái bẫy gate (c) sinh ra để chặn.

**QUYẾT: phương án 3 SỬA ĐỔI — cấp đúng MỘT lượt đo (không phải cặp):**
nhánh "CHỈ luật bước 4 + bước 1" (gỡ luật bước 3 multiple_matches), so ghép
cặp với NỀN HIỆN CÓ (161529 — tái dùng hợp lệ: cùng thước, cùng prompt gốc).
Gate lượt này, đặt trước: (a) bịa 0/40 · (b) B2 4 ca + 083 giữ mức cải thiện
· (c) KHÔNG ca nào ngoài xấu đi so nền. Đây là lượt CUỐI của gói:
- ĐẠT → SHIP luật 4+1; luật bước 3 về xưởng kèm hồ sơ: CASE-004 + câu hỏi
  cơ chế (vì sao siết multiple_matches làm 7 ca lệch phân loại?).
- (c) VẪN HỎNG → HOLD toàn bộ; nghi phạm không còn là nội dung luật mà là
  BẢN THÂN VIỆC THÊM luật (độ dài/pha loãng chú ý?) — điều tra tiếp bằng
  ĐỌC transcript 7 ca, không đo thêm.
**BÁC phương án 2** (ship 4+1 không đo) — đúng lý do coder tự nêu.
Ghi nhận: coder thử giả thuyết cơ chế, dữ liệu bác bỏ, và DỪNG không khẳng
định — sau hai lần sai hôm nay, đây là phản xạ đúng.

## GHI NHẬN D1+D2 (7be5dfb) + NÂNG CẤP LUẬT DẤU THƯỚC (PO)

- **D2**: `--so-sanh TRUOC SAU` in bảng xấu-đi/tốt-lên/đổi-bản-chất, THOÁT MÃ 1
  khi có ca xấu đi — cổng máy, không phụ thuộc ai đọc bảng. Đo thử thật:
  14 xấu / 18 tốt / 4 đổi-bản-chất (nhóm mà đếm-số bỏ sót).
- **D1**: raw lưu đủ all_agent_replies · all_customer_texts · tool_calls ·
  luot_tao_ticket; case lỗi giữa chừng giữ phần đã nói. Làm TRƯỚC khi biết
  kết quả gate — đúng: transcript không quay lại lấy được.
- **NÂNG CẤP LUẬT DẤU THƯỚC (thay bản "ghi commit của thước"):** dấu thước =
  BĂM NỘI DUNG phần chấm điểm (_harness.py + golden_set.jsonl), commit chỉ
  ghi kèm để tra cứu. Lý do: đóng dấu bằng HEAD thì một commit chỉ-thêm-công-
  cụ cũng hô "hai thước khác nhau" giữa cặp đo — báo động giả dạy cả đội bỏ
  qua cảnh báo. QA tự bắt trước khi nó xảy ra. Cặp đo B2 đang chạy KHÔNG
  bị ảnh hưởng.
- C13: archive dựng xong kèm luật "file đang được trích dẫn thì không chuyển"
  — chờ coder cấp TÊN 3 lượt bỏ đi (không đoán — chuyển nhầm lượt thật là
  mất mốc). Phát hiện kèm: 1 file .json thực chất là Markdown (bug C6 cũ)
  đã đổi tên; --so-sanh báo lỗi đọc được.

## THREAT MODEL RESEED (4b8cb32) — PO ĐÍNH CHÍNH MỘT PHÁN QUYẾT + 3 LỆNH MỚI

**PO tự đính chính:** câu "dữ liệu chat cũ xử lý theo đợt reseed" (trong trình
ST2-P0-3) SAI với hiện trạng — TM-R1 đo thật: `seed_db.py` chỉ dọn 8 bảng
nền, KHÔNG chạm messages(459) · chat_sessions(149) · tool_results(499) ·
investigation_logs(33) · resolutions(12) · và **checkpoints+checkpoint_blobs
(1.039+1.496 dòng transcript LangGraph NGUYÊN VĂN chưa scrub — kho PII lớn
nhất hệ thống, vô hình vì nằm ngoài models.py)**. Nếu cứ tin "reseed là
sạch" thì việc dọn im lặng không xảy ra mà STATE lại ghi đã đóng — đúng
hình dạng F-11. Cảm ơn security bắt trước khi nó thành sự thật.

**Ba lệnh mới từ phán quyết này:**
1. **Brief reseed (khi tới lượt coder) BẮT BUỘC nhúng:** danh sách kho dọn
   TƯỜNG MINH (gồm checkpoints/checkpoint_blobs) chốt TRƯỚC khi sửa ·
   thứ tự xoá theo FK (TM-R2 đo thật: hiện reseed GÃY ở
   chat_sessions_ticket_id_fkey — cấm hai đường sửa nhanh "tắt FK" và "xoá
   vừa đủ hết lỗi") · sentinel F-11 sinh lại trong gen_dataset (TM-R6) ·
   7 điều kiện nghiệm thu của security đưa nguyên văn vào brief.
2. **SỬA C8 theo TM-R3:** thêm USR-PA01 vào TEST_ACCOUNT_USER_IDS để tiện
   test là OK, NHƯNG trước đợt 150 người thật thì tập mật khẩu chung KHÔNG
   được chứa supervisor/partner_admin (partner_admin = vai duy nhất nạp nội
   dung kho RAG mà agent tin — cửa indirect injection). Ràng buộc này là
   TEST CANH (tester viết), không phải lời dặn.
3. **TM-R7**: chốt luật cho eval/results trong git TRƯỚC khi có người thật
   (transcript người thật không được commit) — gộp vào cùng quyết định
   ST2-P0-3 của PO thật.

TM-R5 (seed quá "ngoan" làm test scrub xanh giả) → yêu cầu gen_dataset đợt
reseed sinh thêm mẫu PII "bẩn" (SĐT viết liền/cách, tên ngoài tập cố định)
— tester thêm case scrub đối kháng trên dữ liệu đó. TM-R8 ghi nhận: làm sạch
RAG tại TRUY VẤN là chủ đích, cấm "tối ưu" thành chỉ-lọc-lúc-nạp.

## C2/C3 — CI CHƯA TỪNG CHẠY TRÊN NHÁNH LÀM VIỆC (1d87f38 — PO phán quyết)

**Sự thật đo được:** workflow chỉ trigger push main/develop + PR đích main —
nhánh dev/learning-loop không khớp cả hai ⇒ toàn bộ Phase 0+1 hôm nay có
ZERO lượt CI độc lập. PO bổ sung nguyên nhân chồng: local đang ahead remote
~42+ commit từ đầu ngày — kể cả trigger đúng cũng chưa ai push. Hai lỗi độc
lập, cùng hậu quả.

**Phán quyết:**
1. DUYỆT đề nghị QA — sửa trigger LÊN ĐẦU hàng đợi coder, được làm NGAY
   không chờ lượt đo (sửa .github/ không chạm src/, không phạm bất biến đo):
   thêm `dev/**` vào push.branches, bỏ giới hạn đích pull_request.
2. Sau khi sửa trigger: PUSH dev/learning-loop + main lên remote để CI chạy
   thật lần đầu — coder thực hiện, báo kết quả lượt CI đầu tiên (kỳ vọng:
   có thể đỏ những chỗ máy cá nhân chưa thấy — đó là MỤC ĐÍCH, không phải
   sự cố).
3. Chuẩn hoá 2 tiêu chí của QA thành luật: **SKIP ≠ ĐẠT** (job phải đỏ khi
   không dựng được môi trường nó cần, không im lặng skip) · **test canh
   trạng thái dữ liệu môi trường cụ thể tách khỏi test canh logic** (hoặc
   tự nhận nhầm môi trường mà skip có thông báo — không bao giờ đỏ oan).
4. Ghi nhận QA tự bắt lỗi C3 của chính mình TRƯỚC khi nó làm coder nhận một
   CI đỏ không liên quan — "cách nhanh nhất để một job bị coi là hay-đỏ-vớ-
   vẩn rồi bị bỏ qua" là chẩn đoán đúng về cách CI chết trong thực tế.

## LƯỢT ĐO CUỐI GÓI B2 (164859) + PHÁN QUYẾT ĐO NHIỄU NỀN (PO)

**Kết quả:** (a) bịa 0/40 ĐẠT · (b) ĐẠT MẠNH — cả 5 ca sạch hoàn toàn ·
(c) HỎNG 5 ca (101, 020, 067, 094, 085) · tổng 30→23 case lỗi, 55→43 check
— tốt nhất mọi lượt hôm nay. Coder tuân thủ HOLD, không commit. ĐÚNG LUẬT.

**Dữ kiện nghi phương pháp (coder nêu, PO công nhận):** tập "xấu đi" đổi gần
hết giữa hai lượt patch (7 ca vs 5 ca, chỉ 3 trùng: 101/094/085) dù cùng
nền. Nếu luật là nguyên nhân tất định, hai tập phải giống nhau về cơ bản.
**PO tự nhận lỗi thiết kế: gate (c) "không ca nào xấu đi" áp lên hệ
temperature 0.2 không tất định sẽ gần như luôn hỏng bất kể bản vá tốt xấu**
— và cổng --so-sanh thoát-mã-1 của QA cũng mang cùng giả định, cần tinh
chỉnh sau khi có số nhiễu.

**PHÁN QUYẾT: DUYỆT LƯỢT ĐO NHIỄU NỀN** (~$0,22) — chạy LẠI đúng cấu hình
nền (prompt nguyên bản, thước 394feef), so với 161529: đếm ca tự đổi trạng
thái giữa hai lượt CÙNG cấu hình. Phân loại: **HẠ TẦNG ĐO** — con số floor
dùng mãi cho mọi gate sau, không tính vào gói B2.

**Quy tắc đọc kết quả — đặt TRƯỚC khi đo, CHỈNH theo phương pháp QA:**
- Công cụ: `--so-sanh` trên hai lượt CÙNG cấu hình — "Ca XẤU ĐI" CHÍNH LÀ số
  ca tự flip, không cần viết thêm (QA chỉ ra).
- **KHÔNG dùng ngưỡng số đếm** ("đỏ khi vượt floor") — QA đúng: 14 xấu/18 tốt
  có thể là 32 flip ngẫu nhiên HOẶC 1 hồi quy thật lẫn 31 flip, cùng một số.
  Số đếm mù đúng chỗ bảng sinh ra để soi.
- **Phương pháp đúng: GIAO của các tập ca-xấu-đi qua N lượt lặp.** Ca xấu đi
  ở MỌI lượt = tín hiệu gần như chắc; ca chỉ xấu một lượt = nhiễu. Áp cho B2:
  giao của {7 ca lượt 3-luật} ∩ {5 ca lượt 2-luật} ∩ {ca xấu ở lượt nhiễu} —
  101/094/085 (đã xấu ở cả hai lượt patch) là ứng viên tín hiệu, kiểm tiếp
  chúng có xấu trong lượt nhiễu-nền-thuần không: xấu → nhạy nhiễu; sạch →
  hiệu ứng thật của luật, xử riêng từng ca.
- Nếu giao ∩ rỗng (mọi ca xấu đều là nhiễu) → gate (c) coi như ĐẠT → SHIP
  luật 4+1. Nếu giao có ca → đọc transcript ĐÚNG ca đó (D1 sẵn), không đọc
  cả 5.
- **TẦNG LỌC A1 (QA bổ sung, PO duyệt): trước khi đọc transcript bất kỳ ca
  nào trong giao, loại ca thuộc nhóm A1 (from_bank dữ liệu hỏng — ví nhận
  gán sai).** 7/14 ca xấu của cặp patch nằm trong A1 (011/038/040/064/065/
  068/094). Ca A1 xấu ổn định KHÔNG chứng minh prompt hồi quy — nó chứng
  minh dữ liệu vẫn hỏng (đã biết, có phương án reseed riêng). Quy tắc chốt:
  giao khác rỗng nhưng CHỈ chứa ca A1 → gate (c) vẫn ĐẠT → ship. Chỉ
  101/085 (scope to_bank/internal_wallet, KHÔNG A1) mới là tín hiệu thật
  đáng đọc transcript. 094 là from_bank → xếp SAU 101/085, và khi đọc phải
  kiểm trước lỗi có phải chữ ký A1 (cite_*) không — QA trung thực: 094 hỏng
  thêm complaint_type/scope nên chưa chắc thuần A1, không khẳng định là nhiễu.

**C13:** duyệt hướng coder — chuyển CẢ BỐN file (3 lượt bỏ + nền thước cũ
131834) vào archive như MỘT CỤM kèm README "thước cũ, trước d72017a";
quyết định cuối của QA. Giữ lại: 161529 · 163222 · 164859 · 041244.

C4 + ADR-021: coder đang làm đúng lệnh, dự thảo theo đủ 3 điều kiện.

## C4 — BOLA NẶNG HƠN: chuỗi tấn công CHỈ TỪ SĐT (security b81466e)

- Xác nhận độc lập BOLA: người lạ REST lookup_transaction → 200 lộ
  amount/fee/status/des/rec_code. Đường tool (agent) đúng ⇒ lỗ ở tầng REST.
- **Nặng hơn mô tả C4 gốc:** KHÔNG cần biết mã giao dịch. phone+amount
  (contract cho phép) → 200 multiple_matches → candidates kèm trans_id của
  nạn nhân. Chuỗi trọn: SĐT → danh sách → tra từng cái → chi tiết đầy đủ.
- **ĐIỀU KIỆN BẢN VÁ (đã chuyển coder KHẨN):** chặn áp cho CẢ đường TÌM KIẾM
  phone+amount, không chỉ đường trả chi tiết. des (PII khách gõ) + rec_code
  (khoá tra cứu) là 2 trường lộ đáng lo nhất.
- Sửa rẻ cùng C4: phone thiếu amount → 500 (ValueError không được
  _handle_tool_error bắt) trái contract status='error' — vá luôn.
- Security đã quét cả họ REST tool: lookup_transaction là route any_authenticated
  DUY NHẤT — đúng chỗ thủng, các route khác không cùng lỗi. Rà xong sớm =
  thu hẹp phạm vi C4 chính xác, không mò.

## NHIỄU NỀN 20/40 — GÓI B2 KHÔNG KẾT LUẬN ĐƯỢC (PO phán quyết đêm 14→15/08)

**Kết quả:** hai lượt HOÀN TOÀN GIỐNG NHAU (161529 vs 170312) → 20/40 ca flip
check, 7 ca "xấu đi", tổng 30 vs 23 case lỗi — CHỈ DO NHIỄU. "Kết quả tốt
nhất ngày" (30→23) TÁI LẬP BẰNG CÁCH KHÔNG LÀM GÌ. Coder tự phủ nhận báo cáo
trước của chính mình — trung thực đúng chuẩn.

**PO công nhận kết luận:** gate (c) không-hỏng theo quy tắc nhiễu-aware,
NHƯNG gate (b) mất hiệu lực cùng lý do (4 ca B2 + 083 tự sạch ở nền lần 2
prompt nguyên bản). 3 ca nghi 101/094/085 đều flip trong nhiễu → nhạy nhiễu.
⇒ **~$1,5 đo hôm nay KHÔNG trả lời được câu hỏi gói B2** — LỖI THIẾT KẾ ĐO
(một-lượt/cấu-hình trên 40 case không đủ phân giải), không phải lỗi ai.

**PHÁN QUYẾT — TÁCH HAI CÂU HỎI:**

A. **HẠ TẦNG ĐO (PO-agent duyệt, ưu tiên cao — dùng cho MỌI gate sau: B6 cắt
   token, Phase 3 learning-loop):**
   - temp=0 cho EVAL — NHƯNG ⚠️ ĐIỀU KIỆN CỨNG: KHÔNG hạ temp production.
     graph.py phục vụ cả agent thật (giữ 0.2 cho tự nhiên) lẫn eval. Phải có
     đường riêng (env var / tham số harness) để CHỈ eval chạy temp=0, prod
     nguyên 0.2. Sửa graph.py hạ thẳng 0 là đổi hành vi sản phẩm — cấm.
   - gate: **GIAO TẬP ca-xấu qua k lượt là phần KẾT LUẬN mở/đóng cổng**
     (ca xấu ở mọi lượt = tín hiệu); so-TRUNG-BÌNH chỉ là CHỈ SỐ PHỤ báo xu
     hướng, KHÔNG dùng mở/đóng cổng — QA đính chính đúng: trung bình vẫn gộp
     mất "1 hồi quy thật lẫn 31 flip". (Sửa bản duyệt trước ghi "so tổng qua
     k lượt" — chưa đủ, tổng cũng mù cùng chỗ.) QA trình kỹ khi vào hạng mục.
   - k=3 tối thiểu; cân nhắc n=40→120 (nhiễu giảm theo căn bậc hai, đã có
     sẵn 120 case). Chi phí: k=3×40 ≈ $0,66/cấu hình.
   - Đây là hạng mục RIÊNG của đợt kế tiếp, KHÔNG tính vào gói B2. Coder +
     QA cùng thiết kế; KHÔNG làm đêm nay (cần đầu óc tỉnh).

B. **LUẬT 4+1 (đánh đổi tiền/thời gian — CỜ CHO PO THẬT):** HOLD, patch giữ
   ở scratchpad/b2_luat41.patch (không mất). Đo lại MỘT lần tử tế khi hạ
   tầng A sẵn. PO-agent nghiêng phương án (c) của coder — không ship trên
   giả thuyết chưa đo, nhưng cũng không chờ "bằng chứng" từ một phương pháp
   đã biết là không cung cấp được. Lý do gắn cờ PO thật: (b) là input trực
   tiếp cho quyết định LÙI MỐC 150 người — nếu bộ đo chất lượng cơ bản chưa
   đủ phân giải thì KHÔNG có cơ sở tuyên bố "chất lượng đạt ngưỡng cho người
   thật". Đây là bằng chứng mạnh nhất trong ngày cho khuyến nghị đóng-băng-
   tính-năng.

C4 độc lập, coder tiếp tục — không chờ A/B.

## C4 XONG + CI CHẠY THẬT LẦN ĐẦU (39a08b0→2bf73ac, đêm 14→15/08)

- **C4/BOLA vá xong** kèm ADR-021 (+45/0): lọc tầng matches, siết theo vai ở
  REST, vô điều kiện ở create_ticket, 9/9 điều kiện tự chấm + ca đối chứng
  CSKH. Chờ security rà (probe + ADR-021).
- **CI lần đầu lộ 4 lỗi hạ tầng (coder đã vá hết, không lỗi code):** (a)
  FIELD_ENCRYPTION_KEY CI 33 byte → mọi job chết ở import, "đỏ" nhìn như vi
  phạm hiến pháp; (b) tsc thiếu next typegen; (c) vitest chết vì Node 20 <
  jsdom cần 22 — **bộ test frontend CHƯA TỪNG chạy được trên CI**; (d) 2 job
  eval thiếu data/generated → thêm make data. Đúng giá trị của "CI chạy thật".
- **Coder tự báo lỗi của chính mình:** allowlist gitleaks ràng theo paths mà
  gitleaks nối OR → toàn bộ ci.yml thành vùng mù cho generic-api-key; tự thử
  bằng Fernet key thật → im lặng → thêm condition=AND → bắt được. Kiểm bằng
  đúng bản gitleaks CI dùng.

## PHÂN LOẠI 5 VIỆC PO + 3 VIỆC TESTER (PO phán quyết)

**PO-agent DUYỆT ngay (không chạm sản phẩm, chỉ chặt hơn):**
- **PO-3**: gate deploy.yml bằng `workflow_run` gated theo CI success — DUYỆT.
  Đúng checklist đóng gói (job deploy phải có needs); hiện chưa deploy được
  nên vá lúc này là vô hại, để sau khi có secret thì "mọi push main deploy
  bất kể test đỏ" là bug production nghiêm trọng. Coder làm trên .github/.
- **PO-4**: khai `engines` trong frontend/package.json (npm báo LỖI thay vì
  cảnh báo khi sai Node) — DUYỆT. package.json ngoài vùng coder → PO-agent
  ủy quyền một-lần cho coder sửa đúng 1 dòng engines, security/tester không
  đụng file đó đợt này.

**BẮT BUỘC PO THẬT (không ai làm thay được — nêu ở phần trả lời):**
- **PO-1 KEY THẬT TRONG LỊCH SỬ GIT** (AI_LOG_API_KEY giảng viên, 2 commit cũ):
  ưu tiên tuyệt đối = XOAY KEY với giảng viên (vô hiệu hoá = key trong lịch
  sử thành vô hại). History rewrite là THỨ YẾU + RỦI RO (force-push nhánh
  người/CI khác đã đọc — chạm luật cấm tự-động của global) → PO thật quyết
  minh thị, KHÔNG vai nào tự làm, KHÔNG nhờ vai khác làm thay.
- **PO-2**: đặt OPENAI_API_KEY secret (2 job eval 0/120 pass vì rỗng) —
  dashboard PO thật.
- **PO-5 = ST2-P0-3** (security-findings-gate đỏ vì live-chat SĐT thô) —
  chính là 4 câu PO thật đang treo. CI giờ ĐỎ vì nó → thành chặn cứng, không
  còn là nợ hoãn được.

**TESTER (T-1/T-2/T-3):** T-1 gỡ xfail test BOLA (giờ XPASS = bằng chứng C4
vá) · T-2 sửa fixture test_sweep dùng USR-B với giao dịch không phải của
mình (fixture đang làm đúng thứ C4 vừa cấm — đổi USR-A hoặc TXN-0001) · T-3
coder ghi chú: test create_ticket xfail nay vô nghĩa (USR-B là bên nhận hợp
pháp) — tester xem lại nó chứng minh đúng thứ nó tuyên bố không.

## F-12 + PO-3 + PO-4 (3ce91b1) — PO ghi nhận

- F-12 XONG 5/5. Thứ tự 3 lớp là bài học: (1) KHÔNG đếm cho challenge người
  khác — nếu không, gửi bừa session_id sếp khác = DoS khoá tài khoản họ;
  (2) chặn "đã khoá" TRƯỚC khi so mã; (3) commit() TRƯỚC khi raise vì
  get_session rollback cả HTTPException — bẫy lặp y nguyên từ /auth/otp/verify.
- PO-3 XONG: deploy.yml gated workflow_run, xét đồng thời conclusion=success
  VÀ head_branch=main (thiếu một vế = cổng hình thức).
- PO-4 DUYỆT MỞ RỘNG: engines + frontend/.npmrc (engine-strict=true) — engines
  một mình chỉ EBADENGINE exit 0; .npmrc là phần còn thiếu để đạt "báo lỗi
  thay vì cảnh báo". Không phải phạm vi mới, là hoàn tất đúng lời uỷ quyền.
- **Việc riêng đợt sau (PO duyệt tách):** thống nhất 401=sai-mã / 403=đã-khoá
  cho cả /auth/otp/verify lẫn approve — coder lùi đúng (đổi mã trạng thái +
  sửa test vùng tester = ngoài F-12). Có tester đi kèm.
- Ghi nhận lỗi đo pipe-tail-nuốt-exit-code (đo vỏ thay ruột) — họ "assertion
  trùng mặc định".

## 🔴 SỰ CỐ TOÀN VẸN THƯỚC (đêm 14→15/08) — dấu-thước-băm-nội-dung bắt được

**Sự việc:** eval/golden_set.jsonl working-tree bị sửa CHƯA COMMIT, mồ côi
(không phán quyết nào cho phép): 4 case B2 (028/029/046/047) gỡ nhãn
must_offer_before_creating_ticket (PO duyệt aa5d593), 4 dòng re-serialize
nén = script ghi đè. Dấu thước e44e76a→aab1e12. Đây là HẠ THƯỚC đúng chỗ
gói B2 đang đo.

**Xử lý:** QA phát hiện qua dấu thước, KHÔNG tự khôi phục (có thể là việc
dở của người khác) — đúng. PO kiểm chứng độc lập, hỏi coder (cho cơ hội lưu
bản sao nếu là thí nghiệm), chờ xác nhận rồi QA git checkout khôi phục.
Đang chờ coder trả lời "có phải bạn không".

**BÀI HỌC THIẾT KẾ (ghi ĐÚNG như QA yêu cầu, không tô thành tầm nhìn):**
dấu thước = BĂM NỘI DUNG phần chấm bắt được sự cố này. NHƯNG QA tự đính
chính: thiết kế đó đến từ việc LO BÁO ĐỘNG GIẢ làm phiền cặp đo đang chạy,
KHÔNG phải từ tiên liệu kịch bản sửa-file-chưa-commit — may mắn có phần.
Bài học thật, giữ nguyên văn: "một dấu vân tay phải bám vào thứ nó định
canh (nội dung quyết định điểm số), không bám vào tương quan lỏng lẻo
(commit hash) — bám lỏng thì vừa kêu oan khi yên, vừa im đúng lúc có
chuyện." (Nếu còn đóng dấu bằng HEAD, sửa working-tree chưa-commit sẽ VÔ
HÌNH: hai lượt vẫn "40 case", vẫn so được, ra cặp số trông hợp lệ mà một
nhánh bị gỡ check.)

**Xử lý cập nhật:** QA đã bảo toàn CẢ HAI bản ngoài repo (bản-bị-sửa +
bản-gốc-HEAD) ⇒ rủi ro mất thí nghiệm = 0 ⇒ PO GẬT khôi phục ngay không
chờ coder; điều tra nguồn chạy song song. QA dựng canh chừng 20s/30 phút.

**✅ ĐÃ LÀNH (00:5x):** golden_set về HEAD, 4 nhãn B2 đủ, dấu thước
e44e76a6f06e — cặp với lượt 170312 hợp lệ lại. Ai đó (nhiều khả năng coder
sau khi PO hỏi) tự trả lại, KHÔNG phải QA (QA vẫn chờ gật — đúng kỷ luật).
Hai bản bằng chứng giữ trong scratchpad QA phòng truy lại.
**✅ NGUỒN ĐÃ RÕ — ĐÓNG SỰ CỐ (coder xác nhận):** vô ý, KHÔNG gian lận,
KHÔNG thí nghiệm. Coder chạy `gen_dataset.py --out <scratchpad>` để đo thời
gian sinh dữ liệu (điều tra 2 job eval đỏ). Bẫy: gen_dataset.py có `eval_dir`
RIÊNG mặc định `ROOT/eval` (dòng 181), ghi golden_set + heldout BẤT KỂ `--out`
trỏ đâu — ĐƯỜNG GHI THỨ HAI ngoài tham số truyền. heldout tái lập trùng byte
(seed cố định) nên git không thấy; chỉ nhãn NGƯỜI thêm tay vào golden_set mất.

**LỖ NGHIÊM TRỌNG HƠN, coder tự bắt + vá (2bf73ac→sửa):** `make data` trần
mà coder thêm vào 2 job eval CI sẽ ghi đè golden_set của runner MỖI lượt CI,
chấm eval bằng thước ngắn hơn, KHÔNG cảnh báo — biến lỗi một-lần thành lỗi
thường-trực trong hạ tầng đo. Đã đổi `--eval-out ${RUNNER_TEMP}/eval-vut-di/`,
kiểm chứng `git status eval/` sạch. Đây là save lớn: nếu lọt, CI sẽ đo bằng
thước sai vĩnh viễn mà không ai biết.

**LUẬT PHÒNG NGỪA (PO duyệt, coder đề xuất):** `gen_dataset.py` TỪ CHỐI ghi
eval/ trừ khi có cờ minh thị `--cho-phep-ghi-de-thuoc`. Cấm bằng cấu trúc,
không dựa trí nhớ — đúng triết lý contract-as-code. Coder làm guard (tooling
gần vùng của mình), QA thêm test canh (chạy gen_dataset không cờ → golden_set
bất động). Bài học chung: script sinh dữ liệu có đường ghi ngoài tham số mình
truyền — kiểm "nó ghi ĐÂU", không chỉ "mình truyền --out đâu".

**LUẬT MỚI (PO phê chuẩn): thí nghiệm KHÔNG BAO GIỜ sửa golden_set gốc.**
Thước dùng chung — mọi thí nghiệm chạy trên BẢN SAO (scratchpad/), không
đụng file gốc. Cân nhắc: thêm test/pre-commit chặn commit golden_set khi
không kèm ADR/ghi chú duyệt (đưa vào hạng mục hạ tầng đo).

## ADR-020/BR-12 MAKER-CHECKER — review lớp 2 + 2 lệch QA bắt (PO, đêm 14→15/08)

**Review lớp 2 nội dung: ĐẠT.** Biểu thức `(created_by IS NULL) OR
(approved_by != created_by)` đúng · giải thích NULL-semantics (approved_by
NULL → CHECK ra NULL → SQL coi thoả) chính xác · ép hai tầng (DB chốt cuối,
route 403 đọc-được) đúng · giới hạn "10/10 created_by NULL ⟹ chưa ràng dòng
nào" ghi trung thực. QA test hiệu lực 3 mặt 10/10 xanh.

**LỆCH 1 (QA bắt) — BR-12 THIẾU SỐ INV = thiếu vế HIỆN DIỆN.** BR-10→INV-07,
BR-11→INV-14, BR-12→(chưa có). test_invariants KHÔNG canh tồn tại của
ck_resolutions_maker_checker_br12: xoá constraint khỏi models.py thì file QA
đỏ nhưng bộ bất biến vẫn 22/22. Đúng cặp hiện-diện-vs-hiệu-lực, lần này
thiếu vế ngược. → thêm **INV-15** vào danh sách invariants contract (sửa
contract, coder làm) + QA thêm test hiện diện đối xứng test_inv14. Bump
CONTRACT_VERSION lại.

**LỆCH 2 (quy trình) — bump version TRƯỚC security rà + PO review lớp 2.**
ADR-020 tự ghi trạng thái "Dự thảo — chờ security rà + PO thật ký" nhưng
contract đã áp + CONTRACT_VERSION đã v2.2.0. Coder hiểu "DUYỆT làm ADR-020"
của PO là duyệt áp — mơ hồ ở lệnh PO. KHÔNG rollback (nội dung đúng, chặt
hơn, maker-checker đã duyệt nguyên tắc từ Phase 0). BÀI HỌC ranh giới:
"duyệt nguyên tắc" ≠ "duyệt áp contract"; lần sau bump version SAU security
rà + PO review lớp 2, kể cả khi nguyên tắc đã duyệt. Đóng nốt: security rà
ADR-020 bổ sung NGAY (biểu thức + hai tầng).

**CHO PO THẬT — GIỚI HẠN COMPLIANCE:** BR-12 hiện KHÔNG bảo vệ dữ liệu nào
(10/10 created_by NULL) — chỉ ràng resolution TƯƠNG LAI tạo qua route mới.
Sự tồn tại constraint KHÔNG phải bằng chứng "đã có maker-checker đầy đủ".
Khi đánh giá sẵn-sàng cho auditor EU/US: maker-checker mới bắt đầu từ đây,
chưa phủ lịch sử.

## RÀ BẢO MẬT ADR-020/BR-12 (b984bec) — ĐẠT CÓ ĐIỀU KIỆN, 4 phát hiện (PO phán)

Biểu thức đúng (probe rollback xác nhận), hai tầng khớp cả ở cửa hở, giới hạn
10/10 NULL đúng. NHƯNG 3 điều kiện trước khi BR-12 coi là có hiệu lực:

**F-17 (CAO) — cửa NULL đang được NUÔI TIẾP, DUYỆT bịt:** propose_resolution()
khai created_by mặc định None ⟹ bỏ quên là IM LẶNG; seed_demo_scenarios.py
gọi 4 lần (149/164/179/197) KHÔNG truyền created_by ⟹ mọi hàng demo miễn
nhiễm maker-checker ở CẢ HAI tầng — và đó đúng là hàng đem diễn rồi duyệt.
→ Coder: đổi created_by thành **keyword-only BẮT BUỘC, bỏ default** (bỏ quên
thành TypeError bắt lúc test) + sửa 4 call site. KHÔNG backfill (đoán tên =
lỗi F-11). Bịt xong thì 10/10 NULL tự hết theo thời gian.

**F-18 — BR-12 không canh nhánh TỪ CHỐI, PO DUYỆT MỞ RỘNG:** created_by=
rejected_by ghi được (probe). Chạm thẳng ADR-019: reject_reason là phán đoán
ĐỘC LẬP của người để chấm AI; người tự-từ-chối + tự-dán-nhãn đề xuất của
CHÍNH MÌNH là vòng-tự-khen phiên bản con người, và nhãn đó chảy vào phễu học
Phase 2. Mở rộng nhất quán với chính lập luận ADR-019 nên PO duyệt: biểu thức
gồm cả `(rejected_by IS NULL OR rejected_by != created_by)`. Vì ADR-020 CHƯA
PO thật ký → gộp reject vào ADR-020 TRƯỚC khi ký (không cần ADR riêng); coder
cập nhật biểu thức + text ADR + migration, security re-probe, QA thêm mặt
test reject.

**F-19 — LUẬT NGHIỆM THU: BR-12 phải chạy trên bản REBUILD.** Container đang
chạy CHƯA có BR-12 (guard route grep=0, model thiếu constraint) trong khi DB
đã có ⟹ tự duyệt hàng có created_by hôm nay ra HTTP 500, và mọi đo trong
container là đo code cũ. "22 passed hash khớp" trong container KHÔNG chứng
minh gì về BR-12. Nghiệm thu BR-12 (+ F-17/F-18) chạy sau docker compose
build. Security ghi rõ thay vì lặng — chuẩn.

**F-20 — INV-15 test phải khẳng định CẢ TÊN LẪN BIỂU THỨC** (khai thiếu biểu
thức thì đổi = vẫn xanh), đích 23 passed. QA + coder phối.

Nhắc: `.claude/state/contract-hashes.json` bump 60977cba503f CHƯA COMMIT —
coder commit cùng đợt INV-15 kẻo mất/commit nhầm.

- Xoay LANGCHAIN_API_KEY theo hướng dẫn security (5 phút).
- Chạy `python scripts/export_project_knowledge.py` + upload lại Project
  knowledge SAU khi coder xong bước 3 (contract mới chốt) — refresh trước
  đó sẽ lại lỗi thời ngay.
- Các quyết định đang mở còn lại: đặc tả nhóm B2 đã phán ("thông báo + đề
  nghị") — nếu muốn đổi thì báo trước khi tester sửa nhãn.

## ĐỢT KỸ THUẬT ĐÓNG (bdc64e3 + b999dec) — chặn CHỈ còn 3 việc PO thật

- F-17/F-18/INV-15 xong, contract v2.3.0, 23/23. QA test INV-15 ĐỌC biểu
  thức TỪ CONTRACT (chuỗi cũ là chuỗi con dạng C → test "có chứa" xanh dù
  canh nửa ràng buộc → F-18 dưới dạng test). F-19: grep container SAU rebuild
  xác nhận BR-12 có mặt (trước rebuild=0). Bảng 6 ca đồng nhất Postgres+SQLite.
- C2 lỗ 2: job route-guards-docker + "SKIP LÀ ĐỎ" (đọc junit, đỏ nếu tests==0/
  skipped>0 vì pytest.skip luôn exit 0). Vế chưa đo: nhánh CÓ-CHẠY chưa thực
  thi trên runner → CI-4/CI-5 của QA.
- CI sau đợt: 384 passed · đỏ CHỈ còn note (28, chờ PO-5) + findings-gate/
  appsec (PO-5) + 2 job eval (PO-2 secret).

**⟹ ĐƯỜNG GĂNG DUY NHẤT: 3 việc PO THẬT** — PO-1 xoay key giảng viên · PO-2
đặt OPENAI_API_KEY · PO-5 chốt mức che note (=ST2-P0-3). Đội máy hết việc tự
làm được. Sau 3 việc: note code (13 test chờ) → CI xanh trọn → CI-4/5 → đóng.
