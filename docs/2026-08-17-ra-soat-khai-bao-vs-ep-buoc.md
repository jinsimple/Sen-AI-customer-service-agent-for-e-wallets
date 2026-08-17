# Rà soát: bản khai nào mô tả CẤU TRÚC nhưng được đọc như NỘI DUNG

> Sinh ra từ câu hỏi mở của ADR-027, PO thật yêu cầu rà toàn dự án 17/08/2026.
> Phương pháp: introspect app đang chạy (`fin05-backend-1`, build `bc143c8`) + đọc contract +
> đối chiếu với `tests/test_invariants.py`. **Mọi số dưới đây đo được, không suy luận.**

## Hình dạng của lớp lỗi

Một artifact tuyên bố là nguồn sự thật về **X**, nhưng cơ chế ép buộc chỉ phủ **một tập con của X**.
Người đọc — người và máy — tin nó phủ trọn X. Không ai được báo, vì **cổng vẫn xanh**: nó xanh
đúng theo nghĩa hẹp của nó.

Khác với lỗi thường ở chỗ: **không có trạng thái đỏ nào tồn tại để mà bỏ qua.** Vì thế nó không
được phát hiện bằng sự cẩn thận, chỉ bằng cách đi hỏi *"cái này ép được tới đâu?"* cho từng bản khai.

---

## 🔴 A1 · FSM khai 8 ràng buộc, bộ kiểm ép 6 — **INV-16 và INV-17 KHÔNG có test**

`contracts/resolution-state-machine.yaml` → khối `invariants` khai 8 mục:
`INV-05 · 06 · 07 · 12 · 14 · 15 · 16 · 17`.
`tests/test_invariants.py` có test cho: `INV-00 · 01 · 02 · 03 · 04 · 05 · 06 · 07 · 08 · 09 · 10 ·
11 · 12 · 13 · 14 · 15`. **Thiếu INV-16, thiếu INV-17.**

### INV-17 — dạng nguỵ trang tệ nhất trong cả đợt rà

Chuỗi `INV-17` **có xuất hiện** trong `tests/test_invariants.py`, dòng 51:

```python
"resolution-state-machine.yaml": "a39f2b84ec5d",  # v2.5.0 — ADR-024 (... + INV-17)
```

**Nó nằm trong một dòng chú thích.** Mắt người lướt qua thấy "INV-17 có trong file test"; `grep INV-17
tests/` trả về kết quả; kết luận sai là *"đã phủ"*. Không có test nào.

Và mỉa mai nhất: chính văn bản INV-17 **tự dặn cách phải test nó**:

> *"Bài học lặp lại từ INV-15 (F-18): kiểm biểu thức, không chỉ tên constraint — một bản vá sau
> này có thể giữ tên nhưng thu hẹp biểu thức."*

Contract ghi lại bài học, giải thích vì sao phải kiểm kỹ, và **không ai viết test**. Constraint
`ck_resolutions_note_bat_buoc_khi_khac` **có thật** trong `src/db/models.py:400` — nên hôm nay hệ
thống đúng. Nhưng nó đúng **không có ai canh**: gỡ nó đi, hoặc thu hẹp biểu thức, thì 23/23 vẫn xanh.
Đúng chế độ hỏng mà INV-15 sinh ra để chống.

### INV-16 — nằm trên hai ràng buộc cứng, không ai canh

> *"Tín hiệu ES-xx KHÔNG được xuất hiện trong `complaints.fraud_signals`, KHÔNG được là đầu vào của
> `evaluate_escalation()`, và KHÔNG được trích dẫn trong `resolutions.cited_tool_result_ids`.
> Cảm xúc ĐỊNH TUYẾN, không bao giờ tham gia vào KẾT LUẬN nghiệp vụ."*
> — nguồn BR-13 (ADR-022), giữ **ràng buộc cứng 2** (AI không vượt cấp) và **3** (cấm bịa số liệu)

