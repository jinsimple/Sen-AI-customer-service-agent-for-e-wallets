# C3 — IR Runbook tối thiểu (DRAFT, chưa ký) — Làn C "Nền Vững"

> Vai: `security`. Giao từ Lead (`p-226-61`), theo `docs/giao-viec/2026-08-30-po-ke-hoach-tong-quan-doi-moi.md`
> §3 Làn C, mục C3. **Đây là DRAFT — đủ để TỒN TẠI trước khi cần dùng thật, chưa cần PO ký.**
> Cố ý làm đơn giản (yêu cầu của kế hoạch: "đừng làm phức tạp").

## 1. Ba mức độ — đủ dùng, không cần thang điểm phức tạp

| Mức | Định nghĩa | Ví dụ trong dự án |
|---|---|---|
| **P0 — Nghiêm trọng** | Mất/lộ dữ liệu KHÁCH HÀNG THẬT, hoặc hệ thống production ngừng phục vụ | Lộ transcript khách thật ra ngoài; DB production bị xoá |
| **P1 — Cao** | Mất/lộ dữ liệu trên môi trường KHÔNG PHẢI production (demo/dev/staging), hoặc lỗ hổng bảo mật đang bị khai thác | Sự cố `fin05` 27/08 (xem mục 4) — đúng mức này |
| **P2 — Trung bình** | Lỗ hổng phát hiện qua rà soát, CHƯA có bằng chứng bị khai thác | Một finding CAO trong `docs/security/` trước khi vá |

**Nguyên tắc phân loại:** phân loại theo **dữ liệu bị ảnh hưởng là của AI**, không theo ý định của
người gây ra sự cố. Một lệnh gõ nhầm (không cố ý) vẫn phân loại theo hậu quả, không theo động cơ.

## 2. Ai làm gì, trong bao lâu

```
Bước 1 — PHÁT HIỆN → BÁO NGAY, không chờ điều tra xong
  Người phát hiện (bất kỳ vai nào) → ghi 1 dòng vào docs/STATE.md §0 (bàn giao đang mở)
  HOẶC gửi thẳng PO qua kênh đang dùng (SendMessage/artifact tra cứu) nếu STATE.md không kịp cập nhật.
  KHÔNG chờ xác định mức độ mới báo — báo trước, phân loại sau.

Bước 2 — PHÂN LOẠI (trong 1 giờ kể từ phát hiện)
  security (hoặc Lead nếu security không sẵn) gán mức P0/P1/P2 theo bảng ở mục 1.
  Ghi vào docs/security/incidents/<ngày>-<tên-ngắn>.md (mẫu ở mục 5).

Bước 3 — NGĂN CHẶN (ngay khi phân loại xong, không đợi báo cáo đầy đủ)
  Việc kỹ thuật tối thiểu để dừng thiệt hại tiếp diễn — vd thu hồi khoá, dừng route, khoá tài khoản.
  KHÔNG phải việc của security một mình — người có quyền kỹ thuật đúng vùng (tech-lead/devops) làm,
  security xác nhận đã dừng.

Bước 4 — THÔNG BÁO — CHỈ áp dụng cho P0 có dữ liệu cá nhân thật bị ảnh hưởng
  🔴 Mốc 72 GIỜ kể từ lúc PHÁT HIỆN (không phải lúc xảy ra), theo Luật 91/2025/QH15 Đ.23.1.
  - Báo CƠ QUAN CHUYÊN TRÁCH bảo vệ dữ liệu — **BẮT BUỘC**, trong 72 giờ, khi vi phạm có khả năng
    ảnh hưởng quốc phòng/an ninh/trật tự xã hội hoặc quyền lợi/tính mạng/sức khoẻ/danh dự/tài sản
    chủ thể dữ liệu. [ĐÃ XÁC MINH lần đầu qua WebSearch 30/08; **[CẬP NHẬT 30/08, theo báo cáo PO
    đọc toàn văn bản PDF gốc, chuyển qua Lead — tôi CHƯA tự đọc bản gốc, chỉ ghi lại có gắn nguồn]**:
    số điều chính xác là Đ.23.1.]
  - Báo CHỦ THỂ DỮ LIỆU bị ảnh hưởng — **[CẬP NHẬT 30/08] KHÔNG bắt buộc trong trường hợp chung**,
    theo báo cáo PO (đọc Đ.23, chưa tự tôi xác nhận): 72 giờ chỉ bắt buộc báo CƠ QUAN CHUYÊN TRÁCH.
    Ngoại lệ duy nhất được nêu: **dữ liệu SINH TRẮC HỌC** (Đ.31.4.b) — không áp dụng cho FIN-05 (dự
    án không xử lý dữ liệu sinh trắc học). Việc tôi TRƯỚC ĐÓ (bản đầu 30/08) từ chối khẳng định
    nghĩa vụ báo chủ thể là ĐÚNG hướng — giờ có căn cứ cụ thể hơn (dù vẫn qua báo cáo, chưa tự đọc):
    **không có nghĩa vụ luật định báo chủ thể dữ liệu cho ca thường của FIN-05.** Runbook này VẪN
    GIỮ bước báo chủ thể như một **lựa chọn thận trọng tự nguyện** (làm chặt hơn luật đòi hỏi không
    phải vi phạm gì) — nhưng từ nay ghi rõ nó KHÔNG phải nghĩa vụ pháp lý, để người đọc không hiểu
    nhầm cả hai vế đều bắt buộc như nhau.
  - Người thật quyết định CÓ báo chủ thể dữ liệu (tự nguyện) hay không — đây vẫn là quyết định đứng
    tên tổ chức (§4 mục 6 kế hoạch Nền Vững), KHÔNG phải quyết định của Lead/security/AI nào trong đội.

Bước 5 — GHI LẠI, KHÔNG XOÁ (Luật P, CLAUDE.md §7b)
  Đóng hồ sơ tại docs/security/incidents/, để nguyên — không xoá kể cả sau khi khắc phục xong.
  Đây chính là bằng chứng SOC2/ISO 27001 sẽ hỏi ("cho xem incident log 12 tháng gần nhất").
```

