# Hồ sơ nghiệm thu ADR-044 (lỗi 5 — CSKH đọc hội thoại bot↔khách của vé bàn giao)

> Lead ráp 20/08/2026, theo yêu cầu PO-agent. Ráp ở scratchpad (vai Lead không có trong bảng vùng
> ghi §4) — PO-agent kiểm vật lý độc lập rồi land vào `docs/`.
> Nguồn: `docs/DECISIONS.md` ADR-044 (`427ebe6`) · nháp gốc `scratchpad/nhap-adr-044-CSKH-doc-hoi-thoai.md`.
> HEAD khi ráp: `c5a9eef`. Đây là yêu cầu PO thật đặt TRỰC TIẾP, đi qua §10 đủ 7 bước, không có
> đường tắt nào ở bất kỳ chỗ nào trong chuỗi này.

---

## 0. Một trang cho người quyết

**Đề nghị: ADR-044 ĐẠT CÓ ĐIỀU KIỆN — CSKH/supervisor đọc được hội thoại bot↔khách gốc của một vé
đã bàn giao, guard chính đứng vững qua ba lớp soi độc lập (Review/Bảo Mật/DevOps), cổng nghiệm thu
4/4 + ma trận authz 72/72 xanh trên ảnh đã dựng thật, xác nhận HAI LẦN độc lập. Điều kiện duy nhất
còn treo: bản vá rate-limit của Bảo Mật (`99e9d57`, 4.2) mới xanh trên cây làm việc, CHƯA vào ảnh
nào — chi tiết ranh giới bằng chứng ở §7/§8.**

**Điểm mạnh nhất của đợt này:** guard chính KHÔNG PHẢI "user_id khớp" (thứ gần như luôn đúng và
không chặn được gì thật, vì mọi cskh/supervisor vốn đã đọc được mọi ticket) — guard thật là
**route TUYỆT ĐỐI không nhận `thread_id` từ request dưới bất kỳ hình thức nào**, luôn suy từ
`ticket.complaint.thread_id` đọc từ DB. Hai ca đối chứng dương (gửi `thread_id` giả qua query VÀ
qua header) đều xác nhận route bỏ qua hoàn toàn — đây là bằng chứng HÀNH VI, không phải bằng chứng
hình dạng response.

**Ba phát hiện của ba vai khác nhau, đều đã xử trước khi merge — không có phát hiện nào bị gác lại
"để sau":**
1. Review — ca bất đối xứng khi checkpoint kết thúc ngay sau ToolMessage bàn giao (khai không vá,
   có cổng canh, `ae4bb3c`).
2. Bảo Mật — rate-limit sai ĐƠN VỊ, không sai con số (`20/minute` hiệu chuẩn cho tốc độ gõ, không
   phải tốc độ đọc transcript) → `5/minute` (`99e9d57`).
3. DevOps — race checkpointer trên DB rỗng khi scale multi-worker, cách ly bằng bước hâm nóng tuần
   tự (`8890cd9`).

**Còn treo, chưa đóng — KHÔNG thuộc phạm vi ADR-044:** cổng ghim OTP-hết-tươi (GĐ2.5, `_OTP_EXPIRED_ERROR`
chưa có field `loai`) và nhánh `/role/i` lỏng ở `ChatClient.tsx` — nợ CŨ hơn ADR-044, đang xử lý
song song, không liên quan tới thiết kế transcript.

---

## 1. §10 — đủ 7 bước, không đường tắt