Ba vế, **không vế nào có test**. Test gần nhất (`test_complaint_intake.py`, `test_create_ticket.py`)
chỉ chạm mã `FS-xx`, khẳng định fraud_signals do tầng service tính — **không** khẳng định `ES-xx`
vắng mặt. Đây là hai mệnh đề khác nhau: *"tính đúng nguồn"* ≠ *"không lẫn loại tín hiệu khác"*.

Vì sao đáng lo hơn INV-17: INV-17 được DB ép (constraint có thật, chỉ thiếu người canh).
**INV-16 không có gì ép cả** — nó thuần tuý là một câu trong contract.

---

## 🟠 A2 · `agent-tools.yaml` khai `output` cho cả 5 tool — không gì so nó với thật

ADR-027 vừa vá phía **input**. Phía **output** còn nguyên hình dạng đó:

| trường khai / tool | số tool khai | có test so với app? |
|---|---|---|
| `mo_ta` | 5 | ❌ *(cố ý — ADR-027 §3 bác)* |
| `input` | 5 | ✅ *(ADR-027, đang land)* |
| `output` | 5 | ❌ **không ai kiểm** |
| `yeu_cau_otp` | 3 | ✅ INV-10 |
| `ghi_chu` | 5 | ❌ *(văn xuôi — đúng, không nên ép)* |

Cả 5 tool khai `output: status: {type: enum, values: [found, not_found, error]}`.
Không test nào đối chiếu enum đó với giá trị app thật trả. Nếu một tool thêm `multiple_matches`
(mà `lookup_transaction` **có** dùng, theo mô tả thật của nó) thì contract sai và không ai biết.

⟹ **Nghi vấn cụ thể, cần coder xác nhận:** mô tả thật của `lookup_transaction` nói rõ
`status=multiple_matches`, nhưng contract khai enum chỉ có 3 giá trị. Nếu đúng thì đây **không phải
rủi ro tiềm ẩn mà là lệch đang tồn tại**, cùng ADR-027 nên vá luôn.

---

## 🟡 A3 · `authority-matrix` khai `extra`, bộ kiểm chỉ so MỘT giá trị

`tests/test_invariants.py` khi so route:

```python
extra_live = [e for e in live[key]["extra"] if e == "require_otp_verified"]
extra_ct   = [e for e in contract[key]["extra"] if e == "require_otp_verified"]
```

Hàm thu thập **cả** `get_current_user` lẫn `require_otp_verified`, rồi **lọc bỏ** cái đầu trước khi
so. Contract khai `extra: [get_current_user]` trên 2 route (`POST /auth/logout`,
`POST /tools/lookup_transaction`) — **hai dòng khai đó không được ép bởi bất cứ gì**. Gỡ
`Depends(get_current_user)` khỏi `/auth/logout` thì cổng vẫn xanh.

Hôm nay khớp (2 khai / 2 thật). Đây là **lỗ chờ**, không phải lệch đang tồn tại.

### A3b · Và `authority-matrix` chỉ khai AI ĐƯỢC GỌI — không khai route được BẢO VỆ THẾ NÀO

Guard thật dùng trong `src/api/`: `require_role` (28) · `get_session` (28) · `get_current_user` (4) ·
`require_otp_verified` (1). Contract khai `roles` + `extra`. **Bất kỳ lớp bảo vệ nào khác — giới hạn
tần suất, kiểm quyền sở hữu bản ghi, chống lặp — đều không có chỗ trong bản khai.**

Người đọc `authority-matrix.yaml` để trả lời *"route này được bảo vệ ra sao"* sẽ nhận một câu trả lời
**đúng nhưng không đủ**, và không có dấu hiệu nào cho biết nó không đủ. Đây đúng câu hỏi security phải
trả lời hàng ngày.

---

## 🟡 A4 · `scripts/check_contracts.py` — tên đọc như "kiểm contract đúng không"

Nó băm SHA-256 file contract rồi so với băm đã đóng dấu trong các artifact và trong baseline
`.claude/state/contract-hashes.json`.

