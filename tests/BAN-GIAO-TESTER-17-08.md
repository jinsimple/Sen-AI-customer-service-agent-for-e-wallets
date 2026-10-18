# Bàn giao — vai TESTER, phiên 17/08/2026

> 🔴 **NIÊM 18/08/2026 — BA PHÁT BIỂU TRONG FILE NÀY ĐÃ BỊ ĐO KHÁC. Thân file
> giữ nguyên (đây là bản ghi lịch sử); đọc ba dòng dưới TRƯỚC khi trích bất cứ
> số nào.** *(Áp Luật P — nghi ngờ không tự lan sang artefact. Ba phát biểu này
> đã được nói là sai trong hội thoại 18/08 và vẫn đứng nguyên ở đây tới lúc
> niêm.)*
>
> | §  | file này nói | **[ĐO] 18/08** |
> |---|---|---|
> | ① | `1 failed · 567 passed · 40 skipped` | **`0 failed · 568 passed · 42 skipped · 11 xfailed`** |
> | ④ | `fin05ttl … kho RAG 419 chunk` | **0 chunk.** Cả hai collection rỗng; index thật có (188K) nên **không phải** soi nhầm path. Vì sao mất: **CHƯA TRUY** |
> | ⑥ | *"vì sao `test_kho_khong_chua_tai_lieu_noi_bo_da_biet` đỏ — **chưa truy**"* | **ĐÃ TRUY, và "kho rỗng" là SAI.** Đầu dò gõ cứng `get_collection('policy_faq')` — collection **rỗng duy nhất trong ba**. Kho thật có 378 chunk ở hai collection song song. Xem `eval/DU-BAO-2026-08-18-KHO-RAG-COLLECTION.md` |
>
> **Và một cảnh báo file này KHÔNG có, vì chưa ai biết lúc viết:**
> `tests/test_api/test_injection.py` gọi **OpenAI embeddings thật** qua
> `POST /policy-docs`, **không qua cổng chi phí nào** — nghĩa là câu *"`pytest
> tests/` mặc định KHÔNG tốn token"* ở §① **đúng cho 3 bộ đã khai, SAI cho
> suite**. Đã bịt ở `17d7706`.
>
> Phần còn lại của file (tài khoản hạt giống, `scripts/phien_do.py`, ba ngăn
> xếp, bốn chỗ bị hạ tầng lừa, cạm bẫy đo lường §⑦) **chưa có gì mâu thuẫn** —
> vẫn dùng được.


> Viết cho **người đọc nguội**: bạn không có gì trong đầu, chỉ có repo, và
> **không được đọc `src/`** (hiến pháp §4). Mọi thứ dưới đây kiểm lại được.
>
> Đọc `CLAUDE.md` → `docs/STATE.md` → `tests/CHUAN-VIET-TEST.md` trước. File này
> là thứ **không nằm trong ba file đó**.

---

## ① Trạng thái bộ ca — đo lúc bàn giao

```
pytest tests/ -m "not security_finding"
  1 failed · 567 passed · 40 skipped · 1 deselected · 11 xfailed
```

**Ca đỏ duy nhất:** `tests/test_rag/test_thanh_phan_tai_lieu_kho.py::test_kho_khong_chua_tai_lieu_noi_bo_da_biet`
→ *"index KHÔNG có doc_id nào — kho rỗng"*. **Tôi chưa truy.** Đừng gán nguyên
nhân; xem §⑥.

### Cờ điều khiển — biết trước khi chạy

| cờ | mặc định | tác dụng |
|---|---|---|
| `FIN05_ALLOW_PAID_CALLS=1` | **TẮT** | bật 3 bộ **gọi LLM thật**: A2 (~42K) · định tuyến (~14K) · F-31/32 (~28K) |
| `.DANG-DONG-BANG-LLM` (tệp ở gốc repo) | **KHÔNG tồn tại** ⟹ cổng TẮT | tạo tệp = cấm mọi test gọi model |
| `FIN05_CHO_PHEP_EP_429=1` | TẮT | cho phép ép 429 — **đốt trần TPM dùng chung**, đừng bật khi ai đang demo |
| `FIN05_BASE_URL` | `https://localhost` | = ngăn xếp `fin05`. `:8443` = `fin05ttl` |

> 🔴 **`pytest tests/` mặc định KHÔNG tốn token.** Đó là kết quả của `5fbd01f`
> + `07ee30e` hôm nay. Trước đó nó **có** thể ra hoá đơn. Đừng gỡ cổng đó.

### 11 xfail(strict) — chúng đỏ NGƯỢC khi được vá

