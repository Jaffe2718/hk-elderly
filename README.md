# Group 13 StoryMap

## 编辑规范

- `story.json` 是文字、章节顺序和素材关联的唯一来源；`storymap.py` 是统一写入入口。
- 每次写入全量重建指定 StoryMap 的草稿，保留 item ID 和 URL。网页中手改的内容会被下一次运行覆盖。
- 沿用原参考故事的 Summit 主题，封面使用 full、themed 标题面板，显示标题、副标题与英文组员署名。无素材时媒体区留空。
- 章节顺序保持不变；前三章 Docked（左、右、左），第四章 Floating（右），第五章 Slideshow（左上）。`layout` 可设为 `docked-panel`、`floating-panel`、`slideshow`；`panel_position` 的 `start`/`end` 对应英文页面的左/右。
- `title`、`subtitle`、`members` 控制封面信息，组员姓名不包含学号。当前副标题为可调整文案，不表示已完成研究结论。
- 当前章节标题为可调整的占位标题，不包含研究结论。只使用本人素材或获得授权的素材。
- 使用 ArcGIS Pro 登录同一个组织账户；本机 API 固定为 2.4.3。不要把密码、token、登录配置提交 Git。
- 写入前关闭 StoryMap 编辑标签，防止浏览器旧状态再次自动保存覆盖脚本结果；完成后重新打开预览。
- 脚本只保存草稿，不发布、不改变分享范围。首次发布前在 StoryMaps 编辑器检查。
- `backups/` 保存运行前草稿 JSON 和生成结果，不提交 Git；这不是全部媒体的离线备份。脚本不主动删除旧资源。

## 运行

本地校验（不联网、不要求 ArcGIS）：

```powershell
python storymap.py
```

全量写入（ArcGIS Pro 保持登录；Codex 中需在沙箱外执行以访问 Pro 许可）：

```powershell
& 'D:\Program Files\ArcGIS\Pro\bin\Python\Scripts\propy.bat' -u storymap.py --apply
```

主题读取公开参考故事；此步骤只读取主题，不复制其文字、图片和地图。
全量重建使用 API 的内部空白模板方法，集中在 `apply()` 中且锁定版本；升级前需验证此适配段。
另有两处 2.4.3 兼容适配：允许 Sidecar 空媒体；保存草稿时跳过重复写入 access 字段，避免 SDK 对 group-shared 故事调用不存在的方法。不会修改安装目录的 SDK。

## 后续添加素材

将本地图片放在 `assets/`，在某个 slide 中加入 `text` 和可选的 `media`：

```json
{"title":"Population Distribution", "text":"Your narrative", "media":{"type":"image", "path":"assets/population.png"}}
```

地图用 `{"type":"map", "item_id":"WebMap 或 WebScene 的 item ID"}`。
嵌入页面用 `{"type":"embed", "path":"embeds/chart/index.html"}`，文件放在 `docs/embeds/chart/index.html`。

## GitHub 与 Pages

仓库：`https://github.com/Jaffe2718/hk-elderly`。
Pages 发布目录为 main 分支的 `docs/`，托管 HTML/CSS/JS、公开图表和精简数据。
`pages_base_url` 为 `https://jaffe2718.github.io/hk-elderly/`。
页面内部使用相对路径，兼容项目仓库的 URL 前缀。空媒体区不引用虚构 URL。
Pages 只承载可公开的静态素材，不承载密钥、原始敏感数据或 Python 后端；图片也可直接上传至 ArcGIS。
GitHub Pages 部署与 StoryMap 写入分开：前者以后可交给 GitHub Actions，后者目前沿用本机 Pro 登录。
现有 demo：`docs/embeds/elderly-map/index.html`，由协作者提供，保留原文件内容。Leaflet、数据与样式内置，无额外依赖文件或 fetch 请求。
嵌入位置：第四章 Service Distribution，inline 显示。demo 是交互预览，尚未作为最终研究结果核验。
新增嵌入素材时先推送并等 Pages 部署成功，再执行 StoryMap 写入，避免草稿指向尚未上线的 URL。
