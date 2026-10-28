# Benchmark RSA dan RSA-CRT

Program ini dibuat untuk membandingkan waktu dekripsi RSA standar dan RSA-CRT pada proyek Matematika Diskrit. Cukup pakai Python 3, tanpa memasang paket tambahan.

Buka PowerShell di folder proyek, lalu cek dulu apakah semua contoh berjalan:

```powershell
py .\test_rsa_benchmark.py
# atau
python .\test_rsa_benchmark.py
```

Tes akan menjalankan 16 kasus dan mencetak PASS atau FAIL untuk masing-masing kasus. Kalau semuanya cocok, baris terakhirnya berbunyi `Hasil: 16/16 PASS, 0 FAIL.` Skrip keluar dengan kode 1 kalau ada kasus yang gagal. Tes berjalan pada salinan skrip di folder sementara.

Untuk mencoba hitungan dari laporan, masukkan p, q, e, dan M lewat terminal:

```powershell
py .\rsa_benchmark.py --p 43 --q 59 --e 13 --message 1819
```

Kalau ingin mengukur waktu dengan prima yang lebih besar, biarkan program membangkitkan p dan q:

```powershell
py .\rsa_benchmark.py --prime-bits 256 512 1024 --e 65537 --message 12345 --trials 100 --warmup 5 --mr-rounds 20
```

`--M` bisa dipakai sebagai pengganti `--message`. Pilih salah satu cara memasukkan prima: isi `--p` dan `--q` sekaligus, atau pakai `--prime-bits`. Tanpa opsi apa pun, program memakai prima 256/512/1024 bit, e=65537, M=1819, 30 percobaan, 3 pemanasan, dan 20 basis Miller-Rabin.

Hasilnya masuk ke `benchmark_results.csv` di folder skrip. Setiap benchmark yang berhasil mengganti hasil sebelumnya.

## Menjalankan Antarmuka Web (Web UI Dashboard)

Selain lewat terminal CLI, Anda dapat menjalankan dashboard visual interaktif berbasis web (cukup dengan pustaka bawaan Python, tanpa perlu install library tambahan):

**Cara 1 (Paling Mudah):**
- Cukup **klik dua kali** file `run_web_ui.bat`.

**Cara 2 (Lewat Terminal PowerShell / CMD):**
```powershell
.\run_web_ui.bat
# atau
py server.py
```

Browser Anda akan otomatis terbuka di `http://localhost:8000`. Fitur web meliputi:
1. **Simulasi & Langkah Matematis**: Perhitungan step-by-step $n, \phi(n), d, d_P, d_Q, q_{inv}$, enkripsi $C$, dan komparasi dekripsi standar vs CRT.
2. **Benchmark & Visualisasi Grafik**: Uji kecepatan multi-bit ($256, 512, 1024$ bit) dengan bar chart waktu eksekusi, line chart rasio *speedup*, dan tombol unduh CSV langsung.
3. **Verifikasi Kasus Uji**: Menjalankan 16 kasus CLI pada salinan sementara dan menampilkan PASS/FAIL berdasarkan keluaran aktual.
4. **Enkripsi Pesan Teks (String)**: Enkripsi kalimat teks bebas (UTF-8) menjadi Ciphertext (HEX & Base64), pemotongan blok modular otomatis ($M < n$), serta bukti dekripsi kembali ke teks asli dengan perbandingan kecepatan RSA Standar vs RSA-CRT.

---

Untuk berbagi tanpa Git, gunakan [paket ZIP](rsa_benchmark_untuk_tim.zip).

## Validasi dan data benchmark

Uji keprimaan memakai Miller-Rabin dengan basis acak independen. Hasil penolakan berarti bukan prima; kandidat yang lolos berstatus kemungkinan prima. Untuk kandidat komposit ganjil, peluang lolos k ronde paling banyak (1/4)^k. Setiap hasil dekripsi tetap diperiksa terhadap pesan asli.

Nilai RSA dikirim sebagai string desimal melalui API agar bilangan besar tetap presisi di browser. Kolom rsa_samples_ns dan crt_samples_ns pada CSV menyimpan seluruh durasi percobaan dalam nanodetik; median dan rerata pada kolom ringkasan menggunakan milidetik. Panjang modulus aktual dapat bernilai 2b-1 atau 2b bit untuk kandidat p dan q masing-masing b bit.

Jalankan `python test_web_api.py` untuk regresi API dan `node test_web_ui.js` untuk aritmetika dan transport integer pada antarmuka. Paket ZIP pada cabang ini mencakup dashboard dan peluncurnya.
Bangun ulang paket setelah perubahan kode dengan `python build_team_zip.py`. Perintah ini memverifikasi bahwa seluruh sumber dalam ZIP sama dengan berkas proyek.

## Versi online

Dashboard tersedia di [proyekmd2-iv.vercel.app](https://proyekmd2-iv.vercel.app).
CSV yang diunduh berisi hasil benchmark pada tab browser Anda. Versi lokal tetap
menyimpan `benchmark_results.csv` seperti biasa.

Untuk menjalankan pemeriksaan deployment, gunakan `python test_vercel.py`.
Konfigurasi Vercel ada di `vercel.json`; deployment memakai Python 3.12 dan
tidak memerlukan paket Python tambahan. Cabang produksi adalah `main` pada
[justhenix/matdis2](https://github.com/justhenix/matdis2).
