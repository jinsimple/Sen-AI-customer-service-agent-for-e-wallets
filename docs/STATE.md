# Trạng thái hiện tại
Cập nhật: **2026-08-15 (phiên Đợt 2 + bàn giao P-226)** · PO-agent điều phối 4 vai (Claude Code)

## 🔄 BÀN GIAO SANG P-226 — ĐỌC ĐẦU TIÊN
> **Repo đã migrate từ P-121 → P-226 (đầy đủ lịch sử).** Nhánh làm việc: `dev/learning-loop`
> (HEAD dacbefd, 256 commit). `main` = 104 commit. Đang code trong thư mục `P-226`.
>
> **Bối cảnh dự án:** FIN-05 — AI Agent CSKH ví điện tử xử lý khiếu nại, chuẩn fintech EU/US.
> Đội = 4 phiên Claude Code (PO-agent điều phối · coder/tech-lead · tester · security), đồng bộ
> qua **git + cross-session message** (SendMessage/ListAgents), mỗi vai chỉ ghi vùng của mình (§4).
> ⚠️ **CÂY LÀM VIỆC DÙNG CHUNG giữa 4 phiên** → mọi `git stash/commit/checkout/clean` **phải kèm
> pathspec vùng của mình**. Lệnh không pathspec sẽ cuốn theo việc đang dở của vai khác.
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
> **✅ ĐƯỜNG AI-LOG P-226 ĐÃ THÔNG — verify thật 15/08, push `eadcca7`:**
> `[ai-log] Submitted 73 entries → 202` · `.ai-log/archive/2026-08-15.jsonl` sinh ra với đúng
> 73 bản ghi, parse JSON 73/73 hỏng 0, metadata đúng (`repo=P-226` · `branch=dev/learning-loop`
> · `student=jin.simple@gmail.com`).
>
> **Chuỗi chẩn đoán 4 lượt push (giữ lại vì mỗi nấc hỏng cho một triệu chứng KHÁC nhau):**
> `954a6a9` CERTIFICATE_VERIFY_FAILED (thiếu SSL_CERT_FILE) → `3f59e3e` **401** (SSL thông) →
> `e6e5f7b` 401 (không đổi vì key chưa thay) → `eadcca7` **202 ✅** (key mới `ai20…` 38 ký tự,
> lấy từ link mời BTC; key cũ `f3p1…` 64 ký tự chép sang từ P-121 là key ĐÃ THU HỒI).
> `LANGCHAIN_*` KHÔNG liên quan tới đường này: `submit_log.py:28-30` chỉ đọc `AI_LOG_SERVER` ·
> `AI_LOG_API_KEY` · `AI_LOG_DIR`.
>
> ⚠️ **Hỏng IM LẶNG — đừng lấy "push xanh" làm bằng chứng.** Hook `exit 0` nên push luôn
> thành công dù submit trượt; dòng `[ai-log] Submit failed` lẫn giữa output git. **Bằng chứng
> khách quan DUY NHẤT là `.ai-log/archive/`** — chỉ sinh ra SAU khi POST thành công.
> `session.jsonl` BIẾN MẤT sau lần gửi được là ĐÚNG THIẾT KẾ (atomic rename), hook tạo lại ở
> lượt ghi kế tiếp — đừng tưởng mất log.
>
> **AI_LOG_API_KEY mới đã hoạt động ở P-226.** LANGCHAIN tạm TẮT có chủ đích
> (`LANGCHAIN_TRACING_V2=false`, key rỗng) — PO quyết gác lại, không chặn gì.
>
> **CÒN TREO — backlog P-121: 9133 dòng ở `P-121-new/.ai-log`.** Phải **thay key mới vào
> `P-121-new/.env` nữa** (nơi đó vẫn là key `f3p1…` đã thu hồi) rồi push từ P-121.
> **ĐỪNG xoá P-121-new tới khi submit xong** (deliverable #4). Liệu lịch: `BATCH_LIMIT=500`
> mỗi lần push ⟹ cần **~19 lượt push**, không phải một phát xong.
> ⚠️ Nhánh leftover của `_archive_entries()` (vá ở `eadcca7`) **CHƯA từng chạy thật** — lượt
> 15/08 chỉ có 73 bản ghi, dưới ngưỡng 500 nên không sinh leftover. Backlog P-121 sẽ là lần
> ĐẦU TIÊN nhánh đó chạy; kiểm `wc -l .ai-log/archive/*.jsonl` sau 2 lượt push đầu để chắc
> archive không phình trùng lặp.
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

## 🔴 HAI FINDING MỚI 15/08 (chiều) — cần PO thật, ghi đầu vì cả hai chặn kết luận đang có

### F-CI — CI ở P-226 CHƯA TỪNG CHẠY MỘT JOB NÀO (tester `p-226-c8` đo bằng `gh run list`)
13/13 lượt chạy trên `dev/learning-loop` đều `failure` sau **4-5 giây**, annotation nguyên văn:
> *"The job was not started because recent account payments have failed or your spending limit
> needs to be increased. Please check the 'Billing & plans' section"*

**Không phải test đỏ, không phải config sai — ZERO job khởi động.** Hai lượt `success` duy nhất
trong lịch sử repo là "Initial commit" 26/07 (22s/27s, trước khi có bộ test thật).
⟹ **Toàn bộ Đợt 2 ở P-226 chạy với 0 lượt CI có hiệu lực.** Mọi câu "CI xanh chưa" vô nghĩa tới
khi thông. **VIỆC PO THẬT (không phiên Claude nào làm được): Billing & plans của org
`AI20K-Build-Phase-Cohort-3`.** Hệ quả: CI-1/CI-4/CI-5 (`tests/TIEU-CHI-CI.md`) không nghiệm thu
được; CI-1 đã nối dây đúng cho `dev/**` nhưng **chưa bao giờ chứng minh được có hiệu lực**.
Đây là "hiện diện ≠ hiệu lực" ở tầng HẠ TẦNG: `ci.yml` đủ 13 job, trigger đúng, mọi push đều
sinh một lượt chạy — và **không byte code nào từng được kiểm**.

### F-NOTE — `note` scrub CHẶN NHẦM 40%, xoá đúng CĂN CỨ TỪ CHỐI (security `p-226-0f` đo, 0 TPM)
Che PII **ĐẠT** (12/12 ca có PII đều bị che; bộ đối kháng 15 passed/1 skipped). **NHƯNG 8/20 ghi
chú CSKH KHÔNG có một mẩu PII nào vẫn bị đục**, NER gán nhầm cụm nghiệp vụ tiếng Việt:
- *"…từ chối theo chính sách."* → *"…từ chối **[PERSON]**"*
- *"Khách đã rút khiếu nại qua tổng đài, không cần xử lý tiếp."* → *"**[LOCATION]** … không **[PERSON]**"*

**KHÔNG phải "đánh đổi đã chốt".** ADR-024 chấp nhận che-nhầm với tiền đề ĐO ĐƯỢC là *mã 12 số
trùng pattern CCCD* (`test_03`). Lớp vừa đo là **cụm nghiệp vụ thuần bị NER gán [PERSON]** —
tiền đề đó **CHƯA TỪNG ĐO** ⟹ đúng **Luật 8** (đo lại GIAO của các quyết định), họ hàng F-25
(xoá trắng chính sách thật), lần này rơi vào **BẢN GHI KIỂM TOÁN**: supervisor đọc `note` để hiểu
vì sao từ chối, mà bản ghi hỏng nghĩa **TRONG IM LẶNG**.
Gốc: `scrub_pii` docstring tự khai dùng cho **log/span attribute** — mất một chữ trong log thì
không sao; ADR-024 tái dùng nó cho **record có giá trị pháp lý** = đổi hạng mục sử dụng.
⟹ **CHƯA BẬT CI security-gate cho `note`** (bật = đóng dấu xanh lên hành vi làm hỏng audit trail).
Bản vá đụng tiền đề ADR-024 → phải qua PO thật, coder ĐỪNG vá vội. Hồ sơ: `docs/security/`.
**Đính chính mục "Vừa xong" bên trên:** `note` đủ về **BẢO MẬT**, KHÔNG đủ về **TOÀN VẸN BẢN GHI**.

## Cảnh báo còn tồn
- **gate-96 giờ BẬT THẬT** (`e4ef0e8`, không còn tắt — mục trên đã lỗi thời, sửa 15/08).
- **Số end-to-end gắn với hệ thống KHÔNG CÒN TỒN TẠI** (tester đo): lượt "sau" chạy ở
  `he_thong 6096dc8b5678` (commit `8d26548`); cây hiện tại `fd16681d8088` vì `7b68992` (note) land
  sau đó. ⟹ hai số **HÀNH VI** (câu 2: 17/17 · câu 4: 2/5) gắn hệ thống đã mất; hai số **DỮ LIỆU**
  (câu 1 cổng-96 · câu 3 fallback) mua vĩnh viễn. Trích cho quyết định 150 người thì trích được
  cả bốn, **chỉ cần ghi rõ nhãn**.
- **Cửa sổ đóng băng đang MỞ:** security (`p-226-0f`) giữ `src/` BẤT ĐỘNG tới khi họ nhắn
  "MỞ TAY src/" (dấu `he_thong=fd16681d8088` · `cham_diem=c0b79835e16c` · commit `2e8c888`).
  `docs/`/`tests/`/`contracts/`/`scripts/` KHÔNG nằm trong dấu → sửa được bình thường.
- **Mốc nền đối kháng chốt VĨNH VIỄN 18/20** (he_thong 6c5fff420bb9); 18 ca MÙ với siết-nhầm → "18/18→18/18"
  là chốt-chặn-hồi-quy MỘT NỬA, nửa kia đo bằng 🔇 + F-25(b). MT-A01/F-01 không quay lại nhánh "trước" được.
- CI: **TẤT CẢ đều treo sau F-CI (billing), không phải "chưa làm"** — note-tests đã land và xanh ở
  MÁY (15 passed), thiếu đúng phần quan sát trên runner · 2 eval chờ PO-2 secret · CI-4/5 chưa
  nghiệm thu. Không mục nào tiến được tới khi billing thông.
- **[c] oracle-phủ-định "không phải 21"** còn lọt (1 bit/lượt, có tài liệu) → đợt cổng-A (vẫn treo).
- Môi trường test cục bộ (máy PO-agent) thiếu sẵn `argon2` + model NER `xx_ent_wiki_sm` — không phải bug,
  chỉ là máy này chưa từng dựng venv cho repo (dùng venv scratchpad tạm, không commit).

## Việc kế tiếp
1. **PO THẬT — billing org `AI20K-Build-Phase-Cohort-3`** (F-CI). Chặn mọi nghiệm thu CI.
2. **PO THẬT — quyết hướng vá F-NOTE**: scrub cho bản ghi kiểm toán khác scrub cho log. Đụng tiền
   đề ADR-024 nên cần quyết định minh thị, không để coder tự vá.
3. PO chốt hướng đợt 150 người (số end-to-end đã có, nhớ ghi nhãn hành-vi/dữ-liệu ở "Cảnh báo").
4. Coder: chờ security "MỞ TAY src/" rồi mới chạm. Xếp hàng: chip câu 3 (sau 5a core + QA baseline)
   · đợt cổng-A gộp 3 oracle · câu-4 RAG retrieval (chunk/embedding, trước pilot 150 người).
5. **PO-2**: đặt `OPENAI_API_KEY` thành secret trên GitHub → mở 2 CI eval (chỉ có tác dụng SAU khi
   billing thông).

## Hoãn có chủ đích
- Hạ tầng đo temp=0/k≥3 (gói B2 HOLD, floor nhiễu 20/40) · reseed gộp (⚠️ gỡ lọc-A1 khi from_bank sửa) ·
  401/403 hai route OTP · B3 timezone (31 utcnow) · lộ trình EU/US G1(SLA)/G3(audit bất biến) — xem PO-TONG-KET.
