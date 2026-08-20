# Chuẩn viết test — FIN-05

> Vai giữ file: **tester** · 15/08 → 17/08/2026.
> Mỗi luật dưới đây được PO phê chuẩn thành **luật dự án**, và **không luật nào
> được nghĩ ra từ nguyên tắc** — tất cả rút từ một lỗi THẬT đã xảy ra, kèm đúng
> ca đã làm nó lộ ra. Đó cũng là lý do thứ tự trong file là **thứ tự thời gian
> phát hiện**, không phải thứ tự logic: luật con `1c` nằm sau `Luật 10` vì nó
> được phát hiện sau. Dùng mục lục dưới đây để tra, đừng đọc tuần tự.

## Mục lục

| | Luật | Canh cái gì |
|---|---|---|
| **1** · 1b · **1c** | assertion không trùng trạng thái mặc định · không trùng đầu-ra-hỏng · `xfail` nuốt lỗi hạ tầng | **cái thước** |
| **2** | ràng buộc phải có ca chứng minh không chặn nhầm | cái thước |
| **3** | lượt LLM để KHÁM PHÁ, lượt viết cứng để ĐIỀU TRA | phép đo |
| **4** | ghim cả thước lẫn vật, ghim ở CẢ HAI đầu | phép đo |
| **5** | bộ đo lưu đủ để VAI KHÁC bác được nó | cái sổ |
| **6** · 6b | `skip` phải tự chứng minh lý do · và không được quét quá rộng | trạng thái `skip` |
| **7** | công cụ đo cũng cần được canh | công cụ đo |
| **8** | thứ phát hiện công cụ sai là MỘT ĐƯỜNG ĐO KHÁC | công cụ đo |
| **9** | xác minh nhãn phải soi CẢ HAI phía | nhãn |
| **10** · 10b · 10c · **10d** | bộ đo tự tạo ra hiện tượng nó đo · nuốt mã trạng thái · cổng phải-nhớ-bật · vô hiệu hậu quả trước khi kiểm cổng | bộ đo & cổng |
| **11** | từ chối rồi trả lời tiếp là bịa có VỎ BỌC | đầu ra agent |
| **12** · 12b | không sai một chữ nào mà vẫn gây hiểu sai · xếp hạng trên MỘT trục | tài liệu & báo cáo |
| **13** · 13b | đo đúng thứ, nhưng đưa vào một KÍCH THÍCH khác · đo trên phần đang chú ý thay vì kích thích trọn vẹn | đầu vào của bộ đo |
| **14** | hai người đo độc lập rồi so SỐ — cấm hoà ở tầng KẾT LUẬN | quy trình đo |
| **15** | DẤU VẾT bộ đo để lại trong hệ đang chạy, không phải độ chính xác của nó | hậu quả của phép đo |
| **16** | N mệnh đề cần N ĐỘT BIẾN, mỗi cái làm đúng một tập con đỏ | quan hệ GIỮA các test |
| **17** | che theo VẬT không theo MẪU — danh sách CHO PHÉP, không phải danh sách CẤM | thứ bộ đo IN RA |
| **18** | băm phải khai TÊN THUẬT TOÁN — hex không tự khai nguồn gốc | định danh phép đo |
| **19** | KHẢ NĂNG QUAN SÁT của test bị chính cơ chế xử lý lỗi của hệ xoá đi | tiền đề của phép đo |
>
> **Vị trí file:** nội dung này thuộc về `docs/TESTING.md`, nhưng `docs/` là
> vùng ghi của vai `po` (hiến pháp §4). Tôi giữ bản gốc ở đây — vùng của
> tester — và đã gửi PO nguyên văn để dán sang. Không tự ghi vào vùng khác,
> kể cả khi được mời: ranh giới co giãn "một lần cho tiện" thì lần sau không
> còn là ranh giới.

## Vì sao nhiều luật, không phải một

Luật 1–5 canh **cái thước** và **phép đo**. Luật 6 canh **trạng thái `skip`**.
Luật 7 canh thứ không ai nghĩ cần canh: **chính công cụ đo** — corpus đối chứng,
hàm đếm, dòng in kết quả. Nó là lớp có ít người canh nhất vì nó không phải sản
phẩm (không ai review) mà cũng không phải test (không ai viết test cho nó).

Tám vế đầu (Luật 1–8) là bộ khung; một test chỉ có giá trị khi chứng minh
được **cả tám**:

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

### 4e — Ca đo hành vi MỘT LƯỢT phải chạy trên `thread_id`/`user_id` MỚI, không tái dùng

Sự cố (19/08, GĐ3): 4 lượt "cổng nhập bể" chạy chung `user_id="USR-A"`, không
truyền `thread_id`. `run_agent_turn` mặc định `thread_id = user_id`, và
checkpointer (`PostgresSaver`) sống **ngoài tiến trình**, khoá theo
`thread_id` — bốn `docker run --rm` tách biệt vẫn là **MỘT hội thoại
LangGraph liên tục** trong mắt hệ thống, không phải bốn phép đo độc lập.

Lượt đầu gọi tool thật (`so_tool_call=1`, kết quả thật). Ba lượt sau
`so_tool_call=0` — vì agent **NHỚ ĐÚNG** kết quả đã tra ở lượt trước trong
cùng thread, không phải bịa — nhưng câu trả lời trông **y hệt** "model không
gọi tool và tự bịa đã kiểm tra". Suýt leo thang thành nghi vi phạm ràng buộc
cứng số 3 trước khi bị chặn lại bằng cách đối chiếu ngược lượt đầu tiên.

**Vì sao đây không chỉ là "nhiễu":** nó đổi CÂU HỎI mà cổng trả lời. Cổng viết
để đo *"model này có gọi tool khi cần không"*; chạy chung một thread thì cổng
đo *"agent có nhớ ngữ cảnh cũ không"* — và trả về một giá trị **trông hợp lệ**
cho câu hỏi đầu. Lỗi nằm ở tầng **bố trí phép đo** (thiết kế ca), không nằm
ở mã sản phẩm — cùng họ với Luật 4 nói chung (thước/vật đứng yên), nhưng lệch
sang trục **danh tính của cuộc hội thoại**, một trục Luật 4 gốc chưa nêu tên.

**Vế thi hành:**
1. Mỗi ca đo hành vi một lượt phải sinh `user_id`/`thread_id` **MỚI**, không
   hardcode một giá trị dùng lại qua nhiều lượt — kể cả khi các lượt đó chạy
   ở container/tiến trình khác nhau (trạng thái sống trong DB dùng chung, không
   phải trong tiến trình).
2. Khi đọc sổ (`usage.jsonl`) để chẩn đoán, đọc kèm cột định danh hội thoại
   (`thread_id` nếu sổ có ghi) — đây là thứ phân biệt được "bốn phép đo" với
   "một hội thoại bốn lượt".
3. **Tín hiệu cảnh báo:** nhiều lần chạy cho kết quả **giống hệt nhau** (không
   chỉ cùng kết luận, mà gần như cùng câu chữ) là dấu hiệu nghi **CÙNG MỘT
   NGUỒN** (state rò rỉ giữa các lượt) — kiểm điều đó TRƯỚC khi mừng vì "tái
   lập được". Đối lập có chủ đích với 4d: 4d nói khi nào ĐƯỢC TIN sự lặp lại
   (lỗi ngắt quãng, cùng vật); 4e nói khi nào chính sự lặp lại là dấu hiệu
   **phép đo hỏng** (không phải cùng vật — cùng NGỮ CẢNH bị rò).

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

### 7h — Đếm ca mang một NHÃN thì phải hỏi bộ chọn nhãn, không hỏi văn bản

*(20/08 — PO-agent vấp, tự khai và tự sửa. Ghi thẳng tên vì luật rút từ lỗi
của người điều phối mà giấu tên thì lần sau người khác sẽ tưởng nó chỉ áp
cho cấp dưới.)*

`pytest -m X --collect-only -q` chứ không `grep -rl X`. `grep` khớp cả **văn
xuôi bàn về nhãn** — kể cả một câu đang khai *"không còn nhãn X"* — nên nó có
thể đếm **bằng chứng nhãn đã gỡ** thành **bằng chứng nhãn còn đó**, cho kết
quả **ngược hẳn** sự thật, không chỉ lệch số.

Ca thật: `grep -rl security_finding tests/` ra **9**; bộ chọn nhãn thật
(`pytest -m security_finding --collect-only`) ra **1**. Ba trong chín "hit"
sai là những dòng docstring viết nguyên văn *"Không còn
`@pytest.mark.security_finding`"* — PO-agent đếm chính lời khai NHÃN ĐÃ GỠ
thành bằng chứng NHÃN CÒN ĐÓ, một kết luận đảo ngược 180 độ dù công cụ "đọc
được chữ" hoàn toàn chính xác.