`xfail(strict)` XPASS ⟹ báo FAILED. **Đó là tín hiệu gỡ nhãn, không phải lỗi
mới.** Đọc `reason` của nó trước khi chẩn.

---

## ② Việc đang dở giữa chừng

**Không có việc viết dở.** Cây làm việc sạch, mọi thứ đã commit và push lên
`dev/learning-loop`.

Một thứ **đã viết xong nhưng chưa chạy**: `tests/test_a2_dong_y_truoc_khi_tao_ve.py`
— xem §③.

---

## ③ Việc sẽ làm ngay, theo thứ tự của tôi

**1. Thêm một assertion cho 6 cổng an toàn** (`eval/QUET-TEN-HUA-KHAC-ASSERTION.md`,
commit `4ac2162`). Quét **đã xong**, kết quả đã có, **chưa vá**. Sáu ca kiểm
`status_code` thay vì kiểm hiệu quả; **5/6 nằm trên đường duyệt HITL**. Mỗi ca
cần **một** dòng: trạng thái CSDL sau lời gọi, hoặc "không tệp nào ngoài thư
mục kho". 0 token. **Đây là việc số một.**

**2. Viết lại ca A2.** Bộ hiện tại **không chạm được điều kiện nó định canh**:
trên thread mới agent còn đang hỏi thêm, chưa đủ tiền đề để tới bước tạo vé, nên
`Δ=0` **trước** bản vá y hệt **sau** bản vá. Tôi đã thử nhét `trans_id` thật vào
câu hỏi — vẫn không tới (xem §④). **Chưa có ca tái hiện.**

**3. Chạy A2** khi có ca mới **và** sau khi coder land bản vá prompt + bộ số
thời gian. PO đã chốt: *quyết trọn → đổi một lần → đo lại nền → rồi mới chạy*.

**4. Nhịp gõ nhóm nhỏ** 5–10 người / 15 phút. **0 token, đòn bẩy lớn nhất trong
cả danh sách** — xem §⑤. Truy vấn đã sẵn, chạy trong vài phút khi có phiên
người thật.

---

## ④ Thứ chỉ tồn tại trong đầu tôi

### Chạy được `scripts/phien_do.py` — thiếu nó mất một giờ

```bash
python scripts/phien_do.py --sdt 0387000001
```
Tạo phiên **đã xác thực OTP** đi đúng ba bước sản phẩm. **Không có cờ
`SKIP_OTP` và PO đã cấm tạo một cái** — lý do: cờ đó xoá mất chính quan sát mà
cửa OTP đang cho ta.

### Tài khoản hạt giống

`USR-0001` · phone `0387000001` · mật khẩu `Demo@123` · **440 giao dịch**.
Trên `fin05do` và `fin05` đều có. Ví: `900000000001`.

Một giao dịch thật dùng được: `TXN20260731000566` · 177.000đ · `internal_wallet`
· status `success` (**không phải** `completed` — tôi mất một vòng vì đoán sai
tên trạng thái).

### Ba ngăn xếp — KHÁC NHAU, đừng gộp

```
fin05      cổng 80/443   kho RAG 378 chunk   ← ngăn xếp CHUẨN cho mọi phép đo RAG
fin05ttl   cổng 8443     kho RAG 419 chunk   ← kho dựng từ .pdf, CÓ chunk rác
                                               (mục lục toàn dấu chấm)
fin05do    KHÔNG cổng ra host   kho RỖNG     ← ngăn xếp ĐO DÙNG RIÊNG
```

> 🔴 **`fin05do` kho RỖNG** ⟹ `search_policy` ở đó **luôn** `not_found`. Mọi ca
> chạm chính sách chạy ở đó sẽ xanh/đỏ vì lý do không liên quan.
> 🔴 **378 ≠ 419** ⟹ hai người đo trên hai ngăn xếp sẽ ra hai đáp án cho **cùng
> một câu hỏi chính sách**, và cả hai đều "đo thật".

### Chạy test TỪ HOST, không phải trong container

Bốn bộ điều khiển container qua `docker exec`. Chạy chúng *bên trong* container
⟹ `FileNotFoundError: 'docker'`. Coder mất một vòng vì điều này; giờ đã ghi vào
docstring từng file.

### 🔴 Trông như bug mà KHÔNG phải

- **`create_ticket` trả `status=error` kèm thông điệp OTP** ⟹ **đúng**. Cửa OTP
  hoạt động ở tầng tool, không chỉ tầng HTTP. Truyền `otp_verified_at=time.time()`
  khi gọi tool trực tiếp.
