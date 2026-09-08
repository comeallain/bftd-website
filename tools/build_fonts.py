#!/usr/bin/env python3
"""Turn a Google Fonts css2 response into self-hosted woff2 files + fonts/fonts.css."""
import re, subprocess, os, sys
from collections import defaultdict

SUBSETS = {'latin', 'latin-ext'}          # the site is English and Irish; no Cyrillic or Greek

css = open(sys.argv[1], encoding='utf-8').read()
blocks = re.findall(r'/\*\s*([\w-]+)\s*\*/\s*(@font-face\s*\{.*?\})', css, re.S)

# Group by file URL. One physical file can serve a range of weights (variable
# fonts) — declaring each weight as its own rule would reference files that do
# not exist, and every bold weight would silently fall back to a system font.
groups = defaultdict(lambda: {'weights': set()})
for subset, block in blocks:
    if subset not in SUBSETS:
        continue
    g = groups[re.search(r'url\((https://[^)]+)\)', block).group(1)]
    g['weights'].add(int(re.search(r'font-weight:\s*(\d+)', block).group(1)))
    g.update(fam=re.search(r"font-family:\s*'([^']+)'", block).group(1),
             style=re.search(r'font-style:\s*(\w+)', block).group(1),
             subset=subset,
             range=re.search(r'unicode-range:\s*([^;}]+)', block).group(1).strip())

rules = []
for url, g in groups.items():
    fn = f"fonts/{g['fam'].lower().replace(' ', '-')}-{g['style']}-{g['subset']}.woff2"
    subprocess.run(['curl', '-sS', '-o', fn, url], check=True)
    w = sorted(g['weights'])
    rules.append((g['fam'], g['style'], str(w[0]) if len(w) == 1 else f'{w[0]} {w[-1]}', fn, g['range']))

rules.sort(key=lambda r: (r[0], r[1], r[3]))
with open('fonts/fonts.css', 'w', encoding='utf-8') as f:
    f.write("/* Self-hosted webfonts — GENERATED, do not edit.\n"
            "   Regenerate with: bash tools/fetch-fonts.sh\n"
            "   Served from our own domain so no visitor IP reaches Google.\n"
            "   DM Sans and Playfair Display are variable: one file serves a\n"
            "   weight range, which is why some rules declare two weights. */\n")
    for fam, style, weight, fn, ur in rules:
        f.write(f"@font-face{{font-family:'{fam}';font-style:{style};font-weight:{weight};"
                f"font-display:swap;src:url('/{fn}') format('woff2');unicode-range:{ur}}}\n")

refs = {fn for _, _, _, fn, _ in rules}
missing = [r for r in refs if not os.path.exists(r)]
if missing:
    sys.exit(f"ERROR: generated CSS references missing files: {missing}")
print(f"  {len(rules)} @font-face rules, {len(refs)} files, "
      f"{sum(os.path.getsize(r) for r in refs)//1024} KB")
