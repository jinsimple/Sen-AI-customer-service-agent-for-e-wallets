# Hồ sơ họ lỗi **KHAI ≠ CHẠY** — năm cơ chế tìm được trong MỘT ngày

> Vai: **security** · 2026-08-17 · PO-agent đề nghị: *"ba đường trong một ngày,
> ba cơ chế khác nhau, cùng một mệnh đề bị phá — đó là mục lớn nhất hồ sơ hôm
> nay, hơn cả từng finding riêng lẻ."* Đồng ý. Đây là bản gộp.
>
> Rà lại cả ngày thì **không phải ba — là NĂM.**

## §1. Mệnh đề bị phá

> **Thứ ta ĐÓNG DẤU không phải thứ ĐANG CHẠY.**

Cả bộ đo lường của dự án dựng trên mệnh đề ngược lại: `dau_thuoc()` băm
`src/**/*.py` + `commit`, rồi ta so hai lượt đo bằng cách so hai cái dấu. Nếu
hai lượt cùng dấu mà **kích thích hoặc mã khác nhau**, mọi so sánh giữa chúng
**vô nghĩa mà không có triệu chứng nào**.

## §2. Năm cơ chế — mỗi cái phá mệnh đề đó bằng một đường khác

| # | Cơ chế | Dấu vẫn khớp? | Phát hiện bằng | Đã gặp ở đâu |
|---|---|---|---|---|
| 1 | **`docker cp` vào container đang chạy** | ✅ `build_commit` không đổi | `docker diff` (bản siết) | `tests/conftest.py` · `src/agents/graph.py` |
| 2 | **Ảnh dựng từ CÂY LÀM VIỆC, không từ HEAD** | ✅ `BUILD_COMMIT=HEAD` vẫn đúng | so md5 `src/` ↔ `git show HEAD` | ảnh `faad6e8` dựng lúc cây còn 2 mục chưa commit |
| 3 | **Phiên bản thư viện phụ thuộc đổi** | ✅ commit **và** `he_thong` **đều** trùng khít | băm **payload đã gửi**, không băm nguồn | `langchain-core` 1.5.3↔1.5.4 đổi `description` ~12% |
| 4 | **Prompt chứa thời gian thực** | ✅ mọi dấu trùng | ghi **mốc thời gian** cạnh dấu | `build_system_prompt(current_time=…)` |
| 5 | **Bộ đo tự soạn lại kích thích** | — (không ai đóng dấu) | so **từng trường** với app sống | bộ đo v4: system 123 ký tự · lược đồ thừa 399 ký tự |

**Hai cái đáng sợ nhất là #3 và #4** — chúng **không cần thao tác Docker nào**,
không ai làm gì sai, và **mọi cái dấu ta đang có đều trùng khít**.

### Vì sao chúng ẩn được lâu — chẩn đoán của PO-agent, ratify

> **Bán kính của tác nhân không trùng vật đang đo** ⟹ **người gây ra không thấy
> hậu quả, người chịu hậu quả không thấy nguyên nhân.**

Đúng cho cả năm: người `docker cp` không chạy phép đo; người nâng thư viện
không đọc prompt; người soạn bộ đo không đọc mô tả tool của app.

## §3. Bản vá đúng cho CẢ HỌ — một câu

> **Băm THỨ ĐÃ GỬI / ĐANG CHẠY, đừng băm THỨ SINH RA NÓ.**

- băm **payload trọn vẹn** gửi cho model — bắt được #3, #4, #5; băm `src/`
  **không bao giờ** bắt được;
- băm **nội dung trong container** (`md5 src/**/*.py`) — bắt được #1, #2; nhãn
  `build_commit` **không bao giờ** bắt được;
- băm phải **sinh trong chính container sẽ chạy lượt đo**, nếu không nó băm một
  payload chưa ai từng gửi.

*(Tester đi tới cùng kết luận này độc lập, từ quy tắc chung "băm thứ thực sự lên
dây" — họ khai rõ **không** vì lường trước trôi-do-thư-viện. Ghi đúng công: quy
tắc tốt che được cả rủi ro người đặt ra nó chưa nhìn thấy.)*

