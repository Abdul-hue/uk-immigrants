from fastapi import APIRouter, HTTPException, Depends
from api.models.schemas import (
    StartSessionRequest, StartSessionResponse,
    HardGateAnswersRequest, HardGateResponse
)
from api.engine.sequence import (
    initialize_session, process_hard_gate_answers
)
from db.connection import get_connection
import psycopg2
import io
import csv
from fastapi.responses import StreamingResponse

router = APIRouter()

def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()

from api.utils import strip_internal_refs

@router.get("/{session_id}/export")
def export_session_csv(session_id: str, db=Depends(get_db)):
    """
    Returns a CSV of: question, answer, rule_result, paragraph_ref.
    """
    cur = db.cursor()
    # Bug 5 — MEDIUM: Reference column is blank in every CSV row
    # Join session_answers with rule_paragraphs to get the plain-English rule text
    cur.execute("""
        SELECT sa.question_text, sa.answer, sa.rule_result, rp.raw_text
        FROM session_answers sa
        LEFT JOIN rule_paragraphs rp ON sa.paragraph_ref = rp.paragraph_ref
        WHERE sa.session_id = %s
        ORDER BY sa.created_at ASC
    """, (session_id,))
    rows = cur.fetchall()
    cur.close()
    
    if not rows:
        raise HTTPException(status_code=404, detail="No answers found for this session")
    
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["Question", "Answer", "Result", "Reference"])
    for row in rows:
        # Strip internal refs from all string fields in the row
        # If raw_text (Reference) is missing, use default text
        question, answer, result, reference = row
        reference = reference if reference else "See full assessment for details."
        
        clean_row = [
            strip_internal_refs(str(question)),
            strip_internal_refs(str(answer)),
            str(result),
            strip_internal_refs(str(reference))
        ]
        writer.writerow(clean_row)
    
    output.seek(0)
    
    return StreamingResponse(
        iter([output.getvalue()]),
        media_type="text/csv",
        headers={"Content-Disposition": f"attachment; filename=eligibility_result_{session_id}.csv"}
    )

@router.post("/start", response_model=StartSessionResponse)
def start_session(request: StartSessionRequest, 
                  db=Depends(get_db)):
    """
    Entry point for every user session.
    Classifies intent, creates session row, loads hard gates.
    """
    try:
        result = initialize_session(
            user_input=request.user_input,
            nationality_iso=request.nationality_iso,
            db_conn=db
        )
        
        if result.get("status") == "NEEDS_CLARIFICATION":
            raise HTTPException(
                status_code=422,
                detail={
                    "status": "NEEDS_CLARIFICATION",
                    "clarifying_question": result.get("clarifying_question"),
                    "disclaimer": (
                        "This is a Preliminary Self-Assessment only. "
                        "It does not constitute legal advice."
                    )
                }
            )
        
        return StartSessionResponse(
            session_id=str(result["session_id"]),
            route=result["route"],
            confidence=result["confidence"],
            flags_2026=result["flags_2026"],
            eta_required=result["eta_required"],
            flag_warnings=result.get("flag_warnings", []),
            next_step=result["next_step"],
            hard_gate_questions=result["hard_gate_questions"],
            disclaimer=result["disclaimer"]
        )
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/hard-gate", response_model=HardGateResponse)
def submit_hard_gate(request: HardGateAnswersRequest,
                     db=Depends(get_db)):
    """
    Submit answers to all 6 hard gate questions.
    Returns PASS, FLAGGED, or HARD_FAIL.
    HARD_FAIL ends the session immediately.
    """
    try:
        answers = {
            "has_deportation_order": request.has_deportation_order,
            "has_used_deception": request.has_used_deception,
            "has_criminal_conviction": request.has_criminal_conviction,
            "has_immigration_debt": request.has_immigration_debt,
            "has_overstayed_90_days": request.has_overstayed_90_days
        }
        
        result = process_hard_gate_answers(
            session_id=request.session_id,
            answers=answers,
            db_conn=db
        )
        
        return HardGateResponse(
            session_id=request.session_id,
            result=result["result"],
            session_can_continue=result["session_can_continue"],
            flagged_gates=result.get("flagged_gates", []),
            fail_message=strip_internal_refs(result.get("fail_message")),
            next_step=result.get("next_step", "questions"),
            disclaimer=result["disclaimer"]
        )
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{session_id}/status")
def get_session_status(session_id: str, db=Depends(get_db)):
    """Get current session status and progress."""
    cur = db.cursor()
    cur.execute("""
        SELECT s.id, s.route, s.status, s.flags_2026,
               s.started_at, s.completed_at,
               COUNT(sa.id) as answers_given
        FROM sessions s
        LEFT JOIN session_answers sa ON sa.session_id = s.id
        WHERE s.id = %s
        GROUP BY s.id
    """, (session_id,))
    row = cur.fetchone()
    cur.close()
    
    if not row:
        raise HTTPException(status_code=404, 
                           detail="Session not found")
    
    return {
        "session_id": str(row[0]),
        "route": row[1],
        "status": row[2],
        "flags_2026": row[3],
        "started_at": str(row[4]),
        "completed_at": str(row[5]) if row[5] else None,
        "answers_given": row[6],
        "disclaimer": (
            "This is a Preliminary Self-Assessment only. "
            "It does not constitute legal advice."
        )
    }
