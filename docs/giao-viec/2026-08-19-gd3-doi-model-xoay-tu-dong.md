# GĐ3 — 19/08: Tính năng ĐỔI MODEL cho khách test + TỰ XOAY khi hết hạn ngạch

> PO thật yêu cầu 19/08 (kèm ảnh console nhà cung cấp). PO-agent chuyển thành brief.
> **THỨ TỰ: GĐ2 (envelope + E2E) XONG TRƯỚC — chatbot phải sống đã rồi mới gắn thêm cần số.**
> GĐ3 làm trên nền GĐ2 đã xanh, cùng đội, cùng trình tự đã chạy tốt hai vòng.

## 1. YÊU CẦU CỦA PO THẬT — nguyên văn ý

1. Khách hàng test thử **đổi được model** đang trả lời chat.
2. **Hết token model nào → tự xoay sang model khác**, không chết giữa chừng.

**Bể model miễn phí (ảnh console 19/08, cùng tài khoản API hiện tại):**
```
deepseek-v4-pro-0813 · deepseek-v4-flash · deepseek-v4-pro · deepseek-v3.2 · deepseek-v4-flash-0731
mỗi model: 1M token free · consumed 0 · hết hạn 15/11/2026 (88 ngày) · Free quota only
+ họ qwen3.7-plus hiện tại (~650K còn lại theo sổ nội bộ)
```

## 2. RÀNG BUỘC THIẾT KẾ — từ chính lịch sử dự án, KHÔNG bỏ qua cái nào

1. **Đây là đảo một quyết định cũ CÓ CHỦ ĐÍCH** — `a3fb125` ghim model theo NGÀY vì "đổi model =
   đổi VẬT" (mọi phép đo A/B phụ thuộc danh tính model). PO thật tự yêu cầu nên quyền quyết là
   của PO — nhưng phải đi kèm **ADR mới** ghi rõ: xoay model là chế độ DEMO/TEST, mọi dòng
   `usage.jsonl` đã ghi `model` per-lượt (giữ nguyên — đó là thứ cứu ta khi đọc số sau này),
   và mọi phép đo eval nghiêm túc phải GHIM lại một model.
2. **Bộ an toàn 30/30 + prompt hiệu chuẩn trên gpt-4o-mini/Qwen, CHƯA từng chạy trên deepseek.**
   ⟹ model chỉ được vào BỂ XOAY sau khi qua **cổng nhập bể** (mục 3-QA). Không thả model lạ
   thẳng vào mặt khách.
3. **Suy luận TẮT mặc định** (a3fb125): deepseek v3.2/v4 có thể có cơ chế reasoning/param khác
   họ qwen — Coder phải kiểm cách tắt trên TỪNG model, không giả định chung.
4. **Embedding GIỮ NGUYÊN OpenAI** — xoay CHỈ áp cho chat model. Đổi embedding = đổi VẬT kho RAG
   (phải nạp lại 378 chunk) — ngoài phạm vi tuyệt đối.
5. Chốt chặn chi phí tầng transport (`cong_ra_ngoai`) + sổ `usage.jsonl` là hạ tầng ĐÃ CÓ — xoay
   model cắm VÀO đó, không xây đường song song.

## 3. THIẾT KẾ YÊU CẦU — mức ràng buộc, Coder tự quyết chi tiết

### Backend (Coder)
- **Bể model qua env** (12-factor): `LLM_MODEL_POOL="qwen3.7-plus-2026-05-26,deepseek-v4-pro-0813,…"`
  — thứ tự = ưu tiên. `LLM_MODEL` hiện tại = phần tử đầu. Thiếu biến ⟹ hành vi cũ (một model, không xoay).
- **Trigger xoay = PHÂN LOẠI LỖI ĐÃ CÓ** (họ 8 lớp lỗi nhà cung cấp, `5ac18bf`): chỉ xoay khi lỗi
  thuộc lớp HẾT HẠN NGẠCH/429-quota (đọc kỹ phân loại có sẵn, đừng xoay trên timeout lẻ — một
  timeout không phải "hết token", xoay nhầm là đổi vật vô cớ).
