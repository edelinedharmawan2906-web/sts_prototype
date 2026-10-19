# Lanjutkan TA: mesin STS lama + FastAPI

Paket ini melanjutkan STS_Prototype_v056. Engine dan aturan STS tidak ditulis ulang. Tujuan tahap ini: memahami bagaimana web memanggil fungsi Python melalui API. Pengujian akurasi formal tetap terpisah.

## 1. Jalankan di Windows

Ekstrak ZIP. Buka folder STS_TA_FastAPI di VS Code, pilih Terminal → New Terminal. Jalankan dari folder yang berisi api.py:

```powershell
py -3.11 -m venv .venv-api
.\.venv-api\Scripts\python.exe -m pip install -r requirements-api.txt
.\.venv-api\Scripts\python.exe -m uvicorn api:app --host 127.0.0.1 --port 8000
```

Jika hanya ada Python 3.12, ganti perintah pertama dengan `py -3.12 -m venv .venv-api`. Aktivasi PowerShell tidak diperlukan. Terminal ini dibiarkan terbuka selama mencoba aplikasi. Tekan Ctrl+C untuk menghentikan server.

Buka http://127.0.0.1:8000 di Chrome/Edge. Klik **Jalankan simulasi 1 siklus**. Harapannya terlihat **1 bangkit lengkap dan 1 siklus**. Klik **Unduh JSON sesi**. Ini data buatan untuk mengecek integrasi, bukan hasil kamera atau bukti akurasi.

Alternatif dari terminal kedua:

```powershell
.\.venv-api\Scripts\python.exe demo_data.py
```

Lihat http://127.0.0.1:8000/docs untuk mencoba endpoint dengan tombol Try it out. http://127.0.0.1:8000/health menunjukkan server hidup.

## 2. Apa yang barusan berjalan?

Browser mengirim JSON berisi waktu dan 33 titik tubuh. FastAPI memeriksa formatnya. `measurements.py` menghitung sudut memakai fungsi asli aplikasi TA. Pengelola sesi melakukan smoothing dan kalibrasi seperti app.py, lalu memanggil `Engine.update()` dalam engine.py. Hasil fase dan hitungan dikirim kembali ke browser.

- **Frontend**: halaman yang kamu buka di browser.
- **Backend**: Python yang berjalan di terminal.
- **API**: pintu masuk fungsi backend, misalnya POST /sessions.
- **POST**: mengirim data atau perintah; **GET**: meminta data.
- **JSON**: bentuk data yang dipahami JavaScript dan Python.
- **localhost / 127.0.0.1**: laptopmu sendiri. Belum cloud.

Urutan request:

1. `POST /sessions` dengan `{"width":640,"height":480}` → simpan session_id.
2. `POST /sessions/{id}/calibration` dengan `{"posture":"duduk","delay":10}`.
3. Kirim `POST /sessions/{id}/frames` berulang berisi `{"t":0.0,"landmarks":[...33 titik...]}`.
4. Sesudah CAL_BERDIRI muncul, kirim perintah kalibrasi posture `berdiri`, tetap kirim frame.
5. Kembali duduk. Backend berpindah dari KEMBALI ke LATIHAN setelah duduk terlihat selama 1 detik.
6. Terus kirim frame dan tampilkan phase, message, complete, cycles dari respons.
7. `POST /sessions/{id}/finish` → simpan di results_api/{id}.json.
8. `GET /sessions/{id}/export` → unduh data.
9. `DELETE /sessions/{id}` → lepaskan memori sesi; file hasil yang telah disimpan tetap ada.

Waktu `t` adalah detik sejak sesi dimulai, harus meningkat. Pose tidak terbaca dikirim sebagai `landmarks: null` dengan timestamp baru, agar backend menjeda penilaian. Jangan mengirim nol sebagai pengganti landmark hilang.

## 3. Hubungkan ke React yang sudah dibuat

`sts-client.ts` adalah penghubung yang disalin ke folder src proyek React lama. Tidak ada mesin hitungan STS baru di file ini. Tambahkan proxy di konfigurasi Vite lama (gabungkan dengan konfigurasi yang sudah ada):

