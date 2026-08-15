# Corpus đối chứng — 20 ghi chú CSKH SẠCH (không chứa PII)

> Vai: **security** · xuất 2026-08-15 · máy-đọc-được:
> [`corpus-ghi-chu-sach-20-ca.jsonl`](corpus-ghi-chu-sach-20-ca.jsonl)
>
> **Đây là vật đã dùng để đo con số `8/20 = 40%` chặn nhầm của S-01.**
> Xuất ra file để con số đó **tái kiểm được sau khi phiên đóng** — Luật 10:
> *bộ đo phải lưu đủ để NGƯỜI KHÁC BÁC ĐƯỢC kết luận của nó, không chỉ đủ để
> nó tự tin.*

## Dấu của lượt đo GỐC — đọc trước khi dùng

```
he_thong (lúc đo 8/20) : fd16681d8088      commit b293167
he_thong (lúc xuất file): f3193ecae0e2      commit 27843d4   ⟵ ĐÃ TRÔI
```

⚠️ **Cây `src/` đã trôi giữa lúc đo và lúc xuất** (coder đang land A1 —
`src/db/models.py` đang sửa lúc tôi xuất). Hệ quả bắt buộc:

- Cột **`ket_qua_goc`** dưới đây là nhãn của **lượt đo gốc tại
  `fd16681d8088`**, **KHÔNG phải** kết quả chạy lại hôm nay. Tôi **cố ý không
  re-run** để lấy nhãn — re-run trên cây đã trôi sẽ trộn hai hệ thống vào một
  bảng, đúng sự cố `8e46f28→6c5fff`.
- 20 câu ở cột `cau` được trích **verbatim bằng AST** từ script đo gốc (không
  chép tay, không import `src/`) ⟹ **vật** không đổi dù cây có trôi.
- Ai đo lại: đó là một **cặp MỚI**, phải đóng dấu `he_thong` riêng và so với
  `fd16681d8088` như một mốc lịch sử, không ghi đè cột `ket_qua_goc`.

## Cách dùng

Corpus này là **trục đối chứng** (Luật 2): mọi lớp che/lọc chạm `note` — và
sau này chạm ba cửa còn lại — phải chứng minh nó **không phá nội dung hợp lệ**.

- **Kỳ vọng của MỌI câu: `khong_doi`** — không một ký tự nào được đổi.
- **Ngưỡng đề nghị: `0/20`**, KHÔNG phải "thấp hơn 8" (cùng kỷ luật đã dùng
  cho over-block O1-O4: `27/96 → 0/96`, không phải "giảm đáng kể").
- 20 câu này **không chứa một mẩu PII nào**. Bất kỳ thay đổi nào = chặn nhầm.

## Bảng — 8 ca chặn nhầm ở lượt gốc được đánh dấu 🔴

