"""FIN-05 — FastAPI app.

Hai nhóm route, cố ý tách bạch để ranh giới HITL (Data Brief §6.6, quyết
định thiết kế #1 trong ngữ cảnh dự án) hiện rõ ngay ở tầng routing:

  /tools/*        — agent gọi để điều tra/tạo ticket/đề xuất/escalate.
                    KHÔNG route nào trong nhóm này có thể ghi `approved`.
  /resolutions/{id}/approve  — CHỈ sếp (role=supervisor) gọi được. Đây là
                    con đường DUY NHẤT trong toàn hệ thống ghi trạng thái
                    approved — mọi phạm vi giao dịch, kể cả nội bộ ví
                    (quyết định thiết kế đã sửa, xem ngữ cảnh dự án §4.1).
  /tickets*       — đọc, dùng cho UI CSKH/sếp.

Vá bảo mật (phiên làm việc sau demo đầu): MỌI route cần danh tính giờ khai
báo `Depends(get_current_user)` hoặc `Depends(require_role(...))` — danh
tính lấy từ JWT đã ký (src/auth.py), KHÔNG BAO GIỜ từ field client tự khai
trong body (user_id/approved_by/rejected_by/created_by/requested_by đã bị
xoá khỏi schemas.py). Trước đây bất kỳ ai gọi API cũng mạo danh được bất kỳ
user nào — đây là lỗ hổng nghiêm trọng nhất đã vá.
"""
from __future__ import annotations

import datetime as dt
import hashlib
import json
import logging
import random
import time
import uuid

from fastapi import Depends, FastAPI, File, HTTPException, Request, UploadFile
from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from slowapi.util import get_remote_address
from sqlalchemy import select
from sqlalchemy.orm import Session

from src.agents.graph import run_agent_turn
from src.api.deps import get_session
from src.api.schemas import (
    AgentChatRequest,
    CreateTicketRequest,
    EscalateTicketRequest,
    GetCustomerHistoryRequest,
    LoginRequest,
    LookupTransactionRequest,
    OtpVerifyRequest,
    PolicySearchRequest,
    ProposeResolutionRequest,
    RequestMoreInfoRequest,
)
from src.auth import (
    CurrentUser,
    create_access_token,
    get_current_user,
    require_otp_verified,
    require_role,
    try_decode,
)
from src.config import DATASET_SEED, OTP_MAX_FAILED_ATTEMPTS, ROOT_DIR
from src.db.models import (
    AuthSession,
    Complaint,
    Escalation,
    InvestigationLog,
    PolicyDocument,
    Resolution,
    Ticket,
    ToolResult,
    User,
)
from src.observability.context import bind_context, clear_context
from src.observability.logging_config import configure_logging
from src.observability.tracing import configure_tracing, instrument_fastapi_app
from src.rag.ingest import delete_document as _delete_policy_document
from src.rag.ingest import ingest_document
from src.rag.search import search_policy_text
from src.services import reporting
from src.services.complaint_intake import create_ticket_with_fraud_check
from src.tools.base import ToolError, new_id
from src.tools.escalate_ticket import escalate_ticket as _escalate_ticket
from src.tools.get_customer_history import get_customer_history as _get_customer_history
from src.tools.lookup_transaction import lookup_transaction as _lookup_transaction
from src.tools.propose_resolution import propose_resolution as _propose_resolution

configure_logging()  # JSON stdout, gắn correlation_id/user_id tự động — xem
# src/observability/logging_config.py. Gọi Ở ĐÂY (module import time, trước
# khi bất kỳ route/middleware nào chạy) để MỌI logger trong process (kể cả
# uvicorn.access nếu propagate) dùng chung 1 format ngay từ request đầu tiên.
configure_tracing()  # OTel -> Jaeger (OTEL_EXPORTER_OTLP_ENDPOINT, mặc định
# localhost:4317) — graceful-degrade nếu Jaeger không sống, xem tracing.py.

limiter = Limiter(key_func=get_remote_address)

app = FastAPI(title="FIN-05 AI Agent CSKH — Backend", version="0.1.0")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
instrument_fastapi_app(app)  # auto-instrument tầng HTTP (Giai đoạn 4) — span
# request/response tự động, KHÔNG tự viết tay span cho những gì framework đã lo.

