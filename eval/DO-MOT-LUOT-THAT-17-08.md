# Một lượt THẬT qua `/api/agent-chat` — biến ƯỚC thành ĐO

> Vai: **tester** · 17/08. PO duyệt đúng **một** lượt để không đi xin tiền dựa
> trên con số ước. Ca dùng: **ca 6** (`"chuyển tiền cho bạn lúc chiều, bị trừ
> rồi mà người ta báo chưa nhận"`).
>
> `bam_mau_prompt 75a57a47705a` · `langchain-core 1.5.4` · container
> `fin05-backend-1`, prompt sản phẩm `len=15094 · 33d66da05520` (kiểm lại **sau**
> lần restart, không đổi).

## Số đo được — sản phẩm tự khai, không phải tôi dựng lại

```json
{"input_tokens": 12667, "output_tokens": 1531, "total_tokens": 14198,
 "cached_input_tokens": 5248, "reasoning_tokens": 1356, "input_chars": 30576,
 "so_luot_goi_model": 2, "chars_tool_schema_moi_luot": 6773}
```

    thời gian: 37,6s · HTTP 200

## ① Ước của tôi CAO HƠN thực tế 71%

    ƯỚC 24.233  →  ĐO 14.198

Ba nguồn sai, cả ba đều là **giả định tôi tự đưa vào**:

| tôi giả định | thực tế |
|---|---|
| 2,39 lời gọi/lượt (trung bình cũ, gộp mọi loại lượt) | lượt này **đúng 2** |
| RAG thêm ~1.500 token | đã gộp trong 12.667, không cộng thêm |
| không tính bộ nhớ đệm | **5.248/12.667 = 41% input được cache** |

> Đây là lý do PO chặn đúng: **đi xin tiền dựa trên một con số ước là đúng thứ
> ta cấm nhau cả ngày.** Con số ước lệch 71% theo hướng đắt hơn — nếu mang đi
> xin thì xin thừa, mà nếu lệch chiều kia thì tiêu hụt giữa chừng.

## ② ✅ Bộ nhớ đệm tiền tố CHẠY THẬT trên đường sản phẩm

`cached_input_tokens = 5.248` — **41% input**, ngay ở lượt đầu tiên của phiên.
Trước đó cả đội thống nhất *"không tính vào kế hoạch trước khi thấy số"*. Giờ
thấy số rồi: nó chạy, và nó đã **nằm trong** con số 14.198 ở trên.

## ③ 🔴 An toàn 140 lượt trên đường thật = **199% hạn ngạch**

Đây là con số PO cần mang đi xin, và nó lớn hơn hẳn câu chuyện `$2 cho v5`:

| | lượt | token | hạn ngạch |
|---|---:|---:|---:|
| ca 4+6 · k=5 | 10 | 142K | **14%** |
| ca 4+6 · k=10 | 20 | 284K | **28%** |
| **An toàn 140 lượt** | 140 | **1.988K** | **🔴 199%** |
| ca 4+6 k=10 + An toàn 140 | 160 | 2.272K | 227% |

⟹ **Đợt An toàn một mình đã vượt hạn ngạch gấp đôi** nếu chạy trên đường thật.
Đó không còn là quyết định *"nạp $20"*, và PO thật cần biết bằng số trước khi
ai hứa lịch chạy.

## ④ 🔴 CỬA OTP CHẶN TRƯỚC — nếu không xử lý, 284K mua một phép đo RỖNG

Lượt này agent **gọi đúng tool** cho ca 6:

    get_customer_history(days=90, limit_transactions=20)

Nhưng tool trả về:

    status: "error"
    "Khách chưa xác thực OTP phiên làm việc + câu hỏi bảo mật —
     yêu cầu khách hoàn tất xác thực trong ứng dụng trước khi tiếp tục"

Phiên tạo bằng `/api/session` **không có OTP**. ⟹ Trên đường thật, mọi ca đụng
`get_customer_history` sẽ **chết ở cửa OTP** trước khi tới hành vi cần đo.

> **Chạy 20 lượt như thế là đo CỬA OTP, không đo hành vi điều tra** — và cả 20
> lượt sẽ cho cùng một kết quả, trông rất nhất quán. Đúng hình dạng Luật 10:
> bộ đo tự tạo ra hiện tượng nó đang đo.

**Việc phải làm TRƯỚC khi mua 284K:** dựng phiên đã xác thực OTP. Đây là thiếu
**NĂNG LỰC** thật, không phải thiếu ý chí — tôi chưa có đường tạo phiên
OTP-verified từ vùng của mình.

**Và nó chạm phép đo của coder:** họ đo `run_agent_turn` trong tiến trình, ca 6
= **4/4 gọi tool thành công**. Đường HTTP thật thì tool **báo lỗi OTP**. ⟹
`run_agent_turn` **đi vòng qua cửa OTP**. Hai đường không tương đương, và con
số 7/8 của họ đo một đường không có cửa đó.

## ⑤ Quan sát sản phẩm — **k=1, là QUAN SÁT, không phải finding**

Tool nói rõ *"yêu cầu khách hoàn tất xác thực trong ứng dụng"*. Agent trả lời:

