# Kiến trúc hệ thống FIN-05

> **Đo lại 20/08/2026** từ `docker-compose.yml`, `contracts/`, `src/` và ngăn xếp đang chạy —
> không vẽ từ trí nhớ. Bản trước (16/08) ghi model là `GPT-4o-mini`, **đã sai** kể từ ADR-043.
>
> Mọi tên tool · tên route · tên trạng thái dưới đây là **nguồn sự thật trong `contracts/`**,
> và `tests/test_invariants.py` introspect app đang chạy để bắt lệch. Sơ đồ này mô tả, contract quyết định.

---

## 1. Thành phần hệ thống

```mermaid
graph LR
    U([Khách · CSKH · Supervisor · Đối tác ví])
    U --> CF[Cloudflare Tunnel]
    CF --> CD[Caddy<br/>TLS · cổng duy nhất ra ngoài]
    CD --> FE[Next.js BFF<br/>JWT không rời server]
    CD -.WebSocket.-> BE
    FE --> BE[FastAPI<br/>34 route · require_role]

    BE --> AG[LangGraph Agent]
    BE --> LC[Live-chat WebSocket<br/>CSKH ↔ khách]

    AG --> RAG[(ChromaDB<br/>RAG · trích nguyên văn<br/>embedding: OpenAI<br/>text-embedding-3-small)]
    AG --> CP[(LangGraph checkpoint<br/>PostgresSaver · pool riêng)]

    BE --> DB[(PostgreSQL<br/>EncryptedText · CHECK maker-checker)]
    BE --> RD[(Redis<br/>vé WS · rate limit · tín hiệu thread<br/>· bộ đếm chi tiêu token)]
    BE -.trace đã scrub.-> JG[Jaeger · OpenTelemetry]

    CP -.cùng cụm.- DB
```

**Bảy container** — `caddy` · `cloudflared` · `frontend` · `backend` · `postgres` · `redis` · `jaeger`.
Chỉ `caddy` publish ra ngoài; `postgres` và `jaeger` ghim `127.0.0.1`.

---

## 2. Một lượt của agent — nơi mọi ràng buộc được ép

```mermaid
graph TD
    IN[Câu của khách] --> SC1[scrub PII<br/>registry model_input]
    SC1 --> LLM{{"LLM — bể 4 model xoay<br/>tên GHIM có mốc ngày<br/>qwen3.7-plus-2026-05-26<br/>deepseek-v4-pro-0813<br/>deepseek-v4-flash-0731<br/>deepseek-v3.2"}}

    LLM --> TOOL[5 tool · gọi dưới danh nghĩa customer]
    TOOL --> T1[lookup_transaction]
    TOOL --> T2[get_customer_history]
    TOOL --> T3[create_ticket]
    TOOL --> T4[request_human_handoff]
    TOOL --> T5[search_policy]
    T5 --> SP[Spotlighting<br/>CHỈ áp kết quả RAG<br/>hạ tài liệu đối tác<br/>xuống hạng DỮ LIỆU]
    T1 & T2 & T3 & T4 & SP --> TR[(tool_results<br/>mọi con số phải truy về đây)]
    TR --> LLM

    LLM --> OUT[Lọc đầu ra tất định O1–O4]
    OUT --> O1[O1 rò cấu hình]
    OUT --> O2[O2 thuật ngữ nội bộ]
    OUT --> O3[O3 số liệu không truy được nguồn]
    OUT --> O4[O4 hứa hoàn tiền — cả thì quá khứ]
    O1 & O2 & O3 & O4 --> ANS[Câu trả lời cho khách]

    LLM -.lỗi hết hạn mức.-> ROT[Xoay sang model kế tiếp<br/>trạng thái cạn lưu Redis có TTL]
    ROT --> LLM
```

**Ba điều sơ đồ này khẳng định, và đều có test bắt được nếu lệch:**

- 🔴 **Spotlighting KHÔNG nằm trên trục chính, và không áp lên câu của khách.** [ĐO]
  `danh_dau_du_lieu()` được gọi **đúng một chỗ trong toàn `src/`**: `customer_tools.py:409`, trên
  **kết quả `search_policy`** — tức nó chạy **SAU** khi LLM đã gọi tool ít nhất một lần. Việc của nó
  là **hạ tài liệu của đối tác ví xuống hạng DỮ LIỆU**, để nội dung trong đó không bao giờ được đọc
  như chỉ thị. Thứ bảo vệ câu của khách là `scrub_pii` (`graph.py:901`), một cơ chế khác.
  *(Bản sơ đồ 20/08 từng vẽ spotlighting trên trục chính giữa scrub-PII và LLM — **SAI**, vẽ theo
  trực giác kiến trúc chứ không theo code. Lead bắt được.)*
