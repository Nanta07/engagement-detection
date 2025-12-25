#Deploy WebSocket Server to receive engagement data from Raspberry Pi clients and log them into structured CSV files
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
LOG_DIR = os.path.join(BASE_DIR, "logs")
SESSION_DIR = os.path.join(BASE_DIR, "sessions")

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(SESSION_DIR, exist_ok=True)

GLOBAL_LOG = os.path.join(LOG_DIR, "engagement_log.csv")

# ============================================================
# INIT GLOBAL CSV
# ============================================================
if not os.path.exists(GLOBAL_LOG):
    with open(GLOBAL_LOG, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp",
            "responden",
            "sesi",
            "frame",
            "engagement_level",
            "fps",
            "response_time"
        ])

# ============================================================
# WEBSOCKET HANDLER
# ============================================================
async def handler(websocket):
    print("✅ Raspi connected")

    async for message in websocket:
        try:
            data = json.loads(message)

            if data.get("type") != "engagement":
                continue

            responden = data["responden"]
            sesi = data["sesi"]
            frame = data["frame"]
            engagement = data["engagement_level"]
            fps = data["fps"]
            response_time = data["response_time"]
            timestamp = data["timestamp"]

            iso_time = datetime.fromtimestamp(timestamp).isoformat()

            # Folder per responden & sesi
            session_path = os.path.join(
                SESSION_DIR,
                f"responden_{responden}",
                f"sesi_{sesi}"
            )
            os.makedirs(session_path, exist_ok=True)

            session_csv = os.path.join(session_path, "results.csv")

            if not os.path.exists(session_csv):
                with open(session_csv, "w", newline="") as f:
                    writer = csv.writer(f)
                    writer.writerow([
                        "timestamp",
                        "frame",
                        "engagement_level",
                        "fps",
                        "response_time"
                    ])

            with open(session_csv, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    iso_time,
                    frame,
                    engagement,
                    fps,
                    response_time
                ])

            with open(GLOBAL_LOG, "a", newline="") as f:
                writer = csv.writer(f)
                writer.writerow([
                    iso_time,
                    responden,
                    sesi,
                    frame,
                    engagement,
                    fps,
                    response_time
                ])

            print(f"📥 {responden} | sesi {sesi} | level {engagement}")

        except Exception as e:
            print("❌ Error:", e)

# ============================================================
# MAIN
# ============================================================
async def main():
    print(f"🚀 WebSocket Server running on {PORT}")
    async with websockets.serve(handler, HOST, PORT):
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())