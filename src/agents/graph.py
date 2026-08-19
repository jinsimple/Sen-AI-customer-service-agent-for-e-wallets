"""LangGraph agent cho luồng khiếu nại lõi (PRD §6) — entrypoint duy nhất
`run_agent_turn()`, gọi từ `POST /agent/chat` (src/api/main.py).

Lưu ý API: `langgraph.prebuilt.create_react_agent` đã deprecated ở bản
langgraph 1.2.10/langchain 1.3.14 đang cài — dùng `langchain.agents.create_agent`
thay thế (tham số prompt tên là `system_prompt`, không phải `prompt`)."""
from __future__ import annotations

import datetime as dt
import json
import logging
import os
import re
import time
from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import TimeoutError as FutureTimeoutError
from typing import Any

from langchain.agents import create_agent
from langchain_core.messages import AIMessage, HumanMessage, ToolMessage
from langchain_openai import ChatOpenAI
from langgraph.checkpoint.memory import MemorySaver
from langgraph.errors import GraphRecursionError
from openai import (
    APIError,
    AuthenticationError,
    BadRequestError,
    NotFoundError,
    PermissionDeniedError,
    RateLimitError,
)
from opentelemetry.trace import Status, StatusCode
from sqlalchemy.orm import Session

from src.agents.nodes.investigation_log import write_investigation_logs_for_ticket
from src.agents.output_filter import loc_dau_ra, tin_hieu_lo_chi_thi
from src.agents.phan_luong import BAM_LUAT, DUONG_DAY_DU, DUONG_NHE, TRA_LOI_NHE, phan_luong
from src.agents.prompt import bam_mau_prompt, build_system_prompt
from src.agents.tools.customer_tools import TurnGuard, build_customer_tools
from src.config import (
    AGENT_TURN_TIMEOUT_SECONDS,
    DATABASE_URL,
    DB_KIND,
    KENH_HO_TRO_KHAC,
    LLM_API_KEY,
    LLM_BASE_URL,
    LLM_MAX_TOKENS,
    LLM_MODEL,
    OPENAI_MAX_RETRIES,
    OPENAI_TIMEOUT_SECONDS,
    PHAN_LUONG_BAT,
    SUY_LUAN_BAT,
)
from src.cong_ra_ngoai import http_client_dung_chung
from src.dau_ma_nguon import CACH_BAM, nhan_luc_dung
from src.db.models import Complaint, Ticket, User
from src.observability.langchain_callback import OTelTracingCallbackHandler
from src.observability.pii import scrub_pii
from src.observability.so_usage import ghi_usage
from src.observability.tracing import get_tracer
from src.services.complaint_intake import flag_human_handoff
from src.services.emotion_signals import danh_gia_luot
from src.tools.base import ToolError

_tracer = get_tracer("fin05.agent")
_logger = logging.getLogger("fin05.agents.graph")

# CONSUME-002 (FIN05_QA_TestCases.jsonl, OWASP LLM10:2025 Unbounded
# Consumption) — mặc định thật của langgraph đang cài (xác nhận trực tiếp
# `langgraph._internal._config.DEFAULT_RECURSION_LIMIT`) là 10007 bước, thực
# chất tương đương KHÔNG có giới hạn (đốt hết ngân sách OpenAI/timeout rất
# lâu trước khi chạm ngưỡng đó nếu agent kẹt vòng lặp gọi tool mơ hồ liên
# tục). 20 đủ cho vài vòng ReAct thật (LLM suy luận + gọi tool xen kẽ), thấp
# hơn nhiều để chặn lặp vô hạn.
_AGENT_RECURSION_LIMIT = 20


class TraLoiRongError(RuntimeError):
    """Model trả nội dung rỗng vì HẾT TRẦN TOKEN — lỗi cấu hình của TA.

    Có lớp riêng để bộ đo phân biệt được nó với mọi lỗi khác. Nuốt nó thành
    một câu trả lời rỗng nghĩa là thước sẽ ghi "model trả lời kém" cho một
    lỗi hạ tầng của chính ta — tính nhầm lỗi của mình thành lỗi nhà cung cấp.
    """

# JSON schema của 5 tool gửi kèm MỌI lượt gọi model — hằng số, đo 2026-08-16.
# Đổi khi thêm/bớt tool. Xem giải thích ở chỗ dựng `usage["input_chars"]`.
_CHARS_TOOL_SCHEMA = 6773

# Số tool bind ở lần dựng agent gần nhất trong tiến trình này. Ghi bởi tầng
# DỰNG REQUEST, không phải bởi tầng quyết định — xem chú thích tại chỗ gán.
_SO_TOOL_GUI = 0

# Suy luận có BẬT ở lần dựng model gần nhất không — đọc ngược từ đối tượng
# model, không từ config. Xem chú thích tại chỗ gán.
_SUY_LUAN_GUI = True

# Kích thước lược đồ tool ĐO ĐƯỢC ở lần dựng gần nhất — thay hằng số gõ tay.
_CHARS_TOOL_SCHEMA_THAT = _CHARS_TOOL_SCHEMA

def _giay_cho_lai(loi: Exception) -> float | None:
    """Moi so giay nha cung cap BAO, khong tu doan.

    OpenAI tra nguyen van "Please try again in 1.381s" trong than loi. Doc
    dung so do de noi voi khach, thay vi bia mot con so nghe hop ly — cung
    tinh than rang buoc cung 3: con so noi ra phai co nguon.

    Khong tra duoc thi tra None, va cau tra loi noi "sau it giay" thay vi mot
    con so gia.
    """
    m = re.search(r"try again in ([0-9.]+)s", str(loi))
    return float(m.group(1)) if m else None


# ═══ Phân loại lỗi NHÀ CUNG CẤP ════════════════════════════════════════════
#
# `APIError` là ranh giới CHÍNH XÁC của họ này: mọi lỗi nhà cung cấp đều kế
# thừa nó (đã kiểm cây thừa kế trên openai==3.0.0 đang chạy: 401/403/400/404/
# 429/5xx đi qua APIStatusError, timeout/rớt mạng đi qua APIConnectionError,
# cả hai đều dưới APIError), và KHÔNG lỗi nào của ta lọt vào. Bắt rộng hơn
# (`Exception`) sẽ nuốt cả bug của chính mình thành "hệ thống bận".
#
# VÌ SAO CẦN: trước bản này `except` khoá vào ĐÚNG MỘT TÊN — `RateLimitError`.
# Nhưng thứ cần xử lý không phải một tên, mà là TRẠNG THÁI "nhà cung cấp không
# phục vụ lượt này". 429 chỉ là một trong các cách họ từ chối; 6 lớp còn lại
# rơi thẳng ra HTTP 500 trần. tester quan sát được trên đường thật khi hạn mức
# Qwen cạn giữa buổi: hết giờ -> 200 + vé fallback, nhưng 403 -> 500, không vé,
# không gì cả.
#
# ⚠️ TUYỆT ĐỐI KHÔNG nối họ này vào nhánh fallback-TẠO-VÉ bên dưới. Lý do đã
# đúng với 429 (chú thích ở nhánh đó), và MẠNH HƠN với 401/403: hết hạn mức là
# hỏng TOÀN CỤC, nó đánh mọi khách cùng lúc ⟹ tạo vé nghĩa là một vé cho mỗi
# khách đang online. Trong buổi 150 người đó là 150 vé ma trong một phút, cho
# những khiếu nại KHÔNG TỒN TẠI — và làm loãng đúng hàng chờ mà vé "AI bó tay"
# cần được nhìn thấy.

# Bốn lớp mà KHÁCH THỬ LẠI BAO NHIÊU LẦN CŨNG KHÔNG HẾT — phải có người xử.
# 400/404 là lỗi CỦA TA (sai model/tham số), không phải sự cố nhà cung cấp;
# xếp chung ở đây vì đứng từ phía khách chúng giống hệt nhau: chờ không hết.
_LOI_CAN_CAN_THIEP = (
    AuthenticationError,      # 401 khoá sai / vừa xoay / hết hạn
    PermissionDeniedError,    # 403 hết hạn mức HOẶC sai quyền
    BadRequestError,          # 400 lỗi của ta
    NotFoundError,            # 404 lỗi của ta
)

# Dấu hiệu "hết tiền" trong thân thông báo. CỐ Ý chỉ dùng cho MỘT trường log,
# không bao giờ cho thứ khách nhìn thấy:
#   `403 free quota exhausted` của DashScope CÙNG LỚP PermissionDeniedError với
#   403 sai quyền. Tách hai ca bắt buộc phải so chuỗi -> mong manh theo từng
#   nhà cung cấp, và hỏng IM LẶNG khi họ đổi câu chữ.
#   Luật: một phép phân biệt MONG MANH chỉ được điều khiển hậu quả RẺ. Sai ở
#   đây tốn một nhãn log lệch (tự lộ ngay khi người vận hành mở ra xem). Nếu
#   nó điều khiển "khách thấy gì" thì một lần đổi câu chữ = khách nhận 500.
_DAU_HIEU_HET_HAN_MUC = ("quota", "exhaust", "insufficient", "balance", "arrear", "unpurchased")


def _mo_ta_loi_nha_cung_cap(loi: APIError) -> dict[str, object]:
    """Trường để hồi cứu sự cố. KHÔNG chứa thân thông báo thô.

    Thân thô có thể mang khoá hoặc định danh nội bộ; ta chỉ rút ra một cờ
    boolean từ nó. Đủ để người vận hành biết "hết tiền hay sai khoá", không đủ
    để rò thứ gì ra log.
    """
    than = (str(getattr(loi, "message", "") or str(loi))).lower()
    return {
        "lop_loi": type(loi).__name__,
        "ma_trang_thai": getattr(loi, "status_code", None),
        "nha_cung_cap": LLM_BASE_URL or "openai",
        "model": LLM_MODEL,
        "can_can_thiep": isinstance(loi, _LOI_CAN_CAN_THIEP),
        "co_dau_hieu_het_han_muc": any(d in than for d in _DAU_HIEU_HET_HAN_MUC),
        # `request_id` của nhà cung cấp: CHÍNH thứ bộ phận hỗ trợ của họ hỏi khi
        # ta khiếu nại hoá đơn/hạn mức — không có nó thì hồi cứu với họ là bất
        # khả (security ④). Không phải bí mật, không phải PII. CHỈ dùng trong hồ
        # sơ nội bộ, KHÔNG bao giờ đưa ra khách.
        "request_id_ncc": getattr(loi, "request_id", None),
    }


