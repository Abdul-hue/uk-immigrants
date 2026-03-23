from db.connection import get_connection

def list_tables():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT table_name FROM information_schema.tables WHERE table_schema = 'public'")
    tables = [row[0] for row in cur.fetchall()]
    for t in tables:
        print(t)

if __name__ == '__main__':
    list_tables()
