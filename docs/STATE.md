# Trạng thái dự án FIN-05

> **Viết cho người đọc NGUỘI** — bạn không có gì trong đầu, chỉ có repo này.
> Đọc `CLAUDE.md` (hiến pháp) trước, rồi file này, rồi 5 ADR gần nhất trong `docs/DECISIONS.md`.
>
> Cập nhật: **18/08/2026**, ngay trước khi PO thật tắt toàn đội để khởi động lại sạch.
> Nhật ký chi tiết ngày 17/08 (3.001 dòng, mọi lập luận và số đo):
> `docs/nhat-ky/2026-08-17-nhat-ky-day-du.md`

---

## 1. ĐỌC MỤC NÀY TRƯỚC KHI GÕ BẤT CỨ LỆNH NÀO

| | |
|---|---|
| **Nhánh** | `dev/learning-loop` (một nhánh, PR theo đợt) |
| **Cây làm việc DÙNG CHUNG** giữa nhiều phiên | 🔴 **Mọi lệnh `git` phải có pathspec.** `stash`/`commit`/`checkout`/`clean` không pathspec sẽ đụng việc dở của phiên khác. Đã gây 3 sự cố. |
| **Ba ngăn xếp Docker** | `fin05` (demo, kho RAG 378 chunk) · `fin05ttl` (đo) · `fin05do` (đo, kho RỖNG) |
| **Bắt buộc `-p`** | `docker compose -p fin05 …` — thiếu `-p` là hạ ngăn xếp khác |
| **Chạy test** | `docker exec … pytest` (an toàn). `P-121-new/.venv` chạy được test nhưng **CẤM dùng để đo kích thích gửi model** (lệch `langchain-core` với container) |
| **Biến bắt buộc** | `JWT_SECRET_KEY` · `FIELD_ENCRYPTION_KEY` · `REDIS_URL` (`fake://ci` cho test) |
| 🔴 **`FIELD_ENCRYPTION_KEY`** | **KHÔNG được xoay** nếu chưa có script mã hoá lại — xoay là **mất vĩnh viễn** dữ liệu đã mã hoá |
| **Production** `app.adaptivealgo.uk` | **CHỈ ĐỌC** với mọi phiên. Thăm dò phải báo trước |
| **`eval/heldout_set.jsonl`** | **NIÊM PHONG** — chỉ chạy MỘT LẦN, sau khi hiệu chuẩn trọng tài |

## 2. TRẠNG THÁI VẬT (đo lúc bàn giao)

```
HEAD nhánh dev/learning-loop
băm src/          b8e7c5397457
BUILD_COMMIT      bec7235   ← cả ba ngăn xếp, ĐỒNG NHẤT
sửa-tay           0 · 0 · 0
docker diff       0 · 0 · 0
lệch×             0 · 0 · 0
invariants        23/23 xanh
check_contracts   sạch
suite backend     1 ĐỎ  (test_thanh_phan_tai_lieu_kho::…noi_bo_da_biet — "kho rỗng",
                         điều kiện hạ tầng, CHƯA TRUY, chưa ai gán nguyên nhân)
```

**Model đang chạy:** `qwen3.7-max` qua DashScope **Singapore** (`dashscope-intl`).
Embedding vẫn **OpenAI** (tách khỏi chat có chủ đích — đổi embedding = đổi VẬT ⟹ phải nạp lại kho).

⚠️ **Cờ đóng băng LLM `.DANG-DONG-BANG-LLM` ĐANG BỊ XOÁ** khỏi cây làm việc (tracked, chưa commit
việc xoá ⟹ `git checkout -- .DANG-DONG-BANG-LLM` khôi phục được). Tệp tự khai *"xoá file này khi
hết đóng băng"* nên **xoá có thể là thao tác đúng** — không ai trong đội nhận. Lý do đóng băng ghi
trong tệp: *"PO thật quay video demo"*. **Câu cho PO: video quay xong chưa?** Xong ⟹ để nguyên.
Chưa ⟹ khôi phục.

## 3. BA LỚP GIỮ HOÁ ĐƠN — kiểm trước khi chạy bất cứ thứ gì

