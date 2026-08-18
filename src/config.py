"""FIN-05 — cấu hình dùng chung cho DB, seed, và API.

Đọc trước khi sửa: mọi đường dẫn ở đây là tương đối so với thư mục gốc repo,
để `make db` chạy được từ bất kỳ máy nào không cần chỉnh tay.
"""
from __future__ import annotations

import os
import re
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

# Dấu vật, do Dockerfile ARG đặt lúc build. "khong-ro" = không truyền được —
# tự tố cáo, không im lặng giả vờ hợp lệ.
# Phân luồng lượt chat (T1). MẶC ĐỊNH TẮT — bật là đổi hành vi sản phẩm, và
# chưa có số nào về `f` (tỉ lệ lượt đơn thật) để biết nó đáng bao nhiêu.
PHAN_LUONG_BAT = os.environ.get("PHAN_LUONG_BAT", "").strip().lower() in ("1", "true", "yes")

# T3 · công tắc suy luận của model. MẶC ĐỊNH ĐỔI 1 -> 0 ngày 18/08: đây không
# còn là cờ ĐO, nó là bản vá cho một sản phẩm ĐANG HỎNG.
#
# [ĐO] cùng `qwen3.7-plus-2026-05-26`, cùng câu hỏi CSKH thật:
#     mặc định (suy luận BẬT)   20,88s · out 1161 · suy luận 980
#     enable_thinking=False      2,48s · out  101 · suy luận   0     ← 8,4× nhanh
#     thinking_budget=0          HTTP 400 — đường này KHÔNG dùng được
# [ĐO tester] một lượt agent thật: trung vị 18,6s · CHẬM NHẤT 49,1s
# [ĐO] AGENT_TURN_TIMEOUT_SECONDS = 45,0
# ⟹ 49,1 > 45 ⟹ câu "xem giao dịch gần đây" — câu khách CHẮC CHẮN hỏi — đang
# rơi fallback vì hết giờ. Bật suy luận là trạng thái làm sản phẩm vượt trần.
#
# 🔴 Cờ này mua TỐC ĐỘ, KHÔNG mua TOKEN. [ĐO] sổ thật 5 lượt gần nhất:
# input 10.920–23.520 · output 236–709 ⟹ input chiếm >95% chi phí. Đòn bẩy
# token thật nằm ở input ~14K (nhắc hệ thống + schema tool + lịch sử), là việc
# KHÁC. Ai đọc cờ này thành "đã tối ưu chi phí" là đọc sai.
#
# 🔴 KHÔNG đặt thêm biến thứ hai (`FIN05_LLM_SUY_LUAN`…) cho cùng một công tắc:
# hai định nghĩa của cùng một vật sẽ lệch nhau, và lệch trong im lặng — cùng lý
# do đã có `bam_ma_nguon` và `BUILD_COMMIT`. Bật lại: `SUY_LUAN_BAT=1`.
#
# ⚠️ Đọc LÚC IMPORT ⟹ đổi nó bắt buộc RECREATE container. `docker exec -e` chỉ
# đổi tiến trình con, KHÔNG chạm uvicorn đang phục vụ.
SUY_LUAN_BAT = os.environ.get("SUY_LUAN_BAT", "0").strip().lower() not in ("0", "false", "no")

BUILD_COMMIT = os.environ.get("BUILD_COMMIT") or "khong-ro"
BUILD_AT = os.environ.get("BUILD_AT") or "khong-ro"


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