# KHÔNG có CORSMiddleware — cố ý. Frontend (Next.js, frontend/) gọi qua BFF
# proxy (route handler server-side, xem frontend/src/app/api/), tức là
# server-to-server, không phải request từ trình duyệt nên không bị/cần CORS
# chi phối. JWT nằm trong cookie httpOnly, JS phía trình duyệt không đọc
# được để tự gắn Authorization header — mở CORS cho localhost:3000 sẽ không
# giúp ích gì (không có token để gọi) mà chỉ mở thêm bề mặt tấn công (VD
# site độc hại chạy trên trình duyệt nạn nhân fetch thẳng origin này). Nếu
# cần debug tay, dùng Swagger UI tại chính origin của API (same-origin,
# không cần CORS) hoặc curl.


# ---------------------------------------------------------------------------
# Audit log — ai gọi API nào, khi nào, kết quả gì. Ghi ra file riêng
# (logs/access.log), tách khỏi log ứng dụng, để tra cứu sự cố bảo mật không
# phải lục log lẫn với debug thường ngày.
# ---------------------------------------------------------------------------

_LOG_DIR = ROOT_DIR / "logs"
_LOG_DIR.mkdir(exist_ok=True)
_access_logger = logging.getLogger("fin05.access")
_access_logger.setLevel(logging.INFO)
if not _access_logger.handlers:
    _handler = logging.FileHandler(_LOG_DIR / "access.log", encoding="utf-8")
    _handler.setFormatter(logging.Formatter("%(message)s"))
    _access_logger.addHandler(_handler)
    _access_logger.propagate = False


@app.middleware("http")
async def audit_log_middleware(request: Request, call_next):
    start = time.monotonic()
    identity = "anonymous"
    user_id = None
    auth_header = request.headers.get("authorization", "")
    if auth_header.lower().startswith("bearer "):
        current_user = try_decode(auth_header.split(" ", 1)[1])
        if current_user:
            identity = f"{current_user.user_id}:{current_user.role}"
            user_id = current_user.user_id
        else:
            identity = "invalid-token"

    # correlation_id: nhận lại `X-Request-ID` nếu client/proxy đã gắn sẵn (vd
    # Caddy, xem docs/DEPLOY.md), tự sinh nếu không có — gắn 1 LẦN Ở ĐÂY qua
    # contextvars (src/observability/context.py), mọi log/span bên trong
    # request này (kể cả sâu trong agent/tool) tự động thừa hưởng, không cần
    # truyền tay qua tham số hàm. `reset()` trong finally — BẮT BUỘC theo
    # đúng checklist observability Giai đoạn 2, chống rò rỉ context sang
    # request kế tiếp nếu thread/task bị tái sử dụng.
    correlation_id = request.headers.get("x-request-id") or f"req-{uuid.uuid4().hex[:16]}"
    tokens = bind_context(correlation_id=correlation_id, user_id=user_id)
    try:
        response = await call_next(request)
    finally:
        clear_context(tokens)
    response.headers["X-Correlation-Id"] = correlation_id

    _access_logger.info(
        json.dumps(
            {
                "ts": dt.datetime.utcnow().isoformat(),
                "correlation_id": correlation_id,
                "ip": request.client.host if request.client else None,
                "method": request.method,
                "path": request.url.path,
                "status": response.status_code,
                "identity": identity,
                "duration_ms": round((time.monotonic() - start) * 1000, 1),
            },
            ensure_ascii=False,
        )
    )
    return response


def _handle_tool_error(fn, *args, **kwargs):
    try:
        return fn(*args, **kwargs)
    except ToolError as e:
        raise HTTPException(status_code=400, detail=str(e)) from e


# ---------------------------------------------------------------------------
# /auth/login — không có mật khẩu thật (xem LoginRequest); chỉ định danh
# phone + role khai báo phải khớp role thật trong DB, phát JWT nếu đúng.
# Rate-limit chặt hơn route khác — chống dò số điện thoại hàng loạt.
# ---------------------------------------------------------------------------


@app.post("/auth/login")
@limiter.limit("10/minute")
def login(request: Request, req: LoginRequest, session: Session = Depends(get_session)):
    user = session.scalar(select(User).where(User.phone == req.phone))
    if user is None or user.role != req.role:
        raise HTTPException(status_code=401, detail="Số điện thoại hoặc vai trò không khớp")
    token = create_access_token(user_id=user.user_id, role=user.role)
    return {
        "user_id": user.user_id,
        "role": user.role,
        "full_name": user.full_name,
        "access_token": token,
    }