> Công cụ hiểu **CHUỖI KÝ TỰ** và công cụ hiểu **NHÃN** là hai công cụ khác
> nhau, dù nhãn thường được viết bằng chuỗi ký tự trùng tên nó. Khi câu hỏi
> là "cái gì đang mang nhãn X", chỉ công cụ thứ hai trả lời được — công cụ
> thứ nhất trả lời một câu hỏi khác trông giống hệt.

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

### 1c — `xfail` NUỐT lỗi hạ tầng thành "finding tái hiện"

*(PO phê chuẩn 17/08. Loại nguy hiểm nhất gặp tới nay.)*

Chạy bộ F-31/F-32 với `BASE_URL` trỏ vào một cổng chết. Kết quả: **ba ca báo
`XFAIL`** — tức *"finding tái hiện"* — trong khi **phép đo không hề chạy**. Lỗi
nối mạng xảy ra ở fixture, và `xfail(strict=True)` nuốt luôn nó.

Kịch bản thật mà nó dẫn tới: **stack sập giữa lượt chạy ⟹ báo cáo "hai finding
vẫn tái hiện" một cách hoàn toàn thành thật và hoàn toàn sai.**

> **Đỏ-oan thì có người soi. Xanh-đúng-ý thì không ai soi.**

Đó là điều làm dạng này nguy hơn mọi dạng ở Luật 1: nó **khớp với điều ta đang
kỳ vọng**. Một ca đỏ bất ngờ luôn có người đi tìm nguyên nhân; một ca xác nhận
đúng thứ ta vừa báo cáo tuần trước thì không ai chạm vào.

**Cách chữa — cổng ở tầng MODULE, không để `xfail` tự xử:**

```python
def _song() -> bool:      # tiến trình CÒN SỐNG không   (docker ps)
def _api_song() -> bool:  # dịch vụ TRẢ LỜI ĐƯỢC không  (gọi thử một endpoint)

pytestmark = [pytest.mark.skipif(not _api_song(), reason="…KHÔNG đo được")]
```

**Hai câu hỏi đó khác nhau, và ta đã trả giá một lần cho việc nhầm chúng:** kho
báo `378 chunk`, Chroma báo `378 vector`, `kiem` xanh — mà `/api/policy-search`
trả rỗng cho **mọi** truy vấn. Ba nguồn xác nhận "còn sống", không nguồn nào
xác nhận "trả lời được".

---

### 7c — bộ rà chưa biết SÀN NHIỄU của mình thì báo cáo của nó không đọc được

*(PO phê chuẩn 17/08.)*

Một bộ rà báo `9 ca có vấn đề`. Con số đó **không đọc được** nếu chưa biết bộ
rà đó báo mấy ca trên một tập **đã biết là sạch**.

**Cách hiệu chuẩn — rẻ, và luôn làm được:** chạy bộ rà trên tập ta **đã tự tay
rà xong**, rồi đếm nó báo nhầm bao nhiêu.

Ca thật: bộ rà nhãn chạy trên golden-set (bộ vừa rà hai phía, biết là sạch) báo
**9/47 "không thấy trong kho"**. Cả 9 là **dương tính giả** — đã kiểm hôm trước
bằng đường độc lập, 15/15 chuỗi nghi ngờ đều có thật. ⟹ phép dò đó có **sàn
nhiễu ~19%**.

**Hệ quả về CÁCH GỌI TÊN, không chỉ về con số:** sau khi biết sàn nhiễu, nhãn
kết quả đổi từ

    "lỗi: không có trong kho"
    → "NGHI không có trong kho — phép dò YẾU, phải kiểm lại bằng đường độc lập
       TRƯỚC KHI sửa nhãn"

Chữ *"lỗi"* mời người ta đi sửa. Trên một bộ chỉ-bắn-một-lần, **nhiễu còn tệ
hơn im lặng**: người đọc báo cáo sẽ đi sửa thứ không hỏng, và mỗi lần sửa nhãn
theo một phép dò yếu là một lần **hiệu chuẩn thước theo vật**.

Đây chính là vòng lặp đã suýt cắn hôm trước: 15 nhãn **lành** suýt bị sửa vì
một phép dò báo chúng vắng.

**Ba câu hỏi trước khi tin bất kỳ bộ rà nào — kể cả của mình:**
1. Nó báo mấy ca trên một tập **đã biết là sạch**?
2. Những ca nó báo có **kiểm lại được bằng đường khác** không?
3. Tên gọi kết quả có mời người ta **sửa ngay** không, trong khi lẽ ra phải
   **kiểm lại trước**?

---

### 8b — nhiều đối tượng ĐỘC LẬP cùng cho một kết quả lạ ⟹ nghi KÍCH THÍCH trước

*(PO phê chuẩn 17/08.)*

Ba model **độc lập**, 15/15 lượt, cùng từ chối gọi một tool. Tôi đi được **nửa
đường**: nghi **nhãn** thay vì nghi model — đúng, và Luật 9 dạy thế. Rồi dừng.

Cả đội bàn tiếp về nhãn: tôi sửa nhãn, PO ra ba điều kiện thủ tục, ta khoá băm,
ta tranh luận thiên vị hậu-kiểm. **Không ai hỏi vì sao cả ba model cùng từ chối
đúng một tool.**

Câu trả lời thật: tool đó **trống rỗng** — mô tả **31 ký tự**, **0 tham số**,
vì tôi dựng lược đồ từ `contracts/` mà contract khai thiếu. Sản phẩm thật đưa
model **1266 ký tự và 5 tham số**. Ba model không "sai giống nhau"; chúng phản
ứng **đúng** với thứ ta đưa.

> **Nhiều đối tượng độc lập cùng cho một kết quả bất thường thì thứ đáng nghi
> là NGUỒN KÍCH THÍCH, không phải các đối tượng — và cũng không dừng ở nhãn.**

Thứ tự nghi ngờ khi thấy một kết quả nhất quán bất thường:

    1. kích thích ta ĐƯA vào có đúng thứ sản phẩm đưa không?
    2. nhãn ta gán có suy được từ nguồn sự thật không?
    3. đối tượng có thật sự yếu không?

Ta quen bắt đầu từ (3), Luật 9 kéo về (2), và luật này kéo về (1). **Càng gần
(1) thì lỗi càng rẻ để sửa và càng làm hỏng nhiều số nếu bỏ qua.**

**Hệ quả cụ thể:** `contracts/` là nguồn sự thật về **CẤU TRÚC** (tên tool, ai
gọi được, ràng buộc) — **không phải** về **NỘI DUNG** mô tả mà model đọc. Bộ đo
nào cần đúng kích thích thì phải **introspect app đang chạy**, không đọc
contract. Đo được ngày 17/08: mô tả contract ngắn hơn app **11×–41×**.

---

### 8c — người GIAO việc mô tả một lỗi KHÔNG đảm bảo lỗi đó tồn tại

*(PO phê chuẩn 17/08, sau khi chính họ giao một lỗi không tồn tại.)*

PO xếp `by_severity.get(sev, 0)` là **ca ưu tiên cao nhất** trong họ mặc-định-
im-lặng, kèm lập luận đúng và cấp bách. Tôi bắt tay sửa. Rồi đọc dòng trên:

```python
by_severity = Counter(r["severity"] for r in results)
```

`Counter` — **khoá vắng nghĩa là đếm được 0**, đúng nghĩa. Bản sửa của tôi sẽ
in `"KHÔNG BIẾT"` trong khi sự thật là `0`. **Người giao làm output tệ hơn qua
tay người làm.**

> **Kiểm tiền đề trước khi sửa — kể cả khi người giao việc mô tả rõ ràng, cấp
> bách, và có lý.**

Đây là mặt đối xứng của Luật 8b: ở đó ta nghi sai **đối tượng đo**; ở đây ta
nhận sai **mô tả lỗi**. Cả hai đều là *"làm theo thứ được đưa mà không kiểm thứ
được đưa"*.

**Và đừng vứt cả yêu cầu.** Sau khi bác tiền đề, vẫn còn một ca thật: `results`
rỗng, hoặc `severity` thiếu trường ⟹ bảng in `Blocker=0` từ **zero dữ liệu**,
và lúc đó *"0 Blocker"* với *"chưa đo được"* đúng là giống hệt nhau trên slide.
Cảnh báo **đúng ca đó**, im lặng ca lành — kết quả tốt hơn cả bản gốc lẫn bản
sửa theo mô tả.

---

### 7b — NGUỒN DỮ LIỆU ĐÚNG, DÂN SỐ SAI

*(PO phê chuẩn 17/08.)*

Luật 7 canh *"công cụ đo có còn đo đúng thứ cần đo không"*. Đây là dạng tinh vi
nhất của nó: **công cụ đúng, nguồn đúng, truy vấn đúng — chỉ dân số là sai.**

