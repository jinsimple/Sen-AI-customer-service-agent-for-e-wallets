"""Nối `scripts/fraud_engine.py` (script thuần, không chạm DB) vào tool
`create_ticket` (§4.1 FIN05-Backend-Handoff.md).

Data Brief §4.2: `complaints.fraud_signals` "do tầng service tính từ dữ
liệu, không phải do agent tự điền" — đây là tầng service đó. Tool
`create_ticket` giữ mỏng, không tự tính tín hiệu; nơi DUY NHẤT chuyển dữ
liệu từ DB (SQLAlchemy rows) sang định dạng `LedgerIndex` (list[dict] như
JSONL) mà `fraud_engine.py` cần là ở đây.

Dùng `FraudEngine.evaluate()` để tính TOÀN BỘ tín hiệu (tái dùng nguyên
engine đã qua 16 nhóm kiểm định dataset, không viết lại — mã khác ngoài
FS-06 vẫn được lưu vào `complaints.fraud_signals`, dữ liệu thừa không sao).
Quyết định escalate/priority sau đó do `src.tools.fraud_policy.evaluate_escalation()`
quyết — phạm vi MVP chỉ `FS-06` (PRD §5). KHÔNG dùng `FraudEngine.decide()`
— đó là chính sách 2 tầng cũ của dataset gốc, chỉ còn dùng nội bộ ở
`scripts/validate_dataset.py` để tự kiểm định dataset, không áp cho sản phẩm.
"""
from __future__ import annotations

import datetime as dt
from functools import lru_cache
from typing import Any

import yaml
from sqlalchemy import select
from sqlalchemy.orm import Session

from scripts.fraud_engine import FraudEngine, LedgerIndex
from src.config import DATA_SCHEMA_DIR
from src.db.models import AuthSession, BankAccount, Complaint, Ticket, Transaction, User, Wallet
from src.tools.create_ticket import create_ticket as _create_ticket

# A2 (ADR-025 QĐ 5) — ≈300-400 từ tiếng Việt: đủ tường thuật chi tiết một vụ,
# gấp nhiều lần khiếu nại điển hình, chặn được flood 20.000 ký tự.
MAX_DESCRIPTION_CHARS = 2000


@lru_cache(maxsize=1)
def _load_fraud_config() -> dict:
    path = DATA_SCHEMA_DIR / "fraud_signals.yaml"
    return yaml.safe_load(path.read_text(encoding="utf-8"))


def _rows_as_dicts(session: Session, model: Any) -> list[dict]:
    cols = model.__table__.columns.keys()
    return [{c: getattr(row, c) for c in cols} for row in session.scalars(select(model))]


def _build_engine(session: Session) -> FraudEngine:
    """Nạp toàn bộ dữ liệu nền hiện có trong DB thành LedgerIndex. Quy mô demo
    (60k transactions, vài trăm dòng các bảng khác) nên nạp lại mỗi lần gọi
    là đủ nhanh — không cần cache, tránh rủi ro đọc dữ liệu cũ sau khi có
    ticket/complaint mới."""
    idx = LedgerIndex(
        _rows_as_dicts(session, User),
        _rows_as_dicts(session, Wallet),
        _rows_as_dicts(session, BankAccount),
        _rows_as_dicts(session, Transaction),
        _rows_as_dicts(session, Complaint),
        _rows_as_dicts(session, AuthSession),
        _rows_as_dicts(session, Ticket),
    )
    return FraudEngine(_load_fraud_config(), idx)


