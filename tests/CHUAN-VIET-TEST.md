# Chuẩn viết test — FIN-05

> Vai giữ file: **tester** · 15/08/2026.
> Bốn luật dưới đây được PO phê chuẩn thành **luật dự án**, rút ra từ lỗi THẬT
> gặp trong hai ngày 14–15/08, mỗi luật kèm đúng những ca đã làm nó lộ ra.
>
> **Vị trí file:** nội dung này thuộc về `docs/TESTING.md`, nhưng `docs/` là
> vùng ghi của vai `po` (hiến pháp §4). Tôi giữ bản gốc ở đây — vùng của
> tester — và đã gửi PO nguyên văn để dán sang. Không tự ghi vào vùng khác,
> kể cả khi được mời: ranh giới co giãn "một lần cho tiện" thì lần sau không
> còn là ranh giới.

## Vì sao bốn luật, không phải một

Một test chỉ có giá trị khi chứng minh được **cả năm** vế:

| | Câu hỏi | Thiếu nó thì |
|---|---|---|
| **Luật 1** | Ràng buộc có **HIỆU LỰC** không? | suite xanh trên một guardrail không tồn tại |
| **Luật 2** | Ràng buộc có **QUÁ RỘNG** không? | suite xanh trên một guardrail cấm cả người hợp lệ |
| **Luật 3** | Phép đo có **TÁI LẬP** được không? | kết luận rút từ một kịch bản không quay lại được |
| **Luật 4** | Thước và vật có **ĐỨNG YÊN** suốt lượt đo không? | cặp before/after lẫn nhiều biến, không quy được nhân quả |
| **Luật 5** | Bản ghi có đủ để **VAI KHÁC BÁC** kết luận không? | một bộ đo không ai kiểm chứng ngược được, kể cả khi nó sai |

Thiếu vế nào cũng cho ra một kết luận **trông như đo được mà không đo được gì**.
Đó là lý do năm luật này là một họ, không phải năm quy tắc rời: Luật 1 và 2
canh **cái thước**, Luật 3 và 4 canh **phép đo**, Luật 5 canh **cái sổ** —
thứ duy nhất còn lại sau khi lượt đo kết thúc.

### Luật 5 — bộ đo phải lưu đủ để người khác bác được nó

*(PO phê chuẩn 15/08/2026, sau hai lần vấp cùng một hình dạng trong một đêm.)*

Tiêu chuẩn **không phải** "lưu đủ để tôi tự tin vào kết luận của mình", mà
"lưu đủ để một vai khác dựng lại và **chứng minh tôi sai**".

Hai lần vấp làm nên luật này — cùng một hình dạng, khác nội dung:

1. Một ca TRƯỢT được ghi lại **không kèm traceback**. Biết là hỏng, không
   biết hỏng ở đâu ⇒ không ai phản biện được, kể cả tôi.
2. Mọi lượt được ghi lại **không kèm thời gian chạy**. Timeout và "agent từ
   chối" cho ra **cùng một câu fallback**, nên không có `elapsed` thì một
   vấn đề **hiệu năng** bị chẩn đoán thành vấn đề **hành vi** — và bản vá sẽ
   nhắm sai chỗ.

Vì sao đây là luật chứ không phải mẹo: nó là **bản đo-lường của chính kiến
trúc phân vai đối kháng của dự án**. Coder tự nghiệm thu là *cần nhưng
không đủ*; y hệt vậy, một bộ đo **tự đủ cho mình** là cần nhưng không đủ —
nó phải đủ cho **vai khác** phản biện. Một bộ đo chỉ thuyết phục được tác
giả của nó thì không khác gì một suite xanh chứng minh bug chạy đúng như
bug.

Cụ thể, mỗi bản ghi kết quả phải mang: `traceback` khi lỗi · thời gian từng
lượt · dấu thước (`cham_diem` + `he_thong`) · dữ liệu thô mà bất biến đã
đọc để ra phán quyết. **Nguyên tắc gốc: cái gì bộ chấm ĐỌC để phán quyết
thì bản ghi phải LƯU** — nếu không, phán quyết không chấm lại được, và một
phán quyết không chấm lại được thì không bác được.

---

## LUẬT 1 — Assertion không được trùng trạng thái MẶC ĐỊNH của hệ thống

