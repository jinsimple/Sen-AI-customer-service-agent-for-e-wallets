# Giao việc — TECH-LEAD · 18/08/2026 · chuyển CI sang runner self-hosted của BTC

> Viết cho người đọc **NGUỘI**. Đọc `docs/DECISIONS.md` → **ADR-037** trước. Việc này **gấp**: từ
> 17/08 tới nay **không commit nào qua cổng tự động nào**.

🔴 **Luật Q trước tiên:** `git rev-parse --abbrev-ref HEAD && git log --oneline -1`.
Nhánh đúng: **`dev/learning-loop`**.

## 0. Chuyện gì đang xảy ra

CI đỏ **không phải vì code**. [ĐO] annotation nguyên văn GitHub:
*"The job **was not started** because recent account payments have failed…"*, và
`gh run view --job … --log` → **`log not found`, 0 dòng**. Job chưa từng được cấp máy.

BTC cho dùng **runner dùng chung của chương trình** (FIFO, chia sẻ giữa mọi team) bằng cách đổi
`runs-on`.

## 1. Việc — đo trước khi gõ

```
[ĐO] grep -rn "runs-on:" .github/workflows/
     .github/workflows/ci.yml      14 dòng   → ĐỔI thành  self-hosted
     .github/workflows/deploy.yml   1 dòng   → 🚫 GIỮ NGUYÊN ubuntu-latest
```

**Vì sao `deploy.yml` KHÔNG đổi:** nó mang `secrets.DEPLOY_SSH_KEY` — khoá riêng SSH vào
**production** — và nó đang **skipped** ở mọi run gần đây. Chuyển nó **không mua được gì** mà đặt
tài sản nặng nhất lên máy dùng chung với các team khác. (ADR-037 QĐ2)

## 2. Điều kiện tiên quyết — KIỂM, đừng giả định

Runner BTC **không nhất thiết** có sẵn như `ubuntu-latest`. `ci.yml` của ta cần:

| cần | dùng ở đâu |
|---|---|
| **Docker** | `services: postgres:16-alpine` (`ci.yml:118-120`) |
| **Docker Compose v2** | `docker compose up -d --build` (`ci.yml:560` · `623`) |
| `actions/setup-python@v5` · `actions/setup-node@v4` | nhiều job |

Cách kiểm rẻ nhất: đổi **một** job trước (gợi ý `invariants` — nhẹ, khoá giả, không cần compose),
đẩy, xem nó có xanh không. **Xanh rồi mới đổi 13 job còn lại.** Đừng đổi cả 14 rồi đoán xem cái nào
hỏng vì lý do gì.

## 3. 🔴 Cổng đụng nhau — cái này SẼ cắn nếu bỏ qua

`docker compose` của ta publish cổng ra host. Runner **dùng chung** ⟹ hai team chạy cùng lúc trên
một máy ⟹ **đụng cổng** ⟹ cổng ĐỎ vì lý do **không liên quan gì tới code ta**. Đúng lớp tín hiệu
giả nguy hiểm nhất: đỏ mà không phải lỗi mình.

⟹ **Bắt buộc `-p` với tên project DUY NHẤT theo run:**
```bash
docker compose -p fin05-ci-${{ github.run_id }} up -d --build
```
Và **mọi** lệnh compose sau đó trong cùng job phải mang đúng `-p` ấy (`ps`, `exec`, `logs`, `down`).

## 4. 🔴 Khoá thật trên máy dùng chung

[ĐO] phân loại 14 job:
```
8 job  khoá GIẢ (ci-dummy / test-key-…)                  → chuyển: không thêm phơi nhiễm
6 job  khoá THẬT secrets.OPENAI_API_KEY
└─ 2 trong đó GHI KHOÁ THẬT RA TỆP .env TRÊN ĐĨA runner:
   route-guards-docker  (ci.yml:554)
   livechat-e2e-nightly (ci.yml:618)
```

**Việc của bạn ở đây — một thứ, làm cùng lúc với đổi `runs-on`:**
bước dọn tệp `.env` ở hai job đó phải là **`if: always()`**. Dọn chỉ khi job thành công là
**không dọn ở đúng lúc cần dọn nhất** (job bị huỷ giữa chừng để lại khoá thật trên đĩa máy dùng chung).

🚫 **Không tự quyết chuyện xoay khoá OpenAI** — `security` đang định hạng, PO quyết. Bạn chỉ làm
phần cơ học: `if: always()`.

## 5. Điều KHÔNG được làm

- 🚫 **Không đụng `deploy.yml`.**
- 🚫 **Không sửa nội dung test / không nới cổng nào** để "cho CI xanh". Việc này là **hạ tầng**,
  không phải sửa cổng. Cổng đỏ vì code thì để nó đỏ — đó là lần đầu ta thấy chúng chạy từ 17/08.
- 🚫 **Không `docker compose down -v`** (mất `usage.jsonl` + `postgres_data` ở máy local).
- 🚫 **Mọi lệnh `git` phải có pathspec** — cây dùng chung, đã 3 sự cố.

## 6. Nghiệm thu — dán số thật

```
① đổi 1 job (invariants) → đẩy → job CÓ khởi động không? (có log ≠ 0 dòng = ĐÃ được cấp máy)
② đổi 13 job còn lại     → đẩy → dán bảng 14 job: xanh/đỏ, và ĐỎ VÌ GÌ
③ với mỗi job đỏ: phân biệt rõ  "đỏ vì CODE"  ≠  "đỏ vì HẠ TẦNG runner"  ≠  "đỏ vì đụng cổng"
```

⚠️ **Ba trạng thái ở bước ③ là bắt buộc, không được gộp.** Gộp "đỏ vì hạ tầng" vào "đỏ vì code" sẽ
đẩy cả đội đi truy một bug không tồn tại — chuyện này đã suýt xảy ra một lần (Luật 19 ③).