- **Trạng thái "model X đã cạn"** ghi Redis có TTL (không giữ trong RAM process — 4 worker, điều
  kiện scale ngang đã là luật). Log sự kiện `model_rotated` kèm from/to/lý_do — không log key.
- **Quyết định model tại ĐẦU LƯỢT**, giữa lượt không đổi. Một hội thoại được phép đổi model giữa
  các lượt (chấp nhận cho demo, ghi vào ADR).
- **API cho UI**: GET danh sách bể + model đang hoạt động + trạng thái cạn/sống từng model;
  POST chọn model (khách test). Route mới ⟹ **khai `authority-matrix.yaml` + đi đủ §10** —
  đây là đụng contract THẬT, không có đường tắt. Đề xuất: GET cho mọi role đã đăng nhập,
  POST chỉ `customer` (đúng tính năng cho khách test).
- Ping 1 lượt tối thiểu MỖI model trong bể trên base_url hiện tại trước khi khai "bể sẵn sàng"
  (ảnh console nói model tồn tại — chưa nói nó trả lời được qua endpoint của ta).

### UI (Coder + tham khảo ux-ui nếu cần)
- Chat khách: dropdown/chip chọn model (tên thân thiện, không lộ mã nội bộ dài), nhãn nhỏ
  "đang trả lời bởi: X" trên bubble sau mỗi lượt — khách test biết mình đang thử gì.
- Khi tự xoay: một dòng hệ thống trung tính ("đã chuyển sang model dự phòng") — KHÔNG im lặng
  (khách đang test model A mà nhận câu trả lời của model B không khai là đánh lừa phép thử của khách).

### QA/QC — CHUẨN MỚI CỦA PO ÁP TỪ ĐẦU
1. **Cổng nhập bể cho TỪNG model mới (trước khi model được bật cho khách):** 3 good case chat
   (nhẹ/nặng/tạo vé) + đối chứng an toàn tối thiểu (1 ca O1 lộ cấu hình · 1 ca O4 hứa hoàn tiền
   · 1 ca bịa số — bộ đối kháng rút gọn từ 30 ca có sẵn). Model trượt ⟹ KHÔNG vào bể, ghi rõ.
2. **Cổng xoay (0 token):** giả lập lỗi-hết-hạn-ngạch bằng transport giả — xoay đúng thứ tự ưu
   tiên · KHÔNG xoay trên lỗi không-phải-quota · Redis đánh dấu cạn có TTL · 4 worker không lệch nhau.
3. **E2E UI localhost (chuẩn 19/08):** ≥3 good case cho tính năng đổi model trên giao diện thật —
   chọn model, thấy nhãn đổi, chat trả lời; ca tự-xoay mô phỏng được thì làm, không thì khai.

### Bảo Mật
- Route mới + tên model lộ ra khách (định hạng: tên model có phải thông tin nội bộ nhạy cảm?
  đề xuất: tên thân thiện, mã thật chỉ trong log) · xoay model có đổi biên dữ-liệu-rời-hạ-tầng
  không (cùng nhà cung cấp/endpoint ⟹ dự kiến không — kiểm base_url từng model) · cập nhật hồ sơ
  tuân thủ đã viết cho qwen (2026-08-17-y-kien-tuan-thu-chot-qwen…) một đoạn phủ deepseek.

### Review
- Soi: trigger xoay có đúng chỉ lớp quota không · trạng thái cạn có race giữa 4 worker không ·
  contract §10 đi đủ 7 bước không · UI có khai việc tự xoay cho khách không.

### Lead
- Điều phối SAU KHI GĐ2 đóng. §10 cho route mới: dừng ở bước 4 (PO duyệt) — PO-agent sẽ trình
  PO thật duyệt contract + ADR một lần.
- Ngân sách: cổng nhập bể ~5 model × 6 ca ≈ 30 lượt — khai ước trước khi chạy; bể mới cho ~5M
  token nên trần thoải mái, nhưng SỔ vẫn phải khớp.

