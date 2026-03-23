"""Scraper manifest — GOV.UK source URLs and crawl config."""

from dataclasses import dataclass
from typing import Optional

from db.connection import get_connection


@dataclass
class AppendixEntry:
    code: str
    url: str
    priority: int
    is_hard_gate_source: bool
    flag_2026: Optional[str]
    description: str


APPENDIX_MANIFEST = [
    AppendixEntry(
        code="PART_SUITABILITY",
        url="https://www.gov.uk/guidance/immigration-rules/immigration-rules-part-suitability",
        priority=1, is_hard_gate_source=True, flag_2026=None,
        description="Hard Gate source. 2026 replacement for Part 9. Must scrape first."
    ),
    AppendixEntry(
        code="PART_9_LEGACY",
        url="https://www.gov.uk/guidance/immigration-rules/immigration-rules-part-9-grounds-for-refusal",
        priority=2, is_hard_gate_source=True, flag_2026=None,
        description="Legacy refusal grounds. Cross-referenced with Part Suitability."
    ),
    AppendixEntry(
        code="APPENDIX_FINANCE",
        url="https://www.gov.uk/guidance/immigration-rules/immigration-rules-appendix-finance",
        priority=3, is_hard_gate_source=False, flag_2026=None,
        description="FIN rules used across ALL visa routes."
    ),
    AppendixEntry(
        code="APPENDIX_ENGLISH",
        url="https://www.gov.uk/guidance/immigration-rules/immigration-rules-appendix-english-language",
        priority=4, is_hard_gate_source=False, flag_2026="B2_ENGLISH_UPDATE",
        description="WARNING: B2 level update effective Jan 8 2026. Old data says B1."
    ),
    AppendixEntry(
        code="APPENDIX_ETA",
        url="https://www.gov.uk/guidance/immigration-rules/immigration-rules-appendix-electronic-travel-authorisation",
        priority=5, is_hard_gate_source=True, flag_2026="ETA_MANDATORY",
        description="WARNING: Mandatory for 85 nations from Feb 25 2026."
    ),
    AppendixEntry(
        code="SKILLED_WORKER",
        url="https://www.gov.uk/guidance/immigration-rules/immigration-rules-appendix-skilled-worker",
        priority=6, is_hard_gate_source=False, flag_2026="B2_ENGLISH_UPDATE",
        description="Core work route. B2 English from Jan 2026."
    ),
    AppendixEntry(
        code="SALARY_LIST",
        url="https://www.gov.uk/guidance/immigration-rules/immigration-rules-appendix-immigration-salary-list",
        priority=7, is_hard_gate_source=False, flag_2026=None,
        description="2025/26 salary thresholds for Skilled Worker route."
    ),
    AppendixEntry(
        code="GLOBAL_TALENT",
        url="https://www.gov.uk/guidance/immigration-rules/immigration-rules-appendix-global-talent",
        priority=8, is_hard_gate_source=False, flag_2026=None,
        description="Academia, research, arts, digital technology leaders."
    ),
    AppendixEntry(
        code="HPI",
        url="https://www.gov.uk/guidance/immigration-rules/immigration-rules-appendix-high-potential-individual",
        priority=9, is_hard_gate_source=False, flag_2026="B2_ENGLISH_UPDATE",
        description="Top global university graduates. B2 English from Jan 2026."
    ),
    AppendixEntry(
        code="SCALE_UP",
        url="https://www.gov.uk/guidance/immigration-rules/immigration-rules-appendix-scale-up",
        priority=10, is_hard_gate_source=False, flag_2026="SETTLEMENT_10YR",
        description="High-growth UK company workers. 10yr settlement from Apr 2026."
    ),
    AppendixEntry(
        code="APPENDIX_FM",
        url="https://www.gov.uk/guidance/immigration-rules/immigration-rules-appendix-fm",
        priority=11, is_hard_gate_source=False, flag_2026=None,
        description="Family Members route. Spouse, partner, children."
    ),
    AppendixEntry(
        code="APPENDIX_STUDENT",
        url="https://www.gov.uk/guidance/immigration-rules/immigration-rules-appendix-student",
        priority=12, is_hard_gate_source=False, flag_2026=None,
        description="Study at UK licensed student sponsor institution."
    ),
    AppendixEntry(
        code="APPENDIX_GRADUATE",
        url="https://www.gov.uk/guidance/immigration-rules/immigration-rules-appendix-graduate",
        priority=13, is_hard_gate_source=False, flag_2026=None,
        description="Post-study work route. 18-month duration update."
    ),
    AppendixEntry(
        code="APPENDIX_VISITOR",
        url="https://www.gov.uk/guidance/immigration-rules/immigration-rules-appendix-v-visitor-rules",
        priority=14, is_hard_gate_source=False, flag_2026=None,
        description="Tourism, business visits, family visits."
    ),
    AppendixEntry(
        code="APPENDIX_CONTINUOUS_RESIDENCE",
        url="https://www.gov.uk/guidance/immigration-rules/immigration-rules-appendix-continuous-residence",
        priority=15, is_hard_gate_source=False, flag_2026="SETTLEMENT_10YR",
        description="10-year earned settlement path from April 2026."
    ),
    AppendixEntry(
        code="APPENDIX_TB",
        url="https://www.gov.uk/guidance/immigration-rules/immigration-rules-appendix-tuberculosis-tb",
        priority=16, is_hard_gate_source=False, flag_2026=None,
        description="TB test requirement for certain nationalities."
    ),
    AppendixEntry(
        code="RULES_INTRODUCTION",
        url="https://www.gov.uk/guidance/immigration-rules/immigration-rules-introduction",
        priority=17, is_hard_gate_source=False, flag_2026=None,
        description="Definitions and general provisions."
    ),
    AppendixEntry(
        code="PART_1_LEAVE_TO_ENTER",
        url="https://www.gov.uk/guidance/immigration-rules/immigration-rules-part-1-leave-to-enter-or-stay-in-the-uk",
        priority=18, is_hard_gate_source=False, flag_2026=None,
        description="Validity of applications and leave to enter."
    ),
]

