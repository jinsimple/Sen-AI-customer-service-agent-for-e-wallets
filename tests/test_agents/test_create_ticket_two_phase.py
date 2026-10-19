"""ADR-051 — `create_ticket` in TWO STEPS (`xac_nhan`), tested at the tool level.

Step 1 (`xac_nhan=False`) must create NOTHING and return a summary built in code. Step 2
(`xac_nhan=True`) must be refused unless the summary for EXACTLY the same fields was produced earlier
in the SAME thread, and the permission is single-use.

Deterministic, no LLM: the real LangChain tool is invoked with the arguments the agent would pass.
These tests prove the CODE enforces the protocol. They do not prove a live model follows the prompt
(that needs the golden set).
"""
from __future__ import annotations

import datetime as dt
import uuid

from src.agents.tools.customer_tools import build_customer_tools
from src.db.models import Ticket

_NOW = dt.datetime.utcnow().timestamp()
_ARGS = {
    "complaint_type": "money_not_received",
    "scope": "internal_wallet",
    "description_raw": "Tôi chuyển 270k cho bạn mà bạn chưa nhận được.",
    "trans_id": "TXN-0001",
}


def _tool(sample_db, *, user_id="USR-A", thread_id=None, otp_verified_at=_NOW):
    tools = build_customer_tools(
        sample_db,
        user_id=user_id,
        otp_verified_at=otp_verified_at,
        thread_id=thread_id or f"T-{uuid.uuid4().hex}",
    )
    return {t.name: t for t in tools}["create_ticket"]


def _tickets(sample_db) -> int:
    return sample_db.query(Ticket).count()


def test_step1_creates_nothing_and_carries_no_ticket_id(sample_db):
    before = _tickets(sample_db)
    out = _tool(sample_db).invoke(dict(_ARGS))

    assert out["status"] == "summary"
    assert out["da_tao_ticket"] is False
    assert "ticket_id" not in out, "constraint ②: the ticket-claim guards key on this field"
    assert _tickets(sample_db) == before


def test_step1_summary_is_built_from_the_database_not_from_the_model(sample_db):
    args = dict(_ARGS, description_raw="mô tả của khách")
    out = _tool(sample_db).invoke(args)

    # amount and time come from the customer's own transaction row, never from model arguments
    assert "270.000đ" in out["tom_tat"]
    assert "TXN-0001" in out["tom_tat"]
    assert "mô tả của khách" in out["tom_tat"]
    assert "Tiền chưa về" in out["tom_tat"]


def test_step2_without_a_summary_is_refused(sample_db):
    before = _tickets(sample_db)
    out = _tool(sample_db).invoke(dict(_ARGS, xac_nhan=True))

    assert out["status"] == "error"
    assert out["loai"] == "chua_gui_tom_tat"
    assert _tickets(sample_db) == before


def test_summary_then_confirmation_creates_exactly_one_ticket(sample_db):
    tool = _tool(sample_db)
    before = _tickets(sample_db)

    assert tool.invoke(dict(_ARGS))["status"] == "summary"
    created = tool.invoke(dict(_ARGS, xac_nhan=True))

    assert "ticket_id" in created, created
    assert _tickets(sample_db) == before + 1


def test_changing_a_field_between_steps_is_refused(sample_db):
    tool = _tool(sample_db)
    tool.invoke(dict(_ARGS))
    before = _tickets(sample_db)

    out = tool.invoke(dict(_ARGS, xac_nhan=True, description_raw="một mô tả khác hẳn"))

    assert out["loai"] == "chua_gui_tom_tat"
    assert _tickets(sample_db) == before


def test_otp_disclosed_flag_is_covered_by_the_digest(sample_db):
    # `otp_disclosed` is not shown in the summary but raises priority: flipping it must invalidate step 2.
    tool = _tool(sample_db)
    tool.invoke(dict(_ARGS, otp_disclosed=False))
    out = tool.invoke(dict(_ARGS, xac_nhan=True, otp_disclosed=True))

    assert out["loai"] == "chua_gui_tom_tat"


def test_permission_is_single_use(sample_db):
    tool = _tool(sample_db)
    tool.invoke(dict(_ARGS))
    assert "ticket_id" in tool.invoke(dict(_ARGS, xac_nhan=True))
    after_first = _tickets(sample_db)

    again = tool.invoke(dict(_ARGS, xac_nhan=True))

    assert again["loai"] == "chua_gui_tom_tat", "the 'customer agrees twice' branch must be closed"
    assert _tickets(sample_db) == after_first


def test_summary_of_one_thread_cannot_authorise_another_thread(sample_db):
    _tool(sample_db, thread_id="THREAD-ONE").invoke(dict(_ARGS))
    before = _tickets(sample_db)

    out = _tool(sample_db, thread_id="THREAD-TWO").invoke(dict(_ARGS, xac_nhan=True))

    assert out["loai"] == "chua_gui_tom_tat"
    assert _tickets(sample_db) == before


def test_otp_gate_applies_to_step_one_as_well(sample_db):
    never = _tool(sample_db, otp_verified_at=None).invoke(dict(_ARGS))
    stale = _tool(sample_db, otp_verified_at=_NOW - 3600).invoke(dict(_ARGS))

    assert never["status"] == "error" and "tom_tat" not in never
    assert stale["status"] == "error" and stale.get("loai") == "otp_het_tuoi" and "tom_tat" not in stale


def test_invalid_input_never_gets_a_summary_nor_a_permission(sample_db):
    tool = _tool(sample_db)
    bad = tool.invoke(dict(_ARGS, complaint_type="not_a_type"))
    assert bad["status"] == "error" and "tom_tat" not in bad

    # the failed step 1 must not have stored a permission for the (invalid) fields
    out = tool.invoke(dict(_ARGS, complaint_type="not_a_type", xac_nhan=True))
    assert out["status"] == "error"


def test_someone_elses_transaction_cannot_be_summarised(sample_db):
    # USR-CSKH is not a party to TXN-0001, so step 1 must refuse instead of echoing its amount.
    out = _tool(sample_db, user_id="USR-CSKH").invoke(dict(_ARGS))

    assert out["status"] == "error"
    assert "tom_tat" not in out and "270.000" not in str(out)


def test_not_found_case_summary_says_undetermined_without_inventing_a_transaction(sample_db):
    args = dict(_ARGS, trans_id=None, scope="unknown")
    out = _tool(sample_db).invoke(args)

    assert out["status"] == "summary"
    assert out["tom_tat"].count("chưa xác định") >= 3  # scope, transaction id, amount, time


def test_screening_gate_for_wrong_transfer_still_applies_at_step_two(sample_db):
    tool = _tool(sample_db)
    args = dict(_ARGS, complaint_type="wrong_recipient")
    tool.invoke(args)  # step 1 passes: the screening question is a step-2 concern (constraint ④)
    before = _tickets(sample_db)

    out = tool.invoke(dict(args, xac_nhan=True))

    assert out["loai"] == "sang_loc_lua_dao_chua_hoan_tat"
    assert _tickets(sample_db) == before
