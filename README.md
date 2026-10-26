# Benchmark RSA dan RSA-CRT

Program ini dibuat untuk membandingkan waktu dekripsi RSA standar dan RSA-CRT pada proyek Matematika Diskrit. Cukup pakai Python 3, tanpa memasang paket tambahan.

Buka PowerShell di folder proyek, lalu cek dulu apakah semua contoh berjalan:

```powershell
python .\test_rsa_benchmark.py
```

Tes akan menjalankan 16 kasus dan mencetak PASS atau FAIL untuk masing-masing kasus. Kalau semuanya cocok, baris terakhirnya berbunyi `Hasil: 16/16 PASS, 0 FAIL.` Skrip keluar dengan kode 1 kalau ada kasus yang gagal. Tes berjalan pada salinan skrip di folder sementara.

Untuk mencoba hitungan dari laporan, masukkan p, q, e, dan M lewat terminal:

```powershell
python .\rsa_benchmark.py --p 43 --q 59 --e 13 --message 1819
```

Kalau ingin mengukur waktu dengan prima yang lebih besar, biarkan program membangkitkan p dan q:

```powershell
python .\rsa_benchmark.py --prime-bits 256 512 1024 --e 65537 --message 12345 --trials 100 --warmup 5 --fermat-rounds 20
```

`--M` bisa dipakai sebagai pengganti `--message`. Pilih salah satu cara memasukkan prima: isi `--p` dan `--q` sekaligus, atau pakai `--prime-bits`. Tanpa opsi apa pun, program memakai prima 256/512/1024 bit, e=65537, M=1819, 30 percobaan, 3 pemanasan, dan 20 basis Fermat.

Hasilnya masuk ke `benchmark_results.csv` di folder skrip. Setiap benchmark yang berhasil mengganti hasil sebelumnya.

[Panduan presentasi](PANDUAN_PRESENTASI_RSA.md) menghubungkan flowchart dengan fungsi di kode. [Daftar kasus uji](KASUS_UJI_RSA.md) memuat input dan hasil yang dicek oleh skrip tes. Untuk berbagi tanpa Git, kirim [paket ZIP](rsa_benchmark_untuk_tim.zip).
