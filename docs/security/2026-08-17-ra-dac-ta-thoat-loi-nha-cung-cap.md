# Rà đặc tả "đường thoát lỗi nhà cung cấp" — trước khi PO duyệt

> Vai: **security** · 2026-08-17 · tech-lead gửi đặc tả (nháp **ngoài repo**),
> **chưa code gì**, hỏi bốn điểm. Rà theo bộ tiêu chí `2359536`.

## §0. Tiêu chí thứ 8 KHÔNG áp cho đặc tả này — nói trước để khỏi hiểu nhầm

Tôi vừa thêm tiêu chí #8 (*thay đổi tầng **prompt** phải chạy một lượt thử rẻ
TRƯỚC khi duyệt đặc tả*). **Đặc tả này là tầng MÃ**, và ở tầng mã thì *"đọc một
diff thì biết được điều gì sẽ xảy ra"* — nên **đặc-tả-rồi-code là thứ tự đúng**.
Không đòi pilot.

Và §5 của họ đã có phần verify **đúng vật** (tiêm thẳng exception, không mô
phỏng gần đúng) **kèm ca đối chứng** — tự nó thoả tiêu chí #2 mà tôi không phải
nhắc.

## §1. Câu ① — *"có ca nào khách ĐÁNG nhận 500 không?"*

### Trả lời: **Không có, kết luận của bạn đúng. NHƯNG nó không land một mình được.**

Tôi thử bác theo ba hướng, hai hướng gãy:

- *"Client cần phân biệt để tự thử lại"* — gãy: client duy nhất là BFF của
  chính ta, và §2 đã bảo khách thử lại.
- *"500 giúp phát hiện tấn công"* — gãy: 401/403 lặp là tín hiệu **vận hành**,
  không phải thứ khách cần thấy.
- 🔴 **"500 hôm nay LÀ cái chuông duy nhất"** — **không gãy.**

### 🔴 Bác thật: hôm nay **KHÔNG TỒN TẠI** kênh báo động nào — [ĐO]

```
prometheus · /metrics · webhook · kênh cảnh báo   : KHÔNG CÓ
logger.error/critical trong toàn bộ src/          : 2 chỗ
/ready (readiness)                                : KHÔNG TỒN TẠI (chỉ có /health)
```

⟹ Cột **"BÁO ĐỘNG"** trong bảng §1 của bạn **chưa có gì để trỏ vào**. Nếu land
trục khách mà trục vận hành chỉ là một dòng log, ta **đổi một hỏng-ỒN lấy một
hỏng-CÂM**: khách nhận câu xin lỗi lịch sự, hệ thống đứng hình, và **không tín
hiệu nào rời khỏi tiến trình**.

**Bằng chứng mạnh nhất cho điều này nằm ngay trong lịch sử của chính finding
đang bàn:** tester phát hiện hạn mức cạn **vì lượt đo trả về 500**. Nếu bản vá
này đã có mặt sáng nay, harness của họ sẽ ghi *"agent đã trả lời"* — **và không
ai biết hạn mức đã cạn.** Bản vá, land một mình, **sẽ làm chính finding sinh ra
nó trở nên vô hình.**

### ⟹ Điều kiện DUYỆT: trục vận hành phải land CÙNG lượt, và đặc tả phải nói nó là gì

Không đòi dựng hệ thống cảnh báo. Đòi **một bề mặt máy đọc được**, rẻ:

1. **Bộ đếm + sự kiện log có TÊN RIÊNG** ở mức `error` cho nhóm *cần can thiệp*
   (401 · 403 · 400 · 404) — khác tên với nhóm *thoáng qua*. Tối thiểu là
   `grep` được, và có tên riêng thì sau này gắn cảnh báo không phải sửa code.
2. **Phơi trạng thái ra chỗ máy đọc được**: `so_loi_nha_cung_cap_5_phut` +
   `thoi_diem_loi_cuoi` + `lop_loi_cuoi`, trên một endpoint nội bộ hoặc thêm
   trường vào `/health`.
   ⚠️ **KHÔNG nối nó vào liveness/readiness gating.** Nhà cung cấp hỏng đánh
   **mọi** replica cùng lúc; để nó rút container khỏi vòng phục vụ là biến một
   dịch vụ **suy giảm** thành một dịch vụ **chết**.
3. Ghi rõ trong đặc tả: **hôm nay chưa ai nhận chuông.** Một cột "BÁO ĐỘNG"
   không có người trực là một cột **mô tả ý định**, không phải một cơ chế —
   phải khai đúng như thế để PO biết mình đang duyệt gì.

