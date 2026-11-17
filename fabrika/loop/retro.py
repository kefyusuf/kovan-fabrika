"""KOVAN — haftalık retrospektif üreticisi (Cuma ritüeli).

Kural (ORGANIZATION §6): her retro en az bir MEKANİK CHECK üretir;
"daha dikkatli olalım" çıktı değildir. Check = koşulabilir KOMUT.

Girdi: runs/*/ledger.jsonl + lessons.jsonl + ozet.json + beceri durumu.
Çıktı: reports/retro-<hafta>.md — sayılar, trend, mekanik checkler.

Kullanim:
    python retro.py                       # bu haftanın retrosu
    python retro.py --runs <dizin> --out <dizin> --json
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import konsol

konsol.hazirla()

from beceri import skills_tara  # noqa: E402

BURASI = Path(__file__).resolve().parent


def _jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()]


def gpk_hesapla(ledgerler: list[Path]) -> dict:
    """İlk turda kabul edilen görev oranı (GPK) — RUN-BAZLI.

    Aynı görev farklı koşularda tekrar edilirse her koşum ayrı sayılır:
    (koşu, görev) anahtarı koşu karışımını engeller (S3b kapanışı).
    """
    ilk: dict[tuple[str, str], str] = {}
    for ledger in sorted(ledgerler):
        run_adi = ledger.parent.name
        run_ilk: dict[str, str] = {}
        for kayit in _jsonl(ledger):
            p = kayit.get("payload", {})
            if p.get("type") != "decision":
                continue
            gorev = p.get("task")
            if gorev and gorev not in run_ilk:
                run_ilk[gorev] = p.get("kind", "?")
        for gorev, karar in run_ilk.items():
            ilk[(run_adi, gorev)] = karar
    gorev_sayisi = len(ilk)
    basari = sum(1 for k in ilk.values() if k == "accepted")
    return {
        "gorev": gorev_sayisi,
        "ilk_tur_kabul": basari,
        "gpk": round(basari / gorev_sayisi, 3) if gorev_sayisi else 0.0,
        "run_bazli": True,
    }


def log_saglik(runs: Path) -> dict:
    """Koşum loglarında çöküm imzası tarar (EVIDENCE §15 dersi).

    Gece koşuları artefaktları print'ten ÖNCE yazdığı için yarım/çökmüş
    koşum "başarılı" görünebiliyordu. Log bütünlüğü ayrı bir sinyaldir.
    Kodlama: yeni loglar UTF-8; eski PowerShell logları UTF-16 (BOM'lu).
    """
    taranan, bozuk = 0, []
    for p in sorted(runs.glob("*.log")):
        taranan += 1
        try:
            ham = p.read_bytes()
        except OSError:
            continue
        if ham.startswith(b"\xff\xfe") or ham.startswith(b"\xfe\xff"):
            metin = ham.decode("utf-16", errors="replace")
        else:
            metin = ham.decode("utf-8", errors="replace")
        if "Traceback" in metin or "UnicodeEncodeError" in metin:
            bozuk.append(p.name)
    return {"taranan": taranan, "bozuk": bozuk}


def mekanik_checkler(istatik: dict, dersler: dict, beceriler: list[dict]) -> list[dict]:
    """Veriden koşulabilir komutlar üretir; tavsiye DEĞİL, komut."""
    checkler: list[dict] = []

    kapı_sirasi = istatik.get("kapı_hatalari", [])
    if kapı_sirasi and kapı_sirasi[0][0] == "tests":
        checkler.append(
            {
                "tetik": f"tests kapısı {kapı_sirasi[0][1]} kez düştü",
                "komut": "python tests/skills/test_tests_kapisi.py",
                "neden": "test zayıflatma taramasının kapsam setini tazele",
            }
        )
    if istatik.get("ertelenen_is", 0) > 0:
        checkler.append(
            {
                "tetik": f"{istatik['ertelenen_is']} iş ertelendi (kapasite)",
                "komut": "python kovan.py plan --saat 3.0",
                "neden": "ertelenenler için ayrı kapasite günü planla",
            }
        )
    aktif = [b for b in beceriler if b.get("durum") == "active"]
    aday = [b for b in beceriler if b.get("durum") == "proposed"]
    if aday and not aktif:
        checkler.append(
            {
                "tetik": f"{len(aday)} beceri adayı insan onayı bekliyor",
                "komut": "python beceri.py liste",
                "neden": "C1 insan kapısı: onaylanmayan öğrenme birikir",
            }
        )
    if istatik.get("vardiya_raporu", 0) == 0:
        checkler.append(
            {
                "tetik": "vardiya raporu yok",
                "komut": "python vardiya.py run",
                "neden": "gece hattı bu hafta koşmamış",
            }
        )
    if istatik.get("log_bozuk", 0) > 0:
        checkler.append(
            {
                "tetik": f"{istatik['log_bozuk']} koşum logu çöküm imzası içeriyor",
                "komut": "python retro.py --log-saglik",
                "neden": "artefakt var ≠ koşu başarılı: exit kodu ve log bütünlüğü izlenmeli",
            }
        )
    if not checkler:
        checkler.append(
            {
                "tetik": "tüm göstergeler normal",
                "komut": "python kovan.py durum --json",
                "neden": "haftalık sayıları tazele (rutin bakım)",
            }
        )
    return checkler


def uret(runs: Path, vardiya_runs: Path, out: Path, bugun: datetime | None = None) -> dict:
    bugun = bugun or datetime.now(timezone.utc)
    hafta = bugun.strftime("%G-W%V")
    ledgerler = sorted(runs.glob("*/ledger.jsonl"))

    ozetler = []
    for oz in sorted(runs.glob("*/ozet.json")):
        veri = json.loads(oz.read_text(encoding="utf-8"))
        veri["_dizin"] = oz.parent.name
        ozetler.append(veri)
    kabul = sum(int(o.get("accepted", 0)) for o in ozetler)
    blok = sum(int(o.get("blocked", 0)) for o in ozetler)
    ertelenen = sum(len(o.get("ertelenen", [])) for o in ozetler)
    doluluklar = [float(o["doluluk"]) for o in ozetler if "doluluk" in o]

    gpk = gpk_hesapla(ledgerler)

    kapı_hatalari: Counter = Counter()
    dersler: dict[str, dict] = {}
    for ders_dosya in sorted(runs.glob("*/lessons.jsonl")):
        for kayit in _jsonl(ders_dosya):
            fp = kayit.get("fingerprint")
            if fp:
                kapı_hatalari[kayit.get("gate", "?")] += 1
                d = dersler.setdefault(fp, {"gate": kayit.get("gate", "?"), "detail": kayit.get("detail", ""), "seen": 0})
                d["seen"] += 1
    beceriler = skills_tara(BURASI / "skills")
    vardiya_raporlari = len(list(vardiya_runs.glob("*/sabah-raporu.md")))

    istatik = {
        "koşu": len(ozetler),
        "kabul": kabul,
        "blok": blok,
        "ertelenen_is": ertelenen,
        "ortalama_doluluk": round(sum(doluluklar) / len(doluluklar), 3) if doluluklar else 0.0,
        "kapı_hatalari": kapı_hatalari.most_common(3),
        "vardiya_raporu": vardiya_raporlari,
        "log_bozuk": len(log_saglik(runs)["bozuk"]),
    }

    checkler = mekanik_checkler(istatik, dersler, beceriler)

    rapor = [
        f"# Haftalık Retrospektif — {hafta}",
        "",
        f"Koşu: **{istatik['koşu']}** · Kabul: **{istatik['kabul']}** · Blok: **{istatik['blok']}** · "
        f"Ort. doluluk: **{istatik['ortalama_doluluk']:.0%}** · Vardiya raporu: **{vardiya_raporlari}**",
        "",
        "## 1. Kabul kalitesi (GPK vekili)",
        "",
        f"Görev: {gpk['gorev']} · İlk turda kabul: {gpk['ilk_tur_kabul']} · **GPK: {gpk['gpk']:.0%}**",
        "(Vekil: defterdeki ilk karar kabul ise ilk tur sayılır; revizyon sonrası kabul sayılmaz.)",
        "",
        "## 2. Kapı trendi",
        "",
    ]
    rapor += [f"- {k}: {v} kez" for k, v in istatik["kapı_hatalari"]] or ["- Kapı hatası yok."]
    rapor += ["", "## 3. Beceri durumu", ""]
    rapor += [f"- {b['ad']}: {b.get('durum', '?')}" for b in beceriler] or ["- Beceri yok."]
    rapor += [
        "",
        "## 4. Mekanik checkler (koşulabilir)",
        "",
    ]
    rapor += [f"- [{c['tetik']}] → `{c['komut']}` — {c['neden']}" for c in checkler]
    rapor += [
        "",
        "## 5. Dürüstlük notu",
        "",
        "- Sayılar defterden gelir; dry/canlı koşular aynı tabloda sayılır.",
        "- GPK vekildir: gerçek 'ilk tur' tanımı spec'te netleşene kadar yaklaşık.",
    ]

    out.mkdir(parents=True, exist_ok=True)
    dosya = out / f"retro-{hafta}.md"
    dosya.write_text("\n".join(rapor) + "\n", encoding="utf-8")

    ozet_json = {
        "hafta": hafta,
        "gpk": gpk,
        "istatik": istatik,
        "checkler": checkler,
        "dosya": str(dosya),
    }
    (out / f"retro-{hafta}.json").write_text(
        json.dumps(ozet_json, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return ozet_json


def ana(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="KOVAN haftalık retrospektif")
    parser.add_argument("--runs", default=str(BURASI / "runs"))
    parser.add_argument("--vardiya-runs", default=str(BURASI / "vardiya-runs"))
    parser.add_argument("--out", default=str(BURASI / "reports"))
    parser.add_argument("--json", action="store_true")
    parser.add_argument(
        "--log-saglik",
        action="store_true",
        help="rapor üretme; yalnız log bütünlüğü taraması yap (bozuk varsa çıkış 1)",
    )
    args = parser.parse_args(argv)

    if args.log_saglik:
        saglik = log_saglik(Path(args.runs))
        print(json.dumps(saglik, ensure_ascii=False))
        return 1 if saglik["bozuk"] else 0

    sonuc = uret(Path(args.runs), Path(args.vardiya_runs), Path(args.out))
    if args.json:
        print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    else:
        print(f"Retro dosyası: {sonuc['dosya']}")
        print(f"GPK vekili   : {sonuc['gpk']['gpk']:.0%} ({sonuc['gpk']['ilk_tur_kabul']}/{sonuc['gpk']['gorev']})")
        print(f"Checkler     : {len(sonuc['checkler'])} komut")
    return 0


if __name__ == "__main__":
    raise SystemExit(ana())