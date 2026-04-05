import json
from db.connection import get_connection

SKILLED_WORKER_QUESTIONS = [
  # Stage 1: Validity
  {
    "paragraph_ref": "SW-1.1",
    "appendix_code": "SKILLED_WORKER",
    "sequence_stage": "route_specific",
    "question_text": "Do you have a Certificate of Sponsorship (CoS) from a UK Home Office licensed sponsor?",
    "answer_type": "boolean",
    "answer_options": None,
    "fail_condition_description": "A valid CoS from a licensed sponsor is mandatory for the Skilled Worker route.",
    "plain_english_hint": "A CoS is a digital record from your employer confirming your job offer.",
    "constraint_json": {"field": "has_cos", "operator": "exists", "value": None},
    "is_hard_gate": True,
    "confidence": 0.98
  },
  {
    "paragraph_ref": "SW-1.2",
    "appendix_code": "SKILLED_WORKER",
    "sequence_stage": "route_specific",
    "question_text": "Is your Certificate of Sponsorship less than 3 months old?",
    "answer_type": "boolean",
    "answer_options": None,
    "fail_condition_description": "The CoS must have been issued within 3 months of your application date.",
    "constraint_json": {"field": "cos_within_3_months", "operator": "eq", "value": True},
    "confidence": 0.97
  },
  {
    "paragraph_ref": "SW-1.3",
    "appendix_code": "SKILLED_WORKER",
    "sequence_stage": "route_specific",
    "question_text": "Are you aged 18 or over?",
    "answer_type": "boolean",
    "answer_options": None,
    "fail_condition_description": "Applicants must be at least 18 years old.",
    "constraint_json": {"field": "age_18_or_over", "operator": "eq", "value": True},
    "confidence": 0.99
  },
  # Stage 2: Salary
  {
    "paragraph_ref": "SW-14.1",
    "appendix_code": "SKILLED_WORKER",
    "sequence_stage": "route_specific",
    "question_text": "What is your annual salary as stated on your Certificate of Sponsorship (in £)?",
    "answer_type": "currency",
    "answer_options": None,
    "fail_condition_description": "Your salary must meet the minimum threshold of £26,200 per year or the going rate for your occupation, whichever is higher.",
    "constraint_json": {"field": "salary_annual_gbp", "operator": "gte", "value": 26200},
    "confidence": 0.98
  },
  {
    "paragraph_ref": "SW-14.2",
    "appendix_code": "SKILLED_WORKER",
    "sequence_stage": "route_specific",
    "question_text": "Do you hold a PhD that is relevant to your job?",
    "answer_type": "boolean",
    "answer_options": None,
    "fail_condition_description": None,
    "constraint_json": {"field": "has_phd", "operator": "any", "value": None},
    "confidence": 0.95
  },
  {
    "paragraph_ref": "SW-14.3",
    "appendix_code": "SKILLED_WORKER",
    "sequence_stage": "route_specific",
    "question_text": "Is your job in a shortage occupation listed on the Immigration Salary List?",
    "answer_type": "boolean",
    "answer_options": None,
    "fail_condition_description": None,
    "constraint_json": {"field": "is_shortage_occupation", "operator": "any", "value": None},
    "confidence": 0.93
  },
  {
    "paragraph_ref": "SW-14.4",
    "appendix_code": "SKILLED_WORKER",
    "sequence_stage": "route_specific",
    "question_text": "Is your job in health or social care?",
    "answer_type": "boolean",
    "answer_options": None,
    "fail_condition_description": None,
    "constraint_json": {"field": "is_health_care_worker", "operator": "any", "value": None},
    "confidence": 0.95
  },
  # Stage 3: English Language (2026 B2 requirement)
  {
    "paragraph_ref": "SW-ENG.1",
    "appendix_code": "SKILLED_WORKER",
    "sequence_stage": "route_specific",
    "question_text": "Do you meet the B2 English language requirement? (e.g. IELTS 5.5 overall, or equivalent SELT)",
    "answer_type": "boolean",
    "answer_options": None,
    "fail_condition_description": "Skilled Workers must demonstrate English at B2 level as of 8 January 2026. B1 is no longer sufficient.",
    "constraint_json": {"field": "english_level_b2", "operator": "eq", "value": True},
    "confidence": 0.97
  },
  {
    "paragraph_ref": "SW-ENG.2",
    "appendix_code": "SKILLED_WORKER",
    "sequence_stage": "route_specific",
    "question_text": "Which English language evidence do you have?",
    "answer_type": "select",
    "answer_options": [
      "IELTS SELT (minimum 5.5 overall)",
      "Degree taught in English",
      "Citizen of majority English-speaking country",
      "Other approved SELT",
      "None of the above"
    ],
    "fail_condition_description": "You must provide an approved form of English language evidence at B2 level.",
    "constraint_json": {"field": "english_evidence_type", "operator": "neq", "value": "None of the above"},
    "confidence": 0.95
  },
  # Stage 4: Occupation
  {
    "paragraph_ref": "SW-5.1",
    "appendix_code": "SKILLED_WORKER",
    "sequence_stage": "route_specific",
    "question_text": "Is your job listed as an eligible occupation (RQF Level 3 or above)?",
    "answer_type": "boolean",
    "answer_options": None,
    "fail_condition_description": "The job must be at RQF Level 3 or above and appear on the list of eligible occupations.",
    "constraint_json": {"field": "job_eligible_occupation", "operator": "eq", "value": True},
    "confidence": 0.96
  },
  {
    "paragraph_ref": "SW-5.2",
    "appendix_code": "SKILLED_WORKER",
    "sequence_stage": "route_specific",
    "question_text": "What is the SOC 2020 occupation code for your job?",
    "answer_type": "text",
    "answer_options": None,
    "fail_condition_description": "The occupation code must match an eligible Skilled Worker occupation.",
    "constraint_json": {"field": "soc_code", "operator": "exists", "value": None},
    "confidence": 0.90
  },
  # Stage 5: Sponsor
  {
    "paragraph_ref": "SW-4.1",
    "appendix_code": "SKILLED_WORKER",
    "sequence_stage": "route_specific",
    "question_text": "Is your employer on the Home Office Register of Licensed Sponsors?",
    "answer_type": "boolean",
    "answer_options": None,
    "fail_condition_description": "Your employer must hold a valid Skilled Worker sponsor licence.",
    "constraint_json": {"field": "sponsor_licensed", "operator": "eq", "value": True},
    "confidence": 0.99
  },
  # Stage 6: Financial
  {
    "paragraph_ref": "SW-FIN.1",
    "appendix_code": "SKILLED_WORKER",
    "sequence_stage": "route_specific",
    "question_text": "Have you been sponsored by this employer for at least 3 months and they are covering your maintenance?",
    "answer_type": "boolean",
    "answer_options": None,
    "fail_condition_description": None,
    "constraint_json": {"field": "sponsor_covers_maintenance", "operator": "any", "value": None},
    "confidence": 0.92
  },
  {
    "paragraph_ref": "SW-FIN.2",
    "appendix_code": "SKILLED_WORKER",
    "sequence_stage": "route_specific",
    "question_text": "If maintenance funds are required, do you have at least £1,270 in your bank account held for 28 consecutive days?",
    "answer_type": "boolean",
    "answer_options": None,
    "fail_condition_description": "You must show £1,270 in funds held for 28 consecutive days unless your sponsor certifies maintenance.",
    "constraint_json": {"field": "maintenance_funds_met", "operator": "eq", "value": True},
    "confidence": 0.97
  },
  # Stage 7: TB Test
  {
    "paragraph_ref": "SW-TB.1",
    "appendix_code": "SKILLED_WORKER",
    "sequence_stage": "route_specific",
    "question_text": "If required for your nationality, do you have a valid TB test certificate from an approved clinic?",
    "answer_type": "boolean",
    "answer_options": None,
    "fail_condition_description": "Applicants from certain countries must provide a valid TB test certificate.",
    "constraint_json": {"field": "tb_certificate_if_required", "operator": "eq", "value": True},
    "confidence": 0.94
  },
  # Stage 8: Settlement planning (2026 flag)
  {
    "paragraph_ref": "SETTLE-2026",
    "appendix_code": "SKILLED_WORKER",
    "sequence_stage": "route_specific",
    "question_text": "Are you planning to apply for settlement (Indefinite Leave to Remain) in the UK?",
    "answer_type": "boolean",
    "answer_options": None,
    "fail_condition_description": None,
    "constraint_json": {"field": "planning_settlement", "operator": "any", "value": None},
    "confidence": 0.99
  },
]

