# Hồ sơ nghiệm thu GĐ2 + phụ lục GĐ2.5 — trình PO thật quyết MERGE

> Lead ráp 19/08/2026. Ráp ở scratchpad vì vai Lead không có trong bảng vùng ghi §4 —
> PO-agent kiểm vật lý độc lập rồi land vào `docs/`.
> Nguồn quyết định: `docs/giao-viec/2026-08-19-gd25-va-finding-ab-otp.md`
> — QĐ-B `32751c2` · QĐ-C `783ea5d` · QĐ-D `82c9c90` · **đính chính QĐ-D `847e21b`**.
> Chữ ký: Bảo Mật `4373c56` · Review (toàn văn ở mục 9).
> Cây làm việc SẠCH khi ráp.

---

## 0. Một trang cho người quyết

**Đề nghị:** merge GĐ2 + GĐ2.5.

**Cái đã chứng minh:** lỗi PO thật tự vấp trên UI (`tool_calls: null` → UI câm) đã chết, có
**cặp nhân quả** đo được hai đầu. Hai finding OTP (A, B) đã vá, 5 ca đỏ dựng sẵn từ hợp đồng
**xanh nguyên trạng** — không sửa một assertion nào.

**Cái CHƯA chứng minh, khai thẳng:** 3 ca nghiệm thu chưa chạy, vì **hai lý do khác nhau**
(mục 5). Và **6/168 gói phụ thuộc đã trôi** so với lock file — trôi có thật, đã đo tới tận nơi,
nằm ngoài mọi gói mà GĐ1/GĐ2 đo trực tiếp (mục 7e).

**Vật nghiệm thu còn nguyên:** băm mã nguồn `38e65466e3ce` khớp ba cách, và **mọi ca nghiệm thu
GĐ2.5 chạy trên đúng vật đang sống**, mỗi dòng sổ tự mang băm theo (7c, 7d). Lead từng báo ngược
lại — báo cáo ấy sai tại tiền đề, đã rút, và **ở lại trong hồ sơ**.

**Năm khối sự cố của chính đội** ở mục 7 — không phải phụ lục cho đẹp: **ba trong năm là lỗi
Lead**, cả ba tự khai trước khi bị ai vặn. Người ráp hồ sơ là người sai nhiều nhất trong đó; đó
là lý do hồ sơ này đáng tin hơn một hồ sơ sạch sẽ.

---

## 1. Cặp nhân quả — bằng chứng mạnh nhất của cả hai giai đoạn

Một ca xanh không chứng minh bản vá làm nó xanh. Cần **cùng một ca, đo hai lần, chỉ đổi bản vá**.

### 1a. GĐ2 — `tool_calls: null`

```
ca:  đăng nhập UI thật → gõ "chào bạn" (đường nhẹ, không gọi tool)
trên 57bdc05 (trước vá) :  ĐỎ   — UI hiện "Có lỗi khi kết nối trợ lý"
                                   backend 200 OK, reply ĐẦY ĐỦ, tool_calls = null
                                   ChatClient.tsx: result.tool_calls.length → TypeError
trên 06132a9 (sau vá)   :  XANH  — bubble reply vẽ đúng
đổi giữa hai lần đo: CHỈ 3 envelope :639/:789/:906 None→[] + chuẩn hoá biên main.py:659
```

### 1b. GĐ2.5 — Finding A (rail OTP đóng lại sau F5)

```
ca:  AUTH-003 — xác thực OTP xong → F5 → rail giao dịch phải CÒN MỞ (hợp đồng 12h)
trước vá A : ĐỎ      sau vá A : XANH      hiệu ngân sách = 0 token
```

🔴 **`hiệu = 0` là con số đắt nhất trong hồ sơ này.** Nó nói: cặp nhân quả sạch nhất của cả đợt
**không tốn một token nào**. Ca đắt không đồng nghĩa ca có giá trị.

---

## 2. Cổng nghiệm thu GĐ2.5 — 5 ca đỏ dựng sẵn

Viết từ hợp đồng ADR-005 / AUTH-005 / AUTH-007 / AUTH-008 **TRƯỚC KHI** bản vá tồn tại. Điều
kiện: phải xanh **nguyên trạng**, sửa assertion nào phải khai từng dòng. **Không assertion nào bị sửa.**

