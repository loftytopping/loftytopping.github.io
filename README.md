# David Topping, personal website

A small static site in the same style as the group site. Content lives in plain text files;
`build.py` turns them into HTML and a GitHub Action publishes the result to GitHub Pages.

## What to edit

| To change | Edit |
|---|---|
| Name, roles, intro, links (ORCID, Scholar, LinkedIn...) | `site.yml` |
| Areas of work on the home page | `content/themes.yml` |
| CV page | `content/cv.yml` |
| Full publication list | `content/publications.yml` (add new items at the top) |
| Media coverage | `content/mentions.yml` |
| Teaching, Work with me | `content/teaching.md`, `content/work-with-me.md` |
| Photo | `static/profile-crop.jpg` (path set in `site.yml`) |
| PDF CV | `static/David_Topping_CV.pdf`, or regenerate with `python make_cv_pdf.py` |
| Where you'll be | `content/events.yml`: upcoming and past are sorted by date, and anything on today shows as "Happening now" with a "Now at ..." line under your name |
| Posts | add a Markdown file to `content/posts/` |

### Writing a post

Create `content/posts/2026-11-02-my-post.md`:

```
---
title: My post title
date: 2026-11-02
summary: One line shown in lists and the RSS feed.
tags: [ai, air-quality]
draft: false        # set to true to keep it off the site
---

Write in Markdown here. Links, **bold**, lists, images and code blocks all work.
```

Images can go in `static/` and be referenced as `../static/picture.jpg` from a post.

## Preview locally

```
pip install -r requirements.txt
python build.py
python -m http.server -d _site 8000
```

then open http://localhost:8000.

## Publish (one-off setup)

1. Create a public repository called `loftytopping.github.io` under your GitHub account.
2. Push this folder to its `main` branch.
3. In the repository, go to Settings, Pages, and set Source to **GitHub Actions**.

Every push to `main` rebuilds and publishes the site to https://loftytopping.github.io.
It also rebuilds once a day so events move from Upcoming to Past without you touching it.
To use a custom domain later, add it under Settings, Pages and change `url` in `site.yml`.
