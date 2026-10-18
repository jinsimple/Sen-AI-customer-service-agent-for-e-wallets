# DỰ BÁO — bất biến chống livelock, nửa (a). Công bố TRƯỚC khi chạm vật.

> Kỷ luật STATE §8: *công bố dự báo vào git TRƯỚC khi chạm vật*. Đã chạy 2 lần, trúng 6/6 và 2/2.
> File này viết **trước** khi sửa một dòng `src/` nào. Ai đọc sau: so cột **DỰ BÁO** với cột **THẬT**
> ở cuối file. Lệch ⟹ đọc bảng *"nếu khác thì nghi gì"*, **đừng** giải thích cho qua.

Người viết: tech-lead · 18/08/2026 · nền `HEAD=addec5e`, băm `src/` = `b8e7c5397457`

---

## 0. Khai trước — điều gì sẽ KHÔNG được tính là xác nhận

**Một kết quả thuận lợi ở đây KHÔNG xác nhận rằng livelock đã bị đóng trên lưu lượng thật.**
Nửa (a) là bất biến **tất định** ở tầng gọi tool; nó chỉ chứng minh được bằng test tất định.
Tần suất thật (`1/13`, mẫu nhỏ, STATE §6.⓶) **không đổi** vì bản vá này, và **không đo lại được**
khi chưa có hạn mức (A3). Cổng xanh ⟹ *"cơ chế bắn đúng trong ca dựng"*, **không** ⟹ *"đã hết
livelock"*.

---

## 1. Bất biến sẽ cài

> *"Cùng tool + cùng tham số + cùng lỗi ⟹ lần thứ hai là DỪNG."*

**Điểm chèn:** decorator `_locked` trong `build_customer_tools()`
(`src/agents/tools/customer_tools.py`). Chọn chỗ này vì nó là nơi **duy nhất** nhìn thấy đủ **ba**
thứ bất biến cần, trong **một** chỗ, cho **cả năm** tool:

| cần | `_locked` có? | vì sao |
|---|---|---|
| tên tool | ✅ | `functools.wraps` giữ `fn.__name__` |
| tham số | ✅ | `*args, **kwargs` của chính lời gọi |
| **lỗi** | ✅ | nó bọc **dưới** `@tool` ⟹ thấy **giá trị TRẢ VỀ** |

🔴 Vế thứ ba là vế quyết định chỗ chèn: cổng OTP **`return` một dict** `{"status":"error"}`,
**không `raise`** (`customer_tools.py:578-585`). Bất biến nào chỉ bắt exception sẽ **không thấy gì**
và livelock chạy y nguyên.

**Phạm vi đếm:** một `TurnGuard` — tức **một lượt chat**, đúng phạm vi livelock đã đo
(8 tool call **trong một lượt**). Không xuyên lượt, không xuyên thread.

## 2. Ranh giới CỐ Ý — nêu ra để người sau không tưởng là bỏ sót

- **Chỉ đếm `status == "error"`.** `not_found` / `multiple_matches` là **kết quả hợp lệ**, không
  phải lỗi. Lặp lại chúng cũng vô ích, nhưng nới bất biến sang đó là đổi hành vi ở nhánh mà
  **chưa ai đo**, và bất biến sẽ thôi tất định.
- **Chỉ nửa (a).** Không chạm câu nói với khách (nửa (b), đã có 12 ca mẫu, việc riêng).
- **Không đụng `_AGENT_RECURSION_LIMIT`.** Trần đó chặn cả vòng lặp **hợp lệ** (đã đo một lượt
  5 bước tra cứu bình thường). Đây là hai cơ chế khác trục, không thay nhau.
- **Không đụng contract.** Không thêm/bớt/đổi tên tool, không đổi lược đồ, không thêm route.
- **Không gộp 3 chú thích TPM.** Lý do gom chúng vào đợt này đã chết cùng đính chính §5.C1.

## 3. DỰ BÁO — điền TRƯỚC, không sửa sau

