"""KOVAN — tek giriş noktalı mini fabrika.

Üç komut:
    python kovan.py plan   --backlog sample-backlog.yaml --hours 3
    python kovan.py run    --backlog sample-backlog.yaml --hours 3
    python kovan.py verify --run runs/<id>

`run` şunları yapar:
1. backlog'u okur
2. kapasite valfinden geçirir (kaç iş alınır?)
3. kabul edilenleri hat koşucusunda çalıştırır
4. run dizinine defter, dersler, beceri adayları, rapor ve özet yazar
5. defterin hash zincirini doğrular

Model çağrılmaz: `KuruAdapter` deterministik bir senaryo üretir. Amaç,
sistemin iskeletini modelden bağımsız çalıştırmak ve ölçmek.
"""

from __future__ import annotations

import argparse
import json
import random
import sys
from collections import Counter
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

BURASI = Path(__file__).resolve().parent
sys.path.insert(0, str(BURASI))

import console

console.hazirla()

import yaml

from adapter_http import AdapterError, HttpAdapter  # noqa: E402
import skill  # noqa: E402
from verify import sinyaller  # noqa: E402
from eval_run import kos as eval_kos  # noqa: E402
from reviewer import Incelemeci, IncelemeciError  # noqa: E402
from compliance import sinyal as uyum_sinyali  # noqa: E402
from capacity import WorkItem, review_hours, accept  # noqa: E402
from runner import (  # noqa: E402
    Candidate,
    ChangeClass,
    GateSpec,
    Ledger,
    Loop,
    ScriptedAdapter,
    Spec,
    Task,
)

BURASI = Path(__file__).resolve().parent
SINIFLAR = {"C0": ChangeClass.C0, "C1": ChangeClass.C1, "C2": ChangeClass.C2, "C3": ChangeClass.C3}


def canli_kapilar_yukle(path: Path) -> list[GateSpec]:
    """gates-live.yaml -> kapı listesi (S2 geçici profili)."""
    veri = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    kapilar: list[GateSpec] = []
    for i, satir in enumerate(veri.get("gates", []), start=1):
        kapilar.append(
            GateSpec(
                name=str(satir["name"]),
                blocking=bool(satir.get("blocking", True)),
                threshold=float(satir["threshold"]) if "threshold" in satir else None,
                signal=satir.get("signal"),
                order=int(satir.get("order", i * 10)),
            )
        )
    return sorted(kapilar, key=lambda g: g.order)


def _anahtar_oku(dosya: str) -> str:
    if dosya:
        return Path(dosya).read_text(encoding="utf-8").strip()
    import os

    return os.environ.get("KOVAN_API_KEY", "").strip()


