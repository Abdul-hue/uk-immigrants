import json, csv, os
from datetime import datetime
from db.connection import get_connection

def export_all_sessions(output_dir: str = "exports") -> dict:
    """
    Export all completed sessions to JSON files.
    Creates one file per session in output_dir.
    """
    os.makedirs(output_dir, exist_ok=True)
    conn = get_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT s.id, s.route, s.nationality_iso,
               s.flags_2026, s.status, s.started_at,
               s.completed_at,
               sr.overall_result, sr.rules_failed,
               sr.disclaimer
        FROM sessions s
        LEFT JOIN session_results sr ON sr.session_id = s.id
        WHERE s.status IN ('pass','fail','flagged','completed')
        ORDER BY s.started_at DESC
    """)
    sessions = cur.fetchall()
    
    exported = 0
    for sess in sessions:
        session_id = str(sess[0])
        
        cur.execute("""
            SELECT paragraph_ref, question_text, answer,
                   rule_result, fail_reason, answered_at
            FROM session_answers
            WHERE session_id = %s
            ORDER BY answered_at ASC
        """, (session_id,))
        answers = cur.fetchall()
        
        data = {
            "export_timestamp": str(datetime.now()),
            "session_id": session_id,
            "route": sess[1],
            "nationality_iso": sess[2],
            "flags_2026": sess[3],
            "status": sess[4],
            "started_at": str(sess[5]),
            "completed_at": str(sess[6]),
            "overall_result": sess[7],
            "rules_failed": sess[8],
            "answers": [
                {
                    "paragraph_ref": a[0],
                    "question": a[1],
                    "answer": a[2],
                    "result": a[3],
                    "fail_reason": a[4],
                    "timestamp": str(a[5])
                }
                for a in answers
            ],
            "disclaimer": sess[9] or (
                "This is a Preliminary Self-Assessment only. "
                "It does not constitute legal advice."
            )
        }
        
        filename = f"{output_dir}/session_{session_id[:8]}.json"
        with open(filename, 'w') as f:
            json.dump(data, f, indent=2)
        exported += 1
    
    cur.close()
    conn.close()
    
    return {
        "exported": exported,
        "output_dir": output_dir,
        "timestamp": str(datetime.now())
    }


if __name__ == "__main__":
    print("Exporting all sessions...")
    result = export_all_sessions()
    print(f"Exported: {result['exported']} sessions")
    print(f"Output:   {result['output_dir']}/")
