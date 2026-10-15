# Atlas brief engine: turns a brand config (briefs/<slug>.py) + the library (data/library-jg) into site/<slug>/data.js.
# Usage: python3 scripts/atlas_build.py <slug> [--lib data/library-jg] [--out site/<slug>/data.js]
# Draft mode: a config with only PRODUCT / CUT / CLUSTERS prints the candidate pool and stops (no data.js) —
# use it to iterate on clusters before writing COMPETITORS / TEARDOWNS / LAWS.
#
# The config holds the judgment (clusters, scores, format rules, examples, teardowns, laws);
# this engine computes everything that can be counted (pool stats, heat, formats, scatter, evidence, zones).
import argparse, datetime, hashlib, importlib.util, json, os, re, statistics as st, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
ap = argparse.ArgumentParser()
ap.add_argument('slug')
ap.add_argument('--lib', default=os.path.join(ROOT, 'data/library-jg') if os.path.isdir(os.path.join(ROOT, 'data/library-jg')) else os.path.join(ROOT, 'data/library'))
ap.add_argument('--out')
args = ap.parse_args()
out = args.out or os.path.join(ROOT, 'site', args.slug, 'data.js')

spec = importlib.util.spec_from_file_location('brief', os.path.join(ROOT, 'briefs', f'{args.slug}.py'))
B = importlib.util.module_from_spec(spec); spec.loader.exec_module(B)

items = json.load(open(f'{args.lib}/items.json'))
det = json.load(open(f'{args.lib}/det.json'))
class ById(dict):  # notes are referenced by full id or by an 8-char prefix; a prefix shared by two notes must be spelled out
    def __missing__(self, k):
        hits = [i for i in items if i['id'].startswith(k)]
        if len(hits) == 1: return hits[0]
        sys.exit(f'note id {k!r}: ' + ('not in the library' if not hits else f'ambiguous, use one of {[i["id"] for i in hits]}'))
byId = ById({i['id']: i for i in items})
HIT = B.CUT.get('hit', 80)
TRANSFER = B.CUT.get('transfer', 60)

# ---------- helpers ----------
def pct(i): return float(i['metrics'][0]['value'].rstrip('%') or 0)

def lists(i):
    for s in det[i['id']]['detail']['sections']:
        if s['kind'] == 'table':
            return [{'list': r[0], 'rank': int(r[1]), 'total': int(r[2]), 'metric': r[5], 'window': int(r[6])} for r in s['rows']]
    return []

def date(i):  # real publish date when the library has it (聚光 pulls); else 小红书 note ids start with a hex unix timestamp
    return i.get('date') or datetime.datetime.fromtimestamp(int(i['id'][:8], 16)).strftime('%Y-%m-%d')

def clean(t):  # first line, without #话题# tags
    t = re.sub(r'#[^#]*?\[话题\]#', '', t.split('\n')[0]).strip(' ：:')
    return t or '（无标题）'

def objective(name):
    for k, v in [('应用推广·应用下载', '应用下载'), ('蒲公英合作', '蒲公英合作'), ('客资收集', '客资收集'), ('产品种草', '产品种草'), ('小红书热门', '自然热门')]:
        if name.startswith(k): return v
    return name.split('·')[0]

def jitter(s, span):
    return (int(hashlib.md5(s.encode()).hexdigest()[:6], 16) % (2 * span + 1)) - span

def best_list(i):
    L = lists(i)
    return min(L, key=lambda r: r['rank'] / r['total']) if L else None

# Re-hosted media for this brief (scripts/jg_media.py): img / images / video per note
BRIEF_MEDIA_PATH = os.path.join(ROOT, 'site', args.slug, 'media.json')
MEDIA = json.load(open(BRIEF_MEDIA_PATH)) if os.path.exists(BRIEF_MEDIA_PATH) else {}

def note(i, c, f):
    b = best_list(i)
    extra = {k: v for k, v in i.get('extra', {}).items() if not k.startswith('src')}  # real numbers from 聚光 pulls
    return {**_note(i, c, f, b), **extra, **MEDIA.get(i['id'], {})}

def _note(i, c, f, b):
    return {'id': i['id'], 'title': clean(i['title'])[:60], 'tags': re.findall(r'#([^#]*?)\[话题\]#', i['title']), 'img': i['cover'], 'aspect': i['coverAspect'], 'account': i['subtitle'],
            'type': i['facets']['fmt'], 'pct': pct(i), 'featured': i['facets']['tier'] == 'featured', 'url': i['url'],
            'list': b['list'] if b else '', 'rank': b['rank'] if b else None, 'total': b['total'] if b else None,
            'objective': objective(b['list']) if b else '', 'date': date(i), 'video': i.get('video'), 'competitor': c, 'format': f}