*(Đây cũng là chỗ nợ `/ready` — playbook đòi tách liveness/readiness, mã chưa
có. Không bắt buộc đóng trong lượt này, nhưng nó là chỗ tự nhiên của trạng thái
"phụ thuộc ngoài đang hỏng".)*

## §2. Câu ② — câu trả lời cho khách: đúng ba điều nó **không** nói, nhưng **một** điều nó nói lại quá tay

Ba cái bẫy bạn né đều đúng, và cái thứ hai (*không hứa "đã ghi nhận" khi §3
không tạo vé*) là **thứ giữ cho §3 đứng vững về pháp lý** — xem §3 dưới.

🔴 **Nhưng:** *"Bạn thử lại sau ít phút giúp mình nhé"* **sai với đúng ca đã xảy
ra hôm nay.** Hết hạn mức · khoá sai · model chưa mở quyền: **thử lại sau ít
phút KHÔNG giúp gì**, có khi hàng giờ. Đó **cùng hình dạng** với cái bẫy bạn
đang né — *hứa một điều ta không làm được* — chỉ nhẹ hơn.

**Sửa, mà KHÔNG phá nguyên tắc "đừng so chuỗi ở trục khách":** tách **hai** câu,
và khoá vào **LỚP LỖI**, không vào thân thông báo.

```
thoáng qua   429 · 5xx · timeout · lỗi mạng
             → "…thử lại sau ít phút giúp mình nhé."          (giữ nguyên)

cần can thiệp 401 · 403 · 400 · 404
             → KHÔNG hứa mốc thời gian. Nêu đúng sự thật là đang trục trặc
               kỹ thuật, VÀ chỉ đường sang kênh khác (tổng đài).
```

Phân nhánh theo **lớp ngoại lệ** thì vẫn tránh được đúng thứ bạn muốn tránh —
không có so chuỗi nào ở trục khách, nhà cung cấp đổi câu chữ **không** đổi được
thứ khách thấy.

**Và câu "chỉ đường sang kênh khác" không phải phép lịch sự** — xem §3.

## §3. Câu ③ — PDPA / nghĩa vụ ghi nhận. **Chỗ bạn ít chắc nhất, và bạn ĐÚNG.** Kèm MỘT điều kiện

### Không phát sinh nghĩa vụ ghi nhận — vì §2 không hứa gì

Nghĩa vụ tiếp nhận/xử lý khiếu nại (NĐ 52/2024 · TT 40/2024) gắn với một khiếu
nại **đã được nộp**. Một hội thoại đứt **trước khi** có vé nào không phải một
khiếu nại đã nộp ⟹ **không ghi lại không phải một thiếu sót pháp lý.**

**NĐ 13/2023 (PDPA): không chạm** — không có nghĩa vụ lưu dữ liệu ta chưa từng
thu thập. Quy tắc của bạn **giảm** lượng dữ liệu cá nhân được tạo ra, tức đi
đúng chiều tối thiểu hoá.

🔴 **Nhưng cả hai kết luận trên đứng được CHỈ VÌ §2 không nói "đã ghi nhận".**
Rủi ro thật không phải bản ghi thiếu — nó là **niềm tin của khách rằng họ đã
khiếu nại**. Một khách tin mình đã nộp thì **không nộp lại**, và khi tranh chấp
xảy ra, khoảng lặng đó nằm về phía ta.

⟹ Ràng buộc (d) của bạn — *"§2 và §3 khoá nhau, đổi một phải đổi cả hai"* —
**không chỉ là nhất quán nội bộ. Nó chính là thứ giữ cho đánh đổi này hợp
pháp.** Đề nghị ghi thẳng lý do đó vào (d), để người sửa sau không tưởng đó là
một quy ước văn phong.

### ⚠️ Điều kiện tôi thêm: **cái giá của "cố ý mất dấu" KHÔNG đồng đều**

Bạn khai đánh đổi rất sòng phẳng. Nhưng nó không phẳng đều:

- mất một khách hỏi *"phí rút bao nhiêu"* → **giá ≈ 0**
- mất một khách đang định **báo gian lận / mất tiền** → **giá cao**, và **nhạy
  thời gian**: chậm giờ nào là khả năng chặn/truy vết giảm giờ đó

Và ta **không phân biệt được hai ca này**, vì agent đã hỏng **trước** khi phân
loại được — đúng cái làm nó khó.