Ca thật. Cần biết người dùng gõ với nhịp nào để tính trần chịu tải. Nguồn đúng
(`messages`), truy vấn đúng, chạy trơn:

    81 phiên · 230 tin khách · khoảng giữa hai tin: trung vị 3 giây
    ⟹ 19,8 lượt/phút/người — gấp 40 lần giả định 0,50

Con số **vô nghĩa**: 230 tin đó do **script test** sinh, không phải người. Máy
gõ tin tiếp theo ngay khi nhận xong phản hồi.

> **Nguồn sai thì lộ ra sớm — nó lỗi, nó rỗng, nó không khớp. Dân số sai thì
> CHẠY TRƠN**: đường ống thông, con số ra đẹp đẽ, và nó nói về một quần thể
> không phải quần thể ta cần.

**Cách chữa — ghi cảnh báo NGAY CẠNH TRUY VẤN**, không phải trong một mục ghi
chú xa xôi: người kế tiếp sẽ gặp truy vấn **trước khi** gặp tài liệu.

**Câu hỏi tự soi:** *"những bản ghi này do AI hay do NGƯỜI sinh ra? do đúng
nhóm người tôi cần chưa?"* — hỏi trước khi đọc con số, không phải sau.

**Hệ quả về việc mượn số ngoài:** một con số benchmark ngành, từ sản phẩm khác
· tập người dùng khác · ngôn ngữ khác, **cũng là một giả định** — chỉ khác là
nó **trông có căn cứ hơn nên khó bị chất vấn hơn**.

> **Một giả định đội lốt dữ liệu tệ hơn một giả định tự nhận là giả định.**

Thà giữ con số cũ với nhãn *"giả định của ta, chưa đo"*.

---

### 10e — ĐUÔI phải tính CÓ ĐIỀU KIỆN, không ghép chéo phân vị

*(PO phê chuẩn 17/08, từ một lỗi của chính người vừa dạy "đọc ở đuôi".)*

Bài toán: hệ chịu được bao nhiêu lượt/phút? Ràng buộc là **token/phút** và
**lời gọi/phút**, nên phải biết một lượt tốn bao nhiêu của mỗi thứ.

Cách sai — và nó trông rất hợp lý: lấy **max số lời gọi** (8) ghép với **trung
vị token** (27,9k) để dựng "kịch bản đuôi". Nhưng hai đại lượng đó **không độc
lập**. Đo trên 40 bản ghi có cả hai trường:

    r = +0,88
    2 lời gọi → 13.709 token (trung vị)
    7 lời gọi → 67.572 token

> **Ghép phân vị cao của biến này với phân vị giữa của biến kia mô tả một kịch
> bản có thể KHÔNG TỒN TẠI** — và ở đây nó khiến ta kết luận sai về việc ràng
> buộc nào đang chặn.

**Cách đúng — tính có điều kiện:** mỗi mức của biến này dùng **đúng giá trị đo
được của biến kia ở chính mức đó**.

    lời gọi   token      trần theo TPM   trần theo RPM   CHẶN bởi
       2     13.709          364,7           300,0        RPM
       5     36.998          135,1           120,0        RPM
       7     67.572           74,0            85,7        TPM   ← đuôi thật

Kết quả **đảo ngược kết luận**: ở đuôi thật, ràng buộc chuyển từ RPM sang TPM,
và một model có RPM cao gấp 25 lần **không hơn được gì** vì TPM chặn trước.

**Dấu hiệu để tự soi:** khi một kịch bản được dựng từ **nhiều thống kê của
nhiều biến**, hỏi *"tôi có bản ghi nào THẬT SỰ trông như thế này không?"* Không
có ⟹ đang suy luận trên một điểm dữ liệu tưởng tượng.

---

### 10d — kiểm một cổng chặn thì phải vô hiệu hoá HẬU QUẢ trước

*(PO phê chuẩn 17/08, nâng thành nguyên tắc chung.)*

> **Cách kiểm một cổng chặn KHÔNG được là "chạy thử xem có bị chặn không" —
> làm thế thì lúc cổng thủng, ta TRẢ TIỀN để biết. Phải làm cho lối đi phía sau
> cổng vô hại TRƯỚC, rồi mới thử.**

Tôi học điều này bằng cách đốt hai lần hạn mức LLM để kiểm chính cái cổng mình
dựng ra để không đốt hạn mức.

**Bảng vô hiệu hoá — mỗi đường một cách, và MỘT cách không phủ hết:**

| Nơi gọi model | Vô hiệu bằng | Vì sao cách kia không được |
|---|---|---|
| đọc key ở **host** (`_harness` · `_llm_judge` · …) | `OPENAI_API_KEY=sk-invalid` | — |
| đi qua **`/api/agent-chat`** | `FIN05_BASE_URL=https://127.0.0.1:9` | model gọi **trong container**, container có key RIÊNG — key giả ở host không chạm tới |

Đã kiểm: container mang key riêng dài 164 ký tự. **4 file** thuộc nhóm trên,
**6 file** thuộc nhóm dưới — và cả hai lần đốt tiền đều nằm ở nhóm dưới.

**Khái quát ra ngoài chuyện tiền:** mọi cổng chặn một **hành động không đảo
ngược** đều phải kiểm theo kiểu này — vô hiệu hoá hậu quả trước, rồi mới thử
cổng. Xoá dữ liệu, gửi thư, đẩy commit, gọi API tính phí: đừng bao giờ kiểm
bằng cách để nó thật sự xảy ra nếu cổng thủng.

---

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

## Luật 13 — ĐO ĐÚNG THỨ, NHƯNG ĐƯA VÀO MỘT KÍCH THÍCH KHÁC

> Nguồn: bộ đo tool-calling v4, 17/08. Ba lần siết kích thích rồi, vẫn sót.

Bộ đo v4 đã làm đúng thứ khó: lược đồ tham số **introspect từ app**, mô tả tool
lấy **nguyên văn** `build_customer_tools()` — vì v1/v2 từng dựng từ `contracts/`
và đo nhầm một kích thích ngắn hơn thật 11–41 lần. Tưởng đã sạch.

Nhưng `system` message thì tôi **tự soạn 123 ký tự**. Sản phẩm gửi **15.094 ký
tự**, mọi lượt, vô điều kiện.

    bộ đo :    123 ký tự  (tôi viết)
    sản phẩm: 15.094 ký tự (build_system_prompt())
    ⟹ bộ đo gửi 1/123 lượng chỉ dẫn

Và phần thiếu không phải rìa: nó chứa `"PHẢI tra ra CẢ HAI"` và `"chủ động tra
giúp"` — chỉ dẫn cho **đúng hai ca mà cả bốn model đều sai**.

**Vì sao nó nguy hiểm hơn một bộ đo hỏng hẳn.** Bộ đo hỏng hẳn thì ra số vô lý,
ai cũng thấy. Cái này ra một **quy luật đẹp và nhất quán**: bốn nhà cung cấp
khác nhau, hai họ model khác nhau, cùng sai đúng hai ca. Sự đồng thuận đó **tự
nó trông như bằng chứng** — bốn chứng nhân độc lập khai giống nhau. Đội tôi đã
bắt đầu đi tìm *"vì sao sản phẩm sai"*, tức đi giải một bí ẩn không tồn tại.
Chúng nó chưa từng được đọc chỉ dẫn đó.

> **Một bộ đo thiếu kích thích không tạo ra nhiễu — nó tạo ra TÍN HIỆU SẠCH của
> một câu hỏi khác.** Càng nhiều model đồng thuận, tín hiệu càng thuyết phục,
> càng khó ngờ.

**Cách chặn — kê khai kích thích, không kê khai ý định.** Mọi bộ đo gọi model
phải in ra, cạnh kết quả:

    system   : <độ dài> ký tự · băm · NGUỒN (tự soạn / lấy từ hàm nào của app)
    mô tả tool: <độ dài từng cái> · NGUỒN
    lược đồ  : NGUỒN

Trường **NGUỒN** là thứ bắt lỗi này, không phải độ dài. `123 ký tự` không gợi
gì; `TỰ SOẠN` đặt cạnh `introspect app` thì lệch lộ ra ngay. Ba dòng, không có
dòng nào là "tôi tin nó đúng".

**Và luật đối chiếu:** với mỗi kênh kích thích, đo cả **hai đầu** — thứ bộ đo
gửi và thứ sản phẩm gửi — rồi in tỉ lệ. Đây là Luật 7c (bắc cầu hai đầu) áp cho
**đầu vào**, không phải đầu ra. Tôi đã áp nó cho kết quả và quên áp cho kích
thích.

### 13b — vế thi hành: đo trên KÍCH THÍCH TRỌN VẸN, không đo trên phần đang chú ý

