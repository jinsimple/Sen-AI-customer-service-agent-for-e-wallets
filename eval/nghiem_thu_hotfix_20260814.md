# Bảng nghiệm thu hotfix V1–V6 — demo tối 14/08

> Phiên tester · lập lúc phần **chuẩn bị** (coder chưa commit code hotfix nào —
> commit mới nhất trên `main` là `b45167b` chỉ có docs; container frontend vẫn
> từ 13/08 15:50). Nghiệm thu bằng UI/API/DB trên stack Docker, **không đọc
> `src/`**. Quy tắc đợt này: **chỉ báo cáo, không sửa**.

## 0. Mốc "TRƯỚC HOTFIX" — đã đo, dùng để so sánh sau

| Hạng mục | Trạng thái trước | Cách đo |
|---|---|---|
| Bất biến | **19/19 xanh** | `pytest tests/test_invariants.py` |
| Contract | sạch, không artifact lỗi thời | `check_contracts.py` |
| `/approve` có dữ liệu? | **CÓ — 3/3 pending_approval** | `GET /api/resolutions` (đăng nhập sếp) |
| Dòng "6đ" | **còn**: `RES-b8d2c7798d53 · refund_to_wallet · 6 · pending_approval` | DB + API |
| Rail chưa OTP | **hiện đủ dữ liệu**: `POST /api/tools/customer-history` → 200 kèm số dư ví + giao dịch gần đây khi CHƯA xác thực OTP | curl USR-0001 |
| `lookup-transaction` thiếu tham số | **500 Internal Server Error** (xem M-09) | curl |
| Container | backend 14/08 00:44 (healthy) · **frontend 13/08 15:50 — chưa rebuild** | `docker inspect` |

## 1. Bảng nghiệm thu — bước bấm cụ thể × kỳ vọng

### V3 — số tiền đề xuất (ưu tiên cao nhất, chạm tiền)

| # | Bước | Kỳ vọng | Kết quả |
|---|---|---|---|
| V3.1 | CSKH `0353000201` mở ticket có giao dịch → xem form đề xuất | Ô số tiền **đã điền sẵn** đúng số tiền giao dịch gắn với ticket | ⬜ |
| V3.2a | Trình đề xuất `amount = 0` | Backend **chặn**, thông báo tiếng Việt đọc được, **không** `[object Object]`, **không** tạo resolution | ⬜ |
| V3.2b | Trình đề xuất `amount = -1000` | nt | ⬜ |
| V3.2c | Trình đề xuất `amount` **lớn hơn** số tiền giao dịch | nt (xem ghi chú mâu thuẫn bên dưới) | ⬜ |
| V3.2d | Trình đề xuất `amount` **hợp lệ** | Vẫn tạo được bình thường — chặn không được làm hỏng đường đúng | ⬜ |
| V3.3 | Xem lại DB + màn `/approve` | **Không còn** dòng `amount = 6` nào | ⬜ |

> ⚠️ **Điểm chưa rõ, phải hỏi trước khi phán V3.2c:** luật "amount ≤ số tiền
> giao dịch được trích" định nghĩa thế nào khi ticket gắn **nhiều** giao dịch?
> Case demo **D4 là `double_charge`** — khách bị trừ **hai** lần 852.000đ; số
> tiền hoàn hợp lệ là 852.000đ (một lần), nhưng nếu luật so với *tổng* hai
> giao dịch thì 1.704.000đ cũng lọt. Chưa chốt thì tôi ghi ĐẠT/KHÔNG kèm
> nguyên văn hành vi quan sát được, không tự suy ra ý định.

### V1 — đường tới nút duyệt

| # | Bước | Kỳ vọng | Kết quả |
|---|---|---|---|
| V1.1 | Sếp `0905000205` mở ticket detail | Banner có **nút/link bấm được** "Mở trang Phê duyệt →" tới `/approve` | ⬜ |
| V1.2 | Vào `/approve` | Danh sách **hiện** đề xuất `pending_approval` | ✅ **đã trả lời trước: API trả đủ 3/3, không rỗng** |
| V1.3 | Xin OTP duyệt → duyệt | `status → approved`, DB có `approved_by` đúng người | ⬜ |
| V1.4 | (âm bản) duyệt khi chưa xin OTP | Bị chặn, thông báo sạch | ⬜ |
| V1.5 | Nút duyệt **không** xuất hiện trên ticket detail | Tách trang là thiết kế có chủ đích (OTP dynamic linking) — nếu nút duyệt trực tiếp xuất hiện ở đây là **sai** | ⬜ |

