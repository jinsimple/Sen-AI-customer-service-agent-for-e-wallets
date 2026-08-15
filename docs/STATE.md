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

## ⚡ BA QUYẾT ĐỊNH PO THẬT — chiều tối 15/08 (mới nhất, đè các mục cũ bên dưới)
1. **Billing/CI:** PO thật KHÔNG phải owner org — chỉ BTC sửa được. ⟹ gửi BTC/mentor tin nhắn kèm
   annotation nguyên văn (PO-agent đã soạn, xem cuối STATE). Trong lúc chờ: tester đã chạy đủ lệnh
   từng job trên host (446 passed/0 failed) — **công việc hằng ngày KHÔNG bị chặn**, chỉ thiếu
   bằng chứng trên runner + badge (deliverable). F-CI-2 đã vá sẵn đón ngày billing thông.
2. **ADR-025: NGUYÊN TẮC ĐÃ DUYỆT** ("chốt theo hướng security"). PO thật uỷ quyền PO-agent research
   chuẩn EU/US cho 3 chỗ trống → **dự thảo ADR-025 ĐÃ VIẾT** vào `docs/DECISIONS.md` với đề xuất:
   retention **5 năm** (max của VN-PCRT-5n/EU-AMLD-5n/US-RegE-2n-sàn, cờ: cần tư vấn pháp lý thật
   trước production) · đọc transcript theo **NGƯỜI PHỤ TRÁCH** + supervisor có audit-log (GDPR 25/32
   · PCI DSS Req 7 · ISO 27001 · SOC 2) · fail-visible = **preview-confirm** (nhân viên thấy bản đã
   che, xác nhận trước khi ghi; engine lỗi vẫn fail-closed 500 giữ ADR-024). Con số chờ PO xác nhận
   nhanh rồi coder mới chạm contract/code phần B + A3/A4.
3. **PILOT 150 NGƯỜI: HOÃN** — PO thật chốt: chỉ mở khi (a) tối ưu **caching** xong và (b) chatbot
   **tự học/tự nâng cấp** được (learning loop Phase 2). ⟹ các mục "trước pilot" (F-29, A1/A2, RAG,
   TPM) **giãn deadline nhưng KHÔNG huỷ** — F-29/A1/A2 rẻ nên vẫn làm ngay trong lô hiện tại. Hai
   cam kết của security (dữ liệu thật + đường xoá) ghi lại cho thời điểm pilot thật.

## Chặn / chờ PO THẬT — RÚT GỌN 15/08 (chip câu 3 + ADR-020 ĐÃ CHỐT, xem "Vừa xong")
- **Hướng đợt 150 người.** Số end-to-end đã có: bộ lọc 17/17 không siết nhầm, RAG retrieval là
  điểm yếu; 4 góc chưa-sẵn-sàng: TPM · 429→500 · timeout · RAG (sổ Đợt 2, mục "429 SẢN PHẨM" +
  "TIMEOUT trên câu phổ biến nhất").
  **➕ Ý KIẾN BẢO MẬT VỀ PILOT (security, kết sổ `80b217a`) — đọc trước khi quyết:**
  > Bốn cửa **KHÔNG chặn pilot về mặt bảo mật**. Thứ **thật sự cần trước pilot** là **A1 + A2** —
  > rẻ, không cần quyết cơ chế, đóng đúng phần *"lưu plaintext vĩnh viễn"*. Phần còn lại
  > (B1/B2, A3, A4) là **nợ đúng hạn, không phải nợ gấp**.

  🔴 **SECURITY KHÔNG CẤP PHÉP CHO PILOT — họ nói bốn cửa KHÔNG PHẢI THỨ CHẶN nó.** Hai chuyện
  khác nhau, và security nhắc lại lần hai để nó không mòn đi qua vài tay. Kèm **hai ràng buộc mà
  PO PHẢI CAM KẾT**, không phải bảo mật cấp:
  1. **Dữ liệu pilot được coi là DỮ LIỆU THẬT** — chịu NĐ 13/2023 như dữ liệu khách thật, **không
     phải** *"dữ liệu demo nên thoải mái"*.
  2. **Có ĐƯỜNG XOÁ sau đợt** — **có người chịu trách nhiệm, có mốc thời gian**, không phải *"tính sau"*.

  **Thiếu một trong hai thì ý kiến của security ĐỔI.**

  ⚠️ **Phạm vi:** bốn cửa không chặn pilot **VỀ MẶT BẢO MẬT**. Bốn góc chưa-sẵn-sàng còn lại
  (**TPM · 429→500 · timeout · RAG retrieval**) **KHÔNG thuộc phạm vi security đánh giá** và
  **không được cộng gộp** vào câu trên.
  ⚠️ Và **bốn cửa không phải một khối** — chúng có **hạng khác nhau**; trộn lại sẽ khiến **A1/A2
  (rẻ, đáng làm ngay) bị kẹt sau A3/A4** (đụng vận hành CSKH, cần PO).
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

**Tester đã chạy TRƯỚC đúng lệnh của từng job trên host** (Python 3.14 vs CI 3.12 — ghi rõ để
không đọc thành chắc chắn), HEAD `2e8c888`, để khi runner sống lại thì tách sẵn "đỏ vì billing"
khỏi "đỏ vì code":

| Job | Lệnh CI | Host |
|---|---|---|
| `invariants` | `pytest tests/test_invariants.py` | 23 passed ✅ |
| contract drift | `check_contracts.py` | 3/3 khớp ✅ |
| `lint-and-test` | `pytest tests/ -m "not security_finding"` | **446 passed · 41 skipped · 0 failed** ✅ |
| `security-findings-gate` | `pytest tests/ -m security_finding` | 1 failed — ĐỎ ĐÚNG CHỦ ĐÍCH |
| `appsec` | `pytest tests/test_api/` | **1 failed** · 227 passed 🔴 |

**🔴 F-CI-2 — job `appsec` sẽ đỏ vì LÝ DO SAI ngay khi billing thông.** `appsec` chạy
`pytest tests/test_api/ -v` **thiếu `-m "not security_finding"`** mà `lint-and-test` có ⟹ nó bắt
luôn `test_live_chat_pii_gap.py::…_is_not_masked_before_storage` = **ST2-P0-3**, finding P0 duy
nhất còn lại (3 P0 kia đã vá đợt Auth5). `security-findings-gate` đỏ là ĐÚNG THIẾT KẾ; `appsec`
đỏ là SAI. Vi phạm chiều hai của `tests/TIEU-CHI-CI.md`: *"cổng đỏ vì lý do sai còn tệ hơn không
có cổng — nó dạy cả đội bỏ qua chính cảnh báo đó"*. **Nguy hơn thường lệ vì nó nổ ĐÚNG LÚC billing
vừa thông**, lúc cả đội đang mong thấy xanh và dễ tặc lưỡi nhất. Vá = **một dòng `ci.yml`** (vùng
coder). Tester đã ghi tiêu chí **CI-10** + 2 phép thử vào `tests/TIEU-CHI-CI.md`.

**🟡 F-CI-3 — hai test tier-split TỰ SKIP BẰNG ĐOÁN TÊN HÀM.** Trong 41 skip, 38 có lý do chính
đáng. Còn `test_mau_tier1_chi_thi.py` + `test_f24_recall_tier1.py` skip với *"F-22 CHƯA SHIP"* —
chúng thử 4 cặp module/tên cho `phan_tier`, không thấy thì skip. Nhưng sổ Đợt 2 ghi F-22/F-24/F-25
đã chốt và ship. Tester **không phân biệt được vì không đọc `src/`** (§4): hoặc chưa ship thật
(skip trung thực), hoặc **đã ship DƯỚI TÊN KHÁC** ⟹ hai bộ skip vĩnh viễn trong khi cả đội tưởng
đang được canh. **Khả năng thứ hai ĐÃ XẢY RA một lần cùng đợt này**: `8d26548` — *"O2 mỏ neo tìm
đúng tên `dem_mat_do_liet_ke`, 7 ca hết SKIP"*. **Coder chỉ cần trả lời một dòng: tên hàm thật.**
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
Bản vá đụng tiền đề ADR-024 → phải qua PO thật, coder ĐỪNG vá vội.
**Hồ sơ đầy đủ (23KB, §0-§8): `docs/security/2026-08-15-ra-soat-cuoi-sprint-note-scrub-va-pipeline.md`** (`c2c2d06`).
**Đính chính mục "Vừa xong" bên trên:** `note` đủ về **BẢO MẬT**, KHÔNG đủ về **TOÀN VẸN BẢN GHI**.

