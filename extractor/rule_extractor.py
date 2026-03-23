"""
Rule Extractor — converts raw legal text into structured constraint JSON using GPT-4.
GPT-4 is used ONLY for text extraction. It does NOT make eligibility decisions.
"""

import json
import time
from typing import Optional

from openai import OpenAI

from db.connection import get_connection

EXTRACTION_PROMPT = """
You are a legal data extraction assistant for UK Immigration Rules.
Your ONLY job is to convert a raw legal paragraph into structured JSON.
Never infer, guess, or add rules not explicitly written in the text.

Appendix: {appendix_code}
Paragraph reference: {paragraph_ref}
Heading context: {heading_context}
Raw legal text: "{raw_text}"

Return ONLY a valid JSON object with this exact schema:
{{
  "paragraph_ref": "{paragraph_ref}",
  "appendix_code": "{appendix_code}",
  "rule_type": "one of: eligibility|suitability|definition|procedure|evidence|financial|language",
  "field": "snake_case name of the data field being checked (e.g. salary_annual_gbp, english_level, bank_balance_gbp, has_criminal_conviction)",
  "operator": "one of: gte|lte|eq|neq|in|not_in|exists|not_exists|between|any",
  "value": "the threshold or required value (number, string, array, or null)",
  "value_max": "upper bound if operator is between, else null",
  "unit": "one of: GBP|days|years|months|null",
  "user_question": "plain English question a non-lawyer can answer in under 20 words",
  "answer_type": "one of: currency|integer|boolean|select|date|text|number",
  "answer_options": ["array of strings if answer_type is select, else null"],
  "fail_condition_description": "one plain English sentence — why this causes failure",
  "is_hard_gate": false,
  "confidence": 0.0,
  "extraction_notes": "flag any ambiguity, complex conditions, or multi-part rules"
}}

Confidence scoring rules (be strict):
- 0.90-1.00: field, operator, value all unambiguous and directly stated
- 0.75-0.89: minor ambiguity in one field, or multi-part condition
- below 0.75: complex conditional, cross-reference to another rule, 
              or text is a definition not a checkable constraint

Return ONLY the JSON. No preamble, no explanation, no markdown fences.
"""

VALID_OPERATORS = frozenset(
    ["gte", "lte", "eq", "neq", "in", "not_in", "exists", "not_exists", "between", "any"]
)
VALID_ANSWER_TYPES = frozenset(
    ["currency", "integer", "boolean", "select", "date", "text", "number"]
)


def validate_constraint_json(constraint: Optional[dict]) -> bool:
    """Validate constraint JSON. Returns False if any check fails."""
    if not constraint or not isinstance(constraint, dict):
        return False
    if not constraint.get("field") or not isinstance(constraint["field"], str):
        return False
    if constraint.get("operator") not in VALID_OPERATORS:
        return False
    uq = constraint.get("user_question")
    if not uq or not isinstance(uq, str) or len(uq) <= 10:
        return False
    conf = constraint.get("confidence")
    if conf is None or not isinstance(conf, (int, float)) or not (0.0 <= conf <= 1.0):
        return False
    if constraint.get("answer_type") not in VALID_ANSWER_TYPES:
        return False
    return True


def extract_single_rule(paragraph: dict) -> dict:
    """
    Extract structured constraint from one paragraph using GPT-4.
    paragraph: {paragraph_ref, appendix_code, raw_text, heading_context}
    """
    prompt = EXTRACTION_PROMPT.format(
        appendix_code=paragraph.get("appendix_code", ""),
        paragraph_ref=paragraph.get("paragraph_ref", ""),
        heading_context=paragraph.get("heading_context", ""),
        raw_text=(paragraph.get("raw_text", "") or "").replace('"', '\\"'),
    )
    try:
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4",
            temperature=0,
            max_tokens=600,
            messages=[{"role": "user", "content": prompt}],
        )
        content = response.choices[0].message.content.strip()
        content = content.removeprefix("```json").removeprefix("```").strip()
        constraint_json = json.loads(content)
    except (json.JSONDecodeError, Exception):
        return {
            "paragraph_ref": paragraph.get("paragraph_ref", ""),
            "constraint_json": None,
            "requires_human_review": True,
            "confidence": 0.0,
        }

    if not validate_constraint_json(constraint_json):
        return {
            "paragraph_ref": paragraph.get("paragraph_ref", ""),
            "constraint_json": None,
            "requires_human_review": True,
            "confidence": 0.0,
        }

    confidence = float(constraint_json.get("confidence", 0.0))
    requires_human_review = confidence < 0.75

    return {
        "paragraph_ref": paragraph.get("paragraph_ref", ""),
        "constraint_json": constraint_json,
        "requires_human_review": requires_human_review,
        "confidence": confidence,
    }


def save_extraction_results(
    db_conn,
    paragraph_ref: str,
    constraint_json: dict,
    requires_human_review: bool,
) -> None:
    """Update rule_paragraphs and insert question_template."""
    cur = db_conn.cursor()
    cur.execute(
        """
        UPDATE rule_paragraphs SET
            constraint_json = %s,
            requires_human_review = %s
        WHERE paragraph_ref = %s
        """,
        (json.dumps(constraint_json), requires_human_review, paragraph_ref),
    )

    sequence_stage = (
        "hard_gate"
        if constraint_json.get("is_hard_gate") is True
        else "route_specific"
    )

    cur.execute(
        """
        INSERT INTO question_templates (
            paragraph_ref, appendix_code, sequence_stage, question_text,
            answer_type, answer_options, fail_condition_description,
            confidence, requires_human_review, verified
        ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE)
        """,
        (
            paragraph_ref,
            constraint_json.get("appendix_code", ""),
            sequence_stage,
            constraint_json.get("user_question", ""),
            constraint_json.get("answer_type", "text"),
            json.dumps(constraint_json.get("answer_options")) if constraint_json.get("answer_options") else None,
            constraint_json.get("fail_condition_description"),
            constraint_json.get("confidence", 0.0),
            requires_human_review,
        ),
    )
    db_conn.commit()
    cur.close()


