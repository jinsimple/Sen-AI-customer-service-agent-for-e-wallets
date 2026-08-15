# Bản nộp AS-BUILT — nhịp migration F-11 · F-13 · F-14

> Người nộp: coder (tech-lead) · Ngày: 2026-08-15 · Người nhận: security
> PO yêu cầu soạn để security đối chiếu **thứ tự đã thực thi** với ràng buộc
> phi-giao-hoán trong `docs/security/pre-review-nhip-migration-note-f11-f13.md`.
>
> Mọi con số dưới đây **đo lại tại thời điểm viết**, trên DB Postgres đang chạy
> — không chép từ commit message. Migration head lúc đo: `e5f6a7b8c9d0`.
>
> **Phạm vi:** chỉ F-11 · F-13 · F-14. Field `note` (nhóm A, 15 test đỏ) **CHƯA
> LÀM**, chờ PO-5 chốt chính sách che PII — xem §5.

---

## 1. Thứ tự đã thực thi — đúng ràng buộc phi-giao-hoán

Tiền-kiểm §1 yêu cầu **xoá residue → sentinel → backfill**, trong **cùng một
transaction**. Đã thực thi đúng thứ tự đó trong `migrations/versions/
c3d4e5f6a7b8_f11_f13_don_du_lieu_hitl.py`, ba bước nằm trong một hàm `upgrade()`
(alembic trên Postgres bọc transaction sẵn).

**Bằng chứng thứ tự đúng, kiểm được bằng dữ liệu chứ không bằng đọc code:**

`TCK-518527ab869f` hiện có **0 resolution** và `hitl_status = 'pending'`.

Đây chính là ca mà security cảnh báo. Nếu backfill chạy TRƯỚC xoá, ticket này
đã bị set `hitl_status='rejected'` (vì lúc đó nó còn 2 resolution rejected), rồi
cả hai resolution bị xoá — để lại một ticket **khẳng định một phán quyết HITL mà
không còn bản ghi nào chống đỡ**. Trạng thái quan sát được hôm nay (`pending` +
0 resolution) chỉ có thể sinh ra nếu xoá chạy trước. Thứ tự sai sẽ để lại dấu
vết khác hẳn và không tự sửa được.

## 2. Trạng thái đích — đối chiếu từng dòng với tiền-kiểm §3

| Điều kiện (tiền-kiểm §3) | Yêu cầu | Đo được | |
|---|---|---|---|
| resolutions theo status | 6 approved · 3 pending_approval · 1 rejected | 6 · 3 · 1 | ✔ |
| dòng rejected còn lại | `RES-3b3026227331` | `RES-3b3026227331` | ✔ |
| `rejected_by` của dòng đó | id sentinel, KHÔNG phải `USR-0205` | `USR-SYS-UNKNOWN` | ✔ |
| ticket `pending` mà resolution mới nhất đã approved/rejected | 0 | 0 | ✔ |
| số ticket đổi trạng thái | đúng 6 (5 approved + 1 rejected) | đúng 6, khớp từng ID | ✔ |
| `TCK-518527ab869f` | 0 resolution, vẫn `pending` | 0 resolution, `pending` | ✔ |
| hàng non-rejected mang nhãn từ chối | 0 | 0 | ✔ |

**Về "đúng 6 ticket đổi trạng thái":** đối chiếu bằng bản sao lưu `tickets`
chụp **TRƯỚC** khi chạy migration (`/tmp/backup_tickets.csv` trong container
postgres), không phải bằng suy luận. Danh sách khớp chính xác danh sách trong
tiền-kiểm: `TCK-173cee0218a0` · `TCK-5ce978c5fd8b` · `TCK-5ff347d86281` ·
`TCK-77f6333334e2` · `TCK-cfd642f7461c` sang `approved`, và
`TCK-0e7f530fbd4f` sang `rejected`.

**Một khác biệt so với tiền-kiểm, nêu để security không phải tự truy:** tiền-kiểm
nói "8 dòng lệch". Lúc tôi đo trước khi chạy thì còn **7**, trong đó 1 là
`TCK-518527ab869f` — ticket bị xoá hết resolution ở bước 1 nên bước 3 bỏ qua nó.
7 − 1 = 6 ticket đổi. Con số đích (6) khớp; chỉ con số xuất phát khác, nhiều khả
năng do dữ liệu thay đổi giữa lúc security viết tiền-kiểm và lúc tôi chạy.

## 3. Sentinel — đối chiếu 5 điều kiện nghiệm thu (tiền-kiểm §4)

| # | Điều kiện | Cách làm | Nghiệm thu |
|---|---|---|---|
| 1 | Không đăng nhập được, **chứng minh bằng chạy thật** | `password_hash = NULL` | `POST /auth/login` bằng phone sentinel → **401**, kể cả khi mật khẩu rỗng. **Đối chứng:** supervisor THẬT vẫn đăng nhập → **200** (không siết nhầm) |
| 2 | Không mang danh một con người | `full_name` = `[HỆ THỐNG] không xác định — backfill ADR-019` | Đọc từ DB, đúng nguyên văn |
| 3 | Không lọt vào phép chọn tự động | `user_id = USR-SYS-UNKNOWN`; ASCII `'S'(83) > '0'(48)` nên `'USR-0205' < 'USR-SYS-UNKNOWN'` | Chạy đúng câu SQL từng GÂY RA F-11 (`WHERE role='supervisor' ORDER BY user_id LIMIT 1`) → trả `USR-0205`, **không** trả sentinel |
| 4 | Không vào thống kê người | — | **CHƯA ĐỦ, xem §4** |
| 5 | `rationale` khai đủ BA thứ suy ra | Ghi chú mới khai rõ lý do · người · thời điểm đều là suy ra | Đọc từ DB, có đủ 3 mục |

