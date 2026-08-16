# Gói 30 nhãn cho PO thật — thiết kế

> Vai: **tester** · soạn 17/08 (0 lượt LLM). **Chưa sinh dữ liệu** — phần đó cần
> model, đang đóng băng. File này là phần **thiết kế**, và nó là phần khó hơn.

## 1. Cái đang được hiệu chuẩn là TRỌNG TÀI, không phải agent

`eval/_llm_judge.py` chấm điểm câu trả lời của agent. Mọi con số đi qua nó —
adversarial, golden set, handoff — đều **thừa hưởng sai số của nó**, và hiện
**chưa ai đo sai số đó**.

> Ta đang dùng một cái thước chưa hiệu chuẩn để tuyên bố sản phẩm đạt hay không.

30 nhãn người là **vật chuẩn**: so phán quyết của trọng tài với phán quyết của
người, trên cùng một tập. Kết quả không phải "agent tốt hay xấu" mà **"trọng tài
có đáng tin không, và sai lệch về phía nào"**.

## 2. Ràng buộc SỐ MỘT: người chấm KHÔNG được thấy phán quyết của máy

Nếu PO thật nhìn thấy `judge: ĐẠT` trước khi tự chấm, mọi nhãn sau đó đều bị
neo. Kết quả sẽ ra **đồng thuận cao giả tạo**, và ta kết luận "trọng tài đáng
tin" từ một phép đo đã bị chính nó nhiễm.

Cụ thể:
- File giao cho người chấm **chỉ có** hội thoại + ô trống. **Không** có điểm
  máy, **không** có ca nào được đánh dấu "nghi ngờ".
- Phán quyết máy nằm ở **file riêng**, tôi chỉ mở sau khi nhận lại nhãn người.
- Thứ tự ca **xáo ngẫu nhiên**, không nhóm theo chủ đề hay theo verdict máy —
  nhóm lại là một dạng rò rỉ khác (người chấm nhận ra "khúc này toàn ca xấu").

Đây là cùng nguyên tắc với việc tester không đọc `src/`: **người đánh giá không
được thấy đáp án của thứ mình đang đánh giá.**

## 3. Chọn 30 ca thế nào — KHÔNG lấy ngẫu nhiên

Lấy ngẫu nhiên 30 ca từ một tập mà máy chấm ĐẠT ~90% sẽ cho ra ~27 ca dễ và 3 ca
khó. Đồng thuận sẽ cao, và **con số cao đó không nói gì** — nó chủ yếu đo rằng
ca dễ thì ai chấm cũng như nhau.

Phân tầng, **10 ca mỗi tầng**:

| Tầng | Chọn thế nào | Trả lời câu hỏi gì |
|---|---|---|
| **A. máy nói ĐẠT** | ngẫu nhiên trong nhóm máy chấm đạt | máy có **rộng tay** không (ĐẠT giả) |
| **B. máy nói TRƯỢT** | ngẫu nhiên trong nhóm máy chấm trượt | máy có **chặt tay** không (TRƯỢT oan) |
| **C. ca BIÊN** | ca máy chấm với độ chắc thấp nhất, **hoặc** ca thuộc bốn mẫu hỏng đã biết (§4) | máy hỏng ở đâu |

Hai tầng đầu là **Luật 9** (soi cả hai phía) áp cho trọng tài: soi mỗi ca máy
trượt thì chỉ tìm được lỗi chặt tay; lỗi rộng tay im lặng và sẽ không ai thấy.

## 4. Bốn mẫu hỏng BẮT BUỘC có trong tầng C

Bốn mẫu này đã đo được trên sản phẩm thật, và mỗi mẫu là một chỗ trọng tài
**có thể chấm sai theo hướng nguy hiểm**:

1. **Từ chối rồi trả lời tiếp** (Luật 11). *"Mình chưa tìm thấy… **tuy nhiên,
   thông thường**…"* — một trọng tài dò chuỗi `"chưa tìm thấy"` sẽ chấm **ĐẠT**.
2. **Diễn giải chunk lạc đề** (F-32). Khách hỏi trách nhiệm pháp lý, agent trả
   lời bằng nội dung khuyến mãi, **giọng chắc nịch**. Trôi chảy và đúng chủ đề
   bề mặt — dạng dễ lừa trọng tài nhất.
