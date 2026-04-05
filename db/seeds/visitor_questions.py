import json
from db.connection import get_connection

VISITOR_QUESTIONS = [
    {
        "paragraph_ref": "GEN-VIS-1",
        "appendix_code": "APPENDIX_VISITOR",
        "sequence_stage": "route_specific",
        "question_text": "What is the primary purpose of your visit to the UK?",
        "answer_type": "select",
        "answer_options": ["Tourism", "Business", "Study (short-term)", "Medical Treatment", "Transit", "Other"],
        "fail_condition_description": "Your visit purpose must fall under permitted visitor activities.",
        "plain_english_hint": "Select the main reason you want to come to the UK.",
        "constraint_json": {"field": "visit_purpose", "operator": "in", "value": ["Tourism", "Business", "Study (short-term)", "Medical Treatment", "Transit"]},
        "confidence": 0.99
    },
    {
        "paragraph_ref": "GEN-VIS-2",
        "appendix_code": "APPENDIX_VISITOR",
        "sequence_stage": "route_specific",
        "question_text": "How long do you intend to stay in the UK (in days)?",
        "answer_type": "number",
        "answer_options": None,
        "fail_condition_description": "Standard visitor stays are generally limited to 6 months (180 days).",
        "plain_english_hint": "Enter the total number of days you plan to be in the UK.",
        "constraint_json": {"field": "stay_duration_days", "operator": "lte", "value": 180},
        "confidence": 0.98
    },

    {
        "paragraph_ref": "GEN-VIS-4",
        "appendix_code": "APPENDIX_VISITOR",
        "sequence_stage": "route_specific",
        "question_text": "If you are from an ETA-eligible country, do you have a valid Electronic Travel Authorisation (ETA)?",
        "answer_type": "boolean",
        "answer_options": None,
        "fail_condition_description": "As of 2025/2026, many non-visa nationals require a valid ETA to travel to the UK.",
        "plain_english_hint": "An ETA is an Electronic Travel Authorisation, required for some visitors.",
        "constraint_json": {"field": "has_valid_eta", "operator": "eq", "value": True},
        "confidence": 0.96
    },
    {
        "paragraph_ref": "GEN-VIS-5",
        "appendix_code": "APPENDIX_VISITOR",
        "sequence_stage": "route_specific",
        "question_text": "Do you intend to leave the UK at the end of your visit?",
        "answer_type": "boolean",
        "answer_options": None,
        "fail_condition_description": "You must satisfy the decision-maker that you are a genuine visitor who will leave at the end of your stay.",
        "plain_english_hint": "Confirm that you will leave the UK when your visit is over.",
        "constraint_json": {"field": "intends_to_leave", "operator": "eq", "value": True},
        "confidence": 0.99
    },
    {
        "paragraph_ref": "GEN-VIS-6",
        "appendix_code": "APPENDIX_VISITOR",
        "sequence_stage": "route_specific",
        "question_text": "Will you undertake any prohibited activities, such as paid work or frequent/successive visits to live in the UK?",
        "answer_type": "boolean",
        "answer_options": None,
        "fail_condition_description": "Visitors are prohibited from working or using successive visits to live in the UK.",
        "plain_english_hint": "Confirm you will not work or try to live in the UK through frequent visits.",
        "constraint_json": {"field": "undertakes_prohibited_activity", "operator": "eq", "value": False},
        "confidence": 0.98
    },
    {
        "paragraph_ref": "GEN-VIS-7",
        "appendix_code": "APPENDIX_VISITOR",
        "sequence_stage": "route_specific",
        "question_text": "Do you have sufficient funds to cover all reasonable costs of your visit without working or accessing public funds?",
        "answer_type": "boolean",
        "answer_options": None,
        "fail_condition_description": "You must have enough money to support yourself during your stay.",
        "plain_english_hint": "Confirm you have your own money for your trip.",
        "constraint_json": {"field": "has_sufficient_funds", "operator": "eq", "value": True},
        "confidence": 0.97
    },
    {
        "paragraph_ref": "GEN-VIS-8",
        "appendix_code": "APPENDIX_VISITOR",
        "sequence_stage": "route_specific",
        "question_text": "What evidence of funds do you have?",
        "answer_type": "select",
        "answer_options": ["Bank statements", "Sponsorship letter", "Payslips", "Other approved evidence", "None"],
        "fail_condition_description": "You must provide evidence of your financial circumstances.",
        "plain_english_hint": "Choose the type of financial documents you can provide.",
        "constraint_json": {"field": "funds_evidence_type", "operator": "neq", "value": "None"},
        "confidence": 0.95
    },
    {
        "paragraph_ref": "GEN-VIS-9",
        "appendix_code": "APPENDIX_VISITOR",
        "sequence_stage": "route_specific",
        "question_text": "Do you have strong ties to your home country (e.g. job, family, property) that will encourage you to return?",
        "answer_type": "boolean",
        "answer_options": None,
        "fail_condition_description": "Strong ties to your home country are essential to demonstrate genuine intention to leave.",
        "plain_english_hint": "This helps show that you are likely to return home after your visit.",
        "constraint_json": {"field": "has_home_ties", "operator": "eq", "value": True},
        "confidence": 0.96
    },
    {
        "paragraph_ref": "GEN-VIS-10",
        "appendix_code": "APPENDIX_VISITOR",
        "sequence_stage": "route_specific",
        "question_text": "Do you have confirmed accommodation for the duration of your stay in the UK?",
        "answer_type": "boolean",
        "answer_options": None,
        "fail_condition_description": "You must have suitable accommodation for your visit.",
        "plain_english_hint": "Confirm you have a place to stay during your visit.",
        "constraint_json": {"field": "has_accommodation", "operator": "eq", "value": True},
        "confidence": 0.94
    },
    {
        "paragraph_ref": "GEN-VIS-11",
        "appendix_code": "APPENDIX_VISITOR",
        "sequence_stage": "route_specific",
        "question_text": "Have you complied with the conditions of any previous UK visas?",
        "answer_type": "boolean",
        "answer_options": None,
        "fail_condition_description": "Previous non-compliance with UK immigration laws can lead to refusal.",
        "plain_english_hint": "This refers to any past issues with UK immigration authorities.",
        "constraint_json": {"field": "previous_compliance", "operator": "eq", "value": True},
        "confidence": 0.98
    },
    {
        "paragraph_ref": "GEN-VIS-12",
        "appendix_code": "APPENDIX_VISITOR",
        "sequence_stage": "route_specific",
        "question_text": "Is your passport or travel document valid for the entire duration of your stay?",
        "answer_type": "boolean",
        "answer_options": None,
        "fail_condition_description": "You must hold a valid travel document.",
        "plain_english_hint": "Ensure your passport is valid for your entire trip.",
        "constraint_json": {"field": "passport_valid", "operator": "eq", "value": True},
        "confidence": 0.99
    }
]

