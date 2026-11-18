"""KOVAN — beceri yaşam döngüsü ve test zayıflatma tespiti.

İki iş:
1. **test_zayiflatma_tespiti(diff)** — `tests-kapisi-tekrar-dusmesi`
   becerisinin prosedürü. Anayasa m.2 gereği bu tespit MODELDE değil
   KODDA yaşar; diff'te tests/ altında assertion silinmesi/zayıflatması
   aranır. Sonuç `tests` kapısını etkileyebilir (kovan.py bağlar).
2. **Beceri yaşam döngüsü**: proposed → active → stale → archived.
   Aktifleşme ölçütleri (LEARNING §5):
   - becerinin kendi test dosyası var ve GEÇİYOR;
   - kanıt (evidence) en az 2 görev;
   - insan onay notu (m.2: üreten ≠ onaylayan — onay alanı zorunlu).

Kullanim:
    python beceri.py liste
    python beceri.py aktiflestir --ad tests-kapisi-tekrar-dusmesi --onay "kurucu"
    python beceri.py rapor
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import console

console.hazirla()

BURASI = Path(__file__).resolve().parent
SKILLS = BURASI / "skills"
STALE_GUN = 90

ZAYIF_DESEN = re.compile(
    r"assert\s+True\b|assert\s+False\b|assertTrue\(\s*True\s*\)|assert\s+1\s*==\s*1"
)


def test_zayiflatma_tespiti(diff: str) -> dict:
    """Diff tests/ altını değiştiriyorsa assertion kaybını/zayıflatmayı ölçer."""
    satirlar = (diff or "").splitlines()
    hedef_test = False
    silindi = False
    silinen_assert = 0
    eklenen_assert = 0
    zayif = False
    for satir in satirlar:
        if satir.startswith("diff --git") or satir.startswith("--- "):
            yol = satir.split(" b/")[-1] if " b/" in satir else satir
            hedef_test = "tests" in yol
        if satir.startswith("deleted file mode") and hedef_test:
            silindi = True
        if not hedef_test:
            continue
        if satir.startswith("-") and not satir.startswith("---") and "assert" in satir:
            silinen_assert += 1
        if satir.startswith("+") and not satir.startswith("+++") and "assert" in satir:
            eklenen_assert += 1
            if ZAYIF_DESEN.search(satir):
                zayif = True

    detay = {
        "silinen_assert": silinen_assert,
        "eklenen_assert": eklenen_assert,
        "zayif_desen": zayif,
        "test_dosyasi_silindi": silindi,
    }
    if not (hedef_test or silindi):
        return {"ihlal": False, "neden": "tests/ dokunulmadı", "detay": detay}
    if silindi:
        return {"ihlal": True, "neden": "test dosyası silindi", "detay": detay}
    if zayif:
        return {"ihlal": True, "neden": "assertion zayıflatıldı (assert True vb.)", "detay": detay}
    if silinen_assert > 0 and eklenen_assert == 0:
        return {"ihlal": True, "neden": f"assertion silindi ({silinen_assert})", "detay": detay}
    return {"ihlal": False, "neden": "meşru düzenleme", "detay": detay}


# --------------------------------------------------------------------------
# Yaşam döngüsü
# --------------------------------------------------------------------------


def skills_tara(skills_dir: Path = SKILLS) -> list[dict]:
    """skills/*/SKILL.md frontmatter'larını okur."""
    beceriler = []
    for dosya in sorted(skills_dir.glob("*/SKILL.md")):
        beceriler.append(_frontmatter(dosya))
    return beceriler


def _frontmatter(dosya: Path) -> dict:
    veri = {"ad": dosya.parent.name, "dosya": str(dosya), "durum": "proposed"}
    satirlar = dosya.read_text(encoding="utf-8").splitlines()
    icinde = False
    for satir in satirlar:
        if satir.strip() == "---":
            if icinde:
                break
            icinde = True
            continue
        if icinde and ":" in satir:
            k, v = satir.split(":", 1)
            if k.strip() == "status":
                veri["durum"] = v.strip()  # 'status' alanı 'durum' olarak sunulur
            else:
                veri[k.strip()] = v.strip()
    if "evidence" in veri:
        veri["evidence_liste"] = [
            x.strip(" []\"'") for x in veri["evidence"].split(",") if x.strip(" []\"'")
        ]
    return veri


def durum_degistir(dosya: Path, yeni_durum: str, ek_not: str = "") -> None:
    metin = dosya.read_text(encoding="utf-8")
    yeni = re.sub(
        r"(?m)^status:.*$", f"status: {yeni_durum}", metin, count=1
    )
    if ek_not:
        yeni += f"\n\n<!-- {ek_not} -->\n"
    dosya.write_text(yeni, encoding="utf-8")