### V6 — rail giao dịch gate theo OTP (frontend-only)

| # | Bước | Kỳ vọng | Kết quả |
|---|---|---|---|
| V6.1 | Khách MỚI đăng nhập, **chưa** OTP → nhìn rail | Không hiện giao dịch; có placeholder + nút mở luồng OTP | ⬜ |
| V6.2 | Xác thực OTP xong | Rail hiện lại bình thường | ⬜ |
| V6.3 | API `POST /api/tools/customer-history` chưa OTP | **VẪN trả 200 kèm dữ liệu** — đúng chủ đích, vì fix là frontend-only. Nếu API đổi hành vi = coder đã đụng backend/contract ngoài phạm vi → **báo PO** | ⬜ |

### V5 (chỉ nếu coder làm) — không bắt gõ lại sau OTP

| # | Bước | Kỳ vọng | Kết quả |
|---|---|---|---|
| V5.1 | Phiên mới, gõ "mình chuyển nhầm …" **trước** OTP → bị chặn → xác thực | Agent **tự tra tiếp**, không bắt gõ lại | ⬜ |
| V5.2 | Nhìn khung chat sau khi tự chạy tiếp | **Không** bubble trùng, không gửi lặp tin | ⬜ |
| V5.3 | Nhánh thường (OTP trước, chat sau), chạy 2 lần | Không đổi hành vi, không gửi trùng | ⬜ |

### V4 (chỉ nếu coder làm) — trail không còn `null` trần

| # | Bước | Kỳ vọng | Kết quả |
|---|---|---|---|
| V4.1 | Mở investigation trail của ticket có lượt bị chặn OTP | Ghi "bị chặn — cần OTP phiên", không phải `kết quả: null` | ⬜ |

### V2 — nghiệm thu NGƯỢC (xác nhận KHÔNG có gì đổi)

| # | Bước | Kỳ vọng | Kết quả |
|---|---|---|---|
| V2.1 | DB: `TXN20260730000514` | vẫn `status = refunded` (seed thật, UI hiển thị đúng) | ⬜ |
| V2.2 | Không có commit nào đụng đường hiển thị status | Nếu có = ngoài phạm vi, báo PO | ⬜ |

### Hồi quy nhanh (sau khi coder rebuild)

| # | Lệnh | Kỳ vọng | Kết quả |
|---|---|---|---|
| R1 | `pytest tests/test_invariants.py` | 19/19 | ⬜ |
| R2 | `npx playwright test --config=playwright.livechat.config.ts` | Không tệ hơn mốc: 4 pass / 2 fail đã biết (QA-14 ô nhập · L4-06 login timeout) | ⬜ |
| R3 | D2 chạy 1 lần | Nói rõ không tìm thấy, 0 số bịa, ~3–9s | ⬜ |
| R4 | D4 chạy 1 lần đúng lời thoại | Tạo ticket + vào hàng chờ CSKH, ~8,2s±  | ⬜ |
| R5 | **Verify code mới CÓ trong container** | grep trong container, không tin "build thành công" | ⬜ |

## 2. Ngân sách phải giữ

- **Không** tạo ticket rác cho `USR-0145` (hàng chờ sẽ chiếu lên màn hình).
  Mọi bước phá dùng `USR-0001` (`0387000001`).
- Live-chat **60 tin/giờ/người** — chạy `live-chat.spec.ts` đúng **một lần**.
- Nếu bước V3.2 tạo ra resolution rác (vì backend chưa chặn), **ghi lại mã và
  báo PO dọn** — không tự chạy UPDATE/DELETE.

## 3. Phát hiện mới trong lúc chuẩn bị (chưa sửa gì)

### M-09 · `POST /tools/lookup_transaction` trả 500 trần khi thiếu tham số

| Đầu vào | Trả về |
|---|---|
| `{"trans_id": "TXN20260801000466"}` | 200 · `status=found` ✅ |
| `{"trans_id": "TXN99999999999999"}` | 200 · `status=not_found` ✅ |
| `{}` (rỗng) | **500 · `{"detail":"Internal Server Error"}`** ❌ |
| `{"phone": "0387000001"}` (thiếu amount) | **500** ❌ |

Vi phạm contract có dẫn nguồn — `contracts/agent-tools.yaml`,
`lookup_transaction`: *"Cần ÍT NHẤT một trong: trans_id · rec_code · (phone
kèm amount). Thiếu cả ba → `status='error'`, không đoán."* Phải là `error` có
thông báo, không phải 500 trần (lộ lỗi hệ thống ra client).