# ---------------------------------------------------------------------------
# /auth/otp/* — OTP phiên làm việc + câu hỏi bảo mật THẬT ở backend (Brief §7
# #4). TRƯỚC bản vá này, OTP chỉ là gate UI mô phỏng ở frontend
# (ChatClient.tsx) — backend không kiểm tra gì, nghĩa là gọi thẳng
# /tools/lookup_transaction bằng JWT hợp lệ vẫn lấy được dữ liệu nhạy cảm mà
# không cần xác thực OTP (phát hiện thật khi đối chiếu bộ QA test AUTH-*).
# `AuthSession`/`User.security_answer_hash` đã có sẵn trong data model (dùng
# để tính FS-06/FS-11 từ dữ liệu lịch sử) — giờ mới có endpoint thật ghi/đọc
# lúc runtime.
# ---------------------------------------------------------------------------


@app.post("/auth/otp/request")
@limiter.limit("10/minute")
def request_otp(
    request: Request,
    current_user: CurrentUser = Depends(require_role("customer")),
    session: Session = Depends(get_session),
):
    user = session.get(User, current_user.user_id)
    otp_code = f"{random.randint(0, 999999):06d}"
    session.add(
        AuthSession(
            session_id=new_id("SES"),
            user_id=current_user.user_id,
            otp_code=otp_code,
            otp_status="pending",
            security_q_passed=False,
            failed_attempts=0,
            created_at=dt.datetime.utcnow(),
        )
    )
    return {
        "security_question": user.security_question,
        "otp_code": otp_code,
        "note": (
            "Môi trường demo — mã OTP trả trực tiếp ở đây để tiện test/tự động hoá "
            "(sản phẩm thật sẽ gửi qua SMS, KHÔNG BAO GIỜ trả OTP qua API response). "
            "Câu trả lời bảo mật KHÔNG được trả qua API — xem docs/TESTING.md để biết "
            "công thức tính (chỉ áp dụng ở môi trường demo/seed cố định)."
        ),
    }


@app.post("/auth/otp/verify")
@limiter.limit("10/minute")
def verify_otp(
    request: Request,
    req: OtpVerifyRequest,
    current_user: CurrentUser = Depends(require_role("customer")),
    session: Session = Depends(get_session),
):
    user = session.get(User, current_user.user_id)
    auth_session = session.scalar(
        select(AuthSession)
        .where(AuthSession.user_id == current_user.user_id)
        .order_by(AuthSession.created_at.desc())
    )
    if auth_session is None:
        raise HTTPException(status_code=400, detail="Chưa yêu cầu OTP — gọi /auth/otp/request trước")
    if auth_session.locked_at is not None:
        raise HTTPException(
            status_code=403, detail="Phiên xác thực đã bị khoá do sai quá nhiều lần — yêu cầu OTP mới"
        )

    expected_answer = f"ans-{DATASET_SEED}-{current_user.user_id}"
    otp_ok = req.otp_code == auth_session.otp_code
    answer_ok = hashlib.sha256(req.security_answer.encode()).hexdigest() == user.security_answer_hash
    # Demo: chấp nhận thêm đúng công thức plaintext (không phải hash) để tiện
    # test tay/Playwright mà không cần tự tính SHA-256 — vẫn giữ đường hash
    # thật ở trên cho trường hợp client tự hash trước khi gửi.
    if not answer_ok:
        answer_ok = req.security_answer == expected_answer

    if not (otp_ok and answer_ok):
        auth_session.failed_attempts += 1
        # commit() Ở ĐÂY, TRƯỚC KHI raise — get_session() (src/api/deps.py)
        # rollback() bất kỳ exception nào thoát khỏi route, kể cả
        # HTTPException chủ động raise. Thiếu commit() này thì failed_attempts
        # vừa tăng bị CUỐN NGƯỢC mỗi lần, khoá sau N lần sai KHÔNG BAO GIỜ
        # thật sự xảy ra qua HTTP thật — phát hiện thật lúc test tay qua UI
        # (bấm sai nhiều lần liên tục không thấy khoá), dù test tự động
        # trước đó pass NHẦM vì fixture test dùng chung 1 Session không qua
        # commit/rollback như get_session() thật (xem test_otp.py).
        if auth_session.failed_attempts >= OTP_MAX_FAILED_ATTEMPTS:
            auth_session.locked_at = dt.datetime.utcnow()
            session.commit()
            raise HTTPException(
                status_code=403,
                detail=f"Sai quá {OTP_MAX_FAILED_ATTEMPTS} lần — phiên xác thực đã bị khoá, yêu cầu OTP mới",
            )
        session.commit()
        raise HTTPException(status_code=401, detail="Mã OTP hoặc câu trả lời bảo mật không đúng")

    auth_session.otp_status = "verified"
    auth_session.security_q_passed = True
    # utcfromtimestamp (KHÔNG phải fromtimestamp — tránh lệch theo timezone máy
    # chủ) để tái tạo đúng iat gốc, giữ nguyên thread_id hội thoại (user_id:iat,
    # xem src/agents/graph.py) không đổi giữa chừng phiên chat khi cấp JWT mới.
    now = dt.datetime.utcnow()
    new_token = create_access_token(
        user_id=current_user.user_id,
        role=current_user.role,
        otp_verified_at=now,
        iat=dt.datetime.utcfromtimestamp(current_user.iat),
    )
    return {"access_token": new_token, "otp_verified": True}


