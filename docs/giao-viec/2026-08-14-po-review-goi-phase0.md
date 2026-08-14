# PHIẾU RÀ SOÁT PO — Gói Phase 0 (ADR-018/019 + diff contract)

> PO-agent rà 14/08. Trạng thái: KHUYẾN NGHỊ DUYỆT sau 1 sửa lỗi + các điều
> kiện dưới đây. Quyết định cuối cùng: PO thật (xem mục "Chốt của PO thật").

## 1. Lỗi phải sửa trước khi áp dụng diff

- **Trùng số bất biến:** diff đặt bất biến mới là `INV-13`, nhưng INV-13 ĐÃ
  TỒN TẠI trong `contracts/agent-tools.yaml` (tool_results +
  cited_tool_result_ids). Đánh số INV là toàn cục xuyên 3 file contract —
  bất biến mới của BR-11 phải là **INV-14**.

## 2. Phán quyết 4 điểm coder trình

| # | Điểm | Phán quyết đề xuất |
|---|---|---|
| ① | Taxonomy 7 giá trị + cờ `la_tin_hieu_hoc` | **DUYỆT — tốt hơn bản kế hoạch gốc 5 giá trị.** Tách "đề xuất sai ở đâu" khỏi "từ chối không do lỗi" (trung_case, khach_rut) chặn đúng nguy cơ bơm case-không-có-gì-để-học vào bộ eval. Đây là cải tiến thật, ghi nhận. |
| ② | Ranh giới `thieu_can_cu` vs `request-more-info` | **DUYỆT theo đề xuất coder**: thiếu-tạm-thời → `request-more-info` (need_more_info); thiếu-không-thể-bổ-sung → reject `thieu_can_cu`. ĐIỀU KIỆN: ghi ranh giới này thành `ghi_chu` ngay trong enum của contract (để tester viết test từ đó), và UI màn reject hiện gợi ý "nếu có thể bổ sung → dùng Yêu cầu điều tra thêm" khi sếp chọn giá trị này. |
| ③ | Ghi chú tự do | **DUYỆT CÓ ĐIỀU KIỆN** đúng 3 điều kiện coder nêu (scrub NGAY LÚC GHI · giới hạn độ dài ≤500 ký tự · không bao giờ trả trên route customer) + 2 điều kiện bổ sung của PO: (a) ghi chú KHÔNG tự động theo case ứng viên ở Phase 2 — chỉ vào export sau khi người duyệt xem (cổng kép chống PII/poisoning), (b) bắt buộc với `khac`, tuỳ chọn với giá trị khác. Vẫn chờ ý kiến security (nhiệm vụ 3 của họ) trước khi code phần này — các phần khác của Phase 1 không phải chờ. |
| ④ | Backfill 1 dòng rejected cũ → `khac` + ghi chú "dữ liệu trước ADR-019" | **DUYỆT** — tường minh, 1 dòng, đúng cách. |

## 3. Đánh số ADR

DUYỆT phương án của coder: soạn nốt **ADR-016 (vé WS→Redis)** và **ADR-017
(TurnGuard)** — nợ từ 13/08 — và commit CẢ BỐN (016→019) trong cùng đợt, giữ
DECISIONS.md liền mạch không lỗ hổng. ADR-018/019 giữ số như đã trình.

## 4. Về ADR-018

Nội dung ĐẠT — đặc biệt mục "Lý do BÁC BỎ: đã thử đúng phương án lớp 1+2, đo
lại vẫn mất tin" là đúng loại lý-do-bác-bỏ chặn tối-ưu-ngược mà DECISIONS.md
tồn tại để giữ. Hai nợ cứng hoá (TTL `_session_staff`, lưới DB qua session
được tiêm) ghi trong ADR là đủ; lịch làm: cùng Phase 1 nếu gọn, không thì
tách việc riêng ngay sau.

## 5. Trình tự sau khi PO thật duyệt

1. Sửa INV-13 → INV-14 trong diff.
2. Áp diff vào `contracts/resolution-state-machine.yaml` (kèm ghi_chu ranh
   giới ② và cờ `la_tin_hieu_hoc`).
3. Ghi ADR-016/017/018/019 vào `docs/DECISIONS.md` (chỉ ghi thêm).
4. `python scripts/check_contracts.py --update` + bump `CONTRACT_VERSION`.
5. Vào Phase 1 code (phần ghi-chú-tự-do chờ security sign-off rồi làm sau
   cùng trong Phase 1).
6. Báo tester: contract mới đã chốt — bắt đầu viết test từ đặc tả (INV-14,
   CHECK br11, ranh giới thieu_can_cu/need_more_info, authz trường audit).

## Chốt của PO thật

- [x] **DUYỆT toàn gói theo phiếu này (kèm sửa INV-14)** — PO duyệt 14/08/2026.
- **Điều chỉnh ③ theo TM-03 của security (chặt hơn phiếu gốc, thay thế điều
  kiện (a)):** ghi chú tự do được phép TRONG hệ thống (scrub lúc ghi · ≤500
  ký tự · chỉ route staff), nhưng **KHÔNG BAO GIỜ xuất ra ngoài** — kể cả đã
  scrub, kể cả vào `eval/candidates/`. File xuất chỉ mang enum. Người duyệt
  đọc ghi chú trong hệ thống rồi TỰ VIẾT LẠI case bằng lời mình + dữ liệu
  seed tổng hợp (luật "cấm nguyên văn" — `docs/security/threat-model-learning-loop.md`).
  Bắt buộc ghi chú với `khac`, tuỳ chọn với giá trị còn lại.