## 4. ĐỊNH NGHĨA XONG GĐ3
- [ ] ADR xoay-model (đảo có khai `a3fb125`) + contract route mới — PO thật đã duyệt
- [ ] Bể model qua env, thiếu biến = hành vi cũ · trigger chỉ lớp quota · trạng thái cạn ở Redis
- [ ] Từng model trong bể qua cổng nhập bể (3 good + 3 đối kháng) — model trượt bị loại CÓ KHAI
- [ ] Cổng xoay 0-token xanh · E2E UI ≥3 good case tính năng đổi model
- [ ] Khách thấy model đang trả lời + được báo khi tự xoay
- [ ] Sổ token khớp: mỗi lượt ghi đúng model thật đã trả lời

## BỔ SUNG 19/08 — việc đi nhờ chuyến gỡ băng backend (từ QUYẾT ĐỊNH B của GĐ2.5)
- Coder: thêm `"loai": "otp_het_tuoi"` vào `_OTP_EXPIRED_ERROR` / tương ứng `_OTP_REQUIRED_ERROR`
  (`customer_tools.py:600-603`) — field thuần cộng thêm, không đụng route/contract.
- Client chuyển nhận diện OTP-hết-tươi từ khớp-chuỗi sang đọc `loai`; tháo cổng ghim chuỗi của GĐ2.5.
- Nhân tiện xử nhánh 403-role `ChatClient.tsx:431` theo khuôn ba-trạng-thái.

## BƯỚC 0 BỔ SUNG (PO-agent quyết 19/08, sau sự cố lộ khoá trong phiên Lead)
- 🔴 **XOAY `JWT_SECRET_KEY` của ngăn xếp dev TRƯỚC lượt khách test đầu tiên** — khoá đã hiện
  nguyên văn trong sổ hội thoại một phiên (Luật S, ca thứ hai). Coder thi hành (tầng `.env`,
  khuôn ADR-035): khai trước + hỏi-và-chờ (Luật U) vì xoay vô hiệu mọi phiên đăng nhập đang mở;
  recreate có kế hoạch; chạy SAU khi hồ sơ GĐ2.5 chốt, TRƯỚC khách test GĐ3.

## BỔ SUNG 19/08 (chiều) — GĐ3 KHỞI ĐỘNG, kèm nợ GĐ2.5 lên chuyến

- PO thật quyết **HOÃN merge** GĐ2/GĐ2.5 — làm GĐ3 trước, merge gộp sau. Hồ sơ nghiệm thu đã ĐẠT
  và nằm tại `docs/nhat-ky/2026-08-19-ho-so-nghiem-thu-gd2-gd25.md` — KHÔNG mở lại.
- Nợ lên chuyến này (từ mục 8 hồ sơ, cộng với hai mục đã ghi ở BỔ SUNG trước):
  1. 🔴 **Nối `requirements.lock.txt` vào Dockerfile** (đang không nơi nào dùng nó — 6/168 gói đã
     trôi thật, xem hồ sơ 7e). Coder, cùng đợt gỡ băng backend.
  2. Ghim base image theo **digest** thay tag `python:3.12-slim` (Dockerfile:5, :33). Coder.
  3. **Playwright chạy TRONG mạng Docker** (gỡ AUTH-008×2 · AUTH-007 ca 2 · lỗ auth-multirole). Coder.
  4. `"loai":"otp_het_tuoi"` + client đọc `loai` + tháo cổng ghim + siết 403-role (đã ghi ở BỔ SUNG trước).
  5. **Mỗi lần dựng ảnh trong GĐ3 = một dòng `docs/nhat-ky/so-giam-ho-anh.md` TRƯỚC khi báo kết
     quả đo trên ảnh ấy** (Luật W) — sổ đã mở, GĐ3 là chuyến đầu tiên nó có hiệu lực.
- Thứ tự không đổi: **BƯỚC 0 (xoay JWT_SECRET_KEY) đi đầu** — hồ sơ GĐ2.5 đã chốt nên điều kiện
  "sau khi hồ sơ chốt" ĐÃ THOẢ; Coder thi hành với hỏi-và-chờ (Luật U).

## BỔ SUNG 19/08 (tối) — PO THẬT YÊU CẦU: xoay model phải chạy tốt trên BẢN LIVE (VPS + API key product)

Nguyên tắc xuyên suốt: **cùng MỘT code, khác MỖI config.** Không nhánh code nào hỏi "đang ở prod à?" —
mọi khác biệt dev/live nằm trong biến môi trường (12-factor, checklist đóng gói toàn cục).

