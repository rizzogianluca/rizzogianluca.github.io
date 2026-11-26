#!/usr/bin/env python3
"""Regenerate the Ubaldo Rizzo site.

Edit data.js (titles, materials, years, images; add "n"/"ne" for notes), then run:
    python3 ubaldo-rizzo/_src/build.py
Requires Python 3.12+ and Pillow. Writes all HTML pages into the folder above this one.
"""
import json, re, os, html, unicodedata, shutil

HERE = os.path.dirname(os.path.abspath(__file__))
OUT = os.path.normpath(os.path.join(HERE, ".."))
EMAIL = ""   # address for "Segnala un'opera"; leave empty to hide the mail button
FONTS = '<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin><link href="https://fonts.googleapis.com/css2?family=Cormorant+Garamond:ital,wght@0,400;0,500;0,600;1,400;1,500&family=Inter:wght@400;500&display=swap" rel="stylesheet">'

raw = open(os.path.join(HERE, "data.js"), encoding="utf-8").read()
works = json.loads(raw[raw.index("["): raw.rindex("]") + 1])

def esc(s): return html.escape(s or "", quote=True)
def slug(s):
    s = unicodedata.normalize("NFD", s).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", s).strip("-")
def L(it, en): return f'<span lang="it">{it}</span><span lang="en">{en}</span>'

TYPE = {"wood": ("scultura", "sculpture"), "stone": ("scultura", "sculpture"), "relief": ("bassorilievo", "bas-relief"), "paint": ("pittura / incisione", "painting / print")}
TYPEKEY = {"wood": "sculpture", "stone": "sculpture", "relief": "relief", "paint": "paint"}
PERIODS = [("1960", "1960–1969"), ("1970", "1970–1979"), ("1980", "1980–1989"), ("1990", "1990–1999"), ("2000", "2000–2003")]

def sortyear(w):
    y = w.get("y") or ""
    m = re.match(r"(\d{4})", y)
    return int(m.group(1)) + (5 if "–" in y else 0) if m else 9999
