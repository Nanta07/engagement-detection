# Server WebSocket for accepting engagement data from Raspberry Pi clients

from flask import Flask
from flask_socketio import SocketIO, emit
import os
import csv
from datetime import datetime

# ============================================================
# CONFIG
# ============================================================
SERVER_HOST = "0.0.0.0"
SERVER_PORT = 8000

BASE_DIR = "data"
LOG_DIR = os.path.join(BASE_DIR, "logs")
SESSION_DIR = os.path.join(BASE_DIR, "sessions")

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(SESSION_DIR, exist_ok=True)

GLOBAL_LOG = os.path.join(LOG_DIR, "engagement_log.csv")

# ============================================================
# INIT APP
# ============================================================
app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*")

# ============================================================
# INIT CSV
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
# SOCKET EVENTS
# ============================================================
@socketio.on("connect")
def on_connect():
    print("🔌 Raspi connected")

@socketio.on("disconnect")
def on_disconnect():
    print("❌ Raspi disconnected")

@socketio.on("engagement_result")
def on_engagement_result(data):
    print("📥 Data received:", data)

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
            timestamp,
            data["frame"],
            data["engagement_level"],
            data["fps"],
            data["response_time"]
        ])

    with open(GLOBAL_LOG, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            timestamp,
            responden,
            sesi,
            data["frame"],
            data["engagement_level"],
            data["fps"],
            data["response_time"]
        ])

    emit("ack", {"status": "saved"})

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    socketio.run(app, host=SERVER_HOST, port=SERVER_PORT)