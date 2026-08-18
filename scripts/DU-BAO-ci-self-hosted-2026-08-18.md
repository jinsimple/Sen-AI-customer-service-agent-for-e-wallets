# DỰ BÁO — chuyển CI sang runner self-hosted (ADR-037)

> Công bố **trước** khi sửa dòng nào. Nền: `HEAD=ff4f40b`, nhánh `dev/learning-loop`.
> tech-lead · 18/08/2026.

---

## 0. Ba lời khai của brief — tôi tự tra lại, cả ba TRÚNG

| brief nói | tôi đo | |
|---|---|---|
| `ci.yml` 14 `runs-on`, `deploy.yml` 1 | 14 · 1 | ✅ |
| 5 hit `always()`, **cả năm là `upload-artifact`** | 349·386·436·482·644, cả năm `upload-artifact@v4` | ✅ |
| 0 `rm .env` · 0 `compose down` | 0 · 0 | ✅ |
| 8 lệnh compose ở 560·562·572·598 · 623·625·634·642 | khớp từng dòng | ✅ |

Và duyệt của PO thật: `472bba5` ADR-033 *"CẢ HAI phần… phê chuẩn 18/08 vòng 2"* · `7e63ddc`
STATE §5.A0 bảng VÒNG 2 · `5e1b618` `CLAUDE.md` §4 thêm `.github/workflows/**` vào vùng tech-lead
(tác giả `jinsimple`, không phải phiên nào). **Ba vết đọc được, không tin lời ai.**

## 1. 🔴 MỘT CHỖ TRONG BRIEF SAI CƠ CHẾ — `-p` KHÔNG chống đụng cổng

Brief §3: *"docker compose publish cổng ra host. Runner dùng chung ⟹ đụng cổng ⟹ **bắt buộc `-p`**"*.

**`-p` đổi tên project. Nó không đổi cổng host.** [ĐO] `docker-compose.yml`:

```
caddy    "80:80"  "443:443"          ← MỌI interface
postgres "127.0.0.1:5432:5432"
jaeger   "127.0.0.1:16686:16686"
```

Bốn cổng này **cố định trong file**, `-p` không chạm tới. Hai lượt chạy đồng thời trên cùng máy
⟹ lượt sau **không bind được 443** ⟹ đỏ, và `-p` có mặt hay không đều thế.

**`-p` vẫn PHẢI có** — nhưng nó mua thứ khác, và cần gọi đúng tên:

| `-p` mua được | `-p` KHÔNG mua được |
|---|---|
| hai lượt **của chính ta** không giẫm lên container/volume của nhau (tên project mặc định đều là `p-226`) | cổng host 80·443·5432·16686 vẫn là **tài nguyên độc quyền của cả máy** |
| `down -v` xoá đúng volume **của lượt mình** | |

⟹ Đây đúng **Luật G**: *một cơ chế làm đúng việc của nó ≠ nó làm việc ta tưởng.* Nếu tin `-p` đã
lo phần cổng, ta sẽ đọc mọi lần đỏ vì cổng thành "đỏ vì code".

### 🔴 Và kịch bản tệ hơn "đỏ": XANH GIẢ

Cả hai job docker chạy test **từ host, trỏ vào `https://localhost`**
([ĐO] `test_frontend_route_guards.py:30` `BASE = "https://localhost"` ·
`playwright.livechat.config.ts:28` `baseURL: "https://localhost"`).

Ghép với phát hiện *"không có `compose down`"*: một stack của **lượt trước** còn sống trên máy
dùng chung vẫn giữ 443. Lượt sau `up` hỏng, nhưng test host vẫn **kết nối được** — vào **stack cũ**.

```
đỏ vì đụng cổng     → còn đọc ra được
XANH vì test bắn vào stack CŨ  → không đọc ra được, và nó nói "đạt"
```
Đây là hạng tệ nhất: cổng im lặng trong lúc bất thường (**Luật A**). Nó cũng làm bước dọn (Việc 2)
quan trọng hơn brief mô tả: dọn không chỉ để **khỏi bỏ khoá lại**, mà để **lượt sau không đo nhầm
lượt trước**.

