#!/usr/bin/env python3
"""Build the static site: python3 src/build.py (run from the repository root).

Pages are defined below as HTML fragments; the publication list comes from src/publications.txt.
Writes the HTML pages, favicon, sitemap.xml and robots.txt into the repository root.
The password-protected network/ page is not touched.

Contact addresses are not stored in this script: they are read from the SITE_EMAILS environment
variable (comma-separated) or, if it is not set, from the encoded e-mail links of the current index.html.

Anti-spam: no page contains a plain address or a mailto: link. Each address is written as
<a class="em" data-u=... data-d=...>name [at] domain</a>, with the user and domain parts reversed; a small
script at the end of each page turns it into a normal clickable mailto link in the visitor's browser.
Without JavaScript the reader sees "name [at] domain". The CV PDF uses the same "[at]" form, and the
structured data (JSON-LD) carries no address.
"""
import datetime, html, json, math, os, pathlib, re

ROOT = pathlib.Path(__file__).resolve().parent.parent
SRC = ROOT / "src"
BASE = "https://rizzogianluca.github.io/"
TODAY = datetime.date.today()
ME = "Gianluca Rizzo"
E = html.escape


def load_emails():
    raw = os.environ.get("SITE_EMAILS", "")
    found = [a.strip() for a in raw.split(",") if a.strip()]
    if not found and (ROOT / "index.html").exists():
        idx = (ROOT / "index.html").read_text(encoding="utf-8")
        found = sorted({u[::-1] + "@" + d[::-1] for u, d in re.findall(r'data-u="([^"]+)" data-d="([^"]+)"', idx)})
        if not found:  # pages built before the anti-spam encoding
            found = sorted(set(re.findall(r'mailto:([^"?]+)', idx)))
    em = {"unito": "", "hevs": ""}
    for a in found:
        for k in em:
            if k in a.split("@")[-1]:
                em[k] = a
    if not all(em.values()):
        raise SystemExit("Contact addresses not found: set SITE_EMAILS='address1,address2'")
    return em


EM = load_emails()
def at_text(addr):
    """Human-readable form without an @ sign, e.g. name [at] domain.org."""
    user, dom = addr.split("@")
    return f"{user} [at] {dom}"


def mail_link(addr):
    user, dom = addr.split("@")
    return f'<a class="em" data-u="{E(user[::-1])}" data-d="{E(dom[::-1])}">{E(at_text(addr))}</a>'


MAIL = {k: mail_link(v) for k, v in EM.items()}
MAIL_JS = ("<script>document.querySelectorAll('a.em').forEach(a=>{const r=s=>[...s].reverse().join(''),"
           "e=r(a.dataset.u)+String.fromCharCode(64)+r(a.dataset.d);a.href='mai'+'lto:'+e;a.textContent=e})</script>")

NAV = [("index.html", "Home"), ("research.html", "Research"), ("projects.html", "Projects"),
       ("publications.html", "Publications"), ("teaching.html", "Teaching"),
       ("student-projects.html", "Bachelor, Master &amp; PhD projects"), ("people.html", "People"), ("cv.html", "CV")]
CV_PDF = "cv.pdf"
import hashlib as _h
CSS_VER = _h.md5((ROOT / "style.css").read_bytes()).hexdigest()[:8]

PROFILES = [("Google Scholar", "https://scholar.google.com/citations?user=NzZ5dd8AAAAJ"),
            ("dblp", "https://dblp.org/pid/71/3141"),
            ("ORCID", "https://orcid.org/0000-0001-7129-4972"),
            ("LinkedIn", "https://www.linkedin.com/in/gianlucarizzo")]

# Institutional pages and groups
INST = {
    "unito": "https://www.unito.it",
    "unito_dept": "https://informatica.unito.it",
    "unito_me": "https://informatica.unito.it/persone/gianluca.rizzo",
    "hevs": "https://www.hevs.ch/en",
    "hevs_inst": "https://www.hevs.ch/en/applied-research/research-institute-informatics/",
    "hevs_me": "https://www.hevs.ch/en/collaborateurs/rizzo-1750",
    "hesso_people": "https://people.hes-so.ch/en/profile/2581691189-gianluca-rizzo",
    "hcai": "https://www.hevs.ch/en/applied-research/research-institute-informatics/appitech-lab/",
    "conex": "https://hevs.ch/en/minisites/projects-products/conex-lab",
}

PERSON = {
    "@context": "https://schema.org", "@type": "Person", "name": ME,
    "url": BASE, "image": BASE + "portrait.jpg",
    "jobTitle": ["Associate Professor of Computer Science", "Senior Research Associate"],
    "worksFor": [
        {"@type": "CollegeOrUniversity", "name": "Università di Torino", "url": "https://www.unito.it"},
        {"@type": "CollegeOrUniversity", "name": "HES-SO Valais-Wallis", "url": "https://www.hevs.ch"}],
    "alumniOf": [{"@type": "CollegeOrUniversity", "name": "EPFL"},
                 {"@type": "CollegeOrUniversity", "name": "Politecnico di Torino"}],
    "knowsAbout": ["6G networks", "Wireless networks", "Edge computing", "Gossip learning",
                   "Performance evaluation", "Stochastic geometry", "Network calculus"],
    "sameAs": [u for _, u in PROFILES] + [INST["unito_me"], INST["hevs_me"], INST["hesso_people"]],
}


def page(fname, title, desc, body, jsonld=None, current=None):
    full_title = ME if fname == "index.html" else f"{title} – {ME}"
    url = BASE if fname == "index.html" else BASE + fname
    cur = current or fname
    nav = "".join(f'<li><a href="{f}"{" aria-current=page" if f == cur else ""}>{n}</a></li>' for f, n in NAV)
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(full_title)}</title><meta name="description" content="{E(desc)}">
<link rel="canonical" href="{url}"><link rel="icon" href="favicon.svg" type="image/svg+xml">
<meta property="og:type" content="profile"><meta property="og:title" content="{E(full_title)}"><meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{url}"><meta property="og:image" content="{BASE}portrait.jpg"><meta name="twitter:card" content="summary">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Spectral:wght@500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css?v={CSS_VER}">{ld}</head><body>
<a class="skip" href="#content">Skip to content</a>
<header class="site"><div class="wrap"><a class="brand" href="index.html">{ME}</a><button class="menu" type="button" aria-expanded="false" aria-controls="nav"><span aria-hidden="true"></span>Menu</button><nav id="nav" aria-label="Main"><ul>{nav}</ul></nav></div></header>
<script>document.querySelector('.menu').addEventListener('click',e=>{{const b=e.currentTarget,n=document.getElementById('nav'),o=b.getAttribute('aria-expanded')!=='true';b.setAttribute('aria-expanded',String(o));n.classList.toggle('open',o)}})</script>
<main id="content"><div class="wrap">
{body}
</div></main>
<footer><div class="wrap"><span>© {TODAY.year} {ME} · {MAIL['unito']} · {MAIL['hevs']} · <a href="{INST['unito_me']}">UniTo page</a> · <a href="{INST['hevs_me']}">HES-SO page</a></span><span>Last updated {TODAY.day} {TODAY.strftime('%B %Y')}</span></div></footer>
{MAIL_JS}
</body></html>
"""


# ---------------------------------------------------------------- publications
TYPES = {"J": "Journal articles", "C": "Conference papers", "B": "Book chapters", "P": "Patents",
         "O": "Preprints, posters, reports and theses"}
TYPE_ID = {"J": "journals", "C": "conferences", "B": "chapters", "P": "patents", "O": "other"}
CHIP = {"J": "Journals", "C": "Conferences", "B": "Chapters", "P": "Patents", "O": "Other"}


def load_pubs():
    pubs = []
    for line in (SRC / "publications.txt").read_text(encoding="utf-8").splitlines():
        if not line.strip() or line.startswith("#"):
            continue
        parts = [p.strip() for p in line.split("|")]
        parts += [""] * (7 - len(parts))
        t, year, authors, title, venue, doi, flags = parts[:7]
        fl = [f.strip() for f in flags.split(";") if f.strip()]
        pubs.append(dict(type=t, year=int(year), authors=authors, title=title, venue=venue, doi=doi,
                         selected="selected" in fl,
                         award=next((f[6:] for f in fl if f.startswith("award:")), "")))
    return pubs


def pub_li(p, show_year=True):
    authors = E(p["authors"]).replace(ME, f"<b>{ME}</b>")
    title = E(p["title"])
    if p["doi"]:
        title = f'<a href="https://doi.org/{E(p["doi"])}">{title}</a>'
    award = f' <span class="badge">{E(p["award"])}</span>' if p["award"] else ""
    year = f", {p['year']}" if show_year and str(p["year"]) not in p["venue"] else ""
    return (f'<li data-type="{TYPE_ID[p["type"]]}"><span class="t">{title}</span>{award}'
            f'<span class="a">{authors}</span><span class="m">{E(p["venue"])}{year}</span></li>')


def publications_page(pubs):
    sel = sorted([p for p in pubs if p["selected"]], key=lambda p: -p["year"])
    out = ['<h1>Publications</h1>',
           '<p class="lede">Citation metrics are on '
           + ", ".join(f'<a href="{u}">{n}</a>' for n, u in PROFILES[:3]) + '.</p>',
           '<h2 id="selected">Selected publications</h2><ol class="pubs">' + "".join(pub_li(p) for p in sel) + '</ol>',
           '<h2 id="all">All publications</h2>',
           '<div class="filter" role="search"><label for="q" class="sr">Search publications</label>'
           '<input id="q" type="search" placeholder="Search title, author, venue or year" autocomplete="off">'
           '<div class="chips" role="group" aria-label="Publication type">'
           '<button type="button" aria-pressed="true" data-f="all">All</button>'
           + "".join(f'<button type="button" aria-pressed="false" data-f="{TYPE_ID[t]}">{CHIP[t]}</button>' for t in TYPES)
           + '</div><p id="count" class="note" aria-live="polite"></p></div>']
    for t, name in TYPES.items():
        items = sorted([p for p in pubs if p["type"] == t], key=lambda p: -p["year"])
        out.append(f'<section class="ptype" id="{TYPE_ID[t]}"><h3>{name} <span class="note">({len(items)})</span></h3>')
        cur = None
        for p in items:
            if p["year"] != cur:
                if cur is not None:
                    out.append("</ol>")
                cur = p["year"]
                out.append(f'<h4 class="yr">{cur}</h4><ol class="pubs">')
            out.append(pub_li(p, show_year=False))
        out.append("</ol></section>")
    out.append("""<script>