> Biết Luật 13 **không** miễn nhiễm với Luật 13. Trong ngày viết ra nó, lớp lỗi
> này bắt cả tôi lẫn security, **mỗi người hai lần, trên cùng một đoạn văn bản**.

Lần hai của tôi xảy ra **bên trong phần sửa lỗi lần một**. Tôi so *"lệnh cấm
bịa"* giữa hai `system` message — 1 lần / 123 ký tự so với 6 lần / 15.094 — và
công bố **loãng 20 lần**. Sai, vì **mô tả tool cũng là chỉ dẫn, cũng chứa lệnh
cấm bịa, và có mặt ở CẢ HAI phiên bản**. Tôi đo trên kênh mình đang chú ý, chứ
không trên thứ model thật sự đọc.

Đo lại trên ba định nghĩa kích thích:

    chỉ system (bỏ mô tả tool)      0,8130% → 0,0398%  =  20,45×
    system + description            0,0802% → 0,0451%  =   1,78×
    system + JSON tool trọn vẹn     0,0548% → 0,0404%  =   1,36×

**Hướng ổn định, độ lớn không.** Kết luận định tính (*"bộ đo đậm hơn sản phẩm"*)
đứng ở mọi định nghĩa; con số thì đi từ 1,36× tới 20,5× **chỉ vì đổi ranh giới
của thứ được gọi là "kích thích"**.

> Một đại lượng đổi **15 lần** theo định nghĩa mà không ai đổi phép đo nào —
> đó không phải kết quả, đó là **một câu hỏi chưa đặt xong**.

**Hai vế thi hành:**

1. **Chốt định nghĩa "kích thích" MỘT lần, trước khi đo**, và băm đúng vật đó.
   Ở đây: `system message + JSON tool trọn vẹn như gửi đi` — vì đó là thứ thực
   sự lên dây; *"chỉ description"* bỏ mất tên tool và lược đồ tham số, mà model
   đọc cả hai.
2. **Đại lượng phải sửa nhiều lần trong một ngày thì KHÔNG rời khỏi đội** — kể
   cả khi lần sửa cuối trông đã đúng. Ghi lại đầy đủ trong hồ sơ, công bố ra
   ngoài chỉ phần định tính đã ổn định.

**Dấu hiệu quy trình đang lành:** ba lần sửa con số này đi **ngược chiều nhau**
(hạ · nâng · thành khoảng), và mỗi lần do **bên bất lợi vì nó** tự nêu ra. Khi
mọi lần đính chính đều đẩy số về phía có lợi cho người đính chính, đó là lúc
phải nghi ngờ — không phải khi nó đổi nhiều.

**Hệ quả khi lỡ vi phạm rồi:** bộ đo **câm theo cả hai chiều**. Không được rút
*"sản phẩm sai"*, và cũng không được rút *"sản phẩm ổn"* — chiều thứ hai dễ
trượt hơn vì nó nghe như sự thận trọng. Thứ **còn** dùng được là **so sánh giữa
các model**, vì mọi model nhận cùng payload; thứ **mất** là mọi ngưỡng đặt theo
hành vi sản phẩm (`≥45/50` ở đây) — ngưỡng ấy nói về sản phẩm, không nói về
model trần.

---

## Luật 14 — HAI NGƯỜI ĐO ĐỘC LẬP RỒI SO **SỐ**, và cấm hoà ở tầng KẾT LUẬN

> Nguồn: 17/08. **Năm** cặp số lệch trong một ngày, năm vùng khác nhau, năm cặp
> vai khác nhau. **Không cặp nào bị bắt bởi một người tự kiểm.**

    lược đồ tool   chuẩn-hoá 4129d298555c   vs  file-thô 76273c1ef838
    .env           sha256 db1965367fa0      vs  md5 9d3d3c79e48e
    mô tả tool     thô 4.862                vs  bỏ-thụt-dòng 4.334
    contracts/     9 trường 612             vs  5 trường 241
    lược đồ gửi đi bộ đo 7.172              vs  app 6.773

Lớp lỗi *"đọc kích thích qua một đại diện thay vì đọc chính nó"* (Luật 13/13b)
**không chết vì bị đặt tên.** Hôm nay nó bắt tôi ba lần và security ba lần —
kể cả **ngay sau** khi mỗi người vừa tự tay viết ra luật cấm chính nó.

### Vế thi hành, và đây là chỗ dễ trượt nhất

**Phải so SỐ. Cấm hoà ở tầng KẾT LUẬN.**

Ca thật, và người suýt phạm là bên đang đúng về mọi thứ khác: vụ `4.862` vs
`4.334` suýt đóng bằng câu

> *"hai cách đếm khác nhau thôi, lấy bản của tester."*

Câu đó ở tầng **kết luận**. Nó nghe hợp lý, nó đúng về mặt hành động (bản của
tester đúng là bản nên dùng), và **hai bên cùng yên**. Nó cũng **che mất** gốc
thật: `langchain-core` **1.5.4 giữ thụt đầu dòng docstring, 1.5.3 gỡ** — mọi
delta chia hết cho 8 = số dòng tiếp nối × 8 dấu cách. Tức **văn bản gửi cho
model là hàm của phiên bản một thư viện phụ thuộc**, mà `requirements.txt` ghi
`langchain>=0.3.0` — sàn, không lockfile. Dựng lại image ngày khác đổi prompt,
**im lặng, không commit nào, không diff nào**.

Thứ cứu được finding đó là **một bên từ chối cách hoà** và đòi so tiếp ở tầng
số cho tới khi ra nguyên nhân.

> **Một luật "hai người cùng đo" mà thiếu vế "cấm hoà ở tầng kết luận" sẽ tự vô
> hiệu ngay lần đầu hai người lịch sự với nhau.**

### Ba dấu hiệu đang hoà thay vì đang đo

1. Câu chốt chứa *"hai cách đếm"*, *"tuỳ định nghĩa"*, *"đằng nào cũng…"* mà
   **chưa ai chỉ ra được phép biến đổi cụ thể** biến số này thành số kia.
2. Kết luận **giữ nguyên hành động** của cả hai bên — không ai phải sửa gì.
3. Không ai hỏi *"nếu đúng là cách đếm khác, thì cách đếm nào, và nó ra đúng
   con số kia chứ?"* — ở đây phép thử là `strip` từng dòng, và nó cho **3/5
   khớp CHÍNH XÁC**, đó mới là bằng chứng.

### Và vế phòng, mạnh hơn cả hai vế trên

**Phép đo không thể sai theo lớp này là phép đo KHÔNG DỰNG LẠI GÌ.** Cả năm
lỗi trên đều sinh từ việc *dựng lại* thứ sản phẩm gửi — prompt tự soạn, mật độ
đo trên phần đang chú ý, runtime khác, lược đồ phồng, mốc thời gian trôi. Khi
câu hỏi là *"sản phẩm hành xử thế nào"*, đo qua **chính cửa sản phẩm**, dù đắt
hơn. Bộ đo dựng-payload giữ đúng việc nó làm tốt: **so model với model**.

---

## Luật 15 — DẤU VẾT của bộ đo, không phải độ chính xác của nó

> Nguồn: 17/08, lượt đo đầu tiên qua `/api/agent-chat`. Tôi xin PO một lượt để
> biến ước thành đo, PO duyệt, tôi bắn — rồi security chỉ ra thứ **cả hai chúng
> tôi đều không nghĩ tới**: đường đó **GHI DỮ LIỆU THẬT**.

Mười bốn luật trước đều canh **một** câu hỏi: *phép đo có đúng không?* Không
luật nào hỏi câu thứ hai: ***phép đo để lại gì sau khi chạy xong?***

    bộ đo dựng-payload   gọi API nhà cung cấp        → không chạm hệ ta
    đường THẬT           chạy đủ vòng ReAct          → GHI vào hệ đang chạy

Một lượt **thành công** ở ca điều tra kết thúc bằng `create_ticket`, tức ghi vào
`complaints` · `tickets` · `investigation_logs` · `tool_results` · `messages`.

### Ba mức thiệt hại, nặng dần

**① Làm bẩn hàng chờ vận hành.** `k=10 × 2 ca` = tới **20 khiếu nại giả** người
thật nhìn thấy — ngay trước buổi test 150 người. Không phân biệt được vé đo với
vé thật ⟹ buổi test bắt đầu trên một hàng chờ đã bẩn, và **không ai biết số nào
của buổi đó là thật**.

**② Bơm dữ liệu máy sinh vào bảng BẰNG CHỨNG.** `complaints.description_raw`
thuộc nhóm *lời khai = bằng chứng* (ADR-025). Cả thiết kế nhóm đó dựng trên một
mệnh đề: **mọi dòng ở đây đều do một người thật gõ** — đó là lý do ADR-025 bác
che-lúc-ghi cho nhóm này. Thêm lời khai **chưa từng có người nào khai** là cùng
một tổn hại, đi từ cửa khác.

