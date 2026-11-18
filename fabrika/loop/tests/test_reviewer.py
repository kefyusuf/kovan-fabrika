"""Incelemeci adapter testleri — yerel sahte sunucu ile."""

from __future__ import annotations

import json
import sys
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from reviewer import Incelemeci, IncelemeciError  # noqa: E402


class _Sunucu(BaseHTTPRequestHandler):
    mod = "onay"
    def do_POST(self):
        self.rfile.read(int(self.headers.get("Content-Length", 0)))
        if _Sunucu.mod == "onay":
            karar = {"onay": True, "gerekce": "kapsam ve tasarim uygun", "bulgular": []}
        elif _Sunucu.mod == "gerekcesiz":
            karar = {"onay": True, "gerekce": "", "bulgular": []}
        elif _Sunucu.mod == "ret":
            karar = {"onay": False, "gerekce": "spec kapsami disina cikiyor", "bulgular": ["x.py"]}
        else:
            govde = json.dumps({"choices": [{"message": {"content": "JSON degil"}}]}).encode()
            self.send_response(200); self.end_headers(); self.wfile.write(govde); return
        govde = json.dumps({"choices": [{"message": {"content": json.dumps(karar, ensure_ascii=False)}}]}).encode()
        self.send_response(200); self.send_header("Content-Type", "application/json")
        self.end_headers(); self.wfile.write(govde)
    def log_message(self, *a):
        pass


class IncelemeciTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sunucu = HTTPServer(("127.0.0.1", 0), _Sunucu)
        cls.url = f"http://127.0.0.1:{cls.sunucu.server_address[1]}"
        threading.Thread(target=cls.sunucu.serve_forever, daemon=True).start()

    @classmethod
    def tearDownClass(cls):
        cls.sunucu.shutdown()

    def _a(self):
        return Incelemeci(self.url, "anahtar", "m", timeout=5)

    def test_onay_gerekceyle(self):
        k = self._a().incele("gorev", "C2", "--- a/x.py", True)
        self.assertTrue(k["onay"])
        self.assertTrue(k["gerekce"])

    def test_gerekcesiz_onay_gecersiz(self):
        _Sunucu.mod = "gerekcesiz"
        k = self._a().incele("gorev", "C2", "--- a/x.py", True)
        self.assertFalse(k["onay"])
        _Sunucu.mod = "onay"

    def test_ret_bulgularla(self):
        _Sunucu.mod = "ret"
        k = self._a().incele("gorev", "C2", "--- a/x.py", True)
        self.assertFalse(k["onay"])
        self.assertEqual(k["bulgular"], ["x.py"])
        _Sunucu.mod = "onay"

    def test_json_olmayan_yanit(self):
        _Sunucu.mod = "bozuk"
        with self.assertRaises(IncelemeciError):
            self._a().incele("gorev", "C2", "--- a/x.py", True)
        _Sunucu.mod = "onay"


if __name__ == "__main__":
    unittest.main(verbosity=2)