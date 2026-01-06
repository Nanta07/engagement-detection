import os
import time
import csv
import serial
import struct
import threading
import cv2
import mediapipe as mp
import joblib
import requests
import tkinter as tk
from tkinter import messagebox
from tkcalendar import Calendar
from PIL import Image, ImageTk
import numpy as np

# ============================================================
# CONFIG
# ============================================================
BASE_FOLDER = "/home/elvindo/raspi-engagement/data"
SERIAL_PORT = "/dev/ttyUSB0"
BAUDRATE = 115200

SERVER_IP = "10.201.65.218"
SERVER_PORT = 8000

CURRENT_RESPONDEN = "esp32_user"
CURRENT_SESI = None

SESSION_ACTIVE = False
STOP_RECORDING = False

csv_file_path = None

os.makedirs(BASE_FOLDER, exist_ok=True)

# ============================================================
# MODEL & MEDIAPIPE
# ============================================================
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1
)

rf_model = joblib.load("Fix_kan.pkl")

# ============================================================
# SERIAL
# ============================================================
ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=1)

def read_frame():
    while True:
        if ser.read(1) == b'\xAA' and ser.read(1) == b'\x55':
            size = struct.unpack("<I", ser.read(4))[0]
            data = ser.read(size)
            if len(data) == size:
                return data

# ============================================================
# SERVER
# ============================================================
def send_result_to_server(payload):
    try:
        requests.post(
            f"http://{SERVER_IP}:{SERVER_PORT}/upload_result",
            json=payload,
            timeout=3
        )
    except:
        pass

def format_timestamp(ts):
    return time.strftime("%H:%M:%S", time.localtime(ts))

# ============================================================
# CLASSIFICATION
# ============================================================
def classify_frame(frame, frame_name, session_folder):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = face_mesh.process(rgb)

    level = -1
    confidence = 0.0

    if result.multi_face_landmarks:
        vec = []
        for lm in result.multi_face_landmarks[0].landmark:
            vec.extend([lm.x, lm.y])

        if len(vec) == 936:
            probs = rf_model.predict_proba([vec])[0]
            level = int(rf_model.predict([vec])[0])
            confidence = max(probs)

            save_dir = os.path.join(
                session_folder, "engagement", str(level)
            )
            cv2.imwrite(os.path.join(save_dir, frame_name), frame)

    return level, confidence

# ============================================================
# SESSION LOOP
# ============================================================
def serial_loop(label):
    global SESSION_ACTIVE, STOP_RECORDING

    while True:
        jpeg = read_frame()
        if not SESSION_ACTIVE or STOP_RECORDING:
            continue

        start = time.time()
        ts = int(time.time())
        frame_name = f"frame_{ts}.jpg"

        frame = cv2.imdecode(
            np.frombuffer(jpeg, np.uint8),
            cv2.IMREAD_COLOR
        )

        level, confidence = classify_frame(
            frame, frame_name, SESSION_FOLDER
        )

        response_time = time.time() - start
        fps = 1 / response_time if response_time > 0 else 0

        with open(csv_file_path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                ts,
                format_timestamp(ts),
                frame_name,
                level,
                confidence,
                response_time,
                fps
            ])

        send_result_to_server({
            "responden": CURRENT_RESPONDEN,
            "sesi": CURRENT_SESI,
            "frame": frame_name,
            "engagement_level": int(level),
            "fps": fps,
            "response_time": response_time
        })

        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = ImageTk.PhotoImage(Image.fromarray(rgb))
        label.configure(image=img)
        label.image = img

# ============================================================
# SESSION CONTROL
# ============================================================
def start_session(selected_date, label):
    global CURRENT_SESI, SESSION_ACTIVE, STOP_RECORDING
    global csv_file_path, SESSION_FOLDER

    STOP_RECORDING = False
    SESSION_ACTIVE = True
    CURRENT_SESI = selected_date

    SESSION_FOLDER = os.path.join(BASE_FOLDER, f"sesi_{selected_date}")
    os.makedirs(SESSION_FOLDER, exist_ok=True)

    engagement_folder = os.path.join(SESSION_FOLDER, "engagement")
    for lvl in ["0", "1", "2", "3"]:
        os.makedirs(os.path.join(engagement_folder, lvl), exist_ok=True)

    csv_file_path = os.path.join(
        SESSION_FOLDER, "engagement_results.csv"
    )

    with open(csv_file_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "timestamp",
            "time",
            "frame",
            "engagement_level",
            "confidence",
            "response_time",
            "fps"
        ])

    threading.Thread(
        target=serial_loop,
        args=(label,),
        daemon=True
    ).start()

def stop_session(window):
    global STOP_RECORDING, SESSION_ACTIVE
    STOP_RECORDING = True
    SESSION_ACTIVE = False
    window.destroy()
    messagebox.showinfo("Session", "Session selesai")

# ============================================================
# UI
# ============================================================
root = tk.Tk()
root.title("ESP32 Engagement Session")

calendar = Calendar(root, date_pattern="yyyy-mm-dd")
calendar.pack(pady=10)

preview_label = tk.Label(root)
preview_label.pack()

tk.Button(
    root,
    text="Start Session",
    command=lambda: start_session(
        calendar.get_date(), preview_label
    )
).pack(pady=10)

tk.Button(
    root,
    text="Stop Session",
    command=lambda: stop_session(root)
).pack(pady=10)

root.mainloop()