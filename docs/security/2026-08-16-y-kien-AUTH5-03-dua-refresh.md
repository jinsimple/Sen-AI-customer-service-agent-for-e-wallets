# Ý kiến bảo mật — AUTH5-03 và ca đua refresh hợp lệ

> Vai: **security** · 2026-08-16 · trả lời yêu cầu của PO-agent (control này là
> của tôi nên quyết định nới/giữ thuộc tôi).
> Đọc mã tại `src/auth.py:134-160`. Chưa có số tái lập của tester — ý kiến này
> dựa trên **cơ chế đọc được từ mã**, và tôi ghi rõ chỗ nào cần số để chốt.

## 0. Ba câu trả lời ngắn

| Câu hỏi | Trả lời |
|---|---|
| (1) Single-flight phía client có ĐỦ không? | **Cần, đúng hướng, NHƯNG KHÔNG ĐỦ** — nó không phủ đua **đa-tab** |
| (2) Grace-window có đáng làm KÈM không? | **DUYỆT — nhưng CHỈ ở dạng phát-lại-bất-biến**, không phải "tha rồi cấp cặp mới" |
| (3) Ghi hồ sơ về false-positive-mode? | **Có** — và tôi thêm một finding nặng hơn: §3 |

## 1. Giả thuyết của PO-agent đúng về cơ chế — và chính docstring tự nêu tiền đề hỏng

`rotate_refresh_token` đánh dấu `rotated=True`, giữ key **60s**; lần dùng thứ
hai trong cửa sổ đó → `revoke_family` → giết cả phiên. Docstring viết:

> *"client hợp pháp đã nhận token MỚI và không còn lý do gì dùng lại token cũ"*

**Đúng tiền đề bị ca đua phá.** Hai request đồng thời **đều đang cầm token CŨ**
— chưa đứa nào nhận được token mới. Không phải control sai; là **tiền đề của
control không phủ trạng thái đồng thời**.

## 2. Vì sao single-flight CẦN nhưng KHÔNG ĐỦ

Single-flight = **một promise dùng chung trong MỘT ngữ cảnh JS**. Nó đóng
đúng ca đua trong cùng một tab. **Nó không đóng:**

- 🔴 **Đa-tab.** Hai tab = hai ngữ cảnh JS = **hai promise độc lập**. Chúng
  không thấy nhau. Với sản phẩm này đó **không phải ca hiếm**: CSKH mở nhiều
  ticket ra nhiều tab là cách làm việc bình thường. Vá single-flight sẽ làm bug
  **biến mất trong demo một-tab** rồi **quay lại trên bàn làm việc thật** — và
  lần sau nó sẽ khó truy hơn vì "đã vá rồi mà".
- Tải lại trang giữa lúc đang refresh · app khôi phục từ nền · retry mạng khi
  response đã tới server nhưng client không thấy.

Muốn phủ đa-tab bằng client thì cần khoá chéo tab (`BroadcastChannel` /
`localStorage` lock) — **phức tạp và dễ hỏng**, và vẫn không phủ retry mạng.

⟹ **Làm single-flight** (đúng, rẻ, không tốn gì về bảo mật) **nhưng đừng coi
nó là xong.**

## 3. 🔴 Finding chặn trước cả hai phương án: AUTH5-03 **KHÔNG CÓ QUAN SÁT NÀO**

```
src/auth.py — 294 dòng, KHÔNG có `import logging`, KHÔNG một dòng log nào.
revoke_family() có ĐÚNG MỘT caller: chính nhánh reuse-detection (auth.py:150).
```

Nghĩa là: **sự kiện có ý nghĩa bảo mật lớn nhất của cả hệ thống xác thực —
"chúng tôi tin refresh token đã bị đánh cắp" — xảy ra HOÀN TOÀN IM LẶNG.**
Khách bị đăng xuất, không bản ghi nào.

Hệ quả trực tiếp lên chính câu hỏi đang hỏi:

