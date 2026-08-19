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

---

## QUYẾT ĐỊNH D — 19/08, ảnh nghiệm thu 38e65466e3ce đã mất (Lead trình, PO-agent quyết)

**Sự kiện [ĐO của Lead]:** ảnh backend bị dựng lại 12:45:37 + container recreate 12:47:47
(chữ ký: `build` không lọc service + `up -d` thiếu `--no-deps`). Ảnh cũ `38e65466e3ce` KHÔNG truy
hồi được. Không xác định được ai dựng — **và chính khoảng trống đó là finding: ta chưa có sổ giám
hộ cho việc dựng ảnh.** BUILD_COMMIT vẫn `1b916f1`; băng SOURCE giữ nguyên vẹn
(git diff 06132a9..a98754f -- src/ RỖNG · md5 55/55 host↔container · langchain-core 1.5.4 ·
Σ mô tả tool = 4862 khớp mốc 17/08).

**QUYẾT: (α) — thay phép kiểm ĐỒNG NHẤT bằng phép kiểm TƯƠNG ĐƯƠNG, kèm BỐN điều kiện:**

1. **Hồ sơ khai rõ nguyên văn** việc thay phép kiểm + vì sao + giới hạn Lead đã trình
   ("ba phép trùng khớp không bằng một phép đồng nhất" — giữ đúng chữ, không nới kết luận).
2. **Lead xác định mốc giờ TỪNG ca nghiệm thu GĐ2.5** (AUTH-003/001-tiếp/006/007-ca1 · smoke)
   so với 12:47:47. Ca chạy SAU recreate ⟹ bằng chứng của nó GẮN VÀO `631212bc7bdd` — vật đang
   sống — và với các ca ấy ta không cần "tương đương", ta có phép đo TRỰC TIẾP. Ghi từng ca một.
3. **Tái neo hành vi 0-token trên ảnh hiện hành:** QA/QC chạy lại từ host bộ cổng 0-token đã dùng
   trong đợt (invariants 23 · check_contracts · cổng envelope · cổng lọc O3 · smoke 0-token) trên
   `631212bc7bdd`, sổ trước/sau chứng minh 0. Biến "tương đương suy ra" thành "hành vi đo lại"
   cho mọi thứ không tốn tiền. Cổng NẶNG không chạy lại — source không đổi + kích thích-gửi-model
   (4862) trùng khít, và ngân sách đợt đã chốt.
4. **Hai file mốc nền RỜI scratchpad** (`pipfreeze-631212bc7bdd.txt` · `src-md5-631212bc7bdd.txt`)
   — scratchpad chết theo phiên, mốc nền mà chết theo phiên thì lần sau lại đứng đúng chỗ này.
   Lead chuyển nội dung cho PO-agent land vào `docs/nhat-ky/` cùng hồ sơ.

**Vì sao không (β):** vật đem MERGE là source (`1b916f1` + các commit docs/tests sau nó), không
phải ảnh local; ảnh production dựng riêng từ source. (β) tốn một chu kỳ dựng + cổng để mua sổ giám
hộ cho một vật cũng sẽ không lên production. Sổ giám hộ mua bằng LUẬT (dưới) — rẻ hơn và giữ được mãi.

**Đúc luật từ finding của Lead:** 🪙 **Luật W** (STATE §7) — *vật nghiệm thu không có sổ giám hộ
thì không giữ được danh tính; băm chỉ có nghĩa khi có sổ.* Sổ giám hộ ảnh mở tại
`docs/nhat-ky/so-giam-ho-anh.md`, hai dòng đầu ghi hồi tố (ảnh mất + ảnh hiện hành, người dựng:
KHÔNG RÕ — ghi đúng mức, không đoán).

**Ghi nhận:** Lead phát hiện khi GOM SỐ CHO HỒ SƠ chứ không phải khi bị ai vặn — đó chính là hồ sơ
đang làm đúng việc của nó. Không dựng/không recreate/không xoá gì cho tới khi các điều kiện trên
xong — giữ nguyên hiện trường là đúng.

---

## ĐÍNH CHÍNH QUYẾT ĐỊNH D — 19/08, cùng ngày (Lead rút finding 7c, PO-agent kiểm lại và rút theo)