- **`fin05do` có `tool_results` gần rỗng** ⟹ **không phải hỏng**. Là **vắng mặt
  lưu lượng**. Tôi đã suy sai chỗ này và suýt rút một finding thật.
- **Hai CHECK `scope` khác nhau** (`complaints` có `unknown`, `transactions`
  không) ⟹ **đúng thiết kế**, contract nói qua `rang_buoc_db`. Đừng "sửa cho đều".
- **`lookup_transaction` trả `found` khi gọi tay nhưng agent nói "chưa tra được"**
  ⟹ **chưa truy được**, xem §⑥.

### 🔴 Chỗ tôi bị hạ tầng lừa — cả bốn đều mất thời gian thật

1. **`docker exec -e BIẾN=…` KHÔNG đổi tiến trình đang phục vụ.** Nó chỉ đổi
   tiến trình con. Muốn đổi cờ của server ⟹ **recreate container**. Xác minh cờ
   phải qua **HTTP thật**, không qua `docker exec -e`.
2. **`git ≠ container`.** Hai lần trong ngày: bản vá `conftest` và code T1 nằm
   trong git mà **không** trong ảnh. Luôn kiểm trong container trước khi tin.
3. **`git checkout --` KHÔNG khôi phục tệp CHƯA từng commit.** Tôi chạy đột biến
   trên một file mới và suýt commit bản đã đột biến.
4. **`tests/conftest.py` từng gọi `flushdb()` lên Redis THẬT** — `cmdstat_flushdb
   calls=437`. Đã vá (`e9ae55a`): ép `REDIS_URL=fake://ci` **trước mọi import**.
   **Đừng gỡ.** Nó xoá phiên đăng nhập của mọi người đang dùng ngăn xếp.

### Ca đã thử và BỎ

- **Ép timeout bằng `AGENT_TURN_TIMEOUT_SECONDS=1`**: ép được (biến đọc từ env),
  nhưng cần recreate ⟹ **đổi vật** ⟹ phải nằm trong đợt đổi bộ số của coder,
  không làm riêng.
- **Đo trần RPM bằng thực nghiệm**: **không cần**. Số học đã trả lời (§⑤).
- **Đâm trần TPM hai model song song** để kiểm bucket độc lập: **không làm** —
  đốt hạn mức và **chặn phiên khác**.

### `scripts/` hay dùng

```
scripts/phien_do.py        phiên đã xác thực OTP (xem trên)
scripts/kho_rag.py         nạp/soi kho RAG · in "băm-chuẩn-hoá(md5,12)"
scripts/check_contracts.py phát hiện artefact lỗi thời so với contracts/
scripts/gen_dataset.py     sinh lại dữ liệu; CÓ cổng từ chối ghi đè eval/
```

### venv để chạy test

Repo **không có venv**. Tôi dùng
`/private/tmp/claude-501/…/3740554a-…/scratchpad/venv-fin05` — nó có `argon2`,
`tiktoken`, `yaml`. **Nó nằm trong thư mục tạm và có lịch xoá.** Người kế tiếp
nên dựng venv riêng thay vì mượn.

---

## ⑤ Số đo được — kèm mẫu số và điều kiện

> Con số không có mẫu số thì **đừng ghi**. Mọi dòng dưới đây có mẫu số.

### Token & thông lượng

```
14.198 token/lượt   ← 1 lượt đầy đủ THÀNH CÔNG qua /agent/chat, n=1, fin05do
                      ⚠️ TRUNG BÌNH LƯỢT THÀNH CÔNG. Lượt HỎNG tốn 50–70K.
                      ⟹ mọi trần tính từ số này là QUÁ LẠC QUAN.
 6.565 token/lượt   ← kích thích CỐ ĐỊNH (system 4.587 + lược đồ tool 1.978),
                      đo bằng tiktoken o200k_base. Đi kèm MỌI lượt đầy đủ.
 2,39 lời gọi/lượt  ← trung bình đo trước đó
     0 token        ← lượt đường NHẸ ("alo"), n≥13, đo trên usage.jsonl
```

### Trần — [SỐ HỌC] từ số đo được ÷ số tài liệu

```
TPM 1.000.000 ÷ 14.198  =  70,4 lượt/phút   ← TRẦN CHẠM TRƯỚC
RPM       600 ÷   2,39  = 251,0 lượt/phút
⟹ TPM chạm trước RPM 3,6 lần. RPM KHÔNG BAO GIỜ là trần chặn ở tải thực tế.

150 người × 0,50 lượt/ph =  75 lượt/ph → TPM 106% 🔴 → cần ≥  6,1% lượt đơn
150 người × 1,00 lượt/ph = 150         →     213% 🔴 → cần ≥ 53,0%
100 người × 0,50 lượt/ph =  50         →      71% ✅ → không cần gì
```

