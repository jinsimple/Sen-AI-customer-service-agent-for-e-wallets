# Bàn giao — vai coder (tech-lead), phiên 17/08/2026

Viết cho **người đọc nguội**: bạn không có gì trong đầu, chỉ có repo này.
Mọi số dưới đây **đo lúc viết**, không nhớ lại. Nằm trong `scripts/` vì đó là
vùng ghi của vai này (`docs/` thuộc PO — xem `CLAUDE.md` §4).

---

## ① Trạng thái VẬT lúc bàn giao

    HEAD                4ac2162
    băm src/            b8e7c5397457     (sha256 nội dung mọi src/**/*.py, 12 hex)

    container            BUILD_COMMIT  nhãn ảnh      sửa-tay  lệch  PHAN_LUONG  SUY_LUAN
    fin05-backend-1      bec7235       b8e7c5397457    0       0        1       (trống=bật)
    fin05ttl-backend-1   bec7235       b8e7c5397457    0       0        1       (trống=bật)
    fin05do-backend-1    bec7235       b8e7c5397457    0       0        1       (trống=bật)

    sổ usage (fin05):    88 dòng, /app/logs/usage.jsonl (volume, sống qua recreate)

⚠️ `BUILD_COMMIT=bec7235` **cũ hơn HEAD=4ac2162** — bình thường: các commit sau
`bec7235` **không chạm `src/`** (nhãn băm khớp cả ba, đó mới là bằng chứng).
**`build_commit` định danh KHO, nhãn băm định danh MÃ.** Tin nhãn băm.

**Cây làm việc có 2 mục, KHÔNG phải của vai này:**

    D  .DANG-DONG-BANG-LLM                            ← xem ④
    R  docs/STATE.md -> docs/nhat-ky/2026-08-17-...    ← PO đang dựng lại

---

## ② Việc đang dở giữa chừng

**KHÔNG CÓ.** Không file nào sửa dở, không commit nào treo, `docker diff` sạch
cả ba. Mọi thứ đã land hoặc đã khai là "chưa làm, chờ ai".

---

## ③ Nếu phiên không bị tắt, tôi làm gì tiếp — theo thứ tự của tôi

1. **Bất biến chống lặp lời gọi** *(xem ④ · livelock)* — `cùng tool + cùng
   tham số + cùng lỗi ⟹ lần thứ hai DỪNG`. Tất định, không cần hiệu chuẩn.
   Land được **một mình** (không cần phần "nói gì với khách"), vẫn ăn trọn
   phần tiết kiệm.
2. **Chờ tester** đo hình dạng lỗ `path_traversal` ở `/policy-docs` rồi vá —
   `src/rag/ingest.py` là vùng này. **Đừng vá mù.**
3. **Chờ PO thật** cho ADR-031 (đang 🔴 TẠM DỪNG THI HÀNH, xem ⑥).
4. A2 (thêm tiền đề "khách đồng ý" vào bước 4 của prompt) — chờ tester dựng
   được nền hợp lệ.

---

## ④ Thứ chỉ tồn tại trong đầu — đọc kỹ mục này nhất

### Ba ngăn xếp, và cái bẫy `-p`

`docker-compose.yml` ghi cứng `name: fin05`. **Thiếu `-p` là đè lên ngăn xếp
demo** — đã làm chết stack chính 2 phút. Lấy lệnh từ nhãn container, đừng gõ
từ trí nhớ:

    docker inspect <c> --format '{{index .Config.Labels "com.docker.compose.project.config_files"}}'

    fin05     -f docker-compose.yml                                  demo, kho RAG 378 chunk
    fin05ttl  -f docker-compose.yml -f docker-compose.ttl-test.yml   đo auth, kho 419 chunk (.pdf!)
    fin05do   -f docker-compose.yml -f docker-compose.do.yml         đo, kho **RỖNG (0 chunk)**

🔴 **`fin05do` có kho RAG rỗng** ⟹ `search_policy` ở đó **luôn** `not_found`.
Một lượt đo trên `do` sẽ cho tổng token thấp hơn ~16% và **không nói gì** về
đường chính sách. Đã cắn một lần (40.032 vs 47.878).

