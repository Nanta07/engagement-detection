import serial
import struct
import cv2
import numpy as np

SERIAL_PORT = "/dev/ttyUSB0"
BAUDRATE = 115200

ser = serial.Serial(SERIAL_PORT, BAUDRATE, timeout=2)
print("✅ SERIAL CONNECTED")

def read_frame():
    while True:
        if ser.read(1) == b'\xAA' and ser.read(1) == b'\x55':
            size = struct.unpack("<I", ser.read(4))[0]
            data = ser.read(size)
            if len(data) == size:
                return data

while True:
    jpeg = read_frame()
    frame = cv2.imdecode(
        np.frombuffer(jpeg, np.uint8),
        cv2.IMREAD_COLOR
    )

    if frame is not None:
        cv2.imshow("ESP32-CAM", frame)

    if cv2.waitKey(1) & 0xFF == 27:
        break

cv2.destroyAllWindows()