### Ràng buộc thiết kế thêm — Coder
1. **Bể model là CONFIG THEO MÔI TRƯỜNG**, không phải hằng trong code: dev dùng
   `LLM_MODEL_POOL` với 5 deepseek free; live dùng bể RIÊNG khai trên VPS với những model mà
   **API key product thật sự có quyền gọi**. Code không được biết tên model nào cả.
   🔴 **Bản live KHÔNG được phụ thuộc model quota-free** — quota free hết hạn 15/11/2026 và thuộc
   key dev; bể live phải sống độc lập với danh sách ấy.
2. **API key + base_url đọc theo môi trường, fail-fast nếu thiếu** (không default, không fallback
   sang key dev — thiếu là chết lúc khởi động, đúng luật secret của checklist đóng gói).
3. **Xoay trên key TRẢ TIỀN = quyết định CHI TIÊU**: trước khi xoay sang model khác, đi qua ĐÚNG
   thứ tự đã là luật — xác thực → rate limit → **cost guard** → rồi mới gọi. Xoay không được thành
   đường vòng qua cost guard. Bể cạn hoặc chạm trần chi phí ⟹ trả lời "hệ thống bận, thử lại sau"
   TỬ TẾ + log sự kiện, KHÔNG xoay vòng vô hạn, KHÔNG im lặng.
4. **Trạng thái cạn ở Redis theo stack** (đã là ràng buộc) — trên VPS là Redis của stack live;
   TTL + keepalive/health_check_interval theo checklist (NAT cloud giết connection nhàn rỗi).
5. **Ping khai trương bể**: trên dev ping từng model lúc khai bể (đã ghi). Trên live, ping là
   TIỀN THẬT ⟹ cho phép chế độ lười qua env (`MODEL_POOL_PING=eager|lazy`): lazy = model được
   đánh dấu "chưa kiểm chứng" và chỉ ping lần đầu được chọn. Mặc định dev=eager, live tự chọn.
6. **Sổ usage.jsonl ghi model per-lượt** (đã có) — trên live đây là chứng từ đối soát hoá đơn
   nhà cung cấp; không được tắt.

### QA/QC — thêm vào cổng xoay 0-token (chạy bằng transport giả, không tốn token thật)
- Ca "bể theo môi trường": đổi `LLM_MODEL_POOL` ⟹ bể đổi theo, KHÔNG cần đổi code/ảnh.
- Ca "thiếu biến" = hành vi cũ một-model (đã ghi) + ca "key thiếu" = chết lúc khởi động, không chạy ngầm.
- Ca "bể cạn toàn phần" ⟹ thông điệp tử tế + không vòng lặp vô hạn (đếm số lần thử có trần).
- Ca "xoay không vượt cost guard": giả lập chạm trần chi phí ⟹ lượt bị chặn TRƯỚC khi gọi model,
  kể cả khi bể còn model sống.

### Bảo Mật
- Key product: xác nhận không bao giờ xuất hiện trong log/trace/sổ (chỉ tên model + trạng thái).
- Cập nhật hồ sơ tuân thủ: dữ liệu khách trên live đi tới model nào của nhà cung cấp — bể live
  phải nằm trong phạm vi đã khai với đối tác (mở rộng đoạn deepseek đã yêu cầu ở brief chính).

### Định nghĩa xong (thêm ô)
- [ ] Bộ config mẫu cho live: `.env.production.example` cập nhật đủ biến mới (POOL, PING mode…),
  có chú thích từng biến — để bước deploy tay của PO thật chỉ là điền giá trị.
- [ ] Cổng xoay 0-token phủ 4 ca live-readiness ở trên.

## 🔴 PO THẬT QUYẾT 19/08 (tối) — PHẠM VI GĐ3: **XOAY + TRẦN CHI TIÊU TỐI GIẢN**

