# ForgeCAD 后端

Notion3D 通过 `apps/forge-runner` 调用本机 ForgeCAD CLI 渲染几何。

## 安装

```bash
cd apps/forge-runner && npm install
# 或 make install
```

依赖声明（`apps/forge-runner/package.json`）：

```json
"forgecad": "github:symbiontarch/ForgeCAD#mainline"
```

CLI 路径：

```
apps/forge-runner/node_modules/forgecad/dist-cli/forgecad.js
```

Engine 经 `export-parts.mjs` 调用上述 CLI。

## STL 渲染

```
POST /api/projects/{id}/render-forge
  → Engine 写入 data/.../model.forge.js（+ 可选 src/）
  → node apps/forge-runner/export-parts.mjs
  → forgecad export stl ...
  → model.stl + parts/*.stl + parts.json
  → Web 装配预览 + 部件树
```

MCP：`notion3d_render_forge` → 同上。

`export-parts.mjs` 会为每个部件解析 `source_ref`（主脚本变量或 `src/` 子文件），写入 `parts.json`，供 Web **部件精修**点选跳转。

## Forge 实时预览

```
POST /api/projects/{id}/versions/{v}/forge-preview
  → 同步源码到 data/forge-preview/{projectId}/
  → 本机 ForgeCAD Studio（127.0.0.1:5174）
  → Web iframe（Vite 代理 /forge-preview）
```

左栏调 `param()` 后同步 forge-preview，可在 **Forge 实时** 视口即时看几何变化。

## 产物

| 文件 | 说明 |
|------|------|
| `model.forge.js` | 主脚本 |
| `src/*.forge.js` | 可选子模块（`importAssembly`） |
| `model.stl` | 合并网格 |
| `parts.json` | 部件清单（含 `source_ref` 可选） |
| `parts/{id}.stl` | 分件网格 |

`parts.json` 示例字段：

| 字段 | 说明 |
|------|------|
| `id` / `label` | 部件标识与显示名 |
| `stl_url` | 分件 STL 路径 |
| `color` / `opacity` | 渲染样式（Shell 默认半透明） |
| `source_ref` | 源码位置（主脚本或 `src/` 文件），供部件精修 |

## 自检

```bash
make install
make dev AGENT=engine
curl http://127.0.0.1:8000/health
```

期望：`forgecad_available: true`
