from flask import Flask, request, jsonify
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
# ROUTES
# ============================================================
@app.route("/")
def home():
    return "Engagement Server Running"

@app.route("/upload_result", methods=["POST"])
def upload_result():
    data = request.get_json(force=True)

    responden = data["responden"]
    sesi = data["sesi"]
    frame = data["frame"]
    engagement = data["engagement_level"]
    fps = data["fps"]
    response_time = data["response_time"]

    timestamp = datetime.now().isoformat()

    # Folder per responden & sesi
    session_path = os.path.join(
        SESSION_DIR,
        f"responden_{responden}",
        f"sesi_{sesi}"
    )
    os.makedirs(session_path, exist_ok=True)

    session_csv = os.path.join(session_path, "results.csv")

    # Init session CSV
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

    # Append session CSV
    with open(session_csv, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            timestamp,
            frame,
            engagement,
            fps,
            response_time
        ])

    # Append global CSV
    with open(GLOBAL_LOG, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            timestamp,
            responden,
            sesi,
            frame,
            engagement,
            fps,
            response_time
        ])

    return jsonify({"status": "ok"}), 200

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    app.run(host=SERVER_HOST, port=SERVER_PORT, debug=True)