# ============================================================
# WebSocket Server for Engagement Detection (FINAL)
# Receives metadata from Raspberry Pi
# ============================================================

import asyncio
import websockets
import json
import os
import csv
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================
HOST = "0.0.0.0"
PORT = 8000

BASE_DIR = "data"
SESSION_DIR = os.path.join(BASE_DIR, "sessions")

os.makedirs(SESSION_DIR, exist_ok=True)

# ============================================================
# HELPER
# ============================================================
def ensure_session_csv(responden, sesi):
    """
    Ensure folder & CSV exist for a session
    """
    session_path = os.path.join(
        SESSION_DIR,
        f"responden_{responden}",
        f"sesi_{sesi}"
    )
    os.makedirs(session_path, exist_ok=True)

    csv_path = os.path.join(session_path, "engagement_metadata.csv")

    if not os.path.exists(csv_path):
        with open(csv_path, "w", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                "server_timestamp",
                "responden",
                "sesi",
                "frame_name",
                "engagement_level",
                "fps",
                "response_time"
            ])

    return csv_path

# ============================================================
# WS HANDLER
# ============================================================
async def handler(websocket):
    print("✅ Client connected")

    try:
        async for message in websocket:
            data = json.loads(message)

            responden = data["responden"]
            sesi = data["sesi"]

            csv_path = ensure_session_csv(responden, sesi)

            server_ts = datetime.now().isoformat()

            with open(csv_path, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    server_ts,
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

    except Exception as e:
        print("⚠️ Server error:", e)

# ============================================================
# MAIN
# ============================================================
async def main():
    print(f"🚀 WebSocket Server running on {HOST}:{PORT}")
    async with websockets.serve(handler, HOST, PORT):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())