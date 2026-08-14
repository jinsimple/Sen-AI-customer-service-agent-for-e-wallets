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

## Việc của PO thật

- Xoay LANGCHAIN_API_KEY theo hướng dẫn security (5 phút).
- Chạy `python scripts/export_project_knowledge.py` + upload lại Project
  knowledge SAU khi coder xong bước 3 (contract mới chốt) — refresh trước
  đó sẽ lại lỗi thời ngay.
- Các quyết định đang mở còn lại: đặc tả nhóm B2 đã phán ("thông báo + đề
  nghị") — nếu muốn đổi thì báo trước khi tester sửa nhãn.