| # | vật | DỰ BÁO | THẬT | |
|---|---|---|---|---|
| 1 | băm `src/` | **ĐỔI** khỏi `b8e7c5397457` (sửa ≥1 file `.py`) | `78154194edff` | ✅ |
| 2 | số file `src/` đổi | **1** — chỉ `customer_tools.py` | 1 file, +145/−1 | ✅ |
| 3 | `contracts/` | **0 file đổi** | 0 | ✅ |
| 4 | `check_contracts.py` | **sạch** — băm 3 contract KHÔNG đổi | sạch, `cd3d15a5c90a`·`a5afeae0684b`·`a39f2b84ec5d` | ✅ |
| 5 | `test_invariants.py` | **23 passed** — không đổi số ca | **23 passed** in 1,83s | ✅ |
| 6 | `docker diff` ba container | **0 · 0 · 0** (không dựng ảnh, không `docker cp`) | 0 · 0 · 0 | ✅ |
| 7 | `BUILD_COMMIT` ba container | **`bec7235`, KHÔNG đổi** | `bec7235` cả ba | ✅ |
| 8 | nhãn băm trong ảnh | **`b8e7c5397457`, KHÔNG đổi** ⟹ **lệch× = 1·1·1** so cây | `b8e7c5397457` cả ba ⟹ lệch× 1·1·1 | ✅ |
| 9 | ca đỏ "kho rỗng" | **VẪN ĐỎ** — bản vá này không liên quan | vẫn đỏ, cùng dòng `:112` | ✅ |
| 10 | token tiêu | **0** — bất biến tất định, không lượt LLM nào | 0 tính tiền — **nhưng xem §7** | ⚠️ |

**10/10 dự báo trúng.** Lần thứ ba quy trình này chạy (trước đó 6/6 và 2/2).
⚠️ Dòng 10 trúng về **con số** nhưng tôi đã suýt làm nó sai — xem §7, đó là phần đáng đọc nhất.

🔴 **Dòng 8 là dòng dễ đọc nhầm nhất.** Sau khi tôi land, cây làm việc **cố ý lệch** khỏi ảnh
đang chạy, vì PO-agent đã ra lệnh **không dựng ảnh** cho tới khi tester land xong (`tests/` nằm
trong ảnh, dựng hai lần là hai lần rủi ro). **`lệch× = 1·1·1` ở giai đoạn này là ĐÚNG, không phải
sự cố.** Nó chỉ thành sự cố nếu còn lệch **sau** lần dựng chung.

## 4. Nếu khác thì nghi gì

| lệch | nghi |
|---|---|
| #1 băm **không** đổi | file chưa ghi thật (harness nuốt lỗi ghi) — `git diff --stat` trước khi tin bất cứ gì |
| #2 >1 file đổi | tôi sửa lan sang chỗ khác ngoài ý định, hoặc đụng việc dở của phiên khác trên **cây dùng chung** |
| #4 `check_contracts` bẩn | tôi đã chạm `contracts/` mà không nhận ra ⟹ **DỪNG**, đi đủ §10, không tự chữa |
| #5 ≠ 23 passed | 🔴 nghi **nặng nhất**. INV gọi thẳng `build_customer_tools()`; đổi chữ ký/hành vi tool là đổi thứ INV soi. Đọc **ca nào** đổi, đừng đọc màu |
| #5 xanh nhưng **số ca < 23** | `skip` và `pass` cùng màu trên bảng tổng (STATE §9) — đọc bằng **số ca chạy** |
| #6 ≠ 0 | tôi đã ghi vào container đang chạy — **Luật I**, hoàn nguyên rồi mới báo bất cứ số nào |
| #9 chuyển **XANH** | 🔴 **Luật J**. Bản vá của tôi không có đường nào chạm kho RAG. Nó xanh ⟹ có người khác vừa đổi thứ khác, **không phải** ⟹ tôi vá được nó |
| #10 ≠ 0 | có lượt LLM thật chạy ⟹ tìm xem lớp giữ hoá đơn nào thủng (STATE §3 đang là **HAI** lớp, không phải ba — cờ `.DANG-DONG-BANG-LLM` đang mất) |