```
① FIN05_CHO_PHEP_TON_TIEN   mặc định TẮT ⟹ 3 bộ test gọi LLM thật đều SKIP
                             ⟹ `pytest tests/` KHÔNG thể ra hoá đơn      ✅ đang chạy
② .DANG-DONG-BANG-LLM       cờ đóng băng                                  ⚠️ đang MẤT (mục 2)
③ PHAN_LUONG_BAT=1          định tuyến: câu chào hỏi đi đường nhẹ, 0 token ✅ đang bật
```

🔴 **Hạn mức: A3 của PO thật còn hiệu lực — "chưa nạp gì cho tới khi tối ưu xong chi tiêu token."**
Còn **~32K** token miễn phí trên `qwen3.7-max`. `qwen3.8-max` đã cạn. Quota là **1M/model**.

---

## 4. ĐÃ LÀM ĐƯỢC (nền, tin được)

- **Kiến trúc contract-first hoạt động thật.** `tests/test_invariants.py` **introspect app đang
  chạy** (đọc `app.routes`, moi `allowed_roles` từ closure, đọc `CheckConstraint` qua AST, gọi
  thẳng `build_customer_tools()`). Thêm route / đổi guard / đổi tên tool mà quên contract ⟹ **đỏ
  ngay**. 23/23 xanh.
- **Năm ràng buộc cứng** đã mã hoá thành test (HITL tuyệt đối · AI không vượt cấp · cấm bịa số
  liệu · OTP phiên · cờ gian lận ≠ khoá ví).
- **T1 định tuyến (`src/agents/phan_luong.py`)** — luật cứng, allow-list, tự khai băm. Đo được:
  **−33,5% tất định**, câu `"alo"` = **0 token**.
- **Sự cố lộ khoá OpenAI đã đóng**: `_khoa_cho_nha_cung_cap()` fail-fast — thiếu khoá + base_url
  khác ⟹ `RuntimeError` lúc khởi động, **không bao giờ âm thầm mượn `OPENAI_API_KEY`**.
- **Benchmark 74,57/85 = 87,7%** — luôn kèm 3 caveat (xem nhật ký).
- **Bộ an toàn 30/30** — ⚠️ **hiệu chuẩn trên `gpt-4o-mini`, CHƯA chạy lại trên Qwen.** Đây là
  tài sản lớn nhất dự án và nó đang **chưa được xác nhận trên model đang chạy**.

## 5. ĐANG DỞ / CHẶN — theo mức

### 🔴 A. CHẶN, chỉ PO thật gỡ được

**A1 · ADR-031 (truy vấn `search_policy`) — TẠM DỪNG THI HÀNH, TIỀN ĐỀ SAI.**
PO đã duyệt, nhưng duyệt trên tiền đề *"query chưa được lưu ở đâu"* — **sai**:
`investigation_logs.tool_input_json` (`models.py:328`, JSON **thường không mã hoá**) đã lưu query
từ lâu. **Ba câu cần PO:**
1. phạm vi **một bảng** (`tool_results`) hay **hai bảng**?
2. **thêm cột mới** hay **mở rộng cơ chế đã có** ở `investigation_logs` cho lượt không tạo vé?
   *(đường thứ hai rẻ hơn hẳn, không tạo chuẩn thứ ba)*
3. `tool_input_json` plaintext chứa **mã GD · SĐT · số tiền** (input của MỌI tool, không riêng
   `search_policy`) — tách thành **finding bảo mật riêng**, độc lập ADR-031?

**A2 · Hồ sơ Đ.25 (NĐ 13/2023) — đồng hồ CÓ THỂ đã chạy từ 15/08.**
```
demo mentor 15/08  ·  hạn 60 ngày = 14/10/2026  ·  CÒN 58 NGÀY (tính lúc 17/08)
```
**Việc đầu tiên là XÁC ĐỊNH, không phải làm hồ sơ:** *buổi demo mentor 15/08 có ai gõ SĐT / tên /
mã giao dịch **THẬT** vào ô chat không?* Không ⟹ đồng hồ chưa chạy. Có ⟹ hồ sơ là "bù" chứ không
phải "chuẩn bị".
> **Nghĩa vụ này CÓ TỪ TRƯỚC QWEN** — hệ thống gửi văn bản khách sang Mỹ từ thời `gpt-4o-mini`.
> Vật liệu §2/§3/§4 do security dựng: `docs/security/2026-08-17-kiem-ke-du-lieu-roi-bien-gioi-cho-ho-so-D25.md`

