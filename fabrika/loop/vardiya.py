"""KOVAN — gece vardiyasi (23:00-06:00).

Anayasa m.3: gece urun kodu (C2) YAZILMAZ. Bu hattin ciktisi artefakttir:
kaynakli not, beceri adayi, kirilma senaryosu, ADR taslagi, sabah raporu.

Kuru mod (bugun): "arastirmaci" yerel kaynaklardan kaynakli iddia cikarir;
"damitici" tekrar eden dersleri SKILL.md adayina cevirir; "kirmizi takim"
kapı kapsamini seedtest ile olcer; "yapi tasarımcisi" defter istatistiginden
olcum planli ADR taslagi yazar. Model baglandiginda ayni adimlar adapter'a
gecer; dosya sozlesmesi degismez.

Kullanim:
    python vardiya.py run --id ornek-vardiya
"""

from __future__ import annotations

import argparse
import json
import sys
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent))

import console

console.hazirla()

from runner import Ledger  # noqa: E402
from seedtest import kos as seedtest_kos, varsayilan_hatalar, varsayilan_kapilar  # noqa: E402

BURASI = Path(__file__).resolve().parent
KOK = BURASI.parent.parent  # calisma alani koku (izolasyon siniri)


def _jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()]


def topla_dersler(runs_dir: Path) -> dict[str, dict]:
    """Butun kovan kosularinin derslerini parmak izine gore toplar."""
    toplam: dict[str, dict] = {}
    for lessons in sorted(runs_dir.glob("*/lessons.jsonl")):
        for kayit in _jsonl(lessons):
            fp = kayit.get("fingerprint")
            if not fp:
                continue
            if fp not in toplam:
                toplam[fp] = {
                    "gate": kayit.get("gate", "?"),
                    "detail": kayit.get("detail", ""),
                    "seen": 0,
                    "tasks": [],
                }
            toplam[fp]["seen"] += 1
            if kayit.get("task") and kayit["task"] not in toplam[fp]["tasks"]:
                toplam[fp]["tasks"].append(kayit["task"])
    return toplam


def _kaynak_gecmisi(vardiya_runs: Path) -> set[str]:
    """Önceki vardiyalarda okunan kaynak yolları (rotasyon için)."""
    gecmis = vardiya_runs / "kaynak-gecmisi.jsonl"
    if not gecmis.exists():
        return set()
    return {
        kayit.get("kaynak", "")
        for kayit in _jsonl(gecmis)
        if kayit.get("kaynak")
    }


def kaynak_tara(kaynaklar: list[dict], harcanan: frozenset[str] = frozenset()) -> tuple[list[dict], list[dict]]:
    """Dosya kaynaklarindan URL tasiyan satirlari toplar; URL kaynaklarini
    kuru modda atlar (model gerekli).

    Rotasyon: harcanan (okunmuş) kaynaklar atlanır — tekrar eden ders 'yeni
    öğrenme' değildir. TÜM dosya kaynakları tükenmişse, en eski kaynaklar
    'tekrar tarama' işaretiyle yeniden okunur (açıkça işaretli).
    """
    okunan: list[dict] = []
    atlanan: list[dict] = []
    import re

    desen = re.compile(r"https?://\S+")
    dosya_yollari: list[str] = []
    cozumlu: dict[str, Path] = {}
    for kaynak in kaynaklar:
        if kaynak.get("tur") != "dosya":
            continue
        yol = Path(str(kaynak.get("yol", "")))
        if not yol.is_absolute():
            yol = (KOK / yol).resolve()
        else:
            yol = yol.resolve()
        dosya_yollari.append(str(yol))
        cozumlu[str(kaynak.get("yol", ""))] = yol
    tumu_tukendi = bool(dosya_yollari) and all(p in harcanan for p in dosya_yollari)

    for kaynak in kaynaklar:
        if kaynak.get("tur") != "dosya":
            atlanan.append({**kaynak, "neden": "kuru mod: URL kaynagi model gerekli"})
            continue
        yol = cozumlu.get(str(kaynak.get("yol", "")), Path(str(kaynak.get("yol", ""))))
        if not str(yol).startswith(str(KOK)) or not yol.is_file():
            atlanan.append({**kaynak, "neden": "izinli kok disi veya yok"})
            continue
        if str(yol) in harcanan and not tumu_tukendi:
            atlanan.append(
                {
                    "tur": "dosya",
                    "yol": kaynak.get("yol", ""),
                    "konu": kaynak.get("konu", ""),
                    "neden": "önceden okundu (rotasyon)",
                }
            )
            continue
        metin = yol.read_text(encoding="utf-8", errors="replace")
        satirlar = [s.strip() for s in metin.splitlines() if desen.search(s)]
        tekrar = str(yol) in harcanan
        for satir in satirlar[:5]:
            okunan.append(
                {
                    "konu": kaynak.get("konu", yol.name),
                    "kaynak_dosya": str(yol.relative_to(KOK)),
                    "url": desen.search(satir).group(0)[:120],
                    "baglam": satir[:180],
                    "tekrar_tarama": tekrar,
                }
            )
    return okunan, atlanan


