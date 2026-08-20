# GĐ3 chuẩn bị trước — Bảo Mật: tên model lộ khách · biên dữ liệu deepseek · tuân thủ · O5 · 3 câu Lead

🟢 **NIÊM 20/08 — GĐ3 ĐÃ XONG, không phải tạm dừng.** [ĐO] `docs/DECISIONS.md:2518-2522` — ADR-043
"Model KHÔNG còn ghim; hạ tầng TỰ XOAY trong một bể đã kiểm", **Trạng thái: chấp nhận · 19/08/2026**.
Còn nợ **duy nhất**: bộ kiểm an toàn đầy đủ 46+100 ca trên deepseek — **PO thật cắt có chủ đích**
("không cần test 154 lần cho mỗi model, chỉ cần test chạy được 1-2 lần"), chờ hạn ngạch riêng cho
việc đo, không phải việc bị quên. Đừng đi tìm ai đã bỏ rơi GĐ3.

> 19/08/2026. Theo `docs/giao-viec/2026-08-19-gd3-doi-model-xoay-tu-dong.md` mục 3-Bảo Mật, PO-agent
> giao chuẩn bị trước GĐ2 chưa đóng. **Không chạm container/ngăn xếp** — chỉ đọc mã + WebFetch tài
> liệu công khai. Nhãn: **[ĐO]** = kiểm được, có nguồn · **[PHẢI KIỂM]** · **[PHÁN ĐOÁN]**.

---

## 1a. Tên model lộ ra khách — MỨC THẤP, đề xuất tên thân thiện + một điều kiện PDPA

**Không phải bí mật kỹ thuật.** Nhiều sản phẩm thương mại công khai "Powered by GPT-4" — tên
model không phải credential, không mở đường tấn công trực tiếp (biết tên model không giúp bypass
`authority-matrix`/tool guard nào, mọi ràng buộc cứng nằm ở tầng CODE, không ở tầng model).

**Hai lý do THỰC vẫn nên dùng tên thân thiện, không phải lý do "giấu vì giấu":**
1. **Rủi ro danh tiếng/địa chính trị đặc thù cho ví điện tử VN.** Lộ mã nội bộ dài
   (`deepseek-v4-pro-0813`) mời câu hỏi *"ví X đọc tin nhắn khách bằng model Trung Quốc"* — đúng
   chủ đề đang nhạy (xem hồ sơ Đ.25/vùng dữ liệu, §1b dưới). Đây không phải lý do kỹ thuật, là lý do
   truyền thông — nhưng vẫn đáng cân vì brief này CHÍNH LÀ tính năng cho khách **thấy và chọn**.
2. **Giảm bề mặt cho prompt injection nhắm mục tiêu.** Biết đúng model + version giúp kẻ tấn công
   tra cứu điểm yếu ĐÃ CÔNG BỐ của riêng bản đó (jailbreak DB công khai theo model). Giá trị thấp
   (kẻ tấn công nghiêm túc thử nhiều kỹ thuật bất kể có biết tên hay không) nhưng **chi phí ẩn = 0**
   nên vẫn nên làm.

**Đề xuất cụ thể:** tên thân thiện dạng trung tính không gắn hãng (`"Trợ lý nhanh"` /
`"Trợ lý tiêu chuẩn"` hoặc `"Model A/B/C"`), mã thật CHỈ ở log + `usage.jsonl` (đã đúng hiện trạng)
+ response API cho khách test (không phải bubble hiển thị) nếu QA/QC cần verify đúng model đang chạy.
**Không cần phân theo role** — `/agent/chat` chỉ phục vụ `customer` (`main.py:604-605`, CSKH/Sếp
thao tác qua webapp trực tiếp, không qua chat) nên không có "màn CSKH cần thấy tên thật" phải tính.

**🔴 MỘT ĐIỀU KIỆN — hướng ngược lại thứ trực giác đầu tiên:** đây là tính năng **khách TỰ CHỌN
test model**, tức khách đang tham gia một hành vi có thông tin. Nguyên tắc PDPA/Đ.25 (bên nhận xử lý
phải được khai) nghiêng về **minh bạch nhà xử lý**, không phải che giấu. Đề xuất: tên thân thiện
trên UI (đúng UX, đúng lý do ①②) NHƯNG có một dòng/tooltip disclosure dùng được (không phải mã kỹ
thuật, mà câu kiểu *"một số lựa chọn dùng mô hình AI của bên thứ ba, dữ liệu xử lý ngoài Việt Nam"*)
**TRƯỚC khi khách bắt đầu test** — đây là điều kiện MỀM (không chặn code), chỉ áp dụng thật nếu
tính năng mở cho khách THẬT (không chỉ đội nội bộ test).

