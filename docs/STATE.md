# Trạng thái hiện tại

## 🔴 ĐANG ĐIỀU TRA (16/08) — DEMO-BUG "gặp người thật ra lỗi": đua-refresh → AUTH5-03 thu hồi family
PO gặp lỗi giữa demo mentor 15/08 (đúng quy trình 2 cửa sổ — giả thuyết đè-phiên BỊ BÁC bởi dữ
kiện PO). **Dữ kiện bổ sung của PO siết thêm:** trước demo họ chạy TRỌN kịch bản KỂ CẢ handoff —
ĐẠT (lướt nhanh <13 phút từ đăng nhập); rồi ĐĂNG XUẤT HẲN, 1 tiếng sau đăng nhập TƯƠI demo thật
— chết ở handoff (>13 phút vì có mentor). ⟹ biến số duy nhất giữa đạt/trượt là THỜI-GIAN-TỪ-ĐĂNG-
NHẬP; loại nghi vấn phiên-cũ-để-rác (family demo là mới sạch). Cặp đối chứng tự nhiên từ đời thật. Giả thuyết hiện tại (coder đọc code xác nhận KHẢ THI CẤU TRÚC, "gần như tất định"):
access token vào cửa sổ refresh (`REFRESH_MARGIN_SECONDS=120`) → handoff là thời điểm đầu tiên có
≥2 request đồng thời (`ChatClient.tsx:195` bắn ws-ticket ngay) → 2 đường cùng refresh bằng MỘT
token dùng-một-lần → đứa thua trúng AUTH5-03 (`auth.py:146-155`) → **thu hồi CẢ FAMILY kể cả cặp
vừa phát** → phiên chết chuỗi → "Có lỗi" trong khung chat. Cờ `rotated` giữ 60s ⟹ KHÔNG cần trùng
mili-giây. Khớp 3 dữ kiện PO + log (`refresh 401`×2, `ws-ticket 401`×4 cụm).
- **TTL access token ĐO ĐƯỢC (tester): 15,0 phút ĐỒNG NHẤT cả 4 role** — khớp chính xác "chat
  ~15-20 phút rồi chết" của PO; con số đó là TTL, không phải cảm giác.
- **Tester tinh chỉnh không gian giả thuyết (từ số đo tối qua, tất định):** một request ĐƠN sau
  khi token chết đã đủ 401 (proxy đặt cookie lên response, handler đọc từ request — 401 rồi lượt
  sau 200, TỰ HỒI). ⟹ đua là **điều kiện ĐỦ chứ chưa chắc CẦN** cho "có lỗi"; nhưng chỉ ĐUA mới
  giải thích được **chết-hẳn-không-hồi** (AUTH5-03 revoke family). Trục phép đo = phân biệt
  "401-rồi-hồi" vs "401-rồi-chết-luôn" (3 lần gọi lại sau đó là phép thử quyết định).
- **HAI QUYẾT ĐỊNH ĐO (tester đề nghị, PO-agent duyệt):** ① **N của grace CHỈ lấy từ dấu thời
  gian SERVER-SIDE** (log `auth.py:150`) — khoảng cách `curl & curl` là độ trễ spawn của MÁY ĐO
  không phải của sản phẩm; lấy N từ đó = hạ một control bảo mật dựa trên hiện vật công cụ (họ 7b,
  hậu quả nằm trong ADR). Số client-side chỉ ghi nhãn "giới hạn trên thô, không dùng định N".
  ② **Instance TTL ngắn (`JWT_ACCESS_EXPIRE_MINUTES=1`, compose project riêng) = HẠ TẦNG ĐO BẮT
  BUỘC vùng auth** — cửa sổ refresh mở ở phút 13 ⟹ k=10 mất 2 giờ; TTL 1 phút → k=30/20phút, và
  test hồi quy vùng auth CHỈ tồn tại được nếu có đường này (Luật 14 chiều thời gian: nhánh không
  chạy NHANH được cũng là nhánh không ai canh). → coder.
- **🏁 TÁI LẬP TRỌN VẸN CA PO (tester, stack demo, backend a216b98c1b79 có tầng-0):** mở /chat →
  2 request → **16 phút ngồi yên KHÔNG một request nào** (trang im hoàn toàn — không heartbeat)
  → token chết lặng → bấm gặp-người-thật → `agent-chat` **401**, màn hình in nguyên văn
  **"Có lỗi: Phiên đăng nhập đã hết hạn"** → **chính response 401 đó mang cookie mới**
  (tầng-0: rotated=1, revoked=0) → gõ lại một tin → **200 + handoff chạy trọn** (~86s sau).
  Cơ chế chốt = đúng khiếm khuyết proxy.ts coder đọc: cookie đặt trên RESPONSE không áp cho
  request đang chạy. Không đua · không revoke · không hồi quy · không hai tab.
  **UI-no-retry BÁC CHO CA NÀY** (agent-chat chết TRƯỚC khi luồng chạm ws-ticket ⟹ ref-guard
  chưa bao giờ bật; lần thử lại đi trọn) — UI-02 vẫn làm trên merit nhưng PR không được claim
  fix-bug-demo. Ref-guard vẫn có thể là lỗ riêng nếu 401 rơi đúng ws-ticket — chưa quan sát,
  không vá mù.
- **🔴 ĐÍNH CHÍNH HỒ SƠ (PO-agent):** câu "PO nói bấm lại vẫn không được" **KHÔNG tồn tại trong
  lời khai nào** — PO chỉ nói "nhận được tin trả lời là có lỗi"; 3 câu hỏi lời khai ĐANG CHỜ.
  Câu đó sinh từ vòng diễn-giải nội bộ rồi được trích như lời khai = **lời-kể-ma ở dữ liệu định
  tính** (họ hàng dấu-băm cho dữ liệu định lượng). Không có mâu thuẫn số-vs-lời — chỉ có câu hỏi
  chưa trả lời (đã hỏi lại bản sắc: GÕ TIN MỚI hay BẤM NÚT trên khung lỗi).
- **Cặp cổng mốc-nền "trước" hoàn chỉnh** (frontend chưa vá): [cổng proxy: sau-ngồi-yên thao tác
  đầu 401] + [cổng tầng-0: rotated=1/revoked=0 ✅]. Điều kiện bắt buộc ghi trong cổng: trang MỞ
  SẴN không điều hướng (goto() tự lành → xanh giả). Coder land hướng-2 → deploy → đo "sau".
- **Drift BÁC bằng đo** (3 image cùng node 20.20.2 / next 16.3.0 / manifest rỗng; `oldc447abb`
  trúng cache toàn phần, timestamp 15/08T13:01Z ⟹ nhiều khả năng CHÍNH LÀ image 15/08 — và nó
  cho 0 Set-Cookie). **Code khớp docs Next 16 từng điểm** (src/proxy.ts đúng chỗ, export đúng
  tên, mẫu cookie đúng docs). Đã bác HẾT 8 giả thuyết. Còn: proxy CHẠY + manifest RỖNG +
  Set-Cookie KHÔNG egress (có đối chứng /api/session=1 header).
- **PO-agent chặn một vòng lãng phí:** câu coder định hỏi ("harness 15/08 có /api/session xen
  giữa?") ĐÃ được tester trả lời từ trưa (chỉ dòng 14 lúc login). Phép hoà giải cuối giao coder:
  grep route handler nào NGOÀI /api/session tự set-cookie (nếu đường ws-ticket có → +842s là
  cookie từ ROUTE HANDLER, không phải proxy → mâu thuẫn tan). Không có → +842s = dị thường lịch
  sử, GHI KHÔNG LẤP KHÔNG CHẶN (nếp MT-E02).
- **QUYẾT: HƯỚNG (2) GO — không chờ giải dị thường.** Refresh chuyển xuống `backendFetch()` MỘT
  điểm chặn: 401 → refresh → set-cookie trên response route handler (đường ĐÃ chứng minh egress).
  Điều kiện đóng: single-flight per-request trong backendFetch (không tái tạo bug đua tầng mới) ·
  test cấu trúc canh proxy-đăng-ký · cổng đo request-1-VÀ-2 + family-không-revoke · gỡ phần
  refresh chết khỏi proxy.ts có ghi lý do · security re-probe. Sau land: PO-agent viết ADR-026
  ghi quyết định + trọn lịch sử điều tra.
- **Bước (1) coder: khả-năng-(3) BÁC có đối chứng** (`/api/session` route-handler-tự-set-cookie
  grep THẤY ⟹ dụng cụ không hỏng; ws-ticket + trang /chat đều 0 set-cookie). Thu hẹp: middleware
  CHẠY nhưng **mọi mutation lên response bị BỎ** — proxy.ts biên dịch + thực thi nhưng KHÔNG được
  đăng ký như middleware thật (manifest rỗng khớp). Hai hướng vá treo: (1) sửa đăng ký Next 16 /
  (2) chuyển refresh xuống backendFetch (một điểm chặn).
- **🔍 PO-agent chỉ ra MÂU THUẪN DỮ KIỆN = lối tắt:** tối 15/08 tester đo image THẬT đang chạy —
  **cookie CÓ XOAY tới client** (+842s đọc từ jar); hôm nay rebuild TỪ CÙNG COMMIT `c447abb` →
  0 set-cookie. Cùng mã, hai hành vi ⟹ nghi phạm mới ngoài cả 3 khả năng: **DRIFT PHỤ THUỘC lúc
  build** (base image node tag di chuyển / Next patch khác). Phép kiểm rẻ giao coder TRƯỚC khi
  đọc docs: tìm image thật 15/08 còn trên đĩa (untagged/dangling) → so version Next + manifest
  hai bên. Version khác = root là drift → vá bằng GHIM dependency (digest base image + lockfile).
- **Điều kiện đóng RATIFY bất kể hướng:** thêm test CẤU TRÚC canh middleware-được-đăng-ký
  (manifest không rỗng / probe cookie-tới-client trong e2e) — middleware chết im lặng không ai
  biết bao lâu là bài học lớn nhất vụ này (Luật 14). Tiêu chí chọn hướng đã chốt sẵn: cấu-hình-
  có-tài-liệu→(1); mơ hồ→(2) qua MỘT điểm chặn backendFetch.
- **🎯 CƠ CHẾ CỤ THỂ NHẤT TỪ ĐẦU (coder đo 1-request sau khi vá thử, CHƯA LAND):** middleware
  chạy ĐÚNG MỘT lần (đo) · backend xoay token THÀNH CÔNG (tầng-0 `refresh_rotated`) · **Set-Cookie
  KHÔNG BAO GIỜ RỜI SERVER** (header response không có set-cookie) ⟹ request kế cầm token cũ đã
  rotate → AUTH5-03 revoke. Không đua, không hai-lần-gọi — **cookie mất trên đường ra**. Bản vá
  hiện tại của coder chỉ sửa vế route-handler-thấy-token-mới (cần) — CHƯA sửa vế browser-nhận-
  cookie (vế giết phiên). **Coder TỪ CHỐI LAND** vì cổng tester ("request đầu 200") sẽ xanh trong
  khi phiên vẫn chết ở request thứ hai — xanh-cổng-mà-không-hết-bệnh. Thứ tự duyệt: kiểm khả-năng-
  (3) (chính bản vá làm mất cookie — rẻ nhất, nghi-mình-trước) → rebuild demo backend sau khi
  tester xong → chốt hình dạng vá. **Cổng nghiệm thu MỞ RỘNG: đo cả REQUEST THỨ HAI** (req1 200 ∧
  req2 200 ∧ family không revoke). UI-02+retry song song.
- **Quy ước báo-trước-rebuild TRẢ LÃI trong 1 giờ:** tester xin coder giữ tay rebuild vì phép đo
  đang chạy — rebuild giữa chừng KHÔNG làm phép đo đỏ, nó vẫn in số, chỉ là số của HAI backend ở
  hai nửa lượt (dạng vật-trôi nguy nhất: không triệu chứng). Lần thứ tư vật-trôi trong hai ngày,
  lần ĐẦU tránh được nhờ báo trước.
- **✅ KHÉP VÒNG SỐ (coder xác nhận bằng bằng chứng mạng):** cả 11 refresh + cặp 10/10 đều ở
  backend fin05ttl (172.20.x), client là middleware TTL, probe của chính coder — "10/10 mô tả
  instance TTL, chấm hết"; coder tự nhận *"nặng hơn vì chính tôi dựng instance đó rồi quên nó là
  vật khác"*. Cơ chế TTL-là-chế-độ-biên xác nhận: TTL 60s < margin 120s ⟹ token TRONG cửa sổ
  refresh từ giây đầu ⟹ refresh MỌI request (production: 2 phút cuối/15). Cảnh báo ghi thẳng vào
  `docker-compose.ttl-test.yml`. Demo backend CHƯA có tầng-0 (build trước a74de7d) → việc-0:
  rebuild theo quy ước báo-trước-khi-rebuild-image.
- **✅ REF-GUARD XÁC NHẬN ĐỌC-MÃ (mảnh ráp trọn ca PO):** `liveChatConnectStartedRef` đúng 3 dòng,
  KHÔNG reset ở đâu — một lần thử vĩnh viễn. Chi tiết chốt: nhánh `.catch` bảo khách *"thử lại
  giúp mình nhé"* trong khi KHÔNG TỒN TẠI đường thử lại (effect chỉ chạy lại khi liveChatTicketId
  đổi — nó không đổi). ⚠️ Điều kiện nghiệm thu vá (ratify): reset-ref KHÔNG đủ (deps không đổi thì
  effect không chạy lại) — cần đường thử-lại THẬT (nút/retryCount trong deps), GIỮ chống-StrictMode;
  e2e assert "sau 401 đầu, UI CÓ bắn request thứ hai khi thử lại".
- **GREENLIGHT đã phát:** ① vá `proxy.ts` cookie-trên-request (PR, gate: cổng hồi quy tester +
  re-probe security) · ② UI-02+retry (PR) · ⓪ rebuild demo backend lấy tầng-0 (xin khe tester).
  Lời khai PO (đã hỏi 3 câu) không chặn vá — nó quyết có CÒN cơ chế nào ngoài hai defect đã chốt.
- **⚖️ PHÂN XỬ CUỐI (tester, log server-side, MỘT request sạch):** `rotated=1 · family_revoked=0
  · HTTP 200` ⟹ refresh gọi ĐÚNG MỘT lần, chạy THÀNH CÔNG, không thu hồi gì. **Cặp "10/10 tất
  định" là TỔNG TÍCH LUỸ của nhiều lượt thử trộn lẫn** (gồm cả probe song song của tester) — suy
  nhân-quả từ hai tổng bằng nhau = ca sách giáo khoa **đếm-tổng không thay được đếm-theo-lượt**
  (LUẬT MỚI). Số +842s cũng khép: chuỗi đầy đủ 200→(16 phút)→401-vì-token-MỚI-cũng-hết-hạn→200→200
  — phiên sống khoẻ, không cần cơ chế thu-hồi nào để giải thích.
- **VẬT ĐỔI LẦN BA** (image TTL bị dựng lại giữa hai phép đo → "TTL không rotate" RÚT). **RATIFY
  quy ước đội:** ① mọi phép đo trên stack kèm IMAGE ID trong nhãn; ② **ai dựng lại image phải báo
  vai đang đo** — luật BÁO-TRƯỚC-KHI-LAND mở rộng sang image.
- **CHỖ ĐỨNG THẬT SAU MỌI SỐ:** thứ DUY NHẤT tái lập được = hiện vật `proxy.ts:112` — *token hết
  hạn ⟹ request đó 401, cookie mới về client, request KẾ 200*. KHÔNG tái lập được: đua-giết-phiên
  · thu-hồi-family · refresh-không-chạy · hồi-quy-image. Ứng viên ráp trọn ca PO: hiện vật 401-
  một-lần + **UI ref-guard không-bao-giờ-thử-lại** (`ChatClient.tsx:199` — PO-agent góp, chờ e2e
  + coder xác nhận). Mảnh quyết định còn thiếu: **lời khai PO — lúc lỗi có thao tác lần hai
  không, kết quả gì** (đang hỏi).
- **✅ CƠ CHẾ CHỐT (16/08 tối, bằng chứng server-side tầng-0):** middleware refresh CÓ chạy nhưng
  **nuốt lỗi im lặng**; cặp log `refresh_rotated`×10 ↔ `refresh_family_revoked`×10 **ghép 1-1 tất
  định**: cookie mới đặt lên RESPONSE, lượt gọi refresh THỨ HAI trong cùng vòng request vẫn cầm
  token CŨ → AUTH5-03 thu hồi family — **hệ TỰ BẮN VÀO CHÂN, không cần user sai, không hai tab,
  không đua.** Dòng-A (hồi quy UI-01) BÁC bằng đo (image c447abb hành xử y hệt, proxy.ts 0 byte
  đổi); ứng viên-4 cũng sai ("không chạy" = "chạy-thất-bại-nuốt-lỗi"). **Dòng B (bug demo PO)
  được giải thích trọn**: sau phút 15, lượt đầu tiên rotate+tự-thu-hồi → mọi thứ 401.
  **Grace-window RÚT khỏi kế hoạch** (bug tất định của client, không phải đua hiếm — AUTH5-03 giữ
  nguyên, nó vừa chứng minh làm đúng việc). Còn lại: tester đếm `refresh_rotated` trên ĐÚNG MỘT
  request (phân xử vì-sao-gọi-hai-lần, quyết hình dạng vá) → coder vá (hướng: request-headers cho
  lượt sau thấy token mới) → hồi quy TTL → security re-probe → đóng.
  Coder tự khai: suýt kết luận sai BA lần từ artifact tĩnh — thứ cứu là hỏi-hệ-thống-một-câu-khác
  thay vì đọc-kỹ-hơn-cùng-một-chỗ.
- **🔴🔴 BƯỚC NGOẶT (16/08 chiều): KHÔNG AI ĐO SAI — VẬT ĐỔI. Image frontend stack demo được DỰNG
  LẠI 2026-08-16T02:11Z** (12,5h sau phép đo exp+842s; nghi là lần deploy UI-01). **Image cũ:
  refresh CHẠY** (exp+842s = một lần xoay thật, harness tester sạch — không /api/session xen giữa,
  đã kiểm). **Image mới: refresh CHẾT** (cả hai endpoint, phủ-đều-bằng-không). Hai image ID:
  `90d7b915bcbf` (mới) vs `210edbc5a06a` (TTL). ⟹ **TÁCH HAI DÒNG ĐIỀU TRA:**
  · **Dòng A — HỒI QUY refresh (ưu tiên 1, ĐANG SỐNG trên stack demo):** mọi phiên chết cứng phút
    15. Coder dựng image từ commit trước 15/08T13:43Z probe đối chiếu → chốt hồi quy → tìm diff
    trong cửa sổ [demo-GO … 6a07b16+lô cùng deploy].
  · **Dòng B — BUG DEMO 15/08 của PO: CHƯA GIẢI.** Nó xảy ra trên IMAGE CŨ nơi refresh CHẠY ⟹
    ứng viên "refresh chưa bao giờ chạy" KHÔNG giải thích được nó; và MỌI số Pha A/C/D hôm nay đo
    trên hệ đã-hồi-quy — nói về dòng A, không nói được gì về B. Đua-revoke/harness sống lại làm
    ứng viên; đo lại B chỉ được SAU khi A vá (cần hệ có refresh chạy). CẤM vá single-flight/grace
    tới khi B đo trên vật đúng.
- **📌 Lỗ nhãn phép đo (tester tự nhận): `he_thong` băm `src/**/*.py` — KHÔNG phủ `frontend/`**,
  mà refresh sống ở `frontend/src/proxy.ts` ⟹ vật trôi ngay dưới chân phép đo, cái ghim mù trước
  nó. Từ giờ nhãn phép đo kèm **IMAGE ID** (+ SHA + he_thong) cho mọi phép đo chạm frontend.
- **🔄 ĐẢO BÀN CỜ (16/08 chiều — coder đọc-mã + đo trên instance TTL):** `refreshSessionIfNeeded`
  có đúng MỘT call-site (`proxy.ts` dòng đầu, matcher phủ mọi `/api/*`) — phủ ĐỀU, **nhưng đo ra
  phủ-đều-BẰNG-KHÔNG: không endpoint nào xoay cookie** (TTL=1ph < margin=120s ⟹ mọi request trong
  cửa sổ; đã loại backend-unreachable + image-cũ). ⟹ **Ứng viên cơ chế THỨ TƯ, đơn giản nhất:
  refresh KHÔNG BAO GIỜ CHẠY** — token chết phút 15, "15-20 phút rồi lỗi" của PO = TTL, handoff
  chỉ tình cờ là thao tác đầu tiên sau mốc. Nếu đúng: single-flight = vá thứ không tồn tại, grace
  không áp dụng — bản vá đúng là LÀM CHO REFRESH CHẠY. **CẤM viết vá tới khi phân xử.**
  Mâu thuẫn còn lại: số tester tối qua (`ws-ticket` exp+842s = một lần refresh thật) vs 0 hôm nay
  → kiểm (a) rẻ nhất: tester đọc lại harness tối qua tìm `/api/session` xen giữa; (b) nếu âm:
  probe stack demo phút 13. Tầng-0 log đã LAND `a74de7d` (trường `refresh_rotated` server-side).
  Instance TTL SỐNG: `https://localhost:8443`, project `fin05ttl`, 208 user, stack demo nguyên vẹn.
- **📌 Tri thức mới (coder tự bắt khi đo):** compose đặt tên IMAGE theo PROJECT — hai stack = hai
  image khác nhau (`fin05-frontend` ≠ `fin05ttl-frontend`); đo trên stack TTL mà so với số stack
  demo là ĐO NHẦM VẬT. Phát hiện bằng `docker inspect`, chữa bằng build-lại-từ-nguồn cho khớp.
  Nhãn phép đo đa-stack phải kèm IMAGE ID.
- **Tái lập đang chạy nền (~32 phút, 0 TPM):** Pha A đua (2 request song song cùng chuỗi cookie
  cũ, đúng cảnh browser 2 request in-flight) + Pha B đối chứng tuần tự. Qua đúng đường BFF
  `https://localhost/api/live-chat/ws-ticket` = đúng chỗ PO chết. Giới hạn tự khai: bắn 2 request
  CÙNG endpoint — nếu single-flight có ở đường này thiếu ở đường khác thì đo không thấy ⟹ Pha A
  xanh = "chưa tái lập bằng cách này", KHÔNG phải "giả thuyết sai".
- **Coder chờ số mới vá**: single-flight promise module-scope `proxy.ts` — tự khai giới hạn *chỉ
  chặn đua cùng tiến trình Node*; scale nhiều replica frontend cần khoá Redis (ghi vào bản vá).
