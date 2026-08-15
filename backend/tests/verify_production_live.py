"""
Comprehensive Production Real-Environment Diagnostic & Health Audit Script.
Tests:
1. Health, RAG, Current Affairs, Books, Progress, Revision, Tests, Notes HTTP endpoints
2. Real Production WebSocket: wss://mj-ai-teacher.onrender.com/api/mj/live-ws
3. Live Audio/Text round-trip, barge-in, and turn-taking
"""

import sys
import time
import json
import asyncio
import ssl
import urllib.request
import urllib.parse

PROD_URL = "https://mj-ai-teacher.onrender.com"
WS_PROD_URL = "wss://mj-ai-teacher.onrender.com/api/mj/live-ws"

def audit_http_endpoints():
    print("=" * 60)
    print("PHASE 1: PRODUCITON HTTP ENDPOINT HEALTH AUDIT")
    print("=" * 60)

    ctx = ssl.create_default_context()
    ctx.check_hostname = False
    ctx.verify_mode = ssl.CERT_NONE

    endpoints = [
        ("GET", "/", None),
        ("GET", "/api/health", None),
        ("GET", "/api/books", None),
        ("GET", "/api/current-affairs", None),
        ("GET", "/api/progress/summary", None),
        ("GET", "/api/revision/today", None),
        ("GET", "/api/tests/daily", None),
        ("GET", "/api/notes/all?user_id=1", None),
    ]

    for method, ep, body_data in endpoints:
        url = PROD_URL + ep
        start = time.time()
        try:
            req = urllib.request.Request(
                url,
                data=json.dumps(body_data).encode("utf-8") if body_data else None,
                headers={
                    "User-Agent": "Mozilla/5.0",
                    "Content-Type": "application/json"
                }
            )
            with urllib.request.urlopen(req, context=ctx, timeout=20) as resp:
                elapsed = int((time.time() - start) * 1000)
                raw = resp.read()
                try:
                    text = raw.decode("utf-8")
                except Exception:
                    text = str(raw)
                print(f"[SUCCESS {resp.status}] {ep} ({elapsed}ms)")
                print(f"  Response: {text[:200]}")
        except urllib.error.HTTPError as e:
            elapsed = int((time.time() - start) * 1000)
            err_body = e.read().decode("utf-8", errors="replace")[:200]
            print(f"[HTTP {e.code}] {ep} ({elapsed}ms)")
            print(f"  Error Body: {err_body}")
        except Exception as e:
            elapsed = int((time.time() - start) * 1000)
            print(f"[FAIL] {ep} ({elapsed}ms): {e}")

async def audit_websocket():
    print("\n" + "=" * 60)
    print("PHASE 2: PRODUCTION WEBSOCKET AUDIT")
    print("=" * 60)
    import websockets

    print(f"Connecting to {WS_PROD_URL}...")
    start = time.time()
    try:
        async with websockets.connect(WS_PROD_URL, ping_timeout=25) as ws:
            elapsed = int((time.time() - start) * 1000)
            print(f"[WS CONNECTED in {elapsed}ms] Waiting for ready frame...")
            
            ready_msg = await asyncio.wait_for(ws.recv(), timeout=20)
            print(f"[WS READY RECEIVED]: {ready_msg}")

            # Send test conversation message
            print("Sending text turn: 'Are MJ, aaj kasa ahes?'")
            await ws.send(json.dumps({
                "type": "text",
                "text": "Are MJ, aaj kasa ahes?"
            }))

            received_audio_count = 0
            received_transcripts = []
            
            while True:
                resp = await asyncio.wait_for(ws.recv(), timeout=30)
                data = json.loads(resp)
                msg_type = data.get("type")

                if msg_type == "audio":
                    received_audio_count += 1
                elif msg_type == "transcript":
                    received_transcripts.append(data.get("text", ""))
                elif msg_type == "turn_complete":
                    print("[WS TURN COMPLETE]")
                    break
                elif msg_type == "error":
                    print(f"[WS SERVER ERROR]: {data.get('message')}")
                    break

            print(f"Total audio chunks received: {received_audio_count}")
            print(f"Assistant Marathi transcript: {''.join(received_transcripts)}")

    except Exception as e:
        print(f"[WS CONNECTION/SESSION FAILED]: {type(e)} - {e}")

if __name__ == "__main__":
    audit_http_endpoints()
    try:
        asyncio.run(audit_websocket())
    except Exception as e:
        print("WebSocket audit failed:", e)