def _ghi_so(kq: dict, thread_id: str | None, user_id: str) -> None:
    """Ghi MỘT dòng sổ usage cho MỌI đường ra của `run_agent_turn`.

    Đặt ở một hàm vì bài học vừa trả giá: bản đầu tôi gắn `ghi_usage` ngay
    trước `return` cuối cùng — và MỌI đường fallback (429 · lỗi nhà cung cấp ·
    hết giờ · recursion) `return` SỚM, không bao giờ tới đó. Sổ kế toán vắng
    mặt đúng những lượt HỎNG, tức nó đếm thiếu số lượt và đọc thành "ít lượt
    hơn thực tế" chứ không thành một khoảng trống nhìn thấy được.

    Cùng hình dạng với ca `flag_human_handoff` sáng nay: một cơ chế đúng, gắn
    đúng chỗ nó được nghĩ ra, và không ai đi tìm chỗ thứ hai cùng lớp. Ở đây
    "chỗ thứ hai" là bốn `return` khác.

    `ly_do_fallback` lấy TỪ CHÍNH dict trả về, không dựng lại — hai nguồn sẽ
    lệch nhau, và lệch trong im lặng.
    """
    u = kq.get("usage") or {}
    ghi_usage({
        "ts": dt.datetime.utcnow().isoformat() + "Z",
        "thread_id": thread_id or user_id,
        "model": LLM_MODEL,
        # ĐO Ở ĐÂU. tester phải loại trừ ngăn xếp ttl bằng đường gián tiếp vì
        # "không bản ghi nào ghi URL của lượt đo" — cùng họ với mốc-thời-gian
        # của security. Một con số không tự khai NÓ ĐO Ở ĐÂU thì lần sau lại
        # phải điều tra như lần này.
        "base_url": LLM_BASE_URL or "openai",
        # VẬT nào sinh ra số này — KÈM cách băm, vì một chuỗi 12 hex không tự
        # khai nguồn gốc của nó. 17/08 đã mất một vòng vì tôi so md5 với sha256
        # của người khác rồi kết luận ".env đổi 4 lần". Sổ này được đọc lại sau
        # nhiều tháng, là chỗ tệ nhất để bỏ nhãn.
        "bam_ma_nguon": nhan_luc_dung(),
        "cach_bam": CACH_BAM,
        "so_luot_goi_model": u.get("so_luot_goi_model"),
        "input_tokens": u.get("input_tokens"),
        "output_tokens": u.get("output_tokens"),
        "cached_input_tokens": u.get("cached_input_tokens"),
        "reasoning_tokens": u.get("reasoning_tokens"),
        "input_chars": u.get("input_chars"),
        "so_tool_call": len(kq.get("tool_calls") or []),
        "ly_do_fallback": kq.get("ly_do_fallback"),
        # Ba trường TRIỆU CHỨNG, luôn có mặt (None ở lượt thường) — khoá thiếu
        # và khoá null đọc khác nhau ở mọi công cụ phân tích, và "thiếu khoá"
        # sẽ bị đọc thành "chưa bao giờ hỏng".
        "lop_loi_ncc": (kq.get("trieu_chung") or {}).get("lop_loi_ncc"),
        "ma_trang_thai_ncc": (kq.get("trieu_chung") or {}).get("ma_trang_thai_ncc"),
        "giay_da_troi": (kq.get("trieu_chung") or {}).get("giay_da_troi"),
        "duong": kq.get("duong"),
        "so_tool_schema_gui": u.get("so_tool_schema_gui"),
        # TRẠNG THÁI THẬT của lượt, không phải giá trị cờ config — nếu không có
        # trường này thì dòng R2 và R3 trong sổ KHÔNG phân biệt được khi đọc
        # lại sau nhiều tháng, mà sổ sinh ra để được đọc lại sau nhiều tháng.
        "suy_luan_gui": u.get("suy_luan_gui"),
        "co_ticket": bool(kq.get("ticket_id")),
    })


def _ly_do_fallback(loi: Exception) -> str:
    """Phân loại vì sao rơi vào fallback. Trả chuỗi, không bao giờ None.

    Nhánh mặc định `"khac"` là CÓ CHỦ ĐÍCH dù hôm nay nó không bao giờ bắn (chỉ
    có đúng một `except` dẫn tới fallback). Nó tồn tại cho NGÀY ai đó thêm đường
    fallback thứ ba mà quên khai: tester nhận được một giá trị lạ nhìn thấy ngay,
    thay vì một khoảng trống mà họ sẽ đọc nhầm thành "lượt bình thường".

    LƯU Ý cho người đọc biên bản: 429 quá tải HIỆN ĐANG đội lốt `"timeout"` —
    thời gian ngủ theo `retry_after` ăn vào ngân sách AGENT_TURN_TIMEOUT_SECONDS
    nên một lỗi tự-phục-hồi-được hiện ra như hết giờ. Tách nó cần một giá trị
    `"qua_tai"` và phải bắt RateLimitError ở tầng này — việc riêng, đã vào hồ sơ
    pilot, KHÔNG làm ở commit này.
    """
    if isinstance(loi, FutureTimeoutError):
        return "timeout"
    if isinstance(loi, GraphRecursionError):
        return "recursion_limit"
    return "khac"


def _trieu_chung_loi(loi: BaseException | None) -> dict[str, object]:
    """TRIỆU CHỨNG của lỗi, tách khỏi KẾT LUẬN về lỗi (Luật H).

    Vì sao cần, bằng ca thật: sổ ghi `ly_do_fallback = "nha_cung_cap_can_can_thiep"`.
    Đó là một KẾT LUẬN — nó nói *phải làm gì*, không nói *nhà cung cấp đã trả
    lời gì*. Hai sự cố khác hẳn nhau (`401` khoá sai · `403` hết hạn ngạch ·
    `404` sai tên model) đổ chung vào một nhãn, và cách xử ba ca đó KHÁC NHAU
    hoàn toàn — một cái nạp tiền, một cái sửa khoá, một cái sửa cấu hình.
    Người trực sự cố đọc sổ sẽ không phân biệt được, và sẽ đi thử cả ba.

    ⟹ Mã trạng thái đi VÀO SỔ, cạnh kết luận, không thay thế nó. Hai trường,
    hai câu hỏi: *"nhà cung cấp nói gì"* và *"ai phải làm gì"*.

    🔴 `None` ở đây nghĩa **KHÔNG ĐỌC ĐƯỢC** (lỗi không mang mã trạng thái —
    hết giờ, vòng lặp), KHÔNG phải "mã 0". Cùng quy ước với `input_tokens`.
    """
    if loi is None:
        return {"lop_loi_ncc": None, "ma_trang_thai_ncc": None}
    ma = getattr(loi, "status_code", None)
    return {
        "lop_loi_ncc": type(loi).__name__,
        # ép về int hoặc None — vài SDK trả chuỗi, và một chuỗi lọt vào sổ sẽ
        # làm mọi phép lọc `>= 500` im lặng trả rỗng thay vì báo lỗi.
        "ma_trang_thai_ncc": int(ma) if isinstance(ma, (int, str)) and str(ma).isdigit() else None,
    }


def _reply_goc_cho_eval(reply_goc: str, nhom_khop: list[str]) -> dict:
    """Câu TRƯỚC KHI LỌC — chỉ khi bật cờ, chỉ khi thật sự có chặn.

    Vì sao tester cần: `loc_dau_ra=["O3"]` cho biết bộ lọc ĐÃ chặn, nhưng không
    cho biết chặn ĐÚNG hay siết NHẦM. Không đọc được thứ bị nuốt thì mọi ca bị
    chặn đều "đạt" theo bộ chấm (câu an toàn không vi phạm bất biến nào), và
    lượt "sau" trông đẹp hơn lượt "trước" trong khi bộ lọc có thể đang siết nhầm
    hàng loạt — confound hướng-có-lợi, loại nguy hiểm nhất.

    Vì sao KHÔNG bật mặc định: câu này chính là thứ bộ lọc tồn tại để không cho
    ra ngoài. Ship nó trong envelope production là tự mở lại đúng cái cửa vừa
    đóng, và nó sẽ chảy tiếp vào log/trace/bên thứ ba. Fail-closed: thiếu biến
    môi trường thì KHÔNG trả.
    """
    if os.environ.get("FIN05_EVAL_GIU_REPLY_GOC") != "1" or not nhom_khop:
        return {}
    return {"reply_truoc_loc": reply_goc}


def _nang_uu_tien_theo_cam_xuc(session: Session, *, ticket_id: str) -> None:
    """ES bật -> nâng `complaints.priority`, TRẦN LÀ `high`. CHỈ NÂNG.

    KHÔNG BAO GIỜ lên `critical`: mức đó thuộc về FS-06 (nghi gian lận). Cho bức
    xúc leo lên cùng mức nghi gian lận là làm hỏng ĐÚNG hàng đợi quan trọng nhất
    — người trực hết phân biệt được "khẩn vì rủi ro tiền" với "khẩn vì khách
    đang giận", và họ sẽ mất niềm tin vào chính cái nhãn critical.

    KHÔNG BAO GIỜ HẠ: ES tắt ở lượt sau không có nghĩa vấn đề nhẹ đi. Hạ xuống
    là xoá dấu vết một lần khách đã căng, mà CSKH cần thấy điều đó khi mở hồ sơ.
    """
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        return
    complaint = session.get(Complaint, ticket.complaint_id)
    if complaint is None or complaint.priority in ("high", "critical"):
        return
    complaint.priority = "high"
    session.flush()


