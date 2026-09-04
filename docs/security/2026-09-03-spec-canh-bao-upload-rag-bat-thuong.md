# SPEC — Hướng C: log + cảnh báo khi upload chính sách RAG bất thường

> Vai: `security`. PO chọn làm trước hướng C trong 4 hướng đã đề xuất ở
> `docs/security/2026-09-03-finding-rag-upload-khong-kiem-duyet-noi-dung.md` — rẻ nhất, không cần
> ADR (không đổi schema/contract, chỉ mở rộng log đã có). Đây là SPEC, chưa code — đủ chi tiết để
> `tech-lead` áp thẳng. Đọc trước: finding gốc (đường link trên) để biết bối cảnh ca `STATE.md`
> 400-chunk đã lọt qua như thế nào.

## 0. Nguyên tắc thiết kế — vì sao chọn ngưỡng thế này

Kho hiện tại **chỉ có 3 tài liệu** — quá ít để suy luận thống kê "chắc chắn" (percentile/z-score cần
mẫu lớn hơn nhiều). Mọi ngưỡng số dưới đây là **KHỞI ĐIỂM ĐỀ XUẤT dựa trên suy luận hợp lý, KHÔNG PHẢI
số đã đo/hiệu chuẩn trên dữ liệu thật** — khác hẳn cách dự án thường làm (đo trước, chọn ngưỡng sau).
Ở quy mô 3 tài liệu, đo trước là bất khả thi; đề xuất ở đây ưu tiên **thà cảnh báo thừa (false
positive) còn hơn im lặng bỏ sót** — đúng tinh thần Ràng buộc cứng #3, và đúng cách dự án đã chấp
nhận đánh đổi tương tự cho PII scrubbing. `tech-lead`/PO cần tự chỉnh ngưỡng khi kho lớn hơn (ghi rõ
"CẦN HIỆU CHỈNH LẠI KHI KHO > 10 TÀI LIỆU" tại từng mục).

**Không đổi CHECK constraint, không đổi contract, không route mới ở phiên bản này** — chỉ mở rộng sự
kiện log `policy_doc_nap` đã tồn tại (`src/rag/ingest.py:91-112`) và (tuỳ chọn, xem mục 4) thêm field
tính-lúc-đọc vào response `GET /policy-docs` đã có sẵn.

## 1. Bốn tín hiệu cảnh báo — mỗi tín hiệu độc lập, không cái nào chặn upload

Tất cả tín hiệu chỉ **cảnh báo (log mức `warning`)**, KHÔNG chặn upload — chặn cứng thuộc hướng A
(trạng thái "chờ duyệt"), ngoài phạm vi bản spec này.

### Tín hiệu 1 — Kích thước lệch xa phân bố hiện có (mạnh, ít false positive)

```
Điều kiện kích hoạt: có ≥ 2 tài liệu status='indexed' đã tồn tại TRƯỚC lượt upload này, VÀ
  chunk_count(tài liệu mới) > 2.0 × TRUNG_BÌNH(chunk_count của các tài liệu 'indexed' hiện có)
```
- Ca `STATE.md`: trung bình 2 tài liệu MoMo = (297+81)/2 = 189. `400 > 2.0×189=378`? **400 < 378 →
  KHÔNG kích hoạt ở ngưỡng 2.0x.** Đo lại: `400/189 ≈ 2.12x` — vậy ngưỡng **2.0x đúng là bắt được ca
  này**, sát nút. Đề xuất giữ `2.0x`, không nới lên `3x` (nới thêm sẽ bỏ lọt chính ca đã xảy ra thật).
- Bỏ qua tín hiệu này khi kho có **< 2** tài liệu hiện có trước đó (không đủ để so sánh — tài liệu
  đầu tiên hoặc thứ hai luôn qua, đúng logic).
- 🔴 **CẦN HIỆU CHỈNH LẠI KHI KHO > 10 TÀI LIỆU** — trung bình cộng nhạy với outlier khi mẫu nhỏ;
  ở quy mô lớn hơn nên đổi sang median hoặc IQR.

### Tín hiệu 2 — Từ khoá nội bộ dự án xuất hiện trong nội dung đã trích xuất (mạnh nhất, gần như chắc chắn đúng khi khớp)

