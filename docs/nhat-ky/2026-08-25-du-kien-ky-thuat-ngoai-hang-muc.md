# Dữ kiện kỹ thuật đo được trong đợt "OTP trước token" — NGOÀI mọi hạng mục

> **Ngày:** 2026-08-25 · **Người đo:** Coder (`p-226-63`) · **Yêu cầu:** PO thật (đóng đợt)
>
> Đây **không phải** nhật ký đợt. Đây là **sáu dữ kiện kỹ thuật** không thuộc hạng mục
> nào, sẽ **chết cùng phiên** nếu không ghi, và **áp cho mọi đợt sau**.
> Đọc hết trong hai phút. Mỗi mục: **số đo · cách dựng lại · vì sao đáng nhớ.**

---

## ① `return_direct=True` CÓ hỗ trợ — và phép dò hiển nhiên nhất cho ÂM TÍNH GIẢ

```
langchain 1.3.15 · langchain-core 1.5.4   (đo TRONG container, không trên host)

@tool                      → return_direct = False
@tool(return_direct=True)  → return_direct = True        ← cờ CÓ tác dụng thật
inspect.getsource(create_agent), dòng 838-842:
  "# Only include exit_node in destinations if any tool has return_direct=True"
  any(tool.return_direct for tool in tool_node.tools_by_name.values())
```
⟹ `create_agent` **tự dựng `exit_node`**. Thiết kế *"dừng ngay sau một tool cụ thể"*
**không cần** viết lại bằng `StateGraph` tuỳ biến, **không cần** đổi kiến trúc agent.

🔴 **BẪY — phép dò hiển nhiên nhất cho kết quả NGƯỢC:**
```
hasattr(BaseTool, 'return_direct')          →  False    ← SAI, âm tính giả
BaseTool.model_fields  chứa 'return_direct' →  True     ← đúng
```
`return_direct` là **field pydantic trên INSTANCE**, không phải thuộc tính LỚP.
Nếu báo cáo dừng ở `hasattr`, cả đội đã kết luận *"không hỗ trợ ⟹ phải đổi kiến trúc"*.
Nó chỉ lộ ra vì `create_agent` **mâu thuẫn** với phép dò — và người đo đi đào tiếp thay
vì báo con số đầu tiên.

**Luật rút ra:** *một phép dò mâu thuẫn với nguồn khác thì phải ĐÀO, đừng chọn bên nào
tiện hơn.* Với pydantic, kiểm bằng `model_fields`, không bằng `hasattr` trên lớp.

---

## ② Lệch host ↔ container nằm HOÀN TOÀN ở trục `tool`, KHÔNG ở `system`

```
                    băm src/        system    tool     tổng
HOST (venv P-121)   691dd9c40578     5.275    1.982    7.257
container           691dd9c40578     5.275    2.014    7.289
                    ↑ GIỐNG HỆT      ↑ khớp   ↑ +32
nguyên nhân: langchain-core 1.5.3 (host) vs 1.5.4 (container)
             — chỉ chạm `convert_to_openai_tool()`
```
⟹ **Hệ quả dùng được:** thay đổi chỉ chạm `prompt.py` (trục `system`) thì **đo trên host
là HỢP LỆ**; tổng thật tính bằng `tool` số **container**. Thay đổi chạm docstring tool
thì **bắt buộc đo trong container**.

🔴 `docs/STATE.md:24` cấm dùng `P-121-new/.venv` *"để đo kích thích gửi model"*. Câu ấy
phủ **cả việc đếm token của kích thích**, không chỉ *gọi LLM thật* — người đo trong đợt
này đọc đúng chữ mà hiểu hẹp, và con số `293 token headroom` sai đã lan vào kế hoạch
của cả đội trước khi QA/QC đo lại ra `261`. (Đã niêm ở `e727067`.)

---

## ③ SÁU lần dụng cụ đo hỏng trong MỘT phiên — và chiều lệch của từng lần

Ghi cả **chiều** vì chiều mới quyết định mức nguy:

| # | dụng cụ hỏng thế nào | chiều lệch | hậu quả nếu tin |
|---|---|---|---|
| 1 | bộ bóc câu corpus mù khoá `utterances` (là DANH SÁCH) → 7/409 câu, rồi mù `query_co_dau` → 349/409 | **TRẤN AN** | báo *"4 → 4, không đổi"* cho một nghiệm thu |
| 2 | `cd $D` rò sang lệnh sau ⟹ đo **bản sao hai lần**, in ra hai số giống nhau | **CHO PHÉP HÀNH ĐỘNG NGUY** | kết luận *"bản sao vẫn khớp repo, dựng thoải mái"* |
| 3 | đo bằng venv `P-121-new` — thứ STATE cấm đúng cho việc này | **TRẤN AN** | `293` thay vì `261`, lan vào quyết định phân bổ |
| 4 | `hasattr` trên lớp cho field pydantic (mục ①) | **BI QUAN** | bỏ một đường kiến trúc đúng |
| 5 | `head -8` cắt mất 2 dòng cuối của kết quả tra giao dịch | **TRẤN AN** | báo *"không có giao dịch nào đúng 393.000"* — trong khi có đúng hai, và giả định của PO **đúng** |
| 6 | `npx vitest run` chạy từ **gốc repo** thay vì `frontend/` → `29 failed` (thật: `2 failed \| 37 passed`) | **BI QUAN** | gỡ một **bản vá ĐÚNG** vì tưởng nó làm vỡ frontend |

🔴 **Bốn lần lệch về phía trấn an, hai lần lệch về phía bi quan.** Cả hai chiều
đều đắt, nhưng **khác cách**: trấn an làm ta tin sai; bi quan làm ta **bỏ đường đúng**.
Một bộ kiểm chỉ canh chiều trấn an sẽ **không bao giờ bắt được lần ④ và lần ⑥**.

**Phép thử rẻ đã cứu cả sáu lần:** in **MẪU SỐ** cạnh mọi tỉ lệ, và **đo tách rời từng
lệnh** thay vì nối `&&`/`cd`.

---

## ③b 🔴 MẪU HÌNH LỚN NHẤT CỦA NGÀY — "ĐO ĐÚNG CÁCH, SAI VẬT"

*(PO yêu cầu ghi nguyên văn kèm đủ bốn ca, 25/08; ca ⑤ bổ sung cùng ngày theo yêu cầu PO.
Chưa cấp ký hiệu luật — Lead cân lúc nghiệm thu. **Có bằng chứng năm ca thì cân được; chỉ
có một câu hay thì không.**)*

> **Cả năm lần dụng cụ đo hỏng trong ngày đều là "đo ĐÚNG CÁCH, sai VẬT" — không lần
> nào là "đo sai cách". Bộ kiểm của đội đang canh CÁCH ĐO; chưa có gì canh ĐO CÁI GÌ.**

```
① đo `_TOKEN_MA`              — hàm KHÔNG bị vá   (vật cần đo: `_MA_CO_GACH`)
② đo băm ảnh vs CHÍNH NÓ       — do `cd` rò sang lệnh sau (vật cần: ảnh vs CÂY LÀM VIỆC)
③ đo trên `fin05-po-test`      — ngăn KHÔNG mang mã của đợt (build từ bản sao đông cứng)
④ dò `hasattr(BaseTool, …)`    — trên LỚP, trong khi field nằm trên INSTANCE
⑤ chạy `vitest` từ GỐC REPO    — trong khi bộ test sống ở cây `frontend/`
```
**Năm lần · nhiều người · nhiều thời điểm khác nhau · CÙNG MỘT hình dạng.**

🔴 **Mọi cổng dự án hiện có đều MÙ với nó**, vì chúng kiểm *phép đo có đúng quy trình
không* — không kiểm *phép đo có trỏ vào đúng VẬT không*. Một phép đo sai vật đi qua
mọi cổng, cho một con số **đúng định dạng, đúng đơn vị, đúng cách tính**, và sai.

**Chiều lệch không cố định — đó là chỗ nguy nhất:**
```
① và ② và ③  → TRẤN AN     (tin rằng ổn trong khi không ổn)
④ và ⑤       → BI QUAN     (bỏ một đường đi ĐÚNG / gỡ một bản vá ĐÚNG)
```
Một bộ kiểm chỉ canh chiều trấn an **không bao giờ bắt được ca ④ và ca ⑤**.