APPENDIX_FM_QUESTIONS = [
  # Stage 1: Relationship
  {
    "paragraph_ref": "FM-GEN.1.1",
    "appendix_code": "APPENDIX_FM",
    "sequence_stage": "route_specific",
    "question_text": "What is your relationship to your UK-based sponsor?",
    "answer_type": "select",
    "answer_options": [
      "Spouse or civil partner",
      "Unmarried partner (2+ years together)",
      "Fiancé(e) or proposed civil partner",
      "Child under 18",
      "Adult dependent relative"
    ],
    "fail_condition_description": "You must have a qualifying relationship with a British citizen or person settled in the UK.",
    "constraint_json": {"field": "relationship_type", "operator": "in",
      "value": ["Spouse or civil partner","Unmarried partner (2+ years together)",
                "Fiancé(e) or proposed civil partner","Child under 18",
                "Adult dependent relative"]},
    "confidence": 0.98
  },
  {
    "paragraph_ref": "FM-ECP.2.1",
    "appendix_code": "APPENDIX_FM",
    "sequence_stage": "route_specific",
    "question_text": "Is your UK sponsor a British citizen, settled person, or refugee with protection status?",
    "answer_type": "boolean",
    "answer_options": None,
    "fail_condition_description": "Your sponsor must be a British citizen, settled in the UK, or hold refugee/humanitarian protection.",
    "constraint_json": {"field": "sponsor_settled_or_british", "operator": "eq", "value": True},
    "confidence": 0.99
  },
  {
    "paragraph_ref": "FM-ECP.2.2",
    "appendix_code": "APPENDIX_FM",
    "sequence_stage": "route_specific",
    "question_text": "Have you and your partner met in person?",
    "answer_type": "boolean",
    "answer_options": None,
    "fail_condition_description": "You and your partner must have met in person.",
    "constraint_json": {"field": "met_in_person", "operator": "eq", "value": True},
    "confidence": 0.98
  },
  {
    "paragraph_ref": "FM-ECP.2.3",
    "appendix_code": "APPENDIX_FM",
    "sequence_stage": "route_specific",
    "question_text": "Is your relationship genuine and subsisting?",
    "answer_type": "boolean",
    "answer_options": None,
    "fail_condition_description": "The relationship must be genuine, subsisting, and you must intend to live together permanently in the UK.",
    "constraint_json": {"field": "relationship_genuine", "operator": "eq", "value": True},
    "confidence": 0.97
  },
  # Stage 2: Financial requirement
  {
    "paragraph_ref": "FM-E-ECP.3.1",
    "appendix_code": "APPENDIX_FM",
    "sequence_stage": "route_specific",
    "question_text": "What is your UK sponsor's annual gross income (before tax) in £?",
    "answer_type": "currency",
    "answer_options": None,
    "fail_condition_description": "The UK sponsor must meet the minimum income threshold of £29,000 per year (2024 threshold).",
    "constraint_json": {"field": "sponsor_income_gbp", "operator": "gte", "value": 29000},
    "confidence": 0.97
  },
  {
    "paragraph_ref": "FM-E-ECP.3.2",
    "appendix_code": "APPENDIX_FM",
    "sequence_stage": "route_specific",
    "question_text": "Has your sponsor been employed or self-employed for at least 6 months?",
    "answer_type": "boolean",
    "answer_options": None,
    "fail_condition_description": "Income from employment must be from a job held for at least 6 months to be counted towards the financial requirement.",
    "constraint_json": {"field": "sponsor_employed_6_months", "operator": "eq", "value": True},
    "confidence": 0.95
  },
  {
    "paragraph_ref": "FM-E-ECP.3.3",
    "appendix_code": "APPENDIX_FM",
    "sequence_stage": "route_specific",
    "question_text": "Do you have evidence of your sponsor's income? (payslips, bank statements, employer letter)",
    "answer_type": "boolean",
    "answer_options": None,
    "fail_condition_description": "You must provide documentary evidence of the sponsor's income.",
    "constraint_json": {"field": "sponsor_income_evidence", "operator": "eq", "value": True},
    "confidence": 0.97
  },
  # Stage 3: Accommodation
  {
    "paragraph_ref": "FM-E-ECP.4.1",
    "appendix_code": "APPENDIX_FM",
    "sequence_stage": "route_specific",
    "question_text": "Do you have adequate accommodation in the UK that is not overcrowded?",
    "answer_type": "boolean",
    "answer_options": None,
    "fail_condition_description": "There must be adequate accommodation available without recourse to public funds.",
    "constraint_json": {"field": "adequate_accommodation", "operator": "eq", "value": True},
    "confidence": 0.96
  },
  {
    "paragraph_ref": "FM-E-ECP.4.2",
    "appendix_code": "APPENDIX_FM",
    "sequence_stage": "route_specific",
    "question_text": "What type of accommodation evidence do you have?",
    "answer_type": "select",
    "answer_options": [
      "Tenancy agreement",
      "Mortgage statement",
      "Land registry proof of ownership",
      "Letter from landlord",
      "None of the above"
    ],
    "fail_condition_description": "You must provide evidence of suitable accommodation.",
    "constraint_json": {"field": "accommodation_evidence_type", "operator": "neq",
                        "value": "None of the above"},
    "confidence": 0.95
  },
  # Stage 4: English Language
  {
    "paragraph_ref": "FM-ECP.4.1",
    "appendix_code": "APPENDIX_FM",
    "sequence_stage": "route_specific",
    "question_text": "Do you meet the English language requirement for a spouse/partner visa (A1 level minimum)?",
    "answer_type": "boolean",
    "answer_options": None,
    "fail_condition_description": "Spouse/partner applicants must demonstrate English at A1 level minimum.",
    "constraint_json": {"field": "english_level_a1", "operator": "eq", "value": True},
    "confidence": 0.95
  },
  {
    "paragraph_ref": "FM-ECP.4.2",
    "appendix_code": "APPENDIX_FM",
    "sequence_stage": "route_specific",
    "question_text": "Are you a national of a majority English-speaking country?",
    "answer_type": "boolean",
    "answer_options": None,
    "fail_condition_description": None,
    "constraint_json": {"field": "majority_english_country", "operator": "any", "value": None},
    "confidence": 0.97
  },
  # Stage 5: No recourse to public funds
  {
    "paragraph_ref": "FM-GEN.1.11",
    "appendix_code": "APPENDIX_FM",
    "sequence_stage": "route_specific",
    "question_text": "Do you understand that you will have No Recourse to Public Funds (NRPF) initially?",
    "answer_type": "boolean",
    "answer_options": None,
    "fail_condition_description": "Applicants must acknowledge the No Recourse to Public Funds condition.",
    "constraint_json": {"field": "accepts_nrpf", "operator": "eq", "value": True},
    "confidence": 0.96
  },
]

