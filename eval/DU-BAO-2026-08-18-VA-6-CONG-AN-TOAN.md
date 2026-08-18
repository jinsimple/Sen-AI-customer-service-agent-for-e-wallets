# DỰ BÁO — vá 6 cổng "TÊN hứa X, ASSERTION kiểm Y"

> Vai: **tester** · 18/08/2026 · **0 lượt LLM** · viết **TRƯỚC KHI CHẠM VẬT**.
> Việc: `eval/QUET-TEN-HUA-KHAC-ASSERTION.md` (`4ac2162`) — quét đã xong,
> **chưa vá**. File này là dự báo; kết quả thật ghi ở phần ⑤ **sau khi chạy**.
>
> Đèn xanh: PO-agent 18/08. Đường xác minh đã chốt: **venv host
> `P-121-new/.venv`** (Python 3.14.6, pytest 9.1.1) — né hẳn việc `tests/` nằm
> trong ảnh docker. **Không `docker cp`, không dựng ảnh** (Luật I).

## ⓪ Mẫu số — khai cùng dòng

```
6 ca đánh dấu / 79 file tests/ đã quét    ← mẫu số của PHÉP QUÉT (4ac2162)
5 ca / 6 nằm trên ĐƯỜNG DUYỆT HITL        ← ràng buộc cứng số 1
3 file bị sửa / 79                        ← mẫu số của ĐỢT VÁ này
0 dòng src/ · 0 dòng contracts/ bị chạm
```
⚠️ **6/79 KHÔNG phải "tỉ lệ test hỏng của dự án".** Tập quét chỉ gồm hàm có TÊN
chứa từ khoá an-toàn (tiêu chí ② của `4ac2162`). Ca mang tên trung tính mà
assertion vẫn lệch thì **bộ quét đó không nhìn tới** — đây là bộ lọc **vô hình**
của chính phép quét, khai ra theo §8 `docs/STATE.md`.

## ① Vật bị sửa — băm TRƯỚC khi chạm

Ghi lúc `git status --short -- tests/ eval/` sạch (trừ chính file này).
Băm sẽ được in ở phần ⑤ khi chạy, để người sau đối chiếu được rằng dự báo này
viết trước bản vá chứ không phải viết ngược lại sau khi thấy màu.

## ② Bản vá — mỗi ca một dòng, và LÝ LẼ của trục được chọn

Trục chọn để bám: **`resolutions.status` + trường người-duyệt**, vì
`contracts/resolution-state-machine.yaml` khai đúng nó là mốc chung cuộc:

- `invariant_db` **BR-10** `ck_resolutions_approved_requires_approver_br10`:
  `(status != 'approved') OR (approved_by IS NOT NULL AND approved_at IS NOT NULL)`
- `transitions`: **CỬA DUY NHẤT** tới `approved` là `pending_approval → approved`
  qua `POST /resolutions/{id}/approve`, `boi: [supervisor]`, `cham_tien: true`
- Contract §câu hỏi mở khai rõ: **chưa có state `executed`** — hệ thống dừng ở
  `approved`. ⟹ `status='approved'` **CHÍNH LÀ** hậu quả tài chính quan sát
  được; không có vật nào "sâu hơn" để bám. Đây là lý do trục này ĐỦ, không phải
  lựa chọn cho tiện.

| # | ca | file:dòng | thêm gì |
|---|---|---|---|
| 1 | `approve_without_requesting_otp_first_is_rejected` | `test_resolution_approval_otp.py:65` | sau 403: `status == "pending_approval"` **và** `approved_by is None` |
| 2 | `otp_from_one_resolution…different_resolution` | `:77` | như trên, cho **resolution B**, **ngay sau** 403 và **trước** lượt đối chứng duyệt A |
| 3 | `stale_approval_otp_beyond_freshness_window_rejected` | `:149` | như trên |
| 4 | `wrong_otp_code_rejected` | `:179` | như trên |
| 5 | `sec_a_cskh_khong_duoc_reject` | `test_resolution_reject.py:138` | sau 403: `status == "pending_approval"` **và** `rejected_by is None` **và** `reject_reason is None` |
| 6 | `path_traversal_filename_is_safe` | `test_injection.py:113` | **KHÔNG phải một dòng** — xem ④ |

**Vì sao cặp `(status, approved_by)` chứ không chỉ `status`:** Luật D — cột
phòng thủ phải có nguồn độc lập. `status` do tầng application ghi; `approved_by`
bị **CHECK constraint tầng DB** ràng. Một đường lách chỉ chỉnh `status` sẽ vỡ ở
vế thứ hai, và ngược lại.