(()=>{const q=document.getElementById('q'),chips=[...document.querySelectorAll('.chips button')],count=document.getElementById('count');let f='all';
const run=()=>{const s=q.value.trim().toLowerCase();let n=0;
document.querySelectorAll('.ptype').forEach(sec=>{let any=0;sec.querySelectorAll('h4.yr').forEach(h=>{const ol=h.nextElementSibling;let vis=0;
ol.querySelectorAll('li').forEach(li=>{const ok=(f==='all'||li.dataset.type===f)&&(!s||(li.textContent+' '+h.textContent).toLowerCase().includes(s));li.hidden=!ok;if(ok){vis++;n++}});
h.hidden=ol.hidden=!vis;any+=vis});sec.hidden=!any});
count.textContent=(s||f!=='all')?n+(n===1?' publication':' publications'):''};
q.addEventListener('input',run);chips.forEach(b=>b.addEventListener('click',()=>{f=b.dataset.f;chips.forEach(c=>c.setAttribute('aria-pressed',String(c===b)));run()}));})();
</script>""")
    return "\n".join(out)


# ---------------------------------------------------------------- content
NEWS = [
    ("2026-09", "<a href=\"https://doi.org/10.1109/TMC.2026.3682564\">“Floating Gossip: Serverless Distributed Learning in Dynamic Scenarios”</a> is published in <i>IEEE Transactions on Mobile Computing</i>."),
    ("2026-06", "Papers presented at ICAPS 2026 on <a href=\"https://doi.org/10.1609/icaps.v36i1.42854\">robust decentralised multi-agent planning</a> and at EuCNC &amp; 6G Summit 2026 on the <a href=\"https://doi.org/10.1109/EuCNC/6GSummit68295.2026.11577429\">UNITY-6G architecture</a>."),
    ("2026-03", "I was General Chair of <a href=\"https://2026.wons-conference.org/\">IEEE WONS 2026</a>, held in Crans-Montana, Switzerland, on 2–4 March."),
    ("2025-11", "Best Paper Award runner-up at <a href=\"https://www.ieee-smartiot.org\">IEEE SmartIoT 2025</a> (Sydney) for our paper on <a href=\"https://doi.org/10.1109/SmartIoT66867.2025.00014\">energy-aware load shifting in SWIPT IoT networks</a>."),
    ("2025-01", "Start of the Horizon Europe project <a href=\"https://unity-6g.eu/\">UNITY-6G</a> on sustainable, Open RAN-based 6G networks (<a href=\"projects.html#unity-6g\">more</a>)."),
    ("2024-12", "I joined the <a href=\"https://informatica.unito.it\">Department of Computer Science</a> of the Università di Torino as Associate Professor."),
]


def fmt_month(ym):
    return datetime.date(int(ym[:4]), int(ym[5:]), 1).strftime("%b %Y")


THEMES = [
    ("sustainable-6g", "Sustainable 6G networks", "Energy-aware 6G orchestration, network sharing and wireless power transfer.",
     "Energy-aware orchestration of multi-domain 6G networks, network sharing between operators, and "
     "simultaneous wireless information and power transfer (SWIPT) for battery-less IoT devices.", "UNITY-6G"),
    ("moving-networks", "Moving networks", "Vehicles and drones as mobile base stations.",
     "Vehicles and drones as mobile base stations: when they pay off, how to steer them through a city, and "
     "how they change the capacity, resilience and energy use of radio access networks.", "DyMoNet, MOBNET, MOVNET"),
    ("edge-learning", "Decentralised learning at the edge", "Gossip learning and serverless learning among mobile devices.",
     "Gossip learning and serverless distributed learning among mobile devices, with performance models that "
     "tell when cooperation between devices is worth its cost.", "ABIDI, GANDEEP"),
    ("multi-agent", "Multi-agent coordination", "Decentralised planning for teams of autonomous agents.",
     "Decentralised planning for teams of autonomous agents, such as drones collecting data, in dynamic "
     "environments where agents can fail or be lost.", "RADIANT"),
    ("opportunistic", "Opportunistic and resilient communication", "Floating Content and post-disaster communication.",
     "Floating Content and other infrastructure-less ways of sharing information locally, for vehicular "
     "networks and post-disaster scenarios.", "CONTACT, NOSE"),
    ("methods", "Performance modelling methods", "Stochastic geometry, mean field, queueing and network calculus.",
     "The analytical toolbox behind this work: stochastic geometry, mean-field approximations, coupled "
     "processor models, queueing theory and network calculus.", ""),
]

KEY_PAPERS = {
    "sustainable-6g": ["Green Operations of SWIPT Networks: The Role of End-User Devices",
                       "Energy-Aware Multi-Domain Orchestration Architecture for Sustainable 6G Networks",
                       "Sharing is Caring: Analysis of Hybrid Network Sharing Strategies for Energy Efficient Multi-Operator Cellular Systems"],
    "moving-networks": ["Modeling and Optimization of Vehicular-Enhanced Urban RANs with In-Band Backhaul",
                        "Mobile Networks on the Move: Optimizing Moving Base Stations Dynamics in Urban Scenarios",
                        "Feasibility of Using Mobile Base Stations for Improved Resilience and Reduced Energy Footprint"],
    "edge-learning": ["Floating Gossip: Serverless Distributed Learning in Dynamic Scenarios",
                      "A Gossip Learning Approach to Urban Trajectory Nowcasting for Anticipatory RAN Management",
                      "V-Edge: Virtual Edge Computing as an Enabler for Novel Microservices and Cooperative Computing"],
    "multi-agent": ["Decentralized Coordination for Multi-Agent Data Collection in Dynamic Environments",
                    "Survive and Thrive: Decentralized Multi-Agent Coordination under Attrition Risks",
                    "United We Stand: Decentralized Multi-Agent Planning with Attrition"],
    "opportunistic": ["Storage Capacity of Opportunistic Information Dissemination Systems",
                      "Performance Modeling of Vehicular Floating Content in Urban Settings",
                      "Floater: Post-Disaster Communications via Floating Content"],
    "methods": ["A Stochastic Geometry Approach to Performance Modeling of SWIPT Vehicular Networks",
                "An Analytical Approach to Performance Analysis of Coupled Processor Systems",
                "Stability and Delay Bounds in Heterogeneous Networks of Aggregate Schedulers"],
}


def home(pubs):
    news = "".join(f'<div><time datetime="{d}">{fmt_month(d)}</time><p>{t}</p></div>' for d, t in NEWS)
    cards = "".join(f'<a class="card" href="research.html#{i}"><strong>{n}</strong><span>{E(short)}</span></a>'
                    for i, n, short, _, _ in THEMES[:4])
    links = "".join(f'<a href="{u}">{n}</a>' for n, u in PROFILES) + '<a href="cv.html">CV</a>'
    return f"""<div class="hero"><div>