Sau bước `extract_text()` (`src/rag/ingest.py:56`, đã có văn bản thô trước khi chia đoạn), quét
substring (không phân biệt hoa/thường, không cần NLP) danh sách khởi điểm:

```
"CLAUDE.md", "docs/security", "docs/STATE", "STATE.md", "DECISIONS.md", "ADR-0", "ADR-1",
"contracts/authority-matrix", "contracts/agent-tools", "contracts/resolution-state-machine",
"tests/test_invariants", "p-226-", "PO thật", "OTP_DEMO_MODE", "QWEN_API_KEY", "OPENAI_API_KEY",
"docs/giao-viec", "project-knowledge/"
```
- Ca `STATE.md`: chứa `"CLAUDE.md"`, `"docs/STATE"`(tên chính nó), `"ADR-0"`, `"p-226-"` nhiều lần —
  khớp ngay ở lần quét đầu tiên, đây là tín hiệu ĐÁNG TIN CẬY NHẤT trong 4 tín hiệu vì false positive
  gần như 0 (không có lý do gì một tài liệu chính sách MoMo hợp lệ chứa các cụm từ này).
- Danh sách trên là **khởi điểm do tôi đề xuất, PO/tech-lead cần rà lại và bổ sung** — đặc biệt các
  cụm nhạy cảm khác có thể xuất hiện trong tài liệu nội bộ (tên miền nội bộ, biệt danh nhân sự...).
  Không đưa các cụm QUÁ NGẮN/QUÁ CHUNG (vd `"key"`, `"token"`) — sẽ khớp nhầm cả nội dung chính sách
  hợp lệ nói về bảo mật, gây nhiễu vô ích.
- Đây là tín hiệu DUY NHẤT trong 4 tín hiệu đủ mạnh để cân nhắc nâng lên mức cảnh báo cao hơn (xem
  mục 3) thay vì `warning` thường.

### Tín hiệu 3 — Tên file không khớp mẫu tài liệu đối tác đã biết (yếu, chỉ tham khảo)

```
Điều kiện: filename KHÔNG khớp regex đơn giản, vd r"^MoMo_.*\.(docx|pdf)$" (rút ra TỪ đúng 2 tài
liệu hợp lệ hiện có trong kho `po-demo` — CẦN PO xác nhận đây có phải quy ước đặt tên THẬT của đối
tác hay chỉ là trùng hợp ngẫu nhiên của 2 tài liệu demo).
```
- Ca `STATE.md`: không khớp `MoMo_*` → kích hoạt.
- 🔴 Tín hiệu YẾU NHẤT, dễ false positive cao nếu đối tác đổi cách đặt tên hợp lệ (vd thêm tài liệu
  `Dieu_khoan_2027.pdf`). **Không dùng làm căn cứ chặn dưới bất kỳ hình thức nào, kể cả tương lai** —
  chỉ ghi kèm để người đọc log có thêm ngữ cảnh, không phải điều kiện kích hoạt cảnh báo riêng.

### Tín hiệu 4 — Tần suất upload cao trong thời gian ngắn (trung bình)

```
Điều kiện: cùng uploaded_by có ≥ 5 lượt upload (bất kể thành công/thất bại) trong 60 phút gần nhất.
```
- Rate limiter hiện có (`@limiter.limit("20/hour")`, `main.py:1381`) là ngưỡng CHẶN CỨNG — đây là
  ngưỡng CẢNH BÁO SỚM HƠN nhiều (5 so với 20), để phát hiện hành vi bất thường TRƯỚC KHI chạm ngưỡng
  chặn, không phải thay thế nó.
- Ca `STATE.md`: chỉ 1 lượt trong khung giờ đó (13:59 → 16:48 cách nhau gần 3 tiếng) → **KHÔNG kích
  hoạt tín hiệu này**. Đúng — ca này không phải hành vi spam/dồn dập, tín hiệu 1+2 mới là thứ bắt
  được nó. Nêu ra để không ai hiểu lầm tín hiệu 4 là "đã đủ" — bốn tín hiệu bổ sung cho nhau, không
  cái nào một mình đủ.

