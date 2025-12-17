# ESP32-CAM Edge Device for Engagement Detection
This ESP32-CAM project:
- captures frames from camera
- stores them temporarily in SD card
- sends all frames to Raspberry Pi Flask server
- works as an Edge Device (image acquisition only)

## Steps
1. Connect to WiFi
2. Receive "start_recording" from browser / system
3. Capture frames every 100ms → save to SD
4. When "stop_recording" is triggered → send frames via HTTP POST

## Compile on Arduino IDE
- Install ESP32 Board
- Select AI Thinker ESP32-CAM
- Upload via UART / USB TTL

Berikut adalah **README utama (project brief)** untuk keseluruhan project Anda, ditulis dalam **bahasa Inggris**, profesional, dan siap digunakan sebagai README root GitHub atau dokumentasi utama untuk skripsi Anda.

Jika Anda ingin, nanti saya bisa buatkan juga versi “extended documentation”, atau README untuk masing-masing repo.

---

# **Engagement Detection System Using Facial Landmarks, Machine Learning, and Edge Computing**

*A complete pipeline combining Raspberry Pi, ESP32-CAM, Mediapipe, and Random Forest for real-time engagement monitoring.*

---

## 📖 **Project Overview**
This project implements a real-time **Engagement Detection System** designed to measure user engagement levels using facial landmarks and machine learning. The system integrates **edge computing**, **computer vision**, and **embedded systems** to create a scalable, low-cost, and efficient engagement monitoring solution.

It is composed of three main modules:
1. **Webcam-Based Desktop Application** (Raspberry Pi + Tkinter)
   Handles real-time engagement detection using a connected webcam.
2. **Flask-Based Backend Server** (Raspberry Pi)
   Receives frames from an Edge Device (ESP32-CAM), performs landmark extraction, classification, and stores results.
3. **ESP32-CAM Edge Device**
   Captures images, stores them locally, and sends them to the Raspberry Pi server for classification.

The system detects facial landmarks using **MediaPipe FaceMesh (468 points)** and classifies engagement using a **Random Forest model** trained on extracted features.

---

##  **Objectives**
* Build an end-to-end machine learning pipeline running on low-power hardware.
* Perform real-time facial landmark extraction on Raspberry Pi.
* Classify user engagement into four levels:

  * **0 — Very Low Engagement**
  * **1 — Low Engagement**
  * **2 — High Engagement**
  * **3 — Very High Engagement**
* Enable multi-input support (Webcam or ESP32-CAM camera module).
* Implement a distributed architecture using edge computing.

---

##  **System Architecture**
The system consists of three interconnected components:

### **1️⃣ Webcam Application – Raspberry Pi (Frontend + Processing)**
* Real-time webcam feed
* MediaPipe landmark extraction
* Engagement classification with Random Forest
* Stores frames and classification results
* Provides GUI for starting sessions

### **2️⃣ Flask Server – Raspberry Pi (Backend)**
* Receives HTTP POST images from ESP32-CAM
* Processes images with MediaPipe
* Classifies engagement levels
* Saves frames to labeled folders
* Generates session-based statistics

### **3️⃣ ESP32-CAM (Edge Device)**
* Captures images periodically
* Stores temporary frames on SD card
* Sends all frames to Flask server after recording
* Acts purely as an image acquisition device

---

### **Software**
* Python 3
* Flask
* OpenCV
* MediaPipe
* Scikit-Learn
* Tkinter
* Joblib