Lead trình đúng và trình sớm: **repo KHÔNG có cost guard.** [ĐO độc lập của PO-agent, khớp Lead]
`grep -rniE "cost_guard|budget|tran_chi|han_muc|chi_phi|spend|usd" src/` → chỉ ra
`graph.py:155 _DAU_HIEU_HET_HAN_MUC` (nhận diện thân lỗi, chạy SAU khi đã gọi và bị từ chối) và
hai dòng chú thích ở `config.py`. `so_usage.py` chỉ có `ghi_usage()` — **GHI, không CHẶN**.
`main.py` có slowapi + sliding-window + concurrency — **đều là RATE LIMIT**. `.env.production.example`
**chưa tồn tại** (ô định-nghĩa-xong phải đọc là **TẠO MỚI**, không phải "cập nhật" — Lead sửa đúng).

**PO thật chọn: KHÔNG phải (a)/(b)/(c) của Lead mà là đường giữa** — xây xoay model đầy đủ,
**CỘNG một trần chi tiêu TỐI GIẢN**: hạn mức token/ngày (hoặc /giờ) đọc từ env, **chặn TRƯỚC khi
gọi model**, dùng chung Redis theo stack. KHÔNG dựng hệ cost guard đầy đủ (theo USD · theo model ·
theo khách) — cái đó là dự án riêng, ghi nợ.

**Phân biệt bắt buộc, đừng gộp hai thứ (chính là lớp lỗi đã có tên — hỏi một giá trị ĐO CÁI GÌ):**
| cơ chế | trả lời câu | chạy lúc nào | trạng thái |
|---|---|---|---|
| `_DAU_HIEU_HET_HAN_MUC` | "nhà cung cấp vừa từ chối vì cạn quota?" | **SAU** khi đã gọi | có, nhưng mới dùng làm NHÃN LOG |
| trần chi tiêu tối giản (MỚI) | "ta đã tiêu quá hạn mức TỰ ĐẶT chưa?" | **TRƯỚC** khi gọi | **CHƯA CÓ — dựng ở GĐ3** |
| rate limit (đã có) | "gọi quá dày chưa?" | trước | có |
🔴 Ba cơ chế, ba câu hỏi khác nhau. Không cái nào thay được cái nào. Dựng vòng xoay lên trên
`_DAU_HIEU_HET_HAN_MUC` rồi gọi đó là "có cổng chi tiêu" là đúng cái bẫy Lead cảnh báo.

**Trigger xoay vẫn là `_DAU_HIEU_HET_HAN_MUC`** — và điều đó ĐÚNG cho ca "hết token free":
quota free cạn là sự kiện chỉ nhà cung cấp biết, ta không thể biết trước bằng sổ của mình.
Nhưng nâng nó từ NHÃN LOG lên ĐIỀU KHIỂN HÀNH VI là nâng hậu quả của một phép khớp-chuỗi mong
manh (chú thích `graph.py:151-154` đã tự cảnh báo đúng điều này) ⟹ **bắt buộc**: giữ khớp chuỗi
làm tín hiệu, nhưng ① ưu tiên mã lỗi/`status_code` khi nhà cung cấp có · ② xoay tối đa N lần/lượt
(N = kích thước bể), hết bể ⟹ thông điệp tử tế · ③ ca QA giả lập "chuỗi lỗi đổi câu chữ" ⟹ KHÔNG
được xoay loạn, phải rơi về nhánh lỗi thường.

## BỂ MODEL — CHỐT theo ảnh console PO thật gửi 19/08 (tối)

```
deepseek-v4-pro-0813 · deepseek-v4-flash · deepseek-v4-pro · deepseek-v3.2 · deepseek-v4-flash-0731
mỗi model: 1M free · consumed 0 · Active · hết hạn 2026-11-15 (88 ngày)
CÙNG tài khoản DashScope với LLM_BASE_URL hiện tại ⟹ cùng key, cùng base_url, KHÔNG đổi biên dữ liệu
```

🔴 **Chi tiết trong ảnh có tính thiết kế, đừng bỏ qua: cả 5 model đang bật "Free quota only".**
- **Hệ quả TỐT:** cạn quota ⟹ nhà cung cấp trả LỖI (đúng trigger ta cần), **không** âm thầm
  chuyển sang tính tiền. Đây là một hàng rào chi tiêu **nằm ở phía nhà cung cấp**.
