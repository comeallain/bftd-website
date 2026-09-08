#!/usr/bin/env python3
"""
Build index.html from content.json + template.html.

    python3 build.py

Edit content.json, never index.html — index.html is generated and any hand
edits are overwritten on the next build. Requires nothing but Python 3.
"""
import json, os, re, struct, sys, html

ROOT = os.path.dirname(os.path.abspath(__file__))

def esc(s):
    """Escape a plain-text value for use in HTML."""
    return html.escape(str(s), quote=True)

# ---------------------------------------------------------------- image size
def image_size(path):
    """Read pixel dimensions straight from the file header. PNG and JPEG."""
    f = os.path.join(ROOT, path.lstrip('/'))
    if not os.path.exists(f):
        print(f"  ! missing image: {path}", file=sys.stderr)
        return None
    with open(f, 'rb') as fh:
        head = fh.read(26)
        if head[:8] == b'\x89PNG\r\n\x1a\n':
            w, h = struct.unpack('>II', head[16:24])
            return w, h
        if head[:2] == b'\xff\xd8':                       # JPEG
            fh.seek(2)
            while True:
                b = fh.read(1)
                if not b:
                    break
                if b != b'\xff':
                    continue
                marker = fh.read(1)
                while marker == b'\xff':
                    marker = fh.read(1)
                m = marker[0]
                if m in (0xD8, 0xD9) or 0xD0 <= m <= 0xD7:
                    continue
                seglen = struct.unpack('>H', fh.read(2))[0]
                if m in (0xC0, 0xC1, 0xC2, 0xC3, 0xC5, 0xC6, 0xC7,
                         0xC9, 0xCA, 0xCB, 0xCD, 0xCE, 0xCF):
                    fh.read(1)
                    h, w = struct.unpack('>HH', fh.read(4))
                    return w, h
                fh.seek(seglen - 2, 1)
    print(f"  ! could not read dimensions: {path}", file=sys.stderr)
    return None

def img(src, alt, cls='', lazy=True, extra=''):
    """An <img> with width/height baked in, so the layout never jumps."""
    wh = image_size(src)
    dim = f' width="{wh[0]}" height="{wh[1]}"' if wh else ''
    c = f' class="{cls}"' if cls else ''
    load = ' loading="lazy"' if lazy else ' loading="eager" fetchpriority="high"'
    return f'<img src="{esc(src)}" alt="{esc(alt)}"{c}{dim}{load}{extra}>'

# ---------------------------------------------------------------- fragments
ARROW = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
         'stroke-linecap="round"><path d="M5 12h14M12 5l7 7-7 7"/></svg>')
EXTLINK = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
           'stroke-linecap="round"><path d="M18 13v6a2 2 0 01-2 2H5a2 2 0 01-2-2V8a2 2 0 '
           '012-2h6M15 3h6v6M10 14L21 3"/></svg>')
PLAY = '<svg viewBox="0 0 24 24"><polygon points="6,3 20,12 6,21"/></svg>'

PILLAR_ICONS = {
    'eye':    '<path d="M1 12s4-8 11-8 11 8 11 8-4 8-11 8-11-8-11-8z"/><circle cx="12" cy="12" r="3"/>',
    'camera': '<path d="M23 7l-7 5 7 5V7z"/><rect x="1" y="5" width="15" height="14" rx="2" ry="2"/>',
    'globe':  ('<circle cx="12" cy="12" r="10"/><path d="M2 12h20M12 2a15.3 15.3 0 0 1 4 10 '
               '15.3 15.3 0 0 1-4 10 15.3 15.3 0 0 1-4-10 15.3 15.3 0 0 1 4-10z"/>'),
}
SOCIAL_ICONS = {
    'Vimeo': ('<path d="M22 7.42c-.09 2.1-1.56 4.97-4.39 8.62C14.7 19.69 12.34 21.5 10.37 '
              '21.5c-1.22 0-2.25-1.13-3.09-3.38-.56-2.06-1.12-4.12-1.69-6.18-.62-2.25-1.29-3.38-2-3.38-.16 '
              '0-.7.33-1.63.98L1 8.32c1.03-.9 2.04-1.81 3.04-2.72C5.47 4.36 6.6 3.69 7.39 '
              '3.62c1.42-.14 2.29.84 2.61 2.92.35 2.25.59 3.65.72 4.18.4 1.81.84 2.72 1.31 '
              '2.72.37 0 .93-.59 1.67-1.76.75-1.17 1.14-2.07 1.2-2.69.1-1.03-.3-1.55-1.2-1.55-.43 '
              '0-.87.1-1.33.29.88-2.89 2.56-4.3 5.05-4.21 1.84.05 2.71 1.25 2.58 3.6z"/>'),
    'IMDb':  '<path d="M2 3h3v18H2V3zm5 0h3.5l1.5 9 1.5-9H17v18h-2.5V9L13 18h-2L9.5 9v12H7V3zm13 0h2v18h-2V3z"/>',
}

