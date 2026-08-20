# ĐÁNH GIÁ — kho checkpoint LangGraph trước lần deploy VPS công khai đầu tiên

> 20/08/2026. Bảo Mật, theo yêu cầu PO-agent. **CHỈ ĐÁNH GIÁ, không thiết kế/không code.** Mọi số đo
> chạy trên `fin05` qua `docker exec` (chỉ đọc, không sửa gì). Mọi truy vấn CHỈ ĐẾM/DÒ BYTE — không
> in một byte nội dung hội thoại nào ra bất cứ đâu, kể cả trong tài liệu này.

## KHÔNG có phát hiện ở mức "không được deploy trước khi vá" — nhưng có MỘT điểm PHẢI KIỂM trước khi kết luận điều đó vững

Đã kiểm ngay khi thấy, không đợi viết xong: **[ĐO] `docker-compose.yml:22` — cổng Postgres ghim
`127.0.0.1:5432:5432`, không publish ra ngoài.** Deploy lên VPS công khai KHÔNG tự động mở đường mạng
trực tiếp tới kho này — kẻ tấn công từ Internet cần chiếm được máy chủ trước (SSH/lỗ hổng khác), không
phải chỉ cần biết địa chỉ. Đây là lý do tôi KHÔNG báo khẩn ngay.

🔴 **Nhưng đây là file docker-compose DEV trong repo, không phải cấu hình THẬT sẽ chạy trên VPS.**
Tôi không có khả năng kiểm cấu hình VPS thật (ngoài phạm vi đọc của tôi, có thể do một phiên DevOps
khác dựng). **Câu PHẢI HỎI trước khi tin kết luận trên: cấu hình sẽ deploy lên VPS có publish cổng
Postgres ra ngoài không?** Nếu CÓ — nâng toàn bộ đánh giá dưới đây lên mức khẩn, báo tôi ngay để định
hạng lại.

## 1. Phơi nhiễm thật — [ĐO] lấy mẫu byte thật, không suy từ schema

```
select count(*) from checkpoint_blobs;                    → 6.842  (18/08 là 6.213, tăng ~315/ngày)
pg_total_relation_size('checkpoint_blobs')                → 38 MB
```

**[ĐO] dò trên BYTE (không dò chuỗi đã escape — đúng bài học Luật L đã rút 18/08), theo TỪNG channel:**

| channel | tổng | có tiếng Việt (dấu, byte thật) | dạng Fernet (đã mã hoá) | có `HumanMessage` | có nhãn scrub `[PERSON`/`[LOCATION` |
|---|---|---|---|---|---|
| `messages` | 3.956 | 3.152 (80%) | 0 | 3.956 (100%) | 2.552 (65%) |
| `__start__` | 1.164 | 339 (29%) | 0 | 1.164 (100%) | 430 (37%) |
| `__pregel_tasks` | 1.722 | 118 (7%) | 0 | 0 | 9 |

**Kết luận rõ:** **0% mã hoá trên CẢ BA channel** — không đổi so với 18/08. `messages`/`__start__`
mang lời khách đã qua `scrub_pii()` (thấy nhãn `[PERSON]`/`[LOCATION]` — bằng chứng scrub CÓ chạy,
không phải bằng chứng kho sạch, đúng cảnh báo đã ghi 18/08).

### 🔴 Phát hiện MỚI so với 18/08 — `__pregel_tasks` không đi qua đường scrub nào cả

**[ĐO] dò tên tool trong `__pregel_tasks` (1.722 blob, KHÔNG in nội dung, chỉ đếm khớp tên field/tool
đã biết công khai từ chính contract dự án):**

```
create_ticket        116   ·  description_raw   116   (khớp CHÍNH XÁC — xác nhận đây là tham số tool)
lookup_transaction    159  ·  get_customer_history 408  ·  search_policy  127  ·  request_human_handoff 60
```

**Đây là kênh phơi nhiễm KHÁC hẳn `messages`** — không phải lời khách gõ tự do (đã qua `scrub_pii`),
mà là **THAM SỐ TOOL do model chọn truyền**, trong đó có `description_raw` — đúng cột Nhóm A theo
ADR-025 QĐ1, **CỐ Ý không che-lúc-ghi** (lý do toàn vẹn bằng chứng, giống hệt lý lẽ đã dùng cho
`complaints.description_raw`). Ràng buộc "đừng che `HumanMessage`" PO-agent nhắc là đúng cho
`messages`; nhưng `__pregel_tasks` không phải `HumanMessage` — nó là bản sao **THAM SỐ TOOL**, đã
tồn tại độc lập với ràng buộc đó.

