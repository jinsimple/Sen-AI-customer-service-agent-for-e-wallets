"""FIN-05 — SQLAlchemy 2.0 models.

Nguồn sự thật cho schema: docs/FIN05-Data-Brief.md §4.1 (ERD) và §4.2 (định
nghĩa bảng). Mọi thay đổi ở đây PHẢI đồng bộ ngược lại tài liệu đó — đây là
nơi các bất biến I1-I7 (§6.2) và ràng buộc HITL (BR-10, BR-11) được ép ở
tầng DB, không chỉ ở tầng prompt (xem Data Brief §6.6 "guardrail được test
ở tầng service/DB, không phải tầng prompt").
"""
from __future__ import annotations

import datetime as dt
from typing import Any

from sqlalchemy import (
    JSON,
    Boolean,
    CheckConstraint,
    DateTime,
    ForeignKey,
    Integer,
    String,
    Text,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column

from src.db.crypto_types import EncryptedString, EncryptedText


class Base(DeclarativeBase):
    pass


# ---------------------------------------------------------------------------
# Identity & tài khoản
# ---------------------------------------------------------------------------


class User(Base):
    __tablename__ = "users"
    __table_args__ = (
        # partner_admin — role riêng cho đối tác ví điện tử, tách khỏi
        # supervisor (sếp CSKH nội bộ). CHỈ role này được upload/xoá tài liệu
        # chính sách/FAQ (src/rag/, src/api/main.py::/policy-docs).
        CheckConstraint(
            "role IN ('customer','cskh','supervisor','partner_admin')", name="ck_users_role"
        ),
    )

    user_id: Mapped[str] = mapped_column(String, primary_key=True)
    role: Mapped[str] = mapped_column(String, nullable=False)
    full_name: Mapped[str] = mapped_column(String, nullable=False)
    phone: Mapped[str] = mapped_column(String, unique=True, nullable=False)
    email: Mapped[str | None] = mapped_column(String, nullable=True)
    kyc_level: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    security_question: Mapped[str | None] = mapped_column(Text, nullable=True)
    security_answer_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    # Đăng nhập bằng mật khẩu (quyết định 2026-08-12, thay luồng phone+role
    # chọn tay trước đó) — argon2id có salt (cùng thư viện/pattern đã dùng
    # cho security_answer_hash, xem scripts/gen_dataset.py). Nullable vì lý
    # do kỹ thuật migration (thêm cột vào bảng đã có dữ liệu), nhưng THỰC TẾ
    # luôn được seed đầy đủ — verify_otp không có "user không mật khẩu" nào
    # được tạo mới sau đợt này.
    password_hash: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)


class Wallet(Base):
    __tablename__ = "wallets"
    __table_args__ = (
        CheckConstraint("status IN ('active','frozen','closed')", name="ck_wallets_status"),
        CheckConstraint("balance >= 0", name="ck_wallets_balance_nonneg"),
    )

    wallet_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    balance: Mapped[int] = mapped_column(Integer, nullable=False)  # VND, INTEGER — I7
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")


class BankAccount(Base):
    __tablename__ = "bank_accounts"
    __table_args__ = (
        CheckConstraint("status IN ('active','closed')", name="ck_bank_accounts_status"),
    )

    bank_account_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    bank_code: Mapped[str] = mapped_column(String, nullable=False)
    # Mã hoá trong suốt ở tầng ORM (src/db/crypto_types.py) — bản đầy đủ vẫn
    # cần lưu (BR-07, chủ TK có quyền xem đủ số của chính mình), nhưng file
    # SQLite trên đĩa giờ chỉ chứa ciphertext, không phải số TK dạng thô.
    account_no: Mapped[str] = mapped_column(EncryptedString, nullable=False)
    card_last4: Mapped[str | None] = mapped_column(String, nullable=True)
    status: Mapped[str] = mapped_column(String, nullable=False, default="active")
    linked_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)


# ---------------------------------------------------------------------------
# Giao dịch — bảng lõi
# ---------------------------------------------------------------------------

_SCOPE_DIRECTION_CHECK = """
    (
        scope = 'internal_wallet'
        AND send_wal_id IS NOT NULL AND rec_wal_id IS NOT NULL
        AND send_bank_account_id IS NULL AND rec_bank_account_id IS NULL
    ) OR (
        scope = 'from_bank'
        AND send_bank_account_id IS NOT NULL AND rec_wal_id IS NOT NULL
        AND send_wal_id IS NULL AND rec_bank_account_id IS NULL
    ) OR (
        scope = 'to_bank'
        AND send_wal_id IS NOT NULL AND rec_bank_account_id IS NOT NULL
        AND send_bank_account_id IS NULL AND rec_wal_id IS NULL
    )
"""