def _build_checkpointer():
    """Nơi lưu bộ nhớ hội thoại của agent — quyết định KIẾN TRÚC, không chỉ kỹ thuật.

    TRƯỚC 2026-08-13: `MemorySaver()` giữ toàn bộ hội thoại trong RAM của MỘT
    process. Hệ quả kéo dài suốt dự án:
      - Backend BẮT BUỘC chạy đúng 1 worker (ghi rõ trong Dockerfile). Máy 10
        vCPU chỉ dùng được 1 — lãng phí 90% năng lực, và 150 người dùng đồng
        thời chia chung một event loop duy nhất.
      - Restart backend = MỌI khách mất sạch ngữ cảnh giữa chừng. Với buổi test
        150 người, một lần deploy/crash là hỏng cả buổi.

    PostgresSaver đưa state ra ngoài process (đúng nguyên tắc "stateless
    processes" của 12-Factor), mở đường cho multi-worker VÀ giúp hội thoại sống
    sót qua restart.

    FALLBACK CÓ CHỦ ĐÍCH, KHÔNG IM LẶNG: test chạy trên SQLite (conftest tạo
    engine tạm riêng mỗi test) — PostgresSaver không chạy được ở đó. Rơi về
    MemorySaver khi DB không phải Postgres là ĐÚNG cho test, nhưng phải GHI LOG
    rõ ràng, không lặp lại bài học DATABASE_URL (ADR-013): một fallback im lặng
    từng làm hệ thống âm thầm tách đôi database.

    Xem ADR-014.
    """
    if DB_KIND != "postgresql":
        _logger.warning(
            "checkpointer_in_memory",
            extra={"db_kind": DB_KIND, "ly_do": "DB không phải Postgres — hội thoại "
                   "chỉ nằm trong RAM, mất khi restart, KHÔNG chạy được multi-worker. "
                   "Bình thường với test/SQLite; nếu thấy dòng này ở production là SAI."},
        )
        return MemorySaver()

    from langgraph.checkpoint.postgres import PostgresSaver
    from psycopg_pool import ConnectionPool

    # DATABASE_URL ở dạng SQLAlchemy (postgresql+psycopg2://) — psycopg3 mà
    # langgraph dùng cần dạng chuẩn (postgresql://). Đổi ở đây thay vì bắt
    # người vận hành khai 2 biến dễ lệch nhau.
    conninfo = DATABASE_URL.replace("postgresql+psycopg2://", "postgresql://", 1)
    pool = ConnectionPool(
        conninfo=conninfo,
        max_size=_CHECKPOINT_POOL_MAX,
        # autocommit BẮT BUỘC: PostgresSaver tự quản giao dịch của nó, để
        # psycopg mở transaction ngầm sẽ giữ khoá và treo khi nhiều worker ghi.
        kwargs={"autocommit": True, "prepare_threshold": 0},
        open=True,
    )
    saver = PostgresSaver(pool)
    saver.setup()  # idempotent — tự tạo bảng checkpoint nếu chưa có
    global _CHECKPOINT_POOL
    _CHECKPOINT_POOL = pool  # giữ tham chiếu để đóng sạch lúc shutdown
    _logger.info("checkpointer_postgres", extra={"pool_max": _CHECKPOINT_POOL_MAX})
    return saver


def close_checkpointer() -> None:
    """Đóng pool của checkpointer — gọi từ FastAPI shutdown (src/api/main.py).

    ConnectionPool của psycopg chạy thread nền; không đóng tường minh thì lúc
    interpreter thoát sẽ ném `PythonFinalizationError: cannot join thread at
    interpreter shutdown` (đã gặp thật lúc verify). Với server chạy dài thì
    lỗi này chỉ bẩn log lúc tắt, nhưng graceful shutdown là yêu cầu bắt buộc
    của checklist đóng gói production — và pool không đóng còn giữ kết nối
    Postgres cho tới khi TCP timeout, ăn vào max_connections khi deploy liên tục.
    """
    global _CHECKPOINT_POOL
    if _CHECKPOINT_POOL is not None:
        try:
            _CHECKPOINT_POOL.close()
            _logger.info("checkpointer_pool_closed")
        except Exception as e:  # noqa: BLE001 — shutdown không được ném lỗi ra ngoài
            _logger.warning("checkpointer_pool_close_failed", extra={"loi": repr(e)})
        finally:
            _CHECKPOINT_POOL = None


# Pool riêng cho checkpointer, TÁCH khỏi pool của SQLAlchemy: hai thứ này có
# nhịp truy cập khác nhau (checkpoint ghi mỗi bước ReAct, ORM đọc/ghi nghiệp vụ)
# và gộp chung sẽ làm nghẽn lẫn nhau. Tổng kết nối = workers x (pool ORM + pool
# này) phải nhỏ hơn max_connections của Postgres (mặc định 100).
_CHECKPOINT_POOL_MAX = int(os.environ.get("CHECKPOINT_POOL_MAX", "5"))
_CHECKPOINT_POOL = None  # gán trong _build_checkpointer(), đóng ở close_checkpointer()

# Singleton module-level: agent được build lại mỗi request (session/tools gắn
# với request đó), nhưng checkpointer dùng chung 1 instance nên lịch sử hội
# thoại nối tiếp được qua nhiều request cùng thread_id.
_CHECKPOINTER = _build_checkpointer()

# Sentinel — phân biệt "không truyền otp_verified_at" (backward-compat: coi như
# vừa xác thực XONG, dùng bởi eval harness/test hiện có vốn giả định "khách đã
# xác thực OTP trước khi vào chat") với "truyền None thật" (current_user thật
# CHƯA TỪNG xác thực — /agent/chat luôn truyền tường minh, xem src/api/main.py).
# Tính "now" lúc GỌI HÀM (không phải lúc module nạp) để không lệch thời gian
# nếu test suite chạy lâu.
_ALWAYS_FRESH = object()


# ---------------------------------------------------------------- nguồn O3
# Nhánh LỖI của tool bị loại khỏi nguồn (điều kiện Đ1 của Bảo Mật,
# docs/security/2026-08-18-dinh-hang-ban-va-A-o3-toolmessage-lich-su.md §3):
# nhánh error echo nguyên văn THAM SỐ DO MODEL TỰ ĐẶT (vd
# `create_ticket.py:42 "complaint_type không hợp lệ: {complaint_type}"`), nên
# một mã/số agent BỊA ở lượt N-1, tool từ chối, echo nó vào ToolMessage — nếu
# nhánh đó lọt vào nguồn thì lượt N nhắc lại đúng mã bịa ấy sẽ được O3 coi là
# "đã truy được về tool", cấp giấy thông hành vĩnh viễn cho một số KHÔNG THẬT.
#
# ĐÃ TỪNG là allow-list `status in {found, not_found, multiple_matches}` —
# RÚT, vì tiền đề sai: Lead [ĐO] 3/5 tool (get_customer_history · create_ticket
# · request_human_handoff) KHÔNG có khoá `status` ở TOP-LEVEL trên đường THÀNH
# CÔNG (status nằm lồng trong từng phần tử, hoặc không tồn tại). Allow-list
# theo đúng chữ sẽ loại sạch payload thành công của CẢ BA tool đó khỏi nguồn —
# và `get_customer_history` chính là tool đứng sau câu verify "xem giao dịch
# gần đây", nên bản vá sẽ KHÔNG chữa được ca nó dựng ra để chữa.
# `contracts/agent-tools.yaml:65,94,106` cũng khai `output.status` cho CẢ BA
# tool đó (`get_customer_history`/`create_ticket`/`request_human_handoff`) mà
# runtime KHÔNG phát — allow-list cũ tin đúng nguồn sự thật của dự án, và
# nguồn đó LỆCH runtime. Không ai chế ra tiền đề sai từ không khí: đây là hạng
# mù ADR-027 — checker `test_invariants` so KHAI-BÁO với KHAI-BÁO (contract ↔
# CHECK constraint/route), chưa bao giờ so contract với PAYLOAD THẬT lúc chạy.
#
# Deny-list `status == "error"` — vị ngữ này NEO VÀO HÀNH VI QUAN SÁT ĐƯỢC,
# KHÔNG NEO VÀO CONTRACT (bài học vừa trả giá ở trên).
#
# [ĐO] 19/08, `grep -rn '"status": "error"' src/agents/tools/customer_tools.py`
# → 9 điểm trả lỗi (`:597 :601 :637 :819 :840 :873 :919 :947 :997`), 0 payload
# thành công mang khoá này. `:637` là hằng số `_CHI_THI_DUNG_LAP` DÙNG LẠI, trả
# về ở `:777` (chỉ thị dừng livelock) — không phải `return {...}` inline, nên
# nó lọt khỏi BA lần quét độc lập trước đó (Review, Lead, tôi) cùng đếm ra 8:
# cả ba đều quét theo hình dạng `return {...}`, không theo hình dạng hằng số.
#
# Con số trên là ẢNH CHỤP, SẼ LỆCH LẠI khi có tool thứ 6 hoặc một nhánh lỗi
# mới (đúng Luật N: một con số ĐẾM phải kèm phép đếm; đúng Luật P: con số làm
# cũ phải niêm, không phải mốc neo vĩnh viễn). Thứ giữ tính chất này đúng VỀ
# SAU là ca ⑩ của QA/QC (canh mọi đường trả lỗi thật đều mang `status:"error"`)
# — KHÔNG phải dòng comment này.
_TRANG_THAI_LOI_TOOL = "error"

# Tool được gom kết quả LỊCH SỬ vào nguồn. Khai TƯỜNG MINH ở đúng một chỗ để
# thu hẹp phạm vi sau này là sửa một dòng, không phải đọc lại vòng lặp: Bảo Mật
# đã cân trục "payload có echo tham số model tự đặt không" và chỉ ra nhánh error
# là kênh rửa số bịa (đóng bằng allow-list trên), nhưng nếu trục ấy được cân lại
# cho tool GHI thì chỗ sửa là dòng dưới.
TOOL_GOM_LICH_SU = frozenset({
    "lookup_transaction",
    "get_customer_history",
    "create_ticket",
    "request_human_handoff",
    "search_policy",
})


