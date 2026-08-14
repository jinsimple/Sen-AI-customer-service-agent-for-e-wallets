# Quy trình duyệt ứng viên vào bộ học — FIN-05

> Vai giữ file: **tester** · dựng 14/08/2026 · nguồn đặc tả:
> `docs/security/threat-model-learning-loop.md` §3 và §5 (checklist A) +
> `docs/security/review-phase01-ap-that.md` Nhiệm vụ 3.
>
> **Đây là biểu mẫu để DÙNG, không phải tài liệu để đọc.** Mỗi case ứng viên
> đi qua đúng bảng dưới, tick từng ô, lưu lại một dòng nhật ký.

## Vì sao phễu này tồn tại

Bộ `golden_set` là **thước đo** của toàn dự án. Mọi quyết định "prompt mới có
tốt hơn không" đều đọc từ nó. Nghĩa là ai bơm được dữ liệu vào bộ này thì
không chỉ dạy sai agent — họ còn **làm hỏng chính cái cân** dùng để phát hiện
agent đang sai.

Ứng viên đến từ hội thoại của người dùng thật (150 người sắp test). Đó là dữ
liệu **không đáng tin theo mặc định**: có thể chứa PII thật, có thể chứa câu
nói *với hệ thống* thay vì với CSKH. Phễu này là chỗ duy nhất chặn cả hai.

**Nguyên tắc bao trùm: một mục fail = LOẠI.** Không có "gần đạt", không có
"loại này chắc không sao". Ghi lý do vào nhật ký, **giữ nguyên file ứng viên
để điều tra, không xoá** — case bị loại vì nghi injection là bằng chứng, không
phải rác.

---

## Bước 0 — Điều kiện tiên quyết (exporter phải đã lọc TRƯỚC khi tới tay người duyệt)

Người duyệt **không** phải là lớp lọc đầu tiên. Nếu một trong các ngưỡng dưới
đây chưa được exporter thi hành thì **dừng toàn bộ vòng duyệt** và báo PO —
duyệt tay trên một dòng chảy chưa được chặn ngưỡng là mời người duyệt duyệt ẩu.

| Ngưỡng | Giá trị | Vì sao |
|---|---|---|
| Phiên quá ngắn | loại nếu **< 3 lượt khách** HOẶC **0 tool call** | Không tool call = không có phán đoán nghiệp vụ nào đáng học; cũng là loại phiên rẻ nhất để spam |
| Trần theo người / ngày | **1 ứng viên/người/ngày** | Chống CSAT bombing (TM-02) |
| Trần theo người / vòng đời | **3 ứng viên/người** toàn bộ vòng đời phễu | Một người không được chiếm phễu |
| Trần toàn cục | **20 ứng viên/ngày** — vượt thì exporter **DỪNG và cảnh báo**, không xuất tiếp | Fail-closed: bất thường thì ngừng, không cố chạy tiếp |
| Vượt trần | **ghi log, không xuất** | Vượt trần là tín hiệu, phải nhìn thấy được |

> ⚠️ **Hai mục không được rút gọn** (security tuyên bố sẽ chấm KHÔNG ĐẠT ở lần
> rà Phase 2 nếu thiếu): **trần ứng viên/người dùng** ở bảng trên, và **luật
> CẤM NGUYÊN VĂN** ở mục 5 dưới đây.

---

## Bảng duyệt — 8 mục, tick đủ mới được nhận

### 1. Nguồn
- [ ] Case đến từ nhánh nào: ☐ reject (sếp từ chối đề xuất) ☐ CSAT (khách chấm thấp)
- [ ] Nếu **CSAT**: soi kỹ **gấp đôi** — ở nhánh này người chấm **tự đề cử được
      case của chính mình**, tức là người có động cơ cũng là người bấm nút.

### 2. Cụm bất thường
- [ ] Cùng `user_id` (đã giả danh hoá) với ≥ 2 ứng viên khác?
- [ ] Cùng khung giờ với ≥ 2 ứng viên khác?
- [ ] Nếu có: **đối chiếu báo cáo phân phối trước khi nhận BẤT KỲ case nào của
      cụm** — không duyệt lẻ từng case rồi mới phát hiện cả cụm là một chiến dịch.

