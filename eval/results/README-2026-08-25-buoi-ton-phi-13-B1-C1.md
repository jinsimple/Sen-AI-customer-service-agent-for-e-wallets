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

## Lần 4 — `golden_run_20260825_042822.md` — TÁI LẬP, VẪN RỖNG, KHÔNG CÒN CRASH

Chạy lại sạch, KHÔNG crash lần này (khác Lần 2). Kết quả: `tool_calls: []`
**VẪN RỖNG cả hai ca**, `duong_theo_luot: ['day_du']` **VẪN NHƯ CŨ**. B1 lần
này KHÔNG lặp lại đúng 7 số cũ — trả lời khác (do LLM không tất định), lần
này chỉ nói "không thấy giao dịch nào khớp" rồi hỏi tên người nhận, không nêu
số nào cả.

🔴 **Đây là dữ kiện MỚI, làm yếu giả thuyết "harness làm mất bản ghi vì
crash"** (Lần 2) — lần này KHÔNG có crash nào, chạy trọn vẹn, mà `tool_calls`
vẫn rỗng. Hai khả năng còn lại, KHÔNG tự chọn giữa chúng (ngoài phạm vi đọc
được của QA/QC — cần Coder đọc `src/agents/graph.py` mới phân định được):
 (a) một lỗi ghi nhận `tool_calls` KHÁC, độc lập với bug `usage` vừa vá,
     tồn tại xuyên suốt cả hai lần chạy `day_du` của bộ ca này;
 (b) agent THẬT SỰ không gọi tool trong nhánh hội thoại này (khác giả thuyết
     "đã gọi nhưng harness làm mất" của Lần 3) — nếu đúng vậy, cùng conclusion
     "báo không thấy dù có thật" vẫn đứng, nhưng qua đường KHÁC (không tra
     thật, không phải tra-thật-rồi-lọc-sai).
Hai khả năng cho ra CÙNG một hệ quả bên ngoài (bất định số liệu không truy
được tool_result) nhưng khác nhau ở NƠI cần sửa — cần Coder xác nhận trước
khi ai chọn một trong hai.

## 🔴 ĐÍNH CHÍNH LẦN 2 [PO 25/08] — quét 149 file kết quả, phân định dứt điểm

[ĐO, quét toàn `eval/results/`]:

```
quality_run_20260814_170312   40 ca | tool_calls có: 40/40 | usage có: 40/40
tang_c_raw                      8 ca | tool_calls có:  0/8 | usage có:  8/8
golden_run 25/08 (cả 4 lần)     2 ca | tool_calls có:  0/2 | usage có:  0/2 (trước vá) → 0/2 (sau vá, usage vẫn rỗng dù đã trả tiền thật)
```

`usage={}` trên một lượt ĐÃ TRẢ TIỀN THẬT (duong=day_du, có câu trả lời) là
**bản ghi tự chứng minh nó mù** — không thể "gọi LLM thật mà usage rỗng".
⟹ **`tool_calls: []` trên đường adaptive mang ĐÚNG BẰNG KHÔNG thông tin** —
không phải "agent không gọi tool", mà "bộ ghi không ghi được".

**QUAN TRỌNG — đã tự kiểm thêm (QA/QC 25/08):** `eval/measure_quality.py`
(nguồn của `quality_run_20260814...`, đường CÓ ghi được) gọi **ĐÚNG CÙNG MỘT
HÀM** `run_case_turns_adaptive` (`eval/_harness.py`) mà `run_golden_set.py`
đang dùng — không phải hai cơ chế ghi khác nhau. Cùng code eval, một lần ghi
được (14/08) một lần không (25/08) ⟹ **loại được khả năng lỗi nằm ở
`eval/_harness.py`** — khiếm khuyết nằm ở phía TRẢ VỀ của `run_agent_turn`
(`src/agents/graph.py`), lệch đi đâu đó **giữa 14/08 và 25/08** (đúng cửa sổ
đợt "OTP trước token" — ④⑤⑦⑨⑫b đều land trong khoảng này). Việc xác định
CHÍNH XÁC thay đổi nào thuộc Coder (đọc `src/`, ngoài phạm vi QA/QC).

**② Rút lại "xác suất không đáng kể":** PO tính lại đàng hoàng — dải 380-400k
có 13 mức thật/20 mức khả dĩ (trừ 393k), chọn bừa 7 mức: `C(12,7)/C(20,7) ≈
1,0%`. Khó tin, **không phải bất khả** — và lần chạy lại (Lần 4) không lặp
lại đúng 7 số đó (mẫu n=1). Sửa lại: bằng chứng ban đầu GỢI Ý mạnh nhưng
KHÔNG CHỨNG MINH được nguồn gốc 7 số. Kết luận cuối cùng KHÔNG dựa vào phép
đếm trùng khớp đó nữa mà dựa vào bằng chứng cấu trúc (usage={} tự mâu thuẫn +
cùng hàm harness khi ghi được khi không).

**③ Khung đúng cuối cùng — hai phát hiện TÁCH RỜI, không gộp:**

| Phát hiện | Trạng thái |
|---|---|
| `CASE-KBCG-B1` khai `must_cite_trans_ids`+`edge_type: multiple_matches`, agent báo "không thấy 393k" khi có 2 giao dịch thật → **ca TRƯỢT đúng tiêu chí lõi nó sinh ra để đo** | ĐỨNG VỮNG, tái lập 2/2 |
| "Agent bịa số liệu" (nghi vi phạm ràng buộc cứng 3) | **KHÔNG kết luận được** — bộ đo mù trên đường `adaptive`, không phải agent được minh oan hay kết tội |
| Cơ chế gây mù `tool_calls`/`usage` trên đường adaptive, lệch giữa 14/08→25/08 | **CHƯA RÕ, việc của Coder** — đã loại trừ được lỗi `eval/_harness.py` |

