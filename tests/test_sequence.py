import pytest
from unittest.mock import MagicMock
from api.engine.sequence import load_sequence, get_next_question

def test_load_sequence_returns_list():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = [
        (1, "REF-1", "Q1", "text", None, None, "1", 1.0, None, {}),
        (2, "REF-2", "Q2", "text", None, None, "1", 1.0, None, {}),
        (3, "REF-3", "Q3", "text", None, None, "1", 1.0, None, {})
    ]
    
    result = load_sequence("SKILLED_WORKER", [], mock_conn)
    assert isinstance(result, list)
    assert len(result) == 3

def test_settlement_flag_adds_question():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    mock_cursor.fetchall.return_value = []
    
    result = load_sequence("SKILLED_WORKER", ["SETTLEMENT_10YR"], mock_conn)
    assert any(q["paragraph_ref"] == "SETTLE-2026" for q in result)

def test_get_next_question_skips_answered():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    # First query for load_sequence
    mock_cursor.fetchall.side_effect = [
        [
            (1, "REF-1", "Q1", "text", None, None, "1", 1.0, None, {}),
            (2, "REF-2", "Q2", "text", None, None, "1", 1.0, None, {}),
            (3, "REF-3", "Q3", "text", None, None, "1", 1.0, None, {})
        ],
        [("REF-1",), ("REF-2",)]  # Second query for answered
    ]
    
    result = get_next_question("session_id", "SKILLED_WORKER", [], mock_conn)
    assert result is not None
    assert result["paragraph_ref"] == "REF-3"
    assert result["question_number"] == 3

def test_complete_when_all_answered():
    mock_conn = MagicMock()
    mock_cursor = MagicMock()
    mock_conn.cursor.return_value = mock_cursor
    
    mock_cursor.fetchall.side_effect = [
        [
            (1, "REF-1", "Q1", "text", None, None, "1", 1.0, None, {}),
            (2, "REF-2", "Q2", "text", None, None, "1", 1.0, None, {})
        ],
        [("REF-1",), ("REF-2",)]
    ]
    
    result = get_next_question("session_id", "SKILLED_WORKER", [], mock_conn)
    assert result is None
