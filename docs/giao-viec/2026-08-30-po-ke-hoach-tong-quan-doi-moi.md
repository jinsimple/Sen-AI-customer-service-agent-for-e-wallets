# KẾ HOẠCH TỔNG QUAN — ĐỢT "NỀN VỮNG"

> **Từ:** phiên PO · **Cho:** Lead (p-226-61) · **Ngày:** 30/08/2026
> **Người thật quyết định cuối:** PO thật (Đào Ngọc Bích). Tôi là phiên PO — tôi chốt
> **phạm vi và thứ tự**; tôi **không** chốt tiền, khoá bí mật, push production, hay đổi contract.
> Mục §4 liệt kê rõ ranh giới đó.

---

## 0. Một câu

**Đợt này không thêm tính năng nào. Mục tiêu duy nhất: làm cho những gì đã có TRỞ NÊN
CHỨNG MINH ĐƯỢC** — vá hai lỗ xác thực, phục hồi tín hiệu đo, và đóng hồ sơ pháp lý đang
trích dẫn văn bản đã hết hiệu lực.

---

## 1. Vì sao đóng băng tính năng — ba dữ kiện, không phải cảm tính

**① Hai lỗ xác thực đang phủ nhận toàn bộ phần thiết kế đúng phía trên.**
`/auth/otp/request` **và** `/resolutions/{id}/request-approval-otp` (route duyệt hoàn tiền —
Bảo mật vừa bổ sung 30/08) đều trả thẳng `otp_code` trong response body. Cộng thêm
`verify_otp` so sánh bằng `==` thay vì constant-time.
⟹ Yếu tố "sở hữu" của xác thực hai lớp **không tồn tại trên đường chạy thật**. Mọi câu
"đạt PSD2 SCA / NIST AAL2" nói ra lúc này đều sai — không phải sai một phần, mà sai hẳn.

**② Không có tín hiệu đo nào đáng tin để xác nhận bất cứ thứ gì vừa vá.**
CI chưa từng xanh cho cả đợt "OTP trước token". QA/QC đo thật 30/08: **27/27 file e2e vẫn
dùng `loginAs()` cũ, 0 file đã retrofit** *(nặng hơn con số "~3 tệp đã dùng" ghi trong
`docs/STATE.md` §0.1 — dùng số 27/27, đừng dùng số cũ)*. Thêm 3 test luôn đỏ vì thiếu module
`eval/` trong container.
⟹ Nếu Coder vá xong mà không ai phân biệt được "đỏ vì lỗi mới" với "đỏ vì nợ cũ", thì bản
vá đó **không nghiệm thu được**, chỉ có thể *tin*.

**③ Toàn bộ hồ sơ pháp lý đang trích dẫn văn bản đã hết hiệu lực 8 tháng.**
Luật 91/2025/QH15 + NĐ 356/2025/NĐ-CP thay thế NĐ 13/2023 từ 01/01/2026. Grep toàn repo:
`"91/2025"` → **0 kết quả**. NĐ 13/2023 xuất hiện ở ≥20 file, gồm cả `CLAUDE.md §8` và bản
rà soát mới nhất 27/08.
⟹ Đây là lỗi rẻ nhất trong toàn bộ danh sách và cũng là lỗi **dễ mất mặt nhất** nếu đối tác
ví điện tử thật phát hiện trước ta.

---

## 2. Bốn làn, chạy SONG SONG — không xếp hàng chờ nhau

Xếp tuần tự là sai ở đây: làn A đang chảy máu, làn B là điều kiện để nghiệm thu làn A,
làn C và D không đụng code nên không có lý do gì phải đợi.

| Làn | Vai chính | Nội dung | Vì sao không đợi làn khác |
|---|---|---|---|
| **A · Vá xác thực** | Coder (+Bảo mật soát) | 2 route OTP + constant-time | Đang hở thật, không đợi CI xanh mới vá |
| **B · Phục hồi tín hiệu đo** | QA/QC | retrofit 27 file e2e + tách nhiễu 3 test `eval/` | Là điều kiện nghiệm thu làn A |
| **C · Hồ sơ pháp lý** | Bảo mật (+PO) | cập nhật luật · DPIA · IR runbook | Không chạm code, không tranh chấp file |
| **D · Soát chéo** | Review | soát bản vá làn A + đối chiếu contract | Chạy sau A, nhưng chuẩn bị được ngay |

