# STS Prototype v0.5.6

Aplikasi kamera lokal MediaPipe Full + geometri proyeksi 2D. Pedoman operasional mengikuti PDF Ringkasan_Pedoman_STS_dan_Toleransi dan keputusan pengguna. Belum memakai LSTM. Sumber serta status angka dirinci di PEDOMAN_ANGKA.md.

## Perbaikan v0.5.6

- Kecepatan naik dan progress >8% selama 0.3 detik membentuk kandidat. Bangkit baru dikonfirmasi ketika progress juga >20% (keluar dari rentang duduk seated_progress). Gerak kecil yang berhenti dalam rentang duduk tidak menambah percobaan. Kandidat tetap harus memenuhi pemeriksaan kecepatan kontinu; tanpa condong tetap dapat terdeteksi. Ini perubahan aturan deteksi, bukan sekadar tampilan. Kenaikan sangat kecil yang tidak keluar dari rentang duduk belum dihitung sebagai percobaan bangkit; tidak diklaim sebagai deteksi seat-off klinis.
- Snapshot duduk punya jalur tambahan untuk jitter kecepatan lokal: jendela 0.5 detik, >=3 sampel/cakupan >=0.4 detik, slope absolut <=0.08 perjalanan/detik, rentang progress <=0.04. Semua sampel tetap harus berada dalam rentang duduk dan badan dekat baseline kalibrasi. Setelah stabil, sudut median tetap diperiksa dengan toleransi postur yang sama. Jalur pendek sebelumnya tetap dipakai jika lolos.
- Duduk yang stabil tetapi sudutnya di luar batas tetap BELUM MEMENUHI. Pengamatan hilang/gap menghapus bukti jendela; snapshot lama tidak mengisi data yang tidak tersedia. JSON duduk_awal_metode menyebut short_speed atau bounded_window.
- Replay fitur sesi 102249 menghasilkan 4 percobaan/4 berdiri/3 siklus, sebelumnya 6/4/3. Dua deteksi tambahan saat duduk hilang. Empat posisi awal kini punya bukti; semuanya belum memenuhi, terutama paha >10°. Tidak menaikkan toleransi duduk/berdiri atau menurunkan target 25°.
- Replay Full 190637 juga memperoleh bukti duduk stabil baru untuk dua gerakan terakhir. Hasilnya berubah dari DATA KURANG menjadi BELUM MEMENUHI, bukan menjadi MEMENUHI. Ini perubahan ketersediaan bukti, bukan pengisian snapshot historis.

Semua parameter jendela/batas deteksi tersebut merupakan rancangan teknis yang diuji pada data pengembangan. Tidak menjamin semua gerak kecil tertolak. Tes kamera fisik baru tetap diperlukan.

## Fitur yang dipertahankan dari v0.5.5

- Hasil keseluruhan tetap MEMENUHI / BELUM MEMENUHI / BELUM DAPAT DINILAI. Duduk awal, target condong >=25°, dan berdiri lengkap tetap menjadi syarat. Angka tidak dilonggarkan berdasarkan anotasi 12 frame.
- Panel menampilkan nilai median duduk, target, dan hasil masing-masing pemeriksaan; puncak condong dan status berdiri terakhir. Rincian penilaian_tahap dalam JSON mencakup data, target, dan status. Baris hasil terakhir merujuk percobaan yang sudah selesai, bukan percobaan yang sedang berlangsung.
- Bantuan tangan DINONAKTIFKAN di aplikasi. Nilai hand=False pada kolom kompatibilitas bukan bukti tidak menggunakan tangan. Gunakan metadata hand_warning.enabled=false dan bantuan_tangan.dinilai=false.
- Video kamera tanpa gambar skeleton/teks, waktu setiap frame, 33 landmark mentah, dan sudut mentah disimpan sejak awal pembacaan termasuk kalibrasi dan pose ditolak. Tidak perlu merekam layar untuk pemeriksaan berikutnya.
- R tidak mereset sesi yang sudah memiliki data latihan. Tekan Q lalu buka ulang untuk sesi baru, supaya JSON dan CSV tidak berbeda riwayat.

## Menjalankan di Windows

Ekstrak ke folder baru. Jika memakai folder lama, salin semua file paket; pertahankan .venv dan results yang sudah ada. Dependensi sama dengan v054/v055, gunakan Python 3.11.