### 🔴 S-02 (CAO) — tiền đề "chỗ DUY NHẤT" của ADR-024 BỊ BÁC: `InvestigationLog.agent_note`
Route `POST /tickets/{id}/request-more-info` ghi thẳng `req.note` → `agent_note`: **không scrub,
không trần độ dài, không cờ tier**. Probe HÀNH VI (gọi route thật + đọc thẳng DB, không grep tên):
PAN 16 số `9704123456789012` · CCCD · SĐT · tên đều nằm **plaintext trong DB**; note **5.000 ký
tự** nhận trọn (bên `reject` chặn ở 500); payload injection lưu nguyên văn.
Không rò ra khách (3 đường đọc đều gated `cskh,supervisor`; node agent ghi `agent_note=None` nên
không vào LLM). Nhưng hở **NĐ 13/2023** — và `EncryptedText` ĐÃ được áp cho chat content
(`models.py:475`) lẫn RAG (`:513`), nên `agent_note` **chỉ đơn giản bị BỎ SÓT, không phải một
quyết định**. Cộng hở **phễu học Phase 2**: `test_14` cắm cọc cấm `note` ra file ứng viên, **không
có cọc nào cho `agent_note`** — trong khi `investigation_logs` mới là thứ tự nhiên nhất để xuất
làm dữ liệu học.
⚠️ **S-01 và S-02 PHẢI SỬA CÙNG MỘT QUYẾT ĐỊNH** — bê nguyên `scrub_pii` sang cửa thứ hai là
**nhân bản lỗi chặn-nhầm 40% sang trường thứ hai**.

### 🔴🔴 PHẠM VI THẬT LÀ **BỐN CỬA**, KHÔNG PHẢI HAI — đây là quyết định lớn nhất đang chờ PO
Security rà tiếp (`eff47ac`) và mở rộng §8.3 từ 2 lên **4** cửa văn bản tự do:

**CẢ BỐN Ô NAY ĐO BẰNG HÀNH VI TRONG PHIÊN** (`b7e4230` + `eb444eb`) — hai ô phải bổ sung sau:
`description_raw` (security tự thấy không ổn khi nó sắp thành căn cứ quyết ADR-025) và
`messages.content` (PO-agent xin đo, lý do: nhóm A là nơi security khuyến nghị **BÁC** một cơ chế,
mà **bác = để nguyên hiện trạng hở** ⟹ cần số chắc hơn khuyến nghị áp; nếu hiện trạng đã trôi thì
đang bác dựa trên trạng thái không còn đúng). **Kết quả: hiện trạng KHÔNG trôi ⟹ khuyến nghị §2
đứng nguyên** (không scrub · 4/4 PII còn nguyên sau giải mã · 20.000 ký tự · không cờ · injection
nguyên văn). Bảng nay có **4 chiều**:

| Cửa | Ai gõ | Scrub | Trần độ dài | Cờ tier | Mã hoá at-rest |
|---|---|---|---|---|---|
| `messages.content` (live-chat) | khách + CSKH | ❌ | ❌ | ❌ | ✅ `EncryptedText` |
| `complaints.description_raw` | khách | ❌ | ❌ **20.000 ký tự nhận trọn** | ❌ | ❌ **`Text` thuần** |
| `resolutions.note` | nhân viên | ✅ **nhưng hỏng nghĩa 40%** (S-01) | ✅ 500 | ✅ | ❌ |
| `investigation_logs.agent_note` | nhân viên | ❌ | ❌ | ❌ | ❌ (S-02) |

**Hai điểm mới, quyết định cách xếp thứ tự trong ADR-025:**
1. `description_raw` chứa **PII BÊN THỨ BA ngay ở ca dùng điển hình nhất** — *"em chuyển nhầm cho
   anh X, sđt…"*. Người đó **không phải khách hàng**, không có cơ sở pháp lý để lưu. Đo: 5/5 mẩu
   PII còn nguyên văn (2 SĐT · STK · CCCD · **tên bên thứ ba**), injection lưu nguyên văn.
2. Nó là **cửa khách-tự-gõ DUY NHẤT không có mã hoá at-rest** (live-chat có `EncryptedText`, cửa
   này không).
⟹ Nếu PO định làm ADR-025 theo kiểu *"cửa nào gấp làm trước"* thì **`description_raw` KHÔNG phải
cửa nhẹ nhất như tên gọi gợi ý.**

### ✅ ĐIỂM SÁNG — `EncryptedText` KHÔNG chỉ được khai, nó CHẠY THẬT (kiểm bằng BYTE)
Security đọc **byte thô trong DB bằng SQL, vòng qua type decorator**:
```
'gAAAAABqgCRz6DpP1R2B9-N2Sg_Onanat4Bvpi7cdkfHq_vg6UnKiYmU0J9T40Z5quppnkJ8d…'
PII lộ plaintext? -> False        ⟹ mã hoá at-rest CÓ HIỆU LỰC
```
Đây là control **DUY NHẤT trong bốn cửa** được xác nhận bằng **HÀNH VI** thay vì bằng một dòng khai
báo kiểu — ba cửa kia mới chỉ đọc được dòng khai `Text`/`EncryptedText`, **chưa kiểm byte**.
📌 **Nhắc quan trọng: "hiện diện ≠ hiệu lực" áp cho cả thứ ĐANG CHẠY ĐÚNG, không riêng thứ hỏng.**
Ta quen dùng luật đó để bắt lỗi; đây là lần nó dùng để **xác nhận một thứ tốt là tốt thật**.

**Hai hệ quả cho ADR-025:**
1. **CỦNG CỐ lập luận BÁC che-lúc-ghi ở nhóm A.** Ở `messages.content` lớp bảo vệ at-rest **đã hoạt
   động** ⟹ đổi thêm **giá trị chứng cứ** để lấy một mức giảm thiểu nữa là **đánh đổi tồi**. Câu
   *"tại sao không che cho xong cho an toàn"* nay có thêm một vế trả lời: **vì lớp phòng vệ không
   phá gì đã chạy rồi.**
2. **NÂNG giá trị A1.** Mã hoá `description_raw` không phải "thêm một chuẩn mới trên giấy" — là kéo
   cửa yếu lên một chuẩn **đã chứng minh chạy được ở cửa bên cạnh**.

⚠️ **Mã hoá at-rest KHÔNG chạm tới lỗ đọc-theo-vai.** `messages.content` vẫn hở ST2-P0-3 §3: mọi
`cskh`/`supervisor` đọc được **mọi** transcript, không giới hạn theo ca phụ trách. At-rest chống
**mất đĩa/backup**, không chống **người đọc hợp lệ**. Đó là việc **A3** — cần PO quyết vì đụng vận
hành CSKH. Đừng đọc "mã hoá đã chạy" thành "cửa này đã an toàn".

### 🧭 MỘT NGUYÊN TẮC, **HAI CƠ CHẾ** — đọc TRƯỚC khi soạn ADR-025 (security `6f18c9d`)
Phương án + lý do bác cho từng cửa đã viết sẵn:
`docs/security/2026-08-15-co-che-cho-bon-cua-dau-vao-adr-025.md`.

**Nguy cơ lớn nhất của việc gộp bốn cửa vào một ADR là nó kết thành "áp scrub-lúc-ghi cho cả
bốn"** — và số đo nói điều đó **hỏng nặng nhất ở đúng hai cửa quan trọng nhất**. Đây là lý do
security viết phần cơ chế TRƯỚC bản dự thảo, không phải sau.

⚠️ **Đường phân chia KHÔNG phải "nhân viên gõ / khách gõ"** như bảng bốn cửa ở trên gợi ý —
security tự cảnh báo chính bảng của họ dễ dẫn người đọc đi sai. **Trục thật: bản ghi đó có phải
BẰNG CHỨNG không, và người gõ có SỬA LẠI ĐƯỢC không.**

**NHÓM A — `description_raw` + `messages.content` = LỜI KHAI CỦA KHÁCH.** Là căn cứ giải quyết
tranh chấp tiền bạc, và khách **không sửa lại được** (họ đã rời đi).
⟹ **BÁC che-lúc-ghi.** Ba cửa kia hỏng thì mất khả năng ĐỌC; cửa này hỏng thì **mất GIÁ TRỊ CHỨNG
CỨ** — một lời khai bị hệ thống sửa chữ **không đứng được** nếu khiếu nại đi xa hơn (NHNN, hoặc
toà). Cơ chế đúng: **mã hoá at-rest + trần + siết đọc theo NGƯỜI PHỤ TRÁCH (không theo vai) +
retention + che lúc XUẤT**. Chỗ xuất/log mới đúng hạng mục `scrub_pii` được viết ra — **vì bản gốc
vẫn còn**.

**NHÓM B — `note` + `agent_note` = ghi chú thao tác.** Nhân viên **đang ngồi trước màn hình**, sửa
lại được. ⟹ che-lúc-ghi **được**, nhưng phải **FAIL-VISIBLE** (xác nhận vòng tròn), **không im lặng**.

**Cắt lô:**
- **LÀM NGAY, KHÔNG cần PO quyết cơ chế** → nhập vào nhóm việc rẻ: **A1** mã hoá at-rest
  `description_raw` (chỉ là **bù cho ngang chuẩn dự án đã có** — live-chat có `EncryptedText`,
  cửa này không) · **A2** trần độ dài.
- **CẦN PO quyết**: **B1-vs-B2** (chế độ fail-visible) · **A3/A4** (siết đọc + retention — đụng
  vận hành CSKH, không thuần kỹ thuật).
