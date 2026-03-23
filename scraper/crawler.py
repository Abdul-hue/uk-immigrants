"""GOV.UK crawler — fetches appendix pages, extracts paragraphs, stores in PostgreSQL."""

import hashlib
import re
import time
from datetime import date, datetime
from typing import Optional

import httpx
from bs4 import BeautifulSoup

from db.connection import get_connection
from scraper.manifest import (
    AppendixEntry,
    get_manifest_by_priority,
    get_phase1_critical,
)

USER_AGENT = "UKImmigrationResearch/1.0 (contact@platform.com)"
CRAWL_DELAY_SECONDS = 2.5
CHANGE_CUTOFF_DATE = datetime(2026, 2, 1).date()
HTTP_TIMEOUT = 30


def resolve_print_url(url: str) -> str:
    """
    GOV.UK guide pages have a /print variant that renders all
    sections on a single page. Use this to get full content.

    Examples:
    .../immigration-rules-appendix-skilled-worker
    -> .../immigration-rules-appendix-skilled-worker/print

    If /print returns 404, fall back to the original URL.
    """
    base = url.rstrip("/")
    if base.endswith("/print"):
        return base
    return base + "/print"


def fetch_page_with_fallback(url: str, headers: dict) -> tuple:
    """
    Try /print URL first for full content.
    Falls back to original URL if /print returns 404.
    Returns (response, url_used)
    """
    print_url = resolve_print_url(url)
    try:
        response = httpx.get(print_url, headers=headers, timeout=HTTP_TIMEOUT)
        if response.status_code == 200:
            return response, print_url
    except Exception:
        pass
    response = httpx.get(url, headers=headers, timeout=HTTP_TIMEOUT)
    return response, url


def extract_paragraphs(soup: BeautifulSoup, appendix_code: str) -> list[dict]:
    """Extract numbered paragraphs from GOV.UK immigration rules HTML."""
    # GOV.UK has multiple gem-c-govspeak divs per page.
    # The first is always a short intro — the rules are in a later div.
    # Pick the div with the most text content.
    all_govspeak = soup.find_all("div", class_="gem-c-govspeak")
    if all_govspeak:
        content = max(all_govspeak, key=lambda d: len(d.get_text()))
    else:
        content = (
            soup.find("div", {"class": lambda c: c and "govspeak" in (c if isinstance(c, str) else " ".join(c or []))})
            or soup.find("main", id="content")
            or soup.find("main")
            or soup.find("article")
        )
    if not content:
        return []

    paragraphs = []
    current_heading = ""
    seen_refs = set()

    # CORRECT REGEX for GOV.UK immigration rules format:
    # Matches: "SW 1.1." "FIN 2.1." "SW A1.1." "S-EC 1.1."
    # Pattern: 2-5 uppercase letters, space or hyphen,
    #          optional letter(s), digits, dot, digits, optional letter, dot
    PARA_REGEX = re.compile(
        r"^([A-Z]{1,5}(?:\s|-)[A-Z]?[A-Z]?\d{1,3}\.\d{1,3}[a-z]?)\."
    )

    all_elements = content.find_all(["h1", "h2", "h3", "h4", "h5", "p", "li"])

    for element in all_elements:
        tag = element.name
        text = element.get_text(separator=" ", strip=True)

        if not text:
            continue

        if tag in ["h1", "h2", "h3", "h4", "h5"]:
            current_heading = text[:150]
            continue

        if len(text) < 10:
            continue

        match = PARA_REGEX.match(text)

        if match:
            ref_raw = match.group(1).strip()
            normalised = re.sub(r"\s+", "-", ref_raw).upper()

            if normalised in seen_refs:
                continue
            seen_refs.add(normalised)

            rule_text = text[match.end() :].strip()
            if not rule_text:
                rule_text = text

            paragraphs.append({
                "appendix_code": appendix_code,
                "paragraph_ref": normalised,
                "raw_text": rule_text,
                "heading_context": current_heading,
                "is_hard_gate": False,
                "verified": False,
            })

    return paragraphs


