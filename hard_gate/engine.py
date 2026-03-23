"""
Hard Gate Engine — evaluates hard gates per session.
"""

from hard_gate.loader import HARD_GATE_DEFINITIONS

ETA_REQUIRED_NATIONALITIES = {
    "AG", "AI", "AL", "AN", "AR", "AT", "AU", "AW", "AZ",
    "BA", "BB", "BE", "BG", "BH", "BM", "BO", "BR", "BW",
    "CA", "CH", "CL", "CO", "CR", "CW", "CY", "CZ",
    "DE", "DK", "DM", "DO",
    "EC", "EE", "FI", "FJ", "FR",
    "GB", "GD", "GR", "GT", "GY",
    "HK", "HR", "HU",
    "IL", "IS",
    "JP",
    "KN", "KR", "KW",
    "LC", "LI", "LT", "LU", "LV",
    "MC", "MD", "ME", "MK", "MT", "MU", "MX", "MY",
    "NL", "NO", "NZ",
    "OM",
    "PA", "PE", "PL", "PT",
    "QA", "RO",
    "SA", "SE", "SG", "SI", "SK", "SM", "SR", "SX",
    "TC", "TH", "TT", "TW",
    "US", "UY",
    "VA", "VC", "VG", "VN", "WS",
}

DISCLAIMER = (
    "This is a Preliminary Self-Assessment only. "
    "It does not constitute legal advice. "
    "You should consult a qualified immigration solicitor "
    "before making any application."
)

ANSWER_MAP = {
    "DEPORTATION_ORDER": "has_deportation_order",
    "DECEPTION": "has_used_deception",
    "CRIMINALITY": "has_criminal_conviction",
    "IMMIGRATION_DEBT": "has_immigration_debt",
    "OVERSTAY": "has_overstayed_90_days",
}


def load_gates_from_db(db_conn) -> list:
    """Load active gates from DB ordered by gate_order."""
    cur = db_conn.cursor()
    cur.execute(
        "SELECT gate_order, name, paragraph_ref, question, fail_type, fail_message, fires_before_route "
        "FROM hard_gates WHERE active = TRUE ORDER BY gate_order"
    )
    columns = ["gate_order", "name", "paragraph_ref", "question", "fail_type", "fail_message", "fires_before_route"]
    rows = cur.fetchall()
    cur.close()
    return [dict(zip(columns, row)) for row in rows]


def evaluate_hard_gates(user_answers: dict, db_conn=None) -> dict:
    """
    Evaluate hard gates in order.
    If db_conn is None: use HARD_GATE_DEFINITIONS (no DB).
    Else: load gates from DB.
    """
    if db_conn is None:
        gates = HARD_GATE_DEFINITIONS
    else:
        gates = load_gates_from_db(db_conn)

    flagged_gates = []

    for gate in gates:
        gate_name = gate["name"]

        if gate_name == "ETA_PRE_GATE":
            nationality = user_answers.get("nationality_iso") or ""
            if nationality.upper() in ETA_REQUIRED_NATIONALITIES:
                flagged_gates.append({
                    "gate_name": gate_name,
                    "fail_type": "FLAG",
                    "fail_message": gate["fail_message"],
                    "paragraph_ref": gate["paragraph_ref"],
                })
            continue

        answer_key = ANSWER_MAP.get(gate_name)
        if answer_key is None:
            continue

        if user_answers.get(answer_key) is True:
            if gate["fail_type"] == "HARD_FAIL":
                return {
                    "result": "HARD_FAIL",
                    "gate_name": gate_name,
                    "paragraph_ref": gate["paragraph_ref"],
                    "fail_message": gate["fail_message"],
                    "session_can_continue": False,
                    "flagged_gates": [],
                    "requires_solicitor_review": True,
                    "disclaimer": DISCLAIMER,
                }
            elif gate["fail_type"] == "FLAG":
                flagged_gates.append({
                    "gate_name": gate_name,
                    "fail_type": "FLAG",
                    "fail_message": gate["fail_message"],
                    "paragraph_ref": gate["paragraph_ref"],
                })

    return {
        "result": "FLAGGED" if flagged_gates else "PASS",
        "gate_name": None,
        "paragraph_ref": None,
        "fail_message": None,
        "session_can_continue": True,
        "flagged_gates": flagged_gates,
        "requires_solicitor_review": len(flagged_gates) > 0,
        "disclaimer": DISCLAIMER,
    }
