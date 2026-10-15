# ads-atlas-skill

一个 Claude Code skill：在输入框里说「我的产品是 XX」，Claude 接管你已登录的 Chrome，从**小红书聚光「内容广场」**榜单抓真实爆款笔记，
圈竞品、拆爆款、提规律，生成一页竞品爆款 brief，发布到**你自己仓库**的 GitHub Pages。

```
我的产品 → 锁定竞品（相关性 × 爆品度）→ 竞品爆款（榜内百分位 × 可迁移度）→ 爆款拆解（账号 / 流量 / 变现 / 结构）→ 规律与落地
```

页面上的每条视频都能直接播放，每条图文都能左右翻看。

## 安装

```sh
git clone https://github.com/ziyetsui/ads-atlas-skill ~/.claude/skills/ads-atlas-skill
```

需要（skill 第一步会逐项检查，缺了会告诉你怎么装）：

| 依赖 | 用途 |
|---|---|
| Chrome + [OpenCLI](https://github.com/jackwener/opencli)（`npm i -g @jackwener/opencli` + Chrome 扩展） | 控制你已登录的浏览器 |
| 聚光账号 | 内容广场要登录才能看 |
| `gh`（已 `gh auth login`） | 建仓库、推送、开 GitHub Pages |
| Python 3 + Pillow，ffmpeg（可选，用来压缩视频） | 生成与转存 |

## 用法

在 Claude Code 里：

> 我的产品是「橘子肉肉」，帮我做竞品爆款 brief（最好附一张产品图）

Claude 会在这几处停下来等你：

1. **登录聚光**：它在 Chrome 打开内容广场，你扫码登录后回复它。
2. **确认搜索范围**：它列出聚光的行业路径和关键词，你确认或增删。
3. **确认发布**：仓库名（默认 `atlas-briefs`）、公开还是私有。

一次大约 1–1.5 小时（抓取 15–40 分钟，分析和检查占大头），产出 `https://<你的 GitHub 用户名>.github.io/<仓库名>/<slug>/`。

## 目录

| 路径 | 内容 |
|---|---|
| `SKILL.md` | 固定流程和停顿点 |
| `agents/analyst.md` | 怎么从素材写出 brief 配置（圈竞品、拆形式、拆解、规律） |
| `agents/qa.md` | 发布前检查 |
| `references/` | 聚光接口与报错对照、配置字段契约、完整实例（橘子肉肉） |
| `scripts/` | 抓取 `juguang.py`、建库、引擎、媒体转存、封面对照图、探针、浏览器验证、发布 |
| `workspace/` | 新工作区（= 你的 brief 仓库）的骨架：页面模板、样式、首页、Pages 工作流 |

## 数据边界

数据来自聚光内容广场的 Top 100 榜单：有榜内名次、阅读、点赞、收藏、评论和粉丝数，没有曝光量和正文。
相关性、可迁移度是判断分，爆品度、爆款率、规律证据是算出来的。只抓你自己账号能看到的内容，请遵守平台规则。