# ---------------------------------------------------------------------------
# /tools/* — agent gọi. Danh tính (user_id) luôn lấy từ token, không nhận từ
# body — đóng lỗ hổng "tự khai user_id bất kỳ để đọc/tạo dữ liệu hộ người khác".
# ---------------------------------------------------------------------------


@app.post("/tools/lookup_transaction")
def lookup_transaction(
    req: LookupTransactionRequest,
    current_user: CurrentUser = Depends(get_current_user),
    session: Session = Depends(get_session),
):
    # KHÔNG gắn require_otp_verified ở đây (dù có ở agent path — xem
    # customer_tools.py) — route này còn phục vụ CSKH/sếp tra cứu khi xử lý
    # ticket (ALL_ROLES) và khách hàng dùng gián tiếp qua rail "Giao dịch gần
    # đây" (ChatClient.tsx) NGAY KHI vào trang, trước khi có cơ hội xác thực
    # OTP — chặn ở đây sẽ phá UX xem thông tin cơ bản đã có từ trước khi làm
    # việc này. Thao tác THẬT SỰ nhạy cảm (agent chủ động điều tra/tạo ticket
    # giữa hội thoại) đã được chặn đúng chỗ — xem create_ticket bên dưới và
    # customer_tools.py.
    return _handle_tool_error(
        _lookup_transaction, session, requesting_user_id=current_user.user_id, **req.model_dump()
    )


@app.post("/tools/get_customer_history")
def get_customer_history(
    req: GetCustomerHistoryRequest,
    current_user: CurrentUser = Depends(require_role("customer")),
    session: Session = Depends(get_session),
):
    # Lý do không gắn require_otp_verified: xem comment ở lookup_transaction.
    return _handle_tool_error(
        _get_customer_history, session, user_id=current_user.user_id, **req.model_dump()
    )


@app.post("/tools/create_ticket")
def create_ticket(
    req: CreateTicketRequest,
    current_user: CurrentUser = Depends(require_role("customer")),
    _otp: CurrentUser = Depends(require_otp_verified),
    session: Session = Depends(get_session),
):
    # fraud_signals KHÔNG do caller truyền — tự tính ở tầng service (§4.1
    # FIN05-Backend-Handoff.md) từ dữ liệu DB, tránh agent tự bịa/quên tín hiệu.
    return _handle_tool_error(
        create_ticket_with_fraud_check, session, user_id=current_user.user_id, **req.model_dump()
    )


@app.post("/tools/propose_resolution")
def propose_resolution(
    req: ProposeResolutionRequest,
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    session: Session = Depends(get_session),
):
    return _handle_tool_error(_propose_resolution, session, **req.model_dump())


@app.post("/tools/escalate_ticket")
def escalate_ticket(
    req: EscalateTicketRequest,
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    session: Session = Depends(get_session),
):
    return _handle_tool_error(
        _escalate_ticket, session, created_by=current_user.user_id, **req.model_dump()
    )


# ---------------------------------------------------------------------------
# /agent/chat — AI agent thật (LangGraph, src/agents/), thay luồng kịch bản
# cũ ở frontend. Chỉ phục vụ role=customer — agent không dùng cho CSKH/Sếp,
# CSKH/Sếp thao tác trực tiếp qua webapp (không qua chat).
# ---------------------------------------------------------------------------


