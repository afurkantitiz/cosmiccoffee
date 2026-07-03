/* ============================================================
   COSMIC — Coffee & More · QR Menü
   Reads data/menu.json (static now — swap the fetch URL for an
   API later to go dynamic) and renders the whole page from it.
   ============================================================ */
(() => {
  'use strict';

  const DATA_URL = 'data/menu.json';

  /* ---------- tiny DOM helpers ---------- */
  const el = (tag, cls, html) => {
    const n = document.createElement(tag);
    if (cls) n.className = cls;
    if (html != null) n.innerHTML = html;
    return n;
  };
  const svgUse = (id) => `<svg width="16" height="16" aria-hidden="true"><use href="#${id}"/></svg>`;
  const esc = (s) => String(s == null ? '' : s)
    .replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;')
    .replace(/"/g, '&quot;');

  // Turkish-aware search normalisation (diacritic-insensitive)
  const norm = (s) => String(s || '')
    .toLocaleLowerCase('tr')
    .replace(/ı/g, 'i').replace(/İ/g, 'i')
    .normalize('NFD').replace(/[̀-ͯ]/g, '');

  const thumbOf = (img) => img ? img.replace('assets/products/', 'assets/products/thumbs/') : null;

  /* ---------- state ---------- */
  let MENU = null;
  const nodesByCat = {};   // slug -> section element
  const itemNodes = [];    // { node, hay(name+desc), catSlug }

  /* ---------- boot ---------- */
  fetch(DATA_URL)
    .then((r) => { if (!r.ok) throw new Error(r.status); return r.json(); })
    .then((data) => { MENU = data; render(data); })
    .catch((err) => showLoadError(err));

  /* ============================================================
     RENDER
     ============================================================ */
  function render(data) {
    renderHero(data.restaurant);
    renderRail(data.categories);
    renderMenu(data);
    renderFooter(data.restaurant);
    wireSearch();
    wireScrollSpy(data.categories);
    wireReveal();
    wireLightbox();
  }

  function renderHero(r) {
    const hero = document.getElementById('hero');
    hero.innerHTML = `
      <img class="hero__logo" src="${esc(r.logo)}" alt="${esc(r.nameFull)} logosu" width="190" height="190" />
      <h1 class="hero__wordmark engraved">${esc(r.name.toUpperCase())}</h1>
      <p class="hero__sub">${esc(r.slogan)}</p>
      <p class="hero__tag">${esc(r.tagline)}</p>
      <div class="divider" aria-hidden="true">
        <span class="divider__line"></span>
        <svg class="key"><use href="#ico-key"/></svg>
        <svg class="mark"><use href="#ico-xxx"/></svg>
        <svg class="key" style="transform:scaleX(-1)"><use href="#ico-key"/></svg>
        <span class="divider__line divider__line--r"></span>
      </div>
      <div class="hero__meta">
        <span class="chip">${svgUse('ico-pin')} ${esc(shortAddr(r.address))}</span>
        <span class="chip">${svgUse('ico-clock')} ${esc(r.hours)}</span>
        <a class="chip" href="${esc(r.instagramUrl)}" target="_blank" rel="noopener">${svgUse('ico-ig')} @${esc(r.instagram)}</a>
      </div>`;
  }

  function shortAddr(addr) {
    // "... Bafra, Samsun" -> "Bafra · Samsun"
    const m = addr.match(/([\wğüşıöçİĞÜŞÖÇ.]+)\s*,\s*([\wğüşıöçİĞÜŞÖÇ.]+)\s*$/i);
    return m ? `${m[1]} · ${m[2]}` : addr;
  }

  function renderRail(cats) {
    const rail = document.getElementById('rail');
    rail.innerHTML = '';
    cats.forEach((c, i) => {
      const btn = el('button', 'rail__btn' + (i === 0 ? ' is-active' : ''),
        `<span class="ic">${esc(c.icon)}</span>${esc(c.name)}`);
      btn.type = 'button';
      btn.dataset.target = c.slug;
      btn.setAttribute('role', 'tab');
      btn.addEventListener('click', () => {
        const sec = nodesByCat[c.slug];
        if (sec) sec.scrollIntoView({ behavior: 'smooth', block: 'start' });
      });
      rail.appendChild(btn);
    });
  }

  function renderMenu(data) {
    const main = document.getElementById('menu');
    main.innerHTML = '';
    const legend = data.allergenLegend;

    data.categories.forEach((cat) => {
      const sec = el('section', 'cat');
      sec.id = 'cat-' + cat.slug;
      sec.dataset.slug = cat.slug;

      const head = el('div', 'cat__head reveal', `
        <span class="cat__icon" aria-hidden="true">${esc(cat.icon)}</span>
        <h2 class="cat__title engraved">${esc(cat.name)}</h2>
        ${cat.subtitle ? `<p class="cat__subtitle">${esc(cat.subtitle)}</p>` : ''}`);
      sec.appendChild(head);

      const grid = el('div', 'grid');
      cat.items.forEach((item) => {
        const card = buildCard(item, legend);
        grid.appendChild(card);
        itemNodes.push({
          node: card,
          hay: norm(item.name + ' ' + (item.description || '')),
          catSlug: cat.slug,
        });
      });
      sec.appendChild(grid);

      nodesByCat[cat.slug] = sec;
      main.appendChild(sec);
    });

    // allergen legend + disclaimer
    main.appendChild(buildLegend(data));
  }

  function buildCard(item, legend) {
    const card = el('article', 'card reveal');

    // thumbnail
    const thumb = thumbOf(item.image);
    if (thumb) {
      const t = el('button', 'card__thumb');
      t.type = 'button';
      t.setAttribute('aria-label', item.name + ' görselini büyüt');
      t.dataset.full = item.image;
      t.dataset.name = item.name;
      t.dataset.price = item.priceFormatted;
      t.innerHTML = `<img loading="lazy" decoding="async" src="${esc(thumb)}" alt="${esc(item.name)}" />`;
      card.appendChild(t);
    } else {
      card.appendChild(el('div', 'card__thumb card__thumb--empty', '&#10022;'));
    }

    // body
    const body = el('div', 'card__body');
    body.innerHTML = `
      <div class="card__topline">
        <h3 class="card__name">${esc(item.name)}</h3>
        <span class="card__price">${esc(item.priceFormatted)}</span>
      </div>
      ${item.description ? `<p class="card__desc">${esc(item.description)}</p>` : ''}
      <div class="card__foot">
        ${kcalHtml(item.calories)}
        ${allergensHtml(item.allergens, legend)}
      </div>`;
    card.appendChild(body);
    return card;
  }

  function kcalHtml(cal) {
    if (cal == null) return '';
    return `<span class="kcal" title="Ortalama enerji değeri"><span class="flame">&#9832;</span> <b>${cal}</b> kcal</span>`;
  }

  function allergensHtml(list, legend) {
    if (!list || !list.length) return '';
    const chips = list.map((k) => {
      const a = legend[k];
      if (!a) return '';
      return `<span class="aller" title="${esc(a.label)}" aria-label="${esc(a.label)}">${esc(a.icon)}</span>`;
    }).join('');
    return `<span class="allergens" role="group" aria-label="Alerjenler">${chips}</span>`;
  }

  function buildLegend(data) {
    const box = el('section', 'legend reveal');
    const items = Object.entries(data.allergenLegend).map(([, a]) =>
      `<div class="legend__item"><span class="aller">${esc(a.icon)}</span>${esc(a.label)}</div>`).join('');
    box.innerHTML = `
      <h3 class="legend__title">Alerjen Rehberi</h3>
      <div class="legend__grid">${items}</div>
      <p class="legend__note">${esc(data.nutritionNote)}</p>`;
    return box;
  }

  function renderFooter(r) {
    const foot = document.getElementById('foot');
    foot.innerHTML = `
      <div class="meander-band" aria-hidden="true"></div>
      <p class="foot__name engraved">${esc(r.name.toUpperCase())}</p>
      <p class="foot__tag">${esc(r.slogan)} — ${esc(r.tagline)}</p>
      <div class="foot__links">
        <a class="foot__btn foot__btn--wa" href="https://wa.me/${esc(r.whatsapp)}" target="_blank" rel="noopener">
          ${svgUse('ico-wa')} WhatsApp</a>
        <a class="foot__btn foot__btn--ig" href="${esc(r.instagramUrl)}" target="_blank" rel="noopener">
          ${svgUse('ico-ig')} Instagram</a>
        <a class="foot__btn" href="${esc(r.mapsUrl)}" target="_blank" rel="noopener">
          ${svgUse('ico-map')} Yol Tarifi</a>
      </div>
      <p class="foot__addr">
        ${svgUse('ico-pin')}
        <a href="${esc(r.mapsUrl)}" target="_blank" rel="noopener">${esc(r.address)}</a>
      </p>
      <p class="foot__addr">${svgUse('ico-clock')} Her gün ${esc(r.hours)}</p>
      <p class="foot__credit">${esc(r.nameFull)} · Dijital Menü</p>`;

    // paint the meander band (silver, tiling square-key)
    const band = foot.querySelector('.meander-band');
    const key = "data:image/svg+xml;utf8," + encodeURIComponent(
      "<svg xmlns='http://www.w3.org/2000/svg' width='16' height='12'><path d='M0 6V1H8V11H16V6' fill='none' stroke='%23B7B7C0' stroke-width='1.4'/></svg>");
    band.style.backgroundImage = `url("${key}")`;
    band.style.backgroundRepeat = 'repeat-x';
    band.style.backgroundPosition = 'center';
  }

  /* ============================================================
     SEARCH
     ============================================================ */
  function wireSearch() {
    const input = document.getElementById('search');
    const main = document.getElementById('menu');
    let emptyState = null;

    const apply = () => {
      const q = norm(input.value.trim());
      const perCat = {};
      let total = 0;

      itemNodes.forEach(({ node, hay, catSlug }) => {
        const hit = !q || hay.includes(q);
        node.style.display = hit ? '' : 'none';
        if (hit) { perCat[catSlug] = (perCat[catSlug] || 0) + 1; total++; }
      });

      // hide categories with no visible items
      Object.entries(nodesByCat).forEach(([slug, sec]) => {
        sec.style.display = (!q || perCat[slug]) ? '' : 'none';
      });
      // legend visible only when not searching
      const legend = main.querySelector('.legend');
      if (legend) legend.style.display = q ? 'none' : '';

      // empty state
      if (q && total === 0) {
        if (!emptyState) {
          emptyState = el('div', 'empty', `<h3>Sonuç yok</h3><p>“<span id="eq"></span>” için ürün bulunamadı. Başka bir arama deneyin.</p>`);
          main.appendChild(emptyState);
        }
        emptyState.querySelector('#eq').textContent = input.value.trim();
        emptyState.style.display = '';
      } else if (emptyState) {
        emptyState.style.display = 'none';
      }
    };

    input.addEventListener('input', apply);
    input.addEventListener('search', apply); // clear (x) button
  }

  /* ============================================================
     SCROLL-SPY  (highlight active category in the rail)
     ============================================================ */
  function wireScrollSpy(cats) {
    const rail = document.getElementById('rail');
    const btns = {};
    rail.querySelectorAll('.rail__btn').forEach((b) => { btns[b.dataset.target] = b; });

    const nav = document.getElementById('nav');
    const setActive = (slug) => {
      rail.querySelectorAll('.rail__btn').forEach((b) => b.classList.remove('is-active'));
      const b = btns[slug];
      if (b) {
        b.classList.add('is-active');
        // keep active chip in view
        const r = b.getBoundingClientRect();
        const rr = rail.getBoundingClientRect();
        if (r.left < rr.left + 8 || r.right > rr.right - 8) {
          rail.scrollTo({ left: rail.scrollLeft + (r.left - rr.left) - 16, behavior: 'smooth' });
        }
      }
    };

    let ticking = false;
    const onScroll = () => {
      if (ticking) return;
      ticking = true;
      requestAnimationFrame(() => {
        const navBottom = nav.getBoundingClientRect().bottom + 12;
        let current = cats[0].slug;
        for (const c of cats) {
          const sec = nodesByCat[c.slug];
          if (sec && sec.style.display !== 'none' && sec.getBoundingClientRect().top <= navBottom) {
            current = c.slug;
          }
        }
        setActive(current);
        ticking = false;
      });
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ============================================================
     SCROLL REVEAL
     ============================================================ */
  function wireReveal() {
    const reduce = window.matchMedia('(prefers-reduced-motion: reduce)').matches;
    const els = document.querySelectorAll('.reveal');
    if (reduce || !('IntersectionObserver' in window)) {
      els.forEach((e) => e.classList.add('in'));
      return;
    }
    const io = new IntersectionObserver((entries) => {
      entries.forEach((en) => {
        if (en.isIntersecting) { en.target.classList.add('in'); io.unobserve(en.target); }
      });
    }, { rootMargin: '0px 0px -8% 0px', threshold: 0.06 });
    els.forEach((e) => io.observe(e));
  }

  /* ============================================================
     LIGHTBOX
     ============================================================ */
  function wireLightbox() {
    const box = document.getElementById('lightbox');
    const img = document.getElementById('lightboxImg');
    const cap = document.getElementById('lightboxCap');
    const closeBtn = document.getElementById('lightboxClose');
    let lastFocus = null;

    const open = (full, name, price) => {
      lastFocus = document.activeElement;
      img.src = full;
      img.alt = name;
      cap.innerHTML = `<h4>${esc(name)}</h4><span class="p">${esc(price)}</span>`;
      box.classList.add('is-open');
      document.body.style.overflow = 'hidden';
      closeBtn.focus();
    };
    const close = () => {
      box.classList.remove('is-open');
      document.body.style.overflow = '';
      img.removeAttribute('src');
      if (lastFocus) lastFocus.focus();
    };

    document.getElementById('menu').addEventListener('click', (e) => {
      const t = e.target.closest('.card__thumb');
      if (!t || t.classList.contains('card__thumb--empty')) return;
      open(t.dataset.full, t.dataset.name, t.dataset.price);
    });
    closeBtn.addEventListener('click', close);
    box.addEventListener('click', (e) => { if (e.target === box) close(); });
    document.addEventListener('keydown', (e) => {
      if (e.key === 'Escape' && box.classList.contains('is-open')) close();
    });
  }

  /* ============================================================
     ERROR STATE
     ============================================================ */
  function showLoadError(err) {
    const main = document.getElementById('menu');
    main.innerHTML = `
      <div class="empty">
        <h3>Menü yüklenemedi</h3>
        <p>Veri dosyası okunamadı. Sayfayı yerel bir sunucu üzerinden açtığınızdan emin olun:<br>
        <code style="color:var(--silver)">python3 -m http.server</code></p>
      </div>`;
    console.error('[Cosmic] menu load failed:', err);
  }
})();
