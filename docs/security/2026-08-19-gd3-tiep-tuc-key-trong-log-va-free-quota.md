# GĐ3 tiếp tục — key production trong log/sổ · bản chốt (B) · free-quota-only

> 19/08/2026 (đội bật lại). Theo yêu cầu PO-agent, brief `docs/giao-viec/2026-08-19-gd3-doi-model-xoay-tu-dong.md`
> (`876a240`). Mục 3/4/tên-model/biên-dữ-liệu đã có đầy đủ trong
> `docs/security/2026-08-19-gd3-chuan-bi-truoc-doi-model-xoay-tu-dong.md` — KHÔNG lặp lại ở đây, chỉ
> tóm tắt + một cập nhật. File này xử ba việc MỚI: (1) key-trong-log [ĐO thật], (2) bản chốt (B) để
> land vào brief, (3) định hạng "Free quota only".

## 1. Key production trong log/sổ — [ĐO] SẠCH, và một điểm cần PHÂN BIỆT rõ cho PO-agent

**[ĐO] `grep -n "LLM_API_KEY" src/agents/graph.py` → đúng 2 hit: import (`:45`) và MỘT lần dùng duy
nhất tại `:540`, tham số `api_key=` của constructor `ChatOpenAI(...)`.** Không có đường thứ hai. Khoá
KHÔNG đi vào bất kỳ dict/log/trace nào.

**[ĐO] `_mo_ta_loi_nha_cung_cap()` (`graph.py:158-178`, hàm DUY NHẤT dựng bản ghi lỗi nhà cung cấp cho
`usage.jsonl`) — docstring TỰ KHAI đúng nguyên tắc cần:** *"Thân thô có thể mang khoá hoặc định danh
nội bộ; ta chỉ rút ra MỘT CỜ BOOLEAN từ nó."* Bản ghi thật chỉ gồm: tên lớp lỗi, mã trạng thái HTTP,
`base_url`, tên model, hai cờ boolean, `request_id` của nhà cung cấp (không nhạy cảm, chỉ dùng để hồi
cứu khiếu nại hoá đơn). **KHÔNG có trường nào chứa thân thông báo thô** — đây chính là hàng rào chặn
kịch bản "thân lỗi 403 vô tình echo lại khoá" mà nhà cung cấp đôi khi làm.

🔴 **PHÂN BIỆT PO-agent cần biết trước khi giao tiếp — `base_url` KHÔNG PHẢI bí mật, đừng xếp chung
với `api_key`.** [ĐO] `graph.py:169,206` — `usage.jsonl` CÓ ghi `base_url` (vd
`https://dashscope-intl.aliyuncs.com/compatible-mode/v1`). Đây là **địa chỉ endpoint công khai**,
không phải credential — biết base_url không giúp ai gọi được API (vẫn cần `api_key`). Ghi nó là **có
ích** (biết lượt nào đi qua nhà cung cấp nào khi debug/hồi cứu chi phí), không phải rò rỉ. **Câu hỏi
đúng không phải "usage.jsonl có ghi base_url không" (có, và nên có) mà là "có ghi API KEY VALUE
không" (không, đã kiểm).** Đừng gộp hai khái niệm khi soi GĐ3.

**Yêu cầu cho Coder khi viết `model_rotated` + API GET-bể GĐ3 (mới, chưa code):** tái dùng NGUYÊN
MẪU `_mo_ta_loi_nha_cung_cap()` — chỉ log **tên model, trạng thái (cạn/sống), lý do (mã lỗi/lớp lỗi,
KHÔNG phải thân thông báo thô)**. Không dựng cơ chế log mới; đây đã là khuôn ĐÚNG có sẵn.

## 2. BẢN CHỐT điều khoản (B) — dán thẳng vào brief GĐ3, mục Ràng buộc thiết kế