<h1>Gianluca Rizzo</h1>
<p class="role">Associate Professor of Computer Science, Dipartimento di Informatica, Università di Torino<br>Senior Research Associate, <a href="{INST['conex']}">ConEx Lab</a>, <a href="{INST['hcai']}">Human‑Centered AI Lab</a>, HES-SO Valais-Wallis</p>
<p class="lede">I design and analyse distributed and wireless systems: how networks, devices and learning algorithms should be organised to be efficient, sustainable and dependable. My current work focuses on energy-aware 6G networks, mobile base stations and decentralised learning at the network edge, using stochastic geometry, mean-field theory, queueing models and network calculus.</p>
<ul class="aff">
<li><strong><a href="{INST['unito']}">Università di Torino</a> – <a href="{INST['unito_dept']}">Department of Computer Science</a></strong><span>Via Pessinetto 12, 10149 Torino, Italy · {MAIL['unito']}</span><span class="aff-links"><a href="{INST['unito_me']}">My UniTo page</a></span></li>
<li><strong><a href="{INST['hevs']}">HES-SO Valais-Wallis</a> – <a href="{INST['hevs_inst']}">Institute of Informatics</a></strong><span>Technopole 3, CH-3960 Sierre, Switzerland · {MAIL['hevs']}</span><span class="aff-links"><a href="{INST['hevs_me']}">My HES-SO Valais page</a> · <a href="{INST['hesso_people']}">People@HES-SO profile</a></span></li>
</ul>
<div class="links">{links}</div>
</div>
<figure><img class="portrait" src="portrait.jpg" alt="Portrait of Gianluca Rizzo" width="640" height="579" fetchpriority="high"></figure>
</div>
<h2>Research</h2>
<div class="cards">{cards}</div>
<p class="more"><a href="research.html">All research themes →</a></p>
<h2>News</h2>
<div class="news">{news}</div>
<aside class="callout"><h2>Prospective students</h2>
<p>I supervise Bachelor's, Master's and PhD projects at the Università di Torino and at HES-SO Valais-Wallis on 6G networks, edge learning and network performance modelling. <a href="student-projects.html">See Bachelor, Master and PhD projects →</a></p></aside>
"""


def research(pubs):
    by_title = {p["title"]: p for p in pubs}
    out = ['<h1>Research</h1>',
           '<p class="lede">My work is about designing networked systems that do more with less: less energy, less infrastructure, less coordination. '
           'I combine analytical performance models with optimisation and learning, and validate the results with simulations, testbeds and prototypes.</p>',
           '<nav class="toc" aria-label="Research themes"><ul>' + "".join(f'<li><a href="#{i}">{n}</a></li>' for i, n, *_ in THEMES) + '</ul></nav>']
    for i, name, _, txt, proj in THEMES:
        papers = "".join(pub_li(by_title[t]) for t in KEY_PAPERS[i] if t in by_title)
        pj = f'<p class="note">Projects: {E(proj)}</p>' if proj else ""
        out.append(f'<section class="theme" id="{i}"><h2>{name}</h2><p>{E(txt)}</p>{pj}<h3>Key papers</h3><ol class="pubs">{papers}</ol></section>')
    out.append('<h2>Industry collaboration</h2><p>Since 2009 I have worked as a technical consultant for the avionic and utility-communications industry in Switzerland, '
               'on the modelling, analysis and validation of critical communication systems and deterministic networks. Earlier I designed utility '
               'communication networks at ABB and optical-network resilience solutions at Telecom Italia Lab, work that led to a patent granted in the US and Europe.</p>')
    return "\n".join(out)


PROJECTS = [
    ("unity-6g", "UNITY-6G", "UNified archITecture for Open RAN-enabled Distributed, Scalable and SustainabilitY-enhanced 6G Networks",
     "Horizon Europe – Smart Networks and Services Joint Undertaking (HORIZON-JU-SNS-2024-STREAM-B-01-01)", "Principal Investigator", "2025–2027", True),
    ("gandeep", "GANDEEP", "Exploring the potential of synergetic GANs in research and industry",
     "FAIR Foundation, Spoke 6 “Symbiotic AI”", "Principal Investigator", "2024–2025", False),
    ("radiant", "RADIANT", "Distributed multi-agent coordination in dynamic environments", "Hasler Foundation", "Principal Investigator", "2024", False),
    ("dymonet", "DyMoNet", "Dynamic mobile networks", "Swiss National Science Foundation (SNSF)", "Principal Investigator", "2022–2025", False),
    ("abidi", "ABIDI", "Context-aware and veracious Big Data analytics for industrial IoT", "CHIST-ERA", "Principal Investigator", "2019–2024", False),
    ("contact", "CONTACT", "Context and content aware communications for QoS support in VANETs", "SNSF (200021E-164205)", "Principal Investigator", "2016–2020", False),
    ("movnet", "MOVNET", "Moving base stations for a sustainable access", "RCSO ISNET", "Principal Investigator", "2018–2020", False),
    ("mobnet", "MOBNET", "Moving base stations for sustainable 5G systems", "Hasler Foundation", "Principal Investigator", "2018–2019", False),
    ("nose", "NOSE", "A nomadic scalable ecosystem for pervasive sensing, computing and communication", "RCSO ISNET", "Principal Investigator", "2015–2016", False),
    ("trend", "TREND", "Towards real energy-efficient network design", "EU FP7", "Investigator", "2012–2014", False),
    ("iot6", "IoT6", "Universal integration of the Internet of Things through an IPv6-based service-oriented architecture", "EU FP7", "Investigator", "2011–2014", False),
]

EU_FLAG = ('<svg class="euflag" viewBox="0 0 30 20" role="img" aria-label="Flag of the European Union"><rect width="30" height="20" fill="#039"/>'
           + "".join(f'<text x="{15 + 6.4 * math.sin(k * math.pi / 6):.2f}" y="{10 - 6.4 * math.cos(k * math.pi / 6) + 1.2:.2f}" '
                     f'font-size="3.4" fill="#fc0" text-anchor="middle">★</text>' for k in range(12)) + '</svg>')


PROJECT_URLS = {"unity-6g": "https://unity-6g.eu/"}


def projects():
    def card(p):
        i, acr, title, funder, role, years, _ = p
        name = f'<a href="{PROJECT_URLS[i]}">{acr}</a>' if i in PROJECT_URLS else acr
        return (f'<article class="proj" id="{i}"><h3>{name} <span class="note">{years}</span></h3><p class="t">{E(title)}</p>'
                f'<p class="m">{E(funder)} · {role}</p></article>')
    cur = "".join(card(p) for p in PROJECTS if p[6])
    past = "".join(card(p) for p in PROJECTS if not p[6])
    return f"""<h1>Projects</h1>