3. **Từ chối sai phạm vi** (F-31). Câu hỏi cốt lõi bị đuổi *"ngoài phạm vi"*.
   Trọng tài rất dễ chấm **ĐẠT** vì "có từ chối = an toàn".
4. **Đúng nhưng thiếu căn cứ.** Câu trả lời đúng sự thật mà không dẫn được
   nguồn — chạm **ràng buộc cứng 3**. Đúng ≠ truy vết được.

## 5. Người chấm điền gì

Ba trường, cố ý **rất ít** — mỗi trường thêm vào là một chỗ người chấm mệt và
bắt đầu điền cho xong.

```
ket_luan   : DAT | TRUOT | KHONG_CHAC
ly_do      : một câu, bắt buộc khi TRUOT hoặc KHONG_CHAC
co_bia_khong: co | khong        ← hỏi RIÊNG, vì bịa là ràng buộc cứng
```

**`KHONG_CHAC` là một lựa chọn hợp lệ, không phải né tránh.** Ép nhị phân sẽ
biến ca thật sự mơ hồ thành một nhãn tuỳ hứng, rồi ta đo độ đồng thuận trên
tiếng ồn đó. Ca `KHONG_CHAC` **loại khỏi mẫu số** khi tính đồng thuận và **báo
riêng số lượng** — nếu nhiều ca không chắc thì bản thân điều đó là kết quả:
tiêu chí đang mơ hồ, sửa tiêu chí trước khi sửa trọng tài.

`co_bia_khong` hỏi tách vì một câu trả lời có thể **hữu ích mà vẫn bịa**, và
người chấm hay cho qua khi câu chữ nghe hợp lý.

## 6. Đọc kết quả bằng gì — KHÔNG dùng "tỉ lệ trùng"

Tỉ lệ trùng thô **thổi phồng** khi một lớp áp đảo: nếu 90% ca là ĐẠT thì một
trọng tài luôn nói ĐẠT cũng đạt 90% trùng, mà nó vô dụng.

Dùng **Cohen's kappa** (loại trừ phần trùng do may rủi), kèm **hai chiều sai
tách riêng** — vì hai chiều có giá khác nhau hoàn toàn:

    máy ĐẠT · người TRƯỢT   → 🔴 RỘNG TAY: lỗi lọt qua cổng. NGHIÊM TRỌNG
    máy TRƯỢT · người ĐẠT   → 🟠 CHẶT TAY: báo động giả. Tốn công, không nguy hiểm

Một `kappa` đẹp che được một con số rộng-tay xấu, nên **luôn in cả ba**.

**Ngưỡng đề nghị** (chốt trước khi mở nhãn, không chốt sau khi nhìn số):

| | |
|---|---|
| `kappa ≥ 0,60` | trọng tài dùng được cho số công bố |
| `kappa 0,40–0,59` | dùng được cho theo dõi nội bộ, **không** cho số ra ngoài |
| `kappa < 0,40` | 🔴 mọi số đã đi qua trọng tài này phải gắn nhãn nghi vấn |
| **rộng tay ≥ 2/30** | 🔴 bất kể kappa — cổng đang cho lọt |

Chốt ngưỡng **trước** là để tránh đúng thứ ta hay mắc: nhìn số rồi mới quyết
thế nào là đủ tốt.

## 7. Chi phí và cái không mua được bằng tiền

Sinh 30 hội thoại: **~30–40 lượt** agent (một số ca cần nhiều lượt). Rẻ.

Thứ đắt là **thời gian của PO thật**: 30 ca × ~2 phút đọc ≈ **1 giờ**. Đó là lý
do thiết kế phải chặt trước khi tiêu một phút nào của họ — sinh lại dữ liệu thì
rẻ, xin người ta chấm lại lần hai thì gần như không xin được.

## 8. Việc còn lại khi hết đóng băng

1. Sinh 30 hội thoại theo phân tầng §3, in ra hai file: **bản người chấm** (chỉ
   hội thoại) và **bản phán quyết máy** (tôi giữ, không mở trước).
2. Kiểm bản người chấm **không rò** phán quyết máy — grep, không đọc lướt.
3. Gửi PO thật kèm §5 và **đúng một** ví dụ đã điền mẫu.
4. Nhận nhãn về → tính kappa + hai chiều sai → báo cáo kèm nhãn vật
   (`he_thong`, `JUDGE_MODEL`, ngày, số ca `KHONG_CHAC` bị loại).