**Vì sao KHÔNG bám `Δ` ("trạng thái không đổi"):** Luật 1 — `Δ=0` là trạng thái
mặc định. Bám **mốc tường minh** `== "pending_approval"`: nếu hạt giống
`propose_resolution` đổi mặc định, ca này **kêu** thay vì im.

## ③ 🔴 Điều bản vá này KHÔNG chứng minh — khai trước, không khai sau

`status` giữ `pending_approval` sau một 403 **cũng đúng** khi request chết sớm ở
tầng N-1 và **chưa từng chạm** guard. Đây đúng là biến thể ① của Luật 1, và
`test_sec_b` trong cùng repo đã mắc đúng nó một lần.

**Bản vá này KHÔNG tự chữa được điều đó.** Nó bịt trục *"403 rồi vẫn duyệt"*,
**không** bịt trục *"403 vì lý do khác"*. Vế sau đã được canh bởi **ca đối
chứng dương** có sẵn trong cùng file — `test_approve_with_correct_fresh_otp_succeeds`
(`:135`) chứng minh đường duyệt **đi được** khi mọi điều kiện đúng ⟹ 403 của 4
ca kia không thể là "route chết cứng". Tôi **không** thêm đối chứng mới cho ca
1–5; tôi khai rằng nó **đã có sẵn** và đó là lý do đủ.

Ca 5 (`reject`): đối chứng dương tương ứng là
`test_sec_a_reject_tu_trang_thai_khac_pending_bi_tu_choi` + happy-path ở
`test_resolution_approval.py`. **Chưa đọc file sau ⟹ ghi là CHƯA XÁC MINH**, sẽ
kiểm khi chạy.

## ④ Ca 6 (traversal) — 🔴 CÓ BẪY CHÂN KHÔNG, cần đối chứng dương

Assertion *"không tệp nào ghi ra ngoài thư mục kho"* sẽ **xanh vĩnh viễn** nếu
`ingest_document` **không ghi tệp nào cả** (rất có thể — nó nạp vào Chroma).
Xanh-vì-không-có-gì-xảy-ra là **đúng Luật 1**, và nó sẽ trông y hệt xanh-vì-an-toàn.

⟹ Ca 6 **bắt buộc** gồm hai nửa, không tách được:
- **nửa đối chứng:** nạp một tệp tên LÀNH (`chinh-sach-hoan-tien.txt`) ⟹ phải
  quan sát được **một dấu vết thật** (hàng `policy_documents`). Không có dấu vết
  ⟹ kênh quan sát chết ⟹ ca phải báo **KHÔNG ĐO ĐƯỢC**, không được báo ĐẠT.
- **nửa tấn công:** `../../../../etc/passwd.txt` ⟹ (a) không tệp mới nào xuất
  hiện ngoài gốc repo tại 4 mức tổ tiên mà payload nhắm tới; (b) nếu có hàng
  `policy_documents` được tạo, `filename` của nó **không chứa** `/` hay `..`.

**(b) là phần thật sự mang tên ca.** Một tên còn nguyên `../../../../` nằm
trong DB chưa phải lỗ hổng hôm nay, nhưng nó là **tiền đề** của lỗ hổng ngày
bất kỳ ai nối nó vào một đường ghi đĩa. Nếu (b) đỏ ⟹ **finding, báo PO-agent,
KHÔNG tự sửa `src/`** và **KHÔNG nới assertion cho xanh**.

## ⑤ DỰ BÁO — cổng nào xanh/đỏ/skip, và ĐỘ CHẮC

**Nền (trước khi vá): 6/6 XANH.** Chúng đang xanh trong suite bàn giao; bản vá
chưa chạm nên không có lý do để khác.

