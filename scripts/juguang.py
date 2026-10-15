# 聚光「内容广场」crawler, driven through the user's logged-in Chrome via the OpenCLI browser bridge.
# Page: https://ad.xiaohongshu.com/microapp/creativity/inspire
#
#   python3 scripts/juguang.py open                     open the page in OpenCLI session (default "jz")
#   python3 scripts/juguang.py status                   {"loggedIn", "account", "signer", "url"} — loop on this while the user logs in
#   python3 scripts/juguang.py config                   filter config + industry trees → data/fetch/jg-config/
#   python3 scripts/juguang.py suggest 橘子 果干 果脯     industry paths whose names contain any word (pick from these for `plan`)
#   python3 scripts/juguang.py plan --spu PATH PATH … --ecom PATH … --kw WORD WORD … [--nd7]
#                                                       → data/fetch/jg_queries.json (one query = one Top-100 list)
#   python3 scripts/juguang.py crawl [--pages 3] [--reverse]   every query not yet on disk → data/fetch/jg/<name>.json
#
# Options for every command: --session NAME (OpenCLI browser session; a 2nd worker uses another one + --reverse).
#
# How it works: the page's own API (POST edith.xiaohongshu.com/api/pgy_leona/content_square/search_note_v2) is called
# from the page's MAIN world and signed with the page's window._webmsxyw (unsigned GETs return code -1).
# OpenCLI `eval` runs in an isolated world, so we inject a <script> and read the result back from a DOM attribute.
import json, os, re, subprocess, sys, time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))  # the workspace this copy of scripts/ lives in
FETCH = os.path.join(ROOT, 'data/fetch')
CFG = os.path.join(FETCH, 'jg-config')
URL = 'https://ad.xiaohongshu.com/microapp/creativity/inspire'
EDITH = 'https://edith.xiaohongshu.com'
argv = sys.argv[1:]

def opt(name, default=None):
    return argv[argv.index(name) + 1] if name in argv else default

def opts(name):  # `--kw a b c` and `--kw a --kw b` both work: take every value up to the next --flag
    out, on = [], False
    for a in argv:
        if a.startswith('--'): on = a == name; continue
        if on: out.append(a)
    return out

SESSION = opt('--session', 'jz')

def oc(*args, timeout=120):
    try:
        r = subprocess.run(['opencli', 'browser', SESSION, *args], capture_output=True, text=True, timeout=timeout)
    except FileNotFoundError:
        sys.exit('没有找到 opencli：先安装（见 guide/references/setup.md），再重试')
    except subprocess.TimeoutExpired:
        return json.dumps({'error': 'opencli timeout'})
    return r.stdout.split('\n\n  Update available')[0].strip() or json.dumps({'error': r.stderr.strip()[:300]})

MW = r"""(async()=>{document.documentElement.removeAttribute('data-mw');const s=document.createElement('script');
s.textContent='(async()=>{const R=x=>document.documentElement.setAttribute("data-mw",x);const tf=(u,o)=>{const c=new AbortController();setTimeout(()=>c.abort(),25000);return fetch(u,Object.assign({signal:c.signal},o))};try{'+%s+'}catch(e){R(JSON.stringify({error:String(e)}))}})()';
document.documentElement.appendChild(s);s.remove();
for(let i=0;i<200;i++){const v=document.documentElement.getAttribute('data-mw');if(v!==null)return v;await new Promise(r=>setTimeout(r,500))}return JSON.stringify({error:'timeout'})})()"""

def main_world(js, timeout=150):
    """Run `js` (an async body that ends with R(string)) in the page's main world; returns parsed JSON or {'error'}."""
    out = oc('eval', MW % json.dumps(js), timeout=timeout)
    try:
        return json.loads(out)
    except ValueError:
        return {'error': out[:300]}

def signed_get(path, tries=3):
    for k in range(tries):
        d = _signed_get(path)
        if d.get('success'): return d
        time.sleep(3)
    return d

def _signed_get(path):
    return main_world("const p=%s;const sg=window._webmsxyw(p,undefined);"
                      "const r=await tf('%s'+p,{credentials:'include',headers:{'x-s':sg['X-s'],'x-t':String(sg['X-t'])}});"
                      "R(await r.text())" % (json.dumps(path), EDITH))

# ---------- commands ----------
def cmd_open():
    print(oc('open', URL))

