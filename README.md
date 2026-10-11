# Core Photo 📷

**Aplikasi Desktop Windows untuk Pengambilan Foto Drill Core Terstruktur & Otomatis**

> Sesuai dengan spesifikasi [PRD Core Photo AI Agent](PRD_Core_Photo_AI_Agent.md).

---

## 🌟 Fitur Utama

1. **Camera Subsystem & Wi-Fi DSLR Wireless Tethering**
   - **Wi-Fi DSLR Adapter (`WiFiDslrAdapter`):** Mendukung kamera DSLR/Mirrorless modern (Canon, Nikon, Sony, Fuji) secara nirkabel melalui High-Speed Tethering Watcher & Network Reachability Probe.
   - **Direct USB DSLR (`DirectUsbAdapter`):** Mendukung koneksi kabel langsung via Windows WIA/PTP tanpa memerlukan SDK pihak ketiga.
   - **Universal Hot-Folder (`HotFolderAdapter`):** Integrasi folder ingest serbaguna untuk berbagai utilitas kamera eksternal.
   - **Webcam / Simulator (`WebcamAdapter`):** Fallback webcam atau pola teknis simulasi core tray untuk demonstrasi dan testing.
   - **Real EXIF Metadata Parser:** Mengekstrak informasi autentik kamera (*Make, Model, Serial Number, ISO, Lens*) langsung dari foto yang masuk.
   - **Switching Antarmuka Cepat:** Penggantian koneksi kamera (*Wi-Fi DSLR, Direct USB, Webcam*) langsung dari Tab 2 (*Camera Settings*) di layar Capture.

2. **Target Server Folder & Auto-Transfer**
   - **Target Server Folder Input:** Kolom konfigurasi folder server/network share (`\\server\share` atau drive jaringan) langsung di Tab 1 (*Tray Data*) dan menu Settings.
   - **Instant Auto-Transfer:** Saat foto disetujui (*Approve & Next Tray*) di layar Review, file otomatis terkirim dan tersinkronisasi ke server folder.
   - **Manual Session Sync:** Tombol "Sync Session to Server Folder" untuk sinkronisasi seluruh foto sesi secara manual kapan saja.

3. **Full Offline-First Operation**
   - Seluruh alur (Session, Tray, Framing, Capture, Review, Validasi, Browser) berjalan 100% lokal tanpa memerlukan internet.
   - Database SQLite mandiri per sesi (`session.db`) dengan WAL mode untuk ketahanan crash.

4. **Crash Recovery & Data Safety**
   - File RAW disimpan ke disk **sebelum** pemrosesan gambar dimulai.
   - Jika komputer mati atau crash, aplikasi secara otomatis mendeteksi pekerjaan yang belum selesai dan melanjutkannya tanpa memaksa operator mengulang capture.
   - File RAW dan lokal tidak akan pernah dihapus secara otomatis setelah transfer.

5. **Live View & Framing Tools**
   - Kamera preview ~30 FPS dengan overlay grid (Rule of Thirds).
   - Standard Tray Crop framing overlay (300 x 200 aspect ratio) dengan pembagi baris core tray dinamis.

6. **10-Point Pre-Flight Check Engine**
   - Memastikan kamera terhubung & siap, sesi aktif, Hole ID & Tray ID terisi, interval valid (`To >= From`), kapasitas storage cukup, dan konfigurasi valid sebelum tombol Capture dapat ditekan.

7. **Review & Retake Workflow**
   - Preview foto hasil crop dan metadata lengkap.
   - "Simpan & Lanjut Tray": Otomatis meningkatkan nomor tray dan interval kedalaman.
   - "Ambil Ulang (Retake)": Menandai capture lama sebagai `SUPERSEDED` di database tanpa menghapus riwayat audit.

8. **Photo Browser & Validasi**
   - Galeri thumbnail dengan pencarian Hole ID, nomor Tray, dan filter status.
   - Auditor integritas data (verifikasi keberadaan RAW/JPG/Thumbnail dan kecocokan hash MD5).

---

## 📡 Panduan Konektivitas Kamera DSLR (Wi-Fi & USB)

### A. Menghubungkan Kamera DSLR via Wi-Fi (Wireless Tethering)
1. **Mode Wi-Fi Kamera:**
   - Di menu kamera DSLR (Canon/Sony/Nikon), aktifkan Wi-Fi dan pilih **Camera Access Point / Direct Connection** (atau hubungkan kamera dan PC ke router Wi-Fi lokal yang sama).
2. **Koneksi di PC:**
   - Buka utilitas vendor kamera di latar belakang (misal: **Canon EOS Utility**, **Sony Imaging Edge Remote**, atau **Nikon NX Tether**).
   - Di aplikasi **Core Photo -> Settings -> CAMERA HARDWARE INTERFACE**:
     - Pilih antarmuka: `Wi-Fi DSLR Wireless Tethering (Canon / Nikon / Sony)`.
     - Masukkan IP kamera dan klik **Ping / Test Wi-Fi** untuk memverifikasi keterjangkauan jaringan.
     - Klik **Auto-Detect** untuk mendeteksi folder penyimpanan tethering bawaan vendor secara otomatis (atau pilih folder kustom melalui tombol `...`).
     - Klik **Save Wi-Fi Setup**.
