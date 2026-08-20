# Đọc bảng CI đỏ: phân biệt bốn nguyên nhân — 2026-08-20

> Một job đỏ trên GitHub Actions không có nghĩa "code sai". Bảng job màu đỏ
> gộp chung bốn nguyên nhân khác hẳn nhau, và ba trong bốn **không cần sửa
> code**. Đọc nhầm loại nào tốn đúng một lượt chẩn đoán oan — [ĐO 20/08]
> lượt CI #299 tốn của cả DevOps lẫn QA/QC một lượt mỗi người trước khi
> phân biệt được "đỏ vì code" với "đỏ vì mạng".

## Bốn nguyên nhân

| # | nguyên nhân | dấu hiệu | việc cần làm |
|---|---|---|---|
| 1 | **Mạng/hạ tầng** — lỗi tải gói, timeout kết nối, runner mất kết nối giữa chừng | Log có `Connection broken`, `IncompleteRead`, `ReadTimeoutError`, `Temporary failure in name resolution` — thường ở bước cài đặt, KHÔNG phải bước chạy test | `gh run rerun --failed`. Không phải bug, không cần sửa code |
| 2 | **Billing/runner chưa cấp** — job chưa từng chạy | `runner_name` RỖNG, `steps` RỖNG (mảng `[]`) trong `gh run view --json jobs` | Không phải lỗi kỹ thuật — cần người có quyền bật billing/runner. Đừng chẩn đoán code |
| 3 | **Đỏ ĐÚNG THIẾT KẾ** — cổng cố ý canh một finding P0 chưa vá/chưa quyết | Tên job/test tự khai trong docstring hoặc comment (vd `security_finding` marker) — xem ADR liên quan trước khi hoảng | Không sửa để "cho xanh" — đọc ADR, hỏi PO nếu chưa rõ trạng thái |
| 4 | **Lỗi thật** — code/contract/test thực sự sai | Log có traceback cụ thể, assertion fail, thông báo lỗi nghiệp vụ (không khớp 3 dấu hiệu trên) | Sửa code/test/contract theo đúng vùng ghi của vai phụ trách |

## Lệnh tra nhanh — phân biệt cả bốn trong MỘT lệnh

```bash
gh run view <id> --json jobs -q '.jobs[] | select(.conclusion=="failure")
   | "\(.name)|\(.steps|map(select(.conclusion=="failure"))|map(.name)|join(";"))"'
```

Đọc kết quả:
- **Bước hỏng RỖNG** (`name|` không có gì sau dấu `|`) ⟹ job **chưa từng
  chạy** (nguyên nhân 2, billing/runner) — [ĐO] cách phân biệt nhanh nhất,
  đã cứu hai lượt chẩn đoán trong ngày 20/08.
- **Bước hỏng có tên, và tên đó là bước cài đặt** (`pip install`, `npm ci`,
  `Initialize containers`) ⟹ nghi nguyên nhân 1 (mạng) TRƯỚC — đọc log của
  chính bước đó, tìm các cụm từ ở bảng trên.
- **Bước hỏng có tên, là bước TEST/CHẠY**, và tên job/test tự khai một
  finding đã biết ⟹ nguyên nhân 3 — đối chiếu `docs/DECISIONS.md`/ADR liên
  quan trước khi kết luận là bug mới.
- **Còn lại, có traceback/assertion cụ thể** ⟹ nguyên nhân 4, lỗi thật.

## Ghi chú vận hành

- Kể từ [`813b7c7`](../.github/workflows/ci.yml) mọi bước cài Python trong
  CI đi qua `scripts/ci_pip_install_retry.sh` — retry TỰ ĐỘNG cho nguyên
  nhân 1 (chỉ khi khớp thông báo lỗi mạng đã biết), nên **nguyên nhân 1 sẽ
  ít gặp hơn từ giờ**, nhưng KHÔNG biến mất hoàn toàn (mạng chập 3 lần liên
  tiếp trong 5 giây vẫn có thể xảy ra) — bảng trên vẫn cần khi retry hết
  lượt.
- Nguyên nhân 2 và 3 không tự sửa được bằng thao tác kỹ thuật đơn thuần —
  đừng dành thời gian "debug" chúng, chuyển thẳng cho người có thẩm quyền
  (PO thật cho billing, PO/an ninh cho finding P0).
