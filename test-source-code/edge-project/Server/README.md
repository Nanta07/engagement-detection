

Folder Directory Detail:
server/
│
├── app.py                     # Flask server utama (receiver dari Raspi)
├── config.py                  # Konfigurasi server (host, port, path)
├── requirements.txt           # Dependency server
├── README.md                  # Dokumentasi server
├── run_server.bat             # Shortcut run server (Windows)
│
└── data/
    │
    ├── logs/
    │   └── engagement_log.csv # Log global semua data (SEMUA SESI)
    │
    └── sessions/
        └── responden_1/
            └── sesi_1/
                └── results.
                csv