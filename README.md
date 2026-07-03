# Cosmic Coffee & More · QR Menü

Cosmic Coffee & More için tasarlanmış, koyu ve premium bir "Engraved Cosmos" temalı dijital QR menü.
Tüm menü verisi **statik bir JSON dosyasından** okunur; ileride tek satır değişiklikle dinamik (API) hale getirilebilir.

Kaynak menü: <https://menum.co/cosmiccoffeemore>

---

## İçerik

| Yol | Açıklama |
|-----|----------|
| `index.html` | Tek sayfa menü iskeleti + SVG ikon seti |
| `css/style.css` | Tasarım sistemi (koyu tema, Cinzel + Jost, meander motifi) |
| `js/app.js` | `data/menu.json`'u okur; hero, kategoriler, kartlar, arama, scroll-spy ve lightbox'ı oluşturur |
| `data/menu.json` | **Tek veri kaynağı** — kafe bilgisi, 11 kategori, 108 ürün + alerjen & kalori |
| `assets/logo.jpg` | Kafe logosu |
| `assets/products/` | 102 ürün fotoğrafı, **WebP** (lightbox tam boy, ≤1400px) |
| `assets/products/thumbs/` | ≤520px **WebP** thumbnail'lar (mobilde hızlı, lazy-load; lightbox orijinali kullanır) |
| `assets/fonts/` | Self-host edilmiş Cinzel + Jost (woff2, latin+latin-ext) + `fonts.css` — Google Fonts bağımlılığı yok |
| `_headers` | Netlify cache başlıkları (font/görsel uzun cache; menu.json/html anında güncellenir) |

**11 kategori / 108 ürün:** Tatlılar · Espresso Bazlı İçecekler · Sıcak Çikolata & Salep · Yeni Nesil Kahveler · Türk Kahvesi · Filtre Kahve · Çay & Bitki Çayları · Soğuk Kahveler · Moctails · Vitamin · Soğuk İçecekler.

---

## Yerelde çalıştırma

Sayfa `fetch` ile JSON okuduğu için dosyayı çift tıklayıp `file://` ile açmak **çalışmaz** (tarayıcı güvenlik kuralı). Basit bir yerel sunucu ile açın:

```bash
cd /Users/titiz/Desktop/cosmic
python3 -m http.server 8000
```

Sonra tarayıcıdan: <http://localhost:8000>

> Node kullananlar için alternatif: `npx serve` veya `npx http-server`.

---

## Menüyü güncelleme

Tüm içerik `data/menu.json` içindedir. Fiyat, isim, açıklama değiştirmek için ilgili ürünü düzenlemeniz yeterli — kod dokunması gerekmez.

Bir ürün örneği:

```json
{
  "id": "101084",
  "name": "Latte",
  "description": "",
  "price": 180.0,
  "priceFormatted": "180,00 ₺",
  "image": "assets/products/101084.jpg",
  "calories": 150,
  "allergens": ["sut"]
}
```

- **`allergens`** geçerli değerler: `sut`, `gluten`, `yumurta`, `sertkabuklu`, `soya`, `susam`, `sulfit`
  (etiket/ikon karşılıkları `menu.json` içindeki `allergenLegend` bölümünde tanımlıdır).
- **`image`** `null` olursa kart, şık bir ✦ yer tutucu gösterir.
- Yeni ürün eklemek: ilgili kategorinin `items` dizisine yeni bir nesne ekleyin.
- Yeni kategori eklemek: `categories` dizisine `slug`, `name`, `icon`, `items` içeren yeni bir nesne ekleyin.

### Alerjen & kalori değerleri hakkında

Kalori ve alerjen bilgileri, her ürünün **tipine ve standart porsiyonuna** göre belirlenmiş **ortalama/tahmini** değerlerdir (ör. Latte ~150 kcal + süt; Americano ~10 kcal, alerjensiz). Rastgele uydurulmamıştır; standart tarif/besin referanslarına dayanır. Sayfada da bu not açıkça belirtilir. Kesin değerler hazırlanışa ve porsiyona göre değişebilir.

---

## Dinamik hale getirme (ileride)

Arayüz zaten veriyi tek bir yerden — `data/menu.json` — okur. Dinamikleştirmek için `js/app.js` içindeki:

```js
const DATA_URL = 'data/menu.json';
```

satırını, **aynı JSON şemasını** dönen bir API adresiyle değiştirmeniz yeterli:

```js
const DATA_URL = 'https://api.cosmiccoffee.example/menu';
```

Arayüzde başka değişiklik gerekmez. Panelden fiyat/ürün güncellemesi, stok durumu, çoklu dil vb. bu aşamada eklenebilir.

---

## Yayınlama & QR

1. Klasörü herhangi bir statik barındırmaya yükleyin (Netlify, Vercel, GitHub Pages, cPanel/hosting, vb.).
2. Ortaya çıkan URL'yi (ör. `https://menu.cosmiccoffee.com`) bir QR kod üretecine verin.
3. QR'ı masalara koyun — müşteriler telefondan menüye ulaşır.

Sayfa mobil öncelikli, responsive; `prefers-reduced-motion` ve klavye erişilebilirliğine saygılıdır.

---

## Tasarım notları

- **Tema:** "Engraved Cosmos" — logodaki kabartma medalyon, gümüş gravür tipografi, tek imza kırmızı (XXX) vurgu, Yunan **meander** deseni.
- **Tipografi:** Cinzel (Roma kitabe serifi, başlıklar) + Jost (geometrik sans, gövde) — Google Fonts.
- **Renkler:** `--void #0A0A0C`, `--platinum #DCDCE1`, `--ember #D11A2A`.