# --- NHÀ CUNG CẤP: tách CHAT khỏi EMBEDDING ------------------------------
# Đổi nhà cung cấp bằng biến môi trường, không sửa code. Mọi biến dưới đây
# FALLBACK về `OPENAI_*` -> không đặt gì thì hành vi y hệt trước.
#
# VÌ SAO TÁCH LÀM HAI, không dùng một cặp base_url/key chung:
# đổi model CHAT là đổi hành vi — đo lại được, hỏng thì thấy ngay.
# Đổi model EMBEDDING là đổi VẬT — mọi vector trong kho thành vô nghĩa, phải
# nạp lại toàn bộ, và mọi con số truy hồi đo trước đó bị cắt chuỗi. Hai việc
# khác hạng, gộp một biến là mời người vận hành làm việc thứ hai trong khi họ
# tưởng mình chỉ làm việc thứ nhất.
# ---------------------------------------------------------------------------
# CẤM HẲN hai biến của SDK. Không suy luận về chúng — chặn chúng.
#
# SDK openai tự đọc `OPENAI_BASE_URL` và `OPENAI_API_BASE` từ môi trường, và
# chúng THẮNG CẢ `base_url=None` truyền tường minh. Đo thật:
#     ChatOpenAI(api_key=...)                    -> dashscope-intl…/v1/
#     ChatOpenAI(api_key=..., base_url=None)     -> dashscope-intl…/v1/
#     OpenAIEmbeddings(api_key=..., base_url=None) -> dashscope-intl…/v1/
#
# ⟹ `_khoa_cho_nha_cung_cap` bên dưới KHÔNG đủ một mình: nó hỏi "CHÚNG TA có
# đổi đích đến không?" (`LLM_BASE_URL` có đặt không). Câu đúng là "ĐÍCH ĐẾN có
# đổi không?" — mà đích đến là HỢP của biến của ta VÀ biến của SDK. Đặt
# `OPENAI_BASE_URL` rồi để trống `LLM_API_KEY` là tái lập CHÍNH XÁC sự cố
# 17/08, im lặng, không lỗi khởi động.
#
# Và đó là thao tác TRỰC GIÁC NHẤT: bảo ai đó "trỏ hệ thống sang nhà cung cấp
# mới", thứ họ tìm đầu tiên là `OPENAI_BASE_URL`. Bản vá cũ chặn con đường CÓ
# TÀI LIỆU; con đường trực giác vẫn mở.
#
# Cấm thay vì hỗ trợ: dự án đã có biến riêng cho TỪNG VAI (`LLM_*` cho chat,
# `EMBEDDING_*` cho embedding). Biến của SDK áp cho CẢ HAI cùng lúc, nên nó chỉ
# có thể ĐI VÒNG qua sự phân tách đó, không bao giờ phục vụ nó.
for _bien_cam in ("OPENAI_BASE_URL", "OPENAI_API_BASE"):
    if os.environ.get(_bien_cam):
        raise RuntimeError(
            f"{_bien_cam} bị CẤM trong dự án này.\n"
            f"  SDK đọc nó và nó THẮNG cả base_url truyền tường minh, nên nó đổi\n"
            f"  đích đến của CẢ chat lẫn embedding cùng lúc mà không cơ chế nào\n"
            f"  của ta nhìn thấy — đúng đường đã làm rò khoá OpenAI sang bên thứ\n"
            f"  ba ngày 17/08.\n"
            f"  Dùng LLM_BASE_URL (chat) hoặc EMBEDDING_BASE_URL (embedding)."
        )


def _khoa_cho_nha_cung_cap(ten_khoa: str, base_url: str | None) -> str | None:
    """Khoá chỉ được PHÉP rơi về OPENAI_API_KEY khi ĐÍCH ĐẾN vẫn là OpenAI.

    🔴 Bản đầu của tôi viết `os.environ.get("LLM_API_KEY") or OPENAI_API_KEY`
    VÔ ĐIỀU KIỆN. Với `LLM_BASE_URL` trỏ nhà cung cấp khác mà quên điền khoá,
    nó GỬI KHOÁ OPENAI SANG MÁY CHỦ BÊN THỨ BA. Đo thật: base_url dashscope +
    LLM_API_KEY trống -> khoá `sk-proj…` đi tới Alibaba.

    Không có lỗi nào bắn ra: bên kia chỉ trả 401, người vận hành đọc "401" rồi
    đi tìm sai chỗ, trong khi khoá production đã rời hệ thống.

    Một fallback chỉ an toàn khi ĐÍCH ĐẾN không đổi. Đổi đích mà giữ fallback
    là biến tiện lợi thành rò rỉ.
    """
    khoa = os.environ.get(ten_khoa)
    if khoa:
        return khoa
    if base_url:
        raise RuntimeError(
            f"Thiếu {ten_khoa} trong khi đã đặt base_url tới nhà cung cấp khác "
            f"({base_url}). KHÔNG tự dùng OPENAI_API_KEY thay thế — làm vậy là "
            f"gửi khoá OpenAI sang máy chủ của họ. Đặt {ten_khoa} trong .env."
        )
    return OPENAI_API_KEY