def rap_nguon_o3(all_messages: list, tool_calls_out: list[dict]) -> str:
    """Ráp kênh NGUỒN (JSON) cho luật xuất xứ của O3.

    Gồm HAI phần, và ranh giới giữa chúng là có chủ đích:

    · `tool_calls_out` — kết quả tool của LƯỢT NÀY, giữ nguyên hình dạng cũ
      (gồm cả `args`).
    · kết quả tool của các LƯỢT TRƯỚC trong cùng hội thoại — CHỈ phần `result`,
      **không** gom `args`. Ràng buộc cứng 3 đòi số agent nói ra truy được về
      một kết quả tool CÓ THẬT; `args` là tham số MODEL TỰ ĐẶT, không phải thứ
      hệ thống trả về. Gom nó là để model tự cấp căn cứ cho chính nó, xuyên
      lượt — đúng cửa rửa số mà Đ1 đóng, chỉ đi bằng trường khác.

    KHÔNG gom `AIMessage`: lời agent không phải nguồn hợp lệ, gom vào là O3 tự
    chứng thực đầu ra của chính mình.

    Vì sao cần phần lịch sử (bản vá A): kênh nguồn cũ chỉ nạp payload của lượt
    hiện tại, nên một lượt agent trả lời từ trí nhớ (không gọi lại tool) làm mọi
    mã/số đã tra ở lượt trước thành "không truy được" -> O3 chặn OAN. Ràng buộc
    cứng 3 nói "một kết quả tool có thật", KHÔNG nói "của lượt này".
    """
    lich_su: list[dict] = []
    for m in all_messages:
        if not isinstance(m, ToolMessage):
            continue
        if getattr(m, "name", None) not in TOOL_GOM_LICH_SU:
            continue
        try:
            payload = json.loads(m.content)
        except (json.JSONDecodeError, TypeError, ValueError):
            continue  # không parse được -> KHÔNG phải nguồn (fail-closed)
        if not isinstance(payload, dict):
            continue
        if payload.get("status") == _TRANG_THAI_LOI_TOOL:
            continue
        lich_su.append(payload)
    return json.dumps(
        {"luot_nay": tool_calls_out, "luot_truoc": lich_su},
        ensure_ascii=False,
        default=str,
    )


def _build_agent(
    session: Session,
    *,
    user_id: str,
    customer_name: str,
    otp_verified_at: float | None,
    guard: TurnGuard | None = None,
):
    model = ChatOpenAI(
        # LLM_* fallback ve OPENAI_* (src/config.py) -> khong dat gi thi hanh vi
        # y het truoc. `base_url=None` la mac dinh cua SDK, khong phai mot gia
        # tri dac biet can xu ly rieng.
        #
        # `http_client` DUNG CHUNG voi duong embedding (src/rag/store.py) —
        # xem src/cong_ra_ngoai.py. Day la noi DUY NHAT moi loi goi ra nha cung
        # cap di qua, nen no la cho duy nhat co cho chot chan + bo dem. Dat o
        # tang nay con thay ca luot SDK TU RETRY (max_retries duoi day): dem o
        # tang tren SDK ghi 1 cho 3 lan ban ra day.
        http_client=http_client_dung_chung(),
        model=LLM_MODEL,
        temperature=0.2,
        api_key=LLM_API_KEY,
        base_url=LLM_BASE_URL,
        # Chỉ truyền khi CÓ đặt — `max_tokens=None` và "không truyền" khác nhau
        # ở một số client. Xem LLM_MAX_TOKENS trong config.py.
        **({"max_tokens": LLM_MAX_TOKENS} if LLM_MAX_TOKENS else {}),
        timeout=OPENAI_TIMEOUT_SECONDS,
        max_retries=OPENAI_MAX_RETRIES,
        # T3 · chỉ TRUYỀN khi TẮT. Không truyền gì khi bật = hành vi cũ y hệt,
        # không phải "truyền enable_thinking=True" (hai thứ đó khác nhau ở một
        # số nhà cung cấp, và ta không có lý do để thử).
        **({} if SUY_LUAN_BAT else {"extra_body": {"enable_thinking": False}}),
    )
    # Đọc NGƯỢC ra từ đối tượng vừa dựng, KHÔNG đọc lại biến config: nếu tên
    # tham số sai thì `extra_body` sẽ không bám vào model, mà biến config vẫn
    # nói "đã tắt". Quan sát hiện vật, đừng tin lời khai — cùng nguyên tắc dấu
    # `duong` và `so_tool_schema_gui`.
    global _SUY_LUAN_GUI
    _SUY_LUAN_GUI = not bool((getattr(model, "extra_body", None) or {}).get("enable_thinking") is False)
    tools = build_customer_tools(
        session, user_id=user_id, otp_verified_at=otp_verified_at, guard=guard
    )
    # Số lược đồ tool THẬT SỰ bind vào lời gọi. Lấy từ chính danh sách vừa
    # dựng, KHÔNG gõ tay — `_CHARS_TOOL_SCHEMA = 6773` phía trên là hằng số
    # người phải nhớ cập nhật, và ta không thêm cái thứ hai cùng loại.
    #
    # Trường này đến từ cơ chế KHÁC với quyết định phân luồng, nên hai thứ
    # không thể cùng nói dối một lúc: dấu `duong` kẹt ở "day_du" trong khi số
    # này = 0 là mâu thuẫn tự lộ, và ngược lại.
    global _SO_TOOL_GUI, _CHARS_TOOL_SCHEMA_THAT
    _SO_TOOL_GUI = len(tools)
    # Kích thước lược đồ ĐO TỪ CHÍNH LƯỢC ĐỒ, không gõ tay. `_CHARS_TOOL_SCHEMA
    # = 6773` phía trên kèm chú thích "đổi khi thêm/bớt tool" — một con số
    # NGƯỜI PHẢI NHỚ cập nhật, tức nó sẽ hỏng im lặng vào ngày có tool thứ sáu.
    # Đo payload thật 17/08: 6.773 ký tự — hằng số ĐÚNG hôm nay, và đúng do
    # người, không do cơ chế.
    try:
        from langchain_core.utils.function_calling import convert_to_openai_tool
        _CHARS_TOOL_SCHEMA_THAT = len(json.dumps(
            [convert_to_openai_tool(t) for t in tools], ensure_ascii=False))
    except Exception:  # noqa: BLE001 — số đo hỏng không được làm chết lượt chat
        _CHARS_TOOL_SCHEMA_THAT = _CHARS_TOOL_SCHEMA
    # KHÔNG truyền customer_name — họ tên thật không được rời hệ thống lên LLM
    # (ADR-010). Giữ tham số ở chữ ký hàm để không vỡ caller cũ.
    system_prompt = build_system_prompt(current_time=dt.datetime.utcnow())
    return create_agent(model, tools, system_prompt=system_prompt, checkpointer=_CHECKPOINTER)