🔴 **`fin05` và `fin05ttl` dùng HAI ĐỊNH DẠNG NGUỒN khác nhau** cho cùng bộ tài
liệu: `fin05` nạp từ `.docx` (đi qua parser có đòn 4b — bảng thành dòng tự mô
tả), `ttl` nạp từ `.pdf` (**không** qua parser đó, và có chunk là **mục lục
toàn dấu chấm** = rác truy hồi). **`fin05` là kho chuẩn.** Mọi phép kiểm chính
sách chạy trên `ttl` là đo một kho chưa vá.

### Đừng gõ vòng lặp shell gọi `docker compose`

Hỏng tham số `-f` **hai lần** trong một buổi. Gõ thẳng từng lệnh.

### Đừng nuốt output

`... >/dev/null` một lần làm tôi đọc trạng thái cũ thành kết quả mới: lệnh
compose **không chạy**, bảng vẫn in ra số của lần trước, và tôi suýt kết luận
"bản vá không hoạt động".

### Chạy test: từ HOST hay trong container?

    tests/ gọi `docker` CLI  ⟹  chạy từ **HOST**
      python: /Users/soidoc/Code/Projects/P-121-new/.venv/bin/python  (⚠️ có lịch xoá)
      env bắt buộc: JWT_SECRET_KEY(≥32 ký tự) · REDIS_URL=fake://ci
                    FIELD_ENCRYPTION_KEY(Fernet.generate_key()) · OPENAI_API_KEY=gia

    tests/test_invariants.py + scripts/check_contracts.py ⟹ chạy TRONG container
      docker exec fin05-backend-1 python -m pytest /app/tests/test_invariants.py -q

🔴 **ĐỪNG chạy `pytest tests/` toàn bộ.** `tests/test_f31_f32_duong_agent_that.py`
gọi LLM **thật** và **chưa có cổng chi phí** (tester biết, chưa sửa — `tests/`
là vùng họ). Hôm nay nó tình cờ tốn 0 vì rơi vào đường nhẹ/fallback. Chạy từng
file, hoặc `--deselect` nó.

### Bước ĐO không được ghi vào container — nhưng đôi khi buộc phải

`ruff`/`pytest` chỉ có đủ phụ thuộc **trong ảnh**, nên tôi `docker cp` để lint.
Hệ quả: tôi **tự tạo** `sửa-tay=1` trên `fin05` và chỉ phát hiện khi đi trả lời
một câu khác. ⟹ **Chạy `docker diff` như một bước trong CHÍNH BÁO CÁO**, không
để trong trí nhớ.

    docker diff <c> | grep -E '^C /app/src.*\.py$' | grep -v __pycache__

⚠️ Bản **thô** (`grep '^C /app/src'`) kêu ở **mọi** lần chạy bình thường
(`__pycache__`, thư mục) — một cái còi kêu bừa là cái còi bị tắt. Dùng bản lọc.

⚠️ Và `docker diff` bắt drift **mã**, **không** bắt drift **phụ thuộc**: cài
gói vào `site-packages` lọt hoàn toàn. Thử nghiệm nặng ⟹ **container vứt đi**
riêng (đã làm với `semantic-router`: `docker run -d --name <tên-có-vut-di>
python:3.12-slim sleep infinity`).

### Trông như bug mà không phải

· **`fin05do` chỉ có `create_ticket` trong `tool_results`** → không phải "không
  ghi", là **vắng mặt lưu lượng**. Đã kiểm: gọi tool trực tiếp ở đó ghi bình
  thường.
· **`agent_recursion_limit_reached` chưa bao giờ bắn** → trần 20, hành vi thật
  ≤8. Không phải guard chết; nó là guard **đúng** cho ca livelock, đặt sai số.
· **`build_commit` cũ hơn HEAD** → xem ①.
· **Cổng đỏ sau khi đổi contract** (`test_bo_test_nay_khong_loi_thoi`) → cơ chế
  chống-drift đang **làm đúng việc**. Xem ⑥ (§3 bước 6).
· **`test_injection.py` không tồn tại** → đường thật là `tests/test_api/test_injection.py`.

### Chỗ đã thử và THẤT BẠI — đừng thử lại

