"""
Intent Classifier — maps free-text input to visa route using GPT-4.
Entry point for every user session. Applies 2026 rule flags.
"""

import json
from typing import Optional

from dotenv import load_dotenv
from openai import OpenAI

load_dotenv()

DISCLAIMER = (
    "This is a Preliminary Self-Assessment only. "
    "It does not constitute legal advice. "
    "You should consult a qualified immigration solicitor "
    "before making any application."
)

ROUTE_2026_FLAGS = {
    "SKILLED_WORKER": ["B2_ENGLISH_UPDATE", "SETTLEMENT_10YR"],
    "HPI": ["B2_ENGLISH_UPDATE", "SETTLEMENT_10YR"],
    "SCALE_UP": ["SETTLEMENT_10YR"],
    "GLOBAL_TALENT": ["SETTLEMENT_10YR"],
    "GRADUATE": [],
    "APPENDIX_FM": [],
    "STUDENT": [],
    "VISITOR": [],
    "UNKNOWN": [],
}

ETA_REQUIRED_NATIONALITIES = {
    "AG", "AI", "AL", "AN", "AR", "AT", "AU", "AW", "AZ",
    "BA", "BB", "BE", "BG", "BH", "BM", "BO", "BR", "BW",
    "CA", "CH", "CL", "CO", "CR", "CW", "CY", "CZ",
    "DE", "DK", "DM", "DO", "EC", "EE", "FI", "FJ", "FR",
    "GB", "GD", "GR", "GT", "GY", "HK", "HR", "HU",
    "IL", "IS", "JP", "KN", "KR", "KW",
    "LC", "LI", "LT", "LU", "LV",
    "MC", "MD", "ME", "MK", "MT", "MU", "MX", "MY",
    "NL", "NO", "NZ", "OM", "PA", "PE", "PL", "PT", "QA", "RO",
    "SA", "SE", "SG", "SI", "SK", "SM", "SR", "SX",
    "TC", "TH", "TT", "TW", "US", "UY",
    "VA", "VC", "VG", "VN", "WS",
}

ORIENTATION_QUESTIONS = [
    {
        "id": "ORIENT-001",
        "question": "Why are you coming to the UK?",
        "answer_type": "select",
        "options": [
            "I have a job offer from a UK employer",
            "I want to study at a UK university or college",
            "I want to join or stay with a family member",
            "I want to visit for tourism or business",
            "I am a recognised leader in my field (talent/research)",
            "I graduated from a top global university",
            "I already have a UK Student visa and recently graduated",
            "I work for a high-growth UK scale-up company",
        ],
    },
    {
        "id": "ORIENT-002",
        "question": "What is your nationality?",
        "answer_type": "text",
        "hint": "Enter your country name or 2-letter ISO code (e.g. US, GB, PK)",
    },
]

CLASSIFICATION_PROMPT = """
You are an intent classifier for a UK visa eligibility platform.
Read the user's input and identify which visa route applies.

Available routes:
- SKILLED_WORKER: has a job offer from a UK Home Office licensed sponsor
- GLOBAL_TALENT: recognised leader in academia, research, arts, or digital technology
- HPI: graduated from a top-ranked global university, no job offer needed
- SCALE_UP: working for a qualifying high-growth UK scale-up company
- APPENDIX_FM: joining or staying with a UK partner, spouse, or family member
- STUDENT: studying at a UK licensed student sponsor institution
- GRADUATE: already in UK on a Student visa and recently graduated
- VISITOR: short stay for tourism, business meeting, or family visit
- UNKNOWN: cannot determine from input provided

User input: "{user_input}"

Return ONLY a valid JSON object — no preamble, no markdown:
{{
  "matched_route": "one of the 9 routes above",
  "confidence": 0.0,
  "reasoning": "one sentence max explaining the match",
  "clarifying_question": "ONE focused question if confidence < 0.75, else null"
}}

Confidence rules:
- 0.90-1.00: route is unambiguous from the input
- 0.75-0.89: likely route but one detail is unclear
- below 0.75: ambiguous — return clarifying_question
"""

