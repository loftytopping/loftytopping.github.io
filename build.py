#!/usr/bin/env python3
"""Build the personal website into _site/.

Content lives in site.yml and content/. Run:  python build.py
Then preview with:  python -m http.server -d _site 8000
Needs: pip install pyyaml markdown
"""
import html
import re
import shutil
from datetime import date, datetime
from pathlib import Path

import markdown
import yaml

ROOT = Path(__file__).parent
OUT = ROOT / "_site"
CONTENT = ROOT / "content"
TODAY = date.today()

NAV = [("index.html", "Home"), ("cv.html", "CV"), ("publications.html", "Publications"),
       ("writing.html", "Writing"), ("media.html", "Media"), ("events.html", "Events"),
       ("teaching.html", "Teaching"), ("work-with-me.html", "Work with me")]


def load(name):
    with open(ROOT / name, encoding="utf-8") as f:
        return yaml.safe_load(f) or {}


def md(text):
    return markdown.markdown(text or "", extensions=["extra", "smarty"])


def md_inline(text):
    out = md(str(text or "")).strip()
    if out.startswith("<p>") and out.endswith("</p>") and out.count("<p>") == 1:
        out = out[3:-4]
    return out


def esc(s):
    return html.escape(str(s or ""), quote=True)


def role_text(r):
    return r["text"] if isinstance(r, dict) else str(r)


def role_html(r):
    if isinstance(r, dict) and r.get("url"):
        return f'<a href="{esc(r["url"])}">{esc(r["text"])}</a>'
    return esc(role_text(r))


def portrait(site, prefix=""):
    photo = site.get("photo")
    if not photo or not (ROOT / photo).exists():
        return ""
    return f'<img class="portrait" src="{prefix}{esc(photo)}" alt="{esc(site["name"])}" width="112" height="112">'


def slugify(s):
    return re.sub(r"[^a-z0-9]+", "-", s.lower()).strip("-")


def as_date(v):
    if isinstance(v, datetime):
        return v.date()
    if isinstance(v, date):
        return v
    return datetime.strptime(str(v), "%Y-%m-%d").date()


def nice_date(d):
    return f"{d.day} {d.strftime('%B %Y')}"


# ---------------------------------------------------------------- layout

def page(site, title, body, active="", prefix="", description="", extra_head=""):
    cur = ' aria-current="page"'
    nav = "".join(
        f'<li><a href="{prefix}{href}"{cur if href == active else ""}>{label}</a></li>'
        for href, label in NAV)
    links = " ".join(f'<a href="{esc(l["url"])}">{esc(l["label"])}</a>' for l in site.get("links", []))
    full_title = site["name"] if title == site["name"] else f"{title} | {site['name']}"
    desc = description or role_text((site.get("roles") or [""])[0])
    return f"""<!DOCTYPE html>
<html lang="en-GB">
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width, initial-scale=1, viewport-fit=cover">
<title>{esc(full_title)}</title>
<meta name="description" content="{esc(desc)}">
<meta property="og:title" content="{esc(full_title)}">
<meta property="og:description" content="{esc(desc)}">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Outfit:wght@300;400;500;700&family=JetBrains+Mono:wght@400;600&family=Source+Serif+4:ital,opsz,wght@0,8..60,400;0,8..60,600;1,8..60,400&display=swap">
<link rel="stylesheet" href="{prefix}static/style.css">
<link rel="alternate" type="application/rss+xml" title="{esc(site['name'])}" href="{prefix}feed.xml">
{extra_head}</head>
<body>
<header class="topbar">
  <div class="topbar-inner">
    <a class="mark" href="{prefix}index.html"><span class="mark-badge">{esc(site.get('short_name', 'DT'))}</span><span class="mark-name">{esc(site['name'])}</span></a>
    <button class="menu-toggle" type="button" aria-expanded="false" aria-controls="nav-list">Menu</button>
    <nav aria-label="Main"><ul id="nav-list">{nav}</ul></nav>
  </div>
</header>
<main id="main">
{body}
</main>
<footer class="footer">
  <div class="footer-inner">
    <p class="footer-contact">{esc(site['email'])}</p>
    <p class="footer-links">{links}</p>
    <p class="footer-note">Department of Earth and Environmental Sciences, University of Manchester</p>
  </div>
</footer>
<script src="{prefix}static/site.js"></script>
</body>
</html>
"""


