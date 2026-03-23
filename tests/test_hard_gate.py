"""Tests for Hard Gate Engine."""

import pytest

from hard_gate.engine import evaluate_hard_gates


def _default_answers():
    return {
        "nationality_iso": "GB",
        "has_deportation_order": False,
        "has_used_deception": False,
        "has_criminal_conviction": False,
        "has_immigration_debt": False,
        "has_overstayed_90_days": False,
    }


def test_deportation_order_is_hard_fail():
    """Deportation order should HARD_FAIL, stop session."""
    answers = _default_answers()
    answers["has_deportation_order"] = True

    result = evaluate_hard_gates(answers, db_conn=None)

    assert result["result"] == "HARD_FAIL"
    assert result["session_can_continue"] is False
    assert result["gate_name"] == "DEPORTATION_ORDER"


def test_deception_is_hard_fail():
    """Deception should HARD_FAIL."""
    answers = _default_answers()
    answers["has_used_deception"] = True

    result = evaluate_hard_gates(answers, db_conn=None)

    assert result["result"] == "HARD_FAIL"
    assert result["gate_name"] == "DECEPTION"


def test_us_nationality_flags_eta_but_continues():
    """US nationality should FLAG for ETA but session continues."""
    answers = _default_answers()
    answers["nationality_iso"] = "US"
    answers["has_deportation_order"] = False
    answers["has_used_deception"] = False
    answers["has_criminal_conviction"] = False
    answers["has_immigration_debt"] = False
    answers["has_overstayed_90_days"] = False

    result = evaluate_hard_gates(answers, db_conn=None)

    assert result["result"] == "FLAGGED"
    assert result["session_can_continue"] is True
    assert any(g["gate_name"] == "ETA_PRE_GATE" for g in result["flagged_gates"])


def test_pakistani_clean_record_passes():
    """Pakistani nationality with clean record should PASS."""
    answers = _default_answers()
    answers["nationality_iso"] = "PK"
    answers["has_deportation_order"] = False
    answers["has_used_deception"] = False
    answers["has_criminal_conviction"] = False
    answers["has_immigration_debt"] = False
    answers["has_overstayed_90_days"] = False

    result = evaluate_hard_gates(answers, db_conn=None)

    assert result["result"] == "PASS"
    assert result["session_can_continue"] is True
    assert len(result["flagged_gates"]) == 0


def test_hard_fail_stops_evaluation_before_flags():
    """HARD_FAIL stops evaluation — US ETA and criminality flag never reached."""
    answers = {
        "nationality_iso": "US",
        "has_deportation_order": True,
        "has_used_deception": False,
        "has_criminal_conviction": True,
        "has_immigration_debt": False,
        "has_overstayed_90_days": False,
    }

    result = evaluate_hard_gates(answers, db_conn=None)

    assert result["result"] == "HARD_FAIL"
    assert result["gate_name"] == "DEPORTATION_ORDER"
    assert len(result["flagged_gates"]) == 0