def run_agent_turn(
    session: Session,
    *,
    user_id: str,
    message: str,
    thread_id: str | None = None,
    otp_verified_at: float | None = _ALWAYS_FRESH,
) -> dict[str, Any]:
    """`otp_verified_at`: timestamp (epoch giây) lúc xác thực OTP+câu hỏi bảo
    mật gần nhất (src/auth.py) — truyền THẬT từ current_user.otp_verified_at ở
    /agent/chat (src/api/main.py), có thể là None nếu khách CHƯA TỪNG xác thực.
    Không truyền tham số này (mặc định `_ALWAYS_FRESH`) nghĩa là coi như vừa
    xác thực XONG — để KHÔNG phá vỡ eval/golden_set.jsonl + adversarial_set
    hiện có: các case đó vốn giả định "khách đã xác thực OTP trước khi vào
    chat" (đúng câu mở đầu system prompt), không phải kiểm tra luồng OTP —
    luồng OTP thật được test riêng ở tests/test_api/test_otp.py +
    frontend/e2e/auth.spec.ts."""
    if otp_verified_at is _ALWAYS_FRESH:
        otp_verified_at = dt.datetime.utcnow().timestamp()

    user = session.get(User, user_id)
    if user is None:
        raise ToolError(f"user_id không tồn tại: {user_id}")

    # Đặt lại đầu MỖI lượt: hai biến này là toàn cục cấp module (ghi ở
    # `_build_agent`). Không đặt lại thì một `return` sớm xảy ra TRƯỚC khi agent
    # được dựng sẽ báo giá trị của LƯỢT TRƯỚC — một con số hợp lý và sai.
    # `None` ở đây là CỐ Ý: nó nói "chưa dựng agent", khác hẳn `0` nghĩa là
    # "đã dựng, không gửi tool nào".
    global _SO_TOOL_GUI, _CHARS_TOOL_SCHEMA_THAT
    _SO_TOOL_GUI = None
    _CHARS_TOOL_SCHEMA_THAT = None

    # ── T1 · PHÂN LUỒNG ─────────────────────────────────────────────────────
    # Sau cờ, MẶC ĐỊNH TẮT. Tắt thì hàm này chạy y hệt trước khi có nhánh này.
    #
    # Đường nhẹ TRẢ NGAY, KHÔNG chạm model, KHÔNG chạm tool, KHÔNG ghi bản ghi
    # nghiệp vụ nào. Đó là toàn bộ điểm của nó: rẻ hơn mọi model rẻ, vì không
    # có model nào.
    #
    # Đặt SAU khi nạp `user` (cần user tồn tại thật) và TRƯỚC mọi thứ khác —
    # đặt muộn hơn là đã tiêu mất thứ ta định tiết kiệm.
    if PHAN_LUONG_BAT:
        _duong, _ly_do_duong = phan_luong(message)
        if _duong == DUONG_NHE:
            _logger.info(
                "agent_turn_duong_nhe",
                extra={"user_id": user_id, "thread_id": thread_id or user_id,
                       "ly_do": _ly_do_duong, "bam_luat": BAM_LUAT},
            )
            _kq_nhe = {
                "reply": TRA_LOI_NHE,
                "tool_calls": [],
                "ticket_id": None,
                "should_escalate": False,
                "usage": {"input_tokens": 0, "output_tokens": 0, "total_tokens": 0,
                          "cached_input_tokens": 0, "reasoning_tokens": 0,
                          "input_chars": 0, "so_luot_goi_model": 0,
                          # Hai trường ĐẾM cùng tầng với `so_luot_goi_model`.
                          # tester sập bẫy hai-tầng: `.get()` trên khoá không
                          # tồn tại trả None, y hệt khoá tồn tại mang None.
                          # `duong` GIỮ top-level — nó là NHÃN, không phải số đo.
                          "so_tool_schema_gui": 0,
                          "chars_tool_schema_moi_luot": 0,
                          "suy_luan_gui": None},
                "loc_dau_ra": [],
                "tin_hieu_lo_chi_thi": {"nguyen_tac": 0, "quy_trinh": 0},
                "goi_y_handoff": False,
                "ly_do_fallback": None,
                # Dấu do TẦNG NÀY ghi, từ thứ nó THẬT SỰ gửi đi (không gửi gì).
                # `so_tool_schema_gui` đến từ một cơ chế KHÁC với quyết định
                # phân luồng, nên một điểm hỏng không giả được cả hai: dấu kẹt
                # "day_du" mà số này = 0 là mâu thuẫn tự lộ.
                "duong": DUONG_NHE,
            }
            _ghi_so(_kq_nhe, thread_id, user_id)
            return _kq_nhe

    # ES-xx (ADR-022) — tính TRƯỚC khi gọi agent, trên tin nhắn khách, ở TẦNG
    # SERVICE. Không gọi LLM, không đi vào prompt, không thêm bước nào.
    #
    # Đặt ở ĐÂY chứ không phải sau khi có reply là có chủ đích: tính sau thì vẫn
    # đúng nghĩa "không vào prompt", nhưng mất khả năng bật gợi ý NGAY ở lượt
    # đang xảy ra — mà toàn bộ giá trị của ES là đưa người bực sang người thật
    # SỚM, không phải một lượt sau.
    #
    # Cố ý KHÔNG đưa nhãn cảm xúc vào prompt: agent sẽ NÓI RA cảm nhận đó, tức
    # khẳng định một kết luận tâm lý về một con người dựa trên bộ phân loại có
    # thể sai — trái tinh thần ràng buộc cứng 3 (mọi điều agent khẳng định phải
    # truy được về dữ liệu thật; cảm xúc suy đoán không phải dữ liệu thật).
    tin_hieu_cam_xuc = danh_gia_luot(message, thread_id or user_id)

    # 1 guard cho MỖI lượt (không phải global) — bàn giao `session` giữa luồng
    # chính và luồng nền khi lượt bị bỏ rơi vì timeout, xem TurnGuard (QA-12).
    guard = TurnGuard()
    agent = _build_agent(
        session, user_id=user_id, customer_name=None, otp_verified_at=otp_verified_at, guard=guard  # PII-OK: cố ý truyền None, không đưa họ tên lên LLM
    )
    # thread_id mặc định = user_id (hành vi thật, không đổi). eval/_harness.py
    # truyền thread_id riêng biệt mỗi case để cô lập bộ nhớ hội thoại
    # (checkpointer module-level dùng chung — nếu không cô lập, nhiều case
    # cùng user_id trong 1 lần chạy eval sẽ nối tiếp hội thoại của nhau).
    config = {"configurable": {"thread_id": thread_id or user_id}}

    state_before = agent.get_state(config)
    prev_len = len(state_before.values.get("messages", [])) if state_before.values else 0

    # Span gốc "agent_turn" — 1 lượt chat là 1 vòng lặp ReAct nhiều bước (LLM
    # generation + tool call xen kẽ), KHÔNG PHẢI 1 khối duy nhất (Giai đoạn 1
    # checklist observability). `callbacks=[handler]` (KHÔNG dùng
    # `.configurable`) tạo span con cho MỖI vòng gọi LLM/tool bên trong, tự
    # nối cây cha-con qua context OTel hiện hành (span gốc đang active).
    with _tracer.start_as_current_span("agent_turn") as root_span:
        root_span.set_attribute("fin05.user_id", user_id)
        root_span.set_attribute("fin05.thread_id", thread_id or user_id)
        root_span.set_attribute("fin05.otp_verified", otp_verified_at is not None)
        def _invoke():
            return agent.invoke(
                {"messages": [HumanMessage(content=scrub_pii(message) or message)]},
                config={
                    **config,
                    "callbacks": [OTelTracingCallbackHandler()],
                    "recursion_limit": _AGENT_RECURSION_LIMIT,
                },
            )

        # AGENT_TURN_TIMEOUT_SECONDS — OPENAI_TIMEOUT_SECONDS chỉ chặn TỪNG
        # lượt gọi OpenAI riêng lẻ; 1 lượt /agent/chat có thể cần NHIỀU lượt
        # gọi xen kẽ với tool (ReAct), nên tổng thời gian vẫn có thể vượt xa
        # (đo thật: 70s cho 1 request) nếu không chặn RIÊNG ở đây. Chạy trong
        # thread riêng để `.result(timeout=...)` trả lỗi có kiểm soát cho
        # client kịp lúc. CỐ Ý KHÔNG dùng `with ThreadPoolExecutor(...) as
        # executor:` — `__exit__` mặc định gọi `shutdown(wait=True)`, tức
        # BLOCK tới khi thread dở xong mới thoát `with`, xoá sạch tác dụng
        # của timeout. `shutdown(wait=False)` khi timeout: không huỷ được
        # lượt gọi OpenAI đang chạy dở bên dưới (Python không kill thread
        # được), nhưng trả quyền điều khiển lại cho client NGAY, không đợi.
        executor = ThreadPoolExecutor(max_workers=1)
        # Mốc để sổ trả lời được "lượt này CHẠY BAO LÂU rồi mới hỏng".
        # Thiếu nó thì nhãn `timeout` là một lời khẳng định KHÔNG KIỂM ĐƯỢC:
        # một lượt bỏ cuộc tức thì và một lượt chạy trọn 45 giây trông y hệt
        # nhau trong sổ. Có nó thì `giay_da_troi ≈ AGENT_TURN_TIMEOUT_SECONDS`
        # là bằng chứng nhãn ĐÚNG, còn `0,4 giây` là bằng chứng nhãn SAI.
        _bat_dau = time.monotonic()
        try:
            result = executor.submit(_invoke).result(timeout=AGENT_TURN_TIMEOUT_SECONDS)
        except RateLimitError as e:
            # 429 quá tải nhà cung cấp. TRƯỚC BẢN NÀY nó không nằm trong tuple
            # `except` dưới -> rơi thẳng ra ngoài thành HTTP 500, khách nhận
            # `{"detail":"Internal Server Error"}` trong khi OpenAI đã nói rõ
            # "try again in 1.381s". Đo thật: tester chạy `--lap 3` là tái hiện.
            #
            # NHÁNH RIÊNG, KHÔNG dùng chung với timeout/recursion bên dưới —
            # khác nhau ở chỗ QUAN TRỌNG NHẤT: nhánh kia TẠO TICKET bàn giao
            # người thật, đúng cho ca agent bó tay. 429 thì không: nó là nghẽn
            # thoáng qua, tự hết sau vài giây. Tạo ticket cho nó nghĩa là mỗi
            # phút cao điểm đổ một nắm ticket ma lên CSKH cho những khiếu nại
            # KHÔNG TỒN TẠI — và khách vẫn chưa được trả lời.
            #
            # Không ngủ-rồi-thử-lại ở đây: `openai` SDK đã tự retry
            # OPENAI_MAX_RETRIES lần theo đúng `Retry-After` của nhà cung cấp
            # TRƯỚC KHI ném lên tới đây. Ngủ thêm ở tầng này chỉ ăn vào ngân
            # sách AGENT_TURN_TIMEOUT_SECONDS rồi biến 429 thành timeout —
            # đúng cái nhầm lẫn `_ly_do_fallback` đã cảnh báo.
            executor.shutdown(wait=False)
            # ĐÍNH CHÍNH commit 8a30238 (message của nó dễ đọc sai, không sửa
            # lịch sử được): cụm "không đẻ ticket ma" ở đó mô tả việc nhánh NÀY
            # tránh làm, KHÔNG phải một bug đã từng xảy ra rồi được chặn. Trước
            # bản vá, 429 rơi thẳng ra 500 và chưa bao giờ chạm nhánh fallback
            # -> chưa từng tạo ticket nào qua đường đó.
            #
            # ⚠️ NHƯNG có một đường ticket-ma THẬT mà nhánh này KHÔNG đóng: khi
            # SDK ngủ theo `Retry-After` rồi TỔNG vượt AGENT_TURN_TIMEOUT_SECONDS,
            # ta nhận FutureTimeoutError chứ không phải RateLimitError -> rơi
            # xuống nhánh dưới -> nhánh ĐÓ CÓ tạo ticket. Tức 429 đủ chậm vẫn đẻ
            # ticket như cũ. Đã vào sổ là F-33b.
            #
            # AI MỞ F-33b: bịt ở đây là bịt NHẦM CHỖ. Chỗ cần bịt nằm ở nhánh
            # timeout, hoặc ở tương quan OPENAI_MAX_RETRIES x
            # AGENT_TURN_TIMEOUT_SECONDS. Và F-33c (lưu `ly_do_fallback` vào bản
            # ghi) là điều kiện để câu "429 có đẻ ticket không" trả lời được
            # bằng MỘT truy vấn — hôm nay không trả lời được, vì 15 complaint
            # fallback trong DB dùng CHUNG một văn bản lý do cho cả timeout lẫn
            # recursion.
            giay = _giay_cho_lai(e)
            _logger.warning(
                "agent_turn_qua_tai",
                extra={
                    "user_id": user_id,
                    "thread_id": thread_id or user_id,
                    "retry_after_giay": giay,
                    "so_lan_sdk_da_thu": OPENAI_MAX_RETRIES,
                },
            )
            root_span.set_attribute("fin05.qua_tai", True)
            khuyen = f" sau khoảng {giay:.0f} giây" if giay else " sau ít giây"
            _kq = {
                "reply": (
                    "Xin lỗi bạn, hệ thống đang bận nên mình chưa xử lý kịp. "
                    f"Bạn nhắn lại giúp mình{khuyen} nhé — tin nhắn của bạn "
                    "chưa bị mất gì cả."
                ),
                "tool_calls": [],
                "ticket_id": None,
                "should_escalate": False,
                "usage": {
                    # `None` = KHÔNG ĐỌC ĐƯỢC, khác hẳn `0` = KHÔNG CÓ.
                    # Ở nhánh này request ĐÃ ĐƯỢC GỬI nhưng không lời gọi nào
                    # TRẢ VỀ ⟹ `so_luot_goi_model = 0` là SỰ THẬT. Nhưng nhà
                    # cung cấp có tính tiền request bị từ chối/bỏ dở hay không
                    # thì ta KHÔNG kiểm được từ trong hệ thống ⟹ token là None.
                    # Đặt 0 ở đó là khẳng định một điều ta không biết.
                    "input_tokens": None,
                    "output_tokens": None,
                    "total_tokens": None,
                    "cached_input_tokens": None,
                    "so_luot_goi_model": 0,
                    "so_tool_schema_gui": _SO_TOOL_GUI,
                    "chars_tool_schema_moi_luot": _CHARS_TOOL_SCHEMA_THAT,
                    "suy_luan_gui": _SUY_LUAN_GUI,
                },
                "loc_dau_ra": [],
                "tin_hieu_lo_chi_thi": {"nguyen_tac": 0, "quy_trinh": 0},
                "goi_y_handoff": False,
                "ly_do_fallback": "qua_tai",
                # KẾT LUẬN ở trên, TRIỆU CHỨNG ở đây — không cái nào thay được cái nào.
                "trieu_chung": {**_trieu_chung_loi(e), "giay_da_troi": round(time.monotonic() - _bat_dau, 2)},
                "duong": DUONG_DAY_DU,
            }
            _ghi_so(_kq, thread_id, user_id)
            return _kq
            executor.shutdown(wait=True)  # thread thật sự đã xong lúc .result() trả về, wait=True không tốn gì thêm
        except APIError as e:
            # Mọi cách từ chối CÒN LẠI của nhà cung cấp. `RateLimitError` đã
            # được bắt ở trên — nó là CON của APIError, nên thứ tự hai nhánh
            # này KHÔNG hoán đổi được: đảo lại thì 429 bị nuốt vào đây và mất
            # thông điệp `retry_after` cụ thể mà nhà cung cấp đã nói rõ.
            #
            # HAI TRỤC ĐỘC LẬP, không phải hai đầu của một trục:
            #   trục KHÁCH     — mềm 8/8, không bao giờ 500 trần. Kể cả 400/404
            #                    (bug của ta): khách không đáng nhận 500 vì bug
            #                    của ta.
            #   trục VẬN HÀNH  — mức ồn đặt riêng. error cho ca cần người xử,
            #                    warning cho ca tự hết.
            # Ghép hai trục làm một sinh ra CẢ HAI lỗi sai: nổ to thì khách
            # nhận 500 (đúng ca hôm nay), êm thì vận hành không biết khoá sai.
            executor.shutdown(wait=False)
            mo_ta = _mo_ta_loi_nha_cung_cap(e)
            can_thiep = bool(mo_ta["can_can_thiep"])
            # HAI TÊN SỰ KIỆN RIÊNG, không phải một tên với một trường phân
            # loại. Lý do (security ①): có tên riêng thì `grep` ra được ngay hôm
            # nay, và ngày ai đó gắn cảnh báo thật thì gắn vào tên — không phải
            # sửa code. Một tên chung + trường lọc bắt người dựng cảnh báo phải
            # biết trường đó tồn tại.
            ten_su_kien = (
                "agent_turn_ncc_can_can_thiep" if can_thiep else "agent_turn_ncc_thoang_qua"
            )
            ghi = _logger.error if can_thiep else _logger.warning
            ghi(
                ten_su_kien,
                extra={
                    "user_id": user_id,
                    # correlation_id: nối sự cố với SỐ PHIÊN bị ảnh hưởng mà
                    # không lưu nội dung nào (security ④).
                    "thread_id": thread_id or user_id,
                    **mo_ta,
                },
            )
            # Bề mặt máy-đọc-được THỨ HAI, và là bề mặt DUY NHẤT truy vấn được
            # hôm nay: span Jaeger. Đã nối sẵn, không cần route mới (thêm route
            # = đổi contract), không phơi trạng thái vận hành ra `/health` công
            # khai — `lop_loi_cuoi="AuthenticationError"` trên một endpoint
            # không xác thực chính là báo cho người ngoài biết khoá ta đang hỏng.
            root_span.set_attribute("fin05.su_kien", ten_su_kien)
            root_span.set_attribute("fin05.loi_nha_cung_cap", str(mo_ta["lop_loi"]))
            root_span.set_attribute("fin05.can_can_thiep", can_thiep)
            root_span.set_attribute("fin05.het_han_muc", bool(mo_ta["co_dau_hieu_het_han_muc"]))
            if can_thiep:
                # Span ĐỎ, không chỉ là span có tag. Jaeger lọc theo `error=true`
                # mặc định; một tag tự đặt thì người trực phải biết trước tên nó.
                root_span.set_status(Status(StatusCode.ERROR, ten_su_kien))
                root_span.record_exception(e)

            # HAI CÂU KHÁC NHAU, và khác nhau ở đúng chỗ có hậu quả. Gộp lại là
            # bảo khách "thử lại sau ít phút" trong khi sự thật là "hết tiền,
            # thử lại bao nhiêu lần cũng không hết".
            #
            # Ba điều CẢ HAI câu cố ý KHÔNG nói:
            #  · không "chưa cho phép truy cập" — agent từng nói vậy rồi xin mã
            #    giao dịch, đẩy khách đi làm một việc vô ích (quan sát ⑤).
            #  · không "đã ghi nhận"/"CSKH sẽ liên hệ" — nhánh này KHÔNG tạo vé
            #    nào. Hứa một bản ghi không tồn tại là loại bịa tệ nhất: khách
            #    NGỒI CHỜ một cuộc gọi không bao giờ tới.
            #  · không mã lỗi, không tên nhà cung cấp — vô ích với khách, và lộ
            #    hạ tầng.
            #
            # Chuỗi là HẰNG SỐ ở tầng code, KHÔNG nhờ model sinh: model vừa
            # hỏng mới rơi vào đây, nhờ nó viết câu xin lỗi là phụ thuộc đúng
            # thứ vừa gãy.
            # Nhóm CẦN CAN THIỆP: KHÔNG hứa mốc thời gian (thử lại có thể
            # không giúp gì trong nhiều giờ) VÀ phải chỉ đường sang kênh khác.
            # Đây là ĐIỀU KIỆN của security ③, không phải tuỳ chọn: ta cố ý
            # không ghi lại lượt này, mà cái giá của việc mất dấu KHÔNG đồng
            # đều — mất một khách hỏi phí thì giá ≈ 0, mất một khách đang định
            # BÁO GIAN LẬN thì giá cao và nhạy thời gian. Ta không phân biệt
            # được vì agent hỏng TRƯỚC khi phân loại. Lối đi cho người thật là
            # biện pháp duy nhất còn lại — nó biến "ta mất dấu khách" thành
            # "khách vẫn còn đường".
            reply = (
                "Xin lỗi bạn, hệ thống đang gặp sự cố kỹ thuật nên tạm thời "
                "chưa xử lý được yêu cầu này. Nếu việc của bạn cần xử lý ngay, "
                f"bạn liên hệ {KENH_HO_TRO_KHAC} giúp mình nhé."
                if can_thiep else
                "Xin lỗi bạn, hệ thống đang bận nên mình chưa xử lý kịp. "
                "Bạn nhắn lại giúp mình sau ít phút nhé — tin nhắn của bạn "
                "chưa bị mất gì cả."
            )
            _kq = {
                "reply": reply,
                "tool_calls": [],
                "ticket_id": None,          # CỐ Ý: xem chú thích ở _LOI_CAN_CAN_THIEP
                "should_escalate": False,
                "usage": {
                    # `None` = KHÔNG ĐỌC ĐƯỢC, khác hẳn `0` = KHÔNG CÓ.
                    # Ở nhánh này request ĐÃ ĐƯỢC GỬI nhưng không lời gọi nào
                    # TRẢ VỀ ⟹ `so_luot_goi_model = 0` là SỰ THẬT. Nhưng nhà
                    # cung cấp có tính tiền request bị từ chối/bỏ dở hay không
                    # thì ta KHÔNG kiểm được từ trong hệ thống ⟹ token là None.
                    # Đặt 0 ở đó là khẳng định một điều ta không biết.
                    "input_tokens": None,
                    "output_tokens": None,
                    "total_tokens": None,
                    "cached_input_tokens": None,
                    "so_luot_goi_model": 0,
                    "so_tool_schema_gui": _SO_TOOL_GUI,
                    "chars_tool_schema_moi_luot": _CHARS_TOOL_SCHEMA_THAT,
                    "suy_luan_gui": _SUY_LUAN_GUI,
                },
                "loc_dau_ra": [],
                "tin_hieu_lo_chi_thi": {"nguyen_tac": 0, "quy_trinh": 0},
                "goi_y_handoff": False,
                # Hai giá trị RIÊNG, không gộp: câu hỏi vận hành "sự cố này tự
                # hết hay cần người xử" phải trả lời được bằng một truy vấn.
                "ly_do_fallback": (
                    "nha_cung_cap_can_can_thiep" if can_thiep else "nha_cung_cap_thoang_qua"
                ),
                # 🔴 Hai nhãn trên là KẾT LUẬN ("ai phải làm gì"). Chúng gộp
                # `401` khoá sai · `403` hết hạn ngạch · `404` sai tên model
                # vào MỘT chuỗi — ba sự cố cần ba cách xử khác hẳn nhau.
                # Mã trạng thái đi kèm ở đây để sổ trả lời được câu thứ hai:
                # "nhà cung cấp đã nói gì". Giữ NGUYÊN hai nhãn cũ vì có test
                # đang khẳng định chúng — đổi tên là việc phải đi qua tester.
                "trieu_chung": {**_trieu_chung_loi(e), "giay_da_troi": round(time.monotonic() - _bat_dau, 2)},
                "duong": DUONG_DAY_DU,
            }
            _ghi_so(_kq, thread_id, user_id)
            return _kq
        except (GraphRecursionError, FutureTimeoutError) as e:
            # wait=False luôn an toàn ở đây: nếu thread đã xong (nhánh
            # GraphRecursionError) thì trả về ngay lập tức; nếu chưa (nhánh
            # timeout thật) thì không chờ, đúng mục đích.
            executor.shutdown(wait=False)
            # Vòng lặp ReAct vượt quá _AGENT_RECURSION_LIMIT HOẶC vượt trần
            # thời gian tổng (thật sự xảy ra — không phải lý thuyết, xem case
            # CONSUME-002) — KHÔNG để lỗi rơi ra ngoài thành 500, chuyển hẳn
            # cho người xử lý thay vì treo vô thời hạn/crash. root_span vẫn
            # ghi nhận đúng (context manager tự đóng dù có exception), chỉ
            # không có span con của lượt hỏng.
            is_timeout = isinstance(e, FutureTimeoutError)
            _logger.warning(
                "agent_turn_timeout" if is_timeout else "agent_recursion_limit_reached",
                extra={"user_id": user_id, "thread_id": thread_id or user_id},
            )
            root_span.set_attribute("fin05.recursion_limit_reached", not is_timeout)
            root_span.set_attribute("fin05.turn_timeout", is_timeout)
            # Bàn giao session lại cho luồng này TRƯỚC KHI ghi (QA-12). Đặt cờ
            # rồi mới giành khoá: tool call dở dang (nếu có) chạy nốt xong mới
            # nhả khoá, và mọi tool call SAU đó thấy cờ nên từ chối chạm DB —
            # luồng nền bị bỏ rơi không thể sinh ticket thứ hai cho cùng lượt
            # chat này nữa (đo thật: 4/4 case từng sinh ticket ma).
            #
            # Ghi bằng CHÍNH `session` được tiêm, không mở session thứ hai:
            # mở connection thứ hai vào cùng DB trong khi connection thứ nhất
            # đang giữ transaction ghi dở là nguyên nhân "database is locked"
            # (QA-12) — và cũng thừa, vì sau khi giành được khoá thì session
            # này đã an toàn tuyệt đối. Dùng session được tiêm cũng chính là
            # thứ giữ QA-10: ticket luôn nằm đúng DB mà caller chỉ định.
            guard.abandoned.set()
            with guard.lock:
                handoff = flag_human_handoff(
                    session,
                    user_id=user_id,
                    reason="Hệ thống AI gặp khó khăn khi xử lý yêu cầu này (vòng lặp tra cứu không ra kết quả rõ ràng) — cần chuyên viên hỗ trợ trực tiếp.",
                )
                # Commit tường minh: khách vừa được báo mã ticket này, nên nó
                # PHẢI tồn tại thật, không phụ thuộc caller có commit hay
                # không (eval harness rollback giữa các case) — báo mã ticket
                # không tra được chính là bịa số liệu, ràng buộc cứng #3.
                session.commit()
            _kq = {
                "reply": "Mình chưa tra được yêu cầu này, để mình chuyển cho chuyên viên hỗ trợ trực tiếp nhé — mã ticket của bạn là "
                + handoff["ticket_id"]
                + ".",
                # `None`, KHÔNG phải `[]`. Đây là bản vá cho một lời nói dối của
                # dữ liệu: `[]` nghĩa là "không tool nào được gọi", mà ở nhánh
                # này ta KHÔNG BIẾT — `_invoke` đã ném lỗi nên không có
                # `result["messages"]` để đọc. Khôi phục từ checkpointer thì
                # phải đọc trong lúc luồng nền vẫn đang ghi, đúng race đã gây ra
                # QA-12; không đáng đổi.
                # Trước bản vá này, tester đọc `[]` như quan sát thật và suýt
                # kết luận "agent không gọi tool nào" cho những ca đã chạy tool.
                # `null` = "không khôi phục được", khác hẳn `[]` = "không có".
                "tool_calls": None,
                "ticket_id": handoff["ticket_id"],
                "should_escalate": False,
                # Bốn số 0 này là "KHÔNG ĐO ĐƯỢC", không phải "đo được 0" —
                # `_invoke` đã ném lỗi SAU khi model có thể đã chạy và đã tốn
                # token thật. Cùng loại phân biệt mà `tool_calls: None` ở trên
                # cố ý giữ. Chưa đổi sang None vì có consumer đang cộng dồn
                # trực tiếp; nhưng ai dựng test/dashboard chi phí trên trường
                # này phải biết: lượt fallback ÂM THẦM báo thiếu tiền đã tiêu,
                # và một assertion `usage == 0` sẽ xanh ở CẢ HAI nghĩa.
                "usage": {
                    # `None` = KHÔNG ĐỌC ĐƯỢC, khác hẳn `0` = KHÔNG CÓ.
                    # Ở nhánh này request ĐÃ ĐƯỢC GỬI nhưng không lời gọi nào
                    # TRẢ VỀ ⟹ `so_luot_goi_model = 0` là SỰ THẬT. Nhưng nhà
                    # cung cấp có tính tiền request bị từ chối/bỏ dở hay không
                    # thì ta KHÔNG kiểm được từ trong hệ thống ⟹ token là None.
                    # Đặt 0 ở đó là khẳng định một điều ta không biết.
                    "input_tokens": None,
                    "output_tokens": None,
                    "total_tokens": None,
                    "cached_input_tokens": None,
                    "so_luot_goi_model": 0,
                    "so_tool_schema_gui": _SO_TOOL_GUI,
                    "chars_tool_schema_moi_luot": _CHARS_TOOL_SCHEMA_THAT,
                    "suy_luan_gui": _SUY_LUAN_GUI,
                },
                # Câu fallback do CHÍNH TA viết, không qua LLM -> không cần lọc.
                "loc_dau_ra": [],
                "tin_hieu_lo_chi_thi": {"nguyen_tac": 0, "quy_trinh": 0},
                # Lượt rơi fallback vẫn phải mang tín hiệu: khách bực mà hệ
                # thống lại lỗi chính là lúc CẦN người thật nhất.
                "goi_y_handoff": bool(tin_hieu_cam_xuc),
                # DẤU HIỆU DƯƠNG DỨT KHOÁT của fallback. Tester dùng đúng trường
                # này để loại ca khỏi phép so-cặp, nên nó gánh phần định nghĩa
                # tập-loại-trừ của phép đo — KHÔNG được set nhầm ở đường thường.
                # Trước đây họ phải nhận diện bằng chữ ký chuỗi trong `reply`,
                # thứ trôi được sau một lần sửa câu chữ.
                "ly_do_fallback": _ly_do_fallback(e),
                # `giay_da_troi` là thứ làm nhãn `timeout` KIỂM ĐƯỢC thay vì
                # phải tin. Không có nó, "timeout" chỉ là tên của một nhánh mã.
                "trieu_chung": {**_trieu_chung_loi(e), "giay_da_troi": round(time.monotonic() - _bat_dau, 2)},
                "duong": DUONG_DAY_DU,
            }
            _ghi_so(_kq, thread_id, user_id)
            return _kq
    all_messages = result["messages"]
    turn_messages = all_messages[prev_len:]

    reply = ""
    ly_do_dung = None
    for m in reversed(turn_messages):
        if isinstance(m, AIMessage) and not m.tool_calls:
            reply = m.content
            ly_do_dung = (getattr(m, "response_metadata", None) or {}).get("finish_reason")
            break

    # KÊU khi model trả nội dung RỖNG. Trước bản này `reply` nhận "" và đi
    # thẳng ra khách: màn hình trắng, HTTP 200, không lỗi, không log.
    # Ca sinh ra nó: model có reasoning tiêu hết trần token vào phần suy nghĩ
    # rồi không còn chỗ sinh nội dung. Không vá được bằng đoán trần — vá bằng
    # cách làm nhánh im lặng KÊU LÊN, rồi mới biết có cần chỉnh trần không.
    if not str(reply).strip():
        _logger.warning(
            "agent_reply_rong",
            extra={
                "user_id": user_id,
                "thread_id": thread_id or user_id,
                "model": LLM_MODEL,
                "so_message_luot_nay": len(turn_messages),
                "finish_reason": ly_do_dung,
                "ghi_chu": "Content rỗng nhưng KHÔNG phải do hết trần — chưa rõ nguyên nhân.",
            },
        )

    tool_msgs_by_id = {m.tool_call_id: m for m in turn_messages if isinstance(m, ToolMessage)}
    tool_calls_out: list[dict] = []
    ticket_id = None
    should_escalate = None

    for m in turn_messages:
        if not (isinstance(m, AIMessage) and m.tool_calls):
            continue
        for call in m.tool_calls:
            tm = tool_msgs_by_id.get(call["id"])
            if tm is None:
                continue
            try:
                payload = json.loads(tm.content)
            except (json.JSONDecodeError, TypeError):
                payload = {"raw": tm.content}
            tool_calls_out.append({"tool_name": call["name"], "args": call["args"], "result": payload})
            if call["name"] == "create_ticket" and "ticket_id" in payload:
                ticket_id = payload["ticket_id"]
                should_escalate = payload.get("should_escalate")

    if ticket_id is not None:
        write_investigation_logs_for_ticket(session, ticket_id=ticket_id, all_messages=all_messages)
        if tin_hieu_cam_xuc:
            _nang_uu_tien_theo_cam_xuc(session, ticket_id=ticket_id)

    # Token usage cộng dồn của LƯỢT NÀY (mọi vòng gọi model bên trong, kể cả
    # vòng gọi tool trung gian) — dùng để đo cost thật (eval/measure_quality.py),
    # KHÔNG ảnh hưởng contract cũ (chỉ thêm key mới, không đổi key sẵn có).
    # T1 — `cached_tokens` là thứ DUY NHẤT nói prompt-cache có ăn hay không.
    # Trước bản này không ai biết cache đang hit 0% hay 50%; suy luận từ tài
    # liệu OpenAI không thay được số đo (và suy luận đó đã sai một lần: mốc
    # thời gian HH:MM nằm ở ký tự 233/16.082 khiến prefix ổn định chỉ ~68
    # token, dưới hẳn ngưỡng 1024 — cache chắc chắn hit 0%).
    # `input_chars` — đại lượng BẤT BIẾN QUA TOKENIZER.
    #
    # Vì sao cần: token của hai nhà cung cấp KHÔNG so được với nhau (tokenizer
    # khác nhau, tiếng Việt là chỗ lệch nhiều nhất), nên chuỗi đo T1->T3 sẽ
    # ĐỨT ngay khi đổi model. Ký tự thì không đổi.
    #
    # ⚠️ ĐẾM ĐÚNG NHỮNG GÌ, KHAI RÕ Ở ĐÂY để nó không thành một "chỉ số một
    # phần trông như đại lượng bất biến":
    #     CÓ    system prompt (15.094 ký tự) + toàn bộ message của mỗi lượt
    #           gọi model, cộng dồn qua các bước ReAct — đúng phần biến thiên
    #     KHÔNG JSON schema của 5 tool = 6.773 ký tự, HẰNG SỐ mỗi lượt gọi
    #
    # Phần thiếu là hằng số ĐO ĐƯỢC, không phải ẩn số: ai cần tổng tuyệt đối
    # thì cộng `6773 × số_luot_goi_model`. Ghi con số ra đây thay vì im lặng
    # bỏ qua — một khoảng trống có tên thì trừ được, không tên thì không.
    usage = {
        "input_tokens": 0,
        "output_tokens": 0,
        "total_tokens": 0,
        "cached_input_tokens": 0,
        "reasoning_tokens": 0,
        "input_chars": 0,
        # ĐẾM LỜI GỌI **ĐÃ TRẢ VỀ**, không phải đã phát — nó chỉ tăng khi một
        # `AIMessage` có `usage_metadata`, tức chỉ khi nhà cung cấp đã đáp.
        # Khai ở đây vì tên trường không nói ra điều đó, và một trường không
        # khai nó đếm gì thì MỌI giá trị của nó đều mơ hồ, kể cả giá trị đúng.
        "so_luot_goi_model": 0,
        "chars_tool_schema_moi_luot": _CHARS_TOOL_SCHEMA_THAT,
        "so_tool_schema_gui": _SO_TOOL_GUI,
        "suy_luan_gui": _SUY_LUAN_GUI,
        # Danh tính CHỈ DẪN của lượt này. Prompt đã render đổi mỗi phút (có
        # ngày/giờ), nên "cùng một prompt" giữa hai đợt đo là GIẢ ĐỊNH chứ
        # không phải sự kiện — trừ khi so băm MẪU. Trả sẵn để không ai phải
        # nhớ ghi, và để một cặp trước/sau bắc qua hai mẫu khác nhau LỘ RA.
        "bam_mau_prompt": bam_mau_prompt(),
    }
    _ky_tu_he_thong = len(build_system_prompt(current_time=dt.datetime.utcnow()))
    for m in turn_messages:
        meta = isinstance(m, AIMessage) and getattr(m, "usage_metadata", None)
        if meta:
            # Mỗi AIMessage có usage_metadata = MỘT lượt gọi model. Input của
            # lượt đó là system prompt + mọi message đứng TRƯỚC nó. Dựng lại từ
            # `all_messages` thay vì chặn ở tầng model: chặn được thì chính xác
            # hơn, nhưng phải vá vào thư viện — không đáng cho một chỉ số đo.
            j = all_messages.index(m)
            usage["so_luot_goi_model"] += 1
            usage["input_chars"] += _ky_tu_he_thong + sum(
                len(str(getattr(x, "content", "") or "")) for x in all_messages[:j]
            )
            for k in ("input_tokens", "output_tokens", "total_tokens"):
                usage[k] += meta.get(k, 0) or 0
            # LangChain gom chi tiết provider vào `input_token_details`; OpenAI
            # đặt phần đã cache ở khoá `cache_read`. Đọc phòng thủ vì tên khoá
            # là hợp đồng của provider, không phải của ta.
            # Token SUY NGHĨ của model reasoning nằm ở `output_token_details`,
            # KHÔNG phải `input_token_details`. Nó được tính vào `output_tokens`
            # nên hoá đơn không sai — nhưng không tách ra thì không ai biết bao
            # nhiêu tiền đang trả cho phần khách không bao giờ đọc.
            usage["reasoning_tokens"] += (meta.get("output_token_details") or {}).get("reasoning", 0) or 0
            chi_tiet = meta.get("input_token_details") or {}
            usage["cached_input_tokens"] += chi_tiet.get("cache_read", 0) or 0

    # HAI ca rỗng KHÁC HẲN NHAU, cố ý không gộp:
    #   rỗng + finish_reason="length" -> model tiêu hết trần token vào phần suy
    #       nghĩ thầm, không còn chỗ sinh nội dung. Đây là hỏng CẤU HÌNH CỦA TA,
    #       sửa được bằng LLM_MAX_TOKENS. Phải NỔ: để nó đi tiếp thì bộ đo ghi
    #       một lỗi hạ tầng của ta thành "model trả lời kém" (Luật 1c).
    #   rỗng vì lý do khác -> chưa biết. Cảnh báo, không đoán, không nuốt.
    if not str(reply).strip() and ly_do_dung == "length":
        _logger.error(
            "agent_reply_rong_het_tran",
            extra={
                "user_id": user_id,
                "model": LLM_MODEL,
                "finish_reason": ly_do_dung,
                "reasoning_tokens": usage["reasoning_tokens"],
                "output_tokens": usage["output_tokens"],
                "llm_max_tokens": LLM_MAX_TOKENS,
            },
        )
        raise TraLoiRongError(
            f"Model {LLM_MODEL} tra noi dung RONG voi finish_reason=length — "
            f"tran token bi phan suy nghi an het ({usage['reasoning_tokens']}/"
            f"{usage['output_tokens']} token dau ra la reasoning). "
            f"Nang LLM_MAX_TOKENS (hien {LLM_MAX_TOKENS})."
        )

    # NGUỒN TRUY VẾT cho luật xuất xứ của O3: mọi mã/dãy số >=7 ký tự agent nói
    # ra phải có mặt ở một trong hai nơi này — nếu không thì nó ở đâu ra?
    #   · kết quả tool của lượt này VÀ của các lượt trước (`rap_nguon_o3`)
    #   · mọi lời KHÁCH đã gõ trong hội thoại — không chỉ lượt hiện tại, vì
    #     khách có thể đọc mã biên lai ở lượt 1 rồi agent nhắc lại ở lượt 3
    # Đây là ràng buộc cứng 3 viết thành một phép kiểm chạy được.
    # TÁCH HAI KÊNH NGUỒN — không gộp thành một chuỗi. Payload tool là JSON nên
    # dấu phẩy trong đó là DẤU PHÂN CÁCH TRƯỜNG; lời khách là văn xuôi nên dấu
    # phẩy/chấm là dấu ngăn hàng nghìn. Gộp chung rồi trích bằng một luật thì một
    # trong hai kênh chắc chắn bị hiểu sai — và hiểu sai ở kênh JSON đẻ ra số
    # KHÔNG TỒN TẠI trong tập nguồn hợp lệ.
    nguon_tool = rap_nguon_o3(all_messages, tool_calls_out)
    loi_khach = " ".join(
        m.content for m in all_messages if isinstance(m, HumanMessage) and isinstance(m.content, str)
    )
    reply_da_loc, nhom_khop = loc_dau_ra(
        reply,
        nguon=nguon_tool,
        loi_khach=loi_khach,
        tin_nhan_khach=message,
        thread_id=thread_id or user_id,
    )
    # O2 ĐẾM-TRƯỚC-CHẶN-SAU (security, docs/security/mo-neo-quy-trinh-cho-O2.md,
    # PO duyệt) — CHẠY TRÊN `reply` GỐC, không phải `reply_da_loc`. Mật độ liệt
    # kê là tín hiệu về HÀNH VI của agent (đang đọc lại nội quy hay không), độc
    # lập với việc O1-O4 có chặn câu đó hay không — trộn hai thứ sẽ làm phân
    # phối mật độ mù chính câu bị O3/O4 thay bằng CAU_AN_TOAN.
    #
    # Trước bản này hàm KHÔNG CÓ call site nào ở đường chạy thật (chỉ tests/ và
    # eval/) — mệnh đề "đếm trước, nâng lên chặn khi thấy rò" tới giờ rỗng trong
    # production. Trả qua ENVELOPE (không chỉ ghi Redis) vì cùng lý do ba trường
    # chẩn đoán bên dưới: eval gọi thẳng graph, Redis là fakeredis per-process,
    # nên bộ đếm vô hình với người đo nếu chỉ ghi Redis.
    tin_hieu_lo_chi_thi_ket_qua = tin_hieu_lo_chi_thi(reply, thread_id=thread_id or user_id)
    _kq_cuoi = {
        "reply": reply_da_loc,
        "tool_calls": tool_calls_out,
        "ticket_id": ticket_id,
        "should_escalate": should_escalate,
        "usage": usage,
        # BỐN trường CHẨN ĐOÁN (`tin_hieu_lo_chi_thi` thêm ở Luật 18). Không
        # phải tiện tay: eval KHÔNG sinh một dòng log nào (runner gọi thẳng
        # graph, logging_config chưa từng khởi tạo) và Redis là fakeredis
        # per-process — nên log + bộ đếm của bộ lọc VÔ HÌNH với người đo. Thiếu
        # chúng thì O1/O3/O4 cùng ra một câu an toàn giống hệt nhau, đúng họ
        # "hai trạng thái đội chung một vỏ"; và trước Luật 18, mật độ liệt kê
        # còn tệ hơn — không chỉ vô hình mà CHƯA TỪNG được tính ở đường thật.
        "loc_dau_ra": nhom_khop,
        "tin_hieu_lo_chi_thi": tin_hieu_lo_chi_thi_ket_qua,
        # ES-xx -> FRONTEND render nút "gặp người thật". KHÔNG tự gọi
        # request_human_handoff: quyền quyết định gặp người là của KHÁCH
        # (CTRL-001 / ISO-IEC 25059), hệ thống chỉ ĐỀ NGHỊ.
        "goi_y_handoff": bool(tin_hieu_cam_xuc),
        "duong": DUONG_DAY_DU,
        "ly_do_fallback": None,  # TƯỜNG MINH null, KHÔNG thiếu key — thiếu key
        # không phân biệt được với "bản cũ chưa có trường này".
        **_reply_goc_cho_eval(reply, nhom_khop),
    }
    _ghi_so(_kq_cuoi, thread_id, user_id)
    return _kq_cuoi
