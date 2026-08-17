# Lộ `LLM_API_KEY` + FINDING: nhà cung cấp 403 → HTTP 500 trần

> Vai: **security** · 2026-08-17 · tester tự báo hai việc trong một tin. Chúng
> **không độc lập** — và chỗ chúng gặp nhau là phần quan trọng nhất tài liệu này.

## §1. Phán quyết lộ khoá: **XOAY — nhưng KHÔNG xoay trước bản vá ở §2**

### Hiệu chuẩn mức: **THẤP hơn sự cố sáng nay**, và nói rõ vì sao

| | Sáng nay (`sk-proj…` → Alibaba) | Bây giờ (`sk-ws…` → bản ghi phiên) |
|---|---|---|
| khoá đi đâu | **rời hạ tầng ta**, sang bên thứ ba, tài phán khác | **ở lại máy này**, một tệp trên đĩa |
| ta kiểm toán được không | **không** (log của họ) | **có** (tệp của ta) |
| giá trị lạm dụng hôm nay | tiêu hạn mức OpenAI | **≈ 0** — hạn mức miễn phí DashScope **đã cạn** (chính 403 tester đo) |

⟹ **Vẫn xoay**, vì ba lý do độc lập với mức: bản ghi phiên **tồn tại lâu**, có
thể được tóm tắt/chia sẻ về sau; tài khoản **có thể nâng lên trả phí**, lúc đó
khoá cũ thành khoá tiêu tiền; và ta **không sửa lại được** một bản ghi chỉ-ghi-
thêm. **Không phải việc gấp trong đêm** — nhưng phải làm, và làm đúng thứ tự §3.

### Chẩn đoán của tester đúng, tôi chỉ nâng nó thành dạng tổng quát

Họ dùng `sed "s/=.*key.*/=***/I"` — khớp trên **GIÁ TRỊ**, mà giá trị không chứa
chuỗi `key`. Cạnh đó, `cut -c1-12` cho `OPENAI_API_KEY` thì **đúng**.

> **Che theo VẬT, không che theo MẪU mình tưởng.** Hai cách đúng, cả hai đều
> **không đoán hình dạng giá trị**:
> ① **theo TÊN** — liệt kê biến cần che (`*_API_KEY`, `*_SECRET*`, `*_TOKEN*`,
>    `*PASSWORD*`) rồi che vế phải;
> ② **theo VỊ TRÍ** — `cut`/thay theo cấu trúc dòng, mặc định che **mọi** giá
>    trị rồi mới mở ra thứ cần đọc.
>
> **Danh sách CHO PHÉP, không phải danh sách CẤM.** Một regex đoán hình dạng bí
> mật là một danh sách cấm, và danh sách cấm hỏng ở đúng thứ nó chưa từng thấy.

*(Tôi tự kiểm phiên của mình theo đúng luật này: các lệnh chạm `.env` của tôi in
**tên biến** (`grep -oE "^[A-Z_0-9]+"`) hoặc giá trị **không nhạy cảm**
(`APP_ENV`, `LLM_MODEL`, `LANGCHAIN_TRACING_V2=false`); URL Postgres che **theo
vị trí** (`sed 's/:[^:@]*@/:***@/'`). **Không khoá nào bị in.** Nó sạch vì che
theo cấu trúc — **không** phải vì tôi cẩn thận hơn.)*

### Ai xoay: **PO thật.** Tester đúng khi không tự làm

Cần đăng nhập tài khoản DashScope của người thật ⟹ đúng mục *"luôn cần xác nhận
người dùng, không tự động hoá"* của playbook. Giao lại kèm hướng dẫn, không cố
tự động hoá.

## §2. 🔴 FINDING — bắt **MỘT** lớp lỗi, nhưng chế độ hỏng có **NHIỀU** lớp

`graph.py:363` bắt **đúng một** ngoại lệ: `RateLimitError` (429).

```
đo được trên đường thật (tester, 5 lượt):
   hết giờ trong agent      → HTTP 200 + vé fallback        (có đường thoát)
   nhà cung cấp trả 403     → HTTP 500 trần                 🔴 KHÔNG đường thoát
```

Nhưng 429 chỉ là **một** cách nhà cung cấp từ chối phục vụ. Các cách còn lại
**đều rơi thẳng ra 500**:

| Tình huống | Ngoại lệ | Hôm nay |
|---|---|---|
| quá tần suất | `RateLimitError` 429 | ✅ có nhánh riêng |
| **hết hạn mức / hết tiền** | `PermissionDeniedError` **403** | 🔴 **500** — tester vừa đo |
| **khoá sai / vừa xoay** | `AuthenticationError` 401 | 🔴 500 |
| model chưa mở quyền | `PermissionDenied`/`BadRequest` | 🔴 500 *(đã gặp 16/08: `AccessDenied.Unpurchased` 6/6 model)* |
| nhà cung cấp lỗi/rớt mạng | `InternalServerError`/`APIConnectionError` | 🔴 500 |

