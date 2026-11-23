"""KOVAN — bağımsız incelemeci adapter (ikinci model uç noktası).

Sözleşme (anayasa m.2 — üreten ≠ onaylayan):
- İncelemeci, kodu yazan modelden FARKLI bir uç nokta/modelde çalışır.
- Çıktı yapılandırılmış karar JSON'u: {"onay": bool, "gerekce": str,
  "bulgular": [...]}. "LGTM" geçersiz: gerekce boşsa onay geçersizdir.
- İncelemeci kodu DÜZELTMEZ; onay/ret + gerekçe üretir.

KOVAN bu sınıfı --inceleme-url verildiğinde devreye alır ve review
kapısını programatik olarak bloklayıcıya yükseltir (rapora işlenir).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from adapter_http import _json_cikar

DEFAULT_TIMEOUT = 60.0
SISTEM = (
    "Sen KOVAN fabrikasinin bagimsiz incelemecisisin. Sana bir unified diff "
    "ve test sonucu verilir. Gorevin: kapsam sapmasi, tasarim hatasi, "
    "gereksiz soyutlama ve guvenlik riski aramak. Kodu duzeltmezsin. "
    "Yanitini SADECE JSON olarak ver: "
    '{"onay": true|false, "gerekce": "...", "bulgular": ["..."]}. '
    "Onay icin gerekce zorunludur; gerekcesiz onay gecersizdir."
)


class IncelemeciError(RuntimeError):
    pass


class Incelemeci:
    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = DEFAULT_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def incele(self, task_baslik: str, sinif: str, diff: str, tests_gecti: bool) -> dict:
        kullanici = "\n".join(
            [
                f"Görev: {task_baslik}",
                f"Sınıf: {sinif}",
                f"Test koşumu: {'GEÇTİ' if tests_gecti else 'DÜŞTÜ'}",
                "Diff:",
                diff[:6000],
            ]
        )
        istek = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(
                {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": SISTEM},
                        {"role": "user", "content": kullanici},
                    ],
                    "temperature": 0.1,
                    "max_tokens": 800,
                }
            ).encode("utf-8"),
            headers={
                "Content-Type": "application/json",
                "Authorization": f"Bearer {self.api_key}",
            },
            method="POST",
        )
        try:
            with urllib.request.urlopen(istek, timeout=self.timeout) as yanit:
                veri = json.loads(yanit.read().decode("utf-8"))
            icerik = veri["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            raise IncelemeciError(f"HTTP {e.code}")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, IndexError) as e:
            raise IncelemeciError(f"incelemeci çağrısı başarısız: {e}")

        karar = _json_cikar(icerik)
        if karar is None or "onay" not in karar:
            raise IncelemeciError("incelemeci yanıtı karar JSON'u değil")
        onay = bool(karar.get("onay"))
        gerekce = str(karar.get("gerekce", "")).strip()
        if onay and not gerekce:
            # Gerekçesiz onay geçersizdir (anayasa m.2).
            onay = False
            gerekce = "gerekçesiz onay reddedildi"
        return {
            "onay": onay,
            "gerekce": gerekce,
            "bulgular": [str(b) for b in karar.get("bulgular", [])][:10],
        }