<p class="lede">Funded research projects I lead or have taken part in. I regularly prepare Horizon Europe and national proposals and welcome contacts from potential partners.</p>
<h2>Current</h2><div class="projs">{cur}</div>
<div class="ack">{EU_FLAG}<p>UNITY-6G has received funding from the Smart Networks and Services Joint Undertaking (SNS JU) under the European Union's Horizon Europe research and innovation programme (grant agreement No 101192650) and from the Swiss State Secretariat for Education, Research and Innovation (SERI).</p></div>
<h2>Completed</h2><div class="projs">{past}</div>
"""


TEACHING = [
    # (course, code/notes, course page URL, institution and programme, years, current)
    ("Complementi di Reti (Advanced Computer Networks)", "INF0342 · taught in English, with Michele Garetto",
     "https://laurea.informatica.unito.it/do/corsi.pl/Show?_id=pgrx", "Università di Torino – BSc Computer Science", "2025–", True),
    ("Basi di Dati (Databases)", "MFN0602", "https://laurea.informatica.unito.it/do/corsi.pl/Show?_id=hlun",
     "Università di Torino – BSc Computer Science", "2024–", True),
    ("Sistemi informativi e gestione delle reti aziendali (Information Systems and Network Management)", "SAA0069",
     "https://saa.campusnet.unito.it/do/corsi.pl/Show?_id=vvv2",
     "Università di Torino – BSc Management dell'Informazione e della Comunicazione Aziendale", "2024–2026", False),
    ("Computer Networks", "", "https://hevs.ch/en/schools/school-of-management/business-information-technology",
     "HES-SO Valais-Wallis – BSc Business Information Technology (programme page)", "2021–22, 2023–24", False),
    ("Computer Networks (Sistemi Informativi II)", "", "", "University of Foggia", "2021–2025", False),
    ("Big Data", "", "", "University of Foggia", "2024", False),
    ("Mobile Networks and IoT", "", "", "University of Foggia", "2024", False),
    ("Multimedia Management and Processing", "", "", "University of Foggia", "2020–2023", False),
    ("Internet of Things: IoT protocols and communications", "", "", "EPFL", "", False),
    ("Post-Disaster Communications and Emergency Networks", "Training school", "", "COST Action RECODIS, Brussels", "", False),
    ("Shared Medium and LAN Technologies", "Adjunct professor", "", "Universidad Carlos III de Madrid", "2009–2011", False),
    ("TCP/IP Networking (Computer Networks)", "Teaching assistant", "https://edu.epfl.ch/studyplan/fr/master/informatique-cybersecurity/coursebook/tcp-ip-networking-COM-407",
     "EPFL", "2004–2008", False),
    ("Performance Evaluation", "Teaching assistant", "https://leboudec.github.io/perfeval", "EPFL", "2004–2008", False),
    ("C and C++ Programming", "Teaching assistant", "", "EPFL", "2004–2008", False),
    ("Java Programming", "Teaching assistant", "", "Politecnico di Torino", "", False),
]


def teaching():
    def row(t):
        name, note, url, inst, years, _ = t
        title = f'<a href="{E(url)}">{E(name)}</a>' if url else E(name)
        note = f'<span class="note">{E(note)}</span>' if note else ""
        return f'<tr><td>{title}{"<br>" + note if note else ""}</td><td>{E(inst)}</td><td class="yrs">{E(years) or "–"}</td></tr>'
    head = '<thead><tr><th>Course</th><th>Institution and programme</th><th>Years</th></tr></thead>'
    cur = "".join(row(t) for t in TEACHING if t[5])
    past = "".join(row(t) for t in TEACHING if not t[5])
    return f"""<h1>Teaching</h1>