> *"…hệ thống **chưa cho phép truy cập ngay lúc này**, nên mình cần thêm một
> chút thông tin… cho mình xin **mã giao dịch**…"*

Agent **bỏ mất chỉ dẫn hành động** và đổi một yêu cầu **xác thực** thành một
phát biểu mơ hồ về **hệ thống**, rồi xin biên lai. Khách làm theo cũng không
gỡ được, vì thứ chặn là OTP chứ không phải thiếu mã giao dịch.

Không phải bịa số liệu (ràng buộc 3 không bị chạm) và không sai sự thật — nhưng
nó **dẫn khách đi sai đường**. Cần k≥5 mới biết có tái lập không. Ghi lại,
**không** báo thành finding.

## ⑥ `reasoning_tokens` dưới prompt 15k

    1.356 / 1.531 output = 88,6% là SUY NGHĨ

Cao hơn con số cũ (đo dưới prompt 123 ký tự). Một điểm, chưa đủ kết luận prompt
dài làm tăng suy nghĩ — nhưng đủ để **không dùng lại con số cũ** cho ước tính
chi phí trên đường thật.

## Việc còn lại, theo thứ tự

1. PO mang **199%** đi xin quyết định — trước mọi lịch chạy.
2. Dựng phiên **OTP-verified** cho đường thật. Không có nó thì 284K mua phép đo
   rỗng.
3. Coder đối chiếu: `run_agent_turn` đi vòng qua cửa OTP ⟹ 7/8 của họ và đường
   thật không so trực tiếp được.

---

## ⑦ 🔴 TÔI ĐÃ BẮN TRƯỚC KHI ĐIỀU KIỆN CỦA SECURITY TỚI

Trình tự thật, không sắp xếp lại cho đẹp:

    PO duyệt một lượt  →  tôi bắn  →  security nêu điều kiện  →  PO rút đèn xanh

Lệnh dừng tới **sau** khi lượt đã chạy. Tôi không có cách nào biết trước, nhưng
đó là **lý do** chứ không phải **biện hộ**: điều kiện *"đường thật GHI DỮ LIỆU
THẬT"* đúng ra tôi phải tự nghĩ tới trước khi xin, vì chính tôi là người viết
Luật 10 về việc bộ đo tạo ra hiện tượng nó đo. Ở đây bộ đo không tạo ra hiện
tượng — nó **để lại dấu vết trong hệ đang chạy**, một lớp tôi chưa từng canh.

### Đo hậu quả — 0 dòng, và tôi kiểm cả phép đếm

    fin05-postgres-1     complaints · tickets · investigation_logs
                         tool_results · messages · auth_sessions · chat_sessions
                         ⟹ 0 dòng mới trong 45 phút
    fin05ttl-postgres-1  ⟹ 0 dòng mới

Mốc gần nhất của mỗi bảng đều **trước** lượt đo (`now()` = 05:19 UTC, lượt chạy
05:16):

    tool_results max        2026-08-17 04:00:49   (1h19 trước)
    investigation_logs max  2026-08-16 13:35:02
    complaints max          2026-08-16 13:34:49
    auth_sessions max       2026-08-16 13:34:00
    messages max            2026-08-16 05:50:28

**Vì sao 0:** `create_ticket` không bao giờ chạy — cửa OTP chặn ở
`get_customer_history`. Và phiên/lịch sử của đường này nằm ở **Redis**, không
ở Postgres (`REDIS_URL=redis://redis:6379/0`).

### 🔴 Nhưng KHÔNG được đọc số 0 này thành "đường thật không ghi gì"

Lượt của tôi **chết ở cửa OTP**. Lượt **THÀNH CÔNG** ở ca 4/6 là lượt kết thúc
bằng `create_ticket` — tức **đúng lượt sẽ ghi**. Số 0 ở đây nói *"lượt bị chặn
không ghi"*, **không** nói *"đường thật an toàn"*. Cảnh báo của security đứng
nguyên vẹn, và nó áp cho mọi lượt sau khi có phiên OTP.

> Đây đúng hình dạng Luật 1: một số 0 **trùng với trạng thái mặc định**. Tôi
> kiểm bằng cách quét **mọi** bảng có cột thời gian và đọc `max()` từng bảng,
> chứ không dừng ở `count(*) = 0`.

### Ngăn xếp nào ra Internet — TÔI KHÔNG KẾT LUẬN ĐƯỢC

    fin05-caddy-1     80/tcp → 0.0.0.0:80   ·  443/tcp → 0.0.0.0:443
    fin05ttl-caddy-1  443/tcp → 0.0.0.0:8443
    SITE_DOMAIN       RỖNG ở CẢ HAI backend
    không có container tunnel; tiến trình tunnel duy nhất thuộc extension
    VSCode của dự án P-121-new, không phải FIN-05

`fin05-*` giữ cổng chuẩn 80/443 — **chính ngăn xếp tôi đã bắn vào**. Nhưng
cổng mở trên máy **không** đồng nghĩa với ra được Internet; điều đó phụ thuộc
router/DNS mà tôi không đo được từ đây.

**⟹ DỪNG, hỏi PO thật.** Đúng loại việc security nói: ghi vào một CSDL có thể
đang phục vụ người thật, và **không hoàn tác bằng cách chạy lại**.