⟹ **Biện pháp duy nhất còn lại khi không phân loại được là chỉ đường sang kênh
khác.** Vì thế câu "cần can thiệp" ở §2 **phải** có một lối đi cho người thật
(tổng đài/kênh chính thức). **Đây là điều kiện, không phải gợi ý** — nó là thứ
biến *"ta mất dấu khách"* thành *"khách vẫn còn đường"*, và nó là phần khiến
tôi ký được vào đánh đổi ở §3.

*(Với riêng nghi ngờ gian lận, nếu sau này PO muốn chặt hơn: nới (c) cho **duy
nhất** trường hợp khách đã nói tới gian lận/mất tiền trong hội thoại. Nhưng nó
đòi phân loại **trên văn bản khách gõ ở tầng code** — một cửa mới, cần rà
riêng. **Không đề nghị làm trong lượt này.**)*

## §4. Câu ④ — trường ghi lại: **đủ, không thừa.** Thêm hai trường, giữ nguyên một điều cấm

**Xác nhận điều cấm quan trọng nhất: KHÔNG ghi thân thông báo thô. Đúng, và dự
án này đã trả giá cho đúng lỗi đó** — S-03: một chuỗi lỗi DB thô mang
`Key (phone)=(0912345678)` đi vào span. Thân lỗi của nhà cung cấp là **văn bản
do bên thứ ba soạn**, ta không kiểm soát nội dung, và một số nhà cung cấp lặp
lại **tiền tố khoá** trong thông báo xác thực. **Giữ nguyên lệnh cấm.**

**Năm trường bạn đề xuất (lớp lỗi · mã · nhà cung cấp · model · thời điểm):
đủ.** Thêm hai, cả hai **không chứa bí mật, không chứa PII**:

| Thêm | Vì sao |
|---|---|
| **`request_id` của nhà cung cấp** (header trả về) | đây **chính** là thứ bộ phận hỗ trợ của họ hỏi khi ta khiếu nại hoá đơn/hạn mức. Không có nó thì hồi cứu với nhà cung cấp là bất khả |
| **`thread_id`/`correlation_id` lượt của ta** | nối sự cố với **số phiên bị ảnh hưởng** mà **không** phải lưu nội dung nào |

⚠️ **Một cảnh báo về `request_id`:** nó là định danh **của họ**, và khi ta đưa
nó cho họ để tra là ta **xác nhận một lượt gọi cụ thể** — chỉ dùng trong hồ sơ
sự cố nội bộ, **không** đưa ra khách (đúng như §2 đã cấm mã lỗi).

## §5. Ba điểm khác tôi soi mà không có câu hỏi — hai xác nhận, một cảnh báo

