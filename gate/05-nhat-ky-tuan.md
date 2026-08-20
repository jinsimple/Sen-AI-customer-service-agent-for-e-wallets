# Nhật ký tuần — FIN-05 · Đội T226

> **Dựng từ lịch sử git thật**, không viết lại từ trí nhớ. Mọi con số dưới đây lấy bằng
> `git log`, tái tạo được bằng lệnh ghi ở cuối file.
>
> **~985 commit · 3 tuần (W32–W34) · 46 ADR · 11 PR đã merge.**
>
> *Con số commit **còn tăng** — bảng ba tuần dưới đây cộng lại là **984**, đo lúc viết file; số mới
> nhất lấy bằng lệnh ở cuối file. Nêu ra để người đọc cộng tay không thấy lệch mà nghi.*
>
> Đội: **1 người thật (PO) + nhiều phiên Claude chuyên trách** (tech-lead · tester · security ·
> UX/UI · DevOps · critic). Mỗi vai có vùng ghi riêng, không vai nào ghi đè vùng vai khác.

---

## Tuần 32 — 09/08 · Khởi động

**2 commit.** Dựng khung repo, chốt bài toán: AI Agent hỗ trợ CSKH ví điện tử xử lý khiếu nại
giao dịch. Ràng buộc đặt ra ngay từ đầu và không đổi suốt dự án: **agent điều tra, agent không
bao giờ quyết định.**

---

## Tuần 33 — 10/08 → 16/08 · Dựng sản phẩm

**498 commit** — `docs 264 · fix 75 · feat 62 · test 61 · chore 14`

**Đã ship:**

| | |
|---|---|
| Nền tảng agent | LangGraph + 5 tool, gọi **dưới danh nghĩa `customer`** — AI không có role riêng |
| RAG chính sách | Nạp DOCX giữ cấu trúc (heading, bảng) · dấu phiên bản kho · `kho_rag.py` |
| Guardrails | Che PII · spotlighting · bộ lọc đầu ra O1–O4 · origin-rule |
| HITL | CSKH điều tra (**không có nút duyệt**) → Supervisor quyết định + OTP step-up |
| Đo lường | Script benchmark một lệnh, 5 trục có trọng số · `input_chars` — đại lượng bất biến qua tokenizer |
| Hạ tầng | Tách nhà cung cấp LLM khỏi embedding · dấu build vào `/health` · CI self-hosted |

**Việc quan trọng nhất tuần này không phải một tính năng:** dựng `contracts/` thành **nguồn sự thật
về cấu trúc**, và viết `tests/test_invariants.py` **introspect app đang chạy thật** để so với
contract. Thêm một route · đổi một guard · đổi tên một tool mà quên cập nhật contract ⟹ đỏ ngay.

**Bài học đắt nhất tuần:** thước đo bị bắt sai **7 lần trong một ngày** (16/08) — phần lớn do chính
người dùng thước tự bắt, **hai lần do vai khác bắt chéo**. Hệ quả: dựng luật *"công cụ đo là lớp
không ai canh"* thành một chương riêng trong chuẩn viết test.

---

## Tuần 34 — 17/08 → 20/08 · Siết chất lượng & chuẩn bị production

**484 commit** — `docs 282 · test 89 · fix 49 · feat 29`

**Đã ship:**

| ADR | nội dung |
|---|---|
| **ADR-041** | Vé hiện **toàn bộ** hội thoại — lời agent ghi vào `messages`, không đọc từ checkpoint |
| **ADR-042** | `tool_calls` trên dây là **mảng ở mọi đường**; ba-trạng-thái sống ở `ly_do_fallback` |
| **ADR-043** | **Model không còn ghim** — hạ tầng tự xoay trong bể 4 model đã kiểm |
| **ADR-044** | CSKH đọc được hội thoại bot↔khách của vé mình xử lý |
| **ADR-045** | Kho checkpoint: mã hoá ở tầng serde *(chờ PO duyệt)* |

**Hai cơ chế nền dựng trong tuần:**

- **`dau_ma_nguon`** — băm nội dung mã nguồn, đóng dấu vào ảnh Docker. Dựng sau khi chứng minh
  `build_commit` **nói dối theo cả hai chiều**. Từ 20/08 có cả bản cho frontend, nên câu
  *"ảnh đang chạy có đúng mã nguồn này không"* trả lời được trong hai giây thay vì phải dựng lại.
- **Trần chi tiêu token theo ngày** + xoay model khi cạn hạn mức — `429` **không** xoay, vì nghẽn
  tạm thời không phải cạn hạn mức.

### Ngày 20/08 — diễn tập deploy trên bản clone sạch

Ngày dài nhất dự án: **61 commit**, và là ngày sản phẩm được chuẩn bị để rời khỏi `localhost`.

**Tìm ra 6 chỗ đứt, không chỗ nào phát hiện được bằng cách đọc lại tài liệu** — cả sáu chỉ lộ khi
có người dựng lại từ một bản clone sạch, vì người viết tài liệu không thể tự thấy thứ máy mình đã có:

