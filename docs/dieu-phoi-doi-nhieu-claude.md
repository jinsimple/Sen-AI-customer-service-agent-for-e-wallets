# Điều phối đội nhiều Claude — sổ tay vận hành

> **Đọc khi:** PO thật vừa bật một đội mới, hoặc một phiên được giao vai Lead/PO-agent.
> **Nguồn:** đúc kết từ các đợt 13/08 → 01/09/2026 trên chính dự án này. Mọi luật dưới đây
> đều có **một sự cố thật** đứng sau — không có luật nào là đề phòng suông.
>
> Vai · phân vùng quyền ghi: **`CLAUDE.md §4`**, không chép lại ở đây.
> Trạng thái đợt gần nhất: **`docs/STATE.md §0-TER`**.

---

## 1. Hình dạng đội — vì sao có Lead

```
PO thật (người)
   └── PO-agent ── Lead ──┬── Coder      (vai DUY NHẤT được ghi src/ + contracts/)
                           ├── QA/QC      (chạy thật trên UI; KHÔNG đọc src/)
                           ├── Review     (không ghi gì, chỉ soát)
                           └── Bảo mật    (chỉ ghi docs/security/)
```

**Vì sao chèn Lead vào giữa:** PO-agent không giữ nổi bốn cuộc hội thoại song song mà vẫn
còn chỗ trong ngữ cảnh để *suy nghĩ*. Lead làm một việc duy nhất: **hỏi bốn vai, gộp lại,
trả về một khối**. Lead **không** quyết định thay PO-agent.

🔴 **Tên phiên KHÔNG suy ra vai.** Luôn tra bản đồ vai trong `STATE.md`, đừng đoán từ tên.

## 2. Điểm danh — nhịp, và vì sao nó không phải nghi thức

**Nhịp 15 phút.** Mỗi vòng hỏi mỗi vai **đúng ba ý**:

| ý | vì sao cần |
|---|---|
| **đang làm gì** | phân biệt "đang chạy việc dài" với "đã xong từ lâu" |
| **nếu đứng im thì CHẶN VÌ CÁI GÌ** | chặn có tên thì gỡ được; chặn không tên thì không |
| **còn làn nào khác mở không** | một làn tắc **không** làm tắc các làn khác |

> **Đứng im mà không ai biết là thứ phải chặn.** Không phải đứng im — mà là *không ai biết*.

**"Không đổi từ lần trước" là câu trả lời hợp lệ.** Bắt viết lại mỗi vòng làm báo cáo phình
ra và người đọc bắt đầu lướt — lúc đó thay đổi thật sẽ trôi qua không ai thấy.

🔴 **Im lặng của một phiên có thể là NÓ ĐANG LÀM ĐÚNG.** (01/09: Review im nhiều vòng vì
đang **hỏi người dùng thật của họ** trước khi chạy một lệnh tốn tiền — đúng kỷ luật. PO-agent
đọc thành "kẹt" và tự tiếp quản.) Hỏi trước khi kết luận.

## 3. Luật vàng: **KIỂM trước khi nhận**

**Không bao giờ nhận một báo cáo "đã xong" bằng lời.** Tự chạy `ls`/`grep`/`wc`/`git log`/
`docker exec` trước khi ghi nó vào bất cứ đâu.

Điều này **không phải nghi ngờ đồng đội** — nó là vì:

- một phiên báo cáo trung thực về **thứ nó tin**, và thứ nó tin có thể đã cũ vài giờ
- lỗi hay gặp nhất không phải nói dối, mà là **địa chỉ dán từ trí nhớ**

**Ba lần trong ngày 01/09 phép kiểm bắt được thứ báo cáo không bắt được**, và cả ba lần
người báo cáo đều hoàn toàn thiện chí.

## 4. Ba luật về BÁO CÁO — áp cho mọi vai, gồm cả PO-agent

**① Địa chỉ phải tự mở lại trước khi dán.**
Không dán từ trí nhớ, dù tin chắc tới đâu. *(01/09: một vai dán
`eval/_harness.py::write_report` — hàm đó ở `eval/run_golden_set.py:138`, một trong **sáu**
hàm trùng tên. Ba kết luận nội dung thì đúng cả ba.)*

