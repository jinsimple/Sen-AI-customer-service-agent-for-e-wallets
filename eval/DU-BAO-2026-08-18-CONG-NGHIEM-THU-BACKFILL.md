# DỰ BÁO — cổng nghiệm thu backfill (ADR-032 việc ②)

> Vai: **tester** · 18/08, sau lần dựng ảnh · **0 token** · viết **TRƯỚC** khi
> đo. Mốc vật: **`bam_ma_nguon = d5b73a04d6ef`**.
> 🔴 **KHÔNG dùng `BUILD_COMMIT`** — PO-agent [ĐO] nhãn `bf1bd5a` **khác** mã
> đang chạy (ảnh dựng từ **cây làm việc**, không từ HEAD). Đúng vế thi hành
> Luật P: *đừng thay một con số chết bằng một con số dễ đọc nhầm.*

## ① Dữ kiện: script backfill CHƯA TỒN TẠI

`migrations/` không có file nào mới; `git log --all --grep=backfill` không có
commit nào của đợt này. ⟹ Cổng này viết **trước** vật nó nghiệm thu — nó **định
nghĩa điều backfill phải thoả**, không mô tả điều backfill đã làm.

🔴 **Và điều đó làm một việc thành KHẨN:** mẫu số **"sau"** đo lúc nào cũng
được; mẫu số **"trước"** chỉ đo được **trong cửa sổ từ giờ tới lúc backfill
chạy**. Bỏ lỡ cửa sổ này thì ADR-032 việc ② **vĩnh viễn không nghiệm thu được**
theo đúng yêu cầu *"đếm phân bố trước/sau"* của chính nó.

## ② 🔴 VÌ SAO "0 dòng plaintext" MỘT MÌNH LÀ CỔNG HỎNG

Cổng `test_cot_nhom_a_khong_nam_plaintext` (`b2825db`) đã khẳng định *"không
dòng nào nằm trần"*. **Một backfill chạy `DELETE FROM complaints` sẽ làm nó
XANH.** Đây là Luật 1 ở dạng nguy hiểm nhất: **bản cài đặt tầm thường nhất thoả
mãn assertion**.

Bốn kiểu hỏng mà "0 plaintext" **không** bắt được:

| # | kiểu hỏng | vì sao lọt |
|---|---|---|
| 1 | **mất dòng** (xoá/bỏ qua) | ít dòng hơn ⟹ vẫn 0 trần |
| 2 | **mất nội dung** (mã hoá một chuỗi rỗng) | đúng hình dạng `gAAAAA`, ruột rỗng |
| 3 | **mã hoá HAI LẦN** (dòng đã mã hoá bị mã hoá lại) | 🔴 hình dạng **không phân biệt được** — token bọc trong token |
| 4 | **mã hoá bằng khoá KHÁC** | hình dạng đúng, **không ai đọc được nữa** |

⟹ Cổng nghiệm thu phải bám **BỐN** mốc, không phải một: **số dòng · giải mã
được · không bọc hai lần · nội dung không đổi.**

## ③ Cách đo — hộp đen, KHÔNG đọc `src/`, KHÔNG in nội dung

Dùng `cryptography.fernet` **thẳng** trong container với `FIELD_ENCRYPTION_KEY`
của chính container. Đây là **thư viện công khai + biến môi trường**, không phải
đọc mã sản phẩm. Ba trạng thái tự rơi ra:

```
decrypt OK                        → giải mã được
InvalidToken  + mở đầu gAAAAA     → KHOÁ KHÁC
InvalidToken  + không mở đầu      → chưa mã hoá (plaintext)
decrypt OK NHƯNG ruột mở đầu gAAAAA → 🔴 BỌC HAI LẦN
```

**Nội dung không đổi — đo bằng VÂN TAY GỘP, không lưu vân tay từng dòng:**
`md5` mỗi bản rõ → sắp xếp → `md5` của chuỗi nối. Một con số cho cả cột.
🔴 **Cố ý KHÔNG lưu băm theo dòng:** băm của một câu ngắn là thứ **dò ngược
được**, và một tệp trong git chứa 761 băm lời khai khách là một tài sản PII mới
do chính bộ đo tạo ra — đúng Luật 10 (*bộ đo tự tạo ra hiện tượng nó đang đo*),
ở trục rủi ro thay vì trục kết quả. Vân tay gộp trả lời đúng câu cần hỏi
(*"tập nội dung có đổi không"*) và **không trả lời được** câu không nên hỏi.

## ④ Đối chiếu mẫu số ĐẦU của tech-lead — kiểm thành phần, không nhận số

PO-agent chuyển: `1.113 giải mã được / 738 chưa mã hoá / 0 khoá khác`.
Tôi **không nhận con số**, tôi kiểm nó **cộng lại từ đâu**:
```
messages.content        467
policy_chunks.text      378
bank_accounts.account_no 245
complaints.description_raw 23
                     ─────
                      1.113  ✅ khớp
```
⟹ `1.113` là mẫu số của **cả bốn cột Nhóm A**, không phải của riêng
`complaints`. Số của tôi (`738 trần / 23 mã hoá` **trên `complaints`**) và số
của họ **cùng một sự thật, hai mẫu số khác nhau**. Ghi rõ để không ai trừ chéo.

## ⑤ DỰ BÁO

| # | dự báo | độ chắc | nếu khác thì nghi gì |
|---|---|---|---|
| 1 | `complaints.description_raw` vẫn **738 trần / 23 giải mã được** | **rất cao** | khác ⟹ **ai đó đã chạy backfill mà không báo** — DỪNG, hỏi, đừng ghi "đã vá" |
| 2 | **0** dòng khoá khác, cả bốn cột | **cao** | >0 ⟹ khoá đã bị xoay ⟹ finding nặng hơn ADR-032 |
| 3 | **0** dòng bọc hai lần, cả bốn cột | **cao** | >0 ⟹ đã có một lần backfill/di trú chạy hai lần trong quá khứ |
| 4 | tổng bốn cột: **1.113 giải mã được** | **cao** | lệch ⟹ số của tech-lead đo trên ngăn xếp khác, hoặc đã đổi |
| 5 | container **thật sự** chạy nhánh ba trạng thái | **trung bình** | 🔴 tôi **tự kiểm**, không nhận lời — đây đúng cạm bẫy tôi đã ghi vào sổ hôm 12/08 |

🔴 **Khai trước:** dự báo 1 TRÚNG nghĩa là **chưa có gì được vá** — đó là kết
quả **đúng** cho lúc này, không phải tin xấu. Cổng này sinh ra để **đỏ cho tới
khi backfill chạy**, giống cổng plaintext.

## ⑥ Điều cổng này KHÔNG chứng minh

- **Không** chứng minh nội dung *đúng nghiệp vụ* — chỉ chứng minh nó **không
  đổi** giữa hai lần đo. Backfill làm hỏng dữ liệu **trước** lần đo đầu thì
  cổng này im.
- **Không** phủ 10 cột `json`/`jsonb`/`bytea` (kho checkpoint) — phạm vi đó đã
  được PO chốt là **ADR riêng**.
- Vân tay gộp bảo *"tập có đổi"*, **không** bảo *"dòng nào đổi"*. Đó là đánh
  đổi **cố ý** đã nêu ở ③.
