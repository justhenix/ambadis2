# Dari flowchart ke kode

Program mulai dari `main()`. Di sini kamu memilih p dan q sendiri atau meminta program membangkitkannya, lalu memasukkan e, M, dan jumlah pengulangan. Setelah input cocok, program menghitung kunci dan mengenkripsi pesan sebelum mulai mengukur dekripsi.

| Bagian flowchart/pseudocode | Tempatnya di kode |
|---|---|
| Mulai dan baca p, q, e, M, R | `main()` membaca --p, --q, --e, --message/--M, dan --trials. |
| Bangkitkan prima otomatis | `bangkitkan_prima()` membuat kandidat; `kunci_acak()` memilih pasangan sesuai --prime-bits. |
| Periksa prima dan GCD | `prima_miller_rabin()` menguji kandidat; `euclid()` mencari GCD dan koefisien Bezout. |
| Cari invers modular | `invers_modulo()` memakai koefisien Bezout jika GCD-nya 1. |
| Hitung perpangkatan biner | `pangkat_modular()` membaca bit eksponen sambil menguadratkan basis dan mengambil modulo. |
| Bentuk kunci | `bangkitkan_kunci()` menghitung n, phi, d, dP, dQ, dan qInv. |
| Enkripsi | `enkripsi()` menghitung C = M^e mod n. |
| Dekripsi RSA standar | `dekripsi_rsa()` langsung menghitung C^d mod n. |
| Dekripsi RSA-CRT | `dekripsi_crt()` menghitung m1=C^dP mod p dan m2=C^dQ mod q, lalu h=qInv*(m1-m2) mod p dan M=m2+h*q. |
| Mulai timer, ulang R kali, cek pesan | `benchmark()` mengukur setiap dekripsi dengan perf_counter_ns dan mencocokkan hasilnya dengan M. |
| Tampilkan dan simpan hasil | `tampilkan_tabel()` mencetak statistik; `simpan_csv()` menulis hasil beserta inputnya. |
| Cocokkan contoh laporan | `uji_contoh()` memeriksa p=43, q=59, e=13, M=1819, C=2081, dan hasil kedua dekripsi. |

Kedua metode memakai kunci, ciphertext, dan pesan yang sama. Yang masuk timer hanya pemanggilan dekripsinya; pembangkitan kunci, enkripsi, dan pemanasan sudah selesai lebih dulu. Pada CRT, waktu penggabungan hasil ikut dihitung. Semua perpangkatan dihitung lewat `pangkat_modular()`, tanpa pow().

Pada percobaan pertama, RSA standar dijalankan lebih dulu; percobaan berikutnya dimulai dengan CRT. Urutan ini terus bergantian. Program melaporkan rerata serta median, lalu membagi median RSA dengan median CRT untuk mendapatkan rasio percepatan. Jadi, rasio 3 berarti median waktu RSA standar tiga kali median waktu CRT.

Ada beberapa penyesuaian dari pseudocode: opsi terminal menggantikan read/lagi, jumlah basis Miller-Rabin bawaan 20 (sama dengan pseudocode), dan program menambahkan pemanasan, median, serta CSV. Koreksi sisa negatif tidak diperlukan karena modulo dengan pembagi positif di Python sudah menghasilkan sisa tidak negatif. Pada mode manual, program mencetak C setelah pengukuran.