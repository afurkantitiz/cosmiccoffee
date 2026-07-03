#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
Cosmic Coffee & More — tek sayfa baskı menüsü üreticisi.

data/menu.json'u okur; fontları (Cinzel + Jost) ve QR kodunu base64 gömerek
kendi kendine yeterli bir HTML oluşturur, ardından sistemdeki Chrome/Chromium'u
headless çalıştırıp baskıya hazır menu-baski.pdf (A4 dikey, tek sayfa) üretir.
Ara HTML geçici bir dosyada tutulur ve PDF üretilince silinir — repoda yalnızca
PDF kalır. (Chrome bulunamazsa fallback olarak menu-baski.html yazılır.)

"Engraved Cosmos"un açık/fildişi baskı versiyonu. Aynı PDF A3'e basılınca
kapı için büyür.

Kullanım:
    python3 tools/build_print_menu.py            # menu-baski.pdf üretir (varsayılan)
    python3 tools/build_print_menu.py --no-pdf   # PDF yerine menu-baski.html üretir

Menü/fiyat değiştikten sonra (data/menu.json) tekrar çalıştırın.
"""
import base64
import html
import json
import os
import shutil
import subprocess
import sys
import tempfile
from urllib.request import pathname2url

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATA = os.path.join(ROOT, "data", "menu.json")
FONTS = os.path.join(ROOT, "assets", "fonts")
QR_PNG = os.path.join(ROOT, "qr", "qr-cosmiccoffee-plain.png")
OUT = os.path.join(ROOT, "menu-baski.html")
OUT_PDF = os.path.join(ROOT, "menu-baski.pdf")

# Google-fonts standart latin / latin-ext unicode aralıkları (Türkçe için ikisi de gerekli)
RANGE_LATIN = ("U+0000-00FF,U+0131,U+0152-0153,U+02BB-02BC,U+02C6,U+02DA,U+02DC,"
               "U+0304,U+0308,U+0329,U+2000-206F,U+20AC,U+2122,U+2191,U+2193,"
               "U+2212,U+2215,U+FEFF,U+FFFD")
RANGE_EXT = ("U+0100-02BA,U+02BD-02C5,U+02C7-02CC,U+02CE-02D7,U+02DD-02FF,U+0304,"
             "U+0308,U+0329,U+1D00-1DBF,U+1E00-1E9F,U+1EF2-1EFF,U+2020,U+20A0-20AB,"
             "U+20AD-20C0,U+2113,U+2C60-2C7F,U+A720-A7FF")

# (aile, ağırlık, dosya-adı-kökü) -> gömülecek font yüzleri
FONT_FACES = [
    ("Cinzel", 700, "Cinzel-700"),
    ("Jost", 400, "Jost-400"),
    ("Jost", 500, "Jost-500"),
    ("Jost", 300, "Jost-300"),
]


def b64_file(path):
    with open(path, "rb") as f:
        return base64.b64encode(f.read()).decode("ascii")


def font_face_css():
    out = []
    for family, weight, stem in FONT_FACES:
        for subset, rng in (("latin", RANGE_LATIN), ("latin-ext", RANGE_EXT)):
            p = os.path.join(FONTS, f"{stem}-{subset}.woff2")
            if not os.path.exists(p):
                continue
            data = b64_file(p)
            out.append(
                "@font-face{"
                f"font-family:'{family}';font-style:normal;font-weight:{weight};"
                "font-display:swap;"
                f"src:url(data:font/woff2;base64,{data}) format('woff2');"
                f"unicode-range:{rng};"
                "}"
            )
    return "".join(out)


def meander_data_uri(color="#B6AC93"):
    """Tek kare-spiral (Yunan meander) birimi, yatay tekrarlanır."""
    svg = (
        "<svg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 26 16' width='26' height='16'>"
        f"<path d='M1 15V1H25V15H9V7H17V11' fill='none' stroke='{color}' "
        "stroke-width='1.5' stroke-linecap='square' stroke-linejoin='miter'/></svg>"
    )
    return "data:image/svg+xml;utf8," + svg.replace("#", "%23").replace("'", "%22")


def fmt_price(item):
    price = item.get("price")
    if price is None:
        return item.get("priceFormatted", "")
    if float(price) == int(price):
        return f"{int(price)} ₺"  # ince boşluk + ₺
    s = f"{price:,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")
    return f"{s} ₺"


def esc(s):
    return html.escape(s or "")


def find_chrome():
    """PATH'te veya standart konumlarda Chrome/Chromium/Edge/Brave arar."""
    for name in ("google-chrome", "google-chrome-stable", "chromium",
                 "chromium-browser", "microsoft-edge", "brave-browser"):
        p = shutil.which(name)
        if p:
            return p
    candidates = [
        "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
        "/Applications/Google Chrome Canary.app/Contents/MacOS/Google Chrome Canary",
        "/Applications/Chromium.app/Contents/MacOS/Chromium",
        "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
        "/Applications/Brave Browser.app/Contents/MacOS/Brave Browser",
        r"C:\Program Files\Google\Chrome\Application\chrome.exe",
        r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
    ]
    for p in candidates:
        if os.path.exists(p):
            return p
    return None


