# Soát "bản tóm ≠ bản đầy đủ" trên `docs/STATE.md` §0b.22 — 01/09/2026 22h

> Vai: `security`/`review` (nội dung do Review `p-226-0c` cung cấp qua tin nhắn — vai này
> không ghi repo — Lead `p-226-92` neo hộ, nguyên văn, không diễn giải thêm).
> Bối cảnh: PO tự bắt mình sa bẫy "bản tóm §0-TER (`STATE.md:68`) bỏ sót thứ bản đầy đủ
> §0b.22 nói khác" ở mục ① (RAG — hiểu nhầm "không ngưỡng" thành "cần thêm ngưỡng", trong khi
> hướng ngưỡng đơn đã bị đo-và-rút-lại từ trước, xem `STATE.md:845`). PO giao Review quét nốt
> các mục ②→⑦ xem còn chỗ nào sa bẫy tương tự không, tránh đội lặp lỗi lần hai trong đêm.

## Đã tìm — 2 mục sa đúng bẫy

### ② Rò rỉ RAM (mục ③ trong sổ tồn đọng)
- **Bản tóm** `STATE.md:68`: *"③ rò rỉ RAM (chặn bài đo 150 người)"* — đọc như một sự thật đã xác lập.
- **Bản đầy đủ** `STATE.md:118-128`: tự dán nhãn **GIẢ THUYẾT**, dòng `:128` nói thẳng *"Giữ làm
  'hướng điều tra', KHÔNG trích như dữ kiện"*. Bằng chứng không còn tái lập được (grep 16:27 →
  0 dòng), không có mốc đồng hồ tuyệt đối, không lưu log ra tệp.
- **Rủi ro nếu chỉ đọc bản tóm:** coi RAM leak là bug đã xác nhận, thiết kế vá xung quanh một
  hiện tượng chưa chắc tái lập được.
- **Việc tiếp:** không vá đêm nay (đúng, đã bị loại khỏi phạm vi 2 tiếng vì lý do khác — chưa
  tái lập được). Ai nhắc "RAM leak" như căn cứ quyết định phải trỏ về `:118-128`, không trỏ `:68`.

### ③ Xoay model dừng ở lỗi non-quota (mục ② trong sổ tồn đọng)
- **Bản tóm** `STATE.md:68`: *"② xoay model dừng ở lỗi non-quota"* — đọc như root cause đã hiểu
  rõ, chỉ cần nới điều kiện xoay.
- **Bản đầy đủ** `STATE.md:846`: để hở câu hỏi chưa giải — *"vì sao `05-17` trả 200 cho request
  tay có `tools` nhưng 400 với payload lượt 3 thật — so payload, đừng suy."*
- **Rủi ro:** vá bằng cách "nới xoay sang cả 400 khi đang xoay vì quota" giả định MỌI 400 trong
  tình huống đó là do quota — bản đầy đủ nói chưa xác nhận, phải so payload trước. Vá theo giả
  định sai có thể làm hệ thống xoay model vì lý do không phải hạn mức thật.
- **Việc tiếp:** không chạm đêm nay (đã loại vì lý do khác — gộp đổi `src/` phá khả năng quy
  trách). Ghi lại để người làm sau không vá nhanh dựa trên giả định chưa kiểm.

## Lưu ý phụ — liên quan trực tiếp đêm nay, không phải bẫy tóm/đầy đủ

**⑥ Golden set không dùng được để kiểm bản vá ①.** `STATE.md:68` ghi "golden không phủ tool
nào" (đọc: 0 coverage). `STATE.md:850` thêm chi tiết: có 9/120 ca tình cờ chạm `search_policy`,
nhưng *"phao KHÔNG lưu `tool_result`"* ⟹ không trả lời được "tra cứu có trả rác không" từ
golden, dù đã tốn 8,3 triệu token đo. (Ghi chú: việc ① đêm nay đã bị PO cắt còn nạp-kho-thôi,
nên caveat này hiện không chặn gì — giữ lại cho lần sau ai định dùng golden set kiểm RAG.)

## Đã kiểm — KHÔNG lệch, an toàn

- **④ OTP git:** `:68` khớp `:849`. Kế hoạch 2 tiếng (Lane C) còn đi SÂU hơn cả hai bản (thêm
  chặn nguồn qua `testIgnore` mà `§0b.22` không nhắc) — thực thi tốt hơn tài liệu, không phải
  thiếu sót.
- **⑤ LAN:** `:68` khớp `:848`. Câu "vá sau buổi quay" đã được kế hoạch 2 tiếng supersede tường
  minh (PO gỡ đóng băng buổi quay) — không phải mâu thuẫn ngầm.
- **⑦ dot-otp:** `:68` khớp `:852`, không lệch.

## Kết luận

3/7 mục trong sổ tồn đọng có khoảng cách bản tóm/đầy đủ đáng ghi (①②③ theo đánh số §0b.22,
① đã tự PO bắt được trước khi Review vào cuộc). 4/7 mục còn lại khớp hoặc được kế hoạch tối
nay supersede tường minh — không cần hành động thêm ngoài việc niêm lại ở đây.