Nếu điều bạn khẳng định vốn đã đúng khi tính năng **chưa tồn tại**, test đó
không kiểm gì cả. Nó vẫn xanh, vẫn có tên đẹp, vẫn nằm trong báo cáo — và cả
đội tưởng chỗ đó đã có người gác.

**Ba biến thể đã mắc thật, cùng một ngày:**

1. `assert status_code >= 400` khi request **chết sớm ở tầng trước** (cổng OTP)
   — không bao giờ chạm tới guard cần đo. *(SEC-B)*
2. `assert "0912345678" not in gia_tri` khi **cột chưa tồn tại** nên `gia_tri`
   là chuỗi rỗng. *(nhóm A của `note`)*
3. `assert status_code == 403` khi **403 cũng là mã của đường thất bại thông
   thường** ("mã sai"), không riêng đường cần đo ("đã khoá"). *(F-12)*

Và hai biến thể ở tầng khác, cùng bản chất:

4. **Gọi nhầm đường**: thử guard `gen_dataset` bằng `make data` — đường vốn
   luôn hợp lệ, nên kết quả xanh **không mang thông tin nào**. *(CI-8)*
5. **Đo nhầm vật**: chạy eval khi `src/` đang sửa dở, hoặc khi chạm trần TPM —
   con số ra được không đo agent. *(W1, ba lần trong một đêm)*

**Cách chữa:** assert vào một dữ kiện **chỉ đúng khi hành vi cần đo THẬT SỰ
xảy ra**. `locked_at` chuyển NULL → có giá trị. Cột phải tồn tại **và** có nội
dung trước khi kiểm nội dung đó. Request phải **sống qua tầng N-1** rồi mới
xét tầng N.

**Hệ quả bắt buộc:** thiếu dữ kiện thì **NÓI LÀ THIẾU**, không đoán bừa thành
kết luận. Đó là lý do có trạng thái thứ ba `KHÔNG ĐO ĐƯỢC` bên cạnh
`ĐẠT`/`TRƯỢT`, và lý do `so_lieu_dung_tham_chieu` từ chối chấm khi tool_calls
không còn kết quả.

### 1b — Cũng không được trùng ĐẦU RA CỦA TRẠNG THÁI HỎNG

*(PO phê chuẩn 15/08/2026.)*

Bản gốc canh *"điều này vốn đã đúng khi tính năng chưa tồn tại"*. Có một dạng
tinh vi hơn, cùng hậu quả: **assertion khớp với chính câu mà hệ thống phát ra
KHI HỎNG.**

Ca thật, bắt được khi soạn F-25 tầng (b) — trước khi tiêu một token nào:

```
ca F25B-05, bất biến `phai_dung_thong_tin_chunk`
    tu_khoa_chunk = ["an toàn", "nơi công cộng", "wifi"]
    câu an toàn của bộ lọc: "Để đảm bảo AN TOÀN thông tin cho bạn…"
```

Bất biến ĐẠT khi **bất kỳ** từ khoá nào khớp. Nên khi bộ lọc nuốt mất câu trả
lời và thay bằng câu an toàn, từ khoá `"an toàn"` vẫn khớp ⟹ ca **XANH đúng
lúc nó phải ĐỎ**. Cổng tự vô hiệu ở chính tình huống nó sinh ra để bắt.

**Vì sao dạng này khó thấy hơn bản gốc:** ở bản gốc, assertion đúng vì *chưa có
gì xảy ra*. Ở dạng này, assertion đúng vì *thứ sai đã xảy ra và tình cờ chứa
đúng chữ ta đang tìm*. Test vẫn chạy qua đủ mọi tầng, vẫn thấy một câu trả lời
thật, chỉ là câu trả lời sai.

**Cách chữa — đối chiếu, đừng nhớ:** liệt kê mọi **đầu ra của trạng thái hỏng**
mà hệ thống có thể phát ra (câu an toàn của bộ lọc · câu báo nội dung bất
thường · câu fallback bàn giao), rồi kiểm bằng máy rằng không dấu hiệu nào ta
đang tìm xuất hiện trong đó. Đã nướng thành test tại
`tests/test_data/test_f25_tang_b_cong_that.py::test_khong_tu_khoa_nao_trung_dau_ra_hong`
— ai thêm ca mới với dấu hiệu tự vô hiệu sẽ đỏ ngay, không cần ai nhớ luật này.

