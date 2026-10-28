import csv
import json
import os
import sys
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
        else:
            self.send_json_response({"status": "error", "message": "Endpoint tidak ditemukan."}, status=404)

    def handle_simulasi(self, data):
        try:
            p = read_rsa_integer(data, "p", 43)
            q = read_rsa_integer(data, "q", 59)
            e = read_rsa_integer(data, "e", 13)
            m = read_rsa_integer(data, "message", 1819)
            mr_rounds = int(data.get("mr_rounds", 20))

            # 1. Validasi Miller-Rabin
            if not rsa.prima_miller_rabin(p, mr_rounds):
                raise ValueError(f"p ({p}) tidak lolos uji prima Miller-Rabin.")
            if not rsa.prima_miller_rabin(q, mr_rounds):
                raise ValueError(f"q ({q}) tidak lolos uji prima Miller-Rabin.")

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
                raise ValueError("Verifikasi dekripsi gagal; periksa kandidat p dan q yang lolos Miller-Rabin.")

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

    def handle_benchmark(self, data):
        try:
            prime_bits = data.get("prime_bits", [256, 512, 1024])
            trials = int(data.get("trials", 30))
            warmup = int(data.get("warmup", 3))
            mr_rounds = int(data.get("mr_rounds", 20))
            message = read_rsa_integer(data, "message", 1819)

            if not prime_bits:
                raise ValueError("Pilih minimal satu ukuran bit prima.")

            hasil_list = []
            for bit in prime_bits:
                kunci = rsa.kunci_acak(int(bit), mr_rounds, 65537)
                res = rsa.benchmark(kunci, message, trials, warmup, mr_rounds)
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
    if not 0 <= port <= 65535:
        raise ValueError("Port harus berada pada rentang 0 sampai 65535.")
    for candidate_port in range(port, min(port + 20, 65536)):
        try:
            server = ThreadingHTTPServer(("0.0.0.0", candidate_port), RSAApiHandler)
            break
        except OSError:
            continue
    else:
        raise OSError(f"Tidak ada port kosong pada rentang {port} sampai {min(port + 19, 65535)}.")

    url = f"http://localhost:{server.server_port}"
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
    finally:
        server.server_close()


if __name__ == "__main__":
    port_arg = 8000
    if len(sys.argv) > 1 and sys.argv[1].isdigit():
        port_arg = int(sys.argv[1])
    no_browser = "--no-browser" in sys.argv
    start_server(port=port_arg, open_browser=not no_browser)
