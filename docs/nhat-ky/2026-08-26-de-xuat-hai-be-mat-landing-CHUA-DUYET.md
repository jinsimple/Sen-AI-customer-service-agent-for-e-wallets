# ĐỀ XUẤT (CHƯA DUYỆT, KHÔNG PHẢI ADR) — Tách hai bề mặt: landing theo fin.ai, màn nghiệp vụ giữ Stripe

> 🔴 **NIÊM 27/08 — TỆP NÀY TỪNG MANG SỐ `ADR-053`. ĐÃ GỠ SỐ.**
>
> **Vì sao gỡ:** nó **chiếm trước** một số ADR mà nó chưa bao giờ được duyệt để mang. Người viết
> ADR-053 thật sẽ đụng số — hoặc tệ hơn, **đọc tệp này và tin nó là một quyết định đã ratify.**
> Chuyện đó **đã xảy ra thật**: phiên Marketing trích nó làm căn cứ thiết kế, vế *"nháp, chưa
> duyệt"* rụng mất trên đường đi, và thứ còn lại trông như một quyết định.
>
> 🔴 **Và commit `cf7a122` (đưa tệp vào git) làm vế đó NẶNG THÊM, không nhẹ đi** — nằm trong repo
> khiến nó **dễ tin hơn** lúc còn là tệp lạc. Đó là hệ quả tôi không lường khi commit.
>
> **NỘI DUNG DƯỚI ĐÂY TẢ MỘT TRANG CHƯA BAO GIỜ ĐƯỢC DỰNG.** Marketing đo 27/08:
> ```
> grep -riE 'particle|magnetic' frontend/src/  → 0 dòng mã (chỉ trúng bình luận viết VỀ sai sót này)
> grep Playfair frontend/src/                  → 0
> globals.css:600 .lp-hero → linear-gradient(120deg,#F6F9FC,#FFE9F3,#FFF6D9), chữ #0A2540
>                            TĨNH, hồng/vàng — KHÔNG phải cam #FF5B24 như tệp này mô tả
> ```
> ⟹ **Đọc tệp này như một ĐỀ XUẤT LỊCH SỬ, không phải mô tả sản phẩm.** Muốn biết trang `/` hôm
> nay trông thế nào thì **mở `globals.css` hoặc mở trang thật ra xem** — đừng đọc tệp này.
>
> *(Giữ nguyên toàn văn bên dưới. Luật P: chuyển chỗ + niêm, không xoá.)*

> **Trạng thái: NHÁP.** Chưa vào `docs/DECISIONS.md`. Soạn 26/08/2026 bởi phiên
> Claude dựng landing page, theo yêu cầu PO. Cần PO duyệt trước khi bất kỳ ai
> sửa `frontend/src/`. Quy trình bắt buộc: CLAUDE.md §3.

## Bối cảnh

Ngày 26/08/2026 tồn tại **hai landing page song song**, hai hướng thương hiệu
xung đột, do hai phiên Claude khác nhau dựng trong cùng một ngày:

| | Landing trong repo | Landing ngoài (đã chốt dùng) |
|---|---|---|
| Vị trí | `frontend/src/app/page.tsx` (144 dòng) | artifact ngoài, chưa vào repo |
| Dựng lúc | 26/08 09:28 → 11:17 (5 commit) | 26/08, cùng ngày |
| Hướng | clone **stripe.com** | clone **fin.ai** |
| Nền | `#F6F9FC` | `#FAF9F6` |
| Accent | `#635BFF` tím | `#FF5B24` cam |
| Token | dùng `var(--*)` của app | bộ token riêng |

`frontend/src/app/globals.css` ghi nguyên văn: *"26/08 vòng 2 — PO đổi hướng
lần 3: clone style từ stripe.com — màu chữ, màu nền, màu chủ đạo, rồi dựng
landing page đồng bộ."*

Lịch sử theme tới nay: Trust Navy + Gold → Mận Sen (`#4C1D95`/`#C026D3`) →
vòng lục (`#5EB68D`) → Stripe (`#635BFF`) → nay là fin.ai. **Lần thứ năm.**

Nội dung hai bản gần như trùng nhau — cùng chốt ở luận điểm "điều tra trong
vài phút, quyết định vẫn thuộc về con người" và "không phải lời hứa, là con số
đếm được".

## Quyết định

1. **Landing theo fin.ai được chọn.** Landing Stripe tại `/` bị bỏ.
2. **Phạm vi đổi CHỈ là route marketing.** Màn nghiệp vụ (`(app)/…`) giữ
   nguyên bộ token Stripe hiện có trong `globals.css`.

