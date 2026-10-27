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
py .\rsa_benchmark.py --prime-bits 256 512 1024 --e 65537 --message 12345 --trials 100 --warmup 5 --fermat-rounds 20
```

`--M` bisa dipakai sebagai pengganti `--message`. Pilih salah satu cara memasukkan prima: isi `--p` dan `--q` sekaligus, atau pakai `--prime-bits`. Tanpa opsi apa pun, program memakai prima 256/512/1024 bit, e=65537, M=1819, 30 percobaan, 3 pemanasan, dan 20 basis Fermat.

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
3. **Verifikasi Kasus Uji**: Menjalankan 16 kasus uji otomatis dengan badge status visual.
4. **Enkripsi Pesan Teks (String)**: Enkripsi kalimat teks bebas (UTF-8) menjadi Ciphertext (HEX & Base64), pemotongan blok modular otomatis ($M < n$), serta bukti dekripsi kembali ke teks asli dengan perbandingan kecepatan RSA Standar vs RSA-CRT.

---

[Panduan presentasi](PANDUAN_PRESENTASI_RSA.md) menghubungkan flowchart dengan fungsi di kode. [Alur pengujian](FLOW_TESTING.md) menjelaskan diagram alir dan tahapan verifikasi tes. [Daftar kasus uji](KASUS_UJI_RSA.md) memuat input dan hasil yang dicek oleh skrip tes. Untuk berbagi tanpa Git, kirim [paket ZIP](rsa_benchmark_untuk_tim.zip).