## 2. Mở rộng sự kiện log — thay đổi cụ thể ở `src/rag/ingest.py`

Thêm bước tính `canh_bao: list[str]` **SAU KHI** `doc.chunk_count`/`doc.status` đã có giá trị cuối
(ngay trước khối `_logger.info("policy_doc_nap", ...)` hiện tại, dòng 91), rồi:

```python
canh_bao = _tinh_canh_bao_upload(session, doc, text, filename)  # hàm mới, xem mục 2b
_logger.log(
    logging.WARNING if canh_bao else logging.INFO,
    "policy_doc_nap",
    extra={
        # ... toàn bộ field cũ giữ nguyên (doc_id, ten_tep, uploaded_by, chunk_count, status, nguon_nap) ...
        "canh_bao": canh_bao,  # [] nếu không có gì bất thường — LUÔN có field này, không phải chỉ
                                 # khi có cảnh báo, để log rỗng cũng tra được bằng cùng một query field.
    },
)
```

**`canh_bao`** là **list các mã tín hiệu đã khớp**, vd `["kich_thuoc_lech", "tu_khoa_noi_bo"]` — không
phải boolean đơn — để người đọc log biết ĐÚNG lý do, không phải chỉ biết "có gì đó lạ".

### 2b. Hàm `_tinh_canh_bao_upload` — chữ ký đề xuất, không phải code hoàn chỉnh

```python
def _tinh_canh_bao_upload(
    session: Session, doc: PolicyDocument, text: str, filename: str
) -> list[str]:
    """Tính TRƯỚC khi log, KHÔNG chặn upload — mọi cảnh báo chỉ ghi log,
    không raise, không đổi doc.status."""
    canh_bao = []
    # Tín hiệu 1 — kích thước
    tai_lieu_cu = session.scalars(
        select(PolicyDocument.chunk_count)
        .where(PolicyDocument.status == "indexed", PolicyDocument.doc_id != doc.doc_id)
    ).all()
    if len(tai_lieu_cu) >= 2:
        trung_binh = sum(tai_lieu_cu) / len(tai_lieu_cu)
        if doc.chunk_count > 2.0 * trung_binh:
            canh_bao.append("kich_thuoc_lech")
    # Tín hiệu 2 — từ khoá nội bộ
    text_lower = text.lower()
    if any(tu.lower() in text_lower for tu in TU_KHOA_NOI_BO):
        canh_bao.append("tu_khoa_noi_bo")
    # Tín hiệu 3 — tên file (chỉ ghi kèm, KHÔNG cộng vào canh_bao độc lập —
    # xem mục 1.3, quá yếu để đứng một mình; đề xuất CHỈ đưa vào nếu tín hiệu
    # 1 hoặc 2 đã kích hoạt, làm ngữ cảnh bổ sung, không phải mã riêng)
    # Tín hiệu 4 — tần suất
    so_lan_gan_day = session.scalars(
        select(func.count(PolicyDocument.doc_id))
        .where(
            PolicyDocument.uploaded_by == doc.uploaded_by,
            PolicyDocument.uploaded_at >= dt.datetime.utcnow() - dt.timedelta(minutes=60),
        )
    ).scalar_one()
    if so_lan_gan_day >= 5:
        canh_bao.append("tan_suat_cao")
    return canh_bao
```

🔴 **`tech-lead` tự quyết vị trí đặt hàm** (cùng file `ingest.py` hay tách `src/rag/canh_bao.py`) —
đây chỉ là chữ ký/logic, không phải yêu cầu vị trí.

## 3. Không nâng cấp tín hiệu 2 lên mức chặn — dù mạnh nhất, vẫn chỉ cảnh báo ở SPEC này

