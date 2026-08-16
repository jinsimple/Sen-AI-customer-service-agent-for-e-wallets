# Đo cho xuất-xứ-nguồn RAG — số trước, đề xuất sau

> Vai: **security** · 2026-08-16 · PO duyệt làm đề tài probe, theo trình tự tôi
> tự đặt: **đo trước, đề xuất sau**. Đây là phần ĐO. Đề xuất ở §5, và nó **chưa
> phải ADR** — ADR cần `contracts/rag-nguon.yaml` + chuỗi xfail của tester
> (`55118b5`).
> Ca dương tính làm căn cứ: hồ sơ sự cố `10af46d`.

## 1. Trường hiện có — xuất xứ đã có MỘT NỬA, ở tầng tài liệu

```
PolicyDocument : doc_id · filename · uploaded_by · uploaded_at · status
                 chunk_count · error_message
PolicyChunk    : chunk_id · doc_id · chunk_index · text(EncryptedText) · created_at
```

`uploaded_by` cho biết **AI** nạp, **không** cho biết **QUA ĐƯỜNG NÀO**. Đó
đúng là chỗ hụt của sự cố vừa rồi: `kho_rag.py:245` **hardcode**
`uploaded_by="USR-PA01"` — trùng y hệt giá trị của một lượt upload thật qua
API, nên `uploaded_by` **không phân biệt được script nội bộ với đối tác thật**.

⟹ Thứ còn thiếu không phải "ai", mà là **"qua cửa nào"**.

## 2. Mọi call-site của `ingest_document` — có ba, không phải hai

| # | Nơi gọi | Cửa | Ghi chú |
|---|---|---|---|
| 1 | `src/api/main.py:1195` | **API upload**, gated `require_role("partner_admin")` | **cửa hợp lệ — và là cửa đã dùng trong sự cố** |
| 2 | `scripts/kho_rag.py:244` | script vận hành, in-process | không qua HTTP |
| 3 | `eval/run_adversarial_set.py:57` | **eval, cố ý đầu độc kho** | xem §4 |
| — | `tests/test_rag/test_ingest.py` ×4 | test | |

⚠️ **Ghi lại một điểm mù của chính công cụ tôi:** `grep "ingest_document("`
**bỏ sót call-site số 1**, vì route API truyền hàm **như tham chiếu** vào
`_handle_tool_error(ingest_document, ...)` chứ không gọi trực tiếp. Tôi chỉ tìm
ra khi truy ngược từ endpoint. Cùng họ bài học **C4** (grep-tên sai cả hai
chiều) — và lần này nó suýt làm tôi viết đặc tả **thiếu đúng cửa quan trọng
nhất**.

## 3. Chi phí — rẻ hơn nhiều so với dự đoán, vì kiến trúc đã thuận

**Backfill: 2 dòng, không phải 378.**

```
policy_documents:   2
policy_chunks:    378
```

Cờ đặt ở **`PolicyDocument`** (không phải `PolicyChunk`): chunk đã FK về doc,
nên cờ ở tầng doc là **đủ** và backfill chỉ **2 dòng**. Đặt ở tầng chunk sẽ
tốn 378 dòng mà không thêm sức phân biệt nào.

**Tầng serve: một mệnh đề, không đụng Chroma, không nhúng lại.**

`search_policy_text` (`src/rag/search.py`) vốn đã chạy **hai bước**:

```
Chroma  ->  chunk_id theo độ tương đồng
SQL     ->  select(PolicyChunk).where(chunk_id.in_(...))  + join PolicyDocument
```

Vòng lặp ghép kết quả **đã** tra `docs_by_id` cho mỗi chunk. ⟹ chỗ lọc là
**một mệnh đề thêm vào truy vấn SQL đã có**. **Không cần metadata trong Chroma,
không cần nhúng lại 378 chunk.**

Và code **đã có sẵn khuôn bỏ-qua-chunk**:

```python
if chunk is None:
    continue   # tài liệu vừa bị xoá, index chưa kịp đồng bộ
```

Bỏ chunk chưa-duyệt đi theo **đúng khuôn đã tồn tại và đã chạy**, không phải
nhánh mới.

**Chi phí recall = 0 ở vận hành bình thường.** Lọc chạy **sau** khi Chroma trả
k kết quả, nên về lý thuyết nó có thể cắt k xuống. Nhưng khi **mọi** tài liệu
đều đã duyệt thì nó **không bỏ gì**; nó chỉ cắt khi trong index **có** tài liệu
chưa duyệt — tức đúng ca sự cố, và ở đó **cắt là hành vi mong muốn**.

## 4. ⚠️ Điểm phải quyết trước khi code: đường EVAL

`eval/run_adversarial_set.py:57` nạp tài liệu độc **có chủ đích** để chạy bộ
đối kháng. Nếu cờ xuất xứ chặn nó thì bộ đối kháng **mất khả năng test**.

**Đề nghị của tôi: eval đánh dấu tài liệu của nó là ĐÃ DUYỆT (`upload_api`),
KHÔNG phải một hạng riêng.** Lý do — và đây là chỗ dễ hiểu sai nhất của cả
thiết kế:

> **Mô hình đe doạ của bộ đối kháng là "đối tác upload tài liệu độc/bị chiếm".**
> Trong kịch bản đó tài liệu **ĐÚNG LÀ đã qua cửa duyệt**. Nếu eval đánh dấu nó
> "chưa duyệt" thì bộ đối kháng **không còn test đúng mối đe doạ nó sinh ra để
> test** — nó chuyển sang test một ca dễ hơn.

