# Tiêu chí "CI đạt" — C2 · C3

> Vai giữ file: **tester** · 14/08/2026 · phần tiêu chí của mục C2/C3 trong
> `docs/giao-viec/2026-08-14-phan-viec-dot-ke-tiep.md`.
> Tester định nghĩa tiêu chí → **coder nối dây** (`.github/workflows/` ngoài
> vùng ghi của tester) → tester nghiệm thu bằng cách **cố tình làm đỏ**.

## Nguyên tắc gốc

Một cổng CI chỉ có giá trị khi thoả **cả hai** chiều:

1. **Có lỗi thì phải ĐỎ.** Test đỏ mà CI xanh thì cổng không tồn tại.
2. **Không có lỗi thì phải XANH.** Cổng đỏ vì lý do sai còn tệ hơn không có
   cổng — nó dạy cả đội bỏ qua chính cảnh báo đó. (Cùng lập luận đã dùng cho
   dấu thước ở `eval/measure_quality.py::dau_thuoc`.)

Vì vậy mọi tiêu chí dưới đây đều đi kèm **một phép thử làm đỏ** và **một phép
thử xác nhận xanh sạch**.

---

## 🔴 C2 — Hai lỗ đã tìm thấy, có bằng chứng

### Lỗ 1: CI KHÔNG CHẠY trên nhánh đang làm việc

`.github/workflows/ci.yml`:

```yaml
on:
  push:
    branches: [main, develop]
  pull_request:
    branches: [main]
```

Nhánh đang làm việc là **`dev/learning-loop`**. Nó không nằm trong `push.branches`,
và PR giữa các nhánh dev cũng không khớp `pull_request.branches: [main]`.

⇒ **Toàn bộ công việc Phase 0 + Phase 1 hôm nay chạy với ZERO lượt CI.** Đây
chính là "unit test đỏ không làm CI đỏ" ở dạng triệt để nhất: test đỏ thật,
nhưng CI **không hề chạy** nên chẳng có gì đỏ cả. Không phải cấu hình job sai —
là cổng chưa từng mở.

**Tiêu chí:** mọi push lên nhánh `dev/**` và mọi pull request **có đích là bất
kỳ nhánh nào** đều phải kích hoạt tối thiểu: `invariants`, `lint-and-test`,
`frontend-lint-and-test`.

### Lỗ 2: Test cần Docker/DB thật SKIP im lặng trong CI

`tests/test_api/test_frontend_route_guards.py` (24 ô ma trận vai × trang) tự
`skip` khi không tới được `https://localhost`. Trong CI hiện tại **không job
nào dựng stack Docker**, nên bộ quét này **chưa bao giờ chạy ở CI** — nó chỉ
xanh trên máy tester.

Đây đúng lớp lỗi mà chính nó sinh ra để canh (guard frontend hẹp hơn contract,
đã xảy ra **ba lần**). Một cổng chỉ chạy trên máy một người thì không phải cổng.

**Tiêu chí:** phải có **một job có Docker** chạy bộ quét vai × trang. Tần suất
tối thiểu: **mỗi PR có đụng `frontend/src/` hoặc `contracts/`**; chấp nhận
được nếu nightly + on-demand (`workflow_dispatch`) cho phần còn lại, vì dựng
stack tốn vài phút.

**Điều kiện bắt buộc kèm theo:** job đó phải **ĐỎ khi bộ quét bị skip**, không
được coi skip là đạt. Skip ở đây nghĩa là "không dựng được stack" — tức là
chưa đo gì cả, không phải "đo xong và ổn".

---

## 🔴 C3 — Lỗi của chính tester, đã tự sửa

`tests/test_migrations/test_trang_thai_dich_nhip_note_f11_f13.py` canh **trạng
thái dữ liệu của DB demo**, nhưng lại nằm trong `tests/test_migrations/` — thư
mục mà job `db-migration-test` chạy trên một **Postgres RỖNG dựng mới mỗi lần**.

Đo thật (dựng `postgres:16-alpine` rỗng, chạy đúng lệnh của CI):

```
9 passed, 7 errors     ← TRƯỚC khi sửa (bảng `resolutions` còn chưa tồn tại)
9 passed, 7 skipped    ← SAU khi sửa
```