ROUTE_TO_APPENDIX = {
    "SKILLED_WORKER": "SKILLED_WORKER",
    "HPI": "HPI",
    "SCALE_UP": "SCALE_UP",
    "GLOBAL_TALENT": "GLOBAL_TALENT",
    "APPENDIX_FM": "APPENDIX_FM",
    "STUDENT": "APPENDIX_STUDENT",
    "GRADUATE": "APPENDIX_GRADUATE",
    "VISITOR": "APPENDIX_VISITOR",
    "UNKNOWN": None,
}

FLAG_WARNINGS = {
    "B2_ENGLISH_UPDATE": (
        "2026 UPDATE: English requirement is now B2 (raised from B1 on 8 Jan 2026). "
        "Your English test result must meet B2 level."
    ),
    "SETTLEMENT_10YR": (
        "2026 UPDATE: Settlement now requires 10 years continuous residence "
        "for this route (changed April 2026, previously 5 years)."
    ),
    "ETA_MANDATORY": (
        "2026 UPDATE: Your nationality requires an Electronic Travel Authorisation (ETA). "
        "This is mandatory from 25 Feb 2026."
    ),
}


def get_orientation_questions() -> list:
    """Return ORIENTATION_QUESTIONS as-is."""
    return ORIENTATION_QUESTIONS


def classify_intent(user_input: str, nationality_iso: Optional[str] = None) -> dict:
    """Classify user input to visa route using GPT-4. Apply 2026 flags."""
    try:
        safe_input = user_input.replace("{", "{{").replace("}", "}}")
        prompt = CLASSIFICATION_PROMPT.format(user_input=safe_input)

        load_dotenv()  # ensure key is loaded even if called in isolation
        client = OpenAI()
        response = client.chat.completions.create(
            model="gpt-4o",
            temperature=0,
            max_tokens=200,
            messages=[{"role": "user", "content": prompt}],
        )
        raw = response.choices[0].message.content.strip()

        # Strip markdown fences
        if raw.startswith("```"):
            raw = raw.split("```")[1]
            if raw.startswith("json"):
                raw = raw[4:]
        if raw.endswith("```"):
            raw = raw[:-3]
        raw = raw.strip()

        # Extract ONLY the first valid JSON object
        # This handles cases where GPT returns extra text after JSON
        import re
        json_match = re.search(r'\{.*?\}', raw, re.DOTALL)
        if not json_match:
            raise ValueError("No JSON object found in response")

        result = json.loads(json_match.group(0))

        route = result.get("matched_route", "UNKNOWN")
        if route not in ROUTE_2026_FLAGS:
            route = "UNKNOWN"

        confidence = float(result.get("confidence", 0.0))
        flags = list(ROUTE_2026_FLAGS.get(route, []))

        eta_required = False
        if nationality_iso:
            eta_required = nationality_iso.upper() in ETA_REQUIRED_NATIONALITIES
            if eta_required and "ETA_MANDATORY" not in flags:
                flags.append("ETA_MANDATORY")

        return {
            "route": route,
            "confidence": confidence,
            "reasoning": result.get("reasoning", ""),
            "flags_2026": flags,
            "eta_required": eta_required,
            "needs_clarification": confidence < 0.75,
            "clarifying_question": result.get("clarifying_question"),
            "disclaimer": DISCLAIMER,
        }
    except Exception as e:
        return {
            "route": "UNKNOWN",
            "confidence": 0.0,
            "reasoning": f"Classification failed: {str(e)}",
            "flags_2026": [],
            "eta_required": False,
            "needs_clarification": True,
            "clarifying_question": ORIENTATION_QUESTIONS[0]["question"],
            "disclaimer": DISCLAIMER,
        }