def seed_visitor_questions(db_conn):
    cur = db_conn.cursor()
    
    # Ensure APPENDIX_VISITOR exists in appendices table
    cur.execute("""
        INSERT INTO appendices (code, url, priority)
        VALUES ('APPENDIX_VISITOR', 'https://www.gov.uk/guidance/immigration-rules/immigration-rules-appendix-v-visitor-rules', 23)
        ON CONFLICT (code) DO NOTHING;
    """)
    
    count = 0
    for q in VISITOR_QUESTIONS:
        # Upsert into rule_paragraphs
        cur.execute("""
            INSERT INTO rule_paragraphs 
              (appendix_code, paragraph_ref, raw_text, constraint_json, verified)
            VALUES (%s, %s, %s, %s, FALSE)
            ON CONFLICT (paragraph_ref) DO UPDATE SET
              constraint_json = EXCLUDED.constraint_json
        """, (
            q["appendix_code"],
            q["paragraph_ref"],
            q["question_text"],
            json.dumps(q["constraint_json"])
        ))

        # Upsert into question_templates
        cur.execute("""
            INSERT INTO question_templates
              (paragraph_ref, appendix_code, sequence_stage,
               question_text, answer_type, answer_options,
               fail_condition_description, plain_english_hint, confidence, verified)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, FALSE)
            ON CONFLICT (paragraph_ref) DO UPDATE SET
              question_text = EXCLUDED.question_text,
              answer_type = EXCLUDED.answer_type,
              answer_options = EXCLUDED.answer_options,
              confidence = EXCLUDED.confidence,
              plain_english_hint = EXCLUDED.plain_english_hint
        """, (
            q["paragraph_ref"],
            q["appendix_code"],
            q["sequence_stage"],
            q["question_text"],
            q["answer_type"],
            json.dumps(q["answer_options"]) if q["answer_options"] else None,
            q["fail_condition_description"],
            q["plain_english_hint"],
            q["confidence"]
        ))
        count += 1

    db_conn.commit()
    cur.close()
    return count

if __name__ == "__main__":
    conn = get_connection()
    print("Seeding Visitor questions...")
    total = seed_visitor_questions(conn)
    print(f"Total Visitor questions seeded: {total}")
    print("All verified=FALSE ✅")
    conn.close()
