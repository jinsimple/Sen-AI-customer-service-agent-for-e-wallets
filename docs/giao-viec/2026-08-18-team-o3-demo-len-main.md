# GIAO VIỆC CẢ ĐỘI — 18/08 tối · Mục tiêu: demo chạy tốt → lên `main` HÔM NAY

> Người viết: PO-agent (phiên PO của PO thật Đào Ngọc Bích). PO thật đã chốt mục tiêu.
> Đọc kèm BẮT BUỘC trước khi làm: `CLAUDE.md` · `docs/BAN-GIAO-2026-08-18.md` (nhất là §5 BẪY) · `docs/STATE.md` §5.A0.
> Đội 5 vai: **Lead · Coder · QA/QC · Review · Bảo Mật**. Lead điều phối, các vai báo cáo qua Lead, Lead báo cáo PO-agent.
> ⚠️ Vai trong file này ánh xạ hiến pháp §4: Coder = `tech-lead` (vùng ghi `src/`) · QA/QC = `tester`
> (vùng ghi `tests/`, **CẤM đọc `src/`**) · Review = `critic` (không ghi gì) · Bảo Mật = `security` (`docs/security/`).

---

## 1. VẤN ĐỀ — chẩn đoán ĐÃ ĐO, không phải phỏng đoán

**Triệu chứng PO thật thấy:** "chatbot không hoạt động".
**Thực tế đo được (log `fin05-backend-1`, 21:40 tối 18/08, USR-0145):** mọi `/agent/chat` trả HTTP 200,
model trả lời bình thường, nhưng bộ lọc đầu ra **O3** (`fin05.output_filter`, WARNING `output_filter_khop nhom=O3`)
thay câu trả lời đúng bằng `CAU_AN_TOAN` → khách thấy bot "từ chối mãi". Đây là việc ① của bàn giao 18/08.

**Phép đo phân định (PO-agent chạy `_khop_o3` offline trên host, 0 token LLM, tái lập 100%):**
giả thuyết "agent bịa số" trong bàn giao **BỊ BÁC**. Chặn oan do BA cơ chế của chính bộ lọc:

| # | Hành vi hợp lệ của agent | Kết quả | Cơ chế lỗi |
|---|---|---|---|
| 1 | Viết ngày bằng dấu CHẤM `01.08.2026` | 🔴 CHẶN OAN | regex trích số văn xuôi cho `.`/`,`/khoảng trắng làm phân cách → dán thành dãy ma `01082026` không có trong nguồn |
| 2 | Hai số tiền cạnh nhau `1.100.000, 262.000` (không chữ "đ" ngăn giữa) | 🔴 CHẶN OAN | dán qua `, ` thành `1100000262000` — số không tồn tại ở đâu |
| 3 | Nhắc lại mã/số từ **kết quả tool LƯỢT TRƯỚC** (lượt này không gọi lại tool) | 🔴 CHẶN OAN | kênh `nguon` chỉ nạp tool payload CỦA LƯỢT NÀY; lời khách các lượt trước có gom, kết quả tool các lượt trước KHÔNG |

Đối chứng dương (cùng phép đo): `01/08/2026` 🟢 · `1.100.000đ` 🟢 · lượt có gọi tool 🟢.

