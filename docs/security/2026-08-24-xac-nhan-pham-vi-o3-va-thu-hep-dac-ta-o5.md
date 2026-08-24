# Xác nhận phạm vi O3 thật (đọc mã + chạy thật, không tin suy luận từ 1 ca) — thu hẹp đặc tả O5

> Nối tiếp câu hỏi PO-agent chuyển từ Tester: O3 có thật sự đã tổng quát hoá so-giá-trị sang mọi mã
> dạng chữ+số không, hay chỉ tình cờ bắt được ca siêu-chuỗi. Đã đọc `_TOKEN_MA`/`_cac_day_so`/
> `_khop_o3` (`output_filter.py`) và **chạy thật** `loc_dau_ra()` (không suy luận tĩnh) để xác nhận.

## Kết luận ngắn: đúng MỘT PHẦN — tổng quát hoá có thật, nhưng có một ngưỡng độ dài Tester's fixture đang che khuất

**[ĐO — đọc mã, xác nhận cơ chế]** `_TOKEN_MA = re.compile(r"[A-Za-z0-9]{7,}")` — mọi token
chữ+số LIỀN (không dấu phân cách) **≥7 ký tự** và có ít nhất 1 chữ số được đưa vào tập so sánh của
O3, không giới hạn riêng cho mã giao dịch. `_khop_o3` so **GIÁ TRỊ** token trong `reply` với tập
`hop_le` (dựng từ `nguon`+lời khách) — khớp giá trị không có trong `hop_le` ⟹ bắt. **Đây đúng là cơ
chế TỔNG QUÁT, không phải luật riêng cho tiền/mã giao dịch** — Tester nói đúng phần này.

