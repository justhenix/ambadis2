import argparse
import csv
import secrets
import statistics
import time
from pathlib import Path


def euclid(a, b):
    """Mengembalikan (gcd, s, t) dengan gcd = s*a + t*b."""
    x, y = a, b
    s0, s1 = 1, 0
    t0, t1 = 0, 1
    while y != 0:
        q = x // y
        x, y = y, x % y
        s0, s1 = s1, s0 - q * s1
        t0, t1 = t1, t0 - q * t1
    if x < 0:
        return -x, -s0, -t0
    return x, s0, t0


def invers_modulo(a, m):
    if m <= 1:
        raise ValueError("Modulus invers harus lebih besar dari 1.")
    gcd, s, _ = euclid(a, m)
    if gcd != 1:
        raise ValueError("Invers tidak ada: a dan modulus harus relatif prima.")
    return s % m


def pangkat_modular(basis, eksponen, modulus):
    if eksponen < 0 or modulus <= 0:
        raise ValueError("Eksponen harus >= 0 dan modulus harus > 0.")
    hasil = 1 % modulus
    power = basis % modulus
    while eksponen != 0:
        if eksponen % 2 == 1:
            hasil = (hasil * power) % modulus
        power = (power * power) % modulus
        eksponen //= 2
    return hasil


def prima_miller_rabin(n, jumlah_uji=20):
    """Mengembalikan True jika n lolos seluruh pengujian Miller-Rabin.

    Hasil False berarti n bukan prima. Hasil True berarti n kemungkinan
    prima; untuk basis acak, peluang komposit lolos paling banyak (1/4)^k.
    """
    if jumlah_uji < 1:
        raise ValueError("Jumlah uji Miller-Rabin minimal 1.")
    if n < 2:
        return False
    # Penyaringan ini menghindari banyak perpangkatan pada kandidat komposit.
    for p in (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37):
        if n % p == 0:
            return n == p
    # Tulis n - 1 = 2^s * d dengan d ganjil.
    d = n - 1
    s = 0
    while d % 2 == 0:
        d //= 2
        s += 1
    for _ in range(jumlah_uji):
        a = secrets.randbelow(n - 3) + 2
        x = pangkat_modular(a, d, n)
        if x == 1 or x == n - 1:
            continue
        # Kuadratkan paling banyak s - 1 kali; harus bertemu n - 1.
        for _ in range(s - 1):
            x = (x * x) % n
            if x == n - 1:
                break
        else:
            return False
    return True


def bangkitkan_prima(bit, jumlah_uji=20):
    if bit < 2:
        raise ValueError("Ukuran kandidat prima minimal 2 bit.")
    while True:
        # Bit teratas menjamin panjang bit; bit terbawah menjamin angka ganjil.
        kandidat = secrets.randbits(bit) | (1 << (bit - 1)) | 1
        if prima_miller_rabin(kandidat, jumlah_uji):
            return kandidat


def bangkitkan_kunci(p, q, e):
    """p dan q berasal dari contoh prima atau pembangkit prima_miller_rabin."""
    if p <= 2 or q <= 2 or p % 2 == 0 or q % 2 == 0 or p == q:
        raise ValueError("p dan q harus prima ganjil yang berbeda.")
    n = p * q
    phi = (p - 1) * (q - 1)
    if not 1 < e < phi:
        raise ValueError("e harus memenuhi 1 < e < phi.")
    d = invers_modulo(e, phi)
    return {
        "p": p, "q": q, "e": e, "n": n, "phi": phi, "d": d,
        "dP": d % (p - 1), "dQ": d % (q - 1),
        "qInv": invers_modulo(q, p),
    }


def kunci_acak(bit, jumlah_uji=20, e=65537):
    if bit < 16:
        raise ValueError("Ukuran prima otomatis minimal 16 bit.")
    if e <= 1 or e % 2 == 0:
        raise ValueError("e harus ganjil dan lebih besar dari 1.")
    while True:
        p = bangkitkan_prima(bit, jumlah_uji)
        q = bangkitkan_prima(bit, jumlah_uji)
        phi = (p - 1) * (q - 1)
        if e >= phi:
            raise ValueError("e terlalu besar untuk kunci ini; perbesar --prime-bits.")
        if p != q and euclid(e, phi)[0] == 1:
            return bangkitkan_kunci(p, q, e)


def enkripsi(pesan, e, n):
    if not 0 <= pesan < n:
        raise ValueError("Pesan harus memenuhi 0 <= M < n.")
    return pangkat_modular(pesan, e, n)


