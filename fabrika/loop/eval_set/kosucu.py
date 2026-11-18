"""Eval v1 kosucusu: dondurulmus vaka setini calistirir (repo icinde).

Kullanim (eval_run.py cagirir):
    python kosucu.py <set.jsonl>

Cikti: son satirda KOSONUC={"gecen":n,"toplam":m,"hatalar":[...]}
Beklenen deger "ValueError" ise fonksiyonun o hatayi firlatmasi beklenir.
"""

from __future__ import annotations

import importlib
import json
import os
import sys

# Repo kokunu import yoluna ekle (script eval_set/ altinda yasiyor).
sys.path.insert(0, os.getcwd())


def main() -> int:
    set_yolu = sys.argv[1]
    gecen = toplam = 0
    hatalar: list[dict] = []
    with open(set_yolu, encoding="utf-8") as fh:
        for satir in fh:
            satir = satir.strip()
            if not satir:
                continue
            vaka = json.loads(satir)
            toplam += 1
            etiket = str(vaka.get("etiket", f"vaka-{toplam}"))
            try:
                mod = importlib.import_module(str(vaka["modul"]))
                fn = getattr(mod, str(vaka["fonksiyon"]))
                sonuc = fn(*vaka["args"])
                bek = vaka["beklenen"]
                if isinstance(bek, str) and bek.endswith("Error"):
                    hatalar.append({"etiket": etiket, "hata": f"hata beklenirdi: {bek}"})
                    continue
                tol = float(vaka.get("tol", 1e-6))
                if abs(float(sonuc) - float(bek)) <= tol:
                    gecen += 1
                else:
                    hatalar.append({"etiket": etiket, "hata": f"{sonuc} != {bek}"})
            except Exception as e:  # noqa: BLE001 - vaka bazli izolasyon
                bek = vaka.get("beklenen")
                if isinstance(bek, str) and bek.endswith("Error") and type(e).__name__ == bek:
                    gecen += 1
                else:
                    hatalar.append({"etiket": etiket, "hata": f"{type(e).__name__}: {e}"})
    print(
        "KOSONUC="
        + json.dumps(
            {"gecen": gecen, "toplam": toplam, "hatalar": hatalar[:10]},
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())