def debug_print_page(url: str) -> None:
    """
    Fetch the page and show paragraph refs found using the same regex as
    extract_paragraphs. Use for verifying regex before full scrape.
    """
    headers = {"User-Agent": USER_AGENT}
    print(f"Fetching: {url}")
    resp = httpx.get(url, headers=headers, timeout=HTTP_TIMEOUT)
    print(f"Status: {resp.status_code}")
    print(f"Content length: {len(resp.text)} chars")

    soup = BeautifulSoup(resp.text, "lxml")
    all_govspeak = soup.find_all("div", class_="gem-c-govspeak")
    if all_govspeak:
        content = max(all_govspeak, key=lambda d: len(d.get_text()))
    else:
        content = soup.find("main")

    if not content:
        print("NO CONTENT BLOCK FOUND")
        return

    PARA_REGEX = re.compile(
        r"^([A-Z]{1,5}(?:\s|-)[A-Z]?[A-Z]?\d{1,3}\.\d{1,3}[a-z]?)\."
    )

    refs_found = []
    for el in content.find_all(["p", "li"]):
        text = el.get_text(separator=" ", strip=True)
        match = PARA_REGEX.match(text)
        if match:
            refs_found.append(match.group(1))

    print(f"\nParagraph refs found: {len(refs_found)}")
    if refs_found:
        print(f"First 15 refs: {refs_found[:15]}")
    else:
        all_text = content.get_text()
        print("NO REFS MATCHED — first 25 non-empty lines:")
        lines = [l.strip() for l in all_text.split("\n") if l.strip()]
        for i, line in enumerate(lines[:25]):
            print(f"  {i:02d}: {line[:120]}")


def debug_page_structure(url: str) -> None:
    """
    Fetch a GOV.UK page and print the CSS classes of the top-level
    divs so we can identify the correct content selector.
    Only used for debugging — not called in production.
    """
    headers = {"User-Agent": USER_AGENT}
    response = httpx.get(url, headers=headers, timeout=30)
    soup = BeautifulSoup(response.text, "lxml")

    print(f"\n=== TOP LEVEL DIVS for {url} ===")
    for div in soup.find_all("div", limit=20):
        classes = div.get("class", [])
        id_ = div.get("id", "")
        if classes or id_:
            print(f"  <div class='{' '.join(classes) if classes else ''}' id='{id_}'>")

    print(f"\n=== FIRST 500 CHARS OF CONTENT ===")
    main = soup.find("div", class_="gem-c-govspeak") or soup.find("main")
    if main:
        print(main.get_text()[:500])
    else:
        print("NO MAIN CONTENT FOUND")


