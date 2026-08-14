# Tiền-kiểm: nhịp migration `note` + F-11 + F-13 — điều kiện nghiệm thu

> Vai: **security** · 2026-08-14 · nhánh `dev/learning-loop`
> Viết **TRƯỚC khi coder chạm dữ liệu**, sau phán quyết PO (`1909c5a`).
> Nối tiếp `review-phase01-ap-that.md` (F-11…F-16) và sign-off TM-03.
>
> Lý do tài liệu này tồn tại: phán quyết của PO gộp **xoá dữ liệu** (F-11) với
> **backfill dữ liệu** (F-13) vào cùng một nhịp. Hai việc đó **không giao hoán**
> — chạy sai thứ tự sẽ tạo ra đúng loại dữ liệu kiểm toán tự mâu thuẫn mà cả
> hai việc sinh ra để dọn. Phát hiện bằng truy vấn dữ liệu thật, không phải
> suy luận.

---

## 1. BẪY THỨ TỰ — F-11 phải chạy TRƯỚC F-13 (bắt buộc)

**Dữ liệu thật:** `TCK-518527ab869f` có **đúng 2 resolution, và cả hai chính là
2 dòng residue QA mà PO ra lệnh xoá** (`RES-663769e6d9dc`, `RES-b9b1f9344dc6`).
Ticket này hiện `hitl_status='pending'` và nằm trong nhóm 8 dòng lệch của F-13.

| Thứ tự | Kết quả |
|---|---|
| F-13 trước, F-11 sau (SAI) | Ticket được set `hitl_status='rejected'`, rồi **cả hai resolution bị xoá** ⟹ ticket khẳng định một phán quyết HITL mà **không còn bản ghi nào chống đỡ**. Trái `dan_xuat.quy_tac` của contract v2.1.0 ("theo resolution MỚI NHẤT"; "ticket chưa có resolution nào vẫn là `pending`"), và là dữ liệu kiểm toán bịa đúng nghĩa. |
| **F-11 trước, F-13 sau (ĐÚNG)** | Xoá xong, ticket còn **0 resolution** ⟹ F-13 bỏ qua nó, `hitl_status` **giữ nguyên `pending`** — đúng contract. |

**Điều kiện nghiệm thu 1:** migration thực hiện theo thứ tự **xoá residue →
sentinel cho dòng genuine → backfill hitl_status**, trong **cùng một
transaction**. Nửa chừng hỏng phải rollback trọn, không để trạng thái lai.

## 2. Câu backfill F-13 phải bám "MỚI NHẤT", không phải "bất kỳ"

**Dữ liệu thật:** `TCK-173cee0218a0` có **2 resolution** (`approved@14/08 07:42`
và `approved@14/08 09:01`). Ticket nhiều resolution **đã tồn tại**, không phải
giả định. Một câu `UPDATE tickets ... FROM resolutions r WHERE r.ticket_id =
tickets.ticket_id AND r.status IN ('approved','rejected')` sẽ **không xác định**
khi hai resolution khác trạng thái — Postgres chọn dòng nào là tuỳ kế hoạch thực
thi. Hôm nay cả hai cùng `approved` nên không lộ; ngày mai lộ và sẽ lộ im lặng.

**Điều kiện nghiệm thu 2:** câu backfill phải chọn resolution mới nhất theo
đúng thứ tự mà `_dong_bo_hitl_status()` dùng ở runtime
(`ORDER BY created_at DESC, resolution_id DESC LIMIT 1`) — hai đường phải cho
cùng kết quả, nếu không thì dữ liệu lịch sử và dữ liệu mới sẽ theo hai luật khác
nhau. Và **chỉ** chuyển khi resolution mới nhất ở `approved`/`rejected`; ticket
mà resolution mới nhất còn `pending_approval` phải **giữ `pending`** (hiện có 3:
`TCK-8a4779f8861a`, `TCK-ddd78e22867f`, `TCK-4fea9a74557b`).

## 3. Trạng thái đích — assert được, dán vào commit

Sau nhịp này, các con số sau phải **đúng chính xác** (tester canh bằng test,
coder dán kết quả truy vấn thật vào commit message):

- `resolutions` theo status: **6 approved · 3 pending_approval · 1 rejected**
  (rejected giảm 3→1 sau khi xoá 2 dòng QA — đây là thay đổi **có chủ đích**,
  không phải dữ liệu trôi).
- Dòng rejected duy nhất còn lại là `RES-3b3026227331`, `rejected_by` = **id
  sentinel**, không phải `USR-0205`.
- Số ticket `hitl_status='pending'` mà resolution MỚI NHẤT đã
  `approved`/`rejected`: **0**.
