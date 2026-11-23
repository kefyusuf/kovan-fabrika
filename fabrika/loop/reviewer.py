"""KOVAN — bağımsız incelemeci adapter (ikinci model uç noktası).

Sözleşme (anayasa m.2 — üreten ≠ onaylayan):
- İncelemeci, kodu yazan modelden FARKLI bir uç nokta/modelde çalışır.
- Çıktı yapılandırılmış karar JSON'u: {"onay": bool, "gerekce": str,
  "bulgular": [...]}. "LGTM" geçersiz: gerekce boşsa onay geçersizdir.
- İncelemeci kodu DÜZELTMEZ; onay/ret + gerekçe üretir.

KOVAN bu sınıfı --review-url verildiğinde devreye alır ve review
kapısını programatik olarak bloklayıcıya yükseltir (rapora işlenir).
"""

from __future__ import annotations

import json
import urllib.error
import urllib.request

from adapter_http import _json_cikar

DEFAULT_TIMEOUT = 60.0
SYSTEM_PROMPT = (
    "Sen KOVAN fabrikasinin bagimsiz incelemecisisin. Sana bir unified diff "
    "ve test sonucu verilir. Gorevin: kapsam sapmasi, tasarim hatasi, "
    "gereksiz soyutlama ve guvenlik riski aramak. Kodu duzeltmezsin. "
    "Yanitini SADECE JSON olarak ver: "
    '{"onay": true|false, "gerekce": "...", "bulgular": ["..."]}. '
    "Onay icin gerekce zorunludur; gerekcesiz onay gecersizdir."
)


class ReviewerError(RuntimeError):
    pass


class Reviewer:
    def __init__(self, base_url: str, api_key: str, model: str, timeout: float = DEFAULT_TIMEOUT):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout

    def review(self, task_title: str, change_class: str, diff: str, tests_passed: bool) -> dict:
        user_message = "\n".join(
            [
                f"Görev: {task_title}",
                f"Sınıf: {change_class}",
                f"Test koşumu: {'GEÇTİ' if tests_passed else 'DÜŞTÜ'}",
                "Diff:",
                diff[:6000],
            ]
        )
        request = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(
                {
                    "model": self.model,
                    "messages": [
                        {"role": "system", "content": SYSTEM_PROMPT},
                        {"role": "user", "content": user_message},
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
            with urllib.request.urlopen(request, timeout=self.timeout) as response:
                data = json.loads(response.read().decode("utf-8"))
            content = data["choices"][0]["message"]["content"]
        except urllib.error.HTTPError as e:
            raise ReviewerError(f"HTTP {e.code}")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError, KeyError, IndexError) as e:
            raise ReviewerError(f"incelemeci çağrısı başarısız: {e}")

        decision = _json_cikar(content)
        if decision is None or "onay" not in decision:
            raise ReviewerError("incelemeci yanıtı karar JSON'u değil")
        approved = bool(decision.get("onay"))
        rationale = str(decision.get("gerekce", "")).strip()
        if approved and not rationale:
            # Gerekçesiz onay geçersizdir (anayasa m.2).
            approved = False
            rationale = "gerekçesiz onay reddedildi"
        return {
            "onay": approved,
            "gerekce": rationale,
            "bulgular": [str(b) for b in decision.get("bulgular", [])][:10],
        }