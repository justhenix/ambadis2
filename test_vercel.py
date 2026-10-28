import json
import threading
import unittest
import urllib.error
import urllib.request
from http.server import ThreadingHTTPServer
from unittest.mock import patch

import rsa_benchmark as rsa
from api.index import handler


class HostedApiTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.http = ThreadingHTTPServer(('127.0.0.1', 0), handler)
        cls.thread = threading.Thread(target=cls.http.serve_forever, daemon=True)
        cls.thread.start()
        cls.url = f'http://127.0.0.1:{cls.http.server_port}'

    @classmethod
    def tearDownClass(cls):
        cls.http.shutdown()
        cls.thread.join(timeout=5)
        cls.http.server_close()

    def post(self, endpoint, data):
        request = urllib.request.Request(self.url + '/api/index?endpoint=' + endpoint,
            json.dumps(data).encode(), {'Content-Type':'application/json'})
        try:
            response = urllib.request.urlopen(request, timeout=45)
        except urllib.error.HTTPError as error:
            response = error
        with response:
            return response.status, json.load(response)

    def test_rewritten_simulation_preserves_exact_integers(self):
        code, data = self.post('simulasi', dict(p='1000000007',q='1000000009',e='65537',message='9007199254740993'))
        self.assertEqual(code,200)
        self.assertEqual(data['m_rsa'],'9007199254740993')
        self.assertEqual(data['m_crt'],data['m_rsa'])

    def test_benchmark_does_not_write_to_read_only_deployment(self):
        with patch.object(rsa,'simpan_csv',side_effect=PermissionError('read-only deployment')) as save:
            code,data = self.post('benchmark',dict(prime_bits=[16],trials=5,warmup=1,mr_rounds=20,message='1819'))
        save.assert_not_called()
        self.assertEqual(code,200)
        self.assertIsNone(data['csv_saved'])
        self.assertEqual(len(data['results'][0]['rsa_samples_ns']),5)

    def test_text_round_trip_and_invalid_input(self):
        text='  \u00e9\U0001f600\n\x00'
        code,data=self.post('text-encrypt',dict(text=text,p='43',q='59',e='13'))
        self.assertEqual(code,200)
        self.assertEqual(data['text_decrypted_rsa'],text)
        self.assertEqual(data['text_decrypted_crt'],text)
        code,data=self.post('simulasi',dict(p='45',q='59',e='13',message='1819'))
        self.assertEqual(code,400)

    def test_hosted_handler_does_not_serve_source_files(self):
        with self.assertRaises(urllib.error.HTTPError) as response:
            urllib.request.urlopen(self.url + '/server.py')
        self.assertEqual(response.exception.code,404)


if __name__ == '__main__':
    unittest.main(verbosity=2)
