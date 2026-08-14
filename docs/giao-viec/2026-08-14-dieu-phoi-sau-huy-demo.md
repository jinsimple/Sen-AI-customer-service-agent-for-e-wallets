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

## Việc của PO thật

- Xoay LANGCHAIN_API_KEY theo hướng dẫn security (5 phút).
- Chạy `python scripts/export_project_knowledge.py` + upload lại Project
  knowledge SAU khi coder xong bước 3 (contract mới chốt) — refresh trước
  đó sẽ lại lỗi thời ngay.
- Các quyết định đang mở còn lại: đặc tả nhóm B2 đã phán ("thông báo + đề
  nghị") — nếu muốn đổi thì báo trước khi tester sửa nhãn.