def load_questions_for_route(route: str, db_conn) -> list:
    """Load verified/unverified question templates for route. Phase 1 allows verified=FALSE."""
    appendix_code = ROUTE_TO_APPENDIX.get(route)
    if not appendix_code:
        return []

    cur = db_conn.cursor()
    cur.execute(
        """
        SELECT qt.id, qt.paragraph_ref, qt.question_text, qt.answer_type,
               qt.answer_options, qt.fail_condition_description,
               qt.sequence_stage, qt.confidence
        FROM question_templates qt
        JOIN rule_paragraphs rp ON qt.paragraph_ref = rp.paragraph_ref
        WHERE rp.appendix_code = %s
          AND qt.verified = FALSE
          AND qt.sequence_stage != 'hard_gate'
        ORDER BY qt.sequence_stage, qt.id
        """,
        (appendix_code,),
    )
    rows = cur.fetchall()
    cur.close()

    questions = []
    for row in rows:
        questions.append({
            "id": row[0],
            "paragraph_ref": row[1],
            "question_text": row[2],
            "answer_type": row[3],
            "answer_options": row[4],
            "fail_condition_description": row[5],
            "sequence_stage": row[6],
            "confidence": float(row[7]) if row[7] is not None else None,
        })

    if questions:
        print(
            f"  Warning: {len(questions)} unverified questions loaded for route {route}. "
            "Solicitor review required before go-live."
        )

    return questions


def build_session_context(
    user_input: str, nationality_iso: str, db_conn=None
) -> dict:
    """Main entry point at session start."""
    result = classify_intent(user_input, nationality_iso)

    if result["needs_clarification"]:
        result["status"] = "NEEDS_CLARIFICATION"
        return result

    if result["route"] == "UNKNOWN":
        result["status"] = "UNKNOWN"
        return result

    questions_loaded = 0
    if db_conn:
        questions = load_questions_for_route(result["route"], db_conn)
        questions_loaded = len(questions)

    flag_warnings = []
    for flag in result["flags_2026"]:
        if flag in FLAG_WARNINGS:
            flag_warnings.append(f"  {FLAG_WARNINGS[flag]}")

    return {
        "status": "READY",
        "route": result["route"],
        "confidence": result["confidence"],
        "flags_2026": result["flags_2026"],
        "eta_required": result["eta_required"],
        "flag_warnings": flag_warnings,
        "questions_loaded": questions_loaded,
        "next_step": "hard_gate",
        "orientation_complete": True,
        "disclaimer": DISCLAIMER,
    }


if __name__ == "__main__":
    import sys

    if "--test" in sys.argv:
        import time

        test_inputs = [
            ("I have a job offer from a hospital in Manchester", "PK"),
            ("I want to visit London for a week", "US"),
            ("I graduated from MIT last year", "IN"),
            ("I want to be with my British wife", "NG"),
            ("I am studying at Oxford University", "CN"),
        ]

        print("Running classifier tests...\n")
        for i, (user_input, nationality) in enumerate(test_inputs):
            result = classify_intent(user_input, nationality)
            flags = ", ".join(result["flags_2026"]) or "none"
            clarify = (
                f" → ASK: {result['clarifying_question']}"
                if result["needs_clarification"]
                else ""
            )
            print(f"Input:  '{user_input}'")
            print(
                f"Route:  {result['route']} "
                f"(confidence: {result['confidence']:.2f}){clarify}"
            )
            print(f"Flags:  {flags}")
            print(f"ETA:    {result['eta_required']}")
            print()
            if i < len(test_inputs) - 1:
                time.sleep(2)  # avoid rate limiting

    else:
        print("UK Visa Intent Classifier — Interactive Mode")
        print("Type your situation in plain English.")
        print("Type 'quit' to exit.\n")

        nationality = input("Your nationality (2-letter ISO code): ").strip()

        while True:
            user_input = input("\nDescribe your situation: ").strip()
            if user_input.lower() == "quit":
                break

            result = classify_intent(user_input, nationality)

            print(f"\n  Route identified: {result['route']}")
            print(f"  Confidence:       {result['confidence']:.2f}")
            print(f"  2026 Flags:       {result['flags_2026']}")
            print(f"  ETA required:    {result['eta_required']}")

            if result["needs_clarification"]:
                print(f"\n  Clarification needed:")
                print(f"  → {result['clarifying_question']}")

            if result["flags_2026"]:
                if "B2_ENGLISH_UPDATE" in result["flags_2026"]:
                    print(f"\n  English requirement is now B2")
                if "SETTLEMENT_10YR" in result["flags_2026"]:
                    print(f"  Settlement path is now 10 years")
                if "ETA_MANDATORY" in result["flags_2026"]:
                    print(f"  ETA required before travel")