| bước | việc | bằng chứng |
|---|---|---|
| 1 | Dừng lại, không sửa code trước | Nháp `scratchpad/nhap-adr-044-CSKH-doc-hoi-thoai.md` soạn trước mọi dòng code |
| 2 | Sửa `contracts/` | `7b1c90d` — `authority-matrix.yaml` 2.0.0→2.1.0, + route `GET /tickets/{ticket_id}/transcript` |
| 3 | Ghi ADR vào `docs/DECISIONS.md` | ADR-044, `427ebe6` |
| 4 | PO thật duyệt | PO thật duyệt **"như thiết kế"** (theo PO-agent, cùng đợt land `427ebe6`) |
| 5 | `check_contracts.py --update` | Commit kèm baseline (đúng bài học nợ cũ "đổi contract không kèm baseline") |
| 6 | Cập nhật `CONTRACT_VERSION` | `tests/test_invariants.py` — xanh sau khi cập nhật (72/72 ma trận authz) |
| 7 | Rồi mới code | Toàn bộ chuỗi commit dưới đây đến SAU bước 6 |

## 2. Chuỗi code — bước ①→⑤, một commit một trách nhiệm

```
7b1c90d  feat(contract): authority-matrix 2.0.0→2.1.0 — ADR-044 transcript route
f678119  feat(db): ADR-044 bước ① — complaints.thread_id + tickets.handoff_at
fab822c  feat(agents): ADR-044 bước ② — luồn thread_id 4 tầng vào Complaint
3fa30a4  feat(services): ADR-044 bước ③ — flag_human_handoff() ghi handoff_at
ac60e5e  fix(tests): _fake_build_agent nhận thêm thread_id= — call site thật đã truyền
e1db3af  feat(api): ADR-044 bước ④ — GET /tickets/{ticket_id}/transcript
247ad46  test(api): thêm GET /tickets/{id}/transcript vào ma trận authz (ADR-044)
a7ced9b  feat(ui): ADR-044 bước ⑤ — khối "Hội thoại với trợ lý" + vạch bàn giao
d0c772d  fix(ADR-044): khai + xử lý ca timeout-handoff không có vạch phân cách
c5a9eef  docs(adr044): khai UI hẹp hơn contract (MVP có chủ đích) + vé timeout không có vạch
99e9d57  fix(security): rate-limit transcript 20→5/minute — sai đơn vị, không sai số
ae4bb3c  test(regression): ca đối chứng checkpoint-kết-thúc-sau-ToolMessage-bàn-giao (Review)
d5a9581  test(api): 3 ca canh guard transcript bàn giao (QA/QC, chuẩn bị trước khi route tồn tại)
```

