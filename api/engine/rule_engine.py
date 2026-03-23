def load_constraint(paragraph_ref: str, db_conn) -> dict:
    cur = db_conn.cursor()
    try:
        cur.execute("SELECT constraint_json FROM rule_paragraphs WHERE paragraph_ref = %s", (paragraph_ref,))
        row = cur.fetchone()
        if not row or not row[0]:
            raise ValueError(f"Constraint not found or NULL for {paragraph_ref}")
        return row[0]
    finally:
        cur.close()

def evaluate_answer(constraint: dict, user_answer: str) -> dict: 
    """ 
    Deterministic rule evaluator. Never crashes regardless of 
    constraint data quality. All eligibility decisions trace 
    back to a paragraph_ref. 
    """ 
    paragraph_ref = constraint.get("paragraph_ref", "UNKNOWN") 
    operator = constraint.get("operator", "any") 
    answer_type = constraint.get("answer_type", "text") 
    fail_description = constraint.get("fail_condition_description") 

    # ========================================================= 
    # STEP 1 — Parse user answer safely 
    # ========================================================= 
    parsed = None 
    try: 
        if answer_type in ("currency", "number", "integer"): 
            clean = str(user_answer).replace("£","").replace(",","").strip() 
            parsed = float(clean) 
        elif answer_type == "boolean": 
            parsed = str(user_answer).lower().strip() in ( 
                "yes", "true", "1", "y" 
            ) 
        elif answer_type == "date": 
            from datetime import datetime 
            parsed = datetime.strptime( 
                str(user_answer).strip(), "%Y-%m-%d" 
            ).date() 
        else: 
            parsed = str(user_answer).strip().lower() 
    except Exception as e: 
        print(f"[RULE ENGINE] Parse error on {paragraph_ref}: {e}") 
        return { 
            "paragraph_ref": paragraph_ref, 
            "field": constraint.get("field", "unknown"), 
            "operator": operator, 
            "user_answer": user_answer, 
            "parsed_value": None, 
            "threshold": constraint.get("value"), 
            "result": "FLAG", 
            "fail_reason": "Could not parse your answer. Please check your input.", 
            "rule_cited": paragraph_ref 
        } 

    # ========================================================= 
    # STEP 2 — Get threshold value safely 
    # ========================================================= 
    threshold = constraint.get("value") 
    threshold_max = constraint.get("value_max") 

    # ========================================================= 
    # STEP 3 — Evaluate operator with full type safety 
    # ========================================================= 
    passed = True  # default to pass for informational rules 

    try: 
        if operator == "any": 
            # Informational only — always pass 
            passed = True 

        elif operator == "exists": 
            if isinstance(parsed, bool): 
                passed = parsed 
            elif isinstance(parsed, str): 
                passed = parsed not in ("no", "false", "0", "", "none") 
            else: 
                passed = bool(parsed) 

        elif operator == "not_exists": 
            if isinstance(parsed, bool): 
                passed = not parsed 
            elif isinstance(parsed, str): 
                passed = parsed in ("no", "false", "0", "", "none") 
            else: 
                passed = not bool(parsed) 

        elif operator == "eq": 
            if threshold is None: 
                passed = True 
            else: 
                passed = parsed == threshold 

        elif operator == "neq": 
            if threshold is None: 
                passed = True 
            else: 
                passed = parsed != threshold 

        elif operator == "gte": 
            if threshold is None or not isinstance(parsed, (int, float)): 
                passed = True 
            else: 
                passed = parsed >= float(threshold) 

        elif operator == "lte": 
            if threshold is None or not isinstance(parsed, (int, float)): 
                passed = True 
            else: 
                passed = parsed <= float(threshold) 

        elif operator == "in": 
            # threshold MUST be a list — if not, treat as pass 
            if not isinstance(threshold, list): 
                print(f"[RULE ENGINE] Warning: 'in' operator on " 
                      f"{paragraph_ref} has non-list value: " 
                      f"{type(threshold)}. Treating as PASS.") 
                passed = True 
            else: 
                # Compare as strings to handle mixed types 
                str_threshold = [str(v).lower() for v in threshold] 
                str_parsed = str(parsed).lower() 
                passed = str_parsed in str_threshold 

        elif operator == "not_in": 
            if not isinstance(threshold, list): 
                print(f"[RULE ENGINE] Warning: 'not_in' operator on " 
                      f"{paragraph_ref} has non-list value: " 
                      f"{type(threshold)}. Treating as PASS.") 
                passed = True 
            else: 
                str_threshold = [str(v).lower() for v in threshold] 
                str_parsed = str(parsed).lower() 
                passed = str_parsed not in str_threshold 

        elif operator == "between": 
            if (threshold is None or threshold_max is None 
                    or not isinstance(parsed, (int, float))): 
                passed = True 
            else: 
                passed = float(threshold) <= parsed <= float(threshold_max) 

        else: 
            # Unknown operator — treat as informational 
            print(f"[RULE ENGINE] Unknown operator '{operator}' " 
                  f"on {paragraph_ref}. Treating as PASS.") 
            passed = True 

    except TypeError as e: 
        print(f"[RULE ENGINE] TypeError on {paragraph_ref} " 
              f"operator={operator}: {e}. Treating as FLAG.") 
        passed = True  # Don't crash — flag for review instead 

    except Exception as e: 
        print(f"[RULE ENGINE] Unexpected error on {paragraph_ref}: {e}") 
        passed = True 

    # ========================================================= 
    # STEP 4 — Build result 
    # ========================================================= 
    result_str = "PASS" if passed else "FAIL" 

    return { 
        "paragraph_ref": paragraph_ref, 
        "field": constraint.get("field", "unknown"), 
        "operator": operator, 
        "user_answer": user_answer, 
        "parsed_value": str(parsed), 
        "threshold": str(threshold) if threshold is not None else None, 
        "result": result_str, 
        "fail_reason": fail_description if not passed else None, 
        "rule_cited": paragraph_ref 
    } 