class Transaction(Base):
    __tablename__ = "transactions"
    __table_args__ = (
        CheckConstraint(
            "status IN ('pending','processing','success','failed','refunded','on_hold')",
            name="ck_transactions_status",
        ),
        CheckConstraint(
            "scope IN ('internal_wallet','from_bank','to_bank')",
            name="ck_transactions_scope",
        ),
        CheckConstraint(
            "channel IN ('p2p','bank_transfer','card_topup','withdrawal')",
            name="ck_transactions_channel",
        ),
        CheckConstraint("amount > 0", name="ck_transactions_amount_positive"),
        CheckConstraint("fee >= 0", name="ck_transactions_fee_nonneg"),
        # I2 — mỗi scope khớp đúng một tổ hợp bên gửi/bên nhận (Data Brief §4.2/§6.2)
        CheckConstraint(_SCOPE_DIRECTION_CHECK, name="ck_transactions_scope_direction_i2"),
    )

    trans_id: Mapped[str] = mapped_column(String, primary_key=True)
    rec_code: Mapped[str] = mapped_column(String, nullable=False)
    send_wal_id: Mapped[str | None] = mapped_column(ForeignKey("wallets.wallet_id"), nullable=True)
    send_bank_account_id: Mapped[str | None] = mapped_column(
        ForeignKey("bank_accounts.bank_account_id"), nullable=True
    )
    rec_wal_id: Mapped[str | None] = mapped_column(ForeignKey("wallets.wallet_id"), nullable=True)
    rec_bank_account_id: Mapped[str | None] = mapped_column(
        ForeignKey("bank_accounts.bank_account_id"), nullable=True
    )
    amount: Mapped[int] = mapped_column(Integer, nullable=False)
    fee: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    status: Mapped[str] = mapped_column(String, nullable=False)
    scope: Mapped[str] = mapped_column(String, nullable=False)
    channel: Mapped[str] = mapped_column(String, nullable=False)
    idempotency_key: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)
    completed_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    des: Mapped[str | None] = mapped_column(Text, nullable=True)


class TransactionEvent(Base):
    __tablename__ = "transaction_events"
    __table_args__ = (
        CheckConstraint(
            "event_type IN ('initiated','debited','sent_to_partner','partner_ack',"
            "'credited','failed','held','refund_initiated','refunded')",
            name="ck_events_event_type",
        ),
        CheckConstraint(
            "actor IN ('wallet_system','partner_bank','cskh')", name="ck_events_actor"
        ),
    )

    event_id: Mapped[str] = mapped_column(String, primary_key=True)
    trans_id: Mapped[str] = mapped_column(ForeignKey("transactions.trans_id"), nullable=False)
    seq: Mapped[int] = mapped_column(Integer, nullable=False)
    event_type: Mapped[str] = mapped_column(String, nullable=False)
    actor: Mapped[str] = mapped_column(String, nullable=False)
    status_from: Mapped[str] = mapped_column(String, nullable=False)
    status_to: Mapped[str] = mapped_column(String, nullable=False)
    occurred_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)
    payload_json: Mapped[dict[str, Any] | None] = mapped_column(JSON, nullable=True)


# ---------------------------------------------------------------------------
# Khiếu nại → ticket → điều tra → đề xuất → duyệt
# ---------------------------------------------------------------------------