> Với một bảng mà giá trị duy nhất là *"không ai sửa, không ai thêm"*, việc ghi
> vào nó phải là quyết định **cố ý** — không bao giờ là **tác dụng phụ của một
> phép đo**.

**③ Không hoàn tác được bằng cách chạy lại.** Một bộ đo sai thì chạy lại là
xong. Một bộ đo đã ghi thì phải **dọn**, và dọn cần biết **đã ghi gì**.

### Bốn điều kiện, thoả TRƯỚC lượt đo — kể cả lượt thăm dò

1. **Ngăn xếp không lộ ra ngoài.** Nếu không xác định chắc chắn được ⟹ **DỪNG,
   hỏi người thật.** Cổng mở trên máy **không** đồng nghĩa ra được Internet, và
   `SITE_DOMAIN` rỗng ở mọi ngăn xếp thì **không** định danh được cái nào.
2. **Tài khoản hạt giống**, khai trong hồ sơ đo. Không bao giờ tài khoản người
   thật, kể cả của PO.
3. **Bản ghi đo phân biệt được** — tiền tố quy ước trong trường lời khai + mốc
   thời gian — và **chốt cách dọn TRƯỚC khi bắn**, không phải sau.
4. **Liệt kê KHO trước, rồi đếm TỪNG kho** — trước và sau.

**Điều kiện 4 là điều kiện tôi vi phạm**, và cách tôi vi phạm nó đáng ghi: tôi
đếm **sau**, không đếm **trước**. Lần này thoát vì hoá ra không có gì để dọn —
`create_ticket` chưa từng chạy, cửa OTP chặn trước. Nhưng *"không có gì để dọn"*
là thứ tôi biết **sau khi** bắn, không phải trước.

> **Không đếm trước thì không dọn được, và không CHỨNG MINH được là đã dọn.**

#### 4a — đếm **mọi kho**, không đếm kho mình nghĩ tới

Tôi đếm sạch **bảy bảng trên hai Postgres** và báo *"0 dòng"*. Đúng số, **thiếu
phạm vi**: lượt đo có ghi **Redis** — một vé phiên `refresh:` sống **7 ngày**.
Mức thấp (tự hết hạn, không chạm bảng bằng chứng), nhưng kết luận *"không để
lại gì"* thì sai.

Danh mục tối thiểu cho một lượt qua API sản phẩm:

    Postgres · Redis (phiên · refresh · rate-limit · concurrency)
    kho vector (nếu chạm nạp) · log & trace (tệp, Jaeger)
    PHÍA NHÀ CUNG CẤP — token đã tiêu, VÀ bản ghi input/output phía họ

Đây là **khuôn mặt thứ ba trong một ngày** của cùng một luật (13b): đo **trọn
vẹn** thứ mình đang nói tới, không đo **phần mình đang chú ý**. Sáng: kích thích
gửi cho model. Trưa: runtime sinh ra nó. Chiều: kho trạng thái nó chạm.

#### 4b — 🔴 trên hệ DÙNG CHUNG, phép đếm trước/sau KHÔNG quy được trách nhiệm

Đây là lỗ trong chính điều kiện 4 ở trên, và nó lộ ra ngay khi đo lần hai:

    05:15:54   vé phiên của TÔI
    05:24:10 → 05:25:18   TÁM vé phiên khác, không phải của tôi
    và các khoá rate-limit sống ~15s — có người đang đăng nhập ngay lúc đo

Kho có **14 khoá** lúc tôi đếm, **1 khoá** lúc người khác đếm tám phút trước.
Không ai sai — **đại lượng biến thiên theo thời gian trên một hệ có nhiều
người dùng**.

> **`sau − trước` chỉ quy được trách nhiệm khi KHÔNG AI KHÁC ghi xen vào.** Trên
> một ngăn xếp dùng chung, hiệu số đó gộp việc của tôi với việc của mọi phiên
> khác, và nó **không có cách nào tách ra**.

**Cách chữa — quy trách nhiệm bằng DẤU, không bằng HIỆU SỐ:**

- ghi bằng **tài khoản hạt giống riêng**, rồi lọc theo tài khoản đó
- **tiền tố quy ước** trong trường lời khai + mốc thời gian
- với kho không có chỗ gắn dấu (vé phiên, khoá rate-limit): ghi lại **định danh
  cụ thể** tạo ra lúc đo (mã vé, mã khoá), không dựa vào việc đếm

#### 4c — 🔴 và thủ phạm hoá ra là CHÍNH BỘ TEST NÀY

Vé phiên tôi cố ý giữ lại làm bằng chứng **biến mất trong ba phút**. Kết luận
đầu tiên của cả đội là *"có người xoá tay"*. Redis tự khai số khác:

    cmdstat_flushdb: calls=437

Nguồn: `tests/conftest.py` — fixture `autouse=True` gọi `flushdb()` **trước mỗi
test**. Docstring của nó nói *"fakeredis trong test"*, nhưng đó là một **giả
định**, không phải ràng buộc: `flushdb()` gọi vào **bất cứ client nào**
`get_default_client()` trả về. Chạy `docker exec <backend> pytest` thì
`REDIS_URL=redis://redis:6379/0` — **Redis thật của ngăn xếp**.

> **Fixture chạy THÀNH CÔNG trong cả hai trường hợp.** Không đỏ, không cảnh
> báo. Nó chỉ **im lặng làm một việc khác hẳn** khi biến môi trường đổi — và
> việc khác đó là cuốn sạch phiên đăng nhập của mọi người đang dùng ngăn xếp.

Đây là **cùng họ với `restart` / `recreate` / `rebuild`**: lệnh yếu hơn vẫn chạy
xong và vẫn báo xanh.

**Cách chữa: cổng NỔ, không cổng BỎ QUA.** Bỏ qua sẽ trả lại đúng chỗ rò rỉ
state mà fixture sinh ra để chặn, rồi ta có một suite xanh vì lý do sai. Và cổng
phải chứng minh **cả hai chiều** (Luật 2):

    REDIS_URL=fake://ci          → 23/23 invariant XANH      (không chặn nhầm)
    trong container, Redis thật  → RuntimeError, flushdb=437 KHÔNG tăng  (chặn thật)

**Bài học rộng hơn ca này:** một bộ đo có-ghi nguy hiểm nhất **không phải** ở
lượt đo — mà ở **hạ tầng test của chính mình**, thứ chạy hàng trăm lần mà không
ai coi là "một phép đo".

**Và bán kính của nó không trùng với vật đang đo.** `test_dua_refresh_token.py`
đo ngăn xếp **ttl** qua HTTP (`FIN05_TEST_BASE_URL=…:8443`), nhưng fixture
`autouse` xoá Redis mà **`REDIS_URL` của tiến trình pytest** trỏ tới — một ngăn
xếp **khác**. Đo được:

    fin05-redis-1     flushdb=437 · dbsize 0     ← NGƯỜI NGOÀI CUỘC, bị xoá sạch
    fin05ttl-redis-1  flushdb=0   · dbsize 22    ← ngăn xếp ĐANG ĐƯỢC ĐO, nguyên vẹn

> Fixture phá **thứ không ai đang nhìn**, và tha **thứ đang được đo**. Nên thiệt
> hại không xuất hiện trong kết quả của người chạy test — nó xuất hiện trong
> công việc của **người bên cạnh**, ở một thời điểm không ai nối lại được với
> lệnh đã gây ra nó.

#### 4d — QUAN SÁT và THỰC THI là hai việc; đừng dùng công cụ của việc sau cho việc trước

Suốt ngày 17/08 cả đội nhắc nhau một lời khuyên **đúng**: *kiểm trong container,
đừng tin runtime mượn* — chính nó gỡ được vụ `langchain-core` 1.5.3/1.5.4.

Rồi hoá ra `docker exec <backend> pytest` **chính là cách người ta làm đúng lời
khuyên đó**, và cũng là **cách duy nhất kích hoạt** vụ 437 lần. Người chạy nó
làm đúng cả lời khuyên lẫn hiến pháp §7.

> **Chạy trong container để ĐỌC trạng thái thật là đúng. Chạy BỘ TEST trong
> container thì bộ test mang theo đồ nghề dọn dẹp của nó.** Quan sát và thực thi
> là hai việc — công cụ của việc sau không được dùng cho việc trước.

Muốn đọc trạng thái thật trong container: dùng `python -c` một dòng, `redis-cli`,
truy vấn chỉ-đọc. **Đừng** gọi `pytest`, vì fixture của nó tồn tại để **dọn**,
và nó sẽ dọn thứ nó gặp.

