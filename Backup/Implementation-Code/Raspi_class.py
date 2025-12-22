import os
import time
import cv2
import mediapipe as mp
import joblib
import csv
import tkinter as tk
from tkinter import messagebox

base_folder = '/home/elvindo/Documents/pi/Day2'
csv_file_path = None
video_writer = None

# Inisialisasi MediaPipe dan model klasifikasi
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=5)
rf_model = joblib.load('Fix_kan.pkl')  # Ganti dengan path model Anda

def format_timestamp(timestamp):
    """Fungsi untuk mengonversi timestamp ke format HH:MM:SS."""
    return time.strftime('%H:%M:%S', time.localtime(timestamp))

def start_session(responden, sesi):
    global csv_file_path, video_writer

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
        writer.writerow(["Timestamp (Unix)", "Time (HH:MM:SS)", "Frame Name", "Engagement Level", "Confidence Score", "Response Time", "FPS"])

    # Set up video writer untuk menyimpan video keseluruhan
    video_path = os.path.join(session_folder, "session_video.mp4")
    video_writer = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'mp4v'), 10, (640, 480))  # Sesuaikan FPS dan resolusi jika perlu

    # Mulai pengambilan frame dari webcam
    capture_frames_from_webcam(session_folder)

def capture_frames_from_webcam(session_folder):
    global video_writer
    cap = cv2.VideoCapture(0)  # Inisialisasi webcam (0 untuk webcam default)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        start_time = time.time()
        timestamp = int(time.time() * 1000)  # Ambil timestamp dalam milidetik
        formatted_time = format_timestamp(timestamp // 1000)  # Hanya format waktu HH:MM:SS (menggunakan detik dari milidetik)
        frame_name = f"frame_{timestamp}.jpg"  # Gunakan timestamp milidetik agar unik

        # Lakukan klasifikasi pada frame yang diambil
        engagement_level, confidence = process_and_classify_frame(frame, frame_name, session_folder)

        # Hitung waktu respons dan FPS
        response_time = time.time() - start_time
        fps = 1 / response_time if response_time > 0 else 0

        # Tulis hasil klasifikasi ke CSV
        with open(csv_file_path, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, formatted_time, frame_name, engagement_level, confidence, response_time, fps])

        # Simpan frame ke video
        video_writer.write(frame)

        # Tampilkan frame pada layar dan tekan 'q' untuk keluar
        cv2.imshow("Webcam Feed", frame)
        if cv2.waitKey(1) & 0xFF == ord('q'):
            break

    cap.release()
    video_writer.release()
    cv2.destroyAllWindows()

def process_and_classify_frame(frame, frame_name, session_folder):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = face_mesh.process(rgb_frame)
    engagement_level = -1
    confidence = 0.0  # Default nilai confidence

    if result.multi_face_landmarks:
        for face_landmarks in result.multi_face_landmarks:
            landmarks = [(lm.x, lm.y) for lm in face_landmarks.landmark]
            flattened = [coord for point in landmarks for coord in point]

            if len(flattened) == 468 * 2:
                probabilities = rf_model.predict_proba([flattened])  # Mendapatkan probabilitas
                engagement_level = rf_model.predict([flattened])[0]
                confidence = max(probabilities[0])  # Confidence score tertinggi untuk kelas yang diprediksi

                # Simpan frame berdasarkan level engagement
                engagement_folder = os.path.join(session_folder, "engagement", str(engagement_level))
                cv2.imwrite(os.path.join(engagement_folder, frame_name), frame)

    return engagement_level, confidence

# Fungsi untuk memulai sesi dari input UI
def start_session_ui():
    responden = entry_responden.get()
    sesi = entry_sesi.get()
    if not responden or not sesi:
        messagebox.showwarning("Input Error", "Responden ID dan Sesi ID tidak boleh kosong!")
        return
    start_session(responden, sesi)
    messagebox.showinfo("Session Started", f"Session started for Responden {responden} Sesi {sesi}")

# Inisialisasi UI Tkinter
root = tk.Tk()
root.title("Start Webcam Session")
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