## 5. Cách nghiệm thu — và vì sao đường xanh KHÔNG đủ

Luật A: cổng phải **IM** lúc bình thường **VÀ KÊU** lúc bất thường; nửa sau **chỉ chứng minh được
bằng ca đối chứng**. Nên nghiệm thu cần **cả hai** chiều:

```
KÊU    hai lời gọi giống hệt + cùng lỗi  ⟹  lời thứ hai trả CHỈ THỊ DỪNG, khác lời thứ nhất
IM     cùng tool, THAM SỐ KHÁC           ⟹  không bắn (vòng lặp tra cứu hợp lệ, 5 bước, đã đo)
IM     cùng tool, cùng tham số, THÀNH CÔNG ⟹ không bắn (không phải lỗi thì không đếm)
IM     lượt KHÁC                          ⟹ không bắn (sổ đếm chết theo lượt, không rò sang lượt sau)
```

Ba dòng `IM` quan trọng ngang dòng `KÊU`: một bất biến bắn cả vào vòng lặp hợp lệ sẽ bị gỡ trong
vòng một tuần, và lúc đó ta mất luôn dòng `KÊU`.

`tests/` là vùng **tester**. Tôi **không viết test**. ~~Tôi soạn nội dung bốn ca trên để họ dán.~~

> 🔴 **ĐÍNH CHÍNH sau khi công bố (giữ nguyên câu gạch trên, không xoá dấu vết):** PO-agent **bác**
> việc tôi soạn sẵn nội dung test, và bác **đúng**. Lý lẽ của họ sắc hơn lý lẽ của tôi: tôi vừa đọc
> `src/rag/store.py` nên nếu tôi soạn, tester sẽ dán một test **gõ cứng tên collection lấy từ
> `src/`** — vẫn là test chép từ code, vẫn chết lần sau khi đổi model nhúng. Đó **chính xác** là
> thứ tường §11 dựng ra để chặn, và tôi suýt trèo qua nó bằng cửa "giúp cho nhanh".
> ⟹ Tester **tự liệt kê** collection từ container đang chạy (quan sát hộp đen, họ được phép) và
> cho ra test **không gõ cứng tên nào cả** — tốt hơn thứ tôi định soạn. Tôi chỉ chuyển **kết luận
> và lý lẽ**, qua PO-agent, không chuyển nội dung.

---

## 6. NGHIỆM THU — chạy trên SEAM THẬT, không chỉ trên bản sao

Vòng đầu tôi kiểm bằng một **bản sao** của `_locked` (15/15 đạt). Bản sao có thể lệch khỏi vật
thật, nên nó **không đủ**. Vòng hai gọi thẳng `build_customer_tools(None, user_id=…,
otp_verified_at=None, guard=…)` — dựng **đúng 5 tool sản phẩm**, và `otp_verified_at=None` đưa
lời gọi vào **đúng đường livelock đã đo** (cổng OTP `return` trước khi chạm DB, nên `session=None`
là an toàn và có chủ đích).

```
KÊU  lookup_transaction(TXN-0001) ×3   lần 1 lỗi OTP · lần 2+3 → chỉ thị DỪNG      ✅
KÊU  get_customer_history(days=30) ×2  tool thứ hai được bảo vệ ĐỘC LẬP             ✅
KÊU  kwargs đảo thứ tự                 `{a,b}` và `{b,a}` vẫn khớp cùng một khoá    ✅
IM   tham số KHÁC (TXN-0002)           không chặn oan dù TXN-0001 đang trong sổ     ✅
IM   THÀNH CÔNG lặp 4 lần              chạy đủ 4, không vào sổ                      ✅
IM   `not_found` lặp 3 lần             ranh giới cố ý — không tính là lỗi           ✅
IM   TOOL KHÁC cùng tham số            không gộp 5 tool làm một                     ✅
IM   LƯỢT MỚI (`TurnGuard` mới)        lời gọi ĐẦU không bị chặn oan                ✅
```