**A3 · Phiếu Alibaba — 4 câu MỘT vòng** (thứ tự đã xếp):
1. 🔴 **trần TPM/RPM ở Singapore có nâng được theo yêu cầu không, điều kiện gì?**
   *(nâng được ⟹ cả nhánh đổi vùng LẪN hồ sơ pháp lý cùng rụng)*
2. request client **ngắt giữa chừng** có tính tiền/TPM không?
3. **cached-token** có vào TPM không?
4. **batch ở Singapore**: giá 50% và bucket riêng hay không?

**A4 · Đối chiếu bảng điều khiển** — tổng token 1 ngày trên dashboard nhà cung cấp **vs** sổ nội
bộ. Đây là phép phân định cho giả thuyết *"lượt hỏng ghi 0 là lời giải cho câu 2,3M"*.

**A5 · Chốt NHỊP GÕ cho buổi 150 người** — xem mục 6, đây là **biến quyết định duy nhất**.

**A6 · Hai công tắc logging chưa ai kiểm:**
- **Alibaba `Model monitoring`**: ghi input/output **mỗi lời gọi**, giữ 30 ngày, **bật bằng một
  nút**, **không diff nào của ta nhìn thấy** ⟹ kiểm + **ghi ngày kiểm**
- **OpenAI stored completions / org logging**: chưa ai kiểm, và nó **định hạng sự cố lộ khoá 17/08**

**A7 · Còn treo từ trước:** xoay khoá Qwen · secret GitHub Actions · **số hotline thật**
(`HOTLINE_CSKH` hiện là `1900-XXXX (SỐ TẠM — CHƯA CẤU HÌNH)`, **cố ý không bấm được**).

### 🟡 B. Đội làm được, không chờ ai

| việc | vùng | ghi chú |
|---|---|---|
| **Bất biến chống livelock** — *"cùng tool + cùng tham số + cùng lỗi ⟹ lần thứ hai là DỪNG"* | `src/` | **Ưu tiên cao nhất.** Tất định, **không cần hiệu chuẩn**. Xem mục 6 |
| **Quét cả lớp: test nào TÊN hứa X mà ASSERTION kiểm Y** | `tests/` | **Công bố tiêu chí TRƯỚC khi quét**, nếu không thì kết quả "0" vô nghĩa |
| Viết vế thiếu cho `path_traversal_filename_is_safe` | `tests/` | assert **không tệp nào ra ngoài thư mục kho** |
| Ca A2 (đồng ý trước khi tạo vé) — viết lại câu | `tests/` | ba trục: thuận · ngược (đã đồng ý thì KHÔNG hỏi lại) · **ca hỏng** |
| F-31/32 — prompt thiếu *"làm gì khi một điều kiện KHÔNG TỰ SỬA ĐƯỢC"* | `src/` | Cùng họ với A2. Vá **sau** bất biến |
| Truy ca đỏ còn lại (`kho rỗng`) | `tests/` | chưa ai gán nguyên nhân |
| `main.py:621` — khách đọc lý do từ chối SAI (*"vượt 200.000 TPM"*, trần thật 1M) | `src/` | **gom vào đợt sau**, đừng dựng lại 3 ảnh vì một dòng chữ |
| Sổ nợ: `_AGENT_MAX_CONCURRENT=20` **mất căn cứ** | — | xem mục 6 |
| `so_luot_da_phat` (đếm ở tầng client HTTP) | `src/` | **nguồn ĐỘC LẬP thật** duy nhất với envelope |
| Container lint/test riêng | hạ tầng | chữa GỐC việc bước-đo-ghi-vào-container. Khuôn đã có: `fin05-THU-ROUTER-vut-di` |

---

## 6. BỐN CON SỐ QUYẾT ĐỊNH — kèm mẫu số, đừng trích thiếu

### ⓵ Trần thật là TPM, và ta ĐÃ VƯỢT ở cấu hình buổi 150 người

```
trần TPM 1.000.000 / 14.198 token/lượt =  70,4 lượt/phút   ← TRẦN THẬT
trần RPM        600 /   2,39 gọi/lượt  = 251,0 lượt/phút   ← không bao giờ chạm trước

150 người × 0,50 lượt/ph =  75 lượt/ph → TPM 🔴 106%
150 người × 1,00 lượt/ph = 150 lượt/ph → TPM 🔴 213%
100 người × 0,50         =  50 lượt/ph → TPM     71%  ✅
```

