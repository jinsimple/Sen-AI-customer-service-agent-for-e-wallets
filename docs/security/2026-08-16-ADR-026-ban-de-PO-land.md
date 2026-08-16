# ADR-026 — bản hoàn chỉnh để PO land vào `docs/DECISIONS.md`

> **Hướng dẫn cho PO-agent:** chép nguyên khối dưới đường kẻ vào `DECISIONS.md`.
> `DECISIONS.md` là vùng PO — tôi không ghi thẳng.
> Nền: đo `d578d0d` · sự cố `10af46d` (ĐÓNG, `3819484`) · dự thảo `5a00717` ·
> khuyến nghị 4 điểm của PO · chuỗi xfail tester `55118b5`.
> Đề xuất nội dung `contracts/rag-nguon.yaml` ở **Phụ lục** (vùng tech-lead —
> tôi đề xuất, không ghi).

---

## ADR-026 — Kho RAG chỉ phục vụ tài liệu ĐÃ DUYỆT; duyệt là hành vi riêng của `supervisor`

- **Ngày:** 2026-08-16 · **Trạng thái:** chờ PO thật ký (đụng `contracts/` — §3)
- **Bối cảnh:**

  16/08, cửa sổ `08:23:14Z → 08:42:47Z` (19 phút 33 giây), hai file nội bộ —
  `business_rules.md` (bảng số `verified=false`) và
  `scenario-candidates-momo-faq.md` (danh sách kịch bản test) — nằm trong **kho
  đang phục vụ**. Đo được: **0 request hướng khách** trong cửa sổ ⟹ không thiệt
  hại tới khách; phơi nhiễm giới hạn ở `/policy-search` (endpoint nhân viên,
  **cố ý** không lọc — Y5). Truy nguồn đã đóng: **người vận hành upload qua
  đúng màn hình Đối-tác-ví** — tai nạn quy trình, không phải xâm nhập.

  **Câu hỏi đầu tiên của người vận hành khi được báo là:** *"đối tác ví có
  luồng upload riêng là đã quản lý được phần này rồi đúng không?"*

  **Niềm tin đó sai, và sai theo cách rất tự nhiên.** Tách vai `partner_admin`
  kiểm soát **AI ĐƯỢC PHÉP LÀM GÌ**; nó **không** kiểm soát **CÁI GÌ TRỞ THÀNH
  CHÍNH SÁCH**. Một vai riêng cho việc nạp *trông* y hệt cơ chế quản trị nội
  dung, nhưng nó chỉ là cơ chế **phân quyền**. Người đầu tiên vấp vào khoảng
  trống đó là **một người thiện chí, dùng đúng cửa được thiết kế cho họ, không
  làm sai quy trình nào** — đó là định nghĩa của khoảng trống thiết kế, không
  phải lỗi người dùng.

  ⟹ ADR này **tách hai thứ vốn bị gộp**: *ai được nạp* (phân quyền — đã có) và
  *cái gì được phục vụ* (duyệt nội dung — **chưa có**).

### Quyết định 1 — Agent chỉ được phục vụ chunk của tài liệu `da_duyet`

Lọc ở **tầng serve**, trong truy vấn SQL đã có của `search_policy_text`.

- **Lý do:** đo được (`d578d0d`) — `search_policy_text` vốn chạy hai bước
  (Chroma → SQL join `PolicyDocument`), nên lọc là **một mệnh đề thêm vào truy
  vấn đã có**: **không đụng Chroma, không nhúng lại 378 chunk**, và đi theo
  đúng khuôn `if chunk is None: continue` **đã tồn tại và đã chạy**. Chi phí
  recall = **0** ở vận hành bình thường (mọi tài liệu đã duyệt thì không bỏ gì).
- **Lý do BÁC "chặn ở tầng nạp là đủ":** có **ba** call-site `ingest_document`
  (API `main.py:1195` · `kho_rag.py:244` · `run_adversarial_set.py:57`), và sự
  cố đi qua **cửa hợp lệ nhất trong ba**. Một cổng ở tầng nạp phải được thực
  thi ở **mọi** đường — kể cả đường mà **công dụng của nó là đi vòng qua cổng**
  (`_ingest_malicious_policy`).

### Quyết định 2 — Duyệt là hành vi RIÊNG, do `supervisor`, SAU khi nạp

Mọi upload — **kể cả `partner_admin`, kể cả cửa hợp lệ** — vào `cho_duyet`;
`supervisor` duyệt → `da_duyet`.

