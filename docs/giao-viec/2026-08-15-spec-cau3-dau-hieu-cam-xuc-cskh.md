# ĐẶC TẢ Câu 3 (ADR-022) — dấu hiệu cảm xúc HIỂN THỊ CHO CSKH

> **PO thật ĐÃ DUYỆT 15/08 (sau khi có đặc tả này):** khung "chip vận-hành mức
> hội-thoại, KHÔNG nhãn trạng-thái-tâm-lý" (§2-§3 dưới) · ngưỡng **N=3** (cùng N
> với nút-cho-khách, câu hỏi §5 mục 2 chốt theo đề xuất "cùng N") · **CSKH THẤY**
> chip vận-hành này (không chỉ khách thấy nút). ES-02 xác nhận lại KHÔNG phủ nhóm
> tổn thương tâm lý (ADR-022 Quyết định 3, không đổi).
> **Còn treo — kỹ thuật, KHÔNG cần PO quyết lại:** §4 hỏi có cần thêm 1 trường
> envelope riêng cho kênh CSKH hay tái dùng cờ ES sẵn có — coder đề xuất khi bắt
> tay code, xếp SAU 5a core + sau QA baseline như §4 đã ghi.

## 1. Nghiên cứu ngành nói gì (nền để thiết kế đúng)

**Mô hình tâm lý được dùng thật — Valence–Arousal (Russell 1980):** cảm xúc không
phải các ô rời rạc mà là hai trục — *valence* (tích cực↔tiêu cực) và *arousal*
(cường độ/kích hoạt). Giận = valence thấp + arousal cao. "Bực âm ỉ" và "nổi khùng"
CÙNG valence nhưng KHÁC arousal. ⟹ **"cường độ leo thang" là một chiều đo có thật,
có cơ sở** — chính là thứ ES-01 (bức xúc tăng qua N lượt) mô hình hoá. Ta không bịa
ra một thang; ta đo trục arousal ở valence âm.

