#!/bin/bash
# ============================================================
# Cosmic — Baskı menüsünü güncelle  (ÇİFT TIKLA ÇALIŞTIR)
# data/menu.json'daki fiyat/ürünlerden menu-baski.pdf üretir.
# ============================================================

# Bu betiğin bulunduğu klasör (tools/) -> proje kökü onun bir üstü
DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT="$(dirname "$DIR")"
cd "$ROOT" || { echo "Proje klasörüne girilemedi."; exit 1; }

echo "══════════════════════════════════════════"
echo "  COSMIC — Baskı menüsü üretiliyor…"
echo "  Klasör: $ROOT"
echo "══════════════════════════════════════════"
echo

# python3'ü bul (Terminal'in PATH'i, Homebrew, sistem)
if command -v python3 >/dev/null 2>&1; then
  PY="$(command -v python3)"
elif [ -x /opt/homebrew/bin/python3 ]; then
  PY=/opt/homebrew/bin/python3
elif [ -x /usr/local/bin/python3 ]; then
  PY=/usr/local/bin/python3
elif [ -x /usr/bin/python3 ]; then
  PY=/usr/bin/python3
else
  echo "HATA: python3 bulunamadı."
  echo "  Kurmak için Terminal'e: xcode-select --install"
  echo
  echo "Kapatmak için Enter'a basın."
  read -r
  exit 1
fi

"$PY" tools/build_print_menu.py
STATUS=$?

echo
if [ "$STATUS" -eq 0 ] && [ -f "menu-baski.pdf" ]; then
  echo "✓ Bitti — çıktı: $ROOT/menu-baski.pdf"
  echo "  PDF açılıyor; Cmd+P ile A4 (kapı için A3) yazdırabilirsiniz."
  open "menu-baski.pdf" 2>/dev/null
else
  echo "✗ Bir sorun oluştu (kod $STATUS). Yukarıdaki mesajlara bakın."
fi

echo
echo "Bu pencereyi kapatabilirsiniz.  (Enter'a basınca kapanır)"
read -r