def aktiflesme_kontrolu(beceri: dict, en_az_kanit: int = 2) -> tuple[bool, str]:
    """Aktifleşme ölçütlerini ölçer: test dosyası geçiyor + kanıt ≥ N + onay."""
    test_yolu = beceri.get("tests", "")
    if not test_yolu or "yok" in test_yolu:
        return False, "test dosyası yok (beceri testli değil)"
    tam = BURASI / test_yolu
    if not tam.exists():
        return False, f"test dosyası bulunamadı: {test_yolu}"
    sonuc = subprocess.run(
        [sys.executable, str(tam)], capture_output=True, text=True, timeout=120
    )
    if sonuc.returncode != 0:
        return False, f"beceri testi düşüyor: {sonuc.stderr[-200:]}"
    kanit = beceri.get("evidence_liste", [])
    if len(kanit) < en_az_kanit:
        return False, f"kanıt yetersiz: {len(kanit)} < {en_az_kanit}"
    if not beceri.get("onay"):
        return False, "insan onay notu yok (m.2)"
    if beceri.get("durum") == "active":
        return False, "zaten aktif"
    return True, "ölçütler sağlandı"


def _frontmatter_alan_yaz(dosya: Path, alan: str, deger: str) -> None:
    """Frontmatter içindeki alanı günceller; yoksa kapanış --- öncesi ekler."""
    metin = dosya.read_text(encoding="utf-8")
    desen = re.compile(rf"(?m)^{alan}:.*$")
    if desen.search(metin):
        metin = desen.sub(f"{alan}: {deger}", metin, count=1)
    else:
        parcalar = metin.split("---")
        if len(parcalar) >= 2:
            parcalar[1] = parcalar[1].rstrip("\n") + f"\n{alan}: {deger}\n"
            metin = "---".join(parcalar)
    dosya.write_text(metin, encoding="utf-8")


def aktiflestir(ad: str, onay: str, skills_dir: Path = SKILLS) -> tuple[bool, str]:
    dosya = skills_dir / ad / "SKILL.md"
    if not dosya.exists():
        return False, f"beceri yok: {ad}"
    if onay.strip():
        # İnsan kararı kayda geçer: kontrol, KAYITLI onayı görür (m.6).
        _frontmatter_alan_yaz(dosya, "onay", onay.strip())
    beceri = _frontmatter(dosya)
    ok, gerekce = aktiflesme_kontrolu(beceri)
    if not ok:
        return False, gerekce
    durum_degistir(
        dosya,
        "active",
        f"aktiflesme: {datetime.now(timezone.utc).strftime('%Y-%m-%d')} · onay: {onay}",
    )
    return True, "aktifleşti"


def kullanim_yaz(skills_dir: Path, ad: str) -> None:
    """Beceri tetiklendiğinde kullanım sayacı (Çürüme raporunun girdisi)."""
    dosya = skills_dir / "kullanim.jsonl"
    kayit = {"ad": ad, "ts": datetime.now(timezone.utc).isoformat()}
    with dosya.open("a", encoding="utf-8") as fh:
        fh.write(json.dumps(kayit, ensure_ascii=False) + "\n")


def rapor(skills_dir: Path = SKILLS, simdi: datetime | None = None) -> dict:
    """Aktif becerilerin kullanım yaşı; STALE_GUN üstü çürüme önerisi."""
    simdi = simdi or datetime.now(timezone.utc)
    kullanim: dict[str, str] = {}
    kullanim_dosya = skills_dir / "kullanim.jsonl"
    if kullanim_dosya.exists():
        for satir in kullanim_dosya.read_text(encoding="utf-8").splitlines():
            if satir.strip():
                k = json.loads(satir)
                if k["ad"] not in kullanim or k["ts"] > kullanim[k["ad"]]:
                    kullanim[k["ad"]] = k["ts"]
    cikti = []
    for b in skills_tara(skills_dir):
        son = kullanim.get(b["ad"])
        gun = None
        if son:
            fark = simdi - datetime.fromisoformat(son)
            gun = round(fark.total_seconds() / 86400, 1)
        cikti.append(
            {
                "ad": b["ad"],
                "durum": b.get("durum", "?"),
                "son_kullanim_gun": gun,
                "cürüme_onerisi": (
                    gun is not None and gun > STALE_GUN and b.get("durum") == "active"
                ),
            }
        )
    return {"beceriler": cikti, "stale_esik_gun": STALE_GUN}


def ana(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="KOVAN beceri yaşam döngüsü")
    sub = parser.add_subparsers(dest="komut", required=True)
    sub.add_parser("liste")
    a = sub.add_parser("aktiflestir")
    a.add_argument("--ad", required=True)
    a.add_argument("--onay", required=True)
    sub.add_parser("rapor")
    args = parser.parse_args(argv)

    if args.komut == "liste":
        for b in skills_tara():
            print(f"{b['ad']:34} {b.get('durum', '?'):10} kanıt={len(b.get('evidence_liste', []))}")
        return 0
    if args.komut == "aktiflestir":
        ok, gerekce = aktiflestir(args.ad, args.onay)
        print(("AKTİF: " if ok else "RED: ") + gerekce)
        return 0 if ok else 1
    if args.komut == "rapor":
        print(json.dumps(rapor(), ensure_ascii=False, indent=2))
        return 0
    return 1


if __name__ == "__main__":
    raise SystemExit(ana())