def links_row(links, cls="chips"):
    if not links:
        return ""
    return f'<p class="{cls}">' + "".join(
        f'<a href="{esc(l["url"])}">{esc(l["label"])}</a>' for l in links) + "</p>"


def event_when(e):
    d = as_date(e["date"])
    if e.get("end_date"):
        d2 = as_date(e["end_date"])
        if d.month == d2.month and d.year == d2.year:
            return f"{d.day} to {d2.day} {d2.strftime('%B %Y')}"
        return f"{nice_date(d)} to {nice_date(d2)}"
    return nice_date(d)


def event_card(e, past=False):
    title = esc(e["title"])
    if e.get("url"):
        title = f'<a href="{esc(e["url"])}">{title}</a>'
    bits = [f'<span class="ev-type">{esc(e.get("type", "Event"))}</span>',
            f'<time datetime="{as_date(e["date"]).isoformat()}">{event_when(e)}</time>']
    meta = "".join(f"<p>{esc(e[k])}</p>" for k in ("location", "role") if e.get(k))
    note = f'<div class="ev-note">{md_inline(e["note"])}</div>' if e.get("note") else ""
    start = as_date(e["date"])
    end = as_date(e.get("end_date") or e["date"])
    now = start <= TODAY <= end
    bits.insert(1, f'<span class="ev-now"{"" if now else " hidden"}>Happening now</span>')
    cls = "event" + (" past" if past else "") + (" now" if now else "")
    return f"""<article class="{cls}" data-start="{start.isoformat()}" data-end="{end.isoformat()}">
  <div class="ev-head">{''.join(bits)}</div>
  <h3>{title}</h3>
  <div class="ev-meta">{meta}</div>{note}
</article>"""


def split_events(events):
    up, past = [], []
    for e in events:
        end = as_date(e.get("end_date") or e["date"])
        (up if end >= TODAY else past).append(e)
    up.sort(key=lambda e: as_date(e["date"]))
    past.sort(key=lambda e: as_date(e["date"]), reverse=True)
    return up, past


# ---------------------------------------------------------------- posts

def load_posts():
    posts = []
    for p in sorted((CONTENT / "posts").glob("*.md")):
        if p.name.startswith("_"):
            continue  # templates and notes
        raw = p.read_text(encoding="utf-8")
        m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.S)
        meta, body = (yaml.safe_load(m.group(1)), m.group(2)) if m else ({}, raw)
        if meta.get("draft"):
            continue
        d = as_date(meta.get("date") or p.name[:10])
        slug = meta.get("slug") or re.sub(r"^\d{4}-\d{2}-\d{2}-", "", p.stem)
        posts.append({"title": meta.get("title", slug), "date": d, "slug": slug,
                      "summary": meta.get("summary", ""), "tags": meta.get("tags", []),
                      "html": md(body)})
    posts.sort(key=lambda x: x["date"], reverse=True)
    return posts


def post_item(p, prefix=""):
    return f"""<li class="post-item">
  <time datetime="{p['date'].isoformat()}">{nice_date(p['date'])}</time>
  <a href="{prefix}posts/{p['slug']}.html">{esc(p['title'])}</a>
  {f'<p>{esc(p["summary"])}</p>' if p['summary'] else ''}
</li>"""


# ---------------------------------------------------------------- pages

