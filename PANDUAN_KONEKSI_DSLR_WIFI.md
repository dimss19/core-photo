# PANDUAN PENGGUNAAN KONEKTIVITAS KAMERA DSLR WI-FI & TARGET SERVER FOLDER
**Core Photo v1.0.0 — Industrial Edition**

Dokumen ini memuat panduan operasional lengkap bagi Operator Core Shed dan Geolog dalam mengoperasikan konektivitas kamera DSLR/Mirrorless nirkabel (Wi-Fi) dan integrasi folder server.

---

## 1. Memahami Cara Kerja Konektivitas Wi-Fi DSLR di Core Photo

Sebagian besar kamera DSLR modern (seperti Canon EOS 60D/80D/90D/R series, Sony Alpha series, dan Nikon D/Z series) mengirimkan data foto resolusi penuh (18MP–24MP+ RAW/JPG) melalui protokol **Wireless Tethering**.

Ketika Anda memotret (baik menekan tombol fisik shutter pada kamera maupun tombol **Capture** pada aplikasi):
1. Kamera secara instan mentransmisikan berkas foto beresolusi penuh melalui jaringan Wi-Fi ke PC.
2. Adapter `WiFiDslrAdapter` di Core Photo langsung mendeteksi kedatangan file dalam hitungan milidetik (*high-speed background watcher*).
3. Core Photo memverifikasi ukuran file, membaca metadata EXIF asli kamera (*Make, Model, Serial Number, ISO, Lensa*), menampilkan *frozen preview*, dan memotong gambar sesuai rasio tray core secara otomatis.

---

## 2. Langkah Pengaturan Kamera Berdasarkan Merek

### A. Kamera Canon (Canon EOS 60D, 70D, 80D, 90D, R series)
1. **Pengaturan Wi-Fi di Kamera:**
   - Masuk ke menu kamera -> **Wi-Fi / Wireless Communication Settings**.
   - Pilih opsi **Connect to PC / Remote Control (EOS Utility)**.
   - Pilih metode koneksi **Camera Access Point Mode** (Kamera memancarkan sinyal Wi-Fi sendiri).
2. **Koneksi di Laptop/PC:**
   - Hubungkan Wi-Fi laptop ke nama sinyal (SSID) kamera Canon Anda.
   - Buka aplikasi **Canon EOS Utility** di laptop (aplikasi resmi bawaan Canon).
   - Pada EOS Utility, foto yang masuk akan otomatis diarahkan ke folder `Pictures/EOS Utility` (default).
3. **Pengaturan di Core Photo:**
   - Buka Core Photo -> Masuk ke menu **Settings**.
   - Pada **Camera Hardware Interface**, pilih: `Wi-Fi DSLR Wireless Tethering (Canon / Nikon / Sony)`.
   - Klik tombol **Auto-Detect** (sistem akan otomatis menemukan folder `Pictures/EOS Utility`).
   - Masukkan IP address kamera (jika ada, contoh: `192.168.1.100`) lalu klik **Ping / Test Wi-Fi**.
   - Klik **Save Wi-Fi Setup**.
4. **Mulai Memotret:**
   - Masuk ke layar **Capture**.
   - Pada **Tab 2 (Camera Settings)**, pastikan antarmuka terpilih `Wi-Fi DSLR Wireless Tethering`.
   - Tekan tombol **Capture** di aplikasi atau tekan shutter di kamera DSLR. Foto akan otomatis muncul dan ter-crop di Core Photo.

---

### B. Kamera Sony (Sony Alpha a6000, a7 series, dll)
1. Buka aplikasi **Imaging Edge Desktop (Remote)** di laptop.
2. Di kamera Sony, aktifkan fitur **PC Remote** via Wi-Fi.
3. Hubungkan Wi-Fi laptop ke kamera.
4. Di Core Photo -> **Settings**, klik **Auto-Detect** atau arahkan ke folder tethering Sony (`Pictures/Imaging Edge`).

---

### C. Kamera Nikon (Nikon D series / Z series)
1. Gunakan utilitas **Nikon NX Tether** atau **Wireless Transmitter Utility**.
2. Tentukan folder tujuan penerimaan foto, lalu salin path folder tersebut ke kolom **Wi-Fi Tether Folder** di menu Settings Core Photo.

---

## 3. Panduan Target Server Folder & Auto-Transfer

### A. Cara Menentukan Folder Server
1. Buka layar **Capture** -> **Tab 1 (Tray Data)**.
2. Pada baris **Target Server Folder**, Anda dapat mengetikkan jalur folder jaringan atau klik tombol **...** (Browse).
   - Format path jaringan Windows: `\\192.168.1.50\CorePhotos` atau `\\SERVER_NAME\CoreSharedFolder`
   - Format drive lokal/mapped drive: `Z:\CorePhotos` atau `D:\ServerData`
3. Nilai ini otomatis disimpan ke pengaturan aplikasi.

### B. Auto-Transfer saat Menyetujui Foto (Review Screen)
1. Setelah foto diambil, klik **Review** atau klik **Save** pada pratinjau.
2. Di layar **Review Screen**, periksa foto dan kelengkapan tray.
3. Klik tombol **Approve & Next Tray**:
   - Status foto otomatis menjadi `APPROVED`.
   - Sistem secara otomatis menyalin berkas JPG, berkas RAW, dan memperbarui rekap CSV sesi ke dalam **Target Server Folder**.
   - Operator tidak perlu lagi menyalin berkas secara manual menggunakan flashdisk atau file explorer.

### C. Sinkronisasi Manual Sesi Penuh
Jika terjadi kendala jaringan saat pemotretan:
1. Hubungkan kembali laptop ke jaringan kantor/server.
2. Buka layar **Capture** -> Tab 1 (*Tray Data*).
3. Klik tombol **Sync Session to Server Folder**.
4. Seluruh foto sesi aktif akan disinkronkan secara otomatis tanpa ada foto yang terlewat.

---

## 4. Troubleshooting & Tanya Jawab

| Masalah | Penyebab | Solusi |
|---|---|---|
| **Layar menampilkan webcam laptop, bukan DSLR** | Antarmuka kamera di Tab 2 terpilih `Physical USB Webcam`. | Buka **Tab 2 (Camera Settings)** di layar Capture, ubah dropdown *Camera Interface* menjadi `Wi-Fi DSLR Wireless Tethering`. |
| **Tes Ping Wi-Fi gagal** | Laptop dan kamera tidak berada di jaringan Wi-Fi yang sama. | Pastikan Wi-Fi laptop terhubung ke SSID kamera DSLR (Direct AP) atau keduanya terhubung ke router yang sama. |
| **Foto dijepret tapi tidak masuk ke Core Photo** | Utilitas vendor (EOS Utility / Sony) belum aktif atau folder tethering salah. | Pastikan EOS Utility sedang berjalan di *system tray*, dan periksa path folder tethering di menu Settings Core Photo menggunakan tombol **Auto-Detect**. |
| **Folder server tidak dapat diakses** | Kredensial jaringan Windows belum terbuka. | Buka *File Explorer* Windows, ketik path server (misal `\\192.168.1.50`), masukkan username & password server sekali, lalu centang *Remember my credentials*. |
