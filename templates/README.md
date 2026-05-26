# Notion3D 模板库

## 目录

```
templates/builtin/{id}/
  meta.json
  model.forge.js
data/templates/user/{id}/    # 用户另存
```

## 内置模板

| ID | 说明 |
|----|------|
| `hello-assembly` | 5 部件装配 demo |
| `open-enclosure` | 参数化敞口盒 |

## 校验

```bash
bash templates/scripts/validate-all.sh
```

## API

- `GET /api/templates?scope=builtin|user|all`
- `GET /api/templates/{id}`
- `POST /api/templates/{id}/apply`
- `POST /api/projects/{id}/versions/{v}/save-template`

MCP：`notion3d_list_templates` · `notion3d_get_template` · `notion3d_apply_template` · `notion3d_save_template`

详见 [docs/architecture.md](../docs/architecture.md)。
