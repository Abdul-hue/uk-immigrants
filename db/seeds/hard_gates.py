from db.connection import get_connection
from hard_gate.loader import HARD_GATE_DEFINITIONS

def seed_hard_gates(db_conn):
    """Seed the hard_gates table."""
    cur = db_conn.cursor()
    
    for gate in HARD_GATE_DEFINITIONS:
        cur.execute("""
            INSERT INTO hard_gates
                (gate_order, name, paragraph_ref, question, fail_type, fail_message, fires_before_route)
            VALUES (%s, %s, %s, %s, %s, %s, %s)
            ON CONFLICT (gate_order) DO UPDATE SET
                name = EXCLUDED.name,
                paragraph_ref = EXCLUDED.paragraph_ref,
                question = EXCLUDED.question,
                fail_type = EXCLUDED.fail_type,
                fail_message = EXCLUDED.fail_message
        """, (
            gate["gate_order"],
            gate["name"],
            gate["paragraph_ref"],
            gate["question"],
            gate["fail_type"],
            gate["fail_message"],
            gate["fires_before_route"]
        ))
    
    db_conn.commit()
    cur.close()
    return len(HARD_GATE_DEFINITIONS)

if __name__ == "__main__":
    conn = get_connection()
    try:
        print("Seeding hard gates...")
        count = seed_hard_gates(conn)
        print(f"Successfully seeded {count} hard gates.")
    finally:
        conn.close()