# ---------------------------------------------------------------- renderers
def r_head(c):
    s = c['site']
    og = s['url'].rstrip('/') + s['ogImage']
    return '\n'.join([
        f'<title>{esc(s["title"])}</title>',
        f'<meta name="description" content="{esc(s["description"])}">',
        f'<link rel="canonical" href="{esc(s["url"])}">',
        f'<meta property="og:title" content="{esc(s["ogTitle"])}">',
        f'<meta property="og:description" content="{esc(s["ogDescription"])}">',
        '<meta property="og:type" content="website">',
        f'<meta property="og:url" content="{esc(s["url"])}">',
        f'<meta property="og:image" content="{esc(og)}">',
        '<meta property="og:image:width" content="1200">',
        '<meta property="og:image:height" content="630">',
        f'<meta property="og:site_name" content="{esc(s["title"])}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{esc(s["ogTitle"])}">',
        f'<meta name="twitter:description" content="{esc(s["ogDescription"])}">',
        f'<meta name="twitter:image" content="{esc(og)}">',
        '<meta name="theme-color" content="#080808">',
    ])

def r_nav(c, prefix=''):
    """prefix is '/' on project pages, so #projects becomes /#projects."""
    out = []
    for l in c['nav']:
        href = l['href']
        if prefix:
            href = '/' if href == '#' else prefix + href
        active = ' active' if l.get('active') and not prefix else ''
        out.append(f'    <li><a href="{esc(href)}" class="nav__link{active}">{esc(l["label"])}</a></li>')
    return '\n'.join(out)

def r_hero(c):
    h = c['hero']
    eyebrow = f'    <p class="hero__pre">{esc(h["eyebrow"])}</p>\n' if h.get('eyebrow') else ''
    title = '<br>'.join(esc(l) for l in h['titleLines'])
    em = f'<em>{esc(h["titleEm"])}</em>' if h.get('titleEm') else ''
    return f'''<section class="hero">
  <div class="hero__bg">{img(h['image'], h['imageAlt'], lazy=False)}</div>
  <div class="hero__ov"></div><div class="hero__vig"></div>
  <div class="hero__c">
    <div class="hero__mark"><svg class="hand-icon" aria-hidden="true"><use xlink:href="#bftd-hand" href="#bftd-hand"></use></svg></div>
{eyebrow}    <h1 class="hero__t">{title}{em}</h1>
    <p class="hero__tag">{esc(h['tagline'])}</p>
  </div>
  <div class="hero__sc"><span>Scroll</span><div class="hero__scl"></div></div>
</section>'''

def r_project_cards(c):
    out = []
    for i, p in enumerate(c['projects']['items']):
        out.append(
            f'<a class="pc" href="/projects/{esc(p["id"])}/" data-idx="{i}">'
            f'<div class="pc__img">{img(p["img"], p["title"])}'
            f'<div class="pc__ov"></div>'
            f'<span class="pc__st">{esc(p["status"])}</span>'
            f'<span class="pc__num">{i+1:02d}</span></div>'
            f'<div class="pc__b"><p class="pc__g">{esc(p["type"])}</p>'
            f'<h3 class="pc__tt">{esc(p["title"])}</h3>'
            f'<p class="pc__ll">{esc(p["logline"])}</p>'
            f'<span class="pc__cta">View Project {ARROW}</span>'
            f'</div></a>')
    return ''.join(out)

def r_reel_tabs(c):
    return '\n'.join(
        f'      <button class="reel__tab{" active" if i == 0 else ""}" data-cat="{esc(t["key"])}">'
        f'{esc(t["label"])}</button>' for i, t in enumerate(c['reel']['categories']))

