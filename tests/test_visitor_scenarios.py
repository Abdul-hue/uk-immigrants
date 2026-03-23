"""
Comprehensive Visitor Scenarios Test Case.
Covers Standard Tourist, Business Visitor, and Hard Gate Flags.
"""

from unittest.mock import MagicMock, patch
import pytest
from classifier.intent_classifier import classify_intent
from hard_gate.engine import evaluate_hard_gates

@pytest.fixture
def mock_visitor_classification():
    with patch("classifier.intent_classifier.OpenAI") as mock_openai:
        mock_client = MagicMock()
        mock_openai.return_value = mock_client
        yield mock_client

def test_scenario_1_standard_tourist_pakistan(mock_visitor_classification):
    """
    Scenario: Pakistani national visiting for tourism.
    Expectation: VISITOR route, No ETA, PASS hard gate.
    """
    mock_visitor_classification.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content='{"matched_route":"VISITOR","confidence":0.98,"reasoning":"Tourist visit","clarifying_question":null}'
                )
            )
        ]
    )

    # 1. Classification
    classification = classify_intent("I want to visit London for a 2-week holiday", "PK")
    assert classification["route"] == "VISITOR"
    assert classification["eta_required"] is False

    # 2. Hard Gate Evaluation
    user_answers = {
        "nationality_iso": "PK",
        "has_deportation_order": False,
        "has_used_deception": False,
        "has_criminal_conviction": False,
        "has_immigration_debt": False,
        "has_overstayed_90_days": False,
    }
    gate_result = evaluate_hard_gates(user_answers)
    
    assert gate_result["result"] == "PASS"
    assert gate_result["session_can_continue"] is True
    assert len(gate_result["flagged_gates"]) == 0

def test_scenario_2_business_visitor_usa(mock_visitor_classification):
    """
    Scenario: US national visiting for a business conference.
    Expectation: VISITOR route, ETA Required, FLAGGED hard gate (ETA).
    """
    mock_visitor_classification.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content='{"matched_route":"VISITOR","confidence":0.95,"reasoning":"Business meeting","clarifying_question":null}'
                )
            )
        ]
    )

    # 1. Classification
    classification = classify_intent("Attending a tech conference in Manchester", "US")
    assert classification["route"] == "VISITOR"
    assert classification["eta_required"] is True

    # 2. Hard Gate Evaluation
    user_answers = {
        "nationality_iso": "US",
        "has_deportation_order": False,
        "has_used_deception": False,
        "has_criminal_conviction": False,
        "has_immigration_debt": False,
        "has_overstayed_90_days": False,
    }
    gate_result = evaluate_hard_gates(user_answers)
    
    assert gate_result["result"] == "FLAGGED"
    assert gate_result["session_can_continue"] is True
    assert any(g["gate_name"] == "ETA_PRE_GATE" for g in gate_result["flagged_gates"])

def test_scenario_3_visitor_with_criminality_flag(mock_visitor_classification):
    """
    Scenario: Canadian national visiting family but has a criminal conviction.
    Expectation: VISITOR route, ETA Required, FLAGGED hard gate (ETA + Criminality).
    """
    mock_visitor_classification.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content='{"matched_route":"VISITOR","confidence":0.97,"reasoning":"Family visit","clarifying_question":null}'
                )
            )
        ]
    )

    # 1. Classification
    classification = classify_intent("Visiting my sister in Edinburgh", "CA")
    assert classification["route"] == "VISITOR"
    assert classification["eta_required"] is True

    # 2. Hard Gate Evaluation (User discloses conviction)
    user_answers = {
        "nationality_iso": "CA",
        "has_deportation_order": False,
        "has_used_deception": False,
        "has_criminal_conviction": True, # <--- DISCLOSED
        "has_immigration_debt": False,
        "has_overstayed_90_days": False,
    }
    gate_result = evaluate_hard_gates(user_answers)
    
    assert gate_result["result"] == "FLAGGED"
    assert gate_result["session_can_continue"] is True
    # Should have 2 flags: ETA and Criminality
    gate_names = [g["gate_name"] for g in gate_result["flagged_gates"]]
    assert "ETA_PRE_GATE" in gate_names
    assert "CRIMINALITY" in gate_names

def test_scenario_4_visitor_with_deportation_fail(mock_visitor_classification):
    """
    Scenario: Indian national visiting London but has a deportation order.
    Expectation: VISITOR route, HARD_FAIL.
    """
    mock_visitor_classification.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content='{"matched_route":"VISITOR","confidence":0.99,"reasoning":"Tourist visit","clarifying_question":null}'
                )
            )
        ]
    )

    # 1. Classification
    classification = classify_intent("Tourist visit to London", "IN")
    assert classification["route"] == "VISITOR"

    # 2. Hard Gate Evaluation (User discloses deportation order)
    user_answers = {
        "nationality_iso": "IN",
        "has_deportation_order": True, # <--- DISCLOSED
        "has_used_deception": False,
        "has_criminal_conviction": False,
        "has_immigration_debt": False,
        "has_overstayed_90_days": False,
    }
    gate_result = evaluate_hard_gates(user_answers)
    
    assert gate_result["result"] == "HARD_FAIL"
    assert gate_result["session_can_continue"] is False
    assert gate_result["gate_name"] == "DEPORTATION_ORDER"

def test_scenario_5_visitor_with_overstaying_flag(mock_visitor_classification):
    """
    Scenario: Australian national visiting for tourism but has overstayed 90+ days before.
    Expectation: VISITOR route, ETA Required, FLAGGED hard gate (ETA + Overstay).
    """
    mock_visitor_classification.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content='{"matched_route":"VISITOR","confidence":0.99,"reasoning":"Tourist visit","clarifying_question":null}'
                )
            )
        ]
    )

    # 1. Classification
    classification = classify_intent("Visiting London for 1 month", "AU")
    assert classification["route"] == "VISITOR"
    assert classification["eta_required"] is True

    # 2. Hard Gate Evaluation (User discloses overstaying)
    user_answers = {
        "nationality_iso": "AU",
        "has_deportation_order": False,
        "has_used_deception": False,
        "has_criminal_conviction": False,
        "has_immigration_debt": False,
        "has_overstayed_90_days": True, # <--- DISCLOSED
    }
    gate_result = evaluate_hard_gates(user_answers)
    
    assert gate_result["result"] == "FLAGGED"
    assert gate_result["session_can_continue"] is True
    # Should have 2 flags: ETA and Overstay
    gate_names = [g["gate_name"] for g in gate_result["flagged_gates"]]
    assert "ETA_PRE_GATE" in gate_names
    assert "OVERSTAY" in gate_names
