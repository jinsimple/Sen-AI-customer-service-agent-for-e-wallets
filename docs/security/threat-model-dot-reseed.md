# Threat model — Đợt reseed gộp (trước 150 người thật)

> Vai: **security** · 2026-08-14 · nhánh `dev/learning-loop`
> Phạm vi reseed theo phân việc PO (`16e8ced` mục 7): sinh lại dữ liệu
> `from_bank` 28 case (A1) · dọn phình M-04 · C8 (USR-PA01 vào
> `TEST_ACCOUNT_USER_IDS`) · C10 (seed kho RAG) · seed đủ 3 `action_type` ·
> C12 đối soát residue. **Cộng thêm** việc PO vừa giao: *"dữ liệu chat cũ xử lý
> theo đợt reseed"* (ST2-P0-3 §6).
>
> Câu hỏi được giao: **dữ liệu mới có phá giả định che PII/masking nào.**
> Trả lời ngắn: **giả định bị phá không nằm ở dữ liệu mới — nằm ở niềm tin
> rằng reseed dọn được dữ liệu cũ.** Nó không dọn, và ở trạng thái hiện tại
> nó còn không chạy nổi. Cả hai đều đã kiểm bằng thực nghiệm.

---

## TM-R1 (NẶNG NHẤT) — Reseed KHÔNG chạm bất kỳ kho PII thô nào

`scripts/seed_db.py` nói rõ ngay trong docstring: chỉ nạp **8 bảng nền**
(`users`, `wallets`, `bank_accounts`, `transactions`, `transaction_events`,
`complaints`, `tickets`, `auth_sessions`) và **KHÔNG** nạp
`tool_results`/`investigation_logs`/`resolutions`/`escalations`/`messages`.
Cơ chế "idempotent" của nó là **xoá sạch rồi nạp lại đúng 8 bảng đó**.

Đếm thật hôm nay những kho **nằm ngoài** phạm vi ấy:

| Kho | Số dòng | Chứa gì |
|---|---|---|
| `messages` | **459** | Nội dung chat gõ tay, **chưa scrub** — đúng đối tượng của ST2-P0-3 |
| `chat_sessions` | 149 | Phiên chat + CSAT |
| `tool_results` | **499** | `raw_json` kết quả tool, gồm dữ liệu bên thứ ba trước khi che |
| `investigation_logs` | 33 | Nhật ký điều tra |
| `resolutions` | 12 | Gồm dòng sentinel/backfill của F-11 |
| `checkpoints` + `checkpoint_blobs` | **1.039 + 1.496** | **Transcript hội thoại LangGraph nguyên văn, chưa scrub** (F-06) |

⟹ **Rủi ro thật:** PO đã quyết "dữ liệu chat cũ xử lý theo đợt reseed". Nếu
reseed được hiểu là "chạy `make db-seed`" thì việc dọn **im lặng không xảy
ra**, trong khi mọi người tin là đã xong — và niềm tin đó sẽ được ghi vào
STATE như một việc đã đóng. Đây đúng hình dạng của F-11 (tin vào mô tả thay vì
kiểm dữ liệu), nên phải chặn trước.

**Yêu cầu:** đợt reseed phải có **danh sách kho được dọn liệt kê tường minh**,
và `checkpoints`/`checkpoint_blobs`/`checkpoint_writes` **phải nằm trong danh
sách** — đây là kho PII lớn nhất hệ thống (2.500+ dòng) và là kho **không ai
nhớ tới** vì nó do LangGraph tạo, không có trong `models.py`.

## TM-R2 — Reseed ở trạng thái hiện tại KHÔNG CHẠY NỔI (đã chứng minh)

Mô phỏng đúng thứ tự xoá của `seed_db.py` trong transaction rồi rollback:

```
xoá auth_sessions   -> OK (355 dòng)
xoá tickets         -> *** GÃY ***: ForeignKeyViolation
    ... violates foreign key constraint "chat_sessions_ticket_id_fkey"
```

`chat_sessions`, `messages`, `resolutions`, `investigation_logs` đều có FK trỏ
vào `tickets`, và `resolutions.approved_by/rejected_by/created_by` trỏ vào
`users` — nhưng không kho nào trong số đó được `seed_db.py` dọn.