def build_home(site, themes, posts, events, mentions=()):
    up, _ = split_events(events)
    now_at = ""
    for e in up:  # one hidden line per upcoming event; the page script shows whichever is on today
        start, end = as_date(e["date"]), as_date(e.get("end_date") or e["date"])
        where = e.get("location") or ""
        until = f" until {nice_date(end)}" if end > start else ""
        label = f"Now at {esc(e['title'])}" + (f", {esc(where)}" if where else "") + until
        now_at += (f'<p class="now-at" data-start="{start.isoformat()}" data-end="{end.isoformat()}"'
                   f'{"" if start <= TODAY <= end else " hidden"}><span class="pulse" aria-hidden="true"></span>{label}</p>')
    roles = "".join(f"<li>{role_html(r)}</li>" for r in site.get("roles", []))
    theme_html = "".join(f"""<article class="theme">
  <h3>{esc(t['title'])}</h3>
  <p>{esc(' '.join(t['text'].split()))}</p>
  {links_row(t.get('links'), 'theme-links')}
</article>""" for t in themes.get("themes", []))
    latest = "".join(post_item(p) for p in posts) or '<li class="empty">No posts yet.</li>'
    if up:
        ev = "".join(event_card(e) for e in up)
    else:
        ev = '<p class="empty">Nothing coming up is listed yet. <a href="events.html">See past events</a>.</p>'
    body = f"""
<section class="hero">
  <div class="hero-text">
    <p class="eyebrow">Modelling · data · AI</p>
    <div class="name-row">{portrait(site)}<div><h1>{esc(site['name'])}</h1>
    <ul class="roles">{roles}</ul>{now_at}</div></div>
    <div class="intro">{md(site.get('intro', ''))}</div>
    {links_row(site.get('links'))}
  </div>
  <figure class="hero-fig" aria-label="Animation of aerosol particles swelling as relative humidity rises">
    <canvas id="growth" width="480" height="420"></canvas>
    <figcaption><span id="rh-readout">RH 85%</span><span class="fig-key"><i class="k1"></i>ammonium sulfate <i class="k2"></i>sea salt <i class="k3"></i>organic</span></figcaption>
  </figure>
</section>

<section class="block" id="work">
  <div class="block-head"><h2>Areas of work</h2><a class="more" href="cv.html">Full CV</a></div>
  <div class="themes">{theme_html}</div>
</section>

<section class="callouts">
  <div class="callout">
    <div><h2>Teaching and summer schools</h2><p>University courses, and short courses and summer schools on programming, machine learning, AI and environmental modelling.</p></div>
    <a class="btn" href="teaching.html">What I offer</a>
  </div>
  <div class="callout">
    <div><h2>Work with me</h2><p>PhD projects, postdoctoral and fellowship applications, visiting researchers and sabbaticals.</p></div>
    <a class="btn" href="work-with-me.html">See opportunities</a>
  </div>
</section>

<section class="block split three">
  <div>
    <div class="block-head"><h2>In the media</h2><a class="more" href="media.html">All coverage</a></div>
    <div class="scrollbox" tabindex="0" aria-label="Media coverage"><ul class="posts">{''.join(mention_item(m) for m in mentions) or '<li class="empty">Nothing listed yet.</li>'}</ul></div>
  </div>
  <div>
    <div class="block-head"><h2>Writing</h2><a class="more" href="writing.html">All posts</a></div>
    <div class="scrollbox" tabindex="0" aria-label="Posts"><ul class="posts">{latest}</ul></div>
  </div>
  <div>
    <div class="block-head"><h2>Where I'll be</h2><a class="more" href="events.html">All events</a></div>
    <div class="scrollbox" tabindex="0" aria-label="Upcoming events"><div class="events">{ev}</div></div>
  </div>
</section>
"""
    return page(site, site["name"], body, "index.html",
                extra_head='<script src="static/growth.js" defer></script>\n')


def cv_entry(e):
    when = f'<div class="cv-when">{esc(e.get("when", ""))}</div>'
    what = md_inline(e.get("what", ""))
    if e.get("url"):
        what = f'<a href="{esc(e["url"])}">{what}</a>'
    where = f'<div class="cv-where">{md_inline(e["where"])}</div>' if e.get("where") else ""
    note = f'<div class="cv-note">{md_inline(e["note"])}</div>' if e.get("note") else ""
    return f'<li class="cv-row">{when}<div class="cv-body"><div class="cv-what">{what}</div>{where}{note}</div></li>'


def ref(p):
    title = esc(p["title"])
    doi = p.get("doi")
    link = f' <a class="doi" href="https://doi.org/{esc(doi)}">doi:{esc(doi)}</a>' if doi else ""
    authors = esc(p["authors"]).rstrip(".").replace("Topping", "<strong>Topping</strong>")
    return (f'<li class="ref"><span class="ref-year">{esc(p["year"])}</span><div><span class="ref-title">{title}</span>'
            f'<span class="ref-meta">{authors}. <em>{esc(p["venue"])}</em>.{link}</span></div></li>')