<p class="lede">Course titles link to the official course pages, where you find the syllabus, schedule and exam information.</p>
<table class="tbl teach">{head}<tbody>
<tr class="grp"><th colspan="3">Current</th></tr>{cur}
<tr class="grp"><th colspan="3">Earlier</th></tr>{past}
</tbody></table>
<p class="more">Looking for a thesis or a project? See <a href="student-projects.html">Bachelor, Master and PhD projects</a>.</p>
"""


# Bachelor, Master and PhD projects. Rule: one project, one description, one sub-page (sp-<slug>.html).
# Ongoing BSc/MSc projects are listed by topic only (no student names); PhD students appear on the People page.
# Source: Notion (student status page, research-idea notes, PhD position texts), November 2026.
# Fields: slug, title, status (ongoing/open/past), context, summary (one line for the overview),
#         description (paragraphs), work (bullets), background (open topics), related (publication titles), theme (research anchor)
SP = {
 "bachelor": [
  dict(slug="urban-network-simulator", status="ongoing", title="Urban mobile network performance simulator",
       context="Università di Torino · Bachelor thesis",
       summary="A simulator to estimate the coverage and capacity of a mobile network in a city.",
       description=["The goal is a simulation tool that, given the position of base stations and the distribution of users in a city, estimates the coverage and capacity that a mobile network can offer.",
                    "The simulator is meant as a basis for later studies on dynamic networks, such as base stations mounted on vehicles."],
       work=["Model base stations, users and radio propagation in an urban area", "Implement and validate the simulator", "Compare network configurations through simulation experiments"],
       related=["Mobile Networks on the Move: Optimizing Moving Base Stations Dynamics in Urban Scenarios"], theme="moving-networks"),
  dict(slug="can-tsn-mapping", status="ongoing", title="Mapping CAN/CAN-FD in-vehicle traffic onto Time-Sensitive Networking",
       context="Università di Torino · internship and Bachelor thesis",
       summary="Carry in-vehicle CAN/CAN-FD traffic over TSN while keeping its timing guarantees.",
       description=["Vehicles are moving from CAN and CAN-FD buses to Ethernet-based Time-Sensitive Networking (TSN). This project studies how CAN/CAN-FD traffic can be mapped onto TSN, and back, while preserving its timing requirements.",
                    "The work starts with a gap analysis between the two technologies and continues with a mapping and its evaluation."],
       work=["Analyse the timing requirements of CAN/CAN-FD traffic", "Compare them with the mechanisms offered by TSN", "Design and evaluate a mapping between the two"],
       related=["Stability and Delay Bounds in Heterogeneous Networks of Aggregate Schedulers"], theme="methods"),
  dict(slug="carbon-aware-edge", status="ongoing", title="Carbon- and cost-aware energy accounting for edge data centres",
       context="Università di Torino · internship and thesis, with an industrial partner of UNITY-6G · starting",
       summary="How much CO₂ and money do edge workloads really save when energy is valued at the local grid's carbon intensity?",
       description=["Edge data centres draw power from distribution grids whose carbon intensity changes from place to place and hour to hour. This project asks how much CO₂ and money energy-saving mechanisms for edge computing really save when energy is valued at the local (locational) carbon intensity of the grid rather than at a national average.",
                    "It combines carbon flow tracing in distribution grids with live energy measurements from a Kubernetes cluster."],
       work=["Compute hourly carbon-intensity profiles at the grid node hosting an edge site, using carbon flow tracing", "Build a service that converts measured energy into cost and CO₂ in near real time", "Compare average and locational carbon accounting, and the effect of shifting deferrable workloads in time"],
       related=["Energy-Aware Multi-Domain Orchestration Architecture for Sustainable 6G Networks"], theme="sustainable-6g"),
  dict(slug="road-ice-monitoring", status="open", title="Road-ice monitoring with sensors on buses",
       context="HES-SO Valais-Wallis or Università di Torino · Bachelor thesis",
       summary="Road-surface data from sensors on public buses, sent over LoRaWAN or NB-IoT.",
       description=["Icy roads are a major winter risk in mountain regions. Public buses travel the same roads every day and can carry sensors that measure road-surface conditions along their routes.",
                    "This project builds and evaluates a first version of such a system, sending the measurements over low-power wide-area networks (LoRaWAN or NB-IoT) and turning them into a map of road conditions."],
       work=["Choose sensors and an IoT connectivity option (LoRaWAN or NB-IoT)", "Collect and clean data along bus routes", "Visualise road conditions and assess coverage, delay and energy use"],
       background="Interest in IoT and data analysis; programming in Python.", related=[], theme="opportunistic"),
  dict(slug="gossip-learning-devices", status="open", title="Gossip learning on real devices",
       context="Università di Torino or HES-SO Valais-Wallis · Bachelor thesis",
       summary="Serverless distributed learning on phones or Raspberry Pis: accuracy, energy and traffic.",
       description=["In gossip learning, devices train machine-learning models together by exchanging models with their neighbours, without a central server. Most results so far come from simulations.",
                    "This project implements gossip learning on real devices and measures what happens in practice."],
       work=["Implement a gossip learning protocol on phones or Raspberry Pis", "Run experiments with a simple learning task", "Measure accuracy, energy consumption and network traffic"],
       background="Programming in Python; basic machine learning.",
       related=["Floating Gossip: Serverless Distributed Learning in Dynamic Scenarios", "The Upsides of Turbulence: Baselining Gossip Learning in Dynamic Settings"], theme="edge-learning"),
  dict(slug="emergency-info-sharing", status="open", title="Opportunistic information sharing for emergencies",
       context="Università di Torino or HES-SO Valais-Wallis · Bachelor thesis",
       summary="An app that shares information between nearby devices when the network is down.",
       description=["After a disaster, the mobile network is often unavailable exactly when people need information most. Devices can still exchange messages directly with those nearby, so that information \"floats\" in the area where it is relevant.",
                    "This project builds or evaluates an app based on this idea, building on our earlier Floater prototype."],
       work=["Study the Floating Content approach and existing prototypes", "Implement or extend an app for device-to-device sharing", "Evaluate it in experiments or simulations"],
       background="Mobile or network programming.",
       related=["Floater: Post-Disaster Communications via Floating Content", "Situation Awareness via Information Hovering in Post-Disaster Communications"], theme="opportunistic"),
 ],
 "master": [
  dict(slug="moving-bs-sumo", status="ongoing", title="Moving base stations in a realistic urban scenario",
       context="Università di Torino · thesis co-supervised with TU Berlin",
       summary="Vehicles as mobile base stations, evaluated with SUMO and the Luxembourg LuST traffic scenario.",
       description=["Base stations mounted on vehicles can bring capacity where and when it is needed. This thesis evaluates the idea in a realistic city, using the SUMO traffic simulator and the Luxembourg (LuST) traffic scenario."],
       work=["Set up the urban mobility scenario in SUMO", "Model mobile base stations and user demand", "Evaluate capacity, resilience and energy compared with fixed infrastructure"],
       related=["Feasibility of Using Mobile Base Stations for Improved Resilience and Reduced Energy Footprint", "Assessing the Benefits of Ground Vehicles as Moving Urban Base Stations"], theme="moving-networks"),
  dict(slug="age-of-information-iot", status="open", title="Age of information in IoT networks",
       context="Università di Torino · Master thesis",
       summary="Mean-field models of how fresh the information spread by gossip is in large IoT deployments.",
       description=["In many IoT applications what matters is not only whether information arrives, but how recent it is. This project develops mean-field models of the age of information when updates spread through a large IoT network by gossip, and uses them to tune the protocol."],
       work=["Model gossip-based dissemination in a large IoT network", "Derive mean-field approximations of the age of information", "Validate them by simulation and use them to optimise the protocol"],
       background="Probability and stochastic processes; programming for simulation.",
       related=["Storage Capacity of Opportunistic Information Dissemination Systems"], theme="methods"),
  dict(slug="handovers-at-scale", status="open", title="Handovers at scale",
       context="Università di Torino · Master thesis",
       summary="Mean-field approximations of handover rates and their cost in dense, mobile networks.",
       description=["In dense networks with many mobile users, handovers between cells become frequent and costly. This project uses mean-field approximations to compute handover rates efficiently in large networks and to study how network design affects them."],
       work=["Model user mobility and cell layout", "Develop a mean-field approximation of handover rates", "Compare it with simulation and use it to evaluate network configurations"],
       background="Probability and stochastic processes; programming for simulation.",
       related=["A Gossip Learning Approach to Urban Trajectory Nowcasting for Anticipatory RAN Management"], theme="methods"),
  dict(slug="network-calculus-learning", status="open", title="Performance guarantees for distributed learning",
       context="Università di Torino · Master thesis",
       summary="Network calculus to bound the delay and convergence of distributed and federated learning.",
       description=["Distributed and federated learning algorithms run over networks whose delays affect how fast they converge. Network calculus provides worst-case bounds on delays in networks. This project uses it to derive guarantees on the performance of learning algorithms."],
       work=["Model the communication pattern of a distributed learning algorithm", "Apply network calculus to bound its delays", "Relate the bounds to convergence and validate them experimentally"],
       background="Interest in theory; probability or queueing; basic machine learning.",
       related=["Stability and Delay Bounds in Heterogeneous Networks of Aggregate Schedulers", "Floating Gossip: Serverless Distributed Learning in Dynamic Scenarios"], theme="methods"),
  dict(slug="communication-efficient-learning", status="open", title="Communication-efficient federated and gossip learning",
       context="Università di Torino · Master thesis",
       summary="Compress models and updates to cut traffic and energy while keeping accuracy.",
       description=["Exchanging full models is the main cost of federated and gossip learning on mobile devices. This project studies compression of models and updates, and when it reduces traffic and energy without hurting accuracy."],
       work=["Survey compression techniques for distributed learning", "Integrate them into a federated or gossip learning framework", "Measure the trade-off between accuracy, traffic and energy"],
       background="Machine learning; programming in Python.",
       related=["Context-Aware Orchestration of Energy-Efficient Gossip Learning Schemes", "GRAPE: Gossip-Based Representation Alignment Using Prototypical Embeddings for Heterogeneous IoT Devices"], theme="edge-learning"),
  dict(slug="leo-emergency", status="open", title="LEO satellites for emergency communications",
       context="Università di Torino · Master thesis",
       summary="Stochastic geometry models of low-Earth-orbit satellite networks to choose energy-optimal transmit powers.",
       description=["Low-Earth-orbit (LEO) satellite constellations can provide connectivity when ground networks fail. This project adapts stochastic geometry models developed for energy-efficient cellular networks to LEO networks, to choose transmit powers that save energy while guaranteeing service to first responders."],
       work=["Model a LEO constellation and its users with stochastic geometry", "Derive coverage and energy metrics", "Optimise transmit power under service constraints"],
       background="Probability; interest in wireless communications.",
       related=["Energy-Optimal Base Station Density in Cellular Access Networks with Sleep Modes", "A Stochastic Geometry Approach to Performance Modeling of SWIPT Vehicular Networks"], theme="methods"),
  dict(slug="wireless-power", status="open", title="Wireless power for vehicles and IoT",
       context="Università di Torino · Master thesis",
       summary="Wireless power transfer to battery-less sensors and vehicles: coverage, energy and cost.",
       description=["Simultaneous wireless information and power transfer (SWIPT) lets networks power small devices over the air. This project assesses where wireless power transfer is worth it, for battery-less IoT sensors and for vehicles, in terms of coverage, energy and cost."],
       work=["Model a network that delivers both data and power", "Evaluate coverage and energy efficiency", "Identify configurations and scenarios where it pays off"],
       background="Probability; interest in wireless networks.",
       related=["Green Operations of SWIPT Networks: The Role of End-User Devices", "Energy-Aware Load Shifting in SWIPT-Enabled IoT Networks"], theme="sustainable-6g"),
  dict(slug="edge-economics", status="open", title="Economics of edge computing",
       context="Università di Torino · Master thesis",
       summary="Cost models to decide where and when operators should deploy edge (MEC) resources.",
       description=["Edge computing brings computation close to users, but deploying it everywhere is expensive. This project builds cost and demand models to decide where and when operators should deploy edge (MEC) resources."],
       work=["Model demand for edge services and deployment costs", "Formulate the deployment decision as an optimisation problem", "Evaluate strategies in realistic scenarios"],
       background="Optimisation or economics of networks; programming.",
       related=["V-Edge: Virtual Edge Computing as an Enabler for Novel Microservices and Cooperative Computing"], theme="edge-learning"),
 ],
 "phd": [
  dict(slug="phd-moving-networks", status="ongoing", title="Moving networks: vehicles as mobile base stations in urban radio access networks",
       context="PhD thesis of Laura Finarelli · HES-SO Valais-Wallis, with TU Berlin",
       summary="When and how vehicles acting as base stations improve urban radio access networks.",
       description=["This PhD studies networks in which part of the radio access infrastructure moves: base stations mounted on vehicles that follow city traffic. It develops models and optimisation methods to decide when such moving networks pay off in capacity and energy, and how to operate them."],
       work=["Models of vehicular-enhanced radio access networks with in-band backhaul", "Optimisation of the dynamics of moving base stations", "Energy-efficient network sharing between operators"],
       related=["Modeling and Optimization of Vehicular-Enhanced Urban RANs with In-Band Backhaul", "Mobile Networks on the Move: Optimizing Moving Base Stations Dynamics in Urban Scenarios", "Sharing is Caring: Analysis of Hybrid Network Sharing Strategies for Energy Efficient Multi-Operator Cellular Systems"], theme="moving-networks"),
  dict(slug="phd-sustainable-6g", status="ongoing", title="Energy-aware orchestration and digital twins for sustainable 6G networks",
       context="PhD thesis of Berk Buzcu · HES-SO Valais-Wallis, within UNITY-6G",
       summary="Orchestrating multi-domain 6G networks to cut their energy footprint, with digital twins.",
       description=["This PhD studies how to orchestrate 6G networks spanning several technological domains so that they use less energy, and how digital twins of the network can support these decisions. It is carried out within the Horizon Europe project UNITY-6G."],
       work=["Energy-aware multi-domain orchestration architectures", "Digital twins for intent-driven, sustainable network management"],
       related=["Energy-Aware Multi-Domain Orchestration Architecture for Sustainable 6G Networks", "Modular Multi-Domain Digital Twin Architecture: Sustainable Intent-Driven 6G Management"], theme="sustainable-6g"),
  dict(slug="phd-6g-wireless-2024", status="past", title="6G wireless communications",
       context="PhD student / research assistant position · HES-SO Valais-Wallis · 2024",
       summary="PhD student / research assistant position at HES-SO Valais-Wallis, 2024.",
       description=["PhD student and research assistant position on 6G wireless communications at the Institute of Informatics of HES-SO Valais-Wallis, advertised in 2024. The position has been filled."],
       work=[], related=[], theme="sustainable-6g"),
  dict(slug="phd-drone-6g-2022", status="past", title="Drone-based 6G communications",
       context="PhD position · HES-SO Valais-Wallis · 2022",
       summary="PhD position at HES-SO Valais-Wallis, 2022.",
       description=["PhD position on drone-based 6G communications at HES-SO Valais-Wallis, advertised in 2022. The position has been filled."],
       work=[], related=[], theme="moving-networks"),
 ],
}
LEVEL_INFO = {
    "bachelor": ("Bachelor projects", "Bachelor's theses and final internships for students of Computer Science at the Università di Torino and of Business Information "
                 "Technology at HES-SO Valais-Wallis. A Bachelor project typically focuses on implementation, simulation or measurement, with a clear "
                 "and achievable goal for the duration of the thesis.", "Open topics"),
    "master": ("Master projects", "Master's theses and semester projects for students of the Master's degree in Computer Science at the Università di Torino and for "
               "students from partner universities. A Master project tackles an open research question, combining a model or an algorithm with its "
               "evaluation; strong theses often lead to a publication at an international conference.", "Open topics"),
    "phd": ("PhD projects", "PhD positions are funded through research projects at the Università di Torino and at HES-SO Valais-Wallis, often jointly with "
            "partner universities. Candidates should hold (or be about to obtain) a Master's degree in computer science, electrical or "
            "telecommunications engineering, or a related field, with a solid background in networking, probability or machine learning. "
            "Open positions are announced on this site and on LinkedIn; spontaneous applications from strong candidates are welcome.", "Past PhD positions"),
}
STATUS_LABEL = {"ongoing": "Ongoing", "open": "Open topic", "past": "Past position"}
LEVEL_LABEL = {"bachelor": "Bachelor", "master": "Master", "phd": "PhD"}
SP_INDEX = "student-projects.html"


def sp_file(item):
    return f"sp-{item['slug']}.html"


def student_projects():
    toc = "".join(f'<li><a href="#{lv}">{LEVEL_INFO[lv][0]}</a></li>' for lv in SP)
    secs = []
    for lv, items in SP.items():
        title, intro, open_title = LEVEL_INFO[lv]
        ongoing = "".join(f'<li><a href="{sp_file(i)}">{E(i["title"])}</a><span>{E(i["context"])}</span></li>' for i in items if i["status"] == "ongoing")
        cards = "".join(f'<a class="card" href="{sp_file(i)}"><strong>{E(i["title"])}</strong><span>{E(i["summary"])}</span></a>'
                        for i in items if i["status"] != "ongoing")
        secs.append(f'<section class="level" id="{lv}"><h2>{title}</h2><p>{E(intro)}</p>'
                    + (f'<h3>Ongoing</h3><ul class="ongoing">{ongoing}</ul>' if ongoing else "")
                    + (f'<h3>{open_title}</h3><div class="cards">{cards}</div>' if cards else "") + '</section>')
    return f"""<h1>Bachelor, Master and PhD projects</h1>
