"""KOVAN — Tohumlanmış hata kosucusu.

Sorun: "kapilar calisiyor" cumlesi, kapiyi gecen kodun dogru oldugu anlamina
gelmez. Olcmek icin bilinen hatalari is akisina enjekte edip kapilarin
yakalayip yakalamadigini sayariz.

Bu modul bir *simulasyon*: her hata turu, onu yakalamasi beklenen kapiya
verilir. Amac, kapi setinin kapsamini ve tekrarini gorunur kilmak.

Kritik kural: ayni hata turunu iki kapi yakaliyorsa, bu kapsam artisi degil
maliyet artisidir. Kapi sayisi degil, kapsam onemli.

Kullanim:
    python seedtest.py
    python seedtest.py --json
"""

from __future__ import annotations

import argparse
import json
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Hata:
    id: str
    tur: str
    aciklama: str


@dataclass(frozen=True)
class Kapi:
    ad: str
    yakalar: frozenset[str]
    maliyet_saat: float = 0.0


@dataclass
class Rapor:
    toplam: int
    yakalanan: int
    kacan: list[Hata] = field(default_factory=list)
    kapi_basina: dict[str, int] = field(default_factory=dict)
    tekrar_kapsam: dict[str, list[str]] = field(default_factory=dict)

    @property
    def yakalama_orani(self) -> float:
        return round(self.yakalanan / self.toplam, 4) if self.toplam else 0.0

    def ozet(self) -> dict:
        return {
            "toplam": self.toplam,
            "yakalanan": self.yakalanan,
            "yakalama_orani": self.yakalama_orani,
            "kacan": [h.id for h in self.kacan],
            "kapi_basina": self.kapi_basina,
            "tekrar_kapsam": self.tekrar_kapsam,
        }


def kos(hatalar: list[Hata], kapilar: list[Kapi]) -> Rapor:
    rapor = Rapor(toplam=len(hatalar), yakalanan=0)
    for hata in hatalar:
        yakalayanlar = [k.ad for k in kapilar if hata.tur in k.yakalar]
        if yakalayanlar:
            rapor.yakalanan += 1
            for ad in yakalayanlar:
                rapor.kapi_basina[ad] = rapor.kapi_basina.get(ad, 0) + 1
            if len(yakalayanlar) > 1:
                rapor.tekrar_kapsam[hata.id] = yakalayanlar
        else:
            rapor.kacan.append(hata)
    return rapor


def varsayilan_kapilar() -> list[Kapi]:
    return [
        Kapi("policy", frozenset({"sir_okuma", "kapsam_disi", "lisans"}), 0.01),
        Kapi("lint", frozenset({"bicim"}), 0.01),
        Kapi("types", frozenset({"tip_hatasi"}), 0.01),
        Kapi("tests", frozenset({"test_zayiflatma", "davranis_hatasi", "test_yok"}), 0.05),
        Kapi("review", frozenset({"kapsam_disi", "tasarim_hatasi"}), 0.30),
        Kapi("eval", frozenset({"davranis_hatasi", "regresyon"}), 0.10),
        Kapi("provenance", frozenset({"lisans", "kopya_kod"}), 0.01),
    ]


def varsayilan_hatalar() -> list[Hata]:
    kayitlar = [
        ("H01", "sir_okuma", "Ajan .env dosyasını okumaya çalışıyor"),
        ("H02", "sir_okuma", "Anahtar rapora sızdırılmış"),
        ("H03", "test_zayiflatma", "assert True ile test yeşile çevrilmiş"),
        ("H04", "test_zayiflatma", "Test dosyası silinmiş"),
        ("H05", "test_yok", "Yeni davranış için test eklenmemiş"),
        ("H06", "tip_hatasi", "Optional dönüş tipi yanlış kullanılmış"),
        ("H07", "tip_hatasi", "Yanlış argüman sırası"),
        ("H08", "davranis_hatasi", "Sınır koşulu (off-by-one)"),
        ("H09", "davranis_hatasi", "Hata durumunda sessiz yutma"),
        ("H10", "kapsam_disi", "Spec'te olmayan dosya değiştirilmiş"),
        ("H11", "kapsam_disi", "İstenmeyen API değişikliği"),
        ("H12", "lisans", "GPL bağımlılık eklenmiş"),
        ("H13", "lisans", "Kaynağı gösterilemeyen 60 satır kod"),
        ("H14", "kopya_kod", "Başka repodan birebir kopya"),
        ("H15", "regresyon", "Eski davranış bozulmuş"),
        ("H16", "tasarim_hatasi", "Katman sınırı ihlal edilmiş"),
        ("H17", "bicim", "Biçimlendirme bozuk"),
        ("H18", "davranis_hatasi", "Yarış koşulu (eşzamanlı yazma)"),
    ]
    return [Hata(*k) for k in kayitlar]


def karsilastir(hatalar: list[Hata], setler: dict[str, list[Kapi]]) -> dict[str, dict]:
    return {ad: kos(hatalar, kapilar).ozet() for ad, kapilar in setler.items()}


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="KOVAN tohumlanmış hata koşucusu")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    hatalar = varsayilan_hatalar()
    tam = varsayilan_kapilar()

    # Karsilastirma: hangi kapiyi cikarirsak ne kaybediyoruz?
    setler = {
        "tam": tam,
        "testsiz": [k for k in tam if k.ad != "tests"],
        "incelemesiz": [k for k in tam if k.ad != "review"],
        "policy_siz": [k for k in tam if k.ad != "policy"],
        "sadece_deterministik": [k for k in tam if k.ad in {"lint", "types", "tests"}],
    }
    sonuc = karsilastir(hatalar, setler)

    if args.json:
        print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    else:
        print(f"{'Kapi seti':22} {'Yakalama':>9} {'Kacan':>6}")
        for ad, ozet in sonuc.items():
            print(f"{ad:22} {ozet['yakalama_orani']:>9.2%} {len(ozet['kacan']):>6}")
        tam_rapor = kos(hatalar, tam)
        print("\nKapi basina yakalama:")
        for ad, sayi in sorted(tam_rapor.kapi_basina.items()):
            print(f"  {ad:12} {sayi}")
        if tam_rapor.tekrar_kapsam:
            print("\nAyni hatayi birden fazla kapi yakaliyor (kapsam degil maliyet):")
            for hid, adlar in tam_rapor.tekrar_kapsam.items():
                print(f"  {hid}: {', '.join(adlar)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
