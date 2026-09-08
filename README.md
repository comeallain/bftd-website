# bftd-website

Back From The Dead Productions — official website, live at
**[bftdfilms.com](https://bftdfilms.com)**. Static site, served by GitHub Pages.

## Editing the site

**Edit `content.json`. Never edit `index.html`.**

`index.html` is generated. Anything typed into it by hand is overwritten on the
next build. All copy, projects, reel videos, images and SEO metadata live in
`content.json`.

```bash
python3 build.py     # regenerates index.html, robots.txt and sitemap.xml
```

No dependencies — plain Python 3, which ships with macOS.

Pushing a change to `content.json` on `main` also triggers
`.github/workflows/build.yml`, which rebuilds and commits `index.html` for you.
So editing `content.json` directly on github.com is enough to publish.

## Layout

| File | What it is |
|---|---|
| `content.json` | **All site content.** The only file you normally edit. |
| `template.html` | Page shell — CSS, JavaScript, and `{{SLOT}}` markers. |
| `build.py` | Fills the template from `content.json`. |
| `index.html` | **Generated.** Do not edit. |
| `images/` | Site images. |
| `404.html` | Not-found page. |
| `robots.txt`, `sitemap.xml` | **Generated** by `build.py`. |

## Adding a project

Add an object to `projects.items` in `content.json`:

```json
{
  "id": "short-slug",
  "title": "Project Title",
  "type": "Feature Film",
  "status": "In Development",
  "img": "/images/your-poster.jpg",
  "logline": "One sentence.",
  "synopsis": ["First paragraph.", "Second paragraph."]
}
```

Apostrophes, quotes and ampersands are all safe — the build escapes them. Order
in the file is the order on the page.

## Adding a reel video

Add an object to `reel.items`. Use `"platform": "youtube"` with the ID from
`youtube.com/watch?v=XXXXXXXXXXX`, or `"platform": "vimeo"` with the number from
`vimeo.com/123456789`. `cat` is one of `film`, `music`, `commercial`, `other`.
Leave `sub` or `dur` as `""` and they simply won't render.

## Images

Keep them under roughly 300 KB. `build.py` reads each image's real dimensions
and writes `width`/`height` onto the tag, so the layout never jumps while
images load. To resize on macOS:

```bash
sips -Z 1200 -s format jpeg -s formatOptions 78 big.png --out images/small.jpg
```