**[ĐO — chạy thật, phát hiện Tester's fixture không lộ ra] Ngưỡng 7 ký tự làm một trong ba ca của
Tester KHÔNG ĐƯỢC O3 bắt, khác dự đoán:**

```python
>>> loc_dau_ra("Mình đã tạo hồ sơ khiếu nại cho bạn, mã KN-99999 nhé.",
...            nguon='{"tool":"create_ticket","status":"success","ticket_id":"KN-A1B2C3",...}')
(reply KHÔNG đổi, nhom=[])
```

**Lý do — cả hai token đều DƯỚI ngưỡng 7:** `_MA_THAT = "KN-A1B2C3"` Tester dùng làm mã thật có
phần hậu tố **6 ký tự** (`A1B2C3`) — dưới ngưỡng `_TOKEN_MA`, KHÔNG BAO GIỜ vào `hop_le` dù có mặt
trong `nguon`. Mã bịa `"KN-99999"` có phần số **5 chữ số** — cũng dưới ngưỡng. Cả hai token đều
"tàng hình" với O3 vì quá ngắn, không phải vì O3 không so giá trị.

**Vì sao ca "siêu chuỗi" (`KN-A1B2C399`, Tester đã đo, ĐÚNG là bị O3 bắt) khác ca trên:** hậu tố
bịa `A1B2C399` dài **8 ký tự** — vượt ngưỡng 7, vào diện so sánh, không khớp gì trong `hop_le`
(vì mã thật 6-ký-tự cũng chưa từng vào `hop_le`) ⟹ bắt. **Cùng cơ chế, khác ở việc CHUỖI BỊA đủ dài
để bị soi, không phải vì O3 "nhận ra nó là siêu chuỗi của mã thật".**

**[ĐO] Mã ticket THẬT của hệ thống dài hơn nhiều fixture của Tester:** `src/tools/base.py::new_id()`
→ `f"{prefix}-{uuid.uuid4().hex[:12]}"` — hậu tố **12 ký tự hex**, luôn vượt xa ngưỡng 7. **Với độ
dài THẬT, cả ba ca của Tester (siêu chuỗi, sai giá trị, đúng giá trị) đều sẽ vào diện so sánh của
O3** — nhưng đây là **suy luận từ độ dài**, chưa chạy thật với fixture 12-ký-tự để xác nhận. Đề
nghị Tester đổi `_MA_THAT` sang dạng thật (`"KN-" + uuid.uuid4().hex[:12]`) và chạy lại đúng 3 ca
trong `_CA_CHIEU_BAT` trước khi kết luận chắc "O3 đã phủ hết case sai-giá-trị" — hiện tại chỉ MỘT
trong ba ca (siêu chuỗi) được xác nhận thật, ca sai-giá-trị vừa đo XÁC NHẬN KHÔNG bị bắt ở độ dài
fixture hiện có.

## Hệ quả cho đặc tả O5 — thu hẹp đúng như PO-agent/Tester đề xuất, có điều kiện

**Đồng ý thu hẹp:** O5 **không cần tái phát minh so-giá-trị cho mã ticket** — với độ dài THẬT
(12 ký tự hex), cơ chế tổng quát của O3 (đã xác nhận đúng nguyên tắc, dù chưa đo hết ở độ dài thật)
đã đủ cho lớp "có nêu mã nhưng mã sai/bịa". O5 chỉ cần còn lại đúng MỘT lớp:

> **Trigger:** khớp từ vựng hoàn tất (`đã`/`vừa` + `tạo`/`mở`/`ghi nhận` + `hồ sơ`/`vé`/`ticket`/
> `khiếu nại`, tái dùng 3 bẫy đã ghi trong đặc tả gốc) **VÀ** `reply` **KHÔNG chứa token nào ≥7 ký
> tự khớp định dạng mã** (tức `_cac_day_so(reply)` rỗng đối với phần mã — không có gì để O3 so).

**Không cần đối chiếu `nguon` bên trong O5** cho đúng lớp còn lại này — vì (đã xác nhận với PO-agent
lối (i) đã chọn: sửa docstring `create_ticket` bắt buộc nêu mã, đồng bộ với `request_human_handoff`)
**MỘT câu hoàn tất hợp lệ, theo đúng chính sách ĐÃ CHỌN, LUÔN phải kèm mã.** Vắng mã + khớp từ vựng
hoàn tất ⟹ luôn sai theo đúng chính sách, bất kể `nguon` có tool result thành công hay không — đơn
giản hơn thiết kế ban đầu của tôi (từng đề xuất phải đối chiếu `nguon`).

**[ĐO] Xác nhận docstring `create_ticket` CHƯA cập nhật tại thời điểm đọc (24/08, cùng lượt này)** —
`customer_tools.py:916-917` vẫn là *"đã tạo hồ sơ, CSKH sẽ tiếp nhận"*, chưa có yêu cầu nêu mã. Bản
vá đã giao Coder theo tin trước, chưa land lúc tôi đọc. `test_o5_thanh_cong_khong_neu_ma_CHUA_CHOT`
của Tester (SKIP, chờ chốt lối i/ii) **đúng đắn giữ nguyên trạng thái chờ** cho tới khi bản vá đó
land — sau khi land, ca đó có thể ĐÓNG theo hướng "luôn phải chặn khi không có mã", không cần giữ
CHUA_CHOT nữa.

## Đề nghị cụ thể cho Tester/Coder

1. Đổi `_MA_THAT` trong test sang độ dài thật (12 hex) — chạy lại 3 ca `_CA_CHIEU_BAT` để xác nhận
   thật (không suy luận) rằng O3 phủ đủ cả ba, đặc biệt ca sai-giá-trị vừa đo KHÔNG được bắt ở độ
   dài hiện tại của fixture.
2. Thu hẹp O5 theo đúng một lớp còn lại (từ vựng hoàn tất + KHÔNG có token mã nào ≥7 ký tự trong
   reply) — không cần logic đối chiếu `nguon` bên trong O5.
3. Chờ bản vá docstring `create_ticket` (lối i, đã giao Coder) land trước khi đóng
   `test_o5_thanh_cong_khong_neu_ma_CHUA_CHOT` — khi đó ca này chuyển thành PHẢI CHẶN, không còn
   "chưa chốt".
4. Câu hỏi hướng-khách (§4 đặc tả gốc) — giữ nguyên cách Tester đã làm (in kết quả, không assert),
   chưa có dữ kiện mới để chốt ở đây.

Không sửa `src/`/`tests/` — đây là xác nhận + thu hẹp đặc tả, việc sửa test/code thuộc Tester/Coder.