🔴 **BIẾN QUYẾT ĐỊNH LÀ NHỊP GÕ, KHÔNG PHẢI CODE** — điều khiển bằng **kịch bản chạy**:
```
nhịp ≤0,5 lượt/ph/người → T1 chỉ cần  6,1% lượt đơn  (gần như chắc đạt)
nhịp  1,0               → cần        53,0%           (BẤT KHẢ, không bản vá nào cứu kịp)
```
⚠️ `14.198 token/lượt` là trung bình lượt **THÀNH CÔNG** ⟹ mọi ngưỡng trên là **CẬN DƯỚI**.
5% lượt hỏng ở 60K ⟹ 106% thành ~123%.

### ⓶ Lượt HỎNG là lượt ĐẮT NHẤT, và là lượt DUY NHẤT ghi 0

```
1 lượt hỏng (livelock)  49.700 – 71.600 token   ← đắt gấp 3,3–4,7 lần lượt chạy xong
1 lượt bình thường      15.136
sổ ghi                  0        ← đã vá `0 → None` (620de3e), nhưng chỉ ở envelope
```
**Cơ chế livelock (`[ĐO]`, chuỗi 16 message khôi phục từ PostgresSaver):** khách đã đăng nhập
**chưa xác thực OTP phiên** → hỏi câu cần tra cứu → tool trả `status=error` → model **không có tool
nào để xin OTP** (đúng thiết kế — OTP ở tầng HTTP) → **không sửa được điều kiện nên THỬ LẠI y hệt**
→ không gì đếm số lần thử → lặp tới khi trần thời gian cắt. **8 lời gọi, 6 lần `lookup_transaction`
cùng tham số.**

**Tần suất `[ĐO]`: 1/13** — *cho trước một lỗi OTP, xác suất lặp*. **12/13 dừng sau ĐÚNG MỘT lần
và xử lý ĐÚNG** (trả lời khách · tạo vé · bàn giao).
⚠️ **KHÔNG dùng con số `4%`** (13/370 thread) — 370 là **dân số pha tạp**, gồm nhiều thread thử.

**So 12 ca đối chứng trên 6 biến: KHÔNG biến nào tách được**, và có **2 ca giống hệt ca lặp cho
kết quả khác nhau** ⟹ *"không tìm thấy điều kiện phân biệt trong 6 biến đã đo"* — **mạnh hơn**
"chưa tìm ra", **yếu hơn** "đã chứng minh là ngẫu nhiên".
⟹ **Không có đầu vào nào để lọc** ⟹ sửa prompt là bản vá **xác suất** đánh vào hiện tượng **xác
suất**: giảm tỉ lệ, **không đóng cửa**. **Chỉ bất biến tất định đóng được.**
> Bất biến có **hai nửa**: `(a)` phát hiện+dừng — tất định, **ở đây nằm TRỌN phần tiết kiệm**;
> `(b)` nói gì với khách — **đã có sẵn 12 ca mẫu**, không phải nghĩ ra hành vi mới.
> `(a)` land một mình vẫn ăn trọn tiết kiệm (dừng ở lời gọi thứ 2 → fallback sẵn có → vẫn ra vé,
> sớm hơn 6 lời gọi, rẻ hơn ~40K).

### ⓷ Sổ chi tiêu ghi 1/6 tới 1/9 số thật

```
đã ghi sổ    28.000
3 lượt hỏng 149.000 – 215.000
THỰC TẾ     177.000 – 243.000
```
**`[ĐO]` — đếm-thiếu KHÔNG phải giả thuyết:** `14:26:44.157` ta bỏ → `14:26:45.335` DashScope trả
**HTTP 200 TRỌN VẸN, 1,2s SAU**. Nhà cung cấp tính theo thứ họ **sinh**, không theo thứ ta **đọc**.
🔴 **Giả thuyết chưa xác nhận:** đây là lời giải cho câu *"sao hết 2,3M token?"* — phân định bằng
**A4** (đối chiếu dashboard).

### ⓸ `_AGENT_MAX_CONCURRENT = 20` MẤT CĂN CỨ

Nó được cỡ từ *"trần OpenAI 200.000 TPM ⟹ ~13 lượt/phút"*. Trần thật giờ là **1M**. Con số 200k
còn sống ở **3 chỗ trong `src/`** (`rate_limit.py:62` · `main.py:379` · `main.py:621`).