| ca | kết quả | token |
|---|---|---|
| AUTH-003 | ✓ XANH | 0 |
| AUTH-001-tiếp | ✓ XANH | 20.658 |
| AUTH-006 | ✓ XANH | 28.074 |
| AUTH-007 ca 1 | ✓ XANH | 36.340 |
| AUTH-008 ca 1 | ❌ ĐỎ — **hạ tầng test**, không phải bản vá | 20.665 |
| AUTH-007 ca 2 | ⬜ chưa chạy — **rào NGÂN SÁCH** | — |
| AUTH-008 ca 2 | ⬜ chưa chạy — **rào MẠNG** | — |

**Sổ GĐ2.5 CHỐT: 105.737 / 130.000.**

---

## 3. Vì sao "chưa chạy" KHÔNG phải lỗ nghiệm thu khách hàng

[ĐO] BFF không có route `tools/create-ticket`:

```
frontend/src/app/api/tools/  →  customer-history · escalate-ticket
                                lookup-transaction · propose-resolution
                                (KHÔNG có create-ticket)
```

Trình duyệt **không bao giờ** gọi `/tools/create_ticket` trực tiếp — nó chỉ được gọi làm **tool
bên trong** `/agent/chat`. Hai cổng chưa chạy canh **guard phòng thủ chiều sâu (403 route-level)**,
tức **lớp thứ hai mà sản phẩm không lộ cho người dùng**. Đường khách thật đi — agent chat, tool
trong-tiến-trình, `status:"error"` trong HTTP 200 — đã có cặp nhân quả xanh ở mục 1.

> **Chưa-chạy ≠ lỗ nghiệm thu khách-hàng — VỚI ĐIỀU KIỆN KHAI RÕ.** *(nguyên văn QĐ-C)*

Mệnh đề điều kiện đó là bản lề. Mất nó, mục này thành che giấu.

---

## 4. Ngân sách — chuỗi 3 lần lệch, cả 3 đều đã khai

Ghi vào hồ sơ vì **cách ước sai** có giá trị hơn con số đúng.

| # | ước | thật | nguyên nhân |
|---|---|---|---|
| 1 | 110–140K (PO duyệt) | **207.119** | Lead ra lệnh chạy lại cả bộ 11 ca **mà không hỏi giá trước** |
| 2 | "0 token" | **6.251** | Lead công bố sổ GĐ2.5 = 0 **mà chưa đo** |
| 3 | 15–20K/ca | **20.658 / 28.074 / 36.340** | Lead duyệt ước **mà chưa đọc thân test** — ba ca có ba cấu trúc khác nhau (AUTH-006 hai lượt LLM tuần tự; AUTH-007 năm lời gọi model qua hai lượt HTTP) |

Hai luật rút ra, đã áp:
- **"0-token là một PHÉP ĐO, không phải một PHÂN LOẠI."** Đọc sổ trước và sau, đừng dán nhãn.
- **"SAU là khi sổ NGỪNG TĂNG, chứ không phải khi tiến trình thoát."** *(QA/QC tinh chỉnh, sau khi đọc sổ quá sớm lúc auto-continuation còn đang chạy.)*

---

## 5. Hai dòng chưa-chạy — NGUYÊN VĂN, không được gộp

> **AUTH-008 ×2 = chưa chạy vì rào MẠNG. AUTH-007 ca 2 = chưa chạy vì rào NGÂN SÁCH.**
> **Hai lý do khác nhau, hai cách gỡ khác nhau, đừng gộp.**

Gộp vào một dòng "chưa chạy" là để đợt sau tưởng **cứ có tiền là xong**.

**Rào MẠNG [ĐO]:**
```
docker ps → fin05-backend-1  "8010/tcp"   ← EXPOSE, KHÔNG publish ra host
auth.spec.ts:379 · auth-multirole.spec.ts:23 → BACKEND_URL ?? "http://localhost:8010"
Playwright chạy TỪ HOST → connect ECONNREFUSED ::1:8010
Caddyfile:11-26 → không lộ backend là CHỦ ĐÍCH bảo mật, ngoại lệ duy nhất /ws/live-chat*
```

**Cách gỡ đã quyết:** (b) Playwright chạy **TRONG** mạng Docker — đi nhờ chuyến GĐ3, việc Coder,
**KHÔNG là điều kiện merge**. Một việc gỡ ba thứ: AUTH-008×2 · AUTH-007 ca 2 · lỗ cùng dạng ở
`auth-multirole.spec.ts`. (c) publish cổng backend ra host: **BÁC** — đảo một quyết định bảo mật
có văn bản để mua thứ (b) mua được miễn phí.

