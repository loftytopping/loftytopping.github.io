#!/usr/bin/env python3
"""Make the downloadable short CV (static/David_Topping_CV.pdf) from content/cv.yml.

Optional: only needed when you want to regenerate the PDF after editing cv.yml.
Needs: pip install pyyaml markdown playwright  and then  playwright install chromium
Run:   python make_cv_pdf.py
You can also just replace static/David_Topping_CV.pdf with any PDF of your own.
"""
import os
from pathlib import Path

import yaml

from build import ROOT, esc, md, md_inline, role_text, load

# Order of sections in the PDF; anything not listed is left out.
ORDER = ["Academic appointments", "Education", "Advisory and external roles", "Journal editorships",
         "Selected research funding", "SELECTED_PUBLICATIONS", "Open-source software", "Research students",
         "Teaching", "Leadership and management", "Knowledge exchange", "Selected invited talks",
         "Conference leadership"]


def font_css():
    """Use local font files if FONT_DIR is set (offline builds), otherwise Google Fonts."""
    d = os.environ.get("FONT_DIR")
    if not d:
        return ('<link rel="stylesheet" href="https://fonts.googleapis.com/css2?family=Outfit:wght@400;500;600;700'
                '&family=JetBrains+Mono:wght@400&family=Source+Serif+4:ital,wght@0,400;0,600;1,400&display=swap">')
    faces = [("Outfit", "outfit/files/outfit-latin-{w}-normal.woff2", "normal", [400, 500, 600, 700]),
             ("Source Serif 4", "source-serif-4/files/source-serif-4-latin-{w}-normal.woff2", "normal", [400, 600]),
             ("Source Serif 4", "source-serif-4/files/source-serif-4-latin-{w}-italic.woff2", "italic", [400]),
             ("JetBrains Mono", "jetbrains-mono/files/jetbrains-mono-latin-{w}-normal.woff2", "normal", [400])]
    css = []
    for fam, pat, style, weights in faces:
        for w in weights:
            css.append(f"@font-face{{font-family:'{fam}';font-style:{style};font-weight:{w};"
                       f"src:url('file://{d}/{pat.format(w=w)}') format('woff2')}}")
    return "<style>" + "".join(css) + "</style>"


def row(e):
    what = md_inline(e.get("what", ""))
    where = md_inline(e.get("where", "")) if e.get("where") else ""
    sep = ". " if where and not what.rstrip().endswith((".", ":", "?")) else " "
    return (f'<div class="row"><div class="when">{esc(e.get("when", ""))}</div>'
            f'<div class="body"><span class="what">{what}</span>{sep if where else ""}'
            f'<span class="where">{where}</span></div></div>')


def pub(p):
    doi = f' doi:{esc(p["doi"])}' if p.get("doi") else ""
    authors = esc(p["authors"]).rstrip(".").replace("Topping", "<b>Topping</b>")
    return (f'<div class="row"><div class="when">{esc(p["year"])}</div><div class="body">{authors}. '
            f'<span class="what">{esc(p["title"])}</span>. <i>{esc(p["venue"])}</i>.<span class="doi">{doi}</span></div></div>')