- **SAU CÙNG**: **B3** (áp ba lớp cho `agent_note`) — **phải đi SAU B1/B2**; bê nguyên `scrub_pii`
  sang khi chưa sửa chế độ im lặng = **nhân bản lỗi 40% sang cửa thứ hai**.

**BA điều security ghi rõ là KHÔNG kết luận — giữ nguyên khi soạn ADR-025:**
1. **Không đề xuất con số retention** — đó là câu hỏi **pháp lý** (NĐ 13/2023 + thời hiệu khiếu nại
   TT 40/2024), có thể cần **tư vấn pháp lý thật**, không phải suy luận của security.
2. **Không kết luận nhóm A có cần scrub ở dạng nào** — nếu PO vẫn muốn thì phải đo trên corpus
   **LỜI KHAI THẬT**, ngưỡng **0 câu bị đổi nghĩa**.
3. **`messages.content` là cửa DUY NHẤT chưa probe hành vi trong phiên** (số dẫn từ ST2-P0-3 14/08
   + đọc `models.py`). Nếu ADR-025 quyết dựa trên nó → **nói một tiếng, security đo như đã đo ba
   cửa kia**.

§7 hồ sơ cũ đã cảnh báo *"chốt riêng lẻ sẽ tạo tình trạng che ô chat để hở ô mô tả, người soi bảo
mật tìm ra trong năm phút"* — nay quy mô **gấp đôi**, và một trong bốn cửa đã "được che" theo cách
**làm hỏng bản ghi**. ⟹ **S-01 + S-02 + ST2-P0-3 + `description_raw` là MỘT quyết định, không phải
bốn.** ADR-025 nên phủ **cả bốn cửa**, không riêng `note`.

### ⚠️ SECURITY TỰ BÁC ĐƠN THUỐC CŨ CỦA CHÍNH HỌ — đọc trước khi trả lời §8.2
Hồ sơ ST2-P0-3 §5.2 kê **"dùng `scrub_pii`, giữ 4 số cuối"** — đúng cái hàm hôm nay đo được chặn
nhầm 40%. Tin nhắn live-chat **chính là** văn bản tự do tiếng Việt, cùng loại đầu vào đã đo. Áp
nguyên văn sẽ mang lỗi vào **lời khách gõ cho CSKH**, và ở đó **hậu quả NẶNG HƠN `note`**: che tại
điểm GHI ⟹ **không còn bản gốc**, CSKH đọc một khiếu nại đã bị sửa nghĩa mà không có cách nào biết
chữ nào đã mất (`"không cần xử lý tiếp"` → `"không [PERSON]"` đủ để xử lý sai ca).
- **KHÔNG đổi:** khuyến nghị vẫn là **B**, vẫn phản đối **C**, lỗ hổng §3 vẫn thật.
- **ĐỔI:** câu hỏi §8.2 (*"giữ 4 số cuối hay che trọn"*) **không còn đủ** — phải hỏi TRƯỚC nó
  **"che bằng CƠ CHẾ nào"**. Trả lời §8.2 trên bản cũ = chọn giữa hai biến thể của một cơ chế đã hỏng.
Đính chính đã vào hồ sơ tại `eff47ac` (cảnh báo đầu file + gạch bỏ §5.2 tại chỗ, giữ nguyên văn cũ
để thấy được cái gì đã đổi).

### ST2-P0-3 — **GIỮ NGUYÊN mở/đỏ, KHÔNG đổi trạng thái** (security đo lại rồi mới trả lời)
Không phải finding lỗi thời mà là **quyết định sản phẩm chờ PO thật**, cố ý giữ đỏ để câu hỏi khỏi
bị đóng im lặng. Lỗ §3 còn hở nguyên: `messages.content` lưu nguyên văn, không retention, mọi
`cskh`/`supervisor` đọc được bất kể có phụ trách ca hay không.
⟹ **F-CI-2 sửa ở JOB CI, KHÔNG sửa bằng cách đóng finding** — đóng một finding đang mở để CI xanh
thì CI xanh mà lỗ vẫn hở. Security xác nhận defect: `ci.yml:251` = `pytest tests/test_api/ -v`,
thiếu `-m "not security_finding"`, còn `test_live_chat_pii_gap.py:25` có `@pytest.mark.security_finding`.
Họ cũng **BÁC nghi ngờ thứ hai của chính mình**: job `appsec` KHÔNG thiếu env (`JWT_SECRET_KEY` /
`FIELD_ENCRYPTION_KEY` ở khối `env:` mức workflow `ci.yml:23-31`, mọi job thừa hưởng) ⟹ **MỘT
defect ở job này, không phải hai**.

### 🔴 S-03 (NÂNG HẠNG 15/08 tối — CA DƯƠNG TÍNH ĐO ĐƯỢC, `c99361d`) — exception lên trace không qua scrub
`span.set_status` / `record_exception` (`langchain_callback.py:96-98`). **Không còn là rủi ro suy
luận**: security đo THẬT trên Postgres có sẵn của dự án (`fin05-postgres-1`, docker-compose):
```
DETAIL:  Key (phone)=(0912345678) already exists.   ← SĐT NGUYÊN VĂN trong DETAIL
```
→ vào `str(error)` → `span.set_status(..., str(error))` + `record_exception` → **ra thẳng backend
trace, không qua scrub** (`_scrub_and_truncate` chỉ áp attribute khác). Đường rò: BẤT KỲ vi phạm
unique constraint trên cột có PII (đăng ký trùng SĐT, upsert…). SQLite im lặng — đúng lớp lỗi chỉ
lộ sau deploy. Tái lập 3 dòng SQL. Security tự ghi nhận: trước đó họ khẳng định từ hiểu-biết-chưa-đo
— đúng lỗi họ vẫn đòi vai khác không mắc; nay đã đo. Bỏ nhánh "không dựng được Postgres thì khai
chưa-đo" trong bộ probe — Postgres có sẵn, S03-01..03 chạy ngay khi coder land.
**Bộ probe A1/A2 viết sẵn ở scratchpad** (đúng quy ước nháp): A1-01 byte-level · A1-02/03 round-trip
biên VN-đủ-dấu+emoji · A1-04 hàng-cũ (ca CHẨN ĐOÁN, không assert — chờ coder trả lời minh thị
backfill) · A2-01/02 hai mép 2000/2001 · A2-05 · A2-06 đường agent. Script kẹp dấu `he_thong` HAI
ĐẦU — lệch = phép đo VÔ HIỆU, không phải "gần đúng".

### 🟡 F-28 (TB) — tier-1 tiếng Anh neo vào MỘT động từ `ignore`; việc coder, KHÔNG cần PO quyết
Tester + tech-lead hội tụ bằng **hai phương pháp khác nhau** (Luật 16): mẫu tier-1 tiếng Anh chỉ
neo `ignore`, nên 7 câu tấn công **cùng ý định, đổi động từ** đi thẳng qua (`disregard` · `forget`
· `override` · `bypass` · `skip` · `do not follow` · `must not obey`). Security đo bổ sung: mẫu mở
rộng đưa độ phủ **1/8 → 8/8**, **FP 0/1814** trên kho MoMo thật (239K ký tự) và **0/7** trên đối
chứng tiếng Anh hợp lệ ⟹ thoả tiêu chí vào tier-1 do chính F-25 đặt. **Vá được ngay, không đổi
contract, không cần PO** — chỉ cần xếp lịch.

⚠️ **Hai vế phải giữ, đừng rút gọn khi báo cáo:**
- **(a) TRUNG BÌNH, KHÔNG phải P0** — F-25 §3(a) đã tuyên bố tier-1 **không phải lằn ranh**: nội
  dung vẫn bị spotlighting bọc và vẫn qua O1-O4.
- **(b) Bản vá KHÔNG đóng LỚP lỗi** — thêm 9 động từ vẫn là **danh sách viết tay**. Luật 18
  (ADR-023) đã sửa lớp này **cho tiếng Việt** và **chưa từng sửa cho tiếng Anh**; việc đó thuộc
  **CỔNG-A**. Sau khi vá phải nói *"bắt thêm 7 ca ĐÃ BIẾT"*, **không** được nói *"đã chặn lớp tấn
  công đổi-động-từ"*.

### ✅ Đính chính F-25 §3(a) — hai "lệch impl-vs-đặc-tả" của tester, coder KHÔNG phải vá (`d312428`)
Tester chặn ở hai lệch trên lớp tier injection; security phân xử: **một không phải lệch** (impl
ĐÚNG, kỳ vọng sai — kéo `bo qua…` về tier-1 sẽ **mở lại đúng lỗ F-25 vừa bịt**); **lệch còn lại là
chữ security viết sai**, họ tự rút sau khi đo FP `0/1814` — đúng phép đo mà F-25 §4 giao cho
security, nay mới làm. ⟹ **Coder không phải vá cả hai; tester viết lại kỳ vọng.**

