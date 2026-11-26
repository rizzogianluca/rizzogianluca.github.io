#!/usr/bin/env python3
"""Build the static site: python3 src/build.py (run from the repository root).

Pages are defined below as HTML fragments; the publication list comes from src/publications.txt.
Writes the HTML pages, favicon, sitemap.xml and robots.txt into the repository root.
The password-protected network/ page is not touched.

Contact addresses are not stored in this script: they are read from the SITE_EMAILS environment
variable (comma-separated) or, if it is not set, from the mailto links of the current index.html.
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
        found = sorted(set(re.findall(r'mailto:([^"?]+)', (ROOT / "index.html").read_text(encoding="utf-8"))))
    em = {"unito": "", "hevs": ""}
    for a in found:
        for k in em:
            if k in a.split("@")[-1]:
                em[k] = a
    if not all(em.values()):
        raise SystemExit("Contact addresses not found: set SITE_EMAILS='address1,address2'")
    return em


EM = load_emails()
MAIL = {k: f'<a href="mailto:{v}">{v}</a>' for k, v in EM.items()}

NAV = [("index.html", "Home"), ("research.html", "Research"), ("projects.html", "Projects"),
       ("publications.html", "Publications"), ("teaching.html", "Teaching"), ("people.html", "People"),
       ("cv.html", "CV")]

PROFILES = [("Google Scholar", "https://scholar.google.com/citations?user=NzZ5dd8AAAAJ"),
            ("dblp", "https://dblp.org/pid/71/3141"),
            ("ORCID", "https://orcid.org/0000-0001-7129-4972"),
            ("LinkedIn", "https://www.linkedin.com/in/gianlucarizzo")]

PERSON = {
    "@context": "https://schema.org", "@type": "Person", "name": ME,
    "url": BASE, "image": BASE + "portrait.jpg",
    "jobTitle": ["Associate Professor of Computer Science", "Senior Research Associate"],
    "worksFor": [
        {"@type": "CollegeOrUniversity", "name": "Università di Torino", "url": "https://www.unito.it"},
        {"@type": "CollegeOrUniversity", "name": "HES-SO Valais-Wallis", "url": "https://www.hevs.ch"}],
    "alumniOf": [{"@type": "CollegeOrUniversity", "name": "EPFL"},
                 {"@type": "CollegeOrUniversity", "name": "Politecnico di Torino"}],
    "email": [f"mailto:{EM['unito']}", f"mailto:{EM['hevs']}"],
    "knowsAbout": ["6G networks", "Wireless networks", "Edge computing", "Gossip learning",
                   "Performance evaluation", "Stochastic geometry", "Network calculus"],
    "sameAs": [u for _, u in PROFILES],
}


def page(fname, title, desc, body, jsonld=None):
    full_title = ME if fname == "index.html" else f"{title} – {ME}"
    url = BASE if fname == "index.html" else BASE + fname
    nav = "".join(f'<li><a href="{f}"{" aria-current=page" if f == fname else ""}>{n}</a></li>' for f, n in NAV)
    ld = f'<script type="application/ld+json">{json.dumps(jsonld, ensure_ascii=False)}</script>' if jsonld else ""
    return f"""<!DOCTYPE html>