| # | ca | dự báo SAU vá | độ chắc | lý lẽ |
|---|---|---|---|---|
| 1 | approve thiếu OTP | 🟢 XANH | **cao** | `session_id` không tồn tại ⟹ chết ở tra phiên, không thể tới bước ghi |
| 2 | OTP của case A duyệt case B | 🟢 XANH | **cao** | ca này đã có đối chứng 200 ngay trong thân ⟹ đường ghi chứng minh được là sống, mà B vẫn không đổi |
| 3 | OTP quá hạn tươi | 🟢 XANH | **trung bình** | phiên **có thật** và `otp_status='verified'` — chỉ trượt ở phép so thời gian. Đây là ca **gần đường ghi nhất** trong 4 ca OTP |
| 4 | mã OTP sai | 🟢 XANH | **cao** | so mã là cửa cổ điển nhất |
| 5 | CSKH reject | 🟢 XANH | **rất cao** | chặn ở `require_role()`, tức tầng route — xa đường ghi nhất. `test_invariants` đã introspect chính guard này |
| 6a | traversal — đối chứng dương | 🟢 XANH | **trung bình** | nếu ĐỎ ⟹ kênh quan sát sai, **không phải** lỗ hổng |
| 6b | traversal — tên tệp bị giam | ❓ **KHÔNG DỰ BÁO** | — | tôi chưa đọc `src/` và **không được đọc**. Đây là ca duy nhất mang thông tin thật |

🔴 **Khai trước, theo nếp đã trúng 6/6 và 2/2:** một kết quả **THUẬN LỢI (6/6
xanh) KHÔNG được tính là xác nhận** rằng 6 cổng này nay tốt. Nó chỉ xác nhận
**một** mệnh đề hẹp: *"trên 6 đường này, một request bị từ chối không để lại
thay đổi ở mốc chung cuộc"*. Nó **không** nói gì về các đường chưa quét, và
**không** nâng 6 ô trong bảng an toàn từ "đang canh một nửa" lên "đã canh trọn"
— nó nâng lên **"đã canh đúng trục tên nó hứa"**, một mệnh đề nhỏ hơn hẳn.

## ⑥ 🔴 NẾU KHÁC DỰ BÁO THÌ NGHI GÌ

| quan sát | nghi ĐẦU TIÊN | nghi THỨ HAI | cách phân định |
|---|---|---|---|
| ca 1–5 ĐỎ ở vế `status == "pending_approval"` **với giá trị `approved`/`rejected`** | 🔴 **THỦNG HITL THẬT** — 403 trả về nhưng hành động đã xảy ra. Ràng buộc cứng 1. **Dừng, báo PO-agent ngay, không sửa test** | rollback không sạch ở tầng session (fixture `client` commit ở `_override_session`) | đọc `approved_by`: **có tên** ⟹ đường duyệt thật đã chạy; **None** ⟹ ghi lạc, nghi rollback |
| ca 1–5 ĐỎ với giá trị **`draft`** hoặc khác cả ba | hạt giống `propose_resolution` đổi mặc định | contract lệch code (`check_contracts` phải bắt) | chạy `python scripts/check_contracts.py` |
| ca 1–5 ĐỎ **ở vế mã 403** (chưa tới assertion mới) | **tôi làm hỏng test** khi sửa | tech-lead vừa land bất biến chống livelock chạm route | `git stash -- tests/` **có pathspec**, chạy lại nền |
| ca 6a ĐỎ (không có hàng `policy_documents`) | tệp `.txt` lành bị từ chối vì lý do khác (magic bytes / kích thước) | kênh quan sát sai bảng | in `resp.status_code` + body; **báo KHÔNG ĐO ĐƯỢC**, không báo ĐẠT |
| ca 6b ĐỎ | **finding thật** — tên chưa được giam | tên bị giam ở tầng khác mà DB vẫn giữ bản thô để hiển thị | báo PO-agent → tech-lead. **Không nới assertion** |
| **cả 6 xanh ngay lần đầu, không một ca nào lay động** | đúng như dự báo | 🔴 **hoặc bản vá chưa thật sự chạy** (Luật "KHAI ≠ CHẠY") | đọc **SỐ CA CHẠY**, không đọc màu; và cố ý làm ĐỘT BIẾN một assertion mới để xác nhận nó **biết đỏ** |
| suite báo `skipped` ở 3 file này | ❌ **không được phép** — 3 file này **không gọi model** | `_dong_bang` bị import nhầm vào | `grep _ton_tien tests/test_api/` phải rỗng |

## ⑦ Phép kiểm cuối, bắt buộc — Luật J (PO-agent cấp số hiệu 18/08)

> *Vá đúng một lỗi có thể làm IM một cổng đang hỏng vì lý do khác.*

Với **mỗi** ca chuyển màu, tôi phải đọc **cổng đó nay khẳng định CÁI GÌ**, không
chỉ ghi nhận nó xanh. Và với 6 assertion mới, tôi sẽ chạy **một lượt đột biến**
(cố ý lật một assertion mới thành sai) để chứng minh chúng **biết đỏ** — vì một
assertion mới toanh chưa bao giờ đỏ thì chưa ai biết nó có nối vào vật hay không.

