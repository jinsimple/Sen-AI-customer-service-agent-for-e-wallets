#!/usr/bin/env python3
"""FIN05-StressTest-Plan-v4 6.1/B-07 — vòng lặp hỏi-lại-làm-rõ có THẬT SỰ
dừng đúng CLARIFY_QUESTION_MAX_ROUNDS hay không. `tests/test_agents/
test_clarify_loop.py` (ST2-B-07, viết trước đó) CHỈ verify WIRING (system
prompt có nhúng đúng số vòng cấu hình) — tự nhận trong docstring là KHÔNG
verify được hành vi LLM thật, cần 1 case eval multi-turn thật. Đây là case đó.

Kịch bản: khách hàng CỐ TÌNH mơ hồ ở MỌI lượt trả lời (không đưa ra
trans_id/rec_code/phạm vi rõ ràng dù được hỏi) — đúng "worst case" mà
CLARIFY_QUESTION_MAX_ROUNDS được thiết kế để chặn. Theo đúng chỉ thị prompt
(src/agents/prompt.py dòng 45): hỏi tối đa {max_rounds} lần tìm trans_id, hết
lượt vẫn không ra → hỏi phạm vi (scope) → khách vẫn không xác định được →
tạo ticket với scope="unknown", trans_id=None (KHÔNG tự đoán, KHÔNG hỏi vô
hạn). Case PASS nếu: agent tạo ticket trong một số lượt HỮU HẠN (không lặp
vô hạn hỏi cùng 1 câu), và không tự đoán bừa 1 giá trị trans_id/scope cụ thể
nào mà khách chưa từng xác nhận.

Gọi agent THẬT (OpenAI thật, tốn phí) — như mọi script khác trong eval/,
KHÔNG chạy tự động trong CI mặc định, chỉ chạy thủ công/nightly.

Dùng:
    python eval/run_clarify_loop_check.py
"""
from __future__ import annotations

import sys
import tempfile
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from eval._harness import build_eval_session
from src.agents.graph import run_agent_turn
from src.config import CLARIFY_QUESTION_MAX_ROUNDS
from src.db.models import Complaint, Ticket

# Cố tình mơ hồ ở MỌI lượt — không đưa mã giao dịch, không đưa SĐT/số tiền,
# không xác nhận phạm vi dù được hỏi thẳng. Đây chính là input mà
# CLARIFY_QUESTION_MAX_ROUNDS phải chặn được, khác simulate_customer_reply()
# của _harness.py (vốn CỐ GẮNG hợp tác, luôn có dữ kiện thật để trả lời).
_VAGUE_REPLIES = [
    "Mình bị mất tiền trong ví, không rõ chi tiết gì cả.",
    "Mình không nhớ mã giao dịch, không nhớ số điện thoại đã dùng, cũng không nhớ số tiền — chịu luôn, không tra được đâu.",
    "Mình cũng không phân biệt được là chuyển nội bộ trong ví hay qua ngân hàng, không rành mấy cái đó.",
    "Mình vẫn không xác định được đâu bạn ơi, mình không rành kỹ thuật lắm.",
    "Không biết luôn, chịu thật sự, mình không có thêm thông tin gì khác đâu.",
    "Vẫn không à, mình đã nói hết những gì mình biết rồi.",
]

MAX_TURNS = 8  # dư nhiều so với 2 (CLARIFY_QUESTION_MAX_ROUNDS) + 1 (hỏi scope) — bắt được cả trường hợp lặp vô hạn thật