> 🔴 **Ta ĐÃ vượt trần ở đúng cấu hình buổi test 150 người**, ở nhịp **chậm hơn
> người dùng thật**. Biến quyết định là **NHỊP GÕ**, không phải code.

### Chấm quy tắc phân luồng — luật `sha256:84c476804d08 · md5:d3f822b9bc61`

```
bộ dương 20 câu [241851470116]   15/20   NGOÀI-TẬP=9 · CHỮ SỐ=6 · xã giao=5
bộ âm-ngắn 14   [e411a9dbcc74]   14/14   NGOÀI-TẬP=14
bộ âm gốc  124  [a5ea8c876df0]  124/124  CHỮ SỐ=103 · NGOÀI-TẬP=21
ĐC-1 ✅ 3/3 · ĐC-3 ✅ 10/10 · ĐC-4 ✅ 5/5 · ĐC-5 ✅ 138/138
```
Chạy lại: `python eval/cong_phan_luong.py --luat <đường dẫn>`

### Vé & bản ghi (trên `fin05`, tổng 761 vé)

```
~101–107 vé (≈14%)  KHÔNG phân biệt được "vé do hệ hỏng" với "vé do khách xin"
                    (`human_handoff_requested=true` đúng cho CẢ HAI)
2 lời gọi create_ticket  ⟹  2 VÉ  (KHÔNG có chống-trùng ở bất kỳ tầng nào)
nhánh fallback           ⟹  investigation_logs +0  (chuỗi truy vết đứt mắt ĐẦU)
```

### Sàn nhiễu

```
≥3 lời gọi model/lần chạy  ← 11 vs 14 cùng kịch bản
⟹ chênh nhỏ hơn 3 lời gọi KHÔNG đọc được từ một lần chạy mỗi cấu hình
±1 ca trên n=25 = ±4 điểm phần trăm  ← đo hai lượt riêng, cùng nhãn
```

---

## ⑥ Điều tôi KHÔNG kết luận

| | hạng | ghi chú |
|---|---|---|
| Vì sao `test_kho_khong_chua_tai_lieu_noi_bo_da_biet` đỏ | **chưa truy** | "kho rỗng". Không gán nguyên nhân. |
| `lookup_transaction` trả `found` khi gọi tay, agent nói "chưa tra được" | **chưa truy** | ① requester-is-party **đã bị loại bằng đo**. ② agent truyền tham số khác — chưa xác nhận. Tôi có `args` trong phản hồi HTTP mà **đã vứt đi**. |
| Cached token có bị trừ khỏi TPM không | **KHÔNG XÁC ĐỊNH ĐƯỢC** | Tài liệu **im lặng** ở tier thường; con số `×0.2` lưu hành là của **PTU — sản phẩm khác**. DashScope **không trả header hạn mức nào**. |
| Lượt timeout tiêu bao nhiêu token | [ĐO] **chắc chắn >0**, độ lớn **không biết** | DashScope trả `200 OK` **1,2s SAU** khi ta bỏ. Sổ ghi `0` là **cận dưới**. |
| Bucket TPM độc lập theo model | [TÀI LIỆU] | *"Each model has its own rate limit"*. **Chưa đo.** |
| Đổi vùng US mua `×5` (không phải `×50`) | [SỐ HỌC] | `50×` là tỉ lệ của **RPM — trục không chặn gì**. |
| Tỉ lệ lượt-đơn trong lưu lượng thật | **KHÔNG ĐO ĐƯỢC** | xem §⑦. |
| Chống-trùng `create_ticket` nên có không | **chờ PO thật** | Quy tắc **nghiệp vụ**, không phải kỹ thuật. |
| 3 ca `CHỜ PHÁN` nhánh khách-nói-sai | **chờ security/BA** | `eval/ca_moi_ba_nhanh_CHO_PHAN.json` |
| `RG-12/13` — biểu phí có phân hạng khách không | **chờ** | Kiểm bằng `/policy-search` trên **`fin05`**, sau khi PO mở cửa sổ. |

**Dấu vết tôi cố ý để lại, KHÔNG dọn:** 4 vé `[DO-LUONG cong-chong-trung]` trên
`fin05do` (`TCK-59807a7a80e1` · `TCK-e694e8dba004` · `TCK-6e24656773b9` ·
`TCK-6d34e9dc1c0e`) — **vật chứng** của finding không-có-chống-trùng. Dọn được
bằng bốn mã đó sau khi PO đọc xong.