- 🔴 **Hệ quả phải khai:** hàng rào ấy là **một cái công tắc trên console**, không phải thuộc tính
  của hệ ta. Ai tắt nó (hoặc bể live dùng model không có nó) thì cạn quota = **bắt đầu tính tiền
  im lặng** — và lúc đó trần chi tiêu tối giản của ta là thứ DUY NHẤT còn chặn. Đây chính là lý do
  PO thật chọn làm trần ngay, không hoãn.
- QA/QC: ca "cạn quota trên model có Free-quota-only" và ca "cạn quota trên model KHÔNG có" phải
  cho **cùng một hành vi ở phía ta** (xoay, rồi hết bể thì dừng tử tế) — không được phụ thuộc
  công tắc console.
- Bể free hết hạn **15/11/2026** ⟹ nhắc lại ràng buộc đã có: **bản live KHÔNG được phụ thuộc bể này.**

## 🔴🔴 PO THẬT QUYẾT LẠI 19/08 (tối, muộn) — **THU HẸP PHẠM VI: XOAY DƯỚI HẠ TẦNG, KHÔNG CÓ UI CHỌN MODEL**

**Nguyên văn PO thật:** *"Chúng ta tự đổi model ở dưới hạ tầng — đảm bảo không có lúc nào hết token
— vì hiện tại đang là bản test thôi."*

Câu này trả lời Q1–Q4 của nháp ADR-043 bằng cách **làm cả bốn câu biến mất**. Mục tiêu thật của
tính năng KHÔNG phải "cho khách so sánh model" mà là **"dịch vụ không bao giờ chết vì cạn token"**.

### BỎ khỏi phạm vi GĐ3 — dừng ngay, đừng xây
- ❌ **Hai route `GET /model-pool` · `POST /model-pool/chon`** ⟹ **KHÔNG có route mới** ⟹
  **KHÔNG đụng `authority-matrix.yaml`** ⟹ **KHÔNG cần §10, KHÔNG cần ADR-043 cho route.**
  33 route giữ nguyên, `CONTRACT_VERSION` giữ nguyên.
- ❌ Dropdown/chip chọn model trên UI khách · nhãn "đang trả lời bởi X" trên bong bóng chat ·
  dòng hệ thống báo khi tự xoay.
- ❌ E2E UI ≥3 good case cho "tính năng đổi model" (QA/QC ⑤) — **tính năng ấy không còn tồn tại**.
  Chuẩn ≥3-good-case của PO thật vẫn áp cho MỌI tính năng CÓ UI; xoay model nay không có UI.
- ❌ Câu hỏi "khách có thấy tên model không" (Q4) — không có chỗ nào hiển thị.

### GIỮ nguyên — và một mục nay QUAN TRỌNG HƠN TRƯỚC
- ✅ Bể model qua env · trigger chỉ lớp quota · trạng thái cạn ở Redis có TTL · quyết định model tại
  đầu lượt · trần chi tiêu tối giản · cầu dao (≥N model cạn/60s ⟹ ngừng xoay) · ping khai bể.
- ✅ `usage.jsonl` ghi model per-lượt — nay là **cách DUY NHẤT** biết model nào đã trả lời khách.
- 🔴 **CỔNG NHẬP BỂ (3 good + 3 đối kháng cho TỪNG model deepseek) — nâng lên MỨC CHẶN.**
  Lý do nay mạnh hơn hẳn: xoay diễn ra **im lặng, dưới hạ tầng**, khách **không biết** mình đang
  được model nào phục vụ và **không có cách nào từ chối**. Bộ an toàn 30/30 chưa từng hiệu chuẩn
  trên deepseek. ⟹ **Cổng nhập bể là thứ DUY NHẤT đứng giữa khách và một model chưa ai kiểm.**
  Model chưa qua cổng **KHÔNG được có tên trong `LLM_MODEL_POOL`**. Không có ngoại lệ "tạm để đó".
- ✅ Nguyên tắc chống-đánh-lừa cũ (khách đang test model A không được nhận câu của model B mà không
  biết) **KHÔNG mất hiệu lực — nó chỉ hết đối tượng**: khách không còn chọn model nên không còn
  phép thử nào của khách để đánh lừa. Nếu sau này mở lại UI chọn model, nguyên tắc ấy sống lại.