def run() -> int:
    with tempfile.TemporaryDirectory(prefix="fin05_eval_clarify_") as tmp:
        db_path = Path(tmp) / "eval.db"
        session = build_eval_session(db_path)

        from sqlalchemy import select

        from src.db.models import User

        user = session.scalars(select(User).where(User.role == "customer")).first()
        assert user is not None, "Không tìm được user customer nào trong dataset seed"

        thread_id = "clarify-loop-eval"
        result: dict = {}
        n_question_turns = 0
        turns_used = 0
        for i in range(MAX_TURNS):
            message = _VAGUE_REPLIES[min(i, len(_VAGUE_REPLIES) - 1)]
            result = run_agent_turn(session, user_id=user.user_id, message=message, thread_id=thread_id)
            turns_used += 1
            reply = result.get("reply", "")
            print(f"[turn {i + 1}] khách: {message!r}", file=sys.stderr)
            print(f"[turn {i + 1}] agent: {reply!r}", file=sys.stderr)
            if result.get("ticket_id"):
                break
            if "?" in reply:
                n_question_turns += 1
            # KHÔNG dừng vòng lặp chỉ vì lượt này không có "?" — khách hàng
            # THẬT vẫn tiếp tục trả lời mơ hồ (không tự im lặng bỏ cuộc) cho
            # tới khi có kết luận rõ ràng; dừng sớm ở đây từng làm sai lệch
            # kết quả (coi agent "bỏ cuộc" trong khi thực ra nó chỉ đang tạm
            # dừng hỏi 1 lượt để chờ khách chủ động quay lại — không phải
            # dấu hiệu vòng lặp đã kết thúc). Vòng lặp chỉ dừng khi có
            # ticket_id hoặc hết MAX_TURNS.

        # KHÔNG rollback() trước khi đọc Ticket/Complaint bên dưới — record đã
        # flush() (chưa commit) vẫn nằm trong identity map của session, chỉ
        # session.get() được TRƯỚC khi rollback (phát hiện thật: rollback()
        # sớm xoá sạch object vừa flush, làm session.get() sau đó trả None dù
        # ticket_id vừa nhận được từ chính result này là thật). Script dùng
        # đúng 1 case, DB tạm bị xoá cả thư mục ngay khi hàm return — không
        # cần rollback để cô lập giữa nhiều case như _harness.py.
        ticket_id = result.get("ticket_id")
        ok = True
        reasons = []

        if ticket_id is None:
            ok = False
            reasons.append(f"Sau {turns_used} lượt (đều mơ hồ), agent VẪN chưa tạo ticket lẫn dừng hỏi — nghi vòng lặp vô hạn.")
        else:
            ticket = session.get(Ticket, ticket_id)
            complaint = session.get(Complaint, ticket.complaint_id) if ticket else None
            if complaint is None:
                ok = False
                reasons.append(f"ticket_id={ticket_id} nhưng không tra ra Complaint tương ứng.")
            else:
                # Chỉ thị prompt: khách không xác định được cả trans_id lẫn
                # scope sau khi hỏi lại -> PHẢI dùng scope="unknown",
                # trans_id=None, KHÔNG tự đoán 1 giá trị cụ thể nào khách
                # chưa hề xác nhận.
                if complaint.trans_id is not None:
                    ok = False
                    reasons.append(
                        f"complaint.trans_id={complaint.trans_id!r} dù khách CHƯA từng cung cấp mã giao dịch nào — có vẻ agent tự đoán/bịa."
                    )
                if complaint.scope not in ("unknown",):
                    ok = False
                    reasons.append(
                        f"complaint.scope={complaint.scope!r} dù khách CHƯA từng xác nhận phạm vi cụ thể — kỳ vọng 'unknown'."
                    )

        # Giới hạn "hữu hạn" nới hơn CLARIFY_QUESTION_MAX_ROUNDS+1 lý thuyết —
        # mục đích chính là bắt LẶP VÔ HẠN thật (MAX_TURNS lượt vẫn hỏi tiếp),
        # không phải ép đúng tuyệt đối con số vòng (hành vi ngôn ngữ tự nhiên
        # có thể lệch 1 vòng mà vẫn hợp lý).
        if turns_used >= MAX_TURNS and ticket_id is None:
            ok = False
            reasons.append(f"Dùng hết {MAX_TURNS} lượt (giới hạn an toàn của chính script eval) mà vẫn chưa kết thúc vòng hỏi lại.")

        status = "PASS" if ok else "FAIL"
        print(f"\n{status} — turns_used={turns_used}, n_question_turns={n_question_turns}, CLARIFY_QUESTION_MAX_ROUNDS={CLARIFY_QUESTION_MAX_ROUNDS}, ticket_id={ticket_id}", file=sys.stderr)
        for r in reasons:
            print(f"    - {r}", file=sys.stderr)
        return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(run())