## Vì sao KHÔNG sơn lại toàn app

`FIN05-Theme-Options.md` đã phân sẵn hai nhóm người dùng:

> *Customer — giao diện khách hàng, ưu tiên thân thiện, đa độ tuổi.*
> *Agent — giao diện nội bộ CSKH, dùng liên tục 8 tiếng/ngày, ưu tiên chống
> mỏi mắt, quét thông tin nhanh.*

Landing là bề mặt Customer. Màn nghiệp vụ là bề mặt Agent. Ba lý do cụ thể:

- **Bộ token Agent đã đo xong.** Mọi màu trong `globals.css` có số đo WCAG ghi
  kèm, `--text-faint` từng bị axe-core bắt trượt 3.05:1 và đã sửa. Đổi lần thứ
  năm là ném đi toàn bộ công đo đó.
- **Thang chữ đã gộp từ 17 cỡ xuống 6 bậc**, bỏ hết nửa pixel. Bộ chữ của
  landing (Playfair Display) là serif tương phản cao — đẹp ở 94px, nhưng nét
  mảnh biến mất ở 13px trong bảng dữ liệu, dấu tiếng Việt càng tệ.
- **Hiệu ứng của landing không được vào app.** Particles, magnetic CTA, glow
  thẻ là chi phí nhận thức trên công cụ dùng 8 tiếng/ngày — và ở màn xét duyệt
  hoàn tiền, chuyển động kéo mắt khỏi con số đang cần đọc kỹ.

## Bộ token landing — đã đo, không phải ước lượng

| Token | Giá trị | Đo |
|---|---|---|
| `--paper` | `#FAF9F6` | nền trang |
| `--panel` | `#F1EEE9` | nền khối hình |
| `--ink-40` | `#6B6B6B` | 5.06 kem · 4.61 panel · 5.33 trắng |
| `--sen` | `#FF5B24` | **2.94:1 — CHỈ trang trí**, cấm làm màu chữ/nét |
| `--sen-deep` | `#C7400F` | 4.78 kem · 4.35 panel — chữ và nét có nghĩa |
| `--sen-btn` | `#D4430F` | trắng trên nó 4.56:1 — nền nút |
| `--stop` | `#B3261E` | 5.61 trên `--stop-wash` |
| `--ok` | `#14795C` | 4.63 trên panel |

Chuyển động: easing `cubic-bezier(.165,.84,.44,1)` · reveal 800ms ·
mask-wipe hero 1800ms · blur-fade 1000ms. Số đo lấy trực tiếp từ fin.ai
bằng computed style ngày 26/08/2026.

## Đã kiểm

- **axe-core WCAG 2.1 A/AA**: 0 vi phạm ở 1440×900 và 390×844.
- **Hiệu năng**: p50 16.7ms cả desktop lẫn mobile (CPU ÷4). Rớt nhịp 1–6%.
- Ba lỗi tương phản của bản đầu đã sửa (xem bảng token).

## Hệ quả

- `frontend/src/app/page.tsx` — thay bằng landing mới, hoặc gỡ và dựng lại.
- `globals.css` — **không đổi** phần token dùng chung. Token landing đặt trong
  scope riêng của route marketing, không đổ vào `:root`.
- Bình luận "PO đổi hướng lần 3 → clone Stripe" trong `globals.css` đã **lỗi
  thời một nửa**: vẫn đúng cho màn nghiệp vụ, sai cho landing. Cần niêm lại.
- Chạy lại: `frontend/e2e/accessibility.spec.ts`, và bộ `playwright.qa-stripe`
  nếu bộ đó có case chạm route `/`.
- `docs/2026-08-26-noi-dung-landing-page.md` — đối chiếu xem nội dung 14 lý do
  có khớp bản PO duyệt không.

## Câu hỏi mở

1. ~~Landing mới đặt ở `/` hay tách sang route riêng?~~ **Đã kiểm 26/08:**
   không file nào trong `frontend/e2e/` gọi `goto('/')` hay nhắc tới
   "landing"/"gioi-thieu" — thay landing ở `/` không làm đỏ bộ e2e hiện có.
   Lưu ý `src/proxy.ts` có nhánh riêng cho `pathname === "/"` (cố ý tách khỏi
   `PUBLIC_PATHS`) — giữ nguyên nhánh đó khi thay trang.
2. Playfair Display có bộ Vietnamese (đã xác minh), nhưng đây là font thứ ba
   nạp thêm — chấp nhận chi phí tải trên route marketing?
3. Bốn loại khiếu nại trong ma trận taxonomy vẫn chưa có tên chính thức trên
   landing — chờ điền.