**BA BIẾN THỂ THÊM, tìm được cuối ngày — quan trọng vì chúng KHÁC cách phát hiện:**
```
sai VẬT             → con số trông LẠ          → bắt được bằng ĐO LẠI
cắt mất phần dưới   → con số trông HỢP LÝ      → bắt được bằng IN MẪU SỐ
   (`head -8` giấu 2 dòng ⟹ suýt kết luận "không có giao dịch nào đúng 393.000"
    trong khi có đúng hai — và suýt báo rằng giả định của PO sai, trong khi nó đúng)
sai ĐƠN VỊ          → con số ĐÚNG              → 🔴 KHÔNG bắt được bằng đo lại
   (`so_tool_call` đếm theo LƯỢT; ba phiên cùng đọc nó như số theo HỘI THOẠI,
    mất nhiều vòng cho một mâu thuẫn KHÔNG TỒN TẠI. Chỉ bắt được bằng câu hỏi
    **"số này đơn vị gì"** — không phép đo nào tự trả lời câu ấy.)
sai THƯ MỤC LÀM VIỆC → KHÔNG con số nào SAI  → 🔴 KHÔNG bắt được bằng đo lại,
                                              cũng KHÔNG bằng in mẫu số
   (`npx vitest run` từ gốc repo → `29 failed`; từ `frontend/` → `2 failed | 37 passed`.
    CÙNG một lệnh · CÙNG một công cụ · CÙNG một phiên bản — chỉ khác GỐC QUÉT.
    Đo lại từ chính chỗ cũ cho đúng con số cũ, mãi mãi. Chỉ bắt được bằng câu hỏi
    **"lệnh này đang đứng ở đâu"** — `pwd` cạnh mọi phép đo, không phép đo nào tự khai.)
```

🔴 **VÀ HỆ QUẢ NẶNG NHẤT — nó chạm vào chính cách đội dựng bất biến:**
> **Một bất biến kiểm QUAN HỆ giữa hai số rút từ CÙNG một nguồn thì không phải bất
> biến — nó là một phép lặp lại.**
[ĐO] `so_tool_call` và `so_luot_goi_model` **đều** duyệt `turn_messages =
all_messages[prev_len:]`. Bất biến `so_luot_goi_model == so_tool_call + 1` **khít
100%** — nhưng nếu danh sách ấy thiếu một cụm `AIMessage(tool_calls) → ToolMessage →
AIMessage`, **cả hai cùng tụt** và quan hệ **vẫn khít**.
⟹ Nó **im lặng đúng ở ca nó đáng kêu nhất**, và tệ hơn: **trông như bằng chứng**.
Cùng họ `if tm is None: continue` — cơ chế không sai, nó chỉ **không nhìn thấy thứ đã
rơi khỏi tầm**.
**Phép thử:** với mỗi bất biến, hỏi *"hai vế có rút từ hai NGUỒN ĐỘC LẬP không?"*
Không ⟹ nó chỉ chứng minh **nội bộ nhất quán**, không chứng minh **đúng**.

---

**Phép thử rẻ nhất đã cứu cả sáu lần** — không cái nào cần công cụ mới:
1. **In MẪU SỐ cạnh mọi tỉ lệ** (bắt ①③ ở dạng "quần thể sai").
2. **Đo tách rời từng lệnh**, không nối `&&`/`cd` (bắt ②).
3. **Đọc diff TRƯỚC khi đo** — đừng đo cái mình ĐOÁN là đúng chỗ (bắt ①④).
4. **Một phép dò mâu thuẫn với nguồn khác thì phải ĐÀO**, đừng chọn bên tiện hơn (④).
5. **In `pwd` cạnh mọi phép đo chạy bằng lệnh** (bắt ⑤ — và **chỉ** cái này bắt được nó:
   không con số nào sai, nên đo lại và in mẫu số đều **im lặng**).

🔴 **Vì sao ⑥ đáng ghi hơn năm lần trước** *(PO nêu, 25/08)*: nó lệch về phía **bi quan**,
tức **loại nguy hơn**. Một kết luận sai kiểu *"bản vá này làm vỡ frontend"* khiến ta **gỡ
một bản vá ĐÚNG** — và **không ai đi kiểm lại**, vì không ai muốn đứng ra bảo vệ một bản
vá đã bị tuyên là hỏng. Sai theo hướng trấn an còn có ngày bị thực tế cãi lại; sai theo
hướng bi quan **tự xoá bằng chứng của chính nó**.

---

## ③c 🔴 HỌ THỨ HAI, CHƯA CÓ TÊN — "CHÚ THÍCH CHẾT" *(về ĐỌC, không phải về ĐO)*

*(PO yêu cầu tách khỏi Luật AC, 25/08. **AC nói về ĐO; mục này nói về ĐỌC.** Cùng một ngày,
hai họ khác nhau — và họ này chưa có ký hiệu.)*

> **Một chú thích ĐÚNG-NGHE ngồi trên một dòng KHÔNG còn làm điều nó nói.**
> **Chú thích chết nguy hơn code chết: code chết KHÔNG CHẠY, chú thích chết VẪN ĐƯỢC ĐỌC.**