@app.post("/agent/chat")
@limiter.limit("20/minute")
def agent_chat(
    request: Request,
    req: AgentChatRequest,
    current_user: CurrentUser = Depends(require_role("customer")),
    session: Session = Depends(get_session),
):
    # thread_id gắn theo PHIÊN đăng nhập (user_id + iat lúc login), không chỉ
    # user_id — checkpointer (src/agents/graph.py) dùng chung 1 instance suốt
    # vòng đời process, nếu chỉ khoá theo user_id thì đăng xuất rồi đăng nhập
    # lại (cùng process chưa restart) sẽ vẫn nối tiếp hội thoại phiên cũ, trái
    # PRD US-010 ("không giữ ngữ cảnh xuyên phiên đăng nhập khác nhau").
    return _handle_tool_error(
        run_agent_turn,
        session,
        user_id=current_user.user_id,
        message=req.message,
        thread_id=f"{current_user.user_id}:{current_user.iat}",
        otp_verified_at=current_user.otp_verified_at,
    )


# ---------------------------------------------------------------------------
# /tickets* — đọc, dùng cho UI CSKH/sếp. Không phải data khách hàng tự xem
# trực tiếp (khách theo dõi qua /agent/chat), nên giới hạn 2 role nội bộ.
# ---------------------------------------------------------------------------


@app.get("/tickets")
def list_tickets(
    hitl_status: str | None = None,
    limit: int = 50,
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    session: Session = Depends(get_session),
):
    stmt = select(Ticket).order_by(Ticket.created_at.desc()).limit(limit)
    if hitl_status:
        stmt = stmt.where(Ticket.hitl_status == hitl_status)
    tickets = session.scalars(stmt).all()
    # Dashboard CSKH cần loại/phạm vi/ưu tiên/tín hiệu gian lận ngay trên bảng
    # (US-011, US-014) — join 1 lần qua complaint_id thay vì N+1 request.
    complaints = {
        c.complaint_id: c
        for c in session.scalars(
            select(Complaint).where(Complaint.complaint_id.in_([t.complaint_id for t in tickets]))
        ).all()
    }
    users = {
        u.user_id: u
        for u in session.scalars(
            select(User).where(User.user_id.in_([c.user_id for c in complaints.values()]))
        ).all()
    }
    out = []
    for t in tickets:
        c = complaints.get(t.complaint_id)
        u = users.get(c.user_id) if c else None
        out.append(
            {
                "ticket_id": t.ticket_id,
                "complaint_id": t.complaint_id,
                "hitl_status": t.hitl_status,
                "sla_due_at": t.sla_due_at.isoformat(),
                "partner_wait_status": t.partner_wait_status,
                "created_at": t.created_at.isoformat(),
                "complaint_type": c.type if c else None,
                "scope": c.scope if c else None,
                "priority": c.priority if c else None,
                "fraud_signals": c.fraud_signals if c else [],
                "customer_name": u.full_name if u else None,
            }
        )
    return out


@app.get("/tickets/{ticket_id}")
def get_ticket_detail(
    ticket_id: str,
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    session: Session = Depends(get_session),
):
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="ticket không tồn tại")
    complaint = session.get(Complaint, ticket.complaint_id)
    resolutions = session.scalars(
        select(Resolution).where(Resolution.ticket_id == ticket_id).order_by(Resolution.created_at)
    ).all()
    escalations = session.scalars(
        select(Escalation).where(Escalation.ticket_id == ticket_id).order_by(Escalation.created_at)
    ).all()
    logs = session.scalars(
        select(InvestigationLog)
        .where(InvestigationLog.ticket_id == ticket_id)
        .order_by(InvestigationLog.step_no)
    ).all()
    return {
        "ticket": {
            "ticket_id": ticket.ticket_id,
            "hitl_status": ticket.hitl_status,
            "sla_due_at": ticket.sla_due_at.isoformat(),
            "partner_wait_status": ticket.partner_wait_status,
        },
        "complaint": {
            "complaint_id": complaint.complaint_id,
            "user_id": complaint.user_id,
            "trans_id": complaint.trans_id,
            "type": complaint.type,
            "scope": complaint.scope,
            "priority": complaint.priority,
            "description_raw": complaint.description_raw,
            "fraud_signals": complaint.fraud_signals,
        }
        if complaint
        else None,
        "resolutions": [
            {
                "resolution_id": r.resolution_id,
                "action_type": r.action_type,
                "amount": r.amount,
                "status": r.status,
                "rationale": r.rationale,
            }
            for r in resolutions
        ],
        "escalations": [
            {"escalation_id": e.escalation_id, "target": e.target, "reason": e.reason}
            for e in escalations
        ],
        "investigation_logs": [
            {
                "step_no": log.step_no,
                "tool_called": log.tool_called,
                "tool_input": log.tool_input_json,
                "tool_result_id": log.tool_result_id,
                "tool_result": session.get(ToolResult, log.tool_result_id).raw_json
                if log.tool_result_id
                else None,
                "agent_note": log.agent_note,
                "created_at": log.created_at.isoformat(),
            }
            for log in logs
        ],
    }


