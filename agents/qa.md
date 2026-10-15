# QA：发布前检查

全部过了才能问用户要不要发布。任何一项不过，回去改 `briefs/<slug>.py` 或重跑对应脚本，再从头检查。

1. `python3 $WS/scripts/atlas_build.py <slug>`：控制台里 ✓（入选）和 ◆（右上角）一一对应；每个形式 n ≥ 3。
2. `python3 $WS/scripts/jg_media.py <slug>` 最后一行是 `N/N notes hosted`，没有 missing。有 FAILED = 签名过期，重抓那条所在的榜单再跑。之后**再跑一次** `atlas_build.py`（把媒体地址合进去）和 `sync_template.py`。
3. `python3 $WS/scripts/verify.py <slug>`：退出码 0，`failed` 为空，`consoleErrors` 0，`chart` 是 `0 outside`。
4. 用 Read 看 `data/qa/<slug>/` 的三张截图（太长就用 PIL 切成几段再看）：
   - 浅色 / 深色都能读，没有空白区块、没有溢出；
   - 390 宽：四象限标签不互相压住（压住了就把 cluster `name` 再缩短）；
   - 拆解页的结构描述和你看到的视频 / 图片一致。
5. 页面上所有「待确认」都是真的不知道的东西；没有编出来的数字。

把检查结果用 3–5 行告诉用户（入选竞品、3 条规律、多少条视频 / 图文能在页面里看），附截图路径。