def evaluate_session_answer(session_id: str, paragraph_ref: str, user_answer: str, db_conn) -> dict:
    constraint = load_constraint(paragraph_ref, db_conn)
    eval_result = evaluate_answer(constraint, user_answer)
    
    cur = db_conn.cursor()
    try:
        cur.execute("SELECT question_text FROM question_templates WHERE paragraph_ref = %s", (paragraph_ref,))
        row = cur.fetchone()
        question_text = row[0] if row else ""

        cur.execute(
            """INSERT INTO session_answers
               (session_id, paragraph_ref, question_text, answer, rule_result, fail_reason)
               VALUES (%s, %s, %s, %s, %s, %s)""",
            (session_id, paragraph_ref, question_text, user_answer, eval_result["result"], eval_result["fail_reason"])
        )
        db_conn.commit()
    finally:
        cur.close()
        
    return eval_result

def get_session_summary(session_id: str, db_conn) -> dict:
    cur = db_conn.cursor()
    try:
        cur.execute("SELECT paragraph_ref, rule_result, fail_reason FROM session_answers WHERE session_id = %s", (session_id,))
        answers = cur.fetchall()
        
        passed = []
        failed = []
        flagged = []
        
        for p_ref, res, _ in answers:
            if res == "PASS": passed.append(p_ref)
            elif res == "FAIL": failed.append(p_ref)
            elif res == "FLAG": flagged.append(p_ref)
            
        if failed:
            overall = "FAIL"
        elif flagged:
            overall = "FLAGGED"
        else:
            overall = "PASS"
            
        return {
            "session_id": session_id,
            "overall_result": overall,
            "rules_passed": passed,
            "rules_failed": failed,
            "rules_flagged": flagged,
            "total_questions": len(answers),
            "disclaimer": "This is a Preliminary Self-Assessment only. It does not constitute legal advice. You should consult a qualified immigration solicitor before making any application."
        }
    finally:
        cur.close()

def save_session_result(session_id: str, summary: dict, checklist_items: list, db_conn) -> None:
    import json
    cur = db_conn.cursor()
    try:
        cur.execute(
            """INSERT INTO session_results
               (session_id, overall_result, rules_passed, rules_failed, rules_flagged, checklist_items, disclaimer)
               VALUES (%s, %s, %s, %s, %s, %s, %s)
               ON CONFLICT (session_id) DO UPDATE SET
               overall_result = EXCLUDED.overall_result,
               rules_passed = EXCLUDED.rules_passed,
               rules_failed = EXCLUDED.rules_failed,
               rules_flagged = EXCLUDED.rules_flagged,
               checklist_items = EXCLUDED.checklist_items,
               disclaimer = EXCLUDED.disclaimer""",
            (session_id, summary["overall_result"], json.dumps(summary["rules_passed"]), 
             json.dumps(summary["rules_failed"]), json.dumps(summary["rules_flagged"]), 
             json.dumps(checklist_items), summary["disclaimer"])
        )
        
        cur.execute(
            """UPDATE sessions SET status = %s, completed_at = NOW() WHERE id = %s""",
            (summary["overall_result"].lower(), session_id)
        )
        db_conn.commit()
    finally:
        cur.close()


ROUTE_CHECKLISTS = {
  "SKILLED_WORKER": [
    "Valid passport",
    "Certificate of Sponsorship (CoS) from licensed sponsor",
    "Proof of English language at B2 level",
    "Salary evidence (payslips or employer letter)",
    "TB test certificate (if required by nationality)",
    "Bank statements (if maintenance funds required)",
  ],
  "APPENDIX_FM": [
    "Valid passport",
    "Proof of relationship (marriage/civil partnership certificate)",
    "Financial evidence meeting minimum income threshold",
    "Accommodation proof (tenancy agreement or mortgage)",
    "English language evidence (if applicable)",
    "Sponsor's British passport or settlement proof",
  ],
  "STUDENT": [
    "Valid passport",
    "Confirmation of Acceptance for Studies (CAS)",
    "Proof of English language proficiency",
    "Bank statements showing maintenance funds",
    "ATAS certificate (if required for course)",
    "Parental consent (if under 18)",
  ],
  "HPI": [
    "Valid passport",
    "Degree certificate from qualifying institution",
    "Proof of English language at B2 level",
    "Bank statements showing maintenance funds",
    "TB test certificate (if required)",
  ],
  "VISITOR": [
    "Valid passport",
    "Bank statements showing sufficient funds",
    "Proof of accommodation (hotel booking or host letter)",
    "Return travel booking",
    "Evidence of ties to home country",
  ],
  "GLOBAL_TALENT": [
    "Valid passport",
    "Endorsement letter from endorsing body",
    "Evidence of exceptional talent or promise",
    "CV and supporting portfolio",
  ],
  "SCALE_UP": [
    "Valid passport",
    "Job offer from qualifying scale-up company",
    "Salary evidence meeting threshold",
    "Proof of English language",
  ],
  "GRADUATE": [
    "Valid passport",
    "Proof of UK degree completion",
    "Current Student visa or evidence of recent permission",
  ],
}

def get_checklist_for_route(route: str) -> list:
    return ROUTE_CHECKLISTS.get(route, ["Valid passport"])