## 3. 🔴 Lịch sử cảnh báo tự-kiểm — GIỮ LẠI để thấy phép đo đã đổi, không xoá (Luật P)

Dòng "72 giờ tới cơ quan thẩm quyền **và** chủ thể dữ liệu" trong
`docs/giao-viec/2026-08-30-po-ke-hoach-tong-quan-doi-moi.md` §3-C3 ban đầu chỉ là **chỉ dẫn thiết
kế** từ kế hoạch, chưa phải xác nhận pháp lý. Bản đầu của file này (30/08, trước khi PO đọc toàn
văn) giữ nguyên hai vế ở dạng ngang nhau vì tôi (security) mới xác minh được qua WebSearch phần
**báo cơ quan thẩm quyền**, còn phần **báo chủ thể dữ liệu** chưa xác minh được.

🟢 **CẬP NHẬT — PO đã đọc toàn văn bản gốc (ảnh từng trang, PDF quét), báo qua Lead cùng ngày:**
72 giờ **chỉ** bắt buộc báo cơ quan chuyên trách (Đ.23.1); báo chủ thể dữ liệu **không** bắt buộc
trừ dữ liệu sinh trắc học (Đ.31.4.b, không áp dụng cho FIN-05). Xem Bước 4 ở mục 2 — đã cập nhật
theo đúng phân biệt này. **Việc tôi giữ mơ hồ ở bản đầu là ĐÚNG cách xử lý khi chưa có nguồn** —
giữ đoạn này lại làm ví dụ cho chính nguyên tắc đó, không xoá để trông như tôi biết trước.

⚠️ Vẫn còn một lớp gián tiếp: tôi (security) **chưa tự đọc bản gốc**, chỉ ghi lại báo cáo của PO qua
Lead. Độ tin cậy cao hơn WebSearch nhiều (người thật đọc tay bản chính thống), nhưng **chưa phải
tôi tự xác nhận trực tiếp** — nếu có sai lệch giữa báo cáo và bản gốc, tôi không phải người phát
hiện được.