**Hai ca, cùng một ngày, hai người khác nhau, hai tệp khác nhau:**

```
① ChatClient.tsx:536  "reply vẫn được hiển thị: nó đã mang sẵn câu chống mạo danh K3"
   ⟹ người viết LO ĐÚNG THỨ ĐÁNG LO, rồi tự bảo đảm bằng một `push` MỚI
   ⟹ không biết :501 đã đẩy rồi ⟹ khách thấy bong bóng hiện HAI LẦN   (vá 8e2e72d)

② graph.py:1866   "⑨ — loại khiếu nại đọc từ `args`, KHÔNG từ `result`…"
   ⟹ ⑨ ĐÃ DỜI điểm móc sang hai tín hiệu thread (cùng ngày, cùng đợt)
   ⟹ biến `loai_khieu_nai` thành tử thi, nhưng CHÚ THÍCH Ở LẠI
   ⟹ người sửa ⑨ sau này sẽ đi tìm ở `create_ticket` — sai chỗ, ĐÚNG LÚC ⑨ hỏng  (vá 25e2731)
```

🔴 **Vì sao nó sống sót qua mọi lần đọc lại:** cả hai dòng đều có **lý do chính đáng ghi ngay
bên trên**. Review đi tìm dòng *"trông sai"* **không bao giờ dừng lại ở đây** — dòng trông
**rất đúng**, vì nó **từng đúng**.

**Khác Luật AC ở tiền đề:** AC hỏi *"phép đo có trỏ đúng vật không"*. Mục này hỏi
*"lời giải thích có còn mô tả đúng thứ nó đang ngồi trên không"*. AC bắt bằng phép đo;
mục này **không phép đo nào bắt được** — `ruff` chỉ thấy biến chết, **không thấy chú thích chết**;
ở ca ① thì không cổng nào thấy gì cả.

**Ba chỗ sinh ra nó — đều là việc TỐT làm dở dang:**
```
· DỜI một cơ chế đi chỗ khác  → chú thích ở chỗ CŨ không ai gỡ
· thêm một lớp bảo đảm mới    → lớp CŨ vẫn còn, cộng dồn tác dụng phụ
· nhánh `return` sớm giữa hàm → ở ĐỦ XA đoạn dùng chung để không lọt vào cùng một màn hình
```

**Phép thử rẻ, dùng được ngay:** khi **dời** hoặc **thay** một cơ chế, `grep` tên cũ của nó
*(biến · hằng · tên hàm)* và đọc **mọi chú thích** quanh mỗi kết quả — không chỉ mọi lệnh gọi.
🔴 **Xoá code chết mà để lại chú thích chết là làm xong một nửa, và nửa còn lại mới là nửa
được đọc.**

---

## ③d 🔴 "[ĐO]" LIỆT KÊ THỨ ĐÃ CHẠY, KHÔNG LIỆT KÊ THỨ **KHÔNG** CHẠY

*(PO yêu cầu niêm, 25/08. Họ hàng gần của ③c "chú thích chết" — cùng là **người đọc suy
rộng một câu đúng**, không ai nói dối.)*

```
[ĐO] 2755a9e (20/08), nguyên văn dòng cuối commit:
     "[ĐO] eslint/tsc → sạch, chỉ 2 lỗi tiền tồn tại không do commit này."
     ⟹ commit ấy ĐỔI NHÃN một chip giao diện. Vitest KHÔNG được chạy.
     ⟹ dashboard/page.test.tsx ĐỎ SUỐT 5 NGÀY, tới 25/08 mới ai đó nhìn tới.
```

**Người viết không nói dối:** eslint và tsc **thật sự sạch**. **Người đọc suy rộng:** một
dòng `[ĐO]` liệt kê hai công cụ ở cuối commit đọc ra như ***"đã kiểm xong"***, không đọc ra
*"đã kiểm hai trong ba"*.

🔴 **Vì sao nó nguy hơn quên chạy test bình thường:** commit **có** dòng `[ĐO]`, nên nó
**vượt qua** mọi phản xạ soát của đội — ta dạy nhau *"phải có số đo"*, và **nó có số đo**.
Một commit **không có** `[ĐO]` còn bị hỏi; commit này thì không.

**Luật rút ra:** *một dòng `[ĐO]` đứng ở chỗ người ta sẽ đọc thành "đã kiểm đủ" thì **phải
nói rõ những gì KHÔNG chạy**.* `"eslint/tsc sạch — CHƯA chạy vitest"` dài hơn đúng ba chữ
và đóng trọn khoảng cách ấy.

