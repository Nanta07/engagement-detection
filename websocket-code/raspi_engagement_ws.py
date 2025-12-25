import asyncio
import websockets
import json
import os
import time
import cv2
import csv
import joblib
import mediapipe as mp
import tkinter as tk
from tkinter import messagebox
from tkcalendar import Calendar
from PIL import Image, ImageTk

# ============================================================
# CONFIG
# ============================================================
BASE_FOLDER = "/home/elvindo/raspi-engagement/data"
WS_SERVER = "ws://10.34.3.209:8000"

RESPONDEN = "webcam_user"
CURRENT_SESI = None

os.makedirs(BASE_FOLDER, exist_ok=True)

# ============================================================
# MODEL
# ============================================================
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1)
model = joblib.load("Fix_kan.pkl")

# ============================================================
# WEBSOCKET (ASYNC SAFE)
# ============================================================
async def ws_send(payload):
    async with websockets.connect(WS_SERVER) as ws:
        await ws.send(json.dumps(payload))
        await ws.recv()   # tunggu "ok" dari server

# ============================================================
# CLASSIFICATION
# ============================================================
def classify(frame):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    res = face_mesh.process(rgb)

    level, conf = -1, 0.0

    if res.multi_face_landmarks:
        lm = res.multi_face_landmarks[0]
        vec = []
        for p in lm.landmark:
            vec.extend([p.x, p.y])

        if len(vec) == 936:
            probs = model.predict_proba([vec])[0]
            level = int(model.predict([vec])[0])
            conf = max(probs)

    return level, conf

# ============================================================
# CAMERA LOOP
# ============================================================
def start_capture(session_folder, csv_path):
    cap = cv2.VideoCapture(0)

    win = tk.Toplevel()
    label = tk.Label(win)
    label.pack()

    stop_flag = {"stop": False}

    def stop():
        stop_flag["stop"] = True
        win.destroy()

    tk.Button(win, text="Stop Session", command=stop).pack()

    def update():
        if stop_flag["stop"]:
            cap.release()
            return

        ret, frame = cap.read()
        if not ret:
            return

        start = time.time()
        ts = int(time.time())
        fname = f"frame_{ts}.jpg"

        level, conf = classify(frame)
        rt = time.time() - start
        fps = 1 / rt if rt > 0 else 0

        # save CSV lokal
        with open(csv_path, "a", newline="") as f:
            csv.writer(f).writerow([ts, fname, level, conf, fps, rt])

        # send to server (ASYNC BUT SAFE)
        payload = {
            "responden": RESPONDEN,
            "sesi": CURRENT_SESI,
            "frame": fname,
            "engagement_level": int(level),
            "fps": fps,
            "response_time": rt
        }
        asyncio.run(ws_send(payload))

        img = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
        label.config(image=img)
        label.image = img

        win.after(50, update)

    update()
    win.mainloop()

# ============================================================
# SESSION
# ============================================================
def start_session(date):
    global CURRENT_SESI
    CURRENT_SESI = date

    session_folder = os.path.join(BASE_FOLDER, f"sesi_{date}")
    os.makedirs(session_folder, exist_ok=True)

    csv_path = os.path.join(session_folder, "engagement.csv")
    with open(csv_path, "w", newline="") as f:
        csv.writer(f).writerow([
            "timestamp","frame","level","confidence","fps","response_time"
        ])

    start_capture(session_folder, csv_path)

# ============================================================
# UI
# ============================================================
root = tk.Tk()
root.title("Engagement Detection")

cal = Calendar(root, date_pattern="yyyy-mm-dd")
cal.pack(pady=10)

tk.Button(root, text="Start Session",
          command=lambda: start_session(cal.get_date())).pack(pady=20)

root.mainloop()