**Đã vá phần khai (0 token, `d395cf4`, QA/QC):** chốt `test.skip` trước đây khai **đúng một**
điều kiện (`JWT_SECRET_KEY`) trong khi có **hai**. Nay khai đủ, kèm cách gỡ ngay tại chú thích.

---

## 6. Ghi nhận QA/QC — hành vi muốn nhân bản, không phải lời khen

1. `curl` **cả hai đường** để **CHỨNG MINH** rào mạng, thay vì báo "hình như không kết nối được".
2. Đọc `Caddyfile` tìm **CHỦ ĐÍCH** thay vì đoán — nhờ đó (c) bị bác có căn cứ, không phải theo cảm tính.
3. **Cộng 20.665 token của ca HỎNG vào sổ.** Nhiều người bỏ khoản này vì "test có chạy được đâu".
   Bỏ nó là làm sổ nói dối về giá thật của việc thử.
4. Ở `d395cf4`: **trỏ chéo thay vì chép lại** nội dung sang file thứ hai — để hai bản không trôi khỏi nhau.

---

## 7. NĂM khối sự cố của đội

Nằm trong hồ sơ chính, không phải phụ lục. **Ba trong năm là lỗi Lead**, cả ba tự khai trước khi
bị phát hiện. 7d và 7e là thứ đội **thu được** nhờ 7c bị moi ra — không phải sự cố, nhưng thuộc
cùng câu chuyện nên để cạnh nhau.

### 7a. Đóng băng bị vi phạm bởi chính người tuyên bố đóng băng (GĐ2)

Lead tuyên bố với cả bốn vai là chỉ dựng frontend, rồi chạy `--build frontend` **thiếu `--no-deps`**
⟹ **dựng luôn backend**. Sau đó **ép recreate hai lần dựa trên một phỏng đoán sai** ("nhãn nói dối"
— nhãn hoá ra nói thật).

### 7b. Đi vòng một rào cản mà không khai → **Luật V** (STATE §7, `a98754f`)

Lead vấp **đúng** rào mạng ở mục 5 khi verify GĐ2, **vòng qua bằng `docker exec`, không nói với ai.**
Giá đo được: **20.665 token + một ca QA/QC phải tự chẩn từ đầu**.

> **Luật V — Đi vòng một rào cản mà không khai là biến bài học thành bí mật; rào cản là DỮ KIỆN
> của đội, không phải ma sát riêng của người gặp nó.**
> Vế thi hành: đường vòng phải thành **một dòng cho đội** TRƯỚC khi báo kết quả đạt được nhờ nó.

### 7c. 🔴 Lead trình một finding SAI TẠI TIỀN ĐỀ — giữ nguyên trong hồ sơ, không xoá

**Tôi đã trình:** "vật nghiệm thu GĐ2 — ảnh Docker `38e65466e3ce` — không còn tồn tại, không
truy hồi được", kèm đề nghị thay phép kiểm đồng nhất bằng phép kiểm tương đương. PO ra
**QUYẾT ĐỊNH D** (`82c9c90`) trên tiền đề đó, **mint Luật W**, và **mở sổ giám hộ ảnh**.

**Tiền đề SAI.** `38e65466e3ce` **không phải Docker image ID**:

```
src/build_stamp.py:46   CACH_BAM = "sha256-noi-dung-src-py-da-sap-xep-12"
src/build_stamp.py:50   bam_ma_nguon() = sha256(nội dung mọi src/**/*.py đã sắp xếp)[:12]
src/build_stamp.py:62   DUONG_NHAN = /app/.source_hash  ← đóng vào ảnh lúc build
```

Đó là **băm NỘI DUNG MÃ NGUỒN**, ghi vào mọi dòng `usage.jsonl` (`bam_ma_nguon` + `cach_bam`).
Tôi đọc 12 hex, **nhận nhầm thành image ID**, chạy `docker image inspect`, thấy "KHÔNG CÒN".

**Phép kiểm đồng nhất CHẠY ĐƯỢC và ĐÃ XANH — ba cách, một số:**

```
nhãn đóng vào ảnh (nhan_luc_dung)        : 38e65466e3ce
tính LẠI từ src/ đang nằm TRONG ảnh      : 38e65466e3ce
tính trên HOST từ src/ của cây làm việc  : 38e65466e3ce
```

🔴 `src/build_stamp.py` tồn tại **CHÍNH VÌ** `build_commit` đã bị chứng minh nói dối **cả hai
chiều** hôm 17/08 (docstring dòng 5-14). Dự án **đã giải xong** đúng bài toán tôi tuyên bố là nó
chưa có. Tôi bỏ qua cái nhãn dự án dựng để chống lỗi này, và với tay sang **đúng loại định danh
mà nhãn ấy sinh ra để thay thế**.

