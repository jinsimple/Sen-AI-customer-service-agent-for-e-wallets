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

# ---------------------------------------------------------------------------
# DATABASE_URL — BẮT BUỘC, KHÔNG có giá trị mặc định (ADR-013).
#
# TRƯỚC 2026-08-13 dòng này là:
#     DATABASE_URL = os.environ.get("DATABASE_URL", f"sqlite:///{DB_PATH}")
#
# Fallback im lặng đó đã gây một sự cố thật mất nhiều giờ điều tra: Docker
# stack chạy Postgres, còn mọi thứ chạy trên host (uvicorn dev, seed script,
# load test, verify_security.sh) ÂM THẦM rơi về SQLite. Hai cửa sổ trình duyệt
# nhìn giống hệt nhau nhưng ghi/đọc HAI DATABASE KHÁC NHAU — khách tạo ticket
# ở bên này, CSKH bên kia vĩnh viễn không thấy, F5 bao nhiêu lần cũng vô ích.
#
# Nhãn môi trường (ADR-009) giúp PHÁT HIỆN khi đã lệch. Bỏ fallback ở đây chặn
# từ GỐC: thiếu biến thì chết ngay lúc khởi động với thông báo rõ ràng, thay
# vì lặng lẽ sinh ra một database thứ hai mà không ai hay biết.
#
# Đặt tường minh cho TỪNG môi trường:
#   .env (dev/docker) : postgresql+psycopg2://...@127.0.0.1:5432/fin05
#   CI                : sqlite:///:memory: hoặc Postgres ephemeral
#   pytest            : tests/conftest.py tự tạo engine SQLite tạm riêng,
#                       KHÔNG dùng biến này (xem get_engine ở dưới)
# ---------------------------------------------------------------------------
DB_PATH = ROOT_DIR / "data" / "app.db"  # chỉ còn dùng cho script seed cũ trỏ tay
DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError(
        "Thiếu DATABASE_URL trong .env — KHÔNG còn fallback SQLite tự động "
        "(xem ADR-013: fallback im lặng từng làm hệ thống tách đôi database).\n"
        "  Dev/Docker : DATABASE_URL=postgresql+psycopg2://<user>:<pass>@127.0.0.1:5432/<db>\n"
        "  Test/CI    : DATABASE_URL=sqlite:///:memory:"
    )

# ---------------------------------------------------------------------------
# ĐỊNH DANH MÔI TRƯỜNG (2026-08-13) — sinh ra sau một sự cố thật, không phải
# tính năng trang trí.
#
# Sự cố: Docker stack (Caddy :80 -> Postgres) và stack dev cục bộ
# (next dev :3000 -> uvicorn :8010 -> SQLite) chạy SONG SONG. PO mở cửa sổ
# khách ở `localhost` và cửa sổ CSKH ở `localhost:3000` — hai giao diện GIỐNG
# HỆT NHAU nhưng nói chuyện với HAI DATABASE KHÁC NHAU. Khách tạo ticket vào
# Postgres, CSKH đọc từ SQLite nên vĩnh viễn thấy 0, F5 bao nhiêu lần cũng vô
# ích. Mất nhiều giờ điều tra vì mọi tầng code đều đúng.
#
# Bài học tổng quát: môi trường VÔ HÌNH là lỗi thiết kế. Hệ thống phải TỰ KHAI
# BÁO nó là ai — nhìn là biết, không phải suy luận từ số cổng.
#
# CHỈ suy ra từ scheme + tên database. TUYỆT ĐỐI không đưa user/password/host
# vào đây: giá trị này được trả ra qua /health (endpoint công khai).
# ---------------------------------------------------------------------------
APP_ENV = os.environ.get("APP_ENV", "development")


def _db_identity(url: str) -> tuple[str, str]:
    """Trả (loại_db, tên_db) từ DATABASE_URL, đã lược bỏ mọi thông tin nhạy cảm."""
    scheme = url.split("://", 1)[0].split("+", 1)[0] or "unknown"
    tail = url.rsplit("/", 1)[-1].split("?", 1)[0] if "/" in url else ""
    if scheme == "sqlite":
        tail = tail or "(bộ nhớ)"
    return scheme, tail or "(không rõ)"


DB_KIND, DB_NAME = _db_identity(DATABASE_URL)

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

# Seed cố định dùng khi sinh dataset (scripts/gen_dataset.py --seed, mặc định
# 20260802 — PRD §9). Backend cần lại giá trị này để tái tính câu trả lời bảo
# mật demo (User.security_answer_hash = sha256(f"ans-{seed}-{user_id}")) lúc
# xác thực OTP thật (src/auth.py) — KHÔNG lưu answer plaintext ở đâu cả, chỉ
# tái tạo công thức để so hash, giữ đúng nguyên tắc không lưu bí mật dạng thô.
DATASET_SEED = 20260802