⟹ **Tôi thêm một bước tiền kiểm cổng** (8 dòng) trước `up`: cổng bận thì **đỏ ngay với đúng chữ
"ĐỎ VÌ ĐỤNG CỔNG"**. Đây chính là cơ chế làm nghiệm thu §6③ đọc được — không có nó thì §6③ là
việc đoán bằng mắt.

## 2. Tôi KHÔNG làm, và nói rõ vì sao

- **`concurrency:` cho workflow** — [ĐO] `ci.yml` hiện **không có** khối này. Nó sẽ chặn được
  chính hai lượt của ta đụng nhau, nhưng nó **đổi ngữ nghĩa CI** (huỷ lượt đang chạy, hoặc xếp
  hàng nối đuôi làm nightly trễ). Đó là quyết định của PO, không phải việc cơ học. **Đề xuất, chờ.**
- **Xoay khoá OpenAI** — brief cấm, `security` đang định hạng.
- **`deploy.yml`** — không chạm một ký tự.

## 3. Chia hai nhịp — và nhịp 1 CỐ Ý an toàn

**Nhịp này (commit A)** — đổi `runs-on` **duy nhất job `invariants`** (dòng 65) + **toàn bộ** phần
an toàn (8 × `-p`, 2 × bước dọn, 2 × tiền kiểm cổng).

Vì sao gộp phần an toàn vào nhịp 1 thay vì để nhịp 2: 13 job kia **còn ở `ubuntu-latest`**, nên
hai job docker vẫn chạy trên máy dùng một lần → **phần an toàn được diễn tập ở nơi nó không thể
gây hại**, trước khi có thứ gì thật sự chạy trên máy dùng chung. Land nó cùng lúc với việc chuyển
runner là để cơ chế chưa từng chạy lần nào gánh đúng lượt đầu tiên nó cần thiết.

**Nhịp 2** — chỉ sau khi nhịp 1 cho biết runner có cấp máy không.

## 4. DỰ BÁO — điền TRƯỚC

| # | vật | DỰ BÁO | THẬT |
|---|---|---|---|
| 1 | file đổi | **1** — `.github/workflows/ci.yml` | 1 (+100/−9) | ✅ |
| 2 | `runs-on: self-hosted` | **1** (job `invariants`), còn **13** `ubuntu-latest` | 1 · 13 | ✅ |
| 3 | lệnh compose mang `-p` | **8/8** | 8/8 (+2 trong bước dọn = 10) · 0 lệnh sót | ✅ |
| 4 | bước dọn thêm | **2**, `if: always()` **trần**, không guard | 2 · cả hai `if=always()` trần · là bước **cuối** của cả hai job | ✅ |
| 5 | tiền kiểm cổng thêm | **2** | 2, đặt **ngay trước** `up` | ✅ |
| 6 | `deploy.yml` · `src/` · `contracts/` · `tests/` | **0 dòng đổi** cả bốn | 0 · 0 · 0 · 0 | ✅ |
| 7 | YAML parse | hợp lệ, 14 job | hợp lệ · 14 job · hai job docker 10→**12** bước | ✅ |
| 8 | cổng cục bộ (invariants) | **23 passed** | **23 passed** · `check_contracts` sạch | ✅ |
| 9 | token tiêu | **0** | 0 | ✅ |
| 10 | sau khi đẩy: job `invariants` | **KHÔNG DÁM DỰ BÁO** — xem §5 | **success**, runner `eph-vmrunner2-1c2b45fc`, group `default`, 4′04″ | ✅ đọc được |

## 5. 🔴 Ô #10 là ô tôi KHÔNG đọc được, và nói thẳng thay vì đoán

Tôi đã thử tra nhãn của runner BTC:

```
gh api repos/…/P-226/actions/runners   → 404
gh api orgs/…/actions/runners          → 403 "must be an org admin"
```

**404 và 403 KHÔNG cùng nghĩa.** `403` là *"không cho đọc"* — tức **KHÔNG ĐỌC ĐƯỢC**, không phải
*"không có runner nào"*. Suy ra "chưa ai đăng ký runner" từ hai mã lỗi này là **suy cơ chế từ một
vắng mặt** — đúng lớp lỗi đã có luật riêng.