LLM_BASE_URL = os.environ.get("LLM_BASE_URL") or None

# Kênh cho khách khi agent KHÔNG phục vụ được và ta CỐ Ý không tạo vé (lỗi nhà
# cung cấp cần can thiệp: 401/403/400/404). Đây là lối đi duy nhất còn lại cho
# một khách có thể đang định báo gian lận — xem chú thích ở graph.py.
#
# Mặc định CỐ Ý là cụm chung chung, KHÔNG có số điện thoại: bịa một số tổng đài
# vào câu trả lời cho khách là vi phạm ràng buộc cứng 3 theo đúng nghĩa đen —
# khách sẽ GỌI vào đó. PO đặt `HOTLINE_CSKH` thì câu trả lời có số thật.
_hotline = os.environ.get("HOTLINE_CSKH", "").strip()

# Số có BẤM ĐƯỢC không — phép thử KHẲNG ĐỊNH, không phải danh sách chặn.
#
# 17/08 PO đặt `HOTLINE_CSKH=1900-XXXX (SỐ TẠM — CHƯA CẤU HÌNH)`: cố ý không
# bấm được, để ô đã điền mà vẫn tự khai là chưa cấu hình. Đúng cho vận hành —
# nhưng mã cũ nội suy THẲNG giá trị đó vào câu nói với khách, tức khách sẽ đọc
# "bạn liên hệ tổng đài chăm sóc khách hàng 1900-XXXX (SỐ TẠM — CHƯA CẤU HÌNH)".
#
# Nên chỗ này phải hỏi "giá trị này BẤM ĐƯỢC không", không phải "biến có được
# đặt không". Một danh sách chặn ("XXXX", "TODO", "chưa cấu hình"...) sẽ hụt ở
# placeholder thứ tư ai đó nghĩ ra; phép thử khẳng định thì không.
_CHU_SO_TOI_THIEU = 8
DIALABLE = bool(re.fullmatch(r"[0-9 ()+.\-]+", _hotline)) and \
    sum(c.isdigit() for c in _hotline) >= _CHU_SO_TOI_THIEU

# Khách CHỈ thấy số khi số bấm được. Không bấm được -> lùi về cụm chung chung,
# vì một số không gọi được còn tệ hơn không có số: nó biến "không có đường"
# thành "một đường dẫn tới hư không", và khách tưởng mình đã có lối đi.
KENH_HO_TRO_KHAC = (
    f"tổng đài chăm sóc khách hàng {_hotline}" if DIALABLE
    else "tổng đài chăm sóc khách hàng"
)
# `or OPENAI_MODEL` CÙNG HÌNH DẠNG với lỗ khoá ở trên, nhưng KHÔNG cần guard —
# ghi ra để người đọc sau phân biệt "đã cân nhắc" với "bỏ sót": tải trọng ở đây
# lành. Quên đặt thì ta hỏi nhà cung cấp mới một model tên "gpt-4o-mini" và
# nhận lỗi của họ. Có tiết lộ TA DÙNG GÌ, không tiết lộ BÍ MẬT nào.
LLM_MODEL = os.environ.get("LLM_MODEL") or OPENAI_MODEL
LLM_API_KEY = _khoa_cho_nha_cung_cap("LLM_API_KEY", LLM_BASE_URL)