**Có chặn demo không: KHÔNG.** Luồng demo không đi qua đây (agent gọi qua lớp
bọc tool; rail luôn gửi đủ tham số). Ghi nhận để xử sau demo — cùng khu vực
với finding IDOR/BOLA đang `xfail` ở route này.

### M-08 · (theo brief V2) case eval còn thiếu — agent không cảnh báo giao dịch đã `refunded`

Hành vi đúng: thấy `status=refunded` → nói rõ "giao dịch này đã được hoàn tiền
lúc X" rồi hỏi khách còn muốn khiếu nại không, thay vì tạo thẳng ticket
"chuyển nhầm". Tôi sẽ thêm case vào bộ eval **sau demo** (vùng `eval/`), không
chạm gì tối nay.

---

# KẾT QUẢ NGHIỆM THU (chạy thật sau khi coder báo xong)

**Xác minh code TRONG container trước tiên** (không tin "build thành công"):
`docker exec` thấy đủ — backend có `if amount is None or amount <= 0`;
frontend build có cả `"Mở trang Phê duyệt"` lẫn `"Xác thực OTP để xem"`.
Container: backend 07:31 (healthy) · frontend 07:34 — cả hai đều mới hơn
commit `fc38ee6`.

## Bảng kết quả

| Mục | Kết quả | Bằng chứng |
|---|---|---|
| **V3.1** prefill | ✅ ĐẠT (gián tiếp) | Dòng 6đ đã về đúng 107.000đ = số tiền giao dịch của ticket |
| **V3.2a** amount=0 | ✅ ĐẠT | 400 · *"Số tiền hoàn phải lớn hơn 0 — không đề xuất hoàn tiền mà thiếu số tiền"* |
| **V3.2b** amount=-1000 | ✅ ĐẠT | 400 · cùng thông báo |
| **V3.2c** vượt số tiền GD | ✅ ĐẠT | 400 · *"Số tiền hoàn (999,999,999đ) vượt quá số tiền giao dịch TXN20260801000309 (209,000đ) — không hoàn nhiều hơn số đã trừ"* — trích đúng mã GD |
| **V3.2d** đường hợp lệ | ✅ ĐẠT | Hoàn đủ (209.000đ) và hoàn một phần (100.000đ) đều tạo được → guard không chặn nhầm |
| — không tạo rác | ✅ | pending 3 → 5 (chỉ 2 lần hợp lệ), 3 lần bị chặn không sinh bản ghi nào |
| — `[object Object]` | ✅ không xuất hiện lần nào | grep 0 |
| **V3.3** dọn dòng 6đ | ✅ ĐẠT | `RES-b8d2c7798d53` = 107000 · không còn resolution nào < 1.000đ |
| **V1.1** link "Mở trang Phê duyệt" | ✅ ĐẠT | Chuỗi có trong bundle frontend đang chạy |
| **V1.2** `/approve` có dữ liệu | ✅ ĐẠT | API trả đủ 3/3 `pending_approval`, khớp DB |
| **V1.3** xin OTP → duyệt | ✅ ĐẠT | 200 · `approved_by=USR-0205` · `approved_at` có |
| **V1.4** duyệt khi chưa OTP | ✅ ĐẠT | 403 · thông báo tiếng Việt rõ |
| — nhánh từ chối | ✅ ĐẠT | 200 · `rejected`, không cần OTP (đúng contract) |
| **V6.1** chưa OTP → placeholder | ✅ ĐẠT | Trình duyệt thật: placeholder hiện, **0** mã TXN lộ, `.txn-item = 0` |
| **V6.2** OTP xong → rail hiện | ✅ ĐẠT | Bấm "Xác thực ngay" → điền OTP → **`.txn-item = 20`**, placeholder biến mất |
| **V6.3** API giữ nguyên | ✅ ĐẠT | `customer-history` vẫn 200 khi chưa OTP → đúng "frontend-only", không đụng backend/contract |
| **V5** tự gửi lại sau OTP | ⬜ KHÔNG LÀM | Không có chuỗi đặc trưng trong container — đúng điều kiện an toàn của brief |
| **V4** trail hết `null` | ⬜ KHÔNG LÀM | nt |
| **V2** không đổi gì | ✅ ĐẠT | `TXN20260730000514` vẫn `refunded`; không file `contracts/`/`tests/`/`eval/` nào bị đụng |

## Hồi quy

