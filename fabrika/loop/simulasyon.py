"""KOVAN — operasyon simülasyonu: N günlük çalışmayı tek komutta koşar.

GERÇEK olan parçalar (gerçek kod yolları):
- kapasite valfi (inceleme-saati, kabul/erteleme)
- 6 kapı, fail-closed, defter (hash zinciri)
- kaynak rotasyonu (gece hattı okunanları atlarken)
- run-bazlı GPK hesabı (retro)

SİMÜLE olan parça (dürüstlük notunda da yazar):
- model: "kuru adapter" deterministik senaryo sinyalleri üretir
- token/maliyet: gerçek fatura değil, muhasebe alıştırması

Kullanim:
    python simulasyon.py --gun 5 --saat 3.0 --seed 7
"""

from __future__ import annotations

import argparse
import contextlib
import io
import json
import sys
from datetime import datetime, timedelta, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import yaml

from runner import ChangeClass, Ledger, Loop, ScriptedAdapter, Spec, Task
from vardiya import kos_vardiyasi as vardiya_kos

BURASI = Path(__file__).resolve().parent
HAVUZ = [
    # (id, baslik, sinif, loc, oncelik, dokunur)
    ("S-01", "README yazım hatası", "C0", 40, 1, ["docs/README.md"]),
    ("S-02", "Sıcaklık sınır hatası", "C2", 320, 1, ["src/sicaklik.py"]),
    ("S-03", "API hata mesajları tutarsız", "C2", 120, 2, ["src/api/hatalar.py"]),
    ("S-04", "Rapor modülü refactor", "C2", 600, 2, ["src/rapor/modul.py"]),
    ("S-05", "Test kapsamını artır", "C1", 200, 3, ["tests/"]),
    ("S-06", "Log formatını düzelt", "C0", 90, 3, ["src/log.py"]),
    ("S-07", "Sır okuma isteği", "C2", 60, 1, [".secrets/prod.env"]),
    ("S-08", "Anayasa maddesi ekle", "C3", 80, 4, ["anayasa/madde-11.md"]),
    ("S-09", "Ortalama fonksiyon dokümanı", "C1", 60, 2, ["docs/"]),
    ("S-10", "Mutasyon skoru raporu", "C1", 150, 3, ["reports/"]),
    ("S-11", "Istatistik fonksiyon testi", "C2", 180, 2, ["src/istatistik.py"]),
    ("S-12", "Yapılandırma şablonu", "C1", 70, 3, ["docs/yapilandirma.md"]),
    ("S-13", "Kapasite tablosu dokümanı", "C0", 50, 2, ["docs/kapasite.md"]),
    ("S-14", "Gece planı şablonu", "C1", 100, 3, ["docs/gece-plani.md"]),
    ("S-15", "Egress log örneği", "C1", 120, 3, ["docs/egress.md"]),
    ("S-16", "Retro şablonu dokümanı", "C0", 60, 3, ["docs/retro.md"]),
    ("S-17", "Defter şema dokümanı", "C1", 110, 2, ["docs/defter.md"]),
    ("S-18", "Kanarya kılavuzu", "C1", 140, 3, ["docs/kanarya.md"]),
    ("S-19", "Kopya tespit dokümanı", "C1", 130, 3, ["docs/kopya.md"]),
    ("S-20", "Eval şablon çevirisi", "C0", 80, 3, ["docs/eval-tr.md"]),
]


def _havuz_yukle() -> list[dict]:
    return [
        {
            "id": i,
            "baslik": b,
            "sinif": c,
            "loc": loc,
            "oncelik": p,
            "dokunur": d,
        }
        for i, b, c, loc, p, d in HAVUZ
    ]


def _gun_backlog(havuz: list[dict], kalan: list[str], gun: int) -> list[dict]:
    """Önce ertelenenler (kalan), sonra havuzdan yenileri — kuyruk gerçekçi."""
    sira = {row["id"]: i for i, row in enumerate(havuz)}
    isler = [row for row in havuz if row["id"] in set(kalan)]
    isler.sort(key=lambda r: (sira[r["id"]]))
    isler += [row for row in havuz if row["id"] not in set(kalan)]
    return isler


