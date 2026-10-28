import base64
import csv
import json
import os
import sys
import time
import webbrowser
from http.server import SimpleHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import parse_qs, urlparse

# Pastikan encoding UTF-8 di Windows Console
if hasattr(sys.stdout, "reconfigure"):
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# Pastikan folder root ada di path
BASE_DIR = Path(__file__).resolve().parent
sys.path.insert(0, str(BASE_DIR))

import rsa_benchmark as rsa
import test_rsa_benchmark as test_runner


def read_rsa_integer(data, name, default):
    value = data.get(name, default)
    if isinstance(value, bool) or not isinstance(value, (str, int)):
        raise ValueError(f"{name} harus berupa bilangan bulat desimal.")
    if isinstance(value, int) and abs(value) > 2**53 - 1:
        raise ValueError(f"Kirim {name} sebagai string desimal agar presisi terjaga.")
    return int(value)


class RSAApiHandler(SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(BASE_DIR), **kwargs)

    def do_GET(self):
        parsed = urlparse(self.path)
        if parsed.path == "/" or parsed.path == "/index.html":
            self.send_file_response(BASE_DIR / "index.html", "text/html; charset=utf-8")
        elif parsed.path == "/api/download-csv":
            csv_path = BASE_DIR / "benchmark_results.csv"
            if csv_path.exists():
                self.send_file_response(
                    csv_path,
                    "text/csv; charset=utf-8",
                    as_attachment=True,
                    filename="benchmark_results.csv"
                )
            else:
                self.send_json_response({"status": "error", "message": "Belum ada file CSV benchmark."}, status=404)
        else:
            super().do_GET()

    def do_POST(self):
        parsed = urlparse(self.path)
        length = int(self.headers.get("Content-Length", 0))
        body = self.rfile.read(length) if length > 0 else b"{}"

        try:
            data = json.loads(body.decode("utf-8")) if body else {}
        except Exception as e:
            self.send_json_response({"status": "error", "message": f"Format JSON tidak valid: {e}"}, status=400)
            return

        if parsed.path == "/api/simulasi":
            self.handle_simulasi(data)
        elif parsed.path == "/api/benchmark":
            self.handle_benchmark(data)
        elif parsed.path == "/api/test-suite":
            self.handle_test_suite()
        elif parsed.path == "/api/text-encrypt":
            self.handle_text_encrypt(data)
        elif parsed.path == "/api/generate-key":
            self.handle_generate_key(data)
        else:
            self.send_json_response({"status": "error", "message": "Endpoint tidak ditemukan."}, status=404)

    def handle_simulasi(self, data):
        try:
            p = read_rsa_integer(data, "p", 43)
            q = read_rsa_integer(data, "q", 59)
            e = read_rsa_integer(data, "e", 13)
            m = read_rsa_integer(data, "message", 1819)
            fermat_rounds = int(data.get("fermat_rounds", 20))

            # 1. Validasi Fermat
            if not rsa.prima_fermat(p, fermat_rounds):
                raise ValueError(f"p ({p}) tidak lolos uji prima Fermat.")
            if not rsa.prima_fermat(q, fermat_rounds):
                raise ValueError(f"q ({q}) tidak lolos uji prima Fermat.")

            # 2. Bangkitkan Kunci
            kunci = rsa.bangkitkan_kunci(p, q, e)

            # 3. Validasi Pesan
            if not (0 <= m < kunci["n"]):
                raise ValueError(f"Pesan M ({m}) harus memenuhi 0 <= M < n ({kunci['n']}).")

            # 4. Enkripsi & Dekripsi
            c = rsa.enkripsi(m, kunci["e"], kunci["n"])
            m_rsa = rsa.dekripsi_rsa(c, kunci["d"], kunci["n"])

            # Dekripsi CRT step-by-step
            m1 = rsa.pangkat_modular(c, kunci["dP"], p)
            m2 = rsa.pangkat_modular(c, kunci["dQ"], q)
            h = (kunci["qInv"] * (m1 - m2)) % p
            m_crt = m2 + h * q
            if not m == m_rsa == m_crt:
                raise ValueError("Verifikasi dekripsi gagal; periksa kandidat p dan q yang lolos Fermat.")

            response = {
                "status": "ok",
                "p": p,
                "q": q,
                "e": e,
                "m": m,
                "n": kunci["n"],
                "phi": kunci["phi"],
                "d": kunci["d"],
                "dP": kunci["dP"],
                "dQ": kunci["dQ"],
                "qInv": kunci["qInv"],
                "c": c,
                "m_rsa": m_rsa,
                "m_crt": m_crt,
                "m1": m1,
                "m2": m2,
                "h": h,
                "valid": (m == m_rsa == m_crt)
            }
            self.send_json_response({key: str(value) if type(value) is int else value for key, value in response.items()})

        except Exception as err:
            self.send_json_response({"status": "error", "message": str(err)}, status=400)

    def handle_text_encrypt(self, data):
        try:
            text = data.get("text", "")
            if not isinstance(text, str):
                raise ValueError("Teks pesan harus berupa string.")
            if not text:
                raise ValueError("Teks pesan tidak boleh kosong.")

            key_mode = data.get("key_mode", "custom")
            fermat_rounds = int(data.get("fermat_rounds", 20))

            if key_mode == "generate":
                bits = int(data.get("bits", 128))
                prime_bits = max(16, bits // 2)
                kunci = rsa.kunci_acak(prime_bits, fermat_rounds, 65537)
            else:
                p = read_rsa_integer(data, "p", 43)
                q = read_rsa_integer(data, "q", 59)
                e = read_rsa_integer(data, "e", 13)
                if not rsa.prima_fermat(p, fermat_rounds):
                    raise ValueError(f"p ({p}) tidak lolos uji prima Fermat.")
                if not rsa.prima_fermat(q, fermat_rounds):
                    raise ValueError(f"q ({q}) tidak lolos uji prima Fermat.")
                kunci = rsa.bangkitkan_kunci(p, q, e)

            n = kunci["n"]
            if n <= 255:
                raise ValueError(f"Modulus n ({n}) terlalu kecil untuk teks byte ASCII/UTF-8 (perlu n > 255).")

            # Ukuran blok maksimal dalam byte agar nilai integer blok terjamin < n
            block_size = max(1, (n.bit_length() - 1) // 8)

            raw_bytes = text.encode("utf-8")
            chunks = [raw_bytes[i:i + block_size] for i in range(0, len(raw_bytes), block_size)]

            ciphers = []
            chunk_lengths = []
            blocks_info = []

            for idx, ch in enumerate(chunks):
                m_int = int.from_bytes(ch, "big")
                if m_int >= n:
                    raise ValueError("Nilai blok pesan harus lebih kecil dari modulus n.")
                c_int = rsa.enkripsi(m_int, kunci["e"], n)
                ciphers.append(c_int)
                chunk_lengths.append(len(ch))

                if idx < 30:  # Batasi preview per blok hingga 30 pertama agar UI tetap ringan
                    blocks_info.append({
                        "index": idx + 1,
                        "text": ch.decode("utf-8", errors="replace"),
                        "hex_bytes": ch.hex().upper(),
                        "int_m": str(m_int),
                        "int_c": str(c_int),
                        "hex_c": hex(c_int)[2:].upper(),
                    })

            # Ukur Dekripsi Standar
            t0 = time.perf_counter_ns()
            dec_rsa_bytes = bytearray()
            for c_int, ch_len in zip(ciphers, chunk_lengths):
                m_dec = rsa.dekripsi_rsa(c_int, kunci["d"], n)
                dec_rsa_bytes.extend(m_dec.to_bytes(ch_len, "big"))
            t_rsa = (time.perf_counter_ns() - t0) / 1_000_000  # ms

            # Ukur Dekripsi CRT
            t0 = time.perf_counter_ns()
            dec_crt_bytes = bytearray()
            for c_int, ch_len in zip(ciphers, chunk_lengths):
                m_dec = rsa.dekripsi_crt(c_int, kunci["p"], kunci["q"], kunci["dP"], kunci["dQ"], kunci["qInv"])
                dec_crt_bytes.extend(m_dec.to_bytes(ch_len, "big"))
            t_crt = (time.perf_counter_ns() - t0) / 1_000_000  # ms

            is_valid = bytes(dec_rsa_bytes) == bytes(dec_crt_bytes) == raw_bytes
            if not is_valid:
                raise ValueError("Verifikasi dekripsi RSA dan RSA-CRT gagal.")
            text_decrypted_rsa = dec_rsa_bytes.decode("utf-8")
            text_decrypted = dec_crt_bytes.decode("utf-8")

            speedup = (t_rsa / t_crt) if t_crt > 0 else 1.0

            # Ciphertext representasi
            hex_ciphers = [hex(c)[2:].upper() for c in ciphers]
            hex_joined = " ".join(hex_ciphers)
            
            # Base64 representasi
            packed = ",".join(str(c) for c in ciphers).encode("utf-8")
            b64_cipher = base64.b64encode(packed).decode("ascii")

            self.send_json_response({
                "status": "ok",
                "key_info": {
                    "p": str(kunci["p"]),
                    "q": str(kunci["q"]),
                    "n": str(kunci["n"]),
                    "phi": str(kunci["phi"]),
                    "e": str(kunci["e"]),
                    "d": str(kunci["d"]),
                    "dP": str(kunci["dP"]),
                    "dQ": str(kunci["dQ"]),
                    "qInv": str(kunci["qInv"]),
                    "bit_length": kunci["n"].bit_length(),
                },
                "text_original": text,
                "text_decrypted": text_decrypted,
                "text_decrypted_rsa": text_decrypted_rsa,
                "text_decrypted_crt": text_decrypted,
                "is_valid": is_valid,
                "total_bytes": len(raw_bytes),
                "block_size_bytes": block_size,
                "total_blocks": len(chunks),
                "blocks": blocks_info,
                "has_more_blocks": len(chunks) > 30,
                "ciphertext_hex": hex_joined,
                "ciphertext_base64": b64_cipher,
                "ciphers_count": len(ciphers),
                "rsa_time_ms": round(t_rsa, 4),
                "crt_time_ms": round(t_crt, 4),
                "speedup": round(speedup, 2),
            })

        except Exception as err:
            self.send_json_response({"status": "error", "message": str(err)}, status=400)

    def handle_generate_key(self, data):
        try:
            bits = int(data.get("bits", 128))
            prime_bits = max(16, bits // 2)
            fermat_rounds = int(data.get("fermat_rounds", 20))
            kunci = rsa.kunci_acak(prime_bits, fermat_rounds, 65537)
            self.send_json_response({
                "status": "ok",
                "p": str(kunci["p"]),
                "q": str(kunci["q"]),
                "n": str(kunci["n"]),
                "phi": str(kunci["phi"]),
                "e": str(kunci["e"]),
                "d": str(kunci["d"]),
                "dP": str(kunci["dP"]),
                "dQ": str(kunci["dQ"]),
                "qInv": str(kunci["qInv"]),
                "bit_length": kunci["n"].bit_length(),
            })
        except Exception as err:
            self.send_json_response({"status": "error", "message": str(err)}, status=400)

    def handle_benchmark(self, data):
        try:
            prime_bits = data.get("prime_bits", [256, 512, 1024])
            trials = int(data.get("trials", 30))
            warmup = int(data.get("warmup", 3))
            fermat_rounds = int(data.get("fermat_rounds", 20))
            message = read_rsa_integer(data, "message", 1819)

            if not prime_bits:
                raise ValueError("Pilih minimal satu ukuran bit prima.")

            hasil_list = []
            for bit in prime_bits:
                kunci = rsa.kunci_acak(int(bit), fermat_rounds, 65537)
                res = rsa.benchmark(kunci, message, trials, warmup, fermat_rounds)
                hasil_list.append(res)

            # Simpan ke CSV
            csv_path = rsa.simpan_csv(hasil_list)
            for result in hasil_list:
                for name in ("p", "q", "e", "pesan", "ciphertext"):
                    result[name] = str(result[name])

            self.send_json_response({
                "status": "ok",
                "results": hasil_list,
                "csv_saved": str(csv_path.name)
            })

        except Exception as err:
            self.send_json_response({"status": "error", "message": str(err)}, status=400)

    def handle_test_suite(self):
        try:
            cases = test_runner.jalankan_suite()
            passed = sum(case["status"] == "PASS" for case in cases)
            self.send_json_response({
                "status": "ok",
                "summary": {"total": len(cases), "pass": passed, "fail": len(cases) - passed},
                "cases": cases,
            })
        except Exception as err:
            self.send_json_response({"status": "error", "message": str(err)}, status=500)

    def send_json_response(self, data, status=200):
        body = json.dumps(data, indent=2).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(body)))
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Cache-Control", "no-cache")
        self.end_headers()
        self.wfile.write(body)

    def send_file_response(self, file_path, content_type, as_attachment=False, filename=None):
        try:
            with open(file_path, "rb") as f:
                content = f.read()
            self.send_response(200)
            self.send_header("Content-Type", content_type)
            self.send_header("Content-Length", str(len(content)))
            if as_attachment and filename:
                self.send_header("Content-Disposition", f'attachment; filename="{filename}"')
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(content)
        except Exception as e:
            self.send_json_response({"status": "error", "message": str(e)}, status=500)


def start_server(port=8000, open_browser=True):
    # Port fallback jika 8000 dipakai
    while port < 8020:
        try:
            server = ThreadingHTTPServer(("0.0.0.0", port), RSAApiHandler)
            break
        except OSError:
            port += 1

    url = f"http://localhost:{port}"
    print("============================================================")
    print("  [+] RSA vs RSA-CRT Web Application Server")
    print(f"  [+] URL Aplikasi : {url}")
    print("============================================================")
    print("Tekan Ctrl+C untuk menghentikan server.\n")

    if open_browser:
        try:
            webbrowser.open(url)
        except Exception:
            pass

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer dihentikan.")
        server.server_close()


if __name__ == "__main__":
    port_arg = 8000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port_arg = int(sys.argv[1])
    no_browser = "--no-browser" in sys.argv
    start_server(port=port_arg, open_browser=not no_browser)
