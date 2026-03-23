import os
import json
from dotenv import load_dotenv
load_dotenv(override=True)

import openai

api_key = os.getenv("OPENAI_API_KEY")
print(f"Key loaded: {bool(api_key)}")
print(f"Key preview: {api_key[:12]}...")

client = openai.OpenAI(api_key=api_key)

prompt = """
You are an intent classifier for a UK visa eligibility platform.
Read the user's input and identify which visa route applies.

Available routes:
- SKILLED_WORKER: has a job offer from a UK Home Office licensed sponsor
- VISITOR: short stay for tourism, business meeting, or family visit
- UNKNOWN: cannot determine from input provided

User input: "I have a job offer from a hospital in Manchester"

Return ONLY a valid JSON object:
{
  "matched_route": "one of the routes above",
  "confidence": 0.95,
  "reasoning": "one sentence",
  "clarifying_question": null
}
"""

print("\nCalling GPT-4o...")
try:
    response = client.chat.completions.create(
        model="gpt-4o",
        temperature=0,
        max_tokens=200,
        messages=[{"role": "user", "content": prompt}]
    )
    raw = response.choices[0].message.content
    print(f"Raw response: {raw}")
    
    parsed = json.loads(raw)
    print(f"Parsed route: {parsed['matched_route']}")
    print(f"Confidence: {parsed['confidence']}")
    print("\nSUCCESS — classifier logic works")
    
except json.JSONDecodeError as e:
    print(f"JSON PARSE ERROR: {e}")
    print(f"Raw content was: {raw}")
    
except Exception as e:
    import traceback
    print(f"API ERROR: {type(e).__name__}: {e}")
    traceback.print_exc()