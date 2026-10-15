# Quick numbers while writing briefs/<slug>.py — never edit data.js by hand, iterate on the config with these.
#   python3 scripts/probe.py lib                          library overview: lists, notes, top terms in list names
#   python3 scripts/probe.py group "regex" [--title] [--top 40]   size / heat of a candidate cluster, its top notes
#                                                         (--title: match title only; account names are full of 橘子/果干…)
#   python3 scripts/probe.py laws <slug> 'name=regex' ...  with/without hit rate over the picked competitors' notes
#   python3 scripts/probe.py note <id-or-prefix> ...        list ranks, numbers, account and its other notes
import importlib.util, json, os, re, statistics as st, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
a = sys.argv[1:]
opt = lambda k, d=None: a[a.index(k) + 1] if k in a else d
lib = opt('--lib', os.path.join(ROOT, 'data/library-jg'))
items = json.load(open(os.path.join(lib, 'items.json')))
det = json.load(open(os.path.join(lib, 'det.json')))
pct = lambda i: float(i['metrics'][0]['value'].rstrip('%'))
rows = lambda i: det[i['id']]['detail']['sections'][0]['rows']

def heat(L):
    ps = [pct(i) for i in L]; med = st.median(ps); top = sum(p >= 80 for p in ps) / len(L) * 100
    return round(.5 * med + .3 * top + .2 * min(len(L) / 40, 1) * 100), med, top

def line(i):
    x = i['extra']
    return f"  {i['id'][:8]} {pct(i):5.1f} ♥{x.get('likes')} 阅{x.get('reads')} {i['facets']['fmt'][0]}{'·推广' if x.get('ad') else ''} {i['title'][:40].replace(chr(10), ' ')} | {i['subtitle'][:14]}"

cmd = a[0] if a else ''
if cmd == 'lib':
    names = {r[0] for i in items for r in rows(i)}
    print(f'{len(items)} notes, {len(names)} lists')
    for n in sorted(names): print('  ', n)
elif cmd == 'group':
    rx = a[1]; field = (lambda i: i['title']) if '--title' in a else (lambda i: i['title'] + ' ' + i['subtitle'])
    L = [i for i in items if re.search(rx, field(i))]
    if not L: sys.exit('0 notes')
    h, med, top = heat(L)
    print(f"n={len(L)} accounts={len(set(i['subtitle'] for i in L))} medianPct={med:.1f} hit%={top:.1f} heat={h} video={sum(i['facets']['fmt'] == '视频' for i in L)}")
    for i in sorted(L, key=lambda i: -pct(i))[:int(opt('--top', 40))]: print(line(i))
elif cmd == 'laws':
    spec = importlib.util.spec_from_file_location('brief', os.path.join(ROOT, 'briefs', f'{a[1]}.py'))
    B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)
    members = {k: [i for i in items if c['match'](i)] for k, c in B.CLUSTERS.items()}
    for k, c in B.CLUSTERS.items():
        for o in c.get('exclude', []):
            t = {i['id'] for i in members[o]}; members[k] = [i for i in members[k] if i['id'] not in t]
    N = [i for k in B.COMPETITORS for i in members[k]]
    hr = lambda L: round(sum(pct(i) >= 80 for i in L) / len(L) * 100) if L else 0
    print(f'{len(N)} notes in picked competitors')
    for kv in a[2:]:
        name, rx = kv.split('=', 1)
        w = [i for i in N if re.search(rx, i['title'])]; wo = [i for i in N if not re.search(rx, i['title'])]
        print(f'  {name:10} with {len(w):4} hit {hr(w):3}%   without {len(wo):4} hit {hr(wo):3}%   gap {hr(w) - hr(wo):+d}')
elif cmd == 'note':
    for p in a[1:]:
        i = next(i for i in items if i['id'].startswith(p)); x = i['extra']
        print(line(i)); print(f"   fans {x.get('fans')} · published {x.get('published')} · 推广 {x.get('ad')} · 蒲公英 {x.get('pgy')} · "
                              f"{len(x.get('srcImages') or [])} images · video {bool(x.get('srcVideo'))}")
        for r in rows(i): print(f'   {r[0]}  第 {r[1]}/{r[2]}')
        print('   same account:', [(o['id'][:8], o['title'][:20]) for o in items if o['subtitle'] == i['subtitle'] and o is not i])
else:
    print(open(__file__).read().split('import')[0])