```
① nhánh main thiếu 65 commit — người clone không có .env.example để copy
② thông báo lỗi RAG bảo "chạy trong container" với người ĐANG ở trong container
③ transactions.jsonl không có trong git, không bước nào nói phải sinh trước
④ script seed chết ở ràng buộc BR-11 — 5 khối cuối CHƯA TỪNG chạy lần nào
⑤ curl /health XANH cả khi backend đã chết  ← cổng xác nhận cuối cùng, không thể đỏ
⑥ APP_ENV mặc định mở /docs — 34 route + schema ra Internet, KHÔNG triệu chứng nào
```

Hai chỗ cuối nguy hiểm hơn bốn chỗ đầu cộng lại: bốn chỗ đầu **chặn người deploy lại**, hai chỗ cuối
**để họ đi tiếp với một niềm tin sai**.

**Kết quả diễn tập cuối** (clone sạch, cả sáu bản vá chạy cùng nhau lần đầu):
```
băm nguồn   backend 29b0496a4946 · frontend 6f9bbf28a90e — host KHỚP trong ảnh, cả hai phía
APP_ENV     có dòng → /openapi.json 200 · xoá dòng → 404
pip freeze  168/168 dòng, diff RỖNG so với requirements.lock.txt
chuỗi       6/6 bước ĐẠT, trừ 1 lệnh cần khoá API thật
```

### Kỷ luật đo lường — con số đáng kể nhất của tuần

Trong một ngày, đội bắt được **chín khẳng định sống lâu hơn sự thật của nó**. Không phải chín lời
nói dối — chín câu **từng đúng**, rồi thực tế đi qua mà sổ sách không đi theo. Ví dụ:

- *"Hai ca kiểm an toàn chưa chạy được"* — sai từ 15/08, **sống 5 ngày**; chúng đã chạy và đạt.
- *"Bóp méo tiếng Việt 5,6%"* — đo trên một chữ ký hàm **nay không còn tồn tại**; số thật là **1,6%**.
- *"Chín file mang nhãn finding chưa vá"* — thật ra **một**. Người đếm (PO-agent) dùng tìm-chuỗi
  thay vì bộ lọc nhãn, và đã đếm chính những câu ghi *"không còn nhãn này"* thành bằng chứng ngược lại.

**Cả chín đều được niêm tại chỗ kèm bằng chứng, không xoá** — vì xoá đi thì phiên sau phát hiện lại
từ đầu. Từ đó đúc **Luật X**: *kết quả đo phải rơi vào một file trước khi được đi vào một câu*, và
người **nhận** một con số qua tin nhắn chịu cùng trách nhiệm với người **phát**.

---

## Tái tạo số liệu trong file này

```bash
git log --format='%ad' --date=format:'%Y-W%V' | sort | uniq -c   # commit mỗi tuần
git log --format='%s' | grep -cE '^feat'                          # đếm theo loại
grep -c '^## ADR-' docs/DECISIONS.md                              # số ADR
gh pr list --state merged --limit 50 | wc -l                      # PR đã merge
```


---

## ⚠️ KIỂM TAY TRƯỚC KHI NỘP — file này nằm NGOÀI cơ chế tự canh

`gate/MANIFEST.md` ghi băm sha256 để phát hiện bản sao đã trôi. **File này không có bản gốc nơi
khác, nên nó KHÔNG nằm trong bảng băm đó** — không cơ chế nào báo khi nó nói sai.

Ba thứ đối chiếu tay, mất một phút:
```bash
grep LLM_MODEL_POOL .env                 # tên model — phải KHỚP, KỂ CẢ mốc ngày
grep -c '^## ADR-' docs/DECISIONS.md     # số ADR
git log --oneline | wc -l                # 🔴 TỔNG commit — so 1 số với 1 số
gh pr list --state merged --limit 50 | wc -l                     # số PR đã merge
find src -name '*.py' | wc -l ; find tests -name 'test_*.py' | wc -l   # số file
git log --format='%ad' --date=format:'%Y-W%V' | sort | uniq -c   # commit mỗi TUẦN
```

🔴 **Vì sao lệnh `wc -l` cho TỔNG là lệnh quan trọng nhất ở đây, không phải lệnh cuối:**
lệnh cuối cho ra **bảng theo tuần** — người kiểm phải **tự cộng ba dòng** rồi mới so được với con số
ở đầu file. **Đó chính xác là bước đã sai** (tiêu đề ghi `982`, bảng cộng ra `984`). Tái tạo đúng
phép đo mà không bỏ được bước cộng tay thì cổng kiểm vẫn hở ở đúng chỗ nó từng hở.
**So một số với một số, đừng bắt người kiểm làm phép tính.**
🔴 **Ca thật 20/08:** ba file trong `gate/` từng ghi bể model là `deepseek-v4-pro` / `deepseek-v4-flash`
— **đúng hai bí danh mà ADR-043, nằm chung hồ sơ, đã tường minh TỪ CHỐI vì không có mốc ngày.** Hồ sơ
tự mâu thuẫn ngay trên chủ đề nó dùng làm điểm nhấn. Review bắt được; không cơ chế nào bắt được.
