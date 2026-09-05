# FIN-05 — AI Agent CSKH Ví điện tử

> AI Agent hỗ trợ chăm sóc khách hàng ví điện tử, xử lý khiếu nại giao dịch: **điều tra qua
> tool, phân loại, đề xuất hướng xử lý có căn cứ — và KHÔNG BAO GIỜ tự quyết định.** Mọi hành
> động tài chính đều qua người thật duyệt (HITL), mọi con số agent nói đều truy ngược được về
> dữ liệu thật, và các ràng buộc đó được ép ở tầng database + 23 test bất biến.

**Đội:** T226 (AI 20K Build Phase, Cohort 3 — Vingroup × VinUni) · **PO & Thực hiện:** Đào Ngọc Bích
· **Mentor:** Đặng Hải Lộc · **Đối tác nghiệp vụ:** ZaloPay và VNPT Money

**Live:** https://app.adaptivealgo.uk *(home-server + Cloudflare Tunnel — xem
[hướng dẫn triển khai](docs/giao-viec/2026-08-15-chay-that-tai-nha-windows-tunnel.md))*

---

## Kiến trúc 30 giây

LLM **bể 4 model tự xoay** (`qwen3.8-plus` · 3 bản `deepseek`, qua DashScope — ADR-043) điều phối bằng **LangGraph** (ReAct, 5 tool tra cứu DB thật) · RAG chính sách
trên **ChromaDB** (trích nguyên văn kèm nguồn, không tổng hợp AI) · **mọi lớp an toàn là luật tất
định ngoài model**: che PII trước khi lên LLM (Presidio + spaCy NER), chặn bịa số (origin-rule —
số phải truy về tool result), chống prompt-injection (spotlighting + phân tier), maker-checker ép
bằng CHECK constraint. Chi tiết: [ARCHITECTURE.md](ARCHITECTURE.md).

## Tính năng chính (đã kiểm bằng chạy thật)

**Điều tra & đối thoại**
- Agent điều tra khiếu nại qua **5 tool DB thật**, phân loại (4 loại × 3 phạm vi), đề xuất hướng
  xử lý — **không tự quyết**. Duyệt là việc của người (Sếp).
- **Chống bịa số** (origin-rule): mọi số tiền/trạng thái truy ngược được về tool result; mã giao
  dịch không tồn tại → agent nói thẳng *"không tìm thấy"*, không bịa.
- **Tự chuyển người thật**: `request_human_handoff` mở live-chat + tạo/ưu tiên ticket.

**Tra cứu chính sách (RAG)** — ADR-061/062/065
- Trích **nguyên văn kèm nguồn**, không tổng hợp AI; lọc đúng phạm vi + rerank cross-encoder
  (sidecar, **fail-closed** → `not_found` nếu sidecar chết).
- Tra được **cả từ khoá ngắn** ("phí rút tiền", "hoàn tiền") lẫn câu đầy đủ; câu rác/lạc đề
  ("zzzqwx", "thời tiết") → *"Chưa tìm thấy"* (precision giữ).
- **Xem toàn văn ↗** (ADR-065): bấm kết quả → mở tab mới đọc toàn bộ tài liệu, **tự cuộn + tô sáng
  đúng đoạn khớp** câu tra cứu.

**Hàng chờ CSKH & phân quyền theo dòng** — ADR-063/064
- **Chuông thông báo vé mới** — fan-out theo CSKH đang online, kèm loại khiếu nại · phạm vi · độ
  ưu tiên · SLA; kèm **bảng CSKH đang online** cho Sếp.
- CSKH **chỉ thấy vé chưa ai nhận + của chính mình**; nút **"Nhận vé"** chủ động (idempotent).
  Sếp thấy **toàn bộ** vé (BOLA khoá → 404).
- Bảng vé: **phân trang 30/50/100** + **bộ lọc AND thật** 5 tiêu chí (SQL WHERE) + cột STT.

**An toàn — luật tất định NGOÀI model**
- HITL: chỉ Sếp duyệt hoàn tiền/điều chỉnh cho **mọi** phạm vi (ép bằng CHECK constraint).
- Che PII trước khi lên LLM · OTP step-up cho hành động hậu quả · gắn cờ gian lận **≠** khoá ví.
- Guardrail chặn AI khai khống *"đã tạo vé"* — chỉ kích khi lượt **thật sự** có ý định tạo vé.

