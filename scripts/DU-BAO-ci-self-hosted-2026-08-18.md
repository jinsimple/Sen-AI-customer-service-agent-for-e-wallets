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
| 1 | file đổi | **1** — `.github/workflows/ci.yml` | |
| 2 | `runs-on: self-hosted` | **1** (job `invariants`), còn **13** `ubuntu-latest` | |
| 3 | lệnh compose mang `-p` | **8/8** | |
| 4 | bước dọn thêm | **2**, `if: always()` **trần**, không guard | |
| 5 | tiền kiểm cổng thêm | **2** | |
| 6 | `deploy.yml` · `src/` · `contracts/` · `tests/` | **0 dòng đổi** cả bốn | |
| 7 | YAML parse | hợp lệ, 14 job | |
| 8 | cổng cục bộ (invariants) | **23 passed** — `src/` không đổi thì không có lý do đổi | |
| 9 | token tiêu | **0** | |
| 10 | sau khi đẩy: job `invariants` | **KHÔNG DÁM DỰ BÁO** — xem §5 | |

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
