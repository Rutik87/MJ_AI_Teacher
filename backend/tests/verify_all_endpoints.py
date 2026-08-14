import urllib.request
import json

BASE_URL = "http://127.0.0.1:8000/api"

endpoints = [
    ("GET", "/health", None),
    ("GET", "/subjects", None),
    ("GET", "/books", None),
    ("GET", "/current-affairs/", None),
    ("GET", "/current-affairs/quiz", None),
    ("POST", "/tests/pyq-analysis", {"subject_name": "इतिहास", "topic": "1857 चा उठाव"}),
    ("GET", "/progress/summary", None),
    ("GET", "/revision/summary", None),
    ("POST", "/mj/converse", {"query": "Are MJ"}),
    ("POST", "/sync/batch", {"actions": [{"id": "test_1", "action_type": "reading_progress", "payload": {"subject_name": "History", "questions_attempted": 5, "correct": 4}, "created_at": "2026-08-14T12:00:00Z"}]}),
]

print("=== VERIFYING ALL CLOUD API ENDPOINTS ===")
all_passed = True
for method, path, payload in endpoints:
    url = BASE_URL + path
    try:
        if method == "GET":
            req = urllib.request.Request(url, headers={"User-Agent": "MPSC-AI-Test"})
        else:
            data_bytes = json.dumps(payload).encode("utf-8")
            req = urllib.request.Request(url, data=data_bytes, headers={"Content-Type": "application/json", "User-Agent": "MPSC-AI-Test"})

        with urllib.request.urlopen(req, timeout=5) as response:
            status = response.status
            content = json.loads(response.read().decode("utf-8"))
            print(f"[PASS] {method} {path} -> HTTP {status}")
    except Exception as e:
        print(f"[FAIL] {method} {path} -> FAILED: {e}")
        all_passed = False

if all_passed:
    print("\nALL API ENDPOINTS VERIFIED & WORKING FLAWLESSLY!")
else:
    print("\nSOME ENDPOINTS FAILED")