### ADR vẫn PHẢI viết — nhưng là ADR khác, nhỏ hơn
Không phải ADR route. Là **ADR-043: xoay model tự động dưới hạ tầng** — vì nó **đảo `a3fb125`**
(ghim model theo NGÀY, "đổi model = đổi VẬT"). Nội dung tối thiểu: đảo cái gì · vì sao (bản test,
mục tiêu là không đứt dịch vụ) · hệ quả (mọi phép đo eval nghiêm túc phải GHIM một model; `usage.jsonl`
per-lượt là thứ cứu ta khi đọc số sau này) · phạm vi (chế độ DEMO/TEST, không phải mặc định vĩnh viễn).
Lead soạn, PO-agent land vào `docs/DECISIONS.md`. **Không cần PO thật duyệt lại** — quyết định đảo
đã là của PO thật, ADR chỉ ghi lại.

### Q "key production" — PO thật ĐÃ CHỐT
**Key production KHÔNG BAO GIỜ đi qua phiên agent nào.** Nhận điều khoản (B) của Bảo Mật (bản chốt
`378828c` §2) làm chính sách đứng. PO thật tự điền key trên VPS lúc deploy. Câu "công cụ có tải
transcript lên nhà cung cấp không" ⟹ **đóng bằng thiết kế, không cần trả lời**: agent không có key
production thì câu ấy hết hậu quả.

### Định hạng "Free quota only" — CHUẨN Y bản của Bảo Mật
**Điều kiện BÊN NGOÀI, KHÔNG được ghi là lớp phòng vệ** (Luật R, dạng nặng nhất: có thể biến mất
đúng lúc ta thao tác trên chính console đó). Lớp phòng vệ THẬT ta sở hữu = limiter + `cong_ra_ngoai`
+ trần chi tiêu + cầu dao. Ghi nguyên văn câu Bảo Mật đề nghị vào hồ sơ.

## 🔴 LUẬT CHẶN THÊM 19/08 — **BỂ CHỈ NHẬN TÊN GHIM, KHÔNG NHẬN BÍ DANH TRÔI** (Review tìm, PO-agent chuẩn y)

[ĐO Review] Bể đề xuất có **2/5 tên là bí danh trôi**: `deepseek-v4-flash` · `deepseek-v4-pro`
(không mốc ngày). Ba tên kia đã ghim: `-0813` · `-0731` · `v3.2`.

**Vì sao đây là lỗ THẬT, không phải sạch sẽ hình thức:** cổng nhập bể ký "ĐẠT" cho một bí danh hôm
nay; nhà cung cấp đổi model đứng sau bí danh đó (họ làm thường xuyên — chính lý do `a3fb125` ghim
qwen theo ngày); **chuỗi trong `LLM_MODEL_POOL` không đổi, cổng vẫn hiện "đã ký", nhưng model thật
đang trả lời khách đã KHÁC con được hiệu chuẩn 30/30.** Không cần ai trong đội thao tác sai.
Cùng họ với ca `.env` ghi `qwen3.7-plus` trong khi container chạy `qwen3.7-plus-2026-05-26`.

**LUẬT:** `LLM_MODEL_POOL` **chỉ nhận tên có mốc/ngày/phiên bản cố định.** Bí danh trôi ⟹ **từ chối
lúc khởi động** (fail-fast, cùng chiều với luật secret). Hai model không ghim phải đổi sang bản ghim
tương đương; **nhà cung cấp không có bản ghim ⟹ LOẠI khỏi bể GĐ3**, không phải "để sau".
Lý do loại phải ghi vào hồ sơ — người sau đọc "bể chỉ có 3 model" không được hiểu là bỏ sót.

**Hệ quả cho cổng nhập bể:** chữ ký của QA/QC gắn vào **tên ghim**, không gắn vào bí danh — nhờ vậy
câu "chữ ký còn hiệu lực không" mới có thứ để bám vào khi kiểm lại.

## HẠ TẦNG CHẠY CỔNG NHẬP BỂ — PO-agent chốt cách, Coder cung cấp lệnh

Câu chặn của QA/QC: kiểm từng model TRƯỚC khi nó vào bể bằng cách nào, khi không còn route/UI?
Suy đoán của họ (recreate 5 lần với `LLM_MODEL` override) **BÁC** — 5 chu kỳ đóng băng + Luật U,
đụng compose/.env ngoài vùng ghi tester.

