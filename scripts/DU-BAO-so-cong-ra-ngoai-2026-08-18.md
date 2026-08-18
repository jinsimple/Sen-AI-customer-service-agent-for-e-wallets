# DỰ BÁO — đổ `so_luot_da_phat` vào SỔ trên volume (Giai đoạn 2 ①)

> Công bố **trước** khi viết dòng nào. Nền: `HEAD=8e32808`, băm `src/` = `d5b73a04d6ef`
> (khớp cả ba ảnh, lệch× 0·0·0). tech-lead · 18/08/2026.

---

## 0. Vá đúng lỗ tôi tự khai, không mở rộng phạm vi

Sáng nay tôi land bộ đếm ba rổ rồi **tự bác cách nó được mô tả**: nó là `dict` trong RAM, **4 worker
= 4 bộ đếm**, về 0 mỗi lần recreate, không đọc được từ ngoài tiến trình. PO-agent đã định ghi nó
vào STATE là *"mốc nền đầu tiên của dự án"* — sai, và tôi khai trước khi nó thành một con số ai đó
tin. **Việc này đóng đúng khoảng cách đó**, không hơn.

## 1. 🔴 Việc ③ trong danh sách Giai đoạn 2 KHÔNG CẦN LÀM — việc ① nuốt nó, theo hướng TỐT HƠN

Danh sách có mục *"một đường đọc bộ đếm từ ngoài tiến trình"*. Nếu làm bằng **endpoint** thì nó
**đụng `contracts/`**: thêm route ⟹ `authority-matrix.yaml` đổi ⟹ INV-00 đỏ ⟹ phải đi đủ §10 —
đang bị cấm.

**Nhưng sổ trên volume ĐÃ LÀ đường đọc từ ngoài tiến trình, và nó mạnh hơn endpoint ở đúng chỗ
quan trọng:**

| | endpoint | sổ trên volume |
|---|---|---|
| gộp được **4 worker** | ❌ trả về số của **một** worker ngẫu nhiên | ✅ cả bốn cùng ghi một file |
| sống qua **recreate** | ❌ | ✅ named volume |
| cần đổi **contract** | ✅ có | ❌ không |

⟹ **Bỏ ③ khỏi danh sách, không phải hoãn nó.**

## 2. SỔ RIÊNG, không nhét vào `usage.jsonl`

`usage.jsonl` là **một dòng một LƯỢT CHAT** (18 trường, có `thread_id`, `ly_do_fallback`, `duong`…).
Sự kiện của tôi là **một dòng một REQUEST HTTP** — khác hạt, khác dân số.

🔴 Trộn hai hạt vào một file là dựng lại đúng bẫy **"dân số pha tạp"** (§8): ai `wc -l` sổ ấy sẽ ra
một con số **không phải số lượt, cũng không phải số request**, và nó **trông hợp lệ**. Dự án đã trả
giá cho `4%` (13/370) và cho `so_luot_goi_model = 0`.

⟹ File riêng `cong_ra_ngoai.jsonl`, **cùng volume**. Nhưng **dùng lại đúng hàm ghi** của
`so_usage.py` (thêm tham số `duong`), **không viết writer thứ hai**: nó đã có sẵn hai tính chất khó
làm lại đúng — *không bao giờ làm hỏng lượt vì lỗi ghi sổ*, và *cảnh báo MỘT lần thay vì mỗi lượt*.
Hai định nghĩa của cùng một vật sẽ lệch trong im lặng.

## 3. Ghi GÌ — và KHÔNG ghi gì

```
ghi   ts · ro (da_phat|bi_chan|hong) · host · duong(path) · ly_do(cờ) · bam_ma_nguon · pid
KHÔNG ghi   query string · thân request · khoá · nội dung khách
```
🔴 `path` thì ghi, **query string thì không**: một số nhà cung cấp mang tham số ở đó. Dựng một
đường rò vào log **ngay trong cơ chế sinh ra để chặn rò** là hỏng theo cách buồn cười nhất.
`pid` có mặt để phân biệt **4 worker** — thiếu nó thì sổ gộp được nhưng không tách lại được.

## 4. DỰ BÁO — điền TRƯỚC

| # | vật | DỰ BÁO | THẬT | |
|---|---|---|---|---|
| 1 | file `src/` đổi | **2** — `cong_ra_ngoai.py` + `so_usage.py` | | |
| 2 | `contracts/` · `check_contracts` | 0 đổi · sạch | | |
| 3 | `test_invariants.py` | **23 passed** | | |
| 4 | suite `not security_finding` | **0 failed** | | |
| 5 | ca đối chứng: 1 lượt **bị chặn** | sổ có **3** dòng `bi_chan` (SDK retry 3 lần) | | |
| 6 | ca đối chứng: 1 lượt **hỏng** | sổ có **1** dòng `hong` | | |
| 7 | sổ KHÔNG chứa query string | 0 dòng có `?` trong trường `duong` | | |
| 8 | `usage.jsonl` | **không thêm dòng nào** — hai sổ tách rời | | |
| 9 | `docker diff` | 0 · 0 · 0 | | |
| 10 | token tiêu | **0** | | |

## 5. Nếu khác thì nghi gì

| lệch | nghi |
|---|---|
| #5 ra **1** thay vì 3 | tôi cắm bộ đếm **trên** SDK chứ không **dưới** ⟹ mất đúng loại lượt đắt nhất (lượt retry), đúng bẫy `so_luot_goi_model=0` |
| #8 `usage.jsonl` dài ra | hai sổ đang dùng chung đường ⟹ **dân số pha tạp**, revert ngay |
| #4 đỏ | ghi sổ đang làm hỏng đường nóng ⟹ **revert**, không vá chồng: `ghi_usage` có hợp đồng *"không bao giờ làm hỏng lượt"* |
| #7 > 0 | tôi ghi cả query string ⟹ vừa mở đường rò trong chính cơ chế chống rò |

## 6. Khai trước — KHÔNG được tính là xác nhận

Sổ có dòng ⟹ *"cơ chế ghi được"*. **KHÔNG** ⟹ *"đã có mốc nền cho câu tiêu-bao-nhiêu"*: sổ này đếm
**số LƯỢT GỌI RA DÂY**, **không** đếm **token** và **không** đếm **tiền**. Muốn ra tiền thì phải
nối với `usage` của nhà cung cấp — và [ĐO §6.⓷] nhà cung cấp tính theo thứ họ **sinh**, không theo
thứ ta **đọc**, nên rổ `hong` vẫn là **"không đọc được"** kể cả khi đã vào sổ.

## 7. KẾT QUẢ THẬT

*(để trống)*
