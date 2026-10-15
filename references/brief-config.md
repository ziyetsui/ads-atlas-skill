# `briefs/<slug>.py` 字段契约

引擎 `scripts/atlas_build.py <slug>` 读这个文件 + 素材库，算出其余一切，写 `site/<slug>/data.js`（不要手改）。
完整实例：`references/example-brief.py`。笔记 id 可以写全 id 或 8 位前缀（前缀撞车时引擎会报错，改写全 id）。

| 名字 | 类型 | 说明 |
|---|---|---|
| `PRODUCT` | dict | `name` `brand` `oneLine` `category` `price` `audience` `platform` `goal` `sellingPoints`(3) `copy.transferDef`；不确定的写「待确认：」 |
| `CUT` | dict | `{'relevance': 70, 'heat': 50, 'hit': 80, 'transfer': 60}`，一般不改 |
| `SOURCE` | dict | `name`：来源 + 抓取日期；`note`：一句数据边界（见 juguang-api.md） |
| `CLUSTERS` | dict id → | `match(i)→bool`、`name`（≤ 8 字，四象限上要放得下）、`kind`（直接 / 间接 / 赛道 / 渠道）、`scores`(人群, 动机, 动作)、`picked`、`why`；落选加 `drop`；`exclude`: [前面的组 id] |
| `SELECTION` | dict | `keywords`（怎么圈的，一句）、`common`(3 条，可用 `{picked_notes}` `{picked_accts}`) |
| `COMPETITORS` | dict id → | id 必须是某个 picked cluster。`name` `short` `kind` `tagline` `fmt(i)→形式id` `formats`: [(id, 名字, desc, 内容标签, [3 个例子 id])] ×3、`transfer`: {形式id: 底分}、`takeaway` |
| `TEARDOWNS` | dict 形式id → | `hero`、`account`{name, kind, inLib, note, matrix 或 None}、`traffic`{quant{from, lists:'auto', summary} 或 None, qual{verdict, reason, keywords[{w, where[], role, note}], longtail[3]}}、`money`{steps[{k, d}], path, price}、`structure`[{t, d}]、`why`[3]、`inferred`[structure 的 t] |
| `LAWS` | list ×3 | `id` `name` `claim`(含 `{withHit}` `{withoutHit}`) `evidence`{rx} `examples`[3] `mock`{cover, pal 0–2, person, type} `apply`{title, cover, script, kpi} |

`i`（素材库一条笔记）可用的字段：`i['title']`、`i['subtitle']`（账号名）、`i['facets']['fmt']`（视频 / 图文）、`i['extra']`（reads likes collects comments fans published ad pgy）、`i['id']`。
常用写法：`T = lambda i: i['title']`，`TS = lambda i: i['title'] + ' ' + i['subtitle']`。