⟹ Nó phát hiện **"contract đã đổi mà artifact chưa cập nhật"**. Nó **không** phát hiện
**"contract mô tả sai thực tại"**. Xanh nghĩa là *"không ai sửa file kể từ lần đóng dấu"* —
**không** phải *"bản khai đúng"*.

Chính ADR-027 là bằng chứng: contract khai `create_ticket` 0 tham số suốt một thời gian dài,
`check_contracts.py` xanh trọn, vì **không ai sửa file**. Công cụ hoạt động đúng đặc tả của nó.
Vấn đề nằm ở cái tên và ở kỳ vọng nó tạo ra.

---

## ⚪ A5 · Hiến pháp tự khai một con số đã lệch

`CLAUDE.md:111` — *"tests/ ← 42 file test backend"*. Đếm thật: **72** file `test_*.py`.

Các số còn lại **đúng**: 33 route ✅ · 5 tool ✅ · 13 file e2e ✅ · 23 test invariant ✅
(số 23 vừa được sửa từ "19" hôm 16/08) · 27 ADR.

Vô hại về vận hành, nhưng nó nằm trong file được nạp vào **mọi phiên của mọi vai** — và là file
đặt ra chuẩn *"mọi con số phải kèm nguồn"*.

---

## Điều KHÔNG hỏng — ghi lại để khỏi rà lại

- `agent-tools.yaml` khai 4 ràng buộc (`INV-08/09/10/13`) — **cả 4 đều có test**. Đủ.
- `authority-matrix` so **route + method + roles**, có method trong khoá (`"POST /path"`) ⟹ thêm một
  method vào path cũ **KHÔNG lọt**. Đây là chỗ dễ sai mà bộ kiểm làm đúng.
- Cả hai contract lớn đều có khối `open_questions` **tự khai điều chưa chốt** (FSM 2 mục,
  agent-tools 2 mục). Đây là mặt đối lập của cả lớp lỗi trên: bản khai **tự công bố giới hạn của
  chính nó**. Nên giữ và nên nhân rộng.

---

## Đề xuất — xếp theo giá trị / công sức

| # | Việc | Vì sao | Ai |
|---|---|---|---|
| 1 | **Test cho INV-16** | Nằm trên ràng buộc cứng 2 + 3, **không có gì ép**, thuần văn bản | tester |
| 2 | **Test cho INV-17** kiểu INV-15 (kiểm **biểu thức**, không chỉ tên) | Contract tự dặn mà không ai làm | tester |
| 3 | **Cổng "mỗi INV khai trong contract phải có test mang đúng id"** | Vá **cơ chế**, không vá hai ca. Không có nó thì INV-18 lặp lại y hệt | tester + coder |
| 4 | So `output` enum app ↔ contract; kiểm nghi vấn `multiple_matches` | Cùng ADR-027, đang mở, rẻ | coder |
| 5 | Bỏ bộ lọc `extra`, so cả danh sách | Một dòng | coder+tester |
| 6 | Đổi tên `check_contracts.py` → nói đúng việc nó làm, hoặc in thẳng *"đây là kiểm LỖI THỜI, không kiểm ĐÚNG SAI"* | Cái tên là nguồn kỳ vọng sai | coder |
| 7 | Sửa `42 → 72` trong `CLAUDE.md` | Một ký tự | po |

**Đề xuất số 3 là đề xuất chính.** Sáu mục kia vá sáu cái lỗ; số 3 vá **cái sinh ra lỗ**. Bài học
lặp lại đúng của ADR-027: *sửa dữ liệu mà không sửa cơ chế phát hiện thì lần sau vẫn im lặng y hệt.*

## Câu hỏi còn để mở — không đủ dữ kiện để trả lời hôm nay

Rà này đi từ **contract → có test không**. Chiều ngược lại chưa ai đi:
**có ràng buộc nào đang được ép trong code mà KHÔNG contract nào khai không?**
Nếu có, nó cũng là thông tin chết theo chiều ngược — người đọc contract sẽ tưởng hệ thống lỏng hơn
thực tế, và bản vá "tối ưu" sẽ gỡ mất một thứ đang bảo vệ ai đó.