### 📌 LUẬT MỚI (security rút, đáng đưa vào chuẩn dự án) — assert VẮNG MẶT mù với XOÁ QUÁ TAY
Assert dạng `X not in db` **LUÔN XANH khi nội dung bị xoá nhiều hơn cần thiết** — xoá càng mạnh
test càng xanh. ⟹ Một bộ test chỉ hỏi *"PII có vắng mặt không"* **KHÔNG THỂ** phát hiện over-scrub,
chạy bao nhiêu ca cũng vậy. Đây là lý do cấu trúc khiến bộ 13 ca của tester xanh mà lỗ 40% vẫn
lọt — **bộ test KHÔNG yếu**, nó đo đúng thứ đặc tả (TM-03) yêu cầu; vế toàn-vẹn thiếu vì **không
được viết vào sign-off**, không phải vì ai làm ẩu. Hai câu hỏi phải đi CẶP:
tester hỏi *"X có vắng mặt không"* · security hỏi *"cái CÒN LẠI là gì"* — đúng **Luật 16**, giá trị
nằm ở **sót khác chỗ nhau**. Khi vá S-01, trục đối chứng phải đo *"căn cứ từ chối còn đọc được
không"* và **để FILE RIÊNG** với bộ che-PII (nhét chung = mời một lần sửa làm hỏng cả hai).

**Vế bổ sung (security, để luật đủ dùng về sau):** luật này **không nói bộ test SAI — nó nói bộ
test ĐO SAI THỨ**. Nên cách vá **không phải "viết assert chặt hơn"** mà là **thêm một câu hỏi KHÁC
LOẠI**: cạnh mọi assert *"PII có vắng mặt không"* phải có ca đối chứng *"nội dung hợp lệ có SỐNG
SÓT không"*. Thiếu vế hai thì **bản vá chặt tay nhất luôn thắng theo số đo** (đúng Luật 2 — và là
lý do 27/96 của O1-O4 mới lộ ra được). Hạt giống có sẵn: **corpus 20 ca ghi chú sạch** security đã
giao tester ở §7 hồ sơ 15/08, ngưỡng **0/20** — không phải "thấp hơn".