---

## 3. Thứ tự trong từng làn + cổng nghiệm thu

Cổng nghiệm thu viết theo nguyên tắc đã được PO thật niêm: **cổng phải ăn CẢ HAI đầu vào**
— phải chứng minh được nó ĐỎ khi lỗi còn đó, không chỉ XANH khi lỗi đã hết. Cổng chỉ biết
xanh là cổng không mang thông tin.

### Làn A — Coder
1. **A1.** Gỡ `otp_code` khỏi response body ở **cả hai** route. Giữ đường demo bằng **cờ môi
   trường tường minh**, mặc định TẮT, và cờ đó phải **fail-fast khi `APP_ENV=production`**.
2. **A2.** `verify_otp` → `secrets.compare_digest`. Một dòng, cùng vùng, làm chung một lượt.
3. **A3.** Chuẩn bị *phân tích tác động* cho ADR-055 Bậc 1 (gắn `require_token_chua_thu_hoi`
   vào 3 route) — **CHỈ phân tích, KHÔNG code.** Đây là việc chờ người thật, xem §4.

> 🔴 **Ràng buộc sống còn, chép nguyên văn từ `STATE.md` §0.2:** CHỈ **THÊM**
> `require_token_chua_thu_hoi`. **KHÔNG BAO GIỜ** rút `is_access_token_revoked` ra khỏi
> `require_otp_verified`. Rút ⟹ `create_ticket` mất bảo vệ **im lặng, không test nào đỏ**.

**Cổng A:** test mới phải ĐỎ trên commit trước bản vá và XANH sau — dán cả hai kết quả.
Thiếu vế đỏ thì chưa nghiệm thu.

### Làn B — QA/QC
1. **B1.** Retrofit 27 file e2e sang `loginPath` đúng. Đây là **nợ cũ, không phải hồi quy** —
   đừng ai báo cáo nó như bug mới.
2. **B2.** Tách 3 test thiếu module `eval/` ra khỏi luồng thường, để "3 failed" **không còn
   là nhiễu thường trực**. Ai đọc CI phải phân biệt được đỏ-thật với đỏ-nợ.
3. **B3.** Viết test cho làn A theo cổng ở trên (chờ A1/A2 land trước).

### Làn C — Bảo mật (+ tôi làm phần `CLAUDE.md`)
1. **C1.** *(tôi làm, không phải Bảo mật)* Cập nhật `CLAUDE.md §8` sang Luật 91/2025/QH15 +
   NĐ 356/2025/NĐ-CP. `CLAUDE.md` thuộc vùng ghi của PO.
2. **C2.** Rà toàn bộ tham chiếu NĐ 13/2023 còn lại trong `docs/` → thay hoặc niêm rõ
   "văn bản đã hết hiệu lực, giữ làm lịch sử".
3. **C3.** IR runbook tối thiểu: ai phân loại mức độ · báo ai · trong bao lâu (ngành tài
   chính: **72 giờ** tới cơ quan thẩm quyền **và** chủ thể dữ liệu). Đừng làm phức tạp —
   cần **TỒN TẠI** trước khi cần dùng thật.
4. **C4.** DPIA + hồ sơ chuyển dữ liệu xuyên biên giới. Vật liệu đã có sẵn ở
   `docs/security/2026-08-17-kiem-ke-du-lieu-roi-bien-gioi-cho-ho-so-D25.md`.
   ⚠️ Câu hỏi này **đã treo với PO thật 2 lần chưa có trả lời** — xem §4, đừng hỏi lần 3.

### Làn D — Review
1. **D1.** Soát bản vá làn A — đặc biệt canh đúng cái bẫy ở §3 làn A.
2. **D2.** Một việc riêng, quan trọng hơn vẻ ngoài của nó: cơ chế chống lệch contract hiện
   **chỉ so TÊN tool, không so chữ ký/input** *(tự khai ở `contracts/agent-tools.yaml`
   dòng 34-40)*. Đổi input mà quên contract ⟹ vẫn xanh. Đề xuất cách bịt, **chưa làm**.

