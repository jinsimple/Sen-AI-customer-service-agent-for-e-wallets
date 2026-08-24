# Trạng thái dự án FIN-05

> **Viết cho người đọc NGUỘI** — bạn không có gì trong đầu, chỉ có repo này.
> Đọc `CLAUDE.md` (hiến pháp) trước, rồi file này, rồi 5 ADR gần nhất trong `docs/DECISIONS.md`.
>
> Cập nhật: **18/08/2026**, ngay trước khi PO thật tắt toàn đội để khởi động lại sạch.
>
> 🔴 **NIÊM 24/08 — FILE NÀY CŨ 6 NGÀY.** Đội chạy rất nhanh trong 19–24/08 (đợt 1A/1B, ADR-043→048).
> Mục nào ghi *"chờ PO"* mà không có dấu 24/08 thì **phải đối chiếu `docs/DECISIONS.md` trước khi tin** —
> PO đã gỡ nhiều nút ngày 24/08. Dọn trọn file này là việc của `/wrapup` phiên hiện tại.
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
| **Chạy test** | 🔴 **`docker exec … pytest` NAY KHÔNG CHẠY ĐƯỢC CẢ SUITE** — `.dockerignore:11` loại `eval/`, 3 tệp test đọc `eval/` ⟹ `Interrupted`, **0 ca chạy, hiện ra như "0 failed"**. **Chạy cổng từ HOST.** `docker exec` chỉ còn đúng cho tập con không đụng `eval/`. `P-121-new/.venv` **CẤM dùng để đo kích thích gửi model** (lệch `langchain-core`) |
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
- 🟢 **NIÊM 20/08:** dòng "② THẬT SỰ MẤT" ở trên và cảnh báo `pytest tests/` đẩy lượt nhúng ra
  Internet đều đo **18/08**. §5.F (chốt chặn tầng transport) đã ĐÓNG 20/08 — xem `docs/STATE.md §5.F`
  cho trạng thái hiện hành trước khi dựa vào con số ở đây.

🔴 **Hạn mức: A3 của PO thật còn hiệu lực — "chưa nạp gì cho tới khi tối ưu xong chi tiêu token."**
~~Còn **~32K** token miễn phí trên `qwen3.7-max`~~ **[NIÊM 19/08 — số này đã chết, đừng lập kế hoạch
trên nó]**: 32K là phần dư của model ĐÃ BỎ, tính từ 1/3 ngăn xếp. [ĐO] 19/08 (Lead đo, PO-agent kiểm
độc lập, khớp từng chữ số, cộng đủ BA sổ `usage.jsonl`): `qwen3.7-max` **1.027.494/1M — VƯỢT** · họ
`qwen3.7-plus` (bí danh 44.362 + bản ghim ngày 198.657) = **243.019 ⟹ còn ~757K trên model ĐANG CHẠY,
theo SỔ NỘI BỘ**. Caveat giữ nguyên hiệu lực: lượt hỏng ghi 0 (tiêu thật cao hơn) · "1M/model" chưa đối
chiếu dashboard (A4) · bí danh/bản ghim chung xô là GIẢ ĐỊNH thận trọng. `qwen3.8-max` đã cạn.

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
- **Benchmark 74,57/85 = 87,7%** — luôn kèm 3 caveat (xem nhật ký). 🔴 **NIÊM 19/08** (PO thật quyết,
  `6d05433`): số đo **16/08, TRƯỚC khi đổi model và trước 4 vùng thay đổi** (RAG 5 commit · O4 2 ·
  PII 4 · prompt 1) — **mốc lịch sử, KHÔNG phải điểm của bản đang chạy**. Chạy lại bị huỷ (bất khả
  thi, ước 4.611.600 token vs hạn ngạch 2.733.325); thay bằng chuỗi đo 19/08 làm bằng chứng PLO 7.
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


### ✅ E/M/O. Backfill `complaints.description_raw` — ĐÃ ĐÓNG 20/08, chuyển
`docs/nhat-ky/2026-08-20-state-dep-E-M-O-backfill-pii.md`

**Trạng thái cuối:** `fin05` 0/786 sạch (backfill 738→0, nghiệm thu độc lập ĐẠT) · `fin05do` 0/607
sạch (chưa từng bẩn) · **`fin05ttl` 738/742 vẫn PLAINTEXT, CÓ CHỦ ĐÍCH** — ngăn dùng-một-lần, dữ
liệu tổng hợp (`gen_dataset.py --seed 20260802`), không có khách thật ⟹ không phát sinh nghĩa vụ
PDPA, cố ý không mã hoá. Rủi ro còn sống: đo nhầm ngăn `fin05ttl` sẽ trông như "backfill hỏng" — đọc
kèm nhãn ngăn xếp trước khi trích số mã hoá. **Đừng nạp lại `fin05ttl`** — nó là ca đối chứng duy
nhất chứng minh cổng plaintext còn biết kêu khi bất thường (Luật A, nửa "KÊU lúc bất thường").


### ✅ F. Chốt chặn chi phí sai tầng — ĐÃ ĐÓNG, chuyển
`docs/nhat-ky/2026-08-20-state-dep-F-G-IJ.md`

[ĐO 20/08] Đã vá đúng cả hai việc đề xuất: `src/cong_ra_ngoai.py:22` giải thích lý do cắm ở tầng
transport (không phải `_khoa_cho_nha_cung_cap()`) · `src/cong_ra_ngoai.py:355` có `so_luot_da_phat()`.