> **KEY PRODUCTION KHÔNG BAO GIỜ VÀO NGỮ CẢNH PHIÊN CLAUDE**
>
> Giá trị bí mật cấp production (API key nhà cung cấp LLM/embedding trả phí, `JWT_SECRET_KEY`/
> `FIELD_ENCRYPTION_KEY` của production, mọi credential thật) KHÔNG BAO GIỜ được một phiên Claude
> đọc, gõ, hay để giá trị thật xuất hiện trong bất kỳ lệnh/tệp nào phiên đó chạm tới — kể cả gián
> tiếp (sed/echo/cat trên tệp chứa nó, hay để công cụ tự động đọc tệp đó vào ngữ cảnh).
>
> **Lý do:** giá trị đi vào ngữ cảnh một phiên đồng thời đi qua HAI kênh phơi nhiễm — lưu trên đĩa
> (transcript phiên) VÀ truyền qua mạng tới nhà cung cấp mô hình đang chạy phiên đó, NGAY LÚC ĐỌC,
> bất kể transcript có được lưu hay không. Đây là định nghĩa cách agent hoạt động, không phải lỗi vá
> được bằng kỷ luật thao tác cẩn thận hơn (đã đo thật: một kỹ sư làm đúng mọi bước — một lệnh sed,
> không echo, không trích lại — giá trị vẫn lọt qua cơ chế theo dõi tệp của chính công cụ).
>
> **Thi hành — bằng SỰ VẮNG MẶT, không bằng kỷ luật:**
> 1. `.env.production` (giá trị thật) không bao giờ tồn tại trên máy/thư mục một phiên Claude đọc
>    được. Repo chỉ có `.env.production.example` — tên biến + chú thích, không giá trị thật.
> 2. PO thật (hoặc người có thẩm quyền) điền giá trị TRỰC TIẾP trên máy đích (SSH/dashboard trình
>    duyệt), không qua bất kỳ phiên Claude nào, không ngoại lệ "chỉ lần này có giám sát".
> 3. Agent chỉ đưa hướng dẫn (lệnh mẫu, các bước), KHÔNG là bên thực thi lệnh mang giá trị thật,
>    KHÔNG đọc lại tệp đích để "xác nhận đã ghi đúng" (đọc lại = đưa giá trị vào ngữ cảnh).
> 4. Xác minh (nếu cần) bằng SO SÁNH BĂM người vận hành tự chạy và dán kết quả băm — không dán giá
>    trị. Kiểm bằng SENTINEL (giá trị giả, độc nhất, `grep` được) khi cần chứng minh "giá trị không
>    rời máy" — không bao giờ dùng chính giá trị thật làm dữ liệu thử (tự tạo ra đúng sự kiện đang
>    đo, và tự trói tay chính phép kiểm — không ai dám `grep` khoá thật để xác nhận).
> 5. KHÔNG áp cho khoá DEV/demo (`fin05`/`fin05ttl`/`fin05do`) — giữ kỷ luật hiện có (grep tên biến,
>    không grep cả dòng) + xoay khi cần. Áp cho GIÁ TRỊ, không áp cho TÊN BIẾN — agent vẫn đọc/viết
>    cấu trúc `.env.production.example` bình thường.

*(Toàn văn lý lẽ + phân tích: `docs/security/2026-08-19-kenh-transcript-lo-khoa-dinh-hang-va-chinh-sach-key-product.md`)*

## 3+4. Tên model lộ khách + biên dữ liệu deepseek — ĐÃ CÓ, tóm tắt, một cập nhật

**Không lặp lại** — toàn văn trong `2026-08-19-gd3-chuan-bi-truoc-doi-model-xoay-tu-dong.md` §1a/§1b.
Tóm tắt: (a) tên model MỨC THẤP, không phải bí mật kỹ thuật, nhưng đề xuất tên thân thiện vì lý do
danh tiếng/địa chính trị + giảm bề mặt injection nhắm mục tiêu — mã thật chỉ trong log/sổ (đã đúng
theo mục 1). (b) biên dữ liệu: DeepSeek đứng đúng chỗ Qwen trong khung "bên nhận xử lý" (không cửa
mới), nhưng endpoint tài liệu công khai của DeepSeek khác hostname đang cấu hình — [PHẢI KIỂM] bằng
phép ping Coder đã có trong brief.

