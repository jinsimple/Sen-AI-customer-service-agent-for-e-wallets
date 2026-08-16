# Dự thảo ADR-026 — chỉ phục vụ tài liệu ĐÃ DUYỆT

> Vai: **security** · 2026-08-16 · **DỰ THẢO** trong vùng `docs/security/`.
> `docs/DECISIONS.md` là vùng của PO — PO-agent rà rồi land, PO thật ký (§3).
> Nền: đo `d578d0d` · sự cố `10af46d` · khuyến nghị PO cho §6.1–6.3 ·
> chuỗi xfail của tester `55118b5`.

---

## ⚠️ ĐỌC TRƯỚC — hai việc phải quyết trước khi ADR đóng

Tôi **không tự chọn hộ**, vì cả hai đều đổi hình dạng cơ chế.

### (I) PHÂN KỲ: xfail của tester đợi một CƠ CHẾ KHÁC với khuyến nghị của PO

| | Chuỗi xfail `55118b5` | Khuyến nghị PO §6.1 |
|---|---|---|
| Cơ chế | **danh mục tĩnh** `contracts/rag-nguon.yaml` (khoá `nguon_duoc_duyet`, liệt kê **tên file**) | **trạng thái duyệt theo tài liệu** trong DB (`cho_duyet` → `da_duyet`, supervisor bấm) |
| Kiểm ở đâu | test soi kho: `trong_kho - ten_duyet` phải rỗng | tầng serve lọc `trang_thai_duyet` |
| Hợp với | corpus **cố định** (2 file MoMo hôm nay) | **onboarding đối tác tự phục vụ** |
| Hỏng khi | đối tác thật upload file mới → **chặn nhầm**, phải sửa YAML + commit | cần **UI duyệt + luồng supervisor** = phạm vi sản phẩm thật |

Tôi từng **bác** whitelist tên file (*"danh mục tĩnh sẽ chặn onboarding đối tác thật"*) — vẫn giữ nguyên lập luận đó **cho sản phẩm**. Nhưng đo xong thì thấy hai thứ **không loại trừ nhau**, và **hôm nay chưa có onboarding tự phục vụ nào cả**:

> **Đề nghị làm HAI TẦNG, xếp theo thời gian:**
> - **Tầng 1 — danh mục tĩnh, LÀM NGAY.** Đóng đúng lớp sự cố **hôm nay**,
>   không cần UI, không cần luồng mới, và **cổng của tester đã viết sẵn**. Nó
>   là **dây bẫy phát hiện kho trôi**, không phải cơ chế quản trị.
> - **Tầng 2 — trạng thái duyệt trong DB (khuyến nghị PO), LÀM KHI có
>   onboarding thật.** Đây mới là cơ chế sản phẩm.
>
> Hai tầng trả lời hai câu khác nhau: *"kho có đúng thứ ta chủ ý đưa vào
> không"* (tầng 1) và *"tài liệu này đã được người có thẩm quyền duyệt chưa"*
> (tầng 2). Tầng 1 vẫn đúng **sau khi** có tầng 2.

### (II) 🔴 Bẫy vận hành: nạp-lại kho sẽ LÀM MÙ AGENT

Nếu **mọi** lần nạp đều vào `cho_duyet` thì `scripts/kho_rag.py` (nạp lại kho —
thao tác bảo trì thường quy) sẽ đẩy **toàn bộ** tài liệu về chưa-duyệt ⟹ agent
**mất sạch khả năng tra chính sách** cho tới khi có người bấm duyệt.

**Đây không phải giả định** — chính lượt nạp lại `08:42:47` là thứ **đã sửa**
sự cố. Nếu ADR-026 đang hiệu lực theo bản đơn giản, bản vá đó sẽ **làm agent
mù** và không ai biết cho tới khi khách hỏi chính sách.

