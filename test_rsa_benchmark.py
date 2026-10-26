import csv
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path


def input_manual(p, q, e, pesan):
    return ["--p", str(p), "--q", str(q), "--e", str(e), "--message", str(pesan)]


VALID = [
    ("V1", 43, 59, 13, 1819, 2081),
    ("V2", 61, 53, 17, 65, 2790),
    ("V3", 43, 59, 13, 0, 0),
    ("V4", 43, 59, 13, 2536, 2536),
    ("V5", 17, 61, 7, 42, 423),
    ("V6", 43, 59, 13, 43, 1935),
]

TIDAK_VALID = [
    ("I1", input_manual(45, 59, 13, 1819), "p tidak lolos uji Fermat."),
    ("I2", input_manual(43, 55, 13, 1819), "q tidak lolos uji Fermat."),
    ("I3", input_manual(43, 43, 13, 42), "p dan q harus prima ganjil yang berbeda."),
    ("I4", input_manual(43, 59, 3, 1819),
     "Invers tidak ada: a dan modulus harus relatif prima."),
    ("I5", input_manual(43, 59, 2, 1819), "e harus ganjil dan lebih besar dari 1."),
    ("I6", input_manual(43, 59, 2437, 1819), "e harus memenuhi 1 < e < phi."),
    ("I7", input_manual(43, 59, 13, -1), "Pesan harus memenuhi 0 <= M < n."),
    ("I8", input_manual(43, 59, 13, 2537), "Pesan harus memenuhi 0 <= M < n."),
    ("I9", ["--p", "43", "--e", "13", "--message", "1819"],
     "--p dan --q harus diberikan bersama."),
    ("I10", input_manual(43, 59, 13, 1819) + ["--prime-bits", "256"],
     "Pilih --p/--q manual atau --prime-bits otomatis."),
]


def pastikan(kondisi, pesan):
    if not kondisi:
        raise AssertionError(pesan)


def jalankan(skrip, argumen):
    return subprocess.run(
        [sys.executable, str(skrip), *argumen,
         "--trials", "10", "--warmup", "1", "--fermat-rounds", "5"],
        cwd=skrip.parent, capture_output=True, text=True, timeout=15,
    )


def periksa_valid(skrip, kasus):
    nomor, p, q, e, pesan, ciphertext = kasus
    argumen = input_manual(p, q, e, pesan)
    if nomor == "V2":
        argumen[6] = "--M"
    lokasi_csv = skrip.with_name("benchmark_results.csv")
    if lokasi_csv.exists():
        lokasi_csv.unlink()
    proses = jalankan(skrip, argumen)
    pastikan(proses.returncode == 0,
             f"Kode keluar {proses.returncode}: {proses.stderr.strip()}")
    pastikan("Uji contoh laporan: LULUS" in proses.stdout, "Uji contoh tidak lulus.")
    pastikan(f"Input benchmark: e = {e}, M = {pesan}" in proses.stdout,
             "Input benchmark pada terminal tidak cocok.")
    pastikan(f"n = {p*q}, phi = {(p-1)*(q-1)}," in proses.stdout,
             "n atau phi tidak cocok.")
    pastikan(f"\nC = {ciphertext}\n" in proses.stdout, "Ciphertext terminal tidak cocok.")
    with lokasi_csv.open(newline="", encoding="utf-8") as file:
        baris = list(csv.DictReader(file))
    pastikan(len(baris) == 1, "CSV harus berisi satu hasil.")
    harapan = {
        "p": p, "q": q, "e": e, "pesan": pesan, "ciphertext": ciphertext,
        "bit_p": p.bit_length(), "bit_q": q.bit_length(),
        "bit_kunci": (p*q).bit_length(), "iterasi": 10, "pemanasan": 1,
        "uji_fermat": 5, "status": "LULUS",
    }
    for kolom, nilai in harapan.items():
        pastikan(baris[0][kolom] == str(nilai), f"CSV: kolom {kolom} tidak cocok.")


def periksa_tidak_valid(skrip, kasus):
    _, argumen, kesalahan = kasus
    lokasi_csv = skrip.with_name("benchmark_results.csv")
    sebelum = lokasi_csv.read_bytes() if lokasi_csv.exists() else None
    proses = jalankan(skrip, argumen)
    pastikan(proses.returncode == 2, f"Harus ditolak; kode keluar {proses.returncode}.")
    harapan = "rsa_benchmark.py: error: " + kesalahan
    pastikan(proses.stderr.strip().endswith(harapan),
             f"Pesan kesalahan tidak cocok: {proses.stderr.strip()}")
    sesudah = lokasi_csv.read_bytes() if lokasi_csv.exists() else None
    pastikan(sebelum == sesudah, "Input tidak valid mengubah CSV.")


def main():
    sumber = Path(__file__).resolve().with_name("rsa_benchmark.py")
    if not sumber.is_file():
        print("FAIL: rsa_benchmark.py harus berada di folder yang sama.")
        return 1
    lulus = 0
    gagal = 0
    # Salinan sementara membuat pengujian tidak menimpa hasil benchmark pengguna.
    with tempfile.TemporaryDirectory(prefix="uji_rsa_") as folder:
        skrip = Path(folder) / sumber.name
        shutil.copy2(sumber, skrip)
        for kasus in VALID:
            try:
                periksa_valid(skrip, kasus)
                print(f"PASS {kasus[0]}: C = {kasus[5]}, M = {kasus[4]}")
                lulus += 1
            except Exception as error:
                print(f"FAIL {kasus[0]}: {error}")
                gagal += 1
        for kasus in TIDAK_VALID:
            try:
                periksa_tidak_valid(skrip, kasus)
                print(f"PASS {kasus[0]}: input ditolak dengan pesan yang sesuai.")
                lulus += 1
            except Exception as error:
                print(f"FAIL {kasus[0]}: {error}")
                gagal += 1
    print(f"\nHasil: {lulus}/16 PASS, {gagal} FAIL.")
    return 1 if gagal else 0


if __name__ == "__main__":
    sys.exit(main())