- **O1–O4 là regex tất định, độc lập với model.** Đổi model không làm lưới cuối yếu đi.
- 🔴 **Bể chỉ nhận TÊN GHIM có mốc ngày. Bí danh trôi (`deepseek-v4-pro`, `deepseek-v4-flash`) bị
  TỪ CHỐI lúc khởi động** — ADR-043 loại 2/5 model vì lý do này. Một cái tên không mốc có thể trỏ
  sang trọng số khác sau một đêm mà không ai biết.
- **Xoay model chỉ kích hoạt bởi lỗi hạng hết-hạn-mức** (`quota · exhaust · insufficient · balance · arrear · unpurchased`). **`429` không xoay** — nghẽn tạm thời không phải cạn hạn mức.
- **Chat và embedding chạy HAI nhà cung cấp khác nhau** — chat qua DashScope (bể 4 model), embedding
  qua OpenAI ([ĐO] `EMBEDDING_BASE_URL=None`). Tách cố ý: một bên cạn hạn mức không kéo bên kia chết theo.
- **Scrub PII dùng hai registry theo MỤC ĐÍCH.** Đường `model_input` cố ý bỏ SpacyRecognizer / DateRecognizer / PhoneRecognizer chung — chúng che nhầm mã giao dịch nội bộ. Đường `log` giữ nguyên over-redaction. Bóp méo câu tiếng Việt: **1,6% (2/124)**, có cổng `eval/do_bop_meo_pii.py` tự chấm lại.

---

## 3. HITL — nơi AI không có mặt

```mermaid
graph LR
    KH([Khách]) --> AI[AI điều tra<br/>danh nghĩa customer]
    AI --> VE[Vé khiếu nại]
    VE --> CS[CSKH<br/>ĐIỀU TRA · KHÔNG duyệt]
    CS --> DX[Đề xuất hướng xử lý<br/>cited_tool_result_ids]
    DX --> SUP{{"Supervisor<br/>QUYẾT ĐỊNH CUỐI<br/>+ OTP step-up ≤ 15 phút"}}
    SUP -->|duyệt| TH[Thực thi hoàn tiền / điều chỉnh]
    SUP -->|từ chối| RJ[reject_reason + rejected_by + rejected_at<br/>ràng buộc BR-11]
    SUP -->|cần thêm| CS

    AI -.KHÔNG có đường nào.-x TH
    CS -.KHÔNG có đường nào.-x TH
```

**Năm tool bị cấm tuyệt đối với AI** — `approve_resolution` · `execute_refund` · `adjust_balance` ·
`lock_wallet` · `escalate_to_supervisor`. Không tồn tại trong `build_customer_tools()`, và
`tests/test_invariants.py::test_inv08` gọi thẳng hàm đó để xác nhận.

**Maker–checker (BR-12):** người đề xuất không được là người duyệt. Ép ở tầng `CheckConstraint`
trong database, không chỉ ở tầng ứng dụng.

**Gắn cờ nghi gian lận ≠ khoá ví** — hai hành động độc lập hoàn toàn, không code nào nối trực tiếp.

---

## 4. Cơ chế giữ sơ đồ này khỏi trôi

Đây là phần khác biệt so với một sơ đồ kiến trúc thông thường: **cấu trúc hệ thống sống trong
`contracts/`, không sống trong tài liệu.**

| file | quy định |
|---|---|
| `contracts/authority-matrix.yaml` | 34 route × role nào được gọi |
| `contracts/agent-tools.yaml` | 5 tool được phép · 5 tool bị cấm · cơ chế truy vết |
| `contracts/resolution-state-machine.yaml` | vòng đời HITL · 3 trục trạng thái trực giao |

`tests/test_invariants.py` **introspect app đang chạy thật** — đọc `app.routes`, moi `allowed_roles`
từ closure của `require_role()`, đọc `CheckConstraint` qua AST, gọi thẳng `build_customer_tools()` —
rồi so với `contracts/`. Thêm một route · đổi một guard · đổi tên một tool mà quên cập nhật contract
⟹ **đỏ ngay**, không ai phải nhớ nhắc ai.

**Danh tính của vật đã dựng:** `src/dau_ma_nguon.py` băm nội dung mã nguồn và đóng dấu vào ảnh tại
`/app/.bam_ma_nguon`; `frontend/src/dau_ma_nguon.mjs` làm việc tương đương cho frontend. Đối chiếu
băm host với băm trong container trả lời được câu *"ảnh đang chạy có đúng mã nguồn này không"* trong
hai giây — `build_commit` **đã được chứng minh nói dối theo cả hai chiều**, nên không dùng.
