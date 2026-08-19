# GĐ2.5 — Chữ ký Bảo Mật cho Finding A + Finding B

> 19/08/2026. Ký trên DIFF THẬT đã đọc (`git show 6441319`, `git show 1b916f1`), không dựa mô tả
> commit. Phạm vi ký nêu rõ ở cuối — đọc trước khi trích dẫn "Bảo Mật đã ký" ở chỗ khác.

## KÝ: CÓ, cho cả Finding A và Finding B, theo đúng phạm vi câu 44 brief GĐ2.5.

### Finding A (`6441319`) — [ĐO] khớp đúng ràng buộc đã đặt ra

- `getOtpXemConHan(): boolean` (`session-server.ts`) — trả **boolean thuần**, docstring tự khai
  *"KHÔNG BAO GIỜ trả nguyên claim JWT ra ngoài hàm này"*. Đọc code xác nhận đúng: hàm decode JWT
  **nội bộ**, chỉ `return` một so sánh (`ageMinutes <= OTP_VIEW_MAX_MINUTES`).
- `page.tsx` truyền đúng MỘT prop dẫn xuất (`otpXemConHanLucTai`) — không có `access_token`/claim
  nào lọt ra props.
- Tên biến `...LucTai` tự khai đây là ảnh chụp lúc render, không phải trạng thái sống — đúng điều
  kiện tôi nêu ("không coi là nguồn xác thực real-time").
- Ngưỡng `OTP_VIEW_MAX_MINUTES` là bản sao **có khai nguồn** (`src/config.py`) — có cổng ghim
  (`ChatClient.pin.test.ts` cổng ①) so giá trị hai bên, không so text.

### Finding B (`1b916f1`) — [ĐO] đúng hướng (b) tôi cảnh báo phải xác nhận trước khi viết catch

Xác nhận Coder đã tự phát hiện đúng thứ tôi nêu trong hồ sơ `2026-08-19-gd25-otp-field-bien-va-phan-biet-403.md`
(không cần tôi nhắc lại) — commit message ghi rõ: *"catch(e).status===403 viết theo brief gốc sẽ
không bao giờ bắn... đã dừng lại báo Lead trước khi viết"*. Bản vá đi đúng hướng (b): đọc
`result.tool_calls[].result.status === "error"` trong response 200, KHÔNG bịa ra một đường 403
không tồn tại.

- **Discriminator dùng `===` tuyệt đối** trên hằng số backend thật (`OTP_EXPIRED_MESSAGE`), KHÔNG
  regex/substring — đúng yêu cầu "dấu hiệu bền" tôi đặt ra, siết hơn cả đề xuất `startsWith()` ban
  đầu của tôi.
- **Ba trạng thái được tôn trọng:** khớp sai/không khớp rơi qua nhánh `touchedSensitiveData` cũ —
  KHÔNG bị gộp ngầm vào "OTP". Đúng điều khoản tôi đặt ra ở câu ②.
- **Cổng ghim `ChatClient.pin.test.ts` cổng ②** so `_OTP_EXPIRED_ERROR.message` hai phía bằng đọc
  VĂN BẢN THUẦN (không `import` từ `src/`) — đây CHÍNH LÀ đề xuất "một dòng comment liên kết coupling"
  tôi đưa ra hôm qua, nhưng làm MẠNH HƠN: một bài test THẬT SỰ CHẠY và ĐỎ khi lệch, không chỉ một dòng
  chữ hy vọng có người đọc. Không còn gì để yêu cầu thêm ở điểm này — nợ (i) đã "có hạn kèm chuyến"
  đúng nghĩa, không phải một lời hứa suông.

## 🔴 VỀ DỮ KIỆN MỚI — ảnh backend cũ (`38e65466e3ce`) bị xoá, không diff được 168 gói + OS

**Không chặn chữ ký này**, và tôi nói rõ VÌ SAO, không chỉ nói "không chặn":

1. **Nằm NGOÀI phạm vi Finding A/B.** Hai chữ ký trên xác nhận một TÍNH CHẤT LOGIC ỨNG DỤNG (biên
   dữ liệu qua BFF, chiều fail-closed OTP) — đọc từ **mã nguồn** (`git diff 06132a9..HEAD -- src/`
   rỗng, xác nhận độc lập bởi cả Lead lẫn tôi), không phụ thuộc gì vào việc image nào đang chạy hay
   gói OS nào bên dưới. Tính đúng đắn của hai finding này không suy giảm dù không diff được ảnh cũ.
