# Hồ sơ nộp — FIN-05 · Đội T226

> **Thư mục này để PO lấy file đi nộp.** Cập nhật 20/08/2026.
>
> 🔴 **`gate/` LÀ BẢN SAO, KHÔNG PHẢI NGUỒN.** Sửa tài liệu thì sửa ở nguồn (`docs/`, `contracts/`,
> gốc repo) rồi chạy `bash gate/lam-moi.sh`. Sửa thẳng trong đây sẽ bị ghi đè — và tệ hơn, tạo ra
> một nguồn sự thật thứ hai.
>
> 🔴 **XOÁ CẢ THƯ MỤC NÀY KHÔNG ẢNH HƯỞNG GÌ TỚI ĐỘI.** [ĐO 20/08] `scripts/check_contracts.py` chỉ
> quét `tests · docs · src · eval · frontend/e2e` — không có `gate/`. Không test nào, không job CI
> nào, không script nào của đội đọc thư mục này. `gate/` chứa **0 file `.py`**.
>
> Hai file **không có bản gốc nơi khác** — viết riêng cho hồ sơ nộp, sống ngay trong đây:
> `05-nhat-ky-tuan.md` và `06-pitch-deck.md`. Script sao chép không đụng tới chúng.

---

## Mười mục cần nộp

| # | mục | trạng thái | ở đâu |
|---|---|---|---|
| 1 | **Source code** | ✅ | chính repo — 56 file Python · 67 file TS/TSX |
| 2 | **README.md** | ✅ | [`01-tong-quan/README.md`](01-tong-quan/README.md) |
| 3 | **Sơ đồ kiến trúc** | ✅ | [`02-kien-truc/so-do-kien-truc.md`](02-kien-truc/so-do-kien-truc.md) · bản đầy đủ: `ARCHITECTURE.md` ở gốc repo |
| 4 | **Đặc tả & thiết kế** | ✅ | [`03-dac-ta-thiet-ke/`](03-dac-ta-thiet-ke/) — PRD · Brief · 46 ADR · 3 contract |
| 5 | **Tài liệu kiểm thử** | ✅ | [`04-kiem-thu/`](04-kiem-thu/) — cách chạy · chuẩn viết test (21 luật) |
| 6 | **Nhật ký tuần** | ✅ | [`05-nhat-ky-tuan.md`](05-nhat-ky-tuan.md) — dựng từ 982 commit thật |
| 7 | **Live URL** | 🔴 **CHƯA CÓ** | xem mục "Việc chỉ PO làm được" |
| 8 | **Video demo** | ⬜ **PO tự quay** | kịch bản 8 màn: `docs/giao-viec/2026-08-15-kich-ban-demo-mvp.md` |
| 9 | **Pitch deck** | ✅ nội dung | [`06-pitch-deck.md`](06-pitch-deck.md) — 14 slide, PO đổ vào slide + trình bày |
| 10 | **AI Log** | ⬜ **PO xác nhận** | ngoài repo, đội không kiểm được từ đây |

---

## 🔴 Việc chỉ PO làm được — và mục 7 đang chặn

### ① Live URL — vấn đề lớn nhất của hồ sơ

**`README.md` hiện ghi `https://app.adaptivealgo.uk`. Bản chạy ở đó là repo `P-121-new`, KHÔNG phải
P-226.** Người review bấm link trong repo này sẽ trải nghiệm **một sản phẩm khác với mã nguồn họ đang đọc.**

P-226 **chưa từng được deploy lần nào**. Ba bước:

```bash
git push origin dev/learning-loop:main     # main đang thiếu 77 commit
# rồi deploy theo: docs/devops/2026-08-20-checklist-deploy-lan-dau.md
# khoá API production PO tự điền trên VPS — không đi qua phiên agent nào
```

Sổ tay deploy đọc dễ: **https://claude.ai/code/artifact/cac93278-37d9-4e87-8ab3-83bd6f8c26b1**
— 6 bước đã có người đi hết trên bản clone sạch, 6 chỗ đứt đã tìm ra và vá.

### ② Bấm tay trên dashboard

- **Bật billing GitHub Actions** — 4 job CI hiện **chưa từng chạy một giây nào** (`runner_name` rỗng),
  nhưng hiện màu đỏ y hệt một bài kiểm trượt.
- **Lưu `GITLEAKS_LICENSE` thành GitHub Secret** — miễn phí tại gitleaks.io.

### ③ Ba câu nghiệp vụ đang chờ *(chi tiết trong ADR-045)*

- Che số điện thoại trong live-chat tới mức nào? *(đang giữ 1 job CI đỏ)*
- Giữ hội thoại khách bao lâu rồi xoá? *(hiện **không có gì xoá nó bao giờ**)*
- VPS đặt ở đâu · ARM hay x86 · có mở cổng Postgres ra ngoài không?

---

## Điểm nên nhấn khi trình bày

| | |
|---|---|
| **Ràng buộc cứng ép bằng test** | 5 ràng buộc → **23 test introspect app đang chạy thật** (đọc route, moi guard từ closure, đọc CHECK constraint qua AST). Đỏ = build hỏng. |
| **Contract là nguồn sự thật** | Cấu trúc hệ thống sống trong `contracts/`, không sống trong code. Thêm route · đổi guard · đổi tên tool mà quên cập nhật contract → **đỏ ngay**. |
| **Guardrail độc lập với model** | O1–O4 là regex tất định. Đổi model không làm lưới cuối yếu đi — đó là lý do dám xoay 4 model tự động. |
| **46 ADR có lý do BÁC phương án khác** | Không chỉ ghi "đã chọn gì", mà ghi "vì sao không chọn cái kia". |
| **Kỷ luật đo lường** | Ngày 20/08 bắt được **9 khẳng định sống lâu hơn sự thật của nó** — cả 9 **niêm tại chỗ kèm bằng chứng, không xoá**. Trong đó có lỗi của chính người điều phối, ghi tên. |

🔴 **Và mang theo slide 9** — *"Điều chúng tôi CHƯA chứng minh được"*. Điểm 87,7% là mốc **16/08**,
không phải điểm bản đang chạy, và nó **loại trục Trải nghiệm khỏi mẫu số**. Nói ra trước khi bị hỏi.

---

## Sao chép lại khi tài liệu nguồn đổi

```bash
bash gate/lam-moi.sh     # rồi xem gate/MANIFEST.md
```

`MANIFEST.md` ghi **băm sha256 của bản gốc** tại thời điểm sao chép. Băm khác đi ⟹ bản sao đã cũ.

📁 [`lich-su/`](lich-su/) — hồ sơ các đợt nộp trước, đã niêm số cũ, giữ làm bản ghi.
