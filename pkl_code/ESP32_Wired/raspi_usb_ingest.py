import serial
import struct
import os
import time
import cv2
import csv
import zipfile
import shutil
import joblib
import mediapipe as mp
from flask import Flask, request

# ===============================
# CONFIG
# ===============================
SERIAL_PORT = "/dev/ttyUSB0"
BAUDRATE = 921600

BASE_FOLDER = "sessions"
MODEL_PATH = "Fix_kan.pkl"

os.makedirs(BASE_FOLDER, exist_ok=True)

# ===============================
# FLASK
# ===============================
app = Flask(__name__)
CURRENT_SESSION = None

# ===============================
# MEDIAPIPE & MODEL
# ===============================
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=1)
model = joblib.load(MODEL_PATH)

# ===============================
# SESSION CLASS
# ===============================
class Session:
    def __init__(self, responden, sesi):
        self.responden = responden
        self.sesi = sesi
        self.root = os.path.join(BASE_FOLDER, f"{responden}_{sesi}")
        self.frame_dir = os.path.join(self.root, "frames")
        self.csv_path = os.path.join(self.root, "results.csv")

        os.makedirs(self.frame_dir, exist_ok=True)

        with open(self.csv_path, "w", newline="") as f:
            csv.writer(f).writerow([
                "timestamp", "frame",
                "engagement", "confidence",
                "response_time", "fps"
            ])

    def classify(self, img_path):
        start = time.time()
        frame = cv2.imread(img_path)
        if frame is None:
            return -1, 0, 0, 0

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        res = face_mesh.process(rgb)

        level, conf = -1, 0
        if res.multi_face_landmarks:
            vec = []
            for p in res.multi_face_landmarks[0].landmark:
                vec.extend([p.x, p.y])

            if len(vec) == 936:
                probs = model.predict_proba([vec])[0]
                level = int(model.predict([vec])[0])
                conf = float(max(probs))

        rt = time.time() - start
        fps = 1 / rt if rt > 0 else 0
        return level, conf, rt, fps

    def log(self, fname, lvl, conf, rt, fps):
        with open(self.csv_path, "a", newline="") as f:
            csv.writer(f).writerow([
                int(time.time()*1000),
                fname, lvl, conf, rt, fps
            ])

# ===============================
# SERIAL READER THREAD
# ===============================
ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)

def read_frame():
    while True:
        if ser.read() == b'\xAA' and ser.read() == b'\x55':
            length = struct.unpack("<I", ser.read(4))[0]
            return ser.read(length)

# ===============================
# FLASK ROUTES
# ===============================
@app.route("/start", methods=["POST"])
def start():
    global CURRENT_SESSION
    data = request.json
    CURRENT_SESSION = Session(
        data["responden"],
        data["sesi"]
    )
    return "SESSION STARTED", 200

@app.route("/stop", methods=["POST"])
def stop():
    global CURRENT_SESSION
    CURRENT_SESSION = None
    return "SESSION STOPPED", 200

# ===============================
# MAIN LOOP
# ===============================
def main_loop():
    global CURRENT_SESSION
    while True:
        jpeg = read_frame()
        if CURRENT_SESSION is None:
            continue

        fname = f"{int(time.time()*1000)}.jpg"
        path = os.path.join(CURRENT_SESSION.frame_dir, fname)

        with open(path, "wb") as f:
            f.write(jpeg)

        lvl, conf, rt, fps = CURRENT_SESSION.classify(path)
        CURRENT_SESSION.log(fname, lvl, conf, rt, fps)

# ===============================
# RUN
# ===============================
if __name__ == "__main__":
    import threading
    threading.Thread(target=main_loop, daemon=True).start()
    app.run(host="0.0.0.0", port=5000)