## §4. Quy trình kiểm — thứ tự có lý do

```
① docker diff <c> | grep -E "^C /app/src.*\.py$" | grep -v __pycache__
      → CÓ LỆCH KHÔNG          (bản thô đếm cả thư mục __pycache__ ⟹ NHIỄU)
② so md5 src/**/*.py  container ↔ cây làm việc
      → LỆCH VỀ PHÍA NÀO       (chỉ phép này trả lời "recreate có phá gì không")
③ rồi mới recreate / dựng lại ảnh
④ sau khi dựng: lặp ① ② trên TỪNG container, không suy từ một cái
```

⚠️ **`docker restart` KHÔNG dọn dấu `docker cp`.** `docker cp` ghi vào **lớp
writable**; lớp đó sống qua `restart`, chỉ chết khi **rm/recreate**. *(Tôi phát
biểu sai điều này hôm nay và tech-lead sửa bằng số đo. Cái sai nghiêng về hướng
**nguy hiểm hơn** — nó khiến người ta tưởng một `restart` là đủ.)*

## §5. Hai luật rút ra, và chỗ cả hai dễ bị đọc thiếu một nửa

### Luật A — *"Một cổng phải IM lúc bình thường, nếu không nó không phải cổng."*

Từ ca `docker diff` bản thô: nó bắn ở **mọi** lần chạy (Python ghi
`__pycache__`) ⟹ ai đó sẽ học cách bỏ qua ⟹ **một `docker cp` thật lọt qua đúng
cái còi dựng ra để bắt nó**. Cổng đỏ liên tục bị vô hiệu hoá **bằng thói quen,
không bằng quyết định**.

🔴 **Nửa còn lại, bắt buộc đi kèm:** *"im lúc bình thường"* một mình là **tiêu
chí của một cổng CHẾT**. Một cổng không bao giờ kêu cũng im lúc bình thường.

> **Cổng phải IM lúc bình thường VÀ KÊU THẬT lúc bất thường — và vế thứ hai chỉ
> chứng minh được bằng CA ĐỐI CHỨNG.**

Hôm nay có hai ví dụ sạch cho vế hai: `ĐC-A` của tech-lead (`ValueError` **phải
ném ra**, chặn bản vá "bắt tất cả thành mềm" mà vẫn 10/10) và ca đối chứng của
tôi ở phép thử dấu-duy-nhất (gửi dấu tới chính `localhost` cũng ra 0 ⟹ phép thử
**mù**). Không có vế hai, cả hai cổng đó đều "xanh".

### Luật B — *"Làm tròn một phát biểu lên đúng MỘT nấc."*

Lỗi đắt nhất hôm nay đều có hình dạng đó, không phải hình dạng sai hẳn:

| Phát biểu đúng | Bị làm tròn thành |
|---|---|
| *"không nghi can nào trong `src/`"* | *"có người xoá tay"* |
| *"bản vá đã land"* | *"bước 1 xong, xoay khoá được rồi"* |
| *"lệnh cấm bịa chiếm 1/3 prompt bộ đo"* | *"phép thử khắc nghiệt hơn"* |
| *"v4 không đo được hành vi sản phẩm"* | *(suýt)* *"sản phẩm đang sai"* |

PO-agent tự nhận luật này áp cho họ nhiều nhất vì họ là **nấc cuối trước khi
một phát biểu thành quyết định**. Đúng — và tôi ở nấc ngay trước đó, nên nó áp
cho tôi gần bằng.

## §6. Cách duy nhất đã BẮT được cả năm cơ chế — không phải tự kiểm

**Không cơ chế nào trong năm cái bị bắt bởi một người tự soi lại việc của
mình.** Cả năm đều bị bắt bởi **hai người đo cùng một vật rồi so SỐ** — tám lần
trong ngày, và **tám lần chỗ khác nhau là chỗ có thông tin**.