- **Ý KIẾN SECURITY VỀ AUTH5-03 (`2cff494`) — ba tầng, định hình cả lô vá:**
  ① **Single-flight: CẦN nhưng KHÔNG ĐỦ** — promise dùng chung chỉ phủ MỘT ngữ cảnh JS; **đa-tab
  là hai ngữ cảnh không thấy nhau**, mà CSKH mở nhiều ticket nhiều tab là cách làm việc bình
  thường ⟹ vá single-flight làm bug biến mất trong demo một-tab rồi QUAY LẠI trên bàn làm việc
  thật, lần sau khó truy hơn vì "đã vá rồi mà". Vẫn làm (rẻ, đúng), nhưng KHÔNG coi là xong.
  ② **Grace-window: DUYỆT đúng MỘT dạng — PHÁT-LẠI-BẤT-BIẾN** (trong N giây, cùng token cũ trả
  ĐÚNG cặp đã cấp lần đầu). **BÁC dạng cấp-cặp-mới** (tạo hai phiên phân kỳ = đúng thứ rotation
  sinh ra để chặn). Bốn điều kiện: bất biến · N NGẮN vài giây lấy từ PHÂN BỐ ĐO ĐƯỢC không lấy số
  tròn · bắn-trong-grace log nhánh riêng · ngoài N giữ nghiêm. **KHÔNG land trước khi có số tester.**
  ③ **🔴 FINDING NẶNG HƠN CẢ CÂU HỎI: `auth.py` 294 dòng KHÔNG MỘT DÒNG LOG** — `revoke_family()`
  (sự kiện "chúng tôi tin token bị đánh cắp" — lớn nhất của cả hệ xác thực) bắn HOÀN TOÀN IM LẶNG.
  Không đếm được AUTH5-03, không phân biệt được đua-vs-trộm trên production, **chỉnh control không
  quan sát được = chỉnh mù**. Vá TRƯỚC hoặc CÙNG lô, rẻ nhất trong ba việc: log cấu trúc tại
  `auth.py:150` (family_id · user_id · role · nhánh `reuse_that`/`phat_lai_trong_grace`). Đây
  cũng là lý do bug demo thành bí ẩn: control bắn đúng mà không để lại dấu vết nào.
- Nối finding cũ: đường proxy-cookie (401-rồi-200) LUÔN tiêu một lượt refresh → chồng thêm request
  là 401-vô-hại thành thu-hồi-family ⟹ bản vá proxy.ts backlog NÂNG mức quan trọng.
- UI-01 (timeline không-JSON) đã land `6a07b16` + deploy stack demo. UI-02 (banner lệch-vai) vẫn
  đáng làm, xếp sau.
- Workaround demo tới khi vá: đăng nhập lại vai khách NGAY TRƯỚC màn gặp-người-thật.
Cập nhật: **2026-08-15 (phiên Đợt 2 + bàn giao P-226)** · PO-agent điều phối 4 vai (Claude Code)

## 🔄 BÀN GIAO SANG P-226 — ĐỌC ĐẦU TIÊN
> **Repo đã migrate từ P-121 → P-226 (đầy đủ lịch sử).** Nhánh làm việc: `dev/learning-loop`
> (HEAD dacbefd, 256 commit). `main` = 104 commit. Đang code trong thư mục `P-226`.
>
> **Bối cảnh dự án:** FIN-05 — AI Agent CSKH ví điện tử xử lý khiếu nại, chuẩn fintech EU/US.
> Đội = 4 phiên Claude Code (PO-agent điều phối · coder/tech-lead · tester · security), đồng bộ
> qua **git + cross-session message** (SendMessage/ListAgents), mỗi vai chỉ ghi vùng của mình (§4).
> ⚠️ **CÂY LÀM VIỆC DÙNG CHUNG giữa 4 phiên** → mọi `git stash/commit/checkout/clean` **phải kèm
> pathspec vùng của mình**. Lệnh không pathspec sẽ cuốn theo việc đang dở của vai khác.
>
> **PHIÊN MỚI Ở P-226 làm gì trước:** đọc `CLAUDE.md` (hiến pháp) → file này → sổ Đợt 2
> `docs/giao-viec/2026-08-15-ke-hoach-3-chu-de-nang-cap.md` (18 luật đo + mọi finding) →
> 5 ADR gần nhất trong `docs/DECISIONS.md` (tới ADR-024). Đó là toàn bộ ký ức Đợt 2.
>
> **AI-log (đo lại 15/08 tại P-226 — mục cũ ghi theo P-121, KHÔNG đúng cho repo này):**
> Lớp THU log chạy tốt (`.ai-log/session.jsonl`). Nhưng lớp GỬI cần ba thứ, **hook không đi
> theo git nên migration làm mất hai thứ đầu**:
> 1. `.git/hooks/pre-push` — P-226 ban đầu KHÔNG có (chỉ còn `.sample`); cài bằng
>    `bash scripts/setup_hooks.sh`. Hook là file local, migration `.git` mới là mất.
> 2. `.env` với `AI_LOG_SERVER` + `AI_LOG_API_KEY` — P-226 ban đầu KHÔNG có `.env`.
>    Thiếu → `submit_log.py` in "AI_LOG_SERVER not set" rồi `exit 0` **im lặng**, push vẫn xanh.
> 3. `SSL_CERT_FILE` — **thiếu thì trượt `CERTIFICATE_VERIFY_FAILED`** (đo thật lúc push
>    `954a6a9`). ⚠️ **Phải ghi ĐƯỜNG DẪN THẬT** (`.../certifi/cacert.pem`, lấy bằng
>    `python3 -c "import certifi; print(certifi.where())"`) — dạng `$(python -m certifi)` mà
>    bản STATE trước ghi là **SAI**: `python-dotenv` không chạy command substitution, nó đọc
>    nguyên văn chuỗi `$(...)` thành đường dẫn rác.
>
> **AI log KHÔNG đi qua commit** — `.gitignore:74-75` loại `.ai-log/*.jsonl`; log được POST
> lên grading server bởi pre-push hook, tức lúc **`git push`**, không phải `git commit`.
> Trượt submit KHÔNG chặn push (`exit 0` cuối hook) và log được giữ lại nguyên vẹn (đường
> `_restore_pending` đã verify thật: 0 dòng mất sau lần trượt SSL).
>
> **✅ ĐƯỜNG AI-LOG P-226 ĐÃ THÔNG — verify thật 15/08, push `eadcca7`:**
> `[ai-log] Submitted 73 entries → 202` · `.ai-log/archive/2026-08-15.jsonl` sinh ra với đúng
> 73 bản ghi, parse JSON 73/73 hỏng 0, metadata đúng (`repo=P-226` · `branch=dev/learning-loop`
> · `student=jin.simple@gmail.com`).
>
> **Chuỗi chẩn đoán 4 lượt push (giữ lại vì mỗi nấc hỏng cho một triệu chứng KHÁC nhau):**
> `954a6a9` CERTIFICATE_VERIFY_FAILED (thiếu SSL_CERT_FILE) → `3f59e3e` **401** (SSL thông) →
> `e6e5f7b` 401 (không đổi vì key chưa thay) → `eadcca7` **202 ✅** (key mới `ai20…` 38 ký tự,
> lấy từ link mời BTC; key cũ `f3p1…` 64 ký tự chép sang từ P-121 là key ĐÃ THU HỒI).
> `LANGCHAIN_*` KHÔNG liên quan tới đường này: `submit_log.py:28-30` chỉ đọc `AI_LOG_SERVER` ·
> `AI_LOG_API_KEY` · `AI_LOG_DIR`.
>
> ⚠️ **Hỏng IM LẶNG — đừng lấy "push xanh" làm bằng chứng.** Hook `exit 0` nên push luôn
> thành công dù submit trượt; dòng `[ai-log] Submit failed` lẫn giữa output git. **Bằng chứng
> khách quan DUY NHẤT là `.ai-log/archive/`** — chỉ sinh ra SAU khi POST thành công.
> `session.jsonl` BIẾN MẤT sau lần gửi được là ĐÚNG THIẾT KẾ (atomic rename), hook tạo lại ở
> lượt ghi kế tiếp — đừng tưởng mất log.
>
> **AI_LOG_API_KEY mới đã hoạt động ở P-226.** LANGCHAIN tạm TẮT có chủ đích
> (`LANGCHAIN_TRACING_V2=false`, key rỗng) — PO quyết gác lại, không chặn gì.
>
> **CÒN TREO — backlog P-121: 9133 dòng ở `P-121-new/.ai-log`.** Phải **thay key mới vào
> `P-121-new/.env` nữa** (nơi đó vẫn là key `f3p1…` đã thu hồi) rồi push từ P-121.
> **ĐỪNG xoá P-121-new tới khi submit xong** (deliverable #4). Liệu lịch: `BATCH_LIMIT=500`
> mỗi lần push ⟹ cần **~19 lượt push**, không phải một phát xong.
> ⚠️ Nhánh leftover của `_archive_entries()` (vá ở `eadcca7`) **CHƯA từng chạy thật** — lượt
> 15/08 chỉ có 73 bản ghi, dưới ngưỡng 500 nên không sinh leftover. Backlog P-121 sẽ là lần
> ĐẦU TIÊN nhánh đó chạy; kiểm `wc -l .ai-log/archive/*.jsonl` sau 2 lượt push đầu để chắc
> archive không phình trùng lặp.
>
> **Việc còn treo (không chặn, đã có tài liệu trong sổ Đợt 2):** đợt nâng CỔNG-A gộp 3 oracle
> (số-ngắn+tên+phủ-định) theo xuất-xứ · câu-4 RAG retrieval quality (3/5 câu chính sách hợp lệ agent
> không trả được — sửa chunk/embedding, KHÔNG nới ràng buộc 9) · MT-E02 traceback · hạ tầng đo temp=0/k≥3.
>
> **Chờ PO thật:** tạo lại keys · hướng đợt 150 người (lượt end-to-end đã cho dữ liệu: bộ lọc 17/17
> không siết nhầm, RAG retrieval là điểm yếu; 4 góc chưa-sẵn-sàng: TPM · 429→500 · timeout · RAG).


> Nhánh: **`dev/learning-loop`**. Sổ điều phối Đợt 2 (đầy đủ, ~18 luật + mọi finding):
> `docs/giao-viec/2026-08-15-ke-hoach-3-chu-de-nang-cap.md`. Đêm 14→15/08: sổ `2026-08-14-*`.
> Đồng bộ = git (4 vai cùng repo). Cơ chế: dấu-băm mọi phép đo · nháp-ngoài-repo · báo-trước-khi-land.

## Vừa xong (Đợt 2 — nhánh 5b chống-injection, verified CẢ HAI nửa)
- **Spotlighting** (F-22/23/24/25/26) — bọc dữ liệu untrusted 4 cửa, nhãn TRUNG TÍNH, verify trong container.
- **Lọc đầu ra O1-O4 + luật XUẤT XỨ** (số agent nói phải truy về tool result — trùng ràng buộc cứng 3):
  origin-rule verified 14/14 (corpus độc lập tester) · efficacy 15/16 · chặn-nhầm 0/8 · 0 gán-sai-nhóm.
  Vá dọc đường: JSON-comma phantom (hai-kênh) · F-27 (bỏ neo chữ "OTP") · F-26 (nhãn-sau-scrub).
- **5a (cảm xúc) contract v2.4.0/v2.5.0 ĐÃ KÝ TOÀN BỘ Câu 1+2+3** (ADR-022): thread_signals +
  emotion_signals dựng xong. **Câu 3 (chip câu CSKH) PO thật duyệt 15/08**: khung "chip vận-hành
  mức hội-thoại, KHÔNG nhãn tâm-lý" + N=3 (cùng ngưỡng nút-khách) + **CSKH thấy chip** — xem
  `docs/giao-viec/2026-08-15-spec-cau3-dau-hieu-cam-xuc-cskh.md`. CHƯA CODE (xếp sau 5a core).
- **F-25(b) cổng siết-nhầm** (0-TPM, đã chứng minh hoạt động).
- **Luật 18 (ADR-023)** — khớp cụm cho phép chèn hư từ + mỏ neo QUY TRÌNH cho O2 — LAND
  (`221abb5`, `8d26548`), retroactive F-24/F-27.
- **`resolutions.note` + `note_flagged` (ADR-024)** — LAND (`7b68992`), field ẩn duy nhất nơi
  văn bản tự do nhân viên gõ đi vào bản ghi kiểm toán; scrub tại điểm ghi, fail-closed, ép ở DB.
- **Lượt đo end-to-end "sau" O1-O4 ĐÃ CHẠY** (`e4ef0e8`) — sửa bug 21/24 ở câu 2, **cổng-96 giờ
  BẬT THẬT** (không còn tắt), raw lượt end-to-end đã lưu.
- **Seed test USR-0119/USR-0201 xong** (`dacbefd`, tester) — lộ + vá 2 bug ẩn: TXN-0001 không
  "mượn" được cho user mới (đã parametrize `trans_id`), import sai module
  (`src.tools.registry`→`src.agents.tools.customer_tools`), guard cổng-96 kiểm nhầm payload
  toàn cục thay vì đúng tập mốc nền đang dùng.
- **Xác nhận trạng thái THẬT trong phiên này (Luật 9, 2026-08-15, PO-agent dựng venv sạch chạy
  từ đầu — không suy luận từ code tĩnh):**
  - `pytest tests/test_invariants.py -v` → **23/23 PASSED**, 0 failed.
  - `pytest tests/test_api/test_reject_note_doi_khang.py tests/test_migrations/test_trang_thai_dich_nhip_note_f11_f13.py`
    → **15 passed, 8 skipped** (0 failed) — skip có lý do rõ: 7 ca cần Postgres thật (env test
    dùng `sqlite:///:memory:`), 1 ca chờ exporter Phase 2 chưa tồn tại. KHÔNG có `khong_do_duoc`
    lạ nào.
  - `pytest tests/test_security/ -q` → **38 passed, 26 skipped**, 0 failed.
  - Môi trường test cục bộ trước đó CHƯA từng được dựng ở máy chạy phiên PO-agent (thiếu
    `argon2`, thiếu model NER `xx_ent_wiki_sm` của presidio) — đã dựng venv scratchpad + cài đủ,
    không phải bug sản phẩm.

## Đang dở — chi tiết đủ tiếp ngay
- **Chip câu 3 (dấu cho CSKH)** — PO thật đã duyệt khung+N=3+CSKH-thấy (xem "Vừa xong"). CHƯA CODE:
  coder xếp SAU 5a core + sau QA baseline (thứ tự đã định từ sổ Đợt 2). Câu hỏi kỹ thuật còn treo
  (không cần PO quyết lại, coder tự đề xuất): cần thêm 1 trường envelope riêng cho kênh CSKH, hay
  tái dùng cờ ES sẵn có mà khách cũng đọc — xem đặc tả §4.
- **Đợt nâng CỔNG-A** gộp 3 oracle (số-ngắn+tên+phủ-định "không phải 21") theo xuất-xứ + dữ liệu
  phân phối — chưa làm, có tài liệu ở sổ Đợt 2.
- **Câu-4 RAG retrieval quality** — 3/5 câu chính sách hợp lệ agent không trả được. Sửa chunk/embedding,
  KHÔNG nới ràng buộc 9. Mốc: trước pilot 150 người.
- **MT-E02 traceback** — cơ chế chưa rõ, giữ quan sát, ĐỪNG đốt TPM tái hiện chủ động.

## 🚀 GÓI DEPLOY HOME-SERVER (đêm 15/08, đang chạy) — sự thật nền tảng ĐÃ SỬA HAI LẦN
- **PO thật quyết:** demo mentor XONG → deploy production lên **máy bàn Windows 24/7 ở nhà PO**,
  domain `app.adaptivealgo.uk`, đường ra **Cloudflare Tunnel** (không cần IP công khai/mở port).
- **Sự thật đã kiểm (đè MỌI tài liệu cũ):** KHÔNG có VPS nào tồn tại — `app.adaptivealgo.uk`
  không phân giải; `docs/DEPLOY.md` là tài liệu đợt P-121 CHƯA AI THỰC THI (còn trỏ repo
  P-121-new). Demo chạy localhost Docker trên Mac PO. Domain gốc `adaptivealgo.uk` ĐÃ đăng ký,
  NS = Cloudflare — PO đang kiểm quyền truy cập tài khoản.
- **Hai lần PO-agent sai tiền đề trong CÙNG gói này (Luật 9, ghi để không lặp):** (1) coi VPS
  trong DEPLOY.md là hạ tầng sống; (2) brief cho coder ghi "main đang là bản demo GO" — SAI, demo
  chạy từ `dev/learning-loop`, main đứng sau **220 commit**, thiếu cả vá SSL_CERT_FILE compose lẫn
  hotfix quick-login. Coder DỪNG trước khi viết và bác brief bằng số — nếu làm theo, production
  đêm đầu chết mọi lượt chat.
- **CHỐT NHÁNH: fast-forward `main` lên `dev` HEAD** (PO-agent đo: `dev..main = 0` commit riêng ⟹
  merge là FF thuần, main = đúng cây đã nghiệm thu 540 passed + 2 chữ ký security). Lệnh có chốt
  `--ff-only`. Gói home-server land trên main sau FF.
- **HAI BẪY `.env` khi chuyển máy (coder phát hiện, vào doc từng-bước-bấm):** ① `FIELD_ENCRYPTION_KEY`
  phải GIỮ NGUYÊN (đổi = dữ liệu mã hoá thành rác vĩnh viễn); ② `SSL_CERT_FILE` là đường dẫn
  macOS, PHẢI sửa khi sang Windows — *"`.env` càng được mang sang trung thành thì lỗi càng chắc
  chắn tái hiện"*. Bẫy chết-dữ-liệu và bẫy chết-dịch-vụ, khác nhau, cùng một file.
- Việc tay của PO thật: ✅ Cloudflare CÓ domain (PO xác nhận) · đang tạo tunnel (ô Service điền
  **`caddy:80`, Type HTTP** — KHÔNG điền localhost) · cài Docker Desktop/WSL2 máy Windows ·
  Never-sleep + Docker start-at-login. Nghiệm thu cuối = mở `https://app.adaptivealgo.uk` từ
  **4G tắt WiFi** thấy màn login — phép thử DUY NHẤT được tính.
- **✅ GÓI LAND trên `main` `7ce57bd` — SẴN SÀNG CHỜ TOKEN.** FF main làm bằng `push origin
  HEAD:main` (server từ chối non-FF = giữ chốt an toàn, KHÔNG checkout — cây làm việc dùng chung
  4 phiên, checkout là giật file khỏi tay 3 vai kia; lệnh gốc của PO-agent quên điều này). Verify:
  `03d02da..a694ff1` · diff rỗng · demo-GO→HEAD chỉ 1 commit docs.
- **📌 Tri thức mới (coder đo):** `docker compose` NỘI SUY BIẾN cho MỌI service kể cả service bị
  profile loại — `${VAR:?}` fail-fast trong compose RÒ sang mọi người dùng compose, không riêng
  người bật profile. Fail-fast cho service optional phải đặt ở SCRIPT cửa vào của đường đó.
- **⚠️ Khai minh thị:** `deploy_home.ps1` mới review bằng mắt, CHƯA chạy thật (máy không có pwsh);
  bản `.sh` đã chạy thật cả hai cổng. PO gặp lỗi cú pháp `.ps1` → dùng `.sh` trong WSL, đó là
  đường lui có sẵn.

## 🚨 SỰ CỐ KHO + ĐÒN 4 LAND — MỐC 35,7% VÔ HIỆU KÉP, chờ cặp sạch (16/08)
- **SỰ CỐ (chạm ràng buộc cứng 3):** kho đang-phục-vụ bị nạp 2 file NỘI BỘ lúc 08:23 (hai lần nạp
  thẳng cách 15s, KHÔNG qua nap-lai): `business_rules.md` 20 chunk (bảng số verified=false) +
  `scenario-candidates-momo-faq.md` 37 chunk (kịch bản test). Agent trích cả hai **như chính sách
  thật**. Coder đã GỠ + chặn `_chon_nguon` chỉ nhận `.docx/.pdf` (kèm docstring lý do — bản nháp
  commit của chính coder cũng suýt nạp .md, bắt được nhờ in danh sách nguồn trước khi nạp).
  **Truy nguồn (cập nhật 16/08):** tester + security ĐỀU tự loại trừ BẰNG CHỨNG (tester: log
  container — endpoint/user_id/script chỉ-đọc; security: import-list 3 probe, 0 lời gọi ingest).
  Tester truy ra đường nạp: **`POST /policy-docs` × 2 (08:23:14/08:23:27) dưới `USR-PA01`** —
  cửa upload HỢP LỆ của partner_admin, không phải lách. PO đối chiếu: `kho_rag.py` nạp bằng
  `ingest_document()` trực tiếp (không HTTP) nên không thể tạo 2 dòng POST ⟹ nghi phạm còn lại
  duy nhất: **PO thật thao tác màn hình upload Đối-tác-ví** — đang hỏi. Security được giao đo
  thiệt hại thật (log `/policy-search` trong cửa sổ 08:23→lúc-gỡ, loại 3 đợt quét USR-0201 của
  tester) → hồ sơ vào docs/security/. Dữ kiện giảm nhẹ: bảng trong business_rules.md mang cột
  `verified=false` ngay trong thân — trích là trích kèm.
- **ĐÍNH CHÍNH truy nguồn (tester, 16/08):** "USR-PA01 trông như chữ ký nhưng thật ra là CON DẤU
  CỦA CÁI CỬA" — `uploaded_by=USR-PA01` là danh tính đường nạp, không phải người (lượt nạp đòn-4
  của coder 08:42 cũng mang USR-PA01, 2 file cách 4s; 13s-vs-4s không phân biệt người/máy). PO đã
  lỡ hỏi PO-thật theo hướng dẫn-dắt trước khi đính chính tới — lần chạm sau hỏi MỞ + thêm nghi
  phạm thứ ba: script-của-đội gọi API. Phép kiểm còn phân biệt được (tester đang chạy): đếm lại
  dòng `POST /policy-docs` — kho_rag.py nạp trực-tiếp không qua HTTP, nên nếu vẫn đúng 2 dòng thì
  "08:23 = một client HTTP thật" vẫn đứng.
- **✅ SỐ SẠCH ĐẦU TIÊN: Recall@3 = 41,4% → trục Truy-hồi 8,29/20 → benchmark v0.2 = 86,2% đo
  được** (thước-đã-vá × kho-sạch 378c/2doc × 3-lượt-lặp-y-hệt; nhãn `55118b5`/`1e367a58c2e5`/
  `332c053b9fde`/StartedAt-08:44:29Z). **QUYẾT ĐỊNH: KHÔNG đọc 41,4−35,7 thành delta đòn-4**
  (ba biến cùng đổi: thước+kho+rác) và **KHÔNG dựng lại nền PDF** để attribution — câu hỏi về
  quá khứ, giá = 1 vòng nạp + 1 lần đổi-vật-dưới-chân-4-phiên; chuyện đòn 4 kể bằng số cấu trúc.
  Chuỗi trục Truy-hồi BẮT ĐẦU LẠI tại 41,4%.