def r_reel_items(c):
    labels = {'film': 'Feature Film', 'music': 'Music Video',
              'commercial': 'Commercial', 'other': 'Other'}
    out = []
    for i, v in enumerate(c['reel']['items']):
        dur = f'<span class="reel__item-dur">{esc(v["dur"])}</span>' if v.get('dur') else ''
        sub = f'<p class="reel__item-sub">{esc(v["sub"])}</p>' if v.get('sub') else ''
        out.append(
            f'<div class="reel__item{" active" if i == 0 else ""}" data-idx="{i}">'
            f'{img(v["thumb"], v["title"])}{dur}'
            f'<div class="reel__item-ov"><p class="reel__item-cat">{esc(labels.get(v["cat"], v["cat"]))}</p>'
            f'<p class="reel__item-t">{esc(v["title"])}</p>{sub}</div>'
            f'<div class="reel__item-play">{PLAY}</div></div>')
    return ''.join(out)

def r_about(c):
    a = c['about']
    paras = '\n        '.join(f'<p>{p}</p>' for p in a['storyParagraphs'])
    return f'''<div class="manifesto rv">
      <p class="manifesto__quote">{esc(a['manifestoQuote'])}</p>
      <p class="manifesto__attr">{esc(a['manifestoAttr'])}</p>
    </div>
    <div class="about-grid">
      <div class="about-collage rv">
        <div class="about-collage__main">{img(a['collageMain'], a['collageMainAlt'])}</div>
        <div class="about-collage__float">{img(a['collageFloat'], a['collageFloatAlt'])}</div>
        <div class="about-collage__accent"></div>
      </div>
      <div class="about-story rv rv1">
        <h3>{esc(a['storyHeading'])}</h3>
        {paras}
      </div>
    </div>'''

def r_pillars(c):
    out = []
    for i, p in enumerate(c['about']['pillars']):
        rv = f' rv{i}' if i else ''
        icon = PILLAR_ICONS.get(p['icon'], PILLAR_ICONS['eye'])
        out.append(
            f'<div class="pillar rv{rv}"><div class="pillar__icon">'
            f'<svg viewBox="0 0 24 24" stroke-linecap="round" stroke-linejoin="round">{icon}</svg></div>'
            f'<h4 class="pillar__title">{esc(p["title"])}</h4>'
            f'<p class="pillar__text">{esc(p["text"])}</p></div>')
    return '<div class="pillars">' + ''.join(out) + '</div>'

def r_stats(c):
    st = c['about']['stats']
    cells = ''.join(
        f'<div class="stat"><p class="stat__num" data-target="{int(s["target"])}">0</p>'
        f'<p class="stat__label">{esc(s["label"])}</p></div>' for s in st)
    return (f'<div class="stats-bar rv" style="grid-template-columns:repeat({len(st)},1fr)">'
            f'{cells}</div>')

def r_filmmaker(c):
    f = c['filmmaker']
    bio = '\n        '.join(f'<p class="team-spot__bio">{b}</p>' for b in f['bio'])
    tags = ''.join(f'<span class="role-tag">{esc(t)}</span>' for t in f['roleTags'])
    return f'''<div class="sec__h rv"><p class="sec__l">{esc(f['label'])}</p><h2 class="sec__t">{esc(f['heading'])}</h2></div>
    <div class="team-spot rv">
      <div class="team-spot__portrait">{img(f['portrait'], f['portraitAlt'])}</div>
      <div class="team-spot__info">
        <h3>{esc(f['name'])}</h3>
        <p class="team-spot__role">{esc(f['role'])}</p>
        {bio}
        <div class="team-spot__roles">{tags}</div>
        <a href="{esc(f['ctaUrl'])}" target="_blank" rel="noopener" class="btn">{esc(f['ctaLabel'])} {EXTLINK}</a>
      </div>
    </div>'''

