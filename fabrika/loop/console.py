"""Konsol kodlaması düzeltmesi — Windows cp1254 tuzağına karşı.

Python, stdout PIPE'a yazarken yerel kodlamayı (Windows'ta cp1254) kullanır;
Türkçe karakterli çıktı UnicodeEncodeError ile süreci öldürür. Gece
koşularında tam olarak bu oldu: ozet/defter yazıldıktan sonra `print`
çöktü, çıkış kodu bozuldu, log yarım kaldı.

Çözüm: her CLI girişinde `hazirla()` çağrılır — stdout/stderr UTF-8'e
yeniden yapılandırılır, encode edilemeyen karakter 'replace' ile düşer.
Çıktı kaybolmaz, süreç yaşamaya devam eder.
"""

from __future__ import annotations

import sys


def hazirla() -> None:
    """stdout/stderr'i UTF-8 + replace olarak yeniden yapılandırır."""
    for akis in (sys.stdout, sys.stderr):
        try:
            akis.reconfigure(encoding="utf-8", errors="replace")
        except (AttributeError, ValueError):
            pass  # test ortamı string IO; dokunma