def build_cv(site, cv):
    toc, secs = [], []
    for s in cv.get("sections", []):
        if s.get("web") is False:
            continue
        sid = slugify(s["heading"])
        toc.append(f'<li><a href="#{sid}">{esc(s["heading"])}</a></li>')
        intro = f'<p class="cv-intro">{md_inline(s["intro"])}</p>' if s.get("intro") else ""
        secs.append(f'<section class="cv-sec" id="{sid}"><h2>{esc(s["heading"])}</h2>{intro}'
                    f'<ul class="cv-list">{"".join(cv_entry(e) for e in s.get("entries", []))}</ul></section>')
        if s["heading"].lower().startswith("open-source"):
            # books and selected publications sit after software
            if cv.get("books"):
                toc.append('<li><a href="#books">Books</a></li>')
                secs.append('<section class="cv-sec" id="books"><h2>Books and chapters</h2><ul class="refs">'
                            + "".join(ref(b) for b in cv["books"]) + "</ul></section>")
            if cv.get("selected_publications"):
                toc.append('<li><a href="#selected-publications">Selected publications</a></li>')
                secs.append('<section class="cv-sec" id="selected-publications"><h2>Selected publications</h2>'
                            '<ul class="refs">' + "".join(ref(p) for p in cv["selected_publications"][:6]) + "</ul>"
                            '<p class="cv-intro"><a href="publications.html">Full publication list</a>, also on '
                            f'<a href="https://orcid.org/{esc(site.get("orcid"))}">ORCID</a>.</p></section>')
    roles = " · ".join(role_html(r) for r in site.get("roles", []))
    hl = cv.get("highlights") or []
    highlights = ('<ul class="highlights">' + "".join(f"<li>{md_inline(h)}</li>" for h in hl) + "</ul>") if hl else ""
    pdf = cv.get("pdf")
    if pdf and (ROOT / pdf).exists():
        download = f'<a class="btn" href="{esc(pdf)}">Download CV (PDF, 2 pages)</a>'
        download_inline = f'<a href="{esc(pdf)}">PDF CV</a>'
    else:
        download, download_inline = "", "full CV"
    body = f"""
<div class="doc">
  <aside class="toc" aria-label="CV sections">
    <p class="toc-label">Contents</p>
    <ol>{''.join(toc)}</ol>
  </aside>
  <article class="doc-main">
    <header class="doc-head">
      <p class="eyebrow">Curriculum vitae</p>
      <div class="name-row">{portrait(site)}<div><h1>{esc(site['name'])}</h1>
      <p class="doc-roles">{roles}</p></div></div>
      <div class="lede">{md(cv.get('summary', ''))}</div>
      {highlights}
      <p class="cv-actions">{download}<a href="publications.html">All publications</a></p>
    </header>
    {''.join(secs)}
    <p class="cv-foot">This page is a summary. Funding, invited talks, supervision, leadership and knowledge exchange
    are covered in the {download_inline}.</p>
  </article>
</div>
"""
    return page(site, "CV", body, "cv.html", description=f"Curriculum vitae of {site['name']}")


