# Look at a note before writing its teardown: downloads its images / video from the crawl (signed URLs, same day only)
# and writes one contact image per note → data/qa/frames/<id>.jpg (video: one frame every 4 s, 5 × 2 grid;
# image post: all images side by side). Read the output with the Read tool.
#   python3 scripts/frames.py <id-or-prefix> [<id> …]
import io, json, os, shutil, subprocess, sys, urllib.request
from PIL import Image

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
items = json.load(open(os.path.join(ROOT, 'data/library-jg/items.json')))
out = os.path.join(ROOT, 'data/qa/frames'); os.makedirs(out, exist_ok=True)
get = lambda u: urllib.request.urlopen(urllib.request.Request(u.replace('http://', 'https://'), headers={'User-Agent': 'Mozilla/5.0'}), timeout=180).read()

for p in sys.argv[1:]:
    i = next((i for i in items if i['id'].startswith(p)), None)
    if not i: print(f'{p}: not in library'); continue
    x, dst = i['extra'], os.path.join(out, f"{i['id']}.jpg")
    try:
        if x.get('srcVideo') and shutil.which('ffmpeg'):
            v = os.path.join(out, f"{i['id']}.mp4")
            open(v, 'wb').write(get(x['srcVideo']['src']))
            subprocess.run(['ffmpeg', '-v', 'error', '-y', '-i', v, '-vf', 'fps=1/4,scale=240:-1,tile=5x2', '-frames:v', '1', dst], check=True)
            os.remove(v)
        else:
            ims = [Image.open(io.BytesIO(get(im['src']))).convert('RGB') for im in x['srcImages'][:8]]
            for im in ims: im.thumbnail((360, 480))
            sheet = Image.new('RGB', (sum(im.width for im in ims), max(im.height for im in ims)), 'white'); xo = 0
            for im in ims: sheet.paste(im, (xo, 0)); xo += im.width
            sheet.save(dst, quality=82)
        print(f"{i['id'][:8]} {'video' if x.get('srcVideo') else 'images'} → {os.path.relpath(dst, ROOT)}  {i['title'][:30]}")
    except Exception as e:
        print(f"{i['id'][:8]} failed ({e}) — signed URLs expire in 1–2 days; re-crawl if needed")
