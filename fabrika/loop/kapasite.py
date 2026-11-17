"""KOVAN — Kapasite valfi.

Arastirmanin ana bulgusu: darboğaz kod üretimi değil, kabul (inceleme)
kapasitesi. Bu modül, "kaç iş alabiliriz" sorusunu hisle değil, ölçüyle
cevaplar.

Üç hesap:
1. İnceleme eforu  : LOC / 500 + PR başına 0,25 saat bağlam payı
2. Kuyruk gecikmesi: M/M/1  ->  (rho / (1-rho)) / mu
3. WIP limiti      : Little yasası  ->  hedef cycle time x günlük geliş

Kalibrasyon (arastirma):
- 400 LOC ~ 0,8-1,0 inceleme saati (Cisco/SmartBear)
- mu = 10 PR/gün tabanında: rho = 0,625 -> ~4 saat (Google <4 saat medyan)
- rho = 0,80 -> 9,6 saat; rho = 0,89 -> ~19 saat (Faros +%441)
- rho = 0,95 -> ~46 saat: sistem doygun, kuyruk iki güne çıkıyor

Not: M/M/1'de kuyruk *uzunluğu* (rho/(1-rho)) ile kuyruk *süresi*
(rho/(mu-lam)) karıştırılmamalı. Bu modül süreyi saat olarak verir.

Kullanim:
    python kapasite.py --inceleyici 2 --saat 3
    python kapasite.py --lam 9 --mu 10
"""

from __future__ import annotations

import argparse
import json
import math
from dataclasses import asdict, dataclass, field

LOC_PER_HOUR = 500.0
CONTEXT_HOURS_PER_PR = 0.25
DEFAULT_CONFLICT_RATE = 0.198  # ayni ajan, eszamanli PR ciftleri (arXiv 2607.04697)


@dataclass(frozen=True)
class Gorev:
    id: str
    loc: int
    oncelik: int = 2  # 1 = en yüksek
    bagimlilik: tuple[str, ...] = ()

    def sort_key(self) -> tuple[int, int, str]:
        return (self.oncelik, self.loc, self.id)


@dataclass
class Karar:
    kabul: list[Gorev] = field(default_factory=list)
    ertelenen: list[Gorev] = field(default_factory=list)
    kullanilan_saat: float = 0.0
    kapasite_saat: float = 0.0

    @property
    def doluluk(self) -> float:
        return round(self.kullanilan_saat / self.kapasite_saat, 4) if self.kapasite_saat else 0.0

    def ozet(self) -> dict:
        return {
            "kabul": [g.id for g in self.kabul],
            "ertelenen": [g.id for g in self.ertelenen],
            "kullanilan_saat": round(self.kullanilan_saat, 2),
            "kapasite_saat": round(self.kapasite_saat, 2),
            "doluluk": self.doluluk,
        }


def inceleme_saati(loc: int, baglam: float = CONTEXT_HOURS_PER_PR) -> float:
    """Bir PR'ı incelemek için gereken saat."""
    if loc < 0:
        raise ValueError("loc negatif olamaz")
    return loc / LOC_PER_HOUR + baglam


def kapasite_saat(inceleyici: int, odakli_saat: float) -> float:
    """Günlük/haftalık odaklı inceleme kapasitesi."""
    if inceleyici < 0 or odakli_saat < 0:
        raise ValueError("negatif girdi")
    return inceleyici * odakli_saat


def mm1_gecikme(lam: float, mu: float) -> float:
    """M/M/1 ortalama kuyruk beklemesi (saat). rho >= 1 ise sonsuz."""
    if mu <= 0:
        raise ValueError("mu pozitif olmalı")
    rho = lam / mu
    if rho >= 1:
        return math.inf
    return (rho / (1 - rho)) * (1 / mu) * 24


def wip_limiti(hedef_gun: float, gunluk_gelis: float) -> int:
    """Little yasası: L = lambda * W."""
    if hedef_gun < 0 or gunluk_gelis < 0:
        raise ValueError("negatif girdi")
    return max(0, math.floor(hedef_gun * gunluk_gelis))


def cakisan_cift(n: int, p: float = DEFAULT_CONFLICT_RATE) -> float:
    """n eşzamanlı PR için beklenen çakışan çift sayısı."""
    if n < 2:
        return 0.0
    return n * (n - 1) / 2 * p


