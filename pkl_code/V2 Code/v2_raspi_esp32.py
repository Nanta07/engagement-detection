from flask import Flask, request, send_file
import os
import time
import cv2
import mediapipe as mp
import joblib
import csv
import zipfile
import requests
import shutil

# ============================================================
# FLASK
# ============================================================
app = Flask(__name__)

# ============================================================
# CONFIG
# ============================================================
BASE_FOLDER = "/home/elvindo/raspi-engagement/esp32_data"
UPLOAD_SERVER = "http://10.34.3.210:8000/upload_session"

os.makedirs(BASE_FOLDER, exist_ok=True)

# ============================================================
# SESSION STATE
# ============================================================
CURRENT_SESSION = None

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
# SESSION CLASS
# ============================================================
class Session:
    def __init__(self, responden, sesi):
        self.responden = responden
        self.sesi = sesi
        self.start_time = time.time()

        self.root = os.path.join(
            BASE_FOLDER, f"session_{sesi}_{responden}"
        )

        self.frame_dir = os.path.join(self.root, "frames")
        self.engagement_dir = os.path.join(self.root, "engagement")

        os.makedirs(self.frame_dir, exist_ok=True)
        for lvl in ["0", "1", "2", "3"]:
            os.makedirs(os.path.join(self.engagement_dir, lvl), exist_ok=True)

        self.csv_path = os.path.join(self.root, "results.csv")
        with open(self.csv_path, "w", newline="") as f:
            csv.writer(f).writerow([
                "timestamp",
                "frame",
                "engagement_level",
                "confidence",
                "response_time",
                "fps"
            ])

    def classify(self, image_path):
        start = time.time()

        frame = cv2.imread(image_path)
        if frame is None:
            return -1, 0.0, 0, 0

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

                cv2.imwrite(
                    os.path.join(
                        self.engagement_dir, str(level),
                        os.path.basename(image_path)
                    ),
                    frame
                )

        rt = time.time() - start
        fps = 1 / rt if rt > 0 else 0
        return level, conf, rt, fps

    def log(self, filename, level, conf, rt, fps):
        with open(self.csv_path, "a", newline="") as f:
            csv.writer(f).writerow([
                int(time.time() * 1000),
                filename,
                level,
                conf,
                rt,
                fps
            ])

    def zip_and_upload(self):
        zip_path = self.root + ".zip"

        with zipfile.ZipFile(zip_path, "w", zipfile.ZIP_DEFLATED) as z:
            for folder, _, files in os.walk(self.root):
                for file in files:
                    full = os.path.join(folder, file)
                    z.write(full, arcname=os.path.relpath(full, self.root))

        with open(zip_path, "rb") as f:
            requests.post(
                UPLOAD_SERVER,
                files={"file": f},
                data={
                    "responden": self.responden,
                    "sesi": self.sesi
                }
            )

        shutil.rmtree(self.root)
        os.remove(zip_path)

# ============================================================
# API: RECEIVE FRAME
# ============================================================
@app.route("/upload_frame", methods=["POST"])
def upload_frame():
    global CURRENT_SESSION

    responden = request.headers.get("X-Responden", "unknown")
    sesi = request.headers.get("X-Sesi", "default")
    filename = request.headers.get(
        "X-Filename", f"{int(time.time()*1000)}.jpg"
    )

    if CURRENT_SESSION is None:
        CURRENT_SESSION = Session(responden, sesi)

    frame_path = os.path.join(CURRENT_SESSION.frame_dir, filename)
    with open(frame_path, "wb") as f:
        f.write(request.data)

    level, conf, rt, fps = CURRENT_SESSION.classify(frame_path)
    CURRENT_SESSION.log(filename, level, conf, rt, fps)

    return "OK", 200

# ============================================================
# API: STOP SESSION
# ============================================================
@app.route("/stop_session", methods=["POST"])
def stop_session():
    global CURRENT_SESSION

    if CURRENT_SESSION is None:
        return "No active session", 400

    CURRENT_SESSION.zip_and_upload()
    CURRENT_SESSION = None

    return "SESSION FINISHED & UPLOADED", 200

# ============================================================
# MAIN
# ============================================================
if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)