MASTER_INDEX_URL = "https://www.gov.uk/guidance/immigration-rules/immigration-rules-index"
CHANGE_CUTOFF_DATE = "2026-02-01"


def get_manifest_by_priority() -> list:
    """Returns full manifest sorted by priority ascending."""
    return sorted(APPENDIX_MANIFEST, key=lambda x: x.priority)


def get_phase1_critical() -> list:
    """Returns priorities 1,3,4,5,6 — excludes PART_9_LEGACY (404)."""
    EXCLUDE = {"PART_9_LEGACY"}
    return [a for a in APPENDIX_MANIFEST if a.priority <= 6 and a.code not in EXCLUDE]


def get_hard_gate_sources() -> list:
    """Returns only appendices that are hard gate sources."""
    return [a for a in APPENDIX_MANIFEST if a.is_hard_gate_source]


def get_flagged_2026() -> list:
    """Returns appendices with 2026 rule change flags."""
    return [a for a in APPENDIX_MANIFEST if a.flag_2026 is not None]


def seed_appendices_to_db(db_conn) -> int:
    """
    Insert all manifest entries into the appendices table.
    Uses INSERT ON CONFLICT (code) DO UPDATE to be idempotent.
    Returns count of rows upserted.
    """
    cur = db_conn.cursor()
    count = 0
    for entry in get_manifest_by_priority():
        cur.execute("""
            INSERT INTO appendices
                (code, url, priority, is_hard_gate_source, flag_2026)
            VALUES (%s, %s, %s, %s, %s)
            ON CONFLICT (code) DO UPDATE SET
                url = EXCLUDED.url,
                priority = EXCLUDED.priority,
                is_hard_gate_source = EXCLUDED.is_hard_gate_source,
                flag_2026 = EXCLUDED.flag_2026
        """, (
            entry.code, entry.url, entry.priority,
            entry.is_hard_gate_source, entry.flag_2026
        ))
        count += 1
    db_conn.commit()
    cur.close()
    return count


if __name__ == "__main__":
    manifest = get_manifest_by_priority()
    print(f"Total appendices: {len(manifest)}")
    print(f"Phase 1 critical: {len(get_phase1_critical())}")
    print(f"Hard gate sources: {len(get_hard_gate_sources())}")
    print(f"2026 flagged:      {len(get_flagged_2026())}")
    print("\nPhase 1 Critical Appendices (scrape these first):")
    for a in get_phase1_critical():
        flag = f"  ⚠️  {a.flag_2026}" if a.flag_2026 else ""
        print(f"  [{a.priority}] {a.code}{flag}")

    print("\nSeeding appendices to database...")
    conn = get_connection()
    seeded = seed_appendices_to_db(conn)
    conn.close()
    print(f"Seeded {seeded} appendices to DB ✅")