**Vì sao "chập chờn":** cả ba phụ thuộc lựa chọn định dạng/hành vi ngẫu nhiên của model từng lượt
(chấm hay gạch, có "đ" hay không, gọi lại tool hay trả từ trí nhớ). Khớp đúng số đo cũ: lần chặn 4,1s
= lượt KHÔNG gọi tool (cơ chế #3).

## 2. VIỆC CỦA TỪNG VAI

### CODER (`tech-lead`) — ba bản vá A+B+C, diff nhỏ, tất định

- **A · Mở kênh nguồn cho tool lượt trước** — `src/agents/graph.py` (~dòng 1108, chỗ dựng `nguon_tool`/`loi_khach`):
  gom thêm `content` của mọi `ToolMessage` trong `all_messages` (lịch sử hội thoại) vào kênh nguồn,
  trích NGHIÊM kiểu JSON như `nguon_tool` hiện tại (KHÔNG cho dấu phân cách gộp số — lý do ghi ngay trong comment tại chỗ).
  *Căn cứ:* ràng buộc cứng 3 đòi truy vết tới "một kết quả tool CÓ THẬT" — không giới hạn lượt này.
  🔴 **Đ1 (BẮT BUỘC — Bảo Mật định hạng 18/08 tối, PO-agent phê chuẩn 19/08 sáng, xem
  `docs/security/2026-08-18-dinh-hang-ban-va-A-o3-toolmessage-lich-su.md` §3):** loại bỏ payload có
  `status == "error"` khỏi kênh nguồn lịch sử — nhánh error echo nguyên văn tham số model tự đặt,
  thiếu Đ1 thì số bịa lượt 1 được "rửa" thành nguồn hợp lệ cho cả hội thoại. KHÔNG gom `AIMessage`.
- **B · Siết regex trích số văn xuôi** — `src/agents/output_filter.py` (`_DAY_SO`, ~dòng 161):
  dấu phân cách chỉ hợp lệ khi mang hình dạng ngăn-hàng-nghìn (nhóm ĐÚNG 3 chữ số):
  `\d{1,3}(?:[.,\s]\d{3})+|\d{7,}`. Giữ nguyên `_TOKEN_MA` và so khớp tuyệt đối — KHÔNG nới chiều bắt bịa
  (đọc kỹ comment bẫy B↔F có sẵn trong hàm trước khi sửa).
- **C · Chẩn đoán không lưu nội dung** — khi chặn, log thêm HÌNH DẠNG dãy lạ: số lượng, độ dài từng dãy,
  có chữ cái không, có hình-dạng-ngày không, tool-payload-lượt-này có rỗng không. CẤM log nội dung
  (giữ nguyên nguyên tắc đã ghi ở call-site). Đây là mục "cần cách chẩn đoán KHÔNG lưu nội dung" bàn giao đã đòi.
- Sau vá: chạy từ HOST `pytest tests/test_invariants.py` (23/23) + `python scripts/check_contracts.py`.
- Dựng lại ảnh `fin05` **MỘT LẦN, khai trước với cả đội qua Lead** (không ai đo giữa lúc dựng).
  Sau dựng: **grep bản vá trong container** trước khi tin bất cứ kết quả gì (bài học verify-rebuild).

### QA/QC (`tester`) — cổng nghiệm thu viết TỪ ĐẶC TẢ dưới đây, KHÔNG đọc src/

Hợp đồng hành vi của O3 sau vá (viết test từ đây, tự dựng dữ liệu):
1. Reply chứa NGÀY viết bằng dấu chấm/gạch/khoảng trắng → PHẢI QUA (khi không chứa dãy lạ nào khác).
2. Reply liệt kê ≥2 số tiền hợp lệ (đều có trong tool payload) cạnh nhau, ngăn bằng `", "` → PHẢI QUA.
3. Reply nhắc lại mã giao dịch/số tiền có trong KẾT QUẢ TOOL CỦA LƯỢT TRƯỚC cùng hội thoại → PHẢI QUA.
4. **Chiều KÊU (Luật A — bắt buộc, thiếu là cổng rỗng):** số ≥7 chữ số viết LIỀN không có trong nguồn nào → PHẢI CHẶN;
   SĐT đã bị scrub khỏi tool result → PHẢI CHẶN; token chữ-số là lát cắt định danh nội bộ (`TR-…`) → PHẢI CHẶN.
5. Ca ①+④ ghép: reply vừa có ngày dấu chấm vừa có số bịa viết liền → PHẢI CHẶN (chặn vì số bịa, không phải vì ngày).

### BẢO MẬT (`security`) — một trang định hạng, TRƯỚC khi Coder land bản vá A

HAI câu cần trả lời (câu ② do Lead+Bảo Mật phát hiện 18/08 tối, PO-agent xác nhận):
① *Mở kênh nguồn O3 sang `ToolMessage` lịch sử có mở kênh RÒ mới không?*
② *Trục TOÀN VẸN (ràng buộc cứng 3): mở rộng tập `hop_le` có cho phép số model TỰ ĐẶT ở lượt N-1
(echo trong payload tool chưa scrub) trở thành "nguồn hợp lệ" ở lượt N — agent tự cấp căn cứ cho chính mình?*

🔴 **ĐÍNH CHÍNH 18/08 tối (bản đầu của brief SAI, lỗi §8 của PO-agent):** bản đầu viết *"MỌI ToolMessage
đã qua `_scrub_pii_cho_llm`"*. [ĐO] ba nguồn độc lập (Bảo Mật · Lead · PO-agent) cùng ra: **2/5 tool**
có scrub ở đường trả về (`customer_tools.py:838` lookup_transaction · `:867` get_customer_history);
**3/5 KHÔNG**: create_ticket · request_human_handoff · search_policy. Dữ kiện đúng còn lại: các
`ToolMessage` ấy dù chưa scrub thì model ĐÃ đọc trong `all_messages` — vá A không đặt dữ liệu MỚI
trước mặt model, chỉ thêm vào tập đối chiếu của O3 (nên trục ① hẹp; trục ② mới là trục nặng).

Bảo Mật kiểm độc lập cả hai trục, ghi một trang vào `docs/security/`, kết luận
CHO PHÉP / CHẶN / CHO PHÉP KÈM ĐIỀU KIỆN (điều kiện được phép nêu ở mức RÀNG BUỘC — vd giới hạn
trường/tool nào được vào kênh nguồn — thiết kế cụ thể vẫn thuộc Coder).

### REVIEW (`critic`) — sau khi Coder có diff

Đối chiếu diff với đặc tả mục 2-Coder và nguyên tắc đầu file `output_filter.py` ("hẹp mà chắc,
bỏ sót có kiểm soát — ai siết rộng phải mang số ca âm tính tới trước"). Soi riêng: bản vá B có vô tình
nới chiều bắt-bịa không; bản vá A có gom nhầm `AIMessage` (lời agent — KHÔNG phải nguồn hợp lệ) không.
Chỉ báo cáo, không ghi file.

### LEAD — điều phối + báo cáo

1. Thứ tự bắt buộc: **Bảo Mật định hạng bản vá A → Coder vá → Review soi diff → QA/QC chạy cổng → dựng ảnh MỘT LẦN → verify.**
   QA/QC viết test SONG SONG với Coder được (hai vùng ghi khác nhau) — nhưng không ai dựng ảnh giữa chừng.
2. Verify sau dựng (PO thật đã chốt mức): **1 hành trình demo + tái lập ca O3** — lặp câu
   "xem giao dịch gần đây" 3 lần cùng tài khoản USR-0145 (đúng kịch bản từng chặn 2/3). Đạt = 3/3 có câu
   trả lời thật, log không còn `output_filter_khop nhom=O3` oan. Script hành trình: `scripts/` (commit `b0865e2`).
3. **Ngân sách — ĐÍNH CHÍNH 19/08 (bản đầu ghi "~32K" là LỖI của PO-agent: gắn nhầm phần dư của
   `qwen3.7-max` đã bỏ, và tính từ 1/3 ngăn xếp):** [ĐO] 19/08, Lead đo + PO-agent kiểm lại độc lập,
   khớp từng chữ số, cộng đủ BA ngăn xếp: `qwen3.7-max` 1.027.494/1M (VƯỢT — model đã bỏ) · họ `plus`
   243.019 ⟹ **còn ~757K theo SỔ NỘI BỘ** (caveat: lượt hỏng ghi 0 nên tiêu thật cao hơn; "1M/model"
   chưa đối chiếu dashboard — A4 còn treo). Khai số lượt dự kiến TRƯỚC khi chạy verify. Vượt kế hoạch → dừng, hỏi.
4. Báo cáo về PO-agent theo chuẩn dự án: mọi phát biểu kèm `[ĐO]` + mẫu số. Câu không có số đo sẽ bị trả lại.
5. Lên `main`: Lead CHUẨN BỊ (xác nhận cổng xanh, tổng hợp bằng chứng) — quyết định merge + deploy production
   là của PO thật, KHÔNG tự làm. `main` hiện là khung mẫu trống → đây là lần thăng cấp đầu tiên của 792 commit.

## 3. BẪY — chép từ bàn giao, vấp là mất giờ

- Chạy cổng **TỪ HOST** (`docker exec … pytest` nuốt cả suite vì `.dockerignore` loại `eval/`).
- Cổng ứng dụng là **8010** sau Caddy, không phải 8000/3000.
- Sửa `.env` xong phải **RECREATE** container mới có tác dụng.
- Mọi lệnh git **có pathspec** — cây làm việc dùng chung.
- `1 failed` cổng độ phủ nhãn + các cổng plaintext đỏ là **CÓ CHỦ ĐÍCH** — cấm "sửa cho xanh".
- `eval/heldout_set.jsonl` NIÊM PHONG — không ai chạm.
- Production `app.adaptivealgo.uk` CHỈ ĐỌC với mọi phiên.
- Docker compose luôn kèm `-p fin05` (thiếu `-p` là hạ nhầm ngăn xếp khác).

## 4. ĐỊNH NGHĨA XONG (để PO thật quyết merge)

- [ ] 5/5 ca hành vi QA/QC xanh (3 ca oan QUA + 2 nhóm ca ác CHẶN) — chạy từ host
- [ ] 23/23 invariants + `check_contracts` sạch
- [ ] Bản vá xác nhận CÓ TRONG container đang chạy (grep, không suy luận)
- [ ] Verify thật: 3/3 lượt "xem giao dịch gần đây" có trả lời, 1 hành trình demo trọn vẹn
- [ ] Bảo Mật đã ký một trang bản vá A · Review không còn ý kiến chặn
- [ ] Số token đã tiêu cho verify được khai (đọc `usage.jsonl`)