## ⑦ + Mẫu số lưu lượng thật — 20 câu tự nhiên, và một lỗ quan sát khác hẳn

Sau khi ⑦ đạt (xem tick `[x]` trong CHECKLIST), chạy 20 câu tự nhiên NGOÀI kịch bản qua UI thật
(`frontend/e2e/diag-mau-so-luu-luong.spec.ts`, tạm, không commit) để đo phân bố `duong` trên lưu
lượng thật thay vì corpus đánh giá.

**🔴 Phát hiện: `usage.jsonl` mất bản ghi dưới tải — KHÔNG phải bug bộ ghi, là OOM hạ tầng.**

Đối chiếu hai nguồn độc lập: checkpoint LangGraph (bằng chứng hội thoại THẬT xảy ra) đếm được
**17 thread**; `usage.jsonl` chỉ có bản ghi cho **10 thread**. **7 thread (41%) tốn tiền thật mà
0 dòng log.** Xác nhận cụ thể bằng giải mã checkpoint blob (0 token thêm): thread
`USR-0145:1787633162` (mẫu "cho em hỏi chuyển tiền quốc tế được không ạ") có ĐẦY ĐỦ câu hỏi →
agent trả lời → **gọi tool thật** (`ToolMessage`, `tool_result_id: TR-2d7aeb0894fe`) — một lượt
hoàn chỉnh, tốn tiền thật — nhưng 0 dòng trong `usage.jsonl`.

**[PO 25/08] Truy gốc, loại trừ theo thứ tự:**
```
① bộ ghi hỏng?          src/observability/so_usage.py: Lock + open("a") + 1 write
                        ngắn (< PIPE_BUF, append nguyên tử theo POSIX)  →  LÀNH
② đường ra quên ghi?    run_agent_turn: 10 return, 9/9 gọi _ghi_so ngay trước
                        (cái thứ 10 nằm trong hàm con)                  →  LÀNH
③ nhiều replica?        chỉ 1 container backend                        →  LOẠI
④ /app/logs mất khi restart?  là volume riêng (fin05-dot-otp_logs_data) →  LOẠI
🔴 GỐC: fin05-dot-otp-backend-1 bị KERNEL OOM-KILL lúc 04:32 (container
  StartedAt mới hơn các container khác 37 phút, HostConfig.Memory=0 —
  không đặt trần). Máy 7,75GiB đang chạy SÁU ngăn xếp fin05 cùng lúc,
  ~3,5GiB nằm ở 5 ngăn KHÔNG AI DÙNG (po-test/fin05do/fin05/final/ttl) —
  ngăn đang làm việc thật thiếu bộ nhớ lúc tải dồn, kernel giết đúng nó.
  Lượt đang xử lý khi tiến trình chết: LLM ĐÃ TRẢ LỜI (tốn tiền) nhưng
  chưa kịp ghi sổ.
```

**Phán quyết, BA MỨC — không gộp:**
| | |
|---|---|
| ✅ Số TỪNG LƯỢT (bản ghi còn sống) | DÙNG ĐƯỢC — mất dòng ≠ sai dòng. `so_luot_goi_model = so_tool_call + 1` khít 13/13 trên dòng quan sát được |
| 🔴 PHÂN BỐ `duong` trên 20 mẫu | **KHÔNG dùng để trích %** — mất CÓ CHỌN LỌC theo tải (lượt nặng/nhiều bước dễ bị giết giữa chừng hơn) ⟹ phân bố quan sát được LỆCH VỀ PHÍA NHẸ. Báo cáo kèm caveat này, coi là **cận dưới**, không phải số thật |
| 🔴 Chi phí buổi | **7 lượt đã tốn tiền, 0 bản ghi** phải tính vào tổng chi — "tiền đã tiêu thì phải đếm, kể cả khi sổ không thấy" |

**Phân bố quan sát được (20 mẫu, cận dưới, KHÔNG phải số thật — 13 dòng `day_du` sống sót):**
`can_otp`=5 · `day_du`=13 (trong đó có tool call: 4/13) · `thu_slot`=1 · `otp_resend_thu_slot`=1.
Tổng token các dòng sống sót: 207.741. Trung bình một lượt `day_du` CÓ gọi tool: ~10.430
token/lời gọi tool (giữ nguyên số PO xác nhận, không tính lại vì mẫu đã biết lệch).

**Việc:** dừng thu mẫu số ngay khi phát hiện (đã dừng). KHÔNG sửa `src/observability/so_usage.py`
— bộ ghi lành, sửa nhầm bệnh. Việc gom/tắt 5 ngăn xếp không dùng để tránh OOM lần sau là quyết
định hạ tầng, ngoài phạm vi ghi của QA/QC — đã có PO tự nhận và ghi nợ.

## Bài học công cụ đo (Luật 7 style, ghi vào đây để không lặp lại)

Nhánh xử lý lỗi (`except Exception as e: violations = [f"LỖI CHẠY CASE: {e!r}"]`,
`run_golden_set.py`) gán `severity = "Blocker"` — **đúng lỗi Luật H đã gặp nhiều
lần trong dự án này**: in ra KẾT LUẬN ("Blocker") thay vì TRIỆU CHỨNG ("công cụ
đo không chạy được"). Đề xuất (chưa làm, ghi nợ — ngoài phạm vi khẩn của buổi
này): tách hạng `LỖI ĐO`/`KHÔNG ĐO ĐƯỢC` ra khỏi thang `Blocker/Critical/High`
trong `run_golden_set.py`, cùng tinh thần ba trạng thái `run_adversarial_set.py`
đã có (`đạt · trượt · không đo được`) — `run_golden_set.py` hiện chỉ có hai.
