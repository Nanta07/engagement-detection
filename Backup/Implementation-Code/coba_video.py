import os
import time
import cv2
import mediapipe as mp
import joblib
import csv
import tkinter as tk
from tkinter import filedialog, messagebox

base_folder = '/home/elvindo/Documents/pi/Day2'
csv_file_path = None

# Inisialisasi MediaPipe dan model klasifikasi
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp.solutions.face_mesh.FaceMesh(static_image_mode=False, max_num_faces=5)
rf_model = joblib.load('Fix_kan.pkl')  # Ganti dengan path model Anda

def format_timestamp(timestamp):
    """Fungsi untuk mengonversi timestamp ke format HH:MM:SS."""
    return time.strftime('%H:%M:%S', time.localtime(timestamp))

def start_session_from_video(responden, sesi, video_path):
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
        writer.writerow(["Timestamp (Unix)", "Time (HH:MM:SS)", "Frame Name", "Engagement Level", "Response Time"])

    # Proses video frame-by-frame
    process_video(video_path, session_folder)

def process_video(video_path, session_folder):
    cap = cv2.VideoCapture(video_path)

    if not cap.isOpened():
        messagebox.showerror("Error", "Video gagal dibuka! Periksa file dan coba lagi.")
        return

    # Buat jendela pop-out untuk preview video
    cv2.namedWindow("Preview", cv2.WINDOW_NORMAL)

    while cap.isOpened():
        ret, frame = cap.read()
        if not ret:
            break

        start_time = time.time()  # Catat waktu mulai untuk menghitung response time

        timestamp = int(time.time() * 1000)  # Ambil timestamp dalam milidetik
        formatted_time = format_timestamp(timestamp // 1000)  # Format waktu HH:MM:SS
        frame_name = f"frame_{timestamp}.jpg"  # Nama frame unik berdasarkan timestamp

        # Lakukan klasifikasi pada frame yang diambil
        engagement_level = process_and_classify_frame(frame, frame_name, session_folder)

        # Hitung response time
        response_time = time.time() - start_time  # Waktu selesai - waktu mulai

        # Tambahkan bounding box di wajah dan teks pada frame
        annotated_frame = annotate_frame(frame, engagement_level)

        # Simpan frame dengan bounding box ke folder engagement yang sesuai
        if engagement_level != -1:  # Hanya simpan frame dengan deteksi valid
            engagement_folder = os.path.join(session_folder, "engagement", str(engagement_level))
            cv2.imwrite(os.path.join(engagement_folder, frame_name), annotated_frame)

        # Tampilkan frame pada jendela pop-out
        cv2.imshow("Preview", annotated_frame)

        # Tulis hasil klasifikasi ke CSV
        with open(csv_file_path, mode='a', newline='') as file:
            writer = csv.writer(file)
            writer.writerow([timestamp, formatted_time, frame_name, engagement_level, response_time])

        if cv2.waitKey(1) & 0xFF == ord('q'):  # Tekan 'q' untuk keluar
            break

    cap.release()
    cv2.destroyAllWindows()

def process_and_classify_frame(frame, frame_name, session_folder):
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
    result = face_mesh.process(rgb_frame)
    engagement_level = -1  # Default nilai engagement jika tidak ada deteksi wajah

    if result.multi_face_landmarks:
        for face_landmarks in result.multi_face_landmarks:
            # Ambil koordinat bounding box dari landmark wajah
            h, w, _ = frame.shape
            x_min = min([int(lm.x * w) for lm in face_landmarks.landmark])
            x_max = max([int(lm.x * w) for lm in face_landmarks.landmark])
            y_min = min([int(lm.y * h) for lm in face_landmarks.landmark])
            y_max = max([int(lm.y * h) for lm in face_landmarks.landmark])

            landmarks = [(lm.x, lm.y) for lm in face_landmarks.landmark]
            flattened = [coord for point in landmarks for coord in point]

            if len(flattened) == 468 * 2:
                engagement_level = rf_model.predict([flattened])[0]  # Prediksi kelas engagement

            # Gambar bounding box pada frame
            cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

            # Tampilkan teks di atas bounding box
            text = f"Engagement: {engagement_level}"
            cv2.putText(frame, text, (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    return engagement_level

def annotate_frame(frame, engagement_level):
    return frame.copy()

# Fungsi untuk memulai sesi dari input UI
def start_session_ui():
    responden = entry_responden.get()
    sesi = entry_sesi.get()
    if not responden or not sesi:
        messagebox.showwarning("Input Error", "Responden ID dan Sesi ID tidak boleh kosong!")
        return

    # Pilih file video input
    video_path = filedialog.askopenfilename(
        title="Pilih File Video",
        filetypes=[("MPEG-4 Video", "*.mp4;*.MP4"),
                   ("All Files", "*.*")]
    )
    if not video_path:
        messagebox.showwarning("Input Error", "Video file harus dipilih!")
        return

    start_session_from_video(responden, sesi, video_path)
    messagebox.showinfo("Session Completed", f"Session completed for Responden {responden} Sesi {sesi}")

# Inisialisasi UI Tkinter
root = tk.Tk()
root.title("Process Video Session")
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