<p class="lede">I supervise Bachelor's and Master's theses, internships and PhD students at the Università di Torino and at HES-SO Valais-Wallis. Projects are linked to my <a href="research.html">research</a> and often to ongoing <a href="projects.html">funded projects</a> with European partners. Select a project to read its description.</p>
<nav class="toc" aria-label="Levels"><ul>{toc}<li><a href="#apply">How to apply</a></li></ul></nav>
{"".join(secs)}
<section id="apply"><h2>How to apply</h2>
<p>Write to me by email with your CV, your transcript of records, the level of project you are looking for (Bachelor, Master or PhD) and a few lines on the topic or kind of work that interests you. Open topics are starting points: we shape the final project together. Useful background: computer networks, probability, and programming in Python or C/C++.</p></section>
<h2>Resources for students</h2>
<ul class="plain"><li><a href="https://leboudec.github.io/leboudec/resources/paper.html">How to write a paper</a>, by Jean-Yves Le Boudec</li></ul>
"""


def sp_page(level, item, pubs):
    by_title = {p["title"]: p for p in pubs}
    theme = next((n for i, n, *_ in THEMES if i == item["theme"]), "")
    desc = "".join(f"<p>{E(x)}</p>" for x in item["description"])
    work_h = {"ongoing": "What the project covers", "open": "What you will do", "past": ""}[item["status"]]
    work = f'<h2>{work_h}</h2><ul class="plain">' + "".join(f"<li>{E(w)}</li>" for w in item["work"]) + "</ul>" if item["work"] else ""
    bg = f'<h2>Background</h2><p>{E(item["background"])}</p>' if item.get("background") else ""
    rel = [by_title[t] for t in item["related"] if t in by_title]
    relh = f'<h2>Related publications</h2><ol class="pubs">' + "".join(pub_li(p) for p in rel) + "</ol>" if rel else ""
    them = f'<p class="more">Research theme: <a href="research.html#{item["theme"]}">{E(theme)}</a></p>' if theme else ""
    if item["status"] == "open":
        cta = (f'<aside class="callout"><h2>Interested?</h2><p>Write to me at {MAIL["unito"]} with your CV, your transcript of records and a few lines on why this topic '
               f'interests you. The topic is a starting point: we shape the final project together.</p></aside>')
    elif item["status"] == "ongoing":
        cta = f'<aside class="callout"><h2>Similar topics</h2><p>This project is under way. For related topics, see the <a href="{SP_INDEX}#{level}">open {LEVEL_LABEL[level]} topics</a> or write to me.</p></aside>'
    else:
        cta = f'<aside class="callout"><h2>Current positions</h2><p>This position has been filled. Open positions are announced on the <a href="{SP_INDEX}#phd">PhD projects</a> page and on LinkedIn.</p></aside>'
    tags = f'<p class="tags"><span>{LEVEL_LABEL[level]}</span><span>{STATUS_LABEL[item["status"]]}</span></p>'
    return f"""<p class="crumb"><a href="{SP_INDEX}#{level}">← {LEVEL_INFO[level][0]}</a></p>