### ✅ G. Miễn trừ OTP `search_policy` — ĐÃ ĐÓNG một phần, chuyển
`docs/nhat-ky/2026-08-20-state-dep-F-G-IJ.md`

[ĐO 20/08] Docstring đã khai (`customer_tools.py:968`, *"MIỄN TRỪ OTP CHO `search_policy` — CÓ CHỦ
ĐÍCH"*). **Còn treo, KHÔNG đủ để giữ mục này sống:** đề xuất thêm trường `contracts/agent-tools.yaml`
khai "tool có đường ra ngoài hạ tầng không" — mở rộng contract, không phải nợ, đụng §10 nếu làm.


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


### ✅ I+J. Kho checkpoint 0% mã hoá — ĐÃ THÀNH ADR-045, chuyển
`docs/nhat-ky/2026-08-20-state-dep-F-G-IJ.md`

✅ **PO THẬT DUYỆT 24/08** — bốn tham số vận hành đã chốt, xem **ADR-045b**: giữ **90 ngày** ·
VPS **Việt Nam** · **20 vé/ca** (trung bình ngành quốc tế, NIÊM: không phải số đo đội VN nào) ·
kiến trúc máy để DevOps tự xác định lúc dựng (không chặn ai). **Mục này KHÔNG còn chặn.**

[ĐO 20/08] ADR-045 (`docs/DECISIONS.md`, commit `b37218f`) — bối cảnh gốc. Bốn ràng buộc
I+J từng nêu (serde không đổi cột · đừng che `HumanMessage` · giải quyết retention cùng lúc · nghiệm
thu dò byte) vào ADR nguyên vẹn. Review tìm thêm bảng `checkpoint_writes` (7.015 dòng, chưa ai từng
đếm) ⟹ **tổng 13.857 blob, 0% mã hoá — gấp đôi con số I+J giữ.** Đọc số mới trong ADR-045, không
dùng số cũ trong file lưu trữ.


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

🔴 **[ĐO 20/08, PO-agent] 1/3 XONG — KHÔNG gộp vào §5.F dù cùng chủ đề, đó là hai VIỆC khác nhau
(F = cắm chốt chặn đúng tầng, K giai đoạn 2 = làm bộ đếm đọc được từ ngoài):**
```
✅ src/cong_ra_ngoai.py:355  so_luot_da_phat()  — đường đọc bộ đếm ngoài tiến trình XONG
⬜ src/cong_ra_ngoai.py:181  "…KHÔNG NƠI NÀO ĐỌC nó" — đổ da_phat vào usage.jsonl CHƯA xong
⬜ đảo mặc định cờ compose thành TỪ CHỐI + khai =1 — chưa đo, chưa kết luận
```


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


### 🔴🔴🔴 N. ADR-026 "Đang hiệu lực" — NHƯNG CƠ CHẾ TRUNG TÂM CỦA NÓ KHÔNG TỒN TẠI. Sự cố nó đóng VẪN ĐANG MỞ

🔒 **[ĐO 20/08, PO-agent xác nhận claim còn đúng — `grep 'da_duyet' src/ migrations/ contracts/` = 0
hit] NGĂN RIÊNG, CẤM DỌN, CẤM HỎI LẠI PO THẬT.** Mục này khác mọi mục khác trong §5: nó KHÔNG chờ
VIỆC (chưa ai làm) — nó chờ NGƯỜI (PO thật đã chọn ⏸ **HOÃN** ở A0 vòng 2: *"PO cần nghiên cứu kỹ
hơn"*, một quyết định ĐÃ CHỐT, có khai). Hỏi lại PO thật câu này là vi phạm §5 hiến pháp (*"quyết
định đã chốt thì không bao giờ hỏi lại"*). Lỗ kỹ thuật (route/`CheckConstraint` thiếu `da_duyet`)
vẫn nguyên trạng — chỉ trình DỮ KIỆN mới nếu có, không trình lại câu hỏi.

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


### 🟢 C. ĐÍNH CHÍNH 18/08 — ĐÃ ĐÓNG, chuyển `docs/nhat-ky/2026-08-20-state-dep-dinh-chinh-18-08.md`
(hai đính chính tự khép: C1 khách không đọc lý do từ chối TPM sai — căn cứ chết nằm trong chú
thích, không phải lỗi đối ngoại · C2 `test_f31_f32` đã có cổng chi phí từ `07ee30e`, phát biểu
"chưa vá" sai từ lúc viết).


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

### 🔴🔴 Q. BA BRIEF NẰM KHÔNG HƠN BỐN TIẾNG — kênh giao việc KHÔNG CÓ CHUÔNG

*(PO thật phát hiện: **"tôi có thấy đội chạy đâu bạn?"**. PO-agent chẩn đoán sai lần đầu, **security
bác**, tester đặt tên đúng cho nó.)*

```
[ĐO] ListAgents → 3 phiên đội SỐNG 11 GIỜ, gọi thẳng được: p-226-ab · p-226-cf · p-226-b0
[ĐO] docs/giao-viec/ ngày 18/08:
     14:39  tech-lead-adr033-adr034.md        → chưa ai mở
     14:40  tester-doi-chung-quan-the-vut-di  → chưa ai mở
     19:00  tech-lead-ci-self-hosted.md       → chưa ai mở
[ĐO] cả ba phiên tự khai: "chưa nhận brief nào từ docs/giao-viec/"
```
**Ba brief · hơn 4 tiếng · thông lượng 0.** Và phần nặng nhất: **PO-agent viết cái thứ BA mà không hề
thấy cái thứ NHẤT chưa chạy** — hàng đợi dài ra trong khi tôi báo cáo tiến độ như thể mọi thứ đang trôi.

🔴 **CHẨN ĐOÁN ĐẦU CỦA PO-AGENT SAI, VÀ SAI VỀ PHÍA "TỰ TRÁCH QUÁ TAY":**
tôi phát biểu *"tôi viết file rồi chờ dán tay, trong khi gọi thẳng được"* — đọc như thể **kênh file là
chỗ kém hiệu quả**. **Security bác, và đúng:** kênh file **là THIẾT KẾ của PO thật** — mỗi vai một tab,
**log riêng, tự quản lý được**, thay vì một phiên sinh ra phiên khác.
> ⚠️ **Suýt nữa tôi "tối ưu" mất một ràng buộc có chủ đích** — ca thứ BA trong ngày cùng hình dạng
> (`search_policy` miễn OTP · `complaint_intake` không cache · và ca này). Security nêu đúng phản xạ:
> **hỏi PO một câu trước khi đổi thì rẻ; đổi rồi phát hiện là quyết định của sếp thì đắt.**

⭐ **VÀ VẾ SECURITY THÊM — PO-agent chưa hề nghĩ tới:**
```
brief trong docs/giao-viec/   → CÓ VẾT TRONG GIT: ai giao gì, lúc nào, nội dung ra sao
brief qua SendMessage         → KHÔNG vết nào trong repo
```
Với dự án lấy `contracts/` làm nguồn sự thật và bắt mọi quyết định phải có ADR, **một kênh giao việc
không vết là một khoảng trống truy vết.** ⟹ **Chốt: GIỮ FILE LÀM BẢN GHI, DÙNG TIN NHẮN LÀM CÁI CHUÔNG.**
Tin nhắn **trỏ tới** file, không thay file. Được cả hai.

🔴 **KHOẢNG TRỐNG THẬT NẰM CHỖ KHÁC CHỖ TÔI TƯỞNG — không phải "sai kênh", mà là:**
**thiết kế giả định PO biết có brief đang chờ, và KHÔNG CÓ GÌ báo cho PO.**

**Tester đặt tên đúng — Luật P ở tầng thứ TƯ, kênh giao việc:** việc đã **RỜI KHỎI TAY người viết**
(vào file) nhưng **CHƯA TỚI TAY người nhận**, và **không ai `grep` ra được khoảng trống đó vì file
TỒN TẠI** — trông y hệt một việc đã giao. `ls` không phân biệt được; `git log` càng không, nó chỉ
chứng minh ai đã **VIẾT**, không chứng minh ai đã **ĐỌC**.
⟹ **Đây là dạng khó bịt nhất của Luật P**: ba dạng trước còn để lại vật để đối chiếu; dạng này **vật
trông hoàn hảo**, chỉ thiếu một sự kiện **không được ghi ở đâu cả**.

**KHÔNG kết luận:** ❌ kênh file sai — nó đúng, và có lý do bảo mật để giữ. ❌ ai lười — cả ba phiên
đều rảnh và sẵn sàng suốt 11 tiếng, **không ai biết có việc đang chờ mình**.

### 🔴🔴🔴 R. BỐN THỨ ĐỘI ĐANG DỰA VÀO MÀ KHÔNG AI KHAI — và một trong số đó là MỘT SỰ CỐ

*(Mở bởi PO-agent từ ca `ubuntu-latest`; **security** dựng thành danh sách có tiêu chí (§16);
**tech-lead** thêm ca nặng nhất khi tự phanh giữa lúc dựng. Ba nguồn độc lập, một hình dạng.)*

| # | thứ đang được dựa vào | khai ở đâu | mất đi thì cái gì kêu |
|---|---|---|---|
| 1 | **`ubuntu-latest` bị huỷ sau mỗi job** — gánh **BỐN** việc: dọn `.env` · dọn container · dọn volume · chống đụng cổng | ❌ không đâu | **không gì** |
| 2 | 🔴 **billing hỏng đang CHẶN 3 job nightly** | ❌ không đâu | **không gì** |
| 3 | **`access.log` sống sót `recreate`** — cơ chế bù DUY NHẤT của Pha 1 ADR-025, thay cho `assigned_to` chưa tồn tại | ❌ chỉ **1 dòng** `docker-compose.yml:127,229`; `tests/` · `contracts/` · ADR → **0 hit** | **không gì** — triệu chứng là *một tệp ngắn hơn* |
| 4 | **"không có dữ liệu khách THẬT trong CSDL"** — nền của mọi kết luận PII | ❌ **một TƯ THẾ**, không cổng nhập/cờ/CHECK nào | **không gì** — và **đã rò 1 lần**: 4 chuỗi dạng SĐT ngoài bộ seed, phát hiện bởi **một phép đo tình cờ** |

🔴 **CA SỐ 2 LÀ CA NẶNG NHẤT, VÀ NÓ SUÝT ĐƯỢC DÙNG LÀM CƠ CHẾ AN TOÀN.**
tech-lead định lấy lượt đo thứ hai bằng `workflow_dispatch` — rẻ nhất, không cần commit. Rồi dừng:
**dispatch thoả `if:` của ba job nightly**, trong đó `livechat-e2e-nightly` **ghi `OPENAI_API_KEY`
THẬT ra `.env`**, hai job kia gọi model tính tiền. Ba job ấy hiện không chạy được **NHỜ BILLING HỎNG**.
> ⟹ **Dựa vào một SỰ CỐ HẠ TẦNG làm cơ chế an toàn.** Nó phản lại đúng vào **ngày billing được sửa** —
> và đó là ngày ta đang chủ động đi tới. **Không ai sẽ nhớ rằng có thứ đang dựa vào nó.**
> Họ lấy lượt B bằng **một lần đẩy thường** (push không thoả `if:` của ba job đó): đắt hơn một commit,
> **không mượn cái lưới nào**.

⚠️ **HỆ QUẢ VẬN HÀNH — GHIM CHO NGÀY BILLING ĐƯỢC SỬA:** job `self-hosted` **không phụ thuộc billing**.
⟹ Giây phút `livechat-e2e-nightly` được đổi sang `self-hosted`, nó **chạy được ngay**, bất kể billing.
**Ràng buộc thứ tự giữ nguyên: KHÔNG đổi `runs-on` của hai job docker cho tới khi bước dọn được CHỨNG
MINH LÀ CHẠY** — và [ĐO] tech-lead tự khai: **bước dọn hiện là mã CHƯA TỪNG THỰC THI**.

⭐ **VÀ MỘT CÁI BẪY ĐỌC-NHẦM ai cũng sẽ mắc, tech-lead phát biểu:**
> ***`always()` chỉ có nghĩa "luôn chạy khi job ĐÃ ĐƯỢC CẤP MÁY". Job chưa từng khởi động thì không
> có gì luôn cả.*** Họ **dự báo** bước dọn sẽ chạy, dự báo **TRƯỢT**, và **báo trượt** thay vì lặng lẽ
> bỏ qua — job còn ở `ubuntu-latest` nên không job nào khởi động, kể cả `if: always()`.

✅ **GHI CẢ Ô SẠCH để danh sách không thiên lệch** *(security §16.4)*: ứng viên mạnh nhất họ nghĩ ra là
`thread_id` — [ĐO] `main.py:645` `thread_id=f"{user_id}:{iat}"`, **server tự dựng từ claim JWT, client
không chạm được**, và **có khai ở BA chỗ** (`main.py:315·488·498`) giải thích vì sao `iat` phải giữ
nguyên qua refresh **chính vì** `thread_id` phụ thuộc nó. **Không phải bảo đảm không khai — là quyết
định có ý thức, ghi đúng ba chỗ người ta sẽ phá nó.** Đó là hình dạng ĐÚNG của cả bốn ca trên.

**KHÔNG kết luận:** ❌ bốn ca này là lỗ hổng đang bị khai thác — **không ca nào có sự cố**. Chúng là
**bảo đảm không khai**, và giá trị của việc liệt kê nằm ở chỗ ta đang **chủ động thay đổi môi trường**
(đổi runner, sửa billing) — đúng lúc rẻ nhất để phát hiện mình đang đứng trên cái gì.

### ⓵ Trần thật là TPM, và ta ĐÃ VƯỢT ở cấu hình buổi 150 người

```
trần TPM 1.000.000 / 14.198 token/lượt =  70,4 lượt/phút   ← TRẦN THẬT
trần RPM     10.000 /   2,39 gọi/lượt  = 4.184 lượt/phút  ← không bao giờ chạm trước
                (⛔ NIÊM 20/08: dòng cũ ghi **600**, SAI, lệch ~17 lần. [ĐO BA 20/08,
                 `qwencloud.com/models/<model>` mục Rate Limits] deepseek-v4-pro-0813
                 RPM 10.000 · deepseek-v4-flash-0731 RPM 15.000. **Nguồn của số 600:
                 KHÔNG TRUY ĐƯỢC** — không tài liệu nào trong repo ghi nó đến từ đâu.
                 KẾT LUẬN của mục này KHÔNG đổi: TPM vẫn chặn trước, RPM cao hơn chỉ
                 làm kết luận ấy đúng mạnh hơn.)

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

> ⛔ **NIÊM 20/08 — cả BA mẫu số dùng để cỡ ra số 20 đều đã chết.**
> Số 20 cỡ từ *"trần OpenAI 200.000 TPM ⟹ ~13 lượt/phút"*. Nay:
> ① **không dùng OpenAI cho chat nữa** — chat đi qua DashScope (`dashscope-intl.aliyuncs.com`);
> ② trần **không phải 200.000 mà 1.000.000** (gấp 5);
> ③ **token/lượt dùng để chia cũng đã đổi** — `14.198` là số của `gpt-4o-mini`, model không còn dùng.
>
> 🔴 **KHÔNG ĐỔI GIÁ TRỊ. Chỉ niêm căn cứ.** Đổi một con số mà không biết vì sao nó là con số đó
> chỉ tạo ra một con số mới cũng không ai biết vì sao. **Phải đo lại TRƯỚC khi ai chạm vào 20.**
>
> ⚠️ Và giữ nguyên cảnh báo cũ của chính mục này: **đừng đọc "20" thành "đang tự chặn ở 1/5 năng
> lực"** — đó là ghép số của trục **TPM** vào trục **ĐỒNG THỜI**. Hai trục khác nhau.

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
> ⭐ **MỞ RỘNG 19/08 (Lead đúc sau khi tự bắt mình, PO-agent nối vào A thay vì cấp ký hiệu mới —
> §7b: cùng mệnh đề, áp cho DỤNG CỤ CHẨN ĐOÁN TUỲ ỨNG thay vì cổng thường trực):**
> **Một dụng cụ cho CÙNG kết quả dù giả thuyết đúng hay sai thì không kiểm được giả thuyết nào —
> kể cả khi kết luận nó dẫn tới tình cờ đúng.** Hỏi trước khi tin một phép kiểm: *"nếu điều tôi
> đang bác BỎ mà lại ĐÚNG, dụng cụ này có cho ra kết quả khác không?"* Không ⟹ nó chưa KÊU bao giờ.
> [ĐO 19/08] Lead bác giả thuyết "ca đỏ là hồi quy của GĐ3" bằng `grep` phụ thuộc. Nhưng nếu nó
> **thật sự** là hồi quy, cùng lệnh `grep` vẫn cho cùng kết quả ⟹ không phân biệt được. Phép thử
> phân biệt được: **chạy ca đó trên bản TRƯỚC thay đổi** (PO-agent dựng worktree tại `8785da4`
> ⟹ đỏ y hệt ⟹ đỏ sẵn từ trước). Lời Lead: *"tôi kết luận đúng bằng một dụng cụ không đủ sức
> chứng minh điều tôi nói. May mắn không phải bằng chứng, dù kết quả trùng nhau."*
> *(Họ hàng: Luật N — số đếm phải kèm phép đếm; A-mở-rộng nói về PHÉP KIỂM phải kèm khả năng
> phân biệt.)*

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
> ⭐ **MỞ RỘNG 19/08 (ca của PO-agent + Lead, cùng một sai; Lead đề nghị ghi lâu dài — nối vào D
> thay vì cấp ký hiệu mới, §7b):** **NHIỀU LỆNH KHÁC NHAU ĐỌC CÙNG MỘT NGUỒN SAI thì chúng KHẲNG
> ĐỊNH LẪN NHAU, không kiểm được nhau.** Độc lập phải là của **NGUỒN DỮ LIỆU**, không phải của số
> lượng lệnh — đây là tầng dưới của vế DỤNG CỤ (độc lập của phép quét, không phải của người quét).
> [ĐO] PO-agent chạy `git merge-base main HEAD` · `git rev-list --count main` · `git merge-tree …
> main` — **ba lệnh, một ref `main` cục bộ ĐÃ CŨ TỪ LÚC CLONE** (`git fetch` KHÔNG cập nhật branch
> cục bộ, chỉ cập nhật `origin/main`). Cả ba nhất quán ⟹ không lệnh nào gây nghi ngờ ⟹ kết luận
> "hai nhánh không có tổ tiên chung, lệch 897 commit, 19 file xung đột" đã được **trình lên PO thật**
> như một phát hiện lớn. Sự thật: có tổ tiên chung, **0 xung đột**. Thứ bắt được không phải suy nghĩ
> lại mà là **`git push` bị từ chối** — tức chỉ một nguồn THỨ HAI (máy chủ) mới phá được vòng tự
> khẳng định. Giá: ~2 giờ của Lead + Coder xây trên tiền đề sai.
> **Vế thi hành:** ① trước khi kết luận về một nhánh, `git fetch` rồi so **`git branch -vv`** —
> ref cục bộ và ref từ xa **cùng TÊN là hai VẬT khác nhau** (họ "hai định nghĩa một vật").
> ② Tổng quát: khi ba phép đo cùng khớp, hỏi **chúng có đọc chung một nguồn không** trước khi coi
> sự khớp đó là xác nhận.
> ⚠️ **"Mang thông tin độc lập" ≠ "có NGUỒN độc lập".** Bảng chéo bác được *"một biến viết hai
> lần"* nhưng **KHÔNG** bác được *"hai hằng số gõ cạnh nhau"* — mà cái sau mới là thứ vỡ về sau.
> ⚠️ **Vế DỤNG CỤ (ca thật đầu tiên, 19/08 — Review bắt, Lead trình, PO-agent xếp vào D thay vì cấp
> chữ mới):** độc lập phải là của **PHÉP QUÉT**, không phải của **NGƯỜI QUÉT**. [ĐO] ba người đếm
> điểm-trả-lỗi độc lập cùng ra **8**; con số thật là **9** — điểm thứ chín (`_CHI_THI_DUNG_LAP`,
> hằng số dùng lại thay vì `return {...}` inline) nằm ngoài **hình dạng cả ba cùng quét**. Số người
> là mẫu số giả; phép quét mới là mẫu số thật. **Vế thi hành:** muốn có nguồn thứ hai cho một phép
> ĐẾM, đổi **cách đếm** (AST vs grep · runtime vs tĩnh), đừng đổi người đếm.

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

**Luật R** *(security đúc 18/08 §16.5, PO-agent cấp ký hiệu — bốn ca ở §5.R, ba nguồn độc lập)* —
**MỘT TÍNH CHẤT ĐƯỢC DỰA VÀO MÀ KHÔNG NÊU ĐƯỢC NÓ KHAI Ở ĐÂU THÌ KHÔNG PHẢI MỘT BẢO ĐẢM — NÓ LÀ MỘT
THÓI QUEN CỦA MÔI TRƯỜNG HIỆN TẠI.**
> **Phép thử một câu:** ***"nếu ngày mai thứ này biến mất, CÁI GÌ KÊU?"*** Không trả lời được ⟹ thứ
> đang giữ ta an toàn là **sự may mắn về cấu hình**, và **may mắn thì không xuất hiện trong diff**.
> **Ba điều khoản thi hành:**
> ① **Ba tiêu chí nhận dạng** (security khai trước khi đi tìm, không sau): đang được **dựa vào** ·
>   **không khai** ở contract/ADR/test nào · mất đi thì **hỏng IM LẶNG**. Đủ cả ba mới tính.
> ② 🔴 **Dạng nặng nhất là khi thứ được dựa vào lại là MỘT SỰ CỐ** (vd billing hỏng đang chặn job
>   tiêu tiền). Nó phản lại đúng vào **ngày ta sửa sự cố ấy** — tức đúng ngày ta đang chủ động đi tới,
>   và không ai nhớ có thứ đang dựa vào nó. **Đừng bao giờ để một sự cố làm cơ chế an toàn.**
> ③ **Ghi cả ô SẠCH.** Một danh sách chỉ có ca dương là danh sách không đọc được độ phủ. `thread_id`
>   (§5.R) là ca đối chứng: **có khai, đúng ba chỗ người ta sẽ phá nó** — đó là hình dạng đúng.
> **Khác Luật G ở chỗ nào:** G nói *cơ chế đang làm đúng việc của NÓ ≠ việc ta tưởng*. R hỏi một câu
> **hẹp hơn và kiểm được**: *ta có nêu ra được nó ĐƯỢC KHAI Ở ĐÂU không*. G là chẩn đoán; R là **phép
> thử ai cũng chạy được trong 10 giây**.
> ### 🔴 ④ MỘT PHÉP THỬ PHẢI HỎI **THỨ TA QUAN TÂM**, KHÔNG HỎI **THỨ ĐẠI DIỆN CHO NÓ**.
> *(security đúc 18/08 §18 — chẩn đoán gốc của PO-agent + tech-lead, security phát biểu thành điều
> khoản và tự khai điều đó. Đây là R áp cho **DỤNG CỤ CHẨN ĐOÁN**, không cho hệ thống.)*
> Mỗi **đại diện** mang theo **một giả định chưa kiểm**. Khi giả định ấy sai, phép thử trả về *"không
> có bằng chứng"* **MÃI MÃI** — và *"không có bằng chứng"* **không phân biệt được** với *"không có
> hiện tượng"*.
> **Vế thi hành, một câu hỏi:** trước khi tin một kết quả **ÂM TÍNH**, hỏi ***"điều kiện này ĐÃ BAO
> GIỜ BẮN CHƯA — ở đâu, lúc nào?"*** **Chưa bao giờ ⟹ chưa phải bằng chứng, mới là giả thuyết.**
> **Nếu chỉ nhớ một dòng:** *một phép thử không bao giờ bắn **không phải** một phép thử ĐÃ QUA — nó là
> một phép thử **CHƯA CHẠY**. Và nó **nguy hiểm hơn** một phép thử vắng mặt, vì nó **CHIẾM CHỖ** của
> phép thử thật: người ta thấy nó trong danh sách, tick, rồi đi tiếp.*
> **[ĐO] ca sinh ra nó (ADR-037 QĐ3①):** điều kiện dứt điểm *"đợi hai lượt trúng CÙNG TÊN MÁY"* do
> **PO-agent và tech-lead cùng đặt** — nó **không bao giờ bắn**, vì tên runner xoay theo từng job
> **trong khi đĩa vẫn chung**. Cả cái **TÊN** lẫn cái **PHÉP THỬ dựng ra để kiểm cái tên** đứng trên
> **CÙNG MỘT** giả định chưa ai kiểm: *danh tính runner đi cùng với đĩa*. Phép đo cứu được **chỉ vì
> nó hỏi thẳng thứ ta quan tâm** — *tệp có còn không* — thay vì thứ đại diện — *tên có trùng không*.
> **Vì sao thuộc R chứ không đứng riêng:** nó là **Luật A áp cho dụng cụ** — điều kiện ấy **IM lúc
> bình thường** (đúng) nhưng **chưa ai chứng minh nó KÊU lúc bất thường**, vì **chưa ai dựng ca đối
> chứng dương cho chính nó**. Và là **Luật H ở tầng phương pháp**: nó gộp *"đã kiểm, âm tính"* với
> *"không thể kiểm"* thành một dòng chữ, rồi dòng ấy khẳng định vế thứ nhất. **Ba trạng thái.**

**Luật S** *(tester đúc 18/08 sau khi tự làm lọt khoá và tự báo — PO-agent cấp ký hiệu)* —
**TÌM CẤU HÌNH THÌ `grep` TÊN BIẾN, ĐỪNG `grep` CẢ DÒNG.**
> `env | grep -i llm` **in nguyên văn giá trị** — và đó là câu lệnh **ai cũng gõ** khi đi tìm cấu
> hình. Dạng an toàn: `env | cut -d= -f1 | grep -i llm`.
> **[ĐO] 18/08:** một lượt như thế đưa `LLM_API_KEY` **đang hoạt động** vào log phiên — **chỗ thứ BA**
> khoá tồn tại, ngoài `.env` và `Config.Env` của container. Hai chỗ kia đã được kiểm kê; **chỗ thứ ba
> không ai liệt kê, vì nó không phải một tệp — nó là một THÓI QUEN gõ lệnh.**
> **Vế thi hành:** mọi bước ĐO chạm biến môi trường phải in **TÊN**, và chỉ in **giá trị** khi đã
> khẳng định biến ấy không nhạy cảm. Nghi ngờ ⟹ in tên.

**Luật T** *(Lead đúc 19/08 sau khi tự bắt mình thổi "thuần thắng" ngay sau hai lần sai liên tiếp —
PO-agent cấp ký hiệu; hệ quả của Luật M)* —
**RỦI RO LUẬT M KHÔNG PHÂN BỐ ĐỀU TRONG ĐỘI — NÓ DỒN VÀO NGƯỜI VỪA SAI.**
> Luật M nói: *kết quả ai cũng muốn nghe là kết quả không ai đi kiểm.* Luật T thêm vế phân bố:
> **người vừa sai liên tiếp là người MUỐN nghe "thắng" nhất trong phòng** — nên chính phát biểu
> "thắng" của họ là phát biểu ít được kiểm nhất, bởi đúng người ít có khả năng kiểm nhất.
> **[ĐO] 19/08:** Lead sai hai lần liền (đo regex thay cổng · lệnh thêm `\s`), rồi lập tức relay
> *"bản vá thuần thắng, giới hạn rỗng"* trên bộ ca do chính mình chọn — bộ ấy không có dạng
> phân-cách-trộn; ba ca trộn lọt, và mẫu GỐC từng bắt được cả ba (thu hẹp thật so với đường nền).
> **Vế thi hành:** sau khi sai ≥2 lần liên tiếp trong một mạch việc, phát biểu "thắng/sạch/xong"
> kế tiếp của mình phải được **người KHÁC kiểm trước khi relay** — tự kiểm kỹ hơn không thay được
> kiểm chéo, vì bộ lọc nằm ở khâu CHỌN CA, không ở khâu chạy ca.

**Luật U** *(đúc 19/08 từ HAI ca đo được cùng ngày, cùng hình dạng — PO-agent "gửi chuông thành công
≠ được nghe" · Lead "khai đóng-băng ≠ khoá được tiến trình đang chạy". PO-agent cấp ký hiệu)* —
**PHÁT ĐI không phải HIỆU LỰC. Thông điệp MỘT CHIỀU (chuông giao việc · lời khai trạng thái · lệnh
đóng băng) chỉ thành KHOÁ khi có xác nhận HAI CHIỀU.**
> [ĐO] ca ①: chuông GĐ2 transport báo success, người nhận chưa đọc — PO-agent báo PO thật "đang
> chạy" trên bằng chứng GỬI. [ĐO] ca ②: Lead khai *"không ai đo, không ai chạm ngăn xếp"* rồi dựng
> ảnh — lời khai chặn việc CHƯA bắt đầu, không dừng được đợt E2E nền ĐANG chạy phút thứ 1,5 ⟹
> 10/15 ca nhiễm hạ tầng, vứt cả đợt.
> **Vế thi hành:** ① GIAO việc — chưa có ACK người nhận thì việc CHƯA TỒN TẠI trong mọi báo cáo.
> ② DỪNG/đóng băng/dựng ảnh — phải HỎI TỪNG BÊN *"có tiến trình đang chạy chạm vật không?"* và
> CHỜ TRẢ LỜI; khai-trước chỉ là thông báo. ③ Mọi trạng thái relay lên trên dựng từ XÁC NHẬN,
> không từ "tôi đã phát". *(Họ hàng: Luật Q — ngữ cảnh là ảnh chụp; U nói về hành vi PHÁT thông điệp.)*

**Luật V** *(đúc 19/08 từ ca Lead tự khai: gặp rào backend-không-publish khi verify GĐ2, đi vòng
bằng `docker exec`, KHÔNG khai — QA/QC sau đó đâm đúng rào ấy, mất 20.665 token + một ca đỏ tự chẩn
từ đầu. PO-agent cấp ký hiệu)* — **Đi vòng một rào cản mà KHÔNG KHAI là biến bài học thành BÍ MẬT.
Rào cản là DỮ KIỆN của đội, không phải ma sát riêng của người gặp nó.**
> **Vế thi hành:** gặp rào (cổng không mở · quyền bị chặn · lệnh không chạy được) mà chọn đường
> vòng ⟹ đường vòng ấy phải THÀNH MỘT DÒNG cho đội (rào gì · vì sao có · đi vòng bằng gì) —
> TRƯỚC khi báo kết quả đạt được nhờ nó. Bài-học-chỉ-trong-đầu-một-người không phải bài học.
> *(Họ hàng: rào Caddyfile là quyết định bảo mật CÓ VĂN BẢN — không khai đường vòng còn che mất
> việc mình vừa lách một chủ đích.)*

**Luật W** *(đúc 19/08; PHÁT BIỂU ĐẦU tại `82c9c90` SAI — đúc trên tiền đề "mất ảnh nghiệm thu"
trong khi `38e65466e3ce` là BĂM NỘI DUNG `src/` (dau_ma_nguon.py), không phải image ID, và phép
đồng nhất vẫn xanh. Viết lại CÙNG NGÀY sau khi Lead rút finding và PO-agent đo lại độc lập)* —
**HAI LOẠI ĐỊNH DANH, đừng bắt cái này làm việc của cái kia: BĂM NỘI DUNG là hàm của vật — tự
tái lập bất cứ lúc nào, KHÔNG cần sổ, trả lời "VẬT LÀ GÌ". SỔ GIÁM HỘ trả lời "AI dựng · LÚC
NÀO · bằng LỆNH GÌ" — những câu không hàm nào của vật trả lời được.**
> **Vế thi hành:** ① kiểm danh tính vật nghiệm thu bằng BĂM NỘI DUNG (`dau_ma_nguon`, khớp
> host↔nhãn-trong-ảnh), KHÔNG bằng image ID — image ID đổi theo mọi lần build kể cả khi vật
> không đổi. ② Sự kiện DỰNG ảnh vẫn ghi một dòng `docs/nhat-ky/so-giam-ho-anh.md` (thời điểm ·
> vai · lệnh · image ID · nhãn băm ra) — vi phạm 12:45 19/08 (dựng không khai, không truy được
> ai) là ca sổ này sinh ra để chống. ③ **Nhãn 12-hex không kèm CÁCH ĐỌC thì người đọc tự cấp
> cho nó loại họ hay gặp nhất** — mọi nơi ghi băm phải ghi kèm loại (`cach_bam` đã có sẵn trong
> usage.jsonl; tên file mốc nền phải mang tiền tố loại). *(Họ hàng: Luật I — đo không ghi vào
> vật; Luật T — PO-agent phạm đúng T khi đúc phát biểu đầu: relay tiền đề của người vừa sai mà
> không kiểm.)*
> **Gốc của vế ③ — theo §7b, giữ nguồn CŨ HƠN, không mint luật mới:** vế ③ là phép tổng quát hoá
> của câu đã có từ 17/08 trong docstring `src/dau_ma_nguon.py`: *"một con số băm không kèm CÁCH
> BĂM thì không phải bằng chứng."* Ví dụ mới nhất: sự cố 7c hồ sơ 19/08 (đọc 12-hex-băm-nguồn
> thành image ID). Hình dạng "ba người một ngày cùng lớp lỗi" KHÔNG được cấp luật riêng —
> nó đã có tên ở đây. (Review đề nghị, PO-agent chuẩn y 19/08.)

**Luật X** *(PO-agent đúc 20/08, từ ca finding tool-calling — khẳng định "3/3 đạt, 3 ca chờ ngân
sách" lưu hành trong đội như dữ kiện; QA/QC rà `eval/results/` + `docs/security/`, loại từng ứng viên
có bằng chứng, **không thấy nó nằm trong file nào**. PO-agent tự nhận đã relay nó cho Bảo mật như một
số đo thật, và Bảo mật đã viết nó vào `docs/security/`)* — 🔴 **KẾT QUẢ ĐO PHẢI RƠI VÀO MỘT FILE
TRƯỚC KHI ĐƯỢC ĐI VÀO MỘT CÂU.** Không trích được **đường dẫn + cách dựng lại** ⟹ viết *"nghe báo,
chưa có vật chứng"*, **đừng viết con số trần**.
> **Vế thi hành:** ① Người **NHẬN** một con số qua tin nhắn chịu **cùng trách nhiệm** với người
> **PHÁT** — nhận rồi phát tiếp là chỗ dữ kiện giả được hợp thức hoá. Với người điều phối thì nặng
> hơn một bậc: vai đó **tồn tại để** chặn con số lại mà hỏi *"vật chứng đâu"*. ② **Khác Luật C:** C là
> PHƯƠNG PHÁP so khi đã có vật đo; X là ĐIỀU KIỆN để một con số **được coi là** vật đo — X đứng
> **trước** C. ③ **Khác Luật F:** F nói về HÌNH THỨC con số khi đã ở trong văn bản (có mẫu số không);
> X nói về TƯ CÁCH ĐƯỢC TRÍCH ngay từ đầu. ④ Họ hàng gần nhất: §5.Q *"file làm bản ghi, tin nhắn làm
> cái chuông"* — cùng tinh thần, khác miền (Q là kênh giao việc, X là dữ liệu đo). ⑤ **Phân biệt với
> nhóm "hết hạn":** sáu ca khác cùng ngày là trạng thái TỪNG đúng rồi thực tế đi qua — chữa bằng dọn
> sổ. X là trạng thái **chưa từng tồn tại ở dạng tra được** — không có gì để dọn, chỉ chặn được từ đầu.

🔴 **`mtime` trong `eval/results/` KHÔNG dùng làm mốc thời gian được** — [ĐO QA/QC 20/08] cả thư mục
mang chung dấu `Aug 18 14:33` do một lần rebuild reset. Ai dựng dòng thời gian từ mtime ở đó sẽ đọc
ra một lịch sử **không có thật**. Mốc thời gian tin được nằm **trong nội dung file**, không ở siêu dữ liệu.

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
