"""Fraud-trigger policy — MVP scope (Data Brief §4.5.3, PRD §5).

The most important boundary (§4.5.1): this is NOT a rulebook for the agent to decide
whether fraud occurred — it is only a ROUTING condition (escalate to supervisor or not).

Scope reduced for a 2-week / 1-person timeline: only `FS-06` (account drained right after
an authentication anomaly) triggers escalation. `fraud_signals.yaml` keeps the original
12-signal specification (dataset inherited from the earlier full design) —
codes other than `FS-06` may still appear in `complaints.fraud_signals`
(surplus data, harmless) but do NOT influence the escalation decision here.
The Tier A/Tier B concept no longer exists.
"""
from __future__ import annotations

from typing import NamedTuple

ESCALATING_SIGNAL = "FS-06"
ESCALATION_PRIORITY = "critical"
ESCALATION_TARGET = "supervisor"


class EscalationDecision(NamedTuple):
    should_escalate: bool
    priority: str  # 'critical' or "normal" (the complaint's default level)
    target: str | None  # 'supervisor' or None


def evaluate_escalation(fraud_signals: list[str]) -> EscalationDecision:
    signals = set(fraud_signals or [])

    if ESCALATING_SIGNAL in signals:
        return EscalationDecision(True, ESCALATION_PRIORITY, ESCALATION_TARGET)

    # Any other signal (if present) does not trigger escalation in the MVP scope —
    # it is still recorded in complaints.fraud_signals so staff see it when opening
    # the ticket, but priority stays at the complaint's default level.
    return EscalationDecision(False, "normal", None)