**✅ §3 "biến đúng là *vé này có việc gì cho CSKH làm không*"** — tôi thử tìm
mốc tốt hơn và không tìm ra. Mốc "đang khiếu nại dở" của PO **thật sự ngập**
đúng như bạn nói, và lập luận *"N vé cho MỘT sự cố là nhân bản một việc duy
nhất thành hàng chờ"* là lập luận đúng. Nó cũng **khớp** cảnh báo có sẵn trong
`graph.py` cho nhánh 429 (*"đổ một nắm ticket ma lên CSKH cho những khiếu nại
KHÔNG TỒN TẠI"*) — bạn đang áp cùng một nguyên tắc, nhất quán.

**✅ §4 ba nguồn gốc không gộp** — đúng, và lý do bạn nêu (*cờ
`human_handoff_requested` đã gộp hai cái đầu, đó chính là finding đang chờ vá*)
là lý do đúng. **Đừng thêm cái thứ ba vào một ô đang hỏng.**

⚠️ **Cảnh báo về thứ tự land, ngoài phạm vi đặc tả nhưng chạm nó:** đặc tả này
là **điều kiện tiên quyết của việc xoay khoá**. Cửa sổ xoay khoá = một chuỗi
`AuthenticationError` 401 ⟹ **xoay trước khi vá là tự tạo một cửa sổ 500 trước
mặt khách bằng chính hành động sửa lỗi bảo mật.** Bạn đã ghi ở §6; tôi nâng nó
từ *"điều đặc tả không giải quyết"* lên **ràng buộc thứ tự**: `vá → xoay → gọi
thử một lượt xác nhận 200`.

## §6. Phán quyết

**DUYỆT §0 · §2 · §3 · §4 · §5 · §6** — với **hai sửa bắt buộc**:

1. **§2 tách làm hai câu theo LỚP LỖI** (thoáng qua ↔ cần can thiệp), câu thứ
   hai **không hứa mốc thời gian** và **phải chỉ đường sang kênh khác** (§2+§3).
2. **§4 thêm `request_id` + `correlation_id`**, giữ nguyên lệnh cấm thân thô.

**CHƯA DUYỆT §1** cho tới khi đặc tả **nói rõ trục vận hành land cái gì trong
CÙNG lượt** (§1). Không phải vì bảng phân loại sai — nó đúng — mà vì **cột "BÁO
ĐỘNG" hiện chưa có cơ chế nào phía sau**, và land trục khách một mình sẽ **đổi
một hỏng-ồn lấy một hỏng-câm**.

**Ghi nhận:** đặc tả này **tự khai đánh đổi ở chỗ bất lợi cho chính nó** (§3
"cố ý mất dấu"), **tự nêu điều nó không giải quyết** (§6), và **tự viết ca đối
chứng** trước khi ai đòi. Ba thứ đó là lý do bản rà này ngắn hơn hẳn bản rà
F-31/F-32.

---

## §7. 🔴 CHẶN XOAY KHOÁ — "bước 1 xong" là SAI. Bản vá **chưa chạy** ở đâu cả (trừ một container sửa tay)

Tech-lead land `5ac18bf` và kết luận *"bước 1 xong, xoay khoá được rồi"*. **Đo
lại — không phải vậy:**

```
fin05-backend-1     /health build_commit = 7450184   ·  grep "ncc_can_can_thiep" = 1
fin05ttl-backend-1  /health build_commit = 7450184   ·  grep "ncc_can_can_thiep" = 0   🔴
git: 5ac18bf (bản vá) LÀ HẬU DUỆ của 7450184 ⟹ ẢNH CỦA CẢ HAI KHÔNG CHỨA BẢN VÁ
docker diff fin05-backend-1  →  C /app/src/agents/graph.py                     🔴
```

⟹ Bản vá tồn tại ở **git** và ở **đúng một container bị sửa tay bằng `docker
cp`**. **Không ảnh nào chứa nó.**

**Hệ quả trực tiếp lên thứ tự `vá → xoay`:**

| Ngăn xếp | Khi xoay khoá bây giờ |
|---|---|
| `fin05ttl-backend-1` | **không có bản vá** ⟹ chuỗi `AuthenticationError` 401 → **500 trần** |
| `fin05-backend-1` | có bản vá **cho tới lần restart/rebuild đầu tiên**, rồi mất |

Và `fin05ttl-*` chính là ngăn xếp **có "đường tunnel"** trong Caddyfile — tức
ứng viên số một cho đường ra Internet, câu hỏi **vẫn đang chờ PO thật**.

> **Điều kiện xoay khoá, sửa lại cho chính xác:** không phải *"bản vá đã land"*
> mà **"bản vá ĐANG CHẠY trên MỌI ngăn xếp có thể nhận traffic"** — kiểm bằng
> `grep` trong **từng** container, sau khi **dựng lại ảnh**, không bằng `git log`.

## §8. 🔴 Và nó làm hỏng một lời khuyên tôi đã đưa: `build_commit` KHÔNG định danh mã ĐANG CHẠY

Ở `b35e9dc` §6 tôi đưa PO một câu hỏi đóng: *so `build_commit`/`build_at` để
biết ngăn xếp nào là ngăn xếp nào.* Phép đo trên **bác một nửa lời khuyên đó**:

`fin05-backend-1` khai `build_commit=7450184` **trong khi đang chạy mã khác** —
vì `docker cp` sửa tệp mà **không** đụng nhãn. Hai container khai **cùng**
`build_commit` và **cùng** `build_at` mà **nội dung khác nhau**.

**Sửa lời khuyên:**
- `build_commit` định danh **ẢNH**, không định danh **MÃ ĐANG CHẠY**. Nó vẫn
  dùng được cho câu hỏi *"máy nào"* (câu tôi đưa PO), nhưng **không** dùng được
  cho câu *"mã nào"*.
- Muốn trả lời *"mã nào đang chạy"*, phải kèm `docker diff <container>` — nếu
  có dòng `C /app/...` thì **nhãn đang nói dối**.

*(Đây là lần thứ hai trong ngày `docker cp` tạo ra một khoảng cách giữa **thứ
được khai** và **thứ đang chạy**: lần đầu là `tests/conftest.py`, lần này là
`graph.py`. Cùng cơ chế, và lần này nó nằm chắn trước một thao tác bảo mật.)*