# ---------------------------------------------------------------------------
# HITL gate — CHỈ sếp gọi được. Con đường DUY NHẤT ghi status='approved'.
# approved_by/rejected_by giờ LUÔN là current_user.user_id (đã xác thực qua
# JWT) — trước đây client tự khai approved_by, nghĩa là ai cũng "duyệt" được
# miễn đoán đúng user_id của một sếp bất kỳ. Đây là lỗ hổng nghiêm trọng thứ 2
# đã vá, cùng nhóm với /agent/chat.
# ---------------------------------------------------------------------------


@app.post("/resolutions/{resolution_id}/approve")
def approve_resolution(
    resolution_id: str,
    current_user: CurrentUser = Depends(require_role("supervisor")),
    session: Session = Depends(get_session),
):
    resolution = session.get(Resolution, resolution_id)
    if resolution is None:
        raise HTTPException(status_code=404, detail="resolution không tồn tại")
    if resolution.status not in ("draft", "pending_approval"):
        raise HTTPException(
            status_code=400, detail=f"resolution đang ở trạng thái {resolution.status}, không duyệt được"
        )

    resolution.status = "approved"
    resolution.approved_by = current_user.user_id
    resolution.approved_at = dt.datetime.utcnow()
    session.flush()
    return {"resolution_id": resolution_id, "status": resolution.status, "approved_by": current_user.user_id}


@app.post("/resolutions/{resolution_id}/reject")
def reject_resolution(
    resolution_id: str,
    current_user: CurrentUser = Depends(require_role("supervisor")),
    session: Session = Depends(get_session),
):
    resolution = session.get(Resolution, resolution_id)
    if resolution is None:
        raise HTTPException(status_code=404, detail="resolution không tồn tại")

    resolution.status = "rejected"
    session.flush()
    return {"resolution_id": resolution_id, "status": resolution.status}


# ---------------------------------------------------------------------------
# /resolutions — hàng chờ phê duyệt cho Sếp
# ---------------------------------------------------------------------------


@app.get("/resolutions")
def list_resolutions(
    status: str | None = "pending_approval",
    limit: int = 50,
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    session: Session = Depends(get_session),
):
    stmt = select(Resolution).order_by(Resolution.created_at.desc()).limit(limit)
    if status and status != "all":
        stmt = stmt.where(Resolution.status == status)
    resolutions = session.scalars(stmt).all()
    approvers = {
        u.user_id: u
        for u in session.scalars(
            select(User).where(User.user_id.in_([r.approved_by for r in resolutions if r.approved_by]))
        ).all()
    }
    out = []
    for r in resolutions:
        ticket = session.get(Ticket, r.ticket_id)
        complaint = session.get(Complaint, ticket.complaint_id) if ticket else None
        approver = approvers.get(r.approved_by) if r.approved_by else None
        out.append(
            {
                "resolution_id": r.resolution_id,
                "ticket_id": r.ticket_id,
                "action_type": r.action_type,
                "amount": r.amount,
                "destination_ref": r.destination_ref,
                "rationale": r.rationale,
                "cited_tool_result_ids": r.cited_tool_result_ids,
                "status": r.status,
                "created_at": r.created_at.isoformat(),
                "complaint_type": complaint.type if complaint else None,
                "scope": complaint.scope if complaint else None,
                "approved_by_name": approver.full_name if approver else None,
                "approved_at": r.approved_at.isoformat() if r.approved_at else None,
            }
        )
    return out


# ---------------------------------------------------------------------------
# /tickets/{id}/request-more-info — CSKH yêu cầu điều tra thêm (US-012).
# Không phải HITL gate — không ghi approved, chỉ đổi hitl_status.
# ---------------------------------------------------------------------------