| # | Câu (verbatim) | Gốc | Sau scrub tại `fd16681d8088` |
|---|---|---|---|
| GC-01 | Từ chối vì chứng từ đối tác chưa khớp, chờ ngân hàng phản hồi. | qua | — |
| GC-02 | Khách không cung cấp đủ bằng chứng giao dịch, đã hướng dẫn bổ sung. | 🔴 | `[PERSON]` không cung cấp đủ bằng chứng giao dịch, đã hướng dẫn bổ sung. |
| GC-03 | Giao dịch nằm ngoài phạm vi hoàn tiền theo chính sách hiện hành. | 🔴 | Giao dịch nằm ngoài phạm vi hoàn tiền `[PERSON]` hiện hành. |
| GC-04 | Đã đối chiếu sao kê, số tiền khớp, không có dấu hiệu bất thường. | qua | — |
| GC-05 | Chuyển đội kỹ thuật kiểm tra thêm, hẹn khách trong 48 giờ. | qua | — |
| GC-06 | Khiếu nại trùng với hồ sơ đã xử lý trước đó, đóng hồ sơ này. | qua | — |
| GC-07 | Gọi lại giúp khách vào đầu giờ chiều mai. | 🔴 | Gọi lại giúp khách vào đầu `[ORGANIZATION]` mai. |
| GC-08 | Chờ ngân hàng đối tác xác nhận, chưa đủ căn cứ quyết định. | qua | — |
| GC-09 | Đề xuất hoàn tiền chưa có căn cứ tra cứu, cần điều tra lại. | qua | — |
| GC-10 | Khách đã rút khiếu nại qua tổng đài, không cần xử lý tiếp. | 🔴 | `[LOCATION]` đã rút khiếu nại qua tổng đài, không `[PERSON]`. |
| GC-11 | Số tiền tranh chấp nhỏ hơn ngưỡng, xử lý theo luồng rút gọn. | 🔴 | Số tiền tranh chấp nhỏ hơn ngưỡng, `[PERSON]` luồng `[PERSON]`. |
| GC-12 | Hồ sơ thiếu ảnh chụp màn hình, đã yêu cầu khách gửi lại. | qua | — |
| GC-13 | Đối tác báo lỗi hệ thống phía họ, đang chờ biên bản chính thức. | qua | — |
| GC-14 | Không đủ điều kiện hoàn tiền, đã giải thích rõ cho khách. | qua | — |
| GC-15 | Cần xác minh thêm trước khi trình duyệt, chuyển lại điều tra. | 🔴 | Cần xác minh thêm `[PERSON]` duyệt, chuyển lại điều tra. |
| GC-16 | Giao dịch đã được hoàn trước đó, tránh hoàn trùng lần hai. | qua | — |
| GC-17 | Khách đồng ý phương án xử lý, chờ xác nhận bằng văn bản. | 🔴 | `[PERSON]` đồng ý phương án xử lý, chờ xác nhận bằng văn bản. |
| GC-18 | Thời hạn khiếu nại đã quá quy định, từ chối theo chính sách. | 🔴 | Thời hạn khiếu nại đã quá quy định, từ chối `[PERSON]`. |
| GC-19 | Đã kiểm tra lịch sử, không phát hiện giao dịch trùng lặp. | qua | — |
| GC-20 | Chuyển cấp trên xem xét vì vượt thẩm quyền của tôi. | qua | — |

**8/20 = 40%.** Bốn ca nặng nhất (GC-03, GC-10, GC-11, GC-18) không chỉ che dư
— chúng **xoá mất căn cứ từ chối**, tức phá đúng mục đích tồn tại của cột
`note` (ADR-019: `reject_reason='khac'` bắt buộc kèm ghi chú để người đọc lại
sau biết vì sao case bị từ chối).

## Giới hạn của corpus này — đọc trước khi dựa vào nó

Tôi tự khai để không ai dùng nó rộng hơn thứ nó chứng minh được:

1. **20 câu do tôi soạn tay**, không lấy mẫu từ ghi chú CSKH thật (chưa có).
   Nó chứng minh **tồn tại** lớp chặn nhầm và cho một tỷ lệ **trên chính tập
   này** — nó **không** phải ước lượng tỷ lệ chặn nhầm trên dữ liệu thật.
2. **Chỉ phủ nhóm B** (ghi chú thao tác của nhân viên). Nhóm A — lời khai của
   khách (`description_raw`, `messages.content`) — có **phân bố ngôn ngữ khác
   hẳn** (khẩu ngữ, sai chính tả, không dấu, xen số). Cần corpus riêng; đừng
   dùng 20 câu này để kết luận gì về nhóm A.
3. **Không có ca dương tính.** Đây là corpus **thuần đối chứng** — nó trả lời
   *"có phá nội dung hợp lệ không"*, **không** trả lời *"có che được PII
   không"*. Phải chạy **cùng** một bộ ca có PII, cấm chạy lẻ (Luật 2) — nếu
   không, bản vá "không scrub gì cả" sẽ đạt 0/20 hoàn hảo.

## Bàn giao

Giao **tester** làm hạt giống trục đối chứng. Mở rộng thì **thêm ca, đừng sửa
20 ca này** — sửa là con số `8/20` mất mốc so sánh. Nếu cần biến thể (không
dấu, khẩu ngữ, viết tắt), đặt ID mới (`GC-21`…) và ghi rõ chúng **không** thuộc
tập đã đo `fd16681d8088`.