· **Dời `{current_time}` xuống cuối prompt để cứu prefix cache** — đo: cache
  85,0% → 86,3%. **Đã revert.** Lý lẽ tĩnh rất thuyết phục (`current_time` ở
  byte 208/15.094) nhưng phần lớn cache hit là **trong cùng một lượt**, không
  liên lượt. Bản vá đúng có thể là **giảm ĐỘ PHÂN GIẢI** (chỉ ngày), chưa đo,
  và **đổi hành vi**.
· **`semantic-router` + encoder cục bộ** — đo: greenfield **~609MB**, trong đó
  `litellm` **115M** (cổng gọi 100+ nhà cung cấp LLM, ta không dùng dòng nào).
  Ảnh sản phẩm hiện tại `site-packages` = **892M** ⟹ ngay cả bản gọn (~473M)
  là **+53%**. PO thật bác. Nếu mở lại: bỏ `semantic-router`, dùng `fastembed`
  trực tiếp (so cosine là `numpy.dot`).
· **Tool RAG** (chọn tool bằng vector store) — chỉ đáng khi có ≥15 tool. Ta có
  **5**. Không mở lại khi còn dưới 10.

### Livelock ở cổng OTP — chế độ hỏng đắt nhất đã tìm được

Chuỗi khôi phục từ PostgresSaver (`_CHECKPOINTER.get_tuple({'configurable':
{'thread_id': ...}})`), thread `USR-0001:1786976758`:

    khách hỏi (có mã giao dịch) → lookup_transaction
    → {"status":"error","message":"Khách chưa xác thực OTP phiên..."}
    → model gọi LẠI Y HỆT · 6 lần cùng tham số · 8 tool call tổng
    → hết giờ 46s → nhánh fallback tạo VÉ → sổ ghi total_tokens = 0

**Vì sao model không dừng:** nó **không có tool nào để xin OTP** (đúng thiết
kế — OTP ở tầng HTTP), nên nó không sửa được điều kiện, và **không có luật nào
bảo nó dừng**.

⚠️ Nhưng **1/13** ca gặp lỗi OTP mới lặp; 12 ca kia dừng sau **một** lần và xử
lý **đúng** (trả lời khách · tạo vé · bàn giao). So 6 biến giữa ca lặp và 12 ca
kia: **không biến nào tách được**, và có **2 ca giống hệt** cho kết quả khác
nhau. ⟹ Không có điều kiện đầu vào để chặn; **chỉ bất biến tất định mới đóng
được cửa này**.

### Cổng OTP từ chối TRƯỚC `record_tool_result`

⟹ Tool bị chặn **không sinh `ToolResult`**. Đừng suy "không có `ToolResult`
⟹ không có tool call" — **tôi suy thế hai lần và sai cả hai**.

### `request_human_handoff` KHÔNG ghi `ToolResult`

Tool duy nhất trong 5 tool không gọi `record_tool_result`, dù
`src/tools/base.py:3` viết *"Mọi tool PHẢI gọi..."*. Vé sinh qua đường handoff
**không có `tool_result_id` nào trỏ về hành động tạo ra nó**. ADR-029 mục 2b.

### `phien_do.py` — bắt buộc cho mọi lượt HTTP

    docker exec <c> python /app/scripts/phien_do.py --sdt 0387000001 --api http://localhost:8010

Không dùng nó ⟹ phiên **chưa xác thực OTP** ⟹ mọi tool tra cứu trả `error` ⟹
rơi vào livelock hoặc lượt vô nghĩa. **Tester mất 2 lượt đo vì chuyện này.**

⚠️ `fin05do`/`fin05ttl` **không publish cổng** ⟹ gọi HTTP từ **trong** container.

### Cờ đọc lúc import ⟹ đổi cờ = RECREATE

`PHAN_LUONG_BAT`, `SUY_LUAN_BAT` đọc lúc `import src.config`. `docker exec -e`
chỉ đổi **tiến trình con**, KHÔNG chạm uvicorn đang phục vụ.

⟹ **Xác minh cơ chế**: phải qua HTTP thật. **Chạy phép đo** bằng
`docker exec python`: `-e` là đủ và đúng (tiến trình mới, import mới).

---

## ⑤ Số đo được — kèm mẫu số và điều kiện