def period(w):
    y = sortyear(w)
    if y == 9999: return "nd"
    return "2000" if y >= 2000 else str(y // 10 * 10)

order = {"wood": 0, "stone": 1, "relief": 2, "paint": 3}
works.sort(key=lambda w: (sortyear(w), order[w["s"]], w["t"]))
for i, w in enumerate(works, 1):
    w["no"] = f"UR {i:03d}"
    w["id"] = f"ur-{i:03d}-{slug(w['t'])}"
    w["period"] = period(w)
    w["te"] = w.get("te") or w["t"]
byimg = {w["i"][0]: w for w in works}
# Restored photos (background removed, AI-upscaled, colour-corrected) live in img/r/; transparent cut-outs in img/cut/.
# restored.json lists the images whose restoration was reviewed and approved; all others keep the original photo.
try: RESTORED = set(json.load(open(os.path.join(HERE, "restored.json"))))
except FileNotFoundError: RESTORED = set()
def disp(im): return f"r/{im}" if im in RESTORED and os.path.exists(os.path.join(OUT, "img", "r", im)) else im
for w in works:  # lead with a restored view when the main photo could not be restored
    if w["i"][0] not in RESTORED:
        r = [im for im in w["i"] if im in RESTORED]
        if r: w["i"] = [r[0]] + [im for im in w["i"] if im != r[0]]
def cardimg(im):
    return f"card/{im}" if im in RESTORED and os.path.exists(os.path.join(OUT, "img", "card", im)) else disp(im)
def cutout(im):
    c = os.path.splitext(im)[0] + ".webp"
    return f"cut/{c}" if im in RESTORED and os.path.exists(os.path.join(OUT, "img", "cut", c)) else None

def meta(w, lang="it"):
    m = w["m"] if lang == "it" else w["me"]
    y = w.get("y") or ("s.d." if lang == "it" else "n.d.")
    return f"{m}, {y}"

def head(title, depth, desc="", dark=False, extra=""):
    p = "../" * depth
    return f"""<!DOCTYPE html>
<html lang="it" data-lang="it">
<head>
<meta charset="utf-8"><meta name="viewport" content="width=device-width, initial-scale=1">
<title>{esc(title)}</title>
<meta name="description" content="{esc(desc or "Ubaldo Rizzo: sculture in legno d'ulivo, pietra e gesso, pitture e incisioni, 1960–2003.")}">
<script>try{{var l=localStorage.getItem("ur-lang");if(l)document.documentElement.dataset.lang=l}}catch(e){{}}</script>
{FONTS}
<link rel="stylesheet" href="{p}assets/site.css">
{extra}
</head>
"""

NAV = [("", "Percorso", "Journey"), ("opere/", "Opere", "Works"), ("vita/", "Vita e opere", "Life & work"), ("archivio/", "Archivio", "Archive"), ("segnala/", "Segnala un'opera", "Report a work")]
def bar(depth, current, dark=False):
    p = "../" * depth
    links = "".join(f'<a href="{p}{href}"{" aria-current=\"page\"" if href == current else ""}>{L(it, en)}</a>' for href, it, en in NAV)
    return f"""<header class="bar{' dark' if dark else ''}">
  <a class="brand" href="{p}">Ubaldo Rizzo</a>
  <button class="menu-btn" aria-expanded="false">Menu</button>
  <nav>{links}</nav>
  <div class="langsw" role="group" aria-label="Lingua / Language"><button data-lang="it" aria-pressed="true">IT</button><button data-lang="en" aria-pressed="false">EN</button></div>
</header>"""

def foot(depth, scripts=()):
    p = "../" * depth
    s = "".join(f'<script src="{p}assets/{x}"></script>' for x in ("common.js",) + tuple(scripts))
    return f"""<footer class="footer"><p>© Famiglia Rizzo · {L("Immagini dall'archivio di famiglia.", "Images from the family archive.")}</p><p><a href="https://www.comune.cavallino.le.it" target="_blank" rel="noopener">Cavallino</a></p></footer>
{s}
</body></html>"""

def write(path, content):
    full = os.path.join(OUT, path)
    os.makedirs(os.path.dirname(full) or OUT, exist_ok=True)
    open(full, "w", encoding="utf-8").write(content)

def card(w, p):
    return f"""<a class="wcard" href="{p}opere/{w['id']}/" data-no="{w['no']}" data-title="{esc(w['t'])}" data-year="{sortyear(w):04d}" data-period="{w['period']}" data-type="{TYPEKEY[w['s']]}" data-mat="{slug(w['m'])}" data-search="{esc(w['t']+' '+w['te']+' '+w['m']+' '+w['me']+' '+(w.get('y') or '')+' '+w['no'])}">
<div class="frame{' restored' if w['i'][0] in RESTORED else ''}"><img loading="lazy" src="{p}img/{cardimg(w['i'][0])}" alt="{esc(w['t'])}" style="view-transition-name:{w['id']}"></div>
<div class="cap"><div class="no">{w['no']}</div><div class="t">{L(esc(w['t']), esc(w['te']))}</div><div class="m">{L(esc(meta(w)), esc(meta(w, 'en')))}</div></div></a>"""

# ---------------------------------------------------------------- catalogue
def catalogue():
    p = "../"
    def cnt(f): return sum(1 for w in works if f(w))
    chips_p = f'<button class="chip" data-k="period" data-v="all">{L("Tutti i periodi", "All periods")}</button>' + "".join(
        f'<button class="chip" data-k="period" data-v="{k}">{lab}<span class="n">{cnt(lambda w, k=k: w["period"] == k)}</span></button>' for k, lab in PERIODS) + \
        f'<button class="chip" data-k="period" data-v="nd">{L("senza data", "undated")}<span class="n">{cnt(lambda w: w["period"] == "nd")}</span></button>'
    chips_t = f'<button class="chip" data-k="type" data-v="all">{L("Tutto", "All")}</button>' + "".join(
        f'<button class="chip" data-k="type" data-v="{k}">{L(it, en)}<span class="n">{cnt(lambda w, k=k: TYPEKEY[w["s"]] == k)}</span></button>'
        for k, it, en in [("sculpture", "Sculture", "Sculpture"), ("relief", "Bassorilievi", "Reliefs"), ("paint", "Pitture e incisioni", "Paintings & prints")])
    mats = {}
    for w in works: mats.setdefault(slug(w["m"]), (w["m"], w["me"], 0)); mats[slug(w["m"])] = (w["m"], w["me"], mats[slug(w["m"])][2] + 1)
    opts = '<option value="all">Materiale / medium</option>' + "".join(f'<option value="{k}">{esc(it)} · {esc(en)} ({n})</option>' for k, (it, en, n) in sorted(mats.items(), key=lambda x: -x[1][2]))
    rows = "".join(f"""<a href="{p}opere/{w['id']}/" data-no="{w['no']}" data-title="{esc(w['t'])}" data-year="{sortyear(w):04d}" data-period="{w['period']}" data-type="{TYPEKEY[w['s']]}" data-mat="{slug(w['m'])}" data-search="{esc(w['t']+' '+w['te']+' '+w['m']+' '+w['me']+' '+(w.get('y') or '')+' '+w['no'])}"><span class="no">{w['no']}</span><span class="t">{L(esc(w['t']), esc(w['te']))}</span><span class="m">{L(esc(w['m']), esc(w['me']))}</span><span class="y">{esc(w.get('y') or '—')}</span></a>""" for w in works)
    body = f"""{head("Opere — Ubaldo Rizzo", 1, "Catalogo delle opere di Ubaldo Rizzo.")}<body>
{bar(1, "opere/")}
<main class="page">
  <div class="page-head"><p class="kicker">{L("Catalogo", "Catalogue")}</p><h1 class="title">{L("Opere", "Works")}</h1>
  <p class="lead">{L(f"{len(works)} opere schedate, dal 1960 al 2003. Ogni opera ha un numero di catalogo e una pagina propria.", f"{len(works)} catalogued works, from 1960 to 2003. Each work has a catalogue number and its own page.")}</p></div>
  <div class="tools"><div class="chips">{chips_p}</div></div>
  <div class="tools"><div class="chips">{chips_t}</div>
    <select id="f-mat" aria-label="Materiale">{opts}</select>
    <input id="f-q" type="search" data-ph-it="Cerca un titolo…" data-ph-en="Search a title…" placeholder="Cerca un titolo…" aria-label="Cerca">
    <select id="f-sort" aria-label="Ordina"><option value="no">N° catalogo</option><option value="year">Anno / year</option><option value="title">Titolo / title</option></select>
    <div class="viewsw"><button class="chip" data-view="grid">{L("Griglia", "Grid")}</button><button class="chip" data-view="list">{L("Elenco", "List")}</button></div>
  </div>
  <p class="count"><span class="num">{len(works)}</span> {L("opere", "works")}</p>
  <div class="cat-grid">{''.join(card(w, p) for w in works)}</div>
  <div class="cat-list">{rows}</div>
  <p class="empty hide">{L("Nessuna opera corrisponde ai filtri.", "No works match these filters.")}</p>
</main>
{foot(1, ("catalogue.js",))}"""
    write("opere/index.html", body)

# ---------------------------------------------------------------- work pages
def work_pages():
    p = "../../"
    for i, w in enumerate(works):
        prev, nxt = works[i - 1] if i else None, works[i + 1] if i + 1 < len(works) else None
        related = [x for x in works if x is not w and (slug(x["t"]) == slug(w["t"]) and x["t"] not in ("Senza titolo",))]
        if len(related) < 4:
            related += [x for x in works if x is not w and x not in related and x["period"] == w["period"] and x["s"] == w["s"]][: 4 - len(related)]
        thumbs = "".join(f'<button data-src="{p}img/{disp(im)}" data-orig="{p}img/{im}" data-rest="{str(im in RESTORED).lower()}" aria-current="{str(k == 0).lower()}"><img src="{p}img/{disp(im)}" alt=""></button>' for k, im in enumerate(w["i"])) if len(w["i"]) > 1 else ""
        r0 = w["i"][0] in RESTORED
        anyr = any(im in RESTORED for im in w["i"])
        rest_sw = (f'<div class="restsw"{"" if r0 else " hidden"}><button data-v="r" aria-pressed="true">{L("Restaurata", "Restored")}</button><button data-v="o" aria-pressed="false">{L("Originale", "Original")}</button>'
                   f'<span class="restnote">{L("Sfondo rimosso, nitidezza e colore migliorati con strumenti di IA. Nessuna parte dell\'opera è stata generata.", "Background removed, sharpness and colour improved with AI tools. No part of the work was generated.")}</span></div>') if anyr else ""
        unk = f'<span class="unknown">{L("da completare", "to be completed")}</span>'
        note = f"<div><dt>{L('Note', 'Notes')}</dt><dd>{L(esc(w['n']), esc(w['ne']))}</dd></div>" if w.get("n") else ""
        ld = {"@context": "https://schema.org", "@type": "VisualArtwork", "name": w["t"], "creator": {"@type": "Person", "name": "Ubaldo Rizzo"},
              "artMedium": w["m"], "artform": TYPE[w["s"]][0], "image": f"../../img/{disp(w['i'][0])}", "identifier": w["no"]}
        if w.get("y"): ld["dateCreated"] = w["y"]
        pn = ""
        if prev: pn += f'<a class="prev" href="{p}opere/{prev["id"]}/">← {prev["no"]}<span class="t">{esc(prev["t"])}</span></a>'
        else: pn += "<span></span>"
        if nxt: pn += f'<a class="next" href="{p}opere/{nxt["id"]}/" style="text-align:right">{nxt["no"]} →<span class="t">{esc(nxt["t"])}</span></a>'
        body = f"""{head(f"{w['t']} ({w['no']}) — Ubaldo Rizzo", 2, f"{w['t']}, {meta(w)}. Ubaldo Rizzo, {w['no']}.", extra=f'<script type="application/ld+json">{json.dumps(ld, ensure_ascii=False)}</script>')}<body>
{bar(2, "opere/")}
<main>
<article class="work">
  <div><div class="stage{' is-restored' if r0 else ''}"><img id="w-main" src="{p}img/{disp(w['i'][0])}" data-orig="{p}img/{w['i'][0]}" data-rest="{str(r0).lower()}" alt="{esc(w['t'])} — {esc(meta(w))}" style="view-transition-name:{w['id']}"></div>
  {rest_sw}<div class="thumbs">{thumbs}</div></div>
  <div class="winfo">
    <a class="back" href="{p}opere/">← {L("Tutte le opere", "All works")}</a>
    <p class="no">{w['no']}</p>
    <h1>{L(esc(w['t']), esc(w['te']))}</h1>
    <p class="sub">{L(esc(meta(w)), esc(meta(w, 'en')))}</p>
    <dl>
      <div><dt>{L("Catalogo", "Catalogue")}</dt><dd>{w['no']}</dd></div>
      <div><dt>{L("Anno", "Year")}</dt><dd>{esc(w.get('y')) or L('senza data', 'undated')}</dd></div>
      <div><dt>{L("Tecnica", "Medium")}</dt><dd>{L(esc(w['m']), esc(w['me']))}</dd></div>
      <div><dt>{L("Tipo", "Type")}</dt><dd>{L(*TYPE[w['s']])}</dd></div>
      <div><dt>{L("Dimensioni", "Dimensions")}</dt><dd>{unk}</dd></div>
      <div><dt>{L("Collocazione", "Location")}</dt><dd>{unk}</dd></div>
      {note}
      <div><dt>{L("Viste", "Views")}</dt><dd>{len(w['i'])}</dd></div>
    </dl>
    {btn3d(w, p)}
    <div class="pn">{pn}</div>
  </div>
</article>
<section class="related"><h2>{L("Opere vicine", "Related works")}</h2><div class="cat-grid">{''.join(card(x, p) for x in related[:4])}</div></section>
</main>
<div class="zoom" role="dialog" aria-label="Zoom"><img alt=""></div>
{foot(2)}"""
        write(f"opere/{w['id']}/index.html", body)

CAPPELLA3D = {"bassorilievi-cappella-superiore.jpg": "superiore", "bassorilievi-cappella-intermedio.jpg": "centrale", "bassorilievi-cappella-inferiore.jpg": "inferiore"}
def btn3d(w, p):
    v = next((CAPPELLA3D[im] for im in w["i"] if im in CAPPELLA3D), None)
    return f'<a class="btn3d" href="{p}cappella-3d/#{v}">{L("Esplora il rilievo in 3D", "Explore the relief in 3D")} →</a>' if v else ""

# ---------------------------------------------------------------- cappella 3D
def cappella3d():
    p = "../"
    parts = {v: next(w for w in works if k in w["i"]) for k, v in CAPPELLA3D.items()}
    links = "".join(f'<a href="{p}opere/{parts[v]["id"]}/">{L(esc(parts[v]["t"]), esc(parts[v]["te"]))}</a>' for v in ("superiore", "centrale", "inferiore"))
    views = "".join(f'<button data-view="{k}" aria-pressed="{str(k == "intero").lower()}">{L(it, en)}</button>' for k, it, en in
                    [("intero", "Intero", "Whole"), ("superiore", "Parte superiore", "Upper"), ("centrale", "Parte centrale", "Middle"), ("inferiore", "Parte inferiore", "Lower")])
    imap = '<script type="importmap">{"imports":{"three":"https://cdn.jsdelivr.net/npm/three@0.169.0/build/three.module.js","three/addons/":"https://cdn.jsdelivr.net/npm/three@0.169.0/examples/jsm/"}}</script>'
    body = f"""{head("La cappella in 3D — Ubaldo Rizzo", 1, "Il grande bassorilievo della cappella di Ubaldo Rizzo, da esplorare in tre dimensioni.", extra=imap)}<body>
{bar(1, "opere/")}
<main class="page">
  <div class="page-head"><p class="kicker">{L("Bassorilievo · gesso", "Bas-relief · plaster")}</p><h1 class="title">{L("La cappella, in rilievo", "The chapel relief in 3D")}</h1>
  <p class="lead">{L("Le tre parti del grande bassorilievo della cappella, ricomposte in un unico pannello. Trascinalo per girarci intorno e sposta la luce radente per far emergere le figure.", "The three sections of the large chapel relief, put back together as one panel. Drag to move around it, and move the raking light to bring the figures out.")}</p></div>
  <div class="r3d-wrap">
    <div class="r3d" id="r3d" data-base="{p}img/3d/" aria-label="{L("Modello 3D interattivo del bassorilievo", "Interactive 3D model of the relief")}">
      <img class="r3d-poster" src="{p}img/3d/cappella-albedo.jpg" alt="{L("Il bassorilievo della cappella", "The chapel relief")}">
      <p class="r3d-msg">{L("Caricamento del modello…", "Loading the model…")}</p>
      <noscript><img src="{p}img/3d/cappella-albedo.jpg" alt="" style="position:absolute;inset:0;height:100%;margin:auto"></noscript>
    </div>
    <div class="r3d-panel">
      <div><h2>{L("Vista", "View")}</h2><div class="r3d-views">{views}</div></div>
      <div><h2>{L("Luce radente", "Raking light")}</h2>
        <label>{L("Direzione", "Direction")}<input id="r3d-az" type="range" min="-180" max="180" step="1" value="38"></label>
        <label>{L("Altezza", "Height")}<input id="r3d-el" type="range" min="4" max="85" step="1" value="26"></label></div>
      <div><h2>{L("Rilievo", "Relief")}</h2>
        <label>{L("Profondità", "Depth")}<input id="r3d-depth" type="range" min="0.01" max="0.22" step="0.005" value="0.085"></label></div>
      <div><h2>{L("Superficie", "Surface")}</h2><div class="r3d-mats"><button data-mat="foto" aria-pressed="true">{L("Fotografia", "Photograph")}</button><button data-mat="gesso" aria-pressed="false">{L("Solo forma", "Shape only")}</button></div></div>
      <p class="r3d-hint">{L("Trascina per ruotare · tasto destro o due dita per spostare · rotella o pizzico per avvicinarti · doppio clic per girare intorno a un punto.", "Drag to rotate · right-drag or two fingers to pan · scroll or pinch to zoom · double-click to orbit a point.")}</p>
    </div>
  </div>
  <p class="r3d-note">{L("Il modello è ricostruito a partire dalle fotografie: la profondità del rilievo è stimata dalle luci e dalle ombre, non misurata sull'opera. Le figure e i dettagli sono quelli delle fotografie.", "The model is reconstructed from photographs: the depth of the relief is estimated from light and shadow, not measured on the work. The figures and details are those in the photographs.")}</p>
  <div class="r3d-links">{links}</div>
</main>
<script type="module" src="{p}assets/relief3d.js"></script>
{foot(1)}"""
    write("cappella-3d/index.html", body)

# ---------------------------------------------------------------- vita
def vita():
    p = "../"
    years = {}
    for w in works: years.setdefault(w.get("y") or "s.d.", []).append(w)
    keys = sorted(years, key=lambda y: sortyear({"y": y if y != "s.d." else ""}))
    rows = ""
    for y in keys:
        items = "".join(f'<a href="{p}opere/{w["id"]}/"><img loading="lazy" src="{p}img/{w["i"][0]}" alt=""><span><span class="t">{L(esc(w["t"]), esc(w["te"]))}</span><br><span class="m">{L(esc(w["m"]), esc(w["me"]))}</span></span></a>' for w in years[y])
        rows += f'<div class="tl-year"><h3>{esc(y)}</h3><div class="tl-items">{items}</div></div>'
    body = f"""{head("Vita e opere — Ubaldo Rizzo", 1)}<body>
{bar(1, "vita/")}
<main class="page">
  <div class="page-head"><p class="kicker">{L("Cronologia", "Chronology")}</p><h1 class="title">{L("Vita e opere", "Life and work")}</h1>
  <p class="lead">{L("Anno dopo anno, le opere datate: dal primo bassorilievo del 1960 alle ultime sculture del 2003.", "Year by year, the dated works: from the first relief in 1960 to the last sculptures of 2003.")}</p></div>
  <p class="note">{L("La biografia completa è in preparazione con la famiglia. Se conosci date, mostre o luoghi legati a Ubaldo Rizzo, <a href='../segnala/'>scrivici</a>.", "A full biography is being prepared with the family. If you know dates, exhibitions or places connected with Ubaldo Rizzo, <a href='../segnala/'>write to us</a>.")}</p>
  <div class="tl">{rows}</div>
</main>
{foot(1)}"""
    write("vita/index.html", body)

# ---------------------------------------------------------------- archivio
def archivio():
    p = "../"
    def fig(src, it, en): return f'<figure><img loading="lazy" src="{p}img/{src}" alt="{esc(it)}"><figcaption>{L(it, en)}</figcaption></figure>'
    shop = fig("sculture-cammello1.jpg", "In bottega: <i>Gruppo</i> (1993) appena sbozzato, tra i trucioli.", "In the workshop: <i>Gruppo</i> (1993) freshly roughed out, among the shavings.") + \
           fig("sculture-cammello2.jpg", "<i>Gruppo</i> (1993), un'altra vista in bottega.", "<i>Gruppo</i> (1993), another view in the workshop.") + \
           fig("sculture-bernoccolo1.jpg", "<i>Donna al sole (in piedi)</i>, 2003, sollevata per la fotografia.", "<i>Donna al sole (in piedi)</i>, 2003, held up for the photograph.") + \
           fig("sculture-foto-di-gruppo-2.jpg", "Sculture nel cortile.", "Sculptures in the courtyard.") + \
           fig("sculture-sagoma.jpg", "Accanto ad <i>Atleta</i> (1994).", "Beside <i>Atleta</i> (1994).")
    try: IMM = json.load(open(os.path.join(HERE, "immich.json")))
    except FileNotFoundError: IMM = {"known": [], "new": []}
    unid = "".join(fig(disp(e["i"][0]), f"Fotografia {e['y']}. Opera da identificare.", f"Photograph {e['y']}. Work to be identified.") for e in IMM["new"]) + \
           "".join(fig(f"hi/{h}.jpg", f"Fotografia {d}. Opera da identificare.", f"Photograph {d}. Work to be identified.")
                   for h, d in [("h01", "2007"), ("h53", "2007"), ("h43", "2008"), ("h12", "2009"), ("h101", "2009"), ("h142", "2009")])
    body = f"""{head("Archivio — Ubaldo Rizzo", 1)}<body>
{bar(1, "archivio/")}
<main class="page">
  <div class="page-head"><p class="kicker">{L("Archivio", "Archive")}</p><h1 class="title">{L("Archivio", "Archive")}</h1>
  <p class="lead">{L("Fotografie di lavoro, opere ancora da catalogare e la storia di questo sito.", "Working photographs, works still to be catalogued, and the story of this website.")}</p></div>
  <section class="arch-sec"><h2>{L("La bottega e il cortile", "Workshop and courtyard")}</h2><p>{L("Le opere fotografate dove nascevano e dove venivano messe ad asciugare al sole.", "The works photographed where they were made and where they were set out in the sun.")}</p><div class="arch-grid">{shop}</div></section>
  <section class="arch-sec"><h2>{L("Opere da identificare", "Works to be identified")}</h2><p>{L("Fotografie scattate tra il 2006 e il 2013 di opere che non compaiono nel catalogo del 2005. Se ne riconosci una — titolo, anno, dove si trova — <a href='../segnala/'>segnalacelo</a>.", "Photographs taken between 2006 and 2013 of works that are not in the 2005 catalogue. If you recognise one — title, year, where it is now — <a href='../segnala/'>let us know</a>.")}</p><div class="arch-grid">{unid}</div></section>
  <section class="arch-sec"><h2>{L("La cappella in 3D", "The chapel relief in 3D")}</h2><p>{L("Le tre parti del bassorilievo della cappella ricomposte in un modello tridimensionale, da girare e illuminare.", "The three sections of the chapel relief put back together as a 3D model you can turn and light.")} <a href="../cappella-3d/">{L("Apri il modello", "Open the model")} →</a></p></section>
  <section class="arch-sec"><h2>{L("Le versioni del sito", "Versions of the website")}</h2><p>{L("Questo sito è il quarto: i primi furono costruiti in famiglia.", "This is the fourth version of the site; the first ones were built in the family.")}</p>
  <div class="versions">
    <div><b>2003</b>{L("Prima pagina su Xoom/Virgilio: legno, pietra, bassorilievi.", "First page on Xoom/Virgilio: wood, stone, reliefs.")}</div>
    <div><b>2005</b>{L("«Ubaldo Rizzo Virtual Gallery»: sculture per decennio, pitture, didascalie in italiano.", "“Ubaldo Rizzo Virtual Gallery”: sculptures by decade, paintings, Italian captions.")}</div>
    <div><b>2007</b>{L("Album fotografico delle sculture (132 immagini).", "Photo album of the sculptures (132 images).")}</div>
    <div><b>2026</b>{L("Questo catalogo: numeri di catalogo, schede, percorso.", "This catalogue: catalogue numbers, work pages, journey.")}</div>
  </div></section>
</main>
{foot(1)}"""
    write("archivio/index.html", body)

# ---------------------------------------------------------------- segnala
def segnala():
    subj = "Segnalazione opera di Ubaldo Rizzo"
    mail = (f'<p><a class="btn" href="mailto:{EMAIL}?subject={subj.replace(" ", "%20")}">{L("Scrivi alla famiglia", "Write to the family")}</a></p>' if EMAIL else "")
    body = f"""{head("Segnala un'opera — Ubaldo Rizzo", 1)}<body>
{bar(1, "segnala/")}
<main class="page form-like">
  <div class="page-head"><p class="kicker">{L("Catalogo aperto", "An open catalogue")}</p><h1 class="title">{L("Segnala un'opera", "Report a work")}</h1>
  <p class="lead">{L("Molte sculture di Ubaldo Rizzo sono in case di parenti, amici e collezionisti. Questo catalogo cresce con il vostro aiuto.", "Many of Ubaldo Rizzo's sculptures are in the homes of relatives, friends and collectors. This catalogue grows with your help.")}</p></div>
  <p>{L("Se possiedi o conosci un'opera, inviaci:", "If you own or know of a work, please send us:")}</p>
  <ol>
    <li>{L("una o più fotografie (fronte, profilo, retro);", "one or more photographs (front, side, back);")}</li>
    <li>{L("titolo e anno, se noti;", "title and year, if known;")}</li>
    <li>{L("materiale e dimensioni approssimative;", "material and approximate dimensions;")}</li>
    <li>{L("dove si trova oggi e come è arrivata lì.", "where it is now and how it got there.")}</li>
  </ol>
  {mail}
</main>
{foot(1)}"""
    write("segnala/index.html", body)

# ---------------------------------------------------------------- journey (home)
CHAPTERS = [
    ("1960", "I", "1962 — 1970", "#0d0c0b", ["sculture-10c.jpg", "sculture-scaglia.jpg", "sculture-6c.jpg", "sculture-groviera.jpg", "sculture-donnalsole1.jpg"]),
    ("1970", "II", "1972 — 1980", "#17130f", ["sculture-buco.jpg", "sculture-pesce.jpg", "sculture-puffobronzo1.jpg", "sculture-salto4.jpg"]),
    ("1980", "III", "1982 — 1990", "#241b14", ["sculture-pulcino2.jpg", "sculture-uccello1.jpg", "sculture-spilungone-det1.jpg", "sculture-gruppofamiliare1.jpg"]),
    ("1990", "IV", "1991 — 2000", "#3a2a1d", ["sculture-pinguino.jpg", "sculture-madreal1.jpg", "sculture-urlo.jpg", "sculture-lumaca1.jpg"]),
    ("2000", "V", "2001 — 2003", "#5a4029", ["sculture-emme1.jpg", "sculture-morso1.jpg", "sculture-uccellodimare1.jpg"]),
]
def journey():
    from PIL import Image
    p = ""
    secs, prog = [], []
    for k, (key, roman, years, tone, imgs) in enumerate(CHAPTERS):
        pw = [w for w in works if w["period"] == key]
        n = len(pw)
        ys = [sortyear(w) for w in pw if re.fullmatch(r"\d{4}", w.get("y") or "")]
        years = f"{min(ys)} — {max(ys)}"
        names = [next(x for x in works if im in x["i"])["t"] for im in imgs]
        prog.append(f'<a href="#ch-{key}" data-ch="{key}">{years.split(" ")[0]}</a>')
        secs.append(f"""<section class="j-chapter" id="ch-{key}" data-tone="{tone}" data-ch="{key}">
  <div><p class="roman">{roman}</p><p class="years">{years}</p>
  <p class="ctitle">{esc(", ".join(names[:-1]))} {L("e", "and")} {esc(names[-1])}</p><p class="ccount">{L(f"{n} opere in catalogo", f"{n} works in the catalogue")}</p></div></section>""")
        for j, im in enumerate(imgs):
            w = next(x for x in works if im in x["i"])
            co = cutout(im)
            src = co or im
            wide = Image.open(f"{OUT}/img/{src}").size
            cls = (' class="cut wide"' if co else ' class="wide"') if wide[0] > wide[1] * 1.15 else (' class="cut"' if co else "")
            secs.append(f"""<section class="j-work{' flip' if j % 2 else ''}" data-tone="{tone}" data-ch="{key}">
  <div class="j-fig"><img loading="lazy" src="img/{src}" alt="{esc(w['t'])}"{cls}></div>
  <div class="j-cap"><p class="t">{L(esc(w['t']), esc(w['te']))}</p><p class="m">{L(esc(meta(w)), esc(meta(w, 'en')))}</p><a href="opere/{w['id']}/">{L("La scheda", "The record")} · {w['no']}</a></div>
</section>""")
        if key == "1960":
            secs.append(f"""<section class="j-grain" data-tone="{tone}" data-ch="{key}"><div class="bg"></div><div class="txt">
  <p class="j-small">{L("Il legno d'ulivo", "Olive wood")}</p>
  <p class="j-line">{L("Nodi, venature, vuoti. Una forma che c'era già, e che andava trovata.", "Knots, grain, hollows. A form that was already there, waiting to be found.")}</p></div></section>""")
        if key == "1990":
            secs.append(f"""<section class="j-workshop" data-tone="{tone}" data-ch="{key}"><div>
  <p class="j-small">{L("In bottega", "In the workshop")}</p>
  <p class="j-line">{L("Trucioli a terra, un tronco che diventa figura.", "Shavings on the floor, a trunk becoming a figure.")}</p>
  <div class="j-polas">
    <figure><img loading="lazy" src="img/sculture-cammello1.jpg" alt=""><figcaption>Gruppo, 1993</figcaption></figure>
    <figure><img loading="lazy" src="img/sculture-cammello2.jpg" alt=""><figcaption>Gruppo, 1993</figcaption></figure>
    <figure><img loading="lazy" src="img/sculture-bernoccolo2.jpg" alt=""><figcaption>Donna al sole, 2003</figcaption></figure>
  </div></div></section>""")
    total = len(works)
    body = f"""{head("Ubaldo Rizzo — Sculture in legno d'ulivo", 0)}<body class="journey">
{bar(0, "", dark=True)}
<main>
<section class="j-intro" data-tone="#0d0c0b" data-ch="intro">
  <div class="ghost"><img src="img/{cutout('sculture-10c.jpg') or 'sculture-10c.jpg'}" alt=""></div>
  <div class="lit"><img src="img/{cutout('sculture-10c.jpg') or 'sculture-10c.jpg'}" alt="Preghiera, legno di ulivo, 1968"></div>
  <span class="j-touchnote">{L("Muovi la luce", "Move the light")}</span>
  <div class="j-name"><h1>Ubaldo<br>Rizzo</h1><p>{L("Quarant'anni di forme nel legno d'ulivo · 1960 — 2003", "Forty years of forms in olive wood · 1960 — 2003")}</p></div>
  <div class="j-hint">{L("Scorri", "Scroll")}</div>
</section>
{''.join(secs)}
<section class="j-light" data-tone="#7a5a3a" data-ch="after"><div class="bg" style="background-image:url(img/hi/h142.jpg)"></div>
  <div class="txt"><p class="j-small">{L("Fotografie 2007 — 2009", "Photographs 2007 — 2009")}</p><p class="j-line">{L("Nel cortile, al sole, il legno continua a parlare.", "In the courtyard, in the sun, the wood keeps speaking.")}</p></div></section>
<div class="j-strip"><img loading="lazy" src="img/hi/h01.jpg" alt=""><img loading="lazy" src="img/hi/h53.jpg" alt=""><img loading="lazy" src="img/hi/h12.jpg" alt=""><img loading="lazy" src="img/hi/h101.jpg" alt=""></div>
<section class="j-end" data-tone="#0d0c0b" data-ch="end"><div>
  <h2>{L("Continua a guardare", "Keep looking")}</h2>
  <p>{L(f"Il catalogo raccoglie {total} opere, ognuna con la sua scheda. Alcune aspettano ancora un nome: forse sai dove si trovano.", f"The catalogue holds {total} works, each with its own record. Some are still waiting for a name: perhaps you know where they are.")}</p>
  <div class="doors"><a class="btn" href="opere/">{L("Tutte le opere", "All works")}</a><a class="btn" href="vita/">{L("Vita e opere", "Life & work")}</a><a class="btn" href="segnala/">{L("Segnala un'opera", "Report a work")}</a></div>
</div></section>
</main>
<nav class="j-progress" aria-label="Capitoli">{''.join(prog)}</nav>
{foot(0, ("journey.js",)).replace('<footer class="footer">', '<footer class="footer" style="border-color:rgba(255,255,255,.08);color:rgba(239,231,218,.5)">')}"""
    write("index.html", body)

# ---------------------------------------------------------------- revisione (not linked; for the family)
def revisione():
    try: IMM = json.load(open(os.path.join(HERE, "immich.json")))
    except FileNotFoundError: return
    p = "../"
    byfirst = {}
    for w in works:
        for im in w["i"]: byfirst.setdefault(im, w)
    CONF = {"sure": ("Sicura", "#5a8a4a"), "prob": ("Probabile", "#b08a2a"), "poss": ("Da verificare", "#b0602a")}
    def im(src, cap): return f'<figure><img loading="lazy" src="{p}img/{src}" alt=""><figcaption>{cap}</figcaption></figure>'
    rows = ""
    for e in IMM["known"]:
        w = byfirst.get(e["new"][0]) or byfirst.get(e["cur"])
        lab, col = CONF[e["c"]]
        link = f'<a href="{p}opere/{w["id"]}/">{esc(w["no"])} {esc(w["t"])}</a>' if w else esc(e["t"])
        shown = "nella scheda" if e["c"] != "poss" else "non ancora nella scheda"
        rows += f"""<section class="rev"><h3>{link} <span class="muted">{esc(e['y'] or '')}</span> <span class="pill" style="border-color:{col};color:{col}">{lab}</span> <span class="muted">· {shown}</span></h3>
<div class="rev-grid">{im(e['cur'], 'Foto attuale (2005)')}{''.join(im('r/'+n, 'Immich: ' + esc(o)) for n, o in zip(e['new'], e['src']))}</div></section>"""
    news = "".join(f"""<section class="rev"><h3>Opera nuova {e['n']} <span class="muted">· fotografia {e['y']}</span></h3>
<div class="rev-grid">{''.join(im('r/'+n, 'Restaurata · ' + esc(o)) + im(n, 'Originale') for n, o in zip(e['i'], e['src']))}</div></section>""" for e in IMM["new"])
    body = f"""{head("Revisione foto — Ubaldo Rizzo", 1, extra='<meta name="robots" content="noindex">')}<body>
{bar(1, "")}
<main class="page">
  <div class="page-head"><p class="kicker">Pagina di lavoro, non collegata dal sito</p><h1 class="title">Revisione delle foto da Immich</h1>
  <p class="lead">Fotografie del 2006–2013 trovate nell'archivio di casa. Per ogni opera: la foto attuale e le nuove, restaurate (sfondo neutro, bilanciamento del colore; nessuna parte dell'opera è generata). «Sicura» e «Probabile» sono già nelle schede; «Da verificare» no. Le opere nuove sono in Archivio, tra le opere da identificare.</p></div>
  <h2>Opere del catalogo ({len(IMM['known'])})</h2>{rows}
  <h2>Opere non nel catalogo ({len(IMM['new'])})</h2>{news}
</main>
<style>.rev{{margin:28px 0;border-top:1px solid var(--line,#ddd);padding-top:14px}}.rev h3{{font-size:1.05rem;margin:0 0 10px}}.rev .muted{{color:#8a8178;font-weight:400}}.pill{{font-size:.75rem;border:1px solid;border-radius:99px;padding:1px 8px;margin-left:6px}}.rev-grid{{display:grid;grid-template-columns:repeat(auto-fill,minmax(200px,1fr));gap:10px}}.rev-grid img{{width:100%;aspect-ratio:4/5;object-fit:contain;background:#eee8df}}.rev-grid figcaption{{font-size:.78rem;color:#8a8178}}</style>
{foot(1)}"""
    write("revisione/index.html", body)

catalogue(); work_pages(); vita(); archivio(); segnala(); journey(); cappella3d()
open(os.path.join(OUT, "README.md"), "w").write("""# Ubaldo Rizzo — catalogo e percorso (v2)

Static site generated by `_src/build.py` from `_src/data.js`. To fix a caption or add a work, edit `_src/data.js` and run `python3 ubaldo-rizzo/_src/build.py`.

- `/` — the journey: an immersive, scroll-driven walk through the work, chapter by chapter
- `/opere/` — catalogue with filters (period, type, medium, search, sort; grid or list)
- `/opere/ur-NNN-title/` — one page per work, with catalogue number and all views
- `/vita/` — year-by-year chronology of the dated works
- `/archivio/` — workshop photos, works to be identified, history of the site
- `/segnala/` — how to report a work

`assets/` holds CSS and JS; `img/` the 2005 archive images; `img/hi/` the 2007–2009 high-resolution photos.
""")
print("built", len(works), "works")
