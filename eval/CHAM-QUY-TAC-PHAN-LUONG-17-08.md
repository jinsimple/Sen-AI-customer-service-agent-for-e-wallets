# Chấm quy tắc phân luồng trên bộ ca DƯƠNG

> Vai: **tester** · 17/08 · 0 lượt LLM.
> Luật: `quy_tac_phan_luong.py` băm `742df94b195a` (tôi đo; PO báo `1edd51dff555`
> — **hai băm khác nhau**, xem §cuối).
> Bộ ca: `eval/bo_ca_luot_don.json` băm `241851470116` · 20 ca = 20 câu.
> **Tôi chấm**, script chỉ in quyết định (`--mong-doi` không truyền).

## Kết quả

    ĐÚNG 15/20 · SAI 5/20
    và CẢ NĂM ca sai đều lệch về phía AN TOÀN (mong `nhe`, luật cho `day_du`)

| nhóm | đúng | sai | hạng |
|---|---:|---:|---|
| ④ bẫy ngắn | 4 | 1 | 🔴 điều kiện land |
| ⑤ tham số trần | **4** | **0** | 🔴 điều kiện land |
| ⑥ hỏi chính sách | **2** | **0** | 🔴 điều kiện land |
| ① chào hỏi | 3 | 0 | tốn tiền |
| ② cảm ơn | 2 | 1 | tốn tiền |
| ③ mơ hồ | **0** | **3** | tốn tiền |

⟹ **Mọi điều kiện land ĐẠT.** Ca sai duy nhất trong nhóm ④ là `DON-19`
(*"cảm ơn bạn đã tra giao dịch giúp mình"*) — bẫy **ngược**, tôi đã ghi từ đầu
là ca đo **chi phí**, không đo an toàn.

## 🔴 CÂU NHIỄM CỦA PO — trả lời bằng ĐO, không bằng phán đoán

PO hỏi: *luật chữ số có trông như viết riêng cho ba chuỗi bị rò không?*

Tôi không trả lời bằng cách đọc luật rồi nhận xét. Tôi **vô hiệu hoá luật chữ
số** rồi chấm lại:

    luật ĐẦY ĐỦ       15/20
    luật BỎ chữ số    15/20
    số ca ĐỔI quyết định: 0

**Luật chữ số hoàn toàn THỪA trên bộ ca này.** Mọi ca nó bắt, danh sách cho
phép đã bắt trước rồi — kể cả ba chuỗi bị rò.

> ⟹ **Nhiễm có ảnh hưởng BẰNG KHÔNG lên kết quả** — và không phải vì tác giả
> cưỡng lại được cám dỗ, mà vì thứ họ có thể đã gọt **không làm gì cả ở đây**.
> Đây là bằng chứng mạnh hơn bất kỳ lời khai nào, kể cả lời khai trung thực.

**Không huỷ kết quả, không đổi vai.** Ba dấu hiệu độc lập cùng chiều: luật là
`\d` trần (rộng hơn hẳn mọi hình dạng bị rò — một luật gọt sẽ là `^TXN\d+$`);
nó **cố ý** chấp nhận chặn nhầm `"cảm ơn 1000 lần"`, cái giá không ai trả để
gọt cho ba chuỗi; và nó bắt cả `mất 500k` · `bị trừ 2 lần` · `chiều nay lúc 3h`
— **không chuỗi nào trong số đó bị rò**.

## 🔴 PHÁT HIỆN QUAN TRỌNG HƠN: `XA_GIAO` đang GÁNH TOÀN BỘ

Hệ quả trực tiếp của phép thử trên: **danh sách cho phép làm hết việc.** Luật
chữ số và luật độ dài không quyết định ca nào trên bộ này.

⟹ Chất lượng router **bằng đúng** chất lượng của một tập ~40 từ xã giao. Và đó
là chỗ trôi sẽ xảy ra:

> Ai đó thấy `③ mơ hồ` trượt 0/3 sẽ **thêm từ vào `XA_GIAO`** để cứu — `"hỏi"`,
> `"giúp"`, `"mình"`, `"có"`, `"không"`. Mỗi từ thêm vào **mở một lỗ**, và lỗ
> đó **không hiện trên bộ ca dương** (nó chỉ làm điểm dương ĐẸP HƠN). Nó chỉ
> hiện trên bộ âm — nơi không ai chạy lại vì "chỉ sửa danh sách từ".

**Đề nghị thành cổng:** mọi thay đổi `XA_GIAO` phải chấm lại **CẢ HAI** bộ,
và số bộ âm phải giữ **124/124**. Danh sách cho phép chỉ an toàn khi nó **đóng**
— nới nó là đổi bản chất của luật, không phải tinh chỉnh.

## Năm ca trượt — lý do từng ca, và ba ca đầu là MỘT vấn đề

    DON-05  "thôi mình tự xử lý được rồi, cảm ơn bạn"   token lạ: thôi·mình·tự
    DON-06  "alo có ai không, em hỏi tí"                token lạ: có·ai·không
    DON-07  "cho mình hỏi cái này với"                  token lạ: cho·mình·hỏi
    DON-08  "bạn ơi giúp mình với"                      token lạ: giúp·mình
    DON-19  "cảm ơn bạn đã tra giao dịch giúp mình"     token lạ: đã·tra·giao

Bốn trong năm ca trượt vì cùng một nhóm từ: **đại từ và động từ nối thông
dụng** (`mình` · `cho` · `có` · `không` · `hỏi` · `giúp`). Đó là **một** khoảng
trống, không phải bốn ca lẻ.

⚠️ Nhưng **đừng vá bằng cách thêm chúng vào `XA_GIAO`** — `"giúp mình"` xuất
hiện nguyên vẹn trong `"giúp mình tra giao dịch bị trừ 2 lần"`. Nếu cần cứu
nhóm ③ thì phải là một **cơ chế khác**, không phải nới danh sách.

## `DON-08` — điểm số phụ thuộc một quyết định CHƯA CHỐT

PO phán `nhe` **có điều kiện** (đường nhẹ được phép hỏi lại). Luật cho
`day_du`.

    điều kiện ĐƯỢC cài  →  luật SAI ở ca này  →  15/20
    điều kiện KHÔNG cài →  nhãn lật `day_du`  →  luật ĐÚNG  →  16/20

⟹ **Con số này chưa đứng yên**, và nó đợi một quyết định thiết kế chứ không đợi
thêm phép đo. Ghi ra để không ai trích `15/20` như một hằng số.

## Kinh tế — câu tôi nghĩ PO cần hơn tỉ lệ

Trong 9 ca nhãn `nhe`, luật cho đi đường nhẹ **4**. ⟹ nó thu được **44%** phần
tiết kiệm có thể có, đổi lại **an toàn tuyệt đối** trên mọi điều kiện land.

Đó là một đánh đổi **hợp lý** và đúng hướng-sai-an-toàn. Nhưng nó cũng nói:
nếu ai đó kỳ vọng lớp định tuyến cắt được phần lớn token của lượt đơn thì con
số thật là **44% của phần đó**, không phải 100%.

## ⚠️ Hai băm khác nhau — chưa giải thích

PO báo luật băm `1edd51dff555`. Tôi đo `sha256[:12] = 742df94b195a` trên
`quy_tac_phan_luong.py` (6.305 byte).

Không kết luận ai đúng — nhiều khả năng **hai cách băm**, đúng lần thứ mười
trong ngày. Nhưng nó phải được giải trước khi ai trích `15/20`: **một con số
chấm trên một luật không định danh được thì không tái lập được.**

---

## Bổ sung: PHÂN BỐ LÝ DO, và bộ ca âm kiểm ĐÚNG mệnh đề chính