#### 4e — hai chiều hỏng, và chiều KHÔNG có triệu chứng mới là chiều nguy

    phiên · vé refresh bị cuốn      → phép đo GÃY        → ĐỎ, thấy ngay
    bộ đếm tích luỹ bị cuốn         → ngưỡng đặt lại 0   → 🔴 XANH GIẢ, im lặng

Một test *"gửi quá hạn mức phải bị chặn"* mà bộ đếm bị cuốn giữa chừng sẽ **PASS
vì lý do sai** — đúng họ Luật 1, và đúng các chốt ta quan tâm nhất: rate-limit,
cost guard, độ tươi OTP.

**Và không loại trừ được bằng lập luận:** `INFO commandstats` chỉ có **tổng**,
không có mốc thời gian ⟹ không định vị được 437 lần đó trong thời gian. Chỉ có
hai đường: **chạy lại**, hoặc **chứng minh mình chưa từng đo đại lượng đó**.

Đường thứ hai rẻ hơn nhiều khi nó đúng, nhưng phải chứng minh bằng **rà bản
ghi**, không bằng trí nhớ. Ở đây là năm phép rà độc lập, tất cả trống: không
file kết quả nào chứa trường trạng thái Redis · không file nào chứa trường bộ
đếm tích luỹ · không tệp đo nào vừa nhắc ba đại lượng đó vừa gọi HTTP vào ngăn
xếp bị ảnh hưởng · 81 file kết quả không có 401/403 nào · và ca ép 429 nằm sau
một cờ chưa từng bật.

Và hệ quả vận hành, đáng nói riêng: **một ngăn xếp đang có người khác dùng thì
không phải chỗ để chạy phép đo có ghi.** Không chỉ vì lẫn số — mà vì phép đo
tiêu hạn ngạch, đụng rate-limit, và làm hỏng phép đo của người bên cạnh.

### Và cái bẫy ngay sau đó: số 0 làm lời bào chữa

Tôi đếm ra **0 dòng mới ở cả hai CSDL, mọi bảng**. Rất dễ dừng ở đó và coi như
không có chuyện gì. Nhưng lượt của tôi **chết ở cửa OTP** — nó không đại diện
cho lượt sẽ chạy thật.

> **Số 0 nói *"lượt bị chặn thì không ghi"*. Nó không nói *"đường này an
> toàn"*.** Lượt THÀNH CÔNG mới là lượt kết thúc bằng `create_ticket`, tức đúng
> lượt sẽ ghi.

Cách kiểm cũng phải chặt hơn `count(*) = 0` — đó là một số **trùng với trạng
thái mặc định** (Luật 1). Phải đọc `max(<cột thời gian>)` **từng bảng** và xác
nhận mốc mới nhất nằm **trước** lượt đo, mới loại được khả năng *"đã ghi rồi bị
dọn"*.

### Vế cuối, thuộc về người thiết kế phép đo

Khi câu hỏi buộc phải đo trên đường thật, **đừng bỏ đường thật** — nó là **sự
thật nền duy nhất**. Hãy trả **giá của việc đo đúng chỗ**: tài khoản hạt giống,
quy ước đánh dấu, kế hoạch dọn, và một lần hỏi người thật trước khi bắn phát
đầu tiên.

---

## Luật 16 — N mệnh đề cần N ĐỘT BIẾN, mỗi cái làm đúng MỘT tập con đỏ

> Nguồn: 17/08, nghiệm thu bộ test canh lớp cô lập Redis của `conftest.py`.

Ba test viết ra để canh **ba** mệnh đề. Chúng xanh cả ba — chưa chứng minh gì
(Luật 1). Nên chạy hai đột biến:

    A · ÉP → setdefault (đúng lỗi gốc)   ⟹ cả 3 ĐỎ
    B · cổng luôn trả "an toàn"          ⟹ CHỈ test canh cổng đỏ
                                            hai test canh lớp 1 VẪN XANH

**B là phép thử đắt nhất, và nó không nhắm vào bản vá — nó nhắm vào bộ test.**
Nếu cả ba cùng đỏ ở B thì ba test đang **đo lẫn nhau**, không đo ba mệnh đề
riêng.

> Một bộ test như thế **vẫn xanh, vẫn trông đầy đủ**. Thứ nó mất là khả năng
> nói cho ta biết **CÁI GÌ** hỏng vào ngày nó đỏ — ta chỉ biết *"có gì đó
> hỏng"*, đúng lúc cần biết nhất.

**Luật:** một bộ test chỉ chứng minh được nó đo `N` mệnh đề khi có `N` đột
biến, **mỗi đột biến làm đúng một tập con dự kiến đỏ**. Cả bộ cùng đỏ ở mọi đột
biến là dấu hiệu chúng đo **một** thứ, không phải `N` thứ.

Đây là bậc trên của Luật 2 và Luật 1: hai luật đó áp cho **một** phép thử (nó
có hiệu lực không · có quá rộng không). Luật 16 áp cho **quan hệ giữa các phép
thử** — chúng có độc lập với nhau không.

### Vế kèm: test canh một cái cửa không được tự mình mở đúng cái cửa đó

Test canh cổng phải dựng một client thật **GIẢ ĐỊNH** (monkeypatch), tuyệt đối
không nối vào một Redis nào. Làm ngược lại thì test-canh-`flushdb` trở thành
thứ tiếp theo cuốn Redis của người bên cạnh — **công cụ kiểm trở thành thứ nó
đi kiểm**.

Cùng họ với một ca đã có trong dự án: công cụ soi kho tự tạo ra một kho rỗng
rồi báo *"kho trống"*.

### Và vế thứ ba: kiểm Ý ĐỊNH khác kiểm KẾT QUẢ

Trong ba test trên, hai test cùng canh "lớp 1" nhưng **không** trùng nhau:

    test 1  REDIS_URL == "fake://…"                → kiểm Ý ĐỊNH  (đã đặt chưa)
    test 2  client toàn cục thực sự là fakeredis   → kiểm KẾT QUẢ (đã ăn chưa)

Biến đúng mà client vẫn thật là **hoàn toàn có thể** — khi `conftest.py` được
nạp sau module đầu tiên chạm `src.config`. Đó chính là `hiện-diện ≠ hiệu-lực`,
lần này ở tầng fixture. Bỏ test 2 vì *"trùng test 1"* là bỏ đúng cái đo được
khoảng hở giữa hai thứ đó.

**Và test 2 phải đo trên ĐÚNG cửa mà thứ được canh sẽ dùng** — ở đây là
`get_default_client()`, chính hàm `flushdb()` gọi vào. Đo qua một đường khác,
dù tương đương về lý thuyết, là quay lại Luật 13: đo một vật gần giống vật thật.

---

## Luật 17 — CHE THEO VẬT, không che theo MẪU mình tưởng

> Nguồn: 17/08, và cái giá là một khoá API thật. Lỗi của tôi.

Tôi in biến môi trường của container để xem model nào đang chạy, có che:

```bash
env | grep -iE "^LLM_|^OPENAI_BASE|MODEL" | sed "s/=.*key.*/=***/I"
```

Regex đó khớp trên **giá trị**. Giá trị của `LLM_API_KEY` không chứa chuỗi
`key`, nên nó **không khớp** — và khoá in ra nguyên văn.

Điều làm nó đáng ghi: **ngay dòng bên cạnh tôi làm đúng.** Cùng lệnh, tôi cắt
`OPENAI_API_KEY` bằng `cut -c1-12` và chỉ lộ 12 ký tự vô hại. Tôi **biết** cách
đúng, và vẫn hỏng ở dòng kế — vì hai dòng đó dùng hai **cách nghĩ** khác nhau.

> **Một regex đoán hình dạng bí mật LÀ một danh sách cấm.** Và danh sách cấm
> hỏng ở đúng thứ nó chưa từng thấy — tức đúng thứ ta cần nó bắt.

**Hai cách đúng, điểm chung là KHÔNG đoán hình dạng giá trị:**

1. **Che theo TÊN** — liệt kê `*_API_KEY` · `*_SECRET*` · `*_TOKEN*` ·
   `*PASSWORD*` rồi che vế phải, bất kể giá trị trông thế nào.
2. **Che theo VỊ TRÍ** — `cut` **mọi** giá trị xuống vài ký tự đầu, rồi mới mở
   ra đúng thứ cần đọc.

Cả hai là **danh sách CHO PHÉP**. Danh sách cho phép hỏng theo hướng **phiền**
(che nhầm thứ vô hại, thấy ngay, sửa một dòng); danh sách cấm hỏng theo hướng
**im lặng** (để lọt thứ nhạy cảm, không ai thấy).

### Vì sao luật này nằm trong chuẩn viết TEST