**Vì sao đây là vấn đề BẢO MẬT chứ không chỉ là bug vận hành:** người sửa sẽ
sửa dưới sức ép (sát mốc 150 người), và hai đường sửa nhanh nhất đều tệ:
tắt/bỏ qua ràng buộc khoá ngoại, hoặc chỉ xoá **đúng đủ** để hết lỗi
(`chat_sessions`) rồi để `messages` mồ côi ở lại. Cả hai đều kết thúc bằng
"reseed xanh, PII vẫn nằm nguyên đó". **Danh sách kho phải được chốt trước,
không improvise lúc gãy.**

## TM-R3 — Tài khoản test mật khẩu chung, và C8 định thêm `partner_admin` vào đó

`scripts/gen_dataset.py:48-49`: `TEST_ACCOUNT_USER_IDS = {USR-0001, USR-0145,
USR-0201, USR-0205}` dùng chung `SHARED_TEST_PASSWORD = "Demo@123"` — mật khẩu
nằm trong mã nguồn, tức **công khai**. Bốn tài khoản đó gồm cả CSKH (0201) và
**supervisor (0205)** — vai duy nhất duyệt tiền.

**C8 đề xuất thêm `USR-PA01` (partner_admin) vào chính tập này.** Cần nói rõ
hệ quả: `partner_admin` là **actor duy nhất đưa nội dung mới vào kho RAG** —
thứ mà agent tin tưởng. Một tài khoản `partner_admin` mật khẩu công khai trong
đợt 150 người thật = **cửa indirect prompt injection mở sẵn** (đúng vector
TM-01 của `threat-model-learning-loop.md`, và OWASP LLM01).

**Khuyến nghị:**
1. C8 cứ thêm `USR-PA01` để tiện test — **nhưng** trước đợt 150 người thật,
   `TEST_ACCOUNT_USER_IDS` phải **rỗng hoặc chỉ còn tài khoản không đặc quyền**;
   supervisor và partner_admin **không được** dùng mật khẩu chung.
2. Ràng buộc này nên là **test canh**, không phải lời dặn: một test đọc
   `TEST_ACCOUNT_USER_IDS` và fail nếu nó chứa user có role `supervisor` /
   `partner_admin` khi biến môi trường báo môi trường không phải demo.
3. Nếu PO muốn giữ để vận hành: đổi sang mật khẩu riêng cho từng vai đặc
   quyền, không nằm trong repo.

## TM-R4 — Sửa `from_bank` (A1) + union của C4 mở ra đường masking CHƯA TỪNG chạy

A1: 28/28 case `from_bank` hiện có ví khách **không phải một bên giao dịch** —
tức suốt thời gian qua `_enforce_requester_is_party` **chặn hết**, và đường
"trả dữ liệu giao dịch có bên thứ ba" ở nhánh `from_bank` **chưa bao giờ được
thực thi với dữ liệu thật**. Sau reseed (dữ liệu đúng) + thay đổi ngữ nghĩa
"một bên" của C4 (ví ∪ tài khoản ngân hàng), đường đó **mở ra cùng lúc ở 28
case × 4 ô ma trận**.

Giả định bị phá: *"masking bên thứ ba đã được kiểm"* — nó được kiểm trên các
nhánh **đang chạy được**, không phải nhánh vừa mở. Đây là loại lỗ hổng xuất
hiện đúng lúc dữ liệu trở nên đúng.

**Yêu cầu:** sau reseed, chạy lại bộ đối kháng che-bên-thứ-ba **nhắm riêng
`from_bank`** (tên/SĐT/STK của bên còn lại trong giao dịch nạp tiền), và
`must_not_reveal_full_receiver_phone` phải được đo trên chính các case mới —
không suy từ kết quả các ô khác. Việc này chồng lấn phạm vi probe C4 mục (b)
PO vừa giao; tôi làm một lượt.

## TM-R5 — Dữ liệu seed quá "ngoan", làm test scrub xanh giả

`gen_dataset.py:278` sinh SĐT theo khuôn cứng
`{prefix}{1 chữ số}00{4 chữ số}` — mọi số đều cùng một dạng, không dấu cách,
không `+84`, không gạch nối. Tên do `make_name()` sinh từ tập cố định.

⟹ Test scrub chạy trên dữ liệu seed **chứng minh rất ít** về đợt 150 người
thật, nơi người ta gõ `+84 91…`, `091-234-5678`, đọc rời từng số, viết tên
không dấu, viết tắt. **Đây là giả định bị phá theo chiều ngược với câu hỏi
được giao:** dữ liệu mới không phá masking — dữ liệu seed **quá sạch** khiến ta
tưởng masking đã đủ.