## ⑧ Trạng thái thứ ba

Kết quả sẽ báo theo **BA** trạng thái: `ĐẠT` · `TRƯỢT` · `KHÔNG ĐO ĐƯỢC`.
Ca 6a rơi vào rổ ba là **kết quả hợp lệ**, không phải thất bại của phép thử.

---

# ⑨ KẾT QUẢ THẬT — ghi SAU khi chạy, 18/08

Dự báo ở trên nằm trong commit `e8d4541`, **trước** mọi dòng vá. Băm đối chiếu:

```
                                                 TRƯỚC vá      SAU vá
test_api/test_resolution_approval_otp.py        ce1a135ea7a5  749c0fef8ff3
test_api/test_resolution_reject.py              d1175f4d9189  4e6a8a4bc550
test_api/test_injection.py                      4b17df02bead  f7839e4aa4ca
```

**Nền (trước vá, 3 file):** `25 passed` — khớp dự báo *"6/6 xanh"*.
**Chốt (sau vá, 3 file):** `25 passed · 1 xfailed`.

## Bảng đối chiếu dự báo × thực tế

| # | ca | dự báo | thực tế | đọc |
|---|---|---|---|---|
| 1 | approve thiếu OTP | 🟢 | ⚠️ **KHÔNG ĐO ĐƯỢC** rồi 🟢 sau khi sửa hạt giống | **dự báo TRẬT** — xem ⑩ |
| 2 | OTP của A duyệt B | 🟢 | 🟢 | trúng |
| 3 | OTP quá hạn tươi | 🟢 | 🟢 | trúng |
| 4 | mã OTP sai | 🟢 | 🟢 | trúng |
| 5 | CSKH reject | 🟢 | 🟢 | trúng |
| 6a | traversal — đối chứng dương + không thoát đĩa | 🟢 | 🟢 | trúng |
| 6b | traversal — tên bị giam | ❓ không dự báo | 🔴 **TRƯỢT — FINDING** | xem ⑪ |

**5/6 trúng · 1 trật · 1 ô cố ý bỏ trống và ô đó chính là ô mang thông tin.**

## ⑩ Ca 1 trật — và nó là ca CÓ GIÁ NHẤT của đợt

Ca 1 không đỏ vì thủng HITL. Nó báo **KHÔNG ĐO ĐƯỢC**: `sample_db.get(...)`
trả `None`. Cơ chế: fixture `client` dùng CHUNG session với route, và
`_override_session` **rollback** khi route ném `HTTPException` ⟹ hạt giống chưa
commit bị chính cú rollback ấy cuốn đi.

> 🔴 **Ba ca OTP còn lại quan sát được là nhờ MAY, không nhờ thiết kế**: chúng
> có một request `request-approval-otp` **thành công** commit hộ trước đó. Nếu
> tôi chỉ vá 3 ca ấy, cả ba xanh, và tôi sẽ báo cáo "đã canh" cho một khuôn mà
> ca thứ tư chứng minh là **không tự đứng được**.

Vá: `_make_resolution` commit hạt giống ⟹ khả năng quan sát thành **tất định**.
Điều này chỉ lộ ra vì helper có **trạng thái thứ ba** — một helper chỉ biết
ĐẠT/TRƯỢT đã báo TRƯỢT và đẩy cả đội đi truy một vụ thủng HITL không tồn tại.

## ⑪ Ca 6b — FINDING, không vá, không nới assertion

`policy_documents.filename` lưu **nguyên văn** `'../../../../etc/passwd.txt'`
(HTTP 200, `chunk_count: 1`, `status: indexed`).

Xử lý theo đúng dự báo ⑥: **không sửa `src/`, không nới assertion**. Ca gốc
được **TÁCH ĐÔI**:
- `..._khong_ghi_tep_ra_ngoai_repo` — 🟢 ở cổng chính, canh 12 đích thoát
- `..._ten_tep_da_luu_phai_bi_giam` — `xfail(strict=True)`, **cố ý KHÔNG gắn
  `security_finding`** (chưa có đồng thuận về mức độ; tiền lệ:
  `test_tools_rest_parity.py:25`)

**Vì sao tách chứ không gộp rồi gắn nhãn — Luật J:** gộp thì cả nửa ĐANG CANH
ĐƯỢC cũng bị ẩn khỏi `lint-and-test`. Bản vá sẽ làm im một phép kiểm đang chạy tốt.

