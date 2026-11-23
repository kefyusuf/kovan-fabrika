"""HTTP adapter testleri - yerel sahte sunucu ile (dis ag yok)."""

from __future__ import annotations

import json
import sys
import tempfile
import threading
import unittest
from http.server import BaseHTTPRequestHandler, HTTPServer
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from adapter_http import AdapterError, HttpAdapter  # noqa: E402
from runner import ChangeClass, Task  # noqa: E402


def _gorev():
    return Task("T1", "sinir hatasi", ChangeClass.C2, touches=("src/sicaklik.py",))


class _Sunucu(BaseHTTPRequestHandler):
    mod = "ok"

    def do_POST(self):
        boy = int(self.headers.get("Content-Length", 0))
        self.rfile.read(boy)
        if _Sunucu.mod == "hata":
            self.send_response(500)
            self.end_headers()
            self.wfile.write(b"boom")
            return
        if _Sunucu.mod == "bozuk":
            govde = json.dumps({"choices": [{"message": {"content": "selam, JSON yok"}}]}).encode()
        else:
            ic = json.dumps({"diff": "--- a/src/sicaklik.py", "not": "sinir duzeltildi"})
            govde = json.dumps({"choices": [{"message": {"content": ic}}]}).encode()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.end_headers()
        self.wfile.write(govde)

    def log_message(self, *a):
        pass


class SunucuTest(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.sunucu = HTTPServer(("127.0.0.1", 0), _Sunucu)
        cls.port = cls.sunucu.server_address[1]
        cls.dizi = threading.Thread(target=cls.sunucu.serve_forever, daemon=True)
        cls.dizi.start()

    @classmethod
    def tearDownClass(cls):
        cls.sunucu.shutdown()

    def test_egress_kaydi_yazilir(self):
        with tempfile.TemporaryDirectory() as tmp:
            egress = Path(tmp) / "egress.jsonl"
            a = HttpAdapter(
                f"http://127.0.0.1:{self.port}", "anahtar", "m", egress_log=egress
            )
            a.propose(_gorev(), 1)
            kayitlar = [json.loads(s) for s in egress.read_text(encoding="utf-8").splitlines() if s]
            self.assertEqual(len(kayitlar), 1)
            self.assertEqual(kayitlar[0]["sonuc"], "ok")
            self.assertIn("127.0.0.1", kayitlar[0]["host"])

    def test_ok_yaniti_diff_uretir(self):
        a = HttpAdapter(f"http://127.0.0.1:{self.port}", "anahtar", "m")
        c = a.propose(_gorev(), 1)
        self.assertTrue(c.diff.startswith("---"))
        self.assertNotIn("tests", c.signals)  # sinyal modelden GELMEZ

    def test_bozuk_yanit_adaptererror(self):
        _Sunucu.mod = "bozuk"
        a = HttpAdapter(f"http://127.0.0.1:{self.port}", "anahtar", "m", timeout=5)
        with self.assertRaises(AdapterError):
            a.propose(_gorev(), 1)
        _Sunucu.mod = "ok"

    def test_sunucu_hatasi_iki_deneme_sonra_adaptererror(self):
        _Sunucu.mod = "hata"
        a = HttpAdapter(f"http://127.0.0.1:{self.port}", "anahtar", "m", timeout=5)
        with self.assertRaises(AdapterError):
            a.propose(_gorev(), 1)
        _Sunucu.mod = "ok"

    def test_olmayan_sunucu_fail_closed(self):
        a = HttpAdapter("http://127.0.0.1:1", "anahtar", "m", timeout=2)
        with self.assertRaises(AdapterError):
            a.propose(_gorev(), 1)


if __name__ == "__main__":
    unittest.main(verbosity=2)