Cân nhắc đã có: tín hiệu 2 (từ khoá nội bộ) gần như chắc chắn đúng khi khớp — có thể lập luận nên
CHẶN thẳng thay vì chỉ cảnh báo. **Cố ý KHÔNG làm vậy trong phạm vi hướng C** vì hai lý do: (a) chặn
= đổi hành vi route hiện có (trả lỗi thay vì `indexed`), đây là ranh giới giữa "chỉ log" (rẻ, không
ADR) và "đổi hành vi nghiệp vụ" (cần xem xét kỹ hơn, gần hướng A/B) — trộn lẫn sẽ làm spec này không
còn "rẻ nhất" nữa; (b) danh sách từ khoá là **suy luận, chưa hiệu chỉnh trên dữ liệu thật** — chặn
cứng dựa trên danh sách chưa kiểm chứng có rủi ro chặn nhầm tài liệu hợp lệ chứa trùng lặp ngẫu nhiên
một cụm từ (vd tài liệu chính sách MoMo vô tình nhắc "OTP" gần "token" theo cách trùng mẫu). Nếu PO
muốn nâng tín hiệu 2 lên mức chặn sau khi thấy log thật vài lượt, đó là bước 2 hợp lý — không làm
trong spec này.

## 4. Ai xem được cảnh báo — GAP cần nêu rõ, không tự quyết thay PO

**Hiện trạng sau khi áp spec này:** cảnh báo CHỈ tồn tại dưới dạng dòng log JSON mức `warning` ra
`stdout` (`src/observability/logging_config.py`) — không có kênh thông báo chủ động (không email,
không Slack, không route riêng). Người vận hành phải **chủ động đọc log** (`docker logs
<backend> | grep policy_doc_nap` hoặc tương đương) mới thấy — đúng quy mô 1-người hiện tại của dự án,
không đề xuất dựng hệ thống alerting phức tạp cho bước đầu này.

🔴 **Vấn đề tách bạch giám sát chưa giải quyết được trong phạm vi "chỉ log":** route DUY NHẤT đọc lại
danh sách tài liệu (`GET /policy-docs`) chỉ mở cho `partner_admin` (`authority-matrix.yaml`) — CHÍNH
actor có khả năng là nguồn rủi ro lại là người duy nhất (ngoài đọc log thô) nhìn thấy thông tin về
hành vi của mình. Hai hướng, PO chọn:

- **(a) Chấp nhận hiện trạng cho v1** — log là đủ, vì hệ thống hiện có 1 người vận hành thật (PO) đọc
  log thủ công/định kỳ, không cần route mới.
- **(b) Mở thêm quyền đọc `GET /policy-docs` cho `supervisor`** (route đã tồn tại, chỉ đổi
  `require_role("partner_admin")` thành `require_role("partner_admin", "supervisor")`) — **đây LÀ
  đổi `contracts/authority-matrix.yaml`, cần ADR + PO duyệt theo đúng quy trình `CLAUDE.md §3`**,
  KHÔNG nằm trong phạm vi "rẻ, không ADR" của hướng C. Nêu ra như một bước kế tiếp khả dĩ, không phải
  yêu cầu của spec này.

**Đề xuất cho v1:** chọn (a), vì đúng tinh thần "hướng C rẻ nhất" PO đã chọn. Ghi (b) vào backlog nếu
kho RAG được mở rộng cho nhiều `partner_admin`/nhiều đối tác trong tương lai (khi đó "chỉ 1 người tự
đọc log" không còn đủ).

## 5. Nghiệm thu đề xuất (khi tech-lead code xong)

Test đỏ-trước/xanh-sau tối thiểu (thuộc `tester`, viết từ SPEC này, không đọc `src/`):
1. Upload tài liệu chunk_count > 2x trung bình kho hiện có → log event `policy_doc_nap` có
   `canh_bao` chứa `"kich_thuoc_lech"`, level `WARNING`.
2. Upload tài liệu chứa `"CLAUDE.md"` trong nội dung → `canh_bao` chứa `"tu_khoa_noi_bo"`.
3. Upload tài liệu BÌNH THƯỜNG (không khớp tín hiệu nào) → `canh_bao == []`, level `INFO`, **và
   upload vẫn thành công `status="indexed"`** — xác nhận cảnh báo không chặn gì (đây là ca PHẢI xanh
   để chứng minh hướng C không đổi hành vi nghiệp vụ, chỉ thêm quan sát).
4. Tái tạo đúng ca `STATE.md` bằng dữ liệu giả lập tương đương (2 tài liệu nền + 1 tài liệu 400-chunk
   chứa từ khoá nội bộ) → xác nhận CẢ HAI tín hiệu 1 và 2 cùng khớp trong một `canh_bao`.
