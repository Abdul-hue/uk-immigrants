from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import JSONResponse, StreamingResponse
from db.connection import get_connection
import csv, json, io
from datetime import datetime

router = APIRouter()

def get_db():
    conn = get_connection()
    try:
        yield conn
    finally:
        conn.close()

### GET /api/audit/session/{session_id}
@router.get("/session/{session_id}")
def get_session_audit(session_id: str, db=Depends(get_db)):
    cur = db.cursor()
    
    # Session metadata
    cur.execute("""
        SELECT id, route, nationality_iso, flags_2026,
               eta_required, status, started_at, completed_at
        FROM sessions WHERE id = %s
    """, (session_id,))
    session = cur.fetchone()
    if not session:
        raise HTTPException(status_code=404,
                           detail="Session not found")
    
    # All answers
    cur.execute("""
        SELECT paragraph_ref, question_text, answer,
               rule_result, fail_reason, answered_at
        FROM session_answers
        WHERE session_id = %s
        ORDER BY answered_at ASC
    """, (session_id,))
    answers = cur.fetchall()
    
    # Final result
    cur.execute("""
        SELECT overall_result, rules_passed, rules_failed,
               rules_flagged, checklist_items, disclaimer,
               created_at
        FROM session_results
        WHERE session_id = %s
    """, (session_id,))
    result = cur.fetchone()
    cur.close()
    
    return {
        "session_id": session_id,
        "session": {
            "route": session[1],
            "nationality_iso": session[2],
            "flags_2026": session[3],
            "eta_required": session[4],
            "status": session[5],
            "started_at": str(session[6]),
            "completed_at": str(session[7]) if session[7] else None
        },
        "answers": [
            {
                "paragraph_ref": a[0],
                "question_text": a[1],
                "answer": a[2],
                "rule_result": a[3],
                "fail_reason": a[4],
                "answered_at": str(a[5])
            }
            for a in answers
        ],
        "result": {
            "overall_result": result[0],
            "rules_passed": result[1],
            "rules_failed": result[2],
            "rules_flagged": result[3],
            "checklist_items": result[4],
            "disclaimer": result[5],
            "created_at": str(result[6])
        } if result else None,
        "total_questions_answered": len(answers),
        "disclaimer": (
            "This is a Preliminary Self-Assessment only. "
            "It does not constitute legal advice."
        )
    }


### GET /api/audit/session/{session_id}/export?format=json|csv
@router.get("/session/{session_id}/export")
def export_session(session_id: str,
                   format: str = "json",
                   db=Depends(get_db)):
    # Reuse audit data
    cur = db.cursor()
    cur.execute("""
        SELECT s.route, s.nationality_iso, s.flags_2026,
               s.status, s.started_at,
               sa.paragraph_ref, sa.question_text,
               sa.answer, sa.rule_result, sa.fail_reason,
               sa.answered_at
        FROM sessions s
        LEFT JOIN session_answers sa ON sa.session_id = s.id
        WHERE s.id = %s
        ORDER BY sa.answered_at ASC
    """, (session_id,))
    rows = cur.fetchall()
    cur.close()
    
    if not rows:
        raise HTTPException(status_code=404,
                           detail="Session not found")
    
    if format == "csv":
        output = io.StringIO()
        writer = csv.writer(output)
        writer.writerow([
            "session_id", "route", "nationality",
            "status", "paragraph_ref", "question",
            "answer", "result", "fail_reason", "timestamp"
        ])
        for row in rows:
            writer.writerow([
                session_id, row[0], row[1],
                row[3], row[5], row[6],
                row[7], row[8], row[9],
                str(row[10])
            ])
        output.seek(0)
        return StreamingResponse(
            io.BytesIO(output.getvalue().encode()),
            media_type="text/csv",
            headers={
                "Content-Disposition":
                f"attachment; filename=session_{session_id[:8]}.csv"
            }
        )
    
    # Default JSON export
    data = {
        "export_date": str(datetime.now()),
        "session_id": session_id,
        "route": rows[0][0],
        "nationality": rows[0][1],
        "flags_2026": rows[0][2],
        "status": rows[0][3],
        "started_at": str(rows[0][4]),
        "answers": [
            {
                "paragraph_ref": r[5],
                "question": r[6],
                "answer": r[7],
                "result": r[8],
                "fail_reason": r[9],
                "timestamp": str(r[10])
            }
            for r in rows if r[5]
        ],
        "disclaimer": (
            "This is a Preliminary Self-Assessment only. "
            "It does not constitute legal advice. "
            "You should consult a qualified immigration "
            "solicitor before making any application."
        )
    }
    return JSONResponse(content=data)


### GET /api/audit/stats
@router.get("/stats")
def get_platform_stats(db=Depends(get_db)):
    cur = db.cursor()
    
    cur.execute("SELECT COUNT(*) FROM sessions")
    total_sessions = cur.fetchone()[0]
    
    cur.execute("""
        SELECT status, COUNT(*) 
        FROM sessions GROUP BY status
    """)
    by_status = dict(cur.fetchall())
    
    cur.execute("""
        SELECT route, COUNT(*) 
        FROM sessions GROUP BY route
        ORDER BY COUNT(*) DESC
    """)
    by_route = dict(cur.fetchall())
    
    cur.execute("""
        SELECT overall_result, COUNT(*)
        FROM session_results GROUP BY overall_result
    """)
    by_result = dict(cur.fetchall())
    
    cur.execute("SELECT COUNT(*) FROM question_templates")
    total_questions = cur.fetchone()[0]
    
    cur.execute("""
        SELECT COUNT(*) FROM question_templates
        WHERE verified = FALSE
    """)
    unverified = cur.fetchone()[0]
    
    cur.execute("""
        SELECT COUNT(*) FROM appendices
        WHERE requires_reverification = TRUE
    """)
    flagged_appendices = cur.fetchone()[0]
    
    cur.close()
    
    return {
        "platform_stats": {
            "total_sessions": total_sessions,
            "sessions_by_status": by_status,
            "sessions_by_route": by_route,
            "results_breakdown": by_result
        },
        "rule_database": {
            "total_questions": total_questions,
            "unverified_questions": unverified,
            "flagged_appendices": flagged_appendices
        },
        "compliance": {
            "solicitor_review_required": unverified > 0,
            "reverification_required": flagged_appendices > 0,
            "disclaimer": (
                "This is a Preliminary Self-Assessment only. "
                "It does not constitute legal advice."
            )
        }
    }
