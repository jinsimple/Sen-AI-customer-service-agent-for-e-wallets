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
| CI-8 | Thước bất động được canh ở CI | Gỡ guard trong `scripts/gen_dataset.py` (bỏ nhánh `ap.error` khi thiếu `--cho-phep-ghi-de-thuoc`) → `tests/test_data/test_thuoc_bat_dong.py` **PHẢI đỏ**. Xanh khi guard đã gỡ nghĩa là test đang canh một thứ khác, không phải canh thước | Trả guard lại → xanh |
| CI-9 | Nhóm `slow` không bị bỏ rơi | Để một test `slow` đỏ → CI phải đỏ. Job dùng `-m "not slow"` cho vòng nhanh thì BẮT BUỘC có job khác chạy `-m "slow"` (hoặc chạy đủ, không lọc) | Sửa lại → xanh |

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

**Marker `slow` — xong** (coder khai `55e578d`, tester gắn `3` test). Đúng thứ
tự vùng ghi: khai trước ở `pytest.ini` (coder), gắn sau ở `tests/` (tester) —
gắn marker chưa khai chỉ sinh cảnh báo mà không lọc được gì.

Đã kiểm marker lọc được THẬT, cả hai chiều:
```
pytest tests/test_data/ -m "not slow"  ->  4 passed, 3 deselected
pytest tests/test_data/ -m "slow"      ->  3/7 tests collected
```

⚠️ **`slow` là để lọc lúc dev, KHÔNG phải để CI bỏ bớt phạm vi.** CI vẫn phải
chạy đủ. Nếu một job nào đó dùng `-m "not slow"`, phải có job khác chạy nhóm
`slow` — nếu không thì `CI-8` không được canh ở đâu cả, và ta quay lại đúng lỗ
"test chỉ xanh trên máy một người".

Test này **tự khôi phục file trong `finally`**, nên chạy bao nhiêu lần cũng
không để lại hậu quả — kể cả khi guard bị gỡ và sản phẩm ghi đè thật.

---

## CI-8 — NGHIỆM THU TRỰC TIẾP, chiều ĐỎ: ĐẠT (15/08)

Coder tạm gỡ guard **trên file thật trong repo** (phương án 1 PO chọn — không
phá ranh giới vùng ghi: coder sửa `scripts/`, tester chỉ chạy và đo). Họ mô tả
chính xác một dòng đã đổi trước khi tôi chạy:

```python
if args.eval_out is None and not args.cho_phep_ghi_de_thuoc:   # gốc
if False:  # TẠM GỠ GUARD — nghiệm thu CI-8                      # tạm
```

**Kết quả:**

```
1 failed, 2 passed in 60.06s

AssertionError: gen_dataset ĐÃ GHI ĐÈ eval/golden_set.jsonl dù không có cờ
`--cho-phep-ghi-de-thuoc`.
  [exit=0] [GEN] users=206 tx=60000 events=215944 complaints=600
           golden=180 (dev 120 / heldout 60) seed=20260802
```

Đỏ **đúng test cần đỏ**, hai test kia vẫn xanh — gỡ lệnh cấm chỉ làm hỏng đúng
mặt nó canh, không kéo theo nhiễu.

**Ba dữ kiện xác nhận đo đúng thứ cần đo** (không nhận "đỏ" trống không):
- `exit=0` — nhánh `ap.error` không còn chạy, khớp đúng cách gỡ
- stdout in `golden=180 (dev 120 / heldout 60)` — script **thật sự sinh lại bộ case**
- băm `eval/golden_set.jsonl` **`a5ea8c876df0` trước và sau như nhau** — cơ chế
  khôi phục trong `finally` hoạt động, `git status` sạch, không ai phải dọn

**Vì sao biết chính xác dòng bị đổi lại quan trọng:** nếu chỉ nhận "đã gỡ, chạy
đi" rồi thấy đỏ, ta vẫn phải xác minh thêm một vòng xem đỏ có phải do gỡ guard
không — hay do script hỏng vì lý do khác. Người làm thí nghiệm nói rõ họ đổi gì
thì người đo mới quy được nhân quả.

### Chiều XANH: ĐẠT — CI-8 ✅ TICK

Coder trả guard, tôi **tự kiểm chứ không nhận lời**:

