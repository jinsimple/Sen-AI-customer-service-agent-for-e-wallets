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

~~🔴 **Cả hai ca: agent tuyên bố ĐÃ TRA (kèm chi tiết cụ thể) trong khi
`tool_calls: []`** — nghi vi phạm ràng buộc cứng 3 (cấm bịa số liệu). B1 bịa
hẳn 7 số tiền "gần đúng" không có tool_result nào đứng sau; USR-0034 thật sự
CÓ 2 giao dịch 393.000đ khớp (đã xác nhận DB), lẽ ra phải tra ra và hỏi đổi
trục, không phải tuyên bố "không khớp". Xem transcript để đọc nguyên văn.~~

🔴🔴 **ĐÍNH CHÍNH [PO 25/08, tự đo DB, bằng chứng NGƯỢC LẠI] — khung "bịa hoàn
toàn"/"vi phạm ràng buộc cứng 3" Ở TRÊN SAI, giữ nguyên văn gạch ngang, không
xoá (Luật P).** PO đo trực tiếp lịch sử `USR-0034`: cả 7 số tiền agent nêu
(387/388/391/392/397/398/399) đều là **giao dịch CÓ THẬT**, và agent BỎ QUA
5 mức có thật khác (382/383/384/385/395) — một model bịa bừa "số gần 393k"
không có lý do gì loại đúng 5 mức "gần y hệt" rồi trúng đúng 7 mức thật.
Xác suất trúng 7/7 theo cách đó là không đáng kể ⟹ **7 số này đến từ một kết
quả tool CÓ THẬT**, không phải bịa từ hư không.

🔴 **Đúng chỗ hỏng: `duong=day_du` mà `usage={}` VÀ `tool_calls=[]` CÙNG RỖNG
là một MÂU THUẪN TỰ LỘ** — model chạy thật (`day_du`) thì phải có usage nào
đó, hai trường cùng rỗng nghĩa là **harness làm mất bản ghi**, đúng họ với
bug `int+str` vừa vá (một lượt tốn tiền thật, kết quả bị vứt) và với
`tool_calls: null` mà ADR-042 đã dựng để chống. **Cái rỗng là triệu chứng của
BỘ ĐO, không phải bằng chứng "agent không gọi tool".**

🟢 **Finding THẬT còn lại sau đính chính, đúng lớp kịch bản chuyên gia cảnh
báo:** agent báo *"không thấy giao dịch nào khớp đúng số tiền 393.000đ"* dù
có **hai** giao dịch 393.000đ thật (`TXN20260508000555` 08/05,
`TXN20260509000173` 09/05, cả hai `success`/`internal_wallet`). PO loại trừ
giả thuyết "giới hạn 20 giao dịch gần nhất" bằng đo trực tiếp: 20 giao dịch
gần nhất của user KHÔNG chứa 393k lẫn 7 số kia (0/7) — không phải ca
`limit=20` kịch bản chuyên gia từng cảnh báo, mà một **cửa sổ lọc khác** (chưa
xác định) đang bỏ sót giao dịch có thật. Khung đúng: *"báo KHÔNG TÌM THẤY cho
một giao dịch có thật, tuyên bố đã tra"* — lỗi im lặng ở tầng tra cứu/lọc,
KHÔNG phải bịa số liệu.

**Việc tiếp theo:** chạy lại đúng 2 ca này (đã vá harness) để xem `tool_calls`
lần này có nội dung không — nếu có, đọc được tham số gọi thật và tìm ra vì
sao 393k bị lọc mất; nếu vẫn rỗng mà `duong=day_du`, quay lại bàn "bịa" với
bằng chứng mạnh hơn. Xem cập nhật ngay dưới đây sau khi chạy lại.

## Bài học công cụ đo (Luật 7 style, ghi vào đây để không lặp lại)

Nhánh xử lý lỗi (`except Exception as e: violations = [f"LỖI CHẠY CASE: {e!r}"]`,
`run_golden_set.py`) gán `severity = "Blocker"` — **đúng lỗi Luật H đã gặp nhiều
lần trong dự án này**: in ra KẾT LUẬN ("Blocker") thay vì TRIỆU CHỨNG ("công cụ
đo không chạy được"). Đề xuất (chưa làm, ghi nợ — ngoài phạm vi khẩn của buổi
này): tách hạng `LỖI ĐO`/`KHÔNG ĐO ĐƯỢC` ra khỏi thang `Blocker/Critical/High`
trong `run_golden_set.py`, cùng tinh thần ba trạng thái `run_adversarial_set.py`
đã có (`đạt · trượt · không đo được`) — `run_golden_set.py` hiện chỉ có hai.
