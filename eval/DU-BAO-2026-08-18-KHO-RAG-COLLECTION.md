# DỰ BÁO — ca đỏ `test_kho_khong_chua_tai_lieu_noi_bo_da_biet`

> Vai: **tester** · 18/08 · **0 token** · viết **TRƯỚC** khi liệt kê collection.
> Đèn xanh PO-agent. Đường: quan sát **hộp đen** qua `docker exec` chỉ-đọc.
> **Không đọc `src/`. Không nhận nội dung soạn sẵn từ tech-lead.**

## ① Điều đã biết, và nó KHÔNG phải "kho rỗng"

`docs/STATE.md` §2 (bản 17/08) ghi ca này đỏ vì *"kho rỗng, điều kiện hạ tầng"*.
Đó là **KẾT LUẬN mà chính cái đèn in ra**, không phải triệu chứng — Luật H:

```
tests/test_rag/test_thanh_phan_tai_lieu_kho.py:113
    pytest.fail("index KHÔNG có doc_id nào — kho rỗng, mọi khẳng định … vô nghĩa")
```
Câu đúng đáng lẽ phải là *"collection tên `policy_faq` trả 0 doc_id"*. Vì nó in
kết luận, cả đội chép lại và tin từ 17/08.

## ② SUY LUẬN — nó cho một dự báo KIỂM ĐƯỢC, không phải phỏng đoán

Đầu dò gõ cứng `c.get_collection('policy_faq')` (dòng 80).

- `get_collection` với tên **không tồn tại** ⟹ **ném ngoại lệ** ⟹ `returncode != 0`
  ⟹ ca sẽ chết ở nhánh `"không đọc được index"`, **không** ở nhánh `"kho rỗng"`.
- Ca đang chết ở nhánh **`"kho rỗng"`**.

⟹ **DỰ BÁO 1: collection `policy_faq` TỒN TẠI và RỖNG (0 metadata).**
Đây là suy luận từ **KIỂU thất bại**, không từ nội dung kho — nên nó kiểm được
và có thể sai một cách nhìn thấy được.

## ③ Dự báo, kèm độ chắc

| # | dự báo | độ chắc | nếu khác thì nghi gì |
|---|---|---|---|
| 1 | `policy_faq` tồn tại, **0** metadata | **cao** — suy từ kiểu thất bại (②) | nếu nó KHÔNG tồn tại ⟹ phiên bản chromadb đổi hành vi `get_collection`, và suy luận ② hỏng ⟹ đọc lại từ đầu |
| 2 | index có **≥2** collection | **trung bình-cao** | chỉ có 1 ⟹ dữ liệu nằm ở **path khác**, không phải tên khác ⟹ đổi hướng truy |
| 3 | đúng **1** collection giữ gần hết dữ liệu, cỡ **≈378 chunk** trên `fin05` | **trung bình** — 378 là số bàn giao 17/08, chưa tự đo | lệch nhiều ⟹ ai đó đã nạp lại kho; hỏi trước khi kết luận |
| 4 | `fin05ttl` cho số **khác** (`≈419`) | **trung bình** | giống hệt ⟹ hai ngăn xếp dùng chung volume — finding riêng, nặng hơn |

🔴 **Khai trước:** dự báo 1 TRÚNG **không** xác nhận rằng ta đã hiểu kho. Nó chỉ
loại một giả thuyết (*"kho rỗng thật"*). Tên collection đúng vẫn là thứ phải
**quan sát**, không được suy.

## ④ 🔴 CẤM VÁ NHANH — ca Luật J sách giáo khoa

Sửa `'policy_faq'` thành tên mới làm cổng ĐỎ→XANH trong một dòng. **Không được
làm thế.** Hỏi cổng ấy khẳng định **CÁI GÌ**: tên nó hứa canh **RÒ TÀI LIỆU NỘI
BỘ vào kho RAG** — trục **rò rỉ dữ liệu**. Vì đầu dò trỏ sai chỗ, phép kiểm ấy
**CHƯA TỪNG chạy trên kho thật**.

⟹ Đây **không** phải "cổng đỏ vì hạ tầng". Nó là **cổng chưa bao giờ khẳng định
được điều nó hứa**. Vá tên suông = đổi một cổng **đỏ trung thực** lấy một **cổng
xanh rỗng** — tệ hơn hẳn trạng thái hiện tại.

## ⑤ Hình dạng bản vá — chốt TRƯỚC khi nhìn số

1. **KHÔNG gõ cứng tên collection nào.** Gõ tên mới là chép từ code lần thứ
   hai, và chết y hệt lần sau khi đổi model nhúng. Test phải **tự liệt kê**.
2. **Kiểm MỌI collection**, không chỉ cái to nhất. *Cổng rò rỉ mà bỏ sót một
   collection là cổng rò rỉ hỏng.*