Bốn dòng `IM` quan trọng ngang bốn dòng `KÊU`: một bất biến bắn cả vào vòng lặp hợp lệ sẽ bị gỡ
trong một tuần, và lúc đó mất luôn dòng `KÊU`.

**Hồi quy**, 7 file test chạm tầng tool (`test_customer_tools` · `test_audit_trail_completeness` ·
`test_request_human_handoff` · `test_otp` · `test_tools_rest_parity` · `test_fault_tolerance` ·
`test_pii_khong_ro_ri_len_llm`):

```
lần 1   49 passed · 1 FAILED  ← test_run_agent_turn_times_out_gracefully_instead_of_hanging
lần 2   50 passed
lần 3   50 passed
lần 4   50 passed
```
🔴 **Ghi lại ca đỏ đó thay vì im lặng chạy lại tới lúc xanh.** Cùng mã, cùng lệnh, 1 đỏ / 4 lần.
Chạy riêng một mình: xanh. Trên mã CŨ trong container: xanh. ⟹ **ca NHIỄU, không phải hồi quy** —
nó là test canh `timeout`, nhạy tải máy, và lô 7 file làm máy nặng hơn. Nhưng *"nhiễu"* ở đây là
**kết luận của tôi từ 4 lần chạy**, không phải một điều đã chứng minh; `tests/` là vùng tester và
họ nên biết có một ca đỏ-ngẫu-nhiên ở đó.

## 7. 🔴 SUÝT SAI — một lời gọi mạng THẬT ngoài ý định, tôi tự khai

Lúc dựng ca nghiệm thu tôi chọn `search_policy` làm "tool khác" để kiểm việc không-gộp-5-tool.
`search_policy` **không có cổng OTP** (khác 4 tool kia), nên nó chạy thẳng xuống
`store.search()` → `embed_query()` → **gọi thật ra OpenAI**. Chặn lại bởi `OPENAI_API_KEY=gia`
⟹ `401`, **0 token, 0 đồng**. Nhưng nếu biến môi trường đó là khoá thật thì đây là một lượt nhúng
tính tiền **ngoài hạn mức A3**.

**Bài học không phải "tôi bất cẩn" mà là một lỗ có thật trong ba lớp giữ hoá đơn:**
```
lớp ①  FIN05_ALLOW_PAID_CALLS   là `skipif` NẰM TRONG FILE TEST
lớp ②  .DANG-DONG-BANG-LLM       PO thật quyết 18/08: bỏ hẳn — video demo quay xong
lớp ③  TRIAGE_ENABLED            chỉ định tuyến lượt CHAT
```
Cả ba **không lớp nào chặn một script gọi thẳng tool**. Lớp ① sống trong `tests/`; script nháp
không đi qua `tests/`. Sau quyết định 18/08 thì lớp ② đã mất, nên đây **không còn là hai lớp mà là
một lớp, và lớp đó không phủ đường tôi vừa đi**.
⟹ **Đề xuất (không tự làm, thuộc `src/` nhưng cần PO-agent xếp):** chốt chặn phải nằm ở **tầng
client nhà cung cấp** (`_khoa_cho_nha_cung_cap()` — nơi MỌI đường ra ngoài đi qua), không nằm ở
`tests/`. Một cờ ở đó phủ cả test, cả script nháp, cả lượt chat. Đây cũng chính là chỗ
`so_luot_da_phat` (sổ nợ §5.B) cần cắm — **một chỗ, hai việc**.

⚠️ Và ghi cho người sau: **`search_policy` là tool DUY NHẤT trong 5 tool không có cổng OTP.**
Tôi **không** kết luận đó là lỗi — tra chính sách là tài liệu công khai, không phải dữ liệu khách,
nên nhiều khả năng là cố ý. Nhưng nó có nghĩa: **`search_policy` là tool duy nhất mà một lời gọi
của model chạm được ra Internet khi khách CHƯA xác thực gì cả.** Ai rà thẩm quyền nên biết.

## 8. Còn lại — KHÔNG làm trong đợt này