def render_pdf(doc, chrome, total, catn):
    """HTML'i geçici dosyaya yazıp headless Chrome ile A4 PDF üretir; geçici dosyayı siler."""
    fd, tmp = tempfile.mkstemp(suffix=".html", prefix="cosmic-menu-")
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            f.write(doc)
        url = "file://" + pathname2url(tmp)
        cmd = [
            chrome, "--headless=new", "--disable-gpu", "--no-sandbox",
            "--no-pdf-header-footer", "--virtual-time-budget=5000",
            f"--print-to-pdf={OUT_PDF}", url,
        ]
        subprocess.run(cmd, check=True, timeout=120,
                       stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    except Exception as e:  # noqa: BLE001
        print(f"  ! PDF üretilemedi ({type(e).__name__}).")
        return False
    finally:
        try:
            os.remove(tmp)
        except OSError:
            pass
    if not os.path.exists(OUT_PDF):
        return False
    kb = os.path.getsize(OUT_PDF) / 1024
    print(f"OK -> {OUT_PDF}  ({kb:.0f} KB, {total} ürün / {catn} kategori)")
    return True


def build(make_pdf=True):
    with open(DATA, encoding="utf-8") as f:
        d = json.load(f)

    r = d["restaurant"]
    legend = d.get("allergenLegend", {})
    note = d.get("nutritionNote", "")
    cats = d.get("categories", [])
    total = sum(len(c.get("items", [])) for c in cats)

    # ---- gövde: kategoriler + ürünler ----
    body = []
    for c in cats:
        items = c.get("items", [])
        if not items:
            continue
        icon = c.get("icon", "")
        name = esc(c.get("name", ""))
        body.append('<section class="cat">')
        body.append(
            f'<h2 class="cat-h"><span class="cat-ico">{icon}</span>'
            f'<span class="cat-nm">{name}</span>'
            f'<span class="cat-ct">{len(items)}</span></h2>'
        )
        for it in items:
            nm = esc(it.get("name", ""))
            algs = it.get("allergens", []) or []
            alg_html = ""
            if algs:
                icons = "".join(
                    f'<span class="alg" title="{esc(legend.get(a,{}).get("label",a))}">'
                    f'{legend.get(a,{}).get("icon","")}</span>'
                    for a in algs
                )
                alg_html = f'<span class="algs">{icons}</span>'
            cal = it.get("calories")
            cal_html = ""
            if cal:
                cal_html = f'<span class="kcal">{int(cal)}<i>kcal</i></span>'
            price = fmt_price(it)
            body.append(
                '<div class="item">'
                f'<span class="nm">{nm}{alg_html}</span>'
                '<span class="lead"></span>'
                f'{cal_html}'
                f'<span class="price">{price}</span>'
                "</div>"
            )
        body.append("</section>")
    body_html = "".join(body)

    # ---- alerjen efsanesi ----
    legend_items = "".join(
        f'<span class="leg"><span class="alg">{v.get("icon","")}</span>{esc(v.get("label",""))}</span>'
        for v in legend.values()
    )

    # ---- footer bilgileri ----
    qr = b64_file(QR_PNG)
    ig = esc(r.get("instagram", ""))
    contact_rows = []
    if r.get("address"):
        contact_rows.append(f'<div class="crow"><b>Adres</b>{esc(r["address"])}</div>')
    if r.get("hours"):
        contact_rows.append(f'<div class="crow"><b>Saatler</b>{esc(r["hours"])}</div>')
    if r.get("phone"):
        contact_rows.append(f'<div class="crow"><b>Telefon</b>{esc(r["phone"])}</div>')
    if ig:
        contact_rows.append(f'<div class="crow"><b>Instagram</b>@{ig}</div>')
    contact_html = "".join(contact_rows)

    fonts = font_face_css()
    meander = meander_data_uri()
    xxx = ("M3 3 11 13M11 3 3 13M13 3 21 13M21 3 13 13M23 3 31 13M31 3 23 13")

    name_full = esc(r.get("nameFull", "Cosmic Coffee & More"))
    tagline = esc(r.get("tagline", ""))
    # önce upper() sonra escape — aksi halde "&amp;".upper()="&AMP;" bozulur
    brand_sub = esc(r.get("slogan", "Coffee & More").upper())

    doc = TEMPLATE
    doc = doc.replace("/*__FONTS__*/", fonts)
    doc = doc.replace("__MEANDER__", meander)
    doc = doc.replace("__BRAND_FULL__", "COSMIC")
    doc = doc.replace("__BRAND_SUB__", brand_sub)
    doc = doc.replace("__TAGLINE__", tagline)
    doc = doc.replace("__NAME_FULL__", name_full)
    doc = doc.replace("__XXX__", xxx)
    doc = doc.replace("<!--BODY-->", body_html)
    doc = doc.replace("<!--LEGEND-->", legend_items)
    doc = doc.replace("<!--CONTACT-->", contact_html)
    doc = doc.replace("__QR__", qr)
    doc = doc.replace("__NOTE__", esc(note))
    doc = doc.replace("__COUNT__", str(total))
    doc = doc.replace("__CATCOUNT__", str(len([c for c in cats if c.get("items")])))

    catn = len([c for c in cats if c.get("items")])

    def write_html():
        with open(OUT, "w", encoding="utf-8") as f:
            f.write(doc)
        kb = os.path.getsize(OUT) / 1024
        print(f"OK -> {OUT}  ({kb:.0f} KB, {total} ürün / {catn} kategori)")

    # Varsayılan: yalnızca PDF üret (HTML ara adımdır, geçici dosyada tutulur).
    if not make_pdf:
        write_html()
        return

    chrome = find_chrome()
    if not chrome:
        write_html()
        print("  ! Chrome/Chromium bulunamadı — PDF atlandı; fallback olarak HTML yazıldı.")
        print("    menu-baski.html'i tarayıcıda açıp Cmd/Ctrl+P > 'PDF olarak kaydet' ile alın.")
        return

    if render_pdf(doc, chrome, total, catn):
        # PDF üretildi; repoda ara HTML kalmasın — eski kalıntı varsa temizle.
        if os.path.exists(OUT):
            os.remove(OUT)
    else:
        write_html()
        print("    Fallback olarak HTML yazıldı; tarayıcıdan Cmd/Ctrl+P ile PDF alabilirsiniz.")


TEMPLATE = r"""<!doctype html>
<html lang="tr">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Cosmic Coffee & More — Menü</title>
<style>
/*__FONTS__*/

:root{
  --paper:#F7F3EA; --paper-2:#F0EADB; --band:#ECE4D2;
  --ink:#1B1B20; --ink-2:#3C3A34; --muted:#8C8677; --faint:#A8A290;
  --rule:#CFC6B0; --rule-2:#DED6C2; --ember:#BC1523;
  --display:'Cinzel',Georgia,'Times New Roman',serif;
  --body:'Jost','Segoe UI',system-ui,sans-serif;
}
*{box-sizing:border-box;margin:0;padding:0;}
html,body{background:#6b6b70;}
body{
  font-family:var(--body); color:var(--ink);
  -webkit-font-smoothing:antialiased; text-rendering:optimizeLegibility;
  -webkit-print-color-adjust:exact; print-color-adjust:exact;
}

/* A4 sayfa */
@page{ size:A4 portrait; margin:6mm; }

.sheet{
  width:210mm; min-height:297mm;
  margin:18px auto; padding:7mm 8mm 6mm;
  background:var(--paper);
  color:var(--ink);
  display:flex; flex-direction:column;
  box-shadow:0 10px 40px rgba(0,0,0,.4);
  position:relative;
}
.sheet::after{ /* ince iç çerçeve */
  content:""; position:absolute; inset:4.5mm;
  border:1px solid var(--rule); pointer-events:none;
}

/* ---------- BAŞLIK ---------- */
.head{ text-align:center; position:relative; z-index:1; padding:1mm 2mm 0; }
.mband{
  height:11px; width:100%;
  background:url("__MEANDER__") repeat-x center/auto 11px;
  opacity:.75;
}
.mband--b{ margin-top:3mm; }
.brand{
  font-family:var(--display); font-weight:700;
  font-size:29pt; line-height:1; letter-spacing:.26em;
  padding-left:.26em; margin:2.2mm 0 0; color:var(--ink);
}
.brand-sub{
  font-family:var(--display); font-weight:700;
  font-size:9pt; letter-spacing:.42em; padding-left:.42em;
  color:var(--ember); margin:1.6mm 0 0;
}
.tag{
  font-size:8pt; letter-spacing:.24em; text-transform:uppercase;
  color:var(--muted); margin:1.6mm 0 0; font-weight:400;
}
.xxx{ display:block; width:34px; height:15px; margin:2mm auto 0; color:var(--ember); }

/* ---------- GÖVDE (kategoriler) ---------- */
.menu{
  flex:1 1 auto;
  column-count:3; column-gap:6mm;
  column-rule:1px solid var(--rule-2);
  margin-top:2.5mm; padding-top:0.5mm;
}
.cat{ break-inside:auto; margin:0 0 2.2mm; }
.cat-h{
  display:flex; align-items:baseline; gap:5px;
  break-after:avoid; break-inside:avoid;
  font-family:var(--display); font-weight:700;
  font-size:10pt; letter-spacing:.06em; color:var(--ink);
  padding-bottom:1mm; margin-bottom:1.4mm;
  border-bottom:1.4px solid var(--ember);
}
.cat-ico{ font-size:9pt; line-height:1; filter:saturate(.85); flex:none; }
.cat-nm{ flex:1 1 auto; }
.cat-ct{
  font-family:var(--body); font-weight:400; font-size:6.5pt;
  letter-spacing:.05em; color:var(--muted);
  border:1px solid var(--rule); border-radius:99px;
  padding:.4mm 1.4mm; align-self:center;
}

.item{
  display:flex; align-items:baseline; gap:0;
  font-size:8pt; line-height:1.55;
  break-inside:avoid;
}
.nm{ font-weight:500; color:var(--ink); }
.algs{ margin-left:3px; white-space:nowrap; }
.alg{ font-size:6.6pt; line-height:1; opacity:.9; margin-left:1px; }
.lead{
  flex:1 1 auto; align-self:flex-end;
  border-bottom:1px dotted var(--rule);
  margin:0 4px 2.6px; min-width:8px; height:0;
}
.kcal{
  flex:none; color:var(--muted); font-weight:300;
  font-size:6.6pt; letter-spacing:.02em; margin-right:5px; white-space:nowrap;
}
.kcal i{ font-style:normal; font-size:5.2pt; margin-left:1px; letter-spacing:.02em; }
.price{
  flex:none; color:var(--ember); font-weight:500;
  font-size:8pt; letter-spacing:.01em; white-space:nowrap;
  font-variant-numeric:tabular-nums;
}

/* ---------- FOOTER ---------- */
.foot{ margin-top:2mm; position:relative; z-index:1; }
.foot-mb{
  height:9px; width:100%;
  background:url("__MEANDER__") repeat-x center/auto 9px;
  opacity:.6; margin-bottom:2.2mm;
}
.foot-grid{
  display:grid; grid-template-columns:auto 1fr auto;
  gap:6mm; align-items:center;
}
.qr-box{ display:flex; align-items:center; gap:3mm; }
.qr-box img{
  width:23mm; height:23mm; display:block;
  border:1px solid var(--rule); padding:1.4mm; background:#fff;
}
.qr-cap{ max-width:34mm; }
.qr-cap b{
  display:block; font-family:var(--display); font-weight:700;
  font-size:8pt; letter-spacing:.08em; color:var(--ink); margin-bottom:1mm;
}
.qr-cap span{ font-size:7pt; line-height:1.4; color:var(--muted); }

.contact{ display:flex; flex-direction:column; gap:1.1mm; }
.crow{ font-size:8pt; line-height:1.3; color:var(--ink-2); }
.crow b{
  display:inline-block; min-width:17mm; color:var(--muted);
  font-weight:500; font-size:6.6pt; letter-spacing:.09em; text-transform:uppercase;
}
.foot-name{
  text-align:right;
  font-family:var(--display); font-weight:700;
  font-size:11pt; letter-spacing:.14em; color:var(--ink);
}
.foot-name span{
  display:block; font-family:var(--body); font-weight:400;
  font-size:6.8pt; letter-spacing:.2em; color:var(--ember);
  text-transform:uppercase; margin-top:1mm;
}

.legend{
  margin-top:2.2mm; padding-top:1.8mm; border-top:1px solid var(--rule-2);
  display:flex; flex-wrap:wrap; gap:1.6mm 4mm; justify-content:center;
}
.leg{ font-size:6.8pt; color:var(--ink-2); letter-spacing:.02em; display:inline-flex; align-items:center; gap:2px; }
.leg .alg{ font-size:7.4pt; margin:0; }
.note{
  margin-top:1.4mm; text-align:center;
  font-size:6.2pt; line-height:1.4; color:var(--muted); font-weight:300;
  max-width:170mm; margin-left:auto; margin-right:auto;
}

/* ---------- BASKI ---------- */
@media print{
  html,body{ background:#fff; }
  .sheet{
    width:auto; min-height:auto; margin:0; padding:3mm 3.5mm;
    box-shadow:none;
  }
  .sheet::after{ inset:1mm; }
}
</style>
</head>
<body>
<div class="sheet">

  <header class="head">
    <div class="mband"></div>
    <h1 class="brand">__BRAND_FULL__</h1>
    <div class="brand-sub">__BRAND_SUB__</div>
    <div class="mband mband--b"></div>
  </header>

  <main class="menu"><!--BODY--></main>

  <footer class="foot">
    <div class="foot-mb"></div>
    <div class="foot-grid">
      <div class="qr-box">
        <img src="data:image/png;base64,__QR__" alt="QR — dijital menü">
        <div class="qr-cap">
          <b>Dijital Menü</b>
          <span>Fotoğraflar, kalori &amp; alerjen detayları için telefonla okutun.</span>
        </div>
      </div>
      <div class="contact"><!--CONTACT--></div>
      <div class="foot-name">__BRAND_FULL__<span>__BRAND_SUB__</span></div>
    </div>
    <div class="legend"><!--LEGEND--></div>
    <div class="note">__NOTE__</div>
  </footer>

</div>
</body>
</html>
"""


if __name__ == "__main__":
    build(make_pdf="--no-pdf" not in sys.argv)