⟹ Tôi dùng `runs-on: self-hosted`. Cơ sở: nhãn `self-hosted` do GitHub **tự gắn** cho mọi runner
tự quản và **không gỡ được**, nên nó khớp bất kỳ runner nào repo này với tới. Nhưng nhãn khớp
**không** đảm bảo repo được **cấp** máy (runner group có thể không mở cho repo).

**Ba trạng thái, và trạng thái thứ ba mới là cái dễ đọc nhầm:**

| | nghĩa |
|---|---|
| xanh / đỏ **có log** | đã được cấp máy — điều ta muốn biết |
| **Queued mãi** (không log, không đỏ) | nhãn khớp nhưng **không được cấp máy** — GitHub **không báo lỗi**, nó đợi |
| 404/403 khi tra runner | **không đọc được**, không kết luận gì |

🔴 *Queued* trông giống "đang chạy". Nếu sau **10 phút** job vẫn không có log ⟹ đọc là **KHÔNG
ĐƯỢC CẤP MÁY**, và đó là câu hỏi cho BTC, **không phải** thứ tôi sửa được bằng cách sửa YAML.

## 6. Nếu khác thì nghi gì

| lệch | nghi |
|---|---|
| #2 ra 14 | tôi `sed` cả file thay vì đúng một dòng ⟹ 13 job kia mất lưới ephemeral trước khi có phần an toàn được kiểm |
| #3 < 8 | thiếu `-p` ở `exec`/`logs` ⟹ bước ấy đỏ vì **không tìm thấy container**, dễ bị đọc thành "backend hỏng" |
| #4 có kèm guard `chay == 'co'` | bước dọn tắt đúng lúc job bị bỏ qua giữa chừng — mất đúng ca nó sinh ra để đỡ |
| #8 ≠ 23 | tôi đã chạm thứ ngoài `.github/` mà không biết ⟹ dừng, `git diff` trước khi đẩy |
| job `invariants` **đỏ** ngay | phân biệt: đỏ vì **thiếu Python/tool trên runner** (hạ tầng) ≠ đỏ vì test. Đọc log rồi mới nói. |

## 7. Khai trước — KHÔNG được tính là xác nhận

Nhịp 1 xanh ⟹ *"runner cấp máy được cho một job KHÔNG cần Docker"*.
**KHÔNG** ⟹ *"runner chạy được `ci.yml`"*: job `invariants` không đụng Docker, không đụng
Compose v2, không đụng `services:`. Ba thứ ấy **chưa được kiểm bởi nhịp 1** và chỉ lộ ở nhịp 2.

## 8. Đọc kết quả lượt đẩy này — 13 ĐỎ là DỰ KIẾN, không phải hồi quy

Lý do CI chết là **billing tài khoản**, không phải code. 13 job còn ở `ubuntu-latest` ⟹ vẫn
*"was not started"*. **Chỉ job `invariants` là phép đo.** Ai đọc bảng 14 job mà thấy 13 đỏ rồi kết
luận "nhánh hỏng" là đang đọc **hoá đơn** thành **chất lượng mã**.

Runner tự quản không tính vào phút bị chặn — đó chính là cơ chế được kỳ vọng, và nó **chưa được
chứng minh**; lượt đẩy này là để chứng minh.

Ngoài ra `route-guards-docker` lần này sẽ tự cho `chay=khong` (tôi chỉ chạm `.github/`) ⟹ mọi bước
có guard đều bỏ qua, **trừ bước dọn**. Vô tình đó là bản thu nhỏ của nghiệm thu ③: nếu bước dọn
xanh trong lúc cả job bị bỏ qua, `if: always()` trần đã làm đúng việc. (Nhưng job này cũng nằm
trên `ubuntu-latest` ⟹ nhiều khả năng **không được cấp máy** — thì đó là **SKIP**, không phải bằng
chứng bước dọn hỏng.)

## 9. KẾT QUẢ NHỊP 1 — run `32135940445`

```
Ràng buộc cứng + contract drift :: completed/SUCCESS
  runner = eph-vmrunner2-1c2b45fc   group = default   labels = self-hosted
  12:16:17Z -> 12:20:21Z  (4′04″)
```
**Log thật, không phải dấu tick:** `collected 23 items`, 23 dòng `PASSED`, `check_contracts` →
*"Không có artifact lỗi thời"*. Phân biệt này quan trọng vì một bước `exit 0` với **0 test thu
được** cũng cho conclusion `success` — dự án đã có hẳn một bước *"SKIP LÀ ĐỎ"* sinh ra vì đúng lỗi ấy.

