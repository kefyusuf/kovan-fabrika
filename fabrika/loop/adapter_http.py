"""KOVAN — HTTP model adapter (OpenAI-uyumlu /chat/completions).

Amac: hat koşucusunun `Adapter` arayuzunu gercek bir modele baglamak.
Sozlesme:
- adapter SADECE diff (oneren degisiklik) uretir; "testler gecti" gibi
  sinyalleri MODEL SOYLEMEZ. Sinyaller dogrulama katmanindan (verify.py)
  gelir. Bu, "ajanin kendi testi kendi kodunu dogrulamaz" kuralinin
  kod karsiligidir.
- Ag/JSON hatasinda iki deneme yapar, sonra AdapterError firlatir.
  Kosucu bunu "sinyal yok" olarak gorur ve kapilar kapatir (fail-closed).

Kullanim:
    from adapter_http import HttpAdapter
    a = HttpAdapter(base_url="https://api.x.com/v1",
                    api_key="...", model="...")
    cand = a.propose(task, attempt=1)
"""

from __future__ import annotations

import json
import re
import time
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from runner import Candidate, Task

DEFAULT_TIMEOUT = 60.0
DENEME = 2
SISTEM_PROMPTU = (
    "Sen KOVAN fabrikasinin kodlayicisisin. Gorev icin TEK bir unified diff "
    "uretirsin. Kurallar: (1) yalnizca verilen dosyalara dokun, (2) kod "
    "yazmadan once test ekle, (3) .secrets/ ve anayasa/ altina yazma, "
    "(4) yanitini SADECE JSON olarak ver: {\"diff\": \"...\", \"not\": \"...\"}."
)


class AdapterError(RuntimeError):
    """Model cagrisi basarisiz: kosucu 'sinyal yok' ile kapali kalmali."""


class HttpAdapter:
    def __init__(
        self,
        base_url: str,
        api_key: str,
        model: str,
        timeout: float = DEFAULT_TIMEOUT,
        max_tokens: int = 1200,
        temperature: float = 0.2,
        egress_log: Path | None = None,
    ):
        self.base_url = base_url.rstrip("/")
        self.api_key = api_key
        self.model = model
        self.timeout = timeout
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.egress_log = Path(egress_log) if egress_log else None

    # -- public ---------------------------------------------------------
    def propose(self, task: Task, attempt: int) -> Candidate:
        icerik = self._cagir(self._prompt(task, attempt))
        veri = _json_cikar(icerik)
        if veri is None or not veri.get("diff"):
            raise AdapterError("model yanıtı JSON/diff içermiyor")
        return Candidate(
            task_id=task.id,
            tokens=0,  # gerçek fatura sağlayıcıdan gelir; burada ölçülmez
            diff=str(veri["diff"]),
            signals={"not": str(veri.get("not", ""))[:400]},
        )

    # -- private --------------------------------------------------------
    def _prompt(self, task: Task, attempt: int) -> list[dict[str, str]]:
        kullanici = [
            f"Görev: {task.title}",
            f"Değişiklik sınıfı: {task.change_class.value}",
            f"Dokunulacak dosyalar: {', '.join(task.touches) or 'belirtilmedi'}",
        ]
        if attempt > 1:
            kullanici.append(
                "Önceki deneme kapılarda düştü. Diff'i KÜÇÜLT ve testleri güçlendir; "
                "testi zayıflatmak yasak."
            )
        kullanici.append("Unified diff üret ve JSON alanına yaz.")
        return [
            {"role": "system", "content": SISTEM_PROMPTU},
            {"role": "user", "content": "\n".join(kullanici)},
        ]

    def _cagir(self, mesajlar: list[dict[str, str]]) -> str:
        son_hata = ""
        for deneme in range(1, DENEME + 1):
            try:
                icerik = self._post(mesajlar)
                self._egress("ok")
                return icerik
            except AdapterError as e:
                self._egress(f"hata: {str(e)[:80]}")
                son_hata = str(e)
                if deneme < DENEME:
                    time.sleep(0.5 * deneme)
        raise AdapterError(son_hata)

    def _egress(self, sonuc: str) -> None:
        """Her dış çağrıyı denetim dosyasına yazar (GOVERNANCE §4)."""
        if not self.egress_log:
            return
        kayit = {
            "ts": round(time.time(), 3),
            "host": self.base_url,
            "model": self.model,
            "sonuc": sonuc[:120],
        }
        with self.egress_log.open("a", encoding="utf-8") as fh:
            fh.write(json.dumps(kayit, ensure_ascii=False) + "\n")

    def _post(self, mesajlar: list[dict[str, str]]) -> str:
        istek = urllib.request.Request(
            f"{self.base_url}/chat/completions",
            data=json.dumps(
                {
                    "model": self.model,
                    "messages": mesajlar,
                    "temperature": self.temperature,
                    "max_tokens": self.max_tokens,
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
        except urllib.error.HTTPError as e:
            raise AdapterError(f"HTTP {e.code}: {e.read()[:200]!r}")
        except (urllib.error.URLError, TimeoutError, json.JSONDecodeError) as e:
            raise AdapterError(f"bağlantı hatası: {e}")
        try:
            return veri["choices"][0]["message"]["content"]
        except (KeyError, IndexError, TypeError) as e:
            raise AdapterError(f"yanıt biçimi beklenmedik: {e}")


def _json_cikar(metin: str) -> dict[str, Any] | None:
    """Yanıttan ilk JSON nesnesini çıkarır (kod çiti toleranslı)."""
    if not metin:
        return None
    temiz = re.sub(r"^```(?:json)?|```$", "", metin.strip(), flags=re.M).strip()
    try:
        veri = json.loads(temiz)
        return veri if isinstance(veri, dict) else None
    except json.JSONDecodeError:
        pass
    eslesme = re.search(r"\{.*\}", temiz, re.S)
    if eslesme:
        try:
            veri = json.loads(eslesme.group(0))
            return veri if isinstance(veri, dict) else None
        except json.JSONDecodeError:
            return None
    return None
