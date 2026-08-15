# Phản biện dự thảo ADR-025 — 3 vấn đề CHẶN, 1 lưu ý

> Vai: **security** · 2026-08-15 · phản biện theo yêu cầu PO-agent, **trước khi
> PO thật xác nhận số**.
> Dấu lúc đo: `he_thong=f3193ecae0e2` · HEAD `27843d4` (cây đang trôi — coder
> land A1; các phép đo dưới đây **không phụ thuộc `src/`** trừ chỗ ghi rõ).

## Tóm tắt

| QĐ | Đánh giá |
|---|---|
| 1 — trục BẰNG CHỨNG | ✅ **Trung thành hồ sơ cơ chế.** Không sửa gì. |
| 2 — đọc theo người phụ trách | 🔴 **CHẶN — chưa thực thi được trên mô hình dữ liệu hiện tại** |
| 3 — retention 5 năm | 🟡 đồng ý hướng; **một bẫy kỹ thuật** khi xoá |
| 4 — preview-confirm | 🔴 **CHẶN — thiếu hai vòng khoá, đúng chỗ tôi cũng viết thiếu** |
| 5 — trần 2.000 + CHECK ciphertext ≤4000 | 🔴 **CHẶN — con số 4000 SAI với tiếng Việt, đo được** |

---

## 🔴 QĐ 5 — bound `length <= 4000` chặn nhầm chính khách hàng Việt

Dự thảo đặt CHECK thô trên ciphertext `length <= 4000`, dẫn "worst-case đo được
×1.9 + đệm" với số đo `2.000 → 3.556`.

**Số đó không phải worst case.** Fernet nở theo **byte UTF-8**, mà tiếng Việt có
dấu là **3 byte/ký tự** (emoji 4 byte). Tôi đo trực tiếp:

```
loại                      ký tự  byte UTF-8  ciphertext   vs bound 4000
ASCII thuần                2000        2000        2764   OK
Tiếng Việt CÓ DẤU          2000        6000        8100   *** VƯỢT — CHECK CHẶN NHẦM ***
Khiếu nại thật (trộn)      2000        2486        3404   OK (biên chỉ 15%)

=> Với ký tự 3-byte, CHECK<=4000 chỉ cho tối đa ~975 ký tự — chưa tới MỘT NỬA
   trần nghiệp vụ 2.000.
```

**Hậu quả:** một khiếu nại 2.000 ký tự viết bằng tiếng Việt đủ dấu — tức
**cách viết bình thường của người dùng** — sẽ **vượt CHECK ở tầng DB**. Triệu
chứng: `IntegrityError` → **HTTP 500** cho khách đang khiếu nại, đúng hình dạng
**F-21** (ràng buộc DB nổ thành 500 thay vì 4xx sạch). Và nó sẽ **trông như
chống-flood đang chạy đúng** trong khi thực chất đang từ chối lời khai hợp lệ.

Đây là **S-01 lặp lại ở một cơ chế khác**: một lớp phòng vệ phá nội dung thật,
im lặng, và số biện minh cho nó được đo trên mẫu hẹp (ASCII) rồi áp cho mẫu
rộng (tiếng Việt). Luật 8, lần thứ tư.

**Đề nghị — chọn một, tôi khuyến nghị (b):**
- **(a)** nâng bound lên **≥ 11.000** (worst case thật: 2.000 ký tự × 4 byte =
  8.000 byte → ciphertext ~10.800).
- **(b) ⭐ Bỏ hẳn ý định "CHECK phản chiếu trần nghiệp vụ".** Trần ký tự ép ở
  Pydantic (`max_length=2000`) — chỗ duy nhất diễn đạt được nó đúng. CHECK ở DB
  giữ vai trò **chống-flood thuần tuý**, đặt rộng rãi (vd `<= 40.000`, trên số
  đo 20.000 ký tự → 34.424). Hai lớp giữ **hai mục đích khác nhau** thay vì lớp
  dưới cố bắt chước lớp trên bằng một đơn vị nó không diễn đạt được.

Dù chọn gì: **phải có ca đối chứng "2.000 ký tự tiếng Việt đủ dấu → NHẬN"**
trong bộ A2 (tôi đã bổ sung vào bộ probe).

---

## 🔴 QĐ 2 — "ticket mình phụ trách" chưa tồn tại trong mô hình dữ liệu

Dự thảo: *`cskh` chỉ đọc transcript/description của **ticket mình phụ trách
(assigned)***.

**Đo trên `src/db/models.py`:** `Ticket` có **`assigned_role`** — một **VAI**
(`String`, default `"cskh"`), **không phải** `assigned_to` một **NGƯỜI**. Không
có cột nào gắn ticket với một nhân viên cụ thể. Thứ duy nhất gắn người là
`ChatSession.claimed_by` — nhưng đó là **phiên chat**, không phải ticket, và chỉ
tồn tại khi đã có live-chat.

⟹ QĐ 2 **không phải một thay đổi guard**, nó là một **tính năng nghiệp vụ mới**:
cần cột phân công + quy trình (ai phân công · lúc nào · ticket chưa phân công
thì ai đọc · ticket không có phiên chat thì lấy gì làm căn cứ). Phạm vi lớn hơn
hẳn những gì dự thảo gợi ý, và nó **chạm luồng vận hành CSKH thật**.

