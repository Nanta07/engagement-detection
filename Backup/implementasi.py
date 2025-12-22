import cv2
import mediapipe as mp
import onnxruntime as ort
import numpy as np
import time

# Inisialisasi Mediapipe untuk deteksi landmark wajah
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=5)

# Muat model ONNX menggunakan ONNX Runtime
onnx_model_path = 'model.onnx'  # Gantilah dengan path model ONNX Anda
session = ort.InferenceSession(onnx_model_path)

# Periksa input/output model
input_name = session.get_inputs()[0].name
output_name = session.get_outputs()[0].name

# Cek dimensi input yang diharapkan oleh model
input_shape = session.get_inputs()[0].shape
print(f"Model expects input shape: {input_shape}")

# Buka kamera untuk membaca video secara real-time
cap = cv2.VideoCapture(0)  # Menggunakan kamera default (ID kamera 0)

# Tambahkan pengecekan apakah kamera berhasil dibuka    
if not cap.isOpened():
    print("Kamera tidak dapat diakses.")
    exit()

# Variabel untuk menghitung FPS
prev_frame_time = 0
new_frame_time = 0

while True:
    ret, frame = cap.read()
    if not ret:
        print("Tidak dapat membaca frame dari kamera.")
        break

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

            # Pastikan jumlah fitur sesuai dengan yang diharapkan model (936 features for 468 landmarks)
            if len(flattened_landmarks) == input_shape[1]:
                input_array = np.array([flattened_landmarks], dtype=np.float32)

                # Jalankan prediksi ONNX
                predicted_engagement = session.run([output_name], {input_name: input_array})[0]

                # Ambil prediksi kelas engagement
                engagement_level = np.argmax(predicted_engagement)

                # Debug: Print prediksi engagement level
                print(f"Engagement level predicted: {engagement_level}")

                # Gambar kotak di sekitar wajah (bounding box)
                x_min = min([int(landmark.x * frame.shape[1]) for landmark in face_landmarks.landmark])
                y_min = min([int(landmark.y * frame.shape[0]) for landmark in face_landmarks.landmark])
                x_max = max([int(landmark.x * frame.shape[1]) for landmark in face_landmarks.landmark])
                y_max = max([int(landmark.y * frame.shape[0]) for landmark in face_landmarks.landmark])

                # Gambar bounding box di sekitar wajah
                cv2.rectangle(frame, (x_min, y_min), (x_max, y_max), (0, 255, 0), 2)

                # Tampilkan engagement level di atas bounding box
                cv2.putText(frame, f'Engagement: {engagement_level}', (x_min, y_min - 10), cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)

            else:
                print(f"Jumlah landmark yang tidak sesuai: {len(flattened_landmarks)}")

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

# Bersihkan resource setelah selesai
cap.release()
cv2.destroyAllWindows()