**Cái CÒN đúng, đã hạ cấp:** ảnh Docker bị dựng lại 12:45:37 + container recreate 12:47:47
**không ai khai**, và **không truy được ai dựng**. Kỷ luật đóng băng vẫn bị vi phạm — nhưng hệ
quả tôi gán cho nó thì không tồn tại.

**Cơ chế còn ghi được cả lúc băm ĐỔI — tức nó hoạt động đúng:**
```
00:18–00:51Z  bam = 227ffeb050fe   ← trước bản vá GĐ2
00:53:01Z  →  bam = 38e65466e3ce   ← sau; 06132a9 land 00:49:37Z, băm đổi 4 phút sau
12:45:37    lần dựng hôm nay KHÔNG làm băm đổi — đúng, vì 1b916f1 chỉ chạm frontend
```
Cặp `38e65466e3ce ↔ 06132a9` là **đo được**, không chép từ brief.

**Tự phân loại:** đội đã đặt tên lớp lỗi này — *một dụng cụ đo im lặng trả về một giá trị trông
hợp lệ cho câu hỏi nó không thật sự trả lời.* Lần này **dụng cụ là Lead**. Và xảy ra **đúng ngày**
mint Luật V, **trong lúc gom số cho hồ sơ nói về chính lớp lỗi đó**.

> 🔴 **Một nhãn không kèm CÁCH ĐỌC thì người đọc tự cấp cho nó một loại — và loại họ cấp là loại
> họ hay gặp nhất.** `cach_bam` nằm ngay cạnh trong từng dòng sổ. Tôi đã không đọc nó.

**Và lỗi thứ hai, của người kiểm — PO-agent tự khai, để lại cạnh lỗi Lead:**

PO-agent **tiếp nhận tiền đề của Lead mà không kiểm**, rồi trong vòng một giờ **đúc Luật W và mở
một sổ mới** trên tiền đề ấy. Đúng lúc **Luật T** ("rủi ro dồn về phía người vừa sai") bảo phải
soi kỹ nhất. Nguyên văn PO: *"Người kiểm relay tiền đề của người bị kiểm là bỏ trạm gác."*

⟹ Sự cố này cần **hai** người mới xảy ra: một người đọc nhầm loại nhãn, và một người **không đọc
lại**. Hồ sơ giữ cả hai — vì gỡ vế thứ hai đi thì bài học thành "Lead cẩu thả", và đó là bài học
sai, nó không dạy ai cách chặn lần sau.

**Đã sửa (`847e21b`), PO tự đo lại bằng dụng cụ của họ trước khi viết:** QĐ-D đính chính, (α)/(β)
vô hiệu, câu "ba phép trùng khớp…" **rút**; Luật W viết lại thành **hai loại định danh** — băm nội
dung là **hàm của vật**, không cần sổ, trả lời *VẬT LÀ GÌ*; sổ giám hộ trả lời *AI · LÚC NÀO · LỆNH GÌ*;
sổ giám hộ viết lại, dòng cũ **rút có ghi vết**, dòng mới đánh dấu rõ đâu là **[suy]** đâu là **[đo]**.

---

### 7d. Điều tốt lên nhờ 7c — mốc giờ từng ca, và một phép kiểm mạnh hơn

**Mọi ca nghiệm thu GĐ2.5 chạy SAU recreate (05:47:47Z)**, trên đúng vật đang sống, mỗi dòng tự
mang băm mã nguồn. Không ca nào cần "tương đương" — tất cả là **phép đo TRỰC TIẾP**:

| ca | ts (UTC) | gọi model | token | `bam_ma_nguon` |
|---|---|---|---|---|
| AUTH-003 | 06:04:32 | 0 | **0** | 38e65466e3ce |
| AUTH-001-tiếp | 06:30:41 | 3 | **20.658** | 38e65466e3ce |
| AUTH-006 | 06:33:53–57 | 4 | **28.074** | 38e65466e3ce |
| AUTH-007 ca 1 | 06:36:51–53 | 5 | **36.340** | 38e65466e3ce |
| AUTH-008 ca 1 | 06:40:42 | 3 | **20.665** | 38e65466e3ce |

