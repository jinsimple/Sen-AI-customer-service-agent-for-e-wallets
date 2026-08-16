# AUTH5-03 — hai chế độ dương-tính-giả, và cách phân biệt trên log

> Vai: **security** · 2026-08-16 · phụ lục cho control AUTH5-03
> (`src/auth.py:146-155`, reuse-detection + `revoke_family`).
> Viết để phiên sau **không sửa nhầm control** khi thấy nó bắn.

## 0. Câu quan trọng nhất, đặt lên đầu

**AUTH5-03 chưa từng sai. Cả hai ca dưới đây là control PHÁT HIỆN ĐÚNG một
lượt reuse có thật** — chỉ là kẻ reuse hoá ra là **chính hệ thống**, không phải
kẻ trộm. Thiết kế phân biệt được *"token này bị dùng lại"*; nó **không** phân
biệt được *"ai dùng lại và vì sao"*.

⟹ Thấy AUTH5-03 bắn thì **đừng nới control**. Đi tìm ai đang reuse.

## 1. Hai chế độ dương-tính-giả

| | **A — đua client** (xác suất) | **B — middleware tự gọi hai lần** (tất định) |
|---|---|---|
| Cơ chế | ≥2 request đồng thời, **cả hai đang cầm token CŨ** vì chưa đứa nào nhận token mới | middleware refresh xong, **lượt gọi thứ hai trong CÙNG vòng request** vẫn cầm token cũ (cookie mới mới chỉ nằm trên *response*) |
| Tần suất | lẻ tẻ, phụ thuộc thời điểm | **tất định** — đo được 10/10 |
| Nguồn | client thiếu single-flight · **đa-tab** · reload giữa refresh · retry mạng | lỗi vòng đời request phía client/middleware |
| Chữ ký log | `rotated` ↔ `revoked` **ghép 1-1**, cách nhau mili-giây | như A, nhưng **đều đặn và lặp lại mọi lần** |
| Vá đúng | single-flight (che A cùng-tab) · khoá chéo tab (A đa-tab) | sửa vòng đời request để lượt sau thấy token mới |
| Vá SAI | **nới AUTH5-03** | **nới AUTH5-03** |

**Ca B là ca đã gây bug demo 15/08** — xác nhận bằng log tầng-0, `refresh_rotated`
×10 ↔ `refresh_family_revoked` ×10 ghép hoàn hảo.

## 2. Vì sao ca B đắt hơn ca A dù cùng chữ ký

Ca A **hiếm và ngẫu nhiên** ⟹ nó biểu hiện như "thỉnh thoảng khách bị văng",
dễ bị bỏ qua như nhiễu. Ca B **tất định** ⟹ nó giết phiên **mọi lần** đi qua
đường đó — nhưng vì cùng chữ ký với "phát hiện trộm", người điều tra rất dễ
kết luận *"control quá nhạy"* và đi nới nó. **Nới ca B = tắt reuse-detection để
che một lỗi vòng đời request.** Đó là đổi một control thật lấy một bản vá giả.

## 3. Phân biệt TRỘM THẬT với hai ca trên — đọc trên log

```
rotated ↔ revoked ghép 1-1, đều đặn, cùng phiên      -> TỰ BẮN (A hoặc B)
revoked LẺ TẺ, không cặp rotated tương ứng gần đó    -> ĐÁNG NGHI trộm thật
revoked tăng đột biến sau một đợt deploy client      -> nghi B (hồi quy vòng đời)
```

⚠️ **Ba dòng trên chỉ đọc được vì tầng-0 log ĐÃ TỒN TẠI.** Trước 16/08,
`src/auth.py` **294 dòng không có một dòng log nào** — `revoke_family()` bắn
hoàn toàn im lặng, và bug demo trở thành bí ẩn vì `200 rồi 401` chỉ là hai dòng
access log vô nghĩa.

> **Case study cho luật "chỉnh một control không quan sát được là chỉnh mù":**
> tại đây, thứ **giải** được bài toán không phải một bản vá — mà là **làm cho
> control nhìn thấy được**. Và nếu ta đã nới grace-window trước khi có log, ta
> sẽ (i) che mất bug B, (ii) làm yếu reuse-detection thật, (iii) **không có gì
> để biết mình vừa làm cả hai**.

## 4. Grace-window: ĐÃ RÚT — và vì sao rút là đúng

Tôi từng **duyệt có điều kiện** một grace-window dạng *phát-lại-bất-biến*
(`2cff494` §4), kèm điều kiện minh thị: *"đừng land trước khi có số; nếu số cho
thấy cơ chế khác thì phần này không áp dụng"*.

**Số đã cho thấy cơ chế khác** (B tất định, không phải A xác suất) ⟹ điều kiện
của chính tôi kích hoạt ⟹ **rút, và tôi xác nhận việc rút.**

Lý do bản chất: grace-window là công cụ cho **đua xác suất**. Ca B **không phải
đua** — nó là một lỗi tất định của vòng đời request. Dùng grace để che nó là
**nới một control bảo mật để che một bug client** — và tệ hơn, nó sẽ **thành
công**: bug biến mất, không ai còn động lực sửa vòng đời, và control thì đã yếu
đi vĩnh viễn.

**AUTH5-03 giữ nguyên, không suy suyển.**

## 5. Còn mở: ca A đa-tab — chưa đo, nay ĐO ĐƯỢC

Ca A **chưa được chứng minh là có xảy ra** trong sản phẩm này. Tôi nêu nó từ
lập luận cơ chế (single-flight là **một promise trong MỘT ngữ cảnh JS** ⟹ hai
tab = hai promise độc lập), **không** từ số đo. Bản vá cho ca B **không** phủ
ca A đa-tab.

**Không đề nghị vá phòng ngừa.** Đề nghị: **để log trả lời**. Sau khi ca B được
vá, nếu `revoked` **vẫn còn bắn theo chữ ký tự-bắn** thì ca A là thật và đo
được; nếu tắt hẳn thì ca A hoặc không xảy ra, hoặc quá hiếm để đáng vá.

Đây là dạng đúng của một mối lo chưa có bằng chứng: **biến nó thành thứ đo
được, rồi im lặng chờ số** — thay vì vá theo linh cảm hoặc quên nó đi.

## 6. ⚠️ Nếu ai định thêm chiều "ai gọi" vào log — đọc trước

Muốn log phân biệt **A (cùng máy, cùng người)** với **trộm thật (máy khác)**
thì cần một chiều định danh client: IP · User-Agent · device id.

**Ba thứ đó đều là dữ liệu cá nhân** (NĐ 13/2023; IP được coi là dữ liệu cá
nhân ở cả GDPR). Log bảo mật **không được miễn trừ** khỏi nguyên tắc tối thiểu
hoá. Nếu thêm:

- **băm** (HMAC với khoá riêng) thay vì lưu thô — vẫn so sánh được "cùng hay
  khác máy", không tái dựng được danh tính;
- **retention riêng, NGẮN**, tách khỏi retention 5 năm của hồ sơ khiếu nại
  (ADR-025 QĐ 3) — đây là log vận hành, không phải hồ sơ nghiệp vụ;
- đi qua **cùng lớp scrub** với mọi log khác (S-03).

Chưa cần làm ngay — chỉ ghi để lần sau ai thấy log "thiếu ngữ cảnh" thì không
lặng lẽ thêm IP thô vào.
