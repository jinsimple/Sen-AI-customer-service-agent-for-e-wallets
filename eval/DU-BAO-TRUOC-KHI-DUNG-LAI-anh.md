# Dự báo TRƯỚC khi dựng lại ảnh — `8646d9a → HEAD`

> Vai: **tester** · 17/08 · **ghi TRƯỚC khi ảnh được dựng**, để màu sau đó
> không có hai lời giải. Đỏ-vì-cổng-mới-đúng khác hẳn đỏ-vì-hồi-quy, và phân
> loại **sau** khi thấy màu là mất mốc.

## Căn cứ: `src/` đổi những gì trong dải này

    src/agents/graph.py   ·  src/api/main.py  ·  contracts/authority-matrix.yaml
    🔴 src/agents/prompt.py  KHÔNG đổi        ⟹ **A2 CHƯA LAND**
    🔴 src/agents/tools/customer_tools.py KHÔNG đổi ⟹ create_ticket không đổi

Hai dòng đó quyết định cả ba dự báo.

## ① `bc73cbe` một-lượt-một-hồ-sơ → **XANH** (1 pass · 1 XFAIL · 1 pass)

Test gọi **thẳng tool** trên `fin05do`, không qua `graph.py`. `customer_tools`
không đổi ⟹ hành vi `create_ticket` không đổi ⟹ hai lời gọi vẫn sinh **hai** vé.

    KHÔNG để lại dấu vết          → PASS   (tool vẫn không tự commit)
    hai lời gọi ⟹ ≤1 hồ sơ        → XFAIL  (chống-trùng vẫn chưa có, PO chưa chốt)
    cả hai lời gọi đều THÀNH CÔNG → PASS

**Nếu ĐỎ:** nghi `TurnGuard` hoặc chữ ký `build_customer_tools` đổi — đọc thông
điệp lỗi của test đầu tiên trước, nó là test tiên quyết.
**Nếu test giữa XPASS:** ai đó đã thêm chống-trùng. Đó là **tin tốt**, gỡ dấu
`xfail`, không phải hồi quy.

## ② `7cd8343` ngân sách token → **XANH**, in `6.565/7.550 · còn 985 (13%)`

`prompt.py` và `customer_tools.py` đều không đổi ⟹ `system 4.587` và `tool
1.978` giữ nguyên.

**Nếu ĐỎ ở `test_nen_ghi_trong_test_khop_thuc_te`:** prompt đã đổi >2% mà tôi
không biết — **đó là phát hiện**, không phải lỗi test. Biên ±2% = ±92 token
trên `system`; một khối chỉ dẫn A2 điển hình (100–300 token) **sẽ** vượt nó.
⟹ Khi A2 land thật, cổng này **được kỳ vọng đỏ**, và đỏ đúng: nó buộc người vá
cập nhật `NEN` + lý lẽ biên độ cùng lúc với prompt.

## ③ `e9d110c` A2 → 🔴 **ĐỎ**, và **KHÔNG PHẢI** hồi quy

Đây là dự báo quan trọng nhất. Lý do đỏ đã đo được **trước** khi dựng:

Nền tôi đo trên `fin05do` với chính `CAU_HOI` của bộ ca:
`Δ = 0 · tool = [get_customer_history] · agent đang HỎI THÊM`.

⟹ Trên thread mới, agent **chưa đủ tiền đề** để tới bước tạo vé — nó dừng ở
bước một. Ca A **không chạm được điều kiện nó định canh**.

    test_luot_HOI_khong_tao_ve      → XPASS ⟹ báo FAILED (xfail strict)
    test_luot_DONG_Y_thi_tao_ve     → nhiều khả năng FAILED
                                      ("lượt ĐỒNG Ý cũng KHÔNG tạo vé")
    test_khach_dong_y_TU_DAU...     → không dự báo được, thước dò chuỗi

> **Đỏ này nói bộ ca của TÔI chưa đủ, không nói sản phẩm hỏng và không nói A2
> thất bại.** A2 còn chưa land.

## 🔴 CẢNH BÁO NGÂN SÁCH — đọc trước khi chạy suite

`e9d110c` gọi **LLM thật**: 3 lượt ≈ **42K token**. Nó chỉ `skip` khi
`fin05do-backend-1` **không chạy** hoặc cờ đóng băng bật — **cả hai đều không
đúng lúc này**.

⟹ Chạy `pytest tests/` sau khi dựng sẽ **đốt ~42K** cho một bộ ca tôi vừa dự
báo là đỏ-vì-chưa-đủ. Đề nghị:

    pytest tests/ --deselect tests/test_a2_dong_y_truoc_khi_tao_ve.py
    # hoặc bật cờ đóng băng trong lượt xác minh ảnh

## Tóm tắt

| cổng | dự báo | nếu khác dự báo thì nghi gì |
|---|---|---|
| `bc73cbe` | 🟢 1p · 1 XFAIL · 1p | `TurnGuard`/chữ ký tool đổi |
| `7cd8343` | 🟢 `6.565/7.550` | prompt hoặc lược đồ đã đổi — **là phát hiện** |
| `e9d110c` | 🔴 ĐỎ | *nếu XANH* ⟹ điều kiện tiền đề đã đổi, phải đọc lại nền |