### F-LOG — bản vá `submit_log.py` (`eadcca7`) NUỐT DÒNG JSON HỎNG, im lặng (tech-lead đo A/B)
Chạy `submit_log.py` THẬT với server giả + `AI_LOG_DIR` giả ở scratchpad (không đụng `.ai-log`
thật, không đụng `src/`). Kịch bản 10 dòng, 1 dòng bị cắt giữa chừng:
```
TRƯỚC vá (eadcca7^) băm f1e4950e1df6 : archive 10 dòng · dòng hỏng CÒN (truy được)
SAU   vá (eadcca7)  băm ab75391a3e09 : archive  9 dòng · dòng hỏng MẤT HẲN
```
Cơ chế: `submit_log.py:118-119` nuốt dòng không parse được (`except JSONDecodeError: pass`).
Trước vá, `_archive(pending)` chép NGUYÊN FILE nên dòng hỏng vẫn nằm lại archive. Sau vá,
`_archive_entries(entries)` chỉ ghi bản ghi ĐÃ PARSE → dòng hỏng không gửi, không archive, rồi
`pending.unlink()`. **Mất cả ba đường cùng lúc, không một dòng cảnh báo.**
**NẶNG vì:** STATE này tuyên bố *"bằng chứng khách quan DUY NHẤT là `.ai-log/archive/`"* — bản vá
làm suy yếu đúng kênh đó, và nó sắp chạy **19 lượt trên 9133 dòng backlog P-121** (deliverable #4).
`73/73 parse sạch` ở lượt 15/08 **KHÔNG** loại trừ: 73 dòng sạch thì nhánh nuốt-lỗi không chạy —
lại đúng "hiện diện ≠ hiệu lực" (nhánh CÓ tồn tại ≠ nhánh ĐƯỢC canh).
Vá ~3 dòng: gom dòng không parse được, ghi bytes GỐC vào archive (hoặc `*.hong.jsonl`) TRƯỚC
`unlink`. **CHƯA SỬA** — `scripts/` ngoài vùng ghi của mọi vai (xem F-ZONE), chờ PO thật giao.
⟹ **Khuyến nghị: vá F-LOG TRƯỚC khi đẩy backlog P-121**, đừng chạy 19 lượt trên đường có lỗ.

**Hồ sơ phép đo (Luật 10): `docs/giao-viec/2026-08-15-do-luong-F-LOG.md`** — hai script đo giữ
NGUYÊN VĂN trong đó, chạy lại được, chỉ thư viện chuẩn. **PO-agent đã chạy lại độc lập, khớp từng
số** (băm hai script tính lại bằng `shasum` cũng khớp con số tech-lead báo). ⚠️ Đó là **chỗ đặt
TẠM** vì bản gốc nằm ở `/private/tmp` gắn phiên tech-lead (phiên đóng = bằng chứng bốc hơi, và
đường dẫn chết trong hồ sơ tệ hơn không có); chỗ đúng là `scripts/` hoặc `tests/`, **chờ F-ZONE**.
⚠️ CA2 + phần B **CỐ Ý ĐỎ** (ca tái lập finding, không phải test hồi quy) — đừng ai sửa cho xanh.
**Bẫy đã ghi trong hồ sơ:** CA3 (tuần tự) báo thứ tự ĐẠT còn phần B (đua thật) báo TRƯỢT — cùng
một câu hỏi, ngược nhau; F-LOG-2 **chỉ hiện ra dưới đồng thời thật**, test tuần tự sẽ xanh giả.

**TIN TỐT cùng lượt đo:** nhánh **leftover CHẠY ĐÚNG** — 502 dòng, `BATCH_LIMIT=500` → lượt 1 gửi
500 + "2 deferred", lượt 2 gửi 2; `archive 502 dòng · id duy nhất 502 · trùng lặp 0`. Bản vá làm
đúng điều nó hứa, backlog sẽ không phình archive.

**F-LOG-2 (thấp, CÓ TRƯỚC bản vá — không phải hồi quy):** `submit_log.py:155` dùng
`open(LOG_FILE, "a")` → leftover (CŨ) bị nối SAU phần hook vừa ghi (MỚI); đo thật ra thứ tự
`[900, 901, 500, 501]`. Trớ trêu: nhánh THẤT BẠI `_restore_pending()` cố ý xử đúng ca này (có
comment *"pending (older) + LOG_FILE (newer)"*) — **nhánh thành công mắc đúng lỗi mà nhánh thất
bại được viết ra để tránh**. Chưa từng quan trọng vì leftover chưa từng chạy; backlog P-121 là lần
đầu nó thành thật. Sai thứ tự, KHÔNG mất dữ liệu — server sắp xếp lại được nếu bản ghi có timestamp.

### F-ZONE — `scripts/` là VÙNG VÔ CHỦ trong §4 (đề xuất, PO thật quyết)
§4 giao `src/ frontend/src/ migrations/ contracts/` cho tech-lead, `docs/` + `*.md` gốc cho po —
**không ai sở hữu `scripts/`**. Đó chính là chỗ bản vá `_archive_entries()` nằm lửng lơ trong cây
làm việc mà không vai nào nhận. Tech-lead xác nhận **không phải nháp của phiên này** (phiên khởi
động sạch, chưa ghi byte nào) ⟹ là của một PHIÊN TRƯỚC. Đề xuất thêm một dòng vào §4 giao
`scripts/` cho tech-lead, để nháp mồ côi lần sau có chủ.

## Cảnh báo còn tồn
- **gate-96 giờ BẬT THẬT** (`e4ef0e8`, không còn tắt — mục trên đã lỗi thời, sửa 15/08).
- **Số end-to-end gắn với hệ thống KHÔNG CÒN TỒN TẠI** (tester đo): lượt "sau" chạy ở
  `he_thong 6096dc8b5678` (commit `8d26548`); cây hiện tại `fd16681d8088` vì `7b68992` (note) land
  sau đó. ⟹ hai số **HÀNH VI** (câu 2: 17/17 · câu 4: 2/5) gắn hệ thống đã mất; hai số **DỮ LIỆU**
  (câu 1 cổng-96 · câu 3 fallback) mua vĩnh viễn. Trích cho quyết định 150 người thì trích được
  cả bốn, **chỉ cần ghi rõ nhãn**.
- **Cửa sổ đóng băng ĐÃ ĐÓNG** — security nhắn "MỞ TAY `src/`" sau khi nộp hồ sơ `c2c2d06`.
  Không vai nào đang giữ mốc nền. Coder chạm `src/` được khi PO giao việc.
- 🔴 **MỐC NỀN 18/20 `6c5fff420bb9` ĐÃ TRÔI** — cây làm việc nay `fd16681d8088` (đúng dự kiến:
  O1-O4 + F-27 + `note` đã land). **Hệ quả: lượt đo mới KHÔNG ghép cặp trước/sau với mốc cũ được
  nữa.** Đợt CỔNG-A phải đóng băng một **mốc nền MỚI ở một `he_thong` xác định TRƯỚC khi tiêu
  TPM** — không thì lặp đúng sự cố `8e46f28→6c5fff`.
  📌 **GHIM — security xin được gọi TRƯỚC lượt đo đầu tiên của CỔNG-A, không phải sau.** Bước đóng
  băng mốc nền mới là bước **không được bỏ**; gọi sau thì **lượt đo đã hỏng rồi mới biết**, và TPM
  đã tiêu. Đây là mốc tương lai duy nhất security chủ động xin ghim khi đóng sổ.
- **Rà pipeline scrub mới xong PHẦN OTel/callback.** CHƯA rà: đường **Langfuse** (đang TẮT có chủ
  đích) và **đường log của eval** (`logging_config` chưa init ở runner). Ghi rõ để không ai đọc §5
  của hồ sơ security thành "đã rà hết".
- **MT-E02 thu hẹp** (security §6): chỗ nổ xác định = `investigation_log.py:89 session.flush()`,
  FK `investigation_logs.ticket_id`. **MT-E02 và MT-F01 traceback TRÙNG HÌNH DẠNG** ⟹ nhiều khả
  năng **một defect hai tên** (đúng chỗ sổ ghi "coder gọi MT-F01, tester gọi MT-E02"). Cơ chế sinh
  id cũ **CHƯA kết luận** (Luật 5) — **giữ nguyên: ĐỪNG đốt TPM tái hiện**. Góc bảo mật mới: flush
  chết ⟹ mất `investigation_logs` của lượt đó ⟹ **ĐỨT MẮT XÍCH chuỗi truy vết của RÀNG BUỘC CỨNG
  3**, im lặng.
- **Mốc nền đối kháng chốt VĨNH VIỄN 18/20** (he_thong 6c5fff420bb9); 18 ca MÙ với siết-nhầm → "18/18→18/18"
  là chốt-chặn-hồi-quy MỘT NỬA, nửa kia đo bằng 🔇 + F-25(b). MT-A01/F-01 không quay lại nhánh "trước" được.
- CI: **TẤT CẢ đều treo sau F-CI (billing), không phải "chưa làm"** — note-tests đã land và xanh ở
  MÁY (15 passed), thiếu đúng phần quan sát trên runner · 2 eval chờ PO-2 secret · CI-4/5 chưa
  nghiệm thu. Không mục nào tiến được tới khi billing thông.
- **[c] oracle-phủ-định "không phải 21"** còn lọt (1 bit/lượt, có tài liệu) → đợt cổng-A (vẫn treo).
- Môi trường test cục bộ (máy PO-agent) thiếu sẵn `argon2` + model NER `xx_ent_wiki_sm` — không phải bug,
  chỉ là máy này chưa từng dựng venv cho repo (dùng venv scratchpad tạm, không commit).

## 📋 PHÂN CÔNG SONG SONG 15/08 (chiều muộn) — PO thật uỷ quyền PO-agent giao 3 vai
> PO thật chỉ quản PO-agent; PO-agent giao việc + nhận báo cáo từ 3 vai. Nguyên tắc chia:
> **vùng ghi tách hẳn** (coder: `src/`+`ci.yml`+`scripts/` · tester: `tests/`+`eval/` · security:
> `docs/security/` · PO-agent: `docs/`) và **không vai nào giữ mốc đo trên `src/` trong lúc coder
> mutate nó**. Ba việc đầu mỗi vai đều KHÔNG cần chờ vai khác.

| Vai | Việc (thứ tự ưu tiên) | Ràng buộc chính |
|---|---|---|
| **Coder** (`p-226-8f`) | ① F-CI-3 trả lời tên hàm `phan_tier` (MỘT DÒNG, đang chặn tester) → ② F-CI-2 một dòng `ci.yml` (trước khi billing thông; CẤM sửa bằng đóng ST2-P0-3) → ③ A1+A2 `description_raw` (CẤM scrub — nhóm A chờ ADR-025) → ④ F-LOG (gate đẩy backlog P-121) → ⑤ S-03 → ⑥ F-28 | BÁO-TRƯỚC-KHI-LAND mọi commit chạm `src/` · nháp ở scratchpad · S-03/F-28/A1/A2 KHÔNG tự đóng, chờ security probe |
| **Tester** (`p-226-c8`) | ① Port 2 script F-LOG vào `tests/` canh nhánh leftover (CA2+phần-B CỐ Ý ĐỎ, không sửa cho xanh) → ② Dựng trục đối chứng "căn cứ từ chối còn SỐNG SÓT không" (corpus 20 ca, ngưỡng 0/20, FILE RIÊNG; XÂY chưa chạy gate — chờ ADR-025) → ③ Gỡ skip 2 test tier khi coder trả lời tên hàm | KHÔNG đọc `src/` · KHÔNG mốc nền/TPM đợt này (coder đang mutate `src/`) |
| **Security** (`p-226-0f`) | ① Rà nốt 2 đường scrub tự khai "chưa rà": log-eval (ưu tiên, dính F-LOG) + Langfuse (mức "nếu bật thì rò gì") → ② Soạn trước bộ probe cho A1 (byte-level) · A2 (2 mép) · S-03 (cần Postgres, không kết luận từ SQLite) · F-28 (kèm đối chứng) → ③ GIỮ CHỜ: ADR-025, MT-E02 | Cần đóng băng `src/` thì báo PO-agent xin coder dừng tay, không tự lấy mốc |

**Điểm khớp nối:** coder land ①→tester gỡ skip · coder land ③④⑤⑥→security probe→mới đóng ·
ADR-025 ký→tester chạy trục đối chứng làm gate + coder làm B1/B2/B3/A3/A4.

### Tiến độ phân công (cập nhật chiều muộn 15/08)
- **✅✅ LÔ ĐÓNG SỔ HOÀN TOÀN — security nghiệm thu CẢ BỐN ĐẠT** (biên bản `9122677`, probe tại
  `cf98ef8`, `src/` byte-identical với `cc07dd3`): **A1** ĐẠT probe-bằng-byte **KÈM ĐIỀU KIỆN**
  (chỉ bảo vệ dữ liệu ghi TỪ `cc07dd3` trở đi — *"A1 đã nghiệm thu" ≠ "description_raw đã được mã
  hoá"*, hàng cũ vẫn plaintext, backfill = quyết định PO TRƯỚC pilot) · **A2** ĐẠT chặn ở tầng
  service không rơi xuống CHECK · **S-03** ĐẠT trên Postgres THẬT (lỗi thật từ container →
  `[PHONE_NUMBER]`, 0 PII trong span, vẫn giữ tên constraint để gỡ lỗi — hai vai bù đúng thiết kế:
  coder tự khai "chuỗi lỗi mô phỏng" → security lấy lỗi thật) · **F-28** ĐẠT 8/8 · 0/7 · FP 0/1814.
- **📌 GIỚI HẠN CÔNG CỤ DẤU-BĂM (tech-lead chỉ ra, security xác nhận):** `he_thong` băm
  `src/**/*.py` — **KHÔNG phủ `scripts/` + `migrations/`**. Lô chạm ngoài `src/` sẽ có dấu
  **không lệch mà vẫn VÔ NGHĨA**. Nhãn phép đo cho lô đa-vùng: dùng **SHA commit**, không dùng
  `he_thong`. (Biên bản `9122677` dùng SHA vì đúng lý do này.)
- **🎁 DẪN XUẤT THỨ BA CHO S-01 (từ probe S-03):** scrub gán `DETAIL`/`ERROR` → `[ORGANIZATION]` —
  cùng lớp lỗi với `"chính sách"` → `[PERSON]` nhưng ở **đường khác** (trace ≠ note), **vai khác**
  phát hiện, **phương pháp khác**. Ba dẫn xuất độc lập cùng kết luận: **sai NHẬN DẠNG, không sai
  NGƯỠNG — lỗi là thuộc tính của LỚP NER, mọi cửa dùng `scrub_pii` đều thừa hưởng.** Đây là lập
  luận mạnh nhất cho việc ADR-025 quyết CƠ CHẾ, không vá từng cửa.
- Security tự đính chính trong biên bản: khuyến nghị 40.000 của họ ở phản biện **sai ở mép trên**
  (thiếu trục chặn-flood) — ADR đã ghi 12.000 + cửa sổ từ `cda800d`, khớp. Quét `.md` trong
  `eval/results` đóng: **0 SĐT thật** (16/18 seed, 2/18 mảnh mã GD — số "18" ban đầu tự thổi bởi
  đúng false-positive đó).
- **F-LOG-2 ĐÃ LAND `e321780`** (sớm hơn lịch), tester gỡ marker F-LOG xác nhận 5 passed · 1 xfailed.
- **🔴 F-28b — tester bắt lỗ TRONG phạm vi F-28 vừa ký:** `disregarding all previous instructions`
  LỌT — dạng **V-ing của chính động từ F-28 vừa thêm** (mẫu đòi dấu cách ngay sau động từ). Không
  phải "lớp rộng chưa làm" — biến thể hình thái của từ trong phạm-vi-tự-nhận-đã-đóng. Coder đo HAI
  bản vá trước khi đề xuất: bản A (liệt kê hậu tố `s|ed|ing`) **cũng lọt** `forgetting` (phụ âm
  gấp đôi — danh sách viết tay vá lỗ danh-sách-viết-tay, thiếu đúng chữ kế, lần hai trong cùng bản
  vá); bản B (thân + `\w*`) đóng **8/8, FP 0/7 + 0/2006 kho MoMo thật**. Đo cả cái KHÔNG đóng:
  5 ca đổi-hẳn-động-từ (`refrain from…`, `pay no attention…`, gõ-sai `ignroe`) vẫn lọt = CỔNG-A.
  ~~PO-agent QUYẾT: đường (1) — land bản B vào tier-1~~ → **🔴 ĐẢO LỆNH sau probe khẩn của
  security (Luật 8 lần SÁU — chân bị rút là của CẢ BA):** bản B gây **FP TIER-1 THẬT** — `ignor\w*`
  bắt `ignorant` (từ khác hẳn), và *"Please do not disregard the safety guidelines"* bị **XOÁ
  TRẮNG** = **F-25 tái diễn nguyên hình dạng bằng tiếng Anh** (khuyến cáo an toàn thật bị xoá).
  Vì sao FP 0/7+0/2006 không bắt được — **corpus có lỗi, security tự nhận corpus của họ**: 7 câu
  đối chứng mỏng đúng trục bản vá chạm (không mệnh-lệnh-phủ-định, không ca `\w*` vươn quá);
  2.006 câu kho MoMo là TIẾNG VIỆT — cấu trúc không thể bắt FP mẫu tiếng Anh. Số đúng, không nói
  gì về lớp lỗi này.
  **LỆNH CUỐI (security đề nghị, PO-agent duyệt): `\w*` vào TIER-2** (giữ nội dung + nhãn trung
  tính + đếm — V-ing attack bị đánh dấu, không bị xoá trắng, vẫn qua spotlighting + O1-O4) ·
  **tier-1 GIỮ HẸP** dạng nguyên thể 0/1814 · phân biệt cực-của-động-từ (`do not follow` tấn công
  vs `do not disregard the safety` khuyến cáo) = sửa LỚP thuộc **CỔNG-A**, cấm nhét vào hotfix.
  Đây là áp đúng tiêu chí F-25 §3(a): vào tier-1 = FP đo được phải bằng 0 trên nội dung hợp lệ.
  **Chữ ký F-28 ĐÃ RÚT** — security đang mở rộng bộ đối chứng tiếng Anh đủ trục (hình thái +
  mệnh-lệnh-phủ-định) rồi giao tester; bộ 7 câu cũ KHÔNG đủ để ký bất kỳ bản vá nào chạm mẫu EN.
- **✅ LÔ CODER ĐÃ LAND — HEAD `cc07dd3`** (5 commit: F-LOG `cc07dd3` · F-28 `e082a34` ·
  S-03+F-30+F-29-gitignore `83f45df` · A1+A2 `5b65b81` · F-CI-2+ruff `37ed7fc`). Pathspec sạch —
  không đụng `tests/`/`docs/`. Đo tại `cc07dd3`: ruff sạch · invariants 23 · contracts 3/3 ·
  suite 492 passed/18 skipped/9 xfailed/**1 failed = XPASS(strict) ca F-LOG của tester — cơ chế
  chạy ĐÚNG**: bản vá làm ca tái lập qua được, strict biến "qua" thành đỏ buộc tester gỡ marker
  (họ gỡ, không phải coder). **Chưa đóng A1/A2/S-03/F-28 — chờ probe security** (đã được mời).
- **A2-06 ĐÓNG bằng câu trả lời + số đo:** trần đặt ở `create_ticket_with_fraud_check`
  (`complaint_intake.py:118` — call site DUY NHẤT của `_create_ticket`) ⟹ phủ CẢ BA đường
  (REST `main.py:538` · agent `customer_tools.py:620` · `flag_human_handoff`), đo cả ba có đối
  chứng (3.200→CHẶN · 2.000→NHẬN). Còn TỐT hơn gợi ý đặt-ở-`create_ticket`: trần đứng TRƯỚC fraud
  engine (engine đọc `description_raw` làm `utterance_text`) — không phân tích gian lận trên chuỗi
  20K rồi mới từ chối. CHECK 12.000 không là lưới duy nhất của đường nào — nguyên tắc ADR nguyên vẹn.
- **A1-04 ghi minh thị vào docstring `models.py`** (nơi người sửa tiếp theo thật sự đọc): hàng
  trước 2026-08-15 plaintext VĨNH VIỄN trên đĩa; "đọc được" ≠ "được mã hoá at-rest"; chấp nhận vì
  seed/test + pilot hoãn; **backfill là quyết định RIÊNG phải ra TRƯỚC khi mở pilot**.
- **⚠️ Nuance migration phải giữ khi đọc "A2 đã verify":** migration A2 (`a7b8c9d0e1f2`) **CHƯA
  TỪNG chạy qua alembic** — chuỗi gãy ở `a1b2c3d4e5f6` (SQLite) TRƯỚC khi tới nó; coder verify
  CHECK bằng `create_all` + probe hành vi. "A2 đã verify" ≠ "migration A2 đã verify".
- **F-LOG-2 (thứ tự đảo): PO-agent xếp lịch = lô nhỏ KẾ TIẾP của coder, ưu tiên thấp** — vá rẻ
  (tái dùng logic prepend của `_restore_pending` cho nhánh leftover), xfail của tester đứng làm
  tài-liệu-sống tới lúc đó. Không gấp: sai thứ tự không mất dữ liệu, server sort được theo ts.
- **QĐ 5 / bound 12.000: security ĐO LẠI XÁC NHẬN ĐỦ** (`44c3c9a`) — biên 12% trên worst-case
  emoji 4-byte, và Fernet tất định theo byte nên không có ca xui. **Đủ CÓ ĐIỀU KIỆN** ⟹ ca mới:
- **🟠 A2-06 (CA PHẢI KIỂM, chưa phải finding — security minh thị chưa đo vì cây trôi):**
  `description_raw` có **HAI đường ghi** — REST (qua Pydantic, có trần) và **AI-gọi-tool dưới danh
  nghĩa customer** (`customer_tools` → `create_ticket…`), đường sau **không đi qua
  `ComplaintCreateRequest`**. Nếu đường agent không có trần riêng: mô tả quá dài rơi thẳng xuống
  CHECK DB → `IntegrityError` → 500 (hình dạng F-21), trong khi mọi test REST xanh. **CHECK phải
  là lưới CUỐI, không được là lưới DUY NHẤT của bất kỳ đường nào.** → chuyển coder dạng CÂU HỎI.
- **A1-04 nhắc lại cho probe:** `complaints` ĐÃ CÓ dữ liệu (khác `messages` 0 dòng) — coder chọn
  không-backfill (hàng cũ đọc được qua đường InvalidToken) ⟹ **hàng cũ nằm PLAINTEXT vĩnh viễn
  trên đĩa** trừ khi có quyết định backfill-mã-hoá riêng. Test DB-sạch không lộ ca này.
- **A2 bound CHỐT LẦN CUỐI = 12.000, ghi thành CỬA SỔ [10.764 … 26.764]** (ADR-025 QĐ 5 sửa lần 2):
  40.000 của PO-agent bị coder bác bằng đo — ≈28.943 ký tự ASCII lọt, flood 20K ASCII đi thẳng qua.
  Luật 8 lần NĂM, bắt cả coder (mẫu ASCII) lẫn security+PO-agent (mẫu 3-byte quên emoji 4-byte).
  Thoát vòng = ghi CỬA SỔ kèm cả hai mép, mọi lần đổi số phải đo lại CẢ HAI.
- **Coder vá thêm ngoài phạm vi (chấp nhận, có lý do):** 3 lỗi ruff có sẵn từ trước (N812×2 +
  UP037) — không vá thì job lint đỏ TRƯỚC khi tới pytest, F-CI-2 vô nghĩa.
- **🔴 PHÁT HIỆN MỚI (có sẵn, cần quyết định riêng — CHƯA ai sửa): chuỗi migration GÃY trên SQLite**
  tại `a1b2c3d4e5f6` (ADR-019): `NotImplementedError: No support for ALTER of constraints in SQLite
  dialect` ⟹ `alembic upgrade head` trên DB trắng SQLite CHẾT. Coder verify CHECK A2 bằng
  `create_all` + probe hành vi thay vì alembic. Hướng vá khi giao: `render_as_batch`/batch_alter
  cho SQLite — xếp lịch riêng, không gộp lô này.
- Suite lúc báo cáo: 492 passed · 18 skipped · **9 failed = toàn bộ ở cổng F-NOTE của tester
  (`test_note_toan_ven_can_cu_tu_choi.py`, file chưa track) — ĐỎ CÓ CHỦ ĐÍCH chờ vá B1/B2**,
  không phải hồi quy của lô coder.
- **Coder ①②③(A1) XONG** (báo-trước-khi-land đúng luật): F-CI-2 verify hai chiều (appsec
  227 passed/1 deselected · security-findings-gate VẪN ĐỎ — chuyển finding về đúng job canh, không
  giấu) · A1 `models.py:223` EncryptedText, probe hành vi tiền tố Fernet + đối chứng hàng-cũ-vẫn-đọc
  (đường InvalidToken, không cần migration/backfill) — CHỜ security probe mới đóng. **A2: PO-agent
  quyết phương án (b) + trần 2.000 ký tự** (schema chính-xác-ký-tự + CHECK thô ciphertext ≤4.000;
  Fernet nở theo byte nên DB không diễn đạt được trần ký tự — số đo coder ×1.72-1.9).
- **🔴 Finding mới của coder (Luật 8 lần BA): F-24 vs F-25 MÂU THUẪN trên nhánh EN**
  (`customer_tools.py:152-154` chỉ có comment F-24; `:165` VN có cả hai) — nhánh EN không bị bỏ
  quên, nó bị MỘT trong hai bản vá sờ tới. → security gộp phân xử vào probe F-28.
- **Corpus 20 ca ĐÃ XUẤT FILE** (`c403384`): `docs/security/corpus-ghi-chu-sach-20-ca.jsonl` (+.md,
  8 ca 🔴). Trích **bằng AST** từ script đo gốc — không chép tay, không import src/. **BA GIỚI HẠN
  đi kèm corpus (cấm dùng rộng hơn):** (1) 20 câu soạn tay — chứng minh TỒN TẠI lớp chặn nhầm,
  KHÔNG phải tỷ lệ sản phẩm — **đừng để "40%" đi vào báo cáo PO như tỷ lệ thật**; (2) chỉ phủ nhóm
  B — nhóm A (khẩu ngữ/sai chính tả/không dấu) cần corpus riêng; (3) thuần đối chứng, **PHẢI chạy
  cùng bộ ca có PII, cấm chạy lẻ** — không thì bản vá "không scrub gì" đạt 0/20 hoàn hảo. Mở rộng =
  THÊM ca GC-21+, **không sửa 20 ca gốc** (mất mốc). `ket_qua_goc` là nhãn tại `fd16681d8088` —
  cây ĐÃ trôi sang `f3193ecae0e2` (A1 land); ai đo lại = cặp MỚI đóng dấu riêng, không ghi đè.
- **Tester ①③ XONG** — `tests/test_ai_log/test_f_log_leftover.py`: 3 passed · 2 **xfail(strict)** ·
  suite đầy đủ 478 passed/0 failed. Hai ca finding dùng `xfail(strict=True)` thay đỏ-trần (PO-agent
  RATIFY): hiện rõ trong report, không chặn CI khi billing thông (né hình dạng F-CI-2), và khi coder
  vá F-LOG thì **XPASS tự báo lỗi buộc gỡ marker** — yêu cầu "chỉ xanh sau khi vá" thành CƠ CHẾ.
  Thêm assert server-nhận-đủ (502 archive ≠ 502 đã POST — hai câu hỏi, hai assert). Không port phần
  A/B lịch sử (đã kết luận, `git show eadcca7^` chết trên CI fetch-depth:1) — kết luận giữ trong
  `reason` của xfail. **Việc ③**: `_phan_loai_tier` (coder trả lời) → 2 bộ tier chạy lần đầu, lượt
  đầu 6 failed → security phân xử bằng phép đo mới → tester viết lại kỳ vọng → **29 passed**,
  `he_thong` trước=sau=`fd16681d8088`, `src/` không ai chạm. +5 ca khoá 4 họ tier-1 + Luật 6/6b vào
  `CHUAN-VIET-TEST.md`.
- **Tester ② XONG — trục đối chứng LÀ CỔNG SỐNG** (`he_thong c110a1a8eff7`, dấu trước=sau, đo 3
  lần tất định): **8/20 chặn nhầm, cổng ĐỎ đúng chủ đích**. Giá trị nhất: **DANH SÁCH trùng 8/8
  với security** (GC-02·03·07·10·11·15·17·18) qua **hai phương pháp khác nhau** — security gọi
  thẳng hàm scrub, tester đi đường ghi thật POST /reject → **đọc thẳng DB** (đọc qua API không phân
  biệt được che-khi-ghi với ghi-thô-che-lúc-trả). Chốt được: finding KHÔNG phải hiện vật của cách
  đo · còn nguyên tại cây đã gồm lô A1/F-28 · cổng sống không ai phải nhớ chạy lại. Ba giới hạn
  corpus đều thành CƠ CHẾ (docstring + test cấm-chạy-lẻ đọc `request.session.items`, nghiệm thu
  hai chiều). Bộ đo KHÔNG đọc `ket_qua_goc` để chấm — đo lại từ đầu, đóng dấu riêng.
  **Một lượt đo bị VỨT đúng quy trình** (chạy khi coder sửa dở, dấu trước≠sau): con số không SAI,
  nó **VÔ DANH** — không gán được nhãn hệ thống thì không tái lập/ghép cặp. Khác cơ chế Luật 4
  (pytest import một lần — 20 ca vẫn cùng hệ thống trong bộ nhớ); gộp hai lý do sẽ khiến lần sau
  quy sai nguyên nhân.
  **PO-agent quyết:** cổng 8/20 gắn **marker `security_finding` sẵn có** → tự rơi vào job
  `security-findings-gate` (đúng ngữ nghĩa: finding cố-ý-đỏ làm bằng chứng, tách khỏi
  `lint-and-test`), không cần job mới, không chờ coder. Khi B1/B2 land và cổng xanh → gỡ marker,
  nó thành regression-gate trong lint-and-test.
- **Security ①② XONG** (`7c71905`, không cần đóng băng — toàn đọc tĩnh): đường log eval
  **KHÔNG TỒN TẠI** (`configure_logging()` chỉ ở `main.py:115`) ⟹ câu "log eval có scrub không"
  không áp dụng — chưa có gì để scrub, và hỏng thì không có gì điều tra. **GHIM vào F-LOG: không
  đóng nếu chỉ "có log" — log eval phải qua CÙNG lớp scrub với đường app, verify bằng ca có PII.**
  Bộ probe A1/A2/S-03/F-28 đã soạn, land là chạy; điều kiện ký = đủ BA (hiệu quả + đối chứng +
  dấu he_thong hai đầu), thiếu đối chứng thì không ký kể cả hiệu quả đẹp.
- ⚠️ Nếu `test_mau_tier1_chi_thi.py`/`test_f24_recall_tier1.py` ĐỎ trong lô coder: **không phải
  hồi quy sản phẩm** — hàm đổi tên; gọi tester, đừng sửa test.

### 🔴 F-29 (CAO cho PILOT) — `eval/results/` 138 file TRACK trong git, harness ghi tin khách nguyên văn
PO-agent xác minh độc lập: **138 file track · 74 file `_raw.json` · `.gitignore` 0 dòng về eval**.
File `_raw.json` chứa `all_customer_texts` (tin khách nguyên văn mọi lượt) + `tool_calls_day_du` +
traceback. **Hôm nay phơi nhiễm THẤP** — payload đã che (`********0001`), lớp masking BR-06 chạy
đúng. **Nhưng cơ chế là rủi ro thật:** BR-06 **không che chính chủ** (`lookup_transaction.py:41,53`);
eval chạy dưới danh nghĩa người-không-phải-chủ nên mọi thứ ra đã che — **pilot thật thì khách hỏi
giao dịch CỦA HỌ ⟹ `is_owner=True` ⟹ SĐT/STK/họ tên THẬT không che, vào thẳng file git-track**.
Cộng `all_customer_texts` chưa bao giờ qua scrub.
**Chạm thẳng điều kiện pilot của security ("có đường xoá sau đợt")**: file đã commit thì không có
đường xoá thực hành (xoá commit sau không xoá lịch sử; rewrite+force-push = loại việc luôn phải hỏi
PO, bất khả nếu repo đã clone). ⟹ **chạy harness với người thật mà không sửa = điều kiện pilot TRƯỢT.**
- Mức tối thiểu TRƯỚC pilot: `.gitignore` loại `_raw.json` (→ coder, kèm lô) + scrub-trước-khi-ghi
  (→ tester, vùng `eval/`, sau việc ②).
  **⚠️ PHẠM VI SỬA theo đo lại của tester (không phải chỉ `all_customer_texts`):** trường văn bản
  tự do trong `_raw.json` gồm `all_customer_texts · all_agent_replies · reply · description ·
  tool_calls` — và `reply`/`all_agent_replies` là **lời agent NHẮC LẠI thông tin khách** (tên, số
  tiền, mã GD — đó là mục đích của nó), nên scrub riêng tin khách thì PII thật vẫn rò qua lời agent
  ở pilot. **Phạm vi đúng: scrub MỌI trường văn bản tự do.** Số đo lại: 69 file raw trên đĩa ·
  138 track · 33 file có `all_customer_texts`.
  **HỒI TỐ: KHÔNG scrub lại 69 file cũ — CHỈ chặn từ nay. Lý do ghi rõ (PO-agent quyết):** file cũ
  đã đo là vô hại (eval chạy danh nghĩa không-chính-chủ, BR-06 che hết), và scrub file đang track
  cũng KHÔNG xoá được bản gốc khỏi lịch sử git — muốn xoá thật phải rewrite history, đúng thứ
  security đã cân và chủ động không đòi. Scrub hồi tố = tốn công mà không thêm an toàn thật.
- **138 file CŨ: quyết định của PO THẬT** — phơi nhiễm thấp, rewrite history đắt/rủi ro hơn lợi ích
  (security chủ động KHÔNG đòi xoá), nhưng file kết quả là bằng chứng nộp bài (deliverable #10) nên
  không ai khác quyết thay được.
- Còn treo security tự khai: mới đo MẪU file mới nhất, chưa quét hết 138 file, chưa kiểm các `.md`
  trong `eval/results/`.

### 🟡 F-30 (TB, tiềm ẩn) — LangSmith: kênh xuất dữ liệu mở được bằng env var, không để vết trong git
KHÔNG có tích hợp nào trong `src/` (grep sạch — tin tốt). Nhưng gói `langsmith` 0.11.0 ĐÃ CÀI (kèm
langchain; PO-agent xác minh có trong env), và tracer native của LangChain bật **hoàn toàn bằng env
var**, đi vòng qua `_scrub_and_truncate` (lớp đó nằm trong callback TỰ VIẾT, tracer native không gọi).
Bật trên dashboard ⟹ không diff, không ai review thấy. `docs/guide/chapter-07.md` (giáo trình AI20K,
KHÔNG phải runbook FIN-05) hướng dẫn bật ở production — đội đang học nó. Pháp lý nếu bật với dữ liệu
thật: **chuyển dữ liệu cá nhân ra nước ngoài — NĐ 13/2023 Điều 25**, cần hồ sơ đánh giá tác động.
Vá rẻ (→ coder, kèm lô): đặt `LANGCHAIN_TRACING_V2=false` **MINH THỊ** trong config/Dockerfile —
biến cấu-hình-ngầm thành quyết-định-hiện.

## Việc kế tiếp
0. **PO THẬT — TRƯỚC PILOT (danh sách gom, mới):** quyết **backfill A1** (mã hoá hàng
   `description_raw` cũ — hiện plaintext vĩnh viễn, docstring `models.py` ghi rõ) · cam kết 2 điều
   kiện pilot của security (dữ liệu thật + đường xoá) · A3/A4 pha 2. Pilot đã hoãn nên KHÔNG gấp —
   gom một chỗ để không rơi.
1. **PO THẬT — billing org `AI20K-Build-Phase-Cohort-3`** (F-CI). Chặn mọi nghiệm thu CI.
2. **PO THẬT — MỘT quyết định cho CẢ BỐN CỬA văn bản tự do** (S-01 `note` · S-02 `agent_note` ·
   ST2-P0-3 `messages.content` · `complaints.description_raw`) ⟹ **ADR-025**. Ba lý do buộc phải
   gộp: (a) chốt riêng lẻ = che ô này hở ô kia, hồ sơ §7 đã cảnh báo từ trước; (b) `scrub_pii` —
   cơ chế được kê cho cả bốn — **đã đo được hỏng 40%**, nên phải trả lời **"che bằng CƠ CHẾ nào"**
   TRƯỚC khi trả lời "giữ 4 số hay che trọn" (§8.2); (c) ST2-P0-3 giữ **mở/đỏ có chủ đích** cho
   tới khi có quyết định này — **đừng đóng nó để CI xanh**. KHÔNG để coder tự vá.
3. **PO THẬT — giao ai vá F-LOG** (`scripts/` vô chủ, xem F-ZONE) và chốt: **vá TRƯỚC rồi mới đẩy
   backlog P-121**. Đẩy trước = chạy 19 lượt trên đường có lỗ nuốt-dòng-hỏng, đúng deliverable #4.
4. **Coder — BỐN việc rẻ, KHÔNG cần PO quyết cơ chế, chỉ cần xếp lịch:**
   (a) **F-CI-2** một dòng `ci.yml` thêm `-m "not security_finding"` cho job `appsec` — nên xong
   **TRƯỚC khi billing thông**, nếu không cổng đỏ vì lý do sai đúng lúc đội dễ tặc lưỡi nhất;
   (b) **F-CI-3** trả lời một dòng **tên hàm thật** của `phan_tier` để 2 bộ test tier-split hết skip;
   (c) **S-03** scrub exception trước khi lên trace — độc lập, không chặn gate nào;
   (d) **F-28** mở rộng động từ tier-1 tiếng Anh (1/8→8/8, FP 0/1814) — nhớ **vế (b)**: bản vá
   KHÔNG đóng lớp lỗi, chỉ bắt thêm 7 ca đã biết; lớp thuộc CỔNG-A;
   (e) **A1** mã hoá at-rest `complaints.description_raw` + **(f) A2** trần độ dài — security xác
   nhận **không chờ ADR-025**: A1 chỉ là **bù cho ngang chuẩn đã có** (live-chat đã `EncryptedText`),
   không phải cơ chế mới cần quyết.
   ⚠️ **Cả bốn bản vá S-03 · F-28 · A1 · A2 PHẢI có probe từ VAI KHÁC trước khi coi là đóng** —
   security đã nhận sẵn việc re-probe. Lý do là luật đội đã ratify: **coder tự nghiệm thu là CẦN,
   KHÔNG BAO GIỜ ĐỦ** cho lớp phòng vệ (mọi phép kiểm coder tự thiết kế thừa hưởng điểm mù của coder
   — rút từ sự cố F-23 thật).
3. PO chốt hướng đợt 150 người (số end-to-end đã có, nhớ ghi nhãn hành-vi/dữ-liệu ở "Cảnh báo").
4. Coder: chờ security "MỞ TAY src/" rồi mới chạm. Xếp hàng: chip câu 3 (sau 5a core + QA baseline)
   · đợt cổng-A gộp 3 oracle · câu-4 RAG retrieval (chunk/embedding, trước pilot 150 người).
5. **PO-2**: đặt `OPENAI_API_KEY` thành secret trên GitHub → mở 2 CI eval (chỉ có tác dụng SAU khi
   billing thông).

## Phiên rà soát bảo mật ĐÃ ĐÓNG SỔ — mục lục cho phiên security sau
**`docs/security/2026-08-15-ket-so-ra-soat-cuoi-sprint.md`** (`80b217a`) = mục lục + tư thế rủi ro
tồn dư, **không lặp nội dung**, để phiên sau không phải dựng lại mạch từ 7 commit + một chuỗi tin
nhắn. Năm việc treo security nhận đầu phiên, trạng thái đóng sổ:

| Việc treo | Trạng thái |
|---|---|
| `note` / CI security-gate | **XONG** — kết luận **CHƯA BẬT** |
| mốc nền 18/20 | **ĐÃ TRÔI** `6c5fff` → `fd16681d`, kèm hệ quả bắt buộc cho CỔNG-A |
| oracle-phủ-định "không phải 21" | **KHÔNG ĐỔI** — vẫn thuộc CỔNG-A |
| MT-E02 | **thu hẹp, CHƯA đóng** (cố ý — Luật 5) |
| pipeline scrub | **XONG MỘT PHẦN** — rà OTel/callback; **chưa** rà Langfuse (tắt có chủ đích) + đường log eval (F-LOG) |

### 📌 Về SÁU ca tự-bắt-mình trong phiên (§6 kết sổ) — ghi để đọc đúng, không đọc thành cẩu thả
Sáu ca cùng họ **thước-hiệu-chuẩn-theo-vật**: PO-agent tuyên bố `archive/` là bằng chứng đủ · PO-agent
gọi `note` là việc đã đóng · security viết "cả bốn ô đã đo hành vi" khi một ô chưa probe · security
kê `scrub_pii` ở §5.2 mà chưa đo nó · test skip im lặng hai ngày · 15 kỳ vọng suýt viết theo impl.
Đánh giá security ghi nguyên văn:
> Đây là dấu hiệu **kiến trúc phân-vai ĐANG CHẠY**, không phải dấu hiệu đội cẩu thả. Một đội không
> có cơ chế đối kháng thì các lỗi này **không được PHÁT HIỆN**, chứ không phải không xảy ra.

**Và cả sáu ca đều do CHÍNH NGƯỜI MẮC tự bắt**, không phải do người khác soi ra — thứ khó có hơn cả
việc bắt được lỗi của nhau.

## Hoãn có chủ đích
- Hạ tầng đo temp=0/k≥3 (gói B2 HOLD, floor nhiễu 20/40) · reseed gộp (⚠️ gỡ lọc-A1 khi from_bank sửa) ·
  401/403 hai route OTP · B3 timezone (31 utcnow) · lộ trình EU/US G1(SLA)/G3(audit bất biến) — xem PO-TONG-KET.