def dekripsi_rsa(ciphertext, d, n):
    return pangkat_modular(ciphertext, d, n)


def dekripsi_crt(ciphertext, p, q, dP, dQ, qInv):
    m1 = pangkat_modular(ciphertext, dP, p)
    m2 = pangkat_modular(ciphertext, dQ, q)
    h = (qInv * (m1 - m2)) % p
    return m2 + h * q


def uji_contoh():
    kunci = bangkitkan_kunci(43, 59, 13)
    harapan = {
        "p": 43, "q": 59, "e": 13, "n": 2537, "phi": 2436,
        "d": 937, "dP": 13, "dQ": 9, "qInv": 35,
    }
    c = enkripsi(1819, kunci["e"], kunci["n"])
    m_rsa = dekripsi_rsa(c, kunci["d"], kunci["n"])
    m_crt = dekripsi_crt(c, 43, 59, kunci["dP"], kunci["dQ"], kunci["qInv"])
    if kunci != harapan or c != 2081 or m_rsa != 1819 or m_crt != 1819:
        raise AssertionError("Uji contoh laporan GAGAL.")
    print("Uji contoh laporan: LULUS")
    print("n = 2537, phi = 2436, d = 937, C = 2081")
    print("dP = 13, dQ = 9, qInv = 35; RSA = RSA-CRT = 1819")


def benchmark(kunci, pesan, iterasi, pemanasan, jumlah_uji):
    if iterasi < 1 or pemanasan < 1:
        raise ValueError("Iterasi dan pemanasan minimal 1.")
    c = enkripsi(pesan, kunci["e"], kunci["n"])
    metode = [
        ("RSA", dekripsi_rsa, (c, kunci["d"], kunci["n"])),
        ("RSA-CRT", dekripsi_crt, (
            c, kunci["p"], kunci["q"], kunci["dP"], kunci["dQ"], kunci["qInv"]
        )),
    ]
    for _ in range(pemanasan):
        for nama, fungsi, argumen in metode:
            if fungsi(*argumen) != pesan:
                raise AssertionError(f"{nama} gagal saat pemanasan.")

    waktu = {"RSA": [], "RSA-CRT": []}
    for i in range(iterasi):
        # Urutan dibalik setiap percobaan untuk mengurangi bias urutan.
        urutan = metode if i % 2 == 0 else metode[::-1]
        for nama, fungsi, argumen in urutan:
            mulai = time.perf_counter_ns()
            hasil = fungsi(*argumen)
            durasi = time.perf_counter_ns() - mulai
            waktu[nama].append(durasi)
            if hasil != pesan:
                raise AssertionError(f"{nama} gagal pada percobaan {i + 1}.")

    rsa_median = statistics.median(waktu["RSA"])
    crt_median = statistics.median(waktu["RSA-CRT"])
    if crt_median == 0:
        raise RuntimeError("Waktu CRT tidak terukur; gunakan ukuran prima lebih besar.")
    return {
        "p": kunci["p"],
        "q": kunci["q"],
        "e": kunci["e"],
        "pesan": pesan,
        "ciphertext": c,
        "bit_p": kunci["p"].bit_length(),
        "bit_q": kunci["q"].bit_length(),
        "bit_kunci": kunci["n"].bit_length(),
        "iterasi": iterasi,
        "pemanasan": pemanasan,
        "uji_miller_rabin": jumlah_uji,
        "rsa_rerata_ms": statistics.mean(waktu["RSA"]) / 1_000_000,
        "rsa_median_ms": rsa_median / 1_000_000,
        "crt_rerata_ms": statistics.mean(waktu["RSA-CRT"]) / 1_000_000,
        "crt_median_ms": crt_median / 1_000_000,
        "speedup": rsa_median / crt_median,
        "rsa_samples_ns": waktu["RSA"],
        "crt_samples_ns": waktu["RSA-CRT"],
        "status": "LULUS",
    }


def tampilkan_tabel(hasil):
    print("\nWaktu dekripsi dalam milidetik (ms).")
    print("Rasio = median RSA / median RSA-CRT; nilai > 1 berarti CRT lebih cepat.")
    print(
        f"{'p/q(bit)':>11} {'n(bit)':>7} {'Ulang':>6} "
        f"{'RSA rerata':>11} {'RSA median':>11} "
        f"{'CRT rerata':>11} {'CRT median':>11} {'Rasio':>7} {'Status':>7}"
    )
    for baris in hasil:
        ukuran = f"{baris['bit_p']}/{baris['bit_q']}"
        print(
            f"{ukuran:>11} {baris['bit_kunci']:>7} {baris['iterasi']:>6} "
            f"{baris['rsa_rerata_ms']:>11.4f} {baris['rsa_median_ms']:>11.4f} "
            f"{baris['crt_rerata_ms']:>11.4f} {baris['crt_median_ms']:>11.4f} "
            f"{baris['speedup']:>6.2f}x {baris['status']:>7}"
        )


