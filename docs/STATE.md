# Trạng thái dự án FIN-05

> **Viết cho người đọc NGUỘI** — bạn không có gì trong đầu, chỉ có repo này.
> Đọc `CLAUDE.md` (hiến pháp) trước, rồi file này, rồi 5 ADR gần nhất trong `docs/DECISIONS.md`.
>
> Cập nhật: **18/08/2026**, ngay trước khi PO thật tắt toàn đội để khởi động lại sạch.
> Nhật ký chi tiết ngày 17/08 (3.001 dòng, mọi lập luận và số đo):
> `docs/nhat-ky/2026-08-17-nhat-ky-day-du.md`

---

## 1. ĐỌC MỤC NÀY TRƯỚC KHI GÕ BẤT CỨ LỆNH NÀO

| | |
|---|---|
| **Nhánh** | `dev/learning-loop` (một nhánh, PR theo đợt) |
| **Cây làm việc DÙNG CHUNG** giữa nhiều phiên | 🔴 **Mọi lệnh `git` phải có pathspec.** `stash`/`commit`/`checkout`/`clean` không pathspec sẽ đụng việc dở của phiên khác. Đã gây 3 sự cố. |
| **Ba ngăn xếp Docker** | `fin05` (demo, kho RAG 378 chunk) · `fin05ttl` (đo) · `fin05do` (đo, kho RỖNG) |
| **Bắt buộc `-p`** | `docker compose -p fin05 …` — thiếu `-p` là hạ ngăn xếp khác |
| **Chạy test** | `docker exec … pytest` (an toàn). `P-121-new/.venv` chạy được test nhưng **CẤM dùng để đo kích thích gửi model** (lệch `langchain-core` với container) |
| **Biến bắt buộc** | `JWT_SECRET_KEY` · `FIELD_ENCRYPTION_KEY` · `REDIS_URL` (`fake://ci` cho test) |
| 🔴 **`FIELD_ENCRYPTION_KEY`** | **KHÔNG được xoay** nếu chưa có script mã hoá lại — xoay là **mất vĩnh viễn** dữ liệu đã mã hoá |
| **Production** `app.adaptivealgo.uk` | **CHỈ ĐỌC** với mọi phiên. Thăm dò phải báo trước |
| **`eval/heldout_set.jsonl`** | **NIÊM PHONG** — chỉ chạy MỘT LẦN, sau khi hiệu chuẩn trọng tài |

## 2. TRẠNG THÁI VẬT (đo lúc bàn giao)

```
HEAD nhánh dev/learning-loop        [ĐO] 18/08: addec5e (bàn giao ghi 4ac2162 —
                                      3 commit docs sau đó, 0 chạm src/, băm tự chứng minh)
băm src/          b8e7c5397457
BUILD_COMMIT      bec7235   ← cả ba ngăn xếp, ĐỒNG NHẤT
sửa-tay           0 · 0 · 0
docker diff       0 · 0 · 0
lệch×             0 · 0 · 0
invariants        23/23 xanh
check_contracts   sạch
suite backend     1 ĐỎ  (test_thanh_phan_tai_lieu_kho::…noi_bo_da_biet)
                  🔴 18/08: LÝ DO "kho rỗng" LÀ SAI — kho có đủ 378 chunk. Xem §5.D1
```

**[ĐO] 18/08 — PO-agent kiểm lại độc lập, TRƯỚC khi ai chạm vật.** Kiểm được 5 dòng, còn 3 dòng
**chưa kiểm** (cần `docker exec`, đang chờ đèn xanh):

```
băm src/       ✅ b8e7c5397457  — cây làm việc VÀ /app/.bam_ma_nguon của CẢ BA container, 54 file
BUILD_COMMIT   ✅ bec7235       — cả ba, khớp bàn giao
sửa-tay        ✅ 0 · 0 · 0     — bộ lọc `^C /app/src.*\.py$` trừ __pycache__
ba ngăn xếp    ✅ Up + healthy  — backend 9h, postgres/redis/caddy/jaeger 19–46h
sổ usage       ✅ 88 dòng       — khớp bàn giao; dòng cuối 17/08 15:13, KHÔNG lượt mới nào
invariants · check_contracts · ca đỏ "kho rỗng"   ⬜ CHƯA KIỂM LẠI
```

⚠️ **Bẫy đã gặp lúc kiểm, ghi lại để người sau khỏi vấp:**
- **Băm bằng phép TỰ CHẾ ra số khác.** PO-agent tự gõ `find|xargs shasum` ra `bc20ff277ad3` —
  lệch, vì phép ấy **băm cả đường dẫn**. Phép chính chủ (`src/dau_ma_nguon.py:bam_ma_nguon`) chỉ
  băm **nội dung**, sắp theo đường dẫn. ⟹ **Một con số băm không kèm CÁCH BĂM thì không phải bằng
  chứng** — chính module đó đã viết sẵn câu này, và nó vừa cứu một báo động giả.
- **`docker diff` bản THÔ kêu ở cả ba** (9 · 0 · 7 mục dạng `C /app/src/<thư-mục>`). Đã mở ra
  nhìn: **toàn là THƯ MỤC** bị đổi mtime do `__pycache__` ghi bên trong, **không file `.py` nào
  đổi**. Đúng như bàn giao ④ đã cảnh báo: *một cái còi kêu bừa là cái còi bị tắt* — dùng bản lọc.

**Model đang chạy:** `qwen3.7-max` qua DashScope **Singapore** (`dashscope-intl`).
Embedding vẫn **OpenAI** (tách khỏi chat có chủ đích — đổi embedding = đổi VẬT ⟹ phải nạp lại kho).