def seed_question_sequences(db_conn) -> dict:
    """
    Seed full question sequences for SKILLED_WORKER and APPENDIX_FM.
    Uses INSERT ON CONFLICT (paragraph_ref) DO UPDATE to be idempotent.
    All questions seeded with verified=FALSE.
    """
    cur = db_conn.cursor()
    
    try:
        cur.execute("""
            ALTER TABLE question_templates
            DROP CONSTRAINT IF EXISTS uq_qt_paragraph_ref;
            ALTER TABLE question_templates
            ADD CONSTRAINT uq_qt_paragraph_ref UNIQUE (paragraph_ref);
        """)
        cur.execute("""
            ALTER TABLE rule_paragraphs
            DROP CONSTRAINT IF EXISTS uq_rp_paragraph_ref;
            ALTER TABLE rule_paragraphs
            ADD CONSTRAINT uq_rp_paragraph_ref UNIQUE (paragraph_ref);
        """)
        db_conn.commit()
    except Exception as e:
        db_conn.rollback()
        print(f"Warning: could not add unique constraints: {e}")
    
    sw_count = 0
    fm_count = 0

    all_questions = (
        [(q, "SKILLED_WORKER") for q in SKILLED_WORKER_QUESTIONS] +
        [(q, "APPENDIX_FM") for q in APPENDIX_FM_QUESTIONS]
    )

    for q, route in all_questions:
        # Upsert into rule_paragraphs first
        cur.execute("""
            INSERT INTO rule_paragraphs
              (appendix_code, paragraph_ref, raw_text,
               constraint_json, is_hard_gate, verified)
            VALUES (%s, %s, %s, %s, %s, FALSE)
            ON CONFLICT (paragraph_ref) DO UPDATE SET
              constraint_json = EXCLUDED.constraint_json,
              is_hard_gate = EXCLUDED.is_hard_gate
        """, (
            q["appendix_code"],
            q["paragraph_ref"],
            q["question_text"],
            json.dumps(q["constraint_json"]),
            q.get("is_hard_gate", False)
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
            q.get("plain_english_hint"),
            q["confidence"]
        ))

        if route == "SKILLED_WORKER":
            sw_count += 1
        else:
            fm_count += 1

    db_conn.commit()
    cur.close()

    return {
        "skilled_worker_questions": sw_count,
        "appendix_fm_questions": fm_count,
        "total": sw_count + fm_count
    }

if __name__ == "__main__":
    conn = get_connection()
    print("Seeding question sequences...")
    result = seed_question_sequences(conn)
    print(f'''
  Skilled Worker questions: {result['skilled_worker_questions']}
  Appendix FM questions:    {result['appendix_fm_questions']}
  Total seeded:             {result['total']}
  All verified=FALSE ✅
    ''')
    conn.close()
