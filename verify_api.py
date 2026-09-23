import urllib.request
import json
import sys

# Ensure UTF-8 output
sys.stdout.reconfigure(encoding='utf-8')

# 1. Health check
res = urllib.request.urlopen("http://127.0.0.1:8765/api/health")
print("Health status:", json.loads(res.read()))

# 2. Documents check
res = urllib.request.urlopen("http://127.0.0.1:8765/api/documents")
print("\nDocuments status:", json.loads(res.read()))

# 3. Chat test
req_data = json.dumps({"question": "What is deep learning?", "k": 3}).encode("utf-8")
req = urllib.request.Request(
    "http://127.0.0.1:8765/api/chat",
    data=req_data,
    headers={"Content-Type": "application/json"}
)
res = urllib.request.urlopen(req)
chat_res = json.loads(res.read())

print("\nAI Answer:\n", chat_res.get("answer"))
print(f"\nBook Citations Count: {len(chat_res.get('sources', []))}")
for idx, src in enumerate(chat_res.get("sources", []), 1):
    print(f"Citation {idx}: Book = {src.get('source')}, Page = {src.get('page')}")
    print(f"Snippet: {src.get('content')[:120]}...\n")
