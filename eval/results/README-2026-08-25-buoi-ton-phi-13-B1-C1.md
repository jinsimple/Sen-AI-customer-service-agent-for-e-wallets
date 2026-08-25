# ⑬-B1/C1 — buổi tốn phí 25/08, ba lần chạy, đọc theo THỨ TỰ THẬT

> Niêm tại chỗ, không xoá — cả ba lần chạy đều tốn tiền thật, kể cả hai lần đầu
> không thu được dữ liệu nào.

## Lần 1 — `golden_run_20260825_041609.md` — 🔴 KHÔNG PHẢI FINDING SẢN PHẨM

`0/2 Blocker`, nhưng đọc bảng trực tiếp SẼ SAI: cả hai ca ghi `Reply: ''`,
`Tool đã gọi: (không)`, vi phạm `LỖI CHẠY CASE: ...` — vì `FIN05_CHO_PHEP_GOI_RA_NGOAI`
chưa bật, lượt gọi ra ngoài bị **chặn ở tầng transport TRƯỚC khi tới model**.
**Không tốn tiền** (chưa ra khỏi máy) — an toàn.

## Lần 2 — `golden_run_20260825_041709.md` — 🔴 LỖI ĐO, ĐÃ TỐN TIỀN, 0 DỮ LIỆU

`0/2 Blocker`, `LỖI CHẠY CASE: TypeError("unsupported operand type(s) for +: 'int' and 'str'")`.

**Đây KHÔNG phải phát hiện sản phẩm — là công cụ đo vỡ.** [PO 25/08, truy gốc]:
`src/agents/graph.py:429` — `usage["suy_luan_gui"]` là khoá DUY NHẤT trong
`usage` mang kiểu chuỗi (chẩn đoán suy luận), mười khoá còn lại đều số.
`eval/_harness.py::_add_usage`/`run_case_adversary` cộng dồn MÙ mọi khoá
(`all_usage[k] = all_usage.get(k, 0) + v`) — vỡ ngay khi gặp khoá không phải số.

🔴 **Model ĐÃ CHẠY THẬT trước khi harness vỡ** (thấy `model_rotated` in ra ngay
trước traceback) — nghĩa là **tiền đã tốn, kết quả bị vứt, không triệu chứng
gì cho người đọc báo cáo** ngoài một dòng `Blocker` trông như phát hiện. Đúng
nguyên văn PO 25/08: *"rò rỉ ngân sách không có triệu chứng"*. Bug này **có từ
trước đợt** (không phải do đợt "OTP trước token" gây ra), chỉ lộ ra khi
`suy_luan_gui` xuất hiện trong `usage` — sẽ lộ lại ở bất kỳ khoá không-số nào
thêm vào `usage` sau này nếu không vá.

**Đã vá** (`eval/_harness.py`, cùng commit đợt này): chỉ cộng dồn khoá kiểu số;
khoá khác giữ giá trị MỚI NHẤT (đúng ngữ nghĩa "trạng thái hiện tại", không
phải "tổng cộng dồn").

**Chi phí phải tính vào tổng buổi:** 2 lượt gọi model thật, 0 dữ liệu thu được.
Không được trừ khỏi tổng chỉ vì "ca đỏ" — tiền đã tốn thật.

## Lần 3 — `golden_run_20260825_042017.md` — ✅ ĐÃ VÁ, CÓ DỮ LIỆU THẬT

`0/2 Blocker/High` — lần NÀY là phát hiện sản phẩm thật, không phải lỗi đo.
Transcript đầy đủ: `golden_run_20260825_042017_transcript_day_du.md` (raw.json
gitignored, không giữ lâu dài).

🔴 **Cả hai ca: agent tuyên bố ĐÃ TRA (kèm chi tiết cụ thể) trong khi
`tool_calls: []`** — nghi vi phạm ràng buộc cứng 3 (cấm bịa số liệu). B1 bịa
hẳn 7 số tiền "gần đúng" không có tool_result nào đứng sau; USR-0034 thật sự
CÓ 2 giao dịch 393.000đ khớp (đã xác nhận DB), lẽ ra phải tra ra và hỏi đổi
trục, không phải tuyên bố "không khớp". Xem transcript để đọc nguyên văn.

## Bài học công cụ đo (Luật 7 style, ghi vào đây để không lặp lại)

Nhánh xử lý lỗi (`except Exception as e: violations = [f"LỖI CHẠY CASE: {e!r}"]`,
`run_golden_set.py`) gán `severity = "Blocker"` — **đúng lỗi Luật H đã gặp nhiều
lần trong dự án này**: in ra KẾT LUẬN ("Blocker") thay vì TRIỆU CHỨNG ("công cụ
đo không chạy được"). Đề xuất (chưa làm, ghi nợ — ngoài phạm vi khẩn của buổi
này): tách hạng `LỖI ĐO`/`KHÔNG ĐO ĐƯỢC` ra khỏi thang `Blocker/Critical/High`
trong `run_golden_set.py`, cùng tinh thần ba trạng thái `run_adversarial_set.py`
đã có (`đạt · trượt · không đo được`) — `run_golden_set.py` hiện chỉ có hai.