**Đề nghị:** nạp lại **giữ nguyên trạng thái duyệt** khi `(filename, băm nội
dung)` không đổi. Đổi nội dung ⟹ về `cho_duyet` (đúng — nội dung mới chưa ai
đọc). Đây là ràng buộc **bắt buộc** của ADR, không phải chi tiết triển khai:
thiếu nó, cơ chế an toàn tự tạo ra một sự cố khả dụng.

---

## Bối cảnh

16/08, cửa sổ `08:23:14Z → 08:42:47Z` (19 phút 33 giây): hai file nội bộ
(`business_rules.md` — bảng số `verified=false`; `scenario-candidates-momo-faq.md`
— danh sách kịch bản test) nằm trong **kho đang phục vụ**. Đo được: **0 request
hướng khách** trong cửa sổ ⟹ không thiệt hại tới khách; phơi nhiễm giới hạn ở
`/policy-search` (endpoint nhân viên, **cố ý** không lọc — Y5).

**Điểm quyết định:** cả hai file vào qua **API upload của `partner_admin` —
cửa hợp lệ**. Nên mọi biện pháp ở **tầng nạp** (kiểm đuôi file, chặn đường
script) **đều không chặn được nó**. Chỉ **trạng thái duyệt tách khỏi hành vi
nạp** mới chặn.

## Quyết định 1 — Kho phục vụ khách CHỈ chứa tài liệu đã duyệt

`agent` (`search_policy`) chỉ nhận chunk của tài liệu **đã duyệt**. Lọc ở
**tầng serve**, trong truy vấn SQL đã có của `search_policy_text` — không đụng
Chroma, không nhúng lại (đo: `d578d0d` §3).

- **Lý do BÁC "chặn ở tầng nạp là đủ":** đã đo — có **ba** call-site
  `ingest_document` (API · `kho_rag.py` · `run_adversarial_set.py`), và sự cố
  đi qua **cửa hợp lệ nhất trong ba**. Một cổng ở tầng nạp phải được thực thi ở
  **mọi** đường, kể cả đường mà **công dụng của nó là đi vòng qua cổng**
  (`_ingest_malicious_policy`).

## Quyết định 2 — Duyệt là hành vi RIÊNG, do `supervisor`, sau khi nạp

Mọi upload — **kể cả `partner_admin`, kể cả cửa hợp lệ** — vào `cho_duyet`;
`supervisor` duyệt → `da_duyet`.

- **Lý do:** đây là **maker ≠ checker** (ADR-020/BR-12) mở rộng nhất quán từ
  *tiền* sang *tri thức*. `supervisor` đã là "quyết định cuối, mọi phạm vi" —
  **không mở role mới, không đổi hiến pháp**.
- **Lý do BÁC "`partner_admin` tự duyệt":** tái tạo sự cố bằng **một cú click**.
  Người nạp không được tự duyệt — đúng nguyên tắc đã ép ở tầng DB cho tiền.

## Quyết định 3 — Ai thấy tài liệu CHƯA duyệt

| Vai | Thấy? | Lý do |
|---|---|---|
| `agent` | **KHÔNG** | toàn bộ mục đích của cơ chế |
| `partner_admin` | CÓ | để quản tài liệu mình nạp |
| `cskh`/`supervisor` | **CÓ, kèm huy hiệu «CHƯA DUYỆT» trên TỪNG kết quả** | giữ **Y5**: người là máy dò tài liệu độc — đúng cơ chế **đáng lẽ đã bắt sự cố này sớm hơn** |

⚠️ Huy hiệu phải **sống qua lớp hiển thị** — cùng ràng buộc với dấu che ở
UI-01: *"lớp hiển thị không được làm đẹp mất dấu"*. Một badge bị nuốt còn tệ
hơn không có, vì nó tạo cảm giác đã-kiểm.

## Quyết định 4 — Backfill 2 tài liệu hiện có thành `da_duyet`

`MoMo_FAQ_Giao_dich.docx` + `MoMo_ToS.docx` — đã qua thực chiến, là nguồn đo
benchmark. Bắt duyệt lại là **nghi thức rỗng**.