# Trần token sinh ra. MẶC ĐỊNH None = KHÔNG truyền tham số -> y hệt hành vi
# hôm nay (dựa vào mặc định nhà cung cấp). CỐ Ý không đặt một con số:
# thêm trần ở đây sẽ CẮT NGẮN câu trả lời dài đang chạy tốt, tức sửa một bug
# chưa xảy ra bằng cách tạo một bug chắc chắn xảy ra.
#
# Vì sao cần cái knob này: model có reasoning (Qwen) tiêu token vào phần SUY
# NGHĨ trước khi sinh nội dung. Trần thấp -> tiêu hết vào suy nghĩ -> `content`
# RỖNG, và KHÔNG có lỗi nào. Khi đổi sang model như vậy, đặt biến này tường
# minh thay vì hy vọng mặc định của họ đủ.
# ⚠️ SỐ ĐO THEO MODEL — phần suy nghĩ thầm chiếm bao nhiêu token ĐẦU RA:
#     qwen3.7-plus  61%        qwen3.8-max  77%
# Càng cao thì trần này càng phải rộng. Siết nó để tiết kiệm tiền trên model
# reasoning là mua trả-lời-rỗng: model tiêu hết trần vào suy nghĩ rồi không
# còn chỗ sinh nội dung -> `TraLoiRongError` (graph.py). Tiết kiệm ở đây không
# giảm chi phí suy nghĩ, nó chỉ vứt bỏ phần đã trả tiền.
LLM_MAX_TOKENS = int(os.environ["LLM_MAX_TOKENS"]) if os.environ.get("LLM_MAX_TOKENS") else None

EMBEDDING_BASE_URL = os.environ.get("EMBEDDING_BASE_URL") or None
EMBEDDING_API_KEY = _khoa_cho_nha_cung_cap("EMBEDDING_API_KEY", EMBEDDING_BASE_URL)

# Số chunk gửi trong MỘT lời gọi embedding. LangChain mặc định 1000 — OpenAI
# nhận, Qwen từ chối: "batch size is invalid, it should not be larger than 10".
# Trần này KHÔNG có chuẩn chung giữa các nhà cung cấp, nên nó phải là biến.
# Mặc định 10 khi trỏ nhà cung cấp khác (giá trị an toàn nhất đã gặp), giữ
# nguyên mặc định thư viện cho đường OpenAI để không đổi vật.
EMBEDDING_BATCH_SIZE = int(os.environ.get("EMBEDDING_BATCH_SIZE") or (10 if EMBEDDING_BASE_URL else 0))

