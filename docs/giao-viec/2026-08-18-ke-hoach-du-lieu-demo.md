# Kế hoạch — dựng lại DỮ LIỆU DEMO cho bản `main` ổn định

> PO chốt 18/08: *"ít nhất 4 user có dữ liệu test gần thực tế nhất — từng trường, từng chỗ
> hiển thị, từng ticket, từng đoạn chat lịch sử, từng cái tra soát và từng cái label."*

## 1. Chẩn đoán — [ĐO] 18/08 trên `fin05`

```
761 vé
 28 có điều tra        3,7%      ⟹ 733 vé mở ra: dòng thời gian điều tra TRỐNG
 11 có đề xuất xử lý   1,4%      ⟹ màn DUYỆT của supervisor có 11 dòng / 761 vé
 43 có chat lịch sử    5,7%
 86 có live-chat
  1 chuyển cấp
```

**Dữ liệu hiện tại phủ tốt theo KHỐI LƯỢNG, hỏng theo CHIỀU SÂU.** 200 khách · 60.001 giao dịch ·
đủ **12/12 ô** (4 loại khiếu nại × 3 phạm vi) — nhưng gần như **không vé nào đi hết chuỗi**
`khiếu nại → vé → điều tra → đề xuất → duyệt/từ chối`.

⟹ Demo hiện tại **trình bày được danh sách, không trình bày được QUY TRÌNH** — mà quy trình HITL
mới là thứ dự án này khác biệt.

### 🔴 Nhãn CHƯA BAO GIỜ được thắp sáng

```
[ĐO] complaints.otp_disclosed = false trên CẢ 761 dòng
```
Đây là cờ *"khách lỡ tiết lộ OTP"* — một trong những tình huống **nặng nhất** của CSKH ví.
Màn hình hiển thị nó **chưa từng được ai nhìn thấy ở trạng thái bật**.

**Nguyên tắc của cả kế hoạch này** (Luật E áp cho dữ liệu, không cho test):
> **Một giá trị nhãn không có dòng nào mang nó = một trạng thái màn hình chưa ai từng thấy.**
> Nó không phải "ít gặp" — nó là **chưa kiểm**.

## 2. Bốn khách demo — mỗi người là MỘT CỘT của bảng trạng thái

Không phải "4 user cho có". Bốn hành trình **cố ý không giao nhau**, ghép lại thắp đủ mọi nhãn.

| | khách | hành trình | nhãn mà CHỈ người này thắp |
|---|---|---|---|
| **①** | **chuyển nhầm người · nội bộ ví** | đi trọn: khiếu nại → điều tra 4 bước → đề xuất → **supervisor DUYỆT** | `hitl=approved` · `action=refund_to_wallet` · `approved_by/at` · `status=resolved` |
| **②** | **tiền chưa về · từ ngân hàng** | kẹt ở đối tác | `partner_wait=waiting` **và** `overdue` · `hitl=pending` · `priority=high` |
| **③** | **trừ tiền 2 lần · ra ngân hàng** | supervisor **TỪ CHỐI**, rồi CSKH đề xuất lại | `hitl=rejected` · `reject_reason` · `rejected_by/at` · `status=rejected` · `hitl=need_more_info` |
| **④** | **nghi gian lận · lỡ tiết lộ OTP** | escalate + chuyển người thật | 🔴 `otp_disclosed=TRUE` · `priority=critical` · `fraud_signals` đủ trường · `escalations` · `human_handoff_requested=true` |

⚠️ **Ràng buộc HIẾN PHÁP cho ca ①③ — không được lách:**
`ck_resolutions_maker_checker_br12` ép **người đề xuất ≠ người duyệt**. Dữ liệu demo phải có
**ít nhất 2 tài khoản `cskh` khác nhau** và **1 `supervisor`** để chuỗi này dựng được thật.
Dựng bằng cách cho một người tự duyệt = **CSDL từ chối ghi**, và đó là điều đúng.

⚠️ **Ca ④ KHÔNG được nối cờ gian lận sang khoá ví** — RÀNG BUỘC CỨNG 5. Hai hành động độc lập.

## 3. Yêu cầu bắt buộc cho MỖI khách

1. **Chuỗi bằng chứng truy vết được**: mỗi con số trong `resolutions.rationale` phải trỏ tới một
   `tool_result_id` **có thật** qua `cited_tool_result_ids` (RÀNG BUỘC CỨNG 3). Demo mà `rationale`
   nói một con số không tra được là **demo dạy sai** chính điều sản phẩm bán.
2. **Đoạn chat lịch sử thật**: ≥ 6 lượt, tiếng Việt tự nhiên, có lượt agent **nói "không tra được"**
   — đó là hành vi đúng, và người xem demo cần thấy nó ít nhất một lần.
3. **Dòng thời gian điều tra**: ≥ 3 `investigation_logs`, mỗi dòng gắn `tool_result_id` thật.
4. **Giao dịch nền**: mỗi khiếu nại trỏ tới `transactions` có thật, số tiền/thời điểm **khớp** với
   thứ agent sẽ đọc ra. Số trên màn hình và số trong CSDL **phải là một**.

## 4. Ranh giới — thứ KHÔNG được làm

- 🚫 **Không xoá 60.001 giao dịch và 200 khách hiện có.** Agent cần quần thể lớn để việc tra cứu
  giống thật. Demo **thêm vào**, không **thay thế**.
- 🚫 **Không đụng production** `app.adaptivealgo.uk` — vùng chỉ-đọc, chưa ai đo.
- 🚫 **Không dùng dữ liệu cá nhân THẬT.** Toàn bộ là tổng hợp. Đây cũng là thứ đang được dựa vào mà
  chưa có cơ chế nào ép (§5.R ca 4) — đừng làm nó tệ hơn.
- 🚫 **Không tự nới một CHECK constraint** để nhét dữ liệu vào. Constraint chặn được = dữ liệu sai.

## 5. Thứ tự làm

```
① tech-lead  viết script sinh 4 hành trình, chạy ĐƯỢC LẶP LẠI (idempotent)
             — chạy 2 lần không tạo 8 khách
② tester     viết cổng ĐỘ PHỦ NHÃN: quét mọi CHECK constraint, mọi cột enum,
             khẳng định MỖI giá trị có ≥1 dòng demo mang nó.  Thiếu ⟹ ĐỎ.
③ PO-agent   đi 8 màn hình bằng mắt, đối chiếu từng nhãn với ảnh chụp
④ tester     nghiệm thu: chạy lại script trên CSDL sạch, dán số thật
```

🔴 **Bước ② là bước không được bỏ.** Không có nó, "phủ đủ nhãn" là một lời hứa; có nó, nó là một
cổng. Và nó **tự phát hiện nhãn mới**: thêm một giá trị vào CHECK constraint mà quên thêm dữ liệu
demo ⟹ đỏ ngay, không ai phải nhớ nhắc ai.

## 6. Nghiệm thu — dán số thật, không suy từ script

```
① 4/4 khách đi trọn chuỗi khiếu nại → vé → điều tra → đề xuất → duyệt|từ chối
② mọi giá trị enum có ≥1 dòng      (bảng đầy đủ, không phải "đã kiểm")
③ otp_disclosed=true               ≥1 dòng          ← nhãn chưa từng thắp
④ priority=critical                ≥1 dòng
⑤ partner_wait ∈ {waiting,overdue} ≥1 dòng mỗi giá trị
⑥ maker ≠ checker                  chuỗi duyệt dựng được THẬT, không lách constraint
⑦ mọi số trong rationale           tra ngược được tới tool_result có thật
```