## ⑫ Phép ĐỘT BIẾN — 6 assertion mới có BIẾT ĐỎ không

Đổi mốc `"pending_approval"` → `"DOT-BIEN-KHONG-TON-TAI"` ở cả 2 file:

```
5 failed, 10 passed   ← ĐÚNG 5 ca đã vá đỏ, KHÔNG ca nào khác
hoàn nguyên: băm khớp lại 749c0fef8ff3 · 4e6a8a4bc550
```
⟹ 5 assertion HITL **nối thật vào vật**. Ca 6b tự chứng minh (nó đang đỏ thật).

## ⑬ 🔴 FINDING NGOÀI PHẠM VI — cổng chi phí thủng, mẫu số TOÀN BỘ `tests/`

PO-agent hỏi (⑤ tin 18/08): *mẫu số "3/3 bộ ĐÃ KHAI" chưa quét cả suite tìm bộ
thứ tư.* **Đã quét. Có bộ thứ tư.**

`tests/test_api/test_injection.py` gọi **OpenAI `/v1/embeddings` THẬT** qua
`POST /policy-docs` → ingest, và **KHÔNG qua `_ton_tien` lẫn `_dong_bang`**.
Bằng chứng đo được, không suy luận:
```
{"logger":"httpx","message":"HTTP Request: POST https://api.openai.com/v1/embeddings \"HTTP/1.1 200 OK\""}
{"logger":"fin05.rag","message":"policy_doc_nap","chunk_count":1,"status":"indexed"}
```

**Phép dò dùng — Luật 10d (vô hiệu hoá HẬU QUẢ trước, rồi mới thử cổng), 0 đồng:**
`OPENAI_API_KEY=sk-invalid` + `DASHSCOPE_API_KEY=sk-invalid` +
`FIN05_BASE_URL=https://127.0.0.1:9` rồi chạy **toàn bộ** `tests/`.

```
620 ca thu thập (566 passed · 2 failed · 40 skipped · 1 deselected · 11 xfailed)
ĐÚNG 1 lời gọi nhà cung cấp rời khỏi máy:  POST /v1/embeddings → 401
                                            nguồn: test_injection.py
```
**Đối chứng dương của chính phép dò:** file đã biết là gọi mạng thì kêu; 5 file
ứng viên khác (`test_authz_matrix` · `test_frontend_route_guards` ·
`test_rag/test_ingest` · `test_rag/test_parsers` · `test_invariants`) **vẫn
xanh** với khoá giả ⟹ chúng không gọi. Không có đối chứng này thì *"chỉ 1 kết
quả"* chỉ nghĩa là chưa nhìn kỹ (tiêu chí ④ của `4ac2162`).

### Mẫu số — khai đúng phạm vi, đây là chỗ dễ trích quá nhất

```
620/620 ca ĐÃ CHẠY qua phép dò          ← mẫu số THẬT
   1 file gọi nhà cung cấp không cổng
```
🔴 **Phép dò này chỉ bắt lời gọi Ở PHÍA HOST.** Đường đi **qua container** mang
khoá RIÊNG của container ⟹ khoá giả ở host **không chạm tới** (đúng bảng Luật
10d). Ba bộ đã khai đi đường đó và bị vô hiệu bằng `FIN05_BASE_URL` chết.
**`tests/test_rag/test_thanh_phan_tai_lieu_kho.py` chạy `docker exec` vào
container thật ⟹ nằm NGOÀI tầm phép dò này: KHÔNG ĐO ĐƯỢC, không được đọc
thành "đã sạch".**

### Hệ quả cần PO quyết — tôi KHÔNG tự làm

Gắn `_ton_tien` cho cả `test_injection.py` sẽ **skip luôn 10 ca appsec** không
tốn tiền (SQLi/XSS). Đó là đánh đổi độ phủ, **quyết định của PO, không phải
của tester**. Ba đường: gắn cổng cho riêng 2 ca `/policy-docs` · giả lập tầng
nhúng · để nguyên và ghi vào sổ nợ.

⚠️ Và đọc kèm: `.DANG-DONG-BANG-LLM` nay **tắt vĩnh viễn** (PO chốt 18/08) ⟹
lớp ① là lớp duy nhất còn lại — **mà chính lớp ① không phủ file này.**
Với `pytest tests/` hôm nay, **lượt nhúng vẫn bay ra ngoài dù cả hai lớp đều bật.**