3. **Đối chứng dương bắt buộc** (Luật A — cổng phải KÊU lúc bất thường): nhét
   một `doc_id` nội bộ giả vào một kho THỬ rồi xác nhận nó **kêu**. Thiếu vế
   này thì "xanh" chỉ nghĩa là chưa ai nhìn kỹ.
4. **Ba trạng thái:** kho sạch · kho bẩn · **không đọc được index** — nhánh thứ
   ba KHÔNG được gộp vào "sạch" (đúng lỗi vừa xảy ra ở đây).
5. Đối chứng dương phải chạy trên **kho THỬ**, tuyệt đối không ghi vào kho đang
   phục vụ (Luật I — bước đo không ghi vào container đang chạy).

---

# ⑥ KẾT QUẢ THẬT — ghi SAU khi quan sát

Dự báo ở trên nằm trong commit `09c8de2`, **trước** khi liệt kê.

```
fin05-backend-1   (3 collection)          fin05ttl-backend-1  (2 collection)
  policy_faq                      0         policy_faq__text-embedding-3-small  0
  policy_faq__text-embedding-v4 378         policy_faq                          0
  policy_faq__text-embedding-3-small 378
```

| # | dự báo | thực tế | |
|---|---|---|---|
| 1 | `policy_faq` tồn tại, **0** metadata | tồn tại, **0** | ✅ **TRÚNG** |
| 2 | index có ≥2 collection | **3** | ✅ TRÚNG |
| 3 | **ĐÚNG 1** collection giữ gần hết dữ liệu, ≈378 | **HAI** collection, **mỗi cái 378** | ⚠️ **TRẬT ở phần "đúng 1"** |
| 4 | `fin05ttl` cho số khác (≈419) | **0 và 0** — cả hai collection rỗng | ❌ TRẬT |

**⓷ trật là phần quan trọng nhất của cả đợt.** Kho có **hai collection phục vụ
song song, một cho mỗi model nhúng** (`text-embedding-v4` của DashScope và
`text-embedding-3-small` của OpenAI). Tôi dự báo một, thực tế hai — và **đúng
cái sai đó là lý do bản vá "sửa tên collection" sẽ hỏng**: nó lại chỉ soi một.

**⓸ trật ⟹ ghi vào rổ CHƯA TRUY, không gán nguyên nhân.** Bàn giao 17/08 ghi
`fin05ttl` có 419 chunk; hôm nay 0. Hoặc kho bị nạp lại, hoặc `fin05ttl` đọc
index ở path khác. **Tôi không đo cái nào trong hai.**

## ⑦ Nguyên nhân ca đỏ — KHÔNG phải "kho rỗng"

Đầu dò gõ cứng `get_collection('policy_faq')` — **collection duy nhất RỖNG
trong ba cái**. Kho thật có **378 chunk**. Suốt thời gian qua ca này đỏ vì
**soi nhầm chỗ**, và vì `pytest.fail` in **KẾT LUẬN** (*"kho rỗng"*) thay vì
**TRIỆU CHỨNG** (*"collection tên `policy_faq` trả 0 doc_id"*), `docs/STATE.md`
§2 chép lại thành *"điều kiện hạ tầng"* và cả đội tin từ 17/08. **Luật H thuần
nhất — không ai sai quy trình, cái đèn nói dối.**

## ⑧ Bản vá — và vì sao nó KHÔNG phải "sửa tên"

Test nay **tự liệt kê mọi collection**, không gõ cứng tên nào (tên mang tên
model ⟹ nó SẼ đổi), và đối chiếu trên **hợp của tất cả**. Ba trạng thái tách
bạch: **sạch** · **bẩn** · **KHÔNG ĐO ĐƯỢC** (không có collection nào · mọi
collection rỗng · có vector mang `doc_id` không tra được hàng CSDL).

### 🔴 Ca đối chứng bắt được lỗi trong CHÍNH CÔNG CỤ ĐO của tôi

Bản đầu của `_tim_lot()` gộp `doc_id` mồ côi vào chung rổ "lọt" bằng cách thay
nó bằng nhãn `<doc_id không có hàng…>`. Ca đối chứng đỏ ngay: bộ lọc đối chiếu
`mau_cam` với **chuỗi doc_id**, không với nhãn ⟹ **mồ côi lọt qua im lặng**, và
một kho có hàng CSDL bị mất sẽ được báo là **SẠCH**.

> Đúng Luật 7 — công cụ đo là lớp không ai canh. Nó lọt qua mắt tôi và bị bắt
> bởi **ca đối chứng viết trong cùng một giờ**. Đây là lý lẽ cụ thể cho việc
> tách logic thuần ra khỏi phần đọc hạ tầng: nếu không tách, ca đối chứng ấy
> **không viết được**, và lỗi này đã đi vào cổng.

## ⑨ Cổng nay khẳng định CÁI GÌ — Luật J, đọc chứ không chỉ ghi nhận màu