class _DogrulayanAdapter:
    """İç adapter'ın diff'ini gerçek test koşumuyla ölçer.

    Model hatası fail-closed'a dönüşür: diff='' + tests=False. Sinyal
    asla modelden alınmaz; yalnızca test koşumundan gelir.
    """

    def __init__(self, ic, repo: Path, test_komutu: str, eval_set: Path | None = None, incelemeci=None, uyum_izinli: Path | None = None):
        self.ic = ic
        self.repo = repo
        self.test_komutu = test_komutu
        self.eval_set = eval_set
        self.incelemeci = incelemeci
        self.uyum_izinli = uyum_izinli
        self.inceleme_kayitlari: dict[str, dict] = {}

    def propose(self, task, attempt: int):
        try:
            cand = self.ic.propose(task, attempt)
        except AdapterError as e:
            return Candidate(
                task_id=task.id,
                tokens=0,
                diff="",
                signals={"tests": False, "not": f"adapter hatası: {e}"},
            )
        sinyal = sinyaller(self.repo, cand.diff, self.test_komutu)
        birlesik = dict(cand.signals)
        birlesik.update(sinyal)
        # Beceri: tests-kapisi-tekrar-dusmesi — yalnızca ACTIVE ise yürütür
        # (anayasa m.6: proposed beceri pipeline'ı etkileyemez).
        aktif_mi = any(
            b["ad"] == "tests-kapisi-tekrar-dusmesi" and b.get("durum") == "active"
            for b in skill.skills_tara()
        )
        if aktif_mi:
            tarama = skill.test_zayiflatma_tespiti(cand.diff)
            if tarama["ihlal"]:
                birlesik["tests"] = False
                birlesik["tests_not"] = f"beceri taraması: {tarama['neden']}"
                skill.kullanim_yaz(BURASI / "skills", "tests-kapisi-tekrar-dusmesi")
        prov = uyum_sinyali(cand.diff, self.uyum_izinli, self.repo)
        birlesik["provenance"] = bool(prov["provenance"])
        birlesik["uyum_not"] = str(prov["not"])
        if self.eval_set is not None:
            ev = eval_kos(self.repo, self.eval_set, cand.diff)
            birlesik["eval"] = ev["skor"]
            if ev.get("hatalar"):
                birlesik["eval_not"] = "; ".join(
                    f"{h['etiket']}: {h['hata'][:60]}" for h in ev["hatalar"][:3]
                )
        if self.incelemeci is not None:
            try:
                karar = self.incelemeci.incele(
                    task.title, task.change_class.value, cand.diff, bool(sinyal.get("tests"))
                )
                birlesik["review"] = bool(karar["onay"])
                birlesik["inceleme_gerekce"] = karar["gerekce"][:300]
                self.inceleme_kayitlari[task.id] = karar
            except IncelemeciError as e:
                birlesik["review"] = False
                birlesik["inceleme_gerekce"] = f"incelemeci hatası (fail-closed): {e}"
                self.inceleme_kayitlari[task.id] = {
                    "onay": False,
                    "gerekce": birlesik["inceleme_gerekce"],
                    "bulgular": [],
                }
        birlesik["not"] = " | ".join(
            p
            for p in (str(cand.signals.get("not", "")), str(sinyal.get("not", "")))
            if p
        )
        cand.signals = birlesik
        return cand


@dataclass(frozen=True)
class BacklogIsi:
    id: str
    baslik: str
    sinif: ChangeClass
    loc: int
    oncelik: int
    bagimlilik: tuple[str, ...]
    dokunur: tuple[str, ...]

    def work_item(self) -> WorkItem:
        return WorkItem(self.id, self.loc, self.oncelik, self.bagimlilik)

    def task(self) -> Task:
        return Task(
            self.id,
            self.baslik,
            self.sinif,
            priority=self.oncelik,
            estimate_tokens=max(1_000, self.loc * 40),
            touches=self.dokunur,
        )


def backlog_oku(path: str | Path) -> list[BacklogIsi]:
    data = yaml.safe_load(Path(path).read_text(encoding="utf-8")) or {}
    isler: list[BacklogIsi] = []
    for row in data.get("isler", []):
        sinif = str(row.get("sinif", "C2")).upper()
        if sinif not in SINIFLAR:
            raise ValueError(f"{row.get('id')}: geçersiz sınıf {sinif}")
        isler.append(
            BacklogIsi(
                id=str(row["id"]),
                baslik=str(row.get("baslik", row["id"])),
                sinif=SINIFLAR[sinif],
                loc=int(row.get("loc", 150)),
                oncelik=int(row.get("oncelik", 2)),
                bagimlilik=tuple(row.get("bagimlilik", ()) or ()),
                dokunur=tuple(row.get("dokunur", ()) or ()),
            )
        )
    if not isler:
        raise ValueError("backlog boş: en az bir iş gerekli")
    return isler


