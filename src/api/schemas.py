"""Pydantic request bodies cho các endpoint tool — validation tầng biên,
trước khi chạm tới logic nghiệp vụ trong src/tools/.

Vá bảo mật: KHÔNG còn field nào mang danh tính người gọi (user_id,
requesting_user_id, approved_by, rejected_by, created_by, requested_by).
Trước đây client tự khai các field này trong body — nghĩa là ai gọi API
cũng mạo danh được bất kỳ user nào (VD tự xưng approved_by = một sếp bất kỳ
để duyệt hoàn tiền). Danh tính giờ LUÔN lấy từ JWT đã ký (src/auth.py,
`Depends(get_current_user)` ở src/api/main.py), không có đường nào khác."""
from __future__ import annotations

import datetime as dt
from typing import Optional

from pydantic import BaseModel, Field


class LookupTransactionRequest(BaseModel):
    trans_id: Optional[str] = None
    rec_code: Optional[str] = None
    phone: Optional[str] = None
    amount: Optional[int] = None
    date_from: Optional[dt.datetime] = None
    date_to: Optional[dt.datetime] = None


class GetCustomerHistoryRequest(BaseModel):
    days: int = 90
    limit_transactions: int = 20


class CreateTicketRequest(BaseModel):
    complaint_type: str
    scope: str
    description_raw: str
    trans_id: Optional[str] = None
    otp_disclosed: bool = False
    # Không nhận fraud_signals từ caller — tầng service (complaint_intake.py)
    # tự tính từ dữ liệu DB qua fraud_engine.py (Data Brief §4.2: "do tầng
    # service tính, không phải do agent tự điền").


class ProposeResolutionRequest(BaseModel):
    ticket_id: str
    action_type: str
    rationale: str
    amount: Optional[int] = None
    destination_ref: Optional[str] = None
    cited_tool_result_ids: Optional[list[str]] = None


class EscalateTicketRequest(BaseModel):
    ticket_id: str
    target: str
    reason: str


class LoginRequest(BaseModel):
    """Không có mật khẩu — Brief §7 chỉ yêu cầu OTP phiên + câu hỏi bảo mật
    cho thao tác nhạy cảm, không có hạ tầng mật khẩu thật trong dataset
    (`users` không có cột password). Định danh bằng phone + role khai báo,
    role phải khớp role thật của user trong DB mới cho vào."""
    phone: str
    role: str


class RequestMoreInfoRequest(BaseModel):
    note: Optional[str] = None


class OtpVerifyRequest(BaseModel):
    otp_code: str
    security_answer: str


class AgentChatRequest(BaseModel):
    # max_length=4000 (CONSUME-001, FIN05_QA_TestCases.jsonl, OWASP LLM10:2025
    # Unbounded Consumption) — trước đây KHÔNG giới hạn gì, 1 message dài bất
    # thường (vd flood hàng chục nghìn ký tự) vẫn được chuyển thẳng vào ngữ
    # cảnh LLM, tốn token/tiền không kiểm soát. 4000 ký tự đủ rộng cho hội
    # thoại CSKH thật (khiếu nại dài nhất trong dataset mẫu chưa tới 500 ký
    # tự), FastAPI/Pydantic tự trả 422 rõ ràng khi vượt — không cần code tay.
    message: str = Field(max_length=4000)


class PolicySearchRequest(BaseModel):
    query: str


class LiveChatWsTicketRequest(BaseModel):
    """Live chat (2026-08-11) — khách bấm "gặp người thật" cho 1 ticket ĐÃ
    có sẵn (human_handoff_requested, tạo qua request_human_handoff)."""
    ticket_id: str


class LiveChatCsatRequest(BaseModel):
    score: int = Field(ge=1, le=5)
