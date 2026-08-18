# DỰ BÁO — nhịp 2: 7 job khoá GIẢ sang self-hosted

> Công bố **trước**. Nền: `HEAD=bc5e698`, nhánh `dev/learning-loop`. tech-lead · 18/08/2026.
> Nhịp 1 → `scripts/DU-BAO-ci-self-hosted-2026-08-18.md`.

---

## 0. Phạm vi — 7, không phải 13

| chuyển | giữ `ubuntu-latest` | vì sao giữ |
|---|---|---|
| `lint-and-test` · `db-migration-test` · `frontend-lint-and-test` · `security-findings-gate` · `dependency-and-secret-scan` · `migration-chain` · `appsec` | 4 job nightly khoá thật | **NGÂN SÁCH**, xem §1 |
| | `route-guards-docker` · `livechat-e2e-nightly` | security chặn (ghi khoá thật ra đĩa máy dùng chung) |

## 1. 🔴 Vì sao 4 job nightly KHÔNG đi cùng nhịp này

Chúng **đang không chạy** — và không phải vì ta chặn:

```
① tính ephemeral của ubuntu-latest → lớp lưới KHÔNG AI KHAI (đã khai ở STATE §5.R)
② billing hỏng                     → lớp ĐANG thật sự chặn 4 job này
③ `if:` schedule/dispatch          → lớp DUY NHẤT còn lại sau khi ① ② mất
```

Chuyển chúng sang runner tự quản là **gỡ lớp ②**. Cron `0 20 * * *` **tối nay** sẽ gọi model bằng
khoá thật, **không ai ngồi xem**, và khoản chi chưa ai duyệt (A3 còn ~32K).

Bảng hạng của security xét **phơi nhiễm khoá** — đúng phần việc của họ, và **không xét chi phí**.
Bốn job ấy nằm rổ ✅ của security **và** rổ 🔴 của ngân sách. **Không bảng nào sai; cái rơi giữa
hai bảng là cái cắn.**

⟹ Sau nhịp này, `if:` nightly là **lớp phòng thủ đơn độc**. Một lớp đơn độc mà không ai khai nó là
lớp phòng thủ thì sẽ có người "dọn dẹp" nó ⟹ **đã ghi thẳng comment lên khối `schedule:`**.

## 2. Nhịp 2 đo được thứ nhịp 1 KHÔNG đo được

Nhịp 1 chỉ chứng minh: cấp máy được · `self-hosted` là nhãn đúng · `setup-python` + `pip` chạy được.

| job | thứ nó lần đầu kiểm trên runner BTC |
|---|---|
| `db-migration-test` | **`services: postgres`** ⟹ **runner CÓ Docker không** |
| `dependency-and-secret-scan` | `gitleaks/gitleaks-action@v2` — **action chạy bằng Docker** ⟹ lớp Docker thứ hai, đường khác |
| `frontend-lint-and-test` | `setup-node@v4` — tool cache Node trên máy lạ |
| 4 job còn lại | Python thuần, kỳ vọng như nhịp 1 |

**Vẫn CHƯA kiểm** ở nhịp này: `docker compose` v2, `-p`, tiền kiểm cổng, bước dọn. Chúng nằm ở
hai job security đang chặn ⟹ **bước dọn vẫn là mã CHƯA TỪNG THỰC THI** sau nhịp 2.

## 3. Phụ thuộc bắt buộc: commit `bc5e698` của tester phải lên CÙNG

[ĐO của tester] thiếu `docker`: `594 collected · 11 errors · Interrupted` ⟹ **0 ca chạy**. Bảy module
dò container **trong `skipif`**, tức **lúc IMPORT** ⟹ hỏng ở giai đoạn **thu thập**, xoá sạch kết quả
của **577 ca chẳng liên quan gì tới docker**.

⟹ Không có `bc5e698`, một lượt `0 passed` **không phân biệt được** *"runner thiếu docker"* với
*"suite hỏng"* — mà đó đúng là câu nhịp 2 sinh ra để trả lời. **Cùng nhịp, không tách.**

## 4. DỰ BÁO — điền TRƯỚC

| # | vật | DỰ BÁO | THẬT |
|---|---|---|---|
| 1 | `runs-on` | **8** self-hosted · **6** ubuntu-latest | |
| 2 | file `.github/` đổi | **1**, chỉ dòng `runs-on` + comment `schedule:` | |
| 3 | `src/` · `contracts/` · `tests/` · `deploy.yml` | **0 dòng** cả bốn (`tests/` là của tester, tôi chỉ ĐẨY) | |
| 4 | YAML parse | hợp lệ · 14 job | |
| 5 | 5 job Python thuần | **xanh** | |
| 6 | `db-migration-test` | **KHÔNG DÁM DỰ BÁO** — chưa biết runner có Docker | |
| 7 | `dependency-and-secret-scan` | **KHÔNG DÁM DỰ BÁO** — cùng lý do (+ gitleaks có thể đòi license cho org) | |
| 8 | `frontend-lint-and-test` | nghiêng **xanh**, tool cache Node tải được | |
| 9 | `lint-and-test` nếu runner KHÔNG có docker | **skip vài ca, KHÔNG `Interrupted`** — đây là phép nghiệm thu `bc5e698` | |
| 10 | 4 job nightly | **không chạy** (push không thoả `if:`) — nếu chạy là tôi sai phạm vi | |

## 5. Nếu khác thì nghi gì — và BA màu đỏ phải tách

🔴 Nghiệm thu §6③ của brief nằm ở đây. **Không được gộp:**

| đỏ vì | dấu nhận biết |
|---|---|
| **CODE** | test fail có tên ca, số ca thu thập bình thường |
| **HẠ TẦNG runner** | `docker: command not found` · `services` không dựng được · action Docker lỗi kéo ảnh |
| **ĐỤNG CỔNG** | chỉ có thể ở 2 job compose — **không job nào trong nhịp này** ⟹ nhịp 2 mà đỏ vì cổng là **bất ngờ**, phải điều tra |

| lệch | nghi |
|---|---|
| #1 ≠ 8/6 | tôi `sed` quá tay ⟹ job nightly lên runner ⟹ **tối nay tiêu tiền** |
| #9 ra `Interrupted` | `bc5e698` chưa lên, hoặc chưa phủ hết ⟹ dừng, đừng đọc `0 passed` thành "suite hỏng" |
| #10 có job nightly chạy | tôi đọc sai `if:` ⟹ **revert ngay**, đây là ca tiêu tiền không ai duyệt |

## 6. Khai trước — KHÔNG được tính là xác nhận

Nhịp 2 xanh ⟹ *"runner chạy được 8/14 job"*. **KHÔNG** ⟹ *"chuyển CI xong"*: 2 job nặng nhất
(compose, khoá thật, cổng host, bước dọn) **vẫn ở `ubuntu-latest` và vẫn không chạy được vì
billing**. Số job qua cổng thật sau nhịp 2 là **8/14**, và 6 còn lại **không phải "sắp xong"** —
mỗi cái bị chặn bởi một thứ khác nhau.
