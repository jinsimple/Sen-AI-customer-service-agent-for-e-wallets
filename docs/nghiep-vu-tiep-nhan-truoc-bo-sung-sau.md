# Tiếp nhận trước, bổ sung sau — nghiệp vụ tra soát thật

> **Câu hỏi PO đặt 24/08:** *"Theo luồng nghiệp vụ của một con người CSKH thật thì họ sẽ làm gì?"*
> — khi khách đòi *"tạo vé đi"* giữa lúc bot đang hỏi làm rõ.
>
> Tra ngày 24/08. Nguồn: TT 15/2024/TT-NHNN + hướng dẫn ngành. Không suy luận từ code.

## Câu trả lời: họ GHI NHẬN NGAY, rồi mới hỏi tiếp

Hai vế, và luật đặt chúng **nối tiếp**, không phải loại trừ:

| bước | quy định |
|---|---|
| ① **Tiếp nhận** | Tổ chức thanh toán **phải** nhận đề nghị tra soát/khiếu nại qua **tối thiểu 2 kênh**, trong đó có **tổng đài điện thoại (có ghi âm)**. Không có điều khoản nào cho phép từ chối tiếp nhận vì khách chưa đủ thông tin. |
| ② **Bổ sung** | *Sau khi* tiếp nhận qua tổng đài, tổ chức **yêu cầu khách bổ sung giấy đề nghị theo mẫu** làm **căn cứ chính thức** để xử lý. |

⟹ Cuộc gọi tổng đài **không bị chặn** vì thiếu dữ liệu. Nó được **ghi nhận trước**, hồ sơ hoàn thiện sau.

## 🔴 Vì sao thứ tự này không phải phép lịch sự — nó là đồng hồ pháp lý

> Thời hạn xử lý **không quá 30 ngày làm việc kể từ ngày TIẾP NHẬN** yêu cầu khiếu nại.

Mốc đếm là **ngày tiếp nhận**, **không phải** ngày khách cung cấp đủ thông tin.

Hệ quả trực tiếp lên thiết kế bot:

```
bot GIỮ khách trong vòng hỏi, chưa tạo vé   ⟹ đồng hồ CHƯA CHẠY  ⟹ khách THIỆT
bot tạo vé ngay khi khách yêu cầu           ⟹ đồng hồ chạy       ⟹ khách được bảo vệ
```

**Một bot hỏi thêm ba lượt trước khi mở hồ sơ đang trì hoãn mốc bảo vệ khách ba lượt.**
Với ca gian lận — nơi tiền chạy theo phút — đây không phải sự bất tiện, nó là thiệt hại.

## Ánh xạ sang sản phẩm

| nghiệp vụ thật | trong bot |
|---|---|
| tiếp nhận qua tổng đài (có ghi âm) | **tạo vé ngay** khi khách yêu cầu — mốc SLA bắt đầu |
| giấy đề nghị theo mẫu, bổ sung sau | **tiếp tục hỏi** các slot còn thiếu, cập nhật vào vé đã có |
| hồ sơ chưa đủ căn cứ vẫn tồn tại | vé ghi rõ *"chưa xác định được giao dịch"* — không bịa, đúng ràng buộc cứng 3 |

**Điểm mấu chốt:** tạo vé **không kết thúc** hội thoại. Đây chính là chỗ cả ba phương án PO-agent
trình 24/08 đều sai — cả ba đặt "tạo vé" và "hỏi tiếp" thành hai lựa chọn loại trừ nhau, trong khi
nghiệp vụ thật xếp chúng **nối tiếp**.

## Hệ quả cho test A2

Test A2 vế 2 (*"Ừ tạo đi" ⟹ phải tạo vé*) **kỳ vọng ĐÚNG** theo nghiệp vụ này.
Đỏ suốt 4 vòng ⟹ **bug sản phẩm thật**, không phải kỳ vọng sai của test.
Bốn vòng vá prompt đi đúng hướng nhưng chưa đủ mạnh: luật hiện tại đặt điều kiện
*"đã tra cứu"* trước khi được tạo — nghiệp vụ thật **không** đặt điều kiện đó lên bước tiếp nhận.

## Nguồn

- TT 15/2024/TT-NHNN — thanh toán không dùng tiền mặt (hiệu lực 01/7/2024)
- Hướng dẫn xử lý tra soát/khiếu nại tài khoản thanh toán — Hiệp hội Ngân hàng (vnba.org.vn)
- Tra ngày 24/08/2026. **Chưa đối chiếu bản gốc TT 15/2024 điều/khoản cụ thể** — cần Security
  xác nhận số điều trước khi trích vào tài liệu ra ngoài.
