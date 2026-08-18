# DỰ BÁO — chốt chặn + `so_luot_da_phat` ở tầng TRANSPORT

> Công bố **trước** khi viết dòng nào. Nền: `HEAD=2dba590`, băm `src/` = `42960d5fc61f`.
> tech-lead · 18/08/2026 · việc (2), §5.F.

---

## 0. Tôi đã đề xuất SAI seam một lần — ghi lại để không quay về nó

Tôi đề xuất `_khoa_cho_nha_cung_cap()`. **[ĐO]** nó được gọi **đúng 2 lần, ở mức module**
(`config.py:283` · `:303`) ⟹ bộ đếm cắm ở đó **mãi mãi bằng 2 và trông như đang đếm**. Tôi thấy cả
hai đường cùng *chạm* nó rồi kết luận cả hai *đi qua* nó — **Luật G**, ở chính đề xuất của tôi.

**Seam đúng, đã đo chứ không suy** (openai 3.0.0 · httpx 0.28.1): cả `ChatOpenAI` lẫn
`OpenAIEmbeddings` đều nhận `http_client` ⟹ **một `httpx.Client` dùng chung** là nơi duy nhất mọi
lời gọi **thật sự** đi qua, cả chat lẫn embedding.

**Lợi thế quyết định:** nó thấy **request thật trên dây**, kể cả lượt **SDK tự retry**
(`max_retries=2` ở `graph.py:407`). Mọi bộ đếm đặt TRÊN SDK sẽ ghi **1** cho **3** lần bắn ra —
tức đếm thiếu đúng loại lượt đắt nhất, **cùng hình dạng bẫy `so_luot_goi_model=0`** (§8).

## 1. HAI cơ chế, KHÔNG phải một — tôi đã gộp nhầm, PO-agent tách đúng

```
CỜ CHO PHÉP (nhị phân)  → CHẶN NGAY, không cần con số nào
BỘ ĐẾM BA RỔ (số)       → ĐẾM NGAY, KHÔNG ngưỡng
```
Lỗ §5.F không phải *"tiêu quá nhiều tiền"* mà *"một lời gọi ra Internet mà không ai định thế"* —
câu **có/không**, không phải **bao nhiêu**. Ngược lại, đặt **ngưỡng** bây giờ là đặt theo số ta tự
bịa (A3 là *"chưa nạp gì"*, **không phải một hạn mức thành số**), và **một cổng đã bị nới một lần
thì không ai tin nó nữa**.

## 2. 🔴 BA RỔ — và một điều tôi phải nói thẳng thay vì giả vờ một bộ đếm làm được cả ba

Security xin ba rổ `hit · miss · hỏng` cho **caching**. **Tầng transport KHÔNG đếm được `hit`** —
theo đúng định nghĩa, một cache hit **không bao giờ chạm tới transport**. Giả vờ đếm nó ở đây sẽ
cho ra một cột `hit` **hằng 0**, tức lại dựng đúng một dụng cụ nói dối.

Ba rổ **đúng cho tầng này**, theo thứ transport thật sự phân biệt được:

```
da_phat   request RA TỚI DÂY và có response (mọi status)  → CHẮC CHẮN có thể tính tiền
bi_chan   cờ từ chối, KHÔNG ra dây                        → chắc chắn 0 đồng
hong      ra dây rồi lỗi (timeout · đứt nối · ta bỏ)      → 🔴 KHÔNG ĐỌC ĐƯỢC, KHÔNG phải 0
```
🔴 Rổ `hong` là rổ **quan trọng nhất và dễ bị bóp thành 0 nhất**. [ĐO §6.⓷] `14:26:44` ta bỏ →
`14:26:45.335` DashScope trả **HTTP 200 trọn vẹn, 1,2s SAU**: nhà cung cấp tính theo thứ họ **sinh**,
không theo thứ ta **đọc**. ⟹ một lượt vào rổ `hong` **có thể đã tốn tiền và ta không có cách biết**.
**Không `sum(... or 0)`. Ba mẫu số riêng.**

Khi có caching, `hit` đếm ở **tầng cache** — **nguồn độc lập** với transport, đúng **Luật D**
(hai nguồn thật, không phải một biến viết hai lần).