**Đây là BẢN SAO THỨ HAI, không mã hoá, của đúng dữ liệu vừa được ADR-032 mã hoá ở bảng
`complaints`.** ADR-032 (18-19/08) đã đưa `complaints.description_raw` từ 738 plaintext → 0 plaintext
qua backfill + `EncryptedText`. **Cùng nội dung đó VẪN tồn tại plaintext ở đây, tại MỘT bảng khác,
KHÔNG được ADR-032 chạm tới** — đúng hình dạng đã cảnh báo lúc đóng ADR-032 (§5.J STATE 18/08: "vá
vũng nước làm vòi chảy lộ ra rõ hơn"), giờ có bằng chứng cụ thể bằng số đếm thay vì suy đoán chung
chung. Có khả năng cao **SĐT khách gõ để tra cứu** (`lookup_transaction`) cũng nằm trong 159 blob đó
dưới dạng tham số — chưa đếm riêng, không cần thiết để kết luận mức độ nghiêm trọng.

## 2. Đối chiếu NĐ 13/2023

**Loại dữ liệu:** văn bản tự do khách tự gõ (khiếu nại, câu hỏi) + tham số tra cứu (có thể gồm SĐT)
+ mã giao dịch — dữ liệu cá nhân theo nghĩa thông thường của NĐ 13/2023. **Không tự phán** liệu có
rơi vào hạng "dữ liệu cá nhân nhạy cảm" (điều đó cần người có thẩm quyền pháp lý xác nhận, không phải
suy luận kỹ thuật — đúng ranh giới đã giữ ở hồ sơ Qwen 17/08).

**Retention — [ĐO] xác nhận lại, không giả định từ trí nhớ:** `grep -rn "checkpoint" src/
--include=*.py | grep -iE "delete|prune|ttl|retention|purge|expire"` → **0 kết quả.** Không có gì
xoá kho này bao giờ. Đây là **nghĩa vụ pháp lý ĐỘC LẬP với mã hoá** — NĐ 13/2023 đòi giới hạn thời
gian lưu trữ theo MỤC ĐÍCH xử lý; lưu vô thời hạn (bất kể có mã hoá hay không) tự nó là một khoảng
trống chưa đóng.

**Rời biên giới:** kho này KHÔNG tự nó gửi dữ liệu ra ngoài hạ tầng (khác câu chuyện `scrub_pii` cho
model-input, đã xử lý riêng hôm nay) — nó là lưu trữ TẠI CHỖ. Câu hỏi biên giới ở đây là VỊ TRÍ VẬT
LÝ/PHÁP LÝ của chính VPS sắp deploy — **chưa biết, cần hỏi PO thật**: VPS đặt ở đâu? Nếu ngoài Việt
Nam, đây LÀ một hoạt động chuyển dữ liệu ra nước ngoài, độc lập với câu chuyện LLM provider.

## 3. Tái dùng `FIELD_ENCRYPTION_KEY`/cơ chế đã có — [ĐO] MỘT PHẦN được, MỘT PHẦN không

**KHÔNG tái dùng được `EncryptedText` (kiểu cột SQLAlchemy)** — [ĐO] cơ chế đó hoạt động bằng cách
bọc kiểu dữ liệu của MỘT CỘT trong MỘT MODEL ORM ta tự định nghĩa. `checkpoints`/`checkpoint_blobs`
**không phải model của ta** — LangGraph's `PostgresSaver` tự quản lý schema + tự viết SQL trực tiếp,
không đi qua lớp ORM của ta. Không có "cột" nào của ta để gắn kiểu vào. Đúng ràng buộc đã biết trước
("bảo vệ tầng serde, đừng đổi cột").

**CÓ THỂ tái dùng CHÍNH `FIELD_ENCRYPTION_KEY`** (giá trị khoá, KHÔNG phải cơ chế cột) — nếu bảo vệ
được cắm ở tầng SERDE (tham số `serde=` LangGraph checkpoint saver cho phép truyền serializer tuỳ
biến — **[PHẢI KIỂM bởi Coder, không phải điều tôi xác nhận được từ đọc mã**: cần đối chiếu đúng bản
`langgraph-checkpoint-postgres==3.1.2` đang dùng, API có thể khác giữa các phiên bản, đúng cảnh báo
đã có sẵn trong `pii.py`/nhiều chỗ khác về việc không tự suy diễn hành vi thư viện ngoài). Nếu API đó
tồn tại: MỘT serde tuỳ biến encrypt/decrypt bytes bằng Fernet + `FIELD_ENCRYPTION_KEY` TRƯỚC khi
LangGraph ghi xuống — dùng LẠI đúng khoá, đúng chính sách xoay khoá đã có, không phải khoá thứ hai
phải quản lý riêng.

**Lợi ích của tầng serde so với vá riêng từng channel:** bọc ở TẦNG NÀY bảo vệ **CẢ BA channel cùng
lúc** (`messages`/`__start__`/`__pregel_tasks`) bằng MỘT điểm sửa — closes luôn phát hiện mới ở mục 1
(`__pregel_tasks`) mà không cần một cơ chế riêng cho nó.

## 4. Phương án — BA trục lựa chọn độc lập, không phải một phương án duy nhất

Bốn ràng buộc PO-agent đã cố định (serde không đổi cột · đừng che HumanMessage · giải quyết retention
cùng lúc · nghiệm thu dò byte) thu hẹp không gian lựa chọn, nhưng còn BA trục THẬT cần quyết định —
tôi không tự chọn thay, nêu đánh đổi từng trục:

### Trục A — phạm vi mã hoá: chỉ dữ liệu MỚI, hay backfill cả 6.842 blob cũ?
- **Chỉ mới (từ ngày vá trở đi):** rẻ, không rủi ro hỏng dữ liệu cũ khi migrate. Đánh đổi: 6.842 blob
  hiện có (38 MB, tăng dần mỗi ngày cho tới lúc vá) **vĩnh viễn plaintext** — đúng tiền lệ đã chấp
  nhận cho `fin05ttl`/`complaints` giai đoạn đầu, nhưng ở ĐÂY dân số cũ LỚN HƠN nhiều lần dân số đã
  từng backfill (6.842 so với 761 dòng `complaints`).
- **Backfill cả cũ:** đóng triệt để, nhưng ĐẮT và RỦI RO hơn hẳn backfill `complaints` đã làm — ta
  không sở hữu schema/định dạng serialize (khác `complaints`, nơi ta tự viết cột), một backfill hỏng
  có thể làm HỎNG state LangGraph (không đọc lại được hội thoại cũ), không chỉ mất bằng chứng như
  case trước. Cần script nghiệm thu cực chặt (đúng khuôn "sửa cái đèn trước khi soi" đã dùng cho
  ADR-032) TRƯỚC khi chạy trên dữ liệu thật.

### Trục B — độ dài retention: giữ bao lâu trước khi xoá?
**Tôi KHÔNG tự đề xuất một con số** — đây là câu hỏi MỤC ĐÍCH NGHIỆP VỤ (SLA xử lý khiếu nại bao
lâu? có nghĩa vụ lưu trữ tối thiểu nào theo quy định ngành ví điện tử không?), không phải câu hỏi kỹ
thuật. Cần PO thật/người có thẩm quyền nghiệp vụ trả lời trước khi tôi hoặc Coder chọn số — cùng lý
do tôi từ chối tự chốt ngưỡng rate-limit hôm qua.

### Trục C — thứ tự làm so với ngày deploy: full-fix trước, hay một BƯỚC ĐỆM rẻ trước rồi hoàn thiện sau?
- **Full-fix trước deploy** (serde encryption + retention xong hẳn): đúng "cửa sổ rẻ" PO-agent nêu,
  nhưng khối lượng việc thật (serde tuỳ biến + kiểm tương thích thư viện + nghiệm thu byte + quyết
  Trục A/B) không nhỏ — rủi ro làm vội đúng chỗ dữ liệu khách nhạy cảm nhất.
- **Bước đệm rẻ trước, hoàn thiện sau:** vd đặt MỘT retention TẠM (dài, an toàn — ví dụ vài trăm
  ngày, không cần tối ưu) NGAY, chặn đà tăng vô hạn trước, trong khi serde-encryption được thiết kế
  kỹ hơn làm fast-follow. Giảm rủi ro làm ẩu, nhưng nghĩa là dữ liệu MỚI TẠO SAU DEPLOY vẫn plaintext
  trong một khoảng thời gian nữa — đúng cùng đánh đổi "tốc độ vs rủi ro" đã cân nhắc nhiều lần hôm
  nay cho các quyết định khác.

## Không kết luận

❌ đã đủ an toàn, không cần làm gì — SAI, xác nhận LẠI mức CAO đã định 18/08, thêm bằng chứng cụ thể
(`__pregel_tasks`) chứ không đổi mức. ❌ cần dừng deploy ngay — chưa đủ căn cứ (Postgres không lộ ra
ngoài trong cấu hình DEV đã kiểm), NHƯNG treo ở câu PHẢI HỎI đầu tài liệu (cấu hình VPS thật). ❌ có
phương án nào là "đúng" duy nhất — ba trục A/B/C đều còn mở, cần PO thật quyết trước khi viết ADR.