class Complaint(Base):
    __tablename__ = "complaints"
    __table_args__ = (
        CheckConstraint(
            # 'other' (2026-08-11, CTRL-001 FIN05_QA_TestCases.jsonl) — khách
            # yêu cầu gặp người thật KHÔNG kèm mô tả khớp 1 trong 4 loại khiếu
            # nại giao dịch cụ thể (vd hỏi han chung, chưa mô tả vấn đề gì) —
            # vẫn cần 1 Complaint/Ticket thật để CSKH nhận diện & xử lý, không
            # ép agent tự đoán bừa 1 trong 4 loại không khớp thực tế.
            "type IN ('wrong_recipient','money_not_received','double_charge','refund','other')",
            name="ck_complaints_type",
        ),
        CheckConstraint(
            # 'unknown' (2026-08-11, phát hiện qua functional_qa_set.jsonl case
            # NOTFOUND) — sau khi đã hỏi hết {CLARIFY_QUESTION_MAX_ROUNDS} lượt +
            # 1 câu hỏi phạm vi mà khách vẫn không xác định được (vd khách không
            # rành ví-ví/ngân hàng khác nhau thế nào), trước đây agent bị ép đoán
            # bừa 1 trong 3 giá trị thật — song song với 'other' của complaint_type
            # ở trên, cho phép CSKH tự xác định thủ công thay vì AI bịa.
            "scope IN ('internal_wallet','from_bank','to_bank','unknown')", name="ck_complaints_scope"
        ),
        CheckConstraint(
            "priority IN ('low','normal','high','critical')", name="ck_complaints_priority"
        ),
        CheckConstraint(
            # A2 — LƯỚI CHẶN CUỐI, KHÔNG PHẢI TRẦN NGHIỆP VỤ.
            #
            # Trần nghiệp vụ là 2.000 KÝ TỰ, ép ở `complaint_intake.
            # MAX_DESCRIPTION_CHARS` (điểm hội tụ REST + agent) và
            # `CreateTicketRequest`. Con số 12.000 dưới đây đếm CIPHERTEXT,
            # KHÔNG quy đổi ra 2.000 ký tự được — đừng ai "sửa cho khớp".
            #
            # Vì sao không quy đổi được: Fernet nở theo BYTE utf-8 còn trần
            # nghiệp vụ tính theo KÝ TỰ, mà số byte mỗi ký tự thì thay đổi.
            # Đo thật trên đúng 2.000 ký tự:
            #     ASCII thuần              2.764  (x1.38)
            #     tiếng Việt điển hình     3.596  (x1.80)
            #     tiếng Việt DÀY dấu       5.708  (x2.85)
            #     emoji 4 byte            10.764  (x5.38)
            # Bound 4.000 (suy từ tỉ lệ x1.9 đo ở 500 ký tự) CHẶN NHẦM hai ca
            # cuối — đó là lý do con số ở đây là 12.000 chứ không phải 4.000.
            #
            # Cái giá, ghi rõ để không ai tưởng lớp này chặt hơn thực tế:
            # 12.000 ciphertext ≈ 8.700 ký tự ASCII lọt qua tầng DB. Lớp này
            # CHỈ chặn thảm hoạ (flood 20.000 ký tự ⟹ ~27.600, trượt). Độ
            # chính xác nằm ở tầng service, không nằm ở đây — đây là chỗ
            # nguyên tắc "ép ở tầng DB" của ADR-024 KHÔNG chuyển sang được,
            # và ADR-025 QĐ 5 chấp nhận đánh đổi đó một cách có ý thức.
            "length(description_raw) <= 12000",
            name="ck_complaints_description_raw_tran_tho",
        ),
    )

    complaint_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    trans_id: Mapped[str | None] = mapped_column(ForeignKey("transactions.trans_id"), nullable=True)
    type: Mapped[str] = mapped_column(String, nullable=False)
    scope: Mapped[str] = mapped_column(String, nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="investigating")
    priority: Mapped[str] = mapped_column(String, nullable=False, default="normal")
    # A1 — LỜI KHAI CỦA KHÁCH, mã hoá at-rest. Đây là cửa untrusted duy nhất
    # còn plaintext sau khi chat content (:475) và RAG (:513) đã dùng
    # EncryptedText: không phải cơ chế mới, là bù cho ngang chuẩn đã có.
    #
    # KHÔNG scrub tại điểm ghi (khác hẳn `resolutions.note`/ADR-024): note là
    # văn bản NHÂN VIÊN gõ, còn đây là LỜI KHAI KHÁCH — che lúc ghi là mất bản
    # gốc, mất giá trị chứng cứ nếu khiếu nại đi tới NHNN/toà. Cơ chế che cho
    # nhóm A nằm ở tầng ĐỌC, chờ ADR-025.
    #
    # A1-04 — KHÔNG BACKFILL, VÀ ĐÂY LÀ QUYẾT ĐỊNH GHI RA, không phải hệ quả
    # im lặng của impl. Hàng `complaints` ghi TRƯỚC 2026-08-15 nằm PLAINTEXT
    # vĩnh viễn trên đĩa. Đường `InvalidToken` chỉ khiến chúng ĐỌC ĐƯỢC —
    # "đọc được" và "được mã hoá at-rest" là hai chuyện khác nhau, đừng đọc
    # cái trước thành cái sau.
    # Chấp nhận được HÔM NAY vì dữ liệu hiện có là seed/test và pilot đã hoãn.
    # Khi có dữ liệu khách THẬT, backfill là một quyết định RIÊNG phải ra
    # trước khi mở pilot — không tự động xảy ra nhờ bản vá này.
    #
    # KHÔNG có CHECK độ dài ở tầng DB (khác ADR-024 Quyết định 1) — không phải
    # bỏ quên: cột đã mã hoá thì `length()` đo CIPHERTEXT, mà tỉ lệ nở KHÔNG
    # cố định (đo thật: x1.90 ở 500 ký tự tiếng Việt có dấu → x1.72 ở 20.000,
    # vì Fernet nở theo BYTE utf-8 còn trần nghiệp vụ tính theo KÝ TỰ). Một
    # CHECK trên ciphertext không diễn đạt được trần theo ký tự. Trần thật ép
    # ở tầng schema (`CreateTicketRequest`), xem A2.
    description_raw: Mapped[str] = mapped_column(EncryptedText, nullable=False)
    # Tính từ tầng service (fraud_engine.py), KHÔNG do agent tự điền — Data Brief §4.2.
    fraud_signals: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    otp_disclosed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)


