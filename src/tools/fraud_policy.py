"""Chính sách kích hoạt gian lận — phạm vi MVP (Data Brief §4.5.3, PRD §5).

Ranh giới quan trọng nhất (§4.5.1): đây KHÔNG phải bộ luật để agent phán
quyết có gian lận hay không — nó chỉ là điều kiện ĐỊNH TUYẾN (có escalate
lên supervisor hay không).

Phạm vi rút gọn cho timeline 2 tuần/1 người: chỉ `FS-06` (rút sạch sau bất
thường xác thực) kích hoạt escalate. `fraud_signals.yaml` vẫn giữ nguyên
đặc tả gốc 12 tín hiệu (dataset kế thừa từ bản thiết kế đầy đủ trước đó) —
các mã khác ngoài `FS-06` có thể vẫn xuất hiện trong `complaints.fraud_signals`
(dữ liệu thừa, không sao) nhưng KHÔNG ảnh hưởng quyết định escalate ở đây.
Không còn khái niệm Tầng A/Tầng B.
"""
from __future__ import annotations

from typing import NamedTuple

ESCALATING_SIGNAL = "FS-06"
ESCALATION_PRIORITY = "critical"
ESCALATION_TARGET = "supervisor"


class EscalationDecision(NamedTuple):
    should_escalate: bool
    priority: str  # 'critical' hoặc "normal" (mức mặc định của complaint)
    target: str | None  # 'supervisor' hoặc None


def evaluate_escalation(fraud_signals: list[str]) -> EscalationDecision:
    signals = set(fraud_signals or [])

    if ESCALATING_SIGNAL in signals:
        return EscalationDecision(True, ESCALATION_PRIORITY, ESCALATION_TARGET)

    # Mọi tín hiệu khác (nếu có mặt) không kích hoạt escalate ở phạm vi MVP —
    # vẫn được ghi lại trong complaints.fraud_signals để nhân viên thấy khi
    # mở ticket, nhưng priority giữ mức mặc định của complaint.
    return EscalationDecision(False, "normal", None)
