# Kasus yang diperiksa skrip tes

Jalankan `python .\test_rsa_benchmark.py` untuk mengecek seluruh kasus di bawah. V1 memakai contoh laporan, sedangkan kasus lainnya dibuat untuk menguji program. Agar cepat, tiap kasus memakai 10 percobaan, 1 pemanasan, dan 5 basis Miller-Rabin.

Kalau ingin mencoba satu kasus sendiri, jalankan `python .\rsa_benchmark.py --p P --q Q --e E --message M` lalu ganti P, Q, E, dan M dengan angka pada tabel. V2 memakai --M untuk mengecek aliasnya. Kasus V1 sampai V6 harus menghasilkan C yang sesuai, mengembalikan M pada kedua metode, dan selesai dengan status LULUS serta kode keluar 0.

| ID | p | q | e | M | C |
|---|---:|---:|---:|---:|---:|
| V1 | 43 | 59 | 13 | 1819 | 2081 |
| V2 | 61 | 53 | 17 | 65 | 2790 |
| V3 | 43 | 59 | 13 | 0 | 0 |
| V4 | 43 | 59 | 13 | 2536 | 2536 |
| V5 | 17 | 61 | 7 | 42 | 423 |
| V6 | 43 | 59 | 13 | 43 | 1935 |

Kasus I1 sampai I10 sengaja berisi input yang salah. Program harus menolaknya dengan kode keluar 2 dan pesan di bawah, setelah awalan `rsa_benchmark.py: error:`. Untuk I9, jangan masukkan --q; untuk I10, tambahkan --prime-bits 256.

| ID | p, q, e, M | Pesan kesalahan |
|---|---|---|
| I1 | 45, 59, 13, 1819 | p tidak lolos uji Miller-Rabin. |
| I2 | 43, 55, 13, 1819 | q tidak lolos uji Miller-Rabin. |
| I3 | 43, 43, 13, 42 | p dan q harus prima ganjil yang berbeda. |
| I4 | 43, 59, 3, 1819 | Invers tidak ada: a dan modulus harus relatif prima. |
| I5 | 43, 59, 2, 1819 | e harus ganjil dan lebih besar dari 1. |
| I6 | 43, 59, 2437, 1819 | e harus memenuhi 1 < e < phi. |
| I7 | 43, 59, 13, -1 | Pesan harus memenuhi 0 <= M < n. |
| I8 | 43, 59, 13, 2537 | Pesan harus memenuhi 0 <= M < n. |
| I9 | 43, tanpa q, 13, 1819 | --p dan --q harus diberikan bersama. |
| I10 | 43, 59, 13, 1819 | Pilih --p/--q manual atau --prime-bits otomatis. |

Skrip tes mencocokkan kode keluar, input, n/phi, ciphertext di terminal dan CSV, status, serta pesan kesalahannya. Saat validasi gagal, isi CSV sebelumnya harus tetap sama. Teks `Uji contoh laporan: LULUS` yang muncul di awal cuma dipakai untuk sampel bawaan; hasil inputmu dilihat dari pesan terakhir dan kode keluar program. Angka waktunya boleh berbeda antar eksekusi, jadi tes tidak mencocokkannya dengan angka tetap.