- **Đúng 6 ticket đổi trạng thái**: 5 sang `approved` (`TCK-173cee0218a0`,
  `TCK-5ce978c5fd8b`, `TCK-5ff347d86281`, `TCK-77f6333334e2`,
  `TCK-cfd642f7461c`) và 1 sang `rejected` (`TCK-0e7f530fbd4f`).
- `TCK-518527ab869f`: **0 resolution, `hitl_status` vẫn `pending`**.
- Số hàng non-rejected mang nhãn từ chối: **0** (F-15 được PO chấp nhận là
  CHECK một chiều, nên đây là bất biến canh bằng dữ liệu, không bằng constraint).

**Đã kiểm trước:** `auth_sessions` (bảng DUY NHẤT có FK trỏ vào `resolutions`)
hiện **0 dòng** trỏ vào 2 resolution sắp xoá ⟹ xoá được, không cần dọn FK.
Nhưng migration vẫn phải xoá theo thứ tự an toàn phòng khi có challenge mới
sinh ra giữa lúc viết và lúc chạy.

## 4. Sentinel — điều kiện nghiệm thu (PO giao tôi rà cơ chế coder đề xuất)

Ràng buộc nền: `rejected_by` là FK tới `users` và CHECK br11 cấm NULL khi
`rejected='rejected'` (PO đã chốt **không nới br11**) ⟹ sentinel **buộc phải là
một dòng thật trong `users`**. Vì vậy nó phải được làm cho **vô hại**:

1. **Không đăng nhập được, chứng minh bằng chạy thật.** `password_hash` = NULL
   (đường login hiện tại: `password_ok` chỉ True khi `user.password_hash is not
   None` — `main.py:258-261`, nên NULL là an toàn *theo thiết kế hiện tại*).
   Nghiệm thu: gọi thật `POST /auth/login` với số điện thoại của sentinel →
   **401**, và không có refresh token nào cấp được.
2. **Không mang danh một con người.** `full_name` phải đọc ra là nhãn, không
   phải tên: ví dụ `[HỆ THỐNG] không xác định — backfill ADR-019`. Ai nhìn màn
   duyệt phải thấy ngay đây không phải người.
3. **Không lọt vào phép chọn tự động.** Chính câu SQL gây ra F-11 là
   `SELECT user_id FROM users WHERE role='supervisor' ORDER BY user_id LIMIT 1`.
   Nếu sentinel mang `role='supervisor'` và id sắp trước `USR-0205`, thì lần
   backfill sau lại vớ đúng nó — hoặc tệ hơn, một truy vấn nghiệp vụ nào đó
   coi nó là supervisor thật. **Coder phải nêu rõ chọn `role` nào và vì sao**;
   nếu chọn `supervisor` thì phải chỉ ra mọi nơi liệt kê supervisor đã loại trừ
   nó (báo cáo, danh sách người duyệt, UI phân công).
4. **Không vào thống kê người.** Mọi phép đếm theo `rejected_by`/`approved_by`
   (kể cả `/reports/summary` và các phép đo Phase 2/3) phải loại sentinel hoặc
   gộp nó thành nhóm "không xác định" — không được để nó thành một "supervisor"
   có 1 lần từ chối trong bảng hiệu suất.
5. **Ghi chú `rationale` nói đủ ba thứ.** Bản hiện tại chỉ khai *lý do* không
   được ghi lại; phải khai rõ **người và thời điểm cũng là suy ra**
   (`rejected_at` đang bằng đúng `created_at`). Thiếu câu này thì sentinel dọn
   được nửa vấn đề: người hết bịa, thời điểm vẫn bịa mà không ai biết.

## 5. `note` — nhắc lại 3 điều kiện chặn của sign-off

Không đổi so với `review-phase01-ap-that.md` (Nhiệm vụ 2), nhắc để rà một lượt:

1. **Scrub tại điểm GHI.** Nghiệm thu bằng **đọc thẳng DB**, không qua response
   API — bản trong DB phải là bản đã che.
2. **Fail-closed.** `scrub_pii` lỗi/timeout ⟹ từ chối ghi cả bản ghi, trả lỗi
   rõ. Không có đường nào ghi bản thô rồi hẹn che sau.
3. **Không mở rộng phạm vi đọc.** `note` chỉ ở route đã gated
   `cskh,supervisor`; không vào `/reports/summary`, không vào payload live-chat,
   không vào kết quả tool nào.

Khi coder nộp, tôi rà bằng probe thật đúng khuôn đã dùng ở
`review-phase01-ap-that.md` (dò trên REST **và** `build_customer_tools().invoke()`
— chuỗi thật đi vào prompt), cộng 3 mục sentinel ở §4 và trạng thái đích §3.
