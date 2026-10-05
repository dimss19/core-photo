# PRD --- Aplikasi Pengambilan Foto Core

**Versi:** 1.0 --- AI Agent Ready\
**Status:** Draft\
**Platform:** Windows Desktop\
**Arsitektur:** Full Python\
**UI:** CustomTkinter\
**Kamera tahap awal:** Webcam\
**Target kamera:** Kamera profesional melalui SDK/API vendor

------------------------------------------------------------------------

## 1. Ringkasan

Aplikasi Pengambilan Foto Core adalah aplikasi desktop Windows untuk
membantu operator melakukan dokumentasi foto drill core secara
terstruktur.

Aplikasi harus dapat digunakan sepenuhnya tanpa pengguna berinteraksi
langsung dengan kode, Python, SDK, API, terminal, atau konfigurasi
teknis.

Seluruh proses utama berjalan secara lokal dan tidak bergantung pada
koneksi internet:

-   membuat/melanjutkan sesi;
-   menghubungkan kamera;
-   mengisi data tray;
-   Live View;
-   framing;
-   capture;
-   review dan retake;
-   menghasilkan RAW, JPG, dan Thumbnail;
-   menyimpan metadata;
-   validasi;
-   browsing foto;
-   dan penyimpanan lokal.

Koneksi jaringan hanya digunakan untuk proses transfer data ke server.

Implementasi awal menggunakan webcam untuk menguji seluruh workflow.
Kamera profesional akan ditambahkan kemudian melalui sistem **Camera
Adapter / Plugin** tanpa mengubah core application.

------------------------------------------------------------------------

## 2. Tujuan

1.  Membuat aplikasi desktop pengambilan foto core yang mudah digunakan.
2.  Memastikan setiap foto memiliki hubungan yang benar dengan Hole,
    Tray, dan interval core.
3.  Memungkinkan seluruh proses capture dan processing berjalan offline.
4.  Menghasilkan RAW, JPG, dan Thumbnail sesuai kebutuhan.
5.  Menyediakan validasi sebelum data dianggap selesai.
6.  Menyediakan penyimpanan lokal yang aman dan tahan terhadap crash.
7.  Menyediakan transfer ke server ketika jaringan tersedia.
8.  Membuat arsitektur kamera yang dapat mendukung berbagai vendor dan
    generasi kamera.
9.  Memungkinkan penambahan dukungan kamera baru melalui adapter/plugin
    tanpa mengubah core application.
10. Menghasilkan aplikasi final dalam bentuk `.exe`.

------------------------------------------------------------------------

## 3. Non-Goals

Fitur berikut tidak termasuk scope:

-   Visualisasi 3D drillhole/core.
-   Pembuatan file `.OBJ` dan `.MTL`.
-   Analisis mineral/emas/nikel berbasis AI.
-   Interpretasi isi foto menggunakan AI.
-   Pengguna harus memahami coding.
-   Pengguna harus menjalankan Python dari terminal.
-   Pengguna harus menginstal atau mengonfigurasi SDK kamera secara
    manual jika dapat diotomatisasi oleh installer.
-   Core application bergantung langsung pada satu vendor kamera.

------------------------------------------------------------------------

## 4. Target User

### Operator

Operator menggunakan aplikasi untuk:

-   membuat atau membuka sesi;
-   mengisi data tray;
-   melihat Live View;
-   melakukan capture;
-   memeriksa hasil;
-   retake;
-   validasi;
-   dan transfer data.

### Teknisi/Admin

Teknisi/Admin menggunakan aplikasi yang sama dan dapat melakukan
pekerjaan operator, serta dapat:

-   mendeteksi kamera;
-   memilih kamera yang tersedia;
-   melihat informasi kamera;
-   melakukan reconnect;
-   menjalankan diagnostics;
-   melihat Camera Support Package;
-   mengatur konfigurasi aplikasi;
-   memeriksa log;
-   mengatur koneksi server;
-   dan melakukan troubleshooting.

Tidak ada dua aplikasi berbeda. Semua pengguna menggunakan aplikasi yang
sama dengan prinsip **simple by default, technical when needed**.

------------------------------------------------------------------------

# 5. Prinsip UX

## 5.1 Tidak Ada Coding untuk User

User tidak boleh perlu:

-   membuka terminal;
-   menjalankan Python;
-   memasukkan command;
-   mengedit source code;
-   memilih SDK secara manual;
-   mengatur API kamera secara manual;
-   mengedit file konfigurasi untuk penggunaan normal.