🔴 **Về "ảnh console PO thật vừa gửi lại xác nhận cùng tài khoản/base_url" — KHÔNG đổi kết luận (b).**
Ảnh console xác nhận **quota/account state** (5 model cùng nằm trong một tài khoản DashScope) — đây
là điều tôi **chưa từng nghi ngờ** (brief GĐ3 gốc đã nói rõ "cùng tài khoản API hiện tại"). Câu tôi
để ngỏ là khác hẳn: **model có PHỤC VỤ ĐƯỢC qua đúng `LLM_BASE_URL` (`dashscope-intl.aliyuncs.com`)
hiện cấu hình hay không** — đó là hành vi ROUTING lúc gọi API thật, một ảnh console (hiển thị số dư/
quota) không trả lời được câu đó. Phép ping của Coder vẫn là bước bắt buộc, không phải một bước có
thể bỏ qua vì "console đã xác nhận".

## 5. "Free quota only" — ĐỊNH HẠNG: điều kiện bên ngoài, có thể mất bất cứ lúc nào. KHÔNG được ghi là lớp phòng vệ.

**Áp đúng khung Luật R của dự án — ba tiêu chí:**
1. **Đang được dựa vào?** Có nguy cơ — nếu ai đó đọc "Free quota only, hết là 403 chứ không âm thầm
   tính tiền" rồi coi đó là một GIỚI HẠN CHI PHÍ đã có sẵn, không cần cơ chế nào khác.
2. **Không khai ở contract/ADR/test nào?** Đúng — [ĐO] không có gì trong `contracts/`/`tests/` giả
   định hay kiểm tra trạng thái "free tier" của tài khoản. Nó tồn tại đúng MỘT nơi: một cấu hình trên
   console của nhà cung cấp, ngoài tầm nhìn của mọi cổng ta có.
3. **Mất đi thì hỏng IM LẶNG?** 🔴 **CÓ, và đây là dạng nặng nhất Luật R mô tả (§②) — "dạng nặng nhất
   là khi thứ được dựa vào lại có thể biến mất đúng ngày ta chủ động đi tới".** Tài khoản CÓ THỂ được
   nâng lên trả phí (chính brief GĐ3 mở đầu bằng việc PO thật đang chủ động thao tác trên console này
   — đúng bối cảnh "ngày ta đang chủ động đi tới"). Ngày đó, KHÔNG dòng code nào của ta đổi, hành vi
   "lượt hỏng do hết ngạch → 403 vô hại" lặng lẽ biến thành "lượt hỏng do hết ngạch → tính tiền thật,
   không dừng lại". **Đủ cả ba tiêu chí ⟹ đây KHÔNG PHẢI một bảo đảm, chỉ là một THÓI QUEN của môi
   trường hiện tại.**

**KẾT LUẬN:** ghi vào hồ sơ đúng nguyên văn *"'Free quota only' là điều kiện phía nhà cung cấp,
KHÔNG kiểm soát được từ hệ thống ta, có thể bị gỡ bởi một thao tác console không để lại dấu vết nào
trong repo — không được trích dẫn như một lớp phòng vệ chi phí trong bất kỳ đánh giá bảo mật/tuân
thủ nào."** Lớp phòng vệ THẬT mà ta SỞ HỮU là: `_agent_turn_limiter` (chặn đồng thời, `main.py`) +
chốt chặn tầng transport (`cong_ra_ngoai.py`) + cầu dao GĐ3 đã đề xuất trước đó (≥N model cạn/60s →
ngừng xoay). Đây là những thứ có DIFF, có TEST, có thể ĐO — đúng hình dạng "bảo đảm có khai" Luật R
đòi hỏi, khác hẳn một công tắc trên console người khác quản lý.

**Không kết luận:** ❌ tắt "free quota" đi là mất phòng vệ — nó CHƯA TỪNG là phòng vệ theo đúng định
nghĩa của dự án, chỉ là một sự trùng hợp có lợi hôm nay.
