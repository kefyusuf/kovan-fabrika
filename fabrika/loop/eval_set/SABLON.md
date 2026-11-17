# Eval Seti Şablonu — kendi hedef repon için dondurulmuş vaka seti nasıl kurulur

> Eval seti fabrikanın en değerli varlığıdır: **model değil, bu set tavanıdır.**
> Bu şablon, kendi repon için `eval_set/<repo>-v1.jsonl` dosyasını kurmanın
> kurallarıdır. Kural ihlali = set "yanar" = ölçüm değersizleşir.

---

## 1. Vaka şeması (JSONL — her satır bir vaka)

```json
{"modul": "sicaklik", "fonksiyon": "celsius_fahrenheit", "args": [0], "beklenen": 32.0, "tol": 1e-6, "etiket": "C0->F"}
{"modul": "sicaklik", "fonksiyon": "ortalama", "args": [[]], "beklenen": "ValueError", "etiket": "ort-bos-hata"}
```

| Alan | Zorunlu | Kural |
|---|---|---|
| `modul` | ✓ | Repo içindeki import edilebilir modül (`.py` dosyası adı) |
| `fonksiyon` | ✓ | Modüldeki fonksiyon adı |
| `args` | ✓ | Pozisyonel argüman **listesi** — tek liste argümanı `[liste]` olarak yazılır |
| `beklenen` | ✓ | Değer (tol ile karşılaştırılır) veya `"XxxError"` (istisna adı) |
| `tol` | — | Mutlak tolerans; varsayılan 1e-6 |
| `etiket` | ✓ | Kısa, benzersiz etiket — hata listelerinde bu görünür |

**Yaygın hata:** fonksiyon liste alıyorsa `args: [a, b, c]` yazmak — bu, argüman
açılımıdır. Liste argümanı için `args: [[a, b, c]]` yazın. (İlk setimizde tam
bu hata 7 tutarsızlık üretti ve skor 0,922'ye düştü — set düzeltildi.)

---

## 2. Golden değerler nereden gelir — dürüstlük kuralı

**Doğru:** mevcut, ÇALIŞAN referans davranıştan üret ("golden"). Set,
davranış **değişimini** yakalar; matematiksel doğruluğu kanıtlamaz.

**Yanlış:** kırık kodun çıktısından değer üretmek, veya eval setini geçmek
için üretime bakıp geriye doğru yazmak. İkincisi daireselliğe gider.

Setin kendisi de bir kanıt üretmelidir: **seti yazdıktan sonra bozuk bir
diff enjekte et** (`mutasyon.py` veya elle) ve skorun düştüğünü gör —
düşmüyorsa set ölüdür.

---

## 3. Boy ve dağılım disiplini

| Kural | Değer |
|---|---|
| Minimum vaka | 50 (PRD FR ölçütü; ilk setimiz 90) |
| Sınır vakalar | ≥ %20 (sıfır, negatif, boş liste, maksimum) |
| Hata vakaları | ≥ %10 (`"ValueError"` tarzı istisna beklenenleri) |
| Etiket dağılımı | Tek etiket toplamın %60'ını aşmamalı |
| Dondurma | Dosya adında sürüm: `sicaklik-v1.jsonl`; değişiklik = yeni sürüm dosyası |

**Dondurulmuş setin yaşamı:** eklemek serbest, **çıkarmak yasak**, beklentiyi
değiştirmek yasak. Yeni davranış geldiğinde **v2** dosyası açılır; v1
`retired/` altına taşınır ve "neden emekli oldu" notuyla kalır.

---

## 4. Koşum

```bash
cd fabrika/loop
python eval_kos.py --repo /path/to/kendi-repon --set eval_set/senin-v1.jsonl
# diff'li (modelin yamasını ölçmek için):
python eval_kos.py --repo ... --set ... --diff-dosya yama.diff
```

`kovan.py run --adapter http --eval-set eval_set/senin-v1.jsonl ...`
verilince **eval kapısı bloklayıcı** olur: skor < 0,90 → patch reddedilir.

---

## 5. Anti-patternler (seti öldüren alışkanlıklar)

1. **Seti geçen kodu yazdıktan sonra seti gevşetmek** — ölçümü iyileştirme
   yasağı (anayasa m.2).
2. **Aynı seti üreten ajana göstermek** — dairesellik; holdout disiplini
   ihlali.
3. **Tek etiketle şişirmek** — dağılım yoksa regresyon değildir.
4. **Sürüm dosyası açmadan seti düzenlemek** — eski skorlarla kıyas artık
   yalan olur.
5. **Skoru tek başarı metriği yapmak** — mutasyon skoru (`mutasyon.py`) ve
   gerçek test koşumu ile birlikte oku.
