# HIGH CONFIDENCE INPUTS (score >= 0.75):
# "I have a job offer from a UK employer and need a work visa"
# "I want to visit the UK for tourism for 2 weeks"
# "I want to join my British spouse in the UK"
# "I am a student accepted at a UK university"
# "I graduated from a top global university"

import uuid
import json
from classifier.intent_classifier import classify_intent, ROUTE_TO_APPENDIX
from hard_gate.engine import evaluate_hard_gates
from hard_gate.loader import HARD_GATE_DEFINITIONS
from api.engine.rule_engine import load_constraint, get_session_summary, save_session_result, get_checklist_for_route

DISCLAIMER = (
    "This is a Preliminary Self-Assessment only. "
    "It does not constitute legal advice. "
    "You should consult a qualified immigration solicitor "
    "before making any application."
)

BRANCH_RULES = {
    "SKILLED_WORKER": [
        {
            "trigger_field": "has_phd",
            "trigger_value": True,
            "action": "reduce_salary_threshold",
            "description": "PhD holders qualify for 20% salary discount",
            "modified_constraint": {
                "field": "salary_annual_gbp",
                "operator": "gte",
                "value": 20960,  
                "paragraph_ref": "SW-14.1-PHD"
            }
        },
        {
            "trigger_field": "is_health_care_worker",
            "trigger_value": True,
            "action": "use_ashe_salary",
            "description": "Health/care workers use ASHE salary scale",
            "modified_constraint": None  
        }
    ]
}

def load_sequence(route: str, flags_2026: list, db_conn) -> list:
    from classifier.intent_classifier import ROUTE_TO_APPENDIX
    
    appendix_code = ROUTE_TO_APPENDIX.get(route)
    questions = []
    
    if appendix_code:
        cur = db_conn.cursor()
        cur.execute("""
            SELECT qt.id, qt.paragraph_ref, qt.question_text,
                   qt.answer_type, qt.answer_options,
                   qt.fail_condition_description,
                   qt.sequence_stage, qt.confidence
            FROM question_templates qt
            JOIN rule_paragraphs rp 
              ON qt.paragraph_ref = rp.paragraph_ref
            WHERE rp.appendix_code = %s
              AND qt.sequence_stage != 'hard_gate'
              AND qt.paragraph_ref != 'SETTLE-2026'
            ORDER BY qt.sequence_stage DESC, qt.id ASC
        """, (appendix_code,))
        rows = cur.fetchall()
        cur.close()
        
        for row in rows:
            questions.append({
                "id": row[0],
                "paragraph_ref": row[1],
                "question_text": row[2],
                "answer_type": row[3],
                "answer_options": row[4],
                "fail_condition_description": row[5],
                "sequence_stage": row[6],
                "confidence": float(row[7]) if row[7] else 0.9,
                "heading_context": ""
            })
    
    # Apply B2 English override
    if "B2_ENGLISH_UPDATE" in flags_2026:
        for q in questions:
            if "english" in q.get("paragraph_ref", "").lower() or \
               "english" in q.get("question_text", "").lower():
                q["flag_note"] = "Updated to B2 as of 8 Jan 2026"
    
    # Add settlement question ONLY for work routes
    WORK_ROUTES = ["SKILLED_WORKER", "HPI", "SCALE_UP", 
                   "GLOBAL_TALENT"]
    if "SETTLEMENT_10YR" in flags_2026 and route in WORK_ROUTES:
        questions.append({
            "paragraph_ref": "SETTLE-2026",
            "question_text": "Are you planning to apply for settlement (Indefinite Leave to Remain) in the UK in the future?",
            "answer_type": "boolean",
            "answer_options": None,
            "fail_condition_description": None,
            "sequence_stage": "route_specific",
            "confidence": 0.99,
            "heading_context": "Settlement Planning",
            "flag_note": "Settlement now requires 10 years from April 2026"
        })
    
    # Fallback for routes with no questions in DB
    if len(questions) == 0:
        questions = [
            {
                "paragraph_ref": f"GEN-{route[:3]}-1",
                "question_text": "Do you have a valid passport with at least 6 months remaining validity?",
                "answer_type": "boolean",
                "answer_options": None,
                "fail_condition_description": "A valid passport is required.",
                "sequence_stage": "route_specific",
                "confidence": 0.99,
                "heading_context": "General Requirements"
            },
            {
                "paragraph_ref": f"GEN-{route[:3]}-2",
                "question_text": "Do you have sufficient funds to cover your entire stay in the UK?",
                "answer_type": "boolean",
                "answer_options": None,
                "fail_condition_description": "You must have sufficient funds without recourse to public funds.",
                "sequence_stage": "route_specific",
                "confidence": 0.98,
                "heading_context": "Financial Requirements"
            },
            {
                "paragraph_ref": f"GEN-{route[:3]}-3",
                "question_text": "Do you intend to leave the UK before your visa or permission expires?",
                "answer_type": "boolean",
                "answer_options": None,
                "fail_condition_description": "You must intend to leave before your permission expires.",
                "sequence_stage": "route_specific",
                "confidence": 0.98,
                "heading_context": "Intention to Leave"
            },
            {
                "paragraph_ref": f"GEN-{route[:3]}-4",
                "question_text": "Do you have proof of accommodation for your stay in the UK?",
                "answer_type": "boolean",
                "answer_options": None,
                "fail_condition_description": "You must have confirmed accommodation arrangements.",
                "sequence_stage": "route_specific",
                "confidence": 0.97,
                "heading_context": "Accommodation"
            },
        ]
    
    # Add numbering
    for i, q in enumerate(questions):
        q["question_number"] = i + 1
        q["total_questions"] = len(questions)
        q["progress_pct"] = round(((i + 1) / len(questions)) * 100, 1)
    
    return questions

