# CLAUDE.md

Cosmic Coffee & More — kafe menüsü. **Tek veri kaynağı**, iki yüzey:

- **Dijital QR menü** — `index.html` + `css/style.css` + `js/app.js`; veriyi
  `data/menu.json`'dan `fetch` ile okur. Koyu "Engraved Cosmos" teması.
- **Baskı menüsü (el menüsü / kapıya asılan)** — `data/menu.json`'dan üretilen
  tek sayfa A4 PDF: `menu-baski.pdf`. Aynı temanın açık/fildişi baskı versiyonu.

## Tek veri kaynağı — `data/menu.json`

Kafe bilgisi + 11 kategori / 108 ürün (isim, fiyat, kalori, alerjen). Fiyat/ürün
değişikliği **yalnızca burada** yapılır; kod dokunması gerekmez.
Geçerli alerjenler: `sut, gluten, yumurta, sertkabuklu, soya, susam, sulfit`
(etiket/ikon karşılıkları JSON içindeki `allergenLegend` bölümünde).

## Baskı menüsünü üretme — `menu-baski.pdf`

`data/menu.json` değiştikten sonra yeniden üret:

```bash
python3 tools/build_print_menu.py            # menu-baski.pdf üretir (varsayılan)
python3 tools/build_print_menu.py --no-pdf   # PDF yerine düzenlenebilir HTML
```

Komut yazmadan (macOS): Finder'da `tools/update-menu-pdf.command` dosyasına **çift tıkla**.

**Nasıl çalışır:** `tools/build_print_menu.py` fontları (Cinzel + Jost) ve QR'ı
base64 gömülü, kendi kendine yeterli bir HTML'i **geçici** olarak üretir; sistemdeki
Chrome/Chromium'u headless çalıştırıp A4 PDF'e basar; geçici HTML'i siler. Repoda
yalnızca `menu-baski.pdf` kalır. (Chrome yoksa fallback olarak `menu-baski.html`
yazılır — `.gitignore`'da, commit'lenmez.)

**Baskı:** A4 (renkler PDF'e gömülü, ek ayar gerekmez). Kapı için yazdırma
penceresinde kağıt **A3** + Ölçek **"Sayfaya sığdır"**.

### Baskı düzeni — dikkat edilecekler (değişiklik yaparken)

- Çıktı **tek A4 sayfa** olmalı — sıkı kısıt (108 ürün + kalori + alerjen). Değişiklikten
  sonra doğrula: headless Chrome ile `--print-to-pdf` alıp PDF'in **sayfa sayısı = 1** mi bak.
- Satır sıkılığı `.item { line-height }` ile ayarlı (`tools/build_print_menu.py` içindeki
  CSS şablonu). **1.55** = tek sayfada kalan güvenli en ferah değer; 1.56 sınırda, 1.58
  taşırıyor. Ürün eklenirse bu değeri düşürmek gerekebilir.
- Her ürün satırı: isim (+ küçük alerjen ikonları) · kalori · fiyat (kırmızı). Çok uzun
  isimli + çok alerjenli birkaç üründe ikonlar alt satıra kayabilir (bilinen, kabul edilen).
- Açık/fildişi tema; zemin ve renkler `print-color-adjust: exact` ile basılır.
- Fontlar `assets/fonts/` içinden base64 gömülür (latin + latin-ext → Türkçe karakterler).
  Türkçe metinde `.upper()` sonra HTML-escape yapılmalı (aksi halde `&amp;`.upper() = `&AMP;` bozulur).

## Dijital menüyü yerelde çalıştırma

`fetch` kullandığı için `file://` ile açılmaz; yerel sunucu gerekir:

```bash
python3 -m http.server 8000   # sonra: http://localhost:8000
```
