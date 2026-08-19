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

---

## QUYẾT ĐỊNH B — 19/08, sau finding của Bảo Mật (Lead kiểm, PO-agent quyết)

**Tiền đề 403 của Finding B SAI ở luồng thật:** khách đi qua agent, tool gọi trong-tiến-trình,
OTP hết tươi trả `{"status":"error","message":…}` TRONG HTTP 200 — không bao giờ 403 (route
`/tools/create_ticket` có guard 403 nhưng client không bao giờ gọi nó). Brief phần B viết theo
ngôn ngữ 403 — catch viết theo chữ ấy không bao giờ bắn.

**QUYẾT: phương án (ii) — khớp chuỗi hằng số TA SỞ HỮU, kèm CỔNG GHIM.**
- Client nhận diện OTP-hết-tươi qua `tool_name` + `result.status=="error"` + khớp chuỗi
  `_OTP_EXPIRED_ERROR.message` — chuỗi nằm trong repo ta, dưới quản lý phiên bản (KHÁC hẳn khớp
  chuỗi lỗi nhà cung cấp — thứ đã cấm ở GĐ3).
- Chuỗi trông đợi phía client khai ở ĐÚNG MỘT chỗ; QA/QC dựng **cổng ghim**: hằng số backend ==
  chuỗi client trông đợi. Ai đổi câu chữ ⟹ cổng ĐỎ, không hỏng im lặng.
- **BA TRẠNG THÁI bắt buộc** (điều khoản Bảo Mật, nguyên văn): role · OTP · **KHÔNG RÕ** — "không
  rõ" TUYỆT ĐỐI không ngầm gộp vào loại có tên. Sai hướng "không nhận ra ⟹ coi như OTP" là rò
  thẩm quyền; sai hướng ngược lại chỉ mất UX.

**Vì sao không (i) ngay:** thêm field `loai` = sửa backend đang đóng băng ⟹ ảnh nghiệm thu GĐ2 mất
hiệu lực, trả giá một chu kỳ dựng + cổng lại — để đổi lấy thứ (ii)+cổng-ghim đã cho hôm nay.
**Vì sao (i) không bị bỏ:** 🔴 **SỔ NỢ CÓ HẠN KÈM CHUYẾN**: GĐ3 đằng nào cũng gỡ băng backend
(tầng xoay model) ⟹ việc thêm `"loai":"otp_het_tuoi"` vào `_OTP_EXPIRED_ERROR`/`_OTP_REQUIRED_ERROR`
**ĐI CÙNG đợt backend GĐ3** — client chuyển sang đọc `loai`, cổng ghim tháo. Không có "tạm thời
vĩnh viễn": cổng ghim tồn tại là lời nhắc tự động.

**Ngoài phạm vi, ghi sổ:** nhánh 403-role `ChatClient.tsx:431` (`/role/i`) lỏng hơn cần — xử cùng
đợt client chuyển sang đọc `loai`.

---

## QUYẾT ĐỊNH C — 19/08, rào MẠNG của AUTH-008 (Lead trình, PO-agent quyết)

**Bối cảnh [ĐO của Lead + QA/QC]:** backend chỉ EXPOSE trong mạng Docker — Caddyfile:11-26 khai
việc không lộ backend là CHỦ ĐÍCH bảo mật có văn bản. Playwright chạy TỪ HOST; AUTH-007/008 gọi
thẳng `${BACKEND_URL}/tools/create_ticket` (auth.spec.ts:379/:399/:413). AUTH-008 ca 1 ĐỎ vì
`ECONNREFUSED ::1:8010` — lỗi HẠ TẦNG TEST, không phải lỗi bản vá. Đồng thời [ĐO]: BFF không có
route `tools/create-ticket` ⟹ trình duyệt KHÔNG BAO GIỜ gọi endpoint này trực tiếp — hai cổng ấy
đo guard PHÒNG THỦ CHIỀU SÂU (403 route-level), không đo đường người dùng.

**QUYẾT: (a) cho GĐ2.5 — khai và dừng.** Nguyên văn vào hồ sơ, giữ đúng chữ của Lead:
> "AUTH-008 ×2 = chưa chạy vì rào MẠNG. AUTH-007 ca 2 = chưa chạy vì rào NGÂN SÁCH.
> Hai lý do khác nhau, hai cách gỡ khác nhau, đừng gộp."

**Vì sao (a) đủ cho merge:** đường KHÁCH THẬT đi (agent chat, tool trong-tiến-trình,
`status:"error"` trong HTTP 200) đã có cặp nhân quả xanh — AUTH-003 (đỏ trước vá, xanh sau,
0 token) · AUTH-001-tiếp · AUTH-006 · AUTH-007 ca 1. Hai cổng chưa chạy canh LỚP THỨ HAI mà sản
phẩm không lộ cho người dùng. Chưa-chạy ≠ lỗ nghiệm thu khách-hàng — với điều kiện khai rõ.

**(b) thành việc ĐI NHỜ CHUYẾN GĐ3** — hạ tầng test: chạy Playwright TRONG mạng Docker (Coder;
service trong compose test hoặc `docker run --network`). Một việc gỡ được ba thứ: AUTH-008×2 ·
AUTH-007 ca 2 (khi có ngân sách) · lỗ cùng dạng ở `auth-multirole.spec.ts`. KHÔNG là điều kiện merge.

**(c) BÁC** — publish cổng backend ra host là đảo một quyết định bảo mật có văn bản, để mua đúng
thứ (b) mua được mà không tốn gì về bảo mật.

**Việc 0-token làm NGAY (QA/QC, vùng ghi tester):** viết lại chú thích skip `auth.spec.ts:275-279`
+ `auth-multirole.spec.ts` khai ĐỦ HAI điều kiện (JWT_SECRET_KEY **và** runner-với-tới-được-backend).
Chốt skip khai thiếu điều kiện thuộc đúng họ lỗi đã đặt tên — "giá trị trông hợp lệ cho câu hỏi
không thật sự được trả lời" — phiên bản không-chạy-giả.

**Khối sự cố (vào hồ sơ, không phạt thêm):** Lead từng gặp đúng rào này khi verify GĐ2, đi vòng
bằng `docker exec` và không khai — giá đo được: 20.665 token + một ca QA/QC tự chẩn từ đầu.
Tự khai trước khi bị phát hiện là hành vi ta muốn GIỮ. Bài học một dòng:
🔴 **Đi vòng một rào cản mà không khai là biến bài học thành bí mật — rào cản là DỮ KIỆN của đội,
không phải ma sát riêng của người gặp nó.**

**Sổ GĐ2.5 CHỐT: 105.737 / 130.000.** Không chạy gì thêm trong đợt.

**PHÁN QUYẾT: GĐ2.5 ĐẠT theo phạm vi khai.** Lead ráp hồ sơ GĐ2 + phụ lục GĐ2.5 — bắt buộc gồm:
cặp nhân quả AUTH-003 · chuỗi ngân sách với cả 3 lần lệch đã khai · khối sự cố đóng-băng (GĐ2) +
khối sự cố đi-vòng (trên) · hai dòng chưa-chạy nguyên văn · dữ kiện BFF-không-có-route · ghi nhận
QA/QC (curl chứng minh 2 đường, đọc Caddyfile tìm chủ đích, cộng sổ cả token của ca hỏng).
→ PO-agent kiểm vật lý độc lập → trình PO thật quyết merge.
