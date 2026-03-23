"""
Hard Gate Loader — creates hard_gates table, loads definitions, tags paragraphs.
"""

HARD_GATE_DEFINITIONS = [
    {
        "gate_order": 0,
        "name": "ETA_PRE_GATE",
        "paragraph_ref": "ETA-1.1",
        "question": "What is your nationality?",
        "fail_type": "FLAG",
        "fail_message": "Your nationality requires an Electronic Travel Authorisation (ETA) before travelling to the UK. You must obtain this before any visa assessment continues.",
        "fires_before_route": True,
    },
    {
        "gate_order": 1,
        "name": "DEPORTATION_ORDER",
        "paragraph_ref": "S-EC.1.1",
        "question": "Are you currently subject to a deportation or exclusion order from the UK?",
        "fail_type": "HARD_FAIL",
        "fail_message": "You are subject to a deportation or exclusion order. No UK visa application can proceed. You must seek specialist legal advice immediately.",
        "fires_before_route": True,
    },
    {
        "gate_order": 2,
        "name": "DECEPTION",
        "paragraph_ref": "S-EC.2.2",
        "question": "Have you ever used false documents or provided false information in any UK visa application?",
        "fail_type": "HARD_FAIL",
        "fail_message": "A previous deception finding is an automatic bar to entry. No UK visa application can proceed. You must seek specialist legal advice.",
        "fires_before_route": True,
    },
    {
        "gate_order": 3,
        "name": "CRIMINALITY",
        "paragraph_ref": "SUI-5.1",
        "question": "Do you have any criminal convictions in any country, including spent convictions?",
        "fail_type": "FLAG",
        "fail_message": "Criminal convictions may affect your eligibility. A qualified immigration solicitor must assess the impact before you proceed.",
        "fires_before_route": True,
    },
    {
        "gate_order": 4,
        "name": "IMMIGRATION_DEBT",
        "paragraph_ref": "S-EC.2.5",
        "question": "Do you owe any unpaid litigation costs or civil penalties to the UK Home Office?",
        "fail_type": "FLAG",
        "fail_message": "Outstanding immigration debt may affect your eligibility. This must be resolved or assessed by a solicitor before proceeding.",
        "fires_before_route": True,
    },
    {
        "gate_order": 5,
        "name": "OVERSTAY",
        "paragraph_ref": "S-EC.2.6",
        "question": "Have you previously overstayed a UK visa by more than 90 days?",
        "fail_type": "FLAG",
        "fail_message": "A previous overstay of more than 90 days triggers a re-entry ban. A solicitor must assess the duration and impact before you proceed.",
        "fires_before_route": True,
    },
]


def load_hard_gates(db_conn) -> dict:
    """Load hard gate definitions into DB, tag rule_paragraphs and question_templates."""
    cur = db_conn.cursor()

    cur.execute("""
        CREATE TABLE IF NOT EXISTS hard_gates (
            id            SERIAL PRIMARY KEY,
            gate_order    INTEGER UNIQUE NOT NULL,
            name          VARCHAR(50) NOT NULL,
            paragraph_ref VARCHAR(30),
            question      TEXT NOT NULL,
            fail_type     VARCHAR(20) NOT NULL,
            fail_message  TEXT NOT NULL,
            fires_before_route BOOLEAN DEFAULT TRUE,
            active        BOOLEAN DEFAULT TRUE
        )
    """)
    db_conn.commit()

    paragraphs_tagged = 0
    templates_tagged = 0

    for gate in HARD_GATE_DEFINITIONS:
        cur.execute(
            """
            INSERT INTO hard_gates
                (gate_order, name, paragraph_ref, question, fail_type, fail_message, fires_before_route)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (gate_order) DO UPDATE SET
                name = EXCLUDED.name,
                paragraph_ref = EXCLUDED.paragraph_ref,
                question = EXCLUDED.question,
                fail_type = EXCLUDED.fail_type,
                fail_message = EXCLUDED.fail_message
            """,
            (
                gate["gate_order"],
                gate["name"],
                gate["paragraph_ref"],
                gate["question"],
                gate["fail_type"],
                gate["fail_message"],
                gate["fires_before_route"],
            ),
        )

        cur.execute(
            """
            UPDATE rule_paragraphs SET
                is_hard_gate = TRUE, sequence_stage = 'hard_gate'
            WHERE paragraph_ref = %s
            """,
            (gate["paragraph_ref"],),
        )
        paragraphs_tagged += cur.rowcount

        cur.execute(
            """
            UPDATE question_templates SET
                sequence_stage = 'hard_gate', verified = FALSE
            WHERE paragraph_ref = %s
            """,
            (gate["paragraph_ref"],),
        )
        templates_tagged += cur.rowcount

        print(f"  [{gate['gate_order']}] {gate['name']:18} → {gate['fail_type']:9} | paragraph: {gate['paragraph_ref']}")

    db_conn.commit()
    cur.close()

    return {
        "gates_loaded": len(HARD_GATE_DEFINITIONS),
        "paragraphs_tagged": paragraphs_tagged,
        "templates_tagged": templates_tagged,
    }


if __name__ == "__main__":
    from db.connection import get_connection

    conn = get_connection()
    print("Loading hard gates into database...")
    result = load_hard_gates(conn)
    print(
        f"""
  Gates loaded:       {result['gates_loaded']}
  Paragraphs tagged:  {result['paragraphs_tagged']}
  Templates tagged:   {result['templates_tagged']}
    """
    )
    conn.close()
    print("Hard Gate Engine ready ✅")