```
git diff --stat scripts/gen_dataset.py   -> RỖNG (khớp từng byte bản trong git)
gen_dataset.py --out <tạm>               -> stderr có "Từ chối ghi đè thước đo"
pytest tests/test_data/test_thuoc_bat_dong.py -> 3 passed in 40.89s
băm eval/golden_set.jsonl                -> a5ea8c876df0 trước và sau
git status eval/ scripts/ data/          -> sạch
```

⇒ Cổng biết **kêu** (chiều đỏ) và biết **im** (chiều xanh). Đủ hai chiều mới
tick — một cổng chỉ chứng minh được nó biết kêu thì vẫn chưa dùng được.

### 🔴 CẢNH BÁO CHO NGƯỜI VIẾT LẠI PHÉP THỬ NÀY VỀ SAU

Sau đợt guard, có **HAI đường hợp lệ** và **MỘT đường bị cấm**:

| Đường | Kỳ vọng |
|---|---|
| `make data` (tự truyền `--eval-out <tạm>`) | hợp lệ, **không chạm guard** |
| `gen_dataset.py --cho-phep-ghi-de-thuoc` | hợp lệ, cố ý ghi đè |
| **`gen_dataset.py` TRẦN, không cờ** | **bị cấm — đây là đường phải test** |

**Nếu ai đó viết lại phép thử bằng `make data`, nó sẽ XANH MÃI MÃI và trông
như guard đang hoạt động — trong khi thật ra chưa hề chạm tới guard.**

Chính coder suýt kết luận sai ở đúng chỗ này khi trả guard: phép thử đầu của
họ là `make data`, ra `exit=0` không kèm câu từ chối, nhìn qua như guard chưa
sống lại. Họ tự phát hiện là đo nhầm đối tượng và chạy lại bằng script trần.

Đây lại là **assertion trùng trạng thái mặc định** ở dạng khác: không phải
assert sai, mà **gọi nhầm đường** — đường được chọn vốn dĩ luôn hợp lệ, nên
kết quả xanh không mang thông tin nào. Helper `_chay_gen_dataset()` trong
`tests/test_data/test_thuoc_bat_dong.py` cố ý **không** truyền `--eval-out`
đúng vì lý do này; docstring của nó ghi rõ, đừng "dọn cho gọn".

---

## CI-4 / CI-5 — trạng thái: LOGIC đã kiểm, JOB chưa chạy trên runner

Coder nối dây `route-guards-docker` (`b999dec`) và hiện thực "SKIP LÀ ĐỎ" bằng
cách đọc junit XML — đúng cách, vì `pytest` **không có** cơ chế biến skip thành
fail: `pytest.skip(allow_module_level=True)` luôn cho exit 0, nên bước chạy test
sẽ XANH kể cả khi **0 ô nào được kiểm**.

**Đã kiểm được ngay, không cần runner và không đụng Docker** — bóc đoạn python
trong job ra chạy trên 4 file XML dựng sẵn:

| Tình huống | Kỳ vọng | Kết quả |
|---|---|---|
| 24 pass, 0 skip (stack sống) | xanh | ✅ exit 0 |
| 24 skip (không dựng được Docker) | ĐỎ | ✅ exit 1 |
| 23 pass + **1 skip lẻ** | ĐỎ | ✅ exit 1 |
| **0 test** thu được | ĐỎ | ✅ exit 1 |

Hai ca biên cuối quan trọng hơn ca hiển nhiên: một skip lẻ nghĩa là **một ô của
ma trận không được kiểm** — đủ để lọt đúng lớp lỗi guard-hẹp-hơn-contract; còn
`tests=0` là ca "chạy nhưng không thu được gì", thứ hay bị đọc thành xanh nhất.

⚠️ **CHƯA TICK.** Cái đã kiểm là **logic đọc XML**, không phải **job chạy trên
runner**. Còn thiếu: nhánh `chay == 'co'` thực thi thật (cần một push đụng
`frontend/src/`, `contracts/`, hoặc chính file bộ quét), rồi làm đỏ — xanh theo
đúng CI-4/CI-5.

Ghi tách bạch đúng như CI-8 lúc chưa nghiệm thu trực tiếp: **đọc YAML chứng
minh ý định, chạy đoạn logic chứng minh nó tính đúng, chỉ có chạy thật trên
runner mới chứng minh cả dây chuyền nối đúng.** Ba mức khác nhau, không gộp.