- nửa **(b)** *"nói gì với khách"* — 12 ca mẫu đã có, việc riêng.
- **dựng ảnh** — PO-agent điều phối, dựng MỘT LẦN sau khi tester land (`tests/` nằm trong ảnh).
- **ca đối chứng trong `tests/`** — vùng tester. PO-agent đã bác việc tôi soạn sẵn nội dung, và
  bác đúng: test do người đã đọc `src/` soạn sẽ phản chiếu `src/`.

---

## 9. 🔴 ĐÍNH CHÍNH §7 (18/08, cùng ngày) — câu "tool DUY NHẤT" của tôi là SAI

**Ai gây:** tôi (tech-lead). **Ai bắt:** security, qua PO-agent — họ đang rút lại một [ĐO] khác thì
lời liệt kê đủ của họ **bác luôn câu của tôi**.

§7 trên viết: *"`search_policy` là tool **DUY NHẤT** trong 5 tool không có cổng OTP."* **Sai.**

**[ĐO] liệt kê ĐỦ, không cắt cửa sổ:**
```
791 @tool 792 @_locked  lookup_transaction       813+815 kiểm OTP
842 @tool 843 @_locked  get_customer_history     862+864 kiểm OTP
875 @tool 876 @_locked  create_ticket            904+906 kiểm OTP
921 @tool 922 @_locked  request_human_handoff      —    KHÔNG kiểm   ← tôi bỏ sót
949 @tool 950 @_locked  search_policy              —    KHÔNG kiểm
```
**Phát biểu đúng:** `search_policy` là **MỘT TRONG HAI** tool không kiểm OTP. Tool kia là
`request_human_handoff`. (Và 5/5 tool **đều** mang `@_locked` ⟹ bất biến chống livelock phủ **cả
năm**, không tool nào lọt — điều này thì đúng như đã báo.)

**Cơ chế sinh lỗi của tôi, khai thẳng vì nó tái diễn được:** tôi kiểm 3 tool đầu, thấy cả 3 có cổng
OTP, gặp `search_policy` không có → viết *"khác 4 tool kia"*. **Tôi chưa bao giờ mở
`request_human_handoff` ra xem.** Con số `4` là **suy ra từ `5 − 1`**, không phải đếm.
⟹ **Luật F bắt được miễn phí:** câu của tôi nói "4 tool" mà **không kèm 4 số dòng nào**. Một con số
không có mẫu số đi kèm — và lần này mẫu số ấy không tồn tại vì tôi chưa đếm.

**Điều làm ca này đáng ghi:** PO-agent mắc **đúng lớp lỗi** trong cùng một tin (`head -40` cắt ở
dòng 949, câu trả lời ở 950), và đó là **lần thứ hai trong ngày** của họ (ca ADR-031: `grep` trúng
143, câu trả lời ở 150). Ba ca, hai người, một hình dạng: **đọc một khung nhìn do chính mình cắt ra
rồi dùng nó như toàn cảnh.** Của họ là cửa sổ `head`; **của tôi là một phép trừ.**

**Hệ quả — finding vẫn còn nhưng ĐỔI HÌNH:** vấn đề không phải *"thiếu một cổng"* mà
*"một MIỄN TRỪ không phân biệt được với một CHỖ BỎ SÓT"* — trên mã hai thứ trông y hệt.
`request_human_handoff` **có khai** miễn trừ trong docstring; `search_policy` **không một chữ**.
⟹ Việc đúng là **hai dòng chữ, không phải một cổng** (thêm OTP cho `search_policy` sẽ chặn đúng ca
dùng hợp lệ — *"phí rút tiền bao nhiêu"* — để đổi lấy rủi ro security đã tự hạ hai bậc, vì
`main.py:610` có sẵn `@limiter.limit("20/minute")` + `RedisConcurrencyLimiter`). Đã land: miễn trừ
viết vào docstring `search_policy` theo đúng khuôn `request_human_handoff`, nêu **cả hai trục**
(không chạm dữ liệu khách · có đường ra ngoài tính tiền qua `embed_query`).
