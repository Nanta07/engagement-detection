import os
import time
import cv2
import mediapipe as mp
import joblib
import csv
import tkinter as tk
from tkinter import messagebox
from tkcalendar import Calendar
from flask import Flask, request, jsonify
from threading import Thread

# Flask app untuk menerima data dari ESP32-CAM
app = Flask(_name_)

# Variabel global
base_folder = '/home/elvindo/Documents/pi/engagement_data'
csv_file_path = None
face_mesh = mp.solutions.face_mesh.FaceMesh(static_image_mode=False, max_num_faces=5)
rf_model = joblib.load('Fix_kan.pkl')  # Ganti dengan path model Anda


# Fungsi Flask untuk menerima permintaan dari ESP32-CAM
@app.route('/upload', methods=['POST'])
def upload_file():
    global csv_file_path
    start_time = time.time()

    # Mendapatkan timestamp dan nama file untuk setiap frame yang diterima
    timestamp = int(time.time())
    frame_name = f"frame_{timestamp}.jpg"
    frame_path = os.path.join(os.path.dirname(csv_file_path), frame_name)

    # Simpan gambar yang diterima dari ESP32-CAM
    with open(frame_path, 'wb') as f:
        f.write(request.data)

    # Lakukan klasifikasi pada gambar yang diterima
    engagement_level = process_and_classify_image(frame_path, frame_name)

    # Hitung waktu respons dan FPS
    response_time = time.time() - start_time
    fps = 1 / response_time if response_time > 0 else 0

    # Simpan hasil klasifikasi dan metrik ke CSV
    with open(csv_file_path, mode='a', newline='') as file:
        writer = csv.writer(file)
        writer.writerow([timestamp, frame_name, engagement_level, response_time, fps])

    return "File received", 200


def process_and_classify_image(image_path, frame_name):
    global csv_file_path
    frame = cv2.imread(image_path)
    if frame is None:
        print("Failed to load image.")
        return -1

    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = face_mesh.process(rgb_frame)
    engagement_level = -1

    if result.multi_face_landmarks:
        for face_landmarks in result.multi_face_landmarks:
            landmarks = [(lm.x, lm.y) for lm in face_landmarks.landmark]
            flattened = [coord for point in landmarks for coord in point]

            if len(flattened) == 468 * 2:
                engagement_level = rf_model.predict([flattened])[0]

                # Simpan gambar berdasarkan level engagement
                engagement_folder = os.path.join(os.path.dirname(csv_file_path), "engagement", str(engagement_level))
                cv2.imwrite(os.path.join(engagement_folder, frame_name), frame)

    return engagement_level


def start_flask_app():
    app.run(host="0.0.0.0", port=5000)


# Fungsi untuk memulai sesi baru
def start_session_ui(selected_date):
    global csv_file_path

    # Buat folder untuk tanggal yang dipilih
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
        writer.writerow(["Timestamp", "Frame Name", "Engagement Level", "Response Time", "FPS"])

    messagebox.showinfo("Session Started", f"Session started for date {selected_date}.\nListening for frames from ESP32-CAM...")


# Fungsi untuk menghentikan sesi
def stop_session_ui():
    if csv_file_path:
        messagebox.showinfo("Session Stopped", "Session stopped. All received frames have been saved.")
    else:
        messagebox.showwarning("No Active Session", "No session is currently active.")


# Fungsi untuk menampilkan laporan hasil klasifikasi
def display_results():
    if not csv_file_path or not os.path.exists(csv_file_path):
        messagebox.showwarning("No Results", "No results available to display.")
        return

    engagement_counts = {"0": 0, "1": 0, "2": 0, "3": 0}
    total_frames = 0

    with open(csv_file_path, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            engagement_level = row["Engagement Level"]
            if engagement_level in engagement_counts:
                engagement_counts[engagement_level] += 1
                total_frames += 1

    engagement_percentages = {
        level: (count / total_frames * 100) if total_frames > 0 else 0
        for level, count in engagement_counts.items()
    }

    result = f"""
    Total Frames: {total_frames}
    Engagement 0: {engagement_counts["0"]} ({engagement_percentages["0"]:.2f}%)
    Engagement 1: {engagement_counts["1"]} ({engagement_percentages["1"]:.2f}%)
    Engagement 2: {engagement_counts["2"]} ({engagement_percentages["2"]:.2f}%)
    Engagement 3: {engagement_counts["3"]} ({engagement_percentages["3"]:.2f}%)
    """

    messagebox.showinfo("Classification Results", result)


# Membuat antarmuka Tkinter
def create_ui():
    root = tk.Tk()
    root.title("Engagement Detection System")
    root.geometry("400x300")

    # Label untuk memilih tanggal
    label_calendar = tk.Label(root, text="Pilih Tanggal:")
    label_calendar.pack(pady=5)

    # Widget kalender untuk memilih tanggal
    calendar = Calendar(root, selectmode='day', date_pattern='yyyy-mm-dd')
    calendar.pack(pady=10)

    # Tombol untuk memulai sesi
    start_button = tk.Button(root, text="Start Session", command=lambda: start_session_ui(calendar.get_date()))
    start_button.pack(pady=10)

    # Tombol untuk menghentikan sesi
    stop_button = tk.Button(root, text="Stop Session", command=stop_session_ui)
    stop_button.pack(pady=10)

    # Tombol untuk menampilkan hasil klasifikasi
    results_button = tk.Button(root, text="Show Results", command=display_results)
    results_button.pack(pady=10)

    root.mainloop()


if _name_ == "_main_":
    # Jalankan Flask di thread terpisah
    flask_thread = Thread(target=start_flask_app)
    flask_thread.daemon = True
    flask_thread.start()

    # Jalankan antarmuka pengguna Tkinter
    create_ui()