## 5.2 Teknologi Disembunyikan

User melihat:

> Camera: Canon EOS R7 --- Connected

Bukan:

> Canon EDSDK vX.X loaded successfully.

Informasi teknis tetap tersedia pada bagian **Diagnostics** untuk
teknisi.

## 5.3 Simple by Default

Flow utama harus sesingkat mungkin:

``` text
Dashboard
→ Session
→ Tray
→ Pre-flight
→ Live View
→ Capture
→ Review
→ Validation
→ Next Tray
→ Final Validation
→ Transfer
```

------------------------------------------------------------------------

# 6. User Flow

``` text
START
  ↓
Dashboard
  ↓
Camera Check
  ↓
New Session / Continue Session
  ↓
Session Setup
  ↓
Capture Tray
  ↓
Isi Data Tray
  ↓
Pre-flight Check
  ↓
Live View
  ↓
Framing / Grid / Zoom / Tray Crop
  ↓
Capture
  ↓
Save RAW
  ↓
Image Processing
  ├── JPG
  └── Thumbnail
  ↓
Review
  ├── Retake → Capture
  └── Save
       ↓
Validation
  ├── Invalid → Perbaiki → Validation ulang
  └── Valid
       ↓
Tray Complete
  ↓
Masih ada tray?
  ├── Ya → Capture Tray
  └── Tidak
       ↓
Final Validation
  ↓
Transfer
  ├── Server tersedia → Upload → Verify
  └── Server tidak tersedia → Tetap simpan lokal
       ↓
DONE
```

------------------------------------------------------------------------

# 7. Camera Architecture

## 7.1 Prinsip

Core application tidak boleh bergantung langsung pada API/SDK vendor.

Gunakan abstraction layer:

``` text
Core Application
       ↓
Camera Interface
       ↓
Camera Manager
       ↓
Camera Adapter / Plugin
       ↓
Vendor SDK / API / Standard Interface
       ↓
Driver / OS Interface
       ↓
Camera
```

## 7.2 Camera Interface

Core application hanya mengenal operasi standar seperti:

``` python
connect()
disconnect()
get_status()
get_info()
start_live_view()
stop_live_view()
capture()
set_setting()
get_setting()
```

Adapter bertugas menerjemahkan operasi tersebut ke API kamera
masing-masing.

## 7.3 Webcam sebagai Implementasi Pertama

Tahap awal wajib memiliki:

``` text
WebcamAdapter
    ↓
OpenCV
    ↓
Webcam
```

Webcam digunakan untuk menguji:

-   connection;
-   Live View;
-   capture;
-   preview;
-   retake;
-   processing;
-   storage;
-   validation;
-   dan workflow keseluruhan.

## 7.4 Kamera Masa Depan

Kamera vendor baru harus dapat ditambahkan seperti:

``` text
FutureCameraAdapter
    ↓
Future Camera SDK/API
    ↓
Future Camera
```

Core application tidak boleh perlu diubah hanya karena kamera baru
ditambahkan.

## 7.5 Camera Capability

Setiap adapter harus mendeklarasikan kemampuan kamera:

``` text
capture
live_view
iso
exposure
aperture
focus
zoom
flash
metering
```

UI hanya menampilkan pengaturan yang didukung kamera.

------------------------------------------------------------------------

# 8. Camera Setup

Pada first run:

``` text
Camera Setup
↓
Detect Camera
↓
Identify Camera
↓
Find Compatible Camera Package
↓
Test Connection
↓
Camera Ready
```

Jika beberapa kamera tersedia:

``` text
Select Camera

○ Camera A — Ready
○ Camera B — Ready
○ Camera C — Not Supported
```

User tidak memilih SDK/API.

Jika kamera tidak didukung:

> Kamera terdeteksi tetapi belum didukung oleh aplikasi.

Tampilkan tombol:

-   Try Again
-   Diagnostics
-   Contact Support

Detail teknis hanya tersedia pada Diagnostics.

------------------------------------------------------------------------

# 9. Pre-flight Check

Sebelum tombol Capture aktif, sistem harus memeriksa:

-   Camera connected;
-   Camera ready;
-   Session aktif;
-   Hole ID terisi;
-   Tray ID terisi;
-   Interval valid;
-   Tray data lengkap;
-   Storage tersedia;
-   Tray Crop tersedia;
-   Camera configuration valid.

Jika gagal, Capture harus dinonaktifkan dan user diberi tindakan yang
jelas.

------------------------------------------------------------------------