---

## 4. 🔴 VIỆC CHỈ NGƯỜI THẬT QUYẾT — Lead không quyết, tôi cũng không

Đây là ranh giới cứng. Vi phạm mục này nguy hiểm hơn làm chậm.

| # | Việc | Vì sao không ai trong đội quyết được |
|---|---|---|
| 1 | Đổi `contracts/` | `CLAUDE.md §3`: sửa contract phải qua ADR + PO duyệt, **trước** khi code |
| 2 | ADR-055 Bậc 1 — 3 route nào | Chạm ma trận thẩm quyền ⟹ thuộc mục 1 |
| 3 | Push 47 commit / merge lên `main` | Kích CI trên hạ tầng ban tổ chức + chạm production |
| 4 | Khoá bí mật `LLM_API_KEY`, GitHub billing, self-hosted runner | Tiền + tài khoản cá nhân |
| 5 | Deploy production (`deploy_home.ps1`) | Production **đang LIVE thật** trên máy Windows PO |
| 6 | Có nộp hồ sơ DPIA/Đ.25 chính thức không | Nghĩa vụ pháp lý đứng tên tổ chức, không phải quyết định kỹ thuật |

**Cách trình đúng khi cần một trong sáu mục trên:** trình **DỮ KIỆN kèm hệ quả**, không
trình lại **CÂU HỎI**. PO thật đã ra lệnh 18/08 sau khi bị hỏi lại ba lần cùng một chuyện.
Mục 6 đã treo 2 lần — lần này đưa kèm chi phí của việc *không* làm, để người thật quyết
một phát.

---

## 5. Ba câu QA/QC hỏi — trả lời luôn, đừng chờ

1. **Ba mục CAO trước mốc pitch nào?** → Vá OTP (A1/A2) là **P0, chặn ngôn từ đối ngoại**:
   trước khi bất kỳ tài liệu nào dùng chữ "SCA/PSD2/AAL2". DPIA và IR runbook là **P1** —
   cần trước khi nói "sẵn sàng tuân thủ", **không** chặn một buổi demo kỹ thuật.
2. **WCAG/accessibility có trong MVP không?** → **KHÔNG trong đợt này.** Ghi nhận là khoảng
   trống đã biết *(lưu ý: European Accessibility Act áp cho dịch vụ ngân hàng/thương mại điện
   tử tại EU — sẽ thành thật khi bàn thị trường EU, không phải hôm nay).*
3. **Ngăn `fin05` seed lại không?** → **Có, seed lại.** Nó là ngăn làm việc chính, để trống
   thì phiên sau tưởng "tự nhiên rỗng" và đi điều tra lại từ đầu.

---

## 6. Cách tôi làm việc với Lead

**Nhịp:** Lead gom và báo cáo cho tôi **theo mốc**, không theo giờ — mỗi khi một cổng ở §3
đóng, hoặc khi gặp một mục ở §4. Không cần báo cáo tiến độ trống.

**Ba thứ tôi sẽ kiểm ở mọi báo cáo — nói trước để không ai mất thời gian:**

1. **Phân biệt ĐỌC và CHẠY.** "Sạch" từ đọc diff ≠ "sạch" từ chạy thật. Báo cáo phải nói rõ
   cái nào là cái nào. Không làm tròn lên.
2. **Cổng phải ăn cả hai đầu vào.** Cổng chỉ chứng minh được vế xanh thì tôi trả lại.
3. **Phạm vi của phép đo phải khớp phạm vi của kết luận.** `grep` trả đúng không có nghĩa
   kết luận suy rộng ra là đúng — trình bằng **cơ chế**, đừng trình bằng **số đếm**.

**Một điều tôi muốn Lead chủ động làm, không phải chờ tôi:** nếu một mục trong kế hoạch này
sai — sai thứ tự, sai giả định, hoặc đã lỗi thời so với phép đo thật — **nói ngay và nói
bằng phép đo**, đừng thi hành cho xong. QA/QC vừa làm đúng điều đó với con số 27/27, và nó
có giá trị hơn cả một ngày làm đúng theo kế hoạch sai.