**Ba việc phải quyết kèm, nếu không QĐ 2 sẽ bị vá quanh trong vận hành:**
1. **Break-glass.** CSKH trực đêm gặp khách của ticket người khác thì làm gì?
   Không có đường thoát **có kiểm soát** thì đội sẽ phân công tất-cả-cho-tất-cả
   và quyền đọc quay về như cũ — nhưng nay có thêm một lớp trông-như-đã-siết.
   Đề nghị: cho đọc + **bắt buộc ghi audit + lý do**, không chặn cứng.
2. **Audit-log phải phủ MỌI lượt đọc nhóm A, không riêng `supervisor`.**
   Dự thảo chỉ bắt audit cho supervisor. Nhưng rủi ro nội gián lớn nhất là
   **CSKH có quyền hợp lệ** đọc/trích dữ liệu ca mình. PCI DSS Req 10 và SOC 2
   CC6 đòi log truy cập dữ liệu nhạy cảm **theo mọi chủ thể**, không theo cấp.
3. Ticket **chưa phân công** (mọi ticket hôm nay) — mặc định phải là gì?

**Không phải lý do bác QĐ 2** — hướng need-to-know là đúng và tôi giữ nguyên
khuyến nghị. Đây là "chi phí thật cao hơn dự thảo ngụ ý", PO cần biết trước khi
ký, nếu không nó sẽ trượt lịch và bị cắt xén giữa chừng.

---

## 🔴 QĐ 4 — preview-confirm thiếu hai vòng khoá (chỗ HỒ SƠ CỦA TÔI cũng viết thiếu)

Cơ chế đúng hướng — đây là B1 tôi khuyến nghị. Nhưng bản mô tả (và bản gốc của
tôi) **bỏ trống hai chỗ mà một implementation thẳng tay sẽ làm sai**:

**(1) Không được tin văn bản client gửi ở bước xác nhận.**
Luồng "server trả bản đã che → client xác nhận → server ghi" tạo đúng một cửa
**TOCTOU**: client có thể gửi lại **bản THÔ** (hoặc bất kỳ chuỗi nào) ở bước
confirm, và server — vốn tưởng "cái này đã che rồi" — ghi thẳng. Bug này trông
vô hại trong code và phá sạch lớp phòng vệ.
👉 **Server PHẢI scrub lại văn bản nhận ở bước ghi, luôn luôn**, bất kể client
nói nó đã được xác nhận. Preview chỉ là **giao diện**, không bao giờ là **lớp
tin cậy**.

**(2) "Sửa chữ rồi lưu" là một đường vòng qua scrub — phải khoá vòng lặp.**
Nếu nhân viên sửa lại được, họ **gõ lại đúng PII vừa bị che** và bấm xác nhận.
Fail-visible cho con người quyền ghi đè — đó là **bản chất** của cơ chế, không
phải lỗi. Nhưng nó phải là vòng lặp đóng:
👉 văn bản đã sửa **đi qua scrub lại từ đầu**; còn khớp PII thì **hiện lại
preview**, không có đường "xác nhận lần hai để bỏ qua". Người sửa được **cách
diễn đạt**, không sửa được **kết quả scrub**.

Thiếu (2) thì preview-confirm biến từ "làm phép che nhìn thấy được" thành "cho
nhân viên tắt phép che" — **ngược hẳn mục đích S-01**.

**Tự nhận:** hai khoá này **không có trong hồ sơ `6f18c9d` của tôi**. Tôi viết
"API trả bản đã che → nhân viên xác nhận hoặc viết lại" và dừng ở đó. PO-agent
diễn đạt trung thành đúng những gì tôi viết; chỗ thiếu là của tôi.

---

## 🟡 QĐ 3 — retention: một bẫy kỹ thuật khi tới lúc xoá

Đồng ý hướng, và cảm ơn đã **giữ nguyên cờ pháp lý** của tôi.

Bẫy: *"xoá hoặc ẩn danh hoá không đảo ngược"* — với `messages.content`
(`EncryptedText`) sẽ có người nghĩ tới **crypto-shredding** (huỷ khoá thay vì
xoá dòng). **Không làm được ở đây:** `FIELD_ENCRYPTION_KEY` là **một khoá dùng
chung** cho `messages.content`, `PolicyChunk.text`, `bank_accounts.account_no`.
Huỷ khoá để xoá một ticket sẽ **phá toàn bộ dữ liệu mã hoá của hệ thống**.
👉 Xoá theo retention phải là **xoá dòng thật** (hoặc ẩn danh hoá tại chỗ). Nếu
sau này muốn crypto-shred theo ticket thì cần **khoá theo ticket** — quyết định
kiến trúc riêng, không phải chi tiết triển khai của ADR-025.

---

## ✅ QĐ 1 — không sửa gì

Trục **bằng chứng / sửa-lại-được** được diễn đạt đúng, kể cả vế "che lúc XUẤT
là chỗ `scrub_pii` được viết ra". Phần "Lý do BÁC BỎ" giữ đúng cả ba lập luận,
gồm vế mạnh nhất (`messages.content` at-rest **đã chạy thật, kiểm bằng byte**).

## Việc tôi KHÔNG phản biện

Con số **5 năm** — tôi không có thẩm quyền pháp lý để xác nhận hay bác. Cờ
"cần tư vấn pháp lý thật" đã ở đúng chỗ; đó là điều duy nhất tôi có thể nói
đúng về nó.
