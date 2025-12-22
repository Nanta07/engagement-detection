import os
import time
import cv2
import mediapipe as mp
import joblib
import csv
import tkinter as tk
from tkinter import filedialog, messagebox

base_folder = '/home/elvindo/Documents/pi/Day3'
csv_file_path = None

# Inisialisasi MediaPipe dan model klasifikasi
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=5)
rf_model = joblib.load('(Facial_Landmark)_random_forest_engagement_model.pkl')  # Ganti dengan path model Anda

def start_session(responden, sesi, video_path):
    global csv_file_path

    # Buat folder untuk responden jika belum ada
    responden_folder = os.path.join(base_folder, f"responden_{responden}")
    os.makedirs(responden_folder, exist_ok=True)

    # Buat folder sesi di dalam folder responden
    session_folder = os.path.join(responden_folder, f"sesi_{sesi}")
    os.makedirs(session_folder, exist_ok=True)

    # Buat folder engagement (0, 1, 2, 3) di dalam folder sesi
    engagement_folder = os.path.join(session_folder, "engagement")
    for level in ["0", "1", "2", "3"]:
        os.makedirs(os.path.join(engagement_folder, level), exist_ok=True)

    # Tentukan path file CSV baru untuk sesi ini
    csv_file_path = os.path.join(session_folder, "engagement_results.csv")
    with open(csv_file_path, mode='w', newline='') as file:
        writer = csv.writer(file)
        writer.writerow(["Timestamp", "Frame Name", "Engagement Level", "Response Time", "FPS"])

    # Mulai proses klasifikasi frame dari video
    process_video_frames(video_path, session_folder)

def process_video_frames(video_path, session_folder):
    cap = cv2.VideoCapture(video_path)  # Membuka file video yang dipilih

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        start_time = time.time()
        timestamp = int(time.time())
        frame_name = f"frame_{timestamp}.jpg"

        # Lakukan klasifikasi pada frame yang diambil
        engagement_level = process_and_classify_frame(frame, frame_name, session_folder)

        # Hitung waktu respons dan FPS
        response_time = time.time() - start_time
        fps = 1 / response_time if response_time > 0 else 0

        # Tulis hasil klasifikasi ke CSV
        with open(csv_file_path, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, frame_name, engagement_level, response_time, fps])

    cap.release()
    cv2.destroyAllWindows()

def process_and_classify_frame(frame, frame_name, session_folder):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = face_mesh.process(rgb_frame)
    engagement_level = -1

    if result.multi_face_landmarks:
        for face_landmarks in result.multi_face_landmarks:
            landmarks = [(lm.x, lm.y) for lm in face_landmarks.landmark]
            flattened = [coord for point in landmarks for coord in point]

            if len(flattened) == 468 * 2:
                engagement_level = rf_model.predict([flattened])[0]

                # Simpan frame berdasarkan level engagement
                engagement_folder = os.path.join(session_folder, "engagement", str(engagement_level))
                cv2.imwrite(os.path.join(engagement_folder, frame_name), frame)

    return engagement_level

# Fungsi untuk memilih file video menggunakan Tkinter file dialog
def select_video_file():
    file_path = filedialog.askopenfilename(title="Select Video File", filetypes=[("Video Files", "*.mp4 *.avi *.mov")])
    return file_path

# Fungsi untuk memulai sesi dari input UI
def start_session_ui():
    responden = entry_responden.get()
    sesi = entry_sesi.get()
    video_path = select_video_file()

    if not responden or not sesi or not video_path:
        messagebox.showwarning("Input Error", "Responden ID, Sesi ID, dan video file tidak boleh kosong!")
        return

    start_session(responden, sesi, video_path)
    messagebox.showinfo("Session Started", f"Session started for Responden {responden} Sesi {sesi}")

# Inisialisasi UI Tkinter
root = tk.Tk()
root.title("Start Video Session")
root.geometry("300x200")

# Label dan Entry untuk ID responden
label_responden = tk.Label(root, text="Responden ID:")
label_responden.pack(pady=5)
entry_responden = tk.Entry(root)
entry_responden.pack(pady=5)

# Label dan Entry untuk ID sesi
label_sesi = tk.Label(root, text="Sesi ID:")
label_sesi.pack(pady=5)
entry_sesi = tk.Entry(root)
entry_sesi.pack(pady=5)

# Tombol untuk memulai sesi
start_button = tk.Button(root, text="Start Session", command=start_session_ui)
start_button.pack(pady=20)

# Menjalankan aplikasi Tkinter
root.mainloop()
