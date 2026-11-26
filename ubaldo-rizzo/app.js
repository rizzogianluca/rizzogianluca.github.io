(function () {
  const I18N = {
    it: {
      nav_wood: "Legno", nav_stone: "Pietra", nav_relief: "Bassorilievi", nav_paint: "Pitture", nav_about: "L'artista",
      eyebrow: "Galleria virtuale · 1960–2003",
      lede: "Quarant'anni di forme scavate nel legno d'ulivo — e, accanto, la pietra, il gesso, la pittura e l'incisione.",
      cta: "Entra nella galleria",
      wood_title: "Sculture in legno d'ulivo",
      wood_sub: "Il nucleo dell'opera: figure, gruppi e forme aperte ricavate da tronchi d'ulivo, ordinate per decennio.",
      all: "Tutte",
      stone_title: "Sculture in pietra", stone_sub: "Opere degli anni Sessanta, fotografate in studio.",
      relief_title: "Bassorilievi", relief_sub: "Rilievi in gesso per una cappella e per un'abitazione.",
      paint_title: "Pitture e incisioni", paint_sub: "Le opere non di scultura: chine, linoleografie e oli, 1968–1972.",
      about_title: "L'artista",
      about_p1: "Ubaldo Rizzo ha lavorato soprattutto il legno d'ulivo, seguendone le venature, i nodi e i vuoti fino a farne figure sospese tra corpo e paesaggio. Le opere raccolte qui vanno dal primo bassorilievo, del 1960, alle sculture del 2003.",
      about_p2: "Questa galleria ripropone, con una nuova veste, le immagini e le didascalie del sito originale realizzato in famiglia tra il 2003 e il 2007.",
      f_works: "Opere", f_span: "Periodo", f_mat: "Materiali", f_mat_v: "ulivo, pietra, gesso, bronzo",
      foot: "Tutte le immagini sono di proprietà della famiglia.",
      views: n => n + " viste", undated: "s.d."
    },
    en: {
      nav_wood: "Wood", nav_stone: "Stone", nav_relief: "Reliefs", nav_paint: "Paintings", nav_about: "The artist",
      eyebrow: "Virtual gallery · 1960–2003",
      lede: "Forty years of forms carved from olive wood — alongside stone, plaster, painting and printmaking.",
      cta: "Enter the gallery",
      wood_title: "Olive-wood sculpture",
      wood_sub: "The heart of the work: figures, groups and open forms carved from olive trunks, arranged by decade.",
      all: "All",
      stone_title: "Stone sculpture", stone_sub: "Works from the 1960s, photographed in the studio.",
      relief_title: "Bas-reliefs", relief_sub: "Plaster reliefs made for a chapel and for a house.",
      paint_title: "Paintings and prints", paint_sub: "The works that are not sculpture: ink drawings, linocuts and oils, 1968–1972.",
      about_title: "The artist",
      about_p1: "Ubaldo Rizzo worked above all in olive wood, following its grain, knots and hollows to draw out figures poised between body and landscape. The works gathered here run from a first relief in 1960 to the sculptures of 2003.",
      about_p2: "This gallery presents, in a new form, the images and captions of the original family website made between 2003 and 2007.",
      f_works: "Works", f_span: "Period", f_mat: "Materials", f_mat_v: "olive wood, stone, plaster, bronze",
      foot: "All images are the property of the family.",
      views: n => n + " views", undated: "n.d."
    }
  };
  let lang = (function () { try { return localStorage.getItem("ur-lang") || "it"; } catch (e) { return "it"; } })();
  const works = window.WORKS || [];
  const grids = { wood: "grid-wood", stone: "grid-stone", relief: "grid-relief", paint: "grid-paint" };

  const title = w => (lang === "en" && w.te) ? w.te : w.t;
  const meta = w => {
    const m = lang === "en" ? w.me : w.m;
    return w.y ? `${m}, ${w.y}` : `${m}, ${I18N[lang].undated}`;
  };

  // build cards
  works.forEach((w, idx) => {
    const g = document.getElementById(grids[w.s]);
    if (!g) return;
    const fig = document.createElement("figure");
    fig.className = "card";
    fig.tabIndex = 0;
    fig.dataset.idx = idx;
    if (w.d) fig.dataset.dec = w.d;
    fig.innerHTML = `<div class="frame"><img loading="lazy" src="img/${w.i[0]}" alt="">${w.i.length > 1 ? '<span class="views"></span>' : ""}</div>
      <figcaption><div class="t"></div><div class="m"></div></figcaption>`;
    g.appendChild(fig);
    const im = fig.querySelector("img");
    const mark = () => { if (im.naturalWidth > im.naturalHeight * 1.15) im.parentNode.classList.add("wide"); };
    if (im.complete) mark(); else im.addEventListener("load", mark);
    fig.addEventListener("click", () => open(idx));
    fig.addEventListener("keydown", e => { if (e.key === "Enter" || e.key === " ") { e.preventDefault(); open(idx); } });
  });
  document.getElementById("count-works").textContent = works.length;

  function renderText() {
    document.documentElement.lang = lang;
    document.querySelectorAll("[data-i18n]").forEach(el => {
      const v = I18N[lang][el.dataset.i18n];
      if (typeof v === "string") el.textContent = v;
    });
    document.querySelectorAll(".card").forEach(c => {
      const w = works[c.dataset.idx];
      c.querySelector(".t").textContent = title(w);
      c.querySelector(".m").textContent = meta(w);
      c.querySelector("img").alt = `${title(w)} — ${meta(w)}`;
      const v = c.querySelector(".views");
      if (v) v.textContent = I18N[lang].views(w.i.length);
    });
    document.querySelectorAll(".lang button").forEach(b => b.setAttribute("aria-pressed", b.dataset.lang === lang));
    if (dlg.open) fill();
  }

  document.querySelectorAll(".lang button").forEach(b => b.addEventListener("click", () => {
    lang = b.dataset.lang;
    try { localStorage.setItem("ur-lang", lang); } catch (e) {}
    renderText();
  }));

  // decade filter
  document.querySelectorAll(".chip").forEach(ch => ch.addEventListener("click", () => {
    document.querySelectorAll(".chip").forEach(c => c.classList.toggle("active", c === ch));
    const d = ch.dataset.dec;
    document.querySelectorAll("#grid-wood .card").forEach(c => c.classList.toggle("hide", d !== "all" && c.dataset.dec !== d));
  }));

  // lightbox
  const dlg = document.getElementById("lightbox");
  let cur = 0, view = 0;
  function visibleList() {
    const w = works[cur];
    return [...document.querySelectorAll(`#${grids[w.s]} .card:not(.hide)`)].map(c => +c.dataset.idx);
  }
  function fill() {
    const w = works[cur];
    const img = document.getElementById("lb-img");
    img.src = "img/" + w.i[view];
    img.alt = `${title(w)} — ${meta(w)}`;
    document.getElementById("lb-title").textContent = title(w);
    document.getElementById("lb-meta").textContent = meta(w);
    document.getElementById("lb-note").textContent = w.n ? (lang === "en" ? w.ne : w.n) : "";
    const th = document.getElementById("lb-thumbs");
    th.innerHTML = "";
    if (w.i.length > 1) w.i.forEach((src, k) => {
      const b = document.createElement("button");
      b.setAttribute("aria-current", k === view);
      b.innerHTML = `<img src="img/${src}" alt="">`;
      b.addEventListener("click", () => { view = k; fill(); });
      th.appendChild(b);
    });
  }
  function open(idx) { cur = idx; view = 0; fill(); if (!dlg.open) dlg.showModal(); }
  function step(dir) {
    const list = visibleList();
    const p = list.indexOf(cur);
    cur = list[(p + dir + list.length) % list.length]; view = 0; fill();
  }
  dlg.querySelector(".lb-close").addEventListener("click", () => dlg.close());
  dlg.querySelector(".lb-prev").addEventListener("click", () => step(-1));
  dlg.querySelector(".lb-next").addEventListener("click", () => step(1));
  dlg.addEventListener("click", e => { if (e.target === dlg) dlg.close(); });
  dlg.addEventListener("keydown", e => {
    if (e.key === "ArrowRight") step(1);
    if (e.key === "ArrowLeft") step(-1);
  });

  renderText();
})();
