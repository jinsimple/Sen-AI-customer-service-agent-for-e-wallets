# Finding — Upload chính sách RAG (`partner_admin`) không kiểm duyệt NỘI DUNG, chỉ kiểm ĐỊNH DẠNG

> Vai: `security`. Giao từ Lead (`p-226-92`), tách riêng khỏi Finding ① (chất lượng lọc khoảng cách
> RAG) — đây là lỗ hổng CƠ CHẾ liền kề, không phải cùng một finding. Không điều tra "ai đã nạp" —
> PO thật đang tự làm việc đó riêng. Phạm vi ở đây: đánh giá cơ chế, không truy người.
>
> **Đề nghị placement:** file này ghi vào `docs/security/` (đúng vùng ghi của `security` theo
> `CLAUDE.md §4`). `docs/giao-viec/2026-09-03-vá-finding-1-rag-policy.md` thuộc vùng `po` (mọi thứ
> dưới `docs/` ngoài `docs/security/` là vùng PO/Lead) — tôi không tự ghi vào đó. Lead/PO có thể dán
> nguyên nội dung dưới đây hoặc trỏ đường dẫn vào brief của mình, tuỳ cách hai bên đang tổ chức
> `docs/giao-viec/`.

## Bằng chứng — tự xác nhận độc lập, không chỉ tin lại claim của Lead

**[ĐO 03/09, `psql` trực tiếp trên `fin05-po-demo-postgres-1`]**

```
doc_id            filename                   uploaded_by  uploaded_at                  status    chunk_count
DOC-4c804ba019b1  MoMo_FAQ_Giao_dich.docx    USR-PA01     2026-09-01 13:59:41.864325   indexed   297
DOC-aaf60f95611b  MoMo_ToS.docx              USR-PA01     2026-09-01 13:59:55.337755   indexed   81
DOC-606240c112f8  STATE.md                   USR-PA01     2026-09-01 16:48:29.825166   indexed   400
```

Khớp đúng claim của Lead: 3 tài liệu, dòng thứ 3 là `STATE.md` — tài liệu bàn giao NỘI BỘ ĐỘI, nạp
qua route upload thật **sau** lần nạp kho chính thức (13:59, 2 tài liệu MoMo) gần 3 tiếng. **400
chunk** — không phải một vài dòng lọt qua, mà phần lớn nội dung `STATE.md` (nhật ký sự cố, thảo luận
key/OTP, mốc neo Docker, tên phiên nội bộ…) giờ nằm trong index vector, `status='indexed'` — trạng
thái duy nhất nghĩa là **đã LIVE, agent trích dẫn được ngay**, không có bước trung gian nào.

## Vị trí cơ chế

- Route: `POST /policy-docs` (`src/api/main.py:1380-1403`) — `require_role("partner_admin")`,
  `@limiter.limit("20/hour")`, gọi thẳng `ingest_document()`.
- Hàm xử lý: `ingest_document()` (`src/rag/ingest.py:28-113`).
- Index: `store.add_chunks()` (`src/rag/store.py:233-247`).
- Đọc lại: `search()` (`src/rag/search.py`) — hai đường dùng chung: `duong_tra="agent"` (qua tool
  `search_policy`, CÓ lọc tier ở `_sanitize_policy_results` — nhưng đó là phòng thủ **prompt
  injection**, hạ tài liệu về hạng DỮ LIỆU, KHÔNG phải kiểm tra nội dung có đúng là chính sách ví hay
  không) và `duong_tra="cskh"` (`POST /policy-search`, **CỐ Ý không lọc gì cả** — quyết định Y5, có
  ghi chú riêng trong code). ⟹ Với đường CSKH, nội dung `STATE.md` trả về **nguyên văn, không qua bất
  kỳ lớp nào**.

## Đối chiếu ĐANG CÓ vs ĐANG THIẾU — để không đánh giá quá tay