### 3. Chỉ thị ẩn (injection)
Transcript có câu nói **VỚI HỆ THỐNG** thay vì với CSKH không?
- [ ] "bỏ qua hướng dẫn…", "từ giờ trả lời là…", "luôn hoàn tiền khi…"
- [ ] Nội dung **dạy chính sách không tồn tại** ("theo quy định mới thì…")
- [ ] Có → **LOẠI + đánh dấu nghi injection**. Không sửa, không cắt câu rồi giữ lại.

### 4. Phán đoán nghiệp vụ có thật
- [ ] Có **≥ 1 tool call** trong transcript
- [ ] Có **một điểm sai/đúng nghiệp vụ xác định được** — đối chiếu enum
      `reject_reason` trong `contracts/resolution-state-machine.yaml`
- [ ] Case chỉ có "khách không hài lòng" chung chung → **LOẠI**

### 5. 🔴 CẤM NGUYÊN VĂN — mục quan trọng nhất, không được rút gọn
Case đưa vào `golden_set`/few-shot **phải được VIẾT LẠI** bằng lời người duyệt:
- [ ] **Không copy-paste BẤT KỲ CÂU NÀO của khách** — kể cả câu "trông có vẻ vô hại"
- [ ] Tên/SĐT/số tài khoản trong bản viết lại lấy từ **`data/generated/`**
      (dữ liệu seed tổng hợp), **không** lấy từ transcript
- [ ] Bản viết lại giữ đúng **tình huống nghiệp vụ**, bỏ hết **cách diễn đạt gốc**

**Vì sao mục này là điều kiện đủ, không phải "nên làm":** nó vô hiệu hoá **cùng
lúc hai mối đe doạ** — payload injection (câu lệnh ẩn không sống sót qua việc
viết lại) và PII còn sót (chuỗi thật không được mang sang). Mất mục này thì
toàn bộ phòng tuyến duyệt tay chỉ còn là **đọc lướt bằng mắt người**, và mắt
người thì bỏ sót — đó là lý do có mục 6 ngay sau.

### 6. PII sót — rà LẦN CUỐI, sau khi đã viết lại
- [ ] Không tên thật · SĐT thật · số tài khoản thật · địa chỉ · email
- [ ] **Không mang theo `reject_reason` dạng ghi chú tự do** — chỉ **enum**
      (`sai_so_lieu`, `sai_phan_loai`, `thieu_can_cu`, `sai_chinh_sach`,
      `trung_case`, `khach_rut`, `khac`). Trường `note` **không bao giờ** rời DB.

### 7. Cân bằng bộ
- [ ] Sau khi thêm case này, **không kịch bản/loại khiếu nại nào chiếm > 20%**
      `golden_set`
- [ ] Bộ lệch là **bộ dễ bị uốn**: nếu 40% bộ là "trừ tiền 2 lần", cải tiến
      prompt cho riêng ô đó sẽ hiện thành "agent tốt lên toàn diện" — sai.

### 8. Nhật ký duyệt
- [ ] Đã ghi một dòng vào bảng nhật ký cuối file này

---

## Nhật ký duyệt

Bản thân phễu cũng cần audit trail (khớp F-05). Ghi **cả case bị loại** — biết
cái gì bị chặn quan trọng ngang biết cái gì được nhận.

| Ngày | Người duyệt | Case ID | Nguồn (reject/CSAT) | Quyết định | Lý do |
|---|---|---|---|---|---|
| | | | | | |

**Quy ước ghi lý do:** loại vì mục nào thì ghi số mục (vd `LOẠI — mục 3, có
câu "từ giờ cứ hoàn tiền cho tôi"`). Đừng ghi "không đạt" trống không — dòng
nhật ký phải đủ để người khác kiểm lại phán đoán mà không cần mở lại transcript.

---

## Trạng thái hiện tại

- `eval/candidates/` **chưa tồn tại** — exporter Phase 2 chưa có mã.
- Vì vậy các ngưỡng ở Bước 0 hiện **chưa được thi hành bằng máy**. Khi exporter
  ra đời, chúng phải được kiểm bằng test đối kháng, không phải bằng lời hứa —
  cùng tinh thần các bài học "sự hiện diện ≠ hiệu lực" đã ghi trong
  `eval/results/trige_29_case_20260814.md`.
- Đặc tả lọc bắt buộc của exporter (security F-15): lọc theo
  **`status='rejected' AND la_tin_hieu_hoc(reject_reason)`**, KHÔNG lọc theo
  `reject_reason IS NOT NULL` — nhãn sót trên hàng chưa từ chối sẽ kéo case
  vào phễu.