# 10. Session

Session mencakup:

-   Date;
-   Operator;
-   Site.

User dapat:

-   New Session;
-   Continue Session.

Session harus autosave.

Jika aplikasi crash atau komputer mati, session dapat dilanjutkan.

------------------------------------------------------------------------

# 11. Data Tray

Field:

-   Hole ID;
-   Tray ID;
-   Core Interval From;
-   Core Interval To;
-   Tray Rows;
-   Tray Length;
-   Tray Width;
-   Comments.

Validasi:

-   field wajib harus terisi;
-   `To >= From`;
-   nilai numerik harus valid;
-   Tray ID harus sesuai aturan;
-   filename harus mengikuti konvensi yang ditentukan.

Jika `To < From`, Capture dinonaktifkan.

------------------------------------------------------------------------

# 12. Live View

Live View harus menyediakan:

-   camera preview;
-   Grid;
-   Zoom;
-   Tray Crop;
-   framing area.

Tray Crop menjadi referensi pemrosesan JPG dan Thumbnail.

Ukuran standar hasil crop:

``` text
300 × 200
```

------------------------------------------------------------------------

# 13. Capture

Urutan capture:

``` text
Pre-flight
↓
Capture
↓
Simpan RAW terlebih dahulu
↓
Catat metadata
↓
Generate JPG
↓
Generate Thumbnail
↓
Hitung MD5
↓
Validation
```

RAW harus disimpan sebelum proses berikutnya sehingga hasil capture
tidak hilang apabila processing gagal.

------------------------------------------------------------------------

# 14. Review dan Retake

Setelah capture:

``` text
Preview
├── Retake
└── Save
```

Jika Retake:

-   capture sebelumnya ditandai sebagai superseded/retaken;
-   capture baru menjadi kandidat aktif;
-   jangan menghapus data audit secara diam-diam.

------------------------------------------------------------------------

# 15. Output

Setiap capture menghasilkan:

``` text
RAW
JPG
Thumbnail
```

JPG dan Thumbnail menggunakan Tray Crop.

Filename mengikuti konvensi existing:

``` text
ID_Drillhole_NoTray_IntervalKedalaman
```

Contoh:

``` text
Core01_1_000.00_2.60.jpg
```

------------------------------------------------------------------------

# 16. Metadata

Metadata minimal:

-   Hole ID;
-   Tray ID;
-   Core Interval From;
-   Core Interval To;
-   Path;
-   Comments;
-   Date;
-   Name/Operator;
-   Site;
-   MD5;
-   Timestamp;
-   Tray Rows;
-   Tray Length;
-   Tray Width;
-   Tray Crop;
-   Camera Model;
-   Camera Serial Number jika tersedia;
-   Processing Version;
-   Application Version.

------------------------------------------------------------------------

# 17. Local Storage

Semua proses utama harus tetap dapat dilakukan tanpa jaringan.

Contoh struktur:

``` text
CorePhotoData/
├── Sessions/
│   └── SITE_YYYYMMDD/
│       ├── RAW/
│       ├── JPG/
│       ├── THUMBNAIL/
│       └── session.db
├── Logs/
├── Config/
└── Backup/
```

Jika Drillhole ID yang sama digunakan pada pekerjaan berikutnya, sistem
harus membuat storage session baru sehingga data lama tidak tertimpa.

------------------------------------------------------------------------

# 18. Database

Gunakan **SQLite**.

Entitas minimal:

``` text
sessions
trays
photos
camera_devices
transfers
validation_results
application_events
```

Status foto:

``` text
DRAFT
CAPTURED
PROCESSING
PROCESSED
VALID
INVALID
READY_TO_TRANSFER
TRANSFERRING
TRANSFERRED
TRANSFER_FAILED
```

------------------------------------------------------------------------

# 19. Crash Recovery

Aplikasi harus dapat menemukan pekerjaan yang belum selesai.

Contoh:

``` text
RAW tersimpan
↓
Aplikasi crash
↓
Aplikasi dibuka
↓
Recovery Check
↓
RAW ditemukan tanpa JPG
↓
Resume Processing
```

User tidak boleh dipaksa mengulang capture jika file RAW yang valid
sudah tersimpan.

------------------------------------------------------------------------

# 20. Validation

Validation minimal:

-   kelengkapan data tray;
-   validitas interval;
-   filename;
-   metadata;
-   keberadaan RAW;
-   keberadaan JPG;
-   keberadaan Thumbnail;
-   integritas file;
-   konsistensi database;
-   status processing.