**Hiển thị cho nhân viên là chuẩn ngành — nhưng dạng GỢI Ý HÀNH ĐỘNG, không phải
CHẨN ĐOÁN:** tổng đài thật hiện prompt trợ giúp trên màn hình agent ("cân nhắc đồng
cảm / cân nhắc chuyển cấp") khi phát hiện căng thẳng — KHÔNG hiện nhãn "khách đang
giận". Khung là *coaching*, không phải *diagnosis*.

**Rủi ro có tài liệu (thứ khiến "đánh giá sai" thành hại thật):**
- **Dán nhãn sai theo thiên lệch:** bộ nhận cảm xúc lệch với nhóm phi-phương-Tây/thiểu
  số → phán sai một cách hệ thống; và *người ta phản ứng với cách họ BỊ nhìn nhận*.
  (Trực tiếp với ta: khách Việt; luật tất định v1 né được thiên lệch dữ liệu-huấn-luyện
  nhưng vẫn thô theo cách riêng.)
- **Sai lầm cảm xúc bị KHUẾCH ĐẠI:** trả lời vô cảm đúng lúc khách căng phá vỡ niềm tin
  ở đúng khoảnh khắc quan trọng (vd khách báo lỗi tiền giữa lúc có việc gia đình). Đây
  chính là lý do Câu 2 (KHÔNG dò khủng hoảng tâm lý) là đúng — đoán sai nhóm đó hại nhất.
- **"Chủ quyền cảm xúc":** khi máy diễn giải cảm xúc của một người *trước cả khi họ tự
  gọi tên*, có vấn đề tự chủ. ⟹ củng cố Quyết định 4 (không lưu hồ sơ cảm xúc).

**Thực hành de-escalation:** "tactical empathy" = GỌI TÊN/thừa nhận cảm xúc mà KHÔNG
chẩn đoán, không đồng ý ("em hiểu vì sao việc này khiến anh khó chịu"). Nhân viên
*thừa nhận*, không *chẩn đoán*. ⟹ dấu cho CSKH nên THÚC nhân viên áp de-escalation,
không phải NÓI cho họ "khách là X".

## 2. Nguyên tắc thiết kế (rút ra từ trên)

1. **Khung theo HÀNH ĐỘNG, không theo TRẠNG THÁI.** Hiện "Ca nên ưu tiên xử lý mềm /
   cân nhắc mời người thật" — KHÔNG hiện "Khách đang giận/tuyệt vọng". Khớp ngành
   (coaching prompt) và ràng buộc cứng 3 (không khẳng định điều không truy được).
2. **Neo vào TÍN HIỆU QUAN SÁT ĐƯỢC, không vào nội tâm suy diễn.** Tín hiệu là "N lượt
   liên tiếp nhãn tiêu cực mạnh" (đếm được) → trình bày là *sự thật về HỘI THOẠI*
   ("hội thoại leo thang qua N lượt"), KHÔNG phải *phán về TÂM TRÍ khách* ("khách đang
   căng"). Đây là chiều arousal, hợp lệ để đo, đóng khung ở mức hội-thoại không phải
   người.
3. **Hiện rõ tính KHÔNG CHẮC.** v1 là luật thô. Trình bày là gợi ý mềm ("có thể"),
   không phải phán quyết. Ngành xác nhận các tín hiệu này nhiễu.
4. **Không lịch sử, không hồ sơ.** Đã chốt (Quyết định 4): bộ đếm Redis TTL, không log
   nhãn theo từng tin. "Chủ quyền cảm xúc" củng cố điều này.
5. **Phạm vi = CHỈ khủng hoảng nghiệp vụ.** Câu 2 đã loại tổn thương tâm lý; dấu-CSKH
   thừa hưởng đúng phạm vi đó. Nghiên cứu xác nhận mạnh: nhầm hai nhóm này là kiểu lỗi
   hại nhất.
6. **Câu chữ nhãn tránh tính từ lâm sàng/cảm xúc.** Dùng ngôn ngữ vận hành.

## 3. Đề xuất cụ thể (chờ PO gật)

Dấu cho CSKH = **một chip vận hành, không phán trạng thái tâm lý**:

```
Gợi ý ưu tiên · hội thoại căng kéo dài (N lượt)   [i]
```

- `[i]` mở tooltip: "Tín hiệu tự động dựa trên diễn biến hội thoại, có thể không chính
  xác. Gợi ý cân nhắc xử lý ưu tiên hoặc mời người thật — KHÔNG phải đánh giá về khách."
- KHÔNG dùng: "giận", "bức xúc", "tuyệt vọng", "khó tính", bất kỳ tính từ về người.
- Nguồn dữ liệu: ĐÚNG bộ đếm ES-01/ES-02 đã có (không thêm phân loại mới cho CSKH).
- Không màu đỏ báo động kiểu gian lận — dùng mức "chú ý", tách thị giác khỏi FS-06.

## 4. Việc / thứ tự
- Không cần thêm trường contract nếu chỉ đọc lại cờ ES đã có trong envelope. Nếu muốn
  CSKH thấy mà KHÁCH không nhất thiết thấy nút → cần một trường envelope riêng cho kênh
  CSKH; đó là một vòng §3 nhỏ (thêm mục hieu_luc, không đụng ES core). Xác nhận sau.
- Coder KHÔNG dựng phần này tới khi PO gật hướng §3 trên. Xếp SAU 5a core + sau QA baseline.

## 5. Câu đã hỏi PO — ĐÃ CHỐT 15/08
- ~~Đồng ý khung "chip vận hành mức hội-thoại, không nhãn trạng thái người" không?~~
  → **DUYỆT**, nguyên văn khung §2-§3.
- ~~Ngưỡng hiện chip cho CSKH = cùng N=3 với nút-cho-khách, hay thấp hơn?~~ →
  **DUYỆT cùng N=3**, một nguồn sự thật, đỡ lệch (đúng đề xuất đã ghi ở đây).