### ① Phân bố lý do trên bộ DƯƠNG — nó BÙ đúng lỗ của bộ âm

    bộ ÂM  (124 câu, coder đo)      bộ DƯƠNG (20 câu, tôi đo)
      103  CÓ CHỮ SỐ                   6  CÓ CHỮ SỐ
       21  DÀI > 40                    1  DÀI > 40
        0  TOKEN NGOÀI TẬP  🔴         8  TOKEN NGOÀI TẬP  ← mệnh đề CHÍNH
                                       5  mọi token xã giao (→ nhe)

⟹ Mệnh đề chính **khai hoả 8 lần** trên bộ dương, trong đó ba ca là **khiếu nại
thật, ngắn, không chữ số**: `tiền chưa về` · `chuyển nhầm rồi` · `Phí rút tiền
về ngân hàng bao nhiêu?`.

**Hai bộ ca bù nhau, không chồng nhau** — và không bộ nào một mình đủ. Đó là lý
lẽ mạnh hơn cả hai con số cộng lại.

### ② Bộ ca ÂM mới — `eval/bo_ca_am_ngan_khong_so.json` · băm `e411a9dbcc74`

14 ca, **tất cả không chữ số và dưới 40 ký tự** — tự kiểm bằng máy trước khi
băm, vì một ca lọt vào nhánh khác là một ca **không kiểm được mệnh đề chính**.

    LUẬT HIỆN TẠI        14/14 day_du · 100% qua TOKEN NGOÀI TẬP
    LUẬT ĐÃ XOÁ ĐỘ DÀI   14/14 day_du · 100% qua TOKEN NGOÀI TẬP
    số ca đổi quyết định: 0

⟹ **Con số này thuộc CẢ HAI vật.** PO không phải chờ một vòng đo: dù coder xoá
mệnh đề độ dài hay không, `14/14` vẫn đúng, vì bộ ca **cố ý không chạm** nhánh
đó.

### 🔴 ③ Ba ca cuối là BẪY CHO MỘT BẢN VÁ CHƯA XẢY RA

Tôi đã cảnh báo ở phần trên: ai đó thấy nhóm ③ trượt 0/3 sẽ **thêm từ vào
`XA_GIAO`** — `mình` · `cho` · `hỏi` · `giúp`. `AM-12/13/14` chứa **đúng những
từ đó**, trong những câu là **khách đang mất tiền**:

    AM-12  "mình bị mất tiền"                  ← 'mình'
    AM-13  "cho mình hỏi sao tiền chưa về"     ← 'cho' 'mình' 'hỏi' — nguyên văn DON-07
    AM-14  "giúp mình với, tiền không thấy đâu" ← 'giúp mình với' — nguyên văn DON-08

> Không có ba ca này, cú nới danh sách để cứu 3 ca **tốn tiền** trông như một
> cải tiến thuần — và nó sẽ đẩy 3 ca **hại người** sang đường nhẹ.

Và `AM-03` `"bị trừ hai lần"` là ca tôi thích nhất: **cùng nghĩa** với
`"bị trừ 2 lần"` nhưng viết bằng chữ ⟹ luật chữ số **mù hoàn toàn**. Chỉ danh
sách cho phép cứu được. Nó chứng minh luật chữ số **không** phải lớp phòng thủ
cho nhóm này — điều mà bộ âm cũ (103/124 dựa vào chữ số) che mất.

### ④ Nguyên tắc PO rút, tôi ký và ghi

> **Chữa bằng XOÁ thì không thể vừa-khít bộ ca.**

Xoá một mệnh đề **thu hẹp** không gian hành vi ⟹ không thể ôm sát một bộ ca cụ
thể. Chỉnh một ngưỡng (`40 → 60`) thì **có thể** — và đó đúng thứ ta vừa cấm.
Hai bản vá nghe giống nhau ở chỗ *"động vào mệnh đề độ dài"* mà **khác hẳn về
hạng an toàn**: một cái không gian lận được, một cái có.
