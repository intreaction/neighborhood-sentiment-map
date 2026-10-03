"""Verify the static local demo and its loopback/path restrictions."""
import http.client
from pathlib import Path
import sys
import threading
import unittest

ROOT = Path(__file__).resolve().parent.parent
sys.path.insert(0, str(ROOT / "src"))
import serve_place

class PlaceServerTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.server = serve_place.PlaceServer(("127.0.0.1", 0))
        cls.thread = threading.Thread(target=cls.server.serve_forever, daemon=True)
        cls.thread.start()
        cls.port = cls.server.server_port

    @classmethod
    def tearDownClass(cls):
        cls.server.shutdown()
        cls.server.server_close()
        cls.thread.join(timeout=2)

    def request(self, method="GET", path="/place.html", body=None, headers=None):
        client = http.client.HTTPConnection("127.0.0.1", self.port, timeout=3)
        supplied = dict(headers or {})
        client.request(method, path, body=body, headers=supplied)
        response = client.getresponse()
        data = response.read()
        result = response.status, dict(response.getheaders()), data
        client.close()
        return result

    def test_remote_origin_and_rebound_host_rejected(self):
        self.assertEqual(self.request(headers={"Origin": "https://example.com"})[0], 403)
        self.assertEqual(self.request(headers={"Host": "attacker.example"})[0], 403)
        with self.assertRaises(ValueError):
            serve_place.PlaceServer(("0.0.0.0", 0))

    def test_removed_api_endpoints_are_unavailable(self):
        for path in ("/api/status", "/api/session"):
            self.assertEqual(self.request(path=path)[0], 404)
            self.assertEqual(self.request("POST", path, "unused")[0], 405)

    def test_place_assets_and_head_are_served(self):
        for path in ("/place.html", "/place-app.js", "/place-data.json", "/place-map.json", "/place-model.json", "/place-history.json"):
            code, headers, body = self.request(path=path)
            self.assertEqual(code, 200, path)
            self.assertTrue(body, path)
            self.assertEqual(headers["Cache-Control"], "no-store")
        self.assertEqual(self.request("HEAD", "/place.html")[0], 200)

    def test_static_site_served_without_directory_listing(self):
        self.assertEqual(self.request(path="/index.html")[0], 200)
        self.assertEqual(self.request(path="/../.env")[0], 404)
        self.assertEqual(self.request(path="/api/missing")[0], 404)


if __name__ == "__main__":
    unittest.main()