Đo thẳng, không suy:
```
TỔNG doc_id (hợp của mọi collection) = 2
tên tệp cổng thật sự đối chiếu:  MoMo_FAQ_Giao_dich.docx · MoMo_ToS.docx
=> lọt={}  mồ_côi={}
```
⟹ Phát biểu ĐÚNG là: *"kho phục vụ của `fin05` chứa đúng 2 tài liệu, và không
tài liệu nào trong `{business_rules, scenario-candidates-momo-faq}` có mặt
trong bất kỳ collection nào."* **Đây là lần đầu tiên cổng này khẳng định được
điều tên nó hứa.**

⚠️ **378 chunk = 2 TÀI LIỆU.** `chunk` và `doc_id` là hai đơn vị đếm khác nhau;
`378` không phải "378 tài liệu" — đừng trích lẫn.

### Đột biến trên VẬT THẬT (không phải trên dữ liệu bịa)

```
mẫu cấm = {'MoMo_F'}  ← chắc chắn CÓ trong kho
=> cổng kêu ở 2/2 collection có dữ liệu, đúng tên MoMo_FAQ_Giao_dich.docx
```
⟹ dây nối container → logic thuần **biết đỏ**, và nó **không dừng ở collection
đầu tiên** — đúng lớp lỗi vừa vá.

## ⑩ Còn treo, KHÔNG kết luận

- `fin05ttl` kho rỗng cả hai collection (bàn giao ghi 419) — **chưa truy**
- **Hai kho song song, hai model nhúng.** Sản phẩm đọc cái nào? Cần `src/` để
  trả lời ⟹ **không phải việc của tester.** Nếu nó chỉ đọc một, cái còn lại là
  378 chunk **chết mà vẫn tốn đĩa**; nếu tuỳ cấu hình, đây là **hai đáp án cho
  cùng một câu hỏi chính sách**. Chuyển tech-lead.
- `test_kho_chi_chua_tai_lieu_duoc_duyet` vẫn **skip** — chưa có danh mục nguồn
  đã duyệt. Cổng thật vẫn chưa bật; cái vừa vá là lớp chặn tối thiểu.

---

# ⑪ VÒNG HAI — Luật M bắt được chỗ tôi đã ngừng soi

PO-agent cấp **Luật M** (*"xác nhận không phải bằng chứng — dấu hiệu khó thấy
là kết quả KHỚP với thứ tài liệu đã hứa"*) và chỉ thẳng: *khi bạn liệt kê
collection và thấy đúng thứ mình đoán, đó là lúc dễ ngừng soi nhất.*

**Áp vào chính tôi thì ra một chỗ thật.** Lần liệt kê đầu cho **378** — đúng con
số bàn giao 17/08 đã hứa. Vì nó khớp, không gì kích hoạt phản xạ soi lại
`path='/app/data/rag_index'` — **và tôi thừa kế nguyên văn path ấy từ chính đầu
dò đã hỏng.**

Đo tiếp (hộp đen, `find` chỉ-đọc):
```
fin05-backend-1     /app/data/rag_index    22M     ← index DUY NHẤT
fin05ttl-backend-1  /app/data/rag_index   188K     ← index DUY NHẤT
cả hai container:   CHROMA_PERSIST_DIR=./data/chroma   ← trỏ path KHÔNG có index
```

🔴 **Biến cấu hình và vị trí dữ liệu thật KHÔNG khớp nhau.** Hôm nay vô hại vì
chỉ có một index. Nhưng nếu sản phẩm có ngày nghe theo biến ấy, một cổng gõ
cứng path sẽ **soi nhầm chỗ y hệt lần trước, chỉ khác một tầng** — cùng lớp lỗi,
cùng cách chết im lặng. *Sản phẩm đang đọc biến nào cần `src/` để trả lời ⟹
**không phải việc của tester**, chuyển tech-lead.*

**Vá:** mã trong container **tự tìm** `chroma.sqlite3` thay vì nhận path. Tìm
thấy **≠1** index ⟹ **KHÔNG ĐO ĐƯỢC**, không được chọn đại một cái. Xác minh:
`["/app/data/rag_index"]`, đúng một, và bộ ca vẫn `2 passed · 1 skipped · 1 xfailed`.

**Và nó đóng nốt câu hỏi ⓸:** `fin05ttl` có index thật (188K) nhưng rỗng — **không
phải** ta soi nhầm path. Vì sao 419 chunk biến mất thì **vẫn CHƯA TRUY.**

> Đây là lần thứ **hai** trong cùng một đợt mà ca đối chứng / phép soi lại bắt
> được lỗi trong **công cụ đo**, không phải trong sản phẩm (lần một: `doc_id`
> mồ côi lọt im lặng). Cả hai đều không có triệu chứng nào — cả hai đều được
> tìm ra vì có người **hỏi tiếp sau khi mọi thứ đã xanh**.
