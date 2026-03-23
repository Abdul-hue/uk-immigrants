from db.connection import get_connection

def seed_appendices(db_conn):
    """Seed the appendices table. Must run first."""
    cur = db_conn.cursor()
    
    appendices = [
        ('SKILLED_WORKER', 'https://www.gov.uk/guidance/immigration-rules/immigration-rules-appendix-skilled-worker', 10),
        ('APPENDIX_FM', 'https://www.gov.uk/guidance/immigration-rules/immigration-rules-appendix-fm-family-members', 20),
        ('APPENDIX_VISITOR', 'https://www.gov.uk/guidance/immigration-rules/immigration-rules-appendix-v-visitor-rules', 23),
        ('HPI', 'https://www.gov.uk/guidance/immigration-rules/immigration-rules-appendix-high-potential-individual', 30),
        ('SCALE_UP', 'https://www.gov.uk/guidance/immigration-rules/immigration-rules-appendix-scale-up', 40),
        ('GLOBAL_TALENT', 'https://www.gov.uk/guidance/immigration-rules/immigration-rules-appendix-global-talent', 50),
        ('APPENDIX_STUDENT', 'https://www.gov.uk/guidance/immigration-rules/immigration-rules-appendix-student', 60),
        ('APPENDIX_GRADUATE', 'https://www.gov.uk/guidance/immigration-rules/immigration-rules-appendix-graduate', 70)
    ]
    
    for code, url, priority in appendices:
        cur.execute("""
            INSERT INTO appendices (code, url, priority)
            VALUES (%s, %s, %s)
            ON CONFLICT (code) DO UPDATE SET
                url = EXCLUDED.url,
                priority = EXCLUDED.priority;
        """, (code, url, priority))
    
    db_conn.commit()
    cur.close()
    return len(appendices)

if __name__ == "__main__":
    conn = get_connection()
    try:
        print("Seeding appendices...")
        count = seed_appendices(conn)
        print(f"Successfully seeded {count} appendices.")
    finally:
        conn.close()