## Chạy local

### Cách 1 — Docker (đủ stack, giống production)

```bash
git clone https://github.com/AI20K-Build-Phase-Cohort-3/P-226.git && cd P-226
cp .env.example .env        # điền OPENAI_API_KEY + sinh 2 secret (xem bảng dưới)
docker compose up -d        # backend + frontend + postgres + redis + caddy + jaeger
# đợi ~1 phút, kiểm: docker ps → backend (healthy)
# mở https://localhost (chứng chỉ tự ký — chấp nhận cảnh báo trình duyệt)
```

### Cách 2 — Dev (backend + frontend rời, hot-reload)

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -r requirements.txt
make db          # sinh dữ liệu + dựng schema + seed (60k giao dịch, 200 khách)
make demo-data   # kịch bản mẫu cho Dashboard/Approve
make run         # backend FastAPI :8010

cd frontend && npm install && npm run dev   # frontend Next.js :3000
```

## Biến môi trường

App **fail-fast khi thiếu secret bắt buộc** — không có default kiểu `changeme`.

| Biến | Bắt buộc | Ghi chú |
|---|---|---|
| `JWT_SECRET_KEY` | ✅ | Sinh: `openssl rand -hex 32` |
| `FIELD_ENCRYPTION_KEY` | ✅ | Fernet key, sinh: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`. ⚠️ Mã hoá at-rest chat/STK/mô tả khiếu nại — **mất key = mất dữ liệu vĩnh viễn**; chuyển máy phải mang theo y nguyên. |
| `REDIS_URL` | ✅ | `redis://localhost:6379/0` · test/CI dùng `fake://ci` (fakeredis, không cần Redis thật) |
| `OPENAI_API_KEY` | ✅ (khi chạy agent) | |
| `DATABASE_URL` | — | Mặc định SQLite dev; Docker dùng Postgres (compose set sẵn) |
| `LLM_MODEL_POOL` | — | **Bể model để hạ tầng tự xoay** khi cạn hạn mức (ADR-043). Danh sách phân tách bằng dấu phẩy. Thiếu ⟹ chỉ dùng `LLM_MODEL`, không xoay |
| `LLM_MODEL` | — | Model chat đang dùng. **Đây mới là biến vận hành thật** |
| `APP_ENV` | `production` | 🔴 Mặc định **fail-safe**: thiếu biến ⟹ TẮT `/docs`, `/openapi.json`, `/redoc`. Đặt `development` để bật lại khi làm việc cục bộ |
| `OPENAI_MODEL` | `gpt-4o-mini` | Chỉ còn là **fallback cuối** của `LLM_MODEL` |
| `JWT_ACCESS_EXPIRE_MINUTES` | — | Mặc định 15 |
| `CLOUDFLARE_TUNNEL_TOKEN` | chỉ profile `home` | Deploy home-server; fail-fast ở `scripts/deploy_home.*` |
| `AI_LOG_SERVER` / `AI_LOG_API_KEY` | — | Nộp AI-usage log về server chấm điểm BTC (pre-push hook) |
| `SSL_CERT_FILE` | — | ⚠️ **Phụ thuộc máy** (đường dẫn certifi của máy Mac) — KHÔNG mang sang máy khác |

## Tài khoản demo (mật khẩu chung `Demo@123`)

| Vai | SĐT | Thấy gì |
|---|---|---|
| Khách hàng | `0974000145` | Chat trợ lý AI, live-chat người thật |
| CSKH | `0353000201` | Hàng chờ ticket, timeline điều tra — **không có nút duyệt** |
| Sếp duyệt | `0905000205` | Phê duyệt + OTP step-up theo từng đề xuất |
| Đối tác ví | `0900000001` | Quản kho chính sách RAG — không đụng được tiền/dữ liệu khách |

> Hai vai trên cùng một máy: vai khách cửa sổ thường, vai nhân viên **cửa sổ ẩn danh**
> (một trình duyệt = một phiên đăng nhập).

## Câu hỏi mẫu (đã kiểm bằng chạy thật — xem [eval/EVAL-EVIDENCE.md](eval/EVAL-EVIDENCE.md))