# ---------- pool ----------
members = {k: [i for i in items if c['match'](i)] for k, c in B.CLUSTERS.items()}
for k, c in B.CLUSTERS.items():  # a note belongs to one cluster: drop those claimed by the listed clusters
    for other in c.get('exclude', []):
        taken = {i['id'] for i in members[other]}
        members[k] = [i for i in members[k] if i['id'] not in taken]

def fail(msg): sys.exit(f'briefs/{args.slug}.py: {msg}')
for k, L in members.items():
    if not L: fail(f'cluster {k!r} matches 0 notes (after exclude) — loosen its match, or drop the cluster')
COMPETITORS = getattr(B, 'COMPETITORS', {})
picked = [k for k, c in B.CLUSTERS.items() if c['picked']]
if not COMPETITORS:  # draft mode
    print('draft: pool only (add COMPETITORS / TEARDOWNS / LAWS / SELECTION to build the page)')
    for k, L in sorted(members.items(), key=lambda kv: -len(kv[1])):
        c = B.CLUSTERS[k]; ps = [pct(i) for i in L]; u, m, a = c['scores']
        rel = round(0.3 * u + 0.4 * m + 0.3 * a); heat = round(0.5 * st.median(ps) + 0.3 * sum(p >= HIT for p in ps) / len(ps) * 100 + 0.2 * min(len(L) / 40, 1) * 100)
        core = rel >= B.CUT['relevance'] and heat >= B.CUT['heat']
        print(f"  {'✓' if c['picked'] else ' '}{'◆' if core else ' '} {c['name']:<20} rel {rel:>3} heat {heat:>3} notes {len(L):>4}")
    sys.exit(0)
if set(COMPETITORS) != set(picked):
    fail(f'COMPETITORS {sorted(COMPETITORS)} must be exactly the picked clusters {sorted(picked)}')
for cid, C in COMPETITORS.items():
    ids = [f[0] for f in C['formats']]
    if set(C['transfer']) != set(ids): fail(f'{cid}: transfer keys {sorted(C["transfer"])} ≠ format ids {ids}')
    got = {}
    for i in members[cid]:
        f = C['fmt'](i)
        if f not in ids: fail(f'{cid}: fmt() returned {f!r} for {i["id"][:8]}, not one of {ids}')
        got[f] = got.get(f, 0) + 1
    for f in ids:
        if not got.get(f): fail(f'{cid}: format {f} has 0 notes — change fmt() order/regex or merge formats')
    for f in C['formats']:
        for e in f[4]:
            i = byId[e]
            if i not in members[cid] or C['fmt'](i) != f[0]:
                print(f'warning: example {e} is listed under {cid}/{f[0]} but fmt() puts it in {C["fmt"](i) if i in members[cid] else "another cluster"}')

pool = []
for k, L in members.items():
    c = B.CLUSTERS[k]
    ps = [pct(i) for i in L]
    med = st.median(ps); top = sum(p >= HIT for p in ps) / len(ps) * 100; vol = min(len(L) / 40, 1) * 100
    u, m, a = c['scores']
    pool.append({'id': k, 'name': c['name'], 'kind': c['kind'], 'relevance': round(0.3 * u + 0.4 * m + 0.3 * a), 'heat': round(0.5 * med + 0.3 * top + 0.2 * vol),
                 'notes': len(L), 'accounts': len(set(i['subtitle'] for i in L)), 'medianPct': round(med, 1), 'hitShare': round(top, 1),
                 'user': u, 'motive': m, 'action': a, 'picked': c['picked'], 'why': c['why']})

