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
> **AI-log (đo lại 15/08 tại P-226 — mục cũ ghi theo P-121, KHÔNG đúng cho repo này):**
> Lớp THU log chạy tốt (`.ai-log/session.jsonl`). Nhưng lớp GỬI cần ba thứ, **hook không đi
> theo git nên migration làm mất hai thứ đầu**:
> 1. `.git/hooks/pre-push` — P-226 ban đầu KHÔNG có (chỉ còn `.sample`); cài bằng
>    `bash scripts/setup_hooks.sh`. Hook là file local, migration `.git` mới là mất.
> 2. `.env` với `AI_LOG_SERVER` + `AI_LOG_API_KEY` — P-226 ban đầu KHÔNG có `.env`.
>    Thiếu → `submit_log.py` in "AI_LOG_SERVER not set" rồi `exit 0` **im lặng**, push vẫn xanh.
> 3. `SSL_CERT_FILE` — **thiếu thì trượt `CERTIFICATE_VERIFY_FAILED`** (đo thật lúc push
>    `954a6a9`). ⚠️ **Phải ghi ĐƯỜNG DẪN THẬT** (`.../certifi/cacert.pem`, lấy bằng
>    `python3 -c "import certifi; print(certifi.where())"`) — dạng `$(python -m certifi)` mà
>    bản STATE trước ghi là **SAI**: `python-dotenv` không chạy command substitution, nó đọc
>    nguyên văn chuỗi `$(...)` thành đường dẫn rác.
>
> **AI log KHÔNG đi qua commit** — `.gitignore:74-75` loại `.ai-log/*.jsonl`; log được POST
> lên grading server bởi pre-push hook, tức lúc **`git push`**, không phải `git commit`.
> Trượt submit KHÔNG chặn push (`exit 0` cuối hook) và log được giữ lại nguyên vẹn (đường
> `_restore_pending` đã verify thật: 0 dòng mất sau lần trượt SSL).
>
> **TRẠNG THÁI ĐO ĐƯỢC 15/08 — mắt xích cuối còn ĐỎ là KEY.** Sau khi vá SSL, push `3f59e3e`
> trả **`HTTP 401 Unauthorized`**: mạng/TLS/server đều thông, chỉ `AI_LOG_API_KEY` bị từ chối
> (key cũ chưa thay, hoặc là placeholder chép từ `.env.example` chứ không phải key cá nhân từ
> link mời BTC — hai khả năng cho cùng một 401). **Chưa từng submit thành công từ P-226.**
> `LANGCHAIN_*` KHÔNG liên quan: `submit_log.py:28-30` chỉ đọc `AI_LOG_SERVER` ·
> `AI_LOG_API_KEY` · `AI_LOG_DIR` — xoá/thêm key LangChain không đổi gì ở đường này.
>
> ⚠️ **Hỏng IM LẶNG — đừng lấy "push xanh" làm bằng chứng.** Hook `exit 0` nên push luôn
> thành công dù submit trượt; dòng `[ai-log] Submit failed` lẫn giữa output git. **Bằng chứng
> khách quan DUY NHẤT là `.ai-log/archive/`** — `_archive()` chỉ chạy SAU khi POST thành công,
> nên thư mục đó tồn tại ⟺ đã gửi được thật. Hiện chưa có.
>
> AI_LOG_API_KEY + LANGCHAIN keys ĐANG được tạo lại (key cũ 401). **9133 dòng backlog nằm ở
> P-121-new/.ai-log — submit từ P-121 khi có key mới, ĐỪNG xoá P-121-new tới khi submit xong**
> (deliverable #4). Liệu lịch: `submit_log.py` có `BATCH_LIMIT=500`/lần push ⟹ backlog đó cần
> **~19 lượt push**, không phải một phát xong.
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
- **5a (cảm xúc) contract v2.4.0/v2.5.0 ĐÃ KÝ TOÀN BỘ Câu 1+2+3** (ADR-022): thread_signals +
  emotion_signals dựng xong. **Câu 3 (chip câu CSKH) PO thật duyệt 15/08**: khung "chip vận-hành
  mức hội-thoại, KHÔNG nhãn tâm-lý" + N=3 (cùng ngưỡng nút-khách) + **CSKH thấy chip** — xem
  `docs/giao-viec/2026-08-15-spec-cau3-dau-hieu-cam-xuc-cskh.md`. CHƯA CODE (xếp sau 5a core).
- **F-25(b) cổng siết-nhầm** (0-TPM, đã chứng minh hoạt động).
- **Luật 18 (ADR-023)** — khớp cụm cho phép chèn hư từ + mỏ neo QUY TRÌNH cho O2 — LAND
  (`221abb5`, `8d26548`), retroactive F-24/F-27.
- **`resolutions.note` + `note_flagged` (ADR-024)** — LAND (`7b68992`), field ẩn duy nhất nơi
  văn bản tự do nhân viên gõ đi vào bản ghi kiểm toán; scrub tại điểm ghi, fail-closed, ép ở DB.
- **Lượt đo end-to-end "sau" O1-O4 ĐÃ CHẠY** (`e4ef0e8`) — sửa bug 21/24 ở câu 2, **cổng-96 giờ
  BẬT THẬT** (không còn tắt), raw lượt end-to-end đã lưu.
- **Seed test USR-0119/USR-0201 xong** (`dacbefd`, tester) — lộ + vá 2 bug ẩn: TXN-0001 không
  "mượn" được cho user mới (đã parametrize `trans_id`), import sai module
  (`src.tools.registry`→`src.agents.tools.customer_tools`), guard cổng-96 kiểm nhầm payload
  toàn cục thay vì đúng tập mốc nền đang dùng.
- **Xác nhận trạng thái THẬT trong phiên này (Luật 9, 2026-08-15, PO-agent dựng venv sạch chạy
  từ đầu — không suy luận từ code tĩnh):**
  - `pytest tests/test_invariants.py -v` → **23/23 PASSED**, 0 failed.
  - `pytest tests/test_api/test_reject_note_doi_khang.py tests/test_migrations/test_trang_thai_dich_nhip_note_f11_f13.py`
    → **15 passed, 8 skipped** (0 failed) — skip có lý do rõ: 7 ca cần Postgres thật (env test
    dùng `sqlite:///:memory:`), 1 ca chờ exporter Phase 2 chưa tồn tại. KHÔNG có `khong_do_duoc`
    lạ nào.
  - `pytest tests/test_security/ -q` → **38 passed, 26 skipped**, 0 failed.
  - Môi trường test cục bộ trước đó CHƯA từng được dựng ở máy chạy phiên PO-agent (thiếu
    `argon2`, thiếu model NER `xx_ent_wiki_sm` của presidio) — đã dựng venv scratchpad + cài đủ,
    không phải bug sản phẩm.

## Đang dở — chi tiết đủ tiếp ngay
- **Chip câu 3 (dấu cho CSKH)** — PO thật đã duyệt khung+N=3+CSKH-thấy (xem "Vừa xong"). CHƯA CODE:
  coder xếp SAU 5a core + sau QA baseline (thứ tự đã định từ sổ Đợt 2). Câu hỏi kỹ thuật còn treo
  (không cần PO quyết lại, coder tự đề xuất): cần thêm 1 trường envelope riêng cho kênh CSKH, hay
  tái dùng cờ ES sẵn có mà khách cũng đọc — xem đặc tả §4.
- **Đợt nâng CỔNG-A** gộp 3 oracle (số-ngắn+tên+phủ-định "không phải 21") theo xuất-xứ + dữ liệu
  phân phối — chưa làm, có tài liệu ở sổ Đợt 2.
- **Câu-4 RAG retrieval quality** — 3/5 câu chính sách hợp lệ agent không trả được. Sửa chunk/embedding,
  KHÔNG nới ràng buộc 9. Mốc: trước pilot 150 người.
- **MT-E02 traceback** — cơ chế chưa rõ, giữ quan sát, ĐỪNG đốt TPM tái hiện chủ động.

## Chặn / chờ PO THẬT — RÚT GỌN 15/08 (chip câu 3 + ADR-020 ĐÃ CHỐT, xem "Vừa xong")
- **Hướng đợt 150 người** — DUY NHẤT việc PO thật còn treo. Số end-to-end đã có để quyết: bộ lọc
  17/17 không siết nhầm, RAG retrieval là điểm yếu; 4 góc chưa-sẵn-sàng: TPM · 429→500 · timeout ·
  RAG (chi tiết ở sổ Đợt 2, mục "429 SẢN PHẨM" + "TIMEOUT trên câu phổ biến nhất").
- **PO-1 xong** (key đã xoay). **PO-2**: keys đang tạo lại — AI_LOG_API_KEY + LANGCHAIN keys (key cũ
  401), OPENAI_API_KEY secret PO đang đặt (đã có hướng dẫn). 9118 dòng backlog AI-log ở
  P-121-new/.ai-log chờ submit khi có key mới — ĐỪNG xoá P-121-new tới khi submit xong.

## Cảnh báo còn tồn
- **gate-96 giờ BẬT THẬT** (`e4ef0e8`, không còn tắt — mục trên đã lỗi thời, sửa 15/08).
- **Mốc nền đối kháng chốt VĨNH VIỄN 18/20** (he_thong 6c5fff420bb9); 18 ca MÙ với siết-nhầm → "18/18→18/18"
  là chốt-chặn-hồi-quy MỘT NỬA, nửa kia đo bằng 🔇 + F-25(b). MT-A01/F-01 không quay lại nhánh "trước" được.
- CI: note-tests giờ có thể chạy (land rồi, cần xác nhận CI xanh ở lượt push kế tiếp) · 2 eval (chờ PO-2
  secret) · CI-4/5 route-guards-docker chưa nghiệm thu.
- **[c] oracle-phủ-định "không phải 21"** còn lọt (1 bit/lượt, có tài liệu) → đợt cổng-A (vẫn treo).
- Môi trường test cục bộ (máy PO-agent) thiếu sẵn `argon2` + model NER `xx_ent_wiki_sm` — không phải bug,
  chỉ là máy này chưa từng dựng venv cho repo (dùng venv scratchpad tạm, không commit).

## Việc kế tiếp
1. PO chốt hướng đợt 150 người (số end-to-end đã có, xem "Chặn / chờ PO THẬT").
2. Coder: chip câu 3 (khi tới lượt, sau 5a core + QA baseline) · đợt cổng-A gộp 3 oracle · câu-4 RAG
   retrieval quality (chunk/embedding, trước pilot 150 người).
3. Xác nhận CI xanh ở lượt push kế tiếp (note-tests giờ chạy được, chưa quan sát trên CI thật).

## Hoãn có chủ đích
- Hạ tầng đo temp=0/k≥3 (gói B2 HOLD, floor nhiễu 20/40) · reseed gộp (⚠️ gỡ lọc-A1 khi from_bank sửa) ·
  401/403 hai route OTP · B3 timezone (31 utcnow) · lộ trình EU/US G1(SLA)/G3(audit bất biến) — xem PO-TONG-KET.
