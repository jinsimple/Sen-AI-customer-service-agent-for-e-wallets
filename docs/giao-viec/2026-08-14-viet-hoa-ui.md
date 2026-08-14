# VIỆT HOÁ TOÀN BỘ CHUỖI KỸ THUẬT TRÊN UI — brief coder + QA/QC

> PO thật yêu cầu 14/08 (kèm ảnh: badge `pending_approval`, `refunded`,
> `refund_to_wallet — 6đ`, trail `get_customer_history()` + `kết quả: null`).
> Dán MỤC A cho coder, MỤC B cho QA/QC. QA bắt đầu NGAY (việc read-only);
> coder theo LUẬT PHÂN ĐỢT dưới đây.

## Nguyên tắc thiết kế — 4 luật, vi phạm là làm lại

1. **CHỈ dịch ở tầng HIỂN THỊ.** Giá trị lưu DB / API payload / contract
   (`pending_approval`, `refund_to_wallet`…) GIỮ NGUYÊN tiếng Anh — chúng bị
   CHECK constraint + INV-12 canh, đổi là vỡ contract. Không sửa bất kỳ enum
   nào ở backend.
2. **Nhãn lấy từ contract, không sáng tác.** `resolution-state-machine.yaml`
   đã có `mo_ta` tiếng Việt cho từng giá trị (action_type, status,
   hitl_status, partner_wait_status). Mapping frontend phản chiếu đúng các
   mô tả đó — contract vẫn là nguồn sự thật duy nhất. Giá trị nào contract
   chưa có mô tả (vd status giao dịch `refunded`) → coder đề xuất nhãn, PO
   duyệt danh sách trước khi merge (gửi bảng, không cần họp).
3. **Một chỗ duy nhất.** Mở rộng đúng pattern có sẵn trong
   `frontend/src/lib/types.ts` (`Record<T, string>` exhaustive — thiếu giá
   trị là TypeScript báo lỗi compile): thêm RESOLUTION_STATUS_LABEL ·
   ACTION_TYPE_LABEL · TX_STATUS_LABEL · PARTNER_WAIT_LABEL ·
   TOOL_NAME_LABEL. CẤM dịch rải rác trong từng component.
4. **KHÔNG dịch bằng chứng gốc.** Trong Investigation trail: tên tool hiển
   thị nhãn thân thiện ("Tra cứu lịch sử khách hàng") kèm tên kỹ thuật nhỏ
   bên cạnh; nhưng khối JSON kết quả tool GIỮ NGUYÊN VĂN (thu gọn được, nhãn
   "Dữ liệu gốc — đối chiếu") — đây là bằng chứng chống bịa số liệu
   (ràng buộc cứng 3), dịch nó là phá giá trị truy vết. Riêng `kết quả: null`
   → chữ người đọc được ("Bị chặn — cần OTP phiên" cho ca OTP; "Không có dữ
   liệu" cho ca khác) — chính là nợ V4.

## LUẬT PHÂN ĐỢT (theo giờ demo tối nay)

- **Còn ≥60 phút tới giờ demo:** coder làm Đợt 1 = 3 mapping xuất hiện trong
  luồng demo (RESOLUTION_STATUS_LABEL, ACTION_TYPE_LABEL, TX_STATUS_LABEL)
  áp vào TicketDetailClient + ApproveClient + dashboard, rebuild, QA nghiệm
  thu nhanh. Đợt 2 (phần còn lại theo inventory của QA) làm sau demo.
- **Còn <60 phút:** KHÔNG sửa gì trước demo. Toàn bộ làm sau demo theo
  inventory. Badge tiếng Anh xấu nhưng không sai — sửa vội mới là rủi ro.

## MỤC A — CODER

1. Thêm các mapping còn thiếu vào `lib/types.ts` theo luật 2+3. Đề xuất nhãn
   cho nhóm chưa có trong contract, ví dụ khởi điểm (PO duyệt bảng cuối):
   `refunded → Đã hoàn tiền · success → Thành công · pending → Đang xử lý ·
   failed → Thất bại`; tool: `lookup_transaction → Tra cứu giao dịch ·
   get_customer_history → Tra cứu lịch sử khách · create_ticket → Tạo hồ sơ
   khiếu nại · search_policy → Tra cứu chính sách · request_human_handoff →
   Yêu cầu gặp nhân viên`.
2. Áp mapping vào mọi điểm render theo inventory của QA (Đợt 1: 3 màn luồng
   demo trước). Nhãn kỹ thuật gốc có thể giữ dạng phụ (tooltip/chữ nhỏ) ở
   màn nội bộ CSKH/sếp — nhưng màn KHÁCH tuyệt đối không còn chuỗi kỹ thuật.
3. Trail: nhãn tool + `null` → chữ người đọc (luật 4). JSON giữ nguyên văn.
4. tsc + eslint sạch · rebuild · verify chuỗi mới trong container · commit
   main (đợt 1) — đợt 2 chờ điều phối nhánh sau demo.

## MỤC B — QA/QC

1. **NGAY (read-only, không chờ ai): INVENTORY toàn bộ.** Đi hết các màn bằng
   trình duyệt thật theo TỪNG VAI (khách: login/chat/timeline/OTP · CSKH:
   dashboard/ticket detail/live-chat/policy-lookup · sếp: approve/chi tiết/
   report/policy · partner: knowledge/upload) + các trạng thái lỗi (401, 403,
   validation). Ghi MỌI chuỗi tiếng Anh/kỹ thuật nhìn thấy vào
   `eval/viet_hoa_inventory_20260814.md`: màn × vai × chuỗi × nhãn đề xuất ×
   ưu tiên (P1 = khách thấy · P2 = staff thấy · P3 = tooltip/phụ).
   ID hệ thống (TXN-, TCK-, RES-) KHÔNG tính — giữ nguyên là đúng.
2. Sau khi coder xong từng đợt: nghiệm thu bằng chính inventory — từng dòng
   đã Việt hoá chưa, nhãn có khớp `mo_ta` contract không (đọc contract để
   đối chiếu — đúng vùng của bạn), TypeScript có exhaustive không (hỏi coder
   bằng chứng compile).
3. Regression: luồng demo D2/D4 + duyệt không vỡ vì đổi nhãn (đặc biệt các
   e2e/test đang assert theo text tiếng Anh cũ — RÀ `frontend/e2e/` xem test
   nào assert "pending_approval"… rồi cập nhật CHÍNH test đó, vùng của bạn).

## Đầu ra chờ PO duyệt

Bảng nhãn cuối (đặc biệt nhóm ngoài contract) — PO duyệt 1 lần trước khi
merge đợt 2, để giọng ngôn ngữ thống nhất với tone sản phẩm (PRD §15.2:
không thuật ngữ nghiệp vụ với khách; "tra soát"/"đối soát" chỉ dùng màn nội bộ).