| # | Kết quả |
|---|---|
| R1 bất biến | **19/19 xanh** |
| R1 full suite | **319 passed · 2 failed** · 3 skipped · 2 xfailed (chi tiết dưới) |
| R2 live-chat e2e | **4 pass / 2 fail** — đúng bằng mốc sáng nay, không tệ hơn (QA-14 ô nhập · L4-06 login timeout) |
| R3 · D2 | ✅ 8,2s · nói rõ không tìm thấy · **0 số bịa** · không lộ tên |
| R4 · D4 | ✅ 12,6s · tạo ticket ngay lượt 1 (`TCK-d64828bc6609`) |
| R5 verify container | ✅ cả 3 fix có mặt thật |

**2 test đỏ:**
1. `test_live_chat_pii_gap` — **đỏ có chủ đích** (ST2-P0-3, chờ PO quyết).
2. `test_reporting.py::test_pct_ai_proposal_approved_counts_only_decided_resolutions`
   — **đỏ MỚI**, đúng như coder khai. Đã kiểm: **không phải lỗi sản phẩm**, là
   fixture cũ — 4 lời gọi `propose_resolution(action_type="refund_to_wallet")`
   ở dòng 44–47 không truyền `amount`, nay bị luật V3.2 chặn đúng. Sửa =
   thêm `amount=` vào 4 dòng. **Tôi KHÔNG sửa** (quy tắc đợt này: chỉ báo
   cáo). Không ảnh hưởng container đang chạy.

## Phát hiện mới

### M-10 · P2 — F5 sau khi OTP xong thì rail biến mất trở lại
Đo bằng trình duyệt thật: OTP xong → rail hiện 20 giao dịch → **F5** →
`.txn-item = 0`, placeholder quay lại, dù phiên vẫn còn hạn OTP ở backend
(ngưỡng xem là 12h). Cổng chặn dựa vào state client, không đọc lại trạng thái
OTP thật của phiên sau khi tải lại trang.
**Không chặn demo** (đừng F5 ở màn chat; nếu lỡ F5 thì bấm "Xác thực ngay"
lại, mất ~10 giây). Sau demo nên cho rail đọc `otp_verified_at` từ phiên.

### M-09 · P3 — `lookup_transaction` trả 500 khi thiếu tham số (đã báo ở phần chuẩn bị)
Vi phạm `contracts/agent-tools.yaml` (phải là `status='error'`). Không chặn demo.

### Quan sát cho người demo
- **D4 lượt này KHÔNG mở đầu bằng câu đồng cảm** ("Mình đã tạo hồ sơ…" thay vì
  "Mình hiểu…"). Đã thấy 2/5 lần chạy — không tất định, không sai dữ liệu.
- D4 vừa tạo thêm 1 ticket cho `USR-0145` (`TCK-d64828bc6609`) — khách demo
  giờ có 9 khiếu nại; khi hỏi "tình trạng khiếu nại", agent sẽ đọc con số này.

---

# HOTFIX 2 — phần CHUẨN BỊ (coder chưa bắt đầu: commit mới nhất `18c5107` chỉ là brief, frontend vẫn build 07:34)

## Mốc "TRƯỚC hotfix 2" (đo bằng trình duyệt thật, vai sếp `0905000205`)

| Hạng mục | Trạng thái trước |
|---|---|
| Nav của sếp | **ĐÃ CÓ đủ 3 tab**: Phê duyệt · Báo cáo vận hành · **Tra cứu chính sách** |
| `/approve` | Có **nút "Duyệt"/"Từ chối" trực tiếp trên card** (3 cặp = 3 item chờ) — đúng thứ hotfix 2 muốn bỏ |
| Link tới chi tiết | Card đã có link `TCK-…` bấm được |

## 🔴 HAI CHẶN CHO MỤC B1 — báo trước khi coder bắt tay, kẻo sửa nhầm chỗ

**Chặn 1 — tab đã có, nhưng ROUTE đá sếp ngược lại.**
Bấm "Tra cứu chính sách" → URL **vẫn ở `/approve`**. Vào thẳng
`https://localhost/policy-lookup` bằng vai sếp → **bị chuyển về `/approve`**.
Trong khi backend cho phép: `POST /api/policy-search` với token sếp trả
**HTTP 200** (đúng `authority-matrix.yaml`: `roles: [cskh, supervisor]`).
⇒ Chẩn đoán "chỉ thiếu tab ở nav" **không đúng**: tab đã có sẵn và đang dẫn
tới hư không. Chỗ phải sửa là **guard của route `/policy-lookup`**, không
phải thêm tab.

