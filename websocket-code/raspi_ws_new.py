# ============================================================
# Raspberry Pi Engagement Detection (FINAL)
# Webcam: Logitech C270
# Output: CSV + Image per Class + Video
# Server: WebSocket Metadata Only
# ============================================================

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
from tkinter import simpledialog, messagebox
from tkcalendar import Calendar
from PIL import Image, ImageTk

# ============================================================
# CONFIG
# ============================================================
BASE_FOLDER = "/home/elvindo/raspi-engagement/data"
WS_SERVER = "ws://10.34.3.209:8000"

CAMERA_INDEX = 0  # Logitech C270
FPS_VIDEO = 10

os.makedirs(BASE_FOLDER, exist_ok=True)

# ============================================================
# MODEL
# ============================================================
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1
)

model = joblib.load("Fix_kan.pkl")

# ============================================================
# WEBSOCKET (SAFE PER MESSAGE)
# ============================================================
async def ws_send(payload):
    try:
        async with websockets.connect(WS_SERVER) as ws:
            await ws.send(json.dumps(payload))
            await ws.recv()  # expect {"status":"ok"}
    except Exception as e:
        print("⚠️ WS error:", e)

# ============================================================
# CLASSIFICATION
# ============================================================
def classify_frame(frame):
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

    return level, conf

# ============================================================
# CAMERA LOOP
# ============================================================
def start_capture(session_folder, csv_path, responden, sesi_id):
    cap = cv2.VideoCapture(CAMERA_INDEX)

    if not cap.isOpened():
        messagebox.showerror("Camera Error", "Webcam tidak terdeteksi.")
        return

    video_path = os.path.join(session_folder, "session_video.mp4")
    video_writer = cv2.VideoWriter(
        video_path,
        cv2.VideoWriter_fourcc(*"mp4v"),
        FPS_VIDEO,
        (640, 480)
    )

    win = tk.Toplevel()
    win.title("Engagement Detection - Live Preview")

    label = tk.Label(win)
    label.pack()

    stop_flag = {"stop": False}

    def stop():
        stop_flag["stop"] = True
        win.destroy()

    tk.Button(win, text="Stop Session", command=stop).pack(pady=10)

    def update():
        if stop_flag["stop"]:
            cap.release()
            video_writer.release()
            return

        ret, frame = cap.read()
        if not ret:
            return

        start = time.time()
        ts = int(time.time() * 1000)
        frame_name = f"frame_{ts}.jpg"

        level, conf = classify_frame(frame)
        rt = time.time() - start
        fps = 1 / rt if rt > 0 else 0

        # Save image per engagement level
        if level >= 0:
            save_dir = os.path.join(session_folder, "engagement", str(level))
            cv2.imwrite(os.path.join(save_dir, frame_name), frame)

        # Save CSV locally
        with open(csv_path, "a", newline="") as f:
            csv.writer(f).writerow([
                ts,
                time.strftime("%H:%M:%S", time.localtime(ts / 1000)),
                frame_name,
                level,
                conf,
                rt,
                fps
            ])

        # Save video
        video_writer.write(frame)

        # Send metadata to server
        payload = {
            "responden": responden,
            "sesi": sesi_id,
            "frame": frame_name,
            "engagement_level": int(level),
            "fps": fps,
            "response_time": rt
        }
        asyncio.run(ws_send(payload))

        # UI Preview
        img = ImageTk.PhotoImage(
            Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB))
        )
        label.config(image=img)
        label.image = img

        win.after(80, update)

    update()
    win.mainloop()

# ============================================================
# SESSION HANDLER
# ============================================================
def start_session(date):
    responden = simpledialog.askstring(
        "Responden",
        "Masukkan nama responden:"
    )

    if not responden:
        messagebox.showwarning("Input Error", "Nama responden wajib diisi.")
        return

    sesi_id = f"{date}_{responden}"
    session_folder = os.path.join(
        BASE_FOLDER,
        f"session_{sesi_id}"
    )

    os.makedirs(session_folder, exist_ok=True)

    # Engagement folders
    for lvl in ["0", "1", "2", "3"]:
        os.makedirs(os.path.join(session_folder, "engagement", lvl), exist_ok=True)

    csv_path = os.path.join(session_folder, "engagement_results.csv")
    with open(csv_path, "w", newline="") as f:
        csv.writer(f).writerow([
            "timestamp_unix",
            "time_hms",
            "frame_name",
            "engagement_level",
            "confidence",
            "response_time",
            "fps"
        ])

    start_capture(session_folder, csv_path, responden, sesi_id)

# ============================================================
# UI
# ============================================================
root = tk.Tk()
root.title("Raspberry Pi Engagement Detection")

cal = Calendar(root, date_pattern="yyyy-mm-dd")
cal.pack(pady=10)

tk.Button(
    root,
    text="Start Session",
    command=lambda: start_session(cal.get_date())
).pack(pady=20)

root.mainloop()