```text
minh chuyen 171k cho ban hom 1/8 luc 12:47 ma ban bao chua nhan duoc
→ tìm đúng 1 giao dịch giữa 9 giao dịch cùng số tiền, chọn bằng mốc giờ

kiem tra giup gd TXN20260623999901, toi chuyen ma khong thay trong lich su
→ mã không tồn tại: agent nói thẳng "không tìm thấy", KHÔNG bịa số nào

Trừ một lần đã xót, đây trừ tận hai lần 852k, quá đáng thật.
→ xoa dịu trước, liệt kê đúng 2 giao dịch trùng cách nhau 37 giây

dung roi, 2 giao dich 852.000d luc 11:31 ngay 30/06 do, tao ho so giup minh
→ tạo ticket, vào hàng chờ CSKH; agent CHỈ đề xuất — duyệt là việc của người

cho tôi gặp người thật
→ gọi request_human_handoff, tạo/ưu tiên ticket + mở kênh live-chat
```

## Kiểm thử

```bash
pytest tests/test_invariants.py -v        # 5 ràng buộc cứng, 23 test — introspect app THẬT
python scripts/check_contracts.py         # phát hiện artifact lệch contracts/
pytest tests/ -m "not security_finding"   # toàn bộ backend (**110 file · 598 hàm test**, đo 05/09)
python eval/run_golden_set.py             # 120 case nghiệp vụ (gọi OpenAI thật)
python eval/run_adversarial_set.py        # 45+ case tấn công
```

Frontend E2E: **38 spec Playwright** (`frontend/e2e/`) — chạy trên UI thật, đo DOM.

CI (GitHub Actions, `.github/workflows/ci.yml`) — **14 job**: invariants · contract-drift ·
lint+test · appsec · security-findings-gate · migration-chain · …

🔴 **Đọc bảng CI đỏ — bốn nguyên nhân khác nhau, đừng gộp** *(đo 20/08)*:
- **8 job chạy THẬT** trên runner self-hosted (ADR-037).
- **6 job `ubuntu-latest` KHÔNG chạy** — billing của org bị chặn. Dấu nhận biết: `runner_name`
  **rỗng**, `steps = 0`, thất bại trong **0 giây**. Chúng hiện màu đỏ y hệt một bài kiểm trượt.
- **`security-findings-gate` ĐỎ ĐÚNG THIẾT KẾ** — giữ đỏ chừng nào còn finding P0 chưa vá.
- Lỗi hạ tầng thoáng qua (đứt mạng lúc `pip install`, cổng bị chiếm trên runner dùng chung).

*(Ghi chú cũ ở đây viết "toàn bộ job chạy tương đương trên máy dev" — **đúng lúc viết, nay SAI**:
CI đã chuyển sang self-hosted và 8 job chạy thật.)*

## Cấu trúc & tài liệu

```
contracts/        ← NGUỒN SỰ THẬT: 42 route × role · state machine HITL · 5 tool AI
src/agents/       ← LangGraph agent + 5 tool + guardrails (spotlighting, O1-O4, origin-rule)
src/api/          ← FastAPI (BFF-first, rate-limit, OTP step-up)
frontend/         ← Next.js (BFF pattern — browser không bao giờ cầm JWT backend)
tests/            ← 110 file test + tests/test_invariants.py (đỏ = build hỏng)
eval/             ← golden/adversarial/heldout set + bằng chứng chạy thật
docs/DECISIONS.md ← 65 ADR — mọi quyết định kèm lý do và lý-do-bác-phương-án-khác
docs/STATE.md     ← trạng thái sống của dự án, cập nhật mỗi phiên làm việc
```

Đọc thêm: [FIN05-Brief.md](FIN05-Brief.md) · [FIN05-PRD.md](FIN05-PRD.md) ·
[docs/TESTING.md](docs/TESTING.md) · [JOURNAL.md](JOURNAL.md) · [WORKLOG.md](WORKLOG.md)

## Team

| Member | Role | Student ID |
|--------|------|-----------|
| Đào Ngọc Bích | PO & Thực hiện toàn bộ (điều phối đội **6 phiên** Claude Code: tech-lead · tester · security · DevOps · critic · PO-agent) | 2A202601745 |

## License

MIT