# Ngưỡng khoá phiên xác thực OTP sau N lần sai — dùng LẠI đúng
# min_failed_attempts của FS-06 (data/schema/fraud_signals.yaml) để nhất quán
# với định nghĩa "bất thường xác thực" mà fraud_engine.py đã dùng, không tự
# đặt số riêng.
OTP_MAX_FAILED_ATTEMPTS = 3

# AUTH-005/007/008 (FIN05_QA_TestCases.jsonl) — quyết định thiết kế đã chốt
# sau khi đối chiếu chuẩn ngành (nghiên cứu 2026-08-10, xem docs/TESTING.md):
# - Thao tác CHỈ XEM (lookup_transaction, get_customer_history — bao gồm cả
#   xem trạng thái ticket/khiếu nại đã có, AUTH-005 nhánh (e)): áp đúng
#   NIST SP 800-63B / OWASP ASVS 5.0 Level 2 cho phiên AAL2 — tối đa 12 giờ
#   kể từ lúc xác thực OTP, không phân biệt còn hoạt động hay không (bản đơn
#   giản hoá của "30 phút không hoạt động HOẶC 12 giờ tối đa" — hệ thống hiện
#   tại là JWT stateless, không theo dõi hoạt động realtime giữa các request
#   nên chỉ áp mốc tuyệt đối, không áp mốc "không hoạt động").
OTP_VIEW_MAX_MINUTES = 12 * 60

# - create_ticket (dẫn tới khả năng hoàn tiền thật, hậu quả tài chính) cần
#   xác thực TƯƠI HƠN — mô hình step-up 2 tầng theo rủi ro (chuẩn ngành: cửa
#   sổ hiệu lực step-up phổ biến 15-60 phút, chọn mốc chặt 15 phút vì đây là
#   hành động có hậu quả tài chính, không phải chỉ xem).
OTP_STEPUP_FRESH_MINUTES = 15

# AUTH5-04 (đợt nâng cấp Auth Flow, 2026-08-12) — OTP step-up RIÊNG cho
# POST /resolutions/{id}/approve (PSD2 dynamic linking, xem AuthSession.
# resolution_id/amount_snapshot). Ngắn hơn OTP_STEPUP_FRESH_MINUTES vì đây
# là hành động duyệt tài chính THẬT SỰ (không phải chỉ mở khoá để thao tác
# tiếp như create_ticket) — sếp phải xin OTP ngay sát lúc bấm duyệt.
RESOLUTION_APPROVAL_OTP_FRESH_MINUTES = 10

# BR-06: định dạng masking PDPA cho thông tin bên thứ ba.
PHONE_MASK_VISIBLE_PREFIX = 3
PHONE_MASK_VISIBLE_SUFFIX = 4
BANK_ACCOUNT_MASK_VISIBLE_SUFFIX = 4

# Agent (src/agents/) — PRD §15.3: ưu tiên model rẻ/nhanh cho tra cứu + phân
# loại, phù hợp định vị "chi phí AI thấp" (Brief §3). Đổi qua env, không sửa code.
OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY")
OPENAI_MODEL = os.environ.get("OPENAI_MODEL", "gpt-4o-mini")

# Đo đạc thật 2026-08-13 (stress /agent/chat qua Playwright repeat-each): SDK
# openai-python mặc định KHÔNG timeout (chờ tới khi OS/socket tự đóng), và
# ChatOpenAI mặc định `max_retries=2` — 1 lượt gọi chậm/lỗi transient có thể
# kéo dài hàng chục giây (đã đo thấy 23-33s thật), và vì route `/agent/chat`
# chạy sync trong threadpool, 1 request Playwright timeout bỏ dở KHÔNG huỷ
# được lượt gọi OpenAI đang chạy phía server — nó tiếp tục chiếm 1 thread +
# rate-limit budget, dồn lại qua nhiều test làm hàng loạt request SAU đó cũng
# chậm theo. Set trần rõ ràng để 1 lượt gọi hỏng luôn fail nhanh, không kéo
# theo cả chuỗi.
OPENAI_TIMEOUT_SECONDS = float(os.environ.get("OPENAI_TIMEOUT_SECONDS", "20"))
OPENAI_MAX_RETRIES = int(os.environ.get("OPENAI_MAX_RETRIES", "1"))

