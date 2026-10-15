# Turn 聚光 内容广场 pulls (data/fetch/jg/*.json, from scripts/juguang.py crawl) into the library
# data/library-jg/ (items.json + det.json) that atlas_build.py / probe.py / sheet.py read.
# Usage: python3 scripts/jg_library.py [--out data/library-jg]
#
# Every pull is one ranked list (Top 100 of a 榜单 × 行业/关键词 × 指标 × 窗口). A note's rank in each list it
# appears in becomes a 榜单记录 row; its 榜内百分位 is the best one. Unlike the old library, these notes also carry
# real numbers (阅读 / 点赞 / 收藏 / 评论 / 粉丝) and the publish time; they go in `extra` and the engine passes them on.
import datetime, glob, json, os, sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
OUT = sys.argv[sys.argv.index('--out') + 1] if '--out' in sys.argv else os.path.join(ROOT, 'data/library-jg')

BIZ = {1: '小红书热门', 2: '产品种草', 4: '蒲公英合作', 5: '客资收集', 6: '电商热门', 7: '种草直达', 8: '应用推广'}
METRIC = {'premium_read_num': '阅读量', 'premium_engage_num': '互动量', 'premium_ctr': '阅读率', 'premium_good_read_rate': '阅读率',
          'premium_engage_rate': '互动率', 'premium_like_num': '点赞量', 'premium_fav_num': '收藏量', 'premium_imp_num': '曝光量',
          'premium_ecm_dgmv': '笔记支付金额', 'premium_ecm_order_pv': '笔记支付订单数', 'premium_ecm_order_rate': '笔记支付转化率'}

def scope(body):
    if body.get('searchWord'): return f"搜「{body['searchWord']}」"
    for k in ('spuIndustry', 'eCommerceIndustry', 'noteContentCategory'):
        if body.get(k): return body[k].split('#')[-1]
    return '全行业'

def pct(rank, total):  # same scale as the old library: rank 2/100 → 99.0, rank 7/100 → 93.9
    return round((total - rank) / (total - 1) * 100, 1) if total > 1 else 100.0

items, rows = {}, {}
for path in sorted(glob.glob(os.path.join(ROOT, 'data/fetch/jg/*.json'))):
    d = json.load(open(path))
    b = d['body']
    L = [n for p in d['pages'] for n in p['notes']]
    name = f"{BIZ.get(b['bizType'], b['bizType'])}·{scope(b)}·{METRIC.get(b['orderBy'], b['orderBy'])}·近{b['nd']}日"
    for r, n in enumerate(L, 1):
        i, u = n['noteInfo'], n['userInfo']
        nid = i['noteId']
        rows.setdefault(nid, {})[name] = [name, str(r), str(len(L)), b['orderBy'], d['query']['name'], METRIC.get(b['orderBy'], b['orderBy']), b['nd'], '采用']
        if nid in items: continue
        im = i['noteImages'] or [{}]
        items[nid] = {
            'id': nid, 'title': i['title'], 'cover': im[0].get('imageUrl'),
            'coverAspect': round(im[0]['imageWidth'] / im[0]['imageHeight'], 3) if im[0].get('imageHeight') else 0.75,
            'tags': [], 'facets': {'fmt': '视频' if i['noteType'] == 2 else '图文', 'ind': scope(b), 'yfam': '', 'tier': 'pool'},
            'date': i['notePublishTime'][:10], 'url': i['noteLink'], 'video': None, 'subtitle': u['nickName'],
            'extra': {'reads': i.get('readNum'), 'likes': i.get('likeNum'), 'collects': i.get('favNum'), 'comments': i.get('cmtNum'),
                      'fans': u.get('fansNum'), 'userId': u.get('userId'), 'published': i['notePublishTime'],
                      'ad': i.get('isAdNote') == 1, 'pgy': i.get('bindType') == 1,
                      'srcImages': [{'src': x['imageUrl'], 'w': x['imageWidth'], 'h': x['imageHeight']} for x in i['noteImages']],
                      'srcVideo': {'src': i['videoUrl'], 'durationSec': i.get('videoDuration')} if i.get('videoUrl') else None},
        }

det = {}
for nid, it in items.items():
    R = sorted(rows[nid].values(), key=lambda r: int(r[1]) / int(r[2]))
    best = R[0]
    p = pct(int(best[1]), int(best[2]))
    it['metrics'] = [{'label': '榜内百分位', 'value': f'{p}%'}, {'label': f'{best[5]}·最好名次', 'value': f'{best[1]}/{best[2]}'}, {'label': '入榜次数', 'value': str(len(R))}]
    det[nid] = dict(it, detail={'title': it['title'], 'sections': [
        {'kind': 'table', 'title': '全部榜单记录', 'columns': ['榜单', '排名', '总数', '排序字段', '抓取', '指标', '窗口（天）', '使用状态'], 'rows': R},
        {'kind': 'links', 'title': '来源', 'links': [{'label': '查看原文', 'url': it['url']}]}]})

os.makedirs(OUT, exist_ok=True)
json.dump(list(items.values()), open(os.path.join(OUT, 'items.json'), 'w'), ensure_ascii=False)
json.dump(det, open(os.path.join(OUT, 'det.json'), 'w'), ensure_ascii=False)
print(f'{len(items)} notes from {len(glob.glob(os.path.join(ROOT, "data/fetch/jg/*.json")))} lists → {os.path.relpath(OUT, ROOT)} '
      f'({datetime.date.today()})')