**Vật**: `qwen3.7-max` · dashscope · kho RAG `fin05` 378 chunk · băm src/ thay đổi
theo commit (ghi trong mỗi dòng sổ usage).

    phần cố định mỗi LỜI GỌI    prompt 4.587 + lược đồ 5 tool 1.978 = 6.565 token
                                (thước tiktoken/o200k_base — XẤP XỈ, xem dưới)
    "alo" đường đầy đủ          6.216 token vào · 8,7s      (k=1, HTTP thật)
    "alo" đường nhẹ             **0 token · 0,01–0,06s**    (k=4, HTTP thật, 2 ngăn xếp)

    hội thoại PO 5 lượt         87.470 token · 11 lời gọi · 81s   (R1, k=1)
    hội thoại đơn 4 lượt        46.909 token ·  6 lời gọi         (R1, k=1)
    cùng, T1 BẬT                31.193 token ·  4 lời gọi  = **−33,5%**  (R2, k=1)

**−33,5% là TẤT ĐỊNH** (2/4 lượt đi đường nhẹ = 0 token **theo cấu trúc**),
công bố được từ k=1.

🔴 **SÀN NHIỄU — số quan trọng nhất để đọc mọi phép đo khác:**

    cùng kịch bản, cùng vật, ba lần chạy: **14 · 11 · 11** lời gọi
    ⟹ dao động tự nhiên **≥3 lời gọi ≈ 20.000 token**
    ⟹ hiệu ứng nhỏ hơn thế KHÔNG kết luận được từ k=1

Ca thật: *"tắt suy luận tiết kiệm 32%"* (đo sáng) → đo lại chiều **−11%**, chỉ
vì vế đối chứng rơi vào 11 thay vì 14 lời gọi. **Con số đúng là −11%, k=1.**

**Độ trễ**, n=70 **lời gọi** (không phải lượt), từ 8 file R:

    p50 3,3s · p90 6,9s · p95 8,0s · p99 11,6s · max 11,6s
    ⚠️ **THIÊN LỆCH SỐNG SÓT**: chỉ lời gọi ĐÃ TRẢ VỀ mới có trường `giay`.
       "0/70 chạm trần 20s" gần như hằng đúng — không đọc nó thành "chưa bao giờ chậm".

**Ngân sách đồng thời** (ghép **theo từng lần chạy**, hai biến TƯƠNG QUAN —
đừng ghép chéo):

    lần chạy   tok/lượt  trần TPM(1M)  T hoà vốn  T thật  ai chặn  biên
    R1_po       17.494     57,2/ph       21,0s    16,2s    TPM    **1,30×**
    R2_po       17.327     57,7/ph       20,8s    14,8s    TPM      1,41×
    R3_po       15.397     64,9/ph       18,5s     7,4s    TPM      2,49×
    R1_don      11.727     85,3/ph       14,1s     8,2s    TPM      1,73×
    R2_don      15.596     64,1/ph       18,7s    10,7s    TPM      1,74×
    R3_don      15.380     65,0/ph       18,5s     7,5s    TPM      2,46×

**TPM chặn trước ở cả sáu.** Biên hẹp nhất `1,30×` ở kịch bản demo mặc định.

**Kích thước payload tool** (5.260 bản ghi `ToolResult.raw_json`, `fin05`):

    get_customer_history  trung vị 11.369 ký tự · p95 16.685   ← ĐÃ cắt khi vào context (~2.500)
    search_policy         trung vị  2.886 · n=4.613            ← CHƯA cắt
    lookup_transaction    trung vị    510
    create_ticket         trung vị    188

**tiktoken vs hoá đơn — KHÔNG có hệ số cố định.** Lệch **đảo dấu** trong cùng
một hội thoại: +5,7% ở lời gọi đầu (prompt tiếng Việt chiếm đa số) → −0,4% ở
lời gọi thứ 14 (lịch sử + JSON chiếm đa số). Dùng `usage` nhà cung cấp ở cột
chính; tiktoken chỉ để **ước trước khi bắn**.

**Hạn mức**: free quota tính **theo từng model**. `qwen3.8-max` đã cạn (403).
`qwen3.7-max` tiêu ~**750K/1M** ngày 17/08. Kiểm bằng một lượt tí hon trước khi
lên kế hoạch đo.