def cmd_status():
    js = ("const u=await tf('/api/leona/user/info',{credentials:'include'}).then(r=>r.json()).catch(e=>({}));"
          "R(JSON.stringify({url:location.href,signer:typeof window._webmsxyw==='function',"
          "loggedIn:!!(u&&u.success),account:u&&u.data&&u.data.nickName||null}))")
    d = main_world(js, timeout=60)
    d['onInspire'] = '/creativity/inspire' in (d.get('url') or '')
    d['ready'] = bool(d.get('loggedIn') and d.get('signer') and d['onInspire'])
    d['hint'] = ('就绪' if d['ready'] else
                 'OpenCLI 没连上 Chrome：确认 Chrome 开着、OpenCLI 扩展已启用，再跑 `opencli doctor`' if 'error' in d else
                 '聚光页面没打开：先跑 `juguang.py open`，等 5 秒再查' if 'ad.xiaohongshu.com' not in (d.get('url') or '') else
                 '还没登录聚光：请在打开的 Chrome 标签页里登录' if not d.get('loggedIn') else
                 '已登录，但不在内容广场页：再跑一次 `juguang.py open`' if not d['onInspire'] else
                 '页面还没加载完：等 5 秒再查')
    print(json.dumps(d, ensure_ascii=False))

def cmd_config():
    os.makedirs(CFG, exist_ok=True)
    items = signed_get('/api/pgy_leona/content_square/attribute/item/list?platform=2')
    if not items.get('success'): sys.exit(f'config failed: {items}')
    json.dump(items['data'], open(os.path.join(CFG, 'items.json'), 'w'), ensure_ascii=False, indent=1)
    for key in ('spuIndustry', 'eCommerceIndustry', 'noteContentCategory'):
        t = signed_get(f'/api/pgy_leona/content_square/attribute/item/detail?type=tree&itemKey={key}&platform=2')
        if not t.get('success'): sys.exit(f'tree {key} failed: {t}')
        json.dump(t['data'], open(os.path.join(CFG, f'tree-{key}.json'), 'w'), ensure_ascii=False)
    tabs = [(i['itemValue'], i['label']) for i in items['data']['titleTabs']['itemList']]
    print(f'saved {os.path.relpath(CFG)}: lists {tabs}')

def paths(tree):
    out = []
    def walk(n, p):
        p = p + [n['label']]
        out.append('#'.join(p))
        for c in n.get('children') or []: walk(c, p)
    for n in tree: walk(n, [])
    return out

def cmd_suggest():
    words = [a for a in argv[1:] if not a.startswith('--') and argv[argv.index(a) - 1] != '--session']
    for key, flag in (('spuIndustry', '--spu'), ('eCommerceIndustry', '--ecom'), ('noteContentCategory', '(热门类目，plan 会自动对应)')):
        P = paths(json.load(open(os.path.join(CFG, f'tree-{key}.json'))))
        hits = [p for p in P if any(w in p.split('#')[-1] for w in words)]
        parents = sorted({'#'.join(p.split('#')[:-1]) for p in hits if '#' in p} - set(hits))
        print(f'\n{key}  {flag}  ({len(hits)} 条命中' + ('，只列前 80 条，换更具体的词' if len(hits) > 80 else '') + ')')
        for p in hits[:80]: print('  ', p)
        if parents: print('  上一级（也可以选）:', ' | '.join(parents[:12]))

def sort_keys(items, biz):
    return {i['itemValue'] for i in items['sortTabs']['itemList'] if biz in i['bizType']}

def cmd_plan():
    items = json.load(open(os.path.join(CFG, 'items.json')))
    cats = set(paths(json.load(open(os.path.join(CFG, 'tree-noteContentCategory.json')))))
    spu, ecom, kws = opts('--spu'), opts('--ecom'), opts('--kw')
    Q = []
    def add(name, biz, orders, extra, nds=('30',)):
        ok = sort_keys(items, biz)
        for short, key in orders:
            if key not in ok: continue
            for nd in nds:
                Q.append({'name': f'{name}-{short}-{nd}', 'body': dict({'bizType': biz, 'nd': nd, 'orderBy': key}, **extra)})
    base = [('read', 'premium_read_num'), ('eng', 'premium_engage_num'), ('ctr', 'premium_ctr'), ('grr', 'premium_good_read_rate'), ('er', 'premium_engage_rate')]
    for k, p in enumerate(spu):
        slug = f's{k}'
        nds = ('30', '7') if k == 0 and '--nd7' in argv else ('30',)
        add(f'zc-{slug}', 2, base, {'spuIndustry': p}, nds)       # 产品种草
        add(f'zczd-{slug}', 7, base, {'spuIndustry': p}, nds)     # 种草直达
        add(f'pgy-{slug}', 4, base, {'spuIndustry': p})           # 蒲公英合作
        if '所属行业#' + p in cats:                                  # 小红书热门 uses its own category tree
            add(f'hot-{slug}', 1, base + [('like', 'premium_like_num'), ('fav', 'premium_fav_num')], {'noteContentCategory': '所属行业#' + p})
    for k, p in enumerate(ecom):                                   # 电商热门
        add(f'ec-e{k}', 6, base + [('like', 'premium_like_num'), ('fav', 'premium_fav_num'), ('gmv', 'premium_ecm_dgmv'),
                                   ('ord', 'premium_ecm_order_pv'), ('cvr', 'premium_ecm_order_rate')], {'eCommerceIndustry': p})
    for k, w in enumerate(kws):                                    # keywords: semantic search, noisy — a supplement only
        add(f'kw{k:02d}-zc', 2, base[:1], {'searchWord': w})
        add(f'kw{k:02d}-hot', 1, base[:1], {'searchWord': w})
    os.makedirs(FETCH, exist_ok=True)
    meta = {'spu': spu, 'ecom': ecom, 'kw': kws}
    json.dump(Q, open(os.path.join(FETCH, 'jg_queries.json'), 'w'), ensure_ascii=False, indent=1)
    json.dump(meta, open(os.path.join(FETCH, 'jg_plan.json'), 'w'), ensure_ascii=False, indent=1)
    print(f'{len(Q)} queries → data/fetch/jg_queries.json (≈{max(1, len(Q) * 10 // 60)} min with one worker)')

