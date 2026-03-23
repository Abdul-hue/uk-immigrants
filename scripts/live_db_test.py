from db.connection import get_connection
from api.engine.rule_engine import (
    load_constraint, evaluate_answer, get_checklist_for_route
)
conn = get_connection()

# Load a real FIN constraint from DB
cur = conn.cursor()
cur.execute('''
    SELECT paragraph_ref, constraint_json 
    FROM rule_paragraphs 
    WHERE constraint_json IS NOT NULL 
    LIMIT 1
''')
row = cur.fetchone()
print(f'Loaded constraint: {row[0]}')
print(f'Field: {row[1]["field"]}')
print(f'Operator: {row[1]["operator"]}')

# Test checklist
checklist = get_checklist_for_route('SKILLED_WORKER')
print(f'Checklist items: {len(checklist)}')
for item in checklist:
    print(f'  - {item}')

conn.close()
