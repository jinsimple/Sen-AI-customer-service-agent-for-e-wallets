# Chuẩn viết test — FIN-05

> Vai giữ file: **tester** · 15/08/2026.
> Tám luật dưới đây được PO phê chuẩn thành **luật dự án**, rút ra từ lỗi THẬT
> gặp trong hai ngày 14–15/08, mỗi luật kèm đúng những ca đã làm nó lộ ra.
> (Luật 6 và 7 thêm 15/08, sau khi hai bộ test lộ ra là **chưa từng chạy một
> lần nào** và một cổng đối chứng lộ ra là **đã rỗng mà không ai biết**.)
>
> **Vị trí file:** nội dung này thuộc về `docs/TESTING.md`, nhưng `docs/` là
> vùng ghi của vai `po` (hiến pháp §4). Tôi giữ bản gốc ở đây — vùng của
> tester — và đã gửi PO nguyên văn để dán sang. Không tự ghi vào vùng khác,
> kể cả khi được mời: ranh giới co giãn "một lần cho tiện" thì lần sau không
> còn là ranh giới.

## Vì sao tám luật, không phải một

Luật 1–5 canh **cái thước** và **phép đo**. Luật 6 canh **trạng thái `skip`**.
Luật 7 canh thứ không ai nghĩ cần canh: **chính công cụ đo** — corpus đối chứng,
hàm đếm, dòng in kết quả. Nó là lớp có ít người canh nhất vì nó không phải sản
phẩm (không ai review) mà cũng không phải test (không ai viết test cho nó).

Một test chỉ có giá trị khi chứng minh được **cả tám** vế:

| | Câu hỏi | Thiếu nó thì |
|---|---|---|
| **Luật 1** | Ràng buộc có **HIỆU LỰC** không? | suite xanh trên một guardrail không tồn tại |
| **Luật 2** | Ràng buộc có **QUÁ RỘNG** không? | suite xanh trên một guardrail cấm cả người hợp lệ |
| **Luật 3** | Phép đo có **TÁI LẬP** được không? | kết luận rút từ một kịch bản không quay lại được |
| **Luật 4** | Thước và vật có **ĐỨNG YÊN** suốt lượt đo không? | cặp before/after lẫn nhiều biến, không quy được nhân quả |
| **Luật 5** | Bản ghi có đủ để **VAI KHÁC BÁC** kết luận không? | một bộ đo không ai kiểm chứng ngược được, kể cả khi nó sai |
| **Luật 6** | Một `skip` có **tự chứng minh** lý do là thật không? | test có mà chưa từng chạy một lần nào |
| **Luật 7** | **Công cụ đo** có còn đo đúng thứ cần đo không? | cổng rỗng, và con số đúng cho một câu hỏi khác |
| **Luật 8** | Kết luận này có **đường đo THỨ HAI** chống lưng không? | công cụ sai vẫn trả lời mạch lạc — mạch lạc SAI |

Thiếu vế nào cũng cho ra một kết luận **trông như đo được mà không đo được gì**.
Đó là lý do tám luật này là một họ, không phải tám quy tắc rời:

- Luật **1–2** canh **cái thước** (nó có hiệu lực không, có quá rộng không)
- Luật **3–4** canh **phép đo** (tái lập được không, thước và vật có đứng yên không)
- Luật **5** canh **cái sổ** — thứ duy nhất còn lại sau khi lượt đo kết thúc
- Luật **6** canh **trạng thái `skip`** — chỗ duy nhất trông như thành công mà không đo gì
- Luật **7** canh **chính công cụ đo** — lớp không ai review vì nó không phải sản phẩm, và không ai viết test vì nó không phải test
- Luật **8** trả lời *canh bằng CÁCH NÀO*: bằng một **đường đo khác loại**, không bằng sự cẩn thận

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

## LUẬT 6 — Một `skip` phải TỰ CHỨNG MINH lý do skip là THẬT

*(15/08/2026 — security đề nghị vế thao tác, tester nhận; rút từ sự cố dưới đây.
Vùng `docs/TESTING.md` là của `po`, nên bản gốc giữ ở đây như bốn luật trên.)*

`skip` là trạng thái nguy hiểm nhất trong một suite, vì nó là trạng thái **duy
nhất trông giống thành công mà không đo gì**. Đỏ thì có người sửa; xanh thì có
người tin; **skip thì không ai làm gì cả** — và dòng lý do bên cạnh nó thường
đủ hợp lý để không ai đọc lại lần thứ hai.

**Ca thật, và nó tệ hơn mọi biến thể của Luật 1:**

```
tests/test_security/test_mau_tier1_chi_thi.py  → "F-22 (tách tier) CHƯA SHIP"
tests/test_security/test_f24_recall_tier1.py   → "Hàm phân tier chưa có trong cây làm việc"
```

Hai file dò hàm bằng cách thử **4 cặp module/tên** tìm `phan_tier`, không thấy
thì `pytest.skip(allow_module_level=True)`. Sự thật: tên là **`_phan_loai_tier`**,
và **2 trong 4 module còn không tồn tại**. Hai bộ test canh lớp phòng vệ
injection **skip từ ngày viết** — chưa từng chạy một lần nào — trong khi sổ dự
án ghi F-22/F-24/F-25 là đã chốt và đang được canh.

