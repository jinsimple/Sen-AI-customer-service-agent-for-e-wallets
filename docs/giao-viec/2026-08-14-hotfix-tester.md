# GIAO VIỆC — tester (QA/QC) — NGHIỆM THU hotfix trước demo tối 14/08

> PO giao. Dán nguyên văn vào phiên Claude tester. Bắt đầu phần chuẩn bị NGAY;
> phần nghiệm thu chạy khi coder báo "đã rebuild container xong".
> Bối cảnh lỗi: `docs/giao-viec/2026-08-14-hotfix-demo-toi.md` (V1–V6).

---

Bạn là **tester** của FIN-05. Coder đang hotfix 6 vấn đề trên main (ngoại lệ
đóng băng có lệnh PO thật). Việc của bạn: nghiệm thu ĐỘC LẬP từng fix trên
stack Docker thật rồi phán GO/NO-GO cho demo tối nay. **KHÔNG đọc src/** —
nghiệm thu bằng UI/API/DB, đối chiếu mô tả hành vi trong file bối cảnh.

**Xác nhận trước khi bắt đầu (trả lời ngắn):**
a. Vì sao KHÔNG được chạy Playwright config mặc định (bài học smoke sáng nay)?
b. V2 không có fix — bạn nghiệm thu gì ở đó? (gợi ý: xác nhận KHÔNG có gì đổi)
c. Một điểm thiếu/mâu thuẫn (bắt buộc ≥1).

## Chuẩn bị (làm ngay, không cần chờ coder)

- Soạn bảng nghiệm thu từ V-list dưới đây, mỗi V: bước bấm cụ thể + kỳ vọng.
- Nhắc ngân sách: đừng tạo ticket rác cho USR-0145 (hàng chờ demo); dùng
  USR-0001 (`0387000001`) cho các bước phá; trần live-chat 60 tin/giờ.

## Nghiệm thu (khi coder báo xong — mỗi mục ghi ĐẠT/KHÔNG + bằng chứng)

1. **V3 — số tiền đề xuất:**
   - CSKH `0353000201` mở 1 ticket có giao dịch → form đề xuất: số tiền đã
     prefill đúng số tiền giao dịch?
   - Thử trình với số tiền 0 / âm / lớn hơn giao dịch → backend chặn, thông
     báo tiếng Việt sạch (không [object Object])?
   - Kiểm DB/màn hình: không còn đề xuất "6đ" nào (RES-b8d2c7798d53 đã
     sửa/xoá)?
2. **V1 — đường tới nút duyệt:**
   - Sếp `0905000205` mở ticket detail → banner có nút/link "Mở trang Phê
     duyệt" bấm được, tới `/approve`?
   - **Tại /approve: danh sách CÓ hiện đề xuất pending_approval không?**
     (câu PO đang cần trả lời — nếu RỖNG là bug backend mới, báo NGAY)
   - Đi trọn: xin OTP → duyệt → status đổi, `approved_by` đúng trong DB.
3. **V6 — rail giao dịch gate OTP:**
   - Đăng nhập khách MỚI (chưa OTP phiên) → rail KHÔNG hiện giao dịch, có
     placeholder + nút OTP?
   - OTP xong → rail hiện lại bình thường?
4. **V5 (nếu coder làm) — không bắt gõ lại sau OTP:**
   - Phiên mới, gõ "mình chuyển nhầm <số tiền>" TRƯỚC khi OTP → bị chặn OTP
     → xác thực → agent TỰ tra tiếp, không bắt gõ lại, không bubble trùng?
   - Nhánh thường (OTP trước, chat sau) vẫn bình thường, không gửi trùng tin?
5. **V4 (nếu làm):** trail không còn `kết quả: null` trần — ghi "bị chặn —
   cần OTP phiên"?
6. **Hồi quy nhanh:** `pytest tests/test_invariants.py -v` 19/19 ·
   `npx playwright test --config=playwright.livechat.config.ts` (config Docker
   DUY NHẤT được dùng — config mặc định spawn stack dev, bẫy ADR-009) ·
   D2 + D4 chạy lại 1 lần mỗi case theo `eval/demo_cases_20260814.md`
   (D4 dùng đúng lời thoại, xác nhận vẫn 8,2s±).

## Ràng buộc

- CHỈ BÁO CÁO, KHÔNG SỬA — kể cả fix 1 dòng. Phát hiện chặn demo → báo PO NGAY.
- Vùng ghi: `tests/`, `frontend/e2e/`, `eval/` (bảng nghiệm thu lưu
  `eval/nghiem_thu_hotfix_20260814.md`).

## BÁO CÁO CUỐI (gửi PO)

```
## Kết luận: GO / NO-GO cho demo tối nay (+ điều kiện)
## Bảng V1–V6: ĐẠT/KHÔNG/KHÔNG-LÀM · bằng chứng từng dòng
## Câu trả lời: /approve có hiện danh sách pending không?
## Hồi quy: bất biến · livechat e2e · D2/D4
## Phát hiện mới (nếu có — KHÔNG tự sửa)
```
