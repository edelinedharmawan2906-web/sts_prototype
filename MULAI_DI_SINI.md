# Catatan v0.4

Dokumen berikut adalah panduan versi lama. Untuk menjalankan web terbaru dan aturan pribadi, gunakan **MULAI_V04.md** dan **ATURAN_KALIBRASI.md**.

# Pembaruan v0.3

Mulai dari **MULAI_RIWAYAT.md** untuk cara menjalankan dan mencoba database. Panduan kamera v0.2 di bawah tetap berlaku; label versi terbaru adalah v0.3.

# Tahap kamera: React + MediaPipe + backend TA

Versi 0.2 menambahkan kamera browser ke backend yang sudah kamu coba. Engine v0.5.6 tetap sama. Kamera dan MediaPipe berjalan di browser (edge). Titik tubuh dikirim ke Python melalui HTTP. Python menghitung sudut dan menjalankan aturan STS. Hasilnya ditampilkan kembali di React.

## 1. Jalankan di Windows

Ekstrak ZIP baru ke folder tersendiri, agar paket simulasi lama tetap tersimpan. Buka folder STS_TA_Camera (yang berisi api.py) di VS Code. Pilih Terminal → New Terminal.

Jika server lama masih berjalan, tekan Ctrl+C di terminal server lama dahulu. Hanya satu server boleh memakai port 8000.

Buat lingkungan Python lalu pasang kebutuhan:

```powershell
py -3.11 -m venv .venv-api
.\.venv-api\Scripts\python.exe -m pip install -r requirements-api.txt
```

Jika hanya memiliki Python 3.12, gunakan `py -3.12 -m venv .venv-api` untuk perintah pertama. Tidak perlu aktivasi PowerShell.

Jalankan:

```powershell
.\.venv-api\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

Biarkan terminal terbuka, kemudian buka **http://127.0.0.1:8000** di Chrome/Edge pada laptop yang sama. Halaman akan diarahkan ke /camera/.

React sudah dibangun dan model MediaPipe sudah disertakan. **Untuk mencoba kamera, kamu tidak perlu memasang Node.js atau menjalankan npm.** Backend Python juga tidak perlu menginstal MediaPipe Python atau TensorFlow untuk tahap kamera browser ini.

## 2. Coba latihan

1. Siapkan kursi stabil dan tempatkan kamera di sisi kiri tubuh peserta. Yang harus terlihat adalah bahu, pinggul, lutut, serta pergelangan kaki kiri. Kiri mengikuti tubuh peserta.
2. Klik **Aktifkan kamera** dan izinkan penggunaan kamera. Tunggu model dimuat. Pilih kamera yang berbeda sebelum mengaktifkan bila perlu.
3. Atur waktu menuju kursi: 5, 10, 15, atau 20 detik. Default 10 detik.
4. Klik **Rekam duduk** dari dekat laptop. Tombol tetap dapat ditekan meski tubuh belum terlihat penuh. Berjalan ke kursi selama hitung mundur, lalu duduk diam sampai posisi tersimpan. Pengambilan membutuhkan setidaknya 1 detik data kontinu dan 9 sampel valid, mengikuti TA asli.
5. Setelah duduk tersimpan, klik **Rekam berdiri**. Gunakan waktu persiapan untuk menuju posisi berdiri, lalu tahan sampai posisi tersimpan.
6. Kembali duduk. Setelah posisi duduk teramati selama 1 detik, status berpindah otomatis ke **LATIHAN**.
7. Lakukan gerakan STS. Amati fase, bangkit lengkap, siklus, dan sudut dari Python. Bangkit lengkap dan siklus duduk–berdiri–duduk ditampilkan terpisah.
8. Klik **Akhiri & simpan** setelah selesai. Kamera dihentikan, hasil ditulis ke results_api/{id}.json.
9. Klik **Unduh JSON sesi**. File unduhan diberi nama sts-camera-{id}.json. input_source di dalamnya harus browser_camera.

Sebelum menutup tab atau terminal, akhiri sesi terlebih dahulu. Rekaman video tidak disimpan pada tahap ini. Yang dicatat adalah timestamp, landmark, pemeriksaan kualitas, sudut, kalibrasi, dan hasil STS.

Jika tubuh kurang terlihat setelah hitung mundur, pengambilan posisi menunggu/mengulang sampai data kontinu terkumpul. Hitung mundur tidak mengharuskan tubuh terlihat dahulu. Bantuan tangan tetap tidak dinilai pada versi TA ini.

## 3. Apa yang dipelajari di tahap ini?

- **React** menampilkan kamera, tombol, instruksi, angka sudut dan hasil.
- **TypeScript** dipakai untuk menulis kode frontend dan menentukan bentuk data.
- **MediaPipe Tasks Vision Full** membaca gambar dan menghasilkan 33 landmark di browser.
- **Web Worker** menjalankan MediaPipe terpisah dari kode tampilan.
- **sts-client.ts** mengirim landmark/perintah dan menerima jawaban melalui HTTP.
- **FastAPI** menerima JSON dan mengelola sesi.
- **measurements.py** menghitung sudut dengan fungsi asli TA.
- **engine.py** menjalankan fase dan penilaian STS asli.

Alur latihan yang sekarang: Kamera browser → MediaPipe → sts-client.ts → FastAPI → measurements.py → engine.py → jawaban FastAPI → React.

Tampilan kamera dicerminkan agar nyaman dilihat, tetapi data landmark yang dikirim tidak dicerminkan. Web tidak menghitung fase atau repetisi sendiri. Semua sudut yang ditampilkan berasal dari respons Python, dengan sumber geometry_2d.

Paket ini merupakan kelanjutan backend lokalmu, bukan deployment pada website online yang dahulu dibuat. Web online lama tidak berubah. Buka alamat lokal yang tertulis di poin 1.

## 4. Jika terjadi masalah

- **Alamat tidak terbuka:** lihat apakah terminal masih menampilkan Uvicorn running. Jangan menutup terminal server.
- **Port 8000 sudah dipakai:** hentikan server lama dengan Ctrl+C. Lalu jalankan server dari folder baru ini.
- **Kamera ditolak:** izinkan kamera dari pengaturan situs di Chrome/Edge, lalu coba lagi. Pengaturan privasi kamera Windows juga harus mengizinkan browser.
- **Kamera tidak bisa dibuka:** tutup aplikasi lain yang sedang memakai kamera. Pilih kamera lain jika tersedia. Jika kamera laptop masih bermasalah seperti sebelumnya, antarmuka web tetap membutuhkan kamera yang berfungsi; gunakan webcam lain atau coba simulasi.
- **Kamera yang dipilih salah:** akhiri sesi dahulu, pilih kamera di dropdown, lalu mulai sesi baru.
- **Model tidak dimuat:** lihat pesan pada halaman; pastikan ZIP diekstrak lengkap. Berkas frontend/dist/mediapipe dan frontend/dist/assets harus ada. Model di dalam ZIP dimuat dari server lokal, bukan CDN.
- **Kalibrasi terus mengulang:** periksa sisi kiri terlihat, pencahayaan, tubuh tidak terpotong, dan kamu diam saat pengambilan. Buka panel Aliran data & informasi untuk belajar untuk melihat kualitas dan frame/detik.
- **Aliran lambat:** tutup aplikasi berat. Engine lama memperlakukan gap lebih dari 0,3 detik sebagai data terputus. Timestamp tidak dipalsukan untuk menutupi aliran yang lambat.
- **Backend tidak merespons:** akhiri/simpan sesi jika masih memungkinkan. Jika permintaan sudah timeout, restart backend dan mulai sesi baru. Jangan melanjutkan gerakan seolah-olah data tetap terkirim.
- **Terlalu banyak sesi:** prototipe masih membatasi 10 sesi per proses dan 36000 frame per sesi. Simpan/unduh hasil lalu restart backend bila perlu.

Uji simulasi lama tetap ada: **http://127.0.0.1:8000/simulation**. Halaman **/docs** dan **/health** juga tetap tersedia.

## 5. Untuk mempelajari atau mengubah kode React

Bagian ini boleh dipelajari setelah kamera berjalan. Node.js diperlukan hanya bila kamu mengubah source dan ingin membangun ulang frontend.

- `frontend/src/main.tsx`: komponen React, izin kamera, loop kirim frame, tombol dan hasil.
- `frontend/src/sts-client.ts`: penghubung HTTP frontend dengan backend.
- `frontend/src/pose.worker.ts`: memuat MediaPipe dan menjalankan deteksi pose.
- `frontend/src/tracker.ts`: penghubung komponen React dengan Web Worker.
- `frontend/src/types.ts`: bentuk data TypeScript.
- `frontend/src/style.css`: tampilan antarmuka.
- `api.py`: endpoint, kalibrasi, smoothing, ekspor.
- `engine.py`, `measurements.py`, dan modul Python pendukung: analisis dari TA asli.
- `frontend/dist`: hasil build yang dilayani oleh FastAPI.

Setelah memasang Node.js yang kompatibel dengan Vite 6 (Node 22 LTS atau yang sesuai), buka terminal di folder frontend:

```powershell
npm ci
npm run assets
npm run build
```

Perintah assets menyalin WASM dari paket MediaPipe dan mengambil model resmi jika belum ada di public. Proses rebuild ini memerlukan internet. Sesudah build berhasil, refresh halaman kamera yang disajikan FastAPI.

Tidak perlu menyalin source ke web online. Pengujian sekarang dilakukan di localhost. Penggunaan di HP melalui jaringan atau cloud akan memerlukan pengaturan server dan HTTPS tersendiri.

## 6. Status verifikasi

Build React/TypeScript berhasil. Uji API, kalibrasi saat pose hilang, rute aset, ekspor, serta regresi engine lama diuji. Kamera fisik dan tampilan browser grafis belum bisa diuji di lingkungan pembuatan paket; alur kamera perlu dicoba di perangkatmu. Lihat HASIL_UJI.md untuk rincian.

Belum ada LSTM, MQTT, Docker, C++ tambahan, atau AI generatif. SQLite dan panel riwayat ditambahkan pada v0.3. Tahap ini menyambungkan kamera web ke mesin TA lebih dahulu. Evaluasi akurasi formal tetap pekerjaan terpisah.