## 3. Mặc định của cờ — chỗ dễ sai nhất, khai trước

```
FIN05_CHO_PHEP_GOI_RA_NGOAI khai tường minh   → theo lời khai        (1/0)
không khai + đang chạy dưới pytest            → TỪ CHỐI
không khai + còn lại                          → CHO PHÉP
```
🔴 **Mặc định KHÔNG THỂ là từ-chối-tất-cả ở đợt này**: ba container đang chạy không có biến đó
trong `Config.Env`, và biến môi trường **ghim lúc TẠO container** (§9) ⟹ mặc-định-từ-chối sẽ **giết
sản phẩm đang chạy** ngay khi ảnh được dựng lại. Đó là đổi hành vi sản phẩm để vá một lỗ của công
cụ đo.

⚠️ **Và tôi khai thẳng hạn chế: bản này KHÔNG phủ script nháp** — đúng ca tôi tự đâm vào. Script
chạy `python x.py` không phân biệt được với sản phẩm. Phủ nó cần **đảo mặc định thành TỪ CHỐI** +
compose khai `=1`, tức **giai đoạn 2, sau lần dựng ảnh**. Nói ra vì một bản vá được mô tả rộng hơn
thứ nó làm chính là cách một lỗ được coi như đã đóng.

```
giai đoạn 1 (bản này)  pytest phủ · lượt chat phủ · script nháp KHÔNG phủ
giai đoạn 2 (sau dựng) đảo mặc định + compose khai =1  ⟹ phủ cả ba
```

## 4. DỰ BÁO — điền TRƯỚC

| # | vật | DỰ BÁO | THẬT | |
|---|---|---|---|---|
| 1 | băm `src/` | ĐỔI khỏi `42960d5fc61f` | | |
| 2 | file `src/` đổi | **3** — 1 module mới + `graph.py` + `store.py` | | |
| 3 | `contracts/` · `check_contracts` | 0 đổi · sạch | | |
| 4 | `test_invariants.py` | **23 passed** | | |
| 5 | hồi quy 7 file tầng tool | **50 passed** | | |
| 6 | ca đối chứng **đường EMBEDDING** | **KÊU** — `store.search` bị chặn khi cờ tắt | | |
| 7 | ca đối chứng **đường CHAT** | **KÊU** — cùng transport, cùng cờ | | |
| 8 | ca IM: cờ bật | cả hai đường chạy bình thường, `da_phat` tăng | | |
| 9 | `docker diff` | 0 · 0 · 0 | | |
| 10 | token tiêu | **0** — mọi ca đối chứng chặn TRƯỚC khi ra dây | | |

## 5. Nếu khác thì nghi gì

| lệch | nghi |
|---|---|
| #6 **KHÔNG kêu** | 🔴 **nặng nhất.** `OpenAIEmbeddings` không nhận `http_client` như tôi đã kiểm, hoặc langchain dựng client riêng bỏ qua nó ⟹ **chốt chặn là chốt GIẤY**. Đừng sửa ca đối chứng cho xanh — sửa seam |
| #7 kêu nhưng #6 im | chốt chỉ phủ đường chat = đúng lỗ §5.F còn nguyên, và tôi đã "vá" cái đã an toàn |
| #4/#5 đỏ | client dùng chung phá đường nóng ⟹ **revert**, không vá chồng |
| #2 ≠ 3 | tôi sửa lan ngoài ý định trên **cây dùng chung** |
| #10 ≠ 0 | ca đối chứng của tôi ra tới dây thật ⟹ chốt chặn đặt SAU điểm tốn tiền, sai chỗ |

## 6. Khai trước — KHÔNG được tính là xác nhận

Ca đối chứng xanh ⟹ *"cờ chặn được ở tầng transport trong tiến trình thử"*. **KHÔNG** ⟹
*"§5.F đã đóng"* (script nháp chưa phủ — mục 3) và **KHÔNG** ⟹ *"sản phẩm đang chạy được bảo vệ"*
(container còn mã cũ, `lệch× = 1·1·1`, chỉ hết sau lần dựng ảnh chung).

## 7. KẾT QUẢ THẬT

*(để trống tới khi đo xong)*