def get_next_question(session_id: str, route: str, flags_2026: list, db_conn) -> dict | None:
    sequence = load_sequence(route, flags_2026, db_conn)
    
    cur = db_conn.cursor()
    cur.execute("SELECT paragraph_ref FROM session_answers WHERE session_id = %s", (session_id,))
    answered = {row[0] for row in cur.fetchall()}
    cur.close()
    
    for i, q in enumerate(sequence):
        if q["paragraph_ref"] not in answered:
            q["question_number"] = i + 1
            q["total_questions"] = len(sequence)
            q["progress_pct"] = round((i / len(sequence)) * 100, 2)
            return q
            
    return None

def apply_branch_rules(session_id: str, route: str, last_answer: dict, sequence: list, db_conn) -> list:
    try:
        constraint = load_constraint(last_answer["paragraph_ref"], db_conn)
    except Exception:
        return sequence
        
    field = constraint.get("field")
    rules = BRANCH_RULES.get(route, [])
    
    for r in rules:
        if r["trigger_field"] == field:
            parsed = last_answer.get("parsed_value")
            if parsed == r["trigger_value"] or str(parsed).lower() == str(r["trigger_value"]).lower():
                cur = db_conn.cursor()
                cur.execute(
                    """INSERT INTO session_answers
                       (session_id, paragraph_ref, question_text, answer, rule_result, fail_reason)
                       VALUES (%s, 'BRANCH-NOTE', %s, %s, 'FLAG', %s)""",
                    (session_id, r["description"], str(last_answer.get("user_answer")), r.get("action"))
                )
                db_conn.commit()
                cur.close()
                break
            
    return sequence

def initialize_session(user_input: str, nationality_iso: str, db_conn) -> dict:
    result = classify_intent(user_input, nationality_iso)
    if result.get("needs_clarification"):
        return {"status": "NEEDS_CLARIFICATION", "clarifying_question": result.get("clarifying_question")}
        
    cur = db_conn.cursor()
    cur.execute(
        """INSERT INTO sessions (route, nationality_iso, flags_2026, eta_required)
           VALUES (%s, %s, %s, %s) RETURNING id""",
        (result["route"], nationality_iso, json.dumps(result["flags_2026"]), result["eta_required"])
    )
    session_id = str(cur.fetchone()[0])
    db_conn.commit()
    cur.close()
    
    sequence = load_sequence(result["route"], result["flags_2026"], db_conn)
    
    return {
        "session_id": session_id,
        "status": "READY",
        "route": result["route"],
        "confidence": result["confidence"],
        "flags_2026": result["flags_2026"],
        "eta_required": result["eta_required"],
        "flag_warnings": result.get("flag_warnings", []),
        "hard_gate_questions": HARD_GATE_DEFINITIONS,
        "total_questions": len(sequence),
        "next_step": "hard_gate",
        "disclaimer": DISCLAIMER
    }

def process_hard_gate_answers(session_id: str, answers: dict, db_conn) -> dict:
    cur = db_conn.cursor()
    cur.execute("SELECT nationality_iso FROM sessions WHERE id = %s", (session_id,))
    row = cur.fetchone()
    if row:
        answers["nationality_iso"] = row[0]
        
    result = evaluate_hard_gates(answers, db_conn=db_conn)
    
    if result["result"] == "HARD_FAIL":
        cur.execute("UPDATE sessions SET status='hard_failed' WHERE id=%s", (session_id,))
        db_conn.commit()
        result["next_step"] = "ended"
    elif result["result"] == "FLAGGED":
        result["next_step"] = "solicitor_review"
    else:
        result["next_step"] = "questions"
        
    cur.close()
    return result

def complete_session(session_id: str, db_conn) -> dict:
    cur = db_conn.cursor()
    cur.execute("SELECT route FROM sessions WHERE id = %s", (session_id,))
    route = cur.fetchone()[0]
    cur.close()
    
    summary = get_session_summary(session_id, db_conn)
    checklist = get_checklist_for_route(route)
    save_session_result(session_id, summary, checklist, db_conn)
    
    summary["checklist"] = checklist
    return summary
