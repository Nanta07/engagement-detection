import socketio

# ============================================================
# CONFIG
# ============================================================
SERVER_IP = "10.201.65.218"   # IP SERVER
SERVER_PORT = 8000

sio = socketio.Client()

# ============================================================
# SOCKET EVENTS
# ============================================================
@sio.event
def connect():
    print("✅ Connected to server")

@sio.event
def disconnect():
    print("❌ Disconnected from server")

@sio.on("ack")
def on_ack(data):
    print("📨 Server ACK:", data)

# ============================================================
# CONNECT
# ============================================================
sio.connect(f"http://{SERVER_IP}:{SERVER_PORT}")

# ============================================================
# SEND DATA (CONTOH)
# ============================================================
def send_result(payload):
    sio.emit("engagement_result", payload)

# Contoh kirim data
send_result({
    "responden": "webcam_user",
    "sesi": "2025-01-30",
    "frame": "frame_123.jpg",
    "engagement_level": 2,
    "fps": 10.2,
    "response_time": 0.12
})
