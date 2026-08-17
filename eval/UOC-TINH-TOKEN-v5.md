# Ước tính token cho v5 — trước khi chạy

> Vai: **tester** · 17/08. PO hỏi trước khi mở khe. **Không tốn lượt LLM nào**:
> tất cả rút từ `usage.prompt_tokens` **đã đo** của v4 + tiktoken cục bộ.

## Hai kích thích, đo bằng tiktoken `o200k_base`

| | ký tự | token | băm |
|---|---:|---:|---|
| system **BỘ ĐO** (v4, tôi soạn) | 123 | **37** | `9d6dbff3bc7f` |
| system **SẢN PHẨM** (`build_system_prompt`) | 15.094 | **4.587** | `33d66da05520` |

⟹ **chênh +4.550 token mỗi lượt** — với `gpt-4o-mini` con số này **chính xác**,
vì `o200k_base` đúng là tokenizer của nó và đây là văn xuôi thuần, không có mơ
hồ tuần tự hoá.

## Hiệu chuẩn tokenizer Qwen — không đoán, bắc cầu qua một mẫu số CHÍNH XÁC

`gpt-4o-mini` đạt **10/10 "đúng"** ở ca 7 (ca kiểu TẬP) ⟹ mọi rep đi hết 3 vòng
⟹ **đúng 100 lượt**, không phải khoảng. Đó là mẫu số duy nhất trong bộ không có
bất định, nên nó thành chuẩn:

    gpt-4o-mini: 175.870 token vào / 100 lượt = 1.759 token/lượt

Các model khác nhận **cùng payload**, chỉ khác tokenizer và số lượt (ca 7 gãy
sớm thì ít lượt hơn). Chia ra được tỉ lệ:

| model | token/lượt (đo) | tỉ lệ vs `o200k` | system SP quy đổi | **v5 tổng/model** |
|---|---:|---:|---:|---:|
| `qwen3.8-max` | 2.275–2.298 | **1,29–1,31×** | 5.933–5.993 | **816K–822K** |
| `qwen3.7-plus` | 2.191–2.259 | 1,25–1,28× | 5.715–5.891 | 786K–803K |
| `qwen3.7-flash` | 2.117–2.229 | 1,20–1,27× | 5.522–5.813 | 759K–788K |
| `gpt-4o-mini` | 1.759 (chính xác) | 1,00 | 4.587 | **631K** |

> ⚠️ **Tỉ lệ này áp cho TOÀN payload**, trong đó phần lớn là văn xuôi tiếng
> Việt (mô tả tool 680–1.266 ký tự mỗi cái). Phần lược đồ JSON có thể lệch tỉ lệ
> khác. Đây là **ước lượng có biên**, không phải phép đếm — con số duy nhất
> **đếm được** là `4.587` cho `gpt-4o-mini`.

## 🔴 Chỗ ước tính của PO lệch, và vì sao

PO tính **~625K** (`15.094 ký tự ≈ 5.000 token × 125 lượt`). Hai chênh:

1. **Số lượt là 100, không phải 125** — kéo xuống.
2. **Tokenizer Qwen đắt hơn 1,29–1,31× trên tiếng Việt** — kéo lên mạnh hơn.
3. **Nền v4 (227K) vẫn phải cộng vào** — 625K là *phần thêm*, không phải tổng.

⟹ Với `qwen3.8-max`: **816K–822K**, cao hơn ước tính PO **~31%**.

## 🔴 Câu chặn: `1M` là HẠN NGẠCH hay là NHỊP?

Hai cách đọc cho **hai kết luận ngược nhau**, và tôi không được chọn hộ:

- **1M = TPM (token mỗi PHÚT)** — đây là thứ **tôi đã đo** ở các lượt trước.
  Thì `816K` **không phải 82% của một ngân sách**, mà là 82% lượng cho phép của
  **một phút**. Rải qua 5 phút là chuyện vặt. **Không cần nạp tiền.**
- **1M = tổng token miễn phí/model** — thì v5 ăn **82%** phần free của `max`, và
  đợt An toàn 140 lượt **không còn chỗ**. **Phải nạp tiền trước khi chạy.**

**Tôi ghi nhận nó là TPM.** Nhưng tôi không đo được điều khoản tài khoản từ đây,
và PO đang dùng nó như hạn ngạch. **Xác nhận điều này trước khi mở khe** — sai
chiều nào cũng đắt: một chiều làm hỏng đợt đo sau, chiều kia làm tiêu tiền vô ích.

## Đòn bẩy chưa đo: bộ nhớ đệm tiền tố

Cả 100 lượt dùng **cùng một tiền tố 4.587 token, giống hệt từng byte**. Đây đúng
hình dạng prefix cache của cả hai nhà cung cấp.

**Chưa đo, nên chưa được tính vào kế hoạch.** Đo được **miễn phí** ngay trong v5
bằng `usage.prompt_tokens_details.cached_tokens` — tôi sẽ ghi trường này. Nếu
nó chạy, chi phí thật thấp hơn bảng trên đáng kể; nếu không, bảng trên đúng.
**Không giả định trước.**

## Nhịp chạy

`816K` token dồn trong dưới một phút sẽ đụng trần bất kể cách đọc nào ở trên.
**Rải ≥ 5 phút** (≈ 20 lượt/phút/model), và hô khe như đợt trước.