def search_all(body, pages):
    js = ("const p='/api/pgy_leona/content_square/search_note_v2';const base=%s;const out=[];"
          "for(let n=1;n<=%d;n++){const b=JSON.stringify(Object.assign({},base,{pageNum:n}));"
          "const sg=window._webmsxyw(p,JSON.parse(b));"
          "const r=await tf('%s'+p,{method:'POST',credentials:'include',"
          "headers:{'content-type':'application/json;charset=UTF-8','x-s':sg['X-s'],'x-t':String(sg['X-t'])},body:b});"
          "const d=await r.json();if(!d.success){out.push({page:n,error:d.msg});break}"
          "const L=d.data.noteList||[];out.push({page:n,total:d.data.total,notes:L});"
          "if(L.length<base.pageSize||n*base.pageSize>=(d.data.total||0))break;"
          "await new Promise(r=>setTimeout(r,800))}"
          "R(JSON.stringify(out))") % (json.dumps(body, ensure_ascii=False), pages, EDITH)
    res = main_world(js)
    return res if isinstance(res, list) else [{'page': 1, 'error': res.get('error')}]  # tab navigated away / logged out …

def cmd_crawl():
    pages = int(opt('--pages', 3))
    out_dir = os.path.join(FETCH, 'jg'); os.makedirs(out_dir, exist_ok=True)
    Q = json.load(open(os.path.join(FETCH, 'jg_queries.json')))
    fails = 0
    for q in (Q[::-1] if '--reverse' in argv else Q):
        path = os.path.join(out_dir, q['name'] + '.json')
        if os.path.exists(path): continue
        claim = path + '.claim'  # a second worker (--reverse) skips queries the first one is already on
        try: os.close(os.open(claim, os.O_CREAT | os.O_EXCL))
        except FileExistsError:
            if time.time() - os.path.getmtime(claim) < 600: continue
        base = dict({'searchWord': '', 'pageSize': 34, 'platform': 2, 'sort': 'desc'}, **q['body'])
        res = search_all(base, pages)
        got = [x for x in res if 'notes' in x]
        for x in res:
            if 'error' in x: print(f"  {q['name']} p{x['page']}: {x['error']}", flush=True)
        if not got:
            os.remove(claim); fails += 1
            if fails >= 3: sys.exit('3 queries in a row failed — run `juguang.py status` (logged out? tab moved?) then crawl again')
            continue
        fails = 0
        json.dump({'query': q, 'body': base, 'total': got[-1]['total'], 'pages': got}, open(path + '.tmp', 'w'), ensure_ascii=False)
        os.replace(path + '.tmp', path); os.remove(claim)
        print(f"{q['name']}: total {got[-1]['total']}, got {sum(len(x['notes']) for x in got)}", flush=True)
        time.sleep(1.5)
    done = sum(os.path.exists(os.path.join(out_dir, q['name'] + '.json')) for q in Q)
    print(f'done {done}/{len(Q)}' + ('' if done == len(Q) else '：还有没抓完的，再跑一次 crawl（另一个 worker 可能还在跑）'))

if __name__ == '__main__':
    cmd = argv[0] if argv else ''
    {'open': cmd_open, 'status': cmd_status, 'config': cmd_config, 'suggest': cmd_suggest, 'plan': cmd_plan, 'crawl': cmd_crawl}.get(
        cmd, lambda: sys.exit(__doc__ or open(__file__).read().split('import')[0]))()
