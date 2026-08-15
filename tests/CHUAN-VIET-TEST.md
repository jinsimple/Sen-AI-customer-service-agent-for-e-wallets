# Chuẩn viết test — FIN-05

> Vai giữ file: **tester** · 15/08/2026.
> Ba luật dưới đây được PO phê chuẩn thành **luật dự án**, rút ra từ lỗi THẬT
> gặp trong hai ngày 14–15/08, mỗi luật kèm đúng những ca đã làm nó lộ ra.
>
> **Vị trí file:** nội dung này thuộc về `docs/TESTING.md`, nhưng `docs/` là
> vùng ghi của vai `po` (hiến pháp §4). Tôi giữ bản gốc ở đây — vùng của
> tester — và đã gửi PO nguyên văn để dán sang. Không tự ghi vào vùng khác,
> kể cả khi được mời: ranh giới co giãn "một lần cho tiện" thì lần sau không
> còn là ranh giới.

## Vì sao ba luật, không phải một

Một test chỉ có giá trị khi chứng minh được **cả ba** vế:

| | Câu hỏi | Thiếu nó thì |
|---|---|---|
| **Luật 1** | Ràng buộc có **HIỆU LỰC** không? | suite xanh trên một guardrail không tồn tại |
| **Luật 2** | Ràng buộc có **QUÁ RỘNG** không? | suite xanh trên một guardrail cấm cả người hợp lệ |
| **Luật 3** | Phép đo có **TÁI LẬP** được không? | kết luận rút từ một kịch bản không quay lại được |

Thiếu vế nào cũng cho ra một kết luận **trông như đo được mà không đo được gì**.
Đó là lý do ba luật này là một họ, không phải ba quy tắc rời: Luật 1 và 2 canh
**cái thước**, Luật 3 canh **phép đo**.

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
