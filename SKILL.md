---
name: ads-atlas-skill
description: Use when the user names their product and wants a 小红书 competitor / 爆款 brief from 聚光 (ad.xiaohongshu.com 内容广场 / 创意灵感 / 榜单), e.g. "我的产品是 XX", "帮我做竞品爆款 brief", "找对标 / 找爆款 / 竞品分析 + 小红书", or wants such a brief published to their own GitHub Pages; also when updating or re-crawling an existing Atlas brief.
---

# Ads Atlas：产品名 → 竞品爆款 Brief → GitHub Pages

用户只给一个产品名（最好附产品图 / 链接）。你接管他已登录的 Chrome，从聚光「内容广场」榜单抓真实笔记，
圈竞品、拆爆款、提规律，生成一页 brief（我的产品 → 锁定竞品 → 竞品爆款 → 爆款拆解 → 规律与落地），
所有视频和图文都能在页面里看，最后发布到**用户自己仓库**的 GitHub Pages。

- `$SKILL` = 本文件所在目录；`$WS` = 工作区（要发布的那个仓库，默认 `~/atlas-briefs`）。
- **所有命令都写绝对路径** `python3 $WS/scripts/…`（shell 的当前目录会被重置，脚本自己按所在位置找工作区）。
- 工作区里的 `$WS/guide/` 是本 skill 的 `agents/` 和 `references/` 副本，子 agent 在工作区里也能读。

## 固定流程（按顺序，带 🛑 的必须停下来等用户）

**0. 收集。** 产品名；有图就读图上的字（品牌、规格、产地、卖点）。其余不问，后面写「待确认」。
先告诉用户：需要**一个能登录的聚光账号**（内容广场只对聚光广告主开放），整个过程约 1–2 小时，中间会停 3 次。没有聚光账号就停在这里。
定 `slug`（英文小写，如 `juzi`）。`~/atlas-briefs/site/briefs.js` 存在 = 用户以前做过，沿用这个工作区。

**1. 环境。** `opencli doctor`（Extension connected）、`python3 -c "import PIL"`、`ffmpeg -version`。缺的照 `$SKILL/references/setup.md` 一次列给用户，让他用 `! <命令>` 装，装好再继续。
然后 `python3 $SKILL/scripts/init_workspace.py $WS`（已有工作区会只升级脚本和模板）。

**2. 🛑 登录聚光。** `python3 $WS/scripts/juguang.py open`，告诉用户：
「我在 Chrome 里打开了聚光内容广场，请在那个标签页登录（扫码或账号），看到『探索小红书热门商业内容』后回复我。」
用户回复后跑 `python3 $WS/scripts/juguang.py status`：`ready: true` 才继续；否则按它的 `hint` 处理（不在内容广场页就再跑一次 `open`，等 5 秒再 `status`），把 hint 用中文转告用户。

**3. 🛑 定搜索范围。** `python3 $WS/scripts/juguang.py config`，再 `python3 $WS/scripts/juguang.py suggest <词…>`（产品名拆出来的词 + 上位品类 + 原料 + 形态，如 乌龙 茶包 袋泡茶 冷泡；命中太多就换更具体的词）。
挑 2–4 条 `spuIndustry`（最贴近的放第一个，再加它的上一级）、1–2 条 `eCommerceIndustry`、15–20 个关键词（品类、原料、使用场景、人群），用一段中文列给用户确认或增删。

**4. 抓取。** `python3 $WS/scripts/juguang.py plan --spu 路径1 路径2 --ecom 路径 --kw 词1 词2 词3 … --nd7`（它会打印查询数和预计时间，转告用户）。
后台跑 `python3 $WS/scripts/juguang.py crawl --pages 3`。要快就再开一个：`opencli browser jz2 open https://ad.xiaohongshu.com/microapp/creativity/inspire`，等 5 秒，后台跑 `python3 $WS/scripts/juguang.py crawl --pages 3 --session jz2 --reverse`。
**两个都结束**、最后一行是 `done N/N` 之后，`python3 $WS/scripts/jg_library.py`。不是 N/N 就再跑一次 crawl（只补缺的）。
媒体签名 1–2 天过期：**第 4 到第 6 步要在同一天做完**。

**5. 分析。** 按 `$WS/guide/agents/analyst.md` 写 `$WS/briefs/<slug>.py`：先只写 PRODUCT / CUT / SOURCE / CLUSTERS，`python3 $WS/scripts/atlas_build.py <slug>` 是草稿模式（只打印候选池），圈好竞品再补其余部分，直到完整构建通过、数字和结论一致。
封面用 `sheet.py` 看，主例用 `frames.py` 看，**看过再写**。入选竞品定了以后，用 3 行告诉用户入选了谁、为什么（不用等回复）。

**6. 媒体 + 检查。** `python3 $WS/scripts/jg_media.py <slug>` → `python3 $WS/scripts/atlas_build.py <slug>` → `python3 $WS/scripts/sync_template.py` → 按 `$WS/guide/agents/qa.md` 全部通过（含 `python3 $WS/scripts/verify.py <slug>`）。

**7. 🛑 发布。** 先 `gh auth status`（没登录：让用户跑 `! gh auth login -h github.com -p https --web`）。问用户：仓库名（默认 `atlas-briefs`；以前发过就用原来的）、公开还是私有（私有仓库的 Pages 要付费账号）。确认后：
`cd $WS && bash scripts/publish.sh <仓库名> [--private] "Add <产品名> brief"`，把打印的网址给用户（首页列出所有 brief，`<网址>/<slug>/` 是这一份）。

## 速查

| 要做的事 | 命令（都在 `$WS/scripts/` 下） |
|---|---|
| 登录是否就绪 | `juguang.py status` |
| 抓了哪些榜单 | `probe.py lib` |
| 试一个候选组 | `probe.py group "<regex>" --title` |
| 看封面 | `sheet.py --match "<regex>" --top 60` 或 `sheet.py --ids a,b,c`，再 Read 输出图 |
| 看一条笔记的视频 / 图集 | `frames.py <id前缀> …`，再 Read `data/qa/frames/<id>.jpg` |
| 一条笔记的名次、数字、同账号 | `probe.py note <id前缀>` |
| 试规律特征 | `probe.py laws <slug> 'name=regex' …` |
| 更新已有 brief | 删 `data/fetch/jg/` → 第 3–7 步（config 可沿用） |

接口字段、报错对照、数据边界：`references/juguang-api.md`。config 字段：`references/brief-config.md`。完整实例：`references/example-brief.py`。

## 常见错误

- **`--kw` 只写了一个词**：`plan` 的每个 flag 后面可以跟多个值，确认它打印的查询数里关键词都在。
- **跳过登录确认直接 crawl**：未登录时接口全失败，crawl 连续 3 次失败会自己退出。先 `status`。
- **按账号名匹配品类词**：账号叫「橘子汽水」「苹果干」的笔记和品类无关。圈组只匹配标题。
- **只看标题就定形式 / 写结构**：封面和视频才是证据，必须用 `sheet.py` / `frames.py` 看过。
- **crawl 还在跑就建库**：等两个 worker 都打印 `done N/N`。
- **跨天才转存媒体**：签名过期后只能重抓。
- **手改 `site/<slug>/data.js`**：下次 build 会被覆盖，改 `briefs/<slug>.py`。
- **没问就推送**：发布会公开到用户的 GitHub，必须先确认仓库名和公开 / 私有。
