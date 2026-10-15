# 聚光「内容广场」数据源

页面：`https://ad.xiaohongshu.com/microapp/creativity/inspire`（要用户自己的聚光账号登录）。

## 能拿到什么

每个榜单 = 一个 **Top 100**（榜单类型 × 行业或关键词 × 排序指标 × 时间窗）。每条笔记带：

| 字段 | 说明 |
|---|---|
| 阅读 / 点赞 / 收藏 / 评论 | 真实数字 |
| 作者昵称、粉丝数、userId | 账号量级、矩阵 |
| 发布时间 | 精确到秒 |
| isAdNote / bindType | 是否推广、是否蒲公英合作 |
| 全部图片（宽高） | 图文能在页面里翻 |
| 视频地址 + 时长 | 视频能在页面里播 |
| 签名链接（xsec_token） | 「看原文」能直接打开 |

拿不到：**正文全文**（只有标题）、曝光量和阅读率的具体值（只用来排序）。
**图片和视频地址带签名，约 1–2 天过期**：抓完当天就要跑 `jg_media.py`。

## 筛选字段（`juguang.py plan` 已经处理好，排查报错时看）

| 页面上 | 字段 | 取值 |
|---|---|---|
| 榜单 | `bizType` | 2 产品种草 · 7 种草直达 · 4 蒲公英合作 · 1 小红书热门 · 6 电商热门 · 5 客资收集 · 8 应用推广 |
| 时间 | `nd` | `"3"` `"7"` `"14"` `"30"` |
| 排序 | `orderBy` + `sort:"desc"` | 每个榜单可用的字段不同，见 `data/fetch/jg-config/items.json` 的 `sortTabs`；用错报「排序字段不合法」 |
| 行业（种草 / 种草直达 / 蒲公英） | `spuIndustry` | `#` 连接的路径，如 `食品饮料#休闲零食#蜜饯果干` |
| 行业（电商热门） | `eCommerceIndustry` | 如 `零食/坚果/特产#蜜饯/枣类/梅/果干/冻干` |
| 类目（小红书热门） | `noteContentCategory` | `所属行业#` + spu 路径 |
| 关键词 | `searchWord` | 语义召回，总数 1000，只取前 3 页；噪音大 |

`platform` 固定 2，每页 34 条。缺 `nd` 报「时间周期不合法」。

## 抓取原理

在页面**主环境**里调页面自己的接口 `POST edith.xiaohongshu.com/api/pgy_leona/content_square/search_note_v2`，
用页面的 `window._webmsxyw(path, body)` 生成 `x-s` / `x-t` 签名头（GET 不签名返回 `code:-1`）。
OpenCLI 的 `eval` 跑在隔离环境，看不到页面变量，所以脚本插一个 `<script>` 进主环境，结果写回 DOM 属性再读。

## 常见报错

| 现象 | 原因 → 处理 |
|---|---|
| `_webmsxyw is not a function` | 页面没加载完 / 不在灵感页 → `juguang.py open`，等 5 秒再跑 |
| status 里 `loggedIn:false` | 登录过期 → 让用户在那个 Chrome 标签页重新登录 |
| 标签页跳回 `ad.xiaohongshu.com/` 首页 | 会话被踢 → `open` 后重跑 crawl（已抓的会跳过） |
| 连续 3 个查询失败，crawl 自己退出 | 同上，先 `status` |
| `排序字段不合法` / `时间周期不合法` | 聚光改了配置 → 重新 `config`，再 `plan` |
| 封面 / 媒体下载 403、超时 | 签名过期 → 重跑对应查询（删掉 `data/fetch/jg/<name>.json` 再 crawl）|

## 换算成素材库（`jg_library.py`）

- 一条笔记在每个榜单里的名次 = 一行「榜单记录」，榜单名如 `产品种草·蜜饯果干·阅读量·近30日`、`小红书热门·搜「嘴馋」·阅读量·近30日`。
- **榜内百分位** = 最好那一行的 (总数 − 名次) / (总数 − 1) × 100；**爆款 = ≥ 80**。
- 真实数字在 `extra`（reads / likes / collects / comments / fans / published / ad / pgy / srcImages / srcVideo），引擎原样带进页面。

## 数据边界（写进 brief 的 `SOURCE.note`）

- 来源 = 聚光内容广场 Top 100 榜单，写明抓取日期；榜单滚动，过几天结果会变。
- 有阅读、点赞、收藏、评论、粉丝；没有曝光量和正文。
- 行业是投放方选的 SPU 行业，不等于笔记在讲这个品类（「蜜饯果干」榜里混着茶饮联名、吃播），圈竞品要按标题再筛。
- 相关性、可迁移度是判断分；爆品度、爆款率、规律证据是算出来的。