---

## ⑦ 🔴 CẠM BẪY ĐO LƯỜNG — đọc trước khi tin bất kỳ con số xanh nào

### `eval/messages` KHÔNG phải lưu lượng thật

230 tin khách / 85 phiên, **do script sinh**. Bằng chứng: khoảng giữa hai tin
p10 = 3s · trung vị = 3s ⟹ **19,8 lượt/phút/người** — máy gõ ngay khi nhận xong
phản hồi. Và **script không bao giờ gõ "alo"**.

> 🔴 Người mới **sẽ** dùng bảng này làm mẫu lưu lượng thật. Đừng. Mọi tỉ lệ tính
> từ nó là **sàn giả**.

### Bộ ca của tôi là DÒ BIÊN, không phải MẪU ĐẠI DIỆN

`bo_ca_luot_don.json` có 9/20 nhãn `nhe` = 45%. **Đó là lựa chọn thiết kế**, cố
ý làm giàu ca hiểm. Đọc 45% thành tỉ lệ lưu lượng là dùng bộ dò-biên làm mẫu.
Áp cho **mọi** bộ ca trong `eval/`.

### Thước CHƯA hiệu chuẩn

- **Thước dò chuỗi** (ca A2 đối chứng, quan sát ⑤): bắt được cách diễn đạt
  thường, **không** bắt được cách lạ. Dùng để **không bỏ sót**, **không** dùng để
  khẳng định đạt. Mọi ca ĐẠT phải đọc tay.
- **`o200k_base` chỉ là ĐẠI DIỆN**: Qwen đắt hơn **1,20–1,31×** trên cùng văn
  bản. `6.565 token` canh **xu hướng phình**, **không** dự báo TPM thật.
- **Bộ ca cặp na-ná** (`2ecb739780f4`): `TS trúng = 0` **một mình không nói gì**
  — một cache không bao giờ trúng đạt 100%. Phải đọc **cùng** nhóm `TD`.

### Đơn vị đếm

`golden_set.jsonl` = **120 CA** nhưng **124 CÂU**. Router chấm từng **CÂU**.
`assert == 120` ⟹ 4 câu **không bao giờ được chấm** và cổng **vẫn xanh**.

### Sổ `usage.jsonl` sống qua recreate — LỌC THEO CỬA SỔ THỜI GIAN

Nó tích luỹ **mọi đợt**. 15/62 dòng **không có khoá `duong`** (dòng trước khi
lớp phân luồng land). Script gộp cả sổ và viết `duong != 'day_du'` sẽ đếm
**15 dòng lịch sử thành "lượt đơn"**.

> 🔴 **Đếm `duong == "nhe"` TƯỜNG MINH, và in BA rổ**: `nhe` · `day_du` ·
> **`KHÔNG CÓ KHOÁ`**. Rổ thứ ba khác 0 = dừng lại điều tra.

### `so_luot_goi_model = 0` có HAI nghĩa

*"đường nhẹ, đúng là 0"* và *"lượt hỏng, không đọc được"*. Tách bằng **cặp**
`(duong, ly_do_fallback)` — đo trên n=22, hai trường **không bất đồng lần nào**.
⚠️ Nhưng chúng **cùng một dict literal trong mã** ⟹ *mang thông tin độc lập*
**≠** *có nguồn độc lập*. Trục thay thế bền hơn: **`duong × so_tool_schema_gui`**
(hai tầng khác nhau ⟹ mâu thuẫn tự lộ).

### Băm phải khai TÊN THUẬT TOÁN

`1edd51dff555` (md5) và `742df94b195a` (sha256) là **cùng một tệp**. Cả hai đều
là 12 ký tự hex và **không ai kiểm**. Mọi nhãn trong `eval/` khai
`thuat_toan_bam` — trường đó **nằm ngoài phần được băm**, nên thêm nó **không
đổi** băm đã công bố.

### Và cạm bẫy tôi trả giá đắt nhất

> **Một cổng vừa HỮU ÍCH vừa MANG TÊN SAI thì khó bị nghi ngờ hơn một cổng vô
> dụng** — vì nó có thành tích, và thành tích đó thuộc một trục khác với trục
> tên nó hứa.

`path_traversal_filename_is_safe` **đã bắt được** một bug thật hôm nay (`HTTP
500`), và trong suốt thời gian đó nó **chưa từng kiểm path traversal**. Xem
`eval/QUET-TEN-HUA-KHAC-ASSERTION.md` — còn **5 ca nữa cùng lớp, 5/6 trên đường
duyệt HITL**.
