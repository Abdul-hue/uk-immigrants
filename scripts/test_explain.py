import httpx
import time

BASE = 'http://localhost:8000'

print("Starting session...")
r = httpx.post(f'{BASE}/api/session/start', json={
    'user_input': 'I have a job offer from a UK employer',
    'nationality_iso': 'PK'
}, timeout=30.0)
sid = r.json()['session_id']
print(f"Session: {sid[:8]}...")

httpx.post(f'{BASE}/api/session/hard-gate', json={
    'session_id': sid,
    'has_deportation_order': False,
    'has_used_deception': False,
    'has_criminal_conviction': False,
    'has_immigration_debt': False,
    'has_overstayed_90_days': False
}, timeout=10.0)
print("Hard gate: PASS")
print()

for i in range(10):
    r = httpx.get(f'{BASE}/api/questions/next/{sid}', timeout=10.0)
    
    if r.status_code != 200:
        print(f"Q{i+1}: Status {r.status_code} - {r.json()}")
        break
    
    data = r.json()
    
    if data.get('complete'):
        print(f"Q{i+1}: All questions complete")
        break
    
    ref = data['paragraph_ref']
    qtype = data['answer_type']
    qtext = data['question_text'][:60]
    print(f"Q{i+1}: [{ref}] type={qtype}")
    print(f"     Text: {qtext}")
    
    # Pick answer based on type
    if qtype == 'boolean':
        answer = 'yes'
    elif qtype == 'select' and data.get('answer_options'):
        answer = data['answer_options'][0]
        print(f"     Options: {data['answer_options']}")
    elif qtype == 'currency':
        answer = '30000'
    else:
        answer = 'test answer'
    
    r2 = httpx.post(f'{BASE}/api/questions/answer', json={
        'session_id': sid,
        'paragraph_ref': ref,
        'answer': answer
    }, timeout=10.0)
    
    print(f"     Answer: '{answer}' -> Status: {r2.status_code}")
    
    if r2.status_code != 200:
        print(f"     ERROR DETAIL: {r2.json()}")
        print()
        print("=== FOUND THE BREAKING QUESTION ===")
        print(f"Paragraph ref: {ref}")
        print(f"Answer type: {qtype}")
        print(f"Answer sent: {answer}")
        break
    else:
        result = r2.json()
        print(f"     Rule result: {result.get('result')} | Next: {result.get('next_step')}")
    
    print()
    time.sleep(0.3)

print("Done")