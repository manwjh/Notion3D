# ForgeCAD 后端

Notion3D 默认 CAD 内核为 **ForgeCAD**（`apps/forge-runner` + ForgeCAD CLI）。

## 渲染链路

```
notion3d_render_forge → Engine → export-parts.mjs → ForgeCAD CLI
                              → model.stl + parts/*.stl + parts.json
                              → Web 装配预览 + 部件树
```

## Forge 实时预览

- API `POST .../versions/{v}/forge-preview` 同步源码到 `data/forge-preview/`
- ForgeCAD Studio 默认 `:5174`；Web iframe 经 Vite 代理 `/forge-preview/`

## 产物

| 文件 | 说明 |
|------|------|
| `model.forge.js` | 源脚本 |
| `model.stl` | 合并网格 |
| `parts.json` | 部件清单（id、label、color、opacity） |
| `parts/{id}.stl` | 分件网格 |

## 环境

```bash
cd apps/forge-runner && npm install
make dev AGENT=cursor_sdk
```

Health → `forgecad_available: true`

Legacy OpenSCAD（`model.scad`、旧 API）见 [architecture.md](architecture.md#legacy-engine-保留)。
