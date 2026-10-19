# Pemeriksaan integrasi

- Tiga uji API lulus: siklus end-to-end dan simpan JSON, validasi/missing pose, serta fungsi geometri bersama.
- Regresi test_engine.py asli v0.5.6 lulus, termasuk smoke test kamera memakai test doubles (bukan kamera fisik).
- JavaScript halaman uji dijalankan dengan DOM tiruan dan request HTTP nyata ke uvicorn: 1 bangkit, 1 siklus, file tersimpan; halaman HTTP 200.
- Semua berkas asli selain app.py identik byte per byte dengan STS_Prototype_v056.zip. Di app.py hanya fungsi angle dan measure dipindahkan ke measurements.py dan diimpor kembali.
- Pemeriksaan tidak mencakup kamera langsung, browser grafis, perangkat Windows pengguna, atau akurasi klinis.

Lingkungan uji: Python 3.12, FastAPI 0.144.0, uvicorn 0.54.0, httpx 0.28.1, NumPy 2.3.5. Starlette memberi peringatan deprecation TestClient/httpx; pemeriksaan tetap lulus.
