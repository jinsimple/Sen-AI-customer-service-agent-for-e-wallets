# Biên bản nghiệm thu — A1 · A2 · S-03 · F-28

> Vai: **security** · 2026-08-15 · probe độc lập theo điều kiện đóng của
> PO-agent (*coder tự nghiệm thu là CẦN, KHÔNG BAO GIỜ ĐỦ* — luật F-23).
> Đặc tả probe: `2026-08-15-bo-probe-nghiem-thu-4-ban-va.md`.
>
> **NHÃN PHÉP ĐO = commit `cf98ef8`** (coder land tới `cc07dd3`; `cf98ef8` là
> commit docs của tôi ngay trên đó, `src/` **byte-identical**).
> ⚠️ **Cố ý KHÔNG dùng `he_thong` làm nhãn** — tech-lead chỉ ra `he_thong` băm
> `src/**/*.py` nên **không phủ `scripts/` và `migrations/`**, mà lô này sửa cả
> hai. Dấu kẹp hai đầu vẫn chạy và **không lệch** (`42de64348b9f` trước = sau),
> nhưng nhãn chính thức là SHA.

## Phán quyết

| Bản vá | Kết quả | Ghi chú |
|---|---|---|
| **A1** mã hoá `description_raw` | ✅ **ĐẠT** | kèm một tồn dư đã ghi nhận, xem dưới |
| **A2** trần độ dài | ✅ **ĐẠT** | chặn ở tầng service, KHÔNG rơi xuống CHECK |
| **S-03** scrub chuỗi lỗi | ✅ **ĐẠT — trên Postgres THẬT** | đóng khoảng trống coder tự khai |
| **F-28** mở động từ tier-1 EN | ✅ **ĐẠT** | 8/8 · 0/7 chặn nhầm · FP 0/1814 |

---

## A1 — mã hoá at-rest `complaints.description_raw`

**Probe BẰNG BYTE** (SQL thô vòng qua type decorator — cách DUY NHẤT biết
`EncryptedText` chạy thật, không phải một dòng khai kiểu):

```
byte thô trong DB : 'gAAAAABqgDuMcO2DE167fmG-jtCnvN4Q_VY_nToeB97gH0JGfNf8j6Wwkf7my7EFF2GH…'
0912345678 · 88000000000194 · Trần Văn Bách  -> KHÔNG có trong plaintext
round-trip qua ORM -> đúng nguyên văn
ca biên: tiếng Việt đủ dấu ✓ · emoji 😀🔥 + dấu ✓ · 1.999 ký tự ✓
```

### ⚠️ Tồn dư A1-04 — hàng CŨ nằm plaintext VĨNH VIỄN, và đó là quyết định chờ PO

```
hàng ghi trước migration, đọc qua ORM -> 'MO TA CU CHUA MA HOA 0912345678'
```

Đọc được, qua đường fallback `InvalidToken`. **Đây KHÔNG phải lỗi của bản vá** —
tech-lead đã ghi minh thị vào docstring `models.py`: *hàng ghi trước 2026-08-15
nằm plaintext vĩnh viễn trên đĩa; "đọc được" ≠ "được mã hoá at-rest"; chấp nhận
hôm nay vì seed/test + pilot hoãn; **backfill là quyết định RIÊNG phải ra trước
khi mở pilot**.*

**Tôi xác nhận cách xử lý này đúng** (quyết định ghi ra, không phải hệ quả im
lặng) và **ký A1 ĐẠT**, nhưng gắn kèm điều kiện:

> 🔴 **A1 chỉ bảo vệ dữ liệu ghi TỪ `cc07dd3` trở đi.** Trước khi mở pilot với
> người thật, PO phải ra quyết định backfill — nếu không, dữ liệu cũ vẫn là
> plaintext trên đĩa và **A1 không phủ nó**. Đây là thứ test DB-sạch không bao
> giờ lộ ra.

## A2 — trần độ dài

```
2.000 ký tự            -> NHẬN
2.001 ký tự            -> TỪ CHỐI  (ValueError)          ← không phải IntegrityError
2.000 ký tự tiếng Việt -> NHẬN     (6.000 byte UTF-8)    ← ca A2-05
đường AGENT 20.000 ký tự -> TỪ CHỐI (ValueError)         ← ca A2-06
```

**A2-06 — câu hỏi của tôi được trả lời, và trả lời đúng.** Cả hai mép và cả
đường agent đều ném **`ValueError` ở tầng service**, KHÔNG phải `IntegrityError`
từ CHECK. ⟹ nguyên tắc *"CHECK là lưới CUỐI, không được là lưới DUY NHẤT của
bất kỳ đường nào"* **được thoả**, và không có đường nào rơi vào hình dạng F-21
(ràng buộc DB nổ thành 500 cho khách).

Tech-lead giải thích cơ chế: trần đặt ở `create_ticket_with_fraud_check` —
điểm chặn duy nhất phủ cả ba đường (REST · agent · `flag_human_handoff`).