⚠️ **KHÔNG đọc thành "đang tự chặn ở 1/5 năng lực"** — đó là ghép số của trục **TPM** vào trục
**đồng-thời**. Limiter là trần **ĐỒNG THỜI**, thông lượng = `20 × 60/T`:

```
kịch bản                tok/lượt   T hoà vốn   T thật   ai chặn   biên
NHẸ (lượt đơn)           11.727      14,1s      9,0s     TPM     1,56×
trung bình toàn bộ       15.497      18,6s     11,3s     TPM     1,65×
PO (nặng, 5 lượt)        17.494      21,0s     15,5s     TPM     1,35×
```
🔴 **KHÔNG ghép chéo hai biến** — `token/lượt` và `giây/lượt` **tương quan** (hội thoại nặng thì
vừa nhiều token vừa lâu). Ghép `T` của kịch bản này với hoà-vốn của kịch bản kia là mô tả **một hội
thoại KHÔNG TỒN TẠI**.
⟹ Ghép đúng: **TPM chặn trước ở cả ba.** Nhưng biên ở **kịch bản demo chỉ 1,35×**.
> **CẢNH BÁO CÓ NGƯỠNG:** *nếu `T` trung vị **của kịch bản NẶNG** vượt ~18s, limiter thành nút
> thắt trước TPM — đo lại `_AGENT_MAX_CONCURRENT` trước khi tối ưu tiếp.* Đo từ sổ usage, 0 token,
> **lọc theo loại hội thoại** (trung vị chung 9,0s trông rất an toàn và **sẽ không bao giờ kêu**).
> Một reranker cộng ~5s/lượt là đủ đảo trục chặn.

---

## 7. SỔ ĐĂNG KÝ LUẬT — STATE là nơi cấp phát DUY NHẤT

> Phiên nào đúc luật mới → **đề xuất, KHÔNG tự đặt ký hiệu**. (17/08 đã có va chạm: hai Luật D đúc
> cách nhau 8 phút ở hai file, vì hai không gian tên song song không ai cấp phát.)

**Luật A** — cổng phải **IM** lúc bình thường **VÀ KÊU** lúc bất thường; nửa sau **chỉ chứng minh
được bằng ca đối chứng**.
**Luật B** — làm tròn một phát biểu lên đúng **MỘT nấc** là lớp sai đắt nhất.
> ⭐ **MỞ RỘNG (security):** kiểm tra cuối trước khi một phát biểu **RỜI KHỎI ĐỘI** là hỏi nó **ĐẨY
> NGƯỜI NHẬN VÀO CHẾ ĐỘ NÀO**, không chỉ hỏi nó có đúng không. *(vd: "quá hạn" → chế độ khắc phục
> vi phạm; "còn 58 ngày" → một việc có lịch. Cùng dữ kiện, hai hành động.)*
> ⭐ **HỆ QUẢ:** một khuyến nghị **KHÔNG hành động** và một con số **ĐẨY người ta hành động** nằm
> trong cùng một tin thì **con số THẮNG** — người đọc giữ con số, không giữ lời dặn.

**Luật C** — đối chiếu chéo chỉ hoạt động ở nơi **CÓ VẬT ĐO**; điều khoản thi hành = so **SỐ**,
không so **KẾT LUẬN**. *(Ngoài vùng có vật đo — vd đọc ToS mức hợp đồng — quy tắc thay thế là:
khai HẠNG BẰNG CHỨNG rồi DỪNG.)*
**Luật D** — cột phòng thủ phải có **NGUỒN ĐỘC LẬP**; "dư thừa" là **hệ quả**, không phải tiêu chí.
> ⚠️ **"Mang thông tin độc lập" ≠ "có NGUỒN độc lập".** Bảng chéo bác được *"một biến viết hai
> lần"* nhưng **KHÔNG** bác được *"hai hằng số gõ cạnh nhau"* — mà cái sau mới là thứ vỡ về sau.

**Luật E** — bộ ca xanh phải chứa **PHÂN BỐ CÁC LÝ DO**; nhánh không bao giờ bắn = nhánh **chưa
được kiểm**, kể cả khi độ phủ ghi 100%.
**Luật F** — mọi con số vào một quyết định phải mang **MẪU SỐ** trên **CÙNG DÒNG**.
> ⚠️ Mẫu số phải **cùng quần thể với câu hỏi**. To hơn ≠ đúng hơn: *2 lần lặp của đúng lượt tệ
> nhất mạnh hơn 33 mẫu trộn lẫn các loại lượt.*

