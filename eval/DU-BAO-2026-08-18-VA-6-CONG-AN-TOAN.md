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
