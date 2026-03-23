"""Tests for Intent Classifier."""

from unittest.mock import MagicMock, patch

import pytest

from classifier.intent_classifier import classify_intent


@patch("classifier.intent_classifier.OpenAI")
def test_job_offer_classifies_skilled_worker(mock_openai):
    """Job offer input classifies as SKILLED_WORKER with 2026 flags."""
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content='{"matched_route":"SKILLED_WORKER","confidence":0.95,'
                    '"reasoning":"Has job offer","clarifying_question":null}'
                )
            )
        ]
    )

    result = classify_intent("I have a job offer from a hospital in Manchester", "PK")

    assert result["route"] == "SKILLED_WORKER"
    assert result["needs_clarification"] is False
    assert "B2_ENGLISH_UPDATE" in result["flags_2026"]
    assert "SETTLEMENT_10YR" in result["flags_2026"]


@patch("classifier.intent_classifier.OpenAI")
def test_visitor_classifies_correctly(mock_openai):
    """Visitor intent classifies correctly, no 2026 flags."""
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content='{"matched_route":"VISITOR","confidence":0.97,'
                    '"reasoning":"Short visit","clarifying_question":null}'
                )
            )
        ]
    )

    result = classify_intent("I want to visit London for tourism", "PK")

    assert result["route"] == "VISITOR"
    assert result["flags_2026"] == []


@patch("classifier.intent_classifier.OpenAI")
def test_us_national_gets_eta_flag(mock_openai):
    """US nationality gets ETA_MANDATORY flag even for VISITOR route."""
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content='{"matched_route":"VISITOR","confidence":0.97,'
                    '"reasoning":"Short visit","clarifying_question":null}'
                )
            )
        ]
    )

    result = classify_intent("visit London", "US")

    assert result["eta_required"] is True
    assert "ETA_MANDATORY" in result["flags_2026"]


@patch("classifier.intent_classifier.OpenAI")
def test_low_confidence_returns_clarifying_question(mock_openai):
    """Low confidence returns clarifying_question and needs_clarification."""
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content='{"matched_route":"UNKNOWN","confidence":0.55,'
                    '"reasoning":"Ambiguous","clarifying_question":"Do you have a job offer?"}'
                )
            )
        ]
    )

    result = classify_intent("I want to come to UK")

    assert result["needs_clarification"] is True
    assert result["clarifying_question"] == "Do you have a job offer?"


@patch("classifier.intent_classifier.OpenAI")
def test_family_route_has_no_2026_flags(mock_openai):
    """APPENDIX_FM route has no 2026 flags, eta_required=False when no nationality."""
    mock_client = MagicMock()
    mock_openai.return_value = mock_client
    mock_client.chat.completions.create.return_value = MagicMock(
        choices=[
            MagicMock(
                message=MagicMock(
                    content='{"matched_route":"APPENDIX_FM","confidence":0.91,'
                    '"reasoning":"Family route","clarifying_question":null}'
                )
            )
        ]
    )

    result = classify_intent("I want to be with my British wife", None)

    assert result["route"] == "APPENDIX_FM"
    assert result["flags_2026"] == []
    assert result["eta_required"] is False
