# Trạng thái hiện tại
Cập nhật: **2026-08-15 ~01:30** · Phiên vừa rồi: PO-agent điều phối 4 vai (Claude Code)

> Nhánh làm việc: **`dev/learning-loop`** (main đứng mốc ổn định, dev đi trước ~30 commit).
> Sổ điều phối chi tiết cả đêm 14→15/08: `docs/giao-viec/2026-08-14-dieu-phoi-sau-huy-demo.md`.
> Demo 14/08 ĐÃ HUỶ. Cơ chế đồng bộ = git (4 vai đều Claude Code trên repo, hết upload knowledge).

## Vừa xong (đêm 14→15/08 — mọi bản vá kèm bằng chứng chạy thật)
- **BOLA/C4 + ADR-021**: REST lookup_transaction lộ hồ sơ giao dịch CHỈ TỪ SĐT (phone+amount→
  multiple_matches). Vá bằng lọc-tầng-matches + siết theo vai + helper "một bên" (ví ∪ TK NH).
- **F-12**: route duyệt tiền không đếm lần dò OTP → vá 3 lớp (chống DoS + khoá-thì-mã-đúng-cũng-chặn).
- **Maker-checker BR-12 (ADR-020, contract v2.3.0)**: người đề xuất không tự duyệt/từ chối.
  Biểu thức dạng C, ép 2 tầng, INV-15. **F-17 bịt cửa NULL** (created_by keyword-only bắt buộc).
- **Migration reject-reason (BR-11/ADR-019) + F-13 (vá QA-02) + F-14** (rò phiên live-chat sang
  CSKH cũ = lỗ PDPA, vá TTL+dọn lô). ADR-016/017/018 ghi bổ sung.
- **CI chạy THẬT lần đầu** — lộ+vá 4 lỗ hạ tầng (FIELD_ENCRYPTION_KEY, tsc typegen, vitest Node,
  make data). Bộ test frontend/quét-guard trước nay chưa từng chạy trên CI.
- **Việt hoá UI** đợt 1+2 (nhãn từ contract, câu "chưa có agent" sai sự thật đã sửa).
- **Sự cố toàn vẹn thước** (golden_set bị gen_dataset ghi đè vô ý) — dấu-thước-băm-nội-dung
  bắt được, khôi phục, thêm guard cấm-ghi-thước + test canh.

## Đang dở — chi tiết đủ để tiếp ngay
- **field `note` (reject) CHƯA CODE** — TM-03 đã sign-off, 13-14 test đối kháng đang đỏ chờ.
  Chặn bởi PO-5 (chính sách che PII). Điều kiện: scrub LÚC GHI · fail-closed · không mở phạm vi
  đọc · GIỮ nội dung không-phải-PII. Coder vào ngay khi có chính sách.
- **Gói B2 (luật processing) HOLD** — nhiễu nền đo được **20/40 ca flip** ⟹ đo 1-lượt/40-case
  KHÔNG đủ phân giải. Cần hạ tầng đo: temp=0 CHỈ eval · gate = GIAO TẬP qua k≥3 lượt (không phải
  trung bình) · cân nhắc n=120. Patch ở scratchpad/b2_luat41.patch. Hạng mục riêng đợt sau.

## Chặn / chờ (CHỈ còn việc PO THẬT — đội máy hết việc tự làm)
- **PO-1**: xoay key (API key thật lọt `.env.example` commit eb40e58/b87164f, còn trong lịch sử;
  đã khỏi HEAD). Revoke+tạo mới; history-rewrite KHÔNG tự làm.
- **PO-2**: đặt `OPENAI_API_KEY` secret GitHub (2 job eval 0/120).
- **PO-5 = ST2-P0-3**: chốt che PII live-chat (khuyến nghị: che-lúc-ghi, giữ 4 số cuối, gộp
  description_raw, không commit transcript thật). Chặn field note + CI security-gate.
- **ADR-020 chờ PO THẬT KÝ** (trạng thái "Dự thảo", security đã rà đạt-có-điều-kiện).
- **Quyết định lùi mốc 150 người** — bằng chứng: floor nhiễu 20/40, maker-checker chưa phủ dữ
  liệu nào (10/10 created_by NULL), CI chưa từng chạy tới hôm nay.

## Cảnh báo còn tồn
- CI đỏ: test_reject_note (28, chờ note) · security-findings-gate/appsec (PO-5) · 2 eval (PO-2).
- Maker-checker BR-12 TỒN TẠI nhưng chưa RÀNG dòng nào (10/10 NULL) — không phải "đã có đầy đủ".
- CI-4/CI-5: nhánh CÓ-CHẠY route-guards-docker chưa thực thi trên runner (QA nghiệm thu).
- 2 file untracked: eval/results/quality_run_20260814_170312* (nền nhiễu lần 2, giữ làm bằng chứng).

## Việc kế tiếp đề xuất
1. PO thật xử 3 việc (PO-1/2/5) + ký ADR-020 + quyết lùi mốc — mở khoá mọi thứ còn lại.
2. Coder: field note (sau PO-5) · reseed gộp (brief riêng, ⚠️ gỡ tầng-lọc-A1 khi from_bank sửa xong).
3. Hạ tầng đo (coder+QA): temp=0-chỉ-eval + gate giao-tập k≥3.
4. PO thật cân nhắc sửa hiến pháp §3 (commit contract-hashes sau --update).

## Sau demo / hoãn có chủ đích
- Thống nhất 401=sai-mã/403=đã-khoá cho cả 2 route OTP · B3 timezone (31 chỗ utcnow) · B6 cắt token
  (chờ hạ tầng đo) · B4 L4-04 · lộ trình chuẩn EU/US G1(SLA)/G3(audit log bất biến) — xem PO-TONG-KET.