Validation harus dapat dijalankan ulang.

------------------------------------------------------------------------

# 21. Photo Browser

Fitur:

-   Search Hole ID;
-   Search Tray ID;
-   Search interval;
-   thumbnail navigation;
-   preview ukuran besar;
-   metadata;
-   status validation;
-   status transfer.

Tidak membutuhkan visualisasi 3D.

------------------------------------------------------------------------

# 22. Transfer

Transfer adalah proses terpisah dari capture.

Flow:

``` text
Select Data
↓
Check Server
↓
Upload
↓
Verify
↓
Mark as TRANSFERRED
```

Jika server tidak tersedia:

``` text
Capture tetap berjalan
↓
Data tetap lokal
↓
Transfer dilakukan kemudian
```

File lokal tidak dihapus setelah transfer berhasil.

------------------------------------------------------------------------

# 23. Retry dan Idempotency

Transfer harus aman jika dijalankan berulang.

Contoh:

``` text
Upload Photo A
↓
Network timeout
↓
Retry
```

Sistem tidak boleh membuat duplicate record di server jika upload
sebenarnya sudah berhasil.

Gunakan identifier unik dan status transfer.

------------------------------------------------------------------------

# 24. Error Handling

Pesan error harus human-readable.

Contoh:

### Kamera

> Kamera tidak terhubung. Periksa kabel USB dan coba lagi.

### Storage

> Penyimpanan hampir penuh. Kosongkan ruang sebelum melanjutkan.

### Validation

> Core Interval To tidak boleh lebih kecil dari Core Interval From.

### Transfer

> Server tidak dapat diakses. Data tetap aman di komputer dan dapat
> ditransfer nanti.

Technical details tersedia di Diagnostics/Logs.

------------------------------------------------------------------------

# 25. Diagnostics

Menu Diagnostics harus membantu teknisi tanpa mengharuskan coding.

Informasi:

-   Camera detection;
-   Camera connection;
-   Camera model;
-   Camera package;
-   SDK/API status;
-   Live View test;
-   Capture test;
-   Storage test;
-   Database test;
-   Server connection test;
-   Log viewer;
-   Export diagnostics.

------------------------------------------------------------------------

# 26. Teknologi yang Digunakan

-   Python 3.x
-   CustomTkinter
-   Tkinter
-   OpenCV
-   Pillow
-   rawpy
-   SQLite
-   Piexif / ExifRead
-   hashlib / MD5
-   Requests / HTTPX
-   JSON / TOML
-   Python Logging
-   PyInstaller
-   Inno Setup

Camera SDK/API akan mengikuti vendor kamera dan diisolasi melalui Camera
Adapter.

------------------------------------------------------------------------

# 27. Struktur Project yang Direkomendasikan

``` text
core-photo/
├── app.py
├── requirements.txt
├── pyproject.toml
│
├── ui/
│   ├── dashboard.py
│   ├── session.py
│   ├── capture.py
│   ├── review.py
│   ├── browser.py
│   ├── validation.py
│   ├── transfer.py
│   └── settings.py
│
├── camera/
│   ├── interface.py
│   ├── manager.py
│   ├── capabilities.py
│   └── adapters/
│       └── webcam.py
│
├── imaging/
│   ├── processor.py
│   ├── crop.py
│   ├── raw.py
│   └── thumbnail.py
│
├── database/
│   ├── db.py
│   ├── models.py
│   └── repositories.py
│
├── validation/
│   ├── filename.py
│   ├── interval.py
│   └── metadata.py
│
├── transfer/
│   ├── uploader.py
│   └── verifier.py
│
├── storage/
│   └── manager.py
│
├── diagnostics/
│   └── diagnostics.py
│
└── config/
    └── settings.json
```

------------------------------------------------------------------------

# 28. Packaging

Aplikasi final harus dapat dijalankan sebagai Windows `.exe`.

Target user:

``` text
Install CorePhoto.exe
↓
Open application
↓
Use application
```

User tidak perlu:

-   install Python;
-   menjalankan pip;
-   membuka terminal;
-   menjalankan script;
-   mengedit source code.

PyInstaller digunakan untuk packaging aplikasi.

------------------------------------------------------------------------

# 29. AI Agent Development Rules

AI coding agent wajib mengikuti aturan berikut:

1.  Jangan mengubah arsitektur Camera Interface hanya untuk membuat
    webcam bekerja.