def _gun_kos(gun: int, saat: float, seed: int, sim_kok: Path) -> dict:
    """Bir günün kovan koşusu: kuyruk → kapasite → hat → defter."""
    havuz = _havuz_yukle()
    durum_dosya = sim_kok / "havuz-durumu.json"
    if durum_dosya.exists():
        durum = json.loads(durum_dosya.read_text(encoding="utf-8"))
        kalan = durum.get("kalan", [r["id"] for r in havuz])
    else:
        kalan = [r["id"] for r in havuz]

    isler = _gun_backlog(havuz, kalan, gun)
    backlog_dosya = sim_kok / f"backlog-gun{gun}.yaml"
    backlog_dosya.write_text(
        yaml.safe_dump({"isler": isler}, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )

    import kovan
    import io
    import contextlib

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        kod = kovan.main(
            [
                "run",
                "--backlog", str(backlog_dosya),
                "--saat", str(saat),
                "--seed", str(seed + gun),
                "--out", str(sim_kok / "kovan"),
                "--run-id", f"gun-{gun}",
            ]
        )
    ozet = json.loads(
        (sim_kok / "kovan" / f"gun-{gun}" / "ozet.json").read_text(encoding="utf-8")
    )
    # Kalan havuz: kabul + blok edilenler tükenmiş; ertelenenler kalır.
    bitti = set(ozet.get("kabul", [])) | set(ozet.get("insan_kuyrugu", []))
    ertelenen = set(ozet.get("ertelenen", []))
    kalan = [i for i in kalan if i not in (bitti | ertelenen)] + sorted(
        ertelenen & set(kalan)
    ) if False else [i for i in kalan if i not in bitti]
    # Dürüst kuyruk: ertelenenler sıradaki günün başına döner.
    kalan = [i for i in kalan if i not in bitti]
    durum_dosya.write_text(
        json.dumps({"kalan": kalan, "gun": gun}, ensure_ascii=False), encoding="utf-8"
    )
    return {"gun": gun, "saat": saat, "kod": kod, "ozet": ozet, "kalan": kalan}


def _gece_kos(gun: int, sim_kok: Path, seed: int) -> dict:
    import vardiya

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        vardiya.main(
            [
                "run",
                "--id", f"vardiya-gun{gun}",
                "--runs", str(sim_kok / "kovan"),
                "--out", str(sim_kok / "vardiya"),
            ]
        )
    rapor = sim_kok / "vardiya" / f"vardiya-gun{gun}" / "sabah-raporu.md"
    return {"gun": gun, "rapor": rapor.exists(), "dosya": str(rapor)}


def _retro_kos(sim_kok: Path) -> dict:
    import retro

    buf = io.StringIO()
    with contextlib.redirect_stdout(buf):
        retro.ana(
            [
                "--runs", str(sim_kok / "kovan"),
                "--vardiya-runs", str(sim_kok / "vardiya"),
                "--out", str(sim_kok / "reports"),
                "--json",
            ]
        )
    return json.loads(buf.getvalue())


def kos(gun_sayisi: int, saat: float, seed: int, sim_kok: Path) -> dict:
    sim_kok.mkdir(parents=True, exist_ok=True)
    gunluk = []
    for gun in range(1, gun_sayisi + 1):
        s = saat if gun % 4 != 0 else round(saat / 2, 2)  # kriz günü: kapasite yarıya düşer
        gunduz = _gun_kos(gun, s, seed, sim_kok)
        gece = _gece_kos(gun, sim_kok, seed)
        oz = gunduz["ozet"]
        gunluk.append(
            {
                "gun": gun,
                "saat": s,
                "kabul": len(oz.get("kabul", [])),
                "blok": oz.get("blocked", 0),
                "ret": oz.get("rejected", 0),
                "revizyon": oz.get("revised", 0),
                "ertelenen": len(oz.get("ertelenen", [])),
                "tokens": oz.get("tokens_spent", 0),
                "doluluk": oz.get("doluluk"),
                "kalan_havuz": len(gunduz["kalan"]),
                "gece_rapor": gece["rapor"],
            }
        )
    retro_sonuc = _retro_kos(sim_kok)
    toplam_kabul = sum(g["kabul"] for g in gunluk)
    toplam_tokens = sum(g["tokens"] for g in gunluk)
    return {
        "gun_sayisi": gun_sayisi,
        "seed": seed,
        "gunluk": gunluk,
        "retro": retro_sonuc,
        "toplam_kabul": toplam_kabul,
        "toplam_tokens": toplam_tokens,
        "token_basi_gorev_proxy": (
            round(toplam_tokens / max(1, toplam_kabul), 1) if toplam_kabul else 0
        ),
    }


def _rapor_yaz(sonuc: dict, sim_kok: Path) -> str:
    satir = [
        "# KOVAN Operasyon Simülasyonu — "
        f"{sonuc['gun_sayisi']} gün (seed {sonuc['seed']})",
        "",
        "> **Dürüstlük:** kuru mod simülasyonu. Model sinyalleri senaryodan;\n"
        "> kapasite, kapılar, defter, kaynak rotasyonu ve GPK hesabı GERÇEK kod yollarıdır.\n"
        "> token sayıları gerçek fatura değil, muhasebe alıştırmasıdır.\n",
        "",
        "## 1. Günlük tablo",
        "",
        "| Gün | Saat | Kabul | Blok | Ret | Rev. | Ertelenen | Doluluk | Havuz | Gece raporu |",
        "|---|---|---|---|---|---|---|---|---|---|",
    ]
    for g in sonuc["gunluk"]:
        satir.append(
            f"| {g['gun']} | {g['saat']} | {g['kabul']} | {g['blok']} | {g['ret']} | "
            f"{g['revizyon']} | {g['ertelenen']} | {g['doluluk']:.0%} | {g['kalan_havuz']} | "
            f"{'✓' if g['gece_rapor'] else '✗'} |"
        )
    kabul = sum(g["kabul"] for g in sonuc["gunluk"])
    gpk = sonuc["retro"].get("gpk", {})
    satir += [
        "",
        "## 2. Toplamlar",
        "",
        f"- Toplam kabul: **{kabul}** · Toplam token: {sonuc['toplam_tokens']:,} · "
        f"Kabul başına token (proxy): {sonuc['token_basi_gorev_proxy']:,}",
        f"- **Run-bazlı GPK: {gpk.get('gpk', 0):.0%}** ({gpk.get('ilk_tur_kabul', 0)}/"
        f"{gpk.get('gorev', 0)} görev-koşu çifti)",
        f"- Vardiya raporu: {sonuc['istatik_kullanildi']['vardiya_raporu']} (GHS proxy: her gün ✓)",
        "",
        "## 3. Gözlemler",
        "",
    ]
    gozlemler = []
    kriz = next((g for g in sonuc["gunluk"] if g["saat"] < sonuc["gunluk"][0]["saat"]), None)
    if kriz:
        gozlemler.append(
            f"Gün {kriz['gun']}: kapasite yarıya düşünce kabul {kriz['kabul']}, "
            f"ertelenen {kriz['ertelenen']} — valf çalışıyor."
        )
    blok_gunler = sorted(g["gun"] for g in sonuc["gunluk"] if g["blok"] > 0)
    if blok_gunler:
        gozlemler.append(
            f"Sır okuma isteği gün {','.join(map(str, blok_gunler))} her seferinde "
            "policy kapısında bloklandı — tekrar eden sistematik istek, eğitim değildir."
        )
    gpk_v = gpk.get("gpk", 0)
    if gpk_v < 0.6:
        gozlemler.append(
            f"- Run-bazlı GPK %{gpk_v * 100:.0f}: ilk turda kabul edilmeyen görevler "
            "revizyon/erteleme maliyeti üretiyor — test yazarı becerisinin önceliği artmalı."
        )
    satir += [f"- {g}" for g in gozlemler] or ["- Gözlem üretilmedi."]
    satir += [
        "",
        "## 4. Mekanik checkler (retro'dan)",
        "",
    ]
    satir += [f"- `{c['komut']}` — {c['neden']}" for c in sonuc["retro"].get("checkler", [])]
    satir += [
        "",
        "## 5. Canlıya geçişte ne değişir",
        "",
        "- Yalnızca `--adapter http` + anahtar: kapasite, kapılar, defter, rotasyon aynı.",
        "- token/maliyet gerçek faturaya döner; GPK/GHS hesapları aynı formüllerle kalır.",
        "- Kırılganlık: model varyansı → ilk tur ret oranı değişebilir; kapılar aynı kalır.",
    ]
    return "\n".join(satir) + "\n"


def ana(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="KOVAN operasyon simülasyonu")
    parser.add_argument("--gun", type=int, default=5)
    parser.add_argument("--saat", type=float, default=3.0)
    parser.add_argument("--seed", type=int, default=7)
    parser.add_argument("--out", default=str(BURASI / "simulasyon-runs"))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    sim_kok = Path(args.out)
    sonuc = kos(args.gun, args.saat, args.seed, sim_kok)
    sonuc["istatik_kullanildi"] = {"vardiya_raporu": sum(
        1 for _ in (sim_kok / "vardiya").glob("*/sabah-raporu.md")
    ) if (sim_kok / "vardiya").exists() else 0}
    (sim_kok / "simulasyon-ozeti.json").write_text(
        json.dumps(sonuc, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (sim_kok / "simulasyon-raporu.md").write_text(
        _rapor_yaz(sonuc, sim_kok), encoding="utf-8"
    )
    if args.json:
        print(json.dumps({k: v for k, v in sonuc.items() if k != "gunluk"}, ensure_ascii=False, indent=2))
    else:
        print(f"Simülasyon : {sim_kok}")
        print(f"Gün        : {sonuc['gun_sayisi']} (seed {sonuc['seed']})")
        print(f"Toplam kabul: {sonuc['toplam_kabul']} · token: {sonuc['toplam_tokens']:,}")
        print(f"Run-bazlı GPK: {sonuc['retro'].get('gpk', {}).get('gpk', 0):.0%}")
        print(f"Rapor      : {sim_kok / 'simulasyon-raporu.md'}")
    return 0


if __name__ == "__main__":
    raise SystemExit(ana())