# 1 lượt /agent/chat = 1 vòng ReAct nhiều bước (LLM sinh + gọi tool xen kẽ,
# tới _AGENT_RECURSION_LIMIT=20 bước) — OPENAI_TIMEOUT_SECONDS ở trên chỉ
# chặn TỪNG lượt gọi OpenAI riêng lẻ, không chặn TỔNG thời gian cả lượt chat
# (đo thật: 1 request /agent/chat tốn 70s vì cần nhiều bước, mỗi bước gần
# chạm trần OPENAI_TIMEOUT_SECONDS). Đây là trần TỔNG cho cả agent.invoke(),
# xử lý giống GraphRecursionError (chuyển sang human handoff thay vì treo vô
# thời hạn hay 500) — xem src/agents/graph.py::run_agent_turn.
AGENT_TURN_TIMEOUT_SECONDS = float(os.environ.get("AGENT_TURN_TIMEOUT_SECONDS", "45"))

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
# AUTH5-02 (đợt nâng cấp Auth Flow 2026-08-12, NIST SP 800-63B-4/PSD2) — rút
# từ 8 giờ xuống 15 phút. Token cũ (8h, phát trước khi nâng cấp) VẪN qua được
# _decode() bình thường tới khi hết hạn tự nhiên (không thêm field bắt buộc
# mới vào payload) — không khoá đột ngột session đang sống (AUTH5-MIGRATE-001).
JWT_ACCESS_EXPIRE_MINUTES = 15

# Refresh token (KHÔNG phải JWT — chuỗi ngẫu nhiên, lưu trong Redis, xem
# src/auth.py::mint_refresh_token) — role nội bộ (cskh/supervisor/
# partner_admin) rủi ro cao hơn nếu bị đánh cắp (chạm dữ liệu nhiều khách)
# nên TTL ngắn hơn hẳn khách hàng (AUTH5-02B).
JWT_REFRESH_EXPIRE_DAYS_CUSTOMER = 7
JWT_REFRESH_EXPIRE_DAYS_STAFF = 1

FIELD_ENCRYPTION_KEY = os.environ.get("FIELD_ENCRYPTION_KEY")
if not FIELD_ENCRYPTION_KEY:
    raise RuntimeError(
        "Thiếu FIELD_ENCRYPTION_KEY trong .env — sinh bằng: "
        "python3 -c \"from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())\""
    )

# Redis (đợt nâng cấp Auth Flow, 2026-08-12) — revocation store JWT refresh
# token + rate-limit dùng chung (login, OTP, live-chat ws-ticket/message).
# KHÔNG có giá trị mặc định trỏ tới Redis thật (cùng nguyên tắc fail-fast như
# JWT_SECRET_KEY ở trên) — nhưng CHO PHÉP scheme "fake://" tường minh (dùng
# fakeredis, xem src/redis_client.py) cho CI/test không cần Redis thật, đúng
# convention playbooks/production-packaging-checklist.md ("REDIS_URL: fake://").
REDIS_URL = os.environ.get("REDIS_URL")
if not REDIS_URL:
    raise RuntimeError(
        "Thiếu REDIS_URL trong .env — dùng redis://<host>:6379/0 cho môi trường "
        "thật, hoặc fake://ci cho CI/test không cần Redis thật (fakeredis)."
    )

# RAG chính sách/FAQ (src/rag/) — đối tác ví (role partner_admin) upload,
# agent + CSKH tra cứu (search_policy tool, POST /policy-search).
RAG_INDEX_DIR = ROOT_DIR / "data" / "rag_index"  # Chroma persistent store — không commit (.gitignore)
RAG_EMBEDDING_MODEL = "text-embedding-3-small"
RAG_CHUNK_SIZE = 800
RAG_CHUNK_OVERLAP = 150
RAG_SEARCH_TOP_K = 4
MAX_UPLOAD_SIZE_MB = 10

# Live chat (2026-08-11) — lớp phòng vệ THỨ 2 bên cạnh dọn phiên lúc WS ngắt
# kết nối SẠCH (release_staff_sessions/close_customer_session_on_disconnect,
# src/api/live_chat_ws.py): mạng rớt đột ngột/trình duyệt bị kill không gửi
# được khung đóng kết nối, server có thể không bao giờ nhận WebSocketDisconnect
# — phiên 'waiting' sẽ treo mãi nếu chỉ dựa vào tín hiệu disconnect. Bất kỳ
# phiên 'waiting' nào (chưa ai nhận) quá cũ coi như khách đã rời đi từ lâu —
# 30 phút đủ rộng để không đóng nhầm 1 khách đang chờ thật (ETA hiển thị cho
# khách chỉ là ước tính, không có SLA cam kết cứng ở tầng live-chat).
LIVE_CHAT_STALE_WAITING_MINUTES = 30