- **Lý do:** đây là **maker ≠ checker** (ADR-020/BR-12) mở rộng nhất quán từ
  *tiền* sang *tri thức*. `supervisor` đã là "quyết định cuối, mọi phạm vi" ⟹
  **không mở role mới, không đổi hiến pháp**.
- **Lý do BÁC "`partner_admin` tự duyệt":** tái tạo sự cố bằng **một cú click**.
  Người nạp không được tự duyệt — đúng nguyên tắc đã ép ở tầng DB cho tiền.

### Quyết định 3 — Ai thấy tài liệu CHƯA duyệt

| Vai | Thấy? | Lý do |
|---|---|---|
| `agent` | **KHÔNG** | toàn bộ mục đích của cơ chế |
| `partner_admin` | CÓ | để quản tài liệu mình nạp |
| `cskh` / `supervisor` | **CÓ, kèm huy hiệu «CHƯA DUYỆT» trên TỪNG kết quả** | giữ **Y5**: người là máy dò tài liệu độc — đúng cơ chế **đáng lẽ đã bắt sự cố này sớm hơn** |

- **Ràng buộc:** huy hiệu phải **sống qua lớp hiển thị** — cùng ràng buộc với
  dấu che ở UI-01 (*"lớp hiển thị không được làm đẹp mất dấu"*). **Một badge bị
  nuốt còn tệ hơn không có**, vì nó tạo cảm giác đã-kiểm.

### Quyết định 4 — Backfill 2 tài liệu hiện có thành `da_duyet`

`MoMo_FAQ_Giao_dich.docx` + `MoMo_ToS.docx` — đã qua thực chiến, là nguồn đo
benchmark. Bắt duyệt lại là **nghi thức rỗng**.

- **Ràng buộc:** backfill phải **ghi lại ai quyết và lúc nào** — đây là
  backfill **có chủ đích**, không phải mặc định im lặng. Cùng tinh thần A1-04:
  *không-làm-gì phải là quyết định ghi ra, không phải hệ quả im lặng*.

### Quyết định 5 — Đường EVAL đánh dấu tài liệu của nó là ĐÃ DUYỆT

- **Lý do:** mô hình đe doạ của bộ đối kháng là **"đối tác upload tài liệu độc
  / bị chiếm tài khoản"** — trong kịch bản đó tài liệu **đúng là đã qua cửa
  duyệt**. Đánh dấu nó "chưa duyệt" khiến bộ đối kháng test một ca **dễ hơn**
  mối đe doạ thật.
- **Lý do BÁC "cờ bỏ-qua-lọc khi đang test":** một công tắc tắt-phòng-vệ trong
  mã sản phẩm là lớp lỗi **F-30** — bật bằng một biến môi trường, **không để
  lại vết trong git**, không ai trong quy trình review thấy.

### 🔴 Quyết định 6 — Xuất-xứ KHÔNG thay thế lọc tier. Hai cơ chế cùng tồn tại.

| | Chống | KHÔNG chống |
|---|---|---|
| **Nguồn-đã-duyệt** (ADR này) | tài liệu vào kho **sai cửa / chưa ai duyệt** | tài liệu **đã duyệt** mà **nội dung độc** |
| **Lọc tier + spotlighting** (F-22/F-25/F-28) | nội dung độc **bên trong** tài liệu, bất kể nguồn | tài liệu vào kho sai cửa |

Ghi thành quyết định **riêng** vì đây là chỗ **chắc chắn** sẽ có người hiểu sai
và đi gỡ một trong hai. Sự cố 16/08 là ô **thứ nhất**; ADV-005 (agent lặp lại
chỉ thị độc từ policy doc) là ô **thứ hai**.

### 🔴 Quyết định 7 — Nạp lại kho PHẢI giữ nguyên trạng thái duyệt

`scripts/kho_rag.py` giữ `trang_thai_duyet` khi `(filename, băm nội dung)`
không đổi. Nội dung đổi ⟹ về `cho_duyet`.

- **Lý do — đây là ràng buộc BẮT BUỘC, không phải chi tiết triển khai:** nếu
  **mọi** lần nạp đều vào `cho_duyet` thì nạp-lại-kho (thao tác **bảo trì
  thường quy**) sẽ đẩy toàn bộ về chưa-duyệt ⟹ **agent mất sạch khả năng tra
  chính sách** cho tới khi có người bấm duyệt.
- **Không phải giả định:** chính lượt nạp lại `08:42:47` là thứ **đã sửa** sự
  cố. Nếu ADR này đang hiệu lực theo bản đơn giản, **bản vá đó sẽ làm agent
  mù**, và không ai biết cho tới khi khách hỏi chính sách. **Một cơ chế an toàn
  tự tạo ra một sự cố khả dụng là một cơ chế hỏng.**

