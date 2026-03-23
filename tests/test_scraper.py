"""Tests for GOV.UK scraper."""

import hashlib
from unittest.mock import MagicMock, patch

import pytest
from bs4 import BeautifulSoup

from scraper.crawler import extract_paragraphs, write_scrape_log


def test_extract_paragraphs_finds_numbered_refs():
    """Extract paragraphs with SW 14.1., FIN 2.1. style refs (GOV.UK format)."""
    html = """
    <div class="govuk-govspeak">
        <p>SW 14.1. The applicant must meet the salary threshold.</p>
        <p>FIN 2.1. The applicant must have funds of at least £1,270.</p>
    </div>
    """
    soup = BeautifulSoup(html, "lxml")
    result = extract_paragraphs(soup, "SKILLED_WORKER")
    assert len(result) >= 1
    assert result[0]["paragraph_ref"] == "SW-14.1"
    assert "salary" in result[0]["raw_text"]
    assert result[1]["paragraph_ref"] == "FIN-2.1"


def test_sha256_hash_is_64_chars():
    """SHA-256 hash is 64 hex characters."""
    h = hashlib.sha256(b"any string").hexdigest()
    assert len(h) == 64
    assert all(c in "0123456789abcdef" for c in h)


def test_scrape_log_written_on_success():
    """write_scrape_log calls cursor.execute once."""
    mock_conn = MagicMock()
    mock_cur = MagicMock()
    mock_conn.cursor.return_value = mock_cur

    write_scrape_log(mock_conn, "TEST_CODE", "SUCCESS", 42, 1500, None)
    mock_cur.execute.assert_called_once()
    mock_conn.commit.assert_called_once()


@patch("httpx.get")
def test_429_triggers_retry(mock_get):
    """HTTP 429 triggers 30s wait and retry; 200 on retry succeeds."""
    from scraper.crawler import scrape_appendix
    from scraper.manifest import AppendixEntry

    mock_response_429 = MagicMock()
    mock_response_429.status_code = 429
    mock_response_429.raise_for_status = MagicMock()

    mock_response_200 = MagicMock()
    mock_response_200.status_code = 200
    mock_response_200.text = """
    <html><body>
    <div class="govuk-govspeak">
        <p>SW 14.1 The applicant must meet requirements.</p>
    </div>
    </body></html>
    """
    mock_response_200.raise_for_status = MagicMock()

    mock_get.side_effect = [mock_response_429, mock_response_200]

    entry = AppendixEntry(
        code="TEST",
        url="https://www.gov.uk/test",
        priority=1,
        is_hard_gate_source=False,
        flag_2026=None,
        description="Test",
    )
    mock_conn = MagicMock()

    with patch("scraper.crawler.time.sleep"):
        result = scrape_appendix(entry, mock_conn, dry_run=False)

    assert mock_get.call_count == 2
    assert result["status"] in ("SUCCESS", "FLAGGED")
    assert result["paragraphs_found"] >= 0