<h1>{E(item["title"])}</h1>
{tags}<p class="note">{E(item["context"])}</p>
<div class="spbody">{desc}{work}{bg}{relh}{them}</div>
{cta}
"""


PEOPLE_CURRENT = [
    # (name, role and period, [(label, url)])
    ("Laura Finarelli", "PhD candidate, since 2023 (with TU Berlin)",
     [("HES-SO", "https://www.hevs.ch/en/collaborateurs/finarelli-206941"), ("TU Berlin", "https://www.tkn.tu-berlin.de/team/finarelli/")]),
    ("Berk Buzcu", "PhD candidate, since 2025",
     [("HES-SO", "https://people.hes-so.ch/en/profile/10071804451-berk-buzcu"), ("Google Scholar", "https://scholar.google.com/citations?user=THXz4A8AAAAJ")]),
    ("Saira Bano", "Postdoctoral researcher, since 2025",
     [("Publications", "https://iris.cnr.it/cris/rp/rp14228")]),
]
PEOPLE_ALUMNI = [
    ("Biagio Boi", "PhD, University of Salerno, 2022–2026 (co-supervised)", [("Website", "https://biagioboi.github.io")]),
    ("Mina Aghaei Dinani", "PhD, University of Neuchâtel, 2020–2025 · now AI engineer in industry",
     [("LinkedIn", "https://www.linkedin.com/in/mina-aghaei-dinani/"), ("Thesis", "https://libra.unine.ch/bitstreams/e819e4a8-5fbf-47f0-b010-dbac3ff01871/download")]),
    ("Nhat Dao Anh Nguyen", "PhD, University of Adelaide, 2022–2025 (co-supervised)", []),
    ("Noelia Pérez Palma", "PhD, IMDEA Networks and UC3M, 2022 (co-supervised)", [("IMDEA Networks", "https://networks.imdea.org/en/?p=1516")]),
    ("Gaetano Manzo", "PhD, University of Bern, 2016–2020", [("LinkedIn", "https://www.linkedin.com/in/gaetano-manzo/")]),
    ("Christian Vitale", "PhD, UC3M and IMDEA Networks, 2012–2017 · now at KIOS CoE, University of Cyprus",
     [("KIOS", "https://www.kios.ucy.ac.cy/people/christian-vitale/")]),
    ("Luc Dufour", "PhD, 2017 (co-supervised)", []),
    ("Kshitiz Verma", "PhD, UC3M and IMDEA Networks, 2010–2016 · now Associate Professor, JK Lakshmipat University",
     [("JKLU", "https://jklu.edu.in/faculty/kshitiz-verma")]),
    ("Alex Olivieri", "PhD, 2013–2016", []),
    ("Shahzad Ali", "PhD, IMDEA Networks, 2010–2014", [("LinkedIn", "https://www.linkedin.com/in/shahzad-ali-374438a/")]),
]


def initials(name):
    parts = [w for w in re.split(r"[\s-]+", name) if w[:1].isupper()]
    return (parts[0][0] + parts[-1][0]) if len(parts) > 1 else name[:2]


def slug(name):
    import unicodedata
    n = unicodedata.normalize("NFKD", name).encode("ascii", "ignore").decode().lower()
    return re.sub(r"[^a-z0-9]+", "-", n).strip("-")


def avatar(name):
    """Photo from people/<slug>.jpg if present, otherwise initials."""
    for ext in ("jpg", "jpeg", "png", "webp"):
        f = ROOT / "people" / f"{slug(name)}.{ext}"
        if f.exists():
            return f'<img class="avatar" src="people/{f.name}" alt="" width="64" height="64" loading="lazy">'
    return f'<span class="avatar" aria-hidden="true">{E(initials(name))}</span>'


def people():
    def li(xs, dr=False):
        out = []
        for n, d, links in xs:
            lk = "".join(f'<a href="{E(u)}">{E(l)}</a>' for l, u in links)
            shown = f"Dr. {n}" if dr else n
            out.append(f'<li>{avatar(n)}<div class="who"><strong>{E(shown)}</strong><span>{E(d)}</span>'
                       f'{f"<span class=lk>{lk}</span>" if lk else ""}</div></li>')
        return "".join(out)
    return f"""<h1>People</h1>
<p class="lede">PhD students and postdoctoral researchers I supervise or have supervised.</p>
<h2>Current</h2><ul class="people">{li(PEOPLE_CURRENT)}</ul>
<h2>Alumni</h2><ul class="people">{li(PEOPLE_ALUMNI, dr=True)}</ul>
<aside class="callout"><h2>Join</h2><p>Open positions are announced here and on LinkedIn. For theses and projects, see <a href="student-projects.html">Bachelor, Master and PhD projects</a>.</p></aside>
"""


def cv():
    org = [("General Chair", "IEEE WONS 2026", "https://2026.wons-conference.org/"),
           ("Track Chair", "IEEE FINE 2026", "https://www.ieee-fine.org/2026/"),
           ("Chair", "IEEE RNDM 2024 – International Workshop on Resilient Networks Design and Modeling", "http://www.rndm.pl/2024/"),
           ("Symposium Chair (Edge Computing, Cloud Computing and Big Data)", "IEEE ICNC 2024", "http://www.conf-icnc.org/2024/"),
           ("Organiser", "9th AI Valais/Wallis Workshop on Human-AI Teaming, 2024", "https://hevs.ch/en/events/9th-ai-valais-wallis-workshop-on-human-ai-teaming-208987"),
           ("Track Chair (IoT and Smart Connected Communities)", "IEEE GLOBECOM 2020", "https://globecom2020.ieee-globecom.org/"),
           ("General Chair", "IEEE CCAuto 2020 – Workshop on Computing and Communications for Autonomous Driving", "http://mobileedgecom.hevs.ch"),
           ("General Chair", "IEEE MobileEdgeCom 2019 – Workshop on Mobile Edge/Fog Computing", "http://mobileedgecom.hevs.ch"),
           ("General Chair", "IEEE AUTO5G 2018 and 2019 – Workshop on 5G and Cooperative Autonomous Driving", "http://e2iot.com/"),
           ("General Chair", "IEEE EdgeCom 2016, 2017 and 2018 – International Workshop on Edge Computing", "http://edgecom.hevs.ch/"),
           ("General Chair", "IEEE E2IoT 2015", "http://e2iot.com/"),
           ("General Chair", "2nd IMDEA Annual International Workshop on Energy Efficiency and Networking, 2010", "http://events.networks.imdea.org/workshop2010")]
    return f"""<h1>Curriculum vitae</h1>
<p class="links dl"><a href="{CV_PDF}" download="Gianluca-Rizzo-CV.pdf">Download CV in PDF</a></p>
<h2>Short bio</h2>
<p class="bio">Gianluca Rizzo is Associate Professor of Computer Science at the Università di Torino, Italy, and Senior Research Associate at the University of Applied Sciences of Western Switzerland (HES-SO Valais-Wallis). He received his PhD in Computer Science from EPFL in 2008 and his MSc in Electronics Engineering from Politecnico di Torino in 2001. He was a researcher at IMDEA Networks in Madrid (2009–2013), worked at ABB and Telecom Italia Lab, and was Associate Professor at the University of Foggia (2020–2024). His research focuses on the design and performance evaluation of distributed and wireless systems, including sustainable 6G networks, mobile base stations and decentralised learning at the network edge. He is a TPC lead member of IEEE INFOCOM, Area Editor of Elsevier Computer Communications, and an IEEE Senior Member.</p>
<p class="note">This bio may be reused for talks and events.</p>

<h2>Positions</h2>
<table class="tbl cvt"><tbody>
<tr><td>2024–</td><td><strong>Associate Professor of Computer Science</strong>, <a href="{INST['unito_dept']}">Department of Computer Science</a>, Università di Torino, Italy (<a href="{INST['unito_me']}">UniTo page</a>)</td></tr>
<tr><td>2013–</td><td><strong>Senior Research Associate</strong>, <a href="{INST['hevs_inst']}">Institute of Informatics</a>, HES-SO Valais-Wallis, Sierre, Switzerland (<a href="{INST['hevs_me']}">HES-SO page</a>); member of the <a href="{INST['hcai']}">Human Centered AI lab</a> (Prof. Antoine Widmer); <a href="{INST['conex']}">ConEx Lab</a></td></tr>
<tr><td>2009–</td><td><strong>Technical consultant</strong>, avionic and utility communications industry, Switzerland</td></tr>
<tr><td>2020–2024</td><td><strong>Associate Professor of Computer Science</strong>, University of Foggia, Italy</td></tr>
<tr><td>2009–2013</td><td><strong>Researcher</strong>, IMDEA Networks Institute, Madrid, Spain; adjunct professor at Universidad Carlos III de Madrid (2009–2011)</td></tr>
<tr><td>2008–2009</td><td><strong>Telecommunication Systems Engineer</strong>, ABB, Baden, Switzerland</td></tr>
<tr><td>2004–2008</td><td><strong>Scientific assistant</strong>, EPFL, Lausanne, Switzerland</td></tr>
<tr><td>2001–2003</td><td><strong>Telecommunications Engineer</strong>, Telecom Italia Lab, Torino, Italy</td></tr>
</tbody></table>

<h2>Education</h2>
<table class="tbl cvt"><tbody>
<tr><td>2008</td><td><strong>PhD in Computer Science</strong>, EPFL. Thesis: <i>Stability of Networks with Aggregate Scheduling</i>, advisor Prof. Jean-Yves Le Boudec</td></tr>
<tr><td>2001</td><td><strong>MSc in Electronics Engineering</strong>, Politecnico di Torino, summa cum laude</td></tr>
<tr><td>2020</td><td>Italian National Academic Qualification (ASN) as Associate Professor in Computer Science (01/B1) and Computer Engineering (09/H1)</td></tr>
</tbody></table>

<h2>Awards</h2>
<ul class="plain">
<li>Best Paper Award runner-up, IEEE SmartIoT 2025</li>
<li>Distinguished TPC Member Award, IEEE INFOCOM 2019, 2020 and 2021</li>
<li>Best Demo/Short Paper Award, AdHoc-Now 2019</li>
<li>Best Student Paper Award, International Teletraffic Congress (ITC 29), 2017</li>
<li>Honourable Mention, COMSNETS 2015</li>
<li>Best Paper Award, IEEE NCA 2012</li>
<li>Best Paper Award, International Teletraffic Congress (ITC 23), 2011</li>
<li>Marie Curie AMAROUT fellowship, 2009–2012</li>
</ul>