class Ticket(Base):
    __tablename__ = "tickets"
    __table_args__ = (
        CheckConstraint(
            "hitl_status IN ('pending','approved','rejected','need_more_info')",
            name="ck_tickets_hitl_status",
        ),
        CheckConstraint(
            "partner_wait_status IN ('n/a','waiting','overdue','responded')",
            name="ck_tickets_partner_wait_status",
        ),
    )

    ticket_id: Mapped[str] = mapped_column(String, primary_key=True)
    complaint_id: Mapped[str] = mapped_column(ForeignKey("complaints.complaint_id"), nullable=False)
    assigned_role: Mapped[str] = mapped_column(String, nullable=False, default="cskh")
    hitl_status: Mapped[str] = mapped_column(String, nullable=False, default="pending")
    sla_due_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)
    partner_wait_status: Mapped[str] = mapped_column(String, nullable=False, default="n/a")
    # CTRL-001 (2026-08-11) — khách chủ động yêu cầu gặp người thật (không
    # phải mọi ticket khẩn cấp/ưu tiên đều do khách yêu cầu — tách riêng
    # khỏi priority/fraud_signals, đúng tinh thần ISO/IEC 25059 "user
    # controllability"). CSKH dashboard lọc/đánh dấu riêng cờ này.
    human_handoff_requested: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)
    updated_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False)


class ToolResult(Base):
    """Nguồn sự thật duy nhất để đối chiếu chống bịa số liệu (T4, Data Brief §6.5)."""

    __tablename__ = "tool_results"

    tool_result_id: Mapped[str] = mapped_column(String, primary_key=True)
    tool_name: Mapped[str] = mapped_column(String, nullable=False)
    raw_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    content_hash: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=dt.datetime.utcnow)


class InvestigationLog(Base):
    __tablename__ = "investigation_logs"

    log_id: Mapped[str] = mapped_column(String, primary_key=True)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.ticket_id"), nullable=False)
    step_no: Mapped[int] = mapped_column(Integer, nullable=False)
    tool_called: Mapped[str] = mapped_column(String, nullable=False)
    tool_input_json: Mapped[dict[str, Any]] = mapped_column(JSON, nullable=False)
    tool_result_id: Mapped[str | None] = mapped_column(
        ForeignKey("tool_results.tool_result_id"), nullable=True
    )
    agent_note: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=dt.datetime.utcnow)