def main():
    site = load("site.yml")
    cv = load("content/cv.yml")
    secs = {s["heading"]: s for s in cv.get("sections", [])}
    parts = []
    for h in ORDER:
        if h == "SELECTED_PUBLICATIONS":
            pubs = "".join(pub(p) for p in (cv.get("selected_publications") or [])[:6])
            books = "".join(pub(b) for b in cv.get("books") or [])
            parts.append(f'<section><h2>Selected publications</h2>{pubs}{books}'
                         f'<p class="intro">Full list of more than 130 journal articles at {esc(site["url"])}/publications.html and on ORCID.</p></section>')
            continue
        s = secs.get(h)
        if not s:
            continue
        lim = s.get("pdf_limit")
        entries = s.get("entries", [])
        if lim == 0:
            continue
        if lim:
            entries = entries[:lim]
        intro = f'<p class="intro">{md_inline(s["intro"])}</p>' if s.get("intro") else ""
        parts.append(f'<section><h2>{esc(h)}</h2>{intro}{"".join(row(e) for e in entries)}</section>')

    roles = " · ".join(esc(role_text(r)) for r in site.get("roles", []))
    contact = f'{esc(site["email"])} · ORCID {esc(site.get("orcid", ""))} · {esc(site["url"].replace("https://", ""))}'
    html = f"""<!DOCTYPE html><html lang="en-GB"><head><meta charset="utf-8"><title>{esc(site['name'])} CV</title>
{font_css()}
<style>
@page {{ size: A4; margin: 13mm 15mm 15mm 15mm; }}
:root {{ --ink: #14232b; --muted: #4a5a62; --accent: #b35c00; --line: #e3cfb6; }}
body {{ margin: 0; color: var(--ink); font: 9pt/1.36 'Source Serif 4', Georgia, serif; }}
header {{ border-bottom: 2px solid var(--accent); padding-bottom: 8px; margin-bottom: 10px; }}
h1 {{ font: 700 22pt/1 'Outfit', sans-serif; margin: 0 0 6px; letter-spacing: -0.01em; }}
.roles {{ font: 500 10pt/1.3 'Outfit', sans-serif; color: var(--muted); margin: 0 0 4px; }}
.contact {{ font: 400 8pt 'JetBrains Mono', monospace; color: var(--accent); margin: 0; }}
.profile {{ margin: 0 0 4px; }}
.profile p {{ margin: 0; }}
section {{ margin-top: 8px; }}
h2 {{ font: 600 9pt/1 'Outfit', sans-serif; text-transform: uppercase; letter-spacing: 0.08em; color: var(--accent);
      margin: 0 0 5px; padding-bottom: 3px; border-bottom: 0.5pt solid var(--line); break-after: avoid; }}
.row {{ display: grid; grid-template-columns: 26mm 1fr; gap: 3mm; margin-bottom: 2px; break-inside: avoid; }}
.when {{ font: 400 7.6pt/1.75 'JetBrains Mono', monospace; color: var(--muted); }}
.what {{ font-family: 'Outfit', sans-serif; font-weight: 500; }}
.where {{ color: var(--ink); }}
.doi {{ font: 400 7.2pt 'JetBrains Mono', monospace; color: var(--muted); }}
.intro {{ margin: 0 0 4px; color: var(--muted); font-style: italic; }}
a {{ color: inherit; text-decoration: none; }}
</style></head><body>
<header><h1>{esc(site['name'])}</h1><p class="roles">{roles}</p><p class="contact">{contact}</p></header>
<div class="profile">{md(cv.get('summary', ''))}</div>
{''.join(parts)}
</body></html>"""
    out_html = ROOT / "_cv_print.html"
    out_html.write_text(html, encoding="utf-8")
    pdf = ROOT / (cv.get("pdf") or "static/David_Topping_CV.pdf")
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        kw = {"executable_path": os.environ["CHROMIUM"]} if os.environ.get("CHROMIUM") else {}
        b = p.chromium.launch(**kw)
        pg = b.new_page()
        pg.goto(out_html.resolve().as_uri())
        pg.wait_for_timeout(500)
        pg.pdf(path=str(pdf), format="A4", print_background=True, prefer_css_page_size=True,
               display_header_footer=True, header_template="<span></span>",
               footer_template=f'<div style="width:100%;font:7pt Helvetica,sans-serif;color:#777;padding:0 16mm;display:flex;justify-content:space-between">'
                               f'<span>{esc(site["name"])} CV</span><span><span class="pageNumber"></span> / <span class="totalPages"></span></span></div>')
        b.close()
    out_html.unlink()
    print(f"Wrote {pdf}")


if __name__ == "__main__":
    main()