def build_pubs(site, pubs):
    groups = [("articles", "Journal articles and software", True),
              ("reports", "Reports and other outputs", False),
              ("abstracts", "Conference proceedings and abstracts", False)]
    parts = []
    counts = []
    for key, label, open_ in groups:
        items = pubs.get(key) or []
        if not items:
            continue
        counts.append(f'<a href="#{key}">{len(items)} {label.split(" and ")[0].lower()}</a>')
        by_year = {}
        for it in items:
            by_year.setdefault(it.get("year") or "Undated", []).append(it)
        years = sorted(by_year, key=lambda y: (isinstance(y, int), y), reverse=True)
        inner = "".join(
            f'<h3 class="pub-year">{y}</h3><ol class="pub-list">'
            + "".join(f"<li>{md_inline(i['text'])}</li>" for i in by_year[y]) + "</ol>"
            for y in years)
        parts.append(f'<details class="pub-group" id="{key}"{" open" if open_ else ""}>'
                     f'<summary><h2>{label}</h2><span class="count">{len(items)}</span></summary>{inner}</details>')
    body = f"""
<div class="narrow">
  <header class="doc-head">
    <p class="eyebrow">Publications</p>
    <h1>Publications</h1>
    <div class="lede"><p>Compiled from Google Scholar and reconciled against ORCID and Crossref. The most current
    lists are on <a href="https://orcid.org/{esc(site.get('orcid'))}">ORCID</a> and
    <a href="https://scholar.google.com/citations?user=pCIpAvIAAAAJ">Google Scholar</a>.</p></div>
    <p class="chips">{''.join(counts)}</p>
  </header>
  {''.join(parts)}
</div>
"""
    return page(site, "Publications", body, "publications.html", description=f"Publications by {site['name']}")


def build_writing(site, posts):
    items = "".join(post_item(p) for p in posts) or '<li class="empty">No posts yet.</li>'
    body = f"""
<div class="narrow">
  <header class="doc-head">
    <p class="eyebrow">Writing</p>
    <h1>Notes and news</h1>
    <div class="lede"><p>Occasional writing on research, AI and the environment, and news from the group.
    <a href="feed.xml">RSS feed</a>.</p></div>
  </header>
  <ul class="posts big">{items}</ul>
</div>
"""
    return page(site, "Writing", body, "writing.html")


def build_post(site, p, newer, older):
    nav = []
    if older:
        nav.append(f'<a href="{older["slug"]}.html">Older: {esc(older["title"])}</a>')
    if newer:
        nav.append(f'<a href="{newer["slug"]}.html">Newer: {esc(newer["title"])}</a>')
    tags = "".join(f"<span>{esc(t)}</span>" for t in p["tags"])
    body = f"""
<article class="narrow post">
  <header class="doc-head">
    <p class="eyebrow"><time datetime="{p['date'].isoformat()}">{nice_date(p['date'])}</time></p>
    <h1>{esc(p['title'])}</h1>
    {f'<p class="tags">{tags}</p>' if tags else ''}
  </header>
  <div class="prose">{p['html']}</div>
  <nav class="post-nav" aria-label="More posts"><a href="../writing.html">All posts</a>{''.join(nav)}</nav>
</article>
"""
    return page(site, p["title"], body, "writing.html", prefix="../", description=p["summary"])


def build_events(site, events):
    up, past = split_events(events)
    up_html = "".join(event_card(e) for e in up) or '<p class="empty">Nothing upcoming is listed yet.</p>'
    past_html = "".join(event_card(e, True) for e in past) or '<p class="empty">No past events listed.</p>'
    body = f"""
<div class="narrow">
  <header class="doc-head">
    <p class="eyebrow">Events</p>
    <h1>Where I'll be</h1>
    <div class="lede"><p>Conferences, talks and workshops. If you will be at one of these and would like to meet,
    email <span class="sel">{esc(site['email'])}</span>.</p></div>
  </header>
  <section class="cv-sec"><h2>Upcoming</h2><div class="events">{up_html}</div></section>
  <section class="cv-sec"><h2>Past</h2><div class="events">{past_html}</div></section>
</div>
"""
    return page(site, "Events", body, "events.html")


def build_md_page(site, src, out, eyebrow, show_email=False):
    raw = (CONTENT / src).read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*\n(.*)$", raw, re.S)
    meta, body_md = (yaml.safe_load(m.group(1)), m.group(2)) if m else ({}, raw)
    html_body = md(body_md)
    toc = []
    def anchor(mt):
        title = re.sub(r"<[^>]+>", "", mt.group(1))
        sid = slugify(title)
        toc.append(f'<li><a href="#{sid}">{title}</a></li>')
        return f'<h2 id="{sid}">{mt.group(1)}</h2>'
    html_body = re.sub(r"<h2>(.*?)</h2>", anchor, html_body)
    body = f"""
<div class="doc">
  <aside class="toc" aria-label="Sections">
    <p class="toc-label">Contents</p>
    <ol>{''.join(toc)}</ol>
  </aside>
  <article class="doc-main">
    <header class="doc-head">
      <p class="eyebrow">{esc(eyebrow)}</p>
      <h1>{esc(meta.get('title', eyebrow))}</h1>
      <div class="lede">{md(meta.get('intro', ''))}</div>
      {f'<p class="cv-actions"><span class="sel">{esc(site["email"])}</span></p>' if show_email else ''}
    </header>
    <div class="prose work">{html_body}</div>
  </article>
</div>
"""
    return page(site, meta.get("title", eyebrow), body, out, description=meta.get("description", ""))


