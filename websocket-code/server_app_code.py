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
    return "Engagement Server Running", 200


@app.route("/health")
def health():
    return jsonify({"status": "ok"}), 200


@app.route("/upload_result", methods=["POST"])
def upload_result():
    # ===============================
    # SAFE JSON PARSING
    # ===============================
    data = request.get_json(force=True, silent=True)
    if not data:
        return jsonify({"error": "Invalid or empty JSON"}), 400

    # ===============================
    # SAFE DATA EXTRACTION
    # ===============================
    responden = data.get("responden", "unknown")
    sesi = data.get("sesi", "unknown")
    frame = data.get("frame", "")
    engagement = data.get("engagement_level", -1)
    fps = data.get("fps", 0)
    response_time = data.get("response_time", 0)

    timestamp = datetime.now().isoformat()

    # ===============================
    # SESSION FOLDER
    # ===============================
    session_path = os.path.join(
        SESSION_DIR,
        f"responden_{responden}",
        f"sesi_{sesi}"
    )
    os.makedirs(session_path, exist_ok=True)

    session_csv = os.path.join(session_path, "results.csv")

    # ===============================
    # INIT SESSION CSV
    # ===============================
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

    # ===============================
    # WRITE SESSION CSV
    # ===============================
    with open(session_csv, "a", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            timestamp,
            frame,
            engagement,
            fps,
            response_time
        ])

    # ===============================
    # WRITE GLOBAL CSV
    # ===============================
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


# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    print("🚀 Engagement Server starting...")
    print(f"📡 Listening on {SERVER_HOST}:{SERVER_PORT}")
    app.run(host=SERVER_HOST, port=SERVER_PORT)