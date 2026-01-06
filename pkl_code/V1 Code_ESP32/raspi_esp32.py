# Code raspi for connect with ESP32 camera module and upload to the server

from flask import Flask, request
import os
import time
import cv2
import mediapipe as mp
import joblib
import csv
import asyncio
import websockets
import json

# ============================================================
# FLASK APP
# ============================================================
app = Flask(__name__)

# ============================================================
# CONFIG
# ============================================================
BASE_FOLDER = "/home/elvindo/raspi-engagement/esp32_data"
WS_SERVER = "ws://10.34.3.210:8000"

os.makedirs(BASE_FOLDER, exist_ok=True)

# ============================================================
# SESSION STATE
# ============================================================
CURRENT_RESPONDEN = None
CURRENT_SESI = None
CSV_PATH = None
SESSION_FOLDER = None

# ============================================================
# MEDIAPIPE & MODEL
# ============================================================
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1
)

model = joblib.load("Fix_kan.pkl")

# ============================================================
# WEBSOCKET SEND (SAME AS WEBCAM VERSION)
# ============================================================
async def ws_send(payload):
    try:
        async with websockets.connect(WS_SERVER) as ws:
            await ws.send(json.dumps(payload))
            await ws.recv()
    except Exception as e:
        print("⚠️ WS error:", e)

# ============================================================
# CLASSIFICATION
# ============================================================
def classify_frame(image_path):
    frame = cv2.imread(image_path)
    if frame is None:
        return -1, 0.0

    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = face_mesh.process(rgb)

    level, conf = -1, 0.0

    if result.multi_face_landmarks:
        lm = result.multi_face_landmarks[0]
        vec = []
        for p in lm.landmark:
            vec.extend([p.x, p.y])

        if len(vec) == 936:
            probs = model.predict_proba([vec])[0]
            level = int(model.predict([vec])[0])
            conf = float(max(probs))

            save_dir = os.path.join(
                SESSION_FOLDER, "engagement", str(level)
            )
            cv2.imwrite(
                os.path.join(save_dir, os.path.basename(image_path)),
                frame
            )

    return level, conf

# ============================================================
# API: START SESSION (OPTIONAL)
# ============================================================
@app.route("/start_new_session", methods=["GET"])
def start_new_session():
    global CURRENT_RESPONDEN, CURRENT_SESI, CSV_PATH, SESSION_FOLDER

    CURRENT_RESPONDEN = request.args.get("responden")
    CURRENT_SESI = request.args.get("sesi")

    if not CURRENT_RESPONDEN or not CURRENT_SESI:
        return "Missing responden or sesi", 400

    SESSION_FOLDER = os.path.join(
        BASE_FOLDER, f"session_{CURRENT_SESI}_{CURRENT_RESPONDEN}"
    )

    os.makedirs(SESSION_FOLDER, exist_ok=True)
    for lvl in ["0", "1", "2", "3"]:
        os.makedirs(os.path.join(SESSION_FOLDER, "engagement", lvl), exist_ok=True)

    CSV_PATH = os.path.join(SESSION_FOLDER, "engagement_results.csv")

    with open(CSV_PATH, "w", newline="") as f:
        csv.writer(f).writerow([
            "timestamp_unix",
            "frame",
            "engagement_level",
            "confidence",
            "response_time",
            "fps"
        ])

    return "Session initialized", 200

# ============================================================
# API: RECEIVE FRAME FROM ESP32
# ============================================================
@app.route("/upload_frame", methods=["POST"])
def upload_frame():
    global CURRENT_RESPONDEN, CURRENT_SESI, CSV_PATH, SESSION_FOLDER

    if CURRENT_RESPONDEN is None or CURRENT_SESI is None:
        CURRENT_RESPONDEN = request.headers.get("X-Responden", "unknown")
        CURRENT_SESI = request.headers.get("X-Sesi", "default")

        SESSION_FOLDER = os.path.join(
            BASE_FOLDER, f"session_{CURRENT_SESI}_{CURRENT_RESPONDEN}"
        )
        os.makedirs(SESSION_FOLDER, exist_ok=True)
        for lvl in ["0", "1", "2", "3"]:
            os.makedirs(os.path.join(SESSION_FOLDER, "engagement", lvl), exist_ok=True)

        CSV_PATH = os.path.join(SESSION_FOLDER, "engagement_results.csv")
        if not os.path.exists(CSV_PATH):
            with open(CSV_PATH, "w", newline="") as f:
                csv.writer(f).writerow([
                    "timestamp_unix",
                    "frame",
                    "engagement_level",
                    "confidence",
                    "response_time",
                    "fps"
                ])

    filename = request.headers.get(
        "X-Filename", f"frame_{int(time.time()*1000)}.jpg"
    )

    frame_path = os.path.join(SESSION_FOLDER, filename)

    start = time.time()
    with open(frame_path, "wb") as f:
        f.write(request.data)

    level, conf = classify_frame(frame_path)

    rt = time.time() - start
    fps = 1 / rt if rt > 0 else 0

    with open(CSV_PATH, "a", newline="") as f:
        csv.writer(f).writerow([
            int(time.time()*1000),
            filename,
            level,
            conf,
            rt,
            fps
        ])

    payload = {
        "responden": CURRENT_RESPONDEN,
        "sesi": CURRENT_SESI,
        "frame": filename,
        "engagement_level": int(level),
        "fps": fps,
        "response_time": rt
    }

    asyncio.run(ws_send(payload))

    return "OK", 200

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)