**Đang CÓ (đáng ghi nhận, không phải hệ thống hoàn toàn hở):**
- Kiểm magic bytes thật trước khi parse (`src/rag/parsers.py`), chặn giả đuôi file.
- Giới hạn định dạng: chỉ `.md/.txt/.pdf/.docx`, cố ý không hỗ trợ `.doc` (không có parser an toàn).
- Giới hạn kích thước: `MAX_UPLOAD_SIZE_MB = 10` (`src/config.py:520`).
- Rate limit `20/hour` trên chính route upload.
- Role gate chặt: chỉ `partner_admin`, tách khỏi `supervisor`/`cskh` (comment tự khai đây là "actor
  duy nhất được đưa tài liệu mới vào hệ thống mà agent/CSKH sẽ tin tưởng").
- Audit log đầy đủ: `policy_doc_nap` ghi `doc_id`/`uploaded_by`/`chunk_count`/`nguon_nap` — đây chính
  là cơ chế cho phép Lead/PO TÌM RA sự việc này chỉ bằng đọc log/DB, không phải suy đoán.

**Đang THIẾU (lỗ hổng thật, đúng như Lead nêu):**
1. **Không kiểm duyệt NỘI DUNG ở bất kỳ tầng nào.** `ingest_document()` chỉ kiểm: file không rỗng,
   ≤ 10MB, extract được text, tách được ≥1 đoạn. Không có bất kỳ bước nào hỏi "nội dung này có PHẢI
   là chính sách/FAQ ví điện tử không".
2. **Không có trạng thái "chờ duyệt".** `ck_policy_documents_status` (`src/db/models.py:557-559`)
   CHỈ cho phép `processing`/`indexed`/`failed` — về mặt SCHEMA, không tồn tại khái niệm
   `pending_review`/`draft`/`published`. Đây không phải "có nhưng không dùng" — nó **không có chỗ để
   thêm vào** nếu không sửa CHECK constraint. Upload thành công ⟹ LIVE ngay lập tức, không ai xem lại
   trước khi khách/CSKH có thể chạm tới nội dung đó.
3. **Không có phát hiện bất thường.** Không cảnh báo khi: nạp ngoài giờ hành chính, nạp tài liệu có
   tên/định dạng khác hẳn 2 tài liệu MoMo hiện có (`MoMo_FAQ_Giao_dich.docx`/`MoMo_ToS.docx` →
   `STATE.md`, đổi cả đuôi file lẫn "họ tên" tài liệu), hay nạp với số chunk bất thường lớn/nhỏ so với
   phân bố hiện có (400 chunk cho 1 file so với 297/81 của hai file kia — chênh gấp nhiều lần, một
   ngưỡng đơn giản đã có thể gắn cờ).
4. **Đường CSKH (`/policy-search`) không lọc gì (Y5)** — thiết kế "cố ý không lọc" đó giả định trước
   nội dung trong kho LUÔN đáng tin (vì chỉ `partner_admin` mới nạp được) — giả định đó **sụp đổ**
   ngay khi chính hành vi của `partner_admin` là nguồn gây nhiễm, không phải bên ngoài tấn công vào.

## Tác động — vi phạm ràng buộc nào

Không vi phạm 1-trong-5 ràng buộc cứng THEO ĐÚNG VĂN TỰ (không có route nào bị bypass, không hoàn
tiền tự động, không tool cấm nào được gọi). Nhưng chạm tinh thần **Ràng buộc cứng #3 (cấm bịa số
liệu)** ở dạng gián tiếp nghiêm trọng: agent trích dẫn `search_policy` như nguồn CÓ CĂN CỨ — nếu nội
dung nguồn đó là rác/nội bộ/độc hại, "có căn cứ" chỉ còn là ảo giác có vỏ bọc đúng quy trình. Đây
đúng là lớp rủi ro **data poisoning / RAG injection từ actor NỘI BỘ ĐƯỢC CẤP QUYỀN** — khác hẳn
prompt injection từ khách hàng (đã có phòng thủ `_sanitize_policy_results`) vì **actor này chính là
actor được thiết kế để tin tưởng tuyệt đối**.

