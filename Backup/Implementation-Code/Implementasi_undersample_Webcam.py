import cv2
import mediapipe as mp
import joblib
import numpy as np
import time

# Inisialisasi Mediapipe dan load model yang sudah dilatih
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=5)  # Bisa mendeteksi hingga 5 wajah

# Muat model yang sudah dilatih (pastikan file .pkl ada di folder yang sama)
rf_model = joblib.load('Fix_kan.pkl')

# Buka kamera internal/USB pada Raspberry Pi
cap = cv2.VideoCapture(0)  # Menggunakan kamera default (ID kamera 0)

# Tambahkan pengecekan apakah kamera berhasil dibuka    
if not cap.isOpened():
    print("Kamera tidak dapat diakses.")
    exit()

# Variabel untuk menghitung FPS dan response time
prev_frame_time = 0
new_frame_time = 0
response_times = []  # List untuk menyimpan waktu response tiap frame

while True:
    ret, frame = cap.read()
    if not ret:
        print("Tidak dapat membaca frame dari kamera.")
        break

    # Catat waktu awal inferensi untuk frame ini
    start_time = time.time()

    # Ubah gambar ke RGB (karena Mediapipe menggunakan RGB)
    rgb_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)

    # Proses deteksi landmark wajah
    result = face_mesh.process(rgb_frame)

    if result.multi_face_landmarks:
        # Loop untuk setiap wajah yang terdeteksi
        for face_landmarks in result.multi_face_landmarks:
            # Ekstraksi koordinat landmark dan gambar titik-titik landmark
            landmark_coords = []
            for idx, landmark in enumerate(face_landmarks.landmark):
                x = int(landmark.x * frame.shape[1])  # Koordinat x dalam pixel
                y = int(landmark.y * frame.shape[0])  # Koordinat y dalam pixel

                # Simpan koordinat (x, y) untuk prediksi
                landmark_coords.append((landmark.x, landmark.y))

                # Gambar titik landmark pada frame
                cv2.circle(frame, (x, y), 1, (0, 255, 0), -1)

            # Flatten koordinat landmark untuk prediksi model
            flattened_landmarks = [coord for point in landmark_coords for coord in point]

            # Pastikan jumlah fitur sesuai (jumlah landmark yang diekstraksi)
            if len(flattened_landmarks) == 468 * 2:  # 468 landmarks (x dan y)
                # Lakukan prediksi engagement level menggunakan model
                predicted_engagement = rf_model.predict([flattened_landmarks])
                engagement_level = predicted_engagement[0]

                # Gambar kotak di sekitar wajah (bounding box)
                x_min = min([int(landmark.x * frame.shape[1]) for landmark in face_landmarks.landmark])
                y_min = min([int(landmark.y * frame.shape[0]) for landmark in face_landmarks.landmark])
                x_max = max([int(landmark.x * frame.shape[1]) for landmark in face_landmarks.landmark])
                y_max = max([int(landmark.y * frame.shape[0]) for landmark in face_landmarks.landmark])

                # Gambar bounding box di sekitar wajah
                cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

                # Tampilkan engagement level di atas bounding box
                cv2.putText(frame, f'Engagement: {engagement_level}', (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

    # Catat waktu akhir inferensi untuk frame ini dan hitung response time
    end_time = time.time()
    response_time = end_time - start_time
    response_times.append(response_time)  # Tambahkan waktu response ke daftar

    # Menghitung FPS
    new_frame_time = time.time()
    fps = 1 / (new_frame_time - prev_frame_time)
    prev_frame_time = new_frame_time

    # Tampilkan FPS di frame
    cv2.putText(frame, f'FPS: {int(fps)}', (10, 30), cv2.FONT_HERSHEY_SIMPLEX, 1, (0, 255, 0), 2)

    # Tampilkan frame dengan OpenCV
    cv2.imshow('Engagement Level Detection for Multiple Faces', frame)

    # Tekan 'q' untuk keluar dari loop
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

# Hitung response time rata-rata setelah selesai
average_response_time = sum(response_times) / len(response_times)
print("Average Response Time per Frame:", average_response_time, "seconds")

# Bersihkan resource setelah selesai
cap.release()
cv2.destroyAllWindows()