<html lang="en"><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{E(full_title)}</title><meta name="description" content="{E(desc)}">
<link rel="canonical" href="{url}"><link rel="icon" href="favicon.svg" type="image/svg+xml">
<meta property="og:type" content="profile"><meta property="og:title" content="{E(full_title)}"><meta property="og:description" content="{E(desc)}">
<meta property="og:url" content="{url}"><meta property="og:image" content="{BASE}portrait.jpg"><meta name="twitter:card" content="summary">
<link rel="preconnect" href="https://fonts.googleapis.com"><link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link href="https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600&family=Spectral:wght@500&display=swap" rel="stylesheet">
<link rel="stylesheet" href="style.css">{ld}</head><body>
<a class="skip" href="#content">Skip to content</a>
<header class="site"><div class="wrap"><a class="brand" href="index.html">{ME}</a><nav aria-label="Main"><ul>{nav}</ul></nav></div></header>
<main id="content"><div class="wrap">
{body}
</div></main>
<footer><div class="wrap"><span>© {TODAY.year} {ME} · {MAIL['unito']} · {MAIL['hevs']}</span><span>Last updated {TODAY.day} {TODAY.strftime('%B %Y')}</span></div></footer>
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
    counts = {t: sum(1 for p in pubs if p["type"] == t) for t in TYPES}
    sel = sorted([p for p in pubs if p["selected"]], key=lambda p: -p["year"])
    out = ['<h1>Publications</h1>',
           f'<p class="lede">{counts["J"]} journal articles, {counts["C"]} conference papers, {counts["B"]} book chapters and '
           f'{counts["P"]} patent. Titles link to the published version. Citation metrics are on '
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
    ("2026-09", "“Floating Gossip: Serverless Distributed Learning in Dynamic Scenarios” is published in <i>IEEE Transactions on Mobile Computing</i>."),
    ("2026-06", "Papers presented at ICAPS 2026 (decentralised multi-agent planning) and EuCNC &amp; 6G Summit 2026 (UNITY-6G architecture)."),
    ("2026-03", "I was General Chair of IEEE WONS 2026, held in Crans-Montana, Switzerland, on 2–4 March."),
    ("2025-11", "Best Paper Award runner-up at IEEE SmartIoT 2025 (Sydney) for our work on energy-aware load shifting in SWIPT IoT networks."),
    ("2025-01", "Start of the Horizon Europe project <a href=\"projects.html#unity-6g\">UNITY-6G</a> on sustainable, Open RAN-based 6G networks."),
    ("2024-12", "I joined the Department of Computer Science of the Università di Torino as Associate Professor."),
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
<p class="role">Associate Professor of Computer Science, Università di Torino<br>Senior Research Associate, HES-SO Valais-Wallis</p>
<p class="lede">I design and analyse distributed and wireless systems: how networks, devices and learning algorithms should be organised to be efficient, sustainable and dependable. My current work focuses on energy-aware 6G networks, mobile base stations and decentralised learning at the network edge, using stochastic geometry, mean-field theory, queueing models and network calculus.</p>
<ul class="aff">
<li><strong>Università di Torino – Department of Computer Science</strong><span>Via Pessinetto 12, 10149 Torino, Italy · {MAIL['unito']}</span></li>
<li><strong>HES-SO Valais-Wallis – Institute of Informatics</strong><span>Technopole 3, CH-3960 Sierre, Switzerland · {MAIL['hevs']}</span></li>
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
<p>I supervise PhD and Master's theses at the Università di Torino and at HES-SO Valais-Wallis on 6G networks, edge learning and network performance modelling. If you are interested, write to me with your CV, your transcripts and a few lines on the topic you would like to work on.</p></aside>
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


def projects():
    def card(p):
        i, acr, title, funder, role, years, _ = p
        return (f'<article class="proj" id="{i}"><h3>{acr} <span class="note">{years}</span></h3><p class="t">{E(title)}</p>'
                f'<p class="m">{E(funder)} · {role}</p></article>')
    cur = "".join(card(p) for p in PROJECTS if p[6])
    past = "".join(card(p) for p in PROJECTS if not p[6])
    return f"""<h1>Projects</h1>
<p class="lede">Funded research projects I lead or have taken part in. I regularly prepare Horizon Europe and national proposals and welcome contacts from potential partners.</p>
<h2>Current</h2><div class="projs">{cur}</div>
<div class="ack">{EU_FLAG}<p>UNITY-6G has received funding from the Smart Networks and Services Joint Undertaking (SNS JU) under the European Union's Horizon Europe research and innovation programme.</p></div>
<h2>Completed</h2><div class="projs">{past}</div>
"""


def teaching():
    return """<h1>Teaching</h1>
<p class="lede">I teach computer networks and databases at the Università di Torino and at HES-SO Valais-Wallis. Course material, schedules and exams are on the official course pages of each university.</p>
<h2>Current courses</h2>
<table class="tbl"><thead><tr><th>Course</th><th>Institution</th><th>Years</th></tr></thead><tbody>
<tr><td>Computer Networks</td><td>Università di Torino</td><td>2024–present</td></tr>
<tr><td>Complements of Computer Networks <span class="note">(Complementi di Reti, INF0342)</span></td><td>Università di Torino</td><td>2025–present</td></tr>
<tr><td>Databases <span class="note">(Basi di Dati, MFN0602)</span></td><td>Università di Torino</td><td>2024–present</td></tr>
<tr><td>Computer Networks</td><td>HES-SO Valais-Wallis</td><td>2021–22, 2023–24</td></tr>
</tbody></table>
<h2>Earlier teaching</h2>
<ul class="plain">
<li>Computer Networks (Sistemi Informativi II), Big Data, Mobile Networks and IoT, Multimedia Management and Processing – University of Foggia, 2020–2025</li>
<li>Internet of Things: IoT protocols and communications – EPFL</li>
<li>Post-Disaster Communications and Emergency Networks – COST RECODIS training school, Brussels</li>
<li>Shared Medium and LAN Technologies – Universidad Carlos III de Madrid (adjunct professor), 2009–2011</li>
<li>Teaching assistant at EPFL (Computer Networks, Performance Evaluation, C and C++ Programming) and at Politecnico di Torino (Java Programming)</li>
</ul>
<h2>Theses</h2>
<p>I supervise Bachelor's, Master's and PhD theses on wireless and mobile networks, 6G, edge computing and distributed learning. If you are interested in a thesis, contact me by email with your CV and transcripts.</p>
<h2>Resources for students</h2>
<ul class="plain"><li><a href="https://leboudec.github.io/leboudec/resources/paper.html">How to write a paper</a>, by Jean-Yves Le Boudec</li></ul>
"""


def people():
    cur = [("Mina Aghaei Dinani", "since 2020"), ("Laura Finarelli", "since 2023"), ("Berk Buzcu", "since 2025"),
           ("Saira Bano", "since 2025"), ("Dhekra Zaafrane", "since 2023, co-supervised"), ("Biagio Boi", "2022–2026, co-supervised")]
    alum = [("Nhat Dao Anh Nguyen", "2022–2025, co-supervised"), ("Gaetano Manzo", "2016–2020"), ("Christian Vitale", "2012–2017"),
            ("Alex Olivieri", "2013–2016"), ("Kshitiz Verma", "2010–2016"), ("Shahzad Ali", "2010–2014"),
            ("Noelia Pérez Palma", "co-supervised"), ("Luc Dufour", "co-supervised")]
    li = lambda xs: "".join(f'<li><strong>{n}</strong><span>{d}</span></li>' for n, d in xs)
    return f"""<h1>People</h1>
<p class="lede">PhD students and postdoctoral researchers I supervise or have supervised.</p>
<h2>Current</h2><ul class="people">{li(cur)}</ul>
<h2>Alumni</h2><ul class="people">{li(alum)}</ul>
<aside class="callout"><h2>Join</h2><p>Open positions are announced here and on LinkedIn. Spontaneous applications from strong candidates in networking, performance evaluation or machine learning are welcome: send your CV, transcripts and a short research statement.</p></aside>
"""


def cv():
    org = [("General Chair", "IEEE WONS 2026"), ("Track Chair", "IEEE FINE 2026"), ("Chair", "IEEE RNDM 2024"),
           ("Symposium Chair (Edge Computing, Cloud Computing and Big Data)", "IEEE ICNC 2024"),
           ("Organiser", "9th AI Valais/Wallis workshop “Human-AI Teaming”, 2024"),
           ("Track Chair (IoT and Smart Connected Communities)", "IEEE GLOBECOM 2020"),
           ("General Chair", "IEEE CCAuto 2020, IEEE MobileEdgeCom 2019, IEEE AUTO5G 2018–2019, IEEE EdgeCom 2016–2018, IEEE E2IoT 2015"),
           ("General Chair", "2nd IMDEA Workshop on Energy Efficiency and Networking, 2010")]
    return f"""<h1>Curriculum vitae</h1>
<h2>Short bio</h2>
<p class="bio">Gianluca Rizzo is Associate Professor of Computer Science at the Università di Torino, Italy, and Senior Research Associate at the University of Applied Sciences of Western Switzerland (HES-SO Valais-Wallis). He received his PhD in Computer Science from EPFL in 2008 and his MSc in Electronics Engineering from Politecnico di Torino in 2001. He was a researcher at IMDEA Networks in Madrid (2009–2013), worked at ABB and Telecom Italia Lab, and was Associate Professor at the University of Foggia (2020–2024). His research focuses on the design and performance evaluation of distributed and wireless systems, including sustainable 6G networks, mobile base stations and decentralised learning at the network edge. He is a TPC lead member of IEEE INFOCOM, Area Editor of Elsevier Computer Communications, and an IEEE Senior Member.</p>
<p class="note">This bio may be reused for talks and events.</p>

<h2>Positions</h2>
<table class="tbl cvt"><tbody>
<tr><td>2024–</td><td><strong>Associate Professor of Computer Science</strong>, Università di Torino, Italy</td></tr>
<tr><td>2013–</td><td><strong>Senior Research Associate</strong>, HES-SO Valais-Wallis, Sierre, Switzerland</td></tr>
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
<ul class="plain">{''.join(f'<li>{r}, {E(c)}</li>' for r, c in org)}</ul>

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


def main():
    pubs = load_pubs()
    pages = [
        ("index.html", "Home", "Gianluca Rizzo, Associate Professor of Computer Science at the Università di Torino and Senior Research Associate at HES-SO Valais-Wallis: 6G networks, edge learning, network performance modelling.", home(pubs), PERSON),
        ("research.html", "Research", "Research of Gianluca Rizzo: sustainable 6G networks, moving networks, decentralised learning at the edge, multi-agent coordination and performance modelling.", research(pubs), None),
        ("projects.html", "Projects", "Research projects led by Gianluca Rizzo, including the Horizon Europe project UNITY-6G and SNSF projects.", projects(), None),
        ("publications.html", "Publications", "Publications of Gianluca Rizzo: journal articles, conference papers, book chapters and patents.", publications_page(pubs), None),
        ("teaching.html", "Teaching", "Courses taught by Gianluca Rizzo at the Università di Torino and HES-SO Valais-Wallis, and thesis supervision.", teaching(), None),
        ("people.html", "People", "PhD students and postdocs supervised by Gianluca Rizzo.", people(), None),
        ("cv.html", "CV", "Curriculum vitae of Gianluca Rizzo: positions, education, awards, service and talks.", cv(), None),
    ]
    for fname, title, desc, body, ld in pages:
        (ROOT / fname).write_text(page(fname, title, desc, body, ld), encoding="utf-8")
    (ROOT / "favicon.svg").write_text(FAVICON, encoding="utf-8")
    urls = "".join(f"<url><loc>{BASE if f == 'index.html' else BASE + f}</loc><lastmod>{TODAY}</lastmod></url>" for f, *_ in pages)
    (ROOT / "sitemap.xml").write_text(f'<?xml version="1.0" encoding="UTF-8"?>\n<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">{urls}</urlset>\n', encoding="utf-8")
    (ROOT / "robots.txt").write_text(f"User-agent: *\nDisallow: /network/\nDisallow: /src/\n\nSitemap: {BASE}sitemap.xml\n", encoding="utf-8")
    print(f"built {len(pages)} pages, {len(pubs)} publications")


if __name__ == "__main__":
    main()
