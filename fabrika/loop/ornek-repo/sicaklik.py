"""Sıcaklık dönüşüm örnek modülü (KOVAN ornek-repo)."""


def celsius_fahrenheit(c: float) -> float:
    return c * 9 / 5 + 32


def fahrenheit_celsius(f: float) -> float:
    return (f - 32) * 5 / 9


def ortalama(degerler: list[float]) -> float:
    if not degerler:
        raise ValueError("boş liste")
    return sum(degerler) / len(degerler)
# muhafaza: eval v1


def istatistik(degerler):
    if not degerler:
        raise ValueError("bos liste")
    sirali = sorted(degerler)
    adet = len(sirali)
    toplam = 0.0
    for deger in sirali:
        toplam += float(deger)
    ortalama_deger = toplam / adet
    en_dusuk = sirali[0]
    en_yuksek = sirali[-1]
    if adet % 2 == 1:
        medyan = sirali[adet // 2]
    else:
        medyan = (sirali[adet // 2 - 1] + sirali[adet // 2]) / 2
    return {"adet": adet, "ortalama": ortalama_deger, "medyan": medyan, "en_dusuk": en_dusuk, "en_yuksek": en_yuksek}
# muhafaza: eval v1