**Cùng hình dạng, ba ca trong một ngày:**
```
③c chú thích chết   → lời giải thích ĐÚNG cho một dòng KHÔNG còn làm điều nó nói
③d "[ĐO]" thiếu vế  → phép đo ĐÚNG, nhưng im lặng về thứ KHÔNG đo
④  `gh run list`    → lệnh ĐÚNG, không lọc nhánh ⟹ đọc CI của một CÂY KHÁC
```
Cả ba: **không câu nào sai. Chỗ hỏng nằm ở khoảng trống người đọc tự lấp.**

---

## ③f 🔴 VÌ SAO TỰ SOÁT KHÔNG THAY ĐƯỢC SOÁT CHÉO — kể cả khi người vá ĐÃ ĐO THẬT

*(PO yêu cầu ghi thành mục riêng, 25/08. Mục này **không thuộc** họ ③c–③e — nó nói **VÌ SAO** họ ấy
sinh ra, và vì sao **không ai tự thoát khỏi nó một mình**.)*

> **Người vá đã ĐO một nửa đúng chỗ, và dừng lại vì nửa ấy trả lời XONG câu hỏi họ đang hỏi.**
> **Không phải lười — là CÂU HỎI ĐÃ HẾT, trong khi CƠ CHẾ thì chưa.**
> ⟹ **Người soát có giá trị không phải vì họ cẩn thận hơn, mà vì họ ĐẾN VỚI MỘT CÂU HỎI KHÁC.**

**Ca sinh ra nó — `e5ee8cd`, và cả ba người đều làm đúng phần của mình:**
```
Coder  hỏi "external có chặn `down -v` không"    → ĐO, đúng: chặn được
       hỏi "`name:` có bắt buộc không"            → ĐO, đúng: bắt buộc, thiếu là `up` chết
       🔴 KHÔNG hỏi "tên CỨNG thì cái gì khác vỡ" ← câu hỏi đã hết ở đây
PO     đọc "external chặn `down -v`"              → duyệt. Câu hỏi của họ cũng hết ở đây.
DevOps đến với câu "nó làm gì với `-p`"           → bắt được NGAY VÒNG ĐẦU
       [ĐO] `-p fin05-sach` vẫn trỏ `fin05_postgres_data` — tên cứng VÔ HIỆU HOÁ
            tiền tố ngăn ⟹ MỌI ngăn dùng CHUNG một volume vật lý. Im lặng.
```

🔴 **Điểm đắt: không ai trong hai người đầu lười, và không phép đo nào của họ SAI.** Hai phép đo của
Coder **đều đúng và đều cần thiết**. Thứ thiếu **không phải độ cẩn thận** — là **một câu hỏi thứ ba
mà cấu trúc của công việc không sinh ra được**: người đang vá `down -v` **không có lý do gì** để nghĩ
tới `-p`.

**Vì sao "cẩn thận hơn" KHÔNG phải bản vá:** cẩn thận làm ta trả lời **kỹ hơn** những câu ta **đã
hỏi**. Nó không sinh ra câu hỏi mới. Càng chuyên tâm vào một vấn đề, tập câu hỏi càng **hẹp lại** —
đó là cách sự tập trung hoạt động, không phải khiếm khuyết cá nhân.

**Phép thử dùng được, rẻ, không cần thêm người:** trước khi land một thay đổi chạm cơ chế dùng
chung, viết ra **câu hỏi mình ĐÃ trả lời**, rồi hỏi *"ai KHÁC dùng cơ chế này, và họ sẽ hỏi gì?"*
Với `docker-compose.yml` thì "ai khác" là **mọi ngăn của mọi phiên** — và câu của họ là `-p`.

⟹ Hệ quả đã thành luật cùng ngày *(PO đặt)*: **mọi thay đổi chạm `docker-compose.yml` phải qua
DevOps soát.** Luật ấy **trả công ngay lần đầu áp dụng**.

---

## ④ `docker compose` GỘP danh sách `ports`, không thay — phải `!override`

```yaml
# SAI — cổng của base VẪN CÒN, ngăn mới đụng cổng ngay
services: { postgres: { ports: ["127.0.0.1:45432:5432"] } }
# ĐÚNG
services: { postgres: { ports: !override ["127.0.0.1:45432:5432"] } }
```
Triệu chứng: `Bind for 127.0.0.1:5432 failed: port is already allocated` **dù override
đã ghi cổng khác**. Mất vài phút vì tưởng mình gõ sai cổng.

