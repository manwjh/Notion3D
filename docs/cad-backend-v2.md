# ForgeCAD 后端

Notion3D 使用 **ForgeCAD**（`apps/forge-runner` + ForgeCAD CLI）作为唯一建模内核。

## 渲染链路

```
notion3d_render_forge → Engine → export-parts.mjs → ForgeCAD CLI
                              → model.stl + parts/*.stl + parts.json
                              → Web 装配预览 + 部件树
```

## Forge 实时预览

- `POST .../versions/{v}/forge-preview` 同步源码到 `data/forge-preview/`
- ForgeCAD Studio `:5174`；Web iframe 经 Vite 代理

## 产物

| 文件 | 说明 |
|------|------|
| `model.forge.js` | 源脚本 |
| `model.stl` | 合并网格 |
| `parts.json` | 部件清单 |
| `parts/{id}.stl` | 分件网格 |

## 环境

```bash
cd apps/forge-runner && npm install
make dev AGENT=cursor_sdk
```

Health → `forgecad_available: true`