---

## ⑥ Điều KHÔNG kết luận — kèm hạng bằng chứng

**Livelock**
· [ĐO] cơ chế: 8 tool call, 6 lần cùng tham số, chuỗi khôi phục đủ từ checkpointer
· [ĐO] 1/13 ca gặp lỗi OTP thì lặp; 12 ca kia xử lý đúng
· [SUY LUẬN] *"khác biệt là ngẫu nhiên của model"* — **CHƯA chứng minh**. Đúng
  hơn: *"không tìm thấy điều kiện phân biệt trong **6 biến đã đo**, và có **2 ca
  giống hệt** cho kết quả khác nhau"*. Không đo: nhiệt độ sinh, thứ tự token,
  trạng thái nhà cung cấp.
· [SỐ HỌC] 1 lượt livelock ≈ 50–70K token. **Nhưng** lời gọi thứ 8 trả về SAU
  khi client bỏ — DashScope có tính tiền request client ngắt giữa chừng không:
  **KHÔNG BIẾT**, không đo được từ trong hệ thống.

**ADR-031 (`query` của `search_policy`) — 🔴 TẠM DỪNG THI HÀNH**
· [ĐO] tiền đề *"query chưa được lưu ở đâu"* **SAI**: `investigation_logs.
  tool_input_json` đã chứa `{"query": "..."}` plaintext, 10 dòng trên `fin05`.
· ⟹ Lỗ hẹp hơn ADR mô tả (chỉ ở lượt **không tạo vé**: 4.613 `tool_results` vs
  **10** dòng log), và vấn đề bảo mật **ngược lại** — chữ khách đã ở cột
  plaintext, chỉ ở bảng ta không nhìn.
· ⚠️ `tool_input_json` chứa input của **mọi** tool, gồm `lookup_transaction`
  (mã GD) và `get_customer_history` (SĐT, số tiền). **Chưa ai xử.**
· PO thật quyết ba việc: một bảng hay hai · thêm cột hay mở rộng cơ chế đã có ·
  `tool_input_json` plaintext xử riêng như finding bảo mật.

**`_AGENT_MAX_CONCURRENT = 20` — căn cứ đã chết**
· [ĐO] ba chỗ trong `src/` ghi *"hạn mức 200.000 TPM"* — đó là trần **OpenAI**;
  ta chạy Qwen trần **1M**. `src/rate_limit.py:62` · `src/api/main.py:379,621`.
· [ĐO] `20` hiện **vừa khít TÌNH CỜ** (bảng ở ⑤) — nếu đúng thì đúng vì một lý
  do **chưa ai viết ra**.
· ⚠️ `main.py:621` nói với khách *"vượt 200.000 TPM"* — **lý do sai** khách đọc
  được. Sửa được mà không cần đo, nhưng **đừng sửa lẻ** (đừng dựng ba ảnh vì
  một dòng chữ).
· **Cảnh báo có ngưỡng:** nếu `T` trung vị **của một lần chạy** vượt ~18s ⟹
  limiter thành nút thắt trước TPM ⟹ đo lại. **Lọc theo lần chạy, không theo
  nhãn kịch bản** — `R2_don` cho thấy nhãn nói sai (T1 bật làm token/lượt-còn-lại
  TĂNG dù tổng giảm).

**`path_traversal_filename_is_safe`**
· [ĐO] xanh sau `d0aabc0`. [TESTER] cùng gốc `KeyError`.
· 🔴 [TESTER] test đó chỉ kiểm `status_code in (200, 400)` — **chưa bao giờ
  kiểm có tệp nào ghi ra ngoài thư mục kho**. ⟹ `/policy-docs` **chưa có bằng
  chứng nào** về chống path traversal. **Đừng vá mù** — chờ tester đo hình dạng
  lỗ.
· Hình dạng đáng nhớ: **vá đúng một lỗi làm IM một cổng đang hỏng vì lý do
  khác** — cổng đỏ có người nhìn, cổng xanh thì không.