def run_extractor(
    appendix_code: Optional[str] = None,
    limit: Optional[int] = None,
    dry_run: bool = False,
) -> dict:
    """Run extraction on paragraphs with constraint_json IS NULL."""
    conn = get_connection()
    cur = conn.cursor()
    query = "SELECT paragraph_ref, appendix_code, raw_text FROM rule_paragraphs WHERE constraint_json IS NULL"
    params = []
    if appendix_code:
        query += " AND appendix_code = %s"
        params.append(appendix_code)
    query += " ORDER BY appendix_code, paragraph_ref"
    if limit:
        query += " LIMIT %s"
        params.append(limit)
    cur.execute(query, params)
    rows = cur.fetchall()
    cur.close()

    total = len(rows)
    print(f"Found {total} paragraphs to extract")

    processed = 0
    high_confidence = 0
    needs_review = 0
    errors = 0

    for i, row in enumerate(rows, 1):
        paragraph = {
            "paragraph_ref": row[0],
            "appendix_code": row[1],
            "raw_text": row[2],
            "heading_context": "",
        }
        result = extract_single_rule(paragraph)

        if result["constraint_json"] is None:
            errors += 1
            symbol = "✗"
        elif result["requires_human_review"]:
            needs_review += 1
            symbol = "⚠ needs review"
        else:
            high_confidence += 1
            symbol = "✓"

        if not dry_run and result["constraint_json"]:
            save_extraction_results(
                conn,
                result["paragraph_ref"],
                result["constraint_json"],
                result["requires_human_review"],
            )

        processed += 1
        conf = result["confidence"]
        print(f"  [{i}/{total}] {result['paragraph_ref']} → confidence: {conf:.2f} {symbol}")

        time.sleep(0.5)

    conn.close()

    return {
        "processed": processed,
        "high_confidence": high_confidence,
        "needs_review": needs_review,
        "errors": errors,
        "dry_run": dry_run,
    }


def print_extraction_report(db_conn) -> None:
    """Print extraction summary and sample rules."""
    cur = db_conn.cursor()

    cur.execute("SELECT COUNT(*) FROM rule_paragraphs")
    total_paragraphs = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM rule_paragraphs WHERE constraint_json IS NOT NULL"
    )
    extracted = cur.fetchone()[0]

    cur.execute(
        "SELECT COUNT(*) FROM rule_paragraphs WHERE constraint_json IS NULL"
    )
    pending = cur.fetchone()[0]

    cur.execute(
        """
        SELECT COUNT(*) FROM rule_paragraphs
        WHERE constraint_json IS NOT NULL
        AND (constraint_json->>'confidence')::numeric >= 0.75
        """
    )
    high_conf = cur.fetchone()[0]

    cur.execute(
        """
        SELECT COUNT(*) FROM rule_paragraphs
        WHERE constraint_json IS NOT NULL
        AND (constraint_json->>'confidence')::numeric < 0.75
        """
    )
    needs_review = cur.fetchone()[0]

    cur.execute("SELECT COUNT(*) FROM question_templates")
    qt_count = cur.fetchone()[0]

    cur.execute(
        """
        SELECT rp.paragraph_ref,
               rp.constraint_json->>'answer_type' AS answer_type,
               rp.constraint_json->>'confidence' AS confidence
        FROM rule_paragraphs rp
        WHERE rp.constraint_json IS NOT NULL
        ORDER BY rp.paragraph_ref
        LIMIT 5
        """
    )
    samples = cur.fetchall()
    cur.close()

    print("""
╔══════════════════════════════════════╗
  EXTRACTION REPORT
  Total paragraphs:     {}
  Extracted:            {}
  Pending extraction:   {}
  High confidence:      {}  (≥0.75)
  Needs solicitor review: {}  (<0.75)
  question_templates:   {}
╚══════════════════════════════════════╝
""".format(
        total_paragraphs, extracted, pending, high_conf, needs_review, qt_count
    ))

    print("Sample extracted rules (first 5):")
    for ref, atype, conf in samples:
        print(f"  {ref}  | {atype or 'text'} | confidence: {conf or 'N/A'}")


if __name__ == "__main__":
    import sys

    appendix = None
    limit = None
    dry_run = False

    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    for arg in sys.argv[1:]:
        if arg == "--dry-run":
            dry_run = True
        elif arg.startswith("--limit="):
            limit = int(arg.split("=")[1])
        elif arg.startswith("--appendix="):
            appendix = arg.split("=")[1]

    if args:
        if len(args) >= 1 and not args[0].startswith("-"):
            appendix = args[0] if appendix is None else appendix
        if len(args) >= 2:
            try:
                limit = int(args[1]) if limit is None else limit
            except ValueError:
                pass

    print(f"Running extractor — appendix={appendix}, limit={limit}, dry_run={dry_run}")
    result = run_extractor(appendix_code=appendix, limit=limit, dry_run=dry_run)

    print(f"""
Extraction complete:
  Processed: {result['processed']}
  High confidence: {result['high_confidence']}
  Needs review: {result['needs_review']}
  Errors: {result['errors']}
""")

    conn = get_connection()
    print_extraction_report(conn)
    conn.close()
