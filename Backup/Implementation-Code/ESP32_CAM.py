import os
import time
import requests
import tkinter as tk
from tkinter import messagebox
from tkcalendar import Calendar
from flask import Flask, request, jsonify
from threading import Thread
import cv2
import mediapipe as mp
import joblib
import csv

# Flask app
app = Flask(__name__)

# Konfigurasi ESP32-CAM
ESP32_IP = "http://192.168.213.107"  # Ganti dengan IP ESP32-CAM Anda
base_folder = '/home/pi/engagement_data'
csv_file_path = None

# Inisialisasi MediaPipe dan model klasifikasi
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=5)
rf_model = joblib.load('Fix_kan.pkl')  # Ganti dengan path model Anda


@app.route('/start_new_session', methods=['GET'])
def start_new_session():
    """Memulai sesi baru dengan folder dan file CSV berdasarkan tanggal."""
    global csv_file_path

    # Mendapatkan parameter tanggal dari URL
    selected_date = request.args.get('date')

    if not selected_date:
        return "Missing 'date' parameter", 400

    try:
        # Debug logging
        print(f"Starting new session for date: {selected_date}")

        # Buat folder berdasarkan tanggal
        session_folder = os.path.join(base_folder, f"session_{selected_date}")
        os.makedirs(session_folder, exist_ok=True)

        # Buat folder engagement (0, 1, 2, 3)
        engagement_folder = os.path.join(session_folder, "engagement")
        for level in ["0", "1", "2", "3"]:
            os.makedirs(os.path.join(engagement_folder, level), exist_ok=True)

        # Siapkan file CSV
        csv_file_path = os.path.join(session_folder, "engagement_results.csv")
        with open(csv_file_path, mode='w', newline='') as file:
            writer = csv.writer(file)
            writer.writerow(["Timestamp", "Frame Name", "Engagement Level", "Response Time", "FPS"])

        print(f"Session folder and CSV initialized at: {session_folder}")
        return f"New session started for date {selected_date}", 200
    except Exception as e:
        print(f"Error in start_new_session: {e}")
        return f"Internal Server Error: {e}", 500


@app.route('/upload', methods=['POST'])
def upload_file():
    """Menerima file dari ESP32-CAM untuk klasifikasi."""
    try:
        start_time = time.time()
        timestamp = int(time.time())
        frame_name = f"frame_{timestamp}.jpg"
        frame_path = os.path.join(os.path.dirname(csv_file_path), frame_name)

        # Simpan gambar
        with open(frame_path, 'wb') as f:
            f.write(request.data)

        # Klasifikasi gambar
        engagement_level = classify_image(frame_path, frame_name)

        # Simpan ke CSV
        response_time = time.time() - start_time
        fps = 1 / response_time if response_time > 0 else 0
        with open(csv_file_path, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, frame_name, engagement_level, response_time, fps])

        print(f"File received and classified: {frame_name} with engagement level: {engagement_level}")
        return "File received", 200
    except Exception as e:
        print(f"Error in upload_file: {e}")
        return f"Internal Server Error: {e}", 500


def classify_image(image_path, frame_name):
    """Melakukan klasifikasi pada gambar yang diterima."""
    try:
        frame = cv2.imread(image_path)
        if frame is None:
            print(f"Failed to load image: {image_path}")
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

                    # Simpan berdasarkan engagement level
                    engagement_folder = os.path.join(os.path.dirname(csv_file_path), "engagement", str(engagement_level))
                    os.makedirs(engagement_folder, exist_ok=True)
                    cv2.imwrite(os.path.join(engagement_folder, frame_name), frame)

        print(f"Image classified with engagement level: {engagement_level}")
        return engagement_level
    except Exception as e:
        print(f"Error in classify_image: {e}")
        return -1


