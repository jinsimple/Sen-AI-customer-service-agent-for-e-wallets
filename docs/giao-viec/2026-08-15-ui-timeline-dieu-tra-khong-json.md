# UI-01 — Timeline điều tra trong ticket: bỏ JSON thô, hiển thị cho NGƯỜI đọc

> PO thật yêu cầu 15/08 (kèm screenshot): trong chi tiết ticket có **2 chỗ đang hiển thị
> định dạng JSON** — CSKH không hiểu được. Đổi sang kiểu trực quan người CSKH đọc hiểu dễ
> nhất, tránh nhầm lẫn. Hiển thị cho **cả nhân viên CSKH lẫn supervisor duyệt**.
> Vùng: `frontend/src/` — tech-lead thực thi (được ghi vùng này theo §4).

## Hiện trạng (từ screenshot PO)

Timeline "Mỗi bước: tool đã gọi, input, kết quả, ghi chú AI, thời gian" đang hiển thị:

```
get_customer_history()
input: {"amount":107000}
kết quả: null
06:58 14-08

get_customer_history()
input: {"amount":107000}
kết quả: {"user_id":"USR-0001","kyc_level"…
```

Hai chỗ JSON: **input** và **kết quả**. Tên tool cũng đang là tên hàm kỹ thuật.

## Yêu cầu hiển thị

1. **Tên tool → nhãn tiếng Việt nghiệp vụ** (một map cố định, ví dụ):
   - `get_customer_history` → "Tra lịch sử giao dịch khách hàng"
   - `lookup_transaction` → "Tra cứu giao dịch"
   - `search_policy` → "Tra cứu chính sách"
   - `create_ticket` → "Tạo hồ sơ khiếu nại"
   - `propose_resolution` → "Đề xuất hướng xử lý"
   (map đủ 5 tool trong `contracts/agent-tools.yaml` + các bước hệ thống nếu có)
2. **Input → câu/mục mô tả tiếng Việt**, format theo loại dữ liệu:
   - số tiền: `107000` → **107.000 ₫**
   - mã (USR-/TXN-/TCK-): giữ nguyên mã, có nhãn — "Khách hàng: USR-0001"
   - thời gian: định dạng VN `06:58 14/08/2026`
3. **Kết quả → bảng nhãn-giá trị hoặc câu tóm tắt**, KHÔNG ngoặc nhọn/nháy kép:
   - `null` / rỗng → **"Không tra được dữ liệu"** (kèm style nhạt — đây là kết quả thật,
     không phải lỗi hiển thị)
   - object → danh sách "Nhãn: giá trị" từng dòng, nhãn tiếng Việt
     (`kyc_level` → "Mức xác thực KYC", `status` → "Trạng thái"…)
4. **Giữ đường xem dữ liệu gốc**: nút/expander "Xem dữ liệu kỹ thuật" mở ra JSON thô —
   phục vụ audit/đối chiếu. Mặc định ĐÓNG.
5. **Cả hai vai cùng một component** — cskh và supervisor xem giống nhau (supervisor duyệt
   dựa trên đúng thứ CSKH thấy, tránh hai người nhìn hai bản khác nhau rồi cãi nhau).

## Bổ sung sau rà soát security (`7f66fb1`) — thuộc phạm vi UI-01

6. **KHÔNG thêm nút sao-chép/xuất** cho khối "ghi chú AI" (`agent_note`) và cho expander JSON.
   Lý do: `agent_note` chưa scrub/không trần/không cờ cho tới khi B3 land (S-02), và trường tự do
   chưa scrub + nút copy = bề mặt **trích xuất hàng loạt**.
7. Khi B3 land: UI hiển thị **bản đã scrub** của `agent_note`; **cấm frontend cache/nhân bản giá
   trị thô** (bản thô sống thêm một vòng đời là tái diễn hình dạng tồn dư A1-04).
8. Ghi chú ngữ nghĩa (không cần làm gì ở v1): `null` → "Không tra được dữ liệu" là ánh xạ GỘP ba
   ca (*không có bản ghi* · *tool timeout* · *tra được nhưng rỗng*). Chấp nhận ở v1; đừng ai đọc
   timeline rồi kết luận "hệ thống không có dữ liệu" khi thực tế lượt tra đã hỏng —
   `ly_do_fallback` phân biệt được nếu về sau cần tách.

## Ràng buộc CỨNG (không thoả hiệp)

- **Ràng buộc cứng 3 (cấm bịa số liệu):** đây là lớp ĐỊNH DẠNG, không phải lớp DIỄN GIẢI.
  Mọi giá trị hiển thị phải là giá trị gốc format lại — không suy ra, không làm tròn, không
  tóm tắt bằng LLM. Nhãn tiếng Việt lấy từ map tĩnh trong code, không sinh động.
- **Không làm lộ thêm dữ liệu:** giá trị đã che ở tầng dữ liệu (`****0001`, `038***`) hiển
  thị NGUYÊN TRẠNG đã che. Lớp hiển thị không được "làm đẹp" mất dấu che.
- Field không có trong map nhãn → hiển thị tên field gốc (KHÔNG giấu) — thà lộ tên kỹ thuật
  còn hơn giấu dữ liệu khỏi người duyệt.

## Nghiệm thu

- CSKH đọc một bước điều tra hiểu được: tool gì, hỏi gì, ra gì — không cần biết JSON.
- Ca `null`: hiển thị "Không tra được dữ liệu", không hiển thị chữ "null".
- Số tiền có định dạng VN ở mọi chỗ xuất hiện.
- JSON gốc vẫn truy được qua expander (audit).
- Playwright e2e (tester, sau khi land): một ticket có ≥2 bước điều tra — **HAI VẾ, cấm chỉ vế
  âm** (tester chỉ ra: assert-vắng-mặt `{"` LUÔN XANH nếu timeline rỗng/không render — đúng bẫy
  `X not in db` của S-01):
  1. Vế DƯƠNG: đúng N bước hiển thị, mỗi bước có nhãn tiếng Việt thuộc map đã biết;
  2. Vế ÂM: không còn chuỗi `{"` trong hiển thị mặc định; expander mở ra có JSON gốc.
