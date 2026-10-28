import csv
import json
import statistics
import tempfile
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from pathlib import Path
from unittest.mock import patch

import rsa_benchmark as rsa
import server
import test_rsa_benchmark as runner


class WebApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        class QuietHandler(server.RSAApiHandler):
            def log_message(self, *_):
                pass
        cls.http = ThreadingHTTPServer(('127.0.0.1', 0), QuietHandler)
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.http.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.thread.join(timeout=5)
        cls.http.server_close()

    def post(self, endpoint, data):
        request = urllib.request.Request(self.url + endpoint, json.dumps(data).encode(),
            {'Content-Type': 'application/json'})
        try:
            response = urllib.request.urlopen(request, timeout=45)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            return response.status, json.load(response)

    def test_large_integer_round_trip(self):
        code, data = self.post('/api/simulasi', dict(p='1000000007', q='1000000009',
            e='65537', message='9007199254740993'))
        self.assertEqual(code, 200)
        self.assertEqual(data['n'], '1000000016000000063')
        self.assertEqual(data['m_rsa'], '9007199254740993')
        self.assertEqual(data['m_crt'], data['m'])

    def test_reject_fractional_boolean_and_unsafe_numeric_input(self):
        for value in (43.5, True, 9007199254740993, '43.5', ''):
            with self.subTest(value=value):
                code, data = self.post('/api/simulasi', dict(p=value, q=59, e=13, message=1))
                self.assertEqual(code, 400)
                self.assertEqual(data['status'], 'error')

    def test_invalid_simulation_inputs(self):
        for fields in (dict(p=45), dict(q=55), dict(q=43), dict(e=3), dict(e=2),
                       dict(e=2437), dict(message=-1), dict(message=2537)):
            with self.subTest(fields=fields):
                code, _ = self.post('/api/simulasi', dict(dict(p=43,q=59,e=13,message=1819), **fields))
                self.assertEqual(code, 400)

    def test_real_cli_suite_and_existing_csv_preserved(self):
        target = Path(rsa.__file__).with_name('benchmark_results.csv')
        before = target.read_bytes() if target.exists() else None
        code, data = self.post('/api/test-suite', {})
        self.assertEqual(code, 200)
        self.assertEqual(data['summary'], dict(total=16, **{'pass':16, 'fail':0}))
        self.assertEqual(target.read_bytes() if target.exists() else None, before)

    def test_negative_case_cannot_pass_without_observed_error(self):
        canary = [('CANARY', runner.input_manual(43,59,13,1819), 'error that never occurred')]
        with patch.object(runner, 'TIDAK_VALID', canary):
            code, data = self.post('/api/test-suite', {})
        self.assertEqual(code, 200)
        self.assertEqual(data['cases'][-1]['status'], 'FAIL')
        self.assertEqual(data['summary']['fail'], 1)

    def test_composite_passing_single_base_and_failed_decryption_rejected(self):
        # Basis tetap a=2 sengaja dipakai agar komposit lolos satu basis;
        # verifikasi dekripsi tetap harus menolak p yang bukan prima.
        with patch.object(rsa.secrets, 'randbelow', return_value=0):
            self.assertTrue(rsa.prima_miller_rabin(252601, 20))
            code, data = self.post('/api/simulasi', dict(p=1373653,q=59,e=13,message=5))
        self.assertEqual(code, 400)
        self.assertIn('Verifikasi dekripsi gagal', data['message'])

    def test_miller_rabin_rejects_carmichael_numbers_fermat_accepts(self):
        # Faktor prima semuanya > 37, jadi tidak tertangkap penyaringan awal.
        for n in (252601, 56052361, 118901521, 172947529):
            with self.subTest(n=n):
                self.assertEqual(pow(2, n - 1, n), 1)  # uji Fermat basis 2 lolos
                self.assertFalse(rsa.prima_miller_rabin(n, 20))
                code, data = self.post('/api/simulasi', dict(p=n, q=59, e=13, message=5))
                self.assertEqual(code, 400)
                self.assertIn('tidak lolos uji prima Miller-Rabin', data['message'])

    def test_miller_rabin_matches_trial_division_on_small_range(self):
        def prima_biasa(n):
            return n >= 2 and all(n % i for i in range(2, int(n ** 0.5) + 1))
        for n in range(0, 3000):
            self.assertEqual(rsa.prima_miller_rabin(n, 20), prima_biasa(n), n)

    def test_miller_rabin_large_primes_and_products(self):
        m89, m127 = 2 ** 89 - 1, 2 ** 127 - 1
        self.assertTrue(rsa.prima_miller_rabin(m89, 20))
        self.assertTrue(rsa.prima_miller_rabin(m127, 20))
        self.assertFalse(rsa.prima_miller_rabin(m89 * m127, 20))
        with self.assertRaises(ValueError):
            rsa.prima_miller_rabin(m89, 0)

    def test_benchmark_samples_reproduce_summary_and_csv(self):
        with tempfile.TemporaryDirectory() as directory:
            with patch.object(rsa, '__file__', str(Path(directory)/'rsa_benchmark.py')):
                code, data = self.post('/api/benchmark', dict(prime_bits=[16], trials=5,
                    warmup=1, mr_rounds=20, message='1819'))
            self.assertEqual(code, 200)
            row = data['results'][0]
            self.assertIsInstance(row['p'], str)
            self.assertEqual(len(row['rsa_samples_ns']),5)
            self.assertEqual(statistics.median(row['rsa_samples_ns'])/1_000_000, row['rsa_median_ms'])
            self.assertEqual(statistics.mean(row['crt_samples_ns'])/1_000_000, row['crt_rerata_ms'])
            with (Path(directory)/'benchmark_results.csv').open(newline='',encoding='utf-8') as file:
                saved = next(csv.DictReader(file))
            self.assertEqual(json.loads(saved['rsa_samples_ns']), row['rsa_samples_ns'])

    def require_text(self):
        if not hasattr(server.RSAApiHandler, 'handle_text_encrypt'):
            self.skipTest('Text API belongs to web-mess only.')

    def test_exact_text_whitespace_unicode_nul_and_short_last_block(self):
        self.require_text()
        for text in ('  A\n', ' \t\n', 'Ã©ðŸ˜€æ—¥æœ¬èªž', '\x00A\x00', 'X'*67):
            with self.subTest(text=text):
                code,data = self.post('/api/text-encrypt',dict(text=text,p='43',q='59',e='13'))
                self.assertEqual(code,200)
                self.assertEqual(data['text_original'],text)
                self.assertEqual(data['text_decrypted_rsa'],text)
                self.assertEqual(data['text_decrypted_crt'],text)
                self.assertTrue(data['is_valid'])

    def test_text_corruption_in_either_method_is_rejected(self):
        self.require_text()
        for method in ('dekripsi_rsa','dekripsi_crt'):
            with self.subTest(method=method), patch.object(rsa,method,return_value=66):
                code,data = self.post('/api/text-encrypt',dict(text='A',p=43,q=59,e=13))
                self.assertEqual(code,400)
                self.assertIn('Verifikasi',data['message'])

    def test_generated_key_multibyte_text(self):
        self.require_text()
        text = 'Ã©ðŸ˜€'*10+'\x00\n'
        code,data = self.post('/api/text-encrypt',dict(text=text,key_mode='generate',bits=128))
        self.assertEqual(code,200)
        self.assertGreater(data['block_size_bytes'],1)
        self.assertEqual(data['text_decrypted_rsa'],text)
        self.assertEqual(data['text_decrypted_crt'],text)

    def test_empty_and_non_string_text_rejected(self):
        self.require_text()
        for text in ('', None, 43):
            code,_ = self.post('/api/text-encrypt',dict(text=text))
            self.assertEqual(code,400)


if __name__ == '__main__':
    unittest.main(verbosity=2)