# ---------- competitors, formats, scatter ----------
competitors, scatter, notes = [], {}, {}
for cid, C in COMPETITORS.items():
    L = members[cid]; ps = [pct(i) for i in L]
    fmt = C['fmt']
    formats = []
    for fid, name, desc, content, ex in C['formats']:
        fm = [i for i in L if fmt(i) == fid]
        fp = [pct(i) for i in fm]; hits = sum(p >= HIT for p in fp)
        exn = [note(byId[s], cid, fid) for s in ex]
        for n in exn: notes[n['id']] = n
        vid = sum(i['facets']['fmt'] == '视频' for i in fm)
        formats.append({'id': fid, 'name': name, 'desc': desc, 'axis': {'content': content}, 'n': len(fm), 'share': round(len(fm) / len(L) * 100),
                        'hits': hits, 'hitRate': round(hits / len(fm) * 100, 1), 'avgPct': round(st.mean(fp), 1),
                        'type': '视频' if vid >= len(fm) / 2 else '图文', 'notes': exn})
    objs = {}
    for i in L:
        b = best_list(i)
        if b: o = objective(b['list']); objs[o] = objs.get(o, 0) + 1
    competitors.append({'id': cid, 'name': C['name'], 'short': C.get('short', C['name']), 'kind': C['kind'], 'tagline': C['tagline'],
                        'stats': {'notes': len(L), 'accounts': len(set(i['subtitle'] for i in L)), 'hits': sum(p >= HIT for p in ps),
                                  'hitRate': round(sum(p >= HIT for p in ps) / len(L) * 100, 1), 'medianPct': round(st.median(ps), 1)},
                        'objectives': sorted(objs.items(), key=lambda x: -x[1]), 'formats': formats})
    ex_ids = {n['id'] for f in formats for n in f['notes']}
    scatter[cid] = [{'id': i['id'], 'format': fmt(i), 'pct': pct(i),
                     'transfer': max(5, min(98, C['transfer'][fmt(i)] + jitter(i['id'], 12))), 'hit': pct(i) >= HIT,
                     'title': clean(i['title'])[:40], 'account': i['subtitle'], 'date': date(i), 'example': i['id'] in ex_ids} for i in L]

# ---------- teardowns ----------
teardowns = {}
for fid, td in getattr(B, 'TEARDOWNS', {}).items():
    td = json.loads(json.dumps(td, ensure_ascii=False))
    hero = byId[td['hero']]
    td['hero'] = hero['id']
    q = td['traffic'].get('quant')
    if q is not None and q.get('lists') == 'auto':
        q['lists'] = [dict(r, objective=objective(r['list'])) for r in lists(hero)]
    teardowns[fid] = td
for c in competitors:
    for f in c['formats']:
        teardowns.setdefault(f['id'], {'hero': f['notes'][0]['id'], 'inherit': True})

# ---------- laws ----------
allN = [i for cid in COMPETITORS for i in members[cid]]
def ev(rx):
    w = [i for i in allN if re.search(rx, i['title'])]; wo = [i for i in allN if not re.search(rx, i['title'])]
    if not w or not wo: fail(f'law regex {rx!r} matches {len(w)} of {len(allN)} competitor notes — needs some with and some without')
    return {'with': len(w), 'withHit': round(sum(pct(i) >= HIT for i in w) / len(w) * 100),
            'without': len(wo), 'withoutHit': round(sum(pct(i) >= HIT for i in wo) / len(wo) * 100), 'of': len(allN)}
def campaign(cid):
    L = members[cid]
    return {'name': COMPETITORS[cid]['name'], 'notes': len(L), 'accounts': len(set(i['subtitle'] for i in L))}
def fmt_of_note(i):
    cid = next((k for k in COMPETITORS if i in members[k]), None)
    if cid is None: fail(f'law example {i["id"][:8]} is not in any picked competitor — pick examples from COMPETITORS clusters')
    return cid, COMPETITORS[cid]['fmt'](i)

laws = []
for L in getattr(B, 'LAWS', []):
    l = json.loads(json.dumps({k: v for k, v in L.items() if k != 'evidence'}, ensure_ascii=False))
    e = L['evidence']
    l['evidence'] = ev(e['rx']) if 'rx' in e else {'campaigns': [campaign(c) for c in e['campaigns']]}
    if 'with' in l['evidence']: l['claim'] = l['claim'].format(**l['evidence'])
    l['examples'] = [byId[s]['id'] for s in L['examples']]
    for s in L['examples']:
        i = byId[s]
        if i['id'] not in notes:
            cid, f = fmt_of_note(i)
            notes[i['id']] = note(i, cid, f)
    laws.append(l)

# ---------- product + structured summaries ----------
product = dict(B.PRODUCT)
SRC = getattr(B, 'SOURCE', {})  # a brief built from another library (e.g. 聚光内容广场, specs/0004) describes it here
product['pool'] = {'source': SRC.get('name', 'Atlas 素材库 · 小红书聚光 / 蒲公英 / 热门榜单'),
                   'window': f"{min(date(i) for L in members.values() for i in L)} → {max(date(i) for L in members.values() for i in L)}",
                   'brands': len(pool), 'notes': sum(p['notes'] for p in pool), 'library': len(items)}
