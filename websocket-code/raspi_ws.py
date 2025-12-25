#Deploy WebSocket Client on Raspberry Pi to capture webcam video, classify engagement level, and send data to server
import os
import time
import cv2
import csv
import json
import joblib
import mediapipe as mp
import tkinter as tk
from tkinter import messagebox
from tkcalendar import Calendar
from PIL import Image, ImageTk
from websocket import create_connection

# ============================================================
# CONFIG
# ============================================================
BASE_FOLDER = "/home/elvindo/raspi-engagement/data"
WS_SERVER = "ws://10.201.65.218:8000"

CURRENT_RESPONDEN = "webcam_user"
CURRENT_SESI = None

csv_file_path = None
video_writer = None
stop_recording = False
ws = None

os.makedirs(BASE_FOLDER, exist_ok=True)

# ============================================================
# MODEL
# ============================================================
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(max_num_faces=1)
rf_model = joblib.load("Fix_kan.pkl")

# ============================================================
# WEBSOCKET
# ============================================================
def init_ws():
    global ws
    ws = create_connection(WS_SERVER)
    print("✅ Connected to WebSocket Server")

def send_ws(payload):
    try:
        ws.send(json.dumps(payload))
    except:
        pass

# ============================================================
# SESSION
# ============================================================
def start_session(date):
    global CURRENT_SESI, csv_file_path, video_writer, stop_recording

    init_ws()
    CURRENT_SESI = date
    stop_recording = False

    session_folder = os.path.join(BASE_FOLDER, f"sesi_{date}")
    os.makedirs(session_folder, exist_ok=True)

    for lvl in ["0","1","2","3"]:
        os.makedirs(os.path.join(session_folder, "engagement", lvl), exist_ok=True)

    csv_file_path = os.path.join(session_folder, "engagement_results.csv")
    with open(csv_file_path, "w", newline="") as f:
        csv.writer(f).writerow([
            "timestamp","frame","level","confidence","fps","response_time"
        ])

    video_writer = cv2.VideoWriter(
        os.path.join(session_folder, "session_video.mp4"),
        cv2.VideoWriter_fourcc(*"mp4v"),
        10,(640,480)
    )

    capture(session_folder)

# ============================================================
# CAMERA LOOP
# ============================================================
def capture(folder):
    global stop_recording
    cap = cv2.VideoCapture(0)

    win = tk.Toplevel()
    label = tk.Label(win)
    label.pack()

    def update():
        if stop_recording:
            return

        ret, frame = cap.read()
        if not ret:
            return

        ts = int(time.time())
        start = time.time()
        fname = f"frame_{ts}.jpg"

        level, conf = classify(frame, fname, folder)
        rt = time.time() - start
        fps = 1/rt if rt > 0 else 0

        with open(csv_file_path,"a",newline="") as f:
            csv.writer(f).writerow([ts,fname,level,conf,fps,rt])

        video_writer.write(frame)

        send_ws({
            "type": "engagement",
            "responden": CURRENT_RESPONDEN,
            "sesi": CURRENT_SESI,
            "frame": fname,
            "engagement_level": int(level),
            "fps": fps,
            "response_time": rt,
            "timestamp": ts
        })

        img = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(frame,cv2.COLOR_BGR2RGB)))
        label.config(image=img)
        label.image = img

        win.after(10, update)

    update()
    win.mainloop()

    cap.release()
    video_writer.release()

# ============================================================
# CLASSIFY
# ============================================================
def classify(frame, fname, folder):
    res = face_mesh.process(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
    level, conf = -1, 0

    if res.multi_face_landmarks:
        lm = res.multi_face_landmarks[0]
        vec = [c for p in [(l.x,l.y) for l in lm.landmark] for c in p]

        if len(vec) == 936:
            prob = rf_model.predict_proba([vec])[0]
            level = int(rf_model.predict([vec])[0])
            conf = max(prob)
            cv2.imwrite(os.path.join(folder,"engagement",str(level),fname),frame)

    return level, conf

# ============================================================
# UI
# ============================================================
root = tk.Tk()
cal = Calendar(root, date_pattern="yyyy-mm-dd")
cal.pack()

tk.Button(root, text="Start Session",
          command=lambda: start_session(cal.get_date())).pack()

root.mainloop()