def simpan_csv(hasil):
    lokasi = Path(__file__).resolve().with_name("benchmark_results.csv")
    with lokasi.open("w", newline="", encoding="utf-8") as file:
        penulis = csv.DictWriter(file, fieldnames=list(hasil[0]))
        penulis.writeheader()
        penulis.writerows(hasil)
    return lokasi


def main():
    parser = argparse.ArgumentParser(
        description="Bandingkan dekripsi RSA dan RSA-CRT dengan uji prima Miller-Rabin."
    )
    parser.add_argument(
        "--prime-bits", type=int, nargs="+",
        help="Ukuran bit masing-masing p dan q, minimal 16 (bawaan: 256 512 1024).",
    )
    parser.add_argument("--p", type=int, help="Nilai p manual; wajib bersama --q.")
    parser.add_argument("--q", type=int, help="Nilai q manual; wajib bersama --p.")
    parser.add_argument("--e", type=int, default=65537, help="Eksponen publik (bawaan: 65537).")
    parser.add_argument(
        "--message", "--M", dest="pesan", type=int, default=1819,
        help="Pesan bilangan bulat, 0 <= M < p*q (bawaan: 1819).",
    )
    parser.add_argument(
        "--trials", type=int, default=30,
        help="Jumlah percobaan per metode per ukuran (bawaan: 30).",
    )
    parser.add_argument(
        "--warmup", type=int, default=3,
        help="Jumlah pemanasan per metode per ukuran (bawaan: 3).",
    )
    parser.add_argument(
        "--mr-rounds", type=int, default=20,
        help="Jumlah basis acak uji Miller-Rabin per kandidat (bawaan: 20).",
    )
    args = parser.parse_args()
    if (args.p is None) != (args.q is None):
        parser.error("--p dan --q harus diberikan bersama.")
    manual = args.p is not None
    if manual and args.prime_bits is not None:
        parser.error("Pilih --p/--q manual atau --prime-bits otomatis.")
    ukuran_prima = args.prime_bits if args.prime_bits is not None else [256, 512, 1024]
    if not manual and any(bit < 16 for bit in ukuran_prima):
        parser.error("Ukuran prima otomatis minimal 16 bit.")
    if min(args.trials, args.warmup, args.mr_rounds) < 1:
        parser.error("Percobaan, pemanasan, dan uji Miller-Rabin minimal 1.")
    if args.e <= 1 or args.e % 2 == 0:
        parser.error("e harus ganjil dan lebih besar dari 1.")
    if args.pesan < 0:
        parser.error("Pesan harus memenuhi 0 <= M < n.")

    uji_contoh()
    print(f"\nPemanasan: {args.warmup}; percobaan: {args.trials} per metode.")
    print(f"Uji Miller-Rabin: {args.mr_rounds} basis acak.")
    print(f"Input benchmark: e = {args.e}, M = {args.pesan}")
    hasil = []
    try:
        if manual:
            if not prima_miller_rabin(args.p, args.mr_rounds):
                raise ValueError("p tidak lolos uji Miller-Rabin.")
            if not prima_miller_rabin(args.q, args.mr_rounds):
                raise ValueError("q tidak lolos uji Miller-Rabin.")
            kunci = bangkitkan_kunci(args.p, args.q, args.e)
            print(f"Mode manual: p = {args.p}, q = {args.q}")
            print(f"n = {kunci['n']}, phi = {kunci['phi']}, d = {kunci['d']}")
            print(f"dP = {kunci['dP']}, dQ = {kunci['dQ']}, qInv = {kunci['qInv']}")
            hasil.append(benchmark(
                kunci, args.pesan, args.trials, args.warmup, args.mr_rounds
            ))
            print(f"C = {hasil[0]['ciphertext']}")
        else:
            for bit in ukuran_prima:
                print(f"Mengukur p dan q masing-masing {bit} bit...", flush=True)
                kunci = kunci_acak(bit, args.mr_rounds, args.e)
                hasil.append(benchmark(
                    kunci, args.pesan, args.trials, args.warmup, args.mr_rounds
                ))
    except ValueError as error:
        parser.error(str(error))
    tampilkan_tabel(hasil)
    print(f"\nHasil CSV: {simpan_csv(hasil)}")


if __name__ == "__main__":
    main()