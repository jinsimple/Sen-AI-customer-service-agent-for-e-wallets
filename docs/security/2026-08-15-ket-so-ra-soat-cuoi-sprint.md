# Kết sổ rà soát cuối sprint — 2026-08-15

> Vai: **security** · vùng ghi `docs/security/` · nhánh `dev/learning-loop`
> Dấu chung cho mọi phép đo trong phiên: **`he_thong=fd16681d8088`**
> (cây `src/` KHÔNG đổi suốt phiên — xác nhận ba lần, ba vai độc lập).
> Mọi số: **0 TPM, tất định, đo TRONG PHIÊN** (Luật 9).
>
> File này là **mục lục + trạng thái tồn dư**. Không lặp lại nội dung — mỗi
> mục trỏ tới hồ sơ đầy đủ.

---

## 1. Năm việc treo tôi nhận đầu phiên — trạng thái đóng sổ

| # | Việc treo | Trạng thái | Ở đâu |
|---|---|---|---|
| 1 | Verify PII masking của `note` trước khi bật CI security-gate | **XONG — kết luận: CHƯA BẬT GATE** | `…ra-soat-cuoi-sprint-note-scrub-va-pipeline.md` |
| 2 | Canh hồi quy mốc nền đối kháng 18/20 (`6c5fff420bb9`) | **XONG — mốc đã TRÔI, có hệ quả thao tác** | §3 dưới |
| 3 | oracle-phủ-định "không phải 21" | **KHÔNG ĐỔI — vẫn chờ đợt CỔNG-A** | sổ Đợt 2 |
| 4 | MT-E02 traceback | **THU HẸP, chưa đóng** (cố ý — Luật 5) | hồ sơ trên §6 |
| 5 | Rà pipeline scrub trước khi log/trace rời vùng kiểm soát | **XONG MỘT PHẦN** — xem §4 | hồ sơ trên §5 |

## 2. Sinh ra trong phiên — bảy hồ sơ

| Commit | Nội dung | Cần ai |
|---|---|---|
| `c2c2d06` | **S-01** (CAO) `note` chặn nhầm 40%, xoá căn cứ từ chối · **S-02** (CAO) `agent_note` không scrub · **S-03** (TB) exception không qua scrub | PO (S-01/02) · coder (S-03) |
| `eff47ac` | Đính chính **ST2-P0-3 §5.2** — đơn thuốc `scrub_pii` của chính tôi không còn an toàn | PO |
| `d312428` | Đính chính **F-25 §3(a)** — `ignore all/prior` ở lại tier-1, FP đo được 0/1814 | *(đóng — tester đã land)* |
| `b7e4230` | Đo hành vi `description_raw` | PO (ADR-025) |
| `7b6f61b` | **F-28** (TB) tier-1 EN neo một động từ, 7 câu đổi-động-từ lọt | coder (xếp lịch) |
| `6f18c9d` | **Cơ chế bốn cửa** — một nguyên tắc, HAI cơ chế (đầu vào ADR-025) | PO |
| `eb444eb` | Đo hành vi `messages.content` + xác nhận mã hoá at-rest CÓ hiệu lực | PO (ADR-025) |

## 3. Mốc nền đối kháng — ĐÃ TRÔI, hệ quả bắt buộc cho CỔNG-A

Mốc nền 18/20 khoá ở `he_thong 6c5fff420bb9`; cây hôm nay đo ra
**`fd16681d8088`**. Trôi là **đúng dự kiến** (O1-O4 · F-27 · `note` đã land từ
lúc đó) — **không phải sự cố**.

**Nhưng hệ quả thao tác thì bắt buộc:** mọi lượt đo mới **KHÔNG ghép cặp
trước/sau hợp lệ** với mốc cũ nữa. Đợt CỔNG-A phải **đóng băng một mốc nền MỚI
ở một `he_thong` xác định TRƯỚC khi tiêu TPM**. Bỏ qua bước này là lặp lại đúng
sự cố `8e46f28→6c5fff` (mốc gộp nhiều hệ thống, cặp before/after không quy được
nhân quả).

