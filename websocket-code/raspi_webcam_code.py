import os
import time
import cv2
import csv
import requests
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

SERVER_IP = "10.201.65.218"   # GANTI SESUAI IP SERVER
SERVER_PORT = 8000

CURRENT_RESPONDEN = "webcam_user"
CURRENT_SESI = None

csv_file_path = None
video_writer = None
stop_recording = False

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
# NETWORK (SAFE)
# ============================================================
def send_result_to_server(payload):
    try:
        r = requests.post(
            f"http://{SERVER_IP}:{SERVER_PORT}/upload_result",
            json=payload,
            timeout=2
        )
        print("📡 Sent:", r.status_code)
    except Exception as e:
        print("⚠️ Server unreachable (ignored)")

# ============================================================
# UTILS
# ============================================================
def format_time(ts):
    return time.strftime("%H:%M:%S", time.localtime(ts))

# ============================================================
# SESSION
# ============================================================
def start_session(selected_date):
    global csv_file_path, video_writer, stop_recording, CURRENT_SESI

    stop_recording = False
    CURRENT_SESI = selected_date

    session_folder = os.path.join(BASE_FOLDER, f"sesi_{selected_date}")
    os.makedirs(session_folder, exist_ok=True)

    # Engagement folders
    for lvl in ["0", "1", "2", "3"]:
        os.makedirs(os.path.join(session_folder, "engagement", lvl), exist_ok=True)

    csv_file_path = os.path.join(session_folder, "engagement_results.csv")
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

    video_writer = cv2.VideoWriter(
        os.path.join(session_folder, "session_video.mp4"),
        cv2.VideoWriter_fourcc(*"mp4v"),
        10,
        (640, 480)
    )

    capture_webcam(session_folder)

# ============================================================
# CAMERA LOOP
# ============================================================
def capture_webcam(session_folder):
    global stop_recording

    cap = cv2.VideoCapture(0)

    window = tk.Toplevel()
    window.title("Webcam Preview")

    label = tk.Label(window)
    label.pack()

    tk.Button(
        window,
        text="Stop Recording",
        command=lambda: stop_camera(window)
    ).pack(pady=10)

    def update():
        if stop_recording:
            return

        ret, frame = cap.read()
        if not ret:
            window.after(10, update)
            return

        start = time.time()
        ts = int(time.time())
        frame_name = f"frame_{ts}.jpg"

        level, confidence = classify_frame(frame, frame_name, session_folder)

        response_time = time.time() - start
        fps = 1 / response_time if response_time > 0 else 0

        # SAVE CSV LOCAL
        with open(csv_file_path, "a", newline="") as f:
            writer = csv.writer(f)
            writer.writerow([
                ts,
                format_time(ts),
                frame_name,
                level,
                confidence,
                response_time,
                fps
            ])

        video_writer.write(frame)

        # SEND METADATA
        send_result_to_server({
            "responden": CURRENT_RESPONDEN,
            "sesi": CURRENT_SESI,
            "frame": frame_name,
            "engagement_level": level,
            "fps": fps,
            "response_time": response_time
        })

        # PREVIEW
        rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = ImageTk.PhotoImage(Image.fromarray(rgb))
        label.configure(image=img)
        label.image = img

        window.after(10, update)

    update()
    window.mainloop()

    cap.release()
    video_writer.release()

# ============================================================
# STOP & REPORT
# ============================================================
def stop_camera(window):
    global stop_recording
    stop_recording = True
    window.destroy()
    messagebox.showinfo("Session", "Session selesai")

# ============================================================
# CLASSIFICATION
# ============================================================
def classify_frame(frame, frame_name, session_folder):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = face_mesh.process(rgb)

    level = -1
    confidence = 0.0

    if result.multi_face_landmarks:
        face = result.multi_face_landmarks[0]
        landmarks = [(lm.x, lm.y) for lm in face.landmark]
        vector = [c for p in landmarks for c in p]

        if len(vector) == 936:
            probs = rf_model.predict_proba([vector])[0]
            level = int(rf_model.predict([vector])[0])
            confidence = max(probs)

            save_dir = os.path.join(
                session_folder, "engagement", str(level)
            )
            cv2.imwrite(os.path.join(save_dir, frame_name), frame)

    return level, confidence

# ============================================================
# UI
# ============================================================
root = tk.Tk()
root.title("Engagement Detection")

calendar = Calendar(root, date_pattern="yyyy-mm-dd")
calendar.pack(pady=10)

tk.Button(
    root,
    text="Start Session",
    command=lambda: start_session(calendar.get_date())
).pack(pady=20)

root.mainloop()