def beceri_adayi_uret(dersler: dict[str, dict], aday_dizini: Path, en_cok: int = 3) -> tuple[list[Path], list[str]]:
    """seen >= 2 olan derslerden SKILL.md adayi uretir (status: proposed).

    Idempotent: ayni ad daha once yazildiysa DOSYA YAZILMAZ, 'zaten aday'
    olarak isaretlenir. Gece hatti tekrar eden dersi tekrar uretmemelidir.
    """
    adaylar = sorted(dersler.values(), key=lambda d: -d["seen"])
    yazilan: list[Path] = []
    zaten_var: list[str] = []
    aday_dizini.mkdir(parents=True, exist_ok=True)
    for ders in adaylar[:en_cok]:
        if ders["seen"] < 2:
            break
        gate = ders["gate"]
        ad = f"{gate}-kapisi-tekrar-dusmesi"
        dosya = aday_dizini / f"{ad}.md"
        if dosya.exists():
            zaten_var.append(ad)
            continue
        icerik = (
            "---\n"
            f"name: {ad}\n"
            f"when_to_use: Bir degisiklik `{gate}` kapida ayni nedenle dustugunde\n"
            "version: 0.1.0\n"
            "status: proposed\n"
            f"evidence: {json.dumps(ders['tasks'])}\n"
            "tests: yok (S3b — seedtest kapsamina eklenecek)\n"
            "---\n\n"
            "## Semptom\n"
            f"`{gate}` kapisi ayni nedenle tekrar dusuyor: {ders['detail']}\n"
            f"({ders['seen']} kez, gorevler: {', '.join(ders['tasks'] or ['-'])})\n\n"
            "## Prosedur\n"
            f"1. Neden analizi: `{gate}` kapisinin kuralini degistirmeden kok nedeni yazar.\n"
            "2. Kapsami kontrol et: spec'te olmayan dosya varsa reddet.\n"
            "3. Testi guclendir: yeni test eski davranisi da kapsamali.\n"
            "4. Gerekceyi deftere yaz; kapı kuralina dokunma (C3).\n\n"
            "## Dogrulama\n"
            "- Bu beceri uygulandiginda ayni fingerprintin tekrar etmemesi.\n\n"
            "## Sinirlar\n"
            "- Yalnizca ayni hata sinifi icin; genel tavsiye degildir.\n"
        )
        dosya = aday_dizini / f"{ad}.md"
        dosya.write_text(icerik, encoding="utf-8")
        yazilan.append(dosya)
    return yazilan, zaten_var


def kirmizi_takim() -> dict:
    hatalar = varsayilan_hatalar()
    tam = seedtest_kos(hatalar, varsayilan_kapilar())
    canli_kapilar = [k for k in varsayilan_kapilar() if k.ad != "review"]
    canli = seedtest_kos(hatalar, canli_kapilar)
    kacan_canli = {h.id for h in canli.kacan}
    kacan_tam = {h.id for h in tam.kacan}
    kirilanlar = sorted({h.tur for h in hatalar if h.id in (kacan_canli - kacan_tam)})
    return {
        "tam_kapsam": tam.yakalama_orani,
        "canli_profili": canli.yakalama_orani,
        "kirilma_senaryolari": kirilanlar,
        "tekrar_kapsam": sorted(tam.tekrar_kapsam),
    }


def defter_istatigi(runs_dir: Path) -> dict:
    karar = Counter()
    kapı_hatalari: Counter = Counter()
    for ledger in sorted(runs_dir.glob("*/ledger.jsonl")):
        for kayit in _jsonl(ledger):
            p = kayit.get("payload", {})
            if p.get("type") != "decision":
                continue
            karar[p.get("kind", "?")] += 1
            for g in p.get("gates", []):
                if not g.get("ok") and g.get("blocking"):
                    kapı_hatalari[g["gate"]] += 1
    return {
        "kararlar": dict(karar),
        "en_cok_dusen_kapi": kapı_hatalari.most_common(3),
        "toplam_karar": sum(karar.values()),
    }


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="KOVAN gece vardiyasi")
    sub = parser.add_subparsers(dest="komut", required=True)
    r = sub.add_parser("run")
    r.add_argument("--id", default=datetime.now().strftime("vardiya-%Y%m%d-%H%M"))
    r.add_argument("--kaynak", default=str(BURASI / "source-queue.yaml"))
    r.add_argument("--runs", default=str(BURASI / "runs"))
    r.add_argument("--out", default=str(BURASI / "vardiya-runs"))
    args = parser.parse_args(argv)
    return kos_vardiyasi(args)