- **Hồ sơ sự cố ĐÓNG (`10af46d`, docs/security/): 0 thiệt hại tới khách** — cửa sổ 19ph33s
  (15:23:14→15:42 giờ máy), toàn bộ traffic = /policy-search nhịp-máy (trùng mạch tester+commit
  coder) + 0 lượt /chat/agent; stack fin05ttl không ảnh hưởng. **LUẬT MỚI: mọi mốc giờ trong hồ
  sơ sự cố ghi kèm MÚI GIỜ** (08:23 hoá ra là UTC = 15:23 giờ máy — suýt làm điều tra đi tìm log
  đã bay). Truy nguồn còn mở: POST /policy-docs là dấu-vết-đường-đi PHÂN BIỆT ĐƯỢC (kiểm 2 chiều:
  lượt kho_rag 15:42 của coder KHÔNG sinh dòng POST/USR-PA01 nào trong HTTP log) ⟹ 15:23 = một
  client HTTP thật đã đăng nhập partner_admin; khung giờ NẰM GIỮA phiên đòn-4 của coder → đã hỏi
  coder câu mở (curl/script HTTP nào 15:00–15:45?) + PO thật (chưa trả lời). Bằng chứng sống nhờ
  MAY (container restart, không force-recreate) — câu trả lời bằng thiết kế là F-LOG-3.
  **CẢ 3 PHIÊN ĐÃ TỰ LOẠI BẰNG CHỨNG CỨ** (tester: endpoint/user-id/script-chỉ-đọc · security:
  import-list 3 probe · coder: nguồn-IP 172.19.0.6=frontend-container trong khi curl của coder là
  127.0.0.1-trong-backend + CHƯA TỪNG cầm token partner_admin hôm nay nên guard không cho qua +
  Playwright không có setInputFiles + zsh-history 0 dòng). Dấu vết hội tụ: một phiên TRÌNH DUYỆT
  đăng nhập partner_admin, mở trang 08:22:45Z rồi nạp 2 lần — nghi phạm còn lại: PO thật (đang
  hỏi). Nợ mới ghi nhận: `uploaded_at` lưu naive-UTC không hậu tố — bẫy múi giờ sẽ lặp; F-LOG-3
  dùng ts ISO-8601 có offset, đổi `uploaded_at` là mục nợ riêng.
  Quan sát thêm (security, không phải kết luận): mỗi POST kéo theo GET /policy-docs sau 20-40ms =
  nhịp UI-tự-tải-lại-sau-upload; 13s GIỮA hai lượt hợp người bấm 2 lần ⟹ kéo giả thuyết thao-tác-
  UI LÊN (không loại script điều khiển trình duyệt). Đặc tả trường F-LOG-3 security đã gửi coder:
  doc_id[]/chunk_id[] trả về (trường quan trọng nhất) · query_hash HMAC + query_len (KHÔNG log
  nguyên văn — S-01 scrub hỏng 40% nghĩa trên văn bản nghiệp vụ) · nguon cho /policy-docs (tên
  khớp việc xuất-xứ) · retention ngắn tách QĐ3 · không IP/UA.
- **F-LOG-3 GIAO coder (sau fix-kho-restart, trước T3):** log có cấu trúc /policy-search +
  /policy-docs — lần THỨ BA trong 2 ngày câu hỏi sự cố dừng ở "đo không được" vì thiếu 1 dòng log
  (uvicorn access log không có user_id/query/chunk). Security gửi danh sách trường; ràng buộc:
  JSON + PII-scrub-trước-khi-ghi + contextvars sẵn có.
- **Bộ đo 6-trục XONG (`8a7f853`): 41→60 ca · benchmark v0.3 = 85,7%** (trục Truy-hồi hiện hành
  **39,4% / 47 ca có ToS** → 7,87/20; ghi kèm `41,4% / 35 ca chỉ-FAQ` — số ca đổi = cắt chuỗi).
  **ToS 2/8 = trục yếu nhất → tín hiệu ưu tiên đòn RAG kế**, TRÌNH TỰ: chờ coder trả lời §15-ToS
  (15.1 + tiêu đề "Giới Hạn Trách Nhiệm" vắng trong 340/378 chunk khảo sát — lỗi nạp hay 38 chunk
  chưa lộ?) rồi mới đo lại ToS. §G bắt 2/4 ca âm-bản security đề xuất hoá ra DƯƠNG (kho CÓ đáp án:
  ToS 19.2 60-ngày · ToS 2.8) — mọi ca âm-bản nay mang `moi_gan`+`vi_sao_am` chống sửa-nhãn-khớp-
  kết-quả. Datum: typo/caps không phá truy hồi (mỏng, 1 ca/loại); đối chứng 2 lượt nạp cùng nguồn
  15/14 TRÙNG KHÍT ⟹ nạp-lại không đổi phép đo, băm-đổi = ghi sổ không phải nhiễu (chống lưng đề
  xuất `_bam_kho` text-only — coder nhét vào lượt chạm kho_rag kế). Nhắc-một-lần đã gửi coder:
  lượt nạp 08:55Z không hô trước — quy ước mới không được mềm tuần đầu. Nợ tester: mồi-neo §D +
  k-boundary (cần đường agent), sau khi kho đứng yên.
- **🎉 LIVE: https://app.adaptivealgo.uk — PO thật TỰ deploy Windows home-server + Cloudflare
  Tunnel (16/08).** PO-agent smoke-test từ ngoài: /login 200 qua CF edge HKG · title đúng ·
  POST /api/session đăng nhập demo THẬT 200 + đúng user (0,4s) ⟹ tunnel+caddy+BFF+backend+
  Postgres+seed sống. GET /api/session 405 — coder xác nhận chủ-đích hay thiếu. Việc coder (sau
  F-LOG-3): checklist kho-RAG-trên-Windows (kiem xanh trên máy đó · restart-sau-nạp-lại trong
  deploy_home.* · 1 câu policy-search thật) + soạn "3 lệnh kiểm sức khoẻ" cho PO thật. Quy ước
  cho cả đội: stack live = môi trường THẬT — probe chỉ-đọc, báo trước.
- **🔴 CỔNG TUÂN-THỦ ToS SẬP MỆNH ĐỀ (tester chạy 8 ca đường agent): 4/8 đường thoát KHÔNG hoạt
  động** — (c) đúng 2 · (a) từ-chối-an-toàn 2 (RAG-47 đòi OTP step-up = ĐÚNG) · **(b) diễn giải
  2: RAG-41** (hỏi trách-nhiệm-pháp-lý, trả lời bằng chunk cashback, chắc nịch) + **RAG-43**
  ("chưa tìm thấy… **Tuy nhiên, thông thường**: 1.…" — TỪ-CHỐI-RỒI-TRẢ-LỜI-TIẾP = bịa có vỏ bọc,
  bộ chấm dò chuỗi "chưa tìm thấy" sẽ chấm ĐẠT; vào chuẩn viết test: kiểm cả phần SAU câu từ
  chối) · **loại thứ TƯ — từ-chối-SAI-PHẠM-VI 2: RAG-38** ("gửi tra soát bằng cách nào" = chính
  nghề sản phẩm!) + **RAG-40** (chạm vùng ràng buộc 5), cả hai 0 tool call, guardrail chặn trước
  truy hồi, VÔ HÌNH với mọi trục đo. **F-31** (sai-phạm-vi, ưu tiên cao) + **F-32** (diễn-giải)
  GIAO coder xếp sau ②-thí-điểm. Benchmark ghi "2 finding mở", KHÔNG ghi giới-hạn-đã-biết.
- **THƯỚC INDEX-THÔ HỤT (đảo chiều §D):** agent TỰ VIẾT LẠI truy vấn trước khi tra (RAG-37:
  "bao lâu có kết quả"→"thời gian xử lý khiếu nại"→HẠNG 1; thước hỏi nguyên văn thì trượt) ⟹
  security lo index-thô nống, đo thật ra HỤT. Hệ quả coder: HyDE-âm ≠ viết-lại-vô-dụng (âm là
  viết-lại-thành-văn-điều-khoản; đang thắng là viết-lại-thành-truy-vấn-ngắn). Chấm-MỐC đường
  agent càng nặng vai.
- **METRIC ĐỔI @3→@4 (PO duyệt, cắt chuỗi):** sản phẩm luôn đưa agent 4 kết quả (top_k bị bỏ
  qua — coder xác nhận chủ-đích/bug) ⟹ Recall@4 = 48,9% (23/47) = số sổ sách → benchmark v0.4 =
  88,0% kèm 2 finding mở. Dải chẩn đoán @1 27,7% · @3 40,4%. 24/47 ngoài top-4 ⟹ nới k không
  phải đòn chính. Mẫu số ToS chốt 2/10 (tester đếm sót 2 ca, tự sửa).
- **✅ T3 LAND (`99de792`) — input/lượt 19.397→14.698 (−24%) trên câu đo của coder.** Chẩn đoán:
  `get_customer_history` complaints KHÔNG limit/không lọc days = 13.620 ký tự = 41% toàn prompt
  (107 phần tử). Thiết kế: BẢN TRẢ LLM cắt còn 10 complaints (4.707 ký tự) · BẢN GHI DB nguyên
  vẹn 107. **LUẬT MỚI (coder tự dựng): cổng nghiệm thu PHẢI CHẠM ĐƯỜNG THAY ĐỔI** — origin-rule
  0/5 + o-group 0/8 xanh nhưng không chạm đường T3 ("nhận chúng làm bằng chứng là tự lừa");
  bằng chứng thật = ca đúng-rủi-ro: agent thấy 10 bản ghi nói "105/107" (tra ngược được), KHÔNG
  nói "10". **<30k CHƯA tuyên bố đạt** — chờ bộ-lệnh-cố-định đo token+latency (GIAO tester, gộp
  việc backlog "bộ đo latency thay n=8"); coder đo lại lượt dài 47-84k khi thước về. T3 đóng
  ngoài thứ tự = ngoại lệ chấp nhận (code-dở-cây-chung rủi ro hơn), không thành nếp.
- **② điều kiện (c) GIẢI QUYẾT — kiến trúc TÁCH SẴN tìm/trích:** store.py::add_chunks embed
  texts nhưng Chroma documents=chunk_ids (placeholder); văn bản trả LLM lấy từ PolicyChunk.text
  Postgres ⟹ dòng chèn ② chỉ đi vào embedding, không có đường lọt ra khách. Coder thêm docstring
  bất biến tại chỗ chèn. ②-thí-điểm ĐANG CHẠY (hô 4 phiên trước khi nạp).
- **ADR-026 BẢN THẢO XONG (`a65e9fc`, docs/security/…-ban-de-PO-land.md) — TRÌNH PO THẬT KÝ.**
  8 quyết định = 4 điểm PO chốt + QĐ5 (eval đánh dấu ĐÃ-duyệt — mô hình đe doạ là đối-tác-bị-
  chiếm, cờ bỏ-qua-lọc bị bác vì là lớp lỗi F-30) + 🔴QĐ6 (xuất-xứ ≠ thay tier, quyết định riêng
  chống-gỡ-nhầm) + 🔴QĐ7 (nạp-lại GIỮ trạng thái duyệt theo (filename,băm-file) — không thì bảo
  trì thường quy làm agent mù; chính lượt 08:42 đã-sửa-sự-cố sẽ là ca vấp đầu tiên) + QĐ8 (2
  tầng: dây-bẫy contracts/rag-nguon.yaml LÀM NGAY khớp xfail 55118b5 · trạng-thái-duyệt DB khi
  onboarding thật; bác cả hai phương án đơn lẻ). Điểm rà PO-agent: chuyển tiếp production đang
  cầm kho PDF — manifest chỉ có 2 DOCX, dây bẫy phải land CÙNG nhịp release đòn-4 lên production.
- **Ý kiến tuân thủ ToS (security): XÁC NHẬN CÓ ĐIỀU KIỆN KHÔNG-NHÂN-NHƯỢNG** — "an toàn tuân
  thủ VÌ VÀ CHỈ VÌ đường thoát 'không tra được→người thật' đã được XÁC NHẬN hoạt động; chưa đo
  thì mệnh đề chưa đứng". Ca lo nhất: top-3 trả chunk-lân-cận-SAI điểm cao ⟹ agent tưởng tìm
  thấy ⟹ diễn giải thay vì từ chối (trục âm-bản-GẦN chưa có ca canh). ĐÃ GIAO tester: chạy các
  ca ToS trượt qua đường agent, phân loại (a)không-tra-được=đạt (b)diễn-giải-từ-chunk-lạc=TRƯỢT
  NẶNG báo ngay (c)đúng-nhờ-đường-khác=ghi chú; + chốt mẫu số ToS (2/8 vs 2/10 đang lệch).
- **Version-drift HIỆU CHỈNH XUỐNG (security tự đo lại):** origin/main ĐÃ CÓ đủ A1+A2·S-03·F-30·
  F-29·F-28/e·note/ADR-024·CI-appsec — production KHÔNG hở lỗ bảo mật; thiếu duy nhất F-LOG-3 +
  7 commit RAG/observability hôm nay ⟹ lý-do-redeploy là quan-sát-được, không phải vá-khẩn.
  (Bài học security tự ghi: main local là nhánh chết 1 commit — đọc origin/main, đo hai lần
  trước khi kêu.)