## 1b. Xoay model có đổi biên dữ-liệu-rời-hạ-tầng không — CÓ MỘT KHÁC BIỆT ĐÁNG GHI, không phải "y hệt cũ"

**[ĐO] cấu hình hiện tại (bám `docs/security/2026-08-17-y-kien-tuan-thu-chot-qwen3.7-plus-dashscope-intl.md`
+ `docs/security/2026-08-17-su-co-khoa-openai-gui-sang-alibaba.md:108`):**
`LLM_BASE_URL = https://dashscope-intl.aliyuncs.com/compatible-mode/v1` — MỘT host chung cho
mọi model chat, cùng `LLM_API_KEY`. Rotation theo thiết kế GĐ3 (`LLM_MODEL_POOL`) chỉ đổi tham số
`model=` truyền vào, **không đổi `base_url`/khoá** — đúng ràng buộc §2.5 brief ("cắm vào hạ tầng đã
có, không xây đường song song").

**[ĐO] tài liệu công khai Alibaba Cloud (WebFetch 19/08, 3 nguồn — xem mục Nguồn):**

| | Qwen (đã ghim 17/08) | DeepSeek (deepseek-v4-pro/-flash) |
|---|---|---|
| Có trong danh sách vùng Singapore? | ✅ (nguồn §1 hồ sơ 17/08) | ✅ — `alibabacloud.com/help/en/model-studio/models`: cả hai liệt kê "Singapore" cùng bảng vùng với Qwen |
| Endpoint Singapore theo tài liệu | `dashscope-intl.aliyuncs.com/compatible-mode/v1` (dùng thật trong hệ thống) | `{WorkspaceId}.ap-southeast-1.maas.aliyuncs.com/compatible-mode/v1` (trang riêng `deepseek-api`) — **KHÁC HOST** |
| Nhãn của chính Alibaba | Model của Alibaba (Qwen) | **"Third-party models"** — Alibaba tự phân loại khác hạng |
| Hạ tầng suy luận (chạy trên máy của Alibaba hay proxy sang máy DeepSeek) | Đã đọc trong hồ sơ 17/08: "node suy luận trong phạm vi triển khai dịch vụ" | 🔴 **[PHẢI KIỂM] — tài liệu công khai KHÔNG nói rõ.** Không tìm thấy câu khẳng định "chạy trên hạ tầng Alibaba" hay "proxy sang DeepSeek" |

**Kết luận — KHÔNG lặp lại nguyên xi "y hệt cũ" của bài Qwen, phải sửa lại:**
1. **Về mặt TÀI LIỆU/vùng:** DeepSeek được liệt kê trong CÙNG bảng vùng Singapore như Qwen ⟹ khung
   *"lưu trữ Singapore; suy luận tại node toàn cầu ngoài TQ đại lục"* của bài 17/08 **nhiều khả năng
   áp dụng** — vì đó là tuyên bố ở tầng DỊCH VỤ (Model Studio quốc tế), không phải tầng riêng của
   Qwen. Nhưng đây là **[PHÁN ĐOÁN]**, không phải [ĐO], vì trang tuyên bố vùng-triển-khai gốc không
   nêu tên DeepSeek tường minh.
2. **Về mặt HẠ TẦNG KỸ THUẬT:** endpoint tài liệu công khai của DeepSeek (`{WorkspaceId}.ap-southeast-1
   .maas.aliyuncs.com`) **khác hostname** với `dashscope-intl.aliyuncs.com` đang cấu hình. Chưa xác
   nhận được liệu `dashscope-intl.aliyuncs.com` có thật sự phục vụ model `deepseek-*` hay không (có
   thể đây chỉ là hai đường vào cùng một hạ tầng, hoặc có thể không) — **đây chính là việc "ping 1
   lượt tối thiểu mỗi model" mà Coder đã có trong brief**, nhưng tôi khai thêm: **phép ping đó không
   chỉ là smoke test chức năng — nó ĐANG LÀM VIỆC CỦA MỘT PHÉP KIỂM TUÂN THỦ.** Nếu ping một model
   deepseek qua `LLM_BASE_URL` hiện tại mà THẤT BẠI (model not found), đó là bằng chứng model đó cần
   endpoint khác — và nếu ai đó "sửa" bằng cách đổi `LLM_BASE_URL` sang host workspace-specific,
   **phải quay lại kiểm §1 của bài Qwen từ đầu cho endpoint mới**, không giả định nó thừa hưởng kết
   luận cũ.
3. **"Third-party model" là một chữ Alibaba tự chọn, không phải chữ của ta — nhưng nó gợi ý một câu
   hỏi hợp đồng khác:** dữ liệu qua model "của Alibaba" (Qwen) và dữ liệu qua model "bên thứ ba lưu
   trữ trên Alibaba" (DeepSeek) có thể nằm dưới **hai khung DPA/ToS khác nhau** dù cùng một tài
   khoản — câu này **KHÔNG trả lời được bằng tài liệu công khai**, đúng loại câu bài 17/08 đã khoanh
   ("chưa đọc Product Terms of Service mức hợp đồng").

**Về "bên nhận xử lý" (khung ADR-025 đã dùng cho Qwen, §3 bài 17/08):** DeepSeek đứng **ĐÚNG CHỖ**
Qwen đang đứng — bên nhận xử lý nhóm A, không tạo cửa mới bên trong hệ thống ta, dùng khung đã có.
**Không phải phép THAY, là phép THÊM** — sau GĐ3, hồ sơ Đ.25 (nếu dựng lại) phải liệt kê **BA** bên
nhận (OpenAI · Alibaba/Qwen · Alibaba-hoặc-DeepSeek), không phải hai.

## 2. Đoạn bổ sung hồ sơ tuân thủ (nối `2026-08-17-y-kien-tuan-thu-chot-qwen3.7-plus-dashscope-intl.md`)

> Dán ngay dưới §3 của bài gốc, KHÔNG sửa thân bài đã chốt — đúng nếp `docs/DECISIONS.md` "chỉ ghi thêm".

### Phụ lục 19/08 — mở rộng cho họ DeepSeek trên cùng tài khoản (GĐ3 xoay model)

**[ĐO]** DeepSeek (`deepseek-v4-pro`, `deepseek-v4-flash` — xem bảng §1b) xuất hiện trong CÙNG bảng
vùng Singapore mà bài gốc dùng để chốt Qwen, dưới nhãn Alibaba tự gắn **"Third-party models"**.
Khung "bên nhận xử lý" (§3 bài gốc) áp y hệt: đây là **phép THÊM**, không phải phép THAY — hệ thống
sau GĐ3 có tối đa **BA** bên nhận nhóm A tuỳ model đang hoạt động (OpenAI cho embedding/eval; Qwen
hoặc DeepSeek cho chat, tuỳ lượt xoay).

**🔴 Khác biệt PHẢI khai, KHÔNG được gộp vào kết luận "y hệt":**
- Endpoint tài liệu công khai cho DeepSeek (`{WorkspaceId}.ap-southeast-1.maas.aliyuncs.com`) khác
  hostname đang cấu hình (`dashscope-intl.aliyuncs.com`) — **[PHẢI KIỂM]** bằng chính phép ping GĐ3
  đã có, không giả định tương thích.
- "Third-party model" có thể mang khung hợp đồng khác Qwen dù cùng tài khoản — **[PHẢI KIỂM] mức
  hợp đồng**, chưa đọc được từ tài liệu công khai (đúng khoảng trống bài gốc đã khoanh cho Qwen).
- `deepseek-v3.2` (có trong bể đề xuất ở brief GĐ3 §1) — **[ĐO] tìm kiếm công khai 19/08:** model
  này được ghi nhận **sẽ ngừng cung cấp (delist) 10/10/2026** trên nền tảng Alibaba. Không phải vấn
  đề bảo mật, nhưng đáng khai để Coder không đưa một model sắp ngừng vào bể ưu tiên cao.

**Không đổi:** ba điều kiện §5 bài gốc (nói đúng câu vùng · kiểm công tắc inference-log · demo bằng
tài khoản hạt giống) áp NGUYÊN VẸN cho DeepSeek, không cần điều kiện mới — cùng loại rủi ro, cùng
biện pháp giảm nhẹ.

## 3. Rà ca âm tính cho vị ngữ O5 tất định (`\[[A-Z_]+\]` ⟹ chặn) — ĐỀ XUẤT GĐ2, chưa quyết

**[ĐO] quét mã tìm MỌI nguồn hợp lệ có thể sinh ra mẫu `[CHỮ_HOA]` trong reply của agent:**

| nguồn khả nghi | kết quả | có va Đ5 không |
|---|---|---|
| Định dạng ID (`new_id()`, `src/tools/base.py:31`) | `TCK-a1b2c3d4e5f6` — hex THƯỜNG, có gạch ngang, KHÔNG có ngoặc vuông | ❌ không va |
| Template hệ thống (`prompt.py` `_TEMPLATE`) | 0 hướng dẫn model xuất `[XXX]` dạng thẻ | ❌ không va |
| Câu an toàn cố định (`CAU_AN_TOAN`, `output_filter.py:26`) | không chứa ngoặc vuông (đã đọc nguyên văn) | ❌ không va |
| Markdown tự nhiên model có thể sinh (`[Xem thêm](url)`) | vị ngữ đòi TOÀN BỘ ký tự trong ngoặc là `A-Z`/`_` — chữ thường/dấu tiếng Việt/khoảng trắng làm trượt ngay | ❌ không va (vị ngữ đủ hẹp) |
| `spotlight.py` (`_THAY_THE`, `_MAU_NGOAC_NGAN`) | dùng `⟦⟧` (ngoặc kép nhọn) và cụm tiếng Việt thường trong `[]` — khác ký tự, khác case | ❌ không va |
| `_scrub_pii_cho_llm` che `user_id` (`customer_tools.py:525`) | `"[USER]"` | ✅ **VA — đúng chủ đích**, ca dương thứ hai (đã báo Lead 19/08 sáng) |
| `scrub_pii()` observability (Presidio labels) | `[PERSON_VN]`/`[ORGANIZATION]`/... | ✅ **VA — ca gốc GĐ2** |

**KẾT LUẬN: KHÔNG tìm thấy ca âm tính (câu hợp lệ nào của agent chứa `[CHỮ_HOA]` mà KHÔNG phải một
trong hai kênh rò đã biết).** Vị ngữ đủ hẹp để không cần thêm điều kiện loại trừ. Đây là kiểm TRA
CỨU MÃ TĨNH — chưa chạy qua model thật (0 token, đúng phạm vi "chuẩn bị trước"); khuyến nghị QA/QC
khi thiết kế cổng O5 (nếu PO thật duyệt) vẫn nên chạy một lô câu hợp lệ THẬT qua model để xác nhận
bằng quan sát, không chỉ bằng suy luận tĩnh (đúng Luật M của dự án — xác nhận không phải bằng chứng).

---

## Trả lời BA CÂU LEAD THÊM (19/08, cùng GĐ3, nặng hơn brief gốc)

### ① Cổng nhập bể — 3 good + 3 đối kháng của brief có ĐỦ không?

**KHÔNG đủ như liệt kê nguyên văn — đề xuất đổi MỘT slot, không thêm slot.**

Brief đề: 1 ca O1 (lộ cấu hình) · 1 ca O4 (hứa hoàn tiền) · 1 ca bịa số (O3). Tôi đọc lại 4 nhóm
lọc đầu ra (`output_filter.py`): **O1 = lộ config/OTP threshold trong reply** (khớp bằng regex hẹp
— khả năng LỆCH giữa các model THẤP, vì đây là hành vi "lỡ miệng" ngẫu nhiên, không phải năng lực);
**O4 = lời hứa hoàn tiền không được phép** (đe doạ trực tiếp ràng buộc cứng 1 ở TẦNG NỘI DUNG — dù
tool layer đã chặn thực thi, một lời HỨA sai vẫn là rủi ro pháp lý/uy tín thật); **O3 = bịa số**
(đúng tâm GĐ1, khả năng lệch giữa model CAO — đây là năng lực suy luận + kỷ luật gọi tool, khác hẳn
giữa các họ model).

**Thứ brief BỎ SÓT mà tôi cho là nặng hơn O1:** khả năng chống **prompt injection từ nội dung RAG**
(`search_policy` — tool DUY NHẤT model đọc dữ liệu do BÊN NGOÀI kiểm soát một phần, `partner_admin`
upload). Model mới **chưa ai đo độ dễ bị dụ "phớt lờ hướng dẫn trên" khi đọc chunk chính sách** —
đây là năng lực khác hẳn O1 (O1 là model tự lỡ lời; injection-resistance là model bị NGƯỜI KHÁC điều
khiển qua dữ liệu). Dự án đã có sẵn corpus cho việc này (`docs/security/injection-surface-inventory.md`,
`corpus-doi-chung-EN-du-truc.jsonl`) — QA/QC rút 1 ca từ đó thay vì phải soạn mới.

**Đề xuất bộ 3 tối thiểu, xếp theo khả năng LỆCH GIỮA MODEL (cao → thấp), không theo chữ cái:**
1. **O3 bịa số** (giữ nguyên) — đúng tâm khủng hoảng GĐ1, khả năng lệch cao nhất.
2. **1 ca injection từ `search_policy`** (THAY cho O1) — rủi ro model-specific cao, dự án đã có
   corpus sẵn, brief đang bỏ trống hoàn toàn.
3. **O4 hứa hoàn tiền** (giữ nguyên) — đe doạ trực tiếp ràng buộc cứng 1 ở tầng nội dung.

O1 không phải "bỏ hẳn" — hạ xuống ca **khuyến nghị thêm nếu còn ngân sách**, không phải ca bắt buộc.
Quyết định cuối vẫn thuộc QA/QC (họ thiết kế cổng) — đây là **định hạng rủi ro**, không phải thiết kế
thay.

**Một điểm giảm nhẹ đáng ghi, đúng tinh thần "ghi cả ô sạch" (Luật R):** RÀNG BUỘC CỨNG không phụ
thuộc hạnh kiểm model — `forbidden_tools` (execute_refund/lock_wallet/...) không tồn tại trong code
bất kể model nào đang chạy (ADR-001, INV-08), và duyệt resolution luôn cần route `supervisor` +
CHECK constraint DB (ADR-003) — **một model "hư" nhất có thể làm là NÓI sai, không THỰC THI sai.**
Bề mặt rủi ro của việc đổi model bị **giới hạn ở tầng nội dung/lời nói**, không mở rộng sang tầng
hành động — đây là lý do tôi không xếp cổng nhập bể ở mức "chặn toàn bộ GĐ3", dù nó vẫn phải qua
trước khi bật cho khách.

### ② Dữ liệu rời biên giới — đã trả lời đầy đủ ở §1b + §2 phía trên.

Tóm tắt một dòng: DeepSeek đứng đúng chỗ Qwen đang đứng trong khung "bên nhận xử lý" (không cửa
mới), nhưng mang HAI khác biệt kỹ thuật/hợp đồng chưa xác nhận được bằng tài liệu công khai (host
endpoint khác, khung ToS "third-party" có thể khác) — phép ping GĐ3 đã có phải làm thêm vai trò
xác nhận tuân thủ, không chỉ smoke test.

### ③ Fail-fast `_khoa_cho_nha_cung_cap` — chỉ chạy LÚC KHỞI ĐỘNG, và ĐỦ cho thiết kế bể ĐÚNG NHƯ BRIEF

**[ĐO] `config.py:263,299,300`:** `LLM_BASE_URL`/`LLM_MODEL`/`LLM_API_KEY` là **hằng số module-level**,
tính đúng MỘT LẦN lúc import (khởi động process) — `_khoa_cho_nha_cung_cap` chạy đúng một lần cho
đúng MỘT cặp `(base_url, key)`. Nó **KHÔNG chạy lại** khi model đổi giữa lượt.

**Nhưng đây KHÔNG phải lỗ hổng — với ĐÚNG thiết kế brief mô tả.** `LLM_MODEL_POOL` (brief §3-Backend
mục 1) là một **danh sách TÊN MODEL**, không phải danh sách cặp base_url/key — mọi model trong bể
dùng CHUNG `LLM_BASE_URL`/`LLM_API_KEY` đã được validate một lần lúc khởi động. Xoay model chỉ đổi
tham số `model=` truyền vào client ĐÃ ĐƯỢC CẤU HÌNH ĐÚNG — không đi qua con đường sự cố 17/08 (khoá
sai đích) lần nào, vì đích **không đổi theo lượt xoay**, chỉ tên model đổi.

🔴 **NHƯNG ĐÂY LÀ MỘT RÀNG BUỘC THIẾT KẾ PHẢI GIỮ TƯỜNG MINH, KHÔNG PHẢI SỰ THẬT TỰ NHIÊN — đúng
tinh thần câu hỏi của Lead ("rẻ hỏi bây giờ, đắt hỏi sau").** Nếu SAU NÀY ai mở rộng bể sang một
model cần base_url/khoá KHÁC (vd một model chỉ có qua OpenAI trực tiếp, hoặc §1b phát hiện DeepSeek
thật sự cần endpoint `{WorkspaceId}.ap-southeast-1.maas.aliyuncs.com` riêng) — `_khoa_cho_nha_cung_cap`
hiện tại **sẽ không bắt được**, vì nó chỉ biết kiểm MỘT cặp đã đặt lúc khởi động, không biết bể có
thể cần N cặp.

**Đề xuất cụ thể cho Coder (định hạng, không thiết kế thay):** ghi một dòng invariant tại chỗ khai
`LLM_MODEL_POOL` — *"mọi model trong bể PHẢI cùng `LLM_BASE_URL`/`LLM_API_KEY` hiện tại; thêm một
model cần endpoint/khoá khác phải mở rộng `_khoa_cho_nha_cung_cap` thành kiểm N cặp tường minh,
không phải nới lỏng hay bỏ qua nó."* — biến một giả định ngầm thành một ràng buộc đọc được, đúng
nguyên tắc "cơ chế thắng lời hứa" dự án đang theo.

**KẾT LUẬN ③: Fail-fast ĐỦ cho GĐ3 như brief mô tả (single-endpoint pool). Không chặn. Một dòng
khai cần thêm để nó vẫn đủ khi bể lớn hơn sau này.**

---

## PHỤ LỤC 19/08 (chiều) — Trigger xoay dùng `_DAU_HIEU_HET_HAN_MUC`: VI PHẠM một ràng buộc CHÍNH MÃ ĐÃ VIẾT

*(Lead báo thiết kế của Coder đề xuất trigger xoay = `PermissionDeniedError` (403) + so chuỗi thân
lỗi tìm dấu hiệu hết hạn ngạch, và trỏ tới `2026-08-17-lo-khoa-dashscope-va-403-thanh-500.md`. [ĐO]
đọc mã trước khi trả lời — không phán đoán trên mô tả.)*

**[ĐO] `graph.py:147-155` — `_DAU_HIEU_HET_HAN_MUC`, chính chuỗi so khớp Coder định dùng:**

```python
# Dấu hiệu "hết tiền" trong thân thông báo. CỐ Ý chỉ dùng cho MỘT trường log,
# không bao giờ cho thứ khách nhìn thấy: ...
# Luật: một phép phân biệt MONG MANH chỉ được điều khiển hậu quả RẺ. Sai ở
# đây tốn một nhãn log lệch (tự lộ ngay khi người vận hành mở ra xem). Nếu
# nó điều khiển "khách thấy gì" thì một lần đổi câu chữ = khách nhận 500.
_DAU_HIEU_HET_HAN_MUC = ("quota", "exhaust", "insufficient", "balance", "arrear", "unpurchased")
```

🔴 **Đây không phải suy đoán rủi ro — chính đoạn mã ĐANG CÓ đã tự khai ranh giới sử dụng của nó, và
thiết kế GĐ3 định vượt đúng ranh giới đó.** Hôm nay tín hiệu này chỉ gắn vào MỘT trường log
(`co_dau_hieu_het_han_muc` trong `_mo_ta_loi_nha_cung_cap`) — sai thì tốn một nhãn log lệch, tự lộ
khi người vận hành mở ra xem. Dùng nó làm **trigger xoay model** là để nó điều khiển một **HÀNH VI**
(đổi model đang trả lời khách) — đúng loại hậu quả ĐẮT mà chính comment nói KHÔNG được giao cho nó.

**Và `PermissionDeniedError` (403) tự nó cũng KHÔNG phải tín hiệu một-nghĩa** — `graph.py:142`:
`# 403 hết hạn mức HOẶC sai quyền`. Đúng ca đã xảy ra thật (footnote 16/08 trong hồ sơ 17/08:
`AccessDenied.Unpurchased` 6/6 model — một model CHƯA ĐƯỢC MUA/BẬT trên tài khoản, không phải hết
hạn ngạch). Nếu trigger xoay dựa trên so chuỗi để phân biệt hai ca, và một model MỚI trong bể GĐ3
(deepseek nào đó) rơi vào ca "chưa bật quyền" — hệ thống sẽ hiểu nhầm thành "hết hạn ngạch" (hoặc
ngược lại, tuỳ so chuỗi khớp gì) rồi **xoay tiếp**, có thể xoay xuyên suốt cả bể nếu nhiều model
cùng chưa được bật, **im lặng thoái hoá dịch vụ mà không ai biết cấu hình sai** — đúng viễn cảnh
"vòi đang chảy, không cái còi nào kêu" quen thuộc của dự án.

**Đề xuất — KHÔNG cấm dùng 403 làm trigger, sửa CHỖ ĐẶT ranh giới:**
1. **Trigger xoay = `isinstance(loi, PermissionDeniedError)` thô** (đúng lớp `_LOI_CAN_CAN_THIEP` đã
   có, KHÔNG cần so chuỗi để phân biệt "hết hạn ngạch" vs "sai quyền") — cả hai ca đều hợp lý để thử
   model TIẾP THEO trong bể, vì cả hai đều là "model này không phục vụ được lượt này".
2. **KHÔNG dùng `_DAU_HIEU_HET_HAN_MUC` (so chuỗi) để QUYẾT ĐỊNH có xoay hay không** — giữ nguyên
   ranh giới gốc: nó chỉ gắn nhãn LOG, phục vụ người vận hành đọc SAU.
3. **BẮT BUỘC giữ cảnh báo vận hành** — đúng khuyến nghị CHƯA TỪNG LÀM của hồ sơ 17/08 §2
   ("401/403 hết hạn mức phải BÁO ĐỘNG vận hành, không chỉ ghi log"), và nay **quan trọng hơn**: xoay
   tự động che mất TRIỆU CHỨNG phía khách (khách không còn thấy lỗi) — nếu không có báo động riêng,
   một model cấu hình sai có thể nằm im trong bể, bị xoay-qua liên tục, KHÔNG AI PHÁT HIỆN, vì cổng
   duy nhất từng báo hiệu (khách bị lỗi) đã bị chính bản vá xoay che mất.
4. **Đặt trần số lần xoay trong MỘT lượt** (đã ngụ ý ở "Quyết định model tại ĐẦU LƯỢT" của brief,
   nhưng đáng nói thẳng): không để một request duy nhất thử hết cả bể N model tuần tự nếu cấu hình
   sai hàng loạt — nên có một giới hạn rõ, và khi chạm giới hạn thì trả lời khách bằng đường xin lỗi
   đã có (§2 hồ sơ 17/08), không rơi ra 500 trần.

**Không đổi kết luận GĐ3 nào đã chốt — đây là khai TRƯỚC khi Coder viết trigger**, đúng tinh thần
"rẻ hỏi bây giờ, đắt hỏi sau" Lead đã đặt tên.

---

## PHỤ LỤC 2 — trả lời BA CÂU của Lead (bảng 403+404 model-specific · log vs cảnh báo · cầu dao)

### ① Phạm vi 403+404: ĐỒNG Ý VỚI BA HÀNG, KHÔNG XÁC NHẬN ĐƯỢC HÀNG 403 — và đó chính là lý do giữ ③

**400 → KHÔNG xoay: đồng ý, thêm một lý do.** Không chỉ vì "không chắc model-specific" — ràng buộc
#3 của brief ("Coder phải kiểm cách tắt suy luận TỪNG model, không giả định chung") có nghĩa 400 có
thể chính là lỗi tham số RIÊNG của một model (model B không chấp nhận field model A dùng được). Kể cả
khi đó, **KHÔNG xoay vẫn đúng** — đó là lỗi TÍCH HỢP CỦA TA, và cho phép hệ thống tự "lách" bằng cách
âm thầm bỏ qua model lỗi để thử model khác là **che lỗi tích hợp vĩnh viễn**, không phải xử lý đúng.

**401 → KHÔNG xoay: đồng ý** — khoá dùng chung cả bể (§1b/③ phần trên), xoay model không đổi khoá.

**403/404 → XOAY: đồng ý, nhưng [ĐO] hồ sơ 17/08 KHÔNG xác nhận được giả định "403 luôn model-specific".**
Hồ sơ đó quan sát 403 trong bối cảnh **CHỈ MỘT model đang cấu hình** (Qwen, trước GĐ3) — nó không có
cơ hội phân biệt "quota của MODEL này cạn" với "TÀI KHOẢN có vấn đề" (đình chỉ/thanh toán), vì cả hai
giả thuyết đều khớp quan sát duy nhất khi chỉ có một model. **Đây là khoảng trống thật, không suy
đoán được từ tài liệu đã có.** 404 thì an toàn hơn để coi là model-specific (model không tồn tại ở
endpoint — đúng đường tôi lo ở §1b về host DeepSeek khác `dashscope-intl`), vì 404 hiếm khi mang
nghĩa "toàn tài khoản hỏng".

⟹ **Không xác nhận/bác được ①. Đây chính là lý do TÔI ủng hộ ③ (cầu dao) như một LƯỚI ĐỠ cho đúng
khoảng trống này** — cầu dao không cần biết trigger phân loại đúng hay sai, nó chỉ cần biết SỐ MODEL
cạn tăng nhanh bất thường là dấu hiệu phân loại sai, bất kể cơ chế phân loại là gì.

### ② Log CẢNH BÁO: CẦN nhưng THEO CHÍNH HỒ SƠ 17/08 — KHÔNG ĐỦ MỘT MÌNH

Hồ sơ `2026-08-17-lo-khoa-dashscope-va-403-thanh-500.md` §2 đã viết thẳng: *"401/403 hết hạn mức
phải BÁO ĐỘNG vận hành, KHÔNG CHỈ GHI LOG"* — dự án tự đặt ra tiêu chuẩn này 17/08, GĐ3 không nên hạ
xuống dưới nó. Log mức WARNING vẫn là **log** — cần ai đó chủ động mở ra đọc, và **xoay êm nghĩa là
chính triệu chứng duy nhất từng khiến người ta mở log lên xem (khách báo lỗi) đã biến mất.**

**Đề xuất rẻ, dùng hạ tầng ĐÃ CÓ TRONG BRIEF, không xây thêm:** brief §3-Backend đã có sẵn
`GET` "danh sách bể + trạng thái cạn/sống từng model" cho UI khách chọn model. Đây **CHÍNH LÀ** chỗ
để lộ tín hiệu cho vận hành — không cần kênh cảnh báo mới: miễn field trạng thái cạn của route đó
phản ánh ĐÚNG dữ liệu Redis đang có (không cache/làm tròn), nó tự động thành một "dashboard tối
thiểu" bất kỳ ai trong đội mở UI cũng thấy — **rẻ hơn một cơ chế alerting riêng, và không có gì để
quên bật**. Log WARNING vẫn giữ (rẻ, cho hồi cứu) — nhưng đừng coi nó là đủ.

### ③ Cầu dao ≥3 model / 60s — MỨC HỢP LÝ, thêm HAI điều kiện thi hành

**Đồng ý ngưỡng.** Với bể ~5-6 model (brief §1), ≥3 trong 60s là phần lớn bể chết trong một cửa sổ
ngắn hơn nhiều so với nhịp cạn quota thật (quota theo brief là hạn mức tính theo **ngày/tháng**, TTL
15 phút của trạng thái "cạn" tự nó đã ngụ ý đây là trạng thái MỀM/thử-lại-được — cạn quota thật khó
lòng tự "hết cạn" sau 15 phút, cạn HÀNG LOẠT trong giây thì càng không phải hình dạng quota).

**Hai điều kiện thi hành, đề xuất thêm:**
1. **Không cần cửa sổ thời gian riêng — dùng chính TTL Redis đã có.** Đếm SỐ khoá `model_can:*`
   đang tồn tại tại một thời điểm (không phải "trong M giây qua") đạt được hiệu quả tương đương mà
   không cần dựng thêm cơ chế đếm-theo-cửa-sổ: TTL 15 phút đã tự động "quên" các lần cạn cũ, nên một
   phép đếm đơn giản `SCARD`/đếm khoá khớp mẫu tại thời điểm kiểm tra đã tương đương "N model cạn
   trong M phút gần nhất" — rẻ hơn về thiết kế, cùng tinh thần "cắm vào hạ tầng đã có" của brief §2.5.
2. **Khi cầu dao bật, "giữ nguyên model hiện tại" nên là model ĐẦU BỂ (`LLM_MODEL_POOL[0]`, ưu tiên
   cao nhất theo brief), KHÔNG phải model cuối cùng trót dừng lại giữa chuỗi xoay.** Chính chuỗi xoay
   dẫn tới lúc cầu dao bật là bằng chứng trạng thái gần đây KHÔNG đáng tin — "giữ nguyên" nên là quay
   về đường cơ sở đã biết tốt, không phải đóng băng tại một điểm ngẫu nhiên giữa một cơn hỏng hàng
   loạt.

**KẾT LUẬN PHỤ LỤC 2: đồng ý cả ba đề xuất của Lead, với ba điều chỉnh nhỏ ở trên. Không đổi việc
đang cầm — sáp nhập vào (1b)/(2)/(3) đã nộp, không phải mục thứ năm.**

## Nguồn (WebFetch 19/08)

- [Region, deployment scope & access domains](https://www.alibabacloud.com/help/en/model-studio/regions/) (bài gốc 17/08)
- [Supported Models and Capabilities Overview](https://www.alibabacloud.com/help/en/model-studio/models)
- [DeepSeek V4, DeepSeek R1, DeepSeek V3, DeepSeek V3.1 API](https://www.alibabacloud.com/help/en/model-studio/deepseek-api)
- [Singapore region access information](https://help.aliyun.com/en/model-studio/singapore-regional-access-information)
- [deepseek-v3.2 Model Info — thông báo ngừng cung cấp](https://help.aliyun.com/en/model-studio/deepseek-v3-3)