def create_ticket_with_fraud_check(
    session: Session,
    *,
    user_id: str,
    complaint_type: str,
    scope: str,
    description_raw: str,
    trans_id: str | None = None,
    otp_disclosed: bool = False,
    now: dt.datetime | None = None,
    # ADR-044 — thread_id HIỆU LỰC của lượt sinh ra complaint này, ghi vào
    # Complaint.thread_id lúc TẠO (NULLABLE VĨNH VIỄN nếu None — caller cũ/
    # REST không có phiên chat). Luồn tới _create_ticket, KHÔNG tự suy đoán.
    thread_id: str | None = None,
) -> dict[str, Any]:
    """Tính tín hiệu gian lận từ dữ liệu DB rồi tạo ticket — thay vì để agent
    tự truyền `fraud_signals` tay (rủi ro agent quên/bịa tín hiệu). Đây là
    entrypoint agent/API nên gọi thay cho `create_ticket` trực tiếp khi
    `trans_id` có giá trị; case not_found (`trans_id=None`) vẫn tính được
    FS-09/FS-10/FS-11 (không cần giao dịch) rồi mới tạo ticket.
    """
    now = now or dt.datetime.utcnow()

    # A2 — trần 2.000 ký tự, ép ở ĐÂY vì đây là điểm HỘI TỤ của cả hai đường
    # ghi: REST (`main.py:538`) và AGENT (`customer_tools.py:620`). Đặt trần
    # chỉ ở `CreateTicketRequest` là hụt đường agent — tool `create_ticket`
    # KHÔNG có `args_schema`, nó dùng type hint trần nên Pydantic không áp
    # ràng buộc nào. Đúng bài học ADR-019/024: validate-chỉ-ở-route không bảo
    # vệ được cửa thứ hai.
    #
    # TỪ CHỐI chứ không CẮT BỚT: cắt là sửa lời khai của khách — trái ràng
    # buộc cứng 3 và làm hỏng giá trị chứng cứ, đúng lý do nhóm A không được
    # che lúc ghi.
    if len(description_raw) > MAX_DESCRIPTION_CHARS:
        raise ValueError(
            f"description_raw {len(description_raw)} ký tự, vượt trần "
            f"{MAX_DESCRIPTION_CHARS}. Không tự cắt bớt lời khai của khách — "
            f"tách thành nhiều khiếu nại hoặc yêu cầu khách tóm tắt."
        )

    engine = _build_engine(session)
    # QUAN TRỌNG: lấy tx từ engine.idx.tx_by_id (không tự query Transaction
    # riêng) — LedgerIndex gắn khoá "_created" ngay trên object trong lúc
    # dựng chỉ mục; evaluate()/receiver_first_time() đọc "_created" từ chính
    # object đó, dựng dict tách rời sẽ thiếu khoá này và vỡ KeyError.
    tx_dict = engine.idx.tx_by_id.get(trans_id) if trans_id is not None else None

    fired = engine.evaluate(
        user_id=user_id,
        tx=tx_dict,
        complaint_at=now,
        utterance_text=description_raw,
        otp_disclosed=otp_disclosed,
        refund_dest_ref=None,  # chưa xác định ở bước tạo ticket, chỉ có tại propose_resolution
    )

    return _create_ticket(
        session,
        user_id=user_id,
        complaint_type=complaint_type,
        scope=scope,
        description_raw=description_raw,
        trans_id=trans_id,
        otp_disclosed=otp_disclosed,
        fraud_signals=fired,
        now=now,
        thread_id=thread_id,
    )