- Không ai **đếm** được AUTH5-03 bắn bao nhiêu lần, cho user nào, lúc nào.
- Không phân biệt được **đua** với **trộm thật** trên production — hai thứ có
  hậu quả trái ngược hoàn toàn (một cái phải vá client, một cái phải báo động).
- **Chỉnh một control mà không quan sát được nó = chỉnh mù.** Nếu ta nới grace
  window rồi trộm thật bị bỏ sót, **sẽ không có gì cho ta biết**.

⟹ **Đề nghị làm TRƯỚC hoặc CÙNG lô**, rẻ hơn cả hai phương án kia: log có cấu
trúc tại `auth.py:150` (`family_id`, `user_id`, `role`, thời điểm, và — sau khi
có grace — **nhánh nào đã bắn: `reuse_that` hay `phat_lai_trong_grace`**).
Không có PII mới; `family_id` đã là định danh nội bộ.

Đây là mục tôi thấy **quan trọng hơn** cả câu (1) và (2).

## 4. Grace-window: DUYỆT, nhưng chỉ đúng MỘT dạng

Grace window cho reuse-detection là **pattern được công nhận**, không phải nới
cho tiện — chính vì ca đua hợp pháp này. Nhưng **cách cài đặt quyết định nó là
bản vá hay là lỗ hổng**:

| Dạng | Hành vi | Đánh giá |
|---|---|---|
| ❌ **Tha rồi cấp cặp MỚI** | mỗi request đua nhận một cặp khác nhau | **BÁC.** Tạo **hai phiên hợp lệ phân kỳ** từ một token — đúng thứ rotation sinh ra để chặn. Kẻ trộm cũng được cấp nhánh riêng, im lặng. |
| ✅ **Phát lại BẤT BIẾN** | trong N giây, cùng token cũ → trả **ĐÚNG cặp đã cấp** ở lần rotate đầu | **DUYỆT.** Khớp đúng bản chất ca lỗi: cùng client, cùng token, hai request đang bay → **phải nhận cùng một câu trả lời**. Không sinh nhánh mới, không tạo phiên phân kỳ. |

**Điều kiện tôi kèm cho việc duyệt:**

1. **Phát lại bất biến**, không tha-rồi-cấp-mới (bảng trên).
2. **N ngắn** — vài giây, đủ cho một chùm request đồng thời. **Không** dùng
   trọn 60s của cửa sổ `rotated`; 60s là cửa sổ **phát hiện**, không phải cửa
   sổ **tha thứ**.
3. **Bắn trong grace phải được LOG như một nhánh riêng** (§3). Nó không phải
   sự kiện bình thường — nó là *"đã có một cuộc đua"*. Tần suất tăng đột biến
   là **tín hiệu**, và nếu không log thì ta vừa xoá mất tín hiệu đó.
4. **Ngoài N giây, giữ nguyên hành vi nghiêm** — thu hồi cả family, không nới.

Vì sao tôi thấy cái giá bảo mật chấp nhận được: kẻ đã cầm refresh token trộm
được **không cần đua** — chúng dùng lúc nào cũng được. Giá trị thật của
reuse-detection là bắt được **va chạm cuối cùng** giữa kẻ trộm và client thật,
và phát-lại-bất-biến **không xoá** va chạm đó — nó chỉ tha đúng ca "hai request
của cùng một client, cùng một token, trong vài giây".

## 5. Điều tôi KHÔNG kết luận

- **Chưa có số tái lập của tester.** Ý kiến này đọc từ mã; nếu số cho thấy cơ
  chế khác (vd token hết hạn chứ không phải đua) thì §4 **không áp dụng** và
  phải xét lại từ đầu. Đừng land grace-window trước khi có số.
- **Không đề xuất N cụ thể** — cần biết phân bố độ trễ thật của chùm request ở
  thời điểm handoff. Nếu tester đo được khoảng cách giữa hai request đua, N nên
  lấy từ số đó chứ không lấy tròn.
- Tôi **không** rà phần còn lại của luồng refresh trong lượt này (chỉ đọc
  `rotate_refresh_token` + `revoke_family`).