## 4. Ca ví dụ đầu tiên — sự cố mất CSDL `fin05`, 27/08/2026

Áp dụng runbook (hồi tố) cho sự cố đã ghi ở `docs/STATE.md §0.6b`, để runbook không viết suông:

- **Phát hiện:** Coder gõ tên lệnh trong dấu nháy kép; dấu huyền ngược khiến shell THỰC THI lệnh đó
  thay vì trích dẫn ⟹ mất sạch CSDL ngăn `fin05`.
- **Phân loại: P1** (không phải P0) — vì: (a) `fin05` là ngăn DEMO/làm việc, **KHÔNG PHẢI
  production** *(production là máy Windows PO, xác nhận riêng ở `docs/STATE.md`)*; (b) dữ liệu mất
  là dữ liệu SEED (tài khoản demo, giao dịch mẫu), **không phải dữ liệu khách hàng thật** — dự án
  chưa có dữ liệu khách hàng thật (mốc kích hoạt Đ.25/DPIA còn chưa tới, xem C4 §5). ⟹ **Bước 4
  (thông báo) KHÔNG áp dụng** cho ca này — đúng tinh thần bảng mức độ mục 1.
- **Ngăn chặn:** không cần — sự cố đã xảy ra và dừng tự nhiên (không phải tấn công đang tiếp diễn).
  Việc còn lại là khôi phục (seed lại), chờ quyết định PO (`docs/STATE.md §0.7` mục PO đã trả lời
  30/08 ở `docs/giao-viec/...-tong-quan-doi-moi.md` §5 mục 3: "Có, seed lại").
- **Bài học đã rút, dùng được cho toàn đội** *(đã ghi sẵn ở `docs/STATE.md`, trích lại vì đây đúng
  hình dạng một dòng "root cause" trong incident report thật)*: dấu huyền ngược trong nháy kép của
  shell **thực thi**, không phải trích dẫn — tên lệnh muốn đưa vào văn bản thì dùng nháy đơn hoặc
  thoát dấu.
- **Ghi lại:** đã ghi đầy đủ tại `docs/STATE.md §0.6b` từ 27/08 — **không tạo bản sao ở
  `docs/security/incidents/`**, chỉ trỏ về đây làm ca đầu tiên của runbook (Luật P — không nhân bản
  cùng một sự kiện ở hai nơi).

## 5. Mẫu ghi sự cố (dùng cho các ca SAU thời điểm này)

```markdown
# INC-<YYYYMMDD>-<tên-ngắn>

- Phát hiện: <ai, lúc nào, qua đâu>
- Mức độ: P0 / P1 / P2 (theo bảng mục 1)
- Dữ liệu bị ảnh hưởng: <loại + có phải dữ liệu khách hàng thật không>
- Ngăn chặn: <việc đã làm, ai làm, lúc nào>
- Thông báo (chỉ P0 có dữ liệu cá nhân thật): <đã báo ai, lúc nào, hay đang chờ PO thật quyết>
- Nguyên nhân gốc: <1-2 câu>
- Bài học: <việc cụ thể tương lai làm khác đi>
```

## 6. Việc CHƯA làm — khai rõ, không giấu

- Chưa đọc toàn văn Luật 91/2025/QH15 + NĐ 356/2025/NĐ-CP để xác nhận nghĩa vụ báo chủ thể dữ liệu
  (mục 3). **Bắt buộc trước khi PO ký bản này thành chính thức.**
- Runbook này giả định `docs/security/incidents/` là nơi lưu — thư mục **chưa tồn tại**, sẽ tạo khi
  có ca đầu tiên SAU thời điểm này (ca `fin05` 27/08 xử lý hồi tố ở mục 4, không cần thư mục riêng).
- Chưa có cơ chế BÁO ĐỘNG tự động (chỉ dựa vào con người phát hiện) — ngoài phạm vi "tối thiểu" của
  C3, ghi nhận là khoảng trống roadmap nếu cần sau này.