**Migration:** `a8b9c0d1e2f3` (2 cột nullable, không backfill — đúng tiền lệ A1-04: `Complaint.thread_id`,
`Ticket.handoff_at`). [ĐO] `alembic current` trong container ảnh `c5a9eef` → `a8b9c0d1e2f3 (head)`,
không lỗi — container **tự dậy lại được** sau restart (phép kiểm quyết định, khác hẳn "đúng code
chưa").

**Luồn `thread_id` — bốn tầng, không phải một chỗ sửa (đúng ước công sức nháp đã tự đo):**
`run_agent_turn` → `build_customer_tools(..., thread_id=...)` → tool `create_ticket` →
`create_ticket_with_fraud_check` → ghi `Complaint.thread_id` lúc INSERT.

## 3. Guard chính — bằng chứng hành vi, ba lớp độc lập cùng đóng

**Thiết kế (ADR-044, sửa theo Bảo Mật lúc soi nháp):** `thread_id` suy DUY NHẤT từ
`ticket.complaint.thread_id` đọc từ DB. Route **tuyệt đối không nhận** `thread_id` như tham số
request dưới bất kỳ hình thức nào (query/body/header). "user_id khớp" — đề xuất gốc của chính Bảo
Mật khi soi nháp — bị **loại bỏ hoàn toàn** ở bản thi hành thay vì hạ xuống 404-handler phụ, và Bảo
Mật tự nhận xét bản thi hành **tốt hơn đề xuất gốc của họ** (giữ một check vô tác dụng tạo cảm giác
an toàn giả).

**Ba lớp soi độc lập, không lớp nào chỉ đọc code tĩnh:**

1. **QA/QC (`d5a9581`)** — 2 ca đối chứng dương: gửi `thread_id` giả qua QUERY, qua HEADER. Cả hai
   [ĐO] route bỏ qua hoàn toàn, response giống hệt nhau dù có/không kèm tham số lạ.
2. **Review** — soi đường GHI `Complaint.thread_id` (không chỉ đường ĐỌC như QA/QC), xác nhận field
   được set đúng lúc tạo, không có đường ghi đè sau đó.
3. **Bảo Mật** — xác nhận cơ chế Pydantic đúng: `CreateTicketRequest` KHÔNG có `extra="forbid"`
   ⟹ Pydantic v2 mặc định `ignore` — field lạ client gửi kèm **rơi mất lặng lẽ**, route không bao
   giờ thấy nó. *(Đính chính: Review ban đầu nói "Pydantic chặn" — kết luận an toàn không đổi
   nhưng CƠ CHẾ khác; biết đúng cơ chế mới biết nó còn đúng khi ai đó đổi schema sau này.)*

**Ca thứ ba, vé cũ:** `[ĐO]` `create_ticket` hiện tại chưa truyền `thread_id` ở một số call site cũ
⟹ vé tạo trước ADR-044 tự nhiên là ca "vé cũ" — `transcript: null` kèm lý do rõ ràng, KHÔNG đoán
theo mốc thời gian gần nhất.

**Ca thứ tư, `handoff_at`:** ghi đúng lúc `flag_human_handoff()`/`request_human_handoff` chạy —
tách rõ mốc TẠO ticket khỏi mốc BÀN GIAO, không đo trùng một dấu thời gian (đọc lại qua
`expire_all()`, Luật 19, tránh đọc cache session).

## 4. Ba phát hiện — mỗi cái một vai, mỗi cái đã xử

### 4.1 Review — bất đối xứng checkpoint/ToolMessage bàn giao

Checkpoint LangGraph có thể kết thúc NGAY SAU ToolMessage bàn giao (trước khi model kịp trả lời câu
tiếp theo trong cùng lượt) — case biên khi khách yêu cầu gặp người thật và ngắt phiên ngay lập tức.
**Khai không vá** (hành vi hợp lệ của hệ thống, không phải bug), nhưng cần **cổng canh** để nếu sau
này có refactor vô tình đổi hành vi, ca phải đỏ. QA/QC viết ca hồi quy đúng seam Coder khai
(monkeypatch `_CHECKPOINTER.get_tuple`), assert đủ hai vế (`chi_so_bang_giao is None` VÀ mọi lượt
`co_goi_tool=False`) — **5/5 xanh** (`ae4bb3c`).

### 4.2 Bảo Mật — rate-limit sai đơn vị

`main.py:816` route transcript ban đầu dùng `@limiter.limit("20/minute")`, chép nguyên từ
`/agent/chat`. Bảo Mật chỉ ra: `20/minute` hiệu chuẩn cho **tốc độ GÕ của khách** (một tin nhắn ~3
giây); route transcript trả lời câu khác — **tốc độ CSKH ĐỌC+XỬ LÝ một hội thoại đầy đủ** (tối
thiểu ~30 giây/hội thoại theo lập luận PO-agent) trước khi hợp lý mở cái tiếp theo. Sai đơn vị,
không sai con số — cùng lớp lỗi "tên giống nhau, vật khác nhau" cả đội gặp trong ngày.

Ước exfiltration (Bảo Mật, khai rõ là ƯỚC không phải ĐO): một credential CSKH bị lộ ⟹ tới
1.200 transcript/giờ ở ngưỡng cũ — đủ nhanh cho khai thác có ý nghĩa.

**Quyết định vận hành** (Lead trả lời, có căn cứ tài liệu — không suy đoán thay CSKH thật): tra
`docs/*.md` + `contracts/*.yaml` KHÔNG có kịch bản "rà backlog đầu ca"/"duyệt hàng loạt" nào được
khai. Duyệt resolution đã là hành động một-lần-một qua OTP step-up (ràng buộc cứng 1), không có
"duyệt hàng loạt" ở tầng thiết kế. Rà backlog hợp lý ở tầng liệt kê (`GET /tickets`, route khác,
không giới hạn theo cách này), không phải mở transcript ĐẦY ĐỦ của mọi vé. ⟹ **`5/minute`**
(`99e9d57`) — nợ RẺ, ĐẢO NGƯỢC được nếu 150-user test lộ ra nhịp dùng thật khác.

⚠️ **[ĐO] `99e9d57` CHƯA vào ảnh `c5a9eef`** — `docker exec fin05-backend-1 grep -n "minute" /app/src/api/main.py` vẫn ra
`20/minute` ở route transcript. Bản vá xanh trên cây làm việc, CHƯA chạy trong một vật nào. Chi tiết
ranh giới bằng chứng xem §7.

🔴 **Tự khai của PO-agent, đừng để thành lỗi của Coder:** ADR-044 mục 6 (bản gốc PO-agent viết)
ghi *"rate limit tái dùng cái đã có"* — thiếu vế *"ngưỡng phải hiệu chuẩn lại cho mục đích mới"*.
Coder làm ĐÚNG CHỮ đã viết. Lỗi đơn vị nằm ở văn bản ADR, không nằm ở người thi hành.

### 4.3 DevOps — race checkpointer trên DB rỗng

Phát hiện KHẨN trong lúc dựng: `alembic_version` DB đã stamp `a8b9c0d1e2f3` (chạy từ host) nhưng
ẢNH backend đang chạy lúc đó KHÔNG chứa file migration đó — restart tiếp theo sẽ crash-loop
(entrypoint chạy `alembic upgrade head` trước uvicorn, không tìm thấy revision). Vá bằng bước hâm
nóng TUẦN TỰ (`8890cd9`): `python3 -c "import src.agents.graph as g; g.close_checkpointer()"` chạy
MỘT LẦN ngoài mọi worker, giữa `alembic upgrade head` và spawn uvicorn — tránh N worker cùng đua
`PostgresSaver.setup()` trên DB rỗng (N-1 worker crash `UniqueViolation` trên `pg_type`).

**Có cặp trước/sau** — dòng sổ Luật W ghi cả sự kiện phát hiện lẫn sự kiện vá, không chỉ kết quả
cuối.

## 5. Hai khai báo lệch có chủ đích — không phải bug

1. **UI hẹp hơn contract, CÓ CHỦ ĐÍCH (MVP).** Contract định nghĩa route đủ, UI hiện tại chỉ hiển
   thị đường chính (khối "Hội thoại với trợ lý" + vạch bàn giao) — chưa có mọi nhánh phụ. Khai
   trong `c5a9eef`.
2. **Vé sinh từ nhánh timeout có `handoff_at` nhưng KHÔNG có vạch phân cách** — đúng, không phải
   bug: nhánh timeout không đi qua đúng luồng UI đặt vạch, đã có dòng giải thích trên UI
   (`d0c772d`).

## 6. Dựng ảnh — kiểm bằng phép QUYẾT ĐỊNH, không chỉ phép "đúng code"

**Bài học rút ra giữa đợt này** (PO-agent, sau sự cố DB-đi-trước-ảnh của DevOps): có HAI câu hỏi
khác nhau khi dựng ảnh — *"đúng code chưa"* (băm nguồn, BUILD_COMMIT, grep bundle) và *"container
có tự dậy lại được không"* (`alembic current` — phép QUYẾT ĐỊNH). Sáng nay suýt mất dịch vụ vì chỉ
hỏi câu thứ hai.

**Ảnh `c5a9eef` — 4 phép kiểm dựng, [ĐO] Lead, cả 4 ĐẠT:**
```
① alembic current (container)   a8b9c0d1e2f3 (head), KHÔNG lỗi     ← phép QUYẾT ĐỊNH
② BUILD_COMMIT                  c5a9eef == HEAD
③ grep "Hội thoại với trợ lý"  có trong 2 file bundle (SSR+static)
④ LLM_MODEL_POOL                4 phần tử, đúng bể GĐ3
```

**Sự cố nhỏ trong lúc dựng, đã đóng:** dòng sổ giám hộ hồi tố của DevOps ghi nhầm `.Id` (container
ID) vào cột "image ID" thay vì `.Image` — hai trường cùng dạng 12-hex, cùng "trông như image ID".
Lead bắt bằng đối chiếu `StartedAt` (khớp tới mili-giây ⟹ chắc chắn cùng container ⟹ `.Image`
KHÔNG THỂ khác), DevOps đo lại xác nhận, tự sửa + rút luật riêng: mọi số vào sổ phải ghi kèm TÊN
TRƯỜNG `docker inspect` đã dùng, không chỉ con số. Không ảnh hưởng kết luận cuối — ảnh đúng, sổ
đúng sau khi sửa.

## 7. Cổng nghiệm thu — chạy trên ảnh thật, xác nhận HAI LẦN độc lập

```
tests/test_api/test_adr044_transcript_bang_giao.py — 4/4 PASSED
  ✅ route bỏ qua thread_id gửi qua QUERY       (guard chính)
  ✅ route bỏ qua thread_id gửi qua HEADER      (guard chính)
  ✅ vé không có thread_id → transcript=null kèm lý do
  ✅ handoff_at ghi đúng lúc bàn giao, không phải lúc tạo ticket

tests/test_api/test_authz_matrix.py — 72/72 PASSED (gồm route mới)
```

QA/QC chạy HAI LẦN độc lập (host venv + `docker exec` thẳng vào container ảnh `c5a9eef`) — khớp
tuyệt đối cả hai nơi. Tự kiểm trước: `sample_db` fixture cô lập qua SQLite tạm, không chạm Postgres
thật dù `DATABASE_URL` trong container trỏ production — không dữ liệu demo nào bị đụng.

⚠️ **Ranh giới bằng chứng:** cổng ở trên chạy trên ảnh `c5a9eef`, **KHÔNG bao gồm `99e9d57`** (siết
rate-limit 20→5/minute, mục 4.2). [ĐO] `docker exec fin05-backend-1 grep -n "minute" /app/src/api/main.py`
— route transcript trong ảnh đang chạy vẫn `20/minute`. Bản vá `99e9d57` **xanh trên cây làm việc,
CHƯA chạy trong ảnh nào** — đang chờ lượt dựng kế tiếp. ⟹ **ADR-044 ĐẠT về CODE và về ba phát hiện
đầu (Review/DevOps + guard chính); vế 4.2 (Bảo Mật) đạt về code, CHƯA nghiệm thu trong vật.** Ô
này đóng sau lượt dựng của DevOps — PO-agent tự đóng khi đó, không lặp lại việc này.

## 8. Định nghĩa xong

- [x] §10 đủ 7 bước, PO thật duyệt "như thiết kế" trước khi Coder chạm `contracts/`
- [x] Migration 2 cột, không backfill, `alembic current` = head trong ảnh dựng thật
- [x] Guard chính: 2 ca đối chứng dương (query + header) xác nhận route bỏ qua `thread_id` client gửi
- [x] Vé cũ → `transcript: null` kèm lý do · `handoff_at` ghi đúng lúc bàn giao
- [x] Ba phát hiện độc lập (Review/Bảo Mật/DevOps) đều đã xử — Review+DevOps đã nghiệm thu TRONG ảnh,
      Bảo Mật (4.2) đã xử về CODE, CHƯA nghiệm thu trong ảnh (xem §7)
- [x] UI khối "Hội thoại với trợ lý" + vạch bàn giao, hai khai báo lệch có chủ đích đã ghi rõ
- [x] Cổng nghiệm thu 4/4 + ma trận authz 72/72, xác nhận HAI LẦN độc lập trên ảnh thật
- [ ] **Ngoài phạm vi ADR-044, KHÔNG chặn merge:** cổng ghim OTP-hết-tươi GĐ2.5 + nhánh `/role/i`
      — nợ đang xử song song, xem brief riêng, không liên quan thiết kế transcript

**Kết luận: ADR-044 ĐẠT CÓ ĐIỀU KIỆN.** Điều kiện là lượt dựng tới mang `99e9d57` vào ảnh — mọi
phần khác (contract, migration, guard chính, luồn thread_id, UI, hai phát hiện Review+DevOps) đã
nghiệm thu đầy đủ trong vật thật, không còn điều kiện nào treo.

**→ PO-agent kiểm vật lý độc lập → mời PO thật xem trên giao diện thật (họ đặt hàng trực tiếp,
nên là người xem nó chạy) — có thể xem NGAY, ô 4.2 không chặn việc xem giao diện, chỉ chặn dòng
"đã nghiệm thu trong vật" cho riêng phát hiện đó.**


---

## ✍️ CHỮ KÝ — PO-agent, sau kiểm vật lý độc lập

**ADR-044: ĐẠT CÓ ĐIỀU KIỆN.** Ký sau khi tự đo lại bằng dụng cụ của mình:
```
contract   authority-matrix.yaml 2.1.0 · 34 route · "transcript" ×3 · baseline commit KÈM  ✅
guard      def get_ticket_transcript(request, ticket_id, current_user, session)
           → KHÔNG tham số nào nhận thread_id (query/header/body)                          ✅
route sống openapi.json → /tickets/{ticket_id}/transcript                                  ✅
gọi THẬT   login cskh 0353000201 → GET …/transcript → transcript:null + ly_do đúng thiết kế ✅
cổng       test_adr044 + test_authz_matrix + test_invariants → 99 passed                   ✅
migration  alembic current TRONG container = a8b9c0d1e2f3 (head)                           ✅
⚠️ 99e9d57 (rate-limit 20→5/minute) CHƯA vào ảnh — grep "5/minute" trong container = 0
```

**ĐIỀU KIỆN DUY NHẤT còn treo:** lượt dựng ảnh tới mang `99e9d57`. Mọi phần khác — contract,
migration, guard, luồn `thread_id` bốn tầng, `handoff_at`, route, UI, cùng ba phát hiện của
Review/Bảo Mật/DevOps — **không còn điều kiện nào**.

**Điều tôi ký cùng, không tách ra phụ lục:** §4.2 ghi **nguyên văn tự khai của PO-agent** rằng
ADR-044 mục 6 do tôi viết (*"rate limit tái dùng cái đã có"*) **thiếu vế** *"ngưỡng phải hiệu chuẩn
lại cho mục đích mới"* — Coder làm đúng chữ của tôi, lỗi thuộc về chữ ấy. Và §6 ghi cả **sự cố
`.Id`/`.Image`** trong sổ giám hộ thay vì giấu.

**Một hồ sơ ghi cả những lần suýt sai của người ký đáng tin hơn một hồ sơ chỉ ghi kết quả.**


---

## 🟢 ĐÓNG Ô TREO — 20/08, sau lượt dựng `cbeb02c`

**Điều kiện duy nhất còn treo (`99e9d57` chưa vào ảnh) NAY ĐÃ ĐÓNG.** [ĐO PO-agent, độc lập]:
```
băm nguồn host == container   6722ab874767   ·  BUILD_COMMIT cbeb02c
backend   grep "5/minute" ×3          ← bản vá Bảo Mật ĐÃ vào ảnh
backend   grep "otp_het_tuoi" ×1      ← nợ GĐ2.5 ĐÃ vào ảnh
frontend  grep "Cần role thuộc" — 2 file bundle (SSR + static)
log khởi động  4× "Started server process" · 0 traceback · 0 UniqueViolation
đường khách    login → agent trả lời thật → tool_calls là list
QA/QC          cổng 403-role chạy lại NGUYÊN FILE trên ảnh mới → 4/4 XANH (gồm ca ③ KHÔNG RÕ)
```
⟹ **ADR-044: ĐẠT, không còn điều kiện nào.**

🔴 **Phép kiểm không lặp lại được, ghi riêng:** bản vá race checkpointer (`8890cd9`) trước nay chỉ
chứng minh trên **DB rỗng**. Lượt dựng này chạy trên `fin05` — **DB đã init từ lâu** — và cho
**4/4 worker sạch, 0 lỗi**. Đó là chiều kiểm ngược lại (**không hồi quy**), chỉ lượt dựng này mới có.

---

## ⚠️ ĐÍNH CHÍNH LIÊN QUAN — "MT-F01/MT-F02 chưa chạy được" là câu SAI của PO-agent

**Niêm tại chỗ, không xoá — câu này đã rời khỏi đội (vào hồ sơ GĐ3) nên phải để lại dấu.**

**Câu sai:** *"Hai ca `MT-F01`/`MT-F02` không chạy được vì lược đồ `kich_ban_leo_thang` chưa có runner
— khai CHƯA CHẠY ĐƯỢC, không gộp vào đã-chạy."* (PO-agent chốt 19/08)

**[ĐO QA/QC, PO-agent kiểm lại độc lập — khớp]:**
```
eval/_harness.py:531   kich_ban = list(case.get("kich_ban_leo_thang") or case.get("utterances") or [])
                       ⟹ runner ĐỌC kich_ban_leo_thang TRƯỚC, có fallback — KHÔNG thiếu gì
eval/results/adversarial_run_20260815_053214_raw.json
   MT-F01  so_luot_da_chay=3  passed=True  violations=[]
   MT-F02  so_luot_da_chay=3  passed=True  violations=[]
⟹ HAI CA ĐÃ CHẠY THẬT NGÀY 15/08 VÀ ĐẠT. Không có runner nào phải viết.
```

🔴 **Truy nguồn sai — đây mới là phần đáng giữ:** Lead đo **CORPUS** (đúng: hai ca có `utterances`
rỗng, dùng lược đồ khác) rồi **GIẢ ĐỊNH hành vi runner mà không mở `_harness.py`**. PO-agent **nhận
giả định đó, không kiểm**, ra quyết định và đưa vào hồ sơ.
⟹ **Một quan sát ĐÚNG + một giả định CHƯA KIỂM = một kết luận SAI trông rất có cơ sở.** Nó sống
**năm ngày** vì không ai mở `eval/results/` — thứ có sẵn, miễn phí, và QA/QC làm đầu tiên.

**Và nhiều khả năng đây là nơi câu sai ra đời** [ĐO]: cùng ngày 15/08 có ba lần chạy —
`011116` (MT-F01 `so_luot=0, passed=False`) · `011505` (`IntegrityError FOREIGN KEY constraint
failed`) · `053214` (**3 lượt, passed**). Ai đó nhìn **một lần chạy hỏng vì hạ tầng test** rồi ghi
"chưa chạy được", và trạng thái ấy **sống tiếp sau khi thực tế đã đổi**. Đúng thứ **Luật P** sinh ra
để chống — trạng thái làm cũ mà không ai niêm.

**Hành vi đáng nhân bản (QA/QC):** họ **từ chối viết code cho một vấn đề không xác minh được là có
thật**, và đọc `eval/results/` trước khi tin một mô tả. Tiết kiệm một buổi làm việc cho một runner
đã tồn tại.
