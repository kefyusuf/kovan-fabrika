"""KOVAN — kanıtlı iş önerisi üreticisi (kuyruk kendi kendini besler).

Kural: fabrika kendi kendine İŞ ÜRETMEZ; kanıtla ÖNERİ üretir. Öneriler
`backlog-proposals.yaml` dosyasına yazılır ve insan onayı bekler (C1/C2).
Onaylanmadan üretim kuyruğuna girmez.

Girdi: defterler (tekrar eden dersler, doluluk), son vardiya raporu
(kırılma senaryoları), beceri durumu.
Çıktı: backlog-proposals.yaml + oneri-raporu.md (her öneri kanıtlı).

Kullanim:
    python queue_build.py --runs runs --vardiya-runs vardiya-runs --out .
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
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


def _son_vardiya_ledger(vardiya_runs: Path) -> dict | None:
    adaylar = sorted(vardiya_runs.glob("*/ledger.jsonl"))
    if not adaylar:
        return None
    kirilma = None
    for kayit in _jsonl(adaylar[-1]):
        p = kayit.get("payload", {})
        if p.get("type") == "kirilma_raporu":
            kirilma = p.get("veri", {})
    return kirilma


def oneriler(runs: Path, vardiya_runs: Path) -> list[dict]:
    oneriler: list[dict] = []

    # 1. Tekrar eden ders → beceri kapsam önerisi (C1)
    parmak: Counter = Counter()
    gate_adi: dict[str, str] = {}
    for ders_dosya in sorted(runs.glob("*/lessons.jsonl")):
        for kayit in _jsonl(ders_dosya):
            fp = kayit.get("fingerprint")
            if fp:
                parmak[fp] += 1
                gate_adi.setdefault(fp, kayit.get("gate", "?"))
    for fp, sayi in parmak.most_common(2):
        if sayi >= 3:
            gate = gate_adi.get(fp, "?")
            oneriler.append(
                {
                    "id": f"O-{len(oneriler) + 1:02}",
                    "baslik": f"{gate} kapısı tekrarını azaltacak beceri kapsamı",
                    "sinif": "C1",
                    "loc": 120,
                    "oncelik": 2,
                    "gerekce": f"Aynı hata sınıfı {sayi} kez tekrar etti; beceri kapsamı genişletilmeli.",
                    "kanit": {"fingerprint": fp, "seen": sayi, "gate": gate},
                }
            )

    # 2. Kırılma senaryosu → kapı profil önerisi (C3)
    kirilma = _son_vardiya_ledger(vardiya_runs)
    if kirilma and kirilma.get("kirilma_senaryolari"):
        turler = ", ".join(kirilma["kirilma_senaryolari"])
        oneriler.append(
            {
                "id": f"O-{len(oneriler) + 1:02}",
                "baslik": f"Canlı profilde yakalanmayan türler için kapı: {turler}",
                "sinif": "C3",
                "loc": 80,
                "oncelik": 1,
                "gerekce": "Kırmızı takım, canlı profilin bu hata türlerini kaçırdığını ölçtü.",
                "kanit": kirilma,
            }
        )

    # 3. Yüksek doluluk → kapasite planı (C1)
    ozetler = sorted(runs.glob("*/ozet.json"))
    if ozetler:
        son = json.loads(ozetler[-1].read_text(encoding="utf-8"))
        if float(son.get("doluluk", 0)) > 0.85:
            oneriler.append(
                {
                    "id": f"O-{len(oneriler) + 1:02}",
                    "baslik": "Ertelenen işler için ayrı kapasite günü",
                    "sinif": "C1",
                    "loc": 60,
                    "oncelik": 3,
                    "gerekce": f"Son koşu doluluğu %{float(son['doluluk']) * 100:.0f} — kuyruk büyüyor.",
                    "kanit": {"doluluk": son.get("doluluk"), "ertelenen": son.get("ertelenen")},
                }
            )

    # 4. Aktif beceri yok → bellek bakımı (C1)
    beceriler = skills_tara(BURASI / "skills")
    if beceriler and not any(b.get("durum") == "active" for b in beceriler):
        oneriler.append(
            {
                "id": f"O-{len(oneriler) + 1:02}",
                "baslik": "Beceri adaylarını insan onayına sun",
                "sinif": "C1",
                "loc": 40,
                "oncelik": 2,
                "gerekce": "Aday var, aktif beceri yok — öğrenme birikiyor ama kullanılmıyor.",
                "kanit": {"aday": len(beceriler)},
            }
        )
    return oneriler


def yaz(oneriler_liste: list[dict], out: Path) -> tuple[Path, Path]:
    out.mkdir(parents=True, exist_ok=True)
    yaml_dosya = out / "backlog-proposals.yaml"
    isler = [
        {
            "id": o["id"],
            "baslik": o["baslik"],
            "sinif": o["sinif"],
            "loc": o["loc"],
            "oncelik": o["oncelik"],
            "dokunur": [],
            "gerekce": o["gerekce"],
        }
        for o in oneriler_liste
    ]
    basliklar = ["# KOVAN — kanıtlı iş önerileri (insan onayı bekler)"]
    basliklar.append("# Onaylanmadan üretim kuyruğuna girmez. Kanıt: oneri-raporu.md")
    import yaml

    yaml_dosya.write_text(
        "\n".join(basliklar) + "\n" + yaml.safe_dump({"isler": isler}, allow_unicode=True, sort_keys=False),
        encoding="utf-8",
    )
    rapor = out / "oneri-raporu.md"
    satir = ["# İş Önerileri — kanıtlı", ""]
    satir += [
        f"## {o['id']} — {o['baslik']}\n\n"
        f"- Sınıf: **{o['sinif']}** · LOC: {o['loc']} · Öncelik: {o['oncelik']}\n"
        f"- Gerekçe: {o['gerekce']}\n"
        f"- Kanıt: `{json.dumps(o['kanit'], ensure_ascii=False)[:300]}`\n"
        for o in oneriler_liste
    ] or ["Öneri yok — tüm göstergeler normal."]
    rapor.write_text("\n".join(satir) + "\n", encoding="utf-8")
    return yaml_dosya, rapor


def ana(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="KOVAN kanıtlı iş önerisi üreticisi")
    parser.add_argument("--runs", default=str(BURASI / "runs"))
    parser.add_argument("--vardiya-runs", default=str(BURASI / "vardiya-runs"))
    parser.add_argument("--out", default=str(BURASI))
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args(argv)

    liste = oneriler(Path(args.runs), Path(args.vardiya_runs))
    yaml_dosya, rapor = yaz(liste, Path(args.out))
    if args.json:
        print(json.dumps({"oneriler": liste, "yaml": str(yaml_dosya)}, ensure_ascii=False, indent=2))
    else:
        print(f"Öneri: {len(liste)}")
        for o in liste:
            print(f"  {o['id']} [{o['sinif']}] {o['baslik']}")
        print(f"Dosya: {yaml_dosya}")
    return 0


if __name__ == "__main__":
    raise SystemExit(ana())