2. **[ĐO] tự kiểm — vật thay thế cho việc diff ảnh, mạnh hơn diff ảnh ở điểm quan trọng nhất:**
   `git diff 06132a9..HEAD -- requirements.lock.txt requirements.txt Dockerfile` → **RỖNG**. Lock
   file là nguồn xác định phiên bản 168 gói Python — không đổi thì **không có lý do để phiên bản gói
   đổi**, bất kể build ở lần nào. Diff-ảnh-cũ nếu còn cũng chỉ xác nhận lại đúng điều này, không hơn.
3. **Khoảng trống THẬT còn lại, không phải giả:** `Dockerfile:5,33` ghim base image bằng **TAG**
   (`FROM python:3.12-slim`), không phải **digest**. Tag này TRÔI theo thời gian (Docker Hub cập
   nhật bản vá OS/Python patch dưới cùng một tên) — hai lần build cùng Dockerfile, cách nhau vài
   ngày, có thể kéo hai layer OS khác nhau dù mọi file trong repo giống hệt. Đây là khoảng trống
   **CÓ THẬT, TỒN TẠI TỪ TRƯỚC GĐ2.5**, không phải điều GĐ2.5 gây ra, và **không có gì trong đợt vá
   Finding A/B chạm tới lớp này**.

**Kết luận:** không xin PO thật DỪNG merge vì lý do này. Việc bảo mật của tôi đúng phạm vi được giao
là ĐẠT. Ghi một mục sổ nợ RIÊNG (không phải điều kiện của chữ ký GĐ2.5): *ghim `FROM python:3.12-slim`
bằng digest thay vì tag* — cùng nguyên tắc "ghim phiên bản, chống trôi chuỗi cung ứng" dự án đã áp cho
GitHub Actions (`@v4` không `@main`, ADR liên quan CI). Việc RẺ, KHÔNG GẤP — làm lúc nào backend gỡ
băng lần tới, không phải hôm nay.

## QĐ-C (PO bác publish cổng backend ra host) — ghi nhận, không việc gì thêm

Không mở bề mặt mạng mới — khớp mọi phân tích trước đó của tôi (mọi kết luận về biên dữ liệu/JWT dựa
trên kiến trúc BFF hiện có, cookie httpOnly, không route mới). Không cần xem lại gì.

## PHẠM VI CHỮ KÝ — đọc trước khi trích dẫn

Ký cho: (1) Finding A — field boundary qua BFF đủ hẹp, không lộ claim JWT thô. (2) Finding B — chiều
fail-closed phía server không đổi, discriminator client dùng dấu hiệu bền (so tuyệt đối, có cổng
ghim), ba trạng thái được tôn trọng.
**KHÔNG ký cho:** toàn vẹn mặt phẳng phụ thuộc ảnh (168 gói/OS) — ngoài phạm vi được giao, và đã nêu
lý do kỹ thuật vì sao không cần chặn vì lý do đó (mục trên). Không ký thay Review (diff B/regex vá
GĐ3 thuộc vai khác) — chỉ ký phần tôi được giao.

---

## 🔴 NIÊM 19/08 (Lead + Review) — SUY LUẬN LOCK-FILE Ở TRÊN SAI TIỀN ĐỀ. THÂN GIỮ NGUYÊN, ĐỌC KÈM MỤC NÀY.

*(Đúng Luật P: niêm tại chỗ phát biểu sai đứng, không sửa lại chữ cũ — người sau cần thấy CẢ câu sai
LẪN câu đúng, không chỉ câu đúng.)*

**[ĐO] tự kiểm lại sau khi Lead báo, không nhận nguyên văn:**
```
Dockerfile:20-21   COPY requirements.txt .  →  RUN pip install -r requirements.txt
grep -rn "requirements.lock" Dockerfile .github/ docker-compose*.yml scripts/  →  0 kết quả
```
**`requirements.lock.txt` KHÔNG được `docker build` đọc ở đâu cả.** Phép suy ở mục trên
(*"diff lock file rỗng ⟹ không có lý do gói trôi"*) **sai vì tiền đề sai** — tôi kiểm diff đúng
file, nhưng chưa kiểm file đó có được DÙNG hay không trước khi suy từ nó. Đúng lớp lỗi Lead tự nhận
("suy đúng phép, tiền đề chưa kiểm") — và đúng cùng ngày ba người mắc same lớp, độc lập.

