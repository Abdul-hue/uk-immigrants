import pytest
from api.engine.rule_engine import evaluate_answer

def test_salary_gte_pass():
    constraint = {
      "paragraph_ref": "SW-14.1",
      "field": "salary_annual_gbp",
      "operator": "gte",
      "value": 26200,
      "answer_type": "currency",
      "fail_condition_description": "Salary below minimum"
    }
    result = evaluate_answer(constraint, "30000")
    assert result["result"] == "PASS"

def test_salary_gte_fail():
    constraint = {
      "paragraph_ref": "SW-14.1",
      "field": "salary_annual_gbp",
      "operator": "gte",
      "value": 26200,
      "answer_type": "currency",
      "fail_condition_description": "Salary below minimum"
    }
    result = evaluate_answer(constraint, "25000")
    assert result["result"] == "FAIL"
    assert result["fail_reason"] == "Salary below minimum"
    assert result["rule_cited"] == "SW-14.1"

def test_boolean_true_passes_exists():
    constraint = {
      "paragraph_ref": "SW-1.1",
      "field": "has_cos",
      "operator": "exists",
      "value": None,
      "answer_type": "boolean",
      "fail_condition_description": "No CoS provided"
    }
    result = evaluate_answer(constraint, "yes")
    assert result["result"] == "PASS"

def test_boolean_false_fails_exists():
    constraint = {
      "paragraph_ref": "SW-1.1",
      "field": "has_cos",
      "operator": "exists",
      "value": None,
      "answer_type": "boolean",
      "fail_condition_description": "No CoS provided"
    }
    result = evaluate_answer(constraint, "no")
    assert result["result"] == "FAIL"

def test_any_operator_always_passes():
    constraint = {
      "paragraph_ref": "FIN-8.4",
      "operator": "any",
      "value": None,
      "answer_type": "text",
      "fail_condition_description": None
    }
    result = evaluate_answer(constraint, "anything")
    assert result["result"] == "PASS"

def test_between_operator():
    constraint = {
      "paragraph_ref": "TEST-1.1",
      "operator": "between",
      "value": 18,
      "value_max": 65,
      "answer_type": "integer",
      "fail_condition_description": "Age out of range"
    }
    assert evaluate_answer(constraint, "25")["result"] == "PASS"
    assert evaluate_answer(constraint, "17")["result"] == "FAIL"
    assert evaluate_answer(constraint, "66")["result"] == "FAIL"