**Bound `12.000` — đính chính số của tôi.** Tôi tính worst case 3 byte/ký tự
→ 8.100. Tech-lead chỉ ra thiếu một trục: **emoji 4 byte → 10.764** ở đúng
2.000 ký tự. Tôi đã đo lại và **họ đúng**; cửa sổ hợp lệ thật là
**[10.764 … 26.764]** (mép trên: còn phải chặn được flood 20K ASCII = 26.764).
`12.000` nằm trong cửa sổ; **`40.000` mà tôi từng đề xuất thì KHÔNG** — nó để
lọt đúng flood 20K ASCII. Khuyến nghị (b) của tôi ở phản biện ADR-025 **sai ở
mép trên**, tech-lead bắt được.

## S-03 — scrub chuỗi lỗi vào span

**Đóng khoảng trống tech-lead TỰ KHAI** (*"probe của tôi tự dựng chuỗi lỗi kiểu
Postgres, không phải lấy TỪ Postgres"*). Tôi lấy lỗi **THẬT** từ container
`fin05-postgres-1` rồi đẩy qua **đúng đường span của sản phẩm**
(`OTelTracingCallbackHandler._end_span` + `InMemorySpanExporter`):

```
Lỗi THẬT từ Postgres:
  ERROR:  duplicate key value violates unique constraint "probe_s03_real_phone_key"
  DETAIL:  Key (phone)=(0912345678) already exists.

Span sau khi qua _end_span:
  status.description: '…[ORGANIZATION]:  Key (phone)=[PHONE_NUMBER/VN_PHONE_NUMBER/
                       VN_ID_NUMBER]) already exists.'
  SĐT · email · tên   -> KHÔNG có trong span
  exception.stacktrace thô -> không còn
  'unique constraint' -> CÒN GIỮ (vẫn debug được)
```

⟹ **S-03 ĐẠT end-to-end trên Postgres thật**, không chỉ trên chuỗi mô phỏng.
Hai dẫn xuất, hai phương pháp (Luật 16), hội tụ.

Ghi nhận thiết kế: bỏ `record_exception` thay bằng `add_event` ghi tay là lựa
chọn ĐÚNG — OTel dựng attribute từ chính object exception nên không có đường
chèn scrub vào giữa; giữ cả hai thì bản đã che chỉ là **trang trí cạnh bản thô**.

## F-28 — mở họ động từ tier-1 tiếng Anh

```
F28-A hiệu quả   : 8/8 tier1   (ignore · disregard · forget · override ·
                                bypass · skip · do not follow · must not obey)
F28-B đối chứng  : 7/7 qua sạch ("Skip this step…" · "Do not follow links…" ·
                                "…follow the instructions on the screen" …)
F28-C kho MoMo   : 1.814 câu -> tier1 0/1814 · tier2 2/1814 (lành, đúng thiết kế)
```

Chạy **A và B cùng nhau** đúng Luật 2. Comment stale đã được dọn, trỏ
`d312428` + `0/1814`.

⚠️ **Ghi đúng chữ khi báo cáo:** *"bắt thêm 7 ca ĐÃ BIẾT"*, **KHÔNG** phải
*"đã chặn lớp tấn công đổi-động-từ"*. Thêm 9 động từ vẫn là danh sách viết tay
— `refrain from following`, `pay no attention to`, gõ sai chính tả vẫn qua.
Sửa LỚP cho tiếng Anh (`KC.GAP`, kiểu Luật 18/ADR-023) thuộc **CỔNG-A**.

---

## Dẫn xuất thứ BA cho S-01 — quà từ probe S-03

Chuỗi lỗi sau scrub cho ra `[ORGANIZATION]:  Key (phone)=…` — **NER gán chữ
`DETAIL` và `ERROR` thành `[ORGANIZATION]`**. Cùng lớp lỗi với `"chính sách"` →
`[PERSON]` của S-01, nhưng ở **một đường hoàn toàn khác** (trace, không phải
`note`) và do **một vai khác** phát hiện.

⟹ **Ba dẫn xuất độc lập, ba phương pháp, cùng một kết luận: sai NHẬN DẠNG,
không sai NGƯỠNG.** Dùng được nếu ADR-025 cần chứng minh lỗi **không đặc thù
cho field `note`** — nó là thuộc tính của lớp NER, nên mọi cửa dùng `scrub_pii`
đều thừa hưởng.

Ở trace thì che thừa **vô hại** (không ai đọc trace để ra quyết định nghiệp vụ)
— tôi **không** coi đó là bug cần vá, đồng ý với tech-lead.

## Điều tôi KHÔNG ký

- **Backfill A1** — quyết định của PO, phải ra **trước pilot** (xem A1-04).
- **Chuỗi migration gãy trên SQLite** (`a1b2c3d4e5f6`, ADR-019 — *No support for
  ALTER of constraints in SQLite dialect*): tech-lead phát hiện, **có sẵn từ
  trước lô này**, không thuộc bốn bản vá. Tôi không nghiệm thu nó, chỉ ghi nhận
  — nhưng nó đáng một finding riêng vì `alembic upgrade head` trên DB trắng
  SQLite là **chết**, tức đường dựng schema chính thức không chạy được ở môi
  trường test mặc định của dự án.