def r_contact(c):
    ct = c['contact']
    details = '\n        '.join(
        f'<div class="contact__detail"><p class="contact__dl">{esc(d["label"])}</p>'
        f'<p class="contact__dv">{esc(d["value"])}</p></div>' for d in ct['details'])
    socials = ''.join(
        f'<a href="{esc(s["url"])}" target="_blank" rel="noopener" class="contact__sl" '
        f'aria-label="{esc(s["name"])}"><svg viewBox="0 0 24 24" fill="currentColor">'
        f'{SOCIAL_ICONS.get(s["name"], "")}</svg></a>' for s in ct['socials'])
    return f'''<div class="contact__info rv">
        {details}
        <div class="contact__detail"><p class="contact__dl">{esc(ct['socialsLabel'])}</p>
          <div class="contact__socials">{socials}</div>
        </div>
      </div>'''

def r_footer(c, prefix=''):
    f = c['footer']
    home = prefix if prefix else '#'
    links = ''.join(
        f'<li><a href="{esc(l["url"])}" target="_blank" rel="noopener" class="ft__l">'
        f'{esc(l["label"])}</a></li>' for l in f['links'])
    return f'''<footer class="ft"><div class="con"><div class="ft__in">
  <a href="{home}" class="ft__logo"><svg class="hand-icon" aria-hidden="true"><use xlink:href="#bftd-hand" href="#bftd-hand"></use></svg>{esc(f['logoText'])}</a>
  <p class="ft__c">{esc(f['copyright'])}</p>
  <ul class="ft__ls">{links}</ul>
</div></div></footer>'''

def r_site_data(c):
    """The data the page's JavaScript needs, as JSON that cannot break out of the tag."""
    payload = {'projects': c['projects']['items'], 'reel': c['reel']['items']}
    j = json.dumps(payload, ensure_ascii=False, separators=(',', ':'))
    return j.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')


# ---------------------------------------------------------------- structured data
SCHEMA_TYPE = {'Series': 'TVSeries', 'Documentary': 'Movie', 'Feature Film': 'Movie'}

def _ld(obj):
    """A <script type=application/ld+json> block that cannot break out of its tag."""
    j = json.dumps(obj, ensure_ascii=False, separators=(',', ':'))
    j = j.replace('<', '\\u003c').replace('>', '\\u003e').replace('&', '\\u0026')
    return f'<script type="application/ld+json">{j}</script>'

def r_jsonld_home(c):
    s, f = c['site'], c['filmmaker']
    base = s['url'].rstrip('/')
    socials = [x['url'] for x in c['contact']['socials']]
    return _ld({
        '@context': 'https://schema.org',
        '@graph': [
            {'@type': 'Organization', '@id': f'{base}/#organization',
             'name': s['title'], 'url': s['url'],
             'description': s['ogDescription'],
             'logo': f'{base}/images/bftd-lockup-h-black.png',
             'image': base + s['ogImage'],
             'sameAs': socials,
             'founder': {'@id': f'{base}/#richie'},
             'email': 'contact@bftdfilms.com',
             'areaServed': ['US', 'IE']},
            {'@type': 'WebSite', '@id': f'{base}/#website', 'url': s['url'],
             'name': s['title'], 'publisher': {'@id': f'{base}/#organization'},
             'inLanguage': 'en'},
            {'@type': 'Person', '@id': f'{base}/#richie', 'name': f['name'],
             'jobTitle': 'Director', 'description': re.sub(r'<[^>]+>', '', f['bio'][0]),
             'image': base + f['portrait'],
             'sameAs': [f['ctaUrl'], 'https://www.imdb.com/name/nm1100217/'],
             'worksFor': {'@id': f'{base}/#organization'}},
            {'@type': 'ItemList', '@id': f'{base}/#slate', 'name': 'Productions',
             'itemListElement': [
                 {'@type': 'ListItem', 'position': i + 1,
                  'url': f'{base}/projects/{p["id"]}/', 'name': p['title']}
                 for i, p in enumerate(c['projects']['items'])]},
        ]})

def r_jsonld_project(c, p):
    base = c['site']['url'].rstrip('/')
    return _ld({
        '@context': 'https://schema.org',
        '@type': SCHEMA_TYPE.get(p['type'], 'Movie'),
        '@id': f'{base}/projects/{p["id"]}/#work',
        'name': p['title'],
        'url': f'{base}/projects/{p["id"]}/',
        'description': p['logline'],
        'abstract': ' '.join(p['synopsis']),
        'image': base + p['img'],
        'genre': p['type'],
        'creativeWorkStatus': p['status'],
        'inLanguage': 'en',
        'productionCompany': {'@id': f'{base}/#organization'},
        'director': {'@id': f'{base}/#richie'},
    })

