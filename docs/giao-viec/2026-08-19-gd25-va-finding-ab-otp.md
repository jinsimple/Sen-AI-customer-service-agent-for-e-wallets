# GĐ2.5 — vá Finding A (M-10) + Finding B trước merge · 19/08

> PO thật QUYẾT 19/08: "Vá A/B trước rồi mới merge." Hồ sơ GĐ2 giữ nguyên giá trị — đợt này
> CỘNG THÊM vào nó, không thay nó. Đọc kèm: hồ sơ merge GĐ2 (tin nhắn Lead) + brief GĐ2.

## 1. PHẠM VI GỠ BĂNG — hẹp, có khai

- **GỠ BĂNG: `frontend/src/` + `frontend/e2e/`.** Cả hai finding nằm ở client (`ChatClient.tsx`).
- 🔴 **`src/` BACKEND VẪN ĐÓNG BĂNG.** Ảnh backend `38e65466e3ce`/`06132a9` là vật đã nghiệm thu —
  không dòng nào được đổi. Nếu đường vá NÀO đòi route/field backend mới ⟹ DỪNG, báo PO-agent
  (đụng authority-matrix là §10, và làm mất hiệu lực bằng chứng GĐ2 — hai lý do độc lập để dừng).
- Dựng lại CHỈ `fin05-frontend` sau khi land. Backend không recreate.

## 2. VIỆC — theo vai

### CODER (tech-lead — frontend/src thuộc vùng ghi của vai này theo §4)
**A · (= M-10, hướng fix đã ghi sổ từ 14/08):** khởi tạo trạng thái OTP từ PHIÊN thay vì `useState(false)`.
- Ưu tiên 1: đọc từ dữ liệu phiên ĐÃ CÓ phía BFF (`/api/session` — JWT server-side đã mang
  `otp_verified_at`; QA từng đọc được nó sau reload trong phép phân định ⟹ nhiều khả năng không
  cần route backend mới — XÁC MINH trước khi viết).
- BFF chỉ trả về thứ client cần: boolean `otp_xem_con_han` / `otp_stepup_con_han` hoặc mốc hết hạn —
  KHÔNG bê nguyên claim JWT ra client (Bảo Mật soi điểm này).
- Ràng buộc: logic hạn tính MỘT nơi (server), client chỉ tiêu thụ — không tự tính lại 12h/15min
  ở client bằng hằng số chép tay (hai định nghĩa một vật là lớp lỗi đã có tên).

**B · (mới):** hết tươi step-up phải thành LỜI MỜI, không phải LỖI.
- Đường chính: bắt đúng lỗi 403-OTP-cũ từ backend (phân biệt với 403-role đã có nhánh riêng trong
  catch `ChatClient.tsx`) → mở lại luồng OTP (`beginOtpFlow`) + giữ lại hành động khách đang làm
  để gửi tiếp sau xác thực (khuôn `pendingStarterRef` đã có sẵn — dùng lại, đừng chế mới).
- KHÔNG chỉ đặt timer client xoá ref — timer client là bản sao thứ hai của đồng hồ server, lệch là
  quay lại đúng bug này. Timer (nếu muốn thêm cho UX) chỉ là tối ưu phụ, nguồn sự thật là 403.

### QA/QC
1. Commit 6 file E2E đang dở (pathspec) — chúng thuộc đợt này.
2. **Cổng nghiệm thu = 5 ca đỏ dựng sẵn** (AUTH-003 + 4 ca step-up) — KHÔNG sửa assertion để "cho
   hợp bản vá"; chúng được viết từ hợp đồng ADR-005/AUTH-005/007/008, bản vá phải làm chúng xanh
   nguyên trạng. Sửa ca nào phải khai lý do từng dòng.
3. Ca hồi quy: bẫy hằng-đúng đã ghi (unlock TRƯỚC forge, không phải sau) — giữ nguyên vị trí.
4. Re-run smoke 0-token (login/dashboard/chào/US-012) trên frontend mới.
5. **Ngân sách RÀO MỚI, sổ riêng GĐ2.5:** khai ước TỪNG ca nặng trước khi chạy ("0-token là phép
   đo, không phải phân loại" — đọc sổ trước/sau). Lead giữ sổ, PO-agent duyệt số trước lượt đầu tiên.

### BẢO MẬT (một đoạn)
- Field phiên lộ ra client qua BFF: boolean/mốc hết hạn có đủ hẹp chưa, có lộ gì thừa không.
- Finding B fix: xác nhận chiều fail-closed server KHÔNG đổi (client mời lại chỉ là UX; 403 server
  vẫn là chốt).

### REVIEW
- Soi: A không chép hằng số 12h/15min sang client · B phân biệt 403-OTP với 403-role bằng dấu hiệu
  BỀN (không match chuỗi thông báo dễ đổi) · bẫy hằng-đúng không tái xuất · diff không lan ra ngoài
  hai finding.

### LEAD
- Trình tự như hai vòng trước. Dựng frontend MỘT LẦN sau land + ký. Khai trước khi dựng (Luật U:
  hỏi-và-chờ, không chỉ khai).
- Định nghĩa xong GĐ2.5: 5 ca đỏ → XANH nguyên trạng · smoke 0-token xanh · 2 chữ ký · số token khai đủ.
- Xong ⟹ hồ sơ GĐ2 + phụ lục GĐ2.5 → PO-agent kiểm → trình PO thật MERGE.

## 3. ĐỊNH NGHĨA XONG
- [ ] Finding A: F5 sau OTP — rail còn mở, không hỏi lại (đúng hợp đồng 12h)
- [ ] Finding B: quá 15' + hành động nhạy cảm — khách nhận LỜI MỜI xác thực lại, xong việc đi tiếp
- [ ] 5 ca đỏ dựng sẵn → XANH nguyên trạng (không sửa assertion không khai)
- [ ] Smoke 0-token xanh trên frontend mới · backend KHÔNG bị chạm (băm giữ nguyên 38e65466e3ce)
- [ ] Chữ ký Bảo Mật + Review · sổ token GĐ2.5 khai đủ
