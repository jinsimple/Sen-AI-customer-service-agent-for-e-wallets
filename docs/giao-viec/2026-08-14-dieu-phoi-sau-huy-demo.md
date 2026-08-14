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

## Việc của PO thật

- Xoay LANGCHAIN_API_KEY theo hướng dẫn security (5 phút).
- Chạy `python scripts/export_project_knowledge.py` + upload lại Project
  knowledge SAU khi coder xong bước 3 (contract mới chốt) — refresh trước
  đó sẽ lại lỗi thời ngay.
- Các quyết định đang mở còn lại: đặc tả nhóm B2 đã phán ("thông báo + đề
  nghị") — nếu muốn đổi thì báo trước khi tester sửa nhãn.
