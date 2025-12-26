# server_ws.py
import asyncio
import websockets
import json
import os
import csv
from datetime import datetime

HOST = "0.0.0.0"
PORT = 8000

BASE_DIR = "data"
SESSION_DIR = os.path.join(BASE_DIR, "sessions")
LOG_DIR = os.path.join(BASE_DIR, "logs")

os.makedirs(SESSION_DIR, exist_ok=True)
os.makedirs(LOG_DIR, exist_ok=True)

GLOBAL_LOG = os.path.join(LOG_DIR, "engagement_log.csv")

if not os.path.exists(GLOBAL_LOG):
    with open(GLOBAL_LOG, "w", newline="") as f:
        csv.writer(f).writerow([
            "timestamp","responden","sesi",
            "frame","engagement_level",
            "fps","response_time"
        ])

async def handler(websocket):
    print("✅ Client connected")

    try:
        async for message in websocket:
            data = json.loads(message)

            responden = data["responden"]
            sesi = data["sesi"]

            timestamp = datetime.now().isoformat()

            session_path = os.path.join(
                SESSION_DIR,
                f"responden_{responden}",
                f"sesi_{sesi}"
            )
            os.makedirs(session_path, exist_ok=True)

            session_csv = os.path.join(session_path, "results.csv")

            if not os.path.exists(session_csv):
                with open(session_csv, "w", newline="") as f:
                    csv.writer(f).writerow([
                        "timestamp","frame",
                        "engagement_level","fps","response_time"
                    ])

            with open(session_csv, "a", newline="") as f:
                csv.writer(f).writerow([
                    timestamp,
                    data["frame"],
                    data["engagement_level"],
                    data["fps"],
                    data["response_time"]
                ])

            with open(GLOBAL_LOG, "a", newline="") as f:
                csv.writer(f).writerow([
                    timestamp,
                    responden,
                    sesi,
                    data["frame"],
                    data["engagement_level"],
                    data["fps"],
                    data["response_time"]
                ])

            await websocket.send(json.dumps({"status": "ok"}))

    except websockets.exceptions.ConnectionClosed:
        print("❌ Client disconnected")

async def main():
    print(f"🚀 WebSocket Server running on {HOST}:{PORT}")
    async with websockets.serve(handler, HOST, PORT):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())