**Luật G** — một cơ chế **đang làm đúng việc của NÓ** không có nghĩa nó đang làm việc **ta giả
định**.
**Luật H** *(security `ec8026e`)* — **nhánh xử lý lỗi in ra KẾT LUẬN thay vì TRIỆU CHỨNG là nhánh
NÓI DỐI ĐƯỢC.** Bộ đo báo *"tôi thấy gì"*, không báo *"tôi kết luận gì"*.
> **Bốn lần trong một ngày, ba người, bốn tầng:** `"không có sự kiện"` ≠ `"không đọc được"`
> (security) · `total_tokens=0` ≠ `None` (coder) · `ĐẠT·TRƯỢT·không_đo_được` (tester) ·
> `xanh·đỏ·SKIP` (coder). **Luôn là BA trạng thái, không phải hai.**

**Luật 1** — assertion **không được trùng trạng thái mặc định** (test xanh giả).
**Luật 12b** — mọi phát biểu xếp hạng phải **khai TRỤC**: *"xếp trên trục X, trục Y chưa xét"*.
**Luật 17** — **trước** khi chạy một phép thử, hỏi: *nếu giả thuyết SAI thì phép thử này ra gì, và
có phân biệt được không?*

**Luật mới 17/08 (chờ số hiệu, đề nghị `I`/`J`/`K`):**
- **Bước ĐO không được ghi vào container đang chạy.** Buộc phải ghi ⟹ **khai trước + hoàn nguyên
  ngay**, và trạng thái *"đã ghi"* phải **hiện ra**, không nằm trong trí nhớ.
  **Vế thi hành:** sau **MỖI** phiên đo, chạy `docker diff` **trước khi báo cáo bất cứ số nào**.
- **Vá đúng một lỗi có thể làm IM một cổng đang hỏng vì lý do khác** — bản vá đúng, tác dụng phụ là
  **xoá mất triệu chứng duy nhất** tố cáo cổng ấy rỗng. **Vế thi hành:** khi bản vá làm một cổng
  **ĐỎ → XANH**, phải **đọc xem cổng đó khẳng định CÁI GÌ**, không chỉ ghi nhận nó đã xanh.
- **Nhiều ước lượng độc lập cùng lệch MỘT hướng = thiên lệch CHUNG, đi tìm bộ lọc chung.**
  *(Bằng chứng: `45K` → `0–21K` → thực tế `149–215K`. Bản "đính chính" đi XA HƠN khỏi sự thật.)*

---

## 8. 🔴 BÀI HỌC LỚN NHẤT 17/08 — đọc mục này rồi hãy tin bất kỳ con số nào

**BẢY lỗi, ba người, MỘT lớp: suy từ một tập ĐÃ BỊ LỌC mà không khai bộ lọc.**

| bộ lọc | ca |
|---|---|
| **vắng mặt** | *"không thấy `ToolResult` ⟹ không tool call"* — thật ra **8 tool call**, cổng OTP từ chối **TRƯỚC** `record_tool_result` |
| **sống sót** | *"0/70 lời gọi chạm trần 20s"* — `giay` **chỉ tồn tại cho lời gọi ĐÃ TRẢ VỀ** ⟹ hằng đúng |
| **sống sót** | *"trần đệ quy 20 đặt xa gấp 4 hành vi thật (max 5)"* — max 5 là của lượt **THÀNH CÔNG**; lượt **HỎNG** có **8** |
| **tự cầm kéo** | tính xác suất trên một cấu hình **chưa từng quan sát** (lấy trung bình rồi giả định cả 3 giá trị bằng nó) |
| **tự cầm kéo** | chọn 3 điểm **vì chúng gần nhau** rồi đo độ phân tán của chính tập vừa chọn |
| **tự cầm kéo** | trích `contracts/agent-tools.yaml:143-146` rồi **dừng đọc** — câu trả lời ở **dòng 150** |
| **dân số pha tạp** | `4%` (13/370) vs `1/13`; `30%` trích **không kèm kịch bản** |