**Chặn 2 — kho chính sách RỖNG.**
`policy_documents = 0` · `policy_chunks = 0`. Bốn truy vấn thử ("hoàn tiền",
"phí giao dịch", "chính sách", "khiếu nại") đều trả `status=not_found`,
`results: []`.
⇒ Tiêu chí B1 "tra 1 câu FAQ **ra kết quả**" **không thể đạt** dù sửa xong
route — không có tài liệu nào để tìm. Muốn demo bước này thì PO phải nạp tài
liệu chính sách qua `partner_admin` trước.
⇒ Liên đới: US-002 ("AI trả lời theo tài liệu thật của ví") **không demo
được**. Nếu khách hỏi chính sách, agent sẽ nói "không có thông tin" — đúng
hành vi (CTRL-002 cấm bịa chính sách), nhưng người demo **không được hứa**
sản phẩm có knowledge base.

## Việc PO giao riêng (ngoại lệ "không sửa") — ĐÃ XONG

Sửa fixture `test_reporting.py` (thêm `amount=` vào 4 lời gọi, dòng 44–47).
Đã xác nhận trước khi sửa: test kiểm `pct_ai_proposal_approved == 66.7`
(**tỉ lệ duyệt**), không kiểm số tiền → thêm `amount` không đổi thứ nó canh.
Số tiền truyền vào khớp đúng giao dịch trong `conftest` (270.000 · 500.000 ·
500.000 · 100.000 cho ticket không có trans_id).
**Kết quả: full suite `320 passed` · 3 skipped · 2 xfailed · 1 đỏ có chủ đích
(ST2-P0-3)** — đúng con số PO kỳ vọng. ruff sạch.

---

# HOTFIX 2 — KẾT QUẢ NGHIỆM THU ĐỘC LẬP (Mục B)

Container: frontend **08:53** (sau `6c0684c`/`d0baf35`) · backend 07:31 healthy ·
kho RAG **2 tài liệu / 338 chunk**.

| Mục | Kết quả | Bằng chứng |
|---|---|---|
| **B1** sếp tra cứu chính sách | ✅ ĐẠT | Bấm tab → vào đúng `/policy-lookup` (trước hotfix bị đá về `/approve`); tra "chuyển nhầm tiền thì xử lý thế nào" → **ra trích đoạn nguyên văn từ `MoMo_FAQ_Giao_dich.pdf`** |
| **B2** card không còn nút duyệt | ✅ ĐẠT | Nút trên `/approve` chỉ còn `["Chế độ tối","Đăng xuất"]` — **không còn Duyệt/Từ chối trực tiếp** (trước hotfix có 3 cặp) |
| **B2** "Mở chi tiết →" | ✅ ĐẠT | Link có, bấm tới đúng ticket của card (`TCK-518527ab869f`) |
| **B3** sếp thấy đủ căn cứ | ✅ ĐẠT | Ticket detail vai sếp: **khối duyệt + trail + đề xuất** đều hiện |
| **B3** xin OTP → duyệt | ✅ ĐẠT | 200 · `status=approved` · `approved_by=USR-0205` trong DB |
| **B3** nhánh từ chối | ✅ ĐẠT | 200 · `status=rejected` |
| **B3** duyệt thiếu OTP | ✅ ĐẠT | 403 · thông báo tiếng Việt rõ |
| **B4** CSKH mở cùng ticket | ✅ ĐẠT | Thấy trail + đề xuất, **KHÔNG có khối duyệt** |
| **B4** khách mở cùng ticket | ✅ ĐẠT | Bị chặn hẳn, đá về `/chat` |
| **B4** API approve token CSKH | ✅ ĐẠT | **403** *"Cần role thuộc ['supervisor'], tài khoản hiện tại là cskh"* — reject cũng 403 (backend không đổi, đã xác nhận lại) |
| **B5** hàng chờ | ✅ ĐẠT | Đúng **3 item thật**: 323.000 · 178.000 · 107.000 |
| **B5** bất biến | ✅ **19/19** | |
| **B5** D2 / D4 | ✅ ĐẠT | D2 nói rõ không tìm thấy, 0 số bịa · D4 10,5s tạo ticket ngay lượt 1, **có câu đồng cảm** |

**Dấu vết tôi để lại — đã tự dọn:** 2 resolution thử (`RES-f746bbdb1f00`,
`RES-b9b1f9344dc6`) tạo trên ticket của `USR-0100`/`USR-0119` (không đụng
tài khoản demo), đã **duyệt một · từ chối một** → vừa nghiệm thu trọn 2 nhánh
B3 vừa đưa hàng chờ về lại đúng 3 item.