Nếu đẩy nguyên trạng, coder sẽ nhận một CI đỏ **không liên quan gì tới việc họ
làm** — và đó là cách nhanh nhất để một job bị coi là "hay đỏ vớ vẩn".

**Đã sửa:** module tự `skip` khi DB không có bảng `resolutions` hoặc không có
resolution nào — phân biệt "DB rỗng của CI" với "DB demo cần canh". Đã xác
minh **cả hai chiều**: rỗng → skip sạch; DB demo → vẫn đỏ đúng 5 ca trước
migration.

**Tiêu chí chung rút ra:** test canh **trạng thái dữ liệu của một môi trường
cụ thể** không được nằm chung thư mục với test canh **logic**. Nếu buộc phải
nằm chung, nó phải tự nhận ra mình đang ở nhầm môi trường và skip có thông báo
rõ — không bao giờ đỏ vì nhầm môi trường.

---

## Bảng tiêu chí — coder nối dây theo bảng này

| # | Tiêu chí | Phép thử LÀM ĐỎ (tester chạy) | Phép thử XANH SẠCH |
|---|---|---|---|
| CI-1 | Push lên `dev/**` kích hoạt CI | Push 1 commit có test đỏ cố ý lên nhánh `dev/thu-ci` → phải thấy lượt chạy CI và nó ĐỎ | Revert → cùng nhánh xanh |
| CI-2 | Unit test đỏ ⇒ job `lint-and-test` đỏ | Thêm `assert False` vào 1 test bất kỳ | Gỡ ra |
| CI-3 | Lint đỏ ⇒ CI đỏ | Thêm dòng `import os` thừa | Gỡ ra |
| CI-4 | Bộ quét vai×trang chạy ở job CÓ DOCKER | Sửa 1 ô ánh xạ trang→route cho sai → job đó phải đỏ | Trả lại đúng |
| CI-5 | **Skip ≠ đạt** ở job Docker | Tắt stack trước khi chạy job → job phải ĐỎ (báo "không dựng được stack"), KHÔNG xanh | Bật stack → xanh |
| CI-6 | Test dữ liệu-môi-trường không đỏ oan | Chạy `tests/test_migrations/` trên Postgres rỗng → skip sạch, không error | Chạy trên DB demo → đỏ đúng ca thật |
| CI-7 | Cổng so sánh eval nối vào CI | `measure_quality.py --so-sanh` trả **exit 1** khi có ca xấu đi → job phải đỏ | Hai lượt giống nhau → exit 0, xanh |
| CI-8 | Thước bất động được canh ở CI | Gỡ guard trong `gen_dataset.py` → `tests/test_data/test_thuoc_bat_dong.py` phải đỏ | Trả guard lại → xanh |

## Cách nghiệm thu (tester làm sau khi coder nối dây)

Đi lần lượt từng dòng bảng trên: **làm đỏ trước, xanh sau**. Không nhận tiêu
chí nào chỉ bằng cách đọc file YAML — đọc YAML chứng minh *ý định*, chạy thật
chứng minh *hiệu lực*. Cùng nguyên tắc "sự hiện diện ≠ hiệu lực" đã áp cho
CHECK constraint.

Nghiệm thu xong ghi kết quả từng dòng (đỏ được / xanh được) vào file này.

---

## Ghi chú vận hành cho coder khi nối dây

`tests/test_data/test_thuoc_bat_dong.py` chạy **~40s** (ba lượt sinh dataset
thật — không mock được, vì thứ cần canh chính là hành vi GHI FILE thật).

Tôi **không** gắn `@pytest.mark.slow`: marker đó chưa khai trong `pytest.ini`,
mà `pytest.ini` ngoài vùng ghi của tester. Nếu muốn tách nhóm chậm ra khỏi job
nhanh, coder khai marker `slow` trong `pytest.ini` rồi tôi gắn — đừng để tôi
gắn marker chưa khai, vì nó chỉ sinh cảnh báo mà không có tác dụng lọc nào.

Test này **tự khôi phục file trong `finally`**, nên chạy bao nhiêu lần cũng
không để lại hậu quả — kể cả khi guard bị gỡ và sản phẩm ghi đè thật.
