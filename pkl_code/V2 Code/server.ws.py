# websocket-code/server_ws-update.py
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
# WEBSOCKET HANDLER
# ============================================================
async def handler(websocket):
    print("✅ Client connected")

    try:
        async for message in websocket:
            data = json.loads(message)

            # ----------------------------
            # Required fields validation
            # ----------------------------
            if not all(k in data for k in [
                "responden", "sesi",
                "frame", "engagement_level",
                "fps", "response_time"
            ]):
                await websocket.send(json.dumps({
                    "status": "error",
                    "message": "Invalid payload structure"
                }))
                continue

            responden = data["responden"]
            sesi = data["sesi"]

            timestamp = datetime.now().isoformat()

            # ----------------------------
            # Session folder
            # ----------------------------
            session_path = os.path.join(
                SESSION_DIR,
                f"responden_{responden}",
                f"sesi_{sesi}"
            )
            os.makedirs(session_path, exist_ok=True)

            # ----------------------------
            # Session CSV (1 session = 1 CSV)
            # ----------------------------
            session_csv = os.path.join(
                session_path,
                "engagement_results.csv"
            )

            if not os.path.exists(session_csv):
                with open(session_csv, "w", newline="") as f:
                    csv.writer(f).writerow([
                        "timestamp",
                        "frame",
                        "engagement_level",
                        "fps",
                        "response_time"
                    ])

            with open(session_csv, "a", newline="") as f:
                csv.writer(f).writerow([
                    timestamp,
                    data["frame"],
                    data["engagement_level"],
                    data["fps"],
                    data["response_time"]
                ])

            await websocket.send(json.dumps({
                "status": "ok",
                "session": sesi
            }))

    except websockets.exceptions.ConnectionClosed:
        print("❌ Client disconnected")

    except Exception as e:
        print("🔥 Server error:", e)

# ============================================================
# MAIN
# ============================================================
async def main():
    print(f"🚀 WebSocket Server running on {HOST}:{PORT}")
    async with websockets.serve(handler, HOST, PORT):
        await asyncio.Future()  # run forever

if __name__ == "__main__":
    asyncio.run(main())

    
interface=wlan0
driver=nl80211

ssid=RASPI_ESP32_AP
hw_mode=g
channel=6

ieee80211n=1
wmm_enabled=0

auth_algs=1
ignore_broadcast_ssid=0

wpa=2
wpa_passphrase=raspi12345
wpa_key_mgmt=WPA-PSK
rsn_pairwise=CCMP

[Service]
ExecStart=
ExecStart=/usr/sbin/hostapd -B -P /run/hostapd.pid $DAEMON_OPTS $DAEMON_CONF