def load_mentions():
    ms = load("content/mentions.yml").get("mentions") or []
    for m in ms:
        m["_d"] = as_date(m["date"])
    return sorted(ms, key=lambda m: m["_d"], reverse=True)


def mention_item(m):
    note = f'<p>{md_inline(m["note"])}</p>' if m.get("note") else ""
    return f"""<li class="post-item mention">
  <span class="m-meta"><span class="m-outlet">{esc(m.get('outlet', ''))}</span><time datetime="{m['_d'].isoformat()}">{nice_date(m['_d'])}</time></span>
  <a href="{esc(m['url'])}">{esc(m['title'])}</a>
  {note}
</li>"""


def build_media(site, mentions):
    items = "".join(mention_item(m) for m in mentions) or '<li class="empty">Nothing listed yet.</li>'
    body = f"""
<div class="narrow">
  <header class="doc-head">
    <p class="eyebrow">Media</p>
    <h1>Coverage of my work</h1>
    <div class="lede"><p>News stories, features and case studies that mention my research. For academic citations,
    see <a href="https://scholar.google.com/citations?user=pCIpAvIAAAAJ">Google Scholar</a>.</p></div>
  </header>
  <ul class="posts big">{items}</ul>
</div>
"""
    return page(site, "Media", body, "media.html", description=f"Coverage of work by {site['name']}")


def build_feed(site, posts):
    base = site.get("url", "").rstrip("/")
    items = "".join(f"""<item><title>{esc(p['title'])}</title><link>{base}/posts/{p['slug']}.html</link>
<guid>{base}/posts/{p['slug']}.html</guid><pubDate>{datetime.combine(p['date'], datetime.min.time()).strftime('%a, %d %b %Y 00:00:00 +0000')}</pubDate>
<description>{esc(p['summary'])}</description></item>""" for p in posts[:20])
    return f"""<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0"><channel><title>{esc(site['name'])}</title><link>{base}/</link>
<description>Writing and news from {esc(site['name'])}</description>{items}</channel></rss>
"""


def main():
    site = load("site.yml")
    themes = load("content/themes.yml")
    cv = load("content/cv.yml")
    pubs = load("content/publications.yml")
    events = (load("content/events.yml").get("events") or [])
    posts = load_posts()

    if OUT.exists():
        shutil.rmtree(OUT)
    (OUT / "posts").mkdir(parents=True)
    shutil.copytree(ROOT / "static", OUT / "static")

    def write(name, text):
        (OUT / name).write_text(text, encoding="utf-8")

    write("index.html", build_home(site, themes, posts, events, load_mentions()))
    write("cv.html", build_cv(site, cv))
    write("publications.html", build_pubs(site, pubs))
    write("writing.html", build_writing(site, posts))
    write("events.html", build_events(site, events))
    write("media.html", build_media(site, load_mentions()))
    write("teaching.html", build_md_page(site, "teaching.md", "teaching.html", "Teaching and training", True))
    write("work-with-me.html", build_md_page(site, "work-with-me.md", "work-with-me.html", "Opportunities", True))
    write("feed.xml", build_feed(site, posts))
    for i, p in enumerate(posts):
        newer = posts[i - 1] if i > 0 else None
        older = posts[i + 1] if i + 1 < len(posts) else None
        write(f"posts/{p['slug']}.html", build_post(site, p, newer, older))
    (OUT / ".nojekyll").write_text("")
    print(f"Built {8 + len(posts)} pages into {OUT}")


if __name__ == "__main__":
    main()