## 4. Pipeline scrub — rà tới đâu, CHƯA rà cái gì

**Đã rà:** đường OTel/`langchain_callback` → tìm ra **S-03** (`set_status` +
`record_exception` không qua scrub; chưa có ca dương tính vì SQLite không echo
tham số, **nhưng Postgres có** ⟹ lớp lỗi chỉ lộ sau deploy thật).

**CHƯA rà — nói rõ để không ai đọc §5 hồ sơ chính thành "đã rà hết":**
- đường **Langfuse** (đang TẮT có chủ đích, `LANGCHAIN_TRACING_V2=false`)
- đường **log của eval** (`logging_config` chưa từng init ở runner → 0 dòng
  JSON; đã có tên F-LOG, PO đang giao người)

## 5. Tư thế rủi ro tồn dư — đọc trước pilot 150 người

Bốn cửa văn bản tự do, **cả bốn đo bằng hành vi**:

- **Không cửa nào rò ra KHÁCH** — mọi đường đọc đều gated `cskh`/`supervisor`,
  và `agent_note`/`note` không vào ngữ cảnh LLM. Đây là vế **đóng**.
- **Ba trong bốn cửa lưu PII plaintext** trong bảng kiểm toán; cửa thứ tư
  (`note`) có che nhưng **che hỏng nghĩa 40%**.
- **Một cửa chứa PII bên thứ ba** (`description_raw`) — người **chưa từng vào
  quan hệ với ví**, không có cơ sở pháp lý để lưu ngay từ đầu. Đây là mục
  **NĐ 13/2023** nặng nhất trong bốn.
- ✅ **Mã hoá at-rest của `messages.content` CHẠY THẬT** (kiểm byte thô, không
  tin dòng khai kiểu). ⚠️ Nhưng **đừng đọc thành "cửa này an toàn"**: at-rest
  chống mất đĩa/backup, **không** chống người đọc hợp lệ — lỗ đọc-theo-vai
  (mọi CSKH đọc mọi transcript, không giới hạn theo ca) **còn nguyên**.

**Ý kiến của tôi về mốc pilot:** bốn cửa này **không chặn** pilot 150 người về
mặt bảo mật *nếu* dữ liệu pilot được coi là dữ liệu thật và có đường xoá sau
đợt. Thứ **thật sự** cần trước pilot là **A1 + A2** (mã hoá `description_raw` +
trần độ dài) — rẻ, không cần quyết cơ chế, và đóng đúng phần "lưu plaintext
vĩnh viễn". Phần còn lại (B1/B2, A3, A4) là nợ đúng hạn, không phải nợ gấp.
Quyết định cuối thuộc PO.

## 6. Ghi chú quản trị — ba lần một vai tự bắt mình trong một phiên

Ghi lại vì nó nói về **cơ chế**, không về người:

1. PO-agent, AI-log: lấy `73/73 parse sạch` làm bằng chứng cho mệnh đề rộng hơn.
2. PO-agent, `note`: lấy `15 passed` làm bằng chứng "note đã đóng".
3. **Tôi**, bảng bốn cửa: viết *"cả bốn ô đều đo bằng hành vi"* khi
   `messages.content` chưa probe — **rộng hơn thứ tôi đã đo, đúng loại lỗi
   chính hồ sơ đó đang bắt người khác.**

Cùng một hình dạng: **lấy một phép đo xanh làm bằng chứng cho một mệnh đề rộng
hơn thứ nó đo.** Ba lần, ba vai, trong một phiên — và cả ba đều do **chính
người mắc** tự bắt, không phải do người khác soi ra.

Cộng thêm ba ca cùng họ *thước-hiệu-chuẩn-theo-vật* (bộ test skip im lặng hai
ngày · 15 kỳ vọng suýt viết theo impl · đơn thuốc §5.2 của tôi kê `scrub_pii`
mà chưa đo nó).

Đánh giá của tôi: đây là **dấu hiệu kiến trúc phân-vai đang chạy**, không phải
dấu hiệu đội cẩu thả. Một đội không có cơ chế đối kháng thì các lỗi này **không
được phát hiện**, chứ không phải không xảy ra.
