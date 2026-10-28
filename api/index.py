import sys
from pathlib import Path
from urllib.parse import parse_qs, urlparse

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from server import RSAApiHandler


class handler(RSAApiHandler):
    persist_benchmarks = False

    def do_POST(self):
        endpoint = parse_qs(urlparse(self.path).query).get('endpoint', [None])[0]
        if endpoint is not None:
            self.path = '/api/' + endpoint
        super().do_POST()

    def do_GET(self):
        self.send_json_response({'status': 'error', 'message': 'Endpoint tidak ditemukan.'}, status=404)