Bộ đo là thứ **in ra nhiều nhất** trong dự án: nó dump env để khai runtime,
dump cấu hình để khai phạm vi, dump payload để khai kích thích. Chính kỷ luật
*"khai đủ để vai khác bác được"* (Luật 5) là thứ **đẩy** ta in nhiều hơn — và
mỗi lần in là một cơ hội lộ.

> **Luật 5 và Luật 17 kéo ngược chiều nhau, và cả hai đều đúng.** Chỗ hoà là:
> khai **TÊN** và **BĂM** của bí mật, không khai **giá trị**. Băm đủ để đối
> chiếu hai lượt chạy dùng cùng khoá hay không — đúng thứ ta cần — mà không
> mang theo khoá.

### Và vế cùng họ, gặp lần thứ ba trong ngày

Cùng ngày, hai chỗ khác hỏng đúng hình dạng này:

    except RateLimitError:        bắt theo TÊN NGOẠI LỆ
                                  trong khi thứ cần xử là TRẠNG THÁI
                                  "nhà cung cấp không phục vụ lượt này"
                                  ⟹ 403 hết hạn mức · 401 khoá sai · 5xx
                                     đều rơi ra ngoài, thành HTTP 500

    sed "s/=.*key.*/…"            bắt theo HÌNH DẠNG GIÁ TRỊ
                                  trong khi thứ cần che là VAI TRÒ của biến

Cùng một sai lầm: **bắt theo cái mình nhận ra được, thay vì theo cái mình cần
xử lý.** Cách chữa cũng cùng một hình: liệt kê **cái được phép đi qua**, mọi
thứ khác vào nhánh an toàn.

---

## Luật 18 — BĂM phải khai TÊN THUẬT TOÁN

> Nguồn: 17/08. Lần thứ ba trong ngày cùng lớp lỗi, và lần này nó lọt qua
> **chính quy ước đặt ra để chặn nó**.

    cùng một file, 6.305 byte
      md5    = 1edd51dff555     ← một bên công bố
      sha256 = 742df94b195a     ← bên kia đo

Hai người đọc hai con số, **nhìn giống hệt nhau** — cùng 12 ký tự hex — và
không ai kiểm. Quy ước dự án ghi *"sha256, lấy 12 ký tự đầu"*; một bên dùng
md5; con số vẫn **trông hợp lệ**.

> **`1edd51dff555` không phải một băm. `md5:1edd51dff555` mới là.**
> Một chuỗi hex **không tự khai nó sinh ra từ đâu** — và đó là toàn bộ vấn đề.

Nó cùng họ với `4.862 vs 4.334` (hai runtime) và `120 ca vs 124 câu` (hai đơn
vị đếm): **con số đúng, phép đo không định danh được.** Nhưng nó tệ hơn hai ca
kia ở một điểm — băm sinh ra **để** định danh. Một băm không định danh được
chính nó là công cụ tự phủ định.

### Khai cái gì

Không chỉ tên thuật toán. Phải đủ để **người khác tái lập được con số**:

    thuat_toan_bam: "sha256[:12] của json.dumps(obj, ensure_ascii=False,
                     indent=1, sort_keys=True) SAU KHI bỏ hai khoá
                     'bam_nhan' và 'thuat_toan_bam'"

Biết `sha256` mà không biết **thứ tự khoá** hay **khoá nào bị loại** thì vẫn
không tái lập được. Tên thuật toán là điều kiện cần, không phải đủ.

### Mẹo: khai mà KHÔNG đổi băm đã công bố

Vấn đề thực tế: nhãn đã băm và **đã có con số gắn với băm đó**. Thêm một trường
vào là đổi băm, và mọi con số đã công bố **mất chỗ neo**.

Cách gỡ: cho trường khai báo **nằm ngoài phần được băm** — loại nó cùng với
`bam_nhan` trước khi tính. Bốn nhãn của dự án này được bổ sung lời khai theo
cách đó, băm **không đổi một ký tự**.

> Thứ tự đúng khi sửa một quy ước băm: **tìm cách khai mà không đụng băm
> trước**, chỉ băm lại khi không còn cách nào — vì mỗi lần băm lại là một lần
> mọi con số cũ phải được đọc lại xem còn thuộc về đâu.

### 12b — XẾP HẠNG TRÊN MỘT TRỤC là nói dối mà không sai chữ nào

> Nguồn: 17/08, buổi bàn tối ưu token. Lỗi của PO-agent, họ tự khai.

Phát hiện *"cached token có thể vẫn đếm vào TPM"* dẫn tới một xếp hạng:
prompt-cache **mất giá**, semantic-cache **lên giá**. Từng vế đều đúng **trên
trục thông lượng**. Bảng xếp hạng không sai một chữ nào.

Nhưng hai vật đó khác nhau **chính ở một trục thứ hai** không được nhắc:

    prompt-cache hit    → khách nhận câu trả lời CỦA CHÍNH LƯỢT ĐÓ.  rủi ro ~0
    semantic-cache hit  → khách nhận câu trả lời CỦA MỘT KHÁCH KHÁC. 🔴 ràng buộc cứng 3

> **Xếp hạng trên một trục, giữa hai vật khác nhau ở trục KHÁC, là một kết luận
> đúng dùng để trả lời sai câu hỏi.**

Điều làm ca này đáng ghi: **mọi rào cho trục thứ hai đã nằm sẵn trong thiết kế**
— shadow mode, bộ ca ranh giới, cổng an-toàn-cache-miss. Không ai thiếu công cụ.
Thứ thiếu là **một câu trong lời trình**.

> **Đó là cách một thiết kế tốt bị triển khai tồi: người trình nói về LỢI ÍCH,
> người nghe không nghe thấy ĐIỀU KIỆN.** (PO-agent tự khai, nguyên văn.)

**Vế thi hành — NẾP KHAI TRỤC, phê chuẩn 17/08:** mọi phát biểu **xếp hạng**
khi trình phải kèm một dòng

    xếp trên trục X · CHƯA XÉT trục Y

kể cả khi trục Y làm phương án mình đang nghiêng về trông xấu đi. Không đủ chỗ
cho dòng đó thì **đừng xếp hạng** — nêu **điều kiện** thay vì nêu **thứ tự**.

Lý do nếp này cần tồn tại riêng, không gộp vào việc kiểm số:

> **`số-đúng-phạm-vi-sai` KHÔNG bị bắt bởi kiểm số — vì số vẫn đúng.** Nó chỉ
> bị bắt bởi một câu hỏi khác hẳn: *"đứng trên trục nào, và trục nào chưa nói?"*

Cả ba lần đính chính trong ngày 17/08 đều thuộc họ này, và không lần nào bị bắt
bởi việc đọc lại con số.

Và có một dạng câu **miễn nhiễm** với lỗi này, đáng học riêng: câu chỉ nói phần
**không phụ thuộc ẩn số**.

    ✗ "semantic cache lên hạng, prompt cache xuống hạng"
      → phụ thuộc một câu trả lời chưa có, và giấu trục rủi ro

    ✅ "T2 là nhánh DUY NHẤT nên hoãn tới khi nhà cung cấp trả lời. Mọi nhánh
       khác quyết được ngay, và thứ tự không đổi vì câu trả lời đó."
      → không xếp hạng gì, và làm được việc của cả bảng xếp hạng

Câu thứ hai **không thể sai** theo hướng ca này, vì nó không đứng trên ẩn số.

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
5. **Con số này đã có ai đo độc lập bằng đường KHÁC chưa?** Chưa → chưa phải
   bằng chứng. Và nếu hai số lệch, **cấm hoà bằng "hai cách đếm khác nhau"**
   khi chưa ai chỉ ra phép biến đổi cụ thể đưa số này thành số kia → vi phạm
   Luật 14.
6. **Phép đo này GHI gì vào hệ đang chạy?** Có ghi → bốn điều kiện Luật 15
   phải thoả TRƯỚC lượt đầu tiên, kể cả lượt thăm dò. Không xác định được ngăn
   xếp có lộ ra ngoài hay không → DỪNG, hỏi người thật.
7. **Bộ test này đo mấy mệnh đề, và đã chạy đủ ngần ấy đột biến chưa?** Cả bộ
   cùng đỏ ở mọi đột biến → chúng đo MỘT thứ, không phải N thứ → vi phạm
   Luật 16.
8. **Bộ đo đưa vào ĐÚNG kích thích sản phẩm dùng chưa?** Với mỗi kênh (system
   prompt · mô tả tool · lược đồ tham số) phải kê được **nguồn**, không phải
   độ dài. Kê không được → vi phạm Luật 13, và kết luận câm theo **cả hai**
   chiều.

---

## LUẬT 19 — Khả năng QUAN SÁT có thể bị chính cơ chế xử lý lỗi của hệ xoá đi

*(Đo được 18/08, trong lúc vá 6 cổng `eval/QUET-TEN-HUA-KHAC-ASSERTION.md`.)*

