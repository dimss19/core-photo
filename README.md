# Core Photo 📷

**Aplikasi Desktop Windows untuk Pengambilan Foto Drill Core Terstruktur & Otomatis**

> Sesuai dengan spesifikasi [PRD Core Photo AI Agent](PRD_Core_Photo_AI_Agent.md).

---

## 🌟 Fitur Utama

1. **Camera Abstraction Layer (Plugin/Adapter Ready)**
   - Mendukung webcam bawaan dan USB camera melalui adapter `WebcamAdapter`.
   - Siap untuk kamera profesional (Canon EDSDK, Nikon SDK, Sony SDK) melalui `AbstractCameraAdapter` tanpa merubah aplikasi utama.
   - Capability detection otomatis (ISO, shutter speed, exposure, zoom).

2. **Full Offline-First Operation**
   - Seluruh alur (Session, Tray, Framing, Capture, Review, Validasi, Browser) berjalan 100% lokal tanpa memerlukan internet.
   - Database SQLite mandiri per sesi (`session.db`) dengan WAL mode untuk ketahanan crash.

3. **Crash Recovery & Data Safety**
   - File RAW disimpan ke disk **sebelum** pemrosesan gambar dimulai.
   - Jika komputer mati atau crash, aplikasi secara otomatis mendeteksi pekerjaan yang belum selesai dan melanjutkannya tanpa memaksa operator mengulang capture.
   - File RAW dan lokal tidak akan pernah dihapus secara otomatis setelah transfer.

4. **Live View & Framing Tools**
   - Kamera preview ~30 FPS dengan overlay grid (Rule of Thirds).
   - Standard Tray Crop framing overlay (300 x 200 aspect ratio).

5. **10-Point Pre-Flight Check Engine**
   - Memastikan kamera terhubung & siap, sesi aktif, Hole ID & Tray ID terisi, interval valid (`To >= From`), kapasitas storage cukup, dan konfigurasi valid sebelum tombol Capture dapat ditekan.

6. **Review & Retake Workflow**
   - Preview foto hasil crop 300x200 dan metadata.
   - "Simpan & Lanjut Tray": Otomatis meningkatkan nomor tray dan interval kedalaman.
   - "Ambil Ulang (Retake)": Menandai capture lama sebagai `SUPERSEDED` di database tanpa menghapus riwayat audit.

7. **Photo Browser & Validasi**
   - Galeri thumbnail dengan pencarian Hole ID, nomor Tray, dan filter status.
   - Auditor integritas data (verifikasi keberadaan RAW/JPG/Thumbnail dan kecocokan hash MD5).

8. **Transfer Server Idempoten**
   - Antrean unggah terpisah dengan token idempotensi untuk mencegah duplikasi data di server pusat.

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
│   ├── config_manager.py      # Pengelola konfigurasi tersentralisasi
│   └── settings.json          # Pengaturan default aplikasi
│
├── core/
│   ├── app_context.py         # Application Context / Service Layer
│   └── logger.py              # Sistem logging rotasi file & konsol
│
├── camera/
│   ├── interface.py           # Abstraksi AbstractCameraAdapter
│   ├── capabilities.py        # Deklarasi capability kamera
│   ├── manager.py             # Camera Manager & deteksi perangkat
│   └── adapters/
│       └── webcam.py          # Adapter Webcam OpenCV (DirectShow/Simulator)
│
├── imaging/
│   ├── crop.py                # Standar crop 300x200 & framing
│   ├── raw.py                 # Penyimpanan RAW instan & MD5 hash
│   ├── thumbnail.py           # Generator thumbnail ringan
│   └── processor.py           # Pipeline pemrosesan capture & metadata sidecar
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
├── transfer/
│   ├── uploader.py            # HTTP client unggah idempoten & retry
│   └── verifier.py            # Pengecekan server receipt
│
├── storage/
│   └── manager.py             # Pengelola path sesi, sanitasi, dan disk space
│
├── diagnostics/
│   └── diagnostics.py         # Diagnostik hardware, log viewer, & crash recovery
│
├── ui/
│   ├── dashboard.py           # Ringkasan sistem & tombol aksi cepat
│   ├── session.py             # Pembuatan & pembukaan sesi
│   ├── capture.py             # Live View, framing, pre-flight, & capture
│   ├── review.py              # Preview, Simpan/Next Tray, & Retake
│   ├── browser.py             # Galeri foto, pencarian, & inspeksi
│   ├── validation.py          # Laporan audit integritas data
│   ├── transfer.py            # Pengaturan server & eksekusi antrean transfer
│   └── settings.py            # Pengaturan tema, diagnostik, & log viewer
│
└── tests/                     # Suite pengujian otomatis (16 unit tests)
    ├── test_camera.py
    ├── test_database.py
    ├── test_imaging.py
    ├── test_storage.py
    ├── test_transfer.py
    └── test_validation.py
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

### 3. Build Standalone `.exe` Windows

```bash
pyinstaller CorePhoto.spec
```
Executable akan dihasilkan di dalam folder `dist/CorePhoto/CorePhoto.exe`.
Operator di lapangan dapat menjalankan `CorePhoto.exe` langsung tanpa perlu install Python, pip, atau membuka terminal.