class Resolution(Base):
    """BR-10: agent chỉ đề xuất — luôn draft/pending_approval, không có đường ghi
    thẳng approved. approved ⟹ approved_by NOT NULL, ép bằng CHECK ở đây."""

    __tablename__ = "resolutions"
    __table_args__ = (
        CheckConstraint(
            "action_type IN ('refund_to_wallet','refund_to_bank','ledger_adjustment',"
            "'no_action','manual_review')",
            name="ck_resolutions_action_type",
        ),
        CheckConstraint(
            "status IN ('draft','pending_approval','approved','rejected')",
            name="ck_resolutions_status",
        ),
        CheckConstraint(
            "(status != 'approved') OR (approved_by IS NOT NULL AND approved_at IS NOT NULL)",
            name="ck_resolutions_approved_requires_approver_br10",
        ),
        # ADR-019 · INV-14 — ĐỐI XỨNG với BR-10 ở trên, cho nhánh từ chối.
        # Nhãn phán đoán của sếp là dữ liệu dùng để CHẤM ĐIỂM agent về sau, nên
        # nó phải được ép ở tầng DB chứ không ở route: một UPDATE viết thẳng SQL
        # hay một route mới quên kiểm tra đều bị chính database từ chối. Thiếu
        # chỗ này thì tập dữ liệu học sẽ thủng đúng ở những nơi khó phát hiện.
        CheckConstraint(
            "reject_reason IN ('sai_so_lieu','sai_phan_loai','thieu_can_cu',"
            "'sai_chinh_sach','trung_case','khach_rut','khac')",
            name="ck_resolutions_reject_reason",
        ),
        CheckConstraint(
            "(status != 'rejected') OR (reject_reason IS NOT NULL "
            "AND rejected_by IS NOT NULL AND rejected_at IS NOT NULL)",
            name="ck_resolutions_rejected_requires_reason_br11",
        ),
        # BR-12 maker-checker (ADR-020). Điều kiện `created_by IS NULL` là BẮT
        # BUỘC, không phải nới lỏng: cột đó nullable vĩnh viễn cho resolution có
        # trước nó (migration b2c3d4e5f6a7 — đoán tên người vào sổ kiểm toán còn
        # tệ hơn để trống), nên CHECK vô điều kiện sẽ vỡ ngay trên dữ liệu cũ.
        # Khi `approved_by` còn NULL thì `approved_by != created_by` cho NULL,
        # và CHECK coi NULL là THOẢ — nên không cần thêm vế cho resolution chưa
        # duyệt.
        # Biểu thức viết DÀI CÓ CHỦ ĐÍCH (dạng "C" security chốt sau khi dựng
        # bảng chân trị 6 ca). Ba cách viết đều ĐÚNG như nhau; chọn cách này vì:
        #  · dạng ngắn `approved_by != created_by` đúng nhờ logic BA TRỊ của SQL
        #    (NULL != x cho NULL, mà CHECK coi NULL là thoả) — đúng, nhưng đúng
        #    theo kiểu người đọc sau phải tự dựng lại lập luận trong đầu, và rất
        #    dễ bị "rút gọn" nhầm. Ràng buộc cứng không nên dựa vào suy luận tinh
        #    tế mà mỗi người phải làm lại.
        #  · dạng `IS DISTINCT FROM` cần SQLite >= 3.39; test chạy SQLite ở CI và
        #    trên máy người khác, không xác minh được bản ở mọi nơi.
        # Cách này chỉ dùng `IS NULL` và `!=` — chạy giống hệt nhau ở mọi backend.
        CheckConstraint(
            "(created_by IS NULL) OR ("
            "(approved_by IS NULL OR approved_by != created_by) AND "
            "(rejected_by IS NULL OR rejected_by != created_by))",
            name="ck_resolutions_maker_checker_br12",
        ),
        # ADR-024/INV-17 — đối xứng br11 ở trên. `khac` = "lý do khác", không
        # có note thì bản ghi kiểm toán rỗng nghĩa: người đọc lại sau này không
        # biết vì sao case bị từ chối. `length(trim(note)) > 0` chặn cả NULL
        # lẫn chuỗi toàn khoảng trắng — validate-chỉ-ở-route không chặn được
        # UPDATE viết thẳng SQL, đúng bài học ADR-019 lặp lại.
        CheckConstraint(
            "(reject_reason != 'khac') OR (note IS NOT NULL AND length(trim(note)) > 0)",
            name="ck_resolutions_note_bat_buoc_khi_khac",
        ),
    )

    resolution_id: Mapped[str] = mapped_column(String, primary_key=True)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.ticket_id"), nullable=False)
    action_type: Mapped[str] = mapped_column(String, nullable=False)
    amount: Mapped[int | None] = mapped_column(Integer, nullable=True)
    destination_ref: Mapped[str | None] = mapped_column(Text, nullable=True)
    rationale: Mapped[str] = mapped_column(Text, nullable=False)
    cited_tool_result_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    status: Mapped[str] = mapped_column(String, nullable=False, default="draft")
    approved_by: Mapped[str | None] = mapped_column(ForeignKey("users.user_id"), nullable=True)
    approved_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    # ADR-019 — nhãn phán đoán chuyên gia tại luồng từ chối. Nullable ở tầng
    # cột (resolution chưa bị từ chối thì không có gì để ghi); tính bắt buộc
    # được ép theo ĐIỀU KIỆN qua CHECK br11 ở trên, đúng cách BR-10 đã làm.
    # ADR-020 (dự thảo) chuẩn bị sẵn cột maker-checker: ai ĐỀ XUẤT, để sau này
    # ép được `approved_by != created_by`. Nullable VĨNH VIỄN cho dữ liệu cũ —
    # resolution tạo trước cột này không có cách nào biết người đề xuất, và bịa
    # một cái tên vào bản ghi kiểm toán còn tệ hơn để trống.
    created_by: Mapped[str | None] = mapped_column(ForeignKey("users.user_id"), nullable=True)
    reject_reason: Mapped[str | None] = mapped_column(String, nullable=True)
    rejected_by: Mapped[str | None] = mapped_column(ForeignKey("users.user_id"), nullable=True)
    rejected_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    # ADR-024 (TM-03 sign-off security) — ghi chú tự do của SUPERVISOR khi từ
    # chối. KHÁC `InvestigationLog.agent_note` (ghi chú của AGENT lúc điều
    # tra) dù trùng tên biến — đừng đọc nhầm cột này thành cột kia, hai cột
    # khác bảng, khác rủi ro (note ở đây là văn bản NHÂN VIÊN gõ tay, qua
    # scrub PII TẠI ĐIỂM GHI trước khi tới đây — xem route reject).
    note: Mapped[str | None] = mapped_column(Text, nullable=True)
    note_flagged: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=dt.datetime.utcnow)