**Yêu cầu:** bộ test scrub phải lấy đầu vào từ **danh sách biến thể do người
viết** (đã đặc tả sẵn: nhóm B1/B3 trong `threat-model-learning-loop.md` §6),
**không** lấy từ dữ liệu seed. Reseed không được coi là bằng chứng cho scrub.

## TM-R6 — Reseed xoá `users` sẽ phá chính bản vá F-11 vừa làm

Sentinel của F-11 là **một dòng trong `users`** (bắt buộc, vì `rejected_by` là
FK và PO đã chốt không nới CHECK br11). Nhưng `users` **nằm trong 8 bảng bị xoá
sạch** khi reseed, còn `resolutions` thì **không**.

Hai hệ quả, cả hai đều xấu: hoặc reseed **gãy** ở bước xoá `users` (FK từ
`resolutions.rejected_by`), hoặc — nếu ai đó "sửa" bằng cách xoá luôn
`resolutions` — **bản vá F-11 và toàn bộ backfill F-13 biến mất không dấu
vết**, và lần rà sau sẽ thấy dữ liệu "sạch" mà không biết vì sao.

**Yêu cầu:** `gen_dataset.py`/`seed_db.py` phải **sinh lại dòng sentinel** như
một phần dữ liệu nền (cùng id, cùng nhãn `[HỆ THỐNG] không xác định`), và điều
kiện nghiệm thu reseed phải bao gồm "sentinel tồn tại sau khi seed xong".
Ghi ngay vào brief reseed, trước khi coder viết.

## TM-R7 — Artefact eval trong git mang dữ liệu của lượt chạy thật

`eval/results/` hiện có **56 file JSON**. Chúng là đầu ra của các lượt chạy
thật (bao gồm nội dung hội thoại) và **nằm trong git** — cùng tính chất "ranh
giới một chiều" đã phân tích ở `threat-model-learning-loop.md`. Với dữ liệu
seed tổng hợp thì chấp nhận được; **sau đợt 150 người thật thì không**.

**Yêu cầu:** trước khi chạy đợt 150 người, chốt luật: đầu ra eval của lượt có
người thật **không commit thô** — hoặc scrub tại điểm ghi file, hoặc để ngoài
git (`.gitignore` + kho riêng). Quyết trước, vì sau khi commit là vĩnh viễn.

## TM-R8 — C10 seed kho RAG: kiểm điểm làm sạch nằm ở đâu

Hiện `_sanitize_policy_results()` chạy ở **thời điểm truy vấn**
(`customer_tools.py:487`), không phải lúc nạp — nên seed thẳng vào DB **không
bỏ qua** lớp làm sạch. Đây là tin tốt, ghi lại để không ai "tối ưu" nó thành
làm-sạch-lúc-nạp rồi bỏ lớp truy vấn.

**Yêu cầu cho C10:** tài liệu seed phải là tài liệu do dự án viết, có nguồn rõ;
không nạp nội dung tải về hoặc do bên thứ ba cung cấp mà chưa đọc. Kho RAG là
thứ agent **tin tưởng** — nó là bề mặt indirect injection, không phải "dữ liệu
mẫu cho đẹp".

---

## Điều kiện nghiệm thu đợt reseed (đề nghị đưa thẳng vào brief coder)

1. **Danh sách kho được dọn liệt kê tường minh trong script**, gồm đủ:
   `messages`, `chat_sessions`, `tool_results`, `investigation_logs`,
   `resolutions`, `escalations`, **`checkpoints` + `checkpoint_blobs` +
   `checkpoint_writes`**. Kho nào cố ý GIỮ phải ghi rõ lý do.
2. **Không tắt/bỏ qua ràng buộc khoá ngoại** để cho qua — xoá đúng thứ tự.
3. **Sentinel F-11 được sinh lại** như dữ liệu nền; nghiệm thu bằng truy vấn.
4. **`TEST_ACCOUNT_USER_IDS` không chứa `supervisor`/`partner_admin`** ở cấu
   hình dùng cho đợt 150 người; có test canh.
5. **Đếm sau khi reseed dán vào commit** (số dòng từng kho), đối chiếu C12 —
   không mô tả bằng lời.
6. **Bộ đối kháng che-bên-thứ-ba chạy lại nhắm `from_bank`** sau khi dữ liệu
   đúng (chồng với probe C4).
7. **Luật artefact eval của lượt có người thật** đã chốt trước khi chạy.

Ba mục 1, 3, 4 là mục security sẽ ghi KHÔNG ĐẠT nếu thiếu.