> **Cả bảy lần bộ lọc đều VÔ HÌNH** — không ai cố tình lọc, **tập tự đến đã lọc rồi**.
> **Dấu hiệu DUY NHẤT: dữ liệu trông QUÁ GỌN.**
>
> ⟹ **NẾP KIỂM:** khi một tập số trông sạch bất thường — không ngoại lệ, không đuôi, một cực đại
> tròn trịa — hỏi ***"cái gì đã KHÔNG sinh ra dòng nào ở đây?"*** **TRƯỚC** khi hỏi *"số này nói
> gì"*.

**Và nó nằm ngay trong dụng cụ đo của chính ta:** sổ usage ghi `so_luot_goi_model = 0` cho lượt
hỏng ⟹ 22 dòng `0` lẫn *"đường nhẹ, đúng 0"* với *"lượt hỏng, không biết"*. **Sổ dựng ra để đếm
lời gọi, và nó lọc mất đúng loại lượt ta đi tìm — rồi báo bằng một giá trị TRÔNG HỢP LỆ.**

**Quy trình đã chứng minh là chữa được:** **công bố DỰ BÁO vào git TRƯỚC khi chạm vật.** Đã chạy 2
lần, trúng 6/6 và 2/2, một lần **trúng tới từng chữ số**. Kèm bảng *"nếu khác thì nghi gì"*.
Và **khai trước rằng một kết quả THUẬN LỢI sẽ không được tính là xác nhận** — đã có ca thật: cổng
xanh nhưng ghi **"chưa giải thích"** thay vì "đã vá", và chính vì thế mà tester đi tìm bằng chứng
và **phát hiện ra cổng ấy rỗng**.

---

## 9. CẠM BẪY — người mới sẽ đâm vào đúng những chỗ này

**"KHAI ≠ CHẠY" — SÁU cơ chế đã gặp thật:**
`docker cp` vào container đang chạy · ảnh dựng từ **cây làm việc** chứ không phải HEAD · **đổi
phiên bản thư viện phụ thuộc** (`langchain-core` 1.5.3→1.5.4 đổi mô tả tool ~12%) · prompt chứa
`current_time` · harness **soạn lại** kích thích · `>/dev/null` nuốt một lệnh **chưa bao giờ chạy**.

- **`restart` ≠ `recreate` ≠ `rebuild`.** `Config.Env` **ghim lúc TẠO container**. `docker cp` **sống
  qua restart**.
- **Dấu thời gian COMMIT ≠ dấu thời gian TRIỂN KHAI**, và nó **lệch về hướng dễ chịu**: nếp
  *chạy → xác minh → mới commit* khiến mọi mỏ neo `git log` tính cửa sổ **RỘNG HƠN** sự thật.
  *(Đã đo: trường xuất hiện trong bản ghi **trước commit 65 giây**.)*
- **`tests/` NẰM TRONG ẢNH** ⟹ **màu cổng đổi được mà KHÔNG một dòng sản phẩm nào đổi.** Đọc kết
  quả bằng **SỐ CA CHẠY**, không chỉ bằng màu — `skip` và `pass` cùng màu trên bảng tổng.
- **Nguồn dữ liệu SAI DÂN SỐ:** `messages` (230 tin, 85 phiên) là **script sinh**, không phải người
  (p10 = p50 = 3s ⟹ 19,8 lượt/ph/người, và script **không bao giờ gõ "alo"**). **Đừng dùng nó làm
  mẫu lưu lượng thật.** `bo_ca_luot_don.json` là **bộ dò biên**, cố ý làm giàu ca hiểm — **không
  phải mẫu đại diện**.
- **Sổ `usage.jsonl` SỐNG QUA `recreate`** ⟹ tích luỹ mọi đợt. Script tổng hợp **phải lọc theo cửa
  sổ thời gian**, nếu không sẽ đếm dòng lịch sử vào kết quả hôm nay.
- **BỐN RỔ bắt buộc** khi tổng hợp: `nhe` → lượt đơn thật · `day_du`+fallback=None → chạy xong ·
  `day_du`+fallback CÓ → **HỎNG** · **KHÔNG có khoá `duong` → 🔴 ĐIỀU TRA, không gộp vào đâu**.
  *(Bẫy cụ thể: viết `duong != 'day_du'` thì lượt 422/500 thành "lượt đơn" ⟹ **thổi tỉ lệ tiết
  kiệm đúng hướng ta muốn nghe** — confound hướng-có-lợi.)*