- **THƯỚC RÀ HAI PHÍA XONG — 39,4% LÀ SỐ SẠCH, mặt trận truy hồi MỞ LẠI (16/08):** phía trượt
  28/28 công bằng (0 nhãn hỏng; 15 ca nghi-oan ban đầu là bẫy truy-vấn-ngắn-embed-kém — kiểm
  đường độc lập 15/15 lành, suýt làm cả đội sửa 15 nhãn lành) · phía đạt 0/47 chuỗi lỏng. Bản đồ
  phủ vào chỗ cố định eval/do_phu_kho.py + phu_kho.json (`ed654b9`, băm `5b5dbc12719f`): ToS
  97,1% · FAQ 87,4% (tester tự bắt 2 lỗi thước của mình: "mục 15 thiếu" = chỉ tra 340/378; "FAQ
  81%" = mẫu số đếm cả 146 dòng mục-lục đã-cố-ý-vứt — "đếm cái ta chủ động vứt thành cái ta đánh
  mất"). **②-THÍ-ĐIỂM PHÁT LỆNH cho coder** (3 điều kiện mở-lại đều thoả): 5 chunk từ bộ RAG-37/
  47/39/41 (khách hỏi "bao lâu có kết quả" ↔ chunk "không quá 45 Ngày Làm Việc" — khoảng cách
  VĂN PHONG không phải chủ đề; giải thích luôn vì sao FAQ tốt hơn ToS); nghiệm thu: ≥3/5 chuyển
  đạt + TRỌN 47 ca không ca-đang-đạt nào rơi + dòng-chèn-không-được-trích-cho-khách (nếu không
  tách được phần-tìm/phần-trích thì DỪNG); xếp sau F-LOG-3 trước T3. Caveat đã ghi: HyDE âm
  (1/47) = sửa-phía-CÂU-HỎI đã có điểm âm; ② = sửa-phía-NỘI-DUNG offline là chiều chưa đo.
- **Kho PRODUCTION SẠCH (PO-agent đo chỉ-đọc qua HTTPS):** GET /policy-docs trên live = đúng 2
  PDF MoMo (uploaded 07:24, 362 chunk) — sự cố .md CHỈ ở stack local, không có sự cố production.
  NHƯNG lộ **version drift**: production = snapshot TRƯỚC đòn 4 (kho PDF cũ) + `deploy_home.*`
  pull `main` ⟹ máy Windows nhiều khả năng chạy code cũ hơn hôm nay. Đang hỏi PO thật: nhánh
  deploy · secret khác dev? · `LANGCHAIN_TRACING_V2`? · live = demo đội hay người thật? (3 câu
  sau là F-30/secret/pilot-cam-kết của security, nay tăng hạng vì có production thật). Kế tiếp:
  một nhịp release dev→main + redeploy CÓ TRẬT TỰ — coder không tự đẩy main trước khi chốt.
- **CHẨN ĐOÁN ToS XONG (coder) — 5 SỐ ÂM LIÊN TIẾP, quyết ①+③:** kho ổn (0/10 thiếu nội dung) ·
  embedding ổn (8/8 ca trượt lên hạng-1 khi hỏi bằng chính văn chunk) ⟹ lỗi = khoảng cách
  hỏi-đời-thường↔viết-pháp-lý. Top-3 của ca trượt = 79% FAQ = đúng tỉ lệ nền kho (truy hồi không
  thiên vị, chỉ không phân biệt nguồn). 5 cơ chế đo đều âm: BM25 0/10 · RRF 3/10 (FAQ chưa đo) ·
  trộn-nguồn 17/47↓ · HyDE 1/47↓↓ · RRF+HyDE 8/47↓↓. HyDE datum giữ: cứu ca chôn sâu (>100→8)
  nhưng phá ca đang đúng — sống lại nếu có bộ phân-loại-ca-khó. **QUYẾT: ① ToS 2/10 = giới-hạn-
  đã-biết** (câu pháp lý nên escalate người thật; ràng buộc 3 làm trượt-truy-hồi thành hành vi AN
  TOÀN "không tra được"; chờ security 1 dòng góc tuân thủ) **+ ③ không chọn đòn trên thước FAQ
  chưa rà; ② (chèn câu-hỏi-tương-ứng vào chunk ToS) ĐỖ BẾN** — mở lại khi: thước FAQ sạch + ToS
  vẫn ưu tiên theo số + đo trước 5 ca. `GET /api/session` 405 = CHỦ ĐÍCH giữ nguyên (BFF: 34 chỗ
  đọc getServerSession server-side, không mở thêm cửa phát thông tin phiên).
- **🔒 ÁN KHO ĐÓNG — PO thật xác nhận chính họ upload 2 file .md qua UI Đối-tác-ví ~15:23** (tai
  nạn quy trình, không xâm nhập, không ai có lỗi). Khớp trọn chuỗi bằng chứng (IP frontend ·
  nhịp UI POST→GET 20-40ms · 13s giữa 2 lượt). Câu hỏi đầu tiên của PO thật khi nghe tin — "đối
  tác ví có luồng riêng là đã quản lý được rồi đúng không?" — vào phần động-cơ ADR-026: người
  vận hành thiện chí TIN tách-vai = kiểm-soát-nội-dung, và sự cố chứng minh niềm tin đó sai.
- **§15-ToS ĐÓNG — nghi vấn bị chính người nêu tự bác bằng đo:** phủ ToS = 198/206 đoạn (96,1%);
  mục 15 đủ 6/6; **mục 19 (tra soát & khiếu nại) đủ 11/11 TRONG KHI 6/8 ca ToS trượt hỏi đúng
  mục 19** ⟹ ToS 2/8 chắc chắn là lỗi TRUY-HỒI-thứ-đã-có, tín hiệu sạch nhất ngày. 8 đoạn vắng =
  mảnh vụn gạch-đầu-dòng, QUYẾT ĐỊNH không vá (riêng [210] hotline ghi biên-biết-trước — còn ở
  19.3). Lần thứ TƯ trong ngày họ lỗi "không-thấy-bằng-cách-A ⟹ không-tồn-tại" nhưng lần ĐẦU
  người mắc TỰ bắt trước khi ai phải đo lại. **Đầu bài coder đặt lại (sau F-LOG-3, trước T3):
  CHẨN ĐOÁN 6 ca ToS trượt** (top-3 trả gì · khoảng cách embedding · giả thuyết lệch văn phong
  khách-hỏi↔chunk-pháp-lý) rồi mới chọn đòn — không lặp T1. Tester chạy thêm bản đồ phủ FAQ
  (0 LLM) → đóng câu 29-chunk-không-lộ; hai bản đồ phủ vào eval/ (không để scratchpad).
- **ADR-026 (xuất-xứ kho RAG) ĐANG SOẠN — security, sau khi ĐO (`d578d0d`):** chi phí rẻ bất ngờ
  (cờ ở PolicyDocument, backfill 2 DÒNG; serve = 1 mệnh đề SQL vào bước join sẵn có; không đụng
  Chroma; recall-cost 0 khi vận hành bình thường). **Phát hiện quyết định (security tự bác đề
  xuất gốc):** ghi ĐƯỜNG NẠP không chặn được sự cố — file đi qua đúng cửa hợp lệ; phải là TRẠNG
  THÁI DUYỆT tách khỏi hành vi nạp. Khuyến nghị PO-agent đã chuyển security soạn (chốt = PO thật
  ký, quy trình §3): ① mọi upload vào `cho_duyet`, **supervisor** duyệt (maker≠checker mở rộng
  nhất quán sang kho tri thức; partner_admin tự duyệt = tái tạo sự cố 1 click) ② backfill 2 doc
  MoMo = `da_duyet` có-chủ-đích ③ thấy chưa-duyệt: partner_admin CÓ · agent KHÔNG · CSKH CÓ kèm
  badge «CHƯA DUYỆT» (giữ Y5 người-là-máy-dò, không để dựa nhầm làm căn cứ) ④ mục riêng: xuất-xứ
  ≠ thay lọc tier (hai mối đe doạ, hai cơ chế). Kèm `contracts/rag-nguon.yaml` khớp chuỗi xfail
  `55118b5`. **Va chạm tên bắt kịp lúc rẻ:** `nguon` (F-LOG-3, đường ĐỌC) đổi thành `duong_tra`;
  `nguon_nap`+`trang_thai_duyet` dành cho đường GHI — coder đang đổi. Điểm mù công cụ (họ C4):
  grep "ingest_document(" bỏ sót call-site truyền-hàm-như-tham-chiếu (`_handle_tool_error(
  ingest_document, ...)`) — chỉ lộ khi truy ngược từ endpoint.
- **LUẬT MỚI (tester): nhãn định danh LƯỢT ≠ nhãn định danh VẬT** — `new_id("CHK")` ngẫu nhiên ⟹
  nạp cùng nguồn+parser vẫn ra băm khác (6e3c11…→8820b6…→a3c5c7… là MỘT kho). "Băm khác ⟹ kho
  khác" SAI; chỉ chiều "giống ⟹ giống" đúng. So hai lượt bằng chunk/doc/parser. Đề xuất route
  coder (chưa quyết): `_bam_kho` chỉ băm sorted(text), bỏ chunk_id ⟹ băm định danh được VẬT.
- **Biến thể #4 luật assertion-trùng-mặc-định** (tester bắt trong chính test của mình `55118b5`):
  hai vế CÙNG KIỂU (set[str]) nhưng khác KHÔNG-GIAN-TÊN (doc_id-băm so với filename) — không bao
  giờ khớp, test xanh mà chặn con số 0. Bắt bằng CA ĐỐI CHỨNG: đổi danh sách sang tài liệu ĐANG
  có thật trong kho → test phải đỏ (đã đỏ đúng: 'MoMo_ToS.docx'). Fix: lấy tên thật từ
  `policy_documents.filename` ∩ doc_id-có-vector, fail-nếu-index-rỗng. `55118b5` = chuỗi
  xfail(strict)-đẻ-nghĩa-vụ: đặc tả `contracts/rag-nguon.yaml` xuất hiện → XPASS → strict đỏ →
  buộc người kế bật cổng thật; file contract đó sẽ ra đời cùng gói ADR xuất-xứ (quy trình §3).
- **Bug kho tra-rỗng-không-tất-định: coder ĐÃ root-cause** (docstring `_server_dang_cam_kho_cu`):
  `chromadb.PersistentClient` không dùng chung persist-dir giữa 2 tiến trình — `nap-lai` chạy
  docker-exec riêng, server giữ segment CŨ đã bị xoá → tra rỗng, HTTP 200, không log lỗi; mọi
  công cụ kiểm (tiến trình riêng) mở client MỚI thấy kho mới → cả ba đèn xanh trong khi sản phẩm
  trả rỗng. **Khắc phục: sau `nap-lai` PHẢI restart backend**; `kiem` nay có cổng-cuối phát hiện
  (dấu `nap_lai_luc` do riêng nap-lai đặt — mtime chroma.sqlite3 ĐÃ THỬ VÀ SAI vì server cũng ghi
  WAL). Mở rộng: bước restart cần vào cả `deploy_home.*` (kho_rag nap-lai trong script deploy).
  Tester thêm cổng canary vào benchmark (3 truy vấn tối giản, rỗng cả 3 = DỪNG không đo) sau khi
  SUÝT báo 0,0% làm số sản phẩm.
- **Hướng thiết kế sự cố (security chủ trì, probe kế tiếp):** chặn đuôi file = đóng cửa TAI NẠN,
  không đóng cửa QUY TRÌNH (.docx nháp vẫn vào cửa hợp lệ). Whitelist tên file ở serve = SAI
  (chặn onboarding đối tác thật). Hướng nghiêng: **XUẤT XỨ trên chunk** (nguon_da_duyet) — đúng
  hình dạng origin-rule cho RAG, xử cả ca-tai-nạn lẫn ca-eval-cố-ý. Chưa đo chưa đề xuất; không
  ai code trước khi có số + ADR. Tester (trong lúc chờ kho): ca hồi quy chặn-thành-phần-tài-liệu,
  danh mục lấy từ ĐẶC TẢ không hardcode 2 tên PDF.
- **QUY ƯỚC MỚI (PO phát 16/08):** kho RAG đang-phục-vụ là VẬT DÙNG CHUNG của 4 phiên — không ai
  nạp thẳng vào nó để test. Cần kho thử → collection/CHROMA-path riêng trong scratchpad (như
  run_adversarial_set dùng DB tạm). Đổi kho phục vụ CHỈ qua `kho_rag.py nap-lai` + hô cả 4 phiên.
- **MỐC 35,7% VÔ HIỆU KÉP** — hỏng cả THƯỚC (tester tìm ra `bo_dau()` không gộp khoảng trắng ⟹
  cụm ≥2 từ vắt qua xuống-dòng = TRƯỢT GIẢ, ngược hướng với pass-giả cũ) lẫn VẬT (57 chunk rác
  nội bộ nằm trong kho lúc chấm, có thể chiếm top-3). Chuỗi so sánh trục Truy-hồi CẮT tại đây
  (Luật 6). **KHÔNG ghi delta đòn 4 nào** cho tới khi tester trả cặp sạch: thước-đã-vá × kho-sạch
  (nền phải là `f9b06f9983bc`, không phải kho lúc 08:23).
- **Đòn 4a+4b LAND (`1481074`), tách 3 mốc băm:** nền PDF-đã-gỡ-md 362 `f9b06f9983bc` · 4a DOCX-
  parser-cũ 333 `71bb841435ea` · 4b DOCX-giữ-cấu-trúc 378 `6e3c11fb04f4` (đang phục vụ). Số CẤU
  TRÚC (đếm được, không phụ thuộc thước truy hồi): chữ-vỡ-từ-điển 131→0 · hàng bảng bank vào kho
  0→25 · chunk mồ côi nhãn 61%→36%. Ca đối chứng 4b: docx thường ra chuỗi GIỐNG BYTE bản cũ;
  upload partner_admin không đổi hành vi. 36% mồ côi còn lại = đuôi khối dài cắt theo kích thước
  — coder CHƯA làm chưa hứa, quyết sau khi có số cặp sạch.
- **Hai đính chính coder tự khai:** ① "đòn 1 quét sạch lớp một" SAI — lớp `[aeiouyăâêôơư]` thiếu
  ký tự dựng sẵn có dấu (`ị`,`ồ`,`ế`) ⟹ `đ ịnh`,`g ồm` lọt, tester đếm đúng ~53 còn lại; đáng ghi:
  coder CẦM bằng chứng bác mình (list 131 chứa `b ất`,`đ ịnh`) mà phát biểu ngược — lỗi đọc-lướt-
  số-của-chính-mình, cùng họ với bài coder-tự-nghiệm-thu. ② Hai thước cùng tên: băm trong
  `kho_chunks.tsv` ≠ `kho_rag.py::_bam_kho` — chỉ tin băm in từ `kho_rag.py nhan`.
- Coder chuyển sang **T3** (truncation tool-result; cổng-96 + origin-rule phải xanh nguyên, đo
  input-tokens/lượt trước-sau cùng bộ lệnh, tham chiếu <30k/lượt).

## ✅ UI-02 ĐÓNG + ĐÒN 4 THÀNH 4a/4b — bảng-23-hàng là lời giải bài chôn (16/08 đêm)
- **UI-02 nghiệm thu 5/5** (đối chứng 1/5 trên image-chưa-vá, A2 tái hiện nguyên văn lỗi PO demo).
  Mẫu thiết kế nghiệm thu UI ghi lại: **đếm REQUEST không đếm pixel** — vá-giả (reset ref quên
  deps) hiện nút y hệt mà không request nào đi; B2 bắt bằng 1→2 request. Nợ: e2e vào repo
  (coder thêm dep playwright · tester dựng sau chuỗi benchmark).
- **Đòn 4 hồ sơ tiền-đề-sai-kết-luận-đúng:** "215 chữ vỡ trong kho" SAI (tester đếm PDF thô; kho
  đã qua đòn 1) — nhưng thước độc lập từ-điển-DOCX lộ **lớp vỡ THỨ HAI: 131 lần/52 dạng cả đòn-1
  lẫn luật-đếm-tester đều mù** (`ho ặc`,`kho ản` — vế trái có nguyên âm). Soi đối xứng PDF↔DOCX:
  DOCX sạch 0 vỡ + đủ hơn (17-vs-9 câu thiếu). **4a GO** (đổi nguồn nạp).
- **4b DUYỆT mở phạm vi `parsers.py` (gồm upload partner_admin), 4 điều kiện** (một-parser-dùng-
  chung đúng thiết kế · ca đối chứng upload-docx-thường · bảng→mỗi-hàng-một-chunk-mang-tên-thực-
  thể · đo trên thước 35,7% tách 4a/4b nếu rẻ). **Phát hiện chốt: "20 đoạn gần-trùng" thật ra là
  MỘT BẢNG 23 hàng (bank·viết-tắt·hạn-mức) bị PDF nghiền thành cháo** — `_extract_docx` hiện vứt
  heading + KHÔNG đọc tables. 4b = chunk theo H3 (mỗi FAQ-bank một heading có sẵn tên) ⟹ chunk-
  theo-thực-thể MIỄN PHÍ. **ĐÍNH CHÍNH nhận định cũ**: "đòn 4 không chữa được lớp chôn" — sai với
  4b; 4b chữa được vì tách bảng thành 23 dòng riêng.
- Coder GIỮ TAY nạp-lại chờ tester nhả khe (362 chunk_id sẽ đổi giữa lúc họ rà nhãn) — quy ước
  báo-trước-đổi-vật chạy đều. Danh sách chunk_id đã đổ cho tester (băm 8a3185199493).

## 🔍 ĐIỀU TRA CHUNK-CHÌM XONG: KHÔNG PHẢI RÁC — CHÔN-DO-GẦN-TRÙNG (16/08 tối)
- Tester tự sửa số 47%→**31,5%** (thước lại là thủ phạm: 160 câu quét đều là câu FAQ mà kho có 2
  tài liệu; quét lại 340 truy vấn → 82/260 chunk FAQ không bao giờ nổi với chính câu sinh ra
  chúng; 60 chunk ToS "chìm" chỉ là chưa-hỏi-tới). **Mẫu 20/20 = nội dung THẬT bị chôn, 0 rác.**
- **Cơ chế: GẦN-TRÙNG** — ~20 đoạn hướng-dẫn-liên-kết-bank gần y hệt (khác mỗi tên bank): một
  truy vấn lấy 3, 17 cái vĩnh viễn chìm. Nhóm chìm CHỨA đáp án các ca đang trượt (RAG-08/22/23/
  29) — nguyên nhân thứ hai của RAG-22. **Đòn 4 DOCX không chữa lớp này.**
- Hướng đề xuất (tester, CHƯA đo): **chunk-theo-THỰC-THỂ** (mỗi bank một chunk có nhãn tên) —
  coder trả lời khả thi trước, tester dựng ca đo sau. Thứ tự: đòn 4 trước (rẻ, chắc) → chống-chôn
  theo số. Còn mù: 29 chunk (8%) không lộ bằng cách nào — coder đổ danh sách chunk_id cho tester.

## 🎯 ~~THƯỚC ĐÃ RÀ — 35,7%~~ ⚠️ VÔ HIỆU KÉP 16/08 (bo_dau + 57 chunk rác — xem mục SỰ CỐ ở trên)
- Luật chuỗi-đặc-trưng (3 cửa: có-trong-đáp-án-đúng-biên · sống-qua-trích-PDF · ≤2 câu FAQ) +
  xác minh nhãn bằng ĐƯỜNG ĐỘC LẬP (quét kho bằng 160 câu nguồn → 31/35 chuỗi có thật trong kho
  ⟹ trượt THẬT). Khoảng bất định siết từ 25,7 điểm còn 4,6 (cận trên 40,3% nếu 4 ca chưa-kết-luận
  đều nhãn hỏng). **12/12 pass-giả lộ diện** (9 nghi + 3 chưa nghi: RAG-06/28/32).
- **Hai mốc cũ 54,3% & 60,0% ghi SAI THƯỚC** (không phải cận trên — số đo bằng thước đã chứng
  minh cho pass giả không có tư cách cận trên). Chuỗi so sánh trục Truy-hồi BẮT ĐẦU tại 35,7%.
- **① 215 chữ vỡ chắc chắn trong kho** (vế trái không nguyên âm) từ trích PDF — trong khi DOCX
  SẠCH cùng nội dung nằm ngay cạnh trong data/raw/ ⟹ **RAG ĐÒN 4: ingest DOCX thay PDF** (coder,
  sau UI-02, trước T3 — chất lượng 7,14/20 ưu tiên hơn tối ưu giá). Đòn 1 giữ cho nguồn chỉ-có-PDF.
- **② 171/362 chunk (47%) không bao giờ lọt top-3** với chính 160 câu kho sinh ra để trả lời —
  tester lấy mẫu 20 chunk phân loại (rác vs nội-dung-bị-chôn) trước khi viết ca 6-trục; kết quả
  quyết đòn-chunk-theo-cấu-trúc có quay lại không.

## 💰 T1 KHÉP BẰNG KẾT QUẢ ÂM — cache ĐÃ hit ~85% từ trước, bản vá revert (16/08 tối)
- Coder đo hai vế chỉ-khác-một-file: bản cũ 85,0% cache-hit, bản "vá" 86,3% — chênh = nhiễu;
  `cache_read` lượt 1 giống nhau TỚI TỪNG TOKEN (29.568). **Cache chưa bao giờ hit 0% — phần tái
  dùng chính nằm GIỮA các bước ReAct trong CÙNG lượt** (mốc thời gian render một lần/lượt = hằng
  số trong lượt; vị trí của nó chưa bao giờ quan trọng). Giả thuyết T1 sai → **REVERT dù vô hại**.
- **LUẬT MỚI (ratify):** bản vá không-có-số-lợi-ích = revert, kể cả vô hại — land nó là gieo tiền
  lệ "chỗ này tối ưu rồi" chặn người sau tìm đòn thật. GIỮ LẠI phần đo (`cached_input_tokens`
  vào envelope, `e2cf59b`) — công cụ đã bác chính người tạo nó.
- **Bức tranh chi phí ĐÍNH CHÍNH:** 63M là token danh nghĩa; ~85% phần lặp hưởng giá cache rẻ ⟹
  hoá đơn thật THẤP hơn ước tính đầu. Nhưng mục tiêu <30k/lượt là về LƯỢNG (input 46,8-84,7k/lượt
  đo được) — cache giảm GIÁ không giảm LƯỢNG ⟹ **T3 là đòn duy nhất chạm mục tiêu**.
- **Thứ tự chốt:** UI-02 đóng trước (compiled, hoãn 5 lần, chỉ còn verify) → T3 (cổng kèm:
  origin-rule xanh — cắt phần đưa-LLM không được làm số mất nguồn) → T4 → T2 độc lập.
- Đòn 3 đính chính: **mốc 20/35 (+1)**, RAG-04 = pass-giả-bị-lộ không phải hồi quy — nhất quán
  chuỗi 9/21; số nằm vùng thước-đang-rà, chưa vào benchmark.

## ⚖️ TRỤC TRUY-HỒI: TẠM TREO SỐ — thước đang được rà HAI PHÍA (16/08 tối)
- Tester (theo dữ kiện tech-lead nêu) soi 21 ca ĐẠT sau đòn-3: **9/21 đạt CHỈ nhờ từ khoá chung
  chung** (RAG-17 có chuỗi đặc trưng `20.000.000` KHÔNG khớp mà vẫn đạt nhờ `hạn mức` — đáp án
  thật không trong top-3, thước vẫn ĐẠT). ⟹ **60% (21/35) là GIỚI HẠN TRÊN, cận dưới 34,3%**;
  và mốc 54,3% hôm trước CÙNG bộ từ-khoá ⟹ cùng caveat. Benchmark ghi `[đang rà thước]`, không
  số nào của thước-chưa-rà đứng như số thật.
- **LUẬT MỚI (ratify vào CHUAN-VIET-TEST):** xác minh nhãn phải soi CẢ HAI PHÍA — ca trượt (oan?)
  VÀ ca đạt (giả?). *"Chỉ soi ca trượt thì thước lỏng tay nhất luôn thắng — chiều im lặng nguy
  hơn vì không ai đi tìm"* — mặt đối xứng Luật 2, do chính tác giả Luật 2 phát hiện mình mắc.
- Luật từ-khoá mới: **≥1 chuỗi ĐẶC TRƯNG bắt buộc** (số/viết-hoa/cụm-dài), từ chung chỉ phụ. Áp
  cả 41 ca + ca mới. Thứ tự: rà 9 ca → đo lại (MỐC THẬT đầu tiên của thước-đã-rà) → ca 6-trục.
- Cặp tester↔coder hai lượt liền bác-nhau-bằng-số và nhận-bằng-số (RAG-04 không-phải-hồi-quy ·
  ca-đạt-cũng-phải-soi) — ví dụ vận hành tốt nhất của kiến trúc đối kháng tới giờ.

## 📊 THƯỚC 35-CA CHẠY LẦN ĐẦU — mốc Truy-hồi MỚI 54,3% + phát hiện TOC (16/08)
- **19/35 = 54,3% CẢ HAI chế độ gõ** (nhãn: 7fdca4e · he_thong 5d63edfc7cc7 · backend 95e17b99 ·
  kho 418·2doc·v2 · cổng-kiem-trong-container). Trục benchmark: **10,86/20 — MỐC MỚI trên thước
  mới, KHÔNG so cặp với 3,75/20 probe-8** (hai bộ khác nhau; chuỗi so sánh bắt đầu từ đây).
- **Xác minh 16 ca trượt: 1 nhãn sai (RAG-08 — từ khoá là TIÊU ĐỀ MỤC, sửa; thước sai vật đúng)
  · 15 truy hồi kém THẬT (không sửa nhãn)** — luật chỉ-sửa-nhãn-chứng-minh-được-sai giữ nghiêm.
- **🔴 PHÁT HIỆN → RAG ĐÒN 3 CHỐT: MỤC LỤC BỊ INDEX** — TOC chứa nguyên văn 160 câu hỏi, embedding
  khớp câu-hỏi-trong-mục-lục thay vì đáp-án-trong-thân; càng giống câu thật càng dễ trúng TOC
  (RAG-21/22 top-3 toàn dòng mục lục). Kho tự cạnh tranh với mình. Đòn 3 = LOẠI DÒNG TOC khỏi
  index (luật 2-điều-kiện: ≥N chấm liền VÀ kết thúc số trang — chống loại nhầm kiểu F-25), giao
  coder; **thước trước/sau = chính bộ 35 ca, mốc 19/35**. Đòn chunk-theo-cấu-trúc HOÃN chờ số.
- **Spec sửa (tester đề, duyệt):** sau đòn 2 hai chế độ gõ HỘI TỤ (19/35 cùng danh sách trượt) —
  "trung bình 2 chế độ" = cộng-số-với-chính-nó, hết thông tin. Đổi: 2 chế độ thành **CỔNG chống
  hồi quy** (phải bằng nhau), trục biến-thiên-đầu-vào chấm bằng **sai-chính-tả·viết-hoa·dấu-câu**.

## 🔴 BĂM KHO RAG KHÔNG TẤT ĐỊNH (tester bắt bằng Luật 4) — nhãn tạm bỏ trường băm
- Đọc `kho_rag.py kiem` 3 lần liên tiếp trên kho KHÔNG đổi → 3 giá trị băm khác nhau ⟹ mọi suy
  luận "băm khác = kho đổi" trong ngày VÔ HIỆU hai chiều (re-index vẫn THẬT — bằng chứng là số
  probe 0/8→5/8, không phải băm). Bắt được vì kiểm-nhạc-cụ-trước-khi-kết-luận-vật-đổi — sau một
  ngày kết-luận-vật-đổi đúng 3/4 lần, phản xạ tin lần 4 rất mạnh; không kiểm là cả đội đi truy
  "lần đổi kho thứ tư" không tồn tại.
- **Quy ước nhãn tạm (ratify):** bỏ trường băm-kho, dùng `418 chunk · 2 doc · chuẩn-hoá v2`.
  Băm quay lại khi tất định (nghiệm thu: 3 lần đọc cùng giá trị, trong container).
- **3 fix giao coder (xen trước UI-02):** ① băm tập-đã-sắp-xếp `(chunk_id,text)` hoặc bỏ băm
  nội dung; ② xoá rác `data/rag_index/` trên host (store rỗng do chính công cụ đẻ, bẫy người
  chạy host); ③ `kho_da_cu()` FAIL-CLOSED — hiện trả False khi KHÔNG dấu, mà không-dấu chính là
  kho-cũ cần bắt: **cổng cấp chứng nhận an toàn cho đúng ca nguy hiểm nhất** ("cổng sai hướng
  tệ hơn không có cổng" — bản tầng-dữ-liệu của F-CI-2).
- Tester song song: `benchmark.py` gọi cổng qua `docker exec` (kho thật sống trong volume, công
  cụ chỉ đúng TRONG container) → xác minh 41 nhãn không chờ fix băm (fix chỉ ảnh hưởng nhãn).

## ▶️ PHIÊN NỐI LẠI 16/08 — ba mốc mới
- **✅ CẶP AUTH ĐÓNG — BUG DEMO CHÍNH THỨC ĐƯỢC CHỨNG MINH ĐÃ VÁ** (tester, dấu khớp hai đầu,
  StartedAt vào nhãn chuẩn): sau 16 phút ngồi yên + token chết thật (−63s đo từ cookie), thao
  tác đầu **200** (trước-vá: 401 + "Có lỗi"), tầng-0 `rotated=1·revoked=0`. Caveat tự khai:
  backend khác giữa hai nửa (2 đòn RAG) — không phải cặp một-biến tuyệt đối, trích số phải kèm
  câu này. Giả thuyết log-bay-do-force-recreate của coder xác nhận đúng. Workaround demo
  (đăng-nhập-lại-trước-handoff) HẾT CẦN.
- **🔴 `kho_rag.py kiem` bắn sai trong container** (đường Chroma không tồn tại cả container lẫn
  host; báo "kho trống · băm-MD5-chuỗi-rỗng" trong khi policy-search trả 4 kết quả thật) — đúng
  món coder tự khai chưa-verify; tester GIỮ CỔNG không đo, bắt nhờ hai-đường-đo-mâu-thuẫn.
  Coder sửa XEN TRƯỚC UI-02 (đang chặn đường găng tester).
- **✅ Security nộp soi-trục golden-set** (`37c5511`, 6 trục): nặng nhất §A âm-bản-GẦN (bộ âm bản
  hiện toàn loại-xa-dễ-pass — về cấu trúc không phát hiện được chế-độ-hỏng nó tồn tại để phát
  hiện: chunk-lân-cận-sai điểm cao → bịa chính sách) + §B ToS trống kể cả **Điều 19 tra-soát-
  khiếu-nại — điều khoản điều chỉnh chính công việc của agent, zero ca**.
  **PO-agent chốt câu §D:** trục Truy-hồi benchmark đo **ĐƯỜNG AGENT THẬT** (sau sanitize) —
  benchmark đo sản-phẩm-khách-nhận; index-thô giữ làm chẩn đoán phụ, hai số hai tên. Ratify luật
  bộ: ca âm-bản-gần phải kèm bằng-chứng-đã-tìm-mà-không-thấy (tester + security độc lập cùng đề).

## ⏸️ ĐIỂM DỪNG PHIÊN 16/08 (hết limit) — phiên sau đọc mục này TRƯỚC
- **Đang chờ chuyển tiếp:** 5 bullet soi-trục golden-set của coder (ca-ranh-giới-k · độ-dài-query
  · đối-chứng-kho-lệch-vế dùng `kho_rag.py kiem` · ca-vắt-ranh-chunk cho đòn 3 · 2-3 ca
  đáp-án-không-tồn-tại) **CHƯA tới tay tester** — nằm trong transcript PO-agent; phiên sau chuyển.
  Security đang soi song song, chưa nộp.
- **Coder:** re-index tự động `0a4ff58` CHƯA VERIFY TRONG CONTAINER (tự khai) · UI-02 vừa bắt đầu
  · kế: 2 việc nhỏ lô auth → ADR-025 phần B → exporter.
- **Tester:** thứ tự 3→1→2 (script benchmark → xác minh nhãn 41 ca → gói 30 nhãn PO) · lượt đo
  sạch cặp auth đang/vừa chạy — kết quả chưa báo.
- **PO thật:** không việc nào chờ họ. PR 7/10 — 3 đợt release dev→main nữa là đủ.
- Doc home-server đã có dòng re-index (f3eba77). Mọi trạng thái khác: các mục phía dưới của
  chính file này — không có tri thức nào chỉ nằm trong đầu phiên nào.

## 🔀 PO THẬT ĐỔI QUY TRÌNH GIT (16/08 tối): MỘT NHÁNH, PR CHỈ THEO ĐỢT
- **Bỏ tách-nhánh-mỗi-việc** — cả 4 phiên code THẲNG trên `dev/learning-loop` (PO chứng kiến chi
  phí: 2 merge nhầm + thứ-tự + retarget trong một chiều). #4 + #7 đã merge sạch, **7/10 PR**.
- **PR còn MỘT loại: `dev` → `main` theo ĐỢT** (release gate) — PO-agent soạn, PO thật merge theo
  link đích danh. Vừa đủ đường tới 10 PR (3 đợt release nữa), vừa làm mỗi lần deploy home-server
  = một bản nghiệm thu trọn. **PO chỉ merge PR có link PO-agent gửi; bỏ qua banner GitHub.**
- Luật git cây-chung (một-lệnh-pathspec · HEAD+nhánh · file-mới-dính-liền · staged-lạ-dừng-hỏi ·
  báo-trước-land-src) NÂNG mức quan trọng — 4 phiên giờ chung một nhánh. Điều kiện chất lượng
  (đo-trước-land, probe-vai-khác cho lớp phòng vệ) KHÔNG đổi. Coder đưa cây chung về dev (có báo).

## 🏆 RAG ĐÒN 2 — SỐ VỀ: HAI CHẾ ĐỘ GÕ BẰNG NHAU (16/08)
- **Không dấu 0/8 → 5/8 · có dấu giữ 5/8 — Recall@3 trung bình 18,75% → 62,5%.** Ba mốc kho:
  `419·b630414088f8` (gốc) → `418·5aab3e7c43a2` (đòn 1) → `418·265aa93031bd` (đòn 2, hiện tại).
  Một-biến-mỗi-lần giữ nghiêm (đòn 1 đo xong hẳn mới áp đòn 2); cùng một thước (tái lập
  0/8·3/8 trên kho gốc). Chế-độ-người-dùng-thật (không dấu) từ 0% lên ngang có dấu — đòn ăn
  đúng như dự đoán.
- **PR: #4 (đòn 1) + #7 (đòn 2, đã retarget → dev). THỨ TỰ MERGE BẮT BUỘC #4 TRƯỚC #7** — đòn-2
  đâm trên đòn-1; merge ngược thì dev nhận cả hai một lượt, #4 rỗng, lịch sử mất khả năng tách
  hai đòn (thứ làm cặp số một-biến đọc được về sau).
- Sự cố merge-nhầm của PO thật (#5 dev→main vô hại · #6 đòn-2→main): KHÔNG cần revert — cả hai
  đòn ĐÃ ĐO trước khi mở PR, main không mang code chưa nghiệm thu. Quy tắc mới cho PO: CHỈ merge
  PR có link PO-agent gửi kèm số; bỏ qua banner gợi ý của GitHub (default-branch=main nên banner
  luôn trỏ main).
- **⚠️ Hệ quả cho gói home-server:** main giờ chứa cả hai đòn RAG ⟹ máy nhà dựng lần đầu PHẢI
  RE-INDEX kho sau deploy — không thì text cũ (còn dấu, còn từ vỡ) nằm cạnh query đã bỏ dấu,
  lệch một vế và KHÔNG CÓ TRIỆU CHỨNG. Coder soạn dòng lệnh chính xác → PO-agent đặt vào Phần C
  doc home-server + trang HTML.

## 📈 RAG ĐÒN 1 — SỐ VỀ, LAND DUYỆT (16/08)
- **Có dấu 3/8 → 5/8 (+2) · không dấu 0/8 KHÔNG ĐỔI (đúng dự đoán — việc của đòn 2) · 0 hồi quy.**
  Vật: kho TRƯỚC `419·b630414088f8` → SAU `418·5aab3e7c43a2` (backup kho cũ giữ nguyên) · thước
  probe-8 nguyên văn, coder KIỂM DỤNG CỤ bằng tái lập 0/8·3/8 trên kho cũ trước khi đo kho mới.
  Nhân quả sạch nhất đợt: ca 5 mới-đạt có top-1 cũ là chính chunk vỡ `"giao d ich… t oi da"`.
  Nhãn: **số-probe, không vào chuỗi benchmark** — trục RAG chấm lại khi golden-set land.
  PR đòn 1 sắp mở (`fix/rag-don1-extraction-pdf` @ 585ca06) — PO thật merge theo quy ước.
  Đòn 2 (chuẩn hoá dấu) GO ngay sau. Tester gán nhãn golden-set trên KHO MỚI; khuyến nghị nhãn
  theo định-danh-bền (mã câu FAQ/số Điều) thay vì chunk-id — sống qua re-index.
- Coder nhận nửa sự cố cây-chung không giảm nhẹ + tự gọi tên meta-pattern: *"biết một cái bẫy
  không miễn nhiễm với nó"* (lần 2 trong phiên: TTL-số-nói-về-hệ, rồi switch-cây-chung sau hai
  lần chính mình cảnh báo). Ghi thành luật đọc-người: **người cảnh báo giỏi nhất về một bẫy
  thường là người sắp dính nó — vì họ làm việc gần bẫy nhất.** Worktree áp ngay từ lô này.

## ⚖️ SỰ CỐ GIT TRÊN CÂY DÙNG CHUNG (16/08) + HAI LUẬT MỚI + QUY ƯỚC PR
- **Sự cố (lỗi ĐÔI, đã khắc phục, KHÔNG mất gì):** tester `git add` 9 file (đúng pathspec) →
  PO-agent `git commit` KHÔNG pathspec cuốn cả 9 file staged vào commit `7548bcb` → tester
  `reset HEAD~1` không đọc lại HEAD, đè local (remote an toàn, đã khôi phục khớp remote).
  **Hồ sơ:** commit `7548bcb` ("docs(state): PO chốt benchmark…") ngoài nội dung message còn mang
  **2.584 dòng thuộc `tests/`+`eval/` của tester** (cuốn vào do sự cố index, không chủ đích).
  Nội dung (5 bullet của tester, ghi lại để người đọc lịch sử khỏi mò diff):
  ① **`eval/EVAL-EVIDENCE.md`** — DELIVERABLE nộp BTC: 7 ca manual output NGUYÊN VĂN từ stack
  thật (nhãn `c447abb`), gồm 2 ca ÂM BẢN; cặp CA1↔CA6 = cùng câu hỏi, khác trạng thái xác thực,
  hai kết quả ngược (bằng chứng cổng OTP thật); có mục "những gì bộ này KHÔNG chứng minh".
  ② **`tests/test_ai_log/`** — cổng nhánh leftover `submit_log.py` (sắp chạy 19 lượt backlog
  P-121); F-LOG/F-LOG-2 vá cùng phiên nên 2 ca xfail-strict tự XPASS → lật thành regression gate.
  ③ **`tests/test_security/test_corpus_en_du_truc.py`** — cổng ký mẫu tier-1 EN: 50 ca/8 trục/
  BA mức kỳ vọng (mức giữa "tier-2 chấp nhận được" là thứ bộ hai-mức báo đỏ nhầm cho hành vi
  đúng) + mức `theo_doi` in-số-không-chấm có rào 4 vế.
  ④ **`test_note_toan_ven_can_cu_tu_choi.py`** — trục "căn cứ từ chối còn đọc được": 8/20 trùng
  8/8 ID với security qua phương pháp khác + cổng cấm-chạy-lẻ. Kèm `test_dua_refresh_token.py`
  — giả thuyết đua bác bằng đo, file ở lại canh tính-chất-đang-đúng, docstring giữ lịch sử.
  ⑤ **`tests/CHUAN-VIET-TEST.md` lên 8 LUẬT** — Luật 6 (skip tự chứng minh) · Luật 7 (canh chính
  công-cụ-đo) · Luật 8 (phát hiện công cụ sai = một ĐƯỜNG ĐO KHÁC, không phải sự cẩn thận — 6 ca
  thật/một buổi/hai vai) + `TIEU-CHI-CI.md` (F-CI, F-CI-2, CI-10/11) + 2 bộ tier-1 cũ bỏ tầng
  dò-đoán-tên (chúng SKIP TỪ NGÀY VIẾT vì đoán `phan_tier` ≠ tên thật `_phan_loai_tier`). Nhánh rác `test/bo-do-va-bang-chung-16-08` đã xoá; KHÔNG tạo PR ngược
  (PR rỗng cho đẹp số là thứ không làm khi BTC đếm PR).
- **HAI LUẬT GIT MỚI (ratify, áp cả 4 phiên):** ① `git commit <pathspec> -m …` MỘT LỆNH — cấm
  add-rồi-commit-rời, index dùng chung không được có trạng thái chờ; ② sau MỌI lệnh đổi HEAD,
  ĐỌC LẠI HEAD trước lệnh kế (in ra chưa đủ — phải đọc).
  **Addendum ①b (coder bắt):** một-lệnh KHÔNG phủ FILE CHƯA TRACK — ca đó `git add <file> &&
  git commit <cùng file>` DÍNH LIỀN; thấy staged-LẠ trong status thì DỪNG HỎI, không commit đè.
  **Addendum ②b (PO-agent tự dính ngay sau khi ratify ②):** đọc HEAD phải đọc CẢ TÊN NHÁNH —
  3 commit docs của PO-agent (923e42a·ed0d237·3493dbd) đi lạc lên nhánh coder vì cây chung bị
  chuyển nhánh giữa chừng mà PO-agent chỉ đọc hash, không đọc nhánh. Đã cứu về dev bằng
  push-ref + worktree, không mất gì.
  **Addendum ③ (quy ước cây chung):** CHUYỂN NHÁNH cây dùng chung = ĐỔI VẬT của cả 4 phiên —
  phải BÁO TRƯỚC như rebuild image; làm việc nhánh riêng ưu tiên `git worktree` thay vì checkout
  tại chỗ.
- **QUY ƯỚC PR (PO thật chốt trực tiếp với tester):** các vai tách nhánh + tạo PR, **KHÔNG tự
  merge — PO thật là người merge**. PO-agent gom danh sách PR chờ-merge cho PO duyệt theo đợt;
  chờ-merge không được chặn việc kế (nhánh sau đâm trên nhánh trước nếu phụ thuộc).
- **RAG đòn 1 — KHE MỞ, đang chạy:** tester xác nhận không giữ phép đo trên demo. Trình tự chốt:
  re-index trước (backup Chroma+policy_chunks, báo nhãn kho mới số-chunk+băm) → tester soạn
  golden-set trên kho MỚI (nhãn đoạn gắn kho — soạn trước là công đôi + vật-trôi). Ràng buộc cặp
  trước/sau: **GIỮ NGUYÊN VĂN 8 câu probe** (cùng bộ câu, khác kho — một biến). Golden-set ETA:
  ~3h sau nhãn kho mới cho bản DỰ THẢO; thành THƯỚC sau vòng soi-trục-thiếu của security+coder.
  Thiết kế hay của tester ghi lại: bộ có **ca đối chứng ÂM TÍNH** (câu không có đáp án trong kho
  ⟹ Recall phải =0 — chống thước-tự-thưởng).

## 🎯 QUYẾT ĐỊNH PO THẬT 16/08 — BENCHMARK + LEARNING LOOP v1 (mới nhất)
1. **Chiến lược đánh giá chất lượng: CHỐT** theo `2026-08-16-chien-luoc-danh-gia-chat-luong.md`
   (kim tự tháp 3 tầng · lấy taxonomy OpenAI graders không lấy hosted · heldout 60 niêm phong).
2. **Benchmark spec v1 + v0: CHỐT** (`2026-08-16-benchmark-spec-va-v0.md`, PR #3) — trọng số
   30/25/20/15/10; **v0 = 68,75/85 điểm đo được (80,9%)**, điểm nghẽn định lượng: Truy hồi RAG
   3,75/20 (Recall@3 probe: 0/8 không dấu · 3/8 có dấu — đáp án CÓ trong kho ⟹ lỗi tầng truy hồi).
   Đang chạy: tester golden-set truy hồi 30-50 câu + script benchmark + gói 30 ca nhãn PO (hiệu
   chuẩn judge ≥85%) · coder RAG đòn 1 (extraction sạch — chunk dính "Giao D ịch") + đòn 2 (chuẩn
   hoá dấu tầng query), mỗi đòn một PR có đo trước/sau; đòn 3-4 chờ số.
3. **LEARNING LOOP v1: GO** ("sau benchmark chạy luôn phần LLM tự cải thiện") — bánh đà dữ liệu
   CÓ NGƯỜI GÁC, không phải model tự train: ① tín hiệu học ĐÃ thu (reject_reason +
   la_tin_hieu_hoc, ADR-019; maker-checker chống bơm nhãn giả, ADR-020) · ② thước = benchmark
   vừa chốt · ③ mảnh thiếu = **exporter Phase 2** (`eval/candidates/`, test_14 cắm cọc chờ sẵn).
   **TRÌNH TỰ AN TOÀN BẮT BUỘC: ADR-025 phần B land TRƯỚC exporter** — S-02 (`agent_note` chưa
   cọc/chưa scrub) là nguồn tự nhiên nhất của phễu học; mở exporter trước khi đóng cọc = dữ liệu
   bẩn chảy vào bộ học. Sau exporter: quy trình đề-cử→duyệt 10 phút/tuần (PO hoặc uỷ PO-agent sơ
   duyệt) → golden-set tự lớn từ vận hành thật → benchmark v2 chứng minh "học được" bằng số.

## ⚡⚡ QUYẾT ĐỊNH PO THẬT MỚI NHẤT — tối muộn 15/08 (đè mọi mục cũ)
1. **ADR-025 ĐÃ KÝ TOÀN BỘ** — PO thật xác nhận cả 4 con số sau khi đọc giải thích: retention
   5 năm (giữ cờ tư-vấn-pháp-lý) · trần 2.000 ký tự · quyền đọc 2 pha · preview-confirm 2 vòng
   khoá. ⟹ **MỞ KHOÁ cho coder**: Pha-1 audit-log đọc nhóm A · B1/B2 preview-confirm cho `note`
   (2 vòng khoá) · B3 `agent_note` (SAU B1/B2) · nếu cần route/contract mới → quy trình §3.
   Tester: cổng 8/20 sẽ xanh khi B1/B2 land → gỡ marker thành regression-gate.
2. **F-MIG: DUYỆT làm luôn LÔ KẾ TIẾP** của coder (cùng lô với phần B ADR-025 hoặc trước, coder
   xếp) — 4 phép kiểm nghiệm thu trong hồ sơ, quan trọng nhất: so schema hai đường phải TRÙNG.
3. **VIỆC MỚI UI-01**: 2 chỗ JSON thô trong timeline điều tra của ticket (input + kết quả) →
   hiển thị tiếng Việt trực quan cho CSKH + supervisor. Đặc tả đầy đủ:
   `docs/giao-viec/2026-08-15-ui-timeline-dieu-tra-khong-json.md`. Ràng buộc cứng 3 giữ nguyên:
   lớp ĐỊNH DẠNG không phải lớp DIỄN GIẢI, map nhãn tĩnh, giá trị đã che hiển thị nguyên trạng,
   JSON gốc giữ trong expander cho audit.

## ⚡ BA QUYẾT ĐỊNH PO THẬT — chiều tối 15/08 (mới nhất, đè các mục cũ bên dưới)
1. **Billing/CI: PO thật CHỐT ĐỂ LẠI SAU (tối 15/08)** — không giải quyết hôm nay; PO không phải
   owner org, chỉ BTC sửa được, và việc liên hệ BTC dời sang ngày khác. **KHÔNG chặn gì**: tester
   đã chạy đủ lệnh từng job trên host (540 passed sau lô mới), F-CI-2 đã vá sẵn đón ngày billing
   thông. Tin nhắn gửi BTC đã soạn sẵn trong lịch sử trao đổi — khi PO sẵn sàng thì lấy dùng.
   Việc DUY NHẤT sẽ đọng lại nếu quên: bằng chứng CI trên runner + badge cho Demo Day
   (deliverable) — nhắc lại khi gần mốc nộp.
2. **ADR-025: NGUYÊN TẮC ĐÃ DUYỆT** ("chốt theo hướng security"). PO thật uỷ quyền PO-agent research
   chuẩn EU/US cho 3 chỗ trống → **dự thảo ADR-025 ĐÃ VIẾT** vào `docs/DECISIONS.md` với đề xuất:
   retention **5 năm** (max của VN-PCRT-5n/EU-AMLD-5n/US-RegE-2n-sàn, cờ: cần tư vấn pháp lý thật
   trước production) · đọc transcript theo **NGƯỜI PHỤ TRÁCH** + supervisor có audit-log (GDPR 25/32
   · PCI DSS Req 7 · ISO 27001 · SOC 2) · fail-visible = **preview-confirm** (nhân viên thấy bản đã
   che, xác nhận trước khi ghi; engine lỗi vẫn fail-closed 500 giữ ADR-024). Con số chờ PO xác nhận
   nhanh rồi coder mới chạm contract/code phần B + A3/A4.
3. **PILOT 150 NGƯỜI: HOÃN** — PO thật chốt: chỉ mở khi (a) tối ưu **caching** xong và (b) chatbot
   **tự học/tự nâng cấp** được (learning loop Phase 2). ⟹ các mục "trước pilot" (F-29, A1/A2, RAG,
   TPM) **giãn deadline nhưng KHÔNG huỷ** — F-29/A1/A2 rẻ nên vẫn làm ngay trong lô hiện tại. Hai
   cam kết của security (dữ liệu thật + đường xoá) ghi lại cho thời điểm pilot thật.

## Chặn / chờ PO THẬT — RÚT GỌN 15/08 (chip câu 3 + ADR-020 ĐÃ CHỐT, xem "Vừa xong")
- **Hướng đợt 150 người.** Số end-to-end đã có: bộ lọc 17/17 không siết nhầm, RAG retrieval là
  điểm yếu; 4 góc chưa-sẵn-sàng: TPM · 429→500 · timeout · RAG (sổ Đợt 2, mục "429 SẢN PHẨM" +
  "TIMEOUT trên câu phổ biến nhất").
  **➕ Ý KIẾN BẢO MẬT VỀ PILOT (security, kết sổ `80b217a`) — đọc trước khi quyết:**
  > Bốn cửa **KHÔNG chặn pilot về mặt bảo mật**. Thứ **thật sự cần trước pilot** là **A1 + A2** —
  > rẻ, không cần quyết cơ chế, đóng đúng phần *"lưu plaintext vĩnh viễn"*. Phần còn lại
  > (B1/B2, A3, A4) là **nợ đúng hạn, không phải nợ gấp**.

  🔴 **SECURITY KHÔNG CẤP PHÉP CHO PILOT — họ nói bốn cửa KHÔNG PHẢI THỨ CHẶN nó.** Hai chuyện
  khác nhau, và security nhắc lại lần hai để nó không mòn đi qua vài tay. Kèm **hai ràng buộc mà
  PO PHẢI CAM KẾT**, không phải bảo mật cấp:
  1. **Dữ liệu pilot được coi là DỮ LIỆU THẬT** — chịu NĐ 13/2023 như dữ liệu khách thật, **không
     phải** *"dữ liệu demo nên thoải mái"*.
  2. **Có ĐƯỜNG XOÁ sau đợt** — **có người chịu trách nhiệm, có mốc thời gian**, không phải *"tính sau"*.

  **Thiếu một trong hai thì ý kiến của security ĐỔI.**

  ⚠️ **Phạm vi:** bốn cửa không chặn pilot **VỀ MẶT BẢO MẬT**. Bốn góc chưa-sẵn-sàng còn lại
  (**TPM · 429→500 · timeout · RAG retrieval**) **KHÔNG thuộc phạm vi security đánh giá** và
  **không được cộng gộp** vào câu trên.
  ⚠️ Và **bốn cửa không phải một khối** — chúng có **hạng khác nhau**; trộn lại sẽ khiến **A1/A2
  (rẻ, đáng làm ngay) bị kẹt sau A3/A4** (đụng vận hành CSKH, cần PO).
- **PO-1 xong** (key đã xoay). **PO-2**: keys đang tạo lại — AI_LOG_API_KEY + LANGCHAIN keys (key cũ
  401), OPENAI_API_KEY secret PO đang đặt (đã có hướng dẫn). 9118 dòng backlog AI-log ở
  P-121-new/.ai-log chờ submit khi có key mới — ĐỪNG xoá P-121-new tới khi submit xong.

## 🔴 HAI FINDING MỚI 15/08 (chiều) — cần PO thật, ghi đầu vì cả hai chặn kết luận đang có

### F-CI — CI ở P-226 CHƯA TỪNG CHẠY MỘT JOB NÀO (tester `p-226-c8` đo bằng `gh run list`)
13/13 lượt chạy trên `dev/learning-loop` đều `failure` sau **4-5 giây**, annotation nguyên văn:
> *"The job was not started because recent account payments have failed or your spending limit
> needs to be increased. Please check the 'Billing & plans' section"*

**Không phải test đỏ, không phải config sai — ZERO job khởi động.** Hai lượt `success` duy nhất
trong lịch sử repo là "Initial commit" 26/07 (22s/27s, trước khi có bộ test thật).

**Tester đã chạy TRƯỚC đúng lệnh của từng job trên host** (Python 3.14 vs CI 3.12 — ghi rõ để
không đọc thành chắc chắn), HEAD `2e8c888`, để khi runner sống lại thì tách sẵn "đỏ vì billing"
khỏi "đỏ vì code":

| Job | Lệnh CI | Host |
|---|---|---|
| `invariants` | `pytest tests/test_invariants.py` | 23 passed ✅ |
| contract drift | `check_contracts.py` | 3/3 khớp ✅ |
| `lint-and-test` | `pytest tests/ -m "not security_finding"` | **446 passed · 41 skipped · 0 failed** ✅ |
| `security-findings-gate` | `pytest tests/ -m security_finding` | 1 failed — ĐỎ ĐÚNG CHỦ ĐÍCH |
| `appsec` | `pytest tests/test_api/` | **1 failed** · 227 passed 🔴 |

**🔴 F-CI-2 — job `appsec` sẽ đỏ vì LÝ DO SAI ngay khi billing thông.** `appsec` chạy
`pytest tests/test_api/ -v` **thiếu `-m "not security_finding"`** mà `lint-and-test` có ⟹ nó bắt
luôn `test_live_chat_pii_gap.py::…_is_not_masked_before_storage` = **ST2-P0-3**, finding P0 duy
nhất còn lại (3 P0 kia đã vá đợt Auth5). `security-findings-gate` đỏ là ĐÚNG THIẾT KẾ; `appsec`
đỏ là SAI. Vi phạm chiều hai của `tests/TIEU-CHI-CI.md`: *"cổng đỏ vì lý do sai còn tệ hơn không
có cổng — nó dạy cả đội bỏ qua chính cảnh báo đó"*. **Nguy hơn thường lệ vì nó nổ ĐÚNG LÚC billing
vừa thông**, lúc cả đội đang mong thấy xanh và dễ tặc lưỡi nhất. Vá = **một dòng `ci.yml`** (vùng
coder). Tester đã ghi tiêu chí **CI-10** + 2 phép thử vào `tests/TIEU-CHI-CI.md`.

**🟡 F-CI-3 — hai test tier-split TỰ SKIP BẰNG ĐOÁN TÊN HÀM.** Trong 41 skip, 38 có lý do chính
đáng. Còn `test_mau_tier1_chi_thi.py` + `test_f24_recall_tier1.py` skip với *"F-22 CHƯA SHIP"* —
chúng thử 4 cặp module/tên cho `phan_tier`, không thấy thì skip. Nhưng sổ Đợt 2 ghi F-22/F-24/F-25
đã chốt và ship. Tester **không phân biệt được vì không đọc `src/`** (§4): hoặc chưa ship thật
(skip trung thực), hoặc **đã ship DƯỚI TÊN KHÁC** ⟹ hai bộ skip vĩnh viễn trong khi cả đội tưởng
đang được canh. **Khả năng thứ hai ĐÃ XẢY RA một lần cùng đợt này**: `8d26548` — *"O2 mỏ neo tìm
đúng tên `dem_mat_do_liet_ke`, 7 ca hết SKIP"*. **Coder chỉ cần trả lời một dòng: tên hàm thật.**
⟹ **Toàn bộ Đợt 2 ở P-226 chạy với 0 lượt CI có hiệu lực.** Mọi câu "CI xanh chưa" vô nghĩa tới
khi thông. **VIỆC PO THẬT (không phiên Claude nào làm được): Billing & plans của org
`AI20K-Build-Phase-Cohort-3`.** Hệ quả: CI-1/CI-4/CI-5 (`tests/TIEU-CHI-CI.md`) không nghiệm thu
được; CI-1 đã nối dây đúng cho `dev/**` nhưng **chưa bao giờ chứng minh được có hiệu lực**.
Đây là "hiện diện ≠ hiệu lực" ở tầng HẠ TẦNG: `ci.yml` đủ 13 job, trigger đúng, mọi push đều
sinh một lượt chạy — và **không byte code nào từng được kiểm**.

### F-NOTE — `note` scrub CHẶN NHẦM 40%, xoá đúng CĂN CỨ TỪ CHỐI (security `p-226-0f` đo, 0 TPM)
Che PII **ĐẠT** (12/12 ca có PII đều bị che; bộ đối kháng 15 passed/1 skipped). **NHƯNG 8/20 ghi
chú CSKH KHÔNG có một mẩu PII nào vẫn bị đục**, NER gán nhầm cụm nghiệp vụ tiếng Việt:
- *"…từ chối theo chính sách."* → *"…từ chối **[PERSON]**"*
- *"Khách đã rút khiếu nại qua tổng đài, không cần xử lý tiếp."* → *"**[LOCATION]** … không **[PERSON]**"*

**KHÔNG phải "đánh đổi đã chốt".** ADR-024 chấp nhận che-nhầm với tiền đề ĐO ĐƯỢC là *mã 12 số
trùng pattern CCCD* (`test_03`). Lớp vừa đo là **cụm nghiệp vụ thuần bị NER gán [PERSON]** —
tiền đề đó **CHƯA TỪNG ĐO** ⟹ đúng **Luật 8** (đo lại GIAO của các quyết định), họ hàng F-25
(xoá trắng chính sách thật), lần này rơi vào **BẢN GHI KIỂM TOÁN**: supervisor đọc `note` để hiểu
vì sao từ chối, mà bản ghi hỏng nghĩa **TRONG IM LẶNG**.
Gốc: `scrub_pii` docstring tự khai dùng cho **log/span attribute** — mất một chữ trong log thì
không sao; ADR-024 tái dùng nó cho **record có giá trị pháp lý** = đổi hạng mục sử dụng.
⟹ **CHƯA BẬT CI security-gate cho `note`** (bật = đóng dấu xanh lên hành vi làm hỏng audit trail).
Bản vá đụng tiền đề ADR-024 → phải qua PO thật, coder ĐỪNG vá vội.
**Hồ sơ đầy đủ (23KB, §0-§8): `docs/security/2026-08-15-ra-soat-cuoi-sprint-note-scrub-va-pipeline.md`** (`c2c2d06`).
**Đính chính mục "Vừa xong" bên trên:** `note` đủ về **BẢO MẬT**, KHÔNG đủ về **TOÀN VẸN BẢN GHI**.

### 🔴 S-02 (CAO) — tiền đề "chỗ DUY NHẤT" của ADR-024 BỊ BÁC: `InvestigationLog.agent_note`
Route `POST /tickets/{id}/request-more-info` ghi thẳng `req.note` → `agent_note`: **không scrub,
không trần độ dài, không cờ tier**. Probe HÀNH VI (gọi route thật + đọc thẳng DB, không grep tên):
PAN 16 số `9704123456789012` · CCCD · SĐT · tên đều nằm **plaintext trong DB**; note **5.000 ký
tự** nhận trọn (bên `reject` chặn ở 500); payload injection lưu nguyên văn.
Không rò ra khách (3 đường đọc đều gated `cskh,supervisor`; node agent ghi `agent_note=None` nên
không vào LLM). Nhưng hở **NĐ 13/2023** — và `EncryptedText` ĐÃ được áp cho chat content
(`models.py:475`) lẫn RAG (`:513`), nên `agent_note` **chỉ đơn giản bị BỎ SÓT, không phải một
quyết định**. Cộng hở **phễu học Phase 2**: `test_14` cắm cọc cấm `note` ra file ứng viên, **không
có cọc nào cho `agent_note`** — trong khi `investigation_logs` mới là thứ tự nhiên nhất để xuất
làm dữ liệu học.
⚠️ **S-01 và S-02 PHẢI SỬA CÙNG MỘT QUYẾT ĐỊNH** — bê nguyên `scrub_pii` sang cửa thứ hai là
**nhân bản lỗi chặn-nhầm 40% sang trường thứ hai**.

### 🔴🔴 PHẠM VI THẬT LÀ **BỐN CỬA**, KHÔNG PHẢI HAI — đây là quyết định lớn nhất đang chờ PO
Security rà tiếp (`eff47ac`) và mở rộng §8.3 từ 2 lên **4** cửa văn bản tự do:

**CẢ BỐN Ô NAY ĐO BẰNG HÀNH VI TRONG PHIÊN** (`b7e4230` + `eb444eb`) — hai ô phải bổ sung sau:
`description_raw` (security tự thấy không ổn khi nó sắp thành căn cứ quyết ADR-025) và
`messages.content` (PO-agent xin đo, lý do: nhóm A là nơi security khuyến nghị **BÁC** một cơ chế,
mà **bác = để nguyên hiện trạng hở** ⟹ cần số chắc hơn khuyến nghị áp; nếu hiện trạng đã trôi thì
đang bác dựa trên trạng thái không còn đúng). **Kết quả: hiện trạng KHÔNG trôi ⟹ khuyến nghị §2
đứng nguyên** (không scrub · 4/4 PII còn nguyên sau giải mã · 20.000 ký tự · không cờ · injection
nguyên văn). Bảng nay có **4 chiều**:

| Cửa | Ai gõ | Scrub | Trần độ dài | Cờ tier | Mã hoá at-rest |
|---|---|---|---|---|---|
| `messages.content` (live-chat) | khách + CSKH | ❌ | ❌ | ❌ | ✅ `EncryptedText` |
| `complaints.description_raw` | khách | ❌ | ❌ **20.000 ký tự nhận trọn** | ❌ | ❌ **`Text` thuần** |
| `resolutions.note` | nhân viên | ✅ **nhưng hỏng nghĩa 40%** (S-01) | ✅ 500 | ✅ | ❌ |
| `investigation_logs.agent_note` | nhân viên | ❌ | ❌ | ❌ | ❌ (S-02) |

**Hai điểm mới, quyết định cách xếp thứ tự trong ADR-025:**
1. `description_raw` chứa **PII BÊN THỨ BA ngay ở ca dùng điển hình nhất** — *"em chuyển nhầm cho
   anh X, sđt…"*. Người đó **không phải khách hàng**, không có cơ sở pháp lý để lưu. Đo: 5/5 mẩu
   PII còn nguyên văn (2 SĐT · STK · CCCD · **tên bên thứ ba**), injection lưu nguyên văn.
2. Nó là **cửa khách-tự-gõ DUY NHẤT không có mã hoá at-rest** (live-chat có `EncryptedText`, cửa
   này không).
⟹ Nếu PO định làm ADR-025 theo kiểu *"cửa nào gấp làm trước"* thì **`description_raw` KHÔNG phải
cửa nhẹ nhất như tên gọi gợi ý.**

### ✅ ĐIỂM SÁNG — `EncryptedText` KHÔNG chỉ được khai, nó CHẠY THẬT (kiểm bằng BYTE)
Security đọc **byte thô trong DB bằng SQL, vòng qua type decorator**:
```
'gAAAAABqgCRz6DpP1R2B9-N2Sg_Onanat4Bvpi7cdkfHq_vg6UnKiYmU0J9T40Z5quppnkJ8d…'
PII lộ plaintext? -> False        ⟹ mã hoá at-rest CÓ HIỆU LỰC
```
Đây là control **DUY NHẤT trong bốn cửa** được xác nhận bằng **HÀNH VI** thay vì bằng một dòng khai
báo kiểu — ba cửa kia mới chỉ đọc được dòng khai `Text`/`EncryptedText`, **chưa kiểm byte**.
📌 **Nhắc quan trọng: "hiện diện ≠ hiệu lực" áp cho cả thứ ĐANG CHẠY ĐÚNG, không riêng thứ hỏng.**
Ta quen dùng luật đó để bắt lỗi; đây là lần nó dùng để **xác nhận một thứ tốt là tốt thật**.

**Hai hệ quả cho ADR-025:**
1. **CỦNG CỐ lập luận BÁC che-lúc-ghi ở nhóm A.** Ở `messages.content` lớp bảo vệ at-rest **đã hoạt
   động** ⟹ đổi thêm **giá trị chứng cứ** để lấy một mức giảm thiểu nữa là **đánh đổi tồi**. Câu
   *"tại sao không che cho xong cho an toàn"* nay có thêm một vế trả lời: **vì lớp phòng vệ không
   phá gì đã chạy rồi.**
2. **NÂNG giá trị A1.** Mã hoá `description_raw` không phải "thêm một chuẩn mới trên giấy" — là kéo
   cửa yếu lên một chuẩn **đã chứng minh chạy được ở cửa bên cạnh**.

⚠️ **Mã hoá at-rest KHÔNG chạm tới lỗ đọc-theo-vai.** `messages.content` vẫn hở ST2-P0-3 §3: mọi
`cskh`/`supervisor` đọc được **mọi** transcript, không giới hạn theo ca phụ trách. At-rest chống
**mất đĩa/backup**, không chống **người đọc hợp lệ**. Đó là việc **A3** — cần PO quyết vì đụng vận
hành CSKH. Đừng đọc "mã hoá đã chạy" thành "cửa này đã an toàn".

### 🧭 MỘT NGUYÊN TẮC, **HAI CƠ CHẾ** — đọc TRƯỚC khi soạn ADR-025 (security `6f18c9d`)
Phương án + lý do bác cho từng cửa đã viết sẵn:
`docs/security/2026-08-15-co-che-cho-bon-cua-dau-vao-adr-025.md`.

**Nguy cơ lớn nhất của việc gộp bốn cửa vào một ADR là nó kết thành "áp scrub-lúc-ghi cho cả
bốn"** — và số đo nói điều đó **hỏng nặng nhất ở đúng hai cửa quan trọng nhất**. Đây là lý do
security viết phần cơ chế TRƯỚC bản dự thảo, không phải sau.

⚠️ **Đường phân chia KHÔNG phải "nhân viên gõ / khách gõ"** như bảng bốn cửa ở trên gợi ý —
security tự cảnh báo chính bảng của họ dễ dẫn người đọc đi sai. **Trục thật: bản ghi đó có phải
BẰNG CHỨNG không, và người gõ có SỬA LẠI ĐƯỢC không.**

**NHÓM A — `description_raw` + `messages.content` = LỜI KHAI CỦA KHÁCH.** Là căn cứ giải quyết
tranh chấp tiền bạc, và khách **không sửa lại được** (họ đã rời đi).
⟹ **BÁC che-lúc-ghi.** Ba cửa kia hỏng thì mất khả năng ĐỌC; cửa này hỏng thì **mất GIÁ TRỊ CHỨNG
CỨ** — một lời khai bị hệ thống sửa chữ **không đứng được** nếu khiếu nại đi xa hơn (NHNN, hoặc
toà). Cơ chế đúng: **mã hoá at-rest + trần + siết đọc theo NGƯỜI PHỤ TRÁCH (không theo vai) +
retention + che lúc XUẤT**. Chỗ xuất/log mới đúng hạng mục `scrub_pii` được viết ra — **vì bản gốc
vẫn còn**.

**NHÓM B — `note` + `agent_note` = ghi chú thao tác.** Nhân viên **đang ngồi trước màn hình**, sửa
lại được. ⟹ che-lúc-ghi **được**, nhưng phải **FAIL-VISIBLE** (xác nhận vòng tròn), **không im lặng**.

**Cắt lô:**
- **LÀM NGAY, KHÔNG cần PO quyết cơ chế** → nhập vào nhóm việc rẻ: **A1** mã hoá at-rest
  `description_raw` (chỉ là **bù cho ngang chuẩn dự án đã có** — live-chat có `EncryptedText`,
  cửa này không) · **A2** trần độ dài.
- **CẦN PO quyết**: **B1-vs-B2** (chế độ fail-visible) · **A3/A4** (siết đọc + retention — đụng
  vận hành CSKH, không thuần kỹ thuật).
- **SAU CÙNG**: **B3** (áp ba lớp cho `agent_note`) — **phải đi SAU B1/B2**; bê nguyên `scrub_pii`
  sang khi chưa sửa chế độ im lặng = **nhân bản lỗi 40% sang cửa thứ hai**.

**BA điều security ghi rõ là KHÔNG kết luận — giữ nguyên khi soạn ADR-025:**
1. **Không đề xuất con số retention** — đó là câu hỏi **pháp lý** (NĐ 13/2023 + thời hiệu khiếu nại
   TT 40/2024), có thể cần **tư vấn pháp lý thật**, không phải suy luận của security.
2. **Không kết luận nhóm A có cần scrub ở dạng nào** — nếu PO vẫn muốn thì phải đo trên corpus
   **LỜI KHAI THẬT**, ngưỡng **0 câu bị đổi nghĩa**.
3. **`messages.content` là cửa DUY NHẤT chưa probe hành vi trong phiên** (số dẫn từ ST2-P0-3 14/08
   + đọc `models.py`). Nếu ADR-025 quyết dựa trên nó → **nói một tiếng, security đo như đã đo ba
   cửa kia**.

§7 hồ sơ cũ đã cảnh báo *"chốt riêng lẻ sẽ tạo tình trạng che ô chat để hở ô mô tả, người soi bảo
mật tìm ra trong năm phút"* — nay quy mô **gấp đôi**, và một trong bốn cửa đã "được che" theo cách
**làm hỏng bản ghi**. ⟹ **S-01 + S-02 + ST2-P0-3 + `description_raw` là MỘT quyết định, không phải
bốn.** ADR-025 nên phủ **cả bốn cửa**, không riêng `note`.

### ⚠️ SECURITY TỰ BÁC ĐƠN THUỐC CŨ CỦA CHÍNH HỌ — đọc trước khi trả lời §8.2
Hồ sơ ST2-P0-3 §5.2 kê **"dùng `scrub_pii`, giữ 4 số cuối"** — đúng cái hàm hôm nay đo được chặn
nhầm 40%. Tin nhắn live-chat **chính là** văn bản tự do tiếng Việt, cùng loại đầu vào đã đo. Áp
nguyên văn sẽ mang lỗi vào **lời khách gõ cho CSKH**, và ở đó **hậu quả NẶNG HƠN `note`**: che tại
điểm GHI ⟹ **không còn bản gốc**, CSKH đọc một khiếu nại đã bị sửa nghĩa mà không có cách nào biết
chữ nào đã mất (`"không cần xử lý tiếp"` → `"không [PERSON]"` đủ để xử lý sai ca).
- **KHÔNG đổi:** khuyến nghị vẫn là **B**, vẫn phản đối **C**, lỗ hổng §3 vẫn thật.
- **ĐỔI:** câu hỏi §8.2 (*"giữ 4 số cuối hay che trọn"*) **không còn đủ** — phải hỏi TRƯỚC nó
  **"che bằng CƠ CHẾ nào"**. Trả lời §8.2 trên bản cũ = chọn giữa hai biến thể của một cơ chế đã hỏng.
Đính chính đã vào hồ sơ tại `eff47ac` (cảnh báo đầu file + gạch bỏ §5.2 tại chỗ, giữ nguyên văn cũ
để thấy được cái gì đã đổi).

### ST2-P0-3 — **GIỮ NGUYÊN mở/đỏ, KHÔNG đổi trạng thái** (security đo lại rồi mới trả lời)
Không phải finding lỗi thời mà là **quyết định sản phẩm chờ PO thật**, cố ý giữ đỏ để câu hỏi khỏi
bị đóng im lặng. Lỗ §3 còn hở nguyên: `messages.content` lưu nguyên văn, không retention, mọi
`cskh`/`supervisor` đọc được bất kể có phụ trách ca hay không.
⟹ **F-CI-2 sửa ở JOB CI, KHÔNG sửa bằng cách đóng finding** — đóng một finding đang mở để CI xanh
thì CI xanh mà lỗ vẫn hở. Security xác nhận defect: `ci.yml:251` = `pytest tests/test_api/ -v`,
thiếu `-m "not security_finding"`, còn `test_live_chat_pii_gap.py:25` có `@pytest.mark.security_finding`.
Họ cũng **BÁC nghi ngờ thứ hai của chính mình**: job `appsec` KHÔNG thiếu env (`JWT_SECRET_KEY` /
`FIELD_ENCRYPTION_KEY` ở khối `env:` mức workflow `ci.yml:23-31`, mọi job thừa hưởng) ⟹ **MỘT
defect ở job này, không phải hai**.

### 🔴 S-03 (NÂNG HẠNG 15/08 tối — CA DƯƠNG TÍNH ĐO ĐƯỢC, `c99361d`) — exception lên trace không qua scrub
`span.set_status` / `record_exception` (`langchain_callback.py:96-98`). **Không còn là rủi ro suy
luận**: security đo THẬT trên Postgres có sẵn của dự án (`fin05-postgres-1`, docker-compose):
```
DETAIL:  Key (phone)=(0912345678) already exists.   ← SĐT NGUYÊN VĂN trong DETAIL
```
→ vào `str(error)` → `span.set_status(..., str(error))` + `record_exception` → **ra thẳng backend
trace, không qua scrub** (`_scrub_and_truncate` chỉ áp attribute khác). Đường rò: BẤT KỲ vi phạm
unique constraint trên cột có PII (đăng ký trùng SĐT, upsert…). SQLite im lặng — đúng lớp lỗi chỉ
lộ sau deploy. Tái lập 3 dòng SQL. Security tự ghi nhận: trước đó họ khẳng định từ hiểu-biết-chưa-đo
— đúng lỗi họ vẫn đòi vai khác không mắc; nay đã đo. Bỏ nhánh "không dựng được Postgres thì khai
chưa-đo" trong bộ probe — Postgres có sẵn, S03-01..03 chạy ngay khi coder land.
**Bộ probe A1/A2 viết sẵn ở scratchpad** (đúng quy ước nháp): A1-01 byte-level · A1-02/03 round-trip
biên VN-đủ-dấu+emoji · A1-04 hàng-cũ (ca CHẨN ĐOÁN, không assert — chờ coder trả lời minh thị
backfill) · A2-01/02 hai mép 2000/2001 · A2-05 · A2-06 đường agent. Script kẹp dấu `he_thong` HAI
ĐẦU — lệch = phép đo VÔ HIỆU, không phải "gần đúng".

### 🟡 F-28 (TB) — tier-1 tiếng Anh neo vào MỘT động từ `ignore`; việc coder, KHÔNG cần PO quyết
Tester + tech-lead hội tụ bằng **hai phương pháp khác nhau** (Luật 16): mẫu tier-1 tiếng Anh chỉ
neo `ignore`, nên 7 câu tấn công **cùng ý định, đổi động từ** đi thẳng qua (`disregard` · `forget`
· `override` · `bypass` · `skip` · `do not follow` · `must not obey`). Security đo bổ sung: mẫu mở
rộng đưa độ phủ **1/8 → 8/8**, **FP 0/1814** trên kho MoMo thật (239K ký tự) và **0/7** trên đối
chứng tiếng Anh hợp lệ ⟹ thoả tiêu chí vào tier-1 do chính F-25 đặt. **Vá được ngay, không đổi
contract, không cần PO** — chỉ cần xếp lịch.

⚠️ **Hai vế phải giữ, đừng rút gọn khi báo cáo:**
- **(a) TRUNG BÌNH, KHÔNG phải P0** — F-25 §3(a) đã tuyên bố tier-1 **không phải lằn ranh**: nội
  dung vẫn bị spotlighting bọc và vẫn qua O1-O4.
- **(b) Bản vá KHÔNG đóng LỚP lỗi** — thêm 9 động từ vẫn là **danh sách viết tay**. Luật 18
  (ADR-023) đã sửa lớp này **cho tiếng Việt** và **chưa từng sửa cho tiếng Anh**; việc đó thuộc
  **CỔNG-A**. Sau khi vá phải nói *"bắt thêm 7 ca ĐÃ BIẾT"*, **không** được nói *"đã chặn lớp tấn
  công đổi-động-từ"*.

### ✅ Đính chính F-25 §3(a) — hai "lệch impl-vs-đặc-tả" của tester, coder KHÔNG phải vá (`d312428`)
Tester chặn ở hai lệch trên lớp tier injection; security phân xử: **một không phải lệch** (impl
ĐÚNG, kỳ vọng sai — kéo `bo qua…` về tier-1 sẽ **mở lại đúng lỗ F-25 vừa bịt**); **lệch còn lại là
chữ security viết sai**, họ tự rút sau khi đo FP `0/1814` — đúng phép đo mà F-25 §4 giao cho
security, nay mới làm. ⟹ **Coder không phải vá cả hai; tester viết lại kỳ vọng.**

### 📌 LUẬT MỚI (security rút, đáng đưa vào chuẩn dự án) — assert VẮNG MẶT mù với XOÁ QUÁ TAY
Assert dạng `X not in db` **LUÔN XANH khi nội dung bị xoá nhiều hơn cần thiết** — xoá càng mạnh
test càng xanh. ⟹ Một bộ test chỉ hỏi *"PII có vắng mặt không"* **KHÔNG THỂ** phát hiện over-scrub,
chạy bao nhiêu ca cũng vậy. Đây là lý do cấu trúc khiến bộ 13 ca của tester xanh mà lỗ 40% vẫn
lọt — **bộ test KHÔNG yếu**, nó đo đúng thứ đặc tả (TM-03) yêu cầu; vế toàn-vẹn thiếu vì **không
được viết vào sign-off**, không phải vì ai làm ẩu. Hai câu hỏi phải đi CẶP:
tester hỏi *"X có vắng mặt không"* · security hỏi *"cái CÒN LẠI là gì"* — đúng **Luật 16**, giá trị
nằm ở **sót khác chỗ nhau**. Khi vá S-01, trục đối chứng phải đo *"căn cứ từ chối còn đọc được
không"* và **để FILE RIÊNG** với bộ che-PII (nhét chung = mời một lần sửa làm hỏng cả hai).

**Vế bổ sung (security, để luật đủ dùng về sau):** luật này **không nói bộ test SAI — nó nói bộ
test ĐO SAI THỨ**. Nên cách vá **không phải "viết assert chặt hơn"** mà là **thêm một câu hỏi KHÁC
LOẠI**: cạnh mọi assert *"PII có vắng mặt không"* phải có ca đối chứng *"nội dung hợp lệ có SỐNG
SÓT không"*. Thiếu vế hai thì **bản vá chặt tay nhất luôn thắng theo số đo** (đúng Luật 2 — và là
lý do 27/96 của O1-O4 mới lộ ra được). Hạt giống có sẵn: **corpus 20 ca ghi chú sạch** security đã
giao tester ở §7 hồ sơ 15/08, ngưỡng **0/20** — không phải "thấp hơn".

### F-LOG — bản vá `submit_log.py` (`eadcca7`) NUỐT DÒNG JSON HỎNG, im lặng (tech-lead đo A/B)
Chạy `submit_log.py` THẬT với server giả + `AI_LOG_DIR` giả ở scratchpad (không đụng `.ai-log`
thật, không đụng `src/`). Kịch bản 10 dòng, 1 dòng bị cắt giữa chừng:
```
TRƯỚC vá (eadcca7^) băm f1e4950e1df6 : archive 10 dòng · dòng hỏng CÒN (truy được)
SAU   vá (eadcca7)  băm ab75391a3e09 : archive  9 dòng · dòng hỏng MẤT HẲN
```
Cơ chế: `submit_log.py:118-119` nuốt dòng không parse được (`except JSONDecodeError: pass`).
Trước vá, `_archive(pending)` chép NGUYÊN FILE nên dòng hỏng vẫn nằm lại archive. Sau vá,
`_archive_entries(entries)` chỉ ghi bản ghi ĐÃ PARSE → dòng hỏng không gửi, không archive, rồi
`pending.unlink()`. **Mất cả ba đường cùng lúc, không một dòng cảnh báo.**
**NẶNG vì:** STATE này tuyên bố *"bằng chứng khách quan DUY NHẤT là `.ai-log/archive/`"* — bản vá
làm suy yếu đúng kênh đó, và nó sắp chạy **19 lượt trên 9133 dòng backlog P-121** (deliverable #4).
`73/73 parse sạch` ở lượt 15/08 **KHÔNG** loại trừ: 73 dòng sạch thì nhánh nuốt-lỗi không chạy —
lại đúng "hiện diện ≠ hiệu lực" (nhánh CÓ tồn tại ≠ nhánh ĐƯỢC canh).
Vá ~3 dòng: gom dòng không parse được, ghi bytes GỐC vào archive (hoặc `*.hong.jsonl`) TRƯỚC
`unlink`. **CHƯA SỬA** — `scripts/` ngoài vùng ghi của mọi vai (xem F-ZONE), chờ PO thật giao.
⟹ **Khuyến nghị: vá F-LOG TRƯỚC khi đẩy backlog P-121**, đừng chạy 19 lượt trên đường có lỗ.

**Hồ sơ phép đo (Luật 10): `docs/giao-viec/2026-08-15-do-luong-F-LOG.md`** — hai script đo giữ
NGUYÊN VĂN trong đó, chạy lại được, chỉ thư viện chuẩn. **PO-agent đã chạy lại độc lập, khớp từng
số** (băm hai script tính lại bằng `shasum` cũng khớp con số tech-lead báo). ⚠️ Đó là **chỗ đặt
TẠM** vì bản gốc nằm ở `/private/tmp` gắn phiên tech-lead (phiên đóng = bằng chứng bốc hơi, và
đường dẫn chết trong hồ sơ tệ hơn không có); chỗ đúng là `scripts/` hoặc `tests/`, **chờ F-ZONE**.
⚠️ CA2 + phần B **CỐ Ý ĐỎ** (ca tái lập finding, không phải test hồi quy) — đừng ai sửa cho xanh.
**Bẫy đã ghi trong hồ sơ:** CA3 (tuần tự) báo thứ tự ĐẠT còn phần B (đua thật) báo TRƯỢT — cùng
một câu hỏi, ngược nhau; F-LOG-2 **chỉ hiện ra dưới đồng thời thật**, test tuần tự sẽ xanh giả.

**TIN TỐT cùng lượt đo:** nhánh **leftover CHẠY ĐÚNG** — 502 dòng, `BATCH_LIMIT=500` → lượt 1 gửi
500 + "2 deferred", lượt 2 gửi 2; `archive 502 dòng · id duy nhất 502 · trùng lặp 0`. Bản vá làm
đúng điều nó hứa, backlog sẽ không phình archive.

**F-LOG-2 (thấp, CÓ TRƯỚC bản vá — không phải hồi quy):** `submit_log.py:155` dùng
`open(LOG_FILE, "a")` → leftover (CŨ) bị nối SAU phần hook vừa ghi (MỚI); đo thật ra thứ tự
`[900, 901, 500, 501]`. Trớ trêu: nhánh THẤT BẠI `_restore_pending()` cố ý xử đúng ca này (có
comment *"pending (older) + LOG_FILE (newer)"*) — **nhánh thành công mắc đúng lỗi mà nhánh thất
bại được viết ra để tránh**. Chưa từng quan trọng vì leftover chưa từng chạy; backlog P-121 là lần
đầu nó thành thật. Sai thứ tự, KHÔNG mất dữ liệu — server sắp xếp lại được nếu bản ghi có timestamp.

### F-ZONE — `scripts/` là VÙNG VÔ CHỦ trong §4 (đề xuất, PO thật quyết)
§4 giao `src/ frontend/src/ migrations/ contracts/` cho tech-lead, `docs/` + `*.md` gốc cho po —
**không ai sở hữu `scripts/`**. Đó chính là chỗ bản vá `_archive_entries()` nằm lửng lơ trong cây
làm việc mà không vai nào nhận. Tech-lead xác nhận **không phải nháp của phiên này** (phiên khởi
động sạch, chưa ghi byte nào) ⟹ là của một PHIÊN TRƯỚC. Đề xuất thêm một dòng vào §4 giao
`scripts/` cho tech-lead, để nháp mồ côi lần sau có chủ.

## Cảnh báo còn tồn
- **gate-96 giờ BẬT THẬT** (`e4ef0e8`, không còn tắt — mục trên đã lỗi thời, sửa 15/08).
- **Số end-to-end gắn với hệ thống KHÔNG CÒN TỒN TẠI** (tester đo): lượt "sau" chạy ở
  `he_thong 6096dc8b5678` (commit `8d26548`); cây hiện tại `fd16681d8088` vì `7b68992` (note) land
  sau đó. ⟹ hai số **HÀNH VI** (câu 2: 17/17 · câu 4: 2/5) gắn hệ thống đã mất; hai số **DỮ LIỆU**
  (câu 1 cổng-96 · câu 3 fallback) mua vĩnh viễn. Trích cho quyết định 150 người thì trích được
  cả bốn, **chỉ cần ghi rõ nhãn**.
- **Cửa sổ đóng băng ĐÃ ĐÓNG** — security nhắn "MỞ TAY `src/`" sau khi nộp hồ sơ `c2c2d06`.
  Không vai nào đang giữ mốc nền. Coder chạm `src/` được khi PO giao việc.
- 🔴 **MỐC NỀN 18/20 `6c5fff420bb9` ĐÃ TRÔI** — cây làm việc nay `fd16681d8088` (đúng dự kiến:
  O1-O4 + F-27 + `note` đã land). **Hệ quả: lượt đo mới KHÔNG ghép cặp trước/sau với mốc cũ được
  nữa.** Đợt CỔNG-A phải đóng băng một **mốc nền MỚI ở một `he_thong` xác định TRƯỚC khi tiêu
  TPM** — không thì lặp đúng sự cố `8e46f28→6c5fff`.
  📌 **GHIM — security xin được gọi TRƯỚC lượt đo đầu tiên của CỔNG-A, không phải sau.** Bước đóng
  băng mốc nền mới là bước **không được bỏ**; gọi sau thì **lượt đo đã hỏng rồi mới biết**, và TPM
  đã tiêu. Đây là mốc tương lai duy nhất security chủ động xin ghim khi đóng sổ.
- **Rà pipeline scrub mới xong PHẦN OTel/callback.** CHƯA rà: đường **Langfuse** (đang TẮT có chủ
  đích) và **đường log của eval** (`logging_config` chưa init ở runner). Ghi rõ để không ai đọc §5
  của hồ sơ security thành "đã rà hết".
- **MT-E02 thu hẹp** (security §6): chỗ nổ xác định = `investigation_log.py:89 session.flush()`,
  FK `investigation_logs.ticket_id`. **MT-E02 và MT-F01 traceback TRÙNG HÌNH DẠNG** ⟹ nhiều khả
  năng **một defect hai tên** (đúng chỗ sổ ghi "coder gọi MT-F01, tester gọi MT-E02"). Cơ chế sinh
  id cũ **CHƯA kết luận** (Luật 5) — **giữ nguyên: ĐỪNG đốt TPM tái hiện**. Góc bảo mật mới: flush
  chết ⟹ mất `investigation_logs` của lượt đó ⟹ **ĐỨT MẮT XÍCH chuỗi truy vết của RÀNG BUỘC CỨNG
  3**, im lặng.
- **Mốc nền đối kháng chốt VĨNH VIỄN 18/20** (he_thong 6c5fff420bb9); 18 ca MÙ với siết-nhầm → "18/18→18/18"
  là chốt-chặn-hồi-quy MỘT NỬA, nửa kia đo bằng 🔇 + F-25(b). MT-A01/F-01 không quay lại nhánh "trước" được.
- CI: **TẤT CẢ đều treo sau F-CI (billing), không phải "chưa làm"** — note-tests đã land và xanh ở
  MÁY (15 passed), thiếu đúng phần quan sát trên runner · 2 eval chờ PO-2 secret · CI-4/5 chưa
  nghiệm thu. Không mục nào tiến được tới khi billing thông.
- **[c] oracle-phủ-định "không phải 21"** còn lọt (1 bit/lượt, có tài liệu) → đợt cổng-A (vẫn treo).
- Môi trường test cục bộ (máy PO-agent) thiếu sẵn `argon2` + model NER `xx_ent_wiki_sm` — không phải bug,
  chỉ là máy này chưa từng dựng venv cho repo (dùng venv scratchpad tạm, không commit).

## 📋 PHÂN CÔNG SONG SONG 15/08 (chiều muộn) — PO thật uỷ quyền PO-agent giao 3 vai
> PO thật chỉ quản PO-agent; PO-agent giao việc + nhận báo cáo từ 3 vai. Nguyên tắc chia:
> **vùng ghi tách hẳn** (coder: `src/`+`ci.yml`+`scripts/` · tester: `tests/`+`eval/` · security:
> `docs/security/` · PO-agent: `docs/`) và **không vai nào giữ mốc đo trên `src/` trong lúc coder
> mutate nó**. Ba việc đầu mỗi vai đều KHÔNG cần chờ vai khác.

| Vai | Việc (thứ tự ưu tiên) | Ràng buộc chính |
|---|---|---|
| **Coder** (`p-226-8f`) | ① F-CI-3 trả lời tên hàm `phan_tier` (MỘT DÒNG, đang chặn tester) → ② F-CI-2 một dòng `ci.yml` (trước khi billing thông; CẤM sửa bằng đóng ST2-P0-3) → ③ A1+A2 `description_raw` (CẤM scrub — nhóm A chờ ADR-025) → ④ F-LOG (gate đẩy backlog P-121) → ⑤ S-03 → ⑥ F-28 | BÁO-TRƯỚC-KHI-LAND mọi commit chạm `src/` · nháp ở scratchpad · S-03/F-28/A1/A2 KHÔNG tự đóng, chờ security probe |
| **Tester** (`p-226-c8`) | ① Port 2 script F-LOG vào `tests/` canh nhánh leftover (CA2+phần-B CỐ Ý ĐỎ, không sửa cho xanh) → ② Dựng trục đối chứng "căn cứ từ chối còn SỐNG SÓT không" (corpus 20 ca, ngưỡng 0/20, FILE RIÊNG; XÂY chưa chạy gate — chờ ADR-025) → ③ Gỡ skip 2 test tier khi coder trả lời tên hàm | KHÔNG đọc `src/` · KHÔNG mốc nền/TPM đợt này (coder đang mutate `src/`) |
| **Security** (`p-226-0f`) | ① Rà nốt 2 đường scrub tự khai "chưa rà": log-eval (ưu tiên, dính F-LOG) + Langfuse (mức "nếu bật thì rò gì") → ② Soạn trước bộ probe cho A1 (byte-level) · A2 (2 mép) · S-03 (cần Postgres, không kết luận từ SQLite) · F-28 (kèm đối chứng) → ③ GIỮ CHỜ: ADR-025, MT-E02 | Cần đóng băng `src/` thì báo PO-agent xin coder dừng tay, không tự lấy mốc |

**Điểm khớp nối:** coder land ①→tester gỡ skip · coder land ③④⑤⑥→security probe→mới đóng ·
ADR-025 ký→tester chạy trục đối chứng làm gate + coder làm B1/B2/B3/A3/A4.

### Tiến độ phân công (cập nhật chiều muộn 15/08)
- **✅✅ LÔ ĐÓNG SỔ HOÀN TOÀN — security nghiệm thu CẢ BỐN ĐẠT** (biên bản `9122677`, probe tại
  `cf98ef8`, `src/` byte-identical với `cc07dd3`): **A1** ĐẠT probe-bằng-byte **KÈM ĐIỀU KIỆN**
  (chỉ bảo vệ dữ liệu ghi TỪ `cc07dd3` trở đi — *"A1 đã nghiệm thu" ≠ "description_raw đã được mã
  hoá"*, hàng cũ vẫn plaintext, backfill = quyết định PO TRƯỚC pilot) · **A2** ĐẠT chặn ở tầng
  service không rơi xuống CHECK · **S-03** ĐẠT trên Postgres THẬT (lỗi thật từ container →
  `[PHONE_NUMBER]`, 0 PII trong span, vẫn giữ tên constraint để gỡ lỗi — hai vai bù đúng thiết kế:
  coder tự khai "chuỗi lỗi mô phỏng" → security lấy lỗi thật) · **F-28** ĐẠT 8/8 · 0/7 · FP 0/1814.
- **📌 GIỚI HẠN CÔNG CỤ DẤU-BĂM (tech-lead chỉ ra, security xác nhận):** `he_thong` băm
  `src/**/*.py` — **KHÔNG phủ `scripts/` + `migrations/`**. Lô chạm ngoài `src/` sẽ có dấu
  **không lệch mà vẫn VÔ NGHĨA**. Nhãn phép đo cho lô đa-vùng: dùng **SHA commit**, không dùng
  `he_thong`. (Biên bản `9122677` dùng SHA vì đúng lý do này.)
- **🎁 DẪN XUẤT THỨ BA CHO S-01 (từ probe S-03):** scrub gán `DETAIL`/`ERROR` → `[ORGANIZATION]` —
  cùng lớp lỗi với `"chính sách"` → `[PERSON]` nhưng ở **đường khác** (trace ≠ note), **vai khác**
  phát hiện, **phương pháp khác**. Ba dẫn xuất độc lập cùng kết luận: **sai NHẬN DẠNG, không sai
  NGƯỠNG — lỗi là thuộc tính của LỚP NER, mọi cửa dùng `scrub_pii` đều thừa hưởng.** Đây là lập
  luận mạnh nhất cho việc ADR-025 quyết CƠ CHẾ, không vá từng cửa.
- Security tự đính chính trong biên bản: khuyến nghị 40.000 của họ ở phản biện **sai ở mép trên**
  (thiếu trục chặn-flood) — ADR đã ghi 12.000 + cửa sổ từ `cda800d`, khớp. Quét `.md` trong
  `eval/results` đóng: **0 SĐT thật** (16/18 seed, 2/18 mảnh mã GD — số "18" ban đầu tự thổi bởi
  đúng false-positive đó).
- **F-LOG-2 ĐÃ LAND `e321780`** (sớm hơn lịch), tester gỡ marker F-LOG xác nhận 5 passed · 1 xfailed.
- **🔴 F-28b — tester bắt lỗ TRONG phạm vi F-28 vừa ký:** `disregarding all previous instructions`
  LỌT — dạng **V-ing của chính động từ F-28 vừa thêm** (mẫu đòi dấu cách ngay sau động từ). Không
  phải "lớp rộng chưa làm" — biến thể hình thái của từ trong phạm-vi-tự-nhận-đã-đóng. Coder đo HAI
  bản vá trước khi đề xuất: bản A (liệt kê hậu tố `s|ed|ing`) **cũng lọt** `forgetting` (phụ âm
  gấp đôi — danh sách viết tay vá lỗ danh-sách-viết-tay, thiếu đúng chữ kế, lần hai trong cùng bản
  vá); bản B (thân + `\w*`) đóng **8/8, FP 0/7 + 0/2006 kho MoMo thật**. Đo cả cái KHÔNG đóng:
  5 ca đổi-hẳn-động-từ (`refrain from…`, `pay no attention…`, gõ-sai `ignroe`) vẫn lọt = CỔNG-A.
  ~~PO-agent QUYẾT: đường (1) — land bản B vào tier-1~~ → **🔴 ĐẢO LỆNH sau probe khẩn của
  security (Luật 8 lần SÁU — chân bị rút là của CẢ BA):** bản B gây **FP TIER-1 THẬT** — `ignor\w*`
  bắt `ignorant` (từ khác hẳn), và *"Please do not disregard the safety guidelines"* bị **XOÁ
  TRẮNG** = **F-25 tái diễn nguyên hình dạng bằng tiếng Anh** (khuyến cáo an toàn thật bị xoá).
  Vì sao FP 0/7+0/2006 không bắt được — **corpus có lỗi, security tự nhận corpus của họ**: 7 câu
  đối chứng mỏng đúng trục bản vá chạm (không mệnh-lệnh-phủ-định, không ca `\w*` vươn quá);
  2.006 câu kho MoMo là TIẾNG VIỆT — cấu trúc không thể bắt FP mẫu tiếng Anh. Số đúng, không nói
  gì về lớp lỗi này.
  **LỆNH CUỐI (security đề nghị, PO-agent duyệt): `\w*` vào TIER-2** (giữ nội dung + nhãn trung
  tính + đếm — V-ing attack bị đánh dấu, không bị xoá trắng, vẫn qua spotlighting + O1-O4) ·
  **tier-1 GIỮ HẸP** dạng nguyên thể 0/1814 · phân biệt cực-của-động-từ (`do not follow` tấn công
  vs `do not disregard the safety` khuyến cáo) = sửa LỚP thuộc **CỔNG-A**, cấm nhét vào hotfix.
  Đây là áp đúng tiêu chí F-25 §3(a): vào tier-1 = FP đo được phải bằng 0 trên nội dung hợp lệ.
  ~~Chữ ký F-28 ĐÃ RÚT~~ → **✅ F-28 ĐÓNG HẲN — security ký lại tại `ae954fe`** (biên bản
  `a7c191a`), cổng đối chứng mới **50 ca / 8 trục** thay bộ 7 câu cũ. Bốn vòng trong một tối:
  F-28 → F-28b (bác vì FP tier-1) → F-28c → F-28d → F-28e. Suite **540 passed · 0 failed**,
  ruff sạch, 4 test tier của tester xanh.
- **Hồ sơ F-MIG đặt tại `docs/giao-viec/2026-08-15-f-mig-alembic-sqlite.md`** (tech-lead soạn,
  PO-agent chép nguyên văn vào docs/ — attribution trong file). Chờ PO thật xếp lô riêng; phép
  kiểm quan trọng nhất sau vá = SO SCHEMA HAI ĐƯỜNG (upgrade-head vs create_all phải TRÙNG).
- **HAI LUẬT MỚI từ lô F-28 (PO-agent ratify vào chuẩn dự án):**
  · **Luật mỏ-neo-sau-bỏ-khoảng-trắng** (security `20bb323`): token dùng làm MỎ NEO dưới phép
    khớp ĐÃ BỎ KHOẢNG TRẮNG phải ĐỦ DÀI VÀ ĐẶC TRƯNG để không xuất hiện như chuỗi con, kể cả
    vắt ngang ranh giới từ (ca `these` ⊂ `thesecurity`).
  · **Luật điểm-mù** (coder+security chốt): *điểm mù không được chữa bằng cố gắng — nó được chữa
    bằng việc VỪA NHÌN THẤY cùng lớp lỗi ở người khác.* Hệ quả thao tác: **finding phải được kể
    kèm CƠ CHẾ, không chỉ kèm kết luận** — cơ chế mới là thứ truyền được sang người khác. (Bằng
    chứng: coder viết `system rules` mù với `ecosystem`; thứ cứu họ là ca `these`⊂`thesecurity`
    của security còn nóng trong đầu.)
  · Hệ luận corpus, đúng HAI CHIỀU trong lô: bộ ca do MỘT vai soạn gần như chắc chắn hụt trục
    của vai khác — cả bộ ĐỐI CHỨNG (security hụt trục danh-từ-đích) lẫn bộ TẤN CÔNG (bản siết
    của security tụt recall 3 ca vì bộ 10 ca của họ không chứa chúng).
- **✅ LÔ CODER ĐÃ LAND — HEAD `cc07dd3`** (5 commit: F-LOG `cc07dd3` · F-28 `e082a34` ·
  S-03+F-30+F-29-gitignore `83f45df` · A1+A2 `5b65b81` · F-CI-2+ruff `37ed7fc`). Pathspec sạch —
  không đụng `tests/`/`docs/`. Đo tại `cc07dd3`: ruff sạch · invariants 23 · contracts 3/3 ·
  suite 492 passed/18 skipped/9 xfailed/**1 failed = XPASS(strict) ca F-LOG của tester — cơ chế
  chạy ĐÚNG**: bản vá làm ca tái lập qua được, strict biến "qua" thành đỏ buộc tester gỡ marker
  (họ gỡ, không phải coder). **Chưa đóng A1/A2/S-03/F-28 — chờ probe security** (đã được mời).
- **A2-06 ĐÓNG bằng câu trả lời + số đo:** trần đặt ở `create_ticket_with_fraud_check`
  (`complaint_intake.py:118` — call site DUY NHẤT của `_create_ticket`) ⟹ phủ CẢ BA đường
  (REST `main.py:538` · agent `customer_tools.py:620` · `flag_human_handoff`), đo cả ba có đối
  chứng (3.200→CHẶN · 2.000→NHẬN). Còn TỐT hơn gợi ý đặt-ở-`create_ticket`: trần đứng TRƯỚC fraud
  engine (engine đọc `description_raw` làm `utterance_text`) — không phân tích gian lận trên chuỗi
  20K rồi mới từ chối. CHECK 12.000 không là lưới duy nhất của đường nào — nguyên tắc ADR nguyên vẹn.
- **A1-04 ghi minh thị vào docstring `models.py`** (nơi người sửa tiếp theo thật sự đọc): hàng
  trước 2026-08-15 plaintext VĨNH VIỄN trên đĩa; "đọc được" ≠ "được mã hoá at-rest"; chấp nhận vì
  seed/test + pilot hoãn; **backfill là quyết định RIÊNG phải ra TRƯỚC khi mở pilot**.
- **⚠️ Nuance migration phải giữ khi đọc "A2 đã verify":** migration A2 (`a7b8c9d0e1f2`) **CHƯA
  TỪNG chạy qua alembic** — chuỗi gãy ở `a1b2c3d4e5f6` (SQLite) TRƯỚC khi tới nó; coder verify
  CHECK bằng `create_all` + probe hành vi. "A2 đã verify" ≠ "migration A2 đã verify".
- **F-LOG-2 (thứ tự đảo): PO-agent xếp lịch = lô nhỏ KẾ TIẾP của coder, ưu tiên thấp** — vá rẻ
  (tái dùng logic prepend của `_restore_pending` cho nhánh leftover), xfail của tester đứng làm
  tài-liệu-sống tới lúc đó. Không gấp: sai thứ tự không mất dữ liệu, server sort được theo ts.
- **QĐ 5 / bound 12.000: security ĐO LẠI XÁC NHẬN ĐỦ** (`44c3c9a`) — biên 12% trên worst-case
  emoji 4-byte, và Fernet tất định theo byte nên không có ca xui. **Đủ CÓ ĐIỀU KIỆN** ⟹ ca mới:
- **🟠 A2-06 (CA PHẢI KIỂM, chưa phải finding — security minh thị chưa đo vì cây trôi):**
  `description_raw` có **HAI đường ghi** — REST (qua Pydantic, có trần) và **AI-gọi-tool dưới danh
  nghĩa customer** (`customer_tools` → `create_ticket…`), đường sau **không đi qua
  `ComplaintCreateRequest`**. Nếu đường agent không có trần riêng: mô tả quá dài rơi thẳng xuống
  CHECK DB → `IntegrityError` → 500 (hình dạng F-21), trong khi mọi test REST xanh. **CHECK phải
  là lưới CUỐI, không được là lưới DUY NHẤT của bất kỳ đường nào.** → chuyển coder dạng CÂU HỎI.
- **A1-04 nhắc lại cho probe:** `complaints` ĐÃ CÓ dữ liệu (khác `messages` 0 dòng) — coder chọn
  không-backfill (hàng cũ đọc được qua đường InvalidToken) ⟹ **hàng cũ nằm PLAINTEXT vĩnh viễn
  trên đĩa** trừ khi có quyết định backfill-mã-hoá riêng. Test DB-sạch không lộ ca này.
- **A2 bound CHỐT LẦN CUỐI = 12.000, ghi thành CỬA SỔ [10.764 … 26.764]** (ADR-025 QĐ 5 sửa lần 2):
  40.000 của PO-agent bị coder bác bằng đo — ≈28.943 ký tự ASCII lọt, flood 20K ASCII đi thẳng qua.
  Luật 8 lần NĂM, bắt cả coder (mẫu ASCII) lẫn security+PO-agent (mẫu 3-byte quên emoji 4-byte).
  Thoát vòng = ghi CỬA SỔ kèm cả hai mép, mọi lần đổi số phải đo lại CẢ HAI.
- **Coder vá thêm ngoài phạm vi (chấp nhận, có lý do):** 3 lỗi ruff có sẵn từ trước (N812×2 +
  UP037) — không vá thì job lint đỏ TRƯỚC khi tới pytest, F-CI-2 vô nghĩa.
- **🔴 PHÁT HIỆN MỚI (có sẵn, cần quyết định riêng — CHƯA ai sửa): chuỗi migration GÃY trên SQLite**
  tại `a1b2c3d4e5f6` (ADR-019): `NotImplementedError: No support for ALTER of constraints in SQLite
  dialect` ⟹ `alembic upgrade head` trên DB trắng SQLite CHẾT. Coder verify CHECK A2 bằng
  `create_all` + probe hành vi thay vì alembic. Hướng vá khi giao: `render_as_batch`/batch_alter
  cho SQLite — xếp lịch riêng, không gộp lô này.
- Suite lúc báo cáo: 492 passed · 18 skipped · **9 failed = toàn bộ ở cổng F-NOTE của tester
  (`test_note_toan_ven_can_cu_tu_choi.py`, file chưa track) — ĐỎ CÓ CHỦ ĐÍCH chờ vá B1/B2**,
  không phải hồi quy của lô coder.
- **Coder ①②③(A1) XONG** (báo-trước-khi-land đúng luật): F-CI-2 verify hai chiều (appsec
  227 passed/1 deselected · security-findings-gate VẪN ĐỎ — chuyển finding về đúng job canh, không
  giấu) · A1 `models.py:223` EncryptedText, probe hành vi tiền tố Fernet + đối chứng hàng-cũ-vẫn-đọc
  (đường InvalidToken, không cần migration/backfill) — CHỜ security probe mới đóng. **A2: PO-agent
  quyết phương án (b) + trần 2.000 ký tự** (schema chính-xác-ký-tự + CHECK thô ciphertext ≤4.000;
  Fernet nở theo byte nên DB không diễn đạt được trần ký tự — số đo coder ×1.72-1.9).
- **🔴 Finding mới của coder (Luật 8 lần BA): F-24 vs F-25 MÂU THUẪN trên nhánh EN**
  (`customer_tools.py:152-154` chỉ có comment F-24; `:165` VN có cả hai) — nhánh EN không bị bỏ
  quên, nó bị MỘT trong hai bản vá sờ tới. → security gộp phân xử vào probe F-28.
- **Corpus 20 ca ĐÃ XUẤT FILE** (`c403384`): `docs/security/corpus-ghi-chu-sach-20-ca.jsonl` (+.md,
  8 ca 🔴). Trích **bằng AST** từ script đo gốc — không chép tay, không import src/. **BA GIỚI HẠN
  đi kèm corpus (cấm dùng rộng hơn):** (1) 20 câu soạn tay — chứng minh TỒN TẠI lớp chặn nhầm,
  KHÔNG phải tỷ lệ sản phẩm — **đừng để "40%" đi vào báo cáo PO như tỷ lệ thật**; (2) chỉ phủ nhóm
  B — nhóm A (khẩu ngữ/sai chính tả/không dấu) cần corpus riêng; (3) thuần đối chứng, **PHẢI chạy
  cùng bộ ca có PII, cấm chạy lẻ** — không thì bản vá "không scrub gì" đạt 0/20 hoàn hảo. Mở rộng =
  THÊM ca GC-21+, **không sửa 20 ca gốc** (mất mốc). `ket_qua_goc` là nhãn tại `fd16681d8088` —
  cây ĐÃ trôi sang `f3193ecae0e2` (A1 land); ai đo lại = cặp MỚI đóng dấu riêng, không ghi đè.
- **Tester ①③ XONG** — `tests/test_ai_log/test_f_log_leftover.py`: 3 passed · 2 **xfail(strict)** ·
  suite đầy đủ 478 passed/0 failed. Hai ca finding dùng `xfail(strict=True)` thay đỏ-trần (PO-agent
  RATIFY): hiện rõ trong report, không chặn CI khi billing thông (né hình dạng F-CI-2), và khi coder
  vá F-LOG thì **XPASS tự báo lỗi buộc gỡ marker** — yêu cầu "chỉ xanh sau khi vá" thành CƠ CHẾ.
  Thêm assert server-nhận-đủ (502 archive ≠ 502 đã POST — hai câu hỏi, hai assert). Không port phần
  A/B lịch sử (đã kết luận, `git show eadcca7^` chết trên CI fetch-depth:1) — kết luận giữ trong
  `reason` của xfail. **Việc ③**: `_phan_loai_tier` (coder trả lời) → 2 bộ tier chạy lần đầu, lượt
  đầu 6 failed → security phân xử bằng phép đo mới → tester viết lại kỳ vọng → **29 passed**,
  `he_thong` trước=sau=`fd16681d8088`, `src/` không ai chạm. +5 ca khoá 4 họ tier-1 + Luật 6/6b vào
  `CHUAN-VIET-TEST.md`.
- **Tester ② XONG — trục đối chứng LÀ CỔNG SỐNG** (`he_thong c110a1a8eff7`, dấu trước=sau, đo 3
  lần tất định): **8/20 chặn nhầm, cổng ĐỎ đúng chủ đích**. Giá trị nhất: **DANH SÁCH trùng 8/8
  với security** (GC-02·03·07·10·11·15·17·18) qua **hai phương pháp khác nhau** — security gọi
  thẳng hàm scrub, tester đi đường ghi thật POST /reject → **đọc thẳng DB** (đọc qua API không phân
  biệt được che-khi-ghi với ghi-thô-che-lúc-trả). Chốt được: finding KHÔNG phải hiện vật của cách
  đo · còn nguyên tại cây đã gồm lô A1/F-28 · cổng sống không ai phải nhớ chạy lại. Ba giới hạn
  corpus đều thành CƠ CHẾ (docstring + test cấm-chạy-lẻ đọc `request.session.items`, nghiệm thu
  hai chiều). Bộ đo KHÔNG đọc `ket_qua_goc` để chấm — đo lại từ đầu, đóng dấu riêng.
  **Một lượt đo bị VỨT đúng quy trình** (chạy khi coder sửa dở, dấu trước≠sau): con số không SAI,
  nó **VÔ DANH** — không gán được nhãn hệ thống thì không tái lập/ghép cặp. Khác cơ chế Luật 4
  (pytest import một lần — 20 ca vẫn cùng hệ thống trong bộ nhớ); gộp hai lý do sẽ khiến lần sau
  quy sai nguyên nhân.
  ~~PO-agent quyết: gắn marker `security_finding`~~ → **ĐÈ bằng số đo của tester: cơ chế là
  `xfail(strict=True)` THEO TỪNG CA, KHÔNG marker.** Tester đo thử marker và tìm ra lỗ chết
  người: job `security-findings-gate` lọc `-m security_finding` sẽ **DESELECT bộ ca có PII lẫn
  chính test cấm-chạy-lẻ** ⟹ trục đối chứng chạy MỘT MÌNH trong đúng job đó — bản vá "gỡ sạch
  scrub" đạt 20/20 xanh mà không gì bắt được, đúng kịch bản cổng sinh ra để chặn. Cơ chế
  xfail-strict giữ đủ 3 mục tiêu (không đỏ lint-and-test · không job mới · không chờ coder) VÀ
  giữ cặp đối chứng cùng phiên. **Đọc tín hiệu khi B1/B2 land:** 8 ca XPASS ⟹ suite ĐỎ =
  **THÀNH CÔNG** (buộc gỡ marker → thành regression-gate), đừng đọc thành hồi quy; vá-gỡ-sạch-scrub
  thì bộ ca PII cùng phiên đỏ — hai tín hiệu tách bạch. Cơ chế đã tự bắn ĐÚNG hai lần trong
  phiên (F-LOG, F-LOG-2).
  **Luật 7 (5 mục 7a-7e) vào `tests/CHUAN-VIET-TEST.md`** — canh chính CÔNG CỤ ĐO; đã dán tóm
  tắt sang `docs/TESTING.md` theo yêu cầu tester. Treo nhỏ: 2 failed `EN-S03` chờ security phân
  xử `security` có phải mỏ neo META không.
- **Security ①② XONG** (`7c71905`, không cần đóng băng — toàn đọc tĩnh): đường log eval
  **KHÔNG TỒN TẠI** (`configure_logging()` chỉ ở `main.py:115`) ⟹ câu "log eval có scrub không"
  không áp dụng — chưa có gì để scrub, và hỏng thì không có gì điều tra. **GHIM vào F-LOG: không
  đóng nếu chỉ "có log" — log eval phải qua CÙNG lớp scrub với đường app, verify bằng ca có PII.**
  Bộ probe A1/A2/S-03/F-28 đã soạn, land là chạy; điều kiện ký = đủ BA (hiệu quả + đối chứng +
  dấu he_thong hai đầu), thiếu đối chứng thì không ký kể cả hiệu quả đẹp.
- ⚠️ Nếu `test_mau_tier1_chi_thi.py`/`test_f24_recall_tier1.py` ĐỎ trong lô coder: **không phải
  hồi quy sản phẩm** — hàm đổi tên; gọi tester, đừng sửa test.

### 🔴 F-29 (CAO cho PILOT) — `eval/results/` 138 file TRACK trong git, harness ghi tin khách nguyên văn
PO-agent xác minh độc lập: **138 file track · 74 file `_raw.json` · `.gitignore` 0 dòng về eval**.
File `_raw.json` chứa `all_customer_texts` (tin khách nguyên văn mọi lượt) + `tool_calls_day_du` +
traceback. **Hôm nay phơi nhiễm THẤP** — payload đã che (`********0001`), lớp masking BR-06 chạy
đúng. **Nhưng cơ chế là rủi ro thật:** BR-06 **không che chính chủ** (`lookup_transaction.py:41,53`);
eval chạy dưới danh nghĩa người-không-phải-chủ nên mọi thứ ra đã che — **pilot thật thì khách hỏi
giao dịch CỦA HỌ ⟹ `is_owner=True` ⟹ SĐT/STK/họ tên THẬT không che, vào thẳng file git-track**.
Cộng `all_customer_texts` chưa bao giờ qua scrub.
**Chạm thẳng điều kiện pilot của security ("có đường xoá sau đợt")**: file đã commit thì không có
đường xoá thực hành (xoá commit sau không xoá lịch sử; rewrite+force-push = loại việc luôn phải hỏi
PO, bất khả nếu repo đã clone). ⟹ **chạy harness với người thật mà không sửa = điều kiện pilot TRƯỢT.**
- Mức tối thiểu TRƯỚC pilot: `.gitignore` loại `_raw.json` (→ coder, kèm lô) + scrub-trước-khi-ghi
  (→ tester, vùng `eval/`, sau việc ②).
  **⚠️ PHẠM VI SỬA theo đo lại của tester (không phải chỉ `all_customer_texts`):** trường văn bản
  tự do trong `_raw.json` gồm `all_customer_texts · all_agent_replies · reply · description ·
  tool_calls` — và `reply`/`all_agent_replies` là **lời agent NHẮC LẠI thông tin khách** (tên, số
  tiền, mã GD — đó là mục đích của nó), nên scrub riêng tin khách thì PII thật vẫn rò qua lời agent
  ở pilot. **Phạm vi đúng: scrub MỌI trường văn bản tự do.** Số đo lại: 69 file raw trên đĩa ·
  138 track · 33 file có `all_customer_texts`.
  **HỒI TỐ: KHÔNG scrub lại 69 file cũ — CHỈ chặn từ nay. Lý do ghi rõ (PO-agent quyết):** file cũ
  đã đo là vô hại (eval chạy danh nghĩa không-chính-chủ, BR-06 che hết), và scrub file đang track
  cũng KHÔNG xoá được bản gốc khỏi lịch sử git — muốn xoá thật phải rewrite history, đúng thứ
  security đã cân và chủ động không đòi. Scrub hồi tố = tốn công mà không thêm an toàn thật.
- **138 file CŨ: quyết định của PO THẬT** — phơi nhiễm thấp, rewrite history đắt/rủi ro hơn lợi ích
  (security chủ động KHÔNG đòi xoá), nhưng file kết quả là bằng chứng nộp bài (deliverable #10) nên
  không ai khác quyết thay được.
- Còn treo security tự khai: mới đo MẪU file mới nhất, chưa quét hết 138 file, chưa kiểm các `.md`
  trong `eval/results/`.

### 🟡 F-30 (TB, tiềm ẩn) — LangSmith: kênh xuất dữ liệu mở được bằng env var, không để vết trong git
KHÔNG có tích hợp nào trong `src/` (grep sạch — tin tốt). Nhưng gói `langsmith` 0.11.0 ĐÃ CÀI (kèm
langchain; PO-agent xác minh có trong env), và tracer native của LangChain bật **hoàn toàn bằng env
var**, đi vòng qua `_scrub_and_truncate` (lớp đó nằm trong callback TỰ VIẾT, tracer native không gọi).
Bật trên dashboard ⟹ không diff, không ai review thấy. `docs/guide/chapter-07.md` (giáo trình AI20K,
KHÔNG phải runbook FIN-05) hướng dẫn bật ở production — đội đang học nó. Pháp lý nếu bật với dữ liệu
thật: **chuyển dữ liệu cá nhân ra nước ngoài — NĐ 13/2023 Điều 25**, cần hồ sơ đánh giá tác động.
Vá rẻ (→ coder, kèm lô): đặt `LANGCHAIN_TRACING_V2=false` **MINH THỊ** trong config/Dockerfile —
biến cấu-hình-ngầm thành quyết-định-hiện.

## Việc kế tiếp
0. **PO THẬT — TRƯỚC PILOT (danh sách gom, mới):** quyết **backfill A1** (mã hoá hàng
   `description_raw` cũ — hiện plaintext vĩnh viễn, docstring `models.py` ghi rõ) · cam kết 2 điều
   kiện pilot của security (dữ liệu thật + đường xoá) · A3/A4 pha 2. Pilot đã hoãn nên KHÔNG gấp —
   gom một chỗ để không rơi.
1. **PO THẬT — billing org `AI20K-Build-Phase-Cohort-3`** (F-CI). Chặn mọi nghiệm thu CI.
2. **PO THẬT — MỘT quyết định cho CẢ BỐN CỬA văn bản tự do** (S-01 `note` · S-02 `agent_note` ·
   ST2-P0-3 `messages.content` · `complaints.description_raw`) ⟹ **ADR-025**. Ba lý do buộc phải
   gộp: (a) chốt riêng lẻ = che ô này hở ô kia, hồ sơ §7 đã cảnh báo từ trước; (b) `scrub_pii` —
   cơ chế được kê cho cả bốn — **đã đo được hỏng 40%**, nên phải trả lời **"che bằng CƠ CHẾ nào"**
   TRƯỚC khi trả lời "giữ 4 số hay che trọn" (§8.2); (c) ST2-P0-3 giữ **mở/đỏ có chủ đích** cho
   tới khi có quyết định này — **đừng đóng nó để CI xanh**. KHÔNG để coder tự vá.
3. **PO THẬT — giao ai vá F-LOG** (`scripts/` vô chủ, xem F-ZONE) và chốt: **vá TRƯỚC rồi mới đẩy
   backlog P-121**. Đẩy trước = chạy 19 lượt trên đường có lỗ nuốt-dòng-hỏng, đúng deliverable #4.
4. **Coder — BỐN việc rẻ, KHÔNG cần PO quyết cơ chế, chỉ cần xếp lịch:**
   (a) **F-CI-2** một dòng `ci.yml` thêm `-m "not security_finding"` cho job `appsec` — nên xong
   **TRƯỚC khi billing thông**, nếu không cổng đỏ vì lý do sai đúng lúc đội dễ tặc lưỡi nhất;
   (b) **F-CI-3** trả lời một dòng **tên hàm thật** của `phan_tier` để 2 bộ test tier-split hết skip;
   (c) **S-03** scrub exception trước khi lên trace — độc lập, không chặn gate nào;
   (d) **F-28** mở rộng động từ tier-1 tiếng Anh (1/8→8/8, FP 0/1814) — nhớ **vế (b)**: bản vá
   KHÔNG đóng lớp lỗi, chỉ bắt thêm 7 ca đã biết; lớp thuộc CỔNG-A;
   (e) **A1** mã hoá at-rest `complaints.description_raw` + **(f) A2** trần độ dài — security xác
   nhận **không chờ ADR-025**: A1 chỉ là **bù cho ngang chuẩn đã có** (live-chat đã `EncryptedText`),
   không phải cơ chế mới cần quyết.
   ⚠️ **Cả bốn bản vá S-03 · F-28 · A1 · A2 PHẢI có probe từ VAI KHÁC trước khi coi là đóng** —
   security đã nhận sẵn việc re-probe. Lý do là luật đội đã ratify: **coder tự nghiệm thu là CẦN,
   KHÔNG BAO GIỜ ĐỦ** cho lớp phòng vệ (mọi phép kiểm coder tự thiết kế thừa hưởng điểm mù của coder
   — rút từ sự cố F-23 thật).
3. PO chốt hướng đợt 150 người (số end-to-end đã có, nhớ ghi nhãn hành-vi/dữ-liệu ở "Cảnh báo").
4. Coder: chờ security "MỞ TAY src/" rồi mới chạm. Xếp hàng: chip câu 3 (sau 5a core + QA baseline)
   · đợt cổng-A gộp 3 oracle · câu-4 RAG retrieval (chunk/embedding, trước pilot 150 người).
5. **PO-2**: đặt `OPENAI_API_KEY` thành secret trên GitHub → mở 2 CI eval (chỉ có tác dụng SAU khi
   billing thông).

## Phiên rà soát bảo mật ĐÃ ĐÓNG SỔ — mục lục cho phiên security sau
**`docs/security/2026-08-15-ket-so-ra-soat-cuoi-sprint.md`** (`80b217a`) = mục lục + tư thế rủi ro
tồn dư, **không lặp nội dung**, để phiên sau không phải dựng lại mạch từ 7 commit + một chuỗi tin
nhắn. Năm việc treo security nhận đầu phiên, trạng thái đóng sổ:

| Việc treo | Trạng thái |
|---|---|
| `note` / CI security-gate | **XONG** — kết luận **CHƯA BẬT** |
| mốc nền 18/20 | **ĐÃ TRÔI** `6c5fff` → `fd16681d`, kèm hệ quả bắt buộc cho CỔNG-A |
| oracle-phủ-định "không phải 21" | **KHÔNG ĐỔI** — vẫn thuộc CỔNG-A |
| MT-E02 | **thu hẹp, CHƯA đóng** (cố ý — Luật 5) |
| pipeline scrub | **XONG MỘT PHẦN** — rà OTel/callback; **chưa** rà Langfuse (tắt có chủ đích) + đường log eval (F-LOG) |

### 📌 Về SÁU ca tự-bắt-mình trong phiên (§6 kết sổ) — ghi để đọc đúng, không đọc thành cẩu thả
Sáu ca cùng họ **thước-hiệu-chuẩn-theo-vật**: PO-agent tuyên bố `archive/` là bằng chứng đủ · PO-agent
gọi `note` là việc đã đóng · security viết "cả bốn ô đã đo hành vi" khi một ô chưa probe · security
kê `scrub_pii` ở §5.2 mà chưa đo nó · test skip im lặng hai ngày · 15 kỳ vọng suýt viết theo impl.
Đánh giá security ghi nguyên văn:
> Đây là dấu hiệu **kiến trúc phân-vai ĐANG CHẠY**, không phải dấu hiệu đội cẩu thả. Một đội không
> có cơ chế đối kháng thì các lỗi này **không được PHÁT HIỆN**, chứ không phải không xảy ra.

**Và cả sáu ca đều do CHÍNH NGƯỜI MẮC tự bắt**, không phải do người khác soi ra — thứ khó có hơn cả
việc bắt được lỗi của nhau.

## Hoãn có chủ đích
- Hạ tầng đo temp=0/k≥3 (gói B2 HOLD, floor nhiễu 20/40) · reseed gộp (⚠️ gỡ lọc-A1 khi from_bank sửa) ·
  401/403 hai route OTP · B3 timezone (31 utcnow) · lộ trình EU/US G1(SLA)/G3(audit bất biến) — xem PO-TONG-KET.