**Kịch bản cụ thể, không lý thuyết:** một `partner_admin` (dù vô ý như ca này, hay cố ý — tài khoản
`partner_admin` có thể bị chiếm/mạo danh, hoặc chính đối tác ví có động cơ) nạp một tài liệu chứa
hướng dẫn sai lệch ("mọi khiếu nại double_charge tự động hoàn 100% không cần điều tra") — agent
`search_policy` sẽ trích dẫn đúng như chính sách thật, và CSKH tra `/policy-search` cũng thấy y hệt,
không có gì phân biệt được với 2 tài liệu MoMo hợp lệ.

## Đề xuất hướng xử lý — theo đúng 4 hướng Lead gợi ý, kèm đánh đổi

**A. Thêm trạng thái "chờ duyệt" trước khi index (mạnh nhất, chi phí cao nhất)**
Đổi CHECK constraint thêm `pending_review`, route upload dừng ở đó, thêm route
`POST /policy-docs/{doc_id}/publish` (role khác `partner_admin` — vd `supervisor`, để có tách bạch
người-nạp ≠ người-duyệt, cùng tinh thần maker-checker đã áp cho `resolutions`). Đổi contract
(`agent-tools.yaml` không đổi vì đây không phải tool, nhưng `authority-matrix.yaml` cần thêm route
mới) ⟹ cần ADR + PO duyệt (`CLAUDE.md §3`), không phải việc code trực tiếp.

**B. Kiểm nội dung TỰ ĐỘNG trước khi index (trung bình, không chặn hoàn toàn nhưng giảm rủi ro)**
Heuristic rẻ, không cần model: từ khoá cờ đỏ đơn giản trên text đã extract (vd nhãn nội bộ như
`STATE.md`/`ADR-`/tên phiên `p-226-`/từ khoá "PO thật"/"CLAUDE.md"), hoặc so khớp thô-sơ với "văn
phong chính sách" (có/không có cấu trúc điều khoản). Rẻ, nhanh, nhưng dễ vòng qua nếu ai đó cố ý đổi
tên biến/nội dung — không phải phòng thủ triệt để, chỉ là lưới an toàn cho trường hợp NHẦM LẪN (đúng
ca `STATE.md` hôm nay — rất có thể là gõ nhầm tên file, không phải tấn công).

**C. Cảnh báo/log khi nạp bất thường (rẻ nhất, không chặn gì, chỉ tăng khả năng phát hiện SỚM)**
Mở rộng `policy_doc_nap` (đã có, chỉ cần thêm điều kiện cảnh báo): so `chunk_count` với phân bố hiện
có (vd > 2x median) → log mức `warning` thay vì `info`; so tên file với whitelist/pattern các tài
liệu MoMo đã biết → cảnh báo nếu lệch. Không chặn upload, chỉ giúp Lead/PO/security **thấy sớm hơn**
— ca hôm nay bị phát hiện ~2 ngày sau khi nạp (16:48 01/09 → phát hiện 03/09), một cảnh báo real-time
sẽ rút ngắn cửa sổ đó xuống gần 0.

**D. Giới hạn định dạng/nguồn chặt hơn** — đã tương đối chặt (chỉ 4 định dạng, role riêng), không
phải chỗ hở chính của ca này (STATE.md LÀ định dạng `.md` hợp lệ, không lách qua khe hở định dạng nào
— nó lách qua khe hở THIẾU KIỂM NỘI DUNG, không phải khe hở định dạng). Không ưu tiên hướng này.

**Khuyến nghị thứ tự:** C trước (rẻ, làm ngay, không cần ADR vì chỉ thêm log/cảnh báo — thuộc
`tech-lead`) → B sau (cần PO xác nhận danh sách từ khoá cờ đỏ, nhưng vẫn không cần đổi contract/schema)
→ A là hướng ĐÚNG lâu dài nhưng tốn nhất (đổi schema + route mới + ADR), nên xếp sau khi có C/B làm
lưới an toàn tạm thời. Không tự chọn thay PO — đây là quyết định đánh đổi tốc độ vận hành (đối tác ví
cần nạp tài liệu nhanh) và mức độ tin tưởng vào actor `partner_admin`, thuộc phạm vi PO quyết.

