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
from typing import Literal

from pydantic import BaseModel, Field, model_validator


class LookupTransactionRequest(BaseModel):
    trans_id: str | None = None
    rec_code: str | None = None
    phone: str | None = None
    amount: int | None = None
    date_from: dt.datetime | None = None
    date_to: dt.datetime | None = None


class GetCustomerHistoryRequest(BaseModel):
    days: int = 90
    limit_transactions: int = 20


class CreateTicketRequest(BaseModel):
    complaint_type: str
    scope: str
    # A2 — trần 2.000 ký tự (ADR-025 QĐ 5). Ép ở ĐÂY là lớp CHÍNH XÁC duy nhất
    # theo KÝ TỰ; tầng DB không làm được vì cột đã mã hoá (xem models.py).
    description_raw: str = Field(max_length=2000)
    trans_id: str | None = None
    otp_disclosed: bool = False
    # Không nhận fraud_signals từ caller — tầng service (complaint_intake.py)
    # tự tính từ dữ liệu DB qua fraud_engine.py (Data Brief §4.2: "do tầng
    # service tính, không phải do agent tự điền").


class ProposeResolutionRequest(BaseModel):
    ticket_id: str
    action_type: str
    rationale: str
    amount: int | None = None
    destination_ref: str | None = None
    cited_tool_result_ids: list[str] | None = None


class ApproveResolutionRequest(BaseModel):
    """AUTH5-04/05/05B (đợt nâng cấp Auth Flow 2026-08-12) — sếp phải xin OTP
    riêng cho ĐÚNG resolution_id này (POST .../request-approval-otp) trước,
    rồi mới duyệt được — không dùng chung OTP đã xác thực cho case khác.

    `session_id` (vá race condition, 2026-08-13 — cùng lý do OtpVerifyRequest)
    — tra thẳng theo khoá chính AuthSession, không còn "mới nhất theo
    resolution_id"."""

    session_id: str
    otp_code: str


class RejectResolutionRequest(BaseModel):
    """ADR-019 — từ chối PHẢI kèm lý do có cấu trúc.

    Dùng `Literal` chứ không phải `str`: giá trị sai bị chặn ngay ở tầng schema
    với thông báo liệt kê đủ lựa chọn, thay vì để CHECK constraint ném
    IntegrityError 500 xuống người dùng. Hai lớp cùng canh một luật là CÓ CHỦ
    ĐÍCH — schema lo trải nghiệm, CHECK lo toàn vẹn kể cả khi có ai ghi thẳng
    vào DB (lý do đầy đủ ở ADR-019).

    `note` (ADR-024, TM-03 sign-off security) — ghi chú tự do khi từ chối.
    Scrub PII + cờ injection thật diễn ra ở route (`src/api/main.py`), KHÔNG ở
    đây: schema chỉ lo hình dạng (độ dài, có/thiếu), không chạm dữ liệu nhạy
    cảm trước khi tới tầng scrub.

    `max_length=500` bắt lỗi 501 ký tự ở TẦNG SCHEMA (422, thông báo rõ ràng)
    thay vì để CHECK constraint tầng DB ném IntegrityError 500 — cùng triết lý
    "schema lo trải nghiệm, CHECK lo toàn vẹn" đã áp cho `reason` ở trên.

    Chuẩn hoá rỗng/toàn-khoảng-trắng THÀNH thiếu (`None`) trước khi áp luật
    "bắt buộc khi reason='khac'": đây là đường lách kinh điển — một validator
    chỉ kiểm `note is not None` thì một dấu cách là qua được.
    """

    reason: Literal[
        "sai_so_lieu",
        "sai_phan_loai",
        "thieu_can_cu",
        "sai_chinh_sach",
        "trung_case",
        "khach_rut",
        "khac",
    ]
    note: str | None = Field(default=None, max_length=500)

    @model_validator(mode="after")
    def _note_bat_buoc_khi_khac(self) -> RejectResolutionRequest:
        if self.note is not None and not self.note.strip():
            self.note = None
        if self.reason == "khac" and not self.note:
            raise ValueError(
                "note bắt buộc khi reason='khac' — 'lý do khác' không có ghi chú "
                "thì bản ghi kiểm toán rỗng nghĩa"
            )
        return self


class EscalateTicketRequest(BaseModel):
    ticket_id: str
    target: str
    reason: str


class LoginRequest(BaseModel):
    """Đăng nhập bằng mật khẩu thật (quyết định 2026-08-12 — thay luồng
    phone+role chọn tay trước đó). KHÔNG còn field `role` — vai trò lấy từ
    chính user tìm được qua `phone` trong DB, không do client tự khai (đúng
    nguyên tắc "danh tính không bao giờ tự khai" đã áp dụng xuyên suốt file
    này)."""

    phone: str
    password: str


class RefreshTokenRequest(BaseModel):
    """AUTH5-02/03 (đợt nâng cấp Auth Flow 2026-08-12) — refresh_token KHÔNG
    phải JWT (chuỗi ngẫu nhiên, xem src/auth.py::mint_refresh_token), gửi
    trong body vì backend không có quyền truy cập cookie trình duyệt (kiến
    trúc BFF — chỉ Next.js route handler đọc cookie httpOnly rồi forward)."""

    refresh_token: str


class RequestMoreInfoRequest(BaseModel):
    note: str | None = None


class OtpVerifyRequest(BaseModel):
    """AUTH5-01 (đợt nâng cấp Auth Flow 2026-08-12) — `security_answer` đã bỏ:
    câu hỏi bảo mật không còn là authenticator (NIST SP 800-63B-4), mã OTP là
    yếu tố step-up duy nhất.

    `session_id` (vá race condition, 2026-08-13) — bắt buộc, phải khớp ĐÚNG
    AuthSession trả về từ /auth/otp/request vừa gọi. Trước đây verify chỉ tra
    "AuthSession mới nhất của user" — dưới tải đồng thời thật (FastAPI chạy
    route sync trong threadpool, nhiều thread cùng ghi SQLite WAL), 1 request
    verify có thể đọc phải snapshot CŨ chưa thấy AuthSession vừa tạo, so
    nhầm với mã OTP của phiên trước đó và từ chối nhầm mã đúng. Tra thẳng
    theo session_id (khoá chính) loại bỏ hoàn toàn sự mơ hồ này — không phụ
    thuộc "mới nhất theo thời gian" nữa."""

    session_id: str
    otp_code: str


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
