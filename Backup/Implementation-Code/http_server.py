from flask import Flask, request, jsonify
import os
import time
import cv2
import mediapipe as mp
import joblib
import csv

app = Flask(__name__)
base_folder = '/home/elvindo/Documents/pi/engagement_data'
csv_file_path = None

# Inisialisasi MediaPipe dan model klasifikasi
mp_face_mesh = mp.solutions.face_mesh
face_mesh = mp_face_mesh.FaceMesh(static_image_mode=False, max_num_faces=5)
rf_model = joblib.load('Fix_kan.pkl')  # Ganti dengan path model Anda

@app.route('/start_new_session', methods=['GET'])
def start_new_session():
    global csv_file_path
    
    # Mendapatkan ID responden dan nomor sesi dari parameter URL
    responden = request.args.get('responden')
    sesi = request.args.get('sesi')
    
    if not responden or not sesi:
        return "Missing 'responden' or 'sesi' parameters", 400

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
    
    return f"New session started for Responden {responden} Sesi {sesi}", 200

@app.route('/upload', methods=['POST'])
def upload_file():
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

@app.route('/check_results', methods=['GET'])
def check_results():
    # Mendapatkan parameter responden dan sesi dari URL
    responden = request.args.get('responden')
    sesi = request.args.get('sesi')

    if not responden or not sesi:
        return "Missing 'responden' or 'sesi' parameters", 400

    # Tentukan path file CSV berdasarkan ID responden dan sesi
    session_folder = os.path.join(base_folder, f"responden_{responden}", f"sesi_{sesi}")
    csv_file_path = os.path.join(session_folder, "engagement_results.csv")

    if not os.path.exists(csv_file_path):
        return "File not found", 404

    # Inisialisasi penghitung untuk setiap level engagement
    engagement_counts = {"0": 0, "1": 0, "2": 0, "3": 0}
    total_frames = 0

    # Baca data dari file CSV dan hitung jumlah setiap level engagement
    with open(csv_file_path, mode='r') as file:
        csv_reader = csv.DictReader(file)
        for row in csv_reader:
            engagement_level = row["Engagement Level"]
            if engagement_level in engagement_counts:
                engagement_counts[engagement_level] += 1
                total_frames += 1

    # Hitung persentase setiap level engagement
    engagement_percentages = {
        level: (count / total_frames * 100) if total_frames > 0 else 0
        for level, count in engagement_counts.items()
    }

    # Kembalikan hasil persentase dalam format JSON
    result = {
        "total_frames": total_frames,
        "engagement_counts": engagement_counts,
        "engagement_percentages": engagement_percentages
    }
    
    return jsonify(result)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)