Đây là thể hiện của một nguyên tắc chung hơn: **biến bài học thành cơ chế, đừng
để nó thành lời nhắc.** Một lời nhắc chỉ hiệu lực khi người đọc đang tỉnh táo;
một phép kiểm chạy được thì hiệu lực cả lúc bận nhất.

---

## LUẬT 2 — Mọi ràng buộc mới phải có ít nhất MỘT ca chứng minh nó KHÔNG chặn nhầm

Nếu chỉ đo cái bị chặn, thì **bản vá chặt tay nhất luôn thắng theo số đo** —
kể cả khi nó cấm mất một nửa số người dùng hợp lệ.

**Bốn lần cùng một hình dạng trong một đợt** (đủ để thành luật, không phải
trùng hợp):

| Ràng buộc | Ca đối chứng | Nếu thiếu |
|---|---|---|
| **BR-12** maker-checker | bên NHẬN hợp pháp vẫn mở được hồ sơ | bản vá "chỉ cho bên GỬI" vẫn xanh — cấm mất một nửa khách có quyền khiếu nại thật |
| **Thước bất động** (`gen_dataset`) | `--eval-out <tạm>` vẫn chạy được | đường an toàn bị chặn → người ta đi đường `--cho-phep-ghi-de-thuoc` cho xong việc, tức lệnh cấm tự đẩy người dùng sang đúng hành vi nguy hiểm nó sinh ra để chặn |
| **Guardrail đa lượt** | nhóm **MT-Z** hội thoại lành | agent siết quá tay làm CẢ 14 ca đối kháng xanh hơn — bộ đo thưởng cho việc làm hỏng sản phẩm |
| **F-23** thoát mốc spotlighting | tên sạch không bị đụng · nội dung còn đọc được | "vá" bằng cách strip sạch ký tự lạ → 3 ca tấn công xanh mướt, CSKH mất tên người nhận |

**Nguyên tắc chung rút ra:** *đường an toàn phải là đường DỄ ĐI NHẤT*. Một
lệnh cấm khiến đường hợp lệ trở nên phiền hơn đường nguy hiểm sẽ tự bị vô hiệu
hoá bởi chính người dùng nó bảo vệ.

---

## Hai hệ luận về CHỌN LOẠI TEST

**a) Ràng buộc là bất biến CẤU TRÚC thì đo CẤU TRÚC, đừng đo phản ứng của
model.** F-23 kiểm chuỗi đã bọc chứ không hỏi LLM có bị dụ không — rẻ, tất
định, và bền hơn: một mô hình đời sau có thể ngoan hơn hoặc hư hơn, nhưng
**ranh giới bị thủng thì vẫn là thủng**.

**b) Sự HIỆN DIỆN không phải HIỆU LỰC.** `INV-07`/`INV-14`/`INV-15` đọc AST và
khẳng định CheckConstraint *có tồn tại* — một biểu thức viết sai (`OR` thành
`AND`, quên ngoặc) vẫn hiện diện đầy đủ và vẫn làm chúng xanh. Phải có test
ghi thẳng vào DB và **đòi `IntegrityError`** thì mới chứng minh nó chặn thật.
Ngược lại cũng đúng: chỉ có test hiệu lực mà thiếu vế hiện diện thì xoá
constraint đi, bộ ràng-buộc-cứng vẫn xanh.

---

## LUẬT 3 — Lượt LLM sinh để KHÁM PHÁ, lượt viết cứng để ĐIỀU TRA

Lượt do LLM sinh **không tái lập được**. Dùng nó để điều tra một hiện tượng
CỤ THỂ là quy sai nguyên nhân từ một kịch bản khác.

**Ca đã làm luật này lộ ra:** ca smoke đa-lượt có 1 lượt viết sẵn + 2 lượt do
kẻ-tấn-công-ảo sinh. Lượt 3 lần đầu là câu **chính sách**, sinh ra một quan sát
đáng ngờ (agent từ chối cả việc hợp lệ). Chạy lại để điều tra thì lượt 3 thành
câu **khác hẳn** — hiện tượng cần soi không xuất hiện lại, và mọi kết luận rút
từ lượt đó sẽ là kết luận về một kịch bản khác.