# ---------------------------------------------------------------- project pages
def r_head_project(c, p):
    s = c['site']
    base = s['url'].rstrip('/')
    url = f'{base}/projects/{p["id"]}/'
    og = base + p['img']
    title = f'{p["title"]} — {s["title"]}'
    wh = image_size(p['img'])
    dims = ([f'<meta property="og:image:width" content="{wh[0]}">',
             f'<meta property="og:image:height" content="{wh[1]}">'] if wh else [])
    return '\n'.join([
        f'<title>{esc(title)}</title>',
        f'<meta name="description" content="{esc(p["logline"])}">',
        f'<link rel="canonical" href="{esc(url)}">',
        f'<meta property="og:title" content="{esc(p["title"])}">',
        f'<meta property="og:description" content="{esc(p["logline"])}">',
        '<meta property="og:type" content="video.movie">',
        f'<meta property="og:url" content="{esc(url)}">',
        f'<meta property="og:image" content="{esc(og)}">', *dims,
        f'<meta property="og:site_name" content="{esc(s["title"])}">',
        '<meta name="twitter:card" content="summary_large_image">',
        f'<meta name="twitter:title" content="{esc(p["title"])}">',
        f'<meta name="twitter:description" content="{esc(p["logline"])}">',
        f'<meta name="twitter:image" content="{esc(og)}">',
        '<meta name="theme-color" content="#080808">',
    ])

ARROW_L = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
           'stroke-linecap="round"><path d="M15 18l-6-6 6-6"/></svg>')
ARROW_R = ('<svg viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" '
           'stroke-linecap="round"><path d="M9 18l6-6-6-6"/></svg>')

def build_project_pages(c, tpl):
    items = c['projects']['items']
    written = []
    for i, p in enumerate(items):
        prev_p = items[i - 1] if i else None
        next_p = items[i + 1] if i + 1 < len(items) else None
        slots = {
            'HEAD_META':    r_head_project(c, p),
            'NAV_LINKS':    r_nav(c, prefix='/'),
            'PP_IMAGE':     img(p['img'], p['title'], lazy=False),
            'PP_TYPE':      esc(p['type']),
            'PP_TITLE':     esc(p['title']),
            'PP_STATUS':    esc(p['status']),
            'PP_LOGLINE':   esc(p['logline']),
            'PP_SYNOPSIS':  ''.join(f'<p>{esc(x)}</p>' for x in p['synopsis']),
            'PP_PREV':      (f'<a href="/projects/{esc(prev_p["id"])}/">{ARROW_L} {esc(prev_p["title"])}</a>'
                             if prev_p else '<span></span>'),
            'PP_NEXT':      (f'<a href="/projects/{esc(next_p["id"])}/">{esc(next_p["title"])} {ARROW_R}</a>'
                             if next_p else '<span></span>'),
            'FOOTER':       r_footer(c, prefix='/'),
            'JSONLD':       r_jsonld_project(c, p),
            'ANALYTICS':    esc(c['site']['analytics']),
        }
        out = tpl
        for k, v in slots.items():
            out = out.replace('{{' + k + '}}', v)
        left = re.findall(r'\{\{(\w+)\}\}', out)
        if left:
            sys.exit(f"ERROR: project page {p['id']} has unfilled slots: {sorted(set(left))}")
        out = ('<!-- GENERATED FILE — do not edit.\n'
               '     Edit content.json, then run: python3 build.py -->\n') + out
        d = os.path.join(ROOT, 'projects', p['id'])
        os.makedirs(d, exist_ok=True)
        with open(os.path.join(d, 'index.html'), 'w', encoding='utf-8') as f:
            f.write(out)
        written.append(f'projects/{p["id"]}/')

    # Remove pages for projects that are no longer in content.json, otherwise a
    # deleted project stays published at its old URL.
    pdir = os.path.join(ROOT, 'projects')
    if os.path.isdir(pdir):
        live = {p['id'] for p in items}
        for name in sorted(os.listdir(pdir)):
            d = os.path.join(pdir, name)
            if os.path.isdir(d) and name not in live:
                page = os.path.join(d, 'index.html')
                if os.path.exists(page):
                    os.remove(page)
                if not os.listdir(d):
                    os.rmdir(d)
                print(f"  removed stale page: projects/{name}/")
    return written