2.  Webcam harus menjadi adapter pertama dari Camera Interface.
3.  Jangan menaruh kode OpenCV langsung di UI.
4.  UI hanya berkomunikasi dengan service/application layer.
5.  Camera adapter tidak boleh mengandung business logic.
6.  Image processing tidak boleh bergantung pada UI.
7.  Database access tidak boleh tersebar di UI.
8.  Semua file path dikelola oleh Storage Manager.
9.  Semua konfigurasi dikelola oleh Configuration Manager.
10. Semua error penting dicatat menggunakan logging.
11. Setiap operasi capture harus dapat dipulihkan setelah crash.
12. Jangan hardcode path Windows.
13. Jangan hardcode vendor kamera pada core application.
14. Jangan menganggap semua kamera memiliki capability yang sama.
15. Gunakan capability detection.
16. Jangan meminta user melakukan konfigurasi teknis untuk workflow
    normal.
17. Technical configuration hanya melalui Diagnostics/Settings.
18. Semua perubahan schema database harus memiliki migration strategy.
19. Semua status workflow harus eksplisit.
20. Jangan menghapus RAW atau file lokal secara otomatis setelah
    transfer.

------------------------------------------------------------------------

# 30. Development Phases

## Phase 1 --- Webcam Prototype

Target:

-   CustomTkinter UI;
-   Webcam detection;
-   Live View;
-   Capture;
-   Review;
-   Retake;
-   Save;
-   Crop;
-   JPG;
-   Thumbnail.

## Phase 2 --- Core Workflow

Tambahkan:

-   Session;
-   Tray;
-   SQLite;
-   Metadata;
-   Validation;
-   Photo Browser;
-   Autosave;
-   Crash recovery;
-   Logging.

## Phase 3 --- Transfer

Tambahkan:

-   Server configuration;
-   Upload;
-   Verification;
-   Retry;
-   Transfer status;
-   Offline queue.

## Phase 4 --- Camera Integration

Tambahkan:

-   Camera Manager;
-   Camera Package Manager;
-   Vendor Adapter;
-   SDK/API integration;
-   Camera capability detection;
-   Diagnostics.

## Phase 5 --- Production Packaging

-   PyInstaller;
-   Installer;
-   Configuration migration;
-   Logging;
-   Recovery test;
-   Camera test;
-   Storage test;
-   Transfer test;
-   Final acceptance testing.

------------------------------------------------------------------------

# 31. Acceptance Criteria

Aplikasi dianggap berhasil jika:

-   User dapat menjalankan aplikasi melalui `.exe`.
-   User tidak membutuhkan Python/terminal untuk menjalankan aplikasi.
-   Webcam dapat digunakan sebagai kamera pertama.
-   User dapat membuat session.
-   User dapat mengisi data tray.
-   Capture tidak dapat dilakukan ketika data wajib invalid.
-   Live View berjalan.
-   Capture berhasil disimpan.
-   RAW/JPG/Thumbnail dihasilkan.
-   Retake berjalan.
-   Metadata tersimpan.
-   Validation berjalan.
-   Photo Browser dapat mencari foto.
-   Aplikasi tetap dapat capture tanpa internet.
-   Transfer dapat dilakukan ketika jaringan tersedia.
-   Transfer gagal tidak menyebabkan data lokal hilang.
-   Aplikasi dapat recovery setelah crash.
-   Kamera vendor dapat ditambahkan melalui adapter tanpa mengubah core
    workflow.
-   Kamera dengan capability berbeda tidak menyebabkan aplikasi crash.
-   User tidak perlu memahami SDK/API kamera untuk penggunaan normal.

------------------------------------------------------------------------

# 32. Prinsip Arsitektur Utama

``` text
              CORE PHOTO
                   │
          ┌────────▼────────┐
          │ Application Core│
          └────────┬────────┘
                   │
       ┌───────────┼────────────┐
       ▼           ▼            ▼
    Camera      Imaging       Storage
    Manager     Service       Manager
       │
       ▼
Camera Interface
       │
       ▼
Camera Adapter
       │
       ├── Webcam Adapter
       ├── Canon Adapter
       ├── Nikon Adapter
       ├── Sony Adapter
       └── Future Adapter
```

**Invariant utama:**

> Core application tidak boleh mengetahui detail API/SDK vendor kamera.

Dengan prinsip ini, implementasi webcam dapat digunakan untuk menguji
seluruh sistem sekarang, sedangkan dukungan kamera profesional dapat
ditambahkan kemudian tanpa merombak workflow utama.