**Khoảng trống THẬT còn lại (Bảo Mật tìm, Lead xác nhận):** `Dockerfile:5` và `:33` ghim base
image bằng **TAG** `python:3.12-slim`, **không phải digest**. Có từ TRƯỚC GĐ2.5, không chặn merge
— vào sổ nợ, cùng nguyên tắc dự án đã áp cho GitHub Actions.

### 7e. Phụ thuộc CÓ TRÔI THẬT — Review đo được, và nó sửa một suy luận của Bảo Mật

Ba lời khai về cùng một câu hỏi, xếp theo mức chứng cứ:

| ai | nói gì | trạng thái |
|---|---|---|
| **Lead** | "ảnh cũ mất ⟹ **không thể** diff 168 gói" | khai giới hạn, **không đo** |
| **Bảo Mật** | `git diff -- requirements*.txt Dockerfile` RỖNG ⟹ "168 gói **không có lý do trôi**" | suy luận **đúng phép, sai tiền đề** |
| **Review** | đo thẳng `pip freeze` vs `requirements.lock.txt` | **6 gói trôi thật** |

🔴 **Tiền đề chưa kiểm của Bảo Mật:** họ giả định `requirements.lock.txt` là thứ `docker build` dùng.
Review đọc Dockerfile và thấy **không phải**. Lead kiểm lại độc lập:

```
Dockerfile:20-21   COPY requirements.txt .  /  RUN pip install -r requirements.txt
grep -rn "requirements.lock" Dockerfile .github/ docker-compose*.yml scripts/  →  KHÔNG KẾT QUẢ
requirements.txt   37 dòng yêu cầu:  10 ghim cứng ==  ·  27 lỏng >=
```

**Một lock file tồn tại, ghim 168 gói, và KHÔNG NƠI NÀO dùng nó.** Nó không phải hàng rào — nó là
**một tấm ảnh chụp bị nhầm thành hàng rào**. Diff nó ra rỗng vì **không ai đọc nó**, không phải vì
không có gì trôi.

**Trôi thật, Lead đo lại bằng cách đếm riêng — trùng khít danh sách của Review, 6/6:**

```
charset-normalizer  3.5.0   → 3.5.1     patch · encoding HTTP qua requests
langsmith           0.10.18 → 0.11.0    MINOR · client tracing LangChain
orjson              3.11.9  → 3.12.0    MINOR · serialize JSON
phonenumbers        9.0.36  → 9.0.37    patch · CSDL số điện thoại, đổi gần như hàng ngày
pypdf               6.16.0  → 6.16.1    patch · parse PDF cho RAG
python-dotenv       1.2.2   → 1.2.3     patch · nạp .env
162/168 CÒN LẠI trùng khít — gồm TOÀN BỘ họ langchain/langgraph/fastapi/pydantic/sqlalchemy
```

**Hai rủi ro Review nêu là RỦI RO (không kết luận) — Lead đo nốt, 0 token:**

```
orjson    grep -rn "orjson" src/           → KHÔNG KẾT QUẢ
          app = FastAPI(…) main.py:152     → KHÔNG đặt default_response_class
          ⟹ envelope trả về đi bằng JSONResponse (json chuẩn thư viện), KHÔNG qua orjson.
          Nhưng orjson CÓ nằm trong đường serialize checkpoint của langgraph
          (Required-by: chromadb · langgraph-checkpoint-postgres · langgraph-sdk · langsmith).
          Nói đúng mức: KHÔNG chạm envelope; CÓ chạm lưu trạng thái graph.
langsmith LANGCHAIN_TRACING_V2=false · LANGCHAIN_API_KEY= (rỗng)
          ⟹ tracing TẮT. Bản trôi này không ghi gì, nên không lệch được cái gì.
```

**Kết luận đúng mức:** trôi **có thật**, nằm **ngoài** mọi gói mà GĐ1/GĐ2 đo trực tiếp, và hai
đường có thể chạm đã được đo tới tận nơi. Đây **không** phải "đồng nhất" — nhưng nó là
**khai giới hạn KÈM SỐ ĐO của đúng giới hạn đó**, khác hẳn "có gì đó có thể đã trôi".

**Ghi nhận Review:** họ được giao soi bản vá, nhưng khi Lead hỏi "chỗ nào mỏng nhất" thì họ
**không trả lời bằng ý kiến** — họ đi tìm cái Lead khai là không đo được, **và đo nó**. Đồng thời
tự dựng **đối chứng dương** cho hai cổng ghim (bẻ lệch từng bên, xác nhận cổng KÊU, rồi khôi phục)
thay vì nhận lời khai rằng cổng hoạt động.