| Mục đích | Loại lượt | Vì sao |
|---|---|---|
| **Khám phá** đường tấn công chưa ai nghĩ ra | LLM sinh, phản ứng theo agent | biến thiên là TÍNH NĂNG |
| **Điều tra** một hiện tượng cụ thể | viết cứng | biến thiên là thứ phá phép đo |
| **Đo đi đo lại** (gate, so trước/sau) | viết cứng | hệ luận trực tiếp của nhiễu nền 20/40 |

**Kèm theo:** một ca ĐO không phải một ca KẾT LUẬN. Hiện tượng thấy MỘT lần là
**quan sát**, không phải finding. Chỉ khi nó **tái lập ổn định qua k lần** mới
được gọi là lỗi — cùng lý do quy tắc đọc nhiễu dùng GIAO của k lượt thay vì
ngưỡng số đếm.

---

## LUẬT 4 — Ghim cả THƯỚC lẫn VẬT, và ghim ở CẢ HAI ĐẦU lượt đo

Một phép đo có **hai** thứ có thể trôi:

| | Là gì | Ghim bằng |
|---|---|---|
| **THƯỚC** | logic chấm + bộ case | `cham_diem` = băm `_harness.py` + `golden_set.jsonl` |
| **VẬT** | hệ thống đang bị đo | `he_thong` = băm **cây làm việc** `src/**/*.py` |

Ghim một nửa thì nửa kia trôi **trong im lặng** — nguy hiểm hơn sai số, vì nó
không để lại dấu nào để nghi ngờ.

**Băm CÂY LÀM VIỆC, không băm HEAD.** Bộ eval nạp code từ đĩa, nên một file
`src/` **sửa chưa commit** đã sống rồi, y hệt như đã commit. Ghim theo HEAD sẽ
mù trước đúng trạng thái nguy hiểm nhất: thứ chỉ tồn tại trên máy một người.
Hệ quả cho giao ước giữa các vai: câu đúng là **"đừng ĐỤNG `src/`"**, không
phải "đừng commit `src/`" — diễn đạt sau không bảo vệ gì cả.

**Ghim ở CẢ HAI ĐẦU.** Đóng dấu một lần chỉ chứng minh trạng thái *lúc bắt
đầu*. Đo dấu trước và sau, **phải bằng nhau**; khác ⇒ lượt chạy đã straddle
một thay đổi ⇒ **kết quả vô hiệu, chạy lại**. "Giữa chừng" mới là chỗ mọi sự
cố xảy ra: bộ W1 bị chẻ đôi bởi một commit rơi vào giữa hai nửa, cách nhau
**đúng 38 giây**.

**Khi dấu lệch mà `git status` sạch — NGHI CÔNG CỤ CỦA MÌNH TRƯỚC.** Thứ tự
đúng: kiểm bộ đóng dấu có tất định không (chạy k lần, so) → nếu tất định thì
mới kết luận là vật đã đổi. Kết luận ngay "hệ thống đổi" mà chưa tự kiểm thì
có thể đang báo động nhầm một non-determinism của chính mình. **Kiểm nhạc cụ
trước khi kiểm vật.**

*(Ca thật: dấu đổi trong khi `git status src/` sạch. Kiểm 3 lần → tất định →
kết luận là trạng thái nhất thời. Coder xác nhận sau đó: đúng 2 file sửa dở
chưa commit. Dấu bắt được thứ `git status` không thấy.)*

### 4b — ĐÓNG DẤU **MỌI** PHÉP ĐO, KỂ CẢ PHÉP ĐO RẺ

*(PO phê chuẩn 15/08/2026, sau lần thứ ba vấp cùng một hình dạng trong một ngày.)*

Ba lần, cùng một lỗi mặc áo khác nhau:

| lần | ghim cái gì | quên cái gì |
|---|---|---|
| 1 | đóng băng `src/` | quên `eval/` — bộ chấm cũng là một nửa dấu thước |
| 2 | đóng dấu lượt end-to-end | quên lượt đo **offline** |
| 3 | dấu ở lượt **dài** | quên lượt **ngắn** |

**Phép đo rẻ là phép hay chạy nhất, nên cũng là phép hay straddle một thay đổi
nhất.** Trực giác ngược lại — "chỉ chạy 3 giây, ai kịp sửa gì" — chính là thứ
làm ta bỏ dấu ở đúng chỗ dễ hỏng nhất.