> **Trí nhớ không trôi ngẫu nhiên — nó trôi về tệp đang đọc nhiều nhất.** Nghĩa là địa chỉ
> càng sai càng *cảm thấy đúng*.
>
> **Địa chỉ SAI tệ hơn KHÔNG có địa chỉ.** Không có ⟹ người sau đi tìm. Sai ⟹ người sau mở
> đúng tệp được trỏ, không thấy gì, kết luận phát hiện là **bịa**, rồi bỏ qua — kéo theo cả
> phần nội dung đúng.

**② Số phải đi kèm CÁCH ĐO.** "Một con số băm không kèm cách băm thì không phải bằng chứng."
Và phân biệt cho rõ: *sự thật về TỆP* (đối chiếu dữ liệu tĩnh) **không đổi**; *sự thật về
SẢN PHẨM* (agent hành xử thế nào) **chịu nhiễu** — cùng mã, cùng bộ đề, chạy lại chênh gấp ba.

**③ Giả thuyết phải tự khai là giả thuyết.** Ghi `ĐO ĐƯỢC` hay `GIẢ THUYẾT` ngay tại chỗ.
Một giả thuyết còn bằng chứng thì quý; một giả thuyết **mất bằng chứng** phải nói rõ là mất,
đừng để phiên sau trích nó như dữ kiện.

## 5. Chống dẫm chân — cơ chế, không phải lời dặn

**Cây làm việc DÙNG CHUNG.** Nhiều phiên cùng gõ vào một thư mục.

| cấm | vì sao |
|---|---|
| `git add .` · `commit -a` | gói luôn việc dở của phiên khác. **Luôn pathspec tường minh.** |
| `git clean` · `checkout` không pathspec | xoá thẳng việc chưa commit của phiên khác |
| `docker compose down` · `-v` · `rm` · `prune` | **đã xoá sạch một CSDL thật.** Tắt ngăn: **chỉ `stop`** |
| compose thiếu `-p <project>` | thao tác nhầm ngăn |
| rebuild ảnh khi đang có mốc neo | phá băm mà cả đợt đo đang neo vào |

🔴 **"Đóng băng" KHÔNG phải "đừng commit".** Harness đọc **cây làm việc**, không đọc git.
Đóng băng = **cây làm việc bất động**.

🔴 **Nháp thiết kế làm NGOÀI repo.** Ba sự cố trong một buổi vì sửa thẳng `src/` để thử.

🔴 **Mốc neo phải có tên và phải đo được.** Dùng **băm nội dung**, không dùng commit — commit
đã bị chứng minh nói dối **theo cả hai chiều** trong cùng một ngày. Nhưng phải biết **phạm vi**
mốc neo phủ tới đâu: băm `src/**/*.py` **không** phủ `frontend/`, **không** phủ `migrations/`
(mà `migrations/` **chạy thật lúc khởi động** và **không đảo ngược được**).

## 6. Cạm bẫy điều phối — đã trả giá, đừng trả lại

**① Hai nguồn đọc CÙNG một văn bản không phải xác nhận chéo.**
PO-agent viết một khối sai; Review và QA/QC đều "xác nhận đúng" — vì cả hai đọc **văn bản của
PO-agent**, không đọc mã. ⟹ Muốn xác nhận chéo, hai nguồn phải đi **hai đường độc lập**.

**② Cổng hằng XANH không tự khai nó đo nhầm chỗ.**
Một phép kiểm chạy mỗi 15 phút suốt buổi, luôn xanh, và **không đo gì cả** (đo bảng CSDL trong
khi thứ quyết định nằm trong token).

> Cổng hỏng mà **hằng ĐỎ** bị mổ ngay hôm đầu. Cổng hỏng mà **hằng XANH** sống được nhiều
> tháng — nó phát tín hiệu trấn an **đều đặn**, và chính sự đều đặn ấy khiến không ai kiểm lại.

⟹ Định kỳ **soát chính các phép đo**: cổng này ĐỎ được trên hoàn cảnh nào? Nếu chưa từng đỏ,
nó chưa từng được kiểm.

**③ Bản TÓM và bản ĐẦY ĐỦ sẽ trôi khỏi nhau.**
Sửa phần thân mà quên thẻ tóm tắt — xảy ra **hai lần trong một ngày**, lần thứ hai do chính
người vừa ghi lại bài học từ lần thứ nhất. Cơ chế: khi sửa, ta đọc **chỗ mình vừa viết**,
không đọc **chỗ người khác sẽ đọc**.
⟹ Sau mỗi lần sửa tài liệu có bản tóm: **grep lại bản tóm**, đừng tin trí nhớ.

