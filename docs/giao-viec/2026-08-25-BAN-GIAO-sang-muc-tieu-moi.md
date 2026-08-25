# Bàn giao — sang mục tiêu mới (test luồng thật + notification vé mới)

> Đọc hết trong 3 phút. Nguồn chi tiết: `CHECKLIST-dot-otp-truoc-token.md` (1400+ dòng),
> chỉ mở khi cần truy vết một dòng cụ thể ở đây.

## 1. Hạ tầng phải sạch trước khi test luồng thật — điều kiện tiên quyết

🔴 **4 backend đang chạy, KHÔNG cái nào đặt trần bộ nhớ.** Máy 7,75 GiB chạy 6 ngăn xếp
cùng lúc. **Đã OOM một lần giữa buổi đo 25/08, mất 4 lượt đã trả tiền, không có chứng
từ.** Đây không phải việc dọn nhà — nó là điều kiện để bước ① (test luồng thật) không
lặp lại đúng sự cố đã xảy ra. Đang chờ PO thật cho phép dọn (tắt ngăn không dùng /
đặt trần bộ nhớ cho các ngăn còn lại).

## 2. Công cụ đo đã có sẵn — dùng lại, đừng dựng từ đầu

- **Đọc hội thoại 0 token** — giải mã trực tiếp từ LangGraph checkpoint blob trong DB,
  không cần gõ lại câu để soi transcript cũ.
- **`eval/doi_soat_usage_log.py`** — đối soát sổ `usage.jsonl` phía server.
- **Bất biến kiểm tra nhanh:** `so_luot_goi_model = so_tool_call + 1` — khớp 100% trên
  hai ngăn độc lập, dùng để phát hiện log thiếu/lệch mà không cần đọc từng dòng.

## 3. Việc treo — nơi đọc tiếp

| việc | trạng thái | đọc tiếp ở đâu |
|---|---|---|
| ⑩ (bản tóm tắt 6 trường tất định) | Thiết kế đã chốt (`create_ticket` hai thì), chờ PO thật duyệt ADR-051 | `docs/DECISIONS.md` (khi land) + mục ⑩ trong CHECKLIST |
| ⑪ (cấu trúc 3 vế + góc nhìn PDPA) | HOÃN, PO thật quyết 25/08 (đổi prompt ngay trước test luồng thật là tự nhiễu buổi test) | mục ⑪ trong CHECKLIST |
| ⑬ (model có tool không gọi, báo đã tra) | Ràng buộc cứng 3 vi phạm, tái lập 2/2 + UI thật — **cơ chế vì sao model bỏ qua tool CHƯA RÕ** | mục ⑬ trong CHECKLIST |
| Khoảng trống fintech (3 câu) | Chờ PO thật quyết | `docs/2026-08-25-...` (sổ riêng, tên đầy đủ trong CHECKLIST) |

## 4. 🔴 CÁI BẪY PHẢI NHỚ — cả đội đã đo nhầm ngăn suốt nhiều giờ vì quên đúng hai chữ này

**Ngăn đúng: `fin05-dot-otp`. Địa chỉ đúng: `https://localhost:48443`.**

**PHẢI gõ `localhost` — TUYỆT ĐỐI KHÔNG dùng `127.0.0.1` hay IP khác.** Chứng chỉ TLS
cấp cho tên `localhost`; gọi bằng IP làm TLS gãy, trả về lỗi trông y hệt "ngăn đã chết"
— trong khi ngăn vẫn sống bình thường. Đây là lỗi hạ tầng nặng nhất của cả đợt, tốn
nhiều giờ mới lộ ra, và nó **sẽ lặp lại y hệt** nếu người vào sau không đọc dòng này.
