# Notion3D CAD Backend v2

Notion3D 默认使用 **ForgeCAD** 作为代码建模内核；OpenSCAD 降级为 `openscad_legacy` 兼容路径。

## 架构

```
Agent → notion3d_render_forge → Engine → apps/forge-runner/export-parts.mjs
                                              ↓
                                    ForgeCAD CLI (Manifold)
                                              ↓
                              model.stl + parts/*.stl + parts.json
                                              ↓
                                    Web ViewportHost + 部件树
                                              ↓
                              Web「Forge 实时」= forgecad studio :5174
```

## Forge 实时预览

- API `POST .../versions/{v}/forge-preview` 同步源码到 `data/forge-preview/{project}/` 并启动 ForgeCAD Studio（`:5174`）
- Web 通过 `/forge-preview/` 代理内嵌 iframe（Vite dev proxy）
- 切换版本时自动同步 `model.forge.js` + `src/`；同项目内 chokidar 热更新

## 产物

| 文件 | 说明 |
|------|------|
| `model.forge.js` | 源脚本（主） |
| `model.stl` | 合并网格（导出/打印） |
| `parts.json` | 部件清单（id、label、color、opacity） |
| `parts/{id}.stl` | 分件网格（点选、隐藏） |
| `model.scad` | **legacy** OpenSCAD 源（旧版本） |

## 环境

```bash
cd apps/forge-runner && npm install
make dev AGENT=cursor_sdk
```

Health 返回 `forgecad_available`；Web 对话默认 `NOTION3D_CURSOR_MODEL=composer-2.5`（可在 `.env` 覆盖）。

## Agent 路径

1. `notion3d_report_design_plan`
2. 写 `.forge.js`（多部件用 `{ name, shape }` 或 `importAssembly`）
3. `notion3d_render_forge` → `notion3d_wait_job`
4. `notion3d_report_design_review`

## Legacy OpenSCAD

- 模板：`templates/legacy/scad/builtin/`
- API：`POST .../render-scad`（保留）
- 新功能不再扩展 SCAD 模板库
