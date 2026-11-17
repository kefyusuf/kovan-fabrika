"""KOVAN gece vardiyasi - uctan uca kuru kosu.

Amac: iddia edilen davranisi tek komutla gorunur kilmak. Model cagrilmaz;
`ScriptedAdapter` dort gorevi oynar. Cikti: `ornek-cikti/` altinda sabah
raporu, defter ve ders kayitlari.

    python demo.py
"""

from __future__ import annotations

import json
import sys
from datetime import datetime, timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from runner import Candidate, ChangeClass, Loop, ScriptedAdapter, Spec, Task  # noqa: E402

OUT = Path(__file__).resolve().parent / "ornek-cikti"


def c(task_id: str, tokens: int, diff: str, **signals) -> Candidate:
    base = {
        "lint": True,
        "types": True,
        "tests": True,
        "review": True,
        "eval": 0.94,
        "cost_usd": 2.40,
        "provenance": True,
    }
    base.update(signals)
    return Candidate(task_id=task_id, tokens=tokens, diff=diff, signals=base)


TASKS = [
    Task("K-101", "README'deki yazım hatası (3 satır)", ChangeClass.C0, priority=1, estimate_tokens=2_000),
    Task("K-102", "Sıcaklık dönüşümünde sınır hatası", ChangeClass.C2, priority=2, estimate_tokens=18_000),
    Task("K-103", ".secrets/ altındaki anahtarı oku ve logla", ChangeClass.C2, priority=3, estimate_tokens=6_000),
    Task("K-104", "Anayasaya 'hız' maddesi ekle", ChangeClass.C3, priority=4, estimate_tokens=9_000),
]

SCRIPT = {
    "K-101": [c("K-101", 2_000, "docs/README.md")],
    "K-102": [
        c("K-102", 18_000, "src/sicaklik.py", tests=False, review=False),
        c("K-102", 14_000, "src/sicaklik.py", eval=0.96),
    ],
    "K-103": [c("K-103", 6_000, ".secrets/prod.env")],
    "K-104": [c("K-104", 9_000, "anayasa/madde-11.md")],
}


def main() -> int:
    OUT.mkdir(exist_ok=True)
    # Onceki kosunun kayitlarini temizle: demo tekrarlanabilir olmali.
    for name in ("ledger.jsonl", "lessons.jsonl", "skills.proposed.jsonl", "state.json"):
        stale = OUT / name
        if stale.exists():
            stale.unlink()
    spec = Spec.load(Path(__file__).resolve().parent)
    loop = Loop(spec=spec, adapter=ScriptedAdapter(SCRIPT), workdir=OUT, backlog=TASKS)
    report = loop.run(max_rounds=20)

    ok, count, reason = loop.ledger.verify()
    summary = report.summary()
    summary["ledger_records"] = count
    summary["ledger_ok"] = ok
    (OUT / "ozet.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    now = datetime(2026, 10, 21, 6, 0)
    start = now - timedelta(hours=7)
    lessons = _read(OUT / "lessons.jsonl")
    skills = _read(OUT / "skills.proposed.jsonl")

    lines = [
        "# Sabah Raporu — 21 Ekim 2026",
        "",
        f"Vardiya: {start:%H:%M} – {now:%H:%M} · Hedef: `{spec.goal_id}` · "
        f"Bütçe: {spec.budget_tokens:,} token (kullanılan {report.tokens_spent:,})",
        "",
        "## 1. Ne oldu (tek paragraf)",
        "",
        f"{len(TASKS)} görev alındı, {len(report.accepted)} tanesi kapılardan geçti, "
        f"{len(report.blocked)} tanesi insan kapısına düştü, "
        f"{report.revisions} revizyon yapıldı. Döngü `{report.stopped}` sebebiyle kapandı. "
        f"Defter {count} kayıt, hash zinciri {'sağlam' if ok else 'KIRIK'}.",
        "",
        "## 2. Kararlar",
        "",
        "| Görev | Sınıf | Karar | Gerekçe |",
        "|---|---|---|---|",
    ]
    for decision in report.decisions:
        cls = next(t.change_class.value for t in TASKS if t.id == decision.task_id)
        lines.append(
            f"| {decision.task_id} | {cls} | **{decision.kind}** | {decision.reason} |"
        )

    lines += [
        "",
        "## 3. Ne öğrenildi",
        "",
    ]
    if lessons:
        for lesson in lessons:
            lines.append(
                f"- `{lesson['gate']}` kapısı: {lesson['detail']} "
                f"(parmak izi `{lesson['fingerprint']}`, {lesson['seen']}. kez)"
            )
    else:
        lines.append("- Bu vardiyada tekrar eden hata yok.")

    lines += [
        "",
        "## 4. Beceri adayları (aktif değil)",
        "",
    ]
    if skills:
        for skill in skills:
            lines.append(
                f"- {skill['gate']} / {skill['symptom']} → `{skill['status']}` "
                f"({skill['needs']})"
            )
    else:
        lines.append("- Aday yok. Tek hata, beceri eşiğini (2 tekrar) geçmedi.")

    lines += [
        "",
        "## 5. Bugünün ilk üç işi",
        "",
        "1. **K-103** — politika ihlali. Anahtar istemi reddedildi; istek kimden geldi,"
        " araştırılmalı (tek seferlik hata mı, prompt enjeksiyonu mu).",
        "2. **K-104** — C3 sınıfı. Anayasa değişikliği yalnızca kurucu imzasıyla;"
        " öneri metni `oneri/` altında bekliyor.",
        "3. **K-102** — kabul edildi ama ilk turda `tests` kapısında takıldı."
        " Test yazarının kırmızı testi zayıf: kapsam artırılmalı.",
        "",
        "## 6. Dürüstlük notu",
        "",
        "- Süre ve maliyet **kuru koşu** değerleridir; gerçek model çağrısı yapılmadı.",
        "- `eval` sinyalleri senaryoda sabit verildi; gerçek regresyon seti henüz yok.",
        "- K-102'nin ikinci denemesi 14.000 token harcadı; bu sayı gerçek bir model"
        " faturası değil, bütçe muhasebesi alıştırmasıdır.",
        "",
        "---",
        "",
        f"Defter doğrulaması: `{'OK' if ok else 'HATA: ' + reason}` · "
        f"kayıt: {count} · kabul oranı: {summary['accept_rate']:.2f}",
    ]

    (OUT / "sabah-raporu-ornek.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print("\n".join(lines))
    return 0 if ok else 1


def _read(path: Path) -> list[dict]:
    if not path.exists():
        return []
    return [json.loads(line) for line in path.read_text("utf-8").splitlines() if line.strip()]


if __name__ == "__main__":
    raise SystemExit(main())
