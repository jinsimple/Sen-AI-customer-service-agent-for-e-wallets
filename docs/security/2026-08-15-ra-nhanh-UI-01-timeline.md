# Rà nhanh UI-01 — timeline điều tra

> Vai: **security** · 2026-08-15 · rà **trước khi implement** (rẻ nhất ở đây).
> PO-agent nêu là **không bắt buộc, không chặn ai** — tôi vẫn rà vì UI này là
> bề mặt đọc PII dày đặc nhất trong toàn bộ giao diện nhân viên.
> **Không chặn UI-01.** Đặc tả viết tốt: đã cấm LLM-tóm-tắt, đã cấm làm mất dấu
> che, đã chọn hiện-tên-field-gốc thay vì giấu. Ba điều đó đúng.

## Hai góc đặc tả chưa nhắc tới

Endpoint timeline (`GET /tickets/{id}`, `main.py:744-751`) trả về **nhiều hơn**
những gì đặc tả liệt kê:

```python
"tool_input":     log.tool_input_json,
"tool_result":    session.get(ToolResult, log.tool_result_id).raw_json,   # ⟵ payload ĐẦY ĐỦ
"agent_note":     log.agent_note,                                          # ⟵ cửa S-02
```

### 🟡 (1) Khoảng trống PHẠM VI AUDIT-LOG với ADR-025 Pha-1

ADR-025 QĐ 2 Pha-1 bắt **audit-log mọi lượt đọc nhóm A** (`description_raw` +
`messages.content`). Timeline **không thuộc nhóm A** — nhưng nó phơi ra:

- `tool_result.raw_json` — payload tool đầy đủ. Và **BR-06 không che chính chủ**
  (`lookup_transaction.py:41,53`): khi khách tra giao dịch **của chính họ**,
  payload chứa **SĐT · số tài khoản · họ tên THẬT, không che**.
- `agent_note` — văn bản tự do nhân viên gõ, **chưa scrub** cho tới khi B3 land.

⟹ Nghịch lý: cùng một khách, CSKH đọc **transcript chat** thì **CÓ** audit-log;
đọc **SĐT + số tài khoản thật** của họ qua timeline thì **KHÔNG**. Người muốn
moi dữ liệu sẽ đi cửa không có log — và đó là cửa dữ liệu **có cấu trúc**, dễ
khai thác hơn transcript.

**Đề nghị (PO quyết, không chặn UI-01):** khi làm Pha-1, xét mở phạm vi
audit-log sang `GET /tickets/{id}` — hoặc tối thiểu sang **thao tác mở expander
"Xem dữ liệu kỹ thuật"** (§4 đặc tả), vì đó là nơi payload thô hiện ra nguyên
vẹn. Đây là **thay đổi phạm vi ADR-025**, nên thuộc PO chứ không phải một dòng
thêm vào lệnh UI-01.

### 🟡 (2) `agent_note` sẽ được render, và nó là cửa S-02

Đặc tả §Hiện trạng liệt kê timeline gồm **"ghi chú AI"** = `agent_note`. Theo
**S-02**, trường này **không scrub · không trần độ dài · không cờ tier** cho tới
khi **B3** land (và B3 **cố ý đi SAU** B1/B2).

Không phải lỗ mới — đường đọc vốn đã staff-gated. Nhưng hai điều nên ghi vào
lệnh UI-01:

1. **Đừng thêm nút sao-chép/xuất** cho khối này (và cho expander JSON). Một
   trường tự do chưa scrub + một nút copy = bề mặt trích xuất hàng loạt.
2. Khi **B3** land, UI phải hiển thị **bản đã scrub**. Hàng cũ ghi trước B3 vẫn
   là bản thô — cùng hình dạng tồn dư **A1-04** (hàng cũ không backfill). Nếu
   UI cache/duplicate giá trị ở tầng frontend thì bản thô sẽ sống thêm một
   vòng đời nữa.

## Một điểm nhỏ về ràng buộc cứng 3 — không phải lỗi, chỉ là ranh giới

Quy tắc `null` → **"Không tra được dữ liệu"** (§3) là một **ánh xạ ngữ nghĩa**,
không thuần định dạng: `null` có thể là *không có bản ghi*, hoặc *tool timeout*,
hoặc *tra được nhưng rỗng*. Cả ba hiện ra cùng một câu.

Không đề nghị đổi — câu đó đúng và dễ hiểu cho CSKH. Chỉ ghi để đừng ai về sau
đọc timeline rồi kết luận "hệ thống không có dữ liệu này" trong khi thực tế là
lượt tra đã hỏng. Nếu `ly_do_fallback` (đã có, từ đợt MT-E02) truy được tới
bước này thì phân biệt được ba ca — **không gấp**.

## Điều tôi KHÔNG rà

Chưa đọc code frontend (chưa tồn tại). Đây là rà **đặc tả + bề mặt API**, không
phải nghiệm thu implement. Khi UI-01 land, ca đáng probe nhất là: **giá trị đã
che ở tầng dữ liệu có còn nguyên dấu che sau khi qua lớp định dạng không**
(`038***0001` không được thành `0380001` hay `038***-0001`) — đặc tả §Ràng buộc
đã nêu, nhưng đó là loại lỗi chỉ lộ khi chạy thật.