## 🔴 ĐÍNH CHÍNH 04/09 (sau) — "đã xác minh thật" ở mục ngay dưới đây CHƯA ĐỦ, đừng trích như đã đóng

Ba phép đo dưới đây gọi THẲNG `search_policy_text()` bằng Python — **KHÔNG đi qua route HTTP
`/policy-search` hay tool agent đầy đủ**. QA chạy E2E qua UI thật (đường đủ, qua route) bắt được
**HTTP 500 body rỗng 2 lần** ngay sau khi Finding ① land. Review độc lập (không phải tôi) tìm ra gốc
khả dĩ: `src/rag/rerank.py:65-78` — phần PARSE response (`data.get("ket_qua", [])`,
`item["chunk_id"]`, `float(item["score"])`) nằm **NGOÀI** khối `try/except` (chỉ bọc dòng 46-53: gọi
HTTP + `resp.json()`). Nếu sidecar trả HTTP 200 nhưng JSON sai lược đồ (thiếu `chunk_id`/`score` ở
một phần tử, hoặc `score` không parse được thành float) ⟹ `KeyError`/`ValueError` KHÔNG bị bắt ⟹
lan lên tới route ⟹ **đúng như "RÀNG BUỘC BẤT DI" module tự đặt ra ("sidecar lỗi KHÔNG ĐƯỢC làm
`search_policy_text` crash") lại chính bị VI PHẠM bởi module đó, ở một nhánh lỗi hẹp mà phép đo tay
gọi thẳng hàm của tôi không chạm tới** (sidecar trả lời đúng lược đồ trong 3 lần tôi gọi, nên không
lộ ra). Tôi tự đọc lại code, xác nhận ĐÚNG cấu trúc try/except như Review mô tả — không phải suy diễn
lại lời Lead. Chờ Coder xác nhận traceback thật trước khi coi đây là nguyên nhân CHẮC CHẮN. Sau khi
vá, sẽ đo lại đúng 3 câu (rác/near-miss/khớp thật) qua ĐÚNG route CSKH thật để khép vòng.

## Cập nhật 04/09 — dependency bucket STATE.md ĐÓNG (dữ liệu đã xoá), tự kiểm chứng Lớp 1+2 sống thật

`STATE.md` đã bị xoá khỏi kho `po-demo` đêm 03/09 — **tự xác nhận `psql`**: `policy_documents` chỉ
còn 2 dòng (2 tài liệu MoMo gốc). **Tự xác nhận thêm bước Lead không nhắc tới:** kiểm luôn Chroma
(không chỉ Postgres) — `col.get(where={"doc_id": "DOC-606240c112f8"})` → **0 chunk sót**, tổng
`col.count()` = 378 = đúng 297+81 (2 tài liệu còn lại) → xoá qua đúng đường `store.delete_document`,
không phải xoá tay ở tầng DB để lại rác vector.

⟹ Bucket "dò `STATE.md` không-scope" không còn dữ liệu để đo — dependency định lượng C→A mô tả bên
dưới coi như ĐÓNG theo cách khác (rủi ro tức thời hết, không phải vì có số đo). Quyết định C-vs-A cho
hướng vá LÂU DÀI vẫn treo, dựa trên đánh giá rủi ro chung, không phải một con số bucket cụ thể.

**Tự kiểm chứng thêm (không chỉ tin lời "đã land"):** gọi thẳng `search_policy_text()` trên
`po-demo` thật với 3 câu:
```
RÁC ("công thức nấu phở bò")                              → not_found, 0 kết quả
NEAR-MISS ("phí liên ngân hàng" — ĐÚNG câu ADR-061 tự khai từng THẤT BẠI ở
           ngưỡng embedding đơn, distance 0.9697/0.9059)  → not_found, 0 kết quả  ✅ giờ ĐÚNG
KHỚP THẬT ("làm sao liên kết ngân hàng với ví MoMo")       → found, 4 kết quả
```
Đúng câu near-miss mà thiết kế cũ (ngưỡng embedding đơn) thất bại nay bị cross-encoder chặn đúng,
trong khi câu khớp thật vẫn qua — bằng chứng SỐNG, không phải đọc code suy luận. Kiến trúc sidecar
(`src/rag/rerank.py`) fail-closed đúng thiết kế: sidecar lỗi/timeout → `results=[]` →
`status=not_found`, không bao giờ rơi về "trả kết quả chưa lọc" — khớp đúng Ràng buộc cứng #3.

---

## Lịch sử — liên kết với ADR-061 (vá Finding ①): điều kiện định lượng cho quyết định C→A (03/09, một phần đã đóng — xem cập nhật 04/09 trên)

> PO đã chọn làm trước hướng C (`docs/security/2026-09-03-spec-canh-bao-upload-rag-bat-thuong.md`) —
> chỉ log+cảnh báo, KHÔNG chặn upload. ADR-061 (vá Finding ① — chất lượng lọc RAG, quyết 03/09) chọn
> thiết kế 2 lớp (lọc `scope` mức chunk + cổng abstention cross-encoder), và **tự khai** (Hệ quả #4,
> #5 của ADR đó): tài liệu mới nạp mặc định `scope='unknown'`, và `scope='unknown'` luôn **trực giao
> qua Lớp 1** (không lọc được). Ghép hai sự thật này lại:

**Cross-encoder (Lớp 2 của ADR-061) là tuyến phòng thủ DUY NHẤT** cho đúng kịch bản finding này —
một tài liệu nội bộ/độc hại bị `partner_admin` nạp nhầm/cố ý sẽ mang `scope=unknown`, hướng C không
chặn nó (chỉ cảnh báo qua log), Lớp 1 của ADR-061 không lọc được nó (trực giao) ⟹ **chỉ còn cross-
encoder đứng giữa nội dung đó và khách/CSKH.**

**Trigger định lượng cho quyết định C→A** (PO ghi nhận 03/09, đăng ký cách đọc số trước khi Coder có
kết quả — không phải cảm tính sau khi thấy số): Kế hoạch đo của ADR-061 đã có sẵn bucket **"dò nội
dung `STATE.md` KHÔNG kèm `complaint.scope`"** (mô phỏng đúng đường AGENT tự gọi `search_policy`,
đường nguy hiểm nhất vì không truyền scope). Khi Coder đo xong bucket này:

- **Abstain-đúng CAO** (cross-encoder chặn được phần lớn/hầu hết truy vấn dò nội dung nội bộ) ⟹
  hướng C (chỉ log+cảnh báo, không chặn upload) **đủ tạm**, Lớp 2 gánh được vai trò tuyến cuối.
- **Abstain-đúng THẤP** ⟹ đây là **bằng chứng cụ thể, đo được** (không phải suy luận lý thuyết như
  finding gốc) để PO thật cân nhắc nâng ưu tiên hướng A (trạng thái "chờ duyệt" trước khi index —
  mục A trong "Đề xuất hướng xử lý" ở trên, cần ADR riêng vì đổi schema/route).

Không tự đặt ngưỡng số cụ thể "cao/thấp" ở đây — đó là việc của người đo (Coder/QA-QC) đối chiếu với
tiêu chí "tỉ lệ abstain SAI trên câu THẬT" mà ADR-061 đã yêu cầu đo song song (tránh lặp lỗi "từ chối
quá tay" đã ghi nhận ở nơi khác của hệ thống) — hai con số phải đọc CÙNG NHAU, không đọc bucket này
riêng lẻ.

## Chưa kiểm được

- Nội dung `STATE.md` cụ thể đã hiển thị cho khách/CSKH nào qua `search_policy`/`policy-search` hay
  chưa — cần đọc log truy vấn RAG trong khung 01-03/09, ngoài phạm vi "chỉ đánh giá cơ chế" được giao.
- Liệu 2 tài liệu MoMo còn lại (`MoMo_FAQ_Giao_dich.docx`, `MoMo_ToS.docx`) có được xác minh nội dung
  đúng chuẩn khi nạp lúc 13:59 hay không — giả định là hợp lệ vì tên khớp đối tác thật, chưa tự đọc
  nội dung để xác nhận.