```typescript
server: {
  proxy: {
    '/ta-api': {
      target: 'http://127.0.0.1:8000',
      changeOrigin: true,
      rewrite: path => path.replace(/^\/ta-api/, ''),
    },
  },
},
```

Contoh pemanggilan dari React:

```typescript
import { StsClient } from './sts-client';
const api = new StsClient(); // buat sekali; di komponen simpan dengan useRef
await api.create(video.videoWidth, video.videoHeight);
await api.calibrate('duduk', 10); // tombol aktif walau tubuh belum terbaca

// Di loop MediaPipe: kirim koordinat NORMALIZED sebelum mirror tampilan.
// timestamp detik memakai origin tetap saat sesi dibuat.
const result = await api.frame(t, detectedLandmarks ?? null);
// Tampilkan result.phase, result.message, result.complete, result.cycles.
```

Setiap landmark harus memiliki x, y, z, visibility. Kirim satu request frame pada satu waktu: tunggu selesai sebelum berikutnya. Pakai waktu pengambilan frame asli; jangan mengubah timestamp demi mengejar antrian. Selama kalibrasi hitung mundur, loop frame harus tetap berjalan walau landmark null. Rekaman kalibrasi membutuhkan minimal 1 detik data kontinu sesudah hitung mundur, mengikuti aplikasi TA asli.

Pertahankan dimensi video selama satu sesi. Kamera dan sisi tubuh harus sama dengan TA asli: sisi kiri anatomis (11, 23, 25, 27). Sudut tidak boleh dihitung dari gambar yang sudah di-mirror. Nonaktifkan logika fase dan hitungan versi browser saat memakai backend ini agar satu sumber hitungan dipakai.

**Batas tahap ini:** kode React dari web online sebelumnya tidak ada dalam paket sumber yang tersedia di sesi ini. Modul penghubung sudah disiapkan, tetapi belum dipasang ke web online. Halaman `/` adalah halaman uji koneksi dengan landmark simulasi; belum menyalakan kamera. Untuk menguji backend lokal, buka URL lokal di atas. Web online tidak otomatis terhubung ke laptopmu.

## 4. File yang perlu dipelajari

- `engine.py`: aturan STS asli, tanpa perubahan.
- `app.py`: aplikasi kamera Python asli; hanya impor fungsi sudut dipindahkan ke measurements.py.
- `measurements.py`: fungsi angle dan measure asli yang kini bisa dipakai bersama oleh app.py dan API.
- `api.py`: rute FastAPI dan pengelola sesi.
- `connection_test.html`: contoh browser mengirim request dan menampilkan hasil.
- `demo_data.py`: simulasi yang dapat diulang dari Python.
- `sts-client.ts`: penghubung untuk React lama.

Aplikasi desktop lama tetap menggunakan requirements.txt lama; requirements-api.txt hanya untuk backend. Tidak perlu memasang MediaPipe atau TensorFlow untuk uji koneksi ini. Bantuan tangan tetap tidak dinilai, sesuai versi TA asli.

## 5. Pemeriksaan dan batasan

Jalankan `python -m unittest test_api -v` dengan interpreter venv-api untuk pemeriksaan API; jalankan `python test_engine.py` untuk regresi engine lama. Uji mencakup satu siklus simulasi, kalibrasi, sesi terpisah, data hilang, timestamp salah, landmark tidak lengkap, serta simpan/ekspor JSON.

API masih untuk belajar di satu laptop: satu proses/worker, sesi aktif di RAM, maksimal 10 sesi dan 36000 frame per sesi. Restart menghapus sesi di RAM; hasil yang sudah di-finish tetap di results_api. Belum ada autentikasi, pemuatan ulang riwayat, MQTT, database, model LSTM, atau cloud. Selisih waktu frame di atas batas engine lama menandai data terputus; ini sengaja dipertahankan. Latensi kamera/browser nyata belum diuji.

Sumber dokumentasi FastAPI: https://fastapi.tiangolo.com/tutorial/body-nested-models/ dan https://fastapi.tiangolo.com/tutorial/testing/.
