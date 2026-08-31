# Quy trình soát bản ghi thô — cổng an toàn CUỐI CÙNG trước khi phát hành

> Vai: `security`. Chuẩn bị TRƯỚC KHI có phim, để không đợi có phim mới nghĩ cách làm. Chạy sau khi
> PO thật quay xong, đối chiếu bản ghi THẬT với `docs/security/2026-08-31-soat-quay-video-demo-duoc-cam-len-hinh.md`
> (checklist cấm) + `docs/security/2026-08-31-kich-ban-quay-tung-canh.md` (8 cảnh, biết trước mỗi
> cảnh nằm ở đâu trong luồng để định vị nhanh trên timeline thật).
>
> **Đây là cổng CUỐI CÙNG** — mọi tài liệu trước đó (checklist, kịch bản) là chuẩn bị TRƯỚC khi quay;
> tài liệu này soát SAU khi quay, trên chính file video thật, không phải trên kế hoạch. Hai việc khác
> hẳn nhau: kế hoạch đúng không đảm bảo người cầm máy làm đúng 100% — cổng này giả định có thể có sai
> sót thật cần bắt, không giả định buổi quay đã hoàn hảo.

## Cách soát — xem một lượt bình thường trước, rồi soát kỹ theo bảng

1. **Lượt 1 — xem bình thường, tốc độ thật**, không tua, không dừng. Mục đích: có cảm nhận tổng thể,
   ghi lại mốc thời gian ƯỚC LƯỢNG của từng Cảnh (1-8) theo thứ tự đã biết trước từ kịch bản quay.
2. **Lượt 2 — soát TỪNG MỤC CẤM trong bảng dưới đây**, tua tới đúng mốc thời gian nghi ngờ (theo Cảnh
   tương ứng), **dừng khung hình (pause), không chỉ xem lướt qua ở tốc độ thường** — rủi ro thật nằm
   ở khung hình 1-2 giây, xem lướt bằng mắt ở tốc độ phát bình thường KHÔNG đủ để bắt được.
3. **Lượt 3 — tua CHẬM (0.25x hoặc từng khung một nếu công cụ cho phép) đúng các ĐIỂM CẮT** (nếu bản
   dựng có cắt cảnh) — kiểm tra không có nửa giây khung hình cấm lọt qua điểm nối.

## Bảng đối chiếu — mỗi mục: Ở ĐÂU · TÌM GÌ · AN TOÀN LÀ GÌ

| # | Mục cấm | Nằm ở Cảnh nào | Tìm gì khi dừng khung hình | An toàn = |
|---|---|---|---|---|
| 1 | Badge môi trường (`EnvBadge`) | **MỌI cảnh** (topbar, xuyên suốt) | Góc trên-phải mỗi khung hình: có chữ "DEVELOPMENT"/tên môi trường không; có khoảnh khắc nào con trỏ chuột dừng trên badge (tooltip có thể đã bung ra, lộ thêm backend URL + build commit) | Badge không hiện chữ môi trường (đã tắt theo xác nhận `30_login_moi.png`/`31_chat_moi.png`) **VÀ** không có khung hình nào chuột dừng trên vùng đó |
| 2 | Mã OTP hiện số (đăng nhập) | **Cảnh 2** | Đúng khoảng từ lúc panel OTP xuất hiện tới lúc bấm xác nhận — có khung hình nào camera ĐANG BẬT trong khoảng này không (đúng lỗi cần tránh: quên tắt/bật lại đúng lúc) | Cảnh này hoàn toàn KHÔNG có trong bản ghi (đã dừng ghi hình đúng khoảng, theo kịch bản) — nếu CÓ xuất hiện, dừng ngay, xem có số nào hiện trong 6 ô không |
| 3 | Mã OTP hiện số (supervisor duyệt) | **Cảnh 8**, đoạn xin OTP | Cùng cách kiểm mục 2, ở đoạn `/tickets/[id]` trước khi bấm "Xác nhận duyệt" | Cùng tiêu chí mục 2 — đây là mục ƯU TIÊN CAO NHẤT nếu chỉ soát được một chỗ (route chạm tiền nhất hệ thống) |
| 4 | Dashboard NaN | *(đã gỡ khỏi rủi ro — lỗi nằm ở bài test, không phải sản phẩm)* | Cảnh 7, nếu muốn soát cho chắc | Chip số liệu hiện số bình thường — không cần hành động nếu thấy số, đây không còn là rủi ro |
| 5 | Trích luật hết hiệu lực trên UI | *(đã sửa, commit `9d46a3c`)* | Cảnh 8, khối "Thông tin giao dịch" | Dòng đọc "Luật 91/2025/QH15, NĐ 356/2025/NĐ-CP" — nếu vẫn thấy "NĐ 13/2023" ở đây, nghĩa là bản quay dùng ảnh Docker CŨ hơn commit vá, phải dừng và báo ngay (dấu hiệu lệch băm mã) |
| 6 | DevTools/console mở lộ | Bất kỳ đâu | Có cửa sổ/panel lạ nào không phải giao diện sản phẩm xuất hiện thoáng qua không | Không có |
| 7 | Dữ liệu trông giống khách thật (nhận thức) | Cảnh 3, Cảnh 7 | Có caption/lời mở đầu "dữ liệu sinh tổng hợp" xuất hiện đủ rõ, đủ sớm trong video không — không phải mục CẤM lên hình, mà mục PHẢI CÓ | Caption/lời thoại đã xuất hiện trước khi màn hình đầu tiên có tên/SĐT hiện ra |

## Sau khi soát — kết luận, không lấp lửng

```
□ Cả 3 lượt (xem thường / dừng khung hình / tua chậm điểm cắt) đã làm đủ.
□ Với MỖI dòng trong bảng: ghi rõ AN TOÀN hay KHÔNG, kèm mốc thời gian nếu KHÔNG.
□ Nếu có bất kỳ dòng nào KHÔNG an toàn: video CHƯA được phát hành — báo Lead/PO ngay kèm mốc thời
  gian chính xác, không tự ý cắt/sửa video (ngoài vùng ghi `security`), không "để dành sửa sau".
□ Nếu cả bảng đều an toàn: ghi lại thành một dòng NIÊM trong chính tài liệu này (ngày soát, người
  soát, kết luận) — làm bằng chứng đã soát thật, không phải suy luận từ đã có checklist trước khi quay.
```

## Vì sao cần cổng này dù đã có checklist trước khi quay

Checklist trước khi quay là **kế hoạch** — nó nói người cầm máy NÊN làm gì. Cổng này soát **kết quả
thật** — con người có thể quên đúng lúc, bấm nhầm, hoặc gặp tình huống kịch bản không lường trước
(agent trả lời khác dự kiến, phải quay lại một đoạn, vô tình chồng hai lượt ghi hình). Một kế hoạch
tốt không tự động sinh ra một bản ghi tốt — đây chính là khoảng cách giữa hai thứ đó, và không ai
khác ngoài người xem lại chính file video mới lấp được khoảng cách này.