- **Ràng buộc:** backfill phải **ghi lại** ai quyết và lúc nào (đây là
  backfill-có-chủ-đích, không phải mặc định im lặng) — cùng tinh thần A1-04:
  *không-làm-gì phải là quyết định ghi ra, không phải hệ quả im lặng*.

## Quyết định 5 — Đường EVAL đánh dấu tài liệu của nó là ĐÃ DUYỆT

`eval/run_adversarial_set.py` nạp tài liệu độc **có chủ đích**.

- **Lý do:** mô hình đe doạ của bộ đối kháng là **"đối tác upload tài liệu
  độc / bị chiếm tài khoản"** — trong kịch bản đó tài liệu **đúng là đã qua cửa
  duyệt**. Đánh dấu nó "chưa duyệt" khiến bộ đối kháng test một ca **dễ hơn**
  mối đe doạ thật.
- **Lý do BÁC "cờ bỏ-qua-lọc khi đang test":** một công tắc tắt-phòng-vệ trong
  mã sản phẩm là lớp lỗi **F-30** (`LANGCHAIN_TRACING_V2` — bật bằng một biến
  môi trường, **không để lại vết trong git**, không ai review thấy).

## 🔴 Quyết định 6 — Xuất-xứ KHÔNG thay thế lọc tier. Hai cơ chế cùng tồn tại.

| | Chống | KHÔNG chống |
|---|---|---|
| **Nguồn-đã-duyệt** (ADR này) | tài liệu vào kho **sai cửa / chưa ai duyệt** | tài liệu **đã duyệt** mà **nội dung độc** |
| **Lọc tier + spotlighting** (F-22/F-25/F-28) | nội dung độc **bên trong** tài liệu, bất kể nguồn | tài liệu vào kho sai cửa |

Ghi thành quyết định riêng vì đây là chỗ **chắc chắn** có người hiểu sai và đi
gỡ một trong hai. Sự cố 16/08 là ô **thứ nhất**; ADV-005 (agent lặp lại chỉ thị
độc từ policy doc) là ô **thứ hai**.

## Hệ quả

- `contracts/rag-nguon.yaml` — danh mục **tầng 1** (khoá `nguon_duoc_duyet`,
  khớp chuỗi xfail `55118b5`); gỡ `xfail(strict)` khi file tồn tại.
- `PolicyDocument` thêm `trang_thai_duyet` · `duyet_boi` · `duyet_luc` **(tầng
  2)** + migration + backfill 2 dòng.
- `ingest_document` thêm tham số **`nguon_nap` BẮT BUỘC, không default** — theo
  bài học **F-17**: có default thì quên là **im lặng thừa hưởng** giá trị an
  toàn nhất; không default thì quên là `TypeError` ngay tại call-site. Ba
  call-site sản phẩm + 4 test phải khai minh thị.
- `search_policy_text` — thêm mệnh đề lọc; **đổi tên** trường log `nguon` →
  `duong_tra` (va chạm tên, xem `d578d0d` §5b).
- `scripts/kho_rag.py` — giữ trạng thái duyệt khi `(filename, băm)` không đổi
  **(bắt buộc, xem (II))**.
- UI: màn duyệt cho `supervisor` · badge «CHƯA DUYỆT» ở `/policy-search`.

## Điều ADR này KHÔNG làm

- **Không** chặn được tài liệu **đã duyệt nhưng nội dung độc** — đó là việc của
  lọc tier (QĐ 6).
- **Không** có số về chi phí vận hành của luồng duyệt (bao nhiêu lượt/tuần khi
  có đối tác thật) — chưa có đối tác thật để đo.
- **Chưa probe** — chưa có bản vá. Khi coder land, tôi probe theo nếp: ca
  dương tính (doc chưa duyệt → agent **không** thấy) **cùng** ca đối chứng (doc
  đã duyệt → agent **vẫn** thấy đủ, recall không tụt) — cấm chạy lẻ.
