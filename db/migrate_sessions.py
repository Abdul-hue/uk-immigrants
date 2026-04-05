from db.connection import get_connection

def migrate():
    conn = get_connection()
    cur = conn.cursor()
    try:
        print("Migrating sessions table...")
        cur.execute("ALTER TABLE sessions ADD COLUMN IF NOT EXISTS completed_at TIMESTAMP;")
        
        print("Ensuring session_results table exists...")
        cur.execute("""
            CREATE TABLE IF NOT EXISTS session_results (
                id SERIAL PRIMARY KEY,
                session_id UUID UNIQUE REFERENCES sessions(id),
                overall_result VARCHAR(20),
                rules_passed JSONB DEFAULT '[]',
                rules_failed JSONB DEFAULT '[]',
                rules_flagged JSONB DEFAULT '[]',
                checklist_items JSONB DEFAULT '[]',
                disclaimer TEXT,
                created_at TIMESTAMP DEFAULT NOW()
            );
        """)
        conn.commit()
        print("Migration successful! ✅")
    except Exception as e:
        print(f"Migration failed: {e}")
        conn.rollback()
    finally:
        cur.close()
        conn.close()

if __name__ == "__main__":
    migrate()