Instalasi pertama saja:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\python.exe -m pip install -r requirements.txt
```

Tes dan jalankan dari folder yang berisi app.py:

```powershell
.\.venv\Scripts\python.exe test_engine.py
.\.venv\Scripts\python.exe app.py --source 0 --delay 10 --model full
```

Kamera gagal: tutup aplikasi kamera lain, coba --source 1 atau --backend msmf. Heavy tersedia melalui --model heavy, bukan jaminan lebih akurat.

## Langkah satu sesi

1. Tempatkan kamera tetap di samping kiri, seluruh tubuh dan kaki terlihat ketika duduk dan berdiri.
2. Klik jendela kamera, tekan D. Kembali duduk selama timer, diam sampai DUDUK TERSIMPAN.
3. Tekan B. Berdiri selama timer, diam sampai BERDIRI TERSIMPAN.
4. Kembali duduk, tunggu LATIHAN. Duduk diam sekitar 1–2 detik sebelum mulai. Lakukan STS dan berdiri diam sejenak, kemudian kembali duduk. Periksa bahwa badan tetap terlihat.
5. Tekan Q untuk menyimpan dan keluar. Kirim file satu sesi dari folder results. Bila video besar, kompres seluruh hasil sesi menjadi ZIP.

Rekaman otomatis dimulai saat aplikasi menerima gambar pertama. Tidak mengunggah video/data ke layanan luar. AVI MJPG bisa besar. Jika codec gagal, terminal dan panel menunjukkan kegagalan; data mentah tetap disimpan. Periksa camera_*.avi bisa diputar setelah Q.

## Aturan operasional

- Duduk awal: badan-paha 90 +/-10°, badan-vertikal <=10°, paha-horizontal <=10°, jarak horizontal kaki-lutut <=0.15 panjang torso. Menggunakan median jendela duduk stabil 0.5 detik, minimal cakupan 0.4 detik/3 sampel, bukti berusia maksimal 2 detik.
- Condong: puncak sinyal tersaring dalam persiapan hingga transisi bangkit >=25°. Deteksi ini memakai besar sudut, belum membedakan arah depan/belakang. Puncak bukan sudut yang harus dipertahankan sepanjang gerakan.
- Berdiri: progress >=0.9 dan hip/knee >=165°, bersama kestabilan selama >=0.3 detik. Progress=(y_duduk-y_sekarang)/(y_duduk-y_berdiri). Tinggi pinggul kiri adalah proksi posisi, bukan pengukuran CoM seluruh tubuh.
- Kestabilan v054 dipertahankan: kecepatan jendela pendek absolut <=0.08 perjalanan/detik ATAU plateau 0.5 detik (cakupan >=0.4 detik, >=3 sampel, slope absolut <=0.08, excursion <=0.04). Seluruh syarat tinggi/sudut dan tahan 0.3 detik tetap wajib.
- Asal duduk teramati, kenaikan terkonfirmasi setelah keluar dari rentang duduk >20%, dan kembali duduk dipakai untuk hitungan. Postur duduk yang belum memenuhi tidak menghalangi hitungan bangkit.
- Siklus bertambah ketika kembali duduk setelah berdiri lengkap. Berdiri lengkap dihitung tersendiri saat dikonfirmasi.
- Frame ditolak atau celah >0.3 detik mereset jendela/timer. Data kurang tidak diberi label gerakan salah. Pengamatan terputus selama percobaan membuat kualitas keseluruhan belum dapat dinilai.

Ambang toleransi 10°/15°, stabil 0.08, dan sejumlah ambang teknis masih parameter sementara. PDF menggunakan X; X belum diestimasi dari pembanding independen. Angka ini dicatat eksplisit dalam config, bukan dihitung dari MAE anotasi lalu dijadikan toleransi tubuh. Label benar/salah bermakna kepatuhan pada aturan operasional tersebut; bukan diagnosis klinis.

## Berkas hasil (satu ID sesi yang sama)

- session_*.json: konfigurasi, kalibrasi, hitungan, status keseluruhan, alasan, penilaian_tahap. Nilai null berarti tidak cukup data; jangan dibaca sebagai false.
- angles_*.csv: sudut TERFILTER dan progress hanya selama latihan pada frame diterima. frame_index menunjuk frame sumber; video_frame_index menunjuk frame AVI (mulai 0).
- diagnostics_*.csv: kualitas dan waktu proses setiap frame dibaca, termasuk frame ditolak dan kalibrasi. Visibility bukan akurasi.
- raw_*.jsonl: satu objek per frame dengan time, frame_index, video_frame_index, mode, accepted/reason, image_size=[lebar,tinggi], raw_angles dan landmarks. Landmark x/y adalah koordinat gambar ternormalisasi, z relatif model bukan meter. Sudut mentah dihitung dari piksel gambar, tanpa EMA. Jika kualitas geometri tidak lolos raw_angles=null; landmark yang terdeteksi tetap disimpan. Pose tidak terdeteksi memberi landmarks=null.
- frames_*.csv: relasi frame_index (mulai 1), video_frame_index, time dan video_written. Time adalah detik dari awal sesi kamera. Pakai time ini untuk analisis kecepatan/durasi.
- camera_*.avi: input kamera SEBELUM overlay, hanya frame yang berhasil dibaca dan ditulis aplikasi. Bukan rekaman semua frame sensor. Codec MJPG tidak lossless. Tidak merekam suara.

PENTING: AVI memiliki FPS putar tetap; laju kamera aktual berubah sesuai pemrosesan. Durasi AVI bisa berbeda dari waktu sesi. Cocokkan frame dengan frames CSV; jangan memakai waktu putar AVI sebagai waktu asli. Memasukkan AVI kembali dengan --source saja tidak memulihkan timing asli atau kalibrasi lama. CSV/JSON lama dipakai untuk replay engine. Input file video masih memiliki kalibrasi interaktif, bukan replay sesi otomatis.

## Verifikasi

Jalankan test_engine.py tanpa kamera. Tes mencakup sinyal simulasi, batas, data hilang, hitungan/asesmen terpisah, dan enam fixture sesi fitur pengembangan. Sesi 002619 dan 102249 tetap 4 berdiri lengkap/3 siklus, keempat asesmen belum memenuhi karena duduk awal. Pada 102249, percobaan tambahan turun dari 6 menjadi 4. Tes alur input/output memakai perangkat buatan: video direkam sebelum skeleton, data mentah, mapping waktu, dan frame ditolak tetap tersimpan.

Tes tersebut bukan ekstraksi ulang MediaPipe dari video, bukan evaluasi independen, dan tidak menguji kamera/codec fisik. Uji satu sesi kamera berikutnya untuk memeriksa video bisa diputar serta semua file tersimpan.