def kuru_senaryo(isler: list[BacklogIsi], seed: int = 0) -> dict[str, list[Candidate]]:
    """Deterministik sahte model: aynı girdi -> aynı karar."""
    senaryo: dict[str, list[Candidate]] = {}
    for isi in isler:
        attempts: list[Candidate] = []
        for attempt in (1, 2):
            rng = random.Random(f"{seed}:{isi.id}:{attempt}")
            diff = isi.dokunur[0] if isi.dokunur else f"src/{isi.id.lower()}.py"
            signals = {
                "lint": True,
                "types": True,
                "tests": True,
                "review": True,
                "provenance": True,
                "eval": round(0.93 + rng.random() * 0.05, 3),
                "cost_usd": round(1.0 + isi.loc / 500 * 3, 2),
            }
            # İlk turda %35 test, %15 inceleme hatası; ikinci turda düzelir.
            if attempt == 1 and rng.random() < 0.35:
                signals["tests"] = False
            elif attempt == 1 and rng.random() < 0.15:
                signals["review"] = False
            attempts.append(
                Candidate(
                    task_id=isi.id,
                    tokens=max(1_000, isi.loc * 40),
                    diff=diff,
                    signals=signals,
                )
            )
        senaryo[isi.id] = attempts
    return senaryo


def _capacity_summary(items: list[BacklogIsi], hours: float):
    return accept([i.work_item() for i in items], capacity=hours)


def cmd_plan(args: argparse.Namespace) -> int:
    isler = backlog_oku(args.backlog)
    c3 = [i for i in isler if i.sinif is ChangeClass.C3]
    adaylar = [i for i in isler if i.sinif is not ChangeClass.C3]
    karar = _capacity_summary(adaylar, args.hours)
    print(f"Kapasite: {args.hours:.1f} saat")
    print(f"Kabul   : {', '.join(g.id for g in karar.accepted) or '-'}")
    print(f"Ertelenen: {', '.join(g.id for g in karar.deferred) or '-'}")
    print(f"İnsan kuyruğu (C3): {', '.join(i.id for i in c3) or '-'}")
    print(f"Doluluk : {karar.occupancy:.0%}")
    return 0


