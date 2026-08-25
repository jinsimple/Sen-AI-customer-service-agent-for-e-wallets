# Dữ kiện kỹ thuật đo được trong đợt "OTP trước token" — NGOÀI mọi hạng mục

> **Ngày:** 2026-08-25 · **Người đo:** Coder (`p-226-63`) · **Yêu cầu:** PO thật (đóng đợt)
>
> Đây **không phải** nhật ký đợt. Đây là **sáu dữ kiện kỹ thuật** không thuộc hạng mục
> nào, sẽ **chết cùng phiên** nếu không ghi, và **áp cho mọi đợt sau**.
> Đọc hết trong hai phút. Mỗi mục: **số đo · cách dựng lại · vì sao đáng nhớ.**

---

## ① `return_direct=True` CÓ hỗ trợ — và phép dò hiển nhiên nhất cho ÂM TÍNH GIẢ

```
langchain 1.3.15 · langchain-core 1.5.4   (đo TRONG container, không trên host)

@tool                      → return_direct = False
@tool(return_direct=True)  → return_direct = True        ← cờ CÓ tác dụng thật
inspect.getsource(create_agent), dòng 838-842:
  "# Only include exit_node in destinations if any tool has return_direct=True"
  any(tool.return_direct for tool in tool_node.tools_by_name.values())
```
⟹ `create_agent` **tự dựng `exit_node`**. Thiết kế *"dừng ngay sau một tool cụ thể"*
**không cần** viết lại bằng `StateGraph` tuỳ biến, **không cần** đổi kiến trúc agent.

🔴 **BẪY — phép dò hiển nhiên nhất cho kết quả NGƯỢC:**
```
hasattr(BaseTool, 'return_direct')          →  False    ← SAI, âm tính giả
BaseTool.model_fields  chứa 'return_direct' →  True     ← đúng
```
`return_direct` là **field pydantic trên INSTANCE**, không phải thuộc tính LỚP.
Nếu báo cáo dừng ở `hasattr`, cả đội đã kết luận *"không hỗ trợ ⟹ phải đổi kiến trúc"*.
Nó chỉ lộ ra vì `create_agent` **mâu thuẫn** với phép dò — và người đo đi đào tiếp thay
vì báo con số đầu tiên.

**Luật rút ra:** *một phép dò mâu thuẫn với nguồn khác thì phải ĐÀO, đừng chọn bên nào
tiện hơn.* Với pydantic, kiểm bằng `model_fields`, không bằng `hasattr` trên lớp.

---

## ② Lệch host ↔ container nằm HOÀN TOÀN ở trục `tool`, KHÔNG ở `system`

```
                    băm src/        system    tool     tổng
HOST (venv P-121)   691dd9c40578     5.275    1.982    7.257
container           691dd9c40578     5.275    2.014    7.289
                    ↑ GIỐNG HỆT      ↑ khớp   ↑ +32
nguyên nhân: langchain-core 1.5.3 (host) vs 1.5.4 (container)
             — chỉ chạm `convert_to_openai_tool()`
```
⟹ **Hệ quả dùng được:** thay đổi chỉ chạm `prompt.py` (trục `system`) thì **đo trên host
là HỢP LỆ**; tổng thật tính bằng `tool` số **container**. Thay đổi chạm docstring tool
thì **bắt buộc đo trong container**.

🔴 `docs/STATE.md:24` cấm dùng `P-121-new/.venv` *"để đo kích thích gửi model"*. Câu ấy
phủ **cả việc đếm token của kích thích**, không chỉ *gọi LLM thật* — người đo trong đợt
này đọc đúng chữ mà hiểu hẹp, và con số `293 token headroom` sai đã lan vào kế hoạch
của cả đội trước khi QA/QC đo lại ra `261`. (Đã niêm ở `e727067`.)

---

## ③ Bốn lần dụng cụ đo hỏng trong MỘT phiên — và chiều lệch của từng lần

Ghi cả **chiều** vì chiều mới quyết định mức nguy:

| # | dụng cụ hỏng thế nào | chiều lệch | hậu quả nếu tin |
|---|---|---|---|
| 1 | bộ bóc câu corpus mù khoá `utterances` (là DANH SÁCH) → 7/409 câu, rồi mù `query_co_dau` → 349/409 | **TRẤN AN** | báo *"4 → 4, không đổi"* cho một nghiệm thu |
| 2 | `cd $D` rò sang lệnh sau ⟹ đo **bản sao hai lần**, in ra hai số giống nhau | **CHO PHÉP HÀNH ĐỘNG NGUY** | kết luận *"bản sao vẫn khớp repo, dựng thoải mái"* |
| 3 | đo bằng venv `P-121-new` — thứ STATE cấm đúng cho việc này | **TRẤN AN** | `293` thay vì `261`, lan vào quyết định phân bổ |
| 4 | `hasattr` trên lớp cho field pydantic (mục ①) | **BI QUAN** | bỏ một đường kiến trúc đúng |

🔴 **Ba lần đầu lệch về phía trấn an, lần thứ tư lệch về phía bi quan.** Cả hai chiều
đều đắt, nhưng **khác cách**: trấn an làm ta tin sai; bi quan làm ta **bỏ đường đúng**.
Một bộ kiểm chỉ canh chiều trấn an sẽ **không bao giờ bắt được lần thứ tư**.

**Phép thử rẻ đã cứu cả bốn lần:** in **MẪU SỐ** cạnh mọi tỉ lệ, và **đo tách rời từng
lệnh** thay vì nối `&&`/`cd`.

---

## ④ `docker compose` GỘP danh sách `ports`, không thay — phải `!override`

```yaml
# SAI — cổng của base VẪN CÒN, ngăn mới đụng cổng ngay
services: { postgres: { ports: ["127.0.0.1:45432:5432"] } }
# ĐÚNG
services: { postgres: { ports: !override ["127.0.0.1:45432:5432"] } }
```
Triệu chứng: `Bind for 127.0.0.1:5432 failed: port is already allocated` **dù override
đã ghi cổng khác**. Mất vài phút vì tưởng mình gõ sai cổng.

---

## ⑤ Hai bẫy vận hành của ngăn dựng mới — cả hai giả dạng "ngăn chết"

```
curl https://127.0.0.1:48443/...   →  000     ← TLS gãy: chứng chỉ Caddy cấp cho `localhost`
curl https://localhost:48443/...   →  307     ← ĐÚNG
backend nghe cổng 8010, KHÔNG phải 8000        ← probe 8000 → "Connection refused"
```
Cả hai **trông y hệt hệ thống hỏng** trong khi `docker compose` đã ghi `healthy`.
Kiểm chéo bằng `docker inspect -f '{{.State.Health.Status}}'` trước khi kết luận.

---

## ⑥ `eval/_harness.py` KHÔNG BAO GIỜ chạm cổng OTP — và đó là dữ kiện về hiệu lực phép đo

```
_harness.py:559  run_agent_turn(session, user_id=…, message=…, thread_id=…)
                 ↑ KHÔNG truyền `otp_verified_at`
graph.py:913     otp_verified_at: float | None = _ALWAYS_FRESH
                 ↑ sentinel = "coi như vừa xác thực"
```
⟹ Mọi ca eval chạy như thể khách **vừa xác thực OTP**. Cổng ④ (`can_otp`) **không bao
giờ bắn trong eval**.

**Vì sao đáng ghi:** đây là dữ kiện dùng để **bác một P0** trong đợt (nghi *"agent ngừng
gọi tool"* — hoá ra không phải, và cổng ④ cũng không phải thủ phạm). Ai viết ca eval
đụng luồng OTP phải **truyền tay** `otp_verified_at`, nếu không họ đang đo một hệ thống
mà cổng OTP không tồn tại.

---

## Liên quan, đã ghi nơi khác — để khỏi chép lại

- **`test_invariants` chỉ so TÊN tool, KHÔNG so CHỮ KÝ** ⟹ đổi input của một tool mà
  quên `contracts/agent-tools.yaml` thì **cổng VẪN XANH**. Đây là lỗ của chính cơ chế
  contract. → `docs/giao-viec/CHECKLIST-dot-otp-truoc-token.md`, mục ⑩ (`655a112`).
- **`fin05-po-test` / `fin05-final` build từ BẢN SAO repo đông cứng** trong scratchpad
  một phiên khác, không từ repo. → checklist, mục điểm danh 25/08.
- **Bản vá 7/7 bị từ chối** (xanh mọi cổng, vỡ vì một chữ tuỳ chọn).
  → `docs/nhat-ky/2026-08-25-ban-va-7-tren-7-bi-tu-choi.md`.