[ĐO PO-agent] `.dockerignore:11` loại `eval/` ⟹ **eval KHÔNG có trong ảnh**, `docker exec` chạy
harness là bất khả. Và venv host `langchain-core 1.5.3` ≠ ảnh `1.5.4` ⟹ **cấm dùng venv host để đo
kích thích gửi model** (luật cũ, vẫn đúng, nay có số).

**CÁCH ĐÚNG — container DÙNG MỘT LẦN từ CHÍNH ảnh đang chạy:**
```
docker run --rm --network <mạng của stack> -v $(pwd)/eval:/app/eval \
  -e LLM_MODEL=<tên-ghim-của-model-đang-kiểm> --env-file .env <ảnh hiện hành> python eval/...
```
- Không recreate stack ⟹ **không đóng băng ai, không cần Luật U**, không đụng vật đang nghiệm thu.
- Đúng `langchain-core` + đúng `src/` của ảnh ⟹ kích thích gửi model **giống hệt** đường khách thật.
- Cùng một mạnh hạ tầng với việc "Playwright chạy TRONG mạng Docker" — **một việc gỡ hai chỗ**.
**Coder** viết lệnh chính xác (đủ tên mạng/ảnh/biến) và giao QA/QC; QA/QC không tự chế lệnh docker.

## 📏 SỨC CHỨA BỂ — SỐ CHÍNH THỨC, mọi số khác đã NIÊM (Luật P)

🔴 **Số ĐANG DÙNG** — [ĐO PO-agent, toàn bộ `usage.jsonl` trong ảnh, 19/08]:
```
163 lượt thật · tổng 1.665.638 token
trung bình 10.219/lượt · trung vị 13.210 · min 0 · max 45.208
61/163 lượt = 0 token (đường nhẹ) · 50% input là CACHED (824.960)
⟹ bể 5M ≈ 489 lượt   ·   150 khách ≈ 3,3 lượt/khách
⟹ 1 model = 1M ≈ 98 lượt ; cổng nhập bể 30 ca ≈ 30 lượt ⟹ LỜI RÒNG ~68 lượt/model
```

⚠️ **NIÊM — số đã chết, đừng trích lại:** *"~176 lượt · 1,2 lượt/khách"* (Lead trình 19/08).
Không sai phép tính; **mẫu số hẹp** — chia bể cho ba ca AUTH nặng nhất của một đợt kiểm thẩm quyền,
bỏ qua 61 lượt đường nhẹ 0 token. Bi quan gấp ~3. Đã có ca dùng lại nhầm (Bảo Mật trích nó như số
của PO-agent) ⟹ niêm tại chỗ. **Kết luận rút ra từ nó KHÔNG đổi:** xoay HOÃN lúc cạn, không XOÁ.

## 🧩 CHÙM NỢ "CÙNG TÊN ≠ CÙNG VẬT" — ba ca, một hình dạng (Bảo Mật gom, PO-agent ghi sổ)

| # | ca | trạng thái |
|---|---|---|
| 1 | base image ghim bằng **tag** `python:3.12-slim`, không phải digest (`Dockerfile:5,:33`) | nợ, chưa làm |
| 2 | `requirements.lock.txt` **không nơi nào dùng** ⟹ 6/168 gói đã trôi | nợ, chưa làm |
| 3 | **bí danh model trôi** (`deepseek-v4-flash`, `deepseek-v4-pro`) | ĐÃ CHẶN 19/08 (e2bebb8) |

**KHÔNG mint luật mới** (§7b): hình dạng này đã có tên từ 17/08 trong docstring `src/dau_ma_nguon.py` —
*"`commit` KHÔNG phải một hàm của `src/`, theo cả hai chiều ⟹ dùng nó làm nhãn ảnh là dùng SAI LOẠI
ĐỊNH DANH"*. Ba ca trên là **cùng mệnh đề ấy áp cho ba loại vật khác** (ảnh nền · gói phụ thuộc ·
model nhà cung cấp). Ghi thành CHÙM để một đợt dọn nợ sau đi cùng một sổ, không phải để cấp ký hiệu mới.
