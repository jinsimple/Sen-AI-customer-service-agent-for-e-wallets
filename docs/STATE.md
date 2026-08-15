# Trạng thái hiện tại
Cập nhật: **2026-08-15 (phiên Đợt 2 + bàn giao P-226)** · PO-agent điều phối 4 vai (Claude Code)

## 🔄 BÀN GIAO SANG P-226 — ĐỌC ĐẦU TIÊN
> **Repo đã migrate từ P-121 → P-226 (đầy đủ lịch sử).** Nhánh làm việc: `dev/learning-loop`
> (HEAD dacbefd, 256 commit). `main` = 104 commit. Đang code trong thư mục `P-226`.
>
> **Bối cảnh dự án:** FIN-05 — AI Agent CSKH ví điện tử xử lý khiếu nại, chuẩn fintech EU/US.
> Đội = 4 phiên Claude Code (PO-agent điều phối · coder/tech-lead · tester · security), đồng bộ
> qua **git + cross-session message** (SendMessage/ListAgents), mỗi vai chỉ ghi vùng của mình (§4).
>
> **PHIÊN MỚI Ở P-226 làm gì trước:** đọc `CLAUDE.md` (hiến pháp) → file này → sổ Đợt 2
> `docs/giao-viec/2026-08-15-ke-hoach-3-chu-de-nang-cap.md` (18 luật đo + mọi finding) →
> 5 ADR gần nhất trong `docs/DECISIONS.md` (tới ADR-024). Đó là toàn bộ ký ức Đợt 2.
>
> **AI-log:** logging chạy (session.jsonl). Pre-push hook đã cài. SSL cần dòng
> `SSL_CERT_FILE=$(python -m certifi)` trong `.env`. AI_LOG_API_KEY + LANGCHAIN keys ĐANG được
> tạo lại (key cũ 401). **9118 dòng backlog nằm ở P-121-new/.ai-log — submit từ P-121 khi có key mới,
> ĐỪNG xoá P-121-new tới khi submit xong** (deliverable #4).
>
> **Việc còn treo (không chặn, đã có tài liệu trong sổ Đợt 2):** đợt nâng CỔNG-A gộp 3 oracle
> (số-ngắn+tên+phủ-định) theo xuất-xứ · câu-4 RAG retrieval quality (3/5 câu chính sách hợp lệ agent
> không trả được — sửa chunk/embedding, KHÔNG nới ràng buộc 9) · MT-E02 traceback · hạ tầng đo temp=0/k≥3.
>
> **Chờ PO thật:** tạo lại keys · hướng đợt 150 người (lượt end-to-end đã cho dữ liệu: bộ lọc 17/17
> không siết nhầm, RAG retrieval là điểm yếu; 4 góc chưa-sẵn-sàng: TPM · 429→500 · timeout · RAG).


> Nhánh: **`dev/learning-loop`**. Sổ điều phối Đợt 2 (đầy đủ, ~18 luật + mọi finding):
> `docs/giao-viec/2026-08-15-ke-hoach-3-chu-de-nang-cap.md`. Đêm 14→15/08: sổ `2026-08-14-*`.
> Đồng bộ = git (4 vai cùng repo). Cơ chế: dấu-băm mọi phép đo · nháp-ngoài-repo · báo-trước-khi-land.

## Vừa xong (Đợt 2 — nhánh 5b chống-injection, verified CẢ HAI nửa)
- **Spotlighting** (F-22/23/24/25/26) — bọc dữ liệu untrusted 4 cửa, nhãn TRUNG TÍNH, verify trong container.
- **Lọc đầu ra O1-O4 + luật XUẤT XỨ** (số agent nói phải truy về tool result — trùng ràng buộc cứng 3):
  origin-rule verified 14/14 (corpus độc lập tester) · efficacy 15/16 · chặn-nhầm 0/8 · 0 gán-sai-nhóm.
  Vá dọc đường: JSON-comma phantom (hai-kênh) · F-27 (bỏ neo chữ "OTP") · F-26 (nhãn-sau-scrub).
- **5a (cảm xúc) contract v2.4.0 ĐÃ KÝ Câu 1+2** (ADR-022): thread_signals + emotion_signals dựng xong.
- **F-25(b) cổng siết-nhầm** (0-TPM, đã chứng minh hoạt động, chờ lượt "sau" chạy thật).

## Đang dở — chi tiết đủ tiếp ngay
- **Lượt đo end-to-end "sau" O1-O4** — PO thật ĐÃ DUYỆT (1 lượt). Chạy trên version-freeze coder chốt,
  đóng dấu 2 đầu. MỘT lượt trả BỐN câu: cổng-96 · siết-nhầm 18-ca+🔇 · timeout-vs-recursion · F-25(b).
- **field `note`** — PO-5 ĐÃ DUYỆT (che-lúc-ghi/giữ-4-số/không-commit-transcript) → coder implement,
  mở khoá 13-14 test note + CI security-gate.
- **Team follow-up** (additive, không chặn): O2-anchors + filler-word Luật 18 (retroactive F-24/F-27) ·
  đợt nâng CỔNG-A gộp 3 oracle (số-ngắn+tên+phủ-định) theo xuất-xứ + dữ liệu phân phối · chip câu 3 (chờ PO).

## Chặn / chờ PO THẬT (cập nhật theo quyết định phiên này)
- **#4 chip câu 3** — PO đang cân (đã xin giải thích): khung "chip vận-hành mức hội-thoại, KHÔNG nhãn
  trạng-thái-tâm-lý" + ngưỡng N=3. Đặc tả: `docs/giao-viec/2026-08-15-spec-cau3-dau-hieu-cam-xuc-cskh.md`.
- **#5 ADR-020 maker-checker** — PO đang cân (đã xin giải thích): ký để chuyển "Dự thảo"→hiệu lực.
- **PO-1 xong** (key đã xoay). **PO-2**: PO đang đặt OPENAI_API_KEY secret (đã có hướng dẫn).
- **Hướng 150 người**: CHƯA cho vào test (PO chốt) — chờ lượt end-to-end + cân nâng tier TPM.

## Cảnh báo còn tồn
- **gate-96 (chặn-nhầm reply thật) đang TẮT có tài liệu** — bật cùng lượt end-to-end (payload chỉ có sau
  lượt chạy thật). Không phải nợ kỹ thuật, là ràng buộc lịch.
- **Mốc nền đối kháng chốt VĨNH VIỄN 18/20** (he_thong 6c5fff420bb9); 18 ca MÙ với siết-nhầm → "18/18→18/18"
  là chốt-chặn-hồi-quy MỘT NỬA, nửa kia đo bằng 🔇 + F-25(b). MT-A01/F-01 không quay lại nhánh "trước" được.
- CI: note-tests (chờ note land) · 2 eval (chờ PO-2 secret) · CI-4/5 route-guards-docker chưa nghiệm thu.
- **[c] oracle-phủ-định "không phải 21"** còn lọt (1 bit/lượt, có tài liệu) → đợt cổng-A.

## Việc kế tiếp
1. PO chốt #4 (chip) + #5 (ADR-020) — hai cái đang chờ giải thích.
2. Coder: note field (PO-5) + O2-anchors/filler-word; báo tester version-freeze cho lượt end-to-end.
3. Tester: chạy lượt end-to-end (4 câu) khi coder chốt freeze; báo số cho PO quyết hướng 150 người.

## Hoãn có chủ đích
- Hạ tầng đo temp=0/k≥3 (gói B2 HOLD, floor nhiễu 20/40) · reseed gộp (⚠️ gỡ lọc-A1 khi from_bank sửa) ·
  401/403 hai route OTP · B3 timezone (31 utcnow) · lộ trình EU/US G1(SLA)/G3(audit bất biến) — xem PO-TONG-KET.
