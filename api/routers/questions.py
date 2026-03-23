from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse
from api.models.schemas import (
    NextQuestionResponse,
    SubmitAnswerRequest, SubmitAnswerResponse,
    SessionResultResponse
)
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
        paragraph_ref=question["paragraph_ref"],
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
        result = evaluate_session_answer(
            session_id=request.session_id,
            paragraph_ref=request.paragraph_ref,
            user_answer=request.answer,
            db_conn=db
        )
        
        cur = db.cursor()
        cur.execute(
            "SELECT route, flags_2026 FROM sessions WHERE id=%s",
            (request.session_id,)
        )
        row = cur.fetchone()
        cur.close()
        
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
        
        return SubmitAnswerResponse(
            session_id=request.session_id,
            paragraph_ref=request.paragraph_ref,
            result=result["result"],
            fail_reason=result.get("fail_reason"),
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
        SELECT overall_result, rules_passed, rules_failed,
               rules_flagged, checklist_items, disclaimer
        FROM session_results
        WHERE session_id = %s
    """, (session_id,))
    row = cur.fetchone()
    cur.close()
    
    if not row:
        raise HTTPException(
            status_code=404,
            detail="Result not found. Session may not be complete."
        )
    
    return SessionResultResponse(
        session_id=session_id,
        overall_result=row[0],
        rules_passed=row[1] or [],
        rules_failed=row[2] or [],
        rules_flagged=row[3] or [],
        checklist_items=row[4] or [],
        disclaimer=row[5]
    )
