import httpx, json

BASE = 'http://localhost:8000'

try:
    # Test root
    r = httpx.get(f'{BASE}/')
    print('Root:', r.json()['platform'])

    # Test health
    r = httpx.get(f'{BASE}/health')
    print('Health:', r.json()['status'])

    # Test explain stub
    r = httpx.post(f'{BASE}/api/explain/', json={
        'paragraph_ref': 'FIN-2.1',
        'question': 'What funds do I need?'
    })
    print('Explain status:', r.status_code)
    print('Corpus B status:', r.json()['corpus_b_status'])

    print('All endpoints responding ✅')
except Exception as e:
    print(f"Error connected to running uvicorn instance: {e}")
