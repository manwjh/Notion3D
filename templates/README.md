# Notion3D 模板库

ForgeCAD 模板为主；OpenSCAD legacy 在 `templates/legacy/scad/`。

## 目录

```
templates/
  builtin/{id}/           # Forge 模板（默认）
    meta.json               format: "forge"
    model.forge.js
  legacy/scad/builtin/{id}/ # OpenSCAD legacy
    meta.json
    model.scad
data/templates/user/{id}/   # 用户另存（运行时）
```

## 内置 Forge 模板

| ID | 说明 |
|----|------|
| `hello-assembly` | 5 部件装配 demo（Shell/Motor/Battery/PCB/Coil） |
| `open-enclosure` | 参数化敞口盒 |

Legacy SCAD（`scope=legacy`）：`parametric-cube`、`open-box`、`gear-pair-10-1` 等。

## meta.json

| 字段 | 说明 |
|------|------|
| `format` | `forge` 或 `scad`（可省略，按文件推断） |
| `params` | Forge 用 `param("Name", …)` 同名；SCAD 用顶部 `name = 值` |

## 校验

```bash
cd apps/forge-runner && npm install
bash templates/scripts/validate-all.sh
```

## API

- `GET /api/templates?scope=builtin|legacy|user|all`
- `GET /api/templates/{id}` — 含 `forge_code` 或 `scad_code`
- `POST /api/templates/{id}/apply` — 自动选 Forge/SCAD 渲染后端