**`.DANG-DONG-BANG-LLM` bị xoá**
· [ĐO] tracked, **không commit nào xoá**, chỉ mất ở cây làm việc. `git clean`
  không đụng tracked; `checkout` thì khôi phục. ⟹ **không lệnh git nào tạo ra
  được trạng thái này** — nghi phạm là thao tác hệ tệp.
· Nội dung tệp tự khai *"XOÁ FILE NÀY KHI HẾT ĐÓNG BĂNG"* ⟹ xoá **có thể là
  thao tác đúng**. Không ai nhận. PO thật đang được hỏi.
· ⚠️ Tệp đó ghi *"trần TPM 200k"* — **con số đã chết**, cùng lỗi với mục trên.

**Chưa đo, cần lượt thật**
· `f` = tỉ lệ lượt "đơn" trong traffic thật — **không nguồn nào hiện có trả lời
  được**. `golden_set` có **0/120** lượt đơn (dựng để ép agent ⟹ loại lượt đơn
  **theo thiết kế**); lấy nó tính `f` sẽ ra ~0% và **bác oan** đòn bẩy tốt nhất.
· Tần suất livelock trên traffic thật (1/13 là mẫu nhỏ).
· Chất lượng khi `SUY_LUAN_BAT=0` — R3 ghi **4** dòng `investigation_logs` vs
  R1 **1** dòng. Chưa ai chấm. **Đừng đọc thành "tra kỹ hơn" hay "lan man hơn"**
  — `ToolResult` +4 **y hệt** cả ba vòng, chỉ khác tầng ghi chép.

---

## Lớp lỗi đắt nhất của ngày — bảy ca, ba người

**Suy từ một tập ĐÃ BỊ LỌC mà không khai bộ lọc.** Cả bảy lần bộ lọc **vô
hình** — không ai cố tình lọc, tập tự đến đã lọc rồi:

    chỉ lời gọi SỐNG SÓT mới sinh `giay`      → "0/70 chạm trần" gần như hằng đúng
    chỉ tool CHẠY mới sinh `ToolResult`       → "không ToolResult ⟹ không tool call" (SAI, 2 lần)
    `golden_set` loại lượt đơn theo thiết kế  → `f ≈ 0%`, bác oan
    120 ca nhưng **124** câu                  → `assert == 120` bỏ qua 4 câu
    lượt HỎNG ghi `so_luot_goi_model = 0`     → sổ mù với đúng loại lượt cần tìm
    chọn tay 3 điểm gần nhau rồi đo phương sai → "có một cái ghìm" (không có)
    `grep` thấy dòng 143 rồi dừng             → câu trả lời ở dòng 150

**Dấu hiệu duy nhất: dữ liệu trông quá gọn.** Khi một tập số sạch bất thường —
không ngoại lệ, không đuôi, một cực đại tròn trịa — hỏi **"cái gì đã KHÔNG sinh
ra dòng nào ở đây?"** trước khi hỏi "số này nói gì".

---

## Cơ chế tự canh đã dựng hôm nay — đừng gỡ

    src/dau_ma_nguon.py        băm nội dung src/, TỰ TÍNH trong Dockerfile (không build-arg)
                               `.bam_ma_nguon` rỗng/hỏng ⟹ TỪ CHỐI khởi động (fail-closed)
    ma_nguon_lech_anh          sự kiện ERROR lúc khởi động nếu mã chạy ≠ mã trong ảnh
    src/observability/so_usage.py  sổ JSONL trên volume, mang `bam_ma_nguon` + `base_url`
    kiểm mạch lạc ngân sách    OPENAI_TIMEOUT×(RETRIES+1) ≤ AGENT_TURN_TIMEOUT, fail-fast
    _agent_turn_limiter ttl    DẪN XUẤT từ AGENT_TURN_TIMEOUT (trước là hằng số 90 chết)
    scripts/xuat_luat_phan_luong.py  sinh bản luật cho tester TỪ src/ (một nguồn, một dẫn xuất)

**`None` trong sổ usage = KHÔNG ĐỌC ĐƯỢC**, không bao giờ = không có. Người đọc
sổ phải cộng **ba rổ riêng** (`đo được` · `không đọc được` · `đúng 0`) —
**KHÔNG** `sum(... or 0)`, vì `or 0` biến "không biết" thành "không tốn".