class Escalation(Base):
    __tablename__ = "escalations"
    __table_args__ = (
        CheckConstraint(
            "target IN ('supervisor','partner_bank','authority')", name="ck_escalations_target"
        ),
    )

    escalation_id: Mapped[str] = mapped_column(String, primary_key=True)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.ticket_id"), nullable=False)
    target: Mapped[str] = mapped_column(String, nullable=False)
    reason: Mapped[str] = mapped_column(Text, nullable=False)  # NOT NULL — mã tín hiệu, không phải kết luận
    created_by: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=dt.datetime.utcnow)
    partner_response_status: Mapped[str | None] = mapped_column(String, nullable=True)
    responded_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)


# ---------------------------------------------------------------------------
# Xác thực & hội thoại
# ---------------------------------------------------------------------------


class AuthSession(Base):
    """`resolution_id IS NULL` = challenge OTP step-up của khách hàng (luồng
    gốc). `resolution_id IS NOT NULL` = challenge OTP riêng cho 1 lần sếp
    duyệt tài chính cụ thể (đợt nâng cấp Auth Flow 2026-08-12, AUTH5-04/05/
    05B) — tái dùng nguyên cơ chế failed_attempts/locked_at đã có thay vì
    tạo bảng mới. `amount_snapshot` chụp lại `Resolution.amount` NGAY LÚC
    xin OTP — PSD2 dynamic linking: nếu CSKH sửa số tiền sau đó, snapshot
    lệch với số tiền hiện tại của resolution, buộc xin OTP mới (AUTH5-05B)."""

    __tablename__ = "auth_sessions"

    session_id: Mapped[str] = mapped_column(String, primary_key=True)
    user_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    otp_code: Mapped[str | None] = mapped_column(String, nullable=True)
    otp_status: Mapped[str | None] = mapped_column(String, nullable=True)
    security_q_passed: Mapped[bool] = mapped_column(Boolean, nullable=False, default=False)
    failed_attempts: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    locked_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    resolution_id: Mapped[str | None] = mapped_column(ForeignKey("resolutions.resolution_id"), nullable=True)
    amount_snapshot: Mapped[int | None] = mapped_column(Integer, nullable=True)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=dt.datetime.utcnow)


