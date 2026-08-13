# Lời nhắc THU HOẠCH — dán vào chat CŨ trước khi bỏ nó

> Mục đích: các chat cũ (trước khi có `contracts/` và `docs/DECISIONS.md`) có thể chứa
> **quyết định thật** chưa được ghi vào đâu cả. Đóng chat mà không thu hoạch = mất thông
> tin thật, và vài tuần nữa sẽ có phiên Claude "tối ưu" ngược lại đúng thứ đã cân nhắc kỹ.
>
> Dán khối dưới đây vào **cuối chat cũ**, lấy kết quả, rồi mới mở chat mới.

---

Chúng ta sắp chuyển sang một cơ chế đồng bộ mới, và phiên này sẽ được thay bằng phiên mới
có đầy đủ nguồn sự thật. Trước khi dừng, tôi cần bạn **thu hoạch lại** những gì chỉ tồn
tại trong cuộc trò chuyện này.

Hãy rà lại TOÀN BỘ cuộc trò chuyện của chúng ta từ đầu, và liệt kê:

## 1. Quyết định đã chốt

Mọi lần tôi nói "ừ, chốt vậy", "làm theo cách đó", "bỏ cái kia đi"... — kể cả những lần
chốt rất ngắn gọn giữa chừng. Với mỗi quyết định, ghi theo đúng khuôn:

```
- Quyết định: <chốt cái gì>
- Ngày (nếu đoán được từ ngữ cảnh):
- Lý do chọn:
- Phương án đã BÁC BỎ và vì sao: (quan trọng nhất — nếu không có, ghi "không rõ")
- Còn hiệu lực không, hay đã bị thay bằng quyết định sau?
```

## 2. Ràng buộc nghiệp vụ tôi nêu bằng miệng

Những con số, ngưỡng, quy tắc tôi nói trong chat mà **có thể chưa nằm trong tài liệu nào**
— ví dụ ngưỡng thời gian, số lần thử lại, thứ tự ưu tiên, quy tắc đặc thù ví điện tử.

Ghi rõ cái nào bạn **chắc chắn** tôi đã nói, cái nào bạn **suy ra** — đừng trộn lẫn hai
loại đó.

## 3. Việc đang dở

Đang làm tới đâu, bước tiếp theo là gì, có gì đang chờ tôi trả lời không.

## 4. Điều bạn từng cảnh báo mà chưa được xử lý

Những chỗ bạn đã nêu nghi vấn/rủi ro nhưng tôi chưa quyết, hoặc chúng ta bỏ qua để làm
việc khác trước.

## 5. Thứ bạn KHÔNG chắc

Những điều bạn đang giả định về hệ thống mà chưa bao giờ được xác nhận bằng code hay tài
liệu. Mục này quan trọng: nó chỉ ra đúng chỗ phiên mới cần kiểm lại đầu tiên.

---

**Định dạng đầu ra:** markdown, gọn, không diễn giải dài. Không có mục nào thì ghi
"(không có)" — đừng bịa cho đủ.

**Tuyệt đối không** suy đoán để lấp chỗ trống. Nếu không nhớ rõ một chi tiết, ghi "không
chắc" thay vì đoán — thông tin sai được ghi vào ADR còn nguy hiểm hơn thông tin thiếu, vì
nó sẽ được các phiên sau tin tưởng tuyệt đối.
