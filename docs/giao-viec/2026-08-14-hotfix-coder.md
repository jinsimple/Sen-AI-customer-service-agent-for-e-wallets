# GIAO VIỆC — tech-lead — HOTFIX trước demo tối 14/08

> PO giao. Dán nguyên văn vào phiên Claude tech-lead. KHẨN — timebox 2 giờ.
> Chẩn đoán chi tiết từng lỗi (PO đã kiểm bằng DB + code thật, KHÔNG cần
> điều tra lại từ đầu): `docs/giao-viec/2026-08-14-hotfix-demo-toi.md`

---

Bạn là **tech-lead** của FIN-05. PO thật test tay bản main trước demo tối nay
và chốt 6 vấn đề V1–V6. Đây là **ngoại lệ đóng băng main**: được sửa main
theo lệnh PO thật, diff tối thiểu, không refactor.

**Xác nhận trước khi bắt đầu (trả lời ngắn):**
a. Vì sao V2 KHÔNG sửa gì, và V6 tối nay CHỈ được sửa frontend?
b. Sau khi sửa xong, bằng chứng nào chứng minh fix đã CÓ TRONG container?
c. Một điểm thiếu/mâu thuẫn trong brief (bắt buộc ≥1).

## Việc — theo đúng thứ tự, chi tiết kỹ thuật đọc ở file chẩn đoán

1. **V3.2 + V3.3** — validation số tiền đề xuất hoàn (refund_* phải >0 và
   ≤ số tiền giao dịch trích dẫn) + dọn dòng `RES-b8d2c7798d53` amount=6
   (UPDATE về 107000 hoặc xoá — ghi rõ chọn gì, vì sao).
2. **V1** — banner sếp trên ticket detail thêm nút/link "Mở trang Phê duyệt →"
   (`/approve`). KHÔNG đưa nút duyệt vào ticket detail — tách trang là thiết
   kế có chủ đích.
3. **V6** — ChatClient: rail "Giao dịch gần đây" gate theo state otpVerified;
   chưa OTP → placeholder "Xác thực OTP để xem giao dịch gần đây" + nút mở
   luồng OTP sẵn có. **CHỈ frontend** — route/matrix giữ nguyên (comment
   thiết kế trong main.py còn hiệu lực cho tới khi có ADR mới sau demo).
4. **V3.1** — prefill số tiền từ giao dịch gắn ticket vào form đề xuất.
5. **V5 + V4** (CHỈ khi 1–4 xong và còn ≥45 phút): sau verify OTP thành công,
   frontend tự gửi lại tin chưa-được-phục-vụ gần nhất (ẩn, không vẽ bubble
   trùng), copy "Xác thực xong — mình tra tiếp yêu cầu vừa rồi nhé";
   investigation trail hiển thị "bị chặn — cần OTP phiên" thay vì `null`.
   Không kịp → BỎ, ghi nợ, không sửa ẩu.

## Ràng buộc

- Vùng ghi: `src/`, `frontend/src/`. KHÔNG chạm `contracts/`, `tests/`, `eval/`.
- Diff tối thiểu, không refactor, không "tiện tay" sửa gì ngoài V-list.
- Sửa xong TỪNG cụm: chạy test liên quan; cuối cùng bắt buộc
  `pytest tests/test_invariants.py -v` (19/19) + full suite không đỏ thêm.
- `docker compose build && docker compose up -d` + **verify fix TRONG
  container** (`docker exec ... grep` một dòng code đặc trưng mỗi fix) +
  `docker ps` backend healthy.
- Xong: commit lên **main** (message rõ từng V), báo PO + QA/QC nghiệm thu.
  KHÔNG merge sang dev — PO sẽ điều phối sau demo.

## BÁO CÁO CUỐI (gửi PO)

```
## Từng V: làm/không làm · commit hash · test liên quan pass?
## Verify container: (lệnh + output từng fix)
## Bất biến 19/19 + full suite: (output thật)
## Nợ để lại (V nào bỏ, vì sao)
## Sẵn sàng cho QA/QC nghiệm thu: CÓ/CHƯA
```
