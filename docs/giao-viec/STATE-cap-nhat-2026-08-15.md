# Trạng thái hiện tại
Cập nhật: **2026-08-15 (Đợt 2 khoá lại + đã migrate sang P-226)** · PO-agent điều phối 4 vai (Claude Code)

## Bối cảnh nạp lại (phiên mới ở P-226 đọc trước)
> Repo migrate P-121 → **P-226**, đầy đủ lịch sử. Nhánh làm việc: `dev/learning-loop` (256 commit),
> `main` 104 commit. FIN-05 — AI Agent CSKH ví điện tử xử lý khiếu nại, chuẩn fintech EU/US.
> Đội = 4 phiên Claude (PO điều phối · coder/tech-lead · tester · security), đồng bộ qua **git +
> cross-session message**, mỗi vai chỉ ghi vùng của mình (§4). Cây làm việc DÙNG CHUNG → mọi
> git stash/commit/checkout/clean phải kèm pathspec vùng mình.
> Đọc: CLAUDE.md → file này → `docs/giao-viec/2026-08-15-ke-hoach-3-chu-de-nang-cap.md`
> (~18 luật đo + mọi finding) → 5 ADR gần nhất (tới ADR-024). Đó là toàn bộ ký ức Đợt 2.

## Vừa xong (đã land + verify)
- **Spotlighting** F-22..F-27 — bọc dữ liệu untrusted 4 cửa, nhãn trung tính, verify trong container.
- **Lọc đầu ra O1-O4 + luật XUẤT XỨ** — verify CẢ HAI nửa: origin-rule 14/14 · efficacy 15/16 ·
  chặn-nhầm 0/8 · 0 gán-sai. Vá dọc đường: JSON-comma phantom · F-27 (bỏ neo "OTP") · F-26 (nhãn-sau-scrub).
- **5a cảm xúc** contract v2.4.0 KÝ Câu 1+2 (ADR-022): thread_signals + emotion_signals dựng xong.
- **ADR-020 maker-checker ĐÃ KÝ** (PO thật, 2026-08-15) → BR-12 hiệu lực: CSKH/AI tạo ticket,
  CHỈ supervisor duyệt; DB CHECK creator≠approver + route-guard 403.
- **AI-log**: vá bug archive (chỉ archive batch đã submit, không archive cả file) — đã đồng bộ P-226.
  Backlog ~9135 log unique đã lên server chấm điểm; archive local dedup 165MB→17MB (không vào git).

## Quyết định đã CHỐT phiên này (không còn "đang cân")
- **#4 chip câu 3**: DUYỆT — khung "chip vận-hành mức HỘI-THOẠI, KHÔNG nhãn trạng-thái-tâm-lý",
  ngưỡng **N=3**. Đặc tả: `docs/giao-viec/2026-08-15-spec-cau3-dau-hieu-cam-xuc-cskh.md` (§5 cần cập nhật theo).
- **PO-5 field `note`**: DUYỆT (che-lúc-ghi / giữ-4-số / KHÔNG commit transcript) → coder implement.
- **Lượt end-to-end "sau" O1-O4**: DUYỆT 1 lượt (chạy trên version-freeze coder chốt, đóng-dấu 2 đầu).
- **PO-1** xong (key đã xoay). **150 người**: CHƯA test — chờ số từ lượt end-to-end.

## Đang dở — đủ để tiếp ngay
- **coder**: implement field `note` (PO-5) → mở khoá 13-14 test note + CI security-gate; báo tester version-freeze.
- **coder**: O2-anchors + filler-word (Luật 18, retroactive F-24/F-27) · đợt CỔNG-A gộp 3 oracle
  (số-ngắn+tên+phủ-định) theo xuất-xứ · **câu-4 RAG retrieval** (3/5 câu chính sách hợp lệ agent không
  trả được — sửa chunk/embedding, KHÔNG nới ràng buộc 9).
- **tester**: chạy lượt end-to-end (4 câu: cổng-96 · siết-nhầm 18-ca+🔇 · timeout-vs-recursion · F-25(b))
  khi coder chốt freeze; báo số cho PO. Hạ tầng đo temp=0/k≥3 (đang HOLD, floor nhiễu 20/40).
- **security**: verify PII masking `note` khi land · MT-E02 traceback · canh nền đối kháng 18/20.

## Chặn / chờ PO thật
- **PO-2**: đặt OPENAI_API_KEY thành secret trên GitHub (đã có hướng dẫn) → mở 2 CI eval.
- **Hướng 150 người**: quyết sau khi có số end-to-end (4 góc chưa-sẵn-sàng: TPM · 429→500 · timeout · RAG).
- Keys AI-log/LangChain: PO tạo lại (key cũ 401) → cần `SSL_CERT_FILE=$(python -m certifi)` trong `.env`.

## Cảnh báo còn tồn
- **gate-96 (chặn-nhầm reply thật) TẮT có tài liệu** — bật cùng lượt end-to-end (payload chỉ có sau lượt chạy).
- Mốc nền đối kháng chốt VĨNH VIỄN **18/20** (he_thong 6c5fff420bb9). MT-A01/F-01 không quay lại nhánh "trước".
- **oracle-phủ-định "không phải 21"** còn lọt 1 bit/lượt (có tài liệu) → đợt CỔNG-A.
- CI: note-tests (chờ note land) · 2 eval (chờ PO-2 secret) · CI-4/5 route-guards-docker chưa nghiệm thu.

## Việc kế tiếp
1. coder: field `note` + báo version-freeze cho tester.
2. tester: lượt end-to-end (4 câu) → số cho PO quyết hướng 150 người.
3. PO-2 secret → mở CI eval.

## Hoãn có chủ đích
- reseed gộp (⚠️ gỡ lọc-A1 khi from_bank sửa) · 401/403 hai route OTP · B3 timezone (31 utcnow) ·
  lộ trình EU/US G1(SLA)/G3(audit bất biến) — xem PO-TONG-KET.