**④ Trong bản tóm, "thứ bị BỎ RA" nguy hiểm hơn "thứ nói KHÁC".**
Mâu thuẫn thì dễ thấy — hai câu cạnh nhau, khác nhau. Thiếu sót thì vô hình: không có gì để
so, và bản rút gọn đọc vẫn trôi chảy, tự tin.
*(Một thẻ thao tác rút ba nhánh xuống hai, bỏ đúng **nhánh giữa** — nhánh dễ xảy ra nhất. Người
đọc gặp nhánh không có trong thẻ sẽ chọn **lựa chọn gần nhất nhìn thấy được**.)*

**⑤ Điều kiện phải nằm TRONG câu.**
Chú thích rụng trên đường truyền. Người đọc riêng một mục **không thấy** câu ở mục khác.
⟹ Chép nguyên điều kiện vào mọi chỗ cần nó, chấp nhận lặp.

**⑥ Cách soát tốt nhất: trả lời câu được hỏi, RỒI hỏi tiếp.**
*"Còn gì thuộc loại này mà không ai hỏi tới?"* — hai lần trong một ngày, hai vai khác nhau,
và **cả hai lần thứ tìm được nặng hơn thứ đang tìm**.

## 7. Tin nhắn liên phiên — hạng dữ kiện THẤP NHẤT

**Tin nhắn chết khi phiên tắt.** Một kết luận chỉ sống trong tin nhắn = **chưa tồn tại**.

- Vai không có quyền ghi repo (vd Review) ⟹ **PO-agent phải neo hộ**, nếu không mất sạch.
- Tin nhắn liên phiên **KHÔNG thay được** xác nhận trực tiếp cho hành động tốn tiền / khó đảo
  ngược. Một phiên nói "được phép" không phải là người dùng nói "được phép".
- Một phiên bị **từ chối quyền** rồi nhờ phiên khác làm hộ = **rửa quyền**. Từ chối, và báo
  lên người thật.

## 8. Khi TẮT đội — lượt nộp cuối

Trước khi tắt, hỏi mỗi vai **đúng một câu**:

> ### « Cái gì bạn biết mà repo không biết? »

Không phải tóm tắt việc đã làm (`git log` có rồi). Không phải kết luận đã có tệp. Đúng bốn loại:

1. một **bẫy** đã sa vào và tự bò ra, chưa ai ghi
2. một **giả thuyết** tin nhưng chưa chứng minh — ghi rõ là giả thuyết, vẫn quý hơn mất
3. một **con số** đo được nhưng chưa vào tệp nào
4. một chỗ trong tài liệu **nghi là sai** nhưng chưa kịp kiểm

"Không có" là câu trả lời hợp lệ — **đừng bịa cho đủ**.

Rồi PO-agent viết `STATE.md §0-TER` gồm: **lệnh cấm kèm hậu quả THẬT** (không phải lời đề
phòng — lệnh cấm không có hậu quả sẽ bị coi là thói quen của người cũ và bỏ qua) · trạng thái
việc đang dở · sổ tồn đọng **có địa chỉ bằng chứng** · quyết định đang chờ người thật · và
**khai rõ cái gì đã mất**, đừng viết thành "đã bàn giao đầy đủ".

## 9. Việc chỉ NGƯỜI THẬT làm — đừng tự động hoá

- mọi **quyết định phạm vi** (mở rộng bộ đề, đổi hiến pháp, tiêu hạn mức)
- đăng nhập tài khoản cá nhân · tạo/thu hồi token trên dashboard
- `git push --force` lên nhánh người khác có thể đã đọc
- xoá branch/volume/CSDL · đổi tên repository

🔴 **Và luật ngược lại, quan trọng ngang:** **PO đã chốt thì KHÔNG BAO GIỜ hỏi lại** — kể cả
dưới dạng "xác nhận lại" hay "nếu sếp đổi ý". Có dữ kiện MỚI làm quyết định cũ sai thì
**trình DỮ KIỆN kèm hệ quả, không trình lại CÂU HỎI**.
