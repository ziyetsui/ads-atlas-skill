# 环境准备（第一次用）

按缺什么装什么。macOS 用 Homebrew；Windows / Linux 换成对应的包管理器。

| 检查 | 没有的话 |
|---|---|
| `brew --version` | 装 Homebrew：https://brew.sh （终端粘贴首页那行命令） |
| `node --version`（≥ 20） | `brew install node` |
| `opencli --version` | `npm i -g @jackwener/opencli` |
| `opencli doctor` 显示 Extension connected | Chrome 装 OpenCLI 扩展：Chrome 应用店 https://chromewebstore.google.com/detail/opencli/ildkmabpimmkaediidaifkhjpohdnifk ，在 `chrome://extensions` 里确认已启用；再跑 `opencli doctor` |
| `python3 -c "import PIL"` | `python3 -m pip install --user pillow`（新 Mac 第一次跑 python3 会弹出安装「命令行开发者工具」，点安装） |
| `ffmpeg -version` | `brew install ffmpeg`（压缩视频、抽帧必需） |
| `gh auth status`（发布时才需要） | `brew install gh`，然后在 Claude 输入框跑 `! gh auth login -h github.com -p https --web`，浏览器里点授权 |

另外需要：**一个能登录的聚光账号**（ad.xiaohongshu.com）。内容广场只对聚光广告主开放，普通小红书账号进不去。

用户不懂命令行时，把要装的东西一次列清楚，让他在 Claude 输入框里用 `! <命令>` 逐条跑，装完回复你。