> **Cái `except` đang khoá vào TÊN NGOẠI LỆ, trong khi thứ cần xử lý là TRẠNG
> THÁI "nhà cung cấp không phục vụ lượt này".** Cùng lớp lỗi với
> `_khoa_cho_nha_cung_cap` sáng nay (*hỏi "CHÚNG TA có đổi đích không" thay vì
> "đích có đổi không"*) và với bộ kiểm `authority-matrix` (*"cái ta khai có đúng
> không" thay vì "cái đang chạy có được khai không"*). **Lần thứ ba trong ngày.**

### Hai điểm giảm nhẹ — đo được, ghi để không thổi phồng

- **Không rò thông tin ra khách.** FastAPI trả `{"detail":"Internal Server
  Error"}`; câu *"The free quota has been exhausted"* **không** tới khách. Đây
  là điểm **đúng** của hệ thống, ghi nhận.
- **Không tạo vé ma.** Nhánh 500 **không** ghi gì — nên nó **không** chạm ràng
  buộc 3 như finding `scope` bịa. Vấn đề ở đây là **khả dụng**, không phải
  **toàn vẹn bản ghi**.

### Vì sao nó không thể để lại sau — ba lý do đang cùng lúc đúng

1. **Bản vá xoay khoá ở §1 SẼ tự kích hoạt nhánh chưa xử lý.** Cửa sổ xoay khoá
   = một chuỗi `AuthenticationError` 401 ⟹ **mọi lượt chat trong cửa sổ đó
   thành 500 trước mặt khách.** Xoay trước khi vá là tự tạo sự cố.
2. **403 đã xảy ra thật hôm nay**, không phải giả định.
3. **Buổi test 150 người:** trần TPM/hạn mức là **ràng buộc lớn nhất đã biết**
   của buổi đó ⟹ chế độ hỏng **dễ xảy ra nhất** ở đó chính là chế độ **chưa có
   đường thoát**.

### Đề nghị vá — và một cảnh báo về chỗ KHÔNG được vá

- Bắt **cả họ** ngoại lệ "nhà cung cấp không phục vụ" ở `graph.py`, trả **câu
  xin lỗi + mời thử lại**, **HTTP 200**, **KHÔNG tạo vé**.
- 🔴 **KHÔNG dùng nhánh fallback-tạo-vé cho lớp này.** Chính chú thích ở
  `graph.py` đã cảnh báo đúng điều đó cho 429: *"mỗi phút cao điểm đổ một nắm
  ticket ma lên CSKH cho những khiếu nại KHÔNG TỒN TẠI"*. Hết hạn mức là **hỏng
  toàn cục** — nó đánh **mọi** khách cùng lúc, nên nối nó vào đường tạo vé sẽ
  sinh **một vé cho mỗi khách đang online**. Đây là chỗ dễ vá sai nhất.
- Phân biệt trong log: **thoáng qua** (429, 5xx nhà cung cấp) ↔ **cần người
  can thiệp** (401, 403 hết hạn mức). Cái sau phải **báo động cho vận hành**,
  không chỉ ghi log — khách thử lại bao nhiêu lần cũng không tự hết.

## §3. Thứ tự bắt buộc — vì §1 và §2 **không độc lập**

```
1. Vá §2 (bắt cả họ ngoại lệ nhà cung cấp)      ← TRƯỚC
2. Rồi mới xoay LLM_API_KEY (và OPENAI_API_KEY của sáng nay)
3. Sau khi xoay: gọi thử một lượt, xác nhận 200
```

Đảo thứ tự = tự tạo một cửa sổ 500 trước mặt khách, **bằng chính hành động sửa
lỗi bảo mật**.

## §4. Ba ngăn xếp dùng CHUNG một `OPENAI_API_KEY` — lý do thứ hai cho việc tách khoá

Tester nêu: chuyển sang OpenAI để chạy tiếp **không** cho một nguồn độc lập.
Đúng, và hệ quả nặng hơn thế: **cạn hạn mức trên một ngăn xếp làm chết cả ba** —
kể cả ngăn xếp dùng cho demo. **Khoá chung = hỏng chung.**

Sáng nay tôi đề nghị tách khoá theo môi trường vì lý do **bán kính vụ nổ khi
LỘ**. Giờ có lý do thứ hai, độc lập: **bán kính vụ nổ khi CẠN**. Hai lý do khác
nhau, cùng một bản vá.

## §5. Ghi nhận cách tester đọc số của chính mình

`0 ĐẠT · 0 TRƯỢT · 5 không_đo_được` và họ **không** đọc "5 không đo được" thành
bất kỳ kết luận nào về quan sát ⑤ — **trạng thái thứ ba, không phải kết quả.**

Đây là chỗ cả ngày hôm nay ta trượt đi trượt lại theo hướng ngược (đọc một số
thành nhiều hơn nó nói). Lần này số **không** nói gì, và nó được ghi đúng là
không nói gì.
