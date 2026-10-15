# Contact sheets of note covers (5 × 4 per image, id prefix + likes + title under each) — titles rarely name the
# brand, covers do. Read the output images before naming clusters or formats.
#   python3 scripts/sheet.py --match "果干|果脯" [--list 蜜饯果干] [--top 100] [--out data/qa/sheets/name]
#   python3 scripts/sheet.py --ids 6a633b94,6aaa745c,… --out data/qa/sheets/examples   (ids or 8-char prefixes, comma-separated)
# --match: regex on title + account; --list: keep notes that appear in a list whose name contains this text.
import io, json, os, re, sys, urllib.request, concurrent.futures as cf
from PIL import Image, ImageDraw, ImageFont

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[1:]
opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
lib = opt('--lib', os.path.join(ROOT, 'data/library-jg'))
items = json.load(open(os.path.join(lib, 'items.json')))
det = json.load(open(os.path.join(lib, 'det.json')))
out = opt('--out', os.path.join(ROOT, 'data/qa/sheets/sheet'))
os.makedirs(os.path.dirname(out), exist_ok=True)

if opt('--ids'):
    v = opt('--ids'); pre = [l.strip() for l in (open(v) if os.path.exists(v) else v.split(',')) if l.strip()]
    L = [next(i for i in items if i['id'].startswith(p)) for p in pre]
else:
    rx, lst = opt('--match', '.'), opt('--list')
    L = [i for i in items if re.search(rx, i['title'] + ' ' + i['subtitle'])
         and (not lst or any(lst in r[0] for r in det[i['id']]['detail']['sections'][0]['rows']))]
    L = sorted(L, key=lambda i: -(i['extra'].get('likes') or 0))[:int(opt('--top', 100))]

def font(size):
    for f in ('/System/Library/Fonts/STHeiti Medium.ttc', '/System/Library/Fonts/PingFang.ttc',
              '/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc', 'C:/Windows/Fonts/msyh.ttc'):
        if os.path.exists(f): return ImageFont.truetype(f, size)
    return ImageFont.load_default()
F = font(18)

def get(i):
    u = (i['cover'] or '').replace('http://', 'https://').replace('w/1080', 'w/360')
    try: return i['id'], Image.open(io.BytesIO(urllib.request.urlopen(u, timeout=30).read())).convert('RGB')
    except Exception: return i['id'], Image.new('RGB', (300, 400), 'gray')  # expired cover: re-crawl, or skip

with cf.ThreadPoolExecutor(12) as ex: imgs = dict(ex.map(get, L))
W, H, C, R = 300, 400, 5, 4
files = []
for p in range(0, len(L), C * R):
    sheet = Image.new('RGB', (W * C, (H + 48) * R), 'white'); d = ImageDraw.Draw(sheet)
    for k, i in enumerate(L[p:p + C * R]):
        im = imgs[i['id']]; im.thumbnail((W, H)); x, y = (k % C) * W, (k // C) * (H + 48)
        sheet.paste(im, (x, y))
        d.text((x + 4, y + H + 2), f"{i['id'][:8]} ♥{i['extra'].get('likes')}", fill='black', font=F)
        d.text((x + 4, y + H + 24), i['title'][:15].replace('\n', ' '), fill='black', font=F)
    files.append(f'{out}-{p // (C * R) + 1}.jpg'); sheet.save(files[-1], quality=80)
print(f'{len(L)} notes → ' + ' '.join(os.path.relpath(f, ROOT) for f in files))
