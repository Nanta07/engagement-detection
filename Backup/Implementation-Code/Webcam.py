import os
import time
import cv2
import mediapipe as mp
import joblib
import csv
import tkinter as tk
from tkinter import messagebox
from tkcalendar import Calendar
from PIL import Image, ImageTk

# Konfigurasi folder dan variabel global
base_folder = '/home/elvindo/Documents/pi/Day2'
csv_file_path = None
video_writer = None
stop_recording = False  # Variabel global untuk menghentikan proses

# Inisialisasi MediaPipe dan model klasifikasi
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=5)
rf_model = joblib.load('model_fix.pkl')  # Ganti dengan path model Anda

def format_timestamp(timestamp):
    """Fungsi untuk mengonversi timestamp ke format HH:MM:SS."""
    return time.strftime('%H:%M:%S', time.localtime(timestamp))

def start_session(selected_date):
    global csv_file_path, video_writer, stop_recording

    # Reset variabel global untuk sesi baru
    stop_recording = False
    video_writer = None

    # Buat folder berdasarkan tanggal
    session_folder = os.path.join(base_folder, f"session_{selected_date}")
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
    video_writer = cv2.VideoWriter(video_path, cv2.VideoWriter_fourcc(*'mp4v'), 10, (640, 480))

    # Mulai pengambilan frame dari webcam
    capture_frames_from_webcam(session_folder)

def capture_frames_from_webcam(session_folder):
    global video_writer, stop_recording
    cap = cv2.VideoCapture(0)  # Inisialisasi ulang webcam (0 untuk webcam default)

    # Periksa apakah kamera berhasil dibuka
    if not cap.isOpened():
        messagebox.showerror("Camera Error", "Tidak dapat membuka kamera.")
        return

    # Membuka jendela baru dengan webcam feed
    camera_window = tk.Toplevel()
    camera_window.title("Camera Preview")
    camera_window.geometry("700x600")

    video_label = tk.Label(camera_window)
    video_label.pack()

    stop_button = tk.Button(camera_window, text="Stop Recording", command=lambda: stop_camera(camera_window, cap))
    stop_button.pack(pady=10)

    def show_frame():
        nonlocal cap
        ret, frame = cap.read()
        if not ret or stop_recording:  # Hentikan jika stop_recording diatur True
            return

        start_time = time.time()
        timestamp = int(time.time() * 1000)  # Ambil timestamp dalam milidetik
        formatted_time = format_timestamp(timestamp // 1000)  # Format waktu HH:MM:SS
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
        if video_writer:
            video_writer.write(frame)

        # Tampilkan frame di Tkinter
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        img = Image.fromarray(frame_rgb)
        img_tk = ImageTk.PhotoImage(image=img)
        video_label.img_tk = img_tk
        video_label.configure(image=img_tk)

        # Deteksi tombol keyboard untuk menghentikan perekaman
        def on_key_press(event):
            if event.char == 'q':
                stop_camera(camera_window, cap)

        # Bind key press event ke camera_window
        camera_window.bind('<KeyPress>', on_key_press)

        # Lanjutkan loop
        camera_window.after(10, show_frame)

    show_frame()
    camera_window.mainloop()

    # Tutup kamera dan video writer setelah jendela ditutup
    cap.release()
    if video_writer:
        video_writer.release()
    cv2.destroyAllWindows()

def stop_camera(window, cap):
    """Menghentikan kamera, menutup jendela pop-out, dan menampilkan laporan."""
    global stop_recording, video_writer
    stop_recording = True
    window.destroy()  # Menutup jendela webcam
    cap.release()  # Pastikan kamera dirilis
    if video_writer:
        video_writer.release()  # Tutup video writer
    display_classification_report()  # Menampilkan laporan klasifikasi

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

def display_classification_report():
    """Menampilkan laporan klasifikasi setelah perekaman berhenti."""
    if not csv_file_path:
        return

    engagement_counts = {"0": 0, "1": 0, "2": 0, "3": 0}

    # Baca file CSV dan hitung jumlah frame per level engagement
    with open(csv_file_path, mode='r') as file:
        reader = csv.DictReader(file)
        for row in reader:
            level = row["Engagement Level"]
            if level in engagement_counts:
                engagement_counts[level] += 1

    # Tentukan hasil engagement
    low_engagement = engagement_counts["0"] + engagement_counts["1"]
    high_engagement = engagement_counts["2"] + engagement_counts["3"]
    result = "Low Engagement" if low_engagement > high_engagement else "High Engagement"

    # Tampilkan laporan menggunakan messagebox
    messagebox.showinfo("Classification Report", f"""
Classification Report:
Engagement 0 = {engagement_counts['0']}
Engagement 1 = {engagement_counts['1']}
Engagement 2 = {engagement_counts['2']}
Engagement 3 = {engagement_counts['3']}

Engagement Result = {result}
""")

def start_session_ui():
    selected_date = calendar.get_date()
    if not selected_date:
        messagebox.showwarning("Input Error", "Tanggal harus dipilih!")
        return
    start_session(selected_date)

# Inisialisasi UI Tkinter
root = tk.Tk()
root.title("Start Webcam Session")
root.geometry("400x300")

# Label untuk memilih tanggal
label_calendar = tk.Label(root, text="Pilih Tanggal:")
label_calendar.pack(pady=5)

# Widget kalender untuk memilih tanggal
calendar = Calendar(root, selectmode='day', date_pattern='yyyy-mm-dd')
calendar.pack(pady=10)

# Tombol untuk memulai sesi
start_button = tk.Button(root, text="Start Session", command=start_session_ui)
start_button.pack(pady=20)

# Menjalankan aplikasi Tkinter
root.mainloop()
