# Re-probe C4 sau vá — BOLA `/tools/lookup_transaction` + ngữ nghĩa ADR-021

> Vai: **security** · 2026-08-15 · nhánh `dev/learning-loop`
> Cặp đo với `moc-nen-C4-truoc-va.md` (mốc nền trước vá). Cùng giao dịch, cùng
> ba diễn viên. Probe **chỉ đọc**, 4 challenge OTP do probe tạo đã xoá.

---

## 0. ĐÍNH CHÍNH của chính tôi — báo động giả ở lượt trước

Ở tin nhắn trước tôi báo "C4 chưa vá", căn cứ là `grep -c
_enforce_requester_is_party src/api/main.py` = 0. **Đó là kết luận sai, và sai
theo đúng kiểu tôi vẫn cảnh báo người khác: suy từ TÊN HÀM thay vì đo HÀNH VI.**
Đường REST được vá bằng cơ chế khác tên — truyền `chi_giao_dich_cua_nguoi_goi`
xuống rồi lọc ở **tầng `matches`** (`lookup_transaction.py`), còn
`_enforce_requester_is_party` là guard của **đường agent**. PO đọc `src/` và bắt
được; ghi lại ở đây vì một báo động giả từ vai security cũng tốn đúng loại niềm
tin mà vai này sống bằng.

**Bài học ghi thành luật cho chính tôi:** với câu hỏi "đã vá chưa", **chỉ probe
hành vi mới trả lời được**. Grep tên hàm sai cả hai chiều — vừa báo "chưa vá"
khi đã vá (lần này), vừa báo "đã vá" khi tên còn đó mà đường đi đã đổi.

## 1. Container CÓ bản vá (luật F-19 đã kiểm trước khi đo)

`docker exec … grep -c chi_giao_dich_cua_nguoi_goi` → `lookup_transaction.py: 2`,
`main.py: 1` — khớp cây làm việc host. Nên các số dưới đây là đo **mã đang chạy
thật**, không phải mã trên đĩa.

## 2. Cặp đo trước/sau — 5/5 điều kiện nghiệm thu ĐẠT

| Diễn viên | Đường | **TRƯỚC vá** | **SAU vá** |
|---|---|---|---|
| `USR-0002` — **người lạ hoàn toàn** | `trans_id` | `found` · lộ `amount`/`fee`/`status`/`des`/`rec_code` | **`not_found`** ✅ |
| `USR-0002` — người lạ | `phone`+`amount` | `multiple_matches` · liệt kê `trans_id` của nạn nhân | **`not_found` · 0 ứng viên** ✅ |
| `USR-0156` — **chủ TK ngân hàng gửi** | `trans_id` | đường agent: `not_found` (chặn nhầm chính chủ) | **`found`** ✅ (ADR-021) |
| `USR-0068` — chủ ví nhận | `phone`+`amount` | `multiple_matches` | `multiple_matches` · 2 ứng viên ✅ (đúng — của chính mình) |
| bất kỳ | `phone` thiếu `amount` | **HTTP 500** | **HTTP 200 · `status='error'`** ✅ |

**Điều kiện 1 — chặn cả hai đường: ĐẠT.** Đây là phần tôi lo nhất khi gửi mốc
nền: nếu chỉ bọc chỗ trả chi tiết mà bỏ đường tìm kiếm thì vẫn dựng lại được hồ
sơ giao dịch của một người từ số điện thoại. Cách vá đã chọn — lọc ở **tầng
`matches`**, tức trước khi phân nhánh `found`/`multiple_matches`/`not_found` —
đóng cả ba nhánh bằng một chỗ. **Chuỗi tấn công "chỉ cần một số điện thoại" đã
đóng.** Và `not_found` (thay vì "có kết quả nhưng bị che") là lựa chọn đúng: nó
không hé lộ cả việc *có tồn tại* giao dịch khớp.

**Điều kiện 2 — chính chủ TK ngân hàng: ĐẠT.** `USR-0156` tra được giao dịch nạp
của chính mình (`amount=167000`). 277 ca chặn nhầm chính chủ được gỡ.

**Điều kiện 3 — union KHÔNG mở quá: ĐẠT.** Đây là mục tôi nghi nhất khi PO mở
rộng ngữ nghĩa. Đo thật: `USR-0156` thấy giao dịch, nhưng bên còn lại (ví của
`USR-0068`) **vẫn bị che** — `phone: "036***0068"`, `full_name: "Đ. X. An"`.
Mở rộng "một bên" **không** kéo theo mở rộng quyền xem dữ liệu bên kia; hai lớp
độc lập đúng như thiết kế.

**Điều kiện 4 — hết 500: ĐẠT.** `ValueError` nay ra `status='error'` đúng contract.

**Điều kiện 5 — đối chiếu ADR-021 với ATLAS-001: ĐẠT.** ADR-021 **bổ sung**, không
thay thế ATLAS-001: lớp chặn vẫn còn, chỉ định nghĩa lại "một bên" cho khớp
`ck_transactions_scope_direction_i2` (giao dịch `from_bank` có bên gửi là tài
khoản ngân hàng). Ba điểm tôi soi kỹ và đều đạt:
- **Một helper dùng chung** cho cả đường agent lẫn đường REST — không sinh hai
  định nghĩa "một bên" phải giữ đồng bộ (đúng bài học ADR-001).
- **Chặn theo VAI, không vô điều kiện**: chỉ `customer` bị giới hạn ở giao dịch
  của chính mình; CSKH/supervisor vẫn tra được cho ticket. Khớp ghi chú
  `any_authenticated` trong `authority-matrix.yaml` ("quyền xem dữ liệu ai được
  ép ở tầng dưới").
- **Động cơ ghi rõ là NGỮ NGHĨA, không phải cứu dữ liệu A1** — và ADR tự nhắc
  dữ liệu `from_bank` hỏng vẫn phải reseed. Đây đúng chỗ dễ trượt: cùng một
  thay đổi từng bị PO bác khi động cơ là "làm test xanh". Lần này động cơ khác,
  và ADR nói ra sự khác biệt đó thay vì giấu.

## 3. Còn lại

- **Không phát hiện mới** ở lượt này (F-23 của spotlighting vẫn đang chờ coder sửa).
- Kiến nghị nhỏ, không chặn: `des` vẫn nằm trong payload trả về cho **chính chủ**
  — đúng nghiệp vụ, nhưng nhắc lại rằng đó là trường tự do do **người gửi tiền**
  gõ (U2*), nên nó đã và vẫn phải đi qua spotlighting trước khi vào ngữ cảnh LLM.
  Đã xác nhận có (`customer_tools.py:170`).
