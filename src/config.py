"""FIN-05 — cấu hình dùng chung cho DB, seed, và API.

Đọc trước khi sửa: mọi đường dẫn ở đây là tương đối so với thư mục gốc repo,
để `make db` chạy được từ bất kỳ máy nào không cần chỉnh tay.
"""
from __future__ import annotations

import os
from pathlib import Path

from dotenv import load_dotenv

ROOT_DIR = Path(__file__).resolve().parent.parent
load_dotenv(ROOT_DIR / ".env")

DATA_RAW_DIR = ROOT_DIR / "data" / "raw"
DATA_SCHEMA_DIR = ROOT_DIR / "data" / "schema"
DATA_GENERATED_DIR = ROOT_DIR / "data" / "generated"
EVAL_DIR = ROOT_DIR / "eval"

# Đường dẫn DB runtime — SQLite theo quyết định Data Brief §5.1.
# Override bằng biến môi trường DATABASE_URL nếu cần trỏ sang Postgres.
DB_PATH = ROOT_DIR / "data" / "app.db"
DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")

# BR-13: ngưỡng N lần hỏi lại trước khi tạo ticket tra thủ công — CHƯA chốt
# với team (business_rules.md BR-13, verified: false). Cô lập ở đây để đổi
# một chỗ khi PO chốt.
CLARIFY_QUESTION_MAX_ROUNDS = 2

# BR-01/BR-02: trần pháp lý dùng để tính sla_due_at — verified: false, xem
# data/schema/scenarios.yaml §sla.legal.
SLA_LEGAL_BANK_BUSINESS_DAYS = 4
SLA_LEGAL_GENERAL_DAYS = 30

# BR-03: cam kết dịch vụ nội bộ (wording trả khách) — KHÔNG dùng để tính
# sla_due_at (xem BR-04). Chỉ dùng trong câu trả lời agent.
SLA_SERVICE_FIRST_RESPONSE_HOURS = 48
SLA_SERVICE_FRAUD_BUSINESS_DAYS = 7

# BR-06: định dạng masking PDPA cho thông tin bên thứ ba.
PHONE_MASK_VISIBLE_PREFIX = 3
PHONE_MASK_VISIBLE_SUFFIX = 4
BANK_ACCOUNT_MASK_VISIBLE_SUFFIX = 4

# Agent (src/agents/) — PRD §15.3: ưu tiên model rẻ/nhanh cho tra cứu + phân
# loại, phù hợp định vị "chi phí AI thấp" (Brief §3). Đổi qua env, không sửa code.
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

# Bảo mật (src/auth.py, src/db/crypto_types.py) — KHÔNG có giá trị mặc định
# cho 2 key này: một key đoán được/rỗng là lỗ hổng giả vờ có bảo mật, còn tệ
# hơn không có gì (nhìn như đã ép JWT nhưng ai cũng ký giả được token). Thiếu
# key -> lỗi ngay lúc import, không lỗi âm thầm lúc chạy.
JWT_SECRET_KEY = os.environ.get("JWT_SECRET_KEY")
if not JWT_SECRET_KEY:
    raise RuntimeError(
        "Thiếu JWT_SECRET_KEY trong .env — sinh bằng: "
        "python3 -c \"import secrets; print(secrets.token_urlsafe(48))\""
    )
JWT_ALGORITHM = "HS256"
JWT_EXPIRE_MINUTES = 8 * 60  # 8 giờ — khớp thời lượng cookie phiên ở frontend

FIELD_ENCRYPTION_KEY = os.environ.get("FIELD_ENCRYPTION_KEY")
if not FIELD_ENCRYPTION_KEY:
    raise RuntimeError(
        "Thiếu FIELD_ENCRYPTION_KEY trong .env — sinh bằng: "
        "python3 -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
    )

# RAG chính sách/FAQ (src/rag/) — đối tác ví (role partner_admin) upload,
# agent + CSKH tra cứu (search_policy tool, POST /policy-search).
RAG_INDEX_DIR = ROOT_DIR / "data" / "rag_index"  # Chroma persistent store — không commit (.gitignore)
RAG_EMBEDDING_MODEL = "text-embedding-3-small"
RAG_CHUNK_SIZE = 800
RAG_CHUNK_OVERLAP = 150
RAG_SEARCH_TOP_K = 4
MAX_UPLOAD_SIZE_MB = 10