def kos_vardiyasi(args) -> int:
    cikti = Path(args.out) / args.id
    cikti.mkdir(parents=True, exist_ok=True)
    ledger = Ledger(cikti / "ledger.jsonl")

    # 1. Acilis: plan
    plan = [
        "# Gece Planı — " + args.id,
        "",
        "| Blok | Süre | Çıktı | Durum |",
        "|---|---|---|---|",
        "| Tarama | 60 dk | kaynaklı not | aşağıda |",
        "| Damıtma | 90 dk | beceri adayı | aşağıda |",
        "| Kırmızı takım | 60 dk | kırılma senaryosu | aşağıda |",
        "| Yapı önerisi | 45 dk | ADR taslağı | aşağıda |",
        "| Bellek + rapor | 45 dk | sabah raporu | aşağıda |",
    ]
    (cikti / "plan.md").write_text("\n".join(plan) + "\n", encoding="utf-8")
    ledger.append({"type": "vardiya_baslangic", "id": args.id})

    # 2. Tarama (rotasyon: önceden okunanlar atlanır)
    kaynaklar = []
    kuyruk_dosya = Path(args.kaynak)
    if kuyruk_dosya.exists():
        veri = yaml.safe_load(kuyruk_dosya.read_text(encoding="utf-8")) or {}
        kaynaklar = veri.get("kaynaklar", [])
    harcanan = _kaynak_gecmisi(Path(args.out))
    okunan, atlanan = kaynak_tara(kaynaklar, harcanan)
    gecmis_dosya = Path(args.out) / "kaynak-gecmisi.jsonl"
    for n in okunan:
        with gecmis_dosya.open("a", encoding="utf-8") as fh:
            fh.write(
                json.dumps(
                    {
                        "kaynak": str((KOK / n["kaynak_dosya"]).resolve()),
                        "ts": datetime.now(timezone.utc).isoformat(),
                        "tekrar_tarama": bool(n.get("tekrar_tarama")),
                    },
                    ensure_ascii=False,
                )
                + "\n"
            )
    (cikti / "notlar.md").write_text(
        "# Kaynaklı Notlar (kuru mod)\n\n"
        + (
            "\n".join(
                f"- **{n['konu']}** — `{n['kaynak_dosya']}` → {n['url']}"
                + (" — TEKRAR TARAMA" if n.get("tekrar_tarama") else "")
                + f"\n  - {n['baglam']}"
                for n in okunan
            )
            if okunan
            else "- Kaynak okunamadı."
        )
        + "\n",
        encoding="utf-8",
    )
    for n in okunan[:3]:
        ledger.append({"type": "kaynak_okundu", "url": n["url"], "konu": n["konu"]})

    # 3. Damıtma
    dersler = topla_dersler(Path(args.runs))
    # Beceri adayları paylaşılan dizine yazılır: her gece aynı adayı
    # yeniden üretmek, tekrar eden ders için 'yeni öğrenme' izlenimi verir.
    aday_dizini = cikti.parent / "beceri-adaylari"
    adaylar, aday_zaten = beceri_adayi_uret(dersler, aday_dizini)
    for a in adaylar:
        ledger.append({"type": "beceri_adayi", "dosya": a.name})
    for ad in aday_zaten:
        ledger.append({"type": "beceri_adayi_zaten_var", "dosya": ad})

    # 4. Kırmızı takım
    kirilma = kirmizi_takim()
    (cikti / "kirilma.md").write_text(
        "# Kırmızı Takım — kapı kapsamı\n\n"
        f"- Tam set yakalama: **{kirilma['tam_kapsam']:.0%}**\n"
        f"- Canlı profil yakalama: **{kirilma['canli_profili']:.0%}**\n"
        f"- Canlı profilde kırılan hata türleri: {', '.join(kirilma['kirilma_senaryolari']) or 'yok'}\n"
        f"- Tekrar kapsam (maliyet): {', '.join(kirilma['tekrar_kapsam']) or 'yok'}\n",
        encoding="utf-8",
    )
    ledger.append({"type": "kirilma_raporu", "veri": kirilma})

    # 5. Yapı önerisi
    istatik = defter_istatigi(Path(args.runs))
    en_cok = istatik["en_cok_dusen_kapi"][0][0] if istatik["en_cok_dusen_kapi"] else "yok"
    oneri = (
        "# ADR Taslağı (otomatik öneri — C3, insan onayı bekler)\n\n"
        "**Bağlam.** Defter istatistiği: "
        f"{json.dumps(istatik['kararlar'], ensure_ascii=False)} · "
        f"en çok düşen kapı: `{en_cok}`.\n\n"
        f"**Öneri.** `{en_cok}` kapısının ret nedenlerinin tekrarını azaltacak\n"
        "beceri adayına öncelik ver (varsa). Kadro/eşik değişikliği önerilmez.\n\n"
        "**Ölçüm planı.** 2 hafta boyunca aynı kapının ilk tur ret oranı;\n"
        "başarı ölçütü: %15 görece düşüş. Ölçülemezse öneri reddedilir.\n"
    )
    oneri_dizin = cikti / "oneri"
    oneri_dizin.mkdir(exist_ok=True)
    (oneri_dizin / "ADR-taslagi.md").write_text(oneri, encoding="utf-8")
    ledger.append({"type": "oneri", "en_cok_dusen_kapi": en_cok})

    # 6. Sabah raporu (5 bölüm)
    rapor = [
        f"# Sabah Raporu — {args.id}",
        "",
        f"Vardiya: kuru mod · Kaynak: {len(okunan)} okundu / {len(atlanan)} atlandı · "
        f"Ders toplamı: {sum(d['seen'] for d in dersler.values())}",
        "",
        "## 1. Ne öğrenildi (kaynaklı)",
        "",
    ]
    rapor += [f"- `{n['kaynak_dosya']}` → {n['url']}" for n in okunan[:5]] or ["- (kaynak okunamadı)"]
    rapor += [
        "",
        "## 2. Ne üretildi",
        "",
    ]
    rapor += [f"- Beceri adayı: `{a.name}` (status: proposed)" for a in adaylar] or [
        "- Beceri adayı yok (2 tekrar eşiği geçilmedi)."
    ]
    rapor += [f"- Zaten adaydı (yeniden üretilmedi): {a}" for a in aday_zaten]
    rapor += ["- Kırmızı takım: `kirilma.md`", "- ADR taslağı: `oneri/ADR-taslagi.md`"]
    rapor += [
        "",
        "## 3. Ne reddedildi ve neden",
        "",
    ]
    rapor += [f"- {s.get('yol', s.get('url', '?'))}: {s['neden']}" for s in atlanan] or ["- Reddedilen yok."]
    rapor += [
        "",
        "## 4. Bugünün ilk üç işi",
        "",
    ]
    en_son_ozet = sorted(Path(args.runs).glob("*/ozet.json"))
    if en_son_ozet:
        oz = json.loads(en_son_ozet[-1].read_text(encoding="utf-8"))
        ilk = (oz.get("insan_kuyrugu") or ["insan kuyruğu boş"])[0]
        ert = (oz.get("ertelenen") or ["ertelenen yok"])[:2]
        rapor += [f"1. İnsan kuyruğu: **{ilk}**", f"2. Ertelenen işler: {', '.join(ert)}"]
        rapor.append("3. En çok düşen kapıyı hedefleyen beceri adayını gölge modda dene")
    else:
        rapor += ["1. Kovan koşusu bulunamadı — önce `kovan.py run`"]
    rapor += [
        "",
        "## 5. Dürüstlük notu",
        "",
        "- Kuru mod: URL kaynakları ve model analizleri **çalıştırılamadı** (model gerekli).",
        "- Aday beceriler henüz testli değil; aktifleşme S3b'de seedtest kapsamıyla ölçülecek.",
        f"- Defter: {ledger.verify()[1]} kayıt, zincir {'sağlam' if ledger.verify()[0] else 'KIRIK'}.",
        "",
    ]
    (cikti / "sabah-raporu.md").write_text("\n".join(rapor) + "\n", encoding="utf-8")
    ledger.append({"type": "rapor_yazildi"})

    ok, kayit, neden = ledger.verify()
    print(f"Vardiya  : {cikti}")
    print(f"Kaynak   : {len(okunan)} okundu / {len(atlanan)} atlandı")
    print(f"Beceri   : {len(adaylar)} aday")
    print(f"Kırılma  : {len(kirilma['kirilma_senaryolari'])} senaryo (canlı profil)")
    print(f"Defter   : {'OK' if ok else 'KIRIK'} ({kayit} kayıt)")
    print(f"Rapor    : {cikti / 'sabah-raporu.md'}")
    return 0 if ok else 1


if __name__ == "__main__":
    raise SystemExit(main())