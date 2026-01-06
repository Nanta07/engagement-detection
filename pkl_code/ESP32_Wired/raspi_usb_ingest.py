import serial
import struct
import os
import time

SERIAL_PORT = "/dev/ttyUSB0"
BAUDRATE = 115200

SAVE_DIR = "/home/elvindo/esp32_frames"
os.makedirs(SAVE_DIR, exist_ok=True)

ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=5)
print("✅ Serial connected")

def read_frame():
    while True:
        if ser.read(1) == b'\xAA' and ser.read(1) == b'\x55':
            size = struct.unpack("<I", ser.read(4))[0]
            data = ser.read(size)
            if len(data) == size:
                return data

count = 0

while True:
    jpeg = read_frame()
    count += 1

    filename = os.path.join(
        SAVE_DIR,
        f"frame_{int(time.time())}.jpg"
    )

    with open(filename, "wb") as f:
        f.write(jpeg)

    print(f"📸 Saved {filename} ({len(jpeg)} bytes)")