def detect_change(code: str, new_hash: str, db_conn) -> bool:
    """Detect if page content has changed. Returns True if changed."""
    cur = db_conn.cursor()
    cur.execute("SELECT page_hash FROM appendices WHERE code = %s", (code,))
    row = cur.fetchone()
    cur.close()

    if not row or not row[0]:
        return False

    old_hash = row[0]
    if new_hash == old_hash:
        return False

    cur = db_conn.cursor()
    cur.execute(
        """
        INSERT INTO rule_versions
            (paragraph_ref, old_text, new_text, old_hash, new_hash)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (code, old_hash, new_hash, old_hash, new_hash),
    )
    cur.execute(
        "UPDATE appendices SET requires_reverification = TRUE WHERE code = %s",
        (code,),
    )
    db_conn.commit()
    cur.close()
    return True


def upsert_appendix(
    db_conn,
    entry: AppendixEntry,
    last_updated,
    page_hash: str,
    requires_reverification: bool,
) -> None:
    """Update appendices table with scrape results."""
    cur = db_conn.cursor()
    cur.execute(
        """
        UPDATE appendices SET
            last_scraped_at = NOW(),
            last_updated_on = %s,
            page_hash = %s,
            requires_reverification = %s
        WHERE code = %s
        """,
        (last_updated, page_hash, requires_reverification, entry.code),
    )
    db_conn.commit()
    cur.close()


def insert_paragraphs(db_conn, paragraphs: list[dict]) -> None:
    """Insert paragraphs into rule_paragraphs. Uses ON CONFLICT to upsert."""
    _ensure_paragraph_ref_unique(db_conn)

    cur = db_conn.cursor()
    for p in paragraphs:
        cur.execute(
            """
            INSERT INTO rule_paragraphs
                (appendix_code, paragraph_ref, raw_text, is_hard_gate, verified)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (paragraph_ref) DO UPDATE SET
                raw_text = EXCLUDED.raw_text
            """,
            (
                p["appendix_code"],
                p["paragraph_ref"],
                p["raw_text"],
                p["is_hard_gate"],
                p["verified"],
            ),
        )
    db_conn.commit()
    cur.close()


def _ensure_paragraph_ref_unique(db_conn) -> None:
    """Add UNIQUE constraint on paragraph_ref if not already present."""
    cur = db_conn.cursor()
    try:
        cur.execute(
            """
            DO $$
            BEGIN
                IF NOT EXISTS (
                    SELECT 1 FROM pg_constraint
                    WHERE conname = 'uq_paragraph_ref'
                ) THEN
                    ALTER TABLE rule_paragraphs
                    ADD CONSTRAINT uq_paragraph_ref UNIQUE (paragraph_ref);
                END IF;
            END $$;
            """
        )
        db_conn.commit()
    except Exception:
        db_conn.rollback()
    finally:
        cur.close()


def write_scrape_log(
    db_conn,
    code: str,
    status: str,
    paragraphs_found: int,
    duration_ms: int,
    error_message: Optional[str] = None,
) -> None:
    """Insert scrape log entry."""
    cur = db_conn.cursor()
    cur.execute(
        """
        INSERT INTO scrape_log
            (appendix_code, status, paragraphs_found, duration_ms, error_message)
        VALUES (%s, %s, %s, %s, %s)
        """,
        (code, status, paragraphs_found, duration_ms, error_message),
    )
    db_conn.commit()
    cur.close()


def scrape_appendix(entry: AppendixEntry, db_conn, dry_run: bool = False) -> dict:
    """Scrape a single appendix page and store results."""
    start = time.perf_counter()
    last_updated = None
    requires_reverification = False

    headers = {"User-Agent": USER_AGENT}
    url_used = entry.url

    try:
        response, url_used = fetch_page_with_fallback(entry.url, headers)

        if response.status_code == 404:
            duration_ms = int((time.perf_counter() - start) * 1000)
            if not dry_run:
                write_scrape_log(db_conn, entry.code, "FAILED", 0, duration_ms, f"HTTP 404 — {url_used}")
            return {
                "code": entry.code,
                "paragraphs_found": 0,
                "requires_reverification": False,
                "last_updated": None,
                "status": "FAILED",
            }

        if response.status_code == 429:
            time.sleep(30)
            response, url_used = fetch_page_with_fallback(entry.url, headers)
            if response.status_code != 200:
                duration_ms = int((time.perf_counter() - start) * 1000)
                if not dry_run:
                    write_scrape_log(
                        db_conn, entry.code, "FAILED", 0, duration_ms,
                        f"HTTP {response.status_code} after retry — {url_used}",
                    )
                return {
                    "code": entry.code,
                    "paragraphs_found": 0,
                    "requires_reverification": False,
                    "last_updated": None,
                    "status": "FAILED",
                }

        response.raise_for_status()
    except httpx.HTTPStatusError as e:
        duration_ms = int((time.perf_counter() - start) * 1000)
        if not dry_run:
            write_scrape_log(db_conn, entry.code, "FAILED", 0, duration_ms, f"{e} — {url_used}")
        return {
            "code": entry.code,
            "paragraphs_found": 0,
            "requires_reverification": False,
            "last_updated": None,
            "status": "FAILED",
        }
    except Exception as e:
        duration_ms = int((time.perf_counter() - start) * 1000)
        if not dry_run:
            write_scrape_log(db_conn, entry.code, "FAILED", 0, duration_ms, f"{e} — {url_used}")
        return {
            "code": entry.code,
            "paragraphs_found": 0,
            "requires_reverification": False,
            "last_updated": None,
            "status": "FAILED",
        }

    soup = BeautifulSoup(response.text, "lxml")

    # Extract Last Updated date
    time_elem = soup.find("time", attrs={"datetime": True})
    if time_elem and time_elem.get("datetime"):
        try:
            dt_str = time_elem["datetime"]
            if "T" in dt_str:
                last_updated = datetime.fromisoformat(dt_str.replace("Z", "+00:00"))
            else:
                last_updated = datetime.strptime(dt_str[:10], "%Y-%m-%d")
            if hasattr(last_updated, "date"):
                last_updated_date = last_updated.date()
            else:
                last_updated_date = last_updated
            if last_updated_date > CHANGE_CUTOFF_DATE:
                requires_reverification = True
        except (ValueError, TypeError):
            requires_reverification = True
    else:
        # Try app-c-published-dates
        dates_div = soup.find(class_=re.compile("published-dates", re.I))
        if dates_div:
            time_elem = dates_div.find("time", attrs={"datetime": True})
            if time_elem and time_elem.get("datetime"):
                try:
                    dt_str = time_elem["datetime"][:10]
                    last_updated = datetime.strptime(dt_str, "%Y-%m-%d")
                    if last_updated.date() > CHANGE_CUTOFF_DATE:
                        requires_reverification = True
                except (ValueError, TypeError):
                    requires_reverification = True
        else:
            requires_reverification = True

    page_hash = hashlib.sha256(response.text.encode("utf-8")).hexdigest()

    if not dry_run:
        content_changed = detect_change(entry.code, page_hash, db_conn)
        if content_changed:
            requires_reverification = True

    paragraphs = extract_paragraphs(soup, entry.code)

    last_updated_date = last_updated.date() if last_updated and hasattr(last_updated, "date") else last_updated

    if not paragraphs:
        status = "FLAGGED"
        if not dry_run:
            duration_ms = int((time.perf_counter() - start) * 1000)
            write_scrape_log(db_conn, entry.code, "FLAGGED", 0, duration_ms, "No paragraphs found")
    else:
        status = "FLAGGED" if requires_reverification else "SUCCESS"
        if not dry_run:
            upsert_appendix(db_conn, entry, last_updated_date, page_hash, requires_reverification)
            insert_paragraphs(db_conn, paragraphs)
            duration_ms = int((time.perf_counter() - start) * 1000)
            write_scrape_log(db_conn, entry.code, status, len(paragraphs), duration_ms)

    time.sleep(CRAWL_DELAY_SECONDS)

    return {
        "code": entry.code,
        "paragraphs_found": len(paragraphs),
        "requires_reverification": requires_reverification,
        "last_updated": last_updated.strftime("%Y-%m-%d") if last_updated else None,
        "status": status,
    }


def run_scraper(mode: str = "phase1", dry_run: bool = False) -> dict:
    """Run the scraper. mode='phase1' (1-6) or 'all' (all 18)."""
    manifest = get_phase1_critical() if mode == "phase1" else get_manifest_by_priority()
    conn = get_connection()

    total = len(manifest)
    success = 0
    flagged = 0
    failed = 0
    total_paragraphs = 0
    failed_codes = []

    for i, entry in enumerate(manifest, 1):
        suffix = ""
        try:
            result = scrape_appendix(entry, conn, dry_run=dry_run)

            if result["status"] == "FAILED":
                failed += 1
                failed_codes.append(entry.code)
                suffix = "FAILED"
            elif result["status"] == "FLAGGED":
                flagged += 1
                if result.get("last_updated"):
                    suffix = f"FLAGGED (updated {result['last_updated']})"
                else:
                    suffix = "FLAGGED"
            else:
                success += 1
                suffix = "OK"

            total_paragraphs += result["paragraphs_found"]
            pf = result["paragraphs_found"]
            if result["status"] == "FAILED":
                print(f"  [{i}/{total}] Scraping {entry.code}... FAILED")
            elif result["status"] == "FLAGGED":
                lu = result.get("last_updated")
                suffix = f" (updated {datetime.strptime(lu, '%Y-%m-%d').strftime('%b %Y')})" if lu else ""
                part = f"{pf} paragraphs " if pf else ""
                print(f"  [{i}/{total}] Scraping {entry.code}... {part}FLAGGED{suffix}")
            else:
                print(f"  [{i}/{total}] Scraping {entry.code}... {pf} paragraphs ✓")

        except Exception as e:
            failed += 1
            failed_codes.append(entry.code)
            print(f"  [{i}/{total}] Scraping {entry.code}... FAILED ({e})")

    conn.close()

    return {
        "total": total,
        "success": success,
        "flagged": flagged,
        "failed": failed,
        "total_paragraphs": total_paragraphs,
        "failed_codes": failed_codes,
    }


if __name__ == "__main__":
    import sys

    mode = sys.argv[1] if len(sys.argv) > 1 else "phase1"
    dry_run = "--dry-run" in sys.argv

    print(f"Starting GOV.UK scraper — mode: {mode}")
    if dry_run:
        print("DRY RUN — no data will be written")

    result = run_scraper(mode=mode, dry_run=dry_run)

    print(f"""
╔══════════════════════════════════╗
  SCRAPER COMPLETE
  Total:      {result['total']}
  Success:    {result['success']}
  Flagged:    {result['flagged']}
  Failed:     {result['failed']}
  Paragraphs: {result['total_paragraphs']}
╚══════════════════════════════════╝
    """)
    if result["failed_codes"]:
        print(f"Failed appendices: {result['failed_codes']}")