**Định hạng 6 gói trôi thật (Lead+Review đo, tôi kiểm lại phần thuộc vai mình):**

| gói | vai trò | [ĐO] kiểm thêm | rủi ro |
|---|---|---|---|
| `langsmith` 0.10.18→0.11.0 | tracer LangSmith Cloud — **kênh xuất PII SONG SONG bị TẮT có chủ đích** (`config.py:439-457`, F-30, 15/08) | `os.environ.setdefault("LANGCHAIN_TRACING_V2","false")` **VÀ** `setdefault("LANGSMITH_TRACING","false")` — code đã tự phòng cả TÊN CỜ CŨ LẪN MỚI ("tên mới của cùng cờ") | **THẤP, không PHẢI KHÔNG** — gate là biến môi trường phía TA, không phụ thuộc nội bộ langsmith; nhưng gate chỉ phòng được cờ ĐÃ BIẾT TÊN, không phòng được một kênh telemetry MỚI mà bản 0.11.0 có thể thêm dưới tên khác |
| `orjson` 3.11.9→3.12.0 | không dùng trực tiếp trong `src/` — transitive qua `langgraph-checkpoint-postgres`, nhiều khả năng dùng để (de)serialize checkpoint state | chưa đo thẳng — [PHẢI KIỂM], không phải [ĐO] | **THẤP cho bảo mật** (không đổi CÁI GÌ được mã hoá — kho checkpoint đã biết 0% mã hoá từ trước, §5.J STATE, việc này không làm nó tệ hơn); **KHÔNG THẤP cho toàn vẹn dữ liệu** — đổi định dạng serialize có thể ảnh hưởng đọc lại checkpoint cũ, NGOÀI thẩm quyền bảo mật của tôi |
| `pypdf` 6.16.0→6.16.1 | parse PDF chính sách `partner_admin` upload (`rag/parsers.py:126`) | patch version (6.16.0→.1), không phải minor/major | **THẤP** — cùng biên tin cậy cũ (`partner_admin` đã là role được tin), patch version ít khả năng đổi hành vi parse |
| `charset-normalizer`·`phonenumbers`·`python-dotenv` | tiện ích chung | chưa thấy đường chạm PII/thẩm quyền trực tiếp | **THẤP**, không đáng phân tích riêng |

**PHÁN QUYẾT: ĐỒNG Ý VỚI LEAD — KHÔNG CHẶN MERGE.** Nhưng không phải vì "trôi không đáng ngại nói
chung" — vì **đã soi CỤ THỂ gói duy nhất chạm một gate bảo mật đặt tên** (`langsmith`) và gate đó có
**lớp phòng thủ độc lập với version** (biến môi trường, không phải hành vi nội bộ thư viện). Không
có gói nào trong 6 gói tạo ra một đường RÒ MỚI hôm nay — đây là kết luận có kiểm, không phải suy diễn
từ "diff rỗng" như lần trước.

**Đề nghị sổ nợ — GỘP với đề nghị base-image-digest ở mục trên, đúng như Lead gợi ý ("cùng một lỗ"):**
1. **Nối `requirements.lock.txt` vào `Dockerfile`** (`pip install -r requirements.lock.txt`, không
   phải `requirements.txt`) — đây là việc chính, đóng TOÀN BỘ lớp trôi transitive một lần.
2. **Nếu (1) chưa làm ngay, ghim RIÊNG `langsmith==` trong `requirements.txt`** — không phải vì bản
   thân gói này nguy hiểm, mà vì nó là gói DUY NHẤT trong 6 gói đứng sau một dòng comment bảo mật có
   tên (F-30) — cùng lý do dự án đã ghim `langchain-core==1.5.4` sau khi đo lệch mô tả tool. Việc rẻ,
   không gấp, nhưng đáng ưu tiên hơn 5 gói còn lại nếu chỉ chọn ghim một cái trước.

Không đổi CHỮ KÝ Finding A/B ở trên — hai finding đó đứng độc lập với toàn bộ phát hiện này.