# ---------------------------------------------------------------- extras
def write_extras(c, pages):
    s = c['site']
    base = s['url'].rstrip('/')
    with open(os.path.join(ROOT, 'robots.txt'), 'w') as f:
        f.write(f"User-agent: *\nAllow: /\n\nSitemap: {base}/sitemap.xml\n")
    urls = ''.join(
        f'  <url>\n    <loc>{base}/{p}</loc>\n'
        f'    <changefreq>monthly</changefreq>\n'
        f'    <priority>{"1.0" if p == "" else "0.8"}</priority>\n  </url>\n'
        for p in [''] + pages)
    with open(os.path.join(ROOT, 'sitemap.xml'), 'w') as f:
        f.write('<?xml version="1.0" encoding="UTF-8"?>\n'
                '<urlset xmlns="http://www.sitemaps.org/schemas/sitemap/0.9">\n'
                + urls + '</urlset>\n')
    print(f"  robots.txt, sitemap.xml ({len(pages) + 1} urls)")

# ---------------------------------------------------------------- main
def main():
    with open(os.path.join(ROOT, 'content.json'), encoding='utf-8') as f:
        c = json.load(f)
    with open(os.path.join(ROOT, 'template.html'), encoding='utf-8') as f:
        tpl = f.read()

    slots = {
        'HEAD_META':        r_head(c),
        'NAV_LINKS':        r_nav(c),
        'HERO':             r_hero(c),
        'PROJECTS_LABEL':   esc(c['projects']['label']),
        'PROJECTS_HEADING': esc(c['projects']['heading']),
        'PROJECT_CARDS':    r_project_cards(c),
        'REEL_LABEL':       esc(c['reel']['label']),
        'REEL_HEADING':     esc(c['reel']['heading']),
        'REEL_POSTER':      esc(c['reel']['poster']),
        'REEL_NOW_TITLE':   esc(c['reel']['nowPlayingTitle']),
        'REEL_NOW_META':    esc(c['reel']['nowPlayingMeta']),
        'REEL_TABS':        r_reel_tabs(c),
        'REEL_ITEMS':       r_reel_items(c),
        'REEL_VIMEO':       esc(c['reel']['vimeoUrl']),
        'ABOUT_LABEL':      esc(c['about']['label']),
        'ABOUT_HEADING':    esc(c['about']['heading']),
        'ABOUT':            r_about(c),
        'PILLARS':          r_pillars(c),
        'STATS':            r_stats(c),
        'FILMMAKER':        r_filmmaker(c),
        'CONTACT_LABEL':    esc(c['contact']['label']),
        'CONTACT_HEADING':  esc(c['contact']['heading']),
        'CONTACT_INFO':     r_contact(c),
        'FORM_ACTION':      esc(c['contact']['formAction']),
        'FORM_SUBJECT':     esc(c['contact']['formSubject']),
        'FOOTER':           r_footer(c),
        'SITE_DATA':        r_site_data(c),
        'ANALYTICS':        esc(c['site']['analytics']),
        'JSONLD':           r_jsonld_home(c),
    }

    out = tpl
    for k, v in slots.items():
        token = '{{' + k + '}}'
        if token not in out:
            print(f"  ! unused slot: {k}", file=sys.stderr)
        out = out.replace(token, v)

    leftover = re.findall(r'\{\{(\w+)\}\}', out)
    if leftover:
        sys.exit(f"ERROR: template slots never filled: {sorted(set(leftover))}")

    out = ('<!-- GENERATED FILE — do not edit.\n'
           '     Edit content.json, then run: python3 build.py -->\n') + out

    with open(os.path.join(ROOT, 'index.html'), 'w', encoding='utf-8') as f:
        f.write(out)
    print(f"  index.html — {len(out):,} bytes")

    with open(os.path.join(ROOT, 'project.html'), encoding='utf-8') as f:
        ptpl = f.read()
    pages = build_project_pages(c, ptpl)
    print(f"  {len(pages)} project pages")

    write_extras(c, pages)
    print("build ok")

if __name__ == '__main__':
    main()
