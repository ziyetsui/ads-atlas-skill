# Re-host the media of every note a brief shows, so videos play and image posts flip in the page after the
# signed 小红书 URLs from the crawl expire (~1–2 days). Run after the first atlas_build.py, then build again.
#
#   python3 scripts/jg_media.py <slug>               default: files go next to the page, site/<slug>/media/<note id>/,
#                                                    served by the same GitHub Pages site (video re-encoded small with ffmpeg)
#   python3 scripts/jg_media.py <slug> --host r2     upload to Cloudflare R2 instead; needs env ATLAS_R2_BUCKET,
#                                                    ATLAS_R2_PUBLIC (public base URL), CLOUDFLARE_ACCOUNT_ID, and wrangler login
# Writes site/<slug>/media.json; atlas_build.py merges it into the notes (img / images / video).
import json, os, shutil, subprocess, sys, urllib.request

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
slug = sys.argv[1]
host = sys.argv[sys.argv.index('--host') + 1] if '--host' in sys.argv else 'pages'
lib = sys.argv[sys.argv.index('--lib') + 1] if '--lib' in sys.argv else os.path.join(ROOT, 'data/library-jg')
CACHE = os.path.join(ROOT, 'data/fetch/jg-media', slug)
SITE = os.path.join(ROOT, 'site', slug)

src = open(os.path.join(SITE, 'data.js')).read()
notes = json.loads(src[src.index('=') + 1:].rstrip().rstrip(';'))['notes']
items = {i['id']: i for i in json.load(open(os.path.join(lib, 'items.json')))}
out_path = os.path.join(SITE, 'media.json')
media = json.load(open(out_path)) if os.path.exists(out_path) else {}
FFMPEG = shutil.which('ffmpeg')
if host == 'pages' and not FFMPEG:  # 720p originals (~15 MB each) would bloat the repo past GitHub limits
    sys.exit('需要 ffmpeg 来压缩视频：先安装（见 guide/references/setup.md），或用 --host r2')
if host == 'r2':
    BUCKET, PUBLIC = os.environ['ATLAS_R2_BUCKET'], os.environ['ATLAS_R2_PUBLIC'].rstrip('/')

def fetch(url, path):
    if not os.path.exists(path):
        req = urllib.request.Request(url.replace('http://', 'https://'), headers={'User-Agent': 'Mozilla/5.0'})
        with urllib.request.urlopen(req, timeout=180) as r, open(path, 'wb') as f: f.write(r.read())
    return path

def small_video(p):  # ~5–10x smaller than the 720p original; faststart so it plays before fully loaded
    out = p.replace('.mp4', '.small.mp4')
    if FFMPEG and not os.path.exists(out):
        subprocess.run([FFMPEG, '-v', 'error', '-y', '-i', p, '-vf', "scale='min(540,iw)':-2", '-c:v', 'libx264', '-preset', 'veryfast',
                        '-crf', '30', '-c:a', 'aac', '-b:a', '64k', '-movflags', '+faststart', out], check=True)
    return out if os.path.exists(out) else p

def small_image(p):
    out = p.replace('.jpg', '.small.jpg')
    if not os.path.exists(out):
        try:
            from PIL import Image
            im = Image.open(p).convert('RGB'); im.thumbnail((1080, 1440)); im.save(out, quality=80)
        except Exception:
            shutil.copyfile(p, out)
    return out

def place(path, rel, ctype):
    """Store one file; return the URL the page uses."""
    if host == 'r2':
        key = f'atlas/briefs/{slug}/{rel}'
        subprocess.run(['npx', '--yes', 'wrangler', 'r2', 'object', 'put', f'{BUCKET}/{key}', '--file', path, '--content-type', ctype, '--remote'],
                       check=True, capture_output=True)
        return f'{PUBLIC}/{key}'
    dest = os.path.join(SITE, 'media', rel); os.makedirs(os.path.dirname(dest), exist_ok=True)
    shutil.copyfile(path, dest)
    return f'media/{rel}'  # relative to site/<slug>/index.html

for nid in notes:
    if nid in media or nid not in items: continue
    x = items[nid]['extra']
    d = os.path.join(CACHE, nid); os.makedirs(d, exist_ok=True)
    m = {'images': []}
    try:
        for k, im in enumerate(x['srcImages']):
            p = small_image(fetch(im['src'], os.path.join(d, f'{k}.jpg')))
            m['images'].append({'src': place(p, f'{nid}/{k}.jpg', 'image/jpeg'), 'w': im['w'], 'h': im['h']})
        m['img'] = m['images'][0]['src'] if m['images'] else None
        if x.get('srcVideo'):
            p = small_video(fetch(x['srcVideo']['src'], os.path.join(d, 'video.mp4')))
            m['video'] = {'src': place(p, f'{nid}/video.mp4', 'video/mp4'), 'poster': m['img'], 'durationSec': x['srcVideo']['durationSec']}
            m.pop('images')  # a video note opens the player, not a gallery
    except Exception as e:  # usually: signed URL already expired → re-crawl the list this note came from
        print(f'{nid[:8]} FAILED: {e}', flush=True); continue
    media[nid] = m
    json.dump(media, open(out_path, 'w'), ensure_ascii=False, indent=1)
    print(f"{nid[:8]} {'video' if 'video' in m else str(len(m['images'])) + ' images'}", flush=True)
missing = [n for n in notes if n not in media]
print(f'{len(media)}/{len(notes)} notes hosted ({host}) → {os.path.relpath(out_path, ROOT)}' + (f'; missing {missing}' if missing else ''))