@app.post("/tickets/{ticket_id}/request-more-info")
def request_more_info(
    ticket_id: str,
    req: RequestMoreInfoRequest,
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    session: Session = Depends(get_session),
):
    ticket = session.get(Ticket, ticket_id)
    if ticket is None:
        raise HTTPException(status_code=404, detail="ticket không tồn tại")

    now = dt.datetime.utcnow()
    ticket.hitl_status = "need_more_info"
    ticket.updated_at = now

    last_step = session.scalar(
        select(InvestigationLog.step_no)
        .where(InvestigationLog.ticket_id == ticket_id)
        .order_by(InvestigationLog.step_no.desc())
    )
    session.add(
        InvestigationLog(
            log_id=new_id("LOG"),
            ticket_id=ticket_id,
            step_no=(last_step or 0) + 1,
            tool_called="cskh_request_more_info",
            tool_input_json={"requested_by": current_user.user_id},
            agent_note=req.note,
            created_at=now,
        )
    )
    session.flush()
    return {"ticket_id": ticket_id, "hitl_status": ticket.hitl_status}


# ---------------------------------------------------------------------------
# /reports/summary — US-018, số liệu tính trực tiếp từ DB (PRD §12: không ước lượng)
# ---------------------------------------------------------------------------


@app.get("/reports/summary")
def report_summary(
    date_from: dt.datetime | None = None,
    date_to: dt.datetime | None = None,
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    session: Session = Depends(get_session),
):
    return reporting.build_summary(session, date_from=date_from, date_to=date_to)


# ---------------------------------------------------------------------------
# /policy-docs* — RAG chính sách/FAQ (src/rag/). Upload/xoá CHỈ role
# partner_admin (đối tác ví điện tử, tách khỏi supervisor nội bộ) — đây là
# actor duy nhất được đưa tài liệu mới vào hệ thống mà agent/CSKH sẽ tin
# tưởng, nên phân quyền chặt hơn các route /tools/* khác.
# ---------------------------------------------------------------------------


@app.post("/policy-docs")
@limiter.limit("20/hour")
def upload_policy_doc(
    request: Request,
    file: UploadFile = File(...),
    current_user: CurrentUser = Depends(require_role("partner_admin")),
    session: Session = Depends(get_session),
):
    file_bytes = file.file.read()
    doc = _handle_tool_error(
        ingest_document,
        session,
        file_bytes=file_bytes,
        filename=file.filename or "untitled",
        uploaded_by=current_user.user_id,
    )
    return {
        "doc_id": doc.doc_id,
        "filename": doc.filename,
        "status": doc.status,
        "chunk_count": doc.chunk_count,
        "error_message": doc.error_message,
    }


@app.get("/policy-docs")
def list_policy_docs(
    current_user: CurrentUser = Depends(require_role("partner_admin")),
    session: Session = Depends(get_session),
):
    docs = session.scalars(select(PolicyDocument).order_by(PolicyDocument.uploaded_at.desc())).all()
    uploaders = {
        u.user_id: u
        for u in session.scalars(select(User).where(User.user_id.in_([d.uploaded_by for d in docs]))).all()
    }
    return [
        {
            "doc_id": d.doc_id,
            "filename": d.filename,
            "uploaded_at": d.uploaded_at.isoformat(),
            "uploaded_by_name": uploaders[d.uploaded_by].full_name if d.uploaded_by in uploaders else None,
            "status": d.status,
            "chunk_count": d.chunk_count,
            "error_message": d.error_message,
        }
        for d in docs
    ]


@app.delete("/policy-docs/{doc_id}")
def delete_policy_doc(
    doc_id: str,
    current_user: CurrentUser = Depends(require_role("partner_admin")),
    session: Session = Depends(get_session),
):
    _handle_tool_error(_delete_policy_document, session, doc_id)
    return {"doc_id": doc_id, "status": "deleted"}


# ---------------------------------------------------------------------------
# /policy-search — công cụ tra cứu chính sách riêng cho CSKH (retrieval
# thuần, không qua LLM sinh câu trả lời — xem quyết định thiết kế trong
# plan). Dùng chung logic với tool search_policy của agent (src/rag/search.py).
# ---------------------------------------------------------------------------


@app.post("/policy-search")
def policy_search(
    req: PolicySearchRequest,
    current_user: CurrentUser = Depends(require_role("cskh", "supervisor")),
    session: Session = Depends(get_session),
):
    return _handle_tool_error(search_policy_text, session, query=req.query)


@app.get("/health")
def health():
    return {"status": "ok"}
