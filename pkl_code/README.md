# Raspberry Pi ML Deployment (MLP & Logistic Regression)

## Deskripsi Proyek
Project ini berfokus pada **deployment model Machine Learning di Raspberry Pi** untuk melakukan **inference secara real-time**. Model utama yang digunakan adalah **Multi-Layer Perceptron (MLP)**, dengan **Logistic Regression** sebagai model pembanding (baseline).  
Sistem dirancang agar ringan, stabil, dan kompatibel dengan keterbatasan resource Raspberry Pi.

## Tujuan
- Mengimplementasikan model ML yang telah dilatih ke environment Raspberry Pi
- Melakukan inferensi data secara langsung (real-time / near real-time)
- Membandingkan performa MLP dengan Logistic Regression
- Menyediakan pipeline deployment yang reproducible dan mudah dikembangkan

## Arsitektur Sistem
1. **Preprocessing Data**
   - Normalisasi / standarisasi fitur
   - Penyesuaian input agar sesuai dengan model training

2. **Model Machine Learning**
   - MLP (model utama)
   - Logistic Regression (baseline)
   - Model disimpan dalam format `.pkl`

3. **Inference Engine (Raspberry Pi)**
   - Load model dan scaler
   - Menerima input data
   - Menjalankan prediksi
   - Menampilkan atau mengirim hasil output

## Tech Stack
- Python 3
- scikit-learn
- NumPy
- Joblib
- Raspberry Pi OS (Linux)

## Struktur Direktori
```

├── models/
│   ├── mlp_model.pkl
│   ├── logreg_model.pkl
│   └── scaler.pkl
├── src/
│   ├── inference_mlp.py
│   ├── inference_logreg.py
│   └── utils.py
├── requirements.txt
├── README.md

````

## Cara Menjalankan (Raspberry Pi)
1. Install dependency:
   ```bash
   pip install -r requirements.txt
````

2. Jalankan inference MLP:

   ```bash
   python src/inference_mlp.py
   ```

3. Jalankan inference Logistic Regression:

   ```bash
   python src/inference_logreg.py
   ```

## Catatan Implementasi

* Model sudah dioptimalkan untuk inference (tanpa training ulang di Raspberry Pi)
* Fokus pada stabilitas dan efisiensi komputasi
* Cocok untuk pengembangan sistem IoT atau edge AI

## Status Proyek

* Training model: Selesai
* Evaluasi model: Selesai
* Deployment Raspberry Pi: Selesai
* Pengujian fungsional: Berjalan sesuai ekspektasi

## Pengembangan Lanjutan

* Optimasi latency inference
* Integrasi sensor atau input real-time
* Visualisasi hasil via dashboard atau web service