product['dataNote'] = SRC.get('note', '数据来自榜单记录：有榜内百分位和排名，没有点赞数和粉丝数；发布日期由笔记 ID 推算')
product['cut'] = {'relevance': B.CUT['relevance'], 'heat': B.CUT['heat'], 'hit': HIT, 'transfer': TRANSFER}
dropped = {}
for p in pool:
    if not p['picked']: dropped.setdefault(B.CLUSTERS[p['id']]['drop'], []).append(p['name'])
fill = {'picked_notes': len(allN), 'picked_accts': len(set(i['subtitle'] for i in allN))}
S = B.SELECTION
product['selection'] = {
    'pool': f"素材库 {len(items):,} 条 → 按「{S['keywords']}」等关键词圈出 {len(pool)} 组候选、{sum(p['notes'] for p in pool)} 条笔记",
    'rule': f"两道线同时过：相关性 ≥ {B.CUT['relevance']}（和{product['name']}的人群 · 动机 · 动作重合，判断分）× 爆品度 ≥ {B.CUT['heat']}（榜单百分位、爆款占比、素材量算出）",
    'picked': [p['name'] for p in sorted(pool, key=lambda p: -(p['relevance'] + p['heat'])) if p['picked']],
    'dropped': [{'tag': k, 'names': v} for k, v in dropped.items()],
    'common': [t.format(**fill) for t in S['common']],
}
for c in competitors:
    Sx = scatter[c['id']]; z = [x for x in Sx if x['pct'] >= HIT and x['transfer'] >= TRANSFER]
    names = {f['id']: f['name'] for f in c['formats']}
    by = {}
    for x in z: by[x['format']] = by.get(x['format'], 0) + 1
    c['zone'] = {'n': len(z), 'total': len(Sx), 'hits': sum(x['hit'] for x in Sx),
                 'byFormat': [[names[k], v] for k, v in sorted(by.items(), key=lambda kv: -kv[1])], 'takeaway': COMPETITORS[c['id']]['takeaway']}

palettes = [['#f4d9c6', '#e9a98b', '#3b1f14'], ['#1f2a44', '#4b5d8a', '#fff'], ['#e8434a', '#b8202b', '#fff']]
data = {'palettes': palettes, 'product': product, 'pool': pool, 'competitors': competitors, 'teardowns': teardowns, 'laws': laws, 'scatter': scatter, 'notes': notes}
os.makedirs(os.path.dirname(out), exist_ok=True)
open(out, 'w').write(f"// Atlas — {product['name']} brief data. Generated by scripts/atlas_build.py from briefs/{args.slug}.py; do not edit by hand.\n"
                     'window.ATLAS = ' + json.dumps(data, ensure_ascii=False, indent=1) + ';\n')

# ---------- console report ----------
print(f'wrote {os.path.relpath(out, ROOT)}')
for p in sorted(pool, key=lambda p: -p['relevance']):
    core = p['relevance'] >= B.CUT['relevance'] and p['heat'] >= B.CUT['heat']
    print(f"  {'✓' if p['picked'] else ' '}{'◆' if core else ' '} {p['name']:<24} rel {p['relevance']:>3} heat {p['heat']:>3} notes {p['notes']:>3}")
for c in competitors:
    print(f"  {c['name']}: {c['stats']} zone {c['zone']['n']}")
    for f in c['formats']: print(f"     {f['id']} {f['name']:<20} n {f['n']:>3} hit {f['hitRate']:>5}% avg {f['avgPct']}")
for l in laws: print(f"  {l['id']} {l['claim']}")

# ---------- home page list (site/briefs.js) ----------
bj = os.path.join(ROOT, 'site', 'briefs.js')
try:
    txt = open(bj).read() if os.path.exists(bj) else 'window.BRIEFS = [];'
    lst = json.loads(txt[txt.index('['):txt.rindex(']') + 1])
    entry = {'slug': args.slug, 'name': product['name'], 'brand': product.get('brand', ''), 'oneLine': product.get('oneLine', '')}
    lst = [e for e in lst if e.get('slug') != args.slug] + [entry]
    open(bj, 'w').write('// Briefs listed on the home page; maintained by scripts/atlas_build.py.\nwindow.BRIEFS = ' + json.dumps(lst, ensure_ascii=False, indent=1) + ';\n')
except ValueError:
    print(f'note: {os.path.relpath(bj, ROOT)} is not plain JSON, add {args.slug} to it by hand')