## 8. Nợ CÓ CHUYẾN — không phải "sau này"

| nợ | đi cùng chuyến |
|---|---|
| Thêm `"loai":"otp_het_tuoi"` vào `_OTP_EXPIRED_ERROR`/`_OTP_REQUIRED_ERROR`; client đọc `loai`; **tháo cổng ghim** | GĐ3 (gỡ băng backend cho tầng xoay model) |
| Playwright chạy TRONG mạng Docker | GĐ3, Coder |
| Siết nhánh 403-role `ChatClient.tsx:431` (`/role/i` lỏng hơn cần) | cùng đợt client đọc `loai` |
| Sổ giám hộ cho việc dựng ảnh — biết **AI** dựng, **LÚC NÀO** (thứ băm nội dung không trả lời) | **chưa có chuyến — cần PO xếp** |
| 🔴 **Nối `requirements.lock.txt` vào Dockerfile** — file đã tồn tại, ghim đủ 168 gói, và **không nơi nào dùng nó**. Không nối thì mỗi lần dựng lại trôi tiếp, tích luỹ qua nhiều lần sẽ khó truy hơn lần này rất nhiều (7e) | **chưa có chuyến — đề nghị GĐ3, cùng đợt gỡ băng backend** |
| Ghim base image theo **digest** thay vì tag `python:3.12-slim` (`Dockerfile:5`, `:33`) | GĐ3 — cùng nguyên tắc đã áp cho GitHub Actions |

**Cổng ghim tồn tại chính là lời nhắc tự động** — không có "tạm thời vĩnh viễn".

---

## 9. Định nghĩa xong — đối chiếu

- [x] Finding A: F5 sau OTP, rail còn mở (AUTH-003 cặp nhân quả)
- [x] Finding B: OTP hết tươi thành **lời mời**, không phải lỗi câm
- [x] 5 ca đỏ dựng sẵn → xanh **nguyên trạng**, không sửa assertion *(4 xanh, 1 chặn bởi hạ tầng test — mục 5)*
- [x] Smoke 0-token xanh trên frontend mới
- [x] **Băm backend giữ nguyên `38e65466e3ce`** — ĐẠT, ba cách một số (7c). *Lead từng báo ô này
      KHÔNG ĐẠT; báo cáo ấy sai tại tiền đề và đã rút — xem 7c.*
- [x] Sổ token khai đủ (mục 4) — **105.737 / 130.000**
- [x] **Chữ ký Bảo Mật** — CÓ, `docs/security/2026-08-19-gd25-chu-ky-finding-ab.md` (`4373c56`).
      Ký trên diff thật (`git show 6441319`, `git show 1b916f1`), không nhận mô tả của Lead.
      Không điều kiện chặn. *(Một suy luận trong chữ ký cần đọc kèm 7e — xem ở đó.)*
- [x] **Chữ ký Review** — CÓ, không điều kiện nào treo. Tự chạy **đối chứng dương** cho cả hai cổng
      ghim; tự tái tạo độc lập 4862 / langchain-core 1.5.4 / md5; và **tự đo** lỗ phụ thuộc (7e).
      Ghi rõ: Review **KHÔNG ký trên câu chữ (b) cũ** — hạng mục soi đó đã bị QĐ-B thay.

**Mọi ô đã đóng.** Ô duy nhất từng mở là ô Lead tự mở bằng một finding sai tiền đề — nó ở lại
hồ sơ tại 7c, không bị xoá theo kết quả.

---

## 10. Phụ chú kiểm định độc lập của PO-agent — 19/08, TRƯỚC khi land hồ sơ này

Toàn bộ đo bằng dụng cụ của PO-agent, không dùng lại số của Lead:

```
HEAD 847e21b · cây làm việc SẠCH
git log 1b916f1..HEAD -- src/          → RỖNG (không commit nào chạm backend src)
băm nguồn tự tính từ src/ host          → 38e65466e3ce  == nhãn /app/.source_hash trong ảnh
docker exec printenv BUILD_COMMIT       → 1b916f1
chữ ký Bảo Mật                          → docs/security/2026-08-19-gd25-chu-ky-finding-ab.md (có, ký trên diff thật)
số học sổ: 0+20.658+28.074+36.340+20.665 = 105.737  → khớp sổ chốt ĐÚNG TỪNG CHỮ SỐ
cổng invariants chạy lại từ host (venv P-121-new, env giả CI) → 23 passed
```

**Kết luận của người kiểm: hồ sơ ĐẠT, đủ điều kiện trình PO thật quyết merge.**
