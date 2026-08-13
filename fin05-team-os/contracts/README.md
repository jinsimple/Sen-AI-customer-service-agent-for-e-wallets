# contracts/ — Nguồn sự thật duy nhất

Thư mục này là **ranh giới**, không phải tài liệu.

- *Tài liệu* mô tả cái đang có.
- *Contract* quy định cái được phép có.

Code phải khớp contract, không phải ngược lại. Test được sinh từ contract, không từ code.
Báo cáo bảo mật đối chiếu contract, không đọc code trước.

## Ai được sửa
Chỉ agent `tech-lead`, và chỉ **sau khi Bách duyệt**. Quy trình bắt buộc (`CLAUDE.md §3`):

```
1. Dừng code
2. Sửa file contract
3. /adr  — ghi quyết định, đặc biệt là phần "vì sao bác bỏ phương án kia"
4. Hỏi Bách duyệt, CHỜ trả lời
5. python scripts/check_contracts.py --update
6. Code
```

## Vì sao có thư mục này
Vì trong một đội mà mọi thành viên đều mất trí nhớ sau mỗi phiên, thứ duy nhất truyền được
thông tin là artifact chung có cơ chế phát hiện lệch. `check_contracts.py` băm từng file ở đây;
artifact hạ nguồn nào được sinh từ hash cũ sẽ bị đánh dấu stale và CI đỏ.

Không ai phải nhớ báo cho ai. Máy nhắc.

## Danh sách file

| File | Quy định | Ai đọc nhiều nhất |
|---|---|---|
| `authority-matrix.yaml` | Ai được làm gì | tech-lead, tester, security |
| `ticket-state-machine.yaml` | Vòng đời ticket, transition hợp lệ | tech-lead, tester |
| `agent-tools.yaml` | Chữ ký tool AI agent | tech-lead, tester |
| `fraud-signals.yaml` | FS-01…FS-12, ngưỡng, tầng A/B | security, tester |
| `api.openapi.yaml` | Hợp đồng API backend ↔ UI | tech-lead, tester |

> `fraud-signals.yaml` và `api.openapi.yaml` chưa có trong gói khởi tạo — hãy để `tech-lead`
> sinh chúng từ PRD §5 và từ code API hiện có trong sprint 2, theo đúng quy trình trên.

## Quy ước `invariants:`
Mỗi contract có mục `invariants:` liệt kê bất biến rút ra từ ràng buộc cứng.
`tests/test_invariants.py` đọc chính mục này — nghĩa là thêm một bất biến vào contract
sẽ tự động tạo ra một test cần thoả. Đây là cách ràng buộc nghiệp vụ đi thẳng vào CI
mà không qua khâu dịch thủ công.

## Quy ước `open_questions:`
Mọi con số chưa được chuyên gia xác nhận phải nằm trong mục này, không được lẫn vào phần
quy định như thể đã chắc chắn. Đây là danh sách bạn mang đi hỏi ZaloPay, và cũng là thứ
bảo vệ bạn ở buổi pitch: "chúng tôi biết mình chưa biết cái gì" mạnh hơn nhiều so với
một con số bịa nghe có vẻ tự tin.