class ChatSession(Base):
    """Live chat (2026-08-11) — 1 phiên chat 2 chiều thời gian thực giữa
    khách và CSKH, LUÔN gắn 1 ticket có sẵn (ticket_id NOT NULL) — đúng tinh
    thần "escalation path, không phải kênh song song với AI" đã chốt, và
    đảm bảo luôn có Complaint/InvestigationLog để bàn giao ngữ cảnh AI đã
    điều tra cho CSKH nhận ca. claimed_by NULL = đang chờ, có giá trị = CSKH
    nào đó đã nhận (claim-based routing, không round-robin/ML)."""

    __tablename__ = "chat_sessions"
    __table_args__ = (
        CheckConstraint("status IN ('waiting','active','closed')", name="ck_chat_sessions_status"),
        CheckConstraint("csat_score IS NULL OR csat_score BETWEEN 1 AND 5", name="ck_chat_sessions_csat_score"),
    )

    chat_session_id: Mapped[str] = mapped_column(String, primary_key=True)
    ticket_id: Mapped[str] = mapped_column(ForeignKey("tickets.ticket_id"), nullable=False)
    customer_id: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="waiting")
    claimed_by: Mapped[str | None] = mapped_column(ForeignKey("users.user_id"), nullable=True)
    started_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=dt.datetime.utcnow)
    claimed_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    closed_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)
    csat_score: Mapped[int | None] = mapped_column(Integer, nullable=True)
    csat_submitted_at: Mapped[dt.datetime | None] = mapped_column(DateTime, nullable=True)


class Message(Base):
    """Trước 2026-08-11 bảng này tồn tại nhưng chưa từng dùng (0 dòng dữ
    liệu, session_id FK sai đối tượng auth_sessions = phiên ĐĂNG NHẬP thay
    vì phiên CHAT) — tái dùng lại cho live chat, đổi FK sang ChatSession.
    content dùng EncryptedText (mã hoá at-rest, cùng khoá với
    PolicyChunk.text) — transcript chat có thể chứa SĐT/số tài khoản/số
    tiền, không được lưu plaintext."""

    __tablename__ = "messages"
    __table_args__ = (
        CheckConstraint(
            "role IN ('customer','agent','staff','system')", name="ck_messages_role"
        ),
    )

    message_id: Mapped[str] = mapped_column(String, primary_key=True)
    chat_session_id: Mapped[str] = mapped_column(ForeignKey("chat_sessions.chat_session_id"), nullable=False)
    ticket_id: Mapped[str | None] = mapped_column(ForeignKey("tickets.ticket_id"), nullable=True)
    role: Mapped[str] = mapped_column(String, nullable=False)
    content: Mapped[str] = mapped_column(EncryptedText, nullable=False)
    tool_call_ids: Mapped[list[str]] = mapped_column(JSON, nullable=False, default=list)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=dt.datetime.utcnow)


# ---------------------------------------------------------------------------
# RAG chính sách/FAQ (src/rag/) — đối tác ví (role partner_admin) upload,
# agent + CSKH tra cứu. Nội dung tài liệu (PolicyChunk.text) mã hoá tại chỗ
# (EncryptedText) — vector store (Chroma, data/rag_index/) chỉ giữ embedding +
# chunk_id, KHÔNG giữ text thật (xem src/rag/store.py).
# ---------------------------------------------------------------------------


class PolicyDocument(Base):
    __tablename__ = "policy_documents"
    __table_args__ = (
        CheckConstraint(
            "status IN ('processing','indexed','failed')", name="ck_policy_documents_status"
        ),
    )

    doc_id: Mapped[str] = mapped_column(String, primary_key=True)
    filename: Mapped[str] = mapped_column(String, nullable=False)
    uploaded_by: Mapped[str] = mapped_column(ForeignKey("users.user_id"), nullable=False)
    uploaded_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=dt.datetime.utcnow)
    status: Mapped[str] = mapped_column(String, nullable=False, default="processing")
    chunk_count: Mapped[int] = mapped_column(Integer, nullable=False, default=0)
    error_message: Mapped[str | None] = mapped_column(Text, nullable=True)


class PolicyChunk(Base):
    __tablename__ = "policy_chunks"

    chunk_id: Mapped[str] = mapped_column(String, primary_key=True)
    doc_id: Mapped[str] = mapped_column(ForeignKey("policy_documents.doc_id"), nullable=False)
    chunk_index: Mapped[int] = mapped_column(Integer, nullable=False)
    # Mã hoá trong suốt (Fernet, giống BankAccount.account_no) — "bảo mật RAG
    # cấp cao": file SQLite trên đĩa không chứa nội dung chính sách dạng thô.
    text: Mapped[str] = mapped_column(EncryptedText, nullable=False)
    created_at: Mapped[dt.datetime] = mapped_column(DateTime, nullable=False, default=dt.datetime.utcnow)
