# GIAO VIỆC — Vá Finding ① (tra cứu chính sách trả kết quả lạc đề)

> **Từ:** phiên PO · **Cho:** Lead → tech-lead (thiết kế+code) · tester (eval) · BA (gán scope) ·
> security (soát) · QA (verify) · **Ngày:** 03/09/2026
> **PO thật đã chốt 3 quyết định** (xem §5). Đây là việc THẬT, không phải hotfix 1 dòng —
> lần rush trước bằng ngưỡng đã thất bại.

## 1. Vấn đề (grounded, `STATE.md:928`)
Ô tra cứu chính sách không có cổng lọc liên quan: câu rác trả `status=found` + chunk chính sách
CÓ THẬT nhưng lạc đề. `not_found` hiện CHỈ báo khi kho RỖNG, không phải "không có tài liệu khớp".
Agent dùng CHUNG hàm (`customer_tools.py:999`) ⟹ chạm **Ràng buộc cứng #3 (cấm bịa)**.
Vị trí: `src/rag/store.py::search` (không lọc khoảng cách) · `src/rag/search.py::search_policy_text`
(chỉ `if results:`). Docstring tool tự khai `not_found`="không có tài liệu khớp" — SAI, phải sửa.

## 2. 🔴 KHÔNG lặp lại hướng ngưỡng — đã đo và BÁC
"phí liên ngân hàng" (kho chỉ có phí nội bộ ví) distance **0.9697 / 0.9059**, nằm SÂU trong vùng
lõi liên quan (0.698–0.936), 5/6 lọt. **Không ngưỡng đơn nào an toàn.** Đừng đề xuất lại ngưỡng
tương đồng đơn thuần.

## 3. Hướng giải — HAI LỚP (PO chốt làm CẢ HAI)
- **Lớp 1 — lọc theo `scope`:** tag mỗi tài liệu chính sách bằng scope giao dịch; lọc theo scope
  của khiếu nại (`Complaint.scope` đã có, `models.py:209`). Giải ca "cùng chủ đề, sai phạm vi".
- **Lớp 2 — cổng abstention:** bước trả lời CHỈ dùng chunk đã lấy; chunk không trả lời được câu
  hỏi → nói thẳng "không tìm thấy chính sách liên quan" (grounded generation, hoặc rerank-gate —
  tech-lead cân + đo). Giải ca rác hoàn toàn (lớp 1 không chặn).
- 🔴 tech-lead **ĐỀ XUẤT PHƯƠNG ÁN + KẾ HOẠCH ĐO cho PO/Lead TRƯỚC KHI CODE** (đây là vùng đã sai
  một lần — không code trước rồi mới đo).

## 4. Cổng nghiệm thu — PHẢI ăn cả hai đầu
- **Xanh:** query hợp lệ (đúng 3 scope) → trả đúng chunk + trích nguồn.
- **Đỏ:** query rác + near-miss-sai-scope → "không tìm thấy", KHÔNG bịa.
- **KHÔNG tuyên bố vá xong nếu chưa ĐO** precision + tỉ lệ abstention. "Trông ổn" ≠ đã vá.

## 5. Ba quyết định PO thật đã chốt (03/09)
1. **Làm CẢ HAI lớp** (không chỉ scope-filter).
2. **Scope: RESEARCH LẠI rồi gán cho đúng** — BA (hoặc tech-lead) đọc kho 378 chunk, gán scope
   ĐÚNG từng tài liệu; KHÔNG để bừa `unknown`, KHÔNG đoán. Đây là NỀN của lớp 1 — sai scope là
   hỏng cả lớp. `scope='unknown'` chỉ cho tài liệu thật sự trực giao mọi scope, có căn cứ.
3. **CÓ mở rộng golden set** thêm chiều policy (tester).

## 6. Đo lường — sửa lỗ hạ tầng trước
`STATE.md:949` (Finding ⑥): phao KHÔNG lưu `tool_result` ⟹ policy-lookup không đo được dù đã tốn
8,3tr token. → sửa để lưu tool_result, HOẶC đo qua HTTP `/policy-search` trực tiếp. tester xây eval
set (relevant × 3 scope + rác + near-miss), đo trước/sau + mở rộng golden set theo §5.3.

## 7. Ai làm
- **tech-lead:** thiết kế 2 lớp + migration scope + sửa docstring tool. Đề xuất trước khi code.
  Kiểm `contracts/agent-tools.yaml` — nếu `search_policy` đổi chữ ký/hành vi khai báo → quy trình
  contract (§3 hiến pháp, PO duyệt).
- **BA:** research + gán scope đúng cho kho chính sách (§5.2) — nền của lớp 1.
- **tester:** eval set + mở rộng golden set (từ spec, không đọc src).
- **security:** soát mặt injection của ① (`STATE:1514`).
- **QA:** verify trên UI thật sau khi land (câu rác → "không tìm thấy"; câu thật → đúng chunk).

## 8. Nhịp + ràng buộc
- Việc THẬT nhiều bước — KHÔNG chặn demo/quay (chỉ né ô tra cứu tới khi vá). Không rush ẩu.
- Ngân sách: đo eval tốn token (~68% trần lúc giao). Báo nếu gần trần.
- Lead điều phối theo mốc: (a) tech-lead trình phương án+kế hoạch đo → PO/Lead duyệt; (b) BA gán
  scope xong; (c) land + đo; (d) QA verify. Báo PO từng mốc.

## 9. Rủi ro liền kề — finding bảo mật riêng, phát hiện trong lúc khảo sát kho cho việc này

Trong lúc tech-lead khảo sát kho RAG `po-demo` để thiết kế Lớp 1, phát hiện `docs/STATE.md` (400
chunk, nội dung nội bộ đội) đã bị nạp vào kho chính sách qua route upload thật (`USR-PA01`,
2026-09-01 16:48:29) — SAU lần nạp kho chính thức đêm đó. Đây là finding TÁCH BIỆT khỏi Finding ①
(chất lượng RAG): route upload của `partner_admin` không kiểm duyệt NỘI DUNG ở bất kỳ tầng nào,
chỉ kiểm định dạng. Hồ sơ đầy đủ + 4 hướng vá (khuyến nghị thứ tự C→B→A):
`docs/security/2026-09-03-finding-rag-upload-khong-kiem-duyet-noi-dung.md` (Bảo mật).

Xử lý ngay: xoá `STATE.md` khỏi kho qua `delete_document()` — đã chuẩn bị lệnh, chờ tín hiệu Lead
sau khi buổi quay xong (container đang ở trạng thái đặc biệt cho quay, tránh đụng giữa chừng).
