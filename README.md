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
| `template.html` | Homepage shell — JavaScript and `{{SLOT}}` markers. |
| `project.html` | Project detail page shell. |
| `styles.css` | All styling, shared by every page. |
| `build.py` | Fills the templates from `content.json`. |
| `index.html` | **Generated.** Do not edit. |
| `projects/<id>/` | **Generated** detail page per project. Do not edit. |
| `images/` | Site images. |
| `404.html` | Not-found page. |
| `privacy.md` | Privacy policy text. **Edit this**, not the generated page. |
| `page.html` | Shell for long-form content pages. |
| `fonts/` | Self-hosted webfonts. `fonts.css` is **generated**. |
| `tools/` | `fetch-fonts.sh` re-downloads the fonts. Rarely needed. |
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

The `id` becomes the page URL, so `"id": "zarqawi"` publishes at
`bftdfilms.com/projects/zarqawi/` with its own title, description, link preview
image and structured data. Changing an `id` changes the URL and breaks any link
already shared, so treat it as permanent once a project is public.

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

## Fonts

The typefaces are served from our own domain, not Google's CDN. That is
deliberate: loading fonts from Google transmits every visitor's IP address to
Google before they interact with anything, which is not a good position for a
company operating out of Dublin.

You should not need to touch this. If the set of typefaces ever changes, edit
the URL in `tools/fetch-fonts.sh` and run it:

```bash
bash tools/fetch-fonts.sh
```

It downloads the Latin subsets and regenerates `fonts/fonts.css`. Note that
DM Sans and Playfair Display are variable fonts — one file serves a range of
weights — which the generator handles. Declaring each weight separately would
reference files that do not exist and silently drop every bold weight back to
a system font.

## Editing the privacy policy

The policy lives in `privacy.md` as plain Markdown. Edit that file and run the
build; it publishes at `bftdfilms.com/privacy/` in the site's own design.

It supports headings, paragraphs, bullet lists, tables, `**bold**`, `_italic_`,
links and `code`. That is the whole of it — there is no wider Markdown support,
because a policy page does not need any.

To add another page of this kind (terms, for example), write the Markdown file
and add an entry to `pages` in `content.json`:

```json
{ "slug": "terms", "source": "terms.md", "title": "Terms",
  "description": "One line for search results and link previews." }
```