def kabul_et(gorevler: list[Gorev], kapasite: float, wip: int | None = None) -> Karar:
    """Öncelik sırasıyla, kapasiteyi aşmadan iş kabul et."""
    if kapasite < 0:
        raise ValueError("kapasite negatif olamaz")

    kalan = kapasite
    karar = Karar(kapasite_saat=kapasite)
    adaylar = sorted(gorevler, key=lambda g: g.sort_key())
    kabul_edilen: set[str] = set()

    for gorev in adaylar:
        if wip is not None and len(karar.kabul) >= wip:
            karar.ertelenen.append(gorev)
            continue
        if any(dep not in kabul_edilen for dep in gorev.bagimlilik):
            karar.ertelenen.append(gorev)
            continue
        gerekli = inceleme_saati(gorev.loc)
        if gerekli <= kalan + 1e-9:
            karar.kabul.append(gorev)
            kabul_edilen.add(gorev.id)
            kalan -= gerekli
            karar.kullanilan_saat += gerekli
        else:
            karar.ertelenen.append(gorev)

    return karar


def kapasite_raporu(
    *,
    inceleyici: int,
    odakli_saat: float,
    lam: float,
    mu: float,
    hedef_gun: float = 1.0,
) -> dict:
    kapasite = kapasite_saat(inceleyici, odakli_saat)
    rho = lam / mu if mu else math.inf
    return {
        "kapasite_saat": kapasite,
        "gunluk_kapasite_pr": round(kapasite / (400 / LOC_PER_HOUR + CONTEXT_HOURS_PER_PR), 1),
        "rho": round(rho, 3) if math.isfinite(rho) else "sinirsiz",
        "kuyruk_gecikmesi_saat": (
            round(mm1_gecikme(lam, mu), 2) if math.isfinite(mm1_gecikme(lam, mu)) else "sinirsiz"
        ),
        "wip_limiti": wip_limiti(hedef_gun, lam),
        "tavsiye": _tavsiye(rho),
    }


def _tavsiye(rho: float) -> str:
    if rho >= 1:
        return "DUR: kapasite talebi karşılamıyor; yeni iş alma."
    if rho >= 0.85:
        return "KIS: kuyruk patlamak üzere; eşzamanlılığı düşür."
    if rho >= 0.6:
        return "DENGE: sağlıklı bant; WIP limitini koru."
    return "BOŞLUK: kapasite var; iş alımını artırabilirsin."


def _ornek_backlog() -> list[Gorev]:
    return [
        Gorev("K-101", 40, 1),
        Gorev("K-102", 320, 1),
        Gorev("K-103", 120, 2),
        Gorev("K-104", 600, 2),
        Gorev("K-105", 200, 3),
        Gorev("K-106", 90, 3),
    ]


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="KOVAN kapasite valfi")
    parser.add_argument("--inceleyici", type=int, default=1)
    parser.add_argument("--saat", type=float, default=3.0)
    parser.add_argument("--lam", type=float, default=8.0, help="günlük PR gelişi")
    parser.add_argument("--mu", type=float, default=10.0, help="günlük inceleme kapasitesi (PR)")
    parser.add_argument("--hedef-gun", type=float, default=1.0)
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    rapor = kapasite_raporu(
        inceleyici=args.inceleyici,
        odakli_saat=args.saat,
        lam=args.lam,
        mu=args.mu,
        hedef_gun=args.hedef_gun,
    )
    karar = kabul_et(_ornek_backlog(), kapasite_saat(args.inceleyici, args.saat))
    rapor["ornek_kabul"] = karar.ozet()

    if args.json:
        print(json.dumps(rapor, ensure_ascii=False, indent=2))
    else:
        print(f"Kapasite        : {rapor['kapasite_saat']:.1f} saat/gün")
        print(f"Günlük PR tavanı: {rapor['gunluk_kapasite_pr']}")
        print(f"Doluluk (rho)   : {rapor['rho']}")
        print(f"Kuyruk bekleme  : {rapor['kuyruk_gecikmesi_saat']} saat")
        print(f"WIP limiti      : {rapor['wip_limiti']}")
        print(f"Tavsiye         : {rapor['tavsiye']}")
        print(f"Örnek kabul     : {rapor['ornek_kabul']}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