13 job kia: **11 `failure` runner rỗng** (billing, chưa từng khởi động) + **3 `skipped`** (nightly,
đúng `if:`). Đây là **hoá đơn**, không phải chất lượng mã.

### 🔴 Dự báo §8 của tôi TRƯỢT — ghi lại thay vì lặng lẽ bỏ

Tôi dự báo `route-guards-docker` sẽ cho `chay=khong` và **bước dọn vẫn chạy**, thành bản thu nhỏ
của nghiệm thu ③. **Không xảy ra.** Job ấy còn ở `ubuntu-latest` ⟹ **không được cấp máy** ⟹
*không bước nào chạy, kể cả `if: always()`*.

> **`always()` chỉ có nghĩa "luôn chạy khi job ĐÃ ĐƯỢC CẤP MÁY".**
> **Job chưa từng khởi động thì không có gì luôn cả.**

⟹ Bước dọn hiện là **mã CHƯA TỪNG THỰC THI**. Nghiệm thu ①②③ còn nợ nguyên.

### Nhịp 1 xanh KHÔNG có nghĩa gì thêm

`invariants` không đụng Docker, không đụng Compose v2, không đụng `services:`. Ba thứ ấy **chưa
được kiểm** và chỉ lộ ở nhịp 2. Cái đã biết chắc: **runner cấp máy được, `self-hosted` là nhãn
đúng, `setup-python` + `pip install` chạy được trên đó.**

## 10. NHỊP 1b — hai thứ thêm, và cái giá của chúng

**① `concurrency:`** (PO-agent chốt). Hai nhóm tách hẳn nên push không giết nightly.
🔴 **Cái giá:** `cancel-in-progress` cho push ⟹ **commit ở giữa một chuỗi đẩy không có kết quả
cổng riêng**. Với dự án vừa qua *"17/08 tới nay không commit nào qua cổng"*, giá này phải khai, không
được giấu. Đổi `false` tạm thời khi cần chứng thực từng commit — và khai ra khi đổi.

**② Phép đo ephemeral** — trả lời QĐ3① không cần BTC. Ghi `~/.fin05-moc-ci.txt` trên runner.

| lượt sau đọc được gì | kết luận |
|---|---|
| **đọc được** tệp mốc | **PERSISTENT — chứng minh xong** |
| **không** đọc được | **KHÔNG KẾT LUẬN GÌ** (máy khác? cùng máy đã dọn? không tách được) |
| runner_name **giống hệt** | **PERSISTENT — kết luận ngay** |
| runner_name **khác** | gợi ý, **không phải chứng minh** |

🔴 **Bất đối xứng:** phép này **chỉ chứng minh được PERSISTENT**. Nó **không bao giờ** chứng minh
được ephemeral. Ai đọc "không thấy tệp mốc" thành "vậy là ephemeral" đang lặp đúng lỗi mà `eph-`
suýt gây ra.

⚠️ **`cancel-in-progress` ăn vào chính phép đo này:** đẩy lượt B trong lúc lượt A còn chạy sẽ
**huỷ A** ⟹ mất luôn điểm dữ liệu. **Phải đợi A xong rồi mới đẩy B.** Hai cơ chế cùng land một
nhịp và một cái cắn cái kia — ghi ra để lần sau không phải phát hiện lại.

🚫 **Cố ý KHÔNG dùng `workflow_dispatch`** để lấy lượt B, dù nó có sẵn: dispatch thoả `if:` của
**ba job nightly** — trong đó `livechat-e2e-nightly` **ghi `OPENAI_API_KEY` thật ra `.env`** và
hai job kia gọi model tính tiền. Chúng đang không chạy được **nhờ billing hỏng** — dựa vào một
sự cố hạ tầng làm cơ chế an toàn là thứ sẽ phản lại ta đúng lúc nó được sửa. Lượt B lấy bằng
**một lần đẩy thường** (push không thoả `if:` của ba job đó).