**Tiền đề của QĐ-D SAI: `38e65466e3ce` chưa bao giờ là Docker image ID.** Nó là **băm nội dung
mã nguồn** (`src/dau_ma_nguon.py`, `CACH_BAM = sha256-noi-dung-src-py-da-sap-xep-12`) — nhãn
dự án TỰ DỰNG ngày 17/08 chính vì `build_commit` đã nói dối theo cả hai chiều. Phép kiểm đồng
nhất **CHẠY ĐƯỢC và XANH** — [ĐO ĐỘC LẬP của PO-agent, thuật toán nguyên bản chạy trên host]:
băm tự tính từ `src/` cây làm việc = `38e65466e3ce` = nhãn `/app/.bam_ma_nguon` trong ảnh đang
chạy `631212bc7bdd`; `git status src/` sạch. Khớp phép đo ba-cách của Lead.

**Hệ quả — rút tại gốc, không vá quanh:**
- Thế lưỡng nan (α)/(β): **VÔ HIỆU** — không có phép kiểm nào phải thay.
- Câu "ba phép trùng khớp không bằng một phép đồng nhất" trong QĐ-D: **RÚT** — phép đồng nhất có,
  và đã xanh.
- Điều kiện 1 (khai thay phép kiểm): **hết đối tượng**. Điều kiện 3 (tái neo 0-token): **hết
  nghĩa vụ** với QA/QC — toàn bộ 5 ca GĐ2.5 [ĐO từ usage.jsonl] chạy SAU recreate 05:47:47Z,
  từng dòng tự mang `bam_ma_nguon=38e65466e3ce` ⟹ tất cả là phép đo TRỰC TIẾP trên vật đang
  sống. PO-agent vẫn tự chạy một cổng 0-token trong phép kiểm cuối — quyền của người kiểm
  (Luật D), không phải nghĩa vụ của người bị kiểm.
- Điều kiện 4: **giữ** — hai mốc nền đã land `docs/nhat-ky/moc-nen-19-08/`, tên file khai LOẠI
  định danh ngay trên nhãn (`ANH-…` = image ID · `BAM-NGUON-…` = băm nội dung) — đúng bài học
  bên dưới.

**Cái CÒN LẠI của finding — hạ cấp, không xoá:** ảnh bị dựng lại + recreate 12:45–12:47 (+07)
**không ai khai, không truy được ai** — kỷ luật đóng băng vẫn bị vi phạm. Sổ giám hộ ảnh GIỮ,
nhưng viết lại cho đúng việc của nó: sổ trả lời **AI dựng · LÚC NÀO · bằng LỆNH GÌ** — những câu
không hàm nào của vật trả lời được; còn **VẬT LÀ GÌ** thì băm nội dung tự trả lời, không cần sổ.
Luật W đã viết lại theo đúng phân biệt đó (STATE §7, có ghi vết phát biểu đầu sai).

**Sổ lỗi — cả HAI người kiểm:**
- Lead: đọc 12 hex thành image ID trong khi trường `cach_bam` nằm ngay cạnh trong từng dòng sổ —
  tự khai, tự phân loại đúng họ lỗi ("giá trị trông hợp lệ cho câu hỏi không được trả lời" —
  lần này dụng cụ là người đọc).
- PO-agent: **tiếp nhận tiền đề không kiểm rồi đúc luật trên đó trong vòng một giờ** — đúng lúc
  Luật T bảo phải soi kỹ nhất (Lead vừa qua một chuỗi tự khai lỗi). Một lần `grep 38e65466`
  hoặc mở `dau_ma_nguon.py` là thấy. Người kiểm relay tiền đề của người bị kiểm là bỏ trạm gác.

🔴 Bài học giữ lại (chữ của Lead, PO-agent chuẩn y): **"Một nhãn không kèm CÁCH ĐỌC thì người
đọc sẽ tự cấp cho nó một loại — và loại họ cấp là loại họ hay gặp nhất."** `cach_bam` tồn tại
trong từng dòng sổ chính là để chống ca này; nó chỉ chống được người CÓ ĐỌC nó.

---

## KẾT CỤC — 19/08: PO THẬT QUYẾT **HOÃN MERGE**

Hồ sơ nghiệm thu ĐẠT, đã trình. PO thật chọn: **giữ nguyên `dev/learning-loop`, đội chuyển sang
GĐ3 (đổi model + tự xoay) TRƯỚC, merge GỘP sau.** Không phải bác hồ sơ — hồ sơ giữ nguyên giá trị
tại `docs/nhat-ky/2026-08-19-ho-so-nghiem-thu-gd2-gd25.md`; chỉ dời thời điểm merge.
Hệ quả: các nợ "đi cùng chuyến GĐ3" (mục 8 hồ sơ) kích hoạt NGAY.