⟹ **Không làm đường vòng (bypass) trong mã sản phẩm cho eval.** Mọi cờ dạng
"bỏ qua lọc khi đang test" đều là một công tắc có thể bị bật nhầm ở production
— đúng lớp lỗi F-30 (`LANGCHAIN_TRACING_V2` bật bằng một biến môi trường,
không để lại vết trong git).

## 5. 🔴 Nói rõ giới hạn: xuất-xứ KHÔNG thay thế bộ lọc tier

Hai thứ này chống **hai mối đe doạ khác nhau**, và gộp chúng là hiểu sai:

| | Chống cái gì | Không chống cái gì |
|---|---|---|
| **Xuất-xứ nguồn** | tài liệu vào kho **qua cửa không được duyệt** (tai nạn `.md`, script nội bộ, eval) | tài liệu **đã duyệt** nhưng **nội dung độc** |
| **Lọc tier + spotlighting** | nội dung độc **bên trong** tài liệu, bất kể nguồn | tài liệu vào kho sai cửa |

Sự cố vừa rồi là **ô thứ nhất**: nạp qua cửa **hợp lệ** (API `partner_admin`)
— nên ⚠️ **xuất-xứ-nguồn như tôi đề xuất sẽ KHÔNG chặn được chính sự cố này**
nếu cờ chỉ ghi "qua API hay không". Muốn chặn được nó, cờ phải mang nghĩa
**"tài liệu này nằm trong danh mục chính sách được duyệt phục vụ"** — tức một
bước **duyệt có chủ ý**, không phải một thuộc tính suy ra từ đường nạp.

**Đây là điểm quan trọng nhất của cả phép đo này, và nó đi ngược đề xuất ban
đầu của chính tôi:** tôi từng viết *"cờ nguồn-đã-duyệt ở tầng serve mới phân
biệt được tài liệu đối tác đã duyệt với file ai đó lỡ upload"* — nhưng file
`.md` lần này **cũng đi qua đúng cửa đó**. Ghi đường-nạp là **không đủ**; phải
là **trạng thái duyệt** tách khỏi hành vi nạp.

## 5b. ⚠️ VA CHẠM TÊN `nguon` — báo trước khi ADR đóng nó lại

F-LOG-3 vừa land vào `search.py` đã dùng tên **`nguon`** cho một nghĩa **khác
hẳn** nghĩa tôi đang đề xuất:

| Nơi | `nguon` nghĩa là | Trục |
|---|---|---|
| `search_policy_text(nguon=...)` (**đã land**) | **ai đang TRA** — `"agent"` (có lọc tier) vs `"cskh"` (Y5, không lọc) | đường **ĐỌC** |
| Đề xuất xuất-xứ (§5) | **tài liệu vào kho QUA CỬA NÀO / đã duyệt chưa** | đường **GHI** |

Hai trục **trực giao**: một tài liệu chưa-duyệt có thể được tra bởi **cả** agent
lẫn CSKH. Dùng chung một tên sẽ làm mọi câu truy vấn log về sau mơ hồ, và tệ
hơn — người đọc sau sẽ tưởng lọc-theo-nguồn đã tồn tại.

**Đề nghị đổi tên trước khi ADR chốt** (rẻ nhất là bây giờ, chỉ một trường log
vừa land):
- đường ĐỌC → `duong_tra` (`agent` | `cskh`)
- đường GHI → `nguon_nap` (`upload_api` | `script` | `eval`) và **`trang_thai_duyet`**
  (xem §5: hai thứ này **phải tách**, vì file `.md` lần rồi vào **đúng cửa hợp
  lệ** — ghi đường nạp không đủ để chặn nó)

Ghi nhận: đây là **hệ quả của chính lời dặn của tôi** với coder (*"đặt tên
`nguon`, đừng đặt tên khác kẻo sau phải đổi"*) — tôi dặn khi mới có **một**
nghĩa trong đầu, không lường trục thứ hai. Lỗi ở tôi, sửa lúc còn rẻ.

## 6. Ba câu cần PO/ADR quyết (tôi không tự quyết)

1. **Ai duyệt, và lúc nào?** Nạp xong ở trạng thái `cho_duyet` rồi cần một
   thao tác duyệt riêng? Hay `partner_admin` upload là mặc định duyệt, và cái
   ta chặn chỉ là script/eval? — **Phương án 1 chặn được sự cố vừa rồi, phương
   án 2 thì không.**
2. **Kho hiện tại**: 2 tài liệu backfill thành `da_duyet`, hay bắt duyệt lại?
3. **Ai thấy tài liệu chưa duyệt?** Đề nghị: `partner_admin` thấy (để duyệt) ·
   agent **không** · `/policy-search` của CSKH — cần quyết, vì Y5 nói CSKH
   **phải** thấy nguyên văn để phát hiện tài liệu độc.

## 7. Điều tôi CHƯA đo

- **Chưa đo `store.py`/Chroma** có giữ metadata gì — không cần cho đề xuất
  hiện tại (lọc ở SQL), nhưng nếu ai muốn lọc **trong** truy vấn vector (để
  không mất k) thì phải đo tiếp.
- **Chưa chạy** thử mệnh đề lọc — đây là đo **thiết kế + chi phí**, chưa có
  bản vá để probe.
- Chưa đọc chuỗi xfail của tester (`55118b5`) — sẽ đối chiếu khi soạn ADR.
