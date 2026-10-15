# Pre-publish check of site/<slug>/ in a real browser (OpenCLI session "qa"):
#   every note opens in the page (video reaches readyState ≥ 2 / first gallery image loads), no console errors,
#   full-page screenshots light / dark / 390 px → data/qa/<slug>/. Prints a JSON summary; exit 1 if anything failed.
#   python3 scripts/verify.py <slug> [--port N]
import functools, http.server, json, os, subprocess, sys, threading, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
slug = sys.argv[1]
port = int(sys.argv[sys.argv.index('--port') + 1]) if '--port' in sys.argv else 0  # 0 = any free port
qa = os.path.join(ROOT, 'data/qa', slug); os.makedirs(qa, exist_ok=True)

class Quiet(http.server.SimpleHTTPRequestHandler):
    """Static server with HTTP Range (Chrome streams <video> with Range requests, like GitHub Pages serves them)."""
    def log_message(self, *a): pass
    def send_head(self):
        rng = self.headers.get('Range')
        path = self.translate_path(self.path)
        if not rng or not os.path.isfile(path): return super().send_head()
        size = os.path.getsize(path)
        a, _, b = rng.replace('bytes=', '').partition('-')
        start = int(a) if a else max(0, size - int(b)); end = int(b) if a and b else size - 1
        f = open(path, 'rb'); f.seek(start); self._left = end - start + 1
        self.send_response(206)
        self.send_header('Content-Type', self.guess_type(path)); self.send_header('Accept-Ranges', 'bytes')
        self.send_header('Content-Range', f'bytes {start}-{end}/{size}'); self.send_header('Content-Length', str(self._left))
        self.end_headers()
        return f
    def copyfile(self, src, dst):
        left = getattr(self, '_left', None)
        try:
            while left is None or left > 0:
                buf = src.read(65536 if left is None else min(65536, left))
                if not buf: break
                dst.write(buf)
                if left is not None: left -= len(buf)
        except (BrokenPipeError, ConnectionResetError): pass  # the browser cancels video requests it no longer needs
class Server(http.server.ThreadingHTTPServer):
    def handle_error(self, *a): pass
srv = Server(('127.0.0.1', port), functools.partial(Quiet, directory=os.path.join(ROOT, 'site')))
port = srv.server_address[1]
threading.Thread(target=srv.serve_forever, daemon=True).start()

def oc(*args, timeout=300):
    r = subprocess.run(['opencli', 'browser', 'qa', *args], capture_output=True, text=True, timeout=timeout)
    return r.stdout.split('\n\n  Update available')[0].strip()

oc('open', f'http://127.0.0.1:{port}/{slug}/index.html?t={int(time.time())}'); time.sleep(4)
viewers = oc('eval', '''(async()=>{const ids=Object.keys(window.ATLAS.notes);const out={};for(const id of ids){
  const b=document.createElement("button");b.dataset.view=id;document.body.append(b);b.click();
  let ok=false;for(let k=0;k<50&&!ok;k++){await new Promise(r=>setTimeout(r,500));const d=document.querySelector("dialog[open]");
    const v=d&&d.querySelector("video");const im=d&&d.querySelector("img");ok=v?v.readyState>=2:!!(im&&im.complete&&im.naturalWidth>0)}
  const d=document.querySelector("dialog[open]");out[id]=(d&&d.querySelector("video")?"video":"images")+(ok?"":" FAIL");d&&d.close();b.remove();await new Promise(r=>setTimeout(r,300))}
  return JSON.stringify(out)})()''')
try: viewers = json.loads(viewers)
except ValueError: viewers = {'error': viewers[:300]}
chart = oc('eval', '''(()=>{const s=[...document.querySelectorAll("svg")].find(e=>/相关性/.test(e.getAttribute("aria-label")||""));
  if(!s)return "nochart";const W=s.viewBox.baseVal.width;return [...s.querySelectorAll("circle")].filter(c=>+c.getAttribute("cx")>W).length+" outside"})()''')
shots = {}
for name, args, theme in (('light', ['--full-page'], 'light'), ('dark', ['--full-page'], 'dark'), ('390', ['--full-page', '--width', '390'], 'light')):
    oc('eval', f'(()=>{{document.querySelectorAll("dialog[open]").forEach(d=>d.close());document.documentElement.dataset.theme="{theme}";scrollTo(0,0);return 1}})()')
    time.sleep(1)
    p = os.path.join(qa, f'{name}.png'); oc('screenshot', p, *args); shots[name] = os.path.relpath(p, ROOT)
console = oc('console')
try: errors = [m for m in json.loads(console).get('messages', []) if m.get('level') == 'error']
except ValueError: errors = []
oc('close'); srv.shutdown()

failed = [k for k, v in viewers.items() if 'FAIL' in str(v)] if 'error' not in viewers else ['viewer check']
res = {'notes': len(viewers), 'videos': sum(str(v).startswith('video') for v in viewers.values()), 'failed': failed,
       'chart': chart, 'consoleErrors': len(errors), 'screenshots': shots}
print(json.dumps(res, ensure_ascii=False, indent=1))
sys.exit(1 if failed or errors or not chart.startswith('0') else 0)