🔴 **Vế thi hành, chỗ dễ trượt nhất: so SỐ, không so KẾT LUẬN.** Tôi suýt đóng
vụ `4.862 vs 4.334` bằng câu hoà *"hai cách đếm khác nhau thôi"* — một phát biểu
ở tầng **kết luận**, nghe hợp lý, **hai bên cùng yên**, và nó **đã che mất** cơ
chế #3. Thứ cứu được là tester **từ chối cách hoà đó**.

⟹ Một quy ước *"hai người cùng đo"* mà thiếu vế *"cấm hoà ở tầng kết luận"* sẽ
**tự vô hiệu ngay lần đầu hai người lịch sự với nhau**.

## §7. Nợ còn mở, xếp theo mức

| | Việc | Ai |
|---|---|---|
| 🔴 | `HOTLINE_CSKH` chưa đặt trên cả 3 container ⟹ lối thoát cho khách mới là câu chữ | PO thật |
| 🔴 | Ngăn xếp nào phục vụ `app.adaptivealgo.uk` — mọi phép đo rẻ ở máy này hoặc **vắng mặt**, hoặc **mù** | PO thật |
| 🔴 | Hồ sơ ĐGTĐ chuyển dữ liệu ra nước ngoài (NĐ 13/2023 Đ.25) — **hỏi lần thứ hai, chưa ai trả lời** | PO thật |
| 🟡 | Ghim phiên bản + lockfile (`langchain>=0.3.0` để ngỏ đúng thứ đổi được prompt) | tech-lead |
| 🟡 | Tắt `docs_url`/`redoc_url`/`openapi_url` khi `APP_ENV=production` | tech-lead |
| 🟡 | Dựng ảnh từ cây **sạch** hoặc `git archive HEAD` (cơ chế #2) | tech-lead |
| 🟡 | Thêm **mốc thời gian prompt** vào `dau_thuoc()` (cơ chế #4) | tech-lead |
| 🟢 | Đếm vé `scope='internal_wallet'` ∧ `complaint_type='other'` ∧ `trans_id IS NULL` — **chờ câu hỏi ngăn xếp** | security, sau khi PO trả lời |

---

## §8. Bổ sung sau khi kiểm lượt land `c01223a` — nhãn và mã lệch nhau theo **CẢ HAI CHIỀU**

Kiểm độc lập lời tech-lead, [ĐO]:

```
container            build      chuông thiếu_hotline   sửa-tay(.py, trừ __pycache__)
fin05-backend-1      c01223a          ×4                      0
fin05ttl-backend-1   36d6a1a          ×4                      0
fin05do-backend-1    c01223a          ×4                      0

git diff --name-only c01223a..HEAD -- src/   →  RỖNG
c01223a chạm đúng 1 tệp: src/api/main.py (+35)
36d6a1a LÀ HẬU DUỆ của c01223a, và nó chỉ đổi docs/
```

⟹ Ba ảnh **khác nhãn, cùng mã sản phẩm**. Xác nhận, không cần dựng lại.

### 🔴 Nhưng `fin05ttl-backend-1` đang mang nhãn `36d6a1a` — **một commit TÀI LIỆU của tôi**

Ảnh đó **không chứa gì** của `36d6a1a` (commit ấy chỉ thêm chính tài liệu bạn
đang đọc). Nhãn dịch **vì tôi commit docs**, không vì mã sản phẩm đổi. Người đọc
nhãn đó sáu tháng sau sẽ tra ra một commit **chẳng liên quan gì** tới thứ đang
chạy.

**Gộp với ca sáng nay, ta có đủ HAI CHIỀU:**

| Chiều | Ca | Cơ chế |
|---|---|---|
| **nhãn ĐỨNG YÊN, mã DỊCH** | `fin05-backend-1` khai `7450184` trong khi chạy `graph.py` đã sửa | `docker cp` (#1) |
| **nhãn DỊCH, mã ĐỨNG YÊN** | `fin05ttl-backend-1` khai `36d6a1a` = commit docs | HEAD dịch vì lý do **không liên quan tới mã** |

> **`commit` KHÔNG phải một hàm của `src/`, theo cả hai chiều.** Dùng nó làm nhãn
> của một ảnh là dùng sai loại định danh — nó định danh **trạng thái kho**, còn
> thứ ta cần định danh là **nội dung được đóng gói**.

### ⟹ Đề nghị của tech-lead là bản vá đúng, và **dự án đã có sẵn hàm để làm**

> **Nhãn ảnh nên là BĂM CỦA `src/`, không phải băm của commit.**

Ba lý do, và lý do thứ ba là lý do tôi không nghĩ tới cho tới lượt này:

1. **Bắt được cơ chế #1** — băm lại `src/` **trong container đang chạy** rồi so
   với nhãn; `docker cp` làm hai số lệch ngay.
2. **Bắt được cơ chế #2** — băm `src/` **đưa vào ảnh lúc dựng** rồi so với băm
   `src/` **tại HEAD**; dựng trên cây bẩn làm hai số lệch ngay. Cơ chế #2 hôm
   nay **không có phép kiểm nào**; cách này cho nó một phép kiểm miễn phí.
3. **Nhãn thôi dịch vì lý do không liên quan** — docs, ADR, hồ sơ security
   commit bao nhiêu lần cũng **không** làm nhãn ảnh nhúc nhích. Nhãn chỉ đổi khi
   **thứ nó định danh** đổi.

**Và không phải viết hàm mới:** `eval/measure_quality.py::dau_thuoc()` đã băm
`src/**/*.py` cho trường `he_thong`. Bản vá là **dùng lại đúng hàm đó làm nhãn
ảnh** — cùng một định nghĩa cho *"mã sản phẩm nào"* ở **cả** tầng đo lường lẫn
tầng đóng gói, thay vì hai định nghĩa lệch nhau như hôm nay.

## §9. Một cơ chế THỨ SÁU, tech-lead tự bắt — ở tầng khác

> **`>/dev/null` nuốt một lệnh KHÔNG CHẠY, và trạng thái cũ bị đọc thành kết quả mới.**

Vòng lặp shell của họ làm hỏng tham số `-f`, `docker compose` **không chạy**,
nhưng output đã bị chuyển hết ra `/dev/null` nên chỉ còn bảng kết quả — nhãn
vẫn `faad6e8`, chuông ×0. Họ **suýt đọc thành *"bản vá không hoạt động"***.

Không phải **khai-vs-chạy** mà **lệnh-không-chạy-vs-tưởng-đã-chạy** — nhưng cùng
mệnh đề bị phá: *thứ được báo cáo không phải thứ đã xảy ra.*

🔴 **Thứ cứu được là một cột họ in ra vì lý do hoàn toàn khác** (`sửa-tay=1`).

> **Trong một bảng đo, trường DƯ THỪA là thứ bắt được ca "phép đo không hề chạy".**
> Một bảng chỉ chứa đúng thứ ta muốn biết thì **không phân biệt được** *"kết quả
> là X"* với *"lệnh không chạy nên bảng còn giá trị cũ"*.

Đó cũng là lý do quy trình §4 đòi **lặp ① ② trên TỪNG container** thay vì tin
một dòng tổng: giá trị giống nhau ở nhiều nguồn độc lập là thứ phát hiện được
sự im lặng.

## §10. Hai con số bị rút trong ngày — ghi để không ai trích lại

| Con số | Người báo | Trạng thái |
|---|---|---|
| *"23 · 20 · 9 file bị sửa tay"* | tech-lead | 🔴 **RÚT** — đếm cả thư mục + `__pycache__`. Không tái dựng được (lớp writable đã mất khi recreate). Kết luận **không đổi**: phép so md5 độc lập cho `0 · 3 · 2` và **không dính nhiễu này** |
| *"tổng mô tả tool 4.334 ký tự"* | security (tôi) | 🔴 **RÚT** — đo trên venv mượn (`langchain-core` 1.5.3), số đúng là **4.862** (1.5.4, trong container) |

Cả hai đều là **cùng một lỗi ở hai người**: đọc một con số mà **không hỏi nó
đếm cái gì, ở đâu**. Và cả hai đều chỉ lộ ra khi **người thứ hai đo lại**.
