from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from api.models.schemas import (
    NextQuestionResponse,
    SubmitAnswerRequest, SubmitAnswerResponse,
    SessionResultResponse, CheckSummary
)
from api.utils import strip_internal_refs, get_route_display_name
from api.engine.sequence import (
    get_next_question, complete_session
)
from api.engine.rule_engine import (
    evaluate_session_answer, get_checklist_for_route
)
from db.connection import get_connection

router = APIRouter()

def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()

@router.get("/next/{session_id}", 
            response_model=NextQuestionResponse)
def get_next(session_id: str, db=Depends(get_db)):
    """
    Returns the next unanswered question for this session.
    Returns 204 if all questions are answered.
    """
    cur = db.cursor()
    cur.execute(
        "SELECT route, flags_2026 FROM sessions WHERE id = %s",
        (session_id,)
    )
    row = cur.fetchone()
    cur.close()
    
    if not row:
        raise HTTPException(status_code=404,
                           detail="Session not found")
    
    route, flags_2026 = row
    flags = flags_2026 if flags_2026 else []
    
    question = get_next_question(
        session_id=session_id,
        route=route,
        flags_2026=flags,
        db_conn=db
    )
    
    if question is None:
        return JSONResponse(
            status_code=200,
            content={"complete": True, "next_step": "result"}
        )
    
    return NextQuestionResponse(
        session_id=session_id,
        question_number=question["question_number"],
        total_questions=question["total_questions"],
        paragraph_ref=strip_internal_refs(question["paragraph_ref"]),
        ref_id=question["paragraph_ref"],
        question_text=question["question_text"],
        answer_type=question.get("answer_type", "text"),
        answer_options=question.get("answer_options"),
        heading_context=question.get("heading_context"),
        disclaimer=(
            "This is a Preliminary Self-Assessment only. "
            "It does not constitute legal advice."
        )
    )

@router.post("/answer", response_model=SubmitAnswerResponse)
def submit_answer(request: SubmitAnswerRequest,
                  db=Depends(get_db)):
    """
    Submit answer to a question.
    Evaluates against Rule Engine deterministically.
    Returns PASS, FAIL, or FLAG with rule cited.
    """
    try:
        # Prefer ref_id if provided
        ref = request.ref_id if request.ref_id else request.paragraph_ref
        
        # Bug 6 — MEDIUM: "I don't know" answer for SOC occupation code is silently passed
        # The user says "SOC 2020 occupation code question", but let's apply it generally
        # if the answer is "I don't know" or equivalent.
        is_unknown = request.answer.lower().strip() in ["i don't know", "unknown", "unsure", "not sure"]
        
        if is_unknown:
            # We bypass the rule engine and record a FLAG manually
            cur = db.cursor()
            cur.execute("SELECT question_text FROM question_templates WHERE paragraph_ref = %s", (ref,))
            q_row = cur.fetchone()
            question_text = q_row[0] if q_row else "Unknown Question"
            
            fail_reason = "We could not verify your occupation code. A solicitor should confirm this before you apply." if "soc" in ref.lower() or "occupation" in question_text.lower() else "User was unsure. Review required."
            
            cur.execute(
                """INSERT INTO session_answers
                   (session_id, paragraph_ref, question_text, answer, rule_result, fail_reason)
                   VALUES (%s, %s, %s, %s, 'FLAG', %s)""",
                (request.session_id, ref, question_text, request.answer, fail_reason)
            )
            db.commit()
            cur.close()
            result = {"result": "FLAG", "fail_reason": fail_reason}
        
        else:
            result = evaluate_session_answer(
                session_id=request.session_id,
                paragraph_ref=ref,
                user_answer=request.answer,
                db_conn=db
            )
            
            # Bug 3 — CRITICAL: Salary FAIL has no explanation or threshold shown
            # If it's a salary question and it failed, update the reason.
            if result["result"] == "FAIL" and ("salary" in ref.lower() or "SW-14.1" in ref):
                # Get the threshold from the constraint
                from api.engine.rule_engine import load_constraint
                constraint = load_constraint(ref, db)
                threshold = constraint.get("value")
                human_reason = f"The minimum salary for this role is £{int(threshold):,}. Your Certificate of Sponsorship states £{request.answer}."
                
                cur = db.cursor()
                cur.execute(
                    "UPDATE session_answers SET fail_reason = %s WHERE session_id = %s AND paragraph_ref = %s",
                    (human_reason, request.session_id, ref)
                )
                db.commit()
                cur.close()
                result["fail_reason"] = human_reason

        # Bug 2 — CRITICAL: Hard gate FAIL does not stop the session
        # Check if the current rule is marked as a hard gate in rule_paragraphs
        cur = db.cursor()
        cur.execute("SELECT is_hard_gate FROM rule_paragraphs WHERE paragraph_ref = %s", (ref,))
        p_row = cur.fetchone()
        is_hard_gate = p_row[0] if p_row else False
        
        if result["result"] == "FAIL" and is_hard_gate:
            # Halt session immediately
            complete_session(request.session_id, db)
            next_step = "complete"
        else:
            cur = db.cursor()
            cur.execute(
                "SELECT route, flags_2026 FROM sessions WHERE id=%s",
                (request.session_id,)
            )
            row = cur.fetchone()
            
            route = row[0] if row else "UNKNOWN"
            flags = row[1] if row else []
            
            next_q = get_next_question(
                session_id=request.session_id,
                route=route,
                flags_2026=flags or [],
                db_conn=db
            )
            
            next_step = "next_question" if next_q else "complete"
            
            if next_step == "complete":
                complete_session(request.session_id, db)
            cur.close()
        
        return SubmitAnswerResponse(
            session_id=request.session_id,
            paragraph_ref=strip_internal_refs(ref),
            ref_id=ref,
            result=result["result"],
            fail_reason=strip_internal_refs(result.get("fail_reason", "")),
            next_step=next_step,
            disclaimer=(
                "This is a Preliminary Self-Assessment only. "
                "It does not constitute legal advice."
            )
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/result/{session_id}",
            response_model=SessionResultResponse)
def get_result(session_id: str, db=Depends(get_db)):
    """
    Get the final eligibility result for a completed session.
    """
    cur = db.cursor()
    cur.execute("""
        SELECT overall_result, checklist_items, disclaimer
        FROM session_results
        WHERE session_id = %s
    """, (session_id,))
    row = cur.fetchone()
    
    if not row:
        cur.close()
        raise HTTPException(
            status_code=404,
            detail="Result not found. Session may not be complete."
        )
    
    overall_result, checklist_items, disclaimer = row
    
    cur.execute("""
        SELECT question_text, answer, rule_result, fail_reason
        FROM session_answers
        WHERE session_id = %s
        ORDER BY created_at ASC
    """, (session_id,))
    answers = cur.fetchall()
    cur.close()
    
    summary = [
        CheckSummary(
            question=strip_internal_refs(row[0]),
            answer=strip_internal_refs(row[1]),
            result=row[2],
            reason=strip_internal_refs(row[3]) if row[2] == 'FAIL' else "You meet this requirement."
        )
        for row in answers
    ]
    
    return SessionResultResponse(
        session_id=session_id,
        overall_result=overall_result,
        rules_passed=[], # Deprecated in favor of summary
        rules_failed=[], # Deprecated in favor of summary
        rules_flagged=[], # Deprecated in favor of summary
        summary=summary,
        checklist_items=checklist_items or [],
        disclaimer=disclaimer
    )