# --- THƯỚC của eval: GHIM BẰNG HẰNG SỐ, KHÔNG theo model sản phẩm ---------
# Một lượt adversarial có BA vai cùng gọi model:
#     ĐỐI TƯỢNG   agent bị đo        (run_agent_turn -> LLM_MODEL)
#     KÍCH THÍCH  kẻ tấn công giả lập (eval/_harness.py)
#     TRỌNG TÀI   người chấm          (eval/_llm_judge.py)
# Nếu cả ba đọc chung một biến thì đổi nhà cung cấp làm cả ba đổi cùng lúc, và
# `96/96 -> 94/96` không quy được nhân quả: agent yếu đi, kẻ tấn công mạnh
# lên, hay trọng tài chấm khác? Ba biến một số — đúng bẫy đã giết cặp
# 41,4/35,7, lần này nằm trong bộ đo AN TOÀN.
#
# CỐ Ý ghim vào chuỗi literal, KHÔNG `or OPENAI_MODEL`: cách đổi nhà cung cấp
# tự nhiên nhất của người vận hành là sửa `OPENAI_MODEL` trong `.env`, và nếu
# thước neo vào đó thì nó lặng lẽ đi theo vật. Thước phải đứng yên kể cả khi
# người ta đổi vật bằng con đường mình không lường trước.
#
# Đổi thước là quyết định RIÊNG, phải cố ý đặt biến, và phải chấm lại toàn bộ.
_THUOC_MAC_DINH = "gpt-4o-mini"
JUDGE_MODEL = os.environ.get("EVAL_JUDGE_MODEL") or os.environ.get("JUDGE_MODEL") or _THUOC_MAC_DINH
EVAL_SIM_MODEL = os.environ.get("EVAL_SIM_MODEL") or _THUOC_MAC_DINH

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
# Đọc từ env (mặc định GIỮ NGUYÊN 15) — thêm 2026-08-16 để dựng được instance
# test TTL ngắn. Vì sao đáng: tái lập lớp lỗi đua-refresh phải chờ tới cửa sổ
# 120s cuối của phiên, tức ~phút 13 mỗi lần; k=10 mất hơn 2 giờ. Với TTL=1
# phút thì k=30 gọn trong 20 phút, và test hồi quy vùng auth mới TỒN TẠI được
# — không ai cho CI chờ 13 phút một ca.
#
# ⚠️ HẠ giá trị này là HẠ MỘT CONTROL BẢO MẬT (AUTH5-02, rút từ 8h xuống 15
# phút theo NIST SP 800-63B-4/PSD2). Chỉ dùng cho instance TEST chạy dưới
# project name RIÊNG. KHÔNG bao giờ set trên `.env` của stack thật.
JWT_ACCESS_EXPIRE_MINUTES = int(os.environ.get("JWT_ACCESS_EXPIRE_MINUTES", "15"))

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
# Đọc từ env `EMBEDDING_MODEL`. MỘT hằng số cho MỘT thứ — cố ý không thêm tên
# thứ hai `EMBEDDING_MODEL` ở tầng Python, hai tên cho một giá trị là cách
# chắc chắn để sau này chúng lệch nhau.
#
# ⚠️ ĐỔI BIẾN NÀY = ĐỔI VẬT, và store.py CÓ RÀO (xem `_dong_dau`): dấu phiên
# bản kho trước đây chỉ ghi `chuan_hoa`, KHÔNG ghi model. Nếu để nguyên vậy thì
# đổi model embedding sẽ làm mọi vector lệch một vế mà `kiem` vẫn xanh —
# search trả đủ k, kết quả sai, không triệu chứng. Đúng lớp lỗi đòn 2.
RAG_EMBEDDING_MODEL = os.environ.get("EMBEDDING_MODEL") or "text-embedding-3-small"
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

# ---------------------------------------------------------------------------
# F-30 — LangSmith/LangChain tracing TẮT MINH THỊ (2026-08-15)
# ---------------------------------------------------------------------------
# Gói `langsmith` đi kèm `langchain` nên đã có sẵn trong môi trường. Tracer
# NATIVE của LangChain bật hoàn toàn bằng biến môi trường — không cần một dòng
# code nào — và nó gửi thẳng prompt/response lên LangSmith Cloud.
#
# Vì sao đây là vấn đề riêng, không phải trùng với observability đã có: lớp
# `_scrub_and_truncate` của dự án nằm trong callback TỰ VIẾT
# (src/observability/langchain_callback.py). Tracer native KHÔNG gọi qua lớp
# đó — nó là một kênh xuất dữ liệu SONG SONG, đi vòng qua toàn bộ PII
# scrubbing, và bật được mà không để lại vết nào trong git.
#
# Đặt false MINH THỊ ở đây để biến một cấu-hình-NGẦM thành một quyết-định-HIỆN:
# muốn bật thật thì phải sửa dòng này ⟹ có diff, có review, có hồ sơ theo
# NĐ 13/2023 Điều 25 (chuyển dữ liệu cá nhân ra ngoài). `setdefault` chứ không
# gán đè: người vận hành vẫn cố ý bật được bằng env var, nhưng mặc định im
# lặng thì không bao giờ là "bật".
os.environ.setdefault("LANGCHAIN_TRACING_V2", "false")
os.environ.setdefault("LANGSMITH_TRACING", "false")  # tên mới của cùng cờ