### Quyết định 8 — HAI TẦNG, xếp theo thời gian

- **Tầng 1 — danh mục tĩnh `contracts/rag-nguon.yaml`, LÀM NGAY.** Đóng đúng
  lớp sự cố **hôm nay**: không cần UI, không cần luồng mới, và **cổng của
  tester đã viết sẵn** (`55118b5`, hiện `xfail(strict)` — gỡ khi file tồn tại).
  Nó là **dây bẫy phát hiện kho trôi**, không phải cơ chế quản trị.
- **Tầng 2 — trạng thái duyệt trong DB (QĐ 1–4, 7), làm khi có onboarding đối
  tác thật.** Đây mới là cơ chế sản phẩm.
- **Lý do làm cả hai:** chúng trả lời **hai câu khác nhau** — *"kho có đúng thứ
  ta chủ ý đưa vào không"* (tầng 1) và *"tài liệu này đã được người có thẩm
  quyền duyệt chưa"* (tầng 2). **Tầng 1 vẫn đúng SAU KHI có tầng 2.**
- **Lý do BÁC "chỉ làm tầng 1":** danh mục **tên file** sẽ chặn nhầm ngay khi
  có đối tác thật upload — không dùng được làm cơ chế sản phẩm.
- **Lý do BÁC "chỉ làm tầng 2":** nó cần **UI duyệt + luồng supervisor** =
  phạm vi sản phẩm thật, trong khi lớp sự cố đang hở **hôm nay**.

### Hệ quả

- `contracts/rag-nguon.yaml` (**tầng 1**, khoá `nguon_duoc_duyet`) · gỡ
  `xfail(strict)` ở `55118b5` · `CONTRACT_VERSION` bump + `--update` baseline.
- `PolicyDocument` thêm `trang_thai_duyet` · `duyet_boi` · `duyet_luc` +
  migration + **backfill 2 dòng có ghi người quyết**.
- `ingest_document` thêm **`nguon_nap`** — **default `"khong_ro"`** (⚠️ **KHÁC**
  bài học F-17 một cách có chủ đích: ở F-17, default làm bộ lọc **thoái hoá im
  lặng**; ở đây default `"khong_ro"` **tự tố cáo** đường chưa khai. Luật đúng
  là *default phải là giá trị DỄ THẤY nhất, không phải tiện nhất*).
- `search_policy_text` — thêm mệnh đề lọc `da_duyet`.
- `scripts/kho_rag.py` — **QĐ 7** (giữ trạng thái duyệt theo `(filename, băm)`).
- UI: màn duyệt cho `supervisor` · badge «CHƯA DUYỆT» ở `/policy-search`.

### Điều ADR này KHÔNG làm

- **Không** chặn tài liệu **đã duyệt nhưng nội dung độc** — việc của lọc tier
  (QĐ 6).
- **Không** có số về chi phí vận hành luồng duyệt khi có đối tác thật — chưa có
  đối tác thật để đo.
- **Chưa probe.** Khi coder land, security probe theo nếp: ca **dương tính**
  (doc chưa duyệt → agent **không** thấy) **cùng** ca **đối chứng** (doc đã
  duyệt → agent **vẫn** thấy đủ, recall không tụt) — **cấm chạy lẻ** (Luật 2).

---

## Phụ lục — đề xuất nội dung `contracts/rag-nguon.yaml`

> Vùng `contracts/` là của tech-lead sau khi PO duyệt. Đây là **đề xuất**, khoá
> đặt theo đúng thứ chuỗi xfail `55118b5` đang dò (`nguon_duoc_duyet`).

```yaml
# Danh mục nguồn ĐƯỢC PHÉP có mặt trong kho RAG phục vụ khách (ADR-026 tầng 1).
# Đây là DÂY BẪY phát hiện kho trôi, KHÔNG phải cơ chế quản trị nội dung —
# cơ chế đó là trang_thai_duyet ở tầng DB (ADR-026 tầng 2).
version: 1
nguon_duoc_duyet:
  - ten_file: MoMo_FAQ_Giao_dich.docx
    mo_ta: FAQ giao dịch — nguồn chính sách vận hành cho khách
  - ten_file: MoMo_ToS.docx
    mo_ta: Điều khoản dịch vụ — phần ràng buộc pháp lý
# Mọi tài liệu KHÁC xuất hiện trong kho phục vụ = kho đã trôi khỏi chủ đích.
# Thêm dòng ở đây là một QUYẾT ĐỊNH, phải qua review như mọi thay đổi contract.
```
