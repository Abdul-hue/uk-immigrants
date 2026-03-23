import httpx

try:
    r = httpx.get('http://localhost:8000/openapi.json')
    routes = [k for k in r.json()["paths"].keys()]
    print("Swagger /docs exposed routes:")
    for root in sorted(routes):
        print(f" - {root}")
except Exception as e:
    print(f"Failed to fetch openapi.json: {e}")
