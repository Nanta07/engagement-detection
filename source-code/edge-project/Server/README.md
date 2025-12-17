File Directories
server/
│
├── app.py                 # Flask server utama (receiver data)
├── requirements.txt       # Dependency server
├── README.md              # Dokumentasi server
│
├── config/
│   └── config.py          # Konfigurasi (port, folder, dll)
│
├── data/
│   ├── raw/
│   │   ├── frames/        # (optional) frame dari raspi
│   │   └── vectors/       # landmark / feature vector
│   │
│   ├── logs/
│   │   └── engagement.csv # log data utama
│   │
│   └── sessions/          # data per responden / sesi
│
├── utils/
│   └── file_utils.py      # helper save file / csv
│
└── run_server.bat         # shortcut run server (Windows)