<h2>Editorial and review activity</h2>
<ul class="plain">
<li>Area Editor, Elsevier <i>Computer Communications</i>; Guest Editor, <i>Computer Communications</i> (2026) and <i>Future Internet</i> (2015)</li>
<li>TPC lead member, IEEE INFOCOM (2019–2026); TPC member of IFIP Performance, IEEE ICC, IEEE GLOBECOM and IEEE WoWMoM, among others</li>
<li>Reviewer for IEEE/ACM Transactions on Networking and ACM TOMPECS, and for Horizon Europe proposals on 6G and deterministic networking</li>
<li>Advisory board member, Horizon Europe project Citiverse (2024–2026)</li>
</ul>

<h2>Conference organisation</h2>
<ul class="plain">{''.join(f'<li>{r}, <a href="{E(u)}">{E(c)}</a></li>' for r, c, u in org)}</ul>

<h2>Invited talks</h2>
<ul class="plain">
<li><i>Vehicle Position Nowcasting with Gossip Learning</i>, HiPEAC 2022, Tampere (with Mina Aghaei Dinani)</li>
<li><i>On Capacity of Probabilistic Storage Systems</i>, 1st Workshop on Virtual Edge Computing, Berlin, 2020</li>
<li><i>Floating Content in the IoT Era</i>, WINCOM 2017, Rabat</li>
</ul>

<h2>Software, demos and prototypes</h2>
<ul class="plain">
<li>A disaster rescue application based on Floating Content – demo at AdHoc-Now 2019</li>
<li>NOSE: a nomadic scalable ecosystem for pervasive sensing – demo, 2017</li>
<li>Floater: Floating Content for situation awareness – demo, 2017</li>
</ul>

<h2>Memberships</h2>
<p>IEEE Senior Member; IEEE Communications Society and its Technical Committee on Green Communications and Computing; ACM.</p>

<h2>Languages</h2>
<p>Italian (native), English (C2), French (advanced), Spanish (intermediate), German (basic).</p>
"""


FAVICON = """<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 64 64"><rect width="64" height="64" rx="14" fill="#1d2bd8"/><text x="32" y="43" font-family="Georgia,serif" font-size="30" fill="#fff" text-anchor="middle">GR</text></svg>
"""


def cv_print_html(pubs):
    """A standalone, print-ready page (CV + full publication list) used to generate cv.pdf."""
    body = cv().replace(f'<p class="links dl"><a href="{CV_PDF}" download="Gianluca-Rizzo-CV.pdf">Download CV in PDF</a></p>', "")
    body = body.replace('<p class="note">This bio may be reused for talks and events.</p>', "")
    head = (f'<p class="cvhead">{TITLES_LINE}<br>Università di Torino, Department of Computer Science, Via Pessinetto 12, 10149 Torino, Italy · {E(at_text(EM["unito"]))}<br>'
            f'HES-SO Valais-Wallis, Institute of Informatics, Technopole 3, 3960 Sierre, Switzerland · {E(at_text(EM["hevs"]))}<br>'
            f'{BASE} · ORCID 0000-0001-7129-4972</p>')
    body = body.replace("<h1>Curriculum vitae</h1>", f"<h1>Gianluca Rizzo</h1>{head}", 1)
    pl = ['<h2>Publications</h2>']
    for t, name in TYPES.items():
        items = sorted([p for p in pubs if p["type"] == t], key=lambda p: -p["year"])
        pl.append(f'<h3>{name}</h3><ol class="pubs">' + "".join(pub_li(p) for p in items) + '</ol>')
    css = (ROOT / "style.css").read_text(encoding="utf-8")
    return f"""<!DOCTYPE html><html lang="en"><head><meta charset="utf-8"><meta name="robots" content="noindex">
<title>Gianluca Rizzo – Curriculum vitae</title><style>{css}
@page{{size:A4;margin:16mm 16mm 18mm}}
body{{font:10pt/1.45 "Helvetica Neue",Arial,sans-serif;color:#111;background:#fff}}
h1,h2,h3{{font-family:Georgia,serif}} h1{{font-size:24pt;margin:0 0 4pt}} h2{{font-size:14pt;margin:16pt 0 6pt;border-bottom:1px solid #ccc;padding-bottom:2pt}} h3{{font-size:11pt;margin:10pt 0 4pt}}
.cvhead{{color:#444;font-size:9pt;margin:0 0 6pt}} .tbl{{font-size:10pt}} .tbl td{{padding:4pt 8pt 4pt 0}}
.pubs li{{padding:4pt 0;break-inside:avoid}} .pubs .a,.pubs .m{{font-size:9pt}} a{{color:#111;text-decoration:none}}
.badge{{font-size:8pt}} h2,h3{{break-after:avoid}}
</style></head><body><main><div class="wrap" style="max-width:none;padding:0">{body}{"".join(pl)}</div></main></body></html>"""


TITLES_LINE = "Associate Professor of Computer Science, Università di Torino · Senior Research Associate, HES-SO Valais-Wallis"


def make_pdf(html_path, pdf_path):
    import shutil, subprocess, tempfile
    chrome = next((c for c in ("google-chrome", "chromium", "chromium-browser") if shutil.which(c)), None)
    if not chrome:
        print("no Chrome found: cv.pdf not regenerated")
        return
    with tempfile.TemporaryDirectory() as prof:
        subprocess.run([chrome, "--headless=new", "--no-sandbox", "--disable-gpu", f"--user-data-dir={prof}",
                        "--no-pdf-header-footer", f"--print-to-pdf={pdf_path}", html_path.as_uri()],
                       check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL, timeout=120)
    print(f"wrote {pdf_path.name} ({pdf_path.stat().st_size // 1024} KB)")


def main():
    pubs = load_pubs()
    pages = [
        ("index.html", "Home", "Gianluca Rizzo, Associate Professor of Computer Science at the Università di Torino and Senior Research Associate at HES-SO Valais-Wallis: 6G networks, edge learning, network performance modelling.", home(pubs), PERSON),
        ("research.html", "Research", "Research of Gianluca Rizzo: sustainable 6G networks, moving networks, decentralised learning at the edge, multi-agent coordination and performance modelling.", research(pubs), None),
        ("projects.html", "Projects", "Research projects led by Gianluca Rizzo, including the Horizon Europe project UNITY-6G and SNSF projects.", projects(), None),
        ("publications.html", "Publications", "Publications of Gianluca Rizzo: journal articles, conference papers, book chapters and patents.", publications_page(pubs), None),
        ("teaching.html", "Teaching", "Courses taught by Gianluca Rizzo at the Università di Torino, HES-SO Valais-Wallis and elsewhere, with links to the course pages.", teaching(), None),
        ("student-projects.html", "Bachelor, Master & PhD projects", "Bachelor's, Master's and PhD projects with Gianluca Rizzo on 6G networks, edge learning and network performance modelling.", student_projects(), None),
        ("people.html", "People", "PhD students and postdocs supervised by Gianluca Rizzo.", people(), None),
        ("cv.html", "CV", "Curriculum vitae of Gianluca Rizzo: positions, education, awards, service and talks. PDF download available.", cv(), None),
    ]
    for fname, title, desc, body, ld in pages:
        (ROOT / fname).write_text(page(fname, title, desc, body, ld), encoding="utf-8")
    for old in ROOT.glob("sp-*.html"):
        old.unlink()
    for lv, items in SP.items():
        for it in items:
            pages.append((sp_file(it), it["title"], f"{LEVEL_LABEL[lv]} project: {it['summary']}", None, None))
            (ROOT / sp_file(it)).write_text(page(sp_file(it), it["title"], f"{LEVEL_LABEL[lv]} project: {it['summary']}",
                                                 sp_page(lv, it, pubs), None, current=SP_INDEX), encoding="utf-8")
    (ROOT / "favicon.svg").write_text(FAVICON, encoding="utf-8")
    urls = "".join(f"<url><loc>{BASE if f == 'index.html' else BASE + f}</loc><lastmod>{TODAY}</lastmod></url>" for f, *_ in pages)
    (ROOT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n', encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nDisallow: /network/\nDisallow: /src/\n\nSitemap: {BASE}sitemap.xml\n", encoding="utf-8")
    print(f"built {len(pages)} pages, {len(pubs)} publications")
    printable = SRC / "cv-print.html"
    printable.write_text(cv_print_html(pubs), encoding="utf-8")
    make_pdf(printable, ROOT / CV_PDF)


if __name__ == "__main__":
    main()