def hop_nhat_tin_hieu_gian_lan(
    session: Session,
    *,
    thread_id: str,
    utterance_text: str,
    them_ma: list[str] | None = None,
) -> list[str] | None:
    """MẢNH 4 (⑨/FS-13) — chấm tín hiệu gian lận trên MỘT LƯỢT SAU và HỢP NHẤT
    vào khiếu nại đã tạo của chính thread đó.

    Trước bản này, `engine.evaluate()` chỉ được gọi ĐÚNG MỘT LẦN, với
    `utterance_text=description_raw` lúc TẠO VÉ. Hệ quả đo được: FS-13 dù có
    tồn tại cũng chỉ bắt được ca khách TỰ KHAI "có người hướng dẫn" ngay trong
    mô tả đầu — mà khách gọi việc của mình là "chuyển nhầm" thì không bao giờ
    chạm tới nó. Tức tín hiệu chỉ bật khi ta đã không cần nó.

    Trả danh sách tín hiệu SAU hợp nhất, hoặc `None` nếu không tìm thấy khiếu
    nại nào của thread (không phải lỗi — thread chưa tạo vé).

    🔴 HỢP NHẤT, TUYỆT ĐỐI KHÔNG GHI ĐÈ. Lượt sau gọi `evaluate()` với
    `tx=None`, nên FS-01…08/FS-12 KHÔNG tính lại được (chúng cần giao dịch).
    Gán thẳng `complaint.fraud_signals = fired_moi` sẽ XOÁ SẠCH tín hiệu bắt
    lúc tạo vé — **kể cả FS-06, tín hiệu DUY NHẤT đang escalate** — và xoá
    không lỗi, không log, không ai biết. Union là idempotent: gọi lại bao
    nhiêu lần cũng cho cùng kết quả.

    Khoá theo `Complaint.thread_id` (ADR-044), KHÔNG đoán theo mốc thời gian.
    ⚠️ KHAI GIỚI HẠN: một thread có thể mang nhiều khiếu nại; hàm này chọn cái
    MỚI NHẤT theo `created_at`. Ở đường gọi hiện tại điều đó là chính xác theo
    cấu trúc — cổng ⑨ bắn TỐI ĐA MỘT LẦN mỗi thread, ngay sau một `create_ticket`
    — nên "mới nhất" chính là vé vừa tạo. Nếu sau này có đường gọi khác, phải
    đọc lại câu này trước khi dùng.
    """
    complaint = session.scalar(
        select(Complaint)
        .where(Complaint.thread_id == thread_id)
        .order_by(Complaint.created_at.desc())
        .limit(1)
    )
    if complaint is None:
        return None

    engine = _build_engine(session)
    fired = engine.evaluate(
        user_id=complaint.user_id,
        tx=None,  # lượt sau không gắn với một giao dịch cụ thể nào
        complaint_at=complaint.created_at,
        utterance_text=utterance_text,
        otp_disclosed=False,  # đã tính lúc tạo vé; KHÔNG hạ cờ cũ ở đây
    )
    cu = list(complaint.fraud_signals or [])
    gop = sorted(set(cu) | set(fired) | set(them_ma or []))
    if gop != sorted(set(cu)):
        complaint.fraud_signals = gop
        session.flush()
    return gop


