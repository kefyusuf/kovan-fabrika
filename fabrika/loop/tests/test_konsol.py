"""Konsol UTF-8 düzeltmesi testleri."""

from __future__ import annotations

import contextlib
import io
import sys
import unittest

from konsol import hazirla  # noqa: E402


class KonsolTest(unittest.TestCase):
    def test_string_io_guvenli_gecer(self):
        """StringIO reconfigure desteklemez — hazirla sessizce geçmeli."""
        eski = sys.stdout
        sys.stdout = io.StringIO()
        try:
            hazirla()  # istisna fırlatmamalı
        finally:
            sys.stdout = eski
        self.assertTrue(True)

    def test_gercek_akis_utf8_olur(self):
        """Gerçek stdout (test koşumunda pipe) UTF-8'e döner; Türkçe yazılır."""
        eski = sys.stdout
        try:
            hazirla()
            self.assertEqual(sys.stdout.encoding, "utf-8")
            # Cp1252 tuzağındaki karakterler artık yazılır:
            print("şğüı — Koşu tamam")
        finally:
            sys.stdout = eski

    def test_stderr_de_doner(self):
        eski = sys.stderr
        try:
            hazirla()
            self.assertEqual(sys.stderr.encoding, "utf-8")
        finally:
            sys.stderr = eski


if __name__ == "__main__":
    unittest.main(verbosity=2)