- **BA RỔ cho token:** `đo được` · `không đọc được` · `đúng 0`. **KHÔNG `sum()` với `or 0`** —
  `or 0` biến *"không biết"* thành *"không tốn"*. Và **ba rổ phải có BA MẪU SỐ RIÊNG**.
- **Phiên chưa xác thực OTP** làm lượt rơi vào livelock. Dùng `scripts/phien_do.py` để có phiên đã
  xác thực — thiếu nó thì mất một giờ chẩn nhầm.

**Đọc trước, dọn sau. LUÔN.** *(Đã có ca: `--force-recreate` để dọn đã **xoá hiện trường** trước
khi chẩn, phải tiêm lại từ đầu. Ngoại lệ này đã được viết ra sáng cùng ngày và **vẫn bị bỏ qua**,
vì phản xạ dọn nhanh hơn phản xạ đọc.)*

**Nháp thiết kế làm NGOÀI repo.** Mọi script đo phải **IN BĂM** của vật nó đo.

---

## 10. QUY TRÌNH ĐỔI CONTRACT — không có đường tắt

```
1. DỪNG. KHÔNG sửa code trước.
2. Sửa file trong contracts/
3. Ghi ADR mới vào docs/DECISIONS.md   (DECISIONS.md CHỈ GHI THÊM, không sửa thân ADR cũ)
4. Hỏi PO thật duyệt. CHỜ trả lời.
5. python scripts/check_contracts.py --update
6. Cập nhật CONTRACT_VERSION ở đầu tests/test_invariants.py
7. commit — 🔴 KÈM FILE BASELINE mà --update sinh ra   ← §3 hiến pháp KHÔNG viết bước này
8. BÂY GIỜ mới code
```
🔴 **Thiếu bước 7 ⟹ local xanh, CI đỏ.** Đội đã vấp.

## 11. PHÂN VÙNG QUYỀN GHI (nhắc lại — §4 hiến pháp)

`po` → `docs/`, `*.md` gốc · `tech-lead` → `src/`, `frontend/src/`, `migrations/`, `contracts/`
(sau khi PO duyệt) · `tester` → `tests/`, `frontend/e2e/`, `eval/` — **KHÔNG đọc `src/`** ·
`security` → `docs/security/` · `ux-ui` → `frontend/src/` · `critic` → không ghi gì.

> **Vì sao tester không đọc `src/`:** test sẽ **phản chiếu** logic đang có, kể cả logic sai. Kết quả
> là một suite xanh mướt chứng minh rằng bug hoạt động đúng như bug.
>
> **Và quy tắc PO-agent tự đặt sau khi vi phạm:** khi chuyển tin giữa các vai bị cách ly, **chỉ
> chuyển KẾT LUẬN và LÝ LẼ, không bao giờ chuyển NỘI DUNG CORPUS.**

## 12. TÀI LIỆU LIÊN QUAN

```
docs/nhat-ky/2026-08-17-nhat-ky-day-du.md    ← toàn bộ lập luận + số đo 17/08 (3.001 dòng)
docs/DECISIONS.md                             ← ADR-001..031 (031 TẠM DỪNG, xem §5.A1)
docs/security/                                ← 20+ hồ sơ; 2 file quan trọng nhất:
   2026-08-17-kiem-ke-du-lieu-roi-bien-gioi-cho-ho-so-D25.md   (vật liệu Đ.25)
   2026-08-17-ho-so-KHAI-khac-CHAY-nam-co-che.md               (Luật H + 5 cơ chế)
docs/2026-08-17-ra-soat-khai-bao-vs-ep-buoc.md ← INV-16/INV-17 KHÔNG có test (INV-17 chỉ là
                                                  một chú thích ở dòng 51 test_invariants.py)
docs/giao-viec/                               ← brief giao việc + hồ sơ chuyên gia token
contracts/                                    ← NGUỒN SỰ THẬT về cấu trúc
```

**Pháp lý hiện hành:** NĐ 52/2024 · TT 40/2024 (**KHÔNG** dùng TT 39/2014 — hết hiệu lực) ·
NĐ 13/2023 (PDPA) · QĐ 2345/QĐ-NHNN (10tr/lần, 20tr/ngày — là ngưỡng **xác thực sinh trắc**,
**KHÔNG** phải ngưỡng gian lận; phải nói rõ điều này khi trao đổi với chuyên gia).