3. **Pengambilan Foto:**
   - Di layar **Capture -> Tab 2 (Camera Settings)**, pilih antarmuka **Wi-Fi DSLR Wireless Tethering**.
   - Ketika tombol **Capture** ditekan atau tombol shutter fisik kamera ditekan, foto resolusi tinggi akan otomatis ditransfer, dipotong (*crop*), dan diproses ke sistem secara *real-time*.

### B. Menghubungkan Kamera DSLR via Kabel USB
- Sambungkan kamera ke PC menggunakan kabel USB.
- Di Tab 2 layar Capture atau menu Settings, pilih **Direct USB DSLR (Canon/Nikon/Sony)**.
- Sistem menggunakan driver bawaan Windows WIA/PTP tanpa perlu instalasi SDK tambahan.

---

## 📁 Panduan Sinkronisasi Folder Server

1. **Konfigurasi Path Server:**
   - Pada Tab 1 (*Tray Data*) di layar Capture atau di menu **Settings -> STORAGE & SERVER CONFIGURATION**, isi kolom **Target Server Folder** (contoh: `\\192.168.1.50\CorePhotos` atau `D:\ServerShare\CorePhotos`).
2. **Transfer Otomatis:**
   - Setiap kali operator menyetujui foto (*Approve*) di layar **Review**, sistem secara otomatis menduplikasikan foto JPG, RAW, dan metadata CSV ke folder server tujuan.
3. **Sinkronisasi Manual:**
   - Tekan tombol **Sync Session to Server Folder** pada Tab 1 untuk menyinkronkan seluruh riwayat foto sesi aktif ke folder server.

---

## 🏗️ Struktur Project

```text
core-photo/
├── app.py                     # Entry point aplikasi desktop CustomTkinter
├── CorePhoto.spec             # Spesifikasi packaging PyInstaller (.exe)
├── requirements.txt           # Dependensi Python
├── pyproject.toml             # Konfigurasi project & pytest
├── PRD_Core_Photo_AI_Agent.md # Dokumen PRD
│
├── config/
│   ├── config_manager.py      # Pengelola konfigurasi tersentralisasi (Wi-Fi & Server)
│   └── settings.json          # Pengaturan default aplikasi
│
├── core/
│   ├── app_context.py         # Application Context / Service Layer
│   └── logger.py              # Sistem logging rotasi file & konsol
│
├── camera/
│   ├── interface.py           # Abstraksi AbstractCameraAdapter
│   ├── capabilities.py        # Deklarasi capability kamera
│   ├── manager.py             # Central CameraManager & deteksi perangkat
│   └── adapters/
│       ├── wifi_dslr.py       # Adapter Wi-Fi DSLR Wireless Tethering & PTP/IP
│       ├── direct_usb.py      # Adapter Direct USB DSLR (Windows WIA/PTP)
│       ├── hot_folder.py      # Adapter Universal Hot-Folder Ingest
│       └── webcam.py          # Adapter Webcam OpenCV / Simulator
│
├── imaging/
│   ├── crop.py                # Standar crop & framing core tray
│   ├── raw.py                 # Penyimpanan RAW instan & MD5 hash
│   ├── thumbnail.py           # Generator thumbnail ringan
│   └── processor.py           # Pipeline pemrosesan capture & metadata sidecar CSV/JSON
│
├── database/
│   ├── db.py                  # SQLite DatabaseManager dengan migrasi skema & WAL
│   ├── models.py              # Model data & status enums
│   └── repositories.py        # Repository pattern untuk seluruh entitas
│
├── validation/
│   ├── interval.py            # Validasi kedalaman (To >= From)
│   ├── filename.py            # Validasi konvensi ID_Drillhole_NoTray_Interval
│   ├── metadata.py            # Validasi kelengkapan metadata
│   ├── preflight.py           # 10 kriteria pre-flight checks
│   └── runner.py              # Runner validasi ulang sesi
│
├── storage/
│   └── manager.py             # Pengelola path sesi, sanitasi, dan disk space
│
├── diagnostics/
│   └── diagnostics.py         # Diagnostik hardware, log viewer, & crash recovery
│
├── ui/
│   ├── capture.py             # Live View, framing, pre-flight, capture & Wi-Fi selector
│   ├── review.py              # Preview, Simpan/Next Tray, Retake, & Auto-Transfer
│   ├── data_hub.py            # Manajemen sesi, arsip, & galeri foto
│   └── settings.py            # Pengaturan hardware, Wi-Fi tethering, server, & tema
│
└── tests/                     # Suite pengujian otomatis (36 unit tests)
    ├── test_camera.py
    ├── test_capture_workflow.py
    ├── test_data_hub_and_review.py
    ├── test_database.py
    ├── test_imaging.py
    ├── test_review_transfer.py
    ├── test_server_folder.py
    ├── test_storage.py
    ├── test_validation.py
    └── test_wifi_dslr.py
```

---

## 🚀 Cara Menjalankan

### 1. Menjalankan dari Source Code

```bash
# Install dependencies
pip install -r requirements.txt

# Jalankan aplikasi
python app.py
```

### 2. Menjalankan Unit Tests

```bash
pytest -v
```
Seluruh 36 test pengujian otomatis diverifikasi lulus 100%.

### 3. Build Standalone `.exe` Windows

```bash
pyinstaller CorePhoto.spec
```
Executable akan dihasilkan di dalam folder `dist/CorePhoto/CorePhoto.exe`. Operator di lapangan dapat menjalankan `CorePhoto.exe` langsung tanpa perlu install Python, pip, atau membuka terminal.