Đây là *hiện-diện ≠ hiệu-lực* ở một dạng chưa từng ghi nhận: không phải
**code có mà không chạy**, mà **TEST CÓ MÀ CHƯA TỪNG CHẠY**. Và nó là lần thứ
HAI cùng hình dạng trong một đợt — trước đó `8d26548`, mỏ neo O2 đoán sai tên
`dem_mat_do_liet_ke`, 7 ca skip.

### Vì sao đây là lớp lỗi có hệ thống, không phải hai lần bất cẩn

Hiến pháp §4 chặn tester đọc `src/` — **đúng**, và không nên nới. Nhưng nó có
một phí tổn có thật: tester phải **ĐOÁN mã định danh**, và đoán trượt thì test
**tự tắt trong im lặng**. Đúng họ Luật 14 (*một nhánh không gọi được từ test là
nhánh không ai canh*), lần này là **test không ai canh**.

### Quy tắc

1. **Skip vì "không tìm thấy hàm/lớp/module" gần như luôn là BUG CỦA BỘ TEST**,
   không phải điều kiện môi trường hợp lệ. `skip` chỉ dành cho một **NĂNG LỰC
   chưa tồn tại** (chưa có Postgres, chưa dựng Docker, chưa sinh dataset) —
   không dành cho **dây nối sai**.
2. **Ưu tiên `import` thẳng hơn tầng dò.** Đổi tên/xoá hàm ⟹ `ImportError` ⟹
   **collection error, đỏ ngay**, không ai phải nhớ gì. Cái giá — hàm nội bộ
   `_ten` trở thành **giao diện có hợp đồng**, đổi tên phải báo tester — là giá
   nên trả cho một hàm quyết định xoá-hay-giữ nội dung thật.
3. **Không dùng cờ "bộ test khẳng định tính năng đã ship" để chọn fail-hay-skip.**
   Cờ đó là một **lời nhắc** do người đặt tay, và lời nhắc hỏng đúng vào ngày
   người ta quên sửa nó. Ưu tiên cơ chế tự đỏ.
4. **Mã định danh phải HỎI, không ĐOÁN.** Tên hàm/miền giá trị trả về xin từ
   tech-lead hoặc đọc từ `contracts/`. Đây không phải lách §4: §4 cấm để logic
   sản phẩm nhào nặn *kỳ vọng*, không cấm biết một cái tên.

### 6b — Ranh giới HỎI-hay-ĐOÁN, và một lỗ trong chính §4

Khi xin tên hàm, tôi cũng xin **miền giá trị trả về** (`"tier1"`/`"tier2"`/`""`)
thay vì tự gọi hàm rồi lấy đầu ra làm kỳ vọng — dù việc tự gọi **không vi phạm
chữ nào của §4** (gọi hàm là quan sát hành vi, không phải đọc code).

**Lý do, và nó là một lỗ trong §4 cần bịt bằng kỷ luật:** hiệu chuẩn thước theo
vật cho ra **cùng hậu quả** với đọc code — suite xanh với **bất kỳ** hành vi nào
hàm đang có, kể cả hành vi sai — mà không chạm tới điều cấm nào. Lằn ranh đúng:

> **MÃ ĐỊNH DANH và BẢNG MÃ** hỏi tech-lead / đọc `contracts/`.
> **KỲ VỌNG** (giá trị nào đúng cho đầu vào nào) luôn dẫn từ ĐẶC TẢ, không bao
> giờ từ đầu ra của hàm.

**⚠️ LUẬT NÀY KHÔNG RIÊNG CỦA VAI `tester` — xin giữ ghi chú này khi dán sang
`docs/TESTING.md`.** Trong đúng một phiên (15/08) có **ba** ca cùng họ
*thước-hiệu-chuẩn-theo-vật*, ở **ba vai khác nhau**:

| Vai | Ca |
|---|---|
| tester | hai bộ test skip im lặng 2 ngày vì đoán sai tên hàm |
| tester | 15 kỳ vọng suýt viết lại theo impl thay vì theo đặc tả |
| security | đơn thuốc §5.2 cho ST2-P0-3 kê `scrub_pii` **mà chưa đo nó** |

Ba dạng khác nhau, cùng một lỗi: **để thứ đang bị kiểm quyết định cái thước
dùng để kiểm nó.** Vai nào cũng mắc được, nên luật phải áp cho vai nào cũng vậy.