✅ **CỜ ĐÓNG BĂNG — PO THẬT ĐÃ QUYẾT 18/08: video demo QUAY XONG ⟹ ĐỂ NGUYÊN TRẠNG THÁI XOÁ.**
Việc xoá `.DANG-DONG-BANG-LLM` là **thao tác ĐÚNG**, khớp lời tự khai của tệp (*"xoá file này khi
hết đóng băng"*). Câu hỏi treo từ 17/08 nay đã đóng.

🔴 **HỆ QUẢ PHẢI ĐỌC KÈM — ta CỐ Ý đứng trên HAI lớp, không phải ba.** Lớp ② nay vĩnh viễn tắt
(xem §3): cả 3 bộ test tốn tiền mất chốt `skipif(dang_dong_bang())`. **Lớp ① là lớp DUY NHẤT còn
chặn.** Nó đủ mạnh và là nguồn độc lập thật (biến môi trường vs file — Luật D), nhưng **dự phòng
đã hết**: một sơ suất đặt `FIN05_CHO_PHEP_TON_TIEN=1` giờ **không còn gì đỡ phía sau**.
⟹ Việc xoá vẫn chưa commit (`D` trong `git status`). Ai commit thì **dùng pathspec** và ghi rõ
đây là quyết định của PO thật 18/08, không phải dọn rác.

## 3. BA LỚP GIỮ HOÁ ĐƠN — kiểm trước khi chạy bất cứ thứ gì

```
① FIN05_CHO_PHEP_TON_TIEN   mặc định TẮT ⟹ 3 bộ test gọi LLM thật đều SKIP   ✅ [ĐO] 18/08
② .DANG-DONG-BANG-LLM       cờ đóng băng                                🔴 [ĐO] 18/08 — ĐANG MẤT
③ PHAN_LUONG_BAT=1          câu chào hỏi đi đường nhẹ, 0 token          ✅ [ĐO] 18/08
```

**[ĐO] 18/08 — PO-agent kiểm tận mắt, kèm MẪU SỐ:**
- **① còn nguyên.** `FIN05_CHO_PHEP_TON_TIEN` không đặt trong môi trường, không trong `.env*`.
  **Mẫu số: 3/3 bộ ĐÃ KHAI** đều có `skipif(not duoc_phep_ton_tien())` — `test_a2…:119` ·
  `test_bat_bien_dinh_tuyen…:60` · `test_agents/test_f31_f32…:133`.
  ⚠️ **CHƯA quét toàn `tests/` tìm bộ thứ tư chưa khai.** "3/3 bộ đã biết" ≠ "toàn bộ suite".
- 🔴 **② THẬT SỰ MẤT, và nó CHỊU LỰC trong code test.** Cả ba bộ trên còn mang thêm
  `skipif(dang_dong_bang())`; `tests/_dong_bang.py:56` quyết bằng **sự tồn tại của file marker**.
  File bị xoá ⟹ **chốt chặn ấy không còn bắn**. Ta đang đứng trên **HAI lớp, không phải ba**.
- 🔴🔴 **ĐÍNH CHÍNH cùng ngày — "① vẫn đủ chặn một mình" là SAI. PO-agent viết câu đó, tester bác
  bằng ĐO.** Xem **§5.F**. `pytest tests/` **HÔM NAY vẫn đẩy một lượt nhúng ra Internet** dù cả hai
  lớp đều bật. Sai vì tôi kết luận trên mẫu số **"3 bộ ĐÃ KHAI"** rồi phát biểu về **cả suite** —
  tôi có khai mẫu số ấy ra, và **vẫn bước qua chính nó ở câu kế tiếp**. Đúng §8, do chính người
  viết nếp kiểm phạm.
- **③ còn nguyên.** `PHAN_LUONG_BAT=1` trong `Config.Env` của **cả ba** container.

🔴 **Hạn mức: A3 của PO thật còn hiệu lực — "chưa nạp gì cho tới khi tối ưu xong chi tiêu token."**
Còn **~32K** token miễn phí trên `qwen3.7-max`. `qwen3.8-max` đã cạn. Quota là **1M/model**.

---

## 4. ĐÃ LÀM ĐƯỢC (nền, tin được)

- **Kiến trúc contract-first hoạt động thật.** `tests/test_invariants.py` **introspect app đang
  chạy** (đọc `app.routes`, moi `allowed_roles` từ closure, đọc `CheckConstraint` qua AST, gọi
  thẳng `build_customer_tools()`). Thêm route / đổi guard / đổi tên tool mà quên contract ⟹ **đỏ
  ngay**. 23/23 xanh.
- **Năm ràng buộc cứng** đã mã hoá thành test (HITL tuyệt đối · AI không vượt cấp · cấm bịa số
  liệu · OTP phiên · cờ gian lận ≠ khoá ví).
- **T1 định tuyến (`src/agents/phan_luong.py`)** — luật cứng, allow-list, tự khai băm. Đo được:
  **−33,5% tất định**, câu `"alo"` = **0 token**.
- **Sự cố lộ khoá OpenAI đã đóng**: `_khoa_cho_nha_cung_cap()` fail-fast — thiếu khoá + base_url
  khác ⟹ `RuntimeError` lúc khởi động, **không bao giờ âm thầm mượn `OPENAI_API_KEY`**.
- **Benchmark 74,57/85 = 87,7%** — luôn kèm 3 caveat (xem nhật ký).
- **Bộ an toàn 30/30** — ⚠️ **hiệu chuẩn trên `gpt-4o-mini`, CHƯA chạy lại trên Qwen.** Đây là
  tài sản lớn nhất dự án và nó đang **chưa được xác nhận trên model đang chạy**.

## 5. ĐANG DỞ / CHẶN — theo mức

### 🗺️ BẢN ĐỒ CHẶN — dựng lại 18/08 bằng trạng thái THẬT, không chép lại bản cũ

**Cách dựng:** PO-agent hỏi thẳng từng phiên, không tin danh sách cũ. Kết quả:

```
phiên        có mặt?  vai đã nhận   đang sửa dở  đang đo dở   trạng thái
tech-lead      ✅     đã nhận            0            0        ĐANG CHẠY: bất biến ① nửa (a)
tester         ✅     đã nhận            0            0        ĐANG CHẠY: 6 cổng an toàn
security       ✅     PO xác nhận tab đã mở (p-226-b0) — đã giao việc, chờ xác nhận vai
```

🔴 **Cả hai phiên xác nhận: cây làm việc chỉ có ĐÚNG MỘT dòng `D .DANG-DONG-BANG-LLM`, và
KHÔNG phiên nào nhận đã xoá.** Ba nguồn độc lập (tech-lead · tester · PO-agent) cùng thấy một
thứ ⟹ trạng thái cây là **sạch ngoài đúng mục đó**. Chưa phiên nào tiêu một token nào của A3.

**Ai chặn ai — sau khi kiểm:**

```
ADR-031          → PO THẬT (3 câu, §5.A1)  → chặn tech-lead SỬA CONTRACT   (KHÔNG chặn việc ①)
phiếu Alibaba    → PO THẬT (4 câu, §5.A3)  → chặn mọi quyết định hạn mức
nhịp gõ 150 ng   → PO THẬT (§5.A5)         → chặn kế hoạch buổi test
hồ sơ Đ.25       → PO THẬT (1 câu, §5.A2)  → chặn KHÔNG AI, hạn 14/10
cờ đóng băng ②   → ✅ ĐÃ ĐÓNG 18/08        → PO: video quay xong ⟹ để nguyên. Lớp ② tắt VĨNH VIỄN
mức-bản-ghi      → SECURITY                → ✅ hết vô chủ, đã giao p-226-b0 18/08
tool_input_json  → SECURITY                → 🔴 plaintext chứa mã GD/SĐT/số tiền; chặn phạm vi ADR-031
/ready (ADR-028) → PO THẬT (§10)           → 🔴 MỚI: ADR duyệt 17/08, CHƯA CODE. Đụng contract
ca A2 viết lại   → TESTER                  → chặn tech-lead vá F-31/32
```

**Và một ràng buộc KHÔNG có trong bản đồ cũ — nó có thật, hai phiên cùng chỉ ra:**

> 🔴 **`tests/` NẰM TRONG ẢNH.** Tester vá `tests/`, nhưng cổng chạy bằng `docker exec … pytest`
> đọc **bản cũ trong ảnh** cho tới khi dựng lại. Và tech-lead land `src/` cũng cần dựng lại để
> xác minh. ⟹ **Hai việc độc lập cùng đổ vào MỘT thao tác dựng ảnh**, mà dựng ảnh giữa lúc ai đó
> đo là đúng cái lỗi *"đổi vật giữa phép đo"*.
>
> **Điều phối 18/08 (PO-agent chốt, thuộc thẩm quyền điều phối, KHÔNG phải quyết của PO thật):**
> 1. Hai phiên viết **song song**, **KHÔNG ai dựng ảnh**.
> 2. Tester xác minh 6 bản vá bằng **venv host** (`P-121-new/.venv`, [ĐO] 18/08 còn sống,
>    Python 3.14.6) — hợp lệ vì cả 3 file đích **không gọi LLM** ([ĐO]: 0 dấu hiệu
>    `_ton_tien`/`dang_dong_bang`/`ChatOpenAI`/`dashscope`), nên **không rơi vào lệnh cấm
>    "CẤM venv để đo kích thích gửi model"** — lệnh cấm ấy nói về **lệch `langchain-core`**, một
>    trục không tồn tại ở test API thuần.
> 3. Dựng ảnh **MỘT LẦN**, sau khi cả hai land, và **khai trước với cả hai phiên**.
> 4. **CẤM `docker cp`** vào container đang chạy (Luật I).


### ✅ A0. PO THẬT ĐÃ QUYẾT — 18/08/2026. Đọc mục này TRƯỚC §5.A.

| # | việc | quyết định | hệ quả |
|---|---|---|---|
| A3 | phiếu Alibaba (trần TPM/RPM) | 🚫 **KHÔNG LÀM BÂY GIỜ** | Ưu tiên chuyển sang **tối ưu caching + token**. Trần TPM chưa cần biết |
| A5 | nhịp gõ buổi 150 người | 🚫 **CHƯA ĐẾN LÚC** | §6.⓵ giữ nguyên làm tài liệu, **không lên lịch** |
| A2 | hồ sơ Đ.25 (NĐ 13/2023) | 🚫 **BỎ, KHÔNG LÀM** | Xem cảnh báo dưới |
| §2 | cờ đóng băng LLM | ✅ video quay xong ⟹ **để nguyên trạng thái xoá** | Lớp ② tắt vĩnh viễn |
| — | tab security | ✅ đã mở (`p-226-b0`) | Nhánh "chờ security" hết vô chủ |

**VÒNG 2 — 18/08, sau khi PO đọc bản giải thích bốn đầu việc:**

| # | việc | quyết định | hệ quả |
|---|---|---|---|
| ADR-033 | `/ready` + cổng canh hạng mù | ✅ **DUYỆT cả hai phần** | tech-lead mở khoá, đi đủ §10 (gồm **bước 7: commit KÈM baseline**) |
| ADR-034 | gỡ tạm dừng ADR-031 | ✅ **DUYỆT cả ba lựa chọn phạm vi** | §5.A1 **ĐÓNG** — ba câu treo đã có ba trả lời |
| — | `fin05ttl` · `fin05do` | ✅ **xoá `ttl` theo BA BƯỚC · giữ `do`** → **ADR-036** | tester có việc: dựng lại ca đối chứng trên quần thể vứt đi **TRƯỚC** |
| ADR-026 | duyệt tài liệu chính sách | ⏸ **HOÃN — PO cần nghiên cứu kỹ hơn** | 🔴 lỗ §5.N **VẪN MỞ**, và đó là lựa chọn **có khai**, không phải bỏ quên |
| CI | 11 job đỏ | ✅ **billing — XÁC NHẬN bằng annotation nguyên văn GitHub** | chỉ PO gỡ được; xem §5.P |
| ADR-037 | `.github/` vào vùng ghi tech-lead · CI sang runner BTC | ✅ **DUYỆT QĐ1 + QĐ2** | `CLAUDE.md` §4 đã sửa; brief đã sẵn |
| — | `deploy.yml` giữ `ubuntu-latest` | ✅ **DUYỆT** | quả mìn hẹn giờ được tháo TRƯỚC khi đặt secret |
| — | hỏi BTC: runner ephemeral? | ⏸ **PO hỏi tối 18/08** | 🔴 tới lúc đó **giả định PERSISTENT**; `if: always()` **không chờ** |

> ⚠️ **ĐỌC KÈM MỤC ADR-026 HOÃN — đừng đọc "hoãn" thành "không còn là lỗ".**
> §5.N đo được: **không có trạng thái `da_duyet`, không có ai duyệt**, tài liệu đi thẳng
> `processing → indexed` rồi được phục vụ. Sự cố 16/08 (19 phút 33 giây, hai file nội bộ trong kho
> đang phục vụ) **tái diễn được bằng đúng thao tác cũ**. PO hoãn **quyết định**, không hoãn **sự thật**.
> **Ranh giới phát biểu giữ nguyên §5.N:** *"cơ chế duyệt chưa tồn tại"* ✅ — **KHÔNG** phải
> *"đang có tài liệu chưa duyệt được phục vụ"* ❌ (2 tài liệu hiện có đều qua đúng cửa).

**⟹ HƯỚNG ƯU TIÊN MỚI CỦA ĐỘI: tối ưu CACHING + TOKEN.** Mọi việc trong §5.B phải xếp lại theo trục
này. Việc §6.⓶ (bất biến chống livelock) **vẫn là ưu tiên số một** — nó chính là việc tiết kiệm token
lớn nhất đo được (~40K/lượt hỏng), không phải một việc khác cạnh tranh với nó.

> ⚠️ **GHI MỘT LẦN, KHÔNG NHẮC LẠI — ranh giới của quyết định "bỏ Đ.25".**
> PO thật bỏ **HỒ SƠ Đ.25** (thủ tục giấy tờ NĐ 13/2023 cho dữ liệu rời biên giới). Đó là quyết định
> của PO, đã ghi, đội không mở lại.
> **Nhưng "bỏ hồ sơ" ≠ "dữ liệu plaintext không còn là vấn đề kỹ thuật".** §5.E (738/761 dòng Nhóm A
> nằm plaintext trên đĩa) và finding ① của security (`tool_input_json` plaintext) **tồn tại độc lập
> với hồ sơ giấy** — chúng là lỗ **trong sản phẩm**, không phải mục trong một biểu mẫu. Đừng đọc
> "bỏ Đ.25" thành "đóng luôn §5.E".
> ✅ **Và bỏ Đ.25 GỠ được một nút thắt:** security đã ghi *"vá finding ① sẽ xoá dụng cụ đo của Đ.25
> ⟹ phải kiểm kê xong TRƯỚC khi vá"*. Bỏ Đ.25 ⟹ **ràng buộc thứ tự ấy tan** ⟹ vá plaintext được
> land **sớm hơn**, không phải muộn hơn.

### 🔴 A. CHẶN, chỉ PO thật gỡ được

**A1 · ADR-031 — ✅ ĐÓNG 18/08 vòng 2. Không còn chặn.**
PO thật phê chuẩn **cả ba** lựa chọn phạm vi của **ADR-034** ⟹ ba câu treo dưới đây đã có ba trả lời:
**① HAI bảng · ② MỞ RỘNG cơ chế đã có (không thêm cột) · ③ `tool_input_json` tách thành finding
bảo mật ĐỘC LẬP.** Giữ nguyên văn ba câu bên dưới **để người đọc sau thấy câu hỏi, không chỉ thấy đáp
án** — một đáp án không kèm câu hỏi là thứ phiên sau sẽ "tối ưu" ngược lại.

<details><summary>nguyên văn ba câu treo (đã trả lời — bấm để xem)</summary>

**A1 · ADR-031 (truy vấn `search_policy`) — TẠM DỪNG THI HÀNH, TIỀN ĐỀ SAI.**
PO đã duyệt, nhưng duyệt trên tiền đề *"query chưa được lưu ở đâu"* — **sai**:
`investigation_logs.tool_input_json` (`models.py:328`, JSON **thường không mã hoá**) đã lưu query
từ lâu. **Ba câu cần PO:**
1. phạm vi **một bảng** (`tool_results`) hay **hai bảng**?
2. **thêm cột mới** hay **mở rộng cơ chế đã có** ở `investigation_logs` cho lượt không tạo vé?
   *(đường thứ hai rẻ hơn hẳn, không tạo chuẩn thứ ba)*
3. `tool_input_json` plaintext chứa **mã GD · SĐT · số tiền** (input của MỌI tool, không riêng
   `search_policy`) — tách thành **finding bảo mật riêng**, độc lập ADR-031?

</details>

**A2 · Hồ sơ Đ.25 (NĐ 13/2023) — đồng hồ CÓ THỂ đã chạy từ 15/08.**
```
demo mentor 15/08  ·  hạn 60 ngày = 14/10/2026  ·  CÒN 58 NGÀY (tính lúc 17/08)
```
**Việc đầu tiên là XÁC ĐỊNH, không phải làm hồ sơ:** *buổi demo mentor 15/08 có ai gõ SĐT / tên /
mã giao dịch **THẬT** vào ô chat không?* Không ⟹ đồng hồ chưa chạy. Có ⟹ hồ sơ là "bù" chứ không
phải "chuẩn bị".
> **Nghĩa vụ này CÓ TỪ TRƯỚC QWEN** — hệ thống gửi văn bản khách sang Mỹ từ thời `gpt-4o-mini`.
> Vật liệu §2/§3/§4 do security dựng: `docs/security/2026-08-17-kiem-ke-du-lieu-roi-bien-gioi-cho-ho-so-D25.md`

**A3 · Phiếu Alibaba — 4 câu MỘT vòng** (thứ tự đã xếp):
1. 🔴 **trần TPM/RPM ở Singapore có nâng được theo yêu cầu không, điều kiện gì?**
   *(nâng được ⟹ cả nhánh đổi vùng LẪN hồ sơ pháp lý cùng rụng)*
2. request client **ngắt giữa chừng** có tính tiền/TPM không?
3. **cached-token** có vào TPM không?
4. **batch ở Singapore**: giá 50% và bucket riêng hay không?

**A4 · Đối chiếu bảng điều khiển** — tổng token 1 ngày trên dashboard nhà cung cấp **vs** sổ nội
bộ. Đây là phép phân định cho giả thuyết *"lượt hỏng ghi 0 là lời giải cho câu 2,3M"*.

**A5 · Chốt NHỊP GÕ cho buổi 150 người** — xem mục 6, đây là **biến quyết định duy nhất**.

**A6 · Hai công tắc logging chưa ai kiểm:**
- **Alibaba `Model monitoring`**: ghi input/output **mỗi lời gọi**, giữ 30 ngày, **bật bằng một
  nút**, **không diff nào của ta nhìn thấy** ⟹ kiểm + **ghi ngày kiểm**
- **OpenAI stored completions / org logging**: chưa ai kiểm, và nó **định hạng sự cố lộ khoá 17/08**

**A7 · Còn treo từ trước:** xoay khoá Qwen · secret GitHub Actions · **số hotline thật**
(`HOTLINE_CSKH` hiện là `1900-XXXX (SỐ TẠM — CHƯA CẤU HÌNH)`, **cố ý không bấm được**).

### 🟡 B. Đội làm được, không chờ ai

| việc | vùng | ghi chú |
|---|---|---|
| **Bất biến chống livelock** — *"cùng tool + cùng tham số + cùng lỗi ⟹ lần thứ hai là DỪNG"* | `src/` | **Ưu tiên cao nhất.** Tất định, **không cần hiệu chuẩn**. Xem mục 6 |
| 🔴 **VÁ 6 ca "TÊN hứa X, ASSERTION kiểm Y" — 5/6 trên ĐƯỜNG DUYỆT HITL** | `tests/` | Quét **ĐÃ XONG** (`4ac2162`, `eval/QUET-TEN-HUA-KHAC-ASSERTION.md`), tiêu chí công bố trước, bộ quét bắt được ca đã biết. **Việc còn lại là VÁ**, mỗi ca một dòng. Bắt đầu từ 5 ca HITL |
| Ca A2 (đồng ý trước khi tạo vé) — viết lại câu | `tests/` | ba trục: thuận · ngược (đã đồng ý thì KHÔNG hỏi lại) · **ca hỏng** |
| F-31/32 — prompt thiếu *"làm gì khi một điều kiện KHÔNG TỰ SỬA ĐƯỢC"* | `src/` | Cùng họ với A2. Vá **sau** bất biến |
| Truy ca đỏ còn lại (`kho rỗng`) | `tests/` | chưa ai gán nguyên nhân |
| ~~`main.py:621` — khách đọc lý do từ chối SAI~~ → **ĐÍNH CHÍNH 18/08, xem §5.C** | `src/` | Phát biểu cũ SAI. Gộp vào sổ nợ `_AGENT_MAX_CONCURRENT` (§6.⓸), **hạ mức gấp** |
| Sổ nợ: `_AGENT_MAX_CONCURRENT=20` **mất căn cứ** | — | xem mục 6 |
| `so_luot_da_phat` (đếm ở tầng client HTTP) | `src/` | **nguồn ĐỘC LẬP thật** duy nhất với envelope |
| Container lint/test riêng | hạ tầng | chữa GỐC việc bước-đo-ghi-vào-container. Khuôn đã có: `fin05-THU-ROUTER-vut-di` |
| 🔴 **Vá đầu dò + DỰNG CA ĐỐI CHỨNG cho cổng rò tài liệu nội bộ** | `tests/` | Xem §5.D1. **Không vá tên suông.** Tester tự khám phá tên collection bằng quan sát hộp đen |
| `GET /ready` — ADR-028 duyệt 17/08, **chưa code** | `src/` + `contracts/` | Xem §5.D2. Đụng `authority-matrix.yaml` ⟹ **phải đi đủ §10** ⟹ chờ PO thật |
| Cổng *"ADR Đang-hiệu-lực ⟹ file nó nêu phải tồn tại"* | `tests/` | Đề xuất từ §5.D2. Chưa ai nhận |

### 🔴 D. PHÁT HIỆN MỚI 18/08 — hai thứ cả đội đang tin SAI

*(Bắt bởi **tech-lead**. PO-agent kiểm lại **độc lập** từng số trước khi ghi — không relay qua lời kể.)*

**D1 · Ca đỏ "kho rỗng" là một KẾT LUẬN SAI. Kho `fin05` có ĐỦ 378 chunk.**

```
[ĐO] docker exec fin05-backend-1 → chromadb.PersistentClient('/app/data/rag_index')
     policy_faq                            count =   0    ← đầu dò của test soi ĐÚNG cái này
     policy_faq__text-embedding-v4         count = 378
     policy_faq__text-embedding-3-small    count = 378
[ĐO] src/rag/store.py:33  _ten_collection() → f"{_COLLECTION_GOC}__{RAG_EMBEDDING_MODEL}"
     — CỐ Ý: Chroma ghim số chiều lúc tạo (3-small 1536 vs Qwen v4 1024) ⟹ hai model
       KHÔNG dùng chung collection được. Sản phẩm ĐANG ĐÚNG.
[ĐO] tests/test_rag/test_thanh_phan_tai_lieu_kho.py:80  gõ cứng get_collection('policy_faq')
     — tên TRẦN, thứ sản phẩm KHÔNG CÒN ghi vào.
```

⟹ **Không có bug sản phẩm.** Sai nằm ở **đầu dò của test**: nó đo một collection đã ngừng dùng.

🔴 **Và đây là ca LUẬT H thuần nhất mà chính Luật H không cứu được** — vì luật ra đời **sau** test.
Câu test in ra là `"index KHÔNG có doc_id nào — kho rỗng, mọi khẳng định dưới đây vô nghĩa"`: đó là
**KẾT LUẬN** (*"kho rỗng"*), không phải **TRIỆU CHỨNG** (*"collection `policy_faq` trả 0 doc_id"*).
Vì nó in kết luận nên `docs/STATE.md` §2 chép lại thành *"kho rỗng, điều kiện hạ tầng"* và **cả đội
tin suốt từ 17/08 tới 18/08**. **Không ai sai quy trình — cái đèn nói dối.**

🔴 **CẤM VÁ NHANH (Luật J).** Đổi tên collection trong test làm cổng **ĐỎ → XANH** trong một dòng.
Nhưng phải hỏi **cổng ấy khẳng định CÁI GÌ**: tên nó là `test_kho_khong_chua_tai_lieu_noi_bo_da_biet`
— một phép kiểm **RÒ TÀI LIỆU NỘI BỘ** vào kho RAG. Vì đầu dò trỏ sai chỗ, phép kiểm ấy **CHƯA
TỪNG thật sự chạy trên kho thật**. Nó không phải *"cổng đỏ vì hạ tầng"*, nó là **cổng chưa bao giờ
khẳng định được điều nó hứa**. Vá tên mà không kèm **ca đối chứng** (Luật A: cổng phải KÊU lúc bất
thường) là **đổi một cổng đỏ trung thực lấy một cổng xanh rỗng**.

> ⚠️ **ĐIỀU PHỐI — bức tường tester/`src/` suýt thủng ở đúng đây.** tech-lead (đã đọc `src/`) đề
> nghị **soạn sẵn nội dung test cho tester dán vào**. PO-agent **TỪ CHỐI**: đó chính là cơ chế
> khiến test *phản chiếu* code (§11). Cách đúng: tester **tự khám phá** tên collection bằng cách
> **liệt kê collection từ container đang chạy** — đó là quan sát **hộp đen**, tester được phép, và
> nó cho ra một test **TỐT HƠN**: không gõ cứng tên nào cả, nên không chết lần sau khi đổi model
> nhúng. Chuyển **KẾT LUẬN và LÝ LẼ**, không chuyển **NỘI DUNG**.

**D2 · ADR-028 ghi "Đang hiệu lực" nhưng `GET /ready` CHƯA HỀ TỒN TẠI.**

```
[ĐO] app đang chạy, liệt kê từ app.routes (không suy từ vắng mặt):
     37 cặp (method, path) · khớp 'health|ready|ops' → GET /health, DUY NHẤT
     ⚠️ tech-lead báo 40, PO-agent đo 37 — MẪU SỐ lệch, KẾT LUẬN không đổi
       (hit duy nhất là GET /health ở cả hai phép đếm). Chưa truy nguyên chỗ lệch.
[ĐO] grep -rn "ready" src/        → 2 hit, CẢ HAI là chú thích (main.py:1527, 1580)
[ĐO] grep -n "ready" contracts/authority-matrix.yaml  → 0 hit
```

ADR-028 (PO thật chốt 17/08) quyết thêm `GET /ready`, khai vào `authority-matrix.yaml`, làm ĐỎ khi
kho rỗng. **Không thứ nào trong ba thứ đó tồn tại.** Không ai làm sai — ADR ghi rõ *"§3: ADR trước,
code sau"*, và phần *"code sau"* chưa tới. Vấn đề là **không chỗ nào theo dõi việc nó chưa tới**,
và hai chú thích ở `main.py:1527,1580` viết về `/ready` **như thể nó đã có**.

🔴 **Vì sao cơ chế contract-first KHÔNG bắt được — đây mới là phần đáng ghi.** INV-00 ép `app.routes`
khớp chính xác `authority-matrix.yaml`. **Cả hai đều KHÔNG có `/ready`** ⟹ chúng khớp nhau hoàn hảo
⟹ **23/23 xanh**. Cơ chế đang làm **đúng việc của NÓ** (bắt code lệch contract); ta đã quen đọc nó
thành một thứ rộng hơn (bắt **quyết định chưa được thi hành**). Đúng **Luật G**, lần này ở tầng
**cơ chế phòng thủ** chứ không ở tầng dữ liệu.
⟹ **Không cơ chế tự động nào của dự án bắt được "ADR đã duyệt mà chưa ai code".** Chỗ bịt **không
phải** `test_invariants.py` mà là một cổng mới: *"mọi ADR Đang-hiệu-lực có mục Hệ quả nêu file thì
file đó phải tồn tại"*. **Đề xuất — chưa ai làm, cần PO thật cho vào hàng đợi.**


### 🔴🔴 E. PHÁT HIỆN NẶNG NHẤT 18/08 — cột Nhóm A **KHÔNG được mã hoá trên 97% số dòng**

*(Bắt bởi **PO-agent**, trong lúc kiểm lại một phát biểu của **security** trước khi relay cho PO thật.
Security báo `complaints.description_raw` **đã mã hoá**; số không khớp, và lệch về hướng **nặng hơn**.)*

**Security phát biểu** (hồ sơ 18/08): *"`complaints.description_raw` → `gAAAAABq…` **MÃ HOÁ**"*, và
dựng finding ① trên khung *"cột đã mã hoá đang có một BẢN SAO plaintext ở bảng khác."*

**[ĐO] PO-agent, `psql` thẳng vào `fin05-postgres-1`, đếm ĐỦ dân số:**

```
complaints.description_raw     PLAINTEXT  738   tạo 05/05/2026 → 14/08/2026
                               MÃ HOÁ      23   tạo 15/08/2026 → 17/08/2026
                               ⟹ 738/761 = 97% NẰM PLAINTEXT TRÊN ĐĨA

messages.content               MÃ HOÁ     467   tạo 11/08 → 16/08   (467/467 = 100%)
```

⟹ **Khung của finding ① SAI, và sai về phía trấn an.** Không phải *"lớp mã hoá bị đi vòng"* —
**bản thân cột ấy chưa từng được mã hoá cho dữ liệu có sẵn.** `EncryptedText` được gắn vào
`models.py:274` khoảng **15/08** và **738 dòng cũ chưa bao giờ được nạp lại**. `messages` không
dính vì bảng ấy chỉ có dữ liệu từ 11/08 và mã hoá từ đầu.

🔴 **VÌ SAO KHÔNG AI THẤY — `src/db/crypto_types.py:59-65`:**

```python
def process_result_value(self, value, dialect):
    try:
        return _fernet.decrypt(value.encode()).decode()
    except InvalidToken:
        return value          # ← nuốt IM LẶNG, trả nguyên văn
```

Nhánh lỗi **trả về thứ trông y hệt một lần đọc thành công**. Ứng dụng đọc 738 dòng plaintext ấy
**không một lỗi nào**, không một dòng log nào. **Luật H ở dạng mạnh nhất từng gặp:** các ca trước
nhánh lỗi *in ra kết luận*; ca này nhánh lỗi **không in gì cả** — nó **giả trang thành thành công**.
Và **Luật G**: cơ chế đang làm **đúng việc của NÓ** (tương thích ngược lúc di trú), ta đọc nó thành
một thứ rộng hơn (*"cột này được mã hoá"*).

🔴 **HỆ QUẢ THỨ HAI, chưa ai nêu — nó làm cảnh báo §1 về `FIELD_ENCRYPTION_KEY` NGHIÊM TRỌNG HƠN.**
§1 ghi *"KHÔNG xoay khoá nếu chưa có script mã hoá lại — xoay là mất vĩnh viễn"*. Với nhánh nuốt
lỗi này, xoay khoá **không báo lỗi**: 23 dòng đã mã hoá sẽ `InvalidToken` → **trả về nguyên chuỗi
`gAAAAA…`** như thể đó là nội dung khiếu nại. **Không mất dữ liệu ồn ào — mà hỏng dữ liệu IM LẶNG.**

**[ĐO] 18/08 bổ sung — security kiểm CẢ HỌ cột, bước PO-agent đã bỏ sót. Tin TỐT:**

```
cột khai Encrypted*          MÃ HOÁ   PLAINTEXT
messages.content               467        0     ✅
policy_chunks.text             378        0     ✅
bank_accounts.account_no       245        0     ✅
complaints.description_raw      23      738     🔴  ← DUY NHẤT
```
⟹ **Nợ khu trú ở ĐÚNG MỘT cột. Hệ thống mã hoá KHÔNG hỏng.** `description_raw` là cột **mới nhất**
được gắn kiểu, gắn lên một bảng **đã có 738 dòng**. Việc sửa gói trong **một script backfill**, không
phải một cuộc rà soát toàn hệ thống.

🔴 **[ĐO] PHÉP ĐO DỨT ĐIỂM — §5.E và finding ① là HAI LỖ KHÁC LOẠI, không phải một lỗ hai triệu chứng.**
Ghép 27 dòng `create_ticket` với chính `complaint` của chúng:

```
13/08  gốc PLAINTEXT  6      15/08  gốc MÃ HOÁ  3
14/08  gốc PLAINTEXT  5      16/08  gốc MÃ HOÁ  8
                             17/08  gốc MÃ HOÁ  5
⟹ 16/27 dòng có BẢN GỐC ĐÃ MÃ HOÁ ĐÚNG và một BẢN SAO PLAINTEXT NẰM CẠNH
```
Với 16 dòng ấy, cơ chế ADR-025 **đã chạy, đã đúng, và vẫn bị đi vòng trong cùng một giao dịch**.

| | **§5.E** | **finding ① (`tool_input_json`)** |
|---|---|---|
| loại | **nợ MIGRATE** — cơ chế có, đúng, đang chạy | **thiếu CƠ CHẾ** — chưa từng có gì |
| ghi mới hôm nay | ✅ được mã hoá | 🔴 **vẫn sinh plaintext, mỗi lượt** |
| sửa bằng | script backfill, chạy MỘT LẦN | một **quyết định thiết kế** |
| sau khi sửa lỗ kia | — | **vẫn nguyên** |

> **§5.E là VŨNG NƯỚC — tát một lần là hết. Finding ① là VÒI ĐANG CHẢY — không script nào đóng được.**
> ⟹ **Vá §5.E làm ① nặng thêm về mặt TƯƠNG ĐỐI:** backfill xong, `complaints` sạch 100% ⟹
> `investigation_logs` thành **bản plaintext DUY NHẤT còn lại của lời khai khách**.

🔴 **THỨ TỰ BẮT BUỘC — mục 1 đứng trước mục 2 KHÔNG phải vì nó rẻ hơn:**
**nếu backfill chạy trước, phép nghiệm thu của chính nó đi qua đúng nhánh đang nói dối** — một dòng
backfill hỏng sẽ đọc ra nguyên văn và **trông y hệt một dòng thành công**. **Sửa cái đèn trước khi soi.**
Cơ chế phân biệt rẻ và tin được: `gAAAAA` là dấu hiệu của Fernet token (byte phiên bản `0x80` →
base64url luôn mở đầu `gA`) ⟹ *bắt đầu bằng `gAAAAA` mà decrypt hỏng* = **SAI KHOÁ, ném lỗi, KHÔNG
nuốt**; *ngược lại* = plaintext cũ, trả nguyên văn. **Phải land TRƯỚC mọi thao tác xoay khoá.**

**Ba việc, KHÔNG gộp làm một:**
1. `src/` — nhánh `except InvalidToken` phải **phân biệt ba trạng thái** (giải mã được · chưa mã hoá ·
   mã hoá bằng khoá khác), không phải hai. Đúng Luật H: *luôn là BA trạng thái.*
2. `migrations/` — script nạp lại 738 dòng. **Chưa tồn tại.**
3. `docs/security/` — security phải **đánh giá lại finding ①** trên dân số đúng: bản sao plaintext ở
   `investigation_logs` là **lỗ thứ hai**, không phải lỗ duy nhất, và **không phải lỗ lớn nhất**.

> ⚠️ **NẾP KIỂM, ghi lại vì nó vừa hiệu quả lần thứ hai trong ngày:** security trích **3 dòng mẫu**
> và đọc ra *"đã mã hoá"*. Ba dòng ấy tình cờ nằm trong **23 dòng mới**. PO-agent hỏi **MẪU SỐ**
> (`GROUP BY` trên toàn bảng) thì bức tranh **lật ngược**. Đúng §8: *tập tự đến đã bị lọc rồi* — lần
> này bộ lọc là **`LIMIT 3` mặc định trả về dòng mới nhất.**


### 🔴🔴 F. HAI PHIÊN ĐỘC LẬP HỘI TỤ — chốt chặn chi phí đặt SAI TẦNG

*(tech-lead và tester tìm ra **cùng một lỗ từ hai hướng khác nhau**, không ai biết việc của ai.
Hai NGUỒN độc lập — Luật D ở dạng mạnh nhất: không phải một biến viết hai lần.)*

**Hướng 1 — tech-lead**, khi dựng ca nghiệm thu, tự khai một suýt-sai:
~~`search_policy` là tool DUY NHẤT trong 5 tool không có cổng OTP~~ → **SAI, xem đính chính §5.G.**
Phát biểu đúng: `search_policy` là **một trong HAI** tool không kiểm OTP (tool kia:
`request_human_handoff`), và **cả năm tool đều mang `@_locked`**. Vế còn nguyên hiệu lực: một script
gọi thẳng tool chạy tới `embed_query()` → **gọi thật ra OpenAI**.
Lần này chặn bởi `OPENAI_API_KEY=gia` ⟹ 401, **0 đồng**. Khoá thật thì đó là lượt nhúng tính tiền.

**Hướng 2 — tester**, phép dò *vô hiệu hoá hậu quả TRƯỚC* (khoá giả + base_url `127.0.0.1:9`), chạy
**toàn bộ** `tests/`:

```
620/620 ca ĐÃ CHẠY qua phép dò        ← MẪU SỐ THẬT của cả suite, không phải "3 bộ đã khai"
  1 lời gọi rời khỏi máy: POST api.openai.com/v1/embeddings → nguồn tests/test_api/test_injection.py
[ĐO] PO-agent kiểm lại: test_injection.py có 0 hit `_ton_tien|dang_dong_bang|skipif` — KHÔNG cổng nào
```
**Đối chứng dương của chính phép dò** (thiếu nó thì "chỉ 1 kết quả" = chưa nhìn kỹ): 5 file ứng viên
khác vẫn xanh với khoá giả ⟹ chúng thật sự không gọi.
⚠️ **TRẠNG THÁI THỨ BA:** phép dò chỉ bắt lời gọi phía **HOST**. `test_thanh_phan_tai_lieu_kho.py`
chạy `docker exec` vào container mang khoá RIÊNG ⟹ **NGOÀI tầm đo: KHÔNG ĐO ĐƯỢC**, không được đọc
thành "đã sạch".

🔴 **MỘT GỐC CHO CẢ HAI: chốt chặn chi phí đang nằm ở TẦNG `tests/`, còn cửa ra Internet nằm ở TẦNG
CLIENT NHÀ CUNG CẤP.** Lớp ① là `skipif` **bên trong file test** ⟹ không phủ script nháp, không phủ
file test quên khai, không phủ lượt chat. Lớp ② đã tắt vĩnh viễn. ⟹ **Đường đi tiền hiện không có
lớp nào phủ, và sẽ không có lớp nào phủ cho người sau.**
Và `CLAUDE.md §7` **in sẵn câu lệnh `pytest tests/`** ⟹ người mới **sẽ** gõ nó.

**Bản vá đúng — MỘT CHỖ, BA VIỆC:** chốt chặn phải cắm ở `_khoa_cho_nha_cung_cap()` — **nơi MỌI
đường ra ngoài đi qua**. Một cờ ở đó phủ **test + script nháp + lượt chat**. Và đó **đúng là chỗ**
`so_luot_da_phat` (sổ nợ §5.B, *"nguồn ĐỘC LẬP thật duy nhất với envelope"*) cần cắm ⟹ vừa **chặn
chi tiêu**, vừa **đo chi tiêu** — đúng trục ưu tiên PO đặt 18/08 (§5.A0).

**Điều phối (PO-agent chốt 18/08) — HAI việc, KHÔNG phải chọn một:**
1. **NGAY, tester:** cổng riêng cho **đúng 2 ca `/policy-docs`**, **KHÔNG** gắn `_ton_tien` cả file —
   gắn cả file sẽ **skip luôn 10 ca appsec** (SQLi/XSS) không tốn tiền. Luật J: đừng làm im một cổng
   đang canh đúng để bịt một cổng khác.
2. **TIẾP THEO, tech-lead:** chốt chặn + `so_luot_da_phat` ở tầng client. Đây là việc **thay nửa (b)**
   của bất biến — (b) đã có sẵn 12 ca mẫu và không chảy máu; cái này thì đang chảy.


### 🔴 G. ĐÍNH CHÍNH — PO-AGENT ĐỌC MỘT OUTPUT BỊ CHÍNH MÌNH CẮT, LẦN THỨ HAI TRONG NGÀY

*(Bắt bởi **security**. PO-agent phát biểu sai, đã kiểm lại và xác nhận security đúng cả hai điểm.)*

**PO-agent viết** (§5.F, bản đầu): *"4 tool mang `@_locked` + kiểm `otp_verified_at`; `search_policy`
dòng 949 mang `@tool` trần."* **Sai hai chỗ:**

```
[ĐO] customer_tools.py, liệt kê ĐỦ, không cắt cửa sổ:
  791 @tool  792 @_locked   lookup_transaction       813 kiểm otp   OTP_VIEW_MAX_MINUTES
  842 @tool  843 @_locked   get_customer_history     862 kiểm otp   OTP_VIEW_MAX_MINUTES
  875 @tool  876 @_locked   create_ticket            904 kiểm otp   OTP_STEPUP_FRESH_MINUTES
  921 @tool  922 @_locked   request_human_handoff     —  KHÔNG kiểm
  949 @tool  950 @_locked   search_policy             —  KHÔNG kiểm
[ĐO] thân _locked (735-790): `otp_verified_at` chỉ xuất hiện trong CHÚ THÍCH, 0 lần làm điều kiện
```

**Sai ①** — `search_policy` **KHÔNG** mang `@tool` trần: dòng 950 là `@_locked`. **Cả NĂM tool đều có.**
**Sai ②** — **`@_locked` KHÔNG PHẢI cổng OTP.** Nó làm hai việc khác: chặn lượt đã bị bỏ
(`TurnAbandonedError`) và **bất biến chống livelock**. Câu *"4 tool mang `@_locked` + kiểm OTP"*
**gộp hai cơ chế không liên quan**, rồi đọc sự vắng mặt của cơ chế thứ hai như sự vắng mặt của cả hai.

🔴 **CƠ CHẾ SINH LỖI — cùng lớp với đính chính ADR-031, lần thứ HAI trong ngày, cùng một người:**
PO-agent chạy `grep … | head -40`. Output **bị cắt đúng ở dòng 949**. Dòng 950 tồn tại, nằm **ngay
dòng sau chỗ bị cắt**. ⟹ **đọc một khung nhìn đã bị chính lệnh của mình lọc, rồi dùng như toàn cảnh.**
Ca ADR-031: `grep` trúng dòng 143, câu trả lời ở dòng 150. Ca này: `head` cắt ở 949, câu trả lời ở 950.
> ⚠️ **Và dấu hiệu đã nằm SẴN trong chính câu sai, bắt được MIỄN PHÍ lúc đọc, không cần chạy gì:**
> câu viết **"4 tool"** nhưng chỉ kèm **BA số dòng**. **Mẫu số và danh sách lệch nhau trong một câu —
> Luật F.** Không ai phải mở `psql` mới thấy.

**FINDING THẬT — và nó không nằm ở chỗ ai cũng nhìn:**

```
request_human_handoff   docstring: "KHÔNG cần OTP (đây là routing request…)"   ← MIỄN TRỪ CÓ KHAI
search_policy           docstring: không một chữ nào về OTP                     ← MIỄN TRỪ IM LẶNG
```

⟹ Vấn đề **không phải** *"thiếu một cổng"* mà **"một MIỄN TRỪ không phân biệt được với một CHỖ BỎ
SÓT"**. Trên mã hai thứ ấy **trông y hệt nhau** — cùng là sự vắng mặt của mấy dòng. Người đọc sáu
tháng sau biết ngay `request_human_handoff` là **quyết định**; với `search_policy` họ **không có cách
nào biết**. **Luật H ở tầng mã nguồn:** một bên báo triệu chứng kèm chẩn đoán, một bên để lại **im
lặng — và im lặng thì không bác được**.

**Thẩm quyền: KHÔNG vi phạm** (security rà, không nâng hạng). Ràng buộc cứng 2 ✅ · ràng buộc cứng 4 ✅
(OTP gác **truy cập dữ liệu KHÁCH**; `search_policy` đọc tài liệu công khai) · `authority-matrix` ✅ ·
ADR-005 ✅. Miễn trừ **nhiều khả năng cố ý và trên trục "truy cập dữ liệu" là ĐÚNG**.

**Nhưng có TRỤC THỨ HAI chưa ai cân:** `search_policy` là tool **duy nhất mà một khách CHƯA xác thực
OTP làm cho văn bản mình gõ RỜI HẠ TẦNG** (`/agent/chat` → `search_policy` → `search_policy_text()` →
`store.search()` → `embed_query()` → OpenAI/Hoa Kỳ). Bốn tool kia dừng ở cổng OTP trước khi chạm gì.
Miễn trừ được cân trên trục *"có đọc dữ liệu khách không"* (đáp án đúng: KHÔNG) — nhưng đó **không
phải trục có chi phí** của tool này. **Trục có chi phí là ĐƯỜNG RA, và chưa ai cân nó trên trục đó.**

⚠️ **Security tự bác một khung của chính họ trước khi gửi** — [ĐO] `main.py:610`: `@limiter.limit(
"20/minute")` **+** `RedisConcurrencyLimiter`. Có chặn, **hai lớp**. ⟹ tụt từ *"lỗ thủng ngân sách"*
xuống *"một cái đuôi chi phí nhỏ trên một miễn trừ chưa khai"* — **hạ hai bậc, KHÔNG phải việc gấp.**

**Đề nghị (security, PO-agent duyệt): HAI DÒNG CHỮ, KHÔNG phải một cổng.**
🔴 **KHÔNG thêm OTP cho `search_policy`** — nó chặn đúng ca dùng hợp lệ (*"phí rút tiền bao nhiêu"*)
để đổi lấy một rủi ro vừa bị hạ hai bậc. Đúng phản xạ *"thêm một cổng cho yên tâm"* mà **Luật A** gọi tên.
1. **Viết miễn trừ vào docstring `search_policy`**, đúng khuôn `request_human_handoff` đã dùng, nêu
   **CẢ HAI trục**. *Miễn trừ có khai thì lần sau sửa được; miễn trừ im lặng thì người ta xoá nhầm
   hoặc nới nhầm.* (tech-lead, một dòng)
2. **Đề xuất PO:** thêm vào `contracts/agent-tools.yaml` trường khai ***"tool này có ĐƯỜNG RA ngoài
   hạ tầng không"***. Hôm nay contract khai tên + lược đồ, **không khai đường ra**. Có trường đó thì
   `search_policy` là tool **duy nhất** bật cờ ⟹ **câu hỏi tự hiện ra** thay vì phải có người đi tìm.
   Đụng contract ⟹ đủ §10.


### 🔴🔴 H. "PREFIX CACHE HIT 0%" LÀ SAI — ĐO ĐƯỢC 50,8%, VÀ BẢN VÁ ĐỀ XUẤT ĐÃ TỪNG BỊ REVERT

*(security báo 18/08 là **đòn bẩy caching lớn nhất**. PO-agent phân định trước khi giao việc. **Phát
biểu tiêu đề SAI**; ba phần còn lại của phân tích thì **đúng và có giá trị** — tách bạch kỹ, đừng
vứt cả gói.)*

**Security phát biểu:** *"tiền tố ổn định ~189 ký tự, prompt cache cần ≥1024 token ⟹ **hit 0%, mọi
lượt, từ trước tới nay**"*, và đề xuất dời `{current_time}` xuống cuối prompt.

**[ĐO] PO-agent — sổ `usage.jsonl` CÓ SẴN trường `cached_input_tokens`, 90 dòng:**

```
dòng đọc được CẢ input LẪN cached   54/90        ← MẪU SỐ (36 dòng còn lại: None/0, ba rổ)
tổng input_tokens                  923.787
tổng cached_input_tokens           468.864
⟹ TỈ LỆ CACHE THẬT                  50,8%       ← KHÔNG PHẢI 0%
dòng có cached > 0                  50/54
```

**Và một NGUỒN ĐỘC LẬP THỨ HAI nói cùng chiều** — `scripts/BAN-GIAO-coder-2026-08-17.md:133-137`,
mục *"Chỗ đã thử và THẤT BẠI — đừng thử lại"*:
> *"Dời `{current_time}` xuống cuối prompt để cứu prefix cache — đo: **cache 85,0% → 86,3%. ĐÃ
> REVERT.** Lý lẽ tĩnh rất thuyết phục (`current_time` ở byte 208/15.094) nhưng **phần lớn cache hit
> là TRONG CÙNG MỘT LƯỢT, không liên lượt.**"*

⟹ **Bản vá đề xuất KHÔNG PHẢI việc chưa ai làm — nó đã được làm, đo được +1,3 điểm, và revert.**

🔴 **CƠ CHẾ SINH LỖI — nhãn `[ĐO]` gắn lên một phần SUY LUẬN:**
Phép đo *"tiền tố 189 ký tự"* là **thật**. Bước *"⟹ hit 0%"* là **suy luận**, và nó sai vì nó giả định
tiền tố cache-được **chỉ là system prompt**. Thực tế trong một lượt nhiều lời gọi, **toàn bộ ngữ cảnh
lời gọi trước** trở thành tiền tố của lời gọi sau ⟹ cache ăn **trong cùng một lượt**. Đúng nguyên văn
điều bàn giao đã ghi.
> **Luật C:** đối chiếu chéo chỉ hoạt động ở nơi **CÓ VẬT ĐO** — ở đây **có vật đo** (`cached_input_tokens`
> nằm sẵn trong sổ, 90 dòng, chưa ai mở) và phát biểu lại được dựng bằng **lý lẽ tĩnh**. Điều khoản
> thi hành: **so SỐ, không so KẾT LUẬN.**
> **Luật M áp cho chính đội:** *"đòn bẩy lớn nhất, bản vá một dòng"* là kết quả **ai cũng muốn nghe**
> trên đúng trục PO vừa ưu tiên ⟹ **không gì kích hoạt phản xạ soi lại**. Suýt tiêu ô ưu tiên số một.

**⟹ KHÔNG giao việc dời `current_time`.** Nếu ai muốn mở lại: bàn giao đã chỉ hướng khác —
**giảm ĐỘ PHÂN GIẢI thời gian (chỉ ngày)**, chưa đo, và **đổi hành vi**.

---

**BA PHẦN CÒN LẠI CỦA PHÂN TÍCH: ĐÚNG, GIỮ NGUYÊN, và chúng KHÔNG phụ thuộc phát biểu sai ở trên.**

**H1 · [ĐO] Chưa có cache tầng ứng dụng nào.** Mọi `lru_cache` trong `src/` đều `maxsize=1` (nạp cấu
hình/model một lần). `_bam_truy_van` mới chỉ **ghi log** `query_hash` (`rag/search.py:116`), chưa làm
khoá cache của gì. ⟹ mọi ràng buộc dưới đây là **phòng ngừa, đúng thời điểm**.

**H2 · 🔴 RANH GIỚI TIỀN TỐ CACHE *LÀ* MỘT RANH GIỚI PHÂN LOẠI DỮ LIỆU.**
```
TRÊN ranh giới → nhà cung cấp GIỮ LẠI và TÁI DÙNG qua nhiều request
DƯỚI ranh giới → mỗi request một lần
```
Hôm nay tiền tố là **hằng số thuần** — `build_system_prompt` đóng cứng `customer_name="quý khách"`
(`prompt.py:79`, ADR-010 gỡ tên khách từ 13/08) ⟹ **an toàn**.
**Bẫy ở BƯỚC SAU:** ai muốn đẩy hit rate lên sẽ **đưa THÊM lên tiền tố** — lịch sử hội thoại, hồ sơ
khách, kết quả tool lượt trước. Đúng khoảnh khắc ấy tiền tố **thôi là hằng số** và bắt đầu là **dữ
liệu khách được nhà cung cấp giữ lại**. Ba thứ làm nó không bị bắt: **không cổng nào canh**
(`test_invariants` không nhìn thấy *thứ tự các đoạn trong một chuỗi prompt* — **hạng mù §5.D2, lần thứ
ba**) · **không diff nào của ta thấy** · **triệu chứng là một con số ĐI ĐÚNG HƯỚNG TA MUỐN** (hit rate
tăng) ⟹ **không ai đi kiểm** — Luật M, lần này áp cho một chỉ số **hiệu năng**.
> 📌 **RÀNG BUỘC, ghim cạnh `build_system_prompt`:** *Mọi thứ nằm TRÊN ranh giới cache phải là **HẰNG
> SỐ BIÊN DỊCH**. Đưa bất cứ giá trị nào phái sinh từ khách lên tiền tố là một quyết định **PHÂN LOẠI
> DỮ LIỆU**, không phải một tinh chỉnh hiệu năng.*

**H3 · 🔴 RÀNG BUỘC CỨNG 3 ĐẢM BẢO TRUY VẾT, KHÔNG ĐẢM BẢO TƯƠI.** Ràng buộc 3 đòi số liệu **tồn tại**
trong một `tool_result` có thật — **không đòi tươi**. Một kết quả cache **là** một `tool_result` có
thật ⟹ **thoả ràng buộc cứng 3 một cách HÌNH THỨC** trong khi nói với khách một trạng thái đã cũ.
*Ca cụ thể:* `lookup_transaction` cache 5 phút · giao dịch `pending → completed` · agent trả lời
`pending` · con số **truy vết được tới một dòng có thật** ⟹ **mọi cổng đều xanh.**
*Tiền lệ đúng chiều đã có trong repo* (`services/complaint_intake.py:52`): *"nạp lại mỗi lần gọi là đủ
nhanh — **không cần cache, tránh rủi ro đọc dữ liệu cũ**"*.

| tool | cache được? | |
|---|---|---|
| `search_policy` | ✅ **có** | tài liệu đổi theo tuần. **Tool duy nhất caching có nghĩa** — và cũng đúng tool tốn embedding |
| `lookup_transaction` · `get_customer_history` | 🔴 **không** | trạng thái là thứ khách **đang khiếu nại**; cũ = sai |
| `create_ticket` · `request_human_handoff` | — | tool GHI |

🔴 **Và `search_policy` phải vô hiệu hoá cache theo KHO RAG, KHÔNG theo đồng hồ.** ADR-026 buộc kho chỉ
phục vụ tài liệu **đã duyệt**; một tài liệu `supervisor` vừa duyệt mà cache còn giữ câu trả lời cũ thì
**ADR-026 bị vô hiệu bởi một lớp cache** — cơ chế chạy đúng, vẫn bị đi vòng.

**H4 · 🔴 SẮC LẠI 18/08 — việc rút 10.2 làm H2 và H4 NẶNG THÊM, không nhẹ đi.**
- **H2 nặng hơn:** bản cũ viết *"cái bẫy nằm ở bước sau"* như một rủi ro **tương lai**. **Sai chiều.**
  Cache **đang ăn 50,8% THẬT** ⟹ prompt cache **không phải cơ chế lý thuyết**, nên áp lực đẩy tỉ lệ
  ấy lên cao hơn là áp lực **có thật, đang diễn ra**. Ranh giới tiền tố = ranh giới phân loại dữ liệu
  cần được **ghim SỚM HƠN**, không phải muộn hơn.
- **H4 đổi hạng:** bản cũ là *"chưa biết TPM"* — một ô trống. Nay **tiền đề đã xác nhận**: ta biết
  **50,8% là có thật**, nên câu *"50,8% ấy có được MIỄN khỏi TPM không"* thành câu **có trọng lượng**:
  **CÓ miễn** ⟹ trần hiệu dụng **cao hơn ta tưởng**. **KHÔNG miễn** ⟹ mọi tối ưu cache **không chạm
  được trần đang chặn buổi 150 người** (§6.⓵).
  ⟹ **Hai thế giới rất khác nhau, và ta chưa biết đang ở cái nào.** Đây là **câu ③ phiếu Alibaba**
  (§5.A3) — PO đã gác cả phiếu 18/08, **và quyết định đó không bị mở lại ở đây**; chỉ ghi rằng **giá
  trị của riêng câu ③ đã tăng** kể từ lúc gác, để PO có dữ kiện nếu muốn xem lại.

⚠️ **BA số cho cùng một vật — khai, KHÔNG hoà:** `graph.py:949` ghi `233/16.082` · bàn giao ghi
`208/15.094` · security đo 18/08 `189/15.094`. Mẫu số **15.094 khớp hai trong ba** ⟹ `16.082` ở
`graph.py:949` **nhiều khả năng đã cũ** (một dòng cho tech-lead). **Chưa truy nguyên và KHÔNG CẦN —
không quyết định nào còn treo trên ba con số này** sau khi 10.2 đã rút.


### 🔴 I. MỞ RỘNG PHẠM VI (KHÔNG phải đính chính) — kho checkpoint nằm NGOÀI sơ đồ mã hoá

*(Bắt bởi **tester**, khi soi tiếp **sau khi** cổng plaintext trúng dự báo 4/4 tới từng chữ số.
PO-agent kiểm lại độc lập bằng `psql`, **chỉ đếm, không in một byte nội dung nào**.)*

```
[ĐO] phép dò của cổng quét KIỂU GÌ:
     character varying 83 · text 30   → 113 cột, QUÉT ĐƯỢC
     json 6 · jsonb 2 · bytea 2       →  10 cột, MÙ HOÀN TOÀN

[ĐO] checkpoint_blobs — chỉ ĐẾM:
     tổng                            6.213
     mang hình dạng Fernet (gAAAAA)      0     ⟹ 0% mã hoá
     CHỨA mã giao dịch "TXN2026…"    2.179
```

⟹ **`738` KHÔNG phải toàn cảnh.** Mẫu số của kho checkpoint (**6.213**) lớn gấp **8,4 lần** mẫu số
ADR-032 đang bàn (**761**).

✅ **KHÔNG AI SAI — đây là MỞ RỘNG PHẠM VI, không phải đính chính.** ADR-032 BỔ SUNG ① **đã khai đúng
mẫu số của nó**: *"[ĐO] cả bốn cột khai `Encrypted*`"*. Kết luận *"hệ thống mã hoá KHÔNG hỏng"* **đúng
BÊN TRONG mẫu số ấy**. Phân biệt này quan trọng: gọi nhầm nó là "đính chính" sẽ làm người đọc mất
niềm tin vào một phát biểu vốn trung thực.

🔴 **RANH GIỚI PHÁT BIỂU — giữ nguyên, đừng nới (Luật B mở rộng: phát biểu này đẩy người nhận vào
CHẾ ĐỘ NÀO):**
`2.179/6.213` là **số dòng chứa MÃ GIAO DỊCH**. **KHÔNG** phải *"2.179 dòng chứa PII khách hàng"*.
SĐT tài khoản hạt giống: **0/6.213**. Khoảng cách giữa hai câu ấy là việc **định hạng của security**,
không phải của tester và không phải của PO-agent.

⚠️ **Nối thẳng vào cảnh báo xoay khoá ở §1, và nó ĐẢO DẤU tin tốt:** `checkpoint_blobs` và
`investigation_logs.tool_input_json` **0% mã hoá** ⟹ chúng **KHÔNG bị ảnh hưởng** khi xoay
`FIELD_ENCRYPTION_KEY`. Nghe như tin tốt. **Nó là tin xấu:** nghĩa là một phần dữ liệu hội thoại
**chưa bao giờ được bảo vệ bởi khoá nào.**

**PHẠM VI — PO-agent chốt: ADR RIÊNG, KHÔNG mở rộng ADR-032.** Ba lý do:
1. **Khác LOẠI, đúng phân biệt đã dùng cho 032 vs 034:** ADR-032 là **nợ MIGRATE** trên một cột **đã
   được khai là mã hoá**; `checkpoint_blobs` **chưa bao giờ nằm trong sơ đồ** — không có gì để migrate.
2. **Ta KHÔNG sở hữu lược đồ ấy** — nó là bảng của LangGraph `PostgresSaver`. Bảo vệ nó là việc ở
   **tầng serde**, không phải đổi kiểu cột ⟹ **cơ chế khác, chi phí khác, rủi ro khác**.
3. **Gộp vào là khoá ADR-032 lại.** 032 đang gần đóng (① xong, ② chờ dựng ảnh, ③ cổng đã land); buộc
   nó chờ một bài toán nặng hơn là **cách chắc chắn nhất để cả hai không xong** — cùng lý lẽ đã dùng
   khi tách finding `tool_input_json` khỏi ADR-031.
🔴 **Cổng CỐ Ý không assert trên 10 cột đó, và đó là quyết định ĐÚNG** — *quyết định cột nào phải mã
hoá là việc của ADR, không phải của tester tự viết chính sách bằng một assertion.* Đúng thứ quy trình
§10 sinh ra để chặn.

**Chờ:** security **định hạng** (mã GD trần có phải finding mức nào) → PO thật duyệt ADR mới.


### 🔴🔴🔴 J. KHO CHECKPOINT CHỨA TOÀN BỘ BẢN GHI HỘI THOẠI, KHÔNG MÃ HOÁ — mức CAO

*(Security định hạng sau khi hỏi *"cái gì đã KHÔNG sinh ra dòng nào ở đây"*. PO-agent kiểm lại độc
lập bằng **byte thật**, **chỉ đếm, 0 byte nội dung được in, không giải mã gì**.)*

```
[ĐO] checkpoint_blobs WHERE channel='messages'
     tổng                       3.597
     mang hình dạng Fernet          0      ⟹ 0% mã hoá
     chứa "HumanMessage"        3.597      ⟹ TIN NHẮN KHÁCH, MỌI DÒNG
     chứa "AIMessage"           3.220
     kích thước bảng             37 MB     (security báo 105 MB — MẪU SỐ khác,
                                            có thể là mọi channel / trước nén. Chưa truy,
                                            KHÔNG ĐỔI kết luận)
[ĐO] FK trên mọi bảng checkpoint*   0
```

⟹ **Kho checkpoint không chứa "một ít mã giao dịch". Nó chứa TOÀN BỘ BẢN GHI HỘI THOẠI — gồm văn bản
KHÁCH TỰ GÕ — chưa mã hoá.** §5.I (2.179 dòng mã GD) là **phần vô hại nhất** của bức tranh này.

🔴 **VÌ SAO CẢ SECURITY LẪN PO-AGENT ĐỀU MÙ Ở VÒNG TRƯỚC — bẫy này sẽ tái diễn, [ĐO] chứng minh:**

```
dò TIẾNG VIỆT bằng BYTE THẬT      position('\xe1babf'::bytea in blob)  →  2.738   (ế)
                                   position('\xe1bb8b'::bytea in blob)  →  2.833   (ị)
dò qua encode(blob,'escape') ~ '[àáảãạăâđ…]'                          →      0   🔴 MÙ HOÀN TOÀN
```

`encode(…,'escape')` biến **mọi byte ngoài ASCII** thành escape bát phân ⟹ **mọi ký tự tiếng Việt biến
mất khỏi phép so khớp**, trong khi `TXN2026` (thuần ASCII) hiện ra bình thường.
> **Một bộ dò PII chạy trên `bytea` mà so khớp bằng CHUỖI sẽ THẤY đúng phần ASCII và MÙ đúng phần
> tiếng Việt** — tức **mù đúng phần chứa lời khai khách, thấy đúng phần vô hại nhất**. Kết quả nó trả
> về **không phải *"ít PII"*** mà là ***"chỉ những PII viết bằng chữ không dấu"***.
> **Luật L ở một mặt phẳng mới:** không phải ngưỡng lỏng/chặt, mà **bộ dò MÙ VỚI CHÍNH BẢNG MÃ của
> dữ liệu nhạy cảm nhất**. **Sửa: dò trên BYTE THẬT** (`position(…::bytea in blob)`).

**MỘT MITIGATION CÓ THẬT, [ĐO] chứ không giả định:** `ToolMessage` **đã được che** —
`_scrub_pii_cho_llm` (`customer_tools.py:495`) che `full_name`/`phone`/`account_no` trước khi vào hội
thoại LLM. **Đó chính là lý do SĐT ra `0/6.213` ở §5.I.**
🔴 ⟹ **Con số `0` ấy là bằng chứng CƠ CHẾ CHE ĐANG CHẠY, KHÔNG phải bằng chứng KHO SẠCH. Đừng ai trích
`0/6.213` như một lời trấn an.**
Còn **`HumanMessage` KHÔNG được che, và đó là CỐ Ý, đúng thiết kế** — ADR-025 QĐ1 bác che-lúc-ghi cho
Nhóm A. **Quyết định ấy đúng** — nó chỉ giả định lời khai được bảo vệ bằng **MÃ HOÁ** thay vì bằng che.
**Ở kho checkpoint KHÔNG CÓ VẾ THỨ HAI.**

🔴 **HỆ QUẢ NẶNG NHẤT — nó làm dấu ✅ ở §5.E thành GÂY HIỂU NHẦM:**

| | cột được chỉ định | bản sao plaintext |
|---|---|---|
| lời khai | 23/761 — nợ migrate (ADR-032) | `investigation_logs` 27 |
| **hội thoại** | **`messages.content` 467/467 — HOÀN HẢO** | **`checkpoint_blobs` 3.597 · 37 MB** |

Con số `467/467` **vẫn đúng**. Nhưng kết luận người đọc rút ra — *"nội dung hội thoại được mã hoá
at-rest"* — **SAI**. ⟹ **Người đọc không hỏi *"cột khai `Encrypted*` có sạch không"*; họ hỏi *"lời khai
khách có được bảo vệ không"*.** Ta trả lời câu thứ nhất và **để họ tưởng đã có câu thứ hai.**

**HẠNG: finding RIÊNG · mức CAO · hạng "HỆ SỐ NHÂN BÁN KÍNH", KHÔNG phải "cửa mới".**
Security **cố ý không chọn hạng cao nhất**, và nói rõ cả hai vế:
- **KHÔNG phải P0 gấp:** không kẻ tấn công mới · không đường ra ngoài hạ tầng · không vi phạm ràng
  buộc cứng nào. Cùng CSDL, **cùng biên tin cậy** — ai đọc được cái này thì đã đọc được 738 dòng
  `complaints`. **Không phải cửa mới; cùng một cửa, mở ra căn phòng lớn hơn nhiều.**
- **LÀ mức cao vì BA tính chất CỘNG LẠI, không vì kích thước:** ① **8,4×** mẫu số ADR-032, **39×**
  finding ① · ② **vô hình với job retention** ([ĐO] **0 FK**) trong khi `thread_id` = `"USR-0145:…"`
  **CHỨA `user_id`** ⟹ **không tra ra được nhưng QUY TRÁCH NHIỆM ĐƯỢC — kết hợp tệ nhất** · ③ **0 cơ
  chế prune/TTL/delete** trong `src/`, ~21 MB/ngày, **không trần**.
  *Khác `investigation_logs`: ở đó `NO ACTION` ít nhất làm job **báo lỗi**. Ở đây **job chạy xong, báo
  thành công, bản ghi hội thoại vẫn nguyên. Không cổng nào kêu.***
- 🔴 **CHI PHÍ CỦA VIỆC KHÔNG LÀM, phát biểu chính xác:** ngày ADR-032 backfill xong, **sẽ có người
  viết *"lời khai khách đã được mã hoá at-rest"*. Câu đó SAI chừng nào kho checkpoint còn như hôm nay**
  — và sai theo kiểu **nghe rất đúng**, đi vào hồ sơ, rồi không ai kiểm lại. **Luật G ở tầng hồ sơ,
  bán kính lớn nhất trong ngày.**

**Sắc lại ca "đảo dấu" §5.I:** cách nói đúng **không phải** *"xoay khoá an toàn hơn ta tưởng"* mà
**"xoay khoá KHÔNG BẢO VỆ GÌ ở đây, vì ở đây CHƯA TỪNG có gì được bảo vệ"** — hai câu khác nhau:
ADR-032 nói về rủi ro **HỎNG** dữ liệu; mục này nói về **vùng khoá chưa bao giờ với tới**.

**BỐN RÀNG BUỘC cho ADR mới** *(security nêu ràng buộc, KHÔNG thiết kế — thiết kế thuộc tech-lead)*:
1. 🔴 **Bảo vệ ở tầng SERDE, KHÔNG đổi kiểu cột** — `PostgresSaver` sở hữu lược đồ; đổi cột là đánh
   nhau với thư viện mỗi lần nâng phiên bản.
2. **ĐỪNG che `HumanMessage`** — cùng lý lẽ ADR-025 QĐ1. **Mã hoá, không che.** Bản vá đi hướng scrub
   là **đi ngược một quyết định đã ký**.
3. 🔴 **Giải quyết RETENTION CÙNG LÚC, không để lần sau.** 0 FK ⟹ mục này **sẽ không tự lộ ra** khi ai
   viết job xoá. ADR chỉ nói *"mã hoá kho checkpoint"* mà không nói *"và xoá theo cùng lịch với hồ sơ
   khiếu nại"* ⟹ ta đổi **kho plaintext vĩnh viễn** lấy **kho ĐÃ MÃ HOÁ vĩnh viễn**.
4. **Nghiệm thu phải dò trên BYTE, không dò trên chuỗi đã escape** — nếu không, cổng nghiệm thu **báo
   xanh đúng theo cách nó đã mù hôm nay**.

**THỨ TỰ:** **SAU** ADR-032 (rẻ, đóng khoảng trống **đã khai**), **TRƯỚC** phần còn lại. Không phải vì
nhỏ hơn — vì **đắt hơn và ta không sở hữu lược đồ**, nên nó cần một **QUYẾT ĐỊNH**, không cần một script.

**KHÔNG kết luận:** ❌ có PII **người thứ ba** trong kho (rất có thể có, **chưa đo** — cần NER, chưa
chạy) · ❌ về `fin05ttl`/`fin05do` (số này của `fin05`) · ❌ không giải mã, không trích, không xem tin
nhắn nào.


### 🔴 K. THIÊN LỆCH CỦA CHÍNH PO-AGENT — BA LẦN, MỘT HƯỚNG: thổi PHẠM VI lúc relay

*(Ca thứ ba do **tech-lead** bắt, trước khi phát biểu kịp vào STATE. Ghi lại vì **ba lần cùng một
hướng là TÍN HIỆU, không phải ba tai nạn** — Luật K.)*

```
① "search_policy là tool DUY NHẤT không có cổng OTP"   → SAI: một trong HAI (§5.G)
② "lớp ① đủ chặn một mình"                             → SAI: pytest vẫn ra Internet (§5.F)
③ "da_phat là MỐC NỀN ĐẦU TIÊN của dự án"              → SAI: bộ đếm trong RAM (dưới)
```

**Cả ba lệch CÙNG MỘT HƯỚNG: làm cho cơ chế nghe RỘNG HƠN thứ nó thật sự làm.**
🔴 **Bộ lọc chung, PO-agent tự khai:** *ở vị trí relay, tôi thưởng cho câu nghe GỌN và DỨT KHOÁT* —
và *"mốc nền đầu tiên của dự án"* gọn hơn *"bộ đếm trong tiến trình phục vụ ca đối chứng"* rất nhiều.
⟹ **Đừng nhận phát biểu PHẠM VI từ PO-agent mà không kiểm.** Ba lần đều do phiên khác bắt, không lần
nào do PO-agent tự bắt.

**[ĐO] ca ③ — `so_luot_da_phat()` KHÔNG PHẢI MỘT CUỐN SỔ:**
```
docker-entrypoint.sh:16-17   UVICORN_WORKERS mặc định 4  ⟹ BỐN bộ đếm độc lập
src/cong_ra_ngoai.py:173     _dem: dict[str, int]        ⟹ trong RAM, về 0 mỗi lần recreate
grep so_luot_da_phat src/    2 hit, cả hai cùng một file ⟹ 0 endpoint · 0 ghi volume
```
**Phát biểu ĐÚNG:** bộ đếm **trong tiến trình**, phục vụ **ca đối chứng** — nó chứng minh chốt chặn
có bắn hay không (16/16 ca nghiệm thu đọc nó). Nó **KHÔNG** trả lời được *"hôm nay cả hệ thống phát
bao nhiêu lượt ra ngoài"*. **CHƯA PHẢI SỔ.**
⚠️ **Hệ quả cho lời dặn `down -v`:** vẫn dặn, nhưng **đúng lý do** — `usage.jsonl` (sổ thật, volume,
sống qua recreate) và `postgres_data`. **KHÔNG phải vì `da_phat`** — nó không mất gì, vì chưa bao giờ
có gì được ghi xuống.

> **Vì sao ca này suýt đắt hơn hai ca kia:** nếu nó vào STATE như PO-agent viết, sáu tháng sau sẽ có
> người đi tìm *"mốc nền đầu tiên"* và **tìm thấy một con số bằng 0 trông hoàn toàn hợp lệ** — đúng
> hình dạng `so_luot_goi_model=0` ở §8, **dựng lại bởi chính đội vừa vá nó**.

**GIAI ĐOẠN 2 — ba việc, cùng một câu *"làm cho cơ chế đủ tốt như cách nó đang được MÔ TẢ"*:**
đổ `da_phat` vào `usage.jsonl` · đảo mặc định cờ thành **TỪ CHỐI** + compose khai `=1` (phủ **script
nháp**) · một đường đọc bộ đếm từ ngoài tiến trình. **Sau khi ảnh mới chạy ổn, TRƯỚC ADR-033.**


### ✅ L. DỰNG ẢNH 18/08 — nghiệm thu ĐỘC LẬP ĐẠT, kèm MỘT nhãn đang nói dối

**PO-agent kiểm bằng phép của mình, không đọc lại số của tech-lead:**
```
băm src/ cây làm việc   d5b73a04d6ef · 55 file
fin05 · fin05ttl · fin05do   bam-anh d5b73a04d6ef ×3   sửa-tay 0·0·0   ⟹ lệch× 0·0·0  ✅
cổng ngân sách token    6.565/7.550 · system 4.587 (+0) · tool 1.978 (+0) · 3 passed   ✅
security_finding        3 failed · 3 passed  (chạy từ HOST)
```

🔴 **NHÃN `BUILD_COMMIT` ĐANG NÓI DỐI — ca thứ ba, đúng thứ `dau_ma_nguon.py` sinh ra để chống.**
```
[ĐO] BUILD_COMMIT trong cả ba container   bf1bd5a
[ĐO] HEAD                                  9f864c6   (chuyển docstring search_policy → chú thích #)
[ĐO] git show bf1bd5a:src/agents/tools/customer_tools.py  vs  bản trong cây  →  🔴 KHÁC
```
Mã trong ảnh là của **cây làm việc lúc dựng** (đã có bản vá `9f864c6`), nhưng nhãn trỏ về **`bf1bd5a`**
— một commit mà `customer_tools.py` **vẫn còn docstring 376 token**. ⟹ **Ai lần theo nhãn sẽ tìm thấy
mã KHÁC thứ đang chạy.**
✅ **Băm `bam_ma_nguon` khớp tuyệt đối ở cả bốn chỗ ⟹ KHÔNG SAI VẬT.** Đúng như docstring
`dau_ma_nguon.py` đã viết: ***`build_commit` định danh KHO, nhãn băm định danh MÃ — tin nhãn băm.***
Nhưng đây là **lần thứ ba trong dự án** nhãn ấy lệch, nên nó không còn là tai nạn: **`BUILD_COMMIT`
chỉ đúng khi cây làm việc == HEAD lúc build**, và nếp *chạy → xác minh → mới commit* của đội **bảo đảm
điều đó thường KHÔNG đúng**. Ghi lại để không ai dùng cột ấy làm mỏ neo chẩn đoán.

**Ba ca đỏ `security_finding` — đã phân định, KHÔNG ca nào là hồi quy:**
2 ca là **cổng plaintext** (đỏ **đúng chủ đích**, ADR-032 chưa backfill). Ca thứ ba
`test_live_chat_pii_gap::…raw_phone_number_is_not_masked` là **P0 CŨ**, xác nhận bằng **hai đường độc
lập**: file sửa lần cuối **12/08** (`553b9e8`, sáu ngày trước) · nó import `live_chat` +
`complaint_intake`, **không module nào nằm trong 5 file `src/` đổi hôm nay**.
⟹ **Kỳ vọng đúng là `3 failed`**, không phải `2`. *(PO-agent relay "2" từ tester mà quên P0 có sẵn —
đúng lớp §5.K: phát biểu phạm vi không kiểm.)*

⚠️ **Và một bẫy PO-agent tự đâm vào, ghi để người sau khỏi vấp:** chạy
`docker exec … pytest /app/tests` cho **12 lỗi thu thập** (`FileNotFoundError: 'docker'`,
`No module named 'eval'`). **KHÔNG phải cổng hỏng** — 12 file ấy gọi `docker` CLI và đọc `eval/`, **phải
chạy từ HOST**. Suýt báo động giả về chính lần dựng vừa nghiệm thu.


### ✅ M. ADR-032 ② BACKFILL ĐÃ CHẠY — nghiệm thu độc lập ĐẠT. §5.E đóng MỘT PHẦN

**PO-agent kiểm bằng phép của mình, sau khi tech-lead làm đủ ①→④:**
```
[ĐO] psql thẳng, GROUP BY toàn bảng   complaints.description_raw: MÃ HOÁ 761 · PLAINTEXT 0
[ĐO] đọc qua ĐƯỜNG SẢN PHẨM (container py3.12, ORM, nhánh ba trạng thái):
       tổng đọc được        761
       rỗng                   0
       CÒN dạng gAAAAA        0   ← >0 nghĩa là giải mã HỎNG, trả nguyên bản mã
[ĐO] sửa-tay 0·0·0 · băm cây == băm ảnh d5b73a04d6ef · lệch× 0·0·0
```
**738 → 0.** Cột Nhóm A nặng nhất nay mã hoá 100% trên `fin05`.

🔴 **PHÉP QUYẾT ĐỊNH KHÔNG PHẢI CON SỐ `761/0`** — nó là con số **ta muốn nghe**, và theo **Luật M**
đó là lúc không gì kích hoạt phản xạ soi lại. Hai phép dưới mới phân định, và **cả hai được khai
TRƯỚC khi chạy**, không nghĩ ra sau:
- **① so TỪNG DÒNG với bản sao lưu:** `761/761 khớp · 0 lệch`. Chi tiết làm nó có nghĩa: **giải mã CẢ
  HAI bên qua cùng `_giai_ma()` của sản phẩm**, không so chuỗi thô — bản gốc là *738 plaintext + 23 đã
  mã hoá*, so thô sẽ cho 738 "lệch" và dẫn người ta đi chữa một thứ không hỏng.
- **② đọc qua ORM trong container** *(phép PO-agent thêm)*: cảnh báo `doc_gia_tri_chua_ma_hoa`
  **738 → 0**, lỗi `giai_ma_that_bai_nghi_xoay_khoa` **0**.
  🔴 **Đây là số duy nhất chứng minh 738 dòng đổi trạng thái THEO CÁCH SẢN PHẨM NHÌN THẤY** — mọi số
  khác đều đo bằng script của tech-lead, trên Python của tech-lead. Thiếu phép này thì toàn bộ báo cáo
  là *"dụng cụ của tôi nói dụng cụ của tôi đúng"*.
  ⭐ Và nó là **ca đối chứng TỰ NHIÊN** cho nhánh ba trạng thái land sáng nay: `738 → 0` là chuỗi thời
  gian ngắn nhất chứng minh **cả cơ chế lẫn bản vá** cùng hoạt động.

**Hai điều kiện PO-agent thêm đã bắt được HAI lỗi thật, trước khi ghi:**
1. *"Sao lưu phải được KIỂM PHỤC HỒI, không chỉ được tạo"* → bản `pg_dump --data-only` đầu tiên có đủ
   761 INSERT, kích thước đẹp, băm đẹp — **và không tự phục hồi được**.
2. *"So BYTE khoá host với khoá container"* → [ĐO] host **KHÔNG có `FIELD_ENCRYPTION_KEY`**; phản xạ
   mặc định cả buổi chiều là `Fernet.generate_key()`. Ở đây nó là **ghi đè 738 dòng bằng khoá không ai
   giải được**.
> 🔴 **Cả hai thuộc CÙNG MỘT LỚP, và tech-lead gọi đúng tên nó:**
> ***"thứ tôi đã làm đúng 20 lần hôm nay ở một ngữ cảnh mà nó vô hại"***. Hai điều kiện ấy **không bắt
> sự cẩu thả** — chúng bắt **một thói quen ĐÚNG bị mang sang chỗ nó SAI**. Đó là lý do chúng đáng tồn
> tại kể cả khi người thao tác đang rất cẩn thận.

**Quyết định thiết kế giữ lại — đừng ai đảo:** **KHÔNG làm alembic revision.** Entrypoint chạy
`alembic upgrade head` **mỗi lần container khởi động, trên cả ba ngăn xếp VÀ production** ⟹ revision
hoá nghĩa là **738 dòng lời khai khách bị viết đè tự động, không ai bấm nút**.
> ***Di trú LƯỢC ĐỒ nên tự động; di trú NỘI DUNG thì không.***
Và ba phép kiểm sau khi ghi nằm **trong cùng giao dịch, `raise` để rollback** — *một script ghi dữ
liệu mà chỉ CẢNH BÁO khi phát hiện sai là script đã ghi rồi mới nói.*

🔴 **CHƯA ĐÓNG — §5.E đóng ĐÚNG MỘT PHẦN:**
- Backfill **chỉ chạy trên `fin05`**. **`fin05ttl` · `fin05do` · PRODUCTION là BA QUẦN THỂ RIÊNG**,
  mỗi nơi **một quyết định, một lần sao lưu**. tech-lead **không tự mở rộng** — đúng.
- **ADR-032 ③** (cổng trong `tests/`) thuộc tester.
- **CSDL `vutdi_kiem_saoluu` GIỮ LẠI** — nó là bản phục hồi **đã kiểm**, và là **đường lùi duy nhất còn
  lại**. Xoá khi PO thấy đủ an toàn.
- **§5.J (kho checkpoint) KHÔNG bị đụng tới** — và nay nó thành **bản plaintext DUY NHẤT còn lại của
  lời khai khách**, đúng như security dự đoán: *vá vũng nước làm vòi chảy lộ ra rõ hơn.*

⚠️ **Dự báo 9/10 — dòng lệch tech-lead TRUY thay vì làm ngơ, và lệch về phía DỄ CHỊU:** `not
security_finding` dự báo 569, thật **570** (tổng ca thu thập 628→630 vì **tester land song song**).
`src/` đổi 0 file, backfill không đụng `tests/`. **Luật K:** lệch về phía nhiều-ca-xanh-hơn là loại
lệch **không ai đi truy** — họ truy vì *"nếu nó lệch xuống 568 thì tôi đã truy ngay"*.


### 🔴🔴🔴 N. ADR-026 "Đang hiệu lực" — NHƯNG CƠ CHẾ TRUNG TÂM CỦA NÓ KHÔNG TỒN TẠI. Sự cố nó đóng VẪN ĐANG MỞ

*(Bắt bởi **security**, khi áp vế thi hành Luật M cho H3 — *mở sổ trước khi lập luận*: đi tìm trường
nào đo thẳng *"kho RAG đổi lúc nào"*. **Không có trường nào**, và trên đường đi đụng thứ này.
PO-agent kiểm lại độc lập từng điểm.)*

```
[ĐO] models.py:543   CheckConstraint("status IN ('processing','indexed','failed')")
                     ⟹ KHÔNG có giá trị nào nghĩa là ĐÃ DUYỆT
[ĐO] approved_by/approved_at  chỉ tồn tại trên `resolutions` (models.py:412-413)
                              KHÔNG có gì tương đương cho tài liệu chính sách
[ĐO] cả BA route /policy-docs (POST 1223 · GET 1249 · DELETE 1273)
                              → require_role("partner_admin") · KHÔNG route supervisor nào
[ĐO] dữ liệu thật             2 tài liệu, CẢ HAI status='indexed'
```

**ADR-026 Quyết định 1 ghi:** *"Agent chỉ được phục vụ chunk của tài liệu **`da_duyet`**"*.
⟹ **Không có trạng thái `da_duyet`. Không có ai duyệt. Tài liệu đi thẳng `processing → indexed` rồi
được phục vụ.**

🔴 **VÌ SAO CA NÀY NẶNG HƠN §5.D2 (`/ready`) VÀ ADR-025 QĐ2 (`assigned_to`) — CA THỨ BA CÙNG LỚP,
NHƯNG KHÁC HẲN VỀ HẬU QUẢ:**
Hai ca kia là **tính năng chưa tới**. **ADR-026 được viết ĐỂ ĐÓNG MỘT SỰ CỐ CÓ THẬT** — [ĐO] chính
ADR-026: `16/08, 08:23:14Z → 08:42:47Z` (**19 phút 33 giây**), hai file nội bộ (`business_rules.md`
bảng số `verified=false` · `scenario-candidates-momo-faq.md`) **nằm trong kho ĐANG PHỤC VỤ**.
⟹ **Khoảng trống ấy VẪN ĐANG MỞ.** Cùng một thao tác, cùng một người thiện chí, cùng một màn hình —
**sẽ tái diễn y hệt.**
> Và ADR-026 tự viết ra chẩn đoán ấy: *"người đầu tiên vấp vào khoảng trống đó là một người thiện chí,
> dùng đúng cửa được thiết kế cho họ, không làm sai quy trình nào — đó là định nghĩa của khoảng trống
> thiết kế."* **Bản vá được thiết kế, được PO duyệt, và chưa bao giờ được xây.**

🔴 **CƠ CHẾ CONTRACT-FIRST KHÔNG BẮT ĐƯỢC — và lần này nó ĐAU HƠN §5.D2.** `CheckConstraint` **CHÍNH LÀ**
thứ `tests/test_invariants.py` introspect (đọc qua AST). Nó đọc `('processing','indexed','failed')`,
so với contract — **contract cũng không có `da_duyet`** ⟹ **khớp hoàn hảo ⟹ 23/23 XANH**.
⟹ **Ca thứ ba của cùng một HẠNG MÙ** (§5.D2 · security §3 · ca này): contract-first canh **thứ khai
được trong một tệp YAML**; nó **không canh được khoảng cách giữa QUYẾT ĐỊNH và THI HÀNH**.
⭐ **Và ca này là ca chứng minh cổng ADR-033 đáng xây** — cổng *"mọi ADR Đang-hiệu-lực nêu tên file/cơ
chế thì thứ đó phải tồn tại"*. Ba ca trước là lý lẽ; **ca này có một sự cố đứng sau.**

**Hệ quả cho H3 — security tự bác việc của chính mình, và đúng:** *"H3 như đặt ra là PREMATURE, và lý
do premature LỚN HƠN chính H3"* — không thể dựng *"vô hiệu hoá cache theo sự kiện duyệt"* khi **sự kiện
duyệt không có biểu diễn nào**. Dựng nó sẽ cho ra một cơ chế **trông như đang thi hành ADR-026 và
không thi hành gì** — đúng hình dạng *"hồ sơ trông kín hơn"*. **H3 GÁC LẠI cho tới khi ADR-026 được
thi hành.**

🔴 **CÁI BẪY SẼ CẮN NGƯỜI TIẾP THEO — `CHUAN_HOA_VERSION` KHÔNG PHẢI khoá vô hiệu hoá cache.**
Nó **TÊN là** version, **NẰM TRÊN** collection Chroma, **TRÔNG ĐÚNG NHƯ** thứ ta cần — và không phải.
[ĐO] `src/rag/store.py:138` → `CHUAN_HOA_VERSION = 2`, một **hằng số gõ cứng trong mã**, ghi vào
metadata ở `:73` · `:160`, so ở `:184`. ⟹ nó đổi khi **TA ĐỔI MÃ** (cách chuẩn hoá text + model
nhúng), **KHÔNG đổi khi KHO ĐỔI NỘI DUNG**. **CẤM dùng làm khoá cache** — đó là *"hai định nghĩa của
cùng một vật"*, đúng lớp lỗi ADR-031 điều kiện ① đã cấm.
**Khoá đúng phải là hàm của NỘI DUNG KHO** — vd `(count(chunks), max(created_at), count(docs))`, phủ
được thêm + xoá. *(Bốn ứng viên đã rà, không cái nào phủ đủ `{thêm · xoá · duyệt · gỡ duyệt}`.)*

📌 **GHI VÀO ADR-026 TRƯỚC KHI AI CODE PHẦN DUYỆT — rẻ bây giờ, đắt sau:** *khoá cache phải gồm
**TRẠNG THÁI DUYỆT***. Thiếu nó thì cache **giữ nguyên câu trả lời sinh từ tài liệu chưa duyệt** sau
khi `supervisor` gỡ duyệt — ADR-026 bị **một lớp cache** vô hiệu.

**PHÂN BIỆT SẮC HƠN — ba ca cùng hạng mù KHÔNG bằng nhau, và trục phân biệt là CÓ KHAI HAY KHÔNG:**
| ca | ADR có TỰ KHAI là chưa code không? |
|---|---|
| `/ready` (ADR-028, §5.D2) | ❌ không |
| `assigned_to` (ADR-025 QĐ2) | ✅ **CÓ** — ADR tự khai *"tính năng nghiệp vụ MỚI"* |
| **duyệt tài liệu (ADR-026)** | ❌ **không** — và nó đóng một **sự cố có thật** |
⟹ Một ADR **tự khai** phần chưa xây thì **không cần cổng nào canh**. Cổng chỉ cần cho ca **không khai**.

🔴 **RANH GIỚI PHÁT BIỂU — security tự dựng, PO-agent giữ nguyên, ĐỪNG NỚI:**
*"**Cơ chế duyệt CHƯA TỒN TẠI**"* ✅ đo được — **KHÔNG** phải *"đang có tài liệu chưa duyệt được phục
vụ"* ❌ chưa đo. Kho có 2 tài liệu, **cả hai do `partner_admin` nạp qua đúng cửa**. Hai câu khác nhau,
và câu thứ hai đẩy người đọc vào **chế độ xử lý sự cố** cho một sự cố **chưa được chứng minh**.

**🔴 CẦN PO THẬT:** ADR-026 do PO chốt 16/08 sau một sự cố thật. **Việc thi hành nó chạm `contracts/`
+ `migrations/` + `src/`** ⟹ đủ §10. **Trình PO: thi hành ngay, hay chấp nhận rủi ro có khai?**


### 🔴🔴 O. ĐÍNH CHÍNH §5.M — "738 → 0" ĐÚNG CHO MỘT NGĂN XẾP, KHÔNG ĐÚNG CHO HỆ THỐNG

*(Ô `O` chỉ bỏ trống ở **SỔ LUẬT §7**, không ở đây — hai không gian tên khác nhau.)*
*(Bắt ĐỘC LẬP bởi **security** và **tester**, cùng lúc, không ai biết việc của ai. PO-agent kiểm lại.)*

```
[ĐO] complaints.description_raw, cả ba ngăn xếp cục bộ:
     fin05      mã hoá 761  ·  PLAINTEXT   0   ✅ đã backfill
     fin05ttl   mã hoá   4  ·  PLAINTEXT 738   🔴 NGUYÊN VẸN
     fin05do    mã hoá 607  ·  PLAINTEXT   0
[ĐO] 738 dòng ở ttl: created_at 05/05/2026 → 14/08/2026  ⟹ ĐÚNG CÙNG TẬP đã có ở fin05
```
⟹ ***"738 → 0"* đúng cho `fin05`, và CHỈ cho `fin05`. Tính cả ba ngăn xếp cục bộ: VẪN 738.**

🔴 **SẮC THÁI TESTER THÊM — `fin05do` sạch KHÔNG phải bằng chứng backfill tốt: NÓ CHƯA BAO GIỜ BẨN**
(kho nạp **sau** khi `EncryptedText` đã có). Đọc *"hai ngăn xếp đã sạch"* là **dân số pha tạp** (§8):
**BỐN quần thể, mỗi cái sạch/bẩn vì một LÝ DO KHÁC NHAU.**

🔴 **CƠ CHẾ — VÀ NÓ NẰM Ở PHÉP NGHIỆM THU, KHÔNG Ở BẢN VÁ.**
Bản vá **đúng**. Phép nghiệm thu của PO-agent cũng **chặt** (đọc lại qua ORM trong container, 761 đọc
được, 0 dòng còn bản mã). **Không ai làm ẩu.**
> **PHÉP NGHIỆM THU THỪA HƯỞNG MẪU SỐ CỦA BẢN VÁ.** Bản vá chạy trên `fin05` ⟹ người kiểm mở `fin05`
> ⟹ kết luận mang tên *"backfill xong"* thay vì *"backfill xong TRÊN `fin05`"*.
> **Tập tự đến bị lọc bởi CHÍNH THAO TÁC đang được kiểm.**
Đây là §8 áp lên một **NGHIỆM THU** thay vì một **phép đo** — **hiểm hơn**, vì nghiệm thu là bước ta
dựng ra **ĐỂ BẮT** thiếu sót. Ba ngăn xếp nằm ở **dòng thứ tư của §1**; không ai phải đi tìm. Nó chỉ
**không có mặt trong CÂU HỎI**.
⚠️ **Và security mắc đúng lỗi ấy cùng ngày, độc lập:** §11 định hạng kho checkpoint **chỉ trên
`fin05`**. Họ **có tự khai** — nhưng **khai một khoảng trống không lấp nó**, y hệt ca §10.2.
**Hai người, hai artefact, một bộ lọc, một ngày** ⟹ tính chất của **quy trình**, không phải lỗi của ai.

**MẪU SỐ ĐẦY ĐỦ cho §5.J (kho checkpoint) — gấp 1,7× con số đã báo:**
```
             blob(messages)  HumanMessage  tiếng Việt   dung lượng
fin05            3.597          3.597        3.413       105 MB
fin05ttl         2.482          2.482        2.318        95 MB
fin05do             62             62           59       127 kB
TỔNG cục bộ      6.141          6.141        5.790      ~200 MB
```
**Hạng §5.J GIỮ NGUYÊN mức CAO — security KHÔNG nâng**, lý do họ nêu đúng: mẫu số lớn hơn **không đổi
bản chất** (cùng biên tin cậy, không kẻ tấn công mới), nó đổi **độ chính xác của hồ sơ**. *Nhưng một
định hạng đúng với mẫu số sai vẫn là một định hạng phải làm lại.*

**🔴 CÂU CẦN MỘT QUYẾT ĐỊNH, KHÔNG CẦN THÊM PHÉP ĐO:**
> **`fin05ttl` và `fin05do` là ngăn xếp DÙNG MỘT LẦN, hay dữ liệu ở đó phải được bảo vệ như `fin05`?**
- **DÙNG MỘT LẦN** ⟹ khai ra, và **mọi phát biểu về mã hoá at-rest phải KÈM PHẠM VI** (*"trên ngăn xếp
  phục vụ"*). 738 dòng ở `ttl` là **chấp nhận được CÓ Ý THỨC**.
- **KHÔNG** ⟹ **backfill CHƯA XONG**; cả hai mục ADR-032 phải chạy trên `fin05ttl`.
**Im lặng thì không nhận được** — hôm nay đội đang tin *"lời khai khách đã mã hoá at-rest"*, và **câu
đó SAI với 738 dòng**.

⭐ **VÀ `fin05ttl` NAY LÀ TÀI SẢN KIỂM THỬ, KHÔNG PHẢI RÁC** *(tester)*: cổng plaintext chuyển ĐỎ→XANH
nhờ backfill, nhưng **không ai chứng minh nó CÒN BIẾT ĐỎ** — nửa *"KÊU lúc bất thường"* của **Luật A**
bỏ trống. Cách rẻ nhất trông có vẻ là nhét một dòng plaintext giả vào CSDL — **tester TỪ CHỐI** (ghi
vào ngăn xếp đang phục vụ, Luật I). **Không cần:** `fin05ttl` là **quần thể bẩn CÓ THẬT, sẵn có,
không do ta tạo ra**. Ca đối chứng hai chiều đã dựng, và **chiều thứ hai mới quan trọng**: ngày
`fin05ttl` được nạp lại, ca ấy **báo MẤT KHẢ NĂNG ĐỐI CHỨNG** thay vì lặng lẽ xanh.
🔴 ⟹ **Ai định dọn `fin05ttl` phải biết: nạp lại nó sẽ TẮT ca đối chứng duy nhất chứng minh cổng
plaintext còn sống.**

**QUẦN THỂ THỨ TƯ — `app.adaptivealgo.uk` (production): CHƯA AI ĐO, KHÔNG AI CHẠM.** Mọi số ở §5.J và
mục này là của **BA ngăn xếp CỤC BỘ**. Ai trích chúng như *"toàn hệ thống"* là **một mẫu số sai nữa**.
Nếu một ADR có phạm vi production thì **quần thể quyết định nhất là quần thể duy nhất chưa ai đo** —
đó là **câu xin phép PO thật**, chưa hỏi.

**KHÔNG kết luận:** ❌ `fin05ttl` là **sự cố** — nó là **bản vá chạy chưa hết phạm vi, mà phạm vi đúng
thì CHƯA AI ĐỊNH NGHĨA**. ❌ ai sai — **thiếu sót nằm ở CÂU HỎI, không ở THAO TÁC**.


### 🟢 C. ĐÍNH CHÍNH 18/08 — hai phát biểu trong kho tài liệu là SAI, đã kiểm tận mắt

**C1 · "khách đọc lý do từ chối SAI (*vượt 200.000 TPM*)" — SAI. Không có đường nào tới mắt khách.**
Bắt bởi **tech-lead**; PO-agent kiểm lại độc lập trước khi ghi.

```
[ĐO] src/api/main.py:621   là CHÚ THÍCH
[ĐO] src/api/main.py:629-630  chuỗi khách thật sự nhận:
     "Hệ thống đang xử lý nhiều yêu cầu cùng lúc, bạn vui lòng thử lại
      sau khoảng 30 giây giúp mình nhé."          ← KHÔNG số, KHÔNG chữ "TPM"
[ĐO] grep -rn "TPM" src/        → 5 hit, 5/5 là chú thích/docstring
     rate_limit.py:60,62,69 · main.py:379 · main.py:621
[ĐO] grep -rnE "200\.000|200000|200_000" src/  → 3 hit, 3/3 chú thích
     (rate_limit.py:60 viết "200K" — cách viết thứ tư, chỉ lọt lưới nếu grep theo dấu chấm)
[ĐO] grep -rnE "TPM|200\.000" frontend/src/    → 0 hit
```

⟹ **Đổi HẠNG việc, không chỉ đổi chữ:** không phải *"khách đang đọc chữ sai"* (đối ngoại, gấp)
mà là *"căn cứ chết nằm trong chú thích"* (đối nội, không gấp). Nó **là cùng một việc** với sổ nợ
§6.⓸ `_AGENT_MAX_CONCURRENT` mất căn cứ — **không phải việc riêng**, và **không đi cùng đợt ①**
nữa, vì lý do gom nó vào ① chính là cái vừa mất.

> **Vì sao lỗi này sinh ra:** dòng 621 nằm đúng **5 dòng trên** một `detail=` khách-đọc-được. Ai
> `grep "200.000"` sẽ thấy hit ở 621, liếc xuống thấy `HTTPException(detail=…)` ngay dưới, rồi
> ghép hai thứ. **Cùng lớp lỗi với đính chính ADR-031** (grep trúng dòng 143, câu trả lời ở dòng
> 150) và đúng nếp kiểm §8 — *một khung nhìn đã bị chính lệnh grep của mình lọc, rồi dùng như toàn
> cảnh*. Lần này **bộ lọc là KHOẢNG CÁCH 5 DÒNG.**

**C2 · "`test_f31_f32` chưa có cổng chi phí (tester biết, chưa sửa)" — SAI từ lúc viết.**
`scripts/BAN-GIAO-coder-2026-08-17.md` §④ ghi câu đó và dặn *"ĐỪNG chạy `pytest tests/` toàn bộ"*.

```
[ĐO] cổng land ở 07ee30e  17/08 22:41  "cổng chi phí cho test_f31_f32 — lỗ CUỐI trong họ này"
[ĐO] bàn giao viết ở      17/08 22:46  (4ac2162) và commit muộn hơn nữa (3734c2b)
[ĐO] git merge-base --is-ancestor 07ee30e 4ac2162  → ĐÚNG
[ĐO] tests/test_agents/test_f31_f32_duong_agent_that.py:133  skipif(not duoc_phep_ton_tien())
```

🔴 **ĐỪNG đọc thành "vậy chạy `pytest tests/` được rồi".** Cái chết là **LÝ DO**, không phải lệnh
cấm: lệnh cấm còn hai chân khác chưa ai kiểm — bộ test thứ tư chưa khai cổng (§3, mẫu số "3/3 bộ
ĐÃ BIẾT"), và **lớp ② đang mất**. Đây đúng ca Luật B: *một lời dặn KHÔNG hành động cạnh một dữ
kiện ĐẨY hành động thì dữ kiện thắng* — nên nói rõ cả hai vế.


---

## 6. BỐN CON SỐ QUYẾT ĐỊNH — kèm mẫu số, đừng trích thiếu

### 🔴🔴 P. CÂY LÀM VIỆC BỊ CHUYỂN NHÁNH GIỮA LƯỢT — và KHÔNG có triệu chứng nào

*(PO-agent tự phát hiện khi `src/` đột nhiên chỉ còn khung mẫu. PO thật khôi phục.)*

```
[ĐO] git reflog
d09d4bb HEAD@{2026-08-18 14:25:52 +0700}: checkout: moving from dev/learning-loop to main
```

`main` = `d09d4bb "Initial commit"` — **khung mẫu do `phoenix-mentor[bot]` tạo 26/07**, đi sau nhánh
làm việc **453 commit**. Trong khoảng cây đứng ở đó, trên đĩa **không tồn tại**: `CLAUDE.md` ·
`docs/STATE.md` · `docs/DECISIONS.md` · `contracts/` · `tests/test_invariants.py` · toàn bộ `src/`
thật. Cái `src/` nhìn thấy là `example_tool.py` · `example_node.py` của khung mẫu.

🔴 **VÌ SAO KHÔNG CÓ TRIỆU CHỨNG — đây mới là phần đáng ghi.**
```
[ĐO] git status  →  "nothing added to commit"   (SẠCH)
```
Cây **hoàn toàn tự nhất quán**: index khớp HEAD, HEAD khớp đĩa. Không file nào tự khai *"tôi là bản
khung mẫu"*. **Sạch là tính chất BÊN TRONG một ảnh chụp; danh tính là tính chất GIỮA các ảnh chụp** —
và `git status` chỉ đo được cái thứ nhất.

🔴 **SAI LẦM CỦA PO-AGENT — ĐI TÌM Ở REPO KHÁC TRƯỚC KHI HỎI CÂY ĐANG ĐỨNG Ở ĐÂU.**
Thấy `src/` thành khung mẫu, tôi **sang `P-121-new` lục** (một bản sao cũ, PO xác nhận không còn
dùng) để tìm xem "code thật rơi đâu" — tốn lượt, và đưa PO một khúc lạc đề. **Một lệnh
`git rev-parse --abbrev-ref HEAD` đặt ĐẦU TIÊN đã đóng cả vụ.** Tôi đi tìm **vật** trước khi hỏi
**mình đang đứng ở đâu**.

⭐ **VÀ ĐÂY LÀ CA THỨ BA CỦA MỘT LỚP DỰ ÁN NÀY ĐÃ BIẾT — ở tầng thứ ba:**
| tầng | cơ chế đã dựng | dựng lúc nào |
|---|---|---|
| **ảnh Docker** | `bam_ma_nguon` — băm nội dung `src/`, không tin nhãn | đã có |
| **nhãn commit của ảnh** | `BUILD_COMMIT` tự nối `-CAY-KHAC-HEAD` khi cây ≠ HEAD | 18/08 |
| **cây làm việc trong PHIÊN** | ❌ **KHÔNG CÓ GÌ** | ← lỗ này |
⟹ Đội đã hai lần tự dựng cơ chế chống *"hai định nghĩa của cùng một vật lệch trong im lặng"* — và
**chưa lần nào áp nó cho chính cây mình đang gõ lên**. ⟹ **Luật Q.**

**MỨC RỦI RO THẬT — không phải mất dữ liệu, mà là thứ khác:**
```
[ĐO] dev/learning-loop  9a7666e   ahead 55  — toàn bộ việc 18/08 CÒN NGUYÊN
[ĐO] origin/dev/learning-loop  27b6ea3     — 55 commit ấy CHƯA ĐẨY LÊN GITHUB
```
Không mất gì. **Nhưng 55 commit hôm nay chỉ tồn tại trong kho local trên MỘT máy** — và lý do chưa
đẩy được là CI/billing (§5.A0 vòng 2). Hai việc tưởng rời nhau hoá ra **cùng một rủi ro**: máy hỏng
là mất trắng một ngày.

**KHÔNG kết luận:** ❌ ai chạy lệnh checkout — PO-agent **không** chạy nó, và không đi đoán tiếp.
❌ đây là phá hoại — cây dùng chung, một cú `checkout` nhầm tab là đủ.

### ⓵ Trần thật là TPM, và ta ĐÃ VƯỢT ở cấu hình buổi 150 người

```
trần TPM 1.000.000 / 14.198 token/lượt =  70,4 lượt/phút   ← TRẦN THẬT
trần RPM        600 /   2,39 gọi/lượt  = 251,0 lượt/phút   ← không bao giờ chạm trước

150 người × 0,50 lượt/ph =  75 lượt/ph → TPM 🔴 106%
150 người × 1,00 lượt/ph = 150 lượt/ph → TPM 🔴 213%
100 người × 0,50         =  50 lượt/ph → TPM     71%  ✅
```

🔴 **BIẾN QUYẾT ĐỊNH LÀ NHỊP GÕ, KHÔNG PHẢI CODE** — điều khiển bằng **kịch bản chạy**:
```
nhịp ≤0,5 lượt/ph/người → T1 chỉ cần  6,1% lượt đơn  (gần như chắc đạt)
nhịp  1,0               → cần        53,0%           (BẤT KHẢ, không bản vá nào cứu kịp)
```
⚠️ `14.198 token/lượt` là trung bình lượt **THÀNH CÔNG** ⟹ mọi ngưỡng trên là **CẬN DƯỚI**.
5% lượt hỏng ở 60K ⟹ 106% thành ~123%.

### ⓶ Lượt HỎNG là lượt ĐẮT NHẤT, và là lượt DUY NHẤT ghi 0

```
1 lượt hỏng (livelock)  49.700 – 71.600 token   ← đắt gấp 3,3–4,7 lần lượt chạy xong
1 lượt bình thường      15.136
sổ ghi                  0        ← đã vá `0 → None` (620de3e), nhưng chỉ ở envelope
```
**Cơ chế livelock (`[ĐO]`, chuỗi 16 message khôi phục từ PostgresSaver):** khách đã đăng nhập
**chưa xác thực OTP phiên** → hỏi câu cần tra cứu → tool trả `status=error` → model **không có tool
nào để xin OTP** (đúng thiết kế — OTP ở tầng HTTP) → **không sửa được điều kiện nên THỬ LẠI y hệt**
→ không gì đếm số lần thử → lặp tới khi trần thời gian cắt. **8 lời gọi, 6 lần `lookup_transaction`
cùng tham số.**

**Tần suất `[ĐO]`: 1/13** — *cho trước một lỗi OTP, xác suất lặp*. **12/13 dừng sau ĐÚNG MỘT lần
và xử lý ĐÚNG** (trả lời khách · tạo vé · bàn giao).
⚠️ **KHÔNG dùng con số `4%`** (13/370 thread) — 370 là **dân số pha tạp**, gồm nhiều thread thử.

**So 12 ca đối chứng trên 6 biến: KHÔNG biến nào tách được**, và có **2 ca giống hệt ca lặp cho
kết quả khác nhau** ⟹ *"không tìm thấy điều kiện phân biệt trong 6 biến đã đo"* — **mạnh hơn**
"chưa tìm ra", **yếu hơn** "đã chứng minh là ngẫu nhiên".
⟹ **Không có đầu vào nào để lọc** ⟹ sửa prompt là bản vá **xác suất** đánh vào hiện tượng **xác
suất**: giảm tỉ lệ, **không đóng cửa**. **Chỉ bất biến tất định đóng được.**
> Bất biến có **hai nửa**: `(a)` phát hiện+dừng — tất định, **ở đây nằm TRỌN phần tiết kiệm**;
> `(b)` nói gì với khách — **đã có sẵn 12 ca mẫu**, không phải nghĩ ra hành vi mới.
> `(a)` land một mình vẫn ăn trọn tiết kiệm (dừng ở lời gọi thứ 2 → fallback sẵn có → vẫn ra vé,
> sớm hơn 6 lời gọi, rẻ hơn ~40K).

### ⓷ Sổ chi tiêu ghi 1/6 tới 1/9 số thật

```
đã ghi sổ    28.000
3 lượt hỏng 149.000 – 215.000
THỰC TẾ     177.000 – 243.000
```
**`[ĐO]` — đếm-thiếu KHÔNG phải giả thuyết:** `14:26:44.157` ta bỏ → `14:26:45.335` DashScope trả
**HTTP 200 TRỌN VẸN, 1,2s SAU**. Nhà cung cấp tính theo thứ họ **sinh**, không theo thứ ta **đọc**.
🔴 **Giả thuyết chưa xác nhận:** đây là lời giải cho câu *"sao hết 2,3M token?"* — phân định bằng
**A4** (đối chiếu dashboard).

### ⓸ `_AGENT_MAX_CONCURRENT = 20` MẤT CĂN CỨ

Nó được cỡ từ *"trần OpenAI 200.000 TPM ⟹ ~13 lượt/phút"*. Trần thật giờ là **1M**. Con số 200k
còn sống ở **3 chỗ trong `src/`** (`rate_limit.py:62` · `main.py:379` · `main.py:621`).

⚠️ **KHÔNG đọc thành "đang tự chặn ở 1/5 năng lực"** — đó là ghép số của trục **TPM** vào trục
**đồng-thời**. Limiter là trần **ĐỒNG THỜI**, thông lượng = `20 × 60/T`:

```
kịch bản                tok/lượt   T hoà vốn   T thật   ai chặn   biên
NHẸ (lượt đơn)           11.727      14,1s      9,0s     TPM     1,56×
trung bình toàn bộ       15.497      18,6s     11,3s     TPM     1,65×
PO (nặng, 5 lượt)        17.494      21,0s     15,5s     TPM     1,35×
```
🔴 **KHÔNG ghép chéo hai biến** — `token/lượt` và `giây/lượt` **tương quan** (hội thoại nặng thì
vừa nhiều token vừa lâu). Ghép `T` của kịch bản này với hoà-vốn của kịch bản kia là mô tả **một hội
thoại KHÔNG TỒN TẠI**.
⟹ Ghép đúng: **TPM chặn trước ở cả ba.** Nhưng biên ở **kịch bản demo chỉ 1,35×**.
> **CẢNH BÁO CÓ NGƯỠNG:** *nếu `T` trung vị **của kịch bản NẶNG** vượt ~18s, limiter thành nút
> thắt trước TPM — đo lại `_AGENT_MAX_CONCURRENT` trước khi tối ưu tiếp.* Đo từ sổ usage, 0 token,
> **lọc theo loại hội thoại** (trung vị chung 9,0s trông rất an toàn và **sẽ không bao giờ kêu**).
> Một reranker cộng ~5s/lượt là đủ đảo trục chặn.

---

## 7. SỔ ĐĂNG KÝ LUẬT — STATE là nơi cấp phát DUY NHẤT

> Phiên nào đúc luật mới → **đề xuất, KHÔNG tự đặt ký hiệu**. (17/08 đã có va chạm: hai Luật D đúc
> cách nhau 8 phút ở hai file, vì hai không gian tên song song không ai cấp phát.)

🔴 **RANH GIỚI HAI KHÔNG GIAN TÊN — viết ra 18/08, trước nay CHƯA AI VIẾT, và đó là lỗ thật.**
§7 vẫn ghi *"STATE là nơi cấp phát DUY NHẤT"*, nhưng [ĐO] 18/08 có **HAI dãy đang sống song song**:

```
dãy CHỮ  A–M    luật XUYÊN VAI (đo lường · suy luận · bằng chứng)   sổ: docs/STATE.md §7
dãy SỐ   1–19   nghề VIẾT TEST (assertion · fixture · đối chứng)     sổ: tests/CHUAN-VIET-TEST.md
```

**Cả hai vẫn do PO-agent ĐÓNG DẤU** — điều đổi là *"sổ DUY NHẤT"* thành **"người cấp phát duy nhất,
HAI sổ"**. Câu cũ sai về mặt mô tả, và chính vì nó sai mà tester 18/08 tự đúc `Luật 19`: dãy số
**không có sổ nào ở STATE** để mà tra.
**Chọn dãy nào:** luật chỉ có nghĩa **bên trong việc viết test** → dãy SỐ. Luật áp cho **mọi vai**
(kể cả người không viết test) → dãy CHỮ.

**Luật 19** *(tester đúc 18/08 — PO-agent kiểm: dãy số chạy liên tục 1→18, **19 là số kế tiếp đúng,
không va chạm**; đóng dấu, giữ nguyên ký hiệu tester đã dùng)* — **Khả năng QUAN SÁT của một test có
thể bị chính CƠ CHẾ XỬ LÝ LỖI của hệ xoá đi — và nguy hiểm không nằm ở ca lộ ra, mà ở những ca CÙNG
KHUÔN VẪN XANH.**
> **[ĐO] 18/08:** bốn ca duyệt HITL cùng khuôn (dựng resolution → gọi `/approve` sai điều kiện → 403 →
> đọc CSDL). Ba xanh, ca thứ tư `sample_db.get(...) is None` — **hàng biến mất**. Cơ chế: fixture dùng
> CHUNG session với route, `_override_session` **rollback** khi route ném `HTTPException` ⟹ hạt giống
> chưa commit bị **chính cú rollback của đường lỗi đang được kiểm** cuốn đi. **Cổng càng làm đúng
> việc, vật càng biến mất sạch.**
> 🔴 **Phần đắt nhất là BA CA XANH:** chúng đọc được vì tình cờ có một `request-approval-otp` **thành
> công** commit hộ ⟹ **đọc được nhờ MAY, không nhờ thiết kế** — và ba ca ấy **không có triệu chứng nào**.
> **Bốn quy tắc thi hành:** ① hạt giống của ca kiểm ĐƯỜNG LỖI phải **commit tường minh** · ② đuổi cache
> trước khi đọc khi test và sản phẩm dùng chung session · ③ **trạng thái thứ ba bắt buộc**: *"đọc được
> và ĐÚNG"* ≠ *"không đọc được"* — gộp thành TRƯỢT sẽ đẩy cả đội truy một vụ thủng ràng buộc cứng
> **không tồn tại** (suýt xảy ra thật) · ④ 🔴 **khi N ca cùng khuôn mà chỉ MỘT ca lộ vấn đề, đừng vá ca
> đó — hỏi vì sao N−1 ca kia KHÔNG lộ.**
> **Khác Luật 1 ở tiền đề, không ở mức độ:** Luật 1 hỏi *"assertion có phân biệt được không"*; Luật 19
> hỏi một câu **nằm TRƯỚC** — *"vật có còn ở đó để mà đọc không"*.

**Luật A** — cổng phải **IM** lúc bình thường **VÀ KÊU** lúc bất thường; nửa sau **chỉ chứng minh
được bằng ca đối chứng**.
**Luật B** — làm tròn một phát biểu lên đúng **MỘT nấc** là lớp sai đắt nhất.
> ⭐ **MỞ RỘNG (security):** kiểm tra cuối trước khi một phát biểu **RỜI KHỎI ĐỘI** là hỏi nó **ĐẨY
> NGƯỜI NHẬN VÀO CHẾ ĐỘ NÀO**, không chỉ hỏi nó có đúng không. *(vd: "quá hạn" → chế độ khắc phục
> vi phạm; "còn 58 ngày" → một việc có lịch. Cùng dữ kiện, hai hành động.)*
> ⭐ **HỆ QUẢ:** một khuyến nghị **KHÔNG hành động** và một con số **ĐẨY người ta hành động** nằm
> trong cùng một tin thì **con số THẮNG** — người đọc giữ con số, không giữ lời dặn.

**Luật C** — đối chiếu chéo chỉ hoạt động ở nơi **CÓ VẬT ĐO**; điều khoản thi hành = so **SỐ**,
không so **KẾT LUẬN**. *(Ngoài vùng có vật đo — vd đọc ToS mức hợp đồng — quy tắc thay thế là:
khai HẠNG BẰNG CHỨNG rồi DỪNG.)*
**Luật D** — cột phòng thủ phải có **NGUỒN ĐỘC LẬP**; "dư thừa" là **hệ quả**, không phải tiêu chí.
> ⚠️ **"Mang thông tin độc lập" ≠ "có NGUỒN độc lập".** Bảng chéo bác được *"một biến viết hai
> lần"* nhưng **KHÔNG** bác được *"hai hằng số gõ cạnh nhau"* — mà cái sau mới là thứ vỡ về sau.

**Luật E** — bộ ca xanh phải chứa **PHÂN BỐ CÁC LÝ DO**; nhánh không bao giờ bắn = nhánh **chưa
được kiểm**, kể cả khi độ phủ ghi 100%.
**Luật F** — mọi con số vào một quyết định phải mang **MẪU SỐ** trên **CÙNG DÒNG**.
> ⚠️ Mẫu số phải **cùng quần thể với câu hỏi**. To hơn ≠ đúng hơn: *2 lần lặp của đúng lượt tệ
> nhất mạnh hơn 33 mẫu trộn lẫn các loại lượt.*

**Luật G** — một cơ chế **đang làm đúng việc của NÓ** không có nghĩa nó đang làm việc **ta giả
định**.
**Luật H** *(security `ec8026e`)* — **nhánh xử lý lỗi in ra KẾT LUẬN thay vì TRIỆU CHỨNG là nhánh
NÓI DỐI ĐƯỢC.** Bộ đo báo *"tôi thấy gì"*, không báo *"tôi kết luận gì"*.
> **Bốn lần trong một ngày, ba người, bốn tầng:** `"không có sự kiện"` ≠ `"không đọc được"`
> (security) · `total_tokens=0` ≠ `None` (coder) · `ĐẠT·TRƯỢT·không_đo_được` (tester) ·
> `xanh·đỏ·SKIP` (coder). **Luôn là BA trạng thái, không phải hai.**

**Luật L** *(security đúc 18/08, PO-agent cấp số hiệu)* — **một bộ dò dùng để CHE và một bộ dò dùng
để ĐẾM cần HAI NGƯỠNG NGƯỢC NHAU.** Dùng chung một bộ dò cho cả hai là nhập hai bài toán có **hướng
sai số trái dấu**.
> **CHE:** false positive rẻ, false negative đắt ⟹ **nới rộng** (đúng playbook PII giai đoạn 3).
> **ĐẾM / BÁO CÁO:** false positive **ĐẮT** — nó sinh ra một con số **đẩy người đọc vào chế độ khắc
> phục sự cố cho một sự cố không tồn tại** ⟹ **siết chặt, và báo CẢ HAI SỐ**.
> **Bằng chứng [ĐO]:** cùng một regex SĐT — bản **lỏng** cho `447 dòng "chứa SĐT"` (thật ra khớp
> nhầm `TXN20260801000596` → chuỗi con `0801000596`); bản **nghiêm** cho `29 dòng / 4 giá trị / cả 4
> thuộc bộ seed`. `447` mà rời khỏi đội thì thành **một sự cố rò rỉ PII quy mô lớn**; số đúng là
> **hoạt động bình thường**. Đây là Luật B ở tầng **dụng cụ đo**.

**Luật M** *(security đúc 18/08, PO-agent cấp số hiệu — **tách khỏi L**, không ghép làm vế hai: L nói về
NGƯỠNG của bộ dò, M nói về **KHI NÀO người ta chịu kiểm bộ dò**; ghép lại thì loãng cả hai)* —
**XÁC NHẬN KHÔNG PHẢI BẰNG CHỨNG. Xác nhận là lúc cảnh giác RẺ NHẤT, nên là lúc hay bị bỏ nhất.**
> §8 dạy dấu hiệu là *"dữ liệu trông QUÁ GỌN"*. **Luật M thêm một dấu hiệu khó thấy hơn:
> *"kết quả KHỚP với thứ tài liệu đã hứa"*** — lúc ấy **không có gì kích hoạt phản xạ soi lại**.
> **Bằng chứng [ĐO], cùng một người, cùng một ngày:** ở ca `447` security soi lại bộ dò vì con số
> **không giống thứ họ mong đợi** ⟹ bắt được. Ở ca `LIMIT 3` họ **không soi**, vì kết quả **đúng như
> ADR-025 đã hứa** ⟹ trượt, và cả đội tin theo. **Hai kết cục ngược nhau, khác nhau đúng ở chỗ kết
> quả có làm người đọc ngạc nhiên hay không.**

**Luật N** *(tech-lead đúc 18/08, PO-agent cấp số hiệu)* — **một con số ĐẾM phải kèm PHÉP ĐẾM. Một số
suy ra bằng phép TRỪ trên tổng đã biết KHÔNG PHẢI một quan sát** — nó trông y hệt một số đếm được, và
nó không nhìn vào cái gì cả.
> **Vì sao Luật F chưa phủ:** F đòi **có mẫu số**; N đòi mẫu số phải **ĐƯỢC QUAN SÁT**. Một câu có thể
> thoả F mà vẫn sai theo N.
> **Bằng chứng [ĐO] 18/08 — chuỗi ba người, một câu:** tech-lead mở **3** tool đầu, thấy cả ba có cổng
> OTP, gặp `search_policy` không có ⟹ viết *"khác **4** tool kia"*. **`4` là phép trừ `5−1`, không phải
> phép đếm** — `request_human_handoff` **chưa bao giờ được mở ra xem**, và nó cũng không có cổng OTP.
> Câu sai đi tiếp: PO-agent chuyển nó cho security **kèm ba số dòng cho "4 tool"** (Luật F: mẫu số và
> danh sách lệch nhau trong một câu), security bắt được bằng cách **liệt kê đủ**.
> 🔴 **Ba ca cùng ngày, hai người, MỘT hình dạng — nhưng ca này KHÔNG CÓ LỆNH NÀO ĐỂ ĐỔ LỖI:**
> `grep` trúng 143 dừng, câu ở 150 *(PO-agent, ADR-031)* · `head -40` cắt ở 949, câu ở 950
> *(PO-agent, §5.G)* · **một phép trừ** *(tech-lead)*. Hai ca đầu bộ lọc nằm trong **công cụ**; ca thứ
> ba bộ lọc nằm **trong đầu**. ⟹ Sửa công cụ không đủ.

> 🔴 **VẾ THI HÀNH của Luật M** *(security đúc 18/08 sau khi tự rút §10.2 — PO-agent duyệt)*:
> **Trước khi phát biểu về một ĐẠI LƯỢNG, hỏi: *"sổ nào của ta có TRƯỜNG ĐO THẲNG đại lượng này?"*
> và MỞ NÓ RA TRƯỚC KHI LẬP LUẬN.** Có trường đó ⟹ mọi lý lẽ tĩnh là **GIẢ THUYẾT**, không phải
> kết quả.
> *Ở ca `cached_input_tokens` nó tốn **một dòng lệnh**. Nó không đòi ai nghi ngờ động cơ của mình —
> chỉ đòi **HỎI TRƯỚC KHI SUY**.*
>
> 🔴 **VÌ SAO CẦN VẾ THI HÀNH, VÀ ĐÂY LÀ DỮ LIỆU CHỨ KHÔNG PHẢI LỜI TỰ TRÁCH:**
> **KHAI RA MỘT THIÊN LỆCH KHÔNG VÔ HIỆU HOÁ NÓ.** Security **tự đặt tên** cho đúng bộ lọc của mình
> (*"kiểm mẫu số kỹ hơn khi con số bất lợi, lỏng hơn khi nó có lợi cho báo cáo của tôi"*) ở **§9.5**,
> rồi viết **§10.2** — cách đó **vài trăm dòng trong CÙNG MỘT TỆP** — và **không kiểm gì cả**.
> Thí nghiệm ấy đã chạy thật trên một người trong một phiên, kết quả **ÂM TÍNH**.
> ⟹ **Thứ chặn được KHÔNG THỂ là một quyết tâm cẩn thận hơn.** Phải là một **phép kiểm máy móc bắn
> BẤT KỂ kết quả nghe thế nào**.
> ⚠️ Và câu cấm làm đúng việc ấy **nằm trong chính đoạn đang được trích** — `graph.py:945-949`:
> *"`cached_tokens` là thứ **DUY NHẤT** nói prompt-cache có ăn hay không… **suy luận từ tài liệu
> không thay được số đo** — và suy luận đó **đã sai một lần**."*
> **Ba ca cùng ngày, khoảng cách thu dần:** grep 143→150 · `head` cắt 949→950 · **câu trả lời nằm
> trong CÙNG ĐOẠN VĂN đang được trích dẫn.**

> 🔴 **VẾ THI HÀNH THỨ HAI** *(tester đúc 18/08 — PO-agent duyệt; bổ sung cho vế của security, không
> thay thế)*: **kết quả KHỚP DỰ BÁO tới từng chữ số ⟹ soi PHẠM VI của phép đo, KHÔNG soi lại con số.**
> *Bằng chứng [ĐO]: ba lỗi tester tìm được 18/08 (`doc_id` mồ côi lọt im lặng · path gõ cứng · dòng
> báo lỗi giả định trước kết quả) — **cả ba con số đều ĐÚNG**; cái sai là **cái phép đo KHÔNG NHÌN
> TỚI**. Cả ba **không có triệu chứng nào**, và cả ba lộ ra vì hỏi tiếp **sau khi kết quả đã khớp**.*
> ⟹ Ghép với vế của security: **trước khi lập luận, mở sổ có trường đo thẳng; sau khi khớp, soi phạm
> vi.** Hai vế bịt hai đầu của cùng một khoảnh khắc mất cảnh giác.

**Luật P** *(tester đúc 18/08 — PO-agent cấp số hiệu)* — **NGHI NGỜ KHÔNG TỰ LAN SANG ARTEFACT. Một
phát biểu bị nghi trong hội thoại vẫn ĐỨNG NGUYÊN trong tài liệu — và tài liệu mới là thứ người sau
đọc.**

> ⚠️ **CỐ Ý BỎ TRỐNG KÝ HIỆU `O`.** Dự án có **hai dãy song song** (chữ A–… và số 1–…); `Luật O` và
> `Luật 0` **không phân biệt được khi đọc lướt hoặc khi grep**. Ô `O` **bỏ trống vĩnh viễn** — đừng ai
> lấp nó sau này.
>
> **Bằng chứng [ĐO] — ca của chính tester, cùng ngày, cách nhau chín tiếng:** sáng 18/08 họ viết ra
> lời nghi **đúng con số ấy, đúng file ấy** (*"hoặc số `446` trong `tests/TIEU-CHI-CI.md` đã cũ. Tôi
> chưa đo CI — không kết luận"*). Sau đó **commit BẢY lần vào `tests/`** — vùng chứa chính file đó.
> **`446` đứng nguyên.** Nó chỉ được niêm khi một `[ĐO]` **từ bên ngoài** đến vào buổi chiều.
> ⟹ **Nghi ngờ của chính mình, phát biểu rõ ràng, KHÔNG đủ để tự kích hoạt việc sửa.**
>
> **Vì sao đây là hình dạng RIÊNG, không phải biến thể của L/M/H/12:**
> **① NÓI RA CẢM GIÁC NHƯ ĐÃ XỬ LÝ** — phần độc nhất. Với các luật kia ta **biết** mình chưa xử lý;
> ở đây **hành vi phát ngôn tự giải toả nghĩa vụ**. **Càng nói kỹ càng dễ quên sửa.**
> **② HAI KÊNH CÓ TUỔI THỌ NGƯỢC NHAU** — nghi ngờ sống ở kênh **chú ý cao nhưng phù du** (một tin
> nhắn, đọc một lần); phát biểu cũ sống ở kênh **chú ý thấp nhưng BỀN** (một file, có người `grep` ba
> tuần sau). ⟹ theo thời gian **nghi ngờ phân rã, phát biểu tồn tại** — tỉ lệ xấu đi **ngược chiều
> trực giác**.
> **③ ĐIỂM MÙ CỦA CHÍNH NGƯỜI CẨN THẬN** — phiên cẩu thả không nghi gì nên không sinh ra khoảng cách
> này. Khoảng cách chỉ xuất hiện ở người **CÓ nghi** ⟹ luật này bắt đúng lớp lỗi mà **sự cẩn thận
> không chữa được**. *(Cùng kết luận với vế thi hành Luật M: khai ra một thiên lệch không vô hiệu hoá nó.)*
>
> **VẾ THI HÀNH — bốn câu, làm được ngay:**
> ① Khi viết *"có thể X đã cũ / chưa chắc đúng"*, hỏi **ngay**: ***X đang NẰM Ở ĐÂU ngoài câu này?***
> Nếu nó nằm trong một artefact thì **việc CHƯA XONG** — mới xong phần **nói**.
> ② 🔴 **Cách đóng rẻ nhất KHÔNG phải XÁC MINH, mà là NIÊM** — ghi *ngày đo + "chưa xác nhận lại"*
> ngay tại chỗ phát biểu ấy nằm. **Niêm làm được CẢ KHI KHÔNG ĐO LẠI ĐƯỢC.** *Không đo lại được
> **không phải** lý do để không đóng.*
> 🔴 **NIÊM Ở ĐẦU, GIỮ NGUYÊN THÂN** *(tester bổ sung 18/08 sau khi áp P ba lần trong vùng mình —
> cả ba lần thao tác đúng đều là NIÊM, không SỬA)*: **cám dỗ tự nhiên khi phát hiện số sai là ĐI SỬA
> SỐ — và sửa xong thì KHÔNG AI CÒN BIẾT cả đội đã tin gì, trong bao lâu.** Bản ghi lịch sử (bàn
> giao, biên bản quét, nhật ký) mang bằng chứng về **thứ ta TỪNG tin**; sửa thân là xoá đúng bằng
> chứng ấy. Cùng nếp `docs/DECISIONS.md` **chỉ ghi thêm** — nay khai rõ là một nguyên tắc chung, không
> phải một quy ước riêng của một file.
> ③ **Đừng thay một con số chết bằng một con số DỄ ĐỌC NHẦM.** Thay `446` (CI) bằng `568` (host) là
> đổi **trục** ⟹ phải khai *"host ≠ CI"*. **Thay số mà không khai đổi trục là tạo ra lỗi kế tiếp.**
> ④ **Áp cho MỌI vai** — security · PO · tech-lead · tester **đều nghi trong hội thoại nhiều hơn sửa
> trong file**.
>
> 🔴 **DẠNG THỨ HAI CỦA LUẬT P — *"ĐÚC LUẬT MÀ KHÔNG TỰ ÁP"*** *(tester tự bắt 18/08)*:
> không phải *"nghi mà không sửa"* mà **"biết luật, viết luật, rồi để artefact của chính mình thiếu
> đúng thứ luật ấy đòi"**. **Cùng một khoảng cách — giữa thứ ta BIẾT và thứ ta GHI VÀO VẬT.**
> **Bằng chứng [ĐO]:** tester đúc **Luật 18** (`tests/CHUAN-VIET-TEST.md:1596` — *"BĂM phải khai TÊN
> THUẬT TOÁN"*) từ ca hai băm khác nhau của **cùng một tệp**. Rồi
> `eval/NEN-TRUOC-BACKFILL-2026-08-18.json` của họ mang **bốn `van_tay_gop` KHÔNG kèm cách băm** —
> và PO-agent tính sai **HAI LẦN** trên chính con số ấy (sha256/theo-id → `8440c6c1…`; md5/sorted
> nhưng băm thẳng → `51b7b712…`; phép đúng `md5 TỪNG DÒNG → sắp xếp → md5 → 16` → `2805e52d1a4d0bed`).
> ⚠️ **Và ai chịu trách nhiệm là phần đáng ghi.** PO-agent tự nhận *"lần sau tôi phải đi tìm định
> nghĩa gốc trước khi tự gõ"* — **phản xạ ấy SAI CHỖ**, vì nó là một **lời nhắc**, và lời nhắc hỏng
> đúng lúc cần nhất.
> 🔴 **NGUYÊN TẮC:** *một con số băm không kèm cách băm thì gánh nặng thuộc **NGƯỜI VIẾT TỆP**, không
> thuộc **NGƯỜI ĐỌC**.* Người đọc gõ một phép băm **vì tệp không cho họ phép nào** — đó là khuyết tật
> của tệp, không phải của người đọc.
> ⭐ Đây **cùng một nguyên tắc** đã áp ở hai chỗ khác trong ngày, chỉ khác tầng: **chốt chặn cắm ở
> tầng transport thay vì trong `tests/`** · **hoãn `add_chunks()` thay vì thêm một bộ lọc phải nhớ
> gọi**. ⟹ ***Đặt cơ chế ở nơi không thể đi vòng, thay vì ở nơi phải nhớ.***
> *(Ghi NGUYÊN TẮC, không ghi tên người — một luật mang tên người sẽ được đọc như một ý kiến.)*
> ✅ **Vá bằng CƠ CHẾ, không bằng lời nhắc** ([ĐO] đã land `6f398f2`): tệp nền nay mang
> `__cach_bam__` · `__cach_bam_dien_giai__` · `__do__` (kèm *"KHÔNG dùng BUILD_COMMIT làm mốc"*), và
> **cổng TỪ CHỐI CHẠY** nếu thiếu — đột biến xác nhận: gỡ `__cach_bam__` ⟹ *"KHÔNG ĐO ĐƯỢC"*.
> ⭐ **Hai thứ cơ chế ấy mua được mà một dòng chú thích trong code KHÔNG mua được:** người sau **không
> phải đọc mã test mới dùng được tệp**, và **ai chép tệp đi nơi khác thì mang theo định nghĩa**.

> 🔴 **VẾ THI HÀNH THỨ BA — *"MỘT CON SỐ ĐÃ RỜI KHỎI TAY BẠN LÀ ARTEFACT CỦA NGƯỜI NHẬN"*:**
> **Khi bạn TỰ LÀM CŨ một con số đã đưa cho người khác, việc NIÊM nó là của BẠN — không phải việc
> người ta đi truy.**
> **Bằng chứng [ĐO] 18/08:** tester đưa PO-agent mốc chờ đợi *"`0 failed` / `2 failed`"* **trước** lần
> dựng, rồi **tự làm nó lệch** khi gỡ 6 nhãn `security_finding` (`ba0b812`), và **không cập nhật**.
> PO-agent phải đi truy một chênh lệch (`6 passed → 0 passed`) mà **một dòng đã đóng được**.
> ⚠️ Khác hai vế trước ở chỗ: đây **không phải artefact trong repo** — nó là **một con số trong đầu
> người khác**, và chính vì thế **không ai `grep` ra được** để tự phát hiện.
> ⭐ *Và nó lộ ra CHỈ VÌ đọc bằng **SỐ CA CHẠY**: nhìn màu thì `1 failed` giống hệt nhau ở cả hai lượt.*

> 📌 **ĐỀ XUẤT cơ chế (tester nêu — CHƯA phải một phần của luật, chờ PO):** mỗi bảng số trong
> `tests/*.md` và `docs/*.md` mang một dòng **`đo: <ngày> · <ngăn xếp> · <băm HEAD>`**; thiếu dòng đó
> ⟹ **con số không được trích**. Biến "niêm" từ một quyết định phải nhớ ra thành **điền một chỗ trống
> sẵn có** — đúng tinh thần *cơ chế thắng lời hứa*.

**Luật 1** — assertion **không được trùng trạng thái mặc định** (test xanh giả).
**Luật 12b** — mọi phát biểu xếp hạng phải **khai TRỤC**: *"xếp trên trục X, trục Y chưa xét"*.
**Luật 17** — **trước** khi chạy một phép thử, hỏi: *nếu giả thuyết SAI thì phép thử này ra gì, và
có phân biệt được không?*

**Luật I · J · K** — *(PO-agent CẤP PHÁT SỐ HIỆU 18/08; nội dung đúc 17/08, giữ nguyên):*
**Luật Q** *(PO-agent đúc 18/08 từ sai lầm của chính mình — ô **O** bỏ trống có chủ đích, tránh đọc
nhầm thành số 0)* — **NGỮ CẢNH CỦA BẠN LÀ MỘT ẢNH CHỤP; CÂY LÀM VIỆC LÀ MỘT THỨ SỐNG. Khi hai cái
lệch nhau thì KHÔNG CÓ TRIỆU CHỨNG — vì mỗi cái đều tự nhất quán.**
> **[ĐO] 18/08 (§5.P):** cây bị `checkout` sang nhánh khung mẫu **giữa lượt**. `git status` báo
> **SẠCH**. Mọi đường dẫn + số dòng trong ngữ cảnh vẫn "đúng" — chỉ là chúng trỏ tới **một repo khác**.
> **Ba điều khoản thi hành:**
> ① **`git status` sạch KHÔNG chứng minh cây là cây bạn nghĩ.** Sạch đo *trong* một ảnh chụp; câu
>   bạn cần trả lời nằm *giữa* các ảnh chụp. Hai câu hỏi khác nhau, một lệnh chỉ trả lời câu thứ nhất.
> ② **Phát biểu về nội dung file phải mang DANH TÍNH CÂY**, không chỉ `đường/dẫn:dòng` — tối thiểu
>   `nhánh @ commit`. Đây là **Luật F** (mẫu số cùng dòng) áp cho trích dẫn mã nguồn: một số dòng
>   không kèm danh tính cây là một con số không có mẫu số.
> ③ 🔴 **Khi một file "biến mất" hoặc mã "sai lạ lùng": hỏi MÌNH ĐANG ĐỨNG Ở ĐÂU trước khi đi tìm
>   VẬT.** `git rev-parse --abbrev-ref HEAD && git log -1` **rẻ hơn mọi cuộc truy tìm**, và 18/08
>   PO-agent đã làm ngược — lục sang một repo khác trước, tốn lượt, đưa PO một khúc lạc đề.
> **Khác Luật G ở chỗ nào:** Luật G nói *cơ chế làm đúng việc của NÓ ≠ việc ta tưởng*. Luật Q nói một
> câu **nằm trước cả G** — *vật bạn đang soi có phải vật bạn nghĩ không*. G giả định đã đúng vật.

**Luật I** — **Bước ĐO không được ghi vào container đang chạy.** Buộc phải ghi ⟹ **khai trước + hoàn nguyên
  ngay**, và trạng thái *"đã ghi"* phải **hiện ra**, không nằm trong trí nhớ.
  **Vế thi hành:** sau **MỖI** phiên đo, chạy `docker diff` **trước khi báo cáo bất cứ số nào**.
**Luật J** — **Vá đúng một lỗi có thể làm IM một cổng đang hỏng vì lý do khác** — bản vá đúng, tác dụng phụ là
  **xoá mất triệu chứng duy nhất** tố cáo cổng ấy rỗng. **Vế thi hành:** khi bản vá làm một cổng
  **ĐỎ → XANH**, phải **đọc xem cổng đó khẳng định CÁI GÌ**, không chỉ ghi nhận nó đã xanh.
**Luật K** — **Nhiều ước lượng độc lập cùng lệch MỘT hướng = thiên lệch CHUNG, đi tìm bộ lọc chung.**
  *(Bằng chứng: `45K` → `0–21K` → thực tế `149–215K`. Bản "đính chính" đi XA HƠN khỏi sự thật.)*

---

## 8. 🔴 BÀI HỌC LỚN NHẤT 17/08 — đọc mục này rồi hãy tin bất kỳ con số nào

**BẢY lỗi, ba người, MỘT lớp: suy từ một tập ĐÃ BỊ LỌC mà không khai bộ lọc.**

| bộ lọc | ca |
|---|---|
| **vắng mặt** | *"không thấy `ToolResult` ⟹ không tool call"* — thật ra **8 tool call**, cổng OTP từ chối **TRƯỚC** `record_tool_result` |
| **sống sót** | *"0/70 lời gọi chạm trần 20s"* — `giay` **chỉ tồn tại cho lời gọi ĐÃ TRẢ VỀ** ⟹ hằng đúng |
| **sống sót** | *"trần đệ quy 20 đặt xa gấp 4 hành vi thật (max 5)"* — max 5 là của lượt **THÀNH CÔNG**; lượt **HỎNG** có **8** |
| **tự cầm kéo** | tính xác suất trên một cấu hình **chưa từng quan sát** (lấy trung bình rồi giả định cả 3 giá trị bằng nó) |
| **tự cầm kéo** | chọn 3 điểm **vì chúng gần nhau** rồi đo độ phân tán của chính tập vừa chọn |
| **tự cầm kéo** | trích `contracts/agent-tools.yaml:143-146` rồi **dừng đọc** — câu trả lời ở **dòng 150** |
| **dân số pha tạp** | `4%` (13/370) vs `1/13`; `30%` trích **không kèm kịch bản** |

> **Cả bảy lần bộ lọc đều VÔ HÌNH** — không ai cố tình lọc, **tập tự đến đã lọc rồi**.
> **Dấu hiệu DUY NHẤT: dữ liệu trông QUÁ GỌN.**
>
> ⟹ **NẾP KIỂM:** khi một tập số trông sạch bất thường — không ngoại lệ, không đuôi, một cực đại
> tròn trịa — hỏi ***"cái gì đã KHÔNG sinh ra dòng nào ở đây?"*** **TRƯỚC** khi hỏi *"số này nói
> gì"*.

**Và nó nằm ngay trong dụng cụ đo của chính ta:** sổ usage ghi `so_luot_goi_model = 0` cho lượt
hỏng ⟹ 22 dòng `0` lẫn *"đường nhẹ, đúng 0"* với *"lượt hỏng, không biết"*. **Sổ dựng ra để đếm
lời gọi, và nó lọc mất đúng loại lượt ta đi tìm — rồi báo bằng một giá trị TRÔNG HỢP LỆ.**

**Quy trình đã chứng minh là chữa được:** **công bố DỰ BÁO vào git TRƯỚC khi chạm vật.** Đã chạy 2
lần, trúng 6/6 và 2/2, một lần **trúng tới từng chữ số**. Kèm bảng *"nếu khác thì nghi gì"*.
Và **khai trước rằng một kết quả THUẬN LỢI sẽ không được tính là xác nhận** — đã có ca thật: cổng
xanh nhưng ghi **"chưa giải thích"** thay vì "đã vá", và chính vì thế mà tester đi tìm bằng chứng
và **phát hiện ra cổng ấy rỗng**.

---

## 9. CẠM BẪY — người mới sẽ đâm vào đúng những chỗ này

**"KHAI ≠ CHẠY" — SÁU cơ chế đã gặp thật:**
`docker cp` vào container đang chạy · ảnh dựng từ **cây làm việc** chứ không phải HEAD · **đổi
phiên bản thư viện phụ thuộc** (`langchain-core` 1.5.3→1.5.4 đổi mô tả tool ~12%) · prompt chứa
`current_time` · harness **soạn lại** kích thích · `>/dev/null` nuốt một lệnh **chưa bao giờ chạy**.

- **`restart` ≠ `recreate` ≠ `rebuild`.** `Config.Env` **ghim lúc TẠO container**. `docker cp` **sống
  qua restart**.
- **Dấu thời gian COMMIT ≠ dấu thời gian TRIỂN KHAI**, và nó **lệch về hướng dễ chịu**: nếp
  *chạy → xác minh → mới commit* khiến mọi mỏ neo `git log` tính cửa sổ **RỘNG HƠN** sự thật.
  *(Đã đo: trường xuất hiện trong bản ghi **trước commit 65 giây**.)*
- **`tests/` NẰM TRONG ẢNH** ⟹ **màu cổng đổi được mà KHÔNG một dòng sản phẩm nào đổi.** Đọc kết
  quả bằng **SỐ CA CHẠY**, không chỉ bằng màu — `skip` và `pass` cùng màu trên bảng tổng.
- **Nguồn dữ liệu SAI DÂN SỐ:** `messages` (230 tin, 85 phiên) là **script sinh**, không phải người
  (p10 = p50 = 3s ⟹ 19,8 lượt/ph/người, và script **không bao giờ gõ "alo"**). **Đừng dùng nó làm
  mẫu lưu lượng thật.** `bo_ca_luot_don.json` là **bộ dò biên**, cố ý làm giàu ca hiểm — **không
  phải mẫu đại diện**.
- **Sổ `usage.jsonl` SỐNG QUA `recreate`** ⟹ tích luỹ mọi đợt. Script tổng hợp **phải lọc theo cửa
  sổ thời gian**, nếu không sẽ đếm dòng lịch sử vào kết quả hôm nay.
- **BỐN RỔ bắt buộc** khi tổng hợp: `nhe` → lượt đơn thật · `day_du`+fallback=None → chạy xong ·
  `day_du`+fallback CÓ → **HỎNG** · **KHÔNG có khoá `duong` → 🔴 ĐIỀU TRA, không gộp vào đâu**.
  *(Bẫy cụ thể: viết `duong != 'day_du'` thì lượt 422/500 thành "lượt đơn" ⟹ **thổi tỉ lệ tiết
  kiệm đúng hướng ta muốn nghe** — confound hướng-có-lợi.)*
- **BA RỔ cho token:** `đo được` · `không đọc được` · `đúng 0`. **KHÔNG `sum()` với `or 0`** —
  `or 0` biến *"không biết"* thành *"không tốn"*. Và **ba rổ phải có BA MẪU SỐ RIÊNG**.
- **Phiên chưa xác thực OTP** làm lượt rơi vào livelock. Dùng `scripts/phien_do.py` để có phiên đã
  xác thực — thiếu nó thì mất một giờ chẩn nhầm.

**Đọc trước, dọn sau. LUÔN.** *(Đã có ca: `--force-recreate` để dọn đã **xoá hiện trường** trước
khi chẩn, phải tiêm lại từ đầu. Ngoại lệ này đã được viết ra sáng cùng ngày và **vẫn bị bỏ qua**,
vì phản xạ dọn nhanh hơn phản xạ đọc.)*

**Nháp thiết kế làm NGOÀI repo.** Mọi script đo phải **IN BĂM** của vật nó đo.

---

## 10. QUY TRÌNH ĐỔI CONTRACT — không có đường tắt

```
1. DỪNG. KHÔNG sửa code trước.
2. Sửa file trong contracts/
3. Ghi ADR mới vào docs/DECISIONS.md   (DECISIONS.md CHỈ GHI THÊM, không sửa thân ADR cũ)
4. Hỏi PO thật duyệt. CHỜ trả lời.
5. python scripts/check_contracts.py --update
6. Cập nhật CONTRACT_VERSION ở đầu tests/test_invariants.py
7. commit — 🔴 KÈM FILE BASELINE mà --update sinh ra   ← §3 hiến pháp KHÔNG viết bước này
8. BÂY GIỜ mới code
```
🔴 **Thiếu bước 7 ⟹ local xanh, CI đỏ.** Đội đã vấp.

## 11. PHÂN VÙNG QUYỀN GHI (nhắc lại — §4 hiến pháp)

`po` → `docs/`, `*.md` gốc · `tech-lead` → `src/`, `frontend/src/`, `migrations/`,
**`docker-compose*.yml`** (ADR-035), **`.github/workflows/**`** (ADR-037), `contracts/`
(sau khi PO duyệt) · `tester` → `tests/`, `frontend/e2e/`, `eval/` — **KHÔNG đọc `src/`** ·
`security` → `docs/security/` · `ux-ui` → `frontend/src/` · `critic` → không ghi gì.

> 🔴 **HAI LẦN TRONG MỘT NGÀY (18/08) bảng này thiếu một dòng, và cả hai lần chỉ lộ ra lúc có việc
> cần sửa file ấy:** `docker-compose*.yml` (ADR-035) rồi `.github/workflows/` (ADR-037) — lần thứ hai
> còn **mâu thuẫn với chính định nghĩa vai**: mô tả agent `tech-lead` ghi *"dựng CI"* mà bảng không
> cho họ chạm file CI.
> ⟹ **Bảng §4 được viết theo thứ đội ĐÃ ĐỘNG TỚI, không theo thứ TỒN TẠI trong repo.** Việc còn nợ:
> rà một lượt toàn bộ thư mục gốc, cấp chủ cho mọi thứ **trước** khi có người cần sửa nó.
> **Và ADR-035 đã bác sẵn đường tắt:** cấp quyền một lần cho đúng một ca **không để lại dấu vết đọc
> được** — lần sau người khác lại vấp đúng chỗ ấy. Sửa bảng thì hết vấp.

> **Vì sao tester không đọc `src/`:** test sẽ **phản chiếu** logic đang có, kể cả logic sai. Kết quả
> là một suite xanh mướt chứng minh rằng bug hoạt động đúng như bug.
>
> **Và quy tắc PO-agent tự đặt sau khi vi phạm:** khi chuyển tin giữa các vai bị cách ly, **chỉ
> chuyển KẾT LUẬN và LÝ LẼ, không bao giờ chuyển NỘI DUNG CORPUS.**

## 12. TÀI LIỆU LIÊN QUAN

```
docs/khoi-dong-lai/                           ← 🔴 BỘ PROMPT BẬT LẠI 4 VAI (README + 01..04)
scripts/BAN-GIAO-coder-2026-08-17.md          ← bàn giao tech-lead (3734c2b)
tests/BAN-GIAO-TESTER-17-08.md                ← bàn giao tester    (27b6ea3)
eval/QUET-TEN-HUA-KHAC-ASSERTION.md           ← 6 ca, 5/6 trên đường HITL (4ac2162)
docs/nhat-ky/2026-08-17-nhat-ky-day-du.md    ← toàn bộ lập luận + số đo 17/08 (3.001 dòng)
docs/DECISIONS.md                             ← ADR-001..037 (031 ĐÃ GỠ CHẶN bởi ADR-034)
docs/security/                                ← 20+ hồ sơ; 2 file quan trọng nhất:
   2026-08-17-kiem-ke-du-lieu-roi-bien-gioi-cho-ho-so-D25.md   (vật liệu Đ.25)
   2026-08-17-ho-so-KHAI-khac-CHAY-nam-co-che.md               (Luật H + 5 cơ chế)
docs/2026-08-17-ra-soat-khai-bao-vs-ep-buoc.md ← INV-16/INV-17 KHÔNG có test (INV-17 chỉ là
                                                  một chú thích ở dòng 51 test_invariants.py)
docs/giao-viec/                               ← brief giao việc + hồ sơ chuyên gia token
contracts/                                    ← NGUỒN SỰ THẬT về cấu trúc
```

**Pháp lý hiện hành:** NĐ 52/2024 · TT 40/2024 (**KHÔNG** dùng TT 39/2014 — hết hiệu lực) ·
NĐ 13/2023 (PDPA) · QĐ 2345/QĐ-NHNN (10tr/lần, 20tr/ngày — là ngưỡng **xác thực sinh trắc**,
**KHÔNG** phải ngưỡng gian lận; phải nói rõ điều này khi trao đổi với chuyên gia).