---

## ⑤ Hai bẫy vận hành của ngăn dựng mới — cả hai giả dạng "ngăn chết"

```
curl https://127.0.0.1:48443/...   →  000     ← TLS gãy: chứng chỉ Caddy cấp cho `localhost`
curl https://localhost:48443/...   →  307     ← ĐÚNG
backend nghe cổng 8010, KHÔNG phải 8000        ← probe 8000 → "Connection refused"
```
Cả hai **trông y hệt hệ thống hỏng** trong khi `docker compose` đã ghi `healthy`.
Kiểm chéo bằng `docker inspect -f '{{.State.Health.Status}}'` trước khi kết luận.

---

## ⑥ `eval/_harness.py` KHÔNG BAO GIỜ chạm cổng OTP — và đó là dữ kiện về hiệu lực phép đo

```
_harness.py:559  run_agent_turn(session, user_id=…, message=…, thread_id=…)
                 ↑ KHÔNG truyền `otp_verified_at`
graph.py:913     otp_verified_at: float | None = _ALWAYS_FRESH
                 ↑ sentinel = "coi như vừa xác thực"
```
⟹ Mọi ca eval chạy như thể khách **vừa xác thực OTP**. Cổng ④ (`can_otp`) **không bao
giờ bắn trong eval**.

**Vì sao đáng ghi:** đây là dữ kiện dùng để **bác một P0** trong đợt (nghi *"agent ngừng
gọi tool"* — hoá ra không phải, và cổng ④ cũng không phải thủ phạm). Ai viết ca eval
đụng luồng OTP phải **truyền tay** `otp_verified_at`, nếu không họ đang đo một hệ thống
mà cổng OTP không tồn tại.

---

## ⑦ NỢ CÓ PHẠM VI RÕ — Redis KHÔNG CÓ MẬT KHẨU (treo có chủ đích 25/08)

[ĐO] `grep -r 'requirepass|REDIS_PASSWORD'` trên `docker-compose*.yml` · `src/config.py`
· `.env.example` → **0 kết quả**. Chưa phải lỗ đang mở *(không `ports:` ⟹ chỉ với tới
từ trong mạng compose)*; thành lỗ khi ai đó thêm `ports:`, hoặc có container thứ ba
vào cùng mạng, hoặc chạy trên máy dùng chung.

🔴 **Cảnh báo đặt ở `docker-compose.yml`, khối `redis` — KHÔNG ở đây.** Người sẽ gây ra
lỗ là người thêm `ports:`, và họ đọc tệp compose, không đọc `docs/nhat-ky/`. Mục này
chỉ là con trỏ.

🔴 **VÌ SAO VẾ NÀY TỪNG RƠI — đáng nhớ hơn chính lỗ:** phạm vi PO trình PO thật CÓ vế
*"thêm mật khẩu"*, nhưng vế ấy **chưa bao giờ được land vào repo**. Coder dựng lại phạm
vi từ **nguồn tra được duy nhất** (CHECKLIST) và **rơi mất một nửa, im lặng**. Một giờ
trước đó, chính Coder từ chối tin tin nhắn về ADR-051 và đi tìm bản ghi trong repo —
lần này **repo thiếu**, nên kỷ luật đúng vẫn cho kết quả thiếu.
⟹ *"Tin nhắn là dữ kiện hạng thấp nhất"* chỉ bảo vệ được khi **thứ hạng cao hơn tồn
tại**. Điều gì chưa land thì **không có hạng nào cả**.

---

## Liên quan, đã ghi nơi khác — để khỏi chép lại

- **`test_invariants` chỉ so TÊN tool, KHÔNG so CHỮ KÝ** ⟹ đổi input của một tool mà
  quên `contracts/agent-tools.yaml` thì **cổng VẪN XANH**. Đây là lỗ của chính cơ chế
  contract. → `docs/giao-viec/CHECKLIST-dot-otp-truoc-token.md`, mục ⑩ (`655a112`).
- **`fin05-po-test` / `fin05-final` build từ BẢN SAO repo đông cứng** trong scratchpad
  một phiên khác, không từ repo. → checklist, mục điểm danh 25/08.
- **Bản vá 7/7 bị từ chối** (xanh mọi cổng, vỡ vì một chữ tuỳ chọn).
  → `docs/nhat-ky/2026-08-25-ban-va-7-tren-7-bi-tu-choi.md`.