**Về lựa chọn `role='supervisor'`** (tiền-kiểm §4.3 yêu cầu nêu rõ và chứng minh
mọi nơi liệt kê supervisor đã loại trừ nó): chọn `supervisor` vì `rejected_by`
mang nghĩa "sếp nào đã từ chối" — gán một `customer` vào đó tạo ra bản ghi kiểm
toán vô nghĩa cho người đọc sau. Đã rà: `src/` **không có truy vấn nào chọn user
theo role** (`_STAFF_ROLES` chỉ xét role của người ĐANG đăng nhập;
`ESCALATION_TARGET` là hằng chuỗi, không tra bảng `users`). Rủi ro còn lại là
code TƯƠNG LAI liệt kê supervisor — nhãn `full_name` và tiền tố `USR-SYS-` được
chọn để lộ ngay khi điều đó xảy ra.

## 4. Điều CHƯA đạt — nói trước, không để security tự phát hiện

**Điều kiện §4.4 ("không vào thống kê người") mới đạt một nửa.** Hiện chưa có
phép đếm nào theo `rejected_by`/`approved_by` trong `src/` để mà loại trừ
sentinel (đã grep: không có `count()` nhóm theo hai cột này). Nên hôm nay điều
kiện này **không bị vi phạm** — nhưng cũng **chưa được bảo vệ**: ngày ai đó thêm
bảng hiệu suất người duyệt, sentinel sẽ lặng lẽ xuất hiện như một "supervisor có
1 lần từ chối" và không có gì cản.

Đề xuất (chưa làm, cần security/PO quyết): một bất biến canh "mọi truy vấn thống
kê theo `approved_by`/`rejected_by` phải loại `USR-SYS-%`", đặt cùng chỗ với các
INV khác thay vì trông chờ người sau nhớ.

Đây đúng loại "hiện diện ≠ hiệu lực" mà cả đội rút tối nay: sentinel **có** nhãn
rõ ràng, nhưng nhãn không tự chặn được việc bị đếm.

## 5. Phần CHƯA LÀM của nhịp

Field `note` (nhóm A) — **15 test đang đỏ có chủ đích**, chờ PO-5 chốt chính
sách che PII. Bốn điều kiện tôi sẽ giữ khi làm (3 từ sign-off TM-03, 1 tự thêm):

1. scrub **ở lúc GHI**, không phải lúc đọc;
2. fail-closed;
3. không mở rộng phạm vi đọc;
4. **giữ nguyên phần nội dung KHÔNG phải PII** — che tới mức CSKH không gọi lại
   được khách thì bản vá tự nó thành lỗi nghiệp vụ. Cùng phép thử đối chứng đã
   dùng cho C4 ("người hợp pháp có còn đi qua được không").

## 6. F-14 — TTL cho bộ nhớ tạm `_session_staff`

Ngoài phạm vi tiền-kiểm F-11/F-13 nhưng cùng nhịp, nộp kèm.

**Không phải lỗi hiệu năng — là lỗ quyền riêng tư.** `unclaim` đi qua pub/sub
(bắn-rồi-quên), nên worker vừa restart / Redis chập một nhịp / worker sinh ra
SAU khi tin đã bắn sẽ không bao giờ biết phiên đã đổi người giữ, và tiếp tục đẩy
tin nhắn của **khách** sang CSKH cũ — người không còn quyền đọc phiên đó. Không
tự sửa, không log nào báo.

Đã đo (fakeredis, mô phỏng `unclaim` bị lỡ): đọc lần đầu → A · đổi người giữ
trong Redis, không ai báo → vẫn A (còn hạn, đúng thiết kế) · sau khi hết hạn →
**B, tự lành** · nhồi 563 mục quá hạn rồi đọc 1 lần → còn 1 mục.
Trong container: `_SESSION_STAFF_TTL = 30.0`, `_SESSION_STAFF_NGUONG_DON = 512`.

## 7. Cách security tự kiểm lại (không cần tin bản nộp này)

```bash
docker compose exec -T backend alembic current          # kỳ vọng: e5f6a7b8c9d0 (head)
docker compose exec -T postgres psql -U fin05 -d fin05 -c "
  SELECT status, count(*) FROM resolutions GROUP BY status;
  SELECT resolution_id, rejected_by FROM resolutions WHERE status='rejected';
  SELECT ticket_id, hitl_status FROM tickets WHERE ticket_id='TCK-518527ab869f';
  SELECT user_id FROM users WHERE role='supervisor' ORDER BY user_id LIMIT 1;"
```

Ba câu cuối là ba điều kiện dễ hỏng nhất: dòng rejected phải trỏ sentinel, ticket
mồ côi phải còn `pending`, và câu SQL từng gây ra F-11 phải vẫn trả `USR-0205`.
