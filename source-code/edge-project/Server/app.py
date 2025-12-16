from flask import Flask, request, jsonify
import os
import csv
from datetime import datetime

app = Flask(__name__)

BASE_DIR = "data"
LOG_DIR = os.path.join(BASE_DIR, "logs")
SESSION_DIR = os.path.join(BASE_DIR, "sessions")

os.makedirs(LOG_DIR, exist_ok=True)
os.makedirs(SESSION_DIR, exist_ok=True)

GLOBAL_LOG = os.path.join(LOG_DIR, "engagement_log.csv")

# Init global log
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


@app.route("/")
def home():
    return "Engagement Server Running"


@app.route("/upload_result", methods=["POST"])
def upload_result():
    data = request.json

    responden = data.get("responden")
    sesi = data.get("sesi")
    frame = data.get("frame")
    engagement = data.get("engagement_level")
    fps = data.get("fps")
    response_time = data.get("response_time")

    timestamp = datetime.now().isoformat()

    # Folder per session
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

    return jsonify({"status": "saved"}), 200


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8000)