def start_recording(selected_date):
    """Mengirim perintah ke ESP32-CAM untuk memulai perekaman."""
    try:
        # Memulai sesi di Flask server
        flask_response = requests.get(f"http://localhost:5000/start_new_session", params={"date": selected_date})
        if flask_response.status_code != 200:
            messagebox.showerror("Flask Error", f"Flask server error: {flask_response.text}")
            return

        # Kirim perintah ke ESP32-CAM untuk memulai rekaman
        esp_response = requests.get(f"{ESP32_IP}/start_recording")
        if esp_response.status_code == 200:
            messagebox.showinfo("Recording Started", f"Recording started for date {selected_date}.")
        else:
            messagebox.showerror("Error", "ESP32-CAM failed to start recording.")
    except Exception as e:
        messagebox.showerror("Connection Error", f"Cannot connect to ESP32-CAM: {e}")


def stop_recording():
    """Mengirim perintah ke ESP32-CAM untuk menghentikan perekaman."""
    try:
        response = requests.get(f"{ESP32_IP}/stop_recording")
        if response.status_code == 200:
            messagebox.showinfo("Recording Stopped", "Recording stopped. Data has been saved.")
        else:
            messagebox.showerror("Error", "ESP32-CAM failed to stop recording.")
    except Exception as e:
        messagebox.showerror("Connection Error", f"Cannot connect to ESP32-CAM: {e}")


def display_results(selected_date):
    """Menampilkan hasil klasifikasi dari file CSV."""
    try:
        session_folder = os.path.join(base_folder, f"session_{selected_date}")
        csv_file_path = os.path.join(session_folder, "engagement_results.csv")

        if not os.path.exists(csv_file_path):
            messagebox.showwarning("No Results", "Tidak ada hasil untuk ditampilkan.")
            return

        engagement_counts = {"0": 0, "1": 0, "2": 0, "3": 0}
        total_frames = 0

        # Baca file CSV dan hitung jumlah frame untuk setiap level engagement
        with open(csv_file_path, mode='r') as file:
            csv_reader = csv.DictReader(file)
            for row in csv_reader:
                level = row["Engagement Level"]
                if level in engagement_counts:
                    engagement_counts[level] += 1
                    total_frames += 1

        result = f"""
        Total Frames: {total_frames}
        Engagement 0: {engagement_counts["0"]}
        Engagement 1: {engagement_counts["1"]}
        Engagement 2: {engagement_counts["2"]}
        Engagement 3: {engagement_counts["3"]}
        """
        messagebox.showinfo("Results", result)
    except Exception as e:
        print(f"Error in display_results: {e}")
        messagebox.showerror("Error", f"An error occurred: {e}")


def create_ui():
    """Membuat antarmuka pengguna Tkinter."""
    root = tk.Tk()
    root.title("ESP32-CAM Controller")
    root.geometry("400x400")

    # Kalender untuk memilih tanggal
    label_calendar = tk.Label(root, text="Pilih Tanggal:")
    label_calendar.pack(pady=5)

    calendar = Calendar(root, selectmode='day', date_pattern='yyyy-mm-dd')
    calendar.pack(pady=10)

    # Tombol untuk memulai perekaman
    start_button = tk.Button(root, text="Start Recording",
                             command=lambda: start_recording(calendar.get_date()))
    start_button.pack(pady=10)

    # Tombol untuk menghentikan perekaman
    stop_button = tk.Button(root, text="Stop Recording", command=stop_recording)
    stop_button.pack(pady=10)

    # Tombol untuk menampilkan hasil klasifikasi
    results_button = tk.Button(root, text="Show Results",
                               command=lambda: display_results(calendar.get_date()))
    results_button.pack(pady=10)

    root.mainloop()


if __name__ == "__main__":
    # Jalankan Flask server di thread terpisah
    flask_thread = Thread(target=app.run, kwargs={"host": "0.0.0.0", "port": 5000, "debug": True})
    flask_thread.daemon = True
    flask_thread.start()

    # Jalankan antarmuka pengguna Tkinter
    create_ui()