def flag_human_handoff(
    session: Session,
    *,
    user_id: str,
    reason: str,
    ticket_id: str | None = None,
    now: dt.datetime | None = None,
    # ADR-044 — CHỈ dùng khi tạo ticket MỚI (nhánh ticket_id=None dưới), luồn
    # xuống create_ticket_with_fraud_check. PO-agent 19/08: đường tạo vé
    # KHÔNG chỉ có tool create_ticket — flag_human_handoff cũng tự tạo vé khi
    # khách xin gặp người mà chưa có ticket, thiếu thread_id ở ĐÂY thì đúng
    # loại vé CẦN transcript nhất (bàn giao) lại KHÔNG có transcript.
    thread_id: str | None = None,
) -> dict[str, Any]:
    """CTRL-001 (FIN05_QA_TestCases.jsonl, 2026-08-11) — khách chủ động yêu
    cầu gặp người thật (ISO/IEC 25059 'user controllability'). Kiến trúc
    CSKH vẫn bất đồng bộ (dashboard, không phải live chat) — hàm này tạo/
    đánh dấu 1 Ticket THẬT với `human_handoff_requested=True` để CSKH thấy
    và ưu tiên xử lý, KHÔNG giả vờ có người đang chat trực tiếp ngay lúc này.

    `ticket_id`: nếu agent ĐÃ tạo ticket cho đúng vấn đề đang nói trong hội
    thoại này (tránh tạo trùng, cùng nguyên tắc đã áp dụng cho create_ticket)
    — chỉ set cờ lên ticket đó, PHẢI thuộc đúng `user_id` (chặn agent bị dụ
    flag nhầm ticket của người khác qua tham số này).
    Không có `ticket_id` — tạo ticket MỚI, complaint_type='other' (khách yêu
    cầu người thật không nhất thiết mô tả 1 trong 4 loại khiếu nại cụ thể).
    """
    now = now or dt.datetime.utcnow()

    if ticket_id is not None:
        ticket = session.get(Ticket, ticket_id)
        if ticket is None:
            raise ValueError(f"ticket_id không tồn tại: {ticket_id}")
        complaint = session.get(Complaint, ticket.complaint_id)
        if complaint is None or complaint.user_id != user_id:
            raise ValueError(f"ticket_id không thuộc user_id đang chat: {ticket_id}")
        ticket.human_handoff_requested = True
        # ADR-044 mục 4 — mốc BÀN GIAO thật, KHÔNG PHẢI lúc ticket được tạo
        # (ticket.created_at đã có, khác hẳn ý nghĩa). UI vẽ vạch phân cách
        # hội thoại tại mốc này. `updated_at` cũng đổi theo quy ước có sẵn
        # của cột đó (mọi lần sửa ticket), hai cột phục vụ hai câu hỏi khác
        # nhau ("sửa lần cuối khi nào" vs "bàn giao khi nào") — không gộp.
        ticket.handoff_at = now
        ticket.updated_at = now
        session.flush()
        return {"ticket_id": ticket.ticket_id, "human_handoff_requested": True, "created_new_ticket": False}

    created = create_ticket_with_fraud_check(
        session,
        user_id=user_id,
        complaint_type="other",
        # 🔴 TRƯỚC 17/08 đây là "internal_wallet" — một HẰNG SỐ CỨNG, tức
        # đường này BỊA ra một trong ba phạm vi thật mà không tra giao dịch nào.
        #
        # tester bắt được bằng hiệu số CSDL của đúng một lượt hết-giờ trên ngăn
        # xếp đo: `tool_results` 0->1 (chỉ MỘT dòng, và là create_ticket),
        # `investigation_logs` 0->0, `trans_id` rỗng — vậy mà
        # `scope=internal_wallet`. Không giao dịch nào được tra.
        #
        # Giá trị 'unknown' được thêm vào CHECK constraint ngày 11/08 CHO ĐÚNG
        # CA NÀY (xem models.py): "trước đây agent bị ép đoán bừa 1 trong 3 giá
        # trị thật... cho phép CSKH tự xác định thủ công thay vì AI bịa". Cơ chế
        # có sẵn từ sáu ngày trước; đường fallback này chưa bao giờ được cập
        # nhật theo — bản vá áp cho đường AGENT mà bỏ sót đường CODE.
        #
        # Áp cho CẢ HAI người gọi (graph.py hết-giờ · request_human_handoff):
        # không đường nào trong hai đường đó tra giao dịch, nên mọi giá trị
        # phạm vi cụ thể ở đây đều là bịa.
        scope="unknown",
        description_raw=reason,
        trans_id=None,
        now=now,
        thread_id=thread_id,
    )
    ticket = session.get(Ticket, created["ticket_id"])
    ticket.human_handoff_requested = True
    # ADR-044 mục 4 — vé MỚI sinh ra TỪ chính lượt bàn giao này (không có
    # ticket_id cũ để gắn cờ lên), nên handoff_at == created_at CÙNG giá trị
    # `now` — đúng, không phải trùng hợp: bàn giao và tạo vé xảy ra "đồng
    # thời" về mặt nghiệp vụ trong nhánh này.
    ticket.handoff_at = now
    session.flush()
    return {**created, "human_handoff_requested": True, "created_new_ticket": True}