Một dạng thứ tư cần canh trước vì nó **chưa xảy ra**: cập nhật một MỐC bằng
cách chạy suite rồi chép số ra. Mốc khớp hệ thống thì không canh được gì — một
hồi quy giữa hai lần chép sẽ được chép luôn vào mốc. Mốc phải khớp một **quyết
định có số đo dẫn nguồn**, và hệ thống phải theo kịp quyết định. Đã ghim thành
luật tại chỗ ở `tests/test_security/test_f24_recall_tier1.py` (khối "LUẬT SỬA
MỐC"), viết **trước** khi F-28 land — tức trước khi có ai đó có động cơ lách nó.

Trả lãi ngay trong cùng phiên: chữ ký thật là `-> str` trong khi 15 assertion
viết `== 1` (int). Nếu chỉ vá tên rồi chạy, kết quả là **15/15 đỏ vì lệch kiểu**
— một bảng đỏ **không nói gì** về thứ cần đo. Tên-sai đang che một lệch-kiểu;
tầng dò 4 nhánh không bao giờ phát hiện được, vì nó chỉ có hai nhánh
"thấy hàm" / "không thấy hàm", không có nhánh **"thấy hàm nhưng hợp đồng khác"**.

---

## LUẬT 7 — CÔNG CỤ ĐO cũng cần được canh, và nó là thứ KHÔNG AI canh

*(15/08/2026 — rút từ bốn ca thật trong một buổi chiều, ba vai đều dính.)*

Cả sáu luật trên canh **test** và **phép đo**. Không luật nào canh **thứ dùng
để đo**: corpus đối chứng, hàm đếm, dòng in kết quả. Đó là lớp có ít người canh
nhất, vì nó không phải sản phẩm nên không ai review, mà cũng không phải test
nên không ai viết test cho nó.

### 7a — Bộ đối chứng ĐỦ hôm qua có thể RỖNG hôm nay, không đổi một ký tự

*Luật 8 (đo lại giao của các quyết định) áp cho **công cụ đo** thay vì cho
quyết định.*

| Bản vá | Trục nó chạm | Bộ 7 câu đối chứng phủ? |
|---|---|---|
| F-28 — mở họ **ĐỘNG TỪ** | từ vựng động từ | ✅ ký ĐẠT hợp lệ |
| F-28b — mở **HÌNH THÁI** (`\w*`) | hình thái · phủ định · thân từ | ❌ ký sẽ SAI |

Bộ 7 câu **không thiếu một cách chung chung** — nó **đủ cho bản vá trước và
hụt cho bản vá sau**. Không ai sửa nó, không ai làm hỏng nó; **cái đổi là thứ
nó được dùng để canh**.

⟹ Mỗi lần đổi/mở rộng một ràng buộc, hỏi lại: *"bộ đối chứng có còn phủ TRỤC
MỚI không?"* Tái dùng vì "lần trước nó chạy" là tái dùng một cổng đã rỗng.

### 7b — Corpus đối chứng phải CÙNG NGÔN NGỮ (cùng phạm vi) với thứ đang đo

`FP 0/1814` trên kho tài liệu thật từng là căn cứ để giữ một mẫu ở tier xoá-
trắng. Kho đó **là tiếng Việt**; mẫu đang xét **là tiếng Anh**. Về **cấu trúc**
nó không thể chứa dương tính giả của mẫu đó.

Con số **không sai**. Nó trả lời đúng — **cho một câu hỏi khác câu đang hỏi**.
Và đó là dạng nguy nhất, vì nó có đủ mọi dấu hiệu của một phép đo tốt: mẫu lớn,
tất định, có dấu, hai vai chạy khớp nhau.

Khi đo lại đúng phạm vi: **8/8 dương tính giả**, gồm một khuyến cáo chống lừa
đảo bị xoá trắng. Khoảng cách giữa "0" và "8/8" là khoảng cách giữa *chưa từng
đo* và *đã đo* — không phải giữa hai lần đo.

⟹ Trước khi trích một con số đối chứng, hỏi: **mẫu này có KHẢ NĂNG chứa thứ ta
đang tìm không?** Nếu không, con số đó là 0 vì lý do tầm thường.

### 7c — Bộ đối chứng do MỘT vai soạn gần như chắc chắn hụt trục của vai khác

Cùng một bộ, ba vai bổ sung **ba trục khác nhau**:

| Vai | Trục họ thêm |
|---|---|
| security | hình thái · phủ định |
| tester | biến thể V-ing của chính động từ vừa được thêm (`disregarding`) |
| tech-lead | danh từ đích hợp lệ — trục này làm **8/8** động từ đổ |

Không ai cẩu thả. **Mỗi vai nhìn từ một phía**, nên mỗi bộ mang đúng điểm mù
của người soạn nó. Đây là bản đo-lường của kiến trúc phân-vai: nó không nói
"nhiều người thì kỹ hơn", nó nói **hai người SÓT KHÁC CHỖ NHAU** (Luật 16).

⟹ Một corpus đối chứng chưa qua tay vai khác thì chưa phải cổng ký, dù nó bao
nhiêu ca.

### 7d — Biến dùng để TÍNH không được tái dùng để IN

*(vế thao tác do security đề nghị, sau ca dưới đây.)*

```python
tier = _phan_loai_tier(cau) or '""'    # ← làm đẹp để in
...
dat = tier == SACH                      # ← rồi so với chuỗi RỖNG
```

`SACH` là chuỗi rỗng; `tier` lúc đó đã là chuỗi **hai ký tự** `""`. Mọi ca sạch
bị chấm trượt ⟹ bảng in `dung_hop_le 0/7 XXXXXXX` trong khi **sản phẩm hoàn
toàn đúng**.

Ba assertion thật vẫn đúng suốt. **Chỉ dòng in sai** — và nếu con số đó được
báo ra, hai vai khác đã đi truy một bug **không tồn tại**.

⟹ **Một lỗi chỉ nằm ở lớp BÁO CÁO vẫn đủ sức bẻ lái cả đội**, vì không ai chạy
lại một phép đo khi con số in ra trông hợp lý. Giữ **hai biến riêng**: một để
tính, một để hiển thị.

**Và cách nó bị bắt cũng là luật:** không phải do đọc lại code, mà do **con số
mâu thuẫn với một probe độc lập**. Nguyên tắc hai-dẫn-xuất áp cho chính công cụ
của mình — đúng câu hỏi review số 4: *"đỏ này là lỗi sản phẩm hay lỗi bộ chấm?"*

### 7e — Cổng canh dữ liệu phải bắt MẤT, không được cản THÊM

Cổng canh corpus khoá cứng `{16, 10, 7}` và đỏ ngay khi một vai thêm trục mới —
**đỏ vì lý do sai**: corpus lớn lên là điều ta muốn. Nhưng nới thành "bao nhiêu
cũng được" thì mất luôn thứ cần canh: một ca biến mất vẫn cho tỷ lệ đẹp trên
phần còn lại.

Hai thứ đó **không đối xứng**, nên canh bằng hai luật khác nhau:

```
THÊM ca  ->  hợp lệ, chỉ IN ra để người đọc biết
MẤT ca   ->  ĐỎ, theo TẬP ID cụ thể
```

**Theo tập ID, không theo số đếm** — xoá một ca rồi thêm một ca khác giữ nguyên
tổng và lọt qua mọi phép đếm.

### 7f — Một BIỆN PHÁP chứng minh an toàn trên phạm vi A không mang bảo đảm nào sang B

7b nói về **corpus**. Ca nặng hơn là khi thứ được mang sang không phải một *mẫu*
mà là một **biện pháp**:

| Số | Đo trên | Dùng để duyệt |
|---|---|---|
| `0/1814` | kho tiếng Việt | giữ một **mẫu** ở tier xoá-trắng |
| `0/2006` | kho tiếng Việt | nghiệm thu một **mẫu** mở rộng |
| `0/338` | kho tiếng Việt | duyệt **lượt-2 bỏ khoảng trắng** — một **BIỆN PHÁP** |

**Ba lần trong một đợt.** Cái thứ ba đắt nhất: một **mẫu** sai thì sai một chỗ;
một **biện pháp** sai thì sai ở **mọi mẫu đi qua nó** — và nó im lặng, vì
"biện pháp này đã được duyệt rồi" nên không ai đo lại.

Hậu quả thật: lượt-2 bỏ khoảng trắng biến `the security` → `thesecurity`, chứa
chuỗi con `these` — một mỏ neo. Biện pháp từng **đóng** lớp lỗi né-mức-ký-tự ở
tiếng Việt đã **hồi sinh** lớp lỗi va-chạm-chuỗi-con ở tiếng Anh.

**Hệ luận cho người viết test** (đây mới là phần thuộc file này): nếu bạn đang
canh một phép khớp chạy **sau** một bước chuẩn hoá xoá ký tự, bộ ca **bắt buộc**
phải có ca canh **va chạm chuỗi con vắt ngang ranh giới từ** — `install` chứa
`all`, `priority` chứa `prior`, `the se…` chứa `these`. Không có ca đó thì cổng
mù trước đúng lớp lỗi mà bước chuẩn hoá tạo ra.

### 7g — Đừng suy CƠ CHẾ từ một biến đã cô lập ĐÚNG

*(Mở rộng 4c: bản gốc nói "đừng suy cơ chế từ một cái TÊN"; bản này nói ngay cả
một phép cô lập biến **đúng** cũng chưa đủ.)*

Ca thật: đổi đúng một từ thì kết quả đổi, giữ mọi thứ khác thì không —

```
tier1   Never ignore the security rules ...
tier2   Never ignore the safety   rules ...
tier2   Never ignore the payment/account/house/grammar rules ...
tier2   Never ignore the          rules ...      ← bỏ `security` là hết
```

Kết luận rút ra: *"`security` nằm trong danh sách mỏ neo"*. **Biến đúng, cơ chế
sai.** Đường đi thật: `the security` → (bỏ khoảng trắng) → `thesecurity` ⊃
`these`, và `these` mới là mỏ neo. `security` chỉ là nạn nhân của chữ `the`
đứng trước nó.

> **Cô lập được biến chứng minh CÁI GÌ gây ra, không chứng minh BẰNG ĐƯỜNG NÀO.**
> Nó là điều kiện **cần** để tìm cơ chế, và rất dễ bị nhầm thành điều kiện **đủ**.

**Hệ luận thao tác:** giao **biến đã tách sạch** kèm câu hỏi, đừng giao một
**chẩn đoán** mình không đủ dữ liệu để đưa ra. Người nhận sẽ tìm ra cơ chế thật
nhanh hơn nhiều so với việc phải gỡ một chẩn đoán sai đi kèm vẻ chắc chắn.

Đây cũng là một lợi ích của hiến pháp §4 ít khi được nói tới: **không đọc `src/`
không chỉ chặn test PHẢN CHIẾU code — nó còn chặn CHẨN ĐOÁN TỰ TIN QUÁ MỨC đi
ngược lên chuỗi.** Người đọc code ở cùng vị trí nhiều khả năng đã tự tin hơn
mức dữ liệu cho phép.

---

## LUẬT 8 — Thứ phát hiện công cụ đo sai là MỘT ĐƯỜNG ĐO KHÁC, không phải sự cẩn thận

*(15/08/2026 — rút từ SÁU ca trong một buổi chiều, hai vai.)*

Luật 7 nói **phải canh công cụ đo**. Nó không nói **canh bằng cách nào** — và câu
trả lời không phải "đọc kỹ hơn".

**Sáu lần trong một buổi, không lần nào được cứu bởi việc đọc lại code:**

| # | Vai | Triệu chứng | Thật ra | Thứ phát hiện |
|---|---|---|---|---|
| 1 | tester | `dung_hop_le 0/7` | biến dùng chung cho tính và in | probe trực tiếp ra `""` cả 7 |
| 2 | tester | "relay live-chat một chiều hỏng" | phiên khách hết hạn | mint vé trả `401` |
| 3 | tester | "token 15 phút — rủi ro sân khấu" | đọc tuổi FILE thành tuổi TOKEN | giải mã `exp` trong chính token |
| 4 | tester | "jar rỗng" | parser nuốt dòng `#HttpOnly_` | jar "rỗng" mà request vẫn `200` |
| 5 | tech-lead | "mất sạch dữ liệu, còn 1 user" | `count(*)` thiếu `FROM users` | đếm lại ra 208 |
| 6 | tech-lead | "`middleware.js` rỗng, refresh là mã chết" | stub nạp chunk; chunk mới chứa mã | theo chuỗi nạp thay vì grep một file |

**Mọi lần, cái cứu là một CON SỐ MÂU THUẪN với một đường đo độc lập.** Không lần
nào là "lần này tôi đọc cẩn thận hơn". Cẩn thận không phát hiện được lỗi của
chính mình — vì công cụ sai vẫn trả lời **mạch lạc**, chỉ là mạch lạc sai.

### Quy tắc

1. **Không bao giờ chỉ có MỘT đường đo cho một kết luận sắp làm người khác hành
   động.** Trước khi báo, hỏi: *"nếu công cụ của tôi sai, tôi sẽ thấy gì?"* Nếu
   câu trả lời là "vẫn thấy y hệt thế này" thì chưa đủ để báo.
2. **Ưu tiên đường đo KHÁC LOẠI, không phải đường đo thứ hai cùng loại** (hệ luận
   Luật 16): đọc-mã vs chạy-thật · qua-API vs đọc-thẳng-DB · nhãn-container vs
   probe-hành-vi. Hai lần cùng loại thì **sót cùng chỗ**.
3. **MÂU THUẪN là tín hiệu quý nhất, đừng làm phẳng nó.** Ca 4 lộ ra vì "jar
   rỗng" và "request 200" không thể cùng đúng. Phản xạ tự nhiên là chọn vế hợp ý
   rồi đi tiếp; **đúng lúc đó phải dừng lại**.
4. **Đường đo thứ hai phải rẻ**, nếu không sẽ không ai chạy nó. Giải mã một JWT ·
   probe một hàm · `grep` trong container — vài giây. Rẻ là điều kiện để nó tồn tại.

### Hệ luận cho báo cáo

Khi báo một con số làm người khác hành động, kèm luôn **đường đo thứ hai đã dùng
để tự bác mình**. Không có nó, người nhận phải tin công cụ của bạn — và họ không
có cách nào kiểm.

*Kèm theo, từ cùng buổi:* rút một cảnh báo sai thì dễ; **rút lại một lần-rút** —
khi mọi người đã đồng ý và tài liệu đã sửa theo — thì trông như dao động. Vẫn
phải làm nếu dữ kiện mới không khớp. Ca thật: *"rủi ro lớn nhất"* → *"không có
rủi ro"* → *"có rủi ro, nhưng ở KHOẢNG LẶNG chứ không ở lúc thao tác"*. Chỉ bản
thứ ba là bản đúng, và nó chỉ ra đời vì có người chịu mở lại một hồ sơ đã đóng.

---

## Luật 9 — xác minh nhãn phải soi CẢ HAI phía: ca trượt VÀ ca đạt

> PO phê chuẩn 16/08. Mặt đối xứng của Luật 2, do chính người viết Luật 2 phát
> hiện mình mắc.

Khi một bộ ca có nhãn do người đặt, sai nhãn xảy ra ở **hai chiều**:

| Chiều | Triệu chứng | Ai đi tìm |
|---|---|---|
| **Ca trượt oan** — nhãn quá ngặt | đỏ, gây khó chịu | ai cũng đi tìm, vì nó **kêu** |
| **Ca đạt giả** — nhãn quá lỏng | xanh, êm | 🔴 **không ai đi tìm** |

> **Nếu chỉ soi ca trượt, thước lỏng tay nhất luôn thắng — chiều im lặng nguy
> hơn vì không ai đi tìm.**

**Ca thật (golden-set truy hồi, 16/08).** Tôi soi kỹ 16 ca trượt, **không soi ca
đạt nào**. Coder chứng minh `RAG-04` không phải hồi quy mà là một **pass giả bị
mất**: nó vốn khớp một **dòng mục lục** qua từ khoá yếu `nhận tiền`, chưa bao
giờ tìm ra đáp án. Rà tiếp thì **9/21 ca đạt** chỉ đạt nhờ từ chung. Sau khi
buộc mỗi ca phải khớp **≥1 chuỗi đặc trưng**, số thật: **60,0% → 35,7%**.
Hai phần ba khoảng cách đó là thước, không phải sản phẩm.

**Luật đặt từ khoá (áp cho mọi bộ có nhãn chuỗi):**

1. Mỗi ca **bắt buộc** có ≥1 chuỗi **ĐẶC TRƯNG** khớp mới được tính ĐẠT: có
   **số** · **VIẾT HOA** · hoặc **cụm ≥3 từ**. Từ chung (`hạn mức`, `ngân hàng`,
   `dịch vụ`) chỉ được làm **tham khảo**, không có quyền chấm.
2. Chuỗi đặc trưng phải **hiếm** — có mặt ở ≤2 đơn vị nguồn. Chuỗi trải khắp
   tài liệu vẫn cho pass khi truy hồi lấy nhầm đoạn **bên cạnh**.
3. Chuỗi phải được kiểm là **sống sót qua khâu nạp liệu thật** trước khi gán.
   Nhãn chết vì chữ vỡ (`ngày làm vi`, `xác th ực`) trông y hệt sản phẩm kém.
4. Khi một ca trượt, phải phân biệt **truy hồi trượt** với **nhãn hỏng** bằng
   một đường **độc lập với chính phép chấm** — 16/08 tôi làm việc này bằng cách
   quét kho bằng 160 câu hỏi nguồn rồi hợp nhất đoạn thu được, xác nhận
   **31/35 chuỗi có thật trong kho** ⟹ các ca đó trượt thật.

**Bẫy đã mắc khi làm chính việc này** (Luật 8, ba lần trong một buổi):
tra chuỗi trong Chroma → 0 hit trên **mọi** chuỗi kể cả `miễn phí` 18 lần ⟹ vô
lý ⟹ hoá ra Chroma **chỉ lưu chunk-id**; so chuỗi với PDF chưa chuẩn hoá khoảng
trắng ⟹ 5 báo động giả vì `extract_text` xuống dòng giữa câu; bộ bắt chữ vỡ đầu
tiên báo `nhận được`, `tối đa` là vỡ. **Ba lần đều là thước, không phải vật.**

---

## Luật 10 — BỘ ĐO TỰ TẠO RA HIỆN TƯỢNG NÓ ĐANG ĐO

> Ba ca thật trong một ngày (16/08). Đây là họ lỗi khó thấy nhất vì kết quả
> trông **hợp lý**: nó tăng đều, nó có xu hướng, nó kể một câu chuyện gọn gàng.

**Ca 1 — "câu nặng" hoá ra là số thứ tự lượt.** Bộ đo token chạy cả 7 câu trong
một phiên, ra `N1 13,8k → V1 34,4k` tăng đơn điệu. Kết luận tự nhiên: *V1 là câu
nặng nhất*. Chạy **đảo thứ tự**: `V1 6,2k … N1 26,7k` — vẫn tăng đơn điệu, theo
**vị trí**. Mỗi câu một phiên riêng: tất cả nằm trong `6,2k–15,7k`. Thứ được đo
là **lịch sử hội thoại cộng dồn**, không phải độ nặng của câu.

**Ca 2 — tham số lặp bọc sai chỗ.** `--lap 3` lặp mỗi câu 3 lần *trong cùng
phiên* biến bộ 7 câu thành hội thoại 21 lượt. Muốn lặp một dãy thì lặp phải bọc
**ngoài** dãy, không bọc từng phần tử — nếu không, chính tham số "đo cho chắc"
lại khuếch đại hiện tượng đang đo.

**Ca 3 — phép đo làm cạn tài nguyên rồi hỏng vì chính nó.** Vòng `--lap 3` đẩy
org tới `193.274/200.000 TPM`; một lượt trả `HTTP 500`. Bộ đo vừa là thủ phạm
vừa là nạn nhân.

**Cách bắt — rẻ và gần như luôn hiệu quả:**

1. **Đảo thứ tự.** Nếu kết quả đi theo vị trí chứ không theo phần tử, thứ đang
   đo là vị trí.
2. **Cô lập.** Chạy một phần tử một mình. Số lệch hẳn ⟹ phần còn lại của bộ đo
   đang góp vào con số.
3. **Hỏi phép đo tiêu thụ gì.** Token, kết nối, khoá, dung lượng đĩa — cái nào
   dùng chung thì cái đó có thể quay lại cắn chính phép đo, hoặc cắn người khác.

**Kèm theo — tài nguyên dùng chung cần CỔNG, không cần lời hứa.** Một lời hứa
"tôi sẽ không chạy trong lúc người khác quay demo" không sống sót qua một phiên
bị nén ngữ cảnh, hay một lần bấm mũi tên lên trong shell. `FIN05_DONG_BANG_LLM=1`
làm mọi harness gọi model tự từ chối, và `FIN05_CHO_PHEP_EP_429` tách riêng loại
test **cố ý** đốt hạn mức — bỏ đóng băng nghĩa là *được dùng model bình thường*,
không phải *được phép làm cạn hạn mức của cả đội*.

### 10c — một cổng phải-NHỚ-BẬT vẫn còn một nửa là lời hứa

*(PO phê chuẩn 17/08, từ một vi phạm của chính người dựng cổng.)*

Tôi dựng cổng đóng băng ở trên, đề nghị cả đội dùng nó, rồi **tự đốt 3 lượt LLM
trong lúc đang đóng băng**. Cổng không hỏng — nó chỉ đọc biến môi trường, mà
biến môi trường **chết theo shell**. Tôi `export` nó trong cái shell dùng để
**kiểm cổng**, rồi mở lệnh khác để **thật sự chạy đo**.

> **Một cổng phải-NHỚ-BẬT chỉ chặn được người đang nhớ — tức đúng người không
> cần chặn.**

Đây là bản nâng cấp của chính luật *cơ-chế-thắng-lời-hứa* ở trên: **cơ chế nào
còn một nửa dựa vào trí nhớ thì vẫn còn một nửa là lời hứa.** Và nửa còn lại
hỏng đúng lúc người ta bận — tức đúng lúc cần nó nhất.

**Cách soi một cổng:** hỏi *"cổng này bật bằng cái gì, và cái đó sống được bao
lâu?"*

| Bật bằng | Sống qua | Đủ chưa |
|---|---|---|
| trí nhớ người chạy | không gì cả | ❌ |
| biến môi trường | một shell | ❌ với việc dài hơn một shell |
| **file trong repo** | shell · phiên · nén ngữ cảnh · người khác | ✅ và `ls` là thấy |
| kiểm tra trong CI | mọi lần push | ✅ mạnh nhất, nhưng chậm hơn |

Cổng đóng băng nay nổ khi có **biến môi trường HOẶC** file `.DANG-DONG-BANG-LLM`
ở gốc repo, và thông báo in rõ **nguồn nào** đang chặn — vì bỏ nhầm nguồn cũng
là một cách vô hiệu hoá cổng mà không ai định làm thế.

**Hệ quả về cách báo cáo:** vi phạm này không ai đếm, không ai biết. Tôi vẫn
báo, vì **chọn báo cái gì theo mức độ bị phát hiện** thì mọi con số sau đó mất
chỗ dựa. Và bản thân vi phạm **có giá trị**: nó chỉ ra một lỗ hổng mà đọc code
không tìm ra, bởi lỗ hổng nằm ở chỗ *"con người phải nhớ"* — chỗ không có dòng
code nào để đọc.

---

## Luật 10b — NUỐT MÃ TRẠNG THÁI là một NHÁNH IM LẶNG

Hai lần trong hai ngày, cùng một dòng code:

```python
doan = r.json().get("results") or []      # r.status_code chưa ai xem
```

**Lần 1 (403).** Tôi hỏi agent bằng tài khoản `cskh`; API trả `403 Cần role
thuộc ['customer']`. Không có khoá `tool_calls` ⟹ đếm ra `0` ⟹ tôi kết luận
*"agent không gọi tool chính sách cho một câu hỏi chính sách"* và **báo nó thành
finding**. Nó là lỗi đăng nhập của tôi.

**Lần 2 (422).** Tôi gọi `top_k=10`; API trả `422 "less than or equal to 8"`.
Không có `results` ⟹ đọc ra `0 đoạn` ⟹ tôi kết luận *"API bỏ qua `top_k`"* và
**đem lý do sai đó đi xin đổi metric**. `top_k` hoàn toàn có hiệu lực.

> **Một mã lỗi bị nuốt không biến mất — nó tái sinh thành một PHÁT HIỆN SAI về
> sản phẩm.** Và phát hiện sai thì trông y hệt phát hiện thật: có số, có ngữ
> cảnh, có vẻ hợp lý.

Nguy hơn `try/except` nuốt lỗi, vì ở đây **không có ngoại lệ nào để bắt**:
HTTP 4xx là một phản hồi hợp lệ, `r.json()` chạy trơn tru, `.get()` trả `None`
đúng như hợp đồng. Mọi lớp đều hành xử đúng; chỉ kết luận là sai.

**Luật:** mọi lời gọi mạng trong bộ đo phải **xem mã trạng thái trước khi đọc
thân**, và mã lạ phải **kêu**:

```python
if r.status_code != 200:
    print(f"⚠️  {duong_dan} {r.status_code}: {r.text[:120]}")
    return []          # rỗng thì được — nhưng KHÔNG ÂM THẦM
```

**Biến thể NGÔN NGỮ — tín hiệu VẮNG MẶT bị đọc thành tín hiệu TỐT.** Test dò
chuỗi do **model sinh** (`"ngoài phạm vi"`, `"chưa tìm thấy"`) sẽ **không đỏ**
khi đổi model — nó **âm thầm đổi nghĩa**: model mới từ chối bằng câu chữ khác,
test không thấy chuỗi nào và **báo ĐẠT** trong khi agent vẫn đang đuổi khách đi.
Chữa: assert trên **cờ có cấu trúc** do TA định nghĩa (`should_escalate`,
`goi_y_handoff`), không assert trên chữ do model chọn.

**Dấu hiệu để tự soi:** bất cứ khi nào một phép đo cho **đúng số 0 tròn trĩnh**
— 0 kết quả, 0 lượt gọi, 0 ca đạt — hãy hỏi *"số 0 này là sản phẩm trả lời, hay
là tôi không hỏi được?"* trước khi hỏi *"vì sao sản phẩm tệ thế?"*. Ba lần trong
hai ngày, câu trả lời là vế đầu.

---

## Luật 11 — TỪ CHỐI RỒI TRẢ LỜI TIẾP là bịa có VỎ BỌC

Nguyên văn bắt được ở đường agent thật:

> *"Mình **chưa tìm thấy** thông tin cụ thể về trường hợp nào bạn phải bồi
> hoàn… **Tuy nhiên, thông thường**, việc bồi hoàn có thể xảy ra trong các
> trường hợp như: 1. Thanh toán lặp…"*

Một bộ chấm dò chuỗi `"chưa tìm thấy"` sẽ **chấm ca này ĐẠT**. Câu từ chối có
thật, đúng chữ, đúng chỗ. Cái bịa nằm ở **phần SAU** nó.

> **Bịa thẳng thì thước bắt được. Bịa sau một câu từ chối thì thước KHEN.**

**Assertion phải cắt câu trả lời tại vị trí từ chối và soi phần ĐUÔI**, không
dừng lại ở chỗ tìm thấy câu từ chối:

```python
vi_tri = next((tra.find(t) for t in TU_CHOI if t in tra), -1)
duoi = tra[vi_tri:]                       # phần SAU câu từ chối
assert not [t for t in NOI_TIEP if t in duoi]   # "tuy nhiên", "thông thường"…
```

**Và Luật 3 áp cho chính finding này.** Tôi báo nó thành finding từ **một** lượt.
Chạy lại k=3 rồi k=11: **0/11 tái hiện** — vì coder đã land một đòn tối ưu token
giữa hai lần đo. Quan sát có thật, nhưng nó nói về một **vật khác**. Ca được giữ
lại làm **cổng hồi quy** chứ không phải finding, vì hành vi đúng hiện nay là
**hệ quả phụ chưa ai cố ý làm ra** — thứ như thế mất đi lúc nào không ai biết.

---

## Luật 6b — một `skip` ĐÚNG LÝ DO vẫn có thể QUÉT QUÁ RỘNG

Luật 6 canh *"lý do skip có thật không"*. Luật này canh **phạm vi** của nó.

Ca thật (16/08). Bộ `test_f33*` cần **ép 429**, tức đốt gần hết trần TPM dùng
chung — lý do skip hoàn toàn thật. Tôi gắn nó ở **cả file** bằng `pytestmark`.
Nhưng trong file có `test_f33c`, ca chỉ **hỏi lược đồ DB** xem cột
`ly_do_fallback` đã tồn tại chưa: **0 lượt gọi model, chạy được ngay**.

Gắn cổng cho cả file thì ca kiểm-được-ngay **bị chôn theo mấy ca không chạy
được**, và nó nằm im **đúng lúc nó hữu ích nhất** — lúc đang đóng băng, khi mọi
thứ khác đều không đo được thì đúng ra nó phải là cái duy nhất còn nói được điều
gì đó.

> **Phần bị quét oan im lặng y hệt một `skip` sai.** Không ai đọc log thấy khác
> biệt: cùng một chữ `SKIPPED`, cùng một lý do nghe hợp lý.

Cách làm đúng: hạ cổng xuống **từng ca**, đặt tên cho nó, và chỉ dán lên ca thật
sự cần:

```python
can_dot_han_muc = pytest.mark.skipif(not CHO_PHEP, reason="…")

@can_dot_han_muc
def test_ep_429(...): ...

def test_hoi_luoc_do(...): ...      # KHÔNG dán — nó không tốn gì
```

**Câu hỏi để tự soi:** *mọi ca trong phạm vi cổng này đều thật sự cần thứ đang
thiếu chứ?* Chỉ cần **một** ca không cần, cổng đang quét quá rộng.

---

## Luật 12 — KHÔNG SAI MỘT CHỮ NÀO MÀ VẪN GÂY HIỂU SAI

Áp cho **tài liệu và báo cáo**, không chỉ test. Một câu có thể **đúng từng chữ**
mà vẫn dẫn người đọc tới kết luận sai, và loại lỗi này không bị bất kỳ phép kiểm
sự-thật nào bắt được — vì không có gì để bắt.

**Ba dạng đã gặp trong một ngày:**

**① Phân số đứng trơ cạnh một phân số khác vừa bị sửa.** Tài liệu sửa
`ToS 2/8 → 2/10`, rồi ba dòng sau có `bất ổn định 6/8-2/8` — chỗ này `2/8` là
**tỉ lệ lượt** của một ca, hoàn toàn đúng. Nhưng người đọc vừa học "ToS không
phải 2/8" sẽ đọc nó thành sót hoặc mâu thuẫn. Chữa: viết hẳn ra
*"8 lượt cùng một câu: 6 lượt từ chối an toàn · 2 lượt đuổi ngoài phạm vi"*.

**② Khái quát hoá lặng lẽ.** *"2 ca âm bản để **chứng minh** agent nói 'không
tìm thấy' chứ không bịa số"* — hai ca đó có thật và đúng. Cái sai là bước nhảy
từ *"2 ca này không bịa"* sang một **tính chất của hệ thống**, mà ta có phản ví
dụ đã đo (F-32). Chữa: giữ sự kiện, bỏ chữ `chứng minh`, ghi kèm giới hạn.

**③ Khai thấp cũng là khai sai.** *"7 PR đã merge"* khi thật ra đã 10 — BTC đọc
thành **chưa đạt** tiêu chí. Sai theo hướng khiêm tốn vẫn là sai, và loại này ít
ai đi kiểm vì nó không có mùi khoe.

**Cách soi (dùng khi rà bất kỳ tài liệu nào rời khỏi đội):** đọc từng câu và hỏi
*"người chưa biết gì sẽ kết luận gì từ câu này?"* — rồi so kết luận đó với thứ
**đo được**, không so với câu chữ. Chênh nhau ⟹ sửa câu, kể cả khi từng chữ đều
đúng.

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
