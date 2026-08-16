# Architecture Diagram — FIN-05

> Sơ đồ đầy đủ + data flow + bảng quyết định kiến trúc: **[ARCHITECTURE.md](../ARCHITECTURE.md)**
> (nguồn duy nhất, không nhân bản để tránh trôi). File này giữ bản rút gọn cho deliverable #3.

```mermaid
graph LR
    U([Khách / CSKH / Sếp / Đối tác]) --> C[Caddy + Cloudflare Tunnel]
    C --> FE[Next.js BFF<br/>JWT không rời server]
    FE --> BE[FastAPI]
    BE --> AG[LangGraph Agent<br/>GPT-4o-mini · 5 tool<br/>danh nghĩa customer]
    AG --> GD[Guardrails tất định:<br/>scrub PII · spotlighting ·<br/>O1-O4 + origin-rule]
    GD --> DB[(PostgreSQL<br/>EncryptedText ·<br/>CHECK maker-checker)]
    AG --> RAG[(ChromaDB — RAG<br/>trích nguyên văn)]
    BE --> RD[(Redis — vé WS ·<br/>rate limit · thread signals)]
    BE -.-> JG[Jaeger — OTel đã scrub]
    BE --> HITL[HITL: CSKH điều tra →<br/>Sếp duyệt + OTP step-up<br/>— AI không có mặt]
```

**Data flow một câu:** khách gõ → scrub PII → agent gọi tool thật → lọc đầu ra (số phải truy về
tool result) → khách; tiền chỉ đi khi Sếp mở hồ sơ đọc căn cứ và duyệt bằng OTP gắn đúng đề xuất —
ràng buộc người-tạo-≠-người-duyệt nằm ở tầng database.