Luật 1 canh *"assertion có phân biệt được không"*. Luật 19 canh một tiền đề
**nằm trước** cả Luật 1: **vật có còn ở đó để mà đọc không.**

**Ca thật.** Bốn ca duyệt HITL, cùng khuôn: dựng resolution → gọi `/approve`
sai điều kiện → nhận 403 → đọc CSDL xác nhận không có gì bị duyệt. Ba ca xanh.
Ca thứ tư báo `sample_db.get(...) is None` — **hàng biến mất**.

Cơ chế: fixture `client` dùng **CHUNG session** với route, và dependency
`_override_session` **rollback** khi route ném `HTTPException`. Hạt giống chưa
commit ⟹ chính cú rollback của **đường lỗi đang được kiểm** cuốn luôn vật cần
đo. Cổng càng làm đúng việc, vật càng biến mất sạch.

> 🔴 **Phần nguy hiểm không phải ca đỏ — là ba ca xanh.** Chúng quan sát được
> vì tình cờ có một request **thành công** (`request-approval-otp`) commit hộ
> trước đó. Tức **chúng đọc được nhờ MAY, không nhờ thiết kế.** Vá riêng ba ca
> ấy thì cả ba xanh, và ta báo "đã canh" cho một khuôn không tự đứng được —
> tới ngày ai đó viết ca thứ tư theo cùng khuôn, nó im.

**Vì sao khó thấy:** ba ca xanh **không có triệu chứng nào**. Không có gì để
nghi. Ca thứ tư chỉ khác ở một chi tiết trông vô hại — nó không cần xin OTP
trước — và chính chi tiết ấy gỡ mất cái commit vô tình.

### Quy tắc

1. **Hạt giống của một ca kiểm ĐƯỜNG LỖI phải được commit tường minh.** Đường
   lỗi gần như luôn kéo theo rollback; hạt giống sống nhờ transaction của
   chính nó là hạt giống sống nhờ may.
2. **Đuổi cache trước khi đọc** (`expire_all()` hoặc tương đương) khi test và
   mã sản phẩm dùng chung session. Không đuổi thì ta đọc **đối tượng trong bộ
   nhớ**, không đọc **hàng trong CSDL** — hai thứ khác nhau đúng lúc quan
   trọng nhất. *(Repo này đã mất một bug thật vì điều đó, 10/08.)*
3. **Trạng thái thứ ba là bắt buộc ở đây, không phải tuỳ chọn.** Helper phải
   phân biệt *"đọc được, và nó ĐÚNG"* với *"không đọc được"*. Gộp hai thứ
   thành TRƯỢT sẽ đẩy cả đội đi truy một vụ thủng ràng buộc cứng **không tồn
   tại** — đúng điều suýt xảy ra ngày 18/08.
4. **Khi N ca cùng khuôn mà chỉ một ca lộ vấn đề, đừng vá ca đó — hỏi vì sao
   N-1 ca kia KHÔNG lộ.** Câu trả lời gần như luôn là một điều kiện ngẫu nhiên
   mà không ai khai, và nó sẽ hết hiệu lực lặng lẽ.

---

## LUẬT 20 — Smoke RÚT GỌN vẫn phải có ÍT NHẤT MỘT hành trình NHIỀU LƯỢT

*(Đo được 19/08, GĐ4 — PO thật tự chạy kịch bản A trên UI thật, tự bắt 5 lỗi
mà bốn ô nghiệm thu GĐ3, kể cả ô ④ smoke UI vừa xanh, không ai bắt được.)*

Ô ④ smoke UI (chào nhẹ + một câu nặng) chạy **mỗi bước MỘT lượt độc lập** —
đăng nhập, chào, một câu tra cứu, hết. Xanh sạch. Và xanh sạch đó **không nói
được gì** về bốn trong năm lỗi PO thật vừa gặp: OTP xen giữa làm mất câu hỏi
cũ, hai mã trong một câu chỉ tra được một, ngữ cảnh tích luỹ qua nhiều lượt —
**tất cả chỉ hiện ra từ lượt thứ hai của một hành trình liên tục trở đi.**

> Một smoke một-lượt-mỗi-bước đo được *"từng bước có chạy không"*, không đo
> được *"cuộc hội thoại có sống sót được không"*. Hai câu hỏi khác nhau, và
> câu sau mới là câu khách thật sẽ hỏi — không ai chỉ gõ đúng một câu rồi
> dừng.

**Quy tắc:** dù smoke bị rút gọn tới đâu vì thời gian/ngân sách (đúng tình
huống GĐ4 — PO thật sắp tự vào UI, cần kết quả trong vài phút), **vẫn phải
giữ lại ít nhất MỘT ca hành trình nhiều lượt** — cùng một phiên, cùng một
luồng hội thoại, ≥2 lượt gửi liên tiếp có phụ thuộc lẫn nhau (lượt sau cần
ngữ cảnh/trạng thái của lượt trước: OTP xen giữa, nhiều mã trong một câu,
hỏi tiếp dựa trên câu trả lời trước). Cắt số ca, cắt số lượt còn lại — nhưng
đừng cắt tới mức không còn ca nào có TRỤC NHIỀU LƯỢT, vì đó chính là trục nơi
lỗi thật đang sống.

## Luật 21 — Cổng CỐ Ý ĐỎ: đừng nới, đừng xoá

*(20/08 — PO-agent gặp một ca đỏ (`test_do_phu_nhan_du_lieu_demo.py`), không
biết mới hay cũ, phải đi `git log` mới trả lời được. `grep -rl` xác nhận
KHÔNG tài liệu nào khai nó tồn tại. Một vật chứng không có khẳng định đi kèm
— họ hàng ngược của Luật X — làm người sau phát hiện lại từ đầu, và người
không biết hỏi ai thường kết thúc bằng cách NỚI cổng cho xanh.)*

Mỗi dòng dưới đây: **vì sao đỏ · vá bằng cách nào · vá thế nào là SAI.** Chỉ
liệt kê thứ đã tra được (`git log`, chạy trực tiếp, đọc docstring/marker) —
không liệt kê theo trí nhớ.

| Cổng | Vì sao đỏ | Vá bằng | Vá SAI là |
|---|---|---|---|
| `tests/test_data/test_do_phu_nhan_du_lieu_demo.py` | Nợ độ phủ nhãn enum trong dữ liệu demo — 5 nhãn (`chat_sessions.status=waiting/active`, `policy_documents.status=processing/failed`, `wallets.status=closed`) không có dòng demo nào mang. `git log`: sinh ra ĐỎ 20 nhãn (`3684570`), nay còn 5 — nợ đang trả dần, không phải hồi quy. | **SINH THÊM dữ liệu demo** cho 5 nhãn trên (script `gen_dataset.py`/tương đương) | Sửa/nới assertion, hoặc thêm nhãn vào danh sách miễn trừ mà không thực sự sinh dữ liệu — assertion tự khai nguyên văn: *"Bản vá là SINH DỮ LIỆU DEMO, KHÔNG phải nới cổng này"* |
| `tests/test_api/test_live_chat_pii_gap.py` | `@pytest.mark.security_finding`, P0 chưa vá — `live_chat.py::record_message` lưu nguyên văn SĐT/STK khách gõ tay vào live-chat, không qua scrub/mask nào trước khi lưu (khác luồng AI, đã có `scrub_pii`/`masking.py`). | Một **quyết định của PO** về mức che phù hợp (không được che tới mức CSKH mất khả năng gọi lại khách) — không phải việc kỹ thuật đơn thuần, xem `docs/FIN05-Feature-Inventory-Security-Review.md §6` | Tự chọn mức che rồi vá thẳng `record_message` mà chưa có quyết định PO — hoặc gỡ `security_finding` marker để job CI hết đỏ mà chưa vá thật |

**Đã kiểm, KHÔNG đưa vào bảng trên (loại có chủ đích):**
- `tests/test_security/test_jwt_revocation.py`, `tests/test_security/test_security_answer_hash.py` — cũng mang `@pytest.mark.security_finding`, nhưng chạy trực tiếp [ĐO 20/08] cả hai **ĐANG XANH** — finding đã vá, marker là dấu vết lịch sử, không phải cổng đang cố ý đỏ.
- `tests/test_agents/test_f31_f32_duong_agent_that.py` — [ĐO 20/08] `5 skipped`, không phải đỏ — bị `skipif` bởi cổng chi phí (`FIN05_CHO_PHEP_TON_TIEN`), khác loại với "cố ý đỏ chờ vá".

Gặp một cổng đỏ không rõ mới/cũ mà không có ở đây: tra `git log -- <file>` +
`grep -rl <tên file> docs/` trước khi đoán, rồi **thêm một dòng vào bảng
trên** — đừng chỉ trả lời riêng cho người hỏi rồi để kiến thức đó biến mất.
