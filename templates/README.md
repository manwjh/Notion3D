# Notion3D 模板库

## 目录

```
templates/builtin/{id}/           # Forge 演示模板
  meta.json
  model.forge.js
templates/legacy/scad/builtin/    # OpenSCAD 遗留（Engine legacy API）
data/templates/user/{id}/         # 用户另存（运行时）
```

## 内置 Forge 模板

| ID | 说明 |
|----|------|
| `hello-assembly` | 5 部件装配 demo |
| `open-enclosure` | 参数化敞口盒 |

Legacy SCAD（`scope=legacy`）：`parametric-cube`、`open-box`、`gear-pair-10-1`、`spacer-washer`

## 校验

```bash
bash templates/scripts/validate-all.sh
```

## API

- `GET /api/templates?scope=builtin|legacy|user|all`
- `POST /api/templates/{id}/apply`