def cmd_run(args: argparse.Namespace) -> int:
    isler = backlog_oku(args.backlog)
    c3 = [i for i in isler if i.sinif is ChangeClass.C3]
    adaylar = [i for i in isler if i.sinif is not ChangeClass.C3]

    # Completion-aware kuyruk: tamamlanan işler backlog'tan çıkar.
    atlanan_tamamlanan = 0
    tamamlanan_dosya = Path(args.completed) if args.completed else None
    tamamlanan_id = set()
    if tamamlanan_dosya and tamamlanan_dosya.exists():
        for satir in tamamlanan_dosya.read_text(encoding="utf-8").splitlines():
            if satir.strip():
                tamamlanan_id.add(json.loads(satir).get("id", ""))
        onceki = len(adaylar)
        adaylar = [i for i in adaylar if i.id not in tamamlanan_id]
        atlanan_tamamlanan = onceki - len(adaylar)

    karar = _capacity_summary(adaylar, args.hours)
    kabul_id = {g.id for g in karar.accepted}
    kabul_edilen = [i for i in adaylar if i.id in kabul_id]
    if args.canary and len(kabul_edilen) > args.canary:
        # Kanarya: yalnızca ilk N iş; kalan kapasite harcanmış sayılır
        # (dürüst muhasebe) ama koşulmaz.
        karar.deferred.extend(g for g in karar.accepted[args.canary:])
        karar.accepted = karar.accepted[: args.canary]
        kabul_id = {g.id for g in karar.accepted}
        kabul_edilen = [i for i in kabul_edilen if i.id in kabul_id]

    run_id = args.run_id or datetime.now().strftime("%Y%m%d-%H%M%S")
    run_dir = Path(args.out) / run_id if args.out else BURASI / "runs" / run_id
    run_dir.mkdir(parents=True, exist_ok=True)

    spec = Spec.load(BURASI)
    canli = args.adapter == "http"
    if canli:
        spec.gates = canli_kapilar_yukle(BURASI / "gates-live.yaml")
        anahtar = _anahtar_oku(args.key_file)
        if not anahtar:
            print("HATA: anahtar yok — --key-file veya KOVAN_API_KEY ortam değişkeni")
            return 2
        ic_adapter = HttpAdapter(
            args.base_url,
            anahtar,
            args.model,
            egress_log=Path(args.egress_log) if args.egress_log else None,
        )
        incelemeci = None
        if args.review_url:
            i_anahtar = _anahtar_oku(args.review_key_file)
            if not i_anahtar:
                print("HATA: incelemeci anahtarı yok — --review-key-file veya KOVAN_API_KEY")
                return 2
            incelemeci = Incelemeci(args.review_url, i_anahtar, args.review_model)
            # Bağımsız incelemeci devrede: review kapısı bloklayıcıya yükselir
            # (gates-live.yaml'daki geçici uyarıcı durum bu koşuda kapanır).
            spec.gates = [
                GateSpec(g.name, True, g.threshold, g.signal, g.order) if g.name == "review" else g
                for g in spec.gates
            ]
        if args.repo:
            ic_adapter = _DogrulayanAdapter(
                ic_adapter,
                Path(args.repo),
                args.test_command,
                eval_set=Path(args.eval_set) if args.eval_set else None,
                incelemeci=incelemeci,
                uyum_izinli=Path(args.compliance_allowlist) if args.compliance_allowlist else None,
            )
        adapter = ic_adapter
    else:
        adapter = ScriptedAdapter(kuru_senaryo(kabul_edilen, seed=args.seed))
    loop = Loop(
        spec=spec,
        adapter=adapter,
        workdir=run_dir,
        backlog=[i.task() for i in kabul_edilen],
    )
    rapor = loop.run(max_rounds=args.max_turns)
    ok, kayit, neden = loop.ledger.verify()

    ozet = rapor.summary()
    ozet.update(
        {
            "run_id": run_id,
            "kanarya": args.canary or None,
            "tamamlanan_atlandi": atlanan_tamamlanan,
            "kapasite_saat": args.hours,
            "kabul": [g.id for g in karar.accepted],
            "ertelenen": [g.id for g in karar.deferred],
            "insan_kuyrugu": [i.id for i in c3],
            "doluluk": karar.occupancy,
            "defter": {"ok": ok, "kayit": kayit, "neden": neden},
        }
    )
    (run_dir / "ozet.json").write_text(
        json.dumps(ozet, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    (run_dir / "rapor.md").write_text(
        _rapor_yaz(
            isler,
            karar,
            rapor,
            ok,
            kayit,
            run_id,
            args.hours,
            run_dir,
            c3,
            canli,
            inceleme=getattr(adapter, "inceleme_kayitlari", None),
            kanarya=args.canary,
        ),
        encoding="utf-8",
    )

    # Tamamlanan işleri kaydet: yalnızca KABUL edilenler. Bloklananlar
    # kayda girmez → sonraki gece yeniden denenir (tekrar eden ihlal
    # trendi kaybolmasın; anayasa m.1 kanıt ilkesi).
    if tamamlanan_dosya:
        tamamlanan_dosya.parent.mkdir(parents=True, exist_ok=True)
        with tamamlanan_dosya.open("a", encoding="utf-8") as fh:
            for task_id in rapor.accepted:
                fh.write(
                    json.dumps(
                        {"id": task_id, "ts": datetime.now(timezone.utc).isoformat()},
                        ensure_ascii=False,
                    )
                    + "\n"
                )

    print(f"Koşu     : {run_dir}")
    print(f"Kabul    : {len(karar.accepted)} iş / {len(isler)}")
    print(f"Sonuç    : {len(rapor.accepted)} kabul, {len(rapor.blocked)} insan kapısı")
    print(f"Defter   : {'OK' if ok else 'KIRIK'} ({kayit} kayıt)")
    print(f"Rapor    : {run_dir / 'rapor.md'}")
    return 0 if ok else 1


def cmd_verify(args: argparse.Namespace) -> int:
    run_dir = Path(args.run)
    ok, kayit, neden = Ledger(run_dir / "ledger.jsonl").verify()
    print(f"Defter: {'OK' if ok else 'KIRIK'} — {kayit} kayıt" + (f" — {neden}" if neden else ""))
    return 0 if ok else 1


def cmd_status(args: argparse.Namespace) -> int:
    ozet = json.loads((Path(args.run) / "ozet.json").read_text(encoding="utf-8"))
    print(json.dumps(ozet, ensure_ascii=False, indent=2))
    return 0


def cmd_durum(args: argparse.Namespace) -> int:
    """Tum kosularin capraz metrikleri — haftalık retrospektifin verisi."""
    runs_kok = Path(args.runs)
    vardiya_kok = Path(args.shift_runs)

    kosular: list[dict] = []
    for ozet_dosya in sorted(runs_kok.glob("*/ozet.json")):
        oz = json.loads(ozet_dosya.read_text(encoding="utf-8"))
        oz["_dizin"] = ozet_dosya.parent.name
        kosular.append(oz)

    kabul = sum(int(o.get("accepted", 0)) for o in kosular)
    blok = sum(int(o.get("blocked", 0)) for o in kosular)
    ret = sum(int(o.get("rejected", 0)) for o in kosular)
    revizyon = sum(int(o.get("revised", 0)) for o in kosular)
    ertelenen = sum(len(o.get("ertelenen", [])) for o in kosular)
    insan = sum(len(o.get("insan_kuyrugu", [])) for o in kosular)
    doluluklar = [float(o["doluluk"]) for o in kosular if "doluluk" in o]

    kapı_hatalari: Counter = Counter()
    ders_tekrar: Counter = Counter()
    for ders_dosya in sorted(runs_kok.glob("*/lessons.jsonl")):
        for satir in ders_dosya.read_text(encoding="utf-8").splitlines():
            if not satir.strip():
                continue
            d = json.loads(satir)
            kapı_hatalari[d.get("gate", "?")] += 1
            ders_tekrar[d.get("fingerprint", "?")] += 1

    beceri = sum(
        1
        for _ in runs_kok.glob("*/skills.proposed.jsonl")
    )
    vardiya_sayisi = len(list(vardiya_kok.glob("*/sabah-raporu.md")))

    sonuc = {
        "kosu_sayisi": len(kosular),
        "toplam_kabul": kabul,
        "toplam_bloklanan": blok,
        "toplam_reddedilen": ret,
        "revizyon": revizyon,
        "ertelenen_is": ertelenen,
        "insan_kuyrugu_is": insan,
        "ortalama_doluluk": (
            round(sum(doluluklar) / len(doluluklar), 3) if doluluklar else 0.0
        ),
        "kapi_hatalari": kapı_hatalari.most_common(5),
        "tekrar_eden_ders": ders_tekrar.most_common(5),
        "beceri_adaayli_kosu": beceri,
        "vardiya_raporu": vardiya_sayisi,
        "son_kosular": [
            {
                "id": o.get("run_id", o["_dizin"]),
                "kabul": o.get("accepted", 0),
                "blok": o.get("blocked", 0),
                "doluluk": o.get("doluluk"),
            }
            for o in kosular[-5:]
        ],
    }

    if args.json:
        print(json.dumps(sonuc, ensure_ascii=False, indent=2))
    else:
        print(f"Koşu          : {sonuc['kosu_sayisi']}")
        print(f"Kabul / Blok  : {kabul} / {blok}  (ret {ret}, revizyon {revizyon})")
        print(f"Ertelenen     : {ertelenen} · İnsan kuyruğu: {insan}")
        print(f"Ort. doluluk  : {sonuc['ortalama_doluluk']:.0%}")
        print(f"Kapı hataları : {sonuc['kapi_hatalari']}")
        print(f"Vardiya raporu: {vardiya_sayisi}")
        for k in sonuc["son_kosular"]:
            print(f"  {k['id']:24} kabul={k['kabul']} blok={k['blok']} doluluk={k['doluluk']}")
    return 0


def _rapor_yaz(isler, karar, rapor, ok, kayit, run_id, saat, run_dir: Path, c3=None, canli=False, inceleme=None, kanarya=0) -> str:
    c3 = c3 or []
    c3_id = {i.id for i in c3}
    satir = [
        f"# KOVAN Koşu Raporu — {run_id}" + (f" · KANARYA ({kanarya})" if kanarya else ""),
        "",
        f"Kapasite: **{saat:.1f} saat** · Kabul: **{len(karar.accepted)}** · "
        f"Ertelenen: **{len(karar.deferred)}** · Doluluk: **{karar.occupancy:.0%}**",
        "",
        "## 1. Kapasite kararı",
        "",
        "| İş | LOC | Efor (saat) | Durum |",
        "|---|---|---|---|",
    ]
    kabul_id = {g.id for g in karar.accepted}
    for isi in sorted(isler, key=lambda i: (i.oncelik, i.loc, i.id)):
        if isi.id in c3_id:
            durum = "insan kuyruğu (C3)"
        else:
            durum = "kabul" if isi.id in kabul_id else "ertelendi"
        satir.append(f"| {isi.id} | {isi.loc} | {review_hours(isi.loc):.2f} | {durum} |")

    satir += ["", "## 2. Kararlar", "", "| Görev | Sınıf | Karar | Gerekçe |", "|---|---|---|---|"]
    siniflar = {i.id: i.sinif.value for i in isler}
    for d in rapor.decisions:
        satir.append(f"| {d.task_id} | {siniflar.get(d.task_id, '?')} | **{d.kind}** | {d.reason} |")

    if inceleme:
        satir += ["", "## 2b. Bağımsız incelemeci kararları", "", "| Görev | Onay | Gerekçe |", "|---|---|---|"]
        for gorev_id, k in inceleme.items():
            durum = "ONAY" if k.get("onay") else "RET"
            satir.append(f"| {gorev_id} | {durum} | {k.get('gerekce', '')[:200]} |")

    dersler = _jsonl(run_dir / "lessons.jsonl")
    satir += ["", "## 3. Dersler", ""]
    if dersler:
        for d in dersler:
            satir.append(f"- `{d['gate']}`: {d['detail']} (parmak izi `{d['fingerprint']}`, {d['seen']}. kez)")
    else:
        satir.append("- Tekrar eden hata yok.")

    beceriler = _jsonl(run_dir / "skills.proposed.jsonl")
    satir += ["", "## 4. Beceri adayları (aktif değil)", ""]
    if beceriler:
        for b in beceriler:
            satir.append(f"- {b['gate']} / {b['symptom']} → `{b['status']}`")
    else:
        satir.append("- Aday yok (2 tekrar eşiği geçilmedi).")

    satir += [
        "",
        "## 5. Defter",
        "",
        f"Hash zinciri: **{'sağlam' if ok else 'KIRIK'}** · {kayit} kayıt",
        "",
        "## 6. Dürüstlük notu",
        "",
        (
            "- Bu koşu **canlı**: diff gerçek modelden, `tests` sinyali gerçek test "
            "koşumundan. review/eval S3'te bloklayıcı olacak (gates-live.yaml)."
            if canli
            else "- Bu koşu **kuru koşu**: model çağrılmadı, sinyaller deterministik "
            "senaryodan geldi."
        ),
        "- Süre ve maliyet gerçek fatura değil, muhasebe alıştırması.",
        "- Kapasite hesabı gerçek; karar mekanizması test edilmiş.",
    ]
    return "\n".join(satir) + "\n"


def _jsonl(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(s) for s in path.read_text(encoding="utf-8").splitlines() if s.strip()]


def main(argv: list[str] | None = None) -> int:
    argv = list(sys.argv[1:]) if argv is None else list(argv)
    parser = argparse.ArgumentParser(description="KOVAN mini fabrika")
    parser.add_argument(
        "--config",
        default=str(BURASI / "user.yaml"),
        help="kullanıcı yapılandırması (yoksa yok sayılır)",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("plan", help="kapasiteye göre kabul listesi")
    p.add_argument("--backlog", default=str(BURASI / "sample-backlog.yaml"))
    p.add_argument("--hours", type=float, default=3.0)
    p.set_defaults(func=cmd_plan)

    r = sub.add_parser("run", help="kabul et ve çalıştır")
    r.add_argument("--backlog", default=str(BURASI / "sample-backlog.yaml"))
    r.add_argument("--hours", type=float, default=3.0)
    r.add_argument("--seed", type=int, default=0)
    r.add_argument("--max-turns", type=int, default=20)
    r.add_argument("--out", default="")
    r.add_argument("--run-id", default="")
    r.add_argument("--canary", type=int, default=0, help="yalnızca ilk N kabul edilen iş koşulur (0=kapalı)")
    r.add_argument("--completed", default="", help="tamamlanan iş kaydı (JSONL); verilirse kuyruk ilerler")
    r.add_argument("--adapter", choices=["dry", "http"], default="dry")
    r.add_argument("--base-url", default="https://api.openai.com/v1")
    r.add_argument("--model", default="gpt-4o-mini")
    r.add_argument("--key-file", default="")
    r.add_argument("--repo", default="", help="gerçek test koşumu için git deposu")
    r.add_argument("--eval-set", default="", help="dondurulmuş vaka seti (JSONL); verilirse eval bloklayıcı")
    r.add_argument("--compliance-allowlist", default=str(BURASI / "compliance-allowlist.yaml"), help="izinli üçüncü taraf import listesi")
    r.add_argument("--egress-log", default="", help="dış çağrı denetim dosyası (JSONL)")
    r.add_argument("--review-url", default="", help="bağımsız incelemeci uç noktası")
    r.add_argument("--review-model", default="")
    r.add_argument("--review-key-file", default="")
    r.add_argument(
        "--test-command",
        default="python -m unittest discover -s tests -t .",
    )
    r.set_defaults(func=cmd_run)

    v = sub.add_parser("verify", help="defteri doğrula")
    v.add_argument("--run", required=True)
    v.set_defaults(func=cmd_verify)

    s = sub.add_parser("status", help="koşu özeti")
    s.add_argument("--run", required=True)
    s.set_defaults(func=cmd_status)

    d = sub.add_parser("metrics", help="tüm koşuların çapraz metrikleri")
    d.add_argument("--runs", default=str(BURASI / "runs"))
    d.add_argument("--shift-runs", default=str(BURASI / "vardiya-runs"))
    d.add_argument("--json", action="store_true")
    d.set_defaults(func=cmd_durum)

    # Kullanıcı yapılandırması → alt ayrıştırıcı varsayılanları (CLI ezer).
    config_path = next(
        (Path(argv[i + 1]) for i, a in enumerate(argv) if a == "--config" and i + 1 < len(argv)),
        BURASI / "user.yaml",
    )
    if config_path.exists():
        try:
            veri = yaml.safe_load(config_path.read_text(encoding="utf-8")) or {}
            anahtarlar = {
                "hours": float,
                "backlog": str,
                "repo": str,
                "test_command": str,
                "model": str,
                "base_url": str,
                "key_file": str,
                "eval_set": str,
                "review_url": str,
                "compliance_allowlist": str,
                "egress_log": str,
                "canary": int,
            }
            degerler = {
                k: tip(veri[k])
                for k, tip in anahtarlar.items()
                if k in veri and veri[k] not in (None, "")
            }
            if degerler:
                for sp in (p, r, v, s, d):
                    sp.set_defaults(**degerler)
        except Exception as e:  # noqa: BLE001 — bozuk yapılandırma sessizleşmez
            print(f"UYARI: yapılandırma okunamadı ({e}); varsayılanlarla devam")

    args = parser.parse_args(argv)
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
