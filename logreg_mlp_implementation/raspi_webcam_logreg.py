# ============================================================
# Raspberry Pi Engagement Detection - LOGISTIC REGRESSION
# ============================================================

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
import numpy as np

# ============================================================
# GLOBAL CONFIG
# ============================================================

BASE_FOLDER = "/home/elvindo/Documents/pi/Day2"
MODEL_PATH  = "v3_logreg_engagement.pkl"
SCALER_PATH = "v3_scaler_engagement.pkl"
PCA_PATH    = "v3_pca_engagement.pkl"

csv_file_path = None
video_writer = None
stop_recording = False

# ============================================================
# LOAD MODEL COMPONENTS
# ============================================================

model  = joblib.load(MODEL_PATH)
scaler = joblib.load(SCALER_PATH)
pca    = joblib.load(PCA_PATH)

print("[OK] Logistic Regression, Scaler, PCA loaded")

# ============================================================
# MEDIAPIPE INIT
# ============================================================

mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(
    static_image_mode=False,
    max_num_faces=1,
    refine_landmarks=True,
    min_detection_confidence=0.5,
    min_tracking_confidence=0.5
)

# ============================================================
# UTILITY
# ============================================================

def format_timestamp(ts):
    return time.strftime("%H:%M:%S", time.localtime(ts))


def engagement_label(level):
    return {
        0: ("Very Low", (0, 0, 255)),
        1: ("Low", (0, 165, 255)),
        2: ("High", (0, 255, 255)),
        3: ("Very High", (0, 255, 0))
    }.get(level, ("Unknown", (200, 200, 200)))

# ============================================================
# SESSION HANDLER
# ============================================================

def start_session(selected_date):
    global csv_file_path, video_writer, stop_recording
    stop_recording = False

    session_folder = os.path.join(BASE_FOLDER, f"session_{selected_date}")
    os.makedirs(session_folder, exist_ok=True)

    engagement_dir = os.path.join(session_folder, "engagement")
    for i in range(4):
        os.makedirs(os.path.join(engagement_dir, str(i)), exist_ok=True)

    csv_file_path = os.path.join(session_folder, "engagement_results.csv")
    with open(csv_file_path, "w", newline="") as f:
        writer = csv.writer(f)
        writer.writerow([
            "Timestamp", "Time", "Frame",
            "Engagement", "Confidence", "FPS"
        ])

    video_writer = cv2.VideoWriter(
        os.path.join(session_folder, "session_video.mp4"),
        cv2.VideoWriter_fourcc(*"mp4v"),
        10, (640, 480)
    )

    capture_webcam(session_folder)


# ============================================================
# CAMERA LOOP
# ============================================================

def capture_webcam(session_folder):
    global stop_recording

    cap = cv2.VideoCapture(0)

    win = tk.Toplevel()
    win.title("Engagement Detection - Logistic Regression")
    win.geometry("760x620")

    video_label = tk.Label(win)
    video_label.pack()

    tk.Button(
        win, text="STOP SESSION",
        font=("Arial", 12, "bold"),
        bg="red", fg="white",
        command=lambda: stop_camera(win)
    ).pack(pady=10)

    def update_frame():
        nonlocal cap

        if stop_recording:
            return

        start = time.time()
        ret, frame = cap.read()
        if not ret:
            return

        timestamp = int(time.time())
        frame_name = f"frame_{timestamp}.jpg"

        level, conf = classify_frame(frame, frame_name, session_folder)
        fps = 1 / (time.time() - start)

        label_text, color = engagement_label(level)

        # Overlay UI
        cv2.rectangle(frame, (0, 0), (640, 90), (30, 30, 30), -1)
        cv2.putText(frame, f"Model : Logistic Regression",
                    (10, 25), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (200, 200, 200), 2)
        cv2.putText(frame, f"Engagement : {label_text}",
                    (10, 55), cv2.FONT_HERSHEY_SIMPLEX, 0.8, color, 2)
        cv2.putText(frame, f"Confidence : {conf:.2f} | FPS : {fps:.1f}",
                    (10, 80), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (255, 255, 255), 2)

        with open(csv_file_path, "a", newline="") as f:
            csv.writer(f).writerow([
                timestamp, format_timestamp(timestamp),
                frame_name, level, conf, fps
            ])

        video_writer.write(frame)

        img = ImageTk.PhotoImage(Image.fromarray(cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)))
        video_label.configure(image=img)
        video_label.image = img

        win.after(10, update_frame)

    update_frame()
    win.mainloop()

    cap.release()
    video_writer.release()
    cv2.destroyAllWindows()
    show_report()


# ============================================================
# FRAME CLASSIFICATION
# ============================================================

def classify_frame(frame, frame_name, session_folder):
    rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = face_mesh.process(rgb)

    if not result.multi_face_landmarks:
        return -1, 0.0

    landmarks = result.multi_face_landmarks[0].landmark
    features = np.array([[lm.x, lm.y] for lm in landmarks]).flatten()

    if features.shape[0] != 936:
        return -1, 0.0

    features = scaler.transform([features])
    features = pca.transform(features)

    probs = model.predict_proba(features)[0]
    level = int(np.argmax(probs))
    conf = float(np.max(probs))

    save_dir = os.path.join(session_folder, "engagement", str(level))
    cv2.imwrite(os.path.join(save_dir, frame_name), frame)

    return level, conf


# ============================================================
# STOP & REPORT
# ============================================================

def stop_camera(win):
    global stop_recording
    stop_recording = True
    win.destroy()


def show_report():
    counts = {str(i): 0 for i in range(4)}

    with open(csv_file_path) as f:
        reader = csv.DictReader(f)
        for r in reader:
            if r["Engagement"] in counts:
                counts[r["Engagement"]] += 1

    low = counts["0"] + counts["1"]
    high = counts["2"] + counts["3"]

    result = "LOW ENGAGEMENT" if low > high else "HIGH ENGAGEMENT"

    messagebox.showinfo(
        "Session Result",
        f"""
Engagement Summary:
0 : {counts['0']}
1 : {counts['1']}
2 : {counts['2']}
3 : {counts['3']}

FINAL RESULT:
{result}
"""
    )

# ============================================================
# MAIN UI
# ============================================================

root = tk.Tk()
root.title("Engagement Detection System")
root.geometry("400x320")

tk.Label(root, text="Select Session Date", font=("Arial", 12)).pack(pady=10)
calendar = Calendar(root, date_pattern="yyyy-mm-dd")
calendar.pack(pady=10)

tk.Button(
    root, text="START SESSION",
    font=("Arial", 12, "bold"),
    bg="green", fg="white",
    command=lambda: start_session(calendar.get_date())
).pack(pady=20)

root.mainloop()