Giá của lần thứ ba: phép đo offline không dấu cho 27/96 → 5/96 → 0/96 trong 12
phút (coder đang vá giữa các lượt). Tôi đọc ba số khác nhau thành "phép đo
không tái lập", **rút lại một finding ĐÚNG**, và suýt chôn mất một bản vá đã
đúng. Một dòng đóng dấu đã đủ để thấy `he_thong` đổi ba lần.

**Vá phải là CƠ CHẾ, không phải lời hứa:** script đo giờ tự đóng dấu hai đầu và
**tự tuyên lượt đo vô hiệu** (thoát mã 3) khi lệch — không chỉ in ra rồi trông
chờ người đọc để ý. Một cảnh báo cần người đọc nhận ra là một cảnh báo sẽ bị bỏ
lỡ đúng lúc bận nhất.

### 4c — ĐỪNG SUY CƠ CHẾ TỪ MỘT CÁI **TÊN**

Cùng sự cố, lỗi thứ hai và nó nguy hơn lỗi thứ nhất. Thấy `thread_signals`
trong `dir(module)`, tôi dựng nguyên một câu chuyện "bộ lọc mang trạng thái
tích luỹ liên lượt nên số chặn nở ra", tuyên bố đó là nguyên nhân, và tự nhận
lỗi. **Chưa đo lấy một lần.** Sự thật: quyết định chặn là hàm thuần, lời gọi
`tang()` chạy sau và chỉ ghi.

Một cái tên gợi ý chức năng; nó **không** chứng minh đường dữ liệu. Muốn nói
"X gây ra Y" thì phải bịt X rồi xem Y có mất không.

**Hệ luận đắt nhất — khi TỰ NHẬN LỖI, đòi bằng chứng y hệt như khi buộc lỗi
người khác.** Một lời tự thú sai làm hỏng sổ không kém một lời buộc tội sai,
và nó **khó bị phản biện hơn**: không ai muốn cãi người đang nhận lỗi. Ở ca
này, lời tự thú sai của tôi đã khiến PO giữ lại một bản vá đúng, và chỉ được
gỡ ra vì coder chịu cãi lại người đang nhận lỗi.

### 4d — "BA LẦN GIỐNG NHAU MỚI BÁO" CHỈ ĐÚNG VỚI LỖI **NGẮT QUÃNG**

Sau sự cố trên, phản xạ tự nhiên là ra luật "số càng gây sốc thì càng phải chạy
đủ ba lần rồi mới báo". **Luật đó sai, và đã bị PO rút khỏi sổ.**

Phân biệt hai loại bất định:

- **Ngắt quãng** (cùng vật, kết quả nhảy): chờ và lặp lại là đúng.
- **Vật đổi dưới chân** (mỗi lượt đo một vật khác): lặp lại **không** hội tụ —
  chạy ba lần vẫn ra ba số. Chữa bằng **đóng băng + đóng dấu**, không bằng chờ.

Ở ca 27/96, báo NGAY kèm cơ chế và ba câu nguyên văn là ĐÚNG: nhờ đó coder tìm
ra gốc trong vài phút. Im chờ đủ ba lần thì hoặc vẫn ra ba số, hoặc tệ hơn —
đợi tới lúc coder vá xong, thấy 0/96, rồi kết luận "không có vấn đề gì" và chôn
luôn một bug thật.

---

## Áp dụng khi review test của nhau

Bốn câu hỏi, hỏi theo thứ tự:

1. **Test này xanh vì lý do gì?** Nếu trả lời được bằng "vì hệ thống mặc định
   đã như vậy" → vi phạm Luật 1.
2. **Ràng buộc này có ca nào chứng minh nó không chặn nhầm chưa?** Không có →
   vi phạm Luật 2.
3. **Kết quả này có tái lập được không?** Kịch bản có lượt LLM sinh → chỉ là
   quan sát, chưa phải finding → vi phạm Luật 3 nếu đem đi kết luận.
4. **Đỏ này là lỗi sản phẩm hay lỗi hạ tầng/bộ chấm?** Chưa mở lý do ra đọc
   thì chưa được kết luận. Trong hai ngày, **bốn** lần một con số đỏ hoá ra
   không phải lỗi agent: SyntaxError giữa lúc lưu file · false positive của
   bộ chấm · rate limit 429 · và một bản vá của chính tôi làm ngược mục đích
   của nó